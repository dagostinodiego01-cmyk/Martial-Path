"""Tests for technique (skill) learning rules."""
from game.core.constants import EventType
from game.models.player import Player
from game.models.skill import Skill
from game.systems.skill_system import SkillSystem


def _skills():
    return {
        "spirit_palm": Skill.from_dict(
            {"id": "spirit_palm", "name": "Spirit Palm", "type": "active", "qi_cost": 20, "cooldown": 3}
        ),
    }


def test_learn_skill_adds_to_player():
    system = SkillSystem(_skills())
    player = Player(name="Tester")

    result = system.learn_skill(player, "spirit_palm")

    assert result["event"] == EventType.SKILL_LEARNED
    assert result["skill_id"] == "spirit_palm"
    assert result["source"] == "manual"
    assert "spirit_palm" in player.skills


def test_learn_unknown_skill_is_rejected():
    system = SkillSystem(_skills())
    player = Player(name="Tester")

    result = system.learn_skill(player, "does_not_exist")

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "UNKNOWN_SKILL"
    assert player.skills == []


def test_learn_already_known_skill_is_rejected():
    system = SkillSystem(_skills())
    player = Player(name="Tester", skills=["spirit_palm"])

    result = system.learn_skill(player, "spirit_palm")

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "SKILL_ALREADY_KNOWN"
    assert player.skills == ["spirit_palm"]


def test_learning_comprehension_passive_raises_comprehension():
    skills = {
        "dao_heart_scripture": Skill.from_dict(
            {
                "id": "dao_heart_scripture",
                "name": "Dao Heart Scripture",
                "type": "passive",
                "effect": "comprehension_gain",
                "scaling": 26,
            }
        ),
    }
    system = SkillSystem(skills)
    player = Player(name="Tester")

    result = system.learn_skill(player, "dao_heart_scripture")

    assert result["event"] == EventType.SKILL_LEARNED
    assert player.comprehension == 36


def test_learning_lifespan_passive_extends_lifespan_bonus():
    skills = {
        "inferno_aura": Skill.from_dict(
            {
                "id": "inferno_aura",
                "name": "Inferno Aura",
                "type": "passive",
                "effect": "lifespan",
                "scaling": 400,
            }
        ),
    }
    system = SkillSystem(skills)
    player = Player(name="Tester")

    result = system.learn_skill(player, "inferno_aura")

    assert result["event"] == EventType.SKILL_LEARNED
    assert player.lifespan_bonus_years == 400


def test_active_skill_learn_does_not_apply_passive_effects():
    system = SkillSystem(_skills())
    player = Player(name="Tester")

    result = system.learn_skill(player, "spirit_palm")

    assert result["event"] == EventType.SKILL_LEARNED
    assert player.comprehension == 10
    assert player.lifespan_bonus_years == 0
