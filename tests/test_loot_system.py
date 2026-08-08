"""Tests for the loot system's drop rolling."""
from game.models.item import Item
from game.models.player import Player
from game.systems.effect_system import EffectSystem
from game.systems.inventory_system import InventorySystem
from game.systems.loot_system import LootSystem
from game.utils.rng import RNG


def test_loot_system_adds_guaranteed_drop():
    player = Player(name="Tester")
    inventory = InventorySystem(
        {
            "beast_core": Item(
                id="beast_core",
                name="Beast Core",
                type="material",
                effect="none",
                magnitude=0,
            )
        },
        EffectSystem(),
    )
    loot = LootSystem(inventory, RNG(seed=1))

    result = loot.roll_loot(player, [{"item_id": "beast_core", "chance": 1.0, "count": 1}])

    assert len(result) == 1
    assert player.inventory["beast_core"] == 1
