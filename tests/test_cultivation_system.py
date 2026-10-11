"""Tests for the cultivation system's training and breakthrough rules."""
import pytest

from game.core.constants import Action, EventType
from game.core.game_engine import GameEngine
from game.models.cultivation import CultivationState
from game.models.player import Player
from game.models.skill import Skill
from game.systems.cultivation_system import CultivationSystem
from game.utils.data_loader import load_json
from game.utils.rng import RNG


def _make_system(seed=1):
    return CultivationSystem(
        load_json("cultivation/body_transformation_realms.json"),
        load_json("cultivation/essence_gathering_realms.json"),
        load_json("cultivation/cultivation_config.json"),
        RNG(seed=seed),
        load_json("cultivation/martial_talents.json"),
        load_json("cultivation/body_talents.json"),
    )


def _body_progression() -> dict:
    """Body tuning as configured, so a retune cannot silently invalidate a test (C.3)."""
    return load_json("cultivation/cultivation_config.json")["body_progression"]


def _essence_progression() -> dict:
    return load_json("cultivation/cultivation_config.json")["essence_progression"]


def test_training_caps_progress_at_100():
    player = Player(name="Tester", progress=95.0)
    system = _make_system()

    result = system.train(player)

    assert result["event"] == EventType.TRAIN_RESULT
    assert result["track_id"] == "body_transformation"
    assert player.cultivation_state.body.progress <= 100.0
    assert player.progress == player.cultivation_state.body.progress


def test_breakthrough_requires_full_progress():
    player = Player(name="Tester", progress=50.0)
    system = _make_system()

    result = system.breakthrough(player)

    assert result["event"] == EventType.BREAKTHROUGH_RESULT
    assert result["success"] is False
    assert result["reason"] == "INSUFFICIENT_PROGRESS"


def test_training_body_increases_only_body_progress():
    player = Player(name="Tester")
    system = _make_system()

    result = system.train_body(player)

    assert result["track_id"] == "body_transformation"
    assert player.cultivation_state.body.progress > 0
    assert player.cultivation_state.essence.progress == 0.0


def test_body_training_does_not_grant_permanent_strength():
    player = Player(name="Tester")
    system = _make_system()
    before_player_strength = player.body_strength
    before_track_strength = player.cultivation_state.body.body_strength

    result = system.train_body(player)

    assert result["event"] == EventType.TRAIN_RESULT
    assert result["progress_gained"] > 0
    assert result["strain_gained"] > 0
    assert player.body_strength == before_player_strength
    assert player.cultivation_state.body.body_strength == before_track_strength


def test_training_essence_increases_only_essence_progress():
    player = Player(name="Tester")
    player.cultivation_state.body.realm_id = "tempering_marrow"
    system = _make_system()

    result = system.train_essence(player)

    assert result["track_id"] == "essence_gathering"
    assert player.cultivation_state.essence.progress > 0
    assert player.cultivation_state.body.progress == 0.0


def test_essence_training_is_locked_from_a_fresh_start():
    player = Player(name="Tester")
    system = _make_system()

    result = system.train_essence(player)

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "ESSENCE_LOCKED_BY_BODY_PULSE"
    assert player.cultivation_state.essence.progress == 0.0


def test_essence_gate_is_reachable_early_and_read_from_config():
    """C.5: the gate is a design dial in the data, and it opens early in a run."""
    system = _make_system()
    config = load_json("cultivation/cultivation_config.json")
    gate_id = config["essence_unlock"]["body_realm"]

    assert system.essence_unlock_realm_id() == gate_id
    gate = system._body_by_id[gate_id]
    # The gate must leave the Essence track reachable in the opening, not at realm 7
    # where it used to sit ~350 actions and 13 in-game years in.
    assert int(gate.get("order", 99)) <= 2, gate_id


def test_essence_training_stays_locked_until_the_gate_realm_is_complete():
    player = Player(name="Tester")
    system = _make_system()
    # Standing in the gate realm with its requirements unmet is not enough.
    player.cultivation_state.body.realm_id = system.essence_unlock_realm_id()
    player.cultivation_state.body.progress = 0.0

    result = system.train_essence(player)

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "ESSENCE_LOCKED_BY_BODY_PULSE"
    assert player.cultivation_state.essence.progress == 0.0


def test_essence_training_unlocks_once_the_gate_realm_is_complete():
    player = Player(name="Tester")
    system = _make_system()
    body = player.cultivation_state.body
    body.realm_id = system.essence_unlock_realm_id()
    body.progress = system.get_body_required_progress(player)
    body.foundation = 45.0
    body.foundation_stability = 100.0
    body.cultivation_strain = 0.0

    result = system.train_essence(player)

    assert result["event"] == EventType.TRAIN_RESULT
    assert result["track_id"] == "essence_gathering"
    assert player.cultivation_state.essence.progress > 0


def test_body_breakthrough_does_not_advance_essence():
    player = Player(name="Tester")
    player.cultivation_state.body.progress = 100.0
    player.cultivation_state.body.foundation = 20.0
    before_essence = player.cultivation_state.essence.to_dict()
    system = _make_system()

    result = system.attempt_body_breakthrough(player)

    assert result["success"] is True
    assert player.cultivation_state.body.realm_id == "strength_training"
    assert player.cultivation_state.essence.to_dict() == before_essence


def test_successful_body_breakthrough_grants_configured_stats_once(monkeypatch: pytest.MonkeyPatch):
    player = Player(name="Tester")
    player.cultivation_state.body.progress = 100.0
    player.cultivation_state.body.foundation = 20.0
    system = _make_system()
    monkeypatch.setattr(system._rng, "chance", lambda _probability: True)
    before = {
        "max_hp": player.max_hp,
        "attack": player.attack,
        "defense": player.defense,
        "body_strength": player.body_strength,
        "track_strength": player.cultivation_state.body.body_strength,
    }

    result = system.attempt_body_breakthrough(player)
    second = system.attempt_body_breakthrough(player)

    assert result["success"] is True
    assert result["gains"] == {"max_hp": 15, "attack": 2, "defense": 1, "body_strength": 6, "max_qi": 0}
    assert player.max_hp == before["max_hp"] + 15
    assert player.attack == before["attack"] + 2
    assert player.defense == before["defense"] + 1
    assert player.body_strength == before["body_strength"] + 6
    assert player.cultivation_state.body.body_strength == before["track_strength"] + 6
    assert second["success"] is False
    assert player.body_strength == before["body_strength"] + 6


def test_failed_body_breakthrough_does_not_grant_stats_and_applies_penalties(monkeypatch: pytest.MonkeyPatch):
    player = Player(name="Tester")
    system = _make_system()
    required = system.get_body_required_progress(player)
    player.cultivation_state.body.progress = required
    player.cultivation_state.body.foundation = 20.0
    monkeypatch.setattr(system._rng, "chance", lambda _probability: False)
    before_stats = (player.max_hp, player.attack, player.defense, player.body_strength)

    result = system.attempt_body_breakthrough(player)

    tuning = _body_progression()
    assert result["success"] is False
    assert result["reason"] == "FAILED_ATTEMPT"
    assert player.cultivation_state.body.realm_id == "mortal"
    assert (player.max_hp, player.attack, player.defense, player.body_strength) == before_stats
    # A failed attempt keeps momentum but loses the configured share of it.
    assert player.cultivation_state.body.progress == pytest.approx(
        required * tuning["failed_breakthrough_progress_ratio"], abs=0.05
    )
    assert player.cultivation_state.body.cultivation_strain == pytest.approx(
        tuning["failed_breakthrough_strain_gain"]
    )
    assert player.cultivation_state.body.foundation_stability == pytest.approx(
        100.0 - tuning["failed_breakthrough_foundation_loss"]
    )


def _unlock_essence(player: Player) -> None:
    """Advance the body past Pulse Condensation so Essence Gathering is active."""
    player.cultivation_state.body.realm_id = "tempering_marrow"


def test_essence_training_accumulates_strain():
    player = Player(name="Tester")
    _unlock_essence(player)
    system = _make_system()

    result = system.train_essence(player)

    gain = _essence_progression()["training_strain_gain"]
    assert result["track_id"] == "essence_gathering"
    assert result["strain_gained"] == pytest.approx(gain)
    assert result["current_strain"] == pytest.approx(gain)
    assert player.cultivation_state.essence.cultivation_strain == pytest.approx(gain)


def test_essence_breakthrough_blocked_by_high_strain():
    player = Player(name="Tester")
    _unlock_essence(player)
    player.cultivation_state.essence.progress = 999.0
    player.cultivation_state.essence.foundation = 50.0
    player.cultivation_state.essence.foundation_stability = 100.0
    player.cultivation_state.essence.cultivation_strain = 60.0
    system = _make_system()

    result = system.attempt_essence_breakthrough(player)

    assert result["success"] is False
    assert "STRAIN_TOO_HIGH" in result["missing_requirements"]
    assert result["max_allowed_strain"] == 45.0


def test_essence_breakthrough_blocked_by_low_stability():
    player = Player(name="Tester")
    _unlock_essence(player)
    player.cultivation_state.essence.progress = 999.0
    player.cultivation_state.essence.foundation = 50.0
    player.cultivation_state.essence.cultivation_strain = 0.0
    player.cultivation_state.essence.foundation_stability = 10.0
    system = _make_system()

    result = system.attempt_essence_breakthrough(player)

    assert result["success"] is False
    assert "FOUNDATION_UNSTABLE" in result["missing_requirements"]
    assert result["required_foundation_stability"] == 70.0


def test_failed_essence_breakthrough_applies_strain_and_stability_penalties(monkeypatch: pytest.MonkeyPatch):
    player = Player(name="Tester")
    _unlock_essence(player)
    player.cultivation_state.essence.progress = 999.0
    player.cultivation_state.essence.foundation = 50.0
    player.cultivation_state.essence.cultivation_strain = 10.0
    player.cultivation_state.essence.foundation_stability = 100.0
    system = _make_system()
    monkeypatch.setattr(system._rng, "chance", lambda _probability: False)

    result = system.attempt_essence_breakthrough(player)

    tuning = _essence_progression()
    assert result["success"] is False
    assert result["reason"] == "FAILED_ATTEMPT"
    assert player.cultivation_state.essence.cultivation_strain == pytest.approx(
        10.0 + tuning["failed_breakthrough_strain_gain"]
    )
    assert player.cultivation_state.essence.foundation_stability == pytest.approx(
        100.0 - tuning["failed_breakthrough_foundation_loss"]
    )


def test_successful_essence_breakthrough_reduces_strain(monkeypatch: pytest.MonkeyPatch):
    player = Player(name="Tester")
    _unlock_essence(player)
    player.cultivation_state.essence.progress = 999.0
    player.cultivation_state.essence.foundation = 50.0
    player.cultivation_state.essence.cultivation_strain = 20.0
    player.cultivation_state.essence.foundation_stability = 100.0
    system = _make_system()
    monkeypatch.setattr(system._rng, "chance", lambda _probability: True)

    result = system.attempt_essence_breakthrough(player)

    assert result["success"] is True
    assert player.cultivation_state.essence.cultivation_strain == 12.0


def test_stabilise_essence_reduces_strain_and_restores_stability():
    player = Player(name="Tester")
    _unlock_essence(player)
    player.cultivation_state.essence.cultivation_strain = 40.0
    player.cultivation_state.essence.foundation_stability = 50.0
    system = _make_system()

    result = system.stabilise_essence(player)

    tuning = _essence_progression()["stabilise"]
    assert result["event"] == EventType.STABILISE_RESULT
    assert result["strain_reduced"] == pytest.approx(tuning["strain_reduction"])
    assert result["foundation_gained"] == pytest.approx(tuning["foundation_stability_gain"])
    assert player.cultivation_state.essence.cultivation_strain == pytest.approx(
        40.0 - tuning["strain_reduction"]
    )
    assert player.cultivation_state.essence.foundation_stability == pytest.approx(
        50.0 + tuning["foundation_stability_gain"]
    )


def test_essence_breakthrough_does_not_advance_body():
    player = Player(name="Tester")
    player.cultivation_state.body.realm_id = "tempering_marrow"
    player.cultivation_state.essence.progress = 100.0
    player.cultivation_state.essence.foundation = 20.0
    before_body = player.cultivation_state.body.to_dict()
    system = _make_system()

    result = system.attempt_essence_breakthrough(player)

    assert result["success"] is True
    assert player.cultivation_state.essence.substage == "Middle"
    assert player.cultivation_state.body.to_dict() == before_body


def test_required_progress_scales_for_body_and_essence_realms():
    player = Player(name="Tester")
    system = _make_system()

    player.cultivation_state.body.realm_id = "strength_training"
    player.cultivation_state.body.progress = 159.0
    player.cultivation_state.body.foundation = 20.0
    body_result = system.attempt_body_breakthrough(player)

    player.cultivation_state.body.realm_id = "tempering_marrow"
    player.cultivation_state.essence.realm_id = "xiantian"
    player.cultivation_state.essence.progress = 159.0
    player.cultivation_state.essence.foundation = 20.0
    essence_result = system.attempt_essence_breakthrough(player)

    assert system.get_body_required_progress(player) == 1250.0
    assert body_result["success"] is False
    assert body_result["reason"] == "INSUFFICIENT_PROGRESS"
    assert body_result["required_progress"] == 160.0
    assert system.get_essence_required_progress(player) == 160.0
    assert essence_result["success"] is False
    assert essence_result["reason"] == "INSUFFICIENT_PROGRESS"


def test_high_strain_blocks_body_breakthrough():
    player = Player(name="Tester")
    player.cultivation_state.body.progress = 100.0
    player.cultivation_state.body.foundation = 20.0
    player.cultivation_state.body.cultivation_strain = 46.0
    system = _make_system()

    result = system.attempt_body_breakthrough(player)

    assert result["success"] is False
    assert result["reason"] == "STRAIN_TOO_HIGH"
    assert result["current_strain"] == 46.0
    assert result["max_allowed_strain"] == 45.0


def test_low_foundation_stability_blocks_body_breakthrough():
    player = Player(name="Tester")
    player.cultivation_state.body.progress = 100.0
    player.cultivation_state.body.foundation = 20.0
    player.cultivation_state.body.foundation_stability = 69.0
    system = _make_system()

    result = system.attempt_body_breakthrough(player)

    assert result["success"] is False
    assert result["reason"] == "FOUNDATION_UNSTABLE"
    assert result["foundation_stability"] == 69.0
    assert result["required_foundation_stability"] == 70.0


def test_stabilise_foundation_clamps_strain_and_foundation_stability():
    player = Player(name="Tester")
    player.cultivation_state.body.cultivation_strain = 10.0
    player.cultivation_state.body.foundation_stability = 98.0
    system = _make_system()

    result = system.stabilise_foundation(player)

    assert result["event"] == EventType.STABILISE_RESULT
    assert result["strain_reduced"] == 10.0
    assert result["foundation_gained"] == 2.0
    assert result["current_strain"] == 0.0
    assert result["foundation_stability"] == 100.0
    assert result["comprehension_gain"] == 1


def test_body_training_reports_no_daily_counter(monkeypatch: pytest.MonkeyPatch):
    """TM.1: the day clock is gone, so no per-day step-down survives it.

    Strain is the only thing throttling back-to-back training now.
    """
    player = Player(name="Tester")
    system = _make_system()
    monkeypatch.setattr(system._rng, "randint", lambda _low, _high: 0)

    first = system.train_body(player)
    second = system.train_body(player)

    for field in ("daily_cultivation_count", "daily_multiplier", "current_day"):
        assert field not in first, f"{field} should not survive the day clock"
    assert second["strain_gained"] > 0
    assert player.cultivation_state.body.cultivation_strain > 0


def test_breakthrough_gates_publish_what_the_referee_enforces():
    """C.2: the numbers a UI shows are the numbers that refuse the attempt."""
    player = Player(name="Tester")
    system = _make_system()
    player.cultivation_state.body.cultivation_strain = 60.0

    gates = system.gate_numbers(player, system.BODY_TRACK_ID)
    assert gates["strain"] == 60.0
    assert gates["max_allowed_strain"] == 45.0
    assert gates["required_foundation_stability"] == 70.0
    assert gates["foundation_stability"] == 100.0

    verdict = system.breakthrough_gates(player, system.BODY_TRACK_ID)
    assert verdict["can_attempt"] is False
    assert "STRAIN_TOO_HIGH" in verdict["missing_requirements"]
    assert verdict["gates"] == gates


def test_spiritual_root_affects_essence_gain(monkeypatch: pytest.MonkeyPatch):
    system = _make_system()
    monkeypatch.setattr(system._rng, "randint", lambda _low, _high: 0)
    low = Player(name="Low", martial_talent_id="no_talent")
    high = Player(name="High", martial_talent_id="hallowed_lord_grade")
    for player in (low, high):
        player.cultivation_state.body.realm_id = "tempering_marrow"

    low_result = system.train_essence(low)
    high_result = system.train_essence(high)

    assert high_result["progress_gained"] > low_result["progress_gained"]


def test_physique_affects_body_gain_and_strain(monkeypatch: pytest.MonkeyPatch):
    system = _make_system()
    monkeypatch.setattr(system._rng, "randint", lambda _low, _high: 0)
    frail = Player(name="Frail", body_talent_id="hollow_frame")
    strong = Player(name="Strong", body_talent_id="dao_palace_grade")

    frail_result = system.train_body(frail)
    strong_result = system.train_body(strong)

    assert strong_result["progress_gained"] > frail_result["progress_gained"]
    assert strong_result["strain_gained"] < frail_result["strain_gained"]


def test_cultivation_speed_passive_multiplies_training_gain(monkeypatch: pytest.MonkeyPatch):
    skills = {
        "primordial_chaos_meditation_no2": Skill.from_dict(
            {
                "id": "primordial_chaos_meditation_no2",
                "name": "Primordial Chaos Meditation No.2",
                "type": "passive",
                "effect": "cultivation_speed",
                "scaling": 2.9,
            }
        ),
    }
    system = CultivationSystem(
        load_json("cultivation/body_transformation_realms.json"),
        load_json("cultivation/essence_gathering_realms.json"),
        load_json("cultivation/cultivation_config.json"),
        RNG(seed=1),
        load_json("cultivation/martial_talents.json"),
        load_json("cultivation/body_talents.json"),
        skills,
    )
    monkeypatch.setattr(system._rng, "randint", lambda _low, _high: 0)
    normal = Player(name="Normal")
    boosted = Player(name="Boosted", skills=["primordial_chaos_meditation_no2"])

    normal_result = system.train_body(normal)
    boosted_result = system.train_body(boosted)

    assert boosted_result["progress_gained"] > normal_result["progress_gained"]


def test_comprehension_speeds_cultivation_gain(monkeypatch: pytest.MonkeyPatch):
    system = _make_system()
    monkeypatch.setattr(system._rng, "randint", lambda _low, _high: 0)
    normal = Player(name="Normal")
    sharp = Player(name="Sharp", comprehension=110)  # +100 -> +50% speed

    normal_result = system.train_body(normal)
    sharp_result = system.train_body(sharp)

    assert sharp_result["progress_gained"] > normal_result["progress_gained"]
    # Each point above the starting 10 grants +0.5% base-gain speed.
    assert system._comprehension_cultivation_multiplier(normal) == 1.0
    assert system._comprehension_cultivation_multiplier(sharp) == 1.5


def test_convert_exp_to_comprehension_drains_the_bank():
    system = _make_system()
    player = Player(name="Tester", exp=130)

    gained = system.convert_exp_to_comprehension(player)

    assert gained == 2
    assert player.comprehension == 12  # 10 + 2
    assert player.exp == 30  # 130 - 2 * 50


def test_convert_exp_to_comprehension_is_noop_under_threshold():
    system = _make_system()
    player = Player(name="Tester", exp=49)

    assert system.convert_exp_to_comprehension(player) == 0
    assert player.comprehension == 10
    assert player.exp == 49


def test_physique_multiplies_successful_body_breakthrough_stats(monkeypatch: pytest.MonkeyPatch):
    player = Player(name="Tester", body_talent_id="life_gate_grade")
    player.cultivation_state.body.progress = 100.0
    player.cultivation_state.body.foundation = 20.0
    system = _make_system()
    monkeypatch.setattr(system._rng, "chance", lambda _probability: True)

    result = system.attempt_body_breakthrough(player)

    assert result["success"] is True
    assert result["gains"]["max_hp"] == 26
    assert result["gains"]["attack"] == 4
    assert result["gains"]["body_strength"] == 10


#: The opening budget (TASKS.md F.6): a focused run reaches its first realm inside
#: this many actions and this many in-game years.
OPENING_ACTION_BUDGET = 15
OPENING_YEAR_BUDGET = 1.0


def _opening_run(seed: int, max_actions: int = 200) -> tuple[int, float]:
    """Play a focused opening on a fresh run; return ``(actions, in-game years)``.

    The policy is what a competent player does once they know the loop: train while
    the strain gate allows it, stabilise when it does not, and break through the
    moment the gate opens.
    """
    engine = GameEngine.new_game(seed=seed)
    player = engine.player
    body = player.cultivation_state.body
    strain_gain = _body_progression()["training_strain_gain"]
    cap = _body_progression()["max_strain_for_breakthrough"]
    start_age = load_json("cultivation/cultivation_config.json")["lifespan"]["starting_age_years"]

    actions = 0
    while body.realm_id == "mortal" and actions < max_actions:
        if not engine.cultivation._body_missing_requirements(player):
            engine.process_action({"action": Action.BREAKTHROUGH})
        elif body.cultivation_strain + strain_gain <= cap:
            engine.process_action({"action": Action.TRAIN_BODY})
        else:
            engine.process_action({"action": Action.STABILISE_FOUNDATION})
        actions += 1
    return actions, round(player.age_years - float(start_age), 3)


def test_the_first_body_realm_lands_inside_the_opening_budget():
    """C.3: the opening is a fixed cost, not a lottery decided at character creation.

    Before the retune this took a median of 19 actions and 2.5 in-game years, and up
    to 111 actions when the starting roll was unlucky -- more than seven times the
    F.6 budget for a run that had barely begun.
    """
    runs = [_opening_run(seed) for seed in range(1, 41)]

    stalled = [run for run in runs if run[0] >= 200]
    assert stalled == [], f"a run never reached its first realm: {stalled}"

    inside = [
        run for run in runs
        if run[0] <= OPENING_ACTION_BUDGET and run[1] <= OPENING_YEAR_BUDGET
    ]
    share = len(inside) / len(runs)
    assert share >= 0.90, (
        f"only {share:.0%} of openings reached the first realm inside "
        f"{OPENING_ACTION_BUDGET} actions / {OPENING_YEAR_BUDGET}y; "
        f"slowest five: {sorted(runs, reverse=True)[:5]}"
    )


def test_the_starting_body_talent_roll_is_a_bounded_band():
    """The roll sets a run's pace, so it must not span the whole upgrade ladder.

    It used to roll multipliers from 0.25x to 10x -- a 40x spread that put two seeds
    111 actions apart on the same opening. The high tiers stay in the data for the
    upgrade ladder; only the character-creation roll is narrowed.
    """
    entries = load_json("cultivation/body_talents.json")
    rollable = [entry for entry in entries if float(entry.get("roll_weight", 0)) > 0]

    assert rollable, "nothing is rollable at character creation"
    multipliers = [float(entry["body_cultivation_multiplier"]) for entry in rollable]
    assert min(multipliers) >= 0.5, f"a starting body can be crippled: {min(multipliers)}x"
    assert max(multipliers) <= 2.0, f"a starting body can be a jackpot: {max(multipliers)}x"
    assert max(multipliers) / min(multipliers) <= 4.0, (
        f"the starting band is too wide: {min(multipliers)}x to {max(multipliers)}x"
    )
    ladder = [float(entry["body_cultivation_multiplier"]) for entry in entries]
    assert max(ladder) > max(multipliers), "the upgrade ladder lost its ceiling"


def test_the_starting_martial_talent_roll_is_a_bounded_band():
    """The essence side of the same defect: the commonest roll was the worst one.

    ``no_talent`` held 350 of 910 weight while giving 0.1x essence gain and a -0.3
    breakthrough penalty, so the *typical* fresh character was the slowest one, with
    an essence breakthrough that mostly failed.
    """
    entries = load_json("cultivation/martial_talents.json")
    rollable = [entry for entry in entries if float(entry.get("roll_weight", 0)) > 0]

    assert rollable, "nothing is rollable at character creation"
    multipliers = [float(entry["essence_cultivation_multiplier"]) for entry in rollable]
    assert min(multipliers) >= 0.5, f"a starting root is nearly dead: {min(multipliers)}x"
    assert max(multipliers) <= 2.0, f"a starting root is a jackpot: {max(multipliers)}x"
    modifiers = [float(entry["essence_breakthrough_modifier"]) for entry in rollable]
    assert min(modifiers) >= -0.1, (
        f"a starting root is punished on breakthrough: {min(modifiers)}"
    )
    ladder = [float(entry["essence_cultivation_multiplier"]) for entry in entries]
    assert max(ladder) > max(multipliers), "the upgrade ladder lost its ceiling"


def test_the_training_economy_publishes_what_the_actions_would_do():
    """C.6: the trade preview and the actions that execute it agree, by construction.

    Every figure is read from the same config the actions read, so this test drives
    the real actions and checks the preview predicted them.
    """
    engine = GameEngine.new_game(seed=1)
    player = engine.player
    config = load_json("cultivation/cultivation_config.json")
    body_config = config["body_progression"]

    economy = engine.cultivation.training_economy(player, engine.cultivation.BODY_TRACK_ID)
    assert economy["track_id"] == "body_transformation"
    assert economy["train"]["strain_gain"] == body_config["training_strain_gain"]
    assert economy["strain_cap"] == body_config["max_strain_for_breakthrough"]
    assert economy["stabilise"]["strain_reduction"] == body_config["stabilise"]["strain_reduction"]
    assert economy["stabilise"]["foundation_stability_gain"] == body_config["stabilise"]["foundation_stability_gain"]
    assert economy["train"]["years"] == config["lifespan"]["time_costs"]["train_body"]
    assert economy["stabilise"]["years"] == config["lifespan"]["time_costs"]["stabilise"]

    # The preview predicted this session; the session must deliver it.
    predicted = economy["train"]["strain_after"]
    engine.process_action({"action": Action.TRAIN_BODY})
    assert player.cultivation_state.body.cultivation_strain == pytest.approx(predicted)

    # Train to the brink: the preview must say the gate closes, and it must close.
    player.cultivation_state.body.cultivation_strain = 40.0
    economy = engine.cultivation.training_economy(player, engine.cultivation.BODY_TRACK_ID)
    assert economy["train"]["leaves_gate_open"] is False
    assert economy["stabilise"]["strain_after"] == pytest.approx(
        max(0.0, 40.0 - body_config["stabilise"]["strain_reduction"])
    )
    engine.process_action({"action": Action.TRAIN_BODY})
    assert "STRAIN_TOO_HIGH" in engine.cultivation._body_missing_requirements(player)


def test_the_state_view_publishes_the_economy_for_both_tracks():
    """C.6: the client gets the trade without asking; it cannot render what it lacks."""
    engine = GameEngine.new_game(seed=1)
    state = engine.cultivation_service.get_cultivation_state("player")

    for track in ("body_transformation", "essence_gathering"):
        economy = state[track]["economy"]
        assert economy, f"{track} has no economy block"
        assert economy["track_id"] == state[track]["breakthrough"]["track_id"]
        assert "train" in economy and "stabilise" in economy


def test_talent_upgrades_name_where_their_cost_is_sold():
    """C.7: an unaffordable upgrade is a destination, not a dead end.

    The elixir is not consumable on its own -- its only sink is UPGRADE_TALENT -- so
    the Talents view has to carry the acquisition path or the loop is unlearnable.
    """
    engine = GameEngine.new_game(seed=1)
    result = engine.process_action({"action": Action.TALENTS})

    sources = result.get("item_sources", {})
    assert sources, "talents view carries no cost-item sources"
    assert "talent_refining_elixir" in sources
    places = sources["talent_refining_elixir"]
    assert places, "no shop sells the talent elixir anywhere in the world"
    # Every source names a shop and a price, so the player can plan the trip.
    assert all("(" in place and ")" in place for place in places), places

    # Every cost item named by any upgrade option is covered by the map.
    for track in ("martial_upgrades", "body_upgrades"):
        for option in result.get(track, []):
            for cost_id in (option.get("cost") or {}):
                assert cost_id in sources, f"{cost_id} has no listed source"


def test_traits_do_not_bypass_body_hard_requirements():
    player = Player(name="Tester", martial_talent_id="hallowed_lord_grade", body_talent_id="dao_palace_grade")
    system = _make_system()
    # One point short of this realm's threshold, with the best traits in the game.
    player.cultivation_state.body.progress = system.get_body_required_progress(player) - 1.0
    player.cultivation_state.body.foundation = 20.0

    result = system.attempt_body_breakthrough(player)

    assert result["success"] is False
    assert result["reason"] == "INSUFFICIENT_PROGRESS"


def test_pulse_condensation_belongs_only_to_body_track():
    system = _make_system()

    validation = system.validate_cultivation_data()

    assert validation["valid"] is True
    assert "body_pulse_condensation" in system._body_by_id
    assert "essence_pulse_condensation" not in system._essence_by_id


def test_cultivation_state_save_load_preserves_both_tracks():
    state = CultivationState()
    state.body.realm_id = "tempering_marrow"
    state.body.progress = 40.0
    state.body.foundation = 62.5
    state.essence.realm_id = "xiantian"
    state.essence.substage = "Middle"
    state.essence.progress = 68.0

    restored = CultivationState.from_dict(state.to_dict())

    assert restored.body.realm_id == "tempering_marrow"
    assert restored.body.progress == 40.0
    assert restored.essence.realm_id == "xiantian"
    assert restored.essence.substage == "Middle"
    assert restored.essence.progress == 68.0


def test_derived_stats_update_after_breakthrough():
    player = Player(name="Tester")
    player.cultivation_state.body.progress = 100.0
    player.cultivation_state.body.foundation = 20.0
    system = _make_system()
    before = system.calculate_derived_cultivation_stats(player)

    result = system.attempt_body_breakthrough(player)
    after = system.calculate_derived_cultivation_stats(player)

    assert result["success"] is True
    assert after["max_hp"] > before["max_hp"]


def test_invalid_realm_ids_fail_validation():
    system = _make_system()
    save_data = {
        "cultivation": {
            "body_transformation": {"realm_id": "missing_body_realm"},
            "essence_gathering": {"realm_id": "houtian", "substage": "Early"},
        }
    }

    validation = system.validate_cultivation_data(save_data)

    assert validation["valid"] is False
    assert any("unknown body realm" in error for error in validation["errors"])
