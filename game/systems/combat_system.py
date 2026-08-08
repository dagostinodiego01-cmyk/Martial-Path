"""Combat system.

Implements turn-based, player-vs-enemy combat as a set of *rule calculations*.
Each public method resolves one player action plus the enemy's response (a full
round) and returns a structured result:

* ``COMBAT_TURN`` — the round resolved and the fight continues.
* ``COMBAT_END``  — the fight ended (``VICTORY`` / ``DEFEAT`` / ``FLED``).

The engine drives *when* these are called and handles loot/defeat consequences;
the combat system only computes what happens mechanically. No UI, no formatting.
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


class CombatSystem:
    """Resolves individual combat rounds between the player and an enemy."""

    def __init__(self, rng: RNG, stats: Optional["StatsSystem"] = None) -> None:
        self._rng = rng
        self._stats = stats

    def attack(self, player: Player, enemy: Enemy) -> Dict[str, Any]:
        """Player performs a basic attack, then the enemy retaliates if alive."""
        dealt = enemy.take_damage(self._damage(self._player_attack(player), enemy.defense))
        events: List[TurnEvent] = [
            {"actor": "PLAYER", "action": "ATTACK", "damage": dealt, "target_hp": enemy.hp}
        ]
        return self._resolve_round(player, enemy, events)

    def use_skill(self, player: Player, enemy: Enemy, skill: Skill) -> Dict[str, Any]:
        """Player invokes an active skill, then the enemy retaliates if alive.

        Qi cost and cooldown validation are the engine's responsibility; by the
        time this is called the activation has already been paid for.
        """
        if skill.effect == "damage":
            raw = int(self._player_attack(player) * skill.scaling)
            dealt = enemy.take_damage(self._damage(raw, enemy.defense))
            events: List[TurnEvent] = [
                {
                    "actor": "PLAYER",
                    "action": "SKILL",
                    "skill": skill.name,
                    "damage": dealt,
                    "target_hp": enemy.hp,
                }
            ]
        else:
            events = [
                {"actor": "PLAYER", "action": "SKILL", "skill": skill.name, "note": "no_combat_effect"}
            ]
        return self._resolve_round(player, enemy, events)

    def enemy_turn_only(self, player: Player, enemy: Enemy) -> Dict[str, Any]:
        """Resolve just the enemy's turn (used after the player uses an item)."""
        events = [self._enemy_attack(player, enemy)]
        if not player.is_alive():
            return self._defeat(enemy, events)
        return self._turn(player, enemy, events)

    def flee(self, player: Player, enemy: Enemy) -> Dict[str, Any]:
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
        if not player.is_alive():
            return self._defeat(enemy, events)
        return self._turn(player, enemy, events)

    # -- internal helpers -------------------------------------------------
    def _resolve_round(self, player: Player, enemy: Enemy, events: List[TurnEvent]) -> Dict[str, Any]:
        """After the player's action, check for victory then run the enemy turn."""
        if not enemy.is_alive():
            return self._victory(player, enemy, events)
        events.append(self._enemy_attack(player, enemy))
        if not player.is_alive():
            return self._defeat(enemy, events)
        return self._turn(player, enemy, events)

    def _enemy_attack(self, player: Player, enemy: Enemy) -> TurnEvent:
        dealt = player.take_damage(self._damage(enemy.attack, self._player_defense(player)))
        return {
            "actor": "ENEMY",
            "action": "ATTACK",
            "damage": dealt,
            "target_hp": player.hp,
            "enemy_name": enemy.name,
        }

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
