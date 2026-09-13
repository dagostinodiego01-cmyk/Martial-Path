# TASKS.md — Martial Path: the 10/10 rework programme

**Created:** 2026-09-13. Derived from (a) a full read-through review of all 32
systems, 5 services, 13 engine mixins and 785 tests, and (b) a play-verified
audit — three engine runs driven through the HTTP API and the Godot client driven
live through the godot-ai MCP bridge.

**Purpose:** raise every feature from its measured score to 10/10. Each
programme below states where it is, why it is not a 10, the rework tasks, and
measurable acceptance criteria. `ROADMAP.md` stays the vision/design source;
**this file is the live tracker**.

---

> **Parallel work:** see section 8 for lanes, waves, single-writer files, merge order, and how many agents to run at once.

## 0. How to read this file

- **Programme** = one feature/system, scored and reworked to 10/10.
- **Task IDs** are `PREFIX.N` (e.g. `CB.3`). Phases in section 3 sequence them.
- Every task carries a `done:` clause that a test, a sim, or a play-verify run
  can settle. No "feels better" acceptance criteria are allowed.
- **Score** = the 2026-09-13 review score out of 10.

## 1. What 10/10 means (the rubric)

A feature is 10/10 only when **all eight** hold:

1. **Correct** — no known defect; every path it advertises actually works.
2. **Legible** — the player can see the state, the stakes and the reason for
   every refusal without external help.
3. **Deep** — real decisions with tradeoffs, not one dominant line.
4. **Balanced** — measured by the sim; no dead option, no dominant option.
5. **Narrated** — every outcome produces prose in the Chronicle panel.
6. **Tested** — unit + engine tests, plus a play-verify run recorded in the
   commit body.
7. **Validated** — new data collections are checked by the central validator;
   nothing unreachable or meaningless ships.
8. **Documented** — counts generated, not typed; behaviour described where a
   future author will look for it.

## 2. Scoreboard (current → target 10)

| Programme | Now | Target | Phase | Blocking gap |
|---|---|---|---|---|
| Truth & tooling | 8 | 10 | P0 | gate is red; docs hand-typed; no UI test coverage |
| First-run experience | 3 | 10 | P1 | killed in 3 presses on day 2 of the starter zone |
| Cultivation progression | 5 | 10 | P1-P2 | first realm not reached in 80 competent actions |
| Time model | 4 | 10 | P2 | `current_day` 6 vs `age_years` 44.8 in one run |
| Combat core | 7 | 10 | P1-P2 | damage illegible; early fights lethal |
| Dao layer | 8.5 | 10 | P2 | no dao wheel UI; matchup invisible before the fight |
| Debates & oaths | 7 | 10 | P3 | no debate-capable NPC reachable at the start |
| Encounters & exploration | 7 | 10 | P1 | 20/21 verbs blocked; generic refusal prose; blank render |
| World simulation | 6.5 | 10 | P3 | invisible in play (no ticks, no rumour surface) |
| Economy | 7 | 10 | P3-P4 | two rescue passes already; find-only content by accident |
| Alchemy & gathering | 6.5 | 10 | P3 | loop never confirmed in play; recipes ungatherable |
| Equipment & inventory | 7 | 10 | P3 | no compare/sort UX; durability opaque |
| Skills & trainers | 7.5 | 10 | P4 | no acquisition-path visibility in the UI |
| Social & NPCs | 6.5 | 10 | P3 | no NPC at either start location |
| Sects & factions | 7 | 10 | P3 | no contribution/rank loop |
| Quests & campaign | 7.5 | 10 | P3-P5 | 59 of 62 quests locked, no "what next" |
| Secret realms & endless | 7 | 10 | P3 | not reachable or telegraphed in Act 1 |
| Meta & roguelike | 7 | 10 | P2-P3 | Mortal with a 1058% execute; 100-row ledger |
| Saves & persistence | 7.5 | 10 | P6 | no v1 migration; no save/load UI |
| Narrative engine | 8 | 10 | P5 | ENCOUNTER render blank; generic refusals |
| Frontend (Godot) | 4 | 10 | P1-P6 | fixed today, but no render coverage and heavy refresh |
| Validation & hygiene | 9 | 10 | P0 | 1 error open (the seeding trap) |
| Docs | 6 | 10 | P0-P7 | hand-typed counts that drift |

---

## 3. Phases

- **P0 Gate & truth** — green the gate, generate docs, build the two harnesses.
- **P1 The first 30 minutes** — survivable opening, legible fight, taught loop,
  coherent verb set.
- **P2 Core loop** — cultivation correctness, pacing, one clock, dao legibility.
- **P3 Depth surfaced** — world, alchemy, gear, social, sects, quests, realms.
- **P4 Balance** — the sim drives tuning across combat, dao, economy, skills.
- **P5 Narrative & campaign** — prose polish, campaign pacing, endless.
- **P6 Frontend parity & accessibility** — every event rendered, every panel
  reachable, keyboard/contrast/font.
- **P7 Release** — save migration, docs, onboarding help, 1.0 tag (REL.1, REL.2).

---

## 4. Programmes

### T — Truth & tooling (8 → 10)

Gap: the gate is red; doc numbers are typed by hand and rot; the client had zero
test coverage, which is how a crash-on-startup shipped.

- **T.1** Finish the find-only seeding: make the domination guard check both
  directions so a later placement cannot turn an earlier one into a trap, then
  re-run. `done:` validator 0 errors; `pytest -q` 0 failures; report exits 0.
- **T.2** Commit the Godot refresh-crash fix plus
  `tests/test_godot_state_contract.py`. `done:` both in HEAD.
- **T.3** `tools/refresh_docs.py` writes test/validator/content counts into
  `handover.md`; a test fails when they drift. `done:` no hand-typed count in docs.
- **T.4** Promote the ad-hoc auto-player to `tools/playthrough_report.py`: N
  deterministic fresh runs reporting survival, actions/time-to-realm, income vs
  sinks, dao win-rate spread, dead-action rate. `done:` one command, CI-runnable,
  stable across repeats.
- **T.5** A Godot smoke suite (`frontend-godot/tests/`) covering: state refresh
  with `enemy: null` and `encounter: null`, every tab open/close, and every
  `EventType` render branch. `done:` suite runs via the MCP `test_run` tool.
- **T.6** Determinism replay test: a seed + recorded action log reproduces
  identical state. `done:` passes for 20 recorded logs.

### F — First-run experience (3 → 10)

Gap: hardcore seed 12345 died in **3 combat presses on day 2**; the chronicle is
100/100 identical "fell in battle at 12 yrs"; nothing explains strain, the daily
limit, or why a fight went badly.

- **F.1** Survivable opening: no formation above the player's power in
  `story_tier 1`, cap `pack_stat_scale` at `danger_level <= 2`, and a documented
  first-run mercy rule (hazards already leave the player at 1 HP — reuse the
  pattern). `done:` 200 sim runs, ≥90% reach story tier 2.
- **F.2** Combat legibility: per-turn damage dealt/taken with its components
  (attack, skill scaling, dao multiplier, combo bank, crit). `done:` the numbers
  are visible in the client without opening the Debugger.
- **F.3** A taught first hour: contextual hints driven by engine state (Train →
  Strain → Stabilise → Breakthrough → Explore → first fight), never a wall of text.
  `done:` a new player can state the next action unaided.
- **F.4** A "what next" line in the top bar sourced from engine state (current
  quest objective + nearest gate). `done:` present and correct in every mode.
- **F.5** Death screen that teaches: cause, the fight's turning point, and the
  next meta unlock's progress. `done:` rendered with real numbers.
- **F.6** Budgets: first realm ≤15 actions / ≤1 in-game year; first fight win
  rate ≥90% for a fresh character; time-to-story-tier-2 ≤30 minutes. `done:` sim.

### C — Cultivation progression (5 → 10)

Gap: not reached first realm in 80 competent actions; naive run took 242 actions
and 58 in-game years; the daily-limit fields are stale; the strain/foundation
thresholds are absent from `/state`.

- **C.1** Live daily-limit state: update (or derive) `daily_cultivation_count` /
  `last_cultivation_day` when the day advances, not only when training.
  `done:` rest → state shows a fresh counter; test pins it.
- **C.2** Expose the gate: `max_allowed_strain`, `required_foundation_stability`
  and `missing_requirements` in the state view; render "Strain 27/45 ·
  Foundation 100/70" in the Body/Essence panels. `done:` no refusal lacks a reason.
- **C.3** Retune pacing: `base_gain`, the daily multiplier ladder, strain gain vs
  stabilise, and `required_progress` so `F.6` budgets hold. `done:` sim proves it.
- **C.4** One clock: make the day the primary clock or drop it from the UI; pin
  the day↔year relationship. `done:` test asserts the invariant.
- **C.5** Essence track: re-measure unlock and pacing after C.3; verify the
  Pulse Condensation gate is clear and reachable. `done:` sim reaches essence in
  ≤X actions after the body unlock.
- **C.6** Strain/stability economy shown as numbers with the stabilise tradeoff,
  so the loop is a decision rather than a mystery. `done:` both panels show it.
- **C.7** Talent upgrades: surface elixir sources and the upgrade ladder in the
  UI. `done:` every upgrade lists its cost and where to get it.

### TM — Time model (4 → 10)

Gap: `current_day` 6 while `age_years` went 12.0 → 44.8; travel consumes seasonal
years while training does not consume days.

- **TM.1** Define the authoritative clock and make every time-consuming action
  advance it consistently. `done:` one table in the docs, enforced by a test.
- **TM.2** Show one time readout in the client that matches the engine.
  `done:` top bar and save agree.
- **TM.3** Verify lifespan death is reachable and fair (age cap vs progression
  speed). `done:` sim: a normal run only ages out long after the campaign ends.

### CB — Combat core (7 → 10)

Gap: damage illegible; a fair fight's length is unmeasured; early lethality.

- **CB.1** Damage transparency (with F.2): log every component of every hit.
- **CB.2** Statuses with durations, icons, and stacking rules visible.
- **CB.3** Enemy intent telegraph one round ahead, sourced from `FoeAI`.
  `done:` the client shows what the foe will do next.
- **CB.4** Consequence preview before committing to spar / duel / death duel.
- **CB.5** Fight-length budget: 4-8 rounds for an even matchup, no 60-round
  stalls. `done:` sim distribution within budget.
- **CB.6** Formations readable (leader vs pack, current target, remaining foes).
- **CB.7** Retreat/flee legible and able to save a run.
  `done:` sim: fleeing at <35% HP survives ≥80% of the time.

### D — Dao layer (8.5 → 10)

Gap: no dao wheel UI; the counter graph is invisible before a fight; combo chains
are undiscoverable; insight drips without explanation.

- **D.1** Dao wheel widget (the last MVP-parity gap): your dao, its counters, its
  counters' counters.
- **D.2** Matchup preview in the encounter card and fight header (who counters
  whom, and the damage multiplier that implies).
- **D.3** Combo legibility: banked stage, expected next role, and why a skill was
  refused. `done:` all three visible.
- **D.4** Insight explained (source, drip rate, spend targets) and paced.
- **D.5** Foe AI fairness audit: guard/desperation tuning produces no unwinnable
  fights inside the intended tier. `done:` sim win-rate 40-70% per matchup band.
- **D.6** Dao variety in play: at least three daos reachable in Act 1.
- **D.7** Balance daos to a target win-rate spread. `done:` no dao outside ±10%
  of the median.

### DB — Debates & oaths (7 → 10)

Gap: no debate-capable NPC reachable at the start, so the system never appears.

- **DB.1** Put a debate-capable character in the opening region.
- **DB.2** Conviction UX: bars, stance triangle help, and what sway means.
- **DB.3** Oath stakes previewed before swearing; breach consequences spelled out.
- **DB.4** Balance: matched debates end 45-60% for the player. `done:` sim.
- **DB.5** Debates feed progression so they are not optional flavour.
  `done:` at least one Act-1 quest requires a debate win.

### E — Encounters & exploration (7 → 10)

Gap: 20 of 21 verbs return `INVALID_IN_ENCOUNTER`, including read-only views; the
refusals use one generic prose line; the re-rendered encounter has no narrative.

- **E.1** Mode-aware verb set: read-only views (`SECTS`, `TRAINERS`,
  `WORLD_INFO`, `WORLD_RUMORS`, `CODEX`) available in every mode.
  `done:` matrix test pins the contract.
- **E.2** Every refusal carries a plain-language reason (the option-level reasons
  are already excellent — extend that standard to actions).
- **E.3** Prose on every encounter render path. `done:` no blank Chronicle panel.
- **E.4** Lead with stakes: odds, threat preview, and what withdrawing costs.
- **E.5** Hazards/traps never kill (already true) and always hand a legible
  consequence into the next fight.
- **E.6** Variety: measure the event mix over 100 explores; at least five kinds
  surface. `done:` sim reports the mix.

### W — World simulation (6.5 → 10)

Gap: 29 tests and a real century sim, but nothing appears in play.

- **W.1** A world digest after time-consuming actions (who rose, who died, what
  moved) — currently near-invisible.
- **W.2** NPC agency surfaced where the player can act on it (rivals, elders).
- **W.3** Sect power/standing panel with movement over time.
- **W.4** Market shows price drift and why.
- **W.5** Seasons shown as modifiers in the UI (why autumn gathering matters).
- **W.6** Rumours: a rumour surface (talk + a panel), with reveals that point at
  real places and people.
- **W.7** Performance budget: 100 years < 1s headless, pinned by test.

### EC — Economy (7 → 10)

Gap: needed two rescue passes; 68 items + 137 equipment had no acquisition path;
the rescue introduced a trap; pricing is layered in a way only the tooling knows.

- **EC.1** One displayed-price source of truth (displayed == charged), pinned.
- **EC.2** Income/sink ledger inside the tool target band (income ≈1.3x the
  costliest hall). `done:` `tools/economy_report.py` verdict passes.
- **EC.3** Zero dominated shop offers, enforced by the validator.
- **EC.4** Every item/equipment entry has a deliberate acquisition path;
  find-only becomes an explicit design tier, never an accident.
- **EC.5** Currency clarity: gold vs spirit stones explained, with sinks for
  excess gold in the mid game.

### A — Alchemy & gathering (6.5 → 10)

Gap: the loop was never confirmed end-to-end in play; recipes are visible but
their ingredients are ungatherable there; no gathering UI.

- **A.1** Show what grows here, what you hold, and what you can brew.
- **A.2** Gathering panel with seasonal/realm yields explained.
- **A.3** Refining UX: requirements per recipe plus a missing-ingredient reason.
- **A.4** Every rarity band of pill has a real use in the loop (no dead pills).
- **A.5** Teach the loop in Act 1 (a gather → refine → use beat).
  `done:` the first pill is brewed inside the tutorial arc.

### EQ — Equipment & inventory (7 → 10)

- **EQ.1** Inventory filter/sort by category and rarity.
- **EQ.2** Compare-on-hover: stat deltas against what is equipped.
- **EQ.3** Durability and repair legible (why, cost, consequence).
- **EQ.4** Set bonuses shown with progress.
- **EQ.5** Gear power curve checked per story tier; no dominated pieces.

### S — Skills & trainers (7.5 → 10)

- **S.1** Skill library browsable with its acquisition path ("learn it here / from
  this master / this manual").
- **S.2** Trainer UX: cost, path lock, and what it unlocks.
- **S.3** Balance: no skill strictly dominated by a cheaper one at its tier.
  `done:` lint/sim over tiers.
- **S.4** Every effect family (active/stat/growth) explained in the UI.

### SO — Social & NPCs (6.5 → 10)

- **SO.1** Populate the opening locations with 2-3 meetable NPCs.
- **SO.2** Dialogue choices show their consequences (relationship/morality deltas).
- **SO.3** Relationship tiers unlock content (boons, quests, sparring, debates).
- **SO.4** Morality legible: band, and how it steers quests and endings.

### SE — Sects & factions (7 → 10)

- **SE.1** Contribution/rank loop: sect tasks, inner/outer disciple progression,
  a sect store (the long-standing roadmap gap).
- **SE.2** Sect comparison before joining (path, technique hall, tier, gates).
- **SE.3** Faction storylines surfaced early enough to choose meaningfully.
- **SE.4** Path-locked techniques visible before committing.

### Q — Quests & campaign (7.5 → 10)

Gap: 62 quests, 3 active, 59 locked, no ordering; Act 1 pacing unverified.

- **Q.1** Journal that answers "what next": ordered by chain, with unlock hints.
- **Q.2** Objectives as actionable verbs with a "go there / talk to them"
  affordance.
- **Q.3** Campaign pacing measured: Act 1 completable in 1.5-2.5h; the full
  campaign near 10h. `done:` sim plays Act 1 end-to-end and reports actions/time.
- **Q.4** Progression graph test: every quest is reachable from a fresh start.
- **Q.5** Ending recap: what caused this ending (morality, factions, choices).

### R — Secret realms & endless (7 → 10)

- **R.1** First realm reachable and telegraphed in Act 1.
- **R.2** Realm UI: rooms, progress, retreat consequences, loot preview.
- **R.3** Depth/pacing measured: rewards scale with risk (sim).
- **R.4** Endless proven: 20 depths with no dead ends and no content exhaustion;
  the essence cap lift verified.

### M — Meta & roguelike (7 → 10)

Gap: a fresh Mortal wielded a legacy-taught 1058% execute; the menu shows a
100-row ledger of identical deaths.

- **M.1** Scale legacy-taught arts by realm (or gate them behind story tier) so
  early balance survives the meta layer. `done:` sim measures early power with and
  without legacy unlocks.
- **M.2** Chronicle: last 5 runs plus a summary in the menu, full history in a
  panel; death causes vary once F.1 lands.
- **M.3** Every unlock proves its effect on a run (sim: win-rate/time delta).
- **M.4** Origins 4 → 6, each with a distinct opening measured against F.6.
- **M.5** Run summary teaches: cause, peak, best moment, unlock progress.

### SV — Saves & persistence (7.5 → 10)

- **SV.1** Migration from v1 with a test per version; bump policy documented.
- **SV.2** Autosave at safe points so a crash cannot cost a run.
- **SV.3** Save/load UI in Godot (slot list, summaries, delete).
- **SV.4** Export/import surfaced in the UI.

### N — Narrative engine (8 → 10)

- **N.1** Prose on every render path (the `ENCOUNTER` gap is the known one).
- **N.2** Sameness metric below threshold; a 20-event spot-check rubric.
- **N.3** Repeat-line budget: no template repeats within one run beyond N.
- **N.4** Contextual prose verified in play (realm, season, morality, relationship).
- **N.5** One coherent narrative feed (event log vs Chronicle panel reconciled).

### U — Frontend (Godot) (4 → 10)

Gap: crash on first click (fixed today), no render test coverage, 217 Controls
rebuilt per refresh, 100-row ledger, `BOON` unrendered.

- **U.1** Dao wheel widget (D.1).
- **U.2** Every `EventType` has a render branch, enforced by a test that reads the
  GDScript match table. `done:` test fails on a new unhandled event type.
- **U.3** Journal panel (Q.1) and quest cards with real progress.
- **U.4** Combat detail panel (CB.1-CB.3).
- **U.5** Codex/bestiary/glossary tabs (ROADMAP G.4).
- **U.6** Accessibility: font size, contrast, keyboard navigation, screen-reader
  friendly labels.
- **U.7** Refresh performance: incremental updates, no full teardown; ledger
  capped. `done:` refresh <16 ms with 1k inventory items.
- **U.8** `BOON` render case plus a smoke test for every event the engine emits.

### V — Validation & content hygiene (9 → 10)

- **V.1** Gate green and running in CI (validator + dead-content sweep).
- **V.2** Reachability graph test per content type (largely built — keep it honest
  as content grows).
- **V.3** Zero trap classes; find-only is a declared tier.
- **V.4** Difficulty curve checks: enemy power vs zone danger per story tier.
  `done:` sim flags any zone outside band.

### DOC — Docs (6 → 10)

- **DOC.1** Generated counts (T.3).
- **DOC.2** Refresh `ARCHITECTURE.md` / `DATA_SCHEMA.md` plus a "how to add
  content" recipe.
- **DOC.3** `TASKS.md` is the tracker; `ROADMAP.md` is vision-only (T.4).
- **DOC.4** `handover.md` becomes a one-page orientation that links here.

---

## 5. Global acceptance gates (apply to every task)

1. `pytest -q` → 0 failures; `validate_all_game_data()` → 0 errors.
2. Play-verify: the change is exercised in the running game (API or MCP) and the
   observation is recorded in the commit body.
3. Determinism preserved (T.6).
4. Performance budgets: world tick <1s/100y; suite <60s; UI refresh <16ms.
5. Docs counts regenerated, not hand-edited.

## 6. Open decisions

1. **CLI freeze:** B.9 modified the frozen CLI — revert, or legalise the numbered
   menu?
2. **F.1 approach:** data tuning, a first-run mercy rule, or both?
3. **M.1:** scale legacy arts by realm, or gate them behind story tier?
4. **TM.1:** is the in-game day the primary clock, or the year?
5. **C.5:** keep Pulse Condensation as the essence gate, or open essence earlier
   with a weaker start?

## 7. Evidence index (2026-09-13)

- Godot refresh crash: `MainController.gd` `Dictionary.get("enemy", {})` against
  an engine `null`; fixed and play-verified (23 action cards, Train Body, prose
  plus Body Progress 0.0 → 23.2).
- Lethality: hardcore seed 12345 → dead in 3 presses on day 2; chronicle 100/100
  "fell in battle at 12 yrs".
- Pacing: 80 competent actions → still Mortal; 242 actions / age 70.3 → Strength
  Training.
- Stale limit fields: `cultivation_system.py:908-912`; 37 rests left the view at
  "3 trains, day 1".
- Gate visibility: `/state` omits `max_strain_for_breakthrough` (45) and
  `required_foundation_stability` (70); both appear only in a failure payload.
- Encounter lockout: 20 of 21 verbs `INVALID_IN_ENCOUNTER`, generic prose.
- MCP `game_eval` traps: never mix tabs and spaces (a parse error parks the game
  at a debugger break); run the whole interaction in one eval after `project_run`;
  `--check-only -s` does not register autoloads, so `MainMenuController.gd`
  false-fails that gate.

---

## 8. Parallel workstreams (multi-agent plan)

### 8.1 The three rules

1. **One writer per file, per wave.** JSON data and the Godot controller merge
   line-by-line, so two lanes in the same file means lost work. Every lane below
   therefore owns an explicit, disjoint write-set.
2. **Contract before parallelism.** Everything that touches `dispatch.py`,
   `constants.py`, `views.py` or a shared data schema lands in the serial spine
   (Wave 0) and is frozen. Lanes branch from that frozen point.
3. **Balance runs alone.** The sim-driven tuning sweep (Wave 3) changes numbers
   across every system at once and must be a single agent.

### 8.2 Waves

| Wave | Lane | Tasks | Owns (writes only these) | Depends on |
|---|---|---|---|---|
| 0 | **S0 Green the gate** | T.1, T.2 | `data/shops.json`, `data/enemies/random_enemies.json`, `tools/seed_world_content.py`, `frontend-godot/scripts/MainController.gd` (guard only), `tests/test_godot_state_contract.py` | — |
| 0 | **S1 Interface freeze** | C.2 (state fields), E.1 (info dispatch), CB.1 + F.2 (payload components), TM.1 (clock decision), U.2 (event-coverage test) | `game/core/engine/{dispatch,views,combat,encounters}.py`, `game/core/constants.py`, `game/docs/*` | S0 |
| 0 | **S2 Split for parallelism** | U.0 (split `MainController.gd` into per-panel scripts), V.5 (split `data_validator.py` per collection) | `frontend-godot/scripts/*` (new panel files), `game/validation/*.py` | S1 |
| 1 | **L1 Cultivation & time** | C.1, C.3, C.5, C.6, C.7, TM.2, TM.3 | `game/systems/cultivation_system.py`, `game/models/cultivation.py`, `game/core/engine/progression.py`, `game/data/cultivation/*.json`, `tests/test_cultivation_system.py`, `tests/test_lifespan_system.py` | S2 |
| 1 | **L2 Combat & dao feel** | CB.2, CB.5, CB.6, CB.7, D.3, D.4, D.5, D.7 | `game/systems/combat_system.py`, `game/systems/foe_ai.py`, `game/core/engine/combat.py`, `tests/test_combat_system.py`, `tests/test_combo_combat.py`, `tests/test_foe_ai.py`, `tests/test_dao_combat.py` | S2 |
| 1 | **L3 Funnel & encounters** | F.1, E.4, E.5, E.6, V.4 | `game/data/encounters.json`, `game/data/encounter_pools.json`, `game/data/enemies/random_enemies.json`, `game/data/events.json`, `game/systems/encounter_system.py`, `tools/seed_enemy_pools.py`, `tests/test_encounters.py` | S2 |
| 1 | **L4 Economy & alchemy** | EC.2, EC.4, EC.5, A.1, A.3, A.4 | `game/data/{shops,items,gathering}.json`, `game/systems/{shop,sell,alchemy}_system.py`, `game/utils/economy_balance.py`, `tools/economy_*.py`, `tools/seed_world_content.py`, `tests/test_shop_system.py`, `tests/test_sell_system.py`, `tests/test_alchemy.py`, `tests/test_economy_balance.py` | S2 |
| 1 | **L5 Narrative & prose** | N.1, N.3, N.5, E.3 | `game/data/narrative_templates.json`, `game/data/lore_glossary.json`, `game/systems/narrative_system.py`, `game/core/engine/encounters.py` (prose only), `game/validation/narrative_lint.py`, `tests/test_narrative_*.py` | S2 |
| 1 | **L6 Harness & CI** (enabler) | T.3, T.4, T.5, T.6, V.1 | `tools/*` (new files), `frontend-godot/tests/*`, `.github/workflows/*`, `tests/test_godot_state_contract.py` | S0 for T.3/T.5, S1 for payload shape |
| 1 | **L7 World, social, factions** | W.1-W.6, SO.1-SO.4, DB.1-DB.5, SE.1-SE.4 | `game/systems/{world_simulation,relationship,morality,sect,debate}_system.py`, `game/core/engine/{world,social,debate}.py`, `game/data/characters/*.json`, `game/data/sects.json`, `game/data/dialogue*`, `tests/test_world_simulation.py`, `tests/test_sect_system.py`, `tests/test_dao_debate.py` | S2 |
| 2 | **L8a…L8f Godot panels** (one lane per panel file, possible only after S2) | U.1, U.3, U.4, U.5, U.6, U.7, U.8, plus the render halves of F.2, F.4, CB.1, CB.3, CB.4, Q.1, Q.2, A.1, A.3, EQ.1-EQ.4, SV.3, SV.4, M.2, W.1-W.6 | one panel script each: `dashboard.gd`, `inventory.gd`, `equipment.gd`, `combat.gd`, `journal.gd`, `codex.gd`, `world.gd`, plus `MainMenuController.gd` | S2 **and** the Wave-1 lane that supplies the payload |
| 2 | **L9 Campaign & realms** | Q.1 (engine), Q.3, Q.4, Q.5, R.1-R.4 | `game/data/quests.json`, `game/data/secret_realms*.json`, `game/systems/quest_system.py`, `game/systems/secret_realm_system.py`, `game/core/engine/campaign.py`, `tests/test_campaign.py`, `tests/test_secret_realm.py` | S2 |
| 2 | **L10 Meta & saves** | M.1, M.3, M.4, M.5, SV.1, SV.2 | `game/systems/legacy_system.py`, `game/systems/origin_system.py`, `game/services/save_service.py`, `game/core/engine/lifecycle.py`, `game/data/legacy_tree.json`, `game/data/origins.json`, `tests/test_meta_depth.py`, `tests/test_save_system.py` | S2 |
| 3 | **S3 Balance sweep** (serial, one agent, no other lane writing) | CB.5/CB.7 tuning, D.7, EC.2 tuning, S.3, V.4 thresholds, Q.3 pacing | tuning values only, via `tools/playthrough_report.py` + `tools/economy_*.py` | L1, L2, L3, L4, L9, L10 |
| 4 | **L11 Docs & release** (parallel with S3) | DOC.1-DOC.4, REL.1 (save migration + version bump), REL.2 (README, run instructions, in-game help) | `handover.md`, `ROADMAP.md`, `README.md`, `TASKS.md`, `game/docs/*`, `backend.spec` | S1 (stable contracts) |

### 8.3 Single-writer files (never two lanes at once)

| File | Rule |
|---|---|
| `game/core/engine/{dispatch,views,combat,encounters}.py`, `game/core/constants.py` | **Wave 0 only.** Freeze after S1; later lanes request changes through S1 rather than editing |
| `game/data/narrative_templates.json` | L5 alone (every other lane's prose needs are queued as requests) |
| `game/data/{shops,items,gathering}.json` | L4 alone |
| `game/data/{encounters,encounter_pools,events,enemies/random_enemies}.json` | L3 alone |
| `game/data/characters/*.json`, `game/data/sects.json` | L7 alone |
| `frontend-godot/scripts/MainController.gd` | One writer; split by S2 first, then one lane **per panel file** |
| `game/validation/data_validator.py` | Split by S2 (V.5); before that, only S0/S1 touch it |
| `tests/` | Each lane owns its own test files; never edit another lane's |

### 8.4 Lane protocol

1. Branch `lane/<id>` from the last integrated spine commit; rebase before merge.
2. A lane is done only when **all** of these pass on its own branch:
   ```bash
   .venv/Scripts/python.exe -m pytest -q                      # no new failures
   .venv/Scripts/python.exe -c "from game.validation import validate_all_game_data as v; print(v().is_valid)"
   ```
   plus that lane's own play-verify (API harness for engine lanes, MCP run for
   any lane that changes what the client renders), recorded in the commit body.
3. Merge order inside a wave: **S2 → L6 → L1/L2 → L3/L4/L5 → L7 → L9/L10**.
   A conflict is resolved by the lane that owns the file, never by hand-merging
   data JSON.
4. After a wave integrates: re-tag the spine (`spine-w1`, `spine-w2`, …) and
   branch the next wave from it.

### 8.5 Do NOT parallelise

- **S0, S1, S2** — the gate fix, the interface freeze and the two splits. They
  touch shared schemas; run them one at a time, in order.
- **S3** — balance tuning. Numbers interact; parallel tuning produces a game
  that is locally tuned and globally wrong.
- **A validator change while other lanes are mid-write** — integrate validator
  rules in the wave's merge window, not during lane work.

### 8.6 Dependency map

```
S0 ── S1 ── S2 ─┬─ L1 ─────────────┐
                ├─ L2 ─────────────┤
                ├─ L3 ─────────────┤
                ├─ L4 ─────────────┼─ L8a..L8f (one panel each) ─┐
                ├─ L5 ─────────────┤                            ├─ S3 (serial) ─┐
                ├─ L6 (early) ─────┤                            │               ├─ L11 docs/release
                ├─ L7 ─────────────┤                            │               │
                └─ L9, L10 ────────┘                            └───────────────┘
```

### 8.7 How many agents to run

| Agents | Plan |
|---|---|
| 1 | Walk the spine, then lanes in the order L1 → L3 → L2 → L4 → L5 → L7 → L9 → L10 → UI |
| 2 | Spine on one; L6 (harness/CI) on the other from S0 — it unblocks every later measurement |
| 4 | Spine (1) + L6 (1); then L1, L3, L4 in parallel, L2 next |
| 6 | Spine + L6 early; then L1, L2, L3, L4, L5 in parallel (L7 starts as one finishes) |
| 8+ | All Wave-1 lanes at once, then split L8 into one lane per panel file |

**Expected wall-clock shape:** the spine is the critical path (it is small and
serial); Wave 1 parallelises almost perfectly because the write-sets are
disjoint; Wave 2 is bounded by the panel-file split, not by agent count; Wave 3
is deliberately serial and short.
