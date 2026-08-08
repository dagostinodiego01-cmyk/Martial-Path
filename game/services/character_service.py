"""Character service.

Single authority for "who is here, and what can I do with them?". It coordinates
the static NPC roster, the current location's occupants, the player's morality
band, and per-NPC relationship state into the read models a UI or dialogue system
renders -- so the UI never has to decide availability, tiers, or whether a duel
is allowed.

Pure and read-only: it reads the player and the data it is given and mutates
nothing (in particular, viewing a relationship never creates store entries).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from game.systems.location_system import LocationSystem
from game.systems.morality_system import MoralitySystem
from game.systems.relationship_system import RelationshipSystem


class CharacterService:
    """Answers NPC availability, dialogue-context, and interaction questions."""

    def __init__(
        self,
        characters: List[Dict[str, Any]],
        locations: LocationSystem,
        morality: MoralitySystem,
        relationships: RelationshipSystem,
    ) -> None:
        self._by_id: Dict[str, Dict[str, Any]] = {c["id"]: c for c in (characters or [])}
        self._locations = locations
        self._morality = morality
        self._relationships = relationships

    # -- lookups ----------------------------------------------------------
    def get_character(self, character_id: str) -> Optional[Dict[str, Any]]:
        """Return the raw character definition (or ``None``)."""
        return self._by_id.get(character_id)

    def get_available_characters(self, location_id: str, player: Any) -> List[Dict[str, Any]]:
        """Return UI-safe briefs for the NPCs anchored to ``location_id``."""
        briefs: List[Dict[str, Any]] = []
        for npc_id in self._locations.npc_ids(location_id):
            character = self._by_id.get(npc_id)
            if character is not None:
                briefs.append(self._brief(character, player))
        return briefs

    # -- read models ------------------------------------------------------
    def get_relationship_view(self, character_id: str, player: Any) -> Dict[str, Any]:
        """Return the interaction tier and behaviour text for one NPC."""
        character = self._by_id.get(character_id, {})
        tier = self._tier(character_id, player)
        behavior = character.get("personality", {}).get("relationship_behavior", {})
        return {
            "character_id": character_id,
            "tier": tier,
            "score": self._score(character_id, player),
            "behavior_text": behavior.get(tier, ""),
        }

    def get_dialogue_context(self, character_id: str, player: Any) -> Optional[Dict[str, Any]]:
        """Return everything a dialogue/AI layer needs to voice this NPC now."""
        character = self._by_id.get(character_id)
        if character is None:
            return None
        personality = character.get("personality", {})
        band_id = self._morality.band_id(getattr(player, "morality", 0))
        tier = self._tier(character_id, player)
        return {
            "character_id": character_id,
            "name": character.get("name", character_id),
            "speech_style": personality.get("speech_style", ""),
            "morality_band": band_id,
            "morality_reaction": personality.get("morality_reaction", {}).get(band_id, ""),
            "relationship_tier": tier,
            "relationship_behavior": personality.get("relationship_behavior", {}).get(tier, ""),
            "intro_text": character.get("intro_text", ""),
            "repeat_text": character.get("repeat_text", ""),
            "ai_prompt_notes": character.get("ai_prompt_notes", ""),
        }

    # -- interaction gates ------------------------------------------------
    def can_spar(self, character_id: str, player: Any) -> Dict[str, Any]:
        """Return whether the player may spar this NPC, and why not if blocked."""
        return self._can_do(character_id, player, "can_spar")

    def can_duel(self, character_id: str, player: Any) -> Dict[str, Any]:
        """Return whether the player may duel this NPC, and why not if blocked."""
        return self._can_do(character_id, player, "can_duel")

    # -- internal ---------------------------------------------------------
    def _brief(self, character: Dict[str, Any], player: Any) -> Dict[str, Any]:
        hooks = character.get("gameplay_hooks", {})
        return {
            "id": character["id"],
            "name": character.get("name", character["id"]),
            "faction": character.get("faction", ""),
            "relationship_tier": self._tier(character["id"], player),
            "can_talk": bool(hooks.get("can_talk", False)),
            "can_spar": bool(hooks.get("can_spar", False)),
            "can_duel": bool(hooks.get("can_duel", False)),
            "unlocked": self._is_unlocked(character, player),
        }

    def _can_do(self, character_id: str, player: Any, hook_key: str) -> Dict[str, Any]:
        character = self._by_id.get(character_id)
        if character is None:
            return {"allowed": False, "reason": "UNKNOWN_CHARACTER"}
        hooks = character.get("gameplay_hooks", {})
        if not hooks.get(hook_key, False):
            return {"allowed": False, "reason": "NOT_AVAILABLE"}
        if not self._is_unlocked(character, player):
            return {"allowed": False, "reason": "LOCKED"}
        return {"allowed": True, "reason": None, "enemy_id": hooks.get("enemy_id", "")}

    def _is_unlocked(self, character: Dict[str, Any], player: Any) -> bool:
        """Gate by unlock stage. Realm names use a narrative scheme distinct from
        cultivation ids, so realm gating is fail-open; the stage gate is exact."""
        min_stage = int(character.get("unlock", {}).get("min_stage", 0))
        return int(getattr(player, "stage", 1)) >= min_stage

    def _relationship_state(self, character_id: str, player: Any) -> Dict[str, Any]:
        store = getattr(player, "relationships", {}) or {}
        return store.get(character_id, {})

    def _score(self, character_id: str, player: Any) -> int:
        return int(self._relationship_state(character_id, player).get("relationship_score", 0))

    def _tier(self, character_id: str, player: Any) -> str:
        return self._relationships.tier_for(self._score(character_id, player))
