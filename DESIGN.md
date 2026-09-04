# DESIGN.md — Martial Path (Godot frontend)

<!-- impeccable:design-schema 1 -->

## Visual world: the Standing Door

The **category standard for xianxia, played straight at full commitment** —
chosen deliberately through a nine-card decision round and locked against the
craft bar of *Slay the Spire*, *Wo Long*, and *Tale of Immortal*. Dark
lacquer-ink ground, antique-gold double rules, parchment-toned text, ornate
framing on every container. No irony, no compromise: what a temple gate is to
a mountain sect, this interface is to a lifetime of cultivation — a threshold
you cross to find your deeds recorded.

**Mode: Operate.** The player completes a cultivation lifetime; scanability,
state legibility, and quiet luxury outrank expression. Brand lives in precise
details: double-rule frames, a single diamond sigil, letter-spaced small caps.

## Platform

Godot 4.7 desktop, 1920×1080 primary window, mouse + keyboard. All UI is
built in code (`MainController.gd`, `MainMenuController.gd`) against one
shared theme resource (`frontend-godot/ui/themes/martial_path_theme.tres`).

## Color (the lacquer-and-gold ramp)

| Token | Hex | Role |
|---|---|---|
| Ink ground | `#14100b` | Window/menu ground; warm near-black, never pure black |
| Panel | `#1c1712` | Card and panel fill |
| Panel soft | `#221c14` | Cards on panels (one step up) |
| Panel line / hairline | `#4b3d24` | Inner rules, quiet borders, disabled borders |
| Gold border | `#7a5f2c` | Resting element borders |
| Gold | `#c9a35c` | Primary accent, active tab, bar fills |
| Gold bright | `#e9c87f` | Hover, display headings, focus |
| Parchment | `#e7ddc9` | Primary text |
| Parchment dim | `#a08f74` | Secondary text, captions |
| Parchment ghost | `#877a63` | Tertiary/labels |
| HP red | `#b8433f` (dark `#4a2622`) | Health bars |
| Qi blue | `#4f7fa8` (dark `#2a3d4d`) | Qi bars, spirit stones |
| Danger | `#d24a43` | Errors, death, hostility |
| Success | `#7ea75a` | Gains, affordable, completed |

Rarity ramp (item names and card top-borders): common `#a08f74`, uncommon
`#7ea75a`, rare `#5b8fc9`, epic `#9b6adb`, legendary `#e9a23f`.

Rules: gold is spent on structure and state, never as a flood; red only for
harm and death; the ground is always warm. Contrast floor: body text ≥ 7:1,
captions ≥ 4.5:1 against their fill.

## Type

- **Cinzel** (display): inscribed-capital character for titles, section
  heads, the brand. Always letter-spaced, always gold, 22–44px.
- **Alegreya Sans** (text): 15px default; Regular body, Medium emphasis,
  Bold rare. 13px captions, 11px micro-labels above values.
- System monospace only for quantities inside tables, never for prose.

Both families are OFL; full attribution + license text in
`frontend-godot/ui/fonts/OFL.txt`. Do not add a font without adding its
license file beside it.

## Form grammar

- **Frames:** outer 3px gold border with 1px inner hairline (`#4b3d24`) —
  the double rule — on primary containers (menu door, dialogs). Panels use
  single 1px `#7a5f2c` borders. Corner radius is 0 everywhere; crisp
  architecture, not rounded moderne.
- **Depth:** shadow only on floating layers (dialogs, popups): 28–36px black
  at 55–60% opacity, offset y 8–12.
- **Sigil:** a single `◆` between two 120px gold hairlines — used once per
  surface, above the brand block.
- **Section heads:** 13px gold small-caps between hairlines.
- **Buttons:** resting `#221d12` fill + `#5c4a2a` border; hover lifts fill
  and brightens border to gold; primary actions invert to solid gold with
  dark text (`#241b0d`) at 48px height.
- **Bars:** HP/Qi/progress use dark tinted wells (`COLOR_*_DARK`) with a
  1px `#4b3d24` border and saturated fill; text sits to the right, never
  over the fill.

## Layout grammar

- **Dashboard (Main.tscn):** 86px top bar (brand · HP · Qi · year · season ·
  tab strip · settings · world) over a three-column body — left character
  dossier (22%), center location + actions (56%), right narrative/log (22%).
  12px gutters, panels breathe with 16px inner padding.
- **Tabs:** five spreads (Inventory, Equipment, Journal, Status, Techniques)
  live in one modal overlay: dim 62% black, 76%×88% panel, double-rule
  frame. The overlay carries **its own tab strip in its header** — the
  top-bar buttons sit behind the dim layer and cannot switch tabs while it
  is open. Never remove the in-overlay strip again; that was a verified
  defect once.
- **Each tab answers one question:**
  - *Inventory — "What do I carry and what can I do with it?"* Rarity-edged
    item cards in a 3-column grid, qty/type/desc/modifiers, footer with
    currencies and capacity.
  - *Equipment — "What am I wearing and what does it give me?"* Paper-doll
    slot grid + aggregated bonus tally above it.
  - *Journal — "What is my life's story?"* Quest cards with progress bars
    (current/required from the engine), completed entries dimmed.
  - *Status — "What am I, exactly?"* Two-column character sheet: left
    identity/cultivation/lifespan, right talents/relationships/morality.
  - *Techniques — "What have I mastered?"* Skill cards grouped by category
    with live cooldowns.
- **Dialogs** (`_open_dialog`): titled, hairline rule, centered content,
  explicit close. Destructive or commit actions sit visually isolated on the
  right or below a rule.
- **Menu (MainMenu.tscn):** the Standing Door — one 520px framed panel,
  grain texture (`assets/ink_grain.png` at 55% alpha) over ink ground, brand
  block with sigil, origin select, chronicle ledger (numbered past lives),
  gold NEW GAME, paired CONTINUE/LOAD, footer text links. Legacy unlocks
  open as a proper dialog with AWAKEN/OWNED/SEALED states.

## Motion

Restrained by design: hover states shift fill/border within one frame —
Godot theme transitions are instant by default and that crispness *is* the
character. Permitted: bar fills animate, overlay appears immediately (no
fade that delays interaction). No bounce, no slide-in.

## Voice

Quiet formality, second person, no exclamation marks. Buttons are verbs or
single nouns ("Train Body", "Ascend"); captions are 11px small-caps
("SPIRIT STONES"); errors name the obstacle and the condition ("Your
cultivation has not yet reached the required threshold. Current 40 / 60").
Numbers are exact; the engine is the only source of truth.

## Craft floor (project-specific absolutes)

- No wall-of-text RichTextLabel as a "tab" — every tab is a structured spread.
- Every actionable card states why it is locked when disabled.
- Empty states are written ("The ledger awaits its first entry."), never blank.
- Gameplay logic never enters the client; the backend is the sole authority.
- New view-model fields go through `game/api/server.py` responses, never
  recomputed client-side from other fields.
- Any new font ships with its OFL.txt entry; any new color joins this file
  and the theme resource, not inline literals in controllers (the event
  renderers' legacy `#RRGGBB` bbcode constants are grandfathered).

## Verification loop (how this world is maintained)

Headless parse gate:
`Godot --headless --path frontend-godot --check-only -s res://scripts/<file>.gd`
then godot-ai MCP live run: `project_run` → `game_manage get_ui_elements` →
`input_mouse` (button is the string `"left"`) → `editor_screenshot
source="game"`. Bounded rounds: one inspect, one batch fix, one confirm.
