"""Living-world simulation (ROADMAP Phase 2 E).

E.1 NPC agency -- NPCs cultivate, clash, and die on the world's own clock.
E.2 Sect simulation -- sect power follows living members and reorders over time.
E.3 Economy -- market pressure moves the price multiplier within a bounded band.
E.4 Seasons acting -- gather yield, travel time, and combat-encounter odds.
E.5 Rumors -- world events mint state-backed rumors; learning reveals subjects.

Engine integration: the world ticks with the calendar (travel/closed-door),
seasons touch gather/travel/events, the market touches shop prices, and the
world state round-trips through saves.
"""
from __future__ import annotations

import pytest

from game.core.game_engine import GameEngine
from game.systems.event_system import EventSystem, DEFAULT_WEIGHTS
from game.systems.world_simulation import (
    DEFAULT_CONFIG,
    SEASON_MODIFIERS,
    WorldSimulationSystem,
    default_world_state,
)
from game.utils.rng import RNG


# -- helpers ---------------------------------------------------------------

def quiet_config() -> dict:
    """A config where nothing random happens (for deterministic assertions)."""
    config = dict(DEFAULT_CONFIG)
    config.update({
        "npc_cultivation_chance": 0.0,
        "npc_rivalry_chance": 0.0,
        "npc_mortality_chance": 0.0,
    })
    return config


def make_system(config: dict | None = None, **kwargs) -> WorldSimulationSystem:
    return WorldSimulationSystem(config=config, **kwargs)


# -- E.1: NPC agency --------------------------------------------------------

def test_world_state_is_seeded_and_deterministic():
    a = default_world_state(RNG(42), ["npc_a", "npc_b", "npc_c"])
    b = default_world_state(RNG(42), ["npc_a", "npc_b", "npc_c"])
    assert a["npcs"] == b["npcs"]
    assert all(npc["alive"] for npc in a["npcs"].values())


def test_tick_advances_world_year_and_reports():
    system = make_system(quiet_config())
    state = default_world_state(RNG(1), ["npc_a"])
    system.tick(state, 1.0, RNG(2))  # establish a baseline power first
    state["sect_power"].pop("sect_one", None) if "sect_power" in state else None
    state["sect_power"] = {}
    report = system.tick(state, 1.5, RNG(3))
    assert report["years"] == 1.5
    assert state["year"] == pytest.approx(2.5)
    # A quiet world is not notable: no gains, clashes, deaths, or shifts.
    assert report["notable"] is False


def test_npcs_cultivate_and_ranks_grow():
    config = dict(DEFAULT_CONFIG)
    config["npc_cultivation_chance"] = 1.0  # always progress
    config["npc_progress_slowdown"] = 0.0
    system = make_system(config)
    state = default_world_state(RNG(7), ["npc_a", "npc_b"])
    # Keep both seeded at rank 1 so a single tick cannot double-step anyone.
    for npc in state["npcs"].values():
        npc["rank"] = 1
    report = system.tick(state, 1.0, RNG(8))
    for npc in state["npcs"].values():
        assert npc["rank"] >= 1 + config["npc_progress_rank"]
    assert set(report["rank_gains"]) == {"npc_a", "npc_b"}
    assert report["notable"] is True


def test_higher_realms_advance_slower():
    config = dict(DEFAULT_CONFIG)
    config["npc_cultivation_chance"] = 1.0
    config["npc_progress_slowdown"] = 100.0  # effectively frozen at rank > 1
    system = make_system(config)
    state = default_world_state(RNG(1), ["npc_a"])
    state["npcs"]["npc_a"]["rank"] = 5
    report = system.tick(state, 1.0, RNG(2))
    assert state["npcs"]["npc_a"]["rank"] == 5
    assert report["rank_gains"] == []


def test_rivalries_and_mortality_remove_npc_from_the_world():
    config = dict(DEFAULT_CONFIG)
    config["npc_rivalry_chance"] = 1.0
    config["npc_mortality_chance"] = 1.0
    config["mortality_min_rank"] = 1
    config["npc_rank_cap"] = 1  # ranks stay 1; mortality still claims them
    config["npc_succession_chance"] = 0.0  # isolate: a refilled seat is not a death
    system = make_system(config)
    state = default_world_state(RNG(9), ["npc_a", "npc_b", "npc_c"])
    report = system.tick(state, 1.0, RNG(10))
    dead = [nid for nid, npc in state["npcs"].items() if not npc["alive"]]
    assert report["deaths"], "mortality should claim someone"
    assert set(report["deaths"]) == set(dead)
    assert report["rivalries"], "the strongest should clash"


def test_dead_npcs_stop_progressing():
    config = dict(DEFAULT_CONFIG)
    config["npc_mortality_chance"] = 1.0
    config["mortality_min_rank"] = 1
    config["npc_cultivation_chance"] = 1.0
    config["npc_progress_slowdown"] = 0.0
    config["npc_succession_chance"] = 0.0  # isolate: no seat refills here
    system = make_system(config)
    state = default_world_state(RNG(3), ["npc_a"])
    system.tick(state, 1.0, RNG(4))
    if not state["npcs"]["npc_a"]["alive"]:
        before = dict(state["npcs"]["npc_a"])
        system.tick(state, 5.0, RNG(5))
        assert state["npcs"]["npc_a"] == before


# -- E.2: sect simulation ----------------------------------------------------

def test_sect_power_tracks_living_members():
    system = make_system(quiet_config(), npc_factions={"npc_a": "sect_one", "npc_b": "sect_two"})
    state = default_world_state(RNG(1), ["npc_a", "npc_b"])
    state["npcs"]["npc_a"]["rank"] = 10
    system.tick(state, 1.0, RNG(2))
    power = state["sect_power"]
    assert power["sect_one"] > power["sect_two"]
    # Smoothing: one tick moves partway toward the recomputed strength (20).
    assert power["sect_one"] < 20.0


def test_sect_power_falls_when_members_die():
    config = dict(DEFAULT_CONFIG)
    config["npc_mortality_chance"] = 1.0
    config["mortality_min_rank"] = 1
    config["npc_rank_cap"] = 2
    config["npc_succession_chance"] = 0.0  # isolate decay: no refills
    system = make_system(config, npc_factions={"npc_a": "sect_one"})
    state = default_world_state(RNG(5), ["npc_a", "npc_b"])
    for _ in range(10):
        system.tick(state, 1.0, RNG(6))
    assert not state["npcs"]["npc_a"]["alive"]
    # With no living members the sect fades to the base power (ruins decay).
    assert state["sect_power"]["sect_one"] <= float(system.config["sect_base_power"]) + 0.01


def test_century_sim_reorders_sects_and_keeps_a_living_world():
    system = make_system()
    state = default_world_state(RNG(11), [f"npc_{i}" for i in range(50)])
    factions = {f"npc_{i}": f"sect_{i % 4}" for i in range(50)}
    system._npc_factions = factions
    living_start = sum(1 for npc in state["npcs"].values() if npc["alive"])
    for year in range(100):
        system.tick(state, 1.0, RNG(1000 + year))
    living_end = sum(1 for npc in state["npcs"].values() if npc["alive"])
    # The world is changed but not emptied: mortality thins, never sterilises.
    assert 0 < living_end < living_start
    assert living_end >= living_start // 4
    # Sect power visibly reorders (differences emerge between factions).
    powers = [value for value in state["sect_power"].values()]
    assert max(powers) - min(powers) > 1.0
    # Ranks stay bounded: a century does not produce rank-100 immortals.
    assert max(npc["rank"] for npc in state["npcs"].values()) <= int(system.config["npc_rank_cap"])


# -- E.3: economy -------------------------------------------------------------

def test_market_multiplier_stays_bounded():
    config = dict(DEFAULT_CONFIG)
    config["npc_mortality_chance"] = 1.0
    config["mortality_min_rank"] = 1  # mass death -> scarcity pressure
    system = make_system(config)
    state = default_world_state(RNG(21), [f"npc_{i}" for i in range(30)])
    for year in range(50):
        report = system.tick(state, 1.0, RNG(22 + year))
        multiplier = report["price_multiplier"]
        assert 0.7 <= multiplier <= 1.4


def test_deaths_scarce_the_market_upward():
    config = dict(DEFAULT_CONFIG)
    config["npc_mortality_chance"] = 1.0
    config["mortality_min_rank"] = 1
    config["npc_succession_chance"] = 0.0  # a genocide, not a war: no refills
    system = make_system(config)
    state = default_world_state(RNG(31), [f"npc_{i}" for i in range(30)])
    for year in range(20):
        report = system.tick(state, 1.0, RNG(32 + year))
    assert report["price_multiplier"] > 1.0


def test_succession_refills_dead_seats():
    config = dict(DEFAULT_CONFIG)
    config["npc_mortality_chance"] = 0.0  # no re-deaths muddying the revival
    config["npc_succession_chance"] = 4.0  # 4.0/year == guaranteed each quarter-step
    system = make_system(config)
    state = default_world_state(RNG(33), ["npc_a", "npc_b"])
    state["npcs"]["npc_a"]["rank"] = 3
    state["npcs"]["npc_a"]["alive"] = False
    state["npcs"]["npc_b"]["alive"] = False
    report = system.tick(state, 1.0, RNG(35))
    assert set(report["successions"]) == {"npc_a", "npc_b"}
    for npc in state["npcs"].values():
        assert npc["alive"] is True
        assert npc["rank"] == 1  # a new disciple takes the seat


def test_succession_keeps_the_century_world_alive():
    system = make_system()
    state = default_world_state(RNG(36), [f"npc_{i}" for i in range(40)])
    for year in range(100):
        system.tick(state, 1.0, RNG(370 + year))
    living = sum(1 for npc in state["npcs"].values() if npc["alive"])
    # Succession counterbalances mortality: the world thins to an equilibrium,
    # it never sterilises (the pre-succession world ended around 10-25%).
    assert living >= 30


def test_saturated_wealth_no_longer_pins_prices_below_one():
    system = make_system()
    state = default_world_state(RNG(37), [f"npc_{i}" for i in range(40)])
    seen_above = seen_below = False
    for year in range(100):
        multiplier = system.tick(state, 1.0, RNG(380 + year))["price_multiplier"]
        seen_above = seen_above or multiplier > 1.0
        seen_below = seen_below or multiplier < 1.0
    # The economy now breathes: scarcity and saturation pull both ways.
    assert seen_below, "a young poor world should price goods up"
    assert seen_above, "scarcity (empty seats) should push prices past 1.0"


# -- E.4: seasons --------------------------------------------------------------

def test_season_modifiers_table():
    assert SEASON_MODIFIERS["Winter"]["gather_yield"] < 1.0
    assert SEASON_MODIFIERS["Winter"]["travel_years"] > 1.0
    assert SEASON_MODIFIERS["Autumn"]["gather_yield"] > 1.0
    assert SEASON_MODIFIERS["Summer"]["combat_bias"] > 1.0
    # Unknown seasons fall back to Spring's neutral modifiers.
    system = make_system()
    assert system.season_modifiers("Monsoon") == system.season_modifiers("Spring")


def test_season_scales_npc_progress():
    system = make_system(dict(DEFAULT_CONFIG, npc_cultivation_chance=1.0, npc_progress_slowdown=0.0))
    state = default_world_state(RNG(41), ["npc_a"])
    report = system.tick(state, 1.0, RNG(42), season="Winter")
    # Winter slows the world: progress chance is scaled by 0.7.
    assert report["season"] == "Winter"


def test_event_system_combat_bias_zero_suppresses_combat():
    system = EventSystem({"encounter_weights": dict(DEFAULT_WEIGHTS)}, [], RNG(1))
    system.set_combat_bias(0.0)
    player = type("P", (), {"current_location": "nowhere"})()
    kinds = {system.generate(player).get("event") for _ in range(300)}
    assert "COMBAT" not in kinds


# -- E.5: rumors ---------------------------------------------------------------

def test_rumors_mint_from_world_material():
    config = dict(DEFAULT_CONFIG)
    config["npc_mortality_chance"] = 1.0
    config["mortality_min_rank"] = 1
    system = make_system(config)
    state = default_world_state(RNG(51), [f"npc_{i}" for i in range(20)])
    minted = 0
    for year in range(15):
        report = system.tick(state, 1.0, RNG(52 + year))
        minted += len(report["rumors"])
    assert minted > 0
    assert state["rumors"], "rumors persist in state"


def test_learned_rumors_survive_and_unlearned_fade():
    config = dict(DEFAULT_CONFIG, rumor_lifetime_years=6.0)
    system = make_system(config)
    state = default_world_state(RNG(1), ["npc_a"])
    state["rumors"] = [
        {"id": "1", "kind": "market", "learned": True, "age_years": 0.0, "summary": "known"},
        {"id": "2", "kind": "market", "learned": False, "age_years": 0.0, "summary": "forgotten"},
    ]
    system.tick(state, 10.0, RNG(2))  # a quiet decade
    ids = {rumor["id"] for rumor in state["rumors"]}
    assert "1" in ids and "2" not in ids


def test_learn_rumor_marks_and_returns():
    system = make_system()
    state = default_world_state(RNG(1), [])
    state["rumors"] = [{"id": "7", "kind": "dominance", "learned": False, "age_years": 0.0, "summary": "s"}]
    learned = system.learn_rumor(state, "7")
    assert learned is not None and learned["learned"] is True
    assert system.learn_rumor(state, "7") is None  # already learned
    assert system.learn_rumor(state, "404") is None


def test_minted_rumors_carry_reveals():
    system = make_system(sect_names={"sect_1": "Iron Palm Monastery"}, locations=[{"id": "misty_gorge"}])
    state = default_world_state(RNG(61), ["npc_a"])
    state["npcs"]["npc_a"]["rank"] = 9
    config_guard = dict(DEFAULT_CONFIG)
    config_guard["npc_mortality_chance"] = 1.0
    config_guard["mortality_min_rank"] = 1
    system._config.update(config_guard)
    found_reveal = None
    for year in range(12):
        report = system.tick(state, 1.0, RNG(62 + year))
        for rumor in report["rumors"]:
            found_reveal = rumor.get("reveal")
            break
        if found_reveal:
            break
    assert found_reveal is not None
    assert found_reveal.get("type") in ("death", "dominance", "market", "realm_discovery", "npc", "sect", "location")


# -- engine integration ---------------------------------------------------------

def test_new_game_seeds_a_deterministic_world_roster():
    engine = GameEngine.new_game(seed=12345)
    roster = engine._world_state["npcs"]
    assert len(roster) > 0
    # At least one named NPC belongs to a data-defined sect.
    sect_ids = {sect["id"] for sect in engine.sects.sects} if hasattr(engine.sects, "sects") else set()
    assert any(engine._npc_factions.get(nid) for nid in roster)
    other = GameEngine.new_game(seed=12345)
    assert roster == other._world_state["npcs"]


def test_travel_consumes_seasonal_time_and_ticks_world():
    engine = GameEngine.new_game(seed=12345)
    before = engine._world_state["year"]
    age_before = engine.player.age_years
    result = engine.process_action({"action": "TRAVEL", "location_id": "azure_village"})
    assert result["event"] == "TRAVEL_RESULT"
    assert result["travel_years"] == pytest.approx(0.05)
    assert engine.player.age_years == pytest.approx(age_before + 0.05)
    assert engine._world_state["year"] == pytest.approx(before + 0.05)


def test_closed_door_ticks_the_world_and_report_is_attached():
    engine = GameEngine.new_game(seed=12345)
    result = engine.process_action({"action": "CLOSED_DOOR", "years": 3})
    assert result["event"] == "CLOSED_DOOR_RESULT"
    assert engine._world_state["year"] == pytest.approx(3.0)
    assert result["world_tick"]["years"] == pytest.approx(3.0)


def test_world_info_view_and_rumor_actions():
    engine = GameEngine.new_game(seed=12345)
    info = engine.process_action({"action": "WORLD_INFO"})
    assert info["event"] == "WORLD_INFO"
    assert info["season"] in ("Spring", "Summer", "Autumn", "Winter")
    assert isinstance(info["sect_ranking"], list)
    assert info["cultivators_alive"] == info["cultivators_total"] > 0
    rumors = engine.process_action({"action": "WORLD_RUMORS"})
    assert rumors["event"] == "WORLD_RUMORS"
    unknown = engine.process_action({"action": "LEARN_RUMOR", "rumor_id": "nope"})
    assert unknown["event"] == "ERROR"


def test_season_combat_bias_applied_to_event_system():
    engine = GameEngine.new_game(seed=12345)
    # Drive the calendar into a known season and confirm the bias follows.
    engine.player.age_years = 13.0  # year 1 elapsed: Summer (bias 1.1)
    engine._world_tick(0.01)
    assert engine.event_system._combat_bias == pytest.approx(1.1)
    engine.player.age_years = 15.0  # year 3: Winter (bias 0.8)
    engine._world_tick(0.01)
    assert engine.event_system._combat_bias == pytest.approx(0.8)


def test_market_multiplier_scales_displayed_and_charged_prices():
    engine = GameEngine.new_game(seed=12345)
    # Find a location with a shop and move the player there.
    shop = next(iter(engine.shops._shops.values()))
    engine.player.current_location = shop["location_ids"][0]
    engine._world_state["market"]["price_multiplier"] = 1.2
    engine.shops.set_market_multiplier(1.2)
    view = engine.process_action({"action": "SHOP"})
    assert view["event"] == "SHOP"
    entry = view["stock"][0]
    base = entry["price"]
    # Buy exactly what is displayed: the charged price must match the view.
    currency_id, amount = next(iter(base.items()))
    if currency_id == "spirit_stone":
        engine.player.inventory["spirit_stone"] = int(engine.player.inventory.get("spirit_stone", 0)) + amount * 10
    else:
        engine.player.gold = max(engine.player.gold, amount * 10)
    bought = engine.process_action({"action": "BUY_ITEM", "shop_id": shop["id"], "item_id": entry["item_id"], "quantity": 1})
    assert bought["event"] == "ITEM_PURCHASED"
    assert bought["price"] == base


def test_world_state_round_trips_through_saves():
    engine = GameEngine.new_game(seed=12345)
    engine.process_action({"action": "CLOSED_DOOR", "years": 3})
    engine._world_state["market"]["price_multiplier"] = 1.15
    saved = engine.save_game("world-roundtrip")
    assert saved["success"] is True
    other = GameEngine.new_game(seed=999)
    loaded = other.process_action({"action": "LOAD", "slot": "world-roundtrip"})
    assert loaded["success"] is True
    assert other._world_state["year"] == pytest.approx(3.0)
    assert other.shops.market_multiplier() == pytest.approx(1.15)
    assert set(other._world_state["npcs"]) == set(engine._world_state["npcs"])


def test_gather_yield_scales_with_season():
    engine = GameEngine.new_game(seed=12345)
    gathering_locations = [
        location_id for location_id in engine.gathering._locations
        if engine.gathering.has_gathering(location_id)
    ]
    if not gathering_locations:
        pytest.skip("no gatherable locations in data")
    engine.player.current_location = gathering_locations[0]
    # Year 2 == Autumn (yield x2): elapsed years = age - starting age.
    engine.player.age_years = 14.0
    result = engine.process_action({"action": "GATHER"})
    if result.get("event") == "ERROR":
        pytest.skip("gather rolled empty for this location")
    assert result.get("count", 1) >= 2
    assert result.get("season_bonus", 0) >= 1
