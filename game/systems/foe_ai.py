"""Foe AI (ROADMAP B.8): named foes fight with dao, pressure, and stances.

This is the enemy half of B.6's stance system: instead of only rolling abilities
and basic attacks, a dao-carrying foe *fights a stance* -- it opens, responds,
and finishes chains (feeding the same ``combo_stage`` bank the player enjoys),
presses aggression when its dao counters the player's (the counter graph), and
guards (waives its press) when the player banks a chain it must respect.

Pure logic: no I/O, no UI, no state of its own. ``RNG`` drives every roll so a
fight replays exactly.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from game.models.enemy import Enemy
from game.models.player import Player
from game.systems.combat_system import COMBO_ROLES
from game.utils.rng import RNG

if TYPE_CHECKING:
    from game.models.skill import Skill
    from game.systems.dao_system import DaoSystem

#: Aggression multipliers on the foe's ability/technique chance.
AGGRESSION_WHEN_COUNTERING = 1.5   # its dao beats the player's dao
AGGRESSION_WHEN_COUNTERED = 0.6    # the player's dao beats its dao
AGGRESSION_NEUTRAL = 1.0

#: The HP fraction below which a wounded foe leans on its abilities more.
WOUNDED_HP_FRACTION = 0.5
WOUNDED_AGGRRESSION_BONUS = 0.2

#: The player's banked chain stage at which a prudent foe guards.
GUARD_COMBO_STAGE = 2


class FoeAI:
    """Chooses the enemy's combat action from dao, pressure, and stance state."""

    def __init__(
        self,
        dao: Optional["DaoSystem"] = None,
        skills: Optional[Dict[str, "Skill"]] = None,
        rng: Optional[RNG] = None,
    ) -> None:
        self._dao = dao
        self._skills = skills or {}
        self._rng = rng or RNG()

    # -- aggression -----------------------------------------------------------
    def aggression(self, player: Player, enemy: Enemy) -> float:
        """How hard ``enemy`` presses this round (counter graph + wounds)."""
        base = AGGRESSION_NEUTRAL
        if self._dao is not None and enemy.dao_id:
            matchup = float(self._dao.matchup(enemy.dao_id, player.dao_id))
            if matchup > 1.0:
                base = AGGRESSION_WHEN_COUNTERING
            elif matchup < 1.0:
                base = AGGRESSION_WHEN_COUNTERED
        if enemy.max_hp > 0 and enemy.hp <= enemy.max_hp * WOUNDED_HP_FRACTION:
            base += WOUNDED_AGGRRESSION_BONUS
        return base

    def _countered(self, player: Player, enemy: Enemy) -> bool:
        """True when the player's dao counters the foe's (its aggression drops)."""
        if self._dao is None or not enemy.dao_id:
            return False
        return float(self._dao.matchup(enemy.dao_id, player.dao_id)) < 1.0

    # -- the foe's stance -----------------------------------------------------
    def intended_stance(self, player: Player, enemy: Enemy) -> Optional[str]:
        """The stance the foe pursues this round, or ``None`` for mooks.

        The stance follows the chain: at stage 0 it seeks an ``opening``, at 1 a
        ``response``, at 2 a ``finisher``. A countered dao-careful foe guards
        (stance ``None``) when the player's banked chain reaches the finisher
        -- respecting the player's flow is the AI showing wisdom, not weakness.
        """
        if not enemy.dao_id:
            return None
        if self._countered(player, enemy) and player.combo_stage >= GUARD_COMBO_STAGE:
            return None  # guard: break the flow rather than feed the finisher
        stage = int(getattr(enemy, "ai_stage", 0))
        if stage < len(COMBO_ROLES):
            return COMBO_ROLES[stage]
        return None

    def advance_ai_stage(self, enemy: Enemy, used_role: Optional[str]) -> int:
        """Advance (or reset) the foe's stance bank after it acts.

        Mirrors the player's chain rules: an ``opening`` arms stage 1, a
        ``response`` continues only from stage 1, and a ``finisher`` completes
        and resets the chain to 0.
        """
        if used_role == "opening":
            enemy.ai_stage = 1
        elif used_role == "response" and int(getattr(enemy, "ai_stage", 0)) == 1:
            enemy.ai_stage = 2
        elif used_role == "finisher":
            enemy.ai_stage = 0  # chains complete; the next one begins anew
        else:
            enemy.ai_stage = 0
        return int(enemy.ai_stage)

    # -- the foe's action ------------------------------------------------------
    def choose_action(self, player: Player, enemy: Enemy) -> Dict[str, Any]:
        """Return the foe's intended action for this round.

        The dict carries the intent (``guard`` / ability / technique id /
        ``attack``) plus the resolved stance, so the combat system can execute
        it and the turn log can narrate the foe's *thinking*. Dao-less mooks
        keep the plain behaviour: ability rolls and basic attacks only.
        """
        aggression = self.aggression(player, enemy)
        if not enemy.dao_id:
            ability = self._pick_ability(player, enemy, aggression)
            if ability is not None:
                return ability
            return {"kind": "attack", "stance": None, "aggression": aggression}

        stance = self.intended_stance(player, enemy)
        if stance is None:
            return {"kind": "guard", "stance": None, "aggression": aggression}

        ability = self._pick_ability(player, enemy, aggression)
        technique = self._pick_technique(player, enemy, stance)
        # A data-driven ability fires by chance; otherwise the stance technique
        # (if the foe knows one) or its basic attack.
        if ability is not None:
            ability["stance"] = stance
            return ability
        if technique is not None:
            return {"kind": "technique", "skill_id": technique, "stance": stance, "aggression": aggression}
        return {"kind": "attack", "stance": stance, "aggression": aggression}

    def _pick_technique(self, player: Player, enemy: Enemy, stance: str) -> Optional[str]:
        """A technique the foe knows carrying the wanted ``stance`` role."""
        known = [skill_id for skill_id in getattr(enemy, "skills", []) or [] if skill_id in self._skills]
        for skill_id in known:
            skill = self._skills[skill_id]
            if skill.is_active() and skill.combo_role == stance:
                return skill_id
        return None

    def _pick_ability(self, player: Player, enemy: Enemy, aggression: float) -> Optional[Dict[str, Any]]:
        """Roll the foe's data-driven abilities, scaled by aggression."""
        for ability in enemy.abilities:
            chance = float(ability.get("chance", 0.0)) * aggression
            if self._rng.chance(min(1.0, chance)):
                return {"kind": "ability", "ability": dict(ability), "stance": None, "aggression": aggression}
        return None
