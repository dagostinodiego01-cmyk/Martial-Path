"""Tests for the two-track talent tier ladder."""
import dataclasses

from game.core.game_engine import GameEngine
from game.data.registry import GameDataRegistry
from game.systems.talent_system import TalentSystem
from game.utils.data_loader import load_json
from game.validation import validate_all_game_data


def _make_system():
    return TalentSystem(load_json("cultivation/talents.json")["tiers"])


def test_ladder_covers_twenty_tiers_plus_apex():
    system = _make_system()
    tiers = system.all_tiers()

    tier_indices = [entry["tier"] for entry in tiers]
    assert tier_indices == sorted(tier_indices)
    assert set(range(1, 21)) <= set(tier_indices)
    apex_entries = [entry for entry in tiers if entry.get("is_apex")]
    assert len(apex_entries) == 1


def test_every_tier_carries_both_track_names_realm_and_lifespan():
    system = _make_system()

    for entry in system.all_tiers():
        assert entry["martial_talent_name"]
        assert entry["body_talent_name"]
        assert entry["cultivation_realm"]
        assert "max_lifespan_years" in entry
        assert entry["lifespan_display"]


def test_tier_view_resolves_shared_index_to_both_tracks():
    system = _make_system()

    xiantian = system.tier_view(3)

    assert xiantian["martial_talent_name"] == "Human Grade (4)"
    assert xiantian["body_talent_name"] == "Forged Body Grade"
    assert xiantian["cultivation_realm"] == "Xiantian"
    assert xiantian["max_lifespan_years"] == 400
    assert xiantian["source"] == "canon"


def test_immortal_tiers_use_null_lifespan_sentinel():
    system = _make_system()

    beyond = system.tier_view(20)
    apex = system.view_by_id("apex")

    assert beyond["max_lifespan_years"] is None
    assert beyond["lifespan_display"] == "Effectively immortal"
    assert apex["max_lifespan_years"] is None
    assert apex["lifespan_display"] == "Eternal"


def test_unknown_lookups_return_none():
    system = _make_system()

    assert system.tier_view(999) is None
    assert system.view_by_id("not_a_talent") is None


def test_views_are_defensive_copies():
    system = _make_system()

    view = system.tier_view(1)
    view["martial_talent_name"] = "Mutated"

    assert system.tier_view(1)["martial_talent_name"] == "No Talent"


def test_engine_exposes_talent_ladder():
    engine = GameEngine.new_game("Tester", seed=1)

    assert engine.talents.tier_view(15)["cultivation_realm"] == "Empyrean"


def test_shipped_talent_ladder_is_valid():
    result = validate_all_game_data()
    assert result.is_valid, result.format_errors()


def test_detects_duplicate_talent_tier():
    base = GameDataRegistry.load()
    tiers = [dict(entry) for entry in base.talents["tiers"]]
    tiers[1]["tier"] = tiers[0]["tier"]
    broken = dataclasses.replace(base, talents={**base.talents, "tiers": tiers})
    result = validate_all_game_data(broken)
    assert not result.is_valid
    assert any(error.category == "bad_talent" for error in result.errors)


def test_detects_bad_talent_source():
    base = GameDataRegistry.load()
    tiers = [dict(entry) for entry in base.talents["tiers"]]
    tiers[0]["source"] = "made_up"
    broken = dataclasses.replace(base, talents={**base.talents, "tiers": tiers})
    result = validate_all_game_data(broken)
    assert not result.is_valid
    assert any(error.category == "bad_talent" for error in result.errors)


def test_detects_unknown_talent_realm_id():
    base = GameDataRegistry.load()
    tiers = [dict(entry) for entry in base.talents["tiers"]]
    tiers[2]["realm_id"] = "no_such_realm"
    broken = dataclasses.replace(base, talents={**base.talents, "tiers": tiers})
    result = validate_all_game_data(broken)
    assert not result.is_valid
    assert any(error.category == "bad_talent" for error in result.errors)


def test_detects_missing_apex_tier():
    base = GameDataRegistry.load()
    tiers = [dict(entry) for entry in base.talents["tiers"] if not entry.get("is_apex")]
    broken = dataclasses.replace(base, talents={**base.talents, "tiers": tiers})
    result = validate_all_game_data(broken)
    assert not result.is_valid
    assert any(error.category == "bad_talent" for error in result.errors)
