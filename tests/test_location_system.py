"""Tests for the data-driven location/world-map system."""
from game.systems.location_system import LocationSystem, danger_label, qi_density_label

LOCATIONS = [
    {
        "id": "a",
        "display_name": "A",
        "danger_level": 2,
        "qi_density": 4,
        "npc_ids": ["npc_a"],
        "connected_locations": ["b"],
    },
    {"id": "b", "display_name": "B", "danger_level": 6, "connected_locations": ["a"]},
    {"id": "c", "display_name": "C", "connected_locations": []},
]


def _system():
    return LocationSystem(LOCATIONS)


def test_exists_and_get():
    system = _system()
    assert system.exists("a")
    assert not system.exists("z")
    assert system.get("a")["display_name"] == "A"


def test_can_travel_requires_direct_connection():
    system = _system()
    assert system.can_travel("a", "b")
    assert not system.can_travel("a", "c")
    assert not system.can_travel("a", "z")


def test_view_lists_exits_with_briefs():
    system = _system()
    view = system.view("a")
    assert view["known"] is True
    assert view["name"] == "A"
    assert {exit["id"] for exit in view["connections"]} == {"b"}


def test_view_exposes_numeric_levels_and_display_labels():
    system = _system()
    view = system.view("a")
    assert view["danger_level"] == 2
    assert view["danger"] == "Low"
    assert view["qi_density"] == 4
    assert view["qi_density_label"] == "Moderate"
    assert view["npc_ids"] == ["npc_a"]


def test_neighbors_and_npc_ids_accessors():
    system = _system()
    assert system.neighbors("a") == ["b"]
    assert system.npc_ids("a") == ["npc_a"]
    assert system.display_name("b") == "B"


def test_legacy_connections_key_still_loads():
    system = LocationSystem([{"id": "x", "name": "X", "connections": ["y"]}, {"id": "y", "name": "Y"}])
    assert system.can_travel("x", "y")
    assert system.view("x")["name"] == "X"


def test_danger_and_qi_labels_map_from_numbers():
    assert danger_label(0) == "Safe"
    assert danger_label(6) == "High"
    assert qi_density_label(1) == "Faint"
    assert qi_density_label(6) == "Dense"


def test_view_unknown_location_is_marked_unknown():
    system = _system()
    view = system.view("z")
    assert view["known"] is False

