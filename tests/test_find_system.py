"""Tests for rarity-weighted, danger-gated exploration finds."""
from game.systems.find_system import FindSystem
from game.utils.rng import RNG


def _config():
    return {
        "rarity_order": ["mortal_grade", "low_spirit_grade", "earth_grade"],
        "rarity_weights": {"mortal_grade": 100, "low_spirit_grade": 50, "earth_grade": 10},
        "danger_max_rarity_index": {"0": 0, "5": 1, "10": 2},
        "default_item_rarity": "mortal_grade",
    }


def _catalog():
    return [
        {"item_id": "common_pill", "rarity": "mortal_grade"},
        {"item_id": "spirit_ring", "rarity": "low_spirit_grade"},
        {"item_id": "earth_blade", "rarity": "earth_grade"},
        {"item_id": "no_rarity_item", "rarity": ""},
    ]


def test_danger_maps_to_max_rarity_index():
    system = FindSystem(_catalog(), _config(), RNG(1))

    assert system.max_rarity_index_for_danger(0) == 0
    assert system.max_rarity_index_for_danger(5) == 1
    assert system.max_rarity_index_for_danger(10) == 2


def test_find_respects_rarity_cap():
    system = FindSystem(_catalog(), _config(), RNG(1))

    # Cap index 0 -> only mortal-grade (incl. the no-rarity item which defaults there).
    finds = {system.roll_find(0) for _ in range(80)}

    assert finds <= {"common_pill", "no_rarity_item"}
    assert "earth_blade" not in finds
    assert "spirit_ring" not in finds


def test_find_can_include_higher_tiers_when_allowed():
    system = FindSystem(_catalog(), _config(), RNG(2))

    finds = {system.roll_find(2) for _ in range(300)}

    assert "earth_blade" in finds
    assert "spirit_ring" in finds


def test_find_returns_none_when_no_eligible_candidates():
    assert FindSystem([], _config(), RNG(1)).roll_find(2) is None
