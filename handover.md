# Martial Path — Handover

A data-driven cultivation (xianxia) RPG. The authoritative game logic is a Python
engine in `game/`; several frontends render its state and send commands. **All
gameplay rules live in the engine — never in a UI.**

Last updated: 2026-07-09. Test suite: **329 passing** (`pytest -q`). Data validation: clean.

---

## 1. Running the game

Use the project virtual environment at `.venv`.

| Frontend | Command | Notes |
|---|---|---|
| **Godot client** (primary) | See below | Talks to the FastAPI backend over HTTP |
| FastAPI backend | `& ".venv\Scripts\python.exe" -m uvicorn game.api.server:app --host 127.0.0.1 --port 8000` | Required for Godot |
| CLI | `& ".venv\Scripts\python.exe" main.py` | Text frontend |
| PySide6 desktop GUI | `& ".venv\Scripts\python.exe" gui_main.py` | Dark-fantasy dashboard |
| Tests | `& ".venv\Scripts\python.exe" -m pytest -q` | 329 tests |
| Data validation | `& ".venv\Scripts\python.exe" -c "from game.validation import validate_all_game_data as v; print(v().is_valid)"` | Cross-reference check |

### Godot (Godot 4.7)
1. Start the FastAPI backend (command above). Keep it running.
2. Open `frontend-godot/project.godot` in the Godot editor and press **F5**.
3. The client connects to `http://127.0.0.1:8000` (`ApiClient.gd` `BASE_URL`).

**Gotcha:** the backend runs **without** `--reload`, so after changing Python
engine code **or `game/data/**`** you must restart uvicorn for the Godot/HTTP
client to see it. GDScript changes require re-running the Godot project (F5).

**GDScript gotcha (grey screen):** the Godot project treats warnings as errors.
A `:=` that infers `Variant` — e.g. from the global `clamp()` / `min()` / `max()`
— is a hard **parse error** that fails the whole script, so `Main.tscn` renders
grey. Use the typed variants (`clampf` / `minf` / `maxf`) or an explicit `: float`.
Check Godot's **Output** panel for the offending line.

---

## 2. Architecture

Layered, one-directional dependencies:

```
ui/ (+ frontends)  ->  application/  ->  core/  ->  services/  ->  systems/  ->  models/ + data/
```

- `game/core/game_engine.py` — the single owner of mutable session state; wires
  systems, dispatches actions, builds the UI-agnostic `get_game_state()` snapshot.
- `game/systems/` — pure gameplay rules (no I/O, no UI). Return structured dicts
  tagged with an `EventType`.
- `game/services/` — thin coordination facades over systems.
- `game/data/registry.py` — loads every content collection once into an immutable
  `GameDataRegistry`.
- `game/validation/data_validator.py` — central cross-reference validation.
- `game/core/results.py` / `constants.py` — typed result dataclasses + `Action` /
  `EventType` StrEnums (the UI contract).

Detailed rules live in `.github/instructions/00`–`12` and `.github/skills/`.

---

## 3. Recent work

### This session

#### Exploration fix
- Named-character encounters are now **chance-gated** (`events.json`
  `character_encounter_chance`, default `0.35`): exploring a location with named
  NPCs still rolls combat/loot/special/nothing instead of *only* surfacing the
  characters.

#### Essence fatigue + stability (mirrors the body track)
- `EssenceCultivationState` gained `cultivation_strain` (fatigue) and
  `foundation_stability` (starts 100). `train_essence` builds strain; Essence
  breakthroughs are gated by `STRAIN_TOO_HIGH` / `FOUNDATION_UNSTABLE`; failed
  attempts raise strain + lower stability; success relieves strain.
- New **`STABILISE_ESSENCE`** action (mirrors `STABILISE_FOUNDATION`). Tuning lives
  in `cultivation_config.json` → **`essence_progression`**. Godot shows Essence
  Strain/Stability and a **Stabilise Essence** card.

#### Content discovery (skills / items / gear are now findable)
- **Technique manuals**: a learn-skill manual is **auto-generated for every skill**
  (`<skill_id>_manual`, `effect: learn_skill`). `USE_ITEM` on a manual learns +
  consumes it. `game/data/technique_manuals.json` = *optional* per-skill overrides
  (name/rarity/description) matched by `skill_id`. New pure `SkillSystem`.
- **Trainers**: `game/data/trainers.json` — location-bound masters teach skills for
  Gold / Spirit Stones. `TRAINERS` lists a location's offerings; `LEARN_SKILL`
  pays + learns. New `TrainerSystem`; Godot **Masters** card. Currency spending is
  shared with shops via `game/systems/currency.py`.
- **Exploration finds**: when a location has no curated loot pool, a `LOOT` event
  draws a **rarity-weighted, danger-gated** reward from the whole item/equipment
  catalogue via `events.json` → **`find_config`** (7-grade ladder
  `mortal_grade`→`dao_grade`; a location's `danger_level` caps the rarity). New
  `FindSystem`. Enemy loot + shops remain the curated channels.

#### Use Item (Godot)
- New **Use Item** action card + popup for consumables and technique manuals
  (sends `USE_ITEM`). The backend inventory view now returns `usable` / `effect`
  per item so the UI only offers items that actually do something.

#### Equipment data + validator fix
- Aligned the equipment rarity validator to the canonical 7-grade ladder (added
  `dao_grade`, dropped unused `profound_grade` / `divine_grade`).
- Corrected 24 stale realm requirements in `equipment.json`:
  `marrow_refining`→`tempering_marrow`, `blood_transformation`→
  `eight_gates_hidden_celestial_stems`, `golden_body`→`nine_stars_dao_palace`,
  `mortal_shedding`→`divine_transformation`. Data validation is clean again.

### Prior session (established baseline)

### Talent system (replaces Spiritual Root + Physique)
- New games roll **two independent talents**: a **Martial Talent** (essence
  aptitude) and a **Body Talent** (body aptitude), from
  `game/data/cultivation/martial_talents.json` and `body_talents.json`.
- Grades follow the `talent_system_update_prompt.md` ladder names; **Martial
  "Common Grade" is split into three sub-talents** (Common Grade (1)/(2)/(3),
  each slightly better), all mapping to tier 2.
- The player stores `martial_talent_id` / `body_talent_id`. Cultivation
  multipliers, roll weights, and upgrade hooks were migrated 1:1 (no rebalance).
- `game/data/cultivation/talents.json` is the shared 20-tier + Apex **ladder**
  (grade names, reachable realm, lifespan potential, canon/extrapolated source).
  Each rollable talent carries a `tier` linking into it. `TalentSystem`
  (`game/systems/talent_system.py`) is a pure read-only lookup over the ladder.
- `StartingFateSystem` now rolls the two talent tables (kept its name +
  `ROLL_STARTING_FATE` / `STARTING_FATE_ROLLED` plumbing to avoid CLI churn).

### Lifespan tracking
- `game/systems/lifespan_system.py` (pure). Characters start at **age 12**
  (`age_years`) and age by a **data-driven per-action time cost**
  (`cultivation_config.json` → `lifespan.time_costs`, in years).
- **Maximum lifespan follows the current Essence Gathering realm**
  (`max_lifespan_years` per realm in `essence_gathering_realms.json`; pre-essence
  characters use `lifespan.mortal_base_lifespan_years` = 100). Breakthroughs
  extend the cap; `beyond_divinity` is `null` = effectively immortal.
- Reaching the cap returns `EventType.PLAYER_DIED` and stops the run
  (`_die_of_old_age` in the engine).
- The player view exposes a read-only `lifespan` block: `age_years`, `year`
  (elapsed years since spawn; year 0 at start), `max_lifespan_years`,
  `remaining_years`, `immortal`, `display`.

### Equipment
- Equipment now gates on **actual cultivation (realm/stats)**, not talent. The
  `minimum_spiritual_root_rank` / `minimum_physique_rank` checks were removed;
  `EquipmentSystem` no longer takes the trait tables.

### Shops / spending
- Added **data-driven shops** in `game/data/shops.json`, loaded by
  `GameDataRegistry` and validated by the central data validator.
- New engine actions: `SHOP` lists the current-location market stock;
  `BUY_ITEM` purchases an item from available stock.
- `ShopSystem` (`game/systems/shop_system.py`) spends **Gold** from `player.gold`
  and **Spirit Stones** from the player's `spirit_stone` inventory count, then
  adds the purchased item to inventory. Buying equipment does **not** auto-equip;
  the existing `EQUIP_ITEM` flow still owns slot/requirement validation.
- Godot now shows a **Market** action card when `state.shops` is non-empty. It
  opens backend-returned stock/prices and sends `BUY_ITEM` for the selected ware.

### Save
- `SAVE_VERSION = 2` (talent IDs + `age_years`). Version-1 saves are rejected on load.

### Godot frontend (`frontend-godot/scripts/MainController.gd`)
- Character/Status panels show **Martial Talent**, **Body Talent**, and **Lifespan**.
- Top-right readout is now a **Year** counter (Year 0 at spawn, same year units as
  the lifespan system) instead of "Day / Morning".
- New **World Map** action opens `frontend-godot/assets/sky_spill_continent_map.png`
  and overlays the player's current location marker using backend
  `location.map_position` coordinates (normalized `x`/`y` in `0.0..1.0`, validated
  centrally). Placement math is `_position_world_map_marker` /
  `_world_map_content_rect` (assumes a 1.5 map aspect). Labeled landmarks sit on
  their markers; the early Sky Fortune cluster is a best-fit in the western region.
- New **Equipment** tab (order: Inventory | Equipment | Journal | Status |
  Techniques) listing all 11 gear slots (equipped item + rarity, or `(empty)`).
  The EQUIPPED block was removed from the Inventory tab.
- Old-age death shows a **"Your Dao Ends"** screen (`PLAYER_DIED`).

### Location art
- Added 8 missing location images to `frontend-godot/assets/locations/`
  (`ancient_ruins`, `blood_slaughter_steppes`, `five_element_temples`,
  `holy_demon_continent`, `planetary_gate_array`, `rival_divine_kingdom`,
  `southern_wilderness`, `zenlight_monastery`). Source art lives in `Images/`.

---

## 4. Key data files

| File | Purpose |
|---|---|
| `game/data/cultivation/martial_talents.json` | Rollable Martial (essence) talents |
| `game/data/cultivation/body_talents.json` | Rollable Body talents |
| `game/data/cultivation/talents.json` | 20-tier + Apex talent ladder (names/realm/lifespan potential) |
| `game/data/cultivation/essence_gathering_realms.json` | Essence realms + per-realm `max_lifespan_years` |
| `game/data/cultivation/body_transformation_realms.json` | Body realms |
| `game/data/cultivation/cultivation_config.json` | Training methods, **`body_progression` + `essence_progression`** (strain/stability tuning), `lifespan` block (starting age, mortal base, time_costs) |
| `game/data/locations.json` | 29 world-map locations (art + `map_position` marker coords keyed by `id`) |
| `frontend-godot/assets/sky_spill_continent_map.png` | World map image used by the Godot marker popup |
| `game/data/equipment.json` | Equipment (gated by realm/stats) |
| `game/data/shops.json` | Location-bound markets and item/equipment prices |
| `game/data/trainers.json` | Location-bound skill trainers (teach skills for currency) |
| `game/data/technique_manuals.json` | Optional per-skill manual overrides (manuals auto-generated otherwise) |
| `game/data/events.json` | Encounter weights, `character_encounter_chance`, and `find_config` (rarity-weighted exploration finds) |

Docs: `game/docs/ARCHITECTURE.md`, `CULTIVATION_SYSTEM.md`, `DATA_SCHEMA.md`,
`SAVE_SYSTEM.md`, `EQUIPMENT_SYSTEM.md`, `CHANGELOG.md`.

---

## 5. Testing & validation

- `pytest -q` — full suite (329). Newest: `tests/test_skill_system.py`,
  `tests/test_trainer_system.py`, `tests/test_find_system.py` (plus prior
  `test_lifespan_system.py`, `test_talent_system.py`, `test_shop_system.py`).
- `validate_all_game_data()` — validates talent tracks, realm lifespans, the
  talent ladder, equipment (rarity ladder + realm refs), shops, **trainers**,
  **technique-manual overrides**, **`find_config`**, **`essence_progression`**,
  normalized map positions, and all cross-references.
- Systems are testable without a UI (inject data + a seeded `RNG`).

---

## 6. Known follow-ups / open items

- **Manuals not yet in the wild**: a manual exists for every skill, but none are
  referenced in loot tables or shops yet. Add `<skill_id>_manual` ids to enemy
  `loot_table`s / `shops.json` to make specific techniques findable/buyable.
- **Equipment realm mappings**: two of the four corrected realm requirements were
  judgment calls (`blood_transformation`→`eight_gates_hidden_celestial_stems`,
  `mortal_shedding`→`divine_transformation`, chosen with the user). Re-tune in
  `equipment.json` if the gating tier feels off.
- **CLI / PySide parity**: the new Use Item, Trainers/Masters, manual-learning, and
  essence Stabilise flows are engine-wired but only surfaced in the Godot client
  (plus CLI verbs `learn` / `masters`). The desktop GUIs weren't updated.
- **`divine_phoenix_mystic_realm` has no artwork** (no source image). It shows the
  name-label fallback; could reuse the Divine Phoenix Island art.
- **Talent upgrade paths**: the weight-0 upgrade trait entries were dropped in the
  migration. Re-add later (mapped to the ladder) for a "refine your talent" feature.
- **Realm-scaled time costs**: aging cost is currently flat per action; could scale
  by realm.
- **CLI/PySide talent labels**: those frontends were intentionally left untouched
  (UI work was Godot-only). The fate roll result keeps legacy `spiritual_root` /
  `physique` keys as a compatibility shim, so CLI still shows the old labels. Also
  the cultivation system's private helper names (`_spiritual_root_float`,
  `_spiritual_roots_by_id`) were kept — they now hold talent data.
- **Backend `--reload`**: not enabled; restart uvicorn manually after engine edits.
- **Godot equipment layout**: currently a slot **list**; a paper-doll/grid layout
  is a possible future enhancement.
- **Shop depth**: current shop stock is static and location-bound. Dynamic stock
  depletion, sell-back, sect contribution stores, and auction bidding are future
  enhancements.
- **World-map marker accuracy**: labeled landmarks (Seven Profound Valleys, Divine
  Phoenix Island, the four kingdoms, Zenlight, Five Element, Holy Demon, etc.) sit
  on their markers, but the early Sky Fortune cluster is not individually drawn on
  the continental map and is placed as a best-fit in the west. Nudge individual
  `map_position` values in `locations.json` if a spot looks off.

---

## 7. Project conventions

- Data-driven first: JSON + stable snake_case IDs over hard-coded values.
- Keep gameplay logic out of UIs; UIs display state and send commands only.
- ASCII only inside player-facing printed strings (Windows console is cp1252).
- Update the relevant `game/docs/` files and `CHANGELOG.md` alongside changes.
- Original lore only — no copyrighted names/sects/techniques.
