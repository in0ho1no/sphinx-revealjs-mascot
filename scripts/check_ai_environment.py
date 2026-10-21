"""Check shared AI instructions and optionally run the hook regression suites."""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def check_references(path: Path) -> list[str]:
    """Find broken local links and Claude imports outside fenced examples."""
    text = re.sub(r'^(`{3,}|~{3,}).*?^\1[^\n]*$', '', path.read_text(encoding='utf-8'), flags=re.MULTILINE | re.DOTALL)
    targets = re.findall(r'\[[^\]]*\]\(([^)]+)\)', text)
    if path.name == 'CLAUDE.md':
        targets.extend(re.findall(r'^@([^\s]+)$', text, flags=re.MULTILINE))
    errors: list[str] = []
    for target in targets:
        parsed = urlsplit(target.strip('<>'))
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        resolved = (path.parent / unquote(parsed.path)).resolve()
        if not resolved.is_relative_to(ROOT) or not resolved.exists():
            errors.append(f'{path.relative_to(ROOT)}: broken local reference: {target}')
    return errors


def check_structure() -> list[str]:
    """Validate references and the portable skill/adapter contract without dependencies."""
    errors: list[str] = []
    markdown = [ROOT / 'AGENTS.md', ROOT / 'README.md', ROOT / 'docs/ai-environment.md']
    for directory in ('.agents', '.claude', '.github/agents', '.github/instructions'):
        markdown.extend((ROOT / directory).rglob('*.md'))
    markdown.append(ROOT / '.github/copilot-instructions.md')
    for path in markdown:
        if not path.is_file():
            errors.append(f'missing required document: {path.relative_to(ROOT)}')
            continue
        errors.extend(check_references(path))

    entrypoints = {
        '.claude/CLAUDE.md': '@../AGENTS.md',
        '.github/copilot-instructions.md': '(../AGENTS.md)',
    }
    for relative, reference in entrypoints.items():
        path = ROOT / relative
        if path.is_file() and reference not in path.read_text(encoding='utf-8'):
            errors.append(f'{relative}: missing shared instruction reference')

    for path in (ROOT / '.agents/skills').glob('*/SKILL.md'):
        text = path.read_text(encoding='utf-8')
        parts = text.split('---', 2)
        if len(parts) != 3 or parts[0].strip():
            errors.append(f'{path.relative_to(ROOT)}: missing skill frontmatter')
            continue
        name = re.search(r'^name: ([a-z0-9-]+)$', parts[1], flags=re.MULTILINE)
        if not name or name[1] != path.parent.name or not re.search(r'^description: \S', parts[1], flags=re.MULTILINE):
            errors.append(f'{path.relative_to(ROOT)}: invalid skill discovery metadata')
        if re.search(r'^(context|background|model|allowed-tools):', parts[1], flags=re.MULTILINE):
            errors.append(f'{path.relative_to(ROOT)}: client-specific metadata in shared skill')
        adapter = ROOT / '.claude/skills' / path.parent.name / 'SKILL.md'
        if not adapter.is_file() or f'.agents/skills/{path.parent.name}/SKILL.md' not in adapter.read_text(encoding='utf-8'):
            errors.append(f'{path.relative_to(ROOT)}: missing Claude skill reference')
    if not list((ROOT / '.agents/skills').glob('*/SKILL.md')):
        errors.append('no discoverable Codex skills')
    if list((ROOT / '.github/skills').glob('*/SKILL.md')):
        errors.append('obsolete .github/skills copies: keep shared skills in .agents/skills')
    for adapter in (ROOT / '.claude/skills').glob('*/SKILL.md'):
        if not (ROOT / '.agents/skills' / adapter.parent.name / 'SKILL.md').is_file():
            errors.append(f'{adapter.relative_to(ROOT)}: no canonical skill')

    for path in (ROOT / '.claude/settings.json', *(ROOT / '.github/hooks').glob('*.json')):
        try:
            json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError) as exc:
            errors.append(f'{path.relative_to(ROOT)}: invalid JSON: {exc}')
    for directory in ('.claude/hooks', '.github/hooks', 'scripts'):
        for path in (ROOT / directory).glob('*.py'):
            try:
                ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
            except SyntaxError as exc:
                errors.append(f'{path.relative_to(ROOT)}: invalid Python: {exc}')
    return errors


def main() -> int:
    """Run checks and return a nonzero status for any broken configuration."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hooks', action='store_true', help='also run all hook regression suites')
    arguments = parser.parse_args()
    errors = check_structure()
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print('AI configuration references, skill adapters, JSON and Python syntax: OK', flush=True)
    if arguments.hooks:
        for suite in ('_test_hook.py', '_test_hook_input.py', '_test_log_privacy.py'):
            path = ROOT / '.github/hooks' / suite
            result = subprocess.run([sys.executable, str(path)], cwd=ROOT, capture_output=True, timeout=180)
            if result.returncode:
                print(result.stdout.decode('utf-8', errors='replace'))
                print(result.stderr.decode('utf-8', errors='replace'), file=sys.stderr)
                return 1
            print(f'{suite}: OK', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
