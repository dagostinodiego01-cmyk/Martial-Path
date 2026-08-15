"""Action routing: the public ``process_action`` contract and dispatch tables."""
from __future__ import annotations

from typing import Any, Dict

from game.core.constants import Action, EventType, MODE_COMBAT
from game.core.results import HelpResult, QuitResult


class DispatchMixin:
    """Routes a structured action to the right handler for the current mode."""

    # -- public engine contract ------------------------------------------
    def process_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Process a structured command and return a structured result."""
        if not isinstance(action, dict):
            return {"event": EventType.ERROR, "reason": "MALFORMED_ACTION"}

        name = action.get("action", Action.UNKNOWN)

        # Informational actions (status/inventory/help/quit) never consume a turn
        # and behave identically in every mode, so they are resolved first.
        info_handler = self._info_dispatch.get(name)
        if info_handler is not None:
            return info_handler(action)

        if name == Action.ROLL_STARTING_FATE:
            return self._roll_starting_fate_result()
        if name == Action.ACCEPT_STARTING_FATE:
            return self._accept_starting_fate()
        if not self._fate_accepted:
            return {"event": EventType.ERROR, "reason": "FATE_NOT_ACCEPTED", "pending_fate": self._pending_fate_view()}

        if self._mode == MODE_COMBAT:
            return self._process_combat_action(name, action)
        return self._process_explore_action(name, action)

    # -- action dispatch tables ------------------------------------------
    def _build_info_dispatch(self) -> Dict[str, Any]:
        """Mode-agnostic actions that never consume a turn."""
        return {
            Action.STATUS: lambda action: self._status(),
            Action.INVENTORY: lambda action: self.inventory.list_inventory(self.player),
            Action.MAP: lambda action: self._map(),
            Action.TECHNIQUES: lambda action: self._techniques(),
            Action.TALENTS: lambda action: self._talents(),
            Action.DAO_VIEW: lambda action: self._dao_view(),
            Action.HELP: lambda action: HelpResult().to_dict(),
            Action.QUIT: lambda action: self._quit(),
        }

    def _build_explore_dispatch(self) -> Dict[str, Any]:
        """Exploration-mode actions, keyed by action name.

        Handlers look attributes up on ``self`` at call time, so state swapped in
        by :meth:`load_game` (player, cultivation service) is always honoured.
        """
        return {
            Action.TRAIN: lambda action: self._advance_time_after(self.cultivation_service.train_body("player", action.get("method_id", "train_body")), "train_body"),
            Action.TRAIN_BODY: lambda action: self._advance_time_after(self.cultivation_service.train_body("player", action.get("method_id", "train_body")), "train_body"),
            Action.TRAIN_ESSENCE: lambda action: self._advance_time_after(self.cultivation_service.train_essence("player", action.get("method_id", "gather_essence")), "train_essence"),
            Action.TALK_TO_CHARACTER: lambda action: self._talk_to_character(action.get("character_id", "")),
            Action.DIALOGUE_CHOOSE: lambda action: self._dialogue_choose(action),
            Action.SPAR_CHARACTER: lambda action: self._start_character_combat(action.get("character_id", ""), "spar"),
            Action.DUEL_CHARACTER: lambda action: self._start_character_combat(action.get("character_id", ""), "duel"),
            Action.RECEIVE_BOON: lambda action: self._receive_boon(action.get("character_id", "")),
            Action.BREAKTHROUGH: lambda action: self._advance_time_after(self._after_breakthrough(self.cultivation_service.attempt_body_breakthrough("player")), "body_breakthrough"),
            Action.BODY_BREAKTHROUGH: lambda action: self._advance_time_after(self._after_breakthrough(self.cultivation_service.attempt_body_breakthrough("player")), "body_breakthrough"),
            Action.ESSENCE_BREAKTHROUGH: lambda action: self._advance_time_after(self._after_breakthrough(self.cultivation_service.attempt_essence_breakthrough("player")), "essence_breakthrough"),
            Action.STABILISE_FOUNDATION: lambda action: self._advance_time_after(self._advance_day_after(self.cultivation_service.stabilise_foundation("player")), "stabilise"),
            Action.STABILISE_ESSENCE: lambda action: self._advance_time_after(self._advance_day_after(self.cultivation_service.stabilise_essence("player")), "stabilise_essence"),
            Action.EXPLORE: lambda action: self._explore(),
            Action.REST: lambda action: self._advance_time_after(self._advance_day_after(self._rest()), "rest"),
            Action.MEDITATE: lambda action: self._advance_time_after(self._meditate(), "meditate"),
            Action.TRAVEL: lambda action: self._travel(action.get("location_id", "")),
            Action.SHOP: lambda action: self.shops.shop_view(self.player, action.get("shop_id", "")),
            Action.BUY_ITEM: lambda action: self._buy_item(action),
            Action.SELL_ITEM: lambda action: self._sell_item(action),
            Action.TRAINERS: lambda action: self.trainers.trainer_view(self.player, action.get("trainer_id", "")),
            Action.LEARN_SKILL: lambda action: self._learn_skill(action),
            Action.SECTS: lambda action: self.sects.sect_view(self.player, action.get("sect_id", "")),
            Action.JOIN_SECT: lambda action: self._join_sect(action.get("sect_id", "")),
            Action.UPGRADE_TALENT: lambda action: self._upgrade_talent(action.get("track", ""), action.get("target_id", "")),
            Action.CLOSED_DOOR: lambda action: self._closed_door(action.get("years", 0)),
            Action.REPAIR_ITEM: lambda action: self._repair_item(action.get("item_id", "")),
            Action.GATHER: lambda action: self._advance_time_after(self._gather(), "gather"),
            Action.REFINE: lambda action: self._refine(action.get("recipe_id", "")),
            Action.ENTER_REALM: lambda action: self._enter_realm(),
            Action.REALM_ADVANCE: lambda action: self._realm_advance(),
            Action.REALM_LEAVE: lambda action: self._realm_leave(),
            Action.TOURNAMENT: lambda action: self._tournament(),
            Action.DAO_AWAKEN: lambda action: self._dao_awaken(action.get("dao_id", "")),
            Action.EXPORT_SAVE: lambda action: self._export_save(),
            Action.IMPORT_SAVE: lambda action: self._import_save(action.get("payload", ""), action.get("slot", "default")),
            Action.SAVE: lambda action: self.save_game(action.get("slot") or "default"),
            Action.LOAD: lambda action: self.load_game(action.get("slot") or "default"),
            Action.USE_ITEM: lambda action: self._use_item(action.get("item_id", "")),
            Action.EQUIP_ITEM: lambda action: self._equip_item(action),
            Action.UNEQUIP_ITEM: lambda action: self._unequip_item(action),
            Action.USE_SKILL: lambda action: {"event": EventType.ERROR, "reason": "SKILL_ONLY_IN_COMBAT"},
            Action.ATTACK: lambda action: {"event": EventType.ERROR, "reason": "NOT_IN_COMBAT"},
            Action.FLEE: lambda action: {"event": EventType.ERROR, "reason": "NOT_IN_COMBAT"},
        }

    def _quit(self) -> Dict[str, Any]:
        """Flag the session as finished and return the quit result."""
        self._running = False
        return QuitResult().to_dict()

    # -- exploration-mode dispatch ---------------------------------------
    def _process_explore_action(self, name: str, action: Dict[str, Any]) -> Dict[str, Any]:
        handler = self._explore_dispatch.get(name)
        if handler is None:
            return {"event": EventType.ERROR, "reason": "UNKNOWN_COMMAND", "input": action.get("raw", name)}
        return handler(action)
