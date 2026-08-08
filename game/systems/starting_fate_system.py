"""Starting talent rolls for the Martial and Body cultivation tracks.

The system is data-driven and pure: it receives the two talent tables and a
seeded RNG, rolls only entries with positive ``roll_weight``, and returns UI-safe
talent views. It does not own player state or decide when a talent is accepted.
Talent replaces the earlier Spiritual Root / Physique traits: the Martial Talent
governs Essence cultivation and the Body Talent governs Body cultivation.
"""
from __future__ import annotations

from typing import Any, Dict, List

from game.utils.rng import RNG


class StartingFateSystem:
    """Roll and view Martial Talent / Body Talent starting data."""

    DEFAULT_MARTIAL_TALENT_ID = "earth_grade"
    DEFAULT_BODY_TALENT_ID = "iron_skin_grade"

    def __init__(self, martial_talents: List[Dict[str, Any]], body_talents: List[Dict[str, Any]], rng: RNG) -> None:
        self._martial_talents = list(martial_talents)
        self._body_talents = list(body_talents)
        self._rng = rng
        self._martial_by_id = {entry["id"]: entry for entry in self._martial_talents if "id" in entry}
        self._body_by_id = {entry["id"]: entry for entry in self._body_talents if "id" in entry}

    def roll(self) -> Dict[str, Any]:
        """Roll one Martial Talent and one Body Talent from positive weights."""
        martial = self._roll_weighted(self._martial_talents)
        body = self._roll_weighted(self._body_talents)
        return {
            "martial_talent_id": martial["id"],
            "body_talent_id": body["id"],
            "martial_talent": self.martial_talent_view(martial["id"]),
            "body_talent": self.body_talent_view(body["id"]),
        }

    def martial_talent_view(self, talent_id: str) -> Dict[str, Any]:
        """Return a UI-safe Martial Talent data view by stable ID."""
        return self._trait_view(
            self._martial_by_id.get(talent_id)
            or self._martial_by_id.get(self.DEFAULT_MARTIAL_TALENT_ID)
            or {}
        )

    def body_talent_view(self, talent_id: str) -> Dict[str, Any]:
        """Return a UI-safe Body Talent data view by stable ID."""
        return self._trait_view(
            self._body_by_id.get(talent_id)
            or self._body_by_id.get(self.DEFAULT_BODY_TALENT_ID)
            or {}
        )

    def martial_talent_data(self, talent_id: str) -> Dict[str, Any]:
        return dict(self._martial_by_id.get(talent_id) or self._martial_by_id.get(self.DEFAULT_MARTIAL_TALENT_ID) or {})

    def body_talent_data(self, talent_id: str) -> Dict[str, Any]:
        return dict(self._body_by_id.get(talent_id) or self._body_by_id.get(self.DEFAULT_BODY_TALENT_ID) or {})

    def _roll_weighted(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        rollable = [entry for entry in entries if float(entry.get("roll_weight", 0)) > 0]
        if not rollable:
            raise ValueError("Starting talent data must contain at least one rollable entry.")
        weights = [float(entry["roll_weight"]) for entry in rollable]
        return self._rng.weighted_choice(rollable, weights)

    def _trait_view(self, trait: Dict[str, Any]) -> Dict[str, Any]:
        hidden = {"upgrade_options", "roll_weight"}
        return {key: value for key, value in trait.items() if key not in hidden}