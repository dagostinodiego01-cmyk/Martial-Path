---
description: 'UI separation rules: UI displays state and calls services/engine only, never computes gameplay. Use when editing UI or frontend scripts.'
applyTo: 'game/ui/**,frontend-godot/**'
---

# 02 — UI Separation Rules

The UI must be treated as a replaceable display layer.

## UI Scripts May

UI scripts may:

1. Display character state.
2. Display player choices.
3. Display dialogue.
4. Send selected actions to services.
5. Refresh visible panels.
6. Play animations or sounds.
7. Navigate between screens.
8. Show warnings, tooltips, and feedback.

## UI Scripts Must Not

UI scripts must not:

1. Calculate cultivation breakthroughs.
2. Determine relationship changes.
3. Resolve combat.
4. Decide NPC memory or personality changes.
5. Encode morality rules.
6. Store long-term game state.
7. Contain hard-coded character logic.
8. Directly mutate save state except through approved services.
9. Contain quest progression logic.
10. Contain faction reputation logic.

## Preferred Interaction Flow

Example: player clicks a dialogue option.

```text
UI
└── captures selected option
    └── calls DialogueService.select_option(option_id)
        └── DialogueService validates option
            └── applies relationship/morality/event effects
                └── returns updated dialogue state
                    └── UI renders new dialogue state
```

## Button Rule

Every meaningful button press should call a service or controller method.

Do not allow UI scenes to directly modify:

- Relationship values.
- Morality values.
- NPC trust.
- NPC hostility.
- Story flags.
- Quest completion.
- Cultivation realm.
- Inventory contents.
