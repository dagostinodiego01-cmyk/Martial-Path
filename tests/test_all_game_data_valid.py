"""End-to-end validation of the shipped game data.

The first test is the real guard: all bundled content must be internally
consistent. The rest confirm the validator actually *catches* the classes of
error it claims to, by feeding it deliberately broken registries.
"""
import dataclasses

from game.data.registry import GameDataRegistry
from game.validation import validate_all_game_data


def test_all_shipped_game_data_is_valid():
    result = validate_all_game_data()
    assert result.is_valid, result.format_errors()


def test_detects_duplicate_item_id():
    base = GameDataRegistry.load()
    broken = dataclasses.replace(base, items=base.items + [base.items[0]])
    result = validate_all_game_data(broken)
    assert not result.is_valid
    assert any(error.category == "duplicate_id" for error in result.errors)


def test_detects_dangling_location_connection():
    base = GameDataRegistry.load()
    first = dict(base.locations[0])
    first["connected_locations"] = ["nowhere_at_all"]
    broken = dataclasses.replace(base, locations=[first] + list(base.locations[1:]))
    result = validate_all_game_data(broken)
    assert not result.is_valid
    assert any(error.category == "bad_location_ref" for error in result.errors)


def test_detects_invalid_location_map_position():
    base = GameDataRegistry.load()
    first = dict(base.locations[0])
    first["map_position"] = {"x": 1.5, "y": 0.5}
    broken = dataclasses.replace(base, locations=[first] + list(base.locations[1:]))

    result = validate_all_game_data(broken)

    assert not result.is_valid
    assert any(error.category == "bad_map_position" for error in result.errors)


def test_detects_bad_npc_reference_on_location():
    base = GameDataRegistry.load()
    first = dict(base.locations[0])
    first["npc_ids"] = ["ghost_npc_that_does_not_exist"]
    broken = dataclasses.replace(base, locations=[first] + list(base.locations[1:]))
    result = validate_all_game_data(broken)
    assert not result.is_valid
    assert any(error.category == "bad_npc_ref" for error in result.errors)


def test_detects_missing_item_reference_in_quest_reward():
    base = GameDataRegistry.load()
    quest = dict(base.quests[0])
    quest["rewards"] = {"items": {"nonexistent_item": 1}}
    broken = dataclasses.replace(base, quests=[quest] + list(base.quests[1:]))
    result = validate_all_game_data(broken)
    assert not result.is_valid
    assert any(error.category == "bad_item_ref" for error in result.errors)


def test_detects_invalid_cultivation_required_progress():
    base = GameDataRegistry.load()
    realms = [dict(realm) for realm in base.body_realms["realms"]]
    realms[0]["required_progress"] = 0
    body_realms = dict(base.body_realms)
    body_realms["realms"] = realms
    broken = dataclasses.replace(base, body_realms=body_realms)

    result = validate_all_game_data(broken)

    assert not result.is_valid
    assert any(error.category == "bad_cultivation_progress" for error in result.errors)


def test_detects_invalid_cultivation_progression_config():
    base = GameDataRegistry.load()
    config = dict(base.cultivation_config)
    body_progression = dict(config["body_progression"])
    body_progression["max_strain_for_breakthrough"] = 150
    config["body_progression"] = body_progression
    broken = dataclasses.replace(base, cultivation_config=config)

    result = validate_all_game_data(broken)

    assert not result.is_valid
    assert any(error.category == "bad_cultivation_config" for error in result.errors)


def test_detects_invalid_martial_talent_roll_weight():
    base = GameDataRegistry.load()
    talents = [dict(talent) for talent in base.martial_talents]
    talents[0]["roll_weight"] = -1
    broken = dataclasses.replace(base, martial_talents=talents)

    result = validate_all_game_data(broken)

    assert not result.is_valid
    assert any(error.category == "bad_fate_trait" for error in result.errors)


def test_detects_invalid_body_talent_upgrade_target():
    base = GameDataRegistry.load()
    talents = [dict(talent) for talent in base.body_talents]
    talents[0]["upgrade_options"] = [{"target_id": "missing_talent", "method": "test"}]
    broken = dataclasses.replace(base, body_talents=talents)

    result = validate_all_game_data(broken)

    assert not result.is_valid
    assert any(error.category == "bad_fate_trait" for error in result.errors)


def test_detects_invalid_equipment_slot():
    base = GameDataRegistry.load()
    equipment = [dict(item) for item in base.equipment]
    equipment[0]["valid_slots"] = ["missing_slot"]
    broken = dataclasses.replace(base, equipment=equipment)

    result = validate_all_game_data(broken)

    assert not result.is_valid
    assert any(error.category == "bad_equipment" for error in result.errors)


def test_detects_invalid_equipment_modifier():
    base = GameDataRegistry.load()
    equipment = [dict(item) for item in base.equipment]
    equipment[0]["stat_modifiers"] = {"unknown_stat": 1}
    broken = dataclasses.replace(base, equipment=equipment)

    result = validate_all_game_data(broken)

    assert not result.is_valid
    assert any(error.category == "bad_equipment" for error in result.errors)


def test_detects_invalid_shop_item_reference():
    base = GameDataRegistry.load()
    shop = dict(base.shops[0])
    stock = [dict(entry) for entry in shop["stock"]]
    stock[0]["item_id"] = "missing_market_item"
    shop["stock"] = stock
    broken = dataclasses.replace(base, shops=[shop] + list(base.shops[1:]))

    result = validate_all_game_data(broken)

    assert not result.is_valid
    assert any(error.category == "bad_shop" for error in result.errors)
