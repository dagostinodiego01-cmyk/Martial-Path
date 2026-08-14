"""Sell (liquidation) rules.

Converts owned items/equipment/manuals into gold at a fixed fraction of their
worth, closing the economy loop: exploration loot becomes currency. Equipment
carries its ``value`` from data; manuals derive one from rarity; plain items
derive one from a per-effect heuristic (documented in :meth:`SellSystem.worth`).

Pure logic: the caller owns the player; this system only validates, pays out
gold, and removes stock. It performs no I/O and returns structured results.
"""
from __future__ import annotations

from typing import Any, Dict

from game.core.constants import EventType
from game.models.item import Item
from game.models.player import Player

#: Fraction of an item's worth recovered on sale (the rest is the economy sink).
SELL_RATE = 0.5

#: Gold worth of a manual/equipment of each rarity grade (when no explicit value).
GOLD_PER_RARITY = {
    "mortal_grade": 10,
    "low_spirit_grade": 20,
    "middle_spirit_grade": 40,
    "high_spirit_grade": 80,
    "earth_grade": 160,
    "heaven_grade": 320,
    "dao_grade": 640,
}


class SellSystem:
    """Validates and performs selling owned items for gold."""

    def __init__(self, item_catalog: Dict[str, Item]) -> None:
        self._items = item_catalog

    def worth(self, item: Item) -> int:
        """Return the gold worth of an item (before the sell-rate discount)."""
        if item.value > 0:
            return item.value
        if item.rarity:
            return GOLD_PER_RARITY.get(item.rarity, GOLD_PER_RARITY["mortal_grade"])
        if item.id == "spirit_stone":
            return 50  # the premium currency is convertible back to gold
        effect = item.effect
        magnitude = int(item.magnitude)
        if effect == "heal":
            return max(5, magnitude // 4)
        if effect == "restore_qi":
            return max(5, magnitude // 2)
        if effect == "restore_hp_qi":
            return max(5, magnitude // 3)
        if effect == "breakthrough_aid":
            return 40 + magnitude * 10
        if effect in ("cleanse_poison", "body_temper"):
            return 30
        if effect == "comprehension_boost":
            return 50 + magnitude * 2
        if effect == "lifespan_extension":
            return 100
        if effect == "cultivation_boost":
            return max(10, magnitude)
        return 10  # materials with no other signal

    def unit_price(self, item: Item) -> int:
        """Return what one unit of ``item`` sells for in gold (min 1)."""
        return max(1, int(self.worth(item) * SELL_RATE))

    def sell_item(self, player: Player, item_id: str, quantity: int = 1) -> Dict[str, Any]:
        """Sell ``quantity`` of an owned item for gold; remove it from inventory."""
        if not item_id:
            return {"event": EventType.ERROR, "reason": "NO_ITEM_SPECIFIED"}
        if quantity <= 0:
            return {"event": EventType.ERROR, "reason": "INVALID_QUANTITY", "item_id": item_id, "quantity": quantity}
        item = self._items.get(item_id)
        if item is None:
            return {"event": EventType.ERROR, "reason": "UNKNOWN_ITEM", "item_id": item_id}
        owned = int(player.inventory.get(item_id, 0))
        if owned <= 0:
            return {"event": EventType.ERROR, "reason": "ITEM_NOT_OWNED", "item_id": item_id}
        if item.type == "equipment":
            if item_id in list(player.equipment.values()):
                return {"event": EventType.ERROR, "reason": "UNEQUIP_FIRST", "item_id": item_id}
            quantity = 1

        quantity = min(quantity, owned)
        unit = self.unit_price(item)
        total = unit * quantity
        player.gold += total

        remaining = owned - quantity
        if remaining > 0:
            player.inventory[item_id] = remaining
        else:
            player.inventory.pop(item_id, None)

        return {
            "event": EventType.ITEM_SOLD,
            "item_id": item_id,
            "name": item.name,
            "quantity": quantity,
            "unit_price": unit,
            "total": total,
            "gold": int(player.gold),
            "inventory_count": int(player.inventory.get(item_id, 0)),
            "player_message": f"You sell {item.name} for {total} gold.",
        }
