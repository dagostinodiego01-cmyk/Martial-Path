"""Tests for location-scoped encounter selection."""
from types import SimpleNamespace

from game.core.constants import EventType
from game.systems.event_system import EventSystem
from game.utils.rng import RNG

ENEMIES = [
    {"id": "iron_wolf", "name": "Iron Wolf", "hp": 10, "attack": 3},
    {"id": "corpse_demon", "name": "Corpse Demon", "hp": 40, "attack": 12},
]
EVENTS = {
    "encounter_weights": {"COMBAT": 1.0, "LOOT": 0.0, "SPECIAL": 0.0, "NOTHING": 0.0},
    "loot_pool": [{"item_id": "healing_pill", "weight": 1}],
    "special_events": [{"id": "ancient_manual", "text": "x", "effect": {}}],
}
POOLS = {
    "shrine": {"combat": [{"enemy_id": "corpse_demon", "weight": 1}]},
}


def _player(location):
    return SimpleNamespace(current_location=location)


def test_location_pool_scopes_combat_selection():
    system = EventSystem(EVENTS, ENEMIES, RNG(seed=1), POOLS)
    # The shrine pool only spawns corpse_demon, regardless of the global roster.
    for _ in range(10):
        event = system.generate(_player("shrine"))
        assert event["event"] == EventType.COMBAT
        assert event["enemy_id"] == "corpse_demon"


def test_location_without_pool_falls_back_to_global_roster():
    system = EventSystem(EVENTS, ENEMIES, RNG(seed=1), POOLS)
    event = system.generate(_player("unmapped_place"))
    assert event["event"] == EventType.COMBAT
    assert event["enemy_id"] in {"iron_wolf", "corpse_demon"}


def test_loot_pool_falls_back_when_location_has_no_loot():
    events = dict(EVENTS)
    events["encounter_weights"] = {"COMBAT": 0.0, "LOOT": 1.0, "SPECIAL": 0.0, "NOTHING": 0.0}
    system = EventSystem(events, ENEMIES, RNG(seed=2), POOLS)
    event = system.generate(_player("shrine"))
    assert event["event"] == EventType.LOOT
    assert event["item_id"] == "healing_pill"
