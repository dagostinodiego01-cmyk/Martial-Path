"""Inventory system.

Adds, removes, and uses items on a player's inventory (a ``{item_id: count}``
map). Item effects are resolved from an injected item registry. Consumables are
decremented on use. Returns structured results only.
"""
from __future__ import annotations

from typing import Any, Dict

from game.core.constants import EventType
from game.models.item import Item
from game.models.player import Player
from game.systems.effect_system import EffectSystem


class InventorySystem:
    """Manages a player's carried items."""

    def __init__(self, item_registry: Dict[str, Item], effects: EffectSystem) -> None:
        self._items = item_registry
        self._effects = effects

    def add_item(self, player: Player, item_id: str, count: int = 1) -> Dict[str, Any]:
        """Add ``count`` of an item to the player's inventory."""
        item = self._items.get(item_id)
        if item is None:
            return {"event": EventType.ERROR, "reason": "UNKNOWN_ITEM", "item_id": item_id}
        player.inventory[item_id] = player.inventory.get(item_id, 0) + count
        return {
            "event": EventType.LOOT,
            "item_id": item_id,
            "name": item.name,
            "count": count,
            "total": player.inventory[item_id],
        }

    def remove_item(self, player: Player, item_id: str, count: int = 1) -> bool:
        """Remove up to ``count`` of an item; return ``True`` if any was removed."""
        owned = player.inventory.get(item_id, 0)
        if owned <= 0:
            return False
        remaining = owned - count
        if remaining > 0:
            player.inventory[item_id] = remaining
        else:
            del player.inventory[item_id]
        return True

    def use_item(self, player: Player, item_id: str) -> Dict[str, Any]:
        """Apply an item's effect to the player and consume it if consumable."""
        if not item_id:
            return {"event": EventType.ERROR, "reason": "NO_ITEM_SPECIFIED"}
        if player.inventory.get(item_id, 0) <= 0:
            return {"event": EventType.ERROR, "reason": "ITEM_NOT_OWNED", "item_id": item_id}
        item = self._items[item_id]
        applied = self._effects.apply_to_player(player, item.effect, item.magnitude)
        if item.is_consumable():
            self.remove_item(player, item_id, 1)
        return {
            "event": EventType.ITEM_USED,
            "item_id": item_id,
            "name": item.name,
            "effect": item.effect,
            "remaining": player.inventory.get(item_id, 0),
            **applied,
        }

    def list_inventory(self, player: Player) -> Dict[str, Any]:
        """Return a structured listing of the player's items."""
        entries = []
        for item_id, count in player.inventory.items():
            item = self._items.get(item_id)
            if item is None:
                continue
            entry = {
                "item_id": item_id,
                "name": item.name,
                "type": item.type,
                "count": count,
                "description": item.description,
                "effect": item.effect,
                "usable": item.type != "equipment" and bool(item.effect) and item.effect != "none",
            }
            if item.type == "equipment":
                entry["category"] = item.category
                entry["rarity"] = item.rarity
                entry["valid_slots"] = list(item.valid_slots or [])
            entries.append(entry)
        return {"event": EventType.INVENTORY, "items": entries}
