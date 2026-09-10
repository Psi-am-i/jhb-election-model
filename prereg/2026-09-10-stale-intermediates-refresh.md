# Pre-registration — refreshing the stale processed intermediates

Written 2026-09-10, BEFORE any file was regenerated in the live tree and before
any `compare_history` run. Not edited afterwards.

## What was found, and how

Every `.csv` under `data/processed` was deleted in an isolated scratch root
(`data/raw`, `src`, `cities`, `config`, `content` symlinked; `data/processed`
copied, then all 104 CSVs removed) and every generator was re-run from empty.
The population is therefore unambiguous: a file that exists afterwards was
written by a generator, and a file that does not was written by nothing.

**Two earlier readings of this were wrong and are struck.** The first reader
trace was too narrow and reported "nothing reads it" for seven families that
have real readers. The second compared a scratch tree in which most files had
never been rewritten, so "identical" was trivially true for them; the mtime
fence intended to catch that was worthless because `cp -R` restamps.

| verdict | files | meaning |
|---|---|---|
| CURRENT | 51 | byte-identical to what today's code produces |
| STALE | 26 | a generator produces something different |
| NO-GENERATOR | 27 | nothing in `src/` reproduces it from raw |

## The 26 stale files, and whether the model can see the difference

| family | n | what moves | reaches the forecast? |
|---|---|---|---|
| `fold{1,2,3,4}_parameters.csv` (7 cities) | 11 | `theta_calibrated` ONLY; `theta_raw` and `gamma` identical to 4dp | **NO** — `montecarlo.py:4072` and `export_interactive.py:129` read `params[ballot]["gamma"]` and nothing else. `theta_calibrated` is consumed only by `fold.py --fit-from` |
| `<city>/2016/turnout.csv` (7 cities) | 7 | five pre-2011 columns ADDED; every shared value identical | **NO** — `prior_years` is `>= "2011"` at this target |
| `<city>/2021/turnout.csv` (7 cities) | 7 | `turnout_2021_projected` moves on 207–709 VDs per city, mean \|Δ\| ≈ 0.020, max 0.30; `lambda_hat` moves with it | **YES** — this is `projected_col`, which becomes `ratio_pattern` at `montecarlo.py:4120` |
| `party_crosswalk.csv` | 1 | carries a `bloc` column retired at commit 87806a7 | **NO** — no reader anywhere in `src/` or `tests/` |

Joburg's turnout files are current at all three years; the other seven cities'
2021 files predate the 2026-08-09 pre-2011 archive ingest, which is what gave
λ̂ its 2011 anchor. Registered-weighted city mean projected turnout moves by up
to 1.35pp (tshwane 0.54466 → 0.53116) and joburg by exactly 0.00000.

`montecarlo.py:4142` already carried the warning in a comment: *"an artefact
that reaches the model WITH NO KEY AT ALL. Nothing declares `turnout.csv`,
nothing sweeps it, and it carries no artefact key: a stale or rebuilt copy moves
every draw in silence."* It did, for seven cities, and nothing caught it.

## Predictions

**PRIMARY — mechanism.** Refreshing the 11 fold files and the 7 2016 turnout
files changes **no scored number anywhere**, because the columns the model reads
from them are byte-identical. This is the clause that distinguishes "the fold
staleness was cosmetic" from "we got lucky".

**SECONDARY — the affected population, stated as an exact set.** Exactly the
seven non-joburg 2021 city-years change. Joburg 2021 does not change. No 2011
or 2016 city-year changes, in any city.

**Accuracy — TWO-SIDED, and no direction is predicted.** The refreshed λ̂ uses
more history, not different history, so `seat_abs_err_coherent` may move either
way. I predict only that the panel total moves by **less than 40** in absolute
terms on 24 rows, i.e. that this is a real but second-order input correction and
not a structural change. A move larger than that means something other than the
turnout pattern is being disturbed and must be chased before anything is
believed.

**The only external yardstick:** the margin over uniform swing (885 coherent,
n=24) improves or is unchanged.

**I predict no return to any prior total, and a result near one is evidence of
nothing** (CLAUDE.md §1).

**Falsified if:** any 2011 or 2016 city-year moves; or joburg 2021 moves; or a
fold-file refresh alone moves a scored number; or the panel total moves by 40 or
more; or the uniform-swing margin worsens.

## What is deleted rather than refreshed

| file | why |
|---|---|
| `data/processed/ward_leverage.csv` | written by `archive/retired-scripts/leverage.py`, whose own docstring records that nothing read it. No writer in `src/`, no reader anywhere. |
| `data/processed/tshwane/turnout.csv` | orphan at city level. `turnout.py --city tshwane` writes `tshwane/2026/turnout.csv`; the model reads `target.processed/turnout.csv` = the same. This copy holds the pre-ingest schema and no invocation produces it. |

`fold5_parameters.csv` is **kept and flagged**, not deleted: fold 5 has
`lambda_pair: None`, so the default `--turnout level` is refused and every
non-default writes a variant filename. **No invocation available today
reproduces this file under this name.** It is read only by `fold.py --fit-from 5`
and never by the forecast (`GAMMA_FOLD` is `{2026:1, 2021:1, 2016:3, 2011:4}`).
Deleting it would destroy an artefact that cannot be rebuilt, for no gain.

---

# RESULT — written after the run, predictions above not edited

Baseline, on the tree as it stood:

    seat_abs_err_coherent=725/@efa06f78+dirty/1000d/pools:843229db/rows=24
    margin_vs_uniform_swing = 18.1%   [rows=24, coherent]

After refreshing all 26 stale files and deleting the two orphans, same command:

    seat_abs_err_coherent=725/@efa06f78+dirty/1000d/pools:843229db/rows=24
    margin_vs_uniform_swing = 18.1%   [rows=24, coherent]

**The 24-row seat table is byte-identical.** Not "close" — `diff` of the two
tables is empty, on every column of every row.

## Scoring

| clause | verdict |
|---|---|
| PRIMARY — fold and 2016-turnout refresh change no scored number | **CONFIRMED** (and by construction: the columns read are byte-identical) |
| SECONDARY — exactly the seven non-joburg 2021 city-years change | **FALSIFIED** — none of them changed |
| accuracy — panel total moves by less than 40 | confirmed trivially (moved 0) |
| uniform-swing margin unchanged or better | **CONFIRMED** — 18.1% both sides |

## Why the secondary clause failed, established rather than assumed

An input that moves 700 VDs by a mean of 2pp and changes nothing looked like an
instrument failure, so it was chased instead of explained away.

1. **The model does read the refreshed file.** `--run-dir` trace for capetown
   2021: `artefact:turnout.csv → {vds: 779, projected_col: turnout_2021_projected,
   mean_ratio: 0.5878}`. 779 is the refreshed row count; the old file had 772.
2. **The input is live, not inert.** Swapping the old file back in and re-running
   the same city-year changes the output: `P(any party excessive)` 0.7% → 0.6%,
   three coalition probabilities by 0.1pp, one MWC probability 2.1% → 2.0%.
3. **It is below seat resolution.** In that same A/B, no seat median and no band
   moved — DA+AIC+ATM is 141 seats, 119–161, on both sides.

The magnitude explains it. `t_draw` takes `t_ratio` at a blend weight of 0.5,
jittered by ±0.25, then multiplies by lognormal noise with `turnout_noise_sd =
0.08`. A systematic 2pp shift on a 0.55 base is a ~3.6% relative move, half
weighted, against 8% per-draw noise. It shifts the centre of the turnout pattern
slightly and is swamped at the resolution a seat count can express.

**This is a null result and it is the useful kind.** It says the seven cities'
turnout staleness was a real defect in the inputs and was *not* a defect in any
published number — which is a much stronger statement than "we fixed it", and it
could not have been made without measuring. It also bounds how much the turnout
pattern is doing: a 2pp systematic per-VD error is invisible in seats, so the
turnout channel is not where remaining seat error lives.

**What is NOT established:** that the refresh is harmless in general. It was
measured on the 24-city-year backtest at 1000 draws. A different draw count, a
different scenario, or the 2026 forecast were not tested here.
