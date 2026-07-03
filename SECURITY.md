# Security policy

MoA Synthesis is designed for high-stakes agent workflows, but it should not be given unnecessary secrets.

## Do not include

- API keys or bearer tokens;
- OAuth sessions;
- private keys;
- wallet seed phrases;
- raw `.env` files;
- production credentials;
- private customer data;
- full request dumps containing sensitive headers.

## Recommended practice

- Give advisors sanitized context.
- Keep tool execution centralized in the aggregator.
- Verify model output before acting.
- Preserve rollback paths for production-sensitive changes.
- Store audit traces only when they do not contain secrets.

## Reporting

If you find a security issue in this repository, open a GitHub issue with a minimal reproduction and no secrets.
