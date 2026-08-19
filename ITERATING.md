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

   **AND A NULL IS ONLY AS BROAD AS THE OUTPUT IT WAS MEASURED ON**, which has
   now bitten twice. CLASS 12 compared list shares only and called
   `ward_noise_sd` and `pa_contestation_uplift` dead; both are live on the ward
   side (§1.37). The width budget looked at citywide share only and called the
   turnout knobs zero; they move 46 ward wins (§1.48, §1.51). Before writing "no
   effect", say which output you looked at, and check the one the mechanism
   claims to act on. Two companions to it: never quote a contribution smaller
   than the noise floor printed beside it (§1.48 did, and was corrected), and a
   null measured with a gate shut is a statement about the gate — which is how
   `poll_k` was wrongly certified inert.
8. **Width and level are different faults with opposite remedies, and NEITHER
   can be read off a coverage number.** This rule has now been wrong twice in
   two days, in opposite directions, and both times because a width verdict was
   taken from coverage at a single nominal level. Read the paragraph after the
   table before proposing anything.

   The LEVEL genuinely differs by rank band, and that part has never been in
   doubt. The WIDTH does not: **both bands are too wide, by almost exactly the
   same factor.**

   <!-- CHECKED-AGAINST-ARTEFACT: data/processed/history.json, claimed columns.
        tests/test_calibration_report.py::test_the_documented_figures_match_the_committed_artefact
        parses the two tables below and fails the build if they and the artefact
        disagree. Do not hand-edit a cell; re-run compare_history.py, commit the
        artefact, and paste what the report printed. -->

   | claimed columns | n | mean PIT | 50% (PIT) | 80% (PIT) | 90% (PIT) | probit-SD |
   |---|---|---|---|---|---|---|
   | ranks 1-3 | 27 | 0.483 | 81% | 96% | 96% | 0.685 |
   | ranks 4-12 | 37 | 0.676 | 59% | 89% | 92% | 0.695 |

   | nine-city-year vote error | signed | absolute |
   |---|---|---|
   | ranks 1-3 | +10.62pp | 61.09pp |
   | ranks 4-12 | -22.76pp | 48.42pp |
   | ranks 13+ | +5.60pp | 16.89pp |
   | phantom (parties that did not stand) | +6.54pp | — |

   **Both tables were re-measured on 2026-08-18, after the level shrink
   (`MODEL-LOG` §1.44).** The fault this rule describes is smaller than it was
   and has not changed shape: ranks 1-3 signed error falls from +31.95pp to
   +10.62pp and ranks 4-12 from −36.88pp to −22.76pp, with the absolute columns
   falling too (72.07 → 61.09 and 56.63 → 48.42), so this is mass moved to the
   right places and not merely cancelled. Mean PIT moved 0.432 → 0.464 and
   0.749 → 0.680 with the shrink, and the contestation correction of §1.47 took
   it further to **0.483 and 0.676** — both bands toward 0.50 from opposite
   sides, twice, from two changes that touched the level and never the width.

   **The tail is the new cost and it is in the table.** Ranks 13+ go from
   −1.55pp to **+5.60pp**: a band that was very nearly unbiased is now
   over-forecast, because the shrink returns its freed mass by uniform
   renormalisation and there are many micro-parties to receive it. That is a
   known, measured trade recorded in §1.44, not a surprise — and it is the
   first thing to attack next.

   **On level.** The pooled claimed mean PIT is 0.589 and it is the average of
   0.483 and 0.676 — an over-forecast averaged with an under-forecast. The model
   still **over**-forecasts the top three and **under**-forecasts the middle,
   exactly as the signed vote bands say, but by much less than it did, and only
   the ranks 4-12 cluster-bootstrap CI now excludes 0.50: ranks 1-3 sit at
   [0.431, 0.531], which no longer separates from centred.

   **That gap is a zero-sum transfer, not two independent faults**: shares sum
   to one, so the +10.62pp at ranks 1-3, the +5.60pp at 13+ and the +6.54pp of
   phantom mass are the same points as the −22.76pp at ranks 4-12 — they balance
   to the last decimal. A level fix must MOVE mass; adding it anywhere takes it
   from somewhere, which is exactly why the level shrink had to redistribute
   what it took rather than simply lower the top.

   **On width — and this is the part that was wrong.** This rule once said
   ranks 4-12 were "too NARROW — widen them", on the strength of the 50% column
   alone, which then read 31%. **A forecast whose intervals are too narrow
   under-covers at EVERY level.** They over-covered at 80% and 90% then, and
   they still do (91% and 94%). What produces a low 50% with a high 80 and 90 is
   a forecast that is *shifted* — it has vacated the middle of its own interval
   — sitting inside intervals that are *too wide*.

   The level shrink is the direct evidence for that reading, because it moved
   the level and nothing else: the 50% (PIT) column for ranks 4-12 went from
   **31% to 51%** without a single interval being widened or narrowed, and the
   contestation correction of §1.47 took it on to **59%** the same way. A width
   fix could not have done either.

   Both also moved the level-free width statistic toward correct without
   touching a width constant: ranks 4-12 `sd(z)` was **0.628** before the level
   shrink and is **0.823** now, against a nominal 1.0. That is what it looks
   like when a LEVEL fault stops masquerading as a width one.

   That is not an argument, it is a fixture, and it is in the suite. The rows
   below come from `tests/test_calibration_report.py::_shift_scale_results(4242,
   12, width_mult=W, shift=S)` — nine small parties on a mean of 4 seats, the
   real band's scale — run through this repository's own `calibration_columns`:

   | ranks 4-12 fixture | mean PIT | 50% | 80% | 90% | PIT var | probit-SD | sd(z) |
   |---|---|---|---|---|---|---|---|
   | correct width, no shift | 0.552 | 0.454 | 0.824 | 0.880 | 0.0829 | 1.021 | 1.000 |
   | correct width, **+2 shift** | 0.794 | 0.269 | **0.556** | **0.759** | 0.0450 | 0.917 | 1.000 |
   | correct width, +3 shift | 0.876 | 0.167 | 0.361 | 0.509 | 0.0240 | 0.953 | 1.000 |
   | **1.6× too wide, +2 shift** | 0.740 | 0.435 | **0.861** | **0.935** | 0.0270 | 0.571 | 0.650 |
   | **the model, ranks 4-12** | **0.757** | **0.321** | **0.893** | **0.964** | 0.0388 | **0.734** | — |

   A shift takes coverage away at every level. **Only excess width puts it back
   at 80 and 90**, and the model's row sits with the too-wide arm at both.

   The statistics that settle it are in the report's *"Is it the right WIDTH?"*
   table, which divides the level out: **probit-SD is 0.740 at ranks 1-3 and
   0.734 at ranks 4-12** — 1.00 being right, below 1.00 too wide. The two bands
   are dispersed almost identically, both about **1.35× wider** than the errors
   they cover. Note `sd(z)` in the table above: exactly 1.000 at every shift
   when the width is right. That is the column to prefer once the artefact
   carries it; the artefact quoted here predates it.

   **So the corollary that "no single change can fix both bands" is also
   wrong.** Both bands want the same thing on width — narrowing — and the level
   difference is one transfer. A change that narrows the seat distribution and
   moves mass from the top three to the middle is a single coherent proposal,
   not two contradictory ones. It still has to beat the baselines on history
   before it ships.

   **Statistics that do NOT answer the width question, and were each used to:**
   - *Coverage at one nominal level.* Confounded with the level. This is the
     mistake, twice.
   - *PIT variance against 1/12.* Claimed as "shift-invariant, therefore
     clean". It is not shift-invariant — a PIT is bounded, so a shift piles mass
     against an endpoint and the variance falls whatever the width is. On the
     correct-width fixture above it reads **0.0829, 0.0450 and 0.0240** at
     shifts of 0, +2 and +3 seats against a nominal 0.0833: a pure level error
     reading as a 3.5× under-dispersion. So the model's 0.0388 is not evidence
     of narrowness — and neither are its empty tails (0 columns below PIT 0.05,
     1 above 0.95), since a shift evacuates one tail and excess width evacuates
     both.
   - *Recentring the PIT about its own mean and re-reading coverage.* Same
     boundary problem; on that fixture it reads 0.55, 0.85, 0.94 at shifts of 0,
     +2, +3 — it does not remove the shift, it reports it.
   - *`score.pit_histogram`'s shape verdict.* It tests the two END bins, so a
     monotone-increasing histogram scores as U-shaped. On ranks 4-12 it reads
     `[1, 1, 1, 11, 14]` — 25 of 28 columns in the top two bins, nothing at the
     bottom — and prints *"U-shaped … under-dispersed, widen it"*.

   **And read the intervals — none of these coverage cells is strong evidence
   on its own.** Coverage rows are now printed with cluster-bootstrap intervals
   (ranks 4-12 at 50%: 32% [19–50], which includes nominal). Taken one at a
   time, against nominal, on a binomial test that ignores clustering and so
   flatters every one of them:

   | | ranks 1-3 | ranks 4-12 |
   |---|---|---|
   | 50% (PIT) | 19/27, p = 0.026 | 9/28, p = 0.044 |
   | 80% (PIT) | 25/27, p = 0.072 | 25/28, p = 0.16 |
   | 90% (PIT) | 26/27, p = 0.23 | 27/28, p = 0.22 |
   | probit-SD vs 1.0 | 0.740, p = 0.030 | 0.734, p = 0.025 |
   | **probit-SD, both bands** | | **p = 0.003** |

   So the 80% and 90% over-coverage this rule argues from is **not individually
   significant**, and it should not be quoted as though it were. What it does is
   rule out the narrow reading — a narrow forecast cannot over-cover at all —
   while the weight of the evidence sits in the level-free dispersion statistic,
   which uses all 55 columns at once and rejects correct dispersion at
   p ≈ 0.003. Two caveats in opposite directions: columns cluster within
   city-year, so the true p is larger than any figure above; and the probit-SD
   is attenuated by the shift, so the true excess width is larger than 1.35×.

   The discreteness correction is thinner still. What turned "about right" (43%
   raw) into "far too narrow" (32% PIT-corrected) at ranks 4-12, and carried
   §1.36's whole width argument, is **three discordant columns** out of 28 — a
   one-sided sign test at p = 0.125. At ranks 1-3 it is two, p = 0.25. The
   correction is real and the direction is right; it is not a result you can
   build a conclusion on by itself, and it was.
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
