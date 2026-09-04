"""Dao debates and spirit-oath duels (ROADMAP B.7).

Pure system: stance triangle (assert > yield/absorb rules, probe > transcend,
transcend > assert), insight-based sway, dao matchup scaling, probe exposure.
Engine: debate start/route/end against named characters, oath stakes (win
1.5x, loss exp+gold, breach forfeit), and debate state isolation.
"""
from __future__ import annotations

import pytest

from game.core.game_engine import GameEngine
from game.models.enemy import Enemy
from game.models.player import Player
from game.systems.debate_system import DEBATE_MAX_CONVICTION, DebateSystem
from game.utils.rng import RNG


# -- helpers ----------------------------------------------------------------

def make_player(insight: int = 4, comprehension: int = 8) -> Player:
    player = Player(
        name="Debater",
        realm="Mortal",
        stage=1,
        max_hp=100,
        hp=100,
        max_qi=50,
        qi=50,
        attack=15,
        defense=5,
        comprehension=comprehension,
        dao_id="sword_dao",
    )
    player.insight = insight
    return player


def make_foe(dao_id: str | None = "flame_dao", insight: int = 4) -> Enemy:
    foe = Enemy.from_dict({
        "id": "rival_duel",
        "name": "Rival",
        "body_realm_id": "houtian",
        "hp": 80,
        "attack": 20,
        "defense": 8,
        "dao_id": dao_id,
        "skills": ["s1", "s2", "s3"],
    })
    foe.insight = insight
    return foe


# -- pure: stances and sway ---------------------------------------------------

def test_stance_triangle_transcend_absorbs_assert():
    system = DebateSystem(rng=RNG(1))
    player, foe = make_player(), make_foe()
    state = DebateSystem.new_state(4, 4)
    system.round_resolve(player, foe, state, "assert", "transcend")
    assert state["foe_conviction"] == state.get("initial_foe_conviction", 20)  # absorbed
    assert state["player_conviction"] < state.get("initial_player_conviction", 20)  # transcend still presses


def test_exposure_breaks_transcend_absorption():
    system = DebateSystem(rng=RNG(1))
    player, foe = make_player(), make_foe()
    state = DebateSystem.new_state(4, 4)
    system.round_resolve(player, foe, state, "probe", "transcend")  # expose
    system.round_resolve(player, foe, state, "assert", "transcend")
    assert state["foe_conviction"] < 20  # the pin opened the way


def test_exposure_is_consumed_once():
    system = DebateSystem(rng=RNG(1))
    player, foe = make_player(), make_foe()
    state = DebateSystem.new_state(4, 4)
    system.round_resolve(player, foe, state, "probe", "transcend")  # expose
    assert state["foe_exposed"] == 1  # the pin is set during the probe round
    system.round_resolve(player, foe, state, "assert", "transcend")
    assert state["foe_exposed"] == 0  # and consumed by the next absorb attempt
    assert state["foe_conviction"] < 20  # the pin opened the way


def test_probe_loses_to_assert():
    system = DebateSystem(rng=RNG(1))
    player, foe = make_player(), make_foe()
    state = DebateSystem.new_state(4, 4)
    system.round_resolve(player, foe, state, "probe", "assert")
    assert state["foe_conviction"] == 20  # question beaten by declaration


def test_yield_halves_pressure():
    system = DebateSystem(rng=RNG(1))
    player = make_player(insight=6)
    foe = make_foe()
    state_one = DebateSystem.new_state()
    system.round_resolve(player, foe, state_one, "assert", "probe")
    state_two = DebateSystem.new_state()
    system.round_resolve(player, foe, state_two, "assert", "yield")
    assert state_two["foe_conviction"] > state_one["foe_conviction"]


def test_dao_matchup_scales_sway():
    system = DebateSystem(dao=type("D", (), {"matchup": staticmethod(lambda a, b: 2.0 if a == "sword_dao" else 1.0)})(), rng=RNG(1))
    player, foe = make_player(), make_foe()
    state = DebateSystem.new_state(4, 4)
    system.round_resolve(player, foe, state, "assert", "probe")
    # sword_dao vs flame_dao at 2.0x: 4 insight -> 4 sway doubled to 8.
    assert 20 - state["foe_conviction"] >= 8


def test_debate_reaches_an_outcome():
    system = DebateSystem(rng=RNG(1))
    player, foe = make_player(), make_foe(insight=1)
    state = DebateSystem.new_state()
    outcome = None
    for _ in range(30):
        system.round_resolve(player, foe, state, "assert", system.foe_stance(state))
        outcome = system.outcome(state)
        if outcome:
            break
    assert outcome in ("DEBATE_WON", "DEBATE_LOST", "DEBATE_STALEMATE")


# -- engine flow --------------------------------------------------------------

def _debate_candidate(engine: GameEngine) -> str | None:
    characters = engine.character_service
    for location_id in ("outer_forest", "azure_village", "sky_spill_continent_map", "misty_gorge", "lin_academy"):
        for brief in characters.get_available_characters(location_id, engine.player):
            if brief.get("unlocked") and characters.can_spar(brief["id"], engine.player).get("allowed"):
                return str(brief["id"])
    return None


def test_engine_starts_and_resolves_a_plain_debate():
    engine = GameEngine.new_game(seed=12345)
    cid = _debate_candidate(engine)
    assert cid, "a spar-capable character must exist in data"
    started = engine.process_action({"action": "DEBATE_CHARACTER", "character_id": cid})
    assert started["event"] == "DEBATE_STARTED"
    assert engine._mode == "debate"
    gold_before = engine.player.gold
    exp_before = engine.player.exp
    while True:
        result = engine.process_action({"action": "DEBATE_STANCE", "stance": "assert"})
        if result.get("event") == "DEBATE_END":
            break
        assert result.get("event") == "DEBATE_ROUND"
    assert result["outcome"] in ("DEBATE_WON", "DEBATE_LOST", "DEBATE_STALEMATE")
    assert "oath" not in result  # a plain debate carries no stakes
    assert engine.player.gold == gold_before and engine.player.exp == exp_before
    assert engine._mode == "explore"


def test_oath_duel_pays_out_on_a_win():
    engine = GameEngine.new_game(seed=12345)
    cid = _debate_candidate(engine)
    engine.player.gold = 100
    engine.player.exp = 200
    started = engine.process_action({"action": "OATH_DUEL_CHARACTER", "character_id": cid})
    assert started["event"] == "OATH_DUEL_STARTED"
    assert started["stakes"]["gold_wagered"] == 100
    while True:
        result = engine.process_action({"action": "DEBATE_STANCE", "stance": "assert"})
        if result.get("event") == "DEBATE_END":
            break
    if result["outcome"] == "DEBATE_WON":
        assert result["oath"]["resolved"] == "WON"
        assert result["oath"]["gold_won"] == 150  # 1.5x the sworn stake
        assert engine.player.gold == 250
    elif result["outcome"] == "DEBATE_LOST":
        assert result["oath"]["resolved"] == "LOST"
        assert result["oath"]["gold_lost"] == 100
        assert result["oath"]["exp_lost"] == 100  # half the banked exp


def test_walking_away_from_an_oath_duel_is_a_breach():
    engine = GameEngine.new_game(seed=12345)
    cid = _debate_candidate(engine)
    engine.player.gold = 80
    started = engine.process_action({"action": "OATH_DUEL_CHARACTER", "character_id": cid})
    assert started["event"] == "OATH_DUEL_STARTED"
    result = engine.process_action({"action": "WALK_AWAY"})
    assert result["event"] == "DEBATE_END"
    assert result["outcome"] == "DEBATE_ABANDONED"
    assert result["oath"]["resolved"] == "BREACH"
    # The breach takes the *larger* of the sworn wager or a fraction of
    # current gold: the whole sworn stake (80) is forfeit here.
    assert result["oath"]["gold_forfeit"] == 80
    assert engine.player.gold == 0
    assert engine._mode == "explore"


def test_walking_away_from_a_plain_debate_is_free():
    engine = GameEngine.new_game(seed=12345)
    cid = _debate_candidate(engine)
    engine.player.gold = 80
    engine.process_action({"action": "DEBATE_CHARACTER", "character_id": cid})
    result = engine.process_action({"action": "WALK_AWAY"})
    assert result["outcome"] == "DEBATE_ABANDONED"
    assert "oath" not in result
    assert engine.player.gold == 80


def test_debate_actions_rejected_outside_a_debate():
    engine = GameEngine.new_game(seed=12345)
    result = engine.process_action({"action": "DEBATE_STANCE", "stance": "assert"})
    assert result["event"] == "ERROR" and result["reason"] == "UNKNOWN_COMMAND"
    # A well-formed WALK_AWAY outside a debate is a no-op error, not a crash.
    result = engine.process_action({"action": "WALK_AWAY"})
    assert result["event"] == "ERROR" and result["reason"] == "NOT_IN_DEBATE"


def test_invalid_stance_is_refused_without_ending_the_debate():
    engine = GameEngine.new_game(seed=12345)
    cid = _debate_candidate(engine)
    engine.process_action({"action": "DEBATE_CHARACTER", "character_id": cid})
    result = engine.process_action({"action": "DEBATE_STANCE", "stance": "shout"})
    assert result["event"] == "ERROR" and result["reason"] == "INVALID_DEBATE_STANCE"
    assert engine._mode == "debate"
    # ...and the debate continues afterwards.
    ongoing = engine.process_action({"action": "DEBATE_STANCE", "stance": "yield"})
    assert ongoing.get("event") == "DEBATE_ROUND"


def test_debate_does_not_leak_insight_into_combat():
    engine = GameEngine.new_game(seed=12345)
    cid = _debate_candidate(engine)
    engine.process_action({"action": "DEBATE_CHARACTER", "character_id": cid})
    engine.process_action({"action": "WALK_AWAY"})
    assert engine.player.insight == 0  # the combat pool is untouched
    assert engine._active_debate_view() is None


def test_game_state_carries_the_active_debate():
    engine = GameEngine.new_game(seed=12345)
    cid = _debate_candidate(engine)
    engine.process_action({"action": "DEBATE_CHARACTER", "character_id": cid})
    state = engine.get_game_state()
    assert state["debate"] is not None
    assert state["debate"]["foe_name"]
    assert set(state["debate"]["stances"]) == {"assert", "probe", "transcend", "yield"}
    engine.process_action({"action": "WALK_AWAY"})
    assert engine.get_game_state()["debate"] is None


def test_oath_stakes_survive_no_mutation_until_resolution():
    engine = GameEngine.new_game(seed=12345)
    cid = _debate_candidate(engine)
    engine.player.gold = 50
    engine.process_action({"action": "OATH_DUEL_CHARACTER", "character_id": cid})
    assert engine.player.gold == 50  # nothing taken up front
    assert engine._oath_stakes == {"gold_wagered": 50, "exp_wagered": 0}
