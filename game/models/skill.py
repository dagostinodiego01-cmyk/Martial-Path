"""Skill model.

Skills are fully data-driven (see ``data/skills.json``). The model only holds
the definition; the *logic* of applying a skill lives in the combat system.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Skill:
    """A cultivation technique.

    Attributes:
        id: Stable identifier used in data files and player skill lists.
        name: Human-readable name (content, displayed by the UI).
        type: ``"active"`` (invoked in combat) or ``"passive"`` (always on).
        effect: Effect identifier the systems interpret (e.g. ``"damage"``).
        scaling: Multiplier applied to the relevant stat by the effect.
        cooldown: Turns before an active skill may be reused.
        qi_cost: Qi consumed to activate an active skill.
        insight_required: Minimum insight (see ``combat_system``) needed to
            invoke this technique mid-fight. ``0`` (the default) means it can
            always be used once qi/cooldown allow. Intent techniques carry a
            positive value so they unlock as the fight's insight builds.
        combo_role: Optional stance role for combo sequences (ROADMAP B.6):
            ``"opening"``, ``"response"``, or ``"finisher"``. Landing these in
            order grants escalating damage bonuses (see ``CombatSystem``);
            empty string means the technique takes no stance.
        description: Flavour/help text (content, displayed by the UI).
    """

    id: str
    name: str
    type: str
    effect: str
    scaling: float
    cooldown: int
    qi_cost: int
    insight_required: int = 0
    combo_role: str = ""
    description: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        """Build a skill from a raw data-file entry."""
        return cls(
            id=data["id"],
            name=data["name"],
            type=data.get("type", "active"),
            effect=data.get("effect", "damage"),
            scaling=float(data.get("scaling", 1.0)),
            cooldown=int(data.get("cooldown", 0)),
            qi_cost=int(data.get("qi_cost", 0)),
            insight_required=int(data.get("insight_required", 0)),
            combo_role=str(data.get("combo_role", "")),
            description=data.get("description", ""),
        )

    def is_active(self) -> bool:
        """Return ``True`` if the skill must be invoked (vs. passive)."""
        return self.type == "active"
