---
description: 'Cultivation and progression rules: data-driven realms, breakthrough logic in core not UI, stable realm/stage IDs. Use when editing cultivation or progression.'
applyTo: 'game/systems/**,game/data/**'
---

# 06 — Cultivation and Progression Rules

The cultivation system must be modular, expandable, and data-driven.

Progression should not be a simple linear XP bar unless specifically required.

## Cultivation May Include

- Realm.
- Stage.
- Foundation quality.
- Comprehension.
- Body refinement.
- Soul strength.
- Bloodline.
- Laws or concepts.
- Dao comprehension.
- Bottlenecks.
- Tribulations.
- Resources consumed.
- Technique compatibility.

## Progression Rules

1. Cultivation realms must be defined in data.
2. Breakthrough logic must exist in core gameplay systems, not UI.
3. UI may show breakthrough chance but must not calculate it directly.
4. Breakthroughs should consider more than XP.
5. Foundation quality should affect long-term growth.
6. Rare resources may increase chance or reduce backlash.
7. Failed breakthroughs may have consequences.
8. Different characters may have different growth rates.
9. NPC progression should be possible using the same core system as the player.
10. Avoid hard-coding realm names into logic.
11. Realm and stage IDs should be stable.
12. Display names for realms may change without breaking saves.

## Design Intent

Cultivation should feel like a strategic system with choices, risks, and long-term consequences rather than a basic level-up mechanic.
