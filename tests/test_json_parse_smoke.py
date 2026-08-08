"""Smoke test: every JSON file under ``game/data/`` parses.

A single malformed comma or trailing brace in a data file can break the whole
game at load time. Parsing each file individually keeps that failure obvious and
localised to the offending file rather than surfacing deep inside a system.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

import pytest

_DATA_ROOT = Path(__file__).resolve().parent.parent / "game" / "data"


def _json_files() -> List[Path]:
    return sorted(_DATA_ROOT.rglob("*.json"))


@pytest.mark.parametrize(
    "json_path",
    _json_files(),
    ids=lambda path: str(path.relative_to(_DATA_ROOT)),
)
def test_data_json_parses(json_path: Path) -> None:
    with json_path.open(encoding="utf-8") as handle:
        json.load(handle)
