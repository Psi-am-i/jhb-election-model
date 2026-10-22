# 2. Review of 1b (small parties, the class line, new entrants)

Independent, read-only review of `audits/2026-10-11-model-round/step1/1b-small-party-design.md`.
Nothing in `src/` or `data/` was written; no model run, no `compare_history`, no emit.
Scripts are in the session scratchpad (`review1b/`), not committed.

Sources read: `src/montecarlo.py` 3040-3400 (`make_drawer`, `draw_pools`), 2607-2830
(`pool_spec`), 528 (`log_shock`); `src/pools.py` 3510-3540 (`dirichlet_alpha`), 4196-4199,
6401; `src/levels.py` `_citywide_and_roster`; `src/theta_residual.py` (docstring and
`residuals()`, run in this session: 403 rows); arm E (`data/arms/step11/E/<city>-<year>/`
`arrays.npz`, `meta.json`, `trace/{20_spine,30_centres,02_pools_artefact}.json`); the pool
specs each run read (every `artefact_key` checked equal to its run's `02_pools_artefact.json`,
all 25 city-years). Pool cells were rebuilt with `montecarlo.pool_spec` on each run's
`30_centres.after_shrink`, with the `DIRICHLET_FLOOR` mean floor as at `montecarlo.py:3374`.

"Record" = real election results; "arm E" = the model's draws; "sim" = my citywide
simulation of the proposed draw (lognormal unit parties, arm E's mean shares as centres,
no pool turnout, no ward ballot), the same simplification the design used for §6.

---

## What I recomputed and found to agree

| design claim | recomputed | source |
|---|---|---|
| 337 cases under 1% at the earlier LGE of a 2006→2011, 2011→2016, 2016→2021 metro pair; 175 stood again | 337 / 175 | `levels._citywide_and_roster` on `lge{year}_{CODE}_vd_party_clean.csv` |
| later/earlier quantiles 5/25/50/75/95/99% 0.26/0.42/0.80/1.39/4.07/7.34, max 17.3, sd log 0.88 | 0.26/0.42/0.80/1.39/4.07/7.34, max 17.3, sd log 0.879 (IQR-based sd 0.884) | same |
| two reached 2%: VF+ Ekurhuleni 0.90→3.48%, PA Johannesburg 0.17→2.96% | same two | same |
| 265 entrants with no national record (median 0.055%, p99 5.52%, max 18.12%, ASA ×3 ≥ 5%); 87 with one | 265 / 87, same quantiles | same, plus `npe{2009,2014,2019}` |
| first local election vs preceding NPE (NPE ≥ 0.5%): 24 cases, median 1.02, sd log 1.06 | 24, 1.02, 1.06; mean log −0.60; max 2.99 (AIC NMA, 0.54→1.61%) | same |
| JHB 2026: 321 cells, 290 under 1% of pool, 307 with a < 1, 283 < 0.1, 160 < 0.01 | 321 / 290 / 307 / 283 / 160 | `pool_spec` rebuild |
| AIC alone, Beta(0.106, 16.20) × 0.560: P(> 2%) 0.054, P(> 5%) 0.0125, P(> 10%) 0.0015, median/mean 0.0085 | 0.0539 / 0.0125 / 0.00149 / 0.0031÷0.364 = 0.0085 (4M draws) | simulation |
| level shock alone gives P(AIC > 5%) ≈ 0 | 1.2e-4 (t₇ scaled to sd 0.444 as `log_shock` does, centre 0.38%) | `montecarlo.py:528-557` |
| √trigamma(a) = 0.88 at a = 1.73, 0.76 at 2.19, 0.80 at 2 | 0.880 / 0.760 / 0.803 (sd of log Gamma draws) | simulation |
| between-metro-year sd of forward θ residuals, national < 1%: 0.17 | 0.167 (one-way ANOVA, 250 rows, 32 metro-years; within sd 0.767) | `theta_residual.residuals()` |
| arm E: 403 draws in which a party with a 2021 share under 1% exceeds 5% (design: 400) | 403 | `arrays.npz` |

The diagnosis in §1.1 stands: the tails of established small parties come from the
within-pool Dirichlet at concentration far below 1, not from the level shock.

---

## Findings

### 1. BLOCKING. The widths §3.5 specifies are not the widths §6.2 used, and with the specified ones the design fails its own falsifier

§3.5 says the width record carries, per target year, widths "from targets strictly before
the target year". §6.2's coverage (0.871) and every number in §6 used widths pooled over
all four target years, 2006-2021, so each backtest year was scored with widths fitted
partly on its own outcome and on later ones.

Forward θ residuals by target, RMS by national size bin (`theta_residual.residuals()`,
this session):

| widths available for target | < 0.2% | 0.2-1% | 1-5% | 5-15% |
|---|---|---|---|---|
| 2011 (residuals of target 2006 only) | 0.404 (n 14) | 0.403 (25) | 0.311 (25) | 0.230 (5) |
| 2016 (2006, 2011) | 0.730 (35) | 0.525 (54) | 0.485 (36) | 1.216 (12) |
| 2021 (2006-2016) | 0.712 (57) | 0.738 (95) | 0.517 (49) | 1.038 (17) |
| pooled, all targets (what §6.2 used) | 0.916 (110) | 0.697 (140) | 0.500 (64) | 0.875 (25) |

Sim, 90% band coverage of actual list shares for the unit parties at a* = 2.0 (seeds
excluded; 296 party-cases; σ = 1.06 for a party with no previous-LGE share):

| widths | coverage | below band | above band | 2011 | 2016 | 2021 |
|---|---|---|---|---|---|---|
| arm E draws | 0.922 | 6 | 17 | | | |
| design table (0.92/0.74/0.45/0.66) | 0.868 | 19 | 20 | 0.818 | 0.918 | 0.866 |
| forward, strictly before target (§3.5 as written) | **0.757** | **46** | 26 | **0.506** (35 below, 3 above, n 77) | 0.871 | 0.828 |

My 0.868 reproduces the design's 0.871, so the method agrees; the difference is the
leak. Two things combine at 2011. Its only prior cycle (2006) was quiet, so the forward
widths are about 0.40. And the unit parties' actual shares sit far below the drawn
centre: median log(actual / arm E mean share) is −0.74 at 2011, −0.29 at 2016, +0.05 at
2021 (77/84/132 parties), while the θ residuals, measured about `theta_prior`'s centre,
average +0.12 at 2011. The Dirichlet spike at zero was covering misses about the drawn
centre that the θ residuals never measured (finding 4). This is also CLAUDE.md §4's "a
level is not necessarily a constant" applied to the width table: the design invokes it
for σ_c and not for σ_i.

Limits: citywide sim, arm E means as centres, centre share as the size bin in place of
national size, no class factor (σ_c = 0.17 would widen the 2011 band slightly, not
enough to move 35 lower misses).

**Fix.** Re-predict §6 with the widths §3.5 will actually produce. Then choose, and
write into `JUDGEMENT-CALLS.md`, one of: (a) forward widths as specified, accepting that
2011 cannot be forecast honestly from one prior cycle and saying so in the prediction;
(b) a width taken at the RMS over cycles (`E[k²]` logic, §4), with an explicit cycle
component sized from the record (the conditional class mean residual by cycle:
2006 ≈ +0.12, 2011 ≈ +0.12 with spread −0.32..+0.82, 2016 ≈ −0.10, 2021 ≈ +0.42), declared
as using later cycles if it does. The 0.871 figure cannot be pre-registered.

### 2. BLOCKING. Line 1 depends on the fitted pool concentration `A`, so it classes 5-17% parties as units and puts the 2026 forecast's MK on the knife edge

A party is a unit party when none of its cells has `a = A·m ≥ a*`. `A` is not stable
across specs: every 2011 spec carries `ALPHA_FALLBACK` = 12.0 in all four pools
(`pools.py:4199`, "too few splits to fit"), and elsewhere `A` runs from 10.6 (Ekurhuleni
2021 Indian/Asian) to 174.5 (eThekwini 2016 Black African). At `A` = 12 a cell needs
16.7% of its pool to be major.

Unit parties at a* = 2.0 that the design does not mention (centre share, max cell `a`):

| city-year | party | centre | max a | width it would get |
|---|---|---|---|---|
| Johannesburg 2011 | COPE | 9.92% | 1.38 | 1.06 (no local record) |
| Tshwane 2011 | COPE | 7.87% | 1.15 | 1.06 |
| Cape Town 2011 | COPE | 7.24% | 1.90 | 1.06 |
| Ekurhuleni 2011 | COPE | 6.58% | 0.92 | 1.06 |
| eThekwini 2011 | IFP | 8.56% | 1.44 | national-size bin |
| Tshwane 2011 | VF+ | 5.22% | 1.68 | national-size bin (VF+ national < 1% → 0.74) |
| Buffalo City 2011 | COPE | 17.09% | in [1.73, 2.19) | switches inside the design's own a* range |
| Johannesburg 2026 | MK | 9.09% | **2.00128** | Dirichlet by 0.06%; 1.06 if below |

MK's Black African cell at Johannesburg 2026: m = 0.122702, `A` = 16.310155,
a = 2.001281. A 0.07% relative fall in MK's centre (9.09% → 9.084%) makes MK a unit
party. MK's draw then changes from arm E's p99 22.7% to a mean-1 lognormal of width
1.06: p99 59.8%, P(> 30%) 4.9%, P(> 50%) 1.6%. COPE Johannesburg 2011 as a unit party:
p99 65.2%, P(> 50%) 2.0%, against an actual 1.11% and a record (first local election
after a national debut) whose largest ratio is 2.99 and whose largest for any party at
2% or more nationally is 1.50.

The overflow guard of §3.2 ("expected never to fire") fires in the 2011 runs. Sim,
share of draws with a pool's minor mass M_g ≥ 1 − 1e-6: Cape Town 2011 Black African
1.42%; Johannesburg 2011 0.63%/0.39%/0.27%/0.17% across its four pools; Tshwane 2011
0.39%; Ekurhuleni 2011 0.26%. In those draws the major members of the pool (the ANC's
Black African cell) are pushed to ε and conservation fails. The statement "under 0.06,
e_i would need to be ~16" holds only at Johannesburg 2026 (finding 6).

The design's §2.2 says E differs from every size line "in one case, ALJAMAAH". That is
true at Johannesburg 2026 and false on the panel, where it differs at every 2011
city-year. §6.2's panel sim was run at a* = 1.0 and 1.9, not the recommended 2.0; at
1.0 COPE is a unit party only at Ekurhuleni 2011.

**Fix.** Separate the two decisions Line 1 merges:
- *Which parties are unit parties*: a party-level rule on the party's own size and
  record, not on `A`. E.g. a previous-LGE share and a centre both below a line (finding
  12 proposes three quotas), seeds excluded, and no party above the line ever. This is
  the population the record (finding 10's 0 of 368) speaks about.
- *Which cells of a Dirichlet party are held at their mean*: `a < a*` can stay, since
  that is about the shape of one cell.
- Bound the unit-party lognormal coherently: draw `e_i` truncated so that no pool's
  minor mass reaches 1 (truncate and renormalise the mean, counted), or draw unit
  parties' pool share on the logit scale. A counted guard that fires in 1% of a run's
  draws is a mechanism, not a guard.
- Remove the knife edge: interpolate treatment over a band of `a` (or of size) rather
  than switch at a point, or at least report every party within ±10% of the line in
  the trace and in the pre-registration.

### 3. SHOULD-FIX. The width table in §3.3 is the stale docstring table, not the design's own recomputation

§3.3's 0.92 / 0.74 / 0.45 / 0.66 are the `theta_residual.py` docstring's (n = 78/96/32/14,
257 rows). `residuals()` now returns 403 rows; the design's own §2.1 table was computed
from those (110 rows < 0.2%, rms 0.92). Current values by the same bins: 0.916 (110) /
0.697 (140) / 0.500 (64) / 0.875 (25). The 5-15% bin moved 0.66 → 0.88. The ≥ 15% bin
moved 0.138 → 0.284 (n 37 → 64), so the docstring's statement that the θ width at the
top is "vindicated" is also stale; that is outside this design but the design's §1.1
quotes the docstring's "1.7-3.5x" (now 2.0/1.9/1.7/4.7x against `fitted_sd` medians
0.46/0.37/0.30/0.19).

Population: σ_i is for "a unit party with a local record", but the bins mix parties
with and without θ history. Restricted to `had_record`: 0.959 (57) / 0.560 (109) /
0.485 (50) / 0.330 (13).

**Fix.** §3.5's writer generates the table; the design should not quote one. State the
population (θ history or not) the table is fitted on and apply it to the same population.
Correct the docstring in the commit that adds the writer (CLAUDE.md §2).

### 4. SHOULD-FIX. The widths are residuals about a centre the draw does not use, and one class of party has no width at all

`theta_residual` measures log(observed θ) − log(`theta_prior`'s centre). The draw is
centred on `30_centres.after_shrink`, normalised. At Johannesburg 2026 the after-shrink
centres of small parties are about 1.29-1.35× the spine level and the centre total is
1.112, so the drawn centre is about 1.2× the θ-route level (AIC: spine 0.319%, drawn
0.379%). The spine also blends local and national routes (`20_spine.detail`, w_local
0.04-0.33 for AIC, ATM, PAC, ACDP, NFP). The design's claim that "the model's centres
already condition on the intervening national election" is true for the national
route only. The gap is measurable on the panel: for the unit parties at a* = 2.0, the
mean of log(actual / arm E mean share) is −0.74 at 2011, −0.27 at 2016, +0.16 at 2021;
the mean metro-year θ residual about `theta_prior`'s centre for parties under 1% national at the same targets is +0.12, −0.10,
+0.42. A width measured about one centre is being applied about another that sits 0.3-0.9
in log away from it.

Seven non-seeded parties in the Johannesburg 2026 draws take the route "local only (no
national record)" (UIM, CHANGE, INTERNATIONAL_REVELATION_CONGRESS, ...). They have a
local record, so they are unit parties of the class, and their national size is 0, so
the national-size table has no row for them. In other city-years such parties are
larger (Ekurhuleni 2011: DISPLACEES_RATE_PAYERS_ASSOCIATION, centre 1.74%).

**Fix.** Measure the unit width as the forward residual of the realised share about the
drawn centre (what the run would have drawn around), by local size; or keep the θ
residual and state the substitution and its measured effect. For local-only parties use
the LGE→LGE record (sd log 0.88 overall; 0.82/0.92/0.90/0.71 by earlier-share band).

### 5. SHOULD-FIX. The first-timer width of 1.06 is a centre error stored as a width, in the frame the design itself rejects

The 24 cases are raw LGE/NPE ratios, the unconditional frame §3.3 argues against for
established parties. They are bimodal: COPE 2011 ×8 at 0.12-0.28 (a split collapsing),
EFF 2016 ×8 at 1.01-1.50, others 0.06-2.99. Mean log −0.60: most of the 1.06 is COPE's
level error, which a mean-1 lognormal turns into a symmetric width. Its upper tail has
no support: p95 ratio 3.2, p99 6.6, against a record maximum of 1.50 for any party at
2% or more nationally.

Unstated consequence at Johannesburg 2026: RISE (centre 1.82%) gets p99 ≈ 12%, wider
than arm E's 9.95%; BOSA (1.16%) p99 ≈ 7.7%. The design narrows established small
parties and widens the national debutants. If MK crosses a* (finding 2) the same width
applies to a 9% party.

**Fix.** State that 1.06 is a width fitted to a mixture of one split's collapse and
one party's steady arrival, eight parties in all. Either fit the width in the
conditional frame (residual about the drawn centre for parties at their first local
election, `theta_residual`'s "no record" rows: rms 0.867/1.045/0.553/1.215 by bin, means
+0.45/−0.09/−0.04/−0.60) or declare a narrower value as a judgement call with this
table as its evidence, and bound the upper ratio at a record-supported value, declared.

### 6. SHOULD-FIX. The arithmetic of two §3/§6 statements is wrong

- **Minor mass.** §3.2: "At JHB 2026 the minor mass of a pool is under 0.06." Unit-party
  minor mass by pool: Black African 0.110, Coloured 0.043, Indian/Asian 0.062, White
  0.075. Adding Dirichlet parties' held minor cells: 0.138 / 0.189 / 0.223 / 0.182. The
  guard still does not fire at Johannesburg 2026 (sim: 0 of 200,000), but it does at
  2011 (finding 2).
- **Mean seats of unit parties.** §6.1 expects them to rise slightly. Sim at
  Johannesburg 2026 with largest-remainder list seats on 270 (not the model's ward +
  overhang allocation): the 28 unit parties hold 25.69 → 25.65 seats in total; the 20
  with a centre below one quota fall 5.41 → 4.39; the 8 above one quota rise 20.28 →
  21.26. The seat curve is flat at zero below the remainder threshold, so concentrating
  a sub-quota party's mass near its centre loses the seats its tail used to win. The
  class members (15) fall 3.78 → 2.99.

**Fix.** Replace the §6.1 seat statement with the split above, computed on the real seat
allocation; the pre-registration should predict the class members' seats falling.

### 7. SHOULD-FIX. The check for `A_STAR` is the tuning §7 forbids

§5 lists "panel coverage of unit parties at 1.0, 1.73, 2.19" as how to check `A_STAR`;
§7 says `A_STAR` must never be tuned to coverage. Panel coverage is realised over
predicted width, the barred `k*`-type quantity (CLAUDE.md §4). §7's "if too narrow, the
repair is the width table" is also tuning unless the new table comes from the record
independently of the coverage result. The falsifier "simulated class-total sd within
0.31-0.35" is a consistency check of the inputs (it follows from σ_i, σ_c and the
Herfindahl), not a test against an election.

**Fix.** Drop coverage as the check for `A_STAR`; its check is the record quantity that
pins it (√trigamma against the record's sd log, recomputed by the writer). Keep coverage
as a falsifier only, with the width table's response pre-declared (re-estimate from the
record, never adjust to coverage).

### 8. SHOULD-FIX. The comparison run cannot be paired the way §7 says

§7: draw `c` and `u` from a separate generator so the run shares draws with its
baseline. The main stream still diverges: removing minor cells changes the length of
the vector passed to `rng.dirichlet` (`montecarlo.py:3376`), which changes how many
Gamma variates it consumes, so every later draw on `rng` (later pools, turnout, ward
draws) de-syncs from the first pool of the first draw. This is the failure MODEL-LOG
§1.296 found for A/B8, C/B and C16/D.

**Fix.** Keep the call shape: draw the full-length Dirichlet from `rng` as now and
overwrite the minor components (renormalising the major ones), or move the split and
the new factors to their own generators in both arms (which needs a baseline re-run).
Pre-register the per-draw correlation check §1.296 used.

### 9. SHOULD-FIX. The effect on the top of the ballot is overstated for two of the three parties named

§6.1 and §7 say the DA's, ANC's and EFF's upper tails shorten. Sim of each party's
within-pool split only (independent Beta per pool × pool vote share, no level shock or
turnout), current against minor cells held at their mean:

| party | median | p1 | p99 |
|---|---|---|---|
| DA | 25.96 → 26.19 | 17.30 → 18.04 | 36.32 → 32.38 |
| ANC | 23.54 → 23.52 | | 39.82 → 39.54 |
| EFF | 10.22 → 10.22 | | 25.74 → 25.54 |

Only the DA moves materially, and on both tails. The DA's p99 falling about 4 points
changes how often the DA wins wards beyond its list entitlement, i.e. overhang, which
the design does not mention.

**Fix.** State the table above for the real draw, and name overhang among the couplings.

### 10. NOTE. Counts in §2 that do not agree with each other

- §2.2 candidate C: "0 of 383 below 3 quotas". The design's own §2.1 table sums to 368
  below 3 quotas (158 + 69 + 77 + 40 + 24), and I count 368 (203 stood again), none
  reaching 5%. Below one quota: 304, none.
- §4's entrant table is labelled "2006→2021 pairs (352 cases)" but counts 7 with a
  national record reaching 5%, including the ID (Cape Town 2006), which belongs to the
  quarantined 2000→2006 pair. Within the stated population it is 6 (EFF 2016 ×6).

### 11. NOTE. σ_c and σ_i overlap slightly, and σ_c is measured on a different membership

σ_c = 0.17 is between-metro-year sd for parties under 1% **national**; the class is
defined by one **local** quota on max(previous LGE share, centre). The σ_i table is RMS
including the between-group part, so adding `c` counts 0.17 twice (0.74 → 0.76 in
quadrature). Small; state it, or take σ_i as the within sd (0.767 at < 1% national).

### 12. NOTE. The class line is nearly inert, and the record does not locate it

Sim at Johannesburg 2026: the class factor leaves the 15 class members' mean seats
unchanged (2.98 without `c`, 2.99 with) and raises their seat sd 1.58 → 1.74. Class
total p5/p50/p95 0.77/1.33/2.49%, sd log 0.357 (record, conditional frame: 0.31-0.35).
The record's between-group sd barely moves with the line (0.00 / 0.17 / 0.11 / 0.15 at
national 0.2 / 1 / 2 / 5%), and the class-total sd is flat across lines. The design's
conclusion here is right. What decides seat outcomes is unit-party eligibility
(finding 2), not class membership.

### 13. NOTE. The proposed tail is thinner than the record at 2%, within the record's uncertainty

§6.1 reports the proposed rate above 2% per party-draw, 0.0049, against arm E's 0.0205
and the record's 0.011 (2 of 175). The record's 95% binomial interval is about
0.14%-4.1%, so 0.0049 is inside it. Both record cases were a party near 1% or a party
gaining a pool (PA 2021); the design should say the proposed tail sits below the record
point estimate and why that is acceptable, rather than leave the three numbers side by side.

### 14. NOTE. A record test of the diagnosis that the design does not run

21 of Johannesburg 2026's cells lie inside the `A` fit's own population (m ≥ 1% of the
pool) and have a < 2 (e.g. DA Black African m 0.026, a 0.43; MK White m 0.054, a 1.20).
For these the method of moments matched the variance of the weighted pool, dominated by
large members. The direct test is a per-member concentration from the same fitting
splits (`pools.py` near 6370-6401), by member size: if small members' own m(1−m)/var is
much larger than `A`, the record says the Dirichlet over-disperses them and the shape
argument has a measurement behind it rather than a comparison with citywide ratios.

### 15. NOTE. Couplings the design lists incompletely

- Tests that move besides `test_reweight` and the drawer goldens: `test_pool_conservation`
  (asserts Dirichlet means), `test_draw_record` (its comparison with `4711a15` retires at
  the first change to a drawn number, per its docstring).
- The interactive re-weights published draws by `pool_turnout_draws` (MACHINERY.md
  "Per-draw pool turnouts"). Unit-party factors are independent of turnout, so the
  weights keep their form; I did not read the interactive's code and do not assert it is
  unaffected.
- Ward shares: the design changes list shares; how unit parties' ward shares follow was
  not stated and I did not check it.

---

## Verdict

**Unsound as specified.** The diagnosis is right and the record statistics reproduce
exactly. Two things block it: the predicted panel effect uses widths fitted on the
elections it is scored on, and with the widths the design actually specifies, coverage
falls to 0.757 (0.506 at 2011), past its own falsifier (finding 1); and the line that
decides unit treatment depends on a fitted concentration that is a typed fallback at
2011, so it moves COPE, the IFP and the VF+ at 5-17% into a lognormal of width up to
1.06 with no ceiling, and it puts the 2026 forecast's MK 0.06% from switching from a
p99 of 23% to one of 60% (finding 2). With findings 1-2 fixed and 3-9 addressed it
would be sound.

## Where the class line should be

The record does not locate a line at which a class's combined vote becomes more
predictable: the class total is about half as uncertain in log as a member at every line
tried, and the common factor barely changes with the line. On seats the class factor is
inert. So the line should be drawn where the record supports the treatment that does
change outcomes: **a party that stood at the previous local election in this city, with
both that share and its centre below three quotas of the target council (1.1% in
Johannesburg, 3% in Buffalo City).** Below that line, 0 of 368 cases reached 5% at the
next election (203 stood again); in the 3-5 quota band 1 of 15 did. Use that same line
for unit-party eligibility in place of the `A`-based rule, so one line answers the
owner's questions (1) and (2), and parties with no local record (question 3) are never
in it. One quota (the design's choice) is equally consistent with the record for the
class factor alone; three quotas is preferred because it is also the largest band in
which the record shows no rise to 5%, which is the property the owner is asking the
class to have.
