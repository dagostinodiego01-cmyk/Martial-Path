"""Choice-driven exploration encounters (ROADMAP B.9).

Covers the contract the encounter layer promises: every roll that carries a
decision becomes a prompt with explained options; ambushes strike first;
hazards and traps hurt but never kill; observing reveals and banks an edge;
and a formation fight only ends when the whole group is down.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from game.core.constants import MODE_COMBAT, MODE_ENCOUNTER, MODE_EXPLORE, Action, EventType
from game.core.game_engine import GameEngine
from game.systems.encounter_system import (
    CHOICE_ORDER,
    COMBAT,
    HAZARD,
    LOOT,
    SPECIAL,
    EncounterSystem,
    foe_power,
)
from game.utils.text import with_article

DATA = json.loads((Path(__file__).resolve().parents[1] / "game" / "data" / "encounters.json").read_text(encoding="utf-8"))

WEAK = {
    "id": "test_mook",
    "name": "Test Mook",
    "body_realm_id": "mortal",
    "essence_realm_id": None,
    "hp": 1,
    "attack": 1,
    "defense": 0,
    "exp_reward": 2,
    "loot_table": [{"item_id": "beast_core", "chance": 1.0, "count": 1}],
}


TOUGH = {**WEAK, "id": "test_tough", "name": "Test Tough", "hp": 5000, "attack": 4}


class StubRNG:
    """A scripted RNG: ``chance`` answers from a script, everything else defaults."""

    def __init__(self, chances=(), default: bool = True) -> None:
        self.chances = list(chances)
        self.default = default

    def chance(self, probability: float) -> bool:
        return self.chances.pop(0) if self.chances else self.default

    def choice(self, items):
        return items[0]

    def weighted_choice(self, items, weights):
        return items[0]

    def randint(self, low, high):
        return low


def _engine(seed: int = 1, rng=None, gold: int = 0) -> GameEngine:
    engine = GameEngine.new_game(player_name="Tester", seed=seed, hardcore=False)
    engine.player.gold = gold
    engine._enemy_templates["test_mook"] = dict(WEAK)
    engine._enemy_templates["test_tough"] = dict(TOUGH)
    engine.encounters._enemies["test_mook"] = dict(WEAK)
    engine.encounters._enemies["test_tough"] = dict(TOUGH)
    if rng is not None:
        engine.encounters = EncounterSystem(DATA, list(engine._enemy_templates.values()), rng)
    return engine


def _install(engine: GameEngine, kind: str = COMBAT, **overrides) -> dict:
    """Park a crafted encounter as the pending one, bypassing the roll."""
    encounter = {
        "id": "enc-test",
        "kind": kind,
        "scene_verb": "encounter_combat" if kind == COMBAT else f"encounter_{kind}",
        "title": "Test",
        "text": "",
        "danger": 1,
        "ambush": False,
        "foes": [],
        "hazard": None,
        "loot": None,
        "special": None,
        "observed": False,
        "resolved": False,
        "context": {"enemy": "Test Mook"},
    }
    encounter.update(overrides)
    engine._pending_encounter = encounter
    engine._mode = MODE_ENCOUNTER
    return encounter


def _option(result: dict, choice_id: str) -> dict:
    options = result.get("options") or (result.get("encounter") or {}).get("options") or []
    return next(option for option in options if option["choice_id"] == choice_id)


# -- data contract --------------------------------------------------------
def test_shipped_encounter_data_covers_the_choice_vocabulary():
    options = DATA["options"]
    for choice_id in CHOICE_ORDER:
        assert choice_id in options, f"choice '{choice_id}' has no label/hint"
        assert options[choice_id]["label"] and options[choice_id]["hint"]
    for hazard in DATA["hazards"]:
        for key in ("id", "name", "text", "effect", "push_base_chance", "defuse_base_chance"):
            assert key in hazard, f"hazard '{hazard.get('id')}' is missing '{key}'"
    for trap in DATA["traps"]:
        assert trap["effect"]["type"] and trap["effect"]["magnitude"] > 0


def test_foe_power_matches_the_displayed_threat_scale():
    assert foe_power(WEAK) == pytest.approx(1 + 1 * 5 + 0 * 3)
    assert foe_power({"hp": 45, "attack": 10, "defense": 3}) == pytest.approx(104)


# -- option gating --------------------------------------------------------
def test_mindless_foe_withholds_parley_and_toll_with_reasons():
    engine = _engine()
    _install(engine, foes=["iron_wolf"])
    prompt = engine._encounter_prompt(engine._pending_encounter)
    talk, pay = _option(prompt, "talk"), _option(prompt, "pay")
    assert talk["available"] is False and talk["reason_code"] == "MINDLESS_FOE" and talk["reason"]
    assert pay["available"] is False and pay["reason_code"] == "MINDLESS_FOE"
    for choice_id in ("fight", "sneak", "observe", "withdraw"):
        assert _option(prompt, choice_id)["available"] is True


def test_unaffordable_toll_is_withheld_and_priced():
    engine = _engine(gold=0)
    _install(engine, foes=["rogue_cultivator"])
    pay = _option(engine._encounter_prompt(engine._pending_encounter), "pay")
    assert pay["available"] is False
    assert pay["reason_code"] == "CANNOT_AFFORD"
    assert pay["cost"]["gold"] > 0
    assert str(pay["cost"]["gold"]) in pay["reason"]


def test_ambush_offers_no_time_to_observe_or_sneak():
    engine = _engine()
    _install(engine, foes=["iron_wolf"], ambush=True)
    prompt = engine._encounter_prompt(engine._pending_encounter)
    for choice_id in ("observe", "sneak"):
        option = _option(prompt, choice_id)
        assert option["available"] is False and option["reason_code"] == "AMBUSHED"
    assert _option(prompt, "withdraw")["available"] is True
    assert _option(prompt, "withdraw")["chance"] > 0


def test_formation_encounter_reports_every_foe_and_its_threat():
    engine = _engine()
    _install(engine, foes=["test_mook", "test_mook", "test_mook"])
    prompt = engine._encounter_prompt(engine._pending_encounter)
    assert prompt["foe_count"] == 3
    assert [foe["name"] for foe in prompt["foes"]] == ["Test Mook"] * 3
    assert prompt["threat"] in {"Low", "Moderate", "High", "Deadly"}


def test_unknown_choice_is_reported_with_its_reason_code():
    engine = _engine()
    _install(engine, foes=["iron_wolf"])
    refused = engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "talk"})
    assert refused["event"] == EventType.ERROR
    assert refused["reason"] == "MINDLESS_FOE"
    assert refused["player_message"]
    assert engine._mode == MODE_ENCOUNTER


def test_actions_other_than_a_choice_are_refused_while_an_encounter_waits():
    engine = _engine()
    _install(engine, foes=["iron_wolf"])
    blocked = engine.process_action({"action": Action.REST})
    assert blocked["event"] == EventType.ERROR and blocked["reason"] == "INVALID_IN_ENCOUNTER"
    assert engine._mode == MODE_ENCOUNTER
    freed = engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "withdraw"})
    assert freed["outcome"] == "WITHDREW"
    assert engine._mode == MODE_EXPLORE
    assert engine._pending_encounter is None


# -- combat choices -------------------------------------------------------
def test_fight_opens_combat_against_the_encounters_foes():
    engine = _engine()
    _install(engine, foes=["iron_wolf", "test_mook"])
    opened = engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "fight"})
    assert opened["event"] == EventType.COMBAT
    assert opened["formation"] is True
    assert [foe["name"] for foe in opened["enemies"]] == ["Iron-Fang Wolf", "Test Mook"]
    assert engine._mode == MODE_COMBAT
    assert engine._pending_encounter is None


def test_ambush_lets_the_foe_strike_before_the_first_turn():
    engine = _engine()
    _install(engine, foes=["iron_wolf"], ambush=True)
    opened = engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "fight"})
    assert opened["ambush"] is True
    assert any(event["actor"] == "ENEMY" for event in opened["turn_events"])


def test_parley_success_avoids_the_fight_and_pays_reputation():
    engine = _engine(rng=StubRNG(default=True))
    _install(engine, foes=["rogue_cultivator"])
    before = engine.player.reputation
    result = engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "talk"})
    assert result["outcome"] == "PARLEY"
    assert result["exp_gained"] > 0
    assert engine.player.reputation == before + 1
    assert engine._mode == MODE_EXPLORE


def test_parley_failure_can_hand_the_foe_the_opening_blow():
    engine = _engine(rng=StubRNG(chances=[False, True], default=True))
    _install(engine, foes=["rogue_cultivator"])
    result = engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "talk"})
    assert result["outcome"] == "OFFENDED" and result["event"] == EventType.COMBAT
    assert result["ambush"] is True


def test_sneak_success_slips_past_and_failure_is_an_ambush():
    avoided = _engine(rng=StubRNG(chances=[True, False], default=True))
    _install(avoided, foes=["iron_wolf"])
    slipped = avoided.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "sneak"})
    assert slipped["outcome"] == "AVOIDED" and slipped["exp_gained"] > 0
    assert avoided._mode == MODE_EXPLORE

    spotted = _engine(rng=StubRNG(default=False))
    _install(spotted, foes=["iron_wolf"])
    caught = spotted.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "sneak"})
    assert caught["outcome"] == "SPOTTED" and caught["event"] == EventType.COMBAT
    assert caught["ambush"] is True


def test_paying_a_toll_spends_the_coin_and_opens_the_road():
    engine = _engine(rng=StubRNG(default=True), gold=500)
    _install(engine, foes=["rogue_cultivator"])
    toll = _option(engine._encounter_prompt(engine._pending_encounter), "pay")["cost"]["gold"]
    paid = engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "pay"})
    assert paid["outcome"] == "TOLL_PAID"
    assert paid["cost"] == {"gold": toll}
    assert engine.player.gold == 500 - toll
    assert engine._mode == MODE_EXPLORE


def test_observe_reveals_the_scene_banks_insight_and_stays_open():
    engine = _engine(rng=StubRNG(default=False))  # no provoke
    hazard = {"id": "qi_miasma", "name": "Stagnant Qi Miasma", "text": "x", "revealed": False,
              "neutralized": False, "studied": False, "effect": {"type": "damage", "magnitude": 16},
              "reward": {}, "defuse_reward": {}, "push_base_chance": 0.65, "defuse_base_chance": 0.47,
              "comprehension_bonus": 0.02}
    _install(engine, foes=["iron_wolf"], hazard=hazard)
    before = engine.player.insight
    prompt = engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "observe"})
    assert prompt["event"] == EventType.ENCOUNTER
    assert engine._mode == MODE_ENCOUNTER
    assert prompt["observed"] is True
    assert prompt["reveal"]["hazard"]["id"] == "qi_miasma"
    assert prompt["outcome"]["insight_gained"] > 0
    assert engine.player.insight > before
    # Reading the scene once is enough: the option closes behind you.
    assert _option(prompt, "observe")["available"] is False
    assert _option(prompt, "observe")["reason_code"] == "ALREADY_OBSERVED"


def test_observed_hazard_turns_on_the_foes_instead_of_the_player():
    engine = _engine(rng=StubRNG(default=False))
    engine.player.hp = engine.player.max_hp
    hazard = {"id": "qi_miasma", "name": "Stagnant Qi Miasma", "text": "x", "revealed": False,
              "neutralized": False, "studied": False, "effect": {"type": "damage", "magnitude": 12},
              "reward": {}, "defuse_reward": {}, "push_base_chance": 0.65, "defuse_base_chance": 0.47,
              "comprehension_bonus": 0.02}
    _install(engine, foes=["iron_wolf", "test_mook"], hazard=hazard)
    engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "observe"})
    opened = engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "fight"})
    struck = [event for event in opened["turn_events"] if event["actor"] == "HAZARD"]
    assert struck and struck[0].get("enemy_name")
    assert engine.player.hp == engine.player.max_hp


def test_provoked_observation_starts_the_fight_unprepared():
    engine = _engine(rng=StubRNG(default=True))  # provoke fires
    _install(engine, foes=["iron_wolf"])
    result = engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "observe"})
    assert result["outcome"] == "PROVOKED" and result["event"] == EventType.COMBAT
    assert result["ambush"] is True


# -- discoveries ---------------------------------------------------------
def test_trapped_find_hurts_until_it_is_examined():
    trap = {"id": "needle_ward", "name": "Needle Ward", "text": "x", "effect": {"type": "damage", "magnitude": 15}, "revealed": False}
    engine = _engine()
    _install(engine, kind=LOOT, loot={"item_id": "beast_core", "count": 1, "trap": trap, "revealed": False})
    taken = engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "take"})
    assert taken["outcome"] == "TAKEN" and taken["damage"] == 15
    assert taken["loot"]["name"]

    safe = _engine()
    _install(safe, kind=LOOT, loot={"item_id": "beast_core", "count": 1, "trap": dict(trap), "revealed": False})
    examined = safe.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "examine"})
    assert examined["event"] == EventType.ENCOUNTER
    assert examined["reveal"]["trap"]["trapped"] is True
    assert _option(examined, "examine")["available"] is False
    clean = safe.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "take"})
    assert clean["outcome"] == "TAKEN" and "damage" not in clean


def test_leaving_a_find_costs_nothing_and_yields_nothing():
    engine = _engine()
    _install(engine, kind=LOOT, loot={"item_id": "beast_core", "count": 1, "trap": None, "revealed": False})
    result = engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "leave"})
    assert result["outcome"] == "LEFT"
    assert "loot" not in result
    assert engine._mode == MODE_EXPLORE


def test_studying_a_site_of_power_reveals_it_and_accepting_applies_it():
    engine = _engine()
    special = {"special_id": "spirit_spring", "text": "A spring of clear qi.", "effect": {"type": "heal", "magnitude": 25}, "revealed": False}
    _install(engine, kind=SPECIAL, special=special)
    engine.player.hp = 10
    studied = engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "study"})
    assert studied["event"] == EventType.ENCOUNTER
    assert studied["reveal"]["special"]["effect"] == {"type": "heal", "magnitude": 25}
    accepted = engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "accept"})
    assert accepted["outcome"] == "ACCEPTED"
    assert engine.player.hp == 35
    assert engine._mode == MODE_EXPLORE


def test_declining_a_site_of_power_resolves_without_effect():
    engine = _engine()
    _install(engine, kind=SPECIAL, special={"special_id": "spirit_spring", "text": "", "effect": {"type": "heal", "magnitude": 25}, "revealed": False})
    engine.player.hp = 10
    declined = engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "decline"})
    assert declined["outcome"] == "DECLINED" and engine.player.hp == 10


# -- hazards -------------------------------------------------------------
def _hazard(magnitude: int = 40) -> dict:
    return {
        "id": "unstable_ground",
        "name": "Unstable Ground",
        "text": "The path is a thin crust over a hollow.",
        "revealed": False,
        "neutralized": False,
        "studied": False,
        "effect": {"type": "damage", "magnitude": magnitude},
        "reward": {"exp": 6},
        "defuse_reward": {"exp": 14, "insight": 2},
        "push_base_chance": 0.68,
        "defuse_base_chance": 0.5,
        "comprehension_bonus": 0.02,
    }


def test_hazard_damage_never_finishes_the_player():
    engine = _engine(rng=StubRNG(default=False))  # every roll fails
    engine.player.hp = 5
    _install(engine, kind=HAZARD, hazard=_hazard(magnitude=900))
    result = engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "push"})
    assert result["outcome"] == "CAUGHT"
    assert engine.player.hp == 1
    assert result["shrugged_off"] is True
    assert engine.player.hp >= 1


def test_crossing_a_hazard_clean_grants_its_reward():
    engine = _engine(rng=StubRNG(default=True))
    _install(engine, kind=HAZARD, hazard=_hazard())
    result = engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "push"})
    assert result["outcome"] == "CROSSED" and result["exp_gained"] == 6
    assert engine.player.hp == engine.player.max_hp


def test_defusing_a_hazard_pays_the_bigger_reward():
    engine = _engine(rng=StubRNG(default=True))
    _install(engine, kind=HAZARD, hazard=_hazard())
    result = engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "defuse"})
    assert result["outcome"] == "DEFUSED"
    assert result["exp_gained"] == 14 and result["insight_gained"] == 2


def test_studying_a_hazard_improves_the_odds_and_then_closes():
    engine = _engine()
    _install(engine, kind=HAZARD, hazard=_hazard())
    before = _option(engine._encounter_prompt(engine._pending_encounter), "defuse")["chance"]
    studied = engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "study"})
    assert studied["event"] == EventType.ENCOUNTER
    after = _option(studied, "defuse")["chance"]
    assert after > before
    assert _option(studied, "study")["available"] is False


def test_failed_defusal_costs_half_and_leaves_nothing_behind():
    engine = _engine(rng=StubRNG(default=False))
    engine.player.hp = engine.player.max_hp
    _install(engine, kind=HAZARD, hazard=_hazard(magnitude=40))
    result = engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "defuse"})
    assert result["outcome"] == "FAILED" and result["damage"] == 20
    assert "exp_gained" not in result


# -- formations ----------------------------------------------------------
def test_a_formation_fight_only_ends_when_the_group_is_down():
    engine = _engine()
    engine.player.attack = 500
    _install(engine, foes=["test_mook", "test_mook", "test_mook"])
    opened = engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "fight"})
    assert len(opened["enemies"]) == 3
    events = []
    for _ in range(10):
        turn = engine.process_action({"action": Action.ATTACK})
        events.extend(turn.get("turn_events") or [])
        if turn.get("event") == EventType.COMBAT_END:
            break
    assert turn["event"] == EventType.COMBAT_END and turn["outcome"] == "VICTORY"
    assert turn["formation"] is True
    assert len(turn["defeated"]) == 3
    assert any(event["action"] == "FOE_STEPS_UP" for event in events)
    assert len(turn["loot"]) == 3  # each mook drops a beast core
    assert engine._mode == MODE_EXPLORE


def test_unfocused_foes_only_press_lightly():
    engine = _engine()
    engine.player.attack = 1  # nothing dies, so the whole group acts
    _install(engine, foes=["test_tough", "test_tough", "test_tough"])
    engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "fight"})
    turn = engine.process_action({"action": Action.ATTACK})
    presses = [event for event in turn["turn_events"] if event["action"] == "PACK_PRESS"]
    assert len(presses) == 2  # capped by ``max_pack_presses``
    # A press is a fraction of the foe's real weight, not a second full attack.
    assert all(event["damage"] < 4 for event in presses)


def test_targeting_switches_who_the_player_is_facing():
    engine = _engine()
    engine.player.attack = 1
    _install(engine, foes=["test_tough", "iron_wolf"])
    opened = engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "fight"})
    assert engine._current_enemy.name == "Test Tough"
    wolf_id = opened["enemies"][1]["name"]
    retargeted = engine.process_action({"action": Action.TARGET_FOE, "foe_id": "iron_wolf"})
    assert retargeted["retargeted"] == "iron_wolf"
    assert engine._current_enemy.id == "iron_wolf"
    assert retargeted["enemy"]["name"] == wolf_id
    missing = engine.process_action({"action": Action.TARGET_FOE, "foe_id": "not_here"})
    assert missing["event"] == EventType.ERROR and missing["reason"] == "FOE_NOT_PRESENT"


def test_pack_foes_are_weaker_and_drop_less_than_the_leader():
    engine = _engine()
    _install(engine, foes=["iron_wolf", "iron_wolf"])
    spawned = engine._spawn_formation(engine._pending_encounter)
    leader, pack = spawned
    assert pack.max_hp < leader.max_hp
    assert pack.attack < leader.attack
    assert pack.exp_reward < leader.exp_reward


# -- integration ---------------------------------------------------------
def test_state_view_exposes_the_pending_encounter_and_the_group():
    engine = _engine()
    _install(engine, foes=["test_mook", "test_mook"])
    state = engine.get_game_state()
    assert state["in_encounter"] is True
    assert state["encounter"]["foe_count"] == 2
    assert state["encounter"]["options"]
    engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": "fight"})
    assert engine.get_game_state()["enemies"][0]["name"] == "Test Mook"


# -- prose ---------------------------------------------------------------
def test_every_enemy_name_gets_a_grammatical_article():
    """Names are data, so the article has to be chosen at runtime.

    A hard-coded "A {name}" reads as "A Iron-Fang Wolf"; this walks the whole
    enemy catalogue to keep the sentence correct for every one of them.
    """
    templates = json.loads(
        (Path(__file__).resolve().parents[1] / "game" / "data" / "enemies" / "random_enemies.json").read_text(encoding="utf-8")
    )
    entries = templates if isinstance(templates, list) else templates.get("enemies", [])
    assert entries, "enemy catalogue is empty"
    for entry in entries:
        name = str(entry.get("name", ""))
        if not name:
            continue
        article = with_article(name)
        first = article.split(" ")[0]
        assert first in {"A", "An"} or article == name
        if first == "An":
            assert name[0].lower() in "aeiou", f"{name!r} should not take 'An'"


def test_combat_descriptor_agrees_with_its_article():
    engine = _engine()
    descriptor = engine.event_system._combat_descriptor({"id": "iron", "name": "Iron-Fang Wolf"})
    assert descriptor["text"] == "An Iron-Fang Wolf lunges from the shadows!"


def test_exploration_rolls_land_on_known_events_for_a_long_run():
    engine = _engine(seed=99)
    seen = set()
    for _ in range(300):
        result = engine.process_action({"action": Action.EXPLORE})
        event = str(result["event"])
        seen.add(event)
        if event == EventType.ENCOUNTER:
            option = next(option for option in result["options"] if option["available"])
            resolved = engine.process_action({"action": Action.ENCOUNTER_CHOICE, "choice_id": option["choice_id"]})
            seen.add(str(resolved["event"]))
            if engine._mode == MODE_COMBAT:
                for _ in range(200):
                    turn = engine.process_action({"action": Action.ATTACK})
                    if str(turn["event"]) == "COMBAT_END":
                        break
        assert str(result["event"]) in {
            "ENCOUNTER", "EXPLORE_RESULT", "CHARACTER_ENCOUNTER", "COMBAT", "COMBAT_END",
            "LOOT", "SPECIAL", "PLAYER_DIED", "HEAL"
        } or result.get("event") is None
        if str(result["event"]) == "PLAYER_DIED":
            break
    assert "ENCOUNTER" in seen
    assert engine._pending_encounter is None or engine._mode == MODE_ENCOUNTER
