# How P3's held-out log score is computed (2026-10-16)

Written before either arm of `prereg/2026-10-16-newness-width-by-anchor.md`
is run, and before the width record carrying the class δ's was emitted. That
file names "the held-out log score of anchored newcomers' list shares" and
does not define it; this file fixes the definition. It does not amend any
prediction there.

## Population
Every party in the run's `_new_parties` (no result at the previous local
election in the city) at each backtest city-year of 2016 and 2021, eight
metros. Its class is `montecarlo.newness_class` (anchored: a vote at the
preceding national election in the city; unanchored: none). 2011 is the
fallback width record, which has no newness term, so the two arms draw it
identically; it is not scored. The ENTRANT slot is not a party and is not
scored.

## Score
For each party, the 1,000 drawn citywide list shares of `run_model` (seed
20261104, the scenario `compare_history.run_city_year` builds) and its
realised list share (`compare_history.actual_shares`, the width record's
outcome). The score is the log density, in nats, of log(realised share)
under a normal fitted to log(drawn share) (sample mean and sd; drawn shares
floored at 1e-9). A party whose realised share is 0 has no log share: it is
counted per class and not scored. Each party-city-year is one unit.

Reported per class and arm: the number scored, the sum and the mean score.
Arm comparison: the paired difference (arm S minus single δ) per
party-city-year, summed per class, with its sampling error taken as the
standard deviation of the per-city-year sums of differences times the square
root of the number of city-years (city-years are the independent units; the
parties of one city-year share a draw).

## Readings
- "Improves" (anchored): the summed paired difference is above 0.
- "Does not get worse by more than its sampling error" (unanchored): the
  summed paired difference is above minus one sampling error.
- The falsifier ("arm S scoring worse on the record for anchored newcomers
  than the shipped single δ"): the anchored summed paired difference is below 0.

A second density, a Gaussian kernel on log share with Silverman's bandwidth,
is reported beside the first as a check on the normal's shape; the readings
above are taken on the normal.
