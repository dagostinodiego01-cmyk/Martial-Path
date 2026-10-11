"""Choice-driven exploration encounters.

Exploration used to *resolve* a weighted roll: a fight started, a pill appeared,
a spring healed you. This system turns the same roll into a **decision**. It
builds a pending encounter from an exploration descriptor and exposes the
choices the situation actually offers -- fight, talk, sneak, pay, observe, walk
away -- together with the reason any of them is withheld.

The split of responsibilities mirrors :mod:`game.systems.event_system`:

* this system *selects* content and *rolls* the outcomes (pure decisions, no
  state changes);
* :class:`~game.core.engine.encounters.EncountersMixin` *applies* them (spends
  coin, deals hazard damage, spawns the formation, starts combat).

Nothing here touches UI or formats prose; every outcome carries a ``verb`` the
engine renders through the narrative system.

Encounter shapes by kind:

* ``combat``  -- a hostile scene, optionally an **ambush** (the foes strike
  first) and optionally a **formation** (up to ``max_extra_foes`` extra foes).
  Embedded hazards punish fighting in bad ground -- unless the player spent a
  turn *observing*, in which case the hazard bites the foes instead.
* ``loot``    -- a find that may be a **trap**; examining it first makes taking
  it safe.
* ``special`` -- a site of power; studying it reveals what accepting will do.
* ``hazard``  -- the land itself; push through, read a safe path, or walk away.

Two rules keep the opening fair (F.1), and both are data-tunable under
``funnel`` in ``data/encounters.json``:

* **the funnel** -- while the player is still in the opening story band, a
  hostile scene never fields a foe heavier than the player's own fighting
  weight: the drawn foe is swapped for something the pool offers in band, or
  for the lightest thing the land has. The wilds still bite, but the first
  fights are ones the player can answer;
* **the mercy rule** -- in that same band an encounter is never an ambush and
  never carries embedded hazard ground, borrowing the hazard rule that damage
  never kills (it floors at 1 HP and hands the wound to the next fight).

A hazard or trap that did bite the player is remembered and named in the *next*
combat encounter's text and choice line (E.5), so the consequence of the ground
is legible where it matters instead of only in the HP number.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from game.core.constants import EventType
from game.models.player import Player
from game.utils.rng import RNG
from game.utils.text import with_article

#: Encounter kinds (also the ``kind`` field on every encounter payload).
COMBAT = "combat"
LOOT = "loot"
SPECIAL = "special"
HAZARD = "hazard"

#: The canonical choice vocabulary. Encounter kinds each order their own
#: options (see the ``_*_options`` builders); this tuple is the shared spelling
#: of every choice id so callers and tests can assert against one list.
CHOICE_ORDER = (
    "fight",
    "talk",
    "sneak",
    "pay",
    "observe",
    "take",
    "examine",
    "accept",
    "study",
    "push",
    "defuse",
    "withdraw",
    "leave",
    "decline",
    "move_on",
)

DEFAULT_OPTIONS = {
    "fight": {"label": "Fight", "hint": "Meet them blade to blade."},
    "talk": {"label": "Talk", "hint": "Try words before blows."},
    "sneak": {"label": "Sneak", "hint": "Slip past unseen, if the ground allows it."},
    "pay": {"label": "Pay Toll", "hint": "Buy passage with coin."},
    "observe": {"label": "Observe", "hint": "Study the scene first."},
    "withdraw": {"label": "Withdraw", "hint": "Back away and leave them to it."},
    "take": {"label": "Take It", "hint": "Reach for the find."},
    "examine": {"label": "Examine", "hint": "Study the find before you touch it."},
    "leave": {"label": "Leave It", "hint": "Walk on. Some gifts are bait."},
    "accept": {"label": "Accept", "hint": "Open yourself to what waits here."},
    "study": {"label": "Study", "hint": "Learn what you can before you commit."},
    "decline": {"label": "Decline", "hint": "Refuse the offer and move on."},
    "push": {"label": "Push Through", "hint": "Endure it and keep walking."},
    "defuse": {"label": "Find a Way", "hint": "Spend the time to read a safe path."},
    "move_on": {"label": "Move On", "hint": "Continue your journey."},
}

#: Threat bands, on the same scale as :func:`foe_power`. The engine's encounter
#: view labels a foe with these; a test keeps the two tables in lockstep.
THREAT_BANDS: Tuple[Tuple[float, str], ...] = ((0.6, "Low"), (1.0, "Moderate"), (1.5, "High"))

#: What each choice stakes, as a format string over the numbers the encounter
#: already knows (E.4): what it risks, or what it gives up. ``data/encounters.json``
#: overrides any entry under ``stakes``. A choice that carries a ``chance`` has
#: its percentage rendered by the frontend as its own badge, so these lines leave
#: that number out rather than print it twice.
STAKE_FORMATS: Dict[str, str] = {
    "fight": "Fight - {threat} odds: {foe_power} against your {player_power}.",
    "talk": "Talk - bring them around, or hand them the first blow.",
    "pay": "Pay Toll - coin now rather than blood later.",
    "sneak": "Sneak - slip past, or start the fight on their terms.",
    "observe": "Observe - banks {insight} insight; {provoke}% it provokes them instead.",
    "examine": "Examine - spends the turn and reads the find before your hand moves.",
    "study": "Study - spends the turn, and sharpens the odds of whatever follows.",
    "push": "Push Through - cross clean, or the ground takes about {damage}.",
    "defuse": "Find a Way - read it right and it pays; misread it and lose about {damage}.",
    "withdraw_ambush": "Withdraw - get clear, or they strike first.",
    "take": "Take It - roughly {trap_chance}% of finds like this are warded.",
    "take_revealed": "Take It - you have read the find; your hand is sure.",
    "accept": "Accept - {effect}.",
    "accept_unread": "Accept - you do not yet know what it will do.",
    "withdraw_combat": "Withdraw - they keep the road, and you keep your blood.",
    "leave_loot": "Leave It - the find stays where it lies, and its secret with it.",
    "decline_special": "Decline - you walk away from what waits here.",
    "withdraw_hazard": "Withdraw - you take the long way round and give up what this ground pays.",
}

#: The opening-band funnel (F.1). While ``player.max_story_tier`` is below
#: ``max_story_tier``, a combat scene never leads with a foe above
#: ``lead_ceiling`` times the player's power, pack members are drawn from the
#: same band, and ambushes and embedded hazards are withheld.
FUNNEL_DEFAULTS: Dict[str, Any] = {
    "max_story_tier": 2,
    "lead_ceiling": 1.0,
    "pack_entry_ceiling": 0.6,
    "no_ambush": True,
    "no_hazard": True,
    "note": (
        "The first-run funnel: no hostile scene above the player's weight in the "
        "opening story band, no ambush and no embedded hazard there. See the "
        "module docstring; hazards and traps still never kill."
    ),
}

# Scenario defaults, overridden wholesale by ``data/encounters.json``. Small
# tables that only exist so a partial/missing data file still yields a sane,
# playable encounter instead of an empty prompt.
DEFAULTS: Dict[str, Any] = {
    "parley": {
        "base_chance": 0.65, "power_penalty": 0.35, "comprehension_bonus": 0.01,
        "reputation_bonus": 0.012, "min_chance": 0.05, "max_chance": 0.95,
        "success_exp_ratio": 0.5, "success_reputation": 1, "offend_ambush_chance": 0.35,
    },
    "sneak": {
        "base_chance": 0.6, "power_penalty": 0.4, "comprehension_bonus": 0.015,
        "min_chance": 0.05, "max_chance": 0.95, "cache_chance": 0.35, "escape_exp": 3,
    },
    "bribe": {
        "currency": "gold", "base_chance": 0.75, "power_penalty": 0.25,
        "min_chance": 0.05, "max_chance": 0.95, "power_per_coin": 8,
        "min_cost": 5, "max_cost": 300,
    },
    "observe": {"insight_base": 1, "insight_per_comprehension": 6, "insight_cap": 6, "provoke_chance": 0.22},
    "ambush": {"chance_by_danger": [0.0, 0.06, 0.12, 0.18, 0.24, 0.3, 0.34, 0.38, 0.42, 0.46, 0.5], "strike_multiplier": 1.0},
    "formation": {
        "chance_by_danger": [0.0, 0.1, 0.18, 0.24, 0.3, 0.34, 0.38, 0.42, 0.46, 0.5, 0.54],
        "max_extra_foes": 2, "pack_stat_scale": 0.6, "pack_exp_ratio": 0.5,
        "pack_loot_ratio": 0.35, "pack_press_multiplier": 0.5, "max_pack_presses": 2,
        #: Per-danger ceiling on ``pack_stat_scale``: a pack in the shallow,
        #: busy ground hits softer than one in the deep (F.1).
        "pack_stat_scale_ceiling": [0.5, 0.5, 0.5, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6],
    },
    "encounter": {"hazard_chance_by_danger": [0.0, 0.08, 0.12, 0.16, 0.2, 0.24, 0.28, 0.32, 0.36, 0.4, 0.44], "trapped_loot_chance": 0.3},
}


def foe_power(enemy: Any) -> float:
    """Return a foe's single-number threat: HP plus weighted offence/defence.

    Mirrors the threat preview the engine shows before a fight so a choice's
    odds and the displayed danger tier agree with each other.
    """
    hp = float(getattr(enemy, "max_hp", None) or _value(enemy, "hp") or 0.0)
    attack = float(getattr(enemy, "attack", None) or _value(enemy, "attack") or 0.0)
    defense = float(getattr(enemy, "defense", None) or _value(enemy, "defense") or 0.0)
    return hp + attack * 5.0 + defense * 3.0


def threat_tier(foe_power: float, player_power: float) -> str:
    """Classify a foe relative to the player: Low, Moderate, High, or Deadly.

    The system-layer spelling of the band the engine shows on the encounter
    card; :meth:`game.core.engine.encounters.EncountersMixin._threat_tier`
    renders it. A test asserts the two agree, so the odds a choice quotes and
    the threat the preview shows can never drift apart.
    """
    ratio = foe_power / player_power if player_power > 0 else 1.0
    for ceiling, name in THREAT_BANDS:
        if ratio < ceiling:
            return name
    return "Deadly"


def _value(entry: Any, key: str) -> Any:
    """Read ``key`` from a mapping or object, returning ``None`` when absent."""
    if isinstance(entry, dict):
        return entry.get(key)
    return getattr(entry, key, None)


class EncounterSystem:
    """Builds pending exploration encounters and rolls the outcome of choices."""

    def __init__(
        self,
        data: Optional[Dict[str, Any]],
        enemy_templates: Optional[List[Dict[str, Any]]],
        rng: RNG,
    ) -> None:
        self._data = data or {}
        self._enemies = {template["id"]: template for template in (enemy_templates or []) if template.get("id")}
        self._rng = rng
        mindless = self._data.get("mindless") or {}
        # Derived, not hand-listed: a foe with a Dao or an essence realm is a
        # person, as is anyone named in ``people`` (humanoids who never
        # cultivated). Everything else is wildlife -- and any enemy added later
        # inherits the right answer for free.
        self._people = {str(enemy_id) for enemy_id in (mindless.get("people") or [])}
        self._mindless_overrides = {str(key): bool(value) for key, value in (mindless.get("overrides") or {}).items()}
        self._mindless_ids = {str(enemy_id) for enemy_id in (mindless.get("ids") or [])}
        # The danger of the encounter most recently built. ``_spawn_formation``
        # asks the system for its pack config with no encounter argument, so the
        # danger that config is derived from has to be remembered rather than
        # passed; the spawn always follows its own build in the same action.
        self._built_danger = 10
        # A hazard or trap that took HP from the player, held until the next
        # fight can name it (E.5).
        self._wound: Optional[Dict[str, Any]] = None

    # -- config accessors -------------------------------------------------
    def _config(self, section: str) -> Dict[str, Any]:
        """Return a config section merged over its defaults."""
        merged = dict(DEFAULTS.get(section, {}))
        merged.update(self._data.get(section) or {})
        return merged

    def option_meta(self, choice_id: str) -> Dict[str, str]:
        """Return the UI label/hint for a choice id."""
        entry = dict(DEFAULT_OPTIONS.get(choice_id, {"label": choice_id.title(), "hint": ""}))
        entry.update((self._data.get("options") or {}).get(choice_id) or {})
        return entry

    def stake_line(self, key: str, **values: Any) -> str:
        """Format a staked choice's line (E.4): what it risks, or what it gives up.

        Empty when the copy for ``key`` is missing, so a partial data file
        degrades to the plain hint rather than printing a format error.
        """
        template = str((self._data.get("stakes") or {}).get(key) or STAKE_FORMATS.get(key) or "")
        if not template:
            return ""
        try:
            return template.format(**values)
        except (KeyError, IndexError):
            return ""

    def _funnel(self) -> Dict[str, Any]:
        """Return the opening-band funnel config merged over its defaults."""
        merged = dict(FUNNEL_DEFAULTS)
        merged.update(self._data.get("funnel") or {})
        return merged

    def in_opening_band(self, player: Player) -> bool:
        """True while the player is still inside the first-run funnel (F.1)."""
        ceiling = int(self._funnel().get("max_story_tier", 2) or 2)
        return int(getattr(player, "max_story_tier", 1) or 1) < ceiling

    def _chance_at_danger(self, table: List[float], danger: int) -> float:
        """Index a danger-keyed probability table, clamped to its ends."""
        if not table:
            return 0.0
        return float(table[max(0, min(int(danger), len(table) - 1))])

    def _hazard_catalogue(self) -> List[Dict[str, Any]]:
        return [entry for entry in (self._data.get("hazards") or []) if isinstance(entry, dict) and entry.get("id")]

    def _trap_catalogue(self) -> List[Dict[str, Any]]:
        return [entry for entry in (self._data.get("traps") or []) if isinstance(entry, dict) and entry.get("id")]

    def is_mindless(self, enemy_id: str) -> bool:
        """Return ``True`` when a foe cannot be reasoned with or paid off."""
        if enemy_id in self._mindless_overrides:
            return self._mindless_overrides[enemy_id]
        if enemy_id in self._people:
            return False
        template = self._enemies.get(enemy_id)
        if template is None:
            # An id outside the catalogue (a named character's duel entry): fall
            # back to the legacy explicit list rather than guessing.
            return enemy_id in self._mindless_ids
        return not (template.get("essence_realm_id") or template.get("dao_id"))

    # -- encounter construction ------------------------------------------
    def build(
        self,
        descriptor: Dict[str, Any],
        player: Player,
        *,
        danger: int,
        player_power: float,
        pool: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Build the pending encounter a descriptor describes, or ``None``.

        ``None`` means the descriptor carries no decision (a quiet wander, a
        location with nothing to fight over) and the caller should resolve it as
        it always did.
        """
        self._built_danger = int(danger)
        kind = descriptor.get("event")
        if kind == EventType.COMBAT:
            return self._build_combat(descriptor, player, danger, player_power, pool or {})
        if kind == EventType.LOOT:
            return self._build_loot(descriptor, player, danger)
        if kind == EventType.SPECIAL:
            return self._build_special(descriptor, player)
        if kind == EventType.HAZARD:
            return self._build_hazard(descriptor, player, danger, pool or {})
        return None

    def _build_combat(
        self,
        descriptor: Dict[str, Any],
        player: Player,
        danger: int,
        player_power: float,
        pool: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        leader_id = str(descriptor.get("enemy_id", ""))
        if leader_id not in self._enemies:
            return None
        funnel = self._funnel()
        opening = self.in_opening_band(player)
        text = str(descriptor.get("text", ""))
        # F.1: in the opening band the scene is handed a foe the player can
        # actually answer. The drawn foe is kept whenever it is already in
        # band, so the pool's own variety survives.
        if opening:
            leader_id, text = self._funnel_leader(leader_id, text, pool, player_power, funnel)
        formation = self._config("formation")
        ambush = self._config("ambush")
        foes = [leader_id]
        # Formations: extra foes drawn from the same location pool, weaker than
        # the leader so a pack is a harder fight, not three separate fights.
        if len(pool.get("combat") or []) > 0 and self._rng.chance(self._chance_at_danger(formation["chance_by_danger"], danger)):
            extra = self._roll_formation_size(int(formation.get("max_extra_foes", 2)))
            ceiling = player_power * float(funnel.get("pack_entry_ceiling", 0.6)) if opening else None
            candidates = [
                entry["enemy_id"]
                for entry in pool["combat"]
                if entry.get("enemy_id") in self._enemies
                and (ceiling is None or foe_power(self._enemies[str(entry["enemy_id"])]) <= ceiling)
            ]
            for _ in range(extra):
                if not candidates:
                    break
                foes.append(str(self._rng.choice(candidates)))
        # The mercy rule (F.1): the opening band is never ambushed, and its
        # ground never turns on a player who has not learned to read it yet.
        mercy = bool(opening and funnel.get("no_ambush", True))
        is_ambush = (not mercy) and self._rng.chance(self._chance_at_danger(ambush["chance_by_danger"], danger))
        hazard = None
        if not (opening and funnel.get("no_hazard", True)) and self._rng.chance(
            self._chance_at_danger(self._config("encounter")["hazard_chance_by_danger"], danger)
        ):
            # Fighting in bad ground: the hazard is revealed to the observant, and
            # only bites whoever did not take the time to read it.
            hazard = self._roll_hazard(danger, pool)
        leader = self._enemies[leader_id]
        # E.5: whatever the ground already took is named where it matters.
        wound = self._consume_wound(player)
        if wound is not None:
            text = f"{text} {self.wound_line(wound, player)}".strip()
        return {
            "kind": COMBAT,
            "scene_verb": "encounter_ambush" if is_ambush else "encounter_combat",
            "title": "Ambush" if is_ambush else ("Pack" if len(foes) > 1 else "Hostile Encounter"),
            "text": text,
            "danger": int(danger),
            "ambush": is_ambush,
            "foes": foes,
            "hazard": hazard,
            "loot": None,
            "special": None,
            "observed": False,
            "resolved": False,
            "mercy": bool(opening),
            "wound": wound,
            "context": {"enemy": str(leader.get("name", leader_id))},
            # A clean sneak past a foe can turn up their unattended cache.
            "_pool_loot": list(pool.get("loot") or []),
        }

    def _funnel_leader(
        self,
        leader_id: str,
        text: str,
        pool: Dict[str, Any],
        player_power: float,
        funnel: Dict[str, Any],
    ) -> Tuple[str, str]:
        """Pick the foe an opening-band scene may field (F.1).

        The drawn foe is kept when it is already at or below the player's own
        fighting weight. Otherwise the scene draws again -- from the same
        location pool, so the land keeps its identity -- among the entries in
        band. If the pool offers none, the lightest thing it has is sent: the
        player still meets what lives here, just never the worst of it first.
        """
        ceiling = player_power * float(funnel.get("lead_ceiling", 1.0))
        drawn = self._enemies.get(leader_id, {})
        if foe_power(drawn) <= ceiling:
            return leader_id, text
        entries = [
            entry
            for entry in (pool.get("combat") or [])
            if entry.get("enemy_id") in self._enemies
        ]
        if not entries:
            return leader_id, text
        in_band = [entry for entry in entries if foe_power(self._enemies[str(entry["enemy_id"])]) <= ceiling]
        if in_band:
            pick = str(
                self._rng.weighted_choice(
                    [str(entry["enemy_id"]) for entry in in_band],
                    [entry.get("weight", 1) for entry in in_band],
                )
            )
        else:
            pick = str(
                min(entries, key=lambda entry: (foe_power(self._enemies[str(entry["enemy_id"])]), str(entry["enemy_id"])))["enemy_id"]
            )
        if pick == leader_id:
            return leader_id, text
        return pick, self._retarget_text(text, leader_id, pick)

    def _retarget_text(self, text: str, old_id: str, new_id: str) -> str:
        """Rewrite a combat descriptor's prose when its foe is substituted.

        The descriptor is written by the event system over the foe it drew, so a
        substituted foe needs the sentence re-pointed or the player reads the
        wrong name. The name is swapped in place when it appears; otherwise the
        event system's own sentence shape is appended.
        """
        old_name = str(self._enemies.get(old_id, {}).get("name", ""))
        new_name = str(self._enemies.get(new_id, {}).get("name", new_id))
        if old_name and with_article(old_name) in text:
            return text.replace(with_article(old_name), with_article(new_name))
        if old_name and old_name in text:
            return text.replace(old_name, new_name)
        return f"{text} {with_article(new_name)} lunges from the shadows!".strip()

    def _roll_formation_size(self, max_extra: int) -> int:
        """Pick how many extra foes join: one usually, more rarely."""
        if max_extra <= 0:
            return 0
        if max_extra == 1:
            return 1
        return 1 + (1 if self._rng.chance(0.35) else 0)

    def _build_loot(self, descriptor: Dict[str, Any], player: Player, danger: int) -> Dict[str, Any]:
        item_id = str(descriptor.get("item_id", ""))
        trapped = self._rng.chance(float(self._config("encounter").get("trapped_loot_chance", 0.3)))
        trap = self._roll_trap(danger) if trapped else None
        return {
            "kind": LOOT,
            "scene_verb": "encounter_loot",
            "title": "A Find on the Path",
            "text": "",
            "danger": int(danger),
            "ambush": False,
            "foes": [],
            "hazard": None,
            "loot": {
                "item_id": item_id,
                "count": int(descriptor.get("count", 1) or 1),
                "trap": trap,
                "revealed": False,
            },
            "special": None,
            "observed": False,
            "resolved": False,
            "context": {},
        }

    def _build_special(self, descriptor: Dict[str, Any], player: Player) -> Dict[str, Any]:
        return {
            "kind": SPECIAL,
            "scene_verb": "encounter_special",
            "title": "A Place of Power",
            "text": str(descriptor.get("text", "")),
            "danger": 0,
            "ambush": False,
            "foes": [],
            "hazard": None,
            "loot": None,
            "special": {
                "special_id": descriptor.get("special_id"),
                "text": str(descriptor.get("text", "")),
                "effect": dict(descriptor.get("effect") or {}),
                "revealed": False,
            },
            "observed": False,
            "resolved": False,
            "context": {},
        }

    def _build_hazard(self, descriptor: Dict[str, Any], player: Player, danger: int, pool: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        hazard = self._roll_hazard(danger, pool, requested_id=str(descriptor.get("hazard_id", "")))
        if hazard is None:
            return None
        return {
            "kind": HAZARD,
            "scene_verb": "encounter_hazard",
            "title": str(hazard.get("name", "Perilous Ground")),
            "text": str(hazard.get("text", "")),
            "danger": int(danger),
            "ambush": False,
            "foes": [],
            "hazard": hazard,
            "loot": None,
            "special": None,
            "observed": False,
            "resolved": False,
            "context": {},
        }

    def _roll_hazard(self, danger: int, pool: Dict[str, Any], requested_id: str = "") -> Optional[Dict[str, Any]]:
        """Draw a hazard, preferring the location's own list when it declares one."""
        catalogue = self._hazard_catalogue()
        if requested_id:
            for entry in catalogue:
                if entry.get("id") == requested_id:
                    return self._hazard_entry(entry, danger)
        scoped = [entry.get("hazard_id") for entry in (pool.get("hazards") or []) if entry.get("hazard_id")]
        if scoped:
            by_id = {entry["id"]: entry for entry in catalogue}
            choices = [by_id[hazard_id] for hazard_id in scoped if hazard_id in by_id]
            if choices:
                return self._hazard_entry(self._rng.choice(choices), danger)
        eligible = [entry for entry in catalogue if int(entry.get("min_danger", 0)) <= int(danger)]
        if not eligible:
            return None
        return self._hazard_entry(self._rng.choice(eligible), danger)

    def _hazard_entry(self, entry: Dict[str, Any], danger: int) -> Dict[str, Any]:
        """Scale a hazard's effect and rewards to the area's danger."""
        def scaled(block: Dict[str, Any], key: str) -> Dict[str, Any]:
            scaled_block = {k: v for k, v in block.items() if k != "per_danger"}
            if key in scaled_block:
                scaled_block[key] = self._scale_value(float(scaled_block[key]), block.get("per_danger", 0.0), danger)
            return scaled_block

        return {
            "id": entry["id"],
            "name": str(entry.get("name", entry["id"])),
            "text": str(entry.get("text", "")),
            "revealed": False,
            "neutralized": False,
            "studied": False,
            "effect": scaled(entry.get("effect") or {}, "magnitude"),
            "reward": scaled(entry.get("reward") or {}, "exp"),
            "defuse_reward": scaled(entry.get("defuse_reward") or {}, "exp"),
            "push_base_chance": float(entry.get("push_base_chance", 0.5)),
            "defuse_base_chance": float(entry.get("defuse_base_chance", 0.45)),
            "comprehension_bonus": float(entry.get("comprehension_bonus", 0.015)),
        }

    def _roll_trap(self, danger: int) -> Optional[Dict[str, Any]]:
        catalogue = self._trap_catalogue()
        if not catalogue:
            return None
        entry = self._rng.choice(catalogue)
        effect = dict(entry.get("effect") or {})
        if "magnitude" in effect:
            effect["magnitude"] = self._scale_value(float(effect["magnitude"]), effect.get("per_danger", 0.0), danger)
        effect.pop("per_danger", None)
        return {
            "id": entry["id"],
            "name": str(entry.get("name", entry["id"])),
            "text": str(entry.get("text", "")),
            "effect": effect,
            "revealed": False,
        }

    @staticmethod
    def _scale_value(base: float, per_danger: Any, danger: int) -> int:
        """Scale a magnitude/reward by danger: ``base * (1 + per_danger * danger)``."""
        return max(1, int(round(base * (1.0 + float(per_danger or 0.0) * int(danger)))))

    # -- options ----------------------------------------------------------
    def options(self, encounter: Dict[str, Any], player: Player, player_power: float) -> List[Dict[str, Any]]:
        """Return every choice the encounter offers, with withheld ones explained."""
        builders = {
            COMBAT: self._combat_options,
            LOOT: self._loot_options,
            SPECIAL: self._special_options,
            HAZARD: self._hazard_options,
        }
        builder = builders.get(encounter.get("kind"))
        if builder is None:
            return []
        # Each builder returns its choices in the order that kind wants them read
        # (the decisive action first, the ways out last); ``CHOICE_ORDER`` is the
        # canonical vocabulary, not a display sort.
        return builder(encounter, player, player_power)

    def _option(
        self,
        choice_id: str,
        *,
        available: bool = True,
        reason: str = "",
        reason_code: str = "",
        cost: Optional[Dict[str, int]] = None,
        stakes: str = "",
        **extra: Any,
    ) -> Dict[str, Any]:
        """Build one choice card.

        ``stakes`` (E.4) replaces the plain hint with a line carrying the odds
        the choice actually runs on, or the price of giving it up; ``extra``
        carries the same numbers structurally (``odds``, ``forfeit``, ...) for a
        frontend that wants to lay them out itself.
        """
        meta = self.option_meta(choice_id)
        entry: Dict[str, Any] = {
            "choice_id": choice_id,
            "label": meta["label"],
            "hint": stakes or meta["hint"],
            "available": bool(available),
        }
        if reason:
            entry["reason"] = reason
        if reason_code:
            entry["reason_code"] = reason_code
        if cost:
            entry["cost"] = cost
        for key, value in extra.items():
            if value is not None:
                entry[key] = value
        return entry

    def _combat_options(self, encounter: Dict[str, Any], player: Player, player_power: float) -> List[Dict[str, Any]]:
        foes = encounter.get("foes") or []
        leader_id = foes[0] if foes else ""
        leader = self._enemies.get(leader_id, {})
        power = foe_power(leader)
        ratio = power / player_power if player_power > 0 else 1.0
        mindless = self.is_mindless(leader_id)
        ambushed = bool(encounter.get("ambush"))
        threat = threat_tier(power, player_power)
        wound = encounter.get("wound")
        # E.4: the fight card leads with the comparison it is actually betting on.
        fight_stakes = self.stake_line(
            "fight", threat=threat, foe_power=int(round(power)), player_power=int(round(player_power))
        )
        if wound:
            fight_stakes = f"{fight_stakes} {self.wound_line(wound, player)}".strip()
        options = [
            self._option(
                "fight",
                stakes=fight_stakes,
                odds={
                    "threat": threat,
                    "foe_power": int(round(power)),
                    "player_power": int(round(player_power)),
                    "ratio": round(ratio, 2),
                },
                wound=wound,
                mercy=bool(encounter.get("mercy")),
            )
        ]

        parley_chance = self._check_chance(self._config("parley"), player, ratio)
        talk = self._option(
            "talk",
            stakes=self.stake_line("talk", chance=int(round(parley_chance * 100))),
            chance=round(parley_chance, 2),
        )
        if mindless:
            talk = self._option("talk", available=False, reason_code="MINDLESS_FOE",
                                reason=f"The {leader.get('name', 'thing')} has no speech in it; words will not reach it.")
        elif len(foes) > 1:
            talk = self._option("talk", available=False, reason_code="PACK_TOO_MANY",
                                reason="The pack answers only to the strongest; there is no one voice to parley with.")
        options.append(talk)

        sneak_chance = self._check_chance(self._config("sneak"), player, ratio)
        sneak = self._option("sneak", available=not ambushed,
                             reason_code="AMBUSHED" if ambushed else "",
                             reason="They are already on you -- there is no moment left to slip away." if ambushed else "")
        if not ambushed:
            sneak["chance"] = round(sneak_chance, 2)
            sneak["hint"] = self.stake_line("sneak", chance=int(round(sneak_chance * 100)))
        options.append(sneak)

        toll = self.toll(leader, player_power)
        bribe_chance = self._check_chance(self._config("bribe"), player, ratio)
        pay = self._option(
            "pay",
            cost=toll,
            stakes=self.stake_line("pay", chance=int(round(bribe_chance * 100)), gold=toll.get("gold", 0)),
            chance=round(bribe_chance, 2),
        )
        if mindless:
            pay = self._option("pay", available=False, reason_code="MINDLESS_FOE",
                               reason="It does not know what coin is.")
        elif player.gold < toll.get("gold", 0):
            pay = self._option("pay", available=False, reason_code="CANNOT_AFFORD",
                               reason=f"You cannot afford the toll ({toll.get('gold', 0)} gold).",
                               cost=toll)
        options.append(pay)

        # Reading the scene is a one-time bargain: it banks insight, so letting
        # it repeat would let the patient farm the fight before it starts.
        observe_stakes = self.stake_line(
            "observe",
            insight=self.observed_insight(player),
            provoke=int(round(float(self._config("observe").get("provoke_chance", 0.22)) * 100)),
        )
        if encounter.get("observed"):
            observe = self._option("observe", available=False, reason_code="ALREADY_OBSERVED",
                                   reason="You have already read this scene; there is nothing left to learn from watching.")
        else:
            observe = self._option("observe", available=not ambushed,
                                   reason_code="AMBUSHED" if ambushed else "",
                                   reason="There is no time to study a scene that is already unfolding." if ambushed else "",
                                   stakes=observe_stakes,
                                   insight=self.observed_insight(player))
        options.append(observe)

        # E.4: what walking away actually costs, in this scene's own terms.
        withdraw_stakes = self.stake_line("withdraw_combat")
        withdraw = self._option("withdraw", stakes=withdraw_stakes, forfeit="the road")
        if ambushed:
            chance = round(self._check_chance(self._config("sneak"), player, ratio), 2)
            withdraw["chance"] = chance
            withdraw["hint"] = self.stake_line("withdraw_ambush", chance=int(round(chance * 100)))
        options.append(withdraw)
        return options

    def _loot_options(self, encounter: Dict[str, Any], player: Player, player_power: float) -> List[Dict[str, Any]]:
        loot = encounter.get("loot") or {}
        revealed = bool(loot.get("revealed"))
        trap = loot.get("trap")
        if revealed:
            take_stakes = self.stake_line("take_revealed")
            risk: Dict[str, Any] = {"trap_chance": 0.0, "warded": trap is not None}
        else:
            trapped_chance = float(self._config("encounter").get("trapped_loot_chance", 0.3))
            take_stakes = self.stake_line("take", trap_chance=int(round(trapped_chance * 100)))
            risk = {"trap_chance": round(trapped_chance, 2), "warded": None}
        options = [self._option("take", stakes=take_stakes, risk=risk)]
        if revealed:
            reason = ("You know what waits there now; the ward will not catch you twice."
                      if loot.get("trap") else "You have read the find; nothing about it is hidden any longer.")
            options.append(self._option("examine", available=False, reason_code="ALREADY_EXAMINED", reason=reason))
        else:
            options.append(self._option("examine", stakes=self.stake_line("examine")))
        options.append(self._option("leave", stakes=self.stake_line("leave_loot"), forfeit="the find"))
        return options

    def _special_options(self, encounter: Dict[str, Any], player: Player, player_power: float) -> List[Dict[str, Any]]:
        special = encounter.get("special") or {}
        revealed = bool(special.get("revealed"))
        effect = dict(special.get("effect") or {})
        if revealed:
            accept = self._option(
                "accept",
                stakes=self.stake_line("accept", effect=self.effect_line(effect)) or self.option_meta("accept")["hint"],
                effect=effect,
            )
        else:
            accept = self._option(
                "accept",
                stakes=self.stake_line("accept_unread") or self.option_meta("accept")["hint"],
            )
        options = [accept]
        if revealed:
            options.append(self._option("study", available=False, reason_code="ALREADY_STUDIED",
                                        reason="You have already learned what this place offers."))
        else:
            options.append(self._option("study", stakes=self.stake_line("study")))
        options.append(self._option("decline", stakes=self.stake_line("decline_special"), forfeit="the place's power"))
        return options

    def _hazard_options(self, encounter: Dict[str, Any], player: Player, player_power: float) -> List[Dict[str, Any]]:
        hazard = encounter.get("hazard") or {}
        studied = bool(hazard.get("studied"))
        damage = int(hazard.get("effect", {}).get("magnitude", 0) or 0)
        push_chance = round(self.hazard_push_chance(hazard), 2)
        push = self._option(
            "push",
            stakes=self.stake_line("push", chance=int(round(push_chance * 100)), damage=damage),
            chance=push_chance,
            damage=damage,
        )
        options = [push]
        defuse_chance = round(self.hazard_defuse_chance(hazard, player), 2)
        defuse = self._option(
            "defuse",
            stakes=self.stake_line(
                "defuse", chance=int(round(defuse_chance * 100)), damage=max(1, damage // 2)
            ),
            chance=defuse_chance,
            damage=max(1, damage // 2),
            reward=dict(hazard.get("defuse_reward") or {}),
        )
        options.append(defuse)
        if studied:
            options.append(self._option("study", available=False, reason_code="ALREADY_STUDIED",
                                        reason="You have already read this ground."))
        else:
            options.append(self._option("study", stakes=self.stake_line("study")))
        options.append(self._option("withdraw", stakes=self.stake_line("withdraw_hazard"), forfeit="what this ground pays"))
        return options

    @staticmethod
    def effect_line(effect: Dict[str, Any]) -> str:
        """Render a site-of-power effect as the numbers it will actually apply."""
        parts: List[str] = []
        for key in ("heal", "restore_qi", "restore", "exp", "insight", "progress"):
            value = int(effect.get(key, 0) or 0)
            if value:
                parts.append(f"+{value} {key.replace('_', ' ')}")
        kind = str(effect.get("type", "") or "")
        magnitude = int(effect.get("magnitude", 0) or 0)
        if kind and kind != "none" and magnitude:
            parts.append(f"{kind.replace('_', ' ')} {magnitude}")
        return ", ".join(parts)

    # -- odds -------------------------------------------------------------
    def _check_chance(self, config: Dict[str, Any], player: Player, ratio: float) -> float:
        """Return the clamped probability of a social/stealth check succeeding."""
        chance = (
            float(config.get("base_chance", 0.6))
            - (ratio - 1.0) * float(config.get("power_penalty", 0.35))
            + float(getattr(player, "comprehension", 0) or 0) * float(config.get("comprehension_bonus", 0.01))
            + float(getattr(player, "reputation", 0) or 0) * float(config.get("reputation_bonus", 0.0))
        )
        return max(float(config.get("min_chance", 0.05)), min(float(config.get("max_chance", 0.95)), chance))

    def toll(self, enemy: Any, player_power: float) -> Dict[str, int]:
        """Return the coin a foe wants to let the player pass."""
        config = self._config("bribe")
        power = foe_power(enemy)
        amount = int(round(power / max(1.0, float(config.get("power_per_coin", 8)))))
        amount = max(int(config.get("min_cost", 5)), min(int(config.get("max_cost", 300)), amount))
        return {str(config.get("currency", "gold")): amount}

    def observed_insight(self, player: Player) -> int:
        """Return the opening insight a turn spent observing banks."""
        config = self._config("observe")
        insight = int(config.get("insight_base", 1)) + int(getattr(player, "comprehension", 0) or 0) // max(
            1, int(config.get("insight_per_comprehension", 6))
        )
        return max(0, min(int(config.get("insight_cap", 6)), insight))

    def hazard_defuse_chance(self, hazard: Dict[str, Any], player: Player) -> float:
        """Return the probability of reading a safe path through a hazard."""
        chance = float(hazard.get("defuse_base_chance", 0.45)) + float(getattr(player, "comprehension", 0) or 0) * float(
            hazard.get("comprehension_bonus", 0.015)
        )
        if hazard.get("studied"):
            chance += 0.15
        return max(0.05, min(0.95, chance))

    def hazard_push_chance(self, hazard: Dict[str, Any]) -> float:
        """Return the probability of crossing a hazard unharmed."""
        chance = float(hazard.get("push_base_chance", 0.5))
        if hazard.get("studied"):
            chance += 0.15
        return max(0.05, min(0.95, chance))

    # -- resolution -------------------------------------------------------
    def resolve(
        self,
        encounter: Dict[str, Any],
        choice_id: str,
        player: Player,
        player_power: float,
    ) -> Dict[str, Any]:
        """Roll the outcome of ``choice_id``; the caller applies it.

        The returned payload is a *description*, never a mutation: ``start_combat``
        asks the engine to field the formation, ``cost``/``damage``/``reward`` ask
        it to spend, hurt, or pay the player, and ``verb`` names the prose line.
        """
        resolvers = {
            COMBAT: self._resolve_combat,
            LOOT: self._resolve_loot,
            SPECIAL: self._resolve_special,
            HAZARD: self._resolve_hazard,
        }
        resolver = resolvers.get(encounter.get("kind"))
        if resolver is None:
            return {"outcome": "NONE", "verb": "encounter", "resolve": True}
        payload = resolver(encounter, choice_id, player, player_power)
        self.note_wound(payload)
        return payload

    # -- the wound the ground left (E.5) ----------------------------------
    def note_wound(self, payload: Dict[str, Any]) -> None:
        """Remember a hazard or trap's price, to be named in the next fight.

        Hazard and trap damage never kills (it floors at 1 HP in the engine), so
        the consequence belongs to the *next* fight; this holds it there instead
        of letting it show up only as a smaller HP number.
        """
        damage = int(payload.get("damage", 0) or 0)
        if damage <= 0:
            return
        source = payload.get("hazard") or payload.get("trap") or {}
        self._wound = {
            "id": source.get("id"),
            "name": str(source.get("name") or "the ground"),
            "damage": damage,
        }

    def _consume_wound(self, player: Player) -> Optional[Dict[str, Any]]:
        """Hand the pending wound to the fight now being built, once."""
        wound = self._wound
        self._wound = None
        if wound is None:
            return None
        # Healing in between erases it: the line only ever reports a real debt.
        if int(player.hp) >= int(player.max_hp):
            return None
        return wound

    @staticmethod
    def wound_line(wound: Dict[str, Any], player: Player) -> str:
        """The plain line naming what the ground took and what is left."""
        return (
            f"You are still carrying the {wound.get('name', 'ground')} "
            f"({int(wound.get('damage', 0) or 0)} damage): you meet this at "
            f"{int(player.hp)}/{int(player.max_hp)} HP."
        )

    def _resolve_combat(self, encounter: Dict[str, Any], choice_id: str, player: Player, player_power: float) -> Dict[str, Any]:
        foes = encounter.get("foes") or []
        leader = self._enemies.get(foes[0] if foes else "", {})
        ratio = foe_power(leader) / player_power if player_power > 0 else 1.0
        hazard = encounter.get("hazard")
        if hazard is not None:
            hazard["revealed"] = hazard.get("revealed", False) or bool(encounter.get("observed"))

        if choice_id == "fight":
            # An unread hazard catches whoever walked in first; a hazard the
            # player studied is theirs to turn against the foe instead.
            return {
                "outcome": "ENGAGED",
                "verb": "encounter_fight",
                "start_combat": True,
                "ambush": bool(encounter.get("ambush")),
                "hazard_to_player": hazard is not None and (bool(encounter.get("ambush")) or not bool(hazard.get("revealed"))),
                "hazard_revealed": hazard is not None and bool(hazard.get("revealed")),
                "hazard": hazard,
                "resolve": True,
            }
        if choice_id == "observe":
            insight = self.observed_insight(player)
            encounter["observed"] = True
            hazard_revealed = False
            if hazard is not None:
                hazard["revealed"] = True
                hazard_revealed = True
            trap_revealed = False
            if encounter.get("loot") and not encounter["loot"].get("revealed"):
                encounter["loot"]["revealed"] = True
                trap_revealed = True
            provoked = (not encounter.get("ambush")) and self._rng.chance(float(self._config("observe").get("provoke_chance", 0.22)))
            # A calm read keeps the scene open for the real choice; a provoked
            # read closes it by starting the fight the player did not pick.
            return {
                "outcome": "PROVOKED" if provoked else "REVEALED",
                "verb": "encounter_observed",
                "insight": insight,
                "reveals": {"hazard": hazard_revealed, "trap": trap_revealed},
                "start_combat": provoked,
                "ambush": provoked,
                "hazard": hazard,
                "hazard_to_player": False,
                "resolve": bool(provoked),
            }
        if choice_id == "talk":
            if self.is_mindless(foes[0] if foes else ""):
                return {"outcome": "NO_SPEECH", "verb": "encounter_parley_fail", "start_combat": True, "ambush": False, "hazard": hazard, "hazard_to_player": False, "resolve": True}
            if self._rng.chance(self._check_chance(self._config("parley"), player, ratio)):
                exp = int(round(foe_power(leader) * float(self._config("parley").get("success_exp_ratio", 0.5)) / 5.0))
                return {
                    "outcome": "PARLEY",
                    "verb": "encounter_parley",
                    "reward": {"exp": max(1, exp), "reputation": int(self._config("parley").get("success_reputation", 1))},
                    "resolve": True,
                }
            offended = self._rng.chance(float(self._config("parley").get("offend_ambush_chance", 0.35)))
            return {
                "outcome": "OFFENDED",
                "verb": "encounter_parley_fail",
                "start_combat": True,
                "ambush": offended,
                "hazard": hazard,
                "hazard_to_player": False,
                "resolve": True,
            }
        if choice_id == "sneak":
            if encounter.get("ambush"):
                return {"outcome": "NO_TIME", "verb": "encounter_sneak_fail", "start_combat": True, "ambush": True, "hazard": hazard, "hazard_to_player": True, "resolve": True}
            if self._rng.chance(self._check_chance(self._config("sneak"), player, ratio)):
                cache = None
                if self._rng.chance(float(self._config("sneak").get("cache_chance", 0.35))):
                    cache = self._roll_sneak_cache(encounter)
                return {
                    "outcome": "AVOIDED",
                    "verb": "encounter_sneak",
                    "reward": {"exp": int(self._config("sneak").get("escape_exp", 3))},
                    "loot": cache,
                    "resolve": True,
                }
            return {
                "outcome": "SPOTTED",
                "verb": "encounter_sneak_fail",
                "start_combat": True,
                "ambush": True,
                "hazard": hazard,
                "hazard_to_player": True,
                "resolve": True,
            }
        if choice_id == "pay":
            toll = self.toll(leader, player_power)
            if self._rng.chance(self._check_chance(self._config("bribe"), player, ratio)):
                return {"outcome": "TOLL_PAID", "verb": "encounter_bribe", "cost": toll, "resolve": True}
            return {
                "outcome": "TOLL_REFUSED",
                "verb": "encounter_bribe_refused",
                "start_combat": True,
                "ambush": False,
                "hazard": hazard,
                "hazard_to_player": False,
                "resolve": True,
            }
        if choice_id == "withdraw":
            if encounter.get("ambush") and not self._rng.chance(self._check_chance(self._config("sneak"), player, ratio)):
                return {"outcome": "CUT_OFF", "verb": "encounter_withdraw_fail", "start_combat": True, "ambush": True, "hazard": hazard, "hazard_to_player": True, "resolve": True}
            return {"outcome": "WITHDREW", "verb": "encounter_withdraw", "resolve": True}
        return {"outcome": "UNKNOWN", "verb": "encounter", "resolve": False}

    def _roll_sneak_cache(self, encounter: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """A clean sneak past a foe sometimes turns up their unattended cache."""
        pool_loot = encounter.get("_pool_loot") or []
        if pool_loot:
            entry = self._rng.weighted_choice(
                [item["item_id"] for item in pool_loot],
                [item.get("weight", 1) for item in pool_loot],
            )
            return {"item_id": str(entry), "count": 1}
        return None

    def _resolve_loot(self, encounter: Dict[str, Any], choice_id: str, player: Player, player_power: float) -> Dict[str, Any]:
        loot = encounter.get("loot") or {}
        trap = loot.get("trap")
        if choice_id == "examine":
            loot["revealed"] = True
            if trap is not None:
                trap["revealed"] = True
            return {
                "outcome": "EXAMINED",
                "verb": "encounter_observe",
                "reveals": {"trap": bool(trap)},
                "resolve": False,
            }
        if choice_id == "take":
            payload: Dict[str, Any] = {
                "outcome": "TAKEN",
                "verb": "encounter_taken" if trap is None or loot.get("revealed") else "encounter_trap",
                "loot": {"item_id": loot.get("item_id", ""), "count": int(loot.get("count", 1) or 1)},
                "resolve": True,
            }
            if trap is not None and not loot.get("revealed"):
                payload["damage"] = int(trap.get("effect", {}).get("magnitude", 0))
                payload["trap"] = trap
            return payload
        if choice_id == "leave":
            return {"outcome": "LEFT", "verb": "encounter_decline", "resolve": True}
        return {"outcome": "UNKNOWN", "verb": "encounter", "resolve": False}

    def _resolve_special(self, encounter: Dict[str, Any], choice_id: str, player: Player, player_power: float) -> Dict[str, Any]:
        special = encounter.get("special") or {}
        if choice_id == "study":
            special["revealed"] = True
            return {"outcome": "STUDIED", "verb": "encounter_observe", "reveals": {"special": True}, "resolve": False}
        if choice_id == "accept":
            return {"outcome": "ACCEPTED", "verb": "encounter_accept", "effect": dict(special.get("effect") or {}), "resolve": True}
        if choice_id == "decline":
            return {"outcome": "DECLINED", "verb": "encounter_decline", "resolve": True}
        return {"outcome": "UNKNOWN", "verb": "encounter", "resolve": False}

    def _resolve_hazard(self, encounter: Dict[str, Any], choice_id: str, player: Player, player_power: float) -> Dict[str, Any]:
        hazard = dict(encounter.get("hazard") or {})
        if choice_id == "study":
            hazard["studied"] = True
            hazard["revealed"] = True
            encounter["hazard"] = hazard
            return {"outcome": "STUDIED", "verb": "encounter_observe", "reveals": {"hazard": True}, "resolve": False}
        if choice_id == "push":
            if self._rng.chance(self.hazard_push_chance(hazard)):
                return {"outcome": "CROSSED", "verb": "encounter_hazard_push", "reward": dict(hazard.get("reward") or {}), "resolve": True}
            return {
                "outcome": "CAUGHT",
                "verb": "encounter_hazard_push",
                "damage": int(hazard.get("effect", {}).get("magnitude", 0)),
                "hazard": hazard,
                "resolve": True,
            }
        if choice_id == "defuse":
            if self._rng.chance(self.hazard_defuse_chance(hazard, player)):
                return {
                    "outcome": "DEFUSED",
                    "verb": "encounter_hazard_defuse",
                    "reward": dict(hazard.get("defuse_reward") or {}),
                    "resolve": True,
                }
            magnitude = max(1, int(hazard.get("effect", {}).get("magnitude", 0)) // 2)
            return {
                "outcome": "FAILED",
                "verb": "encounter_hazard_push",
                "damage": magnitude,
                "hazard": hazard,
                "resolve": True,
            }
        if choice_id == "withdraw":
            return {"outcome": "WITHDREW", "verb": "encounter_withdraw", "resolve": True}
        return {"outcome": "UNKNOWN", "verb": "encounter", "resolve": False}

    # -- reveal payloads --------------------------------------------------
    def reveal_view(self, encounter: Dict[str, Any], player: Optional[Player] = None) -> Dict[str, Any]:
        """Return what an observant player has learned about the scene."""
        reveal: Dict[str, Any] = {}
        if encounter.get("hazard") is not None:
            hazard = encounter["hazard"]
            defuse_chance = self.hazard_defuse_chance(hazard, player) if player is not None else float(hazard.get("defuse_base_chance", 0.45))
            reveal["hazard"] = {
                "id": hazard.get("id"),
                "name": hazard.get("name"),
                "text": hazard.get("text"),
                "revealed": bool(hazard.get("revealed")),
                "neutralized": bool(hazard.get("neutralized")),
                "studied": bool(hazard.get("studied")),
                "damage": int(hazard.get("effect", {}).get("magnitude", 0)),
                "push_chance": round(self.hazard_push_chance(hazard), 2),
                "defuse_chance": round(defuse_chance, 2),
            }
        loot = encounter.get("loot")
        if isinstance(loot, dict) and loot.get("revealed"):
            trap = loot.get("trap")
            reveal["trap"] = {
                "id": trap.get("id") if trap else None,
                "name": trap.get("name") if trap else None,
                "text": trap.get("text") if trap else "",
                "damage": int(trap.get("effect", {}).get("magnitude", 0)) if trap else 0,
                "trapped": trap is not None,
            }
        special = encounter.get("special")
        if isinstance(special, dict) and special.get("revealed"):
            reveal["special"] = {
                "special_id": special.get("special_id"),
                "effect": dict(special.get("effect") or {}),
            }
        if encounter.get("kind") == COMBAT and encounter.get("observed"):
            reveal["foes"] = [
                {
                    "id": foe_id,
                    "name": str(self._enemies.get(foe_id, {}).get("name", foe_id)),
                    "abilities": list(self._enemies.get(foe_id, {}).get("abilities") or []),
                    "power": int(foe_power(self._enemies.get(foe_id, {}))),
                }
                for foe_id in (encounter.get("foes") or [])
            ]
        return reveal

    def pack_scale(self, danger: Optional[int] = None) -> float:
        """Return the stat multiplier applied to extra formation foes.

        Capped by the danger of the ground (F.1): a pack in the shallow, busy
        zones hits softer than one in the deep. ``danger`` defaults to the most
        recently built encounter -- the one being spawned -- because the spawner
        asks for the config without the encounter to hand.
        """
        formation = self._config("formation")
        scale = float(formation.get("pack_stat_scale", 0.6))
        level = self._built_danger if danger is None else int(danger)
        ceiling = self._chance_at_danger(list(formation.get("pack_stat_scale_ceiling") or []), level)
        return min(scale, float(ceiling)) if ceiling else scale

    def formation_config(self) -> Dict[str, Any]:
        """Return the formation tuning (pack presses, reward ratios, caps)."""
        return self._config("formation")
