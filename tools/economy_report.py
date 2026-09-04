"""CLI: print the spirit-stone economy balance report (see game.utils.economy_balance).

Usage (from the project root)::

    python tools/economy_report.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from game.utils.economy_balance import build_ledger


def main() -> None:
    report = build_ledger()
    income = report["stone_income"]
    expenses = report["hall_expenses"]
    verdict = report["verdict"]

    print("=== Spirit-Stone Economy Report ===")
    print()
    print("Assumptions:")
    for key, value in report["assumptions"].items():
        print(f"  {key}: {value}")
    print()
    print(f"Income  ({income['endgame_locations']} endgame locations):")
    print(f"  exploration loot : {income['exploration_loot']}")
    print(f"  combat drops     : {income['combat_drops']}")
    print(f"  quest rewards    : {income['quest_rewards']} (open {income['quest_rewards_open']}, gated {income['quest_rewards_gated']})")
    print(f"  secret realms    : {income['secret_realms']}")
    print(f"  TOTAL            : {income['total']}")
    print()
    print(f"Expenses (tier 5-6 halls, total {expenses['total_stones']} stones, priciest technique {expenses['priciest_technique']}):")
    for hall in expenses["halls"]:
        print(
            f"  {hall['sect_id']:<28} tier {hall['tier']}  "
            f"{hall['technique_count']} techniques  {hall['total_stones']} stones"
        )
    print()
    print("Verdict:")
    print(f"  priciest technique {verdict['priciest_technique']} vs budget {verdict['top_technique_budget']}  -> {'OK' if verdict['top_technique_affordable'] else 'OVER BUDGET'}")
    print(f"  costliest hall {verdict['costliest_hall']} vs budget {verdict['costliest_hall_budget']}  -> {'OK' if verdict['costliest_hall_affordable'] else 'OVER BUDGET'}")
    print(f"  (all endgame halls together: {verdict['all_halls_total_info']} -- informational; a run joins one sect)")
    print(f"  reachable: {verdict['reachable']}")


if __name__ == "__main__":
    main()
