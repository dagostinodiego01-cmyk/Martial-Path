"""Tests for data-driven shops and purchase validation."""
from game.core.constants import EventType
from game.models.item import Item
from game.models.player import Player
from game.systems.shop_system import ShopSystem


def _items():
    return {
        "training_sword": Item(
            id="training_sword",
            name="Training Sword",
            type="equipment",
            effect="none",
            magnitude=0,
            category="martial_weapon",
            rarity="mortal_grade",
            valid_slots=["weapon"],
        ),
        "qi_pill": Item(
            id="qi_pill",
            name="Qi Recovery Pill",
            type="consumable",
            effect="restore_qi",
            magnitude=30,
        ),
    }


def _shops():
    return [
        {
            "id": "village_market",
            "display_name": "Village Market",
            "location_ids": ["azure_village"],
            "stock": [
                {"item_id": "training_sword", "price": {"gold": 25}, "stock": 2},
                {"item_id": "qi_pill", "price": {"spirit_stone": 1}},
            ],
        }
    ]


def test_shop_view_lists_location_stock_and_wallet():
    system = ShopSystem(_shops(), _items())
    player = Player(name="Tester", current_location="azure_village", gold=30, inventory={"spirit_stone": 2})

    result = system.shop_view(player)

    assert result["event"] == EventType.SHOP
    assert result["shop"]["id"] == "village_market"
    assert result["wallet"] == {"gold": 30, "spirit_stone": 2}
    assert [entry["item_id"] for entry in result["stock"]] == ["training_sword", "qi_pill"]


def test_buy_equipment_with_gold_adds_inventory_and_spends_gold():
    system = ShopSystem(_shops(), _items())
    player = Player(name="Tester", current_location="azure_village", gold=30)

    result = system.buy_item(player, "training_sword")

    assert result["event"] == EventType.ITEM_PURCHASED
    assert player.gold == 5
    assert player.inventory["training_sword"] == 1


def test_buy_consumable_with_spirit_stone_item_currency():
    system = ShopSystem(_shops(), _items())
    player = Player(name="Tester", current_location="azure_village", inventory={"spirit_stone": 2})

    result = system.buy_item(player, "qi_pill")

    assert result["event"] == EventType.ITEM_PURCHASED
    assert player.inventory["spirit_stone"] == 1
    assert player.inventory["qi_pill"] == 1


def test_purchase_rejects_missing_funds_without_mutating_inventory():
    system = ShopSystem(_shops(), _items())
    player = Player(name="Tester", current_location="azure_village", gold=10)

    result = system.buy_item(player, "training_sword")

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "INSUFFICIENT_FUNDS"
    assert player.gold == 10
    assert "training_sword" not in player.inventory


def test_purchase_requires_shop_at_current_location():
    system = ShopSystem(_shops(), _items())
    player = Player(name="Tester", current_location="outer_forest", gold=30)

    result = system.buy_item(player, "training_sword")
    assert result["event"] == EventType.ERROR
    assert result["reason"] == "NO_SHOP_AVAILABLE"