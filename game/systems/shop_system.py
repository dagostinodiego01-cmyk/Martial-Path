"""Data-driven shop and purchase rules.

Shops are static data keyed by location. The system validates whether the player
can buy an offered item, spends supported currencies, and adds the purchased
item to inventory. It performs no I/O and returns structured results only.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from game.core.constants import EventType
from game.models.item import Item
from game.models.player import Player
from game.systems import currency


class ShopSystem:
    """Lists location shop stock and resolves item purchases."""

    SUPPORTED_CURRENCIES = currency.SUPPORTED_CURRENCIES

    def __init__(
        self,
        shops: Iterable[Dict[str, Any]],
        item_catalog: Dict[str, Item],
        economy_multiplier: float = 1.0,
        market_multiplier: float = 1.0,
    ) -> None:
        self._shops = {str(shop.get("id")): dict(shop) for shop in shops if shop.get("id")}
        self._items = item_catalog
        # World seed (C.6): a run's economy band (cheap 0.9 / fair 1.0 /
        # pricey 1.15) scales every shop price; integral by design so gold
        # amounts stay integers.
        self._economy_multiplier = max(0.1, float(economy_multiplier))
        # E.3: live market drift from the world simulation, layered on the
        # run-seed economy band. The engine refreshes this after every world
        # tick so displayed prices always equal charged prices.
        self._market_multiplier = max(0.1, float(market_multiplier))

    @property
    def economy_multiplier(self) -> float:
        """The price multiplier this world's economy band applies."""
        return self._economy_multiplier

    def shops_for_location(self, location_id: str) -> List[Dict[str, Any]]:
        """Return summary data for shops available at a location."""
        return [self._shop_summary(shop) for shop in self._shops.values() if self._is_at_location(shop, location_id)]

    def shop_view(self, player: Player, shop_id: str = "") -> Dict[str, Any]:
        """Return the current shop stock visible to the player."""
        shop = self._resolve_shop(player.current_location, shop_id)
        if shop is None:
            reason = "UNKNOWN_SHOP" if shop_id else "NO_SHOP_AVAILABLE"
            return {"event": EventType.ERROR, "reason": reason, "shop_id": shop_id, "location_id": player.current_location}
        if not self._is_at_location(shop, player.current_location):
            return {"event": EventType.ERROR, "reason": "SHOP_NOT_AVAILABLE", "shop_id": shop_id, "location_id": player.current_location}
        return {
            "event": EventType.SHOP,
            "shop": self._shop_summary(shop),
            "stock": [self._stock_view(entry) for entry in shop.get("stock", [])],
            "wallet": self._wallet_view(player),
        }

    def buy_item(self, player: Player, item_id: str, quantity: int = 1, shop_id: str = "") -> Dict[str, Any]:
        """Buy an item from an available shop, spending currency and adding inventory."""
        if not item_id:
            return {"event": EventType.ERROR, "reason": "NO_ITEM_SPECIFIED", "shop_id": shop_id}
        if quantity <= 0:
            return {"event": EventType.ERROR, "reason": "INVALID_QUANTITY", "item_id": item_id, "quantity": quantity}

        shop = self._resolve_shop(player.current_location, shop_id)
        if shop is None:
            reason = "UNKNOWN_SHOP" if shop_id else "NO_SHOP_AVAILABLE"
            return {"event": EventType.ERROR, "reason": reason, "shop_id": shop_id, "location_id": player.current_location}
        if not self._is_at_location(shop, player.current_location):
            return {"event": EventType.ERROR, "reason": "SHOP_NOT_AVAILABLE", "shop_id": shop_id, "location_id": player.current_location}

        stock = self._stock_entry(shop, item_id)
        if stock is None:
            return {"event": EventType.ERROR, "reason": "SHOP_ITEM_NOT_AVAILABLE", "shop_id": shop.get("id"), "item_id": item_id}
        item = self._items.get(item_id)
        if item is None:
            return {"event": EventType.ERROR, "reason": "UNKNOWN_ITEM", "shop_id": shop.get("id"), "item_id": item_id}
        if item.type == "equipment" and quantity != 1:
            return {"event": EventType.ERROR, "reason": "EQUIPMENT_QUANTITY_NOT_SUPPORTED", "item_id": item_id, "quantity": quantity}

        stock_limit = stock.get("stock")
        if stock_limit is not None and quantity > int(stock_limit):
            return {"event": EventType.ERROR, "reason": "SHOP_STOCK_TOO_LOW", "item_id": item_id, "available": int(stock_limit), "quantity": quantity}

        unit_price = self._price(stock)  # already scaled by the economy band
        total_price = {currency: amount * quantity for currency, amount in unit_price.items()}
        shortage = self._currency_shortage(player, total_price)
        if shortage:
            return {
                "event": EventType.ERROR,
                "reason": "INSUFFICIENT_FUNDS",
                "item_id": item_id,
                "price": total_price,
                "missing": shortage,
                "wallet": self._wallet_view(player),
            }

        self._spend(player, total_price)
        player.inventory[item_id] = player.inventory.get(item_id, 0) + quantity
        return {
            "event": EventType.ITEM_PURCHASED,
            "shop_id": str(shop.get("id")),
            "item_id": item_id,
            "name": item.name,
            "quantity": quantity,
            "price": total_price,
            "remaining_currency": self._wallet_view(player),
            "inventory_count": player.inventory.get(item_id, 0),
            "player_message": f"You purchase {item.name}.",
        }

    def _resolve_shop(self, location_id: str, shop_id: str) -> Optional[Dict[str, Any]]:
        if shop_id:
            return self._shops.get(shop_id)
        for shop in self._shops.values():
            if self._is_at_location(shop, location_id):
                return shop
        return None

    def _is_at_location(self, shop: Dict[str, Any], location_id: str) -> bool:
        return location_id in [str(entry) for entry in shop.get("location_ids", [])]

    def _stock_entry(self, shop: Dict[str, Any], item_id: str) -> Optional[Dict[str, Any]]:
        for entry in shop.get("stock", []):
            if entry.get("item_id") == item_id:
                return entry
        return None

    def _stock_view(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        item_id = str(entry.get("item_id", ""))
        item = self._items.get(item_id)
        view = {
            "item_id": item_id,
            "name": item.name if item else item_id,
            "type": item.type if item else "unknown",
            "description": item.description if item else "",
            "price": self._price(entry),
            "stock": entry.get("stock"),
        }
        if item and item.type == "equipment":
            view["category"] = item.category
            view["rarity"] = item.rarity
            view["valid_slots"] = list(item.valid_slots)
        return view

    def _shop_summary(self, shop: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": str(shop.get("id", "")),
            "display_name": str(shop.get("display_name", shop.get("id", ""))),
            "location_ids": [str(location_id) for location_id in shop.get("location_ids", [])],
            "description": str(shop.get("description", "")),
        }

    def set_market_multiplier(self, value: float) -> None:
        """Refresh the live market drift applied on top of the seed band (E.3)."""
        self._market_multiplier = max(0.1, float(value))

    def market_multiplier(self) -> float:
        """Return the current live market drift multiplier."""
        return self._market_multiplier

    def _price(self, stock: Dict[str, Any]) -> Dict[str, int]:
        """The displayed price of a stock entry: seed band * live market drift."""
        total = self._economy_multiplier * self._market_multiplier
        return {
            currency: max(1, round(amount * total))
            for currency, amount in currency.normalise_price(stock.get("price")).items()
        }

    def _currency_shortage(self, player: Player, price: Dict[str, int]) -> Dict[str, int]:
        return currency.shortage(player, price)

    def _spend(self, player: Player, price: Dict[str, int]) -> None:
        currency.spend(player, price)

    def _currency_amount(self, player: Player, currency_id: str) -> int:
        return currency.currency_amount(player, currency_id)

    def _wallet_view(self, player: Player) -> Dict[str, int]:
        return currency.wallet_view(player)