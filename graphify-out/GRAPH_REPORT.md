# Graph Report - .  (2026-09-04)

## Corpus Check
- 124 files · ~3,041,236 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2518 nodes · 5878 edges · 161 communities (96 shown, 65 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 193 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- GUI Escape Helper Tests
- Combat Round Mechanics
- Travel & Map Gate Tests
- Save & Persistence Tests
- Find & Loot Rarity Tests
- Data Validation Core
- Engine Result Types
- Roadmap & Origins
- Enemy Model & Views
- API Endpoint Tests
- Engine Integration Tests
- Quest System Tests
- Lifespan & Aging Tests
- CLI Interface Loop
- Dao Counter & Pressure Tests
- Cultivation Training Tests
- Run Lifecycle & Retirement
- Seed Tools & Shop Data
- Loot & Inventory Tests
- Secret Realm Tests
- Living World Simulation
- Effective Stats Tests
- Shop System Tests
- Narrative Linter & Voice
- Skill Learning Tests
- Dialogue & Interaction Service
- Project Docs & Registry
- Validator Coverage Tests
- Meta Save & Ancestral Memory
- Engine Advanced Actions
- Sect System Tests
- Equipment Durability & Sets
- Narrative Renderer Tests
- Result Serialization Tests
- Engine Views & Briefs
- Legacy Tree & World Seed Tests
- Cultivation System Internals
- Combat Statuses & Stakes Tests
- Result Contract Tests
- Voice Lint Tests
- Cultivation Actions (Strain/Breakthrough)
- Lifespan System
- Sell System Tests
- Combo Combat Tests
- Talent Ladder Helpers
- Cultivation Speed & Comprehension
- GameEngine Mixins & Wiring
- Command Router Tests
- Narrative Engine (Prose Renderer)
- Starting Fate System
- Engine Actions Tests
- Meta Depth Tests
- Progression Mixin Actions
- World Map Reachability Tests
- Morality & Relationship Validation
- Insight Combat Tests
- Cultivation State Models
- Relationship System
- Talent System
- Morality System & NPC Rules
- Engine Economy & Social Dispatch
- Cultivation Service
- Breakthrough Logic
- Validation Result Infrastructure
- GitHub Skills & UI Rules
- Engine Combat Mixin
- Trainer System Views
- Origins & Softcore Tests
- Character Interaction Tests
- Currency & Wallet
- Alchemy Herbs & Recipes
- Action Contract & Daos Data
- Player Save Round-Trip
- Refine System Tests
- Data Cross-Reference Tests
- Trainer System Tests
- Router Argument Parsing
- Morality System Tests
- State-Aware Prose Descriptions
- Relationship Tier Tests
- Character Data Tests
- Talent Ladder Tests
- CLI Entry Points
- Derived Stats & Risk
- Boon & Gating Tests
- Essence Unlock Logic
- Inventory System
- Named Foes Data Tests
- Talent Roll Tests
- Location Art Generator
- Shop Seeding Tool
- Import Smoke Tests
- JSON Parse Smoke Tests
- Talent Upgrade Seeding
- Diagnostic Logger
- Skill Reachability Tests
- Enemy Ability Tests
- Map & Ability Validators
- Dao System Core
- Result Serialisation Base
- Body Realm Display Names
- Effect System
- Loot Rolling Core
- Enemy Abilities Seeding
- Enemy Dao Seeding
- Equipment Sets Seeding
- Ancient Ruins
- Asura Divine Kingdom
- Azure Stream Village
- Beast Mountain
- Blood Slaughter Steppes
- Central Region Road
- Divine Phoenix Island
- Divine Phoenix Mystic Realm
- Five Element Temples
- Forbidden Back Mountain
- Holy Demon Continent
- Lin Academy
- Misty Gorge
- Nine Furnace Divine Kingdom
- Outer Forest
- Planetary Gate Array
- Rival Divine Kingdom
- Ruined Shrine
- Sky Fortune Capital
- Sky Fortune Road
- South Horizon City
- South Horizon Route
- South Sea Port
- Southern Wilderness
- Sky Fortune Village
- Vermillion Bird Divine Kingdom
- Zenlight Monastery
- API Package Init
- Application Layer Init
- Engine Mixin Package
- Core Layer Package
- Game Package Root
- Models Layer Package
- Persistence Layer Package
- Services Layer Package
- Systems Layer Package
- UI Layer Package
- Utils Layer Package
- Ponytail Lazy-Dev Rules
- Graphify Skill
- Graphify Extraction Spec
- Graphify Query Reference
- Graphify Update Reference
- Ponytail Skill
- Ponytail Audit Skill
- Ponytail Debt Skill
- Ponytail Gain Skill
- Ponytail Help Skill
- Ponytail Review Skill
- Martial Path App Icon
- Seven Profound Valleys Outer Gate
- Seven Profound Valleys Inner Valley
- Path Utilities
- Phase 3 - 1.0 (balance + polish)
- Phase 4 - Endless (stretch)

## God Nodes (most connected - your core abstractions)
1. `Player` - 297 edges
2. `EventType` - 106 edges
3. `CultivationSystem` - 94 edges
4. `GameDataRegistry` - 84 edges
5. `GUIInterface` - 80 edges
6. `GameEngine` - 70 edges
7. `CombatSystem` - 68 edges
8. `validate_all_game_data()` - 63 edges
9. `CLIInterface` - 50 edges
10. `NarrativeSystem` - 45 edges

## Surprising Connections (you probably didn't know these)
- `Architecture Rules (01)` --semantically_similar_to--> `Shared Project Rules`  [INFERRED] [semantically similar]
  .github/instructions/01-architecture.instructions.md → .agents/rules/game-project.md
- `Dialogue System Rules (07)` --references--> `CharacterService`  [EXTRACTED]
  .github/instructions/07-dialogue-system.instructions.md → game/services/character_service.py
- `Data-Driven Design Rules (03)` --references--> `GameDataRegistry`  [EXTRACTED]
  .github/instructions/03-data-driven-design.instructions.md → game/data/registry.py
- `Martial Path Handover` --references--> `CombatSystem`  [INFERRED]
  handover.md → game/systems/combat_system.py
- `Cultivation & Progression Rules (06)` --references--> `CultivationSystem`  [EXTRACTED]
  .github/instructions/06-cultivation-progression.instructions.md → game/systems/cultivation_system.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Agent Fleet Domain Specialization** — agents_orchestrator, agents_commit_gatekeeper, agents_combat_agent, agents_cultivation_agent, agents_world_agent, agents_economy_agent, agents_social_agent, agents_narrative_agent, agents_data_agent, agents_api_agent, agents_godot_agent, agents_test_engineer, agents_architecture_agent [EXTRACTED 1.00]
- **Godot-Only UI Enforcement** — agents_rules_game_project, gh_instr_ui_separation, gh_skill_gui_updates, handover [EXTRACTED 1.00]
- **Location Art Bound to World Data** — frontend_godot_assets_locations_ancient_ruins, frontend_godot_assets_locations_asura_divine_kingdom, frontend_godot_assets_locations_azure_village, frontend_godot_assets_locations_beast_mountain, frontend_godot_assets_locations_blood_slaughter_steppes, frontend_godot_assets_locations_central_region_road, frontend_godot_assets_locations_divine_phoenix_island, frontend_godot_assets_locations_divine_phoenix_mystic_realm, frontend_godot_assets_locations_five_element_temples, frontend_godot_assets_locations_forbidden_back_mountain, game_data_locations [EXTRACTED 1.00]
- **Cultivation Progression Subsystem** — game_docs_cultivation_system_body_transformation, game_docs_cultivation_system_essence_gathering, game_docs_cultivation_system_cultivation_strain, game_docs_cultivation_system_foundation_stability, game_docs_cultivation_system_breakthrough_gating, game_docs_cultivation_system_talent_ladder, game_docs_cultivation_system_lifespan [EXTRACTED 1.00]

## Communities (161 total, 65 thin omitted)

### Community 0 - "GUI Escape Helper Tests"
Cohesion: 0.05
Nodes (40): main(), Graphical entry point - the composition root for the PySide6 UI. Like…, Construct the Qt application, engine, and window, then run the UI loop., _danger_color(), _esc(), GUIInterface, _HoverButton, martial_path_icon_path() (+32 more)

### Community 1 - "Combat Round Mechanics"
Cohesion: 0.07
Nodes (37): CombatSystem, Any, Enemy, Player invokes an active skill, then the enemy retaliates if alive. Qi cost and…, Resolve just the enemy's turn (used after the player uses an item)., Attempt to escape; a failed attempt gives the enemy a free strike., Apply ``skill``'s effect and return the turn events describing it., Resolve a damage-dealing skill hit and return its event. (+29 more)

### Community 2 - "Travel & Map Gate Tests"
Cohesion: 0.06
Nodes (45): Any, Return ``True`` when the player's realm meets ``minimum`` (fail-open on…, Map realm ids and display names (lowercased) to their order value., Validates and performs travel between connected locations., Return the UI-safe view of the player's current location., List neighbours of the current location, flagged reachable or locked., Return ``{"allowed": bool, "reason": str|None}`` for a candidate move., Validate and, if allowed, move the player, returning a structured result. (+37 more)

### Community 3 - "Save & Persistence Tests"
Cohesion: 0.05
Nodes (43): API Agent, Exception, Cultivation Save Shape, Save Version, Any, Path, Save repository -- low-level persistence for save slots. Owns *where* saves…, Reads and writes raw JSON save slots on disk. (+35 more)

### Community 4 - "Find & Loot Rarity Tests"
Cohesion: 0.07
Nodes (34): Encounter Pools, Location Schema, EventSystem, Any, Event system. Generates random exploration encounters. It only *selects*…, Produces weighted random encounters from data-driven, location-scoped pools., Pick and return the next exploration encounter descriptor.…, FindSystem (+26 more)

### Community 5 - "Data Validation Core"
Cohesion: 0.09
Nodes (51): Data Agent, Shared Project Rules, _check_level(), _check_loot(), _check_map_position(), _connections(), _id_set(), Any (+43 more)

### Community 6 - "Engine Result Types"
Cohesion: 0.08
Nodes (43): EventType, Discriminators attached to every structured result the engine returns. The UI…, Run lifecycle: starting fate, permadeath, and save/load persistence., Cultivation, talents, closed-door seclusion, and time advancement., Any, NPC interaction: talk, dialogue choices, boons, and character combat., Relationship-gated NPC verbs and the spar/duel entry points., Apply a chosen dialogue option's relationship/morality/reputation deltas. (+35 more)

### Community 7 - "Roadmap & Origins"
Cohesion: 0.06
Nodes (31): GatherSystem, Any, Consume a recipe's inputs and produce its output item., Return a non-empty error dict when the player's realm is too low., Per-location herb tables with a seeded weighted roll., Return ``True`` when herbs can be gathered at ``location_id``., Return the weighted herb table for a location (falling back to default)., Return a single gathered herb id from the location's table, or ``None``. (+23 more)

### Community 8 - "Enemy Model & Views"
Cohesion: 0.07
Nodes (28): ExplorationMixin, Any, World exploration, movement, enemy spawning, and their prose helpers., Return the enemy's public stats plus a UI-only threat/reward preview., Derive a UI-only threat tier and reward preview for an enemy. This is…, Exploration and movement verbs plus the enemy/encounter view models., Return the max find rarity index allowed by the current area's danger., Build the standard prose context (realm rank, morality, season, ...). (+20 more)

### Community 9 - "API Endpoint Tests"
Cohesion: 0.09
Nodes (43): BaseModel, ActionRequest, get_meta(), get_state(), health(), list_saves(), load_game(), new_game() (+35 more)

### Community 10 - "Engine Integration Tests"
Cohesion: 0.08
Nodes (43): Build a fully-loaded engine from the central data registry. ``registry`` may be…, Campaign Act 1 (ROADMAP D.1): quest chain, tournament, and Dao awakening., test_act_one_chain_is_a_real_chain(), test_dao_awakening_is_gated_and_one_shot(), test_dao_view_lists_catalogue_and_current(), test_join_sect_objective_advances_on_join(), test_tournament_objective_completes_on_bout_won(), test_tournament_starts_combat_at_sect_location() (+35 more)

### Community 11 - "Quest System Tests"
Cohesion: 0.08
Nodes (28): EffectSystem, Any, Build an item from a raw data-file entry., Any, QuestSystem, Return a UI-safe list of every known quest and its progress., Return how many quests have been completed (used by the run summary)., Return ``True`` when any active quest has an objective of ``event_type``. (+20 more)

### Community 12 - "Lifespan & Aging Tests"
Cohesion: 0.09
Nodes (36): Player, Keep legacy single-progress construction aligned with body progress., Return ``True`` while the player still has HP., Apply ``amount`` damage (clamped at 0 HP) and return damage dealt., Restore up to ``amount`` HP (clamped at max) and return HP recovered., Restore up to ``amount`` Qi (clamped at max) and return Qi recovered., The player-controlled cultivator., Reset the player's insight pool and combo chain at the start of a fight. (+28 more)

### Community 13 - "CLI Interface Loop"
Cohesion: 0.14
Nodes (5): CLIInterface, Any, Renders the game to a terminal and forwards input to the engine., The single output primitive for the whole application., Run the interactive game loop until the player quits.

### Community 14 - "Dao Counter & Pressure Tests"
Cohesion: 0.11
Nodes (28): DaoSystem, Any, Return the signed realm gap and each side's stat multiplier (1.0 = none)., ``True`` when the player outranks the enemy enough that it yields., Return the damage multiplier for ``attacker_dao_id`` vs ``defender_dao_id``., Realm-pressure and Dao-counter rules over the dao + realm catalogues., Roadmap B.7: Dao Debates (open), _combat() (+20 more)

### Community 15 - "Cultivation Training Tests"
Cohesion: 0.11
Nodes (39): MonkeyPatch, _make_system(), Tests for the cultivation system's training and breakthrough rules., Advance the body past Pulse Condensation so Essence Gathering is active., test_body_breakthrough_does_not_advance_essence(), test_body_training_diminishing_returns_in_same_day(), test_body_training_does_not_grant_permanent_strength(), test_breakthrough_requires_full_progress() (+31 more)

### Community 16 - "Run Lifecycle & Retirement"
Cohesion: 0.08
Nodes (20): LifecycleMixin, Any, The cosmetic legacy title this run's character carries (C.5)., Buy a legacy-tree unlock with Ancestral Memory (C.5). Cross-run: the purchase…, Apply purchased legacy unlocks to a fresh character (C.5). Runs after origin…, True when the player has crossed the ascension threshold., Ascend: end the run as a *win* and bank the large legacy reward. Retirement is…, Roll and store a pending starting fate for the current new game. (+12 more)

### Community 17 - "Seed Tools & Shop Data"
Cohesion: 0.08
Nodes (22): Economy Agent, World Agent, Shared constants used across every layer. Centralizing action names and…, Combat-mode routing and end-of-combat resolution., Economy and gear: buy/sell, equip, repair, use, learn, and join a sect., The newer MVP systems: alchemy, Dao awakening, tournament, secret realm., UI-safe state snapshots and view models., Central game engine — the heart of the CORE layer. The engine owns game state,… (+14 more)

### Community 18 - "Loot & Inventory Tests"
Cohesion: 0.11
Nodes (25): Item, Item model. Items are data-driven (see ``data/items.json``). The model holds…, A carryable object. Attributes: id: Stable identifier used in data files and…, Return ``True`` if using the item should consume one from the stack., Player model. Holds the player's persistent state and offers small, self-…, EffectSystem, Effect system. Central interpreter for player-facing effects such as healing,…, Applies named effects to a player and reports what changed. (+17 more)

### Community 19 - "Secret Realm Tests"
Cohesion: 0.08
Nodes (23): Any, Procedural secret realm (seeded dungeon) generator. A secret realm is a…, Fisher-Yates shuffle through the run's RNG (deterministic per seed)., Seeded room generation for a catalogue of hand-placed realms., How many realms are defined (regardless of location)., Every realm id in the catalogue., Return ``True`` when a realm opens at ``location_id``., Return the realm definition that opens at ``location_id``, if any. (+15 more)

### Community 20 - "Living World Simulation"
Cohesion: 0.10
Nodes (18): default_world_state(), Any, RNG, Living-world simulation (ROADMAP E.1-E.5). One pure system evolves the world on…, Return the gameplay modifiers for ``season`` (defaults for unknowns)., Advance the world by ``years`` (fractional); return a tick report. The report…, Sect power tracks its living members' ranks, smoothed (E.2). Power is…, Market pressure nudges the price multiplier each tick (E.3). Two bounded… (+10 more)

### Community 21 - "Effective Stats Tests"
Cohesion: 0.11
Nodes (22): Derived Equipment Stats, Equipment Slots, Any, Effective-stats calculation. Computes a player's *effective* combat stats from…, Return a skill's qi cost after ``qi_cost_reduction`` passives., Derives effective stats from base stats and passive skills., Product of every learned passive's scaling for ``effect`` (1.0 if none)., Sum of every learned passive's scaling for ``effect`` (0 if none). (+14 more)

### Community 22 - "Shop System Tests"
Cohesion: 0.13
Nodes (18): Gold / Spirit Stones, Any, Item, The displayed price of a stock entry, scaled by the world's economy band., Lists location shop stock and resolves item purchases., The price multiplier this world's economy band applies., Return summary data for shops available at a location., Return the current shop stock visible to the player. (+10 more)

### Community 23 - "Narrative Linter & Voice"
Cohesion: 0.09
Nodes (28): Narrative Agent, Lore Glossary Data, Central registry of all static game data. One validated source of truth for the…, Voice Guide (Prose Quality Gates), Narrative system. A deterministic, data-driven prose engine. Templates live in…, _lint_brace_artifacts(), _lint_gamey_terms(), _lint_glossary_slots() (+20 more)

### Community 24 - "Skill Learning Tests"
Cohesion: 0.11
Nodes (22): Any, Skill model. Skills are fully data-driven (see ``data/skills.json``). The model…, A cultivation technique. Attributes: id: Stable identifier used in data files…, Build a skill from a raw data-file entry., Return ``True`` if the skill must be invoked (vs. passive)., Skill, Any, Skill (technique) acquisition rules. Owns the single question "can this player… (+14 more)

### Community 25 - "Dialogue & Interaction Service"
Cohesion: 0.14
Nodes (15): CharacterService, Any, Return a validated, currently-available dialogue choice, or ``None``. The…, Return the first unclaimed relationship reward whose gate is met. Rewards live…, Convenience predicate: is a relationship reward currently claimable?, Return whether a dialogue choice's ``requires`` gate is met., Answers NPC availability, dialogue-context, and interaction questions., Gate by unlock stage. Realm names use a narrative scheme distinct from… (+7 more)

### Community 26 - "Project Docs & Registry"
Cohesion: 0.14
Nodes (11): Legacy Tree Data, _by_id(), GameDataRegistry, _load_optional_collection(), Any, Return the ids of every auto-generated technique-manual item. One manual is…, Load a list collection, returning ``[]`` when the file/folder is absent., Index a list of ``{"id": ...}`` entries by their id (last write wins). (+3 more)

### Community 27 - "Validator Coverage Tests"
Cohesion: 0.14
Nodes (28): _load_optional_object(), Load a JSON object file, returning ``{}`` when it does not exist yet., Load every content collection from the ``data/`` directory., Central Validation, Rarity Ladder, Validate every static content collection and return the collected result., validate_all_game_data(), End-to-end validation of the shipped game data. The first test is the real… (+20 more)

### Community 28 - "Meta Save & Ancestral Memory"
Cohesion: 0.13
Nodes (15): MetaService, Any, Append a run record to the chronicle, keeping the most recent only., Return the run chronicle (most recent last)., Return every purchased legacy-tree unlock id., Record an unlock id once; return ``False`` if already owned., Return ``True`` when ``unlock_id`` has been purchased., Flag that at least one run has ended by retirement/ascension (C.7). (+7 more)

### Community 29 - "Engine Advanced Actions"
Cohesion: 0.11
Nodes (15): Any, Actions that wrap the alchemy, Dao, tournament, and secret-realm systems., The seeded named foe that champions the tournament at this location., Tournaments are held where sects gather (academies, sect halls, arenas)., Open the secret realm at the current location (if one opens here)., Step into the next room of the active realm, resolving its kind., Harvest a herb at the current location (gated by its herb table)., Abandon the realm, returning to the overworld. (+7 more)

### Community 30 - "Sect System Tests"
Cohesion: 0.17
Nodes (17): Any, Lists location sects and resolves joining them., Return summaries for the sects available at a location. Dominant sects (world-…, Return one sect's details plus the player's join status., Return ``{allowed, reason}`` for joining ``sect_id`` right now., Join a sect: assign ``player.path`` and report the starting rank., SectSystem, _player() (+9 more)

### Community 31 - "Equipment Durability & Sets"
Cohesion: 0.19
Nodes (7): EquipmentSystem, Any, Fold in the strongest met set-bonus threshold for each equipped set., Validates equipment actions and aggregates equipped modifiers., Return the item's durability ceiling, or 0 when it has no durability model., Reduce each equipped destructible item's durability by ``amount``. Returns…, Restore a piece of equipped, destructible gear to full durability for gold.…

### Community 32 - "Narrative Renderer Tests"
Cohesion: 0.13
Nodes (23): NarrativeSystem, Renders weighted, conditional template variants into prose., Return every template verb key known to this engine., Return the number of variants declared for ``verb`` (0 if unknown)., _full_context(), Tests for the procedural narrative engine (ROADMAP A.1-A.3)., Every engine event must map (via EVENT_VERB) to a narrated verb., Every processed action returns a non-empty narrative line (A.5). (+15 more)

### Community 33 - "Result Serialization Tests"
Cohesion: 0.14
Nodes (15): DispatchMixin, Any, Action routing: the public ``process_action`` contract and dispatch tables., Exploration-mode actions, keyed by action name. Handlers look attributes up on…, Routes a structured action to the right handler for the current mode., Process a structured command and return a structured result. Every result is…, Flag the session as finished and return the quit result., Attach a fallback narrative line to any result that lacks one. Results that… (+7 more)

### Community 34 - "Engine Views & Briefs"
Cohesion: 0.13
Nodes (12): Any, Return the legacy unlock tree with live purchase state (C.5). Reachable mid-run…, Set the player's display name (used by character creation in the UI)., Return UI-safe briefs for the player's skills, incl. live combat state. Read-…, Return the player's inventory as UI-safe entries (read-only view)., Classify a technique for the Techniques tab. Returns one of ``Active`` (invoked…, The cosmetic title granted by a purchased legacy unlock (C.5)., Read-only views the frontends render (no gameplay rules here). (+4 more)

### Community 35 - "Legacy Tree & World Seed Tests"
Cohesion: 0.11
Nodes (15): LegacySystem, Any, Legacy system (ROADMAP C.5 + C.6). Two pure responsibilities, both rule-only…, True when too few earlier tiers hold purchases for this tier., Derive the run's world variation from the seed. Pure derivation over a pre-…, Resolves the cross-run unlock tree and the world-seed report., Return every tier definition (in data order)., Return one unlock node by id (with its ``tier_id``), or ``None``. (+7 more)

### Community 36 - "Cultivation System Internals"
Cohesion: 0.13
Nodes (11): Body Transformation Track, Breakthrough Gating, Cultivation Strain, Essence Gathering Track, Foundation Stability, CultivationSystem, Handles independent body and essence cultivation tracks., Advance Essence Gathering within the current realm when possible. (+3 more)

### Community 37 - "Combat Statuses & Stakes Tests"
Cohesion: 0.33
Nodes (22): _combat(), _enemy(), _player(), Tests for combat skill-effect resolution and passive stat derivation., _skill(), test_buff_attack_passive_raises_effective_attack(), test_counter_damages_attacker(), test_crit_chance_passive() (+14 more)

### Community 38 - "Result Contract Tests"
Cohesion: 0.13
Nodes (20): ErrorResult, MessageResult, Outcome of accepting a rolled starting fate., A successful move, carrying the destination's UI-safe view., A plain informational message., A rejected command, tagged with a stable ``reason`` code., Outcome of resting: HP/Qi recovered and the new totals., Outcome of stabilising the body cultivation foundation. (+12 more)

### Community 39 - "Voice Lint Tests"
Cohesion: 0.12
Nodes (15): The on-disk meta-save location., load_glossary_terms(), Load the lore glossary as ``{slot: frozenset(approved terms)}``. Terms declared…, Path, A.6 voice-consistency tests: sameness floor, gamey-term ban, glossary. The…, Simulate a 100-event run across the core action loop; every core verb must…, _system(), test_100_event_run_meets_sameness_floor() (+7 more)

### Community 40 - "Cultivation Actions (Strain/Breakthrough)"
Cohesion: 0.15
Nodes (6): Attempt a Body Transformation breakthrough without touching essence progress., Attempt an Essence Gathering breakthrough without touching body progress., Reduce body cultivation strain and restore foundation stability., Reduce Essence Gathering strain and restore essence foundation stability., Return the essence track display name with substage/fall context., Return the current Body Transformation progress requirement.

### Community 41 - "Lifespan System"
Cohesion: 0.14
Nodes (11): LifespanSystem, Any, Return the current season, derived from whole years elapsed since spawn., Compute maximum lifespan, advance age, and detect death by old age., Return the current maximum lifespan in years, or ``None`` if immortal. Lifespan…, Return the age (in years) a given action consumes., Advance the player's age by the action's time cost; return years added. When…, Return years left before old-age death, or ``None`` when immortal. (+3 more)

### Community 42 - "Sell System Tests"
Cohesion: 0.16
Nodes (16): Any, Sell (liquidation) rules. Converts owned items/equipment/manuals into gold at a…, Validates and performs selling owned items for gold., Return the gold worth of an item (before the sell-rate discount)., Return what one unit of ``item`` sells for in gold (min 1)., Sell ``quantity`` of an owned item for gold; remove it from inventory., SellSystem, _items() (+8 more)

### Community 43 - "Combo Combat Tests"
Cohesion: 0.22
Nodes (21): _combat(), _enemy(), _player(), Tests for the B.6 stance/combo combat system. Techniques typed…, _skill(), _start_combat_with(), test_chain_advances_through_all_roles(), test_chain_bonus_scales_with_banked_stage() (+13 more)

### Community 44 - "Talent Ladder Helpers"
Cohesion: 0.20
Nodes (20): _load(), main(), Path, Seed the talent-refining resource (``talent_refining_elixir``) into the world.…, seed_enemies(), seed_masters(), seed_pools(), seed_shops() (+12 more)

### Community 45 - "Cultivation Speed & Comprehension"
Cohesion: 0.12
Nodes (7): Advance only Essence Gathering progress., Backward-compatible default training action: train the body track., Body foundation support used by essence training., Essence density support used by body training., Advance only Body Transformation progress., Product of learned ``cultivation_speed`` passives and a comprehension speed…, Each point of comprehension above the starting 10 grants +0.5% base…

### Community 46 - "GameEngine Mixins & Wiring"
Cohesion: 0.12
Nodes (15): EconomyMixin, ExplorationMixin, Sky Spill Continent Map, World Map (Staged), GameEngine, Any, Item, RNG (+7 more)

### Community 47 - "Command Router Tests"
Cohesion: 0.17
Nodes (18): CommandRouter, Translates human input into engine actions., Return the command reference used by the UI to render help., Tests for the command router's text-to-action mapping., test_boon_command_extracts_character_id(), test_character_interaction_commands_extract_character_id(), test_empty_command_is_unknown(), test_essence_training_and_breakthrough_commands() (+10 more)

### Community 48 - "Narrative Engine (Prose Renderer)"
Cohesion: 0.14
Nodes (9): Any, RNG, Return the narrative verb that narrates ``event`` (A.5). Falls back to the…, Render the fallback prose line for an engine event, or ``""`` if none., Render one eligible weighted variant of ``verb`` (order-sensitive)., Return ``True`` when every predicate in ``when`` holds against ``context``., Substitute ``{slot}`` placeholders, leaving unknown slots verbatim., Prose for a breakthrough attempt, varying by outcome and season. (+1 more)

### Community 49 - "Starting Fate System"
Cohesion: 0.18
Nodes (9): Any, RNG, Roll and view Martial Talent / Body Talent starting data., Roll one Martial Talent and one Body Talent from positive weights., Return a UI-safe Martial Talent data view by stable ID., Return a UI-safe Body Talent data view by stable ID., Return the UI-safe upgrade targets a talent may currently upgrade into.…, Return whether ``target_id`` is a valid upgrade from ``talent_id``. (+1 more)

### Community 50 - "Engine Actions Tests"
Cohesion: 0.11
Nodes (19): _equip_set_pair(), Tests for the medium-priority close-out (P10-P17). Covers: techniques listing,…, test_broken_equipment_provides_no_modifiers(), test_closed_door_cultivation_ages_and_grants_progress(), test_closed_door_rejects_unknown_years(), test_durability_degrades_and_repairs(), test_export_then_import_round_trips_state(), test_ironman_blocks_load() (+11 more)

### Community 51 - "Meta Depth Tests"
Cohesion: 0.16
Nodes (17): Test Engineer Agent, Pytest configuration. An (otherwise empty) ``conftest.py`` at the repository…, _meta(), Meta depth (ROADMAP Phase 2 C): legacy unlock tree, world seed, ascension. C.5…, test_dominant_sect_gets_reputation_discount_and_listing(), test_endless_flag_round_trips_through_save(), test_meta_state_carries_unlock_tree(), test_retire_banks_scaled_reward_and_records_ascension() (+9 more)

### Community 52 - "Progression Mixin Actions"
Cohesion: 0.15
Nodes (11): ProgressionMixin, Any, Notify quests on a successful breakthrough and attach narrative prose., Advance the minimal backend day after successful recovery actions., Age the player by an action's time cost and enforce lifespan limits., The verbs that grow the cultivator and advance the calendar., Return the player's known techniques (active + passive)., Return the player's Martial/Body talents and their upgrade paths. Each upgrade… (+3 more)

### Community 53 - "World Map Reachability Tests"
Cohesion: 0.25
Nodes (17): LocationSystem, _locations(), _player(), Structural tests for the shipped world map (``data/locations.json``). These…, Directed breadth-first search over ``connected_locations`` edges., _reachable_from(), _registry(), test_all_locations_have_normalized_map_positions() (+9 more)

### Community 54 - "Morality & Relationship Validation"
Cohesion: 0.18
Nodes (16): load_json(), JSON content loading. Loads data files from the sibling ``data/`` directory…, Load and parse a JSON file from the data directory., Skill: Game Data Authoring, Tests that data files load and parse as expected., test_body_cultivation_realms_load(), test_body_talents_load(), test_equipment_loads() (+8 more)

### Community 55 - "Insight Combat Tests"
Cohesion: 0.20
Nodes (18): _combat(), _enemy(), _player(), Tests for the B.5 intent/insight combat resource. Insight builds from…, _skill(), _start_combat_with(), test_all_intent_skills_require_insight_and_are_active(), test_attack_builds_insight_and_emits_insight_events() (+10 more)

### Community 56 - "Cultivation State Models"
Cohesion: 0.16
Nodes (10): BodyCultivationState, BreakthroughResult, CultivationState, EssenceCultivationState, Any, Pure cultivation state models. These dataclasses hold persistent cultivation…, Combined cultivation state for a character., Structured result for a cultivation breakthrough attempt. (+2 more)

### Community 57 - "Relationship System"
Cohesion: 0.20
Nodes (9): Any, Record a notable player action (and optional memory flag) for an NPC., Return the NPC's state plus its derived interaction tier., Creates, adjusts, and interprets per-NPC relationship state., Return the NPC's state, creating neutral defaults if it is missing. NPCs never…, Return the interaction tier id a relationship_score falls into., Return ``True`` when ``tier_id`` is at least ``minimum`` in tier order. Tier…, Apply clamped deltas to one NPC's emotional variables. (+1 more)

### Community 58 - "Talent System"
Cohesion: 0.15
Nodes (11): Cultivation Agent, Lifespan, Starting Fate, Talent Ladder, Any, Talent tier ladder lookups. The talent ladder is a data-driven, two-track…, Resolve entries from the two-track talent tier ladder., Return UI-safe views for every ladder entry, ordered by tier index. (+3 more)

### Community 59 - "Morality System & NPC Rules"
Cohesion: 0.20
Nodes (10): Social Agent, MoralitySystem, Any, Reads morality bands from data and interprets/adjusts a morality score., Clamp a score into the configured morality range., Return the band definition a score falls into., Return just the band id for a score., Return a structured description of the score's current band. (+2 more)

### Community 60 - "Engine Economy & Social Dispatch"
Cohesion: 0.18
Nodes (8): EconomyMixin, Any, Item/equipment/currency verbs plus sect membership., Sell owned items/equipment for gold., Repair an equipped piece of worn gear, spending gold per durability point., Use an item in exploration; technique manuals teach their skill instead., Learn a technique from a location trainer, paying its currency cost., Join a sect, assigning the player's martial path.

### Community 61 - "Cultivation Service"
Cohesion: 0.28
Nodes (3): CultivationService, Any, Coordinates cultivation actions for registered players.

### Community 62 - "Breakthrough Logic"
Cohesion: 0.20
Nodes (5): Any, RNG, Return the next Body Transformation realm definition, if any., Advance Essence Gathering to the next reachable realm when possible., Backward-compatible default breakthrough action: advance the body track.

### Community 63 - "Validation Result Infrastructure"
Cohesion: 0.15
Nodes (9): Central data validation for shipped game content. Public entry point: from…, Result types for data validation. A validation pass collects every problem it…, A single data problem, tagged with a category for grouping/filtering., The accumulated outcome of a validation pass., Return ``True`` when no problems were recorded., Record a problem under ``category``., Return a human-readable, newline-separated summary of all problems., ValidationError (+1 more)

### Community 64 - "GitHub Skills & UI Rules"
Cohesion: 0.15
Nodes (15): ApiClient.gd (HTTP client), Copilot Instructions Hub, AI Response Rules (12), Architecture Rules (01), Cultivation & Progression Rules (06), Data-Driven Design Rules (03), Dialogue System Rules (07), Documentation Rules (11) (+7 more)

### Community 65 - "Engine Combat Mixin"
Cohesion: 0.26
Nodes (8): CombatMixin, Any, The combat turn loop and its cleanup/penalty helpers., Use an item during combat; this consumes the player's turn., Resolve the consequences of a finished fight and leave combat mode., A friendly spar ends with no loot or progress loss; the loser is patched up., Defeat is not game over: the player is rescued at a data-driven cost., Validate and resolve an active-skill activation in combat.

### Community 66 - "Trainer System Views"
Cohesion: 0.30
Nodes (6): Any, Lists location trainers and resolves paid technique learning., Return summary data for trainers available at a location., Return a trainer's teachable techniques visible to the player., Learn a technique from an available trainer, spending its currency cost., TrainerSystem

### Community 67 - "Origins & Softcore Tests"
Cohesion: 0.22
Nodes (12): Meta-save service. Persists *cross-run* state that outlives any single…, _meta(), Roguelike legacy & meta (ROADMAP C.1-C.4). Covers the permadeath default + run…, test_chronicle_records_runs_and_stays_bounded(), test_detects_origin_with_unknown_dao(), test_get_meta_state_annotates_affordability(), test_hardcore_death_ends_run_and_banks_meta(), test_memory_adds_and_spends() (+4 more)

### Community 68 - "Character Interaction Tests"
Cohesion: 0.31
Nodes (13): MoralitySystem, _dialogue_service(), _player(), Tests for the CharacterService coordination layer., _service(), test_available_characters_are_scoped_to_the_location(), test_can_spar_reflects_hooks_and_can_duel_respects_unlock(), test_dialogue_choices_are_filtered_by_availability() (+5 more)

### Community 69 - "Currency & Wallet"
Cohesion: 0.17
Nodes (12): currency_amount(), normalise_price(), Any, Shared currency helpers. Purchases (shops) and technique tuition (trainers)…, Return only the supported, positive currency amounts from a raw price., Return how much of ``currency`` the player currently holds., Return the missing amount per currency the player cannot afford., Deduct an affordable ``price`` from the player's wallet/inventory. (+4 more)

### Community 70 - "Alchemy Herbs & Recipes"
Cohesion: 0.29
Nodes (12): build_gathering(), build_herbs(), build_recipes(), _load_json(), main(), Any, Expand the alchemy + secret-realm content breadth (ROADMAP F.1 / D.2 follow-…, Append new herbs to ``items`` in place; return the updated list. (+4 more)

### Community 71 - "Action Contract & Daos Data"
Cohesion: 0.18
Nodes (12): Architecture Agent, Combat Agent, Commit Gatekeeper Agent, Godot Agent, game-orchestrator Agent, Agent Fleet README, MainController.gd (Godot UI), Action (+4 more)

### Community 72 - "Player Save Round-Trip"
Cohesion: 0.18
Nodes (8): empty_equipment_slots(), _equipment_from_save(), Any, Return a fallback display title for the current cultivation state., Return a UI-safe snapshot of the full player sheet., Return a faithful, round-trippable snapshot for the save system., Reconstruct a Player from a :meth:`to_save_dict` snapshot., test_player_dao_round_trips_through_save()

### Community 73 - "Refine System Tests"
Cohesion: 0.17
Nodes (11): Alchemy loop (ROADMAP F.1): gathering herbs and refining them into pills., test_demonic_herbs_grow_only_in_demon_continent(), test_gather_adds_herb_at_herb_rich_location(), test_gather_rejected_where_no_herbs_grow(), test_herbs_carry_rarity(), test_high_tier_recipe_unavailable_in_menu(), test_recipes_exposed_in_state(), test_refine_consumes_inputs_and_produces_output() (+3 more)

### Community 74 - "Data Cross-Reference Tests"
Cohesion: 0.18
Nodes (4): _cultivation_system(), Data-file integrity checks: unique IDs and valid cross-references., test_cultivation_data_is_valid(), test_enemy_loot_references_existing_items()

### Community 75 - "Trainer System Tests"
Cohesion: 0.30
Nodes (11): Tests for data-driven skill trainers (technique masters)., _skills(), _system(), test_learn_already_known_skill_is_rejected(), test_learn_spends_currency_and_teaches(), test_learn_unoffered_skill_is_rejected(), test_learn_without_funds_is_rejected(), test_path_locked_technique_requires_matching_path() (+3 more)

### Community 77 - "Morality System Tests"
Cohesion: 0.25
Nodes (8): Character service. Single authority for "who is here, and what can I do with…, Morality system. Interprets a player's morality score into a named band…, Tests for the morality system's band interpretation and clamped adjustments., _system(), test_adjust_clamps_to_maximum(), test_adjust_clamps_to_minimum(), test_adjust_reports_actual_change(), test_band_ids_cover_the_full_range()

### Community 78 - "State-Aware Prose Descriptions"
Cohesion: 0.18
Nodes (5): Render ``verb`` stably for the given identity ``keys``. The variant is drawn…, Prose for a location, varying by danger and season (stable per place)., Prose for an NPC, varying by relationship tier and morality band., Prose for an item, varying by rarity (stable per item name)., Prose for a technique, flavoured by its Dao affinity.

### Community 79 - "Relationship Tier Tests"
Cohesion: 0.29
Nodes (9): Relationship system. Manages per-NPC relationship state stored as ``{npc_id:…, Tests for the relationship system's per-NPC state, clamping, and tiers., _system(), test_adjust_clamps_and_reports_applied_delta(), test_ensure_creates_neutral_defaults(), test_meets_min_tier_orders_tiers(), test_relationship_score_can_go_negative_into_hostile(), test_remember_records_each_action_once() (+1 more)

### Community 80 - "Character Data Tests"
Cohesion: 0.29
Nodes (10): load_collection(), Any, Load a list-collection by logical ``name``. If a directory ``data/<name>/``…, Validation tests for the data-driven NPC roster (data/characters/)., test_all_characters_have_gameplay_hooks(), test_all_characters_have_personality_schema(), test_all_characters_share_starting_region(), test_character_ids_are_unique() (+2 more)

### Community 81 - "Talent Ladder Tests"
Cohesion: 0.29
Nodes (10): _make_system(), Tests for the two-track talent tier ladder., test_engine_exposes_talent_ladder(), test_every_tier_carries_both_track_names_realm_and_lifespan(), test_immortal_tiers_use_null_lifespan_sentinel(), test_ladder_covers_twenty_tiers_plus_apex(), test_shipped_talent_ladder_is_valid(), test_tier_view_resolves_shared_index_to_both_tracks() (+2 more)

### Community 82 - "CLI Entry Points"
Cohesion: 0.24
Nodes (6): Command router. Maps raw input strings (``"train"``, ``"use healing_pill"``,…, main(), Entry point — the composition root. ``main`` wires the layers together and…, Construct the layers and run the game., Command-line interface. Owns the input/output loop. It converts engine result…, Root-level launcher for the CLI version of Martial Path. Convenience wrapper so…

### Community 83 - "Derived Stats & Risk"
Cohesion: 0.20
Nodes (5): Calculate current Body Transformation stat contribution., Calculate current Essence Gathering stat contribution., Calculate derived stats from both tracks without persisting them., Return balance status from relative realm order., Estimate overall breakthrough safety from foundations and resources.

### Community 84 - "Boon & Gating Tests"
Cohesion: 0.33
Nodes (9): _player(), Tests for relationship-gated rewards (boons) and morality-gated interactions.…, _service(), test_engine_map_returns_position_and_destinations(), test_engine_receive_boon_grants_gold_and_claims_once(), test_engine_receive_boon_grants_item(), test_reward_gates_on_morality_band(), test_reward_gates_on_relationship_tier() (+1 more)

### Community 85 - "Essence Unlock Logic"
Cohesion: 0.22
Nodes (3): Return a non-mutating breakthrough preview for a UI or API., Public: has the body cleared Pulse Condensation, opening Essence Gathering?, Return a display string describing what unlocks Essence Gathering. Empty when…

### Community 86 - "Inventory System"
Cohesion: 0.22
Nodes (5): Any, Add ``count`` of an item to the player's inventory., Remove up to ``count`` of an item; return ``True`` if any was removed., Apply an item's effect to the player and consume it if consumable., Return a structured listing of the player's items.

### Community 88 - "Talent Roll Tests"
Cohesion: 0.36
Nodes (6): Starting talent rolls for the Martial and Body cultivation tracks. The system…, _make_system(), Tests for starting talent roll helpers., test_talent_views_do_not_expose_roll_weights_or_upgrade_options(), test_weighted_roll_only_returns_rollable_entries(), test_weighted_roll_returns_valid_talent_ids()

### Community 89 - "Location Art Generator"
Cohesion: 0.52
Nodes (6): main(), _pixel(), Path, Generate placeholder art for ``divine_phoenix_mystic_realm``. The handover…, _write_import(), _write_png()

### Community 90 - "Shop Seeding Tool"
Cohesion: 0.48
Nodes (6): dump(), _equipment_price(), load(), main(), Any, Seed additional shops so most regions have a market. Until this script exists,…

### Community 91 - "Import Smoke Tests"
Cohesion: 0.33
Nodes (5): _module_names(), parametrize, Smoke test: every module under ``game/`` imports cleanly. Catches syntax…, Return the dotted module name for every ``.py`` file under ``game/``., test_game_module_imports()

### Community 92 - "JSON Parse Smoke Tests"
Cohesion: 0.40
Nodes (5): _json_files(), parametrize, Path, Smoke test: every JSON file under ``game/data/`` parses. A single malformed…, test_data_json_parses()

### Community 93 - "Talent Upgrade Seeding"
Cohesion: 0.47
Nodes (5): main(), Path, Seed ``upgrade_options`` into the Martial and Body talent tracks. Each talent…, resource_quantity(), seed()

### Community 94 - "Diagnostic Logger"
Cohesion: 0.40
Nodes (4): get_logger(), Developer-facing diagnostic logging. This uses the standard :mod:`logging`…, Return a configured logger for ``name`` (idempotent)., Logger

### Community 95 - "Skill Reachability Tests"
Cohesion: 0.50
Nodes (4): _manual_to_skill(), Every skill must be obtainable through at least one acquisition path. Technique…, Map a manual item id back to its skill id (mirrors engine generation)., test_every_skill_is_reachable()

### Community 96 - "Enemy Ability Tests"
Cohesion: 0.40
Nodes (5): _enemy_with(), Enemy, test_enemy_poison_ability_applies_player_dot(), test_enemy_stun_ability_stuns_player(), test_player_stunned_turn_forfeits_action()

### Community 97 - "Map & Ability Validators"
Cohesion: 0.33
Nodes (4): Flag locations whose map markers sit exactly on top of another's., Check enemy ``abilities`` entries are well-formed., _validate_enemy_abilities(), _validate_map_positions()

## Knowledge Gaps
- **81 isolated node(s):** `Gold / Spirit Stones`, `Daos Data (12-dao counter graph)`, `Legacy Tree Data`, `Lore Glossary Data`, `ApiClient.gd (HTTP client)` (+76 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **65 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EventType` connect `Engine Result Types` to `GUI Escape Helper Tests`, `Combat Round Mechanics`, `Travel & Map Gate Tests`, `Find & Loot Rarity Tests`, `Roadmap & Origins`, `Enemy Model & Views`, `API Endpoint Tests`, `Engine Integration Tests`, `Quest System Tests`, `Lifespan & Aging Tests`, `CLI Interface Loop`, `Cultivation Training Tests`, `Run Lifecycle & Retirement`, `Seed Tools & Shop Data`, `Loot & Inventory Tests`, `Secret Realm Tests`, `Shop System Tests`, `Narrative Linter & Voice`, `Skill Learning Tests`, `Engine Advanced Actions`, `Sect System Tests`, `Equipment Durability & Sets`, `Narrative Renderer Tests`, `Result Serialization Tests`, `Engine Views & Briefs`, `Cultivation System Internals`, `Result Contract Tests`, `Sell System Tests`, `Combo Combat Tests`, `Engine Actions Tests`, `Progression Mixin Actions`, `Insight Combat Tests`, `Engine Economy & Social Dispatch`, `Engine Combat Mixin`, `Trainer System Views`, `Action Contract & Daos Data`, `Refine System Tests`, `Trainer System Tests`, `CLI Entry Points`, `Boon & Gating Tests`?**
  _High betweenness centrality (0.207) - this node is a cross-community bridge._
- **Why does `Player` connect `Lifespan & Aging Tests` to `Combat Round Mechanics`, `Save & Persistence Tests`, `Find & Loot Rarity Tests`, `Engine Result Types`, `Quest System Tests`, `Dao Counter & Pressure Tests`, `Cultivation Training Tests`, `Run Lifecycle & Retirement`, `Seed Tools & Shop Data`, `Loot & Inventory Tests`, `Shop System Tests`, `Skill Learning Tests`, `Sect System Tests`, `Equipment Durability & Sets`, `Cultivation System Internals`, `Combat Statuses & Stakes Tests`, `Cultivation Actions (Strain/Breakthrough)`, `Lifespan System`, `Sell System Tests`, `Combo Combat Tests`, `Cultivation Speed & Comprehension`, `GameEngine Mixins & Wiring`, `Engine Actions Tests`, `Insight Combat Tests`, `Cultivation Service`, `Breakthrough Logic`, `Trainer System Views`, `Currency & Wallet`, `Player Save Round-Trip`, `Trainer System Tests`, `Derived Stats & Risk`, `Essence Unlock Logic`, `Inventory System`, `Enemy Ability Tests`, `Body Realm Display Names`, `Effect System`, `Loot Rolling Core`?**
  _High betweenness centrality (0.176) - this node is a cross-community bridge._
- **Why does `GameEngine` connect `GameEngine Mixins & Wiring` to `GUI Escape Helper Tests`, `Combat Round Mechanics`, `Save & Persistence Tests`, `Data Validation Core`, `Roadmap & Origins`, `API Endpoint Tests`, `Engine Integration Tests`, `Lifespan & Aging Tests`, `CLI Interface Loop`, `Dao Counter & Pressure Tests`, `Run Lifecycle & Retirement`, `Seed Tools & Shop Data`, `Secret Realm Tests`, `Effective Stats Tests`, `Shop System Tests`, `Skill Learning Tests`, `Project Docs & Registry`, `Meta Save & Ancestral Memory`, `Sect System Tests`, `Narrative Renderer Tests`, `Result Serialization Tests`, `Engine Views & Briefs`, `Legacy Tree & World Seed Tests`, `Cultivation System Internals`, `Combo Combat Tests`, `Engine Actions Tests`, `Meta Depth Tests`, `Progression Mixin Actions`, `Insight Combat Tests`, `GitHub Skills & UI Rules`, `Engine Combat Mixin`, `Origins & Softcore Tests`, `Character Interaction Tests`, `Action Contract & Daos Data`, `Refine System Tests`, `Talent Ladder Tests`, `CLI Entry Points`, `Boon & Gating Tests`?**
  _High betweenness centrality (0.142) - this node is a cross-community bridge._
- **Are the 17 inferred relationships involving `Player` (e.g. with `LifecycleMixin` and `GameEngine`) actually correct?**
  _`Player` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 53 inferred relationships involving `EventType` (e.g. with `CombatMixin` and `DispatchMixin`) actually correct?**
  _`EventType` has 53 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `CultivationSystem` (e.g. with `GameEngine` and `Engine Changelog`) actually correct?**
  _`CultivationSystem` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `GUIInterface` (e.g. with `Action` and `EventType`) actually correct?**
  _`GUIInterface` has 3 INFERRED edges - model-reasoned connections that need verification._