"""Procedural secret realm (ROADMAP D.2)."""
from game.core.constants import Action, EventType
from game.core.game_engine import GameEngine
from game.data.registry import GameDataRegistry
from game.systems.secret_realm_system import SecretRealmSystem
from game.utils.rng import RNG


def _system():
    return SecretRealmSystem(GameDataRegistry.load().secret_realm, RNG(1))


def _rooms(seed, location_id="misty_gorge"):
    realm = SecretRealmSystem(GameDataRegistry.load().secret_realm, RNG(seed))
    return [(room["kind"], room.get("enemy_id"), room.get("item_id")) for room in realm.generate(location_id)["rooms"]]


def test_same_seed_produces_identical_layout():
    assert _rooms(1) == _rooms(1)


def test_different_seed_produces_different_layout():
    # A few seeds to be robust against coincidental equality on tiny pools.
    assert any(_rooms(1) != _rooms(seed) for seed in (2, 3, 4, 5))


def test_realm_ends_with_a_named_boss():
    realm = _system()
    rooms = realm.generate("misty_gorge")["rooms"]
    assert rooms[-1]["kind"] == "boss"
    assert rooms[-1]["named"] is True


def test_catalogue_has_at_least_five_realms_at_distinct_locations():
    realm = _system()
    assert realm.count >= 5
    definitions = GameDataRegistry.load().secret_realm
    locations = {entry["location_id"] for entry in definitions}
    assert len(locations) == len(definitions)  # one realm per location


def test_realm_generates_only_at_its_location():
    realm = _system()
    assert realm.realm_available_at("misty_gorge") is True
    assert realm.realm_available_at("holy_demon_continent") is True
    assert realm.realm_available_at("azure_village") is False


def test_enter_realm_requires_the_right_location():
    engine = GameEngine.new_game(seed=1)
    engine.player.current_location = "outer_forest"

    result = engine.process_action({"action": Action.ENTER_REALM})
    assert result["event"] == EventType.ERROR
    assert result["reason"] == "NO_REALM_HERE"

    engine.player.current_location = "misty_gorge"
    result = engine.process_action({"action": Action.ENTER_REALM})
    assert result["event"] == EventType.REALM_ENTERED
    assert result["rooms_total"] > 1


def test_realm_advance_resolves_treasure_then_combat():
    engine = GameEngine.new_game(seed=1)
    engine._realm = {
        "realm": {
            "id": "x",
            "display_name": "X",
            "final_reward": {"gold": 100},
            "rooms": [
                {"kind": "treasure", "item_id": "healing_pill", "count": 1},
                {"kind": "encounter", "enemy_id": "iron_wolf", "named": False},
            ],
        },
        "index": 0,
    }

    before = engine.player.inventory.get("healing_pill", 0)
    treasure = engine.process_action({"action": Action.REALM_ADVANCE})
    assert treasure["event"] == EventType.REALM_ROOM
    assert treasure["kind"] == "treasure"
    assert engine.player.inventory.get("healing_pill", 0) == before + 1

    combat = engine.process_action({"action": Action.REALM_ADVANCE})
    assert combat["event"] == EventType.COMBAT
    assert engine._mode == "combat"
    assert engine._current_enemy is not None
    assert combat["enemy"]["name"] == engine._current_enemy.name


def test_realm_leave_clears_realm():
    engine = GameEngine.new_game(seed=1)
    engine.player.current_location = "misty_gorge"
    engine.process_action({"action": Action.ENTER_REALM})
    assert engine._realm is not None

    result = engine.process_action({"action": Action.REALM_LEAVE})
    assert result["event"] == EventType.REALM_ROOM
    assert engine._realm is None


def test_completing_realm_grants_final_reward():
    engine = GameEngine.new_game(seed=1)
    engine.player.current_location = "misty_gorge"
    engine.process_action({"action": Action.ENTER_REALM})
    engine._realm["index"] = len(engine._realm["realm"]["rooms"])  # past the end

    result = engine.process_action({"action": Action.REALM_ADVANCE})

    assert result["event"] == EventType.REALM_COMPLETED
    assert result["reward"]["gold"] == 150
    assert engine.player.inventory.get("talent_refining_elixir", 0) == 1
    assert engine._realm is None
