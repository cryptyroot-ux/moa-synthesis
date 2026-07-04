#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

from hermes_config import deep_merge, dump_yaml, load_yaml, now_stamp


def main() -> int:
    ap = argparse.ArgumentParser(description='Dry-run or apply MoA Synthesis config patch with backup.')
    ap.add_argument('--hermes-home', default=os.environ.get('HERMES_HOME', '~/.hermes'))
    ap.add_argument('--apply', action='store_true', help='Actually write ~/.hermes/config.yaml. Without this, writes merged preview only.')
    args = ap.parse_args()

    home = Path(args.hermes_home).expanduser()
    cfg_path = home / 'config.yaml'
    patch_path = home / 'state' / 'moa-synthesis' / 'config.patch.yaml'
    if not patch_path.exists():
        raise SystemExit(f'Missing patch: {patch_path}. Run tune_panel.py first.')

    config = load_yaml(cfg_path, require_yaml=cfg_path.exists())
    patch = load_yaml(patch_path, require_yaml=True)
    if not patch:
        raise SystemExit(f'Could not parse patch: {patch_path}')
    merged = deep_merge(config, patch)

    out_dir = home / 'state' / 'moa-synthesis'
    out_dir.mkdir(parents=True, exist_ok=True)
    preview = out_dir / 'config.merged.preview.yaml'
    preview.write_text(dump_yaml(merged), encoding='utf-8')
    print(f'Wrote merged preview: {preview}')

    if not args.apply:
        print('Dry run only. Re-run with --apply to write config.yaml with backup.')
        return 0

    if cfg_path.exists():
        backup = home / f'config.yaml.bak-moa-synthesis-{now_stamp()}'
        shutil.copy2(cfg_path, backup)
        print(f'Backup written: {backup}')
    else:
        print('No existing config.yaml; creating new file.')
    cfg_path.write_text(dump_yaml(merged), encoding='utf-8')
    print(f'Applied patch to: {cfg_path}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
