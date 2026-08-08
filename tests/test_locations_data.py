"""Structural tests for the shipped world map (``data/locations.json``).

These complement ``test_all_game_data_valid`` (which checks cross-references) by
guarding map-specific invariants: the whole map is reachable from the starting
location, the V1 core path is present, and cultivation gates actually block or
allow travel as intended.
"""
from collections import deque
from types import SimpleNamespace

from game.data.registry import GameDataRegistry
from game.services.travel_service import TravelService
from game.systems.location_system import LocationSystem

START_LOCATION = "outer_forest"

# The first playable path: safe early game -> academy -> Seven Profound Valleys
# -> Divine Phoenix Island (see the world-map implementation plan).
V1_CORE = {
    "azure_village",
    "sky_fortune_road",
    "starting_village",
    "beast_mountain",
    "lin_academy",
    "sky_fortune_capital",
    "seven_profound_valleys_gate",
    "seven_profound_valleys_inner",
    "forbidden_back_mountain",
    "south_horizon_road",
    "south_horizon_city",
    "divine_phoenix_island",
    "south_sea_port",
}


def _registry():
    return GameDataRegistry.load()


def _locations(registry):
    return {entry["id"]: entry for entry in registry.locations}


def _reachable_from(start, locations):
    """Directed breadth-first search over ``connected_locations`` edges."""
    seen = {start}
    queue = deque([start])
    while queue:
        current = locations.get(queue.popleft(), {})
        for neighbor in current.get("connected_locations", []):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen


def _player(body_realm_id, essence_realm_id, location):
    cultivation = SimpleNamespace(
        body=SimpleNamespace(realm_id=body_realm_id),
        essence=SimpleNamespace(realm_id=essence_realm_id),
    )
    return SimpleNamespace(
        current_location=location,
        cultivation_state=cultivation,
        inventory={},
        reputation=0,
    )


def test_start_location_exists():
    assert START_LOCATION in _locations(_registry())


def test_all_locations_have_normalized_map_positions():
    for location in _locations(_registry()).values():
        position = location.get("map_position")
        assert isinstance(position, dict), location["id"]
        assert 0 <= position.get("x", -1) <= 1, location["id"]
        assert 0 <= position.get("y", -1) <= 1, location["id"]


def test_location_view_exposes_map_position():
    registry = _registry()
    view = LocationSystem(registry.locations).view("outer_forest")

    assert view["map_position"] == _locations(registry)["outer_forest"]["map_position"]


def test_whole_map_is_reachable_from_start():
    locations = _locations(_registry())
    reachable = _reachable_from(START_LOCATION, locations)
    orphans = set(locations) - reachable
    assert not orphans, f"unreachable locations from '{START_LOCATION}': {sorted(orphans)}"


def test_v1_core_path_is_present_and_reachable():
    locations = _locations(_registry())
    missing = V1_CORE - set(locations)
    assert not missing, f"missing V1 core locations: {sorted(missing)}"
    reachable = _reachable_from(START_LOCATION, locations)
    assert V1_CORE <= reachable


def test_azure_village_bridges_into_the_kingdom():
    locations = _locations(_registry())
    assert "sky_fortune_road" in locations["azure_village"]["connected_locations"]


def test_starting_village_anchors_the_lin_family():
    npcs = set(_locations(_registry())["starting_village"]["npc_ids"])
    assert {"lin_xiaodong", "lin_fu", "lin_mu"} <= npcs


def test_cultivation_gate_allows_qualified_travel():
    registry = _registry()
    service = TravelService(
        LocationSystem(registry.locations), registry.body_realms, registry.essence_realms
    )
    # A Pulse Condensation / Houtian cultivator standing on the South Horizon
    # route meets Divine Phoenix Island's entry requirement.
    player = _player("body_pulse_condensation", "houtian", "south_horizon_road")
    assert service.can_travel_to(player, "divine_phoenix_island") == {"allowed": True, "reason": None}


def test_cultivation_gate_blocks_underleveled_endgame_travel():
    registry = _registry()
    service = TravelService(
        LocationSystem(registry.locations), registry.body_realms, registry.essence_realms
    )
    # The same cultivator is far too weak to cross into the Holy Demon Continent.
    player = _player("body_pulse_condensation", "houtian", "south_sea_port")
    result = service.can_travel_to(player, "holy_demon_continent")
    assert result["allowed"] is False
    assert result["reason"] == "BODY_REALM_TOO_LOW"
