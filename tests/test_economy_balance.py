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
