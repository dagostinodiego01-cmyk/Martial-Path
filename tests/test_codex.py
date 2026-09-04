"""CODEX action: the wanderer's codex (secret realms, sects, faction arcs)."""
from __future__ import annotations

import json

import pytest

from game.core.game_engine import GameEngine
from game.utils.data_loader import load_json


@pytest.fixture()
def engine():
    return GameEngine.new_game("CodexTester")


@pytest.fixture()
def codex(engine):
    return engine.process_action({"action": "CODEX"})


def test_codex_is_a_tier1_action(engine, codex):
    assert codex["event"] == "CODEX"
    assert codex["max_story_tier"] == 1


def test_codex_lists_every_secret_realm(codex):
    data = load_json("secret_realm.json")
    assert {r["id"] for r in codex["realms"]} == {r["id"] for r in data}


def test_codex_realms_carry_location_and_discovery(codex):
    verdant = next(r for r in codex["realms"] if r["id"] == "verdant_abyss")
    assert verdant["location_id"] == "misty_gorge"
    assert verdant["story_tier"] == 1
    assert verdant["discovered"] is True
    assert verdant["display_name"]
    assert verdant["location_name"]


def test_codex_realms_gated_by_story_tier(engine):
    """A tier-6 realm stays undiscovered until the player reaches tier 6."""
    codex = engine.process_action({"action": "CODEX"})
    deep = next(r for r in codex["realms"] if r["id"] == "undercroft_circuit_prime")
    assert deep["story_tier"] == 6
    assert deep["discovered"] is False
    engine.player.max_story_tier = 6
    codex = engine.process_action({"action": "CODEX"})
    deep = next(r for r in codex["realms"] if r["id"] == "undercroft_circuit_prime")
    assert deep["discovered"] is True


def test_codex_lists_every_sect_with_hall_progress(codex):
    assert len(codex["sects"]) == 12
    lin = next(s for s in codex["sects"] if s["id"] == "lin_academy")
    assert lin["tier"] == 1
    assert lin["technique_count"] > 0
    # A fresh player starts knowing two Lin Academy arts.
    assert lin["techniques_known"] == 2
    assert lin["joined"] is False


def test_codex_sect_tiers_are_ordered(codex):
    tiers = [s["tier"] for s in codex["sects"]]
    assert tiers == sorted(tiers)


def test_codex_lists_all_three_faction_arcs(codex):
    chains = {arc["chain"]: arc for arc in codex["arcs"]}
    assert set(chains) == {"asura", "phoenix", "valleys"}
    for arc in chains.values():
        assert len(arc["quests"]) == 3
        assert all(q["status"] == "locked" for q in arc["quests"])


def test_codex_arcs_show_progress(engine):
    """Unlocking the first valleys quest shows as active in the arc."""
    engine.quests._activate("valleys_road_of_ambition")
    codex = engine.process_action({"action": "CODEX"})
    valleys = next(a for a in codex["arcs"] if a["chain"] == "valleys")
    first = next(q for q in valleys["quests"] if q["id"] == "valleys_road_of_ambition")
    assert first["status"] == "active"


def test_codex_never_consumes_a_turn(engine):
    day = engine.player.current_day
    engine.process_action({"action": "CODEX"})
    assert engine.player.current_day == day
