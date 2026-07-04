#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from hermes_config import dump_yaml, load_yaml

STRONG_PROOFS = {'configured', 'endpoint'}


def load_inventory(home: Path) -> Dict[str, Any]:
    path = home / 'state' / 'moa-synthesis' / 'model-inventory.json'
    if not path.exists():
        raise SystemExit(f'Missing inventory: {path}. Run discover_models.py first.')
    return json.loads(path.read_text())


def key(m: Dict[str, Any]) -> str:
    return f"{m.get('provider')}:{m.get('model')}"


def score(m: Dict[str, Any], role: str) -> float:
    s = float(m.get('score') or 0)
    roles = set(m.get('roles') or [])
    if role not in roles:
        s -= 25
    if role in {'aggregator', 'advisor'} and not m.get('moa_supported', True):
        s -= 100
    if m.get('needs_validation'):
        s -= 20
    proof = m.get('proof')
    if proof == 'configured':
        s += 10
    elif proof == 'endpoint':
        s += 5
    elif proof == 'env-curated':
        s -= 8
    elif proof == 'user-preferred':
        s -= 12
    ctx = m.get('context_length')
    if isinstance(ctx, int):
        if ctx >= 128000:
            s += 8
        elif ctx >= 64000:
            s += 5
        else:
            s -= 20
    elif role == 'aggregator':
        s -= 5
    provider = str(m.get('provider') or '')
    model = str(m.get('model') or '').lower()
    if role == 'aggregator':
        if 'gpt-5.5.5' in model:
            s += 12
        elif 'gpt-5.5' in model or 'gpt-5' in model:
            s += 9
        if 'deepseek' in model and ('v4' in model or 'v3' in model):
            s += 8
        if provider == 'custom' or provider.startswith('custom:'):
            s -= 10
    else:
        if 'deepseek' in model:
            s += 7
        if 'gpt-5' in model:
            s += 6
        if provider == 'custom' or provider.startswith('custom:'):
            s -= 5
    return s


def parse_pref(value: str | None) -> Tuple[str, str] | None:
    if not value:
        return None
    if ':' not in value:
        raise SystemExit(f'Expected provider:model, got {value!r}')
    # For forced aggregator we intentionally keep the simple pair semantics used by Hermes docs.
    p, m = value.split(':', 1)
    return p.strip(), m.strip()


def as_moa_pair(m: Dict[str, Any]) -> Dict[str, Any]:
    return {'provider': m['provider'], 'model': m['model']}


def as_fallback_pair(m: Dict[str, Any]) -> Dict[str, Any]:
    provider = m['provider']
    out: Dict[str, Any]
    if provider.startswith('custom:') or provider == 'custom':
        out = {'provider': 'custom', 'model': m['model']}
        for f in ('base_url', 'key_env', 'api_mode'):
            if m.get(f):
                out[f] = m[f]
    else:
        out = {'provider': provider, 'model': m['model']}
    return out


def usable_models(models: List[Dict[str, Any]], allow_unverified: bool, role: str) -> List[Dict[str, Any]]:
    out = []
    for m in models:
        if not (allow_unverified or m.get('proof') in STRONG_PROOFS):
            continue
        if role in {'aggregator', 'advisor'} and not m.get('moa_supported', True):
            continue
        if role == 'fallback' and not m.get('fallback_supported', True):
            continue
        out.append(m)
    return out


def choose(models: List[Dict[str, Any]], allow_unverified: bool, max_advisors: int, prefer_agg: Tuple[str,str] | None):
    moa_usable = usable_models(models, allow_unverified, 'aggregator')
    if not moa_usable:
        raise SystemExit('No MoA-safe verified models available. Configure providers with `hermes model`, or rerun with --allow-unverified for preview only.')

    if prefer_agg:
        matches = [m for m in moa_usable if m.get('provider') == prefer_agg[0] and m.get('model') == prefer_agg[1]]
        if matches:
            aggregator = matches[0]
        else:
            raise SystemExit(f'Preferred aggregator {prefer_agg[0]}:{prefer_agg[1]} not found in usable MoA inventory.')
    else:
        aggregator = sorted(moa_usable, key=lambda m: score(m, 'aggregator'), reverse=True)[0]

    advisor_usable = usable_models(models, allow_unverified, 'advisor')
    advisors = []
    for m in sorted(advisor_usable, key=lambda x: score(x, 'advisor'), reverse=True):
        if key(m) == key(aggregator) and (m.get('base_url') or '') == (aggregator.get('base_url') or ''):
            continue
        advisors.append(m)
        if len(advisors) >= max_advisors:
            break

    if not advisors:
        raise SystemExit('Need at least one MoA-safe advisor distinct from the aggregator. Configure another provider/model or use single-model mode.')

    fallback_usable = usable_models(models, allow_unverified, 'fallback')
    fallbacks = []
    for m in sorted(fallback_usable, key=lambda x: score(x, 'aggregator'), reverse=True):
        if key(m) == key(aggregator):
            continue
        if any(key(m) == key(a) for a in advisors):
            continue
        fallbacks.append(m)
        if len(fallbacks) >= 3:
            break
    return aggregator, advisors, fallbacks


def main() -> int:
    ap = argparse.ArgumentParser(description='Generate preview Hermes MoA preset and fallback config patch.')
    ap.add_argument('--hermes-home', default=os.environ.get('HERMES_HOME', '~/.hermes'))
    ap.add_argument('--preset-name', default='moa-synthesis-auto')
    ap.add_argument('--max-advisors', type=int, default=2)
    ap.add_argument('--reference-max-tokens', type=int, default=600)
    ap.add_argument('--allow-unverified', action='store_true', help='Allow user-preferred/env-curated names in preview. Run smoke test before applying.')
    ap.add_argument('--prefer-aggregator', help='Force aggregator provider:model if present.')
    ap.add_argument('--write-preview', action='store_true', default=True)
    ap.add_argument('--include-provider-routing', action='store_true', help='Also write provider_routing recommendations into the config patch. Off by default because provider_routing is global.')
    args = ap.parse_args()

    home = Path(args.hermes_home).expanduser()
    inv = load_inventory(home)
    models = inv.get('models') or []
    aggregator, advisors, fallbacks = choose(models, args.allow_unverified, args.max_advisors, parse_pref(args.prefer_aggregator))

    uses_openrouter = any(m.get('provider') == 'openrouter' for m in [aggregator] + advisors + fallbacks)

    patch: Dict[str, Any] = {
        'moa': {
            'default_preset': args.preset_name,
            'presets': {
                args.preset_name: {
                    'reference_models': [as_moa_pair(m) for m in advisors],
                    'aggregator': as_moa_pair(aggregator),
                    'reference_max_tokens': args.reference_max_tokens,
                    'max_tokens': 4096,
                    'enabled': True,
                }
            }
        },
        # Keep the config patch limited to Hermes-recognized runtime keys.
        # Operational metadata remains in model-inventory.json and tuning-report.md.
    }
    if fallbacks:
        patch['fallback_providers'] = [as_fallback_pair(m) for m in fallbacks]
    if uses_openrouter and args.include_provider_routing:
        patch['provider_routing'] = {'sort': 'latency', 'require_parameters': True, 'data_collection': 'deny'}

    out_dir = home / 'state' / 'moa-synthesis'
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / 'config.patch.yaml'
    out.write_text(dump_yaml(patch), encoding='utf-8')

    report = out_dir / 'tuning-report.md'
    report.write_text('\n'.join([
        '# MoA Synthesis Tuning Report',
        '',
        f'- Preset: `{args.preset_name}`',
        f'- Aggregator: `{key(aggregator)}` proof=`{aggregator.get("proof")}`',
        '- Advisors:',
        *[f'  - `{key(a)}` proof=`{a.get("proof")}`' for a in advisors],
        '- Fallbacks:',
        *([f'  - `{key(f)}` proof=`{f.get("proof")}`' for f in fallbacks] or ['  - none generated']),
        '',
        ('OpenRouter provider_routing was included in the patch.' if args.include_provider_routing and uses_openrouter else 'OpenRouter provider_routing was NOT written by default; add --include-provider-routing if you want that global config change.'),
        'Review `config.patch.yaml`, run `apply_patch.py` in dry-run mode, then run `smoke_test.py` before production use.',
    ]) + '\n', encoding='utf-8')

    print(f'Wrote MoA config preview: {out}')
    print(f'Wrote tuning report: {report}')
    print(f'Aggregator: {key(aggregator)} proof={aggregator.get("proof")}')
    print('Advisors:')
    for a in advisors:
        print(f' - {key(a)} proof={a.get("proof")}')
    if fallbacks:
        print('Fallbacks:')
        for f in fallbacks:
            print(f' - {key(f)} proof={f.get("proof")}')
    if args.allow_unverified:
        print('WARNING: Patch may include unverified preferred/curated models. Run smoke_test.py before production use.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
