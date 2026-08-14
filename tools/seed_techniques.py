"""Seed technique manuals and trainers across the content layer.

Until this script exists, ~205 of the 208 skills in ``skills.json`` are
defined but unobtainable: manuals are auto-generated per skill yet seeded
nowhere, and a single trainer teaches three techniques. This generator makes
every skill reachable through the four acquisition paths the engine already
supports:

1. **Trainers** (``trainers.json``) — the canonical "a master teaches it" path.
   Every skill is taught by exactly one trainer, tiered by power and placed at a
   location whose danger band matches the tier. This alone guarantees full
   coverage.
2. **Shops** (``shops.json``) — every manual is also sold, bucketed by rarity
   across the three existing markets and priced by rarity.
3. **Enemy loot** (``enemies/random_enemies.json`` and
   ``character_enemies/named_foes.json``) — enemies drop a manual matching their
   body-realm tier (low drop chance).
4. **Encounter pools** (``encounter_pools.json``) — each location's loot pool
   offers a manual gated by its danger level.

Tiering is deterministic and derived purely from fields already on the skill
(no hand-authored tier column): active techniques tier by ``qi_cost``; passives
tier by a per-effect magnitude heuristic documented in :func:`skill_power`.

The script is idempotent: it strips any previously seeded manual entries before
re-adding them, and it fully regenerates ``technique_manuals.json`` and
``trainers.json`` (which are generator-owned). Run it from the repo root:

    python tools/seed_techniques.py

It rewrites data in place; commit the regenerated JSON alongside the script.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

# tools/seed_techniques.py -> <repo>/game/data
DATA_DIR = Path(__file__).resolve().parent.parent / "game" / "data"

RARITY_ORDER = [
    "mortal_grade",
    "low_spirit_grade",
    "middle_spirit_grade",
    "high_spirit_grade",
    "earth_grade",
    "heaven_grade",
    "dao_grade",
]

# Prices (currency -> amount) by tier index. Trainers charge a premium over the
# equivalent shop manual; early tiers trade in gold, later tiers in spirit stone.
TRAINER_PRICES = [
    {"gold": 50},
    {"gold": 120},
    {"spirit_stone": 4},
    {"spirit_stone": 6},
    {"spirit_stone": 9},
    {"spirit_stone": 14},
    {"spirit_stone": 22},
]
SHOP_PRICES = [
    {"gold": 30},
    {"gold": 60},
    {"spirit_stone": 3},
    {"spirit_stone": 5},
    {"spirit_stone": 8},
    {"spirit_stone": 12},
    {"spirit_stone": 20},
]

# One trainer per tier band, named after the rarity grade it teaches.
TIER_TRAINER_NAMES = [
    "Mortal Arts Master",
    "Spirit Arts Master",
    "Refined Spirit Master",
    "High Spirit Master",
    "Earth Grade Master",
    "Heaven Grade Master",
    "Dao Sovereign",
]

# The early game keeps the hand-authored trainer so its teaching price (and the
# test that relies on it) is preserved.
WANDERING_SWORD_MASTER = {
    "id": "wandering_sword_master",
    "display_name": "Wandering Sword Master",
    "location_ids": ["outer_forest"],
    "description": "A reclusive cultivator who trades pointers on the martial path for coin.",
    "techniques": [
        {"skill_id": "spirit_palm", "price": {"gold": 80}},
    ],
}

# Path-locked techniques: a sect's secret arts are only learnable by a disciple
# whose ``player.path`` matches (set by joining the sect). Kept as a small,
# hand-tuned map so the mechanic stays intentional rather than emergent.
PATH_LOCKED = {
    "phoenix_sword_art": "Divine Phoenix",
    "phoenix_fist": "Divine Phoenix",
    "blood_sea_palm": "Asura Path",
    "nether_aura": "Asura Path",
}

# The three shops are split into early / mid / late rarity bands.
SHOP_TIER_BANDS = {
    "azure_stream_market": (0, 1),
    "sky_fortune_cultivator_market": (2, 3, 4),
    "nine_furnace_auction_house": (5, 6),
}

MANUAL_DROP_CHANCE = 0.05
POOL_LOOT_WEIGHT = 1


def load(filename: str) -> Any:
    with (DATA_DIR / filename).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dump(filename: str, data: Any) -> None:
    path = DATA_DIR / filename
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def skill_power(skill: Dict[str, Any]) -> float:
    """Return a deterministic power score used only to tier manuals.

    Higher = later game. Active techniques tier by qi cost (their primary
    scaling dial); passives tier by a per-effect magnitude heuristic so that a
    +400-year lifespan aura and a 2.9x cultivation-speed meditation rank as the
    endgame treasures they are.
    """
    if skill.get("type") == "active":
        return float(skill.get("qi_cost", 0))
    effect = skill.get("effect", "")
    scaling = float(skill.get("scaling", 1.0))
    if effect == "lifespan":
        return scaling * 0.5
    if effect == "cultivation_speed":
        return (scaling - 1.0) * 200.0
    if effect == "comprehension_gain":
        return scaling * 8.0
    if effect == "qi_cost_reduction":
        return (1.0 - scaling) * 1000.0
    if effect in ("hp_regen", "qi_regen"):
        return scaling * 3.0
    if effect == "crit_chance":
        return (scaling - 1.0) * 200.0
    if effect == "crit_damage":
        return (scaling - 1.0) * 150.0
    # buff_attack / buff_defense / buff_max_hp / buff_max_qi / buff_speed / buff_evasion
    return (scaling - 1.0) * 100.0


def tier_index(power: float) -> int:
    for idx, cap in enumerate((35, 70, 120, 190, 280, 400)):
        if power <= cap:
            return idx
    return len(RARITY_ORDER) - 1


def manual_id(skill: Dict[str, Any]) -> str:
    return f"{skill['id']}_manual"


def main() -> None:
    skills = load("skills.json")
    locations = load("locations.json")
    body_realms = load("cultivation/body_transformation_realms.json")
    events = load("events.json")
    enemies = load("enemies/random_enemies.json")
    named_foes = load("character_enemies/named_foes.json")
    shops = load("shops.json")
    pools = load("encounter_pools.json")

    # -- tiering ---------------------------------------------------------
    tier = {skill["id"]: tier_index(skill_power(skill)) for skill in skills}
    by_tier: Dict[int, List[Dict[str, Any]]] = {t: [] for t in range(len(RARITY_ORDER))}
    for skill in skills:
        by_tier[tier[skill["id"]]].append(skill)

    # body realm order -> tier (clamped); danger -> tier via find_config.
    realm_order = {realm["id"]: int(realm.get("order", 0)) for realm in body_realms["realms"]}
    danger_to_tier = {
        int(danger): int(idx)
        for danger, idx in events.get("find_config", {}).get("danger_max_rarity_index", {}).items()
    }
    location_danger = {loc["id"]: int(loc.get("danger_level", 0)) for loc in locations}
    band_locations: Dict[int, List[str]] = {t: [] for t in range(len(RARITY_ORDER))}
    for loc in locations:
        band = danger_to_tier.get(location_danger.get(loc["id"], 0), 0)
        band_locations[band].append(loc["id"])

    # -- technique_manuals.json (rarity override per skill) --------------
    manuals = [
        {
            "skill_id": skill["id"],
            "name": f"{skill['name']} Manual",
            "rarity": RARITY_ORDER[tier[skill["id"]]],
            "description": f"A manual recording the {skill['name']} technique. Study it to learn the art.",
        }
        for skill in skills
    ]
    dump("technique_manuals.json", manuals)

    # -- trainers.json ---------------------------------------------------
    trainers: List[Dict[str, Any]] = [dict(WANDERING_SWORD_MASTER)]
    covered = {"spirit_palm"}  # taught by the wandering master above
    for t in range(len(RARITY_ORDER)):
        teachable = [s for s in by_tier[t] if s["id"] not in covered]
        if not teachable:
            continue
        home = (band_locations[t] or [locations[-1]["id"]])[0]
        trainers.append(
            {
                "id": f"master_{RARITY_ORDER[t]}",
                "display_name": TIER_TRAINER_NAMES[t],
                "location_ids": [home],
                "description": f"A master of {RARITY_ORDER[t].replace('_', ' ')} techniques who passes on the arts of their tier.",
                "techniques": [
                    _technique_entry(skill, t)
                    for skill in teachable
                ],
            }
        )
        covered.update(skill["id"] for skill in teachable)
    dump("trainers.json", trainers)

    # -- shops.json (manual stock, bucketed by rarity) -------------------
    manual_ids = {manual_id(skill) for skill in skills}
    for shop in shops:
        shop["stock"] = [entry for entry in shop["stock"] if entry.get("item_id") not in manual_ids]
        for t in SHOP_TIER_BANDS.get(shop["id"], ()):
            for skill in by_tier[t]:
                shop["stock"].append(
                    {"item_id": manual_id(skill), "price": dict(SHOP_PRICES[t])}
                )
    dump("shops.json", shops)

    # -- enemy loot tables (random + named foes) -------------------------
    def seed_enemies(entries: List[Dict[str, Any]]) -> None:
        for index, enemy in enumerate(entries):
            enemy_tier = min(len(RARITY_ORDER) - 1, realm_order.get(enemy.get("body_realm_id", ""), 0))
            pool = by_tier[enemy_tier]
            if not pool:
                continue
            skill = pool[index % len(pool)]
            enemy["loot_table"] = [
                drop for drop in enemy.get("loot_table", [])
                if drop.get("item_id") not in manual_ids
            ]
            enemy["loot_table"].append(
                {"item_id": manual_id(skill), "chance": MANUAL_DROP_CHANCE, "count": 1}
            )

    seed_enemies(enemies)
    dump("enemies/random_enemies.json", enemies)
    seed_enemies(named_foes)
    dump("character_enemies/named_foes.json", named_foes)

    # -- encounter pools (danger-gated manual loot) ----------------------
    for index, location_id in enumerate(pools):
        band = danger_to_tier.get(location_danger.get(location_id, 0), 0)
        pool_skills = by_tier[band]
        if not pool_skills:
            continue
        skill = pool_skills[index % len(pool_skills)]
        pool = pools[location_id]
        pool["loot"] = [entry for entry in pool.get("loot", []) if entry.get("item_id") not in manual_ids]
        pool["loot"].append({"item_id": manual_id(skill), "weight": POOL_LOOT_WEIGHT})
    dump("encounter_pools.json", pools)

    # -- summary ---------------------------------------------------------
    print(f"Seeded {len(skills)} skills across {len(tiers_with_skills(by_tier))} tiers.")
    for t in range(len(RARITY_ORDER)):
        print(f"  {RARITY_ORDER[t]:20s} {len(by_tier[t]):3d} skills")
    print(f"Trainers: {len(trainers)} | Shops: {len(shops)} | Pools: {len(pools)}")
    print(f"All skills trainer-covered: {covered == {s['id'] for s in skills}}")


def _technique_entry(skill: Dict[str, Any], tier: int) -> Dict[str, Any]:
    entry: Dict[str, Any] = {"skill_id": skill["id"], "price": dict(TRAINER_PRICES[tier])}
    path = PATH_LOCKED.get(skill["id"])
    if path:
        entry["required_path"] = path
    return entry


def tiers_with_skills(by_tier: Dict[int, List[Dict[str, Any]]]) -> List[int]:
    return [t for t, skills in by_tier.items() if skills]


if __name__ == "__main__":
    main()
