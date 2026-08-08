---
description: 'Documentation rules: keep README/ARCHITECTURE/schema/system docs and CHANGELOG updated alongside code. Use when adding or changing systems, data, or docs.'
applyTo: '**/*.md'
---

# 11 — Documentation Rules

The AI must keep project documentation updated as the game evolves.

## Required Documentation Files

The project should maintain:

- `README.md`
- `ARCHITECTURE.md`
- `DATA_SCHEMA.md`
- `NPC_SYSTEM.md`
- `CULTIVATION_SYSTEM.md`
- `DIALOGUE_SYSTEM.md`
- `SAVE_SYSTEM.md`
- `EXPORT_GUIDE.md`
- `CHANGELOG.md`

## Documentation Rules

1. When adding a new system, update `ARCHITECTURE.md`.
2. When adding new data fields, update `DATA_SCHEMA.md`.
3. When changing NPC logic, update `NPC_SYSTEM.md`.
4. When changing cultivation logic, update `CULTIVATION_SYSTEM.md`.
5. When changing dialogue rules, update `DIALOGUE_SYSTEM.md`.
6. When changing save format, update `SAVE_SYSTEM.md`.
7. When changing export behaviour, update `EXPORT_GUIDE.md`.
8. Log notable changes in `CHANGELOG.md`.
9. Documentation should explain intent, not just implementation.
10. Assume future developers will rely on the docs.
11. Do not let docs drift from the code.
12. If a rule is intentionally broken, document why.

## Documentation Style

Documentation should be:

- Clear.
- Practical.
- Easy to scan.
- Written for future maintainers.
- Updated alongside code changes.
