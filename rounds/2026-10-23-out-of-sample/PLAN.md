# Plan: backtests from earlier data only

Owner, 2026-10-23 (`OWNER-DECISIONS-ANSWERED.md` items 27–30): for each
election, use the variation between earlier elections, never the election being
forecast; plan every change; have a pollster agent review the plan before
anything is implemented; delete contaminated scores so there is zero chance they
are read; start with Johannesburg. The pollster's answer on keeping the settings
is `POLLSTER-ON-RECORD.md`; what is held is `INVENTORY.md`.

Nothing below is implemented until the review is answered. Each step is written
by an agent and reviewed by another (`~/CLAUDE.md` rule 3). Every run is
pre-registered under `prereg/` first.

## Definitions used throughout

- **Target**: the election being backtested. Johannesburg targets: LGE 2011,
  2016, 2021. Later the other seven metros at the same years.
- **Clean input**: data whose period ends strictly before the target's polling
  day, or published before it (nomination lists, the certified roll). Every
  derived table carries `period_end`; a loader refuses a table whose
  `period_end` is on or after the target.
- **Exception**: the 2022 census population-group split by ward (owner). Any
  other exception needs the pollster's citation and the owner's yes. It is
  labelled on every score it touches ("ex-post input").

## Step 0. Remove the contaminated scores (owner: delete)

0.1 **What goes.** Every backtest score produced with a setting chosen on the
target or a later election, which is every one on disk:
`data/processed/history.json`/`.md`, `validation_2021.json`, `sweep.json`,
the `regime_*_summary.json` files, plausibility and arm outputs, and
`reports/model-changes/*` score tables. The published ones: the
`backtest_*` tokens in `content/joburg/stats.toml` and the pages that print them
(scoring page `docs-public/about-the-model.md`, home, methodology, review).

0.2 **How.** The files move to `quarantine/2026-10-23-in-sample/` outside
`data/` (gitignored, with a README naming what each was). A new test fails if
any code path, page or token references a quarantined file or token. Permanent
deletion of the quarantine folder is the owner's to do (command given to him).
The ledger rows for published backtest tokens are retired with a reason, not
deleted (the ledger is append-only).

0.3 **Pages.** The scoring page says the past scores were withdrawn because
settings had seen the elections scored, and that re-scored figures follow.
Tooltips and pages that quote a backtest score drop it. Per the owner, no
corrections entry is required for the withdrawal itself unless he asks.

0.4 **MODEL-LOG.** One appended entry: every backtest figure in earlier entries
is in-sample and is not evidence. Earlier entries are not edited.

0.5 **Not removed, flagged.** `data/processed/width_record.json` is fitted on
earlier cycles' backtest residuals, which came from runs using the contaminated
settings. The live 2026 forecast reads it for every party's width. It is rebuilt
in step 3 from the clean chain and replaced then; until then the forecast page
says its widths come from in-sample residuals. Removing it now stops the live
forecast. **Owner to confirm.**

## Step 1. Complete the data (Johannesburg first)

Each item ends either with the data on disk, with provenance in `SOURCES.md`,
or with the exact reason it cannot be had.

1.1 National ballot 1999, 2004, 2009, 2014: extract from the zips on disk.
1.2 National ballot 2019, 2024: fetch from the IEC (ids to confirm).
1.3 Votes cast, turnout and special votes: re-extract from the zips into new
    columns.
1.4 Ward for NPE 1999, 2004, 2019, 2024: assign through the preceding LGE's
    VD→ward, flagged as assigned.
1.5 By-elections 2000–06, 2006–11, 2011–16: test whether the IEC dashboard serves
    them; fetch or record why not. Fetch registration/spoilt/votes cast for all
    by-elections if served. Refresh 2021–26 to today.
1.6 MDB ward polygons 2000 and 2006 (2009 layer): fetch.
1.7 Census 2011 by ward (population group): Stats SA SuperWEB2 or a request;
    the owner sends any request.
1.8 Johannesburg 2016–21 by-elections after 2019-07-24: confirm none were held
    or fetch them.
1.9 Fix the records the inventory found wrong (manifest ingester and report
    path, the "national ballot" 6.22% label, the Tshwane roll line in TODO).

## Step 2. Measure every election pair (Johannesburg first)

Pairs: LGE→LGE (2000→06, 06→11, 11→16, 16→21), national→local (NPE 1999→LGE
2000, 2004→06, 2009→11, 2014→16, 2019→21), local→national (LGE 2000→NPE 2004,
06→09, 11→14, 16→19, 21→24). One table per pair, citywide and per ward, each
row carrying the pair and its `period_end`.

2.1 **Per pair, per ward, per party**: votes, share, share ratio (retention),
    share difference; turnout (votes cast ÷ registered) and registration
    change. Wards across delimitations are linked through VDs (no geometry);
    each ward row carries the share of its registration that linked, and a
    ward below a stated threshold is reported as not comparable, with why.
2.2 **Where the share goes.** For every pair, the share each party lost or
    gained is attributed citywide and per ward to: other named parties, new
    parties, independents, and turnout change. This answers "if every party's %
    shrinks, where do the missing % go".
2.3 **Population groups.** Only the 2022 census is held (2011 pending 1.7), so
    group-level change per pair is an ecological estimate on fixed 2022
    composition; it is labelled as such, and for pairs ending before 2022 it is
    an ex-post input.
2.4 **Second order.** For consecutive pairs of the same kind, how the change
    itself changed: direction and size, citywide and per ward (correlation of
    ward changes across pairs, and the distribution of the difference).
2.5 **By-elections.** Each contest against the same VDs at the previous and the
    next LGE: share change in each direction, and the correlation of the
    by-election swing with the next election's swing in that ward. Only the
    2016–21 contests have a next election held (2021); 2021–26 contests are
    scored against 2026 after it.
2.6 Every cell that cannot be computed states why (missing file, no ward,
    link below threshold, party not standing).

## Step 3. Rebuild the backtest, rolling forward by cycle

3.1 **Settings per target from clean inputs only.** Each setting the run reads
    is recomputed per target from step 2's tables with `period_end` before the
    target: turnout correlation, level shrink and its scale, spine k, new-party
    chance and size, slate growth, retention, by-election weight, widths. Where
    the history is too thin (2011 has only 2000 and 2006 local elections), the
    value is declared before the run and bracketed (e.g. turnout correlation 0
    and 1), and the row is labelled "settings declared, not fitted".
3.2 **Switches** (draw method, arrival-group draw, ward noise, level floor):
    each is classified by why it was set. A score-chosen switch is chosen inside
    the rolling origin on earlier targets only; at 2011 it is declared.
3.3 **Mechanical proof, not a register.** Each backtest run records every file
    it opens (Python audit hook on `open`) with that file's `period_end`, and
    fails if any is on or after the target, other than the census. The record
    is part of each scored row.
3.4 **Order.** 2011 targets first; 2016 settings from 2011 outputs; 2021 from
    2011 and 2016. The width record is rebuilt from this chain (step 0.5).
3.5 **Score.** Votes and seats, against uniform swing and persistence, every
    row labelled with its exceptions; headline on the 2016 and 2021 rows, 2011
    beside it (pollster's recommendation; owner to choose).

## Step 4. Stop gap (owner: "do it now")

Before steps 1–2 finish: refit turnout correlation, level shrink and its scale,
and spine k per target from transitions before it, using data already on disk
that step 3.3's audit hook shows to be clean; declare new-party chance and size
at 2011; re-run all 24 rows in cycle order (3.4); publish with the census as the
exception and the switches listed. It uses the same audit hook, so it cannot read
a later file. Expected limits stated on the page: few earlier pairs, provincial
ballot only, no by-elections before 2016.

## Step 5. The 2026 forecast

5.1 The 2026 settings are the last step of the same chain (all data to 2021, and
    by-elections to 2026). If they move the forecast, the old-vs-new report
    (QC §4c) goes to the owner before anything is published.
5.2 Freeze code, settings and inputs before 4 November and publish a dated
    hash; score the frozen forecast afterwards whatever it shows (pollster).

## Step 6. The owner's other items

6.1 **Zille's 490,000 (item 27).** The card's note becomes: This Model expects a
    median of 1,013,993 votes on each ballot, so 490,000 is 48%; the DA reaches
    490,000 on both ballots in 0 of 5,000 simulations. Shipped with the
    tooltip fix.
6.2 **A DA-at-48% scenario.** Raise turnout in the population groups where the
    DA is strongest until the DA reaches 490,000 on both ballots, then read
    which wards it wins and the seats. Method pre-registered; published as a
    scenario, not a forecast.
6.3 **ActionSA (item 28).** Pre-registered measurement: a new party's
    second-local-election retention across the eight metros, on pairs ending no
    later than 2021, and ActionSA's by-election swings against 2021 in the same
    wards. If it holds up it replaces judgement §SJ2 at the next forecast run.

## Order and what blocks what

Step 0 first (it removes the risk the owner named). Step 4 next. Steps 1–2
for Johannesburg, then step 3, then the other metros. Step 6.1 goes with the
pending tooltip release. 6.2 and 6.3 after step 4. Polling day is 4 November
2026; whatever is not done by the freeze is reported as not done.

## Questions for the pollster review

1. Is anything here still in-sample, or is any clean input wrongly excluded?
2. Is the census the only acceptable exception, or does the literature accept
   others the plan should use (e.g. the 2024 roll at a 2021 target: no)?
3. Is 2.3 (fixed 2022 composition) acceptable, and how should it be labelled?
4. Is the threshold approach in 2.1 for linking wards across delimitations
   sound, or should step 1.6's polygons be required first?
5. Is the step 3.3 audit hook sufficient proof, and what would it miss?
6. Step 4: is a stop gap on the current pipeline worth publishing, or does it
   mislead while step 3 is pending?
