"""Give find-only content an authored home (ROADMAP Phase 3 G.2 follow-up).

The dead-content sweep reports items and equipment whose *only* acquisition path
is the rarity-weighted exploration find roll: they exist, they can be stumbled
upon, but no shop, loot table, pool, quest, or realm mentions them. This tool
places every one of them somewhere a player can deliberately go:

* **Equipment** -> the stock of the market whose story tier matches the piece's
  power (rarity, realm and comprehension requirements). Gold for early markets,
  spirit stones for endgame ones, priced off the item's own ``value`` at the
  ratio the hand-authored stock already uses (1 stone per 60 gold).
* **Consumables** (pills, elixirs, decoctions) -> the same tier-matched markets,
  priced off the same worth heuristic ``SellSystem`` uses.
* **Materials** (fang, scale, feather, core, crystal...) -> the loot table of a
  realm-matched random enemy, so they drop from the beasts a cultivator meets.

A piece's tier is read from its own data: equipment from rarity plus its realm /
comprehension requirements, items from the grade words the generated
descriptions carry ("Life Destruction-grade decoction", "Foundation-realm
breakthrough") and, where they do not, from the magnitude bands of its effect.

Placement is deterministic, item-by-item, and spread by load (the least-stocked
candidate market wins), so a re-run after new content lands is additive and the
result never depends on dictionary ordering. An equipment piece is never placed
where the rack already offers a no-more-expensive item that strictly dominates
it -- that would create the very trap option the sweep fails on.

Run from the repo root (idempotent -- already-placed entries are skipped)::

    .venv/Scripts/python.exe tools/seed_world_content.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from game.models.item import Item
from game.systems.sell_system import SellSystem
from game.validation.dead_content import build_report

DATA = Path("game/data")

#: Rarity ladder used to rank a piece of content (matches events.json find_config).
RARITY_ORDER = (
    "mortal_grade",
    "low_spirit_grade",
    "middle_spirit_grade",
    "high_spirit_grade",
    "earth_grade",
    "heaven_grade",
    "dao_grade",
)

#: Grade words the item descriptions carry -> content rank (0-6). Takes the
#: highest match, so "An Life Destruction-grade pill" outranks "Mortal-realm".
GRADE_TOKENS: Tuple[Tuple[str, int], ...] = (
    ("mortal", 0),
    ("houtian", 1),
    ("strength training", 1),
    ("xiantian", 2),
    ("flesh training", 2),
    ("viscera", 3),
    ("foundation", 3),
    ("altering muscle", 4),
    ("bone forging", 4),
    ("revolving core", 4),
    ("tempering marrow", 5),
    ("pulse condensation", 5),
    ("life destruction", 5),
    ("dao palace", 5),
    ("divine sea", 5),
    ("nine stars", 6),
    ("eight gates", 6),
    ("divine transformation", 6),
    ("divine lord", 6),
)

#: Fallback rank bands per effect: sorted (upper_bound, rank) over ``magnitude``.
#: Materials invert (a Mortal-grade fang gives more progress than a Divine Sea
#: one), which is why the description grade is the primary signal for them.
MAGNITUDE_BANDS: Dict[str, Tuple[Tuple[float, int], ...]] = {
    "heal": ((50, 0), (150, 1), (400, 2), (900, 3), (2500, 4), (6000, 5)),
    "restore_hp_qi": ((50, 0), (150, 1), (400, 2), (900, 3), (2500, 4), (6000, 5)),
    "cleanse_poison": ((50, 0), (150, 1), (400, 2), (900, 3), (2500, 4), (6000, 5)),
    "restore_qi": ((20, 0), (60, 1), (150, 2), (400, 3), (900, 4)),
    "breakthrough_aid": ((5, 1), (10, 3), (15, 4), (20, 5)),
    "comprehension_boost": ((3, 1), (8, 3), (15, 4), (22, 5)),
    "lifespan_extension": ((50, 1), (200, 2), (500, 3), (1000, 4), (3000, 5)),
    "body_temper": ((2, 2), (5, 4), (8, 5)),
    "cultivation_boost": ((10, 1), (13, 3), (18, 4), (22, 5)),
}

#: Gold that buys one spirit stone, matching the hand-authored endgame stock.
GOLD_PER_SPIRIT_STONE = 60

#: Chance a realm-matched beast carries a seeded material.
MATERIAL_DROP_CHANCE = 0.12

#: Highest shop rank (story tier 6 markets); content ranks cap out here.
MAX_SHOP_RANK = 5

_MODIFIER_GROUPS = ("stat_modifiers", "cultivation_modifiers", "utility_modifiers")
_STAT_KEYS = frozenset(
    {"strength", "body_strength", "attack", "defense", "max_hp", "max_qi", "speed", "evasion", "comprehension"}
)


def load(name: str):
    with (DATA / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save(name: str, data: Any) -> None:
    with (DATA / name).open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _realm_orders() -> Tuple[List[str], List[str]]:
    body = [realm["id"] for realm in load("cultivation/body_transformation_realms.json")["realms"]]
    essence = [realm["id"] for realm in load("cultivation/essence_gathering_realms.json")["realms"]]
    return body, essence


def _equipment_rank(entry: Dict[str, Any], body_ids: List[str], essence_ids: List[str]) -> int:
    """Rank a piece of gear 0-6 from rarity plus its realm/comprehension gates."""
    rarity = str(entry.get("rarity", "") or "")
    ranks = [float(RARITY_ORDER.index(rarity) if rarity in RARITY_ORDER else 0)]
    requirements = entry.get("requirements", {}) or {}
    body_realm = requirements.get("minimum_body_realm")
    if body_realm in body_ids:
        ranks.append(body_ids.index(body_realm) * len(RARITY_ORDER) / len(body_ids))
    essence_realm = requirements.get("minimum_essence_realm")
    if essence_realm in essence_ids:
        ranks.append(essence_ids.index(essence_realm) * len(RARITY_ORDER) / len(essence_ids))
    comprehension = requirements.get("minimum_comprehension")
    if isinstance(comprehension, (int, float)) and comprehension > 0:
        ranks.append(float(comprehension) * len(RARITY_ORDER) / 30.0)
    return _clamp_rank(max(ranks))


def _item_rank(entry: Dict[str, Any]) -> int:
    """Rank a consumable/material 0-6 from its grade wording, else its magnitude."""
    text = f"{entry.get('name', '')} {entry.get('description', '')}".lower()
    matched = [rank for token, rank in GRADE_TOKENS if token in text]
    if matched:
        return _clamp_rank(max(matched))
    effect = str(entry.get("effect", "") or "")
    bands = MAGNITUDE_BANDS.get(effect)
    magnitude = float(entry.get("magnitude", 0) or 0)
    if bands:
        for upper, rank in bands:
            if magnitude < upper:
                return _clamp_rank(rank)
        return _clamp_rank(len(RARITY_ORDER) - 1)
    return 0


def _clamp_rank(rank: float) -> int:
    return max(0, min(len(RARITY_ORDER) - 1, int(round(rank))))


def _shop_ranks(locations: Dict[str, Dict[str, Any]], shops: List[Dict[str, Any]]) -> Dict[str, int]:
    """Rank each market by the highest story tier it serves."""
    ranks: Dict[str, int] = {}
    for shop in shops:
        tiers = [
            int(locations[location_id].get("story_tier", 1))
            for location_id in shop.get("location_ids", [])
            if location_id in locations
        ]
        ranks[shop["id"]] = min(MAX_SHOP_RANK, max(tiers, default=1) - 1)
    return ranks


def _item_worth(entry: Dict[str, Any]) -> int:
    """Gold worth of an item/equipment entry (its ``value`` or a derived one)."""
    if int(entry.get("value", 0) or 0) > 0:
        return int(entry["value"])
    return int(SellSystem({}).worth(Item.from_dict(entry)))


def _price(entry: Dict[str, Any], shop: Dict[str, Any]) -> Dict[str, int]:
    """Price an entry in the market's own currency, at the established ratio."""
    worth = max(1, _item_worth(entry))
    currencies = {
        currency
        for stock in shop.get("stock", [])
        for currency in (stock.get("price") or {})
    }
    if currencies == {"spirit_stone"}:
        return {"spirit_stone": max(1, round(worth / GOLD_PER_SPIRIT_STONE))}
    return {"gold": worth}


def _stock_item_ids(shop: Dict[str, Any]) -> set:
    return {entry.get("item_id") for entry in shop.get("stock", [])}


def _price_in_gold(price: Dict[str, int]) -> int:
    gold = int(price.get("gold", 0) or 0)
    if gold:
        return gold
    return int(price.get("spirit_stone", 0) or 0) * GOLD_PER_SPIRIT_STONE


def _modifier_value(entry: Dict[str, Any], key: str) -> float:
    for group in _MODIFIER_GROUPS:
        group_data = entry.get(group) or {}
        if key in group_data:
            try:
                return float(group_data[key])
            except (TypeError, ValueError):
                return 0.0
    return 0.0


def _higher_is_better(key: str) -> bool:
    return key in _STAT_KEYS or key.endswith("_bonus")


def _would_be_dominated(candidate: Dict[str, Any], candidate_price: int, shop: Dict[str, Any], equipment: Dict[str, Any]) -> bool:
    """Would stocking ``candidate`` here offer the player a trap option?

    Mirrors the sweep's domination rule: same category, a shared equip slot,
    every comparable stat no better than an existing offer that costs no more,
    and at least one strictly worse. Such a placement is skipped so the sweep
    stays clean.
    """
    for entry in shop.get("stock", []):
        other = equipment.get(entry.get("item_id"))
        if other is None or str(other.get("category")) != str(candidate.get("category")):
            continue
        if not set(other.get("valid_slots", []) or []) & set(candidate.get("valid_slots", []) or []):
            continue
        if _price_in_gold(entry.get("price") or {}) > candidate_price:
            continue
        keys = {
            key
            for group in _MODIFIER_GROUPS
            for item in (other, candidate)
            for key in (item.get(group) or {})
        }
        if any(not _higher_is_better(key) for key in keys):
            return False  # ambiguous direction: not a domination we can defend
        worse_somewhere = any(_modifier_value(other, key) < _modifier_value(candidate, key) for key in keys)
        better_somewhere = any(_modifier_value(other, key) > _modifier_value(candidate, key) for key in keys)
        if better_somewhere and not worse_somewhere:
            return True
    return False


def main() -> None:
    body_ids, essence_ids = _realm_orders()
    locations = {entry["id"]: entry for entry in load("locations.json")}
    shops: List[Dict[str, Any]] = load("shops.json")
    equipment_list: List[Dict[str, Any]] = load("equipment.json")
    equipment = {entry["id"]: entry for entry in equipment_list}
    items_raw = load("items.json")
    items = {entry["id"]: entry for entry in items_raw}
    enemies_raw = load("enemies/random_enemies.json")
    enemies = enemies_raw["enemies"] if isinstance(enemies_raw, dict) and "enemies" in enemies_raw else enemies_raw
    shop_ranks = _shop_ranks(locations, shops)

    report = build_report()
    find_only_equipment: List[str] = report["info"]["find_only_equipment"]
    find_only_items: List[str] = report["info"]["find_only_items"]
    # Materials go to beasts; gear and pills go to markets.
    materials = sorted(
        content_id
        for content_id in find_only_items
        if str((items.get(content_id) or {}).get("type", "material")) == "material"
    )
    market_content = sorted(
        content_id for content_id in find_only_items + find_only_equipment if content_id not in set(materials)
    )

    stock_counts = {shop["id"]: len(shop.get("stock", [])) for shop in shops}
    carrier_counts: Dict[str, int] = {enemy["id"]: 0 for enemy in enemies}

    placed_equipment = 0
    placed_consumables = 0
    rejected: List[str] = []
    for content_id in market_content:
        entry = items.get(content_id) or equipment.get(content_id)
        if entry is None:
            continue
        rank = _equipment_rank(entry, body_ids, essence_ids) if content_id in equipment else _item_rank(entry)
        target = min(MAX_SHOP_RANK, _clamp_rank(rank * MAX_SHOP_RANK / (len(RARITY_ORDER) - 1)))
        candidates = sorted(
            shops,
            key=lambda shop: (
                abs(shop_ranks[shop["id"]] - target),
                stock_counts[shop["id"]],
                shop["id"],
            ),
        )
        chosen: Optional[Dict[str, Any]] = None
        already_stocked = False
        for shop in candidates:
            if content_id in _stock_item_ids(shop):
                already_stocked = True
                break
            price = _price(entry, shop)
            if content_id in equipment and _would_be_dominated(entry, _price_in_gold(price), shop, equipment):
                continue  # never stock a rack with a trap option
            chosen = shop
            break
        if already_stocked:
            continue
        if chosen is None:
            rejected.append(content_id)
            continue
        chosen.setdefault("stock", []).append({"item_id": content_id, "price": _price(entry, chosen)})
        stock_counts[chosen["id"]] += 1
        if content_id in equipment:
            placed_equipment += 1
        else:
            placed_consumables += 1

    placed_materials = 0
    for content_id in materials:
        entry = items[content_id]
        rank = _item_rank(entry)
        target_body_rank = _clamp_rank(rank * (len(body_ids) - 1) / (len(RARITY_ORDER) - 1))
        candidates = sorted(
            enemies,
            key=lambda enemy: (
                abs(body_ids.index(enemy["body_realm_id"]) - target_body_rank)
                if enemy.get("body_realm_id") in body_ids
                else 99,
                carrier_counts[enemy["id"]],
                enemy["id"],
            ),
        )
        carrier = candidates[0]
        ladder = carrier.setdefault("loot_table", [])
        if any(drop.get("item_id") == content_id for drop in ladder):
            continue
        ladder.append({"item_id": content_id, "chance": MATERIAL_DROP_CHANCE, "count": 1})
        carrier_counts[carrier["id"]] += 1
        placed_materials += 1

    save("shops.json", shops)
    save("enemies/random_enemies.json", enemies_raw)

    print(f"find-only at start : equipment {len(find_only_equipment)}, items {len(find_only_items)}")
    print(f"placed equipment   : {placed_equipment}")
    print(f"placed consumables : {placed_consumables}")
    print(f"placed materials   : {placed_materials} (as beast drops)")
    if rejected:
        print(f"rejected (every candidate rack would create a trap): {rejected}")
    print()
    print("Markets after seeding:")
    for shop in sorted(shops, key=lambda shop: (-shop_ranks[shop["id"]], shop["id"])):
        print(f"  rank {shop_ranks[shop['id']]}  {shop['id']:<34} entries {len(shop.get('stock', [])):>3}")
    print("Material carriers:")
    for count, enemy_id in sorted(((count, eid) for eid, count in carrier_counts.items() if count), reverse=True):
        print(f"  {enemy_id:<38} {count}")

    remaining = build_report()
    print()
    print(
        "find-only after run: "
        f"equipment {len(remaining['info']['find_only_equipment'])}, "
        f"items {len(remaining['info']['find_only_items'])}"
    )
    for content_id in remaining["info"]["find_only_equipment"][:20]:
        print(f"  STILL FIND-ONLY EQUIPMENT: {content_id}")
    for content_id in remaining["info"]["find_only_items"][:20]:
        print(f"  STILL FIND-ONLY ITEM: {content_id}")


if __name__ == "__main__":
    main()
