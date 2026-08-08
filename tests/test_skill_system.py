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
