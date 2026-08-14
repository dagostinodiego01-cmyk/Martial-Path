"""Tests for relationship-gated rewards (boons) and morality-gated interactions.

Covers the P9 wiring: an NPC's ``relationship_rewards`` become claimable only
once the relationship tier (and, optionally, morality band) is met, and spar/duel
can additionally require a morality band -- so player choices that shift these
scores change what is available over time.
"""
from types import SimpleNamespace

from game.core.constants import Action, EventType
from game.core.game_engine import GameEngine
from game.services.character_service import CharacterService
from game.systems.location_system import LocationSystem
from game.systems.morality_system import MoralitySystem
from game.systems.relationship_system import RelationshipSystem

MORALITY = {
    "min": -100,
    "max": 100,
    "default": 0,
    "bands": [
        {"id": "demonic", "label": "Demonic", "min": -100, "max": -34},
        {"id": "neutral", "label": "Neutral", "min": -33, "max": 33},
        {"id": "righteous", "label": "Righteous", "min": 34, "max": 100},
    ],
}
RELATIONSHIPS = {
    "variables": {"relationship_score": {"min": -100, "max": 100, "default": 0}},
    "tiers": [
        {"id": "hostile", "min": -100, "max": -34},
        {"id": "neutral", "min": -33, "max": 33},
        {"id": "friendly", "min": 34, "max": 74},
        {"id": "trusted", "min": 75, "max": 100},
    ],
}
CHARACTERS = [
    {
        "id": "sage",
        "name": "The Sage",
        "faction": "None",
        "unlock": {"min_stage": 1},
        "personality": {
            "speech_style": "Calm.",
            "morality_reaction": {"righteous": "Nods.", "neutral": "Watches.", "demonic": "Frowns."},
            "relationship_behavior": {"hostile": "Cold.", "neutral": "Polite.", "friendly": "Warm.", "trusted": "Open."},
        },
        "gameplay_hooks": {
            "can_talk": True,
            "can_spar": True,
            "can_duel": True,
            "enemy_id": "sage_duel",
            "spar_morality_band": "righteous",
            "relationship_rewards": [
                {"min_tier": "friendly", "reward": {"gold": 60}, "once": True},
                {"min_tier": "trusted", "morality_band": "righteous", "reward": {"exp": 120}, "once": True},
            ],
        },
    },
]
LOCATIONS = [{"id": "hall", "display_name": "Hall", "npc_ids": ["sage"], "connected_locations": []}]


def _service() -> CharacterService:
    return CharacterService(CHARACTERS, LocationSystem(LOCATIONS), MoralitySystem(MORALITY), RelationshipSystem(RELATIONSHIPS))


def _player(morality=0, stage=1, relationships=None):
    return SimpleNamespace(
        morality=morality, stage=stage, relationships=relationships or {}, current_location="hall"
    )


def test_reward_gates_on_relationship_tier():
    service = _service()
    assert service.available_reward("sage", _player()) is None  # neutral < friendly
    friendly = _player(relationships={"sage": {"relationship_score": 50}})
    assert service.available_reward("sage", friendly)["reward"]["gold"] == 60


def test_reward_gates_on_morality_band():
    service = _service()
    # First (friendly) reward already claimed; second needs righteous + trusted.
    flags = {"personal_memory_flags": {"reward_0": True}}
    demonic = _player(morality=-60, relationships={"sage": {"relationship_score": 80, **flags}})
    assert service.available_reward("sage", demonic) is None
    righteous = _player(morality=60, relationships={"sage": {"relationship_score": 80, **flags}})
    assert service.available_reward("sage", righteous)["reward"]["exp"] == 120


def test_spar_gates_on_morality_band():
    service = _service()
    assert service.can_spar("sage", _player(morality=-60)) == {"allowed": False, "reason": "MORALITY_BAND_MISMATCH"}
    assert service.can_spar("sage", _player(morality=60))["allowed"] is True


def test_engine_receive_boon_grants_gold_and_claims_once():
    engine = GameEngine.new_game(seed=1)
    engine.player.relationships = {"zhu_yan": {"relationship_score": 60}}
    gold_before = engine.player.gold

    result = engine.process_action({"action": Action.RECEIVE_BOON, "character_id": "zhu_yan"})
    assert result["event"] == EventType.BOON
    assert result["reward"]["gold"] == 60
    assert engine.player.gold == gold_before + 60

    again = engine.process_action({"action": Action.RECEIVE_BOON, "character_id": "zhu_yan"})
    assert again["event"] == EventType.ERROR
    assert again["reason"] == "NO_REWARD_AVAILABLE"


def test_engine_receive_boon_grants_item():
    engine = GameEngine.new_game(seed=1)
    engine.player.stage = 4  # duanmu_qun unlocks at stage 4
    engine.player.relationships = {"duanmu_qun": {"relationship_score": 60}}

    result = engine.process_action({"action": Action.RECEIVE_BOON, "character_id": "duanmu_qun"})
    assert result["event"] == EventType.BOON
    assert result["reward"]["items"] == {"profound_pill": 2}
    assert engine.player.inventory.get("profound_pill", 0) == 2


def test_engine_map_returns_position_and_destinations():
    engine = GameEngine.new_game(seed=1)
    result = engine.process_action({"action": Action.MAP})
    assert result["event"] == EventType.MAP
    assert "map_position" in result
    assert isinstance(result["destinations"], list)
