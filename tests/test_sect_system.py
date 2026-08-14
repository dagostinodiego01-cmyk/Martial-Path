"""Tests for sect joining, path assignment, and join gating."""
from game.core.constants import EventType
from game.models.player import Player
from game.systems.sect_system import SectSystem

BODY_REALMS = {
    "realms": [
        {"id": "mortal", "order": 0},
        {"id": "flesh_training", "order": 2},
        {"id": "bone_forging", "order": 5},
        {"id": "body_pulse_condensation", "order": 6},
    ]
}

SECTS = [
    {
        "id": "divine_phoenix_island",
        "display_name": "Divine Phoenix Island",
        "path": "Divine Phoenix",
        "location_ids": ["divine_phoenix_island"],
        "join_requirements": {"min_reputation": 15, "min_body_realm": "bone_forging"},
        "contribution_ranks": ["outer_disciple", "inner_disciple"],
    },
    {
        "id": "asura_kingdom",
        "display_name": "Asura Divine Kingdom",
        "path": "Asura Path",
        "location_ids": ["asura_divine_kingdom"],
        "join_requirements": {"max_reputation": -10, "min_body_realm": "body_pulse_condensation"},
        "contribution_ranks": ["blood_disciple"],
    },
]


def _system() -> SectSystem:
    return SectSystem(SECTS, BODY_REALMS)


def _player(location="divine_phoenix_island", reputation=20, realm="bone_forging") -> Player:
    player = Player(name="Tester", current_location=location, reputation=reputation)
    player.cultivation_state.body.realm_id = realm
    return player


def test_join_sets_player_path_and_starting_rank():
    system = _system()

    result = system.join(_player(), "divine_phoenix_island")

    assert result["event"] == EventType.SECT_JOINED
    assert result["path"] == "Divine Phoenix"
    assert result["rank"] == "outer_disciple"


def test_join_gated_by_body_realm():
    system = _system()

    result = system.join(_player(realm="flesh_training"), "divine_phoenix_island")

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "REALM_TOO_LOW"


def test_join_gated_by_min_reputation():
    system = _system()

    result = system.join(_player(reputation=5), "divine_phoenix_island")

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "REPUTATION_TOO_LOW"


def test_join_gated_by_max_reputation():
    system = _system()

    result = system.join(_player(location="asura_divine_kingdom", reputation=0, realm="body_pulse_condensation"), "asura_kingdom")

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "REPUTATION_TOO_HIGH"

    joined = system.join(_player(location="asura_divine_kingdom", reputation=-20, realm="body_pulse_condensation"), "asura_kingdom")
    assert joined["event"] == EventType.SECT_JOINED
    assert joined["path"] == "Asura Path"


def test_join_gated_by_location():
    system = _system()

    result = system.join(_player(location="outer_forest"), "divine_phoenix_island")

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "SECT_NOT_AVAILABLE"


def test_join_same_sect_again_is_rejected():
    system = _system()
    player = _player()
    player.path = "Divine Phoenix"

    result = system.join(player, "divine_phoenix_island")

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "ALREADY_JOINED"


def test_sects_for_location_filters_by_location():
    system = _system()

    assert [s["id"] for s in system.sects_for_location("divine_phoenix_island")] == ["divine_phoenix_island"]
    assert system.sects_for_location("outer_forest") == []
