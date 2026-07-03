# Sanitized escalation example

This example shows the shape of an MoA Synthesis escalation brief without exposing private code, credentials, or infrastructure details.

```text
PROBLEM: Choose the safer deployment strategy for a new authentication middleware.

HARD CONSTRAINTS:
- The rollback path must be available within minutes.
- Existing sessions must not be invalidated unexpectedly.
- Secrets, tokens, and private environment files must not be shared with advisors.

SOFT PREFERENCES:
- Prefer the simplest plan that satisfies all hard constraints.
- Prefer observability before rollout.

PRIOR ATTEMPTS:
- A direct production deploy was rejected because it had no staged rollback plan.

DEFINITION OF DONE:
- The plan names the rollout stages.
- The plan names smoke tests.
- The plan names rollback triggers.
- The plan identifies the main risk.

MATERIALS:
- Sanitized architecture summary.
- Sanitized test list.
- No credentials.

MODE:
- Answer directly from this brief. Do not use tools.

OUTPUT CONTRACT:
1. ANSWER — recommended rollout strategy.
2. KEY ASSUMPTIONS — what the answer depends on.
3. WHAT WOULD CHANGE IT — observations that would flip the answer.
4. CONFIDENCE + TOP RISK — one line.
5. DISAGREEMENTS — advisor disagreement crux, if any.
```
