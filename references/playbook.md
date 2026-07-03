# MoA Synthesis v3 — Operating Playbook

Companion to `../SKILL.md`. Read on demand — when escalating at L2/L3, when a
panel result needs reconciliation, or when tuning the panel (§5). Everything
here was verified against Hermes Agent v0.18.0 source on 2026-07-03.

## §1 Briefing template (copy, fill, send)

The child (and its advisor references) see NOTHING of your conversation.
`goal` = one sentence. `context` = this block, filled in:

```
PROBLEM: <the hard question, restated so a stranger gets it>

HARD CONSTRAINTS (violating any = wrong answer):
- <constraint 1>
- <constraint 2>
SOFT PREFERENCES: <nice-to-haves, tiebreakers>

PRIOR ATTEMPTS:
- <attempt> → <why it failed / what it missed>

DEFINITION OF DONE (checkable):
- <e.g. "handles provider A dying mid-stream without data loss">
- <e.g. "stays under 90 turns worst-case">

MATERIALS:
- File: /abs/path/to/file.py (the child can read it — same host)
- Snippet: <paste the load-bearing 10–30 lines inline>
- May run: <exact commands the child is allowed/expected to run, if any>

MODE: <pick one>
- "Answer directly from this brief. Do NOT use tools." (pure judgment — keeps
  the panel at ~3 model calls total)
- "Verify empirically: run <command>, then conclude." (empirical — advisor
  cost multiplies with every tool iteration; only choose this when the
  verification genuinely needs to happen inside the child)

OUTPUT CONTRACT — return exactly:
1. ANSWER — the recommendation/decision, concrete.
2. KEY ASSUMPTIONS — what you took as given.
3. WHAT WOULD CHANGE IT — observations that would flip the answer.
4. CONFIDENCE + TOP RISK — one line.
5. DISAGREEMENTS — if your reference advisors disagreed, name the crux.
```

## §2 L2 framing menu (batch `tasks=[...]`, max 3)

Same PROBLEM block in every task's context; only the FRAMING line changes.
Because every panel uses the same models, framing diversity is how you avoid
one panel's groupthink:

- **Steelman A**: "Argue the strongest possible case FOR <option A>, then give
  your honest verdict."
- **Steelman B**: same for the rival option.
- **Risk audit**: "Assume the leading proposal fails in production 6 months
  from now. Work backwards: what killed it? Rank the top 3 failure modes."
- **Simplicity pass**: "Propose the simplest solution that satisfies every
  hard constraint. What does the complex proposal buy that this doesn't?"
- **Constraint attack**: "Which stated constraint is most likely wrong or
  negotiable, and how does the answer change if it's dropped?"

You are the final aggregator: reconcile the returns yourself (that is the
extra MoA layer), then verify per §4.

## §3 L3 adversarial round (red-team template)

Second `delegate_task`, embedding the surviving draft:

```
PROBLEM: Red-team the draft below. It will ship as-is unless you find a
reason it shouldn't.

DRAFT UNDER REVIEW:
<paste the L1/L2 answer verbatim>

ORIGINAL CONSTRAINTS: <same hard-constraints list>

Return exactly:
1. ERRORS — anything factually or logically wrong.
2. MISSING CONSTRAINTS — real-world requirements the draft ignores.
3. CHEAPER ALTERNATIVE — a materially simpler approach, if one exists.
4. VERDICT — SHIP / FIX-FIRST (with the minimal fix) / REJECT (with why).
```

### Failure → action table

| Symptom | Action |
|---|---|
| Return hedges / refuses to pick | Tighten DEFINITION OF DONE, resend ONCE with "commit to one recommendation" |
| Return contradicts your strong prior | Don't re-roll — identify the crux, test it empirically, decide on evidence |
| Some references errored (auth/rate limit) | Accept if the aggregator + ≥1 reference succeeded; never re-trigger over a partial failure |
| Child timed out / died | Check the brief for an unbounded MODE (empirical loop); resend as judgment-only |
| Output names a model you never configured | STOP — config normalizer fell back to built-in defaults. Run §5.4 verification, flag owner |
| Two L2 panels converge, one dissents | Convergence ≠ truth (same models underneath). Weigh the dissent's argument, not the vote count |

## §4 Verification, crux protocol, telemetry

**Verification checklists by task family:**
- Code/architecture: run it; run the tests; lint; check each HARD CONSTRAINT
  line-by-line against the draft — one pass/fail word each.
- Research: spot-check the 2 most load-bearing factual claims via web tools;
  confirm cited sources exist.
- Design/UX: render it; compare against the ask; one self-critique pass.

**Crux protocol** (when references or panels disagree): state the crux in one
sentence → if testable, test it (that's the cheapest possible resolution) →
if not, present both positions + your recommendation + what evidence would
settle it. Never silently average two incompatible designs.

**Telemetry** (best-effort, one line per escalation):
```
echo "$(date -u +%FT%TZ) | L<1|2|3> | <task, 5 words> | <outcome: adopted/adapted/rejected> | panel-better-than-draft: <y/n/na>" >> ~/state/moa-escalations.log
```
This makes the 15–20% budget guard auditable instead of vibes.

## §5 Panel auto-tuning procedure (full)

### §5.1 Discover (read-only, secrets stay secret)

```bash
# Presets + delegation pointer (no secrets in these blocks)
python3 -c "
import yaml, json
c = yaml.safe_load(open('/root/hermes-luna/home/config.yaml'))
print('delegation:', c.get('delegation'))
print('providers :', list(c.get('providers') or {}))
print(json.dumps((c.get('moa') or {}).get('presets', {}), indent=1))"
# Which provider keys exist — NAMES ONLY, never values
grep -oE '^[A-Z0-9_]+=' /root/hermes-luna/home/.env | sed 's/=$//' | grep -E 'KEY|TOKEN' | grep -vE 'TELEGRAM|GITHUB|MEM0|TAVILY|ELEVENLABS|API_SERVER|LOOPS'
```

### §5.2 Rank (quality-first — Self-MoA)

Ordering heuristics, strongest signal first:
1. **Tier words in the model id**: opus / fable / pro-max / reasoner / pro >
   flash / mini / lite / chat. Flagship families (Claude Opus/Fable, GPT-5.x,
   Gemini Pro, DeepSeek Pro-Max, Grok reasoning) outrank everything below
   their tier.
2. **Never seat a weak model for diversity** — mixing down lowers panel
   quality (Self-MoA, arXiv:2502.00674). Two seats of one top model beat one
   top + one mediocre.
3. **Aggregator = strongest tool-capable model you can afford per-iteration**
   — it runs the whole acting loop. Subscription/OAuth models (e.g.
   openai-codex gpt-5.5) are zero marginal cost and excellent here.
4. **References = deepest reasoners available** — they only write advice, so
   a slow expensive reasoner is fine (latency capped via
   `reference_max_tokens`).

Example candidate inventory from one verified deployment (snapshot 2026-07-03 — re-discover in your own environment; do not assume this list is current): direct `openai-codex:gpt-5.5` (OAuth, proven), `deepseek:deepseek-v4-pro`
(+`-reasoner`; proven), `gemini:gemini-3.5-flash` (proven) / `gemini-3.1-pro`;
keys present for `openrouter` (→ `anthropic/claude-opus-4.8`,
`google/gemini-3.1-pro`, `x-ai/grok-4.20`, …), `openai`, `xai`, `nvidia`, and
custom `9router` (→ `ds/deepseek-v4-pro-max`, `cx/gpt-5.5`). ⚠️ The `anthropic`
provider block currently points `base_url` at DeepSeek's Anthropic-compat
endpoint — a probe of "claude-*" through it does NOT prove real Claude.
Reaching real Claude needs either `openrouter:anthropic/claude-opus-4.8` (works
as-is, MoA's own defaults use openrouter) or owner approval to repoint the
`anthropic` block to `https://api.anthropic.com` + `ANTHROPIC_API_KEY`.

Recommended starting shape for a comparable deployment (pending probes):
references `openrouter:anthropic/claude-opus-4.8` + `9router:ds/deepseek-v4-pro-max`
(or `gemini:gemini-3.1-pro`); aggregator `openai-codex:gpt-5.5`.

### §5.3 Probe each NEW slot

```bash
timeout 150 hermes -z "Reply with exactly: OK" --provider openrouter --model anthropic/claude-opus-4.8
timeout 150 hermes -z "Reply with exactly: OK" --provider 9router --model ds/deepseek-v4-pro-max
```
Any probe that errors/times out → that candidate keeps its old seat. Probes
spawn a full one-shot session (~10–60s each) — probe only what you intend to
seat.

### §5.4 Edit + verify (contents-only, live on next call)

```bash
cp /root/hermes-luna/home/config.yaml "/root/hermes-luna/home/config.yaml.bak.$(date -u +%Y%m%dT%H%M%S)"
python3 - <<'EOF'
import yaml
P = '/root/hermes-luna/home/config.yaml'
c = yaml.safe_load(open(P))
panel = {
  'reference_models': [
    {'provider': 'openrouter', 'model': 'anthropic/claude-opus-4.8'},
    {'provider': '9router',    'model': 'ds/deepseek-v4-pro-max'},
  ],
  'aggregator': {'provider': 'openai-codex', 'model': 'gpt-5.5'},
  'reference_max_tokens': 700,   # advisors: gist, not essays (~halves latency)
  'max_tokens': 8192,            # aggregator answer headroom
  'fanout': 'per_iteration',     # 'user_turn' for judgment-only presets
}
moa = c.setdefault('moa', {})
presets = moa.setdefault('presets', {})
target = (c.get('delegation') or {}).get('model') or moa.get('default_preset', 'default')
presets[target] = {**presets.get(target, {}), **panel}
presets['default'] = {**presets.get('default', {}), **panel}  # shadow built-in fallback
yaml.safe_dump(c, open(P, 'w'), sort_keys=False, allow_unicode=True)
print(f"wrote panel into presets: {target!r} + 'default'")
EOF
# Deterministic verification (reads DISK config through the real resolver):
python3 - <<'EOF'
import sys; sys.path.insert(0, '/root/hermes-luna/src/hermes-agent')
import yaml
from hermes_cli.runtime_provider import resolve_runtime_provider
from hermes_cli.moa_config import resolve_moa_preset
c = yaml.safe_load(open('/root/hermes-luna/home/config.yaml')); dl = c.get('delegation') or {}
rt = resolve_runtime_provider(requested=dl.get('provider'), target_model=dl.get('model'))
p = resolve_moa_preset(c.get('moa') or {}, dl.get('model'))
assert rt.get('provider') == 'moa', f"delegation no longer routes to MoA: {rt}"
print('refs:', [(r['provider'], r['model']) for r in p['reference_models']])
print('agg :', p['aggregator'], '| ref_cap:', p.get('reference_max_tokens'), '| fanout:', p.get('fanout'))
EOF
# Live smoke test (one real panel turn):
timeout 300 hermes -z "Reply with exactly: MOA_OK" --provider moa --model luna-synth
```

If verification shows models you didn't write → the normalizer rejected a slot
(typo, empty field) and substituted built-in defaults. Restore the `.bak`,
fix, retry.

### §5.5 Apply semantics + report

- Preset **contents**: live for the next `delegate_task` — even mid-session
  (`moa_loop.create()` re-reads disk config every step; verified v0.18.0).
- `delegation.model/provider` **pointer**: cached in memory at startup —
  changing it needs a gateway restart. Don't restart yourself mid-task; tell
  the owner it applies on next restart.
- Report old→new diff, probe results, and verification output to the owner in
  one compact block. Offer `moa.save_traces: true` (writes per-turn panel
  traces to `<hermes_home>/moa-traces/` for audit).

## §6 Research notes (why v3 is shaped this way)

- **MoA** (Wang et al. 2024, arXiv:2406.04692): layered proposers→aggregator;
  open-model panel hit 65.1% AlpacaEval 2.0 vs GPT-4o's 57.5%. Layers are the
  mechanism L2/L3 recreate manually.
- **Self-MoA** (Li et al. 2025, arXiv:2502.00674): +6.6% over mixed MoA by
  sampling ONE top model — panel quality dominates diversity; mixing weaker
  models drags the panel down. Drives §5.2's quality-first ranking.
- **Multi-agent debate** (Du et al. 2023, arXiv:2305.14325): critique rounds
  improve factuality/reasoning — the L3 adversarial round.
- **Cascades** (FrugalGPT etc.): escalate on uncertainty/verification failure,
  not by habit; self-verification is the cheap gate — §1's score + §4's
  verify-don't-reroll rule.
