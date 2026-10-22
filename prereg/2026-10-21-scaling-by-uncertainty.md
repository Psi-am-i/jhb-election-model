# Making the shares add to 100%: by uncertainty instead of in proportion

Written before the run, 2026-10-21. No model code changes: the arms wrap
`montecarlo.blended_centres` in a scratch script and write nothing into `data/`.

## The question

Each party's level is estimated on its own, then the size pull
(`compress_levels`, §A23) runs, then every party is divided by the same number
so the shares add to 100% (`pool_spec`). At Johannesburg 2026 the levels add to
114.6%; in the 2021 backtest they added to 100.0–112.4% across the eight
metros. The owner (2026-10-21, OWNER-DECISIONS item 12) asked whether every
party should be scaled the same, and chose to test the alternative now, with
the note: "no point adhering to a level when one has a history of the level
decreasing".

**Already known before this was written:** the preview at Johannesburg 2026
from today's trace (no backtest). Under arm V below: DA 26.6 → 30.0, ANC 22.5
→ 25.2, ActionSA 12.6 → 13.2, EFF 10.1 → 9.8, MK 9.1 → 3.1, PA 6.4 → 5.5
(points of list vote, proportional → V). Nothing about the backtest under
either alternative is known.

## Method

`audits/2026-10-21-scaling-by-uncertainty/run.py` scores every city-year in
`data/processed/history.json` (24: eight metros × 2011, 2016, 2021) with
`compare_history.run_city_year` at 1,000 draws, seed 20261104 (the manifest's),
in process, one arm per process. The wrapper takes the centres
`blended_centres` returns (after the size pull) and, where they sum to `T`,
replaces them by `c_i − (T − 1) · u_i / Σu`, so they sum to 1 and
`pool_spec`'s proportional division becomes the identity. A party whose
reduction would exceed 90% of its centre is held at 10% of its centre and the
rest of the excess is spread over the others by the same rule (iterated). If
`T ≤ 1` the centres are left alone (the shortfall case, rare, is not part of
the question).

`u_i` is built from the model's own width for the party, `σ_i` =
`montecarlo.poll_model_sd` (the draw's total log width at the party's share,
newness included for a party with no previous local list share), read from the
same width record the run uses:

* **P (control):** no wrapper. Proportional, as shipped.
* **V:** `u_i = (c_i σ_i)²`, the variance of the party's share. The standard
  rule for imposing a sum on independent estimates.
* **H:** `u_i = c_i σ_i²`, halfway between V and proportional (proportional is
  `u_i = c_i`).

**Instruments**, summed over the 24 city-years and per election year:
average list-vote error (`pr_mae`, vote-weighted, points), wards called wrong,
seats given to the wrong party (half the summed absolute seat error). Also the
signed list-vote error of parties new to the city at each target (no previous
local list share), summed, and of the three largest.

## Decision rule (fixed now)

An alternative replaces proportional scaling only if, against P, it has (1) a
lower summed list-vote error over the 24 city-years, (2) a lower one in at
least two of the three election years, and (3) no more seats given to the
wrong party in total. If both V and H pass, the one with the lower summed
list-vote error. Otherwise proportional stays. The owner decides; this is the
recommendation.

## Predictions

S1. **Control.** P reproduces `history.json`: `pr_mae` within 1e-12 and seat
errors identical in every city-year.

S2. Under V the levels of parties new to the city fall sharply wherever the
levels sum above 1, because their widths are the largest: their summed signed
list-vote error moves down by more than 3 points over the panel.

S3. V fails the decision rule. The reasoning, not checked against the record
before writing: if new parties are under-forecast more often than
over-forecast in this record, taking the excess from them makes those misses
worse.

S4. H lies between P and V on every instrument summed over the panel.

S5. The three largest parties' summed signed list-vote error rises (more
over-forecast) under V, because they absorb less of the excess.

## What it can and cannot settle

Three cycles; the arrivals the rule acts on hardest are few (EFF 2016, ActionSA
2021, smaller ones). The owner's point about trajectory is not tested here: the
widths measure how uncertain a level is by size and newness, not whether a
party's record is falling. A party-specific trend is not in the model; this
test cannot add it.
