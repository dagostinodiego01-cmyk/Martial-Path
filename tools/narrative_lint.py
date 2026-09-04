"""Standalone narrative-template linter (ROADMAP A.7).

Run from the repo root:

    python tools/narrative_lint.py

Reads ``game/data/narrative_templates.json`` and reports every authoring
problem: undeclared ``{slot}``s, unused ``variables``, unbalanced ``when``
clauses, core verbs below the variant floor, and events with no template.
Exits non-zero when problems are found so it can gate CI.

The checks live in :mod:`game.validation.narrative_lint` so the central data
validator and this tool stay in lockstep; this script is a thin CLI wrapper.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from game.validation.narrative_lint import lint_narrative_templates  # noqa: E402

DATA = ROOT / "game" / "data" / "narrative_templates.json"


def main() -> int:
    templates = json.loads(DATA.read_text(encoding="utf-8"))
    problems = lint_narrative_templates(templates)
    if not problems:
        print("Narrative templates: OK")
        return 0
    for category, message in problems:
        print(f"[{category}] {message}")
    print(f"\n{len(problems)} problem(s) found.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
