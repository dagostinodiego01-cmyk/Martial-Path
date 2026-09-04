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
        # D.4 faction campaigns: ``path`` lists the sect ids (or display paths)
        # whose storyline the quest belongs to; ``path_any`` accepts any of them.
        # ``path`` as a bare string is shorthand for a one-element list.
        faction_paths = requires.get("path_any") or requires.get("path")
        if faction_paths:
            if isinstance(faction_paths, str):
                faction_paths = [faction_paths]
            current_path = str(getattr(player, "path", ""))
            if current_path not in {str(entry) for entry in faction_paths}:
                return False
        # Morality branching: a campaign branch may demand a saint (>= min) or
        # a devil (<= max). Player morality starts at 0.
        min_morality = requires.get("min_morality")
        if min_morality is not None and int(getattr(player, "morality", 0)) < int(min_morality):
            return False
        max_morality = requires.get("max_morality")
        if max_morality is not None and int(getattr(player, "morality", 0)) > int(max_morality):
            return False
        return True

    def _sync_state_objectives(self, player: Player) -> None:
        """Advance state-evaluated objectives of active quests (D.4 polish).

        Some objectives are facts about the player rather than events: e.g. a
        campaign act that opens with a sect bond is satisfied by an *existing*
        membership (``player.path`` is set), not only by a fresh join. Called
        alongside ``check_unlocks`` so a quest activated after the fact still
        sees the current state. Returns nothing; completions surface through
        the normal notify path on the next matching event, or immediately via
        :meth:`state_completions`.
        """
        for quest_id, state in self._state.items():
            if state["status"] != self.STATUS_ACTIVE:
                continue
            definition = self._defs[quest_id]
            for index, objective in enumerate(definition.get("objectives", [])):
                if objective.get("type") != "join_sect":
                    continue
                required = int(objective.get("count", 1))
                if state["progress"][index] < required and str(getattr(player, "path", "")) not in ("", "Unassigned"):
                    state["progress"][index] = required

    def state_completions(self, player: Player, inventory: InventorySystem) -> List[Dict[str, Any]]:
        """Complete state-satisfied quests and return their completion records."""
        self._sync_state_objectives(player)
        completed: List[Dict[str, Any]] = []
        for quest_id, state in self._state.items():
            if state["status"] != self.STATUS_ACTIVE:
                continue
            if self._all_objectives_met(quest_id):
                rewards = self._grant_rewards(quest_id, player, inventory)
                state["status"] = self.STATUS_COMPLETED
                completed.append(
                    {
                        "id": quest_id,
                        "title": self._defs[quest_id].get("title", quest_id),
                        "rewards": rewards,
                    }
                )
        if completed:
            self.check_unlocks(player)
        return completed

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
                    "chain": str(definition.get("chain", "")),
                }
            )
        return entries

    def completed_count(self) -> int:
        """Return how many quests have been completed (used by the run summary)."""
        return sum(
            1 for state in self._state.values() if state.get("status") == self.STATUS_COMPLETED
        )

    def objective_active(self, event_type: str) -> bool:
        """Return ``True`` when any active quest has an objective of ``event_type``."""
        return self._any_objective_with(event_type, self.STATUS_ACTIVE)

    def objective_completed(self, event_type: str) -> bool:
        """Return ``True`` when a quest with an ``event_type`` objective is done."""
        return self._any_objective_with(event_type, self.STATUS_COMPLETED)

    def _any_objective_with(self, event_type: str, status: str) -> bool:
        for quest_id, state in self._state.items():
            if state.get("status") != status:
                continue
            for objective in self._defs.get(quest_id, {}).get("objectives", []):
                if objective.get("type") == event_type:
                    return True
        return False

    def act_end(self, quest_id: str) -> str:
        """Return the campaign act this quest concludes (``""`` if none)."""
        return str(self._defs.get(quest_id, {}).get("act_end", ""))

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
        morality = int(rewards.get("morality", 0))
        player.exp += exp
        player.gold += gold
        player.reputation += reputation
        # D.4: branch quests shape the player's morality (saint/devil axis).
        player.morality += morality

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
        if morality:
            result["morality"] = morality
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
