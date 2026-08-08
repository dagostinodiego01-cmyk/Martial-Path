"""Tests for the CharacterService coordination layer."""
from types import SimpleNamespace

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
        "id": "mentor",
        "name": "Old Mentor",
        "faction": "None",
        "unlock": {"min_stage": 1},
        "personality": {
            "speech_style": "Gruff.",
            "morality_reaction": {"righteous": "Nods.", "neutral": "Watches.", "demonic": "Frowns."},
            "relationship_behavior": {"hostile": "Cold.", "neutral": "Polite.", "friendly": "Warm.", "trusted": "Open."},
        },
        "gameplay_hooks": {"can_talk": True, "can_spar": True, "can_duel": False, "enemy_id": "mentor_spar"},
        "intro_text": "Hello.",
    },
    {
        "id": "boss",
        "name": "Dark Boss",
        "faction": "Evil",
        "unlock": {"min_stage": 5},
        "personality": {
            "speech_style": "Cruel.",
            "morality_reaction": {"righteous": "", "neutral": "", "demonic": ""},
            "relationship_behavior": {"hostile": "", "neutral": "", "friendly": "", "trusted": ""},
        },
        "gameplay_hooks": {"can_talk": True, "can_spar": False, "can_duel": True, "enemy_id": "boss_duel"},
    },
]
LOCATIONS = [{"id": "hall", "display_name": "Hall", "npc_ids": ["mentor", "boss"], "connected_locations": []}]


def _service():
    return CharacterService(
        CHARACTERS, LocationSystem(LOCATIONS), MoralitySystem(MORALITY), RelationshipSystem(RELATIONSHIPS)
    )


def _player(morality=0, stage=1, relationships=None):
    return SimpleNamespace(
        morality=morality, stage=stage, relationships=relationships or {}, current_location="hall"
    )


def test_available_characters_are_scoped_to_the_location():
    briefs = _service().get_available_characters("hall", _player())
    assert {b["id"] for b in briefs} == {"mentor", "boss"}


def test_dialogue_context_selects_by_morality_band_and_tier():
    service = _service()
    player = _player(morality=50, relationships={"mentor": {"relationship_score": 80}})
    context = service.get_dialogue_context("mentor", player)
    assert context["morality_band"] == "righteous"
    assert context["morality_reaction"] == "Nods."
    assert context["relationship_tier"] == "trusted"
    assert context["relationship_behavior"] == "Open."


def test_can_spar_reflects_hooks_and_can_duel_respects_unlock():
    service, player = _service(), _player(stage=1)
    assert service.can_spar("mentor", player)["allowed"] is True
    assert service.can_duel("mentor", player) == {"allowed": False, "reason": "NOT_AVAILABLE"}
    # The boss allows duels but is locked until stage 5.
    assert service.can_duel("boss", player) == {"allowed": False, "reason": "LOCKED"}
    assert service.can_duel("boss", _player(stage=5))["allowed"] is True


def test_relationship_view_defaults_neutral_without_mutating_store():
    service, player = _service(), _player()
    view = service.get_relationship_view("mentor", player)
    assert view["tier"] == "neutral"
    assert view["behavior_text"] == "Polite."
    assert player.relationships == {}  # viewing must not create store entries


def test_engine_exposes_location_characters():
    engine = GameEngine.new_game(seed=1)
    briefs = engine.character_service.get_available_characters("azure_village", engine.player)
    assert any(b["id"] == "lan_yunyue" for b in briefs)
