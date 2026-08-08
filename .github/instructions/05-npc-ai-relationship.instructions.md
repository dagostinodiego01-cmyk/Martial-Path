---
description: 'NPC AI and relationship rules: personality/memory/faction-driven behaviour with multiple emotional variables. Use when building NPC, relationship, or morality systems.'
applyTo: 'game/systems/**,game/data/**'
---

# 05 — NPC AI and Relationship Rules

NPC behaviour must be driven by personality, relationship state, morality, memory, faction, and current world context.

## Persistent NPC State

Each important NPC should maintain state including:

- `relationship_score`
- `trust`
- `fear`
- `respect`
- `resentment`
- `loyalty`
- `suspicion`
- `debt_to_player`
- `known_player_actions`
- `faction_opinion`
- `personal_memory_flags`

## Response Influences

NPC responses should be influenced by:

1. Personality traits.
2. Player morality.
3. Player reputation.
4. Previous choices.
5. Faction alignment.
6. Cultivation difference.
7. Current story arc.
8. Whether the NPC benefits from helping the player.
9. Whether the NPC fears, respects, likes, or distrusts the player.
10. Whether the NPC has conflicting obligations.

## Behaviour Rules

1. Do not make all NPCs respond the same way.
2. Do not base dialogue only on relationship score.
3. Relationship score is not enough; use multiple emotional variables.
4. Important NPCs should remember major player actions.
5. Characters should not instantly trust the player without reason.
6. Arrogant characters should react differently from cautious or loyal characters.
7. Powerful characters should care about status, face, reputation, and benefit.
8. Weak characters may respond more strongly to fear, gratitude, or protection.
9. NPCs may lie, withhold information, exaggerate, or manipulate depending on personality.
10. NPC behaviour should be explainable from stored state.
