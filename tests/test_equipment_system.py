"""Tests for data-driven equipment slots, requirements, and modifiers."""
from game.core.constants import EventType
from game.models.player import Player
from game.systems.equipment_system import EquipmentSystem
from game.systems.stats_system import StatsSystem
from game.utils.data_loader import load_json


def _make_system():
    return EquipmentSystem(
        load_json("equipment.json"),
        load_json("cultivation/body_transformation_realms.json"),
        load_json("cultivation/essence_gathering_realms.json"),
    )


def _bind(player: Player, equipment: EquipmentSystem) -> None:
    setattr(player, "equipment_modifiers", lambda: equipment.aggregate_modifiers(player))


def test_equip_item_success_does_not_mutate_base_stats():
    system = _make_system()
    player = Player(name="Tester", inventory={"training_sword": 1})
    _bind(player, system)
    before_attack = player.attack

    result = system.equip_item(player, "training_sword", "weapon")

    assert result["event"] == EventType.EQUIP_ITEM_RESULT
    assert player.equipment["weapon"] == "training_sword"
    assert player.attack == before_attack
    assert StatsSystem({}).effective_stats(player)["attack"] == before_attack + 2


def test_unequip_item_success_clears_slot_without_mutating_base_stats():
    system = _make_system()
    player = Player(name="Tester", inventory={"training_sword": 1})
    _bind(player, system)
    system.equip_item(player, "training_sword", "weapon")
    before_attack = player.attack

    result = system.unequip_item(player, slot="weapon")

    assert result["event"] == EventType.UNEQUIP_ITEM_RESULT
    assert player.equipment["weapon"] is None
    assert player.attack == before_attack
    assert StatsSystem({}).effective_stats(player)["attack"] == before_attack


def test_ring_slot_compatibility_and_rejection():
    system = _make_system()
    player = Player(name="Tester", inventory={"minor_qi_ring": 1})

    assert system.equip_item(player, "minor_qi_ring", "ring_1")["event"] == EventType.EQUIP_ITEM_RESULT
    assert system.equip_item(player, "minor_qi_ring", "ring_2")["event"] == EventType.EQUIP_ITEM_RESULT
    rejected = system.equip_item(player, "minor_qi_ring", "weapon")
    assert rejected["event"] == EventType.ERROR
    assert rejected["reason"] == "SLOT_NOT_ALLOWED"


def test_artifact_slot_compatibility_and_rejection():
    system = _make_system()
    player = Player(name="Tester", inventory={"nameless_bone_shard": 1})

    assert system.equip_item(player, "nameless_bone_shard", "artifact_1")["event"] == EventType.EQUIP_ITEM_RESULT
    assert system.equip_item(player, "nameless_bone_shard", "artifact_2")["event"] == EventType.EQUIP_ITEM_RESULT
    rejected = system.equip_item(player, "nameless_bone_shard", "ring_1")
    assert rejected["reason"] == "SLOT_NOT_ALLOWED"


def test_flying_sword_slot_restriction():
    system = _make_system()
    player = Player(name="Tester", inventory={"rusted_flying_sword": 1, "training_sword": 1}, comprehension=20)
    player.cultivation_state.essence.realm_id = "xiantian"

    assert system.equip_item(player, "rusted_flying_sword", "flying_sword")["event"] == EventType.EQUIP_ITEM_RESULT
    assert system.equip_item(player, "rusted_flying_sword", "weapon")["reason"] == "SLOT_NOT_ALLOWED"
    assert system.equip_item(player, "training_sword", "flying_sword")["reason"] == "SLOT_NOT_ALLOWED"


def test_requirement_failure_keeps_equipment_unchanged():
    system = _make_system()
    player = Player(name="Tester", inventory={"rusted_flying_sword": 1}, comprehension=10)

    result = system.equip_item(player, "rusted_flying_sword", "flying_sword")

    assert result["event"] == EventType.ERROR
    assert result["reason"] in {"REALM_TOO_LOW", "COMPREHENSION_TOO_LOW"}
    assert player.equipment["flying_sword"] is None


def test_replacement_overwrites_slot_once():
    system = _make_system()
    player = Player(name="Tester", inventory={"training_sword": 1, "iron_spear": 1})

    first = system.equip_item(player, "training_sword", "weapon")
    second = system.equip_item(player, "iron_spear", "weapon")

    assert first["previous_item_id"] is None
    assert second["previous_item_id"] == "training_sword"
    assert player.equipment["weapon"] == "iron_spear"