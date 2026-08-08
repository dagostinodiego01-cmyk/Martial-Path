"""Tests that data files load and parse as expected."""
from game.utils.data_loader import load_json


def test_realms_json_loads():
    realms = load_json("realms.json")

    assert isinstance(realms, list)
    assert realms[0]["name"] == "Body Tempering"
    assert realms[0]["stages"] == 9


def test_body_cultivation_realms_load():
    data = load_json("cultivation/body_transformation_realms.json")

    assert data["track_id"] == "body_transformation"
    assert data["realms"][0]["id"] == "mortal"
    assert any(realm["id"] == "strength_training" for realm in data["realms"])
    assert any(realm["id"] == "body_pulse_condensation" for realm in data["realms"])


def test_essence_cultivation_realms_load():
    data = load_json("cultivation/essence_gathering_realms.json")

    assert data["track_id"] == "essence_gathering"
    assert data["realms"][0]["id"] == "houtian"
    assert all(realm["id"] != "essence_pulse_condensation" for realm in data["realms"])
    assert data["realms"][-1]["id"] == "beyond_divinity"
    assert data["realms"][-1]["reachable"] is False


def test_martial_talents_load():
    data = load_json("cultivation/martial_talents.json")

    assert any(talent["id"] == "earth_grade" for talent in data)
    assert any(talent["roll_weight"] > 0 for talent in data)


def test_body_talents_load():
    data = load_json("cultivation/body_talents.json")

    assert any(talent["id"] == "iron_skin_grade" for talent in data)
    assert any(talent["roll_weight"] > 0 for talent in data)


def test_equipment_loads():
    data = load_json("equipment.json")

    assert any(item["id"] == "minor_qi_ring" for item in data)
    assert any(item["id"] == "rusted_flying_sword" for item in data)
