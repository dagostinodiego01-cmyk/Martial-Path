# Graph Report - .  (2026-08-14)

## Corpus Check
- Large corpus: 225 files · ~5,744,960 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder.

## Summary
- 1403 nodes · 3489 edges · 79 communities (54 shown, 25 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 128 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- PySide GUI Interface
- CLI & Command Routing
- Inventory & Items
- Lifespan & New Game
- Data Registry & Loading
- Save & Persistence
- RNG & Events
- Stats & Equipment
- Results & EventTypes
- Cultivation Advancement
- Player & Cultivation Tests
- FastAPI Server
- Data Validation
- Skills & Techniques
- Combat & Enemies
- Core Engine & Models
- Shops
- Cultivation State Models
- Breakthrough & Stabilise
- Locations
- Data Validation Tests
- Character Service
- Talent System
- Starting Fate & Talents
- Engine Action Dispatch
- Travel Service
- Engine State Snapshot
- Registry Accessors
- Cultivation Service
- Relationships
- Location Map Tests
- Engine New Game & Fate
- NPC Interaction
- Trainers
- Exploration
- Location System
- Morality
- Cultivation Stat Calc
- Currency Helpers
- Trainer Tests
- Travel Tests
- Combat Flow
- GUI Entrypoint
- Engine Process Action
- Validation Package
- Relationship Tests
- Morality Tests
- Cross-Track Support
- UI Theme
- Import Smoke Tests
- JSON Smoke Tests
- Logging
- Backend Entrypoint
- Lifespan Death
- Technique Manuals
- Content Discovery Docs
- Map & Location Docs
- Result Serialisation
- Pytest Config
- API Package
- Application Layer
- Core Layer
- Game Package
- Models Package
- Player Heal
- Player Vitality
- Player Init
- Qi Restore
- Player Damage
- Persistence Layer
- Services Layer
- Body Progress Query
- Essence Progress Query
- Essence Unlock Query
- Essence Unlock Check
- Systems Layer
- UI Layer
- Utils Layer
- Validation Result Format

## God Nodes (most connected - your core abstractions)
1. `Player` - 209 edges
2. `GameEngine` - 121 edges
3. `CultivationSystem` - 87 edges
4. `GUIInterface` - 65 edges
5. `EventType` - 56 edges
6. `load_json()` - 47 edges
7. `RNG` - 47 edges
8. `validate_all_game_data()` - 43 edges
9. `GameDataRegistry` - 41 edges
10. `CLIInterface` - 36 edges

## Surprising Connections (you probably didn't know these)
- `Martial Path Engine` --references--> `GameEngine`  [EXTRACTED]
  handover.md → game/core/game_engine.py
- `Content Discovery` --references--> `FindSystem`  [EXTRACTED]
  handover.md → game/systems/find_system.py
- `Content Discovery` --references--> `SkillSystem`  [EXTRACTED]
  handover.md → game/systems/skill_system.py
- `Content Discovery` --references--> `TrainerSystem`  [EXTRACTED]
  handover.md → game/systems/trainer_system.py
- `_accept_fate()` --references--> `GameEngine`  [EXTRACTED]
  tests/test_game_engine.py → game/core/game_engine.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Cultivation Progression Subsystem** — game_docs_cultivation_system_body_transformation, game_docs_cultivation_system_essence_gathering, game_docs_cultivation_system_cultivation_strain, game_docs_cultivation_system_foundation_stability, game_docs_cultivation_system_breakthrough_gating, game_docs_cultivation_system_talent_ladder, game_docs_cultivation_system_lifespan [EXTRACTED 1.00]
- **Layered Architecture Layers** — game_docs_architecture_layered_architecture, game_docs_architecture_ui_decoupling, game_docs_architecture_engine_contract, game_docs_architecture_state_ownership, game_docs_architecture_eventtype [EXTRACTED 1.00]
- **Content Discovery Channels** — handover_content_discovery, game_docs_data_schema_rarity_ladder, game_docs_shop_system_currency [INFERRED 0.85]

## Communities (79 total, 25 thin omitted)

### Community 0 - "PySide GUI Interface"
Cohesion: 0.06
Nodes (28): _danger_color(), _esc(), GUIInterface, _HoverButton, Any, _ratio(), Assemble the move list: a basic Strike plus each active technique., A push button that reports hover, so the move menu can show move details. (+20 more)

### Community 1 - "CLI & Command Routing"
Cohesion: 0.06
Nodes (32): CommandRouter, Any, Command router. Maps raw input strings (``"train"``, ``"use healing_pill"``,…, Return the command reference used by the UI to render help., Translates human input into engine actions., Convert a raw input line into a structured command dictionary., Action, Canonical action identifiers produced by the command router. The UI never… (+24 more)

### Community 2 - "Inventory & Items"
Cohesion: 0.05
Nodes (46): Item, Any, Item model. Items are data-driven (see ``data/items.json``). The model holds…, A carryable object. Attributes: id: Stable identifier used in data files and…, Build an item from a raw data-file entry., Return ``True`` if using the item should consume one from the stack., EffectSystem, Any (+38 more)

### Community 3 - "Lifespan & New Game"
Cohesion: 0.05
Nodes (53): Build a fully-loaded engine from the central data registry. ``registry`` may be…, LifespanSystem, Any, Lifespan and ageing rules. Pure and data-driven: computes a character's current…, Compute maximum lifespan, advance age, and detect death by old age., Return the current maximum lifespan in years, or ``None`` if immortal. Lifespan…, Return the age (in years) a given action consumes., Advance the player's age by the action's time cost; return years added. (+45 more)

### Community 4 - "Data Registry & Loading"
Cohesion: 0.06
Nodes (54): _load_optional_collection(), _load_optional_object(), Central registry of all static game data. One validated source of truth for the…, Load a JSON object file, returning ``{}`` when it does not exist yet., Load a list collection, returning ``[]`` when the file/folder is absent., load_collection(), load_json(), Any (+46 more)

### Community 5 - "Save & Persistence"
Cohesion: 0.06
Nodes (37): Exception, Cultivation Save Shape, Save Version, Any, Path, Save repository -- low-level persistence for save slots. Owns *where* saves…, Reads and writes raw JSON save slots on disk., The directory save slots are stored in. (+29 more)

### Community 6 - "RNG & Events"
Cohesion: 0.08
Nodes (30): EventSystem, Any, Produces weighted random encounters from data-driven, location-scoped pools., Pick and return the next exploration encounter descriptor.…, FindSystem, Any, Rarity-weighted exploration finds. Chooses what the player stumbles upon while…, Weighted, danger-gated selection over the findable item/equipment catalog. (+22 more)

### Community 7 - "Stats & Equipment"
Cohesion: 0.09
Nodes (28): Effective Stats / Passive Skills, Derived Equipment Stats, Equipment Slots, EquipmentSystem, Any, Validates equipment actions and aggregates equipped modifiers., Any, Derives effective stats from base stats and passive skills. (+20 more)

### Community 8 - "Results & EventTypes"
Cohesion: 0.10
Nodes (40): EventType, Discriminators attached to every structured result the engine returns. The UI…, CharacterEncounterResult, CharacterInteractionResult, ErrorResult, HelpResult, MeditateResult, MessageResult (+32 more)

### Community 9 - "Cultivation Advancement"
Cohesion: 0.11
Nodes (11): CultivationSystem, Any, Handles independent body and essence cultivation tracks., Return the next Body Transformation realm definition, if any., Advance Essence Gathering within the current realm when possible., Advance Essence Gathering to the next reachable realm when possible., Return the body track display name with sequence context., Backward-compatible default training action: train the body track. (+3 more)

### Community 10 - "Player & Cultivation Tests"
Cohesion: 0.16
Nodes (37): Player, The player-controlled cultivator., MonkeyPatch, _make_system(), Tests for the cultivation system's training and breakthrough rules., Advance the body past Pulse Condensation so Essence Gathering is active., test_body_breakthrough_does_not_advance_essence(), test_body_training_diminishing_returns_in_same_day() (+29 more)

### Community 11 - "FastAPI Server"
Cohesion: 0.12
Nodes (33): BaseModel, ActionRequest, get_state(), health(), list_saves(), load_game(), new_game(), NewGameRequest (+25 more)

### Community 12 - "Data Validation"
Cohesion: 0.15
Nodes (31): _check_level(), _check_loot(), _check_map_position(), _connections(), _id_set(), Any, Central data validation. Loads the :class:`GameDataRegistry` and checks the…, _validate_body_progression_config() (+23 more)

### Community 13 - "Skills & Techniques"
Cohesion: 0.10
Nodes (22): Outcome of learning a technique (from a manual or a trainer)., SkillLearnedResult, Any, Skill model. Skills are fully data-driven (see ``data/skills.json``). The model…, A cultivation technique. Attributes: id: Stable identifier used in data files…, Build a skill from a raw data-file entry., Return ``True`` if the skill must be invoked (vs. passive)., Skill (+14 more)

### Community 14 - "Combat & Enemies"
Cohesion: 0.14
Nodes (17): Enemy, Any, Return ``True`` while the enemy still has HP., Apply ``amount`` damage (clamped at 0 HP) and return damage dealt., Return a UI-safe snapshot of the enemy's visible stats., CombatSystem, Any, Effective player defense (passive buffs included) when a stats system is set. (+9 more)

### Community 15 - "Core Engine & Models"
Cohesion: 0.11
Nodes (16): Shared constants used across every layer. Centralizing action names and…, Central game engine — the heart of the CORE layer. The engine owns game state,…, BreakthroughResult, Pure cultivation state models. These dataclasses hold persistent cultivation…, Structured result for a cultivation breakthrough attempt., Enemy model. Enemy templates are data-driven (see ``data/enemies.json``). Each…, Player model. Holds the player's persistent state and offers small, self-…, Service facade for cultivation operations. The service coordinates player… (+8 more)

### Community 16 - "Shops"
Cohesion: 0.17
Nodes (14): Any, Lists location shop stock and resolves item purchases., Return summary data for shops available at a location., Return the current shop stock visible to the player., Buy an item from an available shop, spending currency and adding inventory., ShopSystem, _items(), Tests for data-driven shops and purchase validation. (+6 more)

### Community 17 - "Cultivation State Models"
Cohesion: 0.10
Nodes (15): BodyCultivationState, CultivationState, EssenceCultivationState, Any, Combined cultivation state for a character., Persistent state for the Body Transformation path., Persistent state for the Essence Gathering path., empty_equipment_slots() (+7 more)

### Community 18 - "Breakthrough & Stabilise"
Cohesion: 0.16
Nodes (6): Advance only Essence Gathering progress., Attempt a Body Transformation breakthrough without touching essence progress., Attempt an Essence Gathering breakthrough without touching body progress., Reduce body cultivation strain and restore foundation stability., Reduce Essence Gathering strain and restore essence foundation stability., Return the essence track display name with substage/fall context.

### Community 19 - "Locations"
Cohesion: 0.12
Nodes (14): danger_label(), LocationSystem, Any, Return ``True`` when ``to_id`` is a direct neighbour of ``from_id``., Return a UI-safe snapshot of a location and its exits., Map a numeric ``danger_level`` (0-10) to a display word., Data-driven world map: lookup, adjacency, and UI views., Return ``True`` when ``location_id`` is a known place. (+6 more)

### Community 20 - "Data Validation Tests"
Cohesion: 0.20
Nodes (21): Load every content collection from the ``data/`` directory., Validate every static content collection and return the collected result., validate_all_game_data(), End-to-end validation of the shipped game data. The first test is the real…, test_all_shipped_game_data_is_valid(), test_detects_bad_npc_reference_on_location(), test_detects_dangling_location_connection(), test_detects_duplicate_item_id() (+13 more)

### Community 21 - "Character Service"
Cohesion: 0.18
Nodes (10): CharacterService, Any, Gate by unlock stage. Realm names use a narrative scheme distinct from…, Answers NPC availability, dialogue-context, and interaction questions., Return the raw character definition (or ``None``)., Return UI-safe briefs for the NPCs anchored to ``location_id``., Return the interaction tier and behaviour text for one NPC., Return everything a dialogue/AI layer needs to voice this NPC now. (+2 more)

### Community 22 - "Talent System"
Cohesion: 0.13
Nodes (17): Any, Talent tier ladder lookups. The talent ladder is a data-driven, two-track…, Resolve entries from the two-track talent tier ladder., Return UI-safe views for every ladder entry, ordered by tier index., Return the UI-safe view for a tier index, or ``None`` when unknown., Return the UI-safe view for a stable ladder ID, or ``None`` when unknown., TalentSystem, _make_system() (+9 more)

### Community 23 - "Starting Fate & Talents"
Cohesion: 0.15
Nodes (14): Body Transformation Track, Breakthrough Gating, Cultivation Strain, Essence Gathering Track, Foundation Stability, Lifespan, Starting Fate, Talent Ladder (+6 more)

### Community 24 - "Engine Action Dispatch"
Cohesion: 0.10
Nodes (8): Exploration-mode actions, keyed by action name. Handlers look attributes up on…, Recover a portion of HP and Qi while safely at rest., Meditate to restore Qi and, sometimes, sharpen comprehension., Move to a connected location if the route and requirements allow it., Notify quests on a successful breakthrough and attach any updates., Use an item in exploration; technique manuals teach their skill instead., Advance the minimal backend day after successful recovery actions., Persist the current session to a named save slot.

### Community 25 - "Travel Service"
Cohesion: 0.19
Nodes (9): Any, Return ``True`` when the player's realm meets ``minimum`` (fail-open on…, Map realm ids and display names (lowercased) to their order value., Validates and performs travel between connected locations., Return the UI-safe view of the player's current location., List neighbours of the current location, flagged reachable or locked., Return ``{"allowed": bool, "reason": str|None}`` for a candidate move., Validate and, if allowed, move the player, returning a structured result. (+1 more)

### Community 26 - "Engine State Snapshot"
Cohesion: 0.17
Nodes (7): Any, Return a UI-safe snapshot of the entire game state., Return UI-safe briefs for the player's skills, incl. live combat state. Read-…, Mode-agnostic actions that never consume a turn., Flag the session as finished and return the quit result., Learn a technique from a location trainer, paying its currency cost., Restore a session from a named save slot, replacing current state.

### Community 27 - "Registry Accessors"
Cohesion: 0.25
Nodes (5): _by_id(), GameDataRegistry, Any, Index a list of ``{"id": ...}`` entries by their id (last write wins)., Immutable snapshot of every static content collection.

### Community 28 - "Cultivation Service"
Cohesion: 0.28
Nodes (3): CultivationService, Any, Coordinates cultivation actions for registered players.

### Community 29 - "Relationships"
Cohesion: 0.23
Nodes (8): Any, Return the NPC's state plus its derived interaction tier., Creates, adjusts, and interprets per-NPC relationship state., Return the NPC's state, creating neutral defaults if it is missing. NPCs never…, Return the interaction tier id a relationship_score falls into., Apply clamped deltas to one NPC's emotional variables., Record a notable player action (and optional memory flag) for an NPC., RelationshipSystem

### Community 30 - "Location Map Tests"
Cohesion: 0.29
Nodes (15): _locations(), _player(), Structural tests for the shipped world map (``data/locations.json``). These…, Directed breadth-first search over ``connected_locations`` edges., _reachable_from(), _registry(), test_all_locations_have_normalized_map_positions(), test_azure_village_bridges_into_the_kingdom() (+7 more)

### Community 31 - "Engine New Game & Fate"
Cohesion: 0.14
Nodes (10): GameEngine, Return ``True`` until the player quits., Set the player's display name (used by character creation in the UI)., Return the player's inventory as UI-safe entries (read-only view)., Coordinates systems, manages state, and processes actions., Roll and immediately apply starting talents for a playable new game., Engine Contract, EventType Contract (+2 more)

### Community 32 - "NPC Interaction"
Cohesion: 0.23
Nodes (11): Character service. Single authority for "who is here, and what can I do with…, Morality system. Interprets a player's morality score into a named band…, Relationship system. Manages per-NPC relationship state stored as ``{npc_id:…, _player(), Tests for the CharacterService coordination layer., _service(), test_available_characters_are_scoped_to_the_location(), test_can_spar_reflects_hooks_and_can_duel_respects_unlock() (+3 more)

### Community 33 - "Trainers"
Cohesion: 0.30
Nodes (6): Any, Lists location trainers and resolves paid technique learning., Return summary data for trainers available at a location., Return a trainer's teachable techniques visible to the player., Learn a technique from an available trainer, spending its currency cost., TrainerSystem

### Community 34 - "Exploration"
Cohesion: 0.15
Nodes (4): Return the enemy's public stats plus a UI-only threat/reward preview., Derive a UI-only threat tier and reward preview for an enemy. This is…, Return the max find rarity index allowed by the current area's danger., Spawn a fresh enemy instance from a template entry.

### Community 35 - "Location System"
Cohesion: 0.23
Nodes (12): qi_density_label(), Location system. Owns the world map: which places exist and how they connect.…, Map a numeric ``qi_density`` (0-10) to a display word., Tests for the data-driven location/world-map system., _system(), test_can_travel_requires_direct_connection(), test_danger_and_qi_labels_map_from_numbers(), test_exists_and_get() (+4 more)

### Community 36 - "Morality"
Cohesion: 0.24
Nodes (8): MoralitySystem, Any, Reads morality bands from data and interprets/adjusts a morality score., Clamp a score into the configured morality range., Return the band definition a score falls into., Return just the band id for a score., Return a structured description of the score's current band., Apply a clamped delta to a morality score and report the new band.

### Community 37 - "Cultivation Stat Calc"
Cohesion: 0.15
Nodes (6): Calculate current Body Transformation stat contribution., Calculate current Essence Gathering stat contribution., Calculate derived stats from both tracks without persisting them., Return balance status from relative realm order., Estimate overall breakthrough safety from foundations and resources., Return a non-mutating breakthrough preview for a UI or API.

### Community 38 - "Currency Helpers"
Cohesion: 0.17
Nodes (12): currency_amount(), normalise_price(), Any, Shared currency helpers. Purchases (shops) and technique tuition (trainers)…, Return only the supported, positive currency amounts from a raw price., Return how much of ``currency`` the player currently holds., Return the missing amount per currency the player cannot afford., Deduct an affordable ``price`` from the player's wallet/inventory. (+4 more)

### Community 39 - "Trainer Tests"
Cohesion: 0.33
Nodes (10): Tests for data-driven skill trainers (technique masters)., _skills(), _system(), test_learn_already_known_skill_is_rejected(), test_learn_spends_currency_and_teaches(), test_learn_unoffered_skill_is_rejected(), test_learn_without_funds_is_rejected(), test_trainer_not_at_location_is_rejected() (+2 more)

### Community 40 - "Travel Tests"
Cohesion: 0.44
Nodes (10): _player(), Tests for the travel service: adjacency, requirement gating, and moves., _service(), test_already_there_is_rejected(), test_available_destinations_flag_reachable_and_locked(), test_body_realm_requirement_allows_when_met(), test_body_realm_requirement_blocks_underleveled_travel(), test_required_item_and_reputation_gate_vault() (+2 more)

### Community 41 - "Combat Flow"
Cohesion: 0.24
Nodes (4): Validate and resolve an active-skill activation in combat., Use an item during combat; this consumes the player's turn., Resolve the consequences of a finished fight and leave combat mode., Defeat is not game over: the player is rescued at a cost.

### Community 42 - "GUI Entrypoint"
Cohesion: 0.27
Nodes (7): main(), Graphical entry point - the composition root for the PySide6 UI. Like…, Construct the Qt application, engine, and window, then run the UI loop., martial_path_icon_path(), PySide6 graphical frontend. This is an alternative UI layer that drives the…, Return the absolute path to the shared Martial Path app icon, if present. The…, Root-level launcher for the graphical (PySide6) UI. Convenience wrapper so the…

### Community 43 - "Engine Process Action"
Cohesion: 0.25
Nodes (4): Process a structured command and return a structured result., Roll and store a pending starting fate for the current new game., Return the current pending fate, rolling one if none exists yet., Apply the pending fate to the player and open normal gameplay.

### Community 44 - "Validation Package"
Cohesion: 0.25
Nodes (5): Central data validation for shipped game content. Public entry point: from…, Result types for data validation. A validation pass collects every problem it…, A single data problem, tagged with a category for grouping/filtering., Record a problem under ``category``., ValidationError

### Community 45 - "Relationship Tests"
Cohesion: 0.43
Nodes (7): Tests for the relationship system's per-NPC state, clamping, and tiers., _system(), test_adjust_clamps_and_reports_applied_delta(), test_ensure_creates_neutral_defaults(), test_relationship_score_can_go_negative_into_hostile(), test_remember_records_each_action_once(), test_tier_progression()

### Community 46 - "Morality Tests"
Cohesion: 0.48
Nodes (6): Tests for the morality system's band interpretation and clamped adjustments., _system(), test_adjust_clamps_to_maximum(), test_adjust_clamps_to_minimum(), test_adjust_reports_actual_change(), test_band_ids_cover_the_full_range()

### Community 48 - "UI Theme"
Cohesion: 0.33
Nodes (5): hex_to_rgb(), hp_color(), Martial Path UI theme - dark charcoal / gold design system. The palette…, Convert a ``#RRGGBB`` string into an ``(r, g, b)`` tuple (0-255)., Return the HP bar colour for a fill ratio (0.0-1.0).

### Community 49 - "Import Smoke Tests"
Cohesion: 0.33
Nodes (5): _module_names(), parametrize, Smoke test: every module under ``game/`` imports cleanly. Catches syntax…, Return the dotted module name for every ``.py`` file under ``game/``., test_game_module_imports()

### Community 50 - "JSON Smoke Tests"
Cohesion: 0.40
Nodes (5): _json_files(), parametrize, Path, Smoke test: every JSON file under ``game/data/`` parses. A single malformed…, test_data_json_parses()

### Community 51 - "Logging"
Cohesion: 0.40
Nodes (4): get_logger(), Developer-facing diagnostic logging. This uses the standard :mod:`logging`…, Return a configured logger for ``name`` (idempotent)., Logger

### Community 52 - "Backend Entrypoint"
Cohesion: 0.40
Nodes (3): _ensure_std_streams(), Standalone entry point for the packaged Martial Path backend. Serves the…, Guarantee ``sys.stdout``/``sys.stderr`` exist. A windowed PyInstaller build…

### Community 55 - "Content Discovery Docs"
Cohesion: 0.50
Nodes (4): Central Validation, Rarity Ladder, Gold / Spirit Stones, Content Discovery

### Community 56 - "Map & Location Docs"
Cohesion: 0.50
Nodes (4): Encounter Pools, Location Schema, Cultivation Gating, Travel Graph

## Knowledge Gaps
- **2 isolated node(s):** `Godot Frontend`, `Martial Path Engine`
  These have ≤1 connection - possible missing edges or undocumented components.
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `GameEngine` connect `Engine New Game & Fate` to `PySide GUI Interface`, `CLI & Command Routing`, `Inventory & Items`, `Lifespan & New Game`, `Save & Persistence`, `RNG & Events`, `Stats & Equipment`, `Results & EventTypes`, `Cultivation Advancement`, `Player & Cultivation Tests`, `FastAPI Server`, `Skills & Techniques`, `Combat & Enemies`, `Core Engine & Models`, `Shops`, `Locations`, `Character Service`, `Talent System`, `Starting Fate & Talents`, `Engine Action Dispatch`, `Travel Service`, `Engine State Snapshot`, `Registry Accessors`, `Cultivation Service`, `Relationships`, `NPC Interaction`, `Trainers`, `Exploration`, `Morality`, `Combat Flow`, `GUI Entrypoint`, `Engine Process Action`, `Lifespan Death`, `Technique Manuals`?**
  _High betweenness centrality (0.361) - this node is a cross-community bridge._
- **Why does `Player` connect `Player & Cultivation Tests` to `Inventory & Items`, `Lifespan & New Game`, `Save & Persistence`, `RNG & Events`, `Stats & Equipment`, `Cultivation Advancement`, `Skills & Techniques`, `Combat & Enemies`, `Core Engine & Models`, `Shops`, `Cultivation State Models`, `Breakthrough & Stabilise`, `Engine State Snapshot`, `Cultivation Service`, `Engine New Game & Fate`, `Trainers`, `Cultivation Stat Calc`, `Currency Helpers`, `Trainer Tests`, `Cross-Track Support`, `Player Heal`, `Player Vitality`, `Player Init`, `Qi Restore`, `Player Damage`, `Body Progress Query`, `Essence Progress Query`, `Essence Unlock Query`, `Essence Unlock Check`?**
  _High betweenness centrality (0.212) - this node is a cross-community bridge._
- **Why does `CultivationSystem` connect `Cultivation Advancement` to `Data Registry & Loading`, `Save & Persistence`, `Cultivation Stat Calc`, `Body Progress Query`, `Results & EventTypes`, `Essence Progress Query`, `Player & Cultivation Tests`, `Essence Unlock Query`, `Essence Unlock Check`, `RNG & Events`, `Core Engine & Models`, `Cross-Track Support`, `Breakthrough & Stabilise`, `Starting Fate & Talents`, `Engine State Snapshot`, `Cultivation Service`, `Engine New Game & Fate`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `Player` (e.g. with `GameEngine` and `CultivationState`) actually correct?**
  _`Player` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 47 inferred relationships involving `GameEngine` (e.g. with `ActionRequest` and `NewGameRequest`) actually correct?**
  _`GameEngine` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `CultivationSystem` (e.g. with `GameEngine` and `CultivationService`) actually correct?**
  _`CultivationSystem` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `GUIInterface` (e.g. with `Action` and `EventType`) actually correct?**
  _`GUIInterface` has 3 INFERRED edges - model-reasoned connections that need verification._