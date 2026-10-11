# 1b. Small parties, the class line, and new entrants: design

Read-only design. Nothing in `src/` or `data/` was written; no model run, no
`compare_history`, no emit. Every figure below was computed in this session from
the files named beside it, with scripts in the session scratchpad (not committed).
Sources: arm E (`data/arms/step11/E/<city>-<year>/`, the batch tree, seed
20261104), the pool specs those runs read (`data/processed/pools_2026.json`,
`data/processed/<city>/pools_<year>.json`; every one has the same `artefact_key`
as its run's `02_pools_artefact.json`, checked at all 25), the raw metro results
through `levels._citywide_and_roster` (LGE 2000-2021, NPE 2004-2024) and
`theta_residual.residuals()` (forward θ residuals, 403 rows, 2006-2021 targets).

"Record" below means real election results. "Arm E" means the model's draws.

---

## 1. Mechanism diagnosis

### 1.1 The within-pool split puts a spike at zero and a long tail on every small cell

`src/montecarlo.py:3374-3376`:

    moved = np.maximum(moved, mean_floor)
    moved = moved / moved.sum()
    split = rng.dirichlet(moved * alpha)

Each member's share of pool `g` is marginally Beta(`a`, `A − a`) with
`a = A·m`, where `m` is the member's post-IPF proportion of the pool and `A` the
pool's concentration. In Gamma form a component with shape `a` has
sd(log) = √trigamma(`a`): 10.1 at `a` = 0.1, 2.2 at 0.5, 1.28 at 1, 0.80 at 2,
0.47 at 5. Relative dispersion therefore grows without bound as a cell shrinks.

**Where `A` comes from.** `pools.dirichlet_alpha` (`src/pools.py:3510-3540`),
called at `src/pools.py:6401`: method of moments, `A + 1 = m(1−m)/Var`, over
metro-year pool splits, **only for members above `ALPHA_MIN_SHARE` = 0.01 of the
pool**, averaged with weights `m`, clipped to [`ALPHA_FLOOR` 1, `ALPHA_CEILING`
200]. `A` is derived; the four selection constants are typed and registered 🔴
(JUDGEMENT-CALLS §F31, never swept). `pool_spec` passes `A × dirichlet_scale`
(`src/montecarlo.py:2830`; scale 1.0). Johannesburg 2026: `A` = 16.31 (Black
African), 20.87 (Coloured), 21.38 (Indian/Asian), 22.06 (White).

**The fit is applied outside its population.** Of the 321 member cells at
Johannesburg 2026, 290 are under 1% of their pool, i.e. below the fit's own
inclusion cut; 307 have `a` < 1, 283 have `a` < 0.1, 160 have `a` < 0.01
(reconstructed with `montecarlo.pool_spec` on arm E's `30_centres.after_shrink`).

| party (JHB 2026) | cell | m (share of pool) | a = A·m |
|---|---|---|---|
| AIC | Black African | 0.0065 | 0.106 |
| ATM | Black African | 0.0074 | 0.121 |
| PAC | Black African | 0.0056 | 0.091 |
| UDM | Black African | 0.0027 | 0.043 |
| ACDP | four pools | 0.0045-0.0160 | 0.07-0.33 |
| DA | Black African | 0.0262 | 0.43 |
| EFF | White | 0.0239 | 0.53 |
| ANC | White | 0.0281 | 0.62 |
| PA | Coloured | 0.8025 | 16.74 |

**Confirmed, with numbers.** AIC alone through Beta(0.106, 16.20), its pool
casting 56.0% of the city's votes: median/mean 0.0085, P(citywide > 2%) 0.054,
P(> 5%) 0.0125, P(> 10%) 0.0015. Arm E's AIC: median 0.008%, mean 0.42%,
75 of 5,000 draws above 5% (0.015), max 25.39%. The level shock alone
(`log_shock`, AIC's width 0.444, ν = 7) gives P(> 5%) ≈ 0 at that centre. The
Dirichlet is the mechanism.

**Against the record.** Parties under 1% of the list vote at the earlier
election of a consecutive metro LGE pair (2006→2011, 2011→2016, 2016→2021), that
stood again (175):

| quantile of later share / earlier share | 5% | 25% | 50% | 75% | 95% | 99% | max | sd log |
|---|---|---|---|---|---|---|---|---|
| record (175 parties) | 0.26 | 0.42 | 0.80 | 1.39 | 4.07 | 7.34 | 17.3 | 0.88 |
| arm E, JHB 2026 draws for the 19 ballot parties under 1% in 2021 | 0.000 | 0.001 | 0.003 | 0.18 | 4.28 | 20.6 | 465 | 3.1 |

The draw has the record's 95th percentile and the wrong shape on both sides: a
median of 0.003 of the previous share where the record's is 0.80, and a 99th
percentile of 20.6 where the record's is 7.3. The mean is conserved by
construction, so the error is entirely shape.

**Why the shape was tolerated.** `theta_residual.py`'s docstring records that
the θ prior's width below 15% is 1.7-3.5x narrower than the measured conditional
dispersion, on the argument that "the within-pool Dirichlet independently
supplies most of the drawn variance". It supplies it as a spike plus a tail. The
two layers together have the right variance and the wrong distribution.

**How far it reaches.** Draws at JHB 2026 (arm E, 5,000) in which a party with
mean list share under 1% exceeds 5%: 853. Split: 595 come from the 26 non-seeded
small parties, 285 from the 46 seeded entrants (some draws have both). Above
10%: 76 and 29.

The same cells exist inside large parties. Contributions to citywide share,
Beta draws at the arm E parameters: DA's Black African cell mean 1.47 points,
median 0.60, 99th percentile 10.07, 99.9th 15.76; EFF's White cell mean 0.78,
p99 4.78; ANC's White cell mean 0.91, p99 5.15. These cells hold 5-8% of the
DA's, ANC's and EFF's mean vote, and they put a long tail on each party's draw.

### 1.2 `PA|Coloured` is a different mechanism

`PA|Coloured` fires in 47.9% of arm E's draws (`41_guards.group_share_tripwire`:
2,397 of 5,000; threshold 0.8123 = record 0.4290 + margin 0.3832). The PA's
Coloured cell has `a` = 16.74, which is not a spike: Beta(16.74, 4.12) has sd
0.085. The cell's **centre** is 0.8025 of the pool, so the threshold sits about
0.1 sd above the mean, and the Beta alone gives P(> 0.8123) = 0.499. The cause
is the level: the PA's centre after the shrink is 6.47% of a centre total
of 1.112, i.e. 5.82% of the city, and 99.4% of its weight sits in a pool casting
7.11% of the votes. The IPF must therefore give it ~80% of every Coloured vote,
against 43% in 2021. `pool_spec`'s own comment (`src/montecarlo.py:2672-2688`)
names this as "a clip on a symptom": the PA's level and its pool vector disagree,
and neither layer knows. D (`w_bye` 0.4) fires more often (60.7%) because the
by-election blend raises the PA's centre.

Nothing in this design touches it. It belongs to the level-versus-pool-vector
question (MODEL-LOG §1.33), not to small-party tails.

---

## 2. The line between an individually modelled party and the class

### 2.1 What the record says about size

Consecutive metro LGE pairs as above (452 party-cases). "Quota" = 1/council
seats at the earlier election (2006 councils taken as 2011's; JHB 260, BUF 100).

| earlier share, in quotas | cases | stood again | reached ≥ 1 quota next | reached ≥ 3 quotas | reached ≥ 5% | sd log ratio (stood) | 95th pct ratio |
|---|---|---|---|---|---|---|---|
| < 0.25 | 158 | 45 | 0.6% | 0% | 0 | 0.81 | 3.78 |
| 0.25-0.5 | 69 | 36 | 7.2% | 2.9% | 0 | 1.06 | 7.12 |
| 0.5-1 | 77 | 65 | 13.0% | 3.9% | 0 | 0.81 | 3.37 |
| 1-2 | 40 | 37 | 27.5% | 2.5% | 0 | 0.74 | 1.96 |
| 2-3 | 24 | 20 | 45.8% | 12.5% | 0 | 0.80 | 2.09 |
| 3-5 | 15 | 14 | 73.3% | 40.0% | 1 (6.7%) | 0.85 | 2.00 |
| 5-10 | 14 | 12 | 78.6% | 64.3% | 5 | 0.88 | 2.22 |
| ≥ 10 | 55 | 54 | 98.2% | 96.4% | 51 | 0.41 | 1.52 |

In share bands the same break: sd log ratio 0.82 (< 0.1%), 0.92, 0.90, 0.71
(0.5-1%), 0.84 (1-2%), 0.93 (2-5%, n = 17), 0.47 (5-15%, n = 9), 0.22 (≥ 15%).
**Above 2% every bin holds 9-20 parties; the location of the break near 5% is
coarse.**

**Class totals are more predictable than members.** For each metro-pair, the
members under line `L` that stood again; their combined share later over earlier:

| L | metro-pairs | median members | sd log(class total ratio) | sd log member ratio | between metro-pair sd | within sd | ρ |
|---|---|---|---|---|---|---|---|
| 0.5% | 20 | 5 | 0.77 | 0.91 | 0.64 | 0.69 | 0.46 |
| 1% | 22 | 7 | 0.65 | 0.88 | 0.51 | 0.71 | 0.34 |
| 2% | 24 | 8 | 0.62 | 0.89 | 0.49 | 0.73 | 0.31 |
| 5% | 24 | 9 | 0.62 | 0.90 | — | — | — |

The common part is the cycle: the class's mean log ratio is −0.97 (2006→2011,
ratio 0.38), −0.39 (2011→2016, 0.68), +0.32 (2016→2021, 1.38) at L = 1%. This is
CLAUDE.md §4's "a level is not necessarily a constant": nothing models how
fragmenting a cycle is.

**Conditioned on the information the model's centres use** (the forward θ
residuals: observed against the centre `theta_prior` gave, which already uses
the preceding national election), most of that common part disappears. Members
grouped by metro-year, national size under the cut:

| national size | n | member residual rms | between metro-year sd | within sd | ρ | mean residual |
|---|---|---|---|---|---|---|
| < 0.2% | 110 | 0.92 | 0.00 | 0.92 | 0.00 | +0.32 |
| < 1% | 250 | 0.80 | 0.17 | 0.77 | 0.04 | +0.17 |
| < 2% | 283 | 0.77 | 0.11 | 0.74 | 0.02 | +0.16 |
| < 5% | 314 | 0.75 | 0.15 | 0.72 | 0.04 | +0.13 |

Class total in the same frame (combined actual over combined centre, per
metro-year, membership by centre < L): sd log 0.35 (L = 1%, 32 metro-years,
median Herfindahl 0.20), 0.31 (2%), 0.32 (3.5%); member residual sd 0.77, 0.75,
0.74. So the class total is about half as uncertain in log as a member, at every
line tried. The mean residual (+0.13 to +0.32) says the centres of small parties
are low on average; that is a level finding and this design preserves it.

### 2.2 Candidates

| candidate | JHB 2026 value | evidence for | evidence against |
|---|---|---|---|
| A. one seat's quota (1/council) | 0.37% | Defined by the thing at stake (a seat); scales with council (BUF 1.0%). Below it, 0.6-13% of parties reached a quota next time. | AIC (centre 0.42%), ATM (0.47%), ACDP, VF+, RISE, IFP, BOSA stay outside, and they carry most of the 595 extreme draws. |
| B. 1% flat | 1% | The population of the problem statement: 0 of 337 (0 of 175 standing again) reached 5%. | A different number of seats in each council (2.7 in JHB, 1 in BUF). RISE, IFP, BOSA (1.2-1.8%) stay in the spiky Dirichlet. |
| C. three quotas | 1.11% | Largest band with no party reaching 5% (0 of 383 below 3 quotas; 1 of 15 at 3-5). | Same parties outside as B at JHB 2026. |
| D. ten quotas / ~5% | 3.7% | Where relative unpredictability changes: sd log 0.85 → 0.41. | n = 9-20 per bin above 2%; would class the PA at a slightly lower centre; knife-edged around real parties. |
| E. mechanism: a party joins the draw-as-a-unit treatment when none of its pool cells has concentration ≥ `a*` | 1.82% in JHB 2026 (largest such party, RISE) | Targets the pathology directly; types no share; computed at draw time from `m` and `A`, so no `pools.py` change and no re-emit. `a*` is pinned by the record (2.3). | Per-pool citywide equivalent varies (`a*`·poolshare/`A`: ≈ 6.9% for a party wholly in JHB's Black African pool, 3.0% White, 0.7% Coloured, 0.4% Indian/Asian, at `a*` = 2). |

At Johannesburg 2026 no party has a centre between 1.82% (RISE) and 5.82% (PA).
D classes every party below 1.82%; B and C leave out RISE, IFP and BOSA. E
differs from every size line in one case: ALJAMAAH (0.88% citywide, about 20% of
the Indian/Asian pool, `a` ≈ 4.3) stays in the Dirichlet, because the fit
measured cells of that size. That is why Line 1 below is per cell: a small party
concentrated in one pool is drawn where the fit applies, a diffuse one is not.

### 2.3 Recommendation: two lines, because there are two questions

The owner's question merges two things the record separates.

**Line 1, the shape line (which parties leave the Dirichlet): candidate E.** It
is applied per cell, to every party alike: a cell with `a = A·m < a*` is not
drawn by the Dirichlet. A party none of whose cells reaches `a*` is drawn as a
unit (section 3). `a*` is where the Dirichlet's per-cell sd(log) reaches the
record's sd(log) for a small party: √trigamma(`a*`) = 0.88 gives `a*` = 1.73
(LGE→LGE record), = 0.76 gives 2.19 (forward θ residual record). **Recommend
`a*` = 2.0**, inside [1.73, 2.19]; it is a judgement call (section 5). `a*` = 1
(the Gamma mode leaves zero; the same reason `ALPHA_FLOOR` = 1 exists) is the
floor: below it every cell is a spike.

**Line 2, the class line (which drawn-as-a-unit parties share one common
factor and are reported as a class total): candidate A, one quota of the target
council, on max(previous LGE share, centre).** Reasons: (i) the record's
diversification and common-factor numbers barely move with `L` (class sd 0.31-0.35
in the conditional frame at every line), so the record does not locate this line
and the owner's own criterion decides it: a class member is a party that on
its own showing cannot win a seat; (ii) it scales with council size; (iii)
max(previous, centre) keeps out a party whose centre has grown past a seat
(the PA 2016→2021 case: 0.17% → 2.96%). Candidate C (three quotas) is the
alternative; the record gives no reason to prefer either beyond the wording of
the owner's question. **Line 2 decides little**: membership adds a common factor
of sd 0.17 and a reported class total. Every class member is still drawn
individually and wins seats on its own share.

Line 1 does the work against Problem 1. Line 2 answers the owner's question.

---

## 3. Specification

All changes in `src/montecarlo.py` (`make_drawer`, `draw_pools`); one new
record writer (3.5). **No change to `src/pools.py`, so no re-emit of the pool
specs.** `src/levels.py` changes only if the width function in 3.5 is put
there instead of in its own module.

### 3.1 Partition, once per run in `make_drawer`

For each pool `g` (from `pool_spec`'s `props` and `alpha`) and member `i`:

- `a_gi = A_g · m_gi` with `m_gi` the floored, renormalised mean already computed
  at `:3374-3375`. That uses the unshocked props; the per-draw IPF moves `m_gi`
  by the level shock, and the partition must not change draw to draw, so it is
  fixed on the unshocked spec.
- **major** if `a_gi ≥ A_STAR`, **minor** otherwise.
- **Exemption by category, not by party: every seeded arrival** (`pool_seeds > 0`,
  the same set `make_drawer` already zeroes the level shock for at
  `:3148-3152`) keeps all its cells in the Dirichlet. Reason in section 4.

Party categories:

- **Dirichlet party**: at least one major cell. Unchanged: pre-IPF level shock
  `sd_for_party` (`level_shock_sd`), major cells in the Dirichlet. Its minor
  cells are held at their post-IPF proportion (no split noise): the party's
  level shock and its major cells already carry its width.
- **Unit party** (not seeded): no major cell. Its pre-IPF `pool_sd_shock` is set
  to 0 (same treatment as seeds, `:3152`); its column target in `capped_targets`
  is therefore unshocked. Its whole width comes from one party-level factor
  `e_i` applied to every one of its cells.
- **Class member**: a unit party with a list vote at the previous local
  election in this city (`prior_pr_share[i] > 0`, the previous-LGE list shares
  `run_model` already holds at `src/montecarlo.py:4878`) and
  max(`prior_pr_share[i]`, centre_i) < 1/council. Class members share a common
  factor. Not `base_city_d`: that is the preceding **national** election's
  citywide shares (`:4512-4513`), plus local-only parties at their LGE share and
  the seeds (`:4882-4887`), so it cannot answer "has a local record".

### 3.2 The draw

Per draw:

    c      ~ Normal(−σ_c²/2, σ_c)            one per run-draw, class members only
    u_i    ~ Normal(−σ_i²/2, σ_i)            per unit party
    e_i    = exp(u_i + c·[i in class])        E[e_i] = 1 exactly

In pool `g`, after the IPF has produced `props` (`:3346`):

    minor_gi = m_gi · e_i      for minor cells of unit parties
             = m_gi            for minor cells of Dirichlet parties
    M_g      = Σ_minor minor_gi
    major    = (1 − M_g) · Dirichlet(A_g · m_gj  over major j and seeded cells)
               / normalised so the Dirichlet's mean is m_gj / Σ_major m_g

The Dirichlet keeps each major cell's own concentration `A_g·m_gj` (the fitted
one); only the minor cells' concentration leaves its total. The composed vector
(minor and major in member order) is what `split_record[name]` stores (`:3380`),
so the group-share tripwire reads the same population, the same shape.

Guard: if `M_g ≥ 1 − ε` (ε = 1e-6), rescale the minor cells to `1 − ε` and count
the event on `ipf_stats` (never silent). At JHB 2026 the minor mass of a pool is
under 0.06, and `e_i` would need to be ~16 for every member at once; the guard
is expected never to fire.

Seat allocation needs no split back. Each unit party's citywide share is
Σ_g (pool votes_g / cast)·m_gi·e_i, drawn individually; it wins a seat in any
draw where that share clears the quota.

### 3.3 Widths

`σ_i` for a unit party with a local record: the **conditional** dispersion of
log θ at its size, as measured by `theta_residual` (residual about the centre
the model would have used, forward-validated): ≈ 0.92 (< 0.2% national),
0.74 (0.2-1%), 0.45 (1-5%), 0.66 (5-15%, n = 14, CI 0.24-1.01). It replaces
both the θ prior width (0.28-0.44 for these parties at JHB 2026) and the
Dirichlet, so nothing is counted twice: the docstring argument that kept the
θ width narrow ("the Dirichlet supplies the rest") no longer applies to a party
the Dirichlet no longer draws. Not the raw LGE→LGE 0.88: the model's centres
already condition on the intervening national election, and in that frame the
member dispersion is 0.75-0.80.

`σ_i` for a unit party with **no local record but a national one** (a first
local election after a national debut): ≈ 1.06 (section 4).

`σ_c` = 0.17: the between-metro-year sd of forward θ residuals for parties
under 1% national. Check that the simulated class total reproduces the record's
conditional class-total sd (0.31-0.35).

Gaussian, not Student-t, for `c` and `u_i`: `exp` of a t has no finite mean for
any ν, so `log_shock` is median-1 and conserves only after the end-of-draw
renormalisation (`:3388-3390`). A mean-1 lognormal makes `E[e_i] = 1` exact,
which the conservation argument below uses.

### 3.4 Conservation

Conditional on the pool votes and on the IPF props (the convention the current
code already uses: `target/total` at `:3388-3390` renormalises at the end):

- minor cell of a unit party: `E[m_gi·e_i] = m_gi`, since `E[e_i] = 1` and `c`,
  `u_i` are independent of everything else;
- minor cell of a Dirichlet party: `m_gi`, exact;
- major cell: `E[(1 − M_g)]·m_gj/Σ_major m_g = (1 − Σ_minor m_g)·m_gj/(1 − Σ_minor m_g) = m_gj`,
  using independence of `M_g` and the Dirichlet;
- the pool sums to one in every draw by construction.

So every party's expected share of every pool equals the proportion asked for.
The only departure is the guard in 3.2, counted.

### 3.5 Where the widths live

`σ_i` by size and `σ_c` must be one definition, generated from the record. The
measurement exists in `src/theta_residual.py`, which is a measurement module the
model does not import (~45 s per call). Specify a record writer on the pattern
of `src/group_share_record.py --emit`: `src/unit_width_record.py --emit` writes
`data/processed/unit_width_record.json` with an artefact key (the θ record's
dependencies), carrying per target year the conditional width per size bin (or a
fitted curve), `σ_c`, the first-timer width, each with its n and cluster CI, from
targets strictly before the target year. `make_drawer` reads it and refuses a
missing or stale record, as `read_group_share_record` does. It is a new shared
artefact: run it in a re-emit window.

### 3.6 What else reads the changed objects

- `split_record` / `group_share_tripwire`: same shapes; population unchanged.
- `draw_pools.level_sd_at_size`: unit parties no longer record a size-rule
  level width; record `σ_i` and its rule instead, for the trace.
- `--run-dir` trace `41_guards`: add the partition (cells, unit parties, class
  members, `a*`) and the guard count.
- `tests/test_reweight` (paired-rerun z for tiny seeded parties) and the drawer
  goldens move: seeded parties' Dirichlet loses the minor cells' concentration
  from its total.
- `individual` parties (in no pool, `:3383-3384`) keep the narrow θ width with a
  t shock. They are outside this change and inconsistent with it; listed in 7.

---

## 4. New entrants

**The record.** Parties absent from the previous LGE in a metro, 2006→2021
pairs (352 cases; the 2000→2006 pair is quarantined at seven metros and used
only for the ID):

| kind | cases | median | 95th pct | 99th pct | max | ≥ 1% | ≥ 5% |
|---|---|---|---|---|---|---|---|
| no national record either | 265 | 0.055% | 1.13% | 5.52% | 18.12% | 15 | 3 (ActionSA ×3, 2021) |
| with a national record from the intervening NPE | 87 | 0.28% | 7.25% | 11.18% | 11.64% | 19 | 7 (EFF ×6; ID CPT 2006 from the quarantined pair) |

Every rise past 5% from under 1% was a party absent at the earlier election.
Per metro-year, the combined share of parties with no national record: median
1.75%, 90th percentile 8.3%, max 19.96% (JHB 2021); the largest took a median
52% of that total.

First local election against the preceding national election in the same
metro, NPE ≥ 0.5%, 2006→2021 pairs (24 cases, 8 parties, COPE ×8 and EFF ×8
supplying 16): median ratio 1.02, sd log 1.06, and bimodal: COPE 2011 0.12-0.28
everywhere; EFF 2016 1.01-1.50; GOOD 2021 0.69-1.07. The ID 2006 (0.65-1.37)
comes from the quarantined 2000→2006 pair and is not in the 24. Forward θ residuals for parties with no θ history and ≥ 5%
national: rms 1.23 (n = 14, effectively COPE and EFF).

**How they sit relative to the class and the limit:**

1. **No class membership and no common factor for any party without a local
   record** (class membership requires one, 3.1). Entrants are not drawn down by
   small-party behaviour.
2. **No range limit of any kind.** This design caps nothing: unit parties get a
   lognormal with no ceiling, and the record's own tail is what it is.
3. **Arrivals from nothing (seeded) keep the Dirichlet spike.** Their record is
   spike-shaped (median 0.055%, max 18%), heavier-tailed than any lognormal of
   width ~0.9, and arm E reproduces the aggregate: seeded total per draw
   p5/p50/p95 0.24/1.85/7.77% against the record's metro-year totals
   (p10/p50/p90) 0.30/1.75/8.30%, largest member's share of the total median 0.55
   against 0.52. Draws with some seeded entrant above 5%: 285 of 5,000 (5.7%);
   the record had a no-record entrant above 5% in 3 of 23 metro-years (13%).
   The entrant tail is if anything lighter than the record, so it must not be
   cut. Removing other parties' minor cells lowers the pool's Dirichlet total by
   their concentration (under 1 of 16-22 at JHB 2026), so seeded marginals move
   little; verify on the arm E spec before the run.
4. **Arrivals with a national record** (MK, RISE, BOSA at 2026) are sized by the
   spine from the national result, as now. Where such a party is a unit party
   (RISE 1.82%, BOSA 1.16% at JHB 2026), its `σ_i` is the first-timer width
   ≈ 1.06, not the established-party table. MK (major cells) stays in the
   Dirichlet; its arm E draw has p1 1.47%, p99 22.74% around a mean of 9.03%
   (≈ 0.59 in log), against a record of 1.06-1.23 that rests on 2-5 parties. That
   is reported, not designed here.

**What this does not fix.** The seat-error audit (1a) puts 126.5 of 363.5
wrong-party seats on parties new at that election: COPE 2011 drawn at 7-16%
against about 1% (≈ 50 seats), ActionSA Johannesburg 2021 6.8% against 18.1%
(20.5). Both are **centre** errors, in opposite directions: a split sized as a
fraction of its parent and an arrival sized from nothing. This design conserves
centres and cannot move either. A wider first-timer width (1.06) puts COPE's
actual share about 2 sd below a 9.9% centre instead of further out, which
changes coverage, not the seat error.

---

## 5. Judgement calls

| call | value | evidence | how to check |
|---|---|---|---|
| `A_STAR` (cell leaves the Dirichlet below it) | 2.0 | √trigamma(a) equals the record's small-party sd(log) at a = 1.73 (LGE→LGE, 0.88) and 2.19 (conditional θ, 0.76); 1.0 is the spike floor | Panel coverage of unit parties at 1.0, 1.73, 2.19 (simulation in 6.2 gives 0.871 at 1.0 and 0.863 at 1.9) |
| class line | one quota of the target council, on max(previous LGE share, centre) | record does not locate it (class sd 0.31-0.35 at every L); owner's criterion "cannot win a seat on its own" | alternative three quotas; compare class-total coverage |
| `σ_c` | 0.17 | between-metro-year sd of forward θ residuals, national < 1% (250 rows, 31 groups) | simulated class-total sd vs the record's 0.31-0.35 |
| unit-party width table | 0.92 / 0.74 / 0.45 / 0.66 by national size bin | `theta_residual` measured conditional widths, cluster CIs in its docstring | regenerate from `unit_width_record`; bins are national size, applied to local centre: check the substitution on the panel |
| first-timer width | 1.06 | 24 metro cases, 8 parties, 16 of them COPE and EFF; bimodal | grows with each cycle; record count printed by the writer |
| Gaussian shocks for unit parties | ν = ∞ | exact mean; t's tail measured indistinguishable for 7 vs 30 (§A18) | one panel run at t ν = 7 |
| guard ε | 1e-6 | numerical | guard count in the trace |

`ALPHA_MIN_SHARE` (0.01 of a pool) stays the fit's selection rule; `A_STAR` is
where the fit's output stops being applied. They should agree on the cells that
matter and do not exactly (a cell at 1-12% of a pool is in the fit and, at
`A_STAR` = 2 with `A` = 16.3, out of the draw). State that next to both.

---

## 6. Predicted effect, against the world and the mechanism

### 6.1 Johannesburg 2026

Simulated at the citywide level from arm E's mean shares (the conserved
centres), widths as in 3.3, σ_c = 0.17, without pool turnout:

- Draws in which a non-seeded party with a 2021 share under 1% exceeds 5%:
  arm E 400 → 0 of 5,000. Record: 0 of 175.
- Draws in which any party with mean share under 1% exceeds 5%: 853 → the
  seeded share, 285, plus a handful from the ~7 non-seeded parties under 1%
  with no 2021 record (first-timer width 1.06; entrants untouched, section 4).
- At the 1% line, 24 parties drawn this way: class total p5/p50/p95 2.81/4.17/6.50%
  against arm E's 1.02/3.47/10.88% for the same parties; members' rate above 2%
  0.0049 per party-draw against 0.0205. Record rate above 2% for parties under
  1%: 0.011 (2 of 175: VF+ Ekurhuleni 0.90 → 3.48%, PA Johannesburg 0.17 →
  2.96%).
- Upper tails of DA, ANC and EFF shorten: their minor cells (DA's Black African
  cell p99 10 points citywide) stop drawing chunks. Mean shares unchanged.
- Mean seats of the parties now drawn as units: arm E 11.87 for the 24 under 1%;
  the change is in their spread; their mean moves only through seat-rounding
  convexity (a spike at zero wastes votes below quota), so expect their mean
  seats to **rise** slightly.
- `PA|Coloured` firing rate: unchanged (1.2).

### 6.2 Panel (24 city-years)

Simulation as above on every city-year (unit parties at `a*` = 1.0, excluding
seeds; 272 party-cases):

- 90% band coverage of actual list shares: arm E 0.934 (3 below, 15 above);
  proposed 0.871 (17 below, 18 above). At `a*` = 1.9: 0.925 → 0.863 (20/20).
  Arm E over-covers because its band is wide in the wrong shape; the proposed
  band is balanced and slightly narrow.
- Draws with an established sub-1% party above 5%: 1,367 → 41 of 24,000 (at
  `a*` = 1.9: 1,559 → 104).
- Panel-mean list MAE: no prediction of a change larger than the three-seed
  spread (0.026 points). The change moves shape, not centres; MAE is a
  mean-share statistic. **It is not predicted to repair item 8's +0.0754**, which
  was a centre effect of entering parties.

**What would falsify it:** panel coverage of unit parties' actual shares below
0.85 (too narrow) or the two-sided miss counts strongly unbalanced; the rate of
established sub-1% parties above 5% not falling by an order of magnitude;
panel-mean list MAE moving by more than 0.05 points (would mean centres moved,
which the conservation argument says cannot happen); the simulated class-total
sd outside the record's 0.31-0.35 by more than its cluster interval.

---

## 7. Risks and couplings

- **Narrower small-party bands.** The shape fix removes width; coverage falls
  from an over-covered 0.93 to about 0.87. If the panel says too narrow, the
  repair is the width table (an estimate), never `A_STAR` tuned to coverage
  (that would be fitting to the model's own output, CLAUDE.md §4).
- **Centres of small parties are low on average** (mean conditional residual
  +0.13 to +0.32; +0.43 in 2021). The spike used to hide this in the tail. With
  the tail gone, under-forecast small parties will show as misses above the
  band. That is a level finding for the level layer.
- **Dirichlet parties with minor cells** lose split noise in those cells; this
  moves the DA, ANC and EFF tails. Forecast-moving, and it moves the top of
  the ballot, which is where the seat error is (1a: ANC/DA 136.5 of 363.5).
- **`individual` parties** (no pool) still draw θ width with a t shock:
  inconsistent with unit parties. Small at present; list for the next round.
- **Partition at the knife edge.** A cell at `a` ≈ 2 switches treatment
  between runs when the centre moves; a party at the class line likewise.
  The class line changes only a σ = 0.17 factor; the cell line changes the
  shape. Report the partition in the trace so a moved forecast can be traced to
  a switched cell.
- **Unpaired runs.** Step 12 found arm pairs with uncorrelated draws. The
  comparison run for this change must share draws with its baseline for every
  stream except the new ones (draw `c`, `u` from a separate generator seeded
  from the run seed), or its panel effect is lost in seed noise.
- **Coupled with `pools.py`: none in this design.** The partition is computed
  from `m` and `A` already in each spec. `ALPHA_MIN_SHARE` and `A_STAR` are a
  pair; changing the former is a `pools.py` change and re-emits every spec.
- **New record writer** (`unit_width_record`) is a shared artefact with its own
  re-emit window (CLAUDE.md §3). It has no importer, so it must be named in
  CLAUDE.md §5's standalone list with an `ENTRY_POINTS` entry in
  `tests/test_standalone_modules.py`, or that test treats it as dead.
- **Out of scope here:** the census date leak (coordinator), the PA level
  versus pool vector, and the sizing of splits and arrivals (COPE, ActionSA).
