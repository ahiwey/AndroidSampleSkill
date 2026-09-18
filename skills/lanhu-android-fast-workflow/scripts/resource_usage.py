"""Read-only scoped resource evidence; candidates are not runtime-resolved values."""
import argparse
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ANDROID = '{http://schemas.android.com/apk/res/android}'
TOOLS = '{http://schemas.android.com/tools}'
LOCAL = re.compile(r'^@(?:\+)?([a-z][a-z0-9_]*/[A-Za-z_][A-Za-z0-9_.]*)$')


def read(path):
    return path.read_text(encoding='utf-8-sig')


def attributes(element):
    return {('tools:' if k.startswith(TOOLS) else '') + k.split('}')[-1]: v
            for k, v in element.attrib.items()}


def without_comments(text, xml=False):
    # Preserve lines and quoted strings, including Kotlin raw strings.
    pattern = r'<!--[\s\S]*?-->' if xml else r'"""[\s\S]*?"""|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/'
    return re.sub(pattern, lambda m: re.sub(r'[^\n]', ' ', m[0])
                  if xml or m[0].startswith(('//', '/*')) else m[0], text)


def inspect(resources, scopes, res_dirs, limit=12, node_id=None):
    documents = [(Path(p).resolve(), read(Path(p))) for p in scopes]
    index, issues = {}, []
    for root in dict.fromkeys(Path(p).resolve() for p in res_dirs):
        if not root.is_dir():
            raise ValueError(f'resource directory missing: {root}')
        for folder in sorted(root.iterdir()):
            if not folder.is_dir():
                continue
            kind = folder.name.split('-', 1)[0]
            for file in sorted(folder.iterdir()):
                if not file.is_file():
                    continue
                base = {'path': str(file.resolve()), 'qualifier': folder.name, 'res_root': str(root)}
                if kind != 'values':
                    index.setdefault(f'{kind}/{file.name.split(".")[0]}', []).append(base)
                    continue
                if file.suffix != '.xml':
                    continue
                try:
                    tree = ET.fromstring(read(file))
                except ET.ParseError as error:
                    issues.append({'path': str(file), 'issue': str(error)})
                    continue
                for element in tree:
                    key = f"{element.get('type', element.tag)}/{element.get('name', '')}"
                    item = dict(base)
                    if element.tag == 'style':
                        item['items'] = {e.get('name'): (e.text or '').strip() for e in element if e.tag == 'item'}
                        name = element.get('name', '')
                        item['parent'] = element.get('parent', name.rsplit('.', 1)[0] if '.' in name else '')
                    else:
                        item['value'] = ''.join(element.itertext()).strip()[:400]
                    index.setdefault(key, []).append(item)

    def resolve(key, chain=()):
        if key in chain or len(chain) >= 6:
            return {'resource': key, 'status': 'cycle' if key in chain else 'depth_limit'}
        entries = index.get(key, [])
        candidates = []
        for entry in entries[:limit]:
            result = dict(entry)
            alias = LOCAL.fullmatch(entry.get('value', ''))
            if alias:
                result['alias'] = resolve(alias[1], chain + (key,))
            elif entry.get('value', '').startswith(('?', '@')):
                result['unresolved'] = 'theme, external or complex value'
            candidates.append(result)
        return {'resource': key, 'status': 'candidates_only' if entries else 'not_defined_in_scope',
                'candidate_count': len(entries), 'candidates': candidates}

    def styles(value, chain=()):
        key = value[1:] if value.startswith('@style/') else 'style/' + value
        if value.startswith(('@android:', '?')):
            return [{'unresolved': value}]
        if key in chain or len(chain) >= 6:
            return [{'unresolved': 'style cycle/depth limit', 'resource': key}]
        result = []
        for entry in index.get(key, [])[:limit]:
            merged, unresolved = {}, []
            parent = entry.get('parent')
            if parent:
                inherited = styles(parent, chain + (key,))
                if len(inherited) == 1 and not inherited[0].get('unresolved'):
                    merged.update(inherited[0].get('attributes', {}))
                else:
                    unresolved.append({'parent': parent, 'reason': 'missing, external, cyclic or variant-dependent'})
            merged.update({k.removeprefix('android:'): v for k, v in entry.get('items', {}).items()})
            result.append({**entry, 'attributes': merged, 'unresolved': unresolved})
        return result or [{'unresolved': value, 'reason': 'not defined in supplied roots'}]

    def node(element):
        attrs = attributes(element)
        result = {'tag': element.tag, 'attributes': attrs,
                  'children': [c.get(ANDROID + 'id', c.tag) for c in element]}
        if 'style' in attrs:
            result['style_candidates'] = styles(attrs['style'])
            for candidate in result['style_candidates']:
                candidate['attribute_resources'] = {
                    k: resolve(LOCAL.fullmatch(v)[1]) for k, v in candidate.get('attributes', {}).items()
                    if LOCAL.fullmatch(v)}
        refs = {k: resolve(LOCAL.fullmatch(v)[1]) for k, v in attrs.items()
                if LOCAL.fullmatch(v) and not k.startswith('tools:') and k not in ('id', 'style')}
        if refs:
            result['attribute_resources'] = refs
        return result

    def includes(tree, chain=()):
        found = []
        for element in tree.iter('include'):
            value = element.get('layout', '')
            match = LOCAL.fullmatch(value)
            if not match:
                found.append({'layout': value, 'unresolved': True})
                continue
            key = match[1]
            edge = {'layout': value, 'candidates': []}
            if key in chain or len(chain) >= 4:
                edge['unresolved'] = 'include cycle/depth limit'
            else:
                entries = index.get(key, [])
                edge['candidate_count'] = len(entries)
                for entry in entries[:limit]:
                    candidate = dict(entry)
                    try:
                        included = ET.fromstring(read(Path(entry['path'])))
                        candidate['root'] = node(included)
                        candidate['includes'] = includes(included, chain + (key,))
                    except (OSError, ET.ParseError) as error:
                        candidate['unresolved'] = str(error)
                    edge['candidates'].append(candidate)
            found.append(edge)
        return found[:limit]

    reports = []
    for resource in resources:
        kind, name = resource.split('/')
        pattern = re.compile(r'@(?:\+)?' + re.escape(resource) + r'(?![\w.])|(?<![\w.])R\.' +
                             re.escape(kind) + r'\.' + re.escape(name) + r'(?![\w])')
        hits, previews = [], []
        for path, content in documents:
            clean = without_comments(content, path.suffix == '.xml')
            spans = [(m.start(), m.end()) for m in re.finditer(r'\btools:[\w]+\s*=\s*(?:"[^"]*"|\'[^\']*\')', clean)] if path.suffix == '.xml' else []
            for match in pattern.finditer(clean):
                number = clean.count('\n', 0, match.start()) + 1
                entry = {'path': str(path), 'line': number, 'text': content.splitlines()[number-1].strip()[:500]}
                target = previews if any(a <= match.start() < b for a, b in spans) else hits
                if entry not in target:
                    target.append(entry)
        entries = index.get(resource, [])
        reports.append({'resource': resource, 'definitions': entries[:limit], 'definition_count': len(entries),
                        'resolution': resolve(resource), 'references': hits[:limit], 'reference_count': len(hits),
                        'preview_references': previews[:limit], 'preview_reference_count': len(previews),
                        'status': 'references_found_in_scope' if hits else 'not_found_in_scope'})
    layouts = []
    for path, content in documents:
        if path.suffix != '.xml' or not path.parent.name.startswith('layout'):
            continue
        try:
            tree = ET.fromstring(content)
        except ET.ParseError as error:
            issues.append({'path': str(path), 'issue': str(error)})
            continue
        parents = {child: parent for parent in tree.iter() for child in parent}
        targets = [tree] if not node_id else [e for e in tree.iter() if e.get(ANDROID + 'id', '').split('/')[-1] == node_id]
        elements = list(dict.fromkeys(e for target in targets for e in target.iter()))
        ancestors = []
        for target in targets:
            while target in parents:
                target = parents[target]
                if target not in ancestors:
                    ancestors.append(target)
        layouts.append({'path': str(path), 'nodes': [node(e) for e in elements[:limit]], 'node_count': len(elements),
                        'ancestors': [node(e) for e in ancestors[:limit]], 'ancestor_count': len(ancestors),
                        'includes': includes(tree), 'target_found': bool(targets)})
    return {'resources': reports, 'layouts': layouts, 'issues': issues, 'scope_files': len(documents),
            'limitations': 'Static candidates only, not active runtime values. Source references are lexical evidence, '
                           'not proof a code path runs. Theme/skin, dynamic bindings, source-set precedence and selectors '
                           'need targeted follow-up. Aliases/styles depth 6; includes depth 4; output limited. '
                           'No match in supplied scope does not prove an unused resource.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resource', action='append', default=[], help='type/name, repeatable')
    parser.add_argument('--scope', action='append', required=True, help='Exact source/layout file; repeatable')
    parser.add_argument('--res', action='append', default=[], help='Explicit res root; repeat for other source sets')
    parser.add_argument('--limit', type=int, default=12, help='Maximum evidence rows per section')
    parser.add_argument('--node-id', help='Target subtree plus ancestors, without @id/')
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 100:
        parser.error('--limit must be between 1 and 100')
    if any(not re.fullmatch(r'[a-z][a-z0-9_]*/[A-Za-z_][A-Za-z0-9_.]*', r) for r in args.resource):
        parser.error('resources must be type/name')
    try:
        report = inspect(list(dict.fromkeys(args.resource)), args.scope, args.res, args.limit, args.node_id)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, separators=(',', ':')))
    return 1 if report['issues'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
