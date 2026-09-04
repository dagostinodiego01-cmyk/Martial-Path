"""Dao debates and spirit-oath duels (ROADMAP B.7): engine-side flow.

This mixin owns the *when*: opening a debate or oath duel against a named
character, routing debate stances while ``MODE_DEBATE`` is active, and resolving
the spirit-oath's asymmetric stakes when the duel ends. The pure rules live in
:class:`~game.systems.debate_system.DebateSystem`.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from game.core.constants import (
    OATH_WIN_MULTIPLIER,
    OATH_LOSS_EXP_PENALTY,
    OATH_LOSS_GOLD_PENALTY,
    OATH_BREACH_GOLD_FRACTION,
    MODE_COMBAT,
    MODE_DEBATE,
    MODE_EXPLORE,
    Action,
    EventType,
)
from game.core.results import DebateRoundResult, DebateStartedResult, OathDuelStartedResult
from game.models.enemy import Enemy
from game.models.player import Player


class DebateMixin:
    """Starts debates/oath duels and routes their stances each round."""

    # -- eligibility ----------------------------------------------------------
    def _debate_candidates(self, character_id: str) -> Dict[str, Any]:
        """Resolve a character into its debate/oath foe spawn, or an error reason.

        A character may debate (and optionally stake an oath duel) when it can
        spar: both are consensual contests against the character's foe template.
        """
        character = self.character_service.get_character(character_id)
        if character is None:
            return {"error": "UNKNOWN_CHARACTER", "character_id": character_id}
        gate = self.character_service.can_spar(character_id, self.player)
        if not gate.get("allowed"):
            return {"error": gate.get("reason", "NOT_AVAILABLE"), "character_id": character_id}
        enemy_id = gate.get("enemy_id", "")
        if not enemy_id:
            return {"error": "NO_CHARACTER_ENEMY", "character_id": character_id}
        enemy = self._spawn_character_enemy(enemy_id)
        if enemy is None:
            return {"error": "UNKNOWN_ENEMY", "character_id": character_id, "enemy_id": enemy_id}
        return {"enemy": enemy, "character_id": character_id, "name": str(character.get("name", character_id))}

    # -- starting a debate ------------------------------------------------------
    def _start_debate(self, character_id: str, oath: bool = False) -> Dict[str, Any]:
        """Open a dao debate (or a spirit-oath duel) with a named character."""
        if self._mode == MODE_DEBATE:
            return {"event": EventType.ERROR, "reason": "ALREADY_IN_DEBATE"}
        resolved = self._debate_candidates(character_id)
        if "error" in resolved:
            return {"event": EventType.ERROR, **resolved}
        foe: Enemy = resolved["enemy"]
        # Conviction is insight-shaped: for the debate's duration the player's
        # insight pool carries their comprehension-derived conviction (the
        # combat pool is zero out of combat anyway) and is restored afterwards.
        self._insight_before_debate = int(self.player.insight)
        self.player.insight = max(1, int(self.player.comprehension) // 2)
        # The foe's conviction grows with the world it walks: named foes carry a
        # realm-scaled floor over their technique-derived base, so late-game
        # duelists argue as hard as they fight.
        base_foe_insight = max(2, len(getattr(foe, "skills", []) or []) + 2)
        if foe.essence_realm_id:
            realm_order = int(self._essence_realm_orders.get(foe.essence_realm_id, 1))
            base_foe_insight = max(base_foe_insight, 2 + realm_order * 2)
        foe.insight = base_foe_insight
        self._debate = self.debate.new_state(self.player.insight, foe.insight)
        self._debate_foe = foe
        self._debate_character = str(resolved["character_id"])
        self._mode = MODE_DEBATE
        self._oath_stakes: Optional[Dict[str, Any]] = None
        if oath:
            self._oath_stakes = self._capture_oath_stakes()
        view = self.debate.view(self._debate, foe.name)
        if oath:
            return OathDuelStartedResult(
                character_id=self._debate_character,
                foe_name=foe.name,
                debate=view,
                stakes=dict(self._oath_stakes or {}),
                player_message=(
                    f"You and {foe.name} swear a spirit oath: the loser's dao will bear the weight."
                ),
            ).to_dict()
        return DebateStartedResult(
            character_id=self._debate_character,
            foe_name=foe.name,
            debate=view,
            player_message=f"You and {foe.name} settle your differences in a contest of dao.",
        ).to_dict()

    def _capture_oath_stakes(self) -> Dict[str, Any]:
        """Snapshot what the player puts on the line before the oath is sworn."""
        return {
            "gold_wagered": int(self.player.gold),
            "exp_wagered": int(self.player.exp),
        }

    # -- the debate loop --------------------------------------------------------
    def _process_debate_action(self, name: str, action: Dict[str, Any]) -> Dict[str, Any]:
        """Route a stance action while a debate is active."""
        if self._debate is None or self._debate_foe is None:
            self._mode = MODE_EXPLORE
            return {"event": EventType.ERROR, "reason": "NOT_IN_DEBATE"}
        if name == Action.YIELD_DEBATE:
            action = dict(action)
            action["stance"] = "yield"
        if name == Action.WALK_AWAY:
            return self._abandon_debate()
        if name != Action.DEBATE_STANCE:
            return {"event": EventType.ERROR, "reason": "INVALID_IN_DEBATE", "input": name}
        stance = str(action.get("stance", ""))
        if stance not in self.debate.stances:
            return {
                "event": EventType.ERROR,
                "reason": "INVALID_DEBATE_STANCE",
                "stances": list(self.debate.stances),
                "stance": stance,
            }

        foe_stance = self.debate.foe_stance(self._debate)
        events = self.debate.round_resolve(
            self.player, self._debate_foe, self._debate, stance, foe_stance
        )
        outcome = self.debate.outcome(self._debate)
        view = self.debate.view(self._debate, self._debate_foe.name)
        if outcome is None:
            return DebateRoundResult(
                outcome="ONGOING",
                debate=view,
                turn_events=events,
                player_message=f"You hold your ground in the debate with {self._debate_foe.name}.",
            ).to_dict()
        return self._end_debate(outcome, view, events)

    def _end_debate(self, outcome: str, view: Dict[str, Any], events: Any) -> Dict[str, Any]:
        """Close the debate and resolve any spirit-oath stakes."""
        foe = self._debate_foe
        character_id = self._debate_character
        self._mode = MODE_EXPLORE
        # Restore the combat insight pool the debate borrowed.
        self.player.insight = int(getattr(self, "_insight_before_debate", 0))
        self._debate = None
        self._debate_foe = None
        self._debate_character = ""

        result: Dict[str, Any] = {
            "event": EventType.DEBATE_END,
            "outcome": outcome,
            "character_id": character_id,
            "foe_name": foe.name,
            "debate": view,
            "turn_events": list(events or []),
        }
        if outcome == "DEBATE_WON":
            result["player_message"] = f"{foe.name} bows to the weight of your dao."
            result["narrative"] = self.narrative.render(
                "debate_won", {**self._narrative_context(), "enemy": foe.name}
            )
        elif outcome == "DEBATE_LOST":
            result["player_message"] = f"Your conviction falters; {foe.name} has the truer path."
            result["narrative"] = self.narrative.render(
                "debate_lost", {**self._narrative_context(), "enemy": foe.name}
            )
        else:
            result["player_message"] = "The debate ends in philosophical stalemate."
            result["narrative"] = self.narrative.render(
                "debate_stalemate", {**self._narrative_context(), "enemy": foe.name}
            )

        # D.4: settled debates feed the faction campaigns (branch objectives).
        if outcome == "DEBATE_WON":
            updates = self.quests.notify("debate", self.player, self.inventory, target=character_id)
            if updates:
                result["quest_updates"] = list(result.get("quest_updates", [])) + updates
                self._maybe_complete_campaign(result)

        # B.7 spirit-oath stakes: asymmetric, sworn before the first word.
        if self._oath_stakes is not None:
            result["oath"] = self._resolve_oath_stakes(outcome, result)
            self._oath_stakes = None
        return result

    def _resolve_oath_stakes(self, outcome: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply the spirit-oath's asymmetric stakes for the debate's outcome.

        * Won: the oath-bearer's dao yields -- a large Ancestral Memory-style
          reward banked immediately (gold and exp at ``OATH_WIN_MULTIPLIER``).
        * Lost: the player's cultivation survives but pays exp and gold.
        * Breach (walked away mid-debate): the sworn spirit enforces the full
          forfeit -- the larger of the wagered or current gold is taken.
        """
        stakes = dict(self._oath_stakes or {})
        wagered_gold = int(stakes.get("gold_wagered", 0))
        if outcome == "DEBATE_WON":
            gold = int(wagered_gold * OATH_WIN_MULTIPLIER)
            exp = int(int(stakes.get("exp_wagered", 0)) * OATH_WIN_MULTIPLIER)
            self.player.gold += gold
            self.player.exp += exp
            return {"resolved": "WON", "gold_won": gold, "exp_won": exp}
        if outcome == "DEBATE_LOST":
            gold = min(int(self.player.gold), int(wagered_gold * OATH_LOSS_GOLD_PENALTY))
            exp = int(int(stakes.get("exp_wagered", 0)) * OATH_LOSS_EXP_PENALTY)
            self.player.gold -= gold
            self.player.exp = max(0, self.player.exp - exp)
            return {"resolved": "LOST", "gold_lost": gold, "exp_lost": exp}
        if outcome == "DEBATE_STALEMATE":
            # A true draw: the oath releases both parties unharmed.
            return {"resolved": "STALEMATE"}
        # Breach: walking away from a sworn duel mid-debate.
        forfeit = max(wagered_gold, int(self.player.gold * OATH_BREACH_GOLD_FRACTION))
        forfeit = min(int(self.player.gold), forfeit)
        self.player.gold -= forfeit
        return {"resolved": "BREACH", "gold_forfeit": forfeit}

    # -- views ---------------------------------------------------------------
    def _active_debate_view(self) -> Optional[Dict[str, Any]]:
        """UI-safe snapshot of the active debate (``None`` outside one)."""
        if self._debate is None or self._debate_foe is None:
            return None
        view = self.debate.view(self._debate, self._debate_foe.name)
        view["oath"] = dict(self._oath_stakes) if self._oath_stakes else None
        return view

    # -- breach hook -------------------------------------------------------------
    def _abandon_debate(self) -> Dict[str, Any]:
        """Walk away from a debate (breaching an oath duel if one is sworn)."""
        if self._debate is None or self._debate_foe is None:
            self._mode = MODE_EXPLORE
            return {"event": EventType.ERROR, "reason": "NOT_IN_DEBATE"}
        foe_name = self._debate_foe.name
        had_oath = self._oath_stakes is not None
        view = self.debate.view(self._debate, foe_name)
        result = self._end_debate("DEBATE_ABANDONED", view, [])
        result["outcome"] = "DEBATE_ABANDONED"
        result["player_message"] = (
            "You break off the debate and walk away." if not had_oath
            else "You break the spirit oath and walk away; the sworn spirits take their due."
        )
        return result
