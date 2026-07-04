# Public v3.0.0 to v4.1.0 Audit Notes

These notes describe the gap between the previous public GitHub baseline, v3.0.0, and the operational v4.1.0 package.

## 1. Docs-first baseline

The public v3.0.0 repository was primarily conceptual: `README.md`, `SKILL.md`, `assets/`, `references/playbook.md`, `examples/sanitized-escalation-example.md`, `SECURITY.md`, and `LICENSE`.

That was enough to explain the escalation doctrine, but not enough to operate model discovery, preset generation, config patching, smoke tests, or benchmark gates directly from the repository.

## 2. Manual provider/model handling

v3.0.0 described how an operator should think about panel composition, but did not include a model inventory schema or a discovery script. v4.1.0 adds proof levels for model availability: `configured`, `endpoint`, `env-curated`, and `user-preferred`.

## 3. No executable preset workflow

v3.0.0 treated tuning as an operator workflow. v4.1.0 adds `discover_models.py`, `tune_panel.py`, `apply_patch.py`, and `smoke_test.py`, turning the workflow into repeatable preview/apply/verify steps.

## 4. No benchmark gate

v3.0.0 explained when MoA should be used, but the gate was not backed by an executable benchmark file. v4.1.0 adds `eval_gate.py` and `benchmarks/gate_cases.jsonl` so escalation decisions can be regression-tested.

## 5. Prompt templates were not first-class

v3.0.0 included a sanitized example. v4.1.0 adds reusable advisor and red-team templates so panel briefs can be generated consistently without copying from prose.

## 6. Safety moved from policy to light enforcement

v3.0.0 had useful security guidance. v4.1.0 adds validation, secret-pattern scanning, dry-run patching, backup-before-apply behavior, smoke tests, regression tests, and CI.

## 7. Production readiness

v3.0.0 was a strong blueprint. v4.1.0 is a stronger production baseline because it packages the doctrine with the scripts and tests needed to operate it on a real Hermes server. Operators should still run local validation and smoke tests before applying generated config changes.
