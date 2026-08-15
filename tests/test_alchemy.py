"""Alchemy loop (ROADMAP F.1): gathering herbs and refining them into pills."""
from game.core.constants import Action, EventType
from game.core.game_engine import GameEngine


def test_gather_adds_herb_at_herb_rich_location():
    engine = GameEngine.new_game(seed=1)
    result = engine.process_action({"action": Action.GATHER})

    assert result["event"] == EventType.GATHER_RESULT
    assert result["item_id"] in ("spirit_grass", "frost_herb")
    assert engine.player.inventory.get(result["item_id"], 0) == 1


def test_gather_rejected_where_no_herbs_grow():
    engine = GameEngine.new_game(seed=1)
    engine.player.current_location = "azure_village"  # hub with no herb table

    result = engine.process_action({"action": Action.GATHER})

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "NO_HERBS_HERE"


def test_refine_consumes_inputs_and_produces_output():
    engine = GameEngine.new_game(seed=1)
    engine.player.inventory = {"spirit_grass": 3}

    result = engine.process_action({"action": Action.REFINE, "recipe_id": "brew_healing_pill"})

    assert result["event"] == EventType.REFINE_RESULT
    assert result["item_id"] == "healing_pill"
    assert engine.player.inventory == {"spirit_grass": 1, "healing_pill": 1}


def test_refine_rejected_without_inputs():
    engine = GameEngine.new_game(seed=1)
    engine.player.inventory = {}

    result = engine.process_action({"action": Action.REFINE, "recipe_id": "brew_healing_pill"})

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "INSUFFICIENT_RESOURCES"
    assert "spirit_grass" in result["missing"]


def test_refine_unknown_recipe_rejected():
    engine = GameEngine.new_game(seed=1)

    result = engine.process_action({"action": Action.REFINE, "recipe_id": "no_such_recipe"})

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "UNKNOWN_RECIPE"


def test_recipes_exposed_in_state():
    engine = GameEngine.new_game(seed=1)
    state = engine.get_game_state()

    assert len(state["refining_recipes"]) >= 100
    assert state["gathering_available"] is True  # starts in outer_forest
    # Every recipe is annotated with its realm gate and availability.
    for recipe in state["refining_recipes"]:
        assert recipe.get("minimum_body_realm")
        assert "available" in recipe


def test_refine_gated_by_cultivation_realm():
    engine = GameEngine.new_game(seed=1)
    engine.player.inventory = {"soul_nurturing_pill": 99}  # irrelevant; realm gate comes first

    # soul_nurturing_pill requires nine_stars_dao_palace; a fresh mortal cannot brew it.
    result = engine.process_action({"action": Action.REFINE, "recipe_id": "refine_soul_nurturing_pill"})

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "REALM_TOO_LOW"
    assert result["required"] == "nine_stars_dao_palace"


def test_high_tier_recipe_unavailable_in_menu():
    engine = GameEngine.new_game(seed=1)
    recipes = engine.refine.recipes(engine.player)
    high = next(r for r in recipes if r["id"] == "refine_soul_nurturing_pill")
    low = next(r for r in recipes if r["id"] == "brew_healing_pill")

    assert high["available"] is False
    assert low["available"] is True


def test_demonic_herbs_grow_only_in_demon_continent():
    from game.data.registry import GameDataRegistry

    gathering = GameDataRegistry.load().gathering
    demonic = {"demon_blood_lotus", "nether_ghost_grass", "abyssal_bone_flower", "holy_demon_heartroot"}
    for location_id, table in gathering["locations"].items():
        herb_ids = {entry["item_id"] for entry in table}
        overlap = herb_ids & demonic
        if location_id == "holy_demon_continent":
            assert overlap == demonic
        else:
            assert not overlap, f"{location_id} unexpectedly grows demonic herbs {overlap}"


def test_herbs_carry_rarity():
    from game.data.registry import GameDataRegistry

    items = GameDataRegistry.load().items_by_id()
    for herb_id in ("spirit_grass", "frost_herb", "demon_blood_lotus", "five_element_blossom"):
        assert items[herb_id]["category"] == "herb"
        assert items[herb_id]["rarity"], f"{herb_id} missing rarity"
