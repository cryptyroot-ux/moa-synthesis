# Changelog

## v4.1.0 — changes from public GitHub v3.0.0

This changelog intentionally lists only the delta from the previous public GitHub baseline, v3.0.0.

### Changed

- Repositioned the project from a docs-first MoA escalation doctrine into an installable Hermes skill plus operator toolkit.
- Expanded the repository layout from `README.md`, `SKILL.md`, `assets/`, `references/`, one sanitized example, `SECURITY.md`, and `LICENSE` into a full skill package with `scripts/`, `templates/`, `schemas/`, `benchmarks/`, `tests/`, and CI.
- Made model/provider handling proof-aware: configured, endpoint-discovered, env-curated, and user-preferred candidates are treated differently.
- Kept Hermes native MoA as the execution engine; MoA Synthesis remains the decision, tuning, verification, and rollback discipline above it.

### Added

- `scripts/discover_models.py` for model/provider discovery.
- `scripts/tune_panel.py` for MoA preset preview generation.
- `scripts/apply_patch.py` for dry-run, backup, and explicit apply workflows.
- `scripts/smoke_test.py` for validating config, patch, and merged config sources.
- `scripts/eval_gate.py` and `benchmarks/gate_cases.jsonl` for testing the escalation gate.
- `scripts/validate_skill.py` for package validation and lightweight safety checks.
- `scripts/hermes_config.py` for shared config parsing/merge behavior.
- `templates/advisor-brief.md` and `templates/red-team-brief.md` for reusable sanitized panel prompts.
- `schemas/model_inventory.schema.json` for model inventory structure.
- `references/provider-model-policy.md`, `references/hermes-skill-compatibility.md`, and `references/audit-v3-findings.md`.
- `.github/workflows/ci.yml` plus `tests/test_regressions.py`.

### Safety

- Unverified preferred model names are not used in safe config patches unless the operator explicitly opts in with `--allow-unverified`.
- Config changes are preview-first and apply only with an explicit `--apply` flag.
- Apply workflow creates backups before modifying the Hermes config.
- Smoke tests and regression tests protect against silent config breakage.

### Unchanged

- Hermes native MoA remains the execution mechanism.
- Routine low-risk tasks should still stay single-model for speed and cost control.
- The core workflow remains: gate → brief → advise → aggregate → verify → report or roll back.
