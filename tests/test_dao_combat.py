"""Tests for the Dao layer: realm pressure, the counter-graph, and combat wiring.

The last block is the D.7 audit: the same seeds played once per dao against an
identical foe roster, so the only variable is the player's dao. A dao must not
sit more than 10% away from the median win rate.
"""
import statistics

import pytest

from game.core.game_engine import GameEngine
from game.data.registry import GameDataRegistry
from game.models.enemy import Enemy
from game.models.player import Player
from game.systems.combat_system import MAX_FIGHT_ROUNDS, CombatSystem
from game.systems.dao_system import DaoSystem, YIELD_GAP
from game.systems.foe_ai import FoeAI
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


# -- D.7 dao balance audit --------------------------------------------------
def _dao_win_rates(seeds=range(3), attack=30, defense=8, hp=200):
    """Win rate per dao over an identical dao-vs-dao foe roster.

    Parity stats and one foe per dao in the catalogue mean the only thing that
    varies between runs is the player's own dao -- exactly what the balance
    question asks. Plain attacks: no techniques, no items, no luck beyond the
    roll.
    """
    dao = _dao_system()
    rates = {}
    for player_dao in dao.dao_ids():
        wins = 0
        fights = 0
        for foe_dao in dao.dao_ids():
            for seed in seeds:
                combat = CombatSystem(RNG(seed), None, dao, foe_ai=FoeAI(dao=dao, rng=RNG(seed)))
                player = _player(dao_id=player_dao, attack=attack, defense=defense, hp=hp)
                enemy = _enemy(dao_id=foe_dao, attack=attack, defense=defense, hp=hp)
                fights += 1
                for _ in range(MAX_FIGHT_ROUNDS + 2):
                    result = combat.attack(player, enemy)
                    if result["event"] == "COMBAT_END":
                        if result.get("outcome") == "VICTORY":
                            wins += 1
                        break
        rates[player_dao] = wins / fights
    return rates


def test_no_dao_lands_outside_ten_percent_of_the_median_win_rate():
    """D.7: the same seeds, once per dao, spread no wider than +/-10%."""
    rates = _dao_win_rates()
    median = statistics.median(rates.values())

    outliers = {
        dao_id: round(rate, 3)
        for dao_id, rate in rates.items()
        if abs(rate - median) > 0.10 * median + 1e-9
    }
    assert not outliers, f"dao win rates drift outside +/-10% of {median:.3f}: {outliers}"
    assert 0.0 < median < 1.0, "the audit is vacuous unless fights are genuinely undecided"


def test_non_void_daos_are_structurally_interchangeable():
    """Every non-void dao counters exactly one and is countered by one, so in a
    round-robin they must all post the identical win rate. A drift here means the
    counter graph has stopped being a single cycle."""
    rates = _dao_win_rates(seeds=range(2))
    non_void = [rate for dao_id, rate in rates.items() if dao_id != "void_dao"]

    assert len(set(round(rate, 6) for rate in non_void)) == 1


def test_void_daos_neutrality_is_the_measured_edge_to_price():
    """Audit note (D.7): ``void_dao`` never gains a counter bonus but is never
    countered either, so it wins every mirror in the round-robin -- measured at
    the top of the +/-10% band and nowhere near the bottom. The band holds, and
    this test is what will fail if a future dao change pushes it out.
    """
    rates = _dao_win_rates(seeds=range(3))
    median = statistics.median(rates.values())

    assert rates["void_dao"] == max(rates.values())
    assert rates["void_dao"] - median <= 0.10 * median + 1e-9


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
