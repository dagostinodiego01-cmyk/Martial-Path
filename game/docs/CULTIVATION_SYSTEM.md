# Cultivation System

Martial Path uses two separate cultivation tracks that can progress unevenly:

- Body Transformation: physical refinement and body stability.
- Essence Gathering: qi, dantian, true essence density, and inner world growth.

The authoritative logic lives in `game/systems/cultivation_system.py`. UI layers call the engine or `CultivationService` and render returned dictionaries; they do not calculate progress, breakthrough success, or balance.

## State

Cultivation state is stored on the player as `cultivation_state`:

```json
{
  "body_transformation": {
    "realm_id": "mortal",
    "progress": 0.0,
    "foundation": 10.0,
    "opened_gates": [],
    "opened_stars": [],
    "marrow_percent": 0.0,
    "body_strength": 1.0,
    "breakthrough_failures": 0,
    "cultivation_strain": 0.0,
    "foundation_stability": 100.0,
    "daily_cultivation_count": 0,
    "last_cultivation_day": 1
  },
  "essence_gathering": {
    "realm_id": "houtian",
    "substage": "Early",
    "progress": 0.0,
    "foundation": 10.0,
    "dantian_capacity": 10.0,
    "true_essence_density": 1.0,
    "circulation_stability": 1.0,
    "life_destruction_fall": 0,
    "inner_world_development": 0.0,
    "breakthrough_failures": 0,
    "cultivation_strain": 0.0,
    "foundation_stability": 100.0
  }
}
```

Legacy `player.progress` is kept as a compatibility alias for Body Transformation progress. The player also stores `current_day`; normal training does not advance the day, while recovery actions such as rest and stabilising foundation do.

New players also roll a starting fate: a `martial_talent_id` and `body_talent_id`.
Only the stable IDs are saved. The current data definitions are resolved at
runtime so tuning can change without rewriting saves. Characters also begin at
`age_years` 12.

## Data

Realm data is loaded from:

- `game/data/cultivation/body_transformation_realms.json`
- `game/data/cultivation/essence_gathering_realms.json`
- `game/data/cultivation/cultivation_config.json`

The Body Transformation track begins at `mortal` (display name `Mortal`), a
pre-cultivation state with a small base HP bonus. Only Body Tempering is available
until the player advances beyond it.

`Pulse Condensation` belongs to Body Transformation only, as
`body_pulse_condensation`, between `bone_forging` and `tempering_marrow`.
Essence Gathering begins at `houtian`, but Essence training and breakthroughs are
locked until Body Transformation satisfies the breakthrough requirements for
`body_pulse_condensation`, or has already advanced beyond it. Clearing that
threshold only opens the Essence Gathering path; it does not advance or clear
`houtian`. The engine exposes `essence_unlocked` in the cultivation state so UIs
can show the locked state.

Both tracks use data-driven progress requirements. Body realms define `required_progress`; Essence realms define `required_progress` for each substage/fall requirement. Higher realms require more progress, and UI state exposes both raw progress and required progress so frontends can render `current / required` without calculating rules.

Starting talent data is loaded from:

- `game/data/cultivation/martial_talents.json`
- `game/data/cultivation/body_talents.json`

The Martial Talent primarily affects Essence cultivation; the Body Talent
primarily affects Body cultivation. These two tables replace the former Spiritual
Root and Physique traits and carry the same cultivation multipliers. Each entry
carries a `tier` linking into the talent ladder (`talents.json`).

## Starting Fate

New games automatically roll and assign a Martial Talent and a Body Talent before
gameplay begins. The two tracks are rolled independently, so a character can be
gifted in one path and weak in the other. The engine stores only
`martial_talent_id` and `body_talent_id` on the player and exposes read-only
talent views for UI display. Rerolls and manual selection are future features.

## Talent Tiers

An innate two-track talent ladder describes a cultivator's potential ceiling. It
is data-driven and read-only: `game/data/cultivation/talents.json` lists 20 tiers
plus a final Apex tier (tier 21). Every tier shares a single index across both
tracks, so one tier value resolves to both a Martial talent name and a
Body-cultivation talent name, alongside the reachable `cultivation_realm` and a
`max_lifespan_years`.

`TalentSystem` (`game/systems/talent_system.py`) resolves ladder entries into
UI-safe views by tier index (`tier_view`) or stable ID (`view_by_id`), and lists
the whole ladder (`all_tiers`). The engine exposes it as `engine.talents`. A
`max_lifespan_years` of `null` means the tier is effectively immortal/eternal, so
UIs render `lifespan_display` for player text. Canon-accurate lifespans (Xiantian,
Divine Sea, Empyrean, True Divinity) are flagged `source: "canon"`; scaled values
are `"extrapolated"` and tier 1 is `"mixed"`.

Each rolled Martial/Body Talent carries a `tier` that links into this ladder for
its grade name and lifespan potential; the character's current maximum lifespan,
however, comes from their Essence realm (see Lifespan below), not from talent.

## Lifespan

Every character has an `age_years` (new games start at 12). Time-consuming actions
-- body/essence training, breakthrough attempts, stabilising, resting, meditating
-- advance age by a data-driven cost from `cultivation_config.json`
(`lifespan.time_costs`, in years).

Maximum lifespan follows the current **Essence Gathering** realm: each essence
realm defines `max_lifespan_years`, and pre-essence characters use
`lifespan.mortal_base_lifespan_years` (100). Breaking through to a higher essence
realm therefore extends the lifespan cap. `beyond_divinity` has a `null` cap
(effectively immortal). When `age_years` reaches the current cap the engine
returns a `PLAYER_DIED` result and ends the run. The pure `LifespanSystem` owns
these rules; the engine ages the player after each qualifying action and surfaces
a read-only `lifespan` view (age, max, remaining years) in the player state.

## Training

Body training mutates only `cultivation_state.body`. Essence training mutates only `cultivation_state.essence`. Essence Gathering cannot be trained until Body Transformation has satisfied Pulse Condensation's breakthrough requirements. Once unlocked, each path can contribute a small modifier to the other path's training formula, but it does not directly advance the other path.

Repeated Body training in the same backend day uses diminishing returns from `cultivation_config.json`. Body training also increases `cultivation_strain`; it no longer grants permanent `body_strength` or combat stats. Permanent body stat gains are awarded only by successful Body breakthroughs, from the target realm's `success_stat_gains` data.

Essence Gathering has its own fatigue and stability system mirroring the body track: Essence training increases the Essence track's `cultivation_strain` (fatigue), and the Essence track carries its own `foundation_stability` (starting at 100). Both are tuned by the `essence_progression` block in `cultivation_config.json`.

Trait multipliers apply to base values only:

- Physique multiplies Body training base gain.
- Physique multiplies Body training strain gain.
- Spiritual Root multiplies Essence training base gain.
- Spiritual Root modifies meditation comprehension gain.

Flat support bonuses, variance, resources, locations, and future item/technique
bonuses should not be stacked into one uncontrolled multiplier chain.

Available engine actions:

- `TRAIN_BODY`
- `TRAIN_ESSENCE`
- `STABILISE_FOUNDATION`
- `STABILISE_ESSENCE`
- `BODY_BREAKTHROUGH`
- `ESSENCE_BREAKTHROUGH`

Bare CLI commands `train` and `breakthrough` default to the body path for compatibility.

## Breakthroughs

`STABILISE_FOUNDATION` reduces Body cultivation strain, restores foundation stability, grants a small comprehension gain, and advances the backend day. It returns `STABILISE_RESULT` with read-only display fields such as current strain and foundation stability. `STABILISE_ESSENCE` is the Essence-track equivalent, reducing Essence strain and restoring Essence foundation stability (tuned by `essence_progression.stabilise`).

Breakthrough checks include realm existence, configured progress, foundation, resources, injury state, and track-specific stability. Body breakthroughs additionally require cultivation strain at or below `max_strain_for_breakthrough` and `foundation_stability` at or above `required_foundation_stability`. Essence breakthroughs enforce the same strain/stability gates from the `essence_progression` config. Failures return stable message codes such as:

- `INSUFFICIENT_PROGRESS`
- `INSUFFICIENT_FOUNDATION`
- `MISSING_RESOURCE`
- `STRAIN_TOO_HIGH`
- `FOUNDATION_UNSTABLE`
- `BODY_TOO_WEAK`
- `ESSENCE_LOCKED_BY_BODY_PULSE`
- `ESSENCE_UNSTABLE`
- `REALM_LOCKED`
- `INVALID_REALM`
- `ALREADY_AT_PEAK`

UI layers should display `player_message` when present.

Failed Body breakthrough attempts do not grant permanent stats. They reduce progress to the configured failure ratio, increase cultivation strain, reduce foundation stability, and increment `breakthrough_failures`. Failed Essence breakthroughs likewise increase Essence strain and reduce Essence foundation stability (from `essence_progression`), on top of scattering essence progress.

Traits can improve odds but cannot bypass hard requirements. Physique adds to
Body breakthrough chance and multiplies successful Body breakthrough stat gains.
Spiritual Root adds to Essence breakthrough chance. Neither trait ignores
required progress, strain, foundation stability, resources, or realm locks.

Future work: reroll modes, manual selection, root/physique upgrade actions,
rare upgrade resources, awakening events, and NPC reactions to rare traits.

## Balance

The system reports body/essence balance as one of:

- `Harmonised`
- `Body-Leaning`
- `Essence-Leaning`
- `Unstable`
- `Severely Imbalanced`

Balance is currently based on relative realm order and is returned as read-only state for UI warnings.

## Late Game

Late-game Essence Gathering realms are present as data stubs. `Beyond Divinity` is a theoretical endpoint and is intentionally unreachable in the current build.