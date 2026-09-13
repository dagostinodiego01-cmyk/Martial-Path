"""CLI: print the dead-content sweep (see game.validation.dead_content).

Answers the ROADMAP Phase 3 G.2 question -- is every skill/item/technique/dao/
enemy reachable and meaningful, or is some of it invisible work? Exits non-zero
when anything unreachable or trap-like is found, so it can gate a release.

Usage (from the project root)::

    python tools/dead_content_report.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from game.validation.dead_content import build_report, collect_problems


def main() -> int:
    report = build_report()
    counts = report["counts"]

    print("=== Dead-Content Sweep (ROADMAP G.2) ===")
    print()
    print(
        "Catalogue: "
        + ", ".join(f"{name} {value}" for name, value in counts.items())
    )
    print()

    print("Unreachable (no acquisition path can produce these):")
    for content, ids in report["unreachable"].items():
        mark = "OK" if not ids else f"{len(ids)} DEAD"
        detail = "" if not ids else f"  {ids[:12]}{' ...' if len(ids) > 12 else ''}"
        print(f"  {content:<16} {mark}{detail}")
    print()

    print("Trap options (reachable but meaningless / strictly worse):")
    for kind, entries in report["traps"].items():
        mark = "OK" if not entries else f"{len(entries)} FLAGGED"
        print(f"  {kind:<32} {mark}")
        for entry in entries[:12]:
            if isinstance(entry, dict):
                print(f"      {entry.get('id')}: {entry.get('reason')}")
        if len(entries) > 12:
            print(f"      ... {len(entries) - 12} more")
    print()

    info = report["info"]
    print("Content-quality notes (not failures):")
    print(f"  items reachable only via the find roll      : {len(info['find_only_items'])}")
    print(f"  equipment reachable only via the find roll  : {len(info['find_only_equipment'])}")
    print(f"  daos no enemy carries                       : {info['daos_without_a_foe']}")
    poolless = info["locations_without_a_combat_pool"]
    mark = "OK" if not poolless else f"{len(poolless)} (global fallback active)"
    print(f"  locations with no curated combat pool       : {mark}")
    quests = info["quests"]
    print(
        f"  quests reachable {len(quests['reachable'])}/{quests['total']}"
        f" (auto-start {quests['auto_start']})"
    )
    print()

    problems = collect_problems(report)
    if problems:
        print(f"RESULT: {len(problems)} problems")
        for problem in problems[:40]:
            print(f"  - {problem}")
        if len(problems) > 40:
            print(f"  ... {len(problems) - 40} more")
        return 1
    print("RESULT: clean -- nothing unreachable, no trap options.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
