# Martial Path — Handover

A data-driven cultivation (xianxia) RPG. The authoritative game logic is a Python
engine in `game/`; several frontends render its state and send commands. **All
gameplay rules live in the engine — never in a UI.**

Last updated: 2026-08-14. Test suite: **414 passing, 3 skipped** (`pytest -q`).
Data validation: clean (**0 errors**).

---

## 1. Running the game

Use the project virtual environment at `.venv`.

| Frontend | Command | Notes |
|---|---|---|
| **Godot client** (primary) | See below | Talks to the FastAPI backend over HTTP |
| FastAPI backend | `& ".venv\Scripts\python.exe" -m uvicorn game.api.server:app --host 127.0.0.1 --port 8000` | Required for Godot |
| CLI | `& ".venv\Scripts\python.exe" main.py` | Text frontend (frozen — see Conventions) |
| PySide6 desktop GUI | `& ".venv\Scripts\python.exe" gui_main.py` | Dark-fantasy dashboard (frozen — see Conventions) |
| Tests | `& ".venv\Scripts\python.exe" -m pytest -q` | 414 tests |
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

---

## 3. Recent work (2026-08-14, the GROK-review close-out)

This session executed the full **17-priority roadmap** derived from a code review
(see `Tasks.md` for the measurable criteria and evidence of each). Summary by theme:

### Combat & skills
- **All 26 skill effect types now do something.** `CombatSystem` resolves
  `damage`, `true_damage`, `aoe_damage`, `execute`, `life_steal`, `heal_self`,
  `stun`, `dot_damage`, `shield`, `counter`, `debuff_attack`, `debuff_defense`
  plus a shield/status model; `StatsSystem` honours the full passive set
  (`buff_*`, `crit_*`, regen, `qi_cost_reduction`). Meta-passives
  (`comprehension_gain`, `lifespan`, `cultivation_speed`) are wired into
  learn/lifespan/cultivation.
- **Spar vs duel are distinct.** Spars end at 25% HP with no loot/exp/penalty;
  duels/exploration keep full stakes.
- **Defeat penalty is data-driven** (`cultivation_config.defeat_penalty`): 25%
  body-progress loss + revive ratios, not a wipe.
- **Enemy abilities** (`heavy`/`poison`/`stun` with chance+magnitude) on 4 named
  foes; enemy stun forfeits the player's turn.

### Martial growth economy
- Every skill has an auto-generated manual; `tools/seed_techniques.py` seeds them
  into enemy loot, shops, and encounter pools — **0 unreachable skills** (was 205).
- `trainers.json` (8 trainers) teaches all 208 skills; 4 path-locked secret arts.
- **Talent upgrades** (`talents` / `upgrade <track> <target>`) chain every talent
  into the next grade, gated by the rare **`talent_refining_elixir`** (not gold).
  The elixir is reachable through encounters (high-danger pools + enemy drops),
  Masters (relationship reward), and late-game shops.

### Social & faction
- **Dialogue choices** (`dialogue.choices[]`) mutate relationship/morality/
  reputation; `TALK_TO_CHARACTER` returns available choices.
- **Relationship-gated rewards** (`relationship_rewards`) are claimable one-time
  boons via `RECEIVE_BOON`, tracked in NPC memory flags.
- **Sects** (`sects.json`, 4 sects): `JOIN_SECT` sets `player.path`; joining
  gates on realm + reputation.

### World & progression
- **Quest chains**: 3 → 9 quests with `requires` gates (completed quests,
  reputation, location) and skill/manual rewards.
- **Economy**: `SELL_ITEM`, 3 → 12 shops, spirit-stone sinks.
- **Time model**: `closed_door <years>` seclusion, seasons, realm-scaled aging.
- **Save/meta**: ironman flag, NG+ scaling bonus, portable `export`/`import`
  (cloud substitute).

### Frontend (Godot only)
- Full GUI restructure per `Martial_Path_GUI_Master_Prompt_Final.md`: top bar
  (Year + tabs), 3-column body with a permanent event log, floating tab overlays,
  monogram portrait, location chips + clickable exits, grouped actions, paper-doll
  equipment slot grid.
- Item interaction consolidated into the **Inventory** overlay (Use/Equip/Unequip
  buttons); the main Actions hub's *Commerce & Support* grid keeps only Market +
  Masters.

---

## 4. Key data files

| File | Purpose |
|---|---|
| `game/data/cultivation/martial_talents.json` / `body_talents.json` | Rollable Martial/Body talents (with `upgrade_options` chains) |
| `game/data/cultivation/talents.json` | 20-tier + Apex talent ladder |
| `game/data/cultivation/essence_gathering_realms.json` | Essence realms + per-realm `max_lifespan_years` |
| `game/data/cultivation/cultivation_config.json` | Training methods, strain/stability, `lifespan`, `defeat_penalty`, `closed_door`, realm aging |
| `game/data/locations.json` | 29 world-map locations (art + `map_position`) |
| `game/data/sects.json` | 4 sects (path, join requirements, contribution ranks) |
| `game/data/encounter_pools.json` | Location loot pools |
| `game/data/character_enemies/named_foes.json` | Named foes (abilities) |
| `game/data/equipment.json` | Equipment (realm-gated; some with `set_id` + durability) |
| `game/data/items.json` | Items incl. `talent_refining_elixir` |
| `game/data/shops.json` | 12 location-bound markets |
| `game/data/trainers.json` | Skill trainers (teach for currency; `required_path`) |
| `game/data/technique_manuals.json` | Optional per-skill manual overrides |
| `game/data/events.json` | Encounter weights, `character_encounter_chance`, `find_config` |
| `frontend-godot/assets/sky_spill_continent_map.png` | World map image |

Seed generators live in `tools/` (all deterministic + idempotent):
`seed_techniques.py`, `seed_shops.py`, `seed_talent_upgrades.py`,
`seed_talent_resources.py`, `seed_equipment_sets.py`, `seed_enemy_abilities.py`,
`normalize_available_systems.py`, `gen_missing_location_art.py`.

Docs: `game/docs/ARCHITECTURE.md`, `CULTIVATION_SYSTEM.md`, `DATA_SCHEMA.md`,
`SAVE_SYSTEM.md`, `EQUIPMENT_SYSTEM.md`, `CHANGELOG.md`. Roadmap: `Tasks.md`.

---

## 5. Testing & validation

- `pytest -q` — **414 passed, 3 skipped**. Newer files: `test_medium_priority.py`
  (the P10–P17 close-out), `test_sell_system.py`, `test_sect_system.py`,
  `test_relationship_rewards.py`, plus combat/trainer/find/lifespan/talent/shop.
- `validate_all_game_data()` — validates skills/effects, talents + upgrade chains
  + elixir costs, trainers (+ `required_path`), shops, sects, quests, equipment
  (rarity, realm, sets, durability), items, enemy abilities, encounter pools,
  normalized `available_systems`, and map-position duplicates. **0 errors.**
- Systems are testable without a UI (inject data + a seeded `RNG`).

---

## 6. Known follow-ups / open items

- **Deferred (needs an external service):** cloud save (local `export`/`import`
  ships instead) and a full LLM dialogue layer (`ai_prompt_notes` is surfaced as
  a `(manner: …)` line, but no generated dialogue).
- **Untested at runtime here:** PySide6 (`gui_main.py`) and the Godot paper-doll
  render — both compile/parse clean but weren't executed against a display.
- **New engine actions not yet surfaced as dedicated Godot widgets:** `talents`,
  `closed_door`, `repair`, `export`, `import` work through the API/state but have
  no bespoke Godot buttons/panels yet (Godot renders them via generic handling).
- **`BOON` narration gap in Godot:** the "Receive Reward" button appears from the
  backend `options`, but `MainController._render_event` has no `BOON` case, so the
  reward result isn't logged visually (it is granted by the backend).
- **Sect contribution ranks** exist as data but there is no contribution-earning
  mechanic yet (tasks, inner/outer disciple progression, sect store).
- **Subjective map placement:** the early Sky Fortune cluster is a best-fit (no
  reference coordinates); the objective guard (no duplicate markers) is enforced.
- **Backend `--reload`:** not enabled; restart uvicorn manually after engine edits.

---

## 7. Project conventions

- Data-driven first: JSON + stable snake_case IDs over hard-coded values.
- Keep gameplay logic out of UIs; UIs display state and send commands only.
- **Frontend scope: only the Godot interface (`frontend-godot/`) is updated.**
  Do NOT modify the CLI (`game/ui/cli_interface.py` + its
  `game/application/command_router.py` translator) or the PySide6 interface
  (`game/ui/gui_interface.py`). Engine/data/system changes are fine, but any
  player-facing UI work lands in Godot only.
- ASCII only inside player-facing printed strings (Windows console is cp1252).
- Update `Tasks.md` / `handover.md` and the relevant `game/docs/` files alongside
  changes.

---

## 8. Next steps (proposed)

Priority-ordered ideas to progress the game further (none started):

1. **Sect contribution loop** — earn contribution via sect tasks / sparring,
   spend it at a sect store, promote inner/outer disciple ranks that unlock
   path-locked techniques and higher trainers.
2. **Alchemy / gathering loop** — make `gather` a real verb at herb-rich
   locations, then refine herbs (with the `talent_refining_elixir` as a template)
   into pills that feed cultivation and combat.
3. **Multi-enemy & boss-fight combat** — formations/positioning and phased boss
   encounters to break the 1v1 monotony; tie named foes to quests.
4. **Companion / relationship depth** — let bonded NPCs travel and fight with the
   player, and gate more content on relationship tiers.
5. **Sect tournament / arena ladder** — a recurring ranked sparring event as a
   mid-game loop and a reputation/contribution sink.
6. **Seasonal weather effects** — P12 added seasons as display; make seasons
   modify travel, gathering, and encounter odds for real texture.
7. **Surface the new actions in Godot** — bespoke widgets for `talents`,
   `closed_door`, `repair`, `export`/`import`, and the `BOON` result narration.
8. **Cloud save + LLM dialogue** — once an external service is chosen, wire the
   two deferred items from §6.
