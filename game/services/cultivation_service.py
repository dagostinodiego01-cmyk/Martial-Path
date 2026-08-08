"""Service facade for cultivation operations.

The service coordinates player lookup and delegates actual progression rules to
the cultivation system. It is intentionally thin so UI/API adapters can depend
on a stable application-facing API without owning gameplay logic.
"""
from __future__ import annotations

from typing import Any, Dict

from game.models.player import Player
from game.systems.cultivation_system import CultivationSystem


class CultivationService:
    """Coordinates cultivation actions for registered players."""

    def __init__(self, players: Dict[str, Player], system: CultivationSystem) -> None:
        self._players = players
        self._system = system

    def get_cultivation_state(self, player_id: str) -> Dict[str, Any]:
        player = self._player(player_id)
        state = player.cultivation_state.to_dict()
        state["body_transformation"]["display_name"] = self._system.get_body_display_name(player)
        body_required = self._system.get_body_required_progress(player)
        state["body_transformation"]["required_progress"] = round(body_required, 1)
        state["body_transformation"]["progress_percent"] = round(
            (state["body_transformation"].get("progress", 0.0) / body_required) * 100.0,
            1,
        )
        state["essence_gathering"]["display_name"] = self._system.get_essence_display_name(player)
        essence_required = self._system.get_essence_required_progress(player)
        state["essence_gathering"]["required_progress"] = round(essence_required, 1)
        state["essence_gathering"]["progress_percent"] = round(
            (state["essence_gathering"].get("progress", 0.0) / essence_required) * 100.0,
            1,
        )
        state["essence_gathering"]["unlocked"] = self._system.is_essence_unlocked(player)
        state["essence_gathering"]["unlock_requirement"] = self._system.get_essence_unlock_requirement(player)
        state["essence_unlocked"] = self._system.is_essence_unlocked(player)
        state["balance"] = self._system.calculate_body_essence_balance(player)
        state["breakthrough_safety"] = self._system.calculate_breakthrough_safety(player)
        state["summary"] = (
            f"Body Transformation: {state['body_transformation']['display_name']} | "
            f"Essence Gathering: {state['essence_gathering']['display_name']}"
        )
        return state

    def train_body(self, player_id: str, method_id: str = "train_body") -> Dict[str, Any]:
        return self._system.train_body(self._player(player_id), method_id)

    def train_essence(self, player_id: str, method_id: str = "gather_essence") -> Dict[str, Any]:
        return self._system.train_essence(self._player(player_id), method_id)

    def attempt_body_breakthrough(self, player_id: str) -> Dict[str, Any]:
        return self._system.attempt_body_breakthrough(self._player(player_id))

    def attempt_essence_breakthrough(self, player_id: str) -> Dict[str, Any]:
        return self._system.attempt_essence_breakthrough(self._player(player_id))

    def stabilise_foundation(self, player_id: str) -> Dict[str, Any]:
        return self._system.stabilise_foundation(self._player(player_id))

    def stabilise_essence(self, player_id: str) -> Dict[str, Any]:
        return self._system.stabilise_essence(self._player(player_id))

    def calculate_derived_cultivation_stats(self, player_id: str) -> Dict[str, Any]:
        return self._system.calculate_derived_cultivation_stats(self._player(player_id))

    def get_breakthrough_preview(self, player_id: str, track_id: str) -> Dict[str, Any]:
        return self._system.get_breakthrough_preview(self._player(player_id), track_id)

    def validate_cultivation_data(self) -> Dict[str, Any]:
        return self._system.validate_cultivation_data()

    @property
    def system(self) -> CultivationSystem:
        return self._system

    def _player(self, player_id: str) -> Player:
        try:
            return self._players[player_id]
        except KeyError as exc:
            raise KeyError(f"Unknown player_id: {player_id}") from exc