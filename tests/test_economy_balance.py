"""Economy balance acceptance criteria (ROADMAP Phase F follow-up).

The ledger in :mod:`game.utils.economy_balance` derives a run's spirit-stone
income and the tier 5-6 hall expenses from the live data files, then issues a
verdict against budgeted shares. These tests hold the line so future content
waves that add expenses (or remove income) fail loudly instead of silently
pricing the endgame out of reach.

Criteria (see module constants in the ledger):
* the priciest single technique fits a quarter of estimated run income;
* the costliest single hall (a run joins one sect) fits ~90% of it.
"""
from __future__ import annotations

from game.utils.economy_balance import build_ledger


def _verdict() -> dict:
    return build_ledger()["verdict"]


def test_endgame_income_is_positive():
    ledger = build_ledger()
    assert ledger["stone_income"]["total"] > 0
    assert ledger["stone_income"]["endgame_locations"] > 0


def test_all_endgame_income_sources_contribute():
    """Every income stream should carry real weight (no dead sources)."""
    income = build_ledger()["stone_income"]
    assert income["combat_drops"] > 0
    assert income["exploration_loot"] > 0
    assert income["secret_realms"] > 0
    # Quest stones are gated on the endgame chains; they must exist to keep
    # the hall curve honest for a run that rushes the frontier.
    assert income["quest_rewards"] > 0


def test_priciest_technique_is_affordable():
    verdict = _verdict()
    assert verdict["priciest_technique"] > 0
    assert verdict["top_technique_affordable"], (
        f"priciest technique {verdict['priciest_technique']} exceeds "
        f"{verdict['top_technique_budget']} budget"
    )


def test_costliest_hall_is_affordable():
    verdict = _verdict()
    assert verdict["costliest_hall"] > 0
    assert verdict["costliest_hall_affordable"], (
        f"costliest hall {verdict['costliest_hall']} exceeds "
        f"{verdict['costliest_hall_budget']} budget"
    )


def test_endgame_is_reachable():
    verdict = _verdict()
    assert verdict["reachable"], f"verdict: {verdict}"


# -- EC.2: the verdict's target band, locked ----------------------------------

TOP_TECHNIQUE_INCOME_SHARE_BAND = (0.10, 0.35)
COSTLIEST_HALL_INCOME_SHARE_BAND = (0.60, 0.95)


def test_income_to_cost_band_holds():
    """EC.2: income stays in the designed ratio to expenses (~1.3x costliest hall).

    The verdict already compares against budgeted shares; this pins the live
    ratios *inside* those shares so a content wave that quietly halves income
    (or doubles a hall's tuition) trips a balance alarm, not just a reachability
    one. Widen the bands deliberately, with the economy lane's blessing.
    """
    verdict = _verdict()
    income = verdict["income"]
    assert income > 0
    top_ratio = verdict["priciest_technique"] / income
    hall_ratio = verdict["costliest_hall"] / income
    assert (
        TOP_TECHNIQUE_INCOME_SHARE_BAND[0]
        <= top_ratio
        <= TOP_TECHNIQUE_INCOME_SHARE_BAND[1]
    ), f"priciest technique is {top_ratio:.2f} of income (band {TOP_TECHNIQUE_INCOME_SHARE_BAND})"
    assert (
        COSTLIEST_HALL_INCOME_SHARE_BAND[0]
        <= hall_ratio
        <= COSTLIEST_HALL_INCOME_SHARE_BAND[1]
    ), f"costliest hall is {hall_ratio:.2f} of income (band {COSTLIEST_HALL_INCOME_SHARE_BAND})"


def test_currency_guide_exists_and_is_renderable():
    """EC.5: the canonical gold-vs-stones explainer ships from the engine."""
    from game.systems.currency import SUPPORTED_CURRENCIES, currency_guide

    guide = currency_guide()
    described = {entry["id"] for entry in guide["currencies"]}
    assert described == set(SUPPORTED_CURRENCIES), "every currency must be explained"
    for entry in guide["currencies"]:
        assert entry["description"].strip()
        assert entry["sinks"], f"{entry['id']} must name at least one sink"
    assert guide["notes"], "the guide carries the one-line rule of thumb"


def test_currency_economy_validator_passes():
    """EC.5: every currency has a sink, and gold has one in reach per tier."""
    from game.data.registry import GameDataRegistry
    from game.validation import validate_all_game_data
    from game.validation.economy_checks import _validate_currency_economy
    from game.validation.validation_error import ValidationResult

    registry = GameDataRegistry.load()
    result = ValidationResult()
    _validate_currency_economy(registry, result)
    assert result.is_valid, result.format_errors()
    # And the whole-data gate that includes it stays green.
    assert validate_all_game_data(registry).is_valid
