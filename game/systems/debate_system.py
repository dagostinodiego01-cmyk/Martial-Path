"""Dao debates (ROADMAP B.7): non-lethal duels of conviction.

A debate is a duel fought with stances and words instead of blades. It is
*non-lethal*: nobody loses HP, and the loser is simply convinced. Each side
holds a conviction pool (HP-flavoured but spiritual); each round the acting
side plays a stance, and the other side's current stance resolves the
opposition:

* ``assert``  -- press your view. Beats ``yield`` (opponent buckles), loses to
  ``transcend`` (your assertion is absorbed and reframed).
* ``probe``   -- expose your opponent's footing. Beats ``transcend`` (which is
  exposed as evasion), loses to ``assert`` (a probing question is simply
  overpowered).
* ``transcend`` -- rise above the argument entirely. Beats ``assert``,
  loses to ``probe``. While guarding (first round, or after being probed), it
  also absorbs the next assert.
* ``yield``   -- concede ground: halve incoming pressure this round. Anyone
  may yield; the conviction cost is simply reduced.

Damage (``sway``) is the attacker's **insight** scaled by the stance's
``scaling``, further scaled by the **Dao matchup** (``DaoSystem.matchup``): the
right dao slices through the wrong one in argument as in combat.

Pure logic: no I/O, no UI. ``RNG`` drives every roll so a debate replays
exactly.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from game.core.constants import EventType
from game.models.enemy import Enemy
from game.models.player import Player
from game.systems.dao_system import DaoSystem
from game.utils.rng import RNG

#: The three active debate stances (the rock-paper-scissors triangle) plus the
#: always-available ``yield``. Order matters for tests only.
DEBATE_STANCES = ("assert", "probe", "transcend", "yield")

#: Sway multiplier per stance (like a technique's ``scaling``).
STANCE_SCALING = {"assert": 1.0, "probe": 0.8, "transcend": 1.2, "yield": 0.0}

#: Conviction a side starts with, and the arena's bounds. Sway is insight-based
#: (comprehension-derived), so pools stay small and debates stay short.
DEBATE_MAX_CONVICTION = 6

#: Guard: after a probe, the target's next ``transcend`` is pinned (no absorb).
GUARD_ROUNDS = 1

#: Yield halves incoming sway this round.
YIELD_RESISTANCE = 0.5

#: Sweep: the non-acting side loses one conviction per stage of its insight.
SWEEP_INSIGHT_DIVISOR = 3


class DebateSystem:
    """Resolves individual debate rounds between the player and a foe."""

    #: The stance vocabulary (readable by callers without importing the constant).
    stances = DEBATE_STANCES

    #: Expected exchanges per debate (balance): conviction pools are derived
    #: from each side's insight as ``insight * DEBATE_ROUNDS_TARGET``, so a
    #: debate lasts roughly this many rounds at every stage of progression.
    DEBATE_ROUNDS_TARGET = 5

    def __init__(self, dao: Optional[DaoSystem] = None, rng: Optional[RNG] = None) -> None:
        self._dao = dao
        self._rng = rng or RNG()

    @staticmethod
    def resolve_pools(player_insight: int, foe_insight: int) -> Dict[str, int]:
        """Conviction pools for a debate between these two depths of insight.

        Sway is insight-based, so pools must scale with insight or debates
        collapse to one round late-game. Each pool is ``insight * target``:
        both sides need about ``DEBATE_ROUNDS_TARGET`` good exchanges to win,
        and the *asymmetry* between a shallow foe and a deep player is the
        difficulty dial (stance play, not stat inflation, decides close ones).
        """
        target = DebateSystem.DEBATE_ROUNDS_TARGET
        return {
            "player_conviction": max(6, int(player_insight) * target),
            "foe_conviction": max(6, int(foe_insight) * target),
        }

    # -- state -------------------------------------------------------------
    @staticmethod
    def new_state(
        player_insight: int = 4,
        foe_insight: int = 4,
    ) -> Dict[str, Any]:
        """Fresh transient debate state (rounds, convictions, stances).

        Pools scale with each side's insight (see :meth:`resolve_pools`) so
        debates hold about ``DEBATE_ROUNDS_TARGET`` exchanges at any depth;
        the caller passes the bridged values (the engine mirrors the player's
        comprehension into insight before a debate opens).
        """
        pools = DebateSystem.resolve_pools(player_insight, foe_insight)
        return {
            "rounds": 0,
            "max_rounds": 20,
            "player_conviction": pools["player_conviction"],
            "foe_conviction": pools["foe_conviction"],
            # Starting pools are kept for the UI's conviction bars and tests.
            "initial_player_conviction": pools["player_conviction"],
            "initial_foe_conviction": pools["foe_conviction"],
            "player_stance": "",
            "foe_stance": "",
            # A side "exposed" by a probe (its transcend caught mid-rise) cannot
            # absorb with its *next* transcend: the false calm is broken once.
            "player_exposed": 0,
            "foe_exposed": 0,
        }

    # -- one debate round ----------------------------------------------------
    def round_resolve(
        self,
        player: Player,
        foe: Enemy,
        state: Dict[str, Any],
        player_stance: str,
        foe_stance: str,
    ) -> Dict[str, Any]:
        """Resolve one exchange: both stances are declared; compute sway both ways.

        Returns turn events plus the updated state fields; the caller checks
        the conviction totals for the debate's end.
        """
        state["rounds"] = int(state.get("rounds", 0)) + 1
        events: List[Dict[str, Any]] = [
            {"actor": "PLAYER", "action": "DEBATE_STANCE", "stance": player_stance},
            {"actor": "ENEMY", "action": "DEBATE_STANCE", "stance": foe_stance},
        ]

        # Dao matchup: the right dao cuts through the wrong one in argument.
        player_matchup = self.matchup(getattr(player, "dao_id", None), getattr(foe, "dao_id", None))
        foe_matchup = self.matchup(getattr(foe, "dao_id", None), getattr(player, "dao_id", None))

        # --- the player's stance presses the foe's stance --------------------
        player_sway = self._sway(player, foe, player_stance, foe_stance, state, side="player")
        player_cost = int(round(int(player_sway.get("cost", 0)) * player_matchup))
        if player_cost:
            state["foe_conviction"] = max(0, int(state["foe_conviction"]) - player_cost)
            events.append(
                {
                    "actor": "PLAYER",
                    "action": "DEBATE_PRESS",
                    "stance": player_stance,
                    "cost": int(player_sway["cost"]),
                    "foe_conviction": state["foe_conviction"],
                }
            )
        for extra in player_sway.get("events", []):
            events.append(extra)

        # --- the foe's stance presses back -----------------------------------
        foe_sway = self._sway(foe, player, foe_stance, player_stance, state, side="foe")
        foe_cost = int(round(int(foe_sway.get("cost", 0)) * foe_matchup))
        if foe_cost:
            state["player_conviction"] = max(0, int(state["player_conviction"]) - foe_cost)
            events.append(
                {
                    "actor": "ENEMY",
                    "action": "DEBATE_PRESS",
                    "stance": foe_stance,
                    "cost": int(foe_sway["cost"]),
                    "player_conviction": state["player_conviction"],
                }
            )
        for extra in foe_sway.get("events", []):
            events.append(extra)

        state["player_stance"] = player_stance
        state["foe_stance"] = foe_stance
        return events

    # -- stance resolution -------------------------------------------------
    def _sway(
        self,
        attacker: Any,
        defender: Any,
        stance: str,
        defender_stance: str,
        state: Dict[str, Any],
        side: str,
    ) -> Dict[str, Any]:
        """Compute one side's conviction cost against the opposing stance.

        ``side`` is ``player`` when the *player* attacks (their target fields in
        ``state`` are the foe's); ``foe`` mirrors it.
        """
        cost = 0
        extra: List[Dict[str, Any]] = []
        defender_side = "foe" if side == "player" else "player"
        if stance == "yield":
            return {"cost": 0, "events": extra}
        pressure = self._pressure(attacker, stance)
        if stance == "assert":
            if defender_stance == "transcend":
                # The defender rises above the assertion -- it fails to land --
                # unless their evasion was exposed by a prior probe.
                if int(state.get(f"{defender_side}_exposed", 0)) > 0:
                    state[f"{defender_side}_exposed"] = 0
                    cost = pressure
                else:
                    cost = 0
                    extra.append({"actor": "PLAYER" if side == "player" else "ENEMY", "action": "DEBATE_ABSORBED"})
            else:
                # A declaration overpowers a question and lands on a concession.
                cost = pressure
        elif stance == "probe":
            if defender_stance == "assert":
                cost = 0  # a question does not beat a declaration
            else:
                cost = pressure
                if defender_stance == "transcend":
                    # Caught mid-rise: their next transcend cannot absorb.
                    state[f"{defender_side}_exposed"] = 1
                    extra.append({"actor": "PLAYER" if side == "player" else "ENEMY", "action": "DEBATE_EXPOSED"})
        else:  # transcend
            if defender_stance == "probe":
                cost = 0  # exposed mid-rise before the ascension completes
            else:
                cost = pressure
        cost = int(round(cost * (YIELD_RESISTANCE if defender_stance == "yield" else 1.0)))
        return {"cost": cost, "events": extra}

    def _pressure(self, actor: Any, stance: str) -> int:
        """Sway for ``stance``: the actor's insight scaled by the stance."""
        base = float(STANCE_SCALING.get(stance, 1.0))
        return max(1, int(round(max(1, int(getattr(actor, "insight", 1))) * base)))

    # -- resolution ----------------------------------------------------------
    def outcome(self, state: Dict[str, Any]) -> Optional[str]:
        """``None`` while the debate continues; otherwise its terminal outcome."""
        if int(state["foe_conviction"]) <= 0:
            return "DEBATE_WON"
        if int(state["player_conviction"]) <= 0:
            return "DEBATE_LOST"
        if int(state["rounds"]) >= int(state["max_rounds"]):
            return "DEBATE_STALEMATE"
        return None

    # -- the foe's debate stance ----------------------------------------------
    def foe_stance(self, state: Dict[str, Any]) -> str:
        """Pick the foe's stance for the round (a simple, readable policy).

        A desperate foe (low conviction) yields to protect what remains; an
        assured one presses with assertions and occasional probes; the
        transcend comes out when the foe still holds comfortable ground.
        """
        if int(state["foe_conviction"]) <= 2:
            weights = {"assert": 2, "probe": 1, "transcend": 2, "yield": 3}
        else:
            weights = {"assert": 3, "probe": 2, "transcend": 2, "yield": 1}
        return self._rng.weighted_choice(
            list(weights.keys()), [float(weight) for weight in weights.values()]
        )

    # -- matchup -------------------------------------------------------------
    def matchup(self, player_dao_id: Any, foe_dao_id: Any) -> float:
        """Dao-vs-dao multiplier for a debate exchange (1.0 with no dao system)."""
        if self._dao is None:
            return 1.0
        return float(self._dao.matchup(player_dao_id, foe_dao_id))

    # -- views ---------------------------------------------------------------
    @staticmethod
    def view(state: Dict[str, Any], foe_name: str) -> Dict[str, Any]:
        """UI-safe debate snapshot."""
        return {
            "round": int(state["rounds"]),
            "max_rounds": int(state["max_rounds"]),
            "player_conviction": int(state["player_conviction"]),
            "foe_conviction": int(state["foe_conviction"]),
            "max_conviction": int(state.get("initial_player_conviction", DEBATE_MAX_CONVICTION)),
            "foe_max_conviction": int(state.get("initial_foe_conviction", DEBATE_MAX_CONVICTION)),
            "foe_name": foe_name,
            "player_stance": str(state.get("player_stance", "")),
            "foe_stance": str(state.get("foe_stance", "")),
            "stances": list(DEBATE_STANCES),
        }
