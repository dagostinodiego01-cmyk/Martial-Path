---
name: game-data-authoring
description: 'Procedure for adding or editing data-driven content in the Martial Path RPG: NPCs/characters, items, skills, enemies, named foes, locations, quests, encounter pools, cultivation realms, morality/relationship config, and dialogue. Use when creating game content, adding a JSON data file, editing game/data/**, working with stable IDs or the GameDataRegistry, or when validation/cross-reference errors appear. Covers merge-on-load collection folders, registry loading, and the central validation layer.'
argument-hint: 'the content to add or edit'
---

# Martial Path Data Authoring

Content is data-driven (instruction 03). Add content by editing `game/data/**`
with stable IDs — not by hard-coding it in engine, systems, or UI.

## When to Use
- Adding/editing characters, items, skills, enemies, locations, quests, events,
  encounter pools, cultivation realms, or morality/relationship config.
- Diagnosing broken references or duplicate IDs.

## Where content lives
- Single files: `items.json`, `skills.json`, `events.json`, `quests.json`, `locations.json`, `morality.json`, `relationships.json`, `encounter_pools.json`, `cultivation/*.json`.
- Merge-on-load folders (each file is a JSON list, merged in filename order): `characters/*.json` (grouped by faction), `enemies/random_enemies.json`, `character_enemies/named_foes.json`.

## Procedure

1. **Pick the right file/folder.** Match the schema of sibling entries exactly. For a large/growing collection, add a new file to the matching folder — `load_collection(name)` in `game/utils/data_loader.py` merges the folder automatically; no code change needed.
2. **Use stable, unique, snake_case IDs.** IDs are referenced across files (loot → items, quests → items, locations → locations/NPCs, encounter pools → enemies/items/specials, character_enemies → characters). Never renumber or reuse an ID.
3. **Load through the registry.** Static data is loaded once by `GameDataRegistry.load()` (`game/data/registry.py`) and injected into systems. Do not re-read JSON inside systems; add a field to the registry if you introduce a new collection.
4. **Extend validation.** Add or update cross-reference checks in `game/validation/data_validator.py` (unique IDs, every referenced ID exists, numeric ranges, required keys). Keep the message categorised.
5. **Validate.** Run `validate_all_game_data()` (or `pytest tests/test_all_game_data_valid.py`) and the JSON parse smoke test. Add a negative test proving the validator catches a bad reference (build a broken registry with `dataclasses.replace`).
6. **Document.** Update `game/docs/DATA_SCHEMA.md` with any new/changed schema and add a `CHANGELOG.md` bullet.

## Schema notes
- Locations use the node schema: `display_name`, `zone`, `location_type`, numeric `danger_level`/`qi_density` (0–10), `connected_locations`, `npc_ids`, and `requirements` (`body_transformation`/`essence_gathering` minimums, `unlock_flags`, `required_items`, `required_reputation`).
- Character `morality_reaction` keys must match `morality.json` band IDs; `relationship_behavior` keys must match `relationships.json` tier IDs.
- Original lore only — no copyrighted names/sects/techniques (instruction 10).
