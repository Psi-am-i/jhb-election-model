# 1j v4. One width curve for the whole vote

This version follows the owner's direction of 2026-10-12: "we were trying to look at the whole vote not just certain segments". The draw keeps the form of v2 and v3, but its width comes from **one smooth curve fitted jointly to every party-election in the record**.

- No bands are used as estimators, there is no bridge between anchors, and no party is removed. The owner's addition, "drop cope and actionSA from the record when we are evaluating options. With and without", is honoured by fitting everything twice and presenting both side by side. Neither fit is chosen here.
- The result is judged on the whole vote: the whole-election plausibility measures of step 1h, plus the combined share of everything outside the two largest parties.
- The origin table of new-to-city parties is kept as an appendix, as information only. `1j-arrivals-and-outliers.md` (9967be5) is superseded wherever it proposed dropping or setting aside parties.

**Constraints.** Read-only: nothing in `src/`, `tests/` or `data/` was written. No model run, no `compare_history`, no emit, no sub-delegation. Scripts are in the session scratchpad, `uni4/` (`v4.py`, `wv.py`, `sumwv.py`, `e4.py`, `e5.py`); none is committed.

**Labels.** *Measured* means computed by those scripts. *Citywide simulation* means the v2/v3 reimplementation of the draw: normal own term, shared factor, κ solved on an independent calibration sample, arm E's pool turnouts. It has no IPF, ward or VD layer, so turnout and ward features are not scored. *Full* and *without COPE and ActionSA* name the two fits; the second deletes every row of both parties, in every metro and cycle, from the width record only. The draws still contain those parties wherever they are on the ballot, and the judging record is the real record, unchanged.

## Summary for the owner

How wide each party's draw is now comes from one smooth curve over all party sizes, fitted to every party in every metro and every past election at once.

**Parties new to a city** get one extra term, the same for every new party.

**The over-wide small parties.** The very smallest parties used to come out too wide because the model's centres for them are systematically off. A second smooth curve, fitted jointly, now captures that systematic error. It is still counted as uncertainty the draws share, not as each party's own noise. That keeps the draw honest while the centres remain uncorrected; the correction itself belongs to the next round.

**The whole vote.** The three designs now on the table (v3 option A, v3 option B and v4) behave much alike, and all are far closer to the record than today's model:

- **Draws outside the record on two or more key measures:** about 28-31% of backtest draws, against 36% today. The real elections show this 4 times in 16 (the models expect 4.4 to 5.0).
- **Everything outside the two largest parties:** comparably plausible in all of them.

**Where v4 differs:**

- Its single newness term is fitted mostly on the 200-odd small arrivals, and it widens national debutants. MK at Johannesburg 2026 gets a log spread of 0.84-0.87, against 0.60 today. A new party then exceeds the largest new-party share on record in about 600 of 5,000 draws, against 255 today.
- Its large parties are a little wider than in v3, about 0.18. On the backtests that costs it the large-party pass mark on the full record. It passes on neither fit.

**Without COPE and ActionSA.** Removing them changes the curve itself little. For the whole-vote measures, at most three points of draws move. It matters most in three places:

- v3 option A's debutant width: MK's spread 0.56 → 0.46; largest-new-party draws 325 → 196;
- the backtest middle-party score, which improves in every design;
- v4's large-party score, which turns from a small loss to a small gain.

---

## 1. The curve

For every party-election *i* in the earlier backtest cycles, the residual `r_i` is in v1's frame:

- for every party below 20%, it is measured relative to the large block;
- for parties at or above 20%, it is the within-block residual.

The residual is modelled as

    r_i ~ Normal( m(s_i) − σ_i²/2 ,  σ_i² )
    σ_i² = σ(s_i)² + δ²·new_i
    σ(s) = a + (b − a) / (1 + exp(k·(log s − log s_mid)))      one smooth width curve over all sizes
    m(s) = c1·L + c2·L²,  L = min(log(s / 20%), 0)              a smooth location curve, 0 for the large block
    new_i = 1 if the party had no result at the previous local election in this city, else 0

The terms:

- `s` is the party's `pool_spec` centre. The curve is fitted by weighted maximum likelihood over all party-elections, with weights of 1 per party-cycle. Each target uses only earlier cycles, and the location fixed point of v2 §2.3 is applied (two iterations).
- `−σ²/2` is the offset-aware location of a mean-preserving draw.
- `m(s)` is the systematic level error of the centres by size. Fitting it jointly means the level error is not read as spread. This is what pulled v1's curve up at the bottom without excluding anyone.
- δ is the one newness term.

Bands appear only as diagnostics (§1.3).

### 1.1 Fitted curves (2026 record; all three cycles)

| | full record | without COPE and ActionSA |
|---|---|---|
| party-elections / party-cycles | 589 / 237 | 561 / 233 |
| width curve a / b / midpoint / steepness | 0.030 / 0.816 / 8.56% / 2.57 | 0.030 / 0.827 / 8.05% / 2.46 |
| newness δ | **0.873** | **0.844** |
| location c1 / c2 | +0.342 / +0.075 | +0.352 / +0.076 |
| width at 25% / 11.7% / 9.1% / 5.8% / 3% / 1.5% / 0.5% / 0.2% / 0.05% | 0.077 / 0.274 / 0.393 / 0.603 / 0.766 / 0.807 / 0.815 / 0.815 / 0.816 | 0.076 / 0.258 / 0.369 / 0.580 / 0.763 / 0.815 / 0.826 / 0.827 / 0.827 |
| location m(s) at 11.7% / 5.8% / 1.5% / 0.5% / 0.2% / 0.05% | −0.16 / −0.31 / −0.38 / −0.24 / +0.01 / +0.64 | −0.17 / −0.32 / −0.40 / −0.26 / −0.00 / +0.63 |
| shared share of variance, < 1% / 1-20% | 0.33 / 0.11 | 0.29 / 0.12 |

The same model without a location curve (2026 record): b 0.925 / 0.958 and δ 0.687 / 0.606 (full / without COPE and ActionSA). The level error then inflates the width of every party under 3% by about 0.1-0.15.

Earlier records, used for the backtests:

| record | fit | b | δ | location at 0.5% | shared share, < 1% / 1-20% |
|---|---|---|---|---|---|
| 2021 (2011-2016) | full | 0.774 | 0.945 | −0.59 | 0.28 / 0.18 |
| 2021 | without COPE and ActionSA | 0.777 | 0.916 | −0.60 | 0.20 / 0.16 |
| 2016 (2011 only) | full | 0.720 | 0.955 | −0.87 | 0.00 / 0.00 |
| 2016 | without COPE and ActionSA | 0.804 | 0.697 | −0.77 | 0.00 / 0.00 |

With one cycle, the location curve **is** that cycle's swing, which is why the 2016 shared shares are zero (§1.2).

### 1.2 The location curve: counted as shared uncertainty

`m(s)` is the centres' average size-related error. Three treatments were measured:

| label | treatment | consequence |
|---|---|---|
| L0 | no location curve | the level error is counted as each party's own spread. This is v1's problem: tiny parties too wide |
| L1 | location fitted and dropped | narrower draws. They are centred where the model says, which the record shows is off by `m(s)`. For the 2016 backtest, whose record is one cycle, L1 also discards that cycle's whole swing (shared share 0) |
| **L2 (proposed)** | location fitted, and the draw carries it as a second shared term with loading `m(s)` (stream `level.shared_loc`) | each party's own spread excludes the level error, but the draws still move by it, jointly across parties of a size |

**Why L2.** A bias the centres still carry is uncertainty for a forecast of an unknown cycle (CLAUDE.md §4: a forecast carries E[k²], not the mean). It is shared by parties of a size, not independent per party. L1 would be right only once the centres are corrected. That correction belongs to the level layer next round, and the fitted `m(s)` is its out-of-sample input.

The cost: L2 widens the large parties through normalisation (ANC and DA log-sd 0.18, against 0.16 under L1). On the backtests the large-party score is then about +0.04 on the full record against −0.16 for L1 (§3). The owner can take L1 instead; both are shown.

### 1.3 Diagnostics only: bands against the curve

The band roots of v3, under the same weights, are printed by the writer beside the curve: 1-5% 0.84, 0.3-1% 0.82, 0.1-0.3% 0.90, under 0.1% no root. The curve with location gives 0.77-0.82 across 0.2-3%. Without location it gives 0.90-0.93: the location term removes the excess that v1 and the review found. No band is used to set a width.

### 1.4 Newness: one term

One δ applies to every party new to the city: seeded arrivals and national debutants alike. Under the full fit it is 0.873 for 2026.

The record measured the two kinds apart in earlier documents: national debutants 0.0-0.48 extra, seeds about 0.74-0.85. One term therefore widens national debutants beyond their own record. At Johannesburg 2026 that is MK, RISE and BOSA: MK's log-sd is 0.87, against 0.56-0.70 under v3.

The §11 judgement overlay is where a judged centre and width for such a party belong. It stays optional, and a forecast is reported with and without it.

---

## 2. The whole vote, judged against the record

Whole-election features of step 1h are computed for each draw: Pedersen volatility, new parties' share, the largest new party, the largest gain and loss, the effective number of parties and its change, parties at ≥ 1% and ≥ 5%, the sub-1% mass, the largest and combined share of previously sub-1% parties, and how many of them reach 1%. To these is added the **combined share outside the two largest parties** (`outside2` = 100 − top two).

Each target is judged by the real transitions before it (strict mode: 2016 by 2000-2011; 2021 by 2000-2016; Johannesburg 2026 by all 32). The backtests are the 16 city-years of 2016 and 2021. A world-like model puts about 10% of its draws outside the record's range across both ends (exchangeable rate, 1h §2.3). The 2026 level features sit beyond the local record because Johannesburg's 2024 national result already went past it (1h §2.3).

### 2.1 Side by side

`noCA` marks the fit without COPE and ActionSA. The judging record is always the full real record.

| measure (backtests: 16 city-years, 2016 and 2021) | today (arm E) | v3 A | v3 A noCA | v3 B | v3 B noCA | **v4** | **v4 noCA** | v4-L1 | v4-L1 noCA |
|---|---|---|---|---|---|---|---|---|---|
| draws outside the record on ≥ 2 of 7 core features | 36.4% | 28.2% | 27.8% | 27.9% | 27.7% | 31.0% | 30.7% | 27.5% | 27.5% |
| expected / realised elections with ≥ 2 (realised 4) | 5.8 | 4.5 | 4.4 | 4.5 | 4.4 | 5.0 | 4.9 | 4.4 | 4.4 |
| outside the two largest: draws outside the record | 25.7% | 27.1% | 25.3% | 27.2% | 26.0% | 36.2% | 33.0% | 26.8% | 25.7% |
| outside the two largest: realised in central 90% / 50% | 15 / 12 | 15 / 10 | 15 / 9 | 15 / 11 | 15 / 11 | 16 / 12 | 16 / 12 | 15 / 9 | 15 / 9 |
| volatility: draws outside the record | 15.4% | 6.8% | 5.3% | 9.2% | 8.4% | 12.5% | 11.4% | 7.5% | 6.1% |
| largest new party: draws outside | 11.7% | 19.9% | 17.8% | 21.0% | 19.9% | 25.6% | 23.2% | 21.0% | 19.0% |
| largest loss: draws outside | 20.7% | 10.7% | 10.3% | 11.5% | 11.4% | 15.8% | 15.2% | 11.3% | 10.7% |
| sub-1% mass: realised in central 90% | **8/16** | 15 | 15 | 15 | 15 | 16 | 15 | 14 | 14 |
| parties ≥ 1%: P(as many or more elections outside than realised) | 0.078 | **0.022** | **0.017** | **0.020** | **0.017** | 0.173 | 0.119 | **0.013** | **0.007** |
| previously sub-1% parties reaching 1%: same test | **0.014** | **0.007** | **0.006** | **0.007** | **0.006** | **0.020** | **0.014** | **0.000** | **0.000** |
| **Johannesburg 2026** | | | | | | | | | |
| draws outside the record on ≥ 2 core features | 71.7% | 61.0% | 63.0% | 55.1% | 56.3% | 51.2% | 51.9% | 52.4% | 53.2% |
| outside the two largest, p5 / median / p95 | 37.1 / 49.6 / 59.6 | 42.1 / 50.3 / 58.1 | 42.6 / 50.4 / 57.9 | 39.4 / 49.6 / 58.3 | 39.8 / 49.7 / 58.3 | 38.1 / 49.3 / 60.2 | 38.3 / 49.3 / 60.4 | 39.9 / 49.5 / 58.8 | 40.3 / 49.6 / 58.7 |
| volatility: draws above the record | 49.9% | 20.6% | 18.8% | 31.6% | 31.5% | 25.6% | 24.9% | 22.9% | 22.2% |
| largest new party: draws above the record | 5.1% | 6.4% | 3.8% | 9.4% | 8.0% | 12.6% | 12.1% | 12.3% | 11.9% |

Bold marks a 1h §3.2 failure (P < 0.05, or fewer than 18 of 24 inside the central 90%; scaled to 16 that is about 12).

### 2.2 What the whole vote says

- **Every new design is closer to the record than today's model** on joint implausibility, volatility, the largest loss and the sub-1% mass. Today's sub-1% mass is the clearest failure: the realised value sits in the central 90% of draws in only 8 of 16 city-years.
- **v3 A, v3 B and v4 differ little on the whole vote.** v4 (L2) puts somewhat more draws outside the record on volatility, the largest new party and `outside2`: wider, through the shared location term and the newness term. It is the only design that passes the parties-≥-1% test (0.173 and 0.119 against 0.007-0.022).
- **One failure remains in every design:** too few previously sub-1% parties reach 1% in the draws (P 0.000-0.020). The centres of rising small parties are low (v2 §8.3); the widths do not fix that.
- **Johannesburg 2026's combined share outside the two largest** has a median of about 49-50% in every design. Its 5-95% range runs from about 38-60% (v4, today) to 42-58% (v3 A). The local record's largest is 41.3% (Johannesburg 2021), so most draws are beyond it in every design; the 2024 national result in the city is already beyond it as well.

---

## 3. §8 recomputed: v3 A, v3 B and v4 side by side, both fits

Johannesburg 2026 is the citywide simulation, 5,000 draws (party widths from one seed, counts the mean of four). The backtests are 2016 and 2021, with a city-year cluster bootstrap 90% interval. The must-not-worsen rule passes when the 90% upper bound of the score difference is at most +0.05 points.

| | today | v3 A | v3 A noCA | v3 B | v3 B noCA | **v4** | **v4 noCA** | v4-L1 | v4-L1 noCA |
|---|---|---|---|---|---|---|---|---|---|
| **JHB 2026 log-sd** DA / ANC | 0.21 / 0.34 | 0.13 / 0.13 | 0.12 / 0.12 | 0.16 / 0.17 | 0.15 / 0.16 | 0.18 / 0.18 | 0.18 / 0.18 | 0.16 / 0.16 | 0.16 / 0.16 |
| ASA / EFF | 0.50 / 0.57 | 0.28 / 0.31 | 0.28 / 0.31 | 0.44 / 0.48 | 0.44 / 0.48 | 0.28 / 0.31 | 0.26 / 0.29 | 0.27 / 0.30 | 0.25 / 0.28 |
| MK / PA | 0.60 / 0.30 | 0.56 / 0.50 | **0.46** / 0.50 | 0.70 / 0.67 | 0.64 / 0.67 | **0.87** / 0.61 | 0.84 / 0.59 | 0.86 / 0.58 | 0.83 / 0.56 |
| draws: established, previous < 1%, above 5% | 403 | 22.8 | 23.3 | 24.0 | 23.5 | 21.8 | 25.3 | 17.5 | 20.3 |
| draws: any party of centre < 1% above 5% | 853 | 58.5 | 59.8 | 59.5 | 60.0 | 62.8 | 70.0 | 51.8 | 57.8 |
| draws: largest new party above 18.12% | 255 | 325 | **196** | 471 | 400 | **607** | 590 | 602 | 581 |
| previously sub-1% parties' combined share, log-sd (record 0.59) | 0.75 | 0.58 | — | 0.59 | — | 0.48 | 0.47 | — | — |
| their draws keeping < 14.6% of previous share (exchangeable 0.005) | 0.740 | 0.072 | 0.077 | 0.074 | 0.079 | 0.107 | 0.110 | — | — |
| **Backtests** large parties: score difference [90%] | — | −0.171 [−0.316, −0.008] | −0.213 [−0.366, −0.042] | −0.158 [−0.286, −0.019] | −0.190 [−0.324, −0.045] | +0.041 [−0.063, +0.149] **fails** | −0.027 [−0.136, +0.095] **fails** | −0.159 [−0.293, −0.006] | −0.198 [−0.344, −0.030] |
| large parties inside 90% band (of 32) | 32 | 30 | 30 | 31 | 31 | 32 | 32 | 31 | 30 |
| middle parties: score difference [90%] | — | +0.143 [−0.119, +0.429] fails | −0.043 [−0.234, +0.136] fails | +0.364 [+0.120, +0.667] fails | +0.236 [+0.055, +0.450] fails | +0.319 [−0.000, +0.686] fails | +0.136 [−0.114, +0.399] fails | +0.261 [−0.052, +0.616] fails | +0.068 [−0.181, +0.318] fails |
| middle parties inside 90% band (of 14) | 13 | 14 | 14 | 14 | 14 | 14 | 14 | 14 | 14 |
| large drawn log-sd median, 2016 / 2021 (realised 0.040 / 0.114) | 0.144 / 0.182 | 0.093 / 0.091 | — | 0.105 / 0.109 | — | 0.145 / 0.143 | 0.122 / 0.140 | 0.106 / 0.106 | 0.083 / 0.100 |
| wrong-party seats, list proxy, 2016 / 2021 | 71.8 / 154.9 | 72.6 / 153.1 | 72.4 / 153.1 | 72.7 / 153.2 | 72.6 / 153.3 | 72.5 / 152.4 | 72.3 / 152.4 | 72.4 / 152.5 | 72.4 / 152.5 |

Every design fails the middle-party rule. The cause is the 2016 national-debutant width applied to the EFF in 2016, which is largest when COPE's 2011 collapse is in the record.

### 3.1 How much removing COPE and ActionSA moves each figure

| figure | v3 A | v3 B | v4 | v4-L1 |
|---|---|---|---|---|
| MK log-sd | 0.56 → 0.46 | 0.70 → 0.64 | 0.87 → 0.84 | 0.86 → 0.83 |
| largest new party above 18.12% (of 5,000) | 325 → 196 | 471 → 400 | 607 → 590 | 602 → 581 |
| middle score difference | +0.143 → −0.043 | +0.364 → +0.236 | +0.319 → +0.136 | +0.261 → +0.068 |
| large score difference | −0.171 → −0.213 | −0.158 → −0.190 | +0.041 → −0.027 | −0.159 → −0.198 |
| whole-vote measures (§2.1) | at most 2.0 points of draws | at most 1.4 | at most 3.2 (`outside2`) | at most 2.0 |
| curve: width at 0.5% / 9.1%; δ | — | — | 0.815 → 0.826; 0.393 → 0.369; 0.873 → 0.844 | as v4 |

**Where the removal matters.** It moves most where a width is built from new-party rows that COPE dominates: v3's separate national-debutant width, the 2016 record of every design, and through it the EFF 2016 backtest. In v4 the single newness term is fitted mostly on about 200 seeded arrivals, so removing two parties moves it little (0.873 → 0.844). The whole-vote measures move by a few points of draws at most.

---

## 4. Judgement calls changed by v4 (added to the v3 addendum's list)

| # | call | value | evidence | how checked |
|---|---|---|---|---|
| 32 | width | one smooth logistic curve in log size, fitted jointly by weighted ML over every party-election, offset-aware | owner direction; §1 | bands printed as diagnostics |
| 33 | level error | a smooth location curve fitted jointly (quadratic in log size below 20%) and carried as a second shared term (L2), or dropped (L1) | §1.2; E[k²] | both printed; L1 is the option once centres are corrected |
| 34 | newness | one term for every party new to the city | owner direction; it widens national debutants beyond their own record (§1.4) | the judgement overlay is reported with and without |
| 35 | record with or without COPE and ActionSA | both fits presented; owner's choice | §3.1 | — |

Calls 1-2 of the addendum (the A/B middle choice and its exception) do not apply to v4; v4 has no anchors. The others stand.

---

## What I re-derived and what I did not

**Re-derived:**

- the v4 curve and location, both fits, all three records, with and without location;
- shared shares;
- the whole-election features for nine designs or fits, plus today's model, on 16 backtests and Johannesburg 2026;
- §8 for v4 (L1 and L2) under both fits;
- v3 A and B under both fits.

**Not done:**

- turnout and ward features (the simulation has no VD or ward layer);
- the real drawer and IPF;
- the location fixed point uses the citywide simulation;
- the "—" cells were not printed by the runs.

---

## Appendix: new-to-city party-elections in the width record (information only)

169 party-elections (322 metro results). The four record categories:

| record category | party-elections | metro results |
|---|---|---|
| no earlier record in any metro or national election | 123 | 208 |
| national record only | 22 | 66 |
| stood in another metro before | 19 | 38 |
| returning to this city | 5 | 10 |

Sourced origins:

| origin | party-elections | which |
|---|---|---|
| split from a named party | 8 | COPE 2011, APC 2011 and 2021, EFF 2016, ASA 2021, GOOD 2021, Abantu Batho Congress 2021, UIM 2021 |
| split party re-entering | 1 | NFP 2021 |
| known-figure vehicle, no parent | 3 | Agang 2016, PA 2016 and 2021 |
| new organisation | 6 | AIC 2011, 2016 and 2021; ATM 2021; Cape Coloured Congress 2021; Northern Alliance 2021 |
| merger in the record window | 0 | the declared mergers are 2025 and 2026 |
| not sourced | 151 | — |

The NFP's 2011 arrival is the generic `ENTRANT` slot and not in the record. The table is information; no party is removed or treated differently on its basis. Sources are as in `1j-arrivals-and-outliers.md` §1.2.

| party | year | metros | record category (cases) | largest realised / centre | origin | source |
|---|---|---|---|---|---|---|
| COPE | 2011 | 8 | national record only (8) | 4.88% / 17.09% | split: left ANC (Lekota, Shilowa, 2008) | pools.SPLITS; SOURCES.md |
| AIC | 2011 | 1 | national record only (1) | 3.58% / 0.72% | new organisation: Matatiele boundary protest by former ANC members (2005) | [Wikipedia](https://en.wikipedia.org/wiki/African_Independent_Congress); [SABC](https://www.sabcnews.com/sabcnews/political-party-african-independent-congress/) |
| ALJAMAAH | 2011 | 1 | national record only (1) | 0.35% / 0.86% | not sourced |  |
| APC | 2011 | 7 | national record only (7) | 0.68% / 0.30% | split: left PAC (Godi, PAC deputy leader, 2007 floor-crossing) | [Mail & Guardian 2007](https://mg.co.za/article/2007-09-04-godi-leaves-pac-for-african-peoples-convention); [Wikipedia](https://en.wikipedia.org/wiki/African_People%27s_Convention) |
| NATIONAL_PARTY_SOUTH_AFRICA | 2011 | 1 | national record only (1) | 0.54% / 0.23% | not sourced |  |
| PAN_AFRICANIST_MOVEMENT | 2011 | 1 | national record only (1) | 0.23% / 0.28% | not sourced |  |
| MOVEMENT_DEMOCRATIC_PARTY | 2011 | 1 | national record only (1) | 0.03% / 0.22% | not sourced |  |
| CAPE_PARTY_KAAPSE_PARTY | 2011 | 1 | national record only (1) | 0.13% / 0.16% | not sourced |  |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | 2011 | 1 | stood in another metro (1) | 0.08% / 0.10% | not sourced |  |
| AFRICAN_CHRISTIAN_ALLIANCE_AFRIKANER_CHRISTEN_ALLIANSIE | 2011 | 2 | stood in another metro (2) | 0.08% / 0.09% | not sourced |  |
| EFF | 2016 | 8 | national record only (8) | 11.64% / 9.47% | split: expelled from ANC (Malema, ANCYL leadership, 2012-13) | pools.SPLITS |
| AIC | 2016 | 6 | stood in another metro (6) | 2.74% / 1.11% | new organisation: Matatiele boundary protest by former ANC members (2005) | [Wikipedia](https://en.wikipedia.org/wiki/African_Independent_Congress); [SABC](https://www.sabcnews.com/sabcnews/political-party-african-independent-congress/) |
| AGENCY_FOR_NEW_AGENDA | 2016 | 1 | no record (1) | 1.57% / 0.49% | not sourced |  |
| PEOPLES_ALLIANCE | 2016 | 1 | no record (1) | 0.16% / 0.96% | not sourced |  |
| UNITED_FRONT_OF_THE_EASTERN_CAPE | 2016 | 2 | no record (2) | 0.80% / 0.94% | not sourced |  |
| AGANG | 2016 | 3 | national record only (3) | 0.04% / 0.67% | vehicle of a known figure, no parent (Ramphele, 2013) | [Wikipedia](https://en.wikipedia.org/wiki/Agang_South_Africa); [Britannica](https://www.britannica.com/topic/Agang-SA) |
| FORUM_4_SERVICE_DELIVERY | 2016 | 1 | no record (1) | 0.04% / 0.55% | not sourced for 2016; merged into ActionSA in 2025 | SOURCES.md (mergers) |
| AZANIAN_ALLIANCE_CONGRESS | 2016 | 1 | no record (1) | 0.13% / 0.49% | not sourced |  |
| BOTSHABELO_UNEMPLOYED_MOVEMENT | 2016 | 1 | no record (1) | 0.12% / 0.49% | not sourced |  |
| UNITED_FRONT_OF_CIVICS | 2016 | 3 | no record (3) | 0.02% / 0.44% | not sourced |  |
| DEMOCRATIC_LIBERAL_CONGRESS | 2016 | 1 | no record (1) | 0.43% / 0.14% | not sourced |  |
| AFRICAN_PEOPLE_S_SOCIALIST_PARTY | 2016 | 3 | no record (3) | 0.02% / 0.43% | not sourced |  |
| AFRICAN_MANDATE_CONGRESS | 2016 | 1 | no record (1) | 0.09% / 0.41% | not sourced |  |
| PA | 2016 | 5 | national record only (4); no record (1) | 0.29% / 0.19% | new organisation around known figures, no parent (McKenzie, Kunene, 2013) | [News24 2013](https://www.news24.com/southafrica/news/cape-gangsters-form-political-party-20131201); [Wikipedia](https://en.wikipedia.org/wiki/Patriotic_Alliance) |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | 2016 | 1 | returning (1) | 0.28% / 0.25% | not sourced |  |
| ALTERNATIVE_DEMOCRATS | 2016 | 1 | no record (1) | 0.25% / 0.28% | not sourced |  |
| DEMOCRATIC_INDEPENDENT_PARTY | 2016 | 1 | no record (1) | 0.28% / 0.10% | not sourced |  |
| BUILDING_A_COHESIVE_SOCIETY | 2016 | 3 | no record (3) | 0.03% / 0.27% | not sourced |  |
| MINORITIES_OF_SOUTH_AFRICA | 2016 | 1 | no record (1) | 0.27% / 0.15% | not sourced |  |
| AFRICAN_POWER_MOVEMENT | 2016 | 1 | no record (1) | 0.03% / 0.27% | not sourced |  |
| UBUNTU_PARTY | 2016 | 3 | no record (3) | 0.04% / 0.27% | not sourced |  |
| ALLIED_MOVEMENT_FOR_CHANGE | 2016 | 1 | no record (1) | 0.08% / 0.21% | not sourced |  |
| UNITED_CONGRESS | 2016 | 1 | national record only (1) | 0.10% / 0.19% | not sourced |  |
| ALJAMAAH | 2016 | 2 | stood in another metro (2) | 0.18% / 0.19% | not sourced |  |
| INTERNATIONAL_REVELATION_CONGRESS | 2016 | 2 | no record (2) | 0.03% / 0.19% | not sourced |  |
| PALMRIDGE_COMMUNITY_FORUM | 2016 | 1 | no record (1) | 0.03% / 0.19% | not sourced |  |
| PAN_AFRICAN_SOCIALIST_MOVEMENT_OF_AZANIA | 2016 | 1 | no record (1) | 0.03% / 0.19% | not sourced |  |
| UNITED_RESIDENTS_FRONT | 2016 | 2 | stood in another metro (2) | 0.03% / 0.18% | not sourced |  |
| BOLSHEVIKS_PARTY_OF_SOUTH_AFRICA | 2016 | 1 | no record (1) | 0.00% / 0.18% | not sourced |  |
| PREM_PEOPLES_AGENDA | 2016 | 1 | no record (1) | 0.01% / 0.18% | not sourced |  |
| EKURHULENI_COMMUNITY_MOVEMENT | 2016 | 1 | no record (1) | 0.04% / 0.18% | not sourced |  |
| AFRICAN_MANTUNGWA_COMMUNITY | 2016 | 1 | no record (1) | 0.18% / 0.08% | not sourced |  |
| PEOPLE_S_CIVIC_ORGANISATION | 2016 | 1 | stood in another metro (1) | 0.01% / 0.17% | not sourced |  |
| PATRIOTIC_ASSOCIATION_OF_SOUTH_AFRICA | 2016 | 2 | no record (2) | 0.05% / 0.17% | not sourced |  |
| PEOPLE_S_REVOLUTIONARY_MOVEMENT | 2016 | 1 | no record (1) | 0.17% / 0.14% | not sourced |  |
| TRULY_ALLIANCE | 2016 | 1 | stood in another metro (1) | 0.08% / 0.16% | not sourced |  |
| INDEPENDENT_CIVIC_ORGANISATION_OF_SOUTH_AFRICA | 2016 | 1 | stood in another metro (1) | 0.12% / 0.16% | not sourced |  |
| THE_PROMISE_OF_FREEDOM | 2016 | 1 | no record (1) | 0.02% / 0.15% | not sourced |  |
| PAC | 2016 | 1 | returning (1) | 0.09% / 0.15% | not sourced |  |
| SOUTH_AFRICAN_POLITICAL_PARTY | 2016 | 1 | no record (1) | 0.03% / 0.15% | not sourced |  |
| ACADEMIC_CONGRESS_UNION | 2016 | 2 | no record (2) | 0.04% / 0.14% | not sourced |  |
| INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA | 2016 | 1 | stood in another metro (1) | 0.04% / 0.14% | not sourced |  |
| UNITED_PEOPLES_PARTY | 2016 | 1 | no record (1) | 0.13% / 0.14% | not sourced |  |
| INDEPENDENT_PEOPLE_S_PARTY | 2016 | 1 | no record (1) | 0.14% / 0.14% | not sourced |  |
| AZAPO | 2016 | 1 | returning (1) | 0.03% / 0.12% | not sourced |  |
| CHRISTIAN_DEMOCRATIC_PARTY | 2016 | 1 | stood in another metro (1) | 0.09% / 0.11% | not sourced |  |
| INDEPENDENT_SPORT_PARTY | 2016 | 1 | no record (1) | 0.01% / 0.11% | not sourced |  |
| KHOISAN_KINGDOM_AND_ALL_PEOPLE | 2016 | 1 | no record (1) | 0.04% / 0.11% | not sourced |  |
| KHOISAN_REVOLUTION | 2016 | 1 | no record (1) | 0.04% / 0.11% | not sourced |  |
| LOCAL_PEOPLE_S_PARTY | 2016 | 1 | no record (1) | 0.08% / 0.11% | not sourced |  |
| PEOPLE_S_DEMOCRATIC_MOVEMENT | 2016 | 1 | no record (1) | 0.02% / 0.11% | not sourced |  |
| SIZWE_UMMAH_NATION | 2016 | 1 | no record (1) | 0.02% / 0.11% | not sourced |  |
| SOUTH_AFRICAN_PEOPLE_FOR_EQUALITY | 2016 | 1 | no record (1) | 0.01% / 0.11% | not sourced |  |
| SOUTH_AFRICA_PEOPLE_S_PARTY | 2016 | 1 | no record (1) | 0.04% / 0.11% | not sourced |  |
| THE_GREENS | 2016 | 1 | no record (1) | 0.03% / 0.11% | not sourced |  |
| NATIONALIST_COLOURED_PARTY_OF_SOUTH_AFRICA | 2016 | 1 | no record (1) | 0.05% / 0.10% | not sourced |  |
| COLOURED_VOICE | 2016 | 1 | no record (1) | 0.04% / 0.10% | not sourced |  |
| AL_SHURA_PARTY | 2016 | 1 | no record (1) | 0.05% / 0.10% | not sourced |  |
| ASA | 2021 | 4 | no record (4) | 18.12% / 6.71% | split: left DA (Mashaba, former Johannesburg mayor, 2019); vehicle of a known figure | pools.SPLITS; SOURCES.md |
| GOOD | 2021 | 6 | national record only (6) | 3.68% / 3.19% | split: left DA (De Lille, former Cape Town mayor, 2018) | pools.SPLITS |
| CAPE_COLOURED_CONGRESS | 2021 | 4 | no record (4) | 2.83% / 0.17% | new organisation (Fadiel Adams, 2020) | [Wikipedia](https://en.wikipedia.org/wiki/National_Coloured_Congress) |
| NORTHERN_ALLIANCE | 2021 | 1 | no record (1) | 2.09% / 0.18% | new community organisation, Nelson Mandela Bay northern areas (2020) | [HeraldLIVE 2021](https://www.heraldlive.co.za/news/politics/2021-11-08-northern-alliance-at-centre-of-coalition-talks/); [Polity 2024](https://polity.org.za/article/gbeberha-based-national-alliance-formerly-northern-alliance-throws-its-weight-behind-good-for-2024-election-2024-05-20) |
| PA | 2021 | 3 | stood in another metro (3) | 1.78% / 1.76% | new organisation around known figures, no parent (McKenzie, Kunene, 2013) | [News24 2013](https://www.news24.com/southafrica/news/cape-gangsters-form-political-party-20131201); [Wikipedia](https://en.wikipedia.org/wiki/Patriotic_Alliance) |
| DOP | 2021 | 3 | no record (3) | 1.38% / 0.18% | not sourced |  |
| AFRIKAN_ALLIANCE_OF_SOCIAL_DEMOCRATS | 2021 | 1 | national record only (1) | 1.26% / 0.37% | not sourced |  |
| ABANTU_INTEGRITY_MOVEMENT | 2021 | 1 | no record (1) | 1.11% / 0.18% | not sourced |  |
| ATM | 2021 | 8 | national record only (8) | 0.89% / 1.00% | new organisation: political arm of a church council (2018) | [Wikipedia](https://en.wikipedia.org/wiki/African_Transformation_Movement); [Daily Maverick 2019](https://www.dailymaverick.co.za/article/2019-05-06-prophecy-or-political-party-the-atm-a-church-jacob-zuma-a-50-year-history/) |
| AIC | 2021 | 1 | stood in another metro (1) | 0.81% / 0.62% | new organisation: Matatiele boundary protest by former ANC members (2005) | [Wikipedia](https://en.wikipedia.org/wiki/African_Independent_Congress); [SABC](https://www.sabcnews.com/sabcnews/political-party-african-independent-congress/) |
| ACTIVE_CITIZENS_COALITION | 2021 | 1 | no record (1) | 0.81% / 0.13% | not sourced |  |
| ABANTU_BATHO_CONGRESS | 2021 | 7 | no record (7) | 0.65% / 0.22% | split: left NFP (Mavundla, NFP councillor, 2020) | [City Press 2021](https://www.news24.com/citypress/politics/abantu-batho-congress-gets-tough-20210109); [Wikipedia](https://en.wikipedia.org/wiki/Abantu_Batho_Congress) |
| AFRICA_RESTORATION_ALLIANCE | 2021 | 7 | no record (7) | 0.64% / 0.20% | not sourced |  |
| CAPE_INDEPENDENCE_PARTY_KAAPSE_ONAFHANKLIKHEIDS_PARTY | 2021 | 1 | no record (1) | 0.62% / 0.08% | not sourced |  |
| JUSTICE_AND_EMPLOYMENT_PARTY | 2021 | 2 | no record (1); national record only (1) | 0.61% / 0.31% | not sourced |  |
| UIM | 2021 | 8 | no record (8) | 0.56% / 0.37% | vehicle of a known figure who left ANC (de Beer, 2020) | [Cape Argus 2020](https://capeargus.co.za/capetimes/news/2020-10-02-maimane-former-mk-agent-de-beer-join-forces-in-united-independent-movement); [Wikipedia](https://en.wikipedia.org/wiki/United_Independent_Movement) |
| VFPLUS | 2021 | 1 | stood in another metro (1) | 0.52% / 0.43% | not sourced |  |
| NFP | 2021 | 7 | returning (5); stood in another metro (2) | 0.36% / 0.51% | split from IFP (2011); here re-entering cities it skipped in 2016 | pools.SPLITS |
| AFRICAN_DEMOCRATIC_CHANGE | 2021 | 1 | no record (1) | 0.45% / 0.09% | not sourced |  |
| INDEPENDENT_CITIZENS_MOVEMENT | 2021 | 1 | no record (1) | 0.45% / 0.14% | not sourced |  |
| AHC | 2021 | 1 | no record (1) | 0.43% / 0.08% | not sourced |  |
| THE_ORGANIC_HUMANITY_MOVEMENT | 2021 | 8 | no record (8) | 0.10% / 0.37% | not sourced |  |
| AFRICA_S_NEW_DAWN | 2021 | 1 | no record (1) | 0.13% / 0.35% | not sourced |  |
| INDEPENDENT_SOUTH_AFRICAN_NATIONAL_CIVIC_ORGANISATION | 2021 | 4 | no record (4) | 0.34% / 0.16% | not sourced |  |
| BLACK_FIRST_LAND_FIRST | 2021 | 5 | national record only (4); no record (1) | 0.12% / 0.30% | not sourced |  |
| INTERNATIONAL_PARTY | 2021 | 4 | no record (4) | 0.08% / 0.29% | not sourced |  |
| MANGAUNG_COMMUNITY_FORUM | 2021 | 1 | no record (1) | 0.21% / 0.29% | not sourced |  |
| SOUTH_AFRICAN_ROYAL_KINGDOMS_ORGANIZATION | 2021 | 3 | no record (3) | 0.03% / 0.29% | not sourced |  |
| AFRICAN_PEOPLE_FIRST | 2021 | 1 | no record (1) | 0.28% / 0.09% | not sourced |  |
| KZN_INDEPENDENCE | 2021 | 1 | no record (1) | 0.27% / 0.10% | not sourced |  |
| AFRICAN_MULTICULTURAL_ECONOMIC_CONGRESS | 2021 | 1 | no record (1) | 0.26% / 0.21% | not sourced |  |
| FORUM_4_SERVICE_DELIVERY | 2021 | 3 | stood in another metro (3) | 0.16% / 0.24% | not sourced for 2016; merged into ActionSA in 2025 | SOURCES.md (mergers) |
| ALJAMAAH | 2021 | 3 | stood in another metro (3) | 0.22% / 0.20% | not sourced |  |
| APC | 2021 | 1 | stood in another metro (1) | 0.12% / 0.21% | split: left PAC (Godi, PAC deputy leader, 2007 floor-crossing) | [Mail & Guardian 2007](https://mg.co.za/article/2007-09-04-godi-leaves-pac-for-african-peoples-convention); [Wikipedia](https://en.wikipedia.org/wiki/African_People%27s_Convention) |
| PEOPLE_S_FREEDOM_PARTY | 2021 | 2 | no record (2) | 0.20% / 0.10% | not sourced |  |
| BATHO_PELE_MOVEMENT | 2021 | 1 | no record (1) | 0.10% / 0.19% | not sourced |  |
| AFRICAN_COVENANT | 2021 | 2 | national record only (2) | 0.07% / 0.17% | not sourced |  |
| SPECTRUM_NATIONAL_PARTY | 2021 | 5 | no record (5) | 0.05% / 0.17% | not sourced |  |
| GOD_SAVE_AFRICA | 2021 | 6 | no record (6) | 0.08% / 0.17% | not sourced |  |
| ARUSHA_ECONOMIC_COALITION | 2021 | 3 | no record (3) | 0.08% / 0.16% | not sourced |  |
| CIVIC_INDEPENDENT | 2021 | 1 | no record (1) | 0.04% / 0.16% | not sourced |  |
| PROGRESSIVE_COMMUNITY_MOVEMENT | 2021 | 1 | no record (1) | 0.13% / 0.16% | not sourced |  |
| MANDELA_BAY_COMMUNITY_MOVEMENT | 2021 | 1 | no record (1) | 0.15% / 0.14% | not sourced |  |
| COMPATRIOTS_OF_SOUTH_AFRICA | 2021 | 2 | no record (2) | 0.10% / 0.14% | not sourced |  |
| INDEPENDENT_CIVIC_MOVEMENT | 2021 | 1 | no record (1) | 0.06% / 0.14% | not sourced |  |
| CREDIBLE_ALTERNATIVE_1ST_MOVEMENT | 2021 | 1 | no record (1) | 0.14% / 0.10% | not sourced |  |
| CHANGE | 2021 | 2 | no record (2) | 0.05% / 0.14% | not sourced |  |
| THE_NATIONALS_OF_SOUTH_AFRICA | 2021 | 1 | no record (1) | 0.08% / 0.14% | not sourced |  |
| AFRICAN_PEOPLE_S_MOVEMENT | 2021 | 3 | no record (3) | 0.06% / 0.13% | not sourced |  |
| ONE_MOVEMENT_FOR_CAPE_TOWN | 2021 | 1 | no record (1) | 0.13% / 0.06% | not sourced |  |
| RCT | 2021 | 1 | no record (1) | 0.13% / 0.10% | not sourced |  |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | 2021 | 3 | returning (2); stood in another metro (1) | 0.10% / 0.13% | not sourced |  |
| PARTY_OF_ACTION | 2021 | 2 | no record (2) | 0.13% / 0.10% | not sourced |  |
| AFRICAN_FREEDOM_REVOLUTION | 2021 | 4 | no record (4) | 0.11% / 0.11% | not sourced |  |
| AFRICAN_SECURITY_CONGRESS | 2021 | 2 | no record (2) | 0.09% / 0.11% | not sourced |  |
| BOLSHEVIKS_PARTY_OF_SOUTH_AFRICA | 2021 | 2 | stood in another metro (2) | 0.01% / 0.11% | not sourced |  |
| NATIONAL_PEOPLE_S_FRONT | 2021 | 2 | national record only (2) | 0.11% / 0.06% | not sourced |  |
| ABLE_LEADERSHIP | 2021 | 1 | no record (1) | 0.05% / 0.10% | not sourced |  |
| LAND_PARTY | 2021 | 2 | national record only (1); no record (1) | 0.04% / 0.10% | not sourced |  |
| FEDERAL_PARTY_SA | 2021 | 2 | no record (2) | 0.05% / 0.10% | not sourced |  |
| DEMOCRATIC_PEOPLE_S_CONGRESS | 2021 | 1 | no record (1) | 0.04% / 0.10% | not sourced |  |
| ACTIVISTS_MOVEMENT_OF_SOUTH_AFRICA | 2021 | 3 | no record (3) | 0.08% / 0.10% | not sourced |  |
| ADVANCED_DYNAMIC_ALLIANCE | 2021 | 1 | no record (1) | 0.06% / 0.09% | not sourced |  |
| DEMOCRATIC_UNION_PLUS | 2021 | 1 | no record (1) | 0.05% / 0.09% | not sourced |  |
| IQELA_LENTSANGO_DAGGA_PARTY | 2021 | 1 | no record (1) | 0.09% / 0.06% | not sourced |  |
| DEMOCRATIC_LABOUR_PARTY | 2021 | 1 | no record (1) | 0.09% / 0.08% | not sourced |  |
| AFRICAN_PROGRESSIVE_MOVEMENT | 2021 | 1 | national record only (1) | 0.09% / 0.03% | not sourced |  |
| AGENCY_FOR_NEW_AGENDA | 2021 | 2 | stood in another metro (2) | 0.03% / 0.08% | not sourced |  |
| CONCERN | 2021 | 1 | no record (1) | 0.08% / 0.08% | not sourced |  |
| AFRICAN_ISLAMIC_MOVEMENT | 2021 | 1 | no record (1) | 0.06% / 0.08% | not sourced |  |
| AFRICAN_BASIC_REPUBLICANS | 2021 | 1 | no record (1) | 0.03% / 0.08% | not sourced |  |
| OUR_NATION | 2021 | 1 | no record (1) | 0.03% / 0.08% | not sourced |  |
| UNITED_SOUTH_AFRICA | 2021 | 1 | no record (1) | 0.06% / 0.08% | not sourced |  |
| DEMOCRATIC_PEOPLE_S_ALTERNATIVE | 2021 | 1 | no record (1) | 0.08% / 0.08% | not sourced |  |
| ACTIVE_MOVEMENT_FOR_CHANGE | 2021 | 1 | no record (1) | 0.00% / 0.08% | not sourced |  |
| DEMOCRATIC_ARTISTS_PARTY | 2021 | 2 | no record (2) | 0.06% / 0.08% | not sourced |  |
| DISABILITY_AND_OLDER_PERSON_POLITICAL_PARTY | 2021 | 1 | no record (1) | 0.00% / 0.08% | not sourced |  |
| POELANO_REVELATION_PARTY | 2021 | 1 | no record (1) | 0.02% / 0.08% | not sourced |  |
| UNITED_CULTURAL_MOVEMENT | 2021 | 3 | no record (3) | 0.04% / 0.08% | not sourced |  |
| ECONOMIC_EMANCIPATION_FORUM | 2021 | 3 | national record only (2); no record (1) | 0.06% / 0.08% | not sourced |  |
| UNITED_PROGRESSIVE_PARTY_SOUTH_AFRICA | 2021 | 1 | no record (1) | 0.06% / 0.08% | not sourced |  |
| THE_PEOPLE_S_VOICE | 2021 | 1 | no record (1) | 0.05% / 0.08% | not sourced |  |
| ROYAL_LOYAL_PROGRESS | 2021 | 1 | no record (1) | 0.02% / 0.08% | not sourced |  |
| SHOSHOLOZA_PROGRESSIVE_PARTY | 2021 | 1 | no record (1) | 0.02% / 0.08% | not sourced |  |
| AFRICAN_FEDERAL_CONVENTION | 2021 | 1 | no record (1) | 0.04% / 0.08% | not sourced |  |
| AFRICAN_AMBASSADORS_OF_SOUTH_AFRICA | 2021 | 1 | no record (1) | 0.08% / 0.07% | not sourced |  |
| DEMOCRATIC_EQUALITY_EMPOWERMENT_PARTY | 2021 | 1 | no record (1) | 0.00% / 0.07% | not sourced |  |
| EASTERN_CAPE_MOVEMENT | 2021 | 1 | no record (1) | 0.01% / 0.07% | not sourced |  |
| KHOI_SAN_KINGDOM_OF_RSA | 2021 | 1 | no record (1) | 0.00% / 0.07% | not sourced |  |
| CHRISTIANS_OF_SOUTH_AFRICA | 2021 | 1 | no record (1) | 0.00% / 0.06% | not sourced |  |
| DEMOCRATIC_PEOPLE_S_MOVEMENT | 2021 | 1 | no record (1) | 0.06% / 0.06% | not sourced |  |
| ABAHLALY_BAAHI | 2021 | 1 | no record (1) | 0.05% / 0.06% | not sourced |  |
| COMMUNITY_SOLIDARITY_ASSOCIATION | 2021 | 1 | no record (1) | 0.03% / 0.06% | not sourced |  |
| DISRUPT_PARTY | 2021 | 1 | no record (1) | 0.02% / 0.06% | not sourced |  |
| US_THE_PEOPLE | 2021 | 1 | no record (1) | 0.06% / 0.06% | not sourced |  |
| AMALGAMATED_RAINBOW_MOVEMENT | 2021 | 1 | no record (1) | 0.03% / 0.06% | not sourced |  |
| KHOISAN_KINGDOM_AND_ALL_PEOPLE | 2021 | 1 | stood in another metro (1) | 0.00% / 0.06% | not sourced |  |
| CIVIC_MOVEMENT_OF_SOUTH_AFRICA | 2021 | 1 | no record (1) | 0.02% / 0.06% | not sourced |  |
| BLACK_AND_WHITE_PARTY | 2021 | 1 | no record (1) | 0.01% / 0.05% | not sourced |  |
| SAKHISIZWE_CONVENTION | 2021 | 1 | no record (1) | 0.00% / 0.05% | not sourced |  |
| FREE_DEMOCRATS | 2021 | 1 | national record only (1) | 0.01% / 0.03% | not sourced |  |
