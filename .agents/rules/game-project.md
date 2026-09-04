# Martial Path — Shared Project Rules (inherited by every agent)

You are working on **Martial Path**, a data-driven cultivation (xianxia) RPG.
The authoritative game logic is a Python engine in `game/`; a Godot 4.7 client
renders its state over HTTP. Follow these rules in every task.

## Architecture (hard, one-directional)

```
ui/ + frontends  ->  application/  ->  core/  ->  services/  ->  systems/  ->  models/ + data/
```

- `game/core/game_engine.py` is the single owner of mutable session state. It
  wires systems and builds the UI-agnostic `get_game_state()` snapshot.
- `game/systems/` are **pure gameplay rules**: no I/O, no UI, no engine imports.
  They return structured dicts tagged with an `EventType`.
- `game/services/` are thin coordination facades over systems.
- `game/data/registry.py` loads every content collection once into an immutable
  `GameDataRegistry`.
- Gameplay logic must **never** leak into a UI. UIs display state and send
  commands only.

## Frontend scope: Godot only

Only `frontend-godot/` receives player-facing UI work. Do **NOT** modify the
frozen CLI (`game/ui/cli_interface.py` + `game/application/command_router.py`)
or the PySide6 interface (`game/ui/gui_interface.py`). Engine/data changes are
fine; port them to Godot in `frontend-godot/scripts/` when player-visible.

## Data-driven first

- Stable `snake_case` IDs in JSON; new content = new JSON, not new code paths.
- Every new data collection gets a `_validate_*` in
  `game/validation/data_validator.py` (ids, references, reachability, ranges).
- `validate_all_game_data()` must return **0 errors** after any data change.
- Seed generators in `tools/` are deterministic + idempotent; regenerate data
  with them instead of hand-editing seeded output.

## Determinism

All RNG goes through the seeded `RNG`; a run's seed must reproduce it exactly.
Never use unseeded randomness in systems, generators, or narrative rendering.

## Godot gotchas (GDScript)

- The Godot project treats warnings as errors: a `:=` inferring `Variant` (e.g.
  from global `clamp()`/`min()`/`max()`) is a hard parse error that greys out
  the UI. Use `clampf`/`minf`/`maxf` or explicit `: float`.
- The backend runs without `--reload`: restart uvicorn after changing Python
  engine code or `game/data/**`.
- ASCII only in player-facing CLI strings (Windows console is cp1252). Godot
  narrative prose may use UTF-8.

## Definition of done (every task)

1. Code/data committed to `game/` (and `frontend-godot/` for UI) per the
   architecture above.
2. At least one test under `tests/` exercises the change (unit or engine-level).
3. `python -m pytest -q` passes; `validate_all_game_data()` returns 0 errors.
4. Godot scripts parse clean (`godot --headless --check-only`) when touched.
5. `handover.md` (and `ROADMAP.md` checkbox if applicable) note the change.

## Project documentation map

- `handover.md` — current state, commands, conventions, known gaps.
- `ROADMAP.md` — the phased forward plan (MVP -> Alpha -> 1.0 -> Endless);
  flip checkboxes to `[x]` when a task ships.
- `graphify-out/graph.json` — the codebase knowledge graph (2,184 nodes):
  communities, god nodes, and 5,284 dependency edges. Query it (or
  `graphify-out/GRAPH_REPORT.md`) to find the real blast radius of a change.
- `game/docs/` — ARCHITECTURE, CULTIVATION_SYSTEM, DATA_SCHEMA, SAVE_SYSTEM,
  EQUIPMENT_SYSTEM, CHANGELOG.
