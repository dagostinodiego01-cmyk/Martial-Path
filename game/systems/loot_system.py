"""Loot system.

Responsible for rolling enemy loot tables and adding successful drops to the
player's inventory. The engine decides *when* loot should be rolled; this system
decides *how* it is rolled.

Returns structured results only; never prints or formats player-facing text.
"""
from __future__ import annotations

from typing import Any, Dict, List

from game.core.constants import EventType
from game.models.player import Player
from game.systems.inventory_system import InventorySystem
from game.utils.rng import RNG


class LootSystem:
    """Rolls loot tables and grants successful drops."""

    def __init__(self, inventory: InventorySystem, rng: RNG) -> None:
        self._inventory = inventory
        self._rng = rng

    def roll_loot(self, player: Player, loot_table: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Roll each entry in ``loot_table`` and return the drops obtained."""
        obtained: List[Dict[str, Any]] = []
        for entry in loot_table:
            if self._rng.chance(entry.get("chance", 0.0)):
                added = self._inventory.add_item(
                    player, entry["item_id"], entry.get("count", 1)
                )
                if added.get("event") == EventType.LOOT:
                    obtained.append(added)
        return obtained
