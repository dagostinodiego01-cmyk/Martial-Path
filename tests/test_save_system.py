"""Tests for the versioned save service and its persistence repository."""
import json

import pytest

from game.core.game_engine import GameEngine
from game.persistence.save_repository import SaveRepository
from game.services.save_service import SAVE_VERSION, SaveError, SaveService


def test_write_read_roundtrip(tmp_path):
    service = SaveService(tmp_path)
    service.write("slot1", {"player": {"name": "Tester"}, "quests": {}})

    data = service.read("slot1")
    assert data["version"] == SAVE_VERSION
    assert data["player"]["name"] == "Tester"


def test_read_missing_raises_not_found(tmp_path):
    service = SaveService(tmp_path)
    with pytest.raises(SaveError) as exc:
        service.read("nope")
    assert exc.value.code == "SAVE_NOT_FOUND"


def test_version_mismatch_raises(tmp_path):
    service = SaveService(tmp_path)
    (tmp_path / "bad.json").write_text(json.dumps({"version": 999, "player": {}}), encoding="utf-8")
    with pytest.raises(SaveError) as exc:
        service.read("bad")
    assert exc.value.code == "SAVE_VERSION_MISMATCH"


def test_repository_sanitises_slot_against_traversal(tmp_path):
    repository = SaveRepository(tmp_path)
    repository.write_raw("../evil", {"player": {}})

    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1
    assert ".." not in files[0].name


def test_list_slots_returns_summaries(tmp_path):
    service = SaveService(tmp_path)
    service.write("a", {"player": {"name": "A", "realm": "Strength Training"}})

    slots = service.list_slots()
    assert any(s["slot"] == "a" and s["name"] == "A" for s in slots)


def test_engine_save_load_roundtrip(tmp_path):
    engine = GameEngine.new_game(seed=1)
    engine.saves = SaveService(tmp_path)
    engine.player.gold = 123
    engine.player.current_location = "azure_village"
    engine.player.current_day = 7
    engine.player.martial_talent_id = "hallowed_lord_grade"
    engine.player.body_talent_id = "dao_palace_grade"
    engine.player.equipment["ring_1"] = "minor_qi_ring"
    engine.player.cultivation_state.body.progress = 55.0
    engine.player.cultivation_state.body.cultivation_strain = 33.0
    engine.player.cultivation_state.body.foundation_stability = 77.0
    engine.player.cultivation_state.body.daily_cultivation_count = 4
    engine.player.cultivation_state.body.last_cultivation_day = 7

    assert engine.save_game("slot1")["success"] is True

    # Mutate live state, then load should restore the saved values.
    engine.player.gold = 0
    engine.player.current_location = "outer_forest"
    engine.player.current_day = 1
    engine.player.martial_talent_id = "earth_grade"
    engine.player.body_talent_id = "iron_skin_grade"
    engine.player.equipment["ring_1"] = None
    engine.player.cultivation_state.body.progress = 0.0
    engine.player.cultivation_state.body.cultivation_strain = 0.0
    engine.player.cultivation_state.body.foundation_stability = 100.0
    engine.player.cultivation_state.body.daily_cultivation_count = 0
    engine.player.cultivation_state.body.last_cultivation_day = 1

    result = engine.load_game("slot1")
    assert result["success"] is True
    assert engine.player.gold == 123
    assert engine.player.current_location == "azure_village"
    assert engine.player.current_day == 7
    assert engine.player.martial_talent_id == "hallowed_lord_grade"
    assert engine.player.body_talent_id == "dao_palace_grade"
    assert engine.player.equipment["ring_1"] == "minor_qi_ring"
    assert engine.player.cultivation_state.body.progress == 55.0
    assert engine.player.cultivation_state.body.cultivation_strain == 33.0
    assert engine.player.cultivation_state.body.foundation_stability == 77.0
    assert engine.player.cultivation_state.body.daily_cultivation_count == 4
    assert engine.player.cultivation_state.body.last_cultivation_day == 7


def test_engine_load_missing_returns_failure(tmp_path):
    engine = GameEngine.new_game(seed=1)
    engine.saves = SaveService(tmp_path)

    result = engine.load_game("missing")
    assert result["success"] is False
    assert result["reason"] == "SAVE_NOT_FOUND"


def test_quest_progress_survives_save_load(tmp_path):
    engine = GameEngine.new_game(seed=1)
    engine.saves = SaveService(tmp_path)
    # Advance the "defeat" quest by one and persist.
    engine.quests.notify("defeat", engine.player, engine.inventory)
    engine.save_game("q")

    engine.load_game("q")
    trial = {q["id"]: q for q in engine.quests.snapshot()}["trial_of_the_forest"]
    assert trial["objectives"][0]["current"] == 1


def test_old_save_defaults_starting_fate_ids():
    player = GameEngine._build_player("Old Save")
    restored = player.from_save_dict({"name": "Old Save"})

    assert restored.martial_talent_id == "earth_grade"
    assert restored.body_talent_id == "iron_skin_grade"


def test_old_save_defaults_empty_equipment():
    restored = GameEngine._build_player("Old Save").from_save_dict({"name": "Old Save"})

    assert all(item_id is None for item_id in restored.equipment.values())

