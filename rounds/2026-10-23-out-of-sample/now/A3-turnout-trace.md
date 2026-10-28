# A3. Pool turnout and VD turnout: how they combine in a Johannesburg 2026 draw

2026-10-28, Scout, branch `site-sweep-1` at `99556398`, no tracked file edited.
Answers DATA-USE-AUDIT.md §2 item 3 and §3. Line numbers are from `grep -n` on
this tree.

**Measured** means it came out of the in-process runs in §3. **Read** means it
was read from the code at the cited line. **Inferred** means it is reasoning
from the code that the runs did not isolate.

## 1. Summary

- The two turnouts do different jobs and neither overwrites the other.
  Pool turnout sets only the **relative pool mix** of each draw's citywide PR
  target vector. VD turnout sets **every vote count** and the **ward tallies**.
- The pool-turnout **level** cancels at `montecarlo.py:4876` (`totals/cast`),
  and its **mean effect** is removed twice, by the modal-vote IPF
  (`:3299`, `:3422`) and by the universal law's κ calibration (`:4971`).
  Measured: scaling every pool's `[lo, mid, hi]` by 1.10 changed no drawn
  number (max |Δ citywide PR share| 3.9e-16 as a fraction, over 1,000 draws). Shifting one
  pool moved per-draw shares by up to 1.37pp, moved mean citywide shares by
  at most 0.008pp, and left mean seats unchanged within what 1,000 draws resolve (every party within 0.04).
- The VD-turnout **level** cancels at `:1619` (`weight / weight.sum()`) and
  `:7539`. Its citywide level from `turnout.csv`'s level column is replaced
  by the ratio column's level at `:6845`. The VD **pattern** survives into
  ward winners through `:7543` → `:7552` → `:7556` → `:7594`, and slightly
  into the citywide ward-ballot share of parties on few ward ballots (max
  0.15pp in one draw). Measured: a pattern
  perturbation left citywide PR shares fixed (max |Δ| 9.7e-7 as a fraction) and flipped
  2,758 of 135,000 draw×ward winners. It moved ANC mean seats +1.20 and DA
  −0.46 over 1,000 draws.
- Of the two, VD turnout moves seat means. Pool turnout moves seats
  within individual draws and leaves the mean in place.

## 2. Code trace

### 2a. Pool turnout, from record to draw

| step | file:line | what happens (read) |
|---|---|---|
| record | `pools.py:2542` `turnout_record` | per-pool LGE turnout record |
| band | `pools.py:2585` `turnout_band`, called at `:6051` | triangular `(lo, mid, hi)` per pool |
| emit | `pools.py:6400-6404` | written to the spec as `"turnout": [lo, mid, hi]` |
| load | `montecarlo.py:6118` | `scenario["pools"] = spec["pools"]` |
| pool votes at the mode | `montecarlo.py:3299` | `pool_votes[g] = registered × turnout[1]` (mid only) |
| IPF | `montecarlo.py:3422` | `R` balanced so that, at modal pool votes, citywide party shares equal the centres |
| spec tuple | `montecarlo.py:3469` | `(lo, mid, hi)` carried into `pools[name][2]` |
| drawer built | `montecarlo.py:4299` (in `make_drawer`, called at `:7403`) | |
| conserved centres | `montecarlo.py:4571`, `pool_spec_centres` `:3820` | centres computed at **modal** turnout, `registered × mid` |
| composition variance | `montecarlo.py:4696`, subtracted at `:4708` | the variance that pool-turnout draws put into each party's share is taken **out** of that party's own width |
| per-draw turnout | `montecarlo.py:4625-4628` | `correlated_triangular` (ρ = `TURNOUT_CORRELATION`), `totals[name] = registered × turnout` |
| per-draw balance | `montecarlo.py:4670` | `R0` rebalanced to the shocked centres, still against the **modal** `pool_votes` |
| pool mix enters the target | `montecarlo.py:4772`, `:4876` | `target += (totals[name] / cast) × split`. Only each pool's share of the drawn total reaches the target. |
| normalise | `montecarlo.py:4893` | `target / total` |
| κ calibration | `montecarlo.py:4971` | κ moved until each party's mean drawn share over the calibration draws equals `u_c` |
| out | `montecarlo.py:7476` | `pr_target = draw_target(d)`; ward target from it at `:7488` (`ballot_targets`, `:1579`) |

Pool turnout ends at `pr_target`. It never multiplies a VD, a ward or a vote
count (read: no consumer of `totals` outside `draw_pools`; measured: the mean
drawn PR vote total over 1,000 draws is 1,013,938 in every pool arm and in base).

### 2b. VD turnout, from turnout.csv to seats

| step | file:line | what happens (read) |
|---|---|---|
| build | `turnout.py:156` `main`. Writes `turnout_<T>_projected` (`:405`, `:419`) = previous-NPE turnout × λ̂ × by-election tilt, capped at 1; and `turnout_<T>_level` (`:444`) | |
| columns read | `montecarlo.py:6799-6800` | `turnout_2026_projected` (ratio pattern) and `turnout_2021` (the previous LGE). **Not** `turnout_2026_level`. Its only reader in `src/` and `tests/` is `export_interactive.py:186` (grep for `_level` with `turnout`, and for `year}_level`). |
| read | `montecarlo.py:6806`, `:6816`, `:6818` | level capped at 1.0 per VD |
| roll | `montecarlo.py:6787`, `:6828` | `reg` = crosswalk part registration summed per VD |
| level replaced | `montecarlo.py:6840`, `:6845` | the level pattern is rescaled to the ratio pattern's roll-weighted mean. Only the ratio column's citywide level survives. |
| dead anchors | `montecarlo.py:6859-6864` | `t_hi`, `t_lo` are computed and never read again in the file |
| per-draw blend | `montecarlo.py:7492-7501` | blend of the two patterns, jittered, lognormal VD noise, clipped to [0.02, 0.95] (`:584-585`) |
| weights | `montecarlo.py:7523` | `weight_cal = reg × t_draw` |
| VD shares calibrated to the target | `montecarlo.py:7528`, `:7531`. `solve_and_predict` normalises weights at `:1619` | θ is solved so that the **turnout-weighted** citywide share equals `pr_target` / `ward_target`. Turnout level cancels. The turnout pattern decides which VDs carry each party's citywide total. |
| votes | `montecarlo.py:7537-7540` | `pr_votes = weight @ pr`; shares renormalised, so these equal `pr_target` up to the solver's reachable gap |
| ward tallies | `montecarlo.py:7543`, `:7552`, `:7556`, `:7561` | `part_cast = part_reg × t_draw[part_vd]`. The ward winner is the argmax of turnout-weighted VD ballots. |
| allocation | `montecarlo.py:7575-7581`, `:7593-7603` | integer-rounded ward + PR votes → `eligible_parties` → `allocate_with_overhang` (ward wins enter as `pool_wins`) → `council_seats` |

### 2c. Where each is normalised away

- **Pool-turnout level:** `montecarlo.py:4876`. A common factor on every
  pool's turnout cancels in `totals[name] / cast`, and `R` is row-normalised
  after `:3299`, so it cancels there too.
- **Pool-turnout mean effect on shares:** `:3299` + `:3422` place the modal
  draw on the centres. `:4971` forces the mean drawn share onto `u_c`, which
  `:4571` computes at modal turnout.
- **Pool-turnout effect on width:** subtracted at `:4708`.
- **VD-turnout level:** `:1619` and `:7539`, and the ward argmax at `:7556`,
  which does not change when every VD is scaled by the same factor.
- **turnout.csv level column's level:** replaced at `:6845`.

## 3. Perturbation runs (measured)

**Method.** `run_model` was imported and called in-process
(`/private/tmp/claude-501/turnout-trace/perturb.py`), with no `run_dir`.
Per its docstring (`montecarlo.py:5937`) it then writes nothing. The settings
were Johannesburg 2026, 1,000 draws per arm, seed 20261104 (the DEFAULTS
seed), `draw_law = "universal"`, and `kappa_converged = True` in every arm.

- **Pool arms:** `montecarlo.read_pool_spec` was wrapped to deep-copy the spec
  and change `turnout` in the copy, after the staleness check. The spec read
  in every arm carried the same `artefact_key` (`pools_sha e532c3005e0524b8`)
  and `stale = None`.
- **VD arms:** `montecarlo.csv` was replaced by a shim whose `DictReader`
  rescales every `turnout_*` column only when the file is `turnout.csv`. The
  delivery record `artefact:turnout.csv` confirms the change reached the model:

| arm | `mean_ratio` delivered |
|---|---|
| base | 0.41937 |
| `vd_uniform` | 0.37744 |
| `vd_split` | 0.43001 |

- **Write checks:** `find data -newer <marker> -type f`, taken after the
  seven arms, returned nothing. The sha256 of `data/processed/turnout.csv`
  and `pools_2026.json` was unchanged before and after the runs.
- **Pairing:** draws are keyed streams, so arm and base share every random
  number. `pool_tri_all` reproduces base to 1e-16, which shows the pairing.

The baseline pool bands from the spec (`[lo, mid, hi]`) were:

| pool | lo | mid | hi |
|---|---|---|---|
| Black African | 0.236 | 0.370 | 0.528 |
| Coloured | 0.251 | 0.561 | 0.830 |
| Indian/Asian | 0.123 | 0.461 | 0.840 |
| White | 0.358 | 0.602 | 0.803 |

Arms:

| arm | change (in memory only) |
|---|---|
| `pool_mid_BA` | Black African mid +0.05, lo and hi unchanged |
| `pool_tri_BA` | Black African lo, mid and hi +0.05 |
| `pool_tri_W` | White lo, mid and hi −0.10 |
| `pool_tri_all` | every pool's lo, mid and hi ×1.10 (none reaches the 0.999 cap) |
| `vd_uniform` | every `turnout_*` value ×0.90 |
| `vd_split` | VDs above the median `turnout_2021` ×1.15, the rest ×0.85, on every `turnout_*` column |

Differences from base, paired by draw, over 1,000 draws:

| arm | max \|Δ PR share\|, any draw and party (pp) | max \|Δ mean PR share\| (pp) | max \|Δ ward-ballot share\|, any draw and party (pp) | seats changing party per draw, mean (max) | draws with any seat move | draw×ward winner flips (of 135,000) | mean drawn PR vote total |
|---|---|---|---|---|---|---|---|
| base | – | – | – | – | – | – | 1,013,938 |
| `pool_mid_BA` | 0.760 | 0.0032 | 0.782 | 0.88 (4) | 692 | 251 | 1,013,938 |
| `pool_tri_BA` | 1.187 | 0.0072 | 1.245 | 1.14 (4) | 786 | 366 | 1,013,938 |
| `pool_tri_W` | 1.365 | 0.0082 | 1.406 | 1.01 (4) | 717 | 328 | 1,013,938 |
| `pool_tri_all` | 3.9e-14 | 1.3e-14 | 4.4e-14 | 0 | 0 | 0 | 1,013,938 |
| `vd_uniform` | 2.4e-5 | 4.3e-8 | 7.2e-5 | 0.013 (1) | 13 | 0 | 912,581 |
| `vd_split` | 9.7e-5 | 3.1e-5 | 0.150 | 1.57 (11) | 731 | 2,758 | 1,039,356 |

"Seats changing party per draw" is half the summed absolute seat difference
between arm and base in the same draw.

Mean seats over 1,000 draws, base → arm. Every arm moved every other party in
the table by 0.04 seats or less:

| party | base | `pool_tri_W` | `vd_split` | base ward seats → `vd_split` ward seats |
|---|---|---|---|---|
| DA | 71.63 | 71.65 | 71.17 | 47.10 → 45.56 |
| ANC | 70.39 | 70.38 | 71.59 | 68.71 → 69.92 |
| ASA | 29.57 | 29.57 | 29.37 | 0.04 → 0.03 |
| EFF | 27.66 | 27.65 | 27.47 | 3.81 → 3.66 |
| MK | 22.57 | 22.57 | 22.48 | 9.57 → 9.61 |
| PA | 16.83 | 16.84 | 16.72 | 2.13 → 2.46 |

The sd of citywide PR share per party (over draws) moved by at most 0.07pp in
any pool arm: PA 3.484 → 3.413 in `pool_mid_BA`, DA 3.807 → 3.837 in
`pool_tri_W`. It did not move in either VD arm.

### What the runs show, and what is inferred

- **Measured:** a common scale on pool turnout is inert. A relative shift
  between pools moves each draw's citywide target and through it the seats of
  that draw. It does not move mean shares beyond 0.008pp, under the
  universal law with κ converged. Mean seats moved by 0.04 or less per party,
  which 1,000 draws cannot distinguish from zero.
- **Inferred:** the mean is held by `:3299`/`:3422` together with `:4971`. The
  runs do not separate those two, because κ calibration was not switched off.
  Under `draw_law = "incumbent"` there is no κ pass (the pass is gated
  at `:4939`, `if law == "universal"`), so a pool-turnout shift that moves the triangle's mean
  away from its mode could move mean shares there. That was not run.
- **Measured:** a uniform scale on VD turnout moves no citywide share (max |Δ| 2.4e-7 as a fraction)
  and no ward winner. Thirteen draws changed one seat each, between two
  parties, mostly small ones (measured). Two lines can produce that (inferred,
  not separated):
  - the `int(round(...))` vote totals at `:7575-7577`, on a vote base 10%
    smaller, changing a near-tie at the last remainder;
  - the per-draw ceiling of 0.95 at `:7499`. With VD noise sd 0.08, it can
    bind in some draws for the highest-turnout VDs (max `turnout_2021` 0.966,
    max projected 0.875; measured), and a ×0.9 scale changes which ones bind.

  The per-VD cap at 1.0 (`:6818`) never binds: no value exceeds 1.0
  (measured).
- **Measured:** a VD turnout pattern change holds citywide PR shares (max
  |Δ| 9.7e-5pp) and moves ward winners. It holds the citywide ward-ballot
  share less tightly:
  - The largest move is DUDULA, 0.150pp in one draw, against a mean ward
    share of 0.142%. DUDULA is on 4 of 135 ward ballots (`levels.ballots`).
  - Next are two parties on one ward ballot each (TAU_DIA_RORA…,
    RESIDENT_DEVELOPMENT), at 0.057pp and 0.056pp, then DA at 0.050pp.
  - The largest change in any party's mean ward-ballot share is 0.0012pp.

  Inferred: the masked ward solve (`:7531`, `mask=ward_mask_vd`) does not
  reach its target exactly for a party confined to a few VDs, so that party's
  share depends on those VDs' turnout weight. The runs do not separate how
  much of `vd_split`'s seat movement comes through this route into `combined`
  (`:7575-7581`) and how much through ward winners. Given the size of this
  route, ward winners probably carry most of it (inferred). Inferred mechanism: with citywide shares fixed, more weight
  on the high-turnout VDs makes `solve_and_predict` lower the θ of the
  parties strong there, which costs those parties marginal wards elsewhere.
  DA lost 1.54 ward seats; ANC gained 1.21. ANC's ward wins equalled or
  exceeded its total seats in 874 of 1,000 base draws (measured). In those
  draws an extra ward win is an extra seat, which is how a ward-winner change
  reaches total seats (inferred from `allocate_with_overhang`, not traced
  draw by draw).
- `vd_split` is a constructed pattern correlated with geography. It shows the
  channel and an order of magnitude for a ±15% pattern change. It is not an
  estimate of how wrong `turnout.csv` is.

## 4. Consequences for the audit's §2 item 3

- The two definitions (pool: PR valid ÷ roll; VD: valid + spoilt on the higher
  ballot ÷ roll) never meet in one quantity. Pool turnout reaches the draw
  only as relative pool weights in `pr_target`. VD turnout reaches it only as
  relative VD weights and ward tallies. No line reconciles their citywide
  levels, and the code needs none, because both levels cancel (PR ballot
  exactly; ward ballot to within the masked solve's gap, §3). A
  disagreement between the two citywide levels is invisible to the seats.
- The pool and VD weights can disagree about the same voters. A draw in which
  the White pool turns out high raises DA's citywide target (via `:4876`).
  The VD turnout of that draw is drawn independently (`:7492-7501`, streams
  `vd_turnout.*`), so the VDs where that pool lives do not turn out high in
  the ward tallies. Read, not measured.
- Two unused computations sit on the path. `t_hi`/`t_lo`
  (`montecarlo.py:6859-6864`) are dead. `turnout_2026_level` is emitted by
  `turnout.py:444` and ignored by `run_model`, which rebuilds the level
  pattern from `turnout_2021` at `:6818` and `:6845`.

Run artefacts (outside the repo): `/private/tmp/claude-501/turnout-trace/`.
It holds `perturb.py`, `analyse.py`, `res_<arm>.json` (per-draw seats, shares,
ward winners and pool turnouts), `log_<arm>.txt` and `sha_before.txt`.
