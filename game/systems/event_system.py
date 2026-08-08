"""Event system.

Generates random exploration encounters. It only *selects* content and returns a
descriptor; the engine decides how to apply it (spawn a fight, grant loot, apply
a special effect). This split keeps content selection here and state changes in
the engine.

Selection is location-aware: when ``encounter_pools`` contains an entry for the
player's current location, its weighted ``combat``/``loot``/``special`` pools are
used so each area has its own identity. Locations without a pool fall back to the
global pools defined in ``events.json``.

Returned descriptors:

* ``COMBAT``         — ``{"enemy_id", "text"}``
* ``LOOT``           — ``{"item_id", "count"}``
* ``SPECIAL``        — ``{"special_id", "text", "effect"}``
* ``EXPLORE_RESULT`` — a quiet "nothing happened" outcome
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from game.core.constants import EventType
from game.models.player import Player
from game.utils.rng import RNG

if TYPE_CHECKING:
    from game.systems.find_system import FindSystem

DEFAULT_WEIGHTS = {"COMBAT": 0.5, "LOOT": 0.25, "SPECIAL": 0.15, "NOTHING": 0.10}


class EventSystem:
    """Produces weighted random encounters from data-driven, location-scoped pools."""

    def __init__(
        self,
        events_data: Dict[str, Any],
        enemy_templates: List[Dict[str, Any]],
        rng: RNG,
        encounter_pools: Optional[Dict[str, Any]] = None,
        find_system: Optional["FindSystem"] = None,
    ) -> None:
        self._data = events_data or {}
        self._enemies = enemy_templates or []
        self._enemy_by_id = {template["id"]: template for template in self._enemies}
        self._rng = rng
        self._pools = encounter_pools or {}
        self._find_system = find_system

    def generate(self, player: Player, find_rarity_index: Optional[int] = None) -> Dict[str, Any]:
        """Pick and return the next exploration encounter descriptor.

        ``find_rarity_index`` caps the rarity of catalog-based finds for the
        current area (supplied by the engine from the location's danger level).
        """
        location_id = getattr(player, "current_location", "") or ""
        pool = self._pools.get(location_id)
        weights = self._data.get("encounter_weights") or DEFAULT_WEIGHTS
        kind = self._rng.weighted_choice(list(weights.keys()), list(weights.values()))
        if kind == "COMBAT":
            return self._combat_event(pool)
        if kind == "LOOT":
            return self._loot_event(pool, find_rarity_index)
        if kind == "SPECIAL":
            return self._special_event(pool)
        return self._nothing("You roam the misty wilds but encounter nothing of note.")

    # -- internal helpers -------------------------------------------------
    def _combat_event(self, pool: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        entries = (pool or {}).get("combat")
        if entries:
            enemy_id = self._rng.weighted_choice(
                [entry["enemy_id"] for entry in entries],
                [entry.get("weight", 1) for entry in entries],
            )
            template = self._enemy_by_id.get(enemy_id)
            if template is not None:
                return self._combat_descriptor(template)
        if not self._enemies:
            return self._nothing("The area is unnaturally still.")
        return self._combat_descriptor(self._rng.choice(self._enemies))

    def _combat_descriptor(self, template: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "event": EventType.COMBAT,
            "enemy_id": template["id"],
            "text": f"A {template['name']} lunges from the shadows!",
        }

    def _loot_event(self, pool: Optional[Dict[str, Any]], find_rarity_index: Optional[int] = None) -> Dict[str, Any]:
        # 1) A location's own curated loot pool always wins.
        source = (pool or {}).get("loot")
        if source:
            item_id = self._rng.weighted_choice(
                [entry["item_id"] for entry in source],
                [entry.get("weight", 1) for entry in source],
            )
            return {"event": EventType.LOOT, "item_id": item_id, "count": 1}
        # 2) Otherwise draw a rarity-weighted, danger-gated find from the catalog.
        if self._find_system is not None and find_rarity_index is not None:
            item_id = self._find_system.roll_find(find_rarity_index)
            if item_id:
                return {"event": EventType.LOOT, "item_id": item_id, "count": 1}
        # 3) Legacy fallback for callers that supply only a flat loot pool.
        legacy = self._data.get("loot_pool") or []
        if not legacy:
            return self._nothing("You search the area but find nothing of value.")
        item_id = self._rng.weighted_choice(
            [entry["item_id"] for entry in legacy],
            [entry.get("weight", 1) for entry in legacy],
        )
        return {"event": EventType.LOOT, "item_id": item_id, "count": 1}

    def _special_event(self, pool: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        specials = self._data.get("special_events") or []
        entries = (pool or {}).get("special")
        if entries and specials:
            by_id = {special.get("id"): special for special in specials}
            chosen_id = self._rng.weighted_choice(
                [entry["special_id"] for entry in entries],
                [entry.get("weight", 1) for entry in entries],
            )
            special = by_id.get(chosen_id)
            if special is not None:
                return self._special_descriptor(special)
        if not specials:
            return self._nothing("A strange feeling passes over you, then fades.")
        return self._special_descriptor(self._rng.choice(specials))

    def _special_descriptor(self, special: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "event": EventType.SPECIAL,
            "special_id": special.get("id"),
            "text": special.get("text", ""),
            "effect": special.get("effect", {}),
        }

    def _nothing(self, text: str) -> Dict[str, Any]:
        return {"event": EventType.EXPLORE_RESULT, "kind": "NOTHING", "text": text}

