# Save System

Persistence is split into two layers so storage and policy stay independent:

- `game/persistence/save_repository.py` — `SaveRepository` owns *where* saves live
  (`%APPDATA%/MartialPath/saves` on Windows, `~` elsewhere), sanitises slot names
  against path traversal, and reads/writes raw JSON. It knows no schema version.
- `game/services/save_service.py` — `SaveService` owns *policy*: it stamps the
  schema `version` on write, validates it on read, and raises `SaveError` with a
  stable code (`SAVE_NOT_FOUND`, `SAVE_CORRUPT`, `SAVE_VERSION_MISMATCH`,
  `WRITE_FAILED`). It delegates all I/O to a `SaveRepository`, so a future cloud
  or alternate backend only needs a new repository.

`GameEngine` owns the session snapshot: `save_game(slot)` builds a snapshot
(`player.to_save_dict()` plus quest state) and hands it to `self.saves.write`;
`load_game(slot)` reads a validated snapshot and reconstructs the player. The
cultivation state is serialized through `CultivationState.to_dict()` /
`CultivationState.from_dict()`.

## Cultivation Save Shape

Save data should store both tracks separately using stable IDs:

```json
{
  "save_version": "0.1.0",
  "cultivation": {
    "body_transformation": {
      "realm_id": "tempering_marrow",
      "progress": 40.0,
      "foundation": 62.5,
      "opened_gates": [],
      "opened_stars": [],
      "marrow_percent": 40.0,
      "body_strength": 128.0,
      "breakthrough_failures": 1,
      "cultivation_strain": 22.0,
      "foundation_stability": 84.0,
      "daily_cultivation_count": 2,
      "last_cultivation_day": 7
    },
    "essence_gathering": {
      "realm_id": "xiantian",
      "substage": "Middle",
      "progress": 68.0,
      "foundation": 58.0,
      "dantian_capacity": 95.0,
      "true_essence_density": 42.0,
      "circulation_stability": 76.0,
      "life_destruction_fall": 0,
      "inner_world_development": 0.0,
      "breakthrough_failures": 0,
      "cultivation_strain": 15.0,
      "foundation_stability": 88.0
    }
  }
}
```

The player save snapshot also includes `current_day`. Current day is intentionally minimal: it lets repeated same-day cultivation use diminishing returns and gives rest/stabilising foundation a backend time cost without introducing a full calendar system.

The player save snapshot stores starting talents by stable IDs only, plus the
character's `age_years`:

```json
{
  "martial_talent_id": "earth_grade",
  "body_talent_id": "iron_skin_grade",
  "age_years": 12.0
}
```

Multiplier values are loaded from `game/data/cultivation/martial_talents.json`
and `game/data/cultivation/body_talents.json`, not copied into saves. Older saves
that do not contain these IDs default to `earth_grade` and `iron_skin_grade`. The
save schema is at version 2; version-1 saves (which used the earlier Spiritual
Root / Physique fields) are rejected on load.

Equipment is saved as slot item IDs only:

```json
{
  "equipment": {
    "weapon": null,
    "armor": null,
    "boots": null,
    "cloak": null,
    "ring_1": "minor_qi_ring",
    "ring_2": null,
    "amulet": null,
    "talisman": null,
    "artifact_1": null,
    "artifact_2": null,
    "flying_sword": null
  }
}
```

Derived equipment stat totals are not saved. Older saves without `equipment`
default every slot to empty.

## Validation Expectations

When a full save service is added, load validation should reject:

- unknown body realm IDs.
- unknown essence realm IDs.
- invalid essence substages for the saved realm.
- Essence saves that still reference the removed `essence_pulse_condensation` ID.
- reachable theoretical endpoints.
- unknown `spiritual_root_id` or `physique_id` once strict save validation is added.
- unknown equipped item IDs once strict save validation is added.

`CultivationSystem.validate_cultivation_data(save_data)` already validates cultivation realm IDs and substages for the shape above.