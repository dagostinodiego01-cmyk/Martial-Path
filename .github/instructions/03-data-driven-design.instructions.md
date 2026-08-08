---
description: 'Data-driven design: store characters/items/skills/realms/dialogue as data with stable IDs, not hard-coded. Use when adding game content or data files.'
applyTo: 'game/data/**,**/*.json'
---

# 03 — Data-Driven Design Rules

The game must be data-driven wherever practical.

Characters, locations, factions, techniques, items, realms, and dialogue rules should be stored as structured data rather than hard-coded into scripts.

## Preferred Data Structure

```text
data/
├── characters/
├── factions/
├── locations/
├── skills/
├── cultivation_realms/
├── dialogue_rules/
├── events/
├── quests/
└── items/
```

## NPC Data Fields

Each NPC should support fields such as:

- `id`
- `display_name`
- `origin_region`
- `faction`
- `cultivation_realm`
- `personality_traits`
- `morality_alignment`
- `ambition`
- `loyalty`
- `arrogance`
- `caution`
- `relationship_to_player`
- `memory_flags`
- `dialogue_style`
- `combat_style`
- `recruitment_status`
- `story_importance`

## Data Rules

1. Never hard-code NPCs directly into a UI script.
2. Never hard-code item or skill lists directly into menus.
3. If new content is added, create or update data files.
4. Use stable IDs rather than display names for references.
5. Display names can change; IDs should not.
6. Validate data before loading it into gameplay systems.
7. Prefer explicit fields over vague text blobs.
8. Keep game data readable during early development.
9. Avoid duplicating the same data across multiple files.
10. Use references by ID, not by copied object blocks, unless there is a strong reason.
