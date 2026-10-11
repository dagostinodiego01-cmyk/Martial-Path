# Martial Path

A data-driven cultivation (xianxia) text RPG. The authoritative game logic is a
Python engine in `game/` — **all gameplay rules live in the engine, never in a
UI**. Frontends render state and send commands; the primary frontend is a Godot
4.7 client that talks to a FastAPI backend over HTTP.

## Quick start

Create the project virtual environment, then install dependencies:

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
```

| What | Command |
|---|---|
| FastAPI backend (required for Godot) | `.venv/Scripts/python.exe -m uvicorn game.api.server:app --host 127.0.0.1 --port 8001` |
| Godot client (primary) | Open `frontend-godot/project.godot` in Godot 4.7 and press **F5** |
| CLI (frozen) | `.venv/Scripts/python.exe main.py` |
| Desktop GUI (frozen, PySide6) | `.venv/Scripts/python.exe gui_main.py` |
| Tests | `.venv/Scripts/python.exe -m pytest -q` |

## Active work

The live implementation plan is maintained in [`TASKS.md`](TASKS.md). The current
sequence is:

1. **M0** — integrate and re-baseline the shared working tree.
2. **M1** — make save/load deterministic and harden the local API/persistence boundary.
3. **M2** — finish narrative, world/social, campaign/realm, and residual meta work.
4. **M3** — roll out Godot panel parity against stable engine payloads.
5. **M4/M5** — run the serial balance sweep, then package and certify a release.

The repository currently contains a large uncommitted implementation wave. Do not
infer integration state from an old roadmap checkbox; start every feature chat by
reading `TASKS.md` and checking `git status`.

## Documentation

- `handover.md` — current orientation: running the game, architecture, conventions, recent work, and handoff notes
- `TASKS.md` — **live execution tracker**: M0–M5 milestones, dependencies, write sets, and cross-chat handoffs
- `ROADMAP.md` — vision and long-range phased design; it is not the live task checklist
- `game/docs/` — system docs: `ARCHITECTURE.md`, `DATA_SCHEMA.md`, `CULTIVATION_SYSTEM.md`,
  `SAVE_SYSTEM.md`, `EQUIPMENT_SYSTEM.md`, `SHOP_SYSTEM.md`, `MAP_SYSTEM.md`,
  `VOICE_GUIDE.md`, `CHANGELOG.md`

## Architecture

Layered, one-directional dependencies:

```
ui/ (+ frontends)  ->  application/  ->  core/  ->  services/  ->  systems/  ->  models/ + data/
```

- `game/core/game_engine.py` — the single owner of mutable session state; wires
  systems, dispatches actions, builds UI-agnostic state snapshots
- `game/systems/` — pure gameplay rules (no I/O, no UI)
- `game/data/` — data-driven content (JSON with stable `snake_case` IDs), validated
  centrally by `game/validation/data_validator.py`

## Conventions

- Data-driven first: new content = new JSON, not new code paths.
- Keep gameplay logic out of UIs; UIs display state and send commands only.
- Frontend scope: only the Godot interface (`frontend-godot/`) receives updates;
  the CLI and PySide6 interfaces are frozen.
- Every change ships with a test under `tests/` and a clean
  `validate_all_game_data()` run.
