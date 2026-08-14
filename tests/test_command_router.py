"""Tests for the command router's text-to-action mapping."""
from game.application.command_router import CommandRouter
from game.core.constants import Action


def test_train_alias_maps_to_body_training():
    router = CommandRouter()
    assert router.route("t")["action"] == Action.TRAIN_BODY
    assert router.route("train body")["action"] == Action.TRAIN_BODY


def test_essence_training_and_breakthrough_commands():
    router = CommandRouter()

    assert router.route("train essence")["action"] == Action.TRAIN_ESSENCE
    assert router.route("breakthrough essence")["action"] == Action.ESSENCE_BREAKTHROUGH
    assert router.route("breakthrough")["action"] == Action.BODY_BREAKTHROUGH


def test_skill_command_extracts_skill_id():
    router = CommandRouter()
    result = router.route("skill iron fist")
    assert result["action"] == Action.USE_SKILL
    assert result["skill_id"] == "iron_fist"


def test_empty_command_is_unknown():
    router = CommandRouter()
    assert router.route("")["action"] == Action.UNKNOWN


def test_rest_and_meditate_aliases():
    router = CommandRouter()
    assert router.route("rest")["action"] == Action.REST
    assert router.route("m")["action"] == Action.MEDITATE


def test_stabilise_aliases_map_to_foundation_action():
    router = CommandRouter()
    assert router.route("stabilise")["action"] == Action.STABILISE_FOUNDATION
    assert router.route("stabilize foundation")["action"] == Action.STABILISE_FOUNDATION


def test_starting_fate_aliases():
    router = CommandRouter()
    assert router.route("roll fate")["action"] == Action.ROLL_STARTING_FATE
    assert router.route("fate")["action"] == Action.ROLL_STARTING_FATE
    assert router.route("accept fate")["action"] == Action.ACCEPT_STARTING_FATE


def test_character_interaction_commands_extract_character_id():
    router = CommandRouter()
    assert router.route("talk zhu yan") == {"action": Action.TALK_TO_CHARACTER, "raw": "talk zhu yan", "character_id": "zhu_yan"}
    assert router.route("spar zhu_yan")["action"] == Action.SPAR_CHARACTER
    assert router.route("duel zhu_yan")["action"] == Action.DUEL_CHARACTER


def test_travel_extracts_location_id():
    router = CommandRouter()
    result = router.route("travel outer forest")
    assert result["action"] == Action.TRAVEL
    assert result["location_id"] == "outer_forest"


def test_shop_and_buy_commands():
    router = CommandRouter()

    assert router.route("shop")["action"] == Action.SHOP
    assert router.route("market azure stream market") == {
        "action": Action.SHOP,
        "raw": "market azure stream market",
        "shop_id": "azure_stream_market",
    }
    assert router.route("buy training sword") == {
        "action": Action.BUY_ITEM,
        "raw": "buy training sword",
        "item_id": "training_sword",
    }
    assert router.route("purchase qi pill 3") == {
        "action": Action.BUY_ITEM,
        "raw": "purchase qi pill 3",
        "item_id": "qi_pill",
        "quantity": 3,
    }


def test_sell_command():
    router = CommandRouter()

    assert router.route("sell training sword") == {
        "action": Action.SELL_ITEM,
        "raw": "sell training sword",
        "item_id": "training_sword",
    }
    assert router.route("sell qi pill 3") == {
        "action": Action.SELL_ITEM,
        "raw": "sell qi pill 3",
        "item_id": "qi_pill",
        "quantity": 3,
    }
