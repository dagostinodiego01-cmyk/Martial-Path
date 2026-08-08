"""Tests for starting talent roll helpers."""
from game.systems.starting_fate_system import StartingFateSystem
from game.utils.data_loader import load_json
from game.utils.rng import RNG


def _make_system(seed=1):
    return StartingFateSystem(
        load_json("cultivation/martial_talents.json"),
        load_json("cultivation/body_talents.json"),
        RNG(seed=seed),
    )


def test_weighted_roll_returns_valid_talent_ids():
    system = _make_system(seed=1)

    result = system.roll()

    assert result["martial_talent_id"] == result["martial_talent"]["id"]
    assert result["body_talent_id"] == result["body_talent"]["id"]


def test_weighted_roll_only_returns_rollable_entries():
    system = _make_system(seed=1)
    martial_ids = {t["id"] for t in load_json("cultivation/martial_talents.json") if t["roll_weight"] > 0}
    body_ids = {t["id"] for t in load_json("cultivation/body_talents.json") if t["roll_weight"] > 0}

    for _ in range(100):
        result = system.roll()
        assert result["martial_talent_id"] in martial_ids
        assert result["body_talent_id"] in body_ids


def test_talent_views_do_not_expose_roll_weights_or_upgrade_options():
    system = _make_system(seed=1)

    martial = system.martial_talent_view("earth_grade")
    body = system.body_talent_view("iron_skin_grade")

    assert "roll_weight" not in martial
    assert "upgrade_options" not in martial
    assert "roll_weight" not in body
    assert "upgrade_options" not in body