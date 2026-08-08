"""Tests for the central effect interpreter."""
from game.models.player import Player
from game.systems.effect_system import EffectSystem


def test_effect_system_heals_player():
    player = Player(name="Tester", hp=10, max_hp=100)
    effects = EffectSystem()

    result = effects.apply_to_player(player, "heal", 40)

    assert result["healed"] == 40
    assert player.hp == 50


def test_effect_system_caps_progress_at_100():
    player = Player(name="Tester", progress=90)
    effects = EffectSystem()

    result = effects.apply_to_player(player, "cultivation_boost", 25)

    assert result["progress"] == 100.0
    assert player.progress == 100.0
