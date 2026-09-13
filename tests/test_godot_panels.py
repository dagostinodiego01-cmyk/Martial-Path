"""Runs the Godot frontend's panel smoke check as part of the Python gate.

The frontend's panels are GDScript, so the pytest suite cannot import them. This
shells out to ``frontend-godot/tests/check_panels.gd`` -- which builds every
panel from a synthetic state payload and asserts the text a player would read
reached the tree -- and fails whenever a panel renders wrong.

Skips (rather than fails) when no Godot binary is installed, so the suite stays
runnable on a machine that only has the engine half of the project.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GODOT_PROJECT = PROJECT_ROOT / "frontend-godot"
CHECK_SCRIPT = "res://tests/check_panels.gd"
TIMEOUT_SECONDS = 120

# Where a Godot 4 download usually lands, newest first.
_FALLBACK_GLOBS = (
    "Downloads/Godot_v4*/Godot_v4*_console.exe",
    "Downloads/Godot_v4*/Godot_v4*.exe",
    "Downloads/Godot_v4*.exe",
    "Desktop/Godot_v4*/Godot_v4*.exe",
)


def _find_godot() -> str | None:
    for name in ("GODOT_BIN", "GODOT4_BIN", "GODOT"):
        configured = os.environ.get(name, "").strip()
        if configured and Path(configured).is_file():
            return configured
    for name in ("godot4", "godot", "Godot"):
        found = shutil.which(name)
        if found:
            return found
    for pattern in _FALLBACK_GLOBS:
        for candidate in sorted(Path.home().glob(pattern), reverse=True):
            if candidate.is_file():
                return str(candidate)
    return None


def test_panels_render_the_state_they_are_given() -> None:
    godot = _find_godot()
    if godot is None:
        pytest.skip("no Godot binary found; set GODOT_BIN to run the panel check")

    result = subprocess.run(
        [godot, "--headless", "--path", str(GODOT_PROJECT), "-s", CHECK_SCRIPT],
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
    )
    output = result.stdout + result.stderr

    assert result.returncode == 0, f"panel check failed:\n{output}"
    assert "0 panel check(s) failed" in output, output
    # A panel that silently stops rendering reports no failures; the script's own
    # per-panel OK lines are the proof it actually exercised them.
    for panel in ("OK   InventoryPanel", "OK   EquipmentPanel", "OK   JournalPanel", "OK   StatusPanel", "OK   TechniquesPanel"):
        assert panel in output, f"{panel} never reported:\n{output}"
