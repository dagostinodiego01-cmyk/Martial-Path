"""Alchemy loop: gathering herbs and refining them into pills/elixirs.

Two pure rules live here, mirroring the rest of ``game/systems``:

* ``GatherSystem`` answers *where* herbs grow and *which* herb a ``gather`` verb
  yields, using the seeded ``RNG`` so a run's harvest is reproducible.
* ``RefineSystem`` owns the recipe graph (``data/refining_recipes.json``): it
  checks inputs and cultivation-realm requirements, consumes them, and produces
  the output item.

Neither system performs I/O or formats player-facing prose; the engine wires
them to the player/inventory and attaches narrative. Recipes reference the
existing item catalogue, so refining reuses the pills/elixirs already shipped,
rather than inventing a parallel item space.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from game.core.constants import EventType


class GatherSystem:
    """Per-location herb tables with a seeded weighted roll."""

    def __init__(self, gathering_data: Optional[Dict[str, Any]] = None) -> None:
        gathering_data = gathering_data or {}
        self._default: List[Dict[str, Any]] = list(gathering_data.get("default", []))
        self._locations: Dict[str, List[Dict[str, Any]]] = {
            str(location_id): list(table)
            for location_id, table in (gathering_data.get("locations") or {}).items()
        }

    def has_gathering(self, location_id: str) -> bool:
        """Return ``True`` when herbs can be gathered at ``location_id``."""
        return str(location_id) in self._locations

    def table_for(self, location_id: str) -> List[Dict[str, Any]]:
        """Return the weighted herb table for a location (falling back to default)."""
        return self._locations.get(str(location_id), self._default)

    def roll(self, location_id: str, rng: Any) -> Optional[str]:
        """Return a single gathered herb id from the location's table, or ``None``."""
        table = self.table_for(location_id)
        if not table:
            return None
        ids = [str(entry.get("item_id")) for entry in table]
        weights = [float(entry.get("weight", 1)) for entry in table]
        return str(rng.weighted_choice(ids, weights))


class RefineSystem:
    """Herb-to-pill recipe graph with input checking and output production.

    Recipes may declare ``minimum_body_realm`` (and optionally
    ``minimum_essence_realm``): refining is gated by the cultivator's actual
    realm, so stronger pills require the corresponding cultivation to brew.
    """

    def __init__(
        self,
        recipes: Optional[List[Dict[str, Any]]] = None,
        body_realms: Optional[Dict[str, Any]] = None,
        essence_realms: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._recipes: Dict[str, Dict[str, Any]] = {
            str(recipe["id"]): dict(recipe)
            for recipe in (recipes or [])
            if recipe.get("id")
        }
        self._body_order = self._realm_orders((body_realms or {}).get("realms", []))
        self._essence_order = self._realm_orders((essence_realms or {}).get("realms", []))

    def recipes(self, player: Any = None) -> List[Dict[str, Any]]:
        """Return every recipe for the UI, annotated with its realm gate.

        When ``player`` is supplied each entry also carries ``available`` so the
        UI can grey out recipes the cultivator is not yet strong enough to brew.
        """
        entries: List[Dict[str, Any]] = []
        for recipe in self._recipes.values():
            entry = {
                "id": recipe.get("id"),
                "display_name": recipe.get("display_name", recipe.get("id")),
                "inputs": dict(recipe.get("inputs", {})),
                "output": dict(recipe.get("output", {})),
                "description": recipe.get("description", ""),
                "minimum_body_realm": recipe.get("minimum_body_realm"),
                "minimum_essence_realm": recipe.get("minimum_essence_realm"),
            }
            if player is not None:
                entry["available"] = not self._realm_failure(player, recipe)
            entries.append(entry)
        return entries

    def get(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """Return a raw recipe definition, or ``None`` if unknown."""
        entry = self._recipes.get(str(recipe_id))
        return dict(entry) if entry is not None else None

    def refine(self, player: Any, recipe_id: str, inventory: Any) -> Dict[str, Any]:
        """Consume a recipe's inputs and produce its output item."""
        recipe = self.get(recipe_id)
        if recipe is None:
            return {"event": EventType.ERROR, "reason": "UNKNOWN_RECIPE", "recipe_id": recipe_id}
        failed = self._realm_failure(player, recipe)
        if failed:
            failed.update({"recipe_id": recipe_id, "event": EventType.ERROR})
            return failed
        inputs = recipe.get("inputs", {})
        missing: Dict[str, int] = {}
        for item_id, quantity in inputs.items():
            needed = int(quantity)
            if int(player.inventory.get(item_id, 0)) < needed:
                missing[item_id] = needed - int(player.inventory.get(item_id, 0))
        if missing:
            return {
                "event": EventType.ERROR,
                "reason": "INSUFFICIENT_RESOURCES",
                "recipe_id": recipe_id,
                "required": {str(item_id): int(quantity) for item_id, quantity in inputs.items()},
                "missing": missing,
                "inventory": dict(player.inventory),
            }
        for item_id, quantity in inputs.items():
            inventory.remove_item(player, item_id, int(quantity))
        output = recipe.get("output", {})
        item_id = str(output.get("item_id", ""))
        count = int(output.get("count", 1))
        inventory.add_item(player, item_id, count)
        return {
            "event": EventType.REFINE_RESULT,
            "recipe_id": recipe_id,
            "name": recipe.get("display_name", recipe_id),
            "item_id": item_id,
            "count": count,
            "inventory_items": inventory.list_inventory(player)["items"],
        }

    # -- realm gating -----------------------------------------------------
    def _realm_failure(self, player: Any, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Return a non-empty error dict when the player's realm is too low."""
        body_realm = recipe.get("minimum_body_realm")
        if body_realm:
            current = self._player_body_realm(player)
            if self._realm_too_low(current, str(body_realm), self._body_order):
                return {
                    "reason": "REALM_TOO_LOW",
                    "track": "body",
                    "required": body_realm,
                    "current": current,
                }
        essence_realm = recipe.get("minimum_essence_realm")
        if essence_realm:
            current = self._player_essence_realm(player)
            if self._realm_too_low(current, str(essence_realm), self._essence_order):
                return {
                    "reason": "REALM_TOO_LOW",
                    "track": "essence",
                    "required": essence_realm,
                    "current": current,
                }
        return {}

    def _player_body_realm(self, player: Any) -> str:
        state = getattr(player, "cultivation_state", None)
        body = getattr(state, "body", None)
        return str(getattr(body, "realm_id", "") or "")

    def _player_essence_realm(self, player: Any) -> str:
        state = getattr(player, "cultivation_state", None)
        essence = getattr(state, "essence", None)
        return str(getattr(essence, "realm_id", "") or "")

    def _realm_too_low(self, current_id: str, required_id: str, orders: Dict[str, int]) -> bool:
        return orders.get(current_id, -1) < orders.get(required_id, 10**9)

    def _realm_orders(self, realms: Iterable[Dict[str, Any]]) -> Dict[str, int]:
        return {str(realm.get("id")): int(realm.get("order", 0)) for realm in realms}
