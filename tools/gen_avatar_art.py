"""Generate the 20 selectable player-avatar portraits (pure stdlib).

The Godot client lets the player name their cultivator and wear one of twenty
portraits -- ten male, ten female -- each a stock archetype of the cultivation
web-novel canon (the mortal-born disciple who claws his way up, the cold sword
immortal, the nine-tailed fox spirit, the sect mistress on her jade mountain).
Hand-painted art can replace any of these files later without touching code: the
filename is the contract (``frontend-godot/assets/avatars/<id>.png``), and the
roster in ``frontend-godot/scripts/PlayerProfile.gd`` names the same ids.

Every portrait is drawn deterministically from the recipe table below -- flat
paper-cut geometry in the game's own lacquer/gold palette, at 256x256, with a
matching Godot ``.import`` sidecar so the editor picks the art up without a
rescan. Regenerate with:

    python tools/gen_avatar_art.py

``tests/test_player_identity.py`` pins the roster contract (ids, gender split,
distinct art, the GDScript roster matching this table).

These PNGs are **placeholders**: flat paper-cut geometry with no rendering, kept
so the picker is playable end to end. Real painted portraits replace them
file-for-file (same id, same directory) -- ``python tools/gen_avatar_art.py
--brief`` writes the art spec and a per-character prompt sheet (`
game/docs/AVATAR_BRIEF.md``) for producing that art.
"""
from __future__ import annotations

import hashlib
import json
import math
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "frontend-godot" / "assets" / "avatars"

SIZE = 256
SS = 2  # supersample factor: draw big, average down for cheap anti-aliasing
_CANVAS = SIZE * SS

Res = "res://assets/avatars/%s.png"

# --- Recipe table -----------------------------------------------------------
# Each entry is one portrait. ``hair`` picks a hairstyle, ``accessories`` a list
# of props; both are keys into the draw functions further down. Colours are RGB
# triples. ``inspiration`` records where the archetype comes from (provenance).
RECIPES = [
    # -- male -------------------------------------------------------------
    {
        "id": "mortal_disciple", "name": "Mortal Disciple", "gender": "male",
        "epithet": "A village boy who refused to stay mortal.",
        "inspiration": "Han Li (A Record of a Mortal's Journey to Immortality)",
        "skin": (226, 189, 152), "hair": (28, 24, 24), "eyes": (86, 58, 38),
        "robe": (78, 84, 96), "robe_dark": (52, 57, 67), "inner": (206, 200, 186),
        "trim": (168, 138, 84), "aura": (78, 96, 116),
        "hair_style": "topknot", "accessories": ["gourd"], "lips": (166, 106, 92),
    },
    {
        "id": "sword_immortal", "name": "Sword Immortal", "gender": "male",
        "epithet": "One blade, one lifetime of cold light.",
        "inspiration": "the sword-dao immortal (Zhu Xian, Li Qiye)",
        "skin": (233, 206, 180), "hair": (226, 231, 238), "eyes": (110, 158, 196),
        "robe": (238, 240, 244), "robe_dark": (196, 204, 216), "inner": (120, 156, 190),
        "trim": (120, 178, 214), "aura": (96, 138, 178),
        "hair_style": "long_straight", "accessories": ["sword_hilt"], "lips": (176, 124, 118),
    },
    {
        "id": "azure_prodigy", "name": "Azure Prodigy", "gender": "male",
        "epithet": "A genius who stunned three sects in one night.",
        "inspiration": "Xiao Yan (Battle Through the Heavens)",
        "skin": (222, 180, 140), "hair": (24, 20, 20), "eyes": (198, 138, 52),
        "robe": (44, 42, 50), "robe_dark": (28, 27, 33), "inner": (196, 168, 108),
        "trim": (198, 156, 70), "aura": (150, 84, 48),
        "hair_style": "wild", "accessories": ["flame"], "lips": (150, 92, 78),
    },
    {
        "id": "demon_path_heir", "name": "Demon Path Heir", "gender": "male",
        "epithet": "Power taken, never granted.",
        "inspiration": "Ye Xiao (Against the Gods), the demonic heir",
        "skin": (216, 190, 176), "hair": (18, 16, 20), "eyes": (198, 60, 56),
        "robe": (26, 24, 30), "robe_dark": (16, 15, 19), "inner": (128, 40, 44),
        "trim": (176, 58, 54), "aura": (128, 34, 40),
        "hair_style": "long_straight", "accessories": ["horns", "mask"], "lips": (150, 66, 62),
    },
    {
        "id": "alchemist_sage", "name": "Alchemist Sage", "gender": "male",
        "epithet": "A furnace, a gourd, and infinite patience.",
        "inspiration": "Meng Hao (I Shall Seal the Heavens)",
        "skin": (228, 192, 156), "hair": (46, 36, 28), "eyes": (96, 122, 74),
        "robe": (54, 82, 62), "robe_dark": (36, 58, 44), "inner": (198, 190, 162),
        "trim": (150, 168, 104), "aura": (74, 112, 82),
        "hair_style": "bun", "accessories": ["gourd", "beads"], "lips": (162, 108, 92),
    },
    {
        "id": "dharma_monk", "name": "Dharma Monk", "gender": "male",
        "epithet": "The staff is heavy; so is mercy.",
        "inspiration": "the scripture-bearing ascetic (Journey to the West)",
        "skin": (196, 152, 116), "hair": (30, 26, 24), "eyes": (92, 66, 44),
        "robe": (196, 148, 62), "robe_dark": (150, 106, 42), "inner": (222, 176, 96),
        "trim": (138, 96, 40), "aura": (176, 128, 64),
        "hair_style": "bald", "accessories": ["beads"], "lips": (150, 96, 78),
    },
    {
        "id": "thunder_sovereign", "name": "Thunder Sovereign", "gender": "male",
        "epithet": "The heavens answer him in lightning.",
        "inspiration": "Ji Ning (Desolate Era), the lightning sovereign",
        "skin": (226, 190, 156), "hair": (30, 26, 40), "eyes": (216, 186, 92),
        "robe": (84, 62, 118), "robe_dark": (58, 42, 86), "inner": (196, 190, 214),
        "trim": (188, 192, 206), "aura": (110, 92, 170),
        "hair_style": "high_ponytail", "accessories": ["headband"], "lips": (156, 104, 96),
    },
    {
        "id": "beast_blood_hunter", "name": "Beast-Blood Hunter", "gender": "male",
        "epithet": "He learned the mountain by surviving it.",
        "inspiration": "Chu Feng (Monster Paradise), the beast hunter",
        "skin": (206, 162, 122), "hair": (72, 50, 32), "eyes": (104, 142, 84),
        "robe": (92, 66, 46), "robe_dark": (64, 46, 32), "inner": (128, 106, 76),
        "trim": (150, 122, 78), "aura": (108, 96, 66),
        "hair_style": "wild", "accessories": ["fur_mantle", "scar"], "lips": (146, 88, 76),
    },
    {
        "id": "young_master", "name": "Young Master", "gender": "male",
        "epithet": "Born to gold, tested by fire.",
        "inspiration": "the sect young master of a thousand novels",
        "skin": (232, 200, 172), "hair": (26, 22, 24), "eyes": (74, 52, 40),
        "robe": (150, 40, 44), "robe_dark": (108, 28, 34), "inner": (226, 208, 168),
        "trim": (206, 166, 74), "aura": (176, 66, 58),
        "hair_style": "bun", "accessories": ["crown"], "lips": (170, 100, 92),
    },
    {
        "id": "wandering_swordsman", "name": "Wandering Swordsman", "gender": "male",
        "epithet": "No sect, no master -- only the road.",
        "inspiration": "the rogue cultivator (Zhu Xian's wanderers)",
        "skin": (214, 174, 136), "hair": (34, 28, 26), "eyes": (78, 70, 58),
        "robe": (58, 52, 46), "robe_dark": (40, 36, 32), "inner": (146, 60, 52),
        "trim": (142, 116, 72), "aura": (96, 78, 62),
        "hair_style": "ponytail", "accessories": ["headband", "sword_hilt", "scar"], "lips": (150, 94, 82),
    },
    {
        "id": "sect_patriarch", "name": "Sect Patriarch", "gender": "male",
        "epithet": "Three generations of disciples have never seen him stand.",
        "inspiration": "the venerable ancestor on his jade throne",
        "skin": (226, 196, 174), "hair": (232, 234, 238), "eyes": (156, 116, 196),
        "robe": (78, 56, 122), "robe_dark": (52, 36, 84), "inner": (208, 204, 212),
        "trim": (190, 160, 84), "aura": (120, 98, 170),
        "hair_style": "long_straight", "accessories": ["crown", "beard"], "lips": (170, 116, 110),
    },
    # -- female -----------------------------------------------------------
    {
        "id": "sword_maiden", "name": "Sword Maiden", "gender": "female",
        "epithet": "Her blade hums before she draws it.",
        "inspiration": "the sword maiden (Ning Caichen's lineage, Zhu Xian)",
        "skin": (238, 208, 186), "hair": (186, 200, 214), "eyes": (96, 146, 190),
        "robe": (236, 240, 246), "robe_dark": (194, 204, 218), "inner": (128, 168, 202),
        "trim": (124, 180, 216), "aura": (104, 148, 184),
        "hair_style": "long_straight", "accessories": ["hairpin"], "lips": (198, 118, 118),
    },
    {
        "id": "nine_tailed_fox", "name": "Nine-Tailed Fox", "gender": "female",
        "epithet": "A fox spirit who smiles at heaven.",
        "inspiration": "Bai Qian / the huli jing spirit",
        "skin": (244, 216, 198), "hair": (232, 234, 240), "eyes": (214, 168, 66),
        "robe": (240, 238, 240), "robe_dark": (206, 198, 206), "inner": (176, 56, 62),
        "trim": (176, 56, 62), "aura": (196, 132, 138),
        "hair_style": "long_straight", "accessories": ["fox_ears", "fox_tail"], "lips": (206, 104, 104),
    },
    {
        "id": "jade_sect_mistress", "name": "Jade Sect Mistress", "gender": "female",
        "epithet": "She rules a mountain and its silence.",
        "inspiration": "Nangong Wan (A Will Eternal's elders)",
        "skin": (234, 202, 178), "hair": (30, 28, 30), "eyes": (96, 158, 128),
        "robe": (72, 132, 106), "robe_dark": (48, 96, 78), "inner": (218, 216, 190),
        "trim": (198, 168, 92), "aura": (86, 148, 120),
        "hair_style": "bun", "accessories": ["crown", "hairpin"], "lips": (186, 106, 106),
    },
    {
        "id": "moon_palace_fairy", "name": "Moon Palace Fairy", "gender": "female",
        "epithet": "Cold light, cold palace, a warm heart.",
        "inspiration": "Chang'e of the Guanghan Palace",
        "skin": (240, 216, 206), "hair": (226, 224, 234), "eyes": (150, 158, 190),
        "robe": (222, 228, 240), "robe_dark": (182, 192, 214), "inner": (206, 212, 226),
        "trim": (206, 210, 226), "aura": (140, 152, 194),
        "hair_style": "hime", "accessories": ["crescent"], "lips": (196, 132, 142),
    },
    {
        "id": "phoenix_heiress", "name": "Phoenix Heiress", "gender": "female",
        "epithet": "Fire remembers her bloodline.",
        "inspiration": "the Vermillion Bird heir (Xiao Xun'er's line)",
        "skin": (240, 204, 176), "hair": (172, 48, 40), "eyes": (216, 158, 62),
        "robe": (162, 40, 44), "robe_dark": (114, 26, 32), "inner": (232, 196, 138),
        "trim": (216, 172, 78), "aura": (200, 92, 56),
        "hair_style": "long_straight", "accessories": ["feather", "crown"], "lips": (206, 96, 92),
    },
    {
        "id": "poison_valley_disciple", "name": "Poison Valley Disciple", "gender": "female",
        "epithet": "Sweetness with a bitter end.",
        "inspiration": "the medicine-poison valley disciple",
        "skin": (232, 200, 186), "hair": (32, 26, 34), "eyes": (152, 96, 176),
        "robe": (86, 52, 112), "robe_dark": (60, 36, 82), "inner": (172, 196, 150),
        "trim": (150, 190, 122), "aura": (124, 78, 158),
        "hair_style": "twin_tails", "accessories": ["vial"], "lips": (188, 100, 124),
    },
    {
        "id": "ice_phoenix_princess", "name": "Ice Phoenix Princess", "gender": "female",
        "epithet": "Winter answers when she speaks.",
        "inspiration": "the ice phoenix bloodline (Douluo Dalu)",
        "skin": (236, 220, 216), "hair": (206, 232, 244), "eyes": (120, 186, 216),
        "robe": (168, 208, 226), "robe_dark": (126, 168, 194), "inner": (232, 242, 248),
        "trim": (206, 238, 250), "aura": (150, 202, 226),
        "hair_style": "hime", "accessories": ["snowflake"], "lips": (192, 132, 148),
    },
    {
        "id": "beast_girl_tamer", "name": "Beast Tamer", "gender": "female",
        "epithet": "The wolves came when she called.",
        "inspiration": "Xiao Wu (Soul Land)",
        "skin": (232, 196, 162), "hair": (92, 60, 38), "eyes": (206, 132, 58),
        "robe": (150, 116, 74), "robe_dark": (112, 84, 54), "inner": (196, 176, 142),
        "trim": (176, 146, 96), "aura": (168, 128, 78),
        "hair_style": "braid", "accessories": ["fox_ears", "fur_mantle"], "lips": (186, 108, 96),
    },
    {
        "id": "rogue_swordswoman", "name": "Rogue Swordswoman", "gender": "female",
        "epithet": "She left the sect and took the blade.",
        "inspiration": "the rogue swordswoman (Zhu Xian, Snow Eagle Lord)",
        "skin": (224, 184, 152), "hair": (34, 28, 30), "eyes": (88, 74, 62),
        "robe": (56, 50, 48), "robe_dark": (38, 34, 33), "inner": (152, 54, 50),
        "trim": (150, 122, 82), "aura": (104, 82, 70),
        "hair_style": "ponytail", "accessories": ["headband", "sword_hilt", "scar"], "lips": (176, 96, 96),
    },
    {
        "id": "dragon_princess", "name": "Dragon Princess", "gender": "female",
        "epithet": "The tide itself bows to her.",
        "inspiration": "the Dragon Palace princess (Ao bloodlines)",
        "skin": (232, 208, 186), "hair": (32, 74, 72), "eyes": (108, 190, 172),
        "robe": (46, 118, 122), "robe_dark": (30, 84, 90), "inner": (214, 224, 196),
        "trim": (198, 172, 92), "aura": (66, 148, 146),
        "hair_style": "long_straight", "accessories": ["dragon_horns", "crown"], "lips": (190, 112, 110),
    },
]

BY_ID = {recipe["id"]: recipe for recipe in RECIPES}


def _rgb(value) -> tuple:
    return (int(value[0]), int(value[1]), int(value[2]))


def _shade(color, factor: float) -> tuple:
    """Lighten (factor > 1) or darken (factor < 1) a colour."""
    return tuple(max(0, min(255, int(channel * factor))) for channel in color)


def _mix(a, b, t: float) -> tuple:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# --- Raster canvas ----------------------------------------------------------


class Canvas:
    """A tiny float-alpha RGB raster with the primitives the portraits need.

    All public coordinates are in 256-space; the canvas itself is drawn at
    ``SS``x that and averaged down at write time.
    """

    def __init__(self) -> None:
        self.px = bytearray(_CANVAS * _CANVAS * 3)

    # -- pixel access -----------------------------------------------------
    def blend(self, x: int, y: int, color, alpha: float) -> None:
        if alpha <= 0.0 or x < 0 or y < 0 or x >= _CANVAS or y >= _CANVAS:
            return
        i = (y * _CANVAS + x) * 3
        if alpha >= 1.0:
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]
            return
        inv = 1.0 - alpha
        self.px[i] = int(self.px[i] * inv + color[0] * alpha + 0.5)
        self.px[i + 1] = int(self.px[i + 1] * inv + color[1] * alpha + 0.5)
        self.px[i + 2] = int(self.px[i + 2] * inv + color[2] * alpha + 0.5)

    # -- geometry helpers -------------------------------------------------
    @staticmethod
    def _span(a: float, b: float) -> tuple:
        return int(math.floor(a * SS)), int(math.ceil(b * SS))

    def ellipse(self, cx, cy, rx, ry, color, alpha: float = 1.0, clip=None) -> None:
        color = _rgb(color)
        if clip is not None:
            x0, y0 = max(cx - rx, clip[0]), max(cy - ry, clip[1])
            x1, y1 = min(cx + rx, clip[2]), min(cy + ry, clip[3])
        else:
            x0, y0, x1, y1 = cx - rx, cy - ry, cx + rx, cy + ry
        px0, py0 = self._span(x0, y0)
        px1, py1 = self._span(x1, y1)
        px0, py0 = max(px0, 0), max(py0, 0)
        px1, py1 = min(px1, _CANVAS - 1), min(py1, _CANVAS - 1)
        inv_rx2, inv_ry2 = 1.0 / (rx * rx), 1.0 / (ry * ry)
        for y in range(py0, py1 + 1):
            dy = (y + 0.5) / SS - cy
            t = dy * dy * inv_ry2
            if t >= 1.0:
                continue
            half = rx * math.sqrt(1.0 - t)
            xa = max(px0, int(math.floor((cx - half) * SS)))
            xb = min(px1, int(math.ceil((cx + half) * SS)))
            for x in range(xa, xb + 1):
                self.blend(x, y, color, alpha)

    def ring(self, cx, cy, rx, ry, thickness: float, color, alpha: float = 1.0) -> None:
        color = _rgb(color)
        inner = 1.0 - thickness / max(1.0, (rx + ry) / 2.0)
        px0, py0 = self._span(cx - rx, cy - ry)
        px1, py1 = self._span(cx + rx, cy + ry)
        inv_rx2, inv_ry2 = 1.0 / (rx * rx), 1.0 / (ry * ry)
        for y in range(max(py0, 0), min(py1, _CANVAS - 1) + 1):
            dy = (y + 0.5) / SS - cy
            dy2 = dy * dy * inv_ry2
            if dy2 > 1.0:
                continue
            for x in range(max(px0, 0), min(px1, _CANVAS - 1) + 1):
                dx = (x + 0.5) / SS - cx
                d = math.sqrt(dx * dx * inv_rx2 + dy2)
                if inner <= d <= 1.0:
                    self.blend(x, y, color, alpha)

    def poly(self, points, color, alpha: float = 1.0, clip=None) -> None:
        color = _rgb(color)
        ys = [p[1] for p in points]
        py0, py1 = self._span(min(ys), max(ys))
        py0, py1 = max(py0, 0), min(py1, _CANVAS - 1)
        count = len(points)
        for y in range(py0, py1 + 1):
            yy = (y + 0.5) / SS
            crossings = []
            for i in range(count):
                ax, ay = points[i]
                bx, by = points[(i + 1) % count]
                if (ay <= yy < by) or (by <= yy < ay):
                    crossings.append(ax + (yy - ay) / (by - ay) * (bx - ax))
            crossings.sort()
            for i in range(0, len(crossings) - 1, 2):
                xa, xb = self._span(crossings[i], crossings[i + 1])
                if clip is not None:
                    xa, xb = max(xa, int(math.ceil(clip[0] * SS))), min(xb, int(math.floor(clip[2] * SS)))
                for x in range(max(xa, 0), min(xb, _CANVAS - 1) + 1):
                    self.blend(x, y, color, alpha)

    def capsule(self, p0, p1, width: float, color, alpha: float = 1.0) -> None:
        color = _rgb(color)
        radius = width / 2.0
        (ax, ay), (bx, by) = p0, p1
        dx, dy = bx - ax, by - ay
        length_sq = dx * dx + dy * dy
        px0, py0 = self._span(min(ax, bx) - radius, min(ay, by) - radius)
        px1, py1 = self._span(max(ax, bx) + radius, max(ay, by) + radius)
        for y in range(max(py0, 0), min(py1, _CANVAS - 1) + 1):
            py = (y + 0.5) / SS
            for x in range(max(px0, 0), min(px1, _CANVAS - 1) + 1):
                pxx = (x + 0.5) / SS
                if length_sq <= 1e-9:
                    t = 0.0
                else:
                    t = ((pxx - ax) * dx + (py - ay) * dy) / length_sq
                    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
                ex = pxx - (ax + t * dx)
                ey = py - (ay + t * dy)
                if ex * ex + ey * ey <= radius * radius:
                    self.blend(x, y, color, alpha)

    def background(self, top, bottom, glow, center=(128, 116), radius: float = 130.0) -> None:
        top, bottom, glow = _rgb(top), _rgb(bottom), _rgb(glow)
        for y in range(_CANVAS):
            t = y / (_CANVAS - 1)
            base = (top[0] + (bottom[0] - top[0]) * t,
                    top[1] + (bottom[1] - top[1]) * t,
                    top[2] + (bottom[2] - top[2]) * t)
            for x in range(_CANVAS):
                d = math.hypot(x / SS - center[0], y / SS - center[1]) / radius
                w = max(0.0, 1.0 - d * d) * 0.55
                i = (y * _CANVAS + x) * 3
                self.px[i] = int(base[0] + (glow[0] - base[0]) * w)
                self.px[i + 1] = int(base[1] + (glow[1] - base[1]) * w)
                self.px[i + 2] = int(base[2] + (glow[2] - base[2]) * w)

    def to_rgb_rows(self) -> bytes:
        counts = SS * SS
        rows = bytearray()
        scale = 1.0 / counts
        for y in range(SIZE):
            rows.append(0)
            for x in range(SIZE):
                r = g = b = 0
                for sy in range(SS):
                    base = ((y * SS + sy) * _CANVAS + x * SS) * 3
                    for sx in range(SS):
                        i = base + sx * 3
                        r += self.px[i]
                        g += self.px[i + 1]
                        b += self.px[i + 2]
                rows += bytes((int(r * scale), int(g * scale), int(b * scale)))
        return bytes(rows)


# --- Geometry of one portrait (all coordinates in 256-space) ----------------
FACE = (128.0, 132.0, 43.0, 50.0)  # cx, cy, rx, ry
EYE_Y = 138.0
HEAD_TOP = 82.0
TORSO_TOP = 206.0


def _draw_backdrop(c: Canvas, r: dict) -> None:
    aura = r["aura"]
    # Bright enough to read as a portrait at 52px in the top rail, dark enough
    # to sit inside a lacquer panel without glowing.
    c.background(_shade(aura, 0.36), _shade(aura, 0.12), _shade(aura, 1.25), radius=150.0)
    # A gold hairline medallion behind the head: the portrait framing language.
    c.ring(128, 116, 96, 96, 2.0, _shade(r["trim"], 1.15), 0.38)
    c.ring(128, 116, 88, 88, 1.0, _shade(r["trim"], 1.3), 0.22)
    c.ellipse(128, 118, 88, 88, _shade(aura, 0.24), 0.5)


def _draw_hair_mass(c: Canvas, r: dict) -> None:
    """Hair behind the head and over the shoulders (drawn before the face)."""
    style = r["hair_style"]
    hair = r["hair"]
    dark = _shade(hair, 0.72)
    if style in ("long_straight", "hime", "twin_tails", "braid", "ponytail"):
        c.ellipse(128, 128, 56, 66, dark, 1.0)
        c.ellipse(128, 132, 53, 63, hair, 1.0)


def _draw_torso(c: Canvas, r: dict) -> None:
    robe, darkside, inner, trim = r["robe"], r["robe_dark"], r["inner"], r["trim"]
    # Shoulders: a wide ellipse whose top half reads as the robe silhouette.
    c.ellipse(128, 340, 116, 132, darkside)
    c.ellipse(128, 336, 110, 128, robe)
    # Sash / waist band across the bottom of the frame.
    c.poly([(18, 236), (238, 236), (238, 262), (18, 262)], _shade(trim, 0.95), 0.9)
    c.poly([(18, 236), (238, 236), (238, 242), (18, 242)], _shade(trim, 1.2), 0.8)
    # Crossed lapels: two panels converging under the throat.
    c.poly([(96, 200), (128, 214), (128, 300), (74, 236)], inner, 1.0)
    c.poly([(160, 200), (128, 214), (128, 300), (182, 236)], _shade(inner, 0.9), 1.0)
    c.capsule((100, 202), (128, 214), 3.0, trim, 0.95)
    c.capsule((156, 202), (128, 214), 3.0, trim, 0.95)
    c.capsule((128, 214), (128, 300), 2.0, _shade(trim, 0.8), 0.55)
    # Collar band rising to the throat.
    c.poly([(106, 196), (150, 196), (154, 216), (102, 216)], _shade(inner, 1.05), 1.0)


def _draw_hair_front(c: Canvas, r: dict) -> None:
    style = r["hair_style"]
    hair = r["hair"]
    dark = _shade(hair, 0.7)
    if style == "bald":
        c.ellipse(FACE[0], FACE[1] - 12, FACE[2] * 0.82, FACE[3] * 0.72, _shade(r["skin"], 0.93), 0.5)
        return
    # Cap: the top of the head, clipped so it never covers the brow line.
    c.ellipse(128, 108, 48, 46, dark, 1.0, clip=(72, 40, 184, 118))
    c.ellipse(128, 106, 46, 44, hair, 1.0, clip=(72, 38, 184, 114))
    # Fringe: a few locks dipping over the forehead.
    c.poly([(84, 106), (98, 96), (108, 116), (120, 98), (134, 114), (148, 96), (160, 110), (172, 104), (172, 82), (84, 82)],
           hair, 1.0)
    if style == "wild":
        for x0, tip in ((92, 58), (120, 48), (150, 60)):
            c.poly([(x0, 84), (tip, 44), (x0 + 22, 84)], hair, 1.0)
    # Side locks framing the cheeks (front layer).
    c.capsule((88, 104), (80, 162), 13.0, dark, 1.0)
    c.capsule((168, 104), (176, 162), 13.0, dark, 1.0)
    c.capsule((88, 100), (81, 152), 9.0, hair, 1.0)
    c.capsule((168, 100), (175, 152), 9.0, hair, 1.0)
    if style in ("long_straight", "hime"):
        # Long falls over the shoulders, drawn after the torso.
        c.capsule((84, 150), (76, 226), 22.0, dark, 1.0)
        c.capsule((172, 150), (180, 226), 22.0, dark, 1.0)
        c.capsule((85, 152), (79, 222), 16.0, hair, 1.0)
        c.capsule((171, 152), (177, 222), 16.0, hair, 1.0)
    if style == "hime":
        c.poly([(86, 104), (104, 104), (98, 148), (80, 148)], hair, 1.0)
        c.poly([(170, 104), (152, 104), (158, 148), (176, 148)], hair, 1.0)
    if style == "topknot":
        _draw_knot(c, r, 128, 62, 15.0)
        c.capsule((112, 74), (144, 74), 7.0, dark, 1.0)
    if style == "bun":
        c.ellipse(128, 60, 18, 17, dark, 1.0)
        c.ellipse(128, 58, 15, 15, hair, 1.0)
        c.capsule((110, 72), (146, 72), 6.0, _shade(hair, 0.85), 1.0)
    if style == "high_ponytail":
        c.ellipse(146, 62, 15, 14, dark, 1.0)
        c.ellipse(146, 60, 13, 12, hair, 1.0)
        c.capsule((150, 58), (196, 26), 15.0, dark, 1.0)
        c.capsule((150, 58), (194, 28), 10.0, hair, 1.0)
    if style == "ponytail":
        c.ellipse(172, 104, 14, 13, dark, 1.0)
        c.capsule((176, 106), (190, 208), 19.0, dark, 1.0)
        c.capsule((176, 106), (188, 204), 13.0, hair, 1.0)
    if style == "twin_tails":
        for sign in (-1, 1):
            x = 128 + sign * 52
            c.ellipse(x, 100, 14, 13, dark, 1.0)
            c.capsule((x, 104), (x + sign * 26, 198), 20.0, dark, 1.0)
            c.capsule((x, 104), (x + sign * 25, 194), 14.0, hair, 1.0)
            c.ellipse(x + sign * 26, 200, 11, 11, hair, 1.0)
    if style == "braid":
        c.capsule((80, 112), (74, 210), 18.0, hair, 1.0)
        for i in range(5):
            c.ellipse(75 - i * 0.6, 128 + i * 20, 11 - i * 0.8, 9 - i * 0.6, dark, 0.55)


def _draw_knot(c: Canvas, r: dict, cx: float, cy: float, size: float) -> None:
    hair = r["hair"]
    c.ellipse(cx, cy, size, size * 0.94, _shade(hair, 0.7), 1.0)
    c.ellipse(cx, cy - 1, size * 0.82, size * 0.8, hair, 1.0)


def _draw_face(c: Canvas, r: dict) -> None:
    skin, hair, eyes = r["skin"], r["hair"], r["eyes"]
    shadow = _shade(skin, 0.88)
    cx, cy, rx, ry = FACE
    # Ears, then head, then a jaw wedge so the silhouette is not a plain egg.
    c.ellipse(cx - rx + 2, cy + 4, 9, 12, shadow, 1.0)
    c.ellipse(cx + rx - 2, cy + 4, 9, 12, shadow, 1.0)
    c.ellipse(cx, cy, rx, ry, skin, 1.0)
    c.poly([(cx - 30, cy + 28), (cx + 30, cy + 28), (cx + 20, cy + 52), (cx - 20, cy + 52)], skin, 1.0)
    c.ellipse(cx, cy + 6, rx * 0.93, ry * 0.93, skin, 1.0)
    # Cheek warmth.
    for sign in (-1, 1):
        c.ellipse(cx + sign * 27, cy + 18, 10, 6, (206, 128, 118), 0.18)
    # Eyes: flat almond, dark lid, bright iris.
    for sign in (-1, 1):
        ex = cx + sign * 17
        c.ellipse(ex, EYE_Y, 10, 6, (250, 248, 244), 1.0)
        c.ellipse(ex, EYE_Y + 1, 6.4, 6.0, eyes, 1.0)
        c.ellipse(ex, EYE_Y + 1, 3.0, 3.2, _shade(eyes, 0.45), 1.0)
        c.ellipse(ex - 2, EYE_Y - 2, 1.6, 1.4, (255, 255, 255), 0.75)
        c.capsule((ex - 10, EYE_Y - 5), (ex + 10, EYE_Y - 6), 2.4, _shade(hair, 0.55), 0.95)
        c.capsule((ex - 9, EYE_Y - 15), (ex + 9, EYE_Y - 17), 3.0, _shade(hair, 0.7), 0.9)
    # Nose and mouth.
    c.capsule((cx, cy + 8), (cx, cy + 16), 2.0, shadow, 0.8)
    c.capsule((cx - 7, cy + 26), (cx + 7, cy + 26), 2.6, r["lips"], 0.95)
    c.capsule((cx - 3, cy + 29), (cx + 3, cy + 28), 1.6, _shade(r["lips"], 0.8), 0.5)


def _draw_neck(c: Canvas, r: dict) -> None:
    skin = r["skin"]
    c.poly([(114, 168), (142, 168), (146, 212), (110, 212)], _shade(skin, 0.9), 1.0)
    c.ellipse(128, 176, 19, 12, _shade(skin, 0.82), 0.55)


# --- Accessories ------------------------------------------------------------


def _acc_crown(c: Canvas, r: dict) -> None:
    gold = (216, 178, 88)
    c.poly([(96, 96), (160, 96), (156, 76), (146, 88), (136, 70), (128, 86), (120, 70), (110, 88), (100, 76)], gold, 1.0)
    c.capsule((94, 96), (162, 96), 7.0, gold, 1.0)
    c.ellipse(128, 94, 7, 7, r["aura"], 1.0)
    c.ellipse(128, 93, 4, 4, _shade(r["aura"], 1.6), 1.0)


def _acc_headband(c: Canvas, r: dict) -> None:
    band = _shade(r["trim"], 1.05)
    c.capsule((84, 100), (172, 100), 9.0, band, 1.0)
    c.capsule((84, 98), (172, 98), 3.0, _shade(band, 1.25), 0.85)
    c.capsule((172, 100), (186, 112), 7.0, band, 1.0)


def _acc_hairpin(c: Canvas, r: dict) -> None:
    gold = (222, 186, 96)
    c.capsule((98, 84), (144, 66), 3.4, gold, 1.0)
    c.ellipse(144, 65, 5.5, 5.5, r["aura"], 1.0)
    c.ellipse(146, 64, 2.5, 2.5, (250, 244, 224), 0.8)


def _acc_fox_ears(c: Canvas, r: dict) -> None:
    hair = r["hair"]
    for sign in (-1, 1):
        x = 128 + sign * 26
        c.poly([(x - 15, 84), (x + sign * 6, 40), (x + 17, 80)], _shade(hair, 0.82), 1.0)
        c.poly([(x - 9, 80), (x + sign * 5, 52), (x + 11, 78)], (222, 158, 168), 0.9)


def _acc_horns(c: Canvas, r: dict) -> None:
    for sign in (-1, 1):
        x = 128 + sign * 28
        c.capsule((x, 88), (x + sign * 20, 40), 13.0, (58, 44, 46), 1.0)
        c.capsule((x, 88), (x + sign * 18, 48), 8.0, (96, 74, 72), 1.0)
        for i in range(3):
            t = 0.25 + i * 0.25
            c.capsule((x + sign * 20 * t - 6, 88 - 48 * t), (x + sign * 20 * t + 6, 88 - 48 * t), 3.0, (44, 32, 34), 0.8)


def _acc_dragon_horns(c: Canvas, r: dict) -> None:
    for sign in (-1, 1):
        x = 128 + sign * 24
        c.capsule((x, 86), (x + sign * 14, 46), 10.0, (210, 224, 200), 1.0)
        c.capsule((x + sign * 14, 46), (x + sign * 34, 34), 7.0, (216, 232, 208), 1.0)
        c.capsule((x + sign * 4, 62), (x + sign * 26, 52), 3.5, (176, 196, 168), 0.9)


def _acc_crescent(c: Canvas, r: dict) -> None:
    silver = (226, 230, 240)
    c.ring(128, 46, 26, 26, 9.0, silver, 0.95)
    c.ellipse(140, 50, 20, 20, _shade(r["aura"], 0.22), 0.85)


def _acc_feather(c: Canvas, r: dict) -> None:
    c.capsule((150, 62), (198, 26), 7.0, (206, 74, 48), 1.0)
    for i in range(5):
        t = i / 5.0
        x = 152 + 46 * t
        y = 60 - 34 * t
        c.capsule((x, y), (x + 16, y - 12), 5.0, (232, 148, 66), 0.85)
        c.capsule((x, y), (x + 12, y + 12), 4.0, (216, 96, 56), 0.7)
    c.ellipse(198, 26, 5.0, 5.0, (244, 206, 120), 1.0)


def _acc_snowflake(c: Canvas, r: dict) -> None:
    cx, cy = 200.0, 96.0
    for k in range(6):
        angle = math.pi * k / 3.0
        c.capsule((cx, cy), (cx + 26 * math.cos(angle), cy + 26 * math.sin(angle)), 2.6, (236, 250, 255), 0.75)


def _acc_flame(c: Canvas, r: dict) -> None:
    c.poly([(196, 176), (188, 132), (200, 106), (210, 132), (206, 120), (222, 152), (216, 186)], (206, 92, 42), 0.75)
    c.poly([(200, 176), (196, 142), (205, 128), (212, 148), (212, 178)], (240, 190, 84), 0.85)


def _acc_gourd(c: Canvas, r: dict) -> None:
    c.capsule((62, 236), (62, 208), 6.0, (110, 78, 48), 0.95)
    c.ellipse(62, 246, 15, 17, (196, 156, 82), 1.0)
    c.ellipse(62, 224, 10, 12, (206, 168, 96), 1.0)
    c.ellipse(56, 240, 4, 6, (232, 204, 142), 0.6)


def _acc_sword_hilt(c: Canvas, r: dict) -> None:
    c.capsule((182, 210), (214, 150), 8.0, (46, 42, 44), 1.0)
    c.capsule((186, 204), (212, 156), 4.0, (78, 72, 72), 0.9)
    c.capsule((200, 168), (224, 196), 5.0, (206, 168, 88), 1.0)
    c.ellipse(216, 148, 6.0, 6.0, (216, 178, 92), 1.0)
    c.capsule((220, 140), (232, 122), 7.0, (168, 44, 44), 1.0)


def _acc_beads(c: Canvas, r: dict) -> None:
    gold = (206, 172, 92)
    for i in range(9):
        t = i / 8.0
        x = 104 + 48 * t
        y = 206 + math.sin(t * math.pi) * 34
        c.ellipse(x, y, 4.6, 4.6, gold, 1.0)
        c.ellipse(x - 1, y - 1, 1.8, 1.8, (244, 226, 176), 0.7)


def _acc_fur_mantle(c: Canvas, r: dict) -> None:
    fur, fur_dark = (128, 106, 78), (92, 74, 54)
    c.poly([(38, 214), (218, 214), (226, 258), (30, 258)], fur_dark, 0.95)
    for i in range(14):
        x = 42 + i * 13
        c.poly([(x - 9, 210), (x, 190 + (i % 3) * 6), (x + 9, 210)], fur, 0.95)
        c.ellipse(x, 214, 8.0, 7.0, fur, 0.9)


def _acc_mask(c: Canvas, r: dict) -> None:
    c.poly([(88, 150), (168, 150), (166, 178), (150, 186), (128, 180), (106, 186), (90, 178)], (24, 22, 28), 0.94)
    c.capsule((88, 152), (168, 152), 3.0, (168, 46, 44), 0.95)


def _acc_vial(c: Canvas, r: dict) -> None:
    c.capsule((152, 214), (152, 208), 5.0, (222, 206, 150), 1.0)
    c.ellipse(152, 240, 11, 18, (150, 112, 186), 0.95)
    c.ellipse(148, 234, 3.5, 6.0, (216, 196, 240), 0.65)
    c.capsule((144, 222), (160, 222), 4.0, (150, 190, 122), 1.0)


def _acc_fox_tail(c: Canvas, r: dict) -> None:
    hair = r["hair"]
    c.ellipse(196, 168, 30, 34, _shade(hair, 0.82), 1.0)
    c.ellipse(214, 118, 22, 24, _shade(hair, 0.82), 1.0)
    c.ellipse(222, 74, 15, 16, (246, 244, 248), 1.0)
    c.ellipse(196, 168, 24, 28, hair, 1.0)
    c.ellipse(214, 118, 17, 19, hair, 1.0)


def _acc_scar(c: Canvas, r: dict) -> None:
    c.capsule((152, 116), (162, 156), 2.6, (176, 108, 96), 0.85)
    c.capsule((147, 130), (158, 130), 2.0, (176, 108, 96), 0.7)


def _acc_beard(c: Canvas, r: dict) -> None:
    hair = r["hair"]
    c.poly([(106, 148), (150, 148), (156, 194), (128, 224), (100, 194)], hair, 1.0)
    c.poly([(116, 150), (140, 150), (144, 186), (128, 206), (112, 186)], _shade(hair, 0.92), 1.0)
    c.capsule((116, 160), (140, 160), 6.0, hair, 1.0)


_ACCESSORIES = {
    "crown": _acc_crown,
    "headband": _acc_headband,
    "hairpin": _acc_hairpin,
    "fox_ears": _acc_fox_ears,
    "horns": _acc_horns,
    "dragon_horns": _acc_dragon_horns,
    "crescent": _acc_crescent,
    "feather": _acc_feather,
    "snowflake": _acc_snowflake,
    "flame": _acc_flame,
    "gourd": _acc_gourd,
    "sword_hilt": _acc_sword_hilt,
    "beads": _acc_beads,
    "fur_mantle": _acc_fur_mantle,
    "mask": _acc_mask,
    "vial": _acc_vial,
    "fox_tail": _acc_fox_tail,
    "scar": _acc_scar,
    "beard": _acc_beard,
}

#: Accessories drawn behind the body silhouette rather than over it.
_BEHIND = {"fox_tail", "flame", "snowflake"}


def render(recipe: dict) -> bytes:
    """Draw one portrait and return the encoded PNG bytes."""
    c = Canvas()
    behind = [a for a in recipe["accessories"] if a in _BEHIND]
    front = [a for a in recipe["accessories"] if a not in _BEHIND]

    _draw_backdrop(c, recipe)
    for name in behind:
        _ACCESSORIES[name](c, recipe)
    _draw_hair_mass(c, recipe)
    _draw_torso(c, recipe)
    _draw_neck(c, recipe)
    _draw_face(c, recipe)
    _draw_hair_front(c, recipe)
    for name in front:
        _ACCESSORIES[name](c, recipe)
    # Vignette: pull the frame corners down so the portrait sits in its panel.
    for y in range(_CANVAS):
        for x in range(_CANVAS):
            dx = (x / SS - 128.0) / 128.0
            dy = (y / SS - 128.0) / 128.0
            d = min(1.0, (dx * dx + dy * dy)) * 0.32
            if d > 0.02:
                c.blend(x, y, (12, 10, 8), d * 0.5)
    return _encode_png(c.to_rgb_rows())


def _encode_png(rows: bytes) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        payload = struct.pack(">I", len(data)) + tag + data
        return payload + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b"")


def _write_import(png_path: Path, res_path: str, mipmaps: bool = False) -> None:
    """Write the Godot sidecar that imports ``png_path`` as a texture.

    ``mipmaps`` is off for generated placeholders (flat colour: nothing to
    alias) and on for painted portraits, which carry fine line work shown at
    roughly a tenth of its shipped size -- without mips that detail speckles
    when the picker draws a 512px painting in a 76px cell.
    """
    digest = hashlib.md5(res_path.encode("utf-8")).hexdigest()
    uid = "uid://b" + hashlib.md5(("avatar:" + res_path).encode("utf-8")).hexdigest()[:14]
    ctex = f"res://.godot/imported/{png_path.name}-{digest}.ctex"
    png_path.with_suffix(".png.import").write_text(
        f"""[remap]

importer="texture"
type="CompressedTexture2D"
uid="{uid}"
path="{ctex}"
metadata={{
"vram_texture": false
}}

[deps]

source_file="{res_path}"
dest_files=["{ctex}"]

[params]

compress/mode=0
compress/high_quality=false
compress/lossy_quality=0.7
compress/uastc_level=0
compress/rdo_quality_loss=0.0
compress/hdr_compression=1
compress/normal_map=0
compress/channel_pack=0
mipmaps/generate={'true' if mipmaps else 'false'}
mipmaps/limit=-1
roughness/mode=0
roughness/src_normal=""
process/channel_remap/red=0
process/channel_remap/green=1
process/channel_remap/blue=2
process/channel_remap/alpha=3
process/fix_alpha_border=true
process/premult_alpha=false
process/normal_map_invert_y=false
process/hdr_as_srgb=false
process/hdr_clamp_exposure=false
process/size_limit=0
detect_3d/compress_to=1
""",
        encoding="utf-8",
    )


def painted_ids(out_dir: Path = OUT_DIR) -> set:
    """Ids whose art came from a file rather than this generator.

    ``tools/import_avatar_art.py`` records imported portraits in
    ``art_manifest.json``; anything absent from that manifest is still a
    placeholder, and placeholders are the only art this tool may overwrite.
    """
    manifest = out_dir / "art_manifest.json"
    if not manifest.is_file():
        return set()
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    avatars = data.get("avatars", {}) if isinstance(data, dict) else {}
    return {
        key
        for key, entry in avatars.items()
        if isinstance(entry, dict) and entry.get("art") == "painted"
    }


def generate(out_dir: Path = OUT_DIR, force: bool = False) -> dict:
    """Write a placeholder for every slot that is not carrying painted art."""
    out_dir.mkdir(parents=True, exist_ok=True)
    keep = set() if force else painted_ids(out_dir)
    written: list = []
    kept: list = []
    for recipe in RECIPES:
        if recipe["id"] in keep:
            kept.append(recipe["id"])
            continue
        path = out_dir / f"{recipe['id']}.png"
        path.write_bytes(render(recipe))
        _write_import(path, Res % recipe["id"])
        written.append(recipe["id"])
    return {"written": written, "kept": kept}


# --- art brief --------------------------------------------------------------
#
# The recipe table is also the art spec: each row already carries the palette,
# the hairstyle, and the props that make one archetype distinguishable from the
# other nineteen. ``--brief`` renders that into prose for an artist or an image
# model, so the twenty portraits can be produced as one family.

_BRIEF_PATH = ROOT / "game" / "docs" / "AVATAR_BRIEF.md"

_HAIR_PHRASES = {
    "topknot": "swept into a scholar's topknot with a few loose strands at the temples",
    "bun": "gathered into a high bun above the crown",
    "long_straight": "long and straight, falling past the shoulders",
    "high_ponytail": "swept back into a high ponytail",
    "ponytail": "in a low ponytail resting over one shoulder",
    "twin_tails": "in long twin tails framing the face",
    "wild": "wild and unkempt, strands falling over the eyes",
    "braid": "in a thick side braid over one shoulder",
    "hime": "long and straight with blunt side locks framing the jaw",
    "bald": "shaved to the scalp",
}

_ACCESSORY_PHRASES = {
    "crown": "a gold circlet set with a jewel",
    "headband": "a dark cloth headband with its tail hanging loose",
    "hairpin": "a jade hairpin",
    "fox_ears": "fox ears",
    "horns": "ribbed black demon horns",
    "dragon_horns": "pale jade dragon horns",
    "crescent": "a crescent-moon ornament floating above the brow",
    "feather": "a phoenix-feather pin trailing flame-gold barbs",
    "snowflake": "a pale frost sigil hanging in the air behind one shoulder",
    "flame": "a soul-flame burning behind one shoulder",
    "gourd": "a gourd hanging at the shoulder",
    "sword_hilt": "a sword hilt rising over one shoulder",
    "beads": "a strand of prayer beads across the chest",
    "fur_mantle": "a fur mantle over the shoulders",
    "mask": "a black half-mask over the lower face",
    "vial": "a small glass vial pendant",
    "fox_tail": "a pale fox tail curling behind the shoulder",
    "scar": "a scar across one cheek",
    "beard": "a long white beard and moustache",
}


def _hex(rgb) -> str:
    return "#%02X%02X%02X" % _rgb(rgb)


def _colour_word(rgb) -> str:
    """Name a colour the way a brief should ("crimson", "pale jade"), not as bytes."""
    r, g, b = (channel / 255.0 for channel in _rgb(rgb))
    high, low = max(r, g, b), min(r, g, b)
    value = high
    sat = 0.0 if high == 0.0 else (high - low) / high
    if value < 0.14:
        return "black"
    if sat < 0.10:
        return "white" if value > 0.9 else ("silver" if value > 0.65 else "grey")
    if high == r:
        hue = 60.0 * (((g - b) / (high - low)) % 6.0)
    elif high == g:
        hue = 60.0 * (((b - r) / (high - low)) + 2.0)
    else:
        hue = 60.0 * (((r - g) / (high - low)) + 4.0)
    if hue < 18.0 or hue >= 345.0:
        word = "crimson" if value > 0.6 else "dark red"
    elif hue < 42.0:
        word = "amber" if value > 0.7 and sat > 0.45 else "copper"
    elif hue < 70.0:
        word = "gold" if sat > 0.4 else "ochre"
    elif hue < 100.0:
        word = "moss"
    elif hue < 165.0:
        word = "emerald" if sat > 0.5 else "jade"
    elif hue < 200.0:
        word = "teal"
    elif hue < 235.0:
        word = "ice-blue" if value > 0.8 else "blue"
    elif hue < 265.0:
        word = "indigo"
    elif hue < 300.0:
        word = "violet"
    else:
        word = "purple"
    if value > 0.86 and sat < 0.35 and word not in ("gold",):
        word = "pale " + word
    elif value < 0.38 or (sat < 0.3 and value < 0.6):
        word = "dark " + word
    return word


def prompt_for(recipe: dict) -> str:
    """One copy-pasteable portrait prompt for an image model or an artist."""
    hair = _HAIR_PHRASES.get(recipe["hair_style"], recipe["hair_style"].replace("_", " "))
    details = [_ACCESSORY_PHRASES.get(a, a.replace("_", " ")) for a in recipe["accessories"]]
    clause = f" Details: {', '.join(details)}." if details else ""
    return (
        f"Head-and-shoulders portrait of a {recipe['gender']} xianxia cultivator, young adult, "
        f"three-quarter view, calm and composed gaze. {recipe['name']} -- {recipe['epithet']} "
        f"Hair: {_colour_word(recipe['hair'])} ({_hex(recipe['hair'])}), {hair}. "
        f"Eyes: {_colour_word(recipe['eyes'])} ({_hex(recipe['eyes'])}). "
        f"Wearing {_colour_word(recipe['robe'])} robes ({_hex(recipe['robe'])}) with crossed lapels, "
        f"{_hex(recipe['trim'])} trim, and a {_hex(recipe['inner'])} inner collar.{clause} "
        f"Background: neutral warm grey with a faint {_hex(recipe['aura'])} cast. Soft light from the "
        f"upper left, painted manhua xianxia character art with clean line work, 1:1 square, "
        f"character centred, head in the upper third, no text, no watermark."
    )


def art_brief() -> str:
    """The full markdown brief: direction, contract, roster, and prompts."""
    painted = painted_ids()
    lines = [
        "# Avatar art brief (player portraits)",
        "",
        "Generated by `python tools/gen_avatar_art.py --brief` from the recipe table in",
        "`tools/gen_avatar_art.py`. The same table feeds",
        "`frontend-godot/scripts/PlayerProfile.gd` (the roster the picker shows) and",
        "`tests/test_player_identity.py`, so art, roster, and recipes stay one contract.",
        "",
        "## Status",
        "",
        f"{len(painted)} of {len(RECIPES)} portraits in `frontend-godot/assets/avatars/` are "
        "**painted**; the rest are **generated placeholders** -- flat paper-cut geometry, no "
        "rendering -- kept so the identity picker is playable end to end. A painting replaces a",
        "placeholder file-for-file: same id, same directory, same filename, and",
        "`art_manifest.json` records which is which and what each painting was cut from. A",
        "painted slot's row below still describes the recipe it was authored from, which is what",
        "a replacement would be matched against; the shipped file is the art.",
        "",
        "## Target style",
        "",
        "Hand-painted manhua/xianxia character art: a head-and-shoulders bust in three-quarter",
        "view, painterly shading with soft light from the upper left, clean dark line work,",
        "individual hair strands over massed shadow, calm expressions, and a neutral warm-grey",
        "ground so the roster reads as one family in the picker grid.",
        "",
        "## Technical contract",
        "",
        "- **Framing:** 1:1 square, head and shoulders, eye line about a third from the top,",
        "  shoulders cropped by the frame edge, character centred, no text or watermark.",
        "- **Size:** author at 1024x1024, ship at 512x512 (the client draws it as small as",
        "  52px in the top rail and 76px in the picker).",
        "- **Format:** PNG, sRGB, 8-bit. Opaque ground is fine: the client cover-crops, so a",
        "  square file is always used whole.",
        "- **Naming:** `frontend-godot/assets/avatars/<id>.png`, ids exactly as tabled below.",
        "- **Import:** never hand-copy art in. `python tools/import_avatar_art.py <id>=<file>`",
        "  converts and crops it, writes the Godot sidecar, and records source hash, shipped",
        "  hash, crop geometry, and the recipe that produced it in `art_manifest.json`.",
        "- **Framing:** the importer's default `--anchor face` measures the subject and frames a",
        "  bust; painted backgrounds sometimes read as skin, so check the result and re-run with",
        "  an explicit `zoom`/`top` (`<id>=<file>:0.46:0.08`) until the face fills the square.",
        "  The manifest then reports what was actually shipped -- a crop wider than ~90% of the",
        "  source's short side fails `tests/test_player_identity.py` as a full-torso crop.",
        "",
        "## Roster",
        "",
        "| # | id | name | gender | art | hair | eyes | robe | trim | accessories |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for index, recipe in enumerate(RECIPES, 1):
        lines.append(
            "| %d | `%s` | %s | %s | %s | %s | %s | %s | %s | %s |"
            % (
                index,
                recipe["id"],
                recipe["name"],
                recipe["gender"],
                "painted" if recipe["id"] in painted else "placeholder",
                _HAIR_PHRASES.get(recipe["hair_style"], recipe["hair_style"]),
                _hex(recipe["eyes"]),
                _hex(recipe["robe"]),
                _hex(recipe["trim"]),
                ", ".join(recipe["accessories"]) or "-",
            )
        )
    lines += [
        "",
        f"Painted so far: {len(painted)} of {len(RECIPES)} "
        f"({len(RECIPES) - len(painted)} slots still wear a generated placeholder).",
        "",
        "## Prompt sheet",
        "",
    ]
    for index, recipe in enumerate(RECIPES, 1):
        lines.append(f"### {index}. `{recipe['id']}` - {recipe['name']} ({recipe['gender']})")
        lines.append("")
        lines.append(f"*Archetype: {recipe['inspiration']}*")
        lines.append("")
        lines.append(f"> {prompt_for(recipe)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_brief(path: Path = _BRIEF_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    # CRLF: the repo's docs are checked out that way on Windows.
    path.write_text(art_brief(), encoding="utf-8", newline="\r\n")
    return path


def main(argv=None) -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate the avatar portraits (or the art brief).")
    parser.add_argument("--brief", action="store_true", help="write game/docs/AVATAR_BRIEF.md and exit")
    parser.add_argument("--only", help="regenerate a single avatar by id")
    parser.add_argument("--force", action="store_true", help="overwrite slots that already carry painted art")
    args = parser.parse_args(argv)

    if args.brief:
        print(f"wrote {write_brief()}")
        return

    if args.only:
        if args.only not in BY_ID:
            raise SystemExit(f"unknown avatar id: {args.only}")
        if args.only in painted_ids() and not args.force:
            raise SystemExit(f"{args.only} carries painted art; pass --force to replace it with a placeholder")
        recipe = BY_ID[args.only]
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUT_DIR / f"{recipe['id']}.png"
        path.write_bytes(render(recipe))
        _write_import(path, Res % recipe["id"])
        print(f"wrote {path.name} (+ .import)")
        return

    outcome = generate(force=args.force)
    print(f"wrote {len(outcome['written'])} placeholders to {OUT_DIR}")
    if outcome["kept"]:
        print(f"kept {len(outcome['kept'])} painted portraits untouched: {', '.join(outcome['kept'])}")
    print("hint: --brief writes the art spec and prompt sheet for painted replacements")


if __name__ == "__main__":
    main()
