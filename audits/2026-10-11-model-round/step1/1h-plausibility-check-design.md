# 1h. A plausibility check: scoring whole simulated elections against the real record

Design agent, read-only, 2026-10-11, branch `remediation` at 923efe1. Nothing in `src/`,
`tests/` or `data/` was written. No model run, no `compare_history`, no emit. Scratch
scripts: `$SCRATCH/plaus/` (`build_record.py`, `plaus.py`, `r1_record.py` … `r8_headline.py`),
where `$SCRATCH` is this session's scratchpad. They are prototypes for §5, not the instrument.

**Inputs read.** Real results: `fold.load` + `fold.citywide` over
`data/raw/elections/lge{2000,2006,2011,2016,2021}_{CODE}_vd_party_clean.csv` (the same
reader `compare_history.actual_shares` and `backtest.actual_result` use), list ballot for
shares, ward ballot for ward winners (aggregated by `ward_of` exactly as
`backtest.actual_result` does), `Registered_Population` per (VD, ward) on the list ballot
for the roll. Johannesburg 2026 roll: `archive/iec-registration-2026-09-26/` (2,417,915).
Draws: `data/arms/step11/{A,E}/<city>-<year>/arrays.npz` (`pr_share_draws`,
`pr_vote_draws`, `ward_winner_draws`; column names `meta.json` `seat_cols`), 24 backtests
at 1,000 draws and Johannesburg 2026 at 5,000.

**Label convention.** *Measured* = computed in this session from the files above.
*Argued* = reasoning, not tested. *Judgement call* = a value the record does not force,
to be registered in `JUDGEMENT-CALLS.md` before the instrument is used.

**A and E are not paired** (different column sets and draw streams, MODEL-LOG §1.296).
Each is reported on its own; no A−E difference in this document is a measured effect.

---

## 1. Features of a whole simulated election

Every feature is defined identically on a draw and on a real election, and **names no
party**: ranks, size classes and counts only (owner rule: every control applies to all
parties or none). A transition is (previous real result at t−1, election at t). For a draw,
t−1 is the real previous result and t is the draw.

### 1.1 Citywide features (one value per draw)

| # | feature | definition (unit) | what a real election says about it |
|---|---|---|---|
| 1 | `vol` | Pedersen volatility: ½ Σ\|s_t − s_{t−1}\| over every party at either election (points) | how much the vote moves in total |
| 2 | `new_share` | combined list share at t of parties absent at t−1 (points) | entry |
| 3 | `max_new` | largest list share at t of a party absent at t−1 (points) | size of the biggest arrival |
| 4 | `max_gain` | largest single-party gain, s_t − s_{t−1} (points) | |
| 5 | `max_loss` | largest single-party loss, including a party that did not stand at t (points) | |
| 6 | `enp` | effective number of parties, 1/Σs² (parties) | fragmentation level |
| 7 | `d_enp` | `enp`_t − `enp`_{t−1} (parties) | fragmentation change |
| 8 | `top1` | largest party's list share (points) | |
| 9 | `top2` | two largest parties' combined list share (points) | |
| 10-12 | `n_ge1`, `n_ge5`, `n_ge10` | parties at or above 1%, 5%, 10% of the list vote (count) | |
| 13 | `sub1_mass` | combined list share at t of parties under 1% **at t** (points) | the small-party bucket as it lands |
| 14 | `tiny_max` | largest list share at t of a party that stood at t−1 with 0 < s < 1% (points) | the tiny-party jump |
| 15 | `tiny_mass` | combined list share at t of the parties that stood at t−1 under 1% (points) | the owner's class, followed forward |
| 16 | `tiny_n_ge1` | how many of those parties reach 1% at t (count) | |
| 17 | `d_turnout` | (valid list votes / registered roll)_t − same at t−1 (points of the roll) | |
| 18 | `w_top` | share of wards won by the party winning most wards (% of wards) | ward dominance |
| 19 | `w_n` | number of parties winning at least one ward (count) | |
| 20 | `w_other` | share of wards won outside the two largest ward-winning parties (% of wards) | |

**Joint features.** (a) `J` = number of features, out of a declared core set of eight
(`vol`, `max_gain`, `max_loss`, `d_enp`, `top2`, `n_ge5`, `tiny_max`, `w_top`), on which a
draw falls outside the record's range. A draw in which several things each happen at a rate
the world has shown, but together, scores high on `J`; the world's own `J` is measured the
same way (§3c). (b) Pairs (`tiny_max`, `sub1_mass`) and (`vol`, `d_turnout`) carry the two
shape findings of §4 and are reported side by side.

### 1.2 Party-level features (one value per party per draw), by size class at t−1

Classes by list share at t−1: under 1%, 1-3%, 3-10%, 10-30%, 30% and over (judgement call:
the bands; §5 registers them). Per class:

| feature | definition |
|---|---|
| retained ratio | s_t / s_{t−1} for a party standing at both elections |
| collapse | retained ratio below the record's lowest for that class |
| jump | retained ratio above the record's highest for that class |
| threshold events | s_t ≥ 2%, ≥ 5%, ≥ 10% for a party under 1% at t−1 |
| class mass | Σ s_t / Σ s_{t−1} over the class's members standing at both (log) |

Exits (stood at t−1, not at t) have no draw counterpart: in a backtest the roster is the
target's own and in 2026 it is the certified list, so a draw never contains a party that
did not stand. Exits are therefore kept out of every ratio population and reported as a
count only (§2.1).

### 1.3 Mismatches between draws and record, stated where they bite (measured)

- **Normalisation.** `pr_share_draws` rows sum to 1 over the model's columns; the record
  sums to 1 over every party on the ballot. The realised list vote in parties with no model
  column (arm E) is 0.00 at every 2016 and 2021 backtest, and 0.25-4.87 points at the 2011
  backtests, where the largest such party is the 2011 arrival the `ENTRANT` slot stands for
  (eThekwini 4.48, Ekurhuleni 1.13). Counting only column-less parties under 1%, the 2011
  gap is 0.25-1.27 points (Johannesburg 1.27, Cape Town 1.01). This affects `sub1_mass` at
  2011 only, and by less than the gap §4 reports.
- **Previous-election parties missing from the draws** count as losses (`vol`,
  `max_loss`), as in reality: the Independent Democrats at Cape Town 2006 (11.02%, merged
  into the DA by 2011) and the NFP at eThekwini 2011 (4.48%, off the 2016 ballot).
- **`ENTRANT`** at the 2011 runs is a party absent at t−1, so it enters `new_share` and
  `max_new` without relabelling; no feature depends on its label.
- **Turnout.** Drawn turnout = Σ `pr_vote_draws` / the target's registered roll (backtests:
  the roll in the target's own result file; 2026: the IEC snapshot). Same unit as the
  record (valid list votes over the roll).
- **Ward features in 2000.** Ward features are within-election shares, so the 2000
  delimitation does not enter a comparison across elections.

---

## 2. The reference distribution

### 2.1 What exists (measured)

Five local elections per metro are on disk (2000, 2006, 2011, 2016, 2021): **32
consecutive transitions** (8 metros × 4 cycles). The 2000 files for seven metros are held
back from the *model* by `levels.HELD_BACK`, "ingested and correct; held pending diagnosis
of a … regime effect". That is a reason about the model's prior, not about the data, so the
2000→2006 transitions are admissible to a judge of plausibility (CLAUDE.md §1: real
elections are the standard). The instrument and the model therefore deliberately read
different record sets; the instrument says so in its output.

Party-transitions in the record, all four cycles:

| class at t−1 | party-transitions | exits (did not stand at t) | stood at both | retained ratio p5 / median / p95 | lowest / highest retained ratio | reached ≥2% at t | reached ≥5% at t | largest share at t |
|---|---|---|---|---|---|---|---|---|
| under 1% | 378 | 173 | 205 | 0.26 / 0.78 / 3.89 | 0.146 / 17.30 | 2 | 0 | 3.48% |
| 1-3% | 64 | 7 | 57 | 0.20 / 0.60 / 1.54 | 0.087 / 3.95 | 6 | 1 | 7.79% |
| 3-10% | 23 | 1 | 22 | 0.14 / 0.90 / 1.73 | 0.093 / 2.98 | 13 | 6 | 12.37% |
| 10-30% | 23 | 1 | 22 | 0.63 / 0.96 / 1.67 | 0.350 / 1.70 | 22 | 21 | 40.24% |
| 30% and over | 47 | 0 | 47 | 0.73 / 0.90 / 1.22 | 0.662 / 1.45 | 47 | 47 | 81.33% |

(The ratio quantiles for the two largest classes are exp of the log-ratio quantiles
measured in `r5_party.py`.) MODEL-LOG §1.296 counted 337 sub-1% cases over three pairs;
adding 2000→2006 gives 378, and the two that reached 2% are still the same two (VF Plus,
Ekurhuleni 2016→2021, 0.90%→3.48%; the PA, Johannesburg 2016→2021, 0.17%→2.96%).

Citywide features of the 32 transitions (measured; range within each cycle, then all 32):

| feature | 2000→06 | 2006→11 | 2011→16 | 2016→21 | all 32: min / median / max |
|---|---|---|---|---|---|
| `vol` (pts) | 1.65-17.36 | 8.59-22.26 | 11.13-17.73 | 8.56-26.86 | 1.65 / 13.43 / 26.86 |
| `new_share` (pts) | 1.15-12.62 | 1.64-7.52 | 4.89-13.69 | 3.67-20.93 | 1.15 / 6.06 / 20.93 |
| `max_gain` (pts) | 0.66-12.01 | 4.25-18.89 | 5.60-11.64 | 2.09-18.12 | 0.66 / 7.21 / 18.89 |
| `max_loss` (pts) | 1.32-11.02 | 1.70-15.48 | 4.48-14.98 | 3.96-16.60 | 1.32 / 8.33 / 16.60 |
| `enp` | 1.48-2.93 | 1.92-2.29 | 1.97-2.76 | 2.38-4.54 | 1.48 / 2.36 / 4.54 |
| `d_enp` | −0.52-0.62 | −0.86-0.44 | −0.09-0.63 | 0.01-1.78 | −0.86 / 0.20 / 1.78 |
| `top2` (pts) | 75.79-93.27 | 83.84-95.20 | 82.96-91.28 | 58.68-80.00 | 58.68 / 85.61 / 95.20 |
| `n_ge1` | 4-7 | 3-5 | 4-6 | 5-10 | 3 / 5 / 10 |
| `sub1_mass` (pts) | 1.28-4.86 | 1.67-4.31 | 1.81-4.48 | 3.67-9.55 | 1.28 / 3.60 / 9.55 |
| `tiny_max` (pts) | 0.13-1.43 | 0.00-0.62 | 0.31-1.83 | 0.70-3.48 | 0.00 / 0.59 / 3.48 |
| `tiny_mass` (pts) | 0.13-3.94 | 0.00-1.77 | 0.93-2.93 | 1.69-7.56 | 0.00 / 1.69 / 7.56 |
| `d_turnout` (pts of roll) | −7.12-2.07 | 3.73-15.23 | −1.50-3.91 | −17.29 to −10.01 | −17.29 / −0.90 / 15.23 |
| `w_top` (% wards) | 58.1-91.1 | 56.7-86.0 | 60.0-90.0 | 61.7-84.0 | 56.7 / 69.7 / 91.1 |
| `w_other` (% wards) | 0-12.0 | 0-7.8 | 0-6.4 | 0-3.7 | 0 / 0 / 12.0 |

### 2.2 Out of sample: which record judges which target

**Primary (strict):** a target at year T is judged only by transitions ending at or before
T−5. That gives 8 transitions for a 2011 target (2000→06, one cycle), 16 for 2016, 24 for
2021, and 32 for Johannesburg 2026. **2011 rows are judged against one cycle** and are
labelled so in every table.

**Sensitivities, reported alongside, never substituted:** `strict06` (as strict without
2000→06: 2011 targets cannot be judged at all; 2016 by 8; 2021 by 16) and `loco` (every
cycle but the target's own: 24 for each backtest). `loco` uses later elections to judge an
earlier draw. That is admissible for a question about the world ("could this happen?") and
inadmissible for scoring a forecast; the PIT component (§3b) never uses the record at all,
so the temporal discipline of forecast scoring is not at stake in either mode.

### 2.3 The small sample: the world leaves its own record (measured)

The decisive fact for the design. Each real transition was judged by the record that the
same rule would have given it (strict: earlier cycles; loco: other cycles), and counted
outside the range or more than one record IQR beyond it:

| feature | strict: outside range / 24 | strict: beyond range ± 1 IQR / 24 | loco: outside range / 32 | loco: beyond ± 1 IQR / 32 | exchangeable expectation, outside range |
|---|---|---|---|---|---|
| `vol` | 3 | 2 | 6 | 1 | strict ≈ 3.4 of 24; loco ≈ 2.6 of 32 |
| `max_gain` | 2 | 2 | 2 | 0 | |
| `max_loss` | 3 | 1 | 2 | 0 | |
| `enp` | 5 | 4 | 7 | 4 | |
| `d_enp` | 7 | 5 | 5 | 4 | |
| `top2` | 8 | 3 | 8 | 3 | |
| `n_ge1` | 6 | 2 | 6 | 2 | |
| `sub1_mass` | 5 | 1 | 6 | 1 | |
| `tiny_max` | 4 | 3 | 3 | 2 | |
| `tiny_mass` | 5 | 4 | 5 | 4 | |
| `d_turnout` | **16** | **7** | **15** | 0 | |
| `w_top` | 1 | 0 | 2 | 0 | |
| `w_n`, `w_other` | 0 | 0 | 0-1 | 0-1 | |

(Exchangeable expectation for the range rule = Σ 2/(n_t+1) over the judged transitions.)

What this resolves and what it does not:

| question | resolvable from the record? | why |
|---|---|---|
| Is the record's range the boundary of the possible? | **No — refuted by the record.** | Real transitions fall outside the earlier range more often than exchangeability predicts on six features, and beyond range + 1 IQR on several. |
| Features driven by a common national swing (`d_turnout`, `top2`, `enp`, `d_enp`) | **Only coarsely.** | The 8 metros move together within a cycle (2016→21: turnout down 10-17 points in every metro). The effective sample for the cycle component is **4 cycles**, not 32 transitions, so the size of the next cycle's common shock is not resolvable. |
| Metro-specific features and the party-level shape (retained ratio, threshold events, class mass) | **Yes, at the rates in §4.** | Hundreds of party-transitions, clustered in 32 city-transitions; intervals must be cluster-bootstrapped over the 32. |
| Johannesburg 2026 level features (`enp`, `top2`, `w_other`) | **Not from the local record alone.** | The record's extreme on each is Johannesburg 2021 itself, and the 2024 national election in Johannesburg has already gone past it: list ENP 4.99, top two 56.9 points, against the local record's 4.54 and 58.68 (measured, `npe2024_JHB` read with no ballot filter; a rough figure). |

**How far beyond (the rule).** Three tiers, all relative to the world rather than to a wall:

1. **Rate beyond the range.** Under exchangeability a new real value exceeds the max of n
   with probability 1/(n+1), and the min likewise. A model whose draws are world-like puts
   about that share of draws beyond each end; 0% is as much a failure as 30%.
2. **Distance beyond, in record IQRs.** The share of draws more than 1 IQR beyond the range
   is reported (judgement call: k = 1). §2.3 shows the world itself breaches k = 1 on
   cycle-driven features, so this tier is descriptive, never a pass/fail line on its own.
3. **The calibrated event test (decisive).** "Outside the envelope" is turned into a binary
   event per target. The model assigns it a probability p_t (its share of draws outside);
   the world produced it or not. Under a calibrated model the realised count across the 24
   targets is Poisson-binomial(p_1…p_24). A model that puts mass beyond the record more
   often than the world goes there fails in the lower tail; one too narrow fails in the
   upper tail. This lets a draw exceed anything seen while still bounding how often.

The independence across targets that the Poisson-binomial assumes fails for the
cycle-driven features (three backtest cycles), so their p-values are anti-conservative
(argued). The instrument prints a "cycle-driven" flag beside those rows.

---

## 3. Scoring

Per feature and per arm:

**(a) Envelope exceedance.** Share of draws below the record min and above the record max
(per target, averaged over targets with equal weight), against the exchangeable rate
1/(n_t+1) per side; share beyond range ± 1 IQR. The envelope is a function of the real
record and the target year only.

**(a′) Calibrated event test.** E[count outside] = Σ p_t against the realised count;
report P(X ≤ obs) (model too wide) and P(X ≥ obs) (model too narrow). Same for the ± 1 IQR
event.

**(b) Calibration of the realised outcome.** Randomised PIT of the realised feature among
the target's draws, 24 per feature. Reported as counts, because 24 points cannot support a
distribution test: inside the central 50% (expect 12, s.e. ≈ 2.4), inside the central 90%
(expect 21.6, s.e. ≈ 1.5), below 5% and above 95% (expect 1.2 each).

**(c) Joint.** Per draw `J`; the world's realised `J` per target under the same rule;
event test on `J ≥ 2` and `J ≥ 3`.

**(d) Party level.** Per class: collapse and jump rates per party-draw against 1/(n+1);
threshold-event rates per party-draw against the record's count with a Wilson or
rule-of-three bound, cluster-bootstrapped over city-transitions; class-mass dispersion
against the record's; PIT of the realised class mass.

### 3.1 Estimation or tuning

| quantity | defined from | if used to SET a parameter it would be |
|---|---|---|
| record envelope, record quantiles, record retained-ratio distribution, record class-mass dispersion, record threshold-event rates | real elections only | **estimation** — a property of the world (CLAUDE.md §4). Permitted, but then that feature is in-sample and leaves the check: a parameter estimated from a feature cannot be judged by it. |
| share of draws outside the envelope; E[count] vs realised | model output against the record | **tuning** — a ratio against our own output, the `k*` case |
| PIT and coverage of the realised outcome | model output | **tuning** |
| `J` and its event test | model output | **tuning** |

**The check judges and sets nothing.** Enforcement (§5): no module the model imports may
import the instrument; its outputs carry an artefact key and are read by no code path
that produces a draw. If a later round estimates, say, the small-party retained-ratio
spread from the record, that feature moves to an "estimated from" list in the instrument's
config and is reported as in-sample, and a held-out cycle replaces it as the judge.

### 3.2 Decision rules proposed for this round's pre-registration (argued, for the coordinator)

A change is scored by how it moves each row of §4 from the arm-E baseline, on paired draws
once paired streams exist (step 1c):

1. A feature **fails** when its event test gives P(X ≤ obs) < 0.05 (draws leave the record
   more often than the world) or P(X ≥ obs) < 0.05 (less often), or when its central-90%
   PIT count is outside 18-24 of 24. Cycle-driven rows are reported, not failed.
2. A party class **fails** when its collapse or jump rate exceeds three times 1/(n+1), or
   when its threshold-event rate exceeds the record's rule-of-three bound.
3. A change "makes the simulations more plausible" when it removes failures without adding
   any; a change that adds a failure must explain it (ITERATING.md, "more honest usually
   ships").
4. The 2026 rows are judged on features with a national-election supplement only (§2.3);
   level features at 2026 are reported as "beyond the local record", never as failures.

**What each change of this round should move (argued; to be fixed in the pre-registration
before any run).** Directions are relative to the arm-E baseline of §4.

| change | rows expected to move, and which way | rows that must not move (beyond paired-draw noise) |
|---|---|---|
| paired draw streams | none: each party's distribution is unchanged by design | every row; the only effect is a smaller spread of between-arm differences |
| tiny-party class at the 1% line | under-1% collapse rate down; under-1% median retained ratio up toward the record; `sub1_mass` realised-above-95% count down; `tiny_n_ge1` expected count up; under-1% class-mass sd down toward the record; 2% threshold rate down; `tiny_max` event test toward calibration | the 10-30% and 30%-and-over rows; `top1`; ward rows |
| level-shrink correction | 30%-and-over collapse rate; `max_loss`; `vol`; `top1`/`top2` PIT counts | under-1% threshold-event rates; class-mass rows |
| census-composition change | ward rows (`w_top`, `w_n`, `w_other`); possibly `d_turnout` through pool weights | party-level retained-ratio and threshold rows |

---

## 4. Baseline: arms A and E (measured)

24 backtests (strict mode unless named) and Johannesburg 2026 (judged by all 32). Draw
columns are averages of per-target shares, each target weighted equally. "Exch." is the
exchangeable rate per side, averaged over targets (2011 targets n = 8, 2016 n = 16, 2021
n = 24). The rightmost three columns are Johannesburg 2026.

### 4.1 Arm E (the batch)

| feature | draws < min % | draws > max % | exch. per side % | beyond ± 1 IQR % | E[outside] | realised outside /24 | P(X ≤ obs) | P(X ≥ obs) | PIT in central 50% /24 | in central 90% /24 | PIT < .05 | PIT > .95 | 2026 < min % | 2026 > max % | 2026 beyond ± IQR % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `vol` | 0.0 | 30.3 | 7.0 | 18.3 | 7.3 | 3 | **0.014** | 0.998 | 13 | 22 | 1 | 1 | 0.0 | 49.9 | 12.8 |
| `new_share` | 2.7 | 21.6 | 7.0 | 12.9 | 5.8 | 4 | 0.236 | 0.904 | 10 | 21 | 2 | 1 | 0.0 | 17.2 | 3.9 |
| `max_new` | 3.8 | 17.3 | 7.0 | 10.5 | 5.1 | 3 | 0.185 | 0.938 | 10 | **17** | 6 | 1 | 0.0 | 5.1 | 0.6 |
| `max_gain` | 0.0 | 17.0 | 7.0 | 11.7 | 4.1 | 2 | 0.114 | 0.979 | 16 | 22 | 1 | 1 | 0.0 | 5.0 | 0.4 |
| `max_loss` | 0.3 | 29.4 | 7.0 | 16.1 | 7.1 | 3 | **0.026** | 0.995 | 16 | 22 | 2 | 0 | 0.0 | 18.4 | 2.5 |
| `enp` (c) | 0.2 | 28.5 | 7.0 | 12.1 | 6.9 | 5 | 0.215 | 0.922 | 12 | 23 | 0 | 1 | 0.0 | 90.6 | 70.7 |
| `d_enp` (c) | 2.8 | 33.2 | 7.0 | 17.1 | 8.7 | 7 | 0.296 | 0.846 | 12 | 23 | 0 | 1 | 0.5 | 20.8 | 7.5 |
| `top1` | 15.8 | 0.2 | 7.0 | 1.8 | 3.8 | 4 | 0.683 | 0.570 | 18 | 24 | 0 | 0 | 81.1 | 0.0 | 0.1 |
| `top2` (c) | 24.8 | 1.5 | 7.0 | 8.7 | 6.3 | 8 | 0.890 | 0.246 | 13 | **18** | 1 | 5 | 85.5 | 0.0 | 30.1 |
| `n_ge1` | 2.9 | 8.1 | 7.0 | 2.5 | 2.6 | 6 | 0.991 | **0.036** | 12 | 20 | 2 | 2 | 0.0 | 31.0 | 13.8 |
| `n_ge5` | 0.0 | 4.9 | 7.0 | 2.7 | 1.2 | 1 | 0.670 | 0.713 | 8 | 20 | 4 | 0 | 0.0 | 54.8 | 13.8 |
| `n_ge10` | 0.3 | 2.5 | 7.0 | 2.8 | 0.7 | 1 | 0.854 | 0.508 | 10 | 22 | 2 | 0 | 0.0 | 9.4 | 0.2 |
| `sub1_mass` | 30.0 | 3.4 | 7.0 | 0.3 | 8.0 | 5 | 0.069 | 0.982 | **3** | **8** | 0 | **16** | 2.1 | 0.0 | 0.0 |
| `tiny_max` | 10.0 | 35.4 | 7.0 | 26.7 | 10.9 | 4 | **0.001** | 1.000 | 14 | 22 | 1 | 1 | 0.0 | 16.2 | 12.4 |
| `tiny_mass` | 9.2 | 21.6 | 7.0 | 12.5 | 7.4 | 5 | 0.173 | 0.932 | 17 | 23 | 0 | 1 | 0.0 | 9.8 | 5.8 |
| `tiny_n_ge1` | 0.0 | 2.8 | 7.0 | 2.8 | 0.7 | 3 | 0.997 | **0.027** | 9 | 20 | 1 | 3 | 0.0 | 1.3 | 1.3 |
| `d_turnout` (c) | 10.1 | 8.3 | 7.0 | 0.0 | 4.4 | 16 | 1.000 | **0.000** | **0** | **0** | 8 | 16 | 0.0 | 0.0 | 0.0 |
| `w_top` | 8.7 | 1.3 | 7.0 | 1.4 | 2.4 | 1 | 0.267 | 0.940 | 20 | 23 | 0 | 1 | 61.5 | 0.0 | 24.9 |
| `w_n` | 0.1 | 0.0 | 7.0 | 0.0 | 0.0 | 0 | 0.978 | 1.000 | 9 | 19 | 0 | 5 | 0.0 | 53.6 | 16.5 |
| `w_other` | 0.0 | 2.1 | 7.0 | 1.5 | 0.5 | 0 | 0.592 | 1.000 | 15 | 21 | 0 | 3 | 0.0 | 51.2 | 45.6 |

(c) = cycle-driven; event-test p-values anti-conservative (§2.3). Bold = outside the §3.2
rule.

Joint `J` (eight core features), arm E: draws with J ≥ 1 71.2%, J ≥ 2 47.2%, J ≥ 3 34.3%,
J ≥ 4 23.5%. Realised J over the 24 targets: 11 at 0, 6 at 1, 1 at 2, 3 at 3, 3 at 4.
J ≥ 2: realised 7 against the model's expected 11.3, **P(X ≤ 7) = 0.033**; J ≥ 3: 6
against 8.2, P = 0.197. Johannesburg 2026: J ≥ 1 93.0%, J ≥ 2 80.3%, J ≥ 3 60.5% (mostly
the level features of §2.3's last row).

### 4.2 Arm A (before the batch)

Same columns; rows where A differs from E by more than a few tenths of a point:

| feature | draws > max % | beyond ± IQR % | E[outside] | realised | P(X ≤ obs) | P(X ≥ obs) | PIT 50% / 90% | PIT > .95 | 2026 > max % | 2026 beyond ± IQR % |
|---|---|---|---|---|---|---|---|---|---|---|
| `vol` | 30.3 | 17.9 | 7.3 | 3 | **0.014** | 0.998 | 13 / 22 | 1 | 60.9 | 18.8 |
| `max_loss` | 28.9 | 15.8 | 7.0 | 3 | **0.028** | 0.994 | 17 / 23 | 0 | 24.4 | 4.3 |
| `sub1_mass` (draws < min 34.4%) | 2.4 | 0.1 | 8.8 | 5 | **0.021** | 0.996 | **5 / 8** | **16** | 0.0 | 0.0 |
| `tiny_max` | 31.4 | 23.4 | 11.2 | 4 | **0.001** | 1.000 | 13 / 24 | 0 | 12.8 | 9.7 |
| `n_ge1` | 6.5 | 1.9 | 2.4 | 6 | 0.995 | **0.023** | 11 / 21 | 1 | 37.5 | 19.3 |
| `tiny_n_ge1` | 2.1 | 2.1 | 0.5 | 3 | 0.999 | **0.012** | 11 / 17 | 4 | 0.5 | 0.5 |
| `d_turnout` | 8.3 | 0.0 | 4.4 | 16 | 1.000 | **0.000** | **0 / 0** | 16 | 0.0 | 0.0 |
| `top2` | 1.9 | 7.6 | 6.1 | 8 | 0.913 | 0.206 | 12 / **18** | 5 | 0.0 | 38.7 |
| `enp` | 26.4 | 10.7 | 6.4 | 5 | 0.313 | 0.868 | 13 / 23 | 1 | 93.9 | 79.1 |

Joint, arm A: J ≥ 2 46.9% of draws; realised 7 against expected 11.2, **P = 0.036**.
Johannesburg 2026: J ≥ 2 86.9%.

### 4.3 Party level (both arms)

Retained ratio s_t / s_{t−1}, parties with a draw column standing at both elections, the 24
backtests pooled, each target weighted equally:

| class at t−1 | record p5 / median / p95 | arm A p5 / median / p95 | arm E p5 / median / p95 | record lowest | party-draws below record lowest: A / E (exch. 1/(n+1)) | 2026 below lowest: A / E | party-draws above record highest: A / E (exch.) |
|---|---|---|---|---|---|---|---|
| under 1% | 0.26 / 0.78 / 3.89 | 0.000 / 0.179 / 5.56 | 0.000 / 0.110 / 5.28 | 0.146 | **48.1% / 52.7%** (0.5%) | **71.8% / 74.0%** | 0.6% / 0.6% (0.5%) |
| 1-3% | 0.20 / 0.60 / 1.54 | 0.000 / 0.434 / 3.35 | 0.000 / 0.439 / 3.36 | 0.087 | **27.3% / 27.5%** (1.7%) | **20.1% / 19.1%** | 3.1% / 3.1% (1.7%) |
| 3-10% | 0.14 / 0.90 / 1.73 | 0.008 / 0.779 / 2.78 | 0.008 / 0.781 / 2.81 | 0.093 | **15.7% / 15.4%** (4.3%) | no such party in 2021 | 3.9% / 4.1% (4.3%) |
| 10-30% | 0.63 / 0.96 / 1.67 | (log sd 0.36) | (log sd 0.36) | 0.350 | 1.1% / 1.1% (4.3%) | 6.6% / 7.1% | 7.1% / 6.9% (4.3%) |
| 30% and over | 0.73 / 0.90 / 1.22 | (log sd 0.23) | (log sd 0.23) | 0.662 | **10.7% / 10.6%** (2.1%) | 51.2% / 42.2% | 1.1% / 1.1% (2.1%) |

Threshold events for parties under 1% at t−1, per party-draw (backtests):

| event | record (stood at both, n = 205) | rule-of-three / Wilson 95% upper bound | arm A | arm E |
|---|---|---|---|---|
| reaches ≥ 2% | 2 of 205 (1.0%) | 3.5% | **6.14%** | **5.32%** |
| reaches ≥ 5% | 0 of 205 | 1.5% | 1.36% | 1.17% |
| reaches ≥ 10% | 0 of 205 | 1.5% | 0.23% | 0.19% |

Per-draw headlines (measured): draws containing a previously sub-1% party above the
record's largest such result (3.48%): A 9.2%, E 11.1% of backtest draws; A 12.8%, E 16.2%
of Johannesburg 2026 draws. Median per-draw share of standing sub-1% parties that keep
less than 14.6% of their previous vote (the record's lowest): A 52%, E 54% (backtests);
A 75%, E 74% (2026); at 2026, 99% of draws have half or more of them doing so.

### 4.4 The owner's tiny-party class, tested against the record

Spread of the class's combined change against the spread of its members' individual
changes, members standing at both elections (log of retained ratio; measured):

| class at t−1 | city-transitions | class mass: record sd | individual: record sd | class mass: arm A sd | class mass: arm E sd | realised class mass PIT, central 50% / 90%, arm E |
|---|---|---|---|---|---|---|
| under 1% | 31 | 0.59 | 0.84 | 1.47 | 1.23 | 17 of 23 / 22 of 23 |
| 1-3% | 29 | 0.61 | 0.72 | 1.54 | 1.57 | 18 of 21 / 21 of 21 |
| 3-10% | 18 | 0.75 | 0.91 | 1.52 | 1.48 | 10 of 14 / 14 of 14 |

(The PIT column takes the class's members as every party in the band at t−1, with a
member that did not stand at t counted at its t−1 share in the denominator and at 0 at t, in the draws and in the realised result alike; the sd columns take standing members only.)

- **The record supports a class:** in every band the class's combined change is less
  dispersed than its members' changes (0.59 against 0.84 under 1%).
- **The record does not single out 1% as the line:** the 1-3% band's class mass (0.61) is
  as predictable as the under-1% band's (0.59). The 1% line is a judgement call the
  record neither forces nor contradicts.
- **The model's class mass is about twice as dispersed as the world's** (1.23-1.57 against
  0.59-0.75) and the realised class mass sits in the middle of the draws more often than
  calibration allows (17 of 23 inside the central 50% at under 1%), which is the signature
  of draws too wide, not too narrow.

### 4.5 LOCO sensitivity (24 judging transitions per backtest)

Exchangeable rate 4.0% per side. Failures that survive: `max_loss` (P(X ≤ obs) 0.012-0.013),
`tiny_max` (0.007 A, 0.023 E), `sub1_mass` (0.028 A; 0.096 E, with PIT > .95 at 16 of 24 in
both modes), `n_ge1` (P(X ≥ obs) 0.009-0.011), `tiny_n_ge1` (0.002-0.005), `top2`
(P(X ≥ obs) 0.007-0.008, cycle-driven), `d_turnout`. `vol` weakens to 0.060-0.062. The joint
J ≥ 2 test weakens to P = 0.124-0.131.

### 4.6 What makes the current draws implausible (measured, ranked by strength of evidence)

1. **Small and mid parties collapse in a typical draw.** A party under 1% keeps a median
   11-18% of its previous vote in a draw; in the record it keeps 78%, and no party
   standing at both elections ever kept less than 14.6%. About half of these party-draws
   (72-74% at 2026) fall below that, against an exchangeable 0.5%. The same collapse at
   1-3% (27% of party-draws against 1.7%), 3-10% (15% against 4.3%) and in the largest
   class (11% against 2.1%).
2. **At the same time, a few tiny parties jump.** A sub-1% party reaches 2% in 5.3-6.1% of
   party-draws, against 1.0% in the record (upper bound 3.5%), and the largest such jump
   exceeds the record's largest in 9-16% of draws. The model expects 10.9-11.2 of the 24
   real elections to show a tiny-party jump outside the record; 4 did (P = 0.001).
3. **The two together give the wrong shape.** The small-party bucket as it lands
   (`sub1_mass`) is below the realised value in nearly every backtest (realised above 95%
   of draws at 16 of 24), while the number of previously sub-1% parties reaching 1% is
   too low (realised 3 against 0.5-0.7 expected). The world's small parties hold steady
   and occasionally drift up past 1%; the model's mostly vanish and occasionally explode.
4. **Total movement is too large.** Volatility exceeds anything the record shows in 30%
   of backtest draws; 7.3 real elections were expected outside the record and 3 were
   (P = 0.014); the largest single loss likewise (P = 0.026-0.028). Both are partly the
   collapse of item 1 summed over many parties.
5. **Draws are jointly extreme too often.** 47% of draws are outside the record on two or
   more of eight features; the real elections, judged the same way, did so 7 times in 24
   against 11.3 expected (P = 0.033-0.036; weaker in LOCO, 0.12-0.13).
6. **Turnout does not move.** Drawn citywide turnout spans about one point (p1-p99) in
   every backtest; the real change was −17 to +15 points, and no realised turnout fell in
   the central 50% of its draws. Whether this reaches seats is argued, not measured: it
   enters only through differences in turnout between pools. The drawn vote totals come
   from the turnout specification behind `fold.turnout_weights` (`src/turnout.py`), which
   this design did not read; that is the place to look.
7. **Johannesburg 2026 is beyond the local record on level features** (fragmentation, top
   two, wards won outside the top two) in most draws. The 2024 national result in
   Johannesburg is already past the local record on the first two, so these rows say the
   local record is too short, not that the draws are impossible.

Rejected claims:

| claim | evidence against it |
|---|---|
| The record's range is the boundary of the possible | §2.3: real transitions fall outside the earlier range more often than exchangeability predicts on six features |
| "0 of 337" excludes the model's sub-1% → 5% rate | At 378 cases the rule-of-three bound is 0.8% of all cases, 1.5% of the 205 that stood: the model's 1.2-1.4% per party-draw is at the bound, not decisively beyond it. The 2% event and the collapse rate are decisive. |
| The 1% line is where class behaviour begins | §4.4: the 1-3% band's class mass is as predictable as the under-1% band's |
| The small-party problem is only the upper tail | §4.3: the larger departure is the lower tail — the median draw for a sub-1% party keeps 0.11 (E) to 0.18 (A) of its previous share, against the record's 0.78 |

---

## 5. The instrument as code

### 5.1 Module `src/plausibility.py` (one writer, after this round's design is agreed)

| function | inputs | returns |
|---|---|---|
| `record(data_dir) -> dict` | the raw LGE files for the eight metros, every year in `cityconfig.CALENDAR` of type LGE that has a result file | per (city, year): list shares, ward winners, roll, valid list votes. Reads through `fold.load`/`fold.citywide` (no second parser). The ward-winner aggregation is factored out of `backtest.actual_result` into one function both call (duplication rule). **Ignores `levels.HELD_BACK` deliberately**, and its output says so. |
| `transition_features(s_prev, cols, S, t_prev, T, W) -> dict[str, ndarray]` | previous shares, draw columns, a draws×cols share matrix, previous turnout, per-draw turnout, draws×wards winner indices | the 20 features of §1.1 per row; a real election is a 1-row call (one definition for draws and record) |
| `party_ratios(s_prev, cols, S, classes) -> dict` | as above | per class: retained ratios, threshold events, class mass |
| `reference(record, target_year, mode) -> list` | `mode` ∈ strict, strict06, loco | the judging transitions; refuses (raises) when fewer than a declared minimum, never returns an empty set silently |
| `envelope(values, k) -> (lo, hi, iqr, n)` | | |
| `score_run(run_dir, record, mode) -> dict` | an arm/run directory holding `arrays.npz` + `meta.json` | per feature: rates (a), event-test inputs (a′), PIT (b), J (c); party-level (d) |
| `score_panel(run_dirs, record, mode) -> dict` | the 24 backtests (+ 2026) | aggregates, Poisson-binomial tails (numpy convolution; no scipy in `.venv`), cluster bootstrap over city-transitions for party rates |
| `main()` | `--runs DIR` (an arm root), `--mode`, `--out DIR`, `--label` | writes the outputs below |

Constants registered in `JUDGEMENT-CALLS.md` before first use (none is forced by the
record): the tiny line for features 14-16 (1%, the owner's line), the size-class bands, the
outer-envelope width k = 1 IQR, the core set for `J`, the log floor for ratios (1e-4), the
minimum judging set (8 transitions), and the §3.2 failure thresholds.

### 5.2 Outputs

`data/processed/plausibility/<label>.json` and `.md` (gitignored, like every artefact
there). The JSON carries an `artefact_key` per `src/declares.py`: git sha, the hash of
each `arrays.npz` scored, the record's file hashes, the mode, and the "record ignores
HELD_BACK" flag. It never writes into a run directory, `history.json` or any spec. Nothing
in `montecarlo`, `pools`, `levels` or any module they import may import `plausibility`
(enforced by a test, below).

### 5.3 Tests `tests/test_plausibility.py`, against the four-part rule

All inputs constructed (a synthetic three-city record and synthetic draws), never the live
tree, except one population test.

| test | part of the rule | what it asserts |
|---|---|---|
| `test_record_population_is_every_metro_and_cycle` | 0, 1 | `record()` over the real files returns exactly 8 metros × the LGE years on disk, and `reference(..., "strict")` for 2011, 2016, 2021, 2026 returns exactly 8, 16, 24, 32; both directions (no extra key, none missing). The only test that reads live files. |
| `test_draw_population_equals_array_rows` | 0, 1 | every feature array has the `arrays.npz` row count; a column count mismatch with `seat_cols` raises |
| `test_one_definition_for_draws_and_record` | 0 | a real election passed as a one-row draw matrix gives the record's features exactly |
| `test_tiny_jump_is_seen_and_unseen` | 2, 3 | synthetic draws world-like on every feature score `tiny_max` exceedance near 1/(n+1); inflating one tiny party to 10% in 20% of rows (renormalised) drives the event test below 0.01; reverting the same arrays returns it above 0.05 |
| `test_collapse_is_seen_and_unseen` | 2, 3 | same construction for the retained-ratio lower tail |
| `test_two_sided` | 1, 2 | synthetic draws with zero spread fail the upper-tail event test (too narrow); draws matching the record pass both tails |
| `test_poisson_binomial_against_enumeration` | 2 | the convolution tail equals brute-force enumeration for n ≤ 10 |
| `test_reference_refuses_short_record` | 1 | a target with fewer than the minimum judging transitions raises rather than returning an empty envelope |
| `test_nothing_that_draws_imports_the_judge` | 0 | the import closure of `montecarlo.run_model` contains no `plausibility`; a constructed module that imports it is detected, and the detector goes quiet when it is removed |

### 5.4 Size and run time (measured on the prototypes)

Not timed with a clock; observed wall time of the prototypes: building the record from the
40 raw files took on the order of a minute, features for 50 runs (2 arms × 25) under a
minute, scoring both modes seconds. The whole instrument runs in a few
minutes and needs no model run, so it can score any arm that has `arrays.npz`.

### 5.5 Records to change when it lands

`MACHINERY.md` (the instrument and what it judges), `JUDGEMENT-CALLS.md` (the constants of
§5.1), `MODEL-LOG.md` (this baseline, appended, with the prototype's numbers replaced by
the instrument's own run), `ITERATING.md` (that plausibility failures are a judging
criterion and that no parameter may be set from them), `README.md`/CLAUDE.md §5 entry for
the CLI (the standalone-module rule).
