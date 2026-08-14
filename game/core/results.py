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
from typing import Any, ClassVar, Dict, List, Optional

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
    choices: Optional[List[Dict[str, Any]]] = None
    speech_notes: Optional[str] = None


@dataclass(frozen=True)
class DialogueChoiceResult(Result):
    """Outcome of choosing a dialogue option: the social deltas applied."""

    EVENT: ClassVar[str] = EventType.DIALOGUE_CHOICE
    character_id: str
    choice_id: str
    name: str
    player_message: str
    morality: Dict[str, Any]
    reputation: int
    reputation_delta: int
    relationship: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class TravelResult(Result):
    """A successful move, carrying the destination's UI-safe view."""

    EVENT: ClassVar[str] = EventType.TRAVEL_RESULT
    location: Dict[str, Any]


@dataclass(frozen=True)
class MapResult(Result):
    """Text-map view: the current location's map position and reachable exits."""

    EVENT: ClassVar[str] = EventType.MAP
    location_name: str
    map_position: Dict[str, Any]
    destinations: List[Dict[str, Any]]


@dataclass(frozen=True)
class BoonResult(Result):
    """Outcome of receiving a relationship-gated reward from an NPC."""

    EVENT: ClassVar[str] = EventType.BOON
    character_id: str
    name: str
    player_message: str
    reward: Dict[str, Any]
    wallet: Optional[Dict[str, int]] = None


@dataclass(frozen=True)
class TechniquesResult(Result):
    """The player's known techniques (active + passive)."""

    EVENT: ClassVar[str] = EventType.TECHNIQUES
    skills: List[Dict[str, Any]]


@dataclass(frozen=True)
class TalentsResult(Result):
    """The player's current Martial/Body talents and their upgrade paths."""

    EVENT: ClassVar[str] = EventType.TALENTS
    martial_talent: Dict[str, Any]
    body_talent: Dict[str, Any]
    martial_upgrades: List[Dict[str, Any]]
    body_upgrades: List[Dict[str, Any]]


@dataclass(frozen=True)
class TalentUpgradedResult(Result):
    """Outcome of upgrading a Martial or Body talent."""

    EVENT: ClassVar[str] = EventType.TALENT_UPGRADED
    track: str
    talent_id: str
    display_name: str
    player_message: str
    wallet: Optional[Dict[str, int]] = None


@dataclass(frozen=True)
class ClosedDoorResult(Result):
    """Outcome of a deliberate multi-year closed-door cultivation session."""

    EVENT: ClassVar[str] = EventType.CLOSED_DOOR_RESULT
    years: float
    progress_gained: float
    progress: float
    player_message: str
    lifespan: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class RepairResult(Result):
    """Outcome of repairing a piece of worn equipment."""

    EVENT: ClassVar[str] = EventType.REPAIR_RESULT
    item_id: str
    durability: int
    player_message: str
    wallet: Optional[Dict[str, int]] = None


@dataclass(frozen=True)
class SaveExportedResult(Result):
    """A portable JSON snapshot of the current session."""

    EVENT: ClassVar[str] = EventType.SAVE_EXPORTED
    payload: str
    player_message: str


@dataclass(frozen=True)
class SaveImportedResult(Result):
    """Outcome of importing a portable JSON snapshot."""

    EVENT: ClassVar[str] = EventType.SAVE_IMPORTED
    success: bool
    player_message: str
    slot: Optional[str] = None
