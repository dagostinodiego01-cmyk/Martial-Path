# Product

<!-- impeccable:product-schema 1 -->

## Platform

desktop-godot (Godot 4.7 desktop app, primary window 1920×1080; keyboard + mouse)

## Users

The player: a single-player xianxia cultivation RPG player at a desktop, in sessions of roughly 20–60 minutes, who wants the arc of a martial lifetime — train, explore, fight, die, reincarnate stronger — to be legible at a glance. Secondary user: the developer (Diego) iterating on the game with AI agents, who needs the UI to stay structured and reviewable.

## Product Purpose

Martial Path is a text-plus-art cultivation RPG. The player trains Body and Essence, explores a continent of locations, fights, refines items, joins sects, and dies of old age or combat — then reincarnates with meta-progression ("Ancestral Memory", unlock tree, origins). Success: the player always knows where they are, what they can do, and how far they've come.

## Positioning

The mechanic no neighbor can copy: a full lifetime arc (birth → cultivation → death → reincarnation → inherited advantage) where death is progress, not failure. The UI must make the *lifetime* visible, not just the current combat.

## Operating Context

Runs against a local Python FastAPI backend on 127.0.0.1:8001 (required; the Godot client renders engine state). All UI is built in code in `frontend-godot/scripts/MainController.gd` with a shared theme resource `frontend-godot/ui/themes/martial_path_theme.tres` — UI is code, not scenes. Location art lives in `frontend-godot/assets/locations/<location_id>.png`; world map at `frontend-godot/assets/sky_spill_continent_map.png`. Project rule: GUI changes target ONLY the Godot frontend; the backend may gain read-only view-model fields, never gameplay in the client. Live verification available via the godot-ai MCP server (run game, inject input, screenshot).

## Capabilities and Constraints

- Engine returns structured dicts (EventType-tagged); the client renders state/result payloads and sends `{"action": ...}` — no gameplay logic frontend-side.
- Five overlay tabs: Inventory, Equipment, Journal, Status, Techniques. Currently mostly text-dump RichTextLabels; the overhaul's core ask is giving each a purposeful, well-designed layout.
- Dashboard shell: top bar (name, HP/Qi bars, year/season, World button), left character panel, center location + action grids, narrative event log. Popups: Travel, World Map, Shop, Trainer, Sects, Refine, Equip/Use/Unequip, Settings, Credits, Legacy Tree. Plus MainMenu scene.
- Anti-duplication rule (binding): Gold only in Inventory; Body/Essence only in Character panel; HP/Qi only in top bar; full location text only in Location panel.
- `state.player.essence_unlocked` gates locked actions; unlock hint from `cultivation_state.essence_gathering.unlock_requirement`.
- Godot 4.7 gotchas (binding): short Labels AUTOWRAP_OFF; no multi-statement inline lambdas; connect signals to named methods; unique func names.

## Brand Commitments

Name: Martial Path. Genre voice: serious xianxia/wuxia — body cultivation, qi, dao, sects, reincarnation. Existing app icon (`frontend-godot/icon.png`) is a binding asset. Genre must stay xianxia; the visual world (palette, materials, typography) is explicitly open for replacement.

**Visual direction (user-chosen, binding):** the category standard played straight at full commitment — dark ink ground, gold accents, parchment panels, ornate borders — executed impeccably, conventions embraced without irony or smuggled quirk. Craft bar: Slay the Spire, Wo Long: Fallen Dynasty, Tale of Immortal — polished mainstream game UI a xianxia player already trusts. Direction round seed key: ee1c11cf (canon chosen).

## Evidence on Hand

- Location art: 29 PNGs in `frontend-godot/assets/locations/` (verified: ids match `game/data/locations.json` 1:1).
- Backend `/state` payload is rich: rarities, durabilities, item modifiers, quest progress, skill cooldowns, talent ladders, shops, trainers, sects — currently flattened into text walls by the UI.
- Live captures of the current UI exist (main menu + in-game) from the godot-ai session.

## Product Principles

1. The lifetime is the scoreboard — reincarnation progress (Ancestral Memory, unlock tree) must always be visible, never buried.
2. Every tab earns its opening — each overlay tab answers a specific player question at a glance (what do I own, what do I wear, what happened to me, who am I, what can I become).
3. One look, everywhere — dashboard, tabs, popups, and menu share one visual world.
4. Render, don't flatten — the engine's structured data deserves structure: scans, cards, bars, states — not text walls.
5. Rules stay in Python — presentation only in Godot.

## Accessibility & Inclusion

Desktop mouse+keyboard; no specific standard recorded. Text-heavy by nature: keep body text comfortably sized and high-contrast against its ground.
