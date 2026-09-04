"""Economy balance ledger for the spirit-stone endgame.

The tier 5-6 sect technique halls (ROADMAP Phase F) are priced in spirit
stones -- the game's only pure endgame currency. This module answers the
balance question those prices raise: *can a committed run actually afford
them?* Income and expenses are both derived from the live data files, so the
ledger stays honest as content is added.

Income model (all rates read from data, assumptions stated as constants):

* **Exploration loot** -- each explore action at a location draws from its
  encounter pool; the engine's encounter weights give loot a known chance, and
  the pool's weighted ``loot`` entries give spirit stones their share.
* **Combat drops** -- half of all encounters are fights (encounter weights),
  and each enemy's ``loot_table`` carries chance/count per item.
* **Quest rewards** -- stone ``items`` rewards on quest definitions, reported
  split by gate (open vs gated behind a completed quest).
* **Secret realm treasure** -- the stone share of each realm's weighted
  treasure pool plus stone items in ``final_reward``.

Expense is the sum of every tier 5-6 hall technique price, reported per sect
and in total. The verdict compares the two against proportional budgets
(:data:`TOP_TECHNIQUE_INCOME_SHARE`, :data:`FULL_HALLS_INCOME_SHARE`) rather
than pinned constants, so future content waves that add income sources move
the goalposts automatically.

Read-only: the ledger never mutates game state. ``tools/economy_report.py``
prints it; ``tests/test_economy_balance.py`` holds the acceptance criteria.
"""
from __future__ import annotations

from typing import Any, Dict, List

from game.utils.data_loader import load_json

# -- engine constants mirrored here (kept in sync with the engine defaults) --
# data/events.json ``encounter_weights``: how often an explore rolls loot,
# and how often it rolls a fight (whose victory rolls the enemy loot table).
LOOT_CHANCE = 0.25
COMBAT_CHANCE = 0.5

# -- balance assumptions (documented, not hidden) -----------------------------
# A committed player lingers at each endgame location before moving on. This
# drives the loot/drop income estimate; quest and realm income are exact.
ASSUMED_EXPLORES_PER_LOCATION = 40

# Budgets as shares of estimated endgame income. The priciest single
# technique should be a mid-endgame purchase, not the whole run's goal; the
# costliest single hall (a run can join one sect -- one path -- so one hall
# is the realistic ceiling) should fit inside the reachable income with a
# little slack. The grand total across all endgame halls is reported for
# information only: buying every rival hall's arts is impossible by design.
TOP_TECHNIQUE_INCOME_SHARE = 0.25
COSTLIEST_HALL_INCOME_SHARE = 0.90

# Story tiers whose halls are priced in spirit stones (the endgame economy).
ENDGAME_TIERS = (5, 6)


def build_ledger(registry: Any = None) -> Dict[str, Any]:
    """Return the full balance report as a JSON-safe dict.

    ``registry`` is optional and currently unused beyond signature symmetry;
    all figures come straight from the data files so the report can run
    without constructing an engine.
    """
    locations = _locations()
    pools = load_json("encounter_pools.json")
    enemies = _enemies_by_id()
    quests = load_json("quests.json")
    quests = quests["quests"] if isinstance(quests, dict) and "quests" in quests else quests
    realms = load_json("secret_realm.json")

    stone_income = _stone_income(locations, pools, enemies, quests, realms)
    expenses = _hall_expenses()
    verdict = _verdict(stone_income, expenses)

    return {
        "assumptions": {
            "explores_per_location": ASSUMED_EXPLORES_PER_LOCATION,
            "loot_chance": LOOT_CHANCE,
            "combat_chance": COMBAT_CHANCE,
        },
        "stone_income": stone_income,
        "hall_expenses": expenses,
        "verdict": verdict,
    }


# -- income -------------------------------------------------------------------

def _stone_income(
    locations: Dict[str, Dict[str, Any]],
    pools: Dict[str, Any],
    enemies: Dict[str, Dict[str, Any]],
    quests: List[Dict[str, Any]],
    realms: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Estimate the spirit stones a run harvests at endgame locations."""
    endgame = {
        loc_id: loc
        for loc_id, loc in locations.items()
        if int(loc.get("story_tier", 0)) in ENDGAME_TIERS
    }

    loot_per_explore: Dict[str, float] = {}
    drops_per_explore: Dict[str, float] = {}
    for loc_id, _loc in sorted(endgame.items()):
        pool = pools.get(loc_id, {})
        loot_per_explore[loc_id] = _pool_stone_rate(pool.get("loot", []))
        drops_per_explore[loc_id] = _combat_stone_rate(pool.get("combat", []), enemies)

    loot_total = sum(rate for rate in loot_per_explore.values()) * ASSUMED_EXPLORES_PER_LOCATION
    drop_total = sum(rate for rate in drops_per_explore.values()) * ASSUMED_EXPLORES_PER_LOCATION
    quest_total, quest_open, quest_gated = _quest_stone_total(quests)
    realm_total, realm_detail = _realm_stone_total(realms)

    total = loot_total + drop_total + quest_total + realm_total
    return {
        "endgame_locations": len(endgame),
        "exploration_loot": round(loot_total, 1),
        "combat_drops": round(drop_total, 1),
        "quest_rewards": quest_total,
        "quest_rewards_open": quest_open,
        "quest_rewards_gated": quest_gated,
        "secret_realms": realm_total,
        "secret_realms_detail": realm_detail,
        "total": round(total, 1),
        "per_location_per_visit": {
            loc_id: round(
                (loot_per_explore[loc_id] + drops_per_explore[loc_id])
                * ASSUMED_EXPLORES_PER_LOCATION,
                1,
            )
            for loc_id in sorted(endgame)
        },
    }


def _pool_stone_rate(loot_entries: List[Dict[str, Any]]) -> float:
    """Expected stones per loot roll at one location."""
    if not loot_entries:
        return 0.0
    total_weight = sum(max(0, int(entry.get("weight", 1))) for entry in loot_entries)
    if total_weight <= 0:
        return 0.0
    stone_weight = sum(
        max(0, int(entry.get("weight", 1)))
        for entry in loot_entries
        if entry.get("item_id") == "spirit_stone"
    )
    return LOOT_CHANCE * stone_weight / total_weight


def _combat_stone_rate(
    combat_entries: List[Dict[str, Any]], enemies: Dict[str, Dict[str, Any]]
) -> float:
    """Expected stones dropped per fight roll at one location."""
    if not combat_entries:
        return 0.0
    total_weight = sum(max(0, int(entry.get("weight", 1))) for entry in combat_entries)
    if total_weight <= 0:
        return 0.0
    expected = 0.0
    for entry in combat_entries:
        share = max(0, int(entry.get("weight", 1))) / total_weight
        foe = enemies.get(entry.get("enemy_id", ""), {})
        for drop in foe.get("loot_table", []):
            if drop.get("item_id") != "spirit_stone":
                continue
            expected += share * float(drop.get("chance", 0.0)) * int(drop.get("count", 1))
    return COMBAT_CHANCE * expected


def _quest_stone_total(quests: List[Dict[str, Any]]) -> tuple:
    """Sum stone rewards across quests; split open vs gated behind other quests."""
    total = gated = 0
    for quest in quests:
        rewards = quest.get("rewards", {}) or {}
        stones = int((rewards.get("items", {}) or {}).get("spirit_stone", 0))
        if stones <= 0:
            continue
        total += stones
        if (quest.get("requires", {}) or {}).get("completed"):
            gated += stones
    return total, total - gated, gated


def _realm_stone_total(realms: List[Dict[str, Any]]) -> tuple:
    """Stones from secret-realm treasure pools and final rewards."""
    total = 0.0
    detail: List[Dict[str, Any]] = []
    for realm in realms:
        pool = realm.get("treasure_pool", []) or []
        per_room = _pool_stone_rate(pool) / LOOT_CHANCE if pool else 0.0
        # A clear visits ``treasure_rooms`` treasure rooms (deterministic) ...
        clear = per_room * int(realm.get("treasure_rooms", 1))
        # ... plus stone items from the final reward.
        final = int(((realm.get("final_reward", {}) or {}).get("items", {}) or {}).get("spirit_stone", 0))
        clear += final
        if clear > 0:
            detail.append({"realm_id": realm.get("id", ""), "stones_per_clear": round(clear, 1)})
        total += clear
    return round(total, 1), detail


# -- expenses -----------------------------------------------------------------

def _hall_expenses() -> Dict[str, Any]:
    """Every tier 5-6 hall's technique prices, cheapest entry, and totals."""
    sects = load_json("sects.json")
    sects = sects["sects"] if isinstance(sects, dict) and "sects" in sects else sects
    locations = _locations()

    halls: List[Dict[str, Any]] = []
    grand_total = 0
    priciest = 0
    for sect in sects:
        if int(sect.get("tier", 0)) not in ENDGAME_TIERS:
            continue
        techniques = []
        sect_total = 0
        for entry in sect.get("techniques", []):
            price = entry.get("price", {}) or {}
            stones = int(price.get("spirit_stone", 0))
            if stones <= 0:
                continue
            techniques.append({"skill_id": entry.get("skill_id", ""), "stones": stones})
            sect_total += stones
            priciest = max(priciest, stones)
        if not techniques:
            continue
        home_tiers = sorted(
            {
                int(locations[loc_id]["story_tier"])
                for loc_id in sect.get("location_ids", [])
                if loc_id in locations
            }
        )
        halls.append(
            {
                "sect_id": sect.get("id", ""),
                "tier": int(sect.get("tier", 0)),
                "home_story_tiers": home_tiers,
                "technique_count": len(techniques),
                "total_stones": sect_total,
                "techniques": sorted(techniques, key=lambda t: t["stones"]),
            }
        )
        grand_total += sect_total

    halls.sort(key=lambda hall: -hall["total_stones"])
    return {
        "halls": halls,
        "total_stones": grand_total,
        "priciest_technique": priciest,
    }


# -- verdict ------------------------------------------------------------------

def _verdict(stone_income: Dict[str, Any], expenses: Dict[str, Any]) -> Dict[str, Any]:
    """Compare reachable income to hall prices against the budget shares."""
    income = float(stone_income.get("total", 0.0))
    top_budget = income * TOP_TECHNIQUE_INCOME_SHARE
    hall_budget = income * COSTLIEST_HALL_INCOME_SHARE
    priciest = int(expenses.get("priciest_technique", 0))
    halls_total = int(expenses.get("total_stones", 0))
    costliest_hall = max((int(hall.get("total_stones", 0)) for hall in expenses.get("halls", [])), default=0)
    affordable_top = priciest <= top_budget
    affordable_hall = costliest_hall <= hall_budget
    return {
        "income": income,
        "top_technique_budget": round(top_budget, 1),
        "costliest_hall_budget": round(hall_budget, 1),
        "priciest_technique": priciest,
        "costliest_hall": costliest_hall,
        "all_halls_total_info": halls_total,
        "top_technique_affordable": affordable_top,
        "costliest_hall_affordable": affordable_hall,
        "reachable": affordable_top and affordable_hall,
    }


# -- data helpers -------------------------------------------------------------

def _locations() -> Dict[str, Dict[str, Any]]:
    raw = load_json("locations.json")
    entries = raw["locations"] if isinstance(raw, dict) and "locations" in raw else raw
    return {entry["id"]: entry for entry in entries if entry.get("id")}


def _enemies_by_id() -> Dict[str, Dict[str, Any]]:
    raw = load_json("enemies/random_enemies.json")
    entries = raw["enemies"] if isinstance(raw, dict) and "enemies" in raw else raw
    return {entry["id"]: entry for entry in entries if entry.get("id")}
