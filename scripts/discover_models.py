#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from hermes_config import (
    load_dotenv_keys,
    load_json_keys,
    load_yaml,
    normalize_custom_name,
    provider_model_key,
    split_provider_model,
)

PROVIDER_ENVS = {
    'openrouter': ['OPENROUTER_API_KEY'],
    'anthropic': ['ANTHROPIC_API_KEY', 'ANTHROPIC_TOKEN'],
    'deepseek': ['DEEPSEEK_API_KEY'],
    'gemini': ['GOOGLE_API_KEY', 'GEMINI_API_KEY'],
    'zai': ['GLM_API_KEY'],
    'minimax': ['MINIMAX_API_KEY'],
    'ollama-cloud': ['OLLAMA_API_KEY'],
    'xai': ['XAI_API_KEY'],
    'nvidia': ['NVIDIA_API_KEY'],
    'huggingface': ['HF_TOKEN'],
    'openai-api': ['OPENAI_API_KEY'],
    'copilot': ['COPILOT_GITHUB_TOKEN', 'GH_TOKEN', 'GITHUB_TOKEN'],
}

AUTH_MARKERS = {
    'openai-codex': ['codex', 'openai-codex', 'codex-oauth'],
    'nous': ['nous', 'portal'],
    'anthropic': ['anthropic', 'claude'],
    'xai': ['xai', 'grok'],
    'qwen-oauth': ['qwen', 'qwen-oauth'],
}

CURATED_MODELS = {
    'openrouter': [
        ('deepseek/deepseek-v4-pro', 98, ['aggregator', 'advisor']),
        ('openai/gpt-5.5', 96, ['aggregator', 'advisor']),
        ('anthropic/claude-opus-4.8', 97, ['aggregator', 'advisor']),
        ('anthropic/claude-sonnet-4.6', 92, ['aggregator', 'advisor']),
    ],
    'deepseek': [
        ('deepseek-v4-pro', 95, ['aggregator', 'advisor']),
        ('deepseek-chat', 80, ['advisor', 'fallback']),
    ],
    'anthropic': [
        ('claude-opus-4-8', 97, ['aggregator', 'advisor']),
        ('claude-sonnet-4-6', 92, ['aggregator', 'advisor']),
    ],
    'openai-codex': [
        ('gpt-5.5', 96, ['aggregator', 'advisor']),
    ],
    'ollama-cloud': [
        ('qwen3-coder:480b-cloud', 88, ['advisor']),
        ('gpt-oss:120b', 82, ['fallback', 'advisor']),
    ],
}

SAFE_CUSTOM_NAME = re.compile(r'^[A-Za-z0-9_.-]+$')


def endpoint_models(base_url: str, api_key: Optional[str] = None, timeout: int = 5) -> List[str]:
    url = base_url.rstrip('/') + '/models'
    headers = {'Accept': 'application/json'}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    try:
        with urlopen(Request(url, headers=headers), timeout=timeout) as resp:
            data = json.loads(resp.read().decode('utf-8', errors='replace'))
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        return []
    models = []
    for item in data.get('data', []):
        if isinstance(item, dict) and item.get('id'):
            models.append(str(item['id']))
    return sorted(set(models))


def auth_present(provider: str, env_keys: set[str], auth_keys: set[str]) -> bool:
    if any(e in env_keys for e in PROVIDER_ENVS.get(provider, [])):
        return True
    markers = AUTH_MARKERS.get(provider, [])
    return any(any(marker in key.lower() for marker in markers) for key in auth_keys)


def main() -> int:
    ap = argparse.ArgumentParser(description='Discover Hermes provider/model candidates without storing secrets.')
    ap.add_argument('--hermes-home', default=os.environ.get('HERMES_HOME', '~/.hermes'))
    ap.add_argument('--preferred', action='append', default=[], help='Add preferred provider:model candidate; unverified unless already configured/discovered.')
    ap.add_argument('--base-url', action='append', default=[], help='Probe extra OpenAI-compatible endpoint URL.')
    ap.add_argument('--no-trust-env-curated', action='store_true', help='Do not seed curated model names just from credential presence.')
    args = ap.parse_args()

    home = Path(args.hermes_home).expanduser()
    cfg = load_yaml(home / 'config.yaml', require_yaml=(home / 'config.yaml').exists())
    env_keys = load_dotenv_keys(home / '.env') | set(os.environ.keys())
    auth_keys = load_json_keys(home / 'auth.json')
    models: List[Dict[str, Any]] = []
    seen = set()

    configured_custom_names = set()
    for cp in cfg.get('custom_providers') or []:
        if isinstance(cp, dict) and cp.get('name'):
            configured_custom_names.add(normalize_custom_name(str(cp.get('name'))))
            configured_custom_names.add(str(cp.get('name')).strip())

    def add(provider: str, model: str, source: str, proof: str, **kw: Any) -> None:
        if not provider or not model:
            return
        provider = provider.strip()
        model = model.strip()
        key = provider_model_key(provider, model, kw.get('base_url'))
        if key in seen:
            return
        seen.add(key)
        is_custom = provider == 'custom' or provider.startswith('custom:')
        moa_supported = bool(kw.get('moa_supported'))
        if not is_custom:
            moa_supported = True
        rec = {
            'provider': provider,
            'model': model,
            'source': source,
            'proof': proof,
            'base_url': kw.get('base_url'),
            'key_env': kw.get('key_env'),
            'api_mode': kw.get('api_mode'),
            'context_length': kw.get('context_length'),
            'supports_tools': kw.get('supports_tools'),
            'supports_vision': kw.get('supports_vision'),
            'score': kw.get('score', 50),
            'roles': kw.get('roles', ['fallback']),
            'moa_supported': moa_supported,
            'fallback_supported': bool(kw.get('fallback_supported', True)),
            'needs_validation': proof in {'user-preferred', 'env-curated'},
            'warnings': kw.get('warnings', []),
        }
        models.append(rec)

    # Main model
    mcfg = cfg.get('model') if isinstance(cfg.get('model'), dict) else {}
    if isinstance(mcfg, dict):
        provider = str(mcfg.get('provider') or '').strip()
        model = str(mcfg.get('default') or mcfg.get('model') or '').strip()
        if provider and model:
            add(
                provider,
                model,
                'config.model',
                'configured',
                base_url=mcfg.get('base_url'),
                api_mode=mcfg.get('api_mode'),
                context_length=mcfg.get('context_length'),
                score=86,
                roles=['aggregator', 'fallback'],
                moa_supported=(provider != 'custom' or bool(mcfg.get('base_url'))),
            )

    # Fallback providers
    for fp in cfg.get('fallback_providers') or []:
        if isinstance(fp, dict):
            provider = str(fp.get('provider') or '')
            roles = ['fallback', 'advisor'] if provider != 'custom' else ['fallback']
            add(
                provider,
                str(fp.get('model') or ''),
                'config.fallback_providers',
                'configured',
                base_url=fp.get('base_url'),
                key_env=fp.get('key_env'),
                api_mode=fp.get('api_mode'),
                score=78,
                roles=roles,
                moa_supported=(provider != 'custom'),
            )
    legacy = cfg.get('fallback_model')
    if isinstance(legacy, dict):
        add(str(legacy.get('provider') or ''), str(legacy.get('model') or ''), 'config.fallback_model', 'configured', score=72, roles=['fallback'])

    # Existing MoA presets
    moa = cfg.get('moa') if isinstance(cfg.get('moa'), dict) else {}
    presets = moa.get('presets') if isinstance(moa.get('presets'), dict) else {}
    for pname, preset in presets.items():
        if not isinstance(preset, dict):
            continue
        agg = preset.get('aggregator')
        if isinstance(agg, dict):
            add(str(agg.get('provider') or ''), str(agg.get('model') or ''), f'config.moa.presets.{pname}.aggregator', 'configured', score=90, roles=['aggregator','fallback'], moa_supported=True)
        for ref in preset.get('reference_models') or []:
            if isinstance(ref, dict):
                add(str(ref.get('provider') or ''), str(ref.get('model') or ''), f'config.moa.presets.{pname}.reference_models', 'configured', score=84, roles=['advisor'], moa_supported=True)

    # Named custom providers.
    for cp in cfg.get('custom_providers') or []:
        if not isinstance(cp, dict):
            continue
        raw_name = str(cp.get('name') or 'custom').strip()
        name = normalize_custom_name(raw_name)
        base_url = str(cp.get('base_url') or '').strip()
        key_env = cp.get('key_env')
        api_key = os.environ.get(str(key_env)) if key_env else None
        api_mode = cp.get('api_mode')
        provider_id = f'custom:{name}'
        name_safe = bool(SAFE_CUSTOM_NAME.match(name))
        warning = [] if name_safe else [f'Custom provider name {raw_name!r} is not a simple identifier; run hermes model to verify provider id.']
        for mid, meta in (cp.get('models') or {}).items():
            ctx = meta.get('context_length') if isinstance(meta, dict) else None
            add(provider_id, str(mid), f'custom_providers.{raw_name}.models', 'configured', base_url=base_url, key_env=key_env, api_mode=api_mode, context_length=ctx, score=64, roles=['fallback','advisor'], moa_supported=name_safe, warnings=warning)
        if base_url:
            for mid in endpoint_models(base_url, api_key=api_key):
                add(provider_id, mid, f'custom_providers.{raw_name}./models', 'endpoint', base_url=base_url, key_env=key_env, api_mode=api_mode, score=62, roles=['fallback','advisor'], moa_supported=name_safe, warnings=warning)

    # Local Ollama if reachable. This is fallback-only unless configured as model/custom_provider.
    for mid in endpoint_models('http://localhost:11434/v1'):
        add('custom', mid, 'ollama-local./models', 'endpoint', base_url='http://localhost:11434/v1', context_length=None, score=58, roles=['fallback'], moa_supported=False, warnings=['Fallback-only unless configured as model/custom_providers. Verify OLLAMA_CONTEXT_LENGTH >= 64000 server-side.'])

    # Extra endpoints are fallback-only unless operator creates a named custom provider.
    for url in args.base_url:
        for mid in endpoint_models(url):
            add('custom', mid, f'cli-base-url:{url}', 'endpoint', base_url=url, score=60, roles=['fallback'], moa_supported=False, warnings=['Fallback-only until added as a named custom provider in config.yaml.'])

    # Seed curated provider models only when credential exists, unless disabled.
    if not args.no_trust_env_curated:
        for provider in sorted(set(PROVIDER_ENVS) | set(AUTH_MARKERS)):
            if auth_present(provider, env_keys, auth_keys):
                for mid, score, roles in CURATED_MODELS.get(provider, []):
                    add(provider, mid, 'credential-present-curated-list', 'env-curated', score=score, roles=roles, context_length=64000, supports_tools=True, moa_supported=True)

    # Explicit user preferences.
    for pref in args.preferred:
        provider, model = split_provider_model(pref, custom_names=configured_custom_names)
        add(provider, model, 'cli-preferred', 'user-preferred', score=88, roles=['aggregator','advisor','fallback'], context_length=64000, supports_tools=True, moa_supported=(provider != 'custom'), warnings=['User-preferred model name; run smoke test before production use.'])

    inventory = {
        'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'hermes_home': str(home),
        'model_count': len(models),
        'models': sorted(models, key=lambda m: (m['proof'] != 'configured', not m.get('moa_supported', False), m.get('needs_validation', False), -(m.get('score') or 0), m['provider'], m['model'])),
        'notes': [
            'Secret values are never written.',
            'proof=configured or endpoint is stronger than env-curated or user-preferred.',
            'Custom endpoints are only MoA-safe when configured as model or named custom_providers.',
            'Use tune_panel.py without --allow-unverified for safer production patches.',
        ],
    }
    out_dir = home / 'state' / 'moa-synthesis'
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / 'model-inventory.json'
    out.write_text(json.dumps(inventory, indent=2), encoding='utf-8')
    print(f'Wrote sanitized model inventory: {out}')
    print(f'Discovered {len(models)} candidates.')
    if not models:
        print('No candidates found. Configure providers with `hermes model`, or pass --preferred provider:model for an experimental preview.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
