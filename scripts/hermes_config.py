#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

HAVE_YAML = yaml is not None


def now_stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d-%H%M%S')


def load_dotenv_keys(path: Path) -> set[str]:
    keys: set[str] = set()
    if not path.exists():
        return keys
    for raw in path.read_text(errors='ignore').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key = line.split('=', 1)[0].strip()
        if key:
            keys.add(key)
    return keys


def load_json_keys(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(errors='ignore'))
    except Exception:
        return set()
    keys: set[str] = set()
    if isinstance(data, dict):
        keys.update(str(k) for k in data.keys())
        for k, v in data.items():
            if isinstance(v, dict):
                keys.update(f'{k}.{sub}' for sub in v.keys())
    return keys


def load_yaml(path: Path, *, require_yaml: bool = False) -> Dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(errors='ignore')
    if yaml is None:
        try:
            data = json.loads(text)
            return data if isinstance(data, dict) else {}
        except Exception:
            if require_yaml:
                raise RuntimeError(
                    f'PyYAML is required to parse {path}. Install with: python3 -m pip install pyyaml'
                )
            return {}
    try:
        data = yaml.safe_load(text) or {}
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        if require_yaml:
            raise RuntimeError(f'Could not parse YAML file {path}: {exc}') from exc
        return {}


def _scalar(value: Any) -> str:
    if value is True:
        return 'true'
    if value is False:
        return 'false'
    if value is None:
        return 'null'
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value)
    if s == '' or any(c in s for c in ':#{}[]&,*?|-<>=!%@`') or s.lower() in {'true','false','null','yes','no','on','off'}:
        return json.dumps(s, ensure_ascii=False)
    return s


def dump_yaml(data: Dict[str, Any]) -> str:
    if yaml is not None:
        return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)

    def emit(obj: Any, indent: int = 0) -> List[str]:
        pad = ' ' * indent
        lines: List[str] = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    lines.append(f'{pad}{k}:')
                    lines.extend(emit(v, indent + 2))
                else:
                    lines.append(f'{pad}{k}: {_scalar(v)}')
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, dict):
                    # Compact first scalar keys are harder to render without PyYAML; keep valid block form.
                    lines.append(f'{pad}-')
                    lines.extend(emit(item, indent + 2))
                elif isinstance(item, list):
                    lines.append(f'{pad}-')
                    lines.extend(emit(item, indent + 2))
                else:
                    lines.append(f'{pad}- {_scalar(item)}')
        else:
            lines.append(f'{pad}{_scalar(obj)}')
        return lines
    return '\n'.join(emit(data)) + '\n'


def _identity_for_list_item(key_name: str, item: Dict[str, Any]) -> Tuple[Any, ...]:
    if key_name == 'fallback_providers':
        return (item.get('provider'), item.get('model'), item.get('base_url'), item.get('key_env'))
    if key_name == 'custom_providers':
        return (item.get('name'), item.get('base_url'))
    return tuple(sorted(item.items()))


def merge_named_list(key_name: str, base_list: list, patch_list: list) -> list:
    """Merge config lists without destroying existing user-managed entries."""
    out: list = []
    seen: set[Tuple[Any, ...]] = set()
    for item in base_list + patch_list:
        if not isinstance(item, dict):
            ident = (repr(item),)
        else:
            ident = _identity_for_list_item(key_name, item)
        if ident in seen:
            continue
        seen.add(ident)
        out.append(item)
    return out


def deep_merge(base: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for k, v in patch.items():
        if k in {'fallback_providers', 'custom_providers'} and isinstance(v, list) and isinstance(out.get(k), list):
            out[k] = merge_named_list(k, out[k], v)
        elif isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def provider_model_key(provider: str, model: str, base_url: str | None = None) -> Tuple[str, str, str]:
    return (provider.strip(), model.strip(), (base_url or '').strip())


def normalize_custom_name(name: str) -> str:
    name = str(name or '').strip()
    return name.replace(' ', '-').lower()


def split_provider_model(value: str, custom_names: Iterable[str] | None = None) -> Tuple[str, str]:
    """Parse provider:model, preserving named custom providers and model tags.

    Examples:
    - openrouter:deepseek/deepseek-v4-pro -> openrouter, deepseek/deepseek-v4-pro
    - custom:local:qwen3:4b with custom_names={local} -> custom:local, qwen3:4b
    - custom:qwen3:4b -> custom, qwen3:4b
    """
    if ':' not in value:
        raise ValueError(f'Expected provider:model, got {value!r}')
    parts = value.split(':')
    if parts[0] == 'custom' and len(parts) >= 3:
        names = set(custom_names or [])
        if parts[1] in names:
            provider = f'custom:{parts[1]}'
            model = ':'.join(parts[2:])
        else:
            provider = 'custom'
            model = ':'.join(parts[1:])
    else:
        provider, model = value.split(':', 1)
    provider = provider.strip()
    model = model.strip()
    if not provider or not model:
        raise ValueError(f'Expected provider:model, got {value!r}')
    return provider, model
