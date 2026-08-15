"""Lint checks for ``data/narrative_templates.json`` (ROADMAP A.7).

A single source of truth for narrative-template authoring errors, shared by the
central validator (``validate_all_game_data``) and the standalone authoring tool
``tools/narrative_lint.py``. Every check returns a ``(category, message)`` pair
so callers can render problems however they like.

Checks:

* **structure** — every verb is an object with a non-empty ``variants`` list and
  a ``variables`` list of strings; every variant has a non-empty ``template``
  string and a non-negative numeric ``weight``.
* **missing vars** — every ``{slot}`` used in a template is declared in
  ``variables``.
* **unused vars** — every declared ``variables`` entry is actually used in some
  template.
* **unbalanced branches** — every ``when`` predicate has a non-empty ``field``,
  a known ``op``, and a ``value``.
* **coverage** — the core verbs ship with >= 3 weighted variants, and every
  :class:`~game.core.constants.EventType` maps (via ``EVENT_VERB``) to a verb
  with at least one variant.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from game.core.constants import EventType
from game.systems.narrative_system import EVENT_VERB, SUPPORTED_OPS

_SLOT_RE = re.compile(r"\{([a-z_][a-z0-9_]*)\}")

# Verbs every narrative catalogue must cover with at least three weighted
# variants (ROADMAP A.1).
CORE_VERBS: Tuple[str, ...] = (
    "train_body",
    "train_essence",
    "rest",
    "meditate",
    "explore_nothing",
    "explore_combat",
    "explore_loot",
    "explore_special",
    "travel",
    "attack",
    "breakthrough_success",
    "breakthrough_failure",
    "death",
)


def lint_narrative_templates(templates: Any) -> List[Tuple[str, str]]:
    """Return ``(category, message)`` problems found in ``templates``."""
    problems: List[Tuple[str, str]] = []
    if not isinstance(templates, dict):
        return [("bad_narrative", "narrative_templates must be an object mapping verbs to variants")]

    for verb, entry in templates.items():
        if not isinstance(entry, dict):
            problems.append(("bad_narrative", f"narrative verb '{verb}' must be an object"))
            continue

        variants = entry.get("variants")
        if not isinstance(variants, list) or not variants:
            problems.append(("bad_narrative", f"narrative verb '{verb}' must declare a non-empty 'variants' list"))
            continue

        declared = entry.get("variables", [])
        if not isinstance(declared, list) or not all(isinstance(name, str) and name for name in declared):
            problems.append(("bad_narrative", f"narrative verb '{verb}' 'variables' must be a list of strings"))
            declared = []
        declared_set = set(declared)

        used_slots: set = set()
        for variant in variants:
            if not isinstance(variant, dict):
                problems.append(("bad_narrative", f"narrative verb '{verb}' has a non-object variant"))
                continue
            template = variant.get("template")
            if not isinstance(template, str) or not template:
                problems.append(("bad_narrative", f"narrative verb '{verb}' has a variant missing a 'template' string"))
                continue
            weight = variant.get("weight", 1)
            if isinstance(weight, bool) or not isinstance(weight, (int, float)) or weight < 0:
                problems.append(("bad_narrative", f"narrative verb '{verb}' has a variant with a non-numeric 'weight'"))
            for slot in _SLOT_RE.findall(template):
                used_slots.add(slot)
                if slot not in declared_set:
                    problems.append(("bad_narrative", f"narrative verb '{verb}' uses undeclared slot '{{{slot}}}'"))
            _lint_when(verb, variant.get("when"), problems)

        # Unused declarations (declared but never referenced in a template).
        for slot in declared_set - used_slots:
            problems.append(("bad_narrative", f"narrative verb '{verb}' declares unused variable '{slot}'"))

    for verb in CORE_VERBS:
        entry = templates.get(verb)
        count = (
            len(entry.get("variants", []))
            if isinstance(entry, dict) and isinstance(entry.get("variants"), list)
            else 0
        )
        if count < 3:
            problems.append(("bad_narrative", f"core narrative verb '{verb}' must have >= 3 weighted variants (has {count})"))

    # Coverage: every EventType must narrate through an existing verb (A.5).
    for event in EventType:
        verb = EVENT_VERB.get(event.value, event.value.lower())
        entry = templates.get(verb)
        if not isinstance(entry, dict) or not isinstance(entry.get("variants"), list) or not entry["variants"]:
            problems.append(("bad_narrative", f"event '{event.value}' maps to missing/empty narrative verb '{verb}'"))

    return problems


def _lint_when(verb: str, when: Any, problems: List[Tuple[str, str]]) -> None:
    if when is None:
        return
    predicates = when if isinstance(when, list) else [when]
    for predicate in predicates:
        if not isinstance(predicate, dict):
            problems.append(("bad_narrative", f"narrative verb '{verb}' has a non-object when-predicate"))
            continue
        if not isinstance(predicate.get("field"), str) or not predicate.get("field"):
            problems.append(("bad_narrative", f"narrative verb '{verb}' when-predicate is missing a 'field'"))
        if predicate.get("op", "eq") not in SUPPORTED_OPS:
            problems.append(("bad_narrative", f"narrative verb '{verb}' has an unknown op '{predicate.get('op')}'"))
        if "value" not in predicate:
            problems.append(("bad_narrative", f"narrative verb '{verb}' when-predicate is missing a 'value'"))


def variant_count(templates: Any, verb: str) -> int:
    """Return the number of variants declared for ``verb`` (0 if unknown)."""
    entry = templates.get(verb) if isinstance(templates, dict) else None
    if not isinstance(entry, dict) or not isinstance(entry.get("variants"), list):
        return 0
    return len(entry["variants"])
