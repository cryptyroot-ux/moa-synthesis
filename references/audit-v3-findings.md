# Audit Findings from v3 to v4

## 1. Over-restrictive skill discovery

v3 declared `requires_toolsets: [delegation, skills]`. Hermes hides skills when required toolsets are unavailable, so this could make the skill disappear exactly when an operator needed to inspect its playbook. v4 removes `requires_toolsets` and keeps tool requirements inside the procedure.

## 2. Fallback list replacement

v3 generated a `fallback_providers` patch, and `apply_patch.py` deep-merged it by replacing lists. This could remove existing fallback entries. v4 merges `fallback_providers` by provider/model/base_url/key_env identity, preserving existing entries and appending managed ones.

## 3. Smoke test source limitation

v3 smoke-tested only `config.yaml`, which meant the normal preview workflow could not be validated before applying. v4 supports `--source auto|config|patch|merged`.

## 4. Named custom provider ambiguity

v3 represented custom providers too generically. v4 preserves named custom providers as `custom:<name>` for MoA use and emits `provider: custom` + `base_url` for fallback use, matching Hermes' documented distinction between named custom model selection and custom endpoint fallback.

## 5. YAML dependency clarity

v3 could silently treat YAML config as empty if PyYAML was not available. v4 raises a clear error when parsing real Hermes YAML requires PyYAML.

## 6. Regression tests

v4 adds `tests/test_regressions.py` to verify that unverified preferred models do not leak into safe patches, existing fallbacks survive apply, and empty configs do not generate fake production patches.
