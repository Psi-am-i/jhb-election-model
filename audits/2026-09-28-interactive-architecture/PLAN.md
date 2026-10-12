# Architecture specification — as returned by the review agent, 2026-09-28

Read-only review. `README.md` beside this file says what the lead verified and
what is carried as the agent's measurement. Every run called `run_model`
directly (Johannesburg 2026, seed 20261104, 5,000 draws, about 150 s each
natively). Nothing was written.

## Summary

Most of what the owner wants needs no re-run of the model. The published 5,000
draws already contain the variation these controls move, so the page re-weights
them: instant, with no change to how the model draws. One small recording
addition should land before 1 October, and even that has a fallback that
touches nothing in the model.

## 1. The first interactive

* A JavaScript reimplementation of the model, added in one commit (`3e45354`,
  2026-08-04).
* **Why it was fast.** Citywide seats needed only about 15 numbers, and ward
  winners were approximated over the 135 wards rather than the 865 voting
  districts (`src/export_interactive.py:6-17`).
* **Its controls were party-specific**: `thetaANC`…`thetaPA`, `turnoutANC`,
  `turnoutDA` (`archive/superseded-pages/forecast-interactive.html:242-276`).
  They break today's every-party rule.
* **Why it was retired.** The model replaced the two-bloc engine with voter
  pools, and the page's JavaScript copy was never ported.
  `src/build_interactive.py:20-35` refuses to build it, and
  `MODEL-LOG.md:5456-5468` records the page still carrying a slider for a
  constant the model had deleted.
* **Was the reason sound?** Yes: a second copy of the model drifted within
  three weeks. But the lesson drawn went further than the failure. What failed
  was a copy of the model's drawing code in the page. The fix is a page with no
  drawing code, not a page running the whole model.

## 2. `INPUT-ROUTE.md` asked the wrong question

It asked where each control acts in the model. It never asked whether the
published draws already vary in the quantity the control moves. For turnout by
population group, they do:

* each draw sets the four pool turnouts from the measured bands
  (`src/montecarlo.py:2934-2952`);
* the balancing step (IPF) uses central turnout (`:2518`);
* the drawn turnouts then weight the citywide result (`:3071`).

That is §9a's "after the IPF" placement, and it is already in every draw.

Measured spread across the 5,000 draws, 5th to 95th percentile:

| pool | turnout |
|---|---|
| Black African | 27–47% |
| Coloured | 33–73% |
| Indian/Asian | 20–71% |
| White | 38–66% |

## 3. Re-weighting reproduces an actual re-run (measured)

The pool turnouts were recorded during a 5,000-draw run. That run's seats are
identical to the published `seat_draws.csv`, so these are the published draws.
Re-weighting them was compared with a real paired re-run in which the Black
African band was shifted +5 points after the IPF, on the same seed.

Change in mean seats, Black African turnout +5pp:

| method | DA | ANC | EFF | PA | MK |
|---|---|---|---|---|---|
| re-run of the model (paired) | −3.99 | +2.46 | +1.32 | −1.45 | +0.68 |
| re-weighting, the other three pools held at their means (effective sample 1,243) | −3.58 | +2.54 | +1.70 | −1.70 | +0.56 |
| re-weighting, the Black African pool alone (effective sample 2,630) | −1.5 | +0.7 | +0.4 | −0.1 | +0.3 |

* **The gaps are sampling noise.** At an effective sample of 1,243 draws, the
  re-weighted estimate carries a standard error of about 0.39 seats for the DA
  and 0.42 for the EFF; the re-run's paired mean about 0.02.
* **Re-weighting one pool alone is the wrong control.** Pool turnouts move
  together (correlation 0.63), so selecting draws where one pool is high lifts
  all four and shrinks the difference between them. The honest control sets a
  target for every pool at once.
* **All four pools +5pp** (overall turnout): DA −1.1, ANC +0.8. The owner
  should see how small that is.
* **The range comes from the record.** Black African ±5pp keeps about
  1,220–1,243 effective draws; +8pp leaves 200. Re-weighting cannot leave the
  measured bands.

## 4. Turnout by area cannot move seats in this model

* Voting-district turnout feeds `weight_cal` (`:5117`), and
  `solve_and_predict` (`:5122-5125`, docstring at `:965`) forces the citywide
  share back to the drawn target. An area multiplier is therefore absorbed.
  This agrees with `MEASURED.md`'s 0.01 seats for turnout noise.
* **The honest version** is a pool-turnout direction: a sector's turnout means
  the turnout of the communities who live there, using census composition.
  Label it "turnout among the communities who live in the north", not "turnout
  in the north".
* **Inferred, not measured.** Sectors of similar composition are the same
  control under different names, so the five sectors are probably two or three
  distinct controls. Neither the sector directions nor their effective draws
  were measured.

## 5. Polls as a weight on each draw

The model already computes each draw's PR vote shares (`:5131`), so each draw
can be weighted by its closeness to a poll. That is the standard way to update
a forecast on a poll.

Measured on Ipsos (ANC 31, DA 27.5, ASA 14, EFF 8, MK 6), renormalised to the
five polled parties. The baseline ANC mean is 64.2 seats.

| poll error assumed (σ) | effective draws | ANC mean seats |
|---|---|---|
| 8pp | 2,324 | 76.7 |
| 5pp | 965 | 79.5 |
| 3pp | 238 | 80.6 |
| 1pp | 14 | 81.5 |

Only 44 draws are within 3pp of the poll on all five parties.

* **Trust 0** gives uniform weights: exactly the published forecast, matching
  `DESIGN-decided.md` §3.
* **Trust 100** is not "the poll happens". It is "the N simulations closest to
  this poll", and the page must say so. That is the owner's "within historical
  bounds", at no extra cost.
* **Several polls toggled on** are averaged, as the owner asked, with the spread
  between them shown.

## 6. Within-pool movement and the by-election weight need a grid

Both change how the model draws, so re-weighting cannot honestly stand in for
them. For within-pool movement, weighting by the ratio of Dirichlet densities
across about 80 parties in four pools would leave almost no effective draws
(inferred, not measured).

Instead, a small grid of full 5,000-draw runs on Atlas:

* `dirichlet_scale` {0.5, 1, 2} × `w_bye` {0, 0.4, 1}.
* **Pairing.** The `dirichlet_scale` cells are not paired with the published
  run (the random stream shifts; TODO B2), which costs about 0.2 seats of
  noise against effects of 2–4 seats. The `w_bye` cells stay paired.
* **Each cell records its own turnouts and shares**, so the turnout and poll
  weights still apply within whichever cell is selected.

## 7. Seat law needs no new runs

The three counterfactual runs used the published seed and the same draws: ANC
seats are equal in 96% of draws, and the DA differs only through the seat law.
So weights carry across seat laws by draw index. Each grid cell needs four
runs, one per seat law.

## 8. What is recorded per draw today

* **Published:** `seat_draws.csv`, `ward_draws.csv`, `seat_detail_draws.csv`
  and the three `regime_*_seat_draws.csv`.
* **Computed but discarded:** `pr_share_draws` and `ward_share_draws`
  (`:5072-5073`).
* **Not recorded anywhere:** the four pool turnouts.
* **Adding outputs is not a model change.** `MACHINERY.md:1790-1793` is the
  precedent: recording changes no draw, verified by byte-identity.
* **Fallback.** A recording wrapper around `mc.correlated_triangular`
  reproduced the published seats exactly with no edit to `montecarlo.py`.

## 9. Where Pyodide still fits

Route B is parked, not discarded: it stays the route for combinations off the
grid.

For the one-definition rule, the re-weighting arithmetic should be one Python
module, `src/reweight.py`, run under Pyodide. §10's hand-overrides already need
`seats.allocate` in the browser, so Pyodide adds no new dependency, and its
1.5 s boot runs behind a static first paint. If the owner rejects that load,
the fallback is a JavaScript copy checked against a Python fixture.

The "first 300 draws" problem dissolves: uniform weights are the published
forecast exactly.

## Build plan (about 5–6 working days)

**Before 1 October:**

* **S1 (half a day).** `draw_pools` appends each draw's four pool turnouts to a
  closure attribute, the way `ipf_stats` is attached, and `ModelRun` carries
  them.
  * **Done when** `tests/test_draw_record.py` shows all eight `*draws` arrays
    identical with recording on and off, the published seats byte-equal at seed
    20261104, and the recorded turnouts equal the wrapper's capture.
  * If the §1.263 pool re-emit lands, it comes before the final publishing run.

**After the freeze** (the frozen model at other settings):

* **S2 (1 day).** `src/export_draws.py` calls `run_model` directly, never
  `main`, and writes `site/draws/base.bin` plus a manifest. Per draw: seats
  for the seat-winning parties plus OTHER under all four seat laws, ward
  winners, PR shares and pool turnouts.
  * **Done when** its seat columns byte-equal the four CSVs and the file is at
    most 1.5 MB gzipped.
* **S3 (1 day, mostly Atlas time).** `src/lever_grid.py` runs the 9 cells ×
  4 seat laws, about 2.5 minutes each, in parallel.
  * **Done when** the default cell is byte-identical to `base.bin` and the
    manifest records the code hash.
* **S4 (1 day).** `src/reweight.py`: the joint turnout tilt, the poll
  likelihood on a stated base (renormalised to the polled parties), the
  effective-draw count, and weighted quantiles and probabilities.
  * **Done when** tests pass for uniform weights reproducing the published
    figures exactly, Black African +5pp within 2 standard errors of a paired
    re-run, and a refusal floor (fewer than 200 effective draws greys the
    control out).
* **S5 (half a day).** Ward-to-sector file and sector composition.
  * **Done when** a test shows sector registration sums to the roll and sector
    directions are reported with their effective draws.
  * Kept only if at least two sectors are distinct controls.
* **S6 (1.5 days).** The page: static published figures, background Pyodide
  load, the controls, and effective draws shown beside every result.
  * **Done when** a browser test shows the untouched page equals the published
    figures and one control move gives the `reweight.py` fixture output.

**Critical files:**

* `src/montecarlo.py`: `draw_pools` :2914-3115, the loop :5058-5132,
  `ModelRun` :3417-3468
* `src/overhang_regimes.py`
* `data/processed/pools_2026.json`
* `MACHINERY.md` :1780-1793
* `audits/2026-09-28-route-b/routeb_proto.py`, the harness pattern for S1, S3
  and S4
