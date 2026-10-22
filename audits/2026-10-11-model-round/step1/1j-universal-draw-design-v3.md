# 1j v3. One log-scale draw for every party: design, third version

Answers the re-check `step2/2-recheck-1j-v2.md` (8e4831b) and the
coordinator's instructions of 2026-10-12. v1 and v2 are kept unedited. Where
v2 still holds it is cited by section; everything stated here replaces v2.
Read-only: nothing in `src/`, `tests/` or `data/` written; no model run, no
`compare_history`, no emit; no sub-delegation.

**Sources and labels.** As v2. The new scripts are in the session scratchpad,
`uni3/` (`v3.py`, `b1`-`b5.py`), building on `uni2/`; none is committed.
*Measured* = computed by those scripts. *Argued* = reasoning or code reading.
*Citywide simulation* = v2's reimplementation of the draw: normal own term,
ρ(s), pooled increments, κ from an independent 4,000-draw calibration sample,
arm E's pool-turnout draws; no IPF, water-fill or ward path. Every width below
is after v2 §2.3's location fixed point.

---

## Summary for the owner

The draw is as v2 described it, with one decision left to the owner: **how wide
the middle of the ballot is** (parties at 5-20%, which in 2026 means ActionSA,
the EFF, MK and the PA). The record cannot settle it. The two honest choices:

- **A, bridge.** Read the middle off a straight line between the 1-5% parties
  and the large parties. It fits the twelve middle-sized results the record
  holds too narrowly: their squared misses average twice what the width
  allows. The model's own check on that kind of line also fires.
- **B, middle's own record.** Use the twelve middle-sized results directly. It
  fits them, but they come from five party-elections.

On the 2016 and 2021 backtests both improve the large parties' scores. Both
fail the middle-party rule for the same reason, the 2016 EFF, and B fails it by
more. For Johannesburg 2026:

| option | ActionSA and EFF spread | large parties' spread |
|---|---|---|
| A | a little over half of today's | |
| B | close to today's | about half of today's |

In both, an established party that had under 1% last time exceeds 5% in about
23-24 draws of 5,000, against 403 today.

The judgement rule is simplified. A party's strength is stated with the two
keys the judgements file already has: `support`, a share of the vote, and
`overperform`, a multiplier. One new key, `sigma_j`, states how much less
certain the judgement is than the model's own centres usually are. Zero means
as good as the model's own. Editing a judgement does not force the pool specs
to be rebuilt. Backtests ignore judgements and record that they did.

---

## 0. The re-check's items

| item | verdict | change |
|---|---|---|
| A. 5-20% bridge: the large anchor sat at 20% | **accepted, with a different fix from the re-check's first suggestion** | Every anchor now sits at the weighted geometric centre of its own rows. The large rows split in two by the record: 0.074 at 25.6% (rows 20-30%) and 0.043 at 45.4% (rows ≥ 30%). Placing one large anchor at its rows' centre (38.8%) is **rejected**: the large rows' own residuals then score a mean `u²` of 0.20 at 20-30%, a width 2.2 times too wide for the ANC and DA rows (§2.2). The middle is presented as an owner choice, A or B, with both fits and both backtest scores (§2.3, §8) |
| B1. two ways to state a centre | **accepted** | v2's `centre_share` / `centre_ratio` are dropped. The existing `support` and `overperform` keys of `[party.X]`, with their existing combination rule, are the only way (§11) |
| B2. σ_J double-counts centre error | **accepted** | σ_J is uncertainty beyond the model's own centre error for an established party of the judged size; 0 means as good as the model's (§11.1) |
| B3. arrival factor kept for a judged seed | **accepted** | dropped for a judged party, matching the script (`uni2/v2.py` `components`) |
| B4. file and key mechanics | **accepted** | `support`, `overperform` and `sigma_j` are read at run time and excluded from `_judgements_sha`. A backtest ignores them and records that it did, rather than refusing (§11.2) |
| C1. the stop rule cannot fire | **accepted** | each band is tested against the interpolation built without it. On the current record it fires for option A at 1-5% and is quiet for option B (§2.4) |
| C2. explanation of 1.01 | **accepted** | §0.1 replaces v2's party-clustering explanation |
| C3. large parties under-move in 2021 | noted | the two large anchors widen them slightly: drawn log-sd 0.091 (A) and 0.109 (B) against realised RMS 0.114 (§8) |
| C4. regenerate §8 per option | **done** | §8 |
| v1's 0.05 debutant increment | **accepted** | corrected in §0.2 |
| re-check row 6, the 0.05 claim | **accepted** | as above |
| N4 (zeros) | the re-check accepts v2's rejection | unchanged |

### 0.1 The 1-5% width: 1.01 against 0.83

The re-check settled it (re-check §3). The 1.01 counts a party-cycle's rows
across **all** bands before applying `1/count` inside the band. v2, the
reviewer and this design count rows **within** the band. That count defines
the weight unit on the population being estimated: each party-cycle present
in the band carries equal weight. The all-band count is printed as a
sensitivity in §2.5: 1-5% gives 1.010 raw and 1.041 relative to the block,
against 0.802 and 0.834. v2's party-clustering explanation is withdrawn.

### 0.2 Correction to v2 about v1's debutant increment

v2 said v1's increment of 0.05 for national debutants under 1% "was also an
artefact of the iteration". That is wrong. Under v1's curve widths the closed
form gives 0.052 (roots 0.003 and 2.629; review `r7.py`), so v1's figure was
right for v1's widths. The 0.39 of v2 comes from v2's narrower band widths
below 1%. Only the 2016 value, from COPE's eight 2011 results alone, was a
solver failure: the iteration oscillated, and the exact smaller root is 1.21
(1.09 under v1's curve).

---

## 1. The draw

As v2 §1 (normal own term, ρ(s) by size group, complementary own term,
`pool_spec` centres as the base vector, the individual path in the same
vector, calibration pass, noise-aware falsifier), with the width function of
§2 below.

---

## 2. The width function

### 2.1 Anchors at the centre of their own rows

The estimator is unchanged from v2 §2.1: the offset-aware quadratic root, with
party-cycle weights counted within the band, `MIN_EFF` = 8. Each anchor now
sits at the weighted geometric centre of the rows that produced it:

| anchor | rows | 2026 record: centre, width (cases / party-elections) |
|---|---|---|
| < 0.1% | established, centre < 0.1% | 0.034%, 0.998, no root (41 / 34) |
| 0.1-0.3% | | 0.165%, 0.901 (61 / 37) |
| 0.3-1% | | 0.543%, 0.822 (88 / 35) |
| 1-5% | | 1.94%, 0.840 (35 / 18) |
| 5-20%, option B only | | 8.92%, 0.623 (12 / 5) |
| large, 20-30% | within-block residual | 25.6%, 0.074 (12) |
| large, ≥ 30% | within-block residual | 45.4%, 0.043 (32) |

The width is linear in log size between anchors and constant beyond the ends.
The large rows split at 30% because their residual changes with size: RMS
0.074 at 20-30%, 0.048 at 30-45% and 0.039 at 45% and over (re-check A,
reproduced). Two anchors fit the large rows; a third, at 45%, would add a
level the record barely separates from the second (argued).

### 2.2 Testing each construction against the record it should fit

Each construction is tested on two sets of results it should fit. A width that
fits gives a weighted mean `u²` near 1, where
`u = (r − Δ + σ²/2)/σ`, or the within-block residual over σ for large rows.

| construction (2026 record) | 5-20% established (12 / 5) | large rows 20-30% (12) | large rows ≥ 30% (32) | σ at 26% / 23.8% / 11.7% / 11.0% / 9.1% / 5.8% |
|---|---|---|---|---|
| v2: bridge to one anchor at 20% | 3.62 | 1.91 | 0.66 | 0.053 / 0.053 / 0.235 / 0.256 / 0.319 / 0.469 |
| one large anchor at its rows' centre (38.8%) | 1.54 | **0.20** | 0.49 | 0.158 / 0.182 / 0.369 / 0.385 / 0.434 / 0.551 |
| **A: bridge to two large anchors** | **2.00** | 0.76 | 0.77 | 0.073 / 0.096 / 0.307 / 0.325 / 0.381 / 0.513 |
| **B: two large anchors plus the 5-20% root** | **0.88** | 0.68 | 0.77 | 0.073 / 0.113 / 0.488 / 0.522 / 0.620 / 0.689 |

The same test for the earlier records, 5-20% / 20-30% / ≥ 30%:

| construction | 2021 record | 2016 record |
|---|---|---|
| A | 2.60 / 1.04 / 0.77 | 3.85 / 1.08 / 0.78 |
| B | 0.98 / 1.03 / 0.77 | 0.98 / 1.08 / 0.78 |
| one anchor at 38.8% | 1.96 / 0.18 / 0.46 | 2.82 / 0.31 / 0.46 |

The single anchor at 38.8% passes the middle better than A but makes the ANC
and DA rows 2.2 times too wide in sd (u² 0.18-0.31). It is rejected.

### 2.3 The middle: an owner choice

| | A: bridge | B: middle's own record |
|---|---|---|
| what sets the 5-20% width | the 1-5% band (18 party-elections) and the large rows (44 cases), joined by a straight line in log size | the 5-20% band's own root (12 cases, 5 party-elections: IFP, Minority Front and VF+ in 2011; the DA in Buffalo City and Mangaung 2011; the EFF in 2021) |
| fit to the 12 in-band results | mean `u²` 2.00: the width is about 1.4 times too narrow in sd | 0.88 |
| the stop rule (§2.4) | fires at 1-5% | quiet everywhere |
| backtest middle CRPS, 2016 + 2021 | +0.143 [−0.119, +0.429] | +0.364 [+0.120, +0.667] |
| backtest middle CRPS, established only (2021, 7) | −0.361 [−0.543, −0.166] | −0.147 [−0.210, −0.081] |
| JHB 2026 log-sd ASA / EFF / MK / PA | 0.28 / 0.31 / 0.56 / 0.50 | 0.44 / 0.48 / 0.70 / 0.67 |

The backtest evidence that favours a narrow middle is the EFF in 2021: seven
metros, small residuals, one party-election. The in-band evidence that favours
a wide middle is four 2011 results: three collapses and two single-block DA
results. Both sides rest on at most five party-elections. B is the
construction that passes every record test this design applies. A scores
better on the backtest middle because 2021 rewarded narrowness.

### 2.4 The stop rule, leave one band out

For each band, the writer builds the interpolation without that band's anchor
and compares the band's root with that interpolation at the band's centre.
The test uses a cluster bootstrap of the root over party-cycles (2,000
resamples, 90%). An interpolated value outside the interval stops the writer.
The 5-20% band is tested the same way under both options.

| band | 2026, option A: root / interpolation without it / root interval | A | 2026, option B | B |
|---|---|---|---|---|
| 1-5% | 0.840 / 0.575 / 0.617-0.968 | **fires** | 0.840 / 0.735 / 0.616-0.969 | quiet |
| 0.3-1% | 0.822 / 0.871 / 0.714-0.901 | quiet | 0.822 / 0.872 / 0.714-0.901 | quiet |
| 0.1-0.3% | 0.901 / 0.897 / 0.688-1.109 | quiet | 0.901 / 0.897 / 0.688-1.110 | quiet |
| < 0.1% | 0.998 / 0.901 / 0.780-1.141 | quiet | same | quiet |
| 5-20% | 0.623 / 0.386 / 0.204-0.750 | quiet | 0.630 / 0.387 / 0.209-0.758 | quiet |

For the 2021 record the result is the same: A fires at 1-5% (0.822 against
0.591, interval 0.606-0.950); B is quiet.

**Can it see, and does it go quiet:**

- It fires on a real misfit: under A, a straight line from 0.54% to 25.6%
  passes through the 1-5% band far below its measured width.
- It goes quiet when that line is given the middle anchor (B).
- The 5-20% test is quiet under both: an interval of 0.20-0.75 from five
  party-elections cannot tell them apart.

If the owner chooses A, the stop rule as written stops the writer. Choosing A
therefore also means declaring the 1-5% leave-one-out check exempt, with this
table as the reason.

### 2.5 Sensitivities the writer prints

- **Weight count:** within-band party-cycle count (used) against all-band count
  (§0.1: 1-5% gives 0.834 against 1.041).
- **Weights:** observation weights.
- **Block:** the two largest parties as the block.
- **Large rows:** one anchor against two.
- **Middle:** both options, A and B.

### 2.6 Other widths, 2026 record

| quantity | A | B | v2 |
|---|---|---|---|
| pooled debutant increment δ_deb | 0.477 | 0.457 | 0.472 |
| seed increment δ_seed | 0.848 | 0.847 | 0.839 |
| arrival factor | 0.726 | 0.726 | 0.726 |
| shared share, < 1% / 1-20% | 0.46 / 0.00 | 0.46 / 0.00 | 0.46 / 0.00 |

Forward debutant increments for 2016 and 2021: A 0.776, 0.833; B 0.715, 0.810.

---

## 8. Predictions for each option

As v2 §8.1, the must-not-worsen rules are:

- **large parties:** the 90% upper bound of the CRPS difference is at most
  +0.05, and at least 28 of 32 results fall inside the 90% band;
- **middle parties:** the same CRPS rule, and at least 12 of 14 inside the
  band.

Intervals are a city-year cluster bootstrap over party-city-years.

### 8.1 Backtests, 2016 and 2021

| measure | A: bridge | B: middle's own record | arm E |
|---|---|---|---|
| large, 2016 (16): CRPS / difference [90%] | 1.032 / −0.386 [−0.445, −0.329] | 1.085 / −0.333 [−0.402, −0.265] | 1.418 |
| large, 2021 (16) | 2.224 / +0.045 [−0.218, +0.311] | 2.197 / +0.018 [−0.212, +0.245] | 2.180 |
| **large, both (32)** | **−0.171 [−0.316, −0.008]; 30 / 32 inside 90%: passes** | **−0.158 [−0.286, −0.019]; 31 / 32: passes** | 32 / 32 |
| large drawn log-sd median, 2016 / 2021 (realised RMS 0.040 / 0.114) | 0.093 / 0.091 | 0.105 / 0.109 | 0.144 / 0.182 |
| middle, debutants 2016 (EFF, 5) | +0.855 [+0.672, +0.989] | +1.107 [+0.892, +1.255] | — |
| middle, established 2021 (7) | −0.361 [−0.543, −0.166] | −0.147 [−0.210, −0.081] | — |
| **middle, both (14)** | **+0.143 [−0.119, +0.429]; 14 / 14: fails the CRPS rule** | **+0.364 [+0.120, +0.667]; 14 / 14: fails the CRPS rule** | 13 / 14 |
| wrong-party seats on mean seats, 2016 / 2021 (list-only proxy) | 72.6 / 153.1 | 72.7 / 153.2 | 71.8 / 154.9 |
| expected seats, centre < 1%, 2016 / 2021 (realised 63 / 127) | 72.3 / 88.5 | 72.4 / 88.4 | 75.6 / 94.5 |

Both options fail the middle CRPS rule. The cause is the same: the 2016
national-debutant increment (0.72-0.78, mostly COPE's 2011 collapse) applied
to the EFF, which landed above its centre. Monte Carlo sd of the large and
middle differences: 0.017-0.043 per row.

### 8.2 Johannesburg 2026 (citywide simulation, 5,000 draws; counts are means of 4 seeds)

| party | centre | A: log-sd, p5-p95 | B: log-sd, p5-p95 | arm E: log-sd, p5-p95 |
|---|---|---|---|---|
| DA | 26.00% | 0.13, 20.7-31.4% | 0.16, 19.5-32.6% | 0.21, 17.4-34.6% |
| ANC | 23.76% | 0.13, 18.8-28.9% | 0.17, 17.6-30.1% | 0.34, 12.1-37.1% |
| ASA | 11.67% | 0.28, 7.0-17.8% | 0.44, 5.0-21.6% | 0.50, 4.2-21.8% |
| EFF | 10.96% | 0.31, 6.3-17.4% | 0.48, 4.3-21.3% | 0.57, 3.4-21.3% |
| MK (debutant) | 9.09% | 0.56, 3.1-19.3% | 0.70, 2.2-22.4% | 0.60, 2.6-18.1% |
| PA | 5.82% | 0.50, 2.3-11.9% | 0.67, 1.6-14.2% | 0.30, 3.3-8.4% |
| RISE (debutant) | 1.82% | 0.94, 0.24-5.2% | 0.93, 0.24-5.1% | 1.40, 0.08-6.2% |
| IFP | 1.50% | 0.79, 0.28-3.9% | 0.80, 0.28-3.9% | 2.42, 0.00-6.0% |
| ATM | 0.43% | 0.80, 0.08-1.18% | 0.80, 0.08-1.18% | 3.65, 0.00-2.58% |

| quantity | A | B | arm E | record |
|---|---|---|---|---|
| draws with an established party, previous < 1%, above 5% | 22.8 (sd 2.2) | 24.0 (3.4) | 403 | — |
| the same above 3.48% | 94 | 97 | 807 | — |
| rate above 2% per party-draw | 0.0057 | 0.0058 | 0.0219 | 0.010 |
| party-draws keeping < 14.6% of previous | 0.072 | 0.074 | 0.740 | 0.005 exchangeable |
| median retained share of previous | 0.63 | 0.63 | 0.003 | 0.78 |
| log-sd of their combined share | 0.58 | 0.59 | 0.75 | 0.59 |
| draws with any party of centre < 1% above 5% | 58.5 | 59.5 | 853 | — |
| draws whose largest new party exceeds 18.12% | 325 | 471 | 255 | — |
| mean combined share, centre < 1% | 8.13% | 8.12% | 8.65% | — |

What will still fail is v2 §8.3, with the middle row now per option. Below 5%
the two options are identical.

### 8.3 Arms to pre-register

The owner's choice of A or B is the main draw, and the other becomes a paired
arm. The t own-term arm of v2 §1.4 is unchanged.

---

## 11. Entering a judgement about strength

### 11.1 The rule

A judgement uses the existing keys of `[party.<CODE>]` in the target's
`judgements/` file, plus one new key:

- **`support`** (existing): a list share. When present, it replaces the
  model's centre.
- **`overperform`** (existing): a multiplier. It multiplies `support` if given,
  otherwise the model's centre.
- **`sigma_j`** (new, required when either of the above is present): a log sd.
- **`register`** (new): the JUDGEMENT-CALLS §J row that declares the entry.

The judged centre is `c_J = (support if present else the model's centre) ×
overperform`. That is the combination `pools.py:4925-4937` already applies to
seeded arrivals, now applied to any party at run time. v2's `centre_share` and
`centre_ratio` are not introduced.

Then, the same for every party:

1. **`c_J` replaces the model's centre** in the level vector before
   `pool_spec`. The IPF places it in the party's pools; every other party is
   rescaled by the normalisation; the calibration conserves `c_J`. This changes
   other parties' centres, which is declared and visible in `30_centres`.
2. **Width:** `σ_total² = σ(c_J)² + σ_J²`.
   - `σ(c_J)` is the record's width for an established party of the judged
     size. It is measured about the model's own centres, so it already holds
     the model's usual centre error.
   - **`σ_J` is the judgement's uncertainty beyond that.** `σ_J = 0` states a
     judgement as reliable as the model's own centre for an established party
     of that size.
   - The class increments δ_deb and δ_seed play this role for the model's own
     rules, so a judged party's δ is replaced by `σ_J`, never added to it.
   - The JUDGEMENT-CALLS template for a §J row states this definition.
3. **Shared structure:** loading `ρ(c_J)`; the own term takes the rest less
   composition. **A judged seeded arrival does not load on the arrival
   factor.** That factor is the common part of the seed sizing rule's error,
   and the judgement has replaced the rule.

### 11.2 Mechanics

- **Read at run time.** `make_drawer` reads `support`, `overperform`,
  `sigma_j` and `register` when it builds the level vector. `pools.py` stops
  reading `support` and `overperform` at emit: a declared-weights arrival's
  pool vector is built from the record base, as for any other arrival.
  `_judgements_sha` excludes the four keys, so adding or editing a judgement
  leaves every spec's `artefact_key` unchanged and forces no re-emit.
  - The `pools.py` edit is itself a code change, so it goes in the batched
    re-emit queue with the `dirichlet_alpha` deletion.
  - It is number-neutral today: none of the 26 judgements files declares
    either key (re-check B1).
  - `PARTY_KEYS` gains `sigma_j` and `register`.
- **The judged party in the arrival group budget.** Today a judged arrival is
  held out of the seed group's budget at emit. After the change the emit no
  longer knows about judgements, so a judged arrival is sized like any other at
  emit, and its judged centre takes effect at run time through the
  normalisation. Declared; number-neutral today.
- **Guards.**
  - `make_drawer` refuses `support` or `overperform` without `sigma_j` and
    `register`.
  - A suite test checks both directions: every §J row has an entry, and every
    entry has a row.
  - No code path names a party.
- **Backtests ignore judgements, and say so.** On a target with a result file,
  `make_drawer` applies none of the four keys and records them in
  `35_widths.judgements_ignored`, with each entry's register row and the
  reason ("backtest: a judgement cannot be blind after the election"). It does
  not refuse, so when 2026 becomes a backtest the same file still runs.
- **Forecasts report both.** A forecast with judgements is also run without
  them, paired, and both results are recorded.
- **Dates.** Each §J row carries the date the judgement was made. The run
  records it beside the run date in `35_widths`, so a judgement revised after
  a run is visible. Nothing can enforce that a judgement was not revised after
  seeing scores; the dates make it auditable.

### 11.3 Three entries, worked (hypothetical parties; 2026 record, option B)

The quantiles are of a mean-preserving lognormal on the total width: the
party's own draw, before normalisation and composition.

| case | entry | σ(c) at the centre used | increment | total | p5 / median / p95 |
|---|---|---|---|---|---|
| seeded arrival, no judgement (model centre 0.10%) | — | 0.93 | δ_seed 0.85 | 1.26 | 0.01 / 0.05 / 0.36% |
| seeded arrival, judged | `support = 0.015`, `sigma_j = 0.6`, no arrival factor | 0.84 | replaced by σ_J 0.6 | 1.03 | 0.16 / 0.88 / 4.80% |
| national debutant, no judgement (centre 9.1%) | — | 0.62 | δ_deb 0.46 | 0.77 | 1.9 / 6.8 / 24.0% |
| national debutant, judged as reliable as the model | `overperform = 1.0`, `sigma_j = 0` | 0.62 | replaced by 0 | 0.62 | 2.7 / 7.5 / 20.8% |
| established, no judgement (centre 6%) | — | 0.68 | none | 0.68 | 1.5 / 4.8 / 14.6% |
| established, judged to be collapsing | `overperform = 0.33` (centre 1.98%), `sigma_j = 0.3` | 0.84 | none to replace; σ_J 0.3 added | 0.89 | 0.31 / 1.33 / 5.76% |

These are computed from the option-B widths of §2.2 (`uni3/`) and are
illustrations, not proposals. Entries are the owner's to make.

---

## 7. Judgement-call rows that change from v2

| call | value | evidence | check |
|---|---|---|---|
| anchor placement | weighted geometric centre of each anchor's rows | re-check A | — |
| large anchors | two: rows 20-30% and ≥ 30% | §2.1-2.2: within-block residual 0.074 / 0.048 / 0.039 by size; one anchor at 38.8% scores u² 0.20 on the 20-30% rows | writer prints both |
| **middle width** | **owner's choice: A (bridge) or B (5-20% root)** | §2.3; both rest on at most 5 party-elections | the other option runs as a paired arm |
| stop rule | leave one band out; cluster bootstrap 90% | §2.4 | fires for A at 1-5% |
| strength judgements | `support` / `overperform` / `sigma_j` / `register`, run time | §11 | two-way register guard; `judgements_ignored` on backtests |

All other rows are as v2 §7.

## 9. Writer's order: changes from v2

- **Step 2:** anchors at row centres; two large anchors; both middle options
  behind a scenario switch keyed into the width record; the leave-one-out stop
  rule with its constructed tests:
  - fires when a constructed band is moved outside the interpolation;
  - quiet when reverted.
- **Step 3:** run-time reading of the judgement keys; `judgements_ignored`.
- **Batched `pools.py` change:** stop reading `support` and `overperform`;
  exclude the four keys from `_judgements_sha`; `PARTY_KEYS`.
- **Records:** JUDGEMENT-CALLS §J template with the σ_J definition and a date
  column.

## What I re-derived and what I did not

**Re-derived (`uni3/`):**

- anchors at row centres, all three records;
- the in-band and large-row tests for four constructions;
- the leave-one-out stop rule with bootstraps, for 2021 and 2026;
- increments under each option;
- the Johannesburg 2026 simulation for A and B, four seeds;
- backtest CRPS with city-year bootstrap and Monte Carlo error, coverage and
  the seat proxy for A and B;
- the judgement arithmetic.

**Taken from the re-check:** the 1.01 explanation (§0.1); the 0.052 closed form
under v1's curve.

**Not done:** no model run (the IPF, the water-fill, the ward path and the real
calibration pass are argued); the location fixed point uses the citywide
simulation; seats are a list-only proxy.
