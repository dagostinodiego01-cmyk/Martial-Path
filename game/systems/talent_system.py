"""Talent tier ladder lookups.

The talent ladder is a data-driven, two-track potential ceiling: every tier index
maps to a Martial talent name, a Body-cultivation talent name, a reachable
cultivation realm, and a maximum lifespan. Both tracks share one tier index, so a
single tier value resolves to the correct entry on whichever path a character
follows.

This system is pure and read-only. It resolves ladder entries into UI-safe views
by tier index or stable ID; it owns no player state and applies no progression
rules. A ``max_lifespan_years`` of ``None`` means the tier's lifespan is
effectively immortal/eternal, so callers should render ``lifespan_display`` for
player-facing text.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class TalentSystem:
    """Resolve entries from the two-track talent tier ladder."""

    def __init__(self, tiers: List[Dict[str, Any]]) -> None:
        self._tiers = list(tiers)
        self._by_id = {entry["id"]: entry for entry in self._tiers if "id" in entry}
        self._by_tier = {int(entry["tier"]): entry for entry in self._tiers if "tier" in entry}

    def all_tiers(self) -> List[Dict[str, Any]]:
        """Return UI-safe views for every ladder entry, ordered by tier index."""
        ordered = sorted(self._tiers, key=lambda entry: int(entry.get("tier", 0)))
        return [dict(entry) for entry in ordered]

    def tier_view(self, tier: int) -> Optional[Dict[str, Any]]:
        """Return the UI-safe view for a tier index, or ``None`` when unknown."""
        entry = self._by_tier.get(int(tier))
        return dict(entry) if entry is not None else None

    def view_by_id(self, talent_id: str) -> Optional[Dict[str, Any]]:
        """Return the UI-safe view for a stable ladder ID, or ``None`` when unknown."""
        entry = self._by_id.get(talent_id)
        return dict(entry) if entry is not None else None
