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
        description: Flavour/help text (content, displayed by the UI).
    """

    id: str
    name: str
    type: str
    effect: str
    scaling: float
    cooldown: int
    qi_cost: int
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
            description=data.get("description", ""),
        )

    def is_active(self) -> bool:
        """Return ``True`` if the skill must be invoked (vs. passive)."""
        return self.type == "active"
