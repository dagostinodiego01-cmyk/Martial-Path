"""Tests for the sell (liquidation) rules that close the economy loop."""
from game.core.constants import EventType
from game.models.item import Item
from game.models.player import Player
from game.systems.sell_system import SellSystem


def _items():
    return {
        "healing_pill": Item(
            id="healing_pill",
            name="Healing Pill",
            type="consumable",
            effect="heal",
            magnitude=40,
        ),
        "training_sword": Item(
            id="training_sword",
            name="Training Sword",
            type="equipment",
            effect="none",
            magnitude=0,
            rarity="mortal_grade",
            value=25,
            valid_slots=["weapon"],
        ),
        "beast_core": Item(
            id="beast_core",
            name="Beast Core",
            type="material",
            effect="none",
            magnitude=0,
        ),
    }


def test_sell_consumable_pays_gold_and_removes_stock():
    system = SellSystem(_items())
    player = Player(name="Tester", gold=0, inventory={"healing_pill": 2})

    result = system.sell_item(player, "healing_pill", 1)

    # worth(heal 40) = max(5, 40//4) = 10 -> unit = 5
    assert result["event"] == EventType.ITEM_SOLD
    assert result["unit_price"] == 5
    assert player.gold == 5
    assert player.inventory["healing_pill"] == 1


def test_sell_partial_quantity_clamps_to_owned_and_keeps_remainder():
    system = SellSystem(_items())
    player = Player(name="Tester", inventory={"healing_pill": 2})

    result = system.sell_item(player, "healing_pill", 10)

    assert result["event"] == EventType.ITEM_SOLD
    assert result["quantity"] == 2
    assert "healing_pill" not in player.inventory


def test_sell_unknown_item_errors():
    system = SellSystem(_items())
    player = Player(name="Tester")

    result = system.sell_item(player, "nonexistent_item")

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "UNKNOWN_ITEM"


def test_sell_item_not_owned_errors():
    system = SellSystem(_items())
    player = Player(name="Tester")

    result = system.sell_item(player, "healing_pill")

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "ITEM_NOT_OWNED"


def test_sell_equipment_requires_unequip_first():
    system = SellSystem(_items())
    player = Player(
        name="Tester",
        inventory={"training_sword": 1},
        equipment={"weapon": "training_sword"},
    )

    result = system.sell_item(player, "training_sword")

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "UNEQUIP_FIRST"
    assert player.inventory["training_sword"] == 1


def test_sell_equipment_is_always_single_unit():
    system = SellSystem(_items())
    player = Player(name="Tester", inventory={"training_sword": 3})

    result = system.sell_item(player, "training_sword", 3)

    # worth(value 25) = 25 -> unit = 12
    assert result["event"] == EventType.ITEM_SOLD
    assert result["quantity"] == 1
    assert player.inventory["training_sword"] == 2
    assert player.gold == 12


def test_sell_material_without_signal_uses_floor_price():
    system = SellSystem(_items())
    player = Player(name="Tester", inventory={"beast_core": 1})

    result = system.sell_item(player, "beast_core")

    # no value/rarity/effect signal -> worth 10 -> unit 5
    assert result["event"] == EventType.ITEM_SOLD
    assert result["unit_price"] == 5
    assert player.gold == 5
