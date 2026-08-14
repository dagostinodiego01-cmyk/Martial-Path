"""Lifespan and ageing rules.

Pure and data-driven: computes a character's current maximum lifespan from their
Essence Gathering realm (pre-essence characters use the mortal base), advances
age by a per-action time cost, and reports remaining years / expiry. The system
owns no player state and performs no I/O; the engine decides when to age the
player and what to do on death.

A maximum lifespan of ``None`` means the realm is effectively immortal, so the
character can never die of old age.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from game.models.player import Player


class LifespanSystem:
    """Compute maximum lifespan, advance age, and detect death by old age."""

    def __init__(self, essence_realms: Dict[str, Any], config: Dict[str, Any]) -> None:
        self._lifespan_by_realm = {
            realm["id"]: realm.get("max_lifespan_years")
            for realm in essence_realms.get("realms", [])
            if "id" in realm
        }
        lifespan_config = config.get("lifespan", {})
        self._starting_age = float(lifespan_config.get("starting_age_years", 12))
        self._mortal_base = float(lifespan_config.get("mortal_base_lifespan_years", 100))
        self._time_costs = dict(lifespan_config.get("time_costs", {}))

    def current_max_lifespan(self, player: Player, essence_unlocked: bool) -> Optional[float]:
        """Return the current maximum lifespan in years, or ``None`` if immortal.

        Lifespan follows the Essence Gathering realm. Before Essence cultivation
        is unlocked the character is still mortal, so the mortal base applies.
        ``lifespan`` passive techniques add a flat bonus on top of the
        realm-derived value (never applied to an immortal realm).
        """
        bonus = float(getattr(player, "lifespan_bonus_years", 0.0))
        if not essence_unlocked:
            return self._mortal_base + bonus
        realm_id = player.cultivation_state.essence.realm_id
        if realm_id not in self._lifespan_by_realm:
            return self._mortal_base + bonus
        value = self._lifespan_by_realm[realm_id]
        return None if value is None else float(value) + bonus

    def time_cost(self, action_key: str) -> float:
        """Return the age (in years) a given action consumes."""
        return float(self._time_costs.get(action_key, 0.0))

    def advance_age(self, player: Player, action_key: str) -> float:
        """Advance the player's age by the action's time cost; return years added."""
        cost = self.time_cost(action_key)
        if cost:
            player.age_years = round(float(player.age_years) + cost, 4)
        return cost

    def remaining_years(self, player: Player, essence_unlocked: bool) -> Optional[float]:
        """Return years left before old-age death, or ``None`` when immortal."""
        max_lifespan = self.current_max_lifespan(player, essence_unlocked)
        if max_lifespan is None:
            return None
        return max(0.0, round(max_lifespan - float(player.age_years), 2))

    def is_expired(self, player: Player, essence_unlocked: bool) -> bool:
        """Return ``True`` when the player has reached their maximum lifespan."""
        max_lifespan = self.current_max_lifespan(player, essence_unlocked)
        return max_lifespan is not None and float(player.age_years) >= max_lifespan

    def elapsed_years(self, player: Player) -> int:
        """Return whole years elapsed since the character began (spawn = year 0)."""
        return max(0, int(float(player.age_years) - self._starting_age))

    def lifespan_view(self, player: Player, essence_unlocked: bool) -> Dict[str, Any]:
        """Return a UI-safe lifespan snapshot (read-only)."""
        max_lifespan = self.current_max_lifespan(player, essence_unlocked)
        remaining = self.remaining_years(player, essence_unlocked)
        return {
            "age_years": round(float(player.age_years), 1),
            "year": self.elapsed_years(player),
            "max_lifespan_years": None if max_lifespan is None else int(max_lifespan),
            "remaining_years": None if remaining is None else round(remaining, 1),
            "immortal": max_lifespan is None,
            "display": self._format(float(player.age_years), max_lifespan),
        }

    @staticmethod
    def _format(age: float, max_lifespan: Optional[float]) -> str:
        if max_lifespan is None:
            return f"Age {int(age)} (immortal)"
        return f"Age {int(age)} / {int(max_lifespan):,} years"
