"""NPC interaction: talk, dialogue choices, boons, and character combat."""
from __future__ import annotations

from typing import Any, Dict

from game.core.constants import EventType, MODE_COMBAT
from game.core.results import BoonResult, CharacterInteractionResult, DialogueChoiceResult


class SocialMixin:
    """Relationship-gated NPC verbs and the spar/duel entry points."""

    def _talk_to_character(self, character_id: str) -> Dict[str, Any]:
        if not character_id:
            return {"event": EventType.ERROR, "reason": "NO_CHARACTER_SPECIFIED"}
        character = self.character_service.get_character(character_id)
        if character is None:
            return {"event": EventType.ERROR, "reason": "UNKNOWN_CHARACTER", "character_id": character_id}
        hooks = character.get("gameplay_hooks", {})
        if not hooks.get("can_talk", False):
            return {"event": EventType.ERROR, "reason": "NOT_AVAILABLE", "character_id": character_id}
        context = self.character_service.get_dialogue_context(character_id, self.player)
        if context is None:
            return {"event": EventType.ERROR, "reason": "UNKNOWN_CHARACTER", "character_id": character_id}
        message_parts = [
            context.get("intro_text") or context.get("repeat_text") or "They acknowledge you.",
            context.get("morality_reaction", ""),
            context.get("relationship_behavior", ""),
        ]
        message = " ".join(part for part in message_parts if part).strip()
        result = CharacterInteractionResult(
            interaction="talk",
            character_id=character_id,
            name=context.get("name", character_id),
            dialogue_context=context,
            player_message=message,
            choices=self.character_service.dialogue_choices(character_id, self.player),
            speech_notes=context.get("ai_prompt_notes") or None,
        ).to_dict()
        result["narrative"] = self.describe_npc(character_id)
        # E.5: gossip travels -- an unlearned rumor surfaces in conversation.
        result = self._rumor_hook_for(character_id, result)
        return result

    def _dialogue_choose(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a chosen dialogue option's relationship/morality/reputation deltas."""
        character_id = action.get("character_id", "")
        choice_id = action.get("choice_id", "")
        if not character_id or not choice_id:
            return {"event": EventType.ERROR, "reason": "NO_CHOICE_SPECIFIED"}
        choice = self.character_service.get_dialogue_choice(character_id, choice_id, self.player)
        if choice is None:
            return {
                "event": EventType.ERROR,
                "reason": "CHOICE_NOT_AVAILABLE",
                "character_id": character_id,
                "choice_id": choice_id,
            }

        relationship = None
        relationship_delta = choice.get("relationship_delta") or {}
        if relationship_delta:
            relationship = self.relationships.adjust(
                self.player.relationships, character_id, relationship_delta
            )

        morality = self.morality.adjust(self.player.morality, int(choice.get("morality_delta", 0)))
        self.player.morality = morality["morality"]

        reputation_delta = int(choice.get("reputation_delta", 0))
        self.player.reputation += reputation_delta
        # Reputation can satisfy a quest's unlock gate without any notify event.
        self.quests.check_unlocks(self.player)

        return DialogueChoiceResult(
            character_id=character_id,
            choice_id=choice_id,
            name=str(choice.get("character_name", character_id)),
            player_message=str(choice.get("response", "")),
            relationship=relationship,
            morality=morality,
            reputation=self.player.reputation,
            reputation_delta=reputation_delta,
        ).to_dict()

    def _receive_boon(self, character_id: str) -> Dict[str, Any]:
        """Grant an NPC's currently-available relationship reward (one-time)."""
        if not character_id:
            return {"event": EventType.ERROR, "reason": "NO_CHARACTER_SPECIFIED"}
        available = self.character_service.available_reward(character_id, self.player)
        if available is None:
            return {"event": EventType.ERROR, "reason": "NO_REWARD_AVAILABLE", "character_id": character_id}
        reward = available.get("reward", {})
        granted: Dict[str, Any] = {}
        if "gold" in reward:
            amount = int(reward["gold"])
            self.player.gold += amount
            granted["gold"] = amount
        if "exp" in reward:
            amount = int(reward["exp"])
            self.player.exp += amount
            granted["exp"] = amount
        item_id = reward.get("item_id")
        if item_id:
            count = int(reward.get("count", 1))
            self.inventory.add_item(self.player, item_id, count)
            granted["items"] = {item_id: count}
        skill_id = reward.get("skill_id")
        if skill_id:
            learned = self.techniques.learn_skill(self.player, skill_id, source="boon")
            if learned.get("event") == EventType.SKILL_LEARNED:
                granted["skill_id"] = skill_id
        # Mark the reward claimed so ``once`` rewards never fire twice.
        self.relationships.remember(
            self.player.relationships,
            character_id,
            action="received_reward",
            flag=f"reward_{available['index']}",
        )
        result = BoonResult(
            character_id=character_id,
            name=available.get("name", character_id),
            player_message=str(available.get("message") or "They offer you a gift in recognition of your bond."),
            reward=granted,
            wallet={"gold": self.player.gold},
        ).to_dict()
        result["narrative"] = self.describe_npc(character_id)
        return result

    def _start_character_combat(self, character_id: str, interaction: str) -> Dict[str, Any]:
        if not character_id:
            return {"event": EventType.ERROR, "reason": "NO_CHARACTER_SPECIFIED"}
        gate = (
            self.character_service.can_spar(character_id, self.player)
            if interaction == "spar"
            else self.character_service.can_duel(character_id, self.player)
        )
        if not gate.get("allowed"):
            return {
                "event": EventType.ERROR,
                "reason": gate.get("reason", "NOT_AVAILABLE"),
                "character_id": character_id,
            }
        enemy_id = gate.get("enemy_id", "")
        if not enemy_id:
            return {"event": EventType.ERROR, "reason": "NO_CHARACTER_ENEMY", "character_id": character_id}
        enemy = self._spawn_character_enemy(enemy_id)
        if enemy is None:
            return {"event": EventType.ERROR, "reason": "UNKNOWN_ENEMY", "character_id": character_id, "enemy_id": enemy_id}
        self._current_enemy = enemy
        self._mode = MODE_COMBAT
        self._cooldowns = {}
        self._combat_is_spar = interaction == "spar"
        self.player.statuses.clear()
        self.player.shield = 0
        self.combat.begin_combat(self.player)
        label = "sparring match" if interaction == "spar" else "duel"
        return {
            "event": EventType.COMBAT,
            "interaction": interaction,
            "character_id": character_id,
            "enemy": self._enemy_view(enemy),
            "text": f"You begin a {label} with {enemy.name}.",
        }
