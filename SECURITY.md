# Security Policy

MoA Synthesis multiplies model calls, so context minimization is mandatory.

Never include in advisor briefs:

- API keys;
- bearer tokens;
- OAuth sessions;
- private keys;
- wallet seed phrases;
- raw `.env` files;
- production credentials;
- private customer data;
- full HTTP request/response dumps with sensitive headers.

## Tool Execution

Advisors should generally reason only. Tool execution should remain centralized in the aggregator or parent Hermes agent. Use `delegate_task(toolsets=...)` to restrict child tools.

## Config Changes

Generated config patches are preview-only by default. Applying changes requires explicit `--apply` and creates a backup.

## Trace Hygiene

Do not store raw prompts that contain secrets. Store only provider/model names, escalation level, verification result, and non-sensitive summaries.

## Reporting Issues

Do not paste secrets into issues or chat. Provide sanitized reproduction steps, expected behavior, actual behavior, Hermes version, and non-sensitive config snippets.
