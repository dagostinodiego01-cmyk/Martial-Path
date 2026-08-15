"""Assign a Dao to each named foe in ``character_enemies/named_foes.json``.

Makes the Dao counter-graph matter in character duels: the player's Dao now has
an advantage/disadvantage against specific named foes. Idempotent -- only the
``dao_id`` key is set, and re-running is a no-op.

Usage:
    python tools/seed_enemy_daos.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOES = ROOT / "game" / "data" / "character_enemies" / "named_foes.json"

DAO_BY_FOE = {
    "zhu_yan_duel": "flame_dao",
    "rogue_cultivator_duel": "blood_dao",
    "divine_phoenix_disciple_spar": "flame_dao",
    "ling_sen_duel": "verdant_dao",
    "jiang_baoyun_duel": "tide_dao",
    "ouyang_dihua_duel": "sword_dao",
    "jiang_lanjian_duel": "sword_dao",
    "feng_shen_duel": "space_dao",
    "blood_slaughter_steppes_warrior_arena": "blood_dao",
    "duanmu_qun_duel": "nether_dao",
    "ouyang_boyan_duel": "mountain_dao",
    "situ_yaoyue_duel": "astral_dao",
    "situ_bonan_duel": "sword_dao",
    "holy_demon_continent_demon_duel": "nether_dao",
    "four_divine_kingdoms_prince_or_princess_duel": "karma_dao",
    "steppes_master_trial": "mountain_dao",
    "xuan_wuji_boss": "void_dao",
    "situ_haotian_boss": "astral_dao",
    "yang_yun_boss": "flame_dao",
    "ancient_devil_manifestation": "blood_dao",
    "demon_emperor_avatar": "nether_dao",
}


def main() -> None:
    entries = json.loads(FOES.read_text(encoding="utf-8"))
    by_id = {entry["id"]: entry for entry in entries}
    for foe_id, dao_id in DAO_BY_FOE.items():
        entry = by_id.get(foe_id)
        if entry is None:
            raise SystemExit(f"unknown named foe '{foe_id}'")
        entry["dao_id"] = dao_id
    FOES.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"seeded dao_id for {len(DAO_BY_FOE)} named foes")


if __name__ == "__main__":
    main()
