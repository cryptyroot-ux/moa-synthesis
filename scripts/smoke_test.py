#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict

from hermes_config import deep_merge, load_yaml


def run(cmd, timeout=60):
    try:
        return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        class R:
            returncode = 124
            stdout = f'Timeout after {timeout}s: {e}'
        return R()


def load_source(home: Path, source: str) -> Dict[str, Any]:
    cfg_path = home / 'config.yaml'
    patch_path = home / 'state' / 'moa-synthesis' / 'config.patch.yaml'
    merged_path = home / 'state' / 'moa-synthesis' / 'config.merged.preview.yaml'

    if source == 'config':
        return load_yaml(cfg_path, require_yaml=cfg_path.exists())
    if source == 'patch':
        return load_yaml(patch_path, require_yaml=patch_path.exists())
    if source == 'merged':
        return load_yaml(merged_path, require_yaml=merged_path.exists())
    if source == 'auto':
        cfg = load_yaml(cfg_path, require_yaml=cfg_path.exists())
        if ((cfg.get('moa') or {}).get('presets') or {}):
            return cfg
        if merged_path.exists():
            return load_yaml(merged_path, require_yaml=True)
        if patch_path.exists():
            return deep_merge(cfg, load_yaml(patch_path, require_yaml=True))
        return cfg
    raise SystemExit(f'Unknown source: {source}')


def main() -> int:
    ap = argparse.ArgumentParser(description='Smoke-test MoA Synthesis Hermes config without exposing secrets.')
    ap.add_argument('--hermes-home', default=os.environ.get('HERMES_HOME', '~/.hermes'))
    ap.add_argument('--preset', default='moa-synthesis-auto')
    ap.add_argument('--source', choices=['auto', 'config', 'patch', 'merged'], default='auto')
    ap.add_argument('--run-model-switch-test', action='store_true', help='Try a lightweight Hermes command if hermes binary exists.')
    args = ap.parse_args()

    home = Path(args.hermes_home).expanduser()
    cfg = load_source(home, args.source)
    preset = ((cfg.get('moa') or {}).get('presets') or {}).get(args.preset)
    if not preset:
        print(f'Preset not found in {args.source} source: {args.preset}')
        return 1
    refs = preset.get('reference_models') or []
    agg = preset.get('aggregator') or {}
    if not isinstance(refs, list) or not refs:
        print('MoA preset has no reference_models.')
        return 1
    if not isinstance(agg, dict) or not agg.get('provider') or not agg.get('model'):
        print('MoA preset aggregator missing provider/model.')
        return 1
    for i, ref in enumerate(refs):
        if not isinstance(ref, dict) or not ref.get('provider') or not ref.get('model'):
            print(f'MoA reference_models[{i}] missing provider/model.')
            return 1
        if ref.get('provider') == 'custom' and not ref.get('base_url'):
            # MoA docs use explicit provider/model pairs. Named custom providers should be `custom:<name>`.
            print('MoA reference uses provider: custom without base_url or named provider. Prefer custom:<name> via custom_providers.')
            return 1
    if agg.get('provider') == 'custom' and not agg.get('base_url'):
        # This can be valid only if the global model provider/base_url are custom; warn instead of hard-fail.
        print('WARNING: MoA aggregator uses provider: custom. Verify Hermes can resolve base_url from your active custom model config.')
    rmt = preset.get('reference_max_tokens')
    if isinstance(rmt, int) and rmt > 1500:
        print('WARNING: reference_max_tokens is high; advisor latency may dominate turn time.')
    print(f'Config shape OK for preset {args.preset}: {len(refs)} references, aggregator {agg.get("provider")}:{agg.get("model")}')

    fps = cfg.get('fallback_providers') or []
    if fps and not isinstance(fps, list):
        print('fallback_providers must be a list.')
        return 1
    for i, fp in enumerate(fps):
        if not isinstance(fp, dict) or not fp.get('provider') or not fp.get('model'):
            print(f'fallback_providers[{i}] missing provider/model.')
            return 1
        if fp.get('provider') == 'custom' and not fp.get('base_url'):
            print(f'fallback_providers[{i}] custom fallback missing base_url.')
            return 1

    hermes = shutil.which('hermes')
    if not hermes:
        print('Hermes binary not found in PATH; skipped runtime smoke test.')
        return 0
    if args.run_model_switch_test:
        env = dict(os.environ)
        env['HERMES_HOME'] = str(home)
        res = run([hermes, 'moa', 'list'], timeout=30)
        print(res.stdout[:4000])
        if res.returncode != 0:
            print('`hermes moa list` failed.')
            return res.returncode
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
