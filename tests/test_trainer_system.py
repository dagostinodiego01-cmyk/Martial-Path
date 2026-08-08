"""Tests for data-driven skill trainers (technique masters)."""
from game.core.constants import EventType
from game.models.player import Player
from game.models.skill import Skill
from game.systems.skill_system import SkillSystem
from game.systems.trainer_system import TrainerSystem


def _skills():
    return {
        "spirit_palm": Skill.from_dict(
            {"id": "spirit_palm", "name": "Spirit Palm", "type": "active", "qi_cost": 20, "cooldown": 3}
        ),
    }


def _trainers():
    return [
        {
            "id": "sword_hall",
            "display_name": "Sword Hall",
            "location_ids": ["outer_forest"],
            "techniques": [{"skill_id": "spirit_palm", "price": {"gold": 80}}],
        }
    ]


def _system():
    skills = _skills()
    return TrainerSystem(_trainers(), skills, SkillSystem(skills))


def test_trainer_view_lists_techniques_with_state():
    system = _system()
    player = Player(name="Tester", current_location="outer_forest", gold=100)

    view = system.trainer_view(player)

    assert view["event"] == EventType.TRAINER
    technique = view["techniques"][0]
    assert technique["skill_id"] == "spirit_palm"
    assert technique["price"] == {"gold": 80}
    assert technique["affordable"] is True
    assert technique["already_known"] is False


def test_learn_spends_currency_and_teaches():
    system = _system()
    player = Player(name="Tester", current_location="outer_forest", gold=100)

    result = system.learn(player, "spirit_palm")

    assert result["event"] == EventType.SKILL_LEARNED
    assert result["source"] == "trainer"
    assert player.gold == 20
    assert "spirit_palm" in player.skills


def test_learn_without_funds_is_rejected():
    system = _system()
    player = Player(name="Tester", current_location="outer_forest", gold=10)

    result = system.learn(player, "spirit_palm")

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "INSUFFICIENT_FUNDS"
    assert player.gold == 10
    assert "spirit_palm" not in player.skills


def test_learn_unoffered_skill_is_rejected():
    system = _system()
    player = Player(name="Tester", current_location="outer_forest", gold=100)

    result = system.learn(player, "iron_fist")

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "TECHNIQUE_NOT_OFFERED"


def test_learn_already_known_skill_is_rejected():
    system = _system()
    player = Player(name="Tester", current_location="outer_forest", gold=100, skills=["spirit_palm"])

    result = system.learn(player, "spirit_palm")

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "SKILL_ALREADY_KNOWN"
    assert player.gold == 100


def test_trainer_not_at_location_is_rejected():
    system = _system()
    player = Player(name="Tester", current_location="somewhere_else")

    assert system.trainer_view(player)["event"] == EventType.ERROR
    assert system.trainers_for_location("somewhere_else") == []
    assert len(system.trainers_for_location("outer_forest")) == 1
