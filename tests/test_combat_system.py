"""Tests for combat skill-effect resolution and passive stat derivation.

Also the L2 combat-feel rules, which are measured rather than asserted by eye:
status stacking (CB.2), the 4-8 round fight budget and its stalemate backstop
(CB.5), the retreat that has to save a run (CB.7), and the insight ledger
(D.4).
"""
import statistics

import pytest

from game.models.enemy import Enemy
from game.models.player import Player
from game.models.skill import Skill
from game.systems.combat_system import (
    FATIGUE_PER_ROUND,
    FLEE_BASE_CHANCE,
    FLEE_WOUNDED_BONUS,
    MAX_FIGHT_ROUNDS,
    STALL_ROUNDS,
    STATUS_MAX_STACKS,
    CombatSystem,
    status_views,
)
from game.systems.stats_system import StatsSystem
from game.utils.rng import RNG


def _skill(**overrides):
    base = {
        "id": "x",
        "name": "X",
        "type": "active",
        "effect": "damage",
        "scaling": 1.0,
        "cooldown": 0,
        "qi_cost": 10,
    }
    base.update(overrides)
    return Skill.from_dict(base)


def _player(attack=100, defense=0, hp=1000, max_hp=1000, max_qi=100, qi=100, skills=()):
    return Player(
        name="Tester",
        attack=attack,
        defense=defense,
        hp=hp,
        max_hp=max_hp,
        max_qi=max_qi,
        qi=qi,
        skills=list(skills),
    )


def _enemy(attack=100, defense=0, hp=1000):
    return Enemy.from_dict(
        {"id": "e", "name": "E", "body_realm_id": "mortal", "attack": attack, "defense": defense, "hp": hp}
    )


def _combat(skills=()):
    skill_map = {s.id: s for s in skills}
    stats = StatsSystem(skill_map)
    return CombatSystem(RNG(0), stats), stats


# -- active skill effects ------------------------------------------------
def test_damage_skill_deals_damage():
    combat, _ = _combat()
    player, enemy = _player(), _enemy(defense=0)
    combat.use_skill(player, enemy, _skill(effect="damage", scaling=1.0))
    assert enemy.hp < enemy.max_hp


def test_true_damage_ignores_defense():
    combat, _ = _combat()
    player = _player(attack=100)
    normal = _enemy(defense=1000)
    armored = _enemy(defense=1000)
    combat.use_skill(player, normal, _skill(effect="damage", scaling=1.0))
    combat.use_skill(player, armored, _skill(effect="true_damage", scaling=1.0))
    assert armored.hp < normal.hp


def test_stun_skips_enemy_attack():
    combat, _ = _combat()
    player, enemy = _player(), _enemy()
    result = combat.use_skill(player, enemy, _skill(effect="stun", scaling=1))
    actions = [e.get("action") for e in result["turn_events"]]
    assert "STUNNED" in actions
    assert not any(e.get("actor") == "ENEMY" and e.get("action") == "ATTACK" for e in result["turn_events"])
    assert player.hp == player.max_hp


def test_dot_damage_ticks_over_turns():
    combat, _ = _combat()
    player, enemy = _player(), _enemy()
    combat.use_skill(player, enemy, _skill(effect="dot_damage", scaling=1.0))
    assert "dot_damage" in enemy.statuses
    assert enemy.hp < enemy.max_hp
    before = enemy.hp
    combat.enemy_turn_only(player, enemy)
    assert enemy.hp < before


def test_shield_absorbs_enemy_retaliation():
    combat, _ = _combat()
    player, enemy = _player(), _enemy(attack=100)
    combat.use_skill(player, enemy, _skill(effect="shield", scaling=5.0))
    assert player.hp == player.max_hp  # the retaliation was fully absorbed
    assert player.shield < 500  # some shield was consumed


def test_counter_damages_attacker():
    combat, _ = _combat()
    player, enemy = _player(), _enemy()
    result = combat.use_skill(player, enemy, _skill(effect="counter", scaling=1.0))
    attack = next(e for e in result["turn_events"] if e.get("actor") == "ENEMY" and e.get("action") == "ATTACK")
    assert attack.get("counter_damage", 0) > 0
    assert enemy.hp < enemy.max_hp


def test_life_steal_heals_player():
    combat, _ = _combat()
    player = _player(hp=500)
    enemy = _enemy(attack=0)
    combat.use_skill(player, enemy, _skill(effect="life_steal", scaling=1.0))
    assert player.hp > 550
    assert enemy.hp < enemy.max_hp


def test_heal_self_heals_player():
    combat, _ = _combat()
    player = _player(hp=500)
    enemy = _enemy(attack=0)
    combat.use_skill(player, enemy, _skill(effect="heal_self", scaling=1.0))
    assert player.hp > 500


def test_execute_finishes_low_hp_enemy():
    combat, _ = _combat()
    player, enemy = _player(attack=100), _enemy(hp=50)
    result = combat.use_skill(player, enemy, _skill(effect="execute", scaling=1.0))
    assert result["event"] == "COMBAT_END"
    assert result["outcome"] == "VICTORY"


def test_debuff_attack_reduces_enemy_attack():
    combat, _ = _combat()
    player, enemy = _player(), _enemy(attack=100)
    combat.use_skill(player, enemy, _skill(effect="debuff_attack", scaling=2.0))
    assert combat._enemy_attack_value(enemy) == 50


# -- passives via StatsSystem -------------------------------------------
def test_buff_attack_passive_raises_effective_attack():
    combat, stats = _combat([_skill(id="buff", type="passive", effect="buff_attack", scaling=2.0, qi_cost=0)])
    player = _player(attack=100, skills=["buff"])
    assert stats.effective_stats(player)["attack"] == 200


def test_crit_chance_passive():
    _, stats = _combat([_skill(id="c", type="passive", effect="crit_chance", scaling=1.3, qi_cost=0)])
    player = _player(skills=["c"])
    assert abs(stats.crit_chance(player) - 0.13) < 1e-9


def test_qi_cost_reduction_passive():
    _, stats = _combat([_skill(id="q", type="passive", effect="qi_cost_reduction", scaling=0.8, qi_cost=0)])
    player = _player(skills=["q"])
    assert stats.effective_qi_cost(_skill(qi_cost=10), player) == 8


def test_regen_passive():
    _, stats = _combat(
        [
            _skill(id="hr", type="passive", effect="hp_regen", scaling=6, qi_cost=0),
            _skill(id="qr", type="passive", effect="qi_regen", scaling=4, qi_cost=0),
        ]
    )
    player = _player(skills=["hr", "qr"])
    assert stats.regen(player) == (6, 4)


# -- spar vs duel stakes -------------------------------------------------
def test_spar_ends_with_spar_won_and_no_loot_when_enemy_yields():
    combat, _ = _combat()
    player, enemy = _player(attack=1000), _enemy(attack=1, hp=10)

    result = combat.attack(player, enemy, spar=True)

    assert result["event"] == "COMBAT_END"
    assert result["outcome"] == "SPAR_WON"
    assert "loot_table" not in result
    assert player.exp == 0


def test_spar_ends_with_spar_lost_and_no_defeat_when_player_drops_low():
    combat, _ = _combat()
    player = _player(attack=1, hp=10, max_hp=100)
    enemy = _enemy(attack=1000, hp=1000)

    result = combat.attack(player, enemy, spar=True)

    assert result["event"] == "COMBAT_END"
    assert result["outcome"] == "SPAR_LOST"


def test_duel_attack_returns_victory_with_loot_and_exp():
    combat, _ = _combat()
    player, enemy = _player(attack=1000), _enemy(attack=1, hp=10)
    enemy.exp_reward = 5
    enemy.loot_table = [{"item_id": "healing_pill", "chance": 1.0, "count": 1}]

    result = combat.attack(player, enemy)

    assert result["outcome"] == "VICTORY"
    assert result["loot_table"] == enemy.loot_table
    assert player.exp == 5


# -- CB.2 statuses: durations, stacking rules, and the labelled rows ---------
def test_status_view_publishes_label_icon_duration_and_rule():
    _, enemy = _player(), _enemy()
    CombatSystem(RNG(0))._apply_status(enemy, "stun", 2, 0.0)

    assert status_views(enemy.statuses) == [
        {
            "id": "stun",
            "label": "Stunned",
            "icon": "stun",
            "stacking": "refresh",
            "harmful": True,
            "turns": 2,
            "magnitude": 0.0,
            "stacks": 1,
        }
    ]


def test_status_views_put_harmful_effects_first():
    _, target = _player(), _enemy()
    combat = CombatSystem(RNG(0))
    combat._apply_status(target, "counter", 3, 10.0)
    combat._apply_status(target, "dot_damage", 3, 5.0)

    assert [row["id"] for row in status_views(target.statuses)] == ["dot_damage", "counter"]


def test_reapplied_stun_refreshes_instead_of_stun_locking():
    combat, enemy = CombatSystem(RNG(0)), _enemy()
    combat._apply_status(enemy, "stun", 2, 0.0)
    combat._apply_status(enemy, "stun", 1, 0.0)

    # The longest duration wins; durations never add into a chain of skipped turns.
    assert enemy.statuses["stun"]["turns"] == 2
    assert enemy.statuses["stun"]["stacks"] == 2


def test_reapplied_debuff_keeps_the_strongest_cut():
    combat, enemy = CombatSystem(RNG(0)), _enemy()
    combat._apply_status(enemy, "debuff_attack", 3, 2.0)
    combat._apply_status(enemy, "debuff_attack", 3, 4.0)

    assert enemy.statuses["debuff_attack"]["magnitude"] == 4.0


def test_reapplied_poison_accumulates_up_to_the_stack_cap():
    combat, enemy = CombatSystem(RNG(0)), _enemy()
    for _ in range(STATUS_MAX_STACKS + 3):
        combat._apply_status(enemy, "dot_damage", 3, 5.0)

    # Stacking adds ticks, capped at STATUS_MAX_STACKS times the strongest dose.
    assert enemy.statuses["dot_damage"]["magnitude"] == 5.0 * STATUS_MAX_STACKS
    assert enemy.statuses["dot_damage"]["stacks"] == STATUS_MAX_STACKS


def test_turn_payload_carries_the_round_clock_and_labelled_statuses():
    combat = CombatSystem(RNG(0))
    player, enemy = _player(attack=40), _enemy(hp=1_000_000, attack=1)
    combat._apply_status(player, "counter", 3, 10.0)
    combat._apply_status(enemy, "dot_damage", 3, 5.0)

    result = combat.attack(player, enemy)

    assert result["round"] == 1
    assert [row["id"] for row in result["statuses"]] == ["counter"]
    assert [row["id"] for row in result["enemy_statuses"]] == ["dot_damage"]
    assert result["enemy_statuses"][0]["turns"] == 2  # the dot ticked once this round
    assert result["player_shield"] == 0


# -- CB.5 fight-length budget -----------------------------------------------
def _duel(seeds=range(30), player_stats=(40, 8, 200), foe_stats=(40, 8, 200)):
    """Play plain-attack duels and return ``(rounds, outcome)`` per seed."""
    p_attack, p_defense, p_hp = player_stats
    f_attack, f_defense, f_hp = foe_stats
    played = []
    for seed in seeds:
        combat = CombatSystem(RNG(seed))
        player = _player(attack=p_attack, defense=p_defense, hp=p_hp, max_hp=p_hp)
        enemy = _enemy(attack=f_attack, defense=f_defense, hp=f_hp)
        for round_number in range(1, MAX_FIGHT_ROUNDS + 1):
            result = combat.attack(player, enemy)
            if result["event"] == "COMBAT_END":
                played.append((round_number, result["outcome"]))
                break
    return played


def test_an_even_matchup_lands_inside_the_four_to_eight_round_budget():
    played = _duel()
    rounds = [rounds for rounds, _ in played]

    assert rounds, "the even duel should always resolve"
    assert 4 <= statistics.median(rounds) <= 8
    assert max(rounds) <= 8
    assert {outcome for _, outcome in played} == {"VICTORY"}


def test_a_grinding_fight_escalates_instead_of_stalling():
    combat = CombatSystem(RNG(0))
    assert combat._fatigue_scale() == 1.0

    combat._rounds = STALL_ROUNDS + 4
    assert combat._fatigue_scale() == pytest.approx(1.0 + 4 * FATIGUE_PER_ROUND)


def test_fatigue_shows_up_in_the_damage_breakdown_once_it_bites():
    combat = CombatSystem(RNG(0))
    player, enemy = _player(attack=40), _enemy(hp=1_000_000, attack=1)
    combat._rounds = STALL_ROUNDS + 2

    result = combat.attack(player, enemy)

    assert result["turn_events"][0]["breakdown"]["fatigue_scale"] > 1.0


def test_a_fight_that_outlives_the_cap_ends_in_a_legible_stalemate():
    combat = CombatSystem(RNG(0))
    player = _player(attack=40, defense=8, hp=100_000, max_hp=100_000)
    enemy = _enemy(attack=1, defense=8, hp=100_000)
    result = combat.attack(player, enemy)
    for _ in range(MAX_FIGHT_ROUNDS * 2):
        if result["event"] == "COMBAT_END":
            break
        result = combat.attack(player, enemy)

    assert result["event"] == "COMBAT_END"
    assert result["outcome"] == "STALEMATE"
    assert result["rounds"] == MAX_FIGHT_ROUNDS
    assert any(event.get("action") == "STALEMATE" for event in result["turn_events"])
    assert player.exp == 0  # neither side was beaten: no spoils


# -- CB.7 retreat -----------------------------------------------------------
def test_flee_odds_rise_when_the_run_is_on_the_line():
    combat = CombatSystem(RNG(0))
    enemy = _enemy(attack=40)
    healthy = _player(hp=200, max_hp=200)
    wounded = _player(hp=60, max_hp=200)

    assert combat.flee_chance(healthy, enemy) == FLEE_BASE_CHANCE
    assert combat.flee_chance(wounded, enemy) == pytest.approx(FLEE_BASE_CHANCE + FLEE_WOUNDED_BONUS)


def test_every_round_publishes_the_flee_odds():
    combat = CombatSystem(RNG(0))
    player, enemy = _player(attack=40, hp=200, max_hp=200), _enemy(hp=1_000_000, attack=1)

    result = combat.attack(player, enemy)

    assert result["flee"] == {"chance": FLEE_BASE_CHANCE, "available": True}


def test_a_failed_flee_reports_the_odds_and_costs_a_strike():
    combat = CombatSystem(RNG(0))
    player, enemy = _player(hp=200, max_hp=200, attack=40), _enemy(attack=40, hp=1_000_000)

    result = combat.flee(player, enemy)

    assert result.get("outcome") != "FLED" or result["flee_chance"] == FLEE_BASE_CHANCE
    if result["event"] == "COMBAT_TURN":
        assert result["flee"]["chance"] == FLEE_BASE_CHANCE


def test_fleeing_at_low_hp_saves_the_run_at_least_four_times_in_five():
    survived = 0
    trials = 200
    for seed in range(trials):
        combat = CombatSystem(RNG(seed))
        player = _player(attack=40, defense=8, hp=200, max_hp=200)
        enemy = _enemy(attack=40, defense=8, hp=200)
        player.hp = 60  # 30% of max: the retreat-or-die band
        for _ in range(20):
            result = combat.flee(player, enemy)
            if result.get("outcome") == "FLED":
                survived += 1
                break
            if not player.is_alive():
                break

    assert survived / trials >= 0.8


# -- D.4 insight ledger -----------------------------------------------------
def test_insight_view_names_every_source_and_the_drip_rate():
    gated = _skill(id="gate", insight_required=4)
    combat = CombatSystem(RNG(0), skills={"gate": gated})
    player = _player(skills=["gate"])
    player.comprehension = 60
    player.insight = 1

    view = combat.insight_view(player)

    assert view["drip_per_round"] == 6  # comprehension // the drip divisor
    assert {source["id"] for source in view["sources"]} == {
        "comprehension", "exchange", "crit", "counter"
    }
    assert view["spend_targets"] == [
        {"skill_id": "gate", "name": "X", "required": 4, "ready": False}
    ]
    assert view["next_spend"] == 4


def test_insight_view_marks_a_gated_technique_ready_and_clears_the_shortfall():
    gated = _skill(id="gate", insight_required=3)
    combat = CombatSystem(RNG(0), skills={"gate": gated})
    player = _player(skills=["gate"])
    player.insight = 3

    view = combat.insight_view(player)

    assert view["spend_targets"][0]["ready"] is True
    assert view["next_spend"] is None


def test_unlearned_gates_are_not_listed_as_spend_targets():
    combat = CombatSystem(RNG(0), skills={"gate": _skill(id="gate", insight_required=4)})
    player = _player()  # the technique exists, but this cultivator never learned it

    view = combat.insight_view(player)

    assert view["spend_targets"] == []
    assert view["next_spend"] is None


def test_the_insight_drip_reaches_the_cheapest_gate_within_one_even_fight():
    gated = _skill(id="gate", insight_required=5)
    combat = CombatSystem(RNG(0), skills={"gate": gated})
    player = _player(attack=40, defense=8, hp=200, max_hp=200, skills=["gate"])
    player.comprehension = 30
    enemy = _enemy(attack=40, defense=8, hp=1_000_000)

    for _ in range(8):
        combat.attack(player, enemy)

    # 3/round from comprehension plus 1 per landed hit: a 5-point gate is paced
    # inside the fight budget, so gated techniques are reachable, not theoretical.
    assert player.insight >= 5
    assert combat.insight_view(player)["spend_targets"][0]["ready"] is True
