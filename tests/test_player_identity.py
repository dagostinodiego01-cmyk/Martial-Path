"""Player identity: the cultivator's name (engine-owned) and portrait (client).

The name is the engine's, because it is written into every save and into prose;
the portrait belongs to the Godot client. These tests pin both halves of that
split, plus the contract that keeps the roster, the recipe table, the shipped
art, and the provenance manifest in lockstep.

Art arrives in two kinds, and they are held to different standards. A slot is a
*placeholder* until a painting lands in it: a placeholder must be byte-for-byte
what ``tools/gen_avatar_art.py`` draws, so nobody can slip an unfinished file
into an empty slot. Once ``tools/import_avatar_art.py`` has imported a file, the
manifest says so and the tests stop pinning pixels -- a painting is the
artist's, not the test's -- and pin provenance instead: the shipped bytes match
the recorded hash, the crop is inside the source and replays from its recipe,
and it was never upscaled.
"""
from __future__ import annotations

import hashlib
import json
import re
import struct
import zlib
from pathlib import Path

import pytest

from game.api import server
from game.api.server import ActionRequest, NewGameRequest
from game.core.constants import Action, EventType, MODE_COMBAT
from game.core.engine.views import MAX_NAME_LENGTH
from game.core.game_engine import GameEngine
from game.services.save_service import SaveService
from tools import gen_avatar_art
from tools.gen_avatar_art import RECIPES

ROOT = Path(__file__).resolve().parent.parent
AVATAR_DIR = ROOT / "frontend-godot" / "assets" / "avatars"
MANIFEST_PATH = AVATAR_DIR / "art_manifest.json"
PROFILE_SCRIPT = ROOT / "frontend-godot" / "scripts" / "PlayerProfile.gd"

#: The client's largest portrait is 76px (picker well, dossier well, menu well),
#: so a crop under 128px would be drawn upscaled and soft.
MIN_PORTRAIT_SOURCE = 128

#: One `{"id": ..., "name": ..., "gender": ..., "epithet": ...},` row of the
#: client's roster constant.
_ROSTER_ROW = re.compile(
    r'\{"id": "(?P<id>[a-z_]+)", "name": "(?P<name>[^"]+)", "gender": "(?P<gender>male|female)", "epithet":'
)


# --- the engine owns the name ----------------------------------------------


def test_rename_returns_the_new_name_and_updates_state():
    engine = GameEngine.new_game(seed=1)
    result = engine.process_action({"action": "RENAME", "player_name": "Wei Zhen"})

    assert result["event"] == EventType.NAME_CHANGED
    assert result["name"] == "Wei Zhen"
    assert result["narrative"], "the rename must be narrated like every other result"
    assert engine.get_game_state()["player"]["name"] == "Wei Zhen"


def test_rename_normalises_whitespace():
    engine = GameEngine.new_game(seed=1)
    assert engine.process_action({"action": "RENAME", "player_name": "  Wei   Zhen  "})["name"] == "Wei Zhen"


@pytest.mark.parametrize(
    "bad, reason",
    [("", "NAME_EMPTY"), ("   ", "NAME_EMPTY"), ("x" * (MAX_NAME_LENGTH + 1), "NAME_TOO_LONG")],
)
def test_rename_rejects_empty_and_overlong_names(bad, reason):
    engine = GameEngine.new_game(seed=1)
    before = engine.player.name
    result = engine.process_action({"action": "RENAME", "player_name": bad})

    assert result["event"] == EventType.ERROR
    assert result["reason"] == reason
    assert engine.player.name == before, "a rejected name must not be written"


def test_rename_is_accepted_at_the_length_cap():
    engine = GameEngine.new_game(seed=1)
    name = "x" * MAX_NAME_LENGTH
    assert engine.process_action({"action": "RENAME", "player_name": name})["name"] == name


def test_rename_costs_no_turn_in_any_mode():
    """Identity is cosmetic: it must not spend the turn the current mode owns."""
    engine = GameEngine.new_game(seed=1)
    engine._mode = MODE_COMBAT  # noqa: SLF001 (test-only: identity must ignore the mode)

    result = engine.process_action({"action": "RENAME", "player_name": "Blade of Dawn"})

    assert result["event"] == EventType.NAME_CHANGED
    assert engine._mode == MODE_COMBAT  # noqa: SLF001
    assert engine.player.name == "Blade of Dawn"


def test_rename_survives_a_save_and_load(tmp_path):
    engine = GameEngine.new_game(seed=1)
    engine.saves = SaveService(tmp_path)
    engine.process_action({"action": "RENAME", "player_name": "Shen Rui"})
    engine.save_game("identity")

    loaded = GameEngine.new_game(seed=2)
    loaded.saves = SaveService(tmp_path)
    assert loaded.load_game("identity")["success"] is True
    assert loaded.player.name == "Shen Rui"


def test_rename_is_in_the_mode_agnostic_dispatch_table():
    engine = GameEngine.new_game(seed=1)
    assert Action.RENAME in engine._info_dispatch  # noqa: SLF001 (dispatch tables are built per engine)


# --- through the HTTP layer -------------------------------------------------


def test_api_rename_round_trip():
    server.new_game(NewGameRequest(seed=1, player_name="Daoist"))
    result = server.process_action(ActionRequest(action="RENAME", player_name="Ning Que"))

    assert result["event"] == EventType.NAME_CHANGED
    assert server.get_state()["player"]["name"] == "Ning Que"


def test_api_request_carries_the_name_field():
    """A field missing from ActionRequest is silently dropped by pydantic."""
    dumped = ActionRequest(action="RENAME", player_name="Ning Que").model_dump(exclude_none=True)
    assert dumped == {"action": "RENAME", "player_name": "Ning Que"}


# --- the client owns the portrait ------------------------------------------


def test_roster_faces_are_unique_and_well_formed():
    ids = [recipe["id"] for recipe in RECIPES]
    assert len(set(ids)) == len(ids), "two avatars share an id"
    # A picker needs a full cast of each gender; the cast grows with art, never
    # shrinks, so this is a floor rather than an exact count.
    assert sum(1 for r in RECIPES if r["gender"] == "male") >= 10
    assert sum(1 for r in RECIPES if r["gender"] == "female") >= 10
    for recipe in RECIPES:
        assert re.fullmatch(r"[a-z][a-z_]*", recipe["id"]), recipe["id"]
        assert recipe["gender"] in {"male", "female"}, recipe["id"]
        assert recipe["name"] and recipe["epithet"] and recipe["inspiration"]


def test_every_roster_entry_has_committed_art():
    missing = [r["id"] for r in RECIPES if not (AVATAR_DIR / f"{r['id']}.png").is_file()]
    assert missing == [], f"portraits missing: {missing}"
    sidecars = [r["id"] for r in RECIPES if not (AVATAR_DIR / f"{r['id']}.png.import").is_file()]
    assert sidecars == [], f"Godot .import sidecars missing: {sidecars}"


def test_every_avatar_file_is_its_own_image():
    digests = {}
    for recipe in RECIPES:
        digest = hashlib.md5((AVATAR_DIR / f"{recipe['id']}.png").read_bytes()).hexdigest()
        assert digest not in digests, f"{recipe['id']} duplicates {digests[digest]}"
        digests[digest] = recipe["id"]


def test_the_manifest_lists_exactly_the_imported_slots():
    """The manifest is the roster's other half: it splits painted from generated."""
    manifest = _manifest()
    assert set(manifest) == gen_avatar_art.painted_ids()
    roster = {recipe["id"] for recipe in RECIPES}
    assert set(manifest) <= roster, f"art with no roster slot: {set(manifest) - roster}"
    for avatar_id, entry in manifest.items():
        assert entry["art"] == "painted", avatar_id
        assert entry["source"] and entry["source_sha256"] and entry["shipped_sha256"], avatar_id


def test_imported_art_matches_its_provenance():
    """A painting must still be the bytes the manifest says were imported."""
    for avatar_id, entry in _manifest().items():
        shipped = AVATAR_DIR / f"{avatar_id}.png"
        assert _sha256(shipped) == entry["shipped_sha256"], f"{avatar_id} changed since import"
        width, height, colour_type = _png_header(shipped.read_bytes())
        assert (width, height) == (entry["size"], entry["size"]), avatar_id
        assert colour_type == 2, f"{avatar_id} must be 8-bit RGB"


def test_imported_art_records_a_replayable_crop():
    """The manifest's own recipe has to reproduce the crop that shipped.

    Whether a crop frames a face well is a human judgement -- painted
    backgrounds lie to tone detection, so every imported portrait was reviewed
    by eye -- but the *geometry* is checkable: it replays from the recorded
    spec, it stays inside the source, and it holds enough source pixels that the
    client's 76px portrait is not an upscaled blur.
    """
    for avatar_id, entry in _manifest().items():
        spec = entry["spec"]
        crop = entry["crop"]
        source_width, source_height = entry["source_size"]
        short = min(source_width, source_height)
        assert spec["anchor"] in {"face", "top", "center"}, avatar_id
        assert crop["left"] >= 0 and crop["top"] >= 0, avatar_id
        assert crop["left"] + crop["side"] <= source_width, avatar_id
        assert crop["top"] + crop["side"] <= source_height, avatar_id
        assert MIN_PORTRAIT_SOURCE <= crop["side"] <= short, (avatar_id, crop["side"], short)
        # Never upscaled: the shipped square is the crop, capped at the request.
        assert entry["size"] == min(entry["size_cap"], crop["side"]), avatar_id
        if spec["anchor"] in {"top", "center"}:
            assert abs(crop["side"] - round(short * spec["zoom"])) <= 1, avatar_id
            expected_top = 0 if spec["anchor"] == "top" else round((source_height - crop["side"]) / 2)
            nudged = expected_top + round(source_height * spec["top"])
            assert crop["top"] == min(max(nudged, 0), source_height - crop["side"]), avatar_id


def test_unimported_art_is_exactly_what_the_generator_draws():
    """A slot with no imported painting must still be the generator's own output.

    This is what keeps a placeholder honest: it is not merely *an* image, it is
    the image the recipe table draws, so the roster can never quietly ship a
    stranger's half-finished file in an empty slot. (Every slot is painted
    today, so this is a guard rather than a check that currently bites.)
    """
    painted = gen_avatar_art.painted_ids()
    for recipe in [r for r in RECIPES if r["id"] not in painted]:
        assert (AVATAR_DIR / f"{recipe['id']}.png").read_bytes() == gen_avatar_art.render(recipe)


def test_the_generator_draws_each_recipe_its_own_face():
    """The generator stays covered even while every slot carries a painting."""
    digests = set()
    for recipe in RECIPES[:3]:
        payload = gen_avatar_art.render(recipe)
        width, height, colour_type = _png_header(payload)
        assert (width, height) == (256, 256), recipe["id"]
        assert colour_type == 2, f"{recipe['id']} must be 8-bit RGB"
        pixels = _png_pixels(payload)
        face = pixels[132][128]
        skin = tuple(recipe["skin"])
        assert all(abs(face[i] - skin[i]) <= 14 for i in range(3)), (recipe["id"], face, skin)
        samples = {pixels[y][x] for y in range(0, 256, 8) for x in range(0, 256, 8)}
        assert len(samples) > 40, f"{recipe['id']} looks like a flat fill ({len(samples)} shades)"
        assert sum(1 for p in samples if p == (0, 0, 0)) == 0, recipe["id"]
        digests.add(hashlib.md5(payload).hexdigest())
    assert len(digests) == 3, "two recipes drew the same placeholder"


def test_generation_never_overwrites_imported_art(tmp_path, monkeypatch):
    """``--force`` aside, the generator only ever paints empty slots."""
    (tmp_path / "art_manifest.json").write_text(
        json.dumps({"version": 1, "avatars": {"mortal_disciple": {"art": "painted"}}}),
        encoding="utf-8",
    )
    imported = tmp_path / "mortal_disciple.png"
    imported.write_bytes(b"a painting")
    monkeypatch.setattr(gen_avatar_art, "RECIPES", RECIPES[:3])

    outcome = gen_avatar_art.generate(out_dir=tmp_path)

    assert outcome["kept"] == ["mortal_disciple"]
    assert imported.read_bytes() == b"a painting"
    assert outcome["written"] == [r["id"] for r in RECIPES[1:3]]
    for avatar_id in outcome["written"]:
        assert _png_header((tmp_path / f"{avatar_id}.png").read_bytes())[:2] == (256, 256)


def test_generation_is_deterministic():
    from tools.gen_avatar_art import render

    recipe = RECIPES[0]
    assert hashlib.md5(render(recipe)).hexdigest() == hashlib.md5(render(recipe)).hexdigest()


def test_godot_roster_matches_the_recipe_table():
    """The client's AVATARS constant and the generator must not drift."""
    rows = [
        (m.group("id"), m.group("name"), m.group("gender"))
        for m in _ROSTER_ROW.finditer(PROFILE_SCRIPT.read_text(encoding="utf-8"))
    ]
    expected = [(r["id"], r["name"], r["gender"]) for r in RECIPES]
    assert rows == expected


def test_godot_constants_match_the_engine():
    """The client's name rules and defaults are the engine's, not its own."""
    source = PROFILE_SCRIPT.read_text(encoding="utf-8")
    assert re.search(r"const MAX_NAME_LENGTH := %d\b" % MAX_NAME_LENGTH, source)
    assert re.search(r'const DEFAULT_NAME := "Daoist"', source)
    assert server.NewGameRequest().player_name == "Daoist"


# --- helpers ----------------------------------------------------------------


def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))["avatars"]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _png_header(payload: bytes):
    assert payload.startswith(b"\x89PNG\r\n\x1a\n")
    width, height, _bit_depth, colour_type = struct.unpack(">IIBB", payload[16:26])
    return width, height, colour_type


def _png_pixels(payload: bytes):
    """Decode a filter-0 8-bit RGB PNG (what the generator writes)."""
    chunks = []
    offset = 8
    while offset < len(payload):
        length = struct.unpack(">I", payload[offset : offset + 4])[0]
        tag = payload[offset + 4 : offset + 8]
        data = payload[offset + 8 : offset + 8 + length]
        if tag == b"IDAT":
            chunks.append(data)
        offset += 12 + length
    raw = zlib.decompress(b"".join(chunks))
    stride = 256 * 3
    rows = []
    cursor = 0
    for _y in range(256):
        assert raw[cursor] == 0, "the generator must write filter-0 rows"
        cursor += 1
        line = raw[cursor : cursor + stride]
        cursor += stride
        rows.append([tuple(line[x * 3 : x * 3 + 3]) for x in range(256)])
    return rows
