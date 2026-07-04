# MoA Synthesis v4.1

**Risk-gated Mixture-of-Agents escalation for Hermes Agent.**

MoA Synthesis is a Hermes Agent skill and operator toolkit for deciding when a task should stay single-model and when it deserves a structured Mixture-of-Agents review. Hermes native MoA remains the execution engine; this repository provides the escalation gate, advisor brief discipline, model/provider tuning helpers, verification workflow, and rollback-aware config tooling around it.

This update documents the delta from the previous public GitHub version, **v3.0.0**, to **v4.1.0**.

![MoA Synthesis workflow](assets/moa-synthesis-flow.jpg)

## v4.1.0 vs v3.0.0

v3.0.0 introduced the production operator toolkit: provider discovery, panel tuning, config patch generation, smoke tests, eval gates, and a provider/model policy. v4.1.0 keeps that architecture and hardens the operational edges found during the v3 audit.

| Area | v3.0.0 behavior | v4.1.0 change | Why it matters |
|---|---|---|---|
| Skill discoverability | Declared required toolsets in metadata. | Removed hard `requires_toolsets` from skill metadata; tool needs live inside the procedure instead. | Prevents Hermes from hiding the skill on surfaces where the operator still needs to inspect the playbook. |
| Fallback provider handling | Deep-merge logic could replace the existing `fallback_providers` list. | `apply_patch.py` now preserves existing fallbacks and appends managed entries by provider/model/base URL/key identity. | Safer config updates: existing recovery paths are not accidentally removed. |
| Smoke-test workflow | `smoke_test.py` validated only the live config source. | Smoke tests now support `--source auto`, `config`, `patch`, and `merged`. | Lets operators validate generated previews before applying them to the real config. |
| Custom provider representation | Custom providers were represented too generically. | Named custom providers are preserved as `custom:<name>` for MoA selection; fallback endpoints use `provider: custom` plus `base_url`. | Matches Hermes provider semantics more closely and avoids ambiguous routing. |
| YAML dependency failures | Missing PyYAML could make a real YAML config look empty. | Config parsing now fails clearly when YAML support is required but unavailable. | Avoids generating misleading patches from an accidentally empty config. |
| Regression protection | No dedicated regression suite for the v3 audit findings. | Added `tests/test_regressions.py`. | Locks in key safety properties: unverified preferred models do not enter safe patches, existing fallbacks survive apply, and empty configs do not produce fake production patches. |
| Advisor discipline | Briefing guidance lived mostly in the playbook. | Added `templates/advisor-brief.md` and `templates/red-team-brief.md`. | Makes L1/L2/L3 escalation prompts easier to reuse consistently and safely. |
| Hermes skill compatibility | Functional, but less explicit about package structure and validation expectations. | Added compatibility notes and stricter validation around supported skill layout. | Easier to install, inspect, validate, and maintain as a Hermes skill. |

## What did not change

- MoA Synthesis is still **not** an MoA engine.
- Hermes native MoA still performs the reference-model fan-out, aggregator call, tool loop, and traceable execution.
- The core operating model remains: gate → brief → advise → aggregate → verify → rollback/report when needed.
- Normal low-risk work should remain single-model for speed and cost control.

## Repository contents

```text
.
├── SKILL.md
├── README.md
├── SECURITY.md
├── LICENSE
├── assets/
│   └── moa-synthesis-flow.jpg
├── benchmarks/
│   └── gate_cases.jsonl
├── examples/
│   ├── config.patch.example.yaml
│   ├── sample-hermes-config.yaml
│   └── sanitized-escalation-example.md
├── references/
│   ├── audit-v3-findings.md
│   ├── hermes-skill-compatibility.md
│   ├── playbook-v4.md
│   └── provider-model-policy.md
├── schemas/
│   └── model_inventory.schema.json
├── scripts/
│   ├── apply_patch.py
│   ├── discover_models.py
│   ├── eval_gate.py
│   ├── hermes_config.py
│   ├── smoke_test.py
│   ├── tune_panel.py
│   └── validate_skill.py
├── templates/
│   ├── advisor-brief.md
│   └── red-team-brief.md
└── tests/
    └── test_regressions.py
```

## Quick validation

From the repository root:

```bash
python3 scripts/validate_skill.py .
python3 -m py_compile scripts/*.py tests/*.py
python3 scripts/eval_gate.py benchmarks/gate_cases.jsonl
python3 tests/test_regressions.py
```

Expected result: validation passes, gate cases pass, and regression tests pass.

## Safe config workflow

Preview before apply:

```bash
python3 scripts/discover_models.py --hermes-home ~/.hermes
python3 scripts/tune_panel.py --hermes-home ~/.hermes --write-preview
python3 scripts/apply_patch.py --hermes-home ~/.hermes
python3 scripts/smoke_test.py --hermes-home ~/.hermes --source merged --preset moa-synthesis-auto
```

Apply only after review:

```bash
python3 scripts/apply_patch.py --hermes-home ~/.hermes --apply
python3 scripts/smoke_test.py --hermes-home ~/.hermes --source config --preset moa-synthesis-auto
```

## Positioning

This project is about engineering discipline for tool-using agents: escalation gates, separation between advisors and the acting aggregator, sanitized briefs, verification, traceability, rollback, and cost control. It intentionally avoids turning every task into a multi-model panel.
