---
name: game-testing-validation
description: 'The verification loop for the Martial Path RPG. Use after any code or data change, when adding tests, when a refactor must preserve behaviour, or when validating game data. Covers running the pytest suite, adding focused and negative tests, the central data validation layer, import/JSON smoke tests, behaviour-preserving checks, and testing systems without a UI.'
argument-hint: 'what was changed and needs verifying'
---

# Martial Path Testing & Validation

Systems must be verifiable without a UI (instruction 09). Validate every change
with tests rather than assuming success.

## When to Use
- After any code or data change.
- Adding tests for new behaviour.
- Confirming a refactor preserved behaviour.

## Commands
- Full suite (run from repo root; `game.*` imports are package-qualified):
  `.venv\Scripts\python.exe -m pytest -q`
- Data validation only: `.venv\Scripts\python.exe -m pytest -q tests/test_all_game_data_valid.py`
- Ad-hoc data check: `validate_all_game_data()` from `game.validation`.

## Procedure

1. **Run the full suite after each meaningful change**, not just at the end. Fix regressions before moving on; diagnose failures rather than retrying blindly.
2. **Add focused tests for new behaviour.** Construct systems directly with injected data and a seeded `RNG` (`RNG(seed=…)`) for determinism; use a `SimpleNamespace` fake player when a full engine isn't needed.
3. **Add negative tests.** For validation, feed a deliberately broken `GameDataRegistry` (via `dataclasses.replace`) and assert the specific error category is reported. For actions, assert rejected commands return the right `reason`.
4. **Keep the safety nets green:** the import smoke test (`tests/test_import_smoke.py`) imports every `game/` module; the JSON smoke test parses every data file. New modules/data are covered automatically — a red smoke test means a syntax/JSON error.
5. **Behaviour-preserving refactors:** assert the result dict `event` and error `reason` are byte-identical before/after; lean on existing engine tests.
6. **After green, check errors** on changed files (compile/lint) and confirm the app still imports (engine, API, GUI module).

## Conventions
- ASCII only inside printed player-facing strings; docstrings/comments may use UTF-8.
- Skip optional dependencies in tests: `pytest.importorskip("PySide6")` for GUI-touching tests; the import smoke test skips modules whose only failure is a missing optional dep (PySide6/fastapi).
- Do not weaken assertions or use `--no-verify`-style shortcuts to make tests pass.
