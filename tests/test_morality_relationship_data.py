"""Validation for morality/relationship config, cross-checked against the NPC roster.

These guarantee the data-driven bands/tiers stay contiguous and that their ids
exactly match the reaction/behaviour keys used by every character, so a future
CharacterSystem can look up the correct response text by band/tier id.
"""
from game.utils.data_loader import load_collection, load_json


def test_morality_bands_cover_full_range_without_gaps():
    config = load_json("morality.json")
    bands = sorted(config["bands"], key=lambda band: band["min"])
    assert bands[0]["min"] == config["min"]
    assert bands[-1]["max"] == config["max"]
    for previous, following in zip(bands, bands[1:]):
        assert following["min"] == previous["max"] + 1


def test_morality_band_ids_match_character_reaction_keys():
    band_ids = {band["id"] for band in load_json("morality.json")["bands"]}
    reaction_keys = set()
    for character in load_collection("characters"):
        reaction_keys |= set(character["personality"]["morality_reaction"].keys())
    assert reaction_keys == band_ids


def test_relationship_tiers_cover_full_range_without_gaps():
    config = load_json("relationships.json")
    tiers = sorted(config["tiers"], key=lambda tier: tier["min"])
    score = config["variables"]["relationship_score"]
    assert tiers[0]["min"] == score["min"]
    assert tiers[-1]["max"] == score["max"]
    for previous, following in zip(tiers, tiers[1:]):
        assert following["min"] == previous["max"] + 1


def test_relationship_tier_ids_match_character_behavior_keys():
    tier_ids = {tier["id"] for tier in load_json("relationships.json")["tiers"]}
    behavior_keys = set()
    for character in load_collection("characters"):
        behavior_keys |= set(character["personality"]["relationship_behavior"].keys())
    assert behavior_keys == tier_ids
