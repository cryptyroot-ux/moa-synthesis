# Provider and Model Policy

## Availability Proof Levels

MoA Synthesis v4 distinguishes model names by proof:

- `configured`: found in `config.yaml` as the main model, fallback, or MoA preset.
- `endpoint`: returned by an OpenAI-compatible `/v1/models` endpoint.
- `env-curated`: inferred from credential presence plus a curated catalog. Useful but not proof.
- `user-preferred`: provided by the operator via `--preferred`; not proof.

Safe patch generation uses only `configured` and `endpoint` unless `--allow-unverified` is set.

## MoA vs Fallback Custom Providers

Hermes MoA presets store explicit provider/model pairs. Named custom providers should be represented as `custom:<name>` when they are intended to be selected as a model provider.

Hermes fallback providers support custom endpoints using:

```yaml
fallback_providers:
  - provider: custom
    model: my-local-model
    base_url: http://localhost:8000/v1
    key_env: MY_LOCAL_KEY
```

Therefore v4 stores named custom providers in inventory as `custom:<name>` for MoA use, but emits fallback entries as `provider: custom` plus `base_url`.

Ad-hoc local endpoints discovered from `--base-url` or `localhost:11434` are fallback-only until the operator adds them to `model:` or `custom_providers:` in `config.yaml`.

## Aggregator Policy

The aggregator should be:

- tool-reliable;
- context-safe for Hermes agent use;
- strongly instruction-following;
- configured or endpoint-proven;
- not merely user-preferred.

## Advisor Policy

Advisors should be high-quality and independent. A two-model panel with strong models is usually better than a noisy large panel.

## Fallback Policy

Generated fallbacks are appended to existing fallback providers, not used to replace the operator's chain.
