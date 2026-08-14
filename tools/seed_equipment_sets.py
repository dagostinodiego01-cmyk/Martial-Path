"""Seed set bonuses and durability onto example equipment.

- The three "Spirit Devouring" treasures form a demonstrative set: wearing 2 or
  3 pieces grants escalating stat bonuses (resolved by ``EquipmentSystem``).
- A handful of early-game items gain a ``durability`` ceiling so the
  repair/break mechanic is reachable in the opening hours.

Idempotent: re-running regenerates the same fields. Only adds the new keys to
the listed ids; every other piece of equipment is left untouched.

Usage:
    python tools/seed_equipment_sets.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EQUIPMENT = ROOT / "game" / "data" / "equipment.json"

# set_id -> [piece ids]
SETS = {
    "spirit_devouring": [
        "spirit_devouring_saber",
        "spirit_devouring_shroud",
        "spirit_devouring_circlet",
    ],
}

# The set bonuses carried by every piece of a set (the system dedupes them and
# applies the strongest met threshold).
SET_BONUSES = {
    "spirit_devouring": [
        {"pieces_required": 2, "stat_modifiers": {"attack": 8, "max_hp": 40}},
        {"pieces_required": 3, "stat_modifiers": {"attack": 20, "defense": 8, "max_hp": 100}},
    ],
}

# item_id -> durability ceiling (repair restores to this; 0 = indestructible).
DURABILITY = {
    "training_sword": 40,
    "patched_leather_armor": 50,
    "worn_travel_boots": 35,
    "spirit_devouring_saber": 60,
    "spirit_devouring_shroud": 50,
    "spirit_devouring_circlet": 40,
}


def main() -> None:
    entries = json.loads(EQUIPMENT.read_text(encoding="utf-8"))
    by_id = {entry["id"]: entry for entry in entries}

    for set_id, piece_ids in SETS.items():
        for piece_id in piece_ids:
            entry = by_id.get(piece_id)
            if entry is None:
                raise SystemExit(f"unknown equipment id '{piece_id}'")
            entry["set_id"] = set_id
            entry["set_bonuses"] = [dict(bonus) for bonus in SET_BONUSES[set_id]]

    for item_id, durability in DURABILITY.items():
        entry = by_id.get(item_id)
        if entry is None:
            raise SystemExit(f"unknown equipment id '{item_id}'")
        entry["durability"] = durability

    EQUIPMENT.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"seeded {len(SETS)} set(s) and {len(DURABILITY)} durability entries")


if __name__ == "__main__":
    main()
