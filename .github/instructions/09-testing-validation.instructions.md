---
description: 'Testing and validation rules: systems testable without the UI; validate data IDs and references. Use when writing tests or data validation.'
applyTo: 'tests/**,game/**'
---

# 09 — Testing and Validation Rules

Every important game system should be testable without launching the full UI.

## Prioritise Tests For

- Character data loading.
- Cultivation progression.
- Breakthrough logic.
- Relationship changes.
- Dialogue condition resolution.
- Save/load integrity.
- Faction reputation.
- Quest state transitions.
- Item effects.
- NPC behaviour rules.

## Validation Rules

1. Core systems should be callable from tests.
2. Avoid depending on UI scenes for logic tests.
3. Add validation for required data fields.
4. Detect duplicate IDs.
5. Detect missing references.
6. Detect invalid cultivation realms.
7. Detect dialogue nodes with missing next-node links.
8. Detect NPCs referencing non-existent factions.
9. Detect items referencing non-existent effects.
10. When adding a new data type, add a validation rule for it.
11. Validation errors should identify the file and field that failed.
12. Do not allow invalid data to fail silently.

## Testing Intent

Testing should protect the game from data sprawl and broken references as the number of NPCs, factions, skills, and story events grows.
