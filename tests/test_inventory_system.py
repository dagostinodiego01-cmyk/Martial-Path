"""Tests for the inventory system's item usage and consumption rules."""
from game.core.constants import EventType
from game.models.item import Item
from game.models.player import Player
from game.systems.effect_system import EffectSystem
from game.systems.inventory_system import InventorySystem


def make_inventory_system():
    items = {
        "healing_pill": Item(
            id="healing_pill",
            name="Healing Pill",
            type="consumable",
            effect="heal",
            magnitude=40,
            consumed_on_use=True,
        ),
        "spirit_stone": Item(
            id="spirit_stone",
            name="Spirit Stone",
            type="material",
            effect="cultivation_boost",
            magnitude=25,
            consumed_on_use=True,
        ),
        "talent_refining_elixir": Item(
            id="talent_refining_elixir",
            name="Talent Refining Elixir",
            type="material",
            effect="none",
            magnitude=0,
        ),
    }
    return InventorySystem(items, EffectSystem())


def test_use_consumable_item_reduces_count():
    player = Player(name="Tester", hp=50, max_hp=100, inventory={"healing_pill": 1})
    inventory = make_inventory_system()

    result = inventory.use_item(player, "healing_pill")

    assert result["event"] == EventType.ITEM_USED
    assert player.hp == 90
    assert player.inventory.get("healing_pill", 0) == 0


def test_use_unowned_item_returns_error():
    player = Player(name="Tester", inventory={})
    inventory = make_inventory_system()

    result = inventory.use_item(player, "healing_pill")

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "ITEM_NOT_OWNED"


def test_consumed_on_use_material_is_removed():
    inventory = make_inventory_system()
    player = Player(name="Tester", progress=0, inventory={"spirit_stone": 1})

    result = inventory.use_item(player, "spirit_stone")

    assert result["event"] == EventType.ITEM_USED
    assert player.progress == 25
    assert player.inventory.get("spirit_stone", 0) == 0


def test_use_effectless_material_returns_not_usable():
    # The Talent Refining Elixir is spent by UPGRADE_TALENT, not USE_ITEM; using
    # it directly must error honestly instead of reporting a no-op success.
    inventory = make_inventory_system()
    player = Player(name="Tester", inventory={"talent_refining_elixir": 2})

    result = inventory.use_item(player, "talent_refining_elixir")

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "ITEM_NOT_USABLE"
    # Nothing consumed, nothing changed.
    assert player.inventory.get("talent_refining_elixir") == 2
