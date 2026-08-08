"""Effective-stats calculation.

Computes a player's *effective* combat stats from their pristine base stats plus
always-on modifiers (currently passive skills). Keeping this as a calculation --
rather than permanently baking bonuses into stored stats -- means a passive can
never double-apply across save/load, and leaves room for equipment, pills, and
temporary buffs/debuffs to layer in later without ever corrupting base values.

This system is pure: it reads the player and skill registry it is given and
mutates nothing.
"""
from __future__ import annotations

from typing import Any, Dict

from game.models.skill import Skill


class StatsSystem:
    """Derives effective stats from base stats and passive skills."""

    def __init__(self, skills: Dict[str, Skill]) -> None:
        self._skills = skills

    def effective_defense(self, player: Any) -> int:
        """Return defense after applying always-on passive skill buffs."""
        defense = player.defense
        for skill_id in player.skills:
            skill = self._skills.get(skill_id)
            if skill is not None and not skill.is_active() and skill.effect == "buff_defense":
                defense = int(round(defense * skill.scaling))
        defense += int(self._equipment_stat(player, "defense"))
        return defense

    def effective_stats(self, player: Any) -> Dict[str, int]:
        """Return the full set of effective combat stats."""
        return {
            "attack": player.attack + int(self._equipment_stat(player, "attack")),
            "defense": self.effective_defense(player),
            "max_hp": player.max_hp + int(self._equipment_stat(player, "max_hp")),
            "max_qi": player.max_qi + int(self._equipment_stat(player, "max_qi")),
            "body_strength": player.body_strength + int(self._equipment_stat(player, "body_strength")),
            "comprehension": player.comprehension + int(self._equipment_stat(player, "comprehension")),
            "speed": int(self._equipment_stat(player, "speed")),
            "evasion": int(self._equipment_stat(player, "evasion")),
        }

    def _equipment_stat(self, player: Any, stat_name: str) -> float:
        modifiers = getattr(player, "equipment_modifiers", None)
        if callable(modifiers):
            data = modifiers()
        else:
            data = getattr(player, "_equipment_modifiers", {})
        return float(data.get("stat_modifiers", {}).get(stat_name, 0.0))
