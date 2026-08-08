---
description: 'Dialogue system rules: data-driven, condition-gated dialogue resolved by a service; UI only renders returned options. Use when building dialogue content or logic.'
applyTo: 'game/systems/**,game/data/**'
---

# 07 — Dialogue System Rules

Dialogue should be generated or selected according to character state, personality, context, and relationship.

## Dialogue Entry Fields

Dialogue entries should support fields such as:

- `speaker_id`
- `context_tags`
- `required_flags`
- `blocked_flags`
- `relationship_requirements`
- `morality_requirements`
- `faction_requirements`
- `cultivation_difference_rules`
- `personality_bias`
- `response_options`
- `effects`
- `next_node_id`

## Dialogue Rules

1. Dialogue text should not be stored in UI code.
2. Dialogue options should have clear effects.
3. Dialogue choices can affect relationship, trust, respect, fear, resentment, morality, reputation, quest state, and faction standing.
4. Dialogue should support conditional branches.
5. Important NPCs should have unique dialogue style.
6. Generic NPCs may use templates.
7. Dialogue Service should resolve available options.
8. UI should only display options returned by Dialogue Service.
9. Player choices should be logged if story-relevant.
10. Dialogue should never directly mutate state from the UI layer.
11. Dialogue should support failure conditions and locked choices.
12. Hidden requirements should be used sparingly and intentionally.

## Dialogue Style Rules

NPC dialogue style should reflect:

- Personality.
- Faction.
- Status.
- Relationship with the player.
- Current emotional state.
- Relative power difference.
