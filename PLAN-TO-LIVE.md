# Plan to a new live forecast — amended 2026-08-23

**24 days to nomination lists (16 September). 73 days to polling day
(4 November).** Both are hard dates set by the IEC.

This supersedes the earlier plan, which was written when the panel was nine
city-years and the model list was believed closed. Four things have changed
since and each moves an item:

* **The panel is sixteen city-years** (§1.70) and one effective cycle became
  two. `ITERATING.md`'s "when to stop" section rests on the old premise and is
  obsolete.
* **Six raw inputs went missing and came back** (§1.75–§1.79). Everything
  derived in a four-hour window on 22 August was re-run; the guard that would
  have caught it now exists and runs.
* **The acceptance bar is amended** (2026-08-23, owner): paired and
  cycle-replicated, calibration as an untradeable floor, derivedness priced in
  seats against a budget that never refills.
* **The θ-record question is settled** (§1.82). Recency is refuted on
  forward-validated evidence; the 2009→2011 transition is the defect; the
  footprint and the party-event descriptions **interfere** rather than sum.

---

## The single decision this plan turns on

**The model is good enough to ship today.** 384 coherent seats against uniform
swing's 530 on sixteen city-years, beating it by *more* on the 2016 cycle
(30.0%) than the 2021 one (26.3%) — the only genuinely out-of-sample statement
this project has ever been able to make.

So every modelling item below is optional and every publishing item is not.
**The plan is therefore ordered by deadline, not by interest**, and it carries
one freeze date: **10 September**. Anything not passing by then does not go into
the 16 September forecast.

---

## Track A — publish (not optional, dated, owns the critical path)

### A1. Stage-1 forecast, frozen and hashed, BEFORE 16 September ★ blocking

`PUBLISHING-BACKLOG.md` §5c. A forecast issued *before* the nomination lists is
the only one that can later be shown to have been a forecast rather than a
retrodiction. It already runs. It needs: a frozen artefact, a published hash, a
date, and a statement of what it does and does not know.

**This is model work in disguise and it decays to zero value on 16 September.**
Do it first.

### A2. Say what the poll channel is doing, in public ★ blocking

The largest single risk to the November forecast, and it is not in the θ record.

* `polls.json` holds **four** 2026 entries — two SRF/Victory Research metro
  waves (n=504, n=503), a DA internal with no sample size, and an Ipsos
  metro-aggregate. Effective house count is **1.0**.
* **One house flips the Johannesburg lead**: polls off gives ANC 68 / DA 65;
  polls on gives DA 78 / ANC 63.
* The DA sits **exactly on the `poll_house_k` cap** (w = 0.50), so the poll's
  influence on the party it moves most is set by a declared constant rather
  than by the σ arithmetic.

**Publish the poll-off / poll-on split beside the headline.** It is cheap,
honest, and forecloses the criticism that will otherwise land hardest.

*(Figures above are quoted from the review and the register; verify each against
a fresh run before it goes on the page.)*

### A3. Chase one national 2026 poll ★ start now, long lead time

The arrivals poll path is **worth 48 coherent seats** (§1.65) and **cannot fire
at 2026** — not for want of code, but because no national 2026 poll is in the
register. One acquisition re-enables the whole channel. This has external lead
time, so it starts today and runs in parallel with everything else.

### A4. Rebuild the live pages against the current model

The site HTML is from 17 August and predates the panel doubling, the poll
rebuild and every correction since. Ten front-page claim tokens are still pinned
to `turnout_tilt_da`, a lever `run_model` no longer has.

Rule: **never type a model figure into prose** — register it as a stat token and
let `build_site.py` audit it.

### A5. Nomination lists, 16 September

Dated and mechanical. Retires `contestation_expand`, makes contestation live,
and withdraws the phantom entrant mass. Then re-run, re-score, and publish the
revision under §5c's stated rule.

---

## Track B — model (all optional, all timeboxed, all behind the freeze)

### B1. Type A routing — the one modelling item worth opening

§1.74's own conclusion, confirmed by §1.82: **route, do not drop.**

The 2009→2011 transition is contaminated by party-structural events and accounts
for ~18 of §1.70's 26 seats (§1.78: nine 280→262, sixteen 384→360, CRPS
329.4→320.3). But an *exclusion* moves that volatility out of the model's prior
and into its error — §1.74 measured `sd_for` at 5–15% falling 0.203 → 0.150 with
the filter on while the measured dispersion stayed at 0.839, worsening the ratio
from 4.24× to 5.58×.

So route the volatility into the **width**, through the splinter and arrivals
machinery that already exists, instead of letting it vanish.

**This is not backtest-only.** The 2026 prior is fitted on transitions that
include 2009→2011, and 2026's own party structure is dense with Type A events —
MK's split from the ANC (Dec 2023), ActionSA, the PA's growth.

Pre-register per §1.80. Judge under the amended bar. **Timebox: freeze 10
September.**

### B2. Sweep the nineteen never-swept constants

One afternoon, changes no forecast, and it is the derivedness ledger's first
entry — it converts nineteen "unknown" register rows into nineteen numbers.
`ALPHA_*` feed the model's dominant width lever and have never been swept.

This is the cheapest defensibility gain available and it directly serves the
amended bar's Key 3.

### B3. Separate the width channel from the centre channel

Never measured. Adding the pre-2011 archive changed both the θ centre and
`sd_for`; §1.74's dispersion movement suggests the width channel does the work.
One arm with the new observations feeding the centre and `sd_for` frozen, one
the reverse. If the width arm carries most of the 26, the fix is in `sd_for`'s
specification, not in the record's membership.

### B4. Two code-level defects raised by the review — verify, then decide

* **`sd_for`'s covariate may be inconsistent with the record's weighting.**
  `_reliability(share)` weights by the *base* share; the dispersion fit appears
  to regress on the party's size *at the target*, one x-value per party. For a
  party like COPE — 7.4% at the 2009 base, near zero at a later target — that
  places a contaminated residual at the small-party end where the slope is
  steepest.
* **The by-election decay may conflate τ with a half-life.** Inert today
  (`w_bye_local_*` is 0.0), wrong the day it is switched on.

**Verify both against the code before acting.** Neither is confirmed.

### B5. Ingest the five held-but-never-ingested `lge2000` archives

Data already on disk with `MUNI_HEAD` keys written (§1.79). `ITERATING.md` says
the only thing licensing a restart is **more independent clusters**, and this is
exactly that. But it moves every number, so: **after 16 September, on a settled
tree, once**, under the one-writer rule.

---

## Explicitly NOT doing before November, with reasons

* **A recency decay or date cutoff on the θ record.** Refuted (§1.82): held-out
  NLL is non-monotone in the age of the record, and the premise offered for it
  was false in the code.
* **Re-measuring `TURNOUT_CORRELATION`, `SPLINTER_PARENT_WEIGHT` or
  `SPLIT_SD_FLOOR` against the present record.** It would bake the 2009→2011
  contamination into three more constants.
* **The ward-level upset mechanism.** Real, diagnosed, no measured prize.
* **The tail (ranks 13+).** 33 of 2,960 seats — 1.1% — and the obvious fix was
  measured at 14–22 seats. The bias is carried on the record, deliberately.
* **`dirichlet_scale`.** Measured as a trade; fails Key 1 and buys nothing on
  Key 3.
* **The publishing revamp** — the interactive port, the fidelity gate, the
  sliders. Correctly separated, and its own order-of-work says "close the model
  list" first. **Exception: §5c stage 1, which is A1 above.**

---

## Sequencing, and the one hard rule

```
now ──────────────► 10 Sep ────────► 16 Sep ──────────────► 4 Nov
 A1 freeze+hash      FREEZE          lists land            polling
 A2 poll caveat      B1 in or out    A5 re-run+revise
 A3 chase a poll                     A4 pages rebuilt
 B2 sweep (cheap)
 B1 routing (timeboxed)
                                     B5 lge2000 ingest
```

**One writer on `pools_*.json`, and nobody measures while it writes.** B1, B5
and every re-emit touch it. Canonical numbers come from **one settled run at the
end**, and every figure quoted anywhere comes from that run.

---

## What would make me abandon Track B entirely

If A1, A2 and A4 are not comfortably done by **1 September**, drop Track B. The
model at 384 already beats every baseline and the marginal seat is worth far
less than a published, hashed, honest forecast that exists before the lists
close.
