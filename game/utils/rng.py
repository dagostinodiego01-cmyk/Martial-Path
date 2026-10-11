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

    def get_state(self) -> list:
        """Return the generator's full internal state as JSON-safe data.

        Serializing this (plus the run seed) is what lets a saved run continue
        bit-for-bit in a *fresh process* -- see ``SV.5`` in TASKS.md and
        ``game/docs/SAVE_SYSTEM.md``. The tuple ``random.Random.getstate()``
        returns is flattened to lists so ``json.dumps`` accepts it.
        """
        version, internal, gauss = self._random.getstate()
        return [int(version), [int(value) for value in internal], gauss]

    def set_state(self, state) -> None:
        """Restore a state produced by :meth:`get_state` (list or tuple form)."""
        version, internal, gauss = state
        self._random.setstate((int(version), tuple(int(value) for value in internal), gauss))

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
