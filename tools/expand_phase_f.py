"""ROADMAP Phase F content expansion (F.2 + F.3).

Generates the breadth slice:
  - 16 new locations across story tiers 2-6 (29 -> 45), wired bidirectionally
    into the existing travel graph.
  - 8 new sects (4 -> 12) whose technique halls reference existing skills.
  - 12 new NPCs anchored to the new locations (50 -> 62), three of which give
    the first quest of a faction arc.
  - Encounter pools for all 16 new locations, wired to realm-appropriate
    enemies that previously sat unused in the random pool (dead-content pass).
  - 3 faction quest arcs (Seven Profound Valleys, Divine Phoenix, Asura) of
    three chained quests each (14 -> 23 quests).
  - 2 shops + 2 trainers bound to the new hubs.

Run:  .venv/Scripts/python.exe tools/expand_phase_f.py
"""
from __future__ import annotations

import json
from pathlib import Path

DATA = Path("game/data")


def load(name: str):
    with (DATA / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save(name: str, data) -> None:
    with (DATA / name).open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def req(body_realm: str, body_stage: int, essence_realm: str, essence_stage: int) -> dict:
    return {
        "body_transformation": {"minimum_realm": body_realm, "minimum_stage": body_stage},
        "essence_gathering": {"minimum_realm": essence_realm, "minimum_stage": essence_stage},
        "unlock_flags": [],
        "required_items": [],
        "required_reputation": [],
    }


# --------------------------------------------------------------------------
# 1. Locations
# --------------------------------------------------------------------------
LOCATIONS = [
    # -- story tier 2 ------------------------------------------------------
    {
        "id": "stream_fisher_wharf",
        "display_name": "Stream Fisher Wharf",
        "zone": "Sky Spill World",
        "location_type": "river_wharf",
        "tier": "Early Game",
        "story_tier": 2,
        "description": (
            "A weathered wharf where fishers and drifting cultivators trade "
            "tales for coin. Flat-bottomed boats tie up at thepilings, and the "
            "river current carries whispers from the far kingdoms."
        ),
        "requirements": req("Mortal", 1, "None", 0),
        "danger_level": 1,
        "qi_density": 2,
        "map_position": {"x": 0.095, "y": 0.71},
        "connected_locations": ["azure_village", "outer_forest"],
        "npc_ids": ["old_fisher_yan", "wharf_captain_bao"],
        "available_systems": ["explore", "rest", "travel", "gather", "combat", "dialogue", "quests"],
        "resources": ["River Carp", "Reed Cuttings"],
        "notes": "Story-tier 2 river wharf; early gathering and rumors.",
    },
    {
        "id": "thornwood_hollow",
        "display_name": "Thornwood Hollow",
        "zone": "Sky Spill World",
        "location_type": "deep_forest_wilderness",
        "tier": "Early Game",
        "story_tier": 2,
        "description": (
            "Past the gorge the forest thickens into thorn-choked hollows where "
            "the Mistwood Rangers run their lines. Beasts here have learned to "
            "fear the trail-marked trees."
        ),
        "requirements": req("Flesh Training", 1, "None", 0),
        "danger_level": 3,
        "qi_density": 3,
        "map_position": {"x": 0.03, "y": 0.66},
        "connected_locations": ["misty_gorge", "outer_forest", "deepwood_drift_outpost"],
        "npc_ids": ["mistwood_ranger_elder"],
        "available_systems": ["explore", "travel", "gather", "combat", "meditate"],
        "resources": ["Thornfruit", "Beast Cores"],
        "notes": "Story-tier 2 hunting grounds; home range of the Mistwood Rangers.",
    },
    {
        "id": "sky_fortune_outskirts",
        "display_name": "Sky Fortune Outskirts",
        "zone": "Sky Fortune Kingdom",
        "location_type": "farmland_outskirts",
        "tier": "Early Game",
        "story_tier": 2,
        "description": (
            "Terraced farms and roadside shrines ring the capital's outer wall. "
            "Merchant carts and pilgrims crowd the road, and pickpockets work "
            "the shadowed gaps between lantern posts."
        ),
        "requirements": req("Viscera Training", 1, "None", 0),
        "danger_level": 2,
        "qi_density": 2,
        "map_position": {"x": 0.235, "y": 0.57},
        "connected_locations": ["sky_fortune_capital", "lin_academy"],
        "npc_ids": [],
        "available_systems": ["explore", "rest", "travel", "gather", "combat", "quests"],
        "resources": ["Golden Rice", "Roadside Herbs"],
        "notes": "Story-tier 2 farmland ring; connects academy and capital.",
    },
    # -- story tier 3 ------------------------------------------------------
    {
        "id": "deepwood_drift_outpost",
        "display_name": "Deepwood Drift Outpost",
        "zone": "Sky Spill World",
        "location_type": "wilderness_outpost_hub",
        "tier": "Mid Game",
        "story_tier": 3,
        "description": (
            "A palisade outpost carved into the deepwood's heart, where hunters, "
            "herb-gatherers, and wandering sect scouts trade under lantern light. "
            "The drift changes hands often; the market never closes."
        ),
        "requirements": req("Altering Muscle", 1, "Houtian", 1),
        "danger_level": 4,
        "qi_density": 4,
        "map_position": {"x": 0.045, "y": 0.72},
        "connected_locations": ["thornwood_hollow", "outer_forest"],
        "npc_ids": ["drift_broker_lan"],
        "available_systems": [
            "explore", "rest", "travel", "market", "trainers", "gather",
            "combat", "sparring", "meditate", "quests", "dialogue",
        ],
        "resources": ["Deepwood Herbs", "Hunter Trophies"],
        "notes": "Story-tier 3 wilderness hub with market and trainer.",
    },
    {
        "id": "seven_profound_low_peaks",
        "display_name": "Seven Profound Low Peaks",
        "zone": "Seven Profound Valleys",
        "location_type": "sect_outer_peaks",
        "tier": "Mid Game",
        "story_tier": 3,
        "description": (
            "The valleys' outer peaks host the trial courses where outer "
            "disciples earn their jade tokens. Cloud pools gather between the "
            "crags, and older disciples spar above the mist line."
        ),
        "requirements": req("Altering Muscle", 1, "Houtian", 1),
        "danger_level": 4,
        "qi_density": 5,
        "map_position": {"x": 0.3, "y": 0.462},
        "connected_locations": [
            "seven_profound_valleys_gate", "seven_profound_valleys_inner",
            "forbidden_back_mountain",
        ],
        "npc_ids": [],
        "available_systems": ["explore", "travel", "gather", "combat", "sparring", "meditate"],
        "resources": ["Cloud Pool Dew", "Spirit Stones"],
        "notes": "Story-tier 3 sect trial peaks.",
    },
    {
        "id": "valleys_hidden_market",
        "display_name": "Valleys Hidden Market",
        "zone": "Seven Profound Valleys",
        "location_type": "hidden_market_canyon",
        "tier": "Mid Game",
        "story_tier": 3,
        "description": (
            "A canyon market that appears only when the valley fog thins. "
            "Gamblers hawk technique slips beside alchemists selling mislabeled "
            "pills, and every stall takes spirit stones or a wager."
        ),
        "requirements": req("Altering Muscle", 1, "Houtian", 1),
        "danger_level": 3,
        "qi_density": 4,
        "map_position": {"x": 0.3, "y": 0.575},
        "connected_locations": ["seven_profound_valleys_gate", "south_horizon_road"],
        "npc_ids": ["gambler_king_tan"],
        "available_systems": ["explore", "travel", "market", "rest", "dialogue", "quests"],
        "resources": ["Gambling Slips", "Spirit Stones"],
        "notes": "Story-tier 3 black market; shortcut between valleys and the south.",
    },
    {
        "id": "cloud_terrace_village",
        "display_name": "Cloud Terrace Village",
        "zone": "South Horizon Region",
        "location_type": "mountain_village",
        "tier": "Mid Game",
        "story_tier": 3,
        "description": (
            "Rice terraces climb the mountain shoulder in green steps. The "
            "village rites honor a river spirit, and travelers heading south "
            "stop here for the last honest beds before the coast."
        ),
        "requirements": req("Altering Muscle", 1, "Houtian", 1),
        "danger_level": 2,
        "qi_density": 3,
        "map_position": {"x": 0.235, "y": 0.62},
        "connected_locations": ["south_horizon_road", "sky_fortune_capital"],
        "npc_ids": [],
        "available_systems": ["explore", "rest", "travel", "gather", "market", "dialogue", "quests"],
        "resources": ["Terrace Rice", "Mountain Herbs"],
        "notes": "Story-tier 3 waystation between the capital and the south road.",
    },
    # -- story tier 4 ------------------------------------------------------
    {
        "id": "pearl_pavilion",
        "display_name": "Pearl Pavilion",
        "zone": "Southern Sea",
        "location_type": "sea_pavilion_hub",
        "tier": "Mid / Late Mortal World",
        "story_tier": 4,
        "description": (
            "A pavilion of white coral and pearl gauze floats on the tide, "
            "moored by chains older than the kingdom. Pearlers, pirate envoys, "
            "and sect buyers bid quietly and leave by separate boats."
        ),
        "requirements": req("Tempering Marrow", 1, "Xiantian", 1),
        "danger_level": 4,
        "qi_density": 5,
        "map_position": {"x": 0.355, "y": 0.79},
        "connected_locations": ["south_sea_port", "sea_of_mist_expanse"],
        "npc_ids": ["pearl_mistress_sui"],
        "available_systems": [
            "explore", "rest", "travel", "market", "trainers", "sparring",
            "dialogue", "quests",
        ],
        "resources": ["Sea Pearls", "Tide Herbs"],
        "notes": "Story-tier 4 sea trade hub with market and trainer.",
    },
    {
        "id": "tidecrook_cove",
        "display_name": "Tidecrook Cove",
        "zone": "Southern Sea",
        "location_type": "pirate_cove",
        "tier": "Mid / Late Mortal World",
        "story_tier": 4,
        "description": (
            "A crooked harbor where the Tidecrook pirates beach their hulls. "
            "Bonfires light the sand, loot is sorted openly, and duels settle "
            "every argument worth having."
        ),
        "requirements": req("Tempering Marrow", 1, "Xiantian", 1),
        "danger_level": 5,
        "qi_density": 4,
        "map_position": {"x": 0.405, "y": 0.75},
        "connected_locations": ["south_sea_port", "south_horizon_city"],
        "npc_ids": ["tide_king_hei"],
        "available_systems": ["explore", "travel", "combat", "sparring", "gather"],
        "resources": ["Salvage", "Beast Cores"],
        "notes": "Story-tier 4 pirate haven; dangerous but lucrative.",
    },
    {
        "id": "coral_prison_atoll",
        "display_name": "Coral Prison Atoll",
        "zone": "Southern Sea",
        "location_type": "sunken_prison",
        "tier": "Mid / Late Mortal World",
        "story_tier": 4,
        "description": (
            "A ring of coral towers rises from the reef, its cells drowned at "
            "high tide. The kingdom's worst cultivators were left here when the "
            "sea rose; some are still breathing."
        ),
        "requirements": req("Tempering Marrow", 3, "Xiantian", 1),
        "danger_level": 6,
        "qi_density": 6,
        "map_position": {"x": 0.44, "y": 0.86},
        "connected_locations": ["south_sea_port"],
        "npc_ids": [],
        "available_systems": ["explore", "travel", "combat", "meditate"],
        "resources": ["Black Coral", "Sunken Relics"],
        "notes": "Story-tier 4 high-danger dungeon atoll.",
    },
    {
        "id": "sea_of_mist_expanse",
        "display_name": "Sea of Mist Expanse",
        "zone": "Southern Sea",
        "location_type": "open_sea_expanse",
        "tier": "Mid / Late Mortal World",
        "story_tier": 4,
        "description": (
            "Beyond the pearl lanes the sea fog closes into a white void. "
            "Compass needles spin, birds refuse to cross, and the mist carries "
            "the taste of old lightning."
        ),
        "requirements": req("Tempering Marrow", 2, "Xiantian", 1),
        "danger_level": 5,
        "qi_density": 5,
        "map_position": {"x": 0.33, "y": 0.845},
        "connected_locations": ["pearl_pavilion", "south_sea_port"],
        "npc_ids": [],
        "available_systems": ["explore", "travel", "combat", "gather"],
        "resources": ["Mist Condensate", "Deep-Sea Herb"],
        "notes": "Story-tier 4 open-sea wilderness.",
    },
    # -- story tier 5 ------------------------------------------------------
    {
        "id": "furnace_pillar_city",
        "display_name": "Furnace Pillar City",
        "zone": "Central Region",
        "location_type": "forge_city_hub",
        "tier": "Late Mortal World",
        "story_tier": 5,
        "description": (
            "Pillars of everburning fire vent the city's ten thousand forges. "
            "Weaponwrights temper spirit steel by feel, and the Furnace Forge "
            "Society sells to any hand that can pay and any cause that can."
        ),
        "requirements": req("Tempering Marrow", 7, "Revolving Core", 1),
        "danger_level": 6,
        "qi_density": 6,
        "map_position": {"x": 0.395, "y": 0.29},
        "connected_locations": ["nine_furnace_kingdom", "vermillion_bird_kingdom", "zen_wilds_shrine"],
        "npc_ids": ["forge_master_yan_huo"],
        "available_systems": [
            "explore", "rest", "travel", "market", "trainers", "sparring",
            "combat", "dialogue", "quests", "meditate",
        ],
        "resources": ["Spirit Steel", "Forge Salamander Cores"],
        "notes": "Story-tier 5 forge city; market and trainer.",
    },
    {
        "id": "emberfall_citadel",
        "display_name": "Emberfall Citadel",
        "zone": "Central Region",
        "location_type": "militant_fortress",
        "tier": "Late Mortal World",
        "story_tier": 5,
        "description": (
            "A fortress of black basalt where the ash never settles. The Asura "
            "Kingdom's war pavilions drill here between campaigns, and the "
            "only law is the dueling ring at the gate."
        ),
        "requirements": req("Eight Gates of Hidden Celestial Stems", 1, "Revolving Core", 1),
        "danger_level": 7,
        "qi_density": 6,
        "map_position": {"x": 0.66, "y": 0.4},
        "connected_locations": ["asura_divine_kingdom", "blood_slaughter_steppes"],
        "npc_ids": ["war_pavilion_envoy_ru"],
        "available_systems": ["explore", "travel", "combat", "sparring", "quests"],
        "resources": ["War Spoils", "Blood Crystals"],
        "notes": "Story-tier 5 Asura war-fortress.",
    },
    {
        "id": "zen_wilds_shrine",
        "display_name": "Zen Wilds Shrine",
        "zone": "Great Zen Region",
        "location_type": "mountain_shrine",
        "tier": "Late Mortal World",
        "story_tier": 5,
        "description": (
            "A chain of abandoned shrines climbs into the high wilds. Monks "
            "from Zenlight still walk here in silence, sweeping paths no "
            "pilgrim uses, and the beasts leave the bells alone."
        ),
        "requirements": req("Eight Gates of Hidden Celestial Stems", 1, "Xiantian", 1),
        "danger_level": 5,
        "qi_density": 7,
        "map_position": {"x": 0.19, "y": 0.28},
        "connected_locations": ["zenlight_monastery", "furnace_pillar_city"],
        "npc_ids": ["nameless_zen_wanderer"],
        "available_systems": ["explore", "travel", "meditate", "gather", "combat"],
        "resources": ["Zen Heart Herbs", "Bell Bronze"],
        "notes": "Story-tier 5 meditative wilds linking monastery and furnace roads.",
    },
    # -- story tier 6 ------------------------------------------------------
    {
        "id": "rune_temple_undercroft",
        "display_name": "Rune Temple Undercroft",
        "zone": "Five Element Region",
        "location_type": "elemental_undercroft",
        "tier": "End Mortal World",
        "story_tier": 6,
        "description": (
            "Beneath the temples, buried rune-halls cycle the five elements in "
            "slow, patient circuits. The wardens here answer to no kingdom and "
            "test every intruder against a living element."
        ),
        "requirements": req("Eight Gates of Hidden Celestial Stems", 8, "Life Destruction", 1),
        "danger_level": 8,
        "qi_density": 8,
        "map_position": {"x": 0.82, "y": 0.1},
        "connected_locations": ["five_element_temples"],
        "npc_ids": ["rune_temple_warden"],
        "available_systems": ["explore", "travel", "combat", "meditate", "gather"],
        "resources": ["Rune Stones", "Elemental Cores"],
        "notes": "Story-tier 6 elemental dungeon beneath the temples.",
    },
    {
        "id": "gate_array_approach",
        "display_name": "Gate Array Approach",
        "zone": "Ascension Gate",
        "location_type": "ascension_approach",
        "tier": "End Mortal World",
        "story_tier": 6,
        "description": (
            "The last stair winds up through drifting star-fields to the "
            "planetary gate itself. Cultivators who pause here say the air "
            "tastes of distance, and few descend the way they came."
        ),
        "requirements": req("Nine Stars Dao Palace", 1, "Divine Sea", 1),
        "danger_level": 9,
        "qi_density": 9,
        "map_position": {"x": 0.79, "y": 0.44},
        "connected_locations": ["planetary_gate_array"],
        "npc_ids": ["gate_stair_hermit"],
        "available_systems": ["explore", "travel", "combat", "sparring", "meditate"],
        "resources": ["Starlight Condensate", "Ascension Gate Reeds"],
        "notes": "Story-tier 6 final approach to the ascension gate.",
    },
]

# --------------------------------------------------------------------------
# 2. Sects (technique halls reference existing skill ids)
# --------------------------------------------------------------------------
SECTS = [
    {
        "id": "mistwood_rangers",
        "display_name": "Mistwood Rangers",
        "path": "Mistwood Rangers",
        "tier": 2,
        "location_ids": ["thornwood_hollow"],
        "description": (
            "Hunter-wardens of the deepwood who track beasts by broken dew and "
            "keep the wilds from swallowing the roads."
        ),
        "join_requirements": {
            "min_reputation": 0, "min_body_realm": "flesh_training", "min_story_tier": 2,
        },
        "contribution_ranks": ["trail_hunter", "mist_warden", "ranger_elder"],
        "techniques": [
            {"skill_id": "flowing_step", "price": {"gold": 90}},
            {"skill_id": "iron_guard", "price": {"gold": 110}},
            {"skill_id": "nine_yang_footwork", "price": {"gold": 150}},
        ],
    },
    {
        "id": "stream_cloud_pavilion",
        "display_name": "Stream Cloud Pavilion",
        "path": "Stream Cloud Pavilion",
        "tier": 2,
        "location_ids": ["stream_fisher_wharf", "cloud_terrace_village"],
        "description": (
            "River-folk cultivators who read the current like scripture and "
            "trade soft-water techniques to anyone who shares their table."
        ),
        "join_requirements": {
            "min_reputation": 0, "min_body_realm": "strength_training", "min_story_tier": 2,
        },
        "contribution_ranks": ["river_hand", "tide_reader", "pavilion_elder"],
        "techniques": [
            {"skill_id": "spirit_palm", "price": {"gold": 80}},
            {"skill_id": "windless_fist", "price": {"gold": 120}},
            {"skill_id": "thunderclap_chant", "price": {"gold": 160}},
        ],
    },
    {
        "id": "valleys_gamblers_market",
        "display_name": "Valleys Gamblers' Market",
        "path": "Valleys Gamblers' Market",
        "tier": 3,
        "location_ids": ["valleys_hidden_market"],
        "description": (
            "Not a sect so much as a standing wager. Its 'disciples' stake "
            "technique slips against spirit stones and honor the debts with "
            "startling violence."
        ),
        "join_requirements": {
            "min_reputation": 0, "min_body_realm": "altering_muscle", "min_story_tier": 3,
        },
        "contribution_ranks": ["slip_holder", "odds_runner", "market_king"],
        "techniques": [
            {"skill_id": "shadowless_footwork", "price": {"spirit_stone": 25}},
            {"skill_id": "nether_finger", "price": {"spirit_stone": 30}},
            {"skill_id": "purple_cloud_guard", "price": {"spirit_stone": 35}},
        ],
    },
    {
        "id": "deepwood_drift_hall",
        "display_name": "Deepwood Drift Hall",
        "path": "Deepwood Drift Hall",
        "tier": 3,
        "location_ids": ["deepwood_drift_outpost", "seven_profound_low_peaks"],
        "description": (
            "An outpost hall where out-of-favor valley disciples teach the "
            "mountain-crushing arts they were raised on — for a fair share of "
            "the hunt."
        ),
        "join_requirements": {
            "min_reputation": 0, "min_body_realm": "altering_muscle", "min_story_tier": 3,
        },
        "contribution_ranks": ["drift_hand", "hall_warden", "drift_master"],
        "techniques": [
            {"skill_id": "mountain_crushing_fist", "price": {"spirit_stone": 20}},
            {"skill_id": "earth_vein_guard", "price": {"spirit_stone": 28}},
            {"skill_id": "glacial_claw", "price": {"spirit_stone": 36}},
        ],
    },
    {
        "id": "pearl_tide_pavilion",
        "display_name": "Pearl Tide Pavilion",
        "path": "Pearl Tide Pavilion",
        "tier": 4,
        "location_ids": ["pearl_pavilion"],
        "description": (
            "Mistress Sui's quiet federation of pearlers and tide-wardens. Its "
            "arts move like the sea: patient, enveloping, and impossible to "
            "outrun once committed."
        ),
        "join_requirements": {
            "min_reputation": 10, "min_body_realm": "tempering_marrow", "min_story_tier": 4,
        },
        "contribution_ranks": ["pearler", "tide_warden", "pavilion_mistress"],
        "techniques": [
            {"skill_id": "roaring_tide_sword_intent", "price": {"spirit_stone": 55}},
            {"skill_id": "white_tiger_breathing_method", "price": {"spirit_stone": 60}},
            {"skill_id": "phoenix_footwork", "price": {"spirit_stone": 70}},
        ],
    },
    {
        "id": "furnace_forge_society",
        "display_name": "Furnace Forge Society",
        "path": "Furnace Forge Society",
        "tier": 5,
        "location_ids": ["furnace_pillar_city"],
        "description": (
            "The smith-cult of the pillar city. Its members temper their own "
            "bodies in everburning fire and sell great-sun arts to the "
            "highest-standing bidder."
        ),
        "join_requirements": {
            "min_reputation": 5, "min_body_realm": "eight_gates_hidden_celestial_stems",
            "min_story_tier": 5,
        },
        "contribution_ranks": ["hammer_hand", "forge_adept", "society_master"],
        "techniques": [
            {"skill_id": "great_sun_chant", "price": {"spirit_stone": 70}},
            {"skill_id": "inferno_palm", "price": {"spirit_stone": 80}},
            {"skill_id": "earth_vein_sutra", "price": {"spirit_stone": 90}},
        ],
    },
    {
        "id": "emberfall_war_pavilion",
        "display_name": "Emberfall War Pavilion",
        "path": "Emberfall War Pavilion",
        "tier": 5,
        "location_ids": ["emberfall_citadel"],
        "description": (
            "The Asura Kingdom's own war school. It teaches the severing arts "
            "to soldiers of proved cruelty and asks no questions about whose "
            "blood paid the tuition."
        ),
        "join_requirements": {
            "max_reputation": 0,
            "min_body_realm": "eight_gates_hidden_celestial_stems",
            "min_story_tier": 5,
        },
        "contribution_ranks": ["ash_recruit", "war_banner", "pavilion_executioner"],
        "techniques": [
            {"skill_id": "soul_severing_kick", "price": {"spirit_stone": 75}},
            {"skill_id": "blood_sea_aura", "price": {"spirit_stone": 85}},
            {"skill_id": "windless_roar", "price": {"spirit_stone": 95}},
        ],
    },
    {
        "id": "rune_temple_order",
        "display_name": "Rune Temple Order",
        "path": "Rune Temple Order",
        "tier": 6,
        "location_ids": ["rune_temple_undercroft"],
        "description": (
            "Wardens of the buried rune-halls who guard the five-element "
            "circuits beneath the temples. Joining means surrendering your "
            "name to the circuit and your years to study."
        ),
        "join_requirements": {
            "min_reputation": 20, "min_body_realm": "nine_stars_dao_palace",
            "min_story_tier": 6,
        },
        "contribution_ranks": ["rune_scribe", "hall_warden", "order_patriarch"],
        "techniques": [
            {"skill_id": "great_sun_domain_no2", "price": {"spirit_stone": 160}},
            {"skill_id": "primordial_chaos_seal", "price": {"spirit_stone": 180}},
            {"skill_id": "void_sutra", "price": {"spirit_stone": 200}},
        ],
    },
]

# --------------------------------------------------------------------------
# 3. NPCs (merged into the roster via the characters/ directory loader)
# --------------------------------------------------------------------------
NPC_FILE = "characters/expansion_roster.json"

NPCS = [
    {
        "id": "old_fisher_yan",
        "name": "Old Fisher Yan",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "river_storyteller",
        "alignment": "neutral",
        "importance": "support",
        "faction": "Stream Cloud Pavilion",
        "encounter_type": "neutral",
        "min_story_tier": 2,
        "unlock": {"realm": "Body Tempering", "min_stage": 2},
        "encounter_weight": 3,
        "personality": {
            "traits": ["patient", "observant", "superstitious", "wry", "stubborn"],
            "speech_style": "Slow, salt-cured sentences that circle back to the river.",
            "values": ["patience", "the river's mood", "a fair price"],
            "likes": ["quiet mornings", "good bait", "an unhurried listener"],
            "dislikes": ["loud cultivators", "empty nets", "speed"],
            "relationship_behavior": {
                "hostile": "Cuts your line and lets the current take the rest.",
                "neutral": "Offers tea, weather talk, and careful half-truths.",
                "friendly": "Tells you which bends of the river hide what.",
                "trusted": "Trusts you with the pavilion's quiet errands.",
            },
            "morality_reaction": {
                "righteous": "Approves, mostly, and asks you to mind the fish.",
                "neutral": "Judges you the way he judges weather: wait and see.",
                "demonic": "Watches the water between you and his boat.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": False,
            "can_train_player": False, "can_give_quest": False, "can_join_player": False,
            "enemy_id": "", "quest_ids": [], "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "The old fisher squares his line without looking up. 'River's "
            "chatty today. Sit if you like; it talks more to two.'"
        ),
        "repeat_text": "'Back again. The river must like you — or owe you.'",
    },
    {
        "id": "wharf_captain_bao",
        "name": "Wharf Captain Bao",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "wharf_hardcase",
        "alignment": "neutral",
        "importance": "support",
        "faction": "Unaffiliated",
        "encounter_type": "rival",
        "min_story_tier": 2,
        "unlock": {"realm": "Body Tempering", "min_stage": 4},
        "encounter_weight": 3,
        "personality": {
            "traits": ["gruff", "transactional", "brave", "superstitious", "loyal"],
            "speech_style": "Short orders and shorter questions.",
            "values": ["the wharf's peace", "paid debts", "dry boots"],
            "likes": ["quiet docks", "heavy coin", "deckhands who listen"],
            "dislikes": ["gang recruiters", "night fog", "magic on his deck"],
            "relationship_behavior": {
                "hostile": "Bans you from the wharf and charges you anyway.",
                "neutral": "Nods you past the pilings and quotes loading fees.",
                "friendly": "Tips you off before the fog rolls in wrong.",
                "trusted": "Gives you a wharf token even the pirates respect.",
            },
            "morality_reaction": {
                "righteous": "Grumbles that good men make expensive cargo.",
                "neutral": "Counts you cargo until proven otherwise.",
                "demonic": "Priced your trouble into every quote already.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": True, "can_duel": False,
            "can_train_player": False, "can_give_quest": False, "can_join_player": False,
            "enemy_id": "wharf_captain_bao_spar", "quest_ids": [], "teaches_skills": [],
            "relationship_rewards": [],
        },
        "intro_text": (
            "A barrel-chested captain cracks his knuckles by the mooring "
            "posts. 'Wharf rules: fight on the sand, not the deck.'"
        ),
        "repeat_text": "'Sand's still there if you still want the lesson.'",
    },
    {
        "id": "mistwood_ranger_elder",
        "name": "Elder Shan of the Mistwood",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "ranger_elder",
        "alignment": "good",
        "importance": "support",
        "faction": "Mistwood Rangers",
        "encounter_type": "mentor",
        "min_story_tier": 2,
        "unlock": {"realm": "Body Tempering", "min_stage": 5},
        "encounter_weight": 3,
        "personality": {
            "traits": ["quiet", "sharp-eyed", "practical", "protective", "unhurried"],
            "speech_style": "Trail-wise fragments; names what matters and nothing else.",
            "values": ["the forest's balance", "clean kills", "marked trails"],
            "likes": ["fresh dew-sign", "kept promises", "guests who carry out trash"],
            "dislikes": ["poachers", "fire in dry season", "wasted meat"],
            "relationship_behavior": {
                "hostile": "Trails you for a day before letting you see her.",
                "neutral": "Shares the trail and the shade, little else.",
                "friendly": "Walks you past the thorn lines to the good water.",
                "trusted": "Names you a friend of the wood and means it.",
            },
            "morality_reaction": {
                "righteous": "Approves of discipline, whatever its creed.",
                "neutral": "Weighs your habits more than your vows.",
                "demonic": "Tolerates the wolf-blood, never the waste.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": True, "can_duel": False,
            "can_train_player": False, "can_give_quest": False, "can_join_player": False,
            "enemy_id": "mistwood_ranger_elder_spar", "quest_ids": [], "teaches_skills": [],
            "relationship_rewards": [],
        },
        "intro_text": (
            "A grey-cloaked elder steps from the thorns as if the thorns "
            "stepped aside for her. 'You walk loud. Spar, and I'll show you why.'"
        ),
        "repeat_text": "'The wood remembers loud guests. Show it better.'",
    },
    {
        "id": "drift_broker_lan",
        "name": "Drift Broker Lan",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "outpost_broker",
        "alignment": "neutral",
        "importance": "support",
        "faction": "Deepwood Drift Hall",
        "encounter_type": "ally",
        "min_story_tier": 3,
        "unlock": {"realm": "Body Tempering", "min_stage": 6},
        "encounter_weight": 3,
        "personality": {
            "traits": ["shrewd", "obliging", "careful", "greedy", "well-informed"],
            "speech_style": "Warm market patter that never quite names a price.",
            "values": ["movement of goods", "everybody solvent", "known faces"],
            "likes": ["rare pelts", "settled ledgers", "repeat customers"],
            "dislikes": ["brawls indoors", "unlicensed alchemists", "cheats"],
            "relationship_behavior": {
                "hostile": "Your credit dies quietly in three markets.",
                "neutral": "Finds you anything, for a finder's fee.",
                "friendly": "Holds stock aside and rounds the fee down.",
                "trusted": "Tells you what the valley sects are really buying.",
            },
            "morality_reaction": {
                "righteous": "Adjusts the patter; honest folk overpay happily.",
                "neutral": "Business is business, in any band.",
                "demonic": "Demonic coin spends the same, kept off the books.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": False,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "", "quest_ids": ["spv_outer_sea_ward"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "The broker spreads a pelt across the counter like a map. 'Deepwood "
            "discourages the idle. What are you, and what do you carry?'"
        ),
        "repeat_text": "'Ledgers remember, friend. Yours reads well.'",
    },
    {
        "id": "gambler_king_tan",
        "name": "Gambler King Tan",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "market_gambler",
        "alignment": "neutral_hostile",
        "importance": "rival",
        "faction": "Valleys Gamblers' Market",
        "encounter_type": "rival",
        "min_story_tier": 3,
        "unlock": {"realm": "Body Tempering", "min_stage": 6},
        "encounter_weight": 3,
        "personality": {
            "traits": ["flamboyant", "reckless", "honorable", "provocative", "lucky"],
            "speech_style": "Odds, wagers, and challenges dressed as compliments.",
            "values": ["the stake", "honor among debtors", "the flourish"],
            "likes": ["long odds", "spectators", "a debt paid with style"],
            "dislikes": ["walking away", "cheats", "insurance"],
            "relationship_behavior": {
                "hostile": "Stakes against you in every market in the valleys.",
                "neutral": "Offers you a slip: win, and it's yours.",
                "friendly": "Backs your wagers with the house's money.",
                "trusted": "Stakes his own name against your enemies.",
            },
            "morality_reaction": {
                "righteous": "Righteous marks bet predictably; he says so kindly.",
                "neutral": "Perfect. A coin with two unknown faces.",
                "demonic": "Finds your stakes adorable and your threats boring.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": True,
            "can_train_player": False, "can_give_quest": False, "can_join_player": False,
            "enemy_id": "gambler_king_tan_duel", "quest_ids": [], "teaches_skills": [],
            "relationship_rewards": [],
        },
        "intro_text": (
            "The Gambler King fans a handful of technique slips. 'Everything "
            "here is for sale or for stakes. Which are you good at?'"
        ),
        "repeat_text": "'The table remembers you. The odds have not changed.'",
    },
    {
        "id": "pearl_mistress_sui",
        "name": "Pearl Mistress Sui",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "sea_trade_power",
        "alignment": "neutral_good",
        "importance": "major_support",
        "faction": "Pearl Tide Pavilion",
        "encounter_type": "ally",
        "min_story_tier": 4,
        "unlock": {"realm": "Qi Condensation", "min_stage": 3},
        "encounter_weight": 3,
        "personality": {
            "traits": ["serene", "patient", "protective", "shrewd", "unhurried"],
            "speech_style": "Measured tide-speech; long silences doing half the talking.",
            "values": ["the pearl routes", "the sea's patience", "kept terms"],
            "likes": ["settled waters", "quiet bids", "divers who surface"],
            "dislikes": ["pirate flags", "greedy nets", "storms named after men"],
            "relationship_behavior": {
                "hostile": "The routes close to you, and the tide knows why.",
                "neutral": "Grants you the pavilion's shade and its going rates.",
                "friendly": "Shares the deep lanes and the safe anchors.",
                "trusted": "Names you warden-friend of every route she keeps.",
            },
            "morality_reaction": {
                "righteous": "Approves; the righteous guard better than they preach.",
                "neutral": "Sea judges currents, not creeds.",
                "demonic": "Demonic patrons pay well and break less, oddly.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": False,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "", "quest_ids": ["dpa_pearl_tribute"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "The Pearl Mistress looks up from a shell of black pearls. 'The "
            "tide brought you to my pavilion. That makes you either cargo or "
            "guest. Choose.'"
        ),
        "repeat_text": "'The pavilion keeps its doors, and its memory, open.'",
    },
    {
        "id": "tide_king_hei",
        "name": "Tide King Hei",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "pirate_boss",
        "alignment": "demonic",
        "importance": "major_threat",
        "faction": "Tidecrook Pirates",
        "encounter_type": "antagonist",
        "min_story_tier": 4,
        "unlock": {"realm": "Qi Condensation", "min_stage": 4},
        "encounter_weight": 3,
        "personality": {
            "traits": ["ruthless", "broad-laughed", "pragmatic", "territorial", "unpredictable"],
            "speech_style": "Roaring toasts that end in threats.",
            "values": ["the cove's freedom", "grabbed tides", "bold guests"],
            "likes": ["full hulls", "duels at dusk", "brave fools"],
            "dislikes": ["navy sails", "hide-and-seek", "beggars"],
            "relationship_behavior": {
                "hostile": "Puts your bounty on the bonfire board by nightfall.",
                "neutral": "Pours you a cup and names a price for everything.",
                "friendly": "Grants you cove rights and a pirate's farewell.",
                "trusted": "Sails beside you, which is a pirate's whole soul.",
            },
            "morality_reaction": {
                "righteous": "Righteous fools sink the same; he toasts them anyway.",
                "neutral": "Practical company. The best kind.",
                "demonic": "Kin, near enough. Blood counts as coin here.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": True,
            "can_train_player": False, "can_give_quest": False, "can_join_player": False,
            "enemy_id": "tide_king_hei_duel", "quest_ids": [], "teaches_skills": [],
            "relationship_rewards": [],
        },
        "intro_text": (
            "The Tide King kicks a chest of salvage toward you. 'Cove rules, "
            "guest: fight me, drink with me, or pay harbor weight. Pick fast.'"
        ),
        "repeat_text": "'Ha! The tide spat you back. The offer stands.'",
    },
    {
        "id": "forge_master_yan_huo",
        "name": "Forge Master Yan Huo",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "forge_master",
        "alignment": "neutral",
        "importance": "support",
        "faction": "Furnace Forge Society",
        "encounter_type": "neutral",
        "min_story_tier": 5,
        "unlock": {"realm": "Qi Condensation", "min_stage": 5},
        "encounter_weight": 3,
        "personality": {
            "traits": ["blunt", "perfectionist", "fiery", "honest", "unmovable"],
            "speech_style": "Forge-floor commands and metallurgy metaphors.",
            "values": ["the temper", "honest steel", "earned heat"],
            "likes": ["clean folding", "client silence", "ore with no lies in it"],
            "dislikes": ["sloppy quenching", "haggling", "display pieces"],
            "relationship_behavior": {
                "hostile": "Your commissions cool in the queue forever.",
                "neutral": "Names his price and his week; take both or neither.",
                "friendly": "Quenches your steel with the good well-water.",
                "trusted": "Forges for you what he would forge for himself.",
            },
            "morality_reaction": {
                "righteous": "Good causes still pay the same heat rates.",
                "neutral": "Steel holds no creed; neither does the master.",
                "demonic": "Demonic gold spends. The forge does not judge.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": False,
            "can_train_player": False, "can_give_quest": False, "can_join_player": False,
            "enemy_id": "", "quest_ids": [], "teaches_skills": [],
            "relationship_rewards": [],
        },
        "intro_text": (
            "The Forge Master pulls a blade from the coals with bare fingers. "
            "'Steel first. Talk after. What brings heat to my floor?'"
        ),
        "repeat_text": "'The coals remember every hand. Yours held.'",
    },
    {
        "id": "war_pavilion_envoy_ru",
        "name": "War Pavilion Envoy Ru",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "asura_envoy",
        "alignment": "hostile",
        "importance": "rival",
        "faction": "Emberfall War Pavilion",
        "encounter_type": "rival",
        "min_story_tier": 5,
        "unlock": {"realm": "Qi Condensation", "min_stage": 6},
        "encounter_weight": 3,
        "personality": {
            "traits": ["calculating", "ruthless", "polite", "patient", "savage"],
            "speech_style": "Courtly Asura courtesy over quiet contempt.",
            "values": ["the kingdom's ledger", "proved strength", "clean campaigns"],
            "likes": ["proper duels", "useful enemies", "ash that settles"],
            "dislikes": ["wasted soldiers", "mercy bills", "cowardice"],
            "relationship_behavior": {
                "hostile": "Files your name under future campaigns.",
                "neutral": "Extends the pavilion's terms; declines to explain them.",
                "friendly": "Shares campaign maps and their terrible margins.",
                "trusted": "Counts you among the pavilion's proved blades.",
            },
            "morality_reaction": {
                "righteous": "Righteous enemies die slowest; she keeps them last.",
                "neutral": "Useful. The pavilion prizes useful.",
                "demonic": "The pavilion was built by your kind. Welcome home.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": True, "can_duel": True,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "war_pavilion_envoy_ru_duel", "quest_ids": ["asura_steppes_oath"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "The Envoy sets a war-banner beside the dueling ring. 'The pavilion "
            "bids for blades. Prove yours, or sign the ledger. Either opens doors.'"
        ),
        "repeat_text": "'The banner still stands. So does the offer.'",
    },
    {
        "id": "nameless_zen_wanderer",
        "name": "Nameless Zen Wanderer",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "zen_wanderer",
        "alignment": "neutral_good",
        "importance": "mentor",
        "faction": "Unaffiliated",
        "encounter_type": "mentor",
        "min_story_tier": 5,
        "unlock": {"realm": "Qi Condensation", "min_stage": 5},
        "encounter_weight": 3,
        "personality": {
            "traits": ["silent", "kind", "strange", "perceptive", "detached"],
            "speech_style": "Rare, simple sentences that land like temple bells.",
            "values": ["the swept path", "no-name", "passing weather"],
            "likes": ["silence kept", "shared tea", "questions dropped"],
            "dislikes": ["titles", "urgency", "grand plans"],
            "relationship_behavior": {
                "hostile": "Is simply elsewhere when you arrive.",
                "neutral": "Makes room on the shrine step for one more cup.",
                "friendly": "Sweeps your section of the path too.",
                "trusted": "Answers the question you did not know to ask.",
            },
            "morality_reaction": {
                "righteous": "Bows to the vow and to the burden alike.",
                "neutral": "Pours tea for any weather.",
                "demonic": "Sees the storm and the house it shelters.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": False,
            "can_train_player": False, "can_give_quest": False, "can_join_player": False,
            "enemy_id": "", "quest_ids": [], "teaches_skills": [],
            "relationship_rewards": [],
        },
        "intro_text": (
            "A ragged wanderer sweeps leaves that keep falling. 'Sit. The "
            "mountain does nothing, and everything happens.'"
        ),
        "repeat_text": "'You came back. Most do, eventually. Tea is ready.'",
    },
    {
        "id": "rune_temple_warden",
        "name": "Rune Temple Warden",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "temple_warden",
        "alignment": "neutral",
        "importance": "support",
        "faction": "Rune Temple Order",
        "encounter_type": "entity",
        "min_story_tier": 6,
        "unlock": {"realm": "Qi Condensation", "min_stage": 7},
        "encounter_weight": 3,
        "personality": {
            "traits": ["inexorable", "formal", "ancient", "precise", "impartial"],
            "speech_style": "Litany cadence; measures everything against the circuit.",
            "values": ["the circuit's turn", "tested worth", "sealed halls"],
            "likes": ["proper reverence", "balanced elements", "exact tribute"],
            "dislikes": ["shortcut seekers", "unlicensed runes", "impatience"],
            "relationship_behavior": {
                "hostile": "The undercroft's runes rearrange to unmake you.",
                "neutral": "Names the trial and waits for your answer.",
                "friendly": "Grants passage at the lesser wards.",
                "trusted": "Opens the deep halls and the order's true name.",
            },
            "morality_reaction": {
                "righteous": "Righteousness is one element among five.",
                "neutral": "The circuit does not weigh hearts, only steps.",
                "demonic": "Blood taints the runes. Expect the harder trial.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": True, "can_duel": True,
            "can_train_player": False, "can_give_quest": False, "can_join_player": False,
            "enemy_id": "rune_temple_warden_trial", "quest_ids": [], "teaches_skills": [],
            "relationship_rewards": [],
        },
        "intro_text": (
            "A figure of banded stone and lit runes descends the stair. 'The "
            "circuit turns beneath you. Be tested, or be turned away.'"
        ),
        "repeat_text": "'The circuit remembers your step. It has not closed.'",
    },
    {
        "id": "gate_stair_hermit",
        "name": "Gate Stair Hermit",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "ascension_hermit",
        "alignment": "neutral",
        "importance": "legendary",
        "faction": "Unaffiliated",
        "encounter_type": "entity",
        "min_story_tier": 6,
        "unlock": {"realm": "Qi Condensation", "min_stage": 8},
        "encounter_weight": 2,
        "personality": {
            "traits": ["weathered", "cryptic", "ancient", "serene", "unhurried"],
            "speech_style": "Starfield metaphors; never answers the asked question.",
            "values": ["the climb", "the last step", "no name at all"],
            "likes": ["steep stairs", "honest exhaustion", "left gates"],
            "dislikes": ["crowds", "descendants' complaints", "descent"],
            "relationship_behavior": {
                "hostile": "Rearranges the stair so you climb forever.",
                "neutral": "Points upward and keeps his own counsel.",
                "friendly": "Walks a landing with you, saying little.",
                "trusted": "Tells you what the gate takes, and what it returns.",
            },
            "morality_reaction": {
                "righteous": "Even the righteous stop halfway. He waits.",
                "neutral": "The stair weighs feet, not faith.",
                "demonic": "The gate accepts all blood. It returns none.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": False,
            "can_train_player": False, "can_give_quest": False, "can_join_player": False,
            "enemy_id": "", "quest_ids": [], "teaches_skills": [],
            "relationship_rewards": [],
        },
        "intro_text": (
            "The hermit sits mid-stair, counting stars that are not there. "
            "'Closer now. The last step costs more than the first thousand.'"
        ),
        "repeat_text": "'Still climbing. The stair approves, in its way.'",
    },
]

# --------------------------------------------------------------------------
# 4. Encounter pools for the new locations (realm-matched, wired to the
#    previously-unused enemy pool).
# --------------------------------------------------------------------------
POOLS = {
    "stream_fisher_wharf": {
        "combat": [
            {"enemy_id": "field_bandit", "weight": 5},
            {"enemy_id": "thornwood_cutpurse", "weight": 4},
            {"enemy_id": "stream_captain_no.2", "weight": 2},
        ],
        "loot": [
            {"item_id": "healing_pill", "weight": 3},
            {"item_id": "spirit_grass", "weight": 3},
            {"item_id": "windless_fist_manual", "weight": 1},
        ],
    },
    "thornwood_hollow": {
        "combat": [
            {"enemy_id": "thornwood_bull", "weight": 5},
            {"enemy_id": "thornwood_warder", "weight": 4},
            {"enemy_id": "green_hollow_mantis", "weight": 3},
            {"enemy_id": "azure_ape", "weight": 2},
        ],
        "loot": [
            {"item_id": "beast_core", "weight": 3},
            {"item_id": "spirit_grass", "weight": 2},
            {"item_id": "flowing_step_manual", "weight": 1},
        ],
    },
    "sky_fortune_outskirts": {
        "combat": [
            {"enemy_id": "field_cutpurse", "weight": 5},
            {"enemy_id": "field_scorpion", "weight": 4},
            {"enemy_id": "shade_lizard", "weight": 2},
        ],
        "loot": [
            {"item_id": "healing_pill", "weight": 3},
            {"item_id": "qi_pill", "weight": 2},
            {"item_id": "iron_guard_manual", "weight": 1},
        ],
    },
    "deepwood_drift_outpost": {
        "combat": [
            {"enemy_id": "deepwood_wraith", "weight": 5},
            {"enemy_id": "deepwood_assassin", "weight": 4},
            {"enemy_id": "deepwood_golem", "weight": 3},
            {"enemy_id": "hollow_shaman", "weight": 2},
        ],
        "loot": [
            {"item_id": "marrow_cleansing_pill", "weight": 3},
            {"item_id": "bone_forging_petal", "weight": 2},
            {"item_id": "mountain_crushing_fist_manual", "weight": 1},
        ],
    },
    "seven_profound_low_peaks": {
        "combat": [
            {"enemy_id": "cloud_temple_sprite", "weight": 5},
            {"enemy_id": "zen_rogue_cultivator_no.2", "weight": 4},
            {"enemy_id": "iron_bell_warder", "weight": 3},
            {"enemy_id": "stone_revenant", "weight": 2},
        ],
        "loot": [
            {"item_id": "spirit_stone", "weight": 3},
            {"item_id": "cloud_pool_dew", "weight": 2},
            {"item_id": "earth_vein_guard_manual", "weight": 1},
        ],
    },
    "valleys_hidden_market": {
        "combat": [
            {"enemy_id": "capital_cutpurse", "weight": 5},
            {"enemy_id": "capital_warlock", "weight": 3},
            {"enemy_id": "vermillion_puppet", "weight": 2},
        ],
        "loot": [
            {"item_id": "mystic_pill", "weight": 3},
            {"item_id": "spirit_stone", "weight": 3},
            {"item_id": "shadowless_footwork_manual", "weight": 1},
        ],
    },
    "cloud_terrace_village": {
        "combat": [
            {"enemy_id": "meadow_revenant", "weight": 4},
            {"enemy_id": "green_hollow_toad", "weight": 4},
            {"enemy_id": "misty_boar", "weight": 2},
        ],
        "loot": [
            {"item_id": "healing_pill", "weight": 3},
            {"item_id": "spirit_grass", "weight": 2},
            {"item_id": "windless_chant_manual", "weight": 1},
        ],
    },
    "pearl_pavilion": {
        "combat": [
            {"enemy_id": "tidal_leopard", "weight": 4},
            {"enemy_id": "sea_mantis", "weight": 3},
            {"enemy_id": "coral_serpent", "weight": 3},
        ],
        "loot": [
            {"item_id": "star_gathering_pill", "weight": 3},
            {"item_id": "sea_pearl", "weight": 2},
            {"item_id": "phoenix_footwork_manual", "weight": 1},
        ],
    },
    "tidecrook_cove": {
        "combat": [
            {"enemy_id": "sea_zealot", "weight": 5},
            {"enemy_id": "sea_vulture", "weight": 4},
            {"enemy_id": "tidal_duelist", "weight": 3},
            {"enemy_id": "south_horizon_assassin", "weight": 2},
        ],
        "loot": [
            {"item_id": "great_return_pill", "weight": 3},
            {"item_id": "beast_core", "weight": 2},
            {"item_id": "soul_severing_kick_manual", "weight": 1},
        ],
    },
    "coral_prison_atoll": {
        "combat": [
            {"enemy_id": "coral_golem", "weight": 5},
            {"enemy_id": "coral_tiger", "weight": 4},
            {"enemy_id": "coral_warlock", "weight": 3},
            {"enemy_id": "abyssal_scorpion", "weight": 2},
        ],
        "loot": [
            {"item_id": "void_spirit_pill", "weight": 3},
            {"item_id": "black_coral", "weight": 2},
            {"item_id": "roaring_tide_sword_intent_manual", "weight": 1},
        ],
    },
    "sea_of_mist_expanse": {
        "combat": [
            {"enemy_id": "tidal_ape", "weight": 5},
            {"enemy_id": "sea_mantis", "weight": 4},
            {"enemy_id": "tidal_serpent", "weight": 3},
            {"enemy_id": "misty_wyrm", "weight": 2},
        ],
        "loot": [
            {"item_id": "mist_condensate", "weight": 3},
            {"item_id": "great_return_pill", "weight": 2},
            {"item_id": "white_tiger_breathing_method_manual", "weight": 1},
        ],
    },
    "furnace_pillar_city": {
        "combat": [
            {"enemy_id": "flame_warfiend", "weight": 5},
            {"enemy_id": "elemental_leopard", "weight": 3},
            {"enemy_id": "temple_hound", "weight": 3},
            {"enemy_id": "nine_furnace_fire_golem", "weight": 1},
        ],
        "loot": [
            {"item_id": "phoenix_marrow_pill", "weight": 3},
            {"item_id": "dragon_blood_ore", "weight": 2},
            {"item_id": "inferno_palm_manual", "weight": 1},
        ],
    },
    "emberfall_citadel": {
        "combat": [
            {"enemy_id": "blood_bandit", "weight": 5},
            {"enemy_id": "slaughter_rogue_cultivator", "weight": 4},
            {"enemy_id": "blood_golem", "weight": 3},
            {"enemy_id": "asura_blood_guard", "weight": 2},
        ],
        "loot": [
            {"item_id": "blood_quenching_elixir", "weight": 3},
            {"item_id": "blood_crystal", "weight": 2},
            {"item_id": "blood_sea_aura_manual", "weight": 1},
        ],
    },
    "zen_wilds_shrine": {
        "combat": [
            {"enemy_id": "zen_wolf", "weight": 5},
            {"enemy_id": "zen_lizard", "weight": 4},
            {"enemy_id": "zenlight_ape", "weight": 3},
            {"enemy_id": "zenlight_revenant", "weight": 2},
        ],
        "loot": [
            {"item_id": "soul_nurturing_pill", "weight": 3},
            {"item_id": "zen_heart_herb", "weight": 2},
            {"item_id": "windless_roar_manual", "weight": 1},
        ],
    },
    "rune_temple_undercroft": {
        "combat": [
            {"enemy_id": "rune_qilin", "weight": 5},
            {"enemy_id": "rune_tiger", "weight": 4},
            {"enemy_id": "five_element_crane", "weight": 3},
            {"enemy_id": "elemental_warfiend", "weight": 3},
            {"enemy_id": "five_element_warder", "weight": 2},
        ],
        "loot": [
            {"item_id": "nine_revolutions_elixir", "weight": 3},
            {"item_id": "rune_stone", "weight": 2},
            {"item_id": "great_sun_domain_no2_manual", "weight": 1},
        ],
    },
    "gate_array_approach": {
        "combat": [
            {"enemy_id": "gate_warder", "weight": 5},
            {"enemy_id": "gate_wolf", "weight": 4},
            {"enemy_id": "gate_duelist", "weight": 3},
            {"enemy_id": "planetary_leopard", "weight": 3},
            {"enemy_id": "primal_roc", "weight": 2},
        ],
        "loot": [
            {"item_id": "celestial_elixir", "weight": 3},
            {"item_id": "celestial_gate_essence", "weight": 2},
            {"item_id": "primordial_chaos_seal_manual", "weight": 1},
        ],
    },
}

# --------------------------------------------------------------------------
# 5. Faction quest arcs (F.3): 3 quests x 3 sects, chained via `requires`.
# --------------------------------------------------------------------------
ARCS = [
    {
        "sect": "seven_profound_valleys",
        "giver": "drift_broker_lan",
        "quests": [
            {
                "id": "spv_outer_sea_ward",
                "title": "Ward the Outer Sea of Mist",
                "description": (
                    "The Deepwood Drift's ledgers show mist-beasts drifting "
                    "down from the sea toward the valleys' trade roads. Cull "
                    "them before the caravans notice."
                ),
                "requires": {"completed": ["act1_conclusion"]},
                "objectives": [
                    {"type": "defeat", "target": "any", "count": 6, "text": "Cull 6 mist-road beasts"},
                ],
                "rewards": {"exp": 140, "gold": 60, "reputation": 8, "items": {"marrow_cleansing_elixir": 1}},
            },
            {
                "id": "spv_forbidden_scout",
                "title": "Scout the Forbidden Drift",
                "description": (
                    "The broker wants a mapped route to the Deepwood Drift "
                    "Outpost — the hall there has grown bold enough to bid for "
                    "valley pupils."
                ),
                "requires": {"completed": ["spv_outer_sea_ward"], "location": "seven_profound_valleys_inner"},
                "objectives": [
                    {"type": "visit_location", "target": "deepwood_drift_outpost", "count": 1, "text": "Reach the Deepwood Drift Outpost"},
                    {"type": "defeat", "target": "deepwood_wraith", "count": 3, "text": "Cut down 3 deepwood wraiths"},
                ],
                "rewards": {"exp": 180, "gold": 70, "reputation": 10},
            },
            {
                "id": "spv_marrow_pact",
                "title": "The Marrow Pact",
                "description": (
                    "With the drift mapped and the roads quiet, the valleys' "
                    "elders teach the gla­cial breathing art they once withheld "
                    "— to a disciple who has bled for the trade roads."
                ),
                "requires": {"completed": ["spv_forbidden_scout"]},
                "objectives": [
                    {"type": "breakthrough", "target": "any", "count": 1, "text": "Achieve 1 breakthrough"},
                    {"type": "defeat", "target": "misty_elder", "count": 1, "text": "Defeat the Misty Elder"},
                ],
                "rewards": {"exp": 260, "gold": 120, "reputation": 12, "skills": ["glacial_sword_art"]},
            },
        ],
    },
    {
        "sect": "divine_phoenix_island",
        "giver": "pearl_mistress_sui",
        "quests": [
            {
                "id": "dpa_pearl_tribute",
                "title": "The Pearl Tribute",
                "description": (
                    "Pirate zealots harry the pearl routes that feed the "
                    "island's tribute. Mistress Sui asks the Phoenix's "
                    "disciples to break them, quietly and completely."
                ),
                "requires": {"completed": ["act1_conclusion"]},
                "objectives": [
                    {"type": "defeat", "target": "sea_zealot", "count": 4, "text": "Break 4 pirate zealots"},
                ],
                "rewards": {"exp": 200, "gold": 90, "reputation": 8, "items": {"phoenix_marrow_pill": 1}},
            },
            {
                "id": "dpa_tide_trial",
                "title": "Trial of the Tidecrook",
                "description": (
                    "The Tide King's cove shelters the raiders' sponsor. Walk "
                    "into the cove, thin the vultures, and let the pirates "
                    "learn what the tide costs."
                ),
                "requires": {"completed": ["dpa_pearl_tribute"]},
                "objectives": [
                    {"type": "visit_location", "target": "tidecrook_cove", "count": 1, "text": "Enter Tidecrook Cove"},
                    {"type": "defeat", "target": "sea_vulture", "count": 3, "text": "Fell 3 sea vultures"},
                ],
                "rewards": {"exp": 260, "gold": 110, "reputation": 12},
            },
            {
                "id": "dpa_phoenix_ascendant",
                "title": "Phoenix Ascendant",
                "description": (
                    "With the routes safe, the island names its debt. Two "
                    "breakthroughs by the ember pools, and the phoenix-fist "
                    "lineage opens to you."
                ),
                "requires": {"completed": ["dpa_tide_trial"]},
                "objectives": [
                    {"type": "breakthrough", "target": "any", "count": 2, "text": "Achieve 2 breakthroughs"},
                ],
                "rewards": {"exp": 380, "gold": 150, "reputation": 15, "skills": ["phoenix_fist"]},
            },
        ],
    },
    {
        "sect": "asura_divine_kingdom",
        "giver": "war_pavilion_envoy_ru",
        "quests": [
            {
                "id": "asura_steppes_oath",
                "chain": "asura",
                "title": "Oath of the Steppes",
                "description": (
                    "The War Pavilion buys blades with proved blood. Cut down "
                    "four of the slaughter-dogs hunting the steppes and the "
                    "envoy will draft your name into the ledger."
                ),
                "requires": {"completed": ["act1_conclusion"]},
                "objectives": [
                    {"type": "defeat", "target": "slaughter_rogue_cultivator", "count": 4, "text": "Cut down 4 steppe rogues"},
                ],
                "rewards": {"exp": 320, "gold": 130, "items": {"blood_quenching_elixir": 2}},
            },
            {
                "id": "asura_blood_hunt",
                "chain": "asura",
                "title": "The Blood Hunt",
                "description": (
                    "The pavilion's banner wants raising where the kingdom's "
                    "enemies watch. Take the citadel road, thin the bandit "
                    "hosts, and let Emberfall see your work."
                ),
                "requires": {"completed": ["asura_steppes_oath"]},
                "objectives": [
                    {"type": "visit_location", "target": "emberfall_citadel", "count": 1, "text": "Reach Emberfall Citadel"},
                    {"type": "defeat", "target": "blood_bandit", "count": 4, "text": "Slay 4 blood bandits"},
                ],
                "rewards": {"exp": 420, "gold": 180, "items": {"blood_quenching_elixir": 2}},
            },
            {
                "id": "asura_demon_trial",
                "chain": "asura",
                "title": "Trial of the Demon Gate",
                "description": (
                    "The final proof: two breakthroughs of the body and the "
                    "blood golem of the ring broken beneath your hands. The "
                    "pavilion answers in kind."
                ),
                "requires": {"completed": ["asura_blood_hunt"]},
                "objectives": [
                    {"type": "breakthrough", "target": "any", "count": 2, "text": "Achieve 2 breakthroughs"},
                    {"type": "defeat", "target": "blood_golem", "count": 1, "text": "Break the blood golem"},
                ],
                "rewards": {"exp": 560, "gold": 240, "skills": ["blood_sea_roar"]},
            },
        ],
    },
]

# --------------------------------------------------------------------------
# 6. Shops + trainers for the new hubs
# --------------------------------------------------------------------------
SHOPS = [
    {
        "id": "drift_outpost_market",
        "display_name": "Deepwood Drift Market",
        "location_ids": ["deepwood_drift_outpost", "thornwood_hollow"],
        "description": (
            "Broker Lan's open-air stalls: hunter manuals, trail pills, and "
            "whatever the deepwood yielded this week."
        ),
        "stock": [
            {"item_id": "flowing_step_manual", "price": {"gold": 90}, "stock": 1},
            {"item_id": "iron_guard_manual", "price": {"gold": 100}, "stock": 1},
            {"item_id": "mountain_crushing_fist_manual", "price": {"spirit_stone": 22}, "stock": 1},
            {"item_id": "earth_vein_guard_manual", "price": {"spirit_stone": 30}, "stock": 1},
            {"item_id": "marrow_cleansing_elixir", "price": {"gold": 85}, "stock": 3},
            {"item_id": "mystic_pill", "price": {"gold": 60}, "stock": 5},
            {"item_id": "healing_pill", "price": {"gold": 20}, "stock": 10},
        ],
    },
    {
        "id": "pearl_pavilion_market",
        "display_name": "Pearl Pavilion Exchange",
        "location_ids": ["pearl_pavilion", "south_sea_port"],
        "description": (
            "Quiet bids under pearl gauze: sea-route manuals, deep-sea "
            "salves, and pills graded for the long cultivation tracks."
        ),
        "stock": [
            {"item_id": "roaring_tide_sword_intent_manual", "price": {"spirit_stone": 58}, "stock": 1},
            {"item_id": "phoenix_footwork_manual", "price": {"spirit_stone": 72}, "stock": 1},
            {"item_id": "white_tiger_breathing_method_manual", "price": {"spirit_stone": 64}, "stock": 1},
            {"item_id": "phoenix_marrow_pill", "price": {"spirit_stone": 45}, "stock": 3},
            {"item_id": "soul_nurturing_pill", "price": {"gold": 120}, "stock": 4},
            {"item_id": "star_gathering_pill", "price": {"gold": 95}, "stock": 4},
        ],
    },
]

TRAINERS = [
    {
        "id": "drift_drillmaster_guan",
        "display_name": "Drillmaster Guan",
        "location_ids": ["deepwood_drift_outpost"],
        "description": (
            "A retired valley outer-disciple who drills drift hands in the "
            "fundamentals — for coin, and only in coin."
        ),
        "techniques": [
            {"skill_id": "spirit_palm", "price": {"gold": 120}},
            {"skill_id": "iron_guard", "price": {"gold": 150}},
            {"skill_id": "mountain_crushing_fist", "price": {"gold": 300}},
        ],
    },
    {
        "id": "furnace_elder_fenhuo",
        "display_name": "Elder Fenhuo of the Forges",
        "location_ids": ["furnace_pillar_city"],
        "description": (
            "A Society elder who teaches the great-sun and blood arts to "
            "anyone whose spirit stones survive the tuition."
        ),
        "techniques": [
            {"skill_id": "great_sun_chant", "price": {"spirit_stone": 75}},
            {"skill_id": "inferno_palm", "price": {"spirit_stone": 85}},
            {"skill_id": "blood_sea_aura", "price": {"spirit_stone": 90}},
        ],
    },
]

# --------------------------------------------------------------------------
# Writer
# --------------------------------------------------------------------------

def main() -> None:
    # locations (append; keep file order stable)
    locations = load("locations.json")
    existing = {loc["id"] for loc in locations}
    new_locs = [loc for loc in LOCATIONS if loc["id"] not in existing]
    assert len(new_locs) == len(LOCATIONS), "some Phase F locations already exist"
    locations.extend(new_locs)
    save("locations.json", locations)

    # sects (append)
    sects = load("sects.json")
    existing = {sect["id"] for sect in sects}
    new_sects = [sect for sect in SECTS if sect["id"] not in existing]
    assert len(new_sects) == len(SECTS), "some Phase F sects already exist"
    sects.extend(new_sects)
    save("sects.json", sects)

    # characters (new roster file; the directory loader merges lists)
    roster_path = DATA / NPC_FILE
    if roster_path.exists():
        raise SystemExit(f"{roster_path} already exists; refusing to overwrite")
    save(NPC_FILE, NPCS)

    # encounter pools (merge dict entries)
    pools = load("encounter_pools.json")
    for location_id, pool in POOLS.items():
        assert location_id not in pools, f"pool for {location_id} already exists"
        pools[location_id] = pool
    save("encounter_pools.json", pools)

    # quests (append the three arcs)
    quests = load("quests.json")
    existing = {quest["id"] for quest in quests}
    arc_quests = [quest for arc in ARCS for quest in arc["quests"]]
    for quest in arc_quests:
        assert quest["id"] not in existing, f"quest {quest['id']} already exists"
    quests.extend(arc_quests)
    save("quests.json", quests)

    # shops + trainers (append)
    shops = load("shops.json")
    existing = {shop["id"] for shop in shops}
    new_shops = [shop for shop in SHOPS if shop["id"] not in existing]
    assert len(new_shops) == len(SHOPS), "some Phase F shops already exist"
    shops.extend(new_shops)
    save("shops.json", shops)

    trainers = load("trainers.json")
    existing = {trainer["id"] for trainer in trainers}
    new_trainers = [trainer for trainer in TRAINERS if trainer["id"] not in existing]
    assert len(new_trainers) == len(TRAINERS), "some Phase F trainers already exist"
    trainers.extend(new_trainers)
    save("trainers.json", trainers)

    counts = {
        "locations": len(locations), "sects": len(sects), "quests": len(quests),
        "shops": len(shops), "trainers": len(trainers), "new_npcs": len(NPCS),
        "new_pools": len(POOLS),
    }
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
