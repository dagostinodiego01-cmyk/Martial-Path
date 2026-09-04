# Martial Path — Roadmap to the Best Text-Based Cultivation Game Ever

**Status:** vision + phased plan. This document is the single source of task
tracking; the closed 17-priority GROK-review backlog it superseded has been
removed.

**Last updated:** 2026-09-02.

---

## 0. Vision (locked with the author)

A **data-driven text cultivation RPG** that is simultaneously deep, broad,
well-written, replayable, and balanced. The author ranked **all five** of these
dimensions as critical:

| Pillar | What it means here |
|---|---|
| **Content breadth** | Vast, living world: many sects, techniques, NPCs, regions, events, secret realms |
| **Simulation depth** | Emergent systems that interact (sects, economy, NPC agency, time) |
| **Narrative & prose** | Memorable branching story and characters, prose that reads as *written*, not generated |
| **Replayability** | Roguelike permadeath + cross-run meta unlocks + world-seed variety + NG+ |
| **Balance & polish** | Tight, fair, well-tuned systems; nothing dead or misleading; full frontend parity |

**Key decisions already made:**

- **Text engine:** templated / **procedural** (deterministic, data-driven) — **no LLM**.
- **Game shape:** a **campaign** with a real ending **+ an endless post-game**.
- **Combat:** **Dao / philosophy** model — realm-pressure and dao interplay over raw stat slugfests.
- **Progression:** **roguelike legacy** — permadeath runs + cross-run meta unlocks + NG+.
- **Distribution:** **local + GitHub** (no storefront, but keep the polish bar high).
- **Deliverable format:** phased roadmap (MVP → Alpha → 1.0 → Endless).
- **Dao model:** **both, layered** — a 5-element cycle (Metal/Wood/Water/Fire/Earth)
  **plus** philosophical daos (Sword, Time, Karma, Blood, Void…) in one counter graph.
- **Permadeath:** **hardcore by default** with an opt-out **softcore toggle**.
- **Meta unlocks:** **everything** — sects, origins, techniques, story variants,
  and titles are unlockable across runs (tiered).
- **Campaign length:** **~10h** (Act 1 ≈ 1.5–2.5h), endless post-game unlimited.
- **Win vs death:** reaching an **ending banks a large** legacy reward; **death banks
  a smaller** one (both are valid run-ends).

---

## 1. Guiding principles & hard constraints

1. **Engine owns all rules.** `game/systems/` / `game/services/` are pure; `GameEngine`
   wires state. No gameplay logic in any UI.
2. **Frontend scope: Godot only** (`frontend-godot/`). Do **not** touch
   `game/ui/cli_interface.py`, `game/application/command_router.py` (the CLI
   translator), or `game/ui/gui_interface.py` (PySide6). New player-facing UI lands
   in Godot only; the CLI/PySide are frozen.
3. **Data-driven first.** Stable `snake_case` IDs in JSON, validated centrally by
   `game/validation/data_validator.py`. New content = new JSON, not new code paths.
4. **Deterministic & seeded.** All procedural output (text, world gen, loot, events)
   derives from a per-run seed so a run is reproducible (roguelike fairness + debug).
5. **Original lore only.** No copyrighted sects/techniques/names. (Already the rule;
   this roadmap's Dao system and story must stay original.)
6. **Every task ships with:** a unit/engine test under `tests/`, and
   `validate_all_game_data()` still clean. Done-criteria are **measurable** — no
   "feels better" without a number attached.
7. **Text encoding:** narrative prose is rendered in the Godot UI (UTF-8 allowed —
   em-dashes, proper punctuation). The frozen CLI never receives the new prose; if it
   ever must, apply an ASCII sanitizer, not hand-edits.

---

## 2. Current state (baseline — all DONE)

- **Engine:** dual cultivation (Body + Essence) with strain/stability, 26 skill
  effect types, stats/passives, talent ladders + upgrades, lifespan/seasons/
  closed-door, morality/relationship/reputation, quests (chains), economy
  (buy/sell, 12 shops), trainers, sects (join, path-locked techniques), equipment
  (sets, durability, repair), combat (spar/duel, statuses, enemy abilities),
  save/meta (ironman, NG+, export/import).
- **Content:** 208 skills, 236 enemies, 251 equipment, 213 items, 50 NPCs, 29
  locations, 9 quests, 12 shops, 8 trainers, 4 sects. All skills reachable.
- **Frontend:** Godot GUI restructured (top bar + 3-column body + floating tab
  overlays + paper-doll equipment).
- **Quality:** **414 passing, 3 skipped** tests; validator **0 errors**.

**What this roadmap changes** (the gaps that stand between today and "best ever"):

1. Prose is sparse and static → needs a real **procedural narrative engine**.
2. Combat is HP/stat + status effects → needs a **Dao/philosophy model**.
3. Death/restart is an afterthought → needs **roguelike permadeath + meta unlocks**.
4. Story is 9 scattered quests → needs a **campaign arc + endless post-game**.
5. World is static between player actions → needs **NPC/faction/economy simulation**.
6. Content is broad but shallow → needs **depth + procedural secret realms**.
7. Frontend shows state but not *story* → needs **prose-forward Godot rendering**.

---

## 3. Workstreams (epics)

Each epic maps to one or more pillars; phases pull slices from epics.

- **A. Procedural Narrative Engine** — data-driven, deterministic prose for every
  action/event/description. (Pillar: narrative & prose; supports all others.)
- **B. Dao & philosophy combat** — Dao catalogue, realm-pressure, intent/insight,
  stances, counter-graph. (Pillars: simulation depth, balance.)
- **C. Roguelike legacy & meta** — permadeath default, origins, world seed, legacy
  currency/unlocks, run chronicle. (Pillar: replayability.)
- **D. Campaign + endless post-game** — act-structured story with endings + open
  ascension sandbox. (Pillars: narrative, breadth.)
- **E. Living world simulation** — NPC agency, sect/faction power, economy,
  seasons/weather, rumors. (Pillar: simulation depth.)
- **F. Content breadth** — regions, sects, techniques, NPCs, quests, secret realms,
  gathering/alchemy. (Pillar: breadth.)
- **G. Balance & polish** — dead-content elimination, simulation-tuned balance,
  full Godot parity, QoL/codex/accessibility. (Pillars: balance & polish.)

---

## 4. Phased roadmap

Each phase has an **exit criterion** (objective, testable). Tasks are checkboxes with
a measurable done-criterion in parentheses.

---

### PHASE 1 — MVP ("the core loop sings")

**Goal:** a complete, replayable vertical slice: one act of story, dao combat,
procedural prose for every core verb, permadeath + one meta unlock, one procedural
secret realm. Small but *whole*.

**Exit criterion:** a brand-new player can complete Act 1 → die (permadeath) →
restart with a visible meta unlock → play again and see a *different* run, with
every action narrated procedurally and dao combat replacing stat slugfests. Suite
green, validator clean, Godot renders all of it.

#### A — Narrative engine v1
- [x] **A.1** Template format + engine: JSON templates with `{variable}` slots,
  weighted variant pools, and conditional clauses (`if realm>=X`). Data-driven, no
  code changes to add prose. (≥ 3 weighted variants per core verb.)
  `game/systems/narrative_system.py` + `game/data/narrative_templates.json`.
- [x] **A.2** State-aware description generators for: location, NPC, item,
  technique, breakthrough, death. (Each returns prose varying by realm/morality/
  relationship/season.)
- [x] **A.3** Seeded determinism: same run seed → identical prose; different seed →
  different prose. (Property test over 1,000 seeds.)
- [x] **A.4** Godot rendering path for prose (event-log + a dedicated "narrative"
  panel), UTF-8 safe. (No missing `_render_event` cases — incl. `BOON`.)

#### B — Dao combat core
- [x] **B.1** `game/data/daos.json`: 12 original Daos (5-element cycle +
  philosophical cycle + neutral Void), each with `affinities` + `counters` /
  `countered_by`. Validator checks ids, affinities, counter-graph symmetry, and
  enemy `dao_id` references. (`tools/seed_enemy_daos.py` tags all 21 named foes.)
- [x] **B.2** Character `dao` assignment: `player.dao_id` (default `sword_dao`) and
  `enemy.dao_id` (nullable), both round-tripping through saves. Origin-based
  choice lands with C.3.
- [x] **B.3** Realm pressure: composite rank = body order + (essence order − 1); a
  gap ≥ 2 suppresses the weaker side's offense/defense, a gap ≥ 4 makes it yield
  (exploration foes only). Engine skips trivial fights via `enemy_yields`.
- [x] **B.4** Dao interplay: attacking a countered Dao deals 1.5×, attacking a
  countering Dao deals 0.75×, wired into `CombatSystem` (attack, skills, enemy
  attacks/abilities). *(The Godot "Dao wheel" UI is part of G.1 — pending.)*- [x] **B.5** Intent/insight combat resource: builds from comprehension + successful
exchanges; unlocks stronger techniques mid-fight. (Ties the existing
`comprehension` stat into combat. The 20 `*_intent` techniques carry
`insight_required`; insight drips from `comprehension // 10` each round and
`+1` per damaging hit/crit/counter. UI surfacing lands with G.1.)

#### C — Roguelike core
- [x] **C.1** Permadeath default: death ends the run (ironman becomes the default;
  optional softcore toggle). Death produces a **run summary** (cause, achievements,
  realms reached). (Death → run over, no reload.)
- [x] **C.2** One meta currency ("Ancestral Memory") earned on death/retirement,
  persisted across runs. (Currency persists in a meta-save outside the run.)
- [x] **C.3** Origins: ≥ 4 starting backgrounds (e.g. orphan, noble scion, sect
  foundling, fallen immortal) with different starting dao/technique/stat/story hook.
  (Origins gated by meta currency.)
- [x] **C.4** Run chronicle/graveyard: list of past runs (seed, origin, dao, death
  cause, peak realm). (Persisted + shown in Godot main menu.)

#### D — Campaign Act 1 + endless hook
- [x] **D.1** Act 1 arc: tutorial → join/choose sect → first rival → first
  tournament → a mid-act dao awakening. (A linear-but-branching quest chain with a
  real Act-1 endpoint, not a stub.)
- [x] **D.2** First procedural secret realm: seeded dungeon generator (rooms,
  encounters, loot, a boss) → gives the endless-post-game its first shape. (Two runs
  with different seeds produce different layouts/rewards.)

#### F — Alchemy loop (foundational)
- [x] **F.1** `gather` verb at herb-rich locations; `refine` herbs → pills/elixirs
  (reuses `talent_refining_elixir` as a template). (Herbs are now real inventory
  items with a refine chain; validator covers the recipe graph.)
- [x] **F.1b** Alchemy breadth: 26 rarity-tagged herbs, each region-locked via
  `gathering.json` (demonic ingredients only in the Holy Demon Continent), and
  104 refining recipes gated by cultivation realm (`minimum_body_realm` /
  `minimum_essence_realm`). Secret realm catalogue expanded to 6 hand-placed
  realms. (`tools/expand_alchemy.py` regenerates the four data files.)

#### G — parity for the slice
- [x] **G.1** Godot widgets for every new MVP action (dao view, gather, refine,
  origin select, run summary). (No action reachable only via API.)

---

### PHASE 2 — ALPHA ("depth + breadth")

**Goal:** the whole game is present: full campaign, living world, full dao system,
rich meta unlocks, and a broad content base. Still pre-balance.

**Exit criterion:** a full playthrough Act 1→3 exists with at least two distinct
sect storylines; the world moves without the player (NPCs/sects/economy); meta
unlocks meaningfully change successive runs; procedural prose covers every action.

#### A — Narrative engine full coverage
- [x] **A.5** Prose for 100% of actions/events (zero fallback "debug" strings in
  Godot). (Instrumentation test: every `EventType` has a template.)
- [x] **A.6** Voice consistency: tone guide + lore glossary enforced by validator
  (terminology whitelist, no Mad-Libs artifacts). (0 template errors; a "sameness"
  metric — min distinct variants across a 100-event run.)
  `game/docs/VOICE_GUIDE.md` + `game/data/lore_glossary.json` (seeded from real
  display names/ids) + 4 linter checks in `narrative_lint.py` (gamey terms,
  brace artifacts, ≥2 variants/verb, glossary conformance); sameness property
  test drives a 100-event mixed-action run (`tests/test_narrative_voice.py`).
- [x] **A.7** Authoring ergonomics: `tools/` linter for templates (unused vars,
  missing vars, unbalanced branches). (CI-checks on template data.)

#### B — Dao combat full
- [x] **B.6** Stances + combos: techniques typed opening/response/finisher; chained
  sequences grant bonuses. (Combo system tested for balance and legibility.)
  `combo_role` on 9 chain techniques (3 chains); each banked chain stage grants
  +25% damage into the next technique (1.25x/1.5x/1.75x); neutral techniques
  don't break a chain but don't advance it; engine blocks a wrong-role chain
  skill mid-sequence, refunds qi otherwise, and surfaces
  `combo_stage`/`expected_combo_role`. Chain state is transient (reset each
  fight); validator enforces role vocab/one-role-per-skill.
  (`tests/test_combo_combat.py`, 17 tests.)
- [x] **B.7** Dao debates (non-lethal philosophical duels won by insight) and
  spirit-oath duels with asymmetric stakes. (Distinct from spar/duel/death duel.)
  *Done 2026-09-04:* pure `DebateSystem` (stance triangle assert > probe >
  transcend > assert with a one-round probe-exposure pin, insight-based sway,
  dao-matchup scaling, yield resistance); `MODE_DEBATE` with
  `DEBATE_CHARACTER`/`OATH_DUEL_CHARACTER`/`DEBATE_STANCE`/`YIELD_DEBATE`/
  `WALK_AWAY` actions; offered wherever a character can spar. Spirit-oath
  stakes: win banks 1.5x the sworn gold/exp, loss costs half exp + full wager,
  walking away is a **breach** forfeiting the larger of the wager or half
  current gold, stalemate releases both. Debate conviction is insight-shaped
  and restored after (combat pool untouched). Narrative verbs + validator-clean
  templates; Godot renders conviction bars, oath notices, and stake outcomes.
  (`tests/test_dao_debate.py`, 13 tests.)
- [x] **B.8** Enemy/foe AI uses dao + pressure + stances, not just abilities.
  (Boss fights exploit the counter graph.) *Done 2026-09-04:* pure `FoeAI`
  consulted every enemy phase -- dao-carrying foes fight stance chains
  (opening -> response -> finisher, feeding the same combo bank as the player,
  with +25%/stage into their technique), counter-graph aggression (x1.5 when
  their dao counters yours, x0.6 when countered), wounded desperation, and a
  **guard** that shelters behind +50% defense and banks the respected flow into
  their next press. Mooks (no dao) keep the plain ability/attack pipeline.
  Bosses/elite duelists in `named_foes.json` now carry real chain techniques.
  (`tests/test_foe_ai.py`, 14 tests.)

#### C — Meta depth
- [x] **C.5** Legacy/unlock tree: meta currency unlocks sects, origins, techniques,
story variants, titles. (A browsable unlock tree in Godot.)
  *Done 2026-09-02:* `data/legacy_tree.json` (3 tiers: sects/techniques/titles) +
  pure `LegacySystem`; `UNLOCK_TREE`/`UNLOCK` actions; purchases persist in the
  meta-save, apply on every new character (techniques) and surface as
  `player.title`; validator covers ids/kinds/targets/tier reachability; Godot
  legacy popups in-game and on the main menu. (`tests/test_meta_depth.py`.)
- [x] **C.6** World seed: seeded procedural variation (which sects dominate, market
prices, encounter pools, event order). (Two seeds → measurably different world
state at year 10.)
  *Done 2026-09-02:* the run seed derives a deterministic seed report -- two
  dominant sects (listed first, `-5` reputation subsidy on their join gate), an
  economy band (cheap 0.9 / fair 1.0 / pricey 1.15) scaling all shop prices, and
  an encounter bias consumed by `EventSystem`. Same seed → identical world;
  12 seeds → ≥ 2 distinct bands (pinned by test).
- [x] **C.7** Retirement/ascension as a *win*: reaching the campaign ending banks a
large meta reward and continues into endless mode. (Win ≠ death; both are valid
run-ends.)
  *Done 2026-09-02:* `RETIRE_ASSENT` (≥ Divine Transformation essence) ends the
  run as a win: banks `(death reward) x 3`, records an `ascended` chronicle
  entry (rendered as "ascended beyond the world" in Godot), sets a persisted
  `retired` meta flag, and carries an `endless` flag through saves for the
  post-game. `POST /retire` exposes it to the API.

#### D — Full campaign + post-game
- [x] **D.3** Acts 2–3 (faction conflict → dao awakening → realm war → final
  ascension choice) with ≥ 3 endings. (Campaign completable; endings recorded in the
  chronicle.)
  *Done 2026-09-04:* Act 2/3 chains in `quests.json` (join-sect → Schism War duels →
  Act-2 dao rekindling with a reopened one-change window → realm war against the
  ancient devil → threshold sentinel → final breakthrough beat). Completing the
  final act wins the campaign: `CampaignMixin._maybe_complete_campaign` banks a
  150-memory bonus and picks one of three morality-driven endings (realm_martyr /
  demon_sovereign / ascended_sword), recorded as `campaign_ending` in the
  chronicle. Godot renders the ending and act banners. (`tests/test_campaign.py`,
  D.3 block.)
- [x] **D.4** Sect storylines: ≥ 2 full faction campaigns with branching outcomes.
  (Faction quest chains, not one-off quests.)
  *Done 2026-09-04:* `phoenix` and `valleys` chains (3 quests each), gated by the
  player's sect path (`requires.path_any`) and split into ruthless/honorable
  branches by morality (`min_morality` / `max_morality` gates, morality rewards).
  New objective types wired into real actions: `spar` (gentle branch), `debate`
  (B.7 verdicts), `realm_completed` (secret-realm survival). QuestSystem gates
  and rewards extended; validator enforces quest refs. (`tests/test_campaign.py`,
  D.4 block.)
- [x] **D.5** Endless post-game opens on ascension: procedural secret realms,
  scaling challenges, no realm cap. (Endless mode playable indefinitely without
  content exhaustion for ≥ 50h.)
  *Done 2026-09-04:* `ENDLESS_REALM` action opens `SecretRealmSystem.generate_endless`
  realms at ever-deeper levels — procedural layouts, mixed mook/named foes,
  depth-scaled stats (x1.15/depth) and rewards (x1.25/depth), deterministic per
  (seed, depth). The first descent lifts the essence track's final cap
  (`theoretical_endpoint`), so Beyond Divinity becomes reachable in endless play;
  depth rewards accrue per completed realm. Endless runs also start via the API
  (`endless` new-game flag); flags round-trip through saves. Endless road gated
  behind campaign completion or a retired run. (`tests/test_campaign.py`, D.5 block.)

#### E — Living world simulation
- [x] **E.1** NPC agency: NPCs train/compete/join sects/form rivalries/die on a
  world-tick that advances with player time. (World state changes without player
  input; observable via relationship/status changes.) — `WorldSimulationSystem.tick`
  runs on a dedicated seeded RNG stream from every calendar-consuming action
  (train/rest/meditate/travel/closed-door); roster of all 50 named NPCs cultivates
  with realm-slowed odds, the strongest clash, elders die on the road. Tests:
  `tests/test_world_simulation.py` (E.1 block).
- [x] **E.2** Sect/faction simulation: power/wealth/influence shift; wars, alliances,
  sect rise/fall. (Sect standing changes over a 100-year sim.) — sect power is
  recomputed from living members' ranks and smoothed; empty sects decay to the
  base. Century sim: sects reorder (>1.0 spread), world thins but never empties.
- [x] **E.3** Economy simulation: dynamic prices, supply/demand, market shocks.
  (Prices move with events, not fixed JSON.) — wealth-per-cultivator supply and
  death-scarcity demand nudge a bounded (0.7-1.4) price multiplier; it layers on
  the C.6 seed band in `ShopSystem` so displayed == charged prices.
- [x] **E.4** Seasons/weather as real modifiers (travel, gathering, encounter odds)
  — P12 made seasons display; make them *act*. (Season changes gameplay, tested.)
  — `SEASON_MODIFIERS`: Autumn doubles gather yield, Winter halves it and slows
  travel 1.5x, Summer/Autumn raise combat odds (EventSystem `set_combat_bias`),
  Winter slows NPC progress 0.7x. Travel now consumes seasonal years.
- [x] **E.5** Rumor/intel system: overheard rumors reveal events/people/opportunities
  (feeds quests + narrative). (Rumors are state-backed, not static flavor.) —
  deaths/market moves/sect shifts mint bounded-lifetime rumors; LEARN_RUMOR
  returns a concrete reveal (sect/location/npc with display name); talking to any
  character may surface an unlearned rumor. Save round-trips the world state.

#### F — Breadth
- [x] **F.2** Expand regions/sects/techniques/NPCs/events per the content targets in
  §6 (no dead content — every new entry reachable, validator-enforced).
  *Done 2026-09-04:* locations 29 → 45 (16 new across story tiers 2–6, all
  bidirectionally wired, pooled, and positioned on the map); sects 4 → 12
  (tier 1–6 halls referencing existing skills); 12 new NPCs anchored with
  `min_story_tier` tags and named-foe combat entries; 16 new encounter pools
  wired to previously-unused enemies (dead-content pass: 205 unused → far
  fewer); 2 shops + 2 trainers. `tests/test_content_breadth.py` guards counts,
  connectivity, pools, and reachability.
- [x] **F.3** Faction + character quest arcs (not just location quests).
  *Done 2026-09-04:* three 3-quest faction arcs (Seven Profound Valleys,
  Divine Phoenix, Asura War Pavilion) chained via `requires`, gated on
  `act1_conclusion`, giving skill rewards (`glacial_sword_art`, `phoenix_fist`,
  `blood_sea_roar`); each arc's first quest is offered by an expansion NPC at
  the faction's frontier (broker, pearl mistress, war envoy). Arcs unlock
  alongside the parallel Act 2/3 campaign work.

---

### PHASE 3 — 1.0 ("best ever: balance + polish + prose quality")

**Goal:** everything present is *tight and beautiful*. This phase is where "best
ever" is won or lost — balance, prose quality, and UX.

**Exit criterion:** a simulation-tuned balance pass with no dominant/dead builds; a
prose quality pass (human-readable, voice-consistent, varied); full Godot UX with
codex/journal/glossary/accessibility; a complete campaign + endless integration;
release docs and onboarding.

#### G — Balance & polish
- [ ] **G.2** Dead-content sweep: every skill/item/technique/dao/enemy is reachable
  and meaningful (0 unreachable, 0 trap options). (Validator + reachability tests.)
- [ ] **G.3** Simulation-based balance: automated headless runs/duels to measure
  win-rates, progression curve, time-to-realm, and economy sinks. (CI balance report;
  no build with >X% win-rate spread across daos.)
- [ ] **G.4** QoL/codex: journal, bestiary, glossary of terms, dao wheel, save/load
  UI, accessibility (font size, contrast, screen-reader-friendly text). (All in
  Godot.)
- [ ] **G.5** Onboarding/tutorial + in-game help that teaches dao combat, not just
  buttons. (New-player funnel: ≥ 80% complete Act 1 without external help.)

#### A — Prose quality pass
- [ ] **A.8** Prose polish: variant richness, sentence variety, lore-accurate voice.
  (Sameness metric below threshold; spot-check rubric on a 20-event sample.)

#### D — Campaign/endless integration
- [ ] **D.6** Seamless campaign → endless transition; ending banked, endless
  continues with the same character. (Transition tested end-to-end.)

#### G — Release readiness
- [ ] **G.6** Save migration + version bump; docs (`ARCHITECTURE`, `DATA_SCHEMA`,
  `ROADMAP`, `handover`); README with run instructions; full test/validator green.
  (1.0 tag cut.)

---

### PHASE 4 — ENDLESS / post-1.0 (stretch)

- [ ] **END.1** Expansions: new continents, new Dao families, new realms.
- [ ] **END.2** Challenge modes: sealed-cultivation (no shop), dao-only (no items),
  speedrun-to-ascension, daily seeded runs.
- [ ] **END.3** Achievement + title system beyond meta unlocks.
- [ ] **END.4** (If ever approved) optional LLM dialogue layer as an *add-on*, not a
  dependency — the deterministic engine stays the baseline.

---

## 5. Cross-cutting concerns (do in every phase)

- **Determinism:** all RNG goes through one seeded `RNG`; a run's seed reproduces it
  exactly (test: replay a seed's action log → identical state).
- **Save/meta split:** run-save (per-character, permadeath-scoped) vs meta-save
  (ancestral memory, unlocks, chronicle) must be separate files; bump `SAVE_VERSION`
  on schema changes with migration tests.
- **Testing:** unit + engine tests per task; headless Godot parse/runtime check on
  every GDScript change; property tests for the text engine and generators.
- **Validation:** every new data collection gets a `_validate_*` in
  `data_validator.py` (ids, references, reachability, ranges).
- **Performance:** world-tick simulation must run headless in < 1s/year at 100 years
  (it gates the living-world epic).

---

## 6. Content targets (breadth, measurable)

| Content | Today | 1.0 target |
|---|---|---|
| Regions / locations | 45 | 45+ ✅ |
| Sects | 12 | 12+ ✅ (faction storylines in via F.3) |
| Skills / techniques | 215 | 300+ (all dao-tagged, all reachable) |
| Daos | 12 | 12+ (with counter graph) ✅ |
| NPCs | 90 | 120+ (with agency + arcs) |
| Quests | 62 | 60+ (acts + factions + characters) ✅ |
| Secret realms / dungeons | 6 | 1 procedural generator, 10+ hand-placed |
| Origins | 4 | 6+ |
| Endings | 0 | 3+ |

---

## 7. Decisions (confirmed 2026-08-14)

1. **Dao model flavor:** both, layered — 5-element cycle **+** philosophical daos
   in one counter graph.
2. **Permadeath:** hardcore default with an opt-out softcore toggle.
3. **Meta unlock scope:** everything — sects, origins, techniques, story variants,
   titles (tiered).
4. **Campaign length:** ~10h (Act 1 ≈ 1.5–2.5h), endless post-game unlimited.
5. **Win vs death:** ending banks a large legacy reward; death banks a smaller one.

---

## 8. Definition of done (per task)

A task is **done** when all hold:

1. Code/data committed to `game/` (and `frontend-godot/` for UI), following §1.
2. At least one test under `tests/` exercises it (unit or engine-level).
3. `validate_all_game_data()` returns 0 errors (new data collections validated).
4. Godot script parses clean (`--headless --check-only`).
5. `handover.md` notes the change; the `ROADMAP.md` checkbox is flipped to `[x]`.
