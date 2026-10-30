# Johannesburg 2026 seats under three census group mixes (2026-10-30)

Pre-registration: `prereg/2026-10-30-census-adjusted-composition.md` (8b18875, not edited).
Tree 8b188754, `src/` clean. Seed 20261104, 5,000 draws, arm U's scenario (the defaults) in every arm.
Scripts: `run_arm.py` (one process per arm), `analyse.py`. Outputs: `results.json`, `seats.csv`, `wards.csv` (per-ward top two parties and probabilities, per arm), `B|N|E/arrays.npz`, `B|N|E/meta.json`, `specs/<arm>/pools_2026.json`.

## How the arms were built (measured)

- `pools.read_census` is patched in process for population group, Census 2022: N = the four group counts with White × (1 − 290000/4525800) and Indian/Asian × (1 − 190000/1705882), renormalised per ward, for every ward nationally; E = `../wards.csv` `c11_*` on Johannesburg's 135 wards, other cities unchanged; B = no patch. The patched function served 63 calls per arm, the emit's and the run's. N changed 4,468 wards and E changed 135.
- Each arm's spec is emitted with `pools.emit_pools` into `specs/<arm>/`, and `montecarlo.read_pool_spec` reads it. Its staleness check passes. B's spec equals `data/processed/pools_2026.json` in every field except `judgement_file`, which is the pre-rename folder path.
- **B reproduces the published `data/processed/seat_draws.csv` draw for draw** (0 of 5,000 × 13 cells differ).
- Width record: read from `data/processed/width_record.json` in all three arms with the same key and variant. No `width_override` was needed. It was fitted about B's centres.
- Roll-weighted citywide mix (pool_counts, 2021 wards, registered), %:

| arm | Black African | Coloured | Indian/Asian | White |
|---|---|---|---|---|
| B | 75.559 | 5.516 | 5.017 | 13.907 |
| N | 76.143 | 5.596 | 4.660 | 13.600 |
| E | 74.175 | 5.746 | 5.220 | 14.859 |

- The patch reached the draws. Against B, N changes the seat vector in 1,035 of 5,000 draws (at most 2 seats for one party) and 268 of 675,000 ward-draw winners. E changes 4,218 draws (at most 7 seats) and 2,694 ward-draw winners. A party's list share in a single draw moves by up to 0.19 points (N) and 2.63 points (E).

## Seats per arm (270-seat council; mean, 5th–95th percentile)

| party | B | N | E |
|---|---|---|---|
| DA | 71.005 (55–88) | 71.004 (55–87) | 71.026 (54–88) |
| ANC | 70.121 (50–81) | 70.115 (50–81) | 70.110 (50–81) |
| ActionSA | 29.295 (20–41) | 29.294 (20–41) | 29.301 (20–41) |
| EFF | 27.687 (16–44) | 27.686 (16–44) | 27.682 (16–44) |
| MK | 23.347 (6–57) | 23.348 (6–57) | 23.342 (6–57) |
| PA | 17.283 (6–34) | 17.288 (6–34) | 17.283 (6–34) |

P(largest party alone), %. A tie counts for no party:

| | B | N | E |
|---|---|---|---|
| DA | 46.68 | 46.72 | 46.72 |
| ANC | 45.12 | 45.08 | 45.08 |
| MK | 3.66 | 3.66 | 3.50 |
| EFF | 0.24 | 0.24 | 0.26 |
| PA | 0.20 | 0.22 | 0.20 |
| tied | 4.02 | 4.00 | 4.16 |

Every party is in `seats.csv`, and the per-ward probabilities are in `wards.csv`.

## Differences (paired Monte Carlo error: 200 joint draw-index resamples, seed 20261012)

| | N − B | E − B |
|---|---|---|
| Δ mean seats, DA | −0.001 ± 0.004 | +0.020 ± 0.024 |
| Δ mean seats, ANC | −0.006 ± 0.003 | −0.011 ± 0.009 |
| Δ mean seats, ActionSA | −0.001 ± 0.003 | +0.007 ± 0.007 |
| Δ mean seats, EFF / MK / PA | −0.001 / +0.001 / +0.005 | −0.005 / −0.005 / +0.001 |
| largest \|Δ mean seats\|, any party | 0.006 (ANC) | 0.020 (DA) |
| Δ P(largest alone), DA / ANC, points | +0.04 ± 0.09 / −0.04 ± 0.10 | +0.04 ± 0.31 / −0.04 ± 0.32 |
| Δ P(largest alone), MK, points | 0.00 | −0.16 ± 0.07 |
| wards whose most-likely winner changes | none | none |
| largest per-ward winner-probability change, any party, points | −0.16 ± 0.07 (ward 10, ANC 36.30 → 36.14) | +1.24 ± 0.28 (ward 58, DA 20.82 → 22.06) |
| largest change in B's favourite's probability, points | +0.12 (ward 9, Al Jama-ah) | −1.04 (ward 58, ANC) |

Ward numbers are the model's ward order (index + 1), as in MODEL-LOG.

## Scored

| | bound | measured | verdict |
|---|---|---|---|
| P1 | N−B \|Δ mean\| ≤ 1.0 seat, every party | max 0.006 (ANC) | held |
| P2 | N−B ward winning-party probability ≤ 5 points | max 0.16 (any party), 0.12 (B's favourite) | held |
| P3 | N−B \|Δ P(largest)\| < 2 points, every party | max 0.04 | held |
| P4 | \|ΔE−B\| > \|ΔN−B\| for DA and ANC | DA +0.019 ± 0.019, ANC +0.005 ± 0.008 seats (\|ΔE\| − \|ΔN\|) | not falsified: right direction for both, but within one MC error, so not resolved. E−B's own DA and ANC changes are each within about 1.2 MC errors of zero |
| P5 | E−B \|Δ mean\| ≤ 4 seats, every party | max 0.020 (DA) | held |

Void conditions: nothing under `data/` was written (`find data -newer <marker> -type f` was empty before and after each arm and over the whole session). All three arms share seed, draws, tree, width-record key and variant; `analyse.py` asserts this. Not void.

Not computed: the prereg's "P(majority coalition routes the site reports)". P(one party has a majority alone) is 0.04% (B), 0.06% (N) and 0.04% (E).

## What is measured and what is inferred

- **Measured:** every number above.
- **Inferred, not tested:** why the means do not move. Per draw the arms differ, by up to 7 seats and 2.6 list-share points under E. Averaged over 5,000 draws, the changes cancel to within about 0.02 seats.
  - Two mechanisms fit this. (a) The pool fit re-absorbs the mix change against the same 2021 result, which is the prereg's argument. (b) The universal draw's calibration holds each party's citywide centre (`kappa_converged` true in every arm), so composition reaches seats only through ward geography and overhang.
  - The trace's centres before and after the calibration pass, compared across arms, would separate the two. That comparison was not run.
- The intermediates that carry no artefact key (`turnout.csv`, the group-share record, `bye_value.json`, the width record) were not regenerated under N or E. They are read as in the frozen forecast, as the prereg specifies ("every other input as in the frozen forecast's settings").
