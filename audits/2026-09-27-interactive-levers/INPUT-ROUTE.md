# How the interactive gets its inputs

Rewritten 2026-09-27 because the first version answered the wrong question. It
compared the three routes on **size**. The question that decides it is whether a
reader's lever still acts at the right point in the model.

## The two things a route has to do

1. **Be fast enough to use.** One run today opens 75 files totalling 141 MB and
   takes about 25 seconds of setup before a single draw.
2. **Leave every lever acting where it acts now.** A lever that moves a number
   the page has already precomputed does nothing. This is the test the first
   version of this document never applied.

## Where each lever acts

The model runs in stages. A lever can only work if its stage still runs in the
browser.

| the control | the stage it acts in | can it survive precomputation? |
|---|---|---|
| **the seat law** | after every draw — it converts votes to seats | **Yes, entirely.** It does not need the browser at all: all four laws are already computed |
| **within-pool movement** | the draw itself — it is the spread of the Dirichlet that splits a pool's vote | Only if the draw loop runs in the browser |
| **by-election weight** | before the draw, when a party's centre is set | Only if that stage runs in the browser |
| **turnout by group / area** | after the balancing step, before the draw | Only if that stage runs |
| **polls** | before the draw, adjusting party levels | Only if that stage runs |

So the levers split cleanly in two: **the seat law needs nothing**, and
**everything else needs the model from the party-level stage onward.**

## The three routes, against both tests

### Route A — ship less data, run everything

Prune the archive to what Johannesburg needs.

* **Levers:** all of them keep working. Nothing is precomputed.
* **Speed:** does not solve it. 76% of the 141 MB is other metros' results, and
  they are not surplus — `levels.py:868` reads them to build the theta record,
  the party-trend table behind a measured 14% improvement. Deleting them deletes
  that. Pruning to "Johannesburg only" is a model change disguised as a saving.

### Route B — precompute the pure reductions, run the rest

The other metros are read for one thing: each 8 MB file is reduced to citywide
party totals, and the ratios between elections become the theta record. That
record is **18.8 KB for 52 parties**. The census spreadsheet is read the same
way.

* **Levers:** all of them keep working. The reductions happen *before* any
  lever acts — they are inputs to the party-level stage, not outputs of it.
* **Speed:** 107 MB of the 141 disappears, and `openpyxl` and the spreadsheet
  parse leave the load path, which is a large share of the 25 seconds.
* **The catch:** the shipped record must be checked against what the live path
  produces, or it becomes a second definition of theta — the thing running the
  real model was chosen to avoid.

### Route C — precompute the whole setup, run only the draws

* **Levers:** ⛔ **this is where it breaks.** Everything except the seat law and
  within-pool movement acts in the setup. Precompute the setup and the by-election
  weight, the turnout controls and the poll dial all become sliders attached to a
  number that was fixed on Atlas. Four of the five planned controls stop working.
* **Speed:** the fastest of the three.

## The recommendation

**Route B**, and it is not a compromise: the 141 MB is an implementation detail
of a reduction, not an input to the forecast. It is the only route that is both
materially faster and leaves every planned lever acting where it acts today.

**And ship the seat-law comparison first, separately, before any of this.** It
needs no browser engine, no reduction and no decision here — four complete
forecasts at the published 5,000 draws, already reduced into `site/regimes.json`.
If the browser work slips, that control does not slip with it.

## Three things that were muddled in earlier descriptions, stated plainly

**300 and 400 draws are different things and neither is the published forecast.**

* The **published forecast** is **5,000** draws. That is what the site shows.
* The **backtest** on `/about` — the 2021 track record — was run at **400** draws
  per city. That is a different exercise scoring a different election, and it has
  nothing to do with the interactive.
* **300** is the count proposed for the **interactive**, so a reader's re-run
  finishes in a usable time.

**The "first 300" problem is about the interactive only.** The model uses one
random generator and a plain loop, so a 300-draw run is literally the first 300
draws of the 5,000. That means the page's untouched default would print
different headline percentages from the published page — identically for every
reader, because it is the same 300 draws every time. It is an argument about
what the interactive may display before a reader touches it. It says nothing
about the backtest.

**The roster is in hand; the IEC's own list is not.** We have a roster of 82
parties and the model uses it. What we do not have is the IEC's authoritative
list to check it against, because the IEC publishes no per-municipality list
anywhere reachable. The 82 was typed from press reports that disagree with each
other. So: the roster exists and works, and its provenance is weak — those are
two different statements and both are true.
