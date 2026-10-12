# Pre-registration — the pool-input repairs, and what the re-emit is allowed to conclude

**Written 2026-09-25, before any model run and before any change is made.**
Nothing below is edited after the result. The result is scored against it in
MODEL-LOG, including what it falsifies.

Evidence: MODEL-LOG §1.255–§1.259. Blind pollster review:
`audits/2026-09-25-pool-inputs/brief-pollster.md`, committed before the review ran.

## What is being changed

Four defects in the emitted pool specs, each measured and none a modelling
choice.

**C1 — conservation.** Four specs declare four pools in `categories` and emit
three in `pools`, with the dropped pool's share stated in the same artefact:
buffalocity 2016 (Indian/Asian, 2.86% of the roll), mangaung 2011 (0.43%),
mangaung 2016 (2.46%), mangaung 2021 (1.31%). An artefact that contradicts
itself about where its electorate is.

**C2 — pool levels the ward table cannot identify.** 19 pool-level rates across
the fits behind the emitted specs sit on a bound rather than being estimated,
every one the Indian/Asian pool: `adult_share` at 1.0000 (11), `registration` at
2.0000 (5), `turnout` at exactly 0.0000 (6). A pool at zero turnout casts no
votes, which is how C1 arises. Cape Town's Indian/Asian pool is 8–10% of that
city's roll against a Census 2022 population share of 1.61%; eThekwini's is
18.3–19.0% against a census 19.79%.

**C3 — the registration split is carried from the fitting year.**
`pools.registered_at_target` multiplies the target's real published roll by the
**fitting year's** registration composition. Buffalo City's White pool reads
5.51% of the roll fitted at 2006 and 10.60% fitted at 2011; the 2011 spec carries
6.3%. The target's own roll and the census composition are both available before
polling day; only the turnout half of `pool_counts` needs the outcome.

**C4 — hard zeros.** 245 of 3,417 member cells are exactly zero and 37
party-city-years put over 99.9% of their weight in one pool, across 19 of 24
specs. IPF preserves zeros, so each is a permanent claim that a party wins
exactly nobody in that pool in every draw.
`test_the_pa_is_no_longer_a_single_pool_party` scans one fit and is green.

## Decisions fixed in advance

**D1 — the measurement comes before the repair.** The emitted composition is a
seed: `montecarlo.pool_spec` re-fits it by IPF on every draw against two margins.
How much of the seed survives has never been measured. The first thing the window
produces is that number per city-year and per party in the `--run-dir` trace. If
little survives, C4 and the composition side of C3 are low-value and are
deferred, and this pre-registration is scored on C1–C3 alone.

**D2 — C2 is repaired by partial pooling, not by merging or refusing.** A pool
whose rate its own city cannot identify takes the panel's estimate for that
population group, shrunk toward the city's own estimate by how much identifying
variation that city has. This estimates a property of the world and not a ratio
defined against our own output. Merging is a fallback, admissible only where the
pool is below a share of the roll fixed here at 1.0% **and** its Duncan–Davis
intervals are uninformative. Refusing a city-year is barred: the panel is
emission-limited and refusal would drop the hardest cases.

**D3 — C3 uses the target's own roll and census composition, and must not reach
the turnout solve.** One definition of "the target's ward roll", consumed by both
paths. If the incumbent projection (`projected_pool_shares` /
`pool_shares_at_target`) survives alongside it, that is two estimators of one
quantity and the change is not finished.

**D4 — a green test is not a result.** Enlarging the White pools lowers every
ratio in the impossibility scan. The three fatal cases may drop below 1.0 and the
test go green while the mechanism behind them is untouched. The window ships an
instrument that reports the strain as a continuous number per city-year for all
14 cases, fatal and straining, and the scoring below does not treat the
assertion's colour as evidence.

**D5 — the comparison is paired.** Same city-years, same seeds
(`seed 20261104`, `seed_by_row` in `history.json`), bootstrapped on the paired
differences clustered by city. The panel level's own ±148-seat interval is not
the yardstick for a paired change. No p-value is quoted from eight metros inside
one cycle.

## Predictions

Stated against the world and the mechanism. Not one is stated as agreement with
an earlier output.

**P1 — conservation, arithmetic.** After C1, all 24 emitted backtest specs
satisfy `set(pools) == set(categories)`, and every pool in `categories` with a
non-zero `pool_shares_at_target` appears in `pools`. Falsified by any exception.

**P2 — Cape Town's pool split moves toward the census and eThekwini's does
not.** After C2, Cape Town's Indian/Asian share of the roll falls below 5% at all
three cycles and its Black African share rises above 38%, against census
population shares of 1.61% and 46.35%. eThekwini's Indian/Asian share stays
within 2 percentage points of its current 18.3–19.0%. Falsified if Cape Town does
not move, or if eThekwini does.

**P3 — the impossibility scan falls but does not empty.** After C3, the fatal
count falls from 3 to at most 2, and the 14-case total falls by fewer than 7.
The reviewer's first-order arithmetic, which the lead has not re-derived, gives
buffalocity 2011 clearing (1.254 → 0.913) and capetown 2011 (1.144 → 1.112) and
nelsonmandelabay 2011 (1.067 → 1.042) remaining fatal. Falsified if the scan
empties, which would mean the repair reached the mechanism and the reading in
§1.259 is wrong.

**P4 — the one-party selection survives.** After all four repairs, the remaining
cases, fatal and straining, are still overwhelmingly the DA, and still absent at
2021 targets. Falsified if the party mix of the remaining cases resembles the
parties' shares of the vote.

**P5 — the seat headline does not move for established parties.** Paired
`seat_abs_err_coherent` over 24 city-years changes by less than its own paired
bootstrap interval. The centres are imposed through the IPF column margin, and
composition mixing is level-neutral by algebra (§1.256's two earlier geography
results). A directional prediction is made only for arrival and seeded columns,
which read the spec's `seeds`: their contribution to panel seat error improves.
Falsified if the established columns move materially in either direction, which
would mean a path nobody intended.

**P6 — ward calls do not improve materially.** Panel ward accuracy is currently
2,120 of 2,191 called (96.76%), mean multicategory Brier 0.0531. Cape Town, whose
pool split is the worst on the panel, calls 342 of 343 wards with the three
lowest Briers; eThekwini 2016, the worst city-year at 0.882, has a pool split
that matches the census. The prediction is that panel ward accuracy after the
repair stays inside 2,110–2,135 called, and that Cape Town's three city-years
change by at most one ward in total. Falsified by a gain above that, which would
say the pool split reaches ward calls by a route this reasoning does not contain.

**P7 — dose–response.** There is no placebo set, because C3 moves all 27 specs.
Before the run, each spec's `registered` vector change is measured as an L1
distance as a fraction of the roll — arithmetic on two artefacts, no model. The
prediction is that the paired CRPS change scales with that dose, largest at 2011
targets and smallest at 2021. Falsified if specs whose `registered` barely moved
show changes as large as those that moved most.

## What would say the window failed

* P1 does not hold. The arithmetic claim is then false and nothing else matters.
* The paired CRPS change is a net loss in any one of the three cycles, or its
  sign differs between cycles.
* Calibration degrades: PIT drifts, or coverage at 50/80/90 moves away from
  nominal. A sharper, worse-calibrated forecast is a failure however the seat
  total moves.
* No dose–response (P7 falsified). The change reached city-years by an unintended
  path and is a bug.
* Seats improve while votes do not.

## What is explicitly not in this window

The ActionSA and IFP geography question (§1.256: ward-share R² of 0.153 and
0.082 against 0.962 for the DA). Its two seams are a tilt dimension, which
requires a covariate table the project does not hold and a `fit_joint` that
carries tilt columns, and `vote_located_bloc`, which is circular if used
carelessly. Neither is an emit. What would move it into a later window is
evidence that those columns carry enough panel error to justify the data
acquisition, which is computable from `history.json` without an emit.
