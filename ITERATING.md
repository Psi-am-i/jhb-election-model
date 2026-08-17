# What we are doing, and what the published forecast is not

This repository is **iterating a model**. That sentence sets the terms for every
comparison made here, and it is written down because it is easy to lose.

## The published forecast is not a benchmark

`joburg.whysoserious.city` carries a forecast. It is **a recent output of an
earlier version of this model**, published because it was the best we had at the
time. It is not a target, not a baseline, and not a thing to be defended.

Specifically, it is **not evidence about anything**:

* Being close to the published forecast is not a virtue. The published forecast
  has never been scored against the election it forecasts, because that election
  has not happened.
* Being far from the published forecast is not a fault. If the model has
  improved, the numbers *should* move, and a change that moves nothing has
  probably not fixed anything.
* `data/processed/validation_<year>.json` is a useful record of what an earlier
  version scored on a past election, and it is legitimate to compare against —
  but as a **previous iteration**, on identical terms, and only where the
  comparison is like-for-like. It stores twelve parties where the targets have
  fifteen to twenty-four seat-winners, so a seat error read off it is truncated
  and is not comparable to one summed over the whole ballot.

## The only question

> Does the current model predict past elections better than the previous version
> and better than the naive baselines, on the whole ballot, out of sample?

If yes, it is a candidate for publication. If no, it does not ship and we keep
iterating. There is no third outcome in which a worse model is published because
it is newer, better argued, or built from more measurements.

## What follows from that

1. **Score against history and against baselines, not against ourselves.** The
   references are `last-lge`, `uniform-swing`, `prior-lge-noise` (`benchmarks.py`)
   and the previous iteration's recorded scores. Uniform swing is the one that
   matters — it is the only baseline carrying any information about direction.
2. **A change is not an improvement until it is scored.** Measured, out of
   sample, across as many city-years as the data supports (`src/sweep.py`,
   `src/compare_history.py`, `src/diagnose.py`).
3. **A change that only moves the 2026 numbers cannot be validated here.**
   Anything driven by by-election evidence is in this position: the scraped
   window is 2022-06-01 to 2026-02-26, so no past target has any. Such changes
   are argued, not tested, and must be labelled that way.
4. **Regressions are findable and must stay findable.** The golden-seed
   characterisation tests (`tests/test_drawer.py`) exist to make every movement
   in the prior deliberate. Re-record them when a change is intended, and say in
   the file what changed and why.
5. **The live site is downstream of all of this.** Nothing is republished until
   the model that produced it has beaten the previous iteration on history.
6. **Before tuning a constant, sweep it to a value that MUST change the answer,
   and confirm the answer changes.** A constant whose extreme value moves nothing
   is not calibrated, it is disconnected — and a flat sweep reads as "this lever
   does nothing" when the truth is "you did not pull it". `entrant_prob` returned
   byte-identical rows twice for two different reasons (MODEL-LOG §1.31), and the
   first reading of that was that the arrival machinery was inert. It was not: it
   was sizing the AIC to within 0.2pp and the scoreboard was discarding the
   answer. Sweep through `compare_history.py --set KEY=VALUE`, which lands after
   `apply_city`; editing `montecarlo.DEFAULTS` does **not** reach a run.
   **A MODULE CONSTANT HAS ITS OWN VERSION OF THIS, and setting the module
   attribute is not enough on its own.** `def f(..., df=LEVEL_DF)` evaluates the
   constant once at import, so `montecarlo.LEVEL_DF = 30` reaches nothing:
   `LEVEL_DF` was swept at 2.5, 4, 7, 30, 200 and 1000 for byte-identical output
   at every value while sitting at 🔴 in the register, and `SHARE_FLOOR` and
   `SPINE_K` were frozen at four more sites (MODEL-LOG §1.33). Every constant in
   `src/` now resolves in the function body, and
   `tests/test_ipf_feasibility.py::test_no_numeric_module_constant_is_a_default_argument`
   fails the build if a new one is frozen — but the rule stands whatever the
   test says: **the first thing a sweep must prove is that it swept something.**
7. **A signed error total is not an error total, and a statistic that reports no
   fault is not evidence there is none.** Both of this project's scoreboards
   failed that way at once and neither failure moved a forecast. The rank bands
   reported a SIGNED sum, so Johannesburg 2021's ranks 1-3 read +1.36pp while
   being 26.69pp wrong — the model's worst city-year on seats was the band
   table's second-best row. And the harness computed **no calibration statistic
   at all**: `score.py` had produced coverage and PIT per run for months and
   `compare_history` took `crps.total` and dropped the rest. Both are now in the
   standard report (`compare_history.py`, MODEL-LOG §1.34). When a statistic
   says the model is fine, check what it is capable of saying.
8. **Width and level are different faults with opposite remedies, and the
   harness now separates them.** Pooled over the nine city-years the seat-holding
   columns cover close to the nominal rate at 90% — the bands are roughly the
   right WIDTH — while the pooled PIT mean sits far above 0.5: the model
   under-forecasts, systematically and in one direction, and `sweep.py` says the
   same from the other side (ten anomalies of "the truth is above the whole
   forecast", none below). **Widening the bands would score better on coverage
   and be the wrong fix**, and it would cost sharpness for nothing. Before
   proposing a dispersion change, read the pooled PIT mean; before proposing a
   level change, read the pooled coverage. A change that improves one and
   wrecks the other has not improved the model.
9. **Quote the pooled calibration figure, never a city-year's.** Per city-year it
   is four to fifteen scored columns — Johannesburg 2021 reads 12/62/75 against
   nominal 50/80/90 on n=8, Cape Town 57/100/100 on n=7 — and neither says
   anything. The report prints them for provenance and labels them as noise.
10. **"Improves the backtest" and "defensible" are different claims, and only the
   second one ships.** A constant chosen because it scores best on the nine
   city-years has been fitted to the scoreboard. `entrant_prob` has a clear
   empirical optimum near 0.40 and it was **not** adopted, because nothing
   outside those nine picks it; the arrival record independently gives 0.29–0.35,
   and that is the only number worth quoting. When a change improves the score,
   say *what evidence outside the score chose it* — and if the answer is "the
   score", say so and leave the constant alone.

## Where the record lives

* `MODEL-LOG.md` — findings, obstacles, decisions, mitigations. Append, never
  rewrite.
* `JUDGEMENT-CALLS.md` — every structural choice not forced by the data.
* `data/processed/history.md` — the current iteration's scores against history.
* `DATA-QUALITY.md`, `SOURCES.md` — what the inputs are and what is wrong with
  them.
