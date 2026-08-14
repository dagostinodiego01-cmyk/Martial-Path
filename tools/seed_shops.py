"""Seed additional shops so most regions have a market.

Until this script exists, only three markets serve 29 locations and six of
those locations are the only ones able to buy gear or spend spirit stones. This
generator adds one market per major hub (12 total), each stocked with gear and
consumables appropriate to the region's danger band: early hubs trade in gold,
later hubs in spirit stone (the premium currency the late-game sinks consume).

Pricing is deterministic and reuses the data already shipped with the game:
equipment sells at its ``value`` (gold) in early markets and at ``value / 60``
spirit stones in late markets (matching the existing ``sky_fortune`` / ``nine
furnace`` rate of ~60 gold per stone); consumables/materials carry an explicit
hand-set price per market. The script validates every stock id against the item
and equipment catalogues and fails loudly on a typo rather than shipping a
dangling reference.

The script is idempotent: it strips any shops it previously generated (by id)
and re-appends them, leaving the three hand-authored markets and their
technique-manual stock (owned by ``tools/seed_techniques.py``) untouched. Run
from the repo root:

    python tools/seed_shops.py
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

# tools/seed_shops.py -> <repo>/game/data
DATA_DIR = Path(__file__).resolve().parent.parent / "game" / "data"

#: Spirit-stone worth of one gold (matches the existing market pricing).
GOLD_PER_STONE = 60

# Each generated shop declares which locations it serves, its currency, the
# equipment it stocks (priced from the equipment catalogue's ``value``), and the
# consumables/materials it stocks (explicit price in the shop's currency).
# Equipment always has a stock of 1; goods are unlimited unless stated.
GENERATED_SHOPS: List[Dict[str, Any]] = [
    {
        "id": "lin_academy_supply",
        "display_name": "Lin Academy Supply Hall",
        "location_ids": ["lin_academy"],
        "description": "The academy's outfitter, selling mortal-grade arms and recovery pills to new disciples.",
        "currency": "gold",
        "equipment": ["training_sword", "iron_spear", "patched_leather_armor", "worn_travel_boots"],
        "goods": [("healing_pill", 10), ("qi_pill", 12), ("profound_pill", 25)],
    },
    {
        "id": "beast_mountain_trader",
        "display_name": "Beast Mountain Trader",
        "location_ids": ["beast_mountain"],
        "description": "A weather-beaten trader swapping mortal gear and pelts to hunters heading uphill.",
        "currency": "gold",
        "equipment": ["blazing_yang_saber", "silver_moon_plate", "inferno_treads", "plain_traveller_cloak", "outer_disciple_cloak"],
        "goods": [("healing_pill", 10), ("qi_pill", 12), ("beast_core", 15)],
    },
    {
        "id": "seven_profound_valleys_exchange",
        "display_name": "Seven Profound Valleys Exchange",
        "location_ids": ["seven_profound_valleys_gate", "seven_profound_valleys_inner"],
        "description": "The valley sect's gate-market, selling low-spirit gear and breakthrough aids to outer disciples.",
        "currency": "gold",
        "equipment": ["bone_forged_blade", "beast_hide_vest", "cloudstep_boots", "minor_qi_ring"],
        "goods": [("mystic_pill", 30), ("profound_nectar", 40), ("marrow_cleansing_pill", 25)],
    },
    {
        "id": "zenlight_monastery_hall",
        "display_name": "Zenlight Monastery Hall",
        "location_ids": ["zenlight_monastery"],
        "description": "A quiet monastery hall selling mind-clearing amulets, talismans, and tonic pills.",
        "currency": "gold",
        "equipment": ["clear_mind_amulet", "foundation_stone_amulet", "cracked_protection_talisman"],
        "goods": [("healing_pill", 10), ("profound_pill", 25), ("earth_tonic", 50)],
    },
    {
        "id": "south_sea_port_bazaar",
        "display_name": "South Sea Port Bazaar",
        "location_ids": ["south_sea_port"],
        "description": "A bustling port bazaar where spirit stones buy cultivator gear and breakthrough elixirs.",
        "currency": "spirit_stone",
        "equipment": ["sect_disciple_sword", "mist_concealment_cloak", "iron_thread_boots", "spirit_jade_amulet", "minor_breakthrough_talisman"],
        "goods": [("profound_nectar", 1), ("mystic_pill", 1), ("frost_jade_elixir", 1)],
    },
    {
        "id": "vermillion_bird_kingdom_market",
        "display_name": "Vermillion Bird Kingdom Market",
        "location_ids": ["vermillion_bird_kingdom"],
        "description": "The kingdom's grand market, trading mid-spirit arms and elixirs for spirit stones.",
        "currency": "spirit_stone",
        "equipment": ["spirit_devouring_saber", "nine_nether_vestments", "mist_walking_boots", "blood_heat_ring", "heart_guard_amulet", "blood_sealing_talisman"],
        "goods": [("mystic_dan", 1), ("heaven_tonic", 2), ("nine_revolutions_elixir", 2)],
    },
    {
        "id": "asura_divine_kingdom_blackmarket",
        "display_name": "Asura Divine Kingdom Black Market",
        "location_ids": ["asura_divine_kingdom"],
        "description": "A black market dealing in high-spirit arms and lifespan-extending elixirs.",
        "currency": "spirit_stone",
        "equipment": ["blood_moon_halberd", "sky_severing_scale_mail", "blazing_yang_sabatons", "bronze_spirit_mirror", "ancient_jade_slip"],
        "goods": [("marrow_cleansing_elixir", 3), ("purple_cloud_dan", 2)],
    },
    {
        "id": "planetary_gate_array_exchange",
        "display_name": "Planetary Gate Array Exchange",
        "location_ids": ["planetary_gate_array"],
        "description": "An exchange on the gate array's threshold, selling earth-grade treasures and breakthrough pills.",
        "currency": "spirit_stone",
        "equipment": ["cloud_sea_halberd", "nine_nether_war_vestments", "heaven_splitting_greaves", "miniature_alchemy_cauldron", "cracked_black_pagoda", "cloudpiercer_sword"],
        "goods": [("great_return_pill", 4), ("heaven_decoction", 2)],
    },
    {
        "id": "holy_demon_continent_soul_market",
        "display_name": "Holy Demon Continent Soul Market",
        "location_ids": ["holy_demon_continent"],
        "description": "The continent's soul market, trading heaven-grade relics and immortality pellets for spirit stones.",
        "currency": "spirit_stone",
        "equipment": ["ghost_flame_halberd", "thunder_war_vestments", "azure_trident"],
        "goods": [("immortal_ascension_pill", 10), ("celestial_elixir", 10), ("dao_enlightenment_spirit_stone", 5)],
    },
]


def load(filename: str) -> Any:
    with (DATA_DIR / filename).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dump(filename: str, data: Any) -> None:
    path = DATA_DIR / filename
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _equipment_price(value: int, currency: str) -> Dict[str, int]:
    if currency == "gold":
        return {"gold": max(1, value)}
    return {"spirit_stone": max(1, round(value / GOLD_PER_STONE))}


def main() -> None:
    items = {entry["id"]: entry for entry in load("items.json")}
    equipment = {entry["id"]: entry for entry in load("equipment.json")}
    shops = load("shops.json")

    generated_ids = {spec["id"] for spec in GENERATED_SHOPS}
    # Strip any previously generated shops; keep the hand-authored markets and
    # their technique-manual stock.
    shops = [shop for shop in shops if shop.get("id") not in generated_ids]

    for spec in GENERATED_SHOPS:
        currency = spec["currency"]
        stock: List[Dict[str, Any]] = []
        for item_id in spec["equipment"]:
            entry = equipment.get(item_id)
            if entry is None:
                raise SystemExit(f"unknown equipment id '{item_id}' in shop '{spec['id']}'")
            stock.append(
                {
                    "item_id": item_id,
                    "price": _equipment_price(int(entry.get("value", 0)), currency),
                    "stock": 1,
                }
            )
        for item_id, amount in spec["goods"]:
            if item_id not in items:
                raise SystemExit(f"unknown item id '{item_id}' in shop '{spec['id']}'")
            stock.append({"item_id": item_id, "price": {currency: int(amount)}})

        shops.append(
            {
                "id": spec["id"],
                "display_name": spec["display_name"],
                "location_ids": list(spec["location_ids"]),
                "description": spec["description"],
                "stock": stock,
            }
        )

    dump("shops.json", shops)
    print(f"Seeded {len(GENERATED_SHOPS)} shops; total {len(shops)}.")


if __name__ == "__main__":
    main()
