"""Normalise ``locations.json`` ``available_systems`` to implemented verbs.

The location data declares ~70 distinct ``available_systems`` values, but the
engine only implements a handful of real actions (explore, rest, meditate,
travel, shop, trainers, dialogue, combat, spar/duel, sects, quests). Every other
value is a narrative aspiration that no frontend can actually deliver, which is
the "dead label" problem: the data promises systems the game does not have.

This generator rewrites each location's ``available_systems`` down to the
canonical set defined in ``game.core.constants.AVAILABLE_SYSTEMS``, mapping the
existing narrative verbs onto the closest real action and dropping the rest
(the flavour they carried lives on in each location's ``description``). The
result is honest: every value a frontend reads maps to an action the engine
can actually perform.

Idempotent and deterministic (values are de-duplicated and sorted). Run from the
repo root:

    python tools/normalize_available_systems.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# tools/normalize_available_systems.py -> <repo>
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from game.core.constants import AVAILABLE_SYSTEMS

DATA_DIR = REPO_ROOT / "game" / "data"

#: Map an existing narrative verb onto a canonical implemented verb. Any value
#: not listed here (and not already canonical) is dropped as unimplemented.
_MAP: Dict[str, str] = {
    # canonical identity
    "explore": "explore",
    "rest": "rest",
    "meditate": "meditate",
    "travel": "travel",
    "market": "market",
    "trainers": "trainers",
    "dialogue": "dialogue",
    "combat": "combat",
    "sparring": "sparring",
    "sects": "sects",
    "quests": "quests",
    # exploration / gathering / loot
    "gathering": "explore",
    "risk_reward_exploration": "explore",
    "ruin_exploration": "explore",
    "road_events": "explore",
    "material_farming": "explore",
    "rare_resources": "explore",
    "rare_fire_resources": "explore",
    "survival_chains": "combat",
    # combat / hunting
    "minor_beast_combat": "combat",
    "beast_hunting": "combat",
    "boss_events": "combat",
    "high_level_combat": "combat",
    "major_boss_arc": "combat",
    "ambushes": "combat",
    "pirate_events": "combat",
    "elite_road_encounters": "combat",
    # sparring / duels / tournaments
    "tutorial_duels": "sparring",
    "rival_duels": "sparring",
    "elite_tournaments": "sparring",
    "arena_ladder": "sparring",
    # travel
    "regional_travel": "travel",
    "sea_travel": "travel",
    "high_level_travel": "travel",
    "route_selection": "travel",
    # markets / commerce
    "auction": "market",
    "high_value_auction": "market",
    "merchant_services": "market",
    "merchant_convoys": "market",
    # trainers / technique learning
    "training": "trainers",
    "basic_technique_learning": "trainers",
    "technique_library": "trainers",
    "mentor_events": "trainers",
    "bloodline_training": "trainers",
    "fire_technique_training": "trainers",
    "body_cultivation_rewards": "trainers",
    # meditation / soul
    "meditation_trials": "meditate",
    "soul_tempering": "meditate",
    # dialogue / social
    "rumours": "dialogue",
    "family_dialogue": "dialogue",
    "early_relationships": "dialogue",
    "dangerous_diplomacy": "dialogue",
    # sects
    "academy_rank": "sects",
    "sect_entry_trial": "sects",
    "disciple_rank": "sects",
    "inner_disciple_events": "sects",
    "sect_reputation": "sects",
    # quests
    "city_quests": "quests",
    "royal_quests": "quests",
    "sect_quests": "quests",
    "world_quest_completion": "quests",
}


def _normalise(values: List[str]) -> List[str]:
    mapped = {_MAP[v] for v in values if v in _MAP}
    return sorted(mapped)


def main() -> None:
    path = DATA_DIR / "locations.json"
    with path.open("r", encoding="utf-8") as handle:
        locations: List[Dict[str, Any]] = json.load(handle)

    dropped: Dict[str, int] = {}
    for location in locations:
        raw = location.get("available_systems", [])
        for value in raw:
            if value not in _MAP:
                dropped[value] = dropped.get(value, 0) + 1
        location["available_systems"] = _normalise(raw)

    with path.open("w", encoding="utf-8") as handle:
        json.dump(locations, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    unknown = sum(dropped.values())
    print(f"Normalised {len(locations)} locations; canonical set {sorted(AVAILABLE_SYSTEMS)}.")
    print(f"Dropped {unknown} unimplemented label(s):")
    for value, count in sorted(dropped.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {count:2d}  {value}")


if __name__ == "__main__":
    main()
