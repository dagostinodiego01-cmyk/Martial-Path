"""Tests for the versioned save service and its persistence repository.

Covers the M1 milestone gates: v1/v2 migration (SV.1), the safe-point /
autosave policy (SV.2), deterministic continuation state in the snapshot
(SV.5), and crash-safe atomic writes with backup recovery (SV.6).
"""
import json
import os

import pytest

from game.core.constants import EventType, MODE_ENCOUNTER, MODE_EXPLORE
from game.core.game_engine import GameEngine
from game.persistence.save_repository import SaveRepository
from game.services.save_service import SAVE_VERSION, SaveError, SaveService
from game.utils.rng import RNG


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
    engine.player.age_years = 31.5
    engine.player.martial_talent_id = "hallowed_lord_grade"
    engine.player.body_talent_id = "dao_palace_grade"
    engine.player.equipment["ring_1"] = "minor_qi_ring"
    engine.player.cultivation_state.body.progress = 55.0
    engine.player.cultivation_state.body.cultivation_strain = 33.0
    engine.player.cultivation_state.body.foundation_stability = 77.0

    assert engine.save_game("slot1")["success"] is True

    # Mutate live state, then load should restore the saved values.
    engine.player.gold = 0
    engine.player.current_location = "outer_forest"
    engine.player.age_years = 12.0
    engine.player.martial_talent_id = "earth_grade"
    engine.player.body_talent_id = "iron_skin_grade"
    engine.player.equipment["ring_1"] = None
    engine.player.cultivation_state.body.progress = 0.0
    engine.player.cultivation_state.body.cultivation_strain = 0.0
    engine.player.cultivation_state.body.foundation_stability = 100.0

    result = engine.load_game("slot1")
    assert result["success"] is True
    assert engine.player.gold == 123
    assert engine.player.current_location == "azure_village"
    assert engine.player.age_years == 31.5
    assert engine.player.martial_talent_id == "hallowed_lord_grade"
    assert engine.player.body_talent_id == "dao_palace_grade"
    assert engine.player.equipment["ring_1"] == "minor_qi_ring"
    assert engine.player.cultivation_state.body.progress == 55.0
    assert engine.player.cultivation_state.body.cultivation_strain == 33.0
    assert engine.player.cultivation_state.body.foundation_stability == 77.0


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


# -- SV.1: every supported save version migrates ------------------------


def test_v1_save_migrates_to_the_current_version(tmp_path):
    """A v1 save (old Spiritual Root / Physique fields) loads, renamed."""
    legacy = {
        "version": 1,
        "player": {
            "name": "Ancient",
            "spiritual_root_id": "hallowed_lord_grade",
            "physique_id": "dao_palace_grade",
        },
    }
    (tmp_path / "old.json").write_text(json.dumps(legacy), encoding="utf-8")
    service = SaveService(tmp_path)

    data = service.read("old")

    assert data["version"] == SAVE_VERSION
    assert data["player"]["martial_talent_id"] == "hallowed_lord_grade"
    assert data["player"]["body_talent_id"] == "dao_palace_grade"
    assert "spiritual_root_id" not in data["player"]
    assert "physique_id" not in data["player"]

    # The migrated save is loadable by the engine and the talents apply.
    engine = GameEngine.new_game(seed=1)
    engine.saves = service
    assert engine.load_game("old")["success"] is True
    assert engine.player.martial_talent_id == "hallowed_lord_grade"
    assert engine.player.body_talent_id == "dao_palace_grade"


def test_v2_save_migrates_with_documented_defaults(tmp_path):
    """A current-production v2 save loads with the v3 defaults spelled out."""
    v2 = {
        "version": 2,
        "player": {
            "name": "Mid",
            "martial_talent_id": "earth_grade",
            "body_talent_id": "iron_skin_grade",
        },
        "quests": {},
    }
    (tmp_path / "v2.json").write_text(json.dumps(v2), encoding="utf-8")
    service = SaveService(tmp_path)

    data = service.read("v2")

    assert data["version"] == SAVE_VERSION
    # The documented defaults for the deterministic-continuation fields: a v2
    # save predates them, so it loads but promises no bit-identical continuation.
    assert data["seed"] is None
    assert data["rng"] == {}
    assert data["world_seed"] == {}
    assert data["last_world_report"] == {}
    assert data["cooldowns"] == {}
    assert data["encounter_seq"] == 0
    assert data["fate"] == {"accepted": True, "pending": None}
    assert data["active_realm"] is None
    assert data["tournament_active"] is False
    assert data["oath_stakes"] is None
    assert data["running"] is True

    engine = GameEngine.new_game(seed=1)
    engine.saves = service
    assert engine.load_game("v2")["success"] is True
    assert engine.player.name == "Mid"


def test_write_migrates_an_imported_old_payload(tmp_path):
    """An imported portable payload is migrated, never mislabelled as current."""
    service = SaveService(tmp_path)
    service.write(
        "imported",
        {"version": 1, "player": {"name": "X", "spiritual_root_id": "earth_grade"}},
    )

    data = service.read("imported")

    assert data["version"] == SAVE_VERSION
    assert data["player"]["martial_talent_id"] == "earth_grade"


def test_absent_version_is_rejected(tmp_path):
    service = SaveService(tmp_path)
    (tmp_path / "noversion.json").write_text(json.dumps({"player": {}}), encoding="utf-8")
    with pytest.raises(SaveError) as exc:
        service.read("noversion")
    assert exc.value.code == "SAVE_VERSION_MISMATCH"


def test_non_integer_version_is_reported_as_corrupt(tmp_path):
    service = SaveService(tmp_path)
    (tmp_path / "weird.json").write_text(json.dumps({"version": "banana"}), encoding="utf-8")
    with pytest.raises(SaveError) as exc:
        service.read("weird")
    assert exc.value.code == "SAVE_CORRUPT"


# -- SV.6: crash-safe writes and recovery --------------------------------


def test_serialisation_failure_leaves_the_previous_save_intact(tmp_path):
    """The payload is serialised before any file is touched."""
    service = SaveService(tmp_path)
    service.write("slot", {"player": {"name": "First"}})

    with pytest.raises(SaveError) as exc:
        service.write("slot", {"player": {"bad": {1, 2, 3}}})  # not JSON-serialisable

    assert exc.value.code == "WRITE_FAILED"
    assert service.read("slot")["player"]["name"] == "First"


def test_interrupted_write_leaves_the_previous_save_recoverable(tmp_path, monkeypatch):
    """A crash between the two atomic replaces recovers the old generation."""
    import game.persistence.save_repository as repository_module

    service = SaveService(tmp_path)
    service.write("slot", {"player": {"name": "First"}})

    real_replace = os.replace

    def crash_on_promote(src, dst):
        if str(dst).endswith(f"{os.sep}slot.json"):
            raise OSError("simulated crash during promote")
        return real_replace(src, dst)

    monkeypatch.setattr(repository_module.os, "replace", crash_on_promote)
    with pytest.raises(SaveError) as exc:
        service.write("slot", {"player": {"name": "Second"}})
    assert exc.value.code == "WRITE_FAILED"
    monkeypatch.undo()

    # The primary file is gone (it was moved aside); the backup answers.
    assert service.read("slot")["player"]["name"] == "First"


def test_corrupt_primary_file_recovers_from_the_backup(tmp_path):
    service = SaveService(tmp_path)
    service.write("slot", {"player": {"name": "First"}})
    service.write("slot", {"player": {"name": "Second"}})  # First becomes .bak

    (tmp_path / "slot.json").write_text("{ truncated", encoding="utf-8")

    assert service.read("slot")["player"]["name"] == "First"


def test_slot_whose_primary_file_is_missing_still_lists(tmp_path):
    service = SaveService(tmp_path)
    service.write("a", {"player": {"name": "First"}})
    service.write("a", {"player": {"name": "Second"}})

    (tmp_path / "a.json").unlink()

    slots = {entry["slot"]: entry for entry in service.list_slots()}
    assert "a" in slots
    assert slots["a"]["name"] == "First"
    assert service.exists("a") is True


def test_backups_and_temp_files_never_list_as_separate_slots(tmp_path):
    service = SaveService(tmp_path)
    service.write("a", {"player": {"name": "A1"}})
    service.write("a", {"player": {"name": "A2"}})  # leaves a.json.bak
    service.write("b", {"player": {"name": "B"}})

    assert {entry["slot"] for entry in service.list_slots()} == {"a", "b"}


# -- SV.5: the snapshot carries the deterministic-continuation contract --


def test_rng_state_round_trips_through_json():
    rng = RNG(7)
    rng.randint(0, 100)  # advance the stream

    state = json.loads(json.dumps(rng.get_state()))
    expected = [rng.randint(0, 1000) for _ in range(5)]

    clone = RNG(999999)  # deliberately unrelated construction
    clone.set_state(state)

    assert [clone.randint(0, 1000) for _ in range(5)] == expected


def test_snapshot_carries_seed_and_every_rng_stream(tmp_path):
    engine = GameEngine.new_game(seed=4242)
    engine.saves = SaveService(tmp_path)

    assert engine.save_game("s")["success"] is True

    data = json.loads((tmp_path / "s.json").read_text(encoding="utf-8"))
    assert data["version"] == SAVE_VERSION
    assert data["seed"] == 4242
    assert set(data["rng"]) == {"main", "narrative", "foe_ai", "debate", "world"}
    for name, state in data["rng"].items():
        assert isinstance(state, list) and len(state) == 3, name


def test_load_restores_rng_stream_states_and_run_seed(tmp_path):
    engine = GameEngine.new_game(seed=11)
    engine.saves = SaveService(tmp_path)
    engine.process_action({"action": "EXPLORE"})  # advance some streams
    if not engine.at_safe_point():
        # A pending scene is irrelevant to stream state; clear it so the save
        # (which only fires at safe points) can be taken.
        engine._clear_encounter_state()
        engine._mode = MODE_EXPLORE
    states = {name: stream.get_state() for name, stream in engine._rng_streams().items()}
    world = dict(engine._world)
    assert engine.save_game("x")["success"] is True

    # Clobber everything a naive load would leave behind.
    for stream in engine._rng_streams().values():
        stream.seed(12345)
    engine._seed = -1
    engine._world = {}

    assert engine.load_game("x")["success"] is True

    assert {name: stream.get_state() for name, stream in engine._rng_streams().items()} == states
    assert engine._seed == 11
    assert engine._world == world
    assert engine.sects._dominant == list(world.get("dominant_sects", []))


# -- SV.2: safe points and the single autosave policy --------------------


def _explore_until_encounter(engine, tries: int = 80) -> dict:
    for _ in range(tries):
        result = engine.process_action({"action": "EXPLORE"})
        if result.get("event") == EventType.ENCOUNTER:
            return result
    raise AssertionError("no encounter rolled in 80 explores")


def test_at_safe_point_holds_on_a_fresh_exploration_turn():
    engine = GameEngine.new_game(seed=3)
    assert engine.at_safe_point() is True

    result = engine.process_action({"action": "EXPLORE"})

    if result.get("event") == EventType.ENCOUNTER:
        assert engine.at_safe_point() is False  # a choice is pending
    else:
        assert engine.at_safe_point() is True  # the turn resolved cleanly


def test_save_is_refused_while_an_encounter_is_pending(tmp_path):
    engine = GameEngine.new_game(seed=5)
    engine.saves = SaveService(tmp_path)
    _explore_until_encounter(engine)
    assert engine._mode == MODE_ENCOUNTER
    assert engine.at_safe_point() is False

    result = engine.save_game("mid")

    assert result["success"] is False
    assert result["reason"] == "UNSAFE_SAVE_POINT"
    assert not (tmp_path / "mid.json").exists()


def test_autosave_only_writes_at_safe_points(tmp_path):
    engine = GameEngine.new_game(seed=5)
    engine.saves = SaveService(tmp_path)

    assert engine.autosave("auto")["success"] is True
    assert (tmp_path / "auto.json").exists()

    _explore_until_encounter(engine)
    refused = engine.autosave("auto2")
    assert refused["success"] is False
    assert refused["reason"] == "UNSAFE_SAVE_POINT"
    assert not (tmp_path / "auto2.json").exists()

    # A load resolves the scene the way every safe point sees it, and saving
    # works again afterwards.
    engine._clear_encounter_state()
    engine._mode = MODE_EXPLORE
    assert engine.autosave("auto3")["success"] is True
    assert (tmp_path / "auto3.json").exists()


def test_autosave_never_fires_for_a_finished_run(tmp_path):
    engine = GameEngine.new_game(seed=3)
    engine.saves = SaveService(tmp_path)
    engine._running = False

    result = engine.autosave("dead")

    assert result["success"] is False
    assert result["reason"] == "UNSAFE_SAVE_POINT"
    assert not (tmp_path / "dead.json").exists()

