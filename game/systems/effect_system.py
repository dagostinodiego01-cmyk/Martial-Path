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

# The canonical vocabulary of *implemented* item/event effects. An item whose
# ``effect`` is outside this set advertises a promise the engine cannot keep:
# consuming it would burn the stack for nothing. The dead-content sweep
# (ROADMAP G.2) fails the build on such items so this set stays the contract.
SUPPORTED_EFFECTS = frozenset(
    {
        "heal",
        "restore_qi",
        "cultivation_boost",
        "restore",
        "exp",
        "lifespan_extension",
        "comprehension_boost",
        "restore_hp_qi",
        "cleanse_poison",
        "body_temper",
        "breakthrough_aid",
    }
)

# Effects that heal/restore HP and/or Qi -- handled by the same branch so a
# single consumable can top up both pools.
_RESTORE_EFFECTS = frozenset({"restore_hp_qi"})


class EffectSystem:
    """Applies named effects to a player and reports what changed."""

    def apply_to_player(self, player: Player, effect_type: str, magnitude: int) -> Dict[str, Any]:
        """Interpret an effect identifier and mutate the player accordingly."""
        if effect_type == "heal":
            return {"healed": player.heal(magnitude), "hp": player.hp}
        if effect_type == "restore_qi":
            return {"qi_restored": player.restore_qi(magnitude), "qi": player.qi}
        if effect_type in _RESTORE_EFFECTS:
            healed = player.heal(magnitude)
            restored = player.restore_qi(magnitude)
            return {
                "healed": healed,
                "hp": player.hp,
                "qi_restored": restored,
                "qi": player.qi,
            }
        if effect_type == "lifespan_extension":
            # Longevity pills are the classic cultivation consumable: each adds
            # flat years to the character's maximum lifespan (LifespanSystem
            # reads ``lifespan_bonus_years``).
            player.lifespan_bonus_years += int(magnitude)
            return {"lifespan_bonus_years": player.lifespan_bonus_years, "added_years": int(magnitude)}
        if effect_type == "comprehension_boost":
            player.comprehension += int(magnitude)
            return {"comprehension_gained": int(magnitude), "comprehension": player.comprehension}
        if effect_type == "body_temper":
            # A tempering tonic permanently hardens the body.
            player.body_strength += int(magnitude)
            return {"body_strength_gained": int(magnitude), "body_strength": player.body_strength}
        if effect_type == "cleanse_poison":
            return self._cleanse(player)
        if effect_type == "breakthrough_aid":
            # A breakthrough pill banks foundation stability, making the next
            # attempt safer. It never forces the breakthrough itself.
            body = player.cultivation_state.body
            gain = min(100.0, float(magnitude))
            body.foundation_stability = min(100.0, float(body.foundation_stability) + gain)
            return {
                "foundation_stability_gained": gain,
                "foundation_stability": round(float(body.foundation_stability), 1),
                "track_id": "body_transformation",
            }
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

    # Afflictions a cleansing pill strips (``counter`` is beneficial, so kept).
    _AFFLICTIONS = ("dot_damage", "debuff_attack", "debuff_defense", "stun")

    def _cleanse(self, player: Player) -> Dict[str, Any]:
        """Strip timed combat afflictions (poison/dots/debuffs) from the player."""
        statuses = getattr(player, "statuses", None)
        cleared = 0
        if isinstance(statuses, dict):
            for key in self._AFFLICTIONS:
                if statuses.pop(key, None) is not None:
                    cleared += 1
        return {"statuses_cleared": cleared}
