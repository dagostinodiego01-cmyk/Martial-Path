"""Central registry of all static game data.

One validated source of truth for the content that ships with the game. Loading
happens once (``GameDataRegistry.load()``); systems and the engine then read from
the registry instead of each re-reading JSON. This keeps data access in one place,
makes validation straightforward, and turns "where does this content come from?"
into a single answer.

The registry holds *raw* data (lists/dicts as they appear on disk). Turning raw
entries into models (``Item``, ``Skill``, ...) stays the caller's job, so the
registry has no dependency on the model or system layers and can be validated in
isolation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Set

from game.utils.data_loader import load_collection, load_json


def _by_id(entries: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Index a list of ``{"id": ...}`` entries by their id (last write wins)."""
    return {entry["id"]: entry for entry in entries}


@dataclass(frozen=True)
class GameDataRegistry:
    """Immutable snapshot of every static content collection."""

    items: List[Dict[str, Any]]
    skills: List[Dict[str, Any]]
    enemies: List[Dict[str, Any]]  # random exploration pool
    character_enemies: List[Dict[str, Any]]  # named duel/boss foes (kept out of the random pool)
    characters: List[Dict[str, Any]]  # NPC roster
    locations: List[Dict[str, Any]]
    quests: List[Dict[str, Any]]
    events: Dict[str, Any]
    body_realms: Dict[str, Any]
    essence_realms: Dict[str, Any]
    cultivation_config: Dict[str, Any]
    morality: Dict[str, Any]
    relationships: Dict[str, Any]
    encounter_pools: Dict[str, Any] = field(default_factory=dict)
    shops: List[Dict[str, Any]] = field(default_factory=list)
    martial_talents: List[Dict[str, Any]] = field(default_factory=list)
    body_talents: List[Dict[str, Any]] = field(default_factory=list)
    equipment: List[Dict[str, Any]] = field(default_factory=list)
    talents: Dict[str, Any] = field(default_factory=dict)
    technique_manuals: List[Dict[str, Any]] = field(default_factory=list)
    trainers: List[Dict[str, Any]] = field(default_factory=list)
    sects: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def load(cls) -> "GameDataRegistry":
        """Load every content collection from the ``data/`` directory."""
        return cls(
            items=load_collection("items"),
            skills=load_collection("skills"),
            enemies=load_collection("enemies"),
            character_enemies=load_collection("character_enemies"),
            characters=load_collection("characters"),
            locations=load_collection("locations"),
            quests=load_collection("quests"),
            events=load_json("events.json"),
            body_realms=load_json("cultivation/body_transformation_realms.json"),
            essence_realms=load_json("cultivation/essence_gathering_realms.json"),
            cultivation_config=load_json("cultivation/cultivation_config.json"),
            morality=load_json("morality.json"),
            relationships=load_json("relationships.json"),
            encounter_pools=_load_optional_object("encounter_pools.json"),
            shops=load_collection("shops"),
            martial_talents=load_json("cultivation/martial_talents.json"),
            body_talents=load_json("cultivation/body_talents.json"),
            equipment=load_json("equipment.json"),
            talents=load_json("cultivation/talents.json"),
            technique_manuals=_load_optional_collection("technique_manuals"),
            trainers=_load_optional_collection("trainers"),
            sects=_load_optional_collection("sects"),
        )

    # -- id-indexed views (built on demand) ------------------------------
    def items_by_id(self) -> Dict[str, Dict[str, Any]]:
        return _by_id(self.items)

    def skills_by_id(self) -> Dict[str, Dict[str, Any]]:
        return _by_id(self.skills)

    def enemies_by_id(self) -> Dict[str, Dict[str, Any]]:
        return _by_id(self.enemies)

    def character_enemies_by_id(self) -> Dict[str, Dict[str, Any]]:
        return _by_id(self.character_enemies)

    def characters_by_id(self) -> Dict[str, Dict[str, Any]]:
        return _by_id(self.characters)

    def locations_by_id(self) -> Dict[str, Dict[str, Any]]:
        return _by_id(self.locations)

    def shops_by_id(self) -> Dict[str, Dict[str, Any]]:
        return _by_id(self.shops)

    def martial_talents_by_id(self) -> Dict[str, Dict[str, Any]]:
        return _by_id(self.martial_talents)

    def body_talents_by_id(self) -> Dict[str, Dict[str, Any]]:
        return _by_id(self.body_talents)

    def equipment_by_id(self) -> Dict[str, Dict[str, Any]]:
        return _by_id(self.equipment)

    def technique_manuals_by_id(self) -> Dict[str, Dict[str, Any]]:
        return _by_id(self.technique_manuals)

    def manual_item_ids(self) -> Set[str]:
        """Return the ids of every auto-generated technique-manual item.

        One manual is synthesised per skill (id ``"<skill_id>_manual"`` unless a
        ``technique_manuals.json`` override supplies a custom id). These ids are
        valid item references in shops/loot/pools even though they are not part
        of ``items.json`` -- the engine builds them at runtime from the skills
        and manual-override collections.
        """
        overrides = {entry["skill_id"]: entry for entry in self.technique_manuals if entry.get("skill_id")}
        ids: Set[str] = set()
        for skill in self.skills:
            skill_id = skill.get("id")
            if not skill_id:
                continue
            override = overrides.get(skill_id, {})
            ids.add(str(override.get("id", f"{skill_id}_manual")))
        return ids

    def trainers_by_id(self) -> Dict[str, Dict[str, Any]]:
        return _by_id(self.trainers)

    def sects_by_id(self) -> Dict[str, Dict[str, Any]]:
        return _by_id(self.sects)

    def talents_by_id(self) -> Dict[str, Dict[str, Any]]:
        return {entry["id"]: entry for entry in self.talents.get("tiers", []) if "id" in entry}

    def talents_by_tier(self) -> Dict[int, Dict[str, Any]]:
        return {int(entry["tier"]): entry for entry in self.talents.get("tiers", []) if "tier" in entry}


def _load_optional_object(filename: str) -> Dict[str, Any]:
    """Load a JSON object file, returning ``{}`` when it does not exist yet."""
    try:
        data = load_json(filename)
    except FileNotFoundError:
        return {}
    return data if isinstance(data, dict) else {}


def _load_optional_collection(name: str) -> List[Dict[str, Any]]:
    """Load a list collection, returning ``[]`` when the file/folder is absent."""
    try:
        return load_collection(name)
    except FileNotFoundError:
        return []
