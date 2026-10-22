# The by-election weight measured on 2021, not declared

Written before the run, on 2026-10-20, after
`prereg/2026-10-20-byelection-weight-2021-backtest.md` was run and scored
(MODEL-LOG §1.325). **Already known before this was written:** that run's
arms at weight 0, ½ and 1 (and ½ with seat-changing contests doubled), their
per-metro list-vote errors, wards called wrong and seats given to the wrong
party, and the per-party errors of the larger parties. Every prediction below
is made knowing those three points of the curve. No model code changes; the
experiment runs in a scratch directory and writes nothing into `data/`.

## The question

The owner, 2026-10-20: "Should it be 1/2 or maybe it should be 1/3 — the
results should tell us and make this a measured variable." The weight `w_bye`
(JUDGEMENT-CALLS §A59, declared ½) is to be read from the 2016–2021
by-elections against the 2021 result, per party size if the evidence supports
a difference, and reported with how precisely one cycle can fix it.

Also measured, because the same runs answer them: whether the by-election
level helps through its swing or only through its pull back toward the
previous result (the caveat of §1.325), and whether the cap on the
by-election level (OWNER-DECISIONS item 3) helps or hurts.

## Method

Same scratch deltas, draws (1,000), seed (20261104) and scoring as §1.325
(`audits/2026-10-20-byelection-2021-backtest/run.py`), so arms differ only in
the by-election term. A new script,
`audits/2026-10-20-byelection-weight-measured/sweep.py`, reuses the built
deltas and writes one results file per arm.

**Grid arms (cap on, as the model ships):** `w_bye` ∈ {0, 0.1, 0.2, 0.25, ⅓,
0.4, 0.5, 0.6, ⅔, 0.75, 0.9, 1}. 0, 0.5 and 1 are re-run, not reused.

**Swing-0 arm (R):** `w_bye` 0.5 with every party's `weighted_delta` set to 0
in a copy of the deltas file, weights and contest counts kept. The
by-election level becomes the party's 2016 list share (capped), so R measures
the pull toward the previous result alone.

**Per-class arm (C):** `w_bye` `None` with the class weights the per-class
estimate below gives (classes `byelections.size_class`, edge 1% of the
previous list share), run only if the two class estimates differ by more
than 0.1.

**Instruments.**

1. *Primary: summed average list-vote error* (`pr_mae`, points, summed over
   the eight metros) at each grid weight. The **measured weight** is the grid
   weight with the lowest sum.
2. *Leave one metro out.* For each of the six metros where by-elections
   reach any party (Tshwane and Buffalo City admit none), the grid weight
   minimising the sum over the other seven; and the held-out metro's error at
   that weight. Reported: the six chosen weights, and the summed held-out
   error against fixed ½ and fixed 0 on the same metros.
3. *Least-squares slope on the forecast shares*, per party in the vote table:
   `e = actual − forecast(w=0)`, `d = forecast(w=1) − forecast(w=0)`,
   `w* = Σed / Σd²`, pooled, and per size class at two edges: 1% (the model's
   classes) and 10% of the previous list share. Each with its
   leave-one-metro-out range.
4. *Cap.* The same slope with `d` replaced by the uncapped by-election level
   minus the level (read from the `30_centres` trace's route notes, to 0.1
   point), against the capped `d` read the same way; the pooled squared
   error of each at its own `w*`.
5. Wards called wrong and seats given to the wrong party at every arm,
   reported, not deciding.

## Decision rule (fixed now)

* The measured weight is instrument 1's minimum. It is reported with
  instrument 2's range.
* **If ½ lies inside the leave-one-metro-out range, the record does not
  distinguish the measured weight from ½**, and the report says so in those
  words. The owner chooses; the recommendation is then to keep ½ unless the
  measured weight also wins instrument 2's held-out comparison.
* Per-class weights are recommended only if the two classes' leave-one-out
  ranges do not overlap.
* The cap is recommended off only if the uncapped slope has lower pooled
  squared error in at least four of the six metros.
* Nothing is wired into the model by this run. Making the measured value the
  default (through `bye_value.py` and `w_bye = None`) is a separate change,
  shown to the owner first.

## Predictions

M1. **Control.** The re-run arms at 0, 0.5 and 1 reproduce §1.325's per-metro
`pr_mae` exactly.

M2. The summed `pr_mae` curve is flat (within 0.3 points of its minimum, summed
over eight metros) from about 0.3 to 0.6, and its minimum lies between 0.3
and 0.6.

M3. The leave-one-metro-out range is wide: at least 0.3 between the lowest and
highest chosen weight, and it contains ½.

M4. Instrument 3's pooled slope lies between 0.2 and 0.6, and need not equal
instrument 1's minimum: the shrink and the normalisation sit after the blend,
and `pr_mae` is an absolute error, the slope a squared one.

M5. Arm R improves the summed `pr_mae` on arm 0 by at least half as much as
weight 0.5 does: much of the gain is reversion to the 2016 result, not the
swing (Nelson Mandela Bay most of all).

M6. The 1%-edge class split is not supported: by-elections admit too few
parties under 1% to fix their weight (their leave-one-out range spans more
than 0.5, or is undefined).

M7. The uncapped slope does not beat the capped one in four of six metros.

## What it can and cannot settle

One cycle: six city-years where by-elections reach a party, 2016→2021, when
the ANC fell in nearly every metro and its by-election swing did not show it.
A weight chosen from this record is fitted to that cycle; the
leave-one-metro-out range is the honest statement of its precision, and it
treats metros as independent when they share one national swing. The result
is evidence for 2021→2026 only by assuming by-elections relate to the next
result the same way across cycles. Calibration and band coverage are not
read: the width record was measured about centres with no by-election term.
