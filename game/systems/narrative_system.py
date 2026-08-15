"""Narrative system.

A deterministic, data-driven prose engine. Templates live in
``data/narrative_templates.json`` and are keyed by *verb*; each verb holds a
pool of weighted ``variants``. A variant is a template string with ``{variable}``
slots and an optional ``when`` clause that only selects the variant when its
predicates hold against the current context (e.g. ``realm_rank >= 3`` or
``season == "Winter"``).

Two rendering modes:

* :meth:`render` draws from the injected RNG *in call order*, so action-boundary
  prose (explore, travel, breakthrough, death) is deterministic per run seed
  while still varying from one occurrence to the next.
* :meth:`render_stable` derives a local RNG from a stable hash of
  ``(seed, verb, keys...)``, so read-only descriptions (location, NPC, item,
  technique) are *stable per entity* within a run -- opening the same view twice
  shows the same sentence -- yet still vary across run seeds and across states,
  because ``when`` clauses filter the eligible pool by realm/morality/
  relationship/season.

``{slot}`` substitution is safe: unknown slots are left verbatim rather than
raising, so a typo in content degrades visibly instead of crashing.

Pure logic: it renders strings and mutates nothing except the RNG draw sequence.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Optional

from game.utils.rng import RNG

# The comparison operators a ``when`` predicate may declare.
SUPPORTED_OPS = ("gte", "lte", "gt", "lt", "eq", "ne")

_SLOT_RE = re.compile(r"\{([a-z_][a-z0-9_]*)\}")


class NarrativeSystem:
    """Renders weighted, conditional template variants into prose."""

    def __init__(
        self,
        templates: Optional[Dict[str, Any]],
        rng: RNG,
        seed: Optional[int] = None,
    ) -> None:
        self._templates: Dict[str, Any] = templates or {}
        self._rng = rng
        self._seed = seed

    # -- introspection ---------------------------------------------------
    def verbs(self) -> List[str]:
        """Return every template verb key known to this engine."""
        return list(self._templates)

    def variant_count(self, verb: str) -> int:
        """Return the number of variants declared for ``verb`` (0 if unknown)."""
        entry = self._templates.get(verb)
        if not isinstance(entry, dict):
            return 0
        variants = entry.get("variants")
        return len(variants) if isinstance(variants, list) else 0

    # -- rendering -------------------------------------------------------
    def render(self, verb: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Render one eligible weighted variant of ``verb`` (order-sensitive)."""
        return self._render_with(verb, context or {}, self._rng)

    def render_stable(self, verb: str, context: Optional[Dict[str, Any]] = None, *keys: Any) -> str:
        """Render ``verb`` stably for the given identity ``keys``.

        The variant is drawn from a local RNG seeded by ``(run_seed, verb,
        keys...)``, so repeated calls with the same keys return the same prose
        (within a run) while a different run seed yields a different draw.
        """
        return self._render_with(verb, context or {}, RNG(self._stable_seed(verb, keys)))

    def _render_with(self, verb: str, context: Dict[str, Any], rng: RNG) -> str:
        entry = self._templates.get(verb)
        if not isinstance(entry, dict):
            return ""
        variants = entry.get("variants")
        if not isinstance(variants, list) or not variants:
            return ""

        eligible = [v for v in variants if isinstance(v, dict) and self._conditions_hold(v.get("when"), context)]
        pool = eligible or [v for v in variants if isinstance(v, dict) and not v.get("when")]
        if not pool:
            pool = [v for v in variants if isinstance(v, dict)] or [{"template": ""}]

        chosen = rng.weighted_choice(pool, [self._weight(v) for v in pool])
        return self._fill(str(chosen.get("template", "")), context)

    def _stable_seed(self, verb: str, keys: tuple) -> int:
        payload = f"{self._seed}:{verb}:{'|'.join(str(key) for key in keys)}".encode("utf-8")
        return int.from_bytes(hashlib.md5(payload).digest()[:8], "big")

    def _weight(self, variant: Dict[str, Any]) -> float:
        try:
            return max(0.0, float(variant.get("weight", 1)))
        except (TypeError, ValueError):
            return 1.0

    def _conditions_hold(self, when: Any, context: Dict[str, Any]) -> bool:
        """Return ``True`` when every predicate in ``when`` holds against ``context``."""
        if not when:
            return True
        predicates = when if isinstance(when, list) else [when]
        for predicate in predicates:
            if not isinstance(predicate, dict):
                return False
            field = predicate.get("field")
            op = predicate.get("op", "eq")
            value = predicate.get("value")
            if not self._compare(str(op), context.get(field), value):
                return False
        return True

    @staticmethod
    def _compare(op: str, actual: Any, expected: Any) -> bool:
        if op == "eq":
            return actual == expected
        if op == "ne":
            return actual != expected
        if actual is None or expected is None:
            return False
        try:
            if op == "gte":
                return actual >= expected
            if op == "lte":
                return actual <= expected
            if op == "gt":
                return actual > expected
            if op == "lt":
                return actual < expected
        except TypeError:
            return False
        return False

    @staticmethod
    def _fill(template: str, context: Dict[str, Any]) -> str:
        """Substitute ``{slot}`` placeholders, leaving unknown slots verbatim."""
        def substitute(match: "re.Match[str]") -> str:
            key = match.group(1)
            value = context.get(key)
            return str(value) if value is not None else match.group(0)

        return _SLOT_RE.sub(substitute, template)

    # -- description generators (A.2) ------------------------------------
    def describe_location(self, location: Dict[str, Any], season: str) -> str:
        """Prose for a location, varying by danger and season (stable per place)."""
        key = location.get("id") or location.get("name", "place")
        return self.render_stable(
            "describe_location",
            {
                "name": str(location.get("name", location.get("display_name", "this place"))),
                "danger": str(location.get("danger", "quiet")),
                "season": season,
            },
            key,
        )

    def describe_npc(self, name: str, tier: str, morality_band: str) -> str:
        """Prose for an NPC, varying by relationship tier and morality band."""
        return self.render_stable(
            "describe_npc",
            {"name": name, "tier": tier, "morality": morality_band},
            name,
        )

    def describe_item(self, name: str, rarity: str) -> str:
        """Prose for an item, varying by rarity (stable per item name)."""
        return self.render_stable("describe_item", {"item": name, "rarity": rarity}, name)

    def describe_technique(self, name: str, dao_name: str) -> str:
        """Prose for a technique, flavoured by its Dao affinity."""
        return self.render_stable("describe_technique", {"technique": name, "dao": dao_name}, name)

    def describe_breakthrough(self, success: bool, realm: str, season: str) -> str:
        """Prose for a breakthrough attempt, varying by outcome and season."""
        verb = "breakthrough_success" if success else "breakthrough_failure"
        return self.render(verb, {"realm": realm, "season": season})

    def describe_death(self, cause: str, age: Any, season: str) -> str:
        """Prose for the player's death, varying by cause, age, and season."""
        return self.render("death", {"cause": cause, "age": age, "season": season})
