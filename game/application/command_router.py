"""Command router.

Maps raw input strings (``"train"``, ``"use healing_pill"``, ``"skill iron_fist"``)
into structured command dictionaries such as ``{"action": "TRAIN"}``. It is the
single source of truth for the player's vocabulary, keeping that concern out of
both the UI (which just reads text) and the engine (which only sees actions).
"""
from __future__ import annotations

from typing import Any, Dict, List

from game.core.constants import Action


class CommandRouter:
    """Translates human input into engine actions."""

    #: Maps every accepted verb/alias to a canonical action.
    _ALIASES: Dict[str, str] = {
        "train": Action.TRAIN,
        "t": Action.TRAIN,
        "cultivate": Action.TRAIN,
        "explore": Action.EXPLORE,
        "e": Action.EXPLORE,
        "adventure": Action.EXPLORE,
        "status": Action.STATUS,
        "s": Action.STATUS,
        "stats": Action.STATUS,
        "talk": Action.TALK_TO_CHARACTER,
        "spar": Action.SPAR_CHARACTER,
        "duel": Action.DUEL_CHARACTER,
        "inventory": Action.INVENTORY,
        "inv": Action.INVENTORY,
        "i": Action.INVENTORY,
        "shop": Action.SHOP,
        "market": Action.SHOP,
        "buy": Action.BUY_ITEM,
        "purchase": Action.BUY_ITEM,
        "sell": Action.SELL_ITEM,
        "trainers": Action.TRAINERS,
        "masters": Action.TRAINERS,
        "learn": Action.LEARN_SKILL,
        "sects": Action.SECTS,
        "join": Action.JOIN_SECT,
        "boon": Action.RECEIVE_BOON,
        "receive": Action.RECEIVE_BOON,
        "map": Action.MAP,
        "talents": Action.TALENTS,
        "talent": Action.TALENTS,
        "upgrade": Action.UPGRADE_TALENT,
        "closed_door": Action.CLOSED_DOOR,
        "seclude": Action.CLOSED_DOOR,
        "repair": Action.REPAIR_ITEM,
        "export": Action.EXPORT_SAVE,
        "import": Action.IMPORT_SAVE,
        "breakthrough": Action.BREAKTHROUGH,
        "b": Action.BREAKTHROUGH,
        "stabilise": Action.STABILISE_FOUNDATION,
        "stabilize": Action.STABILISE_FOUNDATION,
        "roll": Action.ROLL_STARTING_FATE,
        "fate": Action.ROLL_STARTING_FATE,
        "accept": Action.ACCEPT_STARTING_FATE,
        "use": Action.USE_ITEM,
        "equip": Action.EQUIP_ITEM,
        "unequip": Action.UNEQUIP_ITEM,
        "skill": Action.USE_SKILL,
        "cast": Action.USE_SKILL,
        "attack": Action.ATTACK,
        "a": Action.ATTACK,
        "flee": Action.FLEE,
        "run": Action.FLEE,
        "rest": Action.REST,
        "meditate": Action.MEDITATE,
        "m": Action.MEDITATE,
        "travel": Action.TRAVEL,
        "go": Action.TRAVEL,
        "techniques": Action.TECHNIQUES,
        "tech": Action.TECHNIQUES,
        "save": Action.SAVE,
        "load": Action.LOAD,
        "help": Action.HELP,
        "h": Action.HELP,
        "commands": Action.HELP,
        "quit": Action.QUIT,
        "exit": Action.QUIT,
        "q": Action.QUIT,
    }

    #: Actions whose remaining words are joined ("iron fist" -> "iron_fist") into
    #: a single argument field. Adding an argument command is a one-line entry.
    _ARG_FIELDS: Dict[str, str] = {
        Action.USE_ITEM: "item_id",
        Action.SHOP: "shop_id",
        Action.UNEQUIP_ITEM: "slot",
        Action.USE_SKILL: "skill_id",
        Action.LEARN_SKILL: "skill_id",
        Action.TALK_TO_CHARACTER: "character_id",
        Action.SPAR_CHARACTER: "character_id",
        Action.DUEL_CHARACTER: "character_id",
        Action.JOIN_SECT: "sect_id",
        Action.SECTS: "sect_id",
        Action.RECEIVE_BOON: "character_id",
        Action.TRAVEL: "location_id",
        Action.SAVE: "slot",
        Action.LOAD: "slot",
        Action.REPAIR_ITEM: "item_id",
    }

    def route(self, raw: str) -> Dict[str, Any]:
        """Convert a raw input line into a structured command dictionary."""
        text = (raw or "").strip().lower()
        if not text:
            return {"action": Action.UNKNOWN, "raw": raw}

        verb, *args = text.split()
        action = self._ALIASES.get(verb, Action.UNKNOWN)
        command: Dict[str, Any] = {"action": action, "raw": raw}

        arg_field = self._ARG_FIELDS.get(action)
        if arg_field is not None:
            command[arg_field] = "_".join(args) if args else ""
        elif action == Action.TRAIN:
            self._route_train_args(command, args)
        elif action == Action.BREAKTHROUGH:
            self._route_breakthrough_args(command, args)
        elif action == Action.STABILISE_FOUNDATION:
            self._route_stabilise_args(command, args)
        elif action == Action.EQUIP_ITEM:
            self._route_equip_args(command, args)
        elif action == Action.BUY_ITEM:
            self._route_buy_args(command, args)
        elif action == Action.SELL_ITEM:
            self._route_sell_args(command, args)
        elif action == Action.UPGRADE_TALENT:
            self._route_upgrade_args(command, args)
        elif action == Action.CLOSED_DOOR:
            self._route_closed_door_args(command, args)
        elif action == Action.IMPORT_SAVE:
            command["payload"] = " ".join(args)

        return command

    def _route_train_args(self, command: Dict[str, Any], args: List[str]) -> None:
        if not args or args[0] in {"body", "physical"}:
            command["action"] = Action.TRAIN_BODY
            return
        if args[0] in {"essence", "qi", "dantian"}:
            command["action"] = Action.TRAIN_ESSENCE

    def _route_breakthrough_args(self, command: Dict[str, Any], args: List[str]) -> None:
        if not args or args[0] in {"body", "physical"}:
            command["action"] = Action.BODY_BREAKTHROUGH
            return
        if args[0] in {"essence", "qi", "dantian"}:
            command["action"] = Action.ESSENCE_BREAKTHROUGH

    def _route_stabilise_args(self, command: Dict[str, Any], args: List[str]) -> None:
        if args and args[0] in {"essence", "qi", "dantian"}:
            command["action"] = Action.STABILISE_ESSENCE

    def _route_equip_args(self, command: Dict[str, Any], args: List[str]) -> None:
        if args:
            command["item_id"] = args[0]
        if len(args) > 1:
            command["slot"] = args[1]

    def _route_buy_args(self, command: Dict[str, Any], args: List[str]) -> None:
        if not args:
            command["item_id"] = ""
            return
        item_parts = list(args)
        if item_parts[-1].isdigit():
            command["quantity"] = int(item_parts[-1])
            item_parts = item_parts[:-1]
        command["item_id"] = "_".join(item_parts)

    def _route_sell_args(self, command: Dict[str, Any], args: List[str]) -> None:
        self._route_buy_args(command, args)

    def _route_upgrade_args(self, command: Dict[str, Any], args: List[str]) -> None:
        if args:
            command["track"] = args[0]
        if len(args) > 1:
            command["target_id"] = args[1]

    def _route_closed_door_args(self, command: Dict[str, Any], args: List[str]) -> None:
        if args and args[0].isdigit():
            command["years"] = int(args[0])
        else:
            command["years"] = 0

    def describe_commands(self) -> List[Dict[str, str]]:
        """Return the command reference used by the UI to render help."""
        return [
            {"command": "train body", "aliases": "train, t, cultivate", "desc": "Advance Body Transformation progress."},
            {"command": "train essence", "aliases": "", "desc": "Advance Essence Gathering progress."},
            {"command": "roll fate", "aliases": "fate", "desc": "Reveal your starting Martial and Body Talent."},
            {"command": "accept fate", "aliases": "accept", "desc": "Accept the revealed starting fate and begin."},
            {"command": "breakthrough body", "aliases": "breakthrough, b", "desc": "Attempt a Body Transformation breakthrough."},
            {"command": "breakthrough essence", "aliases": "", "desc": "Attempt an Essence Gathering breakthrough."},
            {"command": "stabilise foundation", "aliases": "stabilise, stabilize", "desc": "Reduce cultivation strain and steady foundation stability."},
            {"command": "stabilise essence", "aliases": "", "desc": "Reduce essence strain and steady its foundation stability."},
            {"command": "map", "aliases": "", "desc": "Show your current map position and the exits you can reach."},
            {"command": "techniques", "aliases": "tech", "desc": "List the techniques you have learned."},
            {"command": "talents", "aliases": "talent", "desc": "Show your Martial/Body talents and their upgrade paths."},
            {"command": "upgrade <track> <target>", "aliases": "", "desc": "Upgrade a talent, e.g. 'upgrade martial human_grade'."},
            {"command": "closed_door <years>", "aliases": "seclude", "desc": "Cultivate in seclusion for N years."},
            {"command": "repair <item_id>", "aliases": "", "desc": "Repair a piece of worn equipment for gold."},
            {"command": "export", "aliases": "", "desc": "Transcribe your journey to a portable save record."},
            {"command": "import <record>", "aliases": "", "desc": "Restore your journey from a portable save record."},
            {"command": "boon <character_id>", "aliases": "receive", "desc": "Accept a relationship reward from a character who trusts you."},
            {"command": "explore", "aliases": "e", "desc": "Venture out; may trigger combat, loot, or a special encounter."},
            {"command": "talk <character_id>", "aliases": "", "desc": "Speak with a named character at your location."},
            {"command": "spar <character_id>", "aliases": "", "desc": "Start a sparring match with an available character."},
            {"command": "duel <character_id>", "aliases": "", "desc": "Challenge an available character to a duel."},
            {"command": "status", "aliases": "s, stats", "desc": "Show your cultivation, stats, and skills."},
            {"command": "inventory", "aliases": "inv, i", "desc": "List the items you are carrying."},
            {"command": "shop", "aliases": "market", "desc": "View the market available at your current location."},
            {"command": "buy <item_id> [quantity]", "aliases": "purchase", "desc": "Buy an item from the current market."},
            {"command": "sects [sect_id]", "aliases": "", "desc": "View the sects available at your location."},
            {"command": "join <sect_id>", "aliases": "", "desc": "Join a sect at your location and take up its path."},
            {"command": "sell <item_id> [quantity]", "aliases": "", "desc": "Sell an owned item or piece of equipment for gold."},
            {"command": "use <item_id>", "aliases": "", "desc": "Use an item, e.g. 'use healing_pill'."},
            {"command": "equip <item_id> <slot>", "aliases": "", "desc": "Equip an owned item into a valid equipment slot."},
            {"command": "unequip <slot>", "aliases": "", "desc": "Clear an equipped item from a slot."},
            {"command": "attack", "aliases": "a", "desc": "[Combat] Strike the enemy with a basic attack."},
            {"command": "skill <skill_id>", "aliases": "cast", "desc": "[Combat] Unleash an active skill, e.g. 'skill iron_fist'."},
            {"command": "flee", "aliases": "run", "desc": "[Combat] Attempt to escape the battle."},
            {"command": "help", "aliases": "h", "desc": "Show this list of commands."},
            {"command": "quit", "aliases": "exit, q", "desc": "Leave the mortal world (exit the game)."},
        ]
