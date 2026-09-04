# Martial Path — Handover

A data-driven cultivation (xianxia) RPG. The authoritative game logic is a Python
engine in `game/`; several frontends render its state and send commands. **All
gameplay rules live in the engine — never in a UI.**

Last updated: 2026-09-04. Test suite: **722 passing, 3 skipped** (`pytest -q`).
Data validation: clean (**0 errors**).

---

## 1. Running the game

Use the project virtual environment at `.venv`.

| Frontend | Command | Notes |
|---|---|---|
| **Godot client** (primary) | See below | Talks to the FastAPI backend over HTTP |
| FastAPI backend | `& ".venv\Scripts\python.exe" -m uvicorn game.api.server:app --host 127.0.0.1 --port 8001` | Required for Godot |
| CLI | `& ".venv\Scripts\python.exe" main.py` | Text frontend (frozen — see Conventions) |
| PySide6 desktop GUI | `& ".venv\Scripts\python.exe" gui_main.py` | Dark-fantasy dashboard (frozen — see Conventions) |
| Tests | `& ".venv\Scripts\python.exe" -m pytest -q` | 414 tests |
| Data validation | `& ".venv\Scripts\python.exe" -c "from game.validation import validate_all_game_data as v; print(v().is_valid)"` | Cross-reference check |

### Godot (Godot 4.7)
1. Start the FastAPI backend (command above). Keep it running.
2. Open `frontend-godot/project.godot` in the Godot editor and press **F5**.
3. The client connects to `http://127.0.0.1:8001` (`ApiClient.gd` `BASE_URL`). Port 8000 is reserved for the godot-ai MCP helper.

**Gotcha:** the backend runs **without** `--reload`, so after changing Python
engine code **or `game/data/**`** you must restart uvicorn for the Godot/HTTP
client to see it. GDScript changes require re-running the Godot project (F5).

**GDScript gotcha (grey screen):** the Godot project treats warnings as errors.
A `:=` that infers `Variant` — e.g. from the global `clamp()` / `min()` / `max()`
— is a hard **parse error** that fails the whole script, so `Main.tscn` renders
grey. Use the typed variants (`clampf` / `minf` / `maxf`) or an explicit `: float`.
Check Godot's **Output** panel for the offending line.

**GUI note (2026-09-04):** the Godot UI was fully redesigned (the "Standing
Door" canon — see `DESIGN.md` for tokens, layout grammar, and rules).
`MainController.gd` and `MainMenuController.gd` were rewritten; the five tabs
are structured card spreads in one modal overlay that carries **its own tab
strip** (the dim layer blocks the top-bar tab buttons). New fonts live in
`ui/fonts/` with `OFL.txt`; the grain texture is `assets/ink_grain.png`.
Quick parse gate after GDScript edits:
`Godot --headless --path frontend-godot --check-only -s res://scripts/<file>.gd`.

---

## 2. Architecture

Layered, one-directional dependencies:

```
ui/ (+ frontends)  ->  application/  ->  core/  ->  services/  ->  systems/  ->  models/ + data/
```

- `game/core/game_engine.py` — the single owner of mutable session state; wires
  systems, dispatches actions, builds the UI-agnostic `get_game_state()` snapshot.
- `game/systems/` — pure gameplay rules (no I/O, no UI). Return structured dicts
  tagged with an `EventType`.
- `game/services/` — thin coordination facades over systems.
- `game/data/registry.py` — loads every content collection once into an immutable
  `GameDataRegistry`.
- `game/validation/data_validator.py` — central cross-reference validation.
- `game/core/results.py` / `constants.py` — typed result dataclasses + `Action` /
  `EventType` StrEnums (the UI contract).

---

## 2.5 Recent work (2026-09-02, ROADMAP Phase 2: A.6 + B.6)

> 2026-09-04 fix: the HTTP `ActionRequest` model was silently dropping
> `track`/`target_id` (and 9 more dispatch fields), so Godot's Talents upgrade
> always errored; `USE_ITEM` on effect-less materials (Talent Refining Elixir)
> now returns `ITEM_NOT_USABLE` instead of a no-op success. See CHANGELOG.

### Full campaign + post-game (2026-09-04, ROADMAP Phase 2 D.3–D.5)
- **Acts 2–3** (`quests.json`): the campaign continues past Act One — join-sect
  beat → Schism War (seven duels) → Act-2 dao rekindling (the one-time dao gate
  is now per-window, so the story beat genuinely reopens the choice) → realm war
  against the `ancient_devil_manifestation` → Planar Gate sentinel → final
  breakthrough beat (the ascension choice, not another boss re-fight).
- **Three endings** (`game/core/engine/campaign.py`): completing the final act
  (`act_end: "act_three"`) wins the campaign and banks a 150 Ancestral Memory
  bonus; the ending is chosen from morality — `realm_martyr` (≥ +30),
  `demon_sovereign` (≤ −30), `ascended_sword` (between) — and recorded as
  `campaign_ending` in every future chronicle entry for the run.
- **Faction chains (D.4)**: `phoenix` and `valleys` chains, gated by sect path
  (`requires.path_any`) and branched by morality (`min_morality`/`max_morality`
  gates; quest rewards may shift `player.morality`). New quest objectives wired
  to real actions: `spar` (spars count from combat-end), `debate` (won debates),
  `realm_completed` (surviving a secret realm).
- **Endless road (D.5)**: `ENDLESS_REALM` opens `SecretRealmSystem.generate_endless`
  realms — procedural rooms mixing mook and named foes, stats ×1.15/depth and
  rewards ×1.25/depth, deterministic per (seed, depth). First descent lifts the
  essence cap (`beyond_divinity` unlocks), so post-game play can pass Beyond
  Divinity. Depth rewards accrue per realm; gated behind campaign completion or
  an endless run (API `endless` new-game flag; flags persist in saves).
- **Godot**: "Endless Road" card, endless depth/cap-lift lines, campaign-ending
  banner, act-name banners. Also restored the B.7/E render call sites
  (`DEBATE_STARTED`/`DEBATE_END`/`WORLD_INFO`, world-tick lines, rumor reveals)
  that the recent UI rewrite had orphaned.
- Tests: `tests/test_campaign.py` (29 tests). Suite green apart from the other
  tab's in-flight character/enemy additions.

### Phase F wave 2 (2026-09-04)
- **7 new tier 5-6 techniques** (208 → 215): Everburning Forge Body + Pillar
  of the Sun (Furnace Forge Society), Blood Ledger Aura + Ashen Verdict
  (Emberfall War Pavilion), Rune Circuit Body + Five Element World Seal + Gate
  Star-Severing Step (Rune Temple Order). Skill reachability now counts sect
  halls as an acquisition path (`test_all_skills_reachable.py`), so hall-only
  techniques are legal.
- **3 endgame secret realms** (6 → 9): Coral Drowned Panopticon (atoll),
  Undercroft Circuit Prime (undercroft), Starfield Stair Sanctum (gate
  approach) — 8-9 rooms each with named-foe bosses and endgame final rewards.
- **28 new NPCs** (62 → 90) anchored across all new zones with full schema,
  `min_story_tier` tags, and 8 new named-foe combat entries (27 → 35).
- **27 new quests** (35 → 62; §6 target met): zone chains for every expansion
  region (wharf/thornline/outskirts/peaks/market/terrace/pack, five sea
  chains, forge/citadel chains, zen wilds chain, undercroft/gate chain) plus
  character quests (poet's verse, ruin provenance run).
- Generator: `tools/expand_phase_f_wave2.py` (additive-safe, re-runnable).

### Phase F breadth expansion (2026-09-04, ROADMAP F.2 + F.3)
- **16 new locations** (29 → 45) across story tiers 2–6: a river wharf and
  deepwood hunting grounds in the starting wilds, a capital farmland ring, a
  wilderness outpost hub, sect trial peaks, a hidden canyon market, a cloud
  terrace village, sea content (pearl pavilion, pirate cove, sunken prison
  atoll, open-sea expanse), and endgame zones (forge pillar city, Asura war
  citadel, zen wilds shrine, rune temple undercroft, gate array approach).
  All bidirectionally wired, pooled, and map-positioned.
- **8 new sects** (4 → 12) spanning tiers 1–6: Mistwood Rangers, Stream Cloud
  Pavilion, Valleys Gamblers' Market, Deepwood Drift Hall, Pearl Tide
  Pavilion, Furnace Forge Society, Emberfall War Pavilion, Rune Temple Order
  — each with a technique hall referencing existing skills.
- **12 new NPCs** (`characters/expansion_roster.json`, 50 → 62) with full
  personality schema, `min_story_tier` tags, and named-foe combat entries in
  `character_enemies/named_foes.json` (21 → 27).
- **16 new encounter pools** wired to previously-unused enemies (dead-content
  pass), **2 shops + 2 trainers** for the new hubs.
- **3 faction quest arcs** (F.3): Seven Profound Valleys (`spv_*`), Divine
  Phoenix (`dpa_*`), Asura War Pavilion (`asura_*`) — three chained quests
  each, gated on `act1_conclusion`, with skill rewards and NPC quest-givers.
- Content generator: `tools/expand_phase_f.py` (idempotent, refuses to
  overwrite). Guard tests: `tests/test_content_breadth.py`.

### Codex + economy balance (2026-09-04)
- **CODEX action** (no turn cost): returns the wanderer's codex — every
  secret realm (with `story_tier` and `discovered` flags), every sect with
  its tier and hall progress (`technique_count`/`techniques_known`/`joined`),
  and every faction quest arc (quest `chain` groups: asura, phoenix,
  valleys) with live status. Wired through `dispatch` → `views._codex`
  (`SectSystem.codex_summary` + `SecretRealmSystem.definitions()`);
  `QuestSystem.snapshot()` now carries each quest's `chain`. The Godot
  client renders it as a Codex action card + three-section popup.
- **Economy ledger** (`game/utils/economy_balance.py`, CLI
  `tools/economy_report.py`): derives spirit-stone income (exploration loot,
  combat drops, quest rewards, secret-realm treasure) from the live data
  files and compares it to the tier 5-6 hall prices. Verdict criteria: the
  priciest technique ≤ 25% of run income, costliest single hall ≤ 90% (a run
  joins one sect). Held by `tests/test_economy_balance.py`.
- **Economy tuning** (`tools/economy_tune.py`, one-shot + idempotent):
  endgame foes gained stone drops scaled to the existing curve, endgame
  zone quests and the three wave-2 secret realms gained stone rewards, and
  the tier-6 rune hall was re-priced onto one 130-180 ladder. Result:
  ~1175 reachable stones vs costliest hall 930 (was 362 vs 1110).

### Sect story tiers (2026-09-04)
- **Sect tiers 1–6** (`sects.json`): every sect carries a `tier` (roughly where
  it sits along the story) plus a per-sect `techniques` hall — each entry is a
  skill id with a `price` and optional `required_path`. Higher tiers teach
  stronger arts.
- **Story progression tracking**: locations carry a `story_tier` (1–6);
  `GameEngine._note_arrival` raises `player.max_story_tier` on every arrival
  (new game, travel, exploration moves, save load) and the value persists in
  saves. Locations/sects surface their tier in views.
- **Tier gates**: joining a sect with `min_story_tier` above the player's
  reached tier returns `STORY_TIER_TOO_LOW`; techniques can be bought from a
  joined sect's hall via `LEARN_SKILL` with `sect_id` (routes through
  `SectSystem.learn`: membership → tier reach → price), mirroring trainer rules.
- **Tier-aware encounters**: characters may carry `min_story_tier`;
  `CharacterService.meet_characters_at` filters them so late-game figures
  only appear once the story has advanced that far.
- **Godot**: new SECTS action card + sect view listing the technique hall with
  prices and a buy button; joined sect and story tier shown.
- Validator: checks sect `tier` ranges, technique ids/prices, location
  `story_tier` levels, and character `min_story_tier` ranges.
- Tests: `tests/test_story_tiers.py` (unit), `tests/test_sect_tiers_engine.py`
  (engine loop), `tests/test_sect_system.py` updated for the new constructor.
  The earlier "2 failing sect tests from another tab" note is resolved — suite
  is fully green.

### A.6 — Voice consistency (prose quality gates)
- **Voice guide** at `game/docs/VOICE_GUIDE.md`: tone rules, sentence-shape
  guidance, and the banned-gamey-terms list ("level up", "quest log", "HP"...).
- **Lore glossary** at `game/data/lore_glossary.json`: canonical terms seeded
  from *actual* display labels (realms, daos, tiers, seasons, morality ids),
  with per-slot vocabulary for narrative slots (`realm`, `dao`, `tier`,
  `season`, `morality`). Registered in `GameDataRegistry` and validated.
- **Four new linter checks** in `game/validation/narrative_lint.py` (also run
  by `tools/narrative_lint.py` and `validate_all_game_data`): gamey-term
  blocklist, `{`/`}` brace artifacts, ≥2 weighted variants per verb, and
  glossary conformance of template literals per slot.
- **Sameness metric** (`tests/test_narrative_voice.py`): drives a 100-event
  mixed-action run through the narrative system and asserts repeated verbs
  produce distinct variants — the roadmap's anti-Mad-Libs floor.

### B.6 — Stances + combos (technique chains)
- Techniques may carry `combo_role` (`opening`/`response`/`finisher`); 3 chains
  seeded on 9 skills in `game/data/skills.json` (validator enforces the role
  vocabulary and one role per skill).
- `CombatSystem` tracks a banked chain: a chained sequence grants **+25% damage
  per banked stage** (1.25x/1.5x/1.75x) into the next technique. A banked chain
  flows into *any* damaging technique; neutral techniques neither advance nor
  break it; a correct-role chain skill advances and consumes the bank.
- Engine gating (`game/core/engine/combat.py`): using a chain skill out of
  sequence is refused **without** wasting qi; the chain drops cleanly when
  combat ends and on wrong use.
- Surfaced to UI: `combo_stage`/`expected_combo_role` on the player/status
  views and `combo_role`/`expected_combo_role`/`combo_ready` on technique
  briefs (`views.py`). Chain state is transient — reset each fight, like
  insight; a refused out-of-sequence stance leaves the banked chain intact.
- Tests: `tests/test_combo_combat.py` (17 tests) cover banking, multipliers,
  neutral-skill pass-through, wrong-role refusal + qi refund, cleanup, and
  save round-trip.

---

## 3. Recent work (2026-08-14, the GROK-review close-out)

This session executed the full **17-priority roadmap** derived from a code review
(measurable criteria were tracked in the since-removed `Tasks.md`; the live plan is `ROADMAP.md`). Summary by theme:

### Meta depth (Phase 2 C — legacy tree, world seed, ascension)
- **Legacy unlock tree (C.5)**: `data/legacy_tree.json` (3 tiers) + pure
  `LegacySystem`. `UNLOCK_TREE` views the tree; `UNLOCK <id>` spends Ancestral
  Memory cross-run. Purchases persist in the meta-save (`unlocks[]`), teach
  their technique on every new character (`source="legacy"`), free-join nothing
  (sect gates stay), and surface as `player.title`. The validator checks ids,
  kinds, targets (sects/skills), positive costs, and tier reachability.
- **World seed (C.6)**: the run seed derives a deterministic world report
  (`engine._world`): two dominant sects (listed first, `-5` reputation subsidy
  on the join gate), an economy band (cheap 0.9 / fair 1.0 / pricey 1.15)
  scaling every shop price (displayed price == charged price), and an encounter
  bias consumed by `EventSystem`. Same seed replays identically; different
  seeds differ measurably (test-pinned).
- **Retirement/ascension (C.7)**: `RETIRE_ASSENT` (also `POST /retire`) at
  essence order >= `ASCENSION_ESSENCE_ORDER` (6, Divine Transformation) ends
  the run as a *win*: banks the death reward x `ASCENSION_REWARD_MULTIPLIER`
  (3), records an `ascended` chronicle entry, and sets a persisted `retired`
  meta flag. The `endless` session flag round-trips through saves. Godot: a
  Legacy card + unlock popup in-game, a Legacy Tree button on the main menu,
  an Ascend card (locked until the threshold), and RETIRED/UNLOCK_PURCHASED
  event rendering.
- Tests: `tests/test_meta_depth.py` (17 tests). Shop-price engine tests now
  read the displayed price instead of pinning a literal.

### Dao combat full (Phase 2 B — debates, spirit-oath duels, foe AI)
- **Dao debates (B.7)**: pure `DebateSystem` — a non-lethal contest of
  conviction fought with stances: `assert` > probe/yield, `probe` > transcend
  (exposing it, pinning the next absorb), `transcend` > assert, `yield` halves
  incoming pressure. Sway = insight scaled by stance, multiplied by the dao
  matchup. `MODE_DEBATE` routes `DEBATE_STANCE`/`YIELD_DEBATE`/`WALK_AWAY`;
  `DEBATE_CHARACTER`/`OATH_DUEL_CHARACTER` open against any spar-capable
  character (their foe template debates with its dao). Insight is borrowed for
  conviction and restored after — the combat pool is untouched.
- **Spirit-oath duels (B.7)**: asymmetric stakes sworn up front — win banks
  1.5x the wagered gold/exp, loss costs half banked exp + the wager, walking
  away mid-oath is a **breach** (forfeits the larger of the wager or half
  current gold), stalemate releases both parties.
- **Foe AI (B.8)**: pure `FoeAI` consulted each enemy phase. Dao-carrying foes
  fight stance chains (opening -> response -> finisher) with the same
  +25%/stage bank the player enjoys, press harder when their dao counters the
  player's (x1.5) and softer when countered (x0.6), grow desperate when
  wounded, and **guard** against a banked player chain (+50% defense, and the
  respected flow banks into their next press as momentum). Mooks (dao-less)
  keep the plain ability/attack pipeline, so existing encounters are unchanged
  unless data opts in. `named_foes.json` bosses/elite duelists now carry real
  chain techniques (`true_dragon_*`, `white_tiger_*`, `glacial_*`).
- Godot: debate conviction bars, oath notices, and stake outcomes in the log;
  Debate/Oath Duel cards appear automatically on encounter options.
-  Tests: `tests/test_dao_debate.py` (13) + `tests/test_foe_ai.py` (14).

### Living world simulation (Phase 2 E — NPC agency, sects, economy, seasons, rumors)
- **WorldSimulationSystem** (`game/systems/world_simulation.py`, pure): one
  seeded world of all named NPCs evolves on the player's calendar. The engine
  ticks it from every time-consuming action (train/rest/meditate/travel/
  closed-door) via `game/core/engine/world.py` (`WorldMixin`), on a dedicated
  RNG stream (`seed ^ 0x57A7E5`) so main-sequence determinism is untouched.
- **E.1 NPC agency**: NPCs cultivate (odds slow with realm, hard rank cap 12),
  the two strongest clash, elders (rank >= 8) die on the road; the dead stop
  progressing. All state lives in `engine._world_state` and saves round-trip it.
- **E.2 Sect sim**: sect power is recomputed from living members' ranks each
  step and smoothed toward it; sects with no living members decay to the base.
  A 100-year sim reorders the sects without emptying the world.
- **E.3 Economy**: wealth-per-cultivator (supply) and death-scarcity (demand)
  nudge a bounded (0.7–1.4) `price_multiplier`; `ShopSystem.set_market_multiplier`
  layers it on the C.6 seed band so displayed == charged prices.
- **E.4 Seasons act**: `SEASON_MODIFIERS` — Autumn x2 gather yield, Winter x0.5
  yield / x1.5 travel / x0.8 combat odds / x0.7 NPC progress; Summer/Autumn x1.1/
  x1.2 combat odds (`EventSystem.set_combat_bias`). Travel now consumes seasonal
  years (`engine/_advance_travel_time`); gather bonus herbs arrive as
  `season_bonus` on GATHER results.
- **E.5 Rumors**: notable tick material (deaths, market moves, sect shifts)
  mints bounded-lifetime rumors (fade after 6 years, learned persist, list cap
  20). `WORLD_INFO` / `WORLD_RUMORS` / `LEARN_RUMOR` are engine actions; talking
  to any character may surface an unlearned rumor (`rumor_learned` on the talk
  result) whose reveal carries a display name. `get_game_state()` now includes a
  compact `world` view (year, season, sect leader, price multiplier, rumors).
- Godot: Season chip + World button in the top bar, world-tick lines appended
  after time-consuming actions, rumor reveals appended to conversations, and a
  full "The Living World" report (sects, market, rumors) for WORLD_INFO.
- Tests: `tests/test_world_simulation.py` (26 tests). Suite: 605 passed, 3
  skipped; `validate_all_game_data()` clean.

### Combat & skills
- **All 26 skill effect types now do something.** `CombatSystem` resolves
  `damage`, `true_damage`, `aoe_damage`, `execute`, `life_steal`, `heal_self`,
  `stun`, `dot_damage`, `shield`, `counter`, `debuff_attack`, `debuff_defense`
  plus a shield/status model; `StatsSystem` honours the full passive set
  (`buff_*`, `crit_*`, regen, `qi_cost_reduction`). Meta-passives
  (`comprehension_gain`, `lifespan`, `cultivation_speed`) are wired into
  learn/lifespan/cultivation.
- **Spar vs duel are distinct.** Spars end at 25% HP with no loot/exp/penalty;
  duels/exploration keep full stakes.
- **Defeat penalty is data-driven** (`cultivation_config.defeat_penalty`): 25%
  body-progress loss + revive ratios, not a wipe.
- **Enemy abilities** (`heavy`/`poison`/`stun` with chance+magnitude) on 4 named
  foes; enemy stun forfeits the player's turn.

### Martial growth economy
- Every skill has an auto-generated manual; `tools/seed_techniques.py` seeds them
  into enemy loot, shops, and encounter pools — **0 unreachable skills** (was 205).
- `trainers.json` (8 trainers) teaches all 208 skills; 4 path-locked secret arts.
- **Talent upgrades** (`talents` / `upgrade <track> <target>`) chain every talent
  into the next grade, gated by the rare **`talent_refining_elixir`** (not gold).
  The elixir is reachable through encounters (high-danger pools + enemy drops),
  Masters (relationship reward), and late-game shops.

### Social & faction
- **Dialogue choices** (`dialogue.choices[]`) mutate relationship/morality/
  reputation; `TALK_TO_CHARACTER` returns available choices.
- **Relationship-gated rewards** (`relationship_rewards`) are claimable one-time
  boons via `RECEIVE_BOON`, tracked in NPC memory flags.
- **Sects** (`sects.json`, 12 sects, tiers 1–6): `JOIN_SECT` sets `player.path`;
  joining gates on realm + reputation + story tier, and each sect's technique
  hall is purchasable via `LEARN_SKILL` with `sect_id`.

### World & progression
- **Quest chains**: 3 → 9 quests with `requires` gates (completed quests,
  reputation, location) and skill/manual rewards.
- **Economy**: `SELL_ITEM`, 3 → 12 shops, spirit-stone sinks.
- **Time model**: `closed_door <years>` seclusion, seasons, realm-scaled aging.
- **Save/meta**: ironman flag, NG+ scaling bonus, portable `export`/`import`
  (cloud substitute).

### Phase 2 — narrative coverage (A.5 + A.7)
- Every `EventType` now narrates through a canonical `EVENT_VERB` map; the engine
  decorates every result with a `narrative` line, and `narrative_templates.json`
  grew to 64 verbs (every event has >= 1 template, core verbs >= 3).
- `tools/narrative_lint.py` lints templates (undeclared/unused slots, bad
  `when` clauses, core-verb floor, event coverage) and is wired into
  `validate_all_game_data()` via `game/validation/narrative_lint.py`.

### Combat exp -> comprehension -> cultivation speed
- Combat exp now means something: `CultivationSystem.convert_exp_to_comprehension`
  drains the `Player.exp` bank into comprehension at `EXP_PER_COMPREHENSION` (50)
  per point, and the engine's combat-victory path (`_end_combat`) runs it and
  surfaces `comprehension_gained`/`comprehension`. Quest/training exp feeds the
  same bank, so it converts on the next victory.
- Comprehension now speeds cultivation: `_cultivation_speed_multiplier` includes
  a `1 + (comprehension - 10) * 0.005` factor (+50% at 100 comprehension), so
  sharper insight grows both cultivation speed and (existing) breakthrough odds.

### Frontend (Godot only)
- Full GUI restructure per `Martial_Path_GUI_Master_Prompt_Final.md`: top bar
  (Year + tabs), 3-column body, floating tab overlays, monogram portrait,
  location chips + clickable exits, grouped actions, paper-doll equipment slot
  grid.
- The **event log was removed**; the right column is now a single **Narrative**
  panel (prose only). `_append` is a no-op kept for its call sites, and
  quest/act-completion lines are folded into the combat-end narrative.
- The Actions hub's cultivation section is **split vertically** into
  **Body Cultivation** (Train/Stabilise/Breakthrough) and **Essence Cultivation**
  (Gather/Stabilise/Breakthrough) grids.
- Item interaction consolidated into the **Inventory** overlay (Use/Equip/Unequip
  buttons); the main Actions hub's *Commerce & Support* grid keeps only Market +
  Masters.
- Combat actions are now built from the player's **known active techniques**
  (was a hardcoded Attack/Iron-Fist/Healing-Pill/Flee row), so newly learned
  skills appear as usable move buttons mid-battle. Missing skill-error reasons
  (`SKILL_ON_COOLDOWN`, `NOT_ENOUGH_INSIGHT`, `SKILL_NOT_KNOWN`,
  `SKILL_NOT_USABLE`) now translate to readable text.
- The **Techniques** tab groups techniques by classification — **Active**
  (combat techniques with Qi/cooldown/insight costs), **Stats** (always-on
  stat passives), **Growth** (permanent learn-time passives) — driven by a new
  `category` + `effect_label` on the engine's `get_known_skills()` view model.
- Added a **Talents** action (Support grid) + upgrade popup so the
  `talent_refining_elixir` can finally be spent: the engine's `TALENTS` view now
  annotates each upgrade option with `affordable`, and the popup lists Martial
  and Body upgrade paths with click-to-upgrade (`UPGRADE_TALENT`).

---

## 4. Key data files

| File | Purpose |
|---|---|
| `game/data/cultivation/martial_talents.json` / `body_talents.json` | Rollable Martial/Body talents (with `upgrade_options` chains) |
| `game/data/cultivation/talents.json` | 20-tier + Apex talent ladder |
| `game/data/cultivation/essence_gathering_realms.json` | Essence realms + per-realm `max_lifespan_years` |
| `game/data/cultivation/cultivation_config.json` | Training methods, strain/stability, `lifespan`, `defeat_penalty`, `closed_door`, realm aging |
| `game/data/locations.json` | 45 world-map locations (art + `map_position`) |
| `game/data/sects.json` | 12 sects (path, `tier` 1–6, join requirements incl. `min_story_tier`, contribution ranks, per-sect `techniques` hall) |
| `game/data/encounter_pools.json` | Location loot pools |
| `game/data/character_enemies/named_foes.json` | Named foes (abilities) |
| `game/data/equipment.json` | Equipment (realm-gated; some with `set_id` + durability) |
| `game/data/items.json` | Items incl. `talent_refining_elixir` |
| `game/data/shops.json` | 12 location-bound markets |
| `game/data/trainers.json` | Skill trainers (teach for currency; `required_path`) |
| `game/data/legacy_tree.json` | Cross-run unlock tree (C.5): 3 tiers of sect/technique/title unlocks bought with Ancestral Memory |
| `game/data/technique_manuals.json` | Optional per-skill manual overrides |
| `game/data/events.json` | Encounter weights, `character_encounter_chance`, `find_config` |
| `frontend-godot/assets/sky_spill_continent_map.png` | World map image |

Seed generators live in `tools/` (all deterministic + idempotent):
`seed_techniques.py`, `seed_shops.py`, `seed_talent_upgrades.py`,
`seed_talent_resources.py`, `seed_equipment_sets.py`, `seed_enemy_abilities.py`,
`normalize_available_systems.py`, `gen_missing_location_art.py`.

Docs: `game/docs/ARCHITECTURE.md`, `CULTIVATION_SYSTEM.md`, `DATA_SCHEMA.md`,
`SAVE_SYSTEM.md`, `EQUIPMENT_SYSTEM.md`, `CHANGELOG.md`. Roadmap: `ROADMAP.md`.

---

## 5. Testing & validation

- `pytest -q` — **722 passed, 3 skipped**. Newer files: `test_medium_priority.py`
  (the P10–P17 close-out), `test_sell_system.py`, `test_sect_system.py`,
  `test_relationship_rewards.py`, plus combat/trainer/find/lifespan/talent/shop,
  `test_codex.py` (CODEX action) and `test_economy_balance.py` (endgame
  reachability criteria).
- `validate_all_game_data()` — validates skills/effects, talents + upgrade chains
  + elixir costs, trainers (+ `required_path`), shops, sects, quests, equipment
  (rarity, realm, sets, durability), items, enemy abilities, encounter pools,
  normalized `available_systems`, and map-position duplicates. **0 errors.**
- Systems are testable without a UI (inject data + a seeded `RNG`).

---

## 6. Known follow-ups / open items

- **Deferred (needs an external service):** cloud save (local `export`/`import`
  ships instead) and a full LLM dialogue layer (`ai_prompt_notes` is surfaced as
  a `(manner: …)` line, but no generated dialogue).
- **Untested at runtime here:** PySide6 (`gui_main.py`) and the Godot paper-doll
  render — both compile/parse clean but weren't executed against a display.
- **New engine actions not yet surfaced as dedicated Godot widgets:** `talents`,
  `closed_door`, `repair`, `export`, `import` work through the API/state but have
  no bespoke Godot buttons/panels yet (Godot renders them via generic handling).
- **`BOON` narration gap in Godot:** the "Receive Reward" button appears from the
  backend `options`, but `MainController._render_event` has no `BOON` case, so the
  reward result isn't logged visually (it is granted by the backend).
- **Sect contribution ranks** exist as data but there is no contribution-earning
  mechanic yet (tasks, inner/outer disciple progression, sect store).
- **Subjective map placement:** the early Sky Fortune cluster is a best-fit (no
  reference coordinates); the objective guard (no duplicate markers) is enforced.
- **Backend `--reload`:** not enabled; restart uvicorn manually after engine edits.

---

## 7. Project conventions

- Data-driven first: JSON + stable snake_case IDs over hard-coded values.
- Keep gameplay logic out of UIs; UIs display state and send commands only.
- **Frontend scope: only the Godot interface (`frontend-godot/`) is updated.**
  Do NOT modify the CLI (`game/ui/cli_interface.py` + its
  `game/application/command_router.py` translator) or the PySide6 interface
  (`game/ui/gui_interface.py`). Engine/data/system changes are fine, but any
  player-facing UI work lands in Godot only.
- ASCII only inside player-facing printed strings (Windows console is cp1252).
- Update `ROADMAP.md` (flip checkboxes) / `handover.md` and the relevant
  `game/docs/` files alongside changes.

---

## 8. Next steps (proposed)

Priority-ordered ideas to progress the game further (none started):

1. **Sect contribution loop** — earn contribution via sect tasks / sparring,
   spend it at a sect store, promote inner/outer disciple ranks that unlock
   path-locked techniques and higher trainers.
2. **Alchemy / gathering loop** — make `gather` a real verb at herb-rich
   locations, then refine herbs (with the `talent_refining_elixir` as a template)
   into pills that feed cultivation and combat.
3. **Multi-enemy & boss-fight combat** — formations/positioning and phased boss
   encounters to break the 1v1 monotony; tie named foes to quests.
4. **Companion / relationship depth** — let bonded NPCs travel and fight with the
   player, and gate more content on relationship tiers.
5. **Sect tournament / arena ladder** — a recurring ranked sparring event as a
   mid-game loop and a reputation/contribution sink.
6. **Seasonal weather effects** — DONE in Phase 2 E (see §3): seasons now act
   on gathering, travel, encounter odds, and the world's own progress.
7. **Surface the new actions in Godot** — bespoke widgets for `talents`,
   `closed_door`, `repair`, `export`/`import`, and the `BOON` result narration.
8. **Cloud save + LLM dialogue** — once an external service is chosen, wire the
   two deferred items from §6.
