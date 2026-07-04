---
name: moa-synthesis
version: 4.1.0
description: Risk-gated MoA escalation and model auto-tuning
platforms: [linux, macos]
metadata:
  hermes:
    category: orchestration
    tags: [mixture-of-agents, model-routing, provider-routing, agent-safety, decision-governance]
---

# MoA Synthesis

MoA Synthesis is a Hermes Agent skill for deciding when to stay single-model and when to escalate to Hermes native Mixture-of-Agents. It is not an MoA engine. Hermes native MoA is the execution mechanism; this skill is the decision, tuning, verification, and rollback discipline above it.

## When to Use

Use this skill when any condition is true:

- the user asks for the best, safest, most robust, production-ready, or graded answer;
- the decision affects architecture, security, deployment, data migration, provider routing, cost, reliability, or irreversible state;
- multiple defensible approaches exist and the wrong choice is expensive to reverse;
- a single-model answer is uncertain, contradictory, under-evidenced, or fails verification;
- the output will be shipped as-is;
- the user asks for MoA, panel review, red-team review, model routing, provider auto-tuning, or high-confidence synthesis.

Do not use it for formatting, translation, boilerplate, CRUD snippets, deterministic commands, trivial lookup, or low-risk work where latency/cost matters more than quality.

## Procedure

### 1. Apply the escalation gate

Count signals:

1. explicit request for best/production/graded answer;
2. multiple defensible approaches;
3. security, irreversible, or expensive rollback implications;
4. ambiguous or contested requirements;
5. single-model draft fails verification or contradicts itself;
6. confidence below 0.70;
7. provider/model selection materially affects correctness;
8. external evidence is required and one path is insufficient.

Decision:

- mechanical or low-risk task: **L0 single-model**;
- irreversible/graded task with at least one signal: **escalate**;
- any task with at least two signals: **escalate**;
- if more than 15-20% of turns escalate, tighten the gate.

### 2. Choose the escalation level

- **L0 — Single Model:** use Hermes' current default model; add cheap verification if needed.
- **L1 — Panel-once:** use one MoA preset or one isolated `delegate_task` advisory panel for one hard question.
- **L2 — Framed Batch:** run 2-3 frames such as steelman A, steelman B, risk/security audit, cost/latency audit, migration/rollback review, or model-routing review.
- **L3 — Adversarial Red-Team:** produce a draft via L1/L2, then ask a red-team reviewer to find blocking issues.

### 3. Respect the Hermes MoA contract

Hermes native MoA is a virtual model provider. The preset aggregator is the acting model. Reference models run first without tool schemas; their outputs are passed as private context to the aggregator. The aggregator emits the final assistant response and tool calls.

MoA increases model-call count. One model iteration can involve multiple reference calls plus the aggregator call. Use it only when the gate justifies the extra cost.

### 4. Delegate safely when using subagents

`delegate_task` supports restricted child toolsets at top level and per task. Use that capability deliberately. Advisors usually need no dangerous tools. Research advisors may receive `web`; implementation children may receive `terminal` and `file`; never grant broader toolsets than necessary.

Subagents have no parent conversation memory. Every delegated brief must be self-contained and sanitized.

### 5. Auto-tune providers and models

When the user asks Hermes to adapt to available providers/models:

```bash
python3 scripts/validate_skill.py
python3 scripts/discover_models.py --hermes-home ~/.hermes
python3 scripts/tune_panel.py --hermes-home ~/.hermes --write-preview
python3 scripts/apply_patch.py --hermes-home ~/.hermes
python3 scripts/smoke_test.py --hermes-home ~/.hermes --source merged --preset moa-synthesis-auto
```

If expected models are not in config yet, add explicit preferences, for example:

```bash
python3 scripts/discover_models.py --hermes-home ~/.hermes \
  --preferred openai-codex:gpt-5.5.5 \
  --preferred openrouter:deepseek/deepseek-v4-pro
```

Unverified preferred names are visible in inventory but are not used for safe patch generation unless `--allow-unverified` is passed to `tune_panel.py`.

Apply only with explicit operator approval:

```bash
python3 scripts/apply_patch.py --hermes-home ~/.hermes --apply
python3 scripts/smoke_test.py --hermes-home ~/.hermes --source config --preset moa-synthesis-auto
```

Never silently overwrite `~/.hermes/config.yaml`.

### 6. Select roles by quality, not quantity

Aggregator / acting model:

- best tool-use reliability;
- strong instruction following and synthesis;
- context length >= 64k;
- stable provider availability;
- low hallucination under tool pressure.

Reference advisors:

- strong reasoning and critique;
- concise output using `reference_max_tokens`;
- independent enough to expose hidden assumptions;
- no tool schemas unless absolutely required.

Fallbacks:

- confirmed provider/model pairs first;
- local Ollama only as privacy/offline fallback unless quality is sufficient;
- avoid unverified preferred names as production aggregators.

Quality-first rule: two strong advisors are better than four noisy advisors.

### 7. Use a sanitized advisor brief

Every advisor brief must include task, escalation reason, sanitized context, hard constraints, soft preferences, definition of done, forbidden actions, expected output shape, and verification expectations. Use `templates/advisor-brief.md` for the standard contract.

### 8. Reconcile disagreements

When advisors disagree:

1. identify the crux;
2. test the crux if possible;
3. prefer evidence over vote count;
4. preserve useful dissent;
5. never average incompatible designs;
6. do not ship if verification fails.

### 9. Log only non-sensitive telemetry

Log only non-sensitive summaries: timestamp, task family, escalation level, provider/model names, reason, verification status, failure mode, rollback path, and latency/cost estimate if available.

Never log raw secrets, `.env`, bearer tokens, OAuth sessions, private customer data, or full request dumps.

## Pitfalls

- Do not use MoA as a reflex.
- Do not equate consensus with correctness.
- Do not expose credentials to advisors.
- Do not let advisors execute side-effect tools unless required.
- Do not use unverified model names as production aggregators.
- Do not ignore Hermes version drift.
- Do not overwrite provider routing unless the operator explicitly wants it.
- Do not run local low-quality models as production aggregators just because they are free.

## Verification

Before final answer or config apply:

- code: run tests, lint, type checks, or minimal repro;
- config: validate YAML and dry-run merge;
- security: secret scan, least-privilege review, no credential leakage;
- deployment: backup, rollback, health check;
- model routing: confirm provider availability, context length, tool-call compatibility, and fallback behavior;
- research: cite primary sources and label inference.

For this package itself, run:

```bash
python3 scripts/validate_skill.py
python3 -m py_compile scripts/*.py tests/*.py
python3 scripts/eval_gate.py
python3 tests/test_regressions.py
```

## Reference Files

- `references/playbook-v4.md` — operator runbook.
- `references/provider-model-policy.md` — availability and model-proof rules.
- `references/hermes-skill-compatibility.md` — Hermes skill-structure compatibility notes.
- `templates/advisor-brief.md` — sanitized advisor prompt contract.
- `templates/red-team-brief.md` — L3 adversarial review template.
