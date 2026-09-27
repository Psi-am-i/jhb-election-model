# What is left to do

Three lists. Nothing is deleted from them; items move to **Done** with a date
and stay visible.

⛔ **For list 1, whether something changes a published number is NOT a reason to
delay it.** The measure is whether the model is defensible, not whether today's
output matches yesterday's. A change that makes the forecast less flattering and
more defensible is a change that ships.

---

# 1 · The model — is it right?

## Open, in the order I would take them

**Independents cannot win anything, and the model is charged for it.**
`IND` is on the certified ballot and on our roster, and has no pool membership,
so no simulation can seat an independent. Independents took 11,904 votes in
Johannesburg in 2021 — 0.645%, tenth of 57 parties, above the African
Independent Congress — and 52 council seats nationally. In the backtest the
model hands their seats to parties and takes the error. Registered as an
assumption on 2 September and unactioned since. Pre-registration written;
testable out of sample against eThekwini 2011 and 2016, where independents won
wards.

**A merged party's vote is deleted instead of transferred.**
The roster drops 29 parties. Two of the three largest merged into parties that
ARE on the ballot — GOOD into RISE Mzansi (RISE is the Gauteng ballot party),
Forum 4 Service Delivery into ActionSA — and their vote vanishes rather than
moving. It matters most for RISE, which did not contest Johannesburg in 2021 and
is therefore sized as an arrival, the model's weakest area, while the 6,773
votes of the party it merged with are thrown away. Splits already work this way
in reverse, with a measured fraction; mergers need the same with a retention
factor below 1.

**The largest-party headline is decided by a tie-break.**
`np.argmax` awards every DA/ANC tie to the DA because the DA has the higher mean.
Sole largest: ANC 47.20%, DA 45.52%, tied 1.82% — 91 draws. Published as
47.34% / 47.20%, which prints as "47% / 47%" and fires the "dead heat" sentence.
Split the ties evenly and the ANC leads 48.1 to 46.4 and that sentence does not
fire. It is one rule applied asymmetrically to two figures in the largest type
on the site.

**The roster is a newspaper count.**
82 parties, typed from reporting that contradicts itself (82 in three outlets,
75 in two, all citing the same certification). `complete = true` licenses
deleting 27 parties. The IEC publishes no per-municipality list anywhere
reachable — every path checked and recorded at the flag itself. **The list has
to be requested from the IEC.** Count stays at 82 until it arrives.

**The validation table describes itself wrongly.**
`/about` says "every party that won a seat in 2021, in every city" over a table
of the largest few, and prints a total computed over all parties beneath rows
that do not add to it. The code fix is written; applying it needs the artefact
regenerated, which is the first item on this list.

**The baseline field excludes the honest opponent.**
Three baselines are used and the README says a fourth — the roster-aware uniform
swing — is "the honest opponent at 2021". The published "+37% better" is against
the weaker field.

**A published sentence contradicts a registered decision.**
`/forecast` says "every party on the IEC's certified ballot is named in the
simulations". Independents are on that ballot and are excluded by decision. This
is a correction, not a rewording. *(Owner: add, leave for now.)*

## Done

* **The backtest score moved; it was not an implementation error.** Total error
  over eight cities 213.9 → 224.1. Commit `f33528f` (14 Aug) stopped the 2021
  backtest sizing ActionSA from a split three years after the election; 213.9
  was contaminated. Blind review: `audits/2026-09-27-backtest-difference/`.
  Republished as a bugfix. *(27 Sept)*
* **The arrows pointed the wrong way** — four figures frozen as "published 31
  August" came from a build that was never deployed; three showed a rise where
  the published number had fallen. Re-sourced to the publication ledger, arrows
  recomputed, correction filed, and a test now refuses a frozen figure that does
  not cite the ledger and match it. *(27 Sept)*
* **Two medians were quoted against each other** — 118 across all simulations
  against 144 among those where the coalition wins, both called "median". Both
  now named. *(26 Sept)*
* **A range printed over one simulation** — "34 – 34 seats" now collapses to a
  single figure and its source says how many draws it covers. *(27 Sept)*

---

# 2 · The interactive — what it needs to go live

## Decided

* **Seat-law comparison first.** Four laws, already computed at the full 5,000
  draws, no browser engine needed. The data now ships as `site/regimes.json`.
* **Controls that survive measurement:** the seat law, how much support moves
  within a pool, and how much weight by-elections carry. Per-VD turnout noise and
  ward-local by-elections were dropped — measured at 0.01 and 0.04 seats.
* **Polls:** a row per poll with its caveat, a toggle each, one trust slider from
  no effect to taking the poll as the outcome, the spread between houses shown,
  the average as one option. Our own trust is zero, which is what we publish.
* **Turnout** by population group and by area. The geography exists; the grouping
  is a choice between derived compass sectors and the City's official regions.
* **Scoring a reader's map:** their percentile in the distribution of
  draw-to-draw distances, not a probability — independent per-ward marginals
  would rank the model's own best guess above 95% of the maps it actually draws.
* **A reader's controls never touch the published forecast.**

## Open

* **The input route is not settled.** See `INPUT-ROUTE.md`. The question is not
  only size but whether each route still lets a lever act at the right point in
  the model.
* **What the page shows before a reader touches anything**, given that a
  300-draw default is the first 300 of the published 5,000 and prints different
  headline percentages.
* **Turnout by group and by area has to be built** — it does not exist.
* **The poll dial has to be built.** It is a new parameterisation, not a
  relabelling of the existing one.
* **No browser measurement exists.** The timing we have is Node, explicitly a
  floor.
* **Validation of a shared forecast** — a link carrying 135 ward calls, a PR
  vector and lever positions is untrusted input and nothing bounds it.
* **What happens to the coalition table, the ward map and the tested claims**
  when a lever moves.
* **The judgement calls have no published surface** since the sheet was
  withdrawn as unreadable.

## Done

* Pyodide speed measured; the constraint is the input size, not the draw rate.
* Effect sizes measured; two candidate controls deleted.
* Seat-law data lifted out of gitignored storage into the site bundle.

---

# 3 · Everything else

**Before the election**

* **Post-election scoring must be frozen before 4 November** — seat count per
  party, correct party by ward, correct ward-versus-PR allocation, scored
  identically for readers and for us. Still needs the result-ingest path and the
  party-name mapping, and the IEC spells four Johannesburg parties differently
  from our own files.

**Publishing**

* ~~Six commits are unshipped~~ — deployed and verified live 27 Sept
  (`fbb829e`).
* The portal page ships without being scanned by the number gate.

**The newsdesk**

* Thirteen pull requests to close; the rewritten rules are not live because they
  sit in this repository and the routine reads GitHub's copy.
* The routine has produced nothing since 20 September.
* Two `CLAUDE.md` files exist — pushing this line to GitHub would delete the
  routine's instructions.

**Data**

* The IEC's per-voting-district 2026 registration is not published; only ward
  level is. Worth requesting alongside the roster.
* The IEC's own page gives two city totals 613 apart, unreconciled.
* Tshwane is missing both its roll and its roster.

**Housekeeping**

* **Discard list reviewed 27 Sept; deletion not yet done** (the agent's delete
  was blocked by the permission check, so the owner runs it):
  - `splinter-rule-and-historical-tail` — safe. Its tip tree is identical to
    `efa06f7` on `remediation` ("tree identical to splinter-rule-…"), so all
    content survives as a squash. Its 56 commits have no patch-equivalent on
    `remediation`, so tag it before deleting to keep the per-commit history.
  - `atlas/…` tip `a5e8c5d` (WIP, 2 Sep) — safe. Its four files diff empty
    against `af054e3` on the splinter branch, whose content reached
    `remediation` via `efa06f7`.
  - Scout's 14-Sep stash — not reviewed: Scout offline on 27 Sept.
  - The site was published from `remediation`, which is not on the list.
* ~~Commits are unpushed to Atlas~~ — `remediation` pushed to `atlas` 27 Sept.
  GitHub `origin` is not pushed (see the two-`CLAUDE.md` item).
