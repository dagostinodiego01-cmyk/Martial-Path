---
description: 'AI response and output-discipline rules: structured change summaries (what/why/files/follow-ups), focused edits, no vague claims. Applies to all project changes.'
applyTo: '**'
---

# 12 — AI Assistant Response Rules

When generating code or project changes, the AI must respond in a structured way.

## Required Response Structure

For every meaningful change, provide:

1. Summary of what was changed.
2. Files created.
3. Files modified.
4. Architecture impact.
5. Assumptions made.
6. Follow-up tasks.
7. Tests or validation steps.

## Code Generation Rules

When creating new code:

1. Do not create large unexplained files.
2. Prefer smaller focused modules.
3. Avoid mixing many unrelated features in one change.
4. Add comments only where useful.
5. Use clear names.
6. Do not silently remove existing functionality.
7. If replacing a file, explain why.
8. If uncertain, add a TODO rather than inventing hidden behaviour.
9. Keep the codebase maintainable.
10. Respect all architecture rules.
11. Do not introduce dependencies without explaining why.
12. Prefer simple, testable implementations.

## Refactor Behaviour

If existing code violates the project rules:

1. Identify the violation.
2. Explain why it is a problem.
3. Propose a focused refactor.
4. Avoid expanding the bad pattern.
5. Preserve functionality unless explicitly told otherwise.

## Output Discipline

The AI should avoid vague responses such as:

- "I updated everything."
- "This should work."
- "I made some improvements."

Instead, be specific about what changed and why.
