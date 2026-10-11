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

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DATA = Path("game/data")
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# A pool stays a curated encounter list, not a grab bag of the whole bestiary.
# The cap is a preference: a crowded danger band (many endgame foes, few zones)
# can push a pool past it rather than leave an enemy stranded.
MAX_POOL_ENTRIES = 8
# Nearby locations considered per enemy before the least-loaded one wins.
CANDIDATE_COUNT = 12
# How far (on the 0-10 danger scale) a zone may sit from an enemy's realm tier.
# Tightened from 3.5 (V.4): the old width let an endgame foe settle in the
# starting woods, which is what the F.1 funnel then had to absorb.
MAX_DANGER_DISTANCE = 2.0
# Combat weight for seeded entries: the middle of the existing 1-5 range.
SEEDED_WEIGHT = 2
# How far a zone's *typical* foe may sit from the danger it advertises (V.4).
BAND = 1.5


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


@dataclass
class ZoneAudit:
    """One zone's difficulty against the danger it advertises (V.4)."""

    location_id: str
    name: str
    story_tier: int
    danger: int
    entries: int
    weakest: float
    strongest: float
    weakest_id: str
    strongest_id: str
    median_danger: float
    in_band_leader: bool
    flags: List[str] = field(default_factory=list)

    @property
    def over_band(self) -> bool:
        return "over_band" in self.flags

    @property
    def under_band(self) -> bool:
        return "under_band" in self.flags

    @property
    def no_in_band_leader(self) -> bool:
        return "no_in_band_leader" in self.flags


def reference_player_power() -> float:
    """The fighting weight a character has on the first turn of a fresh run.

    Uses the engine's own scale (``_player_power``) so the audit and the funnel
    it checks agree on what "the player's power" means.
    """
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from game.core.game_engine import GameEngine

    return float(GameEngine.new_game(player_name="Audit", seed=1)._player_power())


def _weighted_median(values: List[Tuple[float, float]]) -> float:
    """Median of ``(value, weight)`` pairs: the foe a draw *typically* sends."""
    if not values:
        return 0.0
    ordered = sorted(values)
    total = sum(weight for _, weight in ordered)
    running = 0.0
    for value, weight in ordered:
        running += weight
        if running >= total / 2.0:
            return float(value)
    return float(ordered[-1][0])


def audit_zones(reference_power: Optional[float] = None, band: float = BAND) -> List[ZoneAudit]:
    """Check every zone's bestiary against the danger it advertises (V.4).

    Flags, per zone:

    * ``over_band`` -- the typical foe is tougher than the zone's danger says;
    * ``under_band`` -- the zone advertises more danger than it deals;
    * ``no_in_band_leader`` -- a story-tier-1 zone whose whole pool is above a
      fresh player's weight, so the F.1 funnel has nothing to send instead.
    """
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from game.systems.encounter_system import foe_power

    body_ids, essence_ids = realm_orders()
    locations = load("locations.json")
    pools = load("encounter_pools.json")
    enemies = load("enemies/random_enemies.json")
    by_id = {enemy["id"]: enemy for enemy in enemies}
    reference = float(reference_power if reference_power is not None else reference_player_power())

    audit: List[ZoneAudit] = []
    for location in locations:
        location_id = str(location["id"])
        danger = int(location.get("danger_level", 0) or 0)
        tier = int(location.get("story_tier", 1) or 1)
        entries = [
            entry
            for entry in ((pools.get(location_id) or {}).get("combat") or [])
            if entry.get("enemy_id") in by_id
        ]
        if not entries:
            continue
        rows = [
            (
                float(foe_power(by_id[str(entry["enemy_id"])])),
                float(entry.get("weight", 1) or 1),
                str(entry["enemy_id"]),
            )
            for entry in entries
        ]
        median_danger = _weighted_median(
            [(target_danger(by_id[enemy_id], body_ids, essence_ids), weight) for _, weight, enemy_id in rows]
        )
        weakest = min(rows, key=lambda row: (row[0], row[2]))
        strongest = max(rows, key=lambda row: (row[0], row[2]))
        flags: List[str] = []
        if median_danger - danger > band:
            flags.append("over_band")
        if danger - median_danger > band:
            flags.append("under_band")
        if tier <= 1 and weakest[0] > reference:
            flags.append("no_in_band_leader")
        audit.append(
            ZoneAudit(
                location_id=location_id,
                name=str(location.get("name", location_id)),
                story_tier=tier,
                danger=danger,
                entries=len(rows),
                weakest=weakest[0],
                strongest=strongest[0],
                weakest_id=weakest[2],
                strongest_id=strongest[2],
                median_danger=median_danger,
                in_band_leader=weakest[0] <= reference,
                flags=flags,
            )
        )
    return audit


def format_audit(audit: List[ZoneAudit], reference: float) -> str:
    """The difficulty-curve report: per-zone bands, then per-story-tier rollup."""
    lines = [
        "Difficulty curve: enemy power vs zone danger, by story tier (V.4)",
        f"  reference player power (start of a fresh run): {reference:.0f}",
        "",
        f"  {'location':<30} {'tier':>4} {'dngr':>4} {'n':>2} {'typical':>8} {'weakest':>8} {'strongest':>10}  flags",
    ]
    for zone in sorted(audit, key=lambda z: (z.story_tier, z.danger, z.location_id)):
        lines.append(
            f"  {zone.location_id:<30} {zone.story_tier:>4} {zone.danger:>4} {zone.entries:>2} "
            f"{zone.median_danger:>8.2f} {zone.weakest:>8.0f} {zone.strongest:>10.0f}  "
            + (", ".join(zone.flags) if zone.flags else "in band")
        )
    lines.append("")
    lines.append(f"  {'tier':<6} {'zones':>5} {'danger range':>14} {'strongest foe':>13}  flags")
    for tier in sorted({zone.story_tier for zone in audit}):
        zones = [zone for zone in audit if zone.story_tier == tier]
        dangers = [zone.danger for zone in zones]
        flagged = sum(1 for zone in zones if zone.flags)
        lines.append(
            f"  {tier:<6} {len(zones):>5} {min(dangers):>6}-{max(dangers):<7} "
            f"{max(zone.strongest for zone in zones):>13.0f}  {flagged} flagged"
        )
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Seed and audit location encounter pools.")
    parser.add_argument(
        "--audit",
        action="store_true",
        help="report each zone's enemy power against its danger (V.4) and do not write anything",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="with --audit, exit non-zero when a zone is out of band",
    )
    arguments = parser.parse_args(argv)

    if arguments.audit:
        reference = reference_player_power()
        audit = audit_zones(reference)
        print(format_audit(audit, reference))
        over = [zone for zone in audit if zone.over_band]
        blind = [zone for zone in audit if zone.no_in_band_leader]
        soft = [zone for zone in audit if zone.under_band]
        print()
        print(
            f"  {len(audit)} zones | over band {len(over)} | under band {len(soft)} "
            f"| no in-band leader {len(blind)}"
        )
        for zone in over + blind:
            print(f"  FLAG {zone.location_id}: {', '.join(zone.flags)}")
        if arguments.strict and (over or blind):
            print("FAIL: a zone fields foes outside its band", file=sys.stderr)
            return 1
        return 0

    return seed_pools()


def seed_pools() -> int:
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
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
