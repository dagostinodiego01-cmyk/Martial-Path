"""Integrity tests for the named-character combat entries (data/character_enemies/)."""
from game.utils.data_loader import load_collection, load_json


def test_character_enemies_load_with_unique_ids():
    enemies = load_collection("character_enemies")
    ids = [enemy["id"] for enemy in enemies]
    assert len(ids) > 0
    assert len(ids) == len(set(ids))


def test_every_referenced_enemy_id_has_an_entry():
    characters = load_collection("characters")
    entry_ids = {enemy["id"] for enemy in load_collection("character_enemies")}
    referenced = {
        character["gameplay_hooks"]["enemy_id"]
        for character in characters
        if character["gameplay_hooks"]["enemy_id"]
    }
    missing = referenced - entry_ids
    assert not missing, f"characters reference enemy ids with no entry: {sorted(missing)}"


def test_character_enemy_character_ids_exist():
    character_ids = {character["id"] for character in load_collection("characters")}
    for enemy in load_collection("character_enemies"):
        assert enemy["character_id"] in character_ids


def test_character_enemy_loot_references_existing_items():
    items = {item["id"] for item in load_json("items.json")}
    for enemy in load_collection("character_enemies"):
        for drop in enemy.get("loot_table", []):
            assert drop["item_id"] in items


def test_character_enemies_have_required_combat_stats():
    for enemy in load_collection("character_enemies"):
        assert "level" not in enemy, f"{enemy.get('id')} should use realms instead of level"
        for key in ("id", "name", "body_realm_id", "hp", "attack", "defense", "exp_reward"):
            assert key in enemy, f"{enemy.get('id')} is missing {key}"


def test_character_enemy_realms_reference_cultivation_data():
    body_ids = {realm["id"] for realm in load_json("cultivation/body_transformation_realms.json")["realms"]}
    essence_ids = {realm["id"] for realm in load_json("cultivation/essence_gathering_realms.json")["realms"]}
    for enemy in load_collection("character_enemies"):
        assert enemy["body_realm_id"] in body_ids
        if enemy.get("essence_realm_id") is not None:
            assert enemy["essence_realm_id"] in essence_ids


def test_named_foes_are_not_in_the_random_pool():
    random_ids = {enemy["id"] for enemy in load_collection("enemies")}
    named_ids = {enemy["id"] for enemy in load_collection("character_enemies")}
    assert random_ids.isdisjoint(named_ids)
