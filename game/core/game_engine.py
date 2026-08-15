"""Central game engine — the heart of the CORE layer.

The engine owns game state, wires the gameplay systems together, and exposes a
tiny, UI-agnostic contract::

    process_action(action: dict) -> dict
    get_game_state() -> dict

It NEVER calls ``print`` or ``input`` and never formats player-facing text.
Every method returns structured data that any UI is free to render. Swapping the
CLI for a web/GUI/API frontend requires no changes to this file.

The engine coordinates nine concerns (routing, views, exploration, progression,
social, economy, systems, combat, lifecycle). ``GameEngine`` is the single
orchestrator that owns construction and state; the per-concern *methods* live as
mixins in :mod:`game.core.engine` so this file stays readable.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from game.core.constants import (
    DEFAULT_ORIGIN_ID,
    MODE_COMBAT,
    MODE_EXPLORE,
    STARTING_PLAYER,
)
from game.core.engine.combat import CombatMixin
from game.core.engine.dispatch import DispatchMixin
from game.core.engine.economy import EconomyMixin
from game.core.engine.exploration import ExplorationMixin
from game.core.engine.lifecycle import LifecycleMixin
from game.core.engine.progression import ProgressionMixin
from game.core.engine.social import SocialMixin
from game.core.engine.systems import SystemsMixin
from game.core.engine.views import ViewsMixin
from game.data.registry import GameDataRegistry
from game.models.enemy import Enemy
from game.models.item import Item
from game.models.player import Player
from game.models.skill import Skill
from game.services.character_service import CharacterService
from game.services.cultivation_service import CultivationService
from game.services.meta_service import MetaService
from game.services.save_service import SaveService
from game.services.travel_service import TravelService
from game.systems.alchemy_system import GatherSystem, RefineSystem
from game.systems.combat_system import CombatSystem
from game.systems.cultivation_system import CultivationSystem
from game.systems.dao_system import DaoSystem
from game.systems.effect_system import EffectSystem
from game.systems.equipment_system import EquipmentSystem
from game.systems.event_system import EventSystem
from game.systems.find_system import FindSystem
from game.systems.inventory_system import InventorySystem
from game.systems.lifespan_system import LifespanSystem
from game.systems.location_system import LocationSystem
from game.systems.loot_system import LootSystem
from game.systems.morality_system import MoralitySystem
from game.systems.narrative_system import NarrativeSystem
from game.systems.origin_system import OriginSystem
from game.systems.quest_system import QuestSystem
from game.systems.relationship_system import RelationshipSystem
from game.systems.secret_realm_system import SecretRealmSystem
from game.systems.sect_system import SectSystem
from game.systems.sell_system import SellSystem
from game.systems.shop_system import ShopSystem
from game.systems.skill_system import SkillSystem
from game.systems.starting_fate_system import StartingFateSystem
from game.systems.stats_system import StatsSystem
from game.systems.talent_system import TalentSystem
from game.systems.trainer_system import TrainerSystem
from game.utils.logger import get_logger
from game.utils.rng import RNG


class GameEngine(
    DispatchMixin,
    ViewsMixin,
    ExplorationMixin,
    ProgressionMixin,
    SocialMixin,
    EconomyMixin,
    SystemsMixin,
    CombatMixin,
    LifecycleMixin,
):
    """Coordinates systems, manages state, and processes actions.

    The action handlers are provided by the ``game.core.engine`` mixins; this
    class owns construction (``__init__`` / ``new_game``) and all mutable state
    those handlers read.
    """

    def __init__(
        self,
        player: Player,
        rng: RNG,
        items: Dict[str, Item],
        enemy_templates: List[Dict[str, Any]],
        skills: Dict[str, Skill],
        events_data: Dict[str, Any],
        body_realms: Dict[str, Any],
        essence_realms: Dict[str, Any],
        cultivation_config: Dict[str, Any],
        locations: Optional[List[Dict[str, Any]]] = None,
        quests: Optional[List[Dict[str, Any]]] = None,
        encounter_pools: Optional[Dict[str, Any]] = None,
        characters: Optional[List[Dict[str, Any]]] = None,
        morality: Optional[Dict[str, Any]] = None,
        relationships: Optional[Dict[str, Any]] = None,
        martial_talents: Optional[List[Dict[str, Any]]] = None,
        body_talents: Optional[List[Dict[str, Any]]] = None,
        equipment: Optional[List[Dict[str, Any]]] = None,
        shops: Optional[List[Dict[str, Any]]] = None,
        character_enemies: Optional[List[Dict[str, Any]]] = None,
        talents: Optional[Dict[str, Any]] = None,
        trainers: Optional[List[Dict[str, Any]]] = None,
        sects: Optional[List[Dict[str, Any]]] = None,
        daos: Optional[List[Dict[str, Any]]] = None,
        narrative_templates: Optional[Dict[str, Any]] = None,
        narrative_rng: Optional[RNG] = None,
        seed: Optional[int] = None,
        origins: Optional[List[Dict[str, Any]]] = None,
        origin_id: Optional[str] = None,
        hardcore: bool = True,
        meta: Optional[MetaService] = None,
        gathering: Optional[Dict[str, Any]] = None,
        refining_recipes: Optional[List[Dict[str, Any]]] = None,
        secret_realm: Optional[List[Dict[str, Any]]] = None,
        ironman: bool = False,
        ng_plus: int = 0,
    ) -> None:
        self._log = get_logger("engine")
        self._ironman = bool(ironman)
        self._ng_plus = max(0, int(ng_plus))
        self._hardcore = bool(hardcore)
        self._seed = seed
        self._origin_id = str(origin_id or DEFAULT_ORIGIN_ID)
        self.player = player
        self._rng = rng
        self._items = items
        self._skills = skills
        self._cultivation_config = cultivation_config or {}
        self._enemy_templates = {template["id"]: template for template in enemy_templates}
        self._character_enemy_templates = {template["id"]: template for template in character_enemies or []}
        self._body_realm_names = {
            realm["id"]: realm.get("display_name", realm["id"])
            for realm in body_realms.get("realms", [])
        }
        self._essence_realm_names = {
            realm["id"]: realm.get("display_name", realm["id"])
            for realm in essence_realms.get("realms", [])
        }

        # Gameplay systems (pure logic).
        self.cultivation = CultivationSystem(body_realms, essence_realms, cultivation_config, rng, martial_talents, body_talents, skills)
        self.cultivation_service = CultivationService({"player": player}, self.cultivation)
        self.lifespan = LifespanSystem(essence_realms, cultivation_config)
        self.stats = StatsSystem(skills)
        self.dao = DaoSystem(daos or [], body_realms, essence_realms)
        self.narrative = NarrativeSystem(narrative_templates, narrative_rng or RNG(), seed)
        self.origins = OriginSystem(origins)
        self.meta = meta or MetaService()
        self.gathering = GatherSystem(gathering)
        self.refine = RefineSystem(refining_recipes, body_realms, essence_realms)
        self.secret_realm = SecretRealmSystem(secret_realm, rng)
        self.combat = CombatSystem(rng, self.stats, self.dao)
        self.effects = EffectSystem()
        self.inventory = InventorySystem(items, self.effects)
        self.sell = SellSystem(items)
        self.equipment = EquipmentSystem(equipment or [], body_realms, essence_realms)
        self.shops = ShopSystem(shops or [], items)
        self.techniques = SkillSystem(skills)
        self.trainers = TrainerSystem(trainers or [], skills, self.techniques)
        self.sects = SectSystem(sects or [], body_realms)
        self.loot = LootSystem(self.inventory, rng)
        # Rarity-weighted exploration finds over the whole item/equipment catalog
        # (technique manuals are excluded; skills are learned, not stumbled upon).
        find_catalog = [
            {"item_id": item.id, "rarity": item.rarity}
            for item in items.values()
            if item.type != "technique"
        ]
        self.find_system = FindSystem(find_catalog, (events_data or {}).get("find_config", {}), rng)
        self._location_danger = {loc["id"]: loc.get("danger_level", 0) for loc in (locations or []) if loc.get("id")}
        self.event_system = EventSystem(
            events_data,
            list(self._enemy_templates.values()),
            rng,
            encounter_pools,
            self.find_system,
        )
        # Chance (0.0-1.0) that exploring a location with named characters
        # surfaces them instead of rolling a normal random event. Data-driven so
        # characters never crowd out every other exploration outcome.
        self._character_encounter_chance = float(
            (events_data or {}).get("character_encounter_chance", 0.35)
        )
        self.locations = LocationSystem(locations or [])
        self.travel = TravelService(self.locations, body_realms, essence_realms)
        self.morality = MoralitySystem(morality)
        self.relationships = RelationshipSystem(relationships)
        self.starting_fate = StartingFateSystem(martial_talents or [], body_talents or [], rng)
        self.talents = TalentSystem((talents or {}).get("tiers", []))
        self.character_service = CharacterService(
            characters or [], self.locations, self.morality, self.relationships
        )
        self.quests = QuestSystem(quests or [], self.techniques)
        self.saves = SaveService()

        # Mutable session state.
        self._mode = MODE_EXPLORE
        self._current_enemy: Optional[Enemy] = None
        self._cooldowns: Dict[str, int] = {}
        self._combat_is_spar = False
        self._running = True
        self._fate_accepted = bool(player.martial_talent_id and player.body_talent_id)
        self._pending_fate: Optional[Dict[str, Any]] = None
        # Active secret-realm run (rooms + index), ``None`` outside a realm.
        self._realm: Optional[Dict[str, Any]] = None
        # True while the current combat bout is a tournament match.
        self._tournament_active = False
        self._bind_equipment_modifiers()

        # Action dispatch tables (built once). Informational actions are
        # mode-agnostic; exploration actions are looked up by name. Combat keeps
        # an explicit flow because its actions share turn/end-of-combat handling.
        self._info_dispatch = self._build_info_dispatch()
        self._explore_dispatch = self._build_explore_dispatch()

    # -- construction -----------------------------------------------------
    @classmethod
    def new_game(
        cls,
        player_name: str = "Daoist",
        seed: Optional[int] = None,
        registry: Optional["GameDataRegistry"] = None,
        ironman: bool = False,
        ng_plus: int = 0,
        origin_id: Optional[str] = None,
        hardcore: bool = True,
        meta: Optional[MetaService] = None,
    ) -> "GameEngine":
        """Build a fully-loaded engine from the central data registry.

        ``registry`` may be injected (e.g. by tests) to avoid re-reading disk or
        to supply crafted content; by default it is loaded once from ``data/``.
        """
        if seed is None:
            seed = RNG().randint(0, 2**31 - 1)
        rng = RNG(seed)
        narrative_rng = RNG(seed)
        if registry is None:
            registry = GameDataRegistry.load()
        item_entries = list(registry.items) + [cls._equipment_as_item(entry) for entry in registry.equipment]
        item_entries += cls._build_manual_items(registry.skills, registry.technique_manuals)
        items = {entry["id"]: Item.from_dict(entry) for entry in item_entries}
        skills = {entry["id"]: Skill.from_dict(entry) for entry in registry.skills}
        player = cls._build_player(player_name)
        # Resolve the starting origin, spending Ancestral Memory for priced ones
        # and falling back to the free origin when unaffordable or unknown.
        meta_service = meta or MetaService()
        origin_system = OriginSystem(registry.origins)
        chosen_id = str(origin_id or DEFAULT_ORIGIN_ID)
        origin = origin_system.get(chosen_id)
        if origin is None or origin_system.cost(chosen_id) > meta_service.memory():
            chosen_id = origin_system.default_id()
            origin = origin_system.get(chosen_id)
        if origin is not None:
            if origin_system.cost(chosen_id) > 0:
                meta_service.spend_memory(origin_system.cost(chosen_id))
            origin_system.apply(player, origin)
        engine = cls(
            player,
            rng,
            items,
            registry.enemies,
            skills,
            registry.events,
            registry.body_realms,
            registry.essence_realms,
            registry.cultivation_config,
            registry.locations,
            registry.quests,
            registry.encounter_pools,
            registry.characters,
            registry.morality,
            registry.relationships,
            registry.martial_talents,
            registry.body_talents,
            registry.equipment,
            registry.shops,
            registry.character_enemies,
            registry.talents,
            registry.trainers,
            registry.sects,
            registry.daos,
            registry.narrative_templates,
            narrative_rng=narrative_rng,
            seed=seed,
            origins=registry.origins,
            origin_id=chosen_id,
            hardcore=hardcore,
            meta=meta_service,
            gathering=registry.gathering,
            refining_recipes=registry.refining_recipes,
            secret_realm=registry.secret_realm,
            ironman=ironman,
            ng_plus=ng_plus,
        )
        engine._assign_new_game_fate()
        # New Game Plus carries a modest legacy forward into the next run.
        if ng_plus > 0:
            engine.player.comprehension += int(ng_plus)
            engine.player.gold += int(ng_plus) * 100
        return engine

    @staticmethod
    def _build_player(name: str) -> Player:
        cfg = STARTING_PLAYER
        return Player(
            name=name or "Daoist",
            realm=cfg["realm"],
            stage=cfg["stage"],
            max_hp=cfg["max_hp"],
            hp=cfg["max_hp"],
            max_qi=cfg["max_qi"],
            qi=cfg["max_qi"],
            attack=cfg["attack"],
            defense=cfg["defense"],
            path=cfg.get("path", "Unassigned"),
            dao_id=cfg.get("dao_id", "sword_dao"),
            foundation_quality=cfg.get("foundation_quality", 50),
            body_strength=cfg.get("body_strength", 10),
            soul_strength=cfg.get("soul_strength", 10),
            comprehension=cfg.get("comprehension", 10),
            reputation=cfg.get("reputation", 0),
            morality=cfg.get("morality", 0),
            current_location=cfg.get("current_location", "outer_forest"),
            martial_talent_id="",
            body_talent_id="",
            inventory=dict(cfg["inventory"]),
            skills=list(cfg["skills"]),
        )

    @staticmethod
    def _equipment_as_item(entry: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": entry["id"],
            "name": entry.get("display_name", entry["id"]),
            "type": "equipment",
            "category": entry.get("category", ""),
            "rarity": entry.get("rarity", "mortal_grade"),
            "valid_slots": list(entry.get("valid_slots", [])),
            "effect": "none",
            "magnitude": 0,
            "description": entry.get("description", ""),
            "consumed_on_use": False,
            "value": int(entry.get("value", 0)),
            "stat_modifiers": dict(entry.get("stat_modifiers", {})),
            "cultivation_modifiers": dict(entry.get("cultivation_modifiers", {})),
            "utility_modifiers": dict(entry.get("utility_modifiers", {})),
        }

    @staticmethod
    def _manual_as_item(entry: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a technique-manual entry into a consumable learn-skill item."""
        return {
            "id": entry["id"],
            "name": entry.get("name", entry.get("display_name", entry["id"])),
            "type": "technique",
            "rarity": entry.get("rarity", "mortal_grade"),
            "effect": "learn_skill",
            "magnitude": 0,
            "skill_id": entry.get("skill_id", ""),
            "description": entry.get("description", ""),
            "consumed_on_use": True,
        }

    @classmethod
    def _build_manual_items(
        cls,
        skills: List[Dict[str, Any]],
        overrides: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Auto-generate one learn-skill manual per skill, applying data overrides.

        Every skill in the catalogue becomes learnable via a manual item
        (id ``"<skill_id>_manual"`` by default). ``technique_manuals.json`` entries
        override the generated manual for their ``skill_id`` (custom name, rarity,
        description, or id) so special techniques can carry bespoke flavour.
        """
        overrides_by_skill = {o["skill_id"]: o for o in overrides if o.get("skill_id")}
        manuals: List[Dict[str, Any]] = []
        for skill in skills:
            skill_id = skill.get("id")
            if not skill_id:
                continue
            skill_name = skill.get("name", skill_id)
            override = overrides_by_skill.get(skill_id, {})
            manuals.append(
                cls._manual_as_item(
                    {
                        "id": override.get("id", f"{skill_id}_manual"),
                        "name": override.get("name", f"{skill_name} Manual"),
                        "skill_id": skill_id,
                        "rarity": override.get("rarity", "mortal_grade"),
                        "description": override.get(
                            "description",
                            f"A manual recording the {skill_name} technique. Study it to learn the art.",
                        ),
                    }
                )
            )
        return manuals
