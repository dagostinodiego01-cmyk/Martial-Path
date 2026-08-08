"""Typed engine result models.

The engine and services compute results as small, frozen dataclasses and
serialise them to plain dicts at the boundary via :meth:`Result.to_dict`. The
external contract stays "a dict tagged with an ``EventType``", so UIs and the API
are unaffected -- but internal construction gains autocomplete and guards against
silent key typos.

Each result declares its ``EVENT`` as a class variable; :meth:`Result.to_dict`
emits ``{"event": EVENT, ...}`` and omits any field left as ``None``. Only the
result shapes actually produced today live here; add a dataclass when a system
adopts typed results for a new outcome.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, ClassVar, Dict, Optional

from game.core.constants import EventType


@dataclass(frozen=True)
class Result:
    """Base for typed engine results."""

    EVENT: ClassVar[str] = EventType.MESSAGE

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to the plain ``{"event": ..., ...}`` dict UIs consume."""
        data: Dict[str, Any] = {"event": self.EVENT}
        for field_def in fields(self):
            value = getattr(self, field_def.name)
            if value is not None:
                data[field_def.name] = value
        return data


@dataclass(frozen=True)
class MessageResult(Result):
    """A plain informational message."""

    EVENT: ClassVar[str] = EventType.MESSAGE
    text: str


@dataclass(frozen=True)
class ErrorResult(Result):
    """A rejected command, tagged with a stable ``reason`` code."""

    EVENT: ClassVar[str] = EventType.ERROR
    reason: str
    location_id: Optional[str] = None
    input: Optional[str] = None


@dataclass(frozen=True)
class HelpResult(Result):
    """Signals the UI to render its command reference."""

    EVENT: ClassVar[str] = EventType.HELP


@dataclass(frozen=True)
class QuitResult(Result):
    """Signals that the session should end."""

    EVENT: ClassVar[str] = EventType.QUIT


@dataclass(frozen=True)
class RestResult(Result):
    """Outcome of resting: HP/Qi recovered and the new totals."""

    EVENT: ClassVar[str] = EventType.REST_RESULT
    healed: int
    qi_restored: int
    hp: int
    qi: int


@dataclass(frozen=True)
class MeditateResult(Result):
    """Outcome of meditating: Qi recovered and any comprehension gained."""

    EVENT: ClassVar[str] = EventType.MEDITATE_RESULT
    qi_restored: int
    qi: int
    comprehension_gain: int
    comprehension: int


@dataclass(frozen=True)
class StabiliseResult(Result):
    """Outcome of stabilising the body cultivation foundation."""

    EVENT: ClassVar[str] = EventType.STABILISE_RESULT
    strain_reduced: float
    foundation_gained: float
    current_strain: float
    foundation_stability: float
    comprehension_gain: int
    comprehension: int
    progress_gained: float
    progress: float
    required_progress: float
    player_message: str


@dataclass(frozen=True)
class StartingFateRolledResult(Result):
    """Outcome of rolling pending Spiritual Root and Physique fate."""

    EVENT: ClassVar[str] = EventType.STARTING_FATE_ROLLED
    spiritual_root_id: str
    physique_id: str
    spiritual_root: Dict[str, Any]
    physique: Dict[str, Any]
    requires_fate_acceptance: bool
    player_message: str


@dataclass(frozen=True)
class StartingFateAcceptedResult(Result):
    """Outcome of accepting a rolled starting fate."""

    EVENT: ClassVar[str] = EventType.STARTING_FATE_ACCEPTED
    success: bool
    spiritual_root_id: str
    physique_id: str
    spiritual_root: Dict[str, Any]
    physique: Dict[str, Any]
    player_message: str


@dataclass(frozen=True)
class PlayerDiedResult(Result):
    """Permanent game over when the player's lifespan is exhausted."""

    EVENT: ClassVar[str] = EventType.PLAYER_DIED
    cause: str
    age_years: float
    player_message: str
    last_event: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class CharacterEncounterResult(Result):
    """Outcome of encountering named characters at the current location."""

    EVENT: ClassVar[str] = EventType.CHARACTER_ENCOUNTER
    characters: list[Dict[str, Any]]
    player_message: str


@dataclass(frozen=True)
class SkillLearnedResult(Result):
    """Outcome of learning a technique (from a manual or a trainer)."""

    EVENT: ClassVar[str] = EventType.SKILL_LEARNED
    skill_id: str
    name: str
    source: str
    player_message: str
    price: Optional[Dict[str, int]] = None
    wallet: Optional[Dict[str, int]] = None


@dataclass(frozen=True)
class CharacterInteractionResult(Result):
    """Outcome of a non-combat character interaction such as talking."""

    EVENT: ClassVar[str] = EventType.CHARACTER_INTERACTION
    interaction: str
    character_id: str
    name: str
    dialogue_context: Dict[str, Any]
    player_message: str


@dataclass(frozen=True)
class TravelResult(Result):
    """A successful move, carrying the destination's UI-safe view."""

    EVENT: ClassVar[str] = EventType.TRAVEL_RESULT
    location: Dict[str, Any]
