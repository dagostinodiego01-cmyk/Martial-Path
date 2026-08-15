"""Cultivation, talents, closed-door seclusion, and time advancement."""
from __future__ import annotations

from typing import Any, Dict

from game.core.constants import EventType
from game.core.results import (
    ClosedDoorResult,
    TalentUpgradedResult,
    TalentsResult,
    TechniquesResult,
)


class ProgressionMixin:
    """The verbs that grow the cultivator and advance the calendar."""

    def _techniques(self) -> Dict[str, Any]:
        """Return the player's known techniques (active + passive)."""
        return TechniquesResult(skills=self.get_known_skills()).to_dict()

    def _talents(self) -> Dict[str, Any]:
        """Return the player's Martial/Body talents and their upgrade paths."""
        return TalentsResult(
            martial_talent=self.starting_fate.martial_talent_view(self.player.martial_talent_id),
            body_talent=self.starting_fate.body_talent_view(self.player.body_talent_id),
            martial_upgrades=self.starting_fate.upgrade_options_view("martial", self.player.martial_talent_id),
            body_upgrades=self.starting_fate.upgrade_options_view("body", self.player.body_talent_id),
        ).to_dict()

    def _upgrade_talent(self, track: str, target_id: str) -> Dict[str, Any]:
        """Upgrade a Martial or Body talent to the next grade, spending its cost."""
        if track not in ("martial", "body"):
            return {"event": EventType.ERROR, "reason": "INVALID_TALENT_TRACK", "track": track}
        current_id = self.player.martial_talent_id if track == "martial" else self.player.body_talent_id
        options = self.starting_fate.upgrade_options_view(track, current_id)
        target = next((option for option in options if option.get("target_id") == target_id), None)
        if target is None:
            return {"event": EventType.ERROR, "reason": "INVALID_UPGRADE_TARGET", "target_id": target_id}
        cost = target.get("cost") or {}
        missing = {}
        for item_id, quantity in cost.items():
            needed = int(quantity)
            if int(self.player.inventory.get(item_id, 0)) < needed:
                missing[item_id] = needed - int(self.player.inventory.get(item_id, 0))
        if missing:
            return {
                "event": EventType.ERROR,
                "reason": "INSUFFICIENT_RESOURCES",
                "required": {str(item_id): int(quantity) for item_id, quantity in cost.items()},
                "missing": missing,
                "inventory": dict(self.player.inventory),
            }
        for item_id, quantity in cost.items():
            self.inventory.remove_item(self.player, item_id, int(quantity))
        if track == "martial":
            self.player.martial_talent_id = target_id
        else:
            self.player.body_talent_id = target_id
        first_resource = next(iter(cost), "")
        return TalentUpgradedResult(
            track=track,
            talent_id=target_id,
            display_name=str(target.get("target_name", target_id)),
            player_message=f"Your {track} talent advances to {target.get('target_name', target_id)}.",
            wallet={first_resource: int(self.player.inventory.get(first_resource, 0))},
        ).to_dict()

    def _closed_door(self, years: Any) -> Dict[str, Any]:
        """Deliberately cultivate in seclusion for ``years``, ageing accordingly."""
        config = self._cultivation_config.get("closed_door", {})
        options = config.get("options", [])
        chosen = None
        for option in options:
            if isinstance(option, dict) and option.get("years") == years:
                chosen = option
                break
        if chosen is None:
            return {"event": EventType.ERROR, "reason": "INVALID_CLOSED_DOOR_YEARS", "years": years}
        gain = float(chosen.get("progress_gain", 0.0))
        body = self.player.cultivation_state.body
        body.progress = round(float(body.progress) + gain, 2)
        self.player.progress = body.progress
        # A deliberate seclusion ages the player by exactly the chosen years.
        self.player.age_years = round(float(self.player.age_years) + float(years), 4)
        # A multi-year seclusion restores the body to full vigour.
        self.player.heal(self.player.max_hp)
        self.player.restore_qi(self.player.max_qi)
        essence_unlocked = self.cultivation.is_essence_unlocked(self.player)
        lifespan = self.lifespan.lifespan_view(self.player, essence_unlocked)
        result = ClosedDoorResult(
            years=float(years),
            progress_gained=gain,
            progress=body.progress,
            player_message=f"You seclude yourself for {years} year(s), and your body's foundation deepens.",
            lifespan=lifespan,
        ).to_dict()
        if self.lifespan.is_expired(self.player, essence_unlocked):
            return self._die_of_old_age(result)
        return result

    def _after_breakthrough(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Notify quests on a successful breakthrough and attach narrative prose."""
        if result.get("success"):
            updates = self.quests.notify("breakthrough", self.player, self.inventory)
            if updates:
                result["quest_updates"] = updates
        result["narrative"] = self.narrative.describe_breakthrough(
            bool(result.get("success")),
            str(result.get("cultivation", "")),
            self.lifespan.season(self.player),
        )
        return result

    def _advance_day_after(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Advance the minimal backend day after successful recovery actions."""
        if result.get("event") != EventType.ERROR:
            self.player.current_day += 1
            result["current_day"] = self.player.current_day
        return result

    def _advance_time_after(self, result: Dict[str, Any], action_key: str) -> Dict[str, Any]:
        """Age the player by an action's time cost and enforce lifespan limits."""
        if result.get("event") == EventType.ERROR:
            return result
        essence_unlocked = self.cultivation.is_essence_unlocked(self.player)
        self.lifespan.advance_age(self.player, action_key, essence_unlocked)
        result["lifespan"] = self.lifespan.lifespan_view(self.player, essence_unlocked)
        if self.lifespan.is_expired(self.player, essence_unlocked):
            return self._die_of_old_age(result)
        return result
