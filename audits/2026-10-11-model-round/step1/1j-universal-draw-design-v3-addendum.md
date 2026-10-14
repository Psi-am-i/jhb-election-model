# 1j v3 addendum: wording corrections, the judgement hash, and the checkpoint list

Answers the targeted re-check `step2/2-recheck-1j-v3.md` (f61461a). v3 is kept
unedited; this addendum replaces the parts of v3 it names. No new analysis:
every number below is from v3 (`uni3/`, measured) or from the re-check, which
reproduced them. Read-only; nothing in `src/`, `tests/` or `data/` written.

## For the owner

You have one choice about how wide the middle of the ballot is, and a list of
smaller settings to approve. Each setting is shown with its value, the
evidence for it, and how it will be checked.

**The middle choice.** Neither option is clearly right on the record.

- **A** draws a straight line from the small parties to the large ones. The
  twelve middle-sized results on record do not reject it. But the same
  straight-line construction fails a check one size band lower, at 1-5%: there
  it predicts a width well below the one measured. So A needs that check
  switched off.
- **B** uses the twelve middle results directly. They come from only five
  party-elections, below the minimum of eight the design asks for elsewhere,
  so B needs that minimum waived.

Each option therefore carries one declared exception. B gives the middle
parties more uncertainty, about what the model gives them today; A gives them
a little over half of today's.

A judgement about a party's strength will also be stamped into the published
forecast. If someone later edits it, the forecast will report itself out of
date.

---

## 1. Presentation corrections to v3

### 1a. B's fit to the twelve middle results is in-sample

B's middle anchor is the width root of those same twelve results, so its fit
(mean `u²` 0.88 on the 2026 record; 0.98 on 2021 and 2016) is close to 1 by
construction. A's 1.98 is out-of-sample. The out-of-sample test of the middle
is the leave-one-band-out row for 5-20% (v3 §2.4). Under both options the
interpolation built without the band falls inside the band root's 90% interval:

| | interpolation without the band | band root's interval | verdict |
|---|---|---|---|
| A | 0.386 | 0.204-0.750 | quiet |
| B | 0.387 | 0.209-0.758 | quiet |

**So the middle record rejects neither option.** What separates them is the
1-5% leave-one-band-out test. Under A it fires: root 0.840, interpolation
without it 0.575, interval 0.617-0.968. The 2021 record gives the same result
(0.822 against 0.591, interval 0.606-0.950). That test says width does not fall
in a straight line in log size from 0.5% to 25%. Under B it is quiet.

This replaces:

- the v3 summary's "It fits the twelve middle-sized results … too narrowly …
  It fits them";
- v3 §2.3's "B is the construction that passes every record test".

### 1b. Each option carries one declared exception

- **A:** the 1-5% leave-one-band-out stop check must be exempted, because it
  fires.
- **B:** the 5-20% root rests on 5 party-elections against the design's
  minimum `MIN_EFF` = 8, and on 4 in the 2011-only record used for the 2016
  backtest. Using it is an exception to that minimum.

Both exceptions are declared in JUDGEMENT-CALLS beside the middle-width row
(§3).

### 1c. Spread against today's model, Johannesburg 2026

Each option's log spread divided by arm E's, citywide simulation, seed 7. This
replaces the v3 summary table:

| option | DA | ANC | ASA | EFF |
|---|---|---|---|---|
| A | 0.62 | 0.38 | 0.56 | 0.54 |
| B | 0.76 | 0.50 | 0.88 | 0.84 |

## 2. Writer's order: the judgement hash (re-check 2c)

Taking the strength keys out of the pool-spec hash means a hand edit to them no
longer marks anything stale (the hole `pools.py:480-490` closed). Added to v3
§9, step 3:

- the run computes a hash over the strength entries it applied (party,
  `support`, `overperform`, `sigma_j`, `register`, sorted). It records it in
  `35_widths.judgements_sha` and in the forecast artefacts' declarations
  (`src/declares.py`);
- on a backtest the hash covers the empty set, and the ignored entries are
  listed separately;
- `declares.py --verify` and `tests/test_intermediates_are_current.py`
  recompute the hash from the live judgements file and report `~` (declared and
  wrong) on a mismatch;
- a constructed test edits `sigma_j` in a scratch copy and must see the
  mismatch, and must go quiet when the edit is reverted.

## 3. The owner's checkpoint

### 3.1 The middle-width choice (corrected)

| | A: bridge | B: middle's own record |
|---|---|---|
| sets the 5-20% width from | the 1-5% band (18 party-elections) and two large anchors (44 cases), straight line in log size | the 5-20% band's root (12 cases, 5 party-elections) |
| fit to the 12 middle results | 1.98, out-of-sample | 0.88, in-sample by construction |
| 5-20% leave-band-out test | quiet | quiet |
| 1-5% leave-band-out test | **fires** | quiet |
| declared exception | stop check exempted at 1-5% | `MIN_EFF` waived for 5-20% |
| backtests, large parties, CRPS difference [90%], inside 90% band | −0.171 [−0.316, −0.008]; 30 / 32 | −0.158 [−0.286, −0.019]; 31 / 32 |
| backtests, middle parties | +0.143 [−0.119, +0.429]; fails the CRPS rule | +0.364 [+0.120, +0.667]; fails by more |
| middle, established only (2021, 7) | −0.361 | −0.147 |
| JHB 2026 log-sd DA / ANC / ASA / EFF / MK / PA | 0.13 / 0.13 / 0.28 / 0.31 / 0.56 / 0.50 | 0.16 / 0.17 / 0.44 / 0.48 / 0.70 / 0.67 |
| as a ratio of today's (DA / ANC / ASA / EFF) | 0.62 / 0.38 / 0.56 / 0.54 | 0.76 / 0.50 / 0.88 / 0.84 |
| JHB 2026 draws, largest new party above 18.12% (today 255) | 325 | 471 |
| JHB 2026 draws, established party under 1% last time above 5% (today 403) | 22.8 | 24.0 |
| wrong-party seats on the list proxy, 2016 / 2021 (today 71.8 / 154.9) | 72.6 / 153.1 | 72.7 / 153.2 |

**What both options share:**

- The large-party rules pass.
- The middle CRPS rule fails, for the same reason in both: the 2016
  national-debutant width (0.72-0.78, mostly COPE's 2011 collapse) applied to
  the EFF, which landed above its centre.
- Below 5% the two options are identical.

The option not chosen runs as a paired arm.

### 3.2 Every judgement call to decide

Values are for the 2026 record unless stated. "Check" means how the value is
tested once the change is built. A width is never adjusted to coverage.

| # | call | value(s) | evidence | how it is checked |
|---|---|---|---|---|
| 1 | middle width (5-20%) | A or B (§3.1) | §3.1 | the other option runs as a paired arm; the plausibility check and backtests per option |
| 2 | the exception that goes with 1 | A: stop check exempt at 1-5%; B: `MIN_EFF` waived at 5-20% | §1b | the exemption is printed by the writer every run |
| 3 | width estimator | offset-aware moment root, per band below 5%, linear in log size between anchors | one estimator for widths, cross-checks and increments (v2 §2.1) | writer prints each band with a cluster-bootstrap interval |
| 4 | band edges | 1%, 0.3%, 0.1% | no step anywhere, because widths interpolate | sensitivities printed |
| 5 | anchor placement | weighted geometric centre of each anchor's rows | v3 §2.1; re-check reproduced | — |
| 6 | large anchors | two: 0.074 at 25.6% (rows 20-30%), 0.043 at 45.4% (rows ≥ 30%) | within-block residual 0.074 / 0.048 / 0.039 by size; one anchor at 38.8% scores u² 0.20 on the 20-30% rows | writer prints one-anchor and two-anchor fits |
| 7 | `MIN_EFF` | 8 party-elections per band or increment | 5-20% has 5; 1-5% for 2016 has 5 | — |
| 8 | weight unit | party-cycle, counted within the band | v3 §0.1 | all-band count printed (1-5%: 0.834 against 1.041) |
| 9 | residual reference block | parties with centre ≥ 20% (single-member blocks skipped) | v1 §1.1, v2 N5 | two-largest variant printed |
| 10 | own-term family | normal | the location −σ²/2 is exact; tail evidence depends on standardisation (excess kurtosis 0.87-2.56; 1.4 below 1%) | a Student-t arm, location from the calibration |
| 11 | shared swing loading | 0.46 of a party's variance below 0.55%, 0 from 2.24%, linear in log size between, 0 at 20% | one-way city-year shares: below 1% 0.46, 1-20% 0.00 | the 1-20% shared share is pre-registered as a measured quantity |
| 12 | national-debutant increment | one pooled value: 0.477 (A) / 0.457 (B); 2016 record 0.78 / 0.72 | 87 cases, 35 party-elections; 90% interval 0.00-0.90; the ≥ 1% split has 5 party-elections | split printed with intervals |
| 13 | seeded-arrival increment and arrival factor | 0.85; 0.73 | 221 cases, 133 party-elections, interval 0.57-1.13; 16 city-years | regenerated each record; the seed centre bias (mean −1.16 in 2016) goes to next round |
| 14 | 2016 seed width | the debutant increment | no seeds in the 2011 backtests | labelled in every report |
| 15 | location fixed point | two iterations; stop when the change is below 0.01 | model-internal shift median +0.045 | `35_widths` prints Δ per party |
| 16 | turnout composition | subtracted from each party's own variance, floored at 0, excess recorded | conditional-share rule (MACHINERY §1.50) | `41_guards.width_floored` |
| 17 | mean-conservation falsifier | per-party z on the run's own standard error, Bonferroni at a family error of 0.01 (threshold 3.49 at 21 parties) | 0 false alarms in 20 clean runs; ×1.2 errors detected 10 / 10 | suite test of false alarms and power |
| 18 | `N_CAL`, `KAPPA_TOL` | 4,000; 1e-3 | numerical | registered as numerical constants |
| 19 | stop rule | leave one band out; cluster bootstrap 90% | can fire (A at 1-5%) and goes quiet (B) | constructed test in the suite |
| 20 | minimum data for a target | 20 established party-elections | 2016 has 24 | writer refuses below it |
| 21 | 2011 width | 1b v3 fallback (0.27 / 0.48), untestable, excluded from falsifiers | no earlier backtest | label on every report and public page |
| 22 | no pool-concentration covariate | — | real effect (1f: −0.24, se 0.06); deferred; it would narrow the PA | — |
| 23 | no extra width for a second local election | — | the only precedent at ≥ 5% is EFF 2021; ActionSA and the PA are second-election parties at 2026 | parties listed in the trace |
| 24 | strength judgement: how a centre is stated | existing `support` (a share) and `overperform` (a multiplier), centre = (support or model centre) × overperform | one key set (re-check 1b) | two-way register guard |
| 25 | strength judgement: width | `sigma_j`, required, meaning uncertainty beyond the model's own centre error at the judged size (0 = as good as the model's); replaces the class increment; a judged seed drops the arrival factor | v3 §11.1 | §J register template states the definition |
| 26 | strength judgements in backtests and forecasts | backtests ignore and record them; forecasts report with and without | a judgement cannot be blind after the election | `35_widths.judgements_ignored`; paired forecast runs |
| 27 | judged arrival and the seed group budget | sized like any arrival at emit; the judged centre acts at run time | consequence of reading at run time; number-neutral today | — |
| 28 | judgement hash | forecast artefacts declare a hash of the applied entries | re-check 2c | `declares.py --verify`, `test_intermediates_are_current` |

Rows 3-23 were already in v1-v3 and are restated so that the checkpoint has
one list. Rows 1, 2 and 28 are new or changed here.
