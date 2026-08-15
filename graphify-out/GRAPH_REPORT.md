# Graph Report - .  (2026-08-15)

## Corpus Check
- 112 files · ~5,809,946 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2184 nodes · 5284 edges · 106 communities (84 shown, 22 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 199 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- PySide GUI Interface
- Combat & Enemies
- Travel Service
- Save & Persistence
- Events & Encounters
- Social & Dialogue
- Narrative Engine
- Skills & Techniques
- Dao Combat
- Items & Effects
- CLI Interface
- Shops & Currency
- Data Validation
- Quests & Acts
- Equipment & Skill Models
- Player Model
- Command Routing
- FastAPI Server
- Cultivation Tests
- Engine Integration Tests
- Secret Realms
- Stats System
- Character Service
- Engine Combat Mixin
- Engine Lifecycle Mixin
- Engine Exploration Mixin
- Engine Systems Mixin
- Sects
- Action Constants
- Data Registry
- Alchemy Gather & Refine
- Equipment System
- Lifespan
- Meta Service
- Validation Tests
- Morality
- Talent System
- Combat Tests
- Sell System
- Seed Tools
- Result Types
- Data Loading & Reachability
- Starting Fate
- Engine Dispatch Mixin
- Cultivation Support Calc
- Insight Combat Tests
- Engine Views Mixin
- Relationships
- World Map Tests
- Save/Time/Equipment Tests
- Engine Progression Mixin
- Origins
- Data Load Tests
- Cultivation State Models
- Cultivation Service
- Cultivation Advancement
- Breakthrough Requirements
- Validation Result Types
- Cultivation System
- Character Service Tests
- GameEngine
- Relationship Tests
- Cultivation Stat Calc
- Alchemy Seed Tool
- Character Data Tests
- Alchemy Tests
- Data Uniqueness Tests
- Roguelike Meta Tests
- Equipment Slot Tests
- Cultivation Training
- Boon & Map Tests
- Essence Cultivation
- Act One Tests
- Talent Tests
- Location Art Tool
- Equipment Seed Tool
- UI Theme
- Roadmap Epics & Phases
- Import Smoke Tests
- JSON Smoke Tests
- Talent Seed Tool
- Stabilise Tests
- Logging
- Backend Entrypoint
- Result Serialisation
- Enemy Abilities Seed
- Enemy Daos Seed
- Equipment Sets Seed
- Pytest Config
- API Package
- Application Package
- Engine Package
- Core Package
- Game Package
- Models Package
- Persistence Package
- Services Package
- Systems Package
- UI Package
- Utils Package
- Map Position Validation
- Enemy Ability Validation
- Living World Epic (future)
- Phase 2 (future)
- Phase 3 (future)
- Phase 4 (future)

## God Nodes (most connected - your core abstractions)
1. `Player` - 286 edges
2. `EventType` - 99 edges
3. `CultivationSystem` - 87 edges
4. `GameEngine` - 77 edges
5. `GUIInterface` - 76 edges
6. `GameDataRegistry` - 70 edges
7. `CombatSystem` - 61 edges
8. `validate_all_game_data()` - 57 edges
9. `CLIInterface` - 48 edges
10. `Enemy` - 45 edges

## Surprising Connections (you probably didn't know these)
- `Epic A: Procedural Narrative Engine` --implements--> `NarrativeSystem`  [INFERRED]
  ROADMAP.md → game/systems/narrative_system.py
- `Epic D: Campaign + Endless Post-game` --implements--> `SecretRealmSystem`  [INFERRED]
  ROADMAP.md → game/systems/secret_realm_system.py
- `Epic C: Roguelike Legacy & Meta` --implements--> `MetaService`  [INFERRED]
  ROADMAP.md → game/services/meta_service.py
- `Epic B: Dao & Philosophy Combat` --references--> `CombatSystem`  [INFERRED]
  ROADMAP.md → game/systems/combat_system.py
- `Epic B: Dao & Philosophy Combat` --implements--> `DaoSystem`  [INFERRED]
  ROADMAP.md → game/systems/dao_system.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Phase 1 MVP systems (implemented)** — game_systems_narrative_system_narrativesystem, game_systems_dao_system_daosystem, game_services_meta_service_metaservice, game_systems_origin_system_originsystem, game_systems_secret_realm_system_secretrealmsystem, game_systems_alchemy_system_gathersystem, game_systems_alchemy_system_refinesystem [EXTRACTED 1.00]
- **Cultivation Progression Subsystem** — game_docs_cultivation_system_body_transformation, game_docs_cultivation_system_essence_gathering, game_docs_cultivation_system_cultivation_strain, game_docs_cultivation_system_foundation_stability, game_docs_cultivation_system_breakthrough_gating, game_docs_cultivation_system_talent_ladder, game_docs_cultivation_system_lifespan [EXTRACTED 1.00]
- **Layered Architecture Layers** — game_docs_architecture_layered_architecture, game_docs_architecture_ui_decoupling, game_docs_architecture_engine_contract, game_docs_architecture_state_ownership, game_docs_architecture_eventtype [EXTRACTED 1.00]

## Communities (106 total, 22 thin omitted)

### Community 0 - "PySide GUI Interface"
Cohesion: 0.06
Nodes (34): main(), Graphical entry point - the composition root for the PySide6 UI. Like…, Construct the Qt application, engine, and window, then run the UI loop., _danger_color(), _esc(), GUIInterface, _HoverButton, martial_path_icon_path() (+26 more)

### Community 1 - "Combat & Enemies"
Cohesion: 0.07
Nodes (40): Enemy, Return ``True`` while the enemy still has HP., Apply ``amount`` damage (clamped at 0 HP) and return damage dealt., CombatSystem, Any, Resolve just the enemy's turn (used after the player uses an item)., Attempt to escape; a failed attempt gives the enemy a free strike., Apply ``skill``'s effect and return the turn events describing it. (+32 more)

### Community 2 - "Travel Service"
Cohesion: 0.05
Nodes (49): Encounter Pools, Location Schema, Cultivation Gating, Travel Graph, Any, Return ``True`` when the player's realm meets ``minimum`` (fail-open on…, Map realm ids and display names (lowercased) to their order value., Validates and performs travel between connected locations. (+41 more)

### Community 3 - "Save & Persistence"
Cohesion: 0.06
Nodes (37): Exception, Cultivation Save Shape, Save Version, Any, Path, Save repository -- low-level persistence for save slots. Owns *where* saves…, Reads and writes raw JSON save slots on disk., The directory save slots are stored in. (+29 more)

### Community 4 - "Events & Encounters"
Cohesion: 0.08
Nodes (32): EventSystem, Any, Event system. Generates random exploration encounters. It only *selects*…, Produces weighted random encounters from data-driven, location-scoped pools., Pick and return the next exploration encounter descriptor.…, FindSystem, Any, Rarity-weighted exploration finds. Chooses what the player stumbles upon while… (+24 more)

### Community 5 - "Social & Dialogue"
Cohesion: 0.08
Nodes (46): EventType, Discriminators attached to every structured result the engine returns. The UI…, Run lifecycle: starting fate, permadeath, and save/load persistence., Cultivation, talents, closed-door seclusion, and time advancement., Any, NPC interaction: talk, dialogue choices, boons, and character combat., Relationship-gated NPC verbs and the spar/duel entry points., Apply a chosen dialogue option's relationship/morality/reputation deltas. (+38 more)

### Community 6 - "Narrative Engine"
Cohesion: 0.07
Nodes (32): NarrativeSystem, Any, RNG, Narrative system. A deterministic, data-driven prose engine. Templates live in…, Return ``True`` when every predicate in ``when`` holds against ``context``., Substitute ``{slot}`` placeholders, leaving unknown slots verbatim., Prose for a location, varying by danger and season (stable per place)., Prose for an NPC, varying by relationship tier and morality band. (+24 more)

### Community 7 - "Skills & Techniques"
Cohesion: 0.08
Nodes (34): Any, Build a skill from a raw data-file entry., Any, Validates and records the techniques a player has learned., Return ``True`` if the player already knows the technique., Teach ``skill_id`` to the player if it is valid and not yet known. ``source``…, Apply a newly learned passive's one-time effect to the player. Active skills…, SkillSystem (+26 more)

### Community 8 - "Dao Combat"
Cohesion: 0.09
Nodes (31): Any, Spawn a fresh enemy instance from a template entry., Return a UI-safe snapshot of the enemy's visible stats., RNG, DaoSystem, Any, Return the signed realm gap and each side's stat multiplier (1.0 = none)., ``True`` when the player outranks the enemy enough that it yields. (+23 more)

### Community 9 - "Items & Effects"
Cohesion: 0.07
Nodes (32): EffectSystem, RNG, Item, Item model. Items are data-driven (see ``data/items.json``). The model holds…, A carryable object. Attributes: id: Stable identifier used in data files and…, Return ``True`` if using the item should consume one from the stack., EffectSystem, Any (+24 more)

### Community 10 - "CLI Interface"
Cohesion: 0.13
Nodes (7): Layered Architecture, UI Decoupling, CLIInterface, Any, Renders the game to a terminal and forwards input to the engine., The single output primitive for the whole application., Run the interactive game loop until the player quits.

### Community 11 - "Shops & Currency"
Cohesion: 0.09
Nodes (28): Gold / Spirit Stones, currency_amount(), normalise_price(), Any, Shared currency helpers. Purchases (shops) and technique tuition (trainers)…, Return only the supported, positive currency amounts from a raw price., Return how much of ``currency`` the player currently holds., Return the missing amount per currency the player cannot afford. (+20 more)

### Community 12 - "Data Validation"
Cohesion: 0.12
Nodes (43): _check_level(), _check_loot(), _check_map_position(), _connections(), _id_set(), Any, Central data validation. Loads the :class:`GameDataRegistry` and checks the…, Check relationship/morality gates and relationship rewards reference real… (+35 more)

### Community 13 - "Quests & Acts"
Cohesion: 0.08
Nodes (26): Any, Build an item from a raw data-file entry., Any, QuestSystem, Return a UI-safe list of every known quest and its progress., Return how many quests have been completed (used by the run summary)., Return ``True`` when any active quest has an objective of ``event_type``., Return ``True`` when a quest with an ``event_type`` objective is done. (+18 more)

### Community 14 - "Equipment & Skill Models"
Cohesion: 0.08
Nodes (23): Central game engine — the heart of the CORE layer. The engine owns game state,…, Pure cultivation state models. These dataclasses hold persistent cultivation…, Enemy model. Enemy templates are data-driven (see ``data/enemies.json``). Each…, empty_equipment_slots(), _equipment_from_save(), Player model. Holds the player's persistent state and offers small, self-…, Skill model. Skills are fully data-driven (see ``data/skills.json``). The model…, A cultivation technique. Attributes: id: Stable identifier used in data files… (+15 more)

### Community 15 - "Player Model"
Cohesion: 0.09
Nodes (31): Player, Any, Keep legacy single-progress construction aligned with body progress., Return ``True`` while the player still has HP., Apply ``amount`` damage (clamped at 0 HP) and return damage dealt., Restore up to ``amount`` HP (clamped at max) and return HP recovered., Restore up to ``amount`` Qi (clamped at max) and return Qi recovered., Return a fallback display title for the current cultivation state. (+23 more)

### Community 16 - "Command Routing"
Cohesion: 0.10
Nodes (25): CommandRouter, Any, Command router. Maps raw input strings (``"train"``, ``"use healing_pill"``,…, Convert a raw input line into a structured command dictionary., Translates human input into engine actions., Return the command reference used by the UI to render help., main(), Entry point — the composition root. ``main`` wires the layers together and… (+17 more)

### Community 17 - "FastAPI Server"
Cohesion: 0.12
Nodes (36): BaseModel, ActionRequest, get_meta(), get_state(), health(), list_saves(), load_game(), new_game() (+28 more)

### Community 18 - "Cultivation Tests"
Cohesion: 0.12
Nodes (36): MonkeyPatch, _make_system(), Tests for the cultivation system's training and breakthrough rules., Advance the body past Pulse Condensation so Essence Gathering is active., test_body_breakthrough_does_not_advance_essence(), test_body_training_diminishing_returns_in_same_day(), test_body_training_does_not_grant_permanent_strength(), test_breakthrough_requires_full_progress() (+28 more)

### Community 19 - "Engine Integration Tests"
Cohesion: 0.10
Nodes (34): Build a fully-loaded engine from the central data registry. ``registry`` may be…, Smoke tests for the game engine's UI-agnostic contract., test_buy_then_sell_round_trip_recovers_partial_gold(), test_defeat_penalty_is_partial_and_data_driven(), test_dialogue_choose_mutates_social_state(), test_duel_character_respects_unlock_gate(), test_enemy_view_includes_threat_and_reward_preview(), test_engine_equipment_cultivation_modifier_affects_training() (+26 more)

### Community 20 - "Secret Realms"
Cohesion: 0.08
Nodes (23): Any, Procedural secret realm (seeded dungeon) generator. A secret realm is a…, Fisher-Yates shuffle through the run's RNG (deterministic per seed)., Seeded room generation for a catalogue of hand-placed realms., How many realms are defined (regardless of location)., Every realm id in the catalogue., Return ``True`` when a realm opens at ``location_id``., Return the realm definition that opens at ``location_id``, if any. (+15 more)

### Community 21 - "Stats System"
Cohesion: 0.11
Nodes (22): Effective Stats / Passive Skills, Derived Equipment Stats, Equipment Slots, Any, Return a skill's qi cost after ``qi_cost_reduction`` passives., Derives effective stats from base stats and passive skills., Product of every learned passive's scaling for ``effect`` (1.0 if none)., Sum of every learned passive's scaling for ``effect`` (0 if none). (+14 more)

### Community 22 - "Character Service"
Cohesion: 0.13
Nodes (15): CharacterService, Any, Return a validated, currently-available dialogue choice, or ``None``. The…, Return the first unclaimed relationship reward whose gate is met. Rewards live…, Convenience predicate: is a relationship reward currently claimable?, Return whether a dialogue choice's ``requires`` gate is met., Answers NPC availability, dialogue-context, and interaction questions., Gate by unlock stage. Realm names use a narrative scheme distinct from… (+7 more)

### Community 23 - "Engine Combat Mixin"
Cohesion: 0.11
Nodes (16): CombatMixin, Any, The combat turn loop and its cleanup/penalty helpers., Resolve the consequences of a finished fight and leave combat mode., A friendly spar ends with no loot or progress loss; the loser is patched up., Defeat is not game over: the player is rescued at a data-driven cost., Validate and resolve an active-skill activation in combat., Use an item during combat; this consumes the player's turn. (+8 more)

### Community 24 - "Engine Lifecycle Mixin"
Cohesion: 0.11
Nodes (15): LifecycleMixin, Any, Roll and immediately apply starting talents for a playable new game., Return the current pending fate, rolling one if none exists yet., Apply the pending fate to the player and open normal gameplay., Persist the current session to a named save slot., Return the current session as a portable JSON string (cloud substitute)., Restore a session from a portable JSON string into ``slot``. (+7 more)

### Community 25 - "Engine Exploration Mixin"
Cohesion: 0.11
Nodes (14): ExplorationMixin, Any, Return the enemy's public stats plus a UI-only threat/reward preview., Derive a UI-only threat tier and reward preview for an enemy. This is…, Exploration and movement verbs plus the enemy/encounter view models., Return the max find rarity index allowed by the current area's danger., Build the standard prose context (realm rank, morality, season, ...)., State-aware prose for an NPC (varying by relationship + morality). (+6 more)

### Community 26 - "Engine Systems Mixin"
Cohesion: 0.10
Nodes (16): Any, The newer MVP systems: alchemy, Dao awakening, tournament, secret realm., Actions that wrap the alchemy, Dao, tournament, and secret-realm systems., The seeded named foe that champions the tournament at this location., Tournaments are held where sects gather (academies, sect halls, arenas)., Open the secret realm at the current location (if one opens here)., Step into the next room of the active realm, resolving its kind., Harvest a herb at the current location (gated by its herb table). (+8 more)

### Community 27 - "Sects"
Cohesion: 0.17
Nodes (17): Any, Lists location sects and resolves joining them., Return summaries for the sects available at a location., Return one sect's details plus the player's join status., Return ``{allowed, reason}`` for joining ``sect_id`` right now., Join a sect: assign ``player.path`` and report the starting rank., SectSystem, _player() (+9 more)

### Community 28 - "Action Constants"
Cohesion: 0.09
Nodes (17): Action, Shared constants used across every layer. Centralizing action names and…, Canonical action identifiers produced by the command router. The UI never…, Combat-mode routing and end-of-combat resolution., Economy and gear: buy/sell, equip, repair, use, learn, and join a sect., UI-safe state snapshots and view models., EventType Contract, Alchemy loop: gathering herbs and refining them into pills/elixirs. Two pure… (+9 more)

### Community 29 - "Data Registry"
Cohesion: 0.17
Nodes (8): _by_id(), GameDataRegistry, Any, Return the ids of every auto-generated technique-manual item. One manual is…, Index a list of ``{"id": ...}`` entries by their id (last write wins)., Immutable snapshot of every static content collection., Central Validation, Rarity Ladder

### Community 30 - "Alchemy Gather & Refine"
Cohesion: 0.13
Nodes (13): GatherSystem, Any, Consume a recipe's inputs and produce its output item., Return a non-empty error dict when the player's realm is too low., Per-location herb tables with a seeded weighted roll., Return ``True`` when herbs can be gathered at ``location_id``., Return the weighted herb table for a location (falling back to default)., Return a single gathered herb id from the location's table, or ``None``. (+5 more)

### Community 31 - "Equipment System"
Cohesion: 0.19
Nodes (7): EquipmentSystem, Any, Fold in the strongest met set-bonus threshold for each equipped set., Validates equipment actions and aggregates equipped modifiers., Return the item's durability ceiling, or 0 when it has no durability model., Reduce each equipped destructible item's durability by ``amount``. Returns…, Restore a piece of equipped, destructible gear to full durability for gold.…

### Community 32 - "Lifespan"
Cohesion: 0.12
Nodes (14): Lifespan, Starting Fate, Talent Ladder, LifespanSystem, Any, Return the current season, derived from whole years elapsed since spawn., Compute maximum lifespan, advance age, and detect death by old age., Return the current maximum lifespan in years, or ``None`` if immortal. Lifespan… (+6 more)

### Community 33 - "Meta Service"
Cohesion: 0.14
Nodes (13): MetaService, Any, Path, Return the run chronicle (most recent last)., Return the full meta-save snapshot (memory + chronicle)., Reads and writes the cross-run meta-save., The on-disk meta-save location., Load the meta-save, returning sane defaults when absent/corrupt. (+5 more)

### Community 34 - "Validation Tests"
Cohesion: 0.19
Nodes (22): Load every content collection from the ``data/`` directory., Validate every static content collection and return the collected result., validate_all_game_data(), End-to-end validation of the shipped game data. The first test is the real…, test_all_shipped_game_data_is_valid(), test_detects_bad_npc_reference_on_location(), test_detects_dangling_location_connection(), test_detects_duplicate_item_id() (+14 more)

### Community 35 - "Morality"
Cohesion: 0.15
Nodes (15): MoralitySystem, Any, Morality system. Interprets a player's morality score into a named band…, Reads morality bands from data and interprets/adjusts a morality score., Clamp a score into the configured morality range., Return the band definition a score falls into., Return just the band id for a score., Return a structured description of the score's current band. (+7 more)

### Community 36 - "Talent System"
Cohesion: 0.13
Nodes (17): Any, Talent tier ladder lookups. The talent ladder is a data-driven, two-track…, Resolve entries from the two-track talent tier ladder., Return UI-safe views for every ladder entry, ordered by tier index., Return the UI-safe view for a tier index, or ``None`` when unknown., Return the UI-safe view for a stable ladder ID, or ``None`` when unknown., TalentSystem, _make_system() (+9 more)

### Community 37 - "Combat Tests"
Cohesion: 0.33
Nodes (22): _combat(), _enemy(), _player(), Tests for combat skill-effect resolution and passive stat derivation., _skill(), test_buff_attack_passive_raises_effective_attack(), test_counter_damages_attacker(), test_crit_chance_passive() (+14 more)

### Community 38 - "Sell System"
Cohesion: 0.16
Nodes (16): Any, Sell (liquidation) rules. Converts owned items/equipment/manuals into gold at a…, Validates and performs selling owned items for gold., Return the gold worth of an item (before the sell-rate discount)., Return what one unit of ``item`` sells for in gold (min 1)., Sell ``quantity`` of an owned item for gold; remove it from inventory., SellSystem, _items() (+8 more)

### Community 39 - "Seed Tools"
Cohesion: 0.20
Nodes (20): _load(), main(), Path, Seed the talent-refining resource (``talent_refining_elixir``) into the world.…, seed_enemies(), seed_masters(), seed_pools(), seed_shops() (+12 more)

### Community 40 - "Result Types"
Cohesion: 0.14
Nodes (17): World exploration, movement, enemy spawning, and their prose helpers., ErrorResult, MeditateResult, MessageResult, A successful move, carrying the destination's UI-safe view., A plain informational message., A rejected command, tagged with a stable ``reason`` code., Outcome of resting: HP/Qi recovered and the new totals. (+9 more)

### Community 41 - "Data Loading & Reachability"
Cohesion: 0.11
Nodes (11): _load_optional_collection(), _load_optional_object(), Central registry of all static game data. One validated source of truth for the…, Load a JSON object file, returning ``{}`` when it does not exist yet., Load a list collection, returning ``[]`` when the file/folder is absent., _manual_to_skill(), Every skill must be obtainable through at least one acquisition path. Technique…, Map a manual item id back to its skill id (mirrors engine generation). (+3 more)

### Community 42 - "Starting Fate"
Cohesion: 0.18
Nodes (9): Any, RNG, Roll and view Martial Talent / Body Talent starting data., Roll one Martial Talent and one Body Talent from positive weights., Return a UI-safe Martial Talent data view by stable ID., Return a UI-safe Body Talent data view by stable ID., Return the UI-safe upgrade targets a talent may currently upgrade into.…, Return whether ``target_id`` is a valid upgrade from ``talent_id``. (+1 more)

### Community 43 - "Engine Dispatch Mixin"
Cohesion: 0.17
Nodes (13): DispatchMixin, Any, Action routing: the public ``process_action`` contract and dispatch tables., Flag the session as finished and return the quit result., Routes a structured action to the right handler for the current mode., Process a structured command and return a structured result., Mode-agnostic actions that never consume a turn., Exploration-mode actions, keyed by action name. Handlers look attributes up on… (+5 more)

### Community 44 - "Cultivation Support Calc"
Cohesion: 0.14
Nodes (6): Advance only Essence Gathering progress., Return the current Essence Gathering progress requirement., Body foundation support used by essence training., Essence density support used by body training., Public: has the body cleared Pulse Condensation, opening Essence Gathering?, Return a display string describing what unlocks Essence Gathering. Empty when…

### Community 45 - "Insight Combat Tests"
Cohesion: 0.20
Nodes (18): _combat(), _enemy(), _player(), Tests for the B.5 intent/insight combat resource. Insight builds from…, _skill(), _start_combat_with(), test_all_intent_skills_require_insight_and_are_active(), test_attack_builds_insight_and_emits_insight_events() (+10 more)

### Community 46 - "Engine Views Mixin"
Cohesion: 0.18
Nodes (9): Any, Read-only views the frontends render (no gameplay rules here)., Return a UI-safe snapshot of the entire game state., Return ``True`` until the player quits., Return the cross-run meta view: Ancestral Memory, chronicle, and origins. The…, Set the player's display name (used by character creation in the UI)., Return UI-safe briefs for the player's skills, incl. live combat state. Read-…, Return the player's inventory as UI-safe entries (read-only view). (+1 more)

### Community 47 - "Relationships"
Cohesion: 0.20
Nodes (9): Any, Record a notable player action (and optional memory flag) for an NPC., Return the NPC's state plus its derived interaction tier., Creates, adjusts, and interprets per-NPC relationship state., Return the NPC's state, creating neutral defaults if it is missing. NPCs never…, Return the interaction tier id a relationship_score falls into., Return ``True`` when ``tier_id`` is at least ``minimum`` in tier order. Tier…, Apply clamped deltas to one NPC's emotional variables. (+1 more)

### Community 48 - "World Map Tests"
Cohesion: 0.27
Nodes (17): LocationSystem, _locations(), _player(), Structural tests for the shipped world map (``data/locations.json``). These…, Directed breadth-first search over ``connected_locations`` edges., _reachable_from(), _registry(), test_all_locations_have_normalized_map_positions() (+9 more)

### Community 49 - "Save/Time/Equipment Tests"
Cohesion: 0.12
Nodes (17): _equip_set_pair(), Tests for the medium-priority close-out (P10-P17). Covers: techniques listing,…, test_broken_equipment_provides_no_modifiers(), test_closed_door_cultivation_ages_and_grants_progress(), test_closed_door_rejects_unknown_years(), test_durability_degrades_and_repairs(), test_export_then_import_round_trips_state(), test_ironman_blocks_load() (+9 more)

### Community 50 - "Engine Progression Mixin"
Cohesion: 0.16
Nodes (10): ProgressionMixin, Any, Notify quests on a successful breakthrough and attach narrative prose., Advance the minimal backend day after successful recovery actions., Age the player by an action's time cost and enforce lifespan limits., The verbs that grow the cultivator and advance the calendar., Return the player's known techniques (active + passive)., Return the player's Martial/Body talents and their upgrade paths. (+2 more)

### Community 51 - "Origins"
Cohesion: 0.15
Nodes (10): OriginSystem, Any, Origin system. Starting backgrounds (``data/origins.json``) shape a fresh…, Resolves and applies starting origins., Return every origin definition (in data order)., Return an origin definition, or ``None`` if unknown., Return an origin's Ancestral Memory cost (0 if unknown)., Return the free starting origin (first cost-0 origin, else the first). (+2 more)

### Community 52 - "Data Load Tests"
Cohesion: 0.19
Nodes (15): load_json(), Any, Load and parse a JSON file from the data directory., Tests that data files load and parse as expected., test_body_cultivation_realms_load(), test_body_talents_load(), test_equipment_loads(), test_essence_cultivation_realms_load() (+7 more)

### Community 53 - "Cultivation State Models"
Cohesion: 0.17
Nodes (9): BodyCultivationState, BreakthroughResult, CultivationState, EssenceCultivationState, Any, Combined cultivation state for a character., Structured result for a cultivation breakthrough attempt., Persistent state for the Body Transformation path. (+1 more)

### Community 54 - "Cultivation Service"
Cohesion: 0.28
Nodes (3): CultivationService, Any, Coordinates cultivation actions for registered players.

### Community 55 - "Cultivation Advancement"
Cohesion: 0.20
Nodes (5): Any, RNG, Return the next Body Transformation realm definition, if any., Advance Essence Gathering to the next reachable realm when possible., Backward-compatible default breakthrough action: advance the body track.

### Community 56 - "Breakthrough Requirements"
Cohesion: 0.19
Nodes (4): Attempt a Body Transformation breakthrough without touching essence progress., Reduce body cultivation strain and restore foundation stability., Return the body track display name with sequence context., Return the current Body Transformation progress requirement.

### Community 57 - "Validation Result Types"
Cohesion: 0.15
Nodes (9): Central data validation for shipped game content. Public entry point: from…, Result types for data validation. A validation pass collects every problem it…, A single data problem, tagged with a category for grouping/filtering., The accumulated outcome of a validation pass., Return ``True`` when no problems were recorded., Record a problem under ``category``., Return a human-readable, newline-separated summary of all problems., ValidationError (+1 more)

### Community 58 - "Cultivation System"
Cohesion: 0.23
Nodes (8): Body Transformation Track, Breakthrough Gating, Cultivation Strain, Essence Gathering Track, Foundation Stability, CultivationSystem, Handles independent body and essence cultivation tracks., Validate realm data and optional save-state references.

### Community 59 - "Character Service Tests"
Cohesion: 0.31
Nodes (13): MoralitySystem, _dialogue_service(), _player(), Tests for the CharacterService coordination layer., _service(), test_available_characters_are_scoped_to_the_location(), test_can_spar_reflects_hooks_and_can_duel_respects_unlock(), test_dialogue_choices_are_filtered_by_availability() (+5 more)

### Community 60 - "GameEngine"
Cohesion: 0.21
Nodes (9): GameEngine, Any, Convert a technique-manual entry into a consumable learn-skill item., Auto-generate one learn-skill manual per skill, applying data overrides. Every…, Coordinates systems, manages state, and processes actions. The action handlers…, Engine Contract, Engine State Ownership, GameEngine split into core/engine/ mixins (+1 more)

### Community 61 - "Relationship Tests"
Cohesion: 0.23
Nodes (10): Character service. Single authority for "who is here, and what can I do with…, Relationship system. Manages per-NPC relationship state stored as ``{npc_id:…, Tests for the relationship system's per-NPC state, clamping, and tiers., _system(), test_adjust_clamps_and_reports_applied_delta(), test_ensure_creates_neutral_defaults(), test_meets_min_tier_orders_tiers(), test_relationship_score_can_go_negative_into_hostile() (+2 more)

### Community 62 - "Cultivation Stat Calc"
Cohesion: 0.15
Nodes (6): Calculate current Body Transformation stat contribution., Calculate current Essence Gathering stat contribution., Calculate derived stats from both tracks without persisting them., Return balance status from relative realm order., Estimate overall breakthrough safety from foundations and resources., Return a non-mutating breakthrough preview for a UI or API.

### Community 63 - "Alchemy Seed Tool"
Cohesion: 0.29
Nodes (12): build_gathering(), build_herbs(), build_recipes(), _load_json(), main(), Any, Expand the alchemy + secret-realm content breadth (ROADMAP F.1 / D.2 follow-…, Append new herbs to ``items`` in place; return the updated list. (+4 more)

### Community 64 - "Character Data Tests"
Cohesion: 0.27
Nodes (10): load_collection(), JSON content loading. Loads data files from the sibling ``data/`` directory…, Load a list-collection by logical ``name``. If a directory ``data/<name>/``…, Validation tests for the data-driven NPC roster (data/characters/)., test_all_characters_have_gameplay_hooks(), test_all_characters_have_personality_schema(), test_all_characters_share_starting_region(), test_character_ids_are_unique() (+2 more)

### Community 65 - "Alchemy Tests"
Cohesion: 0.17
Nodes (11): Alchemy loop (ROADMAP F.1): gathering herbs and refining them into pills., test_demonic_herbs_grow_only_in_demon_continent(), test_gather_adds_herb_at_herb_rich_location(), test_gather_rejected_where_no_herbs_grow(), test_herbs_carry_rarity(), test_high_tier_recipe_unavailable_in_menu(), test_recipes_exposed_in_state(), test_refine_consumes_inputs_and_produces_output() (+3 more)

### Community 66 - "Data Uniqueness Tests"
Cohesion: 0.18
Nodes (4): _cultivation_system(), Data-file integrity checks: unique IDs and valid cross-references., test_cultivation_data_is_valid(), test_enemy_loot_references_existing_items()

### Community 67 - "Roguelike Meta Tests"
Cohesion: 0.27
Nodes (11): _meta(), Roguelike legacy & meta (ROADMAP C.1-C.4). Covers the permadeath default + run…, test_chronicle_records_runs_and_stays_bounded(), test_detects_origin_with_unknown_dao(), test_get_meta_state_annotates_affordability(), test_hardcore_death_ends_run_and_banks_meta(), test_memory_adds_and_spends(), test_memory_persists_across_instances() (+3 more)

### Community 68 - "Equipment Slot Tests"
Cohesion: 0.35
Nodes (10): _bind(), _make_system(), Tests for data-driven equipment slots, requirements, and modifiers., test_artifact_slot_compatibility_and_rejection(), test_equip_item_success_does_not_mutate_base_stats(), test_flying_sword_slot_restriction(), test_replacement_overwrites_slot_once(), test_requirement_failure_keeps_equipment_unchanged() (+2 more)

### Community 69 - "Cultivation Training"
Cohesion: 0.20
Nodes (3): Backward-compatible default training action: train the body track., Advance only Body Transformation progress., Product of learned ``cultivation_speed`` passive scalings (1.0 if none).

### Community 70 - "Boon & Map Tests"
Cohesion: 0.33
Nodes (9): _player(), Tests for relationship-gated rewards (boons) and morality-gated interactions.…, _service(), test_engine_map_returns_position_and_destinations(), test_engine_receive_boon_grants_gold_and_claims_once(), test_engine_receive_boon_grants_item(), test_reward_gates_on_morality_band(), test_reward_gates_on_relationship_tier() (+1 more)

### Community 71 - "Essence Cultivation"
Cohesion: 0.22
Nodes (3): Attempt an Essence Gathering breakthrough without touching body progress., Advance Essence Gathering within the current realm when possible., Return the essence track display name with substage/fall context.

### Community 72 - "Act One Tests"
Cohesion: 0.22
Nodes (8): Campaign Act 1 (ROADMAP D.1): quest chain, tournament, and Dao awakening., test_act_one_chain_is_a_real_chain(), test_dao_awakening_is_gated_and_one_shot(), test_dao_view_lists_catalogue_and_current(), test_join_sect_objective_advances_on_join(), test_tournament_objective_completes_on_bout_won(), test_tournament_starts_combat_at_sect_location(), test_tournament_unavailable_in_a_village()

### Community 73 - "Talent Tests"
Cohesion: 0.36
Nodes (6): Starting talent rolls for the Martial and Body cultivation tracks. The system…, _make_system(), Tests for starting talent roll helpers., test_talent_views_do_not_expose_roll_weights_or_upgrade_options(), test_weighted_roll_only_returns_rollable_entries(), test_weighted_roll_returns_valid_talent_ids()

### Community 74 - "Location Art Tool"
Cohesion: 0.52
Nodes (6): main(), _pixel(), Path, Generate placeholder art for ``divine_phoenix_mystic_realm``. The handover…, _write_import(), _write_png()

### Community 75 - "Equipment Seed Tool"
Cohesion: 0.48
Nodes (6): dump(), _equipment_price(), load(), main(), Any, Seed additional shops so most regions have a market. Until this script exists,…

### Community 76 - "UI Theme"
Cohesion: 0.33
Nodes (5): hex_to_rgb(), hp_color(), Martial Path UI theme - dark charcoal / gold design system. The palette…, Convert a ``#RRGGBB`` string into an ``(r, g, b)`` tuple (0-255)., Return the HP bar colour for a fill ratio (0.0-1.0).

### Community 77 - "Roadmap Epics & Phases"
Cohesion: 0.33
Nodes (6): Epic G: Balance & Polish, Epic D: Campaign + Endless Post-game, Epic B: Dao & Philosophy Combat, Epic A: Procedural Narrative Engine, Epic C: Roguelike Legacy & Meta, Phase 1 - MVP (core loop sings)

### Community 78 - "Import Smoke Tests"
Cohesion: 0.33
Nodes (5): _module_names(), parametrize, Smoke test: every module under ``game/`` imports cleanly. Catches syntax…, Return the dotted module name for every ``.py`` file under ``game/``., test_game_module_imports()

### Community 79 - "JSON Smoke Tests"
Cohesion: 0.40
Nodes (5): _json_files(), parametrize, Path, Smoke test: every JSON file under ``game/data/`` parses. A single malformed…, test_data_json_parses()

### Community 80 - "Talent Seed Tool"
Cohesion: 0.47
Nodes (5): main(), Path, Seed ``upgrade_options`` into the Martial and Body talent tracks. Each talent…, resource_quantity(), seed()

### Community 81 - "Stabilise Tests"
Cohesion: 0.40
Nodes (4): Outcome of stabilising the body cultivation foundation., StabiliseResult, Reduce Essence Gathering strain and restore essence foundation stability., test_stabilise_result_serialises_event_and_fields()

### Community 82 - "Logging"
Cohesion: 0.40
Nodes (4): get_logger(), Developer-facing diagnostic logging. This uses the standard :mod:`logging`…, Return a configured logger for ``name`` (idempotent)., Logger

### Community 83 - "Backend Entrypoint"
Cohesion: 0.40
Nodes (3): _ensure_std_streams(), Standalone entry point for the packaged Martial Path backend. Serves the…, Guarantee ``sys.stdout``/``sys.stderr`` exist. A windowed PyInstaller build…

## Knowledge Gaps
- **6 isolated node(s):** `Gold / Spirit Stones`, `Phase 2 - Alpha (depth + breadth)`, `Phase 3 - 1.0 (balance + polish)`, `Phase 4 - Endless (stretch)`, `Epic E: Living World Simulation` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `GameEngine` connect `GameEngine` to `PySide GUI Interface`, `Combat & Enemies`, `Save & Persistence`, `Social & Dialogue`, `Narrative Engine`, `Skills & Techniques`, `Dao Combat`, `Items & Effects`, `CLI Interface`, `Quests & Acts`, `Equipment & Skill Models`, `Player Model`, `Command Routing`, `FastAPI Server`, `Engine Integration Tests`, `Secret Realms`, `Stats System`, `Character Service`, `Engine Combat Mixin`, `Engine Lifecycle Mixin`, `Engine Exploration Mixin`, `Engine Systems Mixin`, `Sects`, `Action Constants`, `Data Registry`, `Alchemy Gather & Refine`, `Equipment System`, `Lifespan`, `Meta Service`, `Talent System`, `Sell System`, `Starting Fate`, `Engine Dispatch Mixin`, `Insight Combat Tests`, `Engine Views Mixin`, `Relationships`, `Save/Time/Equipment Tests`, `Engine Progression Mixin`, `Origins`, `Cultivation System`, `Character Service Tests`, `Alchemy Tests`, `Roguelike Meta Tests`, `Boon & Map Tests`, `Act One Tests`?**
  _High betweenness centrality (0.234) - this node is a cross-community bridge._
- **Why does `Player` connect `Player Model` to `Combat & Enemies`, `Save & Persistence`, `Events & Encounters`, `Social & Dialogue`, `Skills & Techniques`, `Dao Combat`, `Items & Effects`, `Shops & Currency`, `Quests & Acts`, `Equipment & Skill Models`, `Cultivation Tests`, `Engine Lifecycle Mixin`, `Sects`, `Equipment System`, `Lifespan`, `Combat Tests`, `Sell System`, `Cultivation Support Calc`, `Insight Combat Tests`, `Save/Time/Equipment Tests`, `Cultivation Service`, `Cultivation Advancement`, `Breakthrough Requirements`, `Cultivation System`, `GameEngine`, `Cultivation Stat Calc`, `Equipment Slot Tests`, `Cultivation Training`, `Essence Cultivation`, `Stabilise Tests`?**
  _High betweenness centrality (0.180) - this node is a cross-community bridge._
- **Why does `EventType` connect `Social & Dialogue` to `PySide GUI Interface`, `Combat & Enemies`, `Travel Service`, `Events & Encounters`, `Skills & Techniques`, `Items & Effects`, `CLI Interface`, `Shops & Currency`, `Quests & Acts`, `Equipment & Skill Models`, `Player Model`, `FastAPI Server`, `Cultivation Tests`, `Engine Integration Tests`, `Secret Realms`, `Engine Combat Mixin`, `Engine Lifecycle Mixin`, `Engine Exploration Mixin`, `Engine Systems Mixin`, `Sects`, `Action Constants`, `Alchemy Gather & Refine`, `Equipment System`, `Sell System`, `Result Types`, `Engine Dispatch Mixin`, `Insight Combat Tests`, `Engine Views Mixin`, `Save/Time/Equipment Tests`, `Engine Progression Mixin`, `Cultivation System`, `Alchemy Tests`, `Equipment Slot Tests`, `Boon & Map Tests`, `Act One Tests`, `Stabilise Tests`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Are the 17 inferred relationships involving `Player` (e.g. with `LifecycleMixin` and `GameEngine`) actually correct?**
  _`Player` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 51 inferred relationships involving `EventType` (e.g. with `CombatMixin` and `DispatchMixin`) actually correct?**
  _`EventType` has 51 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `CultivationSystem` (e.g. with `GameEngine` and `CultivationService`) actually correct?**
  _`CultivationSystem` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 41 inferred relationships involving `GameEngine` (e.g. with `ActionRequest` and `NewGameRequest`) actually correct?**
  _`GameEngine` has 41 INFERRED edges - model-reasoned connections that need verification._