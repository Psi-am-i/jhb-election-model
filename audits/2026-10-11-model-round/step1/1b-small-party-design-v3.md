# 1b v3. Small parties, the class line, and new entrants: design

Third revision. v1 (`1b-small-party-design.md`) and v2
(`1b-small-party-design-v2.md`) are kept. v2's answers to the first review's 15
findings stand; this revision applies the re-check
`step2/2-recheck-1b-v2.md` (N1-N7; verdict "sound with listed fixes").
Read-only: nothing in `src/` or `data/` written; no model run, no
`compare_history`, no emit; no sub-delegation. Sources as v2 (arm E arrays,
traces and pool specs, artefact keys matched; raw metro LGE 2000-2021 and NPE
2004-2024 through `levels._citywide_and_roster`; `theta_residual.residuals()`).
Scripts in the session scratchpad, not committed.

**Every centre in this revision is the `pool_spec` centre the draw conserves**
(Σ_g pool votes_g · props_gi / Σ_g pool votes_g, unshocked, from the spec each
run read and its `30_centres.after_shrink`), not arm E's mean share.

---

## For the owner

**Where the line is.** A party is drawn on its own (outside the pool split) and
counted in the small-party class when it stood at the previous election in this
city (the local one; for a party new to local elections, the national one) and
both that result and its current centre are below `UNIT_LINE_QUOTAS` seats'
quotas of the target council. The proposed value is 3, which is 1.11% in
Johannesburg and 3% in Buffalo City.

**The record behind it.** In the eight metros, 2006-2021, 273 parties on the
ballot were below that line at their previous election: 203 with a previous local
result and 70 with only a national one. None reached 5% at the next local
election; the largest was 4.41% (VF+ Mangaung 2021, from 1.85%). With 0 of 273
the rate is below 1.1% at 95% confidence. The record cannot tell three quotas
from four (0 of 212 at four), so the value is the owner's to set; it is a named
parameter.

**What it fixes.** At Johannesburg 2026, draws in which one of the 20
established parties below the line exceeds 5% fall from 473 to about 31 of 5,000.
Their draws take the record's shape: a typical result near the centre, not
near zero.

**What it does not fix: parties just above the line keep the spike.** Every
non-seeded party above the line is still drawn by the within-pool split that
causes the problem. At Johannesburg 2026:

| party | why above the line | arm E mean | median | p99 | max | draws above 5% (of 5,000) |
|---|---|---|---|---|---|---|
| VF+ | previous LGE 1.33% (line 1.11%) | 0.90% | 0.47% | 5.38% | 13.26% | 63 |
| IFP | previous LGE 2.36% | 1.49% | 0.60% | 9.71% | 21.47% | 378 |
| RISE | national debutant, centre 1.82% | 1.83% | 1.08% | 9.95% | 18.36% | 400 |
| BOSA | national debutant; national share 1.02% is below the line, its centre 1.16% is not | 1.19% | 0.53% | 8.35% | 23.49% | 210 |

Together these four are above 5% in 995 of 5,000 draws. For comparison, the
record for established parties at 3-10 quotas has a 95th-percentile
next/previous ratio of about 2.0-2.2 and sd log 0.85-0.88. The IFP's p99 is 6.5x
its mean.

Problem 1 is therefore solved below the line and untouched above it. The next
item is a shape fix for small cells of parties above the line that does not read
the fitted pool concentration (§7).

**A level defect, filed separately.** `compress_levels` lifts every small
party's centre by 1.29-1.40x in every backtest cycle and 1.20-1.34x at 2026
(`1b-level-lift-defect.md`).

---

## 0. Answers to the re-check (N1-N7)

| # | finding | verdict | what changed |
|---|---|---|---|
| N1 | 2011 coverage collapse is the fallback width, not mainly the level | **accepted** | 2011's width is declared untestable and in the wrong frame (θ residual about `theta_prior`'s centre, which lacks the `compress_levels` lift and the local-route collapse). 2011 is excluded from the coverage falsifier. 0.302 is no longer attributed to the level layer. The reviewer's check stands: at a 2011 width of 1.0, 2011 coverage is 0.921. |
| N2 | widths and predictions about arm E means, not the `pool_spec` centre | **accepted** | Widths, coverage and every Johannesburg prediction re-derived about the `pool_spec` centre (§3.3, §6). Unit parties' mean shares fall against arm E by +0.034 / +0.086 / +0.111 / +0.111 in log (2011 / 2016 / 2021 / 2026). At JHB 2026 0.41 points of list vote move from the 25 unit parties to the rest. The list-MAE prediction is now −0.027 points, not 0, and the falsifier is centred on it. |
| N3 | the spike stays on parties just above the line | **accepted** | "For the owner" above, with tails. |
| N4 | "0 of 438" mixes denominators | **accepted** | 273 parties on the ballot (203 + 70), 0 to 5%, one-sided 95% bound 1.1%. |
| N5 | non-unit members conserved to first order only | **accepted** | Fixed in the spec: non-unit members are renormalised against the **unshocked** unit sum, which makes their expectation exact (§3.2, §3.4). |
| N6 | widths are about centres partly selected on the same outcomes | **accepted** | Declared beside the width rows (§5): `level_shrink` was chosen on Johannesburg 2016 and confirmed leave-one-out on the 2016/2021 panel, so the 2021 and 2026 forward widths are residuals about centres partly selected on those outcomes. The writer prints cluster intervals; 2016's width rests on one cycle. |
| N7 | knife edge smaller; listing enough | **accepted** | The trace and the pre-registration list every party within ±10% of the line. At JHB 2026 that is BOSA (centre 1.16% against 1.11%, +4.7%; as a unit party its p99 would be about 6.7% against arm E's 8.35%) and VF+ by its previous result (1.33%). The κ inputs and the realised width of a large-cell party are now stated (§3.2). |

---

## 1. Mechanism (unchanged)

The extreme draws of established small parties come from the within-pool
Dirichlet (`src/montecarlo.py:3376`) applied at concentration `a = A·m` far below
1. Those cells lie outside the population `A` was fitted on
(`pools.dirichlet_alpha`, members ≥ 1% of a pool, §F31). `A` itself is the
fallback 12.0 at every 2011 spec, so no decision in this design reads `A`.
`PA|Coloured` is a level-versus-pool-vector problem and is not addressed here.

---

## 2. The line

### 2.1 Record, by candidate line (consecutive metro LGE pairs 2006→2011, 2011→2016, 2016→2021)

Quota = 1/council of the target council. "Stood" = on the ballot at the later
election.

| line | below, all | below, stood | stood and reached 5% | largest later share |
|---|---|---|---|---|
| 1 quota | 304 | 146 | 0 | 2.96% (PA JHB 2021, from 0.17%) |
| 2 quotas | 344 | 183 | 0 | 4.41% (VF+ MAN 2021, from 1.85%) |
| **3 quotas** | **368** | **203** | **0** | **4.41%** |
| 4 quotas | 378 | 212 | 0 | 4.41% |
| 5 quotas | 383 | 217 | 1 | 7.79% (VF+ TSH 2021, from 1.97%) |
| 1% flat | 337 | 175 | 0 | 3.48% (VF+ EKU 2021, from 0.90%) |
| 2% flat | 375 | 210 | 1 | 7.79% |

Parties new to local elections, with a national share below three quotas at the
intervening NPE, that stood: 70; 0 reached 5%; largest 3.58% (AIC Buffalo City
2011). Parties with no record at all: 265; 3 reached 5%, all ActionSA in 2021.

### 2.2 The rule

Three quotas, tested on both the previous result and the centre, with no party
without any record ever in the class. This is `UNIT_LINE_QUOTAS` = 3, a named
parameter.
- **The record property:** 0 of 273 reached 5%.
- **It scales with the council.**
- **The centre test** keeps out parties the model expects past the line. Panel:
  ACDP Cape Town 2021, VF+ Ekurhuleni 2011 and 2021, VF+ Mangaung 2021, the
  Displacees Ratepayers Association in Ekurhuleni 2011. JHB 2026: BOSA.

Membership, using `pool_spec` centres:
- panel: 47 / 68 / 85 established and 16 / 13 / 42 debutants at
  2011 / 2016 / 2021;
- JHB 2026: 20 established (largest ALJAMAAH 0.88%, ACDP 0.73%) and 5 debutants
  (all ≤ 0.24%), unit centre total 4.68%.

---

## 3. Specification

All in `src/montecarlo.py` (`make_drawer`, `draw_pools`) plus one record
writer. No change to `src/pools.py`; no re-emit of pool specs.

### 3.1 Partition, once per run

Party `i` is a **unit party** if all three hold:
- it is not seeded;
- it has a previous result `s_prev` in this city;
- max(`s_prev`, `centre_i`) < `UNIT_LINE_QUOTAS` / council.

Definitions:
- `s_prev` is the previous-LGE list share (`prior_pr_share`, `:4878`) if
  positive. Otherwise it is the preceding-NPE share in this city
  (`baseline_before_seeds`, `:4866`).
- `centre_i` = Σ_g votes_g·props_gi / Σ_g votes_g from the unshocked `pool_spec`
  (`:2607`), with `votes_g` = registered × central turnout.
- **Established** = previous-LGE share > 0; **debutant** otherwise.
- The **class** is all unit parties; its total is reported per draw.

### 3.2 The draw

    c_d   = σ_cyc·z_cyc + σ_btw·z_btw                 established unit parties only
    x_id  = c_d + σ_wit·z_i   (established);  σ_deb·z_i   (debutant)
    share_gid = logistic(logit(m_gi) + κ_gi + x_id)    each pool g with member weight

- `m_gi` is the unshocked `pool_spec` proportion. It is **not** passed through
  the `DIRICHLET_FLOOR` mean floor (`:3374`): that floor exists to keep Dirichlet
  concentrations positive, and unit cells are not in the Dirichlet.
- `κ_gi` is solved once per run so that E[share_gid] = m_gi under x's total sd
  (60-node Gauss-Hermite, bisection). The reviewer measured it as exact to
  machine precision, with κ between −0.44 and 0.
- **Width on the logit scale.** A party with a large cell realises a citywide
  log sd below its nominal width (ALJAMAAH, ~20% of the Indian/Asian pool: 0.755
  against 0.934). Parties with small cells realise 0.925-0.929. This is accepted
  as the price of a pool that cannot overflow.

Non-unit members of pool `g`:

    M_gd   = Σ_unit share_gid
    others = (1 − M_gd) · w_gj · Dirichlet-split
    w_gj   = post-IPF props_gj · (1 − Σ_unit m_gi) / Σ_non-unit post-IPF props_g

The Dirichlet runs over non-unit members with concentrations `A_g · m_gj` and
mean `w_gj / Σ w`. Non-unit members are renormalised against the **unshocked**
unit sum (N5), so their expected share is exact.

Unit parties stay in the IPF with unshocked column targets (`pool_sd_shock` = 0,
as seeds at `:3152`). Their own post-IPF props are discarded.

`split_record` stores the composed full-length vector.

**Guard.** If M_gd ≥ 1 − 1e-6, scale that pool's unit cells to 1 − 1e-6 and
count the draw in `ipf_stats` and `41_guards`. Expected rate at JHB 2026: 1.35e-4
(reviewer, 200,000 draws, all in the Indian/Asian pool). A rate above 5e-3
falsifies the mechanism.

**Seats and wards.** No split back is needed. A unit party's citywide share is
Σ_g (votes_g / cast)·share_gid; it wins a seat in any draw where that share clears
the quota. Wards follow as now (`ward_target = pr_target * ratio`, `:5770`).

### 3.3 Widths: forward, about the `pool_spec` centre

`r = log(realised list share / pool_spec centre)` per unit party per backtest
city-year. Per target `t`, an ANOVA over earlier targets only:
- `σ_cyc` = RMS about zero of per-cycle means. This is the E[k²] reading, so the
  mean bias of the centres (−0.20 across three cycles, largely the
  `compress_levels` lift) is counted as uncertainty.
- `σ_btw` = between-metro component within a cycle.
- `σ_wit` = within-metro member component, n-weighted.

The centres do not depend on any width, because the draw conserves them, so
there is no circularity.

Established unit parties (n counts parties with a positive realised share):

| target | n | cycle mean | between-metro sd | within sd |
|---|---|---|---|---|
| 2011 | 47 | −0.886 | 0.00 | 0.59 |
| 2016 | 67 | −0.156 | 0.16 | 0.62 |
| 2021 | 84 | +0.427 | 0.28 | 0.83 |

| width used for | from | σ_cyc | σ_btw | σ_wit | total |
|---|---|---|---|---|---|
| 2016 | 2011 | 0.89 | 0.00 | 0.59 | 1.06 |
| 2021 | 2011-2016 | 0.64 | 0.11 | 0.61 | 0.89 |
| 2026 | 2011-2021 | 0.57 | 0.19 | 0.71 | 0.94 |

Debutants (n 16 / 13 / 41; means +0.31 / −0.56 / −0.06; RMS 0.94 / 1.59 / 0.60)
get one total width and no common factor, because their cycle means differ in
sign from the established class in two of three cycles. `σ_deb`: 0.94 (2016),
1.27 (2021), 0.94 (2026).

**2011: no earlier backtest, width untestable.** The fallback is the forward θ
residual of target 2006, by population: 0.27 with θ history, 0.48 without. That
residual is measured about `theta_prior`'s centre, which omits the
`compress_levels` lift (about +0.31 in log at 2011) and the local-route parties'
collapse (spine residual −0.92, 12 parties). The 2011 band is therefore too
narrow by construction. 2011 is scored, labelled "width not testable", and
excluded from falsifier 4.

**Estimation, with a caveat (N6).** The widths are the realised dispersion of
the vote about a width-independent centre. They read no predicted width. The
centres come from today's code, whose `level_shrink` was chosen on Johannesburg
2016 and confirmed leave-one-out on the 2016/2021 panel
(`montecarlo.py:2560-2568`). The 2021 and 2026 widths are therefore residuals
about centres partly selected on those outcomes.

Gaussian factors: κ needs a known distribution, and `exp` of a t has no mean.

### 3.4 Conservation

- Unit cells: E[share_gid] = m_gi by κ.
- Non-unit cells: E = (1 − Σ_unit m_gi) · w_gj / Σw = post-IPF props_gj
  rescaled to the non-unit mass, exactly, because M and the Dirichlet are
  independent and the renormalisation uses the unshocked unit sum.
- Every pool sums to one in every draw, except counted guard draws.

**Against arm E this is a change of mean:** arm E did not conserve small
parties' `pool_spec` centres (the mean floor and the end-of-draw renormalisation
lifted them by 3-11% in log). v3 does (§6).

### 3.5 Where the widths live

The widths come from a new writer, `src/unit_width_record.py --emit`, which
writes `data/processed/unit_width_record.json`. Per target year it holds:
- the forward components, with n, per-cycle means and cluster intervals;
- the fallback rows, labelled.

It computes the earlier targets' `pool_spec` centres through the functions
`run_model` uses, with no draws. Its artefact key covers the centres' inputs, so
any level change (for example a `compress_levels` repair) forces a re-estimate.
`make_drawer` refuses a missing or stale record. Couplings:
- run it in a re-emit window;
- name it in CLAUDE.md §5 and in `ENTRY_POINTS` (`tests/test_standalone_modules.py`);
- correct the `theta_residual.py` docstring table in the same commit, to
  0.916 (n 110) / 0.697 (140) / 0.500 (64) / 0.875 (25), and 0.284 (64) at
  ≥ 15%.

### 3.6 Random streams (under `1c-paired-draws-design.md`)

| stage | name | per draw | transform |
|---|---|---|---|
| `unit.cycle` | `""` | z, 1 | `σ_cyc·z` |
| `unit.metro` | `""` | z, 1 | `σ_btw·z` |
| `unit.member` | party code | z, 1 | `σ_wit·z` or `σ_deb·z` |

A unit party reads `unit.member` in place of its `split` streams. Every other
party's primitives stay bit-identical. Implementation follows 1c.

---

## 4. New entrants

| kind | on the ballot | reached 5% | largest |
|---|---|---|---|
| no record at all (seeded arrivals) | 265 | 3 (ActionSA 2021 ×3) | 18.12% |
| national record, national share < 3 quotas | 70 | 0 | 3.58% |
| national record, all | 87 | 6 (EFF 2016) | 11.64% |

- **Seeded arrivals**: never unit parties, never in the class, never bounded.
  They keep the Dirichlet spike. Its aggregate matches the record: seeded total
  p5/p50/p95 0.24/1.85/7.77% against the record's metro-year p10/p50/p90
  0.30/1.75/8.30%. Its tail is lighter: 5.7% of draws against 3 of 23
  metro-years.
- **National debutants below the line**: unit parties with `σ_deb`, no common
  factor.
- **National debutants above the line** (MK, RISE, BOSA by its centre): drawn as
  now. Their tails are in "For the owner".
- **Not fixed here**: audit 1a's 126.5 new-party wrong seats (COPE 2011 too high,
  ActionSA 2021 too low) are centre errors.

---

## 5. Judgement calls

| call | value | evidence | how to check |
|---|---|---|---|
| `UNIT_LINE_QUOTAS` (named; owner may change) | 3 | 0 of 273 on the ballot below it reached 5% (95% bound 1.1%); 0 of 212 established at 4 quotas; 1 of 217 at 5 | the writer reprints the table each cycle; a rise past 5% from below the line is a defect report |
| previous result for a party new to local elections | preceding-NPE share in this city | 70 cases, 0 to 5% | same table |
| unit test uses the centre too | max(previous, centre) | 5 panel exclusions; BOSA 2026 | trace lists exclusions and every party within ±10% of the line |
| `σ_cyc` estimator | RMS of earlier cycle means about zero | CLAUDE.md §4 E[k²]; cycle means −0.886 / −0.156 / +0.427 | the writer also reports sd about the mean, and cluster intervals |
| widths for 2026 | σ_cyc 0.57, σ_btw 0.19, σ_wit 0.71 (total 0.94); σ_deb 0.94 | forward ANOVA about the `pool_spec` centre. Caveat (N6): residuals about centres whose `level_shrink` was selected on 2016/2021 outcomes | regenerated by the writer; never adjusted to coverage |
| widths for 2016 / 2021 | total 1.06 / 0.89; σ_deb 0.94 / 1.27 | same; 2016 rests on one cycle | cluster interval printed |
| 2011 fallback | 0.27 / 0.48 (θ forward, target 2006) | the only out-of-sample record; wrong frame | 2011 labelled untestable; excluded from falsifier 4 |
| no common factor for debutants | | cycle means of opposite sign in 2 of 3 cycles | recheck each cycle |
| logit-scale cell draw; unit cells unfloored | | multiplicative draw overflowed 1.8% of JHB 2026 draws | guard count |
| Gaussian factors | ν = ∞ | exact κ | |
| no range cap | | an out-of-sample record cap (0.92x for 2016, 3.99x for 2021) was broken by 2021 (PA JHB 17.3x, class 3.57x) | |
| guard ε; falsifying rate | 1e-6; 5e-3 | numerical; expected 1.35e-4 | `41_guards` |

---

## 6. Predictions and falsifiers

Citywide simulation:
- unit parties drawn as §3.2 about their `pool_spec` centres;
- other parties from arm E's draws, scaled by (1 − unit total);
- no pool turnout, no ward ballot;
- list seats by largest remainder on 270, not the model's ward-plus-overhang
  allocation;
- four simulation seeds; figures are their means.

### 6.1 Johannesburg 2026 (5,000 draws)

| quantity | arm E | v2 prediction | **v3 prediction** |
|---|---|---|---|
| unit parties' mean list share, total | 5.09% | (assumed unchanged) | **4.68%** (0.41 points move to other parties) |
| AIC / ALJAMAAH / ACDP / ATM mean | 0.422 / 0.950 / 0.758 / 0.468% | | **0.379 / 0.879 / 0.731 / 0.428%** |
| draws with an established unit party above 5% | 473 | 39 | **31** (seed sd 7) |
| rate above 2% per party-draw, established unit parties | 0.0254 | 0.0105 | **0.0086** (record 0.011, 95% interval 0.14%-4.1%) |
| draws with any party of arm E mean share < 1% above 5% | 853 | 389 | **386** (mostly seeded arrivals, 285 in arm E, and VF+, 63; see "For the owner") |
| unit-class total p5 / p50 / p95 | 1.41 / 4.21 / 11.82% | 1.86 / 4.36 / 10.70% | **1.69 / 4.02 / 9.72%** |
| list seats, 20 unit parties below one quota | 5.41 | 4.42 | **3.80** |
| list seats, 5 unit parties above one quota | 8.20 | 8.61 | **8.04** |
| ALJAMAAH / ACDP / ATM p99 | 2.67 / 5.88 / 6.41% | 3.02 / 4.12 / 2.58% | **2.80 / 4.44 / 2.57%** |

Seats of unit parties fall for two reasons:
- the mean-share fall (N2);
- mass moving from the tail to the centre, which wins fewer seats below the
  remainder threshold.

### 6.2 Panel (24 city-years), out of sample

90% band coverage of realised list shares, all unit parties, about the
`pool_spec` centre:

| | n | v3 | note |
|---|---|---|---|
| 2016 | 81 | 0.926 | testable |
| 2021 | 127 | 0.850 | testable |
| 2016 + 2021 | 208 | **0.880** | the falsifier population |
| 2011 | 63 | 0.302 (37 below, 7 above) | width not testable (fallback in the wrong frame). At width 1.0 the reviewer gets 0.921 |
| all 24 | 271 | 0.745 | reported, not a falsifier |

**List MAE.** Moving unit parties to their `pool_spec` centres, with the freed
mass spread over the other parties in proportion, changes share-weighted list
MAE (`compare_history.vote_mae`) by −0.027 points on the panel mean.
- The range across city-years is −0.291 (Buffalo City 2011) to +0.105 (Cape Town
  2021).
- Mean mass moved: 0.26 points per city-year.
- Shape changes do not move the mean share, so this is the whole predicted
  effect on MAE.
- It is approximate: in the model the freed mass goes to each pool's members,
  not to all parties in proportion.

### 6.3 Falsifiers (tests of the description, never tuning targets)

| # | falsifier | v2 | **v3** |
|---|---|---|---|
| 1 | panel-mean list MAE change | outside ±0.05 of zero | **outside −0.027 ± 0.05** |
| 2 | unit party mean drawn share vs its centre | > 5% relative from centre | **> 5% relative from its `pool_spec` centre** (about 3 MC standard errors at 5,000 draws) |
| 3 | JHB 2026 draws with an established unit party above 5% | > 47 | **> 47** (a tenth of arm E's 473; prediction 31) |
| 4 | per-year coverage vs the sim | any year outside ±2 binomial se | **2016 and 2021 only**: outside 0.926 ± 0.06 or 0.850 ± 0.06. 2011 excluded (untestable) |
| 5 | guard firing rate | > 5e-3 of draws | **> 5e-3** (expected 1.35e-4) |
| 6 | unit parties' mean total at JHB 2026 | — | **outside 4.68% ± 0.15 points** (the centre shift is real or conservation failed) |

**Response to a coverage miss, declared now:** re-estimate widths only from the
record (a new cycle or corrected centres), never to coverage. A miss
concentrated in one sign goes to the level layer as a defect report.

---

## 7. Risks and couplings

- **Coverage on testable years: 0.880** (2016 + 2021), against arm E's
  over-coverage from a shape that also produced the extreme draws.
- **Parties above the line keep the spike** (For the owner). Next item: a shape
  fix for small cells that does not read `A`, informed by the per-member
  concentration test (first review, finding 14). The DA's Black African cell and
  its overhang coupling belong to the same item.
- **Level lift**: `1b-level-lift-defect.md`. A repair re-estimates these widths
  through the writer's key; the reviewer estimates σ_cyc for 2026 falling from
  0.57 to about 0.48.
- **Tests that move**:
  - `test_pool_conservation` (extend to unit cells via κ);
  - `test_draw_record` (retires at the first drawn-number change);
  - `test_reweight`, the drawer goldens, `test_group_share_tripwire` (values).
- **Interactive**: reweights by `pool_turnout_draws`; unit factors are
  turnout-independent; its code was not read.
- **Wards**: path unchanged, call site checked only.
- **Pairing** needs 1c first.
- **New artefact** `unit_width_record.json`.
- **Out of scope**: census date leak; PA level versus pool vector; split and
  arrival sizing; debutants above the line.
