"""Relationship system.

Manages per-NPC relationship state stored as ``{npc_id: {variables...}}``. Per the
NPC/relationship rules, an NPC is described by *multiple* emotional variables --
relationship_score, trust, fear, respect, resentment, loyalty, suspicion,
debt_to_player -- plus memory of the player's actions and a faction opinion.

The current interaction *tier* (``hostile`` / ``neutral`` / ``friendly`` /
``trusted``, matching the ``relationship_behavior`` keys in ``characters.json``) is
derived from ``relationship_score``, but callers are expected to consult the other
variables too rather than relying on the tier alone.

Data-driven from ``data/relationships.json``. Pure logic: the caller owns where the
store is persisted (the player sheet / save file); this system only reads and
mutates the passed-in store and returns structured results.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from game.utils.data_loader import load_json


class RelationshipSystem:
    """Creates, adjusts, and interprets per-NPC relationship state."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self._config = config or load_json("relationships.json")
        self._variables: Dict[str, Dict[str, int]] = dict(self._config.get("variables", {}))
        self._tiers: List[Dict[str, Any]] = list(self._config.get("tiers", []))

    def _default_state(self) -> Dict[str, Any]:
        state: Dict[str, Any] = {
            name: int(spec.get("default", 0)) for name, spec in self._variables.items()
        }
        state["faction_opinion"] = 0
        state["known_player_actions"] = []
        state["personal_memory_flags"] = {}
        return state

    def ensure(self, store: Dict[str, Any], npc_id: str) -> Dict[str, Any]:
        """Return the NPC's state, creating neutral defaults if it is missing.

        NPCs never start trusting the player: all emotional variables default to
        their configured baseline (zero) until interactions change them.
        """
        if npc_id not in store:
            store[npc_id] = self._default_state()
        else:
            state = store[npc_id]
            for name, spec in self._variables.items():
                state.setdefault(name, int(spec.get("default", 0)))
            state.setdefault("faction_opinion", 0)
            state.setdefault("known_player_actions", [])
            state.setdefault("personal_memory_flags", {})
        return store[npc_id]

    def _clamp_variable(self, name: str, value: int) -> int:
        spec = self._variables.get(name)
        if spec is None:
            return int(value)
        return max(int(spec.get("min", 0)), min(int(spec.get("max", 100)), int(value)))

    def tier_for(self, score: int) -> str:
        """Return the interaction tier id a relationship_score falls into."""
        for tier in self._tiers:
            if int(tier["min"]) <= int(score) <= int(tier["max"]):
                return str(tier["id"])
        return str(self._tiers[0]["id"]) if self._tiers else "neutral"

    def adjust(self, store: Dict[str, Any], npc_id: str, changes: Dict[str, int]) -> Dict[str, Any]:
        """Apply clamped deltas to one NPC's emotional variables."""
        state = self.ensure(store, npc_id)
        applied: Dict[str, int] = {}
        for name, delta in changes.items():
            if name not in self._variables:
                continue
            before = int(state.get(name, self._variables[name].get("default", 0)))
            after = self._clamp_variable(name, before + int(delta))
            state[name] = after
            applied[name] = after - before
        return self.get(store, npc_id, applied=applied)

    def remember(
        self,
        store: Dict[str, Any],
        npc_id: str,
        action: str,
        flag: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record a notable player action (and optional memory flag) for an NPC."""
        state = self.ensure(store, npc_id)
        if action and action not in state["known_player_actions"]:
            state["known_player_actions"].append(action)
        if flag:
            state["personal_memory_flags"][flag] = True
        return self.get(store, npc_id)

    def get(
        self,
        store: Dict[str, Any],
        npc_id: str,
        applied: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """Return the NPC's state plus its derived interaction tier."""
        state = self.ensure(store, npc_id)
        result: Dict[str, Any] = {
            "npc_id": npc_id,
            "tier": self.tier_for(int(state.get("relationship_score", 0))),
            "state": dict(state),
        }
        if applied is not None:
            result["applied"] = applied
        return result
