"""Tests for the Dao layer: realm pressure, the counter-graph, and combat wiring."""
import pytest

from game.core.game_engine import GameEngine
from game.data.registry import GameDataRegistry
from game.models.enemy import Enemy
from game.models.player import Player
from game.systems.combat_system import CombatSystem
from game.systems.dao_system import DaoSystem, YIELD_GAP
from game.systems.stats_system import StatsSystem
from game.utils.rng import RNG


def _dao_system() -> DaoSystem:
    registry = GameDataRegistry.load()
    return DaoSystem(registry.daos, registry.body_realms, registry.essence_realms)


def _player(dao_id="sword_dao", body_realm="mortal", essence_realm="houtian", attack=100, defense=0, hp=1000):
    player = Player(name="Tester", attack=attack, defense=defense, hp=hp, max_hp=hp, dao_id=dao_id)
    player.cultivation_state.body.realm_id = body_realm
    player.cultivation_state.essence.realm_id = essence_realm
    return player


def _enemy(dao_id=None, body_realm="mortal", essence_realm=None, attack=100, defense=0, hp=1000):
    return Enemy.from_dict(
        {
            "id": "e",
            "name": "E",
            "body_realm_id": body_realm,
            "essence_realm_id": essence_realm,
            "attack": attack,
            "defense": defense,
            "hp": hp,
            "dao_id": dao_id,
        }
    )


def _combat() -> CombatSystem:
    return CombatSystem(RNG(0), StatsSystem({}), _dao_system())


# -- realm rank & pressure ----------------------------------------------
def test_default_player_dao_is_in_catalogue():
    dao = _dao_system()
    assert Player(name="X").dao_id == "sword_dao"
    assert dao.has_dao(Player(name="X").dao_id)


def test_fresh_cultivator_ranks_zero():
    dao = _dao_system()
    assert dao.player_rank(_player(body_realm="mortal", essence_realm="houtian")) == 0


def test_realm_rank_grows_with_body_realm():
    dao = _dao_system()
    assert dao.body_rank("strength_training") == 1
    assert dao.body_rank("nine_stars_dao_palace") == 9
    assert dao.realm_rank("strength_training", None) == 1


def test_no_pressure_for_equal_or_one_tier_gap():
    dao = _dao_system()
    equal = dao.pressure(_player(body_realm="mortal"), _enemy(body_realm="mortal"))
    assert equal["gap"] == 0
    assert equal["player_multiplier"] == 1.0 and equal["enemy_multiplier"] == 1.0


def test_pressure_suppresses_weaker_side():
    dao = _dao_system()
    # Player two body realms above the enemy.
    pressure = dao.pressure(_player(body_realm="flesh_training"), _enemy(body_realm="mortal"))
    assert pressure["gap"] == 2
    assert pressure["player_multiplier"] == 1.0
    assert pressure["enemy_multiplier"] == pytest.approx(0.75)


def test_enemy_yields_when_player_far_stronger():
    dao = _dao_system()
    strong = _player(body_realm="nine_stars_dao_palace")
    weak = _enemy(body_realm="mortal")
    assert dao.enemy_yields(strong, weak)
    assert not dao.enemy_yields(_player(body_realm="mortal"), _enemy(body_realm="mortal"))


# -- dao counter-graph ---------------------------------------------------
def test_counter_dao_multiplier():
    dao = _dao_system()
    assert dao.matchup("sword_dao", "verdant_dao") == pytest.approx(1.5)


def test_countered_dao_multiplier():
    dao = _dao_system()
    assert dao.matchup("verdant_dao", "sword_dao") == pytest.approx(0.75)


def test_void_and_unknown_daos_are_neutral():
    dao = _dao_system()
    assert dao.matchup("void_dao", "sword_dao") == 1.0
    assert dao.matchup("sword_dao", None) == 1.0
    assert dao.matchup("sword_dao", "not_a_dao") == 1.0


def test_every_non_void_dao_counters_exactly_one_and_is_countered_by_one():
    dao = _dao_system()
    for dao_id in dao.dao_ids():
        entry = next(d for d in dao.dao_view() if d["id"] == dao_id)
        if dao_id == "void_dao":
            assert entry["counters"] == [] and entry["countered_by"] == []
        else:
            assert len(entry["counters"]) == 1
            assert len(entry["countered_by"]) == 1


# -- combat integration -------------------------------------------------
def test_counter_dao_deals_more_damage_in_combat():
    combat = _combat()
    player = _player(dao_id="sword_dao")
    countered = _enemy(dao_id="verdant_dao")
    neutral = _enemy(dao_id="void_dao")
    combat.attack(player, countered)
    combat.attack(player, neutral)
    assert countered.hp < neutral.hp


def test_countered_dao_deals_less_damage_in_combat():
    combat = _combat()
    player = _player(dao_id="sword_dao")
    countering = _enemy(dao_id="flame_dao")
    neutral = _enemy(dao_id="void_dao")
    combat.attack(player, countering)
    combat.attack(player, neutral)
    assert countering.hp > neutral.hp


def test_realm_pressure_scales_offense():
    combat = _combat()
    player = _player(body_realm="flesh_training", dao_id="void_dao")
    enemy = _enemy(body_realm="mortal", dao_id="void_dao")
    assert combat._offense_scale(player, enemy, False) == pytest.approx(0.75)
    assert combat._offense_scale(player, enemy, True) == 1.0


def test_realm_pressure_reduces_enemy_damage():
    combat = _combat()
    strong = _player(body_realm="flesh_training", dao_id="void_dao", hp=100000)
    weak_enemy = _enemy(body_realm="mortal", dao_id="void_dao", attack=100, defense=0)
    combat.attack(strong, weak_enemy)
    # A suppressed mortal enemy lands less than its raw 100 attack on an unsuppressed defender.
    assert strong.hp > 100000 - 100


# -- engine wiring & save -----------------------------------------------
def test_engine_wires_dao_and_exposes_enemy_dao():
    engine = GameEngine.new_game(seed=1)
    assert engine.player.dao_id == "sword_dao"
    assert engine.dao.dao_name("sword_dao") == "Sword Dao"
    enemy = _enemy(dao_id="flame_dao", hp=50)
    view = engine._enemy_view(enemy)
    assert view["dao_name"] == "Flame Dao"
    assert "gap" in view["pressure"]


def test_player_dao_round_trips_through_save():
    player = Player(name="X", dao_id="time_dao")
    restored = Player.from_save_dict(player.to_save_dict())
    assert restored.dao_id == "time_dao"


def test_yielded_enemy_resolves_as_victory():
    engine = GameEngine.new_game(seed=1)
    engine.player.cultivation_state.body.realm_id = "nine_stars_dao_palace"
    enemy = Enemy.from_dict(
        {"id": "weak", "name": "Weak", "body_realm_id": "mortal", "attack": 1, "defense": 0, "hp": 10}
    )
    assert engine.dao.enemy_yields(engine.player, enemy)
    engine._current_enemy = enemy
    result = engine._end_combat(
        {
            "event": "COMBAT_END",
            "outcome": "VICTORY",
            "yielded": True,
            "enemy_name": enemy.name,
            "loot_table": enemy.loot_table,
            "turn_events": [{"actor": "ENEMY", "action": "YIELD", "enemy_name": enemy.name}],
        }
    )
    assert result["outcome"] == "VICTORY"
    assert result["yielded"] is True
    assert engine._current_enemy is None  # combat mode was exited cleanly
