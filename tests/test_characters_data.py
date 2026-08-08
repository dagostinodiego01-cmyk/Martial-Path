"""Validation tests for the data-driven NPC roster (data/characters/)."""
from game.utils.data_loader import load_collection

REGION = "Sky Spill World"
RELATIONSHIP_KEYS = {"hostile", "neutral", "friendly", "trusted"}
MORALITY_KEYS = {"righteous", "neutral", "demonic"}
HOOK_KEYS = {
    "can_talk",
    "can_spar",
    "can_duel",
    "can_train_player",
    "can_give_quest",
    "can_join_player",
    "enemy_id",
    "quest_ids",
    "teaches_skills",
    "relationship_rewards",
}


def test_characters_json_has_50_entries():
    characters = load_collection("characters")
    assert len(characters) == 50


def test_character_ids_are_unique():
    characters = load_collection("characters")
    ids = [character["id"] for character in characters]
    assert len(ids) == len(set(ids))


def test_all_characters_share_starting_region():
    characters = load_collection("characters")
    for character in characters:
        assert character["region"] == REGION
        assert character["starting_world"] is True


def test_all_characters_have_personality_schema():
    characters = load_collection("characters")
    for character in characters:
        personality = character["personality"]
        assert len(personality["traits"]) == 5
        assert personality["speech_style"]
        assert personality["values"]
        assert set(personality["relationship_behavior"].keys()) == RELATIONSHIP_KEYS
        assert set(personality["morality_reaction"].keys()) == MORALITY_KEYS


def test_all_characters_have_gameplay_hooks():
    characters = load_collection("characters")
    for character in characters:
        hooks = character["gameplay_hooks"]
        assert HOOK_KEYS <= set(hooks.keys())
        assert isinstance(hooks["enemy_id"], str)


def test_combat_hooks_have_enemy_id_and_peaceful_ones_do_not():
    characters = load_collection("characters")
    for character in characters:
        hooks = character["gameplay_hooks"]
        if hooks["enemy_id"]:
            assert hooks["can_duel"] or hooks["can_spar"]
