"""Shared constants used across every layer.

Centralizing action names and event/result types avoids magic strings and gives
the UI a stable contract to switch on when formatting engine results. Nothing in
this module performs I/O or holds mutable state.

``Action`` and ``EventType`` are :class:`~enum.StrEnum`s: each member *is* a
``str`` equal to its value, so it hashes and serialises exactly like the old
string constants (dict keys, ``==`` comparisons, and ``json.dumps`` are all
unchanged) while adding membership validation and autocomplete.
"""
from __future__ import annotations

from enum import StrEnum
from typing import Any, Dict


class Action(StrEnum):
    """Canonical action identifiers produced by the command router.

    The UI never invents these strings; it obtains them from the router, which
    is the single place that translates human input into engine commands.
    """

    TRAIN = "TRAIN"
    TRAIN_BODY = "TRAIN_BODY"
    TRAIN_ESSENCE = "TRAIN_ESSENCE"
    EXPLORE = "EXPLORE"
    STATUS = "STATUS"
    INVENTORY = "INVENTORY"
    SHOP = "SHOP"
    BUY_ITEM = "BUY_ITEM"
    SELL_ITEM = "SELL_ITEM"
    TALK_TO_CHARACTER = "TALK_TO_CHARACTER"
    DIALOGUE_CHOOSE = "DIALOGUE_CHOOSE"
    SPAR_CHARACTER = "SPAR_CHARACTER"
    DUEL_CHARACTER = "DUEL_CHARACTER"
    RECEIVE_BOON = "RECEIVE_BOON"
    JOIN_SECT = "JOIN_SECT"
    SECTS = "SECTS"
    BREAKTHROUGH = "BREAKTHROUGH"
    BODY_BREAKTHROUGH = "BODY_BREAKTHROUGH"
    ESSENCE_BREAKTHROUGH = "ESSENCE_BREAKTHROUGH"
    STABILISE_FOUNDATION = "STABILISE_FOUNDATION"
    STABILISE_ESSENCE = "STABILISE_ESSENCE"
    TRAINERS = "TRAINERS"
    LEARN_SKILL = "LEARN_SKILL"
    ROLL_STARTING_FATE = "ROLL_STARTING_FATE"
    ACCEPT_STARTING_FATE = "ACCEPT_STARTING_FATE"
    USE_ITEM = "USE_ITEM"
    EQUIP_ITEM = "EQUIP_ITEM"
    UNEQUIP_ITEM = "UNEQUIP_ITEM"
    USE_SKILL = "USE_SKILL"
    ATTACK = "ATTACK"
    FLEE = "FLEE"
    REST = "REST"
    MEDITATE = "MEDITATE"
    TRAVEL = "TRAVEL"
    MAP = "MAP"
    TECHNIQUES = "TECHNIQUES"
    SAVE = "SAVE"
    LOAD = "LOAD"
    HELP = "HELP"
    QUIT = "QUIT"
    UNKNOWN = "UNKNOWN"


class EventType(StrEnum):
    """Discriminators attached to every structured result the engine returns.

    The UI switches on these to decide how to render a result. Adding a new
    engine outcome means adding a constant here and a formatter in the UI, with
    no changes to the systems that produced neighbouring results.
    """

    TRAIN_RESULT = "TRAIN_RESULT"
    BREAKTHROUGH_RESULT = "BREAKTHROUGH_RESULT"
    STABILISE_RESULT = "STABILISE_RESULT"
    STARTING_FATE_ROLLED = "STARTING_FATE_ROLLED"
    STARTING_FATE_ACCEPTED = "STARTING_FATE_ACCEPTED"
    CHARACTER_ENCOUNTER = "CHARACTER_ENCOUNTER"
    CHARACTER_INTERACTION = "CHARACTER_INTERACTION"
    DIALOGUE_CHOICE = "DIALOGUE_CHOICE"
    BOON = "BOON"
    SECTS = "SECTS"
    SECT_JOINED = "SECT_JOINED"
    EXPLORE_RESULT = "EXPLORE_RESULT"
    COMBAT = "COMBAT"
    COMBAT_TURN = "COMBAT_TURN"
    COMBAT_END = "COMBAT_END"
    LOOT = "LOOT"
    SPECIAL = "SPECIAL"
    STATUS = "STATUS"
    INVENTORY = "INVENTORY"
    SHOP = "SHOP"
    ITEM_PURCHASED = "ITEM_PURCHASED"
    ITEM_SOLD = "ITEM_SOLD"
    ITEM_USED = "ITEM_USED"
    TRAINER = "TRAINER"
    SKILL_LEARNED = "SKILL_LEARNED"
    EQUIP_ITEM_RESULT = "EQUIP_ITEM_RESULT"
    UNEQUIP_ITEM_RESULT = "UNEQUIP_ITEM_RESULT"
    REST_RESULT = "REST_RESULT"
    MEDITATE_RESULT = "MEDITATE_RESULT"
    TRAVEL_RESULT = "TRAVEL_RESULT"
    LOCATION = "LOCATION"
    MAP = "MAP"
    QUEST_UPDATE = "QUEST_UPDATE"
    SAVE_RESULT = "SAVE_RESULT"
    LOAD_RESULT = "LOAD_RESULT"
    HELP = "HELP"
    MESSAGE = "MESSAGE"
    ERROR = "ERROR"
    QUIT = "QUIT"
    PLAYER_DIED = "PLAYER_DIED"


#: The only ``available_systems`` values a location may declare. Every value
#: maps to an engine action a frontend can actually perform; narrative-only
#: verbs (forge_crafting, arena_ladder, ...) are excluded so UI labels stay
#: honest. ``tools/normalize_available_systems.py`` writes to this contract and
#: the data validator enforces it.
AVAILABLE_SYSTEMS: frozenset[str] = frozenset({
    "explore",
    "rest",
    "meditate",
    "travel",
    "market",
    "trainers",
    "dialogue",
    "combat",
    "sparring",
    "sects",
    "quests",
})


# Initial player template. Kept here (rather than hard-coded in the engine) so a
# future save/character-creation system can supply a different starting sheet.
STARTING_PLAYER: Dict[str, Any] = {
    "realm": "Mortal",
    "stage": 1,
    "max_hp": 100,
    "max_qi": 50,
    "attack": 15,
    "defense": 5,
    "path": "Unassigned",
    "foundation_quality": 50,
    "body_strength": 10,
    "soul_strength": 10,
    "comprehension": 10,
    "reputation": 0,
    "morality": 0,
    "current_location": "outer_forest",
    "skills": ["iron_fist", "flowing_step"],
    "inventory": {"healing_pill": 2},
}
