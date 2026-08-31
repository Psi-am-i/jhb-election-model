# Pre-registration — the shape of `sd_for` below 15%, named from mechanism

**Written 2026-08-31, BEFORE any refit is built or scored.** Nothing in this
document has been fitted. It exists to satisfy the second door in
`JUDGEMENT-CALLS.md`'s `sd_for` size-dependence row:

> *"No further functional form may be tried against these two folds … Licensed
> next by more folds (ingest the pre-2011 archive for the other seven metros) or
> by **a mechanism argument naming the shape in advance**."*

Two forms are already spent (§1.62). **This is the mechanism door, not the
folds door**, and it is written first precisely so that it cannot be adjusted
after seeing a score.

## 1. What is wrong, and it is not in dispute

`levels.sd_for` fits `sd(log θ)` as **a straight line in log(size)**. The
forward-validated conditional dispersion is not monotone in size:

| size band | measured conditional sd | width in use | ratio |
|---|---|---|---|
| < 0.2% | 0.915 | 0.460 | 1.99× |
| 0.2–1% | 0.737 | — | — |
| 1–5% | 0.448 | — | — |
| 5–15% | 0.663 | 0.188 | 3.53× |
| ≥ 15% | **0.273, CI [0.136, 0.386]** (n=64) | 0.151 | 1.81× |

In all four bands below 15% the cluster-bootstrap interval **excludes** the
width in use, always too narrow, by 1.70× to 3.53×. At ≥15% the used width is
still inside its interval, near its bottom.

⛔ **CORRECTED 2026-08-31, BEFORE ANY FIT — AND THE ERROR IS THE ONE THIS
PROJECT KEEPS MAKING.** The first draft of this document quoted the ≥15% band as
**0.138, CI [0.084, 0.171]** and pinned P2 to that interval. **That is the
NINE-city-year measurement (n=37), superseded on 2026-08-23 (§1.77) and
re-measured on the corrected harness on 2026-08-28 (§1.124).** The current
figure is **0.273, CI [0.136, 0.386] over 64 observations** — an interval 0.250
wide rather than 0.087. The sub-15% rows above are likewise the nine-city-year
table (their n sums to 257, not the current 403) and are retained only as the
qualitative statement that the four bands exclude the width in use, which
survives the re-measurement; **no number in them may be quoted.**

A pre-registration built on a superseded interval would have pre-registered a
prediction against a figure the register had already withdrawn — in the one
document whose entire purpose is to be fixed in advance. Caught in blind review.

**A straight line cannot be right in the middle and at both ends.** That is the
finding. The open question is what shape replaces it.

## 2. The mechanism, and the shape it names

`θ` is a retention ratio — a local share divided by a national one — so
`log θ` is a difference of two log shares. Its dispersion has **two components
with different size-dependence**, and they are not a matter of taste:

**(a) A term that decays with size — and ⛔ IT IS NOT SAMPLING NOISE.**

The first draft called this "a sampling/aggregation term" and wrote the
binomial sd of `log p̂`. **That is wrong and the objection is decisive: an
election is a CENSUS, not a sample.** Every ballot is counted. There is no
sampling error in a party's share, and a mechanism argument resting on one would
be importing survey statistics into a complete enumeration. Raised in blind
review; the shape survives, the reason for it does not.

The correct mechanism is **a roughly size-independent ABSOLUTE perturbation,
which is a large RELATIVE move for a small party and a negligible one for a
large one.** Concretely, and all three are real at this scale:

* **contestation.** A small party stands in some wards and not others, and the
  roster changes between elections. A party contesting 40 of 135 wards rather
  than 52 moves its citywide share by a large fraction of itself; the ANC's
  roster does not move at all.
* **entry and exit near the floor.** Splits, mergers and disappearances are
  concentrated among small parties, and each is a step change in the log ratio.
* **a common pool of marginal voters.** A few thousand voters moving is most of
  a small party's vote and a rounding error in a large one's.

None of these is noise in the measurement. They are real variation whose
ABSOLUTE size is roughly independent of `p`, so in log space it scales as `1/p`.
That gives the same functional form for a defensible reason:

**(b) A behavioural term that does NOT decay with size.** Parties differ in how
much of their national support they convert locally, and that variation has no
reason to vanish for a large party. It is a floor.

**So the mechanism names the shape:**

    sd(log θ | p) = sqrt( a² / p + b² )

with `a ≥ 0` scaling the fixed-absolute-perturbation term and `b ≥ 0` the
proportional behavioural floor. (`n_eff` is dropped with the sampling story
that motivated it; the electorate size is not what sets this.) **Two
parameters, both with a physical meaning, neither chosen to fit a wiggle.**

### What this shape predicts, stated before it is fitted

1. **Monotone decreasing in size.** It cannot produce the dip at 1–5% (0.448)
   followed by the rise at 5–15% (0.663). **The mechanism asserts that dip is
   noise, not signal**, and the register already notes 5–15% has **n = 14** and
   the widest interval of the four — the weakest of the bands.
2. **A finite floor.** As `p` grows the curve flattens to `b`, so it predicts the
   ≥15% band is where the fit should be most trustworthy — which is the one band
   where the current width still lands inside its interval (0.273, CI [0.136,
   0.386], in use 0.151).
3. **Divergence at the bottom, not a straight line.** As `p → 0` it rises like
   `p^(−1/2)`, faster than any line in `log p`. This is why the line is worst at
   the extremes and least wrong in the middle — the observed pattern.

## 3. ⛔ THE PRE-REGISTERED PREDICTIONS

Scored on the estimation record's **held-out NLL**, the Key 4 instrument, at
both folds, using `key4_delta` — not a bare difference of means (§1.124).

* **P1 — the mechanism shape beats the straight line on BOTH folds.** If it wins
  one and loses one, that is **undetermined and the model does not change**,
  exactly as §1.61 ruled for the previous two forms. One-of-two is not a result.
* **P2 — the fitted `b` lands inside the CURRENT ≥15% interval [0.136, 0.386].** The
  behavioural floor is the quantity that band measures. If `b` comes out far
  outside it, the two-component reading is wrong even if the score improves, and
  **a score improvement with a refuted mechanism must not ship** — that is
  curve-fitting wearing a mechanism's clothes.
* **P2a — and P2 is now a WEAK test, which must be said rather than glossed.**
  The interval it holds `b` to is 0.250 wide where the superseded one was 0.087.
  A two-parameter fit landing inside it is much less impressive than the first
  draft implied. **If P1 passes and P2 passes only because the interval is wide,
  that is not a confirmation** — report the fitted `b` with its own uncertainty
  and say whether it would have passed the narrower interval too.

* **P3 — the 1–5% dip does not survive.** The fitted curve should sit ABOVE the
  measured 0.448 at 1–5%. If the residual there is large and one-signed, the dip
  is real, the two-component mechanism is incomplete, and this door closes too.
* **P4 — widening below 15% will make CRPS WORSE, and that is expected.** §1.58
  records that CRPS prefers the forecast narrower all the way out. **CRPS is not
  the arbiter here**; Key 2's calibration floor and Key 4's held-out NLL are.
  Quoting a CRPS regression as a refutation would be scoring a width change on
  an instrument that cannot see width.

**What would refute the whole thing:** P1 not met, or P2 not met. Either ends
it, and the entry goes in `MODEL-LOG.md` with its numbers, as §1.62's did.

## 4. What this does NOT license

* **It is not a third try at the same question.** The register bars *further
  functional forms tried against these two folds*; the bar exists because a
  handful of trials makes a spurious two-of-two likely. This is one shape, named
  from a mechanism, with its parameters interpreted and its failure conditions
  written down first. **If it fails, the mechanism door is closed too** — do not
  return with a three-parameter version.
* **It does not touch ≥15%.** 0.150 is inside its own interval and the mechanism
  predicts that band is where the current fit is least wrong. Changing it would
  repeat §1.50's refuted **global** correction (258→268 seats, 231.9→246.8
  CRPS), which is the failure mode the register's row above this one records.
* **It is not licensed to run before the re-emit window.** Eight of sixteen
  city-years currently run a constant arrival channel because
  `pools.metro_file` cannot resolve 2000/2006 (queue entry 4). A width fitted
  now is fitted against half a panel that is about to change underneath it.

## 5. One piece of evidence that cuts against this, recorded now

`theta_residual`'s `k*` by size bin is **not stable across cycles**:

    2006  <0.2% 0.51  0.2-1% 0.63  1-5% 0.79  >=15% 0.55
    2011  <0.2% 2.52  0.2-1% 1.84  1-5% 3.54  >=15% 2.00
    2016  <0.2% 1.40  0.2-1% 2.36  1-5% 2.32  >=15% 0.71
    2021  <0.2% 1.78  0.2-1% 1.74  1-5% 1.77  5-15% 1.93  >=15% 1.59

At 2006 every band is **below** 1 — the prior was too wide — and at 2011 every
band is well above it. **A shape fitted on the level of these ratios would be
fitting a cycle effect.** The mechanism above is a claim about the *shape in
size*, not the *level in time*, and the 2021 row is the one that most looks like
a constant across bands, which is what a large `b` relative to `a` would produce.

**This is written here, before the fit, because it is the most likely way the
result will be over-read.** If P1 passes, the next question is whether it passes
for the reason claimed or because the level happened to suit two cycles.

### ⛔ AND FOLLOWED THROUGH, THIS EVIDENCE UNDERMINES §1

Computed here, before any fit — the spread of `k*` ACROSS bands, within a cycle:

| cycle | mean k\* | sd | **CV** |
|---|---|---|---|
| 2006 | 0.620 | 0.124 | 0.200 |
| 2011 | 2.475 | 0.767 | 0.310 |
| 2016 | 1.697 | 0.794 | **0.468** |
| **2021** | 1.762 | 0.121 | **0.069** |

**At 2021 — the most recent cycle and the one closest to the target — `k*` is
nearly CONSTANT across size bands.** A constant `k*` means the line's *shape in
size* is already right there and only its *level* is wrong. If that is the true
state, then the correct fix at 2021 is **a scalar multiplier on `sd_for`, not a
new functional form** — and this whole pre-registration is aimed at the wrong
defect.

The non-monotonicity that motivates §1 is carried by 2016 (CV 0.468) and 2011
(0.310), and the ≥15% band is the single largest contributor at both. So there
are two readings and the panel cannot yet separate them:

* **shape is wrong** — the line cannot bend, and the 2021 flatness is a
  coincidence of that cycle's composition;
* **shape is right, level moves by cycle** — and the apparent non-monotonicity
  is a cycle effect read as a size effect, exactly the confound §5 opens with.

**P5 — the discriminating test, and it must be run FIRST because it is free and
consumes no trial.** Fit a *scalar* `k` per cycle against the *shape* fit, on
the same held-out folds. **If the scalar does as well as the shape on both
folds, the shape claim is refuted and nothing further should be tried** — and
that outcome is a genuine finding, not a failure. Only if the shape beats the
scalar does P1 mean what §3 says it means.

This is recorded before the fit precisely because it is the reading that would
otherwise be discovered afterwards, and by then P1 will have consumed a trial.
