"""Small text helpers shared by the systems that write player-facing English.

The engine composes a lot of prose by concatenating a name into a sentence
(``f"A {enemy.name} bars your way."``). Names come from data, so the article has
to be chosen at runtime rather than hard-coded: the catalogue contains both
``Village Shaman`` and ``Iron-Fang Wolf``. Keeping the rule in one function means
every sentence agrees, instead of each call site guessing.
"""
from __future__ import annotations

#: Words that already carry their own determiner; adding one would double it.
_DETERMINERS = ("a ", "an ", "the ", "some ", "his ", "her ", "its ", "their ")


def indefinite_article(word: str) -> str:
    """Return ``A`` or ``An`` for ``word``.

    The test is the first letter rather than the first sound: every name in the
    catalogue is read with its spelling, and a sound-based rule would need a
    pronunciation table for ``hour``/``honour``-style exceptions the data does
    not contain.
    """
    for character in word:
        if character.isalpha():
            return "An" if character.lower() in "aeiou" else "A"
    return "A"


def with_article(name: str) -> str:
    """Return ``name`` prefixed with the right indefinite article.

    ``with_article("Iron-Fang Wolf")`` -> ``"An Iron-Fang Wolf"``. A name that
    already starts with a determiner (``"The Nameless"``) is returned unchanged.
    """
    stripped = str(name or "").strip()
    if not stripped:
        return ""
    lowered = stripped.lower()
    if lowered.startswith(_DETERMINERS):
        return stripped
    return f"{indefinite_article(stripped)} {stripped}"
