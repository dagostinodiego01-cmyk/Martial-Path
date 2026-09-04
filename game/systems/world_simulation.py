"""Living-world simulation (ROADMAP E.1-E.5).

One pure system evolves the world on the same calendar the player lives on. The
engine calls :meth:`tick` with however many years an action consumed (a rest is
a fraction of a year; closed-door seclusion can be a decade), and the world
moves without the player:

* **E.1 NPC agency** -- NPCs cultivate (rank gains), the strongest clash
  (rivalries shed ranks), and high-realm cultivators die pursuing secret
  realms; sects then fill fallen seats with fresh disciples (succession), so
  mortality thins the world toward an equilibrium instead of sterilising it.
  State-backed (``WorldState``), so it round-trips through saves and is
  observable via relationship/registry changes.
* **E.2 sect simulation** -- sect power follows its members' ranks and slowly
  regresses toward the mean; a 100-year sim visibly reorders the world.
* **E.3 economy** -- market pressure (supply from per-npc wealth, demand from
  living cultivators) nudges the world's price multiplier each tick; shocks
  (wars, disasters) jolt it further. The arc: a young poor world has scarce
  goods (prices climb), a saturated wealthy world floods them (prices fall),
  and mass death (war, tribulation) scarce-ifies them again (prices climb).
* **E.4 seasons acting** -- the season modulates gathering yield, travel, and
  combat-encounter odds; ``modifiers()`` is the single authority the engine
  consults.
* **E.5 rumors** -- world events mint state-backed rumors; a learned rumor
  becomes a concrete reveal (a location, a sect, an event).

Pure logic: no I/O, no UI. Seeded RNG drives every roll so a run replays
exactly.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from game.utils.rng import RNG

SEASONS: tuple[str, ...] = ("Spring", "Summer", "Autumn", "Winter")

#: Per-season gameplay modifiers (E.4). ``gather_yield`` multiplies herbs per
#: gather, ``travel_years`` multiplies travel time, ``combat_bias`` scales the
#: COMBAT weight of the encounter roll, ``npc_progress`` scales the world tick.
SEASON_MODIFIERS: Dict[str, Dict[str, float]] = {
    "Spring": {"gather_yield": 1.0, "travel_years": 1.0, "combat_bias": 1.0, "npc_progress": 1.0},
    "Summer": {"gather_yield": 1.0, "travel_years": 1.0, "combat_bias": 1.1, "npc_progress": 1.1},
    "Autumn": {"gather_yield": 2.0, "travel_years": 1.0, "combat_bias": 1.2, "npc_progress": 1.0},
    "Winter": {"gather_yield": 0.5, "travel_years": 1.5, "combat_bias": 0.8, "npc_progress": 0.7},
}

WORLD_STATE_VERSION = 1

DEFAULT_CONFIG: Dict[str, Any] = {
    "npc_cultivation_chance": 0.35,   # per NPC per year at rank 1
    "npc_progress_slowdown": 0.5,     # higher ranks advance slower (1 + k*(rank-1))
    "npc_rivalry_chance": 0.15,       # strongest pair clashes per year
    "npc_mortality_chance": 0.03,     # high-realm cultivators die per year
    "npc_progress_rank": 1,           # ranks gained per successful cultivation
    "npc_rank_cap": 12,               # the ladder's end; no NPC climbs past it
    "rivalry_loss": 1,                # ranks lost by the clash loser
    "sect_smoothing": 0.1,            # power blend toward recomputed strength
    "sect_base_power": 10.0,          # power a dead/empty sect decays toward
    "economy_reversion": 0.05,        # multiplier relaxes toward target per year
    "economy_sensitivity": 0.002,     # wealth-per-cultivator effect on prices
    "economy_wealth_baseline": 30.0,  # per-capita wealth considered neutral (cap is 60)
    "economy_scarcity_effect": 0.3,   # max price push when cultivators die
    "wealth_gain_per_npc": 1,         # wealth a living NPC accrues per sub-step
    "wealth_cap": 60,                 # saturation so pressure stays bounded
    "rumor_lifetime_years": 6.0,      # unlearned rumors fade after this
    "mortality_min_rank": 8,          # ranks >= this risk death on the road
    "npc_succession_chance": 0.05,    # per dead NPC per year, a sect refills the seat
}


def default_world_state(rng: RNG, npc_ids: Iterable[str]) -> Dict[str, Any]:
    """Build a fresh, seed-derived world state for a new run."""
    state: Dict[str, Any] = {
        "version": WORLD_STATE_VERSION,
        "year": 0.0,
        "npcs": {},
        "sect_power": {},
        "market": {"price_multiplier": 1.0},
        "rumors": [],
        "next_rumor_id": 1,
    }
    for npc_id in npc_ids:
        # A seeded spread of starting ranks (1-3) so the world is born unequal.
        state["npcs"][str(npc_id)] = {
            "rank": int(rng.randint(1, 3)),
            "alive": True,
            "wealth": int(rng.randint(0, 5)),
        }
    return state


class WorldSimulationSystem:
    """Advances the living world one player-calendar tick at a time."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        sect_names: Optional[Dict[str, str]] = None,
        npc_factions: Optional[Dict[str, str]] = None,
        locations: Optional[List[Dict[str, Any]]] = None,
        sect_ids: Optional[List[str]] = None,
    ) -> None:
        merged = dict(DEFAULT_CONFIG)
        merged.update(config or {})
        self._config = merged
        self._sect_names = dict(sect_names or {})
        self._npc_factions = dict(npc_factions or {})
        self._location_ids = [str(loc["id"]) for loc in (locations or []) if loc.get("id")]
        self._sect_ids = [str(entry) for entry in (sect_ids or [])]

    # -- configuration -----------------------------------------------------
    @property
    def config(self) -> Dict[str, Any]:
        return dict(self._config)

    # -- E.4: seasons as real modifiers ------------------------------------
    def season_modifiers(self, season: str) -> Dict[str, float]:
        """Return the gameplay modifiers for ``season`` (defaults for unknowns)."""
        return dict(SEASON_MODIFIERS.get(season, SEASON_MODIFIERS["Spring"]))

    # -- E.1/E.2/E.3: the world tick ----------------------------------------
    def tick(
        self,
        state: Dict[str, Any],
        years: float,
        rng: RNG,
        season: str = "Spring",
    ) -> Dict[str, Any]:
        """Advance the world by ``years`` (fractional); return a tick report.

        The report lists notable happenings (rank gains, clashes, deaths,
        sect shifts, price drift) so the engine can narrate or store them. The
        season scales NPC progress (E.4 acting on E.1).
        """
        report: Dict[str, Any] = {
            "years": float(years),
            "rank_gains": [],
            "rivalries": [],
            "deaths": [],
            "successions": [],
            "sect_shifts": [],
            "price_multiplier": None,
            "rumors": [],
            "notable": False,
        }
        if years <= 0:
            return report
        progress_scale = self.season_modifiers(season).get("npc_progress", 1.0)
        report["season"] = season

        npcs: Dict[str, Dict[str, Any]] = state.setdefault("npcs", {})
        steps = max(1, int(round(float(years) * 4)))  # quarterly sub-steps
        if "base_living" not in state:
            state["base_living"] = sum(1 for npc in npcs.values() if npc.get("alive", True))
        for _ in range(steps):
            step_years = float(years) / steps
            self._tick_npcs(state, npcs, step_years * progress_scale, rng, report)
            self._tick_sects(state, report)
            self._tick_economy(state, npcs, step_years, report)
        state["year"] = round(float(state.get("year", 0.0)) + float(years), 4)
        self._fade_rumors(state, float(years))
        self._maybe_mint_rumor(state, rng, report)
        report["notable"] = bool(
            report["rank_gains"] or report["rivalries"] or report["deaths"]
            or report["successions"] or report["sect_shifts"] or report["rumors"]
        )
        return report

    def _tick_npcs(
        self,
        state: Dict[str, Any],
        npcs: Dict[str, Dict[str, Any]],
        years: float,
        rng: RNG,
        report: Dict[str, Any],
    ) -> None:
        # Succession first: seats refilled this year join the living before the
        # year's cultivation and mortality are resolved (a same-tick death is
        # final until the next tick, so reports stay consistent).
        self._tick_succession(state, npcs, years, rng, report)
        chance = float(self._config["npc_cultivation_chance"]) * years
        slowdown = float(self._config["npc_progress_slowdown"])
        for npc_id, npc in npcs.items():
            if not npc.get("alive", True):
                continue
            # Wealth accrues but saturates: high rank brings diminishing returns
            # (bounded so the economy pressure below stays in a sane band).
            cap = int(self._config["wealth_cap"])
            npc["wealth"] = min(cap, int(npc.get("wealth", 0)) + int(self._config["wealth_gain_per_npc"]))
            # Cultivation slows as realms rise: a rank-1 prodigy advances far
            # faster than a rank-10 elder. This bounds the world's power so a
            # century does not empty it of the living.
            rank = int(npc.get("rank", 1))
            effective = chance / (1.0 + slowdown * (rank - 1))
            # The ladder ends: past the cap, elders refine rather than climb.
            if rank < int(self._config["npc_rank_cap"]) and rng.chance(effective):
                npc["rank"] = rank + int(self._config["npc_progress_rank"])
                report["rank_gains"].append(npc_id)

        living = [(nid, npc) for nid, npc in npcs.items() if npc.get("alive", True)]
        # Rivalries: the two strongest cultivators may clash (E.1).
        if len(living) >= 2 and rng.chance(float(self._config["npc_rivalry_chance"]) * years):
            living.sort(key=lambda pair: int(pair[1].get("rank", 1)), reverse=True)
            (a_id, _), (b_id, b) = living[0], living[1]
            loser_id = rng.choice([a_id, b_id])
            npcs[loser_id]["rank"] = max(1, int(npcs[loser_id].get("rank", 1)) - int(self._config["rivalry_loss"]))
            report["rivalries"].append({"winner": b_id if loser_id == a_id else a_id, "loser": loser_id})
        # Mortality: senior cultivators die pursuing secret realms (E.1).
        for npc_id, npc in living:
            if int(npc.get("rank", 1)) >= int(self._config["mortality_min_rank"]):
                if rng.chance(float(self._config["npc_mortality_chance"]) * years):
                    npc["alive"] = False
                    report["deaths"].append(npc_id)

    def _tick_succession(
        self,
        state: Dict[str, Any],
        npcs: Dict[str, Dict[str, Any]],
        years: float,
        rng: RNG,
        report: Dict[str, Any],
    ) -> None:
        """Sects refill fallen seats: the dead are succeeded by new disciples.

        The roster is fixed (ids are lineage seats, not single lifetimes), so a
        succeeded NPC returns at rank 1 with a fresh purse. This gives mortality
        a counterbalance: the world thins toward an equilibrium rather than to
        nothing, and sects recover instead of fading to ruins.
        """
        chance = float(self._config.get("npc_succession_chance", 0.0)) * years
        if chance <= 0:
            return
        for npc_id, npc in npcs.items():
            if npc.get("alive", True):
                continue
            if rng.chance(chance):
                npc["alive"] = True
                npc["rank"] = 1
                npc["wealth"] = int(rng.randint(0, 2))
                report["successions"].append(npc_id)

    def _tick_sects(self, state: Dict[str, Any], report: Dict[str, Any]) -> None:
        """Sect power tracks its living members' ranks, smoothed (E.2).

        Power is *recomputed* from the roster each step (so it is bounded by the
        actual world) and blended with the previous value, which makes rises and
        falls gradual and visible in the tick report.
        """
        sect_power: Dict[str, float] = state.setdefault("sect_power", {})
        npcs = state.get("npcs", {})
        raw: Dict[str, float] = {}
        for npc_id, npc in npcs.items():
            if not npc.get("alive", True):
                continue
            faction = self._npc_factions.get(npc_id)
            if faction:
                raw[faction] = raw.get(faction, 10.0) + int(npc.get("rank", 1))
        blend = float(self._config["sect_smoothing"])
        base = float(self._config["sect_base_power"])
        for sect_id, strength in raw.items():
            previous = float(sect_power.get(sect_id, base))
            after = previous + (strength - previous) * blend
            if abs(after - previous) >= 0.2:
                report["sect_shifts"].append({"sect_id": sect_id, "delta": round(after - previous, 3)})
            sect_power[sect_id] = round(after, 4)
        # Sects with no living members fade toward the base: ruins lose power.
        for sect_id in list(sect_power.keys()):
            if sect_id in raw:
                continue
            previous = float(sect_power[sect_id])
            after = previous + (base - previous) * blend
            if abs(after - previous) >= 0.2:
                report["sect_shifts"].append({"sect_id": sect_id, "delta": round(after - previous, 3)})
            sect_power[sect_id] = round(after, 4)

    def _tick_economy(
        self,
        state: Dict[str, Any],
        npcs: Dict[str, Any],
        years: float,
        report: Dict[str, Any],
    ) -> None:
        """Market pressure nudges the price multiplier each tick (E.3).

        Two bounded pressures:

        * wealth per living cultivator -- rich markets mean abundant supply,
          pushing prices down;
        * deaths of cultivators -- fewer producers, pushing prices up.

        The multiplier relaxes toward that target (never instant) and is clamped
        to a sane band so long runs cannot drift to absurdity.
        """
        market: Dict[str, Any] = state.setdefault("market", {"price_multiplier": 1.0})
        living = [npc for npc in npcs.values() if npc.get("alive", True)]
        avg_wealth = (sum(int(npc.get("wealth", 0)) for npc in living) / len(living)) if living else 0.0
        base_living = max(1, int(state.get("base_living", len(living) or 1)))
        scarcity = (base_living - len(living)) / base_living  # 0 .. 1
        target = 1.0
        target += (float(self._config["economy_wealth_baseline"]) - avg_wealth) * float(self._config["economy_sensitivity"])
        target += scarcity * float(self._config["economy_scarcity_effect"])
        target = max(0.7, min(1.4, target))
        current = float(market.get("price_multiplier", 1.0))
        reversion = 1.0 - float(self._config["economy_reversion"]) * years
        after = current + (target - current) * (1.0 - reversion if reversion > 0 else 1.0)
        after = max(0.7, min(1.4, after))
        market["price_multiplier"] = round(after, 4)
        report["price_multiplier"] = market["price_multiplier"]

    # -- E.5: rumors ---------------------------------------------------------
    def mint_rumor(self, state: Dict[str, Any], rng: RNG, kind: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create a state-backed rumor about the world; return it (or ``None``)."""
        return self._build_rumor(state, rng, kind or rng.choice(("death", "dominance", "market", "realm_discovery")))

    def _maybe_mint_rumor(self, state: Dict[str, Any], rng: RNG, report: Dict[str, Any]) -> None:
        """Mint one rumor per tick if the world has material to talk about."""
        material: List[str] = []
        for death in report.get("deaths", []):
            material.append("death")
        multiplier = report.get("price_multiplier")
        if multiplier is not None and abs(float(multiplier) - 1.0) > 0.01:
            material.append("market")  # only talk when prices actually moved
        for shift in report.get("sect_shifts", []):
            material.append("dominance")
        if not material:
            return
        if not rng.chance(0.6):
            return
        kind = rng.choice(material)
        rumor = self._build_rumor(state, rng, kind)
        if rumor is not None:
            state.setdefault("rumors", []).append(rumor)
            report["rumors"].append(rumor)

    def _build_rumor(self, state: Dict[str, Any], rng: RNG, kind: str) -> Optional[Dict[str, Any]]:
        rumors: List[Dict[str, Any]] = state.setdefault("rumors", [])
        rumor_id = str(int(state.get("next_rumor_id", 1)))
        state["next_rumor_id"] = int(state.get("next_rumor_id", 1)) + 1
        entry: Dict[str, Any] = {
            "id": rumor_id,
            "kind": kind,
            "learned": False,
            "age_years": 0.0,
        }
        if kind == "death":
            dead = [nid for nid, npc in state.get("npcs", {}).items() if not npc.get("alive", True)]
            if not dead:
                return None
            entry["subject_id"] = str(rng.choice(dead))
            entry["summary"] = f"{self._npc_display(entry['subject_id'])} has fallen."
            entry["reveal"] = {"type": "npc", "id": entry["subject_id"]}
        elif kind == "dominance":
            power = state.get("sect_power", {})
            if not power:
                return None
            top = max(power, key=lambda sect_id: float(power[sect_id]))
            entry["subject_id"] = top
            entry["summary"] = f"The {self._sect_name(top)} rises above all other sects."
            entry["reveal"] = {"type": "sect", "id": top}
        elif kind == "market":
            multiplier = float(state.get("market", {}).get("price_multiplier", 1.0))
            entry["subject_id"] = ""
            if multiplier >= 1.05:
                entry["summary"] = "Goods grow scarce; market prices climb."
            elif multiplier <= 0.95:
                entry["summary"] = "Markets flood with goods; prices fall."
            else:
                entry["summary"] = "The markets hold steady this season."
            entry["reveal"] = {"type": "market", "id": "price_multiplier"}
        else:  # realm_discovery
            if not self._location_ids:
                return None
            location_id = rng.choice(self._location_ids)
            entry["subject_id"] = location_id
            entry["summary"] = f"A hidden realm is said to open near {self._location_name(location_id)}."
            entry["reveal"] = {"type": "location", "id": location_id}
        rumors.append(entry)
        return dict(entry)

    def learn_rumor(self, state: Dict[str, Any], rumor_id: str) -> Optional[Dict[str, Any]]:
        """Mark a rumor learned and return its concrete reveal (E.5)."""
        for rumor in state.get("rumors", []):
            if str(rumor.get("id")) == str(rumor_id) and not rumor.get("learned", False):
                rumor["learned"] = True
                return dict(rumor)
        return None

    def rumors(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return the live rumor list (bounded, most recent last)."""
        return [dict(rumor) for rumor in state.get("rumors", [])][-20:]

    def _fade_rumors(self, state: Dict[str, Any], years: float) -> None:
        lifetime = float(self._config["rumor_lifetime_years"])
        rumors: List[Dict[str, Any]] = state.get("rumors", [])
        for rumor in rumors:
            rumor["age_years"] = round(float(rumor.get("age_years", 0.0)) + years, 4)
        state["rumors"] = [
            rumor for rumor in rumors
            if rumor.get("learned", False) or float(rumor.get("age_years", 0.0)) < lifetime
        ][-20:]

    # -- display helpers -----------------------------------------------------
    def sect_name(self, sect_id: str) -> str:
        """Public display name for a sect id (falls back to prettified id)."""
        return self._sect_name(str(sect_id))

    def npc_display(self, npc_id: str) -> str:
        """Public display name for an NPC id (falls back to prettified id)."""
        return self._npc_display(str(npc_id))

    def _npc_display(self, npc_id: str) -> str:
        return str(npc_id).replace("_", " ").title()

    def _sect_name(self, sect_id: str) -> str:
        return self._sect_names.get(sect_id, self._npc_display(sect_id))

    def _location_name(self, location_id: str) -> str:
        return self._npc_display(location_id)
