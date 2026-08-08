"""Result types for data validation.

A validation pass collects every problem it finds rather than failing on the
first, so a single run reports all broken references at once. ``ValidationResult``
is intentionally tiny and dependency-free so it can be used by tests, a CLI check,
or a future editor tool without pulling in the rest of the game.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ValidationError:
    """A single data problem, tagged with a category for grouping/filtering."""

    category: str
    message: str

    def __str__(self) -> str:
        return f"[{self.category}] {self.message}"


@dataclass
class ValidationResult:
    """The accumulated outcome of a validation pass."""

    errors: List[ValidationError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Return ``True`` when no problems were recorded."""
        return not self.errors

    def add(self, category: str, message: str) -> None:
        """Record a problem under ``category``."""
        self.errors.append(ValidationError(category, message))

    def format_errors(self) -> str:
        """Return a human-readable, newline-separated summary of all problems."""
        if not self.errors:
            return "No validation errors."
        return "\n".join(f"- {error}" for error in self.errors)

    def __len__(self) -> int:
        return len(self.errors)
