"""Rarity-weighted exploration finds.

Chooses what the player stumbles upon while exploring an area that has no curated
loot pool. Candidates are drawn from the whole findable catalog (items and
equipment), weighted by rarity so common goods appear far more often than rare
ones, and gated by an area's danger so early zones never surface top-grade gear.

Pure content selection: it holds the catalog + tuning, and returns an item id (or
``None``). It never mutates the player or formats text.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from game.utils.rng import RNG


class FindSystem:
    """Weighted, danger-gated selection over the findable item/equipment catalog."""

    def __init__(self, catalog: List[Dict[str, str]], config: Dict[str, Any], rng: RNG) -> None:
        self._config = config or {}
        self._rng = rng
        self._rarity_order: List[str] = list(self._config.get("rarity_order", []))
        self._rarity_weights: Dict[str, float] = dict(self._config.get("rarity_weights", {}))
        self._default_rarity = str(self._config.get("default_item_rarity", "mortal_grade"))
        # Precompute each candidate's rarity index once so rolls stay cheap.
        self._candidates: List[Dict[str, Any]] = []
        for entry in catalog:
            rarity = entry.get("rarity") or self._default_rarity
            self._candidates.append(
                {
                    "item_id": entry["item_id"],
                    "rarity": rarity,
                    "rarity_index": self._rarity_index(rarity),
                    "weight": float(self._rarity_weights.get(rarity, 1.0)),
                }
            )

    def max_rarity_index_for_danger(self, danger_level: Any) -> int:
        """Return the highest findable rarity index for an area's danger level."""
        mapping = self._config.get("danger_max_rarity_index", {})
        try:
            danger_key = str(int(danger_level))
        except (TypeError, ValueError):
            danger_key = "0"
        if danger_key in mapping:
            return int(mapping[danger_key])
        # Unmapped danger: allow everything up to the top of the ladder.
        return max(0, len(self._rarity_order) - 1)

    def roll_find(self, max_rarity_index: int) -> Optional[str]:
        """Return a weighted-random findable item id at or below ``max_rarity_index``."""
        eligible = [candidate for candidate in self._candidates if candidate["rarity_index"] <= max_rarity_index]
        if not eligible:
            return None
        chosen = self._rng.weighted_choice(
            [candidate["item_id"] for candidate in eligible],
            [candidate["weight"] for candidate in eligible],
        )
        return str(chosen)

    def _rarity_index(self, rarity: str) -> int:
        if rarity in self._rarity_order:
            return self._rarity_order.index(rarity)
        # Unknown rarity: treat as the most common tier so it stays broadly findable.
        return 0
