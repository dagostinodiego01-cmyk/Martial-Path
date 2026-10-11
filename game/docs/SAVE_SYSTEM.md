# Save System

Persistence is split into two layers so storage and policy stay independent:

- `game/persistence/save_repository.py` — `SaveRepository` owns *where* saves live
  (see "Location" below), sanitises slot names against path traversal, and
  reads/writes raw JSON atomically. It knows no schema version.
- `game/services/save_service.py` — `SaveService` owns *policy*: it stamps the
  schema `version` on write, migrates older versions forward on read, and
  raises `SaveError` with a stable code (`SAVE_NOT_FOUND`, `SAVE_CORRUPT`,
  `SAVE_VERSION_MISMATCH`, `WRITE_FAILED`). It delegates all I/O to a
  `SaveRepository`, so a future cloud or alternate backend only needs a new
  repository.

`GameEngine` owns the session snapshot: `save_game(slot)` builds a snapshot
(`player.to_save_dict()`, quest state, the run seed, every RNG stream, and the
session-side world/cooldown/fate state) and hands it to `self.saves.write`;
`load_game(slot)` reads a validated snapshot and reconstructs the session. The
cultivation state is serialized through `CultivationState.to_dict()` /
`CultivationState.from_dict()`.

## Location

Saves default to `%APPDATA%/MartialPath/saves` on Windows (`~` elsewhere). The
`MARTIAL_PATH_SAVE_DIR` environment variable overrides that directory — used
by portable installs and by the test suite, which must never write into a real
save directory.

## Schema versions and migration

`SAVE_VERSION = 3`. Reads migrate older saves forward; anything else is
rejected rather than guessed at.

| From | To | What the migration does |
|---|---|---|
| v1 | v2 | Renames the starting-talent fields from the old Spiritual Root / Physique names (`spiritual_root_id` / `physique_id`) to the stable ids (`martial_talent_id` / `body_talent_id`). |
| v2 | v3 | Installs the documented defaults for the v3 session fields (see below). |
| v3 | — | Loaded as-is. |
| absent / 0 / future | — | `SAVE_VERSION_MISMATCH`. A non-integer version is `SAVE_CORRUPT`. |

`SaveService.write` also migrates a payload that carries an older `version`
(an imported portable save), so stale data can never be mislabelled as current.

**v3 defaults for v2 saves:** `seed: null`, `rng: {}`, `world_seed: {}`,
`last_world_report: {}`, `cooldowns: {}`, `encounter_seq: 0`,
`fate: {accepted: true, pending: null}`, `active_realm: null`,
`tournament_active: false`, `oath_stakes: null`, `running: true`. A migrated
v1/v2 save therefore **loads with stable player/world state but does not
promise bit-identical continuation** — the deterministic contract below only
holds for saves written at v3.

## Deterministic continuation (SV.5)

A v3 snapshot carries everything needed for a *fresh process* that loads it to
produce the same event sequence and state digest as the original run:

- `seed` — the run seed (also re-keyed into `NarrativeSystem`, whose
  `render_stable` prose is drawn from a local RNG keyed by the run seed).
- `rng` — the full `random.Random` internal state of all five gameplay
  streams: `main` (cultivation, combat, loot, finds, encounters, fate),
  `narrative` (action-boundary prose), `foe_ai` (enemy rolls), `debate`
  (conviction rolls), and `world` (living-world ticks). `RNG.get_state()` /
  `RNG.set_state()` in `game/utils/rng.py` are the JSON-safe serialisation.
- `world_seed` — the seed-derived world variation (`dominant_sects`,
  `economy_multiplier`) normally computed at construction; restoring it
  re-points `SectSystem`'s dominance and the shop economy band.
- Session state: `world_state`, `last_world_report`, `cooldowns`,
  `encounter_seq`, `fate`, `active_realm`, `tournament_active`, `oath_stakes`,
  `running`.

Pinned by `tests/test_save_continuation.py`, which replays a recorded
playthrough, saves at a safe point, loads the save **in a separate Python
process built from an unrelated seed**, plays the remaining actions there, and
compares the event list and final state digest against the original run.

## Safe points and autosave (SV.2)

A snapshot never contains transient combat/encounter/debate state, so saving
is restricted to **safe points** — `GameEngine.at_safe_point()`: exploration
turns with no scene open (after a resolved action, at camp/arrival), with the
starting fate accepted.

- **Explicit save** (`SAVE`, `/save`) at an unsafe point is refused with
  `UNSAFE_SAVE_POINT` rather than silently dropping the scene on load.
- **Autosave** (`GameEngine.autosave()`) fires only after a successful turn at
  a safe point. The API layer calls it after every non-refused `/action` (API
  server only — one policy, one place).
- **Never auto-saved:** mid-combat, mid-encounter, mid-debate, before fate
  acceptance, and after a run has ended. A refusal is not a turn, so it never
  autosaves either.

## Crash safety (SV.6)

Writes are atomic and leave the previous save recoverable:

1. The payload is serialised **before any file is touched** (an unserialisable
   snapshot fails with `WRITE_FAILED` and the old file is intact).
2. It is written to `<slot>.json.tmp` and fsynced.
3. The existing `<slot>.json` is moved aside to `<slot>.json.bak`.
4. The temp file becomes `<slot>.json`.

Every interruption window therefore leaves the new save, or the old save in
place, or the old save in `.bak` — never a truncated file. `read_raw` falls
back to `.json.bak` when the primary file is missing or unparseable
(`SAVE_CORRUPT` is only raised when *both* generations are unreadable), and a
slot whose primary file is missing still lists. `.bak`/`.tmp` files never
appear as separate slots.

Pinned by the SV.6 tests in `tests/test_save_system.py` (serialisation
failure, interrupted promote, corrupt primary, listing recovery).

## Transport contract (API.1–API.3)

- `game/api/action_contract.json` is the versioned field contract for
  `POST /action`; `ActionRequest` is pinned against it by
  `tests/test_api_server.py`. Unknown fields are **422** (`extra="forbid"`),
  as are a missing `action` or a wrong type — a typo'd key must not silently
  no-op. The Godot client must be checked against the same fixture (M3).
- The local server holds a single session lock around every endpoint that
  touches the engine (`API.2`): concurrent `/action`, `/save`, `/load`,
  `/new-game` are serialised, never interleaved.
- `tests/test_api_live_http.py` boots a real `uvicorn` subprocess and
  exercises state/action/save/load, 422 contract violations, and concurrent
  mutations over actual HTTP.

## Cultivation Save Shape

Save data stores both tracks separately using stable IDs:

```json
{
  "cultivation": {
    "body_transformation": {
      "realm_id": "tempering_marrow",
      "progress": 40.0,
      "foundation": 62.5,
      "cultivation_strain": 22.0,
      "foundation_stability": 84.0
    },
    "essence_gathering": {
      "realm_id": "xiantian",
      "substage": "Middle",
      "progress": 68.0,
      "foundation": 58.0,
      "cultivation_strain": 15.0,
      "foundation_stability": 88.0
    }
  }
}
```

The player save snapshot stores starting talents by stable IDs only, plus the
character's `age_years`. Multiplier values are loaded from
`game/data/cultivation/martial_talents.json` and
`game/data/cultivation/body_talents.json`, not copied into saves. Older saves
that do not contain these IDs default to `earth_grade` and `iron_skin_grade`.

Equipment is saved as slot item IDs only; derived equipment stat totals are not
saved. Older saves without `equipment` default every slot to empty.

## Validation Expectations

Load validation should reject:

- unknown body realm IDs.
- unknown essence realm IDs.
- invalid essence substages for the saved realm.
- Essence saves that still reference the removed `essence_pulse_condensation` ID.
- reachable theoretical endpoints.
- unknown `spiritual_root_id` or `physique_id` once strict save validation is added.
- unknown equipped item IDs once strict save validation is added.

`CultivationSystem.validate_cultivation_data(save_data)` already validates
cultivation realm IDs and substages for the shape above.
