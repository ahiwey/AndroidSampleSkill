"""Run the installed official validator plus local metadata/reference checks."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validator', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    codex = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex'))
    validator = args.validator or codex / 'skills/.system/skill-creator/scripts/quick_validate.py'
    try:
        import yaml
    except ImportError:
        print('Missing PyYAML. Install into this Python with: python -m pip install --user -r requirements-validation.txt', file=sys.stderr)
        return 2
    if not validator.is_file():
        print('Official validator not found; supply --validator <quick_validate.py>.', file=sys.stderr)
        return 2
    result = subprocess.run([sys.executable, '-X', 'utf8', str(validator), str(root)], check=False)
    if result.returncode:
        return result.returncode
    try:
        ui = yaml.safe_load((root / 'agents/openai.yaml').read_text(encoding='utf-8'))['interface']
        if not 25 <= len(ui['short_description']) <= 64:
            raise ValueError('short_description must contain 25-64 characters')
        if '$' + root.name not in ui['default_prompt']:
            raise ValueError('default_prompt must mention this skill')
        for file in [root / 'SKILL.md', root / 'README.md', *(root / 'references').glob('*.md')]:
            text = file.read_text(encoding='utf-8')
            if text.count('```') % 2:
                raise ValueError(f'unclosed fence: {file.name}')
            for link in re.findall(r'\]\(([^)]+)\)', text):
                if '://' not in link and not link.startswith('#'):
                    target = (file.parent / link.split('#', 1)[0]).resolve()
                    if not target.is_relative_to(root) or not target.exists():
                        raise ValueError(f'invalid local reference: {file.name}: {link}')
    except (ValueError, KeyError, TypeError, OSError, yaml.YAMLError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print('PASS: official format validator, UI metadata, local references and code fences.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
