"""Tests for the travel service: adjacency, requirement gating, and moves."""
from types import SimpleNamespace

from game.core.constants import EventType
from game.services.travel_service import TravelService
from game.systems.location_system import LocationSystem

BODY_REALMS = {
    "realms": [
        {"id": "mortal", "display_name": "Mortal", "order": 0},
        {"id": "strength_training", "display_name": "Strength Training", "order": 1},
        {"id": "flesh_training", "display_name": "Flesh Training", "order": 2},
    ]
}
ESSENCE_REALMS = {"realms": [{"id": "houtian", "display_name": "Houtian", "order": 1}]}

LOCATIONS = [
    {
        "id": "home",
        "display_name": "Home",
        "danger_level": 0,
        "connected_locations": ["market", "gorge", "vault"],
        "requirements": {"body_transformation": {"minimum_realm": "Mortal"}},
    },
    {"id": "market", "display_name": "Market", "danger_level": 1, "connected_locations": ["home"]},
    {
        "id": "gorge",
        "display_name": "Deep Gorge",
        "danger_level": 5,
        "connected_locations": ["home"],
        "requirements": {"body_transformation": {"minimum_realm": "Flesh Training"}},
    },
    {
        "id": "vault",
        "display_name": "Sealed Vault",
        "danger_level": 3,
        "connected_locations": ["home"],
        "requirements": {"required_items": ["vault_key"], "required_reputation": [{"min": 50}]},
    },
]


def _player(realm_id="mortal", loc="home", inventory=None, reputation=0):
    cultivation = SimpleNamespace(
        body=SimpleNamespace(realm_id=realm_id),
        essence=SimpleNamespace(realm_id="houtian"),
    )
    return SimpleNamespace(
        current_location=loc,
        cultivation_state=cultivation,
        inventory=dict(inventory or {}),
        reputation=reputation,
    )


def _service():
    return TravelService(LocationSystem(LOCATIONS), BODY_REALMS, ESSENCE_REALMS)


def test_travel_to_connected_location_moves_player():
    service, player = _service(), _player()
    result = service.travel_to(player, "market")
    assert result["event"] == EventType.TRAVEL_RESULT
    assert player.current_location == "market"


def test_already_there_is_rejected():
    service, player = _service(), _player()
    result = service.travel_to(player, "home")
    assert result["reason"] == "ALREADY_THERE"


def test_unconnected_location_has_no_route():
    service, player = _service(), _player(loc="market")
    result = service.travel_to(player, "gorge")
    assert result["reason"] == "NO_ROUTE"
    assert player.current_location == "market"


def test_body_realm_requirement_blocks_underleveled_travel():
    service, player = _service(), _player(realm_id="mortal")
    result = service.travel_to(player, "gorge")
    assert result["event"] == EventType.ERROR
    assert result["reason"] == "BODY_REALM_TOO_LOW"
    assert player.current_location == "home"


def test_body_realm_requirement_allows_when_met():
    service, player = _service(), _player(realm_id="flesh_training")
    result = service.travel_to(player, "gorge")
    assert result["event"] == EventType.TRAVEL_RESULT
    assert player.current_location == "gorge"


def test_required_item_and_reputation_gate_vault():
    service = _service()
    blocked = service.can_travel_to(_player(), "vault")
    assert blocked == {"allowed": False, "reason": "MISSING_REQUIRED_ITEM"}

    has_item = service.can_travel_to(_player(inventory={"vault_key": 1}), "vault")
    assert has_item == {"allowed": False, "reason": "REPUTATION_TOO_LOW"}

    ready = service.can_travel_to(_player(inventory={"vault_key": 1}, reputation=60), "vault")
    assert ready == {"allowed": True, "reason": None}


def test_available_destinations_flag_reachable_and_locked():
    service, player = _service(), _player()
    by_id = {dest["id"]: dest for dest in service.get_available_destinations(player)}
    assert by_id["market"]["reachable"] is True
    assert by_id["gorge"]["reachable"] is False
    assert by_id["gorge"]["reason"] == "BODY_REALM_TOO_LOW"
    assert by_id["market"]["danger"] == "Low"
