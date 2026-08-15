"""Economy and gear: buy/sell, equip, repair, use, learn, and join a sect."""
from __future__ import annotations

from typing import Any, Dict

from game.core.constants import EventType


class EconomyMixin:
    """Item/equipment/currency verbs plus sect membership."""

    def _equip_item(self, action: Dict[str, Any]) -> Dict[str, Any]:
        result = self.equipment.equip_item(self.player, action.get("item_id", ""), action.get("slot", ""))
        if result.get("event") != EventType.ERROR:
            result["effective_stats"] = self.stats.effective_stats(self.player)
        return result

    def _unequip_item(self, action: Dict[str, Any]) -> Dict[str, Any]:
        result = self.equipment.unequip_item(self.player, action.get("slot", ""), action.get("item_id", ""))
        if result.get("event") != EventType.ERROR:
            result["effective_stats"] = self.stats.effective_stats(self.player)
        return result

    def _buy_item(self, action: Dict[str, Any]) -> Dict[str, Any]:
        quantity = action.get("quantity", 1)
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return {"event": EventType.ERROR, "reason": "INVALID_QUANTITY", "quantity": quantity}
        result = self.shops.buy_item(
            self.player,
            action.get("item_id", ""),
            quantity,
            action.get("shop_id", ""),
        )
        if result.get("event") != EventType.ERROR:
            result["inventory_items"] = self.inventory.list_inventory(self.player)["items"]
        return result

    def _sell_item(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Sell owned items/equipment for gold."""
        quantity = action.get("quantity", 1)
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return {"event": EventType.ERROR, "reason": "INVALID_QUANTITY", "quantity": quantity}
        result = self.sell.sell_item(self.player, action.get("item_id", ""), quantity)
        if result.get("event") != EventType.ERROR:
            result["inventory_items"] = self.inventory.list_inventory(self.player)["items"]
        return result

    def _repair_item(self, item_id: str) -> Dict[str, Any]:
        """Repair an equipped piece of worn gear, spending gold per durability point."""
        result = self.equipment.repair_item(self.player, item_id)
        if result.get("event") == EventType.REPAIR_RESULT:
            result["equipment_details"] = self.equipment.equipment_details(self.player)
            result["effective_stats"] = self.stats.effective_stats(self.player)
            result["wallet"] = {"gold": self.player.gold}
        return result

    def _use_item(self, item_id: str) -> Dict[str, Any]:
        """Use an item in exploration; technique manuals teach their skill instead."""
        item = self._items.get(item_id)
        if item is not None and item.effect == "learn_skill" and item.skill_id:
            if self.player.inventory.get(item_id, 0) <= 0:
                return {"event": EventType.ERROR, "reason": "ITEM_NOT_OWNED", "item_id": item_id}
            result = self.techniques.learn_skill(self.player, item.skill_id, source="manual")
            if result.get("event") == EventType.SKILL_LEARNED:
                self.inventory.remove_item(self.player, item_id, 1)
                result["item_id"] = item_id
                result["inventory_items"] = self.inventory.list_inventory(self.player)["items"]
            return result
        return self.inventory.use_item(self.player, item_id)

    def _learn_skill(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Learn a technique from a location trainer, paying its currency cost."""
        result = self.trainers.learn(
            self.player,
            action.get("skill_id", ""),
            action.get("trainer_id", ""),
        )
        if result.get("event") == EventType.SKILL_LEARNED:
            result["known_skills"] = self.get_known_skills()
        return result

    def _join_sect(self, sect_id: str) -> Dict[str, Any]:
        """Join a sect, assigning the player's martial path."""
        result = self.sects.join(self.player, sect_id)
        if result.get("event") == EventType.SECT_JOINED:
            result["player"] = self._player_view()
            updates = self.quests.notify("join_sect", self.player, self.inventory, target=sect_id)
            if updates:
                result["quest_updates"] = updates
        return result
