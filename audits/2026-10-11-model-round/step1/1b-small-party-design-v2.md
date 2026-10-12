# 1b v2. Small parties, the class line, and new entrants: revised design

Revision of `1b-small-party-design.md` (v1, kept) after the blind review
`step2/2-review-1b.md`. Read-only: nothing in `src/` or `data/` written; no model
run, no `compare_history`, no emit; no sub-delegation. Sources as v1 (arm E
arrays, traces and the pool specs they read, all artefact keys matched; raw metro
LGE 2000-2021 and NPE 2004-2024 through `levels._citywide_and_roster`;
`theta_residual.residuals()` run this session, 403 rows). Scripts in the session
scratchpad, not committed.

**The line, in one sentence.** A party is drawn on its own (outside the pool
split) and counted in the small-party class when it stood at the previous
election in this city (the local one; for a party new to local elections, the
national one) and both that result and its current centre are below three seats'
quotas of the target council (1.11% in Johannesburg, 3% in Buffalo City). On the
record, none of the 438 such cases in the eight metros 2006-2021 reached 5% at
the next local election (368 with a previous local result, 70 with only a
national one); the largest was 4.41% (VF+ Mangaung 2021, from 1.85%).

---

## 0. Answers to the review's 15 findings

| # | finding | verdict | what changed |
|---|---|---|---|
| 1 | widths not out of sample; with forward widths coverage fails | **accepted** | Widths are now forward only: for each target, fitted on earlier targets, measured about the centre the draw uses (§3.3). Recomputed coverage is 0.756 on the panel (2011 0.317, 2016 0.926, 2021 0.866), below v1's falsifier. Stated as the prediction (§6), with the cause: the 2011 small-party centres sat 2.5x above the result (mean log residual −0.91), a level error the Dirichlet spike was covering. |
| 2 | the unit rule depends on fitted `A`; COPE/IFP/VF+ 2011 swept in; MK on the knife edge; overflow guard fires | **accepted** | The `A`-based rule and `A_STAR` are withdrawn entirely, including the cell rule for large parties (§2.3). Unit membership is the size-and-record line above, independent of `A`. COPE 2011 (no previous local or 3q national result), IFP eThekwini 2011, VF+ Tshwane 2011 and MK 2026 are all outside it. Unit cells are drawn on the logit scale so a pool cannot overflow by construction except in a counted tail (P(M ≥ 0.95) = 4.5e-4 at JHB 2026). |
| 3 | stale width table | **accepted** | No table is quoted as a parameter. The docstring correction should carry the current values by national size bin: 0.916 (n 110) / 0.697 (140) / 0.500 (64) / 0.875 (25), and 0.284 (64) at ≥ 15%. The writer generates the widths; the docstring of `theta_residual.py` is corrected in the writer's commit. θ residuals are now used only for the 2011 fallback, restricted by population (`had_record`). |
| 4 | widths measured about `theta_prior`'s centre, not the drawn one; local-only parties have no national size | **accepted** | Widths are residuals of the realised list share about the drawn centre (E[share] from the unshocked `pool_spec`), by target. No national size is needed, so local-route-only parties (UIM, CHANGE, ...) are covered by the same estimator. |
| 5 | 1.06 is a centre error stored as a width | **accepted** | Withdrawn. National debutants below the line get their own forward width about the drawn centre (0.94 for 2026, from 70 cases, §4) and no class common factor. RISE (centre 1.82%) and BOSA (1.16%) are above the Johannesburg line and stay in the Dirichlet; their tails are reported, not changed (§4). |
| 6 | minor-mass and seat arithmetic wrong | **accepted** | Corrected (§3.2, §6.1). Under the new line JHB 2026 unit mass per pool is up to 0.228 (Indian/Asian, ALJAMAAH). List-seat sim: below-quota unit parties fall 5.41 → 4.42 seats; above-quota rise 8.20 → 8.61. |
| 7 | coverage used to check `A_STAR` is tuning | **accepted** | `A_STAR` is gone. No width or line is checked against panel coverage. Coverage appears only as a falsifier of the sim's description of the draw, with the response pre-declared: a coverage miss goes to the level layer, never to the widths (§6.3). |
| 8 | pairing cannot work with a shorter Dirichlet on one `rng` | **accepted** | New factors are specified as keyed streams under `1c-paired-draws-design.md` (§3.6). Under 1c's `split` keys (`pool|party`), removing unit parties from the Dirichlet removes only their own streams. Implementation is sequenced after 1c lands. |
| 9 | top-of-ballot effect overstated | **accepted** | The large-party cell rule is withdrawn (finding 2), so v2 claims no change to DA/ANC/EFF tails beyond the unit mass leaving their pools. The DA's minor-cell tail (p99 36.3 → 32.4 in the reviewer's sim) and its overhang coupling are deferred as a separate item (§7). |
| 10 | counts inconsistent (383 vs 368; 7 vs 6) | **accepted** | Corrected: 368 established cases below three quotas of the target council (203 stood again), 0 reached 5%; entrants with a national record reaching 5% within 2006→2021 pairs: 6 (EFF 2016). |
| 11 | σ_c double-counted; measured on a different membership | **accepted** | Components are now one ANOVA on one population (the unit parties as defined, drawn-centre frame): cycle, between-metro, within; additive, nothing counted twice (§3.3). |
| 12 | the class line is nearly inert | **accepted, used** | The one line now decides unit treatment, which is what changes outcomes. The class common factor is no longer small: in the drawn-centre frame the cycle component is 0.57 in log for 2026 (§3.3). |
| 13 | the proposed 2% tail is below the record point estimate | **accepted** | Under v2 the JHB 2026 rate above 2% per party-draw for the 20 established unit parties is 0.0105 (arm E 0.0254), at the record's 0.011 (2 of 175; 95% interval about 0.14%-4.1%); §6.1. |
| 14 | per-member concentration test not run | **rejected for this design, noted** | v2 no longer depends on `A` for any decision; the test bears on the Dirichlet for parties above the line, which v2 does not change. Listed as an open measurement (§7). |
| 15 | couplings incomplete | **accepted** | Added `test_pool_conservation`, `test_draw_record`, the interactive's pool-turnout reweighting, and the ward path (§7). |

---

## 1. Mechanism diagnosis (unchanged from v1, reproduced by the review)

The tails of established small parties come from the within-pool Dirichlet
(`src/montecarlo.py:3376`, `rng.dirichlet(moved * alpha)`) applied at
concentration `a = A·m` far below 1 to cells outside the population `A` was
fitted on (`pools.dirichlet_alpha`, members ≥ 1% of a pool; §F31). JHB 2026: 290
of 321 cells under 1% of their pool, 307 with `a` < 1. AIC alone: P(> 5%
citywide) 0.0125 from the split, ≈ 1e-4 from the level shock. Record (175 sub-1%
parties standing again) against arm E's draws for the 19 JHB 2026 parties under
1% in 2021: median later/earlier 0.80 against 0.003; p99 7.3 against 20.6; sd log
0.88 against 3.1.

`PA|Coloured` is a level-versus-pool-vector problem (centre at 0.80 of the pool,
threshold 0.81), untouched here.

**`A` is not a stable quantity** (review finding 2): every 2011 spec carries the
fallback 12.0 in all four pools; elsewhere `A` runs 10.6-174.5. This is why no
decision in v2 reads `A`.

---

## 2. The line

### 2.1 Candidates against the record

Consecutive metro LGE pairs 2006→2011, 2011→2016, 2016→2021 (452 cases); line
applied to the earlier share, quota = 1/council of the target (later) council.

| line | cases below | stood again | reached 5% | reached 3 quotas | largest later share |
|---|---|---|---|---|---|
| 1 quota | 304 | 146 | 0 | 5 | 2.96% (PA JHB 2021, from 0.17%) |
| 2 quotas | 344 | 183 | 0 | 6 | 4.41% (VF+ MAN 2021, from 1.85%) |
| **3 quotas** | **368** | **203** | **0** | **9** | **4.41%** |
| 4 quotas | 378 | 212 | 0 | 12 | 4.41% |
| 5 quotas | 383 | 217 | 1 | 15 | 7.79% (VF+ TSH 2021, from 1.97%) |
| 1% flat | 337 | 175 | 0 | 6 | 3.48% (VF+ EKU 2021, from 0.90%) |
| 2% flat | 375 | 210 | 1 | 14 | 7.79% |

Parties new to local elections with a national record (intervening NPE, same
metro), national share below three quotas: 70 cases, 0 reached 5%, 1 reached
three quotas; largest 3.58% (AIC Buffalo City 2011, from 0.49% nationally).
Parties with no record at all (265): 3 reached 5%, all ActionSA 2021.

### 2.2 Recommendation: three quotas, on both the previous result and the centre

- **The property the owner asks of the class**, "combined performance more
  predictable than each one's, and no member given a real chance of a large
  result", holds below the line: 0 of 438 reached 5%.
- **It scales with the council**, which is where seats are decided, unlike a
  flat 1% (2.7 seats in Johannesburg, 1 in Buffalo City).
- **It uses the previous result and the centre.** The centre test keeps out a
  party the model already expects to grow past the line (panel: ACDP Cape Town
  2021 1.13% → centre 2.40%; VF+ Mangaung 2021 1.85% → 3.53%; VF+ Ekurhuleni
  2021, VF+ and DRPA Ekurhuleni 2011). At JHB 2026 it keeps out BOSA (national
  1.02%, centre 1.16%).
- **The record does not separate three quotas from four** (0 of 378 at four).
  Three is chosen because it is the line the review derived independently and
  the smaller of two equally supported values; it is a judgement call (§5).
- **No party without any record is ever in it.** Genuinely new parties are
  where every real rise past 5% from nothing came from.

Membership on the panel: 47 / 68 / 85 established unit parties at 2011 / 2016 /
2021; largest centre 2.60% (UDM Buffalo City 2016, quota 1%). JHB 2026: 20
established (largest ALJAMAAH 0.95%, ACDP 0.76%) and 5 national debutants
(largest UNITED_AFRICANS_TRANSFORMATION 0.24%); unit centre total 4.47%.

### 2.3 What was withdrawn

The per-cell concentration rule (`A_STAR`) for both unit membership and for
holding large parties' minor cells. Reason: `A` is the fallback 12.0 at every
2011 city-year, and the rule moved 5-17% parties into a wide lognormal and left
MK 2026 0.06% from switching (review finding 2). The large parties' minor-cell
tail (DA's Black African cell) remains and is listed in §7.

---

## 3. Specification

All in `src/montecarlo.py` (`make_drawer`, `draw_pools`) plus one record
writer. **No change to `src/pools.py`; no re-emit of the pool specs.**

### 3.1 Partition, once per run

A party `i` is a **unit party** if it is not seeded (`pool_seeds`), it has a
previous result `s_prev` in this city, and max(`s_prev`, `centre_i`) <
`UNIT_LINE_QUOTAS` / council, where:

- `s_prev` = its previous-LGE list share (`prior_pr_share`, held by `run_model`
  at `src/montecarlo.py:4878`) if positive; otherwise its share at the preceding
  national election in this city (`baseline_before_seeds`, `:4866`, which is the
  NPE baseline before seeds and before local-only parties are added);
- `centre_i` = its expected citywide share from the unshocked `pool_spec`
  (Σ_g pool votes_g · props_gi / Σ_g pool votes_g);
- council = the target's council size.

Unit parties are **established** (previous-LGE share > 0) or **debutants**
(national share only). The **class** is all unit parties; its total is reported
per draw. Every other party is drawn exactly as now.

### 3.2 The draw

Per draw `d`:

    c_d    = σ_cyc·z_cyc + σ_btw·z_btw              shared by established unit parties
    x_id   = c_d + σ_wit·z_i      (established)
           = σ_deb·z_i            (debutant)

Unit party `i`'s share of pool `g`, for every pool in which it has a member
weight, on the logit scale:

    share_gid = logistic(logit(m_gi) + κ_gi + x_id)

where `m_gi` is its unshocked `pool_spec` proportion of pool `g` and `κ_gi` is
solved once per run (Gauss-Hermite quadrature, 60 nodes; bisection) so that
E[share_gid] = m_gi under x's total sd. The pool's non-unit members split the
rest:

    M_gd   = Σ_unit share_gid
    others = (1 − M_gd) · Dirichlet(A_g · m_gj over non-unit members j)

`A_g·m_gj` keeps each remaining member's fitted concentration. Unit cells read
the unshocked `m_gi` every draw and never the per-draw IPF output. Unit parties
stay in the IPF with unshocked column targets (`pool_sd_shock` = 0, as seeds at
`:3152`), so the non-unit members' post-IPF props are balanced against them, and
the unit parties' own post-IPF props are discarded. The non-unit members'
`m_gj` are those post-IPF props, renormalised over the non-unit members. `split_record[name]` stores the composed
full-length vector in member order, so the tripwire reads the same population.

**Why the logit scale.** A multiplicative factor on a cell (v1) overflows a pool
whenever a unit party holds a large share of a small pool. Under the new line
that is ALJAMAAH, about 20% of Johannesburg's Indian/Asian pool: the
multiplicative draw put unit mass at or above 1 in 1.8% of draws. On the logit
scale each cell is bounded below 1, and P(M ≥ 0.95) is 4.5e-4 at JHB 2026,
1.5e-4 at Ekurhuleni 2016 and 1e-4 at Mangaung 2016 (sims, 20,000 draws).

**Guard.** If M_gd ≥ 1 − ε (ε = 1e-6), scale the unit cells of that pool to
1 − ε and count the draw on `ipf_stats` and in `41_guards`. Expected rate is
below 5e-4 of draws; a rate above 5e-3 in any run falsifies the mechanism (§6.3).

**Seats.** No split back is needed. A unit party's citywide share is
Σ_g (pool votes_g / cast)·share_gid. It wins a seat in any draw where that share
clears the quota. The ward path is unchanged: `ward_target = pr_target * ratio`
(`:5760-5770`).

### 3.3 Widths: forward, about the drawn centre

**Quantity.** r = log(realised list share / drawn centre) for each unit party at
each backtest city-year, where the drawn centre is the conserved E[share] (arm E
mean shares used here). The centres do not depend on any width, because the draw
conserves them, so computing widths from earlier targets' centres is not
circular.

**Estimator (one ANOVA per population).** Per target year `t`, from city-years
with target < `t` only:

- `σ_cyc` = RMS about zero of the per-cycle mean residuals, the E[k²] reading of
  CLAUDE.md §4: an unknown cycle's mean error is a draw from the past cycles'
  means, sign included;
- `σ_btw` = between-metro component within a cycle;
- `σ_wit` = within-metro member component, pooled weighted by n.

Drawn-centre residuals of established unit parties, arm E:

n counts parties with a realised share above zero (one fewer than §2.2's membership at 2016 and at 2021).

| target | n | cycle mean | between-metro sd | within sd |
|---|---|---|---|---|
| 2011 | 47 | −0.91 | 0.11 | 0.58 |
| 2016 | 67 | −0.24 | 0.13 | 0.61 |
| 2021 | 84 | +0.31 | 0.32 | 0.84 |

Forward widths:

| used for | from | σ_cyc | σ_btw | σ_wit | total |
|---|---|---|---|---|---|
| 2016 | 2011 | 0.91 | 0.11 | 0.58 | 1.08 |
| 2021 | 2011, 2016 | 0.67 | 0.12 | 0.60 | 0.90 |
| 2026 | 2011, 2016, 2021 | 0.57 | 0.21 | 0.71 | 0.93 |

The cycle component is the class's common factor. It matches the record outside
the model: the sub-1% class's LGE→LGE ratio was 0.38, 0.68 and 1.38 by cycle.

Debutants (drawn-centre residuals; n 16 / 13 / 41; means +0.25 / −0.66 / −0.15;
RMS 0.92 / 1.61 / 0.61): one total width, no common factor. Their cycle means
differ in sign from the established class in two of three cycles. Forward
widths: 2016 0.92, 2021 1.27, 2026 0.94.

**2011 has no earlier backtest**, so no drawn-centre record exists for it. The
fallback is the forward θ residual of target 2006, by population: 0.27 for
parties with θ history (n 37), 0.48 without (n 27). That residual is measured
about `theta_prior`'s centre, not the drawn one, and is declared as such (§5).
The consequence is in §6.2.

**Is this estimation or tuning?** It is the realised dispersion of the vote
about a fixed, width-independent point, i.e. the forecast-error variance. It
never reads the model's predicted width and fits no realised-over-predicted
ratio. Its dependence on the centres is real: any change to the level layer
changes the residuals, so the writer's artefact key includes the centres' inputs.

Gaussian factors (not Student-t): the logit-scale construction needs a known
distribution for κ, and `exp` of a t has no finite mean.

### 3.4 Conservation

Conditional on pool votes and IPF props, E[share_gid] = m_gi exactly by κ.
The non-unit cells get E[(1 − M)]·m_gj / Σ_non-unit m_g = m_gj, because M is
independent of the Dirichlet. Every pool sums to one in every draw, except
counted guard draws.

### 3.5 Where the widths live

The widths come from a new writer, `src/unit_width_record.py --emit`, which
writes `data/processed/unit_width_record.json`. Per target year it holds the
forward components (`σ_cyc`, `σ_btw`, `σ_wit`, `σ_deb`) with n and per-cycle
means, the fallback rows for a target with no earlier backtest, and an artefact
key over the centres' inputs. It needs the earlier targets' drawn centres. It
computes them through the same functions `run_model` uses up to the unshocked
`pool_spec`, with no draws; one definition, so the writer imports rather than
re-implements. `make_drawer` reads the record and refuses a missing or stale one
(pattern: `read_group_share_record`). Couplings:
- run it in a re-emit window;
- name it in CLAUDE.md §5 with an `ENTRY_POINTS` entry in
  `tests/test_standalone_modules.py`;
- correct `theta_residual.py`'s docstring table (now 403 rows) in the same commit.

### 3.6 Random streams (under `1c-paired-draws-design.md`)

New stages in 1c's §2.3 table, primitives only:

| stage | name | kind, per draw | transform |
|---|---|---|---|
| `unit.cycle` | `""` | z, 1 | `σ_cyc·z` |
| `unit.metro` | `""` | z, 1 | `σ_btw·z` |
| `unit.member` | party code | z, 1 | `σ_wit·z` or `σ_deb·z` |

A unit party removed from the Dirichlet loses its `split` stream (`pool|party`)
and reads `unit.member` instead. Every other member's `split` primitives stay
bit-identical, and every non-unit party's draws stay paired with a baseline
apart from the normalisation by (1 − M). The two citywide stages are city-year
keyed by 1c's root key, so they are independent across the panel, as 1c
requires. Sequenced after 1c is implemented; before that the change cannot be
compared paired (MODEL-LOG §1.296).

---

## 4. New entrants

Record (2006→2021 pairs):

| kind | cases | median | 95th pct | max | ≥ 5% |
|---|---|---|---|---|---|
| no record at all | 265 | 0.055% | 1.13% | 18.12% | 3 (ActionSA ×3, 2021) |
| national record, national share < 3 quotas | 70 | — | — | 3.58% | 0 |
| national record, all | 87 | 0.28% | 7.25% | 11.64% | 6 (EFF 2016) |

- **Parties with no record** (seeded arrivals) are never unit parties, never
  class members and never bounded. They keep the Dirichlet spike, whose aggregate
  matches the record: seeded total p5/p50/p95 0.24/1.85/7.77% against the record's
  metro-year p10/p50/p90 0.30/1.75/8.30%. The tail is lighter than the record's:
  a seed above 5% in 5.7% of draws, against a no-record party above 5% in 3 of 23
  metro-years. Not cut.
- **National debutants below the line** (5 at JHB 2026, all ≤ 0.24%) are unit
  parties with the debutant width (0.94 for 2026) and no common factor.
- **National debutants above the line** (MK, RISE; BOSA by its centre) are drawn
  as now. Their tails are outside their record, and this design does not change
  them:
  - RISE: national 1.56%, centre 1.82%; arm E p99 9.95%, max 18.36%.
  - BOSA: national 1.02%; arm E p99 8.35%, max 23.49%.
  - The record's largest first-local/national ratio is 2.99 for any party
    (10.9 below three quotas: AIC Buffalo City 2011), and 1.50 for any party at
    2% or more nationally.
  - Extending the unit draw to them needs a width the record can carry. It has 8
    parties above 0.5% nationally, 16 of 24 cases from COPE and EFF, bimodal. That
    is an owner decision, not specified here.
- **What this cannot fix.** Audit 1a's 126.5 wrong-party seats on new parties
  (COPE 2011 too high, ActionSA 2021 too low) are centre errors.

---

## 5. Judgement calls

| call | value | evidence | how to check |
|---|---|---|---|
| `UNIT_LINE_QUOTAS` | 3 | 0 of 368 established and 0 of 70 national-debutant cases below it reached 5%; 4 quotas also 0 of 378; 5 quotas 1 of 383 | the writer reprints the table for every new cycle; a rise past 5% from below the line is a defect report |
| previous result for a party new to local elections | its preceding-NPE share in this city | 70 cases, 0 to 5% | same table |
| centre included in the test | max(previous, centre) | keeps out parties the model expects past the line (5 panel cases, BOSA 2026) | list the excluded parties in the trace |
| `σ_cyc` estimator | RMS of prior cycle means about zero | CLAUDE.md §4 E[k²]; per-cycle means −0.91, −0.24, +0.31; record class ratios 0.38/0.68/1.38 | the alternative (sd about the mean) gives a narrower width: report both in the writer |
| widths (2026) | σ_cyc 0.57, σ_btw 0.21, σ_wit 0.71; σ_deb 0.94 | forward ANOVA, §3.3 | regenerated by the writer; never adjusted to coverage |
| fallback at a target with no earlier backtest | forward θ residual of the previous target, by population (0.27 / 0.48 for 2011) | the only out-of-sample record; frame differs | 2011 scores labelled "width not testable" |
| no common factor for debutants | — | cycle means of opposite sign in 2 of 3 cycles | recheck each cycle |
| logit-scale cell draw | — | multiplicative overflowed 1.8% of JHB 2026 draws | guard count |
| Gaussian factors | ν = ∞ | exact κ; t-tail unresolvable on this panel (§A18) | — |
| no range cap | — | an out-of-sample record cap would have been 0.92x for 2016 and 3.99x for 2021, and 2021 broke it (PA Johannesburg 17.3x; class 3.57x against a prior maximum of 1.18x) | — |
| guard ε, falsifying rate | 1e-6; 5e-3 of draws | numerical; sims below 5e-4 | `41_guards` |

---

## 6. Predictions and falsifiers

Citywide simulation: arm E mean shares as centres, logit-scale unit draws, other
parties from arm E's draws scaled by (1 − unit total); no pool turnout, no ward
ballot. Seats by largest remainder on list shares only, which is not the model's
ward-plus-overhang allocation; the direction holds, the size will differ.

### 6.1 Johannesburg 2026 (5,000 draws)

| quantity | arm E | v2 |
|---|---|---|
| draws with an established unit party above 5% | 473 | 39 |
| rate above 2% per party-draw, established unit parties | 0.0254 | 0.0105 (record 0.011, 95% interval 0.14%-4.1%) |
| draws with any party of mean share < 1% above 5% | 853 | 389 (seeds 285; rest national debutants and parties above the line) |
| unit-class total p5 / p50 / p95 | 1.41 / 4.21 / 11.82% | 1.86 / 4.36 / 10.70% |
| list seats, 20 unit parties below one quota | 5.41 | 4.42 |
| list seats, 5 unit parties above one quota | 8.20 | 8.61 |
| ALJAMAAH p99 / max | 2.67 / 8.55% | 3.02 / 4.06% |
| ACDP p99 / max | 5.88 / 16.41% | 4.12 / 13.40% |
| ATM p99 / max | 6.41 / 14.57% | 2.58 / 10.21% |

The class total stays wide because the cycle factor is wide. That is the
record's statement about how much small parties move together between local
elections.

The 39 draws come from the common factor lifting ACDP or ALJAMAAH. That is 39
of 100,000 party-draws for 20 parties, inside the record's 0 of 438 (95% upper
bound about 0.7%).

Seats of sub-quota members fall: the seat curve is flat below the remainder
threshold, so mass moved from the tail to the centre wins fewer seats.

### 6.2 Panel (24 city-years), out of sample

90% band coverage of realised list shares, unit parties (established and
debutants), forward widths, 2011 on the declared fallback:

| | n | v2 | arm E (same parties) |
|---|---|---|---|
| 2011 | 63 | 0.317 | |
| 2016 | 81 | 0.926 | |
| 2021 | 127 | 0.866 | |
| panel | 271 | **0.756** (44 below, 22 above) | 0.926 |

This fails v1's falsifier (0.85). The 2011 failure is a level finding, not a
width finding: established unit parties at 2011 came in at a median 0.42 of their
drawn centre (mean log −0.91). Arm E covered those results only because its
spike at zero puts mass there. With a width honest about the prior record,
2011's centres are exposed as too high. The review notes a related level effect
at 2026: after-shrink centres of small parties sit 1.29-1.35x the spine
(`compress_levels` lifts small parties by construction). Both belong to the
level layer.

Draws with an established unit party (three-quota line) above 5%: 2,028 of
24,000 in arm E. Not simulated per city-year under v2; the falsifier is stated
for JHB 2026 only (§6.3).

Panel-mean list MAE: no change larger than the three-seed spread (0.026 points)
is predicted; centres are conserved. Item 8's +0.0754 is not predicted to move.

### 6.3 Falsifiers, and the pre-declared response

Each falsifier is a test of whether the implementation matches this
description. None is a tuning target.

1. Panel-mean list MAE moves by more than 0.05 points: centres moved, which
   §3.4 says cannot happen.
2. Any unit party's mean drawn share differs from its centre by more than 5%
   relative at 5,000 draws (about three Monte Carlo standard errors at total
   width 0.93, whose relative sd of the share is about 1.1): conservation broken.
3. JHB 2026 draws with an established unit party above 5% exceed 1/10 of arm E's
   (47).
4. Per-year coverage in the real run differs from §6.2 by more than two binomial
   standard errors (2011 ±0.12, 2016 ±0.06, 2021 ±0.06): the sim misdescribes the
   draw.
5. The guard fires in more than 5e-3 of any run's draws.

**Response to low coverage, declared now:** the widths are re-estimated only
from the record (a new cycle or a corrected centre), never adjusted to coverage.
A coverage miss concentrated in one cycle's sign goes to the level layer as a
defect report.

---

## 7. Risks and couplings

- **Coverage falls, honestly.** 0.926 → about 0.76 on the panel. The owner should
  see this before the run: the old band covered small-party results by a shape
  that also produced the 853 extreme draws.
- **Level defects exposed.** 2011 small-party centres at about 2.5x the result;
  2026 small-party centres lifted about 1.3x by the shrink. Report to the level
  layer; not fixed here.
- **Deferred: large parties' minor cells.** DA's Black African cell
  (`a` 0.43) still gives the DA a long upper tail (reviewer: p99 36.3 → 32.4 if
  held). This feeds overhang. A separate item, needing a rule that does not read
  `A` (finding 2).
- **Open measurement (finding 14).** Per-member concentration from the fitting
  splits, by member size, would test the Dirichlet for parties above the line.
- **Tests that move:**
  - `test_pool_conservation` (asserts Dirichlet means; extend to unit cells via κ);
  - `test_draw_record` (retires at the first drawn-number change, per its
    docstring);
  - `test_reweight`, the drawer goldens and `test_group_share_tripwire`
    (population unchanged, values moved).
- **Interactive.** It reweights published draws by `pool_turnout_draws`. Unit
  factors are independent of turnout, so the weights keep their form. The
  interactive's code was not read.
- **Ward shares** follow `pr_target` through `ward_target = pr_target * ratio`
  (`:5770`). The path is unchanged; I checked the call site only.
- **Knife edge at the line.** A party at three quotas switches treatment. The
  trace lists every party within ±10% of the line, and the pre-registration names
  them (JHB 2026: BOSA at centre 1.16% against 1.11%; ALJAMAAH 0.95%).
- **Pairing** depends on 1c being implemented first (§3.6).
- **New artefact** `unit_width_record.json`, re-emitted when the centres' inputs
  change (its key).
- **Out of scope:** census date leak; PA level versus pool vector; sizing of
  splits and arrivals; the range of national debutants above the line.
