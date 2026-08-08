"""Tests for the morality system's band interpretation and clamped adjustments."""
from game.systems.morality_system import MoralitySystem


def _system():
    return MoralitySystem()


def test_band_ids_cover_the_full_range():
    system = _system()
    assert system.band_id(-100) == "demonic"
    assert system.band_id(0) == "neutral"
    assert system.band_id(100) == "righteous"


def test_adjust_clamps_to_maximum():
    system = _system()
    result = system.adjust(90, 50)
    assert result["morality"] == 100
    assert result["band"] == "righteous"


def test_adjust_clamps_to_minimum():
    system = _system()
    result = system.adjust(-90, -50)
    assert result["morality"] == -100
    assert result["band"] == "demonic"


def test_adjust_reports_actual_change():
    system = _system()
    result = system.adjust(0, 10)
    assert result["changed"] == 10
    assert result["morality"] == 10
    assert result["band"] == "neutral"
