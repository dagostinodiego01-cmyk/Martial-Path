# TASKS.md — Martial Path: the 10/10 rework programme

**Created:** 2026-09-13. Derived from (a) a full read-through review of all 32
systems, 5 services, 13 engine mixins and 785 tests, and (b) a play-verified
audit — three engine runs driven through the HTTP API and the Godot client driven
live through the godot-ai MCP bridge.

**Last reviewed:** 2026-10-11.

**Purpose:** raise every feature from its measured score to 10/10. Each
programme below states where it is, why it is not a 10, the rework tasks, and
measurable acceptance criteria. `ROADMAP.md` stays the vision/design source;
**this file is the live execution tracker**. Historical scorecards and landing
notes are retained below for context, but they do not override the live plan in
this section or section 8.

---

> **Cross-chat rule:** every new chat starts by reading this file, checking
> `git status`, selecting exactly one milestone/subtask, and declaring its write
> set before editing. At the end, update the milestone status and paste a
> handoff record using the template in section 9. Never reset, stage, or
> overwrite work belonging to another chat.

### Current execution baseline (2026-10-11)

| Signal | Current review state |
|---|---|
| Branch / tree | `main`, clean and pushed; the L1-L4 implementation wave landed as `868d6e7`. No uncommitted work is expected; inspect `git status` before any edit. |
| Python gate | Latest full run: 1003 passed, 4 skipped, 1 strict xfail, 0 failures (33 new tests landed with M1). |
| Data gate | Validator: 0 errors. Dead-content sweep: 0 unreachable, 0 trap options. Economy report passes. |
| Determinism gate | 20 recorded replay logs pass, and fresh-process save continuation is now identical: `tests/test_save_continuation.py` loads a v3 save in a separate process built from an unrelated seed and matches the original event sequence and state digest (two seeds, plus a negative control). |
| Godot gate | Headless Godot 4.7 checks pass, including the 8/8 L1 render check. Display-only/manual verification is still pending. |
| Known release debt | Counter-graph strict xfail, High/Deadly tier cliff, UI refresh budget, packaging, and fresh-machine verification are not release-complete. Crash-safe persistence, migration, and API session ownership closed with M1; the Godot side of the action contract (API.1) is an M3 item. |

### Live execution plan (active)

The order below is intentionally different from the old historical wave table.
It adds persistence/transport correctness before broad feature work, integrates
Godot panels as payloads become stable, and keeps balance serial.

| ID | Milestone | Status | Primary owner | Exit condition |
|---|---|---|---|---|
| **M0** | Integrate and re-baseline | **COMPLETE (2026-09-25)** | Integrator / documentation chat | Current tree reviewed, active docs reconciled, gates recorded, no stale execution instructions |
| **M1** | Save continuity and transport safety | **COMPLETE (2026-10-11)** | Persistence/API chat | Fresh-process save continuation is identical; migrations, atomic writes, recovery, and session ownership are tested |
| **M2a** | L5 narrative and prose | **NEXT — after M1, contract checkpoint passed** | Narrative/data chat | Every render path has prose; voice/repetition/context checks pass |
| **M2b** | L7 world, social, factions | **NEXT — parallel to M2a only in a separate worktree** | World/social chat | World changes, NPC actions, sect standing, debates, and factions are surfaced and playable |
| **M2c** | L9 campaign and realms | PENDING after L7 contract checkpoint | Campaign/realms chat | Campaign, three endings, secret realms, and endless transition pass end-to-end |
| **M2d** | L10 residual meta work | PENDING after M1 | Meta/content chat | Legacy/origin/chronicle work is complete without reopening persistence ownership |
| **M3** | L8 rolling Godot parity | **ROLLING** | One panel per Godot chat | Stable payloads are reachable, rendered, live-HTTP tested, and refresh performance is measured |
| **M4** | S3 balance sweep | PENDING after M2/M1 baseline | One balance chat, serial | No unexplained xfails; target win-rate, pacing, encounter, and economy bands pass |
| **M5** | L11 release hardening | PENDING after M1/M3/M4 | Release chat | Clean Windows package launches, saves/reloads, and passes a fresh-machine verification |

#### M0 — Integrate and re-baseline

- **Role:** integrator; this is a review/documentation milestone, not a feature
  lane.
- **Start with:** inspect the current diff and classify changes by engine/data,
  Godot, replay fixtures, and documentation. Do not infer ownership from file
  names alone.
- **Write set:** `TASKS.md`, `handover.md`, `ROADMAP.md`, and `README.md` only
  when the change is a status/documentation correction.
- **Out of scope:** gameplay tuning, save implementation, broad UI refactoring,
  staging, committing, resetting, or deleting another chat's work.
- **Exit evidence:** current gate results are recorded; the archived “held
  commit” instructions are clearly marked historical; `TASKS.md` is named the
  live tracker; current known gaps are listed without stale “gate is red” claims
  in the active status.

<!-- CHAT-HANDOFF M0
Start: read the Current execution baseline and inspect `git status`.
Write set: documentation/status files only.
Stop when: the current tree has a reviewable, non-destructive status packet.
Next chat: M1 persistence/API owner.
-->

**M0 completion record (2026-09-25):** reviewed the shared `main` tree without
staging, resetting, or deleting existing work. Classified 61 changed paths
across engine/data, Godot, tests/replay fixtures, tools, and documentation;
20 replay fixtures and the new `check_l1_render.gd` are part of the existing
implementation wave. Reconciled `README.md`, `ROADMAP.md`, and `handover.md`;
the live tracker now owns status and handoffs. Recorded gates: 970 passed,
4 skipped, 1 strict xfail; validator/dead-content/economy/playthrough pass; Godot
event/state checks pass with the available Godot 4.7 binary. No gameplay files
were edited during M0. **M1 is now the next blocking chat.**

#### M1 — Save continuity and transport safety

- **Role:** persistence/API owner; this milestone blocks release and any
  save-dependent UI work.
- **Tasks:** SV.1, SV.2, SV.5, SV.6, API.1, API.2, API.3.
- **Write set:** `game/utils/rng.py`, `game/core/engine/lifecycle.py`,
  `game/services/save_service.py`, `game/persistence/save_repository.py`,
  `game/services/meta_service.py`, `game/api/server.py`, the corresponding
  `tests/test_save_system.py` / `tests/test_api_server.py` (or new focused test
  files), and `game/docs/SAVE_SYSTEM.md` / `ARCHITECTURE.md` where the contract
  changes.
- **Required behavior:** persist all RNG streams and the run seed; migrate old
  versions; write atomically; recover from corrupt files; autosave only at safe
  points; serialize or explicitly guard the single API session.
- **Out of scope:** visual panel design, balance values, new content, and broad
  `MainController.gd` changes.
- **Exit evidence:** a fresh process loads a save and produces the same event
  sequence and state digest as the original continuation; v1/v2 migration,
  corruption recovery, atomic-write, API concurrency, and live HTTP tests pass.

<!-- CHAT-HANDOFF M1
Start: confirm M0 is integrated and inspect the save snapshot/RNG ownership.
Write set: persistence, API, focused tests, and save/architecture docs only.
Stop when: fresh-process continuation and transport safety are proven.
Next chat: M2a/M2b contract checkpoint, then rolling L8 panels.
-->

**M1 completion record (2026-10-11):** all seven M1 tasks are closed.
**SV.5** — the snapshot now carries the run seed, all five RNG streams' full
internal state (new `RNG.get_state`/`set_state`), the seed-derived world
variation, the narrative stable-prose key, cooldowns, fate, active realm, oath
stakes and the `running` flag; `tests/test_save_continuation.py` proves a save
loaded **in a separate Python process built from an unrelated seed** replays
the original run's remaining ~170 actions event-for-event and lands on the
same state digest (2 seeds + in-process variant + negative control). The one
real gap it exposed — `render_stable` prose keyed by the narrative system's
stored seed — is fixed and pinned. **SV.1** — `SAVE_VERSION` is 3 with a
tested v1→v2 (talent-field rename) and v2→v3 (documented defaults) chain;
imported old payloads are migrated on write; missing/absent/future versions
still fail `SAVE_VERSION_MISMATCH`. **SV.6** — atomic writes (serialise →
fsynced tmp → move-aside `.bak` → promote) with backup recovery on read;
serialisation-failure, simulated-crash and corrupt-primary tests pass. **SV.2**
— `at_safe_point()` + `autosave()` with one policy; explicit saves outside a
safe point refuse with `UNSAFE_SAVE_POINT`; the API autosaves only after
successful, non-refused turns. **API.1** — `game/api/action_contract.json`
pins the `/action` contract, unknown fields are 422 (`extra="forbid"`).
**API.2** — a single session lock serialises every engine-touching endpoint.
**API.3** — `tests/test_api_live_http.py` drives a real `uvicorn` subprocess
through state/action/save/load, 422s and concurrent mutations. Also: saves
honour `MARTIAL_PATH_SAVE_DIR`, so the suite no longer writes into the real
save directory. **Gate evidence:** `pytest -q` → 1003 passed, 4 skipped, 1
strict xfail, 0 failures; validator 0 errors; dead-content clean; economy
report OK; 20 replay logs reproduce; `refresh_docs.py --check` fresh;
playthrough report 19/20 alive, 20/20 reach story tier 2, 0 dead actions of
3950; `git diff --check` clean. Save/architecture docs updated
(`SAVE_SYSTEM.md`, CHANGELOG). **Not in M1:** save/load UI (SV.3/SV.4 → M2d),
Godot-side contract check (API.1 render half → M3), balance (M4).
**Next chat: M2a (L5 narrative) or M2b (L7 world/social)** — separate
worktrees if parallel; the M1 contract is frozen.

#### M2a–M2d — Engine breadth after the persistence checkpoint

- **Role:** one system owner per chat; do not combine M2 lanes in a shared
  checkout.
- **M2a:** L5 owns narrative templates, glossary, narrative system, encounter
  prose, and narrative tests.
- **M2b:** L7 owns world simulation, relationships, morality, sects, debates,
  character data, and their focused tests.
- **M2c:** L9 owns quests, campaign, secret realms, endings, and endless; pause
  for a short contract review before changing shared dispatch/view payloads.
- **M2d:** L10 owns residual legacy/origin/chronicle work after M1 has closed
  persistence ownership; it must not reopen save-service changes casually.
- **Shared rule:** any proposed change to `dispatch.py`, `views.py`,
  `constants.py`, or a shared schema is a contract checkpoint, not an implicit
  side effect of a feature lane.
- **Exit evidence:** each lane passes focused tests, the full Python gate,
  validator/dead-content checks, replay checks, and an API or play verification.

<!-- CHAT-HANDOFF M2
Start: copy the exact lane ID and write set into the chat before editing.
Stop when: the lane's done clauses and play verification are recorded.
Next chat: name the next lane and whether it starts from a clean integrated tree.
-->

#### M3 — Rolling Godot parity

- **Role:** one Godot panel/transport owner per chat; the shell owner is the only
  writer allowed to edit `MainController.gd` for cross-panel wiring.
- **Order:** combat/encounter first, then quest guidance, status/equipment,
  world/codex/campaign, and meta/save surfaces.
- **Write set:** one panel or transport file per chat, plus its focused Godot
  test and fixture. Shared `UIKit.gd` and `MainController.gd` changes require an
  explicit shell-owner handoff.
- **Required behavior:** render backend numbers and refusal reasons without
  re-deriving rules; handle nullable state safely; avoid full teardown; add live
  HTTP smoke coverage; measure the refresh budget with 1,000 inventory items.
- **Out of scope:** gameplay rules, balance constants, and unrelated art/data.
- **Exit evidence:** all actions in the lane are reachable in a real client
  session, the event/state contract remains green, and the performance result is
  recorded rather than estimated.

<!-- CHAT-HANDOFF M3
Start: name the panel, its backend payload owner, and the exact one-file write set.
Stop when: the panel passes headless render, live HTTP, and focused performance checks.
Next chat: list any panels still waiting on a payload or shell decision.
-->

#### M4 — S3 balance sweep

- **Role:** one balance owner, serial; no UI or content lane writes while the
  sweep is active.
- **Tasks:** resolve the strict counter-graph xfail, the High/Deadly tier cliff,
  zone-band flags, economy bands, and campaign pacing.
- **Write set:** tuning constants/data and the balance reports/tests explicitly
  named by the balance owner. Record every intentional replay-fixture change.
- **Out of scope:** broad feature additions, panel refactors, and opportunistic
  cleanup.
- **Exit evidence:** seeded simulations cover the target Dao/tier/story bands;
  no unexplained xfail remains; dead-action, economy, retreat, and pacing
  budgets pass; the report is attached to the handoff.

<!-- CHAT-HANDOFF M4
Start: verify M1 and the M2 baseline are integrated and freeze non-tuning writes.
Stop when: the balance report meets the written bands and fixtures are current.
Next chat: M5 release owner.
-->

#### M5 — L11 release hardening

- **Role:** release owner; split infrastructure work from final certification.
- **L11a (early):** choose the first supported platform, pin dependencies,
  create the backend package/export path, and define install/run behavior.
- **L11b (final):** produce the Godot/backend artifacts, test clean startup and
  shutdown, verify save migration on a clean machine, and finalize docs.
- **Write set:** packaging/config files, release scripts, README, handover,
  roadmap, and release notes. Gameplay and balance files are read-only.
- **Exit evidence:** a fresh Windows x64 machine can launch the packaged game,
  start the local backend, create a run, save, reload, and reach the first
  campaign milestone without a source checkout.

<!-- CHAT-HANDOFF M5
Start: require M1, M3, and M4 exit evidence.
Stop when: the release checklist and fresh-machine result are recorded.
Next chat: post-1.0 roadmap work only after the 1.0 candidate is accepted.
-->

### Spine status (2026-09-13)

| Step | Task | State |
|---|---|---|
| S0 | T.1, T.2 | **✅ Done** — committed as `85abce5` on `main`; tag `spine-w0` marks its parent |
| S1 | C.2, E.1, CB.1/F.2, TM.1, U.2 | **✅ Done** — committed (payload halves; the *render* halves are the L8 lanes) |
| S2 | U.0, V.5 | **✅ Done** — committed with S1; see below |

S1 landed together with the concurrent identity/rename work, which could not be split
away: `dispatch.py` and `MainController.gd` carry both changes, and the spine rule
(§8.1) is that a wave lands whole. Verified 2026-09-13: `pytest -q` → 848 passed,
3 skipped; `validate_all_game_data()` → 0 errors; `tools/dead_content_report.py` →
exit 0, "nothing unreachable, no trap options". Spot-check per task: C.2 publishes
`body_transformation.breakthrough` / `essence_gathering.breakthrough` (gates +
`missing_requirements`) from `cultivation_service.get_cultivation_state()` and the
client renders "Strain n/45 · Foundation n/70"; E.1 resolves the informational verbs
before any mode check in `_process_action_raw`; CB.1/F.2 attach a `breakdown` to every
hit event in `combat_system.py`; TM.1's single clock is `Player.age_years`, documented
in `game/docs/TIME_MODEL.md` and pinned by `tests/test_time_model.py`; U.2's
`tests/test_godot_event_coverage.py` reads the GDScript match tables.

One honest gap inside S1's scope: CB.1/F.2 shipped the **payload** half ("CB.1 + F.2
(payload components)" is the S1 column in §8.2) — the *render* half of F.2, the numbers
on screen in the client, is owned by the L8a-L8f panel lanes.

S2 landed in the same tree (831 tests passing, validator clean). **V.5** split the
1,354-line validator by collection: `game/validation/{support,economy_checks,
progression_checks,world_checks,character_checks}.py` behind an unchanged
`validate_all_game_data()` facade, proven equivalent against a deliberately
corrupted registry (identical 47 errors, same order, same 37 categories) and pinned
by `tests/test_validator_split.py`.

**U.0** split the 3,600-line `MainController.gd` down to 2,890 lines: the palette
and every stateless widget/stylebox/formatting factory moved to
`frontend-godot/scripts/UIKit.gd`, and the five overlay tabs to
`InventoryPanel.gd` / `EquipmentPanel.gd` / `JournalPanel.gd` / `StatusPanel.gd` /
`TechniquesPanel.gd`. The controller keeps its `COLOR_*` names as aliases of the
kit and its `_render_*` entry points as one-line delegations, so no call site
changed. Each panel owns its own widgets and asks the host to act by signal.
Verification is `frontend-godot/tests/check_panels.gd` (run headlessly by
`tests/test_godot_panels.py`, which skips when no Godot binary is present): it
builds every panel from a synthetic state payload and asserts the text a player
would read reaches the tree.

Two notes for whoever commits this:
- `MainController.gd` still carries the concurrent identity/rename work, exactly as
  S1 does. Land S1 and S2 together, or after the identity work is committed.
- Adding a `class_name` script requires the Godot editor to rescan before
  `--check-only` can resolve it (`godot --headless --path frontend-godot --import`
  refreshes `.godot/global_script_class_cache.cfg`). Otherwise the GDScript gate
  reports `Identifier "UIKit" not declared` and cascading false errors.

#### Historical S1 + S2 landing note — archived; do not execute

> The staging instructions below describe an old shared-tree state. They are
> retained as historical context only. The current tree has moved on; use the
> active milestone plan above and inspect the live diff before any Git action.

Everything is written, wired and green in the working tree (840 passed / 3 skipped,
0 failed; validator `is_valid: True`, 0 errors; panel check 6/6 OK). It is **held**
because the concurrent identity/rename feature is finished but uncommitted, and
S1+S2 cannot be committed without it:

- committed `MainController.gd` references the `Profile` autoload **0** times; the
  working-tree version references it **3** times
- `project.godot`'s `Profile="*res://scripts/PlayerProfile.gd"` autoload line is
  uncommitted, and `PlayerProfile.gd` is **untracked**

So staging `MainController.gd` without those two puts three unresolvable `Profile`
references on the spine and the client stops compiling. **Precondition — this must
print a number greater than 0 before staging:**

```bash
git show HEAD:frontend-godot/scripts/MainController.gd | grep -c 'Profile\.'
```

Once it does, land the spine (explicit paths only — never `git add -A`, the tree
carries a second writer):

```bash
git add game/systems/cultivation_system.py game/services/cultivation_service.py \
  game/systems/combat_system.py game/core/engine/dispatch.py \
  game/core/engine/progression.py game/core/engine/world.py \
  game/models/player.py game/models/cultivation.py \
  game/data/cultivation/cultivation_config.json game/docs/TIME_MODEL.md \
  game/validation/data_validator.py game/validation/support.py \
  game/validation/economy_checks.py game/validation/progression_checks.py \
  game/validation/world_checks.py game/validation/character_checks.py \
  frontend-godot/scripts/MainController.gd tests/test_time_model.py \
  tests/test_godot_event_coverage.py tests/test_validator_split.py \
  tests/test_codex.py tests/test_cultivation_system.py tests/test_game_engine.py \
  tests/test_save_system.py TASKS.md
git commit   # then: git tag spine-w1
```

Not in that list because they belong to the other thread: `game/core/engine/views.py`,
`game/core/constants.py`, `handover.md`, `project.godot`, `MainMenuController.gd`,
`game/api/server.py`, `narrative_system.py`, `locations.json`, `narrative_templates.json`,
`DESIGN.md`, `PRODUCT.md`, the avatar/location art, and `PlayerProfile.gd` /
`IdentityEditor.gd`. The panels and their check already landed separately in
`ba5bd3d`, so a lane can branch off `spine-w1` with the UI split in place either way.

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

## 2. Scoreboard (2026-09-13 baseline → target 10)

> The table below is the historical review baseline. It is not the current
> execution status; use the live milestone table near the top of this file.

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
- **P0b Persistence & transport** — deterministic save continuation, migrations,
  crash-safe writes, session ownership, and a versioned command/state contract.
- **P1 The first 30 minutes** — survivable opening, legible fight, taught loop,
  coherent verb set.
- **P2 Core loop** — cultivation correctness, pacing, one clock, dao legibility.
- **P3 Depth surfaced** — world, alchemy, gear, social, sects, quests, realms.
- **P4 Balance** — the sim drives tuning across combat, dao, economy, skills.
- **P5 Narrative & campaign** — prose polish, campaign pacing, endless.
- **P6 Frontend parity & accessibility** — every event rendered, every panel
  reachable, keyboard/contrast/font.
- **P7 Release** — persistence migration, packaging, docs, onboarding help, and
  the 1.0 tag (`REL.1-REL.4`).

---

## 4. Programmes

> The individual programme gap lines and scores below preserve the original
> 2026-09-13 review context. For active status, use the M0-M5 plan at the top;
> do not infer that a historical gap is still open without checking the current
> gate evidence.

### T — Truth & tooling (8 → 10)

Gap: the gate is red; doc numbers are typed by hand and rot; the client had zero
test coverage, which is how a crash-on-startup shipped.

- **T.1** Finish the find-only seeding: make the domination guard check both
  directions so a later placement cannot turn an earlier one into a trap, then
  re-run. `done:` validator 0 errors; `pytest -q` 0 failures; report exits 0.
- **T.2** Commit the Godot refresh-crash fix plus
  `tests/test_godot_state_contract.py`. `done:` both in HEAD.
- **T.3 — ✅ DONE** `tools/refresh_docs.py` writes test/validator/content counts into
  `handover.md` between `refresh_docs` markers; `tests/test_docs_freshness.py`
  fails when the block drifts *and* when a hand-typed count reappears in the live
  part of the document (dated history sections are exempt). `done:` no hand-typed
  count in docs -- the three that remained were rewritten and the block carries
  all thirteen.
- **T.4 — ✅ DONE** `tools/playthrough_report.py` plays N seeded runs with a
  deterministic policy and reports survival, actions to the first realm and to
  story tier 2, gold/stone income vs sinks, the per-dao win-rate spread, and the
  dead-action rate with its top refusal reasons. `--json` for CI,
  `--max-dead-rate` to fail a build, `--dao a,b` for the balance spread,
  `--record <dir>` to write replay logs. `done:` one command, CI-runnable, and
  byte-identical across repeats (`tests/test_playthrough_report.py` pins it).
- **T.5 — ✅ DONE** `frontend-godot/tests/SmokeRunner.tscn` + `SmokeRunner.gd`
  cover a refresh with `enemy: null` and `encounter: null`, a repeat refresh, a
  combat and an encounter refresh, every tab opened and closed, and one render of
  every result payload a real run produced (written by
  `tests/test_godot_smoke.py` from a seeded playthrough). It runs as a *scene*
  rather than a `-s` script, because `-s` has no autoload context and
  `MainController.gd` cannot even compile there. The `EventType` arm contract
  stays with `tests/test_godot_event_coverage.py` (U.2), which reads the match
  tables; the smoke suite proves the arms survive real payloads. `done:` executed
  against Godot 4.7 locally -- 5 tabs, 13 event payloads, 0 failures.
- **T.6 — ✅ DONE** `tests/test_determinism_replay.py` replays the twenty logs in
  `tests/fixtures/replay_logs/` (recorded by the T.4 tool) on fresh engines and
  asserts both the event sequence and the final state digest match. Includes a
  negative control: a tampered log must fail to reproduce. `done:` 20 logs, each
  replaying bit-for-bit.

- **T.7** Rebaseline the live tracker after the current implementation wave:
  reconcile the active status with the working tree, archive obsolete landing
  instructions, and make generated evidence and known gaps unambiguous.
  `done:` `TASKS.md` names the current milestone and no active section claims
  that a green gate is red or that a fixed UI gap is still open.

### F — First-run experience (3 → 10)

Gap: hardcore seed 12345 died in **3 combat presses on day 2**; the chronicle is
100/100 identical "fell in battle at 12 yrs"; nothing explains strain, the daily
limit, or why a fight went badly.

- **F.1 — ✅ DONE** Survivable opening. While `max_story_tier < 2` the encounter
  layer runs a **funnel** (`data/encounters.json` → `funnel`): a hostile scene
  never fields a foe above the player's own fighting weight (the drawn foe is
  swapped for one the pool offers in band; if the pool has none, the lightest
  thing it has is sent), pack members are drawn from the same band, ambushes and
  embedded hazard ground are withheld, and `pack_stat_scale` is capped by
  danger (0.5 at `danger_level <= 2`, unchanged above). `ruined_shrine` gained
  an in-band foe so every story-tier-1 zone has something to send.
  `done:` **200 sim runs, 192/200 (96%) reach story tier 2**, 183/200 alive at
  the cap (was 3/20 alive, 6/20 reaching tier 2).
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

- **C.1 — ✅ DONE (closed as obsolete)** The TM.1 clock decision removed the day
  clock this task tuned, so there is no daily counter left to keep live; strain is
  the throttle now. `test_body_training_reports_no_daily_counter` pins that.
- **C.2** Expose the gate: `max_allowed_strain`, `required_foundation_stability`
  and `missing_requirements` in the state view; render "Strain 27/45 ·
  Foundation 100/70" in the Body/Essence panels. `done:` no refusal lacks a reason.
- **C.3 — ✅ DONE** Retuned to data + code: the starting talent roll narrowed to a
  0.5x-2.0x band (was 0.25x-10x), strain/stabilise economy rebalanced, first-realm
  `required_progress` lowered, failed openings recoverable. Median opening fell
  19 → 10 actions / 0.54 years, 97% inside F.6's budget over 200 seeds.
  `test_the_first_body_realm_lands_inside_the_opening_budget` pins it.
- **C.4** One clock: make the day the primary clock or drop it from the UI; pin
  the day↔year relationship. `done:` test asserts the invariant.
- **C.5 — ✅ DONE** The essence gate is config-driven (`essence_unlock.gate_body_realm`,
  was hard-coded Pulse Condensation) and now sits on the *first* body realm, so the
  whole track unlocks around action ~10 instead of ~350.
- **C.6 — ✅ DONE** `CultivationSystem.training_economy` publishes both sides of the
  strain loop from the same config the actions read; the character sheet and status
  panel show strain against the real gate cap (was a fictional /100) plus the
  stabilise trade and whether one more session closes the gate.
  Pinned by `training_economy_matches_the_referee` and the L1 render check.
- **C.7 — ✅ DONE** Every talent upgrade in the `TALENTS` dialog lists its elixir cost
  and where to buy one at the live market price (`item_sources`, built by
  `shop_system`); the dead Talents button was fixed earlier in the same lane.
  Pinned by `test_talent_dialog_publishes_elixir_sources` + the L1 render check.

### TM — Time model (4 → 10)

Gap: `current_day` 6 while `age_years` went 12.0 → 44.8; travel consumes seasonal
years while training does not consume days.

- **TM.1** Define the authoritative clock and make every time-consuming action
  advance it consistently. `done:` one table in the docs, enforced by a test.
- **TM.2 — ✅ DONE** The top bar renders YEAR/SEASON/AGE from the engine's lifespan
  view (the save-agreement half was already pinned by `test_time_model.py`); the
  L1 render check asserts the labels match the engine's numbers verbatim.
- **TM.3 — ✅ DONE** Sim: a 300-action focused opening burns ~14.6 of 100 mortal
  years (budget derived from the configured time cost), no seed dies mid-opening;
  the death mechanism itself is pinned by `test_reaching_lifespan_cap_ends_the_run`.

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
- **E.4 — ✅ DONE** Lead with stakes. Every choice card now carries the odds it
  runs on and the price of walking away: `odds` (threat band + foe/player power)
  and `chance` on the checks, `cost` on a toll, `forfeit` plus a stakes line on
  withdraw/leave/decline, and a trap-risk estimate on an unread find. Copy lives
  in `data/encounters.json` → `stakes`; a number the client already badges (the
  `chance` percentage) is never repeated in the line.
- **E.5 — ✅ DONE** The ground's consequence is carried into the next fight. A
  hazard or trap that took HP is remembered and named in the next combat
  encounter's body text and fight card (`wound`), once — healing in between
  clears it. Hazards still floor at 1 HP (`HAZARD_HP_FLOOR`), unchanged.
- **E.6 — ✅ DONE** Variety is measured, not assumed: 100 explores in a zone must
  surface at least five kinds (test), and `tools/playthrough_report.py` now
  prints the run-wide `event mix` — currently 6 kinds
  (character/combat/hazard/loot/nothing/special).

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
- **EC.2 — ✅ DONE** `tools/economy_report.py` verdict passes (priciest technique
  180 vs 294.5 budget; costliest hall 930 vs 1060.1), and the target band is
  locked: `test_income_to_cost_band_holds` pins the live income/expenses ratios
  inside the designed shares (0.10-0.35 for the priciest technique, 0.60-0.95
  for the costliest hall) so a content wave that quietly halves income trips a
  balance alarm, not just a reachability one. Share-band widening is S3's call.
- **EC.3** Zero dominated shop offers, enforced by the validator.
- **EC.4 — ✅ DONE** Every entry has an authored path (the sweep has reported
  zero unreachable items/equipment since the rescue pass), and find-only is now
  an explicit data tier: `FIND_ONLY_ALLOWLIST` in
  `game/validation/dead_content.py` is the only way a find-only entry stays
  green, `accidental_find_only` fails the sweep for anything else, and
  `test_find_only_items_are_declared` keeps the allowlist short (≤10), fully
  declared, and free of stale ids.
- **EC.5 — ✅ DONE** Two halves. Payload: `get_game_state()` now carries
  `currency_guide` — the canonical gold-vs-stones explainer rendered verbatim
  from `game/systems/currency.py`, the same module that enforces the rules it
  describes, pinned by `test_currency_guide_exists_and_is_renderable`. Data
  gate: `_validate_currency_economy` (wired into the central validator) proves
  spirit stones have an authored sink anywhere in the world and that a gold
  sink is graph-reachable from the start by every story tier, so mid-game gold
  always has an answer — `test_currency_economy_validator_passes` holds it.

### A — Alchemy & gathering (6.5 → 10)

Gap: the loop was never confirmed end-to-end in play; recipes are visible but
their ingredients are ungatherable there; no gathering UI.

- **A.1 — ✅ DONE** `get_game_state()` now carries `gathering_here`: the
  current location's weighted herb table joined to the player's holdings and
  every recipe each herb feeds (`held`, `weight`, `used_in`), gated by the same
  rule as the GATHER action so it never advertises a table the ground will not
  pay. The brew side was already live (`refining_recipes`); pinned in
  `tests/test_alchemy.py`.
- **A.2** Gathering panel with seasonal/realm yields explained.
- **A.3 — ✅ DONE** Every recipe entry now carries the ingredient ledger:
  `missing` (shortfall per input), and `brewable` (realm met *and* nothing
  missing) beside the existing realm gate — the frontend's have/need rows and
  lock reasons render from engine numbers instead of re-deriving them.
  Pinned in `tests/test_alchemy.py`.
- **A.4 — ✅ DONE** No dead pills, proven rather than assumed: the sweep grew a
  pill-domination check (`dominated_shop_pills`) mirroring the equipment rule —
  a consumable offer strictly beaten by a same-effect shelf-mate is a trap.
  First run found 9 real traps across 4 racks (flat generator pricing hid real
  potency ladders); repriced in `game/data/shops.json` so each same-effect
  shelf is a strictly rising ladder. Zero now, and the sweep stays in
  `validate_all_game_data()`.
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

- **SV.1** Migrate every supported run-save version (currently v1 and v2) with
  a test per version; bump the save policy only after the migration path is
  green. `done:` old saves load with documented defaults and stable player/world
  state.
- **SV.2** Define and implement autosave only at documented safe points (after
  a successful turn, camp/arrival, or explicit save), with a clear policy for
  what is never auto-saved. `done:` a crash cannot silently corrupt the current
  run and the autosave policy is covered by tests.
- **SV.3** Save/load UI in Godot (slot list, summaries, delete).
- **SV.4** Export/import surfaced in the UI.
- **SV.5 — M1 BLOCKING** Preserve deterministic continuation across a fresh
  process: serialize every gameplay RNG stream and the run seed, and add a
  cross-engine continuation test. `done:` the same saved state produces the
  same event sequence and state digest after load/export/import.
- **SV.6 — M1 BLOCKING** Make run-save and meta-save persistence crash-safe:
  atomic writes, a backup/recovery policy, and explicit corrupt-file handling.
  `done:` interrupted writes leave the previous valid file recoverable and
  tests cover the recovery path.

### API — Transport & session contract

- **API.1** Publish a versioned action/state contract fixture for the fields the
  engine dispatch actually reads. `done:` malformed, missing, and unknown
  command fields have stable error behavior; the Godot and Python contracts are
  checked from the same fixture.
- **API.2** Define and enforce ownership of the single local game session. The
  current global `GameEngine` must either be serialized behind a session lock or
  explicitly reject concurrent clients. `done:` concurrent `/action`, `/save`,
  `/load`, and `/new-game` calls cannot interleave mutations.
- **API.3** Add a live HTTP smoke path for the Godot transport, separate from
  synthetic payload tests. `done:` a real local server accepts state, action,
  save, and load requests through the client-facing contract.

### REL — Release hardening

- **REL.1** Declare the first supported distribution target and pin the Python
  dependency set. Working assumption: Windows x64 first; record any change here.
- **REL.2** Package the FastAPI backend as a reproducible executable with a
  documented startup/shutdown contract and a clear port-conflict message.
- **REL.3** Maintain a Godot export preset that includes required assets and
  excludes development-only tooling; verify a clean export imports and starts.
- **REL.4** Perform fresh-machine release verification and finalize the run,
  save, recovery, and troubleshooting documentation.

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

- **V.1 — ✅ DONE** `.github/workflows/ci.yml` runs the gate on every push and pull
  request: the engine job runs the suite, `validate_all_game_data()`, the
  dead-content sweep, `tools/refresh_docs.py --check` and the playthrough report
  with a dead-action budget; the Godot job installs Godot 4.7, imports the
  project and runs the panel, shell-smoke, event-coverage and state-contract
  checks. Every `run:` block was verified locally (YAML parse, `bash -n`, and the
  Godot selection executed against a real Godot 4.7 binary).
- **V.2** Reachability graph test per content type (largely built — keep it honest
  as content grows).
- **V.3** Zero trap classes; find-only is a declared tier.
- **V.4 — ✅ DONE** Difficulty-curve audit: `tools/seed_enemy_pools.py --audit`
  reports every zone's typical/weakest/strongest foe against the danger it
  advertises, rolls the table up per story tier, and flags `over_band`,
  `under_band` and `no_in_band_leader` (`--strict` exits non-zero on the two
  that matter). The seeder's placement band was tightened from 3.5 to 2.0.
  Current flags, assigned to **S3** to tune (not silent data edits):
  `over_band` — `nine_furnace_kingdom`, `southern_wilderness`,
  `planetary_gate_array`; `under_band` — six zones that advertise more danger
  than they deal (`ruined_shrine`, `misty_gorge`, `beast_mountain`, ...).

### DOC — Docs (6 → 10)

- **DOC.1** Generated counts (T.3).
- **DOC.2** Refresh `ARCHITECTURE.md` / `DATA_SCHEMA.md` plus a "how to add
  content" recipe.
- **DOC.3** `TASKS.md` is the tracker; `ROADMAP.md` is vision-only (T.4).
- **DOC.4** `handover.md` becomes a one-page orientation that links here.
- **DOC.5 — M0** Rebaseline the live status: mark historical scorecards and
  landing notes as historical, identify the canonical tracker, and list current
  gate evidence and unresolved release blockers. `done:` a new chat can identify
  the next milestone without relying on stale prose.

---

## 5. Global acceptance gates (apply to every task)

1. `pytest -q` → 0 failures; `validate_all_game_data()` → 0 errors.
2. Twenty recorded replay logs still reproduce, and any intentional gameplay
   contract change regenerates them in the same change.
3. Save-dependent work also passes a fresh-process continuation test; a release
   candidate has no unexplained strict xfail.
4. Engine/API work is exercised through the real local HTTP path; Godot work
   passes headless scene checks and a live transport smoke.
5. Play-verify the change in the running game (API or Godot/MCP) and record the
   observed result in the handoff.
6. Performance budgets: world tick <1s/100y; suite <60s where practical; UI
   refresh <16ms with 1,000 inventory items.
7. Docs counts are generated, active status is current, and historical sections
   are clearly labelled rather than presented as live claims.
8. No lane stages, resets, deletes, or overwrites files outside its declared
   write set.

## 6. Open decisions

1. **Release target:** Windows x64 is the working assumption for L11a. Confirm or
   replace it before packaging; do not leave the backend/export target implicit.
2. **Save migration:** M1 will move the run-save policy to the next version and
   provide tested v1/v2 migration. The current exact-version rejection behavior
   is not the final release policy.
3. **Session ownership:** choose serialized single-session access for the local
   API; do not imply multiplayer/network safety.
4. **Panel order:** combat/encounter and quest guidance are the first L8 parity
   targets; stable inventory/equipment/journal work may proceed in parallel.
5. **Resolved historical decisions:** F.1 uses both data and rule fixes; TM.1
   uses `Player.age_years` as the one clock; C.5 is config-driven and already
   implemented. Do not reopen them without a new measurement or design note.

## 7. Evidence index (2026-09-13)

- Godot refresh crash: `MainController.gd` `Dictionary.get("enemy", {})` against
  an engine `null`; fixed and play-verified (23 action cards, Train Body, prose
  plus Body Progress 0.0 → 23.2).
- Lethality: hardcore seed 12345 → dead in 3 presses on day 2; chronicle 100/100
  "fell in battle at 12 yrs". **After L3 (2026-09-13):** the same seeds give
  200 runs → 183 alive at the action cap, 192 (96%) reaching story tier 2, 0 dead
  actions; measured with `tools/playthrough_report.py --runs 200`.
- L3 zone audit: before the fix a fresh Mortal (power 193) met a 952-power foe in
  `ruined_shrine` (a story-tier-1 zone, no travel gate) and a 262-power foe in the
  starting woods; `tools/seed_enemy_pools.py --audit` now reports the per-zone
  band, and 3 zones remain `over_band` for S3 to tune.
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

### 8.1 The active rules

1. **One writer per file, per milestone.** JSON data, generated replay logs,
   and the Godot controller are shared integration surfaces. Every chat declares
   a disjoint write set before editing.
2. **Contract before parallelism.** M0 and M1 establish the baseline, save
   continuity, and transport/session fields. Changes to `dispatch.py`, `views.py`,
   `constants.py`, or a shared schema require an explicit contract checkpoint.
3. **Balance runs alone.** M4/S3 changes numbers across combat, encounters,
   economy, and pacing; it is always a single-owner milestone.
4. **A shared checkout is single-writer.** Separate branches/worktrees are
   required for real parallel work; a second chat must wait for a handoff rather
   than edit the same tree concurrently.

### 8.2 Current execution waves

The active order is M0 → M1 → M2a/M2b → M2c/M2d, with M3 rolling alongside
stable payloads, then M4 → M5. Lanes may run in parallel only in separate
branches/worktrees with disjoint write sets; a shared checkout is single-writer.

| Milestone | Status | Tasks | Owns (write set) | Depends on | Exit |
|---|---|---|---|---|---|
| **M0 Integrate/rebaseline** | COMPLETE (2026-09-25) | T.7, DOC.5 | Status/docs only; preserve the current diff | Current tree | Gate evidence and canonical tracker are current |
| **M1 Save/transport** | COMPLETE (2026-10-11) | SV.1, SV.2, SV.5, SV.6, API.1-API.3 | RNG, save/meta repository, lifecycle, API, focused tests, save/architecture docs | M0 | Fresh-process continuation, migration, recovery, and session tests pass |
| **M2a L5 Narrative** | PENDING | N.1, N.3, N.5, E.3 | Narrative templates/glossary/system, encounter prose, narrative tests | M1 contract freeze | Every render path is narrated and voice checks pass |
| **M2b L7 World/social** | PENDING | W.1-W.7, SO.1-SO.4, DB.1-DB.5, SE.1-SE.4 | World/social/sect/debate systems, character/sect data, focused tests | M1 contract freeze | World, NPC, sect, and debate loops are surfaced and playable |
| **M2c L9 Campaign/realms** | PENDING | Q.1-Q.5, R.1-R.4 | Quest/campaign/realm data and systems, focused tests | M2b contract checkpoint | Campaign, endings, realms, and endless pass end-to-end |
| **M2d L10 Meta residual** | PENDING | M.1-M.5, SV.3-SV.4 | Legacy/origin/chronicle and save UI after M1; no persistence rewrite | M1 | Meta progression and save surfaces are complete |
| **M3 L8 rolling panels** | ROLLING | U.1-U.8 and render halves of delivered payloads | One Godot panel/transport file per chat; shell owner for `MainController.gd` | Payload owner identified per panel | Live render, transport, accessibility, and refresh checks pass |
| **M4 S3 balance** | PENDING | CB.5, CB.7, D.7, EC.2, S.3, V.4, Q.3, known tier/counter findings | Tuning values/data and balance reports only | M1 + M2 baseline | No unexplained xfail; all target bands pass |
| **M5 L11 release** | PENDING | DOC.1-DOC.5, REL.1-REL.4 | Packaging, dependency/config, release docs and fresh-machine checks | M1 + M3 + M4 | Clean packaged install launches and saves/reloads |

### 8.2a Historical lane map (reference only)

The older S0/S1/S2 and L1-L11 ordering below is retained to explain the existing
implementation history. It is superseded by the active milestone table above;
do not use it to schedule new chats without applying the M0-M5 gates. In
particular, the old L10/L11 save-migration overlap is resolved by M1 → M2d →
M5.

| Wave | Lane | Tasks | Owns (writes only these) | Depends on |
|---|---|---|---|---|
| 0 | **S0 Green the gate — ✅ DONE** | T.1, T.2 | `data/shops.json`, `data/enemies/random_enemies.json`, `tools/seed_world_content.py`, `frontend-godot/scripts/MainController.gd` (guard only), `tests/test_godot_state_contract.py` | — |
| 0 | **S1 Interface freeze — ✅ DONE** | C.2 (state fields), E.1 (info dispatch), CB.1 + F.2 (payload components), TM.1 (clock decision), U.2 (event-coverage test) | `game/core/engine/{dispatch,views,combat,encounters}.py`, `game/core/constants.py`, `game/docs/*` | S0 |
| 0 | **S2 Split for parallelism — ✅ DONE** | U.0 (moved the palette + five overlay tabs out of `MainController.gd`), V.5 (split `data_validator.py` per collection) | landed: `frontend-godot/scripts/{UIKit,InventoryPanel,EquipmentPanel,JournalPanel,StatusPanel,TechniquesPanel}.gd`, `game/validation/{support,economy_checks,progression_checks,world_checks,character_checks}.py` | S1 |
| 1 | **L1 Cultivation & time — ✅ DONE** | C.1 (closed: TM.1 removed the day clock it tuned), C.3, C.5, C.6, C.7, TM.2, TM.3 | `game/systems/cultivation_system.py`, `game/models/cultivation.py`, `game/core/engine/progression.py`, `game/data/cultivation/*.json`, `tests/test_cultivation_system.py`, `tests/test_lifespan_system.py` | S2 |
| 1 | **L2 Combat & dao feel — ✅ DONE (engine payload + measured audit; the Godot render half is L8)** | CB.2, CB.5, CB.6, CB.7, D.3, D.4, D.5, D.7 | `game/systems/combat_system.py`, `game/systems/foe_ai.py`, `game/core/engine/combat.py`, `tests/test_combat_system.py`, `tests/test_combo_combat.py`, `tests/test_foe_ai.py`, `tests/test_dao_combat.py` | S2 |
| 1 | **L3 Funnel & encounters — ✅ DONE** | F.1, E.4, E.5, E.6, V.4 | `game/data/encounters.json`, `game/data/encounter_pools.json`, `game/data/enemies/random_enemies.json`, `game/data/events.json`, `game/systems/encounter_system.py`, `tools/seed_enemy_pools.py`, `tests/test_encounters.py` | S2 |
| 1 | **L4 Economy & alchemy — ✅ DONE (engine payload + data gates; the Godot render half is L8)** | EC.2, EC.4, EC.5, A.1, A.3, A.4 | `game/data/{shops,items,gathering}.json`, `game/systems/{shop,sell,alchemy}_system.py`, `game/utils/economy_balance.py`, `tools/economy_*.py`, `tools/seed_world_content.py`, `tests/test_shop_system.py`, `tests/test_sell_system.py`, `tests/test_alchemy.py`, `tests/test_economy_balance.py` | S2 |
| 1 | **L5 Narrative & prose** | N.1, N.3, N.5, E.3 | `game/data/narrative_templates.json`, `game/data/lore_glossary.json`, `game/systems/narrative_system.py`, `game/core/engine/encounters.py` (prose only), `game/validation/narrative_lint.py`, `tests/test_narrative_*.py` | S2 |
| 1 | **L6 Harness & CI — ✅ DONE** | T.3, T.4, T.5, T.6, V.1 | `tools/*` (new files), `frontend-godot/tests/*`, `.github/workflows/*`, `tests/test_godot_state_contract.py` | S0 for T.3/T.5, S1 for payload shape |
| 1 | **L7 World, social, factions** | W.1-W.6, SO.1-SO.4, DB.1-DB.5, SE.1-SE.4 | `game/systems/{world_simulation,relationship,morality,sect,debate}_system.py`, `game/core/engine/{world,social,debate}.py`, `game/data/characters/*.json`, `game/data/sects.json`, `game/data/dialogue*`, `tests/test_world_simulation.py`, `tests/test_sect_system.py`, `tests/test_dao_debate.py` | S2 |
| 2 | **L8a…L8f Godot panels** (one lane per panel file — S2 is done, so these can start) | U.1, U.3, U.4, U.5, U.6, U.7, U.8, plus the render halves of F.2, F.4, CB.1, CB.3, CB.4, Q.1, Q.2, A.1, A.3, EQ.1-EQ.4, SV.3, SV.4, M.2, W.1-W.6 | one file each — today: `InventoryPanel.gd`, `EquipmentPanel.gd`, `JournalPanel.gd`, `StatusPanel.gd`, `TechniquesPanel.gd`, `UIKit.gd`; still to extract: the dashboard/combat/codex/world panels, plus `MainMenuController.gd` | S2 **and** the Wave-1 lane that supplies the payload |
| 2 | **L9 Campaign & realms** | Q.1 (engine), Q.3, Q.4, Q.5, R.1-R.4 | `game/data/quests.json`, `game/data/secret_realms*.json`, `game/systems/quest_system.py`, `game/systems/secret_realm_system.py`, `game/core/engine/campaign.py`, `tests/test_campaign.py`, `tests/test_secret_realm.py` | S2 |
| 2 | **L10 Meta & saves** | M.1, M.3, M.4, M.5, SV.1, SV.2 | `game/systems/legacy_system.py`, `game/systems/origin_system.py`, `game/services/save_service.py`, `game/core/engine/lifecycle.py`, `game/data/legacy_tree.json`, `game/data/origins.json`, `tests/test_meta_depth.py`, `tests/test_save_system.py` | S2 |
| 3 | **S3 Balance sweep** (serial, one agent, no other lane writing) | CB.5/CB.7 tuning, D.7, EC.2 tuning, S.3, V.4 thresholds, Q.3 pacing; plus the two L2 findings — the High-tier win-rate cliff and the 1.5x/0.75x counter-graph severity (see `handover.md` §5) | tuning values only, via `tools/playthrough_report.py` + `tools/economy_*.py` | L1, L2, L3, L4, L9, L10 |
| 4 | **L11 Docs & release** (parallel with S3) | DOC.1-DOC.4, REL.1 (save migration + version bump), REL.2 (README, run instructions, in-game help) | `handover.md`, `ROADMAP.md`, `README.md`, `TASKS.md`, `game/docs/*`, `backend.spec` | S1 (stable contracts) |

### 8.3 Single-writer files (never two lanes at once)

| File | Rule |
|---|---|
| `game/core/engine/{dispatch,views,combat,encounters}.py`, `game/core/constants.py` | **Wave 0 only.** Freeze after S1; later lanes request changes through S1 rather than editing |
| `game/data/narrative_templates.json` | L5 alone (every other lane's prose needs are queued as requests) |
| `game/data/{shops,items,gathering}.json` | L4 alone |
| `game/data/{encounters,encounter_pools,events,enemies/random_enemies}.json` | L3 alone |
| `game/data/characters/*.json`, `game/data/sects.json` | L7 alone |
| `frontend-godot/scripts/MainController.gd` | One writer: the shell (top bar, dossier, location, chronicle, actions, dialogs). The five overlay tabs are now their own files, so a panel lane never has to touch this. |
| `game/validation/data_validator.py` | Now a thin facade. Edit the per-collection module that owns the rule (`economy_checks.py`, `world_checks.py`, `character_checks.py`, `progression_checks.py`). |
| `tests/` | Each lane owns its own focused test files; never edit another lane's tests to make a gate pass. |
| `game/utils/rng.py`, `game/services/save_service.py`, `game/persistence/save_repository.py`, `game/services/meta_service.py`, `game/core/engine/lifecycle.py`, `game/api/server.py` | **M1 only.** L10 waits for M1 to integrate; no parallel save/API edits. |
| `TASKS.md`, `handover.md`, `ROADMAP.md`, `README.md` | **M0/DOC owner only.** Feature chats record handoff notes here but do not rewrite status or historical sections. |

### 8.4 Cross-chat lane protocol

1. **Start:** read the live milestone table, inspect `git status`, and announce
   the milestone, role, write set, and read-only dependencies before editing.
2. **Claim one unit:** a chat owns one milestone or one panel/lane at a time. If
   the work requires a file outside the declared write set, stop and record a
   handoff request instead of editing it opportunistically.
3. **Work safely:** preserve other chats' changes; do not use broad staging,
   resets, rebases, deletes, or formatting sweeps. JSON and GDScript conflicts
   are resolved by the lane that owns the file, never by hand-merging data.
4. **Verify:** run the focused tests plus the full Python gate, validator,
   dead-content/replay checks, and the relevant Godot/HTTP check. A lane is not
   done because its local test passes; its done clauses and play verification
   must be recorded.
5. **Integrate in dependency order:** M0 → M1 → M2a/M2b → M2c/M2d; M3 rolls
   alongside stable payloads; M4 is serial; M5 is last. Re-tag or rebase only
   when the repository owner explicitly requests it.
6. **End:** update the milestone status and paste a section 9 handoff block with
   changed files, commands, results, open questions, and the exact next starting
   point. Never leave only a prose claim in chat.

The old branch/rebase protocol is historical guidance; the active protocol is
the one above and the write sets in section 8.3.

### 8.5 Do NOT parallelise

- **M0, M1, and the contract checkpoint** — these establish the baseline,
  persistence behavior, and shared transport/view fields. Run them serially.
- **M4/S3 balance** — tuning values interact across combat, encounters, economy,
  and pacing; one owner only.
- **A validator or shared-schema change while another lane is writing** — land
  it in an integration window, not during unrelated feature work.
- **Two chats in one shared checkout** — even with nominally disjoint tasks,
  generated files, replay fixtures, and status documents can collide. Use
  separate branches/worktrees for real parallelism.

### 8.6 Dependency map

```
M0 integrate/rebaseline
  ↓
M1 save continuity + transport contract
  ├─→ M2a L5 narrative ───────────────┐
  ├─→ M2b L7 world/social ──→ M2c L9  │
  │                                  ├─→ M3 rolling Godot parity
  └─→ M2d L10 residual meta ──────────┘
                    │
                    └──────────────→ M4 S3 balance (serial)
                                      ↓
                              M5 L11 release
```

M3 may begin for a panel as soon as its backend payload owner is named; it does
not wait for unrelated engine lanes. M4 waits for the M1 baseline and the M2
gameplay contracts, not for cosmetic UI polish.

### 8.7 How many agents to run

| Agents | Safe plan |
|---|---|
| 1 | M0 → M1 → M2a → M2b → M2c → M3 → M4 → M5, with one panel at a time |
| 2 | One chat owns M0/M1; the second performs read-only review or prepares a separate M2 branch after the contract freeze |
| 3–4 | After M1, M2a and M2b may run in separate branches; one M3 panel chat may run only when its payload owner is fixed |
| 5+ | Separate branches/worktrees only: M2 lanes, one-panel M3 lanes, and documentation can proceed; M4 remains single-owner |
| Shared checkout | One writer at a time; additional agents should wait for an explicit handoff rather than edit concurrently |

**Expected wall-clock shape:** M0/M1 are short but blocking; M2a/M2b are the
first genuinely parallel engine work; M3 is bounded by panel ownership and
payload readiness; M4 is deliberately serial; M5 is a final integration and
certification pass.

## 9. Cross-chat handoff record

Paste one completed block at the end of every feature chat. This is the minimum
context the next chat needs; do not rely on conversational memory.

<!-- CROSS-CHAT-HANDOFF TEMPLATE
Milestone: M0 | M1 | M2a | M2b | M2c | M2d | M3 | M4 | M5
Role:
Start condition:
Write set:
Files changed:
Commands run:
Results:
Play/API/Godot verification:
Decisions or assumptions:
Open questions / blocked work:
Next chat should start at:
-->

### Current next chat

- **Milestone:** M2a — L5 narrative and prose (or M2b — L7 world/social, in a
  separate worktree; the shared checkout stays single-writer).
- **Role:** narrative/data owner (or world/social owner).
- **Start condition:** M1 is integrated and its contract is frozen — do not
  reopen save/API files (`game/utils/rng.py`, `save_service.py`,
  `save_repository.py`, `lifecycle.py`, `api/server.py`) without a handoff.
  Read the M1 completion record above and the live gate table.
- **Write set (M2a):** `game/data/narrative_templates.json`,
  `game/data/lore_glossary.json`, `game/systems/narrative_system.py`,
  `game/core/engine/encounters.py` (prose only),
  `game/validation/narrative_lint.py`, focused narrative tests.
- **Stop condition:** every render path carries prose (N.1, N.3, N.5, E.3),
  voice/repetition/context checks pass, the full gate stays green, and the M2a
  handoff block is pasted here.

### M0 completed handoff (2026-09-25)

- **Milestone:** M0 — integrate and re-baseline.
- **Files changed:** `README.md`, `ROADMAP.md`, `handover.md`, and `TASKS.md`.
- **Files deliberately untouched:** all existing engine/data/Godot/test/tool
  changes, replay fixtures, and the untracked Godot render-check script.
- **Commands run:** `pytest -q -rs`; validator; dead-content report; economy
  report; deterministic playthrough; Godot event/state/panel/smoke checks with
  the available Godot 4.7 binary; `refresh_docs.py --check`; `git diff --check`.
- **Results:** 970 passed, 4 skipped, 1 strict xfail; validator/dead-content/
  economy/playthrough pass; Godot focused checks pass; documentation freshness
  passes.
- **Next chat:** M1 persistence/API owner. Start from the write set in the live
  milestone table and do not broaden scope without a handoff.

---
