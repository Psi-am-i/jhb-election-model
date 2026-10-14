# 2. Recheck of 1j v2

Recheck of `step1/1j-universal-draw-design-v2.md` (e8666e6) against my review
`2-review-1j.md` (ded5d5d). Read-only on code: no model run, no
`compare_history`, no emit, nothing under `data/` written, no sub-delegation.
My scripts are in the session scratchpad, `review1j/`. They are my own code,
none of `uni2/` is imported, and they read the same row files as before.

- `v2w.py`: v2's width function, implemented independently.
- `r21`-`r27.py`: the recomputations.
- `q1.py`: the 1-5% discrepancy.

**Labels.** *Measured* = computed by my scripts. *Argued* = reasoning or code
reading. *Citywide simulation* = my reimplementation of the v2 draw:

- normal own term, ρ(s) by size group, pooled increments;
- arm E's pool-turnout draws for composition;
- κ solved on an independent calibration sample;
- no IPF, water-fill or ward path.

My widths skip v2's location fixed point (§2.3), which moves them by ≤ 0.025.

## Verdict

**Needs another revision.** It is a small one: two blocking items, both cheap.

1. **The 5-20% bridge is built wrong.** The large anchor sits at 20%, against
   v2's own rule that each anchor sits at the geometric centre of its rows
   (finding A). As built, the bridge is about 1.8 times too narrow in sd where
   the record has cases.
2. **§11 adds a second way to state a party's centre.** The judgement files
   already take one, so this does not meet the owner's "one consistent way".
   Its width term also says something the record contradicts (finding B).

Everything else in v2 answers my review correctly, and the decisive numbers
reproduce.

---

## 1. My findings, one by one

| # | v2's fix | verdict | evidence (measured unless marked) |
|---|---|---|---|
| 1 | §8 recomputed under a normal own term | **correct** | Johannesburg 2026, 4 seeds, v2 widths: established, previous share < 1%, above 5%: 24.0 (sd 1.9), v2 24. Above 3.48%: 96.2 (v2 94). Rate above 2%: 0.0058 (0.0057). Retained < 14.6%: 0.074 (0.075). Median retained: 0.63 (0.62). Any centre < 1% above 5%: 59.8 (v2 60). Largest new party above 18.12%: 285 (292). Per-party log-sd matches v2 §8.2 to 0.01 for all ten parties. All of this rests on the bridge; see A |
| 2 | normal own term; t as an arm with calibrated location | **correct and sufficient** | `o(σ) = −σ²/2` is exact for a normal; the t arm's location is no longer a moment of `exp(t)` |
| 3 | per-party z on the run's own SE, Bonferroni at 0.01 | **correct** | 20 independent calibration/run pairs: z rule 0 false alarms; fixed 5% rule 5 (v2: 7). Threshold 3.49 at 21 parties. SE median 0.020, max 0.030 (v2 identical). Power, 10 pairs: IFP (1.50%) ×1.1 detected 8, ×1.2 10; UDM (0.16%) ×1.1 6, ×1.2 10 (v2: 9, 10, 7, 10). Errors under about 10% at small parties pass, as v2 states |
| 4 | ρ(s) by size group, complementary own term | **correct** | between-city-year share, < 1% / 1-20%: 2016 0.39 / 0.00, 2021 0.37 / 0.00, 2026 0.47 / 0.00 (v2: 0.39, 0.37, 0.46; 0.00). 1-5% alone: 0.00. The complement keeps totals. New consequence in note C3 |
| 5 | band roots below 5%, one estimator, curve withdrawn | **correct below 5%**; the bridge above it is not (A) | before the fixed point, 2026: 1-5% 0.834 (35 cases / 18 party-elections), 0.3-1% 0.817 (88/35), 0.1-0.3% 0.910 (61/37), < 0.1% 0.995 with no root (41/34), large anchor 0.053 (44). v2 after the fixed point: 0.840, 0.821, 0.901, 0.998, 0.053. 2021 and 2016 within 0.02 |
| 6 | closed-form increments, MIN_EFF, one pooled debutant value | **fix correct; one claim in the record wrong** | under v2 widths, before the fixed point: pooled debutants 0.499 (2026), 0.855 (2021), 0.845 (2016); < 1% 0.42; ≥ 1% 0.69; seeds 0.856. v2 after the fixed point: 0.472, 0.832, 0.787, 0.385, 0.692, 0.84. Pooled 2026 bootstrap 90% 0-0.87, 19% at zero (v2: 0-0.90, 27%). **Wrong:** v2 says v1's 0.05 "was also an artefact of the iteration: the closed form gives 0.39" (§0 row 6, summary point 4). The closed form under v1's curve gives 0.052, roots 0.003 and 2.629 (`r7.py`, in my review). The 0.39 comes from v2's narrower band widths. Only the 2016 COPE-only value was a solver failure. Correct both places |
| 7 | bootstrap over party-city-years, by city-year | **correct** | CRPS bootstrap not re-run. Coverage reproduced: large 16/16 (2016), 12/16 (2021; v2 13/16); middle 5-15% 14/14 (v2 13/14) |
| 8 | seed formula `ω² = σ² + δ_seed² − σ_arr² − v_comp` | **correct** | — |
| 9 | estimator ↔ calibration fixed point | **acceptable** | not re-derived. My earlier gaps (+0.04 to +0.10) agree in size with v2's Δ (median +0.045). It is model-internal and reads no outcome |
| 10 | PA prose | **correct** | — |
| 11 | consumers | **correct** | all listed. `LEVEL_DF` row added |
| 12 | middle-width arm | **present, but A makes it the less arbitrary main choice** | — |
| N1-N8 | | **accepted**; N4's rejection is reasonable | N4: the rebuttal answers imputation at half a vote, not a censored likelihood. Given 16 cases at centres ≤ 0.17% and no seat at stake, reporting the count is acceptable |

---

## 2. New in v2

### A. The 5-20% bridge puts the large anchor at 20%. **Blocking.**

v2 §2.1 places each band's width at its geometric centre (2.24%, 0.55%, 0.17%,
0.05%). The one exception is the large anchor. It is the within-block residual
of parties at 20.4-60%: 44 cases, median centre 40.4%, geometric mean 38.8%. v2
places it at 20%. Because the bridge is linear in log size between 2.24% and
20%, that placement alone sets every width in 5-20%.

Measured: residuals of established parties in 5-20% (2011-2021, 12 cases, 5
party-elections), standardised by the width being tested. A width that fits
gives a weighted mean of `u²` near 1.

| width in 5-20% | weighted mean of `u²`, 5-20% established | σ at 11.7% (ASA) | σ at 15% | σ at 26% (DA) |
|---|---|---|---|---|
| v1 curve | 1.15-1.25 | 0.28 | ~0.2 | 0.07 |
| **v2 bridge, large anchor at 20%** | **3.27** (2.52 without the two single-block DA 2011 rows) | 0.244 | 0.156 | 0.053 |
| large anchor at its rows' geometric mean, 38.8% | 1.37 | 0.381 | 0.313 | 0.16 |
| two large anchors from the record: 0.074 at 25% (rows 20-30%, n 12) and 0.044 at 45% (rows ≥ 30%) | 1.81 | 0.313 | — | 0.072 |
| band's own root as an anchor (v2's arm) | ≈ 1 by construction | — | — | — |

The within-block residual itself depends on size: RMS 0.074 at 20-30% (n 12),
0.048 at 30-45% (15), 0.039 at 45%+ (17). One anchor value at 20% fixes the
bridge at the narrowest end of a quantity that widens as size falls.

At Johannesburg 2026, with the anchor at 38.8% (citywide simulation, seed 7):

| party | log-sd, v2 bridge | log-sd, anchor at 38.8% |
|---|---|---|
| ASA | 0.23 | 0.35 |
| EFF | 0.26 | 0.38 |
| MK | 0.53 | 0.60 |
| PA | 0.48 | 0.56 |
| DA | 0.12 | 0.18 |
| ANC | 0.11 | 0.19 |

Draws whose largest new party exceeds 18.12% go from 292 to 355.

The backtest evidence that favours a narrow middle is one party-election: EFF
2021, seven metros with residuals −0.25 to +0.09. That is why v2's §8.4 arm
scores worse on middle CRPS. The in-band record says wider.

Fix:

- place the large anchor by the same rule as every other anchor (its rows'
  geometric centre), or use two large anchors measured from the record;
- regenerate §8;
- state the middle as a judgement call. Both sides rest on at most five
  party-elections. The owner decides between the bridge and the band root,
  with both results shown.

### B. §11 strength judgements. **Blocking against the owner's requirement.**

The rule's structure is sound:

- one entry form for any class;
- the judged centre goes into the level vector, and the calibration conserves it;
- the register guard runs in both directions;
- no code path names a party;
- backtests refuse entries, and forecasts report with and without them.

The rule also has a size-consistent width, so a collapse to 2% takes a 2%
party's width. Four problems:

1. **There is already a second way to state a centre.** `judgements/<city>-<year>.toml`
   takes `[party.X] support = …` and `overperform = …`. `pools.py:4925-4937`
   reads them to size a seeded arrival ("pools and support DECLARED in
   judgements/", "after a ×{mult} judgement"). §11 adds `[strength.X]
   centre_share` / `centre_ratio` beside them. Two entry points for one kind of
   judgement is what the owner ruled out. No file declares `support` or
   `overperform` today (checked: none of the 26 files). Fix: §11 retires both
   keys, or defines them as the strength entry, and states which survives.
2. **The meaning of σ_J would double-count.** §11.1 says `σ(c_J)` is "how far
   parties of that size move even when the centre is right". It is not. It is
   measured as dispersion about the model's own centres, so it already
   contains the model's centre error; v1 §4 says so ("centre error, the E[k²]
   reading"). An owner who enters σ_J as "how uncertain my judgement is" counts
   centre error twice. Fix: define σ_J as the judgement's uncertainty **in
   excess of** the model's centre error for an established party of that size.
   That is the role δ_deb and δ_seed play, so replacing them stays consistent.
   A judgement as good as the model's then has σ_J = 0. Say this in the
   register row's template.
3. **The arrival factor is kept for a judged seed.** σ_arr is the city-year
   common part of the seed sizing rule's error, carved out of σ² + δ_seed².
   Once δ_seed is replaced by σ_J, keeping σ_arr keeps part of the replaced
   rule's error. v2's own script disagrees with the text: `uni2/v2.py`
   `components` returns an arrival loading of 0 for a judged party, while §11.1
   point 3 keeps it. Fix: drop it for a judged party and say so (argued).
4. **File and key mechanics.** Two problems with keeping the entry in the
   target's judgements file:
   - `pools._judgements_sha` hashes the parsed file into every spec's
     `artefact_key` (`pools.py:283`, `480`). Adding or editing a strength entry
     therefore marks the spec stale and forces a batched re-emit (CLAUDE.md
     §3), and "the same forecast without judgements" needs a second spec.
   - "Backtest targets refuse any `strength` table" means that when 2026
     becomes a backtest, `joburg-2026.toml` makes it refuse to run.

   Fix: exclude `[strength.*]` from `_judgements_sha` and key it at run time,
   since §11 applies it after the emit, before `pool_spec`. And make a backtest
   ignore the table, recording that it did, rather than refuse.

**Contamination of backtests (argued, from the design and code):** none
through the width record, which reads only backtest targets and model centres.
The two routes left are the refusal trap in B4 and a judgement revised after
seeing backtest scores. §11.2 forbids the second, but nothing can enforce it.
Record each entry's date against the run date in `35_widths`.

### C. Smaller new points

- **C1. The stop rule cannot fire.** §2.4 says "A band root outside its
  bootstrap interval of the interpolated value stops the writer". Every
  non-thin band is an anchor, so the interpolated value at its centre equals
  its root by construction. The one band where it could disagree (5-20%) is
  exempt as thin. It is a guard that cannot see (CLAUDE.md §4, part 2). Fix:
  test each band against the interpolation built without it (leave one band
  out), and apply the check to 5-20% with its own interval.
- **C2. §0's explanation of the 1.01 is wrong** (section 3 below). It is not
  party clustering.
- **C3. Large parties now under-move in 2021.** With no shared loading above
  about 2%, the block's movement comes only from the small parties' swing and
  independent middle own terms. Citywide simulation: drawn block log-sd median
  0.065 in 2021 against realised block RMS 0.090; large-party coverage 12-13
  of 16. v2 attributes this to a 2021 level miss shared across metros, which
  fits the record's mean of −0.063. Finding A's fix widens the large parties
  and reduces it. Declared; no further change.
- **C4. §8 must be regenerated after A**, under whichever middle width the owner
  picks. The pre-registration waits for that.

---

## 3. The 1-5% band: 1.01 against 0.83

Ran `scratchpad/mine/bands.py`: 1-5% gives n 35, mean −0.653, width 1.01. The
frame and centre are the same as mine (`ps_after`); its frame is raw
`log(act/centre)`, not block-relative. **The difference is the weight
normaliser.** `bands.py` counts a party-cycle's rows across **all** bands
(`cnt` over every established row), then applies `1/cnt` inside the 1-5% band.
v2 and I count rows **within the band**. Measured (`q1.py`, same 35 rows):

| frame | in-band party-cycle count | all-band party-cycle count |
|---|---|---|
| raw `log(act/ps_after)` | 0.802 (mean −0.414) | **1.010** (mean −0.653), `bands.py` |
| relative to block | 0.834 (mean −0.424), v2 and me | 1.041 (mean −0.668) |

Under the all-band count, a party-cycle's weight in the band is proportional
to its share of rows that fall in the band. Single-metro local parties keep
full weight (0.115 each, against 0.056 in-band):

- Minority Front 2016 (residual −1.94);
- Displacees Rate Payers 2011 (−1.45);
- Agency for New Agenda 2021 (−2.19);
- AIC 2016 (+0.66).

National parties with one stray row in the band fall to 0.014-0.016 (EFF 2021,
PAC). The three local collapses carry the mean to −0.65 and the width to 1.01.

**Which is right.** The in-band count, for a band estimate. Its weight unit is
defined on the population being estimated: each party-cycle present in the
band has equal total weight. The all-band count makes a band's width depend on
how many metros a party contested at other sizes, which has nothing to do with
the band. The sensitivity is still large: 0.80-0.83 against 1.01-1.04, from
four single-city parties. v2's §0 attributes the gap to party clustering
(0.925-0.951), which is a third convention. Fix: replace §0's explanation with
this one, and print the all-band-count variant beside party clustering in §2.4.

---

## Decisive numbers

| quantity (window, method) | v2 | mine | note |
|---|---|---|---|
| band widths 2026: 1-5 / 0.3-1 / 0.1-0.3 / < 0.1% / large | 0.840 / 0.821 / 0.901 / 0.998 / 0.053 | 0.834 / 0.817 / 0.910 / 0.995 / 0.053 | mine before fixed point |
| σ at 11.7% / 11.0% / 9% / 5.8% (2026) | 0.247 / 0.269 / 0.340 / 0.498 | 0.244 / 0.266 / 0.338 / 0.494 | reproduced; see A |
| 5-20% established, weighted mean u² under the bridge | not reported | **3.27** | A |
| 5-20% own root | 0.623 | 0.615 | |
| shared share < 1% / 1-20%, 2026 | 0.46 / 0.00 | 0.47 / 0.00 | |
| pooled debutant δ, 2016 / 2021 / 2026 | 0.787 / 0.832 / 0.472 | 0.845 / 0.855 / 0.499 | mine before fixed point |
| seed δ / σ_arr, 2026 | 0.84 / 0.73 | 0.856 / 0.73 | |
| JHB 2026: established prev < 1% above 5% | 24 | 24.0 | normal, 4 seeds |
| JHB 2026: any centre < 1% above 5% | 60 | 59.8 | |
| falsifier false alarms, z rule / fixed 5% | 0/20 / 7/20 | 0/20 / 5/20 | |
| falsifier power, 1.50% ×1.1, 0.16% ×1.1 | 9/10, 7/10 | 8/10, 6/10 | |
| large in 90%, 2016 / 2021 | 16/16, 13/16 | 16/16, 12/16 | |
| 1-5% width, `bands.py` convention | — | 1.010 raw / 1.041 relative | section 3 |

## What I checked and did not

**Checked (measured):** v2's width function at all three targets; the
standardised fit of the bridge in 5-20%; alternative anchor placements and
their Johannesburg 2026 effect; increments by closed form with a bootstrap;
shared shares by group; the Johannesburg 2026 §8.2 figures under the normal
own term; falsifier false alarms and power; backtest coverage of large and
middle parties; the `bands.py` discrepancy.

**Checked (code reading):** the judgement-file reader and key
(`pools.py:283, 480, 4925-4937`); the judgements files for `support` and
`overperform`; `uni2/v2.py` `components` against §11.

**Not done:** the location fixed point; the CRPS bootstrap figures of §8.1; the
seat proxy; the t arm; anything through the real drawer.
