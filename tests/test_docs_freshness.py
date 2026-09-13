"""T.3: the live counts in handover.md cannot rot.

The header used to claim "840 passing" while the suite ran 848, and section 5
claimed 780 -- both true once, both wrong by the time anyone read them. Now the
numbers are generated between markers and this file is the gate: it fails when
the block drifts, and when a hand-typed count reappears in the live part of the
document. Dated history sections are exempt on purpose -- they are a log.

Fix either failure with:

    python tools/refresh_docs.py
"""

from __future__ import annotations

import subprocess
import sys

from replay_harness import PROJECT_ROOT, load_tool

docs = load_tool("refresh_docs", "tools/refresh_docs.py")

HANDOVER_TEXT = (PROJECT_ROOT / "handover.md").read_text(encoding="utf-8")


def test_generated_block_matches_the_repository():
    """Runs the same check CI runs: counts, validator, sweep, block content."""
    result = subprocess.run(
        [sys.executable, "tools/refresh_docs.py", "--check"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )

    assert result.returncode == 0, (
        "handover.md is stale -- run: python tools/refresh_docs.py\n" + result.stdout + result.stderr
    )


def test_no_hand_typed_counts_in_the_live_document():
    offenders = docs.hand_typed_counts(HANDOVER_TEXT)

    assert offenders == [], "hand-typed counts (generate them instead): " + "; ".join(offenders)


def test_the_block_is_the_only_place_the_counts_live():
    """The generated block is present, and every count in it is a number."""
    block = docs.current_block(HANDOVER_TEXT)

    assert block.startswith(docs.BEGIN_MARKER)
    assert block.rstrip().endswith(docs.END_MARKER)
    for label, value in docs.compute_counts().items():
        assert f"| {label} | {value} |" in block


def test_a_stale_block_is_detected():
    """The gate has to be able to fail: change a number and it must notice."""
    block = docs.current_block(HANDOVER_TEXT)
    stale = block.replace("| 0 |", "| 1 |", 1)
    tampered = HANDOVER_TEXT.replace(block, stale)

    assert docs.current_block(tampered) != docs.render_block(docs.compute_counts())


def test_missing_markers_are_an_error_not_a_silent_pass():
    import pytest

    with pytest.raises(RuntimeError):
        docs.current_block("no markers here")


def test_dated_history_sections_are_exempt_but_live_prose_is_not():
    history = (
        "## 3. Recent work (2026-08-14, the close-out)\n\n"
        "### Combat & skills\n\n"
        "- Suite: 605 passed, 3 skipped.\n"
    )
    live = "## 5. Testing & validation\n\n- `pytest -q` -- 780 passed, 3 skipped.\n"

    assert docs.hand_typed_counts(history) == []
    assert docs.hand_typed_counts(live) == ["- `pytest -q` -- 780 passed, 3 skipped."]
