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

   **And it is not a strawman — settled 2026-08-20, do not re-litigate.** The
   standard objection is that `last-lge` (594) and `prior-lge-noise` (561) are
   weak, and that the honest reference is Murphy's convex combination of
   persistence and swing. That combination collapses to a *damped* swing
   (`prev + w·swing`), it was built as `benchmarks.blended-swing`, and its
   optimum is **on the boundary at w = 1.0 — uniform swing itself.** Seat error
   is monotone decreasing across the whole interval (594 at 0.0, 456 at 0.5, 376
   at 1.0); the unconstrained optimum at w = 1.05 is worth 4 seats in 376, is not
   a blend, and **loses leave-one-out, 380 against 376.** MODEL-LOG §1.57.

   What is NOT settled, and is the live objection to the headline, is that the
   margin is a **Gauteng** result: 42% off uniform swing inside Gauteng, 10%
   outside, and a loss at Mangaung. `history.md` prints the split; quote it.
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
   | ranks 1-3 | 48 | 0.511 | 83% | 96% | 98% | 0.676 |
   | ranks 4-12 | 56 | 0.613 | 61% | 91% | 93% | 0.828 |

   | sixteen-city-year vote error | signed | absolute |
   |---|---|---|
   | ranks 1-3 | +12.55pp | 94.23pp |
   | ranks 4-12 | -26.57pp | 72.60pp |
   | ranks 13+ | +4.42pp | 22.44pp |
   | phantom (parties that did not stand) | +9.60pp | — |

   **BOTH TABLES ARE NOW MEASURED ON SIXTEEN CITY-YEARS (2026-08-23,
   `MODEL-LOG` §1.77).** They were nine until §1.70 doubled the panel, and that
   entry's own instruction — *"every number in this repository predating this
   entry was measured on nine city-years and must be re-read on sixteen before
   it is quoted again"* — was not carried out at the time. This is that re-read
   for rule 8. **The fault keeps its shape and grows with the panel**: ranks 1-3
   +10.62pp → **+12.55pp** signed and 61.09 → **94.23pp** absolute, ranks 4-12
   −22.76 → **−26.57pp** and 48.42 → **72.60pp**. Half the added city-years are
   a cycle the model had never been scored on, so more absolute error over more
   columns is expected; what matters is that the SIGNS and the ordering are
   unchanged.

   Mean PIT moved with it — ranks 1-3 0.483 → **0.511** and ranks 4-12 0.676 →
   **0.613**, both toward 0.50 — and the width statistic moved the other way:
   probit-SD 0.685 → **0.676** at the top and 0.695 → **0.828** in the middle.
   **On sixteen city-years the middle band is not merely mis-levelled, it is
   measurably wider than it was**, which is the direction §1.59's second finding
   asked for and is not evidence that anything was fixed — nothing about the
   width was changed between the two measurements. The panel was.

   **The tail is the cost, it was attacked, and it stays.** Ranks 13+ sit at
   **+4.42pp** signed (they were −1.55pp before the shrink and +5.60pp on the
   nine): a band that was very nearly unbiased is over-forecast, because the
   shrink returns its freed mass by uniform renormalisation and there are many
   micro-parties to receive it. §1.54 built the obvious fix — a soft floor on
   the receiving side — and measured it: it closes the tail and **costs 14 to 22
   coherent seats**, while making ranks 1-3 and 4-12 *both worse*. The mass
   withheld from the tail goes to the TOP, not the middle, because every weight
   tried is monotone in size. And the tail is **33 of 2,960 seats** at stake
   across the sixteen — **1.1%** of what is being contested, a smaller share
   than the 1.8% it was on the nine.

   So this is a bias the project has decided to carry, on the record, rather
   than an outstanding defect.

   **On level.** The pooled claimed mean PIT is 0.559 and it sits between 0.511
   and 0.613 — an over-forecast averaged with an under-forecast. The model still
   **over**-forecasts the top three and **under**-forecasts the middle, exactly
   as the signed vote bands say, but by much less than it did, and only the
   ranks 4-12 cluster-bootstrap CI excludes 0.50 — [0.537, 0.684] on sixteen
   city-years, against ranks 1-3 at [0.474, 0.544], which does not separate from
   centred. **That split survived the panel doubling**, which is the first
   out-of-sample evidence rule 8 has ever had for its central claim: it was
   measured on one electoral cycle and it holds on two.

   **That gap is a zero-sum transfer, not two independent faults**: shares sum
   to one, so the +12.55pp at ranks 1-3, the +4.42pp at 13+ and the +9.60pp of
   phantom mass are the same points as the −26.57pp at ranks 4-12 — they balance
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

   **A WIDTH COMPARISON GOES ON `reference`, NEVER ON `claimed` — added
   2026-08-20, and it changes the ranks 4-12 half of everything above.**
   `claimed` selects columns from the forecaster's own draws, so two settings of
   a lever are scored on two different populations: 58, 67 and 81 columns across
   the `dirichlet_scale` sweep, of which 30, 37 and 45 are ranks 4-12. Worse,
   the rule selects **away from the failures** — a party the model gives a seat
   in fewer than half its draws is a party the model is failing on, and Cape
   Town's Cape Coloured Congress (z = +12.1) and Johannesburg's PA (z = +9.3)
   are outside `claimed` and inside `reference`.

   On the fixed population ranks 4-12 read `sd(z)` **1.940** against `claimed`'s
   0.823. Ranks 1-3 are the same 27 columns in both and are unchanged at 0.855.

   **AND CHOOSE THE STATISTIC BY THE BAND — §1.58, the same day.** `sd(z)`
   supersedes probit-SD *on continuous columns* and is meaningless on a
   near-degenerate discrete one: where the forecast is roughly Bernoulli(p) and
   the truth is zero, `z = −√(p/(1−p))` exactly, and observed `z` on the 96
   such ranks-13+ columns correlates with that expression at **+0.93**.
   probit-SD is valid there and is attenuated by a shift, so it is a lower
   bound wherever `mean z` is far from zero. Neither is right everywhere; the
   pair is. So:

   - **Ranks 1-3: genuinely too wide, by about 1.5×** (probit-SD 0.682, `mean
     z` −0.009 so nothing is attenuating it). This is the band that is too wide
     and the band that responds to `dirichlet_scale`.
   - **Ranks 4-12: not describable by one width.** On the same 74 columns
     `sd(z)` says 1.940 (far too narrow), `IQR-sd` says 0.595 (too wide) and
     probit-SD says 1.020 (about right, attenuated by `mean z` +0.796). They
     disagree because the distribution is a narrow shifted bulk plus two
     enormous outliers. **Mis-shaped, not mis-scaled** — no scalar fixes it.
   - **Ranks 13+: probit-SD 1.188, and INERT** — 1.208 → 1.192 across a 32-fold
     change in concentration. 124 of the 225 fixed columns. `dirichlet_scale`
     is not their lever.
   - The corollary two paragraphs above — "both bands want the same thing on
     width, narrowing" — is **withdrawn**. It was read off `claimed`, and on a
     fixed population only ranks 1-3 wants narrowing.
   - **CRPS wants the forecast narrower than the seat error does, all the way
     out**: across `dirichlet_scale` 0.5 → 16 CRPS falls monotonically 256.4 →
     212.5 while coherent seats stay flat at 254–262. A width decision taken on
     CRPS alone runs to the end of the sweep. Do not take one.

   The multiplier this rule quotes as "about **1.35×** wider" is also stale: it
   comes from probit-SD figures (0.740 / 0.734) measured before the level
   shrink. The committed artefact reads 0.685 / 0.695 probit-SD, i.e. 1.17–1.21×
   on `claimed` — and on `reference` ranks 4-12 the sign reverses entirely.
   MODEL-LOG §1.56.

   **`reference` coverage and PIT are not calibration figures.** A population
   fixed on inputs must contain columns that are zero on both sides, each a free
   interval hit, so it reads optimistically by construction. The dilution is
   identical at every setting, which is what makes a DIFFERENCE readable.
   Quote `claimed` for "is this model calibrated"; quote `reference` for "did
   that change help".
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
   outside those nine picks it; the arrival record independently gives 0.29–0.35.
   **That advice is WITHDRAWN as of 2026-08-22 (MODEL-LOG §1.69), and the
   withdrawal is instructive.** Both derived values were measured on the nine
   city-years at 1500 draws and both are worse, monotonically: 254 coherent at
   the committed 0.25, **262 at 0.290 and 264 at 0.353**, with CRPS 232.7 /
   234.3 / 236.1. *Worse does not ship.* Note this is not a constant chosen ON
   the scoreboard — 0.25 is the incumbent and the scoreboard was used to REJECT
   a change, which is the one thing it is unambiguously for. And §1.31's finding
   that "the whole range is inside the noise" **has expired**: the same sweep
   moved 2 seats then and moves 10 now, because the level shrink, the
   contestation correction and the poll paths all landed in between. A null is a
   statement about the model that measured it. When a change improves the score,
   say *what evidence outside the score chose it* — and if the answer is "the
   score", say so and leave the constant alone.
11. **"It was forward validated" does not answer rule 10. Say WHICH LOOP.**
    Added 2026-08-20 after the claim *"that is a fit to the forward-validated
    record, not the scoreboard, so rule 10 permits it"* was made about the
    `sd_for` refit and does not survive contact.

    **`compare_history` IS a forward-validated record** — of the whole model
    rather than of one layer — and it is computed on the same elections. "The
    record" and "the scoreboard" are not two datasets. There are three levels,
    and only one of them is where rule 10 bites:

    | | what happens | leakage? |
    |---|---|---|
    | **L0 — estimation** | the model fits its own parameters from data strictly before its target, afresh at every target (`theta_prior` refits `sd_for` per metro-year) | **none.** This is what a model does; rule 10 is not about it |
    | **L1 — specification** | a person chooses the functional form, the covariate, the bin edges — **once, having looked at every target including the ones L2 scores** | **this is the leak** |
    | **L2 — evaluation** | the nine city-years | biased by exactly as much as L1 saw |

    Choosing at L1 using data L2 then scores makes L2 optimistically biased.
    That is the standard nested-cross-validation result and it is the same trap
    §1.44 already carries: the level shrink's *value* was chosen by
    leave-one-city-year-out, but its *functional form* was chosen by screening
    four candidates against all nine.

    **So the defence of a fit is never "it was out of sample". It is the number
    of INDEPENDENT CLUSTERS the fit had, against the number of free parameters
    it spent.** On this panel those numbers are brutal:

    - the **scoreboard** has 9 city-years of which **8 share one cycle** — the
      2021 national swing, ActionSA's arrival, one fragmentation shock. Under
      any honest clustering the effective sample is **about 2**.
    - the **θ residual record** (`src/theta_residual.py`) has **n=257 across 18
      metro-year clusters** spanning four cycles.

    The forecasting literature's rule of thumb is on the order of 30 independent
    observations per free parameter before a fitted choice is trustworthy. At
    two effective clusters **the scoreboard supports approximately zero
    parameters chosen on it**, which is why rule 10 exists and why it has been
    right every time it has been applied. Eighteen clusters is not thirty, but
    it is not two either, and the difference is the whole argument.

    **The protocol that follows.** When a specification choice must be made from
    data, nest it explicitly: choose the form on the earlier targets, apply it
    unchanged to the later one, and report L2 only on the held-out target — then
    reverse. With four LGE targets in the θ record that is executable (choose on
    2006+2011+2016, apply to 2021; then choose on 2006+2011+2021, apply to
    2016). And say in advance what result would count, because **an effect
    smaller than two effective clusters can resolve is "undetermined", not
    "adopted"**.

## When to stop — written 2026-08-21, because "keep iterating" is not a plan

The only question this file asks is whether the model predicts past elections
better than the last version and better than the baselines. It does: **254
coherent seat error against uniform swing's 376**, and uniform swing is measured
to be the strongest member of the naive family (§1.57). What follows is the
other half of the question, which this file never answered: **when is it done?**

### The panel has a floor, and the model is close to it

Three separate measurements, none of which were taken to answer this:

* **The scoreboard carries about two effective clusters.** Nine city-years, eight
  of them one cycle (rule 11). The forecasting rule of thumb is ~30 independent
  observations per fitted parameter. **This panel supports approximately zero
  parameters chosen on it**, which is why rule 10 has been right every time.
* **θ is at its estimation ceiling.** Forward validation puts the floor at
  RMSE(log θ) = 0.715 — a typical error of about 2× on a party's retention —
  and every enrichment tried (year, metro, fragmentation, party dummies
  unpooled) scored *worse* out of sample (§1.43).
* **A third of the error is one party in one city.** Johannesburg 2021 is 86 of
  the 254, and ASA is the largest single party term at 47 of 290 on the median
  vector — an arrival with one prior local election. Its miss mechanically
  generates the ANC, DA and EFF over-forecasts, because shares sum to one.

### And there is no remaining change that improves seat accuracy

Everything with a measurement behind it has now been tried:

| candidate | result | measured at |
|---|---|---|
| `sd_for` refit, two forms | **refuted** — loses held-out NLL | §1.62 |
| arrival-group draw | **refuted** — 254 → 348 | §1.63 |
| chi-square bias correction | **refuted** — worse on everything | §1.50, §1.59 |
| tail soft-floor | **refuted** — costs 14–22 seats | §1.54 |
| symmetric spine blend | **refuted** — 312 → 338 | register |
| `dirichlet_scale` narrowing | **a trade, not a win** — fixes ranks 1-3 width and costs 4 seats at 1.4, 8 at 2.0 | §1.55, §1.58 |

The last row is the only one with a live case, and it is a trade: ranks 1-3 are
about 1.47× too wide (probit-SD 0.682, unattenuated) and narrowing fixes it **at
the cost of coherent seats**. *Worse does not ship* decides that, and rule 10
decides it again, since the method-of-moments fit names 1.0.

### So the remaining work is not modelling

**Stop opening new modelling fronts.** What is left that is worth doing:

1. **Publish.** The forecast is the point, the published page is an output of an
   earlier version, and the pre-nomination window closes on 16 September. This is
   the only time-critical item and its value decays to zero.
2. **A4, on 16 September.** Dated and certain: real nomination lists make the
   contestation correction live, retire `contestation_expand`, and cut phantom
   entrant mass. Mechanical, not a modelling bet.
3. **Disclosure, which is cheap and forecloses the strongest criticisms** —
   already largely done: the Gauteng split (§A7), calibration on a fixed
   population (§1.56), and the stated failure mode the publication gate asks for.

**What to stop:** any constant fitted on these nine city-years. A3's
fragmentation-dependent shrink is the clearest example — its per-city-year
optimum really does span 0.00 to 0.65, and that heterogeneity cannot be
distinguished from the 2021 shock with two effective clusters. It is the same bet
§1.62 just lost.

### What would license restarting

Not an idea. **More independent clusters.** Concretely: the pre-2011 archive
ingested for the seven metros that only have Johannesburg before 2011, which
would roughly double the θ record's cycles; or the 2026 result itself, which adds
a genuinely independent cycle and is the first honest out-of-sample test this
model will ever get.

Until one of those exists, a change that improves the nine city-years is
evidence about the nine city-years.

### And the panel was smaller than the archive for a second reason nobody had found

**Added 2026-08-22 after an outside audit — MODEL-LOG §1.69.** The paragraph
above is right that the pre-2011 archive is the thing to get. It was wrong about
what stood between here and a bigger panel, in a way that made the ceiling look
lower than it is.

`backtest.runnable_targets` reports what the ARCHIVE supports: 2011, 2016 and
2021 **for all eight metros — twenty-four city-years.** `compare_history.runnable`
reported nine. The gap was never stated anywhere, and it had two independent
causes that looked identical from outside because both produced a silent absence:

1. **No emitted pool spec.** Seven of the eight metros had `pools_2021.json` and
   nothing else. This needed **no new data at all** — the `lge2011_*` and
   `npe2014_*` files have been on disk throughout — and it has been fixed: all
   eight 2016 specs are now emitted.
2. **No γ fold.** A 2016 target needs a γ fold strictly preceding it, which is
   fold 3 (2009 NPE → 2011 LGE), which needs `npe2009` and `lge2006`. **Those
   exist for Johannesburg and for no other metro.** There is no way round it:
   fold 1 targets 2016 itself, so borrowing its γ reads the answer.

So the second blocker IS the pre-2011 ingest this file already named — and the
first one was a separate, invisible, entirely mechanical limit sitting in front
of it. **That changes the value of the ingest, not the verdict.** The pre-2011
archive for seven metros now buys **seven city-years and a second full electoral
cycle immediately**, because the other half of the work is done and committed.
It is no longer "roughly double the θ record's cycles, eventually"; it is the
single remaining step.

`compare_history` now PRINTS what the archive supports and this harness cannot
run, with the reason, on every invocation. The number of city-years is the
denominator of every claim this file makes, and it must not be able to shrink
quietly again.

## Where the record lives

* `MODEL-LOG.md` — findings, obstacles, decisions, mitigations. Append, never
  rewrite.
* `JUDGEMENT-CALLS.md` — every structural choice not forced by the data.
* `data/processed/history.md` — the current iteration's scores against history.
* `DATA-QUALITY.md`, `SOURCES.md` — what the inputs are and what is wrong with
  them.
