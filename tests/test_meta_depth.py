"""Meta depth (ROADMAP Phase 2 C): legacy unlock tree, world seed, ascension.

C.5 -- a browsable unlock tree bought with Ancestral Memory, persisted across
runs and applied on character creation.
C.6 -- the run seed derives a deterministic world report (dominant sects,
economy band, encounter bias); two seeds differ measurably, one seed replays
identically.
C.7 -- retirement/ascension is a *win*: it banks the 3x legacy reward, records
an ``ascended`` chronicle entry, and ends the run like death does.
"""
import dataclasses

from game.core.game_engine import GameEngine
from game.data.registry import GameDataRegistry
from game.services.meta_service import (
    ASCENSION_REWARD_MULTIPLIER,
    DEATH_REALM_BONUS,
    DEATH_REWARD,
    MetaService,
)
from game.systems.legacy_system import LegacySystem
from game.validation import validate_all_game_data


def _meta(tmp_path) -> MetaService:
    return MetaService(tmp_path / "meta.json")


# -- C.5: legacy unlock tree ----------------------------------------------
def test_tree_has_three_tiers_with_titles_and_costs():
    system = LegacySystem(GameDataRegistry.load().legacy_tree)
    tiers = system.tiers()
    assert len(tiers) >= 3
    kinds = {node["kind"] for node in system.all_nodes()}
    assert {"sect", "technique", "title"} <= kinds
    assert all(int(node["cost"]) > 0 for node in system.all_nodes())


def test_tier_state_flags_purchased_and_availability():
    system = LegacySystem(GameDataRegistry.load().legacy_tree)
    tiers = system.tier_state([])
    first = tiers[0]
    later = tiers[-1]
    assert first["unlocked"] is True
    assert later["unlocked"] is False  # no purchases yet
    node = system.tier_state(["sect_lin_academy"])[0]
    bought = next(n for n in node["unlocks"] if n["id"] == "sect_lin_academy")
    assert bought["purchased"] is True
    assert bought["available"] is False


def test_can_unlock_gates_tier_and_duplicates():
    system = LegacySystem(GameDataRegistry.load().legacy_tree)
    assert system.can_unlock("sect_lin_academy", [])["ok"] is True
    assert system.can_unlock("sect_lin_academy", ["sect_lin_academy"])["reason"] == "ALREADY_OWNED"
    assert system.can_unlock("title_deathless", [])["reason"] == "TIER_LOCKED"
    assert system.can_unlock("no_such_node", [])["reason"] == "UNKNOWN_UNLOCK"


def test_unlock_persists_and_reapplies_on_new_run(tmp_path):
    meta = _meta(tmp_path)
    meta.add_memory(100)
    engine = GameEngine.new_game(seed=5, meta=meta)
    result = engine.process_action({"action": "UNLOCK", "unlock_id": "technique_nine_yang_domain"})

    assert result["event"] == "UNLOCK_PURCHASED"
    assert meta.memory() == 70  # 100 - 30
    assert "nine_yang_domain" in engine.player.skills

    # A brand-new run starts with the purchased technique (and no double charge).
    fresh = GameEngine.new_game(seed=6, meta=meta)
    assert "nine_yang_domain" in fresh.player.skills
    assert meta.memory() == 70


def test_unlock_requires_balance(tmp_path):
    meta = _meta(tmp_path)  # balance 0
    engine = GameEngine.new_game(seed=5, meta=meta)
    result = engine.process_action({"action": "UNLOCK", "unlock_id": "title_dawn_walker"})
    assert result["event"] == "ERROR"
    assert result["reason"] == "INSUFFICIENT_MEMORY"


def test_meta_state_carries_unlock_tree(tmp_path):
    meta = _meta(tmp_path)
    engine = GameEngine.new_game(seed=5, meta=meta)
    state = engine.get_meta_state()
    assert state["unlocks"] == []
    assert len(state["unlock_tree"]) >= 3
    assert state["unlock_tree"][0]["unlocked"] is True


def test_title_surfaces_in_player_view_and_chronicle(tmp_path):
    meta = _meta(tmp_path)
    meta.add_memory(50)
    engine = GameEngine.new_game(seed=5, meta=meta)
    engine.process_action({"action": "UNLOCK", "unlock_id": "title_dawn_walker"})
    assert engine._player_view()["title"] == "dawn_walker"

    engine._die("combat", {})
    entry = meta.chronicle()[-1]
    assert entry["title"] == "dawn_walker"


def test_validator_flags_legacy_tree_pointing_at_missing_sect():
    base = GameDataRegistry.load()
    tree = dataclasses.replace(
        base,
        legacy_tree={
            "tiers": [
                {
                    "id": "tier_bad",
                    "display_name": "Broken",
                    "required_meta_tier": 0,
                    "unlocks": [
                        {"id": "sect_missing", "kind": "sect", "target_id": "missing_sect", "cost": 5}
                    ],
                }
            ]
        },
    )
    result = validate_all_game_data(tree)
    assert result.is_valid is False
    assert any("missing sect" in error.message for error in result.errors)


# -- C.6: world seed -------------------------------------------------------
def test_world_seed_report_is_deterministic_and_varies():
    from game.utils.rng import RNG

    system = LegacySystem({})
    sects = ["lin_academy", "seven_profound_valleys", "divine_phoenix_island", "asura_divine_kingdom"]

    a1 = system.world_seed_report(1234, RNG(1234), sects)
    a2 = system.world_seed_report(1234, RNG(1234), sects)
    b = system.world_seed_report(9876, RNG(9876), sects)

    assert a1 == a2  # same seed -> identical world
    assert a1["dominant_sects"] != b["dominant_sects"] or a1["economy_band"] != b["economy_band"]
    assert a1["economy_multiplier"] in (0.9, 1.0, 1.15)


def test_two_seeds_produce_measurably_different_worlds():
    worlds = {GameEngine.new_game(seed=seed)._world["economy_band"] for seed in range(12)}
    assert len(worlds) >= 2  # not every seed lands on the same band


def test_dominant_sect_gets_reputation_discount_and_listing():
    engine = GameEngine.new_game(seed=42)
    dominant = list(engine._world["dominant_sects"])
    assert dominant
    # The discount is observable on the join gate: compare requirements.
    sect = next(s for s in engine.sects._sects.values() if s["id"] == dominant[0])
    base_req = int((sect.get("join_requirements", {}) or {}).get("min_reputation", 0) or 0)
    if base_req > 0:
        player = engine.player
        player.reputation = base_req - 5
        player.cultivation_state.body.realm_id = "body_pulse_condensation"
        gate = engine.sects.can_join(player, dominant[0])
        # With -5 subsidy the gate no longer rejects for reputation.
        assert gate.get("reason") != "REPUTATION_TOO_LOW"


def test_shop_prices_follow_economy_band():
    engine = GameEngine.new_game(seed=1)
    engine.player.gold = 1000
    engine.process_action({"action": "TRAVEL", "location_id": "azure_village"})
    shop = engine.process_action({"action": "SHOP"})
    sword = next(e for e in shop["stock"] if e["item_id"] == "training_sword")
    expected = max(1, round(25 * engine._world["economy_multiplier"]))
    assert sword["price"]["gold"] == expected


# -- C.7: retirement / ascension ------------------------------------------
def test_retire_refused_below_ascension_threshold(tmp_path):
    meta = _meta(tmp_path)
    engine = GameEngine.new_game(seed=5, meta=meta)
    result = engine.process_action({"action": "RETIRE_ASSENT"})
    assert result["event"] == "ERROR"
    assert result["reason"] == "ASCENSION_NOT_REACHED"
    assert engine.is_running() is True


def test_retire_banks_scaled_reward_and_records_ascension(tmp_path):
    meta = _meta(tmp_path)
    engine = GameEngine.new_game(seed=5, meta=meta)
    engine.player.cultivation_state.essence.realm_id = "divine_transformation"

    result = engine.process_action({"action": "RETIRE_ASSENT"})

    assert result["event"] == "RETIRED"
    assert result["summary"]["cause"] == "ascended"
    rank = int(result["summary"]["realm_rank"])
    expected = (DEATH_REWARD + DEATH_REALM_BONUS * rank) * ASCENSION_REWARD_MULTIPLIER
    assert result["reward"] == expected
    assert result["ancestral_memory"] == expected
    assert meta.memory() == expected
    assert engine.is_running() is False
    entry = meta.chronicle()[-1]
    assert entry["cause"] == "ascended"


def test_retire_reward_beats_death_reward_at_same_rank(tmp_path):
    death_meta = _meta(tmp_path / "death")
    death_engine = GameEngine.new_game(seed=7, meta=death_meta)
    death_engine.player.cultivation_state.essence.realm_id = "divine_transformation"
    death_engine._die("combat", {})

    retire_meta = _meta(tmp_path / "retire")
    retire_engine = GameEngine.new_game(seed=7, meta=retire_meta)
    retire_engine.player.cultivation_state.essence.realm_id = "divine_transformation"
    retire_engine.process_action({"action": "RETIRE_ASSENT"})

    assert retire_meta.memory() == death_meta.memory() * ASCENSION_REWARD_MULTIPLIER


def test_retired_flag_persists(tmp_path):
    meta = _meta(tmp_path)
    assert meta.state()["retired"] is False
    meta.mark_retired()
    assert MetaService(tmp_path / "meta.json").state()["retired"] is True


def test_endless_flag_round_trips_through_save(tmp_path):
    from game.services.save_service import SaveService

    meta = _meta(tmp_path)
    engine = GameEngine.new_game(seed=5, meta=meta)
    engine._endless = True
    engine.saves = SaveService(tmp_path / "saves")
    engine.save_game("endless_slot")

    reloaded = GameEngine.new_game(seed=5, meta=meta)
    reloaded.saves = SaveService(tmp_path / "saves")
    reloaded.load_game("endless_slot")
    assert reloaded._endless is True
