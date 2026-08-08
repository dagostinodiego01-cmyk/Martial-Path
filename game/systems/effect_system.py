"""Effect system.

Central interpreter for player-facing effects such as healing, Qi restoration,
cultivation boosts, full restores, and experience gains. Both consumable items
(via the inventory system) and special exploration events (via the engine) route
their effects through this single place, so the rules live in one location.

Returns structured results only; never prints or formats player-facing text.
"""
from __future__ import annotations

from typing import Any, Dict

from game.models.player import Player


class EffectSystem:
    """Applies named effects to a player and reports what changed."""

    def apply_to_player(self, player: Player, effect_type: str, magnitude: int) -> Dict[str, Any]:
        """Interpret an effect identifier and mutate the player accordingly."""
        if effect_type == "heal":
            return {"healed": player.heal(magnitude), "hp": player.hp}
        if effect_type == "restore_qi":
            return {"qi_restored": player.restore_qi(magnitude), "qi": player.qi}
        if effect_type == "cultivation_boost":
            body = player.cultivation_state.body
            body.progress = min(100.0, body.progress + magnitude)
            if body.realm_id == "tempering_marrow":
                body.marrow_percent = body.progress
            player.progress = body.progress
            return {"progress_boost": magnitude, "progress": round(body.progress, 1), "track_id": "body_transformation"}
        if effect_type == "restore":
            player.hp = player.max_hp
            player.qi = player.max_qi
            return {"restored": True, "hp": player.hp, "qi": player.qi}
        if effect_type == "exp":
            player.exp += magnitude
            return {"exp_gained": magnitude, "exp": player.exp}
        return {"note": "no_effect"}
