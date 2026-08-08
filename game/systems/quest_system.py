"""Quest system.

Tracks the player's journal: which quests are active, their objective progress,
and the rewards granted on completion. Quest definitions are injected from
``data/quests.json`` so content stays data-driven with stable IDs.

Objectives are simple counters keyed by an event ``type`` (e.g. ``"defeat"``,
``"breakthrough"``, ``"visit_location"``). The engine notifies the system when
such events occur; the system advances matching objectives and, on completion,
applies rewards through the same player/inventory paths every other system uses.
It returns structured data only and never formats player-facing text.
"""
from __future__ import annotations

from typing import Any, Dict, List

from game.models.player import Player
from game.systems.inventory_system import InventorySystem


class QuestSystem:
    """Counter-based quest tracking with data-driven definitions."""

    STATUS_LOCKED = "locked"
    STATUS_ACTIVE = "active"
    STATUS_COMPLETED = "completed"

    def __init__(self, quests: List[Dict[str, Any]]) -> None:
        self._defs: Dict[str, Dict[str, Any]] = {q["id"]: q for q in (quests or [])}
        # Per-quest mutable state: status + one counter per objective index.
        self._state: Dict[str, Dict[str, Any]] = {}
        for quest_id, definition in self._defs.items():
            if definition.get("auto_start", False):
                self._activate(quest_id)

    def _activate(self, quest_id: str) -> None:
        definition = self._defs[quest_id]
        self._state[quest_id] = {
            "status": self.STATUS_ACTIVE,
            "progress": [0 for _ in definition.get("objectives", [])],
        }

    def notify(
        self,
        event_type: str,
        player: Player,
        inventory: InventorySystem,
        target: str = "any",
    ) -> List[Dict[str, Any]]:
        """Advance active objectives matching ``event_type`` and apply rewards.

        Returns a list of completion descriptors for any quest finished by this
        event, so the caller can surface them to the UI/log.
        """
        completed: List[Dict[str, Any]] = []
        for quest_id, state in self._state.items():
            if state["status"] != self.STATUS_ACTIVE:
                continue
            definition = self._defs[quest_id]
            changed = False
            for index, objective in enumerate(definition.get("objectives", [])):
                if objective.get("type") != event_type:
                    continue
                obj_target = objective.get("target", "any")
                if obj_target not in ("any", target):
                    continue
                required = int(objective.get("count", 1))
                if state["progress"][index] < required:
                    state["progress"][index] += 1
                    changed = True
            if changed and self._all_objectives_met(quest_id):
                rewards = self._grant_rewards(quest_id, player, inventory)
                state["status"] = self.STATUS_COMPLETED
                completed.append(
                    {
                        "id": quest_id,
                        "title": definition.get("title", quest_id),
                        "rewards": rewards,
                    }
                )
        return completed

    def snapshot(self) -> List[Dict[str, Any]]:
        """Return a UI-safe list of every known quest and its progress."""
        entries: List[Dict[str, Any]] = []
        for quest_id, definition in self._defs.items():
            state = self._state.get(quest_id)
            status = state["status"] if state else self.STATUS_LOCKED
            objectives = []
            for index, objective in enumerate(definition.get("objectives", [])):
                current = state["progress"][index] if state else 0
                objectives.append(
                    {
                        "text": objective.get("text", objective.get("type", "")),
                        "current": current,
                        "required": int(objective.get("count", 1)),
                    }
                )
            entries.append(
                {
                    "id": quest_id,
                    "title": definition.get("title", quest_id),
                    "description": definition.get("description", ""),
                    "status": status,
                    "objectives": objectives,
                }
            )
        return entries

    def _all_objectives_met(self, quest_id: str) -> bool:
        definition = self._defs[quest_id]
        state = self._state[quest_id]
        for index, objective in enumerate(definition.get("objectives", [])):
            if state["progress"][index] < int(objective.get("count", 1)):
                return False
        return True

    def _grant_rewards(
        self, quest_id: str, player: Player, inventory: InventorySystem
    ) -> Dict[str, Any]:
        rewards = self._defs[quest_id].get("rewards", {})
        exp = int(rewards.get("exp", 0))
        gold = int(rewards.get("gold", 0))
        player.exp += exp
        player.gold += gold
        granted_items: Dict[str, int] = {}
        for item_id, count in rewards.get("items", {}).items():
            inventory.add_item(player, item_id, int(count))
            granted_items[item_id] = int(count)
        return {"exp": exp, "gold": gold, "items": granted_items}

    def export_state(self) -> Dict[str, Any]:
        """Return the raw quest progress for saving (not a UI view)."""
        return {
            quest_id: {"status": state["status"], "progress": list(state["progress"])}
            for quest_id, state in self._state.items()
        }

    def import_state(self, saved: Dict[str, Any]) -> None:
        """Restore quest progress from a saved snapshot, validated against defs."""
        for quest_id, state in (saved or {}).items():
            if quest_id not in self._defs or not isinstance(state, dict):
                continue
            objectives = self._defs[quest_id].get("objectives", [])
            saved_progress = state.get("progress", [])
            progress = [
                int(saved_progress[i]) if i < len(saved_progress) else 0
                for i in range(len(objectives))
            ]
            self._state[quest_id] = {
                "status": state.get("status", self.STATUS_ACTIVE),
                "progress": progress,
            }
