"""Seed example enemy abilities onto a few named foes.

Gives the combat status model (P1) an enemy-side user: poison DoT, heavy
attacks, and stun. Each ability is a ``{type, chance, magnitude}`` entry read by
``CombatSystem._enemy_act``. Idempotent; only the listed ids are touched.

Usage:
    python tools/seed_enemy_abilities.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOES = ROOT / "game" / "data" / "character_enemies" / "named_foes.json"

ABILITIES = {
    "zhu_yan_duel": [
        {"type": "poison", "chance": 0.25, "magnitude": 3},
    ],
    "rogue_cultivator_duel": [
        {"type": "heavy", "chance": 0.3, "magnitude": 1},
    ],
    "xuan_wuji_boss": [
        {"type": "stun", "chance": 0.3, "magnitude": 1},
        {"type": "heavy", "chance": 0.2, "magnitude": 1},
    ],
    "situ_haotian_boss": [
        {"type": "poison", "chance": 0.3, "magnitude": 6},
    ],
}


def main() -> None:
    entries = json.loads(FOES.read_text(encoding="utf-8"))
    by_id = {entry["id"]: entry for entry in entries}
    for foe_id, abilities in ABILITIES.items():
        entry = by_id.get(foe_id)
        if entry is None:
            raise SystemExit(f"unknown named foe '{foe_id}'")
        entry["abilities"] = [dict(ability) for ability in abilities]
    FOES.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"seeded abilities for {len(ABILITIES)} named foes")


if __name__ == "__main__":
    main()
