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
        self._set_bonuses_by_id: Dict[str, List[Dict[str, Any]]] = {}
        for entry in equipment_data:
            set_id = entry.get("set_id")
            if not set_id:
                continue
            bonuses = self._set_bonuses_by_id.setdefault(set_id, [])
            for bonus in entry.get("set_bonuses", []):
                if isinstance(bonus, dict) and bonus not in bonuses:
                    bonuses.append(dict(bonus))

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
        max_durability = self._max_durability(item)
        if max_durability:
            player.equipment_durability[slot] = max_durability
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
        for item in self._equipped_items(player, include_broken=False):
            self._merge_modifiers(totals, item)
        self._apply_set_bonuses(player, totals)
        return totals

    def _merge_modifiers(self, totals: Dict[str, Dict[str, float]], item: Dict[str, Any]) -> None:
        for group in totals:
            for key, value in item.get(group, {}).items():
                number = float(value)
                if key.endswith("_multiplier"):
                    totals[group][key] = totals[group].get(key, 1.0) * number
                else:
                    totals[group][key] = totals[group].get(key, 0.0) + number

    def _apply_set_bonuses(self, player: Player, totals: Dict[str, Dict[str, float]]) -> None:
        """Fold in the strongest met set-bonus threshold for each equipped set."""
        counts: Dict[str, int] = {}
        for item in self._equipped_items(player, include_broken=False):
            set_id = item.get("set_id")
            if set_id:
                counts[set_id] = counts.get(set_id, 0) + 1
        for set_id, worn in counts.items():
            bonuses = self._set_bonuses_by_id.get(set_id, [])
            best = None
            for bonus in bonuses:
                if int(bonus.get("pieces_required", 0)) <= worn:
                    best = bonus
            if best is not None:
                self._merge_modifiers(totals, best)

    def equipment_details(self, player: Player) -> Dict[str, Dict[str, Any]]:
        details: Dict[str, Dict[str, Any]] = {}
        for slot, item_id in player.equipment.items():
            if not item_id:
                continue
            item = self._equipment.get(item_id)
            if item is None:
                continue
            max_durability = self._max_durability(item)
            current = player.equipment_durability.get(slot, max_durability)
            details[slot] = {
                "id": item_id,
                "display_name": item.get("display_name", item_id),
                "rarity": item.get("rarity", "mortal_grade"),
                "category": item.get("category", ""),
                "description": item.get("description", ""),
                "stat_modifiers": dict(item.get("stat_modifiers", {})),
                "cultivation_modifiers": dict(item.get("cultivation_modifiers", {})),
                "utility_modifiers": dict(item.get("utility_modifiers", {})),
                "set_id": item.get("set_id"),
                "durability": None if not max_durability else current,
                "max_durability": None if not max_durability else max_durability,
                "broken": bool(max_durability and current <= 0),
            }
        return details

    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        item = self._equipment.get(item_id)
        return dict(item) if item else None

    def _equipped_items(self, player: Player, include_broken: bool = True) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for slot, item_id in player.equipment.items():
            if not item_id or item_id not in self._equipment:
                continue
            item = self._equipment[item_id]
            if not include_broken and self._is_broken(player, slot, item):
                continue
            items.append(item)
        return items

    # -- durability -------------------------------------------------------
    def _max_durability(self, item: Dict[str, Any]) -> int:
        """Return the item's durability ceiling, or 0 when it has no durability model."""
        return max(0, int(item.get("durability", 0) or 0))

    def _is_broken(self, player: Player, slot: str, item: Dict[str, Any]) -> bool:
        max_durability = self._max_durability(item)
        if not max_durability:
            return False
        return player.equipment_durability.get(slot, max_durability) <= 0

    def degrade_equipped(self, player: Player, amount: int = 1) -> Dict[str, int]:
        """Reduce each equipped destructible item's durability by ``amount``.

        Returns ``{slot: new_durability}`` for every item that degraded. Called on
        defeat so worn gear visibly weathers without being destroyed outright.
        """
        degraded: Dict[str, int] = {}
        for slot, item_id in player.equipment.items():
            if not item_id or item_id not in self._equipment:
                continue
            item = self._equipment[item_id]
            max_durability = self._max_durability(item)
            if not max_durability:
                continue
            current = player.equipment_durability.get(slot, max_durability)
            new_value = max(0, current - amount)
            player.equipment_durability[slot] = new_value
            degraded[slot] = new_value
        return degraded

    def repair_item(self, player: Player, item_id: str, cost_per_point: int = 2) -> Dict[str, Any]:
        """Restore a piece of equipped, destructible gear to full durability for gold.

        ``item_id`` may be the equipment id or the slot it occupies. Broken gear
        still occupies its slot, so repair is how it becomes useful again.
        """
        slot = item_id if item_id in player.equipment else self._slot_for_item(player, item_id)
        if not slot or slot not in player.equipment:
            return self._error("ITEM_NOT_EQUIPPED", item_id=item_id)
        equipped_id = player.equipment.get(slot)
        if not equipped_id:
            return self._error("EQUIPMENT_SLOT_EMPTY", item_id=item_id, slot=slot)
        item = self._equipment.get(equipped_id, {})
        max_durability = self._max_durability(item)
        if not max_durability:
            return self._error("NOT_REPAIRABLE", item_id=equipped_id, slot=slot)
        current = player.equipment_durability.get(slot, max_durability)
        if current >= max_durability:
            return self._error("NOTHING_TO_REPAIR", item_id=equipped_id, slot=slot)
        points = max_durability - current
        cost = points * cost_per_point
        if player.gold < cost:
            return {
                "event": EventType.ERROR,
                "reason": "INSUFFICIENT_FUNDS",
                "required": cost,
                "gold": player.gold,
                "item_id": equipped_id,
                "slot": slot,
            }
        player.gold -= cost
        player.equipment_durability[slot] = max_durability
        return {
            "event": EventType.REPAIR_RESULT,
            "item_id": equipped_id,
            "slot": slot,
            "display_name": item.get("display_name", equipped_id),
            "durability": max_durability,
            "cost": cost,
            "player_message": f"You restore {item.get('display_name', equipped_id)} to full condition.",
        }

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