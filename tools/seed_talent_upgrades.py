"""Seed ``upgrade_options`` into the Martial and Body talent tracks.

Each talent upgrades into the *next* talent in its track (the files are already
ordered by tier), so the whole ladder is reachable by spending gold. The
``roll_weight: 0`` entries (upgrade-only divine/apex tiers) therefore become
obtainable exactly through this path, never through a natural starting roll.

Idempotent: running it again regenerates the same chains. It only rewrites the
``upgrade_options`` field; every other authored field is preserved verbatim.

Usage:
    python tools/seed_talent_upgrades.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "game" / "data" / "cultivation"

TRACKS = ("martial_talents.json", "body_talents.json")

# Upgrades cost a rare resource (``talent_refining_elixir``), not gold. The
# quantity scales by the *target's* tier so higher grades demand more elixir.
RESOURCE_ID = "talent_refining_elixir"


def resource_quantity(tier: int) -> int:
    return max(1, tier // 5)


def seed(path: Path) -> None:
    entries = json.loads(path.read_text(encoding="utf-8"))
    for index, entry in enumerate(entries):
        next_entry = entries[index + 1] if index + 1 < len(entries) else None
        if next_entry is None:
            entry["upgrade_options"] = []
            continue
        tier = int(next_entry.get("tier", 1))
        entry["upgrade_options"] = [
            {
                "target_id": next_entry["id"],
                "target_name": next_entry["display_name"],
                "cost": {RESOURCE_ID: resource_quantity(tier)},
            }
        ]
    path.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    for filename in TRACKS:
        seed(DATA / filename)
        print(f"seeded {filename}")


if __name__ == "__main__":
    main()
