"""Data-file integrity checks: unique IDs and valid cross-references."""
from game.systems.cultivation_system import CultivationSystem
from game.utils.data_loader import load_collection, load_json
from game.utils.rng import RNG


def _cultivation_system():
    return CultivationSystem(
        load_json("cultivation/body_transformation_realms.json"),
        load_json("cultivation/essence_gathering_realms.json"),
        load_json("cultivation/cultivation_config.json"),
        RNG(seed=1),
    )


def test_all_enemy_ids_are_unique():
    enemies = load_collection("enemies")
    ids = [enemy["id"] for enemy in enemies]
    assert len(ids) == len(set(ids))


def test_random_enemies_use_realms_not_levels():
    body_ids = {realm["id"] for realm in load_json("cultivation/body_transformation_realms.json")["realms"]}
    essence_ids = {realm["id"] for realm in load_json("cultivation/essence_gathering_realms.json")["realms"]}
    enemies = load_collection("enemies")
    assert len(enemies) >= 28
    for enemy in enemies:
        assert "level" not in enemy
        assert enemy["body_realm_id"] in body_ids
        if enemy.get("essence_realm_id") is not None:
            assert enemy["essence_realm_id"] in essence_ids


def test_all_item_ids_are_unique():
    items = load_json("items.json")
    ids = [item["id"] for item in items]
    assert len(ids) == len(set(ids))


def test_all_skill_ids_are_unique():
    skills = load_json("skills.json")
    ids = [skill["id"] for skill in skills]
    assert len(ids) == len(set(ids))


def test_enemy_loot_references_existing_items():
    items = {item["id"] for item in load_json("items.json")} | {item["id"] for item in load_json("equipment.json")}
    enemies = load_collection("enemies")

    for enemy in enemies:
        for drop in enemy.get("loot_table", []):
            assert drop["item_id"] in items


def test_event_loot_pool_references_existing_items():
    items = {item["id"] for item in load_json("items.json")}
    events = load_json("events.json")

    for loot in events.get("loot_pool", []):
        assert loot["item_id"] in items


def test_cultivation_data_is_valid():
    validation = _cultivation_system().validate_cultivation_data()

    assert validation["valid"] is True


def test_cultivation_required_resources_exist_as_items():
    items = {item["id"] for item in load_json("items.json")}
    body = load_json("cultivation/body_transformation_realms.json")

    for realm in body["realms"]:
        for resource_id in realm.get("breakthrough_requirements", {}).get("resources", []):
            assert resource_id in items


def test_cultivation_realm_orders_are_unique_within_tracks():
    for filename in [
        "cultivation/body_transformation_realms.json",
        "cultivation/essence_gathering_realms.json",
    ]:
        data = load_json(filename)
        orders = [realm["order"] for realm in data["realms"]]
        assert len(orders) == len(set(orders))
