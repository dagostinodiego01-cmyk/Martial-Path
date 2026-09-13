"""Artwork coverage for the shipped world map.

The Godot location panel loads ``frontend-godot/assets/locations/<location_id>.png``
and falls back to a bare name label when the file is missing (see
``MainController._load_location_texture``). A location without art therefore looks
broken in the client even though the engine happily routes the player there, which
is exactly what happened when the expansion added 16 places and nobody drew them.

These tests pin the 1:1 contract between ``game/data/locations.json`` and the art
folder. They read PNG headers only, so they stay fast.
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCATIONS = ROOT / "game" / "data" / "locations.json"
ART_DIR = ROOT / "frontend-godot" / "assets" / "locations"

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _location_ids():
    return {entry["id"] for entry in json.loads(LOCATIONS.read_text(encoding="utf-8"))}


def _art_files():
    return {path.stem for path in ART_DIR.glob("*.png")}


def test_every_location_has_artwork():
    missing = sorted(_location_ids() - _art_files())
    assert not missing, (
        "locations with no PNG in frontend-godot/assets/locations (run "
        f"`python tools/gen_missing_location_art.py`, then replace with real art): {missing}"
    )


def test_no_orphan_artwork():
    orphans = sorted(_art_files() - _location_ids())
    assert not orphans, f"art files that match no location id (stale renames?): {orphans}"


def test_art_files_are_valid_pngs():
    for location_id in sorted(_art_files()):
        path = ART_DIR / f"{location_id}.png"
        header = path.read_bytes()[:33]
        assert header[:8] == PNG_MAGIC, f"{path.name} is not a PNG"
        width, height = struct.unpack(">II", header[16:24])
        assert width >= 256 and height >= 256, f"{path.name} is {width}x{height}, too small to render"
        assert path.stat().st_size > 4096, f"{path.name} is suspiciously small"


def test_every_art_file_has_a_godot_import_sidecar():
    """Without the sidecar the editor reimports; with a stale one the panel shows nothing."""
    for location_id in sorted(_art_files()):
        sidecar = ART_DIR / f"{location_id}.png.import"
        assert sidecar.exists(), f"{sidecar.name} missing; open the project in Godot to regenerate it"
        text = sidecar.read_text(encoding="utf-8")
        assert f'source_file="res://assets/locations/{location_id}.png"' in text, sidecar.name
