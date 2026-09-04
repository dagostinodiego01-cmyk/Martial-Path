# Martial Path — Agent Fleet

A multi-agent workforce for the game, derived from the codebase knowledge graph
(`graphify-out/graph.json`: 2,184 nodes, 5,284 edges, 110 communities). Each
agent owns one area of the graph; the gatekeeper owns the exit.

Every agent is a **markdown file** in `.agents/*.md` (YAML frontmatter + body).
All agents inherit [rules/game-project.md](rules/game-project.md).

## Models (Freebuff)

| Model | Agents | Why |
|---|---|---|
| **GPT-5.6 Luna** | commit-gatekeeper, game-orchestrator, architecture-agent | judgment-heavy: final verdicts, decomposition, cross-layer contracts |
| **GLM 5.3 Flash** | combat, cultivation, world, economy, social, narrative, godot | bulk domain implementation |
| **Deepseek V4 Flash 07/31** | data, api, test-engineer | precision work: schemas, migrations, test authoring |

## Spawn graph

```
                         you / task
                             |
                      GAME-ORCHESTRATOR  (decompose -> dispatch -> integrate)
                       /   |   |   |   |   |   |   \
        combat cultivation world economy social narrative data api
              \__________|___|___|___|___|___/      |   |
                          godot  test-engineer  (follow-ups)
                          architecture (cross-layer changes)
                             |
                             v
                     COMMIT-GATEKEEPER  (verdict: APPROVE / REJECT)
                       \   |   |   |   |   |   |   /
                   (may spawn any domain agent for narrow patch fixes)
```

## The agents

| Agent | Owns (graph communities / files) | Spawn it for |
|---|---|---|
| **game-orchestrator** | everything; decomposes work orders | any multi-domain task, roadmap epics, parallel work |
| **commit-gatekeeper** | the Definition of Done; final verdict | automatically, before every commit |
| **combat-agent** | Combat & Enemies, Dao Combat, Engine Combat Mixin | fight resolution, dao counters, realm pressure, insight, enemy abilities |
| **cultivation-agent** | Cultivation subsystem (biggest: god node CultivationSystem, 87 edges) | body/essence training, breakthroughs, talents, origins, lifespan, closed-door |
| **world-agent** | Travel Service, Events & Encounters, Secret Realms, Alchemy | travel, encounters, loot, gathering/refining, secret realms, map |
| **economy-agent** | Shops & Currency, Items & Effects, Equipment System | shops, buy/sell, pricing, sets/durability, trainers/tuition |
| **social-agent** | Social & Dialogue, Quests & Acts, Sects, Morality | relationships, dialogue choices, boons, quest chains, sects, path locks |
| **narrative-agent** | Narrative Engine (64+ verbs, every EventType covered) | prose templates, voice consistency, template linter, new-event narration |
| **data-agent** | Data Validation, Data Registry, Seed Tools (208 skills / 236 enemies / 0 unreachable) | JSON content, validator rules, reachability, deterministic regeneration |
| **api-agent** | FastAPI Server, Save & Persistence, Meta Service, backend.spec | HTTP contract, save round-trip/migrations, meta progression, packaging |
| **godot-agent** | frontend-godot/ (NOT in graph corpus — see note) | Godot rendering of new actions/events, overlays, GDScript fixes |
| **test-engineer** | tests/ (48 files; baseline 529 passed, 3 skipped) | authoring tests, coverage sweeps, determinism property tests, red-suite triage |
| **architecture-agent** | Action/EventType constants, result types, GameEngine mixins, registry | new contracts, layering, cross-domain refactors |

## Usage

Spawn agents by name from your Freebuff session:

- Single-domain work — go straight to the specialist:
  "@combat-agent make dao debates a non-lethal alternative to duels"
- Multi-domain / roadmap work — go through the orchestrator:
  "@game-orchestrator implement ROADMAP.md B.6 stances + combos"

The orchestrator dispatches specialists, integrates their results, and always
finishes by spawning the **commit-gatekeeper**. A task is done only when the
verdict block ends with `VERDICT: APPROVE`.

## Gatekeeper protocol (summary)

1. Reads every changed file in full (not just diffs).
2. Enforces hard rules: layering direction, systems purity, Godot-only UI,
   data-driven content, frozen CLI/PySide untouched.
3. Runs the evidence: full test suite, `validate_all_game_data()` == 0 errors,
   Godot parse check when GDScript changed.
4. Spawns domain auditors for any domain whose files changed.
5. Issues `APPROVE | REJECT | REJECT-WITH-PATCH` with file+line-referenced
   blockers. Never approves its own patch without re-running verification.

## Notes

- **graphify-out/ is an operational dependency of this fleet**, not disposable
  output: specialists cite its communities, the orchestrator uses it for blast
  radius, and the gatekeeper uses its god nodes (Player 286 edges, EventType 99,
  CultivationSystem 87, GameEngine 77, GameDataRegistry 70, CombatSystem 61).
  Rebuild it with `/graphify --update` after major refactors.
- **Godot is not in the graph corpus** (graphify scanned game/, tests/, tools/).
  godot-agent sources its conventions from handover.md and the GUI master
  conventions instead. Re-run graphify with frontend-godot/ included if you want
  it graphed.
- Frontmatter field names (`name`, `description`, `model`, `tools`,
  `spawner_prompt`, `spawnable_agents`) follow the existing
  `.agents/skills/graphify/SKILL.md` convention. Adjust the keys here and in the
  agent files if your client expects different ones.
