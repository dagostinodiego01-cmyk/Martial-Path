"""Central game engine — the heart of the CORE layer.

The engine owns game state, wires the gameplay systems together, and exposes a
tiny, UI-agnostic contract:

    process_action(action: dict) -> dict
    get_game_state() -> dict

It NEVER calls ``print`` or ``input`` and never formats player-facing text.
Every method returns structured data that any UI is free to render. Swapping the
CLI for a web/GUI/API frontend requires no changes to this file.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from game.core.constants import (
    STARTING_PLAYER,
    Action,
    EventType,
)
from game.core.results import (
    BoonResult,
    CharacterEncounterResult,
    CharacterInteractionResult,
    ClosedDoorResult,
    DialogueChoiceResult,
    HelpResult,
    MapResult,
    MeditateResult,
    PlayerDiedResult,
    QuitResult,
    RepairResult,
    RestResult,
    SaveExportedResult,
    SaveImportedResult,
    StartingFateAcceptedResult,
    StartingFateRolledResult,
    TalentUpgradedResult,
    TalentsResult,
    TechniquesResult,
)
from game.data.registry import GameDataRegistry
from game.models.enemy import Enemy
from game.models.item import Item
from game.models.player import Player
from game.models.skill import Skill
from game.services.character_service import CharacterService
from game.services.cultivation_service import CultivationService
from game.services.save_service import SAVE_VERSION, SaveError, SaveService
from game.services.travel_service import TravelService
from game.systems.combat_system import CombatSystem
from game.systems.cultivation_system import CultivationSystem
from game.systems.effect_system import EffectSystem
from game.systems.equipment_system import EquipmentSystem
from game.systems.event_system import EventSystem
from game.systems.find_system import FindSystem
from game.systems.inventory_system import InventorySystem
from game.systems.lifespan_system import LifespanSystem
from game.systems.location_system import LocationSystem
from game.systems.loot_system import LootSystem
from game.systems.morality_system import MoralitySystem
from game.systems.quest_system import QuestSystem
from game.systems.relationship_system import RelationshipSystem
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

# Game "modes" gate which actions are valid.
MODE_EXPLORE = "explore"
MODE_COMBAT = "combat"


class GameEngine:
    """Coordinates systems, manages state, and processes actions."""

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
        ironman: bool = False,
        ng_plus: int = 0,
    ) -> None:
        self._log = get_logger("engine")
        self._ironman = bool(ironman)
        self._ng_plus = max(0, int(ng_plus))
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
        self.combat = CombatSystem(rng, self.stats)
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
    ) -> "GameEngine":
        """Build a fully-loaded engine from the central data registry.

        ``registry`` may be injected (e.g. by tests) to avoid re-reading disk or
        to supply crafted content; by default it is loaded once from ``data/``.
        """
        rng = RNG(seed)
        if registry is None:
            registry = GameDataRegistry.load()
        item_entries = list(registry.items) + [cls._equipment_as_item(entry) for entry in registry.equipment]
        item_entries += cls._build_manual_items(registry.skills, registry.technique_manuals)
        items = {entry["id"]: Item.from_dict(entry) for entry in item_entries}
        skills = {entry["id"]: Skill.from_dict(entry) for entry in registry.skills}
        player = cls._build_player(player_name)
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

    # -- public engine contract ------------------------------------------
    def process_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Process a structured command and return a structured result."""
        if not isinstance(action, dict):
            return {"event": EventType.ERROR, "reason": "MALFORMED_ACTION"}

        name = action.get("action", Action.UNKNOWN)

        # Informational actions (status/inventory/help/quit) never consume a turn
        # and behave identically in every mode, so they are resolved first.
        info_handler = self._info_dispatch.get(name)
        if info_handler is not None:
            return info_handler(action)

        if name == Action.ROLL_STARTING_FATE:
            return self._roll_starting_fate_result()
        if name == Action.ACCEPT_STARTING_FATE:
            return self._accept_starting_fate()
        if not self._fate_accepted:
            return {"event": EventType.ERROR, "reason": "FATE_NOT_ACCEPTED", "pending_fate": self._pending_fate_view()}

        if self._mode == MODE_COMBAT:
            return self._process_combat_action(name, action)
        return self._process_explore_action(name, action)

    def get_game_state(self) -> Dict[str, Any]:
        """Return a UI-safe snapshot of the entire game state."""
        player_data = self._player_view()
        return {
            "player": player_data,
            "mode": self._mode,
            "in_combat": self._mode == MODE_COMBAT,
            "enemy": self._enemy_view(self._current_enemy) if self._current_enemy else None,
            "cooldowns": dict(self._cooldowns),
            "inventory_items": self.inventory.list_inventory(self.player)["items"],
            "shops": self.shops.shops_for_location(self.player.current_location),
            "trainers": self.trainers.trainers_for_location(self.player.current_location),
            "sects": self.sects.sects_for_location(self.player.current_location),
            "location": self.locations.view(self.player.current_location),
            "destinations": self.travel.get_available_destinations(self.player),
            "location_characters": self.character_service.get_available_characters(
                self.player.current_location, self.player
            ),
            "quests": self.quests.snapshot(),
            "awaiting_fate_acceptance": not self._fate_accepted,
            "pending_fate": self._pending_fate_view(),
            "running": self._running,
        }

    def is_running(self) -> bool:
        """Return ``True`` until the player quits."""
        return self._running

    def set_player_name(self, name: str) -> None:
        """Set the player's display name (used by character creation in the UI)."""
        if name:
            self.player.name = name

    def get_known_skills(self) -> List[Dict[str, Any]]:
        """Return UI-safe briefs for the player's skills, incl. live combat state.

        Read-only view model used by graphical frontends (e.g. a Pokemon-style
        move menu) to render skill buttons with qi cost, base cooldown, current
        cooldown remaining, and affordability. Adds no gameplay logic.
        """
        briefs: List[Dict[str, Any]] = []
        for skill_id in self.player.skills:
            brief = self._skill_brief(skill_id)
            brief["cooldown_remaining"] = self._cooldowns.get(skill_id, 0)
            brief["affordable"] = self.player.qi >= int(brief.get("qi_cost", 0))
            briefs.append(brief)
        return briefs

    def get_inventory_items(self) -> List[Dict[str, Any]]:
        """Return the player's inventory as UI-safe entries (read-only view)."""
        return self.inventory.list_inventory(self.player)["items"]

    # -- action dispatch tables ------------------------------------------
    def _build_info_dispatch(self) -> Dict[str, Any]:
        """Mode-agnostic actions that never consume a turn."""
        return {
            Action.STATUS: lambda action: self._status(),
            Action.INVENTORY: lambda action: self.inventory.list_inventory(self.player),
            Action.MAP: lambda action: self._map(),
            Action.TECHNIQUES: lambda action: self._techniques(),
            Action.TALENTS: lambda action: self._talents(),
            Action.HELP: lambda action: HelpResult().to_dict(),
            Action.QUIT: lambda action: self._quit(),
        }

    def _build_explore_dispatch(self) -> Dict[str, Any]:
        """Exploration-mode actions, keyed by action name.

        Handlers look attributes up on ``self`` at call time, so state swapped in
        by :meth:`load_game` (player, cultivation service) is always honoured.
        """
        return {
            Action.TRAIN: lambda action: self._advance_time_after(self.cultivation_service.train_body("player", action.get("method_id", "train_body")), "train_body"),
            Action.TRAIN_BODY: lambda action: self._advance_time_after(self.cultivation_service.train_body("player", action.get("method_id", "train_body")), "train_body"),
            Action.TRAIN_ESSENCE: lambda action: self._advance_time_after(self.cultivation_service.train_essence("player", action.get("method_id", "gather_essence")), "train_essence"),
            Action.TALK_TO_CHARACTER: lambda action: self._talk_to_character(action.get("character_id", "")),
            Action.DIALOGUE_CHOOSE: lambda action: self._dialogue_choose(action),
            Action.SPAR_CHARACTER: lambda action: self._start_character_combat(action.get("character_id", ""), "spar"),
            Action.DUEL_CHARACTER: lambda action: self._start_character_combat(action.get("character_id", ""), "duel"),
            Action.RECEIVE_BOON: lambda action: self._receive_boon(action.get("character_id", "")),
            Action.BREAKTHROUGH: lambda action: self._advance_time_after(self._after_breakthrough(self.cultivation_service.attempt_body_breakthrough("player")), "body_breakthrough"),
            Action.BODY_BREAKTHROUGH: lambda action: self._advance_time_after(self._after_breakthrough(self.cultivation_service.attempt_body_breakthrough("player")), "body_breakthrough"),
            Action.ESSENCE_BREAKTHROUGH: lambda action: self._advance_time_after(self._after_breakthrough(self.cultivation_service.attempt_essence_breakthrough("player")), "essence_breakthrough"),
            Action.STABILISE_FOUNDATION: lambda action: self._advance_time_after(self._advance_day_after(self.cultivation_service.stabilise_foundation("player")), "stabilise"),
            Action.STABILISE_ESSENCE: lambda action: self._advance_time_after(self._advance_day_after(self.cultivation_service.stabilise_essence("player")), "stabilise_essence"),
            Action.EXPLORE: lambda action: self._explore(),
            Action.REST: lambda action: self._advance_time_after(self._advance_day_after(self._rest()), "rest"),
            Action.MEDITATE: lambda action: self._advance_time_after(self._meditate(), "meditate"),
            Action.TRAVEL: lambda action: self._travel(action.get("location_id", "")),
            Action.SHOP: lambda action: self.shops.shop_view(self.player, action.get("shop_id", "")),
            Action.BUY_ITEM: lambda action: self._buy_item(action),
            Action.SELL_ITEM: lambda action: self._sell_item(action),
            Action.TRAINERS: lambda action: self.trainers.trainer_view(self.player, action.get("trainer_id", "")),
            Action.LEARN_SKILL: lambda action: self._learn_skill(action),
            Action.SECTS: lambda action: self.sects.sect_view(self.player, action.get("sect_id", "")),
            Action.JOIN_SECT: lambda action: self._join_sect(action.get("sect_id", "")),
            Action.UPGRADE_TALENT: lambda action: self._upgrade_talent(action.get("track", ""), action.get("target_id", "")),
            Action.CLOSED_DOOR: lambda action: self._closed_door(action.get("years", 0)),
            Action.REPAIR_ITEM: lambda action: self._repair_item(action.get("item_id", "")),
            Action.EXPORT_SAVE: lambda action: self._export_save(),
            Action.IMPORT_SAVE: lambda action: self._import_save(action.get("payload", ""), action.get("slot", "default")),
            Action.SAVE: lambda action: self.save_game(action.get("slot") or "default"),
            Action.LOAD: lambda action: self.load_game(action.get("slot") or "default"),
            Action.USE_ITEM: lambda action: self._use_item(action.get("item_id", "")),
            Action.EQUIP_ITEM: lambda action: self._equip_item(action),
            Action.UNEQUIP_ITEM: lambda action: self._unequip_item(action),
            Action.USE_SKILL: lambda action: {"event": EventType.ERROR, "reason": "SKILL_ONLY_IN_COMBAT"},
            Action.ATTACK: lambda action: {"event": EventType.ERROR, "reason": "NOT_IN_COMBAT"},
            Action.FLEE: lambda action: {"event": EventType.ERROR, "reason": "NOT_IN_COMBAT"},
        }

    def _quit(self) -> Dict[str, Any]:
        """Flag the session as finished and return the quit result."""
        self._running = False
        return QuitResult().to_dict()

    # -- exploration-mode dispatch ---------------------------------------
    def _process_explore_action(self, name: str, action: Dict[str, Any]) -> Dict[str, Any]:
        handler = self._explore_dispatch.get(name)
        if handler is None:
            return {"event": EventType.ERROR, "reason": "UNKNOWN_COMMAND", "input": action.get("raw", name)}
        return handler(action)

    # -- combat-mode dispatch --------------------------------------------
    def _process_combat_action(self, name: str, action: Dict[str, Any]) -> Dict[str, Any]:
        # Informational actions are resolved mode-agnostically in process_action
        # and never reach here; only turn-consuming actions remain.
        if self._current_enemy is None:
            self._mode = MODE_EXPLORE
            return {"event": EventType.ERROR, "reason": "NOT_IN_COMBAT"}
        if self.player.statuses.get("stun"):
            result = self.combat.player_stunned_turn(self.player, self._current_enemy, spar=self._combat_is_spar)
            self._tick_cooldowns()
            if result.get("event") == EventType.COMBAT_END:
                return self._end_combat(result)
            return result
        if name == Action.ATTACK:
            result = self.combat.attack(self.player, self._current_enemy, spar=self._combat_is_spar)
            self._tick_cooldowns()
        elif name == Action.FLEE:
            result = self.combat.flee(self.player, self._current_enemy, spar=self._combat_is_spar)
            self._tick_cooldowns()
        elif name == Action.USE_SKILL:
            result = self._use_combat_skill(action.get("skill_id", ""))
            if result.get("event") == EventType.ERROR:
                return result
        elif name == Action.USE_ITEM:
            result = self._use_combat_item(action.get("item_id", ""))
            if result.get("event") == EventType.ERROR:
                return result
        else:
            return {"event": EventType.ERROR, "reason": "INVALID_IN_COMBAT", "input": name}

        if result.get("event") == EventType.COMBAT_END:
            return self._end_combat(result)
        return result

    # -- exploration helpers ---------------------------------------------
    def _explore(self) -> Dict[str, Any]:
        characters = self._location_character_options()
        if characters and self._rng.chance(self._character_encounter_chance):
            return CharacterEncounterResult(
                characters=characters,
                player_message="You encounter familiar cultivators nearby.",
            ).to_dict()

        event = self.event_system.generate(self.player, self._find_rarity_index())
        kind = event.get("event")

        if kind == EventType.COMBAT:
            enemy = self._spawn_enemy(event.get("enemy_id", ""))
            self._current_enemy = enemy
            self._mode = MODE_COMBAT
            self._cooldowns = {}
            self._combat_is_spar = False
            self.player.statuses.clear()
            self.player.shield = 0
            return {
                "event": EventType.COMBAT,
                "enemy": self._enemy_view(enemy),
                "text": event.get("text", "A hostile presence blocks your path!"),
            }
        if kind == EventType.LOOT:
            return self.inventory.add_item(self.player, event.get("item_id", ""), event.get("count", 1))
        if kind == EventType.SPECIAL:
            return self._apply_special(event)
        return event  # EXPLORE_RESULT / NOTHING

    def _apply_special(self, event: Dict[str, Any]) -> Dict[str, Any]:
        effect = event.get("effect", {})
        applied = self.effects.apply_to_player(
            self.player,
            effect.get("type", "none"),
            int(effect.get("magnitude", 0)),
        )

        return {
            "event": EventType.SPECIAL,
            "special_id": event.get("special_id"),
            "text": event.get("text", ""),
            **applied,
        }

    def _spawn_enemy(self, enemy_id: str) -> Enemy:
        template = self._enemy_templates.get(enemy_id)
        if template is None:
            template = next(iter(self._enemy_templates.values()))
        return Enemy.from_dict(template)

    def _spawn_character_enemy(self, enemy_id: str) -> Optional[Enemy]:
        template = self._character_enemy_templates.get(enemy_id)
        if template is None:
            return None
        return Enemy.from_dict(template)

    def _location_character_options(self) -> List[Dict[str, Any]]:
        characters = []
        for brief in self.character_service.get_available_characters(self.player.current_location, self.player):
            options = []
            character_id = brief["id"]
            if brief.get("unlocked") and brief.get("can_talk"):
                options.append({"action": Action.TALK_TO_CHARACTER, "character_id": character_id, "label": "Talk"})
            spar = self.character_service.can_spar(character_id, self.player)
            if spar.get("allowed") and spar.get("enemy_id"):
                options.append({"action": Action.SPAR_CHARACTER, "character_id": character_id, "label": "Spar"})
            duel = self.character_service.can_duel(character_id, self.player)
            if duel.get("allowed") and duel.get("enemy_id"):
                options.append({"action": Action.DUEL_CHARACTER, "character_id": character_id, "label": "Duel"})
            if self.character_service.can_receive_reward(character_id, self.player):
                options.append({"action": Action.RECEIVE_BOON, "character_id": character_id, "label": "Receive Reward"})
            if options:
                entry = dict(brief)
                entry["options"] = options
                characters.append(entry)
        return characters

    def _enemy_view(self, enemy: Enemy) -> Dict[str, Any]:
        """Return the enemy's public stats plus a UI-only threat/reward preview."""
        view = enemy.public_view()
        view["shield"] = enemy.shield
        view["statuses"] = {k: dict(v) for k, v in enemy.statuses.items()}
        body_name = self._body_realm_names.get(enemy.body_realm_id, enemy.body_realm_id)
        essence_name = self._essence_realm_names.get(enemy.essence_realm_id or "", "")
        view["body_realm"] = body_name
        view["essence_realm"] = essence_name
        view["realm"] = f"{body_name} / {essence_name}" if essence_name else body_name
        view.update(self._encounter_preview(enemy))
        return view

    def _encounter_preview(self, enemy: Enemy) -> Dict[str, Any]:
        """Derive a UI-only threat tier and reward preview for an enemy.

        This is presentation metadata for the frontend; it never affects combat
        math (which is owned by the combat system).
        """
        enemy_power = enemy.max_hp + enemy.attack * 5 + enemy.defense * 3
        player_power = (
            self.player.max_hp
            + self.stats.effective_stats(self.player).get("attack", self.player.attack) * 5
            + self.stats.effective_defense(self.player) * 3
        )
        ratio = enemy_power / player_power if player_power > 0 else 1.0
        if ratio < 0.6:
            threat = "Low"
        elif ratio < 1.0:
            threat = "Moderate"
        elif ratio < 1.5:
            threat = "High"
        else:
            threat = "Deadly"
        reward_items = [
            self._items[drop["item_id"]].name
            for drop in enemy.loot_table
            if drop.get("item_id") in self._items
        ]
        return {
            "threat": threat,
            "reward_preview": {"exp": enemy.exp_reward, "items": reward_items},
        }

    # -- exploration actions ---------------------------------------------
    def _rest(self) -> Dict[str, Any]:
        """Recover a portion of HP and Qi while safely at rest."""
        healed = self.player.heal(int(self.player.max_hp * 0.4))
        qi_restored = self.player.restore_qi(int(self.player.max_qi * 0.4))
        return RestResult(
            healed=healed,
            qi_restored=qi_restored,
            hp=self.player.hp,
            qi=self.player.qi,
        ).to_dict()

    def _meditate(self) -> Dict[str, Any]:
        """Meditate to restore Qi and, sometimes, sharpen comprehension."""
        qi_restored = self.player.restore_qi(int(self.player.max_qi * 0.3))
        comprehension_gain = 0
        if self._rng.chance(0.5):
            martial_talent = self.starting_fate.martial_talent_data(self.player.martial_talent_id)
            comprehension_gain = max(0, int(round(float(martial_talent.get("comprehension_multiplier", 1.0)))))
        self.player.comprehension += comprehension_gain
        return MeditateResult(
            qi_restored=qi_restored,
            qi=self.player.qi,
            comprehension_gain=comprehension_gain,
            comprehension=self.player.comprehension,
        ).to_dict()

    def _travel(self, location_id: str) -> Dict[str, Any]:
        """Move to a connected location if the route and requirements allow it."""
        result = self.travel.travel_to(self.player, location_id)
        if result.get("event") != EventType.TRAVEL_RESULT:
            return result
        updates = self.quests.notify("visit_location", self.player, self.inventory, target=location_id)
        if updates:
            result["quest_updates"] = updates
        return result

    def _map(self) -> Dict[str, Any]:
        """Return a text-map view: current location's map position and exits."""
        view = self.locations.view(self.player.current_location)
        return MapResult(
            location_name=view.get("name", self.player.current_location),
            map_position=view.get("map_position", {}),
            destinations=self.travel.get_available_destinations(self.player),
        ).to_dict()

    def _techniques(self) -> Dict[str, Any]:
        """Return the player's known techniques (active + passive)."""
        return TechniquesResult(skills=self.get_known_skills()).to_dict()

    def _talents(self) -> Dict[str, Any]:
        """Return the player's Martial/Body talents and their upgrade paths."""
        return TalentsResult(
            martial_talent=self.starting_fate.martial_talent_view(self.player.martial_talent_id),
            body_talent=self.starting_fate.body_talent_view(self.player.body_talent_id),
            martial_upgrades=self.starting_fate.upgrade_options_view("martial", self.player.martial_talent_id),
            body_upgrades=self.starting_fate.upgrade_options_view("body", self.player.body_talent_id),
        ).to_dict()

    def _upgrade_talent(self, track: str, target_id: str) -> Dict[str, Any]:
        """Upgrade a Martial or Body talent to the next grade, spending its cost."""
        if track not in ("martial", "body"):
            return {"event": EventType.ERROR, "reason": "INVALID_TALENT_TRACK", "track": track}
        current_id = self.player.martial_talent_id if track == "martial" else self.player.body_talent_id
        options = self.starting_fate.upgrade_options_view(track, current_id)
        target = next((option for option in options if option.get("target_id") == target_id), None)
        if target is None:
            return {"event": EventType.ERROR, "reason": "INVALID_UPGRADE_TARGET", "target_id": target_id}
        cost = target.get("cost") or {}
        missing = {}
        for item_id, quantity in cost.items():
            needed = int(quantity)
            if int(self.player.inventory.get(item_id, 0)) < needed:
                missing[item_id] = needed - int(self.player.inventory.get(item_id, 0))
        if missing:
            return {
                "event": EventType.ERROR,
                "reason": "INSUFFICIENT_RESOURCES",
                "required": {str(item_id): int(quantity) for item_id, quantity in cost.items()},
                "missing": missing,
                "inventory": dict(self.player.inventory),
            }
        for item_id, quantity in cost.items():
            self.inventory.remove_item(self.player, item_id, int(quantity))
        if track == "martial":
            self.player.martial_talent_id = target_id
        else:
            self.player.body_talent_id = target_id
        first_resource = next(iter(cost), "")
        return TalentUpgradedResult(
            track=track,
            talent_id=target_id,
            display_name=str(target.get("target_name", target_id)),
            player_message=f"Your {track} talent advances to {target.get('target_name', target_id)}.",
            wallet={first_resource: int(self.player.inventory.get(first_resource, 0))},
        ).to_dict()

    def _closed_door(self, years: Any) -> Dict[str, Any]:
        """Deliberately cultivate in seclusion for ``years``, ageing accordingly."""
        config = self._cultivation_config.get("closed_door", {})
        options = config.get("options", [])
        chosen = None
        for option in options:
            if isinstance(option, dict) and option.get("years") == years:
                chosen = option
                break
        if chosen is None:
            return {"event": EventType.ERROR, "reason": "INVALID_CLOSED_DOOR_YEARS", "years": years}
        gain = float(chosen.get("progress_gain", 0.0))
        body = self.player.cultivation_state.body
        body.progress = round(float(body.progress) + gain, 2)
        self.player.progress = body.progress
        # A deliberate seclusion ages the player by exactly the chosen years.
        self.player.age_years = round(float(self.player.age_years) + float(years), 4)
        # A multi-year seclusion restores the body to full vigour.
        self.player.heal(self.player.max_hp)
        self.player.restore_qi(self.player.max_qi)
        essence_unlocked = self.cultivation.is_essence_unlocked(self.player)
        lifespan = self.lifespan.lifespan_view(self.player, essence_unlocked)
        result = ClosedDoorResult(
            years=float(years),
            progress_gained=gain,
            progress=body.progress,
            player_message=f"You seclude yourself for {years} year(s), and your body's foundation deepens.",
            lifespan=lifespan,
        ).to_dict()
        if self.lifespan.is_expired(self.player, essence_unlocked):
            return self._die_of_old_age(result)
        return result

    def _after_breakthrough(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Notify quests on a successful breakthrough and attach any updates."""
        if result.get("success"):
            updates = self.quests.notify("breakthrough", self.player, self.inventory)
            if updates:
                result["quest_updates"] = updates
        return result

    def _talk_to_character(self, character_id: str) -> Dict[str, Any]:
        if not character_id:
            return {"event": EventType.ERROR, "reason": "NO_CHARACTER_SPECIFIED"}
        character = self.character_service.get_character(character_id)
        if character is None:
            return {"event": EventType.ERROR, "reason": "UNKNOWN_CHARACTER", "character_id": character_id}
        hooks = character.get("gameplay_hooks", {})
        if not hooks.get("can_talk", False):
            return {"event": EventType.ERROR, "reason": "NOT_AVAILABLE", "character_id": character_id}
        context = self.character_service.get_dialogue_context(character_id, self.player)
        if context is None:
            return {"event": EventType.ERROR, "reason": "UNKNOWN_CHARACTER", "character_id": character_id}
        message_parts = [
            context.get("intro_text") or context.get("repeat_text") or "They acknowledge you.",
            context.get("morality_reaction", ""),
            context.get("relationship_behavior", ""),
        ]
        message = " ".join(part for part in message_parts if part).strip()
        return CharacterInteractionResult(
            interaction="talk",
            character_id=character_id,
            name=context.get("name", character_id),
            dialogue_context=context,
            player_message=message,
            choices=self.character_service.dialogue_choices(character_id, self.player),
            speech_notes=context.get("ai_prompt_notes") or None,
        ).to_dict()

    def _dialogue_choose(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a chosen dialogue option's relationship/morality/reputation deltas."""
        character_id = action.get("character_id", "")
        choice_id = action.get("choice_id", "")
        if not character_id or not choice_id:
            return {"event": EventType.ERROR, "reason": "NO_CHOICE_SPECIFIED"}
        choice = self.character_service.get_dialogue_choice(character_id, choice_id, self.player)
        if choice is None:
            return {
                "event": EventType.ERROR,
                "reason": "CHOICE_NOT_AVAILABLE",
                "character_id": character_id,
                "choice_id": choice_id,
            }

        relationship = None
        relationship_delta = choice.get("relationship_delta") or {}
        if relationship_delta:
            relationship = self.relationships.adjust(
                self.player.relationships, character_id, relationship_delta
            )

        morality = self.morality.adjust(self.player.morality, int(choice.get("morality_delta", 0)))
        self.player.morality = morality["morality"]

        reputation_delta = int(choice.get("reputation_delta", 0))
        self.player.reputation += reputation_delta
        # Reputation can satisfy a quest's unlock gate without any notify event.
        self.quests.check_unlocks(self.player)

        return DialogueChoiceResult(
            character_id=character_id,
            choice_id=choice_id,
            name=str(choice.get("character_name", character_id)),
            player_message=str(choice.get("response", "")),
            relationship=relationship,
            morality=morality,
            reputation=self.player.reputation,
            reputation_delta=reputation_delta,
        ).to_dict()

    def _receive_boon(self, character_id: str) -> Dict[str, Any]:
        """Grant an NPC's currently-available relationship reward (one-time)."""
        if not character_id:
            return {"event": EventType.ERROR, "reason": "NO_CHARACTER_SPECIFIED"}
        available = self.character_service.available_reward(character_id, self.player)
        if available is None:
            return {"event": EventType.ERROR, "reason": "NO_REWARD_AVAILABLE", "character_id": character_id}
        reward = available.get("reward", {})
        granted: Dict[str, Any] = {}
        if "gold" in reward:
            amount = int(reward["gold"])
            self.player.gold += amount
            granted["gold"] = amount
        if "exp" in reward:
            amount = int(reward["exp"])
            self.player.exp += amount
            granted["exp"] = amount
        item_id = reward.get("item_id")
        if item_id:
            count = int(reward.get("count", 1))
            self.inventory.add_item(self.player, item_id, count)
            granted["items"] = {item_id: count}
        skill_id = reward.get("skill_id")
        if skill_id:
            learned = self.techniques.learn_skill(self.player, skill_id, source="boon")
            if learned.get("event") == EventType.SKILL_LEARNED:
                granted["skill_id"] = skill_id
        # Mark the reward claimed so ``once`` rewards never fire twice.
        self.relationships.remember(
            self.player.relationships,
            character_id,
            action="received_reward",
            flag=f"reward_{available['index']}",
        )
        return BoonResult(
            character_id=character_id,
            name=available.get("name", character_id),
            player_message=str(available.get("message") or "They offer you a gift in recognition of your bond."),
            reward=granted,
            wallet={"gold": self.player.gold},
        ).to_dict()

    def _start_character_combat(self, character_id: str, interaction: str) -> Dict[str, Any]:
        if not character_id:
            return {"event": EventType.ERROR, "reason": "NO_CHARACTER_SPECIFIED"}
        gate = (
            self.character_service.can_spar(character_id, self.player)
            if interaction == "spar"
            else self.character_service.can_duel(character_id, self.player)
        )
        if not gate.get("allowed"):
            return {
                "event": EventType.ERROR,
                "reason": gate.get("reason", "NOT_AVAILABLE"),
                "character_id": character_id,
            }
        enemy_id = gate.get("enemy_id", "")
        if not enemy_id:
            return {"event": EventType.ERROR, "reason": "NO_CHARACTER_ENEMY", "character_id": character_id}
        enemy = self._spawn_character_enemy(enemy_id)
        if enemy is None:
            return {"event": EventType.ERROR, "reason": "UNKNOWN_ENEMY", "character_id": character_id, "enemy_id": enemy_id}
        self._current_enemy = enemy
        self._mode = MODE_COMBAT
        self._cooldowns = {}
        self._combat_is_spar = interaction == "spar"
        self.player.statuses.clear()
        self.player.shield = 0
        label = "sparring match" if interaction == "spar" else "duel"
        return {
            "event": EventType.COMBAT,
            "interaction": interaction,
            "character_id": character_id,
            "enemy": self._enemy_view(enemy),
            "text": f"You begin a {label} with {enemy.name}.",
        }

    def _equip_item(self, action: Dict[str, Any]) -> Dict[str, Any]:
        result = self.equipment.equip_item(self.player, action.get("item_id", ""), action.get("slot", ""))
        if result.get("event") != EventType.ERROR:
            result["effective_stats"] = self.stats.effective_stats(self.player)
        return result

    def _unequip_item(self, action: Dict[str, Any]) -> Dict[str, Any]:
        result = self.equipment.unequip_item(self.player, action.get("slot", ""), action.get("item_id", ""))
        if result.get("event") != EventType.ERROR:
            result["effective_stats"] = self.stats.effective_stats(self.player)
        return result

    def _buy_item(self, action: Dict[str, Any]) -> Dict[str, Any]:
        quantity = action.get("quantity", 1)
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return {"event": EventType.ERROR, "reason": "INVALID_QUANTITY", "quantity": quantity}
        result = self.shops.buy_item(
            self.player,
            action.get("item_id", ""),
            quantity,
            action.get("shop_id", ""),
        )
        if result.get("event") != EventType.ERROR:
            result["inventory_items"] = self.inventory.list_inventory(self.player)["items"]
        return result

    def _sell_item(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Sell owned items/equipment for gold."""
        quantity = action.get("quantity", 1)
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return {"event": EventType.ERROR, "reason": "INVALID_QUANTITY", "quantity": quantity}
        result = self.sell.sell_item(self.player, action.get("item_id", ""), quantity)
        if result.get("event") != EventType.ERROR:
            result["inventory_items"] = self.inventory.list_inventory(self.player)["items"]
        return result

    def _repair_item(self, item_id: str) -> Dict[str, Any]:
        """Repair an equipped piece of worn gear, spending gold per durability point."""
        result = self.equipment.repair_item(self.player, item_id)
        if result.get("event") == EventType.REPAIR_RESULT:
            result["equipment_details"] = self.equipment.equipment_details(self.player)
            result["effective_stats"] = self.stats.effective_stats(self.player)
            result["wallet"] = {"gold": self.player.gold}
        return result

    def _use_item(self, item_id: str) -> Dict[str, Any]:
        """Use an item in exploration; technique manuals teach their skill instead."""
        item = self._items.get(item_id)
        if item is not None and item.effect == "learn_skill" and item.skill_id:
            if self.player.inventory.get(item_id, 0) <= 0:
                return {"event": EventType.ERROR, "reason": "ITEM_NOT_OWNED", "item_id": item_id}
            result = self.techniques.learn_skill(self.player, item.skill_id, source="manual")
            if result.get("event") == EventType.SKILL_LEARNED:
                self.inventory.remove_item(self.player, item_id, 1)
                result["item_id"] = item_id
                result["inventory_items"] = self.inventory.list_inventory(self.player)["items"]
            return result
        return self.inventory.use_item(self.player, item_id)

    def _learn_skill(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Learn a technique from a location trainer, paying its currency cost."""
        result = self.trainers.learn(
            self.player,
            action.get("skill_id", ""),
            action.get("trainer_id", ""),
        )
        if result.get("event") == EventType.SKILL_LEARNED:
            result["known_skills"] = self.get_known_skills()
        return result

    def _join_sect(self, sect_id: str) -> Dict[str, Any]:
        """Join a sect, assigning the player's martial path."""
        result = self.sects.join(self.player, sect_id)
        if result.get("event") == EventType.SECT_JOINED:
            result["player"] = self._player_view()
        return result

    def _find_rarity_index(self) -> int:
        """Return the max find rarity index allowed by the current area's danger."""
        danger = self._location_danger.get(self.player.current_location, 0)
        return self.find_system.max_rarity_index_for_danger(danger)

    def _advance_day_after(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Advance the minimal backend day after successful recovery actions."""
        if result.get("event") != EventType.ERROR:
            self.player.current_day += 1
            result["current_day"] = self.player.current_day
        return result

    def _advance_time_after(self, result: Dict[str, Any], action_key: str) -> Dict[str, Any]:
        """Age the player by an action's time cost and enforce lifespan limits."""
        if result.get("event") == EventType.ERROR:
            return result
        essence_unlocked = self.cultivation.is_essence_unlocked(self.player)
        self.lifespan.advance_age(self.player, action_key, essence_unlocked)
        result["lifespan"] = self.lifespan.lifespan_view(self.player, essence_unlocked)
        if self.lifespan.is_expired(self.player, essence_unlocked):
            return self._die_of_old_age(result)
        return result

    def _die_of_old_age(self, last_event: Dict[str, Any]) -> Dict[str, Any]:
        """End the run when the player's lifespan is exhausted (permanent death)."""
        self._running = False
        self._mode = MODE_EXPLORE
        self._current_enemy = None
        return PlayerDiedResult(
            cause="old_age",
            age_years=round(float(self.player.age_years), 1),
            player_message=(
                "Your lifespan is exhausted. The dao you chased slips away as your "
                "body returns to dust."
            ),
            last_event=last_event,
        ).to_dict()

    def _roll_starting_fate(self) -> Dict[str, Any]:
        """Roll and store a pending starting fate for the current new game."""
        self._pending_fate = self.starting_fate.roll()
        self._fate_accepted = False
        return self._pending_fate

    def _assign_new_game_fate(self) -> None:
        """Roll and immediately apply starting talents for a playable new game."""
        fate = self.starting_fate.roll()
        self.player.martial_talent_id = str(fate["martial_talent_id"])
        self.player.body_talent_id = str(fate["body_talent_id"])
        self._pending_fate = None
        self._fate_accepted = True

    def _roll_starting_fate_result(self) -> Dict[str, Any]:
        """Return the current pending fate, rolling one if none exists yet."""
        if self._fate_accepted:
            return {"event": EventType.ERROR, "reason": "FATE_ALREADY_ACCEPTED"}
        fate = self._pending_fate or self._roll_starting_fate()
        # The rolled "fate" is the character's Martial and Body Talents. The
        # result keeps the legacy spiritual_root/physique field names so existing
        # text frontends keep working; the values are the talent views.
        return StartingFateRolledResult(
            spiritual_root_id=str(fate["martial_talent_id"]),
            physique_id=str(fate["body_talent_id"]),
            spiritual_root=dict(fate["martial_talent"]),
            physique=dict(fate["body_talent"]),
            requires_fate_acceptance=True,
            player_message="Your starting talents have been revealed.",
        ).to_dict()

    def _accept_starting_fate(self) -> Dict[str, Any]:
        """Apply the pending fate to the player and open normal gameplay."""
        if self._fate_accepted:
            return {"event": EventType.ERROR, "reason": "FATE_ALREADY_ACCEPTED"}
        fate = self._pending_fate or self._roll_starting_fate()
        self.player.martial_talent_id = str(fate["martial_talent_id"])
        self.player.body_talent_id = str(fate["body_talent_id"])
        self._pending_fate = None
        self._fate_accepted = True
        return StartingFateAcceptedResult(
            success=True,
            spiritual_root_id=self.player.martial_talent_id,
            physique_id=self.player.body_talent_id,
            spiritual_root=self.starting_fate.martial_talent_view(self.player.martial_talent_id),
            physique=self.starting_fate.body_talent_view(self.player.body_talent_id),
            player_message="You accept your starting talents and step onto the path.",
        ).to_dict()

    def _pending_fate_view(self) -> Optional[Dict[str, Any]]:
        if not self._pending_fate:
            return None
        return {
            "martial_talent_id": self._pending_fate["martial_talent_id"],
            "body_talent_id": self._pending_fate["body_talent_id"],
            "martial_talent": dict(self._pending_fate["martial_talent"]),
            "body_talent": dict(self._pending_fate["body_talent"]),
        }

    def _bind_equipment_modifiers(self) -> None:
        setattr(self.player, "equipment_modifiers", lambda: self.equipment.aggregate_modifiers(self.player))

    # -- persistence -----------------------------------------------------
    def _session_snapshot(self) -> Dict[str, Any]:
        return {
            "player": self.player.to_save_dict(),
            "quests": self.quests.export_state(),
            "ng_plus": self._ng_plus,
            "ironman": self._ironman,
        }

    def save_game(self, slot: str = "default") -> Dict[str, Any]:
        """Persist the current session to a named save slot."""
        try:
            self.saves.write(slot or "default", self._session_snapshot())
        except SaveError as exc:
            return {"event": EventType.SAVE_RESULT, "success": False, "reason": exc.code, "slot": slot}
        return {"event": EventType.SAVE_RESULT, "success": True, "slot": slot or "default"}

    def _export_save(self) -> Dict[str, Any]:
        """Return the current session as a portable JSON string (cloud substitute)."""
        snapshot = self._session_snapshot()
        snapshot["version"] = SAVE_VERSION
        payload = json.dumps(snapshot, sort_keys=True)
        return SaveExportedResult(
            payload=payload,
            player_message="Your journey has been transcribed into a portable record.",
        ).to_dict()

    def _import_save(self, payload: str, slot: str) -> Dict[str, Any]:
        """Restore a session from a portable JSON string into ``slot``."""
        if not payload:
            return {"event": EventType.ERROR, "reason": "IMPORT_EMPTY"}
        try:
            data = json.loads(payload)
        except (ValueError, TypeError):
            return {"event": EventType.ERROR, "reason": "IMPORT_INVALID"}
        if not isinstance(data, dict) or "player" not in data:
            return {"event": EventType.ERROR, "reason": "IMPORT_INVALID"}
        try:
            self.saves.write(slot or "default", data)
        except SaveError as exc:
            return {"event": EventType.ERROR, "reason": exc.code}
        loaded = self.load_game(slot or "default")
        return SaveImportedResult(
            success=bool(loaded.get("success")),
            slot=slot or "default",
            player_message="Your journey has been restored from the portable record.",
        ).to_dict()

    def load_game(self, slot: str = "default") -> Dict[str, Any]:
        """Restore a session from a named save slot, replacing current state."""
        if self._ironman:
            return {"event": EventType.LOAD_RESULT, "success": False, "reason": "IRONMAN_MODE", "slot": slot}
        try:
            data = self.saves.read(slot or "default")
        except SaveError as exc:
            return {"event": EventType.LOAD_RESULT, "success": False, "reason": exc.code, "slot": slot}
        self.player = Player.from_save_dict(data.get("player", {}))
        self._bind_equipment_modifiers()
        self.cultivation_service = CultivationService({"player": self.player}, self.cultivation)
        self.quests.import_state(data.get("quests", {}))
        self._ng_plus = max(0, int(data.get("ng_plus", 0)))
        self._ironman = bool(data.get("ironman", False))
        self._mode = MODE_EXPLORE
        self._current_enemy = None
        self._cooldowns = {}
        self._pending_fate = None
        self._fate_accepted = True
        return {
            "event": EventType.LOAD_RESULT,
            "success": True,
            "slot": slot or "default",
            "player": self._player_view(),
        }

    # -- combat helpers ---------------------------------------------------
    def _use_combat_skill(self, skill_id: str) -> Dict[str, Any]:
        """Validate and resolve an active-skill activation in combat."""
        if not skill_id:
            return {"event": EventType.ERROR, "reason": "NO_SKILL_SPECIFIED"}
        if skill_id not in self.player.skills:
            return {"event": EventType.ERROR, "reason": "SKILL_NOT_KNOWN", "skill_id": skill_id}
        skill = self._skills.get(skill_id)
        if skill is None or not skill.is_active():
            return {"event": EventType.ERROR, "reason": "SKILL_NOT_USABLE", "skill_id": skill_id}
        if self._current_enemy is None:
            self._mode = MODE_EXPLORE
            return {"event": EventType.ERROR, "reason": "NOT_IN_COMBAT"}
        remaining = self._cooldowns.get(skill_id, 0)
        if remaining > 0:
            return {
                "event": EventType.ERROR,
                "reason": "SKILL_ON_COOLDOWN",
                "skill_id": skill_id,
                "remaining": remaining,
            }
        qi_cost = self.stats.effective_qi_cost(skill, self.player)
        if self.player.qi < qi_cost:
            return {
                "event": EventType.ERROR,
                "reason": "NOT_ENOUGH_QI",
                "required": qi_cost,
                "qi": self.player.qi,
            }

        self.player.qi -= qi_cost
        result = self.combat.use_skill(self.player, self._current_enemy, skill, spar=self._combat_is_spar)
        # Tick existing cooldowns for the elapsed turn, then arm this skill so it
        # is unavailable for exactly ``skill.cooldown`` of the player's turns.
        self._tick_cooldowns()
        self._cooldowns[skill_id] = skill.cooldown
        return result

    def _use_combat_item(self, item_id: str) -> Dict[str, Any]:
        """Use an item during combat; this consumes the player's turn."""
        if self._current_enemy is None:
            self._mode = MODE_EXPLORE
            return {"event": EventType.ERROR, "reason": "NOT_IN_COMBAT"}
        item = self._items.get(item_id)
        if item is not None and item.effect == "learn_skill":
            return {"event": EventType.ERROR, "reason": "CANNOT_STUDY_IN_COMBAT", "item_id": item_id}
        item_result = self.inventory.use_item(self.player, item_id)
        if item_result.get("event") == EventType.ERROR:
            return item_result

        enemy_turn = self.combat.enemy_turn_only(self.player, self._current_enemy, spar=self._combat_is_spar)
        self._tick_cooldowns()

        item_event = {
            "actor": "PLAYER",
            "action": "USE_ITEM",
            "item": item_result.get("name"),
            "healed": item_result.get("healed"),
            "qi_restored": item_result.get("qi_restored"),
        }
        enemy_turn["turn_events"] = [item_event] + enemy_turn.get("turn_events", [])
        return enemy_turn

    def _end_combat(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve the consequences of a finished fight and leave combat mode."""
        outcome = result.get("outcome")
        enemy_id = self._current_enemy.id if self._current_enemy else "any"
        self._mode = MODE_EXPLORE
        self._current_enemy = None
        self._cooldowns = {}
        self.player.statuses.clear()
        self.player.shield = 0
        self._combat_is_spar = False

        if outcome == "VICTORY":
            result["loot"] = self.loot.roll_loot(self.player, result.get("loot_table", []))
            updates = self.quests.notify("defeat", self.player, self.inventory, target=enemy_id)
            if updates:
                result["quest_updates"] = updates
        elif outcome == "DEFEAT":
            self._apply_defeat_penalty(result)
        elif outcome in ("SPAR_WON", "SPAR_LOST"):
            self._apply_spar_end(result)
        return result

    def _apply_spar_end(self, result: Dict[str, Any]) -> None:
        """A friendly spar ends with no loot or progress loss; the loser is patched up."""
        if result.get("outcome") == "SPAR_LOST":
            self.player.hp = max(self.player.hp, self.player.max_hp // 2)
            self.player.qi = max(self.player.qi, self.player.max_qi // 2)
        result["spar"] = True

    def _apply_defeat_penalty(self, result: Dict[str, Any]) -> None:
        """Defeat is not game over: the player is rescued at a data-driven cost."""
        cfg = self._cultivation_config.get("defeat_penalty", {})
        loss_ratio = float(cfg.get("progress_loss_ratio", 1.0))
        hp_ratio = float(cfg.get("revive_hp_ratio", 0.5))
        qi_ratio = float(cfg.get("revive_qi_ratio", 0.5))

        body = self.player.cultivation_state.body
        lost = round(float(body.progress) * loss_ratio, 1)
        body.progress = max(0.0, float(body.progress) - lost)
        self.player.progress = body.progress
        self.player.hp = max(1, int(self.player.max_hp * hp_ratio))
        self.player.qi = int(self.player.max_qi * qi_ratio)
        degraded = self.equipment.degrade_equipped(self.player, 1)
        penalty = {"progress_lost": lost, "revived_hp": self.player.hp}
        if degraded:
            penalty["equipment_degraded"] = degraded
        result["penalty"] = penalty

    def _tick_cooldowns(self) -> None:
        for skill_id in list(self._cooldowns.keys()):
            self._cooldowns[skill_id] = max(0, self._cooldowns[skill_id] - 1)

    # -- status -----------------------------------------------------------
    def _status(self) -> Dict[str, Any]:
        data = self._player_view()
        data["skills"] = [self._skill_brief(skill_id) for skill_id in self.player.skills]
        data["cooldowns"] = dict(self._cooldowns)
        return {"event": EventType.STATUS, "player": data}

    def _player_view(self) -> Dict[str, Any]:
        data = self.player.to_dict()
        # Show effective defense (base + always-on passives) rather than the
        # pristine base value stored on the player.
        data["defense"] = self.stats.effective_defense(self.player)
        cultivation_state = self.cultivation_service.get_cultivation_state("player")
        data["cultivation_state"] = cultivation_state
        data["cultivation"] = cultivation_state["summary"]
        data["progress"] = cultivation_state["body_transformation"]["progress"]
        data["realm"] = cultivation_state["body_transformation"]["display_name"]
        data["essence_progress"] = cultivation_state["essence_gathering"]["progress"]
        data["essence_cultivation"] = cultivation_state["essence_gathering"]["display_name"]
        data["essence_unlocked"] = cultivation_state.get("essence_unlocked", True)
        data["martial_talent"] = self.starting_fate.martial_talent_view(self.player.martial_talent_id)
        data["body_talent"] = self.starting_fate.body_talent_view(self.player.body_talent_id)
        data["lifespan"] = self.lifespan.lifespan_view(self.player, cultivation_state.get("essence_unlocked", True))
        data["equipment_details"] = self.equipment.equipment_details(self.player)
        data["equipment_modifiers"] = self.equipment.aggregate_modifiers(self.player)
        data["effective_stats"] = self.stats.effective_stats(self.player)
        data["shield"] = self.player.shield
        data["statuses"] = {k: dict(v) for k, v in self.player.statuses.items()}
        return data

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

    def _skill_brief(self, skill_id: str) -> Dict[str, Any]:
        skill = self._skills.get(skill_id)
        if skill is None:
            return {"id": skill_id, "name": skill_id, "type": "unknown"}
        return {
            "id": skill_id,
            "name": skill.name,
            "type": skill.type,
            "qi_cost": skill.qi_cost,
            "cooldown": skill.cooldown,
            "description": skill.description,
        }
