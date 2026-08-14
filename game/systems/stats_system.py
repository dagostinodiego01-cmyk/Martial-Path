"""Effective-stats calculation.

Computes a player's *effective* combat stats from their pristine base stats plus
always-on modifiers (passive skills and equipment). Keeping this as a calculation
-- rather than permanently baking bonuses into stored stats -- means a passive
can never double-apply across save/load, and leaves room for temporary
buffs/debuffs to layer in later without ever corrupting base values.

Passive skill effects honoured here:

* ``buff_attack`` / ``buff_defense`` / ``buff_max_hp`` / ``buff_max_qi``
  multiply the matching base stat (stack multiplicatively).
* ``buff_speed`` / ``buff_evasion`` multiply the base speed/evasion.
* ``crit_chance`` adds ``scaling * 0.1`` to crit probability (capped at 100%).
* ``crit_damage`` sets the crit multiplier (highest wins; default 2.0).
* ``hp_regen`` / ``qi_regen`` add flat per-combat-turn recovery.
* ``qi_cost_reduction`` multiplies an active skill's qi cost.

This system is pure: it reads the player and skill registry it is given and
mutates nothing.
"""
from __future__ import annotations

from typing import Any, Dict

from game.models.skill import Skill

DEFAULT_CRIT_MULTIPLIER = 2.0


class StatsSystem:
    """Derives effective stats from base stats and passive skills."""

    def __init__(self, skills: Dict[str, Skill]) -> None:
        self._skills = skills

    # -- passive aggregation helpers ------------------------------------
    def _scale(self, player: Any, effect: str) -> float:
        """Product of every learned passive's scaling for ``effect`` (1.0 if none)."""
        scale = 1.0
        for skill_id in getattr(player, "skills", []):
            skill = self._skills.get(skill_id)
            if skill is not None and not skill.is_active() and skill.effect == effect:
                scale *= skill.scaling
        return scale

    def _sum(self, player: Any, effect: str) -> float:
        """Sum of every learned passive's scaling for ``effect`` (0 if none)."""
        total = 0.0
        for skill_id in getattr(player, "skills", []):
            skill = self._skills.get(skill_id)
            if skill is not None and not skill.is_active() and skill.effect == effect:
                total += skill.scaling
        return total

    def _max(self, player: Any, effect: str) -> float:
        """Largest scaling among learned passives for ``effect`` (0 if none)."""
        best = 0.0
        for skill_id in getattr(player, "skills", []):
            skill = self._skills.get(skill_id)
            if skill is not None and not skill.is_active() and skill.effect == effect:
                best = max(best, skill.scaling)
        return best

    # -- effective stats -------------------------------------------------
    def effective_defense(self, player: Any) -> int:
        """Return defense after applying always-on passive skill buffs."""
        defense = int(round(player.defense * self._scale(player, "buff_defense")))
        defense += int(self._equipment_stat(player, "defense"))
        return defense

    def effective_stats(self, player: Any) -> Dict[str, int]:
        """Return the full set of effective combat stats."""
        base_speed = float(getattr(player, "speed", 0)) + self._equipment_stat(player, "speed")
        base_evasion = float(getattr(player, "evasion", 0)) + self._equipment_stat(player, "evasion")
        return {
            "attack": int(round(player.attack * self._scale(player, "buff_attack"))) + int(self._equipment_stat(player, "attack")),
            "defense": self.effective_defense(player),
            "max_hp": int(round(player.max_hp * self._scale(player, "buff_max_hp"))) + int(self._equipment_stat(player, "max_hp")),
            "max_qi": int(round(player.max_qi * self._scale(player, "buff_max_qi"))) + int(self._equipment_stat(player, "max_qi")),
            "body_strength": player.body_strength + int(self._equipment_stat(player, "body_strength")),
            "comprehension": player.comprehension + int(self._equipment_stat(player, "comprehension")),
            "speed": int(round(base_speed * self._scale(player, "buff_speed"))),
            "evasion": int(round(base_evasion * self._scale(player, "buff_evasion"))),
        }

    # -- combat helpers --------------------------------------------------
    def crit_chance(self, player: Any) -> float:
        """Probability (0..1) of a critical hit, from ``crit_chance`` passives."""
        # ponytail: scaling is a small >1 number in the data (1.08-1.38); treat
        # it as a percentage-point boost (x0.1). Re-tune if the ladder changes.
        return min(1.0, self._sum(player, "crit_chance") * 0.1)

    def crit_multiplier(self, player: Any) -> float:
        """Damage multiplier on a critical hit; ``crit_damage`` passives raise it."""
        return max(DEFAULT_CRIT_MULTIPLIER, self._max(player, "crit_damage"))

    def regen(self, player: Any) -> tuple[int, int]:
        """Flat (hp, qi) recovered at the start of each of the player's combat turns."""
        return int(self._sum(player, "hp_regen")), int(self._sum(player, "qi_regen"))

    def effective_qi_cost(self, skill: Skill, player: Any) -> int:
        """Return a skill's qi cost after ``qi_cost_reduction`` passives."""
        scale = self._scale(player, "qi_cost_reduction")
        return int(round(skill.qi_cost * scale))

    # -- equipment -------------------------------------------------------
    def _equipment_stat(self, player: Any, stat_name: str) -> float:
        modifiers = getattr(player, "equipment_modifiers", None)
        if callable(modifiers):
            data = modifiers()
        else:
            data = getattr(player, "_equipment_modifiers", {})
        return float(data.get("stat_modifiers", {}).get(stat_name, 0.0))
