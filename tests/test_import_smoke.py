"""Smoke test: every module under ``game/`` imports cleanly.

Catches syntax errors, broken imports, and circular-import regressions early --
before they surface as confusing failures during unrelated test collection.

Modules that fail to import *only* because an optional third-party dependency is
missing (e.g. ``PySide6`` for the GUI, which is not a core requirement) are
skipped rather than failed, so the pure-Python engine can still be validated in
a minimal environment.
"""
from __future__ import annotations

import importlib
from pathlib import Path
from typing import List

import pytest

# Third-party packages that are optional for the core engine. A module that
# raises ModuleNotFoundError for one of these is skipped, not failed.
_OPTIONAL_DEPS = {"PySide6", "shiboken6", "fastapi", "uvicorn", "starlette", "pydantic"}

_REPO_ROOT = Path(__file__).resolve().parent.parent
_GAME_ROOT = _REPO_ROOT / "game"


def _module_names() -> List[str]:
    """Return the dotted module name for every ``.py`` file under ``game/``."""
    names: List[str] = []
    for path in sorted(_GAME_ROOT.rglob("*.py")):
        parts = path.relative_to(_REPO_ROOT).with_suffix("").parts
        if parts[-1] == "__init__":
            parts = parts[:-1]
        names.append(".".join(parts))
    return names


@pytest.mark.parametrize("module_name", _module_names())
def test_game_module_imports(module_name: str) -> None:
    try:
        importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        missing = (exc.name or "").split(".")[0]
        if missing in _OPTIONAL_DEPS:
            pytest.skip(f"optional dependency '{missing}' not installed")
        raise
