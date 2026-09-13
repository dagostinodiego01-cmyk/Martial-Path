"""Every engine event type must have a render branch in the Godot client (U.2).

The client dispatches results through a ``match event:`` table. An event with no
arm is a silent failure: the engine answers, the client shows the previous screen
and changes nothing, and nothing anywhere reports the gap. So the table is
checked against :class:`EventType` here -- adding an engine event without a render
case fails this test instead of surfacing as a stuck screen mid-run.

Arms are read from every script rather than one file, so the per-panel split
(U.0) can move render arms between scripts without breaking the contract.

The same reading catches the *other* half of the contract: an arm that exists but
never opens its view. ``TALENTS`` shipped like that -- the engine returned the live
upgrade table, the arm printed a caption, and ``_show_talents()`` sat uncalled, so
the only sink for a Talent Refining Elixir was unreachable.
"""
from __future__ import annotations

import re
from pathlib import Path

from game.core.constants import EventType

GODOT_SCRIPTS = Path(__file__).resolve().parent.parent / "frontend-godot" / "scripts"

#: The dispatch statement every render table is introduced by.
_TABLE_HEADER = "match event:"

#: A match arm: an indented bare string label followed by a colon.
_ARM = re.compile(r"^\s*[\"']([A-Z][A-Z0-9_]*)[\"']\s*:\s*$")


def _render_tables() -> set[str]:
    """Every event name the client matches on across its scripts."""
    names: set[str] = set()
    for script in sorted(GODOT_SCRIPTS.rglob("*.gd")):
        lines = script.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            if line.strip() != _TABLE_HEADER:
                continue
            table_indent = len(line) - len(line.lstrip())
            for following in lines[index + 1:]:
                stripped = following.strip()
                if stripped and len(following) - len(following.lstrip()) <= table_indent:
                    break  # the table ended
                arm = _ARM.match(following)
                if arm:
                    names.add(arm.group(1))
    return names


def test_every_event_type_has_a_render_branch():
    rendered = _render_tables()
    assert rendered, f"no {_TABLE_HEADER!r} render table found under {GODOT_SCRIPTS}"
    missing = sorted(str(event) for event in EventType if str(event) not in rendered)
    assert missing == [], (
        "engine events the Godot client never renders (add a match arm): " + ", ".join(missing)
    )


def test_render_arms_name_real_event_types():
    """A mistyped arm is dead code that silently swallows the event it names."""
    known = {str(event) for event in EventType}
    unknown = sorted(name for name in _render_tables() if name not in known)
    assert unknown == [], f"render arms that match no engine event: {unknown}"


#: A view handler definition: ``func _show_<event>(``.
_HANDLER = re.compile(r"^func (_show_[a-z0-9_]+)\(", re.MULTILINE)


def _code_without_comments(script: Path) -> str:
    """The script's lines with trailing ``#`` comments removed.

    Comments must not count as references, or a handler mentioned in prose would
    pass the orphan check while still never being called.
    """
    return "\n".join(
        line.split("#", 1)[0]
        for line in script.read_text(encoding="utf-8").splitlines()
    )


def test_view_handlers_are_not_orphaned():
    """An event's view handler must actually be called, or the button does nothing.

    The arm table above only proves an arm exists. This proves the arm *opens
    something*: a handler named after an engine event, defined but never
    referenced, is a screen the player can never reach.
    """
    event_names = {str(event).lower() for event in EventType}
    paired: dict[str, str] = {}
    whole_tree = ""
    for script in sorted(GODOT_SCRIPTS.rglob("*.gd")):
        code = _code_without_comments(script)
        whole_tree += code + "\n"
        for handler in _HANDLER.findall(code):
            if handler[len("_show_"):] in event_names:
                paired.setdefault(handler, script.name)

    assert paired, (
        "no _show_<event> view handler found under "
        f"{GODOT_SCRIPTS} -- the naming convention this check relies on changed"
    )
    orphans = sorted(
        f"{handler}() ({script})"
        for handler, script in paired.items()
        if len(re.findall(rf"\b{re.escape(handler)}\b", whole_tree)) <= 1
    )
    assert orphans == [], (
        "view handlers defined for an engine event but never called -- the event's "
        "arm no longer opens its view: " + ", ".join(orphans)
    )
