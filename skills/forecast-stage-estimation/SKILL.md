---
name: forecast-stage-estimation
description: Read and check the ESTIMATION segment of the Johannesburg election model's stage trace — 10_theta_prior, 20_spine and 30_centres. What each stage is, every field and its units, the invariants that must hold between them, the traps that have already caught readers out, and how to resume cold. Use when investigating why a party sits at a particular level, when changing levels.py or blended_centres or compress_levels, when a null result needs to be told apart from an absorbed one, or when writing or repairing a stage observer.
---

# The estimation segment: θ prior → spine → centres

`run_model` writes every stage of a run as JSON when given `--run-dir`. The trace
is **opt-in and changes no number** — `test_chain.py::test_passing_a_run_
directory_changes_no_drawn_number` runs the model twice on one seed and compares
the drawn seats and shares — and it publishes nothing: `main` refuses to rewrite
`data/processed` when a run directory is given, after two diagnostic runs
replaced the shipped 5,000-draw forecast on 2026-08-28.

    .venv/bin/python src/montecarlo.py --city joburg --target 2021 \
        --draws 40 --run-dir /tmp/t

Thirteen stages, of which **three are this segment**:

    00_target · 01_scenario_in · 02_pools_artefact · 03_roster
    10_theta_prior · 20_spine · 30_centres          <-- here
    40_draws · 41_guards · 42_pr_share_draws · 43_ward_share_draws
    44_seat_draws · 45_delivered

They are a chain of three estimates, each consuming the last, and they are where
the model decides **how big each party is**. Everything after them is
distribution and translation.

The executable form of everything below is `tests/test_stage_estimation.py`:
twenty-nine pure predicates over a stage payload, each with a constructed
violation that proves it can see, plus an integration pass over real traces at
two cycles. Run it standalone:

    .venv/bin/python tests/test_stage_estimation.py          # ~21s, 10 tests
    STAGE_TRACE_DIR=/tmp/t .venv/bin/python tests/test_stage_estimation.py

---

## 1. `10_theta_prior` — how a national vote becomes a local one

**θ is a RATIO**, not a share: a party's share at a local election divided by its
share at the national election before it. `levels.theta_record` collects one
observation per party per metro per transition, over eight metros, strictly
before the target. `levels.theta_prior` turns that record into a per-party band.

A party's own log-mean is shrunk toward **the centre for a party its size**
(`size_centre`, fitted `log θ = a + b·log(size)`) by `worth / (worth + SHRINK)`,
where `worth` is what its own observations are worth rather than how many there
are. The width comes from a dispersion fit against the common centre, clamped to
`[SD_FLOOR, SD_CEILING] = [0.15, 1.20]`. The band is the 10th-to-90th percentile
of the resulting lognormal.

| field | type | meaning and units |
|---|---|---|
| `prior` | `{party: [low, mode, high]}` | θ, dimensionless. The band is `mode·exp(∓1.2816·sd)`. |
| `sd` | `{party: float}` | `sd(log θ)`, **after** the clamp. This is what the draw uses (`make_drawer` reads `scenario["_theta_sd"]`, which is this dict). |
| `worth` | `{party: float}` | the party's own θ record, on `_reliability`'s 0-1-per-observation scale. Keyed on parties **with a record**, so a strict subset of `prior`. |
| `centre.n` | int | observations in the whole record. |
| `centre.weighted_geomean` | float | `exp` of the reliability-weighted mean of `log θ`. **Not a median**, despite the name it carried until §1.97 F24. |
| `centre.effective_n` | float | the weight sum; bounded above by `n`. |
| `spread` | `{at_0.1%, at_1%, at_10%, at_40%}` | `sd_for()` at four sizes — the dispersion curve, sampled. |
| `sd_floor`, `sd_ceiling` | float | `levels.SD_FLOOR`, `SD_CEILING`. |
| `at_the_floor` | `[party]` | parties the FLOOR bound. **There is no `at_the_ceiling`.** |

**Who is in it.** `set(record) | set(baseline)` — so a party with a θ record and
no national baseline is here, and a party with a baseline and no record is here
sitting on the size centre with the group's spread.

### What to know before quoting it

* **The floor is the half that matters and the ceiling is the half that is
  loud.** §1.59 measured that `SD_FLOOR`, not the fit, sets the width at the top
  of the ballot — at joburg 2021 `at_the_floor` is exactly `{ANC, DA}`. The
  CEILING binds on far more parties (21 of 44 at joburg 2021, 35 of 79 at 2026,
  11 of 22 at 2011) and **every one of them is a party with no national
  baseline**, whose width is the fit extrapolated to `log(1e-5)`. Those parties
  carry no centre and reach no forecast number. The observer asserts that:
  `cross_no_party_with_a_centre_is_drawn_at_the_width_ceiling`. If it ever
  fires, a real party's width has become a clamp.
* **`theta_prior`'s modes are consumed at no runnable target.** The
  `blended_centres` branch that reads them is the one for parties the spine
  cannot reach, and the spine reaches every party at every target measured
  (§1.49 verified this by shifting the whole band ×3 at 2021 and 2026 and
  getting byte-identical seat draws). The `sd` IS consumed. So a change to the
  centre moves nothing and a change to the dispersion moves everything, which is
  the opposite of what the field names suggest.
* **The absorption account is computed and then thrown away at the trace
  boundary.** `levels.theta_prior` returns an `absorption` block counting the
  clamp and the shrink; `20_spine`'s payload carries its own, and
  `10_theta_prior`'s does not carry this one. Recovering the ceiling census from
  `sd` is one line, which is what the observer does.

---

## 2. `20_spine` — both records, weighted by which one the party has

`levels.spine` gives every party a central citywide level from **two** routes:

* the **national route** — its share at the last NPE, times `exp(µ_θ)`;
* the **local route** — its share at the last LGE, times `exp(µ_ρ)`, where ρ is
  the local-to-local retention ratio from `levels.local_record`.

Both µ are the same estimator (`_shrunk`), so the comparison measures the
evidence and not the estimators. The blend is **geometric**:

    level = local**w · national**(1-w),   w = k / (worth + k),   SPINE_K = 1.0

`w` is the weight on the LOCAL route, keyed on the party's θ worth: a party with
a long retention history sits on the national spine, a party whose θ is nothing
but the group centre sits on its own last local result.

| field | type | meaning and units |
|---|---|---|
| `level` | `{party: float}` | central citywide **share**, 0-1. θ and ρ are already applied. |
| `k` | float | the k the run actually used. Recorded because `scenario.get("spine_k") or SPINE_K` made `spine_k=0` undeliverable (§1.97 F1) and a whole sweep measured the default. |
| `n_theta`, `n_rho` | int | observations in each record. `n_theta` **is** `10_theta_prior.centre.n`. |
| `theta_centre`, `rho_centre` | float | `exp` of each record's reliability-weighted mean log-ratio. `theta_centre` **is** `10_theta_prior.centre.weighted_geomean`. |
| `detail[p].national` | float | ⚠ **not** the party's national vote share — it is that share **already through θ**. A level. |
| `detail[p].local` | float | likewise, the last local share already through ρ. |
| `detail[p].w_local` | float | the weight on the local route, in [0, 1]. |
| `detail[p].worth` | float | the party's θ worth. **Identical** to `10_theta_prior.worth[p]`. |
| `detail[p].route` | str | `blend` / `blend at full local (no θ evidence)` / `blend at full national (k=0)` / `national only (first local election)` / `local only (no national record)`. |
| `absorption.routes` | counts | a census of `detail`. `blend` counts the two saturated labels too — that counter is about which RECORDS a party has. |
| `absorption.dropped_parties` | `[party]` | present in an input at exactly zero and dropped entirely: no level, no row. |
| `absorption.local_only_unused` | `[party]` | a level computed here that **nothing can look up**, because the consumer iterates `baseline`. §1.97 F6, named rather than repaired. |
| `absorption.blend` | account | `disagreement` = Σ\|log(local) − log(national)\|; `moved_from_national` = Σ w·gap (the mass the LOCAL route won); `share_local` = that over the total. |
| `absorption.theta_shrink`, `rho_shrink` | account | `absorbed / offered` per route: how much of the parties' own evidence the shrink took back. |

### What to know before quoting it

* **⛔ THE SPINE LEVEL IS NOT THE CENTRE.** Four routes can set a centre and the
  spine is only the third of them (poll → seed → spine → θ-mode). A reader
  quoting `20_spine` for ActionSA at joburg 2021 gets **5.85%** where the model
  used **6.84%**.
* **The seeded-arrival signature.** A party with an arrival seed has a centre of
  `base × 1.0` (`arrival_rules` returns `band = [lo/mid, 1.0, hi/mid]`, so the
  mode is exactly 1), while the spine gives it `base × exp(c_θ)` because the
  seed loop added it to the baseline before `spine` ran. So
  **`centre / spine_level == 1 / theta_centre`, exactly**, for every seeded
  arrival with no θ record of its own. That is how to recover the route the
  trace does not record. At joburg 2021 it identifies 32 of 55 centres (8.48pp
  of 111.68pp of level, mostly ActionSA); at cape town 2021, 28 of 47.
* **`share_local` is the absorption reading.** At `share_local ≈ 1` the blend is
  an attractor and "changing the national route did not move the forecast" is
  `ABSORBED:spine`, not a null about the world. Measured: 0.136 (jhb 2011),
  0.094 (2016), 0.181 (2021), 0.436 (2026), 0.213 (cpt 2021). At 2016 the
  national route wins 91% of the disagreement.
* **The label must say what happened, not which branch ran** (§1.97 F7). A party
  with both records and no θ evidence gets `w = 1.0` — nothing blended — and was
  labelled `blend` anyway. That is exactly the field a reader checks.
* **`theta_record` never reads `target.city`.** The record is identical for all
  eight metros: cape town 2021 and joburg 2021 both report `n_theta = 272` and
  `theta_centre = 0.8550669364664831`. Do not read a per-city θ into it.

---

## 3. `30_centres` — the level vector, before and after the shrink

`montecarlo.blended_centres` routes every party in the baseline to exactly one of
four levels, in this order, and **raises** if none applies (§1.52 removed the
per-party fallback constants and there is no longer one):

1. `poll_levels[p]` — a national poll, for a party with no record at all;
2. `pool_seeds[p] > 0` — an arrival, sized at `base × band_mode` (mode = 1.0);
3. `spine_level[p]` — the blend above;
4. `prior[p]` — `base × θ-mode`, for a party the spine cannot reach.

A by-election tilt may then move the result, and `compress_levels` shrinks the
whole vector.

| field | type | meaning and units |
|---|---|---|
| `before_shrink` | `{party: float}` | the level per party, 0-1, as the four routes left it. |
| `after_shrink` | `{party: float}` | **a different vector** — the same after `compress_levels`. |
| `ratio` | `{party: float\|null}` | `after/before`, `null` where `before` is 0. |
| `level_shrink` | float | `c` in `1 − c·s/(s+h)`; ships at **0.35**. |
| `level_shrink_scale` | float | `h`, the share at which the pull is half strength; **0.04**. |
| `route_notes` | `{party: str}` | prose, written **only** on the poll route and the by-election tilt. |

### What to know before quoting it

* **⛔ TWO VECTORS, AND CONFUSING THEM IS THIS PROJECT'S RECURRING DEFECT.**
  `before_shrink` and `after_shrink` are both in the file and only one of them is
  the answer to any given question.
* **`compress_levels` conserves the TOTAL and no individual level.** Each party
  keeps `1 − c·s/(s+h)` and the freed mass is returned by renormalising to the
  original total. Equivalently: the **size-weighted mean of `ratio` is exactly
  1**, which is why the largest party's ratio can never exceed 1. An observer
  that checks individual levels screams on every run; one that checks nothing is
  silent. Check the total.
* **The vector is NOT normalised and is not a ballot.** Measured totals: 0.9952
  (jhb 2011, 11 parties), 1.0567 (2016, 24), 1.1168 (2021, 55), 1.1360 (2026,
  44), 1.1198 (cpt 2021, 47). Each party's level is estimated on its own and
  nothing adds them up, so the excess grows with how fragmented the ballot is.
* **…and the next stage divides by that total.** `pool_spec` does
  `want = want / want.sum()` before the IPF. So the total `compress_levels`
  conserves is discarded immediately afterwards, and the excess acts as an
  **unlabelled per-cycle deflation of the whole vector**: 0.5% at 2011, 10.5% at
  2021. The ANC's 43.02% centre at joburg 2021 reaches the draw as 38.5% and
  comes out at 39.6%.
* **`route_notes` is empty at every backtest target.** `blended_centres` computes
  a four-valued `route` local for exactly this purpose and the trace keeps it
  only where a note was written — the poll route and the by-election tilt, and
  `bye` is empty at all sixteen backtest city-years. So the trace **cannot say
  which route placed any party** at a backtest target. Use the seeded signature
  above, or add the field.
* **`after_shrink` is not necessarily what the drawer received.** The metro-poll
  blend runs *after* this stage is written and overwrites `centres[p]` for every
  polled party, and `centres["ENTRANT"] = 0.0` is set after that. At joburg 2026
  the poll blend is live.

---

## 4. The invariants, and what each one is for

Executable in `tests/test_stage_estimation.py`. Grouped by what a violation would
mean.

**The trace is a faithful record of one arithmetic.**

| invariant | why |
|---|---|
| `log(high/low)/(2·1.2816) == sd[p]` | the band and the width are two views of one lognormal, written by different expressions. The draw uses the width; a reader would quote the band. |
| `mode == sqrt(low·high)` | a mode off its band's geometric centre means the shrink reached one and not the other. |
| `level == local**w · national**(1-w)` | the whole arithmetic of the spine, checked against the three numbers the row reports. |
| `w_local == k/(worth+k)`, `w = 0` when `worth+k ≤ 0` | F1 and F2 both lived in this line. The limit is a registered judgement call, not a derivation. |
| `ratio == after/before`; `after == compress_levels(before, recorded levers)` | pins the emitted pair to the levers the stage claims produced it. |

**The stage's account of itself adds up.**

| invariant | why |
|---|---|
| `at_the_floor` is exactly the floor census, **both directions** | the class with the worst record here — a one-way scan let a deleted lever sit in the register for days. |
| `absorption.routes` is a census of `detail`; dropped parties appear nowhere | counters and rows are built in one loop and can still come apart. |
| `moved_from_national + moved_from_local == disagreement`; `share_local` is that quotient | the block is write-only in the model, so nothing else would notice it going wrong — and it is the only thing that distinguishes `ABSORBED` from `INERT`. |
| `0 ≤ absorbed ≤ offered` | a stage reporting it ate more than it was given makes every downstream `ABSORBED:` label wrong. |
| `effective_n ≤ n` | `_reliability` is bounded by 1 per observation. |

**The stages agree with each other.** *(The part nothing else in the suite can see.)*

| invariant | why |
|---|---|
| `spine.theta_centre == theta_prior.centre.weighted_geomean` | one quantity, two functions. §1.49: these shrank toward different centres for weeks (ANC 0.869 vs 0.862, PA 1.115 vs 1.197) and the register carried it at 🔴. |
| `spine.n_theta == theta_prior.centre.n` | the same record, counted twice. A `THETA_WINDOW` applied on one path and not the other shows up here. |
| `spine.detail[p].worth == theta_prior.worth[p]`, both directions | `levels.py` claims this in a comment and nothing asserted it. It is the quantity the blend weight AND the shrinkage are keyed on. |
| every centre has a spine level or a θ prior | the four routes plus the raising `else`. A fifth route with nothing recorded behind it fails here. |
| at least one in six centres sits **exactly** on its spine level | F37's concern made checkable: an absent spine and a spine that reached nobody both degrade every party in silence. Observed: 100% (jhb 2011), 42% (2021), 80% (2026), 40% (cpt 2021). |
| no party with a centre is at `SD_CEILING` | a tripwire. Today the ceiling binds only on parties with no baseline, so it reaches no forecast number. |

**The mechanism's direction.**

| invariant | why |
|---|---|
| `ratio` is monotone non-increasing in `before` | the shrink's whole claim is an ORDERING. A hard threshold was measured first and rejected because where the line falls decides the answer (−13.2% at 5%, −5.6% at 8%, −0.8% at 15%); this form has no line. Also the cheapest detector of `before`/`after` being recorded the wrong way round. |
| largest ratio ≤ 1, smallest ≥ 1 | **see §5** — this passing is the statement of a live defect. |
| `sd` falls with size across `spread` | structurally `sd_for` is monotone, so four non-monotone values cannot come from one call of it; empirically the slope is negative and that is Reif–Schmitt showing up as dispersion. |
| off means bit-for-bit identical | if the off path renormalised a copy, every committed forecast would move for a logging change. |

---

## 5. `level_shrink` has the wrong sign for 2011 — fix #16

`level_shrink = 0.35` is applied **identically at every cycle**. The measured
signed vote-share error for ranks 1-3, summed over eight metros, is:

| cycle | signed error, ranks 1-3 | what the shrink then does |
|---|---|---|
| **2011** | **−40.81pp** (under-forecast) | takes a further **−1.47pp** off ranks 1-3 |
| 2016 | −7.45pp | −1.81pp |
| 2021 | +24.76pp (over-forecast) | −3.00pp |
| 2026 (forecast) | — | −3.42pp |

So at 2011 a non-negative shrink pushes an already forty-point-under-forecast top
of the ballot further down. The magnitude tracks how fragmented the ballot is,
not anything about the cycle.

Two separate things, and only the first is in the observer:

1. `centres_the_shrink_takes_from_the_top_and_gives_to_the_bottom` asserts the
   direction is the same at every cycle, and
   `test_the_level_shrink_is_cycle_blind_by_construction` prints the per-cycle
   magnitude. **This passing is not a clean bill.** It pins the defect so that
   the day someone makes the shrink cycle-aware the test fails and CLAUDE.md §2
   forces the documentation to move in the same commit.
2. The **unlabelled** second level lever, which is arguably larger: the
   normalisation implied by `Σ centres` (§3). It deflates the whole vector by
   0.5% at 2011, 5.4% at 2016 and 10.5% at 2021 — the same sign ordering as the
   measured cycle error, entirely by accident of ballot fragmentation. Nothing
   estimates it and nothing records it as a lever.

---

## 6. Reference readings — what a healthy trace looks like

Measured 2026-09-13 at commit `7fcfd30`, 40 draws, `--run-dir`. Use as a drift
check, **not** as a standard of correctness (CLAUDE.md §1: nothing this model has
produced is one).

| trace | `n_θ` | `θ centre` | `n_ρ` | `ρ centre` | priors | at floor | at ceiling | spine levels | blend/nat/loc | centres | Σ centres | `share_local` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| jhb 2011 | 90 | 0.9799 | 9 | 0.9555 | 22 | 3 | 11 | 20 | 8/3/9 | 11 | 0.9952 | 0.136 |
| jhb 2016 | 175 | 0.8675 | 83 | 0.5503 | 32 | 1 | 0 | 35 | 10/14/11 | 24 | 1.0567 | 0.094 |
| jhb 2021 | 272 | 0.8551 | 174 | 0.6039 | 44 | 2 | 21 | 65 | 16/39/10 | 55 | 1.1168 | 0.181 |
| jhb 2026 | 410 | 0.9256 | 292 | 0.7446 | 79 | 4 | 35 | 76 | 22/22/32 | 44 | 1.1360 | 0.436 |
| cpt 2021 | 272 | 0.8551 | 174 | 0.6039 | 42 | 0 | 0 | 70 | 13/34/23 | 47 | 1.1198 | 0.213 |

Dispersion curve at joburg 2021: `0.476 / 0.288 / 0.174 / 0.150` at 0.1% / 1% /
10% / 40%. Shrink absorption: θ 0.557, ρ 0.682.

---

## 7. What this observer does NOT check

Stated so its silence is not read as coverage.

* **Whether the estimates are right.** Every predicate is internal consistency.
  The only standard of correctness here is a backtest against real results
  (`src/compare_history.py`, sixteen city-years, ~3 min).
* **The dispersion fit, the size centre, the shrink weight.** A trace records
  what a healthy-looking estimator produced. Changing `size_centre`'s slope, or
  the `SHRINK = 2.0` constant, or the reliability half-life, moves every number
  in `10_theta_prior` and violates nothing here. Those are scored changes and
  belong to `compare_history`, `test_theta_prior` and `test_levels_dispersion`.
* **Whether `w_bye`, `PLAN_BOUNDS` or the by-election clamp are right.** They are
  **argued, not tested**: the by-election window is 2022-06 to 2026-02, so no
  backtested target has any by-elections at all and nothing under
  `bye_weight_mode` can ever be scored on the panel.
* **The route that placed each party.** Not recorded — see §3. The seeded
  signature recovers most of it and is not a substitute.
* **`10_theta_prior`'s absorption block.** Computed in `levels.theta_prior` and
  not carried into the payload; only the ceiling census is recoverable, from
  `sd`.
* **Anything downstream of `30_centres`.** Two other stage observers own the
  inputs (`00`-`03`) and the draws (`40`-`45`).
* **Ecological validity of the pools the centres are then fitted into.** The
  centres and the pool vectors can disagree — the PA at joburg 2026 asks for
  about 102% of every Coloured vote in the city — and `pool_spec`'s capacity clip
  makes that visible without settling it. `41_guards` carries the counters.

---

## 8. Resuming cold

1. **Generate a trace, do not infer the schema.**
   `.venv/bin/python src/montecarlo.py --city joburg --target 2021 --draws 40
   --run-dir /tmp/t` (~5s). Compare **2011 against 2021** — the cycle difference
   is the most interesting thing in this segment.
2. **Run the observer against it.**
   `STAGE_TRACE_DIR=/tmp .venv/bin/python tests/test_stage_estimation.py`
   (it also generates its own traces if you give it no directory).
3. **Before trusting a check you have added, corrupt something and watch it
   fire.** `CORRUPTIONS` in that file is the enforced form of this; the
   `test_every_predicate_has_a_constructed_violation` test fails on a predicate
   that has never been shown to fire. Blinding any single predicate turns the
   module red — verified by mutation on 2026-09-13, five predicates blinded one
   at a time, two tests red each time.
4. **The four model-side mutations the observer is known to catch**, each
   mirroring a defect this repository has actually had:

   | mutation in `src/` | caught by |
   |---|---|
   | the spine's route label stops describing `w` (§1.97 F7) | `spine_the_route_label_describes_the_arithmetic` |
   | `compress_levels` stops returning the freed mass | `centres_the_shrink_conserves_the_total` (+2 others) |
   | `before_shrink` / `after_shrink` emitted the wrong way round | `centres_the_recorded_ratio_is_after_over_before`, `cross_the_spine_still_reaches_the_centres` |
   | the emitted `sd` becomes the **unclamped** fit | `theta_the_widths_lie_inside_the_declared_clamp`, `theta_the_band_is_the_measured_width` |

5. **Read the sources in this order:** `src/levels.py` (`theta_record`,
   `local_record`, `_shrunk`, `size_centre`, `theta_prior`, `spine`),
   `src/montecarlo.py` (`blended_centres`, `compress_levels`, `pool_spec`'s
   `want = want / want.sum()`), then `tests/_support.py::election_files_read` —
   this repository's best instrument and the model for what a good observer looks
   like.
