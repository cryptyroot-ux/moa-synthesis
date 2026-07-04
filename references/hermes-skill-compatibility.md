# Hermes Skill Compatibility Notes

This package follows Hermes' documented skill layout:

```text
~/.hermes/skills/<category>/<skill>/
├── SKILL.md
├── references/
├── templates/
├── scripts/
└── assets/   # optional, omitted when unused
```

Important compatibility decisions:

- `SKILL.md` is at the skill root.
- The frontmatter description is intentionally short for Hermes' skill index.
- No `requires_toolsets` is declared. The skill should stay discoverable even when the operator only wants to read the runbook.
- Helper scripts live in `scripts/` and are called explicitly from the procedure.
- Long prompt contracts live in `templates/` for progressive disclosure.
- Long operational details live in `references/`.
- The package is `linux` and `macos` scoped because it expects Python and Unix-like filesystem paths for server operation.
