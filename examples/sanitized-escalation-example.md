# Sanitized Escalation Example

## Task

Choose the best Hermes Agent inference stack for a server deployment using GPT-family and DeepSeek-family cloud models, with future migration to local Mini PC/Mac mini.

## Why Escalated

The decision affects architecture, cost, context length, local/cloud routing, reliability, privacy, and future migration path.

## Sanitized Context

- Current runtime: VPS server.
- Planned primary cloud models: GPT-family and DeepSeek V4 Pro-family.
- Future local hardware planned.
- Credentials omitted.

## Hard Constraints

- Do not expose local inference endpoints publicly.
- Hermes agent workflows need large context.
- Config changes require backup and rollback.
- Do not assume a model exists unless it is configured or discovered.

## Output Format

Return recommendation, alternatives, final config patch, verification checklist, and residual risk.
