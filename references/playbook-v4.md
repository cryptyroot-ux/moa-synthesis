# MoA Synthesis v4 Playbook

## 1. Operating Principle

MoA is an escalation tool, not a default mode. The goal is to improve correctness on high-stakes tasks without turning every turn into an expensive panel call.

## 2. Escalation Levels

- L0: single-model answer with cheap verification.
- L1: panel-once for a difficult judgment.
- L2: framed batch for architecture forks and model/provider choices.
- L3: adversarial red-team for ship-as-is or production-impacting output.

## 3. Provider Auto-Tuning Workflow

```bash
python3 scripts/discover_models.py --hermes-home ~/.hermes
python3 scripts/tune_panel.py --hermes-home ~/.hermes --write-preview
python3 scripts/apply_patch.py --hermes-home ~/.hermes
python3 scripts/apply_patch.py --hermes-home ~/.hermes --apply
python3 scripts/smoke_test.py --hermes-home ~/.hermes --preset moa-synthesis-auto
```

If the desired models are not already configured:

```bash
python3 scripts/discover_models.py \
  --hermes-home ~/.hermes \
  --preferred openai-codex:gpt-5.5.5 \
  --preferred openrouter:deepseek/deepseek-v4-pro
```

Then either configure those providers with `hermes model` or run tuning with `--allow-unverified` only for an experimental preview.

## 4. Advisor Brief Template

```text
Task:
Why escalated:
Sanitized context:
Hard constraints:
Soft preferences:
Definition of done:
Forbidden actions:
Output format:
Verification expected:
```

## 5. Red-Team Template

```text
Review this draft as if it will ship.
Find blocking issues, security risks, hidden assumptions, rollback gaps, missing tests, provider/model routing errors, and places where consensus may be misleading.
Return: blocking issues, non-blocking issues, tests to run, and ship/no-ship judgment.
```

## 6. Rollback

`apply_patch.py --apply` creates:

```text
~/.hermes/config.yaml.bak-moa-synthesis-YYYYMMDD-HHMMSS
```

Rollback:

```bash
cp ~/.hermes/config.yaml.bak-moa-synthesis-YYYYMMDD-HHMMSS ~/.hermes/config.yaml
```
