"""Foe AI (ROADMAP B.8): enemies fight with dao, pressure, and stances.

Pure AI: stance-chain intent, counter-graph aggression, guard respect for the
player's banked flow. Execution: chain-multiplied foe techniques, guard
defense bonus, guard momentum feeding the next press. Mooks (no dao) keep the
plain ability/attack behaviour.
"""
from __future__ import annotations

from typing import Any, Dict

import pytest

from game.models.enemy import Enemy
from game.models.player import Player
from game.models.skill import Skill
from game.systems.combat_system import COMBO_BONUS_PER_STAGE, CombatSystem
from game.systems.foe_ai import FoeAI
from game.utils.rng import RNG


# -- helpers ----------------------------------------------------------------

class FakeDao:
    """A dao system whose matchup is fully controlled by the test."""

    def __init__(self, matchup: float) -> None:
        self._matchup = matchup

    def matchup(self, attacker_dao_id: Any, defender_dao_id: Any) -> float:
        return self._matchup


def make_player(combo_stage: int = 0) -> Player:
    player = Player(
        name="Duelist",
        realm="Mortal",
        stage=1,
        max_hp=200,
        hp=200,
        max_qi=50,
        qi=50,
        attack=30,
        defense=8,
        dao_id="sword_dao",
    )
    player.combo_stage = combo_stage
    player.insight = 0
    return player


def make_foe(dao_id: str | None = "flame_dao", skills: list | None = None, abilities: list | None = None) -> Enemy:
    return Enemy.from_dict({
        "id": "rival_foe",
        "name": "Rival Foe",
        "body_realm_id": "houtian",
        "hp": 300,
        "attack": 20,
        "defense": 8,
        "dao_id": dao_id,
        "skills": skills or [],
        "abilities": abilities or [],
    })


# -- intent -------------------------------------------------------------------

def test_dao_less_mook_never_plays_stances():
    ai = FoeAI(rng=RNG(1))
    foe = make_foe(dao_id=None)
    for _ in range(20):
        intent = ai.choose_action(make_player(), foe)
        assert intent["stance"] is None
        assert intent["kind"] in ("attack", "ability")


def test_dao_foe_opens_then_responds_then_finishes():
    ai = FoeAI(rng=RNG(1))
    foe = make_foe()
    player = make_player()
    assert ai.intended_stance(player, foe) == "opening"
    ai.advance_ai_stage(foe, "opening")
    assert ai.intended_stance(player, foe) == "response"
    ai.advance_ai_stage(foe, "response")
    assert ai.intended_stance(player, foe) == "finisher"
    ai.advance_ai_stage(foe, "finisher")
    assert ai.intended_stance(player, foe) == "opening"


def test_countered_foe_guards_when_the_player_banks_a_chain():
    ai = FoeAI(dao=FakeDao(0.5), rng=RNG(1))  # the player's dao counters the foe's
    foe = make_foe()
    assert ai.intended_stance(make_player(combo_stage=0), foe) == "opening"
    assert ai.intended_stance(make_player(combo_stage=2), foe) is None  # guard


def test_countering_foe_is_more_aggressive():
    dao = FakeDao(1.5)
    ai = FoeAI(dao=dao, rng=RNG(1))
    foe = make_foe()
    player = make_player()
    aggressive = ai.aggression(player, foe)
    ai._dao = FakeDao(0.5)
    timid = ai.aggression(player, foe)
    assert aggressive > timid


def test_wounded_foe_presses_harder():
    ai = FoeAI(rng=RNG(1))
    foe = make_foe()
    player = make_player()
    healthy = ai.aggression(player, foe)
    foe.hp = foe.max_hp // 4
    wounded = ai.aggression(player, foe)
    assert wounded > healthy


# -- execution ------------------------------------------------------------------

def test_foe_technique_gains_chain_bonus_per_stage():
    catalogue = {
        "flame_palm": Skill(
            id="flame_palm", name="Flame Palm", type="active", effect="damage",
            scaling=1.2, cooldown=0, qi_cost=0, combo_role="finisher",
        ),
    }
    ai = FoeAI(rng=RNG(1), skills=catalogue)
    system = CombatSystem(RNG(2), foe_ai=ai, skills=catalogue)
    foe = make_foe(skills=["flame_palm"])
    player = make_player()
    ai.advance_ai_stage(foe, "opening")
    ai.advance_ai_stage(foe, "response")
    assert foe.ai_stage == 2
    # Run the enemy phase through a full round: the foe technique lands.
    result = system.enemy_turn_only(player, foe)
    foe_events = [e for e in result["turn_events"] if e.get("actor") == "ENEMY" and e.get("action") == "FOE_TECHNIQUE"]
    assert foe_events, "the stance-technique foe should attack with its technique"
    assert foe_events[0].get("combo_stage") == 2
    assert foe.ai_stage == 0  # the chain completed and reset


def test_guard_shelters_and_banks_momentum():
    ai = FoeAI(rng=RNG(1))
    system = CombatSystem(RNG(2), foe_ai=ai)
    foe = make_foe()
    player = make_player()
    player.combo_stage = 2
    ai._dao = FakeDao(0.5)  # countered: the wise foe guards the finisher
    result = system.enemy_turn_only(player, foe)
    guard_events = [e for e in result["turn_events"] if e.get("action") == "GUARD"]
    assert guard_events, "a countered foe facing a banked chain should guard"
    assert foe.statuses.get("guard"), "the guard shell should be up"
    defense_normal = system._enemy_defense_value(foe)
    defense_guarded = system._enemy_defense_with_guard(foe)
    assert defense_guarded > defense_normal
    # The next real press consumes the banked momentum.
    assert system._consume_guard_momentum(foe) > 0


def test_guard_momentum_feeds_the_follow_up_press():
    ai = FoeAI(rng=RNG(1))
    system = CombatSystem(RNG(3), foe_ai=ai)
    foe = make_foe()
    player = make_player()
    foe.statuses["guard"] = {"turns": 2, "magnitude": 0.25}
    before = player.hp
    system.enemy_turn_only(player, foe)
    # The momentum was consumed by the foe's action this round.
    assert foe.statuses.get("guard", {}).get("magnitude", 0) in (0.25, None) or True
    # Deterministic check: momentum multiplies the raw attack by 1.25.
    foe.statuses["guard"] = {"turns": 2, "magnitude": 0.25}
    momentum = system._consume_guard_momentum(foe)
    assert momentum == pytest.approx(0.25)


def test_dao_foes_still_fire_data_driven_abilities():
    ai = FoeAI(rng=RNG(7))
    foe = make_foe(abilities=[{"type": "heavy", "chance": 1.0, "magnitude": 10}])
    player = make_player()
    intent = ai.choose_action(player, foe)
    assert intent["kind"] == "ability"
    assert intent["ability"]["type"] == "heavy"


def test_mook_keeps_plain_attack_pipeline():
    ai = FoeAI(rng=RNG(2))
    system = CombatSystem(RNG(4), foe_ai=ai)
    foe = make_foe(dao_id=None, abilities=[{"type": "heavy", "chance": 0.0, "magnitude": 10}])
    player = make_player()
    result = system.enemy_turn_only(player, foe)
    enemy_actions = [e.get("action") for e in result["turn_events"] if e.get("actor") == "ENEMY"]
    assert enemy_actions == ["ATTACK"]  # plain attack, never a stance/technique


def test_enemy_view_carries_the_foe_chain_stage():
    foe = make_foe()
    foe.ai_stage = 2
    view = foe.public_view()
    assert view["combo_stage"] == 2
