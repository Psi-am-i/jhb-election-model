# 1e. The `compress_levels` lift: design

Answers `1b-level-lift-defect.md`; couples to `1b-small-party-design-v3.md` at
the owner's flat 1% line (`PLAN.md`, owner decisions 2026-10-11). Read-only:
nothing in `src/` or `data/` written; no model run, no `compare_history`, no
emit; no sub-delegation.

**Sources.** Arm E (`data/arms/step11/E/*/`): `30_centres` (`before_shrink`,
`after_shrink`), `arrays.npz`, `meta.json`, `result.json`. Realised list shares
from the raw-results cache the v2/v3 work built (`rec.json`), cross-checked
against the `votes` column of `result.json`. `pool_spec` centres recomputed by
calling `montecarlo.pool_spec` on both centre vectors with the specs on disk;
the after-shrink result reproduces v3's `pool_spec` centres to 1e-16. Scripts:
`<scratchpad>/levellift/a1.py`-`a12.py`.

**Two stages, named every time.** *Normalised centre* = a `30_centres` vector
divided by its own total (its total is 0.97-1.18, not 1). *`pool_spec`
centre* = Σ_g votes_g·props_gi / Σ_g votes_g, the centre the draw conserves.
The two agree to 0.02 points at Johannesburg 2026 (table §5.1).

---

## For the owner

1. **The lift is real.** `compress_levels` multiplies every party below 1% by
   1.36-1.45 (log +0.30 to +0.37), in every one of the 25 city-years.
2. **Against real results it is not a demonstrated bias.** For established
   parties below 1%, the realised total divided by the centre total is
   0.44 / 0.82 / 1.64 with the lift and 0.60 / 1.14 / 2.23 without, at
   2011 / 2016 / 2021. Each version is too high in some cycles and too low in
   others. The difference between the cycles is about four times the lift, and
   three cycles cannot tell the two versions apart.
3. **The freed mass cannot go anywhere else without a measured cost.** Any
   redistribution that does not lift small parties sends the mass to the middle
   or the top of the ballot. Both have been measured, and both scored worse
   (§2.2).
4. **So the real question is the shrink itself.** The shrink's premise is that
   the top is over-forecast and the middle under-forecast. That holds in 2021,
   holds weakly in 2016, and is reversed in 2011, the one cycle never used to
   choose 0.35 and never scored with it. One party drives the 2011 reversal:
   COPE, over-forecast by 5-13 points in every metro, while the ANC and DA were
   under-forecast and the shrink cut them further (§1.5). Offline, the shrink
   makes 2011 worse by 1.5 points of list MAE (share-weighted, mean of 8
   metros) and by 33 wrong-party seats (list-only largest-remainder proxy, sum
   of 8). It makes 2016 and 2021 better by 0.8 and 0.5 points and by 8 and 22
   seats on the same proxy. Summed over the three cycles that is roughly zero.
5. **Under v3's current width estimator, removing the lift lowers coverage.**
   The 1b small-party class's 90% coverage on the testable years falls from
   0.878 to 0.808, with 25 parties above the band in 2021 against 15 (offline,
   §4.3). Part of the fall comes from narrower forward widths when the lift is
   gone. Centring and width cannot be separated until σ_cyc is defined about
   the draw's own mean (§3.3).
6. **Recommendation: keep 0.35 this round, and measure removal as a paired arm
   in the canonical run.** Removal needs only a scenario override and no code
   change. The owner decides on the result split by cycle. The specification
   for removal is in §2.5 if it is chosen. In either case, the two places that
   say the shrink ships switched off must be corrected (§1.6).

---

## 1. What `compress_levels` does, and where 0.35 came from

### 1.1 Mechanism (code)

`montecarlo.compress_levels` (`src/montecarlo.py:2541-2599`) runs once, on the
finished centre vector, inside `blended_centres` (call at `:2502`, trace
`30_centres` at `:2503-2517`). Each party keeps `1 − c·s/(s+h)` of its level `s`
(`c` = `level_shrink` = 0.35, `h` = `level_shrink_scale` = 0.04, `DEFAULTS`
`:409-410`). The function then scales everything by `total/freed` (`:2596-2598`).
A party far below `h` keeps about all of its level and then receives the whole
scale factor.

Two properties follow from the code. Neither is documented.

- **`s` is the un-normalised level.** The pull reads `s/(s+h)` on a vector that
  sums to 0.97-1.18 (MODEL-LOG §1.230: "Σ centres is 0.9952 / 1.0567 /
  1.1168" at 2011 / 2016 / 2021). The effective `h` therefore varies by city-year
  with that total.
- **The total it conserves is discarded at the next stage.** `pool_spec`
  divides by `want.sum()` (`pool_spec`, the "FEASIBILITY FIRST" block). The
  ratio after/before is the same whether or not both vectors are normalised.

### 1.2 Re-derived lift (measured, `a1.py`)

`compress_levels` re-run on each `before_shrink` reproduces `after_shrink`
exactly in all 25 runs.

| cycle | F/T (share of the total freed) | scale factor `total/freed` | mean log(after/before), parties below 1% normalised |
|---|---|---|---|
| 2011 (8 metros) | 0.295-0.304 | 1.419-1.438 | +0.317 to +0.341 |
| 2016 (8) | 0.298-0.311 | 1.425-1.452 | +0.323 to +0.362 |
| 2021 (8) | 0.284-0.297 | 1.397-1.423 | +0.321 to +0.343 |
| JHB 2026 | 0.262 | 1.356 | +0.296 (74 parties) |

The defect note's 1.29-1.40 and 1.20-1.34 are residual-based or class-mean
figures. The factor applied to a party at the bottom of the ballot is the
scale factor in this table.

### 1.3 What it is meant to do

From the docstring (`:2542-2584`) and MODEL-LOG §1.44 (2026-08-17): ranks 1-3
were over-forecast by +32.30pp and ranks 4-12 under-forecast by −36.20pp
(nine city-years, cached mean vectors). That was read as one fault, "a share
vector too widely spread", to be fixed by shrinking toward its centre. The
docstring records the cost: ranks 13+ go from +0.78pp to +8.68pp (offline
screen), "under 1pp per city-year in the model".

### 1.4 Was 0.35 chosen on backtest outcomes? Yes.

From the code comments and the register:

- **The value.** It was fitted to minimise summed absolute list-share error
  against realised results. On Johannesburg 2016 alone the fit gives 0.375.
  Leave-one-city-year-out over nine city-years gives 0.350, and those nine are
  JHB 2016 plus the eight 2021 metros (§1.44; `backtest.FITTED_ON_UNINSTRUMENTED["level_shrink"]`,
  `src/backtest.py:388-393`). The targets fitted are targets the harness now
  scores.
- **The form.** Four families were screened against the same nine. §1.44,
  `ITERATING.md` rule 11 and JUDGEMENT-CALLS §A23 record this as an L1 leak.
- **`h` = 0.04** is the optimum of a sweep on the same nine (§F20).
- **The model it was fitted on no longer exists.** §1.94 (2026-08-25) re-read
  it on 16 city-years: +2 coherent seats in 2016 (five ties) and +50 in 2021,
  "a 2021 effect".

**2011 has never been in any fit or any score of the shrink.** It is the only
out-of-sample cycle there is.

### 1.5 The shrink's premise by cycle, on 24 city-years (measured, offline, `a2.py`/`a4.py`/`a6.py`)

Normalised centres before and after the shrink, scored against realised list
shares. Rank bands use the pre-shrink order, so they are fixed before the
result is known. Signed values are summed over the 8 metros of the cycle.

| cycle | ranks 1-3 signed pp, before → after | ranks 4-12 signed pp, before → after | list MAE (share-weighted, mean of 8 metros, pp), before → after | wrong-party seats (list-only largest remainder, sum of 8), before → after |
|---|---|---|---|---|
| 2011 | −1.92 → −15.61 | +12.77 → +25.97 | 3.601 → 5.096 | 131 → 164 |
| 2016 | +10.31 → −4.97 | −6.20 → +5.74 | 1.885 → 1.081 | 79 → 71 |
| 2021 | +67.45 → +45.74 | −44.70 → −29.79 | 3.451 → 2.941 | 164 → 142 |
| mean of three cycles | | | 2.979 → 3.039 | 374 → 377 (sum) |

How far the screen can be trusted, stated where it is used: the after-shrink
column tracks arm E's own `pr_mae` within 0.07pp (2016 and 2021) and 0.8pp
(2011). It is weakest in the cycle where the effect is largest. The seat proxy
is list-only largest remainder, not the model's ward-plus-overhang allocation.
It is the same kind of screen §1.44 used, and §1.44 validated its own version
at 306 against 308.

**Result.** The premise holds in 2021, holds weakly in 2016, and is reversed in
2011, where the shrink pushes both bands the wrong way.

**The 2011 cases (`a12.py`).** Before the shrink, COPE ranks in the top three in
7 of 8 metros and in the top twelve in eThekwini. It is over-forecast by 4.8 to
12.9 points in all eight. The ANC and DA are under-forecast in almost every
metro, by up to 5.3 and 7.8 points. The top band's −1.92 is COPE's over-forecast
cancelling the two large parties' under-forecast. The shrink takes from the ANC
and DA, which were already short, and lifts COPE by less than it cuts them.

The other 2011 errors are small:
- VF+ in Tshwane and Mangaung (+3.6 and +3.0 points after the shrink);
- IFP in Johannesburg and Ekurhuleni (about +1);
- AIC in Buffalo City (−2.9);
- the NFP, absent from the centres, which took 4.48% in eThekwini.

So the 2011 cost is mainly one party's collapse after its split, which the
level layer missed. Two readings fit:

- **Consolidation.** The shrink helps when the ballot fragments (2021) and
  hurts when it consolidates (2011). This is §1.94's fragmentation reading
  (task A3).
- **A COPE effect.** The cost belongs to one party's mis-centred level.

One cycle with one dominant case cannot separate them. Removal improving the
2011 metros other than COPE's largest would favour the first reading.

v3 also declared the 2011 level layer the weakest in the panel: local-route
collapse, spine residual −0.92 on 12 parties, and fallback concentration on
every 2011 spec. 2011 is the only out-of-sample cycle, but it is not a clean
one.

### 1.6 Text that is wrong today, whatever is decided

- `compress_levels` docstring, last line: "Off by default (`level_shrink = 0.0`
  is exactly the identity)". `DEFAULTS` ships 0.35.
- `tests/test_chain.py::test_the_level_shrink_is_exactly_the_identity_when_it_is_off`
  docstring: "`level_shrink` ships at 0.0". The assertion, that 0.0 is the
  identity, is correct; the docstring is not.
- JUDGEMENT-CALLS §A23 "Plain": "The smallest parties are now forecast slightly
  too high". Measured on the current model (§3.2), parties ranked 13+ are
  under-forecast in total in every cycle, with or without the lift.

---

## 2. The correction

### 2.1 Where the freed mass can go (algebra, argued)

Return the freed mass F to party i with weight g(sᵢ). Party i's relative lift
is then F·g(sᵢ)/(sᵢ·Σg). For no lift at the bottom of the ballot, g(s)/s must
go to 0 as s goes to 0. The weight then falls on mid-sized or large parties.
There are three families:

- **Uniform** (g ∝ kept level): the lift.
- **Middle-weighted** (g ∝ s·w(1−w), or "to predicted ranks 4-12"): the mass
  goes to the parties in the ramp's middle.
- **Top-weighted** (any g with g/s increasing, such as a receiver floor
  q/(q+floor), or exempting a class below a line): the mass goes back to
  ranks 1-3.

Each family has a measurement against it (§2.2). A fourth option, shrinking on
a log or logit scale, needs a normalising constant. That constant is a uniform
multiplicative factor, and it lifts the bottom of the ballot in the same way.

### 2.2 Rejected redistributions

| candidate | family | measurement that rejected it |
|---|---|---|
| to predicted ranks 4-12 | middle | §1.44 offline: PR error 139.32 against 134.91 uniform, seats 284 against 272 |
| below the top 3; below the top 3 weighted by room | middle / top | §1.44: 137.12 / 142.58 against 134.91; seats 280 / 288 against 272 |
| soft receiver floor q/(q+floor), floor 0.001-0.005, `c` and `h` fixed | top | §1.54, four metros 2021, 600 draws: coherent seats 168 → 182-190; ranks 1-3 +12.94 → +15.53-17.93. The lever was deleted |
| return ∝ s·w·(1−w), using the shrink's own `h` (`a4.py`) | middle | offline, 24 city-years: list MAE 4.956 against 3.039 uniform and 2.979 none; worse in every cycle (2011 8.28, 2016 3.17, 2021 3.42) |
| exempt the 1% class from shrink and return (`a4.py`) | top (hard line) | offline 3.020 against 3.039, which is inside the screen's error. It is the hard-threshold version of §1.54's floor, with a 21% jump in centre at the line (0.99% → ×1.00, 1.01% → ×~1.21). Not proposed: choosing it because it screens 0.02 better would be choosing on the scoreboard |

### 2.3 Can 0.35 be re-derived? Not from the world.

- **No property of the world fixes `c`.** The size effect the world does show,
  regression of large parties between elections, is already in the spine
  through θ's `size_centre` (JUDGEMENT-CALLS §A26). The shrink corrects what
  the model leaves over after that.
- **Any value fitted to |model centre − realised| is a calibration of the
  model's own output.** CLAUDE.md §4 counts that as tuning: "fitting to a ratio
  defined against our own output".
- **A forward fit per target** (2011 → `c` for 2016, and so on) would be L0 by
  `ITERATING.md` rule 11, but it has three clusters for two parameters. The
  2011 → 2016 step would choose `c` = 0, because 2011 is reversed.
- **Re-sweeping 0.35 on the current panel** would choose on the scoreboard.

The honest set of choices is therefore {keep 0.35, declared as a judgement call
with its 2011 record; remove}. A third value needs a derivation that does not
exist.

### 2.4 Recommendation: Option K (keep), with removal measured as a paired arm

**Why keep in this round** (argued from the measurements above):

- The lift is not shown to be a bias (§3).
- Under v3's width estimator, removing it lowers the 1b class's coverage from
  0.878 to 0.808 (§4.3). That is a comparison of two centre-and-width pairs,
  not of two centres, so the recommendation does not rest on it.
- Removing the shrink is a 2011-for-2016+2021 trade. It is predicted to fail
  Key 1 (net losses in 2016 and 2021).
- Keeping it is also predicted to fail Key 1 on 24 city-years (net loss in
  2011). Key 1 cannot decide between them. Under CLAUDE.md §4.4 that
  disagreement goes to the owner unsplit, with a measurement.

**Option K edits, by function. No number changes.**

| place | edit |
|---|---|
| `montecarlo.compress_levels` docstring | Delete "Off by default". State that it ships at `DEFAULTS["level_shrink"]`. State the scale factor at the bottom of the ballot (it multiplies every party far below `h` by `total/freed`, 1.36-1.45 on the panel, by pointer to this file). State that `s` is un-normalised. Replace the "three targeted redistributions" paragraph with a pointer to §2.2 here. Name 2011 as unscored. |
| `tests/test_chain.py::test_the_level_shrink_is_exactly_the_identity_when_it_is_off` | Docstring only: it guards the 0.0 path used by scenario overrides, not the shipped default |
| `MACHINERY.md`, "The level shrink" | Add the bottom-of-ballot factor and the un-normalised `s` |
| `JUDGEMENT-CALLS.md` §A23 | Correct "Plain": the tail is under-forecast in total. After the canonical run, add the 2011 result with its measurement, and the cluster count (3) beside the fit |
| `MODEL-LOG.md` | Append: lift re-derived; small-party bias by cycle (§3); premise reversed in 2011; paired result |

### 2.5 Option R (remove): specification, if the owner chooses it after the measurement

**Step 1: measure without code change.** Run the canonical arm with scenario
override `level_shrink = 0.0`. The identity at 0.0 is asserted by the test
above, and `compress_levels` returns its input unchanged at that value.

**Step 2: if removal is adopted, delete the lever** (precedent: §1.54 and
`first_local_election`, where a lever with a negative result was deleted
rather than left inert). Edits, by function:

| function / place | edit |
|---|---|
| `montecarlo.DEFAULTS` | Delete `level_shrink`, `level_shrink_scale` and their comment block |
| `montecarlo.compress_levels` | Delete |
| `montecarlo.blended_centres` | Delete `before = dict(centres)` and the `compress_levels` call. In the F35 comment and its assertion message, replace "`compress_levels` renormalises over this membership" with `pool_spec`'s normalisation (`want / want.sum()`), which still rescales every party when a key is added, so the assertion keeps its reason |
| `montecarlo.blended_centres`, `30_centres` trace | Write `centres` once; drop `before_shrink`, `after_shrink`, `ratio`, `level_shrink`, `level_shrink_scale` (the readers are listed in §6) |
| `backtest.FITTED_ON_UNINSTRUMENTED` | Delete both entries. `test_levers_are_live::test_every_defaults_key_declares_whether_it_read_an_election` enforces it in both directions |
| `compare_history` comments (`:1172`, `:1783`) | Remove the `compress_levels` / `level_shrink` mentions |
| JUDGEMENT-CALLS §A23, §F20, summary rows, range table; JUDGEMENT-SHEET; MODEL-INDEX; MACHINERY section | Retire the rows; MACHINERY records the removal and points to the MODEL-LOG entry |
| `PUBLISHING-BACKLOG.md:142` | Presentation only; flag for the owner and do not edit with the model |

**No collision with the paired-streams work.** None of these functions is
`make_drawer` or `draw_pools`, and none consumes a random number.
`compress_levels` and `blended_centres` are deterministic and run before the
drawer is built.

---

## 3. Are small-party centres biased? The record, out of sample

### 3.1 The class below 1% (measured, `a3.py`)

The class is v3's definition at the owner's 1% line: not seeded; previous LGE
result (established) or previous NPE result (debutant); both that result and
the normalised centre below 1%. Realised = list share at the target.

| class | cycle | n | realised total / centre total, before → after | mean log(realised/centre), realised > 0, before → after |
|---|---|---|---|---|
| established | 2011 | 36 | 0.602 → 0.435 | −0.640 → −0.971 |
| established | 2016 | 60 | 1.140 → 0.818 | +0.165 → −0.178 |
| established | 2021 | 79 | 2.229 → 1.635 | +0.812 → +0.485 |
| debutant | 2011 | 16 | 2.876 → 2.061 | +0.648 → +0.305 |
| debutant | 2016 | 13 | 1.178 → 0.852 | −0.217 → −0.556 |
| debutant | 2021 | 41 | 1.378 → 1.004 | +0.267 → −0.062 |

For established parties, the mean of the three cycles' log total-ratios is
+0.142 before and −0.181 after. The standard deviation across cycles is 0.66,
which gives a standard error of 0.38 on a three-cycle mean.

- **With the lift**, centres are high by 0.18 in log on the cycle average.
  They are high in 2011 and 2016 and low in 2021.
- **Without it**, centres are low by 0.14. They are high in 2011 and low in
  2016 and 2021.
- **Neither is distinguishable from zero.** The lift is a constant 0.32 offset.
  The residual it sits on ranges across 1.45 in log between cycles.

**The defect note's "high by about 0.3 in log in every cycle" describes the
centre against its own pre-shrink value, not against the result.** Against
the result it is false in 2021.

Do not quote a pooled figure. The pooled after-lift mean log residual for
established parties is −0.044. That comes from 2021 having 79 of the 175
parties, not from the centres being unbiased.

### 3.2 Ranks 13+ (measured, `a9.py`)

Modelled parties ranked 13+ by pre-shrink centre, signed (centre − realised),
summed over the cycle's 8 metros: −1.21 → −0.72 (2011), −4.11 → −0.76 (2016),
−22.75 → −15.95 (2021). The tail is under-forecast in total in every cycle,
with or without the lift. §1.44's "+5.60pp, over-forecast" described the model
of 2026-08-17.

### 3.3 Which reference is unbiased under the 1b draw (argued)

v3 draws a unit party as logistic(logit m + κ + x), x ~ N(0, s²), with κ chosen
so that E[share] = m. For a small party log(share/m) ≈ κ + x with κ ≈ −s²/2. A
mean-unbiased centre therefore implies a mean log residual near −s²/2, not 0:
about −0.49 at 2026's total width of 0.988. Against that reference, both
versions are too low in the mean:

- with the lift, the cycle-mean log residual is −0.22, which is +0.27 above
  −0.49;
- without it, +0.11, which is +0.60 above.

On this reading the lift brings the class closer to mean-unbiased.

v3's σ_cyc is an RMS about 0, not about −s²/2, so it mixes the median and the
mean. That is a separate defect report for v3; it is not fixed here.

---

## 4. Coupling with the 1% small-party class

### 4.1 What a level change forces the record to re-estimate

The width writer (`src/unit_width_record.py`, v3 §3.5) measures
r = log(realised / `pool_spec` centre). If the shrink changes, these must be
re-estimated:

- **Membership.** The centre test reads the `pool_spec` centre, so parties
  near 1% move. Established parties with a positive result go 58 → 59 (2016)
  and 75 → 78 (2021). The JHB 2026 class stays 19 established and 5 debutants.
- **σ_cyc.** The cycle means shift by the lift, which is one factor per city
  for parties well below `h`.
- **σ_btw.** It moves a little, because the factor varies by metro (1.397-1.452).
- **σ_deb.** As for σ_cyc.
- **σ_wit.** It is almost unchanged. Within a metro, the kept fraction varies
  only from 0.999 to 0.936 across the class, so the change comes mainly from
  membership.
- **The κ table.** It is solved per run from the widths.

### 4.2 Widths with and without the lift (measured, `a7.py`)

Forward ANOVA about the `pool_spec` centre at the 1% line, v3's estimator
unchanged. The with-lift row reproduces the 1% run of 2026-10-11
(`w_1pct.json`).

| width for | lift | σ_cyc | σ_btw | σ_wit | total | σ_deb |
|---|---|---|---|---|---|---|
| 2016 | with | 0.971 | 0.000 | 0.636 | 1.161 | 0.936 |
| 2016 | without | 0.640 | 0.000 | 0.636 | 0.903 | 1.097 |
| 2021 | with | 0.700 | 0.191 | 0.635 | 0.964 | 1.290 |
| 2021 | without | 0.467 | 0.156 | 0.647 | 0.813 | 1.298 |
| **2026** | **with** | **0.639** | **0.175** | **0.734** | **0.988** | **0.949** |
| 2026 | without | 0.605 | 0.166 | 0.735 | 0.966 | 0.980 |

Cycle means for established parties: with the lift −0.971 / −0.191 / +0.495;
without it −0.640 / +0.165 / +0.812.

The reviewer's "0.57 → about 0.48" was for the three-quota line. At 1% the 2026
σ_cyc changes by 0.03.

JHB 2026 unit-class `pool_spec` centre total: 3.950% with the lift, 2.992%
without.

### 4.3 Coverage (measured, offline, v3's coverage method)

90% bands, unit class at 1%, each version with its own forward widths:

| | 2016 | 2021 | 2016 + 2021 |
|---|---|---|---|
| with lift | 0.915 (4 below, 2 above, n 71) | 0.855 (2 below, 15 above, n 117) | **0.878** (n 188) |
| without lift | 0.863 (3 below, 7 above, n 73) | 0.775 (2 below, 25 above, n 120) | **0.808** (n 193) |

Removing the lift adds misses above the band: the realised results sit higher
than the unlifted centres allow.

**This comparison is confounded.** Without the lift the forward widths narrow.
For example, the 2016 σ_cyc falls from 0.971 to 0.640, because it is the RMS
about zero of 2011's cycle mean, and the lift moves that mean from −0.64 to
−0.97. Narrower bands cover less. Part of the fall from 0.878 to 0.808 is
therefore v3's estimator counting the lift's own offset as cycle uncertainty
(§3.3). The two effects can be separated only once σ_cyc is defined about the
draw's own mean (−s²/2).

### 4.4 Sequencing in one canonical run

All steps happen in one re-emit window on a settled tree (CLAUDE.md §3). There
is one writer, and nobody measures while it writes.

1. **Land the code.** That is 1b v3 at the 1% line, 1c paired streams, and the
   Option K text edits. Commit.
2. **Make the width record keyed on the shrink.** The artefact key of
   `unit_width_record.json` must include `level_shrink` and
   `level_shrink_scale` (the scenario values the centres were built with) and
   the source hash of `compress_levels`. The writer takes a scenario override
   and an `--out` path. That gives two records: the default with
   `level_shrink = 0.35`, and `level_shrink = 0.0` written to a second path.
   `make_drawer` refuses a record whose key does not match the run's scenario.
3. **`unit_width_record.py --emit` twice**, once per value.
   `group_share_record.py --emit` in the same window if its key covers centres.
4. **Canonical paired run**, 24 city-years plus JHB 2026. Arms:
   - incumbent (arm E code);
   - v3 at 1% with `c` = 0.35;
   - v3 at 1% with `c` = 0.
   Each reads its own record, with the same paired streams. Report Key 1 per
   arm against the incumbent, **split by cycle (2011, 2016, 2021)**. 2011
   appears in a Key 1 comparison of the shrink for the first time.
5. **The owner decides.** If the decision is removal, apply §2.5 step 2. The
   record and the run with `c = 0` are already the canonical ones for that code
   state, because the identity at 0.0 is exact.

---

## 5. Predicted effect of removal, against the world

Predictions are for v3 at 1% with `c` = 0, against v3 at 1% with `c` = 0.35.
They were computed against arm E's draws with each party's draw mean scaled by
its `pool_spec` centre ratio (no-shrink / shrink) and renormalised (`a8.py`).
v3 itself moves means by −0.027 points of list MAE (v3 §6.2), which is small
against these.

### 5.1 Johannesburg 2026, mean list share

| party | normalised centre, with → without (%) | `pool_spec` centre, with → without (%) | arm E mean → predicted without (%) | change (points) |
|---|---|---|---|---|
| DA | 25.98 → 27.77 | 26.00 → 27.78 | 25.59 → 27.38 | **+1.79** |
| ANC | 23.74 → 25.25 | 23.76 → 25.26 | 23.84 → 25.38 | **+1.54** |
| ActionSA | 11.66 → 11.75 | 11.67 → 11.76 | 11.73 → 11.84 | +0.10 |
| EFF | 10.95 → 10.97 | 10.96 → 10.98 | 10.98 → 11.01 | +0.03 |
| MK | 9.09 → 8.93 | 9.09 → 8.94 | 9.03 → 8.88 | −0.15 |
| PA | 5.82 → 5.44 | 5.82 → 5.44 | 5.67 → 5.30 | −0.37 |
| RISE | 1.82 → 1.50 | 1.82 → 1.50 | 1.83 → 1.50 | −0.32 |
| IFP | 1.50 → 1.21 | 1.50 → 1.21 | 1.49 → 1.21 | −0.28 |
| BOSA | 1.16 → 0.92 | 1.16 → 0.92 | 1.19 → 0.95 | −0.24 |
| ALJAMAAH / VF+ / ACDP | 0.88 / 0.88 / 0.73 → 0.69 / 0.69 / 0.57 | same | | −0.21 / −0.20 / −0.17 |
| 72 parties with arm E mean < 1% | | | 8.65 → 6.55 total | −2.10 |
| unit class at 1% (24 parties) | | 3.950 → 2.992 total | | −0.96 |

**Seats.** These come from list-only largest remainder on the normalised
centre, 270 seats, not the model's allocation. With the shrink → without:

- DA 70 → 75, ANC 64 → 68;
- MK 25 → 24, PA 16 → 15, RISE 5 → 4, VF+ 3 → 2, ALJAMAAH 3 → 2;
- four micro-parties (IRC, AZAPO, African Renaissance Unity, Vuka SA): 1 → 0 each.

BOSA's centre crosses the line (1.16% → 0.92%), but its previous result, the
national share of 1.02%, keeps it out of the class either way. The class test
is max(previous, centre) < 1%. JHB 2026 membership is unchanged: 19
established and 5 debutants with and without the lift (§4.1).

### 5.2 Panel list MAE, per cycle

Change in share-weighted list MAE, without minus with, mean of 8 metros:

| cycle | predicted change (pp) | metros better / worse | range |
|---|---|---|---|
| 2011 | **−1.52** | 8 / 0 | −1.85 to −0.87 |
| 2016 | **+0.72** | 1 / 7 | −0.51 to +1.55 |
| 2021 | **+0.50** | 2 / 6 | −1.70 to +1.97 |
| mean of three cycles | −0.10 | | |

Wrong-party seats (list-only proxy, half the summed absolute seat error, sum of
8): 2011 −33, 2016 +8, 2021 +22.

### 5.3 Falsifiers (tests of the description, never targets)

| # | quantity, in the canonical paired run | prediction | falsified if |
|---|---|---|---|
| 1 | list MAE change, 2011 cycle mean | −1.52 | sign positive, or outside −2.3 to −0.8 |
| 2 | list MAE change, 2016 / 2021 | +0.72 / +0.50 | either sign negative, or outside ±50% of the prediction |
| 3 | coherent seat error (`compare_history`), sign per cycle | removal better in 2011; worse in 2016 and 2021 | any cycle with the other sign. A result of 0 in 2016 is reported as a tie, not as agreement (§1.94 found five ties there) |
| 4 | JHB 2026 DA / ANC mean list share change | +1.79 / +1.54 | outside ±0.5 points |
| 5 | JHB 2026 unit-class mean total | 2.99% without, 3.95% with | outside ±0.15 points of either |
| 6 | unit-class 90% coverage, 2016 + 2021 | 0.878 with, 0.808 without | either outside ±0.06 |

Why the predictions are expected to hold: the shrink pulls the top toward the
middle; 2011's top was under-forecast and 2016's and 2021's over-forecast
(§1.5). If falsifier 1 fails (removal does not help 2011), the 2011
under-forecast does not come from the shrink, and the "stand-in for
fragmentation" reading loses its only out-of-sample support.

Option K predicts no number change. Its falsifier is the suite staying
byte-identical on the goldens after the text edits.

---

## 6. Tests

### Option K

- **Add `test_the_unit_width_record_key_moves_with_the_level_shrink`**
  (with v3's writer). It builds the key at `level_shrink` 0.35 and 0.0 and
  asserts they differ. It perturbs `compress_levels`' source in a copy and
  asserts the key changes, then that it returns when the perturbation is
  reverted. This is the coupling 1b depends on. The test sees a constructed
  change and goes quiet again when it is undone.
- **Add `test_the_shrink_lifts_the_bottom_by_the_scale_factor`.** For a
  constructed vector, a party at 1e-5 has after/before equal to `total/freed`
  to 1e-4. This records the lift as a measured property of the code rather
  than prose.
- **Change, docstring only:**
  `test_chain::test_the_level_shrink_is_exactly_the_identity_when_it_is_off`.

### Option R (after the owner's decision)

Retire or rewrite these. Each asserts the shrink exists or ships:

- `test_chain`: `test_the_level_shrink_takes_from_the_big_and_gives_to_the_small`
  (it asserts `ratio[smallest] > 1`, which is the lift itself); the
  determinism test that calls `compress_levels` twice (`:1666-1669`); the
  identity test; the `30_centres` ordering assertion (`:1700-1703`).
- `test_blended_centres`:
  - `test_the_level_shrink_conserves_the_total_and_the_ordering`;
  - `test_the_shipped_level_shrink_is_not_the_identity`;
  - the scenario fixtures passing `level_shrink` (`:116-120`, `:952`,
    `:983-984`, `:1088`).
- `test_stage_estimation`:
  - the `30_centres` readers (`before_shrink`/`after_shrink`, `:773-900`);
  - `test_the_level_shrink_is_cycle_blind_by_construction`;
  - the conservation notes (`:48`, `:62`).
- `test_export_draws` fixture (`:630`); the `test_drawer` comment (`:358-373`).
- **Values move:** drawer goldens, `test_group_share_tripwire`, the golden
  prior. Re-record them deliberately, saying why (CLAUDE.md §2).
- **Add `test_blended_centres_returns_the_unshrunk_vector`.** On a constructed
  input, `30_centres` equals the per-route centres and the bottom party's
  centre is unchanged.

---

## Judgement calls

| call | value | status |
|---|---|---|
| `level_shrink` | 0.35 | Kept under K. A fit to realised outcomes on 2016/2021 under an earlier model, with its form screened on the same nine city-years. Three clusters. 2011 is reversed (offline). Registered 🟡 in §A23; the 2011 record is added after the run |
| `level_shrink_scale` | 0.04 | Kept under K; §F20 unchanged |
| freed mass returned by uniform renormalisation | | Kept. Every alternative family has a measured cost (§2.2) |
| unit line | flat 1% (owner) | v3 membership; the centre test reads the `pool_spec` centre, so the shrink decision moves panel membership near the line (2016: 58 → 59, 2021: 75 → 78); JHB 2026 membership is unchanged |
| removal if adopted: delete the lever rather than leave it at 0.0 | | precedent §1.54; owner may prefer an inert sweepable lever |

## Measured and argued

- **Measured (offline, from arm E traces and realised results):**
  - the lift factors (§1.2);
  - the band and MAE table by cycle (§1.5);
  - the small-party bias (§3.1, §3.2);
  - widths and coverage (§4.2, §4.3);
  - the JHB 2026 centre shifts (§5.1, at the stated stage).
- **Approximated:**
  - the MAE and seat predictions (§5.1 seats, §5.2): draw means scaled by
    centre ratios, list-only seats;
  - the 2011 screen, which is the least reliable (0.8pp gap to `pr_mae`).
- **Argued:**
  - the redistribution algebra (§2.1);
  - the mean-unbiased reference under v3's draw (§3.3);
  - the fragmentation reading of the 2011 reversal (§1.5).

## Rejected claims

| claim | source | evidence against it |
|---|---|---|
| small-party centres are high by ~0.3 in log in every cycle | `1b-level-lift-defect.md` | that is centre-after against centre-before. Against results, the established class is low in 2021 with the lift (total ratio 1.635, mean log +0.485); §3.1 |
| ranks 13+ are over-forecast | `compress_levels` docstring; §1.44; JUDGEMENT-CALLS §A23 | on the current model, under-forecast in total in all three cycles with and without the lift (§3.2) |
| the shrink is off by default | `compress_levels` docstring; `test_chain` docstring | `DEFAULTS["level_shrink"]` = 0.35 (`src/montecarlo.py:409`) |
| removing the lift lowers 2026 σ_cyc from 0.57 to ~0.48 | reviewer, `step2/2-recheck-1b-v2.md` | that was at three quotas. At the owner's 1% line, 0.639 → 0.605 (§4.2) |
| 0.35 is a property of the model, not the scoreboard | `compare_history`/`compress_levels` docstrings | the value was fitted to realised outcomes of 2016 and 2021, the targets it is scored on. 2011, the one cycle outside the fit, reverses the premise (§1.5) |
| a targeted redistribution can remove the lift at no cost | implied by the defect note's framing | any redistribution with no bottom lift sends the mass to the middle or the top; all three families have measured costs (§2.2) |
