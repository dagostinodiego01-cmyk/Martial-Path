"""Tests for effective-stats calculation (passive skills)."""
from types import SimpleNamespace

from game.core.game_engine import GameEngine
from game.models.skill import Skill
from game.systems.stats_system import StatsSystem


def _skill(**overrides):
    base = {
        "id": "x",
        "name": "X",
        "type": "passive",
        "effect": "buff_defense",
        "scaling": 1.2,
        "cooldown": 0,
        "qi_cost": 0,
    }
    base.update(overrides)
    return Skill.from_dict(base)


def _player(defense=5, skills=("guard",)):
    return SimpleNamespace(defense=defense, skills=list(skills), attack=10, max_hp=100, max_qi=50)


def test_passive_buff_defense_raises_effective_defense():
    stats = StatsSystem({"guard": _skill(id="guard", scaling=1.2)})
    assert stats.effective_defense(_player()) == 6


def test_active_skill_does_not_change_defense():
    stats = StatsSystem({"strike": _skill(id="strike", type="active", effect="damage")})
    assert stats.effective_defense(_player(skills=["strike"])) == 5


def test_effective_defense_never_mutates_or_stacks():
    stats = StatsSystem({"guard": _skill(id="guard", scaling=1.2)})
    player = _player()
    first = stats.effective_defense(player)
    second = stats.effective_defense(player)
    assert first == second == 6
    assert player.defense == 5  # base is pristine; passive is never baked in


def test_engine_reports_effective_defense_and_keeps_base_clean():
    engine = GameEngine.new_game(seed=1)
    # flowing_step (buff_defense x1.2) is a starting passive: base 5 -> effective 6.
    assert engine.player.defense == 5
    assert engine.get_game_state()["player"]["defense"] == 6
