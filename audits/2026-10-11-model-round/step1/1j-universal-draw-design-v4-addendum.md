# 1j v4 addendum: the level-error treatment, the corrected table, and one recommendation

This addendum answers the review `step2/2-review-1j-v4.md` (3522e25). v4 is kept unedited; this replaces the parts of v4 it names.

**Method and limits.** Read-only: nothing in `src/`, `tests/` or `data/` was written. No model run, no `compare_history`, no emit, no sub-delegation. Scripts are in the session scratchpad, `uni4/` (`v4.py` with modes L1, L2, L2′ and the clamp, `wv.py` with randomised PIT, `sum2.py`, `e4.py`, `e5.py`); none is committed. Labels as v4.

## Recommendation for the owner

**Adopt v4 with the level error left out of the draw (option L1), and correct the centres for that error next round.**

**What it is.** One smooth curve sets every party's spread from its size, fitted to every party in every metro and past election at once. Parties new to a city get one extra term, the same for all.

The model's centres for small parties are systematically off by size. The curve measures that error, and it is not counted as spread. It is filed as the correction the next round applies to the centres.

**Reasons:**

- **One rule over the whole vote**, as the owner asked: no bands, no anchors, nobody removed.
- **Whole elections look like real ones.** On the backtests, 27.5% of simulated elections fall outside the real record on two or more key measures, against 36% today. The real elections did so 4 times in 16, against 4.4 expected.
- **Small-party explosions nearly disappear.** At Johannesburg 2026, draws in which a party that had under 1% last time exceeds 5% fall from 403 to 18-20 in 5,000.
- **It is the only v4 version that passes the large-party rule, on both fits** (with and without COPE and ActionSA). It makes the ANC and DA tighter than today (log spread 0.16, against 0.34 and 0.21) without scoring worse on them.

**What still fails or is uncertain:**

1. **Too few small parties climb past 1%.** The draws show it rarely; real elections showed it 3 times in 16. The test fails (P 0.000-0.013), with a second ≥1% test failing alongside (P 0.007-0.013). The reason is that small parties' centres are set too low. Until next round's centre correction, this option is narrower than the uncorrected centres warrant for parties under about 3%. The versions that carry the level error in the draw (L2, L2′) pass both of these tests but fail the large-party rule.
2. **The middle-party rule fails in every design.** The cause is the 2016 backtest's width for new parties, which comes from COPE's 2011 collapse, applied to the EFF.
3. **MK's spread is about 0.85 in log, against 0.60 today.** That width comes from the ~200 small newcomers, extrapolated. The record cannot say whether a large newcomer is wider or narrower. A judged width for MK belongs in the optional judgement overlay, which the forecast reports with and without.
4. **2011 cannot be tested.**

---

## 1. The level error in the draw: L1, L2 and L2′

The three treatments differ in whether the size-related error of the centres, `m(s)`, enters the draw, and with what co-movement:

| treatment | m(s) in the draw | co-movement it implies |
|---|---|---|
| L1 | none; filed as the centre correction for next round | — |
| L2 (v4, withdrawn as the recommendation) | a separate city-wide normal with loading `m(s)` | +1.0 for 0.03% seeds and about −0.2 to −0.38 for every party at 0.3-12%. This is anti-correlation between the smallest parties and the rest, which the record does not show (review §2: city-year residual correlation +0.11) |
| **L2′** (review's proposal) | `m(s)²` added to the existing size-group shared term: loading `√(ρ(s)σ(s)² + m(s)²)` on the one shared normal | every party under 20% moves the same way on it. Total variance is as L2 (E[k²]) |

**Clamp.** `m(s)` is evaluated at `max(s, 0.016%)`, the record's 1st-percentile centre. Without it, the quadratic reaches +1.0 at 0.03% and +1.78 at 0.01%. The clamp applies to L2 and L2′; L1 does not use `m(s)` in the draw.

**Measured consequence of L2′.** Because the shared normal now also carries `m(s)` for parties of 1-12%, those parties move together. Their combined movement shifts the large block through normalisation: ANC and DA log-sd 0.21 (L2′), against 0.18 (L2) and 0.16 (L1). L2′ therefore also fails the large-party rule (§3).

The record measured the shared share of variance for parties of 1-20% as 0.00 in v2/v3 and 0.11 in v4's fit. Carrying the level error as co-movement in that range is not supported by the record either.

---

## 2. Newness: one δ, disclosed

The single newness δ stays: 0.873 on the full record, 0.844 without COPE and ActionSA. A size-dependent variant is not supported (review §3). New parties at 1% and over number 6 party-elections in the full record (COPE 2011, EFF 2016, AIC 2016, GOOD 2021, PA 2021, ASA 2021) and 4 without COPE and ActionSA. Their own δ:

| fit | profile interval | best | improvement in fit over one δ (2ΔNLL) |
|---|---|---|---|
| full | about 0.42-1.78 | near 1.0 | no variant above 2.1 |
| without COPE and ActionSA | 0-1.57 | 0 | no variant above 2.1 |

**MK's log-sd of about 0.85 is the small-arrival δ extrapolated to a 9% party.** The record neither supports nor rejects it.

**The whole-vote record does not call the resulting draws implausible.** The realised largest new party fell outside the record's range in 3 of 16 backtests, against about 3.4 expected under L1 and 4.1 under L2. Johannesburg 2026's draws whose largest new party exceeds 18.12%, about 600 of 5,000, are consistent with that.

A judged centre and width for a large newcomer belong to the §11 overlay. The forecast is reported with and without it.

---

## 3. Corrected side by side

**Column sources.** "Today" is the full model's draws (arm E, `pr_share_draws`). Every other column is the citywide simulation (no IPF, Dirichlet, ward or VD layer; arm E's pool-turnout draws). `noCA` is the fit without COPE and ActionSA; the judging record is always the full real record.

**Backtests.** 16 city-years (2016 and 2021), 1,000 draws each, one seed. Each target is judged by the real transitions before it (strict).

**Exchangeable rate.** A world-like model puts about 5% of draws beyond each end of the record: 1/(n+1) averaged over targets, with n = 16 transitions for 2016 targets and 24 for 2021.

### 3.1 The table

| row | today | v3 A | v3 A noCA | v3 B | v3 B noCA | **v4-L1** | **v4-L1 noCA** | v4-L2′ | v4-L2′ noCA | v4-L2 | v4-L2 noCA |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Whole vote, backtests** | | | | | | | | | | | |
| draws outside the record on ≥ 2 core features (a) | 36.4% | 28.2% | 27.8% | 27.9% | 27.7% | **27.5%** | **27.5%** | 31.8% | 31.7% | 31.1% | 30.7% |
| expected elections with ≥ 2 (realised 4) | 5.8 | 4.5 | 4.4 | 4.5 | 4.4 | 4.4 | 4.4 | 5.1 | 5.1 | 5.0 | 4.9 |
| volatility: draws below / above the record (b) | 0 / 15.4 | 0 / 6.8 | 0 / 5.3 | 0 / 9.2 | 0 / 8.4 | 0 / 7.5 | 0 / 6.1 | 0 / 13.3 | 0 / 12.4 | 0 / 12.4 | 0 / 11.4 |
| largest loss: below / above | 0.3 / 20.4 | 0.5 / 10.2 | 0.4 / 9.9 | 0.4 / 11.1 | 0.4 / 11.0 | 0.6 / 10.6 | 0.6 / 10.1 | 1.0 / 15.5 | 1.0 / 15.1 | 0.9 / 14.9 | 0.8 / 14.4 |
| top-two share: below / above | 25.2 / 0.5 | 25.8 / 1.2 | 24.5 / 0.8 | 25.7 / 1.6 | 24.8 / 1.1 | 26.4 / 0.4 | 25.4 / 0.3 | 29.1 / 8.4 | 28.6 / 6.1 | 28.3 / 7.9 | 27.6 / 5.4 |
| largest new party: below / above; expected outside (realised 3) | 4.2 / 7.5; 1.9 | 9.3 / 10.6; 3.2 | 8.3 / 9.4; 2.8 | 10.2 / 10.8; 3.4 | 9.5 / 10.4; 3.2 | 10.2 / 10.8; 3.4 | 8.8 / 10.2; 3.0 | 14.9 / 11.5; 4.2 | 13.0 / 11.2; 3.9 | 14.4 / 11.2; 4.1 | 12.4 / 10.8; 3.7 |
| parties ≥ 1%: P(as many or more outside as realised) (c) | 0.078 | **0.022** | **0.017** | **0.020** | **0.017** | **0.013** | **0.007** | 0.205 | 0.146 | 0.172 | 0.119 |
| previously sub-1% parties reaching 1%: same test | **0.014** | **0.007** | **0.006** | **0.007** | **0.006** | **0.000** | **0.000** | **0.025** | **0.018** | **0.020** | **0.014** |
| sub-1% mass: realised inside central 90% (randomised PIT, of 16) (d) | **8** | 15 | 15 | 15 | 15 | 14 | 14 | 16 | 15 | 16 | 15 |
| parties ≥ 1%: realised inside central 90% (randomised PIT, of 16) | 14 | 12 | 12 | 12 | 12 | 13 | 12 | 14 | 14 | 14 | 14 |
| **Whole vote, Johannesburg 2026** (judged by all 32 transitions) | | | | | | | | | | | |
| draws outside the record on ≥ 2 core features | 71.7% | 61.0% | 63.0% | 55.1% | 56.3% | 52.4% | 53.2% | 52.4% | 53.1% | 51.3% | 51.8% |
| volatility above the record | 49.9% | 20.6% | 18.8% | 31.6% | 31.5% | 22.9% | 22.2% | 26.7% | 26.2% | 25.4% | 24.7% |
| largest new party above the record | 5.1% | 6.4% | 3.8% | 9.4% | 8.0% | 12.2% | 11.8% | 12.1% | 11.8% | 12.5% | 12.0% |
| **Johannesburg 2026, parties** (5,000 draws; counts the mean of 4 seeds) | | | | | | | | | | | |
| log-sd DA / ANC | 0.21 / 0.34 | 0.13 / 0.13 | 0.12 / 0.12 | 0.16 / 0.17 | 0.15 / 0.16 | 0.16 / 0.16 | 0.16 / 0.16 | 0.21 / 0.21 | 0.20 / 0.20 | 0.18 / 0.18 | 0.18 / 0.18 |
| log-sd ASA / EFF | 0.50 / 0.57 | 0.28 / 0.31 | 0.28 / 0.31 | 0.44 / 0.48 | 0.44 / 0.48 | 0.27 / 0.30 | 0.25 / 0.28 | 0.27 / 0.30 | 0.25 / 0.28 | 0.28 / 0.31 | 0.26 / 0.29 |
| log-sd MK / PA | 0.60 / 0.30 | 0.56 / 0.50 | 0.46 / 0.50 | 0.70 / 0.67 | 0.64 / 0.67 | 0.86 / 0.58 | 0.83 / 0.56 | 0.87 / 0.61 | 0.83 / 0.59 | 0.87 / 0.61 | 0.84 / 0.59 |
| draws: established, previous < 1%, above 5% | 403 | 22.8 | 23.3 | 24.0 | 23.5 | 17.5 | 20.3 | 19.3 | 22.3 | 22.3 | 25.3 |
| draws: any party of centre < 1% above 5% | 853 | 58.5 | 59.8 | 59.5 | 60.0 | 51.8 | 57.8 | 59.0 | 65.5 | 62.8 | 69.5 |
| draws: largest new party above 18.12% | 255 | 325 | 196 | 471 | 400 | 602 | 581 | 605 | 582 | 607 | 589 |
| **Backtests, must-not-worsen** | | | | | | | | | | | |
| large parties: score difference [90% city-year bootstrap] (e) | — | −0.171 [−0.316, −0.008] | −0.213 [−0.366, −0.042] | −0.158 [−0.286, −0.019] | −0.190 [−0.324, −0.045] | **−0.159 [−0.293, −0.006]** | **−0.198 [−0.344, −0.030]** | +0.024 [−0.066, +0.117] | −0.040 [−0.134, +0.063] | +0.039 [−0.065, +0.147] | −0.028 [−0.137, +0.093] |
| large-party rule | — | passes | passes | passes | passes | **passes** | **passes** | fails | fails | fails | fails |
| large parties inside 90% band (of 32) | 32 | 30 | 30 | 31 | 31 | 31 | 30 | 32 | 32 | 32 | 32 |
| middle parties: score difference; rule | — | +0.143; fails | −0.043 (upper +0.136); fails | +0.364; fails | +0.236; fails | +0.261; fails | +0.068 (upper +0.318); fails | +0.327; fails | +0.137; fails | +0.320; fails | +0.137; fails |
| wrong-party seats, list proxy, 2016 / 2021 | 71.8 / 154.9 | 72.6 / 153.1 | 72.4 / 153.1 | 72.7 / 153.2 | 72.6 / 153.3 | 72.4 / 152.5 | 72.4 / 152.5 | 72.7 / 152.0 | 72.6 / 152.0 | 72.5 / 152.4 | 72.3 / 152.4 |

Bold P-values are failures of 1h §3.2 (P < 0.05).

### 3.2 Notes to the table: deviations from step 1h

- **(a)** The joint count uses **7 of 1h's 8 core features**. `w_top` cannot be computed because the citywide simulation has no ward layer. Today's 36.4% is therefore not 1h §4.1's 47.2%.
- **(b)** Exceedance is reported **below and above separately**, as 1h asks. The ±1 IQR outer envelope is not reported.
- **(c)** PIT is **randomised** for count features: ties with the realised value are split uniformly. v4's raw-PIT counts for `n_ge1`, `n_ge5` and `tiny_n_ge1` are superseded.
- **The combined share outside the two largest parties is dropped as a separate row.** It is exactly 100 − top two, which is already a core feature; the top-two row carries it.
- **(d), (e) Not like-for-like** (review §5, point 5). Today's column is the full model; the others are the citywide simulation. One seed per city-year adds about a point of Monte Carlo noise to the rates.

### 3.3 What the table shows

- **L1 against L2 and L2′:** carrying the level error as shared uncertainty widens the large parties through normalisation, and fails the large-party rule on both fits. It also adds draws beyond the record at both ends on volatility and the top-two share. In exchange it passes the parties-≥-1% test, which L1 fails.
- **v4-L1 against v3 A and B:** on the whole vote they are nearly identical (27.5-28.2% joint). v4-L1 has the fewest small-party explosions (17.5-20.3) and passes the large-party rule. It gives MK a wider draw (0.86 against 0.56-0.70).
- **Without COPE and ActionSA** the changes are small on the whole vote and on v4. The largest changes are v3 A's MK (0.56 → 0.46) and the middle-party scores, as v4 §3.1 found.

---

## 4. Judgement calls changed

| # | call | value | evidence | how checked |
|---|---|---|---|---|
| 33 (replaces v4's) | level error | **L1**: fitted jointly and not carried in the draw; `m(s)`, clamped at 0.016%, is handed to the level layer as next round's centre correction | §1, §3: L2 and L2′ fail the large-party rule; L2's co-movement contradicts the record | the writer prints `m(s)`; L2′ runs as a paired arm |
| 36 | clamp | `m(s)` evaluated at no less than 0.016% (the record's 1st-percentile centre) | review §1 | — |
| 37 | newness | one δ, with MK-type extrapolation disclosed; large newcomers via the §11 overlay | §2 | the overlay is reported with and without |

---

## What I re-derived and what I did not

**Re-derived:**

- L2′ and the clamped L2;
- the whole-vote measures for all eleven columns, with randomised PIT and one-sided exceedance;
- Johannesburg 2026 and backtest scores for L2′ and the clamped L2 under both fits.

L1, v3 A and v3 B figures are from v4's runs, which the review reproduced; their whole-vote rows were rerun with randomised PIT.

**Not done:**

- the ±1 IQR envelope;
- ward and turnout features;
- the real drawer.
