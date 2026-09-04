"""Combat system.

Implements turn-based, player-vs-enemy combat as a set of *rule calculations*.
Each public method resolves one player action plus the enemy's response (a full
round) and returns a structured result:

* ``COMBAT_TURN`` — the round resolved and the fight continues.
* ``COMBAT_END``  — the fight ended (``VICTORY`` / ``DEFEAT`` / ``FLED``).

The engine drives *when* these are called and handles loot/defeat consequences;
the combat system only computes what happens mechanically. No UI, no formatting.

Active skill effects are resolved here, keyed by ``Skill.effect``:

* ``damage`` / ``true_damage`` / ``aoe_damage`` / ``execute`` / ``life_steal``
  — damage with defence, armour-piercing, multi-target (single for now),
  low-HP bonus, and self-heal variants respectively.
* ``stun`` — enemy skips its next ``scaling`` turns.
* ``dot_damage`` — enemy takes per-turn damage for a fixed number of turns.
* ``shield`` — player gains a damage-absorption pool.
* ``counter`` — for a few turns the enemy takes damage whenever it hits.
* ``debuff_attack`` / ``debuff_defense`` — enemy's stat divided by ``scaling``.
* ``heal_self`` — player recovers HP.

Passive effects (``StatsSystem``) such as ``buff_*``, ``crit_chance``, regen and
evasion are honoured here where they touch a combat round.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from game.core.constants import EventType
from game.models.enemy import Enemy
from game.models.player import Player
from game.models.skill import Skill
from game.systems.dao_system import DaoSystem
from game.utils.rng import RNG

if TYPE_CHECKING:
    from game.systems.stats_system import StatsSystem

TurnEvent = Dict[str, Any]

# Timed-effect durations (turns). No duration lives in skill data, so these are
# fixed. Re-tune or move into data if the effect ladder needs per-skill control.
DOT_TURNS = 3
COUNTER_TURNS = 3
DEBUFF_TURNS = 3

# ponytail: execute triggers below this HP fraction. Fixed for now.
EXECUTE_THRESHOLD = 0.3
# ponytail: dodge chance per evasion point. Fixed; re-tune with the ladder.
EVASION_CHANCE_PER_POINT = 0.01
EVASION_CAP = 0.5
# ponytail: a spar is called off once either side drops to this HP fraction.
SPAR_END_HP_FRACTION = 0.25
# Insight (B.5): a mid-fight resource built from comprehension and successful
# exchanges. Active skills with ``insight_required > 0`` need this much insight
# to fire, so intent techniques unlock as a fight's exchanges accumulate.
INSIGHT_COMPREHENSION_DIVISOR = 10  # per-round drip: comprehension // 10
INSIGHT_PER_HIT = 1                 # landing a damaging blow (incl. a counter wound)
INSIGHT_PER_CRIT = 1                # extra for a critical hit

# Combos (B.6): the stance roles an active technique may declare. A chain of
# opening -> response -> finisher grants escalating damage bonuses; using a
# role out of order drops the chain. Sequencing/bonus tuning lives here; which
# techniques carry which role lives in ``data/skills.json`` (``combo_role``).
COMBO_ROLES = ("opening", "response", "finisher")
COMBO_BONUS_PER_STAGE = 0.25  # damage bonus per completed chain stage (1.25x, 1.5x, 1.75x)
COMBO_RESET_ROLES = frozenset({"none"})

# Foe AI (B.8): a guarding foe skips its press this round and shelters behind
# its defense; the player's banked chain stage feeds its own momentum on the
# foe's next real press.
FOE_GUARD_DEFENSE_BONUS = 0.5  # +50% effective defense while guarding
FOE_GUARD_MOMENTUM = 0.25      # the guarded flow banked into the next press


class CombatSystem:
    """Resolves individual combat rounds between the player and an enemy."""

    def __init__(
        self,
        rng: RNG,
        stats: Optional["StatsSystem"] = None,
        dao: Optional[DaoSystem] = None,
        skills: Optional[Dict[str, Skill]] = None,
        foe_ai: Optional[Any] = None,
    ) -> None:
        self._rng = rng
        self._stats = stats
        self._dao = dao
        # Technique catalogue (id -> Skill) for combo sequencing (B.6).
        self._skills: Dict[str, Skill] = skills or {}
        # B.8: the foe-mind consulted each enemy phase (dao/pressure/stances).
        self.foe_ai = foe_ai

    def begin_combat(self, player: Player) -> int:
        """Reset the player's insight pool and combo chain at the start of a fight."""
        player.insight = 0
        player.combo_stage = 0
        return player.insight

    def attack(self, player: Player, enemy: Enemy, spar: bool = False) -> Dict[str, Any]:
        """Player performs a basic attack, then the enemy retaliates if alive."""
        raw = int(self._player_attack(player))
        is_crit, mult = self._roll_crit(player)
        raw = int(raw * mult)
        dealt, _ = self._deal_damage(enemy, self._player_damage(player, enemy, raw))
        event: TurnEvent = {"actor": "PLAYER", "action": "ATTACK", "damage": dealt, "target_hp": enemy.hp}
        if is_crit:
            event["crit"] = True
        events: List[TurnEvent] = [event]
        self._record_insight(events, player, self._gain_exchange_insight(player, dealt, is_crit), "exchange")
        return self._resolve_round(player, enemy, events, spar)

    def use_skill(self, player: Player, enemy: Enemy, skill: Skill, spar: bool = False) -> Dict[str, Any]:
        """Player invokes an active skill, then the enemy retaliates if alive.

        Qi cost and cooldown validation are the engine's responsibility; by the
        time this is called the activation has already been paid for.
        """
        events = self._apply_active_skill(player, enemy, skill)
        stage_before = player.combo_stage
        expected = self.next_combo_role(player)
        stage = self._advance_combo(player, skill)
        if stage == 3:
            # The opening -> response -> finisher chain completed: bank the
            # flourish as a turn event and reset for the next sequence.
            events.append({"actor": "PLAYER", "action": "COMBO_FINISH"})
            player.combo_stage = 0
        elif stage_before > 0 and stage == 0:
            # A banked chain was broken (a neutral technique, or an
            # out-of-sequence stance from a direct caller): surface the drop so
            # frontends can narrate the lost flow.
            events.append(
                {"actor": "PLAYER", "action": "COMBO_DROPPED", "expected_role": expected, "used_role": skill.combo_role}
            )
        return self._resolve_round(player, enemy, events, spar)

    def enemy_turn_only(self, player: Player, enemy: Enemy, spar: bool = False) -> Dict[str, Any]:
        """Resolve just the enemy's turn (used after the player uses an item)."""
        events: List[TurnEvent] = []
        self._enemy_phase(player, enemy, events)
        if spar:
            return self._spar_round_end(player, enemy, events)
        if not enemy.is_alive():
            return self._victory(player, enemy, events)
        if not player.is_alive():
            return self._defeat(enemy, events)
        return self._turn(player, enemy, events)

    def flee(self, player: Player, enemy: Enemy, spar: bool = False) -> Dict[str, Any]:
        """Attempt to escape; a failed attempt gives the enemy a free strike."""
        if self._rng.chance(0.5):
            return {
                "event": EventType.COMBAT_END,
                "outcome": "FLED",
                "enemy_name": enemy.name,
                "turn_events": [{"actor": "PLAYER", "action": "FLEE_SUCCESS"}],
            }
        events: List[TurnEvent] = [
            {"actor": "PLAYER", "action": "FLEE_FAILED"},
            self._enemy_act(player, enemy),
        ]
        if spar:
            return self._spar_round_end(player, enemy, events)
        if not player.is_alive():
            return self._defeat(enemy, events)
        return self._turn(player, enemy, events)

    # -- active skill resolution ----------------------------------------
    def _apply_active_skill(self, player: Player, enemy: Enemy, skill: Skill) -> List[TurnEvent]:
        """Apply ``skill``'s effect and return the turn events describing it."""
        effect = skill.effect
        combo_mult = self._combo_multiplier(player, skill)
        if effect in ("damage", "true_damage", "aoe_damage"):
            return self._hit(player, enemy, skill, ignore_defense=effect == "true_damage", combo_mult=combo_mult)
        if effect == "execute":
            return self._hit(player, enemy, skill, execute=True, combo_mult=combo_mult)
        if effect == "life_steal":
            return self._hit(player, enemy, skill, life_steal=True, combo_mult=combo_mult)
        if effect == "heal_self":
            healed = player.heal(int(self._player_attack(player) * skill.scaling))
            return [{"actor": "PLAYER", "action": "SKILL", "skill": skill.name, "healed": healed, "hp": player.hp}]
        if effect == "stun":
            turns = max(1, int(skill.scaling))
            self._apply_status(enemy, "stun", turns, 0.0)
            return [{"actor": "PLAYER", "action": "SKILL", "skill": skill.name, "stun": turns}]
        if effect == "dot_damage":
            tick = max(1, int(self._player_attack(player) * skill.scaling) - self._enemy_defense_value(enemy) // 2)
            self._apply_status(enemy, "dot_damage", DOT_TURNS, float(tick))
            return [{"actor": "PLAYER", "action": "SKILL", "skill": skill.name, "dot": tick, "turns": DOT_TURNS}]
        if effect == "shield":
            amount = max(1, int(self._player_attack(player) * skill.scaling))
            player.shield += amount
            return [{"actor": "PLAYER", "action": "SKILL", "skill": skill.name, "shield": amount, "shield_total": player.shield}]
        if effect == "counter":
            damage = max(1, int(self._player_attack(player) * skill.scaling) - self._enemy_defense_value(enemy) // 2)
            self._apply_status(player, "counter", COUNTER_TURNS, float(damage))
            return [{"actor": "PLAYER", "action": "SKILL", "skill": skill.name, "counter": damage, "turns": COUNTER_TURNS}]
        if effect in ("debuff_attack", "debuff_defense"):
            self._apply_status(enemy, effect, DEBUFF_TURNS, skill.scaling)
            return [{"actor": "PLAYER", "action": "SKILL", "skill": skill.name, "debuff": effect, "turns": DEBUFF_TURNS}]
        return [{"actor": "PLAYER", "action": "SKILL", "skill": skill.name, "note": "no_combat_effect"}]

    def _hit(
        self,
        player: Player,
        enemy: Enemy,
        skill: Skill,
        *,
        ignore_defense: bool = False,
        execute: bool = False,
        life_steal: bool = False,
        combo_mult: float = 1.0,
    ) -> List[TurnEvent]:
        """Resolve a damage-dealing skill hit and return its event."""
        raw = int(self._player_attack(player) * skill.scaling * combo_mult)
        is_crit, mult = self._roll_crit(player)
        raw = int(raw * mult)
        if execute and enemy.max_hp > 0 and enemy.hp < enemy.max_hp * EXECUTE_THRESHOLD:
            raw *= 2
        dealt, absorbed = self._deal_damage(enemy, self._player_damage(player, enemy, raw, ignore_defense=ignore_defense))
        event: TurnEvent = {"actor": "PLAYER", "action": "SKILL", "skill": skill.name, "damage": dealt, "target_hp": enemy.hp}
        if absorbed:
            event["shield_absorbed"] = absorbed
        if is_crit:
            event["crit"] = True
        if life_steal and dealt > 0:
            event["life_steal"] = player.heal(dealt)
        events: List[TurnEvent] = [event]
        self._record_insight(events, player, self._gain_exchange_insight(player, dealt, is_crit), "exchange")
        return events

    # -- round resolution ------------------------------------------------
    def _resolve_round(self, player: Player, enemy: Enemy, events: List[TurnEvent], spar: bool = False) -> Dict[str, Any]:
        """After the player's action, apply regen, run the enemy phase, resolve end."""
        hp_regen, qi_regen = self._regen(player)
        if hp_regen:
            player.heal(hp_regen)
        if qi_regen:
            player.restore_qi(qi_regen)
        self._record_insight(events, player, self._gain_comprehension_insight(player), "comprehension")
        if not enemy.is_alive():
            if spar:
                return self._spar_end(player, enemy, events, "SPAR_WON")
            return self._victory(player, enemy, events)
        self._enemy_phase(player, enemy, events)
        if spar:
            return self._spar_round_end(player, enemy, events)
        if not enemy.is_alive():
            return self._victory(player, enemy, events)
        if not player.is_alive():
            return self._defeat(enemy, events)
        return self._turn(player, enemy, events)

    def _spar_round_end(self, player: Player, enemy: Enemy, events: List[TurnEvent]) -> Dict[str, Any]:
        """Resolve a sparring round: the match is called off at low HP, never death."""
        if not enemy.is_alive() or enemy.hp <= enemy.max_hp * SPAR_END_HP_FRACTION:
            return self._spar_end(player, enemy, events, "SPAR_WON")
        if not player.is_alive() or player.hp <= player.max_hp * SPAR_END_HP_FRACTION:
            return self._spar_end(player, enemy, events, "SPAR_LOST")
        return self._turn(player, enemy, events)

    def _spar_end(self, player: Player, enemy: Enemy, events: List[TurnEvent], outcome: str) -> Dict[str, Any]:
        """End a friendly spar with no exp, loot, or defeat consequences."""
        return {
            "event": EventType.COMBAT_END,
            "outcome": outcome,
            "enemy_name": enemy.name,
            "turn_events": events,
        }

    def _enemy_phase(self, player: Player, enemy: Enemy, events: List[TurnEvent]) -> None:
        """Enemy acts (or skips when stunned), then its timed effects tick.

        With a foe-mind installed (B.8), dao-carrying foes act on intent --
        stance chains, counter-graph aggression, and guards against the
        player's banked flow -- while mooks keep the plain ability/attack roll.
        """
        stun = enemy.statuses.get("stun")
        if stun:
            events.append({"actor": "ENEMY", "action": "STUNNED", "enemy_name": enemy.name})
            self._expire(enemy, "stun")
        else:
            events.append(self._enemy_act(player, enemy))
        self._tick_enemy_statuses(enemy, events)
        self._tick_player_statuses(player, events)

    def _foe_execute(self, player: Player, enemy: Enemy, intent: Dict[str, Any]) -> TurnEvent:
        """Execute a B.8 foe intent (technique/ability/attack/guard) as one event."""
        kind = intent.get("kind")
        if kind == "technique":
            skill = self._skills.get(intent.get("skill_id", ""))
            if skill is not None and skill.is_active():
                return self._foe_technique(player, enemy, skill)
            return self._enemy_attack(player, enemy)
        if kind == "ability":
            return self._enemy_ability(player, enemy, intent.get("ability", {}))
        if kind == "guard":
            # Shelter behind defense; the respected flow banks into the foe's
            # next press as momentum. Two turns so the same-round status tick
            # (which expires it once) still leaves the shell up through the
            # player's next attack.
            enemy.statuses["guard"] = {"turns": 2, "magnitude": FOE_GUARD_MOMENTUM}
            return {"actor": "ENEMY", "action": "GUARD", "enemy_name": enemy.name}
        return self._enemy_attack(player, enemy)

    def _foe_technique(self, player: Player, enemy: Enemy, skill: Skill) -> TurnEvent:
        """Resolve a foe's active technique with its chain bonus, then bank it."""
        stage = int(getattr(enemy, "ai_stage", 0))
        momentum = self._consume_guard_momentum(enemy)
        multiplier = 1.0 + stage * COMBO_BONUS_PER_STAGE + momentum
        raw = int(self._enemy_attack_value(enemy) * skill.scaling * multiplier)
        dealt, _ = self._deal_damage(player, self._enemy_damage(player, enemy, raw))
        event: TurnEvent = {
            "actor": "ENEMY",
            "action": "FOE_TECHNIQUE",
            "skill": skill.name,
            "damage": dealt,
            "target_hp": player.hp,
            "enemy_name": enemy.name,
        }
        if stage > 0:
            event["combo_stage"] = stage
        self.foe_ai.advance_ai_stage(enemy, skill.combo_role)
        return event

    def player_stunned_turn(self, player: Player, enemy: Enemy, spar: bool = False) -> Dict[str, Any]:
        """Resolve a round where the player is stunned and must forfeit their turn."""
        events: List[TurnEvent] = [{"actor": "PLAYER", "action": "STUNNED"}]
        self._expire(player, "stun")
        self._enemy_phase(player, enemy, events)
        if spar:
            return self._spar_round_end(player, enemy, events)
        if not enemy.is_alive():
            return self._victory(player, enemy, events)
        if not player.is_alive():
            return self._defeat(enemy, events)
        return self._turn(player, enemy, events)

    def _enemy_act(self, player: Player, enemy: Enemy) -> TurnEvent:
        """Choose the enemy's action: foe AI intent when installed, else raw rolls."""
        if self.foe_ai is not None:
            intent = self.foe_ai.choose_action(player, enemy)
            return self._foe_execute(player, enemy, intent)
        for ability in enemy.abilities:
            if self._rng.chance(float(ability.get("chance", 0.0))):
                return self._enemy_ability(player, enemy, ability)
        return self._enemy_attack(player, enemy)

    def _enemy_ability(self, player: Player, enemy: Enemy, ability: Dict[str, Any]) -> TurnEvent:
        kind = ability.get("type")
        magnitude = ability.get("magnitude", 0)
        if kind == "stun":
            turns = max(1, int(magnitude))
            self._apply_status(player, "stun", turns, 0.0)
            return {"actor": "ENEMY", "action": "STUN", "turns": turns, "enemy_name": enemy.name}
        if kind == "poison":
            tick = max(1, int(magnitude))
            self._apply_status(player, "dot_damage", DOT_TURNS, float(tick))
            return {"actor": "ENEMY", "action": "POISON", "dot": tick, "turns": DOT_TURNS, "enemy_name": enemy.name}
        if kind == "heavy":
            dealt, _ = self._deal_damage(
                player, self._enemy_damage(player, enemy, int(self._enemy_attack_value(enemy) * 1.5))
            )
            return {"actor": "ENEMY", "action": "HEAVY_ATTACK", "damage": dealt, "target_hp": player.hp, "enemy_name": enemy.name}
        return self._enemy_attack(player, enemy)

    def _enemy_attack(self, player: Player, enemy: Enemy) -> TurnEvent:
        momentum = self._consume_guard_momentum(enemy)
        raw = int(self._enemy_attack_value(enemy) * (1.0 + momentum))
        dealt, _ = self._deal_damage(player, self._enemy_damage(player, enemy, raw))
        event: TurnEvent = {
            "actor": "ENEMY",
            "action": "ATTACK",
            "damage": dealt,
            "target_hp": player.hp,
            "enemy_name": enemy.name,
        }
        counter = player.statuses.get("counter")
        if counter and enemy.is_alive():
            counter_dealt, _ = self._deal_damage(enemy, int(counter["magnitude"]))
            event["counter_damage"] = counter_dealt
            gained = self._gain_exchange_insight(player, counter_dealt, False)
            if gained:
                event["insight_gain"] = gained
                event["insight_total"] = player.insight
        return event

    def _tick_enemy_statuses(self, enemy: Enemy, events: List[TurnEvent]) -> None:
        """Apply per-turn enemy effects (dot) and decrement remaining turns."""
        for effect in list(enemy.statuses):
            if effect == "dot_damage":
                dealt, _ = self._deal_damage(enemy, int(enemy.statuses[effect]["magnitude"]))
                events.append({"actor": "ENEMY", "action": "DOT", "damage": dealt, "target_hp": enemy.hp, "enemy_name": enemy.name})
            self._expire(enemy, effect)

    def _tick_player_statuses(self, player: Player, events: List[TurnEvent]) -> None:
        """Apply per-turn player effects (enemy-inflicted poison) once a round."""
        for effect in list(player.statuses):
            if effect == "dot_damage":
                dealt = player.take_damage(int(player.statuses[effect]["magnitude"]))
                events.append({"actor": "PLAYER", "action": "DOT", "damage": dealt, "target_hp": player.hp})
                self._expire(player, effect)

    # -- status helpers --------------------------------------------------
    def _apply_status(self, target: Any, effect: str, turns: int, magnitude: float) -> None:
        target.statuses[effect] = {"turns": turns, "magnitude": magnitude}

    def _expire(self, target: Any, effect: str) -> None:
        status = target.statuses.get(effect)
        if status is None:
            return
        status["turns"] -= 1
        if status["turns"] <= 0:
            del target.statuses[effect]

    # -- combos (B.6) ----------------------------------------------------
    def next_combo_role(self, player: Player) -> Optional[str]:
        """Return the stance role the chain currently expects, or ``None``.

        ``None`` means any technique may be used (no chain banked and no
        expectation set); otherwise the named role continues (or the engine may
        refuse out-of-sequence stances to protect the banked chain).
        """
        stage = player.combo_stage
        if stage <= 0:
            return None
        if stage < len(COMBO_ROLES):
            return COMBO_ROLES[stage]
        return None

    def _combo_multiplier(self, player: Player, skill: Skill) -> float:
        """Damage multiplier the banked chain grants ``skill`` before it lands.

        Stage N of an opening -> response -> finisher chain multiplies any
        damage-dealing technique by ``1 + N * COMBO_BONUS_PER_STAGE`` -- built-up
        momentum flows into the next strike, so the finisher itself lands at the
        top of the ladder. Called before the chain advances or resets.
        """
        if player.combo_stage <= 0:
            return 1.0
        return 1.0 + player.combo_stage * COMBO_BONUS_PER_STAGE

    def _advance_combo(self, player: Player, skill: Skill) -> int:
        """Advance (or reset) the stance chain after ``skill`` resolves.

        ``opening`` arms stage 1, ``response`` continues to stage 2 when armed,
        and ``finisher`` completes the chain (stage 3). A role out of sequence
        drops the chain. The caller banks the ``COMBO_FINISH`` turn event and
        resets to 0 when stage 3 is reached. Returns the new stage.
        """
        role = skill.combo_role
        if role == "opening":
            player.combo_stage = 1
        elif role == "response" and player.combo_stage == 1:
            player.combo_stage = 2
        elif role == "finisher" and player.combo_stage == 2:
            player.combo_stage = 3
        else:
            # A neutral technique or an out-of-sequence stance lets the flow go:
            # the banked chain drops (surfaced as COMBO_DROPPED by the caller).
            player.combo_stage = 0
        return player.combo_stage

    # -- insight (B.5) ---------------------------------------------------
    def _gain_comprehension_insight(self, player: Player) -> int:
        """Grant the per-round insight drip derived from comprehension."""
        gained = max(0, player.comprehension // INSIGHT_COMPREHENSION_DIVISOR)
        if gained:
            player.insight += gained
        return gained

    def _gain_exchange_insight(self, player: Player, dealt: int, is_crit: bool) -> int:
        """Grant insight for a successful exchange and return the amount gained."""
        gained = 0
        if dealt > 0:
            gained += INSIGHT_PER_HIT
        if is_crit:
            gained += INSIGHT_PER_CRIT
        if gained:
            player.insight += gained
        return gained

    def _record_insight(
        self,
        events: List[TurnEvent],
        player: Player,
        gained: int,
        source: str,
    ) -> None:
        """Append an insight turn event when a source granted some insight."""
        if gained:
            events.append(
                {
                    "actor": "PLAYER",
                    "action": "INSIGHT",
                    "gain": gained,
                    "total": player.insight,
                    "source": source,
                }
            )

    # -- dao & realm pressure -------------------------------------------
    def _offense_scale(self, player: Player, enemy: Enemy, attacker_is_player: bool) -> float:
        """Suppression + Dao-matchup multiplier for the attacker's outgoing damage."""
        if self._dao is None:
            return 1.0
        pressure = self._dao.pressure(player, enemy)
        if attacker_is_player:
            return pressure["player_multiplier"] * self._dao.matchup(player.dao_id, enemy.dao_id)
        return pressure["enemy_multiplier"] * self._dao.matchup(enemy.dao_id, player.dao_id)

    def _defense_scale(self, player: Player, enemy: Enemy, defender_is_player: bool) -> float:
        """Suppression multiplier for the defender's effective defense."""
        if self._dao is None:
            return 1.0
        pressure = self._dao.pressure(player, enemy)
        return pressure["player_multiplier"] if defender_is_player else pressure["enemy_multiplier"]

    def _player_damage(self, player: Player, enemy: Enemy, raw: int, ignore_defense: bool = False) -> int:
        """Player's attack value scaled by realm pressure and Dao matchup."""
        attack = int(raw * self._offense_scale(player, enemy, True))
        defense = 0 if ignore_defense else int(self._enemy_defense_with_guard(enemy) * self._defense_scale(player, enemy, False))
        return self._damage(attack, defense)

    def _enemy_damage(self, player: Player, enemy: Enemy, raw: int) -> int:
        """Enemy's attack value scaled by realm pressure and Dao matchup."""
        attack = int(raw * self._offense_scale(player, enemy, False))
        defense = int(self._player_defense(player) * self._defense_scale(player, enemy, True))
        return self._damage(attack, defense)

    def _pressure_view(self, player: Player, enemy: Enemy) -> Dict[str, Any]:
        """UI-visible realm-pressure and Dao match-up summary for the current round."""
        if self._dao is None:
            return {"gap": 0, "player_multiplier": 1.0, "enemy_multiplier": 1.0}
        pressure = self._dao.pressure(player, enemy)
        pressure["player_dao"] = self._dao.dao_name(player.dao_id)
        pressure["enemy_dao"] = self._dao.dao_name(enemy.dao_id)
        pressure["player_offense"] = round(self._offense_scale(player, enemy, True), 2)
        pressure["enemy_offense"] = round(self._offense_scale(player, enemy, False), 2)
        return pressure

    # -- damage & stats --------------------------------------------------
    def _deal_damage(self, target: Any, amount: int) -> tuple[int, int]:
        """Apply ``amount`` to a target, absorbing through its shield first.

        Returns ``(hp_dealt, shield_absorbed)``.
        """
        amount = max(0, int(amount))
        absorbed = min(target.shield, amount)
        if absorbed:
            target.shield -= absorbed
        return target.take_damage(amount - absorbed), absorbed

    def _roll_crit(self, player: Player) -> tuple[bool, float]:
        if self._stats is None:
            return False, 1.0
        chance = self._stats.crit_chance(player)
        if chance > 0 and self._rng.chance(chance):
            return True, self._stats.crit_multiplier(player)
        return False, 1.0

    def _regen(self, player: Player) -> tuple[int, int]:
        if self._stats is None:
            return 0, 0
        return self._stats.regen(player)

    def _player_defense(self, player: Player) -> int:
        """Effective player defense (passive buffs included) when a stats system is set."""
        if self._stats is not None:
            return self._stats.effective_defense(player)
        return player.defense

    def _player_attack(self, player: Player) -> int:
        """Effective player attack when a stats system is set."""
        if self._stats is not None:
            return int(self._stats.effective_stats(player).get("attack", player.attack))
        return player.attack

    def _enemy_attack_value(self, enemy: Enemy) -> int:
        """Enemy attack after any ``debuff_attack`` status."""
        debuff = enemy.statuses.get("debuff_attack")
        if debuff:
            return int(enemy.attack / debuff["magnitude"])
        return enemy.attack

    def _enemy_defense_with_guard(self, enemy: Enemy) -> int:
        """Enemy defense with the B.8 guard bonus applied (a guarding foe is hard to move)."""
        guard = enemy.statuses.get("guard")
        bonus = float(guard["magnitude"]) if guard else 0.0
        return int(self._enemy_defense_value(enemy) * (1.0 + max(0.0, bonus) / FOE_GUARD_MOMENTUM * FOE_GUARD_DEFENSE_BONUS))

    def _consume_guard_momentum(self, enemy: Enemy) -> float:
        """Consume a banked guard's momentum (the respected flow) into a press."""
        guard = enemy.statuses.pop("guard", None)
        if guard:
            return float(guard.get("magnitude", 0.0))
        return 0.0

    def _enemy_defense_value(self, enemy: Enemy) -> int:
        """Enemy defense after any ``debuff_defense`` status."""
        debuff = enemy.statuses.get("debuff_defense")
        if debuff:
            return int(enemy.defense / debuff["magnitude"])
        return enemy.defense

    def _damage(self, attack: int, defense: int) -> int:
        """Compute damage with light variance; always at least 1."""
        variance = self._rng.randint(-2, 3)
        return max(1, attack - defense // 2 + variance)

    def _turn(self, player: Player, enemy: Enemy, events: List[TurnEvent]) -> Dict[str, Any]:
        return {
            "event": EventType.COMBAT_TURN,
            "turn_events": events,
            "player_hp": player.hp,
            "player_max_hp": player.max_hp,
            "enemy_hp": enemy.hp,
            "enemy_max_hp": enemy.max_hp,
            "enemy_name": enemy.name,
            "insight": player.insight,
            "combo_stage": player.combo_stage,
            "pressure": self._pressure_view(player, enemy),
        }

    def _victory(self, player: Player, enemy: Enemy, events: List[TurnEvent]) -> Dict[str, Any]:
        player.exp += enemy.exp_reward
        return {
            "event": EventType.COMBAT_END,
            "outcome": "VICTORY",
            "enemy_name": enemy.name,
            "turn_events": events,
            "exp_reward": enemy.exp_reward,
            "loot_table": enemy.loot_table,
        }

    def _defeat(self, enemy: Enemy, events: List[TurnEvent]) -> Dict[str, Any]:
        return {
            "event": EventType.COMBAT_END,
            "outcome": "DEFEAT",
            "enemy_name": enemy.name,
            "turn_events": events,
        }
