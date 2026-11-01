# Pre-registration: Johannesburg 2026 seats with the census group mix adjusted (2026-10-30)

**Question (owner, 2026-10-30):** "if we take census as is and adjust census as
reporting suggests - what is the difference in seats?"

**Arms**, Johannesburg 2026, paired (same seed, same draws, same tree), every
other input as in the frozen forecast's settings. Only the ward population-group
shares change; the roll still sizes every ward. The pool spec is re-fitted under
each arm's shares (outside `data/`), and the run's per-VD composition uses the
same shares.

| arm | ward group shares |
|---|---|
| **B** | Census 2022 as read today |
| **N** | Census 2022 with the national overstatements removed (white −290,000 of 4,525,800 = −6.41%; Indian/Asian −190,000 of 1,705,882 = −11.14%; Moultrie & Dorrington 2024), renormalised per ward |
| **E** | Census 2011 moved onto the 2021 wards (`pools.reproject`), all ages. A larger, different mix: a sensitivity of seats to composition, not a correction |

**Scored:** mean seats per party (270-seat council), 5th-95th percentile,
P(largest party), P(majority coalition routes the site reports), per-ward
winner probability; changes N−B and E−B with paired Monte Carlo error.

**Mechanism.** Composition enters twice: (1) the pool fit, which sets each
group's party rates so that the 2021 ward results are reproduced, and (2) the
run, which places those rates in each VD by its ward's mix. Changing the mix
changes the fitted rates in the opposite direction, so the 2021 result is
still reproduced; what can move 2026 is only how a mix difference interacts
with the change between 2021 and 2026 (new parties, shifts). The national
correction moves no ward's white share by more than 1.31 points and the
roll-weighted citywide mix by 0.31 (white) and 0.36 (Indian/Asian) points
(`DATA-QUALITY.md` 23, measured).

**Predictions** (written before any run):

- P1. N−B: no party's mean seats move by more than 1.0 seat.
- P2. N−B: no ward's winning-party probability moves by more than 5 points.
- P3. N−B: P(largest party) moves by less than 2 points for every party.
- P4. E−B: changes are larger than N−B for at least the DA and the ANC
  (|Δ mean seats|), because the 2011 mix differs by up to 32 points per ward.
- P5. E−B: still no party's mean moves by more than 4 seats, because the pool
  fit re-absorbs most of a mix change against the same 2021 result.

**Falsified by** any stated bound being exceeded beyond twice the paired Monte
Carlo error. **Void if** anything under `data/` is written, or the arms do not
share seed, draws and tree.

Not a model change: nothing here alters the published forecast.
