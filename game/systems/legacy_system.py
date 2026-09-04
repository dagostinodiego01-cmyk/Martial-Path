"""Legacy system (ROADMAP C.5 + C.6).

Two pure responsibilities, both rule-only (no I/O, no meta-save access):

**Unlock tree (C.5)** -- cross-run purchases from ``data/legacy_tree.json``.
Every node belongs to a tier; a tier opens once the player has bought the
required number of unlocks from earlier tiers (``required_meta_tier`` = the
number of prior tiers that must have at least one purchase). Each node carries
a stable ``kind``:

* ``sect``     -- the sect joins free (its reputation/realm gates stay).
* ``technique``-- the skill is known from character creation.
* ``title``    -- a cosmetic title shown in views and the run summary.

**World seed (C.6)** -- the same seed derives a *seed report*: which sects
dominate (boosted join pools), the economy price band, and the encounter-pool
order. Deterministic: two runs with the same seed produce the identical world;
different seeds produce (measurably) different ones.

Spending Ancestral Memory and persisting unlocks is the engine/meta-save's job
(the system never touches the meta-save), exactly like ``OriginSystem``.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

#: Unlocks are counted from the earliest tiers upward.
KINDS = ("sect", "technique", "title")


class LegacySystem:
    """Resolves the cross-run unlock tree and the world-seed report."""

    def __init__(self, tree: Optional[Dict[str, Any]] = None) -> None:
        self._tiers: List[Dict[str, Any]] = [
            dict(tier) for tier in (tree or {}).get("tiers", []) if tier.get("id")
        ]

    # -- unlock tree (C.5) -------------------------------------------------
    def tiers(self) -> List[Dict[str, Any]]:
        """Return every tier definition (in data order)."""
        return [dict(tier) for tier in self._tiers]

    def node(self, unlock_id: str) -> Optional[Dict[str, Any]]:
        """Return one unlock node by id (with its ``tier_id``), or ``None``."""
        for tier in self._tiers:
            for node in tier.get("unlocks", []):
                if node.get("id") == unlock_id:
                    entry = dict(node)
                    entry["tier_id"] = tier["id"]
                    return entry
        return None

    def all_nodes(self) -> List[Dict[str, Any]]:
        """Return every unlock node across all tiers (with ``tier_id``)."""
        nodes: List[Dict[str, Any]] = []
        for tier in self._tiers:
            for node in tier.get("unlocks", []):
                entry = dict(node)
                entry["tier_id"] = tier["id"]
                nodes.append(entry)
        return nodes

    def tier_state(self, purchased: Iterable[str]) -> List[Dict[str, Any]]:
        """Annotate the tree with per-tier/per-node purchase state.

        ``purchased`` is the list of unlock ids already bought (persisted in the
        meta-save). A tier is ``unlocked`` when the number of *earlier* tiers
        holding at least one purchase reaches ``required_meta_tier``; a locked
        tier's nodes render as not yet purchasable.
        """
        bought = {str(entry) for entry in purchased}
        states: List[Dict[str, Any]] = []
        earlier_tiers_with_purchases = 0
        for tier in self._tiers:
            required = int(tier.get("required_meta_tier", 0))
            unlocked = earlier_tiers_with_purchases >= required
            nodes: List[Dict[str, Any]] = []
            for node in tier.get("unlocks", []):
                entry = dict(node)
                entry["purchased"] = entry["id"] in bought
                entry["available"] = unlocked and not entry["purchased"]
                nodes.append(entry)
            states.append(
                {
                    "id": tier["id"],
                    "display_name": tier.get("display_name", tier["id"]),
                    "required_meta_tier": required,
                    "unlocked": unlocked,
                    "unlocks": nodes,
                }
            )
            if any(entry["purchased"] for entry in nodes):
                earlier_tiers_with_purchases += 1
        return states

    def can_unlock(self, unlock_id: str, purchased: Iterable[str]) -> Dict[str, Any]:
        """Resolve whether ``unlock_id`` can be bought right now.

        Returns ``{"ok": bool, "reason": str|None}`` with stable reasons:
        ``UNKNOWN_UNLOCK``, ``ALREADY_OWNED``, ``TIER_LOCKED``.
        """
        node = self.node(unlock_id)
        if node is None:
            return {"ok": False, "reason": "UNKNOWN_UNLOCK"}
        bought = {str(entry) for entry in purchased}
        if node["id"] in bought:
            return {"ok": False, "reason": "ALREADY_OWNED"}
        if self._tier_locked(node["tier_id"], bought):
            return {"ok": False, "reason": "TIER_LOCKED"}
        return {"ok": True, "reason": None}

    def _tier_locked(self, tier_id: str, bought: set[str]) -> bool:
        """True when too few earlier tiers hold purchases for this tier."""
        earlier_with_purchases = 0
        for tier in self._tiers:
            if tier["id"] == tier_id:
                break
            if any(entry["id"] in bought for entry in tier.get("unlocks", [])):
                earlier_with_purchases += 1
        tier = next((t for t in self._tiers if t["id"] == tier_id), None)
        required = int(tier.get("required_meta_tier", 0)) if tier else 0
        return earlier_with_purchases < required

    # -- world seed (C.6) --------------------------------------------------
    def world_seed_report(self, seed: int, rng: Any, sect_ids: Iterable[str]) -> Dict[str, Any]:
        """Derive the run's world variation from the seed.

        Pure derivation over a pre-seeded RNG (the engine owns the RNG). Produces:

        * ``dominant_sects`` -- two sect ids whose presence is boosted;
        * ``economy_band``  -- one of ``cheap``/``fair``/``pricey`` scaling shop
          prices (multipliers 0.9 / 1.0 / 1.15);
        * ``encounter_order`` -- a seeded shuffle key (exact order is resolved by
          the event system's own weighted draws, so this is a bias hint).
        """
        sects = [str(entry) for entry in sect_ids]
        dominant: List[str] = []
        remaining = list(sects)
        for _ in range(min(2, len(remaining))):
            pick = rng.choice(remaining)
            dominant.append(pick)
            remaining.remove(pick)
        band = rng.choice(("cheap", "fair", "pricey"))
        return {
            "seed": int(seed),
            "dominant_sects": dominant,
            "economy_band": band,
            "economy_multiplier": {"cheap": 0.9, "fair": 1.0, "pricey": 1.15}[band],
        }
