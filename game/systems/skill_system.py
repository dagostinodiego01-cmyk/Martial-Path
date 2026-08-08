"""Skill (technique) acquisition rules.

Owns the single question "can this player learn this technique, and record it if
so?". Both technique manuals (consumable items) and location trainers route their
learn requests through here, so the dedup/validation rules live in one place.

The system holds no session state; it validates against the skill catalog and
mutates only the player's known-skill list. It returns structured results only.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from game.core.constants import EventType
from game.core.results import SkillLearnedResult
from game.models.player import Player
from game.models.skill import Skill


class SkillSystem:
    """Validates and records the techniques a player has learned."""

    def __init__(self, skills: Dict[str, Skill]) -> None:
        self._skills = skills

    def knows(self, player: Player, skill_id: str) -> bool:
        """Return ``True`` if the player already knows the technique."""
        return skill_id in player.skills

    def learn_skill(
        self,
        player: Player,
        skill_id: str,
        source: str = "manual",
        price: Optional[Dict[str, int]] = None,
        wallet: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """Teach ``skill_id`` to the player if it is valid and not yet known.

        ``source`` records how it was learned ("manual"/"trainer") for the UI.
        ``price``/``wallet`` are pass-through display fields for paid learning.
        """
        if not skill_id:
            return {"event": EventType.ERROR, "reason": "NO_SKILL_SPECIFIED"}
        skill = self._skills.get(skill_id)
        if skill is None:
            return {"event": EventType.ERROR, "reason": "UNKNOWN_SKILL", "skill_id": skill_id}
        if skill_id in player.skills:
            return {"event": EventType.ERROR, "reason": "SKILL_ALREADY_KNOWN", "skill_id": skill_id, "name": skill.name}

        player.skills.append(skill_id)
        return SkillLearnedResult(
            skill_id=skill_id,
            name=skill.name,
            source=source,
            player_message=f"You comprehend {skill.name} and add it to your techniques.",
            price=price,
            wallet=wallet,
        ).to_dict()
