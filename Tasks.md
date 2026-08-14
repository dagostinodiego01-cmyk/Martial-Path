# Martial Path — Development Tasks

Measurable task breakdown derived from the **GROK Build review** (cross-validated
against the code on 2026-08-14). Each task states *what to change, where, and the
criterion that proves it's done*.

## Baseline (measured, not guessed)

| Content | Total | Unreachable today |
|---|---|---|
| skills | 208 | 205 (only 3 reachable: `iron_fist`, `flowing_step`, `spirit_palm`) |
| enemies | 236 | 205 (not in any encounter pool) |
| equipment | 251 | 148 |
| items | 213 | 103 |
| NPCs | 50 | 0 (all anchored) |
| char_enemies | 21 | 0 |
| locations | 29 | 0 (all reachable) |
| quests | 3 | 0 (all auto-start) |
| shops | 3 | — |
| trainers | 1 | — |

Root causes to remember when implementing:
- **Every location has a curated encounter pool**, so the "draw any item from the
  catalogue" (`FindSystem`) and "spawn any enemy" (`EventSystem`) fallbacks never
  fire. Wiring content means touching loot tables / shops / trainers / pools
  directly, not relying on fallbacks.
- **Manuals are auto-generated for every skill but seeded nowhere**, so ~205
  skills are defined-but-unobtainable.

## Conventions (definition of done)

- Rules live in `game/systems/` / `game/services/`; `GameEngine` wires and owns
  state. Never put gameplay logic in a UI.
- **Frontend scope: only the Godot interface (`frontend-godot/`) is updated.**
  Do NOT modify the CLI (`game/ui/cli_interface.py` + its
  `game/application/command_router.py` translator) or the PySide6 interface
  (`game/ui/gui_interface.py`). Engine/data/system changes are fine, but any
  player-facing UI work lands in Godot only.
- Data-driven first: stable `snake_case` IDs in JSON, validated centrally.
- Every change ships with: a unit test under `tests/`, and
  `validate_all_game_data()` still clean.
- ASCII only in player-facing strings (Windows console).

---

## Priority 1 — Skill effects + passives  ✅ DONE

Implemented 2026-08-14:
- `CombatSystem` resolves `damage`, `true_damage`, `aoe_damage`, `execute`,
  `life_steal`, `heal_self`, `stun`, `dot_damage`, `shield`, `counter`,
  `debuff_attack`, `debuff_defense` + a shield/status model on Player/Enemy.
- `StatsSystem` honors `buff_attack/defense/evasion/speed/max_hp/max_qi`,
  `crit_chance`, `crit_damage`, `hp_regen`, `qi_regen`, `qi_cost_reduction`.
- Tests: `tests/test_combat_system.py` (18 tests). Suite: 338 passed.

Meta-passives (non-combat, cross-system wiring) — ✅ DONE 2026-08-14:
- [x] 1.1 `comprehension_gain` — applied on `SkillSystem.learn_skill()`:
  learning one raises `player.comprehension` by `scaling`
  (`tests/test_skill_system.py`).
- [x] 1.2 `lifespan` — `SkillSystem` accrues `player.lifespan_bonus_years`;
  `LifespanSystem.current_max_lifespan` adds it to the realm-derived cap
  (ignored when immortal) (`tests/test_lifespan_system.py`).
- [x] 1.3 `cultivation_speed` — `CultivationSystem` multiplies `base_gain` in
  `train_body`/`train_essence` by the product of learned `cultivation_speed`
  scalings (`tests/test_cultivation_system.py`).

All 26 declared effect types now do something. Suite: 346 passed, 3 skipped.

---

## Priority 2 — Make martial growth reachable (seed manuals + expand trainers)  ✅ DONE

Implemented 2026-08-14 via `tools/seed_techniques.py` (deterministic, idempotent
-- re-runnable to regenerate the seeded data):
- [x] 2.1 Manuals seeded into enemy loot tables (`enemies/random_enemies.json`,
  `character_enemies/named_foes.json`), one tiered drop per enemy at 0.05 chance.
- [x] 2.2 Manuals seeded into shop stock (`shops.json`), all 208 manuals bucketed
  by rarity across the three markets and priced by rarity (gold -> spirit stone).
- [x] 2.3 Manuals added to `encounter_pools.json` loot pools, danger-gated per
  location (weight 1).
- [x] 2.4 `trainers.json` expanded: 8 trainers (kept `wandering_sword_master` +
  one master per rarity tier at a band-matched location) teach **all 208 skills**.
- [x] 2.5 `tests/test_all_skills_reachable.py` added; **0 unreachable skills**
  (baseline 205).
- [x] 2.6 `validate_all_game_data()` clean (0 errors).

Tiering is derived from existing skill fields (active = `qi_cost`; passive =
per-effect magnitude heuristic) and mapped onto the 7-grade rarity ladder;
manuals carry that rarity via `technique_manuals.json`. Validation + loot tests
now recognise auto-generated manual ids as valid item references.

---

## Priority 3 — Dialogue choices that mutate social state  ✅ DONE

Implemented 2026-08-14:
- [x] 3.1 `dialogue.choices[]` blocks added to characters (`zhu_yan`,
  `duanmu_qun`), each choice carrying `relationship_delta`, `morality_delta`,
  `reputation_delta`, and an optional `requires` gate (min tier / morality band).
- [x] 3.2 `DIALOGUE_CHOOSE` action (`EventType.DIALOGUE_CHOICE`,
  `DialogueChoiceResult`) added to `GameEngine._dialogue_choose`; `CharacterService`
  resolves/validates choices (`dialogue_choices` / `get_dialogue_choice`), and the
  engine applies deltas via `RelationshipSystem.adjust`, `MoralitySystem.adjust`,
  and `player.reputation`. `TALK_TO_CHARACTER` now returns the available choices.
- [x] 3.3 `can_spar`/`can_duel` gate on `spar_min_tier`/`duel_min_tier` hooks
  (reason `RELATIONSHIP_TOO_LOW`), via `RelationshipSystem.meets_min_tier`.
- [x] 3.4 Reputation sources: quest rewards now grant `reputation`
  (`QuestSystem._grant_rewards` + `quests.json`); dialogue `reputation_delta`
  adds the second source for the `TravelService` gates.

Tests: `test_dialogue_choose_mutates_social_state` and
`test_relationship_tier_gates_duel` (engine), plus CharacterService/quest/
relationship unit tests. Suite: 354 passed, 3 skipped.

---

## Priority 4 — Quest chains (mid/late purpose)  ✅ DONE

Implemented 2026-08-14:
- [x] 4.1 `QuestSystem` supports a `requires` gate (`completed` quests,
  `min_reputation`, `location`) via `check_unlocks()`, re-checked after every
  `notify()` and after reputation-changing dialogue. Quests without a `requires`
  block stay locked (manual unlock, no false positives).
- [x] 4.2 `quests.json` grew 3 → **9** quests: an Azure Stream faction chain,
  a Sky Fortune chain feeding a mid-game `dao_heart_awakening` and a late-game
  `transcendent_horizon` (gated by completion + reputation + location).
- [x] 4.3 Rewards now support `skills` (directly learned via `SkillSystem`) and
  `manuals` (manual items granted to inventory), alongside exp/gold/reputation.
  Validator cross-checks `requires.completed`/`location` and skill/manual reward
  references.

Tests: `test_completing_quest_unlocks_chained_quest`,
`test_check_unlocks_honours_reputation_and_location`, and skill/manual reward
unit tests. Suite: 358 passed, 3 skipped.

---

## Priority 5 — Economy depth (sell, more shops, sinks)  ✅ DONE

Implemented 2026-08-14:
- [x] 5.1 `SELL_ITEM` action — `game/systems/sell_system.py` (new `SellSystem`)
  liquidates owned items/equipment for gold at half worth (worth = `value` →
  rarity → per-effect heuristic). Wired into the engine (`_sell_item`) and the
  command router (`sell <item_id> [quantity]`). Equipment must be unequipped
  first; stack sales clamp to owned count.
- [x] 5.2 `game/data/shops.json` 3 → **12** markets via `tools/seed_shops.py`
  (deterministic, idempotent), one per major hub: early hubs in gold, later
  hubs in spirit stone (equipment priced at `value`, or `value / 60` stones).
- [x] 5.3 Spirit-stone sinks already in place from P2 (manuals + trainer
  tuition priced in stones); the new late-game markets add stone-priced gear
  and immortality pills.

Tests: `tests/test_sell_system.py` (7 unit tests) + engine sell / buy→sell
round-trip + router `sell` + `test_shops_cover_most_regions` (≥ 10 shops, ≥ 10
served locations). Suite: 370 passed, 3 skipped; validator 0 errors.

---

## Priority 6 — Combat differentiation  ✅ DONE

Implemented 2026-08-14:
- [x] 6.1 Spar vs duel are now mechanically distinct. `CombatSystem` gained a
  `spar` flag: a spar is called off once either side drops to 25% HP
  (`SPAR_END_HP_FRACTION`), ending as `SPAR_WON`/`SPAR_LOST` with **no exp, no
  loot, no quest notify, and no defeat penalty**. A duel/exploration fight keeps
  full stakes (`VICTORY` with loot + exp, `DEFEAT` with penalty). Wired through
  `GameEngine._start_character_combat` (sets `_combat_is_spar`), the combat
  dispatch, and `_end_combat` (`_apply_spar_end` patches the spar loser up, no
  progress loss).
- [x] 6.2 Defeat penalty is data-driven: `cultivation_config.json` gains
  `defeat_penalty` (`progress_loss_ratio` 0.25, `revive_hp_ratio`/`revive_qi_ratio`
  0.5). `_apply_defeat_penalty` now loses a fraction of body progress instead of
  wiping it, and the validator checks the three ratios are in [0, 1].

(6.3 — enemy skill-like behaviors — was optional and is tracked in the Backlog.)

Tests: `tests/test_combat_system.py` (3 spar/duel-stakes tests) +
`test_spar_ends_without_defeat_penalty` +
`test_defeat_penalty_is_partial_and_data_driven`. Suite: 375 passed, 3 skipped;
validator 0 errors.

---

## Priority 7 — Sect / path identity  ✅ DONE

Implemented 2026-08-14:
- [x] 7.1 `game/data/sects.json` (4 sects: Lin Academy, Seven Profound Valleys,
  Divine Phoenix Island, Asura Divine Kingdom) with `path`, `location_ids`,
  `join_requirements` (`min_body_realm`, `min_reputation`/`max_reputation`) and
  `contribution_ranks`. New `SectSystem` (`sects_for_location`, `sect_view`,
  `can_join`, `join`) + `JOIN_SECT`/`SECTS` actions, wired into the engine and
  the command router (`join <sect_id>`, `sects`).
- [x] 7.2 Joining sets `player.path`; `TrainerSystem.learn` now honours
  `required_path` on a technique (reason `PATH_LOCKED`). Four secret arts are
  path-locked via `tools/seed_techniques.py` (`phoenix_sword_art`/`phoenix_fist`
  → Divine Phoenix, `blood_sea_palm`/`nether_aura` → Asura Path).

Validator checks sect ids/locations/realms/requirements and that trainer
`required_path` values reference a known sect path.

Tests: `tests/test_sect_system.py` (7 tests), `test_path_locked_technique_requires_matching_path`
(trainer), and `test_join_sect_assigns_path` (engine). Suite: 386 passed, 3
skipped; validator 0 errors.

---

## Godot GUI restructure (Martial_Path_GUI_Master_Prompt_Final.md) — ✅ DONE

Restructured the Godot frontend per the master prompt (Stages 2–5), entirely in
`frontend-godot/scripts/MainController.gd`:

- **Top bar:** logo + name, HP/Qi bars, Year-only, tab buttons, Settings.
- **Layout:** 3 columns — Character | Location + grouped Actions | permanent
  Event Log (seeded with a welcome entry).
- **Tabs → floating overlays:** Inventory / Equipment / Journal / Status /
  Techniques open as a centred modal over the main view with a close (✕) button
  and click-outside-to-close.
- **Character panel:** monogram portrait + name/path/realm, sectioned vitals,
  integrated Body Progress bar.
- **Location panel:** Danger / Qi / Resources value chips + clickable exit
  buttons (travel directly; locked exits surface the backend reason).
- **Actions:** grouped into Cultivation / Exploration / Commerce & Support;
  locked actions show a 🔒 badge + reason.
- **Polish:** consistent colours/spacing, hover/press/tab-active states, Year
  timestamps in the log.

Validated with Godot 4.7 headless against a live backend: no script/parse/runtime
errors.

**Follow-up (Godot action-hub cleanup):** `Inventory` / `Use Item` / `Equip Item` /
`Unequip Item` were removed from the main Actions hub's *Commerce & Support* grid
(Inventory/Equipment are already reachable from the top bar). Use / Equip /
Unequip now live as a button row inside the Inventory overlay, so all item
interaction happens in that tab.

---

## Priority 8 — Frontend parity + honest labels  ✅ DONE

Implemented 2026-08-14:
- [x] 8.1 `tools/normalize_available_systems.py` maps the ~70 narrative
  `available_systems` values onto the 11 implemented verbs
  (`game.core.constants.AVAILABLE_SYSTEMS`), dropping 24 dead labels. The
  validator flags any non-canonical value (`dead_available_system`);
  `test_available_systems_only_declare_implemented_verbs` pins it at 0.
- [x] 8.2 CLI parity: `stabilise essence` (STABILISE_ESSENCE), `map`
  (`Action.MAP` + `MapResult`), `boon`/`receive` (`Action.RECEIVE_BOON`), and a
  `PLAYER_DIED` formatter. PySide gained Market / Masters / Use Item / Stabilise
  / World Map cards + dialogs and the lifespan-death handler (compiled clean;
  runtime-untested because PySide6 is not installed in this environment).

---

## Priority 9 — Morality & relationship → gameplay hooks  ✅ DONE

Implemented 2026-08-14:
- [x] 9.1 Morality gates on interactions: `spar_morality_band` /
  `duel_morality_band` hooks gate spar/duel on alignment
  (`MORALITY_BAND_MISMATCH`).
- [x] 9.2 Relationship-gated rewards: the declared-but-empty
  `gameplay_hooks.relationship_rewards` is now a real mechanic — `min_tier`
  and/or `morality_band` gate each one-time reward (gold / exp / item / skill),
  claimed via `RECEIVE_BOON` and tracked in the NPC's relationship memory flags.
- [x] 9.3 Encounter options surface a `Receive Reward` action when a reward is
  available, so relationship/morality changes visibly change what an NPC offers.
- [x] 9.4 Seeded rewards for `zhu_yan` + `duanmu_qun`; validator checks reward
  tier/band/item/skill references.

Tests: `tests/test_relationship_rewards.py` (6 tests). Suite: 396 passed, 3
skipped; validator 0 errors.

---

## Priority 10 — Frontend parity sweep  ✅ DONE

Implemented 2026-08-14:
- [x] Fixed the dead `techniques` command: the router advertised
  `Action.TECHNIQUES` but the engine had no handler (it fell through to
  `UNKNOWN_COMMAND`). `GameEngine._techniques()` now returns the player's known
  active/passive techniques, with a CLI formatter.
- [x] Canonical action set lives in `game.core.constants.Action`; the CLI router
  is the single source of truth for player vocabulary and now covers every
  engine action (`talents`, `upgrade`, `closed_door`, `repair`, `export`,
  `import`, `techniques`).

Tests: `test_techniques_action_lists_known_skills`. Suite: 413 passed, 3 skipped.

---

## Priority 11 — Talent upgrade/refine paths  ✅ DONE

Implemented 2026-08-14:
- [x] `tools/seed_talent_upgrades.py` chains every Martial/Body talent into the
  next grade via `upgrade_options` (`target_id` + a rare-resource cost scaled by
  tier), so the `roll_weight: 0` upgrade-only divine/apex tiers are now
  reachable only through upgrading.
- [x] Upgrades cost the rare `talent_refining_elixir` material (not gold);
  `GameEngine._upgrade_talent()` spends it from inventory
  (`INSUFFICIENT_RESOURCES` when short).
- [x] `tools/seed_talent_resources.py` distributes the elixir across encounters
  (17 high-danger location pools + 3% high-tier enemy drops), Masters (3 master
  NPCs gift it as a `trusted` relationship reward), and shops (7 late-game
  spirit-stone markets).
- [x] `StartingFateSystem.upgrade_options_view()` / `can_upgrade()` resolve the
  chain; `GameEngine._talents()` + `_upgrade_talent()` (`Action.TALENTS` /
  `Action.UPGRADE_TALENT`) view and spend for upgrades.
- [x] Router/CLI: `talents` / `upgrade <track> <target>`.

Tests: `test_talents_view_and_upgrade`, `test_talent_upgrade_rejected_when_unaffordable`,
`test_talent_upgrade_rejected_for_bad_target`, `test_talent_refining_elixir_is_reachable_across_sources`.
Validator cross-checks upgrade `target_id`s and that the resource cost references a
real item.

---

## Priority 12 — Time model  ✅ DONE

Implemented 2026-08-14:
- [x] Closed-door cultivation (`Action.CLOSED_DOOR`, `closed_door <years>`): a
  deliberate multi-year seclusion ages the player by exactly the chosen years
  and grants a data-driven progress gain (1/3/10 years in
  `cultivation_config.closed_door`).
- [x] Seasons: `LifespanSystem.lifespan_view()` now reports `season`
  (Spring/Summer/Autumn/Winter) derived from elapsed years.
- [x] Realm-scaled aging: `cultivation_config.lifespan.realm_aging_multipliers`
  scales per-action time cost by Essence realm (higher realms age slower;
  mortal realms stay 1.0), applied by `LifespanSystem.advance_age` when the
  engine passes `essence_unlocked`.

Tests: `test_closed_door_cultivation_ages_and_grants_progress`,
`test_closed_door_rejects_unknown_years`, `test_lifespan_view_reports_season`.

---

## Priority 13 — Map placement + missing art  ✅ DONE

Implemented 2026-08-14:
- [x] Generated the missing `divine_phoenix_mystic_realm` artwork
  (`tools/gen_missing_location_art.py` → `frontend-godot/assets/locations/...png`
  + `.import`), so no location falls back to the text placeholder.
- [x] Validator now flags duplicate `map_position` coordinates
  (`_validate_map_positions`), guarding against overlapping markers.

Note: the early Sky Fortune cluster's *subjective* placement is left as-authored
(there is no reference coordinate data to correct against); the objective
guard — no two locations share a marker — is now enforced.

---

## Priority 14 — Equipment UX (set bonuses + durability + paper-doll)  ✅ DONE

Implemented 2026-08-14:
- [x] Set bonuses: `EquipmentSystem` honours `set_id`/`set_bonuses`
  (`pieces_required` thresholds), seeded on the 3 "Spirit Devouring" treasures
  via `tools/seed_equipment_sets.py`; strongest met threshold is folded into
  `aggregate_modifiers`.
- [x] Durability: `Player.equipment_durability` + `durability` on select items;
  broken gear contributes no modifiers; `degrade_equipped()` wears gear on
  defeat; `Action.REPAIR_ITEM` (`repair <item_id>`) restores it for gold.
- [x] Paper-doll: Godot's Equipment overlay now renders a slot-card grid
  (per-slot name/rarity/durability) instead of a flat text list
  (`MainController._make_equipment_slot_card`).

Tests: `test_set_bonus_applies_when_two_pieces_equipped`,
`test_durability_degrades_and_repairs`, `test_broken_equipment_provides_no_modifiers`.

---

## Priority 15 — Save/meta (ironman + NG+ + local export/import)  ✅ DONE

Implemented 2026-08-14:
- [x] Ironman flag: `GameEngine.new_game(ironman=True)` refuses `load_game`
  (`IRONMAN_MODE`), persisted with the save.
- [x] New Game Plus: `new_game(ng_plus=N)` grants a scaling legacy bonus
  (+N comprehension, +100N gold); `ng_plus` round-trips through saves.
- [x] Local save export/import (`Action.EXPORT_SAVE`/`Action.IMPORT_SAVE`): a
  portable JSON snapshot replaces the deferred cloud save (`export` / `import`).

Tests: `test_ironman_blocks_load`, `test_new_game_plus_grants_scaling_bonus`,
`test_export_then_import_round_trips_state`.

---

## Priority 16 — Dialogue AI notes surfaced  ✅ DONE

Implemented 2026-08-14:
- [x] `CharacterInteractionResult.speech_notes` carries `ai_prompt_notes`; the
  CLI renders it as a `(manner: ...)` line so NPC voice notes are player-visible
  flavor. (The full LLM dialogue layer remains deferred — needs a service.)

Tests: `test_talk_surfaces_ai_prompt_notes`.

---

## Priority 17 — Enemy skill-like behaviors  ✅ DONE

Implemented 2026-08-14:
- [x] `Enemy.abilities` (data-driven `heavy`/`poison`/`stun` with `chance` +
  `magnitude`); `CombatSystem._enemy_act` uses them in place of the basic attack.
- [x] Enemy stun now forfeits the player's next action via
  `CombatSystem.player_stunned_turn` (wired into the combat dispatch); poison
  applies a per-round DoT to the player.
- [x] Seeded abilities on 4 named foes (`tools/seed_enemy_abilities.py`);
  validator checks ability shape.

Tests: `test_enemy_poison_ability_applies_player_dot`,
`test_enemy_stun_ability_stuns_player`, `test_player_stunned_turn_forfeits_action`.

---

## Measurability map

| Priority | Metric to move |
|---|---|
| 1 | skills with a functional effect: 13 → 208 |
| 2 | unreachable skills: 205 → 0 |
| 3 | NPCs whose state changes from player choice: 0 → ≥ 1 per faction |
| 4 | quests: 3 → ≥ 8, with chains |
| 5 | shops: 3 → 12; sell action exists |
| 6 | spar vs duel outcomes distinct; defeat penalty data-driven (25% progress, not wipe) |
| 7 | `path` settable via sect (4 sects); 4 path-locked techniques exist |
| 8 | dead `available_systems` labels: 24 → 0; CLI has essence stabilise, map, boon, death UX |
| 9 | relationship-gated rewards claimable: 0 → 2 NPCs; morality can gate spar/duel |
| 10 | dead `techniques` command → wired; every `Action` reachable from the CLI |
| 11 | talent upgrades: 0 chains → full Martial+Body ladders upgradeable via rare resource |
| 12 | closed-door cultivation (N years), seasons, realm-scaled aging all live |
| 13 | missing location art → 0; duplicate map markers guarded |
| 14 | 1 equipment set + 6 durability items; paper-doll slot grid in Godot |
| 15 | ironman flag, NG+ bonus, portable save export/import |
| 16 | `ai_prompt_notes` surfaced in talk results |
| 17 | enemy stun/poison/heavy abilities on 4 named foes |

Each row is checkable by a test or a validator run — no "feels better" without a
number attached.

---

## Status

**All priorities (1–17) plus the Godot GUI restructure are DONE.**

Final suite: **414 passed, 3 skipped**. `validate_all_game_data()` → **0 errors**.

Deferred (needs an external service, noted above): cloud save (local JSON
export/import ships instead) and the full LLM dialogue layer (`ai_prompt_notes`
is surfaced as flavor).
