"""Smoke tests for the game engine's UI-agnostic contract."""
from game.core.constants import Action, EventType
from game.core.game_engine import MODE_COMBAT, GameEngine


def _accept_fate(engine: GameEngine):
    result = engine.process_action({"action": Action.ACCEPT_STARTING_FATE})
    assert result["event"] == EventType.ERROR
    assert result["reason"] == "FATE_ALREADY_ACCEPTED"
    return result


def test_new_game_returns_initial_state():
    engine = GameEngine.new_game(seed=1)
    state = engine.get_game_state()

    assert state["running"] is True
    assert state["player"]["realm"] == "Mortal"
    assert state["player"]["cultivation_state"]["body_transformation"]["realm_id"] == "mortal"
    assert state["player"]["cultivation_state"]["essence_gathering"]["realm_id"] == "houtian"
    assert state["player"]["essence_unlocked"] is False
    assert state["awaiting_fate_acceptance"] is False
    assert state["pending_fate"] is None
    assert state["player"]["martial_talent_id"]
    assert state["player"]["body_talent_id"]


def test_starting_fate_roll_and_accept_flow():
    engine = GameEngine.new_game(seed=1)
    rolled = engine.process_action({"action": Action.ROLL_STARTING_FATE})
    accepted = engine.process_action({"action": Action.ACCEPT_STARTING_FATE})

    assert rolled["event"] == EventType.ERROR
    assert rolled["reason"] == "FATE_ALREADY_ACCEPTED"
    assert accepted["event"] == EventType.ERROR
    assert accepted["reason"] == "FATE_ALREADY_ACCEPTED"
    assert engine.get_game_state()["awaiting_fate_acceptance"] is False


def test_engine_unlocks_essence_at_completed_body_pulse_threshold():
    engine = GameEngine.new_game(seed=1)
    body = engine.player.cultivation_state.body
    body.realm_id = "body_pulse_condensation"
    body.progress = 960.0
    body.foundation = 45.0

    state = engine.get_game_state()
    result = engine.process_action({"action": Action.TRAIN_ESSENCE})

    assert state["player"]["essence_unlocked"] is True
    assert result["event"] == EventType.TRAIN_RESULT
    assert result["track_id"] == "essence_gathering"


def test_status_action_returns_status_event():
    engine = GameEngine.new_game(seed=1)
    result = engine.process_action({"action": Action.STATUS})

    assert result["event"] == EventType.STATUS
    assert "player" in result


def test_new_game_includes_extended_attributes():
    engine = GameEngine.new_game(seed=1)
    player = engine.get_game_state()["player"]

    for key in (
        "path",
        "foundation_quality",
        "body_strength",
        "soul_strength",
        "comprehension",
        "reputation",
        "morality",
        "current_location",
    ):
        assert key in player
    assert player["current_location"] == "outer_forest"
    assert player["path"] == "Unassigned"


def test_state_includes_location_and_quests():
    engine = GameEngine.new_game(seed=1)
    state = engine.get_game_state()

    assert state["location"]["id"] == "outer_forest"
    assert state["shops"] == []
    assert isinstance(state["quests"], list)
    assert len(state["quests"]) >= 1


def test_engine_lists_and_buys_from_current_location_shop():
    engine = GameEngine.new_game(seed=1)
    engine.player.gold = 30
    engine.process_action({"action": Action.TRAVEL, "location_id": "azure_village"})

    shop = engine.process_action({"action": Action.SHOP})
    bought = engine.process_action({"action": Action.BUY_ITEM, "item_id": "training_sword"})

    assert shop["event"] == EventType.SHOP
    assert shop["shop"]["id"] == "azure_stream_market"
    assert bought["event"] == EventType.ITEM_PURCHASED
    assert engine.player.gold == 5
    assert engine.player.inventory["training_sword"] == 1


def test_engine_rejects_purchase_without_shop_at_location():
    engine = GameEngine.new_game(seed=1)
    engine.player.gold = 30

    result = engine.process_action({"action": Action.BUY_ITEM, "item_id": "training_sword"})

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "NO_SHOP_AVAILABLE"


def test_engine_sells_owned_item_for_gold():
    engine = GameEngine.new_game(seed=1)
    engine.player.gold = 0

    result = engine.process_action({"action": Action.SELL_ITEM, "item_id": "healing_pill", "quantity": 1})

    assert result["event"] == EventType.ITEM_SOLD
    assert result["item_id"] == "healing_pill"
    assert engine.player.inventory["healing_pill"] == 1
    assert engine.player.gold == 5


def test_buy_then_sell_round_trip_recovers_partial_gold():
    engine = GameEngine.new_game(seed=1)
    engine.player.gold = 30
    engine.process_action({"action": Action.TRAVEL, "location_id": "azure_village"})

    bought = engine.process_action({"action": Action.BUY_ITEM, "item_id": "training_sword"})
    assert bought["event"] == EventType.ITEM_PURCHASED
    assert engine.player.gold == 5  # 30 - 25

    sold = engine.process_action({"action": Action.SELL_ITEM, "item_id": "training_sword"})

    assert sold["event"] == EventType.ITEM_SOLD
    assert "training_sword" not in engine.player.inventory
    assert engine.player.gold == 17  # 5 + floor(25 * 0.5)


def test_rest_recovers_hp_and_qi():
    engine = GameEngine.new_game(seed=1)
    engine.player.hp = 10
    engine.player.qi = 5
    before_day = engine.player.current_day

    result = engine.process_action({"action": Action.REST})

    assert result["event"] == EventType.REST_RESULT
    assert engine.player.hp > 10
    assert engine.player.qi > 5
    assert engine.player.current_day == before_day + 1


def test_stabilise_foundation_action_updates_state_and_advances_day():
    engine = GameEngine.new_game(seed=1)
    body = engine.player.cultivation_state.body
    body.cultivation_strain = 30.0
    body.foundation_stability = 80.0

    result = engine.process_action({"action": Action.STABILISE_FOUNDATION})
    state = engine.get_game_state()

    assert result["event"] == EventType.STABILISE_RESULT
    assert result["current_strain"] == 12.0
    assert result["foundation_stability"] == 84.0
    assert result["current_day"] == 2
    assert state["player"]["current_day"] == 2
    assert state["player"]["cultivation_state"]["body_transformation"]["required_progress"] == 100.0
    assert state["player"]["cultivation_state"]["essence_gathering"]["required_progress"] == 100.0


def test_meditate_returns_meditate_result():
    engine = GameEngine.new_game(seed=1)
    result = engine.process_action({"action": Action.MEDITATE})
    assert result["event"] == EventType.MEDITATE_RESULT


def test_travel_moves_to_connected_location():
    engine = GameEngine.new_game(seed=1)
    result = engine.process_action({"action": Action.TRAVEL, "location_id": "azure_village"})

    assert result["event"] == EventType.TRAVEL_RESULT
    assert engine.player.current_location == "azure_village"


def test_travel_rejects_unconnected_location():
    engine = GameEngine.new_game(seed=1)
    result = engine.process_action({"action": Action.TRAVEL, "location_id": "ruined_shrine"})

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "NO_ROUTE"
    assert engine.player.current_location == "outer_forest"


def test_enemy_view_includes_threat_and_reward_preview():
    engine = GameEngine.new_game(seed=1)
    view = engine._enemy_view(engine._spawn_enemy("iron_wolf"))

    assert "threat" in view
    assert "reward_preview" in view
    assert "exp" in view["reward_preview"]


def test_engine_equips_and_unequips_owned_item_without_base_stat_mutation():
    engine = GameEngine.new_game(seed=1)
    engine.player.inventory["training_sword"] = 1
    before_attack = engine.player.attack

    equipped = engine.process_action({"action": Action.EQUIP_ITEM, "item_id": "training_sword", "slot": "weapon"})
    state = engine.get_game_state()
    unequipped = engine.process_action({"action": Action.UNEQUIP_ITEM, "slot": "weapon"})

    assert equipped["event"] == EventType.EQUIP_ITEM_RESULT
    assert engine.player.attack == before_attack
    assert state["player"]["effective_stats"]["attack"] == before_attack + 2
    assert state["player"]["equipment"]["weapon"] == "training_sword"
    assert state["player"]["equipment_details"]["weapon"]["display_name"] == "Training Sword"
    assert unequipped["event"] == EventType.UNEQUIP_ITEM_RESULT
    assert engine.player.equipment["weapon"] is None


def test_engine_equipment_is_listed_as_inventory_item():
    engine = GameEngine.new_game(seed=1)
    engine.player.inventory["minor_qi_ring"] = 1

    items = engine.get_game_state()["inventory_items"]

    ring = next(item for item in items if item["item_id"] == "minor_qi_ring")
    assert ring["type"] == "equipment"
    assert ring["category"] == "ring"
    assert ring["valid_slots"] == ["ring_1", "ring_2"]


def test_engine_equipment_cultivation_modifier_affects_training(monkeypatch):
    engine = GameEngine.new_game(seed=1)
    monkeypatch.setattr(engine.cultivation._rng, "randint", lambda _low, _high: 0)
    engine.player.inventory["iron_body_ring"] = 1
    baseline = engine.process_action({"action": Action.TRAIN_BODY})
    engine.player.cultivation_state.body.progress = 0.0
    engine.player.cultivation_state.body.daily_cultivation_count = 0
    engine.player.cultivation_state.body.cultivation_strain = 0.0

    engine.process_action({"action": Action.EQUIP_ITEM, "item_id": "iron_body_ring", "slot": "ring_1"})
    boosted = engine.process_action({"action": Action.TRAIN_BODY})

    assert boosted["progress_gained"] > baseline["progress_gained"]


def test_explore_surfaces_named_character_options_at_location():
    engine = GameEngine.new_game(seed=1)
    engine.player.current_location = "lin_academy"
    engine._character_encounter_chance = 1.0  # force the encounter for a deterministic assert

    result = engine.process_action({"action": Action.EXPLORE})

    assert result["event"] == EventType.CHARACTER_ENCOUNTER
    zhu = next(character for character in result["characters"] if character["id"] == "zhu_yan")
    # Talk and Spar are available immediately; Duel is gated behind a friendly
    # relationship (see test_relationship_tier_gates_duel).
    assert {option["label"] for option in zhu["options"]} >= {"Talk", "Spar"}
    assert "Duel" not in {option["label"] for option in zhu["options"]}


def test_explore_still_rolls_events_when_named_characters_present():
    # Regression: a location with named characters must not force every explore
    # into a CHARACTER_ENCOUNTER; normal random events still occur.
    engine = GameEngine.new_game(seed=1)
    engine.player.current_location = "lin_academy"
    engine._character_encounter_chance = 0.0  # never surface characters this explore

    result = engine.process_action({"action": Action.EXPLORE})

    assert result["event"] != EventType.CHARACTER_ENCOUNTER


def test_use_technique_manual_learns_skill_and_consumes_it():
    engine = GameEngine.new_game(seed=1)
    assert "great_sun_domain" not in engine.player.skills
    engine.player.inventory["great_sun_domain_manual"] = 1

    result = engine.process_action({"action": Action.USE_ITEM, "item_id": "great_sun_domain_manual"})

    assert result["event"] == EventType.SKILL_LEARNED
    assert "great_sun_domain" in engine.player.skills
    assert engine.player.inventory.get("great_sun_domain_manual", 0) == 0


def test_technique_manual_cannot_be_used_in_combat():
    engine = GameEngine.new_game(seed=1)
    engine.player.inventory["great_sun_domain_manual"] = 1
    engine._mode = "combat"
    engine._current_enemy = engine._spawn_enemy(next(iter(engine._enemy_templates)))

    result = engine.process_action({"action": Action.USE_ITEM, "item_id": "great_sun_domain_manual"})

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "CANNOT_STUDY_IN_COMBAT"
    assert engine.player.inventory.get("great_sun_domain_manual", 0) == 1
    assert "great_sun_domain" not in engine.player.skills


def test_learn_skill_from_trainer_spends_gold():
    engine = GameEngine.new_game(seed=1)
    engine.player.current_location = "outer_forest"
    engine.player.gold = 100

    state = engine.get_game_state()
    assert any(t["id"] == "wandering_sword_master" for t in state["trainers"])

    result = engine.process_action({"action": Action.LEARN_SKILL, "skill_id": "spirit_palm"})

    assert result["event"] == EventType.SKILL_LEARNED
    assert "spirit_palm" in engine.player.skills
    assert engine.player.gold == 20


def test_talk_to_character_returns_dialogue_context():
    engine = GameEngine.new_game(seed=1)
    engine.player.current_location = "lin_academy"

    result = engine.process_action({"action": Action.TALK_TO_CHARACTER, "character_id": "zhu_yan"})

    assert result["event"] == EventType.CHARACTER_INTERACTION
    assert result["character_id"] == "zhu_yan"
    assert "privileged academy student" in result["player_message"]


def test_spar_character_starts_named_combat():
    engine = GameEngine.new_game(seed=1)
    engine.player.current_location = "lin_academy"

    result = engine.process_action({"action": Action.SPAR_CHARACTER, "character_id": "zhu_yan"})

    assert result["event"] == EventType.COMBAT
    assert result["interaction"] == "spar"
    assert result["enemy"]["name"] == "Zhu Yan"
    assert result["enemy"]["realm"] == "Strength Training"


def test_duel_character_respects_unlock_gate():
    engine = GameEngine.new_game(seed=1)
    engine.player.current_location = "seven_profound_valleys_gate"

    result = engine.process_action({"action": Action.DUEL_CHARACTER, "character_id": "jiang_lanjian"})

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "LOCKED"


def test_join_sect_assigns_path():
    engine = GameEngine.new_game(seed=1)
    engine.player.current_location = "lin_academy"

    result = engine.process_action({"action": Action.JOIN_SECT, "sect_id": "lin_academy"})

    assert result["event"] == EventType.SECT_JOINED
    assert result["path"] == "Lin Academy"
    assert engine.player.path == "Lin Academy"


def test_spar_ends_without_defeat_penalty():
    engine = GameEngine.new_game(seed=1)
    engine.player.current_location = "lin_academy"
    engine.player.cultivation_state.body.progress = 400.0
    engine.player.progress = 400.0
    engine.process_action({"action": Action.SPAR_CHARACTER, "character_id": "zhu_yan"})

    engine.player.hp = 1
    engine._current_enemy.attack = 100
    result = engine.process_action({"action": Action.ATTACK})

    assert result["event"] == EventType.COMBAT_END
    assert result["outcome"] == "SPAR_LOST"
    assert result["spar"] is True
    assert "penalty" not in result
    assert engine.player.cultivation_state.body.progress == 400.0


def test_defeat_penalty_is_partial_and_data_driven():
    engine = GameEngine.new_game(seed=1)
    engine.player.cultivation_state.body.progress = 400.0
    engine.player.progress = 400.0
    engine.player.hp = 1

    # Force a losing fight against a deadly exploration enemy.
    engine._current_enemy = engine._spawn_enemy(next(iter(engine._enemy_templates)))
    engine._current_enemy.attack = 100
    engine._mode = MODE_COMBAT

    result = engine.process_action({"action": Action.ATTACK})

    assert result["event"] == EventType.COMBAT_END
    assert result["outcome"] == "DEFEAT"
    assert result["penalty"]["progress_lost"] == 100.0  # 25% of 400
    assert engine.player.cultivation_state.body.progress == 300.0
    assert engine.player.hp == 50  # half of max_hp


def test_dialogue_choose_mutates_social_state():
    engine = GameEngine.new_game(seed=1)
    engine.player.morality = 30  # neutral band, one step from righteous

    result = engine.process_action(
        {
            "action": Action.DIALOGUE_CHOOSE,
            "character_id": "zhu_yan",
            "choice_id": "praise_him",
        }
    )

    assert result["event"] == EventType.DIALOGUE_CHOICE
    # relationship score changed (0 -> 40, neutral -> friendly)
    assert engine.player.relationships["zhu_yan"]["relationship_score"] == 40
    assert result["relationship"]["tier"] == "friendly"
    # morality band changed (30 -> 40, neutral -> righteous)
    assert engine.player.morality == 40
    assert result["morality"]["band"] == "righteous"
    # reputation changed (0 -> 8)
    assert engine.player.reputation == 8
    assert result["reputation"] == 8
    assert result["reputation_delta"] == 8


def test_relationship_tier_gates_duel():
    engine = GameEngine.new_game(seed=1)

    # Zhu Yan only duels once you've earned his respect (friendly tier).
    assert engine.character_service.can_duel("zhu_yan", engine.player) == {
        "allowed": False,
        "reason": "RELATIONSHIP_TOO_LOW",
    }

    engine.process_action(
        {
            "action": Action.DIALOGUE_CHOOSE,
            "character_id": "zhu_yan",
            "choice_id": "praise_him",
        }
    )

    after = engine.character_service.can_duel("zhu_yan", engine.player)
    assert after["allowed"] is True
    assert after["enemy_id"] == "zhu_yan_duel"
