"""Tests for the relationship system's per-NPC state, clamping, and tiers."""
from game.systems.relationship_system import RelationshipSystem


def _system():
    return RelationshipSystem()


def test_ensure_creates_neutral_defaults():
    system = _system()
    store = {}
    state = system.ensure(store, "npc_1")
    assert state["relationship_score"] == 0
    assert state["trust"] == 0
    assert state["known_player_actions"] == []
    assert state["personal_memory_flags"] == {}
    assert system.tier_for(state["relationship_score"]) == "neutral"


def test_adjust_clamps_and_reports_applied_delta():
    system = _system()
    store = {}
    result = system.adjust(store, "npc_1", {"trust": 200})
    assert store["npc_1"]["trust"] == 100
    assert result["applied"]["trust"] == 100
    assert result["tier"] == "neutral"


def test_tier_progression():
    system = _system()
    assert system.tier_for(-100) == "hostile"
    assert system.tier_for(0) == "neutral"
    assert system.tier_for(50) == "friendly"
    assert system.tier_for(90) == "trusted"


def test_relationship_score_can_go_negative_into_hostile():
    system = _system()
    store = {}
    system.adjust(store, "npc_1", {"relationship_score": -50})
    result = system.get(store, "npc_1")
    assert store["npc_1"]["relationship_score"] == -50
    assert result["tier"] == "hostile"


def test_remember_records_each_action_once():
    system = _system()
    store = {}
    system.remember(store, "npc_1", "spared_a_rival")
    system.remember(store, "npc_1", "spared_a_rival")
    system.remember(store, "npc_1", "kept_a_promise", flag="owes_a_debt")
    state = store["npc_1"]
    assert state["known_player_actions"] == ["spared_a_rival", "kept_a_promise"]
    assert state["personal_memory_flags"]["owes_a_debt"] is True
