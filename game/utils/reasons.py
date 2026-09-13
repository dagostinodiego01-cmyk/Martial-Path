"""Player-facing explanations for every way the engine can refuse an action.

A refusal used to be told in prose nobody could act on: the result carried a
machine ``reason`` (``SKILL_ON_COOLDOWN``), the narrative layer replaced it with a
random *error* template ("The attempt falters against the Spring air..."), and each
frontend guessed the rest from its own partial table -- the CLI knew 46 codes, the
Godot client 43, and everything else fell through to "That cannot be done".

This module is the single source. :func:`explain` turns a result dict into one
sentence that says what was refused and, where the result carries the numbers, by
how much. The engine attaches it to every result that has a ``reason``
(``DispatchMixin._decorate_narrative``), so the CLI, the HTTP API and the Godot
client all read the same wording instead of inventing their own.

:data:`REASONS` is deliberately data, not code: ``tests/test_reason_messages.py``
scans ``game/`` for every ``reason`` the engine can emit and fails if one is
missing here, so the table cannot rot back into guesswork.
"""
from __future__ import annotations

from typing import Any, Dict, Mapping

__all__ = ["REASONS", "explain", "knows"]


#: reason code -> sentence template. ``{field}`` slots read the result dict; a
#: slot the result does not carry renders as ``?`` rather than breaking the line.
REASONS: Dict[str, str] = {
    # -- mode: what is already happening --------------------------------
    "ALREADY_IN_COMBAT": "You are already in a fight -- see it through before you do that.",
    "ALREADY_IN_DEBATE": "A debate of dao is already under way. Finish it first.",
    "ALREADY_IN_REALM": "You are already inside a secret realm.",
    "INVALID_IN_COMBAT": "You cannot do that in the middle of a fight.",
    "INVALID_IN_DEBATE": "You cannot do that while a debate of dao is running.",
    "INVALID_IN_ENCOUNTER": "Something is waiting on your decision. Choose one of its options first.",
    "NOT_IN_COMBAT": "There is no fight in progress.",
    "NOT_IN_DEBATE": "There is no debate in progress.",
    "NOT_IN_ENCOUNTER": "Nothing is waiting on your decision.",
    "NOT_IN_REALM": "You are not inside a secret realm.",
    "CANNOT_STUDY_IN_COMBAT": "You cannot study a technique in the middle of a fight.",
    "NOT_AVAILABLE": "That is not available here.",
    "LOCKED": "That is not unlocked yet.",
    "TIER_LOCKED": "That is not unlocked yet at your level.",
    "PATH_LOCKED": "That path has not opened to you yet.",
    "QUEST_FLAG_REQUIRED": "You have not reached that point in the story yet.",
    "STORY_TIER_TOO_LOW": "That opens later in the campaign (needs story tier {required}).",
    "ALREADY_OWNED": "You already have that.",
    "ALREADY_JOINED": "You have already joined.",

    # -- the request itself ---------------------------------------------
    "MALFORMED_ACTION": "The game engine did not understand that request.",
    "UNKNOWN_COMMAND": "The game engine does not recognise that action.",
    "NO_CHOICE_SPECIFIED": "Choose one of the offered options first.",
    "CHOICE_NOT_AVAILABLE": "That is not one of the offered options.",
    "UNKNOWN_CHOICE": "That is not one of the offered options (available: {available}).",
    "CHOICE_OUT_OF_RANGE": "Pick a number between 1 and {available_count}.",
    "NO_FOE_SPECIFIED": "Choose which foe to face first.",
    "FOE_NOT_PRESENT": "There is no '{foe_id}' in this fight.",
    "INVALID_QUANTITY": "That quantity is not valid.",
    "EQUIPMENT_QUANTITY_NOT_SUPPORTED": "Equipment is worn one piece at a time -- a quantity does not apply.",

    # -- starting fate and identity -------------------------------------
    "FATE_NOT_ACCEPTED": "Your starting fate has not been accepted yet. Roll it, then accept it.",
    "FATE_ALREADY_ACCEPTED": "Your starting fate has already been accepted.",
    "NAME_EMPTY": "Enter a name first.",
    "NAME_TOO_LONG": "That name is too long -- at most {max_length} characters.",

    # -- items -----------------------------------------------------------
    "NO_ITEM_SPECIFIED": "Choose an item first.",
    "ITEM_NOT_OWNED": "You are not carrying '{item_id}'.",
    "UNKNOWN_ITEM": "There is no item called '{item_id}'.",
    "ITEM_NOT_USABLE": "{detail}",
    "ITEM_NOT_EQUIPPABLE": "'{item_id}' cannot be equipped.",
    "ITEM_NOT_EQUIPPED": "Nothing is equipped in that slot.",
    "UNEQUIP_FIRST": "Take off what you are wearing there first.",
    "INVALID_EQUIPMENT_SLOT": "'{slot}' is not an equipment slot.",
    "SLOT_NOT_ALLOWED": "'{item_id}' does not go in the {slot} slot.",
    "EQUIPMENT_SLOT_EMPTY": "There is nothing equipped in '{slot}'.",
    "REQUIREMENT_NOT_MET": "You do not meet that item's requirements ({required}).",
    "REALM_TOO_LOW": "Your realm is too low to use that (needs {required}).",
    "STRENGTH_TOO_LOW": "Your body strength is too low (needs {required}).",
    "COMPREHENSION_TOO_LOW": "Your comprehension is too low (needs {required}).",
    "NOT_REPAIRABLE": "That has no durability to repair.",
    "NOTHING_TO_REPAIR": "That is already in perfect condition.",
    "INSUFFICIENT_FUNDS": "You cannot afford that.",
    "INSUFFICIENT_RESOURCES": "You lack the materials for this ({missing}).",
    "INSUFFICIENT_MEMORY": "Not enough Ancestral Memory (costs {cost}, you have {ancestral_memory}).",

    # -- techniques ------------------------------------------------------
    "NO_SKILL_SPECIFIED": "Choose a technique first.",
    "UNKNOWN_SKILL": "There is no technique called '{skill_id}'.",
    "SKILL_NOT_KNOWN": "You do not know that technique.",
    "SKILL_ALREADY_KNOWN": "You already know that technique.",
    "SKILL_NOT_USABLE": "'{skill_id}' cannot be used that way.",
    "SKILL_ONLY_IN_COMBAT": "That technique can only be used in a fight.",
    "SKILL_ON_COOLDOWN": "That technique is still recovering ({remaining} turn(s) left).",
    "NOT_ENOUGH_QI": "Not enough Qi (needs {required}, you have {qi}).",
    "NOT_ENOUGH_INSIGHT": "Not enough Insight (needs {required}, you have {insight}).",
    "TECHNIQUE_NOT_OFFERED": "This teacher does not offer that technique.",
    "COMBO_OUT_OF_SEQUENCE": "That does not follow from the technique you just used.",
    "FAILED_ATTEMPT": "The attempt failed.",

    # -- cultivation and breakthrough ------------------------------------
    "INSUFFICIENT_PROGRESS": "Your cultivation has not reached the threshold ({progress} / {required_progress}). Keep training, meditating, or seeking spiritual resources.",
    "PROGRESS": "Your cultivation progress is not high enough yet. Keep training.",
    "STRAIN_TOO_HIGH": "Your cultivation strain is too high for a safe breakthrough ({current_strain} / {max_allowed_strain} allowed). Stabilise your foundation first.",
    "FOUNDATION_UNSTABLE": "Your foundation is not stable enough ({foundation_stability} / {required_foundation_stability} needed). Stabilise before attempting again.",
    "FOUNDATION": "Your foundation is not stable enough yet.",
    "ESSENCE_LOCKED_BY_BODY_PULSE": "Essence gathering has not opened yet -- reach Pulse Condensation in Body Transformation first.",
    "INVALID_CLOSED_DOOR_YEARS": "Choose one of the offered seclusion lengths.",
    "ASCENSION_NOT_REACHED": "You have not reached the realm needed to ascend.",
    "IRONMAN_MODE": "Ironman mode does not allow reloading a save.",

    # -- travel and the world --------------------------------------------
    "NO_DESTINATION": "Choose somewhere to travel first.",
    "UNKNOWN_LOCATION": "That place is not known to you.",
    "ALREADY_THERE": "You are already there.",
    "NO_ROUTE": "There is no direct route from here.",
    "NO_HERBS_HERE": "Nothing worth gathering grows here.",
    "NO_REALM_HERE": "No secret realm opens here.",
    "NO_TOURNAMENT_HERE": "No tournament is being held here.",
    "ENDLESS_NOT_OPEN": "The endless road opens once the campaign is won, or during an endless run.",
    "UNKNOWN_UNLOCK": "There is no such legacy unlock ('{unlock_id}').",

    # -- markets ----------------------------------------------------------
    "NO_SHOP_AVAILABLE": "There is no market here.",
    "SHOP_NOT_AVAILABLE": "There is no market here.",
    "UNKNOWN_SHOP": "There is no market called '{shop_id}'.",
    "SHOP_ITEM_NOT_AVAILABLE": "This market does not sell that.",
    "SHOP_STOCK_TOO_LOW": "This market does not have that many in stock ({available} left).",

    # -- teachers and sects ------------------------------------------------
    "NO_TRAINER_AVAILABLE": "No technique master is here.",
    "TRAINER_NOT_AVAILABLE": "No technique master is here.",
    "UNKNOWN_TRAINER": "There is no master called '{trainer_id}' here.",
    "SECT_NOT_AVAILABLE": "No sect holds ground here.",
    "SECT_NOT_JOINED": "You do not belong to a sect.",
    "SECT_TIER_TOO_LOW": "Your standing in the sect is too low for that (needs tier {required}).",
    "UNKNOWN_SECT": "There is no sect called '{sect_id}'.",
    "FACTION_REQUIRED": "You do not have the standing with that faction.",
    "RELATIONSHIP_TOO_LOW": "Your bond with them is not close enough yet.",
    "MORALITY_BAND_MISMATCH": "Your alignment does not permit that.",
    "REPUTATION_TOO_LOW": "Your reputation is too low for that (needs {required}).",
    "REPUTATION_TOO_HIGH": "Your reputation is too high for that (at most {required}).",
    "NO_REWARD_AVAILABLE": "They have nothing to give you right now.",

    # -- people -------------------------------------------------------------
    "NO_CHARACTER_SPECIFIED": "Choose someone to deal with first.",
    "UNKNOWN_CHARACTER": "There is no one called '{character_id}' here.",
    "NO_CHARACTER_ENEMY": "That character has no combat entry to fight.",
    "UNKNOWN_ENEMY": "That character's combat entry is missing.",

    # -- dao and debate ------------------------------------------------------
    "NO_DAO_SPECIFIED": "Choose a dao first.",
    "UNKNOWN_DAO": "There is no dao called '{dao_id}'.",
    "DAO_AWAKENING_LOCKED": "The dao heart has not opened to you yet. Walk further into the story.",
    "DAO_ALREADY_AWAKENED": "You have already awakened to a dao.",
    "INVALID_DEBATE_STANCE": "'{stance}' is not a stance you can take (try: {stances}).",
    "UNKNOWN_RUMOR": "There is no such rumour ('{rumor_id}').",
    "NO_RUMOR_SPECIFIED": "Choose a rumour first.",

    # -- talents ---------------------------------------------------------------
    "INVALID_TALENT_TRACK": "A talent track is either 'martial' or 'body'.",
    "INVALID_UPGRADE_TARGET": "'{target_id}' is not an upgrade this talent can take.",

    # -- alchemy ---------------------------------------------------------------
    "UNKNOWN_RECIPE": "There is no recipe called '{recipe_id}'.",

    # -- saves ------------------------------------------------------------------
    "SAVE_NOT_FOUND": "There is no save in that slot.",
    "SAVE_CORRUPT": "That save could not be read -- it may be damaged.",
    "SAVE_VERSION_MISMATCH": "That save was made by a different version of the game.",
    "WRITE_FAILED": "The game could not write that save.",
    "IMPORT_EMPTY": "There is no save record to import.",
    "IMPORT_INVALID": "That save record could not be read.",
}

#: Shown only for a reason code this table does not know -- which the completeness
#: test in ``tests/test_reason_messages.py`` keeps from happening for anything the
#: engine itself can emit. Naming the code beats pretending nothing went wrong.
_UNKNOWN = "That cannot be done just now ({reason})."

#: Used when a result names a material it cannot use but carries no explanation of
#: its own.
_DEFAULT_DETAIL = "That is a material, not something you can use directly -- another action spends it."


class _Values(dict):
    """Result fields, with ``?`` for slots the given result does not carry."""

    def __missing__(self, key: str) -> str:
        return "?"


def knows(reason: str) -> bool:
    """Whether this table can explain ``reason``."""
    return reason in REASONS


def explain(result: Mapping[str, Any]) -> str:
    """One player-facing sentence saying why ``result`` was refused.

    Reads the reason code and whatever numbers the result carries, so the player is
    told the size of the gap ("needs 5, you have 2") rather than just that one
    exists.
    """
    if not isinstance(result, Mapping):
        return _UNKNOWN.format(reason="?")
    reason = str(result.get("reason") or "")
    template = REASONS.get(reason)
    if template is None:
        return _UNKNOWN.format(reason=reason or "?")
    return template.format_map(_values(result))


def _values(result: Mapping[str, Any]) -> _Values:
    """The formatting values for one result, with the lists and dicts flattened."""
    values = _Values(result)
    values.setdefault("detail", _DEFAULT_DETAIL)

    available = result.get("available")
    if isinstance(available, (list, tuple, set)):
        joined = ", ".join(str(entry) for entry in available)
        values["available"] = joined or "none"
        values["available_count"] = len(available)

    for field in ("required", "missing", "cost"):
        entry = result.get(field)
        if isinstance(entry, Mapping):
            values[field] = _materials(entry)

    stances = result.get("stances")
    if isinstance(stances, (list, tuple)):
        values["stances"] = ", ".join(str(stance) for stance in stances) or "none"

    return values


def _materials(costs: Mapping[str, Any]) -> str:
    """``{"talent_refining_elixir": 2}`` -> ``"2 x talent refining elixir"``."""
    parts = [
        f"{quantity} x {str(item_id).replace('_', ' ')}"
        for item_id, quantity in sorted(costs.items())
    ]
    return ", ".join(parts) or "nothing"
