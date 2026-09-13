"""Primitives shared by the per-collection validators.

Split out of ``data_validator`` (V.5) so the four domain modules can each be
owned by one lane without four writers in one file. Nothing here knows about a
specific collection: these are the small checks every collection reuses.

This module reads data only; it never mutates the registry or touches gameplay.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Set

from game.validation.validation_error import ValidationResult


def _id_set(entries: Iterable[Dict[str, Any]]) -> Set[str]:
    return {entry["id"] for entry in entries if "id" in entry}


def _check_loot(entity: Dict[str, Any], item_ids: Set[str], category: str, result: ValidationResult) -> None:
    for drop in entity.get("loot_table", []):
        item_id = drop.get("item_id")
        if item_id not in item_ids:
            result.add(category, f"'{entity.get('id')}' drops missing item '{item_id}'")


def _validate_modifier_group(item_id: str, group_name: str, modifiers: Any, valid_keys: Set[str], result: ValidationResult) -> None:
    if not isinstance(modifiers, dict):
        result.add("bad_equipment", f"equipment '{item_id}' {group_name} must be an object")
        return
    for key, value in modifiers.items():
        if key not in valid_keys:
            result.add("bad_equipment", f"equipment '{item_id}' has unsupported {group_name}.{key}")
        if not isinstance(value, (int, float)):
            result.add("bad_equipment", f"equipment '{item_id}' {group_name}.{key} must be numeric")
        if key.endswith("_multiplier") and isinstance(value, (int, float)) and value <= 0:
            result.add("bad_equipment", f"equipment '{item_id}' {group_name}.{key} must be positive")
