# MoA Synthesis v4.1

**Risk-gated Mixture-of-Agents escalation for Hermes Agent — now packaged as an operational skill toolkit.**

MoA Synthesis is not an MoA engine. Hermes native MoA remains the execution mechanism: reference models run first, then the aggregator acts, writes the final answer, and performs tool calls. This repository provides the discipline above that engine: when to escalate, how to brief advisors, how to choose and verify model/provider combinations, how to generate safe MoA presets, and how to validate or roll back config changes.

This release documents the practical delta from the previous public GitHub baseline, **v3.0.0**, to **v4.1.0**.

![MoA Synthesis workflow](assets/moa-synthesis-flow.jpg)

## Short version

- **GitHub v3.0.0** was a conceptual, docs-first skill: `README.md`, `SKILL.md`, `assets/`, `references/playbook.md`, one sanitized example, `SECURITY.md`, and `LICENSE`.
- **v4.1.0** is the same doctrine turned into an installable Hermes skill plus an operator toolkit: scripts, templates, schemas, benchmarks, tests, CI, dry-run/apply/backup workflow, smoke tests, and benchmark gates.

v3.0.0 answered: **“When should Hermes use MoA?”**

v4.1.0 answers: **“When should Hermes use MoA, which available models should form the panel, what preset should be generated, how should the patch be tested, and how can the operator roll back safely?”**

## v4.1.0 vs public GitHub v3.0.0

| Area | Public v3.0.0 | v4.1.0 | Why it matters |
|---|---|---|---|
| Form | Markdown skill plus playbook. | Hermes skill package plus operator toolkit. | Moves from doctrine to executable operations. |
| Goal | Teach Hermes when MoA escalation is warranted. | Teach escalation and help configure/test MoA automatically. | Reduces manual config drift and operator guesswork. |
| MoA engine | Hermes native MoA. | Hermes native MoA. | The engine stays upstream-compatible; this skill remains the discipline layer. |
| Provider/model discovery | Manual / conceptual. | `scripts/discover_models.py`. | Finds configured, endpoint-listed, curated, and preferred model candidates with proof levels. |
| MoA preset generation | Described as a workflow. | `scripts/tune_panel.py` generates preview config patches. | Produces repeatable panel composition instead of hand-written YAML. |
| Config apply workflow | Manual edits. | `scripts/apply_patch.py` with dry-run, backup, and explicit `--apply`. | Safer operations: preview first, apply only after review, rollback path preserved. |
| Config validation | Manual review. | `scripts/smoke_test.py` with config/patch/merged sources. | Lets operators validate generated presets before touching production config. |
| Escalation benchmark gate | Not included. | `scripts/eval_gate.py` plus `benchmarks/gate_cases.jsonl`. | Makes the “when to escalate” gate testable rather than purely narrative. |
| Advisor/red-team prompts | General example only. | `templates/advisor-brief.md` and `templates/red-team-brief.md`. | Standardizes sanitized briefs for L1/L2/L3 reviews. |
| Hermes skill structure | Basic `SKILL.md` + references. | `SKILL.md`, `references/`, `templates/`, `scripts/`, `schemas/`, `benchmarks/`, `tests/`, CI. | Better fit for modern Hermes skill taps and maintainability. |
| Model/provider policy | Conceptual examples. | `references/provider-model-policy.md` plus inventory schema. | Prevents unverified model names from silently becoming production routes. |
| Safety | Security guidance. | Guidance plus validation, secret-pattern checks, tests, dry-run, backup, and CI. | Converts safety advice into lightweight enforcement. |
| Production readiness | Good blueprint. | More production-ready baseline, still requiring local smoke tests. | Suitable for real Hermes servers after operator validation. |

## Model/provider availability handling

v4.1.0 is deliberately conservative. It separates model candidates by proof level:

| Proof level | Meaning |
|---|---|
| `configured` | Found in Hermes config. |
| `endpoint` | Found from a provider `/v1/models` style endpoint. |
| `env-curated` | Provider credentials/config exist and the model is from a curated list, but it was not endpoint-probed. |
| `user-preferred` | The operator explicitly requested the model name, but availability is not proven yet. |

Unverified preferred models are visible in inventory, but safe patch generation does **not** use them unless the operator explicitly passes `--allow-unverified`.

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
PYTHONPYCACHEPREFIX=/tmp/moa-synthesis-pycache python3 -m py_compile scripts/*.py tests/*.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/eval_gate.py benchmarks/gate_cases.jsonl
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_regressions.py
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

Apply only after operator review:

```bash
python3 scripts/apply_patch.py --hermes-home ~/.hermes --apply
python3 scripts/smoke_test.py --hermes-home ~/.hermes --source config --preset moa-synthesis-auto
```

## Positioning

MoA Synthesis is about engineering discipline for tool-using agents: escalation gates, separation between advisors and the acting aggregator, sanitized briefs, verification, traceability, rollback, and cost control. It intentionally avoids turning every task into a multi-model panel.
