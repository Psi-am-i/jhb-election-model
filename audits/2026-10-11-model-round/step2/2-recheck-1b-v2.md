# 2. Re-check of 1b v2 (small parties)

Read-only re-check of `audits/2026-10-11-model-round/step1/1b-small-party-design-v2.md`
against my review `step2/2-review-1b.md`. Nothing in `src/` or `data/` was written; no
model run, no `compare_history`, no emit. Scripts are in the session scratchpad
(`review1b/`: `v2common.py`, `line.py`, `anova.py`, `cov2.py`, `logit.py`, `level.py`,
`route.py`, `cen.py`), not committed.

To apply v2's line I took the previous-LGE list share (or, for a party absent from it,
the share at the preceding NPE in the same metro) from `levels._citywide_and_roster`,
the centre as arm E's mean list share, and the quota as 1/council of the target council.
That reproduces v2's membership exactly: 47 / 68 / 85 established unit parties at 2011 /
2016 / 2021; 16 / 13 / 42 debutants (v2: 41); at Johannesburg 2026, 20 established and 5
debutants, the largest ALJAMAAH (0.95%) and ACDP (0.76%).

---

## Part 1. The 15 findings

| # | finding | status | evidence |
|---|---|---|---|
| 1 | widths not out of sample | **fixed in the spec**; the 2011 attribution is wrong (new finding N1) | Forward drawn-centre components recomputed: cycle means −0.912 / −0.236 / +0.314 (n 47 / 67 / 84), within-metro sd 0.577 / 0.608 / 0.838, the same as v2. My between-metro sd is 0.00 / 0.19 / 0.31 against v2's 0.11 / 0.13 / 0.32: same order, different estimator, immaterial. Forward σ_cyc = RMS of earlier cycle means: 0.91 (2016), 0.67 (2021), 0.572 (2026), as stated. Coverage at v2's widths: 2011 **0.317** (37 below, 6 above, n 63), the same as v2; 2016 0.938 and 2021 0.880 against v2's 0.926 / 0.866; panel 0.765 against v2's 0.756. My n is 80 / 125, v2's 81 / 127, because I left out parties with zero realised share, which fall below every band. |
| 2 | unit rule depended on `A` | **fixed** | No decision reads `A`. COPE 2011, IFP eThekwini 2011, VF+ Tshwane 2011 and MK 2026 all fall outside the line, because their previous result or centre is above it. Overflow under the logit draw at JHB 2026 (sim, 200,000 draws): P(M ≥ 0.95) 3.3e-4 and P(M ≥ 1 − 1e-6) 1.35e-4, both in the Indian/Asian pool; the other three pools are at 0. v2 says 4.5e-4. Both are below the 5e-3 falsifier. |
| 3 | stale width table | **fixed** | No table is quoted as a parameter. The docstring correction carries the values I measured. |
| 4 | widths about the wrong centre; local-only parties had no width | **fixed in intent; not fixed in the numbers** (N2) | The estimator now needs no national size, so local-only parties are covered. But the residuals were taken about arm E mean shares, which are not the centre v2 conserves. |
| 5 | 1.06 first-timer width | **fixed** | Withdrawn. Debutant widths recomputed: means +0.25 / −0.66 / −0.15, RMS 0.92 / 1.61 / 0.61 (n 16 / 13 / 41), as stated. RISE and BOSA stay above the line, and their tails are reported rather than changed. |
| 6 | minor-mass and seat arithmetic | **fixed** | Indian/Asian unit mass at JHB 2026: mean 0.233 in my sim; v2 says "up to 0.228". The direction of the seat change is now right. |
| 7 | coverage used as a check on `A_STAR` | **fixed** | `A_STAR` is withdrawn. Coverage is a falsifier only, and the response to a coverage miss is declared in advance (§6.3). |
| 8 | pairing | **fixed by deferral** | Keyed streams under 1c. Sound if 1c lands first; v2 says this. |
| 9 | top-of-ballot effect overstated | **fixed** | v2 now claims no change to large parties, and the DA's minor cell is deferred. |
| 10 | inconsistent counts | **fixed, with a new denominator problem** (N4) | Established below three quotas: 368, 203 stood again, 0 reached 5%, maximum 4.41% (VF+ Mangaung 2021, from 1.85%). Debutants: 70 stood, 0 reached 5%, maximum 3.58% (AIC Buffalo City 2011). All reproduced. |
| 11 | σ_c double-counted | **fixed** | One ANOVA on one population. |
| 12 | class line inert | **fixed** | The line now decides unit treatment. |
| 13 | 2% tail below the record | **fixed** | Rate above 2% per party-draw: my sim 0.0088, v2 0.0105; arm E 0.0254 (reproduced); record 0.011. |
| 14 | per-member concentration test | **rejection sound** (Part 2) | |
| 15 | couplings | **fixed** | The tests, the interactive and the ward path are listed. The ward path is checked at the call site only. |

### The Johannesburg 2026 predictions, recomputed (logit cell draw, my sim)

| quantity | v2 | mine |
|---|---|---|
| draws with an established unit party above 5% (arm E 473, reproduced) | 39 | 35.7 per 5,000 |
| ALJAMAAH p99 / max | 3.02 / 4.06% | 2.84 / 4.40% |
| ACDP p99 / max | 4.12 / 13.40% | 4.06 / 25.65% |
| ATM p99 / max | 2.58 / 10.21% | 2.36 / 13.26% |
| unit-class total p5 / p50 / p95 | 1.86 / 4.36 / 10.70% | 1.69 / 4.02 / 9.96% |

The maxima differ because single draws are noisy. My centres are about 7% lower (N2).

### κ, the logit correction

κ is solved by 60-node Gauss-Hermite quadrature and bisection. It is exact to machine
precision (relative error 0 at m from 1e-6 to 0.5, sd 0.93 to 1.5). Monte Carlo checks
with 400,000 draws agree within their noise: largest error 0.9%, at m = 1e-6 and
sd 1.5. κ runs from −0.44 (small m) to 0 (m = 0.5) at sd 0.93; it is smooth and
unique, because E[logistic] is monotone in κ.

Solving it once per run is exact for what v2 specifies: unit cells read the unshocked
m_gi every draw, and x has a fixed normal marginal, since c_d + σ_wit z_i has total
sd √(σ_cyc² + σ_btw² + σ_wit²). Two things the spec should state:
- whether m_gi carries the `DIRICHLET_FLOOR` mean floor (`montecarlo.py:3374`) before
  κ is solved;
- that on the logit scale a party with a large cell has a citywide log sd below its
  measured width. ALJAMAAH, 20% of the Indian/Asian pool, realises 0.755 against a
  total width of 0.934; parties with small cells realise 0.925-0.929.

## Part 2. Finding 14's rejection

The rejection is sound. v2 reads `A` for no decision and leaves every non-unit party's
Dirichlet as it is, so a per-member concentration test cannot change anything this
design specifies. The diagnosis it was meant to support is already confirmed directly:
the record against the draws, and the Beta tails. The test still matters for what v2
leaves out (N3), and v2 lists it as open (§7). That is the correct place for it.

## Part 3. New findings

### N1. SHOULD-FIX. The 2011 coverage failure comes from the fallback width, not mainly from the level

v2 §6.2 says: "The 2011 failure is a level finding, not a width finding." With the
same centres and a 2011 width of 1.0 in place of the fallback's 0.27 / 0.48, 2011
coverage is 0.921 (2 below, 3 above) and the panel's is 0.907.

The fallback is the forward θ residual of target 2006, measured about `theta_prior`'s
centre. That centre leaves out the two things that separate the drawn centre from the
result:
- the `compress_levels` lift, +0.31 in log at 2011;
- local-route parties, whose spine residual at 2011 is −0.92 (12 parties).

v2 itself declares that the fallback's frame differs, so the 2011 band was too narrow by
construction. What the level evidence does show is in Part 4.

**Fix.** Say the 2011 width cannot be tested and is in the wrong frame. Then either take
a fallback in the drawn-centre frame (e.g. the pooled drawn-centre width, with the
leakage declared, or the LGE→LGE record for the previous pair), or keep 0.27 / 0.48 and
leave 2011 out of falsifier 4. Do not attribute 0.317 to the level layer.

### N2. SHOULD-FIX. The widths are measured about arm E's mean shares, but v2 conserves the `pool_spec` centre, which is lower

§3.1 and §3.4 make the unshocked `pool_spec` centre (Σ_g pool votes · props / Σ votes)
the quantity v2 conserves exactly. §3.3's widths, and every §6 number, use arm E's mean
shares as "the drawn centre". For unit parties the two differ systematically.

Mean log(arm E mean / `pool_spec` centre):

| target | mean | sd |
|---|---|---|
| 2011 | +0.033 | 0.13 |
| 2016 | +0.064 | 0.09 |
| 2021 | +0.099 | 0.16 |
| 2026 | +0.103 | 0.08 |

At JHB 2026: AIC 0.422% against 0.379%; ALJAMAAH 0.950% against 0.884%; ACDP 0.758%
against 0.731%. So arm E does not conserve small parties' centres (the mean floor and the
end-of-draw renormalisation), and v2 will. Two consequences:
- **Mean shares change.** Unit parties' mean shares fall by about 3-10% in log against
  arm E: about 0.4 points of Johannesburg's list vote moves from the 25 unit parties to
  everyone else. That contradicts "centres conserved; list MAE unchanged" as a
  comparison with the baseline. The mean seats of unit parties fall by more than the
  seat-curve effect v2 reports.
- **The forward widths are slightly off.** Cycle means about the `pool_spec` centre are
  shifted by +0.03 to +0.10 in log (2021 ≈ +0.41 rather than +0.31).

**Fix.** The writer computes `pool_spec` centres, as §3.5 already says. Re-derive §3.3's
table and §6 from them, and add the mean-share shift to the predictions. Falsifier 1
(list MAE ±0.05) should be checked against this predicted shift, not against zero.

### N3. SHOULD-FIX (scope, for the owner). The spike stays on every non-seeded party just above the line, which is where the remaining extreme draws come from

At JHB 2026 these keep the Dirichlet spike:

| party | previous LGE or national share | arm E mean | median | p99 | max |
|---|---|---|---|---|---|
| VF+ | 1.33% (previous LGE; line 1.11%) | 0.90 | 0.47 | 5.38 | 13.26 |
| IFP | 2.36% (previous LGE) | 1.49 | 0.60 | 9.71 | 21.47 |
| RISE | national debutant | 1.83 | 1.08 | 9.95 | 18.36 |
| BOSA | national debutant, kept out by its centre | 1.19 | 0.53 | 8.35 | 23.49 |

VF+ alone supplies 63 of v2's 389 draws with a sub-1% party above 5%. The record for
established parties at 3-10 quotas: sd log 0.85-0.88, 95th-percentile ratio about 2.0-2.2.
IFP's p99 is 6.5× its mean. So the owner's Problem 1 is solved below three quotas and
untouched above them. The line also switches parties between the honest treatment and
the pathological one: BOSA's `pool_spec` centre is 1.163% against a line of 1.111%
(+4.7%). Under v2 a party the model expects to grow is handed back to the spike.

**Fix.** Say this to the owner in plain terms. Next item: a shape fix for non-unit
parties' small cells that does not read `A`, for example the per-member concentration
test (finding 14) feeding a size-indexed concentration.

### N4. NOTE. "0 of 438" mixes two denominators

368 counts established parties whether or not they stood again (203 did). 70 counts
only debutants that stood (274 national parties were absent at the previous LGE and
below the line). The consistent population for parties on the ballot is 203 + 70 = 273,
none reaching 5%, with a one-sided 95% upper bound of about 1.1%, not v2's 0.7%. The
conclusion holds; the denominator should be stated as 273.

### N5. NOTE. Non-unit members' expected shares are close to conserved, not exactly

Non-unit members get (1 − M)·m_gj / Σ_non-unit m_g, with M built on unshocked unit
props and the denominator on post-IPF props. The unit parties' post-IPF props move with
other parties' level shocks, so E[share_gj] = m_gj·(1 − Σ m_unit, unshocked) /
(1 − Σ m_unit, post-IPF). The ratio is near 1 and is correlated with the draw. It is
largest in the Indian/Asian pool, where unit mass is 0.23. §3.4's "exactly" should say
"to first order", or the renormalisation should use the unshocked unit sum.

### N6. NOTE. Estimation, not tuning, with one caveat

The widths are the realised dispersion of the vote about a width-independent centre.
They read no predicted width and fit no realised-over-predicted ratio, so this is
estimation under CLAUDE.md §4. The caveat: the past centres come from today's code,
whose `compress_levels` constant was chosen on Johannesburg 2016 and confirmed
leave-one-out on the 2016/2021 panel (`montecarlo.py:2560-2568`). The 2021 and 2026
forward widths are therefore residuals about centres partly selected on those same
outcomes. Declare this next to the width rows in `JUDGEMENT-CALLS.md`.

`UNIT_LINE_QUOTAS` = 3 and σ_cyc as an RMS about zero are declared judgement calls; the
record cannot separate three quotas from four (0 of 212 that stood at four). The
3-cycle σ_cyc is noisy: 2016's width rests on one cycle (0.91). The writer should print
the cluster interval.

### N7. NOTE. A knife edge remains at the line, and it is smaller than v1's

Switching a party between the unit and Dirichlet treatments changes its shape, not its
mean. For BOSA as a debutant unit party, p99 would be about 6.7% (centre 1.16%, width
0.94) against arm E's 8.35%. That is moderate, unlike MK under v1 (23% → 60%). Listing
every party within ±10% of the line in the trace is enough.

---

## Part 4. The level question

**What the level evidence shows** (established unit parties, mean log of the result
over each stage's centre; `trace/20_spine.json`, `30_centres.json`):

| target | spine level | after `compress_levels`, normalised | arm E mean | `compress_levels` lift |
|---|---|---|---|---|
| 2011 | −0.577 | −0.886 | −0.912 | +0.310 |
| 2016 | +0.117 | −0.156 | −0.236 | +0.272 |
| 2021 | +0.681 | +0.427 | +0.314 | +0.254 |
| JHB 2026 (unit parties, n 25) | | | | +0.185 |

The spine residual at 2011 by route: blend −0.38 (n 33), local-only −0.92 (12).

- **`compress_levels` lifts small parties by 1.29-1.36× in every backtest cycle and by
  1.20× at 2026.** The 2026 figure is net of the renormalisation (after-shrink centres
  divided by their total of 1.112); v2's "about 1.3×" is the backtest figure. The lift
  is constant in sign and size, so it is a level defect. Its own docstring records the
  same cost (ranks 13+ from +0.78pp to +8.68pp, `montecarlo.py:2575-2583`).
- **The rest is the cycle, not a fixable level.** The spine residual swings −0.58 →
  +0.12 → +0.68. That is the class moving together between local elections (the
  record's class ratios: 0.38 / 0.68 / 1.38), and σ_cyc is what represents it.
- **So v2's attribution is half right.** About 0.3 of 2011's −0.91 is the lift; about
  0.6 is the cycle, mostly local-route parties collapsing. The 2011 coverage of 0.317
  is mainly the fallback width (N1).

**Ship alone, or only with a level fix?** It can ship alone, under ITERATING.md's "more
honest usually ships", once N1 and N2 are fixed. What it makes true that was false
before:
- established small parties' draws have the record's shape (median ratio near 1 rather
  than 0.003);
- extreme draws fall from 473 to about 36-39;
- the 2% rate matches the record;
- out-of-sample coverage is 0.93 / 0.87 at 2016 / 2021, the two years whose widths can
  be tested.

The headline loss is only at 2011, where the width cannot be tested. That is a stated
limit, not "worse and explains nothing".

Shipping alone stays coherent because the `compress_levels` lift is inside σ_cyc: the
RMS about zero includes the mean bias, −0.28 across the three cycles. The widths are
therefore honest about the centres as they are. If the level layer later removes the
lift, the writer's artefact key over the centres' inputs forces a re-estimate:
recomputed about lift-free centres, the cycle means would be about −0.60 / +0.04 / +0.57,
and σ_cyc for 2026 would fall from 0.57 to about 0.48. Doing the level fix first would
change the widths, not the design. The order matters only because each forecast-moving
change needs its own paired comparison.

The level fix should be filed as a defect report with the table above.

---

## Verdict

**Sound with listed fixes.** Nothing blocks. Before pre-registration:
- **N1:** declare 2011's width untestable and in the wrong frame, and stop attributing
  0.317 to the level layer;
- **N2:** re-derive widths and predictions about the `pool_spec` centre v2 conserves,
  and predict unit parties' mean shares falling 3-10% in log against arm E;
- **N3:** tell the owner that the extreme draws above the line (VF+, IFP, RISE, BOSA)
  remain.

N4-N7 are wording and declarations.
