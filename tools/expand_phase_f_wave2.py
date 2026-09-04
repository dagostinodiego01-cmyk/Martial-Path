"""ROADMAP Phase F, second content wave.

Closes the remaining §6 breadth gaps on top of the first wave:
  - 7 new tier 5-6 techniques (skills.json), wired into the Furnace Forge
    Society, Emberfall War Pavilion, and Rune Temple Order halls.
  - 3 hand-placed secret realms bound to the new endgame zones (Coral Prison
    Atoll, Rune Temple Undercroft, Gate Array Approach).
  - 28 new NPCs (62 -> 90) anchored across the new and underused zones.
  - 26 new quests (35 -> 61): zone quest chains for the expansion locations
    plus character quests given by wave-1 and wave-2 NPCs.

Run:  .venv/Scripts/python.exe tools/expand_phase_f_wave2.py
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
# 1. Tier 5-6 techniques (7 new skills; the reachability test counts sect
#    halls as an acquisition path, so these ship seeded into three halls).
# --------------------------------------------------------------------------
SKILLS = [
    {
        "id": "everburning_forge_body",
        "name": "Everburning Forge Body",
        "type": "passive",
        "effect": "buff_max_hp",
        "scaling": 3.0,
        "description": "The Society's master tempering: your body holds the forge's heat, passively raising your vitality by 200%.",
    },
    {
        "id": "pillar_of_the_sun",
        "name": "Pillar of the Sun",
        "type": "active",
        "effect": "aoe_damage",
        "scaling": 11.9,
        "cooldown": 4,
        "qi_cost": 410,
        "description": "Condenses the forge-fires into a standing pillar of sun that sears every foe before you.",
    },
    {
        "id": "ashen_verdict",
        "name": "Ashen Verdict",
        "type": "active",
        "effect": "execute",
        "scaling": 16.1,
        "cooldown": 5,
        "qi_cost": 465,
        "description": "The pavilion's sentence carried out in one stroke: what is judged broken, breaks.",
    },
    {
        "id": "blood_ledger_aura",
        "name": "Blood Ledger Aura",
        "type": "passive",
        "effect": "buff_attack",
        "scaling": 3.1,
        "description": "Every debt of blood the pavilion has collected fuels you, passively raising your attack by 210%.",
    },
    {
        "id": "five_element_world_seal",
        "name": "Five Element World Seal",
        "type": "active",
        "effect": "true_damage",
        "scaling": 11.2,
        "cooldown": 4,
        "qi_cost": 440,
        "description": "Imprints the five-element circuit onto space itself; the seal's judgment cannot be parried or turned.",
    },
    {
        "id": "rune_circuit_body",
        "name": "Rune Circuit Body",
        "type": "passive",
        "effect": "qi_cost_reduction",
        "scaling": 0.35,
        "description": "Living runes circuit through your meridians, passively lowering the qi cost of every technique by 35%.",
    },
    {
        "id": "gate_star_severing_step",
        "name": "Gate Star-Severing Step",
        "type": "active",
        "effect": "counter",
        "scaling": 13.4,
        "cooldown": 4,
        "qi_cost": 420,
        "description": "A footwork art learned on the last stair: step between a blow and its mark, and return the stars' cold answer.",
    },
]

# Hall additions: sect_id -> technique entries to append.
HALL_ADDITIONS = {
    "furnace_forge_society": [
        {"skill_id": "everburning_forge_body", "price": {"spirit_stone": 110}},
        {"skill_id": "pillar_of_the_sun", "price": {"spirit_stone": 130}},
    ],
    "emberfall_war_pavilion": [
        {"skill_id": "blood_ledger_aura", "price": {"spirit_stone": 115}},
        {"skill_id": "ashen_verdict", "price": {"spirit_stone": 135}},
    ],
    "rune_temple_order": [
        {"skill_id": "rune_circuit_body", "price": {"spirit_stone": 170}},
        {"skill_id": "five_element_world_seal", "price": {"spirit_stone": 190}},
        {"skill_id": "gate_star_severing_step", "price": {"spirit_stone": 210}},
    ],
}

# --------------------------------------------------------------------------
# 2. Hand-placed secret realms for the new endgame zones.
# --------------------------------------------------------------------------
REALMS = [
    {
        "id": "coral_drowned_panopticon",
        "display_name": "The Coral Drowned Panopticon",
        "location_id": "coral_prison_atoll",
        "description": (
            "The atoll's deepest ring holds the panopticon: a drowned wheel of "
            "cells around a single lit tower. The kingdom's first prisoners "
            "still pace their circles, and the warden has never left."
        ),
        "room_count": 8,
        "enemy_pool": [
            "coral_golem",
            "coral_tiger",
            "coral_warlock",
            "abyssal_golem",
            "abyssal_scorpion",
            "sea_zealot",
        ],
        "boss_id": "tide_king_hei_duel",
        "treasure_pool": [
            {"item_id": "spirit_stone", "weight": 3},
            {"item_id": "void_spirit_pill", "weight": 2},
            {"item_id": "celestial_nectar", "weight": 2},
            {"item_id": "dao_palace_star_core", "weight": 1},
            {"item_id": "abyssal_bone_flower", "weight": 2},
        ],
        "treasure_rooms": 2,
        "rest_rooms": 1,
        "final_reward": {
            "exp": 2200,
            "gold": 1600,
            "items": {
                "talent_refining_elixir": 2,
                "void_spirit_elixir": 1,
            },
        },
    },
    {
        "id": "undercroft_circuit_prime",
        "display_name": "The Undercroft Circuit Prime",
        "location_id": "rune_temple_undercroft",
        "description": (
            "Below the buried rune-halls lies the circuit's prime meridian, "
            "where the five elements were first balanced. The wardens test "
            "pilgrims here with living elements, one element per hall."
        ),
        "room_count": 9,
        "enemy_pool": [
            "rune_qilin",
            "rune_tiger",
            "five_element_crane",
            "five_element_ape",
            "elemental_warfiend",
            "elemental_leopard",
        ],
        "boss_id": "rune_temple_warden_trial",
        "treasure_pool": [
            {"item_id": "spirit_stone", "weight": 3},
            {"item_id": "dao_palace_star_core", "weight": 2},
            {"item_id": "nine_revolutions_elixir", "weight": 2},
            {"item_id": "dao_enlightenment_root", "weight": 1},
            {"item_id": "starlight_lotus", "weight": 1},
        ],
        "treasure_rooms": 2,
        "rest_rooms": 2,
        "final_reward": {
            "exp": 2800,
            "gold": 2000,
            "items": {
                "talent_refining_elixir": 2,
                "nine_revolutions_elixir": 1,
            },
        },
    },
    {
        "id": "starfield_stair_sanctum",
        "display_name": "The Starfield Stair Sanctum",
        "location_id": "gate_array_approach",
        "description": (
            "Halfway up the last stair, a folding of the star-field holds a "
            "sanctum where earlier climbers left their final techniques, their "
            "regrets, and in a few cases their guardian spirits."
        ),
        "room_count": 9,
        "enemy_pool": [
            "gate_warder",
            "gate_wolf",
            "gate_duelist",
            "planetary_sprite",
            "planetary_leopard",
            "primal_roc",
            "astral_wraith",
        ],
        "boss_id": "steppes_master_trial",
        "treasure_pool": [
            {"item_id": "spirit_stone", "weight": 3},
            {"item_id": "celestial_gate_essence", "weight": 2},
            {"item_id": "immortal_ascension_elixir", "weight": 1},
            {"item_id": "dao_enlightenment_crystal", "weight": 2},
            {"item_id": "ascension_gate_reed", "weight": 2},
        ],
        "treasure_rooms": 2,
        "rest_rooms": 2,
        "final_reward": {
            "exp": 3400,
            "gold": 2400,
            "items": {
                "talent_refining_elixir": 3,
                "immortal_ascension_elixir": 1,
            },
        },
    },
]

# --------------------------------------------------------------------------
# 3. Wave-2 NPCs (28; roster grows 62 -> 90).
# --------------------------------------------------------------------------
NPC_FILE = "characters/expansion_roster_wave2.json"

NPCS = [
    # -- Sky Spill World / early zones -------------------------------------
    {
        "id": "reed_cutter_min",
        "name": "Reed-Cutter Min",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "wharf_hand",
        "alignment": "neutral",
        "importance": "minor",
        "faction": "Stream Cloud Pavilion",
        "encounter_type": "ally",
        "min_story_tier": 2,
        "unlock": {"realm": "Body Tempering", "min_stage": 2},
        "encounter_weight": 3,
        "personality": {
            "traits": ["cheerful", "hardworking", "curious", "gossipy", "resilient"],
            "speech_style": "Quick, wet laughter between reed bundles.",
            "values": ["a full hold", "the day's work", "fresh stories"],
            "likes": ["river gossip", "strong tea", "weather that behaves"],
            "dislikes": ["idle nobles", "tax collectors", "still water"],
            "relationship_behavior": {
                "hostile": "Sells your arrival time to anyone who asks.",
                "neutral": "Chatters while working and shares the shade.",
                "friendly": "Saves you the driest reed bundles and best gossip.",
                "trusted": "Shows you the wharf's hidden channels.",
            },
            "morality_reaction": {
                "righteous": "Beams and tells every wharf-hand about you.",
                "neutral": "Trades with you like anyone else.",
                "demonic": "Keeps her hands busy and her distance shorter.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": False,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "", "quest_ids": ["wharf_silt_beasts"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "A young reed-cutter hoists a dripping bundle. 'You've got a "
            "worker's shoulders under that robe. Want to earn wharf coin?'"
        ),
        "repeat_text": "'The reeds keep coming, and so do the silt-beasts.'",
    },
    {
        "id": "feral_hunter_karu",
        "name": "Karu of the Thorn Line",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "ranger_scout",
        "alignment": "neutral",
        "importance": "minor",
        "faction": "Mistwood Rangers",
        "encounter_type": "rival",
        "min_story_tier": 2,
        "unlock": {"realm": "Body Tempering", "min_stage": 4},
        "encounter_weight": 3,
        "personality": {
            "traits": ["wild", "competitive", "loyal", "blunt", "restless"],
            "speech_style": "Hunting metaphors and direct challenges.",
            "values": ["the hunt", "marked trails", "proving ground"],
            "likes": ["fair chases", "dawn scouting", "meat won by hand"],
            "dislikes": ["snare poachers", "cowardly shots", "fences"],
            "relationship_behavior": {
                "hostile": "Runs you out of the ranger lines at spear-point.",
                "neutral": "Grudging respect: you walk soft for an outsider.",
                "friendly": "Shares kills and teaches trail-sign.",
                "trusted": "Runs the thorn line beside you, back to back.",
            },
            "morality_reaction": {
                "righteous": "Honors the creed if you honor the wood.",
                "neutral": "Weighs your boots, not your vows.",
                "demonic": "Wolf-blood runs in the line too. Prove the control.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": True, "can_duel": False,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "mistwood_ranger_elder_spar", "quest_ids": ["thornline_cull"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "A wiry hunter drops from the thorns, spear grounded. 'You've "
            "crossed three of my marks without noticing. Spar, and I'll show "
            "you the fourth.'"
        ),
        "repeat_text": "'Your steps are quieter now. Good. The hollows test again.'",
    },
    {
        "id": "farmhand_olive",
        "name": "Olive of the Terraces",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "farmhand_fixer",
        "alignment": "neutral_good",
        "importance": "minor",
        "faction": "Unaffiliated",
        "encounter_type": "ally",
        "min_story_tier": 2,
        "unlock": {"realm": "Body Tempering", "min_stage": 3},
        "encounter_weight": 3,
        "personality": {
            "traits": ["practical", "warm", "stubborn", "observant", "brave"],
            "speech_style": "Homely proverbs that land harder than they sound.",
            "values": ["the harvest", "neighbors", "paid debts"],
            "likes": ["shared meals", "fixed fences", "rain on schedule"],
            "dislikes": ["soldiers foraging", "crow thefts", "grand promises"],
            "relationship_behavior": {
                "hostile": "Feeds you last and warns the neighbors first.",
                "neutral": "Sets a bowl out and asks about the roads.",
                "friendly": "Bundles you bread and farm-gossip in one cloth.",
                "trusted": "Hides you in the root cellar when hunters pass.",
            },
            "morality_reaction": {
                "righteous": "Approves, and asks if you've eaten.",
                "neutral": "Judges the harvest, not the heart, for now.",
                "demonic": "Feeds you anyway. Kindness confuses enemies.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": False,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "", "quest_ids": ["outskirts_fences"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "A farmhand mends a fence post without looking up. 'Beasts took "
            "two goats last night. Fence won't hold forever, and neither will I.'"
        ),
        "repeat_text": "'Fence is mended where you walked. Come back soon.'",
    },
    {
        "id": "cloud_pool_hermit_bai",
        "name": "Hermit Bai of the Cloud Pools",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "peak_hermit",
        "alignment": "neutral",
        "importance": "mentor",
        "faction": "Unaffiliated",
        "encounter_type": "mentor",
        "min_story_tier": 3,
        "unlock": {"realm": "Body Tempering", "min_stage": 6},
        "encounter_weight": 2,
        "personality": {
            "traits": ["contemplative", "aloof", "kind", "precise", "unhurried"],
            "speech_style": "Cloud-shaped riddles that resolve into plain sense.",
            "values": ["still water", "the mountain's patience", "small kindnesses"],
            "likes": ["dawn mist", "uninvited guests who sit quietly", "simple tea"],
            "dislikes": ["loud ambitions", "wasted words", "steep demands"],
            "relationship_behavior": {
                "hostile": "The pools simply close; you never find the path again.",
                "neutral": "Points you to water and lets you drink.",
                "friendly": "Shares the pool's quiet and its lessons.",
                "trusted": "Teaches the breathing the peaks taught him.",
            },
            "morality_reaction": {
                "righteous": "Virtue is a heavy staff. Carry it lightly.",
                "neutral": "The pools reflect whatever stands above them.",
                "demonic": "Dark water still mirrors stars.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": True, "can_duel": False,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "cloud_pool_hermit_bai_spar", "quest_ids": ["peaks_pool_trial"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "A grey hermit stirs a cloud-pool with one finger. 'Sit. The pool "
            "will spar with you first, and then I will.'"
        ),
        "repeat_text": "'The pool remembers your ripples. It is pleased.'",
    },
    {
        "id": "market_crier_duo",
        "name": "Duo the Market Crier",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "market_herald",
        "alignment": "chaotic_ally",
        "importance": "minor",
        "faction": "Valleys Gamblers' Market",
        "encounter_type": "neutral",
        "min_story_tier": 3,
        "unlock": {"realm": "Body Tempering", "min_stage": 6},
        "encounter_weight": 3,
        "personality": {
            "traits": ["loud", "clever", "opportunistic", "warm", "exaggerating"],
            "speech_style": "Auction cadence; everything is tonight's biggest deal.",
            "values": ["the crowd", "a good shout", "tomorrow's rumor"],
            "likes": ["full stalls", "duels at dusk", "fresh scandals"],
            "dislikes": ["empty canyons", "quiet bidders", "tax assessors"],
            "relationship_behavior": {
                "hostile": "Your name gets auctioned as a curse.",
                "neutral": "Announces your arrivals with invented titles.",
                "friendly": "Sells your deeds at a flattering margin.",
                "trusted": "Only shouts what you approve first.",
            },
            "morality_reaction": {
                "righteous": "'Righteous! Excellent brand! The crowd loves it!'",
                "neutral": "'Mysterious stranger — that sells in every canyon!'",
                "demonic": "'Demonic! Scandalous! Come closer, don't be shy!'",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": False,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "", "quest_ids": ["market_stall_wars"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "A herald vaults onto a crate. 'Fresh cultivator, straight off the "
            "road! What's your story? The canyon pays for stories!'"
        ),
        "repeat_text": "'Your title's grown three syllables. The crowd will love it.'",
    },
    {
        "id": "terrace_shrine_keeper",
        "name": "Shrine Keeper Wen",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "river_shrine_keeper",
        "alignment": "neutral_good",
        "importance": "minor",
        "faction": "Unaffiliated",
        "encounter_type": "neutral",
        "min_story_tier": 3,
        "unlock": {"realm": "Body Tempering", "min_stage": 6},
        "encounter_weight": 2,
        "personality": {
            "traits": ["devoted", "gentle", "firm", "old-fashioned", "perceptive"],
            "speech_style": "Liturgical calm broken by sudden practicality.",
            "values": ["the river spirit's peace", "rites kept", "weary travelers"],
            "likes": ["clean shrines", "offered rice", "honest prayers"],
            "dislikes": ["mocking cultivators", "graven tolls", "broken bells"],
            "relationship_behavior": {
                "hostile": "The shrine's bells warn the village of you.",
                "neutral": "Offers incense and a bowl of water.",
                "friendly": "Prays for your road and shares the shrine tea.",
                "trusted": "Names you a friend of the river spirit.",
            },
            "morality_reaction": {
                "righteous": "Bows. The spirit favors your kind.",
                "neutral": "The spirit asks little: keep the bells whole.",
                "demonic": "Even demons bow somewhere. Show me where.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": False,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "", "quest_ids": ["terrace_bells"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "An old keeper rings a bronze bell twice. 'The river spirit asks "
            "after travelers. Will you carry its question to the coast?'"
        ),
        "repeat_text": "'The bell rang twice today. The spirit is pleased.'",
    },
    # -- Southern Sea -------------------------------------------------------
    {
        "id": "diver_maru",
        "name": "Diver Maru",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "pearl_diver",
        "alignment": "neutral",
        "importance": "minor",
        "faction": "Pearl Tide Pavilion",
        "encounter_type": "ally",
        "min_story_tier": 4,
        "unlock": {"realm": "Qi Condensation", "min_stage": 3},
        "encounter_weight": 3,
        "personality": {
            "traits": ["fearless", "taciturn", "superstitious", "loyal", "weathered"],
            "speech_style": "Surface-and-depth speech: few words, deep meaning.",
            "values": ["a held breath", "the boat's safety", "the deep's rules"],
            "likes": ["clear water", "full nets", "quiet rows home"],
            "dislikes": ["shark bells", "greedy quotas", "storm signs ignored"],
            "relationship_behavior": {
                "hostile": "Rows away and leaves you to the tide.",
                "neutral": "Shares the boat and the bailing work.",
                "friendly": "Shows you the safe dives and the good reefs.",
                "trusted": "Dives the drowned dark with you at your back.",
            },
            "morality_reaction": {
                "righteous": "Trusts the vow; the sea tests it anyway.",
                "neutral": "The tide takes all sorts; hands matter most.",
                "demonic": "Blood in the water draws what shouldn't feed.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": False,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "", "quest_ids": ["deep_reef_lanterns"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "A diver coils rope with scarred hands. 'Reef lanterns went dark "
            "past the third bar. Boats won't dive. Will you?'"
        ),
        "repeat_text": "'Lanterns still burning. The reef remembers your hands.'",
    },
    {
        "id": "cove_quartermaster_vex",
        "name": "Quartermaster Vex",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "pirate_quartermaster",
        "alignment": "demonic",
        "importance": "support",
        "faction": "Tidecrook Pirates",
        "encounter_type": "neutral",
        "min_story_tier": 4,
        "unlock": {"realm": "Qi Condensation", "min_stage": 4},
        "encounter_weight": 3,
        "personality": {
            "traits": ["dry", "greedy", "fair-minded", "observant", "unsentimental"],
            "speech_style": "Ledger entries read aloud as threats.",
            "values": ["honest shares", "the cove's books", "weights and measures"],
            "likes": ["balanced scales", "paid harbor weight", "clean thefts"],
            "dislikes": ["short weights", "romantic pirates", "burnt cargo"],
            "relationship_behavior": {
                "hostile": "Your debts are sold to collection crews.",
                "neutral": "Quotes fair prices for unfair goods.",
                "friendly": "Rounds shares in your favor, quietly.",
                "trusted": "Falsifies the ledger for you once. Never twice.",
            },
            "morality_reaction": {
                "righteous": "Righteous coin is still coin; the scales don't care.",
                "neutral": "Ideal customer: predictable weights.",
                "demonic": "Demonic shares run rich. The cove approves.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": True,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "tide_king_hei_duel", "quest_ids": ["cove_ledger_fires"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "A quartermaster scratches figures onto slate. 'You owe harbor "
            "weight or labor. The ledger prefers labor.'"
        ),
        "repeat_text": "'Your line in the ledger reads better each visit.'",
    },
    {
        "id": "reef_warden_nimbus",
        "name": "Reef Warden Nimbus",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "reef_warden",
        "alignment": "neutral_good",
        "importance": "support",
        "faction": "Pearl Tide Pavilion",
        "encounter_type": "ally",
        "min_story_tier": 4,
        "unlock": {"realm": "Qi Condensation", "min_stage": 4},
        "encounter_weight": 2,
        "personality": {
            "traits": ["vigilant", "brisk", "principled", "salty", "protective"],
            "speech_style": "Watch-report clippedness.",
            "values": ["the reef's peace", "marked lanes", "rescue first"],
            "likes": ["lit lanterns", "clean hulls", "sailors who signal"],
            "dislikes": ["wreckers", "bait poachers", "night sails unlogged"],
            "relationship_behavior": {
                "hostile": "Every lane in the shallows turns you away.",
                "neutral": "Logs your passage and watches your wake.",
                "friendly": "Shares the watch's charts and hidden anchors.",
                "trusted": "Wrecks your name from every wrecker's list.",
            },
            "morality_reaction": {
                "righteous": "The watch salutes the creed and the rescue both.",
                "neutral": "Signal properly and all is proper.",
                "demonic": "Dark sails get dark water. Choose your lane.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": True, "can_duel": False,
            "can_train_player": False, "can_give_quest": False, "can_join_player": False,
            "enemy_id": "reef_warden_nimbus_spar", "quest_ids": [],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "A warden swings a signal lantern in slow arcs. 'State your lane, "
            "traveler. Or spar, and let the water decide it.'"
        ),
        "repeat_text": "'Lane logged. The reef stays bright behind you.'",
    },
    {
        "id": "atoll_turnkey_owl",
        "name": "Turnkey Owl",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "prison_turnkey",
        "alignment": "neutral_hostile",
        "importance": "minor",
        "faction": "Unaffiliated",
        "encounter_type": "antagonist",
        "min_story_tier": 4,
        "unlock": {"realm": "Qi Condensation", "min_stage": 5},
        "encounter_weight": 2,
        "personality": {
            "traits": ["creepy", "meticulous", "ancient", "chatty", "merciless"],
            "speech_style": "Cell counts and tide times recited like lullabies.",
            "values": ["the tide schedule", "kept prisoners", "quiet keys"],
            "likes": ["cells that stay shut", "loud keys", "high water"],
            "dislikes": ["escapees", "rescuers", "low tides"],
            "relationship_behavior": {
                "hostile": "Offers a cell and means it.",
                "neutral": "Chirps tide times and cell numbers at you.",
                "friendly": "Looks away from small smugglings.",
                "trusted": "Shows you which cells have long been empty.",
            },
            "morality_reaction": {
                "righteous": "Rescuers keep the tide fed, one way or another.",
                "neutral": "Visitors are just prisoners who arrived freely.",
                "demonic": "Demonic guests get the dry cells. Professional courtesy.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": True,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "atoll_turnkey_owl_duel", "quest_ids": ["atoll_nightfall_rounds"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "A bent figure jangles a hundred keys at once. 'Four hundred and "
            "eleven cells. The tide fills four hundred tonight. Curious?'"
        ),
        "repeat_text": "'The count holds. Four hundred and eleven, always.'",
    },
    {
        "id": "mist_shipwright_halloo",
        "name": "Shipwright Halloo",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "mist_shipwright",
        "alignment": "neutral",
        "importance": "minor",
        "faction": "Unaffiliated",
        "encounter_type": "neutral",
        "min_story_tier": 4,
        "unlock": {"realm": "Qi Condensation", "min_stage": 3},
        "encounter_weight": 2,
        "personality": {
            "traits": ["obsessive", "brilliant", "rambling", "brave", "unlucky"],
            "speech_style": "Keel-shape jargon at full speed.",
            "values": ["the perfect hull", "mist-proof joinery", "the lost fleet"],
            "likes": ["mist-cured timber", "brave sailors", "nobody touching the chalk lines"],
            "dislikes": ["storm repairs", "naval requisitions", "questions about the old fleet"],
            "relationship_behavior": {
                "hostile": "Your commissions rot in the fog.",
                "neutral": "Priced work, delivered crooked, patched free.",
                "friendly": "Lends mist-charts older than the kingdom.",
                "trusted": "Builds for you the hull the fog cannot hold.",
            },
            "morality_reaction": {
                "righteous": "Good crews deserve good hulls. Pay on time.",
                "neutral": "Wood floats for anyone with coin.",
                "demonic": "Demonic sails billow strong. He pretends not to admire.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": False,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "", "quest_ids": ["mist_keel_timbers"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "A shipwright chalks a hull on the fog itself. 'The mist took my "
            "fleet and kept the timbers. Bring me what it returns.'"
        ),
        "repeat_text": "'The chalk lines still hold. So does the fleet's shape.'",
    },
    # -- Central Region / endgame -------------------------------------------
    {
        "id": "forge_apprentice_cinder",
        "name": "Apprentice Cinder",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "forge_apprentice",
        "alignment": "neutral",
        "importance": "minor",
        "faction": "Furnace Forge Society",
        "encounter_type": "ally",
        "min_story_tier": 5,
        "unlock": {"realm": "Qi Condensation", "min_stage": 5},
        "encounter_weight": 3,
        "personality": {
            "traits": ["eager", "burnt", "honest", "talented", "stubborn"],
            "speech_style": "Quick, singed enthusiasm.",
            "values": ["the temper", "master's approval", "hands that heal crooked"],
            "likes": ["clean billets", "praise from Yan Huo", "heat that behaves"],
            "dislikes": ["cracked quench tubs", "show-offs", "cold mornings"],
            "relationship_behavior": {
                "hostile": "Your steel mysteriously warps in the queue.",
                "neutral": "Grinds your edge and quotes the master's rates.",
                "friendly": "Finishes your commissions overnight, off-book.",
                "trusted": "Forges with you the blade the master won't touch.",
            },
            "morality_reaction": {
                "righteous": "Righteous hands make steadier hammers, somehow.",
                "neutral": "Steel's steel. Bring billets, not speeches.",
                "demonic": "Demonic quench-water never cracks. He's checked.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": True, "can_duel": False,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "forge_apprentice_cinder_spar", "quest_ids": ["salamander_cores"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "An apprentice with singed brows salutes with tongs. 'Salamander "
            "cores ran the vents again. Help me herd them, hammer-brother?'"
        ),
        "repeat_text": "'Vents are quiet. The master noticed your hammer-work.'",
    },
    {
        "id": "ash_priestess_solene",
        "name": "Ash Priestess Solene",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "ash_priestess",
        "alignment": "hostile",
        "importance": "rival",
        "faction": "Emberfall War Pavilion",
        "encounter_type": "antagonist",
        "min_story_tier": 5,
        "unlock": {"realm": "Qi Condensation", "min_stage": 6},
        "encounter_weight": 2,
        "personality": {
            "traits": ["serene", "fanatical", "perceptive", "ruthless", "poetic"],
            "speech_style": "Funeral-rite cadence for living audiences.",
            "values": ["the ash's truth", "clean endings", "the pavilion's ledger"],
            "likes": ["settled dust", "confessed enemies", "quiet after battle"],
            "dislikes": ["lingering grudges", "unburied dead", "hesitant blades"],
            "relationship_behavior": {
                "hostile": "Pre-assigns your funeral verse.",
                "neutral": "Reads your ash-count and says little.",
                "friendly": "Shares the rite's mercies: quick ends, clean names.",
                "trusted": "Burns your enemies' names beside yours in honor.",
            },
            "morality_reaction": {
                "righteous": "Righteousness burns brightest. It also burns out.",
                "neutral": "Ash is ash. The verse adapts.",
                "demonic": "Demonic ash sings. She has written it down.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": True,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "war_pavilion_envoy_ru_duel", "quest_ids": ["citadel_unburied"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "A priestess sifts ash through ringed fingers. 'The citadel's dead "
            "go unburied. Settle them, and your name enters the verse.'"
        ),
        "repeat_text": "'Your verse is written. It is not a funeral yet.'",
    },
    {
        "id": "zen_bell_ringer_mo",
        "name": "Bell Ringer Mo",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "wilds_bell_ringer",
        "alignment": "neutral_good",
        "importance": "minor",
        "faction": "Unaffiliated",
        "encounter_type": "mentor",
        "min_story_tier": 5,
        "unlock": {"realm": "Qi Condensation", "min_stage": 5},
        "encounter_weight": 2,
        "personality": {
            "traits": ["gentle", "deaf", "perceptive", "patient", "strong"],
            "speech_style": "Lip-read questions answered before they're asked.",
            "values": ["the bell's sweep", "heard silence", "the shrine's sweep"],
            "likes": ["rung bells", "swept paths", "travelers who bow"],
            "dislikes": ["clappers stolen", "hurry", "cruel laughter"],
            "relationship_behavior": {
                "hostile": "The bell's silence marks your road as unsafe.",
                "neutral": "Rings once for your arrival, and offers tea.",
                "friendly": "Sweeps a path for you and rings it clean.",
                "trusted": "Rings the old warning-peal only friends may ring.",
            },
            "morality_reaction": {
                "righteous": "Bows. The bell rings itself for the righteous.",
                "neutral": "All guests ring the same. Few notice.",
                "demonic": "Rings twice: once welcome, once warning.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": False,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "", "quest_ids": ["wilds_silent_bells"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "A bell ringer mimes a question: which bell have you come to hear? "
            "The shrine's, or the storm's?"
        ),
        "repeat_text": "The ringer bows: the bells are loud again. Your doing.",
    },
    {
        "id": "temple_scribe_quin",
        "name": "Scribe Quin of the Undercroft",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "rune_scribe",
        "alignment": "neutral",
        "importance": "support",
        "faction": "Rune Temple Order",
        "encounter_type": "ally",
        "min_story_tier": 6,
        "unlock": {"realm": "Qi Condensation", "min_stage": 7},
        "encounter_weight": 2,
        "personality": {
            "traits": ["bookish", "exact", "curious", "brave-when-inked", "dry-witted"],
            "speech_style": "Footnotes aloud; citations of element and hall.",
            "values": ["the circuit's record", "exact runes", "verified pilgrims"],
            "likes": ["clean rubbings", "balanced elements", "guests who sign in"],
            "dislikes": ["smudged runes", "unverified claims", "burnt pages"],
            "relationship_behavior": {
                "hostile": "Your record reads 'unverified: barred'.",
                "neutral": "Logs your passage in triplicate.",
                "friendly": "Annotates your deeds in the order's margin.",
                "trusted": "Shows you pages the wardens never cite aloud.",
            },
            "morality_reaction": {
                "righteous": "'Righteous: see volume nine, chapter four.'",
                "neutral": "'Unspecified alignment. I will write 'pending'.'",
                "demonic": "'Demonic: the ink resists. Fascinating.'",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": False,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "", "quest_ids": ["circuit_prime_rubbings"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "A scribe ink-brushes a rubbing of humming stone. 'The prime "
            "circuit's outer runes went illegible. Paper, courage, or both?'"
        ),
        "repeat_text": "'Your entry is footnoted twice. That is an honor.'",
    },
    {
        "id": "stair_ascendant_lo",
        "name": "Ascendant Lo",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "stair_rival",
        "alignment": "neutral",
        "importance": "rival",
        "faction": "Unaffiliated",
        "encounter_type": "rival",
        "min_story_tier": 6,
        "unlock": {"realm": "Qi Condensation", "min_stage": 8},
        "encounter_weight": 2,
        "personality": {
            "traits": ["driven", "courteous", "restless", "probing", "lonely"],
            "speech_style": "Counting steps between sentences.",
            "values": ["the climb", "proved rivals", "the final step"],
            "likes": ["stiffer climbs", "honest duels", "star-lit landings"],
            "dislikes": ["descenders", "shortcuts", "wasted stairs"],
            "relationship_behavior": {
                "hostile": "Blocks the stair until you climb past her.",
                "neutral": "Nods at the landing and counts her breaths.",
                "friendly": "Shares landings and climbing rations.",
                "trusted": "Severing-step duels you at every seventh stair.",
            },
            "morality_reaction": {
                "righteous": "Climbs a little faster. Competition honors both.",
                "neutral": "The stair sorts all climbers alike.",
                "demonic": "Dark climbers reach far. She measures herself against you.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": True, "can_duel": True,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "stair_ascendant_lo_duel", "quest_ids": ["seven_landings"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "A climber sits mid-stair, counting. 'Forty-one thousand, two "
            "hundred and six. Duel me and add a number to both our counts.'"
        ),
        "repeat_text": "'The count grows. So does the stair's respect for you.'",
    },
    {
        "id": "ruin_broker_song",
        "name": "Broker Song of the Ruins",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "ruin_broker",
        "alignment": "neutral_hostile",
        "importance": "minor",
        "faction": "Unaffiliated",
        "encounter_type": "neutral",
        "min_story_tier": 5,
        "unlock": {"realm": "Qi Condensation", "min_stage": 6},
        "encounter_weight": 2,
        "personality": {
            "traits": ["slick", "learned", "mercenary", "fearless", "double-dealing"],
            "speech_style": "Appraisal jargon with prices embedded in poetry.",
            "values": ["provenance", "the find", "exit routes"],
            "likes": ["clean relics", "ignorant buyers", "two buyers for one lot"],
            "dislikes": ["sentimental sellers", "ruin wardens", "authenticity disputes"],
            "relationship_behavior": {
                "hostile": "Your finds get appraised, then acquired.",
                "neutral": "Appraises anything twice: once for you, once for him.",
                "friendly": "Splits finds at the finder's advantage.",
                "trusted": "Shows you the lots no buyer ever sees.",
            },
            "morality_reaction": {
                "righteous": "Righteous provenance sells best, he notes honestly.",
                "neutral": "Neutral relics appraise cleanest.",
                "demonic": "Demonic relics carry curses and premiums. Both noted.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": False,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "", "quest_ids": ["ruin_provenance_run"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "A broker unwraps a relic under his coat. 'Recovered, not stolen — "
            "there's a difference and it's priced. Care to see the list?'"
        ),
        "repeat_text": "'The list grew. Your cut grew with it. Ask me why.'",
    },
    {
        "id": "deepwood_beast_singer",
        "name": "Beast-Singer Ilsabet",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "beast_singer",
        "alignment": "neutral_good",
        "importance": "support",
        "faction": "Unaffiliated",
        "encounter_type": "ally",
        "min_story_tier": 3,
        "unlock": {"realm": "Body Tempering", "min_stage": 6},
        "encounter_weight": 2,
        "personality": {
            "traits": ["gentle", "fearless", "strange", "attentive", "melancholy"],
            "speech_style": "Half-spoken, half-hummed; answers in animal terms.",
            "values": ["the pack's peace", "sung boundaries", "the wood's grief"],
            "likes": ["calm predators", "shared kills", "unclanged bells"],
            "dislikes": ["cages", "trophy hunters", "the mist's newest hunger"],
            "relationship_behavior": {
                "hostile": "The wood's eyes follow you until you leave.",
                "neutral": "Hums a boundary you may not cross.",
                "friendly": "Walks the packs with you and names their moods.",
                "trusted": "Sings the old pact: beast and cultivator, one wood.",
            },
            "morality_reaction": {
                "righteous": "The pack accepts creeds it can smell. Yours passes.",
                "neutral": "Beasts read hearts directly. Yours reads tame, for now.",
                "demonic": "She hears the hunger in you and names it to your face.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": False,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "", "quest_ids": ["pack_boundaries"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "A singer sits among wolves that are watching you. 'They want to "
            "know your song. Sing, fight, or fetch — the wood accepts all three.'"
        ),
        "repeat_text": "'The packs sing back when you pass now. That is rare.'",
    },
    {
        "id": "furnace_ore_scout_bram",
        "name": "Ore Scout Bram",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "ore_scout",
        "alignment": "neutral",
        "importance": "minor",
        "faction": "Furnace Forge Society",
        "encounter_type": "ally",
        "min_story_tier": 5,
        "unlock": {"realm": "Qi Condensation", "min_stage": 5},
        "encounter_weight": 3,
        "personality": {
            "traits": ["grizzled", "superstitious", "tough", "laconic", "loyal"],
            "speech_style": "Ore-grade shorthand.",
            "values": ["a good vein", "the crew's return", "the mountain's due"],
            "likes": ["ringing picks", "clean tunnels", "paid crews"],
            "dislikes": ["collapses", "ore-thieves", "veins that hum wrong"],
            "relationship_behavior": {
                "hostile": "Your claim gets jumped, legally.",
                "neutral": "Marks you a fair seam and walks off.",
                "friendly": "Shares strike maps older than the kingdom.",
                "trusted": "Brings you down the vein the Society doesn't map.",
            },
            "morality_reaction": {
                "righteous": "Good tithe-payers get good maps.",
                "neutral": "Ore's ore. Hands are hands.",
                "demonic": "Demonic blood makes the mountain talk. He's heard it.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": False,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "", "quest_ids": ["humming_seam"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "A scout taps rock twice, listening. 'Third seam's ringing wrong. "
            "Fancy a look before the mountain decides?'"
        ),
        "repeat_text": "'Seam's quiet since you went down. The crew drinks your name.'",
    },
    {
        "id": "pearl_auctioneer_lo_fan",
        "name": "Auctioneer Lo Fan",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "pearl_auctioneer",
        "alignment": "neutral",
        "importance": "minor",
        "faction": "Pearl Tide Pavilion",
        "encounter_type": "neutral",
        "min_story_tier": 4,
        "unlock": {"realm": "Qi Condensation", "min_stage": 3},
        "encounter_weight": 2,
        "personality": {
            "traits": ["polished", "sharp", "theatrical", "greedy", "impartial"],
            "speech_style": "Rising bid-cadence that never fully stops.",
            "values": ["the hammer", "fair plates", "the pavilion's cut"],
            "likes": ["spirited bidding", "authenticated pearls", "quiet rooms"],
            "dislikes": ["shills", "snuffed candles", "sea-stained coin"],
            "relationship_behavior": {
                "hostile": "Your lots are withdrawn from every catalog.",
                "neutral": "Books your finds at honest reserve prices.",
                "friendly": "Waives the pavilion's cut on your first lots.",
                "trusted": "Runs closed auctions where only your lots appear.",
            },
            "morality_reaction": {
                "righteous": "Righteous bidders bid clean. The room approves.",
                "neutral": "Bidders bid. That is the whole of the law.",
                "demonic": "Demonic coin bids high. The gavel falls all the same.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": False,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "", "quest_ids": ["salvage_lots"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "An auctioneer taps a small gavel. 'Salvage lots, dusk seating, "
            "one mysterious guest required. Shall I pencil you in?'"
        ),
        "repeat_text": "'Your lots drew a full room. The gavel remembers.'",
    },
    {
        "id": "tide_oracle_sable",
        "name": "Tide Oracle Sable",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "tide_oracle",
        "alignment": "neutral",
        "importance": "special",
        "faction": "Unaffiliated",
        "encounter_type": "entity",
        "min_story_tier": 4,
        "unlock": {"realm": "Qi Condensation", "min_stage": 4},
        "encounter_weight": 2,
        "personality": {
            "traits": ["cryptic", "salt-eyed", "kind", "unsettling", "honest"],
            "speech_style": "Tide-tables as prophecy: times, heights, and turnings.",
            "values": ["the turning", "honest readings", "the sea's memory"],
            "likes": ["asked questions", "salt offerings", "kept appointments"],
            "dislikes": ["false tides", "demanded futures", "hungry spirits"],
            "relationship_behavior": {
                "hostile": "Your tide reads out as storm, always.",
                "neutral": "Reads your tide and charges a small fish.",
                "friendly": "Reads the undercurrents others miss.",
                "trusted": "Tells you when your own tide turns. Once.",
            },
            "morality_reaction": {
                "righteous": "Righteous tides run bright. She says it without awe.",
                "neutral": "Neutral tides are the easiest to read. Lucky you.",
                "demonic": "Demonic tides run red. She has seen yours already.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": False,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "", "quest_ids": ["red_tide_reading"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "A blind oracle tastes the wind. 'Red under the tide-turn tonight. "
            "Someone bleeds for the sea whether they choose it or not.'"
        ),
        "repeat_text": "'The red passed. Your name is not in tomorrow's table.'",
    },
    {
        "id": "ember_armsmith_juno",
        "name": "Armsmith Juno",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "citadel_armsmith",
        "alignment": "neutral",
        "importance": "minor",
        "faction": "Emberfall War Pavilion",
        "encounter_type": "neutral",
        "min_story_tier": 5,
        "unlock": {"realm": "Qi Condensation", "min_stage": 5},
        "encounter_weight": 2,
        "personality": {
            "traits": ["stoic", "particular", "proud", "fair", "scarred"],
            "speech_style": "Weapon specs delivered like verdicts.",
            "values": ["true edges", "the ring's safety", "honest steel"],
            "likes": ["well-kept blades", "duels that end clean", "quiet forges"],
            "dislikes": ["curved lies", "dulled practice steel", "smuggled poison"],
            "relationship_behavior": {
                "hostile": "Every edge you own goes quietly dull.",
                "neutral": "Sharpens what you carry, names a fair price.",
                "friendly": "Repairs your steel before you ask.",
                "trusted": "Forges you the blade she keeps for herself.",
            },
            "morality_reaction": {
                "righteous": "Righteous hands swing true. She has measured yours.",
                "neutral": "Steel serves whoever holds it well.",
                "demonic": "Demonic steel cuts deeper. She oils it the same.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": False,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "", "quest_ids": ["ring_steel_standards"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "An armsmith balances a dueling blade on one finger. 'The ring's "
            "steel walks off every night. Watch the racks, earn the forge's cut.'"
        ),
        "repeat_text": "'Rack's full and honest. The forge sleeps easy.'",
    },
    {
        "id": "zen_gardener_pale",
        "name": "Pale Gardener of the Wilds",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "zen_gardener",
        "alignment": "neutral_good",
        "importance": "minor",
        "faction": "Unaffiliated",
        "encounter_type": "mentor",
        "min_story_tier": 5,
        "unlock": {"realm": "Qi Condensation", "min_stage": 5},
        "encounter_weight": 2,
        "personality": {
            "traits": ["quiet", "ancient", "amused", "rooted", "sharp-tongued"],
            "speech_style": "Gardening metaphors that prune to the point.",
            "values": ["pruned growth", "the long season", "weeds pulled honestly"],
            "likes": ["raked gravel", "answered questions", "weeds by the root"],
            "dislikes": ["forced blooms", "shortcut trellises", "uninvited pruners"],
            "relationship_behavior": {
                "hostile": "You find yourself pruned from every path.",
                "neutral": "Points you to the weeds and lends a hoe.",
                "friendly": "Teaches which growths feed and which strangle.",
                "trusted": "Shows you the garden under the garden.",
            },
            "morality_reaction": {
                "righteous": "Righteous growth runs tall. Watch the shadow it casts.",
                "neutral": "Neutral soil takes any seed. Convenient.",
                "demonic": "Demonic blooms drink deep. Prune before they seed.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": False,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "", "quest_ids": ["wilds_strangling_vines"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "An ancient gardener pulls a weed the size of an arm. 'The wilds "
            "grow strangler vines that dress as pilgrims. Bring a sharp eye.'"
        ),
        "repeat_text": "'The gravel's raked where you knelt. Growth acknowledged.'",
    },
    {
        "id": "undercroft_convict_nine",
        "name": "Convict Nine of the Circuit",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "circuit_convict",
        "alignment": "neutral_hostile",
        "importance": "minor",
        "faction": "Unaffiliated",
        "encounter_type": "antagonist",
        "min_story_tier": 6,
        "unlock": {"realm": "Qi Condensation", "min_stage": 7},
        "encounter_weight": 2,
        "personality": {
            "traits": ["caged", "cunning", "half-runic", "bitter", "honest"],
            "speech_style": "Speaks in circuit verses he cannot stop reciting.",
            "values": ["his name back", "the circuit's mercy", "one honest deal"],
            "likes": ["ink that stays", "visitor noise", "counts he can break"],
            "dislikes": ["wardens", "his own verses", "mercy he can't trust"],
            "relationship_behavior": {
                "hostile": "Sells your rune-signature to whatever listens.",
                "neutral": "Trades verse-answers for news of the surface.",
                "friendly": "Warns you which halls are watching.",
                "trusted": "Gives you the verse that unlocks his cell. Asks nothing.",
            },
            "morality_reaction": {
                "righteous": "'Righteous. The circuit keeps a cell for your kind too.'",
                "neutral": "'Neutral. The circuit loves neutral. It never has to choose.'",
                "demonic": "'Demonic. The verses say we are cousins. I spit on the verses.'",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": True,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "undercroft_convict_nine_duel", "quest_ids": ["convict_name_verse"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "A rune-branded prisoner recites without pausing. 'Free verse for "
            "free news. What's the price of a name down here, visitor?'"
        ),
        "repeat_text": "'You came back. The verses count that as a debt.'",
    },
    {
        "id": "gate_warden_prime_astrid",
        "name": "Warden Prime Astrid",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "gate_warden_prime",
        "alignment": "neutral",
        "importance": "major_support",
        "faction": "Rune Temple Order",
        "encounter_type": "entity",
        "min_story_tier": 6,
        "unlock": {"realm": "Qi Condensation", "min_stage": 8},
        "encounter_weight": 2,
        "personality": {
            "traits": ["immovable", "just", "ancient", "formal", "quietly kind"],
            "speech_style": "Warden's litany: terms, proofs, and doors.",
            "values": ["the gate's terms", "proved worth", "one open door"],
            "likes": ["honest climbs", "paid prices", "kept stairways"],
            "dislikes": ["bribes", "uninvited ascensions", "desecrated stairs"],
            "relationship_behavior": {
                "hostile": "The stair simply ends for you, wherever you stand.",
                "neutral": "States the gate's terms and waits.",
                "friendly": "Proves your small worths early to spare you later.",
                "trusted": "Names you stair-true and walks one landing down with you.",
            },
            "morality_reaction": {
                "righteous": "Righteousness is a coin the gate accepts. It still costs.",
                "neutral": "The gate weighs steps. It does not weigh gods.",
                "demonic": "Demonic climbers pay in years. Bring coin for the fare.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": True, "can_duel": True,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "gate_warden_prime_astrid_duel", "quest_ids": ["gate_terms_proof"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "A warden of layered stone blocks seven stairs at once. 'The gate "
            "takes proofs, not prayers. Which proof will you attempt?'"
        ),
        "repeat_text": "'Your proofs stand. The stair remembers its true climbers.'",
    },
    {
        "id": "pearl_smuggler_gale",
        "name": "Smuggler Gale",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "pearl_smuggler",
        "alignment": "neutral_hostile",
        "importance": "minor",
        "faction": "Tidecrook Pirates",
        "encounter_type": "rival",
        "min_story_tier": 4,
        "unlock": {"realm": "Qi Condensation", "min_stage": 3},
        "encounter_weight": 2,
        "personality": {
            "traits": ["swift", "cheerful", "treacherous", "skilled", "curious"],
            "speech_style": "Wind-talk: swells, gusts, and lee shores.",
            "values": ["a clean run", "the wind's favor", "one more port"],
            "likes": ["fast hulls", "dark nights", "ports with no questions"],
            "dislikes": ["wardens' lanterns", "heavy cargo", "shared routes"],
            "relationship_behavior": {
                "hostile": "Your cargo grows barnacles in every market.",
                "neutral": "Runs one small parcel, no questions asked.",
                "friendly": "Shares moonless calendars and quiet coves.",
                "trusted": "Sails your cargo through the panopticon's watch.",
            },
            "morality_reaction": {
                "righteous": "Righteous fares pay double. He smiles saying it.",
                "neutral": "Neutral cargo rides lowest in the hold.",
                "demonic": "Demonic runs taste of storm. He charges for that.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": True, "can_duel": True,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "pearl_smuggler_gale_duel", "quest_ids": ["moonless_run"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "A smuggler leans on a rigged mast. 'Moonless run in three nights. "
            "Half-share for a blade that can keep up. Interested?'"
        ),
        "repeat_text": "'The wind's good and the run's clean. Same terms.'",
    },
    {
        "id": "valley_wandering_poet_xu",
        "name": "Wandering Poet Xu",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "wandering_poet",
        "alignment": "neutral_good",
        "importance": "minor",
        "faction": "Unaffiliated",
        "encounter_type": "neutral",
        "min_story_tier": 3,
        "unlock": {"realm": "Body Tempering", "min_stage": 6},
        "encounter_weight": 2,
        "personality": {
            "traits": ["witty", "idle", "kind", "observing", "wine-scented"],
            "speech_style": "Couplets that flatter, needle, and record.",
            "values": ["a good line", "witnessed deeds", "tomorrow's wine"],
            "likes": ["duels at dusk", "fresh scandals", "patrons with enemies"],
            "dislikes": ["censors", "empty notebooks", "unpoetic violence"],
            "relationship_behavior": {
                "hostile": "Your deeds enter verse as cautionary tales.",
                "neutral": "Records your arrival in four neat lines.",
                "friendly": "Immortalizes your victories (lightly edited).",
                "trusted": "Shows you the verses the sects paid him not to write.",
            },
            "morality_reaction": {
                "righteous": "'Righteous deeds sell. Forgive me the embellishments.'",
                "neutral": "'Neutral is hard to rhyme. You could help.'",
                "demonic": "'Demonic verse writes itself. Forgive me the truth.'",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": False,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "", "quest_ids": ["poets_lost_verse"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "A poet toasts you with an empty cup. 'Deeds are common; poems are "
            "not. Give me a deed worth the ink, friend.'"
        ),
        "repeat_text": "'Your verse is famous in two canyons. The wine follows.'",
    },
    {
        "id": "sea_lantern_tender_uma",
        "name": "Lantern Tender Uma",
        "region": "Sky Spill World",
        "starting_world": True,
        "role": "lantern_tender",
        "alignment": "neutral_good",
        "importance": "minor",
        "faction": "Pearl Tide Pavilion",
        "encounter_type": "ally",
        "min_story_tier": 4,
        "unlock": {"realm": "Qi Condensation", "min_stage": 3},
        "encounter_weight": 3,
        "personality": {
            "traits": ["steady", "brave", "quiet", "responsible", "haunted"],
            "speech_style": "Counts and conditions: lights kept, lights lost.",
            "values": ["the lane's light", "every boat home", "the drowned remembered"],
            "likes": ["kept wicks", "returned boats", "sailors who wave"],
            "dislikes": ["snuffed lanterns", "wreckers' signals", "fog with voices"],
            "relationship_behavior": {
                "hostile": "Your channel goes dark at every turning.",
                "neutral": "Trims your lane's wicks and asks nothing.",
                "friendly": "Shows you the lost lights' turning-places.",
                "trusted": "Tells you what the drowned lanterns saw.",
            },
            "morality_reaction": {
                "righteous": "Righteous lights burn steady. She relies on that.",
                "neutral": "Lights don't judge. They just burn.",
                "demonic": "Demonic light draws deep things. Burn it far from shore.",
            },
        },
        "gameplay_hooks": {
            "can_talk": True, "can_spar": False, "can_duel": False,
            "can_train_player": False, "can_give_quest": True, "can_join_player": False,
            "enemy_id": "", "quest_ids": ["drowned_lanterns"],
            "teaches_skills": [], "relationship_rewards": [],
        },
        "intro_text": (
            "A tender wicks a lantern taller than herself. 'Three lane-lights "
            "went out past the bar last night. Not wind. Will you row?'"
        ),
        "repeat_text": "'Lane's bright again. The boats follow light like thanks.'",
    },
]

# --------------------------------------------------------------------------
# 4. Wave-2 quests (26: zone chains + character quests).
#    Objective vocab: defeat / visit_location / breakthrough / spar / debate /
#    join_sect / dao_awakening / tournament / realm_completed.
# --------------------------------------------------------------------------
QUESTS = [
    # -- Zone chains (defeat/visit arcs through the new locations) ----------
    {
        "id": "wharf_silt_beasts",
        "title": "Silt-Beasts of the Wharf",
        "description": (
            "Reed-Cutter Min's nets keep coming up torn: silt-beasts have "
            "nested in the pilings. Clear them and the wharf pays in fish and coin."
        ),
        "requires": {"completed": ["act1_conclusion"]},
        "objectives": [
            {"type": "defeat", "target": "field_bandit", "count": 3, "text": "Drive off 3 pilings raiders"},
            {"type": "defeat", "target": "thornwood_cutpurse", "count": 2, "text": "Break 2 cutpurses' dens"},
        ],
        "rewards": {"exp": 120, "gold": 70, "reputation": 5, "items": {"healing_pill": 3}},
    },
    {
        "id": "thornline_cull",
        "title": "Cull on the Thorn Line",
        "description": (
            "Karu's trail marks have been crossed by something heavy. Walk the "
            "thorn line with him and put down what's breaking it."
        ),
        "requires": {"completed": ["act1_conclusion"]},
        "objectives": [
            {"type": "spar", "target": "mistwood_ranger_elder_spar", "count": 1, "text": "Trade blows with Elder Shan"},
            {"type": "defeat", "target": "thornwood_bull", "count": 3, "text": "Fell 3 thornwood bulls"},
        ],
        "rewards": {"exp": 150, "gold": 60, "reputation": 6},
    },
    {
        "id": "outskirts_fences",
        "title": "Fences Against the Night",
        "description": (
            "Olive's farmland loses stock every moonless night. Mend the "
            "fences by clearing whatever uses the gaps, and the terraces feed you well."
        ),
        "requires": {"completed": ["act1_conclusion"]},
        "objectives": [
            {"type": "defeat", "target": "field_scorpion", "count": 3, "text": "Clear 3 scorpion nests"},
            {"type": "defeat", "target": "shade_lizard", "count": 2, "text": "Drive off 2 shade lizards"},
        ],
        "rewards": {"exp": 110, "gold": 55, "reputation": 4, "items": {"great_return_tonic": 2}},
    },
    {
        "id": "peaks_pool_trial",
        "title": "The Cloud Pool Trial",
        "description": (
            "Hermit Bai offers the peaks' oldest lesson: stillness that "
            "answers back. Match the pool's breathing, then match his."
        ),
        "requires": {"completed": ["act1_conclusion"]},
        "objectives": [
            {"type": "visit_location", "target": "seven_profound_low_peaks", "count": 1, "text": "Climb to the low peaks"},
            {"type": "spar", "target": "cloud_pool_hermit_bai_spar", "count": 1, "text": "Match blows with the hermit"},
        ],
        "rewards": {"exp": 190, "gold": 80, "reputation": 8, "items": {"qi_pill": 3}},
    },
    {
        "id": "market_stall_wars",
        "title": "The Stall Wars",
        "description": (
            "Duo the crier has brokered a truce between two stall cartels — "
            "both immediately hired enforcers. Restore the canyon's peace, loudly."
        ),
        "requires": {"completed": ["act1_conclusion"]},
        "objectives": [
            {"type": "defeat", "target": "capital_cutpurse", "count": 3, "text": "Dissuade 3 hired cutpurses"},
            {"type": "debate", "target": "gambler_king_tan", "count": 1, "text": "Win Tan's public concession"},
        ],
        "rewards": {"exp": 170, "gold": 90, "reputation": 6, "items": {"mystic_pill": 2}},
    },
    {
        "id": "terrace_bells",
        "title": "Ring the River Bells",
        "description": (
            "Shrine Keeper Wen asks a pilgrim's errand: carry the river "
            "spirit's blessing down to the coast shrine, clearing the road's trouble as you go."
        ),
        "requires": {"completed": ["act1_conclusion"]},
        "objectives": [
            {"type": "visit_location", "target": "south_sea_port", "count": 1, "text": "Carry the blessing to the sea"},
            {"type": "defeat", "target": "misty_boar", "count": 3, "text": "Clear 3 road beasts"},
        ],
        "rewards": {"exp": 160, "gold": 70, "reputation": 8, "items": {"soul_nurturing_pill": 2}},
    },
    {
        "id": "pack_boundaries",
        "title": "Sing the Pack Boundaries",
        "description": (
            "Beast-Singer Ilsabet needs a blade that walks quiet: the packs' "
            "boundaries are being crossed by something that hunts like a man."
        ),
        "requires": {"completed": ["act1_conclusion"]},
        "objectives": [
            {"type": "defeat", "target": "deepwood_assassin", "count": 2, "text": "Put down 2 false beasts"},
            {"type": "visit_location", "target": "deepwood_drift_outpost", "count": 1, "text": "Report the boundary at the drift"},
        ],
        "rewards": {"exp": 180, "gold": 80, "reputation": 7},
    },
    # -- Sea arc -------------------------------------------------------------
    {
        "id": "deep_reef_lanterns",
        "title": "Reef Lanterns Dark",
        "description": (
            "Diver Maru will dive where boats won't, with a blade at her back. "
            "Relight the reef lanterns and learn what snuffed them."
        ),
        "requires": {"completed": ["act1_conclusion"]},
        "objectives": [
            {"type": "defeat", "target": "sea_mantis", "count": 3, "text": "Clear 3 reef mantises"},
            {"type": "defeat", "target": "tidal_leopard", "count": 2, "text": "Fell 2 tide leopards"},
        ],
        "rewards": {"exp": 210, "gold": 100, "reputation": 6, "items": {"celestial_nectar": 2}},
    },
    {
        "id": "cove_ledger_fires",
        "title": "The Ledger Fires",
        "description": (
            "Quartermaster Vex's holding-house ledger burned with the pier — "
            "and several pirates are suddenly owed enormous sums. Recover the "
            "true ledger from the burners."
        ),
        "requires": {"completed": ["act1_conclusion"]},
        "objectives": [
            {"type": "defeat", "target": "sea_vulture", "count": 3, "text": "Ground 3 ledger-burners' wings"},
            {"type": "defeat", "target": "tidal_duelist", "count": 2, "text": "Break 2 of the burners' champions"},
        ],
        "rewards": {"exp": 230, "gold": 120},
    },
    {
        "id": "atoll_nightfall_rounds",
        "title": "Nightfall Rounds",
        "description": (
            "Turnkey Owl wants a visitor to walk the night rounds: cells that "
            "hold at dusk don't always hold at tide-turn. Keep the count at four hundred eleven."
        ),
        "requires": {"completed": ["act1_conclusion"]},
        "objectives": [
            {"type": "visit_location", "target": "coral_prison_atoll", "count": 1, "text": "Walk the atoll's night rounds"},
            {"type": "defeat", "target": "coral_serpent", "count": 3, "text": "Return 3 escaped swimmers"},
        ],
        "rewards": {"exp": 240, "gold": 110, "items": {"void_spirit_pill": 2}},
    },
    {
        "id": "mist_keel_timbers",
        "title": "Timbers the Fog Kept",
        "description": (
            "Shipwright Halloo swears the mist returns what it takes. Wreckage "
            "has been washing into the cove — salvage it before the pirates do."
        ),
        "requires": {"completed": ["act1_conclusion"]},
        "objectives": [
            {"type": "visit_location", "target": "sea_of_mist_expanse", "count": 1, "text": "Search the mist expanse"},
            {"type": "defeat", "target": "tidal_ape", "count": 3, "text": "Break 3 fog-possessed timbers' guardians"},
        ],
        "rewards": {"exp": 220, "gold": 130, "items": {"great_return_pill": 2}},
    },
    {
        "id": "salvage_lots",
        "title": "The Salvage Lots",
        "description": (
            "Auctioneer Lo Fan's dusk auction lacks a headliner: salvage fresh "
            "enough to draw the pavilion's big buyers. Fill the lot, quietly."
        ),
        "requires": {"completed": ["deep_reef_lanterns"]},
        "objectives": [
            {"type": "defeat", "target": "coral_tiger", "count": 2, "text": "Clear 2 lot-guarding reef tigers"},
            {"type": "visit_location", "target": "pearl_pavilion", "count": 1, "text": "Deliver the lots by dusk"},
        ],
        "rewards": {"exp": 260, "gold": 180, "items": {"star_gathering_pill": 2}},
    },
    {
        "id": "red_tide_reading",
        "title": "The Red Under-Tide",
        "description": (
            "Tide Oracle Sable read blood beneath the tide-turn. Find what "
            "bleeds the sea — or what the sea bleeds — before the reading comes true."
        ),
        "requires": {"completed": ["deep_reef_lanterns"]},
        "objectives": [
            {"type": "defeat", "target": "sea_zealot", "count": 4, "text": "End 4 red-tide zealots"},
            {"type": "visit_location", "target": "tidecrook_cove", "count": 1, "text": "Trace the reading to the cove"},
        ],
        "rewards": {"exp": 280, "gold": 140, "reputation": 5},
    },
    {
        "id": "moonless_run",
        "title": "The Moonless Run",
        "description": (
            "Smuggler Gale's moonless run needs a blade: the pearl routes are "
            "watched by both the pavilion and the pirates this week. See the hull through."
        ),
        "requires": {"completed": ["salvage_lots"]},
        "objectives": [
            {"type": "spar", "target": "pearl_smuggler_gale_duel", "count": 1, "text": "Prove your blade to Gale"},
            {"type": "visit_location", "target": "south_sea_port", "count": 1, "text": "Run the hull past the lantern line"},
        ],
        "rewards": {"exp": 300, "gold": 200, "items": {"phoenix_marrow_pill": 1}},
    },
    {
        "id": "drowned_lanterns",
        "title": "What the Drowned Lanterns Saw",
        "description": (
            "Lantern Tender Uma has kept a secret: the snuffed lane-lights "
            "show the same turning-place on their dark nights. Go and see it."
        ),
        "requires": {"completed": ["red_tide_reading"]},
        "objectives": [
            {"type": "visit_location", "target": "sea_of_mist_expanse", "count": 1, "text": "Row to the turning-place"},
            {"type": "defeat", "target": "tidal_serpent", "count": 2, "text": "Fell 2 turn-guardians"},
        ],
        "rewards": {"exp": 320, "gold": 160, "reputation": 8, "items": {"celestial_nectar": 3}},
    },
    # -- Central region / forge / citadel arc ---------------------------------
    {
        "id": "salamander_cores",
        "title": "Herd the Salamander Cores",
        "description": (
            "Apprentice Cinder's salamanders escaped into the vent-shafts "
            "again. Drive them home before the master's forge cools — and "
            "before they find the spirit-steel stores."
        ),
        "requires": {"completed": ["act1_conclusion"]},
        "objectives": [
            {"type": "defeat", "target": "flame_warfiend", "count": 3, "text": "Herd 3 wayward cores"},
            {"type": "spar", "target": "forge_apprentice_cinder_spar", "count": 1, "text": "Prove your hammer-hands"},
        ],
        "rewards": {"exp": 250, "gold": 120, "items": {"dragon_blood_pill": 2}},
    },
    {
        "id": "humming_seam",
        "title": "The Humming Seam",
        "description": (
            "Ore Scout Bram's third seam hums a note no vein should. Descend, "
            "silence what hums, and the Society's maps open to you."
        ),
        "requires": {"completed": ["act1_conclusion"]},
        "objectives": [
            {"type": "defeat", "target": "temple_hound", "count": 3, "text": "Silence 3 seam-hounds"},
            {"type": "defeat", "target": "elemental_leopard", "count": 2, "text": "Break 2 elemental prowlers"},
        ],
        "rewards": {"exp": 270, "gold": 140, "items": {"phoenix_marrow_pill": 2}},
    },
    {
        "id": "citadel_unburied",
        "title": "The Unburied of the Citadel",
        "description": (
            "Ash Priestess Solene will not sing a funeral for the unburied. "
            "Settle the citadel's walking dead, and the pavilion's verse gains your name."
        ),
        "requires": {"completed": ["act1_conclusion"]},
        "objectives": [
            {"type": "defeat", "target": "slaughter_revenant", "count": 3, "text": "Settle 3 unburied revenants"},
            {"type": "defeat", "target": "blood_golem", "count": 1, "text": "Put down the ring golem"},
        ],
        "rewards": {"exp": 300, "gold": 150, "items": {"blood_quenching_elixir": 2}},
    },
    {
        "id": "ring_steel_standards",
        "title": "Steel Standards for the Ring",
        "description": (
            "Armsmith Juno's dueling racks empty nightly. Catch the thieves — "
            "and whichever enforcer is buying — before the next duels are fought on rotten steel."
        ),
        "requires": {"completed": ["citadel_unburied"]},
        "objectives": [
            {"type": "defeat", "target": "blood_bandit", "count": 4, "text": "Take down 4 rack thieves"},
            {"type": "visit_location", "target": "emberfall_citadel", "count": 1, "text": "Inspect the citadel's ring"},
        ],
        "rewards": {"exp": 330, "gold": 170},
    },
    # -- Zen wilds arc ---------------------------------------------------------
    {
        "id": "wilds_silent_bells",
        "title": "The Silent Bells",
        "description": (
            "Someone is stealing the wilds' bell-clappers, shrine by shrine. "
            "Bell Ringer Mo cannot hear which way they went — but you can follow."
        ),
        "requires": {"completed": ["act1_conclusion"]},
        "objectives": [
            {"type": "defeat", "target": "zen_wolf", "count": 3, "text": "Fell 3 clapper-thieving wolves"},
            {"type": "visit_location", "target": "zen_wilds_shrine", "count": 1, "text": "Recover the clappers' hoard"},
        ],
        "rewards": {"exp": 260, "gold": 120, "items": {"soul_nurturing_pill": 3}},
    },
    {
        "id": "wilds_strangling_vines",
        "title": "Strangler Vines in Pilgrim's Robes",
        "description": (
            "The Pale Gardener's strangler vines have learned to dress as "
            "pilgrims. Root them out before they reach the monastery gates."
        ),
        "requires": {"completed": ["wilds_silent_bells"]},
        "objectives": [
            {"type": "defeat", "target": "zen_lizard", "count": 3, "text": "Uproot 3 robed stranglers"},
            {"type": "visit_location", "target": "zenlight_monastery", "count": 1, "text": "Warn the monastery paths"},
        ],
        "rewards": {"exp": 300, "gold": 140, "reputation": 6, "items": {"zen_heart_herb": 3}},
    },
    # -- Undercroft / gate arc -------------------------------------------------
    {
        "id": "circuit_prime_rubbings",
        "title": "Rubbing the Prime Circuit",
        "description": (
            "Scribe Quin needs rubbings of the prime meridian's outer runes — "
            "taken, of course, while the wardens test the taker."
        ),
        "requires": {"completed": ["act1_conclusion"]},
        "objectives": [
            {"type": "visit_location", "target": "rune_temple_undercroft", "count": 1, "text": "Descend to the undercroft"},
            {"type": "defeat", "target": "rune_qilin", "count": 2, "text": "Survive 2 rune-qilin trials"},
        ],
        "rewards": {"exp": 380, "gold": 200, "items": {"dao_palace_star_core": 2}},
    },
    {
        "id": "convict_name_verse",
        "title": "The Convict's Name-Verse",
        "description": (
            "Convict Nine will trade the verse that unlocks his cell for one "
            "thing: a name spoken by someone who isn't a warden. He asks for yours."
        ),
        "requires": {"completed": ["circuit_prime_rubbings"]},
        "objectives": [
            {"type": "defeat", "target": "undercroft_convict_nine_duel", "count": 1, "text": "Answer the convict in the circuit's tongue"},
            {"type": "visit_location", "target": "rune_temple_undercroft", "count": 1, "text": "Speak the name at his cell"},
        ],
        "rewards": {"exp": 420, "gold": 220, "reputation": 5},
    },
    {
        "id": "seven_landings",
        "title": "The Seven Landings",
        "description": (
            "Ascendant Lo duels at every seventh stair of the approach. Match "
            "her through the seven landings and earn the stair's count."
        ),
        "requires": {"completed": ["act1_conclusion"]},
        "objectives": [
            {"type": "spar", "target": "stair_ascendant_lo_duel", "count": 1, "text": "Match Lo at the first landing"},
            {"type": "visit_location", "target": "gate_array_approach", "count": 1, "text": "Climb to the seventh landing"},
        ],
        "rewards": {"exp": 400, "gold": 210, "items": {"celestial_gate_essence": 2}},
    },
    {
        "id": "gate_terms_proof",
        "title": "Proof of Terms",
        "description": (
            "Warden Prime Astrid accepts only proofs. Climb the star-field, "
            "survive the stair's wardens, and present yourself at the gate as a proved climber."
        ),
        "requires": {"completed": ["seven_landings"]},
        "objectives": [
            {"type": "defeat", "target": "gate_warder", "count": 3, "text": "Prove yourself against 3 wardens"},
            {"type": "defeat", "target": "gate_warden_prime_astrid_duel", "count": 1, "text": "Face the Warden Prime herself"},
        ],
        "rewards": {"exp": 520, "gold": 260, "reputation": 10, "items": {"immortal_ascension_elixir": 1}},
    },
    # -- Character quests -------------------------------------------------------
    {
        "id": "poets_lost_verse",
        "title": "The Poet's Lost Verse",
        "description": (
            "Wandering Poet Xu left his masterwork in a gambling slip-game he "
            "lost decades ago. The slip still circulates in the hidden market. Win it back."
        ),
        "requires": {"completed": ["market_stall_wars"]},
        "objectives": [
            {"type": "visit_location", "target": "valleys_hidden_market", "count": 1, "text": "Find the slip's holder"},
            {"type": "defeat", "target": "capital_warlock", "count": 2, "text": "Best 2 slip-holders' enforcers"},
        ],
        "rewards": {"exp": 280, "gold": 150, "reputation": 6},
    },
    {
        "id": "ruin_provenance_run",
        "title": "The Provenance Run",
        "description": (
            "Broker Song has a buyer for relics 'recovered' from the ancient "
            "ruins — and needs a runner unafraid of wardens. The pay insults neither party."
        ),
        "requires": {"completed": ["act1_conclusion"]},
        "objectives": [
            {"type": "visit_location", "target": "ancient_ruins", "count": 1, "text": "Run the ruins' edge lots"},
            {"type": "defeat", "target": "ancient_ruin_sentinel", "count": 1, "text": "Slip past a ruin sentinel"},
        ],
        "rewards": {"exp": 340, "gold": 220, "items": {"dao_enlightenment_pill": 1}},
    },
]

# --------------------------------------------------------------------------
# 5. Named foes for the new combat-capable NPCs.
# --------------------------------------------------------------------------
CHARACTER_ENEMIES = [
    {"id": "cloud_pool_hermit_bai_spar", "character_id": "cloud_pool_hermit_bai", "name": "Hermit Bai of the Cloud Pools",
     "body_realm_id": "body_pulse_condensation", "essence_realm_id": None, "hp": 250, "attack": 33, "defense": 13, "exp_reward": 115,
     "dao_id": "tide_dao", "abilities": [{"type": "heavy", "chance": 0.2, "magnitude": 1.5}],
     "loot_table": [{"item_id": "qi_pill", "chance": 0.4, "count": 1}]},
    {"id": "reef_warden_nimbus_spar", "character_id": "reef_warden_nimbus", "name": "Reef Warden Nimbus",
     "body_realm_id": "tempering_marrow", "essence_realm_id": None, "hp": 300, "attack": 38, "defense": 16, "exp_reward": 140,
     "dao_id": "tide_dao", "abilities": [],
     "loot_table": [{"item_id": "celestial_nectar", "chance": 0.4, "count": 1}, {"item_id": "roaring_tide_sword_intent_manual", "chance": 0.05, "count": 1}]},
    {"id": "atoll_turnkey_owl_duel", "character_id": "atoll_turnkey_owl", "name": "Turnkey Owl",
     "body_realm_id": "tempering_marrow", "essence_realm_id": None, "hp": 290, "attack": 36, "defense": 15, "exp_reward": 135,
     "dao_id": "void_dao", "abilities": [{"type": "stun", "chance": 0.2, "magnitude": 1}],
     "loot_table": [{"item_id": "void_spirit_pill", "chance": 0.4, "count": 1}]},
    {"id": "forge_apprentice_cinder_spar", "character_id": "forge_apprentice_cinder", "name": "Apprentice Cinder",
     "body_realm_id": "eight_gates_hidden_celestial_stems", "essence_realm_id": None, "hp": 340, "attack": 42, "defense": 16, "exp_reward": 160,
     "dao_id": "flame_dao", "abilities": [{"type": "heavy", "chance": 0.2, "magnitude": 1.5}],
     "loot_table": [{"item_id": "phoenix_marrow_pill", "chance": 0.4, "count": 1}]},
    {"id": "stair_ascendant_lo_duel", "character_id": "stair_ascendant_lo", "name": "Ascendant Lo",
     "body_realm_id": "nine_stars_dao_palace", "essence_realm_id": None, "hp": 520, "attack": 58, "defense": 23, "exp_reward": 280,
     "dao_id": "astral_dao", "abilities": [{"type": "heavy", "chance": 0.25, "magnitude": 1.5}],
     "loot_table": [{"item_id": "celestial_gate_essence", "chance": 0.4, "count": 1}]},
    {"id": "undercroft_convict_nine_duel", "character_id": "undercroft_convict_nine", "name": "Convict Nine of the Circuit",
     "body_realm_id": "nine_stars_dao_palace", "essence_realm_id": None, "hp": 560, "attack": 60, "defense": 24, "exp_reward": 300,
     "dao_id": "nether_dao", "abilities": [{"type": "poison", "chance": 0.25, "magnitude": 5}],
     "loot_table": [{"item_id": "dao_palace_star_core", "chance": 0.4, "count": 1}]},
    {"id": "gate_warden_prime_astrid_duel", "character_id": "gate_warden_prime_astrid", "name": "Warden Prime Astrid",
     "body_realm_id": "nine_stars_dao_palace", "essence_realm_id": None, "hp": 700, "attack": 68, "defense": 28, "exp_reward": 380,
     "dao_id": "mountain_dao", "abilities": [{"type": "stun", "chance": 0.25, "magnitude": 1}],
     "loot_table": [{"item_id": "immortal_ascension_elixir", "chance": 0.3, "count": 1}]},
    {"id": "pearl_smuggler_gale_duel", "character_id": "pearl_smuggler_gale", "name": "Smuggler Gale",
     "body_realm_id": "tempering_marrow", "essence_realm_id": None, "hp": 305, "attack": 39, "defense": 15, "exp_reward": 145,
     "dao_id": "space_dao", "abilities": [],
     "loot_table": [{"item_id": "great_return_pill", "chance": 0.4, "count": 1}]},
]

# --------------------------------------------------------------------------
# Writer
# --------------------------------------------------------------------------

# Wave-2 NPC anchors: npc_id -> location_id (merged into locations.json).
NPC_ANCHORS = {
    'reed_cutter_min': 'stream_fisher_wharf',
    'feral_hunter_karu': 'thornwood_hollow',
    'farmhand_olive': 'sky_fortune_outskirts',
    'cloud_pool_hermit_bai': 'seven_profound_low_peaks',
    'market_crier_duo': 'valleys_hidden_market',
    'terrace_shrine_keeper': 'cloud_terrace_village',
    'diver_maru': 'pearl_pavilion',
    'cove_quartermaster_vex': 'tidecrook_cove',
    'reef_warden_nimbus': 'sea_of_mist_expanse',
    'atoll_turnkey_owl': 'coral_prison_atoll',
    'mist_shipwright_halloo': 'tidecrook_cove',
    'forge_apprentice_cinder': 'furnace_pillar_city',
    'ash_priestess_solene': 'emberfall_citadel',
    'zen_bell_ringer_mo': 'zen_wilds_shrine',
    'temple_scribe_quin': 'rune_temple_undercroft',
    'stair_ascendant_lo': 'gate_array_approach',
    'ruin_broker_song': 'ancient_ruins',
    'deepwood_beast_singer': 'deepwood_drift_outpost',
    'furnace_ore_scout_bram': 'furnace_pillar_city',
    'pearl_auctioneer_lo_fan': 'pearl_pavilion',
    'tide_oracle_sable': 'south_sea_port',
    'ember_armsmith_juno': 'emberfall_citadel',
    'zen_gardener_pale': 'zen_wilds_shrine',
    'undercroft_convict_nine': 'rune_temple_undercroft',
    'gate_warden_prime_astrid': 'gate_array_approach',
    'pearl_smuggler_gale': 'tidecrook_cove',
    'valley_wandering_poet_xu': 'valleys_hidden_market',
    'sea_lantern_tender_uma': 'south_sea_port',
}

def main() -> None:
    # Each step is additive-safe (skips already-applied entries) so a partially
    # applied run can simply be re-executed.

    # 1. skills (append new tier 5-6 techniques)
    skills = load("skills.json")
    items = skills if isinstance(skills, list) else skills["skills"]
    existing = {s["id"] for s in items}
    added_skills = 0
    for skill in SKILLS:
        if skill["id"] not in existing:
            items.append(skill)
            added_skills += 1
    save("skills.json", skills)

    # 2. wire the new techniques into their sect halls
    sects = load("sects.json")
    added_hall = 0
    for sect in sects:
        offered = {entry.get("skill_id") for entry in sect.get("techniques", [])}
        for addition in HALL_ADDITIONS.get(sect["id"], []):
            if addition["skill_id"] not in offered:
                sect.setdefault("techniques", []).append(addition)
                added_hall += 1
    save("sects.json", sects)

    # 3. secret realms (append)
    realms = load("secret_realm.json")
    existing = {realm["id"] for realm in realms}
    added_realms = 0
    for realm in REALMS:
        if realm["id"] not in existing:
            realms.append(realm)
            added_realms += 1
    save("secret_realm.json", realms)

    # 4. wave-2 NPC roster (new file; directory loader merges)
    roster_path = DATA / NPC_FILE
    if roster_path.exists():
        roster: list = json.load(roster_path.open("r", encoding="utf-8"))
    else:
        roster = []
        save(NPC_FILE, NPCS)

    # 5. named foes for new combat NPCs
    foes = load("character_enemies/named_foes.json")
    items = foes if isinstance(foes, list) else foes.get("enemies", foes)
    existing = {foe["id"] for foe in items}
    added_foes = 0
    for foe in CHARACTER_ENEMIES:
        if foe["id"] not in existing:
            items.append(foe)
            added_foes += 1
    save("character_enemies/named_foes.json", foes)

    # 5b. anchor wave-2 NPCs into their locations (idempotent)
    locations = load("locations.json")
    by_id = {loc["id"]: loc for loc in locations}
    added_anchors = 0
    for npc_id, loc_id in NPC_ANCHORS.items():
        loc = by_id[loc_id]
        ids = loc.setdefault("npc_ids", [])
        if npc_id not in ids:
            ids.append(npc_id)
            added_anchors += 1
    save("locations.json", locations)

    # 6. quests (append; validate objective types are engine-supported)
    supported = {
        "defeat", "visit_location", "breakthrough", "spar", "debate",
        "join_sect", "dao_awakening", "tournament", "realm_completed",
    }
    quests = load("quests.json")
    existing = {quest["id"] for quest in quests}
    added_quests = 0
    for quest in QUESTS:
        if quest["id"] in existing:
            continue
        for objective in quest["objectives"]:
            kind = objective.get("type")
            assert kind in supported, f"{quest['id']}: unsupported objective type '{kind}'"
        quests.append(quest)
        added_quests += 1
    save("quests.json", quests)

    print(json.dumps({
        "skills_total": len(skills if isinstance(skills, list) else skills["skills"]),
        "new_skills": added_skills,
        "hall_additions": added_hall,
        "realms_total": len(realms), "new_realms": added_realms,
        "npcs_wave2": len(roster), "new_anchors": added_anchors,
        "foes_total": len(items), "new_foes": added_foes,
        "quests_total": len(quests), "new_quests": added_quests,
    }, indent=2))


if __name__ == "__main__":
    main()
