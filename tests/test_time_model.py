"""The time model is one clock, and this file is the table that says so (TM.1).

``age_years`` is the only stored time value; season, elapsed year and remaining
lifespan derive from it, and every time-consuming action advances the character
and the living world by the same cost. These tests read the contract out of
``game/docs/TIME_MODEL.md`` and check the engine against it, so a new action cost
cannot be added to the config without appearing in the doc, and a documented cost
cannot quietly disappear from the config.
"""
from __future__ import annotations

import re
from pathlib import Path

from game.core.constants import Action, EventType
from game.core.game_engine import GameEngine
from game.models.player import Player
from game.utils.data_loader import load_json

TIME_MODEL_DOC = Path(__file__).resolve().parents[1] / "game" / "docs" / "TIME_MODEL.md"

#: A cost row: ``| Train Body | `train_body` | 0.125 |``.
_COST_ROW = re.compile(r"^\|\s*[^|]+\|\s*`([a-z_]+)`\s*\|\s*([0-9.]+)\s*\|\s*$", re.MULTILINE)
#: Rows whose cost is derived rather than a ``time_costs`` entry.
_DERIVED_ROW = re.compile(r"^\|\s*[^|]+\|\s*`\(derived\)`", re.MULTILINE)


def _documented_costs() -> dict[str, float]:
    return {key: float(years) for key, years in _COST_ROW.findall(TIME_MODEL_DOC.read_text(encoding="utf-8"))}


def test_the_doc_lists_every_time_cost_and_no_others():
    configured = {key: float(value) for key, value in load_json("cultivation/cultivation_config.json")["lifespan"]["time_costs"].items()}
    documented = _documented_costs()

    assert documented, "no cost rows parsed out of TIME_MODEL.md"
    assert documented.keys() == configured.keys(), (
        "TIME_MODEL.md and lifespan.time_costs disagree: "
        f"undocumented={sorted(configured.keys() - documented.keys())}, "
        f"stale={sorted(documented.keys() - configured.keys())}"
    )
    for key, years in configured.items():
        assert documented[key] == years, f"{key} documented as {documented[key]}, configured as {years}"


def test_the_doc_still_describes_the_derived_costs():
    # Travel and closed-door have no time_costs entry; if either stops being
    # derived (or the note vanishes) the table would be silently wrong.
    assert _DERIVED_ROW.search(TIME_MODEL_DOC.read_text(encoding="utf-8"))


def test_age_is_the_only_stored_clock():
    saved = GameEngine.new_game(seed=1).player.to_save_dict()
    assert "age_years" in saved
    assert "current_day" not in saved, "a day counter is a second clock (TM.1)"

    state = GameEngine.new_game(seed=1).get_game_state()
    assert "current_day" not in state["player"]
    assert state["player"]["lifespan"]["age_years"] == state["player"]["age_years"]


def test_a_time_consuming_action_moves_character_and_world_together():
    engine = GameEngine.new_game(seed=1)
    before_age = engine.player.age_years
    before_year = engine._world_state.get("year", 0.0)
    cost = load_json("cultivation/cultivation_config.json")["lifespan"]["time_costs"]["train_body"]

    result = engine.process_action({"action": Action.TRAIN_BODY})

    assert result["event"] == EventType.TRAIN_RESULT
    assert engine.player.age_years == round(before_age + cost, 4)
    assert engine._world_state.get("year", 0.0) == round(before_year + cost, 4)


def test_a_read_only_action_moves_nothing():
    engine = GameEngine.new_game(seed=1)
    before = (engine.player.age_years, engine._world_state.get("year", 0.0))

    engine.process_action({"action": Action.STATUS})

    assert (engine.player.age_years, engine._world_state.get("year", 0.0)) == before


def test_season_is_a_function_of_age_not_a_second_counter():
    player = Player(name="Tester")
    player.age_years = 12.0
    seasons = []
    for _ in range(5):
        seasons.append(GameEngine.new_game(seed=1).lifespan.season(player))
        player.age_years += 1.0
    assert seasons == ["Spring", "Summer", "Autumn", "Winter", "Spring"]
