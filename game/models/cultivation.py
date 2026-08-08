"""Pure cultivation state models.

These dataclasses hold persistent cultivation state only. They do not load data,
format UI, roll odds, or apply progression rules; those responsibilities live in
the cultivation system/service layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class BodyCultivationState:
    """Persistent state for the Body Transformation path."""

    realm_id: str = "mortal"
    progress: float = 0.0
    foundation: float = 10.0
    opened_gates: List[str] = field(default_factory=list)
    opened_stars: List[str] = field(default_factory=list)
    marrow_percent: float = 0.0
    body_strength: float = 1.0
    breakthrough_failures: int = 0
    cultivation_strain: float = 0.0
    foundation_stability: float = 100.0
    daily_cultivation_count: int = 0
    last_cultivation_day: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "realm_id": self.realm_id,
            "progress": round(self.progress, 1),
            "foundation": round(self.foundation, 1),
            "opened_gates": list(self.opened_gates),
            "opened_stars": list(self.opened_stars),
            "marrow_percent": round(self.marrow_percent, 1),
            "body_strength": round(self.body_strength, 1),
            "breakthrough_failures": self.breakthrough_failures,
            "cultivation_strain": round(self.cultivation_strain, 1),
            "foundation_stability": round(self.foundation_stability, 1),
            "daily_cultivation_count": self.daily_cultivation_count,
            "last_cultivation_day": self.last_cultivation_day,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BodyCultivationState":
        return cls(
            realm_id=str(data.get("realm_id", "mortal")),
            progress=float(data.get("progress", 0.0)),
            foundation=float(data.get("foundation", 10.0)),
            opened_gates=list(data.get("opened_gates", [])),
            opened_stars=list(data.get("opened_stars", [])),
            marrow_percent=float(data.get("marrow_percent", 0.0)),
            body_strength=float(data.get("body_strength", 1.0)),
            breakthrough_failures=int(data.get("breakthrough_failures", 0)),
            cultivation_strain=float(data.get("cultivation_strain", 0.0)),
            foundation_stability=float(data.get("foundation_stability", 100.0)),
            daily_cultivation_count=int(data.get("daily_cultivation_count", 0)),
            last_cultivation_day=int(data.get("last_cultivation_day", 1)),
        )


@dataclass
class EssenceCultivationState:
    """Persistent state for the Essence Gathering path."""

    realm_id: str = "houtian"
    substage: str = "Early"
    progress: float = 0.0
    foundation: float = 10.0
    dantian_capacity: float = 10.0
    true_essence_density: float = 1.0
    circulation_stability: float = 1.0
    life_destruction_fall: int = 0
    inner_world_development: float = 0.0
    breakthrough_failures: int = 0
    cultivation_strain: float = 0.0
    foundation_stability: float = 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "realm_id": self.realm_id,
            "substage": self.substage,
            "progress": round(self.progress, 1),
            "foundation": round(self.foundation, 1),
            "dantian_capacity": round(self.dantian_capacity, 1),
            "true_essence_density": round(self.true_essence_density, 1),
            "circulation_stability": round(self.circulation_stability, 1),
            "life_destruction_fall": self.life_destruction_fall,
            "inner_world_development": round(self.inner_world_development, 1),
            "breakthrough_failures": self.breakthrough_failures,
            "cultivation_strain": round(self.cultivation_strain, 1),
            "foundation_stability": round(self.foundation_stability, 1),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EssenceCultivationState":
        return cls(
            realm_id=str(data.get("realm_id", "houtian")),
            substage=str(data.get("substage", "Early")),
            progress=float(data.get("progress", 0.0)),
            foundation=float(data.get("foundation", 10.0)),
            dantian_capacity=float(data.get("dantian_capacity", 10.0)),
            true_essence_density=float(data.get("true_essence_density", 1.0)),
            circulation_stability=float(data.get("circulation_stability", 1.0)),
            life_destruction_fall=int(data.get("life_destruction_fall", 0)),
            inner_world_development=float(data.get("inner_world_development", 0.0)),
            breakthrough_failures=int(data.get("breakthrough_failures", 0)),
            cultivation_strain=float(data.get("cultivation_strain", 0.0)),
            foundation_stability=float(data.get("foundation_stability", 100.0)),
        )


@dataclass
class CultivationState:
    """Combined cultivation state for a character."""

    body: BodyCultivationState = field(default_factory=BodyCultivationState)
    essence: EssenceCultivationState = field(default_factory=EssenceCultivationState)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "body_transformation": self.body.to_dict(),
            "essence_gathering": self.essence.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CultivationState":
        return cls(
            body=BodyCultivationState.from_dict(data.get("body_transformation", {})),
            essence=EssenceCultivationState.from_dict(data.get("essence_gathering", {})),
        )


@dataclass
class BreakthroughResult:
    """Structured result for a cultivation breakthrough attempt."""

    success: bool
    track_id: str
    previous_realm_id: str
    new_realm_id: str
    previous_substage: str = ""
    new_substage: str = ""
    message_code: str = ""
    player_message: str = ""
    stat_changes: Dict[str, int] = field(default_factory=dict)
    consumed_resources: List[str] = field(default_factory=list)
    backlash: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "track_id": self.track_id,
            "previous_realm_id": self.previous_realm_id,
            "new_realm_id": self.new_realm_id,
            "previous_substage": self.previous_substage,
            "new_substage": self.new_substage,
            "message_code": self.message_code,
            "player_message": self.player_message,
            "stat_changes": dict(self.stat_changes),
            "consumed_resources": list(self.consumed_resources),
            "backlash": dict(self.backlash),
        }