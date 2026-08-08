"""Equipment rules and modifier aggregation.

Equipment is owned through the normal inventory and referenced by slot from the
player state. Equipping and unequipping never mutate base stats; callers ask this
system for aggregated modifiers when deriving final stats or cultivation effects.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from game.core.constants import EventType
from game.models.player import EQUIPMENT_SLOTS, Player


class EquipmentSystem:
    """Validates equipment actions and aggregates equipped modifiers."""

    def __init__(
        self,
        equipment_data: Iterable[Dict[str, Any]],
        body_realms: Dict[str, Any],
        essence_realms: Dict[str, Any],
    ) -> None:
        self._equipment = {entry["id"]: dict(entry) for entry in equipment_data}
        self._body_order = self._realm_orders(body_realms.get("realms", []))
        self._essence_order = self._realm_orders(essence_realms.get("realms", []))

    def equip_item(self, player: Player, item_id: str, slot: str) -> Dict[str, Any]:
        if not item_id:
            return self._error("NO_ITEM_SPECIFIED", item_id=item_id, slot=slot)
        if not slot:
            return self._error("INVALID_EQUIPMENT_SLOT", item_id=item_id, slot=slot)
        if player.inventory.get(item_id, 0) <= 0:
            return self._error("ITEM_NOT_OWNED", item_id=item_id, slot=slot)
        item = self._equipment.get(item_id)
        if item is None or not bool(item.get("equippable", True)):
            return self._error("ITEM_NOT_EQUIPPABLE", item_id=item_id, slot=slot)
        if slot not in EQUIPMENT_SLOTS:
            return self._error("INVALID_EQUIPMENT_SLOT", item_id=item_id, slot=slot)
        if slot not in self._valid_slots(item):
            return self._error("SLOT_NOT_ALLOWED", item_id=item_id, slot=slot)
        failed = self._requirement_failure(player, item)
        if failed:
            failed.update({"item_id": item_id, "slot": slot, "event": EventType.ERROR})
            return failed

        previous_item_id = player.equipment.get(slot)
        player.equipment[slot] = item_id
        return {
            "event": EventType.EQUIP_ITEM_RESULT,
            "success": True,
            "item_id": item_id,
            "display_name": item.get("display_name", item_id),
            "slot": slot,
            "previous_item_id": previous_item_id,
            "equipment": dict(player.equipment),
            "equipment_details": self.equipment_details(player),
            "equipment_modifiers": self.aggregate_modifiers(player),
            "player_message": f"You equip {item.get('display_name', item_id)}.",
        }

    def unequip_item(self, player: Player, slot: str = "", item_id: str = "") -> Dict[str, Any]:
        resolved_slot = slot or self._slot_for_item(player, item_id)
        if not resolved_slot or resolved_slot not in EQUIPMENT_SLOTS:
            return self._error("INVALID_EQUIPMENT_SLOT", item_id=item_id, slot=slot)
        equipped_item_id = player.equipment.get(resolved_slot)
        if not equipped_item_id:
            return self._error("EQUIPMENT_SLOT_EMPTY", item_id=item_id, slot=resolved_slot)
        item = self._equipment.get(equipped_item_id, {})
        player.equipment[resolved_slot] = None
        return {
            "event": EventType.UNEQUIP_ITEM_RESULT,
            "success": True,
            "item_id": equipped_item_id,
            "display_name": item.get("display_name", equipped_item_id),
            "slot": resolved_slot,
            "equipment": dict(player.equipment),
            "equipment_details": self.equipment_details(player),
            "equipment_modifiers": self.aggregate_modifiers(player),
            "player_message": f"You unequip {item.get('display_name', equipped_item_id)}.",
        }

    def aggregate_modifiers(self, player: Player) -> Dict[str, Dict[str, float]]:
        totals: Dict[str, Dict[str, float]] = {
            "stat_modifiers": {},
            "cultivation_modifiers": {},
            "utility_modifiers": {},
        }
        for item in self._equipped_items(player):
            for group in totals:
                for key, value in item.get(group, {}).items():
                    number = float(value)
                    if key.endswith("_multiplier"):
                        totals[group][key] = totals[group].get(key, 1.0) * number
                    else:
                        totals[group][key] = totals[group].get(key, 0.0) + number
        return totals

    def equipment_details(self, player: Player) -> Dict[str, Dict[str, Any]]:
        details: Dict[str, Dict[str, Any]] = {}
        for slot, item_id in player.equipment.items():
            if not item_id:
                continue
            item = self._equipment.get(item_id)
            if item is None:
                continue
            details[slot] = {
                "id": item_id,
                "display_name": item.get("display_name", item_id),
                "rarity": item.get("rarity", "mortal_grade"),
                "category": item.get("category", ""),
                "description": item.get("description", ""),
                "stat_modifiers": dict(item.get("stat_modifiers", {})),
                "cultivation_modifiers": dict(item.get("cultivation_modifiers", {})),
                "utility_modifiers": dict(item.get("utility_modifiers", {})),
            }
        return details

    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        item = self._equipment.get(item_id)
        return dict(item) if item else None

    def _equipped_items(self, player: Player) -> List[Dict[str, Any]]:
        return [self._equipment[item_id] for item_id in player.equipment.values() if item_id in self._equipment]

    def _valid_slots(self, item: Dict[str, Any]) -> List[str]:
        slots = item.get("valid_slots")
        if isinstance(slots, list) and slots:
            return [str(slot) for slot in slots]
        slot = str(item.get("slot", ""))
        if slot == "ring":
            return ["ring_1", "ring_2"]
        if slot == "artifact":
            return ["artifact_1", "artifact_2"]
        return [slot] if slot else []

    def _requirement_failure(self, player: Player, item: Dict[str, Any]) -> Dict[str, Any]:
        requirements = item.get("requirements", {}) or {}
        body_realm = requirements.get("minimum_body_realm")
        if body_realm and self._realm_too_low(player.cultivation_state.body.realm_id, str(body_realm), self._body_order):
            return {"reason": "REALM_TOO_LOW", "required": body_realm}
        essence_realm = requirements.get("minimum_essence_realm")
        if essence_realm and self._realm_too_low(player.cultivation_state.essence.realm_id, str(essence_realm), self._essence_order):
            return {"reason": "REALM_TOO_LOW", "required": essence_realm}
        minimum_strength = int(requirements.get("minimum_strength", 0) or 0)
        if minimum_strength and player.body_strength < minimum_strength:
            return {"reason": "STRENGTH_TOO_LOW", "required": minimum_strength}
        minimum_comprehension = int(requirements.get("minimum_comprehension", 0) or 0)
        if minimum_comprehension and player.comprehension < minimum_comprehension:
            return {"reason": "COMPREHENSION_TOO_LOW", "required": minimum_comprehension}
        if requirements.get("required_faction"):
            return {"reason": "FACTION_REQUIRED", "required": requirements.get("required_faction")}
        if requirements.get("required_quest_flags"):
            return {"reason": "QUEST_FLAG_REQUIRED", "required": list(requirements.get("required_quest_flags", []))}
        return {}

    def _slot_for_item(self, player: Player, item_id: str) -> str:
        for slot, equipped_item_id in player.equipment.items():
            if equipped_item_id == item_id:
                return slot
        return ""

    def _realm_too_low(self, current_id: str, required_id: str, orders: Dict[str, int]) -> bool:
        return orders.get(current_id, -1) < orders.get(required_id, 10**9)

    def _realm_orders(self, realms: Iterable[Dict[str, Any]]) -> Dict[str, int]:
        return {str(realm.get("id")): int(realm.get("order", 0)) for realm in realms}

    def _error(self, reason: str, item_id: str = "", slot: str = "") -> Dict[str, Any]:
        return {"event": EventType.ERROR, "reason": reason, "item_id": item_id, "slot": slot}