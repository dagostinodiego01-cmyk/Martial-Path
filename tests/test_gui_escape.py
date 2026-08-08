"""Test for the GUI's HTML escape helper.

The GUI renders player/NPC text into a Qt rich-text log, so ``_esc`` must escape
HTML-sensitive characters (not strip them) to keep names intact and safe.
Skipped when PySide6 is not installed, since the helper lives in the Qt module.
"""
import pytest

pytest.importorskip("PySide6")

from game.ui.gui_interface import _esc  # noqa: E402  (import after skip guard)


def test_escape_preserves_and_encodes_special_characters():
    assert _esc("A&B") == "A&amp;B"
    assert _esc("<test>") == "&lt;test&gt;"


def test_escape_encodes_quotes():
    assert _esc('say "hi"') == "say &quot;hi&quot;"


def test_escape_does_not_drop_characters():
    # The old implementation stripped characters; escaping must retain them all.
    assert _esc("Lin & Sons <Sect>") == "Lin &amp; Sons &lt;Sect&gt;"
