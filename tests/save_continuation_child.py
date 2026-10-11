"""Subprocess half of the SV.5 fresh-process continuation test.

Run by ``tests/test_save_continuation.py`` as a *separate Python process* with
an intentionally unrelated construction seed. Everything the run needs -- the
real seed, all five RNG streams, the seed-derived world variation, cooldowns,
the pending scene state -- must come back out of the save, or the event
sequence this process emits will diverge from the original run's tail.

Usage: save_continuation_child.py SAVE_DIR SLOT ACTIONS_JSON OUT_JSON
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from game.core.game_engine import GameEngine  # noqa: E402
from game.services.save_service import SaveService  # noqa: E402
from replay_harness import playthrough_report  # noqa: E402


def main() -> int:
    save_dir, slot, actions_path, out_path = sys.argv[1:5]
    actions = json.loads(Path(actions_path).read_text(encoding="utf-8"))["actions"]

    # Deliberately the wrong seed: a correct load must overwrite it with the
    # seed stored in the save, along with every RNG stream's state.
    engine = GameEngine.new_game(player_name="Continuation Child", seed=987654321)
    engine.saves = SaveService(save_dir)
    loaded = engine.load_game(slot)
    if not loaded.get("success"):
        print(f"load failed: {loaded}", file=sys.stderr)
        return 1

    events = [str(engine.process_action(dict(action)).get("event", "")) for action in actions]
    digest = playthrough_report().state_digest(engine.get_game_state())
    Path(out_path).write_text(json.dumps({"events": events, "digest": digest}), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
