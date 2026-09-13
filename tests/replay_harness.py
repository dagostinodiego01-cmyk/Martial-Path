"""Loaders shared by the L6 harness tests (T.4, T.6).

``tools/`` holds scripts, not a package, so a test that wants the playthrough
engine imports it by path. The module must be registered in ``sys.modules``
before it executes, otherwise ``@dataclass`` cannot resolve its own namespace on
Python 3.14 (``sys.modules.get(cls.__module__)`` is ``None``).
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GODOT_PROJECT = PROJECT_ROOT / "frontend-godot"

#: Where a Godot 4 download usually lands, newest first.
_GODOT_GLOBS = (
    "Downloads/Godot_v4*/Godot_v4*_console.exe",
    "Downloads/Godot_v4*/Godot_v4*.exe",
    "Downloads/Godot_v4*.exe",
    "Desktop/Godot_v4*/Godot_v4*.exe",
)


def find_godot() -> str | None:
    """The Godot binary to test with, or ``None`` when the machine has none."""
    for name in ("GODOT_BIN", "GODOT4_BIN", "GODOT"):
        configured = os.environ.get(name, "").strip()
        if configured and Path(configured).is_file():
            return configured
    for name in ("godot4", "godot", "Godot"):
        found = shutil.which(name)
        if found:
            return found
    for pattern in _GODOT_GLOBS:
        for candidate in sorted(Path.home().glob(pattern), reverse=True):
            if candidate.is_file():
                return str(candidate)
    return None

#: Recorded replay fixtures (T.6), written by
#: ``python tools/playthrough_report.py --record tests/fixtures/replay_logs``.
REPLAY_LOG_DIR = PROJECT_ROOT / "tests" / "fixtures" / "replay_logs"


def load_tool(module_name: str, relative_path: str):
    """Import a ``tools/`` script by path and return the module."""
    spec = importlib.util.spec_from_file_location(module_name, PROJECT_ROOT / relative_path)
    if spec is None or spec.loader is None:  # pragma: no cover - import failure path
        raise ImportError(f"cannot load {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def playthrough_report():
    """The T.4 playthrough tool, as a module."""
    return load_tool("playthrough_report", "tools/playthrough_report.py")
