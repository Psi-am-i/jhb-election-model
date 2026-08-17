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
8. **Width and level are different faults with opposite remedies — and this
   model's answer to both DIFFERS BY RANK BAND, so a pooled figure answers
   neither.** Keep the first half of that sentence: coverage says whether the
   intervals are the right WIDTH, the PIT mean says whether they are in the
   right PLACE, and a change that improves one while wrecking the other has not
   improved the model. What must go is the idea that either has one answer.
   Pooled over the nine city-years the claimed columns give a mean PIT of 0.588,
   which reads as a mild uniform under-forecast. Split by actual PR rank (nine
   city-years, 1500 draws — quote the draw count or quote neither) it is:

   | claimed columns | n | mean PIT | 95% CI | nominal 50% covers |
   |---|---|---|---|---|
   | ranks 1-3 | 27 | **0.431** | [0.380, 0.479] | 70% — too WIDE |
   | ranks 4-12 | 26 | **0.750** | [0.674, 0.810] | 27% — too NARROW |
   | pooled | 53 | 0.588 | — | 58% |

   **0.588 is the average of a −0.069 and a +0.250**, and the two CIs exclude
   0.50 in opposite directions. The model **over**-forecasts the top three and
   **under**-forecasts the middle, which is exactly what the signed vote bands
   (+32.50pp at ranks 1-3, −37.34pp at 4-12) have said all along; the two
   instruments never disagreed, only one of them was disaggregated. The
   50%-coverage column is the discreteness-corrected one — `score.coverage`
   reads 46% at ranks 4-12 because an integer interval must include whole
   endpoints, and the randomised PIT removes that.

   So: **before proposing a dispersion or a level change, read the per-band
   table, not the pooled row.** "Widening would be the wrong fix" remains true
   at ranks 1-3, where the intervals are already too wide and the centres too
   high. It is false at ranks 4-12, where a nominal 50% interval covers 27% and
   the centres are too low. A single change that moves the whole distribution
   cannot fix both, and the pooled statistic will report progress for a change
   that makes one band worse and the other better by the same amount — which is
   the same arithmetic that let a signed error sum hide a 26.50pp band error.
   `sweep.py`'s ten "the truth is above the whole forecast" anomalies and zero
   below are consistent with this: they are ranks 4-12 parties.
9. **Quote the pooled calibration figure, never a city-year's — and never the
   pooled figure alone.** Pool over CITY-YEARS: per city-year it is four to
   fifteen scored columns, Johannesburg 2021 reads 12/62/75 against nominal
   50/80/90 on n=8 and Cape Town 43/100/100 on n=7, and neither says anything.
   Do NOT pool over RANK BANDS: that is rule 8, and it is where the pooled
   number stops being an estimate of anything. The report prints the city-years
   for provenance and labels them as noise, and prints the band split next to
   the pool.
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
