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


class CombatSystem:
    """Resolves individual combat rounds between the player and an enemy."""

    def __init__(self, rng: RNG, stats: Optional["StatsSystem"] = None) -> None:
        self._rng = rng
        self._stats = stats

    def attack(self, player: Player, enemy: Enemy, spar: bool = False) -> Dict[str, Any]:
        """Player performs a basic attack, then the enemy retaliates if alive."""
        raw = int(self._player_attack(player))
        is_crit, mult = self._roll_crit(player)
        raw = int(raw * mult)
        dealt, _ = self._deal_damage(enemy, self._damage(raw, self._enemy_defense_value(enemy)))
        event: TurnEvent = {"actor": "PLAYER", "action": "ATTACK", "damage": dealt, "target_hp": enemy.hp}
        if is_crit:
            event["crit"] = True
        return self._resolve_round(player, enemy, [event], spar)

    def use_skill(self, player: Player, enemy: Enemy, skill: Skill, spar: bool = False) -> Dict[str, Any]:
        """Player invokes an active skill, then the enemy retaliates if alive.

        Qi cost and cooldown validation are the engine's responsibility; by the
        time this is called the activation has already been paid for.
        """
        events = self._apply_active_skill(player, enemy, skill)
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
            self._enemy_attack(player, enemy),
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
        if effect in ("damage", "true_damage", "aoe_damage"):
            return self._hit(player, enemy, skill, ignore_defense=effect == "true_damage")
        if effect == "execute":
            return self._hit(player, enemy, skill, execute=True)
        if effect == "life_steal":
            return self._hit(player, enemy, skill, life_steal=True)
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
    ) -> List[TurnEvent]:
        """Resolve a damage-dealing skill hit and return its event."""
        raw = int(self._player_attack(player) * skill.scaling)
        is_crit, mult = self._roll_crit(player)
        raw = int(raw * mult)
        if execute and enemy.max_hp > 0 and enemy.hp < enemy.max_hp * EXECUTE_THRESHOLD:
            raw *= 2
        dealt, absorbed = self._deal_damage(enemy, self._damage(raw, 0 if ignore_defense else self._enemy_defense_value(enemy)))
        event: TurnEvent = {"actor": "PLAYER", "action": "SKILL", "skill": skill.name, "damage": dealt, "target_hp": enemy.hp}
        if absorbed:
            event["shield_absorbed"] = absorbed
        if is_crit:
            event["crit"] = True
        if life_steal and dealt > 0:
            event["life_steal"] = player.heal(dealt)
        return [event]

    # -- round resolution ------------------------------------------------
    def _resolve_round(self, player: Player, enemy: Enemy, events: List[TurnEvent], spar: bool = False) -> Dict[str, Any]:
        """After the player's action, apply regen, run the enemy phase, resolve end."""
        hp_regen, qi_regen = self._regen(player)
        if hp_regen:
            player.heal(hp_regen)
        if qi_regen:
            player.restore_qi(qi_regen)
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
        """Enemy acts (or skips when stunned), then its timed effects tick."""
        stun = enemy.statuses.get("stun")
        if stun:
            events.append({"actor": "ENEMY", "action": "STUNNED", "enemy_name": enemy.name})
            self._expire(enemy, "stun")
        else:
            events.append(self._enemy_attack(player, enemy))
        self._tick_enemy_statuses(enemy, events)

    def _enemy_attack(self, player: Player, enemy: Enemy) -> TurnEvent:
        dealt, _ = self._deal_damage(player, self._damage(self._enemy_attack_value(enemy), self._player_defense(player)))
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
        return event

    def _tick_enemy_statuses(self, enemy: Enemy, events: List[TurnEvent]) -> None:
        """Apply per-turn enemy effects (dot) and decrement remaining turns."""
        for effect in list(enemy.statuses):
            if effect == "dot_damage":
                dealt, _ = self._deal_damage(enemy, int(enemy.statuses[effect]["magnitude"]))
                events.append({"actor": "ENEMY", "action": "DOT", "damage": dealt, "target_hp": enemy.hp, "enemy_name": enemy.name})
            self._expire(enemy, effect)

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
