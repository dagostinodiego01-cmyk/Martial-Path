"""Structural tests for the shipped world map (``data/locations.json``).

These complement ``test_all_game_data_valid`` (which checks cross-references) by
guarding map-specific invariants: the whole map is reachable from the starting
location, the V1 core path is present, cultivation gates actually block or
allow travel as intended, and no location is walled off behind a stricter gate
than the one it advertises.
"""
import heapq
import math
from collections import deque
from types import SimpleNamespace

from game.core.constants import AVAILABLE_SYSTEMS
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


def test_available_systems_only_declare_implemented_verbs():
    for location in _locations(_registry()).values():
        dead = set(location.get("available_systems", [])) - set(AVAILABLE_SYSTEMS)
        assert not dead, f"location '{location['id']}' declares unimplemented systems: {sorted(dead)}"


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


def _realm_order(realms_data):
    """Map realm ids and display names (lowercased) to their order value."""
    order = {}
    for realm in (realms_data or {}).get("realms", []):
        for key in (realm.get("id"), realm.get("display_name")):
            if key:
                order[str(key).strip().lower()] = int(realm.get("order", 0))
    return order


def _gate(location, track, order):
    """Return the unlock order a location demands on one cultivation track."""
    minimum = (location.get("requirements", {}).get(track) or {}).get("minimum_realm")
    if minimum is None:
        return 0, True
    key = str(minimum).strip().lower()
    if key in ("", "none", "any"):
        return 0, True
    return order.get(key, 0), key in order


def test_every_travel_gate_names_a_real_realm():
    """An unresolvable gate is silently ignored, so the location is walk-in."""
    registry = _registry()
    tracks = (
        ("body_transformation", _realm_order(registry.body_realms)),
        ("essence_gathering", _realm_order(registry.essence_realms)),
    )
    for location in _locations(registry).values():
        for track, order in tracks:
            _, resolvable = _gate(location, track, order)
            minimum = (location.get("requirements", {}).get(track) or {}).get("minimum_realm")
            assert resolvable, (
                f"location '{location['id']}' {track} minimum_realm {minimum!r} matches no "
                "realm id or display name, so the gate never fires"
            )


def test_validator_flags_an_unresolvable_gate():
    """Negative test: the shipped "Nine Stars Dao Palace" typo must be caught.

    ``_validate_locations`` is handed a one-location stub registry so the real
    location data stays untouched.
    """
    from game.validation.data_validator import _validate_locations
    from game.validation.validation_error import ValidationResult

    real = _registry()

    def _stub(minimum_realm):
        location = {
            "id": "gate_array_approach",
            "danger_level": 9,
            "qi_density": 9,
            "story_tier": 6,
            "map_position": {"x": 0.79, "y": 0.44},
            "connected_locations": [],
            "npc_ids": [],
            "available_systems": ["explore"],
            "requirements": {
                "body_transformation": {"minimum_realm": minimum_realm, "minimum_stage": 1},
                "essence_gathering": {"minimum_realm": "Divine Sea", "minimum_stage": 1},
            },
        }
        return SimpleNamespace(
            locations=[location],
            characters=[],
            body_realms=real.body_realms,
            essence_realms=real.essence_realms,
        )

    for accepted in ("nine_stars_dao_palace", "Nine Stars of the Dao Palace", "None"):
        result = ValidationResult()
        _validate_locations(_stub(accepted), result)
        assert result.is_valid, f"'{accepted}' should resolve: {result.format_errors()}"

    rejected = ValidationResult()
    _validate_locations(_stub("Nine Stars Dao Palace"), rejected)
    assert [error.category for error in rejected.errors] == ["dead_travel_gate"]


def test_every_location_declares_available_systems():
    for location in _locations(_registry()).values():
        assert location.get("available_systems"), (
            f"location '{location['id']}' declares no available systems"
        )


def test_no_location_is_walled_behind_a_stricter_gate_than_its_own():
    """Every location must open at (not after) the realm its own gate names.

    Minimax over the body track: the cheapest route to a location should never
    demand a higher realm than that location's own gate, which would strand an
    easy area behind a hard gateway.
    """
    registry = _registry()
    locations = _locations(registry)
    order = _realm_order(registry.body_realms)

    best = {START_LOCATION: 0}
    queue = [(0, START_LOCATION)]
    while queue:
        demand, current = heapq.heappop(queue)
        if demand != best.get(current):
            continue
        for neighbor in locations[current].get("connected_locations", []):
            neighbor_demand, _ = _gate(locations[neighbor], "body_transformation", order)
            candidate = max(demand, neighbor_demand)
            if candidate < best.get(neighbor, math.inf):
                best[neighbor] = candidate
                heapq.heappush(queue, (candidate, neighbor))

    for location_id, location in locations.items():
        own, _ = _gate(location, "body_transformation", order)
        assert best.get(location_id, math.inf) <= own, (
            f"location '{location_id}' gates at order {own} but needs order "
            f"{best.get(location_id, math.inf)} to reach"
        )


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
