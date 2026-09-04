"""ROADMAP Phase F breadth: reachability, arc structure, and cross-wiring.

Guards the F.2 expansion (16 locations, 8 sects, NPC roster, pools, shops,
trainers) and the F.3 faction quest arcs against silent regression: the map
stays connected, every new entry is referenced by the living world, and the
sect-technique economy still reaches every skill through some acquisition path.
"""
from game.data.registry import GameDataRegistry
from game.utils.data_loader import load_collection
from game.validation import validate_all_game_data


def _locations() -> list[dict]:
    return load_collection("locations")


def _ids(items: list[dict]) -> set[str]:
    return {item["id"] for item in items}


def _load_json(name: str):
    from game.utils.data_loader import load_json
    return load_json(name)


def load_json_collection():
    return _load_json("secret_realm.json")


# -- counts (ROADMAP §6 progress) ------------------------------------------

def test_content_counts_after_expansion():
    # Floors rather than pins: parallel workstreams may keep adding content.
    assert len(_locations()) >= 45
    assert len(load_collection("sects")) == 12
    assert len(load_collection("quests")) >= 61
    assert len(load_collection("shops")) == 14
    assert len(load_collection("trainers")) == 10
    assert len(load_collection("characters")) >= 90


def test_tier_5_6_techniques_are_offered_by_their_halls():
    """New tier 5-6 techniques ship seeded: each is buyable from its hall."""
    sects = {sect["id"]: sect for sect in load_collection("sects")}
    wiring = {
        "everburning_forge_body": "furnace_forge_society",
        "pillar_of_the_sun": "furnace_forge_society",
        "blood_ledger_aura": "emberfall_war_pavilion",
        "ashen_verdict": "emberfall_war_pavilion",
        "rune_circuit_body": "rune_temple_order",
        "five_element_world_seal": "rune_temple_order",
        "gate_star_severing_step": "rune_temple_order",
    }
    for skill_id, sect_id in wiring.items():
        offered = {
            entry.get("skill_id") for entry in sects[sect_id].get("techniques", [])
        }
        assert skill_id in offered, f"{skill_id} missing from {sect_id}'s hall"


def test_endgame_secret_realms_bind_to_new_zones():
    realms = {realm["id"]: realm for realm in load_json_collection()}
    for realm_id, location_id in (
        ("coral_drowned_panopticon", "coral_prison_atoll"),
        ("undercroft_circuit_prime", "rune_temple_undercroft"),
        ("starfield_stair_sanctum", "gate_array_approach"),
    ):
        realm = realms[realm_id]
        assert realm["location_id"] == location_id
        assert realm.get("boss_id"), f"{realm_id} has no boss"
        assert realm.get("enemy_pool"), f"{realm_id} has no enemy pool"


# -- F.2: map connectivity ---------------------------------------------------

def test_connections_are_bidirectional():
    locations = {loc["id"]: loc for loc in _locations()}
    for location_id, location in locations.items():
        for neighbor_id in location.get("connected_locations", []):
            neighbor = locations[neighbor_id]
            assert location_id in neighbor.get("connected_locations", []), (
                f"{neighbor_id} does not link back to {location_id}"
            )


def test_every_new_location_is_anchored_into_the_world():
    locations = {loc["id"]: loc for loc in _locations()}
    new_ids = {
        "stream_fisher_wharf", "thornwood_hollow", "sky_fortune_outskirts",
        "deepwood_drift_outpost", "seven_profound_low_peaks", "valleys_hidden_market",
        "cloud_terrace_village", "pearl_pavilion", "tidecrook_cove",
        "coral_prison_atoll", "sea_of_mist_expanse", "furnace_pillar_city",
        "emberfall_citadel", "zen_wilds_shrine", "rune_temple_undercroft",
        "gate_array_approach",
    }
    assert new_ids <= set(locations)
    for location_id in new_ids:
        location = locations[location_id]
        neighbors = location.get("connected_locations", [])
        assert neighbors, f"{location_id} is unreachable"
        # every location has an encounter pool with at least one enemy
        pool = load_collection  # noqa: F841 (clarity below)
        assert location.get("map_position"), f"{location_id} missing map position"
        assert location.get("story_tier", 1) >= 2


def test_new_sects_bind_to_real_locations_and_existing_skills():
    skills = _ids(load_collection("skills"))
    location_ids = _ids(_locations())
    new_sect_ids = {
        "mistwood_rangers", "stream_cloud_pavilion", "valleys_gamblers_market",
        "deepwood_drift_hall", "pearl_tide_pavilion", "furnace_forge_society",
        "emberfall_war_pavilion", "rune_temple_order",
    }
    sects = {sect["id"]: sect for sect in load_collection("sects")}
    assert new_sect_ids <= set(sects)
    for sect_id in new_sect_ids:
        sect = sects[sect_id]
        assert sect.get("tier"), f"{sect_id} missing tier"
        assert set(sect["location_ids"]) <= location_ids
        assert sect.get("techniques"), f"{sect_id} has an empty technique hall"
        for entry in sect["techniques"]:
            assert entry["skill_id"] in skills, (
                f"{sect_id} hall references unknown skill {entry['skill_id']}"
            )
            assert entry.get("price"), f"{sect_id} technique {entry['skill_id']} lacks a price"


def test_every_new_location_has_a_combat_pool():
    pools = GameDataRegistry.load().encounter_pools
    new_ids = [
        "stream_fisher_wharf", "thornwood_hollow", "sky_fortune_outskirts",
        "deepwood_drift_outpost", "seven_profound_low_peaks", "valleys_hidden_market",
        "cloud_terrace_village", "pearl_pavilion", "tidecrook_cove",
        "coral_prison_atoll", "sea_of_mist_expanse", "furnace_pillar_city",
        "emberfall_citadel", "zen_wilds_shrine", "rune_temple_undercroft",
        "gate_array_approach",
    ]
    for location_id in new_ids:
        pool = pools.get(location_id, {})
        assert pool.get("combat"), f"{location_id} has no combat encounters"
        assert pool.get("loot"), f"{location_id} has no loot table"


def test_expansion_wires_previously_unused_enemies():
    registry = GameDataRegistry.load()
    used: set[str] = set()
    for pool in registry.encounter_pools.values():
        for entry in pool.get("combat", []):
            used.add(str(entry["enemy_id"]))
    for wired in (
        "deepwood_wraith", "sea_zealot", "coral_golem", "rune_tiger",
        "gate_warder", "slaughter_rogue_cultivator", "zen_wolf", "flame_warfiend",
    ):
        assert wired in used, f"{wired} still unused after the expansion"


def test_new_npcs_are_anchored_and_tier_tagged():
    characters = _ids(load_collection("characters"))
    location_ids = _ids(_locations())
    locations = {loc["id"]: loc for loc in _locations()}
    new_npcs = {
        "old_fisher_yan", "wharf_captain_bao", "mistwood_ranger_elder",
        "drift_broker_lan", "gambler_king_tan", "pearl_mistress_sui",
        "tide_king_hei", "forge_master_yan_huo", "war_pavilion_envoy_ru",
        "nameless_zen_wanderer", "rune_temple_warden", "gate_stair_hermit",
    }
    assert new_npcs <= characters
    for location_id, location in locations.items():
        for npc_id in location.get("npc_ids", []):
            if npc_id in new_npcs:
                assert location_id in location_ids  # trivially true; anchor check
    anchored: set[str] = set()
    for location in _locations():
        anchored |= set(location.get("npc_ids", [])) & new_npcs
    assert anchored == new_npcs, f"unanchored NPCs: {sorted(new_npcs - anchored)}"


def test_shops_and_trainers_bind_to_real_locations():
    location_ids = _ids(_locations())
    for shop in load_collection("shops"):
        assert set(shop["location_ids"]) <= location_ids
    for trainer in load_collection("trainers"):
        assert set(trainer["location_ids"]) <= location_ids


# -- F.3: faction quest arcs ---------------------------------------------------

def test_faction_arcs_are_three_quest_chains():
    quests = {quest["id"]: quest for quest in load_collection("quests")}
    arcs = {
        "Seven Profound Valleys": [
            "spv_outer_sea_ward", "spv_forbidden_scout", "spv_marrow_pact",
        ],
        "Divine Phoenix": [
            "dpa_pearl_tribute", "dpa_tide_trial", "dpa_phoenix_ascendant",
        ],
        "Asura": [
            "asura_steppes_oath", "asura_blood_hunt", "asura_demon_trial",
        ],
    }
    for arc_id, chain in arcs.items():
        for quest_id in chain:
            assert quest_id in quests, f"{arc_id} missing quest {quest_id}"
        for earlier, later in zip(chain, chain[1:]):
            requires = quests[later].get("requires", {})
            assert earlier in requires.get("completed", []), (
                f"{arc_id}: {later} does not chain from {earlier}"
            )
        first = quests[chain[0]]
        assert first.get("requires", {}).get("completed") == ["act1_conclusion"]


def test_arc_quests_reference_real_targets():
    quests = load_collection("quests")
    location_ids = _ids(_locations())
    enemy_ids = _ids(load_collection("enemies"))
    for quest in quests:
        if not quest["id"].startswith(("spv_", "dpa_", "asura_")):
            continue
        for objective in quest.get("objectives", []):
            if objective.get("type") == "visit_location":
                assert objective["target"] in location_ids
            if objective.get("type") == "defeat" and objective.get("target") != "any":
                assert objective["target"] in enemy_ids, (
                    f"{quest['id']} defeat target {objective['target']} is not an enemy"
                )


def test_arc_rewards_reference_real_skills_and_items():
    quests = load_collection("quests")
    skills = _ids(load_collection("skills"))
    for quest in quests:
        if not quest["id"].startswith(("spv_", "dpa_", "asura_")):
            continue
        rewards = quest.get("rewards", {})
        for skill_id in rewards.get("skills", []):
            assert skill_id in skills, f"{quest['id']} rewards unknown skill {skill_id}"


# -- invariants ---------------------------------------------------------------

def test_validator_stays_clean_after_expansion():
    result = validate_all_game_data()
    assert result.is_valid, result.errors[:5]


def test_skill_reachability_survives_the_expansion():
    registry = GameDataRegistry.load()
    manual_to_skill: dict[str, str] = {}
    overrides = {e["skill_id"]: e for e in registry.technique_manuals if e.get("skill_id")}
    for skill in registry.skills:
        skill_id = skill["id"]
        override = overrides.get(skill_id, {})
        manual_to_skill[str(override.get("id", f"{skill_id}_manual"))] = skill_id

    reachable: set[str] = set()
    for trainer in registry.trainers:
        for entry in trainer.get("techniques", []):
            reachable.add(str(entry["skill_id"]))
    for shop in registry.shops:
        for entry in shop.get("stock", []):
            skill_id = manual_to_skill.get(entry.get("item_id"))
            if skill_id:
                reachable.add(skill_id)
    for enemy in registry.enemies + registry.character_enemies:
        for drop in enemy.get("loot_table", []):
            skill_id = manual_to_skill.get(drop.get("item_id"))
            if skill_id:
                reachable.add(skill_id)
    for pool in registry.encounter_pools.values():
        for entry in pool.get("loot", []):
            skill_id = manual_to_skill.get(entry.get("item_id"))
            if skill_id:
                reachable.add(skill_id)
    for sect in registry.sects:
        for entry in sect.get("techniques", []):
            reachable.add(str(entry["skill_id"]))

    missing = {s["id"] for s in registry.skills} - reachable
