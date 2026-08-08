# Map System

The world map is a **data-driven, node-based travel graph**. Locations are data
objects with stable `snake_case` IDs; travel rules live in the engine/services,
never in the UI.

## Ownership

| Concern | Owner |
| --- | --- |
| What places exist and how they connect | `LocationSystem` (`game/systems/location_system.py`) |
| "Where can I go, and why not?" | `TravelService` (`game/services/travel_service.py`) |
| Location content | `game/data/locations.json` |
| World-map marker coordinates | `map_position` on each location |

The UI only displays the current location, the destinations the service returns,
and any lock reason. It never decides whether travel is allowed.

The Godot frontend uses `frontend-godot/assets/sky_spill_continent_map.png` for
the world map. Each location stores a normalized `map_position` (`x`/`y` in the
`0.0..1.0` range), and `LocationSystem.view()` returns that coordinate so the UI
can place a current-location marker without hard-coded frontend positions.

See `DATA_SCHEMA.md` ("Location Schema") for the full per-location field list.

## World progression (Sky Spill Continent)

Travel fans out from the starting wilds into the kingdom, then outward by tier:

```text
Outer Forest / Azure Stream Village (start)
  -> Sky Fortune Road -> Sky Fortune Village -> Beast Mountain / Lin Academy
  -> Sky Fortune Capital
  -> Seven Profound Valleys (Outer Gate -> Inner Valley -> Forbidden Back Mountain)
  -> South Horizon Region (Route -> City -> Divine Phoenix Island -> Mystic Realm)
  -> South Sea Port
  -> Central Region (Four Great Divine Kingdoms) / Great Zen / Southern Wilderness
  -> Ancient Ruins / Five Element Temples
  -> Planetary Gate Array (ascension) / Holy Demon Continent (endgame)
```

## Cultivation gating

Each location's `requirements` block sets Body Transformation and Essence
Gathering realm minimums. `TravelService` compares them against the player's
realm order and returns one of these reasons when a move is blocked:

| Reason code | Meaning |
| --- | --- |
| `BODY_REALM_TOO_LOW` | Body Transformation realm below the minimum |
| `ESSENCE_REALM_TOO_LOW` | Essence Gathering realm below the minimum |
| `MISSING_REQUIRED_ITEM` | A required travel item is not in the inventory |
| `REPUTATION_TOO_LOW` | Player reputation below the minimum |
| `NO_ROUTE` | Destination is not connected to the current location |
| `ALREADY_THERE` / `UNKNOWN_LOCATION` / `NO_DESTINATION` | Invalid move |

`"None"`/`""`/`"any"` minimums mean the track does not gate the location. Frontends
should map these codes to player-facing text.

## Scope

- **V1 (playable core):** the safe early game through Academy, Seven Profound
  Valleys, and Divine Phoenix Island, plus the South Sea Port.
- **Locked future content:** the Central Region kingdoms, Great Zen, Southern
  Wilderness, Blood Slaughter Steppes, Five Element Temples, Ancient Ruins,
  Planetary Gate Array, and Holy Demon Continent remain in data but are gated
  behind late-mortal / ascension cultivation, so they show as reachable/locked
  rather than disappearing.

NPCs are anchored to locations by `character_id` only; add or move NPCs by
editing `npc_ids`, and add regions by editing `locations.json` — no code change
is required.

## Validation

- `validate_all_game_data()` checks unique IDs and that every
  `connected_locations` and `npc_ids` reference resolves, plus 0-10 danger/qi
  ranges, normalized map positions, and required requirement keys
  (`tests/test_all_game_data_valid.py`).
- `tests/test_locations_data.py` guards map structure: the whole graph is
  reachable from the start, the V1 core is present, and cultivation gates allow
  qualified travel while blocking underleveled endgame travel.
