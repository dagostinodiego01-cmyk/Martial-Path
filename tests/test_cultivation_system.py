"""Tests for the cultivation system's training and breakthrough rules."""
import pytest

from game.core.constants import EventType
from game.models.cultivation import CultivationState
from game.models.player import Player
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


def test_essence_training_requires_completed_body_pulse_condensation():
    player = Player(name="Tester")
    system = _make_system()

    result = system.train_essence(player)

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "ESSENCE_LOCKED_BY_BODY_PULSE"
    assert player.cultivation_state.essence.progress == 0.0


def test_essence_training_still_locked_until_body_pulse_requirements_are_met():
    player = Player(name="Tester")
    player.cultivation_state.body.realm_id = "body_pulse_condensation"
    player.cultivation_state.body.progress = 100.0
    system = _make_system()

    result = system.train_essence(player)

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "ESSENCE_LOCKED_BY_BODY_PULSE"
    assert player.cultivation_state.essence.progress == 0.0


def test_essence_training_unlocks_when_body_pulse_requirements_are_met():
    player = Player(name="Tester")
    player.cultivation_state.body.realm_id = "body_pulse_condensation"
    player.cultivation_state.body.progress = 960.0
    player.cultivation_state.body.foundation = 45.0
    system = _make_system()

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
    player.cultivation_state.body.progress = 100.0
    player.cultivation_state.body.foundation = 20.0
    system = _make_system()
    monkeypatch.setattr(system._rng, "chance", lambda _probability: False)
    before_stats = (player.max_hp, player.attack, player.defense, player.body_strength)

    result = system.attempt_body_breakthrough(player)

    assert result["success"] is False
    assert result["reason"] == "FAILED_ATTEMPT"
    assert player.cultivation_state.body.realm_id == "mortal"
    assert (player.max_hp, player.attack, player.defense, player.body_strength) == before_stats
    assert player.cultivation_state.body.progress == 85.0
    assert player.cultivation_state.body.cultivation_strain == 20.0
    assert player.cultivation_state.body.foundation_stability == 90.0


def _unlock_essence(player: Player) -> None:
    """Advance the body past Pulse Condensation so Essence Gathering is active."""
    player.cultivation_state.body.realm_id = "tempering_marrow"


def test_essence_training_accumulates_strain():
    player = Player(name="Tester")
    _unlock_essence(player)
    system = _make_system()

    result = system.train_essence(player)

    assert result["track_id"] == "essence_gathering"
    assert result["strain_gained"] == 10.0
    assert result["current_strain"] == 10.0
    assert player.cultivation_state.essence.cultivation_strain == 10.0


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

    assert result["success"] is False
    assert result["reason"] == "FAILED_ATTEMPT"
    assert player.cultivation_state.essence.cultivation_strain == 28.0
    assert player.cultivation_state.essence.foundation_stability == 90.0


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

    assert result["event"] == EventType.STABILISE_RESULT
    assert result["strain_reduced"] == 18.0
    assert result["foundation_gained"] == 4.0
    assert player.cultivation_state.essence.cultivation_strain == 22.0
    assert player.cultivation_state.essence.foundation_stability == 54.0


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


def test_body_training_diminishing_returns_in_same_day(monkeypatch: pytest.MonkeyPatch):
    player = Player(name="Tester")
    system = _make_system()
    monkeypatch.setattr(system._rng, "randint", lambda _low, _high: 0)

    first = system.train_body(player)
    second = system.train_body(player)

    assert first["daily_cultivation_count"] == 1
    assert first["daily_multiplier"] == 1.0
    assert second["daily_cultivation_count"] == 2
    assert second["daily_multiplier"] == 0.85
    assert second["progress_gained"] < first["progress_gained"]


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


def test_traits_do_not_bypass_body_hard_requirements():
    player = Player(name="Tester", martial_talent_id="hallowed_lord_grade", body_talent_id="dao_palace_grade")
    player.cultivation_state.body.progress = 99.0
    player.cultivation_state.body.foundation = 20.0
    system = _make_system()

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
