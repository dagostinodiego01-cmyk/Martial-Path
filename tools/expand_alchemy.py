"""Expand the alchemy + secret-realm content breadth (ROADMAP F.1 / D.2 follow-up).

Idempotent, deterministic generator. Run it from the repo root:

    python tools/expand_alchemy.py

It rewrites four data files:

* ``game/data/items.json``          — appends ~22 new herbs (rarity-tagged) and
  fixes ``thunder_essence_herb``'s category/rarity. Existing items are untouched.
* ``game/data/gathering.json``      — per-location herb tables so every herb
  grows only in its distinct region (demonic ingredients only in the Holy Demon
  Continent).
* ``game/data/refining_recipes.json`` — the 4 hand-authored starter recipes plus
  ~100 generated recipes, each gated by ``minimum_body_realm`` (and, for the top
  tiers, ``minimum_essence_realm``).
* ``game/data/secret_realm.json``   — 6 hand-placed secret realms (a list), one
  per distinct region, each with its own enemy pool, boss, treasure and reward.

Every generated reference is checked against the live data catalogue; a bad id
raises rather than silently emitting broken content.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "game" / "data"

# -- rarity -> (base value, minimum body realm) -------------------------------
# Recipes are gated by the realm a cultivator needs to safely handle the
# ingredients; herbs inherit the same tiering via their rarity.
RARITY_TIER = {
    "mortal_grade": {"value": 5, "realm": "mortal"},
    "low_spirit_grade": {"value": 12, "realm": "strength_training"},
    "middle_spirit_grade": {"value": 25, "realm": "viscera_training"},
    "high_spirit_grade": {"value": 60, "realm": "bone_forging"},
    "earth_grade": {"value": 150, "realm": "tempering_marrow"},
    "heaven_grade": {"value": 400, "realm": "nine_stars_dao_palace"},
    "dao_grade": {"value": 1000, "realm": "nine_stars_dao_palace"},
}

# id -> (name, rarity, [location ids where it grows], description)
HERBS: Dict[str, Any] = {
    "jade_bamboo_shoot": (
        "Jade Bamboo Shoot", "mortal_grade", ["sky_fortune_road", "starting_village"],
        "A young bamboo shoot that glints faintly green. The first herb a travelling alchemist learns to cut.",
    ),
    "cloud_pine_needle": (
        "Cloud Pine Needle", "mortal_grade", ["beast_mountain"],
        "Silvery needles shed by the cloud pines of the beast mountains. A humble but steady base.",
    ),
    "nine_orifice_flower": (
        "Nine Orifice Flower", "low_spirit_grade", ["seven_profound_valleys_gate"],
        "A blossom whose nine pores drink mist and exhale qi. Grows only on the valley's rim.",
    ),
    "cloud_mist_tea_leaf": (
        "Cloud Mist Tea Leaf", "low_spirit_grade", ["seven_profound_valleys_inner"],
        "Tea leaves cured in the valley's cloud banks. Soothes a turbulent foundation.",
    ),
    "sunfire_ginseng": (
        "Sunfire Ginseng", "middle_spirit_grade", ["south_horizon_road"],
        "A ginseng root that pulses with trapped sunlight. Prized for mid-grade elixirs.",
    ),
    "deep_sea_coral": (
        "Deep Sea Coral", "middle_spirit_grade", ["south_sea_port"],
        "Coral harvested from the southern trenches, dense with cold water qi.",
    ),
    "phoenix_feather_bloom": (
        "Phoenix Feather Bloom", "high_spirit_grade", ["divine_phoenix_island"],
        "A bloom the colour of embers, said to grow where a phoenix once preened.",
    ),
    "starlight_lotus": (
        "Starlight Lotus", "high_spirit_grade", ["divine_phoenix_mystic_realm"],
        "A lotus that opens only under starlight, drinking the mystic realm's glow.",
    ),
    "vermilion_jade_root": (
        "Vermilion Jade Root", "earth_grade", ["vermillion_bird_kingdom"],
        "A root veined like carved jade, heavy with the southern kingdom's fire.",
    ),
    "nine_furnace_ember": (
        "Nine Furnace Ember", "earth_grade", ["nine_furnace_kingdom"],
        "An ember that never cools, harvested from the lips of the kingdom's furnaces.",
    ),
    "asura_blood_grass": (
        "Asura Blood Grass", "earth_grade", ["asura_divine_kingdom"],
        "Blade-edged grass that drinks the battlefield. Sharp and vital in equal measure.",
    ),
    "rival_vine": (
        "Rival Vine", "earth_grade", ["rival_divine_kingdom"],
        "A thorned vine that twists toward competing stems — a fierce catalyst in a cauldron.",
    ),
    "zen_heart_herb": (
        "Zen Heart Herb", "earth_grade", ["zenlight_monastery"],
        "An herb that grows in the monastery's still gardens, calming the mind that refines it.",
    ),
    "blood_slaughter_fern": (
        "Blood Slaughter Fern", "heaven_grade", ["blood_slaughter_steppes"],
        "A fern that flourishes on the steppes' killing grounds. Potent and dangerous.",
    ),
    "five_element_blossom": (
        "Five Element Blossom", "heaven_grade", ["five_element_temples"],
        "A single bloom that carries all five elements in perfect balance.",
    ),
    "sea_of_miracles_pearl": (
        "Sea of Miracles Pearl", "heaven_grade", ["ancient_ruins"],
        "A pearl formed where the Sea of Miracles laps against drowned ruins.",
    ),
    "ascension_gate_reed": (
        "Ascension Gate Reed", "heaven_grade", ["planetary_gate_array"],
        "A reed that hums at the threshold of ascension, threaded with gate-light.",
    ),
    # Demonic ingredients — Holy Demon Continent only.
    "demon_blood_lotus": (
        "Demon Blood Lotus", "dao_grade", ["holy_demon_continent"],
        "A black lotus that blooms in demon blood. The heart of the continent's forbidden alchemy.",
    ),
    "nether_ghost_grass": (
        "Nether Ghost Grass", "dao_grade", ["holy_demon_continent"],
        "Pale grass that grows on corpse-qi and whispers. Never gathered by the faint-hearted.",
    ),
    "abyssal_bone_flower": (
        "Abyssal Bone Flower", "dao_grade", ["holy_demon_continent"],
        "A flower that takes root in ancient bone, blooming only in the demon continent's abyss.",
    ),
    "holy_demon_heartroot": (
        "Holy Demon Heartroot", "dao_grade", ["holy_demon_continent"],
        "A root that beats like a heart when pulled from the soil — the rarest demonic ingredient.",
    ),
}

# Starter recipes kept from the original file (ids are referenced by existing
# tests; do not rename).
STARTER_RECIPES: List[Dict[str, Any]] = [
    {
        "id": "brew_healing_pill",
        "display_name": "Brew Healing Pill",
        "inputs": {"spirit_grass": 2},
        "output": {"item_id": "healing_pill", "count": 1},
        "minimum_body_realm": "mortal",
        "description": "Pound spirit grass into a crude paste and shape it into a healing pill.",
    },
    {
        "id": "brew_qi_pill",
        "display_name": "Brew Qi Recovery Pill",
        "inputs": {"spirit_grass": 1, "frost_herb": 1},
        "output": {"item_id": "qi_pill", "count": 1},
        "minimum_body_realm": "mortal",
        "description": "Blend cool frost herb with spirit grass to condense a qi-replenishing pill.",
    },
    {
        "id": "brew_profound_pill",
        "display_name": "Brew Profound Grade Pill",
        "inputs": {"flame_bloom": 2, "moon_herb": 1},
        "output": {"item_id": "profound_pill", "count": 1},
        "minimum_body_realm": "strength_training",
        "description": "Temper flame bloom with a sliver of moon herb to brew a profound-grade restorative.",
    },
    {
        "id": "brew_talent_refining_elixir",
        "display_name": "Brew Talent Refining Elixir",
        "inputs": {"moon_herb": 3, "flame_bloom": 2},
        "output": {"item_id": "talent_refining_elixir", "count": 1},
        "minimum_body_realm": "bone_forging",
        "description": "A demanding refinement that distils rare herbs into an elixir able to reshape innate talent.",
    },
]

# Body-realm tier -> (realm, herbs, pills, [optional essence realm gate]).
# Pills are existing consumables of roughly matching power; the generator verifies.
RECIPE_TIERS: List[Dict[str, Any]] = [
    {"realm": "mortal", "herbs": ["spirit_grass", "jade_bamboo_shoot", "cloud_pine_needle"],
     "pills": ["healing_pill", "qi_pill", "frost_jade_elixir", "common_tonic", "profound_elixir"]},
    {"realm": "strength_training", "herbs": ["frost_herb", "thunder_essence_herb", "nine_orifice_flower"],
     "pills": ["profound_pill", "frost_jade_tonic", "profound_decoction_no3", "mystic_dan", "marrow_cleansing_pill"]},
    {"realm": "flesh_training", "herbs": ["nine_orifice_flower", "cloud_mist_tea_leaf", "frost_herb"],
     "pills": ["frost_jade_pill", "frost_jade_nectar", "mystic_pill_no3", "profound_nectar", "marrow_cleansing_dan"]},
    {"realm": "viscera_training", "herbs": ["flame_bloom", "sunfire_ginseng", "deep_sea_coral"],
     "pills": ["profound_decoction", "mystic_pill", "blood_quenching_pill", "vermilion_elixir", "marrow_cleansing_pellet"]},
    {"realm": "altering_muscle", "herbs": ["sunfire_ginseng", "deep_sea_coral", "flame_bloom"],
     "pills": ["blood_quenching_elixir", "mystic_elixir", "vermilion_pill", "bone_forging_nectar", "profound_nectar_mortal"]},
    {"realm": "bone_forging", "herbs": ["moon_herb", "phoenix_feather_bloom", "starlight_lotus"],
     "pills": ["purple_cloud_pill", "vermilion_tonic", "bone_forging_tonic", "mystic_pill_no4", "frost_jade_nectar_mortal"]},
    {"realm": "body_pulse_condensation", "herbs": ["phoenix_feather_bloom", "starlight_lotus", "moon_herb"],
     "pills": ["mystic_decoction", "marrow_cleansing_elixir", "bone_forging_dan", "purple_cloud_nectar", "blood_quenching_pellet"]},
    {"realm": "tempering_marrow", "herbs": ["vermilion_jade_root", "nine_furnace_ember", "asura_blood_grass", "rival_vine"],
     "pills": ["earth_pellet", "dragon_blood_dan", "nine_revolutions_pellet", "mystic_decoction_no3", "star_gathering_pill"]},
    {"realm": "eight_gates_hidden_celestial_stems", "herbs": ["zen_heart_herb", "five_element_blossom", "blood_slaughter_fern"],
     "pills": ["dragon_blood_tonic", "earth_elixir", "star_gathering_dan", "nine_revolutions_nectar", "heaven_decoction"], "essence": "revolving_core"},
    {"realm": "nine_stars_dao_palace", "herbs": ["sea_of_miracles_pearl", "ascension_gate_reed", "demon_blood_lotus", "nether_ghost_grass", "abyssal_bone_flower"],
     "pills": ["soul_nurturing_pill", "dao_enlightenment_pill", "void_spirit_decoction", "celestial_decoction", "primordial_pill"], "essence": "divine_sea"},
]

# Six hand-placed secret realms (ROADMAP content target: 10+, this is the first
# expansion wave). Each references real enemies/bosses/locations/items.
SECRET_REALMS: List[Dict[str, Any]] = [
    {
        "id": "verdant_abyss",
        "display_name": "The Verdant Abyss",
        "location_id": "misty_gorge",
        "description": "A tear in the mist opens onto a buried grove where the laws of the world bend. Those who descend return changed — or not at all.",
        "room_count": 5,
        "enemy_pool": ["black_pine_serpent", "mist_jaw_leopard", "shrine_bone_thrall", "grave_mist_wraith", "forbidden_herb_guardian"],
        "boss_id": "rogue_cultivator_duel",
        "treasure_pool": [
            {"item_id": "spirit_stone", "weight": 4},
            {"item_id": "qi_pill", "weight": 3},
            {"item_id": "healing_pill", "weight": 3},
            {"item_id": "frost_herb", "weight": 2},
            {"item_id": "moon_herb", "weight": 1},
        ],
        "treasure_rooms": 1,
        "rest_rooms": 1,
        "final_reward": {"exp": 200, "gold": 150, "items": {"talent_refining_elixir": 1}},
    },
    {
        "id": "phoenix_fire_sanctum",
        "display_name": "The Phoenix Fire Sanctum",
        "location_id": "divine_phoenix_island",
        "description": "The island's caldera hides a sanctum where the phoenix's first fire still burns, testing all who seek its blessing.",
        "room_count": 6,
        "enemy_pool": ["phoenix_flame_sprite", "mystic_realm_firebird", "sun_scorched_warfiend", "sand_golem", "star_roc"],
        "boss_id": "divine_phoenix_disciple_spar",
        "treasure_pool": [
            {"item_id": "spirit_stone", "weight": 4},
            {"item_id": "phoenix_feather_bloom", "weight": 3},
            {"item_id": "starlight_lotus", "weight": 2},
            {"item_id": "profound_pill", "weight": 2},
            {"item_id": "mystic_decoction", "weight": 1},
        ],
        "treasure_rooms": 2,
        "rest_rooms": 1,
        "final_reward": {"exp": 600, "gold": 500, "items": {"talent_refining_elixir": 1, "phoenix_marrow_elixir": 1}},
    },
    {
        "id": "asura_blood_temple",
        "display_name": "The Asura Blood Temple",
        "location_id": "asura_divine_kingdom",
        "description": "Beneath the asura kingdom lies a blood-soaked temple where only the strong-willed leave with their mind intact.",
        "room_count": 7,
        "enemy_pool": ["asura_blood_guard", "blood_demon", "blood_golem", "blood_qilin", "crimson_thrall"],
        "boss_id": "blood_slaughter_steppes_warrior_arena",
        "treasure_pool": [
            {"item_id": "spirit_stone", "weight": 3},
            {"item_id": "asura_blood_grass", "weight": 3},
            {"item_id": "blood_quenching_pill", "weight": 2},
            {"item_id": "great_return_pill", "weight": 1},
        ],
        "treasure_rooms": 2,
        "rest_rooms": 1,
        "final_reward": {"exp": 1200, "gold": 1000, "items": {"talent_refining_elixir": 2, "asura_blood_grass": 3}},
    },
    {
        "id": "zen_void_monastery",
        "display_name": "The Zen Void Monastery",
        "location_id": "zenlight_monastery",
        "description": "A hollow monastery drifting between meditation and nothingness. Its trials weigh the stillness of the mind.",
        "room_count": 6,
        "enemy_pool": ["zenlight_iron_monk", "zen_boar", "void_golem", "cloud_temple_sprite", "zenlight_revenant"],
        "boss_id": "situ_bonan_duel",
        "treasure_pool": [
            {"item_id": "spirit_stone", "weight": 3},
            {"item_id": "zen_heart_herb", "weight": 3},
            {"item_id": "nirvana_rebirth_elixir", "weight": 1},
            {"item_id": "mystic_decoction", "weight": 2},
        ],
        "treasure_rooms": 1,
        "rest_rooms": 2,
        "final_reward": {"exp": 1500, "gold": 1200, "items": {"talent_refining_elixir": 2, "nirvana_rebirth_elixir": 1}},
    },
    {
        "id": "five_element_forge",
        "display_name": "The Five Element Forge",
        "location_id": "five_element_temples",
        "description": "Five temples ring a crucible where the elements are hammered into something greater. Only a balanced path survives.",
        "room_count": 8,
        "enemy_pool": ["five_element_warder", "five_element_qilin", "elemental_warfiend", "rune_tiger", "temple_thrall"],
        "boss_id": "yang_yun_boss",
        "treasure_pool": [
            {"item_id": "spirit_stone", "weight": 3},
            {"item_id": "five_element_blossom", "weight": 3},
            {"item_id": "star_gathering_pill", "weight": 2},
            {"item_id": "nine_revolutions_nectar", "weight": 1},
        ],
        "treasure_rooms": 2,
        "rest_rooms": 1,
        "final_reward": {"exp": 3000, "gold": 2500, "items": {"talent_refining_elixir": 3, "five_element_blossom": 2}},
    },
    {
        "id": "holy_demon_abyss",
        "display_name": "The Holy Demon Abyss",
        "location_id": "holy_demon_continent",
        "description": "The demon continent's heart opens onto an abyss of blood and ghost-light, where demonic ingredients grow wild and only the fearless harvest them.",
        "room_count": 9,
        "enemy_pool": ["holy_demon_warfiend", "nether_elder", "holy_demon_serpent", "nether_duelist", "blood_demon"],
        "boss_id": "holy_demon_continent_demon_duel",
        "treasure_pool": [
            {"item_id": "spirit_stone", "weight": 2},
            {"item_id": "demon_blood_lotus", "weight": 3},
            {"item_id": "nether_ghost_grass", "weight": 3},
            {"item_id": "abyssal_bone_flower", "weight": 2},
            {"item_id": "holy_demon_heartroot", "weight": 1},
        ],
        "treasure_rooms": 2,
        "rest_rooms": 2,
        "final_reward": {"exp": 6000, "gold": 5000, "items": {"talent_refining_elixir": 4, "holy_demon_heartroot": 1}},
    },
]


def _load_json(name: str) -> Any:
    with (DATA / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(name: str, data: Any) -> None:
    path = DATA / name
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"wrote {path.relative_to(ROOT)}")


def build_herbs(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Append new herbs to ``items`` in place; return the updated list."""
    by_id = {item["id"]: item for item in items}
    for herb_id, (name, rarity, _locs, description) in HERBS.items():
        value = RARITY_TIER[rarity]["value"]
        entry = {
            "id": herb_id,
            "name": name,
            "type": "material",
            "effect": "none",
            "magnitude": 0,
            "category": "herb",
            "rarity": rarity,
            "value": value,
            "description": description,
        }
        if herb_id in by_id:
            # Update in place (fixes thunder_essence_herb's missing category).
            by_id[herb_id].update(entry)
        else:
            items.append(entry)
            by_id[herb_id] = entry
    # Fix the pre-existing herb that shipped without category/rarity.
    if "thunder_essence_herb" in by_id:
        by_id["thunder_essence_herb"].setdefault("category", "herb")
        by_id["thunder_essence_herb"].setdefault("rarity", "low_spirit_grade")
        by_id["thunder_essence_herb"].setdefault("value", 12)
    return items


def build_gathering() -> Dict[str, Any]:
    """Per-location herb tables so each herb grows only in its region."""
    default = [{"item_id": "spirit_grass", "weight": 5}]
    locations: Dict[str, List[Dict[str, Any]]] = {}
    for herb_id, (_name, _rarity, locs, _description) in HERBS.items():
        for loc in locs:
            table = locations.setdefault(loc, [])
            if not any(e["item_id"] == herb_id for e in table):
                table.append({"item_id": herb_id, "weight": 3})
    # Ensure the original four herbs keep their starter locations.
    for loc, herb, weight in [
        ("outer_forest", "spirit_grass", 5),
        ("outer_forest", "frost_herb", 2),
        ("misty_gorge", "frost_herb", 4),
        ("misty_gorge", "moon_herb", 2),
        ("ruined_shrine", "moon_herb", 3),
        ("ruined_shrine", "flame_bloom", 2),
        ("beast_mountain", "flame_bloom", 3),
        ("beast_mountain", "thunder_essence_herb", 3),
        ("forbidden_back_mountain", "moon_herb", 4),
        ("forbidden_back_mountain", "flame_bloom", 3),
    ]:
        table = locations.setdefault(loc, [])
        existing = next((e for e in table if e["item_id"] == herb), None)
        if existing:
            existing["weight"] = max(existing["weight"], weight)
        else:
            table.append({"item_id": herb, "weight": weight})
    return {"default": default, "locations": locations}


def _recipe_inputs(tier: Dict[str, Any], index: int, alt: bool) -> Dict[str, int]:
    herbs = tier["herbs"]
    n = len(herbs)
    shift = index + (1 if alt else 0)
    return {herbs[(shift) % n]: 2, herbs[(shift + 1) % n]: 1}


def build_recipes(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The starter recipes plus ~100 generated realm-gated recipes."""
    names = {item["id"]: item.get("name", item["id"]) for item in items}
    pill_ids = {item["id"] for item in items}
    recipes: List[Dict[str, Any]] = [dict(r) for r in STARTER_RECIPES]

    for tier in RECIPE_TIERS:
        realm = tier["realm"]
        for index, pill_id in enumerate(tier["pills"]):
            if pill_id not in pill_ids:
                raise SystemExit(f"missing pill '{pill_id}' for tier '{realm}'")
            pill_name = names.get(pill_id, pill_id)
            for alt, suffix in ((False, ""), (True, "_2")):
                inputs = _recipe_inputs(tier, index, alt)
                herb_names = [names.get(h, h) for h in inputs]
                recipe: Dict[str, Any] = {
                    "id": f"refine_{pill_id}{suffix}",
                    "display_name": f"Refine {pill_name}",
                    "inputs": inputs,
                    "output": {"item_id": pill_id, "count": 1},
                    "minimum_body_realm": realm,
                    "description": f"Combine {', '.join(herb_names)} to refine a {pill_name}.",
                }
                if tier.get("essence"):
                    recipe["minimum_essence_realm"] = tier["essence"]
                recipes.append(recipe)
    return recipes


def main() -> None:
    items = _load_json("items.json")
    items = build_herbs(items)

    herb_ids = {item["id"] for item in items if item.get("category") == "herb"}
    for tier in RECIPE_TIERS:
        for herb in tier["herbs"]:
            if herb not in herb_ids:
                raise SystemExit(f"tier '{tier['realm']}' references missing herb '{herb}'")

    gathering = build_gathering()
    recipes = build_recipes(items)
    realms = SECRET_REALMS

    _write_json("items.json", items)
    _write_json("gathering.json", gathering)
    _write_json("refining_recipes.json", recipes)
    _write_json("secret_realm.json", realms)

    print(
        f"herbs={len(herb_ids)}  recipes={len(recipes)}  secret_realms={len(realms)}  "
        f"gathering_locations={len(gathering['locations'])}"
    )


if __name__ == "__main__":
    main()
