#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run(args, cwd=ROOT, expect=0):
    res = subprocess.run([PYTHON] + args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if res.returncode != expect:
        raise AssertionError(f"Command failed ({res.returncode} != {expect}): {args}\n{res.stdout}")
    return res.stdout


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def main():
    with tempfile.TemporaryDirectory() as td:
        home = Path(td) / 'hermes'
        home.mkdir()
        write(home / 'config.yaml', '''
model:
  provider: openrouter
  default: deepseek/deepseek-v4-pro
  context_length: 64000
fallback_providers:
  - provider: openai-codex
    model: gpt-5.5
moa:
  presets:
    review:
      reference_models:
        - provider: openai-codex
          model: gpt-5.5
      aggregator:
        provider: openrouter
        model: deepseek/deepseek-v4-pro
      enabled: true
custom_providers:
  - name: local
    base_url: http://localhost:11434/v1
    models:
      qwen3:4b:
        context_length: 64000
''')
        run(['scripts/discover_models.py', '--hermes-home', str(home), '--preferred', 'openai-codex:gpt-5.5.5'])
        inv = json.loads((home / 'state/moa-synthesis/model-inventory.json').read_text())
        assert any(m['provider'] == 'openai-codex' and m['model'] == 'gpt-5.5.5' and m['proof'] == 'user-preferred' for m in inv['models'])

        run(['scripts/tune_panel.py', '--hermes-home', str(home), '--write-preview'])
        patch = (home / 'state/moa-synthesis/config.patch.yaml').read_text()
        assert 'gpt-5.5.5' not in patch, 'unverified preferred model leaked into safe patch'
        assert 'provider_routing:' not in patch, 'provider_routing should not be written unless explicitly requested'
        agg_block = patch.split('aggregator:', 1)[1].split('reference_max_tokens:', 1)[0]
        assert 'custom:local' not in agg_block, 'custom provider should not become aggregator when strong cloud aggregator exists'

        run(['scripts/tune_panel.py', '--hermes-home', str(home), '--write-preview', '--include-provider-routing'])
        patch_with_routing = (home / 'state/moa-synthesis/config.patch.yaml').read_text()
        assert 'provider_routing:' in patch_with_routing, 'provider_routing flag did not write routing block'
        run(['scripts/tune_panel.py', '--hermes-home', str(home), '--write-preview'])
        run(['scripts/apply_patch.py', '--hermes-home', str(home)])
        run(['scripts/smoke_test.py', '--hermes-home', str(home), '--source', 'merged'])
        run(['scripts/apply_patch.py', '--hermes-home', str(home), '--apply'])
        cfg = (home / 'config.yaml').read_text()
        assert 'provider: openai-codex' in cfg and 'model: gpt-5.5' in cfg, 'existing fallback was destroyed'
        assert 'moa-synthesis-auto' in cfg, 'managed MoA preset not applied'

    with tempfile.TemporaryDirectory() as td:
        home = Path(td) / 'empty'
        home.mkdir()
        run(['scripts/discover_models.py', '--hermes-home', str(home), '--preferred', 'openai-codex:gpt-5.5.5'])
        run(['scripts/tune_panel.py', '--hermes-home', str(home), '--write-preview'], expect=1)

    print('regression tests passed')


if __name__ == '__main__':
    main()
