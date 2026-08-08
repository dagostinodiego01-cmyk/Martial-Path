"""Martial Path UI theme - dark charcoal / gold design system.

The palette implements the "dark fantasy cultivation RPG" direction defined in
``martial_path_final_ui_implementation_brief.md``: a near-black charcoal canvas,
fine gold borders and headings, warm off-white body text, and a small set of
category accent colours (red HP, blue Qi, green Body, purple Essence).

HOW TO USE IN A GAME UI
-----------------------
DOMINANT (large areas, ~70%):
    BACKGROUND (near-black), PANEL (charcoal), TEXT_PRIMARY (warm off-white).
SUPPORTING (structure & emphasis, ~25%):
    GOLD / BORDER_STRONG for headers, borders, primary accents.
ACCENTS (sparingly, ~5% - never large fills):
    HP_COLOR (red), QI_COLOR (blue), BODY_GREEN, ESSENCE_PURPLE, INVENTORY_BLUE.

Every value is a plain hex string so the palette stays framework-agnostic: it
feeds the PySide6 GUI (via QSS) and could feed a future web UI (via CSS) or the
CLI. Colours are tuned for readability and long-session comfort on a dark
surface. This module holds no gameplay logic and performs no I/O.
"""
from __future__ import annotations

from typing import Dict, Tuple

# ============================================================
# BACKGROUNDS  (dominant surfaces, ~70%)
# ============================================================
BACKGROUND = "#05080B"      # app / root canvas - the dominant near-black
PANEL = "#0B1118"           # cards, side panels, tab bodies
PANEL_RAISED = "#101923"    # raised surface / buttons / progress troughs
PANEL_SOFT = "#111820"      # soft inset rows (empty inventory slots, list rows)
HEADER = "#0B1118"          # top bar strip

# ============================================================
# GOLD BRAND  (structure & emphasis, ~25%)
# ============================================================
GOLD = "#D6A64A"            # primary gold - headings, borders, primary accents
GOLD_BRIGHT = "#F0C76A"     # brighter gold - hover, highlights, title
BORDER = "#4B3820"          # fine warm border on dark panels
BORDER_STRONG = "#A9792B"   # stronger gold border / framed containers

# Backwards-compatible brand aliases (brand -> gold).
PRIMARY = GOLD
PRIMARY_DARK = BORDER_STRONG
BLACK = BACKGROUND
CHARCOAL = PANEL_RAISED

# ============================================================
# TEXT
# ============================================================
TEXT_PRIMARY = "#F2E8D5"    # warm off-white - primary text on dark surfaces
TEXT_SECONDARY = "#C7BCA8"  # beige - captions, secondary labels
TEXT_MUTED = "#8F8A81"      # muted grey-beige - disabled / faint metadata
TEXT_ON_ACCENT = "#0B0A07"  # near-black text sitting on gold fills
TEXT_LINK = "#51BDED"       # hyperlink text

# ============================================================
# CATEGORY ACCENTS  (use sparingly, ~5%)
# ============================================================
HP_COLOR = "#D94B4B"        # health - red
QI_COLOR = "#3B9FE8"        # qi / mana - blue
BODY_GREEN = "#79C85A"      # Body Transformation - green
ESSENCE_PURPLE = "#C77DFF"  # Essence Gathering - purple
INVENTORY_BLUE = "#51BDED"  # inventory / interactive text / location links

# Backwards-compatible accent aliases used by combat rendering.
ACCENT_GLOW = GOLD_BRIGHT     # highlights / emphasis
ACCENT_LINK = INVENTORY_BLUE  # interactive text / links (location & item names)
DRAGON_BLUE = QI_COLOR        # qi / info
PHOENIX_ORANGE = "#E6B24A"    # warnings / exp

# ============================================================
# BORDERS / SEPARATORS
# ============================================================
DIVIDER = "#241C10"           # low-contrast divider between sections

# ============================================================
# INTERACTION STATES
# ============================================================
STATE_HOVER = "#16202C"       # brighter panel on hover
STATE_ACTIVE = "#0E1620"      # pressed / active
STATE_SELECTED = GOLD_BRIGHT   # selected accent
STATE_DISABLED_BG = "#0A0F15" # disabled control background
STATE_DISABLED_FG = "#5A554C" # disabled control text
FOCUS_RING = GOLD_BRIGHT       # keyboard focus outline

# ============================================================
# SEMANTIC / STATUS
# ============================================================
SUCCESS = "#70D36B"           # success / healthy / safe
WARNING = "#E6B24A"           # caution
DANGER = "#E05A5A"            # danger / failure

HP_HIGH = SUCCESS             # HP bar (ratio) - healthy
HP_MED = WARNING              # HP bar (ratio) - caution
HP_LOW = HP_COLOR             # HP bar (ratio) - danger
EXP_COLOR = GOLD              # experience
PROGRESS_COLOR = BODY_GREEN   # cultivation Body "progress" bar
ESSENCE_COLOR = ESSENCE_PURPLE  # Essence progress bar

# ============================================================
# PALETTE MAP  (handy for iteration / serialization to CSS/JSON)
# ============================================================
PALETTE: Dict[str, str] = {
    "background": BACKGROUND,
    "panel": PANEL,
    "panel_raised": PANEL_RAISED,
    "panel_soft": PANEL_SOFT,
    "header": HEADER,
    "gold": GOLD,
    "gold_bright": GOLD_BRIGHT,
    "border": BORDER,
    "border_strong": BORDER_STRONG,
    "text_primary": TEXT_PRIMARY,
    "text_secondary": TEXT_SECONDARY,
    "text_muted": TEXT_MUTED,
    "text_on_accent": TEXT_ON_ACCENT,
    "hp": HP_COLOR,
    "qi": QI_COLOR,
    "body": BODY_GREEN,
    "essence": ESSENCE_PURPLE,
    "inventory_blue": INVENTORY_BLUE,
    "success": SUCCESS,
    "warning": WARNING,
    "danger": DANGER,
    "progress": PROGRESS_COLOR,
    "exp": EXP_COLOR,
}


def hex_to_rgb(value: str) -> Tuple[int, int, int]:
    """Convert a ``#RRGGBB`` string into an ``(r, g, b)`` tuple (0-255)."""
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def hp_color(ratio: float) -> str:
    """Return the HP bar colour for a fill ratio (0.0-1.0)."""
    if ratio > 0.5:
        return HP_HIGH
    if ratio > 0.2:
        return HP_MED
    return HP_LOW
