# Martial Path — Master GUI Improvement Prompt (Final)

**Use this prompt with your Coding AI (Cursor, Claude, Godot assistants, etc.)**

---

## Role

You are the lead UI/UX designer and frontend/game UI engineer for **Martial Path**, a cultivation-themed RPG built in Godot.

You are improving an existing playable game. Your job is to **polish and restructure the GUI** according to the layout and design rules below, while preserving all existing game functionality and mechanics.

Do **not** rewrite working gameplay systems, invent new mechanics, or remove existing features unless a small supporting change is genuinely required for the UI.

---

## Core Objective

Transform the current functional but dense interface into a clean, immersive, and professional cultivation RPG UI that feels like a finished indie game.

The player should immediately understand:
- Where they are
- Who they are
- What they can do
- What just happened
- What they can unlock next

The interface must feel like a real game rather than a developer dashboard.

---

## New Layout Structure (Critical)

### Default Main View (World / Exploration)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LOGO          YEAR 0                    HP ████  Qi ████     [Tabs]  ⚙   │
├──────────────┬──────────────────────────────────────────────┬───────────────┤
│              │                                              │               │
│  CHARACTER   │              LOCATION + ACTIONS              │  EVENT LOG    │
│              │                                              │               │
│  Portrait    │  Large location artwork                      │  Scrollable   │
│  Name/Path   │  Description                                 │  history      │
│  Age/Realm   │  Danger / Qi Density / Resources / Exits     │  with         │
│  Vitals      │                                              │  rewards      │
│  Body        │  ACTIONS (grouped, informative)              │               │
│  Essence     │                                              │               │
│  Combat      │                                              │               │
│              │                                              │               │
└──────────────┴──────────────────────────────────────────────┴───────────────┘
```

### Key Layout Rules

1. **Top Bar**
   - Left: Game logo / title
   - Center-left: **Year only** (Season and Day are low priority — minimize or remove)
   - Center-right: HP and Qi bars (clean and prominent)
   - Right: Horizontal tab buttons (Inventory, Equipment, Journal, Status, Techniques)
   - Far right: Settings

2. **Left Panel** → Character (always visible)
   - Portrait, identity, vitals, body progress (integrated), essence, combat stats
   - Clear visual hierarchy and sectioning

3. **Center** → Location + Actions (main focus)
   - Large atmospheric location image
   - Description + icon chips for Danger, Qi Density, Resources, Exits
   - Actions presented in clear groups with useful info (time cost, strain, requirements, locked state)

4. **Right Panel** → **Event Log** (permanent)
   - This is the new home of the Event Log
   - Show recent activity with timestamps and rewards
   - Scrollable, with a Clear Log button
   - Avoid large empty space on first launch (seed with a starting entry if needed)

5. **Tabs open as Floating Overlays**
   - Clicking Inventory / Equipment / Journal / Status / Techniques does **not** replace the main screen
   - A floating panel/modal opens over the center or center-right area
   - The main world view remains partially visible underneath
   - Floating panel has a clear close (X) button
   - Player can still see their character and location context while managing inventory, techniques, etc.

---

## Design Direction

**Aesthetic**: Dark cultivation fantasy + refined RPG interface + subtle Daoist influence.

- Charcoal / deep blue-black panels
- Warm gold for accents, headings, and primary actions
- Jade/green for body and positive growth
- Crimson for HP and danger
- Cyan/blue for Qi
- Purple for locked / advanced systems
- Warm off-white for primary text, muted grey for secondary

**Avoid**:
- Generic Chinese-themed website look
- Excessive dragons, red/gold overload, or decorative characters without purpose
- Anime clichés
- Overly ornate fantasy UI or constant glowing particles

The interface should feel sophisticated and restrained.

### Typography Hierarchy
1. Game title / major location
2. Section headings
3. Stat categories
4. Primary values
5. Descriptions / helper text
6. Muted metadata

The player should be able to understand the screen by scanning it for approximately two seconds.

---

## Specific High-Priority Improvements

### 1. Character Panel
- Strong visual hierarchy with clear sections: Vitals → Body → Essence → Combat
- **Body Progress bar must be integrated** into the Body section (remove any duplicate progress display)
- Locked systems show clear requirements
- Group stats logically and add tooltips for key terms (Foundation, Strain, Stability, Comprehension, etc.)

### 2. Location Panel
- Keep the strong atmospheric image and flavor text
- Convert Danger / Qi Density / Resources / Exits into **icon + value chips**
- Make exits feel interactive (buttons or clearly clickable)

### 3. Actions
- Group related actions (Cultivation, Exploration, Support, etc.)
- Primary actions (Train Body, Explore, Rest, etc.) should stand out visually
- Locked actions must show a clear reason + padlock icon
- Show useful info where the game already supports it (time, strain, requirements)
- Do **not** invent new values or mechanics

### 4. Event Log (now on the right)
- Make it useful and readable
- Show recent entries with day/time and important results
- Seed with a starting entry on first launch if currently empty

### 5. Floating Tab Panels
- **Inventory**: Clean grid + item detail card when selected
- **Equipment**: Clear equipment slots
- **Journal**: Immersive record of the player’s journey
- **Status**: Organized character overview
- **Techniques**: Progression-focused presentation
- All floating panels must feel consistent with the overall design language

### 6. Top Bar
- Year is sufficient (Season/Day can be removed or made very secondary)
- HP and Qi bars should be clean and easy to read
- Tab buttons need clear active / hover / focus states

### 7. Additional Polish
- Elevate Gold and Spirit Stones to a more visible position
- Clarify or resolve the overlap between “View Detailed Status” button and the Status tab
- Add subtle micro-interactions (hover, press, smooth progress transitions)
- Respect `prefers-reduced-motion`

---

## Constraints (Strict)

- Stay within Godot’s UI system (Control nodes, themes, styles)
- Do **not** break existing functionality or data binding
- Do **not** invent fake items, stats, techniques, locations, or mechanics
- Do **not** change gameplay values or progression requirements
- Prefer incremental, readable changes over a complete rewrite
- Preserve the dark cultivation aesthetic

---

## Implementation Process

**Stage 1 — Audit**  
Inspect the current project structure, UI scenes, scripts, themes, and data binding. Do not modify anything yet.

**Stage 2 — Layout Restructure**  
Implement the new overall structure: Top bar with tabs, Event Log on the right, floating overlay panels.

**Stage 3 — High-Priority Fixes**  
Integrate Body Progress, improve locked states, group character stats, improve action presentation.

**Stage 4 — Visual System & Polish**  
Apply consistent colours, typography, spacing, and component styling. Style floating panels.

**Stage 5 — Interaction & QA**  
Add tooltips, micro-interactions, and verify every existing action and system still works.

---

## Deliverables

When finished, provide:

1. Updated GUI implementation
2. Any new or updated theme/style resources
3. Minimal necessary script changes
4. A concise summary of structural and visual changes
5. Confirmation that all existing actions and systems still work
6. List of any assumptions made

---

## Final Instruction

Start by inspecting the existing project and understanding how the current GUI is built.

Then implement the new layout and improvements progressively.

The final result should feel like a polished cultivation RPG while remaining clearly the same Martial Path game.

**Do not change core game mechanics unless explicitly required to support the new UI structure.**
