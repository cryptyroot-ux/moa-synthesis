# Changelog

## v4.1.0 — changes from v3.0.0

This changelog intentionally lists only the delta from the previous public GitHub version, v3.0.0.

### Fixed

- Removed over-restrictive skill metadata that could make the skill undiscoverable when certain toolsets were unavailable.
- Preserved existing `fallback_providers` when applying generated patches instead of replacing the whole list.
- Added smoke-test sources for preview workflows: `auto`, `config`, `patch`, and `merged`.
- Clarified named custom provider handling for MoA selection versus fallback endpoint usage.
- Made YAML dependency failures explicit instead of allowing a missing parser to look like an empty config.

### Added

- `tests/test_regressions.py` for the v3 audit findings.
- `templates/advisor-brief.md` for sanitized advisor prompts.
- `templates/red-team-brief.md` for adversarial review prompts.
- `references/audit-v3-findings.md` documenting the v3-to-v4 hardening rationale.
- `references/hermes-skill-compatibility.md` documenting expected Hermes skill layout.

### Unchanged

- Hermes native MoA remains the execution engine.
- MoA Synthesis remains the escalation, tuning, verification, and rollback discipline above that engine.
- Routine low-risk work should still stay single-model.
