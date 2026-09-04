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
from typing import Any, Dict, List

# Game "modes" gate which actions are valid (exploration vs a single combat).
MODE_EXPLORE = "explore"
MODE_COMBAT = "combat"
# A dao debate (B.7): a non-lethal contest of conviction with its own stances.
MODE_DEBATE = "debate"

# Spirit-oath duel stakes (B.7). Winning banks the wager at this multiple;
# losing costs the exp/gold fractions; breaching (walking away) forfeits the
# larger of the wagered or a fraction of current gold.
OATH_WIN_MULTIPLIER = 1.5
OATH_LOSS_EXP_PENALTY = 0.5
OATH_LOSS_GOLD_PENALTY = 1.0
OATH_BREACH_GOLD_FRACTION = 0.5


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
    DEBATE_CHARACTER = "DEBATE_CHARACTER"
    OATH_DUEL_CHARACTER = "OATH_DUEL_CHARACTER"
    DEBATE_STANCE = "DEBATE_STANCE"
    YIELD_DEBATE = "YIELD_DEBATE"
    WALK_AWAY = "WALK_AWAY"
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
    TALENTS = "TALENTS"
    UPGRADE_TALENT = "UPGRADE_TALENT"
    CLOSED_DOOR = "CLOSED_DOOR"
    REPAIR_ITEM = "REPAIR_ITEM"
    GATHER = "GATHER"
    REFINE = "REFINE"
    ENTER_REALM = "ENTER_REALM"
    ENDLESS_REALM = "ENDLESS_REALM"
    REALM_ADVANCE = "REALM_ADVANCE"
    REALM_LEAVE = "REALM_LEAVE"
    TOURNAMENT = "TOURNAMENT"
    DAO_VIEW = "DAO_VIEW"
    DAO_AWAKEN = "DAO_AWAKEN"
    UNLOCK_TREE = "UNLOCK_TREE"
    UNLOCK = "UNLOCK"
    RETIRE_ASSENT = "RETIRE_ASSENT"
    WORLD_INFO = "WORLD_INFO"
    CODEX = "CODEX"
    WORLD_RUMORS = "WORLD_RUMORS"
    LEARN_RUMOR = "LEARN_RUMOR"
    EXPORT_SAVE = "EXPORT_SAVE"
    IMPORT_SAVE = "IMPORT_SAVE"
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
    DEBATE_STARTED = "DEBATE_STARTED"
    DEBATE_ROUND = "DEBATE_ROUND"
    DEBATE_END = "DEBATE_END"
    OATH_DUEL_STARTED = "OATH_DUEL_STARTED"
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
    TECHNIQUES = "TECHNIQUES"
    TALENTS = "TALENTS"
    TALENT_UPGRADED = "TALENT_UPGRADED"
    CLOSED_DOOR_RESULT = "CLOSED_DOOR_RESULT"
    REPAIR_RESULT = "REPAIR_RESULT"
    GATHER_RESULT = "GATHER_RESULT"
    REFINE_RESULT = "REFINE_RESULT"
    REALM_ENTERED = "REALM_ENTERED"
    REALM_ROOM = "REALM_ROOM"
    REALM_COMPLETED = "REALM_COMPLETED"
    DAO_VIEW = "DAO_VIEW"
    DAO_AWAKENED = "DAO_AWAKENED"
    UNLOCK_TREE = "UNLOCK_TREE"
    UNLOCK_PURCHASED = "UNLOCK_PURCHASED"
    RETIRED = "RETIRED"
    WORLD_INFO = "WORLD_INFO"
    CODEX = "CODEX"
    WORLD_RUMORS = "WORLD_RUMORS"
    RUMOR_LEARNED = "RUMOR_LEARNED"
    SAVE_EXPORTED = "SAVE_EXPORTED"
    SAVE_IMPORTED = "SAVE_IMPORTED"
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
    "gather",
    "refine",
    "secret_realm",
    "tournament",
})


# Experience needed to convert into one point of Comprehension. Combat, quest,
# and training rewards all feed the same ``Player.exp`` bank; the engine converts
# banked exp into comprehension at this rate (which in turn speeds cultivation).
EXP_PER_COMPREHENSION = 50

# The Dao a brand-new cultivator begins with before any Dao awakening. Must be a
# valid id in ``data/daos.json`` (pinned by a test).
DEFAULT_DAO_ID = "sword_dao"

# The free starting origin every new run falls back to when none (or an
# unaffordable one) is chosen. Must be a valid id in ``data/origins.json``.
DEFAULT_ORIGIN_ID = "orphan"

# The essence-realm order a run must reach before the player may retire and
# ascend (C.7). Divine Transformation (order 6) -- past Divine Sea, before the
# late-game stub realms. Retirement banks the ascension reward and opens endless
# mode; death and retirement are both valid run-ends.
ASCENSION_ESSENCE_ORDER = 6

# The act id whose quest completion marks the campaign beaten (D.3).
CAMPAIGN_FINAL_ACT = "act_three"

# Ancestral Memory banked the moment the campaign's final act completes (D.3):
# winning the story pays even if the character never retires or dies.
CAMPAIGN_COMPLETE_BONUS = 150

# Endless-realm treasure pool (D.5): weighted draws fund each depth's hoards.
# Data lives in constants (not JSON) because it only exists for the post-game.
ENDLESS_TREASURE_POOL: List[Dict[str, Any]] = [
    {"item_id": "spirit_stone", "weight": 4},
    {"item_id": "qi_pill", "weight": 3},
    {"item_id": "healing_pill", "weight": 3},
    {"item_id": "talent_refining_elixir", "weight": 1},
]

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
    "dao_id": DEFAULT_DAO_ID,
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
