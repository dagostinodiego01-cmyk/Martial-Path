"""Contract between the state payload and the Godot client.

The engine always sends the ``enemy`` and ``encounter`` keys, and sets them to
``null`` when there is no fight/encounter. In GDScript ``Dictionary.get(key, {})``
returns that stored ``null`` rather than the fallback, so a chain like
``state.get("enemy", {}).get("id", "")`` raises
``Invalid call. Nonexistent function 'get' in base 'Nil'``.

That is not hypothetical: the B.9 formation block read ``enemy`` that way inside
``_rebuild_combat_actions``, which every state refresh calls, so clicking NEW GAME
in the Godot client broke the running game on line 2770 of ``MainController.gd``.
These tests pin the engine side of the contract and keep the landmine out of the
frontend.
"""
from __future__ import annotations

import re
from pathlib import Path

from game.core.game_engine import GameEngine

GODOT_SCRIPTS = Path(__file__).resolve().parent.parent / "frontend-godot" / "scripts"

#: State keys the engine may send as ``null`` (see ``views.get_game_state``).
NULLABLE_STATE_KEYS = ("enemy", "encounter")

#: ``something.get("<nullable key>", {})`` followed by another attribute read.
_LANDMINE = re.compile(
    r'\.get\(\s*"(' + "|".join(NULLABLE_STATE_KEYS) + r')"\s*,\s*\{\}\s*\)\s*\.'
)


def test_engine_sends_nullable_keys_as_null():
    """The engine's null-ability is the reason the client must type-check."""
    state = GameEngine.new_game(seed=1).get_game_state()
    for key in NULLABLE_STATE_KEYS:
        assert key in state, f"state must always carry {key!r}"
    assert state["enemy"] is None, "no fight at start => enemy is null"
    assert state["encounter"] is None, "no pending encounter at start => null"


def test_godot_scripts_never_chain_get_on_a_nullable_key():
    offenders = []
    for script in sorted(GODOT_SCRIPTS.glob("*.gd")):
        for number, line in enumerate(script.read_text(encoding="utf-8").splitlines(), 1):
            if _LANDMINE.search(line):
                offenders.append(f"{script.name}:{number}: {line.strip()}")
    assert offenders == [], (
        "chained .get() on a null-able state key (use a typeof() type check "
        "first): " + "; ".join(offenders)
    )
