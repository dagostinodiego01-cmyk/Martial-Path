"""Draw scene artwork for locations that have no painting yet.

The Godot location panel loads ``frontend-godot/assets/locations/<location_id>.png``
(see ``MainController._load_location_texture``) and falls back to a bare name
label when the file is absent. Every location in ``game/data/locations.json``
should therefore ship an image, so this tool composes one for each id that has
none.

There is no image model in this workspace, so the art is *drawn*: each location's
``location_type`` and description pick a scene archetype (wharf, deepwood,
terraced farmland, lantern outpost, peak sect, canyon market, mountain village,
sea pavilion, pirate cove, coral prison, open sea, forge city, fortress, shrine,
rune undercroft, ascension stair). A scene is a small number of large, clean
shapes — layered ranges receding into atmospheric haze, then a landmark or two in
near-black silhouette (a jetty and hulls, a palisade and gate tower, terraced
contours below a walled capital, a pagoda above a sea of cloud, coral towers in a
storm) — with the sky, water, mist and lighting carried by the palette.

Everything is seeded from the location id, so runs are byte-identical and two
locations never compose the same frame. It is a stand-in for a hand-painted
plate, not a replacement: drop a real PNG over the file and this tool leaves it
alone (it only ever writes *missing* files; ``--location`` redraws a named one).

Each PNG gets the same ``.import`` sidecar a real one has, so the Godot editor
picks it up without a rescan (``_load_texture`` also falls back to reading the
raw PNG, so art shows even before the editor imports it).

Usage:
    python tools/gen_missing_location_art.py                    # fill in the gaps only
    python tools/gen_missing_location_art.py --list             # report gaps, write nothing
    python tools/gen_missing_location_art.py --location X [Y..] # redraw named scenes
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import random
import struct
import zlib
from pathlib import Path
from typing import Callable, Dict, List, NamedTuple, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
LOCATIONS = ROOT / "game" / "data" / "locations.json"
ASSETS = ROOT / "frontend-godot" / "assets" / "locations"

#: 1512x1040 is the size of the shipped hand-made art; keep parity so the
#: TextureRect's aspect-cover crop behaves identically for generated scenes.
WIDTH, HEIGHT = 1512, 1040

RGB = Tuple[int, int, int]
Point = Tuple[float, float]


# --------------------------------------------------------------------------
# canvas
# --------------------------------------------------------------------------
class Canvas:
    """A flat RGB8 pixel buffer with the few fill shapes the scenes need."""

    def __init__(self, width: int, height: int) -> None:
        self.w = width
        self.h = height
        self.data = bytearray(width * height * 3)

    # -- hard fills (slice assignment: the work happens in C) --------------
    def column(self, x: int, y0: int, y1: int, color: RGB) -> None:
        """Paint the vertical run ``[y0, y1)`` of column ``x``."""
        x = int(round(x))
        y0 = max(0, int(round(y0)))
        y1 = min(self.h, int(round(y1)))
        if y1 <= y0 or x < 0 or x >= self.w:
            return
        start = (y0 * self.w + x) * 3
        span = y1 - y0
        self.data[start : start + span * 3] = bytes(color) * span

    def row(self, y: int, x0: int, x1: int, color: RGB) -> None:
        """Paint the horizontal run ``[x0, x1)`` of row ``y``."""
        y = int(round(y))
        x0 = max(0, int(round(x0)))
        x1 = min(self.w, int(round(x1)))
        if x1 <= x0 or y < 0 or y >= self.h:
            return
        start = (y * self.w + x0) * 3
        span = x1 - x0
        self.data[start : start + span * 3] = bytes(color) * span

    def circle(self, cx: float, cy: float, radius: float, color: RGB) -> None:
        for x in range(int(cx - radius), int(cx + radius) + 1):
            dx = (x - cx) / radius
            if abs(dx) > 1.0:
                continue
            dy = math.sqrt(1.0 - dx * dx) * radius
            self.column(x, cy - dy, cy + dy + 1, color)

    def polygon(self, points: Sequence[Point], color: RGB) -> None:
        """Fill a simple polygon by intersecting its edges column by column."""
        spans: Dict[int, List[float]] = {}
        count = len(points)
        for index in range(count):
            x0, y0 = points[index]
            x1, y1 = points[(index + 1) % count]
            if x0 == x1:
                continue
            lo, hi = (x0, x1) if x0 < x1 else (x1, x0)
            for x in range(int(lo), int(hi) + 1):
                t = (x - x0) / (x1 - x0)
                y = y0 + (y1 - y0) * t
                span = spans.get(x)
                if span is None:
                    spans[x] = [y, y]
                else:
                    span[0] = min(span[0], y)
                    span[1] = max(span[1], y)
        for x, (lo_y, hi_y) in spans.items():
            self.column(x, lo_y, hi_y + 1, color)

    # -- soft fills (per-pixel blend, used for atmosphere) ----------------
    def blend_row(self, y: int, x0: int, x1: int, color: RGB, alpha: float) -> None:
        if alpha <= 0.0:
            return
        y = int(round(y))
        x0 = max(0, int(round(x0)))
        x1 = min(self.w, int(round(x1)))
        if x1 <= x0 or y < 0 or y >= self.h:
            return
        a = min(255, int(alpha * 255))
        inv = 255 - a
        cr, cg, cb = color
        buf = self.data
        index = (y * self.w + x0) * 3
        for _ in range(x1 - x0):
            buf[index] = (buf[index] * inv + cr * a) // 255
            buf[index + 1] = (buf[index + 1] * inv + cg * a) // 255
            buf[index + 2] = (buf[index + 2] * inv + cb * a) // 255
            index += 3

    def add_pixel(self, x: int, y: int, color: RGB, amount: float) -> None:
        x = int(round(x))
        y = int(round(y))
        if amount <= 0.0 or x < 0 or y < 0 or x >= self.w or y >= self.h:
            return
        index = (y * self.w + x) * 3
        buf = self.data
        buf[index] = min(255, buf[index] + int(color[0] * amount))
        buf[index + 1] = min(255, buf[index + 1] + int(color[1] * amount))
        buf[index + 2] = min(255, buf[index + 2] + int(color[2] * amount))

    def glow(self, cx: float, cy: float, radius: float, color: RGB, strength: float) -> None:
        """Additive radial light: lanterns, forges, runes."""
        for x in range(int(cx - radius), int(cx + radius) + 1):
            dx = (x - cx) / radius
            if abs(dx) >= 1.0:
                continue
            dy = math.sqrt(1.0 - dx * dx) * radius
            for y in range(int(cy - dy), int(cy + dy) + 1):
                distance = math.hypot((x - cx) / radius, (y - cy) / radius)
                if distance >= 1.0:
                    continue
                self.add_pixel(x, y, color, (1.0 - distance) ** 2 * strength)


def _mix(a: RGB, b: RGB, t: float) -> RGB:
    t = 0.0 if t < 0.0 else 1.0 if t > 1.0 else t
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def _shade(color: RGB, factor: float) -> RGB:
    return (
        max(0, min(255, int(color[0] * factor))),
        max(0, min(255, int(color[1] * factor))),
        max(0, min(255, int(color[2] * factor))),
    )


# --------------------------------------------------------------------------
# mood palettes
# --------------------------------------------------------------------------
class Mood(NamedTuple):
    sky_top: RGB
    sky_low: RGB
    sun: RGB
    far: RGB
    mid: RGB
    near: RGB
    structure: RGB
    lit: RGB
    water_hi: RGB
    water_lo: RGB
    accent: RGB


MOODS: Dict[str, Mood] = {
    "dawn": Mood((56, 66, 104), (226, 168, 124), (255, 226, 178), (108, 108, 132), (68, 66, 86),
                 (30, 30, 40), (26, 26, 36), (226, 182, 118), (168, 162, 182), (52, 56, 78), (255, 196, 120)),
    "day": Mood((104, 152, 200), (222, 226, 214), (255, 248, 220), (154, 176, 184), (92, 118, 108),
                (40, 52, 44), (40, 42, 46), (240, 214, 154), (176, 200, 210), (58, 80, 92), (255, 220, 148)),
    "dusk": Mood((38, 34, 64), (242, 146, 88), (255, 202, 134), (96, 76, 96), (54, 44, 62),
                 (24, 20, 30), (18, 16, 24), (226, 156, 96), (168, 126, 134), (40, 34, 52), (255, 172, 96)),
    "night": Mood((8, 12, 28), (34, 46, 70), (232, 238, 250), (44, 56, 78), (26, 34, 50),
                  (10, 14, 22), (8, 10, 18), (214, 190, 136), (96, 116, 148), (12, 18, 32), (255, 198, 120)),
    "storm": Mood((44, 48, 56), (140, 142, 142), (210, 212, 214), (104, 110, 114), (66, 72, 76),
                  (28, 32, 36), (24, 26, 32), (186, 196, 204), (132, 144, 150), (30, 38, 46), (255, 172, 104)),
    "undercroft": Mood((12, 9, 12), (42, 26, 24), (255, 152, 80), (40, 26, 28), (26, 16, 18),
                       (10, 7, 9), (16, 11, 13), (252, 176, 112), (86, 116, 128), (12, 10, 14), (132, 232, 240)),
    "forest": Mood((70, 96, 96), (186, 206, 168), (246, 250, 220), (104, 128, 108), (52, 74, 60),
                     (18, 28, 22), (20, 26, 22), (206, 220, 156), (122, 152, 134), (26, 40, 36), (228, 246, 180)),
    "astral": Mood((4, 6, 20), (30, 32, 72), (222, 226, 255), (40, 40, 82), (24, 24, 58),
                   (8, 8, 22), (12, 12, 30), (232, 224, 255), (124, 128, 190), (10, 12, 32), (204, 192, 255)),
}

#: location_type -> (mood, scene builder). Anything unlisted falls back by zone.
SCENES: Dict[str, Tuple[str, str]] = {
    "river_wharf": ("dawn", "wharf"),
    "deep_forest_wilderness": ("forest", "deepwood"),
    "wilderness_outpost_hub": ("dusk", "outpost"),
    "farmland_outskirts": ("day", "terraces"),
    "mountain_village": ("day", "mountain_village"),
    "sect_outer_peaks": ("dawn", "peaks"),
    "hidden_market_canyon": ("night", "canyon_market"),
    "sea_pavilion_hub": ("dusk", "sea_pavilion"),
    "pirate_cove": ("dusk", "cove"),
    "sunken_prison": ("storm", "atoll"),
    "open_sea_expanse": ("storm", "open_sea"),
    "forge_city_hub": ("night", "forge_city"),
    "militant_fortress": ("storm", "fortress"),
    "mountain_shrine": ("dawn", "shrine"),
    "elemental_undercroft": ("undercroft", "undercroft"),
    "ascension_approach": ("astral", "ascension"),
    "ascension_gateway": ("astral", "ascension"),
    "waterfall_valley": ("dawn", "peaks"),
    "dungeon": ("undercroft", "undercroft"),
}

ZONE_FALLBACK: Dict[str, str] = {
    "Southern Sea": "open_sea",
    "Ascension Gate": "ascension",
    "Sea of Miracles": "open_sea",
    "Holy Demon Continent": "fortress",
    "Central Region": "forge_city",
    "Great Zen Region": "shrine",
    "Five Element Region": "undercroft",
    "Seven Profound Valleys": "peaks",
    "South Horizon Region": "mountain_village",
    "Sky Fortune Kingdom": "terraces",
}


# --------------------------------------------------------------------------
# shared ingredients
# --------------------------------------------------------------------------
def _ridge(rng: random.Random, width: int, base: float, amplitude: float, roughness: int = 3) -> List[int]:
    """A per-column silhouette line: layered sines plus seeded jitter."""
    terms = [
        (rng.uniform(0.4, 1.8) / width, rng.uniform(0.0, math.tau), rng.uniform(0.35, 1.0))
        for _ in range(roughness)
    ]
    total_weight = sum(weight for _, _, weight in terms)
    jitter = [rng.uniform(-0.16, 0.16) for _ in range(width)]
    profile: List[int] = []
    for x in range(width):
        value = 0.0
        for frequency, phase, weight in terms:
            value += math.sin(x * frequency * math.tau + phase) * weight
        profile.append(int(base + (value / total_weight + jitter[x]) * amplitude))
    return profile


def _fill_below(canvas: Canvas, profile: Sequence[int], color: RGB) -> None:
    for x, top in enumerate(profile):
        canvas.column(x, top, canvas.h, color)


def _sky(canvas: Canvas, mood: Mood, horizon: int, below: RGB) -> None:
    for y in range(0, min(horizon, canvas.h)):
        canvas.row(y, 0, canvas.w, _mix(mood.sky_top, mood.sky_low, y / max(1, horizon - 1)))
    for y in range(horizon, canvas.h):
        t = min(1.0, (y - horizon) / max(1, canvas.h - horizon))
        canvas.row(y, 0, canvas.w, _mix(mood.sky_low, below, t))


def _ranges(canvas: Canvas, rng: random.Random, mood: Mood, horizon: float, count: int,
            spread: float = 0.10, tall: float = 0.13, trees: bool = True, darken: float = 1.0) -> None:
    """Layered ranges receding into haze — the spine of every landscape scene.

    Ranges are painted back to front: each sits lower on screen, is darker, and
    carries taller tree cover, which reads as depth without any perspective math.
    """
    for index in range(count):
        t = index / max(1, count - 1)
        base = horizon + canvas.h * spread * index
        amplitude = canvas.h * (tall * (0.75 + 0.65 * t))
        color = _shade(_mix(mood.far, mood.near, 0.30 + 0.70 * t), darken)
        profile = _ridge(rng, canvas.w, base, amplitude, 3 + (index % 2))
        _fill_below(canvas, profile, color)
        if trees:
            _tree_line(canvas, rng, base + amplitude * 0.42, 12 + index * 7,
                       amplitude * (0.30 + 0.14 * index), _shade(_mix(color, mood.near, 0.35), 0.9),
                       conifer_ratio=0.55 + 0.15 * index)
        # A bright fog bank just above each ridgeline is what makes the next,
        # nearer layer read as a silhouette instead of mushing into the last.
        _haze(canvas, int(base - amplitude * 2.6), int(base - amplitude * 0.15),
              _mix(mood.sky_low, (255, 255, 255), 0.30), 0.0, 0.20)
        if index < count - 1:
            _haze(canvas, int(base - amplitude), int(base + amplitude * 1.4),
                  _mix(mood.sky_low, color, 0.45), 0.20, 0.0)


def _haze(canvas: Canvas, y0: int, y1: int, color: RGB, top_alpha: float, bottom_alpha: float) -> None:
    span = max(1, y1 - y0)
    for y in range(max(0, y0), min(canvas.h, y1)):
        canvas.blend_row(y, 0, canvas.w, color, top_alpha + (bottom_alpha - top_alpha) * ((y - y0) / span))


def _stars(canvas: Canvas, rng: random.Random, limit: int, brightness: float) -> None:
    for _ in range(limit):
        x = rng.randrange(0, canvas.w)
        y = rng.randrange(0, int(canvas.h * 0.58))
        value = rng.uniform(0.25, 1.0) * brightness
        canvas.add_pixel(x, y, (255, 252, 240), value)
        canvas.add_pixel(x + 1, y, (240, 244, 255), value * 0.5)
    for _ in range(max(2, limit // 70)):
        x = rng.randrange(0, canvas.w)
        y = rng.randrange(0, int(canvas.h * 0.45))
        for arm in range(1, 5):
            canvas.add_pixel(x + arm, y, (255, 250, 235), 0.30 / arm)
            canvas.add_pixel(x - arm, y, (255, 250, 235), 0.30 / arm)
            canvas.add_pixel(x, y + arm, (255, 250, 235), 0.30 / arm)
            canvas.add_pixel(x, y - arm, (255, 250, 235), 0.30 / arm)


def _orb(canvas: Canvas, cx: float, cy: float, radius: float, mood: Mood, glow_scale: float = 3.4) -> None:
    canvas.glow(cx, cy, radius * glow_scale, mood.sun, 0.60)
    canvas.circle(cx, cy, radius, mood.sun)
    canvas.circle(cx, cy, radius * 0.82, _mix(mood.sun, (255, 255, 255), 0.40))


def _cloud(canvas: Canvas, cx: float, cy: float, rx: float, ry: float, color: RGB, alpha: float) -> None:
    for y in range(int(cy - ry), int(cy + ry) + 1):
        t = (y - cy) / ry
        if abs(t) > 1.0:
            continue
        half = rx * math.sqrt(1.0 - t * t)
        canvas.blend_row(y, cx - half, cx + half, color, alpha * (1.0 - abs(t)))


def _conifer(canvas: Canvas, rng: random.Random, x: float, base_y: float, height: float, color: RGB) -> None:
    width = height * rng.uniform(0.20, 0.28)
    canvas.column(x, base_y - height * 0.20, base_y, _shade(color, 0.62))
    tiers = 5
    for tier in range(tiers):
        span = 0.20 * tier
        top = base_y - height * (0.36 + span)
        half = width * (0.46 + 0.16 * tier)
        bottom = base_y - height * (0.16 + span)
        canvas.polygon([(x - half, bottom), (x, top), (x + half, bottom)], _shade(color, 0.84 + 0.04 * tier))


def _broadleaf(canvas: Canvas, rng: random.Random, x: float, base_y: float, height: float, color: RGB) -> None:
    canvas.column(x, base_y - height * 0.52, base_y, _shade(color, 0.62))
    crown_y = base_y - height * 0.70
    crown_r = height * 0.32
    canvas.circle(x, crown_y, crown_r, color)
    canvas.circle(x - crown_r * 0.72, crown_y + crown_r * 0.20, crown_r * 0.62, _shade(color, 0.88))
    canvas.circle(x + crown_r * 0.70, crown_y + crown_r * 0.14, crown_r * 0.58, _shade(color, 1.08))
    canvas.circle(x + rng.uniform(-0.2, 0.2) * crown_r, crown_y - crown_r * 0.48, crown_r * 0.5,
                  _shade(color, 1.16))


def _tree_line(canvas: Canvas, rng: random.Random, base_y: float, count: int, height: float, color: RGB,
               conifer_ratio: float = 1.0) -> None:
    for index in range(count):
        x = (index + rng.uniform(0.1, 0.9)) * (canvas.w / count)
        scale = rng.uniform(0.62, 1.32)
        if rng.random() < conifer_ratio:
            _conifer(canvas, rng, x, base_y + rng.uniform(-6, 6), height * scale, color)
        else:
            _broadleaf(canvas, rng, x, base_y + rng.uniform(-4, 4), height * scale, color)


def _pagoda(canvas: Canvas, cx: float, base_y: float, body_w: float, height: float, tiers: int,
            body: RGB, roof: RGB) -> None:
    """Stacked roofs over a tapering body (the xianxia silhouette)."""
    tier_h = height / tiers
    for tier in range(tiers):
        width = body_w * (1.0 - tier * 0.18)
        top = base_y - tier_h * (tier + 1)
        for x in range(int(cx - width / 2), int(cx + width / 2) + 1):
            canvas.column(x, top + tier_h * 0.34, top + tier_h, body if x < cx else _shade(body, 0.86))
        eave = width * 0.78
        roof_y = top + tier_h * 0.34
        canvas.polygon(
            [
                (cx - eave, roof_y + tier_h * 0.08),
                (cx - eave * 0.32, roof_y - tier_h * 0.42),
                (cx + eave * 0.32, roof_y - tier_h * 0.42),
                (cx + eave, roof_y + tier_h * 0.08),
            ],
            roof if tier % 2 == 0 else _shade(roof, 0.86),
        )
        for tip in (cx - eave, cx + eave):
            canvas.column(tip, roof_y - tier_h * 0.10, roof_y + tier_h * 0.08, _shade(roof, 1.2))
    canvas.column(cx, base_y - height - tier_h * 0.5, base_y - height, _shade(roof, 1.1))
    canvas.circle(cx, base_y - height - tier_h * 0.58, tier_h * 0.14, _shade(roof, 1.25))


def _hut(canvas: Canvas, cx: float, base_y: float, width: float, height: float, body: RGB, roof: RGB) -> None:
    """A cottage: wall block, gable roof, and a lit doorway."""
    for x in range(int(cx - width / 2), int(cx + width / 2) + 1):
        canvas.column(x, base_y - height, base_y, body if x < cx else _shade(body, 0.82))
    # A lit window and doorway keep the wall from reading as one flat chevron.
    canvas.column(cx, base_y - height * 0.52, base_y, _shade(roof, 0.42))
    for offset in (-0.28, 0.28):
        canvas.column(cx + width * offset, base_y - height * 0.66, base_y - height * 0.46,
                      _mix(roof, (255, 214, 140), 0.55))
    canvas.polygon(
        [(cx - width * 0.76, base_y - height + height * 0.14),
         (cx, base_y - height - height * 0.46),
         (cx + width * 0.76, base_y - height + height * 0.14)],
        roof,
    )
    canvas.row(base_y - height + height * 0.14, cx - width * 0.76, cx + width * 0.76, _shade(roof, 0.8))


def _wall(canvas: Canvas, x0: int, x1: int, base_y: int, height: float, body: RGB, lit: RGB) -> None:
    for x in range(max(0, x0), min(canvas.w, x1)):
        canvas.column(x, base_y - height, base_y, body)
    merlon_w = max(8, int((x1 - x0) / 24))
    for x in range(x0, x1 - merlon_w, merlon_w * 2):
        for mx in range(x, min(x + merlon_w, x1)):
            canvas.column(mx, base_y - height - height * 0.16, base_y - height, _shade(body, 0.88))
    for x in range(x0 + merlon_w, x1, merlon_w * 4):
        canvas.row(base_y - height * 0.55, x, x + merlon_w, _shade(lit, 0.40))


def _tower(canvas: Canvas, cx: float, base_y: float, width: float, height: float, body: RGB, roof: RGB) -> None:
    for x in range(int(cx - width / 2), int(cx + width / 2) + 1):
        canvas.column(x, base_y - height, base_y, body if x < cx else _shade(body, 0.78))
    for x in range(int(cx - width / 2), int(cx + width / 2), 5):
        canvas.column(x, base_y - height - 10, base_y - height, _shade(body, 1.12))
    canvas.polygon(
        [(cx - width * 0.86, base_y - height + 6),
         (cx, base_y - height - height * 0.36),
         (cx + width * 0.86, base_y - height + 6)],
        roof,
    )
    for slit in (-1, 1):
        canvas.column(cx + slit * width * 0.30, base_y - height * 0.74, base_y - height * 0.56,
                      _shade(roof, 1.35))


def _banner(canvas: Canvas, x: float, y: float, width: float, height: float, color: RGB) -> None:
    canvas.column(x, y - height, y, _shade(color, 0.6))
    canvas.polygon(
        [(x + 2, y - height), (x + width, y - height + height * 0.08),
         (x + width, y - height * 0.52), (x + 2, y - height * 0.44)],
        color,
    )


def _lantern(canvas: Canvas, x: float, y: float, size: float, warm: RGB, strength: float = 0.85) -> None:
    canvas.glow(x, y, size * 7.0, warm, strength * 0.5)
    canvas.circle(x, y, size, _mix(warm, (255, 255, 255), 0.35))


def _boat(canvas: Canvas, cx: float, water_y: float, length: float, hull: RGB, mast_h: float, sail: RGB) -> None:
    canvas.polygon(
        [(cx - length / 2, water_y), (cx + length / 2, water_y),
         (cx + length * 0.32, water_y + length * 0.09), (cx - length * 0.32, water_y + length * 0.09)],
        hull,
    )
    canvas.column(cx, water_y - mast_h, water_y, _shade(hull, 0.7))
    if sail[0] or sail[1] or sail[2]:
        canvas.polygon(
            [(cx, water_y - mast_h), (cx + mast_h * 0.44, water_y - mast_h * 0.32),
             (cx, water_y - mast_h * 0.18)],
            sail,
        )


def _reeds(canvas: Canvas, rng: random.Random, x: float, base_y: float, height: float, color: RGB) -> None:
    for _ in range(rng.randint(3, 7)):
        canvas.column(x + rng.uniform(-height * 0.4, height * 0.4),
                      base_y - height * rng.uniform(0.55, 1.0), base_y, color)


def _rock(canvas: Canvas, x: float, y: float, width: float, height: float, color: RGB) -> None:
    canvas.polygon(
        [(x - width / 2, y + height * 0.4), (x - width * 0.22, y - height),
         (x + width * 0.18, y - height * 0.84), (x + width / 2, y + height * 0.4)],
        color,
    )


def _foreground(canvas: Canvas, rng: random.Random, color: RGB, top: float = 0.90) -> None:
    """A near-black band along the bottom edge anchors the frame."""
    profile = _ridge(rng, canvas.w, canvas.h * top, canvas.h * 0.02, 4)
    _fill_below(canvas, profile, color)


def _water(canvas: Canvas, rng: random.Random, mood: Mood, waterline: int, depth: int = 300) -> None:
    """Mirror the scene above the waterline into it, then break it up with ripples."""
    buf = canvas.data
    width = canvas.w
    for y in range(waterline + 1, min(canvas.h, waterline + depth)):
        source_y = max(0, 2 * waterline - y)
        t = (y - waterline) / max(1, depth)
        blend = 0.26 + 0.44 * t
        wobble = 3.0 * (0.3 + t)
        base = _mix(mood.water_hi, mood.water_lo, min(1.0, t * 1.15))
        source_row = source_y * width * 3
        row = y * width * 3
        for x in range(width):
            shift = int(math.sin(y * 0.5 + x * 0.017) * wobble)
            sx = x + shift
            if sx < 0 or sx >= width:
                sx = x
            s = source_row + sx * 3
            d = row + x * 3
            buf[d] = int(buf[s] * (1.0 - blend) + base[0] * blend)
            buf[d + 1] = int(buf[s + 1] * (1.0 - blend) + base[1] * blend)
            buf[d + 2] = int(buf[s + 2] * (1.0 - blend) + base[2] * blend)
    for _ in range(30):
        y = rng.randrange(waterline + 2, canvas.h)
        length = rng.randint(24, 170)
        x = rng.randrange(0, max(1, canvas.w - length))
        canvas.blend_row(y, x, x + length, _shade(mood.water_hi, 1.30), rng.uniform(0.10, 0.30))


def _mist(canvas: Canvas, rng: random.Random, y: int, thickness: int, color: RGB, alpha: float,
          width_scale: float = 1.0) -> None:
    for offset in range(thickness):
        row_alpha = alpha * math.sin(math.pi * (offset / max(1, thickness))) * rng.uniform(0.75, 1.05)
        if width_scale >= 1.0:
            canvas.blend_row(y + offset, 0, canvas.w, color, max(0.0, row_alpha))
        else:
            half = canvas.w * width_scale / 2
            canvas.blend_row(y + offset, canvas.w * 0.5 - half, canvas.w * 0.5 + half, color,
                             max(0.0, row_alpha))


def _grasses(canvas: Canvas, rng: random.Random, base_y: float, color: RGB, count: int = 90) -> None:
    for _ in range(count):
        _reeds(canvas, rng, rng.randrange(0, canvas.w), base_y + rng.uniform(-4, 10),
               rng.uniform(14, 44), color)


def _finish(canvas: Canvas, rng: random.Random, vignette: float = 0.9, grain: int = 9) -> None:
    """Final pass: soft vignette, a colour lift, and film grain.

    Procedural fills read as washed plastic on their own; the saturation and
    contrast lift keeps generated plates in the same register as the painted
    ones, and the grain stops large gradients from banding.
    """
    width, height, buf = canvas.w, canvas.h, canvas.data
    half_w, half_h = width / 2.0, height / 2.0
    seed = rng.randrange(1 << 30)
    columns = [
        ((((x - half_w) / half_w) ** 2) * 0.34 * vignette, ((x * 2654435761) >> 17) & 0x1F)
        for x in range(width)
    ]
    index = 0
    for y in range(height):
        dy = (((y - half_h) / half_h) ** 2) * 0.34 * vignette
        row_seed = (seed ^ (y * 668265263)) & 0xFFFFFFFF
        for x in range(width):
            falloff, column_seed = columns[x]
            shade = 1.0 - falloff - dy
            if shade < 0.0:
                shade = 0.0
            noise = (((column_seed ^ row_seed) & 0x1F) - 16) * grain // 16
            r = int(buf[index] * shade)
            g = int(buf[index + 1] * shade)
            b = int(buf[index + 2] * shade)
            luma = (r * 77 + g * 151 + b * 28) >> 8
            r = 128 + int((luma + (r - luma) * 1.16 - 128) * 1.10) + noise
            g = 128 + int((luma + (g - luma) * 1.16 - 128) * 1.10) + noise
            b = 128 + int((luma + (b - luma) * 1.16 - 128) * 1.10) + noise
            buf[index] = 0 if r < 0 else 255 if r > 255 else r
            buf[index + 1] = 0 if g < 0 else 255 if g > 255 else g
            buf[index + 2] = 0 if b < 0 else 255 if b > 255 else b
            index += 3


# --------------------------------------------------------------------------
# scenes
# --------------------------------------------------------------------------
def _scene_wharf(c: Canvas, rng: random.Random, mood: Mood) -> None:
    """Weathered wharf: far bank, jetty, moored hulls, lantern light on the river."""
    horizon = int(c.h * 0.44)
    waterline = int(c.h * 0.60)
    _sky(c, mood, horizon, _mix(mood.far, mood.water_lo, 0.35))
    _orb(c, c.w * 0.74, horizon * 0.52, 46, mood, glow_scale=4.4)
    _cloud(c, c.w * 0.28, horizon * 0.40, c.w * 0.24, 30, _shade(mood.lit, 0.82), 0.18)
    _cloud(c, c.w * 0.66, horizon * 0.66, c.w * 0.20, 22, _shade(mood.lit, 0.92), 0.14)
    _ranges(c, rng, mood, horizon - c.h * 0.04, 2, spread=0.09, tall=0.13)
    _fill_below(c, _ridge(rng, c.w, waterline + 4, c.h * 0.014, 3), _mix(mood.mid, mood.near, 0.4))
    bank = waterline + 10
    for cx, w, h in ((c.w * 0.17, 260, 168), (c.w * 0.38, 210, 138), (c.w * 0.58, 176, 118)):
        for leg in (cx - w * 0.34, cx - w * 0.1, cx + w * 0.14, cx + w * 0.36):
            c.column(leg, bank, bank + 34, _shade(mood.structure, 0.62))
        _hut(c, cx, bank, w, h, _mix(mood.structure, mood.far, 0.45), _shade(mood.structure, 0.82))
    plank_y = waterline + 62
    c.row(plank_y, 0, c.w * 0.46, _shade(mood.structure, 0.86))
    c.row(plank_y + 12, 0, c.w * 0.46, _shade(mood.structure, 0.66))
    for x in range(10, int(c.w * 0.46), 64):
        c.column(x, plank_y, plank_y + 40, _shade(mood.structure, 0.58))
        _lantern(c, x, plank_y - 18, 5, mood.accent, 0.55) if x % 128 < 64 else None
    _water(c, rng, mood, waterline, depth=340)
    _boat(c, c.w * 0.62, waterline + 110, 360, _shade(mood.structure, 0.8), 200, _shade(mood.lit, 0.55))
    _boat(c, c.w * 0.90, waterline + 200, 250, _shade(mood.structure, 0.68), 110, (0, 0, 0))
    _lantern(c, c.w * 0.62, waterline + 84, 7, mood.accent, 0.75)
    for _ in range(8):
        _reeds(c, rng, rng.uniform(0, c.w * 0.4), c.h, rng.uniform(70, 150), _shade(mood.near, 0.7))
    _mist(c, rng, waterline - 66, 58, _mix(mood.sun, (255, 255, 255), 0.35), 0.26)
    _foreground(c, rng, _shade(mood.near, 0.7), top=0.97)
    _finish(c, rng, vignette=0.95)


def _scene_deepwood(c: Canvas, rng: random.Random, mood: Mood) -> None:
    """Thorn-choked forest: canopy overhead, receding tree walls, light shafts."""
    horizon = int(c.h * 0.40)
    _sky(c, mood, horizon, mood.near)
    _orb(c, c.w * 0.30, horizon * 0.44, 34, mood, glow_scale=5.0)
    _ranges(c, rng, mood, horizon + c.h * 0.02, 3, spread=0.17, tall=0.17, darken=0.78)
    for _ in range(6):
        x = rng.uniform(c.w * 0.06, c.w * 0.94)
        width = rng.uniform(30, 80)
        for step in range(0, int(c.h * 0.66), 2):
            y = horizon - c.h * 0.12 + step
            if y < 0 or y >= c.h:
                continue
            alpha = 0.085 * math.sin(math.pi * min(1.0, step / (c.h * 0.66)))
            c.blend_row(y, x + step * 0.26 - width / 2, x + step * 0.26 + width / 2, mood.sun,
                        max(0.0, alpha))
    for index in range(8):
        _conifer(c, rng, (index + rng.uniform(0.1, 0.9)) * (c.w / 8), c.h * 1.03,
                 rng.uniform(c.h * 0.42, c.h * 0.62), _shade(mood.near, 0.8))
    for _ in range(7):
        _broadleaf(c, rng, rng.uniform(0, c.w), c.h * 1.01, rng.uniform(c.h * 0.26, c.h * 0.38),
                   _shade(mood.near, 0.85))
    canopy = _ridge(rng, c.w, c.h * 0.05, c.h * 0.11, 5)
    for x, top in enumerate(canopy):
        c.column(x, 0, top, _shade(mood.near, 0.65))
    _haze(c, int(c.h * 0.52), c.h, _mix(mood.sky_low, mood.sun, 0.30), 0.12, 0.02)
    for _ in range(30):
        c.add_pixel(rng.randrange(0, c.w), rng.randrange(int(c.h * 0.4), c.h),
                    _mix(mood.accent, (255, 255, 255), 0.3), rng.uniform(0.25, 0.6))
    _grasses(c, rng, c.h, _shade(mood.near, 0.75), count=130)
    _finish(c, rng, vignette=1.1)


def _scene_outpost(c: Canvas, rng: random.Random, mood: Mood) -> None:
    """Palisade outpost in the deepwood, strung with lanterns."""
    horizon = int(c.h * 0.48)
    _sky(c, mood, horizon, mood.near)
    _stars(c, rng, 110, 0.55)
    _orb(c, c.w * 0.18, horizon * 0.36, 30, mood, glow_scale=4.4)
    _ranges(c, rng, mood, horizon, 2, spread=0.16, tall=0.16)
    ground = c.h * 0.84
    _fill_below(c, _ridge(rng, c.w, ground - c.h * 0.06, c.h * 0.05, 3), mood.mid)
    _pagoda(c, c.w * 0.76, ground - c.h * 0.05, 280, c.h * 0.40, 3, _shade(mood.structure, 0.9),
            _shade(mood.structure, 1.06))
    for x in range(int(c.w * 0.06), int(c.w * 0.86), 46):
        top = ground - c.h * (0.17 if x % 92 < 46 else 0.195)
        c.column(x, top, ground, _shade(mood.structure, 0.84))
        c.polygon([(x - 6, top), (x + 6, top - 34), (x + 18, top)], _shade(mood.structure, 0.7))
    c.row(ground - c.h * 0.145, c.w * 0.06, c.w * 0.86, _shade(mood.structure, 0.95))
    for x in (c.w * 0.16, c.w * 0.30, c.w * 0.44, c.w * 0.58, c.w * 0.70):
        _lantern(c, x, ground - c.h * 0.19, 12, mood.accent, 0.95)
    for x in (c.w * 0.22, c.w * 0.40, c.w * 0.56):
        _hut(c, x, ground - c.h * 0.09, 230, c.h * 0.15, _mix(mood.structure, mood.far, 0.40),
             _shade(mood.structure, 0.88))
    for x in (c.w * 0.02, c.w * 0.96):
        _conifer(c, rng, x, c.h * 1.02, c.h * 0.52, _shade(mood.near, 0.72))
    _haze(c, int(ground - c.h * 0.08), c.h, _mix(mood.mid, mood.near, 0.5), 0.14, 0.22)
    _grasses(c, rng, c.h, _shade(mood.near, 0.75), count=80)
    _finish(c, rng, vignette=1.0)


def _scene_terraces(c: Canvas, rng: random.Random, mood: Mood) -> None:
    """Terraced farms below the capital wall, in full daylight."""
    horizon = int(c.h * 0.34)
    _sky(c, mood, horizon, _mix(mood.sky_low, mood.far, 0.5))
    _orb(c, c.w * 0.80, horizon * 0.42, 42, mood, glow_scale=3.4)
    _cloud(c, c.w * 0.22, horizon * 0.46, c.w * 0.22, 32, (255, 255, 255), 0.34)
    _cloud(c, c.w * 0.54, horizon * 0.30, c.w * 0.18, 24, (255, 255, 255), 0.26)
    _cloud(c, c.w * 0.86, horizon * 0.64, c.w * 0.20, 26, (255, 255, 255), 0.22)
    _ranges(c, rng, mood, horizon + c.h * 0.03, 2, spread=0.14, tall=0.15, darken=0.75)
    wall_y = c.h * 0.68
    _wall(c, int(c.w * 0.48), c.w, wall_y, c.h * 0.22, _mix(mood.structure, mood.far, 0.42), mood.lit)
    _tower(c, c.w * 0.66, wall_y, 200, c.h * 0.40, _mix(mood.structure, mood.far, 0.5),
           _shade(mood.structure, 1.05))
    _tower(c, c.w * 0.90, wall_y, 160, c.h * 0.30, _mix(mood.structure, mood.far, 0.5),
           _shade(mood.structure, 1.05))
    _banner(c, c.w * 0.78, wall_y - c.h * 0.16, 26, 96, mood.lit)
    for _ in range(3):
        _cloud(c, rng.uniform(0, c.w), wall_y - c.h * 0.08 - rng.uniform(0, c.h * 0.05),
               c.w * 0.22, 18, _mix((255, 255, 255), mood.sky_low, 0.2), 0.26)
    band = c.h * 0.115
    for step in range(4):
        top = wall_y + c.h * 0.02 + step * band
        green = _mix((126, 162, 92), (58, 92, 66), step / 5.2)
        profile = [int(top + math.sin((x / c.w) * math.tau * 1.3 + step * 0.7) * band * 0.28)
                   for x in range(c.w)]
        for x, y in enumerate(profile):
            c.column(x, y, int(y + band * 0.94), green)
            c.column(x, y, y + 3, _shade(green, 0.72))
        if step in (1, 3):
            _hut(c, rng.uniform(c.w * 0.08, c.w * 0.44), profile[int(c.w * 0.25)] + band * 0.5,
                 200, 132, _mix(mood.structure, mood.near, 0.4), _shade(mood.structure, 0.8))
    for _ in range(5):
        _broadleaf(c, rng, rng.uniform(0, c.w), c.h * 1.01, rng.uniform(c.h * 0.16, c.h * 0.24),
                   _mix((78, 112, 62), mood.near, 0.3))
    _haze(c, int(wall_y), c.h, _mix(mood.sky_low, mood.far, 0.35), 0.10, 0.04)
    _grasses(c, rng, c.h, _shade(mood.near, 0.68), count=120)
    _finish(c, rng, vignette=0.72, grain=10)


def _scene_mountain_village(c: Canvas, rng: random.Random, mood: Mood) -> None:
    """Rice terraces climbing a mountain shoulder above a spirit river."""
    horizon = int(c.h * 0.30)
    _sky(c, mood, horizon, _mix(mood.sky_low, mood.far, 0.55))
    _orb(c, c.w * 0.22, horizon * 0.44, 38, mood, glow_scale=3.6)
    _cloud(c, c.w * 0.60, horizon * 0.40, c.w * 0.26, 34, (255, 255, 255), 0.30)
    _cloud(c, c.w * 0.20, horizon * 0.70, c.w * 0.30, 24, (255, 255, 255), 0.20)
    _ranges(c, rng, mood, horizon + c.h * 0.02, 2, spread=0.06, tall=0.20, darken=0.8)
    band = c.h * 0.135
    for step in range(4):
        top = c.h * 0.40 + step * band
        green = _mix((132, 168, 104), (62, 96, 70), step / 4.6)
        profile = [int(top + math.sin((x / c.w) * math.tau * (1.05 + step * 0.18) + step) * band * 0.30)
                   for x in range(c.w)]
        for x, y in enumerate(profile):
            c.column(x, y, int(y + band * 0.95), green)
            c.column(x, y, y + 3, _shade(green, 0.74))
    for cx, w, h in ((c.w * 0.22, 240, 158), (c.w * 0.40, 200, 132), (c.w * 0.56, 268, 176)):
        _hut(c, cx, c.h * 0.82, w, h, _mix(mood.structure, mood.far, 0.42), _shade(mood.structure, 0.8))
        _lantern(c, cx, c.h * 0.82 + 16, 9, mood.accent, 0.5)
    _pagoda(c, c.w * 0.82, c.h * 0.78, 240, c.h * 0.33, 3, _shade(mood.structure, 0.88),
            _shade(mood.structure, 1.08))
    river = [int(c.w * 0.62 + math.sin(y * 0.012) * 60) for y in range(c.h)]
    for y in range(int(c.h * 0.58), c.h):
        half = 22 + (y - c.h * 0.58) * 0.5
        c.row(y, river[y] - half, river[y] + half,
              _mix((178, 206, 208), (92, 128, 148), (y - c.h * 0.58) / (c.h * 0.42)))
    for _ in range(4):
        _broadleaf(c, rng, rng.uniform(0, c.w * 0.55), c.h * 1.01, rng.uniform(c.h * 0.14, c.h * 0.22),
                   _mix((84, 118, 66), mood.near, 0.3))
    _haze(c, int(c.h * 0.55), c.h, _mix(mood.sky_low, mood.far, 0.32), 0.09, 0.03)
    _grasses(c, rng, c.h, _shade(mood.near, 0.72), count=110)
    _finish(c, rng, vignette=0.72, grain=10)


def _scene_peaks(c: Canvas, rng: random.Random, mood: Mood) -> None:
    """Trial peaks above a sea of cloud, with a pagoda and a long waterfall."""
    horizon = int(c.h * 0.44)
    _sky(c, mood, horizon, _mix(mood.sky_low, mood.mid, 0.4))
    _orb(c, c.w * 0.70, horizon * 0.34, 40, mood, glow_scale=3.8)
    _cloud(c, c.w * 0.28, horizon * 0.48, c.w * 0.28, 28, _shade(mood.lit, 0.9), 0.22)
    far = _ridge(rng, c.w, horizon - c.h * 0.10, c.h * 0.17, 3)
    _fill_below(c, far, _mix(mood.far, mood.sky_low, 0.30))
    peaks = _ridge(rng, c.w, horizon + c.h * 0.02, c.h * 0.20, 3)
    _fill_below(c, peaks, _mix(mood.mid, mood.far, 0.35))
    _tree_line(c, rng, horizon + c.h * 0.06, 16, c.h * 0.07, _mix(mood.mid, mood.near, 0.4), 0.9)
    cloud_sea = int(c.h * 0.76)
    _fill_below(c, _ridge(rng, c.w, cloud_sea, c.h * 0.022, 3), _mix(mood.sky_low, (255, 255, 255), 0.4))
    for step in range(3):
        _cloud(c, rng.uniform(0, c.w), cloud_sea + 10 + step * 26, c.w * 0.32, 22,
               _mix((255, 255, 255), mood.sky_low, 0.18), 0.36)
    _pagoda(c, c.w * 0.30, cloud_sea - 8, 260, c.h * 0.34, 3, _shade(mood.structure, 0.9),
            _shade(mood.structure, 1.06))
    fall_x = c.w * 0.68
    fall_top = int(horizon + c.h * 0.10)
    for y in range(fall_top, cloud_sea + 18):
        width = 14 + (y - fall_top) * 0.05
        c.row(y, fall_x - width / 2, fall_x + width / 2, _mix((238, 246, 250), mood.far, 0.25))
    c.glow(fall_x, cloud_sea + 16, 70, (255, 255, 255), 0.24)
    for x in (c.w * 0.06, c.w * 0.94):
        _conifer(c, rng, x, c.h * 1.02, c.h * 0.44, _shade(mood.near, 0.78))
    _finish(c, rng, vignette=0.8)


def _scene_canyon_market(c: Canvas, rng: random.Random, mood: Mood) -> None:
    """A lantern market inside a canyon that only appears when the fog thins."""
    _sky(c, mood, c.h, mood.near)
    _stars(c, rng, 170, 0.75)
    _orb(c, c.w * 0.48, c.h * 0.14, 26, mood, glow_scale=4.2)
    _fill_below(c, _ridge(rng, c.w, c.h * 0.42, c.h * 0.11, 3), _mix(mood.far, mood.mid, 0.45))
    floor = c.h * 0.80
    for side in (-1, 1):
        base_x = 0.0 if side < 0 else float(c.w)
        for y in range(c.h):
            depth = 90 + 210 * math.sin((y / c.h) * 2.0) ** 2
            edge = base_x + side * depth
            if side < 0:
                c.row(y, 0, edge, _mix(mood.near, mood.structure, 0.45))
            else:
                c.row(y, edge, c.w, _mix(mood.near, mood.structure, 0.45))
    c.glow(c.w * 0.5, floor - 40, 560, mood.accent, 0.20)
    _mist(c, rng, int(floor - c.h * 0.22), 70, _mix(mood.far, (255, 255, 255), 0.25), 0.16, width_scale=0.94)
    _fill_below(c, _ridge(rng, c.w, floor - 20, c.h * 0.02, 3), _mix(mood.near, mood.structure, 0.55))
    for index, x in enumerate(range(int(c.w * 0.16), int(c.w * 0.86), 132)):
        stall_y = floor - 6 - (index % 2) * 30
        _hut(c, x, stall_y, 200, 128, _mix(mood.structure, mood.far, 0.40),
             _mix(mood.accent, mood.structure, 0.55))
        c.column(x, stall_y - 190, stall_y - 128, _shade(mood.structure, 0.8))
        _lantern(c, x, stall_y - 124, 11, mood.accent, 0.95)
    for _ in range(16):
        _lantern(c, rng.uniform(c.w * 0.10, c.w * 0.90), rng.uniform(c.h * 0.12, c.h * 0.40), 4,
                 mood.accent, 0.5)
    for _ in range(6):
        _banner(c, rng.uniform(c.w * 0.12, c.w * 0.88), rng.uniform(c.h * 0.30, c.h * 0.50), 26, 46,
                mood.lit)
    _mist(c, rng, int(c.h * 0.56), 70, _mix(mood.far, (255, 255, 255), 0.22), 0.16, width_scale=0.9)
    _mist(c, rng, int(c.h * 0.84), 60, _mix(mood.near, (255, 255, 255), 0.18), 0.13, width_scale=0.8)
    _finish(c, rng, vignette=1.2)


def _scene_sea_pavilion(c: Canvas, rng: random.Random, mood: Mood) -> None:
    """White-coral pavilion moored on the tide, lantern strings, moon path."""
    horizon = int(c.h * 0.46)
    waterline = int(c.h * 0.64)
    _sky(c, mood, horizon, _mix(mood.far, mood.water_lo, 0.42))
    _stars(c, rng, 90, 0.5)
    _orb(c, c.w * 0.60, horizon * 0.38, 36, mood, glow_scale=5.0)
    _cloud(c, c.w * 0.24, horizon * 0.58, c.w * 0.26, 24, _shade(mood.lit, 0.85), 0.18)
    _fill_below(c, _ridge(rng, c.w, horizon - c.h * 0.01, c.h * 0.05, 3), _mix(mood.far, mood.mid, 0.4))
    _mist(c, rng, waterline - int(c.h * 0.30), 90, _mix(mood.sun, (255, 255, 255), 0.4), 0.28)
    for x in range(int(c.w * 0.22), int(c.w * 0.80)):
        c.column(x, waterline - 70, waterline - 34, _mix((226, 228, 232), mood.structure, 0.4))
    for x in range(int(c.w * 0.26), int(c.w * 0.76), 62):
        c.column(x, waterline - 34, waterline + 40, _shade(mood.structure, 0.58))
    _pagoda(c, c.w * 0.50, waterline - 70, 330, c.h * 0.42, 3, _mix((228, 230, 236), mood.structure, 0.35),
            _shade(mood.structure, 1.02))
    for x in range(int(c.w * 0.12), int(c.w * 0.90), 78):
        c.column(x, waterline - 150, waterline - 120, _shade(mood.structure, 0.7))
        _lantern(c, x, waterline - 108, 10, mood.accent, 0.8)
    _boat(c, c.w * 0.16, waterline + 60, 300, _shade(mood.structure, 0.74), 160, _shade(mood.lit, 0.5))
    _boat(c, c.w * 0.88, waterline + 130, 240, _shade(mood.structure, 0.68), 100, (0, 0, 0))
    _water(c, rng, mood, waterline, depth=300)
    c.glow(c.w * 0.60, waterline + 60, 220, mood.sun, 0.18)
    _mist(c, rng, waterline - 44, 44, _mix(mood.water_hi, (255, 255, 255), 0.4), 0.09)
    _finish(c, rng, vignette=1.0)


def _scene_cove(c: Canvas, rng: random.Random, mood: Mood) -> None:
    """Pirate cove: a crooked headland, beached hulls, bonfires on the sand."""
    horizon = int(c.h * 0.36)
    waterline = int(c.h * 0.62)
    _sky(c, mood, horizon, _mix(mood.far, mood.water_lo, 0.38))
    _orb(c, c.w * 0.28, horizon * 0.54, 42, mood, glow_scale=4.4)
    _cloud(c, c.w * 0.66, horizon * 0.36, c.w * 0.28, 28, _shade(mood.lit, 0.8), 0.18)
    _ranges(c, rng, mood, horizon + c.h * 0.02, 2, spread=0.04, tall=0.13)
    head = [int(c.h * 0.50 + math.sin((x / c.w) * math.tau * 1.1) * 90 - (x / c.w) * 90)
            for x in range(c.w)]
    for x, top in enumerate(head):
        if x > c.w * 0.62:
            c.column(x, top, c.h, _mix(mood.near, mood.structure, 0.45))
    _mist(c, rng, int(c.h * 0.52), 90, _mix(mood.sun, (255, 255, 255), 0.35), 0.24)
    sand_y = c.h * 0.86
    for y in range(int(sand_y), c.h):
        c.row(y, 0, c.w * 0.72, _mix(_mix(mood.mid, (176, 142, 96), 0.5), mood.near,
                                     (y - sand_y) / max(1, c.h - sand_y)))
    _boat(c, c.w * 0.26, sand_y - 6, 430, _shade(mood.structure, 0.76), 230, _shade(mood.lit, 0.5))
    _boat(c, c.w * 0.56, sand_y - 30, 300, _shade(mood.structure, 0.64), 150, (0, 0, 0))
    for _ in range(4):
        x = rng.uniform(c.w * 0.10, c.w * 0.58)
        y = rng.uniform(sand_y - 40, c.h - 40)
        c.glow(x, y, 110, (255, 156, 76), 0.50)
        _rock(c, x, y + 12, 52, 26, _shade(mood.structure, 0.72))
    for _ in range(5):
        _rock(c, rng.uniform(0, c.w * 0.6), rng.uniform(sand_y - 90, sand_y - 20),
              rng.uniform(60, 170), rng.uniform(30, 70), _shade(mood.near, 0.85))
    _lantern(c, c.w * 0.14, sand_y - 120, 7, mood.accent, 0.8)
    _water(c, rng, mood, waterline, depth=240)
    _mist(c, rng, waterline - 34, 46, _mix(mood.water_hi, mood.sun, 0.4), 0.10)
    _foreground(c, rng, _shade(mood.near, 0.68), top=0.98)
    _finish(c, rng, vignette=1.15)


def _scene_atoll(c: Canvas, rng: random.Random, mood: Mood) -> None:
    """Drowned prison: coral towers standing in a grey reef sea, in rain."""
    horizon = int(c.h * 0.50)
    waterline = int(c.h * 0.62)
    _sky(c, mood, horizon, _mix(mood.far, mood.water_lo, 0.5))
    _orb(c, c.w * 0.50, horizon * 0.28, 26, mood, glow_scale=6.0)
    _cloud(c, c.w * 0.22, horizon * 0.30, c.w * 0.36, 34, _shade(mood.sky_low, 1.04), 0.46)
    _cloud(c, c.w * 0.76, horizon * 0.50, c.w * 0.32, 28, _shade(mood.sky_low, 1.08), 0.40)
    _fill_below(c, _ridge(rng, c.w, horizon - c.h * 0.01, c.h * 0.05, 3), _mix(mood.far, mood.mid, 0.5))
    _mist(c, rng, int(waterline - c.h * 0.30), 90, _mix(mood.sky_low, (255, 255, 255), 0.45), 0.26)
    for cx, width, height in ((c.w * 0.26, 200, c.h * 0.34), (c.w * 0.52, 270, c.h * 0.50),
                              (c.w * 0.78, 180, c.h * 0.29)):
        _tower(c, cx, waterline + 16, width, height, _mix(mood.near, (118, 116, 124), 0.42),
               _shade(mood.structure, 0.9))
        for bar in range(3):
            c.row(waterline + 16 - height * (0.30 + bar * 0.20), cx - width * 0.3, cx + width * 0.3,
                  _shade(mood.structure, 0.32))
    reef = [int(waterline + 20 - c.h * 0.03 * max(0.0, math.sin(x * 0.05) ** 14))
            for x in range(c.w)]
    for x, top in enumerate(reef):
        c.column(x, top, c.h, _mix(mood.water_lo, mood.near, 0.4))
    _water(c, rng, mood, waterline, depth=280)
    for _ in range(6):
        _rock(c, rng.uniform(0, c.w), rng.uniform(waterline + 26, waterline + 110),
              rng.uniform(70, 170), rng.uniform(28, 64), _shade(mood.water_lo, 1.12))
    for _ in range(150):
        x = rng.randrange(0, c.w)
        top = rng.randrange(0, int(c.h * 0.6))
        length = rng.randrange(int(c.h * 0.08), int(c.h * 0.3))
        c.blend_row(top + length // 2, x, x + 1, _mix(mood.sky_low, (255, 255, 255), 0.5), 0.35)
    _mist(c, rng, waterline - 24, 70, _mix(mood.sky_low, (255, 255, 255), 0.3), 0.14)
    _finish(c, rng, vignette=1.15, grain=10)


def _scene_open_sea(c: Canvas, rng: random.Random, mood: Mood) -> None:
    """The mist expanse: a white void, hidden reefs, and a lone sail."""
    horizon = int(c.h * 0.52)
    waterline = int(c.h * 0.60)
    _sky(c, mood, horizon, _mix(mood.sky_low, (206, 212, 214), 0.45))
    _orb(c, c.w * 0.42, horizon * 0.42, 32, mood, glow_scale=6.5)
    for cx, scale in ((c.w * 0.82, 0.5), (c.w * 0.16, 0.34)):
        _fill_below(c, _ridge(rng, c.w, horizon - c.h * 0.02 * scale, c.h * 0.035 * scale, 3),
                    _mix(mood.far, mood.sky_low, 0.62))
    _fill_below(c, _ridge(rng, c.w, waterline - c.h * 0.006, c.h * 0.012, 3),
                _mix(mood.far, mood.sky_low, 0.5))
    _mist(c, rng, horizon - 80, 150, _mix(mood.sky_low, (255, 255, 255), 0.55), 0.24)
    _boat(c, c.w * 0.62, waterline + 30, 340, _shade(mood.structure, 0.62), 230, _shade(mood.lit, 0.45))
    _water(c, rng, mood, waterline, depth=340)
    for _ in range(5):
        _rock(c, rng.uniform(0, c.w), rng.uniform(waterline + 40, waterline + 140),
              rng.uniform(60, 150), rng.uniform(24, 60), _shade(mood.water_lo, 1.08))
    _mist(c, rng, int(c.h * 0.66), 100, _mix(mood.sky_low, (255, 255, 255), 0.6), 0.18)
    _mist(c, rng, int(c.h * 0.88), 80, _mix(mood.sky_low, (255, 255, 255), 0.5), 0.12)
    _finish(c, rng, vignette=0.85, grain=10)


def _scene_forge_city(c: Canvas, rng: random.Random, mood: Mood) -> None:
    """Furnace pillar city: a skyline of pagodas and chimneys over ember light."""
    horizon = int(c.h * 0.52)
    _sky(c, mood, horizon, _mix(mood.accent, mood.near, 0.55))
    _stars(c, rng, 90, 0.45)
    _orb(c, c.w * 0.82, horizon * 0.30, 26, mood, glow_scale=4.0)
    _fill_below(c, _ridge(rng, c.w, horizon - c.h * 0.02, c.h * 0.05, 3), _mix(mood.far, mood.accent, 0.18))
    skyline = c.h * 0.78
    _mist(c, rng, int(skyline - c.h * 0.30), 110, _mix(mood.accent, (255, 255, 255), 0.35), 0.30)
    c.glow(c.w * 0.44, skyline - 40, 640, mood.accent, 0.26)
    _fill_below(c, _ridge(rng, c.w, skyline - c.h * 0.02, c.h * 0.02, 3), mood.near)
    for index, cx in enumerate(range(int(c.w * 0.10), int(c.w * 0.95), 330)):
        _pagoda(c, cx, skyline, 170, c.h * (0.22 + 0.06 * (index % 3)), 3, _shade(mood.structure, 0.95),
                _shade(mood.structure, 1.08))
        for light in (-1, 1):
            c.column(cx + light * 26, skyline - c.h * 0.08, skyline - c.h * 0.055, mood.accent)
    for index, cx in enumerate(range(int(c.w * 0.24), int(c.w * 0.92), 430)):
        chimney_h = c.h * (0.30 + 0.06 * (index % 4))
        c.column(cx, skyline - chimney_h, skyline, _shade(mood.structure, 0.8))
        c.row(skyline - chimney_h, cx - 16, cx + 16, _shade(mood.structure, 1.1))
        for step in range(int(chimney_h * 1.4)):
            y = skyline - chimney_h - step
            if y < 0:
                break
            c.blend_row(y, cx + math.sin(step * 0.05 + index) * 30 - (18 + step * 0.5),
                        cx + math.sin(step * 0.05 + index) * 30 + (18 + step * 0.5),
                        _mix(mood.sky_low, mood.accent, 0.35), 0.09 * (1.0 - step / (chimney_h * 1.4)))
    for x in (c.w * 0.20, c.w * 0.50, c.w * 0.80):
        c.glow(x, skyline - 24, 150, mood.accent, 0.34)
        _lantern(c, x, skyline - 16, 8, mood.accent, 0.45)
    _haze(c, horizon, c.h, _mix(mood.accent, mood.near, 0.5), 0.08, 0.20)
    _finish(c, rng, vignette=1.0)


def _scene_fortress(c: Canvas, rng: random.Random, mood: Mood) -> None:
    """Ash-grey basalt fortress: battlements, war pavilions, banners, embers."""
    horizon = int(c.h * 0.44)
    _sky(c, mood, horizon, _mix(mood.far, mood.accent, 0.22))
    _orb(c, c.w * 0.16, horizon * 0.46, 30, mood, glow_scale=4.4)
    _cloud(c, c.w * 0.58, horizon * 0.32, c.w * 0.36, 32, _shade(mood.sky_low, 1.02), 0.44)
    _cloud(c, c.w * 0.88, horizon * 0.56, c.w * 0.24, 24, _shade(mood.sky_low, 1.06), 0.36)
    _ranges(c, rng, mood, horizon + c.h * 0.03, 2, spread=0.05, tall=0.12)
    ground = c.h * 0.82
    _fill_below(c, _ridge(rng, c.w, ground - c.h * 0.04, c.h * 0.03, 3), _mix(mood.near, mood.structure, 0.35))
    _mist(c, rng, int(c.h * 0.50), 120, _mix(mood.sky_low, (255, 255, 255), 0.4), 0.30)
    wall_y = c.h * 0.72
    _wall(c, int(c.w * 0.02), int(c.w * 0.70), wall_y, c.h * 0.24,
          _mix(mood.structure, (92, 88, 92), 0.32), mood.accent)
    _tower(c, c.w * 0.18, wall_y, 230, c.h * 0.40, _mix(mood.structure, (84, 80, 84), 0.38),
           _shade(mood.structure, 1.0))
    _tower(c, c.w * 0.48, wall_y, 190, c.h * 0.32, _mix(mood.structure, (84, 80, 84), 0.38),
           _shade(mood.structure, 1.0))
    for index, x in enumerate((c.w * 0.10, c.w * 0.30, c.w * 0.42, c.w * 0.62)):
        _banner(c, x, wall_y - c.h * 0.20 - index * 8, 30, 110, _shade((148, 50, 46), 0.82 + index * 0.05))
    for index, cx in enumerate(range(int(c.w * 0.70), int(c.w * 1.0), 168)):
        _hut(c, cx, ground - c.h * 0.06, 210, c.h * 0.15 + (index % 2) * 16, _shade(mood.structure, 0.72),
             _shade(mood.structure, 0.86))
    for _ in range(5):
        x = rng.uniform(c.w * 0.70, c.w)
        c.glow(x, ground - 30, 130, (255, 142, 68), 0.40)
        _rock(c, x, ground - 10, 52, 26, _shade(mood.structure, 0.62))
    for _ in range(26):
        c.blend_row(rng.randrange(0, int(c.h * 0.8)), rng.uniform(0, c.w),
                    rng.uniform(40, 160), mood.sky_low, 0.05)
    _haze(c, horizon, c.h, _mix(mood.sky_low, mood.near, 0.5), 0.12, 0.20)
    _foreground(c, rng, _shade(mood.near, 0.7), top=0.96)
    _finish(c, rng, vignette=1.2)


def _scene_shrine(c: Canvas, rng: random.Random, mood: Mood) -> None:
    """Abandoned shrine chain: stone steps, a tiered temple, pines, low mist."""
    horizon = int(c.h * 0.34)
    _sky(c, mood, horizon, _mix(mood.sky_low, mood.mid, 0.42))
    _orb(c, c.w * 0.20, horizon * 0.42, 36, mood, glow_scale=4.2)
    _cloud(c, c.w * 0.64, horizon * 0.44, c.w * 0.28, 24, _shade(mood.lit, 0.85), 0.18)
    _ranges(c, rng, mood, horizon + c.h * 0.02, 2, spread=0.18, tall=0.16)
    _mist(c, rng, int(c.h * 0.52), 130, _mix(mood.sky_low, (255, 255, 255), 0.40), 0.28, width_scale=0.9)
    plinth = c.h * 0.80
    for step in range(8):
        y = plinth - step * c.h * 0.016
        half = (c.w * 0.10) - step * 9
        c.row(y, c.w * 0.42 - half, c.w * 0.42 + half, _mix(mood.structure, (144, 140, 130), 0.32))
    _pagoda(c, c.w * 0.42, plinth - c.h * 0.115, 320, c.h * 0.36, 3,
            _mix(mood.structure, (126, 122, 116), 0.38), _shade(mood.structure, 1.0))
    for x in (c.w * 0.10, c.w * 0.24, c.w * 0.64, c.w * 0.80, c.w * 0.94):
        _conifer(c, rng, x, c.h * 1.02, rng.uniform(c.h * 0.42, c.h * 0.62),
                 _mix(mood.mid, mood.near, 0.28))
    for x in (c.w * 0.30, c.w * 0.54):
        _lantern(c, x, plinth - c.h * 0.03, 6, mood.accent, 0.55)
        c.column(x, plinth - c.h * 0.03, plinth, _shade(mood.structure, 0.7))
    _haze(c, int(c.h * 0.62), c.h, _mix(mood.sky_low, mood.far, 0.38), 0.10, 0.05)
    _grasses(c, rng, c.h, _shade(mood.near, 0.75), count=90)
    _foreground(c, rng, _shade(mood.near, 0.66), top=0.97)
    _finish(c, rng, vignette=1.05)


def _scene_undercroft(c: Canvas, rng: random.Random, mood: Mood) -> None:
    """Buried rune-hall: stalactites, pillars, glowing circuits, a dark pool."""
    _sky(c, mood, c.h, mood.near)
    floor = c.h * 0.78
    for x in range(c.w):
        c.column(x, 0, int(c.h * 0.03 + rng.uniform(0, 30)), _mix(mood.near, mood.structure, 0.6))
    for _ in range(30):
        x = rng.randrange(0, c.w)
        length = rng.uniform(c.h * 0.06, c.h * 0.24)
        width = rng.uniform(18, 60)
        c.polygon([(x - width / 2, 0), (x, length), (x + width / 2, 0)], _shade(mood.structure, 0.8))
    c.glow(c.w * 0.5, floor - 60, 700, mood.accent, 0.14)
    for index, x in enumerate(range(int(c.w * 0.02), c.w, 250)):
        width = 150 + (index % 2) * 48
        c.column(x - width / 2, int(c.h * 0.10), floor, _shade(mood.structure, 0.92))
        c.column(x + width / 2, int(c.h * 0.10), floor, _shade(mood.structure, 0.74))
        c.row(int(c.h * 0.10), x - width / 2, x + width / 2, _shade(mood.structure, 1.12))
        c.row(floor - 20, x - width * 0.85, x + width * 0.85, _shade(mood.structure, 0.86))
    _fill_below(c, _ridge(rng, c.w, floor, c.h * 0.012, 3), _mix(mood.near, mood.structure, 0.5))
    for _ in range(18):
        _rune(c, rng.uniform(c.w * 0.04, c.w * 0.96), rng.uniform(floor + 8, c.h * 0.95),
              rng.uniform(12, 30), mood.accent, rng)
    pool_y = int(c.h * 0.92)
    for y in range(pool_y, c.h):
        t = (y - pool_y) / max(1, c.h - pool_y)
        c.row(y, c.w * 0.14, c.w * 0.60, _mix(mood.water_lo, mood.accent, 0.10 + t * 0.20))
    c.glow(c.w * 0.36, pool_y + 24, 220, mood.accent, 0.20)
    c.glow(c.w * 0.08, floor - 40, 170, (255, 156, 74), 0.30)
    c.glow(c.w * 0.90, floor - 30, 190, (255, 156, 74), 0.28)
    _haze(c, int(c.h * 0.22), c.h, _mix(mood.structure, mood.accent, 0.10), 0.05, 0.22)
    _foreground(c, rng, _shade(mood.near, 0.6), top=0.99)
    _finish(c, rng, vignette=1.3)


def _rune(c: Canvas, x: float, y: float, size: float, color: RGB, rng: random.Random) -> None:
    """A carved glyph: a few strokes, glowing faintly."""
    c.glow(x, y, size * 3.0, color, 0.18)
    for _ in range(rng.randint(2, 4)):
        if rng.random() < 0.5:
            c.row(y + rng.uniform(-size, size), x - size / 2, x + size / 2, _mix(color, (255, 255, 255), 0.25))
        else:
            c.column(x + rng.uniform(-size / 2, size / 2), y - size / 2, y + size / 2,
                     _mix(color, (255, 255, 255), 0.25))


def _scene_ascension(c: Canvas, rng: random.Random, mood: Mood) -> None:
    """The last stair: drifting star-field, floating rune rings, the gate above."""
    _sky(c, mood, c.h, mood.near)
    _stars(c, rng, 380, 0.95)
    for _ in range(3):
        cx, cy = rng.uniform(c.w * 0.1, c.w * 0.9), rng.uniform(c.h * 0.10, c.h * 0.45)
        radius = rng.uniform(100, 200)
        for step in range(int(radius * 2)):
            angle = math.pi * step / radius
            c.add_pixel(cx + math.cos(angle) * radius, cy + math.sin(angle) * radius * 0.28, mood.sun, 0.30)
    c.glow(c.w * 0.52, c.h * 0.32, 560, mood.accent, 0.20)
    gate_x, gate_y = c.w * 0.52, c.h * 0.34
    for ring in range(5):
        rx = 196 + ring * 48
        ry = 60 + ring * 16
        thickness = 3 + ring
        points = [
            (gate_x + math.cos(math.pi * step / 90) * rx, gate_y + math.sin(math.pi * step / 90) * ry)
            for step in range(180)
        ]
        _ring(c, points, _mix(mood.accent, (255, 255, 255), 0.16 - ring * 0.02), thickness)
    c.glow(gate_x, gate_y, 320, mood.sun, 0.30)
    c.circle(gate_x, gate_y, 48, _mix(mood.sun, mood.sky_top, 0.22))
    for _ in range(30):
        angle = rng.uniform(0, math.tau)
        radius = rng.uniform(230, 470)
        x = gate_x + math.cos(angle) * radius
        y = gate_y + math.sin(angle) * radius * 0.32
        if 0 <= x < c.w and 0 <= y < c.h:
            _rune(c, x, y, rng.uniform(10, 24), mood.accent, rng)
    stair_base = c.h * 1.04
    for step in range(28):
        y = stair_base - step * c.h * 0.018
        half = c.w * 0.30 - step * 13
        c.row(y, gate_x - half, gate_x + half, _shade(mood.structure, 0.9 + step * 0.02))
        c.row(y + 6, gate_x - half, gate_x + half, _shade(mood.near, 0.9))
    for side in (-1, 1):
        x = gate_x + side * c.w * 0.30
        for step in range(9):
            c.column(x + rng.uniform(-3, 3), c.h * 0.60 + step * c.h * 0.022,
                     c.h * 0.72 + step * c.h * 0.022, _shade(mood.structure, 0.8))
    _haze(c, int(c.h * 0.72), c.h, _mix(mood.accent, mood.near, 0.4), 0.05, 0.18)
    _finish(c, rng, vignette=1.2, grain=12)


def _ring(c: Canvas, points: Sequence[Point], color: RGB, thickness: int) -> None:
    for x, y in points:
        for dx in range(-thickness, thickness + 1):
            for dy in range(-2, 3):
                c.add_pixel(x + dx, y + dy, color, 0.42)


SCENE_BUILDERS: Dict[str, Callable[[Canvas, random.Random, Mood], None]] = {
    "wharf": _scene_wharf,
    "deepwood": _scene_deepwood,
    "outpost": _scene_outpost,
    "terraces": _scene_terraces,
    "mountain_village": _scene_mountain_village,
    "peaks": _scene_peaks,
    "canyon_market": _scene_canyon_market,
    "sea_pavilion": _scene_sea_pavilion,
    "cove": _scene_cove,
    "atoll": _scene_atoll,
    "open_sea": _scene_open_sea,
    "forge_city": _scene_forge_city,
    "fortress": _scene_fortress,
    "shrine": _scene_shrine,
    "undercroft": _scene_undercroft,
    "ascension": _scene_ascension,
}


def scene_for(location: Dict[str, object]) -> Tuple[str, str]:
    """Return ``(mood name, scene builder name)`` for a location."""
    kind = str(location.get("location_type", ""))
    if kind in SCENES:
        return SCENES[kind]
    zone = str(location.get("zone", ""))
    if zone in ZONE_FALLBACK:
        return "dusk", ZONE_FALLBACK[zone]
    return "dawn", "peaks"


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------
def render(location: Dict[str, object]) -> Canvas:
    """Compose the scene for one location, deterministically."""
    seed = int(hashlib.md5(str(location["id"]).encode("utf-8")).hexdigest()[:8], 16)
    rng = random.Random(seed)
    mood_name, scene_name = scene_for(location)
    canvas = Canvas(WIDTH, HEIGHT)
    SCENE_BUILDERS[scene_name](canvas, rng, MOODS[mood_name])
    return canvas


def _write_png(path: Path, canvas: Canvas) -> None:
    def chunk(tag: bytes, data: bytes) -> bytes:
        payload = struct.pack(">I", len(data)) + tag + data
        return payload + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = bytearray()
    stride = canvas.w * 3
    data = canvas.data
    for y in range(canvas.h):
        raw.append(0)
        raw += data[y * stride : (y + 1) * stride]

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
        + chunk(b"IEND", b"")
    )


def _uid_for(res_path: str) -> str:
    """A stable, unique Godot uid text derived from the resource path."""
    digest = hashlib.md5(res_path.encode("utf-8")).digest()
    return "uid://" + base64.b32encode(digest).decode("ascii").lower().rstrip("=")[:13]


def _write_import(path: Path, res_path: str) -> None:
    digest = hashlib.md5(res_path.encode("utf-8")).hexdigest()
    name = res_path.rsplit("/", 1)[-1]
    content = f"""[remap]

importer="texture"
type="CompressedTexture2D"
uid="{_uid_for(res_path)}"
path="res://.godot/imported/{name}-{digest}.ctex"
metadata={{
"vram_texture": false
}}

[deps]

source_file="{res_path}"
dest_files=["res://.godot/imported/{name}-{digest}.ctex"]

[params]

compress/mode=0
compress/high_quality=false
compress/lossy_quality=0.7
compress/uastc_level=0
compress/rdo_quality_loss=0.0
compress/hdr_compression=1
compress/normal_map=0
compress/channel_pack=0
mipmaps/generate=false
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
"""
    path.write_text(content, encoding="utf-8")


def _load_locations() -> List[Dict[str, object]]:
    data = json.loads(LOCATIONS.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("game/data/locations.json must hold a list of locations")
    return data


def missing(only: Sequence[str] | None = None) -> List[Dict[str, object]]:
    """Return the locations this run should draw: gaps, or the named ``only`` ids.

    Naming an id is the only way to redraw an existing PNG, so hand-painted
    location art is never collateral damage.
    """
    entries = _load_locations()
    if only:
        wanted = {str(entry_id) for entry_id in only}
        found = {str(entry["id"]) for entry in entries} & wanted
        unknown = sorted(wanted - found)
        if unknown:
            raise SystemExit(f"unknown location id(s): {', '.join(unknown)}")
        return [entry for entry in entries if str(entry["id"]) in wanted]
    return [entry for entry in entries if not (ASSETS / f"{entry['id']}.png").exists()]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--list", action="store_true", help="report gaps without writing")
    parser.add_argument(
        "--location",
        nargs="+",
        metavar="ID",
        default=None,
        help="redraw these location ids (the only way to overwrite an existing PNG)",
    )
    args = parser.parse_args(argv)

    targets = missing(only=args.location)
    if args.list:
        print(f"{len(targets)} location(s) without artwork:")
        for entry in targets:
            mood_name, scene_name = scene_for(entry)
            print(f"  {entry['id']}  ({entry.get('display_name', '?')}) -> {scene_name}/{mood_name}")
        return 0
    if not targets:
        print("every location already has artwork")
        return 0

    uids: Dict[str, str] = {}
    for entry in targets:
        location_id = str(entry["id"])
        res_path = f"res://assets/locations/{location_id}.png"
        uid = _uid_for(res_path)
        if uid in uids:
            raise SystemExit(f"uid collision between {location_id} and {uids[uid]}")
        uids[uid] = location_id
        png = ASSETS / f"{location_id}.png"
        _write_png(png, render(entry))
        _write_import(Path(str(png) + ".import"), res_path)
        mood_name, scene_name = scene_for(entry)
        print(f"wrote {png.name}  [{scene_name}/{mood_name}]")
    print(f"{len(targets)} scene image(s) written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
