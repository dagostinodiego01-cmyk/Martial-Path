# Architecture

This document explains the layered design of the cultivation RPG engine, the
data flow between layers, why the UI is decoupled, and exactly how to replace the
CLI with a different frontend.

The guiding principle is **separation of concerns with a one-directional
dependency flow**: high-level layers depend on lower-level ones, never the
reverse, and the UI is fully replaceable.

---

## 1. Layer separation

```
┌──────────────────────┐
│      UI LAYER        │  ui/cli_interface.py
│  print / input ONLY  │
└─────────┬────────────┘
          │
┌─────────▼────────────┐
│   APPLICATION LAYER  │  application/command_router.py
│  input -> commands   │
└─────────┬────────────┘
          │
┌─────────▼────────────┐
│   GAME ENGINE CORE   │  core/game_engine.py
│  orchestration/state │
└─────────┬────────────┘
          │
┌─────────▼────────────┐
│      SERVICES        │  services/*.py
│ player-facing APIs   │
└─────────┬────────────┘
          │
┌─────────▼────────────┐
│       SYSTEMS        │  systems/*.py
│  pure gameplay rules │
└─────────┬────────────┘
          │
┌─────────▼────────────┐
│     DATA LAYER       │  data/*.json  +  models/*.py
└──────────────────────┘
```

| Layer           | Responsibility                                           | May call `print`/`input`? |
| --------------- | -------------------------------------------------------- | ------------------------- |
| **UI**          | Read input, format and display output                    | **Yes — only here**       |
| **Application** | Translate raw strings into canonical actions             | No                        |
| **Core**        | Own state, coordinate systems/services, process actions  | No                        |
| **Services**    | Coordinate player lookup and stable feature APIs         | No                        |
| **Systems**     | Implement gameplay rules, return structured results      | No                        |
| **Models/Data** | Hold state and content                                   | No                        |

### The non-negotiable rules

1. The **game engine and systems never call `input()` or `print()`**.
2. The engine returns **structured data** — dictionaries tagged with an
   `EventType` — never formatted text.
3. The **UI is the only layer** that prints, formats text, or reads input.
4. Systems accept structured inputs (model objects, ids, an `RNG`) and return
   structured outputs, with no UI logic inside them.

> Diagnostic logging (`utils/logger.py`) is deliberately *not* considered UI. It
> uses the standard `logging` module for developers and never emits player text.

---

## 2. Data flow

A single command travels down through the layers and a structured result travels
back up to be rendered:

```
USER INPUT (UI)
      │  "skill iron_fist"
      ▼
CommandRouter.route()            (Application)
      │  {"action": "USE_SKILL", "skill_id": "iron_fist"}
      ▼
GameEngine.process_action()      (Core)
      │  delegates to the right system, mutates state
      ▼
CombatSystem.use_skill()         (Systems)
      │  returns a structured result
      ▼
{"event": "COMBAT_TURN", "turn_events": [...], "player_hp": 92, ...}
      ▲
      │  result bubbles back up unchanged
      ▼
CLIInterface._render()           (UI)
      │  picks a formatter by EventType and prints text
      ▼
"  You unleash Iron Fist for 22 damage!"
```

### The engine contract

The entire core exposes just two methods to the outside world:

```python
def process_action(self, action: dict) -> dict
def get_game_state(self) -> dict
```

Plus two small conveniences the UI uses to drive its loop:
`is_running() -> bool` and `set_player_name(name)`.

Every result dictionary carries an `event` key (an `EventType`) that the UI uses
to choose a formatter. Example results:

```python
# Body training
{"event": "TRAIN_RESULT", "track_id": "body_transformation", "gained": 14.0,
 "progress": 14.0, "exp_gained": 5, "ready_to_breakthrough": False,
 "cultivation": "Strength Training"}

# Essence training
{"event": "TRAIN_RESULT", "track_id": "essence_gathering", "gained": 10.0,
 "progress": 10.0, "exp_gained": 0, "ready_to_breakthrough": False,
 "cultivation": "Early Houtian"}

# Breakthrough (level up)
{"event": "BREAKTHROUGH_RESULT", "success": True,
 "previous": "Body Tempering Stage 1", "cultivation": "Body Tempering Stage 2",
 "realm_changed": False, "gains": {"max_hp": 30, "max_qi": 16, "attack": 5, "defense": 3}}

# A combat round
{"event": "COMBAT_TURN", "turn_events": [...],
 "player_hp": 92, "enemy_hp": 23, "enemy_name": "Iron-Fang Wolf"}
```

Notice there is **no text** in any of these — only data. The UI decides wording.

### The command contract

`CommandRouter` is the single source of truth for **parsing text input** into
canonical engine commands. It is not the only way to *produce* commands: graphical
and API frontends may construct canonical command dictionaries directly, as long
as they use `Action` constants and obey the engine command contract.

All frontends ultimately send dictionaries of this shape into the engine:

```python
{"action": Action.TRAIN}
{"action": Action.USE_ITEM, "item_id": "healing_pill"}
{"action": Action.USE_SKILL, "skill_id": "iron_fist"}
```

* **Text frontends** (the CLI) call `CommandRouter.route(raw_text)`.
* **Button / API frontends** (the PySide6 GUI) build these dictionaries directly
  from structured input such as a button click, bypassing the router.

### State ownership

The engine is the single owner of mutable session state:

* the `Player`,
* the current game **mode** (`explore` vs `combat`),
* the current `Enemy` (during combat),
* active skill **cooldowns**,
* the `running` flag.

Systems are stateless with respect to the session — they receive the objects
they operate on and return results. This keeps state changes centralized and
predictable.

`StartingFateSystem` follows the same rule: it receives the Martial Talent and
Body Talent tables plus the seeded RNG, rolls weighted talent IDs, and returns
UI-safe talent views. `GameEngine.new_game()` owns the roll and immediately
stores the resulting stable talent IDs on the player so a new game starts
playable without frontend-side logic.

`TalentSystem` is a pure read-only lookup over the data-driven talent tier
ladder (`cultivation/talents.json`). It resolves a shared tier index into
UI-safe views carrying both the Martial and Body-cultivation talent names, the
reachable realm, and the maximum lifespan; it holds no player state and applies
no progression rules.

`LifespanSystem` is a pure, data-driven rules object: it computes a character's
current maximum lifespan from their Essence realm (mortal base before Essence is
unlocked), advances age by a per-action time cost, and reports expiry. The engine
ages the player after time-consuming actions and ends the run on old-age death.

`EquipmentSystem` also follows this split. It validates equip/unequip requests,
checks inventory ownership and requirements, stores only slot item IDs on the
player, and aggregates modifiers for systems such as stats and cultivation.
Derived stat calculations consume those modifiers without mutating base player
stats.

`ShopSystem` is the commerce rules object. It receives registry-loaded shop
data and the item catalog, lists shops available at the player's current
location, validates offered stock and supported currencies, spends Gold or
Spirit Stone inventory items, and adds purchased items to inventory. UI layers
only render returned shop stock and send `SHOP` / `BUY_ITEM` commands.

Content discovery is split across three pure systems. `SkillSystem` owns the
"can this player learn this technique?" rule and records it on the player.
`TrainerSystem` mirrors `ShopSystem`: it lists location-bound technique masters
(`data/trainers.json`), spends currency via the shared `currency` helper, and
delegates the actual learning to `SkillSystem` (`TRAINERS` / `LEARN_SKILL`).
Technique *manuals* are learn-skill items — one auto-generated per skill by
`GameEngine`, overridable via `data/technique_manuals.json` — so `USE_ITEM`
routes manuals to `SkillSystem` (consuming the manual). `FindSystem` performs
rarity-weighted, danger-gated selection over the item/equipment catalogue for
exploration finds; the engine supplies the area's rarity cap from the location's
`danger_level`, and `EventSystem` uses it when a location has no curated loot.

Named character interactions are coordinated by `GameEngine` and
`CharacterService`. When a location has named characters, exploration has a
data-driven chance (`events.json` `character_encounter_chance`) to return a
`CHARACTER_ENCOUNTER` result with backend-provided Talk/Spar/Duel options;
otherwise it rolls a normal random event, so characters never crowd out other
encounters. Talk returns read-only dialogue context; Spar/Duel validate
availability through `CharacterService` and then spawn the named enemy template
from `character_enemies`.

---

## 3. Why the UI is decoupled

Coupling game rules to a specific presentation is the most common reason a
prototype cannot grow. By forbidding UI concerns in the core we gain:

* **Portability** — the same engine runs behind a terminal, a browser, a game
  engine, or an HTTP API.
* **Testability** — systems and the engine can be unit-tested by asserting on
  returned dictionaries; no stdout capture or input mocking required.
* **Parallel development** — UI and gameplay can evolve independently as long as
  the `EventType` contract holds.
* **Determinism** — all randomness flows through a single seedable `RNG`
  (`utils/rng.py`), so tests can reproduce exact scenarios.

---

## 4. How to replace the CLI

Because the frontend only depends on the engine contract, replacing it is
mechanical. The composition root (`main.py`) is the only wiring that changes:

```python
engine = GameEngine.new_game()   # unchanged
router = CommandRouter()         # unchanged
ui = CLIInterface(engine, router)  # <-- swap ONLY this line
ui.run()
```

Any replacement UI performs the same three steps the CLI does:

```python
command = router.route(raw_input_text)      # 1. structure the input
result = engine.process_action(command)     # 2. run it through the engine
render(result)                              # 3. present the structured result
```

### Example: swap the CLI for a Web UI (React + API)

Replace `cli_interface.py` with a thin HTTP layer; **all core systems stay
unchanged**.

```python
# web_api.py  (a new UI layer — no changes to core/systems/models)
from fastapi import FastAPI
from game.application.command_router import CommandRouter
from game.core.game_engine import GameEngine

app = FastAPI()
engine = GameEngine.new_game()
router = CommandRouter()

@app.post("/action")
def action(raw: str):
    command = router.route(raw)
    return engine.process_action(command)   # already JSON-serializable

@app.get("/state")
def state():
    return engine.get_game_state()
```

A React frontend then calls `POST /action` and renders the returned JSON —
formatting text on the client instead of in Python. The rules never moved.

### Example: swap the CLI for a GUI

A desktop GUI (e.g. Tkinter/PyQt) subscribes the same way: a button click builds
a command, calls `engine.process_action`, and updates widgets from the result
dict. `get_game_state()` feeds health bars and stat panels directly.

### Example: expose the engine as an API

Since every result is a plain dict, the engine is already an API core. Wrap
`process_action` / `get_game_state` in any transport (REST, WebSocket, gRPC) and
serialize the dictionaries. Session state can be held per-connection by keeping
one `GameEngine` instance per player.

> **The rule of thumb:** if a change requires editing anything under
> `core/`, `systems/`, `models/`, or `data/` to add a new frontend, the
> separation has been violated. A new UI should only ever add a file alongside
> `ui/` and adjust the one wiring line in `main.py`.

---

## 5. Extending the game

The design is data-first, so most content grows without touching code:

| To add…            | Edit…                                   | Code changes |
| ------------------ | --------------------------------------- | ------------ |
| An enemy           | `data/enemies/*.json`                   | None         |
| An NPC             | `data/characters/*.json`                | None         |
| An item            | `data/items.json`                       | None*        |
| A skill            | `data/skills.json`                      | None*        |
| A special event    | `data/events.json`                      | None*        |
| A location encounter | `data/encounter_pools.json`           | None         |
| A cultivation realm| `data/cultivation/*.json`               | None         |

\* New *effect kinds* (a brand-new item, event, or skill behaviour) require
adding a branch in `EffectSystem.apply_to_player` for player-facing effects, plus
a formatter in the UI for any new `EventType`. Existing effect kinds (`heal`,
`restore_qi`, `cultivation_boost`, `restore`, `exp`, `damage`, `buff_defense`)
are pure data. Multi-file collections (`characters/`, `enemies/`,
`character_enemies/`) are merged on load by `load_collection()`; adding a new file
to one of these folders needs no code.

---

## 6. Passive skills and calculated effective stats

Base stats stored on the player stay pristine. Always-on passive skills (e.g.
`buff_defense`) are applied **on demand** by `StatsSystem.effective_defense`,
which the engine uses for combat damage and for the stat shown in status views.
Because nothing is baked into the stored sheet, a passive can never double-apply
across save/load, and there is no `passives_applied` flag to maintain.

This leaves room for equipment, pills, and temporary buffs/debuffs to layer into
the same calculation (`effective_stats(player)`), keeping modifiers composable
rather than mutating base values. `CombatSystem` takes an optional `StatsSystem`
so the effective defense is used automatically when the engine drives combat.
