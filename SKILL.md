---
name: moa-synthesis
description: >
  Use when a task is genuinely hard, ambiguous, high-stakes, or explicitly asks
  for the best / most thorough / most optimal answer — architecture or design
  decisions with more than one defensible approach, contested or underspecified
  research questions, benchmark or graded tasks where quality is directly scored,
  or whenever the default single-model answer hedges, contradicts itself, or
  fails its own verification step. ALSO use when the owner asks to upgrade,
  tune, re-configure, or "use the most powerful models in" the MoA panel /
  delegation target — this skill can re-configure the panel itself from the
  providers actually available on this machine. Do NOT use for mechanical,
  deterministic, well-specified, or low-stakes tasks — formatting, boilerplate,
  simple CRUD, running existing tests, quick lookups. Those stay on the default
  single model for speed and token efficiency.
version: 3.0.0
author: Crypty Root
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [moa, orchestration, delegation, escalation, panel-tuning, auto-config]
---

# Mixture-of-Agents Synthesis v3 — escalation engine + self-tuning panel

Decide on your own when a task deserves a panel of models instead of one, get
that panel by calling `delegate_task`, verify what comes back, and — new in v3 —
**re-tune the panel itself** to the strongest models actually available on this
machine. Grounded in MoA research (layered proposers→aggregator), Self-MoA
(reference QUALITY beats diversity), multi-agent debate (critique rounds
improve factuality), and cascade routing (escalate on uncertainty, verify
cheaply). Deep procedures live in `references/playbook.md` — read it when you
escalate at L2/L3 or when tuning the panel.

## 0. Build facts (verified against source v0.18.0, 2026-07-03)

- `delegation.provider: moa` + `delegation.model: <preset>` → **every**
  `delegate_task` call runs the configured panel. There is NO per-call
  preset/model/toolset choice (schema: `goal`, `context`, `tasks[]`, `role`;
  `background` is deprecated and ignored).
- **Delegations run async automatically** — the result re-enters the
  conversation as a new message. Fire the panel, keep working, reconcile when
  it lands. Batch `tasks[]` fan out in parallel (max 3 concurrent).
- **Preset CONTENTS are re-read from disk on every panel step**
  (`moa_loop.py: create()` → `load_config()`). Editing `moa.presets.*` in
  config.yaml takes effect on the very next call — no restart. Changing the
  `delegation.*` pointer itself DOES need a gateway restart (cached in memory).
- Cost model: with `fanout: per_iteration` (default) the reference advisors
  re-run on **every tool iteration** of the child — panel cost ≈
  (references × iterations) + aggregator loop, NOT a flat 3 calls. A
  judgment-only brief ("answer from this brief; do not use tools") keeps it at
  a true ~3 calls. `fanout: user_turn` runs advisors once per user turn.
- References are advisors: no tools, stripped view (no system prompt, no tool
  transcript, tool results previewed head+tail). The aggregator holds the
  tools and produces the answer. A failed reference becomes a labelled note —
  the panel continues.
- Recursive MoA is blocked at config level; children are depth-capped
  (`max_spawn_depth` default 1). **If you are a delegated child, answer
  directly — never re-escalate.**

## 1. Decide (10-second gate)

Count escalation signals:
1. Explicitly asks for best / most thorough / most optimal, or is benchmarked/graded.
2. More than one defensible approach (architecture, design, UI/UX fork).
3. Costly to reverse, security-relevant, or ships as-is.
4. Contested / ambiguous / underspecified research question.
5. Your single-model draft hedges, self-contradicts, or failed its own
   verification (tests, lint, render mismatch).
6. You would bet under ~70% that your solo answer survives expert review.

**Escalate at ≥2 signals — or 1 signal if irreversible/graded.** Hard skips:
mechanical/deterministic work; one clearly-right approach; latency beats the
marginal gain; session already token-heavy and stakes don't justify it; you
are a delegated child. Budget guard: if >15–20% of a session's turns escalate,
the gate is mistuned. Escalate **once per decision** — on doubt, verify the
draft instead of re-rolling the panel (cascade principle).

## 2. Escalate at the right level

| Level | Shape | Cost | Use when |
|---|---|---|---|
| **L1 panel-once** | one `delegate_task`, judgment-shaped brief, "no tools" directive | ~3 calls | default for a hard single question |
| **L2 framed batch** | one call, `tasks=[2–3 framings of the same question]` (steelman A / steelman B / risk-audit); YOU aggregate the returns | ~3 calls × N panels | forked decisions with distinct lenses — adds a proposer layer with you as final aggregator (MoA layering) |
| **L3 adversarial round** | second `delegate_task` feeding the L1/L2 draft: "red-team this — find errors, missing constraints, cheaper alternatives" | +~3 calls | output ships/graded as-is or is irreversible (debate research: critique rounds improve factuality) |

All levels are async — keep working while the panel runs. Framing menus and
the red-team template: `references/playbook.md` §2–3.

## 3. Brief like the panel is blind

Subagents know nothing of this conversation. Every brief carries six fields —
PROBLEM (one sentence) · CONSTRAINTS (hard, then soft) · PRIOR ATTEMPTS and why
they failed · DEFINITION OF DONE (checkable) · MATERIALS (exact file paths,
inline snippets, commands the child may run) · OUTPUT CONTRACT (answer, key
assumptions, what would change it, confidence + top risk, reference
disagreements). For pure judgment add: *"Answer directly from this brief; do
not use tools."* For empirical tasks, name exactly what to run and accept the
advisor×iterations cost. Full template: `references/playbook.md` §1.

## 4. Verify and reconcile (draft ≠ gospel)

- Verify empirically where possible — run it, test it, render it. Verification
  is far cheaper than generation; never skip it to save tokens.
- If the return reports reference disagreement: name the crux, test it if
  testable, else present both positions plus your recommendation and why.
- State in one line that you escalated: *"Escalated L2 (design fork,
  irreversible) → panel converged on X; verified via Y."*
- Best-effort telemetry: append one line per escalation to
  `~/state/moa-escalations.log` (format: playbook §4). Skip silently if the
  file toolset is unavailable.

## 5. Panel auto-tuning (self-configuration)

Run this when the owner asks to upgrade/tune the panel or "use the most
powerful models", when panel output is repeatedly weak, or when discovery
shows clearly stronger models available than the current preset. Full
commands: `references/playbook.md` §5.

1. **Discover** — read `config.yaml` (`providers:`, `moa:`, `delegation:`) and
   list `.env` key NAMES only (never values, never print secrets).
2. **Rank quality-first** (Self-MoA finding: reference quality beats
   diversity — never seat a weak model for variety). Prefer flagship /
   pro / max / reasoner tiers; diversity only among equals; the strongest
   tool-capable model takes the aggregator seat (it acts); subscription/OAuth
   models are free marginal capacity.
3. **Probe** each new candidate:
   `timeout 150 hermes -z "Reply with exactly: OK" --provider P --model M`.
   Already-working slots don't need probing.
4. **Edit** — back up config.yaml, then rewrite the **contents** of the preset
   that `delegation.model` points at. Do NOT change `delegation.*` itself (that
   needs a restart; preset contents go live on the next call). While editing:
   set `reference_max_tokens: 700` (advisors need the gist, not essays — this
   roughly halves panel latency), raise `max_tokens` to 8192 for the
   aggregator, and pick `fanout` for the workload (`user_turn` for pure
   judgment). Mirror the same slots into the `default` preset so the built-in
   hardcoded fallback can never seat a model you didn't choose.
5. **Verify** — run the disk-config simulation snippet (playbook §5.4), then
   one live smoke test: `hermes -z "Reply with exactly: MOA_OK" --provider moa
   --model <preset>`.
6. **Report** the old→new panel diff to the owner. Offer `moa.save_traces:
   true` for per-turn panel audit trails.

Safety rails: never print secret values; never edit provider auth blocks
without owner approval (probe first, propose second); keep the `.bak` for
rollback; a failed probe leaves that slot unchanged.

## 6. Gotchas (all code-verified)

- The panel is a judgment engine, not parallel grunt labor — mechanical
  fan-out goes through `execute_code`.
- Self-containment is on you: references see stripped text only.
- Partial reference failure is normal — don't re-trigger the panel over it.
- The config normalizer silently replaces invalid preset slots with built-in
  defaults. After ANY config edit, run the simulation check; if panel output
  ever names a model you didn't configure, stop and flag the owner.
- Results arrive asynchronously as a new message — don't block on them.
- If you are the child: answer directly, never re-delegate.

## 7. Examples

- "Design retry/backoff for 3 unreliable providers under a hard turn budget"
  → L1 (add an L2 risk-audit framing if it ships as-is).
- "Which of these two schemas holds up better at scale, and why?" → L2:
  steelman each schema + one failure-mode audit framing.
- "Rewrite the auth middleware; it deploys straight to prod" → L1 then L3
  red-team on the draft.
- "Rename this variable and fix the lint warning" → never escalate.
- "Upgrade the panel; use the strongest available models" → §5 procedure.
- "Summarize this changelog" → never escalate.
