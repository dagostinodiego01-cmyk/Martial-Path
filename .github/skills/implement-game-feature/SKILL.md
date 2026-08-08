---
name: implement-game-feature
description: 'Master workflow for adding or changing features in the Martial Path cultivation RPG (Python engine in game/, CLI/PySide/FastAPI/Godot frontends). Use when implementing a new system, service, content type, action, or refactor, or when asked to "add", "extend", "optimise", or "wire up" game behaviour. Orchestrates context-gathering, dependency-ordered phased implementation, layered/data-driven discipline, continuous testing, and a structured change summary. Delegates to game-data-authoring, game-engine-architecture, and game-testing-validation.'
argument-hint: 'the feature or change to implement'
---

# Implement a Martial Path Feature

End-to-end methodology for changing this codebase safely. The project keeps the
authoritative game logic in a Python engine (`game/`) with multiple frontends;
gameplay logic must never live in a UI. Detailed rules live in
`.github/instructions/00`–`12`; this skill is the *procedure* for applying them.

## When to Use
- Adding a system, service, content type, action, result, or data file.
- Refactoring engine/systems while preserving behaviour.
- Any task phrased as "add / extend / optimise / wire up / clean up" the game.

## Procedure

### 1. Orient (before touching code)
- Read repo memory (`/memories/repo/`) and the relevant `.github/instructions/NN-*.md` for the files you'll touch (they auto-apply by `applyTo`).
- Recall the layer order and dependency direction: `ui/ -> application/ -> core/ -> services/ -> systems/ -> models/ + data/`. Lower layers never import higher ones.

### 2. Gather context (read before editing)
- Map data flow: `grep_search` for every reference to the symbols/files you'll change (callers, tests, data). Confirm what is loaded where.
- Read the target files and their tests fully. Note existing result shapes and error reasons you must preserve.
- Prefer the `Explore` subagent for broad "where/how is X used" questions.

### 3. Plan in dependency order
- Break the work into phases: foundation (constants/loader/registry) → data → systems/services → engine wiring → UI/frontend → docs.
- Keep each change focused; do not bundle unrelated changes. Do not add backward compatibility unless asked.
- For multi-step work, keep a running plan in session memory (`/memories/session/`).

### 4. Implement, respecting the architecture
- Content/data changes → follow **game-data-authoring**.
- Gameplay logic / new systems, services, actions, results → follow **game-engine-architecture**.
- Never put gameplay math or content in UI/frontend code; UIs display state and send commands only.

### 5. Verify continuously
- Follow **game-testing-validation**: run the full suite after each meaningful change, add focused + negative tests, and run data validation.

### 6. Update documentation
- Update the affected docs in `game/docs/` (`ARCHITECTURE.md`, `DATA_SCHEMA.md`, `CULTIVATION_SYSTEM.md`, `SAVE_SYSTEM.md`) and add a `CHANGELOG.md` bullet under "Unreleased". This is required, not optional (instruction 11).

### 7. Summarise the change (instruction 12)
Report: what changed, files created, files modified, architecture impact,
assumptions/deviations, follow-up tasks, and how you validated (tests/commands).

## Guardrails
- Data-driven first: prefer JSON + stable IDs over hard-coded values.
- Keep systems testable without a UI (inject data/seeded RNG).
- ASCII only inside printed player-facing strings (Windows console is cp1252).
- Make focused, reversible edits; run tests rather than assuming.
