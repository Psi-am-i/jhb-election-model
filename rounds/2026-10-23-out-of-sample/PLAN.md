# Plan: backtests from earlier data only (v2)

Owner, 2026-10-23 (`OWNER-DECISIONS-ANSWERED.md` items 27–30): for each
election, use the variation between earlier elections, never the election being
forecast; plan every change; a pollster agent reviews the plan before anything is
implemented; delete contaminated scores so there is zero chance they are read;
start with Johannesburg. The pollster's answer on keeping the settings is
`POLLSTER-ON-RECORD.md`; what is held is `INVENTORY.md`; the review of v1 is
`PLAN-REVIEW.md`, and v2 applies all 27 of its changes.

Each step is written by one agent and reviewed by another (`~/CLAUDE.md` rule 3).
Every run is pre-registered under `prereg/` first.

## Definitions

- **Target**: the election being backtested. Johannesburg: LGE 2011, 2016, 2021;
  later the other seven metros.
- **Clean input**: data whose period ended before the target's polling day **and**
  that was public before it (nomination lists, the certified roll, earlier
  results). A derived table's `period_end` is computed by the code that writes
  it, as the latest `period_end` of its inputs; a loader refuses any table whose
  `period_end` is on or after the target.
- **Exception**: Census 2022 ward composition, and the 2021 VD→ward
  delimitation used to place it on earlier wards (owner). Census 2011 is ex-post
  at a 2011 target and clean at 2016 and 2021; Census 2001 is clean at 2006 and
  2011. Every score an exception touches is labelled "ex-post input". Any other
  exception needs a citation and the owner's yes.

## Step 0. Remove the contaminated scores (owner: delete)

0.1 **Retire the published scores first** (`src/stats.py` builds the
    `backtest_*` tokens from `history.json`, so moving the file first breaks the
    build): retire the tokens in the ledger with a reason (the ledger is
    append-only) and remove them and their sentences from the scoring page,
    home, methodology and review.
0.2 **Then move the files** outside the repository, to
    `~/projects/quarantine/jhb-election-model-2026-10-23-in-sample/`, with a
    README naming each file: `history.json`/`.md`, `validation_2021.json`,
    `sweep.json`, `regime_*_summary.json`, `width_budget.json`, every past
    target's `seat_draws.csv`, `ward_winner_probs.csv`, `coalition_*.csv` and
    `regime_*_seat_draws.csv`, plausibility and arm outputs, and the score tables
    in `reports/model-changes/`, `prereg/` and `audits/` (committed text is
    handled in 0.4). Permanent deletion is the owner's (command given).
0.3 **The test.** Any backtest score printed on a page or held in a token
    carries a label, in-sample or forward-chained; no code reads a quarantined
    path. A planted unlabelled score fails it and reverting clears it. It does
    not forbid `compare_history` writing a new `history.json`.
0.4 **Committed text.** State the population of files that quote in-sample
    figures (a grep for digits beside "coherent", "city-years", "backtest",
    re-run at implementation; the review's counts are upper bounds) and add one
    banner at the top of `MODEL-LOG.md`, `JUDGEMENT-CALLS.md` and
    `POLLSTER-ON-RECORD.md`: every backtest figure dated before 2026-10-23 is
    in-sample and is not evidence. Entries are not edited. Code comments that
    justify a constant by a panel score are tagged when step 3.1 reclassifies it.
0.5 **Memory.** Auto-memory index entry, and a MemPalace KG fact superseding the
    old belief, saying the same.
0.6 **Corrections.** The published backtest figures were live statements of
    out-of-sample accuracy and were wrong, so item 26's rule applies: one
    corrections entry in the agreed format (what was wrong, what changed).
0.7 **Kept, labelled.** `width_record.json` sets every party's width in the live
    2026 forecast. For 2026 it reads only data before 2026, so it is not a leak;
    it is fitted on residuals around in-sample centres, so the widths are likely
    too narrow. The forecast page says so. Rebuilt in steps 3–4.

## Step 1. Complete the data (Johannesburg first)

Each item ends with the data on disk with provenance in `SOURCES.md`, or with the
exact reason it cannot be had.

1.1 National ballot 1999, 2004, 2009, 2014: extract from the zips on disk.
1.2 National ballot 2019, 2024: fetch from the IEC. Fix the "national ballot"
    label on ActionSA's 6.22% (a provincial-ballot figure).
1.3 Votes cast, turnout, special votes: re-extract from the zips as new columns.
1.4 Ward for NPE 2004, 2019, 2024 through the preceding LGE's VD→ward; NPE 1999
    through LGE 2000's (the following election). Each labelled as assigned.
1.5 By-elections 2000–06, 2006–11, 2011–16: test whether the IEC dashboard
    serves them; fetch or record why not. Registration, spoilt and votes cast for
    every by-election if served. Refresh 2021–26 to today. Johannesburg 2016–21
    after 2019-07-24: confirm none or fetch.
1.6 MDB ward polygons 2000 and 2009 (= 2006): fetch.
1.7 Stats SA: Census 2001 and 2011 by ward (population group), in one request
    the owner sends; Community Survey 2016 at municipality level as a citywide
    check for 2016.
1.8 Fix the records the inventory found wrong (manifest ingester and report
    path; Tshwane roll line in TODO).

## Step 2. Measure every election pair (Johannesburg first)

Pairs: LGE→LGE (2000→06, 06→11, 11→16, 16→21); national→local (1999→2000,
2004→06, 2009→11, 2014→16, 2019→21) and local→national (2000→04, 06→09,
11→14, 16→19, 21→24), each on both the national and the provincial ballot.
National→national pairs are left out unless the owner asks. Every table carries
its computed `period_end`.

2.1 **Per pair, per ward, per party**: votes, vote change, share, share ratio
    (retention), share difference; turnout (votes cast ÷ registered);
    registration change. Wards are linked across delimitations through VDs with
    `pools.reproject`; the link threshold is declared in `JUDGEMENT-CALLS.md`
    before the run, a second threshold is reported beside it, the distribution of
    linked shares is published, and links resting on station names are counted.
2.2 **Where the votes go.** Shares always add to 100%, so they cannot all
    shrink; the question has an answer in votes. Each party's vote change per
    ward is split exactly into registration, turnout and share terms (votes =
    registered × turnout × share, Shapley split). Votes no party keeps go to
    abstention, read off the turnout term. Net flows are reported with
    Duncan–Davis bounds; gross party-to-party flows are labelled ecological
    estimates.
2.3 **Population groups.** An ecological estimate on fixed 2022 composition,
    for description only: it mixes composition change with behaviour change.
    Labelled so, with bounds beside every point estimate; Census 2001/2011 used
    for the pairs they precede once held.
2.4 **Second order.** For consecutive pairs of one kind: how the change itself
    changed, direction and size, citywide and per ward.
2.5 **By-elections.** Each contest against the same VDs at the previous and the
    next LGE, both directions, and the correlation of the by-election swing with
    the next election's swing in that ward. Only 2016–21 contests have a next
    election held. By-election turnout needs 1.5's fields.
2.6 Every cell that cannot be computed says why.
2.7 **National or provincial.** On pre-target pairs only, which ballot predicts
    the local result better; this settles which one the model's national route
    reads.

## Step 3. Rebuild the backtest, rolling forward by cycle

3.1 **Every constant, not a list.** Classify every entry of
    `montecarlo.MODULE_CONSTANTS`, its not-declared block, every other
    module-level constant in `montecarlo`, `levels`, `pools`, `fold`, `turnout`
    and `width_record`, and every key in the four `backtest.py` registers as:
    fitted on results / typed then confirmed on the panel / mechanism or statute
    / numerical. Named at least: `SPLINTER_PARENT_WEIGHT`, `SD_FLOOR`,
    `RHO_ANCHOR_LO/HI`, `LOCATION_CLAMP`, `plan_bounds`, `entrant_geography`,
    `turnout.py`'s `w_recency` and `kappa_bye`, the curated event lists (each
    entry needs a dated pre-target source or is listed as judgement),
    `fold*_parameters.csv`'s calibration and `party_crosswalk.csv`. The
    completeness guard is extended to all of them. Each fitted or confirmed one
    is refit per target from step 2's clean tables, or declared before the run
    and bracketed where history is too thin (2011), and that row is labelled
    "settings declared, not fitted".
3.2 **Arrivals.** Presence comes from nominations (clean); size is refit per
    target or declared.
3.3 **Switches.** Each classified by why it was set; a score-chosen one is chosen
    inside the rolling origin on earlier targets; at 2011 declared.
3.4 **Proof, in three parts.** Pre-election extracts per target and delimitation,
    so a run opens no result file at or after its target; every artefact
    regenerated in an isolated tree per target, one process per target, under an
    `open` audit hook that fails on a later file; a planted-violation test that
    fails and clears when reverted. Constants have no mechanical proof; 3.1
    covers them.
3.5 **Order.** 2011 targets first; 2016 settings from 2011; 2021 from 2011 and
    2016. The width record rebuilt from this chain. `bye_value.py` made
    target-aware before any by-election enters a backtest; at 2021 its weight is
    fitted on 2016–19 contests against NPE 2019 or declared.
3.6 **Score.** Votes and seats; CRPS as the headline; baselines uniform swing,
    persistence, and Murphy's (1992) optimal combination of persistence and
    climatology; beside each score, the number of alternatives tried for each
    score-chosen decision. Headline on 2016 and 2021 with 2011 beside it
    (owner to choose).

## Step 4. Stop gap (owner: "do it now")

Refit turnout correlation, level shrink and its scale, and spine k per target
from transitions before it, using data on disk; declare new-party chance and size
at 2011; rebuild the width record per arm outside `data/`; re-run all 24 rows in
cycle order. No pools re-emit is needed (these are applied at run time).
Published with the old and new scores side by side and the parts still in-sample
listed (3.1's constants, arrivals' size, the switches); never called
out-of-sample. If the width rebuild cannot finish before the freeze, publish
only the withdrawal and the hash.

## Step 5. The 2026 forecast

5.1 **Freeze by 31 October**, before special voting (dates to confirm with the
    IEC): run `src/inputs_preflight.py --strict`, freeze code, settings, specs and
    inputs on the current settings (legitimate for 2026: all chosen on data to
    2021), and publish a dated hash. Score the frozen forecast after 4 November
    whatever it shows.
5.2 After polling day: the chain-derived settings for the next forecast.

## Step 6. The owner's other items

6.1 **Zille's 490,000 (item 27).** The card's note, in the owner's words with
    the figures from `stats.toml` tokens: "This Model expects a median of
    1,013,993 votes on each ballot, so 490,000 is 48%. The DA reaches 490,000 on
    both ballots in 0 of 5,000 simulations. If the DA did in fact win 48% that
    would take some of the ANC's wards." Ships with the tooltip release.
6.2 **DA-at-48% scenario.** Pre-registered feasibility check first: can turnout
    in the DA's strongest groups reach 490,000 DA votes on each ballot at turnouts
    no higher than the highest on record for those VDs (`turnout.py`'s
    `thi_pattern`)? If not, the scenario needs a share shift too and says so.
    Published as a scenario. After polling day.
6.3 **ActionSA (item 28).** Sample: parties with a first and a second local
    election both by 2021 (COPE, NFP, AIC, EFF by the review's count, to be
    checked against the files), across eight metros; the effective sample is the
    number of parties. Spread per party, clustered by party, no single median for
    a bimodal record; plus ActionSA's by-election swings against 2021 in the same
    wards. The cap's code path is stated with it. Only before the freeze if the
    old-vs-new report reaches the owner by 29 October.

## Order

| When | Work |
|---|---|
| 23–24 Oct | Draft the Stats SA request (1.7) for the owner to send; test the IEC dashboard for pre-2016 by-elections (1.5) |
| 23–26 Oct | Step 0 in its order; 6.1 with the tooltip release |
| 24–29 Oct | Step 4, pre-registered; 6.3 only if its report reaches the owner by 29 Oct |
| by 31 Oct | Step 5.1 freeze and hash |
| after 4 Nov | Score the frozen forecast; steps 1–3 for Johannesburg; 5.2; 6.2; the other metros |
