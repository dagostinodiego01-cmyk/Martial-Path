"""Quest system.

Tracks the player's journal: which quests are active, their objective progress,
and the rewards granted on completion. Quest definitions are injected from
``data/quests.json`` so content stays data-driven with stable IDs.

Objectives are simple counters keyed by an event ``type`` (e.g. ``"defeat"``,
``"breakthrough"``, ``"visit_location"``). The engine notifies the system when
such events occur; the system advances matching objectives and, on completion,
applies rewards through the same player/inventory paths every other system uses.

Quests may also be *chained*: a non-``auto_start`` quest carries a ``requires``
block (prior quest completion, minimum reputation, or a required location) and
activates automatically once those conditions are met. Rewards may grant gold,
exp, reputation, items, technique manuals, or directly teach skills.
It returns structured data only and never formats player-facing text.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from game.core.constants import EventType
from game.models.player import Player
from game.systems.inventory_system import InventorySystem


class QuestSystem:
    """Counter-based quest tracking with data-driven definitions."""

    STATUS_LOCKED = "locked"
    STATUS_ACTIVE = "active"
    STATUS_COMPLETED = "completed"

    def __init__(
        self,
        quests: List[Dict[str, Any]],
        skill_system: Optional[Any] = None,
    ) -> None:
        self._defs: Dict[str, Dict[str, Any]] = {q["id"]: q for q in (quests or [])}
        self._skill_system = skill_system
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

    def check_unlocks(self, player: Player) -> List[str]:
        """Activate any locked quest whose ``requires`` are now met.

        Returns the ids of newly-activated quests. Called automatically after
        every :meth:`notify`; the engine may also call it after out-of-band
        state changes (e.g. reputation gained from dialogue) that never raise a
        notify event.
        """
        unlocked: List[str] = []
        for quest_id, definition in self._defs.items():
            if quest_id in self._state:
                continue  # already active or completed
            if not definition.get("requires"):
                continue  # no gate defined -> stays locked until explicitly unlocked
            if self._requires_met(definition, player):
                self._activate(quest_id)
                unlocked.append(quest_id)
        return unlocked

    def _requires_met(self, definition: Dict[str, Any], player: Player) -> bool:
        """Return whether a locked quest's ``requires`` gate is satisfied."""
        requires = definition.get("requires", {}) or {}
        for completed_id in requires.get("completed", []):
            state = self._state.get(completed_id)
            if state is None or state["status"] != self.STATUS_COMPLETED:
                return False
        min_reputation = requires.get("min_reputation")
        if min_reputation is not None and int(getattr(player, "reputation", 0)) < int(min_reputation):
            return False
        location = requires.get("location")
        if location and getattr(player, "current_location", "") != location:
            return False
        return True

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
        # Completing a quest (or any other notified event) may satisfy the
        # ``requires`` of a chained quest, unlocking it for the same turn.
        self.check_unlocks(player)
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
                    "requires": dict(definition.get("requires", {})),
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
        reputation = int(rewards.get("reputation", 0))
        player.exp += exp
        player.gold += gold
        player.reputation += reputation

        granted_items: Dict[str, int] = {}
        for item_id, count in rewards.get("items", {}).items():
            inventory.add_item(player, item_id, int(count))
            granted_items[item_id] = int(count)
        for manual_id, count in rewards.get("manuals", {}).items():
            inventory.add_item(player, manual_id, int(count))
            granted_items[manual_id] = int(count)

        learned_skills: List[str] = []
        if self._skill_system is not None:
            for skill_id in rewards.get("skills", []):
                result = self._skill_system.learn_skill(player, skill_id, source="quest")
                if result.get("event") == EventType.SKILL_LEARNED:
                    learned_skills.append(skill_id)

        result: Dict[str, Any] = {"exp": exp, "gold": gold, "reputation": reputation, "items": granted_items}
        if learned_skills:
            result["skills"] = learned_skills
        return result

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
