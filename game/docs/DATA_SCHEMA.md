# Data Schema

This document records the data files used by the current Python engine.

## Cultivation Data

Cultivation data lives under `game/data/cultivation/`.

### Body Transformation Realms

File: `body_transformation_realms.json`

Top-level fields:

- `track_id`: must be `body_transformation`.
- `display_name`: player-facing track name.
- `realms`: ordered realm definitions.

Required realm fields:

- `id`: stable save ID.
- `display_name`: UI label.
- `order`: unique integer within the track.
- `type`: one of `linear_stage`, `percentage_stage`, or `unlock_sequence`.

Progress realms use:

- `max_progress`
- `required_progress`: positive numeric progress required for breakthrough.
- `base_hp_bonus`
- `base_physical_attack_bonus`
- `base_physical_defence_bonus`
- `success_stat_gains`: breakthrough-success permanent stat gains. Supported fields are `body_strength`, `max_hp`, `max_qi`, `attack`, and `defense`; values must be non-negative numbers.
- `breakthrough_requirements.progress`
- `breakthrough_requirements.foundation_min`
- `breakthrough_requirements.resources`

Sequence realms use:

- `required_progress`: positive numeric progress required for each sequence unlock attempt.
- `sequence_key`: `opened_gates` or `opened_stars`.
- `sequence`: ordered stable IDs.
- `success_stat_gains`: permanent stat gains divided across sequence unlocks.
- `breakthrough_requirements.progress`
- `breakthrough_requirements.foundation_min`
- `breakthrough_requirements.resources`

Every sequence item must have a display-name mapping in `cultivation_config.json`.

### Essence Gathering Realms

File: `essence_gathering_realms.json`

Top-level fields:

- `track_id`: must be `essence_gathering`.
- `display_name`: player-facing track name.
- `default_substages`: fallback substage list.
- `special_substages`: special labels available to data.
- `realms`: ordered realm definitions.

Required realm fields:

- `id`: stable save ID.
- `display_name`: UI label.
- `order`: unique integer within the track.
- `type`: one of `substage_realm`, `numbered_falls`, `late_game_stub`, or `theoretical_endpoint`.

Substage realms use:

- `substages`
- `max_progress_per_substage`
- `required_progress`: positive numeric progress required for each substage breakthrough; higher Essence realms should increase this value.
- `base_qi_bonus`
- `base_technique_power_bonus`
- `base_dantian_capacity_bonus`

`Life Destruction` uses `numbered_falls`, `falls`, `max_progress_per_fall`, and `required_progress`.

`Beyond Divinity` must remain `reachable: false`.

### Cultivation Config

File: `cultivation_config.json`

Contains:

- body training method definitions.
- essence training method definitions.
- `body_progression`: strain, foundation stability, failed breakthrough, stabilise, and daily diminishing-return tuning.
- `essence_progression`: Essence-track strain, foundation stability, failed breakthrough, and stabilise tuning (mirrors `body_progression`, without daily diminishing returns).
- combined action labels.
- sequence display-name mappings.
- failure-code player messages.
- known cultivation resource IDs.
- balance thresholds.

`body_progression` fields:

- `training_strain_gain`: non-negative strain added by Body training.
- `max_strain_for_breakthrough`: 0-100 maximum strain for Body breakthrough eligibility.
- `required_foundation_stability`: 0-100 minimum foundation stability for Body breakthrough eligibility.
- `successful_breakthrough_strain_reduction`: non-negative strain reduced after successful Body breakthrough.
- `failed_breakthrough_strain_gain`: non-negative strain added after failed Body breakthrough.
- `failed_breakthrough_foundation_loss`: non-negative foundation stability lost after failed Body breakthrough.
- `failed_breakthrough_progress_ratio`: 0-1 ratio used to reduce progress after failed Body breakthrough.
- `daily_cultivation_multipliers`: non-empty list of values greater than 0 and up to 1.
- `stabilise`: object containing `strain_reduction`, `foundation_stability_gain`, `comprehension_gain`, `progress_gain`, and `message`.

### Martial Talents

File: `cultivation/martial_talents.json`

The rolled Martial Talent is the character's essence-cultivation aptitude (it
replaces the former Spiritual Root). Each entry uses:

- `id`: stable snake_case ID saved on the player as `martial_talent_id`.
- `display_name`: UI label (matches the talent ladder grade names).
- `tier`: positive integer index into the talent ladder (`talents.json`). Tiers need not be unique across entries (e.g. the three Common Grade sub-talents share tier 2).
- `rarity`: non-empty label.
- `roll_weight`: non-negative number; `0` is excluded from natural rolls.
- `essence_cultivation_multiplier`: positive multiplier for Essence base training gain.
- `comprehension_multiplier`: positive multiplier for meditation comprehension gain.
- `essence_breakthrough_modifier`: breakthrough chance modifier, between `-1.0` and `1.0`.
- `qi_strain_gain_multiplier`: positive multiplier reserved for future Essence strain gain.
- `description`: UI text.
- `upgrade_options`: list of future upgrade definitions. `target_id` must exist and cannot be the same entry.

### Body Talents

File: `cultivation/body_talents.json`

The rolled Body Talent is the character's body-cultivation aptitude (it replaces
the former Physique). Each entry uses:

- `id`: stable snake_case ID saved on the player as `body_talent_id`.
- `display_name`: UI label (matches the talent ladder grade names).
- `tier`: positive integer index into the talent ladder (`talents.json`).
- `rarity`: non-empty label.
- `roll_weight`: non-negative number; `0` means upgrade-only and is excluded from natural rolls.
- `body_cultivation_multiplier`: positive multiplier for Body base training gain.
- `body_breakthrough_modifier`: breakthrough chance modifier, between `-1.0` and `1.0`.
- `body_stat_gain_multiplier`: positive multiplier for successful Body breakthrough stat gains.
- `injury_resistance_multiplier`: positive multiplier reserved for future injury handling.
- `body_strain_gain_multiplier`: positive multiplier for Body training strain gain.
- `description`: UI text.
- `upgrade_options`: list of future upgrade definitions. `target_id` must exist and cannot be the same entry.

### Talent Tiers

File: `cultivation/talents.json`

A single object with `system_id`, `display_name`, `description`, and a `tiers`
list. Every tier entry uses:

- `id`: stable snake_case ID (`tier_1`..`tier_20`, `apex`).
- `tier`: positive integer index shared by both talent tracks. The Apex tier uses `21` with `is_apex: true`.
- `is_apex`: boolean; exactly one entry sets it to `true`.
- `martial_talent_name`: Martial (essence-path) talent label.
- `body_talent_name`: Body-cultivation (body-path) talent label.
- `cultivation_realm`: descriptive label for the realm the tier can reach.
- `realm_id`: stable Essence Gathering realm ID this tier maps to, or `null` for mortal, compound, or transcendent ceilings.
- `max_lifespan_years`: positive integer upper bound, or `null` for effectively immortal/eternal tiers.
- `lifespan_display`: UI text for the lifespan; may be a range such as `300-400 years`.
- `source`: `canon`, `extrapolated`, or `mixed` — lore-accurate vs tuned values.
- `source_notes`: free-text provenance note.

## Equipment Data

Equipment data lives in `game/data/equipment.json`.

Each entry uses:

- `id`: stable snake_case ID. Equipment IDs can be granted as normal item rewards.
- `display_name`: UI label.
- `slot`: broad slot/category hint such as `weapon`, `ring`, `artifact`, or `flying_sword`.
- `valid_slots`: concrete player slots. Must use the supported equipment slot list.
- `category`: one of `martial_weapon`, `robe`, `light_armor`, `heavy_armor`, `boots`, `cloak`, `ring`, `amulet`, `talisman`, `artifact`, `flying_sword`, `cultivation_aid`, `body_tempering_tool`, `utility_tool`, or `sect_token`.
- `rarity`: one of `mortal_grade`, `low_spirit_grade`, `middle_spirit_grade`, `high_spirit_grade`, `earth_grade`, `heaven_grade`, `profound_grade`, or `divine_grade`.
- `description`: UI text.
- `requirements`: optional checks such as `minimum_body_realm`, `minimum_essence_realm`, `minimum_strength`, `minimum_comprehension`, `required_faction`, and `required_quest_flags`. Equipment gates on actual cultivation (realm/stats), never on talent.
- `stat_modifiers`: supported keys are `strength`, `body_strength`, `attack`, `defense`, `max_hp`, `max_qi`, `speed`, `evasion`, and `comprehension`.
- `cultivation_modifiers`: supported keys are `body_cultivation_flat_bonus`, `essence_cultivation_flat_bonus`, `body_strain_gain_multiplier`, `qi_strain_gain_multiplier`, `foundation_stability_bonus`, `breakthrough_chance_modifier`, `body_breakthrough_modifier`, `essence_breakthrough_modifier`, and `comprehension_bonus`.
- `utility_modifiers`: supported future-facing keys include travel, gathering, stealth, ambush, shop, spirit stone, corpse qi, and weather bonuses.
- `tags`: descriptive stable strings.
- `value`: non-negative number.
- `stackable`: must be `false` for equipment.
- `equippable`: must be `true` for equipment.

Equipment is loaded by `GameDataRegistry` and projected into the item registry for inventory display/ownership checks. Equipping does not consume or remove the item.

## Shop Data

Shop data lives in `game/data/shops.json`.

Each shop entry uses:

- `id`: stable snake_case ID.
- `display_name`: UI label.
- `location_ids`: one or more location IDs where this market is available.
- `description`: UI text shown when the market opens.
- `stock`: non-empty list of purchasable entries.

Each stock entry uses:

- `item_id`: item or equipment ID from `items.json` / `equipment.json`.
- `price`: non-empty object keyed by supported currency. Supported currencies are `gold` and `spirit_stone`.
- `stock`: optional positive integer purchase limit for one transaction. Omit it for repeatable consumables/materials.

Gold is stored on the player. Spirit Stones are inventory items, so spending them removes `spirit_stone` from inventory. Shops are validated by the central data validator for duplicate IDs, known locations, known stock item IDs, supported currencies, and positive prices.

## Item Resource References

Cultivation breakthrough resources must exist as item IDs in `game/data/items.json`. Current cultivation resources are:

- `marrow_tempering_elixir`
- `celestial_gate_essence`
- `dao_palace_star_core`

## Content Collections and Folders

Large list-collections are split into folders and merged on load by
`load_collection(name)` (which falls back to `data/<name>.json` when no folder
exists). Each file in a folder is a JSON list; order is filename order.

| Collection         | Location                              |
| ------------------ | ------------------------------------- |
| NPC roster         | `data/characters/*.json` (by faction) |
| Random enemy pool  | `data/enemies/random_enemies.json`    |
| Named duel/boss foes | `data/character_enemies/named_foes.json` |
| Skill trainers     | `data/trainers.json`                  |
| Technique-manual overrides | `data/technique_manuals.json`   |

`GameDataRegistry.load()` (`game/data/registry.py`) is the single entry point that
loads every collection plus the single-file data (items, skills, events,
cultivation, morality, relationships, locations, quests, encounter pools,
shops, trainers, technique manuals).

## Content discovery

Players acquire content through several data-driven channels:

- **Items / equipment**: enemy `loot_table` drops, shop stock, and exploration
  finds. Exploration `LOOT` events without a curated location pool draw a
  **rarity-weighted, danger-gated** find from the whole item/equipment catalogue,
  tuned by `events.json` -> `find_config` (`rarity_order`, `rarity_weights`,
  `danger_max_rarity_index`, `default_item_rarity`). A location's numeric
  `danger_level` caps the rarity that can appear there.
- **Skills (techniques)**: learned from **technique manuals** or **trainers**.
  A manual is auto-generated for every skill at load (id `"<skill_id>_manual"`,
  `effect: "learn_skill"`); `data/technique_manuals.json` entries are *optional
  overrides* matched by `skill_id` (custom name/rarity/description/id). Using a
  manual (`USE_ITEM`) teaches its skill and consumes it.
- **Trainers** (`data/trainers.json`): location-bound masters that teach skills
  for currency. Each trainer has `id`, `display_name`, `location_ids`, and
  `techniques` (`skill_id` + `price` in `gold`/`spirit_stone`). `TRAINERS` lists
  a location's offerings; `LEARN_SKILL` pays and learns one.

Character `gameplay_hooks` drive named interactions:

- `can_talk`: allows `TALK_TO_CHARACTER` and dialogue-context results.
- `can_spar`: allows `SPAR_CHARACTER` when unlocked and `enemy_id` is present.
- `can_duel`: allows `DUEL_CHARACTER` when unlocked and `enemy_id` is present.
- `enemy_id`: references `data/character_enemies/named_foes.json` for spar/duel combat.

Exploration may surface local `npc_ids` as a `CHARACTER_ENCOUNTER` result with
backend-provided interaction options. This is gated by a data-driven
`character_encounter_chance` (in `data/events.json`, `0.0`-`1.0`, default `0.35`);
the rest of the time exploration rolls the normal weighted event pools, so
locations with named characters still yield combat, loot, and special events.

## Location Schema (node-based)

Each entry in `data/locations.json`:

```json
{
  "id": "outer_forest",
  "display_name": "Outer Forest",
  "zone": "Sky Spill World",
  "location_type": "starter_wilderness",
  "tier": "Tutorial / Early Game",
  "description": "…",
  "requirements": {
    "body_transformation": { "minimum_realm": "Mortal", "minimum_stage": 1 },
    "essence_gathering": { "minimum_realm": "None", "minimum_stage": 0 },
    "unlock_flags": [],
    "required_items": [],
    "required_reputation": []
  },
  "danger_level": 2,
  "qi_density": 2,
  "map_position": {"x": 0.070, "y": 0.665},
  "connected_locations": ["azure_village", "misty_gorge"],
  "npc_ids": [],
  "available_systems": ["explore", "gathering"],
  "resources": ["Spirit Grass"],
  "notes": "…"
}
```

- `danger_level` and `qi_density` are integers `0..10`; `LocationSystem` maps them
  to display labels (`danger_label`, `qi_density_label`).
- `map_position` is a normalized coordinate object (`x` and `y` from `0.0` to
  `1.0`) on `Sky Spill Continent Map.png`; Godot uses it to place the current
  location marker without depending on one pixel resolution.
- `connected_locations` replaces the legacy `connections` key (still read for
  backward compatibility). Both must reference existing location IDs.
- `npc_ids` must reference existing character IDs.
- `TravelService` enforces `requirements` (cultivation realm minimums, required
  items, required reputation) when moving between locations.
- `minimum_realm` accepts a realm `id` or `display_name` from the cultivation
  data (e.g. `"Strength Training"`, `"Pulse Condensation"`, `"Houtian"`);
  `"None"`/`""`/`"any"` mean "no gate". `minimum_stage` is descriptive only
  (the gate compares realm order, not stage). `unlock_flags` are reserved for
  future story gating and are not yet enforced.
- The shipped map is the Sky Spill Continent (see `MAP_SYSTEM.md`): the early
  Sky Fortune Kingdom is open, and later regions are locked by realm minimums
  rather than removed, so they list as reachable/locked with a reason.

## Encounter Pools

`data/encounter_pools.json` maps a location ID to weighted `combat`/`loot`/
`special` pools:

```json
{
  "outer_forest": {
    "combat": [{ "enemy_id": "iron_wolf", "weight": 5 }],
    "loot": [{ "item_id": "healing_pill", "weight": 3 }],
    "special": [{ "special_id": "ancient_manual", "weight": 1 }]
  }
}
```

`enemy_id` must exist in the random enemy pool, `item_id` in `items.json` or
`equipment.json`, and `special_id` in `events.json` `special_events`. Locations
without a pool fall back to the global pools in `events.json`.

## Enemy Schema

Random enemies live in `data/enemies/random_enemies.json`; named duel/boss foes
live in `data/character_enemies/named_foes.json`.

Enemies do not use numeric levels. Combat difficulty is described by cultivation
realm IDs:

- `body_realm_id`: required, must reference Body Transformation realm data.
- `essence_realm_id`: optional, must reference Essence Gathering realm data when present.
- `hp`, `attack`, `defense`, and `exp_reward`: combat numbers.
- `loot_table`: item/equipment drops with `item_id`, `chance`, and `count`.

The engine resolves enemy realm display names from the cultivation realm data for
UI output.

## Central Validation

`game/validation/validate_all_game_data()` checks all of the above (unique IDs and
every cross-reference) and is exercised by `tests/test_all_game_data_valid.py`.
Run it after editing any data file.
