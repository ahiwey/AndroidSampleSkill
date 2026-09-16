"""Read-only, explicitly scoped Android resource/reference and layout evidence."""
import argparse
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET


def read(path):
    return path.read_text(encoding='utf-8-sig')


def inspect(resources, scopes, res_dirs, limit=12, node_id=None):
    documents = [(Path(p).resolve(), read(Path(p))) for p in scopes]
    definitions = {r: [] for r in resources}
    issues = []
    for root in map(Path, res_dirs):
        if not root.is_dir():
            raise ValueError(f'resource directory missing: {root}')
        for folder in sorted(root.iterdir()):
            if not folder.is_dir():
                continue
            kind = folder.name.split('-', 1)[0]
            if kind == 'values':
                for file in sorted(folder.glob('*.xml')):
                    try:
                        tree = ET.fromstring(read(file))
                    except ET.ParseError as error:
                        issues.append({'path': str(file), 'issue': str(error)})
                        continue
                    for element in tree:
                        key = f"{element.get('type', element.tag)}/{element.get('name', '')}"
                        if key in definitions:
                            definitions[key].append({'path': str(file.resolve()), 'qualifier': folder.name,
                                                     'value': ''.join(element.itertext()).strip()[:400]})
            else:
                for resource in resources:
                    resource_type, name = resource.split('/')
                    if resource_type != kind:
                        continue
                    for file in sorted(folder.glob(name + '.*')):
                        if file.name.split('.')[0] == name:
                            definitions[resource].append({'path': str(file.resolve()), 'qualifier': folder.name})
    reports = []
    for resource in resources:
        kind, name = resource.split('/')
        pattern = re.compile(r'@(?:[\w.]+:)?' + re.escape(resource) + r'(?![\w])|\bR\.' +
                             re.escape(kind) + r'\.' + re.escape(name) + r'(?![\w])')
        hits = []
        for path, content in documents:
            for number, line in enumerate(content.splitlines(), 1):
                if pattern.search(line):
                    hits.append({'path': str(path), 'line': number, 'text': line.strip()[:500]})
        reports.append({'resource': resource, 'definitions': definitions[resource][:limit],
                        'definition_count': len(definitions[resource]), 'references': hits[:limit],
                        'reference_count': len(hits),
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
        nodes = []
        targets = [tree] if not node_id else [e for e in tree.iter()
                  if e.get('{http://schemas.android.com/apk/res/android}id', '').split('/')[-1] == node_id]
        for element in (e for target in targets for e in target.iter()):
            attrs = {('tools:' if key.startswith('{http://schemas.android.com/tools}') else '') +
                     key.split('}')[-1]: value for key, value in element.attrib.items()}
            selected = {key: value for key, value in attrs.items() if key in
                        ('id', 'orientation', 'text', 'textColor', 'style', 'gravity', 'layout_gravity',
                         'layout_weight', 'layout_width', 'layout_height', 'src', 'tint', 'alpha',
                         'drawableStart', 'drawableLeft', 'drawableEnd') or 'constraint' in key
                        or key.startswith('tools:')}
            if selected:
                nodes.append({'tag': element.tag, 'attributes': selected,
                              'children': [c.get('{http://schemas.android.com/apk/res/android}id', c.tag)
                                           for c in element]})
        layouts.append({'path': str(path), 'nodes': nodes[:limit], 'node_count': len(nodes)})
    return {'resources': reports, 'layouts': layouts, 'issues': issues,
            'scope_files': len(documents),
            'limitations': 'Literal evidence only: comments/tools attributes can match; includes, styles, aliases, '
                           'bindings, runtime overrides and dynamic lookups require targeted follow-up. '
                           'No match in supplied scope does not prove an unused resource. '
                           'Definitions are variants, not a claim about the active runtime value.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resource', action='append', default=[], help='type/name, repeatable')
    parser.add_argument('--scope', action='append', required=True, help='Exact source/layout file; repeatable')
    parser.add_argument('--res', action='append', default=[], help='Explicit res root; repeat for other source sets')
    parser.add_argument('--limit', type=int, default=12, help='Maximum evidence rows per section')
    parser.add_argument('--node-id', help='Limit layout nodes to this id and descendants (without @id/)')
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 100:
        parser.error('--limit must be between 1 and 100')
    if any(not re.fullmatch(r'[a-z][a-z0-9_]*/[A-Za-z_][A-Za-z0-9_]*', r) for r in args.resource):
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
