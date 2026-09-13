"""Play the game N times and report whether it is actually playable (T.4).

A unit test proves a rule; a playthrough proves the *loop*. This tool drives
fresh, seeded runs with a deterministic policy (no RNG of its own, so the same
seed always produces the same run) and prints the measurements the rework
programme is judged on:

* **survival** -- how many runs were still alive at the action cap, and when the
  dead ones died;
* **pace** -- actions to the first realm and to story tier 2;
* **economy** -- gold and spirit-stone income vs sinks, measured off the state
  between actions rather than guessed from data files;
* **combat** -- fights fought/won/fled, and the per-dao win rate spread;
* **dead actions** -- every refusal the engine handed back, by reason. A high
  rate means the client is offering something the engine will not accept.

The same run engine is reused by the tests: ``run_playthrough`` returns the
action log it played, ``--record`` writes those logs as replay fixtures (T.6),
and ``--json`` prints the summary for a CI job to assert on.

Usage:
    python tools/playthrough_report.py                 # 12 runs, human summary
    python tools/playthrough_report.py --runs 50       # wider sample
    python tools/playthrough_report.py --json          # machine-readable
    python tools/playthrough_report.py --record tests/fixtures/replay_logs
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from game.core.constants import Action, EventType  # noqa: E402
from game.core.game_engine import GameEngine  # noqa: E402
from game.data.registry import GameDataRegistry  # noqa: E402

#: Bump when the policy changes: recorded replay fixtures carry it so a log
#: played back by an older policy is visibly stale rather than silently wrong.
POLICY_VERSION = "policy-v1"

DEFAULT_RUNS = 12
DEFAULT_MAX_ACTIONS = 200
DEFAULT_SEED_BASE = 1
SPIRIT_STONE_ID = "spirit_stone"

#: Event names that mean "a fight is running". ``COMBAT`` opens one,
#: ``COMBAT_END`` closes it, with ``COMBAT_TURN`` for the rounds between.
_COMBAT_EVENTS = {EventType.COMBAT, EventType.COMBAT_TURN, EventType.COMBAT_END}

#: Outcomes the engine reports from ``_end_combat``.
_COMBAT_OUTCOMES = {"VICTORY", "DEFEAT", "FLED", "ESCAPED", "STALEMATE"}

# None: every engine refusal counts as a dead action. The policy only asks for
# options the state says are available (reachable exits, available encounter
# choices), so a refusal is a real gap between what the client offers and what
# the engine accepts -- not something to be explained away by an allow-list.


@dataclass
class RunOutcome:
    """Everything one seeded run measured."""

    seed: int
    actions_used: int
    survived: bool
    player_name: str = "Sim"
    died_at: Optional[int] = None
    final_age_years: float = 0.0
    first_realm_at: Optional[int] = None
    story_tier_2_at: Optional[int] = None
    max_story_tier: int = 1
    body_realms_gained: int = 0
    gold_income: int = 0
    gold_sink: int = 0
    stone_income: int = 0
    stone_sink: int = 0
    fights: int = 0
    wins: int = 0
    losses: int = 0
    flees: int = 0
    refusals: Counter = field(default_factory=Counter)
    dao_fights: Counter = field(default_factory=Counter)
    dao_wins: Counter = field(default_factory=Counter)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    events: List[str] = field(default_factory=list)
    final_state_sha256: str = ""

    @property
    def dead_actions(self) -> int:
        """Refused actions: the client offered something the engine would not take."""
        return sum(self.refusals.values())


class Policy:
    """A deterministic player: same state in, same action out.

    Deliberately blunt -- it spends strain, stabilises, breaks through, trains,
    explores for content, gathers where the ground allows, and walks the reachable
    exits in order. That is enough to exercise every one of those verbs; the
    point is to measure the loop, not to play well.
    """

    #: The non-cultivation intents, cycled in order whenever no priority rule
    #: fires. Travel appears often enough that a run actually walks the map --
    #: story tier 2 is only reachable by leaving the starting woods.
    _INTENTS = ("train", "explore", "train", "gather", "train", "travel")

    def __init__(self) -> None:
        self.step = 0
        self.intent_cursor = 0
        self.exit_cursor = 0
        self.visited: List[str] = []

    # -- entry ------------------------------------------------------------
    def choose(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.step += 1
        mode = str(state.get("mode") or "explore")
        if mode == "combat":
            return self._combat(state)
        if mode == "encounter":
            return self._encounter(state)
        if mode == "debate":
            return {"action": Action.DEBATE_STANCE, "stance": "assert"}
        return self._explore(state)

    # -- per-mode rules ---------------------------------------------------
    def _combat(self, state: Dict[str, Any]) -> Dict[str, Any]:
        player = state.get("player", {})
        hp = int(player.get("hp", 0))
        max_hp = max(1, int(player.get("max_hp", 1)))
        if hp * 100 <= max_hp * 30:
            return {"action": Action.FLEE}
        for skill in player.get("skills", []):
            if not isinstance(skill, dict) or str(skill.get("type", "")) != "active":
                continue
            if bool(skill.get("affordable", True)) and int(skill.get("cooldown_remaining", 0)) == 0:
                return {"action": Action.USE_SKILL, "skill_id": str(skill.get("id", ""))}
        return {"action": Action.ATTACK}

    def _encounter(self, state: Dict[str, Any]) -> Dict[str, Any]:
        encounter = state.get("encounter") or {}
        for option in encounter.get("options", []):
            if isinstance(option, dict) and bool(option.get("available", False)):
                return {"action": Action.ENCOUNTER_CHOICE, "choice_id": str(option.get("choice_id", ""))}
        return {"action": Action.ENCOUNTER_CHOICE, "choice_id": ""}

    def _explore(self, state: Dict[str, Any]) -> Dict[str, Any]:
        player = state.get("player", {})
        cultivation = player.get("cultivation_state", {})
        body = cultivation.get("body_transformation", {})
        essence = cultivation.get("essence_gathering", {})
        hp = int(player.get("hp", 0))
        max_hp = max(1, int(player.get("max_hp", 1)))

        if bool(state.get("awaiting_fate_acceptance", False)):
            return {"action": Action.ACCEPT_STARTING_FATE}
        if hp * 100 <= max_hp * 40:
            return {"action": Action.REST}
        if bool(self._gates(body).get("can_attempt", False)):
            return {"action": Action.BODY_BREAKTHROUGH}
        if self._strained(body):
            return {"action": Action.STABILISE_FOUNDATION}
        if bool(player.get("essence_unlocked", False)):
            if bool(self._gates(essence).get("can_attempt", False)):
                return {"action": Action.ESSENCE_BREAKTHROUGH}
            if self._strained(essence):
                return {"action": Action.STABILISE_ESSENCE}
        intent = self._next_intent()
        if intent == "explore":
            return {"action": Action.EXPLORE}
        if intent == "gather" and bool(state.get("gathering_available", False)):
            return {"action": Action.GATHER}
        if intent == "travel":
            destination = self._next_destination(state)
            if destination:
                return {"action": Action.TRAVEL, "location_id": destination}
        if float(body.get("progress", 0.0)) < float(body.get("required_progress", 100.0)):
            return {"action": Action.TRAIN_BODY}
        return {"action": Action.TRAIN_ESSENCE}

    def _next_intent(self) -> str:
        intent = self._INTENTS[self.intent_cursor % len(self._INTENTS)]
        self.intent_cursor += 1
        return intent

    @staticmethod
    def _gates(track: Dict[str, Any]) -> Dict[str, Any]:
        gates = track.get("breakthrough", {}) if isinstance(track, dict) else {}
        return gates if isinstance(gates, dict) else {}

    @classmethod
    def _strained(cls, track: Dict[str, Any]) -> bool:
        """True once strain is in the zone where a breakthrough would be refused."""
        gates = cls._gates(track)
        numbers = gates.get("gates", {}) if isinstance(gates.get("gates"), dict) else {}
        strain = float(numbers.get("strain", 0.0))
        ceiling = float(numbers.get("max_allowed_strain", 45.0) or 45.0)
        return strain >= ceiling * 0.8

    def _next_destination(self, state: Dict[str, Any]) -> str:
        """The next exit to walk.

        Prefers somewhere new (that is how story tier 2 opens, since the starting
        woods only border tier-1 ground), then round-robins the reachable exits so
        a long run keeps moving rather than bouncing between two neighbours.
        """
        reachable = [
            str(destination.get("id", ""))
            for destination in state.get("destinations", [])
            if isinstance(destination, dict) and bool(destination.get("reachable", False))
        ]
        if not reachable:
            return ""
        current = str(state.get("location", {}).get("id", ""))
        for location_id in reachable:
            if location_id and location_id != current and location_id not in self.visited:
                self.visited.append(location_id)
                self.exit_cursor = reachable.index(location_id) + 1
                return location_id
        pick = reachable[self.exit_cursor % len(reachable)]
        self.exit_cursor += 1
        return "" if pick == current and len(reachable) == 1 else pick


def _stones(state: Dict[str, Any]) -> int:
    total = 0
    for item in state.get("inventory_items", []):
        if isinstance(item, dict) and str(item.get("item_id", "")) == SPIRIT_STONE_ID:
            total += int(item.get("count", 0))
    return total


def _body_realm(state: Dict[str, Any]) -> str:
    player = state.get("player", {})
    cultivation = player.get("cultivation_state", {})
    return str(cultivation.get("body_transformation", {}).get("realm_id", ""))


def state_digest(state: Dict[str, Any]) -> str:
    """A stable hash of the whole state, for replay comparison (T.6)."""
    payload = json.dumps(state, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def run_playthrough(
    seed: int,
    max_actions: int = DEFAULT_MAX_ACTIONS,
    player_name: str = "Sim",
    dao_id: Optional[str] = None,
) -> RunOutcome:
    """Play one fresh run with the deterministic policy and measure it.

    ``dao_id`` forces the starting dao. That is a *measurement* switch, not a
    rule: awakening a dao sets exactly ``player.dao_id``, so pinning it lets the
    same seeds be played once per dao and compared on equal footing.
    """
    engine = GameEngine.new_game(player_name=player_name, seed=seed)
    if dao_id:
        engine.player.dao_id = str(dao_id)
    outcome = RunOutcome(seed=seed, actions_used=0, survived=True, player_name=player_name)
    policy = Policy()
    state = engine.get_game_state()
    starting_realm = _body_realm(state)
    gold = int(state.get("player", {}).get("gold", 0))
    stones = _stones(state)
    in_fight = False
    fight_dao = ""

    for step in range(1, max_actions + 1):
        if not bool(state.get("running", True)):
            outcome.survived = False
            outcome.died_at = outcome.died_at or step - 1
            break
        action = policy.choose(state)
        result = engine.process_action(dict(action))
        outcome.actions.append(_jsonable(action))
        event = str(result.get("event", ""))
        outcome.events.append(event)
        outcome.actions_used = step

        # -- refusals ------------------------------------------------------
        if event == EventType.ERROR:
            outcome.refusals[str(result.get("reason", "UNKNOWN"))] += 1
        if event == EventType.PLAYER_DIED:
            outcome.survived = False
            outcome.died_at = step

        # -- combat --------------------------------------------------------
        if event in _COMBAT_EVENTS and not in_fight:
            in_fight = True
            fight_dao = str(state.get("player", {}).get("dao_id", "") or "none")
            outcome.fights += 1
            outcome.dao_fights[fight_dao] += 1
        if in_fight and str(result.get("outcome", "")) in {"VICTORY", "DEFEAT", "FLED", "ESCAPED", "STALEMATE"}:
            outcome_payload = str(result.get("outcome"))
            in_fight = False
            if outcome_payload == "VICTORY":
                outcome.wins += 1
                outcome.dao_wins[fight_dao] += 1
            elif outcome_payload in {"FLED", "ESCAPED"}:
                outcome.flees += 1
            else:
                outcome.losses += 1
        elif in_fight and event == EventType.COMBAT_END:
            in_fight = False

        # -- state deltas --------------------------------------------------
        state = engine.get_game_state()
        gold_now = int(state.get("player", {}).get("gold", 0))
        stones_now = _stones(state)
        outcome.gold_income += max(0, gold_now - gold)
        outcome.gold_sink += max(0, gold - gold_now)
        outcome.stone_income += max(0, stones_now - stones)
        outcome.stone_sink += max(0, stones - stones_now)
        gold, stones = gold_now, stones_now

        realm_now = _body_realm(state)
        if realm_now != starting_realm and outcome.first_realm_at is None:
            outcome.first_realm_at = step
        outcome.body_realms_gained = 1 if (realm_now != starting_realm) else 0
        tier_now = int(state.get("player", {}).get("max_story_tier", 1) or 1)
        outcome.max_story_tier = max(outcome.max_story_tier, tier_now)
        if tier_now >= 2 and outcome.story_tier_2_at is None:
            outcome.story_tier_2_at = step

    outcome.final_age_years = float(state.get("player", {}).get("age_years", 0.0) or 0.0)
    outcome.final_state_sha256 = state_digest(state)
    return outcome


def collect_render_payloads(
    seed: int,
    max_actions: int = 120,
    player_name: str = "Smoke",
) -> Dict[str, Any]:
    """Play one run and keep the payloads the Godot smoke check renders (T.5).

    Returns three real states -- the opening one (``enemy`` and ``encounter`` both
    null, the pair that used to crash the client on NEW GAME), the first combat
    state, and the first pending-encounter state -- plus one result payload per
    distinct event the run produced. All of it is engine output: the smoke check
    feeds the client what the client will actually receive.
    """
    engine = GameEngine.new_game(player_name=player_name, seed=seed)
    policy = Policy()
    states: Dict[str, Any] = {}
    seen: Dict[str, Any] = {}
    state = engine.get_game_state()
    states["explore"] = state

    for _ in range(max_actions):
        if not bool(state.get("running", True)):
            break
        action = policy.choose(state)
        result = engine.process_action(dict(action))
        seen.setdefault(str(result.get("event", "")), result)
        state = engine.get_game_state()
        if "combat" not in states and bool(state.get("in_combat", False)) and isinstance(state.get("enemy"), dict):
            states["combat"] = state
        if "encounter" not in states and isinstance(state.get("encounter"), dict):
            states["encounter"] = state
        if len(states) == 3 and len(seen) >= 40:
            break

    return {"player_name": player_name, "seed": seed, "states": states, "events": list(seen.values())}


def _jsonable(action: Dict[str, Any]) -> Dict[str, Any]:
    """Actions use ``Action`` StrEnum members; store plain strings."""
    return {key: (str(value) if isinstance(value, Action) else value) for key, value in action.items()}


def summarise(outcomes: List[RunOutcome]) -> Dict[str, Any]:
    """Fold the per-run measurements into the report."""
    alive = [run for run in outcomes if run.survived]
    deaths = [run for run in outcomes if not run.survived]
    first_realm = [run.first_realm_at for run in outcomes if run.first_realm_at is not None]
    tier_two = [run.story_tier_2_at for run in outcomes if run.story_tier_2_at is not None]
    actions = sum(run.actions_used for run in outcomes)
    refusals = Counter()
    for run in outcomes:
        refusals.update(run.refusals)

    dao_fights: Counter = Counter()
    dao_wins: Counter = Counter()
    for run in outcomes:
        dao_fights.update(run.dao_fights)
        dao_wins.update(run.dao_wins)
    dao_spread = {
        dao: {
            "fights": dao_fights[dao],
            "wins": dao_wins[dao],
            "win_rate": round(dao_wins[dao] / dao_fights[dao], 3),
        }
        for dao in sorted(dao_fights)
    }

    def _median(values: List[int]) -> Optional[float]:
        return float(statistics.median(values)) if values else None

    return {
        "policy": POLICY_VERSION,
        "runs": len(outcomes),
        "actions": actions,
        "survival": {
            "alive": len(alive),
            "died": len(deaths),
            "death_actions": sorted(run.died_at for run in deaths if run.died_at is not None),
        },
        "pace": {
            "actions_to_first_realm_median": _median(first_realm),
            "actions_to_first_realm_min": min(first_realm) if first_realm else None,
            "actions_to_first_realm_max": max(first_realm) if first_realm else None,
            "runs_reaching_first_realm": len(first_realm),
            "actions_to_story_tier_2_median": _median(tier_two),
            "runs_reaching_story_tier_2": len(tier_two),
            "final_age_years_median": _median([int(run.final_age_years) for run in outcomes]),
            "max_story_tier": max((run.max_story_tier for run in outcomes), default=1),
        },
        "economy": {
            "gold_income": sum(run.gold_income for run in outcomes),
            "gold_sink": sum(run.gold_sink for run in outcomes),
            "stone_income": sum(run.stone_income for run in outcomes),
            "stone_sink": sum(run.stone_sink for run in outcomes),
        },
        "combat": {
            "fights": sum(run.fights for run in outcomes),
            "wins": sum(run.wins for run in outcomes),
            "losses": sum(run.losses for run in outcomes),
            "flees": sum(run.flees for run in outcomes),
            "win_rate": round(sum(run.wins for run in outcomes) / max(1, sum(run.fights for run in outcomes)), 3),
        },
        "dao_spread": dao_spread,
        "dead_actions": {
            "count": sum(refusals.values()),
            "rate": round(sum(refusals.values()) / max(1, actions), 4),
            "top_reasons": refusals.most_common(10),
        },
    }


def format_report(summary: Dict[str, Any]) -> str:
    """The human summary: one line per measurement, numbers only from the run."""
    survival = summary["survival"]
    pace = summary["pace"]
    economy = summary["economy"]
    combat = summary["combat"]
    dead = summary["dead_actions"]

    def number(value: Optional[float]) -> str:
        return "-" if value is None else f"{value:g}"

    lines = [
        "Martial Path - playthrough report",
        f"  {summary['policy']} | {summary['runs']} seeded runs | {summary['actions']} actions",
        "",
        f"  survival       {survival['alive']}/{summary['runs']} alive at the action cap"
        + (f" (deaths at {', '.join(str(a) for a in survival['death_actions'])})" if survival["died"] else ""),
        f"  first realm    {number(pace['actions_to_first_realm_median'])} actions median"
        f" (min {number(pace['actions_to_first_realm_min'])}, max {number(pace['actions_to_first_realm_max'])})"
        f" | {pace['runs_reaching_first_realm']}/{summary['runs']} reached",
        f"  story tier 2   {number(pace['actions_to_story_tier_2_median'])} actions median"
        f" | {pace['runs_reaching_story_tier_2']}/{summary['runs']} reached",
        f"  lifespan       {number(pace['final_age_years_median'])} years median at the cap",
        f"  economy        gold +{economy['gold_income']} / -{economy['gold_sink']}"
        f" | stones +{economy['stone_income']} / -{economy['stone_sink']}",
        f"  combat         {combat['fights']} fights | {combat['wins']} won ({combat['win_rate']:.0%})"
        f" | {combat['flees']} fled | {combat['losses']} lost",
        f"  dead actions   {dead['count']}/{summary['actions']} ({dead['rate']:.1%})",
    ]
    for reason, count in dead["top_reasons"]:
        lines.append(f"                 {reason} x{count}")
    if summary["dao_spread"]:
        spread = " | ".join(
            f"{dao} {data['win_rate']:.0%} ({data['fights']})" for dao, data in summary["dao_spread"].items()
        )
        lines.append(f"  dao spread     {spread}")
    else:
        lines.append("  dao spread     no fights recorded")
    return "\n".join(lines)


def record_logs(directory: Path, outcomes: List[RunOutcome]) -> List[Path]:
    """Write each run's action log as a replay fixture for the determinism test."""
    directory.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []
    for run in outcomes:
        payload = {
            "policy": POLICY_VERSION,
            "seed": run.seed,
            # The name is part of the state, so a replay has to use the same one.
            "player_name": run.player_name,
            "actions": run.actions,
            "events": run.events,
            "actions_used": run.actions_used,
            "final_state_sha256": run.final_state_sha256,
        }
        path = directory / f"seed_{run.seed}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append(path)
    return written


def format_dao_spread(spread: Dict[str, Dict[str, Any]], runs_per_dao: int) -> str:
    """The balance readout: the same seeds played once per dao.

    A dao with no fights is reported as ``no fights`` rather than as a 0% or 100%
    win rate, so an untested dao cannot masquerade as a measured one.
    """
    lines = [
        "dao win-rate spread",
        f"  {runs_per_dao} run(s) per dao, identical seeds and policy",
        "  dao                 fights   wins   win rate   dead actions   first realm (median)",
    ]
    for dao, data in spread.items():
        combat = data["combat"]
        pace = data["pace"]
        rate = f"{combat['win_rate']:.0%}" if combat["fights"] else "n/a"
        first = pace["actions_to_first_realm_median"]
        first_text = "-" if first is None else f"{first:g}"
        lines.append(
            f"  {dao:<18} {combat['fights']:>6} {combat['wins']:>6}   {rate:>8}   "
            f"{data['dead_actions']['rate']:>12.1%}   {first_text:>17}"
        )
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic playthrough report (T.4).")
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS, help="how many fresh runs to play")
    parser.add_argument("--seed-base", type=int, default=DEFAULT_SEED_BASE, help="first seed (runs are seed_base..+n)")
    parser.add_argument("--max-actions", type=int, default=DEFAULT_MAX_ACTIONS, help="action cap per run")
    parser.add_argument("--json", action="store_true", help="print the summary as JSON")
    parser.add_argument("--record", type=Path, help="write each run's action log here (replay fixtures)")
    parser.add_argument(
        "--dao",
        default="",
        help="comma-separated dao ids: play the seed sweep once per dao and report the spread",
    )
    parser.add_argument(
        "--max-dead-rate",
        type=float,
        default=None,
        help="exit non-zero when the dead-action rate exceeds this (CI gate)",
    )
    arguments = parser.parse_args(argv)

    seeds = [arguments.seed_base + index for index in range(max(1, arguments.runs))]
    dao_ids = [entry.strip() for entry in arguments.dao.split(",") if entry.strip()]

    if dao_ids:
        known = {str(entry.get("id", "")) for entry in GameDataRegistry.load().daos}
        unknown = [dao for dao in dao_ids if dao not in known]
        if unknown:
            print(f"FAIL: unknown dao id(s): {', '.join(unknown)}", file=sys.stderr)
            return 2
        spread = {
            dao: summarise(
                [
                    run_playthrough(seed=seed, max_actions=arguments.max_actions, dao_id=dao)
                    for seed in seeds
                ]
            )
            for dao in dao_ids
        }
        payload = {
            "policy": POLICY_VERSION,
            "runs_per_dao": len(seeds),
            "dao_spread": {
                dao: {
                    "combat": data["combat"],
                    "pace": data["pace"],
                    "survival": data["survival"],
                    "dead_actions": data["dead_actions"],
                    "economy": data["economy"],
                }
                for dao, data in spread.items()
            },
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False) if arguments.json else format_dao_spread(spread, len(seeds)))
        worst = max(data["dead_actions"]["rate"] for data in spread.values())
        if arguments.max_dead_rate is not None and worst > arguments.max_dead_rate:
            print(f"FAIL: dead-action rate {worst:.1%} exceeds the {arguments.max_dead_rate:.1%} budget", file=sys.stderr)
            return 1
        return 0

    outcomes = [
        run_playthrough(seed=seed, max_actions=arguments.max_actions)
        for seed in seeds
    ]
    summary = summarise(outcomes)

    if arguments.record:
        written = record_logs(arguments.record, outcomes)
        print(f"recorded {len(written)} replay log(s) in {arguments.record}")

    print(json.dumps(summary, indent=2, ensure_ascii=False) if arguments.json else format_report(summary))

    if arguments.max_dead_rate is not None and summary["dead_actions"]["rate"] > arguments.max_dead_rate:
        print(
            f"FAIL: dead-action rate {summary['dead_actions']['rate']:.1%} "
            f"exceeds the {arguments.max_dead_rate:.1%} budget",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
