# Time Model

One clock: `Player.age_years`. Nothing else stores time, so nothing can disagree
with it. Every time-consuming action funnels through
`ProgressionMixin._advance_time_after`, which ages the character by the action's
cost and advances the living world by the same number of years.

Derived from the clock rather than stored beside it:

| Readout | Derived as |
|---|---|
| Season | `int(age_years - 12) % 4` → Spring, Summer, Autumn, Winter |
| Year elapsed | `int(age_years - 12)` (`LifespanSystem.elapsed_years`) |
| Remaining lifespan | realm maximum − `age_years` |

There is deliberately no day counter. An earlier build kept a separate
`current_day` integer that only rest, meditate and stabilise incremented, which
is how a run could report day 6 while the character had aged to 44.8. Pacing is
throttled by `cultivation_strain` (and the stabilise trade) instead: training
raises strain, `stabilise` lowers it, and strain above `max_strain_for_breakthrough`
refuses a breakthrough.

## Action costs

Read from `cultivation_config.json` → `lifespan.time_costs`. Both the character
and the world advance by the listed cost.

| Action | Cost key | Years |
|---|---|---|
| Train Body | `train_body` | 0.125 |
| Train Essence | `train_essence` | 0.125 |
| Breakthrough (Body) | `body_breakthrough` | 0.25 |
| Breakthrough (Essence) | `essence_breakthrough` | 0.25 |
| Stabilise Foundation | `stabilise` | 0.1 |
| Stabilise Essence | `stabilise_essence` | 0.1 |
| Rest | `rest` | 0.05 |
| Meditate | `meditate` | 0.1 |
| Travel | `(derived)` | 0.05 × the season's `travel_years` modifier |
| Closed-door cultivation | `(derived)` | the chosen 1, 3 or 10 years |

Two multipliers sit on top of a cost, and neither is a second clock:

* **Realm aging** (`realm_aging_multipliers`) slows *the character's* aging once
  Essence Gathering is open — a Divine Sea cultivator ages at 0.85 of the world's
  rate. The world still advances by the full cost.
* **Season** (`season_modifiers.travel_years`) scales travel only.

Actions that cost no time — every read-only view, `CODEX`, `SHOP`, `BUY_ITEM`,
`SAVE`, equipping, and the encounter/debate turns — advance neither.

## Invariants

Pinned by `tests/test_time_model.py`:

1. `time_costs` and this table agree in both directions (no undocumented cost,
   no documented cost the config dropped).
2. No stored time field exists besides `age_years` — a save carries no
   `current_day`, and the state view exposes none.
3. A time-consuming action moves the character's age, the world's year, and the
   season together, by the documented amount.
