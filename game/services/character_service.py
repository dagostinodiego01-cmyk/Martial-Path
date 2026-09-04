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
        """Return UI-safe briefs for the NPCs anchored to ``location_id``.

        Characters carry an optional ``min_story_tier``: they only surface once
        the player has reached that story tier, so higher-tier world figures do
        not appear in a fledgling's story. Untagged characters always appear.
        """
        briefs: List[Dict[str, Any]] = []
        story_tier = self._story_tier(player)
        for npc_id in self._locations.npc_ids(location_id):
            character = self._by_id.get(npc_id)
            if character is None:
                continue
            required = character.get("min_story_tier")
            if required is not None and story_tier < int(required):
                continue
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

    # -- dialogue choices -------------------------------------------------
    def dialogue_choices(self, character_id: str, player: Any) -> List[Dict[str, Any]]:
        """Return the dialogue choices currently available for one NPC.

        A choice is returned only when its ``requires`` gate (min relationship
        tier, morality band) is met, so a UI can render exactly what the player
        may say now. Read-only: this never mutates the player or store.
        """
        character = self._by_id.get(character_id)
        if character is None:
            return []
        return [
            dict(choice)
            for choice in character.get("dialogue", {}).get("choices", [])
            if self._choice_available(choice, character_id, player)
        ]

    def get_dialogue_choice(
        self, character_id: str, choice_id: str, player: Any
    ) -> Optional[Dict[str, Any]]:
        """Return a validated, currently-available dialogue choice, or ``None``.

        The engine applies the returned choice's deltas; this service only
        resolves and validates, keeping its read-only contract intact.
        """
        character = self._by_id.get(character_id)
        if character is None:
            return None
        for choice in character.get("dialogue", {}).get("choices", []):
            if choice.get("id") != choice_id:
                continue
            if not self._choice_available(choice, character_id, player):
                return None
            resolved = dict(choice)
            resolved["character_name"] = character.get("name", character_id)
            return resolved
        return None

    # -- relationship rewards (boons) ------------------------------------
    def available_reward(self, character_id: str, player: Any) -> Optional[Dict[str, Any]]:
        """Return the first unclaimed relationship reward whose gate is met.

        Rewards live in ``gameplay_hooks.relationship_rewards`` and gate on
        ``min_tier`` (relationship tier order) and/or ``morality_band`` (exact
        band). A reward marked ``once`` (default) disappears after it is claimed,
        tracked via the NPC's relationship memory flags. Read-only: claiming is
        the engine's job; this only resolves what is currently available.
        """
        character = self._by_id.get(character_id)
        if character is None or not self._is_unlocked(character, player):
            return None
        rewards = character.get("gameplay_hooks", {}).get("relationship_rewards", [])
        if not isinstance(rewards, list):
            return None
        tier = self._tier(character_id, player)
        band = self._morality.band_id(getattr(player, "morality", 0))
        flags = self._relationship_state(character_id, player).get("personal_memory_flags", {}) or {}
        for index, reward in enumerate(rewards):
            if not isinstance(reward, dict):
                continue
            min_tier = reward.get("min_tier")
            if min_tier and not self._relationships.meets_min_tier(tier, min_tier):
                continue
            morality_band = reward.get("morality_band")
            if morality_band and band != morality_band:
                continue
            if reward.get("once", True) and flags.get(f"reward_{index}"):
                continue
            payload = reward.get("reward", {}) if isinstance(reward.get("reward"), dict) else {}
            return {
                "character_id": character_id,
                "name": character.get("name", character_id),
                "index": index,
                "reward": payload,
                "message": payload.get("message", ""),
                "tier": tier,
            }
        return None

    def can_receive_reward(self, character_id: str, player: Any) -> bool:
        """Convenience predicate: is a relationship reward currently claimable?"""
        return self.available_reward(character_id, player) is not None

    # -- internal ---------------------------------------------------------
    def _story_tier(self, player: Any) -> int:
        """Return the player's highest reached story tier (fail-open on 0)."""
        try:
            return max(1, int(getattr(player, "max_story_tier", 1)))
        except (TypeError, ValueError):
            return 1

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
            "can_receive_reward": self.can_receive_reward(character["id"], player),
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
        # Optional relationship gate: ``spar_min_tier`` / ``duel_min_tier`` in
        # the hooks make availability respond to the player's history with this
        # NPC, not just its static unlock flag.
        min_tier = hooks.get(f"{hook_key.replace('can_', '')}_min_tier")
        if min_tier and not self._relationships.meets_min_tier(self._tier(character_id, player), min_tier):
            return {"allowed": False, "reason": "RELATIONSHIP_TOO_LOW"}
        # Optional morality gate: ``spar_morality_band`` / ``duel_morality_band``
        # require the player to be in a specific morality band, so alignment also
        # changes what an NPC is willing to do over time.
        morality_band = hooks.get(f"{hook_key.replace('can_', '')}_morality_band")
        if morality_band and self._morality.band_id(getattr(player, "morality", 0)) != morality_band:
            return {"allowed": False, "reason": "MORALITY_BAND_MISMATCH"}
        return {"allowed": True, "reason": None, "enemy_id": hooks.get("enemy_id", "")}

    def _choice_available(self, choice: Dict[str, Any], character_id: str, player: Any) -> bool:
        """Return whether a dialogue choice's ``requires`` gate is met."""
        requires = choice.get("requires", {}) or {}
        min_tier = requires.get("min_tier")
        if min_tier and not self._relationships.meets_min_tier(self._tier(character_id, player), min_tier):
            return False
        band = requires.get("morality_band")
        if band and self._morality.band_id(getattr(player, "morality", 0)) != band:
            return False
        return True

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
