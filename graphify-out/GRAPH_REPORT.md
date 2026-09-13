# Graph Report - Martial Path  (2026-09-13)

## Corpus Check
- 302 files · ~4,283,005 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3958 nodes · 9794 edges · 217 communities (186 shown, 31 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 871 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ba5bd3d6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- GUIInterface
- Enemy
- LocationSystem
- SaveService
- rng.py
- results.py
- NarrativeSystem
- Skill
- test_dao_debate.py
- Item
- CLIInterface
- ShopSystem
- gen_avatar_art.py
- QuestSystem
- game_engine.py
- test_lifespan_system.py
- dead_content.py
- server.py
- Player
- EventType
- SecretRealmSystem
- test_combo_combat.py
- CharacterService
- EconomyMixin
- LifecycleMixin
- ExplorationMixin
- SystemsMixin
- SectSystem
- normalize_available_systems.py
- GameDataRegistry
- RefineSystem
- EquipmentSystem
- LifespanSystem
- MetaService
- validate_all_game_data
- MoralitySystem
- .__init__
- test_combat_system.py
- SellSystem
- seed_techniques.py
- test_results.py
- load_collection
- StartingFateSystem
- DispatchMixin
- CultivationSystem
- EncounterSystem
- ViewsMixin
- RelationshipSystem
- test_locations_data.py
- GameEngine
- ProgressionMixin
- OriginSystem
- load_json
- cultivation.py
- CultivationService
- test_encounters.py
- RNG
- ValidationResult
- Essence Gathering Track
- EncountersMixin
- ._build_manual_items
- test_relationship_system.py
- .calculate_derived_cultivation_stats
- expand_alchemy.py
- 4. Programmes
- lint_narrative_templates
- CombatSystem
- test_roguelike_meta.py
- test_equipment_system.py
- test_player_identity.py
- _service
- economy_balance.py
- TurnEvent
- test_starting_fate_system.py
- gen_missing_location_art.py
- seed_shops.py
- ui_theme.py
- Phase 1 - MVP (core loop sings)
- test_import_smoke.py
- test_json_parse_smoke.py
- seed_talent_upgrades.py
- WorldSimulationSystem
- godot_ui_audit.py
- run_backend.py
- .to_dict
- seed_enemy_abilities.py
- seed_enemy_daos.py
- seed_equipment_sets.py
- conftest.py
- api/__init__.py
- application/__init__.py
- engine/__init__.py
- core/__init__.py
- game/__init__.py
- models/__init__.py
- persistence/__init__.py
- services/__init__.py
- systems/__init__.py
- ui/__init__.py
- utils/__init__.py
- test_api_server.py
- Prompt sheet
- Epic E: Living World Simulation
- Phase 2 - Alpha (depth + breadth)
- Phase 3 - 1.0 (balance + polish)
- Phase 4 - Endless (stretch)
- CombatMixin
- WorldMixin
- What You Must Do When Invoked
- FoeAI
- TravelService
- LegacySystem
- Location Art Prompts
- CampaignMixin
- DebateMixin
- test_dead_content.py
- seed_world_content.py
- EventSystem
- test_content_breadth.py
- SaveRepository
- TestActs23
- test_sect_system.py
- Martial Path — Shared Project Rules (inherited by every agent)
- world_checks.py
- test_quest_system.py
- TrainerSystem
- test_codex.py
- test_meta_depth.py
- seed_enemy_pools.py
- gui_interface.py
- Martial Path — A Cultivation Text RPG
- currency.py
- .choose_action
- DESIGN.md — Martial Path (Godot frontend)
- .from_save_dict
- ._player_damage_parts
- Procedure
- Product
- test_trainer_system.py
- economy_tune.py
- test_secret_realm.py
- test_travel_service.py
- complete_v4_swap.py
- with_article
- GatherSystem
- Layer Responsibilities
- test_story_tiers.py
- test_talent_system.py
- graphify reference: extra exports and benchmark
- Ponytail
- .from_dict
- .use_item
- GUI Updates -> Godot Only
- test_location_artwork.py
- test_time_model.py
- Ponytail Help
- Unreleased
- Martial Path — Voice & Prose Guide (ROADMAP A.6)
- test_godot_event_coverage.py
- test_morality_system.py
- godot_mcp_capture.py
- graphify reference: query, path, explain
- Godot AI
- 02 — UI Separation Rules
- 12 — AI Assistant Response Rules
- Martial Path Data Authoring
- Martial Path Engine & Architecture
- Martial Path Testing & Validation
- Martial Path
- expand_phase_f.py
- expand_phase_f_wave2.py
- Architecture & Contracts Specialist
- Godot Frontend Specialist
- ponytail-audit/SKILL.md
- Ponytail Gain
- ponytail-review/SKILL.md
- Test Engineer
- .apply_to_player
- ValidationError
- 03 — Data-Driven Design Rules
- 04 — Godot Export Rules
- 05 — NPC AI and Relationship Rules
- 06 — Cultivation and Progression Rules
- 07 — Dialogue System Rules
- 08 — Save System Rules
- 09 — Testing and Validation Rules
- 11 — Documentation Rules
- test_godot_state_contract.py
- API, Save & Meta Specialist
- Combat & Dao Specialist
- Commit Gatekeeper
- Cultivation & Progression Specialist
- Data Integrity & Content Specialist
- Economy & Equipment Specialist
- Narrative & Prose Specialist
- Game Orchestrator
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native AGENTS.md integration
- graphify reference: incremental update and cluster-only
- ponytail-debt/SKILL.md
- Social, Quest & Sect Specialist
- World & Exploration Specialist
- Time Model
- .unlocks
- Copilot Instructions — Martial Path Cultivation RPG
- 00 — Global Behaviour Rules
- test_godot_panels.py
- godot-ai
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- godot-ai
- .roll_loot
- ponytail.md
- extraction-spec.md
- .convert_exp_to_comprehension
- test_api_request_carries_the_name_field
- test_godot_constants_match_the_engine

## God Nodes (most connected - your core abstractions)
1. `Player` - 363 edges
2. `GameEngine` - 296 edges
3. `EventType` - 277 edges
4. `GameDataRegistry` - 166 edges
5. `RNG` - 156 edges
6. `Action` - 137 edges
7. `CultivationSystem` - 91 edges
8. `Enemy` - 87 edges
9. `CombatSystem` - 83 edges
10. `GUIInterface` - 76 edges

## Surprising Connections (you probably didn't know these)
- `Epic A: Procedural Narrative Engine` --implements--> `NarrativeSystem`  [INFERRED]
  ROADMAP.md → game/systems/narrative_system.py
- `Epic D: Campaign + Endless Post-game` --implements--> `SecretRealmSystem`  [INFERRED]
  ROADMAP.md → game/systems/secret_realm_system.py
- `Epic C: Roguelike Legacy & Meta` --implements--> `MetaService`  [INFERRED]
  ROADMAP.md → game/services/meta_service.py
- `Epic F: Content Breadth` --implements--> `RefineSystem`  [INFERRED]
  ROADMAP.md → game/systems/alchemy_system.py
- `Epic B: Dao & Philosophy Combat` --references--> `CombatSystem`  [INFERRED]
  ROADMAP.md → game/systems/combat_system.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Cultivation Progression Subsystem** — game_docs_cultivation_system_body_transformation, game_docs_cultivation_system_essence_gathering, game_docs_cultivation_system_cultivation_strain, game_docs_cultivation_system_foundation_stability, game_docs_cultivation_system_breakthrough_gating, game_docs_cultivation_system_talent_ladder, game_docs_cultivation_system_lifespan [EXTRACTED 1.00]
- **Layered Architecture Layers** — game_docs_architecture_layered_architecture, game_docs_architecture_ui_decoupling, game_docs_architecture_engine_contract, game_docs_architecture_state_ownership, game_docs_architecture_eventtype [EXTRACTED 1.00]
- **Phase 1 MVP systems (implemented)** — game_systems_narrative_system_narrativesystem, game_systems_dao_system_daosystem, game_services_meta_service_metaservice, game_systems_origin_system_originsystem, game_systems_secret_realm_system_secretrealmsystem, game_systems_alchemy_system_gathersystem, game_systems_alchemy_system_refinesystem [EXTRACTED 1.00]

## Communities (217 total, 31 thin omitted)

### Community 0 - "GUIInterface"
Cohesion: 0.07
Nodes (26): _danger_color(), _esc(), GUIInterface, _HoverButton, Any, _ratio(), Assemble the move list: a basic Strike plus each active technique., A push button that reports hover, so the move menu can show move details. (+18 more)

### Community 1 - "Enemy"
Cohesion: 0.18
Nodes (12): Enemy, Return ``True`` while the enemy still has HP., Apply ``amount`` damage (clamped at 0 HP) and return damage dealt., Any, Player invokes an active skill, then the enemy retaliates if alive. Qi cost and…, Resolve just the enemy's turn (used after the player uses an item)., Attempt to escape; a failed attempt gives the enemy a free strike., After the player's action, apply regen, run the enemy phase, resolve end. (+4 more)

### Community 2 - "LocationSystem"
Cohesion: 0.08
Nodes (27): danger_label(), LocationSystem, Any, qi_density_label(), Location system. Owns the world map: which places exist and how they connect.…, Return the entry requirements for ``location_id`` (or ``{}``)., Return ``True`` when ``to_id`` is a direct neighbour of ``from_id``., Return a UI-safe snapshot of a location and its exits. (+19 more)

### Community 3 - "SaveService"
Cohesion: 0.10
Nodes (23): Exception, Cultivation Save Shape, Save Version, Save repository -- low-level persistence for save slots. Owns *where* saves…, Any, Path, Save service -- save policy over a persistence backend. Owns the save *schema…, Raised when a save cannot be read or is incompatible. ``code`` is a stable, UI-… (+15 more)

### Community 4 - "rng.py"
Cohesion: 0.14
Nodes (16): Event system. Generates random exploration encounters. It only *selects*…, FindSystem, Any, Rarity-weighted exploration finds. Chooses what the player stumbles upon while…, Weighted, danger-gated selection over the findable item/equipment catalog., Return the highest findable rarity index for an area's danger level., Return a weighted-random findable item id at or below ``max_rarity_index``., Starting talent rolls for the Martial and Body cultivation tracks. The system… (+8 more)

### Community 5 - "results.py"
Cohesion: 0.12
Nodes (19): Any, NPC interaction: talk, dialogue choices, boons, and character combat., Relationship-gated NPC verbs and the spar/duel entry points., Apply a chosen dialogue option's relationship/morality/reputation deltas., Grant an NPC's currently-available relationship reward (one-time)., SocialMixin, BoonResult, CharacterInteractionResult (+11 more)

### Community 6 - "NarrativeSystem"
Cohesion: 0.06
Nodes (36): NarrativeSystem, Any, Narrative system. A deterministic, data-driven prose engine. Templates live in…, Renders weighted, conditional template variants into prose., Return every template verb key known to this engine., Return the number of variants declared for ``verb`` (0 if unknown)., Return the narrative verb that narrates ``event`` (A.5). Falls back to the…, Render the fallback prose line for an engine event, or ``""`` if none. (+28 more)

### Community 7 - "Skill"
Cohesion: 0.11
Nodes (25): Any, Skill model. Skills are fully data-driven (see ``data/skills.json``). The model…, A cultivation technique. Attributes: id: Stable identifier used in data files…, Build a skill from a raw data-file entry., Return ``True`` if the skill must be invoked (vs. passive)., Skill, Any, Skill (technique) acquisition rules. Owns the single question "can this player… (+17 more)

### Community 8 - "test_dao_debate.py"
Cohesion: 0.07
Nodes (37): DaoSystem, Any, Return the signed realm gap and each side's stat multiplier (1.0 = none)., ``True`` when the player outranks the enemy enough that it yields., Return the damage multiplier for ``attacker_dao_id`` vs ``defender_dao_id``., Realm-pressure and Dao-counter rules over the dao + realm catalogues., DebateSystem, Any (+29 more)

### Community 9 - "Item"
Cohesion: 0.12
Nodes (24): Item, Item model. Items are data-driven (see ``data/items.json``). The model holds…, A carryable object. Attributes: id: Stable identifier used in data files and…, Return ``True`` if using the item should consume one from the stack., EffectSystem, Effect system. Central interpreter for player-facing effects such as healing,…, Applies named effects to a player and reports what changed., InventorySystem (+16 more)

### Community 10 - "CLIInterface"
Cohesion: 0.05
Nodes (36): CommandRouter, Any, Command router. Maps raw input strings (``"train"``, ``"use healing_pill"``,…, Convert a raw input line into a structured command dictionary., Translates human input into engine actions., Return the command reference used by the UI to render help., Layered Architecture, UI Decoupling (+28 more)

### Community 11 - "ShopSystem"
Cohesion: 0.11
Nodes (19): Gold / Spirit Stones, Any, Refresh the live market drift applied on top of the seed band (E.3)., Return the current live market drift multiplier., The displayed price of a stock entry: seed band * live market drift., Lists location shop stock and resolves item purchases., The price multiplier this world's economy band applies., Return summary data for shops available at a location. (+11 more)

### Community 12 - "gen_avatar_art.py"
Cohesion: 0.06
Nodes (66): test_generation_is_deterministic(), _acc_beads(), _acc_beard(), _acc_crescent(), _acc_crown(), _acc_dragon_horns(), _acc_feather(), _acc_flame() (+58 more)

### Community 13 - "QuestSystem"
Cohesion: 0.10
Nodes (15): Any, QuestSystem, Advance state-evaluated objectives of active quests (D.4 polish). Some…, Complete state-satisfied quests and return their completion records., Advance active objectives matching ``event_type`` and apply rewards. Returns a…, Return a UI-safe list of every known quest and its progress., Return how many quests have been completed (used by the run summary)., Return ``True`` when any active quest has an objective of ``event_type``. (+7 more)

### Community 14 - "game_engine.py"
Cohesion: 0.08
Nodes (25): Shared constants used across every layer. Centralizing action names and…, Full campaign + post-game (ROADMAP D.3-D.5). Three responsibilities, all…, Combat-mode routing and end-of-combat resolution., Dao debates and spirit-oath duels (ROADMAP B.7): engine-side flow. This mixin…, Economy and gear: buy/sell, equip, repair, use, learn, and join a sect., Choice-driven encounter flow: pending state, dispatch, and application.…, UI-safe state snapshots and view models., Living-world glue (ROADMAP E.1-E.5): ticks, seasons, economy, rumors. This… (+17 more)

### Community 15 - "test_lifespan_system.py"
Cohesion: 0.20
Nodes (16): Lifespan and ageing rules. Pure and data-driven: computes a character's current…, _make_system(), Tests for lifespan tracking, ageing, and old-age death., test_advance_age_uses_configured_time_cost(), test_essence_realm_sets_max_lifespan(), test_higher_essence_realm_extends_lifespan(), test_immortal_never_expires(), test_immortal_realm_has_no_max_lifespan() (+8 more)

### Community 16 - "dead_content.py"
Cohesion: 0.05
Nodes (63): build_report(), _character_sources(), collect_problems(), _consumables_with_dead_effects(), _consumables_without_effect(), _dao_sources(), _daos_without_a_foe(), _dominated_shop_equipment() (+55 more)

### Community 17 - "server.py"
Cohesion: 0.14
Nodes (24): get_meta(), get_state(), health(), list_saves(), load_game(), purchase_unlock(), Any, HTTP API frontend for the Martial Path engine. A thin FastAPI adapter that… (+16 more)

### Community 18 - "Player"
Cohesion: 0.09
Nodes (49): Player, Keep legacy single-progress construction aligned with body progress., Return ``True`` while the player still has HP., Apply ``amount`` damage (clamped at 0 HP) and return damage dealt., Restore up to ``amount`` HP (clamped at max) and return HP recovered., Restore up to ``amount`` Qi (clamped at max) and return Qi recovered., The player-controlled cultivator., MonkeyPatch (+41 more)

### Community 19 - "EventType"
Cohesion: 0.09
Nodes (54): Action, EventType, Discriminators attached to every structured result the engine returns. The UI…, Canonical action identifiers produced by the command router. The UI never…, StrEnum, Alchemy loop (ROADMAP F.1): gathering herbs and refining them into pills., test_gather_adds_herb_at_herb_rich_location(), test_gather_rejected_where_no_herbs_grow() (+46 more)

### Community 20 - "SecretRealmSystem"
Cohesion: 0.06
Nodes (22): Any, Realm metadata for the foe pools (id -> realm-tier info). ``foe_orders`` (foe…, The depth-appropriate slice of the mook pool for endless rooms. Without gating,…, The depth-appropriate slice of the named-foe pool (as for mooks)., Draw an endless encounter foe: mostly mooks, sometimes a named foe., Draw endless treasure from a weighted ``{item_id, weight}`` pool., Choose an endless boss whose tier grows with the road's depth. Bosses are drawn…, Seeded room generation for a catalogue of hand-placed realms. (+14 more)

### Community 21 - "test_combo_combat.py"
Cohesion: 0.05
Nodes (71): Effective Stats / Passive Skills, Derived Equipment Stats, Equipment Slots, Any, Effective-stats calculation. Computes a player's *effective* combat stats from…, Probability (0..1) of a critical hit, from ``crit_chance`` passives., Damage multiplier on a critical hit; ``crit_damage`` passives raise it., Flat (hp, qi) recovered at the start of each of the player's combat turns. (+63 more)

### Community 22 - "CharacterService"
Cohesion: 0.12
Nodes (18): CharacterService, Any, Return whether the player may spar this NPC, and why not if blocked., Return whether the player may duel this NPC, and why not if blocked., Return the dialogue choices currently available for one NPC. A choice is…, Return a validated, currently-available dialogue choice, or ``None``. The…, Return the first unclaimed relationship reward whose gate is met. Rewards live…, Convenience predicate: is a relationship reward currently claimable? (+10 more)

### Community 23 - "EconomyMixin"
Cohesion: 0.18
Nodes (8): EconomyMixin, Any, Item/equipment/currency verbs plus sect membership., Sell owned items/equipment for gold., Repair an equipped piece of worn gear, spending gold per durability point., Use an item in exploration; technique manuals teach their skill instead., Learn a technique from a location trainer or joined sect hall., Join a sect, assigning the player's martial path.

### Community 24 - "LifecycleMixin"
Cohesion: 0.06
Nodes (38): LifecycleMixin, Any, Run lifecycle: starting fate, permadeath, and save/load persistence., The cosmetic legacy title this run's character carries (C.5)., Buy a legacy-tree unlock with Ancestral Memory (C.5). Cross-run: the purchase…, Apply purchased legacy unlocks to a fresh character (C.5). Runs after origin…, True when the player has crossed the ascension threshold., Ascend: end the run as a *win* and bank the large legacy reward. Retirement is… (+30 more)

### Community 25 - "ExplorationMixin"
Cohesion: 0.09
Nodes (22): ExplorationMixin, Any, World exploration, movement, enemy spawning, and their prose helpers., Return the enemy's public stats plus a UI-only threat/reward preview., Derive a UI-only threat tier and reward preview for an enemy. This is…, Exploration and movement verbs plus the enemy/encounter view models., Return the max find rarity index allowed by the current area's danger., Build the standard prose context (realm rank, morality, season, ...). (+14 more)

### Community 26 - "SystemsMixin"
Cohesion: 0.10
Nodes (16): Any, The seeded named foe that champions the tournament at this location., Tournaments are held where sects gather (academies, sect halls, arenas)., Actions that wrap the alchemy, Dao, tournament, and secret-realm systems., Open the secret realm at the current location (if one opens here)., Step into the next room of the active realm, resolving its kind., Harvest a herb at the current location (gated by its herb table)., Abandon the realm, returning to the overworld. (+8 more)

### Community 27 - "SectSystem"
Cohesion: 0.16
Nodes (13): Any, Return ``{allowed, reason}`` for joining ``sect_id`` right now., Return the highest story tier the player has visited (0 when unset)., Join a sect: assign ``player.path`` and report the starting rank., Buy a technique from a sect's hall, paying its currency cost. The sect must be…, Return a sect's story tier (defaulting to 1 for untagged data)., Return a brief for the player's current sect, or ``{}`` when none. Includes the…, Lists location sects, resolves joining them, and sells their techniques. (+5 more)

### Community 28 - "normalize_available_systems.py"
Cohesion: 0.67
Nodes (3): main(), _normalise(), Normalise ``locations.json`` ``available_systems`` to implemented verbs. The…

### Community 29 - "GameDataRegistry"
Cohesion: 0.12
Nodes (17): _by_id(), GameDataRegistry, Any, Return the ids of every auto-generated technique-manual item. One manual is…, Index a list of ``{"id": ...}`` entries by their id (last write wins)., Immutable snapshot of every static content collection., _manual_to_skill(), Every skill must be obtainable through at least one acquisition path. Technique… (+9 more)

### Community 30 - "RefineSystem"
Cohesion: 0.24
Nodes (7): Any, Consume a recipe's inputs and produce its output item., Return a non-empty error dict when the player's realm is too low., Herb-to-pill recipe graph with input checking and output production. Recipes…, Return every recipe for the UI, annotated with its realm gate. When ``player``…, Return a raw recipe definition, or ``None`` if unknown., RefineSystem

### Community 31 - "EquipmentSystem"
Cohesion: 0.19
Nodes (7): EquipmentSystem, Any, Fold in the strongest met set-bonus threshold for each equipped set., Validates equipment actions and aggregates equipped modifiers., Return the item's durability ceiling, or 0 when it has no durability model., Reduce each equipped destructible item's durability by ``amount``. Returns…, Restore a piece of equipped, destructible gear to full durability for gold.…

### Community 32 - "LifespanSystem"
Cohesion: 0.14
Nodes (11): LifespanSystem, Any, Return the current season, derived from whole years elapsed since spawn., Compute maximum lifespan, advance age, and detect death by old age., Return the current maximum lifespan in years, or ``None`` if immortal. Lifespan…, Return the age (in years) a given action consumes., Advance the player's age by the action's time cost; return years added. When…, Return years left before old-age death, or ``None`` when immortal. (+3 more)

### Community 33 - "MetaService"
Cohesion: 0.13
Nodes (15): MetaService, Any, Path, Append a run record to the chronicle, keeping the most recent only., Return the run chronicle (most recent last)., Record an unlock id once; return ``False`` if already owned., Flag that at least one run has ended by retirement/ascension (C.7)., Return the full meta-save snapshot (memory + chronicle). (+7 more)

### Community 34 - "validate_all_game_data"
Cohesion: 0.10
Nodes (37): Load every content collection from the ``data/`` directory., Central Validation, Rarity Ladder, Validate every static content collection and return the collected result., validate_all_game_data(), test_demonic_herbs_grow_only_in_demon_continent(), test_herbs_carry_rarity(), End-to-end validation of the shipped game data. The first test is the real… (+29 more)

### Community 35 - "MoralitySystem"
Cohesion: 0.12
Nodes (22): Character service. Single authority for "who is here, and what can I do with…, MoralitySystem, Any, Morality system. Interprets a player's morality score into a named band…, Reads morality bands from data and interprets/adjusts a morality score., Clamp a score into the configured morality range., Return the band definition a score falls into., Return just the band id for a score. (+14 more)

### Community 36 - ".__init__"
Cohesion: 0.11
Nodes (13): LootSystem, Rolls loot tables and grants successful drops., Any, Talent tier ladder lookups. The talent ladder is a data-driven, two-track…, Resolve entries from the two-track talent tier ladder., Return UI-safe views for every ladder entry, ordered by tier index., Return the UI-safe view for a tier index, or ``None`` when unknown., Return the UI-safe view for a stable ladder ID, or ``None`` when unknown. (+5 more)

### Community 37 - "test_combat_system.py"
Cohesion: 0.33
Nodes (22): _combat(), _enemy(), _player(), Tests for combat skill-effect resolution and passive stat derivation., _skill(), test_buff_attack_passive_raises_effective_attack(), test_counter_damages_attacker(), test_crit_chance_passive() (+14 more)

### Community 38 - "SellSystem"
Cohesion: 0.16
Nodes (16): Any, Sell (liquidation) rules. Converts owned items/equipment/manuals into gold at a…, Validates and performs selling owned items for gold., Return the gold worth of an item (before the sell-rate discount)., Return what one unit of ``item`` sells for in gold (min 1)., Sell ``quantity`` of an owned item for gold; remove it from inventory., SellSystem, _items() (+8 more)

### Community 39 - "seed_techniques.py"
Cohesion: 0.20
Nodes (20): _load(), main(), Path, Seed the talent-refining resource (``talent_refining_elixir``) into the world.…, seed_enemies(), seed_masters(), seed_pools(), seed_shops() (+12 more)

### Community 40 - "test_results.py"
Cohesion: 0.15
Nodes (17): ErrorResult, MessageResult, A successful move, carrying the destination's UI-safe view., A plain informational message., A rejected command, tagged with a stable ``reason`` code., Outcome of resting: HP/Qi recovered and the new totals., Outcome of stabilising the body cultivation foundation., RestResult (+9 more)

### Community 41 - "load_collection"
Cohesion: 0.12
Nodes (24): _load_optional_collection(), _load_optional_object(), Central registry of all static game data. One validated source of truth for the…, Load a JSON object file, returning ``{}`` when it does not exist yet., Load a list collection, returning ``[]`` when the file/folder is absent., load_collection(), Any, Load a list-collection by logical ``name``. If a directory ``data/<name>/``… (+16 more)

### Community 42 - "StartingFateSystem"
Cohesion: 0.20
Nodes (8): Any, Roll and view Martial Talent / Body Talent starting data., Roll one Martial Talent and one Body Talent from positive weights., Return a UI-safe Martial Talent data view by stable ID., Return a UI-safe Body Talent data view by stable ID., Return the UI-safe upgrade targets a talent may currently upgrade into.…, Return whether ``target_id`` is a valid upgrade from ``talent_id``., StartingFateSystem

### Community 43 - "DispatchMixin"
Cohesion: 0.14
Nodes (15): DispatchMixin, Any, Action routing: the public ``process_action`` contract and dispatch tables., Routes a structured action to the right handler for the current mode., Exploration-mode actions, keyed by action name. Handlers look attributes up on…, Process a structured command and return a structured result. Every result is…, Flag the session as finished and return the quit result., Attach a fallback narrative line to any result that lacks one. Results that… (+7 more)

### Community 44 - "CultivationSystem"
Cohesion: 0.06
Nodes (28): CultivationSystem, Any, Each point of comprehension above the starting 10 grants +0.5% base…, Advance only Essence Gathering progress., Attempt a Body Transformation breakthrough without touching essence progress., Attempt an Essence Gathering breakthrough without touching body progress., Handles independent body and essence cultivation tracks., Reduce body cultivation strain and restore foundation stability. (+20 more)

### Community 45 - "EncounterSystem"
Cohesion: 0.07
Nodes (27): EncounterSystem, foe_power(), Any, Return a foe's single-number threat: HP plus weighted offence/defence. Mirrors…, Read ``key`` from a mapping or object, returning ``None`` when absent., Builds pending exploration encounters and rolls the outcome of choices., Return a config section merged over its defaults., Return the UI label/hint for a choice id. (+19 more)

### Community 46 - "ViewsMixin"
Cohesion: 0.11
Nodes (15): Any, The wanderer's codex: secret realms, sects, and faction arcs. Pure read-only…, Compact living-world summary for the main state payload (E.1-E.5)., Return ``True`` until the player quits., Return the cross-run meta view: Ancestral Memory, chronicle, and origins. The…, Return the legacy unlock tree with live purchase state (C.5). Reachable mid-run…, Set the player's display name (used by character creation in the UI)., Rename the living cultivator and report the accepted name. A display name is… (+7 more)

### Community 47 - "RelationshipSystem"
Cohesion: 0.20
Nodes (9): Any, Record a notable player action (and optional memory flag) for an NPC., Return the NPC's state plus its derived interaction tier., Creates, adjusts, and interprets per-NPC relationship state., Return the NPC's state, creating neutral defaults if it is missing. NPCs never…, Return the interaction tier id a relationship_score falls into., Return ``True`` when ``tier_id`` is at least ``minimum`` in tier order. Tier…, Apply clamped deltas to one NPC's emotional variables. (+1 more)

### Community 48 - "test_locations_data.py"
Cohesion: 0.16
Nodes (27): _gate(), _locations(), _player(), Structural tests for the shipped world map (``data/locations.json``). These…, Map realm ids and display names (lowercased) to their order value., Return the unlock order a location demands on one cultivation track., An unresolvable gate is silently ignored, so the location is walk-in., Negative test: the shipped "Nine Stars Dao Palace" typo must be caught.… (+19 more)

### Community 49 - "GameEngine"
Cohesion: 0.05
Nodes (80): GameEngine, Coordinates systems, manages state, and processes actions. The action handlers…, Build a fully-loaded engine from the central data registry. ``registry`` may be…, Raise the player's story-tier progress to include ``location_id``. Called on…, Engine Contract, EventType Contract, Engine State Ownership, GameEngine split into core/engine/ mixins (+72 more)

### Community 50 - "ProgressionMixin"
Cohesion: 0.12
Nodes (19): ProgressionMixin, Any, Cultivation, talents, closed-door seclusion, and time advancement., Notify quests on a successful breakthrough and attach narrative prose., Spend an action's time cost on the one clock, then enforce lifespan (TM.1).…, The verbs that grow the cultivator and advance the calendar., Return the player's known techniques (active + passive)., Return the player's Martial/Body talents and their upgrade paths. Each upgrade… (+11 more)

### Community 51 - "OriginSystem"
Cohesion: 0.15
Nodes (10): OriginSystem, Any, Origin system. Starting backgrounds (``data/origins.json``) shape a fresh…, Resolves and applies starting origins., Return every origin definition (in data order)., Return an origin definition, or ``None`` if unknown., Return an origin's Ancestral Memory cost (0 if unknown)., Return the free starting origin (first cost-0 origin, else the first). (+2 more)

### Community 52 - "load_json"
Cohesion: 0.12
Nodes (25): load_json(), JSON content loading. Loads data files from the sibling ``data/`` directory…, Load and parse a JSON file from the data directory., Tests that data files load and parse as expected., test_body_cultivation_realms_load(), test_body_talents_load(), test_equipment_loads(), test_essence_cultivation_realms_load() (+17 more)

### Community 53 - "cultivation.py"
Cohesion: 0.16
Nodes (11): BodyCultivationState, BreakthroughResult, CultivationState, EssenceCultivationState, Any, Pure cultivation state models. These dataclasses hold persistent cultivation…, Combined cultivation state for a character., Structured result for a cultivation breakthrough attempt. (+3 more)

### Community 54 - "CultivationService"
Cohesion: 0.30
Nodes (3): CultivationService, Any, Coordinates cultivation actions for registered players.

### Community 55 - "test_encounters.py"
Cohesion: 0.12
Nodes (40): _engine(), _hazard(), _install(), _option(), Choice-driven exploration encounters (ROADMAP B.9). Covers the contract the…, A scripted RNG: ``chance`` answers from a script, everything else defaults., Park a crafted encounter as the pending one, bypassing the roll., StubRNG (+32 more)

### Community 56 - "RNG"
Cohesion: 0.11
Nodes (36): default_world_state(), Living-world simulation (ROADMAP E.1-E.5). One pure system evolves the world on…, Build a fresh, seed-derived world state for a new run., A thin, seedable wrapper around :class:`random.Random`., Reseed the generator (useful to reset state between tests)., Return a random integer N such that ``low <= N <= high``., Return ``True`` with the given probability (0.0 - 1.0)., Return a uniformly random element from ``items``. (+28 more)

### Community 57 - "ValidationResult"
Cohesion: 0.08
Nodes (56): Collection validators for characters, factions, prose and the legacy tree.…, A.6: glossary entries must be well-formed, unique per slot, and slot-valid., Lint narrative templates (structure, slots, when-clauses, coverage)., Validate the legacy unlock tree (ROADMAP C.5). Checks tier/node structure,…, Check relationship/morality gates and relationship rewards reference real…, _validate_character_enemy_links(), _validate_character_hooks(), _validate_character_reaction_keys() (+48 more)

### Community 58 - "Essence Gathering Track"
Cohesion: 0.29
Nodes (8): Body Transformation Track, Breakthrough Gating, Cultivation Strain, Essence Gathering Track, Foundation Stability, Lifespan, Starting Fate, Talent Ladder

### Community 59 - "EncountersMixin"
Cohesion: 0.08
Nodes (23): EncountersMixin, Any, Drop transient combat/encounter state (a run ending, or a load)., Return the danger level of the area the player is exploring., Return the current location's encounter pool (empty when unmapped)., The player's single-number fighting weight, in the same units as a foe's.…, Classify a foe relative to the player: Low, Moderate, High, or Deadly., Handle actions while an exploration encounter waits on a choice. (+15 more)

### Community 60 - "._build_manual_items"
Cohesion: 0.40
Nodes (3): Any, Convert a technique-manual entry into a consumable learn-skill item., Auto-generate one learn-skill manual per skill, applying data overrides. Every…

### Community 61 - "test_relationship_system.py"
Cohesion: 0.39
Nodes (8): Tests for the relationship system's per-NPC state, clamping, and tiers., _system(), test_adjust_clamps_and_reports_applied_delta(), test_ensure_creates_neutral_defaults(), test_meets_min_tier_orders_tiers(), test_relationship_score_can_go_negative_into_hostile(), test_remember_records_each_action_once(), test_tier_progression()

### Community 62 - ".calculate_derived_cultivation_stats"
Cohesion: 0.20
Nodes (5): Calculate current Body Transformation stat contribution., Calculate current Essence Gathering stat contribution., Calculate derived stats from both tracks without persisting them., Return balance status from relative realm order., Estimate overall breakthrough safety from foundations and resources.

### Community 63 - "expand_alchemy.py"
Cohesion: 0.29
Nodes (12): build_gathering(), build_herbs(), build_recipes(), _load_json(), main(), Any, Expand the alchemy + secret-realm content breadth (ROADMAP F.1 / D.2 follow-…, Append new herbs to ``items`` in place; return the updated list. (+4 more)

### Community 64 - "4. Programmes"
Cohesion: 0.05
Nodes (42): 0. How to read this file, 1. What 10/10 means (the rubric), 2. Scoreboard (current → target 10), 3. Phases, 4. Programmes, 5. Global acceptance gates (apply to every task), 6. Open decisions, 7. Evidence index (2026-09-13) (+34 more)

### Community 65 - "lint_narrative_templates"
Cohesion: 0.09
Nodes (32): _lint_brace_artifacts(), _lint_gamey_terms(), _lint_glossary_slots(), lint_narrative_templates(), _lint_when(), load_glossary_terms(), Any, Lint checks for ``data/narrative_templates.json`` (ROADMAP A.7, A.6). A single… (+24 more)

### Community 66 - "CombatSystem"
Cohesion: 0.08
Nodes (16): CombatSystem, Resolves individual combat rounds between the player and an enemy., Reset the player's insight pool and combo chain at the start of a fight., Apply ``skill``'s effect and return the turn events describing it., Enemy acts (or skips when stunned), then its timed effects tick. With a foe-…, Apply per-turn enemy effects (dot) and decrement remaining turns., Apply per-turn player effects (enemy-inflicted poison) once a round., Return the stance role the chain currently expects, or ``None``. ``None`` means… (+8 more)

### Community 67 - "test_roguelike_meta.py"
Cohesion: 0.24
Nodes (11): Meta-save service. Persists *cross-run* state that outlives any single…, _meta(), Roguelike legacy & meta (ROADMAP C.1-C.4). Covers the permadeath default + run…, test_chronicle_records_runs_and_stays_bounded(), test_get_meta_state_annotates_affordability(), test_hardcore_death_ends_run_and_banks_meta(), test_memory_adds_and_spends(), test_memory_persists_across_instances() (+3 more)

### Community 68 - "test_equipment_system.py"
Cohesion: 0.35
Nodes (10): _bind(), _make_system(), Tests for data-driven equipment slots, requirements, and modifiers., test_artifact_slot_compatibility_and_rejection(), test_equip_item_success_does_not_mutate_base_stats(), test_flying_sword_slot_restriction(), test_replacement_overwrites_slot_once(), test_requirement_failure_keeps_equipment_unchanged() (+2 more)

### Community 69 - "test_player_identity.py"
Cohesion: 0.07
Nodes (30): _manifest(), _png_header(), _png_pixels(), parametrize, Path, Player identity: the cultivator's name (engine-owned) and portrait (client).…, The manifest is the roster's other half: it splits painted from generated., A painting must still be the bytes the manifest says were imported. (+22 more)

### Community 70 - "_service"
Cohesion: 0.60
Nodes (5): _player(), _service(), test_reward_gates_on_morality_band(), test_reward_gates_on_relationship_tier(), test_spar_gates_on_morality_band()

### Community 71 - "economy_balance.py"
Cohesion: 0.12
Nodes (30): build_ledger(), _combat_stone_rate(), _enemies_by_id(), _hall_expenses(), _locations(), _pool_stone_rate(), Any, _quest_stone_total() (+22 more)

### Community 72 - "TurnEvent"
Cohesion: 0.12
Nodes (15): Player performs a basic attack, then the enemy retaliates if alive., Resolve the opening blow of a foe that took the player unawares. Used when an…, Resolve a lighter press from a formation foe the player is not facing. Extra…, Resolve a damage-dealing skill hit and return its event., Execute a B.8 foe intent (technique/ability/attack/guard) as one event., Resolve a foe's active technique with its chain bonus, then bank it., Choose the enemy's action: foe AI intent when installed, else raw rolls., Grant insight for a successful exchange and return the amount gained. (+7 more)

### Community 73 - "test_starting_fate_system.py"
Cohesion: 0.53
Nodes (5): _make_system(), Tests for starting talent roll helpers., test_talent_views_do_not_expose_roll_weights_or_upgrade_options(), test_weighted_roll_only_returns_rollable_entries(), test_weighted_roll_returns_valid_talent_ids()

### Community 74 - "gen_missing_location_art.py"
Cohesion: 0.09
Nodes (94): NamedTuple, Point, Random, RGB, _banner(), _boat(), _broadleaf(), Canvas (+86 more)

### Community 75 - "seed_shops.py"
Cohesion: 0.48
Nodes (6): dump(), _equipment_price(), load(), main(), Any, Seed additional shops so most regions have a market. Until this script exists,…

### Community 76 - "ui_theme.py"
Cohesion: 0.33
Nodes (5): hex_to_rgb(), hp_color(), Martial Path UI theme - dark charcoal / gold design system. The palette…, Convert a ``#RRGGBB`` string into an ``(r, g, b)`` tuple (0-255)., Return the HP bar colour for a fill ratio (0.0-1.0).

### Community 77 - "Phase 1 - MVP (core loop sings)"
Cohesion: 0.33
Nodes (6): Epic G: Balance & Polish, Epic D: Campaign + Endless Post-game, Epic B: Dao & Philosophy Combat, Epic A: Procedural Narrative Engine, Epic C: Roguelike Legacy & Meta, Phase 1 - MVP (core loop sings)

### Community 78 - "test_import_smoke.py"
Cohesion: 0.33
Nodes (5): _module_names(), parametrize, Smoke test: every module under ``game/`` imports cleanly. Catches syntax…, Return the dotted module name for every ``.py`` file under ``game/``., test_game_module_imports()

### Community 79 - "test_json_parse_smoke.py"
Cohesion: 0.40
Nodes (5): _json_files(), parametrize, Path, Smoke test: every JSON file under ``game/data/`` parses. A single malformed…, test_data_json_parses()

### Community 80 - "seed_talent_upgrades.py"
Cohesion: 0.47
Nodes (5): main(), Path, Seed ``upgrade_options`` into the Martial and Body talent tracks. Each talent…, resource_quantity(), seed()

### Community 81 - "WorldSimulationSystem"
Cohesion: 0.11
Nodes (14): Any, Return the gameplay modifiers for ``season`` (defaults for unknowns)., Advance the world by ``years`` (fractional); return a tick report. The report…, Sects refill fallen seats: the dead are succeeded by new disciples. The roster…, Sect power tracks its living members' ranks, smoothed (E.2). Power is…, Market pressure nudges the price multiplier each tick (E.3). Two bounded…, Create a state-backed rumor about the world; return it (or ``None``)., Mint one rumor per tick if the world has material to talk about. (+6 more)

### Community 82 - "godot_ui_audit.py"
Cohesion: 0.13
Nodes (25): canvas_extents(), click_node(), click_text(), compute_transform(), dump_texts(), editor_json(), find_node(), flat_nodes() (+17 more)

### Community 83 - "run_backend.py"
Cohesion: 0.40
Nodes (3): _ensure_std_streams(), Standalone entry point for the packaged Martial Path backend. Serves the…, Guarantee ``sys.stdout``/``sys.stderr`` exist. A windowed PyInstaller build…

### Community 100 - "test_api_server.py"
Cohesion: 0.18
Nodes (27): BaseModel, ActionRequest, new_game(), NewGameRequest, process_action(), Forward a structured command to the engine and return its result dict., Reset the in-process engine and return the initial state., A command for the engine. ``action`` is required (an ``Action`` name such as… (+19 more)

### Community 101 - "Prompt sheet"
Cohesion: 0.07
Nodes (27): 10. `wandering_swordsman` - Wandering Swordsman (male), 11. `sect_patriarch` - Sect Patriarch (male), 12. `sword_maiden` - Sword Maiden (female), 13. `nine_tailed_fox` - Nine-Tailed Fox (female), 14. `jade_sect_mistress` - Jade Sect Mistress (female), 15. `moon_palace_fairy` - Moon Palace Fairy (female), 16. `phoenix_heiress` - Phoenix Heiress (female), 17. `poison_valley_disciple` - Poison Valley Disciple (female) (+19 more)

### Community 106 - "CombatMixin"
Cohesion: 0.16
Nodes (14): CombatMixin, Any, The combat turn loop and its cleanup/penalty helpers., Public views of the foes still standing, in the order they joined., Combine every foe put down in this bout into one loot table. Extra formation…, Validate and resolve an active-skill activation in combat., Use an item during combat; this consumes the player's turn., Resolve the consequences of a finished fight and leave combat mode. (+6 more)

### Community 107 - "WorldMixin"
Cohesion: 0.13
Nodes (15): Any, Attach a display name to a rumor reveal's concrete subject., List the live rumors (bounded, newest last)., Learn a rumor, revealing its concrete subject (sect/location/npc)., Attach an unlearned rumor's reveal to a talk result (hearsay in chat)., Full world snapshot: year, season effects, sects, market, rumors., Advances the world with the calendar and applies world state to play., Tick the world by the years a result reports (e.g. closed-door). (+7 more)

### Community 108 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native AGENTS.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 109 - "FoeAI"
Cohesion: 0.19
Nodes (20): FoeAI, Chooses the enemy's combat action from dao, pressure, and stance state., Advance (or reset) the foe's stance bank after it acts. Mirrors the player's…, FakeDao, make_foe(), make_player(), Any, Foe AI (ROADMAP B.8): enemies fight with dao, pressure, and stances. Pure AI:… (+12 more)

### Community 110 - "TravelService"
Cohesion: 0.15
Nodes (13): Encounter Pools, Location Schema, Cultivation Gating, Travel Graph, Any, Return ``True`` when the player's realm meets ``minimum`` (fail-open on…, Map realm ids and display names (lowercased) to their order value., Validates and performs travel between connected locations. (+5 more)

### Community 111 - "LegacySystem"
Cohesion: 0.11
Nodes (15): LegacySystem, Any, Legacy system (ROADMAP C.5 + C.6). Two pure responsibilities, both rule-only…, True when too few earlier tiers hold purchases for this tier., Derive the run's world variation from the seed. Pure derivation over a pre-…, Resolves the cross-run unlock tree and the world-seed report., Return every tier definition (in data order)., Return one unlock node by id (with its ``tier_id``), or ``None``. (+7 more)

### Community 112 - "Location Art Prompts"
Cohesion: 0.09
Nodes (22): 10. `coral_prison_atoll` — Coral Prison Atoll, 11. `sea_of_mist_expanse` — Sea of Mist Expanse, 12. `furnace_pillar_city` — Furnace Pillar City, 13. `emberfall_citadel` — Emberfall Citadel, 14. `zen_wilds_shrine` — Zen Wilds Shrine, 15. `rune_temple_undercroft` — Rune Temple Undercroft, 16. `gate_array_approach` — Gate Array Approach, 1. `stream_fisher_wharf` — Stream Fisher Wharf (+14 more)

### Community 113 - "CampaignMixin"
Cohesion: 0.12
Nodes (13): CampaignMixin, Any, Lift the essence track's final cap once the endless road opens. The cultivation…, Inflate a foe for endless depth: HP/attack/defense/reward scale., Apply an endless room's ``scale`` to the foe about to spawn., Wrap realm completion with the endless depth reward (D.5)., The campaign ending this run earned (``None`` if unfinished)., Compact campaign/post-game summary for the main state payload. (+5 more)

### Community 114 - "DebateMixin"
Cohesion: 0.15
Nodes (15): DebateMixin, Any, Snapshot what the player puts on the line before the oath is sworn., Route a stance action while a debate is active., Close the debate and resolve any spirit-oath stakes., Apply the spirit-oath's asymmetric stakes for the debate's outcome. * Won: the…, UI-safe snapshot of the active debate (``None`` outside one)., Walk away from a debate (breaching an oath duel if one is sworn). (+7 more)

### Community 115 - "test_dead_content.py"
Cohesion: 0.10
Nodes (19): collect_issues(), Flatten a report into ``(category, message)`` pairs (empty = clean)., ROADMAP Phase 3 G.2: dead-content sweep acceptance criteria. Two things are…, Regression guard: legacy ``unlock.min_stage`` gates used to be unsatisfiable.…, The (category, message) contract the central validator consumes., _report(), _stub_service(), test_breakthrough_aid_steadies_the_foundation() (+11 more)

### Community 116 - "seed_world_content.py"
Cohesion: 0.17
Nodes (22): Stocking a rack must not leave a trap option in either direction. Regression:…, test_seed_tool_refuses_a_rack_both_ways_round(), _clamp_rank(), _equipment_rank(), _item_rank(), _item_worth(), load(), main() (+14 more)

### Community 117 - "EventSystem"
Cohesion: 0.19
Nodes (11): EventSystem, Any, Surface hazardous ground, preferring the location's own hazard list. An empty…, Produces weighted random encounters from data-driven, location-scoped pools., Set the seasonal multiplier applied to the COMBAT encounter weight., Pick and return the next exploration encounter descriptor.…, _player(), Tests for location-scoped encounter selection. (+3 more)

### Community 118 - "test_content_breadth.py"
Cohesion: 0.15
Nodes (21): _ids(), _load_json(), load_json_collection(), _locations(), ROADMAP Phase F breadth: reachability, arc structure, and cross-wiring. Guards…, New tier 5-6 techniques ship seeded: each is buyable from its hall., test_arc_quests_reference_real_targets(), test_arc_rewards_reference_real_skills_and_items() (+13 more)

### Community 119 - "SaveRepository"
Cohesion: 0.15
Nodes (12): Any, Path, Reads and writes raw JSON save slots on disk., The directory save slots are stored in., Sanitise a slot name so it can never escape the save directory., Return the on-disk path for ``slot`` (sanitised)., Serialise ``payload`` to ``slot`` verbatim and return the file path., Load and parse ``slot``; raise ``FileNotFoundError`` when absent. (+4 more)

### Community 120 - "TestActs23"
Cohesion: 0.13
Nodes (8): complete_chain(), engine(), fixture, Full campaign + post-game (ROADMAP D.3-D.5). D.3 -- Acts 2-3 chain (faction…, The Act-Two rekindling reopens dao choice, one change per window., Mark a chain of quests completed exactly as the engine would., Faction conflict -> dao re-awakening -> realm war, in that order., TestActs23

### Community 121 - "test_sect_system.py"
Cohesion: 0.27
Nodes (18): _player(), Tests for sect joining, path assignment, join gating, tiers, and halls., _system(), test_join_gated_by_body_realm(), test_join_gated_by_location(), test_join_gated_by_max_reputation(), test_join_gated_by_min_reputation(), test_join_result_reports_tier() (+10 more)

### Community 122 - "Martial Path — Shared Project Rules (inherited by every agent)"
Cohesion: 0.12
Nodes (15): Gatekeeper protocol (summary), Martial Path — Agent Fleet, Models (Freebuff), Notes, Spawn graph, The agents, Usage, Architecture (hard, one-directional) (+7 more)

### Community 123 - "world_checks.py"
Cohesion: 0.18
Nodes (16): _check_level(), _check_map_position(), _connections(), _is_probability(), Any, Collection validators for locations, the map, and the encounter layer. Split…, Check enemy ``abilities`` entries are well-formed., Validate ``data/encounters.json`` (the choice-driven encounter layer). The… (+8 more)

### Community 124 - "test_quest_system.py"
Cohesion: 0.20
Nodes (13): Any, Build an item from a raw data-file entry., _inventory(), Tests for the data-driven quest/journal system., test_auto_start_quests_are_active_others_locked(), test_check_unlocks_honours_reputation_and_location(), test_completed_quest_ignores_further_events(), test_completing_quest_unlocks_chained_quest() (+5 more)

### Community 125 - "TrainerSystem"
Cohesion: 0.30
Nodes (6): Any, Lists location trainers and resolves paid technique learning., Return summary data for trainers available at a location., Return a trainer's teachable techniques visible to the player., Learn a technique from an available trainer, spending its currency cost., TrainerSystem

### Community 126 - "test_codex.py"
Cohesion: 0.13
Nodes (8): codex(), fixture, CODEX action: the wanderer's codex (secret realms, sects, faction arcs)., A tier-6 realm stays undiscovered until the player reaches tier 6., Unlocking the first valleys quest shows as active in the arc., test_codex_arcs_show_progress(), test_codex_lists_every_secret_realm(), test_codex_realms_gated_by_story_tier()

### Community 127 - "test_meta_depth.py"
Cohesion: 0.22
Nodes (14): _meta(), Meta depth (ROADMAP Phase 2 C): legacy unlock tree, world seed, ascension. C.5…, test_dominant_sect_gets_reputation_discount_and_listing(), test_endless_flag_round_trips_through_save(), test_meta_state_carries_unlock_tree(), test_retire_banks_scaled_reward_and_records_ascension(), test_retire_refused_below_ascension_threshold(), test_retire_reward_beats_death_reward_at_same_rank() (+6 more)

### Community 128 - "seed_enemy_pools.py"
Cohesion: 0.24
Nodes (14): _closeness(), _combat_entries(), load(), main(), Any, Seed encounter pools with every random enemy that has no home (ROADMAP G.2).…, Return (body realm ids low->high, essence realm ids low->high)., Map an enemy's cultivation realm onto the 0-10 location danger scale. (+6 more)

### Community 129 - "gui_interface.py"
Cohesion: 0.21
Nodes (9): main(), Graphical entry point - the composition root for the PySide6 UI. Like…, Construct the Qt application, engine, and window, then run the UI loop., martial_path_icon_path(), PySide6 graphical frontend. This is an alternative UI layer that drives the…, Return the absolute path to the shared Martial Path app icon, if present. The…, Build the global Qt Style Sheet from the theme palette., _stylesheet() (+1 more)

### Community 130 - "Martial Path — A Cultivation Text RPG"
Cohesion: 0.15
Nodes (12): Command-line interface (no dependencies), Commands, Example gameplay, Extending content, Graphical interface (PySide6), HTTP API (for a Godot or web frontend), Layered architecture, Martial Path — A Cultivation Text RPG (+4 more)

### Community 131 - "currency.py"
Cohesion: 0.17
Nodes (12): currency_amount(), normalise_price(), Any, Shared currency helpers. Purchases (shops) and technique tuition (trainers)…, Return only the supported, positive currency amounts from a raw price., Return how much of ``currency`` the player currently holds., Return the missing amount per currency the player cannot afford., Deduct an affordable ``price`` from the player's wallet/inventory. (+4 more)

### Community 132 - ".choose_action"
Cohesion: 0.17
Nodes (7): Any, Return the foe's intended action for this round. The dict carries the intent…, A technique the foe knows carrying the wanted ``stance`` role., Roll the foe's data-driven abilities, scaled by aggression., How hard ``enemy`` presses this round (counter graph + wounds)., True when the player's dao counters the foe's (its aggression drops)., The stance the foe pursues this round, or ``None`` for mooks. The stance…

### Community 133 - "DESIGN.md — Martial Path (Godot frontend)"
Cohesion: 0.17
Nodes (11): Color (the lacquer-and-gold ramp), Craft floor (project-specific absolutes), DESIGN.md — Martial Path (Godot frontend), Form grammar, Layout grammar, Motion, Platform, Type (+3 more)

### Community 134 - ".from_save_dict"
Cohesion: 0.18
Nodes (8): empty_equipment_slots(), _equipment_from_save(), Any, Return a fallback display title for the current cultivation state., Return a UI-safe snapshot of the full player sheet., Return a faithful, round-trippable snapshot for the save system., Reconstruct a Player from a :meth:`to_save_dict` snapshot., test_player_dao_round_trips_through_save()

### Community 135 - "._player_damage_parts"
Cohesion: 0.17
Nodes (6): Suppression + Dao-matchup multiplier for the attacker's outgoing damage., Suppression multiplier for the defender's effective defense., The arithmetic behind a player hit: scale, then defense (CB.1)., Player's attack value scaled by realm pressure and Dao matchup., Damage's own arithmetic, split out so a hit can be explained (CB.1)., Compute damage with light variance; always at least 1.

### Community 136 - "Procedure"
Cohesion: 0.17
Nodes (11): 1. Orient (before touching code), 2. Gather context (read before editing), 3. Plan in dependency order, 4. Implement, respecting the architecture, 5. Verify continuously, 6. Update documentation, 7. Summarise the change (instruction 12), Guardrails (+3 more)

### Community 137 - "Product"
Cohesion: 0.17
Nodes (11): Accessibility & Inclusion, Brand Commitments, Capabilities and Constraints, Evidence on Hand, Operating Context, Platform, Positioning, Product (+3 more)

### Community 138 - "test_trainer_system.py"
Cohesion: 0.30
Nodes (11): Tests for data-driven skill trainers (technique masters)., _skills(), _system(), test_learn_already_known_skill_is_rejected(), test_learn_spends_currency_and_teaches(), test_learn_unoffered_skill_is_rejected(), test_learn_without_funds_is_rejected(), test_path_locked_technique_requires_matching_path() (+3 more)

### Community 139 - "economy_tune.py"
Cohesion: 0.41
Nodes (11): load(), main(), Economy tuning pass (one-shot). Rebalances the tier 5-6 spirit-stone economy so…, Give every foe in a tier 5-6 zone the zone's own stone drop. A zone's rate is…, save(), _stone_drop_of(), tune_enemies(), tune_quests() (+3 more)

### Community 140 - "test_secret_realm.py"
Cohesion: 0.22
Nodes (9): Procedural secret realm (seeded dungeon) generator. A secret realm is a…, Procedural secret realm (ROADMAP D.2)., _rooms(), test_completing_realm_grants_final_reward(), test_different_seed_produces_different_layout(), test_enter_realm_requires_the_right_location(), test_realm_advance_resolves_treasure_then_combat(), test_realm_leave_clears_realm() (+1 more)

### Community 141 - "test_travel_service.py"
Cohesion: 0.44
Nodes (10): _player(), Tests for the travel service: adjacency, requirement gating, and moves., _service(), test_already_there_is_rejected(), test_available_destinations_flag_reachable_and_locked(), test_body_realm_requirement_allows_when_met(), test_body_realm_requirement_blocks_underleveled_travel(), test_required_item_and_reputation_gate_vault() (+2 more)

### Community 142 - "complete_v4_swap.py"
Cohesion: 0.36
Nodes (10): godot_processes(), main(), Path, Complete the Godot AI v3 -> v4 plugin swap by hand. The signed migration…, Live Godot editor/player PIDs as `name:pid`. Plain `tasklist` plus a substring…, Every payload file must match the signed inventory exactly., read_plugin_name(), sha256_file() (+2 more)

### Community 143 - "with_article"
Cohesion: 0.24
Nodes (8): The newer MVP systems: alchemy, Dao awakening, tournament, secret realm., indefinite_article(), Small text helpers shared by the systems that write player-facing English. The…, Return ``A`` or ``An`` for ``word``. The test is the first letter rather than…, Return ``name`` prefixed with the right indefinite article.…, with_article(), Names are data, so the article has to be chosen at runtime. A hard-coded "A…, test_every_enemy_name_gets_a_grammatical_article()

### Community 144 - "GatherSystem"
Cohesion: 0.22
Nodes (6): GatherSystem, Per-location herb tables with a seeded weighted roll., Return ``True`` when herbs can be gathered at ``location_id``., Return the weighted herb table for a location (falling back to default)., Return a single gathered herb id from the location's table, or ``None``., Epic F: Content Breadth

### Community 145 - "Layer Responsibilities"
Cohesion: 0.20
Nodes (9): 01 — Architecture Rules, `adapters/`, `core/`, `data/`, Dependency Rules, Layer Responsibilities, `services/`, `tests/` (+1 more)

### Community 146 - "test_story_tiers.py"
Cohesion: 0.29
Nodes (5): _characters(), _player(), Story-tier progression: location tiers, player progress, sect + encounter…, test_character_service_hides_characters_below_their_min_story_tier(), test_character_service_still_shows_untagged_characters()

### Community 147 - "test_talent_system.py"
Cohesion: 0.33
Nodes (9): _make_system(), Tests for the two-track talent tier ladder., test_every_tier_carries_both_track_names_realm_and_lifespan(), test_immortal_tiers_use_null_lifespan_sentinel(), test_ladder_covers_twenty_tiers_plus_apex(), test_shipped_talent_ladder_is_valid(), test_tier_view_resolves_shared_index_to_both_tracks(), test_unknown_lookups_return_none() (+1 more)

### Community 148 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 149 - "Ponytail"
Cohesion: 0.22
Nodes (8): Boundaries, Intensity, Output, Persistence, Ponytail, Rules, The ladder, When NOT to be lazy

### Community 150 - ".from_dict"
Cohesion: 0.22
Nodes (6): Any, Spawn a fresh enemy instance from a template entry., Return a UI-safe snapshot of the enemy's visible stats., _enemy_with(), test_enemy_poison_ability_applies_player_dot(), test_enemy_stun_ability_stuns_player()

### Community 151 - ".use_item"
Cohesion: 0.22
Nodes (5): Any, Add ``count`` of an item to the player's inventory., Remove up to ``count`` of an item; return ``True`` if any was removed., Apply an item's effect to the player and consume it if consumable., Return a structured listing of the player's items.

### Community 152 - "GUI Updates -> Godot Only"
Cohesion: 0.22
Nodes (8): Allowed backend support (not the PySide6 GUI), Assets (images), Edit these (Godot), Godot procedure & gotchas (learned), GUI Updates -> Godot Only, Routing decision (applies to every GUI request), Verify, When to Use

### Community 153 - "test_location_artwork.py"
Cohesion: 0.39
Nodes (8): _art_files(), _location_ids(), Artwork coverage for the shipped world map. The Godot location panel loads…, Without the sidecar the editor reimports; with a stale one the panel shows…, test_art_files_are_valid_pngs(), test_every_art_file_has_a_godot_import_sidecar(), test_every_location_has_artwork(), test_no_orphan_artwork()

### Community 154 - "test_time_model.py"
Cohesion: 0.25
Nodes (7): _documented_costs(), The time model is one clock, and this file is the table that says so (TM.1).…, test_a_read_only_action_moves_nothing(), test_a_time_consuming_action_moves_character_and_world_together(), test_age_is_the_only_stored_clock(), test_season_is_a_function_of_age_not_a_second_counter(), test_the_doc_lists_every_time_cost_and_no_others()

### Community 155 - "Ponytail Help"
Cohesion: 0.25
Nodes (7): Configure Default Mode, Deactivate, Levels, More, Ponytail Help, Skills, Update

### Community 156 - "Unreleased"
Cohesion: 0.29
Nodes (6): Changelog, Codebase optimisation pass, Godot frontend dashboard + artwork, Martial Path dashboard UI (PySide6), Unreleased, World map expansion (Sky Spill Continent)

### Community 157 - "Martial Path — Voice & Prose Guide (ROADMAP A.6)"
Cohesion: 0.29
Nodes (6): Authoring checklist, Hard voice rules (validator-enforced), Lore glossary (`game/data/lore_glossary.json`), Martial Path — Voice & Prose Guide (ROADMAP A.6), Sameness metric (A.6 done-criterion), Tone

### Community 158 - "test_godot_event_coverage.py"
Cohesion: 0.38
Nodes (6): Every engine event type must have a render branch in the Godot client (U.2).…, Every event name the client matches on across its scripts., A mistyped arm is dead code that silently swallows the event it names., _render_tables(), test_every_event_type_has_a_render_branch(), test_render_arms_name_real_event_types()

### Community 159 - "test_morality_system.py"
Cohesion: 0.48
Nodes (6): Tests for the morality system's band interpretation and clamped adjustments., _system(), test_adjust_clamps_to_maximum(), test_adjust_clamps_to_minimum(), test_adjust_reports_actual_change(), test_band_ids_cover_the_full_range()

### Community 160 - "godot_mcp_capture.py"
Cohesion: 0.43
Nodes (5): Prove MCP access: run the project, capture the game framebuffer, stop it., request(), send(), tool(), wait_for()

### Community 161 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 162 - "Godot AI"
Cohesion: 0.33
Nodes (5): Documentation, Godot AI, License, Quick Start, Requirements

### Community 163 - "02 — UI Separation Rules"
Cohesion: 0.33
Nodes (5): 02 — UI Separation Rules, Button Rule, Preferred Interaction Flow, UI Scripts May, UI Scripts Must Not

### Community 164 - "12 — AI Assistant Response Rules"
Cohesion: 0.33
Nodes (5): 12 — AI Assistant Response Rules, Code Generation Rules, Output Discipline, Refactor Behaviour, Required Response Structure

### Community 165 - "Martial Path Data Authoring"
Cohesion: 0.33
Nodes (5): Martial Path Data Authoring, Procedure, Schema notes, When to Use, Where content lives

### Community 166 - "Martial Path Engine & Architecture"
Cohesion: 0.33
Nodes (5): Guardrails, Martial Path Engine & Architecture, Procedure, When to Use, Where does the logic go?

### Community 167 - "Martial Path Testing & Validation"
Cohesion: 0.33
Nodes (5): Commands, Conventions, Martial Path Testing & Validation, Procedure, When to Use

### Community 168 - "Martial Path"
Cohesion: 0.33
Nodes (5): Architecture, Conventions, Documentation, Martial Path, Quick start

### Community 169 - "expand_phase_f.py"
Cohesion: 0.47
Nodes (4): load(), main(), ROADMAP Phase F content expansion (F.2 + F.3). Generates the breadth slice: -…, save()

### Community 170 - "expand_phase_f_wave2.py"
Cohesion: 0.47
Nodes (4): load(), main(), ROADMAP Phase F, second content wave. Closes the remaining §6 breadth gaps on…, save()

### Community 171 - "Architecture & Contracts Specialist"
Cohesion: 0.40
Nodes (4): Architecture & Contracts Specialist, Invariants you enforce, Territory, Workflow

### Community 172 - "Godot Frontend Specialist"
Cohesion: 0.40
Nodes (4): Godot Frontend Specialist, Hard conventions, Territory, Workflow

### Community 173 - "ponytail-audit/SKILL.md"
Cohesion: 0.40
Nodes (4): Boundaries, Hunt, Output, Tags

### Community 174 - "Ponytail Gain"
Cohesion: 0.40
Nodes (4): Boundaries, Honesty boundary, Ponytail Gain, Scoreboard

### Community 175 - "ponytail-review/SKILL.md"
Cohesion: 0.40
Nodes (4): Boundaries, Examples, Format, Scoring

### Community 176 - "Test Engineer"
Cohesion: 0.40
Nodes (4): Kinds of work you do, Territory, Test Engineer, Workflow

### Community 177 - ".apply_to_player"
Cohesion: 0.50
Nodes (3): Any, Strip timed combat afflictions (poison/dots/debuffs) from the player., Interpret an effect identifier and mutate the player accordingly.

### Community 178 - "ValidationError"
Cohesion: 0.40
Nodes (3): A single data problem, tagged with a category for grouping/filtering., Record a problem under ``category``., ValidationError

### Community 179 - "03 — Data-Driven Design Rules"
Cohesion: 0.40
Nodes (4): 03 — Data-Driven Design Rules, Data Rules, NPC Data Fields, Preferred Data Structure

### Community 180 - "04 — Godot Export Rules"
Cohesion: 0.40
Nodes (4): 04 — Godot Export Rules, Desktop Game Flow, Export Requirements, Godot Boundary Rules

### Community 181 - "05 — NPC AI and Relationship Rules"
Cohesion: 0.40
Nodes (4): 05 — NPC AI and Relationship Rules, Behaviour Rules, Persistent NPC State, Response Influences

### Community 182 - "06 — Cultivation and Progression Rules"
Cohesion: 0.40
Nodes (4): 06 — Cultivation and Progression Rules, Cultivation May Include, Design Intent, Progression Rules

### Community 183 - "07 — Dialogue System Rules"
Cohesion: 0.40
Nodes (4): 07 — Dialogue System Rules, Dialogue Entry Fields, Dialogue Rules, Dialogue Style Rules

### Community 184 - "08 — Save System Rules"
Cohesion: 0.40
Nodes (4): 08 — Save System Rules, Save Data Should Include, Save Rules, Save Versioning

### Community 185 - "09 — Testing and Validation Rules"
Cohesion: 0.40
Nodes (4): 09 — Testing and Validation Rules, Prioritise Tests For, Testing Intent, Validation Rules

### Community 186 - "11 — Documentation Rules"
Cohesion: 0.40
Nodes (4): 11 — Documentation Rules, Documentation Rules, Documentation Style, Required Documentation Files

### Community 187 - "test_godot_state_contract.py"
Cohesion: 0.40
Nodes (3): Contract between the state payload and the Godot client. The engine always…, The engine's null-ability is the reason the client must type-check., test_engine_sends_nullable_keys_as_null()

### Community 188 - "API, Save & Meta Specialist"
Cohesion: 0.50
Nodes (3): API, Save & Meta Specialist, Territory, Workflow

### Community 189 - "Combat & Dao Specialist"
Cohesion: 0.50
Nodes (3): Combat & Dao Specialist, Territory, Workflow

### Community 190 - "Commit Gatekeeper"
Cohesion: 0.50
Nodes (3): Commit Gatekeeper, Protocol, Verdict format (always end with exactly this block)

### Community 191 - "Cultivation & Progression Specialist"
Cohesion: 0.50
Nodes (3): Cultivation & Progression Specialist, Territory, Workflow

### Community 192 - "Data Integrity & Content Specialist"
Cohesion: 0.50
Nodes (3): Data Integrity & Content Specialist, Territory, Workflow

### Community 193 - "Economy & Equipment Specialist"
Cohesion: 0.50
Nodes (3): Economy & Equipment Specialist, Territory, Workflow

### Community 194 - "Narrative & Prose Specialist"
Cohesion: 0.50
Nodes (3): Narrative & Prose Specialist, Territory, Workflow

### Community 195 - "Game Orchestrator"
Cohesion: 0.50
Nodes (3): Game Orchestrator, Output format, Workflow

### Community 196 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 197 - "graphify reference: commit hook and native AGENTS.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native AGENTS.md integration, graphify reference: commit hook and native AGENTS.md integration

### Community 198 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 199 - "ponytail-debt/SKILL.md"
Cohesion: 0.50
Nodes (3): Boundaries, Output, Scan

### Community 200 - "Social, Quest & Sect Specialist"
Cohesion: 0.50
Nodes (3): Social, Quest & Sect Specialist, Territory, Workflow

### Community 201 - "World & Exploration Specialist"
Cohesion: 0.50
Nodes (3): Territory, Workflow, World & Exploration Specialist

### Community 202 - "Time Model"
Cohesion: 0.50
Nodes (3): Action costs, Invariants, Time Model

### Community 204 - "Copilot Instructions — Martial Path Cultivation RPG"
Cohesion: 0.50
Nodes (3): Copilot Instructions — Martial Path Cultivation RPG, Cross-cutting essentials (always apply), Project rules

### Community 205 - "00 — Global Behaviour Rules"
Cohesion: 0.50
Nodes (3): 00 — Global Behaviour Rules, AI Behaviour, Default Project Intent

### Community 206 - "test_godot_panels.py"
Cohesion: 0.67
Nodes (3): _find_godot(), Runs the Godot frontend's panel smoke check as part of the Python gate. The…, test_panels_render_the_state_they_are_given()

## Knowledge Gaps
- **321 isolated node(s):** `C:\Users\Diego\AppData\Roaming\uv\python\cpython-3.14-windows-x86_64-none\pythonw.exe`, `C:\Users\Diego\AppData\Roaming\uv\python\cpython-3.14-windows-x86_64-none/pythonw.exe`, `Models (Freebuff)`, `Spawn graph`, `The agents` (+316 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **31 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `GameEngine` connect `GameEngine` to `GUIInterface`, `Enemy`, `LocationSystem`, `SaveService`, `rng.py`, `results.py`, `NarrativeSystem`, `Skill`, `test_dao_debate.py`, `Item`, `gui_interface.py`, `ShopSystem`, `CLIInterface`, `QuestSystem`, `game_engine.py`, `test_lifespan_system.py`, `GatherSystem`, `server.py`, `Player`, `EventType`, `SecretRealmSystem`, `test_combo_combat.py`, `CharacterService`, `EconomyMixin`, `LifecycleMixin`, `ExplorationMixin`, `SystemsMixin`, `SectSystem`, `test_talent_system.py`, `GameDataRegistry`, `RefineSystem`, `EquipmentSystem`, `LifespanSystem`, `MetaService`, `test_time_model.py`, `MoralitySystem`, `.__init__`, `SellSystem`, `StartingFateSystem`, `DispatchMixin`, `CultivationSystem`, `EncounterSystem`, `ViewsMixin`, `RelationshipSystem`, `ProgressionMixin`, `OriginSystem`, `CultivationService`, `test_encounters.py`, `RNG`, `EncountersMixin`, `._build_manual_items`, `test_godot_state_contract.py`, `test_secret_realm.py`, `CombatSystem`, `test_roguelike_meta.py`, `test_player_identity.py`, `WorldSimulationSystem`, `test_api_server.py`, `CombatMixin`, `WorldMixin`, `FoeAI`, `TravelService`, `LegacySystem`, `CampaignMixin`, `DebateMixin`, `EventSystem`, `TestActs23`, `TrainerSystem`, `test_codex.py`, `test_meta_depth.py`?**
  _High betweenness centrality (0.199) - this node is a cross-community bridge._
- **Why does `Player` connect `Player` to `Enemy`, `currency.py`, `rng.py`, `.choose_action`, `.from_save_dict`, `._player_damage_parts`, `test_dao_debate.py`, `Item`, `Skill`, `ShopSystem`, `test_trainer_system.py`, `QuestSystem`, `game_engine.py`, `test_lifespan_system.py`, `test_story_tiers.py`, `test_combo_combat.py`, `.from_dict`, `.use_item`, `LifecycleMixin`, `test_time_model.py`, `SectSystem`, `EquipmentSystem`, `LifespanSystem`, `.__init__`, `test_combat_system.py`, `SellSystem`, `CultivationSystem`, `EncounterSystem`, `GameEngine`, `.apply_to_player`, `cultivation.py`, `CultivationService`, `.calculate_derived_cultivation_stats`, `CombatSystem`, `test_equipment_system.py`, `TurnEvent`, `.roll_loot`, `.convert_exp_to_comprehension`, `FoeAI`, `test_dead_content.py`, `EventSystem`, `test_sect_system.py`, `test_quest_system.py`, `TrainerSystem`?**
  _High betweenness centrality (0.121) - this node is a cross-community bridge._
- **Why does `EventType` connect `EventType` to `GUIInterface`, `gui_interface.py`, `rng.py`, `results.py`, `NarrativeSystem`, `Skill`, `Item`, `CLIInterface`, `ShopSystem`, `test_secret_realm.py`, `QuestSystem`, `game_engine.py`, `with_article`, `test_lifespan_system.py`, `test_trainer_system.py`, `Player`, `test_travel_service.py`, `test_combo_combat.py`, `EconomyMixin`, `LifecycleMixin`, `ExplorationMixin`, `SystemsMixin`, `SectSystem`, `test_time_model.py`, `RefineSystem`, `EquipmentSystem`, `test_godot_event_coverage.py`, `.__init__`, `SellSystem`, `test_results.py`, `DispatchMixin`, `CultivationSystem`, `EncounterSystem`, `ViewsMixin`, `GameEngine`, `ProgressionMixin`, `test_encounters.py`, `EncountersMixin`, `lint_narrative_templates`, `CombatSystem`, `test_equipment_system.py`, `test_player_identity.py`, `test_api_server.py`, `CombatMixin`, `WorldMixin`, `CampaignMixin`, `DebateMixin`, `EventSystem`, `test_sect_system.py`, `TrainerSystem`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Are the 27 inferred relationships involving `Player` (e.g. with `LifecycleMixin` and `GameEngine`) actually correct?**
  _`Player` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 208 inferred relationships involving `GameEngine` (e.g. with `new_game()` and `GameDataRegistry`) actually correct?**
  _`GameEngine` has 208 INFERRED edges - model-reasoned connections that need verification._
- **Are the 215 inferred relationships involving `EventType` (e.g. with `CampaignMixin` and `CombatMixin`) actually correct?**
  _`EventType` has 215 INFERRED edges - model-reasoned connections that need verification._
- **Are the 116 inferred relationships involving `GameDataRegistry` (e.g. with `GameEngine` and `_validate_character_enemy_links()`) actually correct?**
  _`GameDataRegistry` has 116 INFERRED edges - model-reasoned connections that need verification._