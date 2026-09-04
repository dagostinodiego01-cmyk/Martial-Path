"""Living-world glue (ROADMAP E.1-E.5): ticks, seasons, economy, rumors.

This mixin owns no simulation logic of its own -- :class:`~game.systems.world_simulation.WorldSimulationSystem`
is the pure simulator. The mixin decides *when* the world moves (any action
that advances the calendar) and *how* the world touches the player (seasonal
gather/travel/combat modifiers, the market multiplier on shop prices, learned
rumors surfacing as concrete reveals).
"""
from __future__ import annotations

from typing import Any, Dict

from game.core.constants import EventType

#: Travel consumes this fraction of a year before seasonal scaling (E.4).
BASE_TRAVEL_YEARS = 0.05


class WorldMixin:
    """Advances the world with the calendar and applies world state to play."""

    # -- the world tick -----------------------------------------------------
    def _advance_world_after(self, result: Dict[str, Any], action_key: str) -> Dict[str, Any]:
        """Tick the living world by an action's time cost (E.1/E.2/E.3).

        Errors never consume time. The tick's notable happenings (rank gains,
        rivalries, deaths, sect shifts, price drift, fresh rumors) are folded
        into the result as ``world_tick`` so the UI can narrate them; the last
        report is also kept on the engine for ``WORLD_INFO``.
        """
        if not isinstance(result, dict) or result.get("event") == EventType.ERROR:
            return result
        years = self.lifespan.time_cost(action_key)
        if years <= 0:
            return result
        report = self._world_tick(years)
        if report.get("notable"):
            result["world_tick"] = report
        return result

    def _world_after_result_years(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Tick the world by the years a result reports (e.g. closed-door)."""
        if not isinstance(result, dict) or result.get("event") == EventType.ERROR:
            return result
        try:
            years = float(result.get("years", 0.0))
        except (TypeError, ValueError):
            return result
        if years > 0:
            report = self._world_tick(years)
            if report.get("notable"):
                result["world_tick"] = report
        return result

    def _world_tick(self, years: float) -> Dict[str, Any]:
        """Advance the world by ``years`` and remember the report."""
        season = self.lifespan.season(self.player)
        report = self.world.tick(self._world_state, years, self._world_rng, season)
        self._last_world_report = report
        # E.3: the market drift reached this tick becomes the shop multiplier.
        if report.get("price_multiplier") is not None:
            self.shops.set_market_multiplier(float(report["price_multiplier"]))
        # E.4: the season moved, so the encounter bias moves with it.
        self.event_system.set_combat_bias(
            float(self._season_modifiers().get("combat_bias", 1.0))
        )
        return report

    # -- E.4: seasons acting on play ----------------------------------------
    def _season_modifiers(self) -> Dict[str, float]:
        """The current season's gameplay modifiers (single authority)."""
        return self.world.season_modifiers(self.lifespan.season(self.player))

    def _advance_travel_time(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Seasonal travel time wrapper: age the player, tick the world.

        Kept as a named method (not a lambda in the dispatch table) so save
        snapshots that reference bound handlers keep working.
        """
        if not isinstance(result, dict) or result.get("event") == EventType.ERROR:
            return result
        years = BASE_TRAVEL_YEARS * float(self._season_modifiers().get("travel_years", 1.0))
        self.player.age_years = round(float(self.player.age_years) + years, 4)
        result["travel_years"] = round(years, 4)
        report = self._world_tick(years)
        if report.get("notable"):
            result["world_tick"] = report
        return result

    def _gather_with_seasons(self) -> Dict[str, Any]:
        """Gathering wrapper: yield scales with the season (E.4)."""
        result = self._gather()
        if result.get("event") == EventType.ERROR:
            return result
        yield_mult = float(self._season_modifiers().get("gather_yield", 1.0))
        if yield_mult > 1.0:
            bonus = max(0, int(yield_mult) - 1)
            herb_id = str(result.get("item_id", ""))
            if bonus and herb_id:
                self.inventory.add_item(self.player, herb_id, bonus)
                result["count"] = int(result.get("count", 1)) + bonus
                result["season_bonus"] = bonus
        result["season"] = self.lifespan.season(self.player)
        return result

    # -- E.3: the world market -----------------------------------------------
    def _world_market_multiplier(self) -> float:
        """The simulation-driven part of the price multiplier (1.0 when absent)."""
        market = self._world_state.get("market", {}) if isinstance(self._world_state, dict) else {}
        try:
            return max(0.1, float(market.get("price_multiplier", 1.0)))
        except (TypeError, ValueError):
            return 1.0

    def _shop_price_multiplier(self) -> float:
        """Total shop multiplier: run-seed economy band * live market drift."""
        return float(self.shops.economy_multiplier) * self._world_market_multiplier()

    # -- E.5: rumors ----------------------------------------------------------
    def _reveal_for(self, reveal: Dict[str, Any]) -> Dict[str, Any]:
        """Attach a display name to a rumor reveal's concrete subject."""
        enriched = dict(reveal or {})
        reveal_type = str(enriched.get("type", ""))
        if reveal_type == "sect":
            enriched["name"] = self.world.sect_name(str(enriched.get("id", "")))
        elif reveal_type == "npc":
            enriched["name"] = self.world.npc_display(str(enriched.get("id", "")))
        elif reveal_type == "location":
            location = self.locations.view(str(enriched.get("id", "")))
            enriched["name"] = str(location.get("name", enriched.get("id", "")))
        return enriched

    def _world_rumors(self) -> Dict[str, Any]:
        """List the live rumors (bounded, newest last)."""
        return {
            "event": EventType.WORLD_RUMORS,
            "rumors": self.world.rumors(self._world_state),
            "year": self._world_state.get("year", 0.0),
        }

    def _learn_rumor(self, rumor_id: str) -> Dict[str, Any]:
        """Learn a rumor, revealing its concrete subject (sect/location/npc)."""
        if not rumor_id:
            return {"event": EventType.ERROR, "reason": "NO_RUMOR_SPECIFIED"}
        rumor = self.world.learn_rumor(self._world_state, str(rumor_id))
        if rumor is None:
            return {"event": EventType.ERROR, "reason": "UNKNOWN_RUMOR", "rumor_id": rumor_id}
        reveal = self._reveal_for(dict(rumor.get("reveal") or {}))
        return {
            "event": EventType.RUMOR_LEARNED,
            "rumor": rumor,
            "reveal": reveal,
            "player_message": f"You commit the rumor to memory: {rumor.get('summary', '')}",
        }

    def _rumor_hook_for(self, character_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Attach an unlearned rumor's reveal to a talk result (hearsay in chat)."""
        if not isinstance(result, dict) or result.get("event") == EventType.ERROR:
            return result
        unlearned = [
            rumor for rumor in self.world.rumors(self._world_state)
            if not rumor.get("learned", False)
        ]
        if not unlearned:
            return result
        rumor = unlearned[0]
        learned = self.world.learn_rumor(self._world_state, str(rumor.get("id")))
        if learned is None:
            return result
        result["rumor_learned"] = {
            "rumor": learned,
            "reveal": self._reveal_for(dict(learned.get("reveal") or {})),
            "from_character": str(character_id),
        }
        return result

    # -- world views ------------------------------------------------------------
    def _world_info(self) -> Dict[str, Any]:
        """Full world snapshot: year, season effects, sects, market, rumors."""
        state = self._world_state
        npcs = state.get("npcs", {})
        living = [npc for npc in npcs.values() if npc.get("alive", True)]
        power = state.get("sect_power", {})
        ranking = [
            {"sect_id": sect_id, "name": self.world.sect_name(str(sect_id)), "power": float(value)}
            for sect_id, value in sorted(power.items(), key=lambda item: float(item[1]), reverse=True)
        ]
        return {
            "event": EventType.WORLD_INFO,
            "year": state.get("year", 0.0),
            "season": self.lifespan.season(self.player),
            "season_modifiers": self._season_modifiers(),
            "market_price_multiplier": self._world_market_multiplier(),
            "shop_price_multiplier": round(self._shop_price_multiplier(), 4),
            "cultivators_alive": len(living),
            "cultivators_total": len(npcs),
            "sect_ranking": ranking,
            "rumors": self.world.rumors(state),
            "last_report": self._last_world_report,
        }
