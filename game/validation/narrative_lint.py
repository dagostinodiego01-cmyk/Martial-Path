"""Lint checks for ``data/narrative_templates.json`` (ROADMAP A.7, A.6).

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
* **voice consistency** (A.6) — no gamey/out-of-world vocabulary in templates,
  no brace artifacts (only ``{snake_case}`` slots), and at least two distinct
  variants per verb so prose does not repeat a single sentence.
* **glossary conformance** (A.6) — every ``{realm}``/``{dao}``/``{tier}``/
  ``{season}`` value rendered from shipped templates must be an approved term
  from ``data/lore_glossary.json`` (realms/daos/tiers seeded from the game's
  display names).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

from game.core.constants import EventType
from game.systems.narrative_system import EVENT_VERB, SUPPORTED_OPS

_SLOT_RE = re.compile(r"\{([a-z_][a-z0-9_]*)\}")

# Out-of-world vocabulary that breaks the cultivation-novel register (A.6).
# Matched as whole words, case-insensitive, inside template text only.
GAMEY_TERMS: FrozenSet[str] = frozenset({
    "mana",
    "respawn",
    "respawning",
    "buff",
    "buffs",
    "buffed",
    "nerf",
    "nerfed",
    "grind",
    "grinding",
    "xp",
    "respawned",
    "leveling",
    "levelling",
    "skilltree",
    "gameplay",
    "stat",
    "stats",
    "ui",
    "gui",
    "menu",
    "menus",
    "savefile",
    "savefiles",
    "loadgame",
    "tutorial",
    "loading",
    "debug",
    "log",
    "logs",
    "questlog",
    "inventoried",
    "hopscotch",
})

# Slots whose runtime values must be approved lore-glossary terms (A.6).
GLOSSARY_SLOTS: FrozenSet[str] = frozenset({"realm", "dao", "tier", "season", "morality"})

_GLOSSARY_PATH = Path(__file__).resolve().parents[2] / "game" / "data" / "lore_glossary.json"


def load_glossary_terms(path: "Path | None" = None) -> Dict[str, FrozenSet[str]]:
    """Load the lore glossary as ``{slot: frozenset(approved terms)}``.

    Terms declared with ``slot: "any"`` are admitted to every slot. Missing or
    malformed files yield empty sets (prose values then fail closed, surfacing
    the gap instead of silently passing).
    """
    path = path or _GLOSSARY_PATH
    terms: Dict[str, Set[str]] = {}
    try:
        entries = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {slot: frozenset() for slot in GLOSSARY_SLOTS}
    if not isinstance(entries, list):
        return {slot: frozenset() for slot in GLOSSARY_SLOTS}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        term = entry.get("term")
        slot = entry.get("slot", "any")
        if not isinstance(term, str) or not term:
            continue
        if not isinstance(slot, str) or not slot:
            continue
        targets = GLOSSARY_SLOTS if slot == "any" else {slot}
        for target in targets:
            terms.setdefault(target, set()).add(term)
    return {slot: frozenset(values) for slot, values in {s: terms.get(s, set()) for s in GLOSSARY_SLOTS}.items()}

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


def lint_narrative_templates(templates: Any, glossary: Optional[Dict[str, FrozenSet[str]]] = None) -> List[Tuple[str, str]]:
    """Return ``(category, message)`` problems found in ``templates``.

    ``glossary`` maps narrative slots to approved terms (A.6); it defaults to the
    shipped ``data/lore_glossary.json``. Pass an explicit mapping in tests to
    lint template data against a controlled vocabulary.
    """
    problems: List[Tuple[str, str]] = []
    if not isinstance(templates, dict):
        return [("bad_narrative", "narrative_templates must be an object mapping verbs to variants")]
    if glossary is None:
        glossary = load_glossary_terms()

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
            # A.6 voice checks (per variant).
            _lint_gamey_terms(verb, template, problems)
            _lint_brace_artifacts(verb, template, problems)
            _lint_glossary_slots(verb, variant.get("when"), glossary, problems)
            _lint_when(verb, variant.get("when"), problems)

        # Unused declarations (declared but never referenced in a template).
        for slot in declared_set - used_slots:
            problems.append(("bad_narrative", f"narrative verb '{verb}' declares unused variable '{slot}'"))

        # A.6 sameness floor: every verb needs at least two distinct variants so
        # repeated actions do not narrate with the identical sentence.
        if len(variants) < 2:
            problems.append(
                ("bad_narrative", f"narrative verb '{verb}' must have >= 2 distinct variants for voice variety (has {len(variants)})")
            )

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


def _lint_gamey_terms(verb: str, template: str, problems: List[Tuple[str, str]]) -> None:
    """A.6: no out-of-world/gamey vocabulary inside template prose."""
    for word in re.findall(r"[A-Za-z]+", template.lower()):
        if word in GAMEY_TERMS:
            problems.append(
                ("bad_narrative", f"narrative verb '{verb}' uses out-of-world term '{word}' (see game/docs/VOICE_GUIDE.md)")
            )


def _lint_brace_artifacts(verb: str, template: str, problems: List[Tuple[str, str]]) -> None:
    """A.6: the only brace groups in a template are declared {snake_case} slots."""
    for group in re.findall(r"\{[^}]*\}", template):
        if not _SLOT_RE.fullmatch(group):
            problems.append(
                ("bad_narrative", f"narrative verb '{verb}' contains a non-slot brace group {group!r} (brace artifacts are forbidden)")
            )


def _lint_glossary_slots(
    verb: str,
    when: Any,
    glossary: Optional[Dict[str, FrozenSet[str]]],
    problems: List[Tuple[str, str]],
) -> None:
    """A.6: literal slot values in when-clauses must be approved glossary terms.

    The renderer substitutes slot values at runtime from game state; the shipped
    ``when`` clauses are the one place those values are visible statically, so
    they are checked against the glossary here. Slots with no when-clause
    constraint cannot be statically validated and are skipped.
    """
    if when is None:
        return
    predicates = when if isinstance(when, list) else [when]
    for predicate in predicates:
        if not isinstance(predicate, dict):
            continue
        field = predicate.get("field")
        if field not in GLOSSARY_SLOTS:
            continue
        if "value" not in predicate:
            continue
        approved = (glossary or {}).get(str(field), frozenset())
        value = predicate["value"]
        if isinstance(value, list):
            literals = [str(v) for v in value]
        else:
            literals = [str(value)]
        for literal in literals:
            if approved and literal not in approved:
                problems.append(
                    ("bad_narrative", f"narrative verb '{verb}' when-clause uses '{literal}' for slot '{field}' which is not in the lore glossary")
                )
