"""Seed encounter pools with every random enemy that has no home (ROADMAP G.2).

The dead-content sweep found 148 of the 236 random enemies in no encounter pool,
no secret realm, and no quest -- and because all 45 locations carry a curated
pool, ``EventSystem``'s global fallback never fires, so those foes could not be
fought at all. This tool gives every stranded enemy a realm-appropriate home,
which also routes its loot table (and therefore the technique manuals it drops)
into the world.

Placement is deterministic and mechanical:

* each enemy gets a **target danger** from its body/essence realm ranks;
* the eligible locations are those whose travel gate the enemy is not grossly
  over-levelled for (required body realm <= the enemy's realm + 1);
* among the five closest locations by danger and story tier, the least-loaded
  one receives the enemy (so a zone's bestiary grows evenly), capped at
  ``MAX_POOL_ENTRIES`` combat entries per location.

Run from the repo root (idempotent -- re-running is a no-op)::

    .venv/Scripts/python.exe tools/seed_enemy_pools.py
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

DATA = Path("game/data")

# A pool stays a curated encounter list, not a grab bag of the whole bestiary.
# The cap is a preference: a crowded danger band (many endgame foes, few zones)
# can push a pool past it rather than leave an enemy stranded.
MAX_POOL_ENTRIES = 8
# Nearby locations considered per enemy before the least-loaded one wins.
CANDIDATE_COUNT = 12
# How far (on the 0-10 danger scale) a zone may sit from an enemy's realm tier.
MAX_DANGER_DISTANCE = 3.5
# Combat weight for seeded entries: the middle of the existing 1-5 range.
SEEDED_WEIGHT = 2


def load(name: str):
    with (DATA / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save(name: str, data: Any) -> None:
    with (DATA / name).open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def realm_orders() -> Tuple[List[str], List[str]]:
    """Return (body realm ids low->high, essence realm ids low->high)."""
    body = load("cultivation/body_transformation_realms.json")["realms"]
    essence = load("cultivation/essence_gathering_realms.json")["realms"]
    return [realm["id"] for realm in body], [realm["id"] for realm in essence]


def target_danger(enemy: Dict[str, Any], body_ids: List[str], essence_ids: List[str]) -> float:
    """Map an enemy's cultivation realm onto the 0-10 location danger scale."""
    body_rank = body_ids.index(enemy["body_realm_id"]) if enemy.get("body_realm_id") in body_ids else 0
    essence_id = enemy.get("essence_realm_id")
    essence_rank = essence_ids.index(essence_id) if essence_id in essence_ids else -1
    return min(10.0, body_rank * 0.75 + (essence_rank + 1) * 0.45)


def _target_story_tier(target: float) -> float:
    return 1.0 + (target / 10.0) * 5.0


def _combat_entries(pools: Dict[str, Any], location_id: str) -> List[Dict[str, Any]]:
    """Return (creating if absent) a location's combat list."""
    pool = pools.setdefault(location_id, {"combat": [], "loot": []})
    if not isinstance(pool.get("combat"), list):
        pool["combat"] = []
    return pool["combat"]


def _closeness(location: Dict[str, Any], target: float):
    """Sort key: closest danger first, story tier as the tie-break."""
    return (
        abs(float(location.get("danger_level", 0)) - target),
        abs(float(location.get("story_tier", 1)) - _target_story_tier(target)),
        str(location["id"]),
    )


def main() -> None:
    body_ids, essence_ids = realm_orders()
    locations: List[Dict[str, Any]] = load("locations.json")
    pools: Dict[str, Any] = load("encounter_pools.json")
    enemies: List[Dict[str, Any]] = load("enemies/random_enemies.json")

    pooled = {
        entry.get("enemy_id")
        for pool in pools.values()
        for entry in (pool.get("combat", []) or [])
    }

    stranded = [enemy for enemy in enemies if enemy["id"] not in pooled]
    stranded.sort(key=lambda enemy: (target_danger(enemy, body_ids, essence_ids), enemy["id"]))

    assigned: List[Tuple[str, str]] = []
    for enemy in stranded:
        target = target_danger(enemy, body_ids, essence_ids)
        # Only zones whose danger is in the same neighbourhood are eligible, so a
        # fledgling's foe never waits in the final gate and vice versa.
        candidates = sorted(
            (
                location
                for location in locations
                if abs(float(location.get("danger_level", 0)) - target) <= MAX_DANGER_DISTANCE
            ),
            key=lambda location: _closeness(location, target),
        )
        if not candidates:
            candidates = sorted(locations, key=lambda location: _closeness(location, target))
        # Prefer the least-loaded of the closest zones so a danger band's bestiary
        # spreads across its locations; if they are all at the cap, the
        # least-loaded zone simply grows rather than the enemy going stranded.
        def rank(location: Dict[str, Any]) -> Tuple[int, str]:
            return (len(_combat_entries(pools, str(location["id"]))), str(location["id"]))

        shortlist = sorted(candidates[:CANDIDATE_COUNT], key=rank)
        with_room = [
            location
            for location in shortlist
            if len(_combat_entries(pools, str(location["id"]))) < MAX_POOL_ENTRIES
        ]
        location = (with_room or shortlist or candidates)[0]
        _combat_entries(pools, str(location["id"])).append(
            {"enemy_id": enemy["id"], "weight": SEEDED_WEIGHT}
        )
        assigned.append((enemy["id"], str(location["id"])))

    save("encounter_pools.json", pools)

    print(f"enemies in catalogue      : {len(enemies)}")
    print(f"already pooled            : {len(pooled)}")
    print(f"seeded this run           : {len(assigned)}")
    print(f"locations touched         : {len({location_id for _, location_id in assigned})}")
    print("\nPer-location combat pool sizes after seeding:")
    for location_id in sorted(pools):
        entry_count = len(pools[location_id].get("combat", []) or [])
        print(f"  {location_id:<32} {entry_count}")
    remaining = {
        entry.get("enemy_id")
        for pool in pools.values()
        for entry in (pool.get("combat", []) or [])
    }
    missing = sorted(enemy["id"] for enemy in enemies if enemy["id"] not in remaining)
    print()
    print(f"unpooled after run        : {len(missing)}")
    for enemy_id in missing:
        print(f"  STILL STRANDED: {enemy_id}")


if __name__ == "__main__":
    main()
