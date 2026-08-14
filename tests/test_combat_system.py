"""Tests for combat skill-effect resolution and passive stat derivation."""
from game.models.enemy import Enemy
from game.models.player import Player
from game.models.skill import Skill
from game.systems.combat_system import CombatSystem
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
