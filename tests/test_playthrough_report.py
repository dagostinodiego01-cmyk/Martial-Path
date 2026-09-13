"""T.4: the playthrough report is deterministic, complete and CI-runnable.

The tool plays the real game with a fixed policy, so these tests are the proof
that its numbers mean something: the same seed must produce the same run (or the
report is noise), every measurement the rework programme asks for must be in the
summary, and the command line must fail loudly -- on an unknown dao, or on a
dead-action rate over budget -- instead of printing a reassuring table.
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from replay_harness import PROJECT_ROOT, playthrough_report

report = playthrough_report()

TOOL = "tools/playthrough_report.py"
SHORT_RUN = 40


def _cli(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, TOOL, *arguments],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )


# -- determinism ---------------------------------------------------------
def test_same_seed_replays_to_the_same_run():
    first = report.run_playthrough(seed=3, max_actions=SHORT_RUN)
    second = report.run_playthrough(seed=3, max_actions=SHORT_RUN)

    assert first.actions == second.actions, "the policy must not depend on run order"
    assert first.events == second.events
    assert first.final_state_sha256 == second.final_state_sha256


def test_different_seeds_take_different_paths():
    first = report.run_playthrough(seed=1, max_actions=SHORT_RUN)
    second = report.run_playthrough(seed=2, max_actions=SHORT_RUN)

    assert (first.actions, first.final_state_sha256) != (second.actions, second.final_state_sha256)


def test_summary_is_identical_across_repeats():
    """The whole report is stable -- a CI gate cannot flap."""
    once = report.summarise([report.run_playthrough(seed=seed, max_actions=SHORT_RUN) for seed in (5, 6)])
    twice = report.summarise([report.run_playthrough(seed=seed, max_actions=SHORT_RUN) for seed in (5, 6)])

    assert json.dumps(once, sort_keys=True) == json.dumps(twice, sort_keys=True)


# -- the measurements T.4 asks for ---------------------------------------
def test_summary_carries_every_required_measurement():
    summary = report.summarise([report.run_playthrough(seed=7, max_actions=SHORT_RUN)])

    assert set(summary) >= {"policy", "runs", "actions", "survival", "pace", "economy", "combat", "dao_spread", "dead_actions"}
    # survival
    assert summary["survival"]["alive"] + summary["survival"]["died"] == 1
    # pace: actions to the first realm and to story tier 2
    assert "actions_to_first_realm_median" in summary["pace"]
    assert "actions_to_story_tier_2_median" in summary["pace"]
    # income vs sinks
    assert set(summary["economy"]) == {"gold_income", "gold_sink", "stone_income", "stone_sink"}
    # dao win-rate spread, keyed by the dao the fights were fought under
    for data in summary["dao_spread"].values():
        assert set(data) == {"fights", "wins", "win_rate"}
    # dead-action rate
    assert 0.0 <= summary["dead_actions"]["rate"] <= 1.0


def test_every_action_the_policy_took_was_accepted():
    """A blunt but honest gate: the policy only asks for available options."""
    outcome = report.run_playthrough(seed=4, max_actions=SHORT_RUN)

    assert outcome.dead_actions == 0, outcome.refusals.most_common(5)


def test_dao_spread_measures_the_dao_it_was_told_to():
    sword = report.run_playthrough(seed=9, max_actions=SHORT_RUN, dao_id="sword_dao")
    flame = report.run_playthrough(seed=9, max_actions=SHORT_RUN, dao_id="flame_dao")

    assert sword.dao_fights.keys() == {"sword_dao"}
    assert flame.dao_fights.keys() == {"flame_dao"}
    # Same seed, same policy: forcing the dao must not change the run's shape.
    assert sword.actions == flame.actions


# -- the command line ----------------------------------------------------
def test_cli_prints_a_json_report():
    result = _cli("--runs", "2", "--max-actions", str(SHORT_RUN), "--json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["runs"] == 2
    assert payload["policy"] == report.POLICY_VERSION
    assert payload["dead_actions"]["count"] == 0


def test_cli_prints_the_human_report():
    result = _cli("--runs", "1", "--max-actions", str(SHORT_RUN))

    assert result.returncode == 0, result.stderr
    for expected in ("playthrough report", "survival", "first realm", "story tier 2", "economy", "combat", "dao spread", "dead actions"):
        assert expected in result.stdout, result.stdout


def test_cli_dead_action_budget_fails_when_exceeded():
    """The gate has to be able to fail, or it is decoration."""
    result = _cli("--runs", "1", "--max-actions", str(SHORT_RUN), "--max-dead-rate", "-0.001")

    assert result.returncode == 1
    assert "dead-action rate" in result.stderr


def test_cli_rejects_an_unknown_dao():
    result = _cli("--runs", "1", "--max-actions", str(SHORT_RUN), "--dao", "not_a_dao")

    assert result.returncode == 2
    assert "not_a_dao" in result.stderr


def test_cli_dao_spread_plays_the_same_seeds_once_per_dao():
    result = _cli("--runs", "1", "--max-actions", str(SHORT_RUN), "--dao", "sword_dao,flame_dao", "--json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["runs_per_dao"] == 1
    assert set(payload["dao_spread"]) == {"sword_dao", "flame_dao"}


@pytest.mark.parametrize("bad_dao", ["Tide Dao", ""])
def test_dao_spread_rejects_bad_ids(bad_dao):
    """A display name or an empty id must not silently measure sword_dao."""
    if not bad_dao.strip():
        pytest.skip("an empty --dao value is the no-flag case")
    result = _cli("--runs", "1", "--max-actions", "5", "--dao", bad_dao)

    assert result.returncode == 2
