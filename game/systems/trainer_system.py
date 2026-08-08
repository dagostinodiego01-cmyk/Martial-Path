"""Data-driven skill trainers (technique masters).

Trainers are static data keyed by location, mirroring shops. A trainer offers a
list of techniques the player can learn for a currency cost. This system lists a
location's trainers, resolves affordability/known-state, spends currency, and
delegates the actual learning to :class:`SkillSystem`. It performs no I/O and
returns structured results only.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from game.core.constants import EventType
from game.models.player import Player
from game.models.skill import Skill
from game.systems import currency
from game.systems.skill_system import SkillSystem


class TrainerSystem:
    """Lists location trainers and resolves paid technique learning."""

    def __init__(
        self,
        trainers: Iterable[Dict[str, Any]],
        skills: Dict[str, Skill],
        skill_system: SkillSystem,
    ) -> None:
        self._trainers = {str(trainer.get("id")): dict(trainer) for trainer in trainers if trainer.get("id")}
        self._skills = skills
        self._skill_system = skill_system

    def trainers_for_location(self, location_id: str) -> List[Dict[str, Any]]:
        """Return summary data for trainers available at a location."""
        return [self._trainer_summary(t) for t in self._trainers.values() if self._is_at_location(t, location_id)]

    def trainer_view(self, player: Player, trainer_id: str = "") -> Dict[str, Any]:
        """Return a trainer's teachable techniques visible to the player."""
        trainer = self._resolve_trainer(player.current_location, trainer_id)
        if trainer is None:
            reason = "UNKNOWN_TRAINER" if trainer_id else "NO_TRAINER_AVAILABLE"
            return {"event": EventType.ERROR, "reason": reason, "trainer_id": trainer_id, "location_id": player.current_location}
        if not self._is_at_location(trainer, player.current_location):
            return {"event": EventType.ERROR, "reason": "TRAINER_NOT_AVAILABLE", "trainer_id": trainer_id, "location_id": player.current_location}
        return {
            "event": EventType.TRAINER,
            "trainer": self._trainer_summary(trainer),
            "techniques": [self._technique_view(player, entry) for entry in trainer.get("techniques", [])],
            "wallet": currency.wallet_view(player),
        }

    def learn(self, player: Player, skill_id: str, trainer_id: str = "") -> Dict[str, Any]:
        """Learn a technique from an available trainer, spending its currency cost."""
        if not skill_id:
            return {"event": EventType.ERROR, "reason": "NO_SKILL_SPECIFIED", "trainer_id": trainer_id}

        trainer = self._resolve_trainer(player.current_location, trainer_id)
        if trainer is None:
            reason = "UNKNOWN_TRAINER" if trainer_id else "NO_TRAINER_AVAILABLE"
            return {"event": EventType.ERROR, "reason": reason, "trainer_id": trainer_id, "location_id": player.current_location}
        if not self._is_at_location(trainer, player.current_location):
            return {"event": EventType.ERROR, "reason": "TRAINER_NOT_AVAILABLE", "trainer_id": trainer_id, "location_id": player.current_location}

        entry = self._technique_entry(trainer, skill_id)
        if entry is None:
            return {"event": EventType.ERROR, "reason": "TECHNIQUE_NOT_OFFERED", "trainer_id": str(trainer.get("id")), "skill_id": skill_id}
        if skill_id not in self._skills:
            return {"event": EventType.ERROR, "reason": "UNKNOWN_SKILL", "skill_id": skill_id}
        if self._skill_system.knows(player, skill_id):
            return {"event": EventType.ERROR, "reason": "SKILL_ALREADY_KNOWN", "skill_id": skill_id, "name": self._skills[skill_id].name}

        price = currency.normalise_price(entry.get("price"))
        missing = currency.shortage(player, price)
        if missing:
            return {
                "event": EventType.ERROR,
                "reason": "INSUFFICIENT_FUNDS",
                "skill_id": skill_id,
                "price": price,
                "missing": missing,
                "wallet": currency.wallet_view(player),
            }

        currency.spend(player, price)
        result = self._skill_system.learn_skill(
            player,
            skill_id,
            source="trainer",
            price=price,
            wallet=currency.wallet_view(player),
        )
        if result.get("event") == EventType.SKILL_LEARNED:
            result["trainer_id"] = str(trainer.get("id"))
        return result

    # -- internal helpers -------------------------------------------------
    def _resolve_trainer(self, location_id: str, trainer_id: str) -> Optional[Dict[str, Any]]:
        if trainer_id:
            return self._trainers.get(trainer_id)
        for trainer in self._trainers.values():
            if self._is_at_location(trainer, location_id):
                return trainer
        return None

    def _is_at_location(self, trainer: Dict[str, Any], location_id: str) -> bool:
        return location_id in [str(entry) for entry in trainer.get("location_ids", [])]

    def _technique_entry(self, trainer: Dict[str, Any], skill_id: str) -> Optional[Dict[str, Any]]:
        for entry in trainer.get("techniques", []):
            if entry.get("skill_id") == skill_id:
                return entry
        return None

    def _technique_view(self, player: Player, entry: Dict[str, Any]) -> Dict[str, Any]:
        skill_id = str(entry.get("skill_id", ""))
        skill = self._skills.get(skill_id)
        price = currency.normalise_price(entry.get("price"))
        return {
            "skill_id": skill_id,
            "name": skill.name if skill else skill_id,
            "type": skill.type if skill else "unknown",
            "description": skill.description if skill else "",
            "price": price,
            "already_known": self._skill_system.knows(player, skill_id),
            "affordable": not currency.shortage(player, price),
        }

    def _trainer_summary(self, trainer: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": str(trainer.get("id", "")),
            "display_name": str(trainer.get("display_name", trainer.get("id", ""))),
            "location_ids": [str(location_id) for location_id in trainer.get("location_ids", [])],
            "description": str(trainer.get("description", "")),
        }
