---
description: 'Global behaviour and project intent for the cultivation RPG: clean data-driven architecture, keep gameplay logic out of UI, focused changes. Applies to all work.'
applyTo: '**'
---

# 00 — Global Behaviour Rules

You are assisting with the development of a text-heavy cultivation RPG inspired by xianxia progression fantasy.

Always follow these rules:

1. Prioritise clean architecture over quick implementation.
2. Do not put gameplay logic directly inside UI scenes.
3. Do not hard-code characters, locations, skills, items, sects, realms, or dialogue into UI scripts.
4. Prefer data-driven systems using JSON, Resource files, or clearly separated data modules.
5. Keep systems modular enough that the project could later move away from Godot if required.
6. When adding a new feature, update the relevant documentation.
7. When changing architecture, explain what changed and why.
8. Avoid unnecessary dependencies.
9. Do not introduce backward compatibility unless specifically requested.
10. Keep names clear, descriptive, and consistent.
11. When uncertain, choose the structure that makes testing and future migration easier.

## Default Project Intent

The game should be:

- Exportable as a standalone Windows `.exe`.
- Data-driven.
- Easy to expand with new NPCs, factions, realms, techniques, locations, quests, and dialogue.
- Structured so the UI can be replaced later without rewriting the game logic.

## AI Behaviour

When making changes, the AI must:

1. Respect the existing architecture unless asked to refactor it.
2. Explain any architectural decision that affects future maintainability.
3. Keep changes focused.
4. Avoid creating large monolithic files.
5. Prefer clear, explicit implementation over clever shortcuts.
6. Leave TODO comments only for genuinely incomplete future work.
