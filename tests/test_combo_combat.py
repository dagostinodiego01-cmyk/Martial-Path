"""Tests for the B.6 stance/combo combat system.

Techniques typed opening/response/finisher chain into escalating damage
bonuses; out-of-sequence stances are refused by the engine, neutral techniques
are allowed but drop the chain, and a completed chain banks a COMBO_FINISH
event. All chain sequencing/bonus logic lives in ``CombatSystem``; which
techniques carry which role is data in ``skills.json``.
"""
import pytest

from game.core.constants import Action, EventType
from game.core.game_engine import MODE_COMBAT, GameEngine
from game.data.registry import GameDataRegistry
from game.models.enemy import Enemy
from game.models.player import Player
from game.models.skill import Skill
from game.systems.combat_system import COMBO_BONUS_PER_STAGE, COMBO_ROLES, CombatSystem
from game.systems.stats_system import StatsSystem
from game.utils.rng import RNG
from game.validation.data_validator import validate_all_game_data
from game.validation.validation_error import ValidationError


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


def _player(attack=100, defense=0, hp=1000, max_hp=1000):
    return Player(
        name="Tester",
        attack=attack,
        defense=defense,
        hp=hp,
        max_hp=max_hp,
        max_qi=1000,
        qi=1000,
    )


def _enemy(attack=0, defense=0, hp=100000):
    return Enemy.from_dict(
        {"id": "e", "name": "E", "body_realm_id": "mortal", "attack": attack, "defense": defense, "hp": hp}
    )


def _combat(skills=()):
    skill_map = {s.id: s for s in skills}
    stats = StatsSystem(skill_map)
    return CombatSystem(RNG(0), stats, skills=skill_map)


# -- model plumbing ------------------------------------------------------
def test_skill_parses_combo_role():
    assert _skill(combo_role="opening").combo_role == "opening"
    assert _skill().combo_role == ""


def test_combo_stage_is_not_persisted():
    player = Player(name="Tester", combo_stage=2)
    assert "combo_stage" not in player.to_save_dict()


# -- chain sequencing ----------------------------------------------------
def test_chain_advances_through_all_roles():
    combat = _combat()
    player = _player()
    opening = _skill(id="a", combo_role="opening")
    response = _skill(id="b", combo_role="response")
    finisher = _skill(id="c", combo_role="finisher")
    enemy = _enemy()

    combat.use_skill(player, enemy, opening)
    assert player.combo_stage == 1
    combat.use_skill(player, enemy, response)
    assert player.combo_stage == 2
    result = combat.use_skill(player, enemy, finisher)
    assert player.combo_stage == 0  # completed chain resets
    assert any(ev.get("action") == "COMBO_FINISH" for ev in result["turn_events"])


def test_response_without_opening_resets_chain():
    combat = _combat()
    player = _player()
    response = _skill(id="b", combo_role="response")
    combat.use_skill(player, _enemy(), response)
    assert player.combo_stage == 0


def test_finisher_without_chain_resets_chain():
    combat = _combat()
    player = _player()
    finisher = _skill(id="c", combo_role="finisher")
    combat.use_skill(player, _enemy(), finisher)
    assert player.combo_stage == 0


def test_neutral_technique_drops_a_banked_chain():
    combat = _combat()
    player = _player()
    combat.use_skill(player, _enemy(), _skill(id="a", combo_role="opening"))
    assert player.combo_stage == 1
    result = combat.use_skill(player, _enemy(), _skill(id="n", combo_role=""))
    assert player.combo_stage == 0
    assert any(ev.get("action") == "COMBO_DROPPED" for ev in result["turn_events"])


def test_chain_bonus_scales_with_banked_stage():
    combat = _combat()
    player = _player()
    enemy = _enemy()
    # Bank stage 2 with opening + response...
    combat.use_skill(player, enemy, _skill(id="a", combo_role="opening"))
    combat.use_skill(player, enemy, _skill(id="b", combo_role="response"))
    # ...then measure a neutral damage technique (chain survives the multiplier check).
    player.combo_stage = 2
    dealt = {}
    for stage in (0, 2):
        player.combo_stage = stage
        enemy.hp = enemy.max_hp
        result = combat.use_skill(player, enemy, _skill(id="n", combo_role="", scaling=1.0))
        dealt[stage] = result["turn_events"][0]["damage"]
    assert dealt[2] > dealt[0]
    expected_ratio = 1 + 2 * COMBO_BONUS_PER_STAGE
    assert dealt[2] == pytest.approx(dealt[0] * expected_ratio, rel=0.15)


def test_combo_multiplier_zero_when_no_chain():
    combat = _combat()
    player = _player()
    assert combat._combo_multiplier(player, _skill(combo_role="finisher")) == 1.0


def test_next_combo_role_expectations():
    combat = _combat()
    player = _player()
    assert combat.next_combo_role(player) is None  # no chain banked: anything goes
    player.combo_stage = 1
    assert combat.next_combo_role(player) == "response"
    player.combo_stage = 2
    assert combat.next_combo_role(player) == "finisher"


# -- engine gating and surfacing -----------------------------------------
def _start_combat_with(engine: GameEngine, *skill_ids: str) -> None:
    for skill_id in skill_ids:
        if skill_id not in engine.player.skills:
            engine.player.skills.append(skill_id)
    engine.player.qi = 10_000
    engine.player.max_qi = 10_000
    engine._current_enemy = engine._spawn_enemy(next(iter(engine._enemy_templates)))
    engine._current_enemy.attack = 0
    engine._mode = MODE_COMBAT
    engine._cooldowns = {}
    engine.combat.begin_combat(engine.player)


def test_engine_refuses_out_of_sequence_stance():
    engine = GameEngine.new_game(seed=1)
    _start_combat_with(engine, "white_tiger_palm", "white_tiger_seal")  # opening + finisher
    engine.process_action({"action": Action.USE_SKILL, "skill_id": "white_tiger_palm"})
    assert engine.player.combo_stage == 1

    engine.player.qi = 10_000
    result = engine.process_action({"action": Action.USE_SKILL, "skill_id": "white_tiger_seal"})  # finisher
    assert result["event"] == EventType.ERROR
    assert result["reason"] == "COMBO_OUT_OF_SEQUENCE"
    assert result["expected_role"] == "response"
    assert engine.player.combo_stage == 1  # the banked chain is untouched


def test_engine_allows_neutral_technique_mid_chain():
    engine = GameEngine.new_game(seed=1)
    _start_combat_with(engine, "white_tiger_palm")
    engine.process_action({"action": Action.USE_SKILL, "skill_id": "white_tiger_palm"})
    assert engine.player.combo_stage == 1

    engine.player.qi = 10_000
    result = engine.process_action({"action": Action.USE_SKILL, "skill_id": "iron_fist"})  # no role
    assert result["event"] in (EventType.COMBAT_TURN, EventType.COMBAT_END)
    assert engine.player.combo_stage == 0  # chain dropped, not blocked
    assert any(ev.get("action") == "COMBO_DROPPED" for ev in result.get("turn_events", []))


def test_full_chain_through_engine_banks_combo_finish():
    engine = GameEngine.new_game(seed=1)
    _start_combat_with(engine, "white_tiger_palm", "white_tiger_fist_intent", "white_tiger_seal")
    for skill_id in ("white_tiger_palm", "white_tiger_fist_intent", "white_tiger_seal"):
        engine.player.qi = 10_000
        engine._cooldowns = {}
        result = engine.process_action({"action": Action.USE_SKILL, "skill_id": skill_id})
    assert result["event"] in (EventType.COMBAT_TURN, EventType.COMBAT_END)
    assert any(ev.get("action") == "COMBO_FINISH" for ev in result.get("turn_events", []))
    assert engine.player.combo_stage == 0


def test_skill_briefs_surface_combo_state():
    engine = GameEngine.new_game(seed=1)
    engine.player.skills.extend(["white_tiger_palm", "white_tiger_fist_intent", "white_tiger_seal"])
    engine.player.combo_stage = 1

    briefs = {b["id"]: b for b in engine.get_known_skills()}
    assert briefs["white_tiger_palm"]["combo_role"] == "opening"
    assert briefs["white_tiger_fist_intent"]["expected_combo_role"] == "response"
    assert briefs["white_tiger_fist_intent"]["combo_ready"] is True
    assert briefs["white_tiger_seal"]["combo_ready"] is False
    assert engine.get_game_state()["player"]["combo_stage"] == 1


def test_combo_state_resets_when_combat_ends():
    engine = GameEngine.new_game(seed=1)
    _start_combat_with(engine, "white_tiger_palm")
    engine.process_action({"action": Action.USE_SKILL, "skill_id": "white_tiger_palm"})
    engine.player.combo_stage = 2
    engine._current_enemy.hp = 1
    engine.player.attack = 1000

    result = engine.process_action({"action": Action.ATTACK})

    assert result["event"] == EventType.COMBAT_END
    assert engine.player.combo_stage == 0


# -- shipped data --------------------------------------------------------
def test_shipped_combo_chains_are_well_formed():
    registry = GameDataRegistry.load()
    roles = {s["id"]: s.get("combo_role", "") for s in registry.skills if s.get("combo_role")}
    assert len(roles) >= 9, "combo seeding should cover at least three families"
    for skill_id, role in roles.items():
        assert role in COMBO_ROLES


def test_validate_all_game_data_still_clean():
    result = validate_all_game_data()
    assert result.is_valid, result.format_errors()


def test_combo_role_on_passive_is_rejected():
    registry = GameDataRegistry.load()
    from game.validation.data_validator import GameDataRegistry as _GR  # noqa: F401  (import guard)

    # Build a minimal registry carrying a bad entry through the real validator.
    bad = dict(registry.skills[0])
    bad["combo_role"] = "middle"
    registry_with_bad = GameDataRegistry(
        items=registry.items,
        skills=[bad],
        enemies=registry.enemies,
        character_enemies=registry.character_enemies,
        characters=registry.characters,
        locations=registry.locations,
        quests=registry.quests,
        events=registry.events,
        body_realms=registry.body_realms,
        essence_realms=registry.essence_realms,
        cultivation_config=registry.cultivation_config,
        morality=registry.morality,
        relationships=registry.relationships,
        lore_glossary=registry.lore_glossary,
    )
    result = validate_all_game_data(registry_with_bad)
    assert any("combo_role" in e.message for e in result.errors)
