---
name: game-engine-architecture
description: 'Procedure for adding or changing gameplay LOGIC in the Martial Path RPG while keeping the layered architecture intact. Use when creating a system or service, adding a player action or result type, wiring something into GameEngine, or deciding where logic belongs (systems vs services vs engine vs UI). Covers structured EventType results, typed result models, Action/EventType StrEnums, the command router, dependency injection, and the UI-display-only rule.'
argument-hint: 'the logic or system to add'
---

# Martial Path Engine & Architecture

Keep gameplay logic out of UIs and respect the dependency direction
(instructions 01, 02). The engine owns session state and coordinates; systems
implement pure rules; services provide stable coordination APIs; UIs only render
state and send commands.

## When to Use
- Adding a system, service, action, or result type.
- Wiring new behaviour into `GameEngine`.
- Deciding which layer a piece of logic belongs in.

## Where does the logic go?
- **System** (`game/systems/`): pure gameplay rules. Takes model objects/IDs and a seeded `RNG`; returns structured data. No I/O, no UI, no ownership of session state. Must be testable in isolation.
- **Service** (`game/services/`): coordinates systems + player state behind a stable API (e.g. `TravelService`, `CharacterService`, `CultivationService`). Reads/moves the player it is given; does not own the session.
- **Engine** (`game/core/game_engine.py`): owns the session (player, mode, enemy, cooldowns), builds and injects systems/services, and dispatches actions. Coordinates cross-system side effects (quests, encounters).
- **UI / frontend**: never computes gameplay. It renders `get_game_state()` / result dicts and sends `{"action": ...}` commands.

## Procedure

1. **Return structured results, not text.** Every engine/system result is a dict tagged with an `EventType` (`game/core/constants.py`). Prefer a typed model from `game/core/results.py` (`Result.to_dict()`) at the boundary; add a dataclass there for a new outcome shape.
2. **Add a new action** (if needed): add a member to the `Action` `StrEnum`, map its verb/args in `CommandRouter` (`game/application/command_router.py`, `_ALIASES` / `_ARG_FIELDS`), and add a dispatch-table entry in the engine (`_build_info_dispatch` / `_build_explore_dispatch`, or the explicit combat flow). Preserve existing error reasons.
3. **Add a new system/service:** construct it in `GameEngine.__init__` with injected dependencies (data from the registry, the shared `RNG`, other systems). Thread any new registry data through `GameEngine.new_game`.
4. **Expose to UIs** only via `get_game_state()` (add a UI-safe key) or a result — never by having the UI reach into internals.
5. **Preserve behaviour on refactors:** keep result `event` values and error `reason` codes identical; verify with the existing tests.
6. **Wire, then test and document:** follow game-testing-validation and update `game/docs/ARCHITECTURE.md` + `CHANGELOG.md`.

## Guardrails
- Lower layers never import higher ones; nothing in `core/systems/services` imports UI.
- `StrEnum` members serialise as plain strings (safe for dict keys, JSON, and the API) — rely on that instead of `.value`.
- Keep `GameEngine` lean: prefer dispatch tables and delegation over long `if/elif` chains.
