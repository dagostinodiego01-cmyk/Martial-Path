---
description: 'Layered architecture rules (core/data/services/ui/adapters/tests) and dependency direction. Use when structuring code or deciding where logic lives.'
applyTo: 'game/**,frontend-godot/**'
---

# 01 — Architecture Rules

The project must be organised around separated layers.

Use the following conceptual structure:

```text
project_root/
├── core/
├── data/
├── services/
├── ui/
├── adapters/
├── tests/
└── docs/
```

## Layer Responsibilities

### `core/`

Pure gameplay logic.

Examples:

- Cultivation logic.
- Combat resolution.
- Relationship changes.
- Morality rules.
- Quest progression.
- Inventory effects.
- NPC decision rules.

`core/` must not depend on Godot UI nodes.

### `data/`

Static and semi-static game data.

Examples:

- Characters.
- Factions.
- Locations.
- Realms.
- Techniques.
- Items.
- Dialogue templates.
- World lore.

### `services/`

Coordination layer between data, core logic, and UI.

Examples:

- `NPCService`
- `DialogueService`
- `SaveService`
- `EventService`
- `RelationshipService`
- `CultivationService`

### `ui/`

Godot-specific interface scenes and scripts.

UI should:

- Display state.
- Send user decisions to services.
- React to returned results.

UI should not own business logic.

### `adapters/`

Godot-specific wrappers and engine integration.

Examples:

- File access.
- Scene loading.
- Input mapping.
- Export-specific helpers.

### `tests/`

Validation and logic tests.

Tests should be able to run core systems without launching the full UI.

## Dependency Rules

1. UI can depend on services.
2. Services can depend on core and data.
3. Core must not depend on UI.
4. Data must not depend on UI.
5. Godot-specific code should be isolated where possible.
6. If a system could exist without Godot, place it outside the UI layer.
7. Avoid circular dependencies.
8. Prefer explicit interfaces between layers.
