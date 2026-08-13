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

## Where the record lives

* `MODEL-LOG.md` — findings, obstacles, decisions, mitigations. Append, never
  rewrite.
* `JUDGEMENT-CALLS.md` — every structural choice not forced by the data.
* `data/processed/history.md` — the current iteration's scores against history.
* `DATA-QUALITY.md`, `SOURCES.md` — what the inputs are and what is wrong with
  them.
