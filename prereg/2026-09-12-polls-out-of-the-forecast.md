# Pre-registration — taking the poll channel out of the forecast

Written 2026-09-12, BEFORE the switch was flipped and BEFORE any
`compare_history` run of either arm. Not edited afterwards.

## The decision, and whose it is

The owner, asked to settle `docs-public/methodology.md`'s description of a poll
cap that no longer exists:

> we want to be able to incorporate all the polling we receive. And yes, it
> would be a user lever on the site so they can say i trust or dont trust this
> poll and have that affect numbers within the polls range of error. But we
> still need to design how the various polls interact with each other properly
> so for now, pull the polling mechanism out of the forecast and we will plan
> properly how to re-insert it.

This is the decision MODEL-LOG §1.94 reserved to him in terms:

> **This does not by itself mean switch the channel off at 2026** — and the
> reason is uncomfortable. […] But a channel that is worth −6 where it *can* be
> scored has lost the argument that justified keeping it live where it cannot.
> That is a decision for the owner, pre-registered before it is taken.

It also supersedes the §1.95 position, taken 2026-08-25, that a binary switch
could not express the three jobs polls do. It still cannot. The change is not
"polls are worthless"; it is that **the forecast stops carrying a mechanism
whose interaction between houses is undesigned**, while the machinery stays in
the tree for the redesign the owner describes.

## What changes — ONE default, and nothing else

    montecarlo.DEFAULTS["poll_paths"]   "all"  ->  "off"

`poll_paths` is the existing master switch and already has the three-way form
`"off" | "arrivals" | "all"`. Nothing is deleted: `src/polling.py`, the
register, `screen`, the metro conversion and every judgement call stay exactly
where they are and stay reachable from `--set`, so re-insertion is a default
change and not a rebuild.

⛔ **`poll_credence` IS NOT THE SWITCH AND MUST NOT BE USED AS ONE.** It gates
the metro blend only. The arrivals path writes `scenario["poll_levels"]`
directly and is gated by `poll_paths` alone, so `poll_credence = 0` would leave
the larger of the two paths fully live — the path §1.65 measured at 48 coherent
seats. Anyone reading this later and reaching for the credence dial to turn
polls off will get a forecast that still uses polls.

## The two paths, and which targets each is live at

| path | what it does | gated by | live where |
|---|---|---|---|
| **arrivals** | a *national* poll share converted to a metro one, written as `poll_levels` for parties with NO baseline — the entrant case the model gets wrong 31 times in 32 | `poll_paths in ("arrivals", "all")` | 2021 (`ipsos-2021-lge-national`), 2016 (`ipsos-2016-lge-national`) |
| **metro blend** | a *metro* poll blended against the model's own centre by inverse variance | `poll_paths == "all"`, then `poll_credence` | 2016 (`ipsos-2016-lge-joburg`), 2026 (two SRF waves) |

Both go off together. That is the point: the undesigned part is how the two
interact, and how several houses interact inside the second.

## Predictions

**PRIMARY — accuracy, DIRECTIONAL, and this is the clause that can embarrass
me.** §1.94 measured the whole poll channel at **−6 coherent seats** on the
then-sixteen-row panel. If that measurement generalises, removing it should
*improve* `seat_abs_err_coherent`. I predict the panel total **improves — falls
— by between 1 and 25 seats** on whatever rows `compare_history` reports.

A *worsening* larger than 5 seats falsifies the reading of §1.94 that justifies
this change on accuracy grounds. It would **not** reverse the decision, which
rests on the design argument and is the owner's; it would mean the write-up must
say plainly that the model got less accurate, and `ITERATING.md`'s "more honest
usually ships" is what it ships under.

**SECONDARY — the affected population, as an exact set.** Only city-years with
an admitted poll can move. Every 2011 row is unchanged, in every city, because
the register holds no 2011 poll at all. I predict **2011 rows move by exactly
zero** and that at least one 2016 row and at least one 2021 row move.

**MECHANISM — inertness, and it is checkable without a panel.** With
`poll_paths="off"` the seven poll-weighting levers (`poll_credence`,
`poll_house_k`, `poll_deff_subsample`, `poll_screen_sd`,
`poll_drift_per_root_day`, `poll_min_n`, `poll_half_life_days`) become inert at
**every** target, by design rather than by data. `test_levers_are_live` must
therefore report them dead, and the honest response is an `EXPECTED_INERT`
entry per lever whose blocker is the config and whose gate is checkable — NOT a
loosened assertion. If any of the seven still moves a number with the channel
off, the switch does not do what this document says and the change is wrong.

**THE 2026 FORECAST MOVES AND NO BACKTEST CAN SCORE IT.** The live Johannesburg
2026 headline depends on the metro path: `methodology.md` records the channel
moving the DA from 83 to 77 seats. Turning it off should move the DA back up by
roughly that much. **This is unscoreable by construction** and I predict nothing
about whether it is better — only that it moves, and that the published site
will disagree with the model until it is rebuilt, which is the owner's call and
not part of this change.

**I predict no return to any prior total, and a result near one is evidence of
nothing** (CLAUDE.md §1).

**Falsified if:** any 2011 row moves; or no 2016 row moves; or no 2021 row
moves; or the panel worsens by more than 5 coherent seats; or any of the seven
poll levers is still live with the channel off.

## What this change is NOT

* **Not a deletion.** No poll is removed from `polls.json`, no function is
  deleted, and `--set poll_paths=all` restores the previous forecast exactly.
* **Not a claim that polls are uninformative.** §1.95's second job — polls as an
  external check that the model is in the ballpark — is unscoreable and
  unaffected. The check still exists; it stops being an input.
* **Not a site change.** The published site is the 31 August build and already
  disagrees with the model. Rebuilding it is a separate, owner-authorised act.
* **Not a resolution of `methodology.md`.** That page describes a cap retired
  before this change and a side-by-side publication that never existed. It must
  be rewritten to match — but only once this lands, because until it does, the
  forecast DOES use polls and saying otherwise would repeat the most serious
  error that page has carried (it claimed "no poll is currently used at all"
  for a day after that stopped being true).

---

# RESULT — written after both runs, predictions above not edited

Both arms at 1000 draws on 24 rows, same tree, run serially.

    seat_abs_err_coherent=725/@1d9a0e1d+dirty/1000d/pools:843229db/rows=24   polls ON
    seat_abs_err_coherent=723/@1d9a0e1d+dirty/1000d/pools:843229db/rows=24   polls OFF

| | ON | OFF | Δ |
|---|---|---|---|
| `seat_abs_err_coherent` | 725 | 723 | −2 |
| `seat_abs_err` (marginal) | 709 | 702 | −7 |
| CRPS | 545.84 | 541.39 | −4.45 |
| margin over uniform swing | 18.1% | 18.3% | +0.2pp |

Seven of 24 rows moved. Seventeen were identical to 0.000 on both metrics.

| city-year | Δ seats | Δ CRPS |
|---|---|---|
| ekurhuleni 2021 | +6 | +3.80 |
| joburg 2021 | −4 | −3.63 |
| tshwane 2016 | −4 | −1.31 |
| ethekwini 2021 | 0 | −3.12 |
| tshwane 2021 | 0 | +0.23 |
| joburg 2016 | 0 | −0.35 |
| nelsonmandelabay 2016 | 0 | −0.08 |

## Scoring

| clause | verdict |
|---|---|
| PRIMARY — improves by between 1 and 25 coherent seats | **CONFIRMED** (2, the bottom of the range) |
| SECONDARY — every 2011 row moves by exactly zero | **CONFIRMED** — all 8, both metrics |
| SECONDARY — at least one 2016 row moves | **CONFIRMED** — three |
| SECONDARY — at least one 2021 row moves | **CONFIRMED** — four |
| MECHANISM — the seven poll levers go inert at every target | **CONFIRMED** |
| falsifier — worsens by more than 5 coherent seats | not triggered |
| falsifier — any poll lever still live with the channel off | not triggered |

**Nothing was falsified and the primary clause still deserves little credit.**
A band of 1–25 is wide enough to be confirmed by noise, and the −2 it confirmed
is smaller than the +6 that one city-year moved against the change. The clause
that did the work is the 2011 one: exact, falsifiable on any of eight rows, and
it is what establishes that the switch turns off what it claims to.

**The honest headline is not "removing polls improved the model by 2 seats."**
It is that the poll channel's contribution to seat error cannot be
distinguished from zero on this panel, that CRPS prefers its removal a little
more clearly than seats do, and that the decision to remove it was taken on
design grounds which this measurement neither supports nor contradicts.

## Where the pre-registration was wrong in kind

It predicted that seven newly-inert levers would need an `EXPECTED_INERT` entry
each, and said so in the words "NOT a loosened assertion". That was the wrong
instrument. `EXPECTED_INERT` excuses a lever from having to move;
`CONDITIONAL` holds its gate open in both runs and requires it to move anyway.
All seven now carry both. Getting this wrong in the pre-registration cost
nothing because the file's own design corrected it — but the lesson is that
"switch a channel off" silently deletes the tests of everything behind it
unless something deliberately keeps measuring them.

One unpredicted consequence, found by the suite: `polling.SIGMA_TWO_TERM` went
red, because both sigma decompositions live inside the block that no longer
runs. Deleting that red entry would have removed the sole justification for
keeping `poll_house_k` — a switch-off cascading into a lever deletion two steps
away. `MODULE_PERTURB` now measures it with `poll_paths=all` held open.
