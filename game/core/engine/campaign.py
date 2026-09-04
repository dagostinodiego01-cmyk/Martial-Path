"""Full campaign + post-game (ROADMAP D.3-D.5).

Three responsibilities, all engine-glue around the pure quest, secret-realm,
and cultivation systems:

* **D.3 endings** -- when a quest marked ``act_end: "act_three"`` completes,
  the campaign is won: the ending is chosen from the player's morality
  (guardian / free sword / demon sovereign), a legacy bonus is banked, and the
  ending id travels into the run's chronicle entry when the run eventually
  ends. The run itself continues: ascension (C.7) remains the deliberate way
  out, and death remains death.
* **D.5 endless road** -- once the campaign is complete (or the run retired
  into endless mode), a new ``ENDLESS_REALM`` action opens procedurally
  generated, depth-scaled secret realms that no longer cap essence realms:
  the first descent lifts the ``theoretical_endpoint`` lock on the essence
  track. Realm rewards and foes scale with depth; the same seed always
  produces the same realm at the same depth.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from game.core.constants import (
    CAMPAIGN_FINAL_ACT,
    CAMPAIGN_COMPLETE_BONUS,
    ENDLESS_TREASURE_POOL,
    EventType,
)
from game.models.enemy import Enemy
from game.utils.rng import RNG


class CampaignMixin:
    """Act completion, endings, and the endless post-game."""

    # -- D.3: campaign completion and endings ------------------------------
    def _maybe_complete_campaign(self, result: Dict[str, Any]) -> None:
        """Mark the campaign won when the final act's quest completes.

        Called from the combat-end path with the same result dict, so the
        completion rides the normal ``act_complete`` surfacing.
        """
        if result.get("act_complete") != CAMPAIGN_FINAL_ACT:
            return
        if getattr(self, "_campaign_complete", False):
            return
        self._campaign_complete = True
        ending = self._campaign_ending()
        self._campaign_ending_id = str(ending.get("ending_id", ""))
        bonus = int(CAMPAIGN_COMPLETE_BONUS)
        self.meta.add_memory(bonus)
        result["campaign_complete"] = {
            "ending_id": ending["ending_id"],
            "ending_name": ending["ending_name"],
            "legacy_bonus": bonus,
            "ancestral_memory": self.meta.memory(),
        }

    def _campaign_ending(self) -> Dict[str, str]:
        """Choose the campaign ending from how the player walked the world.

        Morality is the axis the data gives every run (choices, quests, origins
        feed it). Three endings: the guardian who shielded the mortal world,
        the devil who took heaven's throne, and the free sword who ascended
        owing nothing to either.
        """
        morality = int(getattr(self.player, "morality", 0))
        if morality >= 30:
            return {
                "ending_id": "realm_martyr",
                "ending_name": "The Realm Martyr -- a shield rises past the sky",
            }
        if morality <= -30:
            return {
                "ending_id": "demon_sovereign",
                "ending_name": "The Demon Sovereign takes the throne of heaven",
            }
        return {
            "ending_id": "ascended_sword",
            "ending_name": "The Free Sword ascends, owing nothing to saint or devil",
        }

    # -- D.5: the endless road ---------------------------------------------
    def _endless_realm(self) -> Dict[str, Any]:
        """Open a procedurally generated, depth-scaled endless realm (D.5)."""
        if self._realm is not None:
            return {"event": EventType.ERROR, "reason": "ALREADY_IN_REALM"}
        if not (self._endless or getattr(self, "_campaign_complete", False)):
            return {"event": EventType.ERROR, "reason": "ENDLESS_NOT_OPEN"}
        unlocked = self._unlock_endless_essence_cap()
        depth = int(getattr(self, "_endless_depth", 0)) + 1
        essence = self.player.cultivation_state.essence
        essence_order = int(self._essence_realm_orders.get(essence.realm_id, 1))
        mook_pool = [str(enemy_id) for enemy_id in getattr(self, "_enemy_templates", {}).keys()]
        named_pool = [str(enemy_id) for enemy_id in getattr(self, "_character_enemy_templates", {}).keys()]
        # Deterministic per (seed, depth): the same seed replays the same road.
        depth_rng = RNG((int(self._seed) * 1000003 + depth) % (2**31))
        realm = self.secret_realm.generate_endless(
            depth,
            mook_pool,
            named_pool,
            ENDLESS_TREASURE_POOL,
            essence_order=essence_order,
            rng=depth_rng,
            foe_orders=getattr(self, "_foe_essence_orders", {}),
        )
        self._realm = {"realm": realm, "index": 0, "endless_depth": depth}
        self._endless_depth = depth
        result: Dict[str, Any] = {
            "event": EventType.REALM_ENTERED,
            "endless": True,
            "endless_depth": depth,
            "realm": {
                "display_name": realm.get("display_name", "the endless road"),
                "description": realm.get("description", ""),
                "depth": depth,
            },
            "rooms_total": len(realm["rooms"]),
            "player_message": f"You step onto the endless road, depth {depth}.",
        }
        if unlocked:
            result["realm_cap_lifted"] = unlocked
        return result

    def _unlock_endless_essence_cap(self) -> Optional[str]:
        """Lift the essence track's final cap once the endless road opens.

        The cultivation data marks the last realm ``reachable: false``
        (``theoretical_endpoint``). Endless play removes that lock on the
        engine's loaded copy, so ``ESSENCE_BREAKTHROUGH`` may push past it.
        """
        essence_by_id = getattr(self.cultivation, "_essence_by_id", None)
        if not isinstance(essence_by_id, dict):
            return None
        capped = [
            realm
            for realm in essence_by_id.values()
            if realm.get("reachable") is False or realm.get("type") == "theoretical_endpoint"
        ]
        if not capped:
            return None
        realm = sorted(capped, key=lambda entry: int(entry.get("order", 0)))[0]
        realm.pop("reachable", None)
        if realm.get("type") == "theoretical_endpoint":
            realm["type"] = "endless_endpoint"
        return str(realm.get("id", ""))

    def _scale_enemy(self, enemy: Enemy, scale: float) -> None:
        """Inflate a foe for endless depth: HP/attack/defense/reward scale."""
        factor = float(scale)
        if factor <= 1.0:
            return
        enemy.max_hp = max(1, int(round(enemy.max_hp * factor)))
        enemy.hp = enemy.max_hp
        enemy.attack = max(1, int(round(enemy.attack * factor)))
        enemy.defense = max(0, int(round(enemy.defense * factor)))
        enemy.exp_reward = max(1, int(round(enemy.exp_reward * factor)))

    def _scale_endless_room(self, room: Dict[str, Any]) -> None:
        """Apply an endless room's ``scale`` to the foe about to spawn."""
        if self._current_enemy is None:
            return
        try:
            scale = float(room.get("scale", 0) or 0)
        except (TypeError, ValueError):
            scale = 0.0
        if scale > 1.0:
            self._scale_enemy(self._current_enemy, scale)

    def _complete_realm(self) -> Dict[str, Any]:
        """Wrap realm completion with the endless depth reward (D.5)."""
        depth = 0
        if self._realm is not None:
            depth = int(self._realm.get("endless_depth", 0) or 0)
        result = super()._complete_realm()
        if depth > 0:
            bonus_exp = 150 * depth
            bonus_gold = 100 * depth
            self.player.exp += bonus_exp
            self.player.gold += bonus_gold
            reward = result.setdefault("reward", {})
            reward["exp"] = int(reward.get("exp", 0)) + bonus_exp
            reward["gold"] = int(reward.get("gold", 0)) + bonus_gold
            result["endless_depth"] = depth
            result["player_message"] = (
                f"You conquer depth {depth} of the endless road and claim its reward."
            )
        return result

    # -- D.3: chronicle ------------------------------------------------------
    def _campaign_chronicle_field(self) -> Optional[str]:
        """The campaign ending this run earned (``None`` if unfinished)."""
        ending_id = str(getattr(self, "_campaign_ending_id", "") or "")
        return ending_id or None

    # -- views ----------------------------------------------------------------
    def _campaign_view(self) -> Dict[str, Any]:
        """Compact campaign/post-game summary for the main state payload."""
        return {
            "campaign_complete": bool(getattr(self, "_campaign_complete", False)),
            "ending_id": str(getattr(self, "_campaign_ending_id", "") or ""),
            "endless": bool(self._endless),
            "endless_depth": int(getattr(self, "_endless_depth", 0)),
            "can_endless_realm": bool(self._endless or getattr(self, "_campaign_complete", False)),
        }

    # -- shared room-pool constant (data-driven, referenced by systems.py) ----
    def _endless_realm_pools(self) -> Dict[str, List[Dict[str, Any]]]:
        """Expose the endless treasure pool for UI or validation needs."""
        return {"treasure_pool": list(ENDLESS_TREASURE_POOL)}
