"""Seed the talent-refining resource (``talent_refining_elixir``) into the world.

The talent upgrade ladder (see ``seed_talent_upgrades.py``) costs this rare
resource, so it must be obtainable. This script distributes it across three
sources, idempotently:

- **Encounters** — high-danger locations (``danger_level >= 4``) gain a rare
  weight-1 elixir in their encounter-pool loot, and high-tier random enemies
  (``hp >= 150``) gain a 3% elixir drop.
- **Masters** — three master NPCs (Steppes Master, Seven Profound Valleys Elder,
  Divine Phoenix Island Founder) gift elixirs as a ``trusted`` relationship
  reward (boon).
- **Shops** — late-game, spirit-stone-priced markets stock the elixir.

Usage:
    python tools/seed_talent_resources.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "game" / "data"
RESOURCE_ID = "talent_refining_elixir"

MASTER_REWARD = {
    "min_tier": "trusted",
    "reward": {
        "item_id": RESOURCE_ID,
        "count": 2,
        "message": "In recognition of your bond, the master parts with a rare elixir that tempers innate talent.",
    },
    "once": True,
}

MASTER_IDS = {
    "steppes_master",
    "seven_profound_valleys_elder",
    "divine_phoenix_island_founder",
}

DANGER_THRESHOLD = 4
ENEMY_HP_THRESHOLD = 150


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def seed_pools() -> int:
    locations = _load(DATA / "locations.json")
    danger = {loc["id"]: int(loc.get("danger_level", 0)) for loc in locations if "id" in loc}
    pools = _load(DATA / "encounter_pools.json")
    added = 0
    for location_id, pool in pools.items():
        if danger.get(location_id, 0) < DANGER_THRESHOLD:
            continue
        loot = pool.setdefault("loot", [])
        if not any(entry.get("item_id") == RESOURCE_ID for entry in loot):
            loot.append({"item_id": RESOURCE_ID, "weight": 1})
            added += 1
    _write(DATA / "encounter_pools.json", pools)
    return added


def seed_enemies() -> int:
    enemies = _load(DATA / "enemies" / "random_enemies.json")
    added = 0
    for enemy in enemies:
        if int(enemy.get("hp", 0)) < ENEMY_HP_THRESHOLD:
            continue
        loot_table = enemy.setdefault("loot_table", [])
        if not any(drop.get("item_id") == RESOURCE_ID for drop in loot_table):
            loot_table.append({"item_id": RESOURCE_ID, "chance": 0.03, "count": 1})
            added += 1
    _write(DATA / "enemies" / "random_enemies.json", enemies)
    return added


def seed_shops() -> int:
    shops = _load(DATA / "shops.json")
    added = 0
    for shop in shops:
        stock = shop.get("stock", [])
        uses_stones = any(
            any(currency == "spirit_stone" for currency in entry.get("price", {}))
            for entry in stock
        )
        if not uses_stones:
            continue
        if any(entry.get("item_id") == RESOURCE_ID for entry in stock):
            continue
        shop.setdefault("stock", []).append(
            {"item_id": RESOURCE_ID, "price": {"spirit_stone": 40}, "stock": 1}
        )
        added += 1
    _write(DATA / "shops.json", shops)
    return added


def seed_masters() -> int:
    added = 0
    for path in (DATA / "characters").glob("*.json"):
        characters = _load(path)
        changed = False
        for character in characters:
            if character.get("id") not in MASTER_IDS:
                continue
            hooks = character.setdefault("gameplay_hooks", {})
            rewards = hooks.setdefault("relationship_rewards", [])
            if not any(
                isinstance(reward, dict) and reward.get("reward", {}).get("item_id") == RESOURCE_ID
                for reward in rewards
            ):
                rewards.append(dict(MASTER_REWARD))
                changed = True
        if changed:
            _write(path, characters)
            added += 1
    return added


def main() -> None:
    pools = seed_pools()
    enemies = seed_enemies()
    shops = seed_shops()
    masters = seed_masters()
    print(f"seeded {RESOURCE_ID}: {pools} encounter pools, {enemies} enemies, {shops} shops, {masters} masters")


if __name__ == "__main__":
    main()
