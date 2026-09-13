"""The split validators must stay wired into the one entry point (V.5).

``data_validator.py`` is now a facade: the checks live in
``world_checks`` / ``progression_checks`` / ``character_checks`` /
``economy_checks``. A split like that fails quietly when a module exists but is
never called, so every domain is exercised through the public entry point
against a deliberately broken registry -- the same shape the equivalence check
(matching the old monolith's 47 errors) covered at split time.
"""
from __future__ import annotations

from game.data.registry import GameDataRegistry
from game.validation import data_validator, validate_all_game_data


def _categories(registry: GameDataRegistry) -> set[str]:
    return {error.category for error in validate_all_game_data(registry).errors}


def test_world_domain_is_wired():
    registry = GameDataRegistry.load()
    registry.locations[0]["danger_level"] = 99
    assert "bad_level" in _categories(registry)


def test_progression_domain_is_wired():
    registry = GameDataRegistry.load()
    registry.body_realms["realms"][0]["required_progress"] = 0
    assert "bad_cultivation_progress" in _categories(registry)


def test_character_domain_is_wired():
    registry = GameDataRegistry.load()
    registry.daos[0]["counters"] = ["ghost_dao"]
    assert "bad_dao" in _categories(registry)


def test_economy_domain_is_wired():
    registry = GameDataRegistry.load()
    registry.shops[0]["stock"][0]["item_id"] = "ghost_item"
    assert "bad_shop" in _categories(registry)


def test_facade_keeps_the_names_its_callers_import():
    # tests/test_locations_data.py imports `_validate_locations` from here and
    # tests/test_combo_combat.py imports GameDataRegistry; moving either without
    # re-exporting it would break callers that never mention the new modules.
    assert callable(data_validator._validate_locations)
    assert data_validator.GameDataRegistry is GameDataRegistry
