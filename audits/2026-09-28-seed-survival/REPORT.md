# F2: how much of the emitted pool seed survives the per-draw IPF (pool prereg D1)

Measured 2026-09-28 by a delegated agent at commit `4711a15b`. `src/` was taken
with `git archive`, so the live tree was not imported. `run_model` was called
directly: 2,000 draws per variant, seed 20261104. Nothing was written under
`data/`.

Re-run with `run_all.sh 4711a15b 2000`. The full 26-row tables are in
`results/tables.txt`, and `tabulate.py` prints every table from `results/`.
The agent could not write report files, so the lead filed this text from its
hand-back.

**Checked by the lead** (MODEL-LOG §1.268):
* Joburg 2021 was re-run independently for placebo, c4_mild and c4_strong. All
  226 numeric fields agree with `results/joburg-2021.json` to within 5e-4
  (c4_mild seats moved 0.979 against 0.98).
* The spec is read at exactly one place, `montecarlo.py:3901` via
  `Path.read_text`, so the harness's substitution reaches every stage of the
  model.

## Definition

`pool_spec` hands IPF the matrix `members × centre`, normalised per pool
(`R0`). Every draw re-fits it against the pool votes and the shocked party
levels. Three quantities are measured:

1. **Structural survival.** IPF only rescales rows and columns, so every
   cross-product ratio in the seed, and every zero, should reach every draw
   exactly, with only the margins replaced.
2. **Transmission.** `TV(C′,C) / TV(S′,S)`: how much of a change to the seed
   (`S → S′`) reaches the composition the draw uses. `C` is the per-draw `Rd` ×
   pool votes, normalised per party and averaged over draws.
3. **Outcome sensitivity.** The paired change in mean seats, PR share and
   ward-winner probabilities when the seed is perturbed.

C4 changes the seed's interaction, which IPF preserves. C3 changes
`registered`, the row margin, which IPF imposes.

## Variants

| variant | what it changes |
|---|---|
| placebo | each party's column × a constant in [0.3, 3]; IPF is invariant to this |
| c4_eps | each zero cell set to 1e-9, so the party becomes a member and nothing else moves |
| c4_mild | each zero cell set to 0.05 × that pool's vote share, then renormalised (one reading of queue 33) |
| c4_strong | each column mixed halfway to the pool vote shares; an upper bound, not a repair |
| c3_target | the `registered` split replaced by the target year's fitted split from `pool_counts(city, target)`, same total roll; where a spec drops a pool (the four C1 specs) it is renormalised over the pools present, so the dose there understates the real repair |
| c3_proj | the `registered` split replaced by the spec's `pool_shares_at_target` |

**Pairing: common random numbers.** The drawer's generator is reseeded per
draw and each Dirichlet call gets its own stream, so no perturbation can
desynchronise the level shocks, the turnout shocks or the VD/ward stage. This
changes which random numbers the model sees, not its distribution, so the base
run is not byte-equal to a normal run.

**Materiality threshold, fixed in the harness docstring before the first
run.** A variant matters at a city-year if either:

* it moves at least 1.0 expected seat (Σ|Δ mean seats|/2) and at least one
  party moves by more than 3 paired standard errors; or
* it moves at least 1.0 expected ward call.

## Coverage

* **Run:** all 26 specs that `run_model` loads: 8 metros × 2011, 2016 and 2021,
  plus joburg 2026 and tshwane 2026.
* **Never loaded:** `pools_2026_simulation.json`; `run_model` does not read
  that file name.
* **Not measurable:** c3_target at the two 2026 targets, which have no
  target-year fit.
* **Zero cells:** 242 of 3,012 over every party named in `members` (these are
  the cells the C4 variants filled), and 172 of 2,581 over the run's universe
  (the structural table). The prereg's 245 of 3,417, and its 37 single-pool
  parties, reproduce only when the simulation file is counted too: 20 files,
  not "19 of 24".

## Results

**Structural (measured):**
* the additive log-ratio residual of `R0` against the seed is at most 2.8e-15
  in every spec;
* the zero pattern is identical in `R0` and in all 2,000 draws, in all 26
  specs;
* the median total-variation distance between the post-IPF composition and the
  seed is 0.045 per party. The margins cause that distance; the seed's shape is
  carried whole.

**Transmission (measured).** Median per party: 1.07 for c4_mild (58 parties
with seed TV above 0.01), and 1.01 for c4_strong (318 parties). A perturbation
of the seed reaches the draw's composition in full.

**Outcome.** Each cell is expected seats moved, the max paired z in brackets
where shown, then expected ward calls moved. The unpaired floor is the same
model at seed 20261105.

| city-year | unpaired floor | c4_eps | c4_mild | c4_strong | c3_target | C3 dose (L1 / roll) |
|---|---|---|---|---|---|---|
| buffalocity 2011 | 0.79 / 0.39 | 0.01 / 0.03 | 0.03 (2.2) / 0.04 | 0.26 / 0.50 | 0.34 (1.9) / 0.81 | 0.098 |
| capetown 2011 | 1.06 / 0.29 | 0.59 / 0.16 | 0.54 (2.0) / 0.17 | 0.58 / 1.83 | 0.09 (2.0) / 0.14 | 0.029 |
| capetown 2021 | 0.99 / 0.20 | 0.67 / 0.07 | 0.55 (2.8) / 0.08 | 0.90 / 0.42 | 0.14 (2.9) / 0.03 | 0.026 |
| joburg 2021 | 0.97 / 0.45 | 0.99 / 0.43 | 0.98 (2.3) / 0.44 | 1.67 (3.2) / 1.05 | 0.06 (2.2) / 0.04 | 0.007 |
| joburg 2026 | 2.78 / 1.75 | 0.48 / 0.56 | 0.48 (2.4) / 0.56 | 2.07 (3.8) / 4.15 | n/a | n/a |
| tshwane 2026 | 1.11 / 0.70 | 0.43 / 0.34 | 0.44 (2.4) / 0.36 | 1.48 (3.9) / 1.85 | n/a | n/a |
| panel sum (26; c3: 24) | 26.7 / 11.4 | 5.6 / 3.1 | 5.7 / 3.2 | 17.3 / 31.7 | 2.9 / 2.9 | |

**Noise floor:**
* **Placebo:** 0.00 seats at 25 of 26 city-years (0.03 at joburg 2026), and at
  most 0.09 ward calls. That is IPF tolerance.
* **Paired floor for seats moved:** under zero effect, Σ|Δ|/2 is expected to be
  ½ Σ SE·√(2/π). For c4_mild that expectation runs 0.03–1.07 seats across
  city-years, and c4_mild's seats moved is within about 0.1 of it everywhere
  (joburg 2021: 0.98 against 1.07).
* **No real party moves:** in no c4_mild or c3_target run does any party move
  by more than 0.38 mean seats, and none exceeds 3 paired SE.
* **The size of the fill does not matter:** c4_eps and c4_mild agree to within
  0.12 seats at every city-year.
* **Where C3 comes closest:** buffalocity 2011 under c3_target moves 0.81 ward
  calls, below the pre-registered threshold of 1.0 but above that city-year's
  unpaired floor of 0.39.

**The only per-party moves beyond 3 SE are under c4_strong:** DA +0.9 to +1.3
seats and ANC −0.6 to −1.1 seats, at capetown 2016, ekurhuleni 2021, joburg
2021 and 2026, and tshwane 2021 and 2026. So the harness can detect a
composition change, but only one that flattens every party halfway to
independence.

**Cap channel.** The only guard that differs from base is at joburg 2021.
Filling the PA's zeros removes its capacity clip: in base, 1 draw is clipped
and 43,149 votes are moved; under C4, none. Its seat effect is included in the
numbers above.

## Verdict

**The two tests point in opposite directions, and both are measured:**

* **D1 asked whether the seed survives the IPF:** it does, completely, both
  structurally and in transmission. Read literally, D1 would therefore rate C4
  as high-value.
* **The brief asked whether the draws notice a change to the seed:** they do
  not.
  * **C4:** neither c4_eps nor c4_mild reaches the threshold at any of the 26
    city-years. The panel total is 5.7 seats and 3.2 ward calls, which is the
    within-draw noise.
  * **C3, composition side:** c3_target reaches the threshold at none of the 24
    backtests. The panel total is 2.9 seats and 2.9 ward calls. The largest
    dose, buffalocity 2011 at 9.8% of the roll, moves 0.34 seats and 0.81 ward
    calls.

**Answer on the outcome test: no.** Neither C4 nor the composition side of C3
moves the drawn outcome enough to be in this window. Defer both, and score the
prereg on C1–C3.

**Inferred, not measured: why the draws are insensitive.** Each pooled party's
citywide level is imposed through the IPF column margin, and the ward stage
reads pools only to place seeded parties in VDs. Composition therefore reaches
seats only through turnout-weighted mixing and the Dirichlet split. This run
did not test those channels one by one.

**Limits:**

* c4_mild is one reading of queue 33. Drawing rates from their Duncan–Davis
  intervals (§1.262) is a different mechanism and was not measured.
* C3's effect on the impossibility scan (prereg P3) is arithmetic on the spec,
  not a draw outcome, and is outside this measurement.
* §1.263's case for C4 is honesty (a probability of exactly zero), not score,
  and this result leaves that argument standing. The window can take C4 on that
  ground without risk to the forecast, or defer it at no cost to the forecast.

**Not done:** TODO §0's predicate for F2 also names a `--run-dir` stage per
city-year and party. The brief was read-only, so no stage exists. It would hook
onto `pool_spec`'s `ipf_out`, which already carries `R0`, `pool_votes`,
`parties` and `names`, and onto the per-draw `Rd` returned by `_balance`.
