#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    'SKILL.md', 'README.md', 'SECURITY.md', 'LICENSE',
    'references/playbook-v4.md', 'references/provider-model-policy.md', 'references/audit-v3-findings.md', 'references/hermes-skill-compatibility.md',
    'examples/sanitized-escalation-example.md', 'examples/config.patch.example.yaml', 'templates/advisor-brief.md', 'templates/red-team-brief.md',
    'scripts/hermes_config.py', 'scripts/discover_models.py', 'scripts/tune_panel.py', 'scripts/apply_patch.py', 'scripts/smoke_test.py',
    'schemas/model_inventory.schema.json', 'benchmarks/gate_cases.jsonl', 'tests/test_regressions.py',
]
SECRET_PATTERNS = [
    r'sk-[A-Za-z0-9_\-]{20,}',
    r'ghp_[A-Za-z0-9]{20,}',
    r'AIza[0-9A-Za-z_\-]{20,}',
    r'-----BEGIN (RSA|OPENSSH|EC|DSA|PRIVATE) KEY-----',
    r'(?i)bearer\s+[A-Za-z0-9_\-\.]{20,}',
]
SECTIONS = ['## When to Use','## Procedure','## Pitfalls','## Verification']


def main():
    ok = True
    for rel in REQUIRED:
        if not (ROOT / rel).exists():
            print(f'Missing required file: {rel}')
            ok = False
    skill = (ROOT / 'SKILL.md').read_text(errors='ignore') if (ROOT / 'SKILL.md').exists() else ''
    for section in SECTIONS:
        if section not in skill:
            print(f'SKILL.md missing section: {section}')
            ok = False

    # Hermes skill index should stay concise. Enforce short description and no hard requires_toolsets.
    import re as _re
    fm = _re.search(r'^---\n(.*?)\n---', skill, _re.S)
    if not fm:
        print('SKILL.md missing YAML frontmatter')
        ok = False
    else:
        front = fm.group(1)
        m = _re.search(r'^description:\s*(.+)$', front, _re.M)
        if not m:
            print('SKILL.md missing description')
            ok = False
        elif len(m.group(1).strip().strip('"\'')) > 60:
            print('SKILL.md description exceeds 60 characters')
            ok = False
        if 'requires_toolsets:' in front:
            print('Do not declare requires_toolsets; this skill should remain discoverable')
            ok = False
    forbidden_dirs = ['__pycache__']
    for bad in forbidden_dirs:
        if any(part == bad for path in ROOT.rglob('*') for part in path.parts):
            print(f'Forbidden generated directory present: {bad}')
            ok = False

    for path in ROOT.rglob('*'):
        if path.is_file() and path.suffix.lower() in {'.md','.py','.yaml','.yml','.json','.txt','.jsonl'}:
            text = path.read_text(errors='ignore')
            for pat in SECRET_PATTERNS:
                if re.search(pat, text):
                    print(f'Potential secret pattern in {path.relative_to(ROOT)}')
                    ok = False
    if ok:
        print('MoA Synthesis v4.1 validation passed.')
        return 0
    return 1

if __name__ == '__main__':
    sys.exit(main())
