# Pre-registration: ward-contest rule, small-party geography, national-record fits (2026-10-16)

Written before the re-emit. Changes since the §1.304/§1.306 runs: `17a59c1`
(pool-placed parties keep geography), `f309113`/`1a38b2a` (one slate source;
every slated party's ward ballot masked to its wards; ward-only parties leave the
list ballot, §U1/§U2), `a3f039d`/`65d169c` (a party with its own national
record is fitted on it; MK option A, §1.307). Baselines: the published model
(arm A, `data/arms/step11/A`, history at `7f0a921`) and the last rebuild
(`.claude/rebuild-2026-10-15b/with`, history at `bb280c8`).

Gates: G2 the 2026 roll sums to 2,417,915 (unchanged). No party wins a ward
outside its slate in any draw (2026 and every backtest city-year). Ward-only
parties have zero list share in every draw.

Predictions, from the mechanisms (citywide shares are set before geography;
pool vectors do not place a party that has its own map):
P1. Johannesburg 2026: every party's mean list share moves under 0.5 points
    against the last rebuild (ward-only parties' list mass, ~0.4% of the list
    vote, is shared pro rata). Mean seats move under 2 for every party.
P2. Johannesburg 2026: ward favourites change in under 8 wards; MK wins no ward
    it does not contest (it did in ~5% of draws).
P3. Backtests: 2021 city-years move only through the ward mask and small-party
    geography (no 2021 national-record fits apply); list error changes under
    0.10 points per city-year; ward hit rate changes by at most 2 wards per
    city-year.
P4. Backtests 2011/2016: the national-record fits (COPE 2011, EFF/PA/AGANG
    2016, …) do not move any VD's mean share (pool vectors do not place a party
    with a map); list error changes under 0.15 points per city-year.
P5. Small-party sizing: the model's ward-ballot share for ward-only parties
    stays far above their real share (2021: 0.00070 against 0.000027).
Scored in the round's report, including what it got wrong.
