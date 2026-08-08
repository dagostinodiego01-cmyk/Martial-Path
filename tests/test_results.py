"""Tests for the typed engine result models."""
from game.core.constants import EventType
from game.core.results import (
    ErrorResult,
    HelpResult,
    MeditateResult,
    MessageResult,
    QuitResult,
    RestResult,
    StartingFateAcceptedResult,
    StartingFateRolledResult,
    StabiliseResult,
    TravelResult,
)


def test_to_dict_tags_event_and_includes_fields():
    result = RestResult(healed=10, qi_restored=5, hp=60, qi=25).to_dict()
    assert result == {
        "event": EventType.REST_RESULT,
        "healed": 10,
        "qi_restored": 5,
        "hp": 60,
        "qi": 25,
    }


def test_to_dict_omits_none_optional_fields():
    result = ErrorResult(reason="NO_ROUTE").to_dict()
    assert result == {"event": EventType.ERROR, "reason": "NO_ROUTE"}


def test_to_dict_keeps_provided_optional_fields():
    result = ErrorResult(reason="UNKNOWN_LOCATION", location_id="void").to_dict()
    assert result == {
        "event": EventType.ERROR,
        "reason": "UNKNOWN_LOCATION",
        "location_id": "void",
    }


def test_fieldless_results_serialise_to_event_only():
    assert HelpResult().to_dict() == {"event": EventType.HELP}
    assert QuitResult().to_dict() == {"event": EventType.QUIT}


def test_event_values_are_plain_strings():
    # StrEnum members serialise as their string value.
    assert MessageResult(text="hi").to_dict()["event"] == "MESSAGE"
    assert MeditateResult(qi_restored=1, qi=2, comprehension_gain=0, comprehension=3).to_dict()["event"] == "MEDITATE_RESULT"
    assert TravelResult(location={"id": "home"}).to_dict()["location"] == {"id": "home"}


def test_stabilise_result_serialises_event_and_fields():
    result = StabiliseResult(
        strain_reduced=18.0,
        foundation_gained=4.0,
        current_strain=22.0,
        foundation_stability=84.0,
        comprehension_gain=1,
        comprehension=11,
        progress_gained=0.0,
        progress=40.0,
        required_progress=100.0,
        player_message="Stillness returns.",
    ).to_dict()

    assert result["event"] == EventType.STABILISE_RESULT
    assert result["current_strain"] == 22.0
    assert result["foundation_stability"] == 84.0


def test_starting_fate_results_serialise_trait_views():
    rolled = StartingFateRolledResult(
        spiritual_root_id="middle_grade_spiritual_root",
        physique_id="ordinary_mortal_body",
        spiritual_root={"id": "middle_grade_spiritual_root"},
        physique={"id": "ordinary_mortal_body"},
        requires_fate_acceptance=True,
        player_message="Rolled.",
    ).to_dict()
    accepted = StartingFateAcceptedResult(
        success=True,
        spiritual_root_id="middle_grade_spiritual_root",
        physique_id="ordinary_mortal_body",
        spiritual_root={"id": "middle_grade_spiritual_root"},
        physique={"id": "ordinary_mortal_body"},
        player_message="Accepted.",
    ).to_dict()

    assert rolled["event"] == EventType.STARTING_FATE_ROLLED
    assert accepted["event"] == EventType.STARTING_FATE_ACCEPTED
