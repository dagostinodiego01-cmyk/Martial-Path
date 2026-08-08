# Copilot Instructions — Martial Path Cultivation RPG

A data-driven cultivation (xianxia) RPG. The authoritative game logic is a Python
engine (`game/`) with CLI, PySide6, and FastAPI (`game/api/`) frontends, plus a
Godot 4 client (`frontend-godot/`) that talks to the API. Keep gameplay logic in
the engine/systems — never in a UI.

## Project rules

Detailed rules live as auto-applied instruction files in `.github/instructions/`.
Each is scoped with `applyTo`, so the relevant ones load automatically based on
the files being worked on. Open the matching file before non-trivial work.

| #  | Instruction file                                    | Applies to (`applyTo`)          | Topic |
|----|-----------------------------------------------------|---------------------------------|-------|
| 00 | `instructions/00-global.instructions.md`            | all files                       | Global behaviour & project intent |
| 01 | `instructions/01-architecture.instructions.md`      | `game/**`, `frontend-godot/**`  | Layered architecture & dependencies |
| 02 | `instructions/02-ui-separation.instructions.md`     | `game/ui/**`, `frontend-godot/**` | UI is a display layer only |
| 03 | `instructions/03-data-driven-design.instructions.md`| `game/data/**`, `**/*.json`     | Data-driven content & stable IDs |
| 04 | `instructions/04-godot-export.instructions.md`      | `frontend-godot/**`             | Godot & Windows `.exe` export |
| 05 | `instructions/05-npc-ai-relationship.instructions.md`| `game/systems/**`, `game/data/**` | NPC AI & relationships |
| 06 | `instructions/06-cultivation-progression.instructions.md`| `game/systems/**`, `game/data/**` | Cultivation & progression |
| 07 | `instructions/07-dialogue-system.instructions.md`   | `game/systems/**`, `game/data/**` | Dialogue system |
| 08 | `instructions/08-save-system.instructions.md`       | `game/**`                       | Save system |
| 09 | `instructions/09-testing-validation.instructions.md`| `tests/**`, `game/**`           | Testing & validation |
| 10 | `instructions/10-copyright-originality.instructions.md`| all files                    | Copyright & originality |
| 11 | `instructions/11-documentation.instructions.md`     | `**/*.md`                       | Documentation upkeep |
| 12 | `instructions/12-ai-response.instructions.md`       | all files                       | AI response & output discipline |

## Cross-cutting essentials (always apply)

- Keep gameplay logic out of UI/frontend code; UIs display state and send commands only.
- Prefer data-driven content (JSON / data modules) with stable IDs over hard-coded values.
- Keep changes focused; summarise what changed, why, files touched, and follow-ups.
- Original lore only — no copyrighted names, sects, techniques, or dialogue.
