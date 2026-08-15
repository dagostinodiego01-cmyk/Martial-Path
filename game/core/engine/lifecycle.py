"""Run lifecycle: starting fate, permadeath, and save/load persistence."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from game.core.constants import DEFAULT_ORIGIN_ID, EventType, MODE_EXPLORE
from game.core.results import (
    PlayerDiedResult,
    SaveExportedResult,
    SaveImportedResult,
    StartingFateAcceptedResult,
    StartingFateRolledResult,
)
from game.models.player import Player
from game.services.cultivation_service import CultivationService
from game.services.meta_service import DEATH_REALM_BONUS, DEATH_REWARD
from game.services.save_service import SAVE_VERSION, SaveError


class LifecycleMixin:
    """The start (fate) and end (death/retire) of a run, plus save persistence."""

    def _die_of_old_age(self, last_event: Dict[str, Any]) -> Dict[str, Any]:
        """End the run when the player's lifespan is exhausted (permanent death)."""
        return self._die("old_age", last_event)

    def _die(self, cause: str, last_event: Dict[str, Any]) -> Dict[str, Any]:
        """End the run permanently: bank Ancestral Memory and record the chronicle.

        Used for every terminal death (old age, hardcore combat defeat). The run
        is over -- ``_running`` flips off so further actions are refused -- and
        the meta-save is updated so the next run begins with the legacy accrued.
        """
        self._running = False
        self._mode = MODE_EXPLORE
        self._current_enemy = None
        summary = self._run_summary(cause)
        self.meta.add_memory(DEATH_REWARD + DEATH_REALM_BONUS * int(summary["realm_rank"]))
        self.meta.record_run(self._chronicle_entry(cause))
        messages = {
            "old_age": "Your lifespan is exhausted. The dao you chased slips away as your body returns to dust.",
            "combat": "Your strength fails and the world goes dark. This run is over.",
        }
        result = PlayerDiedResult(
            cause=cause,
            age_years=round(float(self.player.age_years), 1),
            player_message=messages.get(cause, "Your journey ends."),
            last_event=last_event,
        ).to_dict()
        result["summary"] = summary
        result["ancestral_memory"] = self.meta.memory()
        result["narrative"] = self.narrative.describe_death(
            "your lifespan runs dry and your body crumbles to dust" if cause == "old_age" else "you fall and do not rise",
            result["age_years"],
            self.lifespan.season(self.player),
        )
        return result

    def _run_summary(self, cause: str) -> Dict[str, Any]:
        """Build the end-of-run summary: realms reached, dao, and achievements."""
        body_id = self.player.cultivation_state.body.realm_id
        essence_id = self.player.cultivation_state.essence.realm_id
        return {
            "cause": cause,
            "age_years": round(float(self.player.age_years), 1),
            "body_realm": self._body_realm_names.get(body_id, body_id),
            "essence_realm": self._essence_realm_names.get(essence_id, "") if essence_id else "",
            "realm_rank": self.dao.player_rank(self.player),
            "dao": self.dao.dao_name(self.player.dao_id),
            "path": self.player.path,
            "origin": self._origin_id,
            "morality": self.morality.band_id(self.player.morality),
            "reputation": self.player.reputation,
            "quests_completed": self.quests.completed_count(),
            "gold": self.player.gold,
        }

    def _chronicle_entry(self, cause: str) -> Dict[str, Any]:
        """Build the graveyard record for this run."""
        body_id = self.player.cultivation_state.body.realm_id
        essence_id = self.player.cultivation_state.essence.realm_id
        return {
            "seed": self._seed,
            "origin": self._origin_id,
            "dao": self.player.dao_id,
            "cause": cause,
            "age_years": round(float(self.player.age_years), 1),
            "peak_body_realm": self._body_realm_names.get(body_id, body_id),
            "peak_essence_realm": self._essence_realm_names.get(essence_id, "") if essence_id else "",
            "path": self.player.path,
        }

    # -- starting fate ----------------------------------------------------
    def _roll_starting_fate(self) -> Dict[str, Any]:
        """Roll and store a pending starting fate for the current new game."""
        self._pending_fate = self.starting_fate.roll()
        self._fate_accepted = False
        return self._pending_fate

    def _assign_new_game_fate(self) -> None:
        """Roll and immediately apply starting talents for a playable new game."""
        fate = self.starting_fate.roll()
        self.player.martial_talent_id = str(fate["martial_talent_id"])
        self.player.body_talent_id = str(fate["body_talent_id"])
        self._pending_fate = None
        self._fate_accepted = True

    def _roll_starting_fate_result(self) -> Dict[str, Any]:
        """Return the current pending fate, rolling one if none exists yet."""
        if self._fate_accepted:
            return {"event": EventType.ERROR, "reason": "FATE_ALREADY_ACCEPTED"}
        fate = self._pending_fate or self._roll_starting_fate()
        # The rolled "fate" is the character's Martial and Body Talents. The
        # result keeps the legacy spiritual_root/physique field names so existing
        # text frontends keep working; the values are the talent views.
        return StartingFateRolledResult(
            spiritual_root_id=str(fate["martial_talent_id"]),
            physique_id=str(fate["body_talent_id"]),
            spiritual_root=dict(fate["martial_talent"]),
            physique=dict(fate["body_talent"]),
            requires_fate_acceptance=True,
            player_message="Your starting talents have been revealed.",
        ).to_dict()

    def _accept_starting_fate(self) -> Dict[str, Any]:
        """Apply the pending fate to the player and open normal gameplay."""
        if self._fate_accepted:
            return {"event": EventType.ERROR, "reason": "FATE_ALREADY_ACCEPTED"}
        fate = self._pending_fate or self._roll_starting_fate()
        self.player.martial_talent_id = str(fate["martial_talent_id"])
        self.player.body_talent_id = str(fate["body_talent_id"])
        self._pending_fate = None
        self._fate_accepted = True
        return StartingFateAcceptedResult(
            success=True,
            spiritual_root_id=self.player.martial_talent_id,
            physique_id=self.player.body_talent_id,
            spiritual_root=self.starting_fate.martial_talent_view(self.player.martial_talent_id),
            physique=self.starting_fate.body_talent_view(self.player.body_talent_id),
            player_message="You accept your starting talents and step onto the path.",
        ).to_dict()

    def _pending_fate_view(self) -> Optional[Dict[str, Any]]:
        if not self._pending_fate:
            return None
        return {
            "martial_talent_id": self._pending_fate["martial_talent_id"],
            "body_talent_id": self._pending_fate["body_talent_id"],
            "martial_talent": dict(self._pending_fate["martial_talent"]),
            "body_talent": dict(self._pending_fate["body_talent"]),
        }

    def _bind_equipment_modifiers(self) -> None:
        setattr(self.player, "equipment_modifiers", lambda: self.equipment.aggregate_modifiers(self.player))

    # -- persistence -----------------------------------------------------
    def _session_snapshot(self) -> Dict[str, Any]:
        return {
            "player": self.player.to_save_dict(),
            "quests": self.quests.export_state(),
            "ng_plus": self._ng_plus,
            "ironman": self._ironman,
            "hardcore": self._hardcore,
        }

    def save_game(self, slot: str = "default") -> Dict[str, Any]:
        """Persist the current session to a named save slot."""
        try:
            self.saves.write(slot or "default", self._session_snapshot())
        except SaveError as exc:
            return {"event": EventType.SAVE_RESULT, "success": False, "reason": exc.code, "slot": slot}
        return {"event": EventType.SAVE_RESULT, "success": True, "slot": slot or "default"}

    def _export_save(self) -> Dict[str, Any]:
        """Return the current session as a portable JSON string (cloud substitute)."""
        snapshot = self._session_snapshot()
        snapshot["version"] = SAVE_VERSION
        payload = json.dumps(snapshot, sort_keys=True)
        return SaveExportedResult(
            payload=payload,
            player_message="Your journey has been transcribed into a portable record.",
        ).to_dict()

    def _import_save(self, payload: str, slot: str) -> Dict[str, Any]:
        """Restore a session from a portable JSON string into ``slot``."""
        if not payload:
            return {"event": EventType.ERROR, "reason": "IMPORT_EMPTY"}
        try:
            data = json.loads(payload)
        except (ValueError, TypeError):
            return {"event": EventType.ERROR, "reason": "IMPORT_INVALID"}
        if not isinstance(data, dict) or "player" not in data:
            return {"event": EventType.ERROR, "reason": "IMPORT_INVALID"}
        try:
            self.saves.write(slot or "default", data)
        except SaveError as exc:
            return {"event": EventType.ERROR, "reason": exc.code}
        loaded = self.load_game(slot or "default")
        return SaveImportedResult(
            success=bool(loaded.get("success")),
            slot=slot or "default",
            player_message="Your journey has been restored from the portable record.",
        ).to_dict()

    def load_game(self, slot: str = "default") -> Dict[str, Any]:
        """Restore a session from a named save slot, replacing current state."""
        if self._ironman:
            return {"event": EventType.LOAD_RESULT, "success": False, "reason": "IRONMAN_MODE", "slot": slot}
        try:
            data = self.saves.read(slot or "default")
        except SaveError as exc:
            return {"event": EventType.LOAD_RESULT, "success": False, "reason": exc.code, "slot": slot}
        self.player = Player.from_save_dict(data.get("player", {}))
        self._bind_equipment_modifiers()
        self.cultivation_service = CultivationService({"player": self.player}, self.cultivation)
        self.quests.import_state(data.get("quests", {}))
        self._ng_plus = max(0, int(data.get("ng_plus", 0)))
        self._ironman = bool(data.get("ironman", False))
        self._hardcore = bool(data.get("hardcore", True))
        self._origin_id = str(self.player.origin_id or DEFAULT_ORIGIN_ID)
        self._mode = MODE_EXPLORE
        self._current_enemy = None
        self._cooldowns = {}
        self._pending_fate = None
        self._fate_accepted = True
        return {
            "event": EventType.LOAD_RESULT,
            "success": True,
            "slot": slot or "default",
            "player": self._player_view(),
        }
