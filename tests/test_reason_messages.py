"""Every refusal must tell the player *why* (``game/utils/reasons.py``).

An action that could not be done used to answer with a machine reason nothing
explained: the narrative layer replaced the result with a random ``error`` template
("The attempt falters against the Spring air; not everything can be done."), the CLI
knew 46 of the reason codes and the Godot client 43, and every other refusal fell
through to "That action cannot be completed right now." The player was told that
something failed, never what.

Three things hold the line now, and each is checked here:

* :data:`game.utils.reasons.REASONS` covers every code the engine can emit,
* the engine attaches a sentence saying why to every result that carries a reason,
* that sentence is what the Godot client shows, ahead of its own stale table.
"""
from __future__ import annotations

import re
from pathlib import Path

from game.core.constants import Action, EventType
from game.core.game_engine import GameEngine
from game.utils.reasons import REASONS, explain

REPO_ROOT = Path(__file__).resolve().parents[1]
GAME_ROOT = REPO_ROOT / "game"
GODOT_CONTROLLER = REPO_ROOT / "frontend-godot" / "scripts" / "MainController.gd"

#: A reason code written into a result, a local, or a gate payload.
_CODE_PATTERNS = (
    re.compile(r'"reason"\s*:\s*"([A-Z][A-Z0-9_]*)"'),
    re.compile(r'"reason"\s*:\s*f"([A-Z][A-Z0-9_]*)"'),
    re.compile(r"reason\s*=\s*\"([A-Z][A-Z0-9_]*)\""),
    re.compile(r"reason\s*=\s*'([A-Z][A-Z0-9_]*)'"),
)


def _engine_reason_codes() -> set[str]:
    """Every reason code written anywhere in the engine's own source."""
    codes: set[str] = set()
    for source in GAME_ROOT.rglob("*.py"):
        text = source.read_text(encoding="utf-8", errors="ignore")
        for pattern in _CODE_PATTERNS:
            codes |= set(pattern.findall(text))
    return codes


def test_every_reason_the_engine_can_emit_has_an_explanation():
    """A code the table does not know is a refusal the player cannot act on."""
    codes = _engine_reason_codes()
    assert codes, "no reason codes found -- did the engine stop reporting reasons?"
    unknown = sorted(code for code in codes if code not in REASONS)
    assert unknown == [], (
        "reason codes with no player-facing explanation (add them to "
        "game/utils/reasons.py): " + ", ".join(unknown)
    )


def test_every_explanation_is_a_sentence_even_with_no_context():
    """The table must not need the result's numbers to say something useful."""
    for code, template in REASONS.items():
        sentence = explain({"reason": code})
        assert "{" not in sentence, f"{code} left an unfilled slot: {sentence!r}"
        assert len(sentence) >= 15, f"{code} explains almost nothing: {sentence!r}"
        assert sentence != explain({"reason": "NO_SUCH_REASON_AT_ALL"}), code
        assert template.strip(), code


def test_an_unknown_reason_is_honest_rather_than_silent():
    """The last resort still names what it does not know."""
    sentence = explain({"reason": "SOMETHING_NEW"})
    assert "SOMETHING_NEW" in sentence, sentence
    assert explain({}), "an empty result must not explain nothing"
    assert explain(None)  # never raises


def test_a_refusal_carries_its_explanation_and_narrates_it():
    """The reported bug: a dropped cause, told as random season flavour."""
    engine = GameEngine.new_game(seed=1)

    result = engine.process_action({"action": Action.ATTACK})

    assert result["event"] == EventType.ERROR
    reason = result["reason"]
    assert result["message"] == explain(result)
    assert result["narrative"] == result["message"], (
        "a refusal's narrative must be its cause, not a random error template"
    )
    # The old templated flavour never named a cause; this must.
    assert "falters against" not in result["narrative"]
    assert reason.replace("_", " ").split()[0].lower() not in result["narrative"], reason


def test_a_material_refusal_says_what_the_material_is_for():
    """The Talent Refining Elixir case: the player asked why, and is told."""
    engine = GameEngine.new_game(seed=1)
    engine.inventory.add_item(engine.player, "talent_refining_elixir", 1)

    result = engine.process_action({"action": Action.USE_ITEM, "item_id": "talent_refining_elixir"})

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "ITEM_NOT_USABLE"
    assert result["message"] == result["narrative"]
    assert "material" in result["message"].lower(), result["message"]


def test_the_client_shows_the_engines_explanation_first():
    """The client's own table covers a third of the codes, so it must not win."""
    source = GODOT_CONTROLLER.read_text(encoding="utf-8")
    start = source.index("func _translate_reason")
    rest = source[start:]
    end = rest.find("\nfunc ", 1)
    body = rest[:end] if end != -1 else rest

    assert 'result.get("message"' in body, (
        "_translate_reason must read the engine's message field"
    )
    assert body.index('result.get("message"') < body.index("match reason:"), (
        "the engine's explanation must be returned before the client's own table, "
        "or the two thirds of codes that table lacks stay unexplained"
    )


#: Actions that must fail, one per dispatch region, with a payload that reaches the
#: refusal rather than the malformed-action guard.
_REFUSALS = (
    ({"action": Action.ATTACK}, None),
    ({"action": Action.USE_SKILL, "skill_id": "iron_fist"}, None),
    ({"action": Action.USE_ITEM, "item_id": "nine_nether_boots"}, None),
    ({"action": Action.BREAKTHROUGH}, None),
    ({"action": Action.JOIN_SECT}, None),
    ({"action": Action.UNLOCK, "unlock_id": "no_such_unlock"}, None),
    ({"action": Action.UPGRADE_TALENT, "track": "nonsense", "target_id": "x"}, None),
    # The debate start used to spell its refusal key "error", so the result carried no
    # ``reason`` at all and the player read the random error template instead.
    ({"action": Action.DEBATE_CHARACTER, "character_id": "nobody_at_all"}, None),
)


def test_no_refusal_reaches_the_player_without_a_reason():
    """Every refused action explains itself -- checked by running them, not scanning.

    The code-scan above cannot catch a refusal spelled with the wrong key (the
    debate start's ``"error"``), because the code inside it is still defined
    somewhere else. This drives the real dispatch and reads what the player gets.
    """
    unresolved = []
    for action, mutate in _REFUSALS:
        engine = GameEngine.new_game(seed=1)
        if mutate:
            mutate(engine)
        result = engine.process_action(action)

        # A refusal is anything that reports a reason. Some outcomes carry their own
        # and a bespoke narrative too (a failed breakthrough is one), which is fine --
        # what is not fine is a reason the player never gets told.
        reason = result.get("reason")
        assert reason, f"{action['action']} was expected to be refused, got {result['event']}"
        if not result.get("message"):
            unresolved.append(f"{action['action']}: reasoned {reason} but explained nothing")
        # A bare ERROR must never narrate the random season template.
        if result["event"] == EventType.ERROR and "falters against" in str(result.get("narrative", "")):
            unresolved.append(f"{action['action']}: random flavour instead of {reason}")

    assert unresolved == [], "refusals with no explanation: " + "; ".join(unresolved)
