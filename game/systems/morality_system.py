"""Morality system.

Interprets a player's morality score into a named band (``demonic`` / ``neutral``
/ ``righteous``, matching the ``morality_reaction`` keys in ``characters.json``)
and applies clamped morality changes. Fully data-driven from ``data/morality.json``.

Pure logic: it takes a numeric score and returns structured results. It never
mutates a player directly and never formats UI text.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from game.utils.data_loader import load_json


class MoralitySystem:
    """Reads morality bands from data and interprets/adjusts a morality score."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self._config = config or load_json("morality.json")
        self._min = int(self._config.get("min", -100))
        self._max = int(self._config.get("max", 100))
        self._bands: List[Dict[str, Any]] = list(self._config.get("bands", []))

    def clamp(self, score: int) -> int:
        """Clamp a score into the configured morality range."""
        return max(self._min, min(self._max, int(score)))

    def band(self, score: int) -> Dict[str, Any]:
        """Return the band definition a score falls into."""
        value = self.clamp(score)
        for band in self._bands:
            if int(band["min"]) <= value <= int(band["max"]):
                return band
        return {"id": "neutral", "label": "Neutral", "description": ""}

    def band_id(self, score: int) -> str:
        """Return just the band id for a score."""
        return str(self.band(score).get("id", "neutral"))

    def describe(self, score: int) -> Dict[str, Any]:
        """Return a structured description of the score's current band."""
        band = self.band(score)
        return {
            "morality": self.clamp(score),
            "band": band.get("id"),
            "label": band.get("label"),
            "description": band.get("description", ""),
        }

    def adjust(self, current: int, delta: int) -> Dict[str, Any]:
        """Apply a clamped delta to a morality score and report the new band."""
        before = self.clamp(current)
        after = self.clamp(before + int(delta))
        band = self.band(after)
        return {
            "morality": after,
            "changed": after - before,
            "band": band.get("id"),
            "label": band.get("label"),
            "description": band.get("description", ""),
        }
