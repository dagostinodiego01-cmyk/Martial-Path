# Martial Path — A Cultivation Text RPG

A text-based cultivation RPG engine inspired by novels like *Martial World*. It is
built as a **scalable game architecture foundation**, not a one-off script: the
game logic is completely decoupled from the user interface so the CLI can be
swapped for a web app, GUI, or API later **without touching the core**.

Core gameplay loop: **Train → Explore → Fight → Loot → Breakthrough**.

## Quick start

### Command-line interface (no dependencies)

Requires Python 3.9+.

```bash
# from the workspace root (canonical)
python -m game.main

# ...or use the root-level launcher
python main.py
```

You will be asked for your cultivator's name, then dropped into the command loop.

### Graphical interface (PySide6)

A full graphical frontend built on Qt. It drives the **same engine** as the CLI —
only the UI layer differs — and features a **Pokémon-style battle menu**
(FIGHT / BAG / STATS / RUN, where FIGHT opens a grid of techniques showing Qi
cost and cooldown).

```bash
pip install PySide6

# canonical
python -m game.gui_main

# ...or use the root-level launcher
python gui_main.py
```

The GUI's colours come from [ui/ui_theme.py](ui/ui_theme.py), a reusable dark
charcoal / gold palette (red HP, blue Qi, green Body, purple Essence) matching
the Martial Path dashboard UI brief.

### HTTP API (for a Godot or web frontend)

The engine can also be driven over HTTP by a separate frontend (e.g. a Godot
client). This runs the **same engine** as the CLI and GUI — it only adds a thin
FastAPI adapter in [api/server.py](api/server.py) that forwards structured
commands and returns the engine's result dictionaries unchanged.

```bash
pip install -r requirements.txt   # fastapi + uvicorn
uvicorn game.api.server:app --reload
```

Endpoints (default `http://127.0.0.1:8001`):

| Method & path    | Body                                              | Returns                          |
| ---------------- | ------------------------------------------------- | -------------------------------- |
| `GET  /health`   | —                                                 | `{"status": "ok"}`               |
| `GET  /state`    | —                                                 | full `get_game_state()` snapshot |
| `POST /action`   | `{"action": "TRAIN"}` (plus `item_id`/`skill_id`) | the engine result dict           |
| `POST /new-game` | `{"player_name": "Daoist", "seed": 1}` (optional) | the initial state snapshot       |

One in-process session is kept, so run a single worker and bind to localhost
only. The API intentionally does **not** expose `QUIT` (that would stop the
shared engine). Native Godot needs no CORS; add `CORSMiddleware` only for a Godot
Web export.

## Layered architecture

The project enforces a strict, one-directional dependency flow. Each layer only
knows about the layer directly beneath it.

```
┌──────────────────────┐
│      UI LAYER        │  ui/cli_interface.py   (CLI / GUI / Web — replaceable)
└─────────┬────────────┘
          │  raw text
┌─────────▼────────────┐
│   APPLICATION LAYER  │  application/command_router.py   (input -> actions)
└─────────┬────────────┘
          │  {"action": ...}
┌─────────▼────────────┐
│   GAME ENGINE CORE   │  core/game_engine.py   (orchestration + state, NO UI)
└─────────┬────────────┘
          │  model objects
┌─────────▼────────────┐
│       SYSTEMS        │  systems/*.py   (pure rules, return structured results)
└─────────┬────────────┘
          │
┌─────────▼────────────┐
│     DATA LAYER       │  data/*.json   (items, enemies, skills, events)
└──────────────────────┘
```

### Why the UI is decoupled

* **The engine never calls `print()` or `input()`.** It returns structured data
  (dictionaries tagged with an `EventType`).
* **The UI is the only place** allowed to print, format text, and read input.
* Systems accept structured inputs and return structured outputs with **zero UI
  logic** inside them.

This makes the same engine reusable behind any frontend — a React web client, a
Unity game, or a REST API — because none of them require changes to the rules.

## Project layout

```
game/
├── main.py                     # Composition root: wires UI + engine, starts loop
├── ui/
│   └── cli_interface.py        # Input/output ONLY (every print lives here)
├── application/
│   └── command_router.py       # Maps raw strings -> structured commands
├── api/
│   └── server.py               # FastAPI HTTP adapter (Godot/web frontend)
├── core/
│   ├── game_engine.py          # Central orchestrator (no UI)
│   └── constants.py            # Action/EventType names, start config
├── systems/
│   ├── cultivation_system.py   # Training, progress, breakthroughs
│   ├── combat_system.py        # Turn-based combat calculations
│   ├── inventory_system.py     # Add / remove / use items
│   ├── effect_system.py        # Central player-effect interpreter
│   ├── loot_system.py          # Rolls enemy loot tables
│   └── event_system.py         # Random encounter generator
├── models/
│   ├── player.py               # Player state + trivial transitions
│   ├── enemy.py                # Enemy instances
│   ├── item.py                 # Item definitions
│   └── skill.py                # Skill definitions
├── data/
│   ├── items.json              # Data-driven content...
│   ├── enemies.json
│   ├── events.json
│   ├── realms.json
│   └── skills.json
├── utils/
│   ├── rng.py                  # Seedable random number generator
│   ├── logger.py               # Diagnostic logging (not player output)
│   └── data_loader.py          # JSON loading
└── docs/
    └── ARCHITECTURE.md         # Deep dive on the architecture
```

## Commands

| Command             | Aliases        | Description                                            |
| ------------------- | -------------- | ------------------------------------------------------ |
| `train`             | `t`            | Cultivate to raise progress toward a breakthrough.     |
| `breakthrough`      | `b`            | Attempt to advance a stage (needs 100% progress).      |
| `explore`           | `e`            | Venture out; may trigger combat, loot, or an event.    |
| `status`            | `s`, `stats`   | Show cultivation, stats, and skills.                   |
| `inventory`         | `inv`, `i`     | List carried items.                                    |
| `use <item_id>`     |                | Use an item, e.g. `use healing_pill`.                  |
| `attack`            | `a`            | *(Combat)* Basic attack.                               |
| `skill <skill_id>`  | `cast`         | *(Combat)* Use an active skill, e.g. `skill iron_fist`.|
| `flee`              | `run`          | *(Combat)* Attempt to escape.                          |
| `help`              | `h`            | Show the command list.                                 |
| `quit`              | `exit`, `q`    | Exit the game.                                         |

## Example gameplay

```
[Body Tempering Stage 1 | HP 100/100 | Qi 50/50 | Progress 0.0%]
> train
You cultivate diligently. Progress +14% (now 14.0%), EXP +5.

[Body Tempering Stage 1 | HP 100/100 | Qi 50/50 | Progress 14.0%]
> explore
------------------------------------------------------------
A Iron-Fang Wolf lunges from the shadows!
  Iron-Fang Wolf (Mortal) — HP 45/45, ATK 10, DEF 3
  Commands: attack | skill <id> | use <id> | flee
------------------------------------------------------------

[COMBAT] You 100/100 HP | Iron-Fang Wolf 45/45 HP
> skill iron_fist
  You unleash Iron Fist for 22 damage!
  The Iron-Fang Wolf hits you for 8 damage.
  [You HP 92/100 | Iron-Fang Wolf HP 23/45]

[COMBAT] You 92/100 HP | Iron-Fang Wolf 23/45 HP
> attack
  You strike for 14 damage.
  The Iron-Fang Wolf hits you for 7 damage.
  [You HP 85/100 | Iron-Fang Wolf HP 9/45]

[COMBAT] You 85/100 HP | Iron-Fang Wolf 9/45 HP
> attack
  You strike for 13 damage.
------------------------------------------------------------
VICTORY! You have slain the Iron-Fang Wolf.
  EXP +15.
  Loot: Demonic Beast Core x1.
------------------------------------------------------------
```

## Swapping the UI (future-proofing)

Because the engine is UI-agnostic, adding a new frontend means writing a new UI
that speaks the same contract and changing **one line** in `main.py`:

```python
# core stays identical
engine = GameEngine.new_game()
router = CommandRouter()

# swap ONLY this line for a different frontend
ui = CLIInterface(engine, router)   # -> WebInterface(engine, router), etc.
ui.run()
```

Any new UI just needs to:

1. Collect input and call `router.route(raw_text)` to get a structured command.
2. Call `engine.process_action(command)` and read the returned result dict.
3. Render that result however it likes (HTML, JSON, GUI widgets…).

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full contract and a
worked example of replacing the CLI with a web, GUI, or API layer.

## Extending content

All content is data-driven. To add a new enemy, item, skill, or special event,
edit the matching file in `data/` — **no code changes required**:

* New enemy → add an entry to `data/enemies.json`.
* New item → add an entry to `data/items.json` (with an `effect` the inventory
  system understands: `heal`, `restore_qi`, `cultivation_boost`).
* New skill → add an entry to `data/skills.json`.
* New realm → add an entry to `data/realms.json`.
