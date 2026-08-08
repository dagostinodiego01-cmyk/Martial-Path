"""Centralized random number generation.

All randomness flows through a single :class:`RNG` instance so that games can be
seeded for deterministic, reproducible tests. Gameplay systems must never touch
the global :mod:`random` state directly; they receive an ``RNG`` instead.
"""
from __future__ import annotations

import random
from typing import Sequence, TypeVar

T = TypeVar("T")


class RNG:
    """A thin, seedable wrapper around :class:`random.Random`."""

    def __init__(self, seed: int | None = None) -> None:
        self._random = random.Random(seed)

    def seed(self, seed: int | None) -> None:
        """Reseed the generator (useful to reset state between tests)."""
        self._random.seed(seed)

    def randint(self, low: int, high: int) -> int:
        """Return a random integer N such that ``low <= N <= high``."""
        return self._random.randint(low, high)

    def chance(self, probability: float) -> bool:
        """Return ``True`` with the given probability (0.0 - 1.0)."""
        return self._random.random() < probability

    def choice(self, items: Sequence[T]) -> T:
        """Return a uniformly random element from ``items``."""
        return self._random.choice(items)

    def weighted_choice(self, items: Sequence[T], weights: Sequence[float]) -> T:
        """Return one element from ``items`` chosen according to ``weights``."""
        return self._random.choices(list(items), weights=list(weights), k=1)[0]
