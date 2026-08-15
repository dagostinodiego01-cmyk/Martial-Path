"""Roguelike legacy & meta (ROADMAP C.1-C.4).

Covers the permadeath default + run summary (C.1), the Ancestral Memory meta
currency (C.2), origins gated by that currency (C.3), and the persistent run
chronicle (C.4).
"""
import dataclasses

from game.core.game_engine import GameEngine
from game.data.registry import GameDataRegistry
from game.services.meta_service import MetaService
from game.systems.origin_system import OriginSystem
from game.validation import validate_all_game_data


def _meta(tmp_path) -> MetaService:
    return MetaService(tmp_path / "meta.json")


# -- C.2: Ancestral Memory ------------------------------------------------
def test_memory_adds_and_spends(tmp_path):
    meta = _meta(tmp_path)
    assert meta.memory() == 0
    assert meta.add_memory(25) == 25
    assert meta.spend_memory(10) is True
    assert meta.memory() == 15
    assert meta.spend_memory(100) is False  # unaffordable
    assert meta.memory() == 15


def test_memory_persists_across_instances(tmp_path):
    path = tmp_path / "meta.json"
    MetaService(path).add_memory(40)
    assert MetaService(path).memory() == 40


# -- C.4: run chronicle ---------------------------------------------------
def test_chronicle_records_runs_and_stays_bounded(tmp_path):
    meta = _meta(tmp_path)
    for i in range(5):
        meta.record_run({"seed": i, "cause": "combat"})
    chronicle = meta.chronicle()
    assert len(chronicle) == 5
    assert chronicle[-1]["seed"] == 4

    # A long-lived meta-save must not grow unbounded.
    for i in range(300):
        meta.record_run({"seed": 1000 + i, "cause": "old_age"})
    assert len(meta.chronicle()) == 100


# -- C.3: origins ---------------------------------------------------------
def test_origins_have_four_and_a_free_default():
    system = OriginSystem(GameDataRegistry.load().origins)
    assert len(system.all()) >= 4
    assert system.cost(system.default_id()) == 0


def test_origin_spends_memory_and_applies_modifiers(tmp_path):
    meta = _meta(tmp_path)
    meta.add_memory(100)
    engine = GameEngine.new_game(seed=1, origin_id="noble_scion", meta=meta)

    assert engine.player.origin_id == "noble_scion"
    assert engine.player.dao_id == "astral_dao"
    assert "spirit_palm" in engine.player.skills
    assert engine.player.gold == 200
    assert meta.memory() == 80  # cost 20 spent


def test_origin_unaffordable_falls_back_to_free(tmp_path):
    meta = _meta(tmp_path)  # 0 memory
    engine = GameEngine.new_game(seed=1, origin_id="fallen_immortal", meta=meta)
    assert engine.player.origin_id == "orphan"
    assert meta.memory() == 0


def test_get_meta_state_annotates_affordability(tmp_path):
    meta = _meta(tmp_path)
    meta.add_memory(20)
    engine = GameEngine.new_game(seed=1, meta=meta)
    state = engine.get_meta_state()

    assert state["ancestral_memory"] == 20
    assert "chronicle" in state
    origins = {entry["id"]: entry for entry in state["origins"]}
    assert origins["orphan"]["affordable"] is True
    assert origins["noble_scion"]["affordable"] is True  # cost 20 <= 20
    assert origins["fallen_immortal"]["affordable"] is False  # cost 50 > 20


# -- C.1: permadeath default ---------------------------------------------
def test_hardcore_death_ends_run_and_banks_meta(tmp_path):
    meta = _meta(tmp_path)
    engine = GameEngine.new_game(seed=1, meta=meta)
    assert engine.is_running()

    result = engine._die("combat", {})

    assert engine.is_running() is False
    assert result["cause"] == "combat"
    assert "summary" in result
    assert meta.memory() > 0
    entries = meta.chronicle()
    assert len(entries) == 1
    assert entries[0]["cause"] == "combat"
    assert entries[0]["origin"] == "orphan"
    assert entries[0]["dao"] == "sword_dao"


def test_softcore_defeat_keeps_run_alive(tmp_path):
    meta = _meta(tmp_path)
    engine = GameEngine.new_game(seed=1, hardcore=False, meta=meta)
    assert engine._hardcore is False

    engine._end_combat({"outcome": "DEFEAT"})

    assert engine.is_running() is True
    assert meta.memory() == 0
    assert len(meta.chronicle()) == 0


# -- validator ------------------------------------------------------------
def test_detects_origin_with_unknown_dao():
    base = GameDataRegistry.load()
    broken_origin = dict(base.origins[0])
    broken_origin["dao_id"] = "missing_dao"
    broken = dataclasses.replace(base, origins=[broken_origin] + list(base.origins[1:]))

    result = validate_all_game_data(broken)

    assert not result.is_valid
    assert any(error.category == "bad_origin" for error in result.errors)
