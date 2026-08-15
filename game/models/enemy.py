"""Enemy model.

Enemy templates are data-driven (see ``data/enemies.json``). Each encounter
spawns a fresh instance so combat can mutate its HP without affecting the
template.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Enemy:
    """A hostile combatant."""

    id: str
    name: str
    body_realm_id: str
    essence_realm_id: str | None
    hp: int
    max_hp: int
    attack: int
    defense: int
    exp_reward: int = 0
    loot_table: List[Dict[str, Any]] = field(default_factory=list)
    # Optional data-driven abilities the enemy uses in place of (or in addition
    # to) its basic attack. Each entry: {"type": heavy|poison|stun, "chance":
    # 0..1, "magnitude": number}.
    abilities: List[Dict[str, Any]] = field(default_factory=list)
    # The enemy's Dao (see ``data/daos.json``). ``None`` means the foe carries no
    # Dao (wild beasts, mooks), so it neither counters nor is countered by the
    # player's Dao. Named foes may declare a specific Dao.
    dao_id: str | None = None
    # Transient combat state (never persisted): a damage-absorption shield and
    # timed status effects applied by the player (stun, dot, debuffs).
    shield: int = 0
    statuses: Dict[str, Dict[str, float]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Enemy":
        """Spawn a fresh enemy instance from a template entry."""
        hp = int(data["hp"])
        return cls(
            id=data["id"],
            name=data["name"],
            body_realm_id=str(data.get("body_realm_id", "mortal")),
            essence_realm_id=str(data["essence_realm_id"]) if data.get("essence_realm_id") else None,
            hp=hp,
            max_hp=hp,
            attack=int(data["attack"]),
            defense=int(data.get("defense", 0)),
            exp_reward=int(data.get("exp_reward", 0)),
            loot_table=list(data.get("loot_table", [])),
            abilities=[dict(ability) for ability in data.get("abilities", []) if isinstance(ability, dict)],
            dao_id=str(data["dao_id"]) if data.get("dao_id") else None,
        )

    def is_alive(self) -> bool:
        """Return ``True`` while the enemy still has HP."""
        return self.hp > 0

    def take_damage(self, amount: int) -> int:
        """Apply ``amount`` damage (clamped at 0 HP) and return damage dealt."""
        dealt = max(0, amount)
        self.hp = max(0, self.hp - dealt)
        return dealt

    def public_view(self) -> Dict[str, Any]:
        """Return a UI-safe snapshot of the enemy's visible stats."""
        return {
            "name": self.name,
            "body_realm_id": self.body_realm_id,
            "essence_realm_id": self.essence_realm_id,
            "dao_id": self.dao_id,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "attack": self.attack,
            "defense": self.defense,
        }
