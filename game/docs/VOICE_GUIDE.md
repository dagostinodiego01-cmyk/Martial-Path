# Martial Path — Voice & Prose Guide (ROADMAP A.6)

How narrative prose in `game/data/narrative_templates.json` must sound, and the
lore glossary the validator enforces. Written for template authors (human or
agent); enforced by `game/validation/narrative_lint.py`.

## Tone

- **xianxia register**: cultivation, qi, meridians, dantian, realms, dao, face,
  seclusion, insight. The prose should feel like a translated cultivation novel,
  not a stat screen.
- **Second person, present tense** for actions ("You sink into a low stance…");
  **reflective tone** for breakthroughs and death; **immediacy** for combat.
- **Concrete and physical** over abstract: bones, breath, frost, tide, ember.
  Avoid explaining mechanics in prose — the UI shows numbers; the prose shows
  texture.
- **Never generated-looking**: no repeated sentence openers within one verb
  pool, no Mad-Libs artifacts (a slot must read naturally in every variant),
  no list-of-features phrasing.

## Hard voice rules (validator-enforced)

1. **No gamey/out-of-world vocabulary** in any template: mana, chi, ki, level,
   xp, respawn, buff, nerf, grind, quest log, skill tree, save file, load game,
   character sheet, stats, ui, menu. (Blocklist: `GAMEY_TERMS` in
   `game/validation/narrative_lint.py`.)
2. **No brace artifacts**: the only `{...}` groups in a template are declared
   `{snake_case}` slots. JSON example fragments, code, or leftover braces are
   linter errors.
3. **Glossary conformance** (see below): every `{realm}`, `{dao}`, `{tier}`,
   and `{season}` value that reaches prose must be an approved term.
4. Every EventType keeps >= 1 template; core verbs keep >= 3 weighted variants
   (existing A.1/A.5 floors).

## Lore glossary (`game/data/lore_glossary.json`)

A data file of approved in-world terms. The validator checks values against it;
prose authors use it as the canon spelling list.

```
{
  "terms": [
    {
      "term": "Qi Condensation",
      "slot": "realm",
      "kind": "realm",
      "summary": "First stage of Essence Gathering where breath is woven into a core."
    }
  ]
}
```

Fields:

- `term` — the exact approved display string (stable, human-readable).
- `slot` — which narrative slot the term is legal for (`realm`, `dao`, `tier`,
  `season`, or `any`).
- `kind` — free-form grouping for authors (`realm`, `dao`, `npc_tier`,
  `season`, `term`).
- `summary` — one line of in-world meaning; never rendered, authoring aid only.

The shipped catalogue is seeded from the *display names already in the game
data* (cultivation realms, the 12 daos, NPC relationship tiers, seasons), so
prose can only use vocabulary the rest of the game already uses.

## Sameness metric (A.6 done-criterion)

A 100-event simulated run must narrate through >= 2 *distinct template
variants* for every visited verb (property test:
`tests/test_narrative_voice.py::test_100_event_run_meets_sameness_floor`).
Weighted pools with duplicate-phrased variants fail this even when structurally
distinct, so keep phrasing genuinely different.

## Authoring checklist

- [ ] Variant reads naturally with every legal value of each slot it uses.
- [ ] No word from the gamey blocklist.
- [ ] Realms/daos/tiers/seasons spelled exactly as in the glossary.
- [ ] At least 2 variants per verb (3 for core verbs).
- [ ] `python tools/narrative_lint.py` exits 0.
