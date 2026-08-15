"""Item model.

Items are data-driven (see ``data/items.json``). The model holds the definition;
the inventory system interprets ``effect``/``magnitude`` when an item is used.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Item:
    """A carryable object.

    Attributes:
        id: Stable identifier used in data files and inventories.
        name: Human-readable name (content, displayed by the UI).
        type: ``"consumable"``, ``"material"``, or ``"equipment"``.
        effect: Effect identifier the inventory system interprets.
        magnitude: Numeric strength of the effect.
        description: Flavour/help text (content, displayed by the UI).
        consumed_on_use: Whether using the item removes one from the stack.
        value: Sell/worth value in gold (equipment carries it; 0 = derive).
    """

    id: str
    name: str
    type: str
    effect: str
    magnitude: int
    description: str = ""
    consumed_on_use: bool = False
    category: str = ""
    rarity: str = ""
    valid_slots: List[str] = field(default_factory=list)
    skill_id: str = ""
    value: int = 0
    # Equipment-only modifier groups (see ``data/equipment.json``). Empty for
    # consumables/materials; surfaced to the UI so item stats can be displayed.
    stat_modifiers: Dict[str, Any] = field(default_factory=dict)
    cultivation_modifiers: Dict[str, Any] = field(default_factory=dict)
    utility_modifiers: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Item":
        """Build an item from a raw data-file entry."""
        item_type = data.get("type", "material")
        return cls(
            id=data["id"],
            name=data.get("name", data.get("display_name", data["id"])),
            type=item_type,
            effect=data.get("effect", "none"),
            magnitude=int(data.get("magnitude", 0)),
            description=data.get("description", ""),
            consumed_on_use=bool(data.get("consumed_on_use", item_type == "consumable")),
            category=str(data.get("category", "")),
            rarity=str(data.get("rarity", "")),
            valid_slots=[str(slot) for slot in data.get("valid_slots", [])],
            skill_id=str(data.get("skill_id", "")),
            value=int(data.get("value", 0)),
            stat_modifiers=dict(data.get("stat_modifiers", {})),
            cultivation_modifiers=dict(data.get("cultivation_modifiers", {})),
            utility_modifiers=dict(data.get("utility_modifiers", {})),
        )

    def is_consumable(self) -> bool:
        """Return ``True`` if using the item should consume one from the stack."""
        return self.consumed_on_use
