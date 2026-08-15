"""Tests for the B.5 intent/insight combat resource.

Insight builds from comprehension (a per-round drip) and successful exchanges
(landing hits, crits, counters), and gates techniques with ``insight_required``.
"""
import pytest

from game.core.constants import Action, EventType
from game.core.game_engine import MODE_COMBAT, GameEngine
from game.data.registry import GameDataRegistry
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
        "qi_cost": 0,
    }
    base.update(overrides)
    return Skill.from_dict(base)


def _player(comprehension=10, attack=100, defense=0, hp=1000, max_hp=1000):
    return Player(
        name="Tester",
        attack=attack,
        defense=defense,
        hp=hp,
        max_hp=max_hp,
        max_qi=1000,
        qi=1000,
        comprehension=comprehension,
    )


def _enemy(attack=0, defense=0, hp=1000):
    return Enemy.from_dict(
        {"id": "e", "name": "E", "body_realm_id": "mortal", "attack": attack, "defense": defense, "hp": hp}
    )


def _combat(skills=()):
    skill_map = {s.id: s for s in skills}
    stats = StatsSystem(skill_map)
    return CombatSystem(RNG(0), stats), stats


# -- model plumbing ------------------------------------------------------
def test_skill_parses_insight_required():
    assert _skill(insight_required=3).insight_required == 3
    assert _skill().insight_required == 0


def test_insight_is_not_persisted():
    player = Player(name="Tester", insight=99)
    assert "insight" not in player.to_save_dict()


# -- resource generation -------------------------------------------------
def test_begin_combat_resets_insight():
    combat, _ = _combat()
    player = _player()
    player.insight = 50
    assert combat.begin_combat(player) == 0
    assert player.insight == 0


def test_comprehension_grants_per_round_drip():
    combat, _ = _combat()
    player = _player(comprehension=27)
    assert combat._gain_comprehension_insight(player) == 2  # 27 // 10
    assert player.insight == 2


def test_successful_hit_grants_insight_and_crit_adds_more():
    combat, _ = _combat()
    player = _player()
    assert combat._gain_exchange_insight(player, dealt=1, is_crit=False) == 1
    assert combat._gain_exchange_insight(player, dealt=1, is_crit=True) == 2
    assert player.insight == 3
    # A miss (fully absorbed) grants nothing.
    assert combat._gain_exchange_insight(player, dealt=0, is_crit=False) == 0
    assert player.insight == 3


def test_attack_builds_insight_and_emits_insight_events():
    combat, _ = _combat()
    player = _player(comprehension=10)
    enemy = _enemy()

    result = combat.attack(player, enemy)

    assert player.insight >= 2  # 1 hit + 1 comprehension drip (10 // 10)
    actions = [e.get("action") for e in result["turn_events"]]
    assert "INSIGHT" in actions
    assert result["insight"] == player.insight


def test_counter_wound_grants_insight():
    combat, _ = _combat()
    player = _player()
    enemy = _enemy(attack=100)
    player.statuses["counter"] = {"turns": 3, "magnitude": 10.0}
    player.insight = 0

    event = combat._enemy_attack(player, enemy)

    assert event["counter_damage"] > 0
    assert player.insight == 1
    assert event["insight_gain"] == 1
    assert event["insight_total"] == 1


# -- engine gating -------------------------------------------------------
def _start_combat_with(engine: GameEngine, skill_id: str) -> None:
    engine.player.skills.append(skill_id)
    engine.player.qi = 10_000
    engine.player.max_qi = 10_000
    engine._current_enemy = engine._spawn_enemy(next(iter(engine._enemy_templates)))
    engine._current_enemy.attack = 0
    engine._mode = MODE_COMBAT
    engine._cooldowns = {}
    engine.combat.begin_combat(engine.player)


def test_intent_skill_rejected_without_insight():
    engine = GameEngine.new_game(seed=1)
    _start_combat_with(engine, "iron_sword_intent")  # insight_required == 2
    engine.player.insight = 0

    result = engine.process_action({"action": Action.USE_SKILL, "skill_id": "iron_sword_intent"})

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "NOT_ENOUGH_INSIGHT"
    assert result["required"] == 2


def test_intent_skill_fires_once_insight_is_met():
    engine = GameEngine.new_game(seed=1)
    _start_combat_with(engine, "iron_sword_intent")
    engine.player.insight = 2

    result = engine.process_action({"action": Action.USE_SKILL, "skill_id": "iron_sword_intent"})

    assert result["event"] in (EventType.COMBAT_TURN, EventType.COMBAT_END)
    assert result.get("reason") != "NOT_ENOUGH_INSIGHT"


def test_insight_resets_when_combat_ends():
    engine = GameEngine.new_game(seed=1)
    _start_combat_with(engine, "iron_fist")
    engine.player.insight = 7
    engine._current_enemy.hp = 1
    engine.player.attack = 1000

    result = engine.process_action({"action": Action.ATTACK})

    assert result["event"] == EventType.COMBAT_END
    assert engine.player.insight == 0


def test_skill_briefs_and_state_surface_insight():
    engine = GameEngine.new_game(seed=1)
    engine.player.skills.append("iron_sword_intent")
    engine.player.insight = 1

    brief = next(b for b in engine.get_known_skills() if b["id"] == "iron_sword_intent")
    assert brief["insight_required"] == 2
    assert brief["insight_met"] is False
    assert engine.get_game_state()["player"]["insight"] == 1


# -- data consistency ----------------------------------------------------
def test_all_intent_skills_require_insight_and_are_active():
    registry = GameDataRegistry.load()
    intents = [s for s in registry.skills if s["id"].endswith("_intent")]
    assert len(intents) == 20
    for skill in intents:
        assert skill["type"] == "active"
        assert skill.get("insight_required", 0) > 0
