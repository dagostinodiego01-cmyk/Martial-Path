"""Tests for the medium-priority close-out (P10-P17).

Covers: techniques listing, talent upgrades, closed-door cultivation + seasons,
equipment set bonuses + durability + repair, ironman/NG+/save export-import,
ai_prompt_notes surfacing, and enemy abilities.
"""
from game.core.constants import Action, EventType
from game.core.game_engine import GameEngine
from game.data.registry import GameDataRegistry
from game.models.enemy import Enemy
from game.models.player import Player
from game.systems.combat_system import CombatSystem
from game.utils.rng import RNG


# -- P10: techniques listing ------------------------------------------------
def test_techniques_action_lists_known_skills():
    engine = GameEngine.new_game(seed=1)

    result = engine.process_action({"action": Action.TECHNIQUES})

    assert result["event"] == EventType.TECHNIQUES
    known = {skill["id"] for skill in result["skills"]}
    assert "iron_fist" in known
    assert "flowing_step" in known


# -- P11: talent upgrades ----------------------------------------------------
def test_talents_view_and_upgrade():
    engine = GameEngine.new_game(seed=1)
    engine.player.martial_talent_id = "no_talent"
    engine.player.inventory["talent_refining_elixir"] = 1

    view = engine.process_action({"action": Action.TALENTS})
    assert view["event"] == EventType.TALENTS
    assert view["martial_upgrades"][0]["target_id"] == "common_grade_1"
    assert view["martial_upgrades"][0]["cost"] == {"talent_refining_elixir": 1}

    result = engine.process_action(
        {"action": Action.UPGRADE_TALENT, "track": "martial", "target_id": "common_grade_1"}
    )
    assert result["event"] == EventType.TALENT_UPGRADED
    assert engine.player.martial_talent_id == "common_grade_1"
    assert engine.player.inventory.get("talent_refining_elixir", 0) == 0


def test_talent_upgrade_rejected_when_unaffordable():
    engine = GameEngine.new_game(seed=1)
    engine.player.martial_talent_id = "no_talent"

    result = engine.process_action(
        {"action": Action.UPGRADE_TALENT, "track": "martial", "target_id": "common_grade_1"}
    )
    assert result["reason"] == "INSUFFICIENT_RESOURCES"
    assert engine.player.martial_talent_id == "no_talent"


def test_talent_refining_elixir_is_reachable_across_sources():
    registry = GameDataRegistry.load()

    item_ids = {entry["id"] for entry in registry.items}
    assert "talent_refining_elixir" in item_ids

    # Encounters: at least one location pool drops it.
    assert any(
        entry.get("item_id") == "talent_refining_elixir"
        for pool in registry.encounter_pools.values()
        for entry in pool.get("loot", [])
    )
    # Shops: at least one market stocks it.
    assert any(
        entry.get("item_id") == "talent_refining_elixir"
        for shop in registry.shops
        for entry in shop.get("stock", [])
    )
    # Masters: at least one master grants it as a relationship reward.
    assert any(
        reward.get("reward", {}).get("item_id") == "talent_refining_elixir"
        for character in registry.characters
        for reward in character.get("gameplay_hooks", {}).get("relationship_rewards", [])
        if isinstance(reward, dict)
    )


def test_talent_upgrade_rejected_for_bad_target():
    engine = GameEngine.new_game(seed=1)
    engine.player.martial_talent_id = "no_talent"

    result = engine.process_action(
        {"action": Action.UPGRADE_TALENT, "track": "martial", "target_id": "saint_grade"}
    )
    assert result["reason"] == "INVALID_UPGRADE_TARGET"


# -- P12: closed-door cultivation + seasons ----------------------------------
def test_closed_door_cultivation_ages_and_grants_progress():
    engine = GameEngine.new_game(seed=1)
    before_age = engine.player.age_years

    result = engine.process_action({"action": Action.CLOSED_DOOR, "years": 3})

    assert result["event"] == EventType.CLOSED_DOOR_RESULT
    assert result["progress_gained"] == 75.0
    assert engine.player.age_years == round(before_age + 3, 4)


def test_closed_door_rejects_unknown_years():
    engine = GameEngine.new_game(seed=1)

    result = engine.process_action({"action": Action.CLOSED_DOOR, "years": 7})

    assert result["reason"] == "INVALID_CLOSED_DOOR_YEARS"


def test_lifespan_view_reports_season():
    engine = GameEngine.new_game(seed=1)

    season = engine.get_game_state()["player"]["lifespan"]["season"]

    assert season == "Spring"


# -- P14: set bonuses + durability + repair ----------------------------------
def _equip_set_pair(engine: GameEngine) -> None:
    engine.player.comprehension = 20
    engine.player.inventory["spirit_devouring_saber"] = 1
    engine.player.inventory["spirit_devouring_shroud"] = 1
    engine.equipment.equip_item(engine.player, "spirit_devouring_saber", "weapon")
    engine.equipment.equip_item(engine.player, "spirit_devouring_shroud", "cloak")


def test_set_bonus_applies_when_two_pieces_equipped():
    engine = GameEngine.new_game(seed=1)
    _equip_set_pair(engine)

    mods = engine.equipment.aggregate_modifiers(engine.player)

    # Saber (attack 16) + shroud (no attack) + 2-piece set bonus (attack +8).
    assert mods["stat_modifiers"]["attack"] == 24
    assert mods["stat_modifiers"]["max_hp"] == 40


def test_durability_degrades_and_repairs():
    engine = GameEngine.new_game(seed=1)
    engine.player.comprehension = 20
    engine.player.inventory["spirit_devouring_saber"] = 1
    engine.equipment.equip_item(engine.player, "spirit_devouring_saber", "weapon")

    degraded = engine.equipment.degrade_equipped(engine.player, 1)
    assert degraded["weapon"] == 59  # 60 - 1

    engine.player.gold = 100
    result = engine.equipment.repair_item(engine.player, "spirit_devouring_saber")
    assert result["event"] == EventType.REPAIR_RESULT
    assert result["durability"] == 60
    assert engine.player.equipment_durability["weapon"] == 60


def test_broken_equipment_provides_no_modifiers():
    engine = GameEngine.new_game(seed=1)
    engine.player.comprehension = 20
    engine.player.inventory["spirit_devouring_saber"] = 1
    engine.equipment.equip_item(engine.player, "spirit_devouring_saber", "weapon")
    engine.player.equipment_durability["weapon"] = 0

    mods = engine.equipment.aggregate_modifiers(engine.player)

    assert "attack" not in mods["stat_modifiers"]


# -- P15: ironman + NG+ + save export/import ---------------------------------
def test_ironman_blocks_load():
    engine = GameEngine.new_game(seed=1, ironman=True)

    result = engine.process_action({"action": Action.LOAD, "slot": "default"})

    assert result["reason"] == "IRONMAN_MODE"


def test_new_game_plus_grants_scaling_bonus():
    engine = GameEngine.new_game(seed=1, ng_plus=2)

    assert engine.player.comprehension == 12  # 10 + 2
    assert engine.player.gold == 200  # 2 * 100


def test_export_then_import_round_trips_state():
    engine = GameEngine.new_game(seed=1)
    engine.player.gold = 1234

    exported = engine.process_action({"action": Action.EXPORT_SAVE})
    assert exported["event"] == EventType.SAVE_EXPORTED

    engine.player.gold = 0
    imported = engine.process_action(
        {"action": Action.IMPORT_SAVE, "payload": exported["payload"], "slot": "portable"}
    )
    assert imported["event"] == EventType.SAVE_IMPORTED
    assert engine.player.gold == 1234


# -- P16: ai_prompt_notes surfacing -----------------------------------------
def test_talk_surfaces_ai_prompt_notes():
    engine = GameEngine.new_game(seed=1)

    result = engine.process_action({"action": Action.TALK_TO_CHARACTER, "character_id": "zhu_yan"})

    assert result["event"] == EventType.CHARACTER_INTERACTION
    assert result.get("speech_notes")


# -- P17: enemy abilities -----------------------------------------------------
def _enemy_with(ability: dict) -> Enemy:
    return Enemy.from_dict(
        {
            "id": "e",
            "name": "Enemy",
            "body_realm_id": "mortal",
            "hp": 50,
            "attack": 10,
            "defense": 0,
            "abilities": [ability],
        }
    )


def test_enemy_poison_ability_applies_player_dot():
    combat = CombatSystem(RNG(1))
    player = Player(name="T", max_hp=100, hp=100)

    combat._enemy_act(player, _enemy_with({"type": "poison", "chance": 1.0, "magnitude": 5}))

    assert player.statuses["dot_damage"]["magnitude"] == 5.0


def test_enemy_stun_ability_stuns_player():
    combat = CombatSystem(RNG(1))
    player = Player(name="T", max_hp=100, hp=100)

    combat._enemy_act(player, _enemy_with({"type": "stun", "chance": 1.0, "magnitude": 2}))

    assert player.statuses["stun"]["turns"] == 2


def test_player_stunned_turn_forfeits_action():
    combat = CombatSystem(RNG(1))
    player = Player(name="T", max_hp=100, hp=100)
    player.statuses["stun"] = {"turns": 1, "magnitude": 0.0}
    enemy = _enemy_with({"type": "heavy", "chance": 0.0, "magnitude": 1})

    result = combat.player_stunned_turn(player, enemy)

    assert result["event"] == EventType.COMBAT_TURN
    assert "stun" not in player.statuses
