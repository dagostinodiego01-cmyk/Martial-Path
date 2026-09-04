"""Economy tuning pass (one-shot).

Rebalances the tier 5-6 spirit-stone economy so the endgame technique halls
are reachable within a committed run, per the ledger in
``game/utils/economy_balance.py``:

1. Endgame foes that anchor their zone's pool but drop no stones gain a drop
   entry scaled to the existing curve (see STONE_DROPS).
2. Endgame zone-chain quests gain a spirit-stone line in ``rewards.items``
   (the ledger counts these exactly).
3. The three wave-2 secret realms gain a stone payout on ``final_reward`` so
   the new dungeons feed the same economy they sit at the bottom of.
4. The tier-6 rune hall is re-priced onto one ascending ladder (130-180)
   that keeps it the costliest hall while leaving run-income headroom.

Run once from the project root::

    python tools/economy_tune.py

Idempotent: entries already carrying the tuned values are skipped.
"""
from __future__ import annotations

import json
from pathlib import Path

DATA = Path("game/data")

# Endgame (tier 5-6 pool) foes that serve as a zone's primary income but
# drop nothing today -> the drop entry to add. Rates follow the curve set by
# the existing droppers (five_element_warder 0.9x5, zenlight_iron_monk
# 0.85x4, nine_furnace_fire_golem 0.8x4, central_region_duelist 0.7x3):
# tier 6 zones pay more, guards pay more than wildlife.
STONE_DROPS = {
    # -- tier 6 zones -------------------------------------------------------
    "asura_blood_guard": {"item_id": "spirit_stone", "chance": 0.9, "count": 4},
    "vermillion_guard_captain": {"item_id": "spirit_stone", "chance": 0.9, "count": 4},
    "ancient_ruin_sentinel": {"item_id": "spirit_stone", "chance": 0.9, "count": 4},
    "gate_warder": {"item_id": "spirit_stone", "chance": 0.9, "count": 4},
    "gate_duelist": {"item_id": "spirit_stone", "chance": 0.85, "count": 3},
    "rune_qilin": {"item_id": "spirit_stone", "chance": 0.85, "count": 3},
    "rune_tiger": {"item_id": "spirit_stone", "chance": 0.85, "count": 3},
    "elemental_leopard": {"item_id": "spirit_stone", "chance": 0.85, "count": 3},
    "holy_demon_warfiend": {"item_id": "spirit_stone", "chance": 0.8, "count": 3},
    "elemental_warfiend": {"item_id": "spirit_stone", "chance": 0.8, "count": 3},
    # -- tier 5 zones -------------------------------------------------------
    "flame_warfiend": {"item_id": "spirit_stone", "chance": 0.8, "count": 2},
    "temple_hound": {"item_id": "spirit_stone", "chance": 0.75, "count": 2},
    "zenlight_ape": {"item_id": "spirit_stone", "chance": 0.75, "count": 2},
    "zenlight_revenant": {"item_id": "spirit_stone", "chance": 0.7, "count": 2},
    "zen_wolf": {"item_id": "spirit_stone", "chance": 0.7, "count": 2},
    "slaughter_rogue_cultivator": {"item_id": "spirit_stone", "chance": 0.7, "count": 2},
    "blood_bandit": {"item_id": "spirit_stone", "chance": 0.7, "count": 2},
    "blood_golem": {"item_id": "spirit_stone", "chance": 0.6, "count": 2},
    "southern_wilderness_shaman": {"item_id": "spirit_stone", "chance": 0.6, "count": 2},
    # -- shared tier 5-6 secondary foes -------------------------------------
    "gate_wolf": {"item_id": "spirit_stone", "chance": 0.6, "count": 1},
    "planetary_leopard": {"item_id": "spirit_stone", "chance": 0.6, "count": 1},
    "primal_roc": {"item_id": "spirit_stone", "chance": 0.6, "count": 1},
    "zen_lizard": {"item_id": "spirit_stone", "chance": 0.5, "count": 1},
    "five_element_crane": {"item_id": "spirit_stone", "chance": 0.5, "count": 1},
    "south_sea_pirate_cultivator": {"item_id": "spirit_stone", "chance": 0.7, "count": 2},
}

# Endgame zone-chain quests -> spirit stones to add to rewards.items.
QUEST_STONES = {
    "salamander_cores": 8,
    "humming_seam": 10,
    "citadel_unburied": 12,
    "ring_steel_standards": 10,
    "wilds_silent_bells": 8,
    "wilds_strangling_vines": 8,
    "circuit_prime_rubbings": 12,
    "convict_name_verse": 10,
    "seven_landings": 25,
    "gate_terms_proof": 30,
}

# Wave-2 secret realms -> stones added to final_reward.items.
REALM_STONES = {
    "coral_drowned_panopticon": 20,
    "undercroft_circuit_prime": 25,
    "starfield_stair_sanctum": 30,
}

# rune_temple_order techniques -> one ascending tier-6 ladder (130-180) that
# keeps the hall the game's costliest while leaving the run income headroom
# reported by the balance ledger (costliest hall <= 85% of endgame income).
RUNE_HALL_REPRICE = {
    "great_sun_domain_no2": 130,
    "primordial_chaos_seal": 150,
    "void_sutra": 170,
    "rune_circuit_body": 140,
    "five_element_world_seal": 160,
    "gate_star_severing_step": 180,
}


def load(name: str):
    with (DATA / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save(name: str, data) -> None:
    with (DATA / name).open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def tune_enemies() -> int:
    path = "enemies/random_enemies.json"
    raw = load(path)
    enemies = raw["enemies"] if isinstance(raw, dict) and "enemies" in raw else raw
    applied = 0
    for enemy in enemies:
        drop = STONE_DROPS.get(enemy.get("id", ""))
        if drop is None:
            continue
        table = enemy.setdefault("loot_table", [])
        existing = next((e for e in table if e.get("item_id") == "spirit_stone"), None)
        if existing is not None:
            continue
        table.append(dict(drop))
        applied += 1
    save(path, raw)
    return applied


def tune_quests() -> int:
    path = "quests.json"
    raw = load(path)
    quests = raw["quests"] if isinstance(raw, dict) and "quests" in raw else raw
    applied = 0
    for quest in quests:
        stones = QUEST_STONES.get(quest.get("id", ""))
        if stones is None:
            continue
        items = quest.setdefault("rewards", {}).setdefault("items", {})
        current = int(items.get("spirit_stone", 0))
        if current >= stones:
            continue
        items["spirit_stone"] = stones
        applied += 1
    save(path, raw)
    return applied


def tune_realms() -> int:
    path = "secret_realm.json"
    realms = load(path)
    applied = 0
    for realm in realms:
        stones = REALM_STONES.get(realm.get("id", ""))
        if stones is None:
            continue
        items = realm.setdefault("final_reward", {}).setdefault("items", {})
        current = int(items.get("spirit_stone", 0))
        if current >= stones:
            continue
        items["spirit_stone"] = stones
        applied += 1
    save(path, realms)
    return applied


def tune_rune_hall() -> int:
    path = "sects.json"
    raw = load(path)
    sects = raw["sects"] if isinstance(raw, dict) and "sects" in raw else raw
    applied = 0
    for sect in sects:
        if sect.get("id") != "rune_temple_order":
            continue
        for technique in sect.get("techniques", []):
            skill_id = technique.get("skill_id", "")
            price = RUNE_HALL_REPRICE.get(skill_id)
            if price is None:
                continue
            if int(technique.get("price", {}).get("spirit_stone", 0)) <= price:
                continue
            technique["price"] = {"spirit_stone": price}
            applied += 1
    save(path, raw)
    return applied


def main() -> None:
    counts = {
        "enemy_drops_added": tune_enemies(),
        "quest_rewards_added": tune_quests(),
        "realm_rewards_added": tune_realms(),
        "rune_hall_prices_set": tune_rune_hall(),
    }
    print(json.dumps(counts, indent=1))


if __name__ == "__main__":
    main()
