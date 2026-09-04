"""Run lifecycle: starting fate, permadeath, and save/load persistence."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from game.core.constants import ASCENSION_ESSENCE_ORDER, DEFAULT_ORIGIN_ID, EventType, MODE_EXPLORE
from game.core.results import (
    PlayerDiedResult,
    RetiredResult,
    SaveExportedResult,
    SaveImportedResult,
    StartingFateAcceptedResult,
    StartingFateRolledResult,
    UnlockPurchasedResult,
)
from game.models.player import Player
from game.services.cultivation_service import CultivationService
from game.services.meta_service import (
    ASCENSION_REWARD_MULTIPLIER,
    DEATH_REALM_BONUS,
    DEATH_REWARD,
)
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
            "title": self._legacy_title(),
            # D.3: which campaign ending this run earned (None if unfinished).
            "campaign_ending": self._campaign_chronicle_field(),
        }

    def _legacy_title(self) -> Optional[str]:
        """The cosmetic legacy title this run's character carries (C.5)."""
        for unlock_id in self.meta.unlocks():
            node = self.legacy.node(unlock_id)
            if node is not None and node.get("kind") == "title":
                return str(node.get("target_id", ""))
        return None

    def _purchase_unlock(self, unlock_id: str) -> Dict[str, Any]:
        """Buy a legacy-tree unlock with Ancestral Memory (C.5).

        Cross-run: the purchase persists in the meta-save, applies immediately
        to the current run (techniques are learned on the spot), and again on
        every future run's character creation.
        """
        node = self.legacy.node(unlock_id)
        if node is None:
            return {"event": EventType.ERROR, "reason": "UNKNOWN_UNLOCK", "unlock_id": unlock_id}
        gate = self.legacy.can_unlock(unlock_id, self.meta.unlocks())
        if not gate.get("ok"):
            return {"event": EventType.ERROR, "reason": gate.get("reason"), "unlock_id": unlock_id}
        cost = int(node.get("cost", 0))
        if not self.meta.spend_memory(cost):
            return {
                "event": EventType.ERROR,
                "reason": "INSUFFICIENT_MEMORY",
                "unlock_id": unlock_id,
                "cost": cost,
                "ancestral_memory": self.meta.memory(),
            }
        self.meta.add_unlock(unlock_id)
        learned = None
        if node.get("kind") == "technique":
            target = str(node.get("target_id", ""))
            result = self.techniques.learn_skill(self.player, target, source="legacy")
            if result.get("event") == EventType.SKILL_LEARNED:
                learned = target
        return UnlockPurchasedResult(
            unlock_id=str(node["id"]),
            kind=str(node.get("kind", "")),
            target_id=str(node.get("target_id", "")),
            cost=cost,
            ancestral_memory=self.meta.memory(),
            player_message=f"Legacy awakened: {node.get('id', unlock_id)} is now part of your inheritance.",
        ).to_dict() | ({"learned_skill": learned} if learned else {})

    def _apply_legacy_unlocks(self) -> None:
        """Apply purchased legacy unlocks to a fresh character (C.5).

        Runs after origin application: technique unlocks teach their skill
        (learning applies growth passives properly); sect unlocks are data the
        sect system already accepts (join gates stay); title unlocks surface in
        views/summaries.
        """
        for unlock_id in self.meta.unlocks():
            node = self.legacy.node(unlock_id)
            if node is None:
                continue
            kind = node.get("kind")
            target = str(node.get("target_id", ""))
            if kind == "technique" and target:
                self.techniques.learn_skill(self.player, target, source="legacy")

    # -- retirement / ascension (C.7) -------------------------------------
    def _can_retire(self) -> bool:
        """True when the player has crossed the ascension threshold."""
        essence = self.player.cultivation_state.essence
        essence_order = self._essence_realm_orders.get(essence.realm_id, 0)
        return essence_order >= ASCENSION_ESSENCE_ORDER

    def _retire(self) -> Dict[str, Any]:
        """Ascend: end the run as a *win* and bank the large legacy reward.

        Retirement is the campaign's ending beat (C.7): reaching the ascension
        point lets the player retire deliberately. The reward is the death
        reward scaled by ``ASCENSION_REWARD_MULTIPLIER`` -- winning beats dying
        -- and the chronicle records the run as ``ascended``.
        """
        if not self._can_retire():
            return {
                "event": EventType.ERROR,
                "reason": "ASCENSION_NOT_REACHED",
                "required_essence_order": ASCENSION_ESSENCE_ORDER,
            }
        self._running = False
        self._mode = MODE_EXPLORE
        self._current_enemy = None
        summary = self._run_summary("ascended")
        reward = (DEATH_REWARD + DEATH_REALM_BONUS * int(summary["realm_rank"])) * ASCENSION_REWARD_MULTIPLIER
        self.meta.add_memory(reward)
        self.meta.mark_retired()
        self.meta.record_run(self._chronicle_entry("ascended"))
        result = RetiredResult(
            cause="ascended",
            age_years=round(float(self.player.age_years), 1),
            player_message=(
                "You step beyond the sky of this world. The run is won -- your "
                "legacy banks and the endless road opens for those who follow."
            ),
            reward=reward,
            ancestral_memory=self.meta.memory(),
            summary=summary,
        ).to_dict()
        result["narrative"] = self.narrative.describe_death(
            "your aura departs the world and you rise past the vault of heaven",
            result["age_years"],
            self.lifespan.season(self.player),
        )
        return result

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
            "endless": self._endless,
            "world_state": self._world_state,
            "campaign_complete": self._campaign_complete,
            "campaign_ending_id": self._campaign_ending_id,
            "endless_depth": self._endless_depth,
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
        self._note_arrival(self.player.current_location)
        self.cultivation_service = CultivationService({"player": self.player}, self.cultivation)
        self.quests.import_state(data.get("quests", {}))
        self._ng_plus = max(0, int(data.get("ng_plus", 0)))
        self._ironman = bool(data.get("ironman", False))
        self._hardcore = bool(data.get("hardcore", True))
        self._endless = bool(data.get("endless", False))
        # D.3/D.5: restore campaign + endless-road progress.
        self._campaign_complete = bool(data.get("campaign_complete", False))
        self._campaign_ending_id = str(data.get("campaign_ending_id", "") or "")
        self._endless_depth = max(0, int(data.get("endless_depth", 0)))
        # Living world (E.1-E.5): restore the evolved world state so a loaded
        # save continues the same living world (rumors, sect power, market).
        world_state = data.get("world_state")
        if isinstance(world_state, dict) and world_state:
            self._world_state = world_state
            market = world_state.get("market", {})
            try:
                self.shops.set_market_multiplier(float(market.get("price_multiplier", 1.0)))
            except (TypeError, ValueError):
                pass
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
