---
description: 'Save system rules: versioned saves, stable IDs, validate on load, keep save logic outside UI. Use when working on save/load.'
applyTo: 'game/**'
---

# 08 — Save System Rules

The save system must be designed early and treated as a core system.

## Save Data Should Include

- Player state.
- Current location.
- Inventory.
- Cultivation state.
- Quest state.
- NPC relationship state.
- NPC memory flags.
- World event flags.
- Faction reputation.
- Discovered locations.
- Unlocked techniques.
- Story progress.
- Settings where appropriate.

## Save Rules

1. Save data should use clear versioning.
2. Never save temporary UI state as core game state unless needed.
3. Use stable IDs for saved references.
4. Do not save display names as primary identifiers.
5. Add migration notes when save structure changes.
6. Save files should be human-readable during early development if practical.
7. Separate player data from static game data.
8. Do not duplicate entire static databases in save files.
9. Validate save data on load.
10. Failed loads should produce clear errors.
11. Do not silently discard unknown save fields during development.
12. Keep save/load logic outside UI scenes.

## Save Versioning

Every save file should include a version field.

Example:

```json
{
  "save_version": "0.1.0",
  "player_id": "player_main",
  "current_location_id": "village_start"
}
```
