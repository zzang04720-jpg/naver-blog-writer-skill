"""Offline repository checks. Never reads .env or contacts providers."""
import argparse
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    errors = []
    for name in ['AGENTS.md', 'CLAUDE.md', 'docs/design.md', '.env.example', 'blog-profile.example.yaml']:
        if not (ROOT / name).is_file():
            errors.append('Missing: ' + name)
    for role in ['keyword-scout', 'post-writer', 'quality-auditor', 'visual-producer']:
        p = ROOT / '.claude/agents' / (role + '.md')
        if not p.is_file() or 'skills:\n' not in p.read_text(encoding='utf-8'):
            errors.append('Agent definition missing/invalid: ' + role)
    left, right = ROOT / '.claude/skills', ROOT / '.agents/skills'
    files = lambda base: {p.relative_to(base) for p in base.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    for relative in files(left) | files(right):
        a, b = left / relative, right / relative
        if not a.is_file() or not b.is_file() or a.read_bytes() != b.read_bytes():
            errors.append('Skill copies differ: ' + relative.as_posix())
    if sys.version_info < (3, 9):
        errors.append('Python 3.9+ is required')
    if not args.offline:
        for name in ['.env', 'blog-profile.yaml']:
            if not (ROOT / name).is_file():
                errors.append('Create and fill your local ' + name + ' (see README.md)')
        if not shutil.which('claude'):
            errors.append('Install Claude Code CLI and sign in from this repository')
        print('Node (optional GUI): ' + ('found' if shutil.which('node') else 'not found'))
        print('Credentials/profile contents are not inspected. Complete S0 before writing.')
    for error in errors:
        print('FAIL: ' + error)
    if errors:
        return 1
    print('PASS: offline repository checks' if args.offline else 'PASS: files/tools present; live credentials and workflow NOT verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
