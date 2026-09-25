# Blind brief — the pool inputs, before a re-emit

You are reviewing an approach, not code. Return a specification and a judgement.
**Do not sub-delegate.** Read-only: propose no edits and make none. Where you need
a number that is not below, say which measurement would produce it.

This brief states evidence and asks questions. It does not contain the lead's
conclusion, by design. Do not ask for it.

## The system, in the four facts you need

1. A **pool** is a census population group: Black African, Coloured,
   Indian/Asian, White. A ward's voters are split across the four.
2. A **party's pool vector** is fitted from one election's ward results by a
   joint ecological fit across all parties, one rate per pool per city-year,
   constrained so each pool's rates sum to 1 and none is negative, and held
   inside its Duncan–Davis interval.
3. A **pool's size at the target** is the target's own published ward roll
   (real, pre-election) multiplied by the **fitting year's** registration
   composition, reprojected onto the target's wards
   (`pools.registered_at_target`).
4. **One census is held**: Census 2022, on the 2021 delimitation. The Census
   2011 entry in `config/dimensions.toml` is commented out as not held. With a
   single point there is no slope, so a composition at any other year is that
   one census reprojected, damped 0.6, capped at 8 years.

## Evidence

### E1 — Two tests fail on the emitted specs, on three distinct causes

* `test_no_emitted_composition_weight_is_arithmetically_impossible` fails at
  buffalocity 2011 (1.25x), capetown 2011 (1.14x), nelsonmandelabay 2011 (1.07x).
  In each the DA's fitted composition demands more votes from the White pool than
  that pool can cast at the top of its turnout band.
* `test_the_three_known_things_hold_at_once` fails at mangaung 2016: the four
  pools' rates sum to `[1, 1, 0, 1]`.
* The model repairs the first class at run time: `montecarlo.pool_spec` re-fits
  the composition by iterative proportional fitting on every draw with each
  pool's counted voters as a hard margin. Buffalo City 2011 DA/White is repaired
  0.575 -> 0.374 before draw one.

### E2 — The pool split against a split fitted at the target year

Roll totals agree to 1.000 in 21 of 24 city-years, so this compares only how the
same real roll is divided.

| city-year | White pool: spec / fitted at that year |
|---|---|
| buffalocity 2011 | 24,294 / 40,807 = 0.595 |
| capetown 2011 | 314,399 / 339,716 = 0.925 |
| nelsonmandelabay 2011 | 108,254 / 113,117 = 0.957 |
| joburg 2011 / 2016 / 2021 | 1.047 / 0.974 / 1.002 |

Three city-years' roll totals disagree with the fitted year's by 3–5%:
buffalocity 2016 (0.972), mangaung 2016 (0.973), tshwane 2011 (0.946).

### E3 — Buffalo City by election, every quantity fitted at that year

| year | White people % | White adults % | White `registration` rate | White % of roll |
|---|---|---|---|---|
| 2006 | 9.53% | 11.98% | **0.2464** | 5.51% |
| 2011 | 8.84% | 11.40% | 0.5481 | 10.60% |
| 2016 | 8.47% | 10.88% | 0.6917 | 12.30% |
| 2021 | 8.49% | 10.87% | 0.6821 | 12.50% |

The emitted `pools_2011.json` carries the White pool at 6.3% of the roll. Its
fitting year is 2006.

### E4 — Rates fitted to a bound rather than estimated

19 across the 24 emitted backtest city-years, every one the Indian/Asian pool.
The percentage is that pool's share of the city's registered roll.

| level | value | cases | largest affected |
|---|---|---|---|
| `adult_share` | 1.0000 | 11 | capetown 2011, 9.29% |
| `registration` | 2.0000 (`REGISTRATION_MAX`) | 5 | capetown 2011, 9.29% |
| `turnout` | 0.0000 | 6 | buffalocity 2021, 3.29% |

The six `turnout = 0.0000` cases are buffalocity 2011 and 2021, mangaung 2011,
2016 and 2021. A pool at zero turnout casts no votes. `pool_counts` reports every
one of these in an `unidentified` list; a rate that is poorly determined without
reaching a bound is not reported.

`_nnls`'s docstring records a measurement at buffalocity 2006: the design
matrix's condition number is 18.8 at `registered` and 486.9 at `voted`.

### E5 — How much of each party's ward variation the pool mix already explains

Johannesburg 2021, vote-weighted R² of ward shares against the pool mix alone:
ANC 0.892, DA 0.962, ActionSA 0.153, EFF 0.712, PA 0.857, IFP 0.082, VF+ 0.385.
ActionSA's fitted rates across the four pools are 0.183 / 0.064 / 0.299 / 0.189.
The IFP's are 0.042 / 0 / 0 / 0.

### E6 — Constraints from earlier measurements

* Mixing each pool's party composition toward the city mean is level-neutral by
  algebra. A γ scaling of pool geography moves under one seat.
* Age and sex are declared as tilt dimensions, fitted, and rejected by a gate
  that admits a dimension only if it improves fit when fitted on one city and
  tested on another: +0.03 to +0.06 R² in sample, about 0.00 out of sample.
* `fit_city` refuses outright if any tilt dimension is admitted; the joint fit
  does not carry tilt columns.
* A fit-time capacity constraint on the composition was built, measured and
  reverted: coherent seat error 306 -> 486 across the panel.
* The panel total's own bootstrap interval is ±148 coherent seats, so a
  difference of a few seats on the panel total is not evidence.
* The canonical measurement is `seat_abs_err_coherent` over 24 city-years at
  1,000 draws, plus CRPS and a calibration floor.

### E7 — What a repair costs

Any change to pool inputs invalidates all 27 emitted specs and requires one
re-emit window. The owner has authorised an emit for the purpose of measuring.
The live 2026 Johannesburg forecast is built from these specs and has not been
republished since 31 August.

## Questions

1. Which of the three causes in E1, if any, should be repaired before the next
   emit, and in what order? Name what you would leave alone and why.
2. `registered_at_target` uses the **fitting year's** registration composition
   with the **target's** real roll (fact 3). The target's own roll and the census
   composition are both available before polling day; the turnout half of
   `pool_counts` is not. Is fitting the registration split at the target year
   sound, and what does it break?
3. For a pool the ward table cannot identify (E4), what treatment is defensible:
   merge it into another pool for that city-year, replace the bound with a
   fallback estimated across the panel, or refuse the city-year? State what each
   costs and how you would tell afterwards that it was right.
4. E4's detector reports a rate only when it reaches a bound. What would you use
   to report a rate that is badly determined without reaching one, and would you
   gate the emit on it?
5. Given E6's ±148 bootstrap interval, what should the re-emit measure so that
   the result discriminates? State the quantity, the population, and the
   comparison, and what result would say the repair failed.
6. What would falsify the reading that E1 is an input-quality problem rather
   than a missing mechanism?
7. E5 is a separate question from E1–E4. Say whether you would put it in this
   window or a later one, and what that decision turns on.
