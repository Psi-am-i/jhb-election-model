# 2. Review of 1j v4 (one whole-vote width curve)

Review of `step1/1j-universal-draw-design-v4.md` (579d8d9). Same constraints as
before: read-only on code, no model run, no `compare_history`, no emit, nothing
under `data/`, no sub-delegation.

My scripts are in `scratchpad/review1j/`:

- `v4f.py`: the joint fit, reimplemented, with variants;
- `r40.py`: the location's stability and co-movement;
- `r41.py`: Johannesburg 2026 under L1 and L2, both fits;
- `r42.py`: the newness profile likelihood.

The plausibility code (`uni4/wv.py`, `sumwv.py`, `scratchpad/plaus/plaus.py`)
was read, not rewritten. My fits skip v4's location fixed point.

## Verdict

**Ready for the owner's checkpoint after one blocking correction.**

The computations reproduce: the joint fit, the forward fits, both fits'
Johannesburg 2026 figures, and the plausibility pipeline. The joint location and
width fit is identified, and the record strongly supports it.

The blocking item is the **recommendation of L2**. L2 carries a known-sign bias
as one symmetric random factor whose loading changes sign across sizes. That
correlation structure is contradicted by the record, and on its own it decides
the large-party pass or fail. The owner cannot choose L1 or L2 fairly from the
text as written (finding 2).

MK's newness width is not identified by the record either way (finding 3). That
is a disclosure, not an error.

---

## 1. Joint location and width fit: identified, and the location is not eating spread

**Re-derived** (`v4f.py`, 2026 record; weight 1 per party-cycle over the whole
fit; my values before the fixed point):

| fit | a / b / midpoint / k | δ | c1 / c2 | m(s) at 11.7% / 1.5% / 0.5% / 0.05% | −2 log-likelihood (weighted) |
|---|---|---|---|---|---|
| full | 0.030 / 0.814 / 8.51% / 2.57 (v4: 0.030 / 0.816 / 8.56% / 2.57) | 0.871 (0.873) | 0.329 / 0.074 (0.342 / 0.075) | −0.16 / −0.36 / −0.21 / +0.69 (v4: −0.16 / −0.38 / −0.24 / +0.64) | 216.9 |
| full, no location | b 0.923 (0.925) | 0.669 (0.687) | — | — | 279.8 |
| without COPE and ActionSA | 0.030 / 0.824 / 8.06% / 2.47 (0.030 / 0.827 / 8.05% / 2.46) | 0.845 (0.844) | 0.340 / 0.076 | −0.16 / −0.37 / −0.22 / +0.68 | 211.9 |

The forward fits also reproduce:

- 2016 full: b 0.728, δ 0.937, m(0.5%) −0.82 (v4: 0.720, 0.955, −0.87);
- 2021 full: 0.766, 0.946, −0.55 (v4: 0.774, 0.945, −0.59);
- 2016 without COPE and ActionSA: 0.797, 0.726 (v4: 0.804, 0.697).

**Identified.** The location adds two parameters and improves −2 log L by 63.
It is a function of size only, so it cannot absorb dispersion among parties of
one size. Adding a separate mean for new parties changes nothing: the fitted
offset is +0.001, and δ stays at 0.871. So δ is not standing in for the seeds'
level bias. The tied offset −(σ² + δ²)/2 together with m(s) already carries
that bias.

**Does the location absorb real spread?** Across three cycles it is systematic,
not random. The band difference "under 0.1% minus 0.3-5%" (established, mean
`r`) has the same sign every cycle and grows: +0.31 (2011, n 2), +0.72 (2016),
+0.88 (2021). The cycle-level swings around it stay in σ and in the shared
share. With one cycle (target 2016), m(s) is that cycle's swing and absorbs it
whole. v4 states this.

**Extrapolation, a note.** m(s) is quadratic in log size. It reaches +1.0 at
0.03%, where Johannesburg 2026's seeds sit, and +1.78 at 0.01%. No Johannesburg
2026 centre falls below the record's minimum, but under L2 this value is a
shared-factor loading. The writer should clamp m(s) at its value at the
record's 1st-percentile centre, which is 0.016%.

## 2. L1 against L2. **Blocking (the recommendation).**

**Total variance: not a double count.** σ is fitted about m(s), so σ² holds no
mean term. L2 adds m², making the total the second moment about the offset.
That is the E[k²] reading CLAUDE.md §4 allows. The location's cycle-to-cycle
variation is in ρσ², and L2 adds its mean square. These are two different
quantities.

**Correlation structure: unsupported, and it decides a rule.** L2 draws one
normal for the whole city and loads every party below 20% on it with loading
m(s). For Johannesburg 2026 that is:

- +1.0 for the 0.03% seeds;
- about −0.2 to −0.38 for every party from 0.3% to 12%, ASA, EFF, MK and PA
  included.

This has three consequences:

- **It makes the 1-12% parties move as one.** v2 and v3 measured that group's
  shared city-year share at 0.00; v4's own fit gives 0.11.
- **It ties the tiniest parties against everything above them.** Their
  correlation is −1 on that component. Measured (`r40.py`, 22 city-years,
  standardised about the fitted location): the correlation of city-year mean
  residuals between centres under 0.2% and 0.3-20% is **+0.11**. The record
  shows no anti-correlation.
- **The bias has a known sign every cycle**, so a symmetric factor sends half
  the draws the opposite way from it.

The large-party result follows from this structure, not from the widths.
Johannesburg 2026 (citywide simulation, my reimplementation, 4 seeds):

| fit | mode | DA / ANC log-sd | ASA / EFF / MK / PA | established < 1% above 5% (draws) | largest new party > 18.12% (draws) |
|---|---|---|---|---|---|
| full | L2 | 0.18 / 0.18 | 0.28 / 0.31 / 0.87 / 0.61 | 21.2 (v4 21.8) | 612 (607) |
| full | L1 | 0.16 / 0.16 | 0.26 / 0.29 / 0.86 / 0.57 | 17.8 (17.5) | 608 (602) |
| without COPE and ActionSA | L2 | 0.18 / 0.18 | 0.26 / 0.29 / 0.84 / 0.59 | 24.5 (25.3) | 593 (590) |
| without COPE and ActionSA | L1 | 0.16 / 0.16 | 0.25 / 0.28 / 0.83 / 0.55 | 19.5 (20.3) | 586 (581) |

All v4 §3 Johannesburg figures reproduce within seed noise. In v4 §3 the
large-party rule fails under L2 on both fits and passes under L1 on both. The
only difference between the two is this factor.

**Fix.** Do not propose L2 as written. Either:

- present L1 and L2 neutrally, stating that L2's correlation pattern (opposite
  signs at the two ends, the middle moving together) is not in the record and
  is what fails the large-party rule; or
- offer an L2′: add m(s)² to the existing size-group shared term (loading
  √(ρσ² + m²) on `z`). That carries the same E[k²] with the co-movement the
  record shows.

Clamp m(s) as in §1 in either case. The level-layer correction stays next round.

## 3. One newness term: a size-dependent term is not supported, and neither is MK's width

Measured (`v4f.py`, `r42.py`; 2026 record; weighted likelihood, one unit per
party-cycle). The 2ΔNLL column gives each variant's change in weighted −2 log L
against v4 (positive means a better fit).

| variant | full: δ (< 1% / ≥ 1%) | 2ΔNLL vs one δ | without COPE and ActionSA | 2ΔNLL |
|---|---|---|---|---|
| one δ (v4) | 0.871 | — | 0.845 | — |
| δ split at 1% | 0.866 / **0.938** | 0.04 | 0.857 / **0.000** | 1.0 |
| δ linear in log size | 1.09 at 1%, slope +0.12 per log unit | 2.1 | 1.14 at 1%, +0.15 | 1.7 |

**New parties at 1% and over are 6 party-elections in the full fit** (COPE
2011, EFF 2016, AIC 2016, GOOD 2021, PA 2021, ASA 2021) **and 4 without COPE
and ActionSA.** Profile of δ for those parties (2ΔNLL < 2.71):

- full: about 0.42-1.78, best near 1.0;
- without COPE and ActionSA: 0-1.57, best at 0.

The record therefore supports no size dependence. The split point estimate
goes from above the common δ to zero when two parties are removed, and no
variant improves the fit by more than 2.1. But a size-dependent term is also
not rejected. MK's log-sd of 0.84-0.87 rests on the ~200 small arrivals' δ,
extrapolated. The record's own estimate for parties like MK spans from no extra
width to wider than v4.

The whole-vote record does not call v4's newness width implausible either. On
the 16 backtests the realised largest new party fell outside the record's range
in **3** city-years. v4 L2 expects 4.1 (P(X ≤ 3) 0.38); arm E expects 1.87
(`sumwv.json`).

At Johannesburg 2026, 12.6% of draws above the record against roughly 3%
exchangeable per side is consistent with the world leaving this envelope 3
times in 16.

**Fix (disclosure).** State the ≥ 1% profile intervals beside MK's width. State
that the uniform δ meets the owner's one-rule requirement and that the record
cannot choose between it and a size-dependent term. MK's width is a case for the
§11 overlay, reported with and without, which v4 §1.4 already says.

## 4. Side-by-side table: reproduced

The Johannesburg 2026 log-sds and counts for v4 L1 and L2, both fits, are in the
table in §2: within 0.02 in log-sd and about 1-2% in counts. The v3 A and B
figures were reproduced in my v3 recheck. The backtest whole-vote rows come from
the designer's `wv_*.json` through `sumwv.py`. I checked their arithmetic
(Poisson-binomial tails, counts) against the json, not by rerunning the draws:

- J ≥ 2 expected 4.96 against 4 realised (v4 L2);
- parties ≥ 1% P(X ≥ obs) 0.173 (L2) and 0.013 (L1);
- previously sub-1% parties reaching 1%: 0.020 / 0.000.

## 5. Whole-election measures against 1h: mostly as specified, five deviations to label

As specified:

- the features (1h §1.1, rows 1-16) in `plaus.features`;
- strict references of 16 / 24 / 32 transitions;
- envelope exceedance against the record's min and max;
- the Poisson-binomial event test (1h §3a′);
- the joint `J`;
- the backtests' forward widths.

Deviations to label in the table:

1. **`J` uses 7 core features, not 1h's 8.** `w_top` is dropped because there
   is no ward layer. Comparisons inside v4 are consistent, but its arm-E 36.4%
   is not 1h §4.1's 47.2%. Say "7 of 8; `w_top` not computable".
2. **Exceedance is reported both sides combined.** 1h asks for below and above
   separately against 1/(n+1) per side, plus the ±1 IQR envelope. The direction
   matters: too narrow and too wide are different failures.
3. **PIT is not randomised.** `wv.py` uses `mean(x < real)`. For count features
   (`n_ge1`, `n_ge5`, `tiny_n_ge1`) the ties then put a realised value that
   equals the draws' mode outside the central 90%. For example, `tiny_n_ge1`
   shows 5-6 of 16 "inside" for every model. The v4 table quotes PIT only for
   continuous features (`sub1_mass`, `outside2`), so no quoted number is wrong.
   Fix it before the count PITs are used.
4. **`outside2` is `100 − top2` exactly.** It adds no information beyond `top2`,
   which is already a core feature, so do not present it as an additional
   whole-vote check.
5. **Not like-for-like.** "Today" is the full model's `pr_share_draws`. The
   designs are the citywide simulation (no IPF, Dirichlet or ward layer; arm E's
   turnout draws). For list-share features the missing layers are small (VD and
   ward noise about 0.3% of a share, 1f §4.2), but the column header should say
   which is which. The backtests use 1,000 draws per city-year with one seed
   for every city-year. That is Monte Carlo noise of a point or two on the rates
   and changes no conclusion.

## Decisive numbers

| quantity | v4 | mine |
|---|---|---|
| 2026 curve b / midpoint / δ, full | 0.816 / 8.56% / 0.873 | 0.814 / 8.51% / 0.871 |
| same, without COPE and ActionSA | 0.827 / 8.05% / 0.844 | 0.824 / 8.06% / 0.845 |
| location's improvement in −2 log L | not reported | 63 for 2 parameters |
| separate mean for new parties | not tested | +0.001 (none) |
| δ at ≥ 1%: point / profile interval, full | not tested | 0.94 / ~0.42-1.78 |
| same, without COPE and ActionSA | not tested | 0.00 / 0-1.57 |
| corr of city-year residuals, < 0.2% against 0.3-20% | not tested | +0.11 (L2 implies negative) |
| JHB 2026 DA / ANC log-sd, L2 / L1 | 0.18 / 0.16 | 0.18 / 0.16 |
| JHB 2026 MK log-sd, full / without | 0.87 / 0.84 | 0.87 / 0.84 |
| largest new party above 18.12%, L2 full / without | 607 / 590 | 612 / 593 |
| backtest `max_new` outside: realised / expected (L2) | — | 3 / 4.1 |

## Not checked

- I did not rerun the backtest whole-vote draws or the CRPS bootstrap; I read
  their outputs.
- I did not check the location fixed point.
- Nothing ran through the real drawer.
