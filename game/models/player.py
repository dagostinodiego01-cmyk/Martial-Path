"""Player model.

Holds the player's persistent state and offers small, self-contained state
transitions (take damage, heal, restore qi). All *rules* — how much training
advances progress, breakthrough odds, damage formulas — live in the systems, not
here. The model has no knowledge of the UI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from game.models.cultivation import CultivationState


EQUIPMENT_SLOTS = (
    "weapon",
    "armor",
    "boots",
    "cloak",
    "ring_1",
    "ring_2",
    "amulet",
    "talisman",
    "artifact_1",
    "artifact_2",
    "flying_sword",
)


def empty_equipment_slots() -> Dict[str, str | None]:
    return {slot: None for slot in EQUIPMENT_SLOTS}


@dataclass
class Player:
    """The player-controlled cultivator."""

    name: str
    realm: str = "Mortal"
    stage: int = 1
    progress: float = 0.0
    cultivation_state: CultivationState = field(default_factory=CultivationState)
    max_hp: int = 100
    hp: int = 100
    max_qi: int = 50
    qi: int = 50
    attack: int = 15
    defense: int = 5
    speed: int = 10
    evasion: int = 5
    # Cultivation identity and extended attributes. A few carry light gameplay
    # hooks (comprehension -> breakthrough odds, body_strength -> HP/attack on
    # breakthrough); the rest are tracked display values for now. All rules live
    # in the systems, never in this model.
    path: str = "Unassigned"
    # The cultivator's Dao (see ``data/daos.json``). Defaults to the starter Dao;
    # a later "Dao awakening" beat can swap it. ``dao_system.DaoSystem`` reads it
    # for realm-pressure and counter-graph combat math.
    dao_id: str = "sword_dao"
    # The starting origin that shaped this run (see ``data/origins.json``).
    # Persisted so a loaded run (and the chronicle) remembers where it began.
    origin_id: str = "orphan"
    foundation_quality: int = 50
    body_strength: int = 10
    soul_strength: int = 10
    comprehension: int = 10
    reputation: int = 0
    morality: int = 0
    # Highest story tier (1-6) the player has reached: sect tiers and who the
    # world sends to meet the player scale with it. Written by the engine on
    # arrival; the model only holds the data.
    max_story_tier: int = 1
    # Flat years added to the realm-derived maximum lifespan by ``lifespan``
    # passive techniques. Applied on learn, honoured by LifespanSystem.
    lifespan_bonus_years: float = 0.0
    current_location: str = "outer_forest"
    current_day: int = 1
    age_years: float = 12.0
    martial_talent_id: str = "earth_grade"
    body_talent_id: str = "iron_skin_grade"
    exp: int = 0
    gold: int = 0
    inventory: Dict[str, int] = field(default_factory=dict)
    equipment: Dict[str, str | None] = field(default_factory=empty_equipment_slots)
    # Per-slot current durability for equipment that declares a ``durability``
    # maximum. Missing/0 means the item is indestructible or has no durability
    # model; a value of 0 with a non-zero max means the item is broken (provides
    # no modifiers until repaired).
    equipment_durability: Dict[str, int] = field(default_factory=dict)
    skills: List[str] = field(default_factory=list)
    # Per-NPC relationship store: {npc_id: {relationship_score, trust, fear, ...}}.
    # Interpreted by the RelationshipSystem; the model only holds the data.
    relationships: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # Transient combat state (never persisted): a damage-absorption shield and
    # timed status effects (e.g. counter). Reset by the engine on combat end.
    shield: int = 0
    statuses: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # Insight (B.5): a mid-fight resource built from comprehension and successful
    # exchanges; gates techniques with ``insight_required``. Transient like
    # ``shield``/``statuses`` -- reset each fight, never persisted.
    insight: int = 0
    # Combos (B.6): how many stages of the opening -> response -> finisher
    # stance chain are currently banked (0-2; 3 wraps to 0 on completion).
    # Transient like ``insight`` -- reset each fight, never persisted.
    combo_stage: int = 0

    def __post_init__(self) -> None:
        """Keep legacy single-progress construction aligned with body progress."""
        if self.progress:
            self.cultivation_state.body.progress = self.progress

    def is_alive(self) -> bool:
        """Return ``True`` while the player still has HP."""
        return self.hp > 0

    def take_damage(self, amount: int) -> int:
        """Apply ``amount`` damage (clamped at 0 HP) and return damage dealt."""
        dealt = max(0, amount)
        self.hp = max(0, self.hp - dealt)
        return dealt

    def heal(self, amount: int) -> int:
        """Restore up to ``amount`` HP (clamped at max) and return HP recovered."""
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before

    def restore_qi(self, amount: int) -> int:
        """Restore up to ``amount`` Qi (clamped at max) and return Qi recovered."""
        before = self.qi
        self.qi = min(self.max_qi, self.qi + amount)
        return self.qi - before

    def cultivation_title(self) -> str:
        """Return a fallback display title for the current cultivation state."""
        body = self.cultivation_state.body.realm_id.replace("_", " ").title()
        essence_id = self.cultivation_state.essence.realm_id.replace("_", " ").title()
        essence = f"{self.cultivation_state.essence.substage} {essence_id}".strip()
        return f"Body Transformation: {body} | Essence Gathering: {essence}"

    def to_dict(self) -> Dict[str, Any]:
        """Return a UI-safe snapshot of the full player sheet."""
        return {
            "name": self.name,
            "realm": self.realm,
            "stage": self.stage,
            "cultivation": self.cultivation_title(),
            "progress": round(self.cultivation_state.body.progress, 1),
            "cultivation_state": self.cultivation_state.to_dict(),
            "hp": self.hp,
            "max_hp": self.max_hp,
            "qi": self.qi,
            "max_qi": self.max_qi,
            "attack": self.attack,
            "defense": self.defense,
            "speed": self.speed,
            "evasion": self.evasion,
            "path": self.path,
            "dao_id": self.dao_id,
            "origin_id": self.origin_id,
            "foundation_quality": self.foundation_quality,
            "body_strength": self.body_strength,
            "soul_strength": self.soul_strength,
            "comprehension": self.comprehension,
            "reputation": self.reputation,
            "morality": self.morality,
            "max_story_tier": self.max_story_tier,
            "lifespan_bonus_years": self.lifespan_bonus_years,
            "current_location": self.current_location,
            "current_day": self.current_day,
            "age_years": round(self.age_years, 2),
            "martial_talent_id": self.martial_talent_id,
            "body_talent_id": self.body_talent_id,
            "exp": self.exp,
            "gold": self.gold,
            "inventory": dict(self.inventory),
            "equipment": dict(self.equipment),
            "equipment_durability": dict(self.equipment_durability),
            "skills": list(self.skills),
            "relationships": {
                npc_id: dict(state) for npc_id, state in self.relationships.items()
            },
        }

    def to_save_dict(self) -> Dict[str, Any]:
        """Return a faithful, round-trippable snapshot for the save system."""
        return {
            "name": self.name,
            "realm": self.realm,
            "stage": self.stage,
            "progress": self.progress,
            "cultivation_state": self.cultivation_state.to_dict(),
            "max_hp": self.max_hp,
            "hp": self.hp,
            "max_qi": self.max_qi,
            "qi": self.qi,
            "attack": self.attack,
            "defense": self.defense,
            "speed": self.speed,
            "evasion": self.evasion,
            "path": self.path,
            "dao_id": self.dao_id,
            "origin_id": self.origin_id,
            "foundation_quality": self.foundation_quality,
            "body_strength": self.body_strength,
            "soul_strength": self.soul_strength,
            "comprehension": self.comprehension,
            "reputation": self.reputation,
            "morality": self.morality,
            "max_story_tier": self.max_story_tier,
            "lifespan_bonus_years": self.lifespan_bonus_years,
            "current_location": self.current_location,
            "current_day": self.current_day,
            "age_years": self.age_years,
            "martial_talent_id": self.martial_talent_id,
            "body_talent_id": self.body_talent_id,
            "exp": self.exp,
            "gold": self.gold,
            "inventory": dict(self.inventory),
            "equipment": dict(self.equipment),
            "equipment_durability": dict(self.equipment_durability),
            "skills": list(self.skills),
            "relationships": {
                npc_id: dict(state) for npc_id, state in self.relationships.items()
            },
        }

    @classmethod
    def from_save_dict(cls, data: Dict[str, Any]) -> "Player":
        """Reconstruct a Player from a :meth:`to_save_dict` snapshot."""
        player = cls(
            name=str(data.get("name", "Daoist")),
            realm=str(data.get("realm", "Strength Training")),
            stage=int(data.get("stage", 1)),
            progress=float(data.get("progress", 0.0)),
            max_hp=int(data.get("max_hp", 100)),
            hp=int(data.get("hp", 100)),
            max_qi=int(data.get("max_qi", 50)),
            qi=int(data.get("qi", 50)),
            attack=int(data.get("attack", 15)),
            defense=int(data.get("defense", 5)),
            speed=int(data.get("speed", 10)),
            evasion=int(data.get("evasion", 5)),
            path=str(data.get("path", "Unassigned")),
            dao_id=str(data.get("dao_id", "sword_dao")),
            origin_id=str(data.get("origin_id", "orphan")),
            foundation_quality=int(data.get("foundation_quality", 50)),
            body_strength=int(data.get("body_strength", 10)),
            soul_strength=int(data.get("soul_strength", 10)),
            comprehension=int(data.get("comprehension", 10)),
            reputation=int(data.get("reputation", 0)),
            morality=int(data.get("morality", 0)),
            max_story_tier=int(data.get("max_story_tier", 1)),
            lifespan_bonus_years=float(data.get("lifespan_bonus_years", 0.0)),
            current_location=str(data.get("current_location", "outer_forest")),
            current_day=int(data.get("current_day", 1)),
            age_years=float(data.get("age_years", 12.0)),
            martial_talent_id=str(data.get("martial_talent_id", "earth_grade")),
            body_talent_id=str(data.get("body_talent_id", "iron_skin_grade")),
            exp=int(data.get("exp", 0)),
            gold=int(data.get("gold", 0)),
            inventory=dict(data.get("inventory", {})),
            equipment=_equipment_from_save(data.get("equipment", {})),
            equipment_durability={
                str(slot): int(value)
                for slot, value in data.get("equipment_durability", {}).items()
            },
            skills=list(data.get("skills", [])),
            relationships={
                npc_id: dict(state) for npc_id, state in data.get("relationships", {}).items()
            },
        )
        if "cultivation_state" in data:
            player.cultivation_state = CultivationState.from_dict(data["cultivation_state"])
        return player


def _equipment_from_save(data: Any) -> Dict[str, str | None]:
    equipment = empty_equipment_slots()
    if isinstance(data, dict):
        for slot in EQUIPMENT_SLOTS:
            value = data.get(slot)
            equipment[slot] = str(value) if value else None
    return equipment
