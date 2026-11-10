#!/usr/bin/env python3
"""Package an existing QRing Sample without changing its tracked source files."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
import zipfile

ITEMS = ('app', 'gradle', 'build.gradle', 'gradle.properties', 'gradlew',
         'gradlew.bat', 'local.properties', 'settings.gradle')
DOCS = ('sdk_ring_external_access_cn.md', 'sdk_ring_external_access_en.md')
SCRIPTS = Path(__file__).resolve().parent
AAR_PATTERN = re.compile(r'qring_sdk_(\d+(?:\.\d+)+)\.aar')


def emit(data):
    print(json.dumps(data, ensure_ascii=False, indent=2), flush=True)


def config_path():
    override = os.environ.get('QRING_SAMPLE_CONFIG')
    if override:
        return Path(override).expanduser().resolve()
    return Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'qring-sdk-sample-skill' / 'config.json'


def read_config():
    target = config_path()
    if not target.exists():
        return {}
    data = json.loads(target.read_text(encoding='utf-8-sig'))
    if not isinstance(data, dict) or (data.get('output_root') is not None and not isinstance(data['output_root'], str)):
        raise ValueError(f'Invalid output configuration: {target}')
    return data


def absolute_path(value):
    result = Path(value).expanduser()
    if not result.is_absolute():
        raise ValueError(f'An absolute path is required: {value}')
    return result.resolve()


def configure(args):
    target = config_path()
    data = read_config()
    if args.reset:
        data.pop('output_root', None)
    elif args.output_root:
        root = absolute_path(args.output_root)
        if root.exists() and not root.is_dir():
            raise ValueError(f'Output root is a file: {root}')
        data['output_root'] = str(root)
    if args.reset or args.output_root:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        try:
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
    return {'config_file': str(target), 'output_root': data.get('output_root'), 'default': 'current project root'}


def is_link(path):
    return path.is_symlink() or bool(getattr(path.lstat(), 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def without_comments(text):
    token = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/')
    return token.sub(lambda match: ' ' if match.group().startswith(('//', '/*')) else match.group(), text)


def select_aar(project, explicit=None):
    build = project / 'app' / 'build.gradle'
    text = without_comments(build.read_text(encoding='utf-8-sig'))
    references = sorted(set(re.findall(r'qring_sdk_(\d+(?:\.\d+)+)(?:\.aar)?[\'\"]', text)))
    if len(references) > 1 and not explicit:
        raise ValueError(f'Multiple QRing SDK references: {references}; specify --sdk-version after checking the intended dependency.')
    if explicit and not re.fullmatch(r'\d+(?:\.\d+)+', explicit):
        raise ValueError('SDK version must contain numeric dot-separated segments.')
    requested = explicit or (references[0] if references else None)
    candidates = {}
    for file in (project / 'app' / 'libs').iterdir():
        match = AAR_PATTERN.fullmatch(file.name)
        if file.is_file() and match:
            if is_link(file):
                raise ValueError(f'AAR must not be a link: {file}')
            candidates[match.group(1)] = file
    if not candidates:
        raise ValueError('No qring_sdk_<numeric-version>.aar found in app/libs.')
    selected = requested if requested in candidates else max(candidates, key=lambda value: tuple(map(int, value.split('.'))))
    aar = candidates[selected]
    with zipfile.ZipFile(aar) as archive:
        if archive.testzip() or not {'AndroidManifest.xml', 'classes.jar'}.issubset(archive.namelist()):
            raise ValueError(f'Invalid Android AAR: {aar}')
    warning = None
    if requested != selected:
        warning = (f'Current reference {requested or "unresolved"} is unavailable; selected latest numeric version {selected}. '
                   'Sample dependency and source documentation were not rewritten; build compatibility is not verified.')
    elif explicit and references and explicit not in references:
        warning = f'Explicit SDK {explicit} differs from Sample references {references}; source dependency was not rewritten.'
    return {'version': selected, 'aar': str(aar), 'requested_version': requested, 'source_references': references, 'warning': warning}


def make_plan(args):
    project = absolute_path(args.project)
    if not project.is_dir():
        raise ValueError(f'Project not found: {project}')
    for name in ITEMS:
        entry = project / name
        if not entry.exists() or is_link(entry):
            raise ValueError(f'Required item missing or linked: {entry}')
        if entry.is_dir() != (name in ('app', 'gradle')):
            raise ValueError(f'Unexpected item type: {entry}')
    for name in DOCS:
        file = project / 'docs' / name
        if not file.is_file() or is_link(file) or is_link(file.parent):
            raise ValueError(f'Source Markdown missing or linked: {file}')
    sdk = select_aar(project, args.sdk_version)
    root = absolute_path(args.output_root or read_config().get('output_root') or str(project))
    for name in ('app', 'gradle', 'docs'):
        if root == project / name or (project / name) in root.parents:
            raise ValueError(f'Output root cannot be inside a packaged/source directory: {root}')
    if root.exists() and not root.is_dir():
        raise ValueError(f'Output root is a file: {root}')
    stem = f'QRing_Android_SDK_{sdk["version"]}'
    return {'project': str(project), 'output_root': str(root), 'folder': str(root / stem),
            'zip': str(root / f'{stem}.zip'), 'sample_zip': f'{project.name}.zip',
            'items': list(ITEMS), 'pdfs': [Path(name).with_suffix('.pdf').name for name in DOCS], **sdk}


def digest(file):
    hasher = hashlib.sha256()
    with Path(file).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            hasher.update(block)
    return hasher.hexdigest()


def source_entries(project):
    entries = []
    for name in ITEMS:
        source = project / name
        if source.is_file():
            entries.append(source)
            continue
        for directory, children, files in os.walk(source, followlinks=False):
            for child in sorted(children + files):
                item = Path(directory) / child
                if is_link(item):
                    raise ValueError(f'Refusing to package a symlink/junction: {item}')
            entries.extend(Path(directory) / file for file in sorted(files))
    return sorted(entries)


def snapshot(project):
    files = source_entries(project) + [project / 'docs' / name for name in DOCS]
    return {str(file.relative_to(project)): digest(file) for file in files}


def run(command, timeout=180, log=None):
    with tempfile.TemporaryFile(mode='w+b') as stream:
        process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True)
            else:
                process.kill()
            process.wait()
            raise RuntimeError(f'Command timed out after {timeout}s; terminated only the process started for this command.')
        finally:
            stream.seek(0)
            output = stream.read().decode('utf-8', errors='replace')
            if log:
                Path(log).write_text(output, encoding='utf-8')
        if code:
            raise RuntimeError(f'Command failed ({code}):\n{output[-6500:]}')
        return output


def renderer_args(args):
    node = args.node or shutil.which('node')
    if not node:
        raise ValueError('Node.js is unavailable. Locate an existing runtime and supply --node.')
    command = [str(node), str(SCRIPTS / 'render_pdf.mjs')]
    for key in ('node_modules', 'browser'):
        if getattr(args, key):
            command += ['--' + key.replace('_', '-'), getattr(args, key)]
    return command


def clean_project(project, timeout, log):
    if os.name != 'nt':
        raise ValueError('This Skill currently supports the Windows Gradle wrapper workflow only.')
    shell = shutil.which('powershell') or shutil.which('pwsh')
    if not shell:
        raise ValueError('PowerShell is unavailable.')
    run([shell, '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File',
         str(SCRIPTS / 'Invoke-Clean.ps1'), '-ProjectRoot', str(project)], timeout, log)
    if (project / 'app' / 'build').exists() or (project / 'build').exists():
        raise ValueError('Gradle clean left a build directory behind; packaging stopped.')


def create_sample_zip(project, target):
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name in ('app', 'gradle'):
            archive.writestr(f'{project.name}/{name}/', '')
        for file in source_entries(project):
            archive.write(file, f'{project.name}/{file.relative_to(project).as_posix()}')
    with zipfile.ZipFile(target) as archive:
        names = archive.namelist()
        roots = {name.split('/')[1] for name in names}
        if archive.testzip() or roots != set(ITEMS):
            raise ValueError('Sample ZIP integrity/eight-item validation failed.')
        if any(not name.startswith(project.name + '/') or '..' in Path(name).parts for name in names):
            raise ValueError('Unexpected Sample ZIP path.')


def verify_package(folder, final_zip, expected):
    if {file.name for file in folder.iterdir()} != set(expected):
        raise ValueError('Delivery folder must contain exactly four expected files.')
    with zipfile.ZipFile(final_zip) as archive:
        if archive.testzip() or set(archive.namelist()) != {f'{folder.name}/{name}' for name in expected}:
            raise ValueError('Outer ZIP integrity/content validation failed.')
        for name in expected:
            if hashlib.sha256(archive.read(f'{folder.name}/{name}')).hexdigest() != digest(folder / name):
                raise ValueError(f'Outer ZIP content mismatch: {name}')


def publish(folder, outer_zip, output_root):
    destination = output_root / folder.name
    destination_zip = output_root / outer_zip.name
    if any(path.exists() and is_link(path) for path in (destination, destination_zip)):
        raise ValueError('Existing delivery destination is linked; refusing to move it.')
    if destination.exists() and not destination.is_dir():
        raise ValueError('Existing delivery folder is a file.')
    if destination_zip.exists() and not destination_zip.is_file():
        raise ValueError('Existing delivery ZIP is a directory.')
    history = None
    moved = []
    installed = []
    if destination.exists() or destination_zip.exists():
        history_root = output_root / '.qring-history'
        if history_root.exists() and is_link(history_root):
            raise ValueError('History directory must not be a link.')
        history = history_root / f'{folder.name}-{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:8]}'
        history.mkdir(parents=True, exist_ok=False)
    try:
        for old in (destination, destination_zip):
            if old.exists():
                # The resolved parents are constrained before any move.
                if old.resolve().parent != output_root.resolve() or not history.resolve().is_relative_to(output_root.resolve()):
                    raise ValueError('Output/history path escaped its root.')
                backup = history / old.name
                old.rename(backup)
                moved.append((backup, old))
        folder.rename(destination)
        installed.append((destination, folder))
        outer_zip.rename(destination_zip)
        installed.append((destination_zip, outer_zip))
    except Exception:
        for new, original in reversed(installed):
            new.rename(original)
        for backup, original in reversed(moved):
            backup.rename(original)
        raise
    return str(history) if history else None


def package(args):
    plan = make_plan(args)
    project, root = Path(plan['project']), Path(plan['output_root'])
    try:
        from validate_pdf import validate_pdf
    except ImportError as error:
        raise ValueError('PDF validation requires pypdf. Use an existing Python runtime with pypdf installed.') from error
    renderer = renderer_args(args)
    run(renderer + ['--probe', 'true'], timeout=30)
    root.mkdir(parents=True, exist_ok=True)
    log_dir = project / 'testdocs' / f'{datetime.now():%Y-%m-%d}-qring-package'
    log_dir.mkdir(parents=True, exist_ok=True)
    report = log_dir / f'{datetime.now():%H%M%S}-{uuid.uuid4().hex[:8]}'
    report.mkdir()
    emit({'stage': 'clean', 'sdk_version': plan['version'], 'output': plan['zip'], 'warning': plan['warning']})
    clean_project(project, args.clean_timeout, report / 'clean.log')
    current = select_aar(project, args.sdk_version)
    if current != {key: plan[key] for key in current}:
        raise ValueError('SDK selection changed during clean; retry after changes settle.')
    before = snapshot(project)
    staging = Path(tempfile.mkdtemp(prefix='.qring-staging-', dir=root))
    try:
        folder = staging / Path(plan['folder']).name
        folder.mkdir()
        create_sample_zip(project, folder / plan['sample_zip'])
        emit({'stage': 'pdf', 'sources': list(DOCS)})
        pdf_checks = {}
        for source_name, pdf_name in zip(DOCS, plan['pdfs']):
            run(renderer + ['--source', str(project / 'docs' / source_name), '--output', str(folder / pdf_name)],
                timeout=180, log=report / f'{pdf_name}.log')
            pdf = folder / pdf_name
            if not pdf.read_bytes().startswith(b'%PDF-') or pdf.stat().st_size < 1000:
                raise ValueError(f'Invalid PDF output: {pdf}')
            pdf_checks[pdf_name] = validate_pdf(project / 'docs' / source_name, pdf)
        aar = Path(plan['aar'])
        shutil.copy2(aar, folder / aar.name)
        if digest(folder / aar.name) != before[str(aar.relative_to(project))]:
            raise ValueError('Copied AAR hash mismatch.')
        if snapshot(project) != before:
            raise ValueError('Source or Markdown changed during packaging; no final artifact published.')
        expected = [plan['sample_zip'], *plan['pdfs'], aar.name]
        outer_zip = staging / Path(plan['zip']).name
        with zipfile.ZipFile(outer_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for name in expected:
                archive.write(folder / name, f'{folder.name}/{name}')
        verify_package(folder, outer_zip, expected)
        hashes = {name: digest(folder / name) for name in expected}
        history = publish(folder, outer_zip, root)
        result = {**plan, 'status': 'success', 'clean': 'passed', 'zip_validation': 'passed',
                  'pdf_width_overflow': 0, 'pdf_checks': pdf_checks, 'source_unchanged_after_clean': True, 'files_sha256': hashes,
                  'zip_sha256': digest(plan['zip']), 'history': history, 'report': str(report / 'result.json'),
                  'sample_build_tested': False, 'device_tested': False}
        (report / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return result
    finally:
        if staging.exists():
            if staging.resolve().parent != root.resolve() or is_link(staging) or not staging.name.startswith('.qring-staging-'):
                raise ValueError('Refusing cleanup outside the created staging directory.')
            shutil.rmtree(staging)


def parser():
    main = argparse.ArgumentParser(description=__doc__)
    commands = main.add_subparsers(dest='command', required=True)
    config = commands.add_parser('config', help='Read or persist the future output root without packaging.')
    exclusive = config.add_mutually_exclusive_group()
    exclusive.add_argument('--output-root')
    exclusive.add_argument('--reset', action='store_true')
    for command in ('plan', 'pack'):
        sub = commands.add_parser(command)
        sub.add_argument('--project', required=True)
        sub.add_argument('--output-root')
        sub.add_argument('--sdk-version')
        if command == 'pack':
            sub.add_argument('--node')
            sub.add_argument('--node-modules')
            sub.add_argument('--browser')
            sub.add_argument('--clean-timeout', type=int, default=180)
    return main


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    args = parser().parse_args()
    try:
        emit(configure(args) if args.command == 'config' else make_plan(args) if args.command == 'plan' else package(args))
        return 0
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as error:
        emit({'status': 'failed', 'error': str(error)})
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
