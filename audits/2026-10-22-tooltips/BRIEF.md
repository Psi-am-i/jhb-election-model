# Tooltips: one short structure everywhere (22 October 2026)

Owner, 2026-10-22, verbatim:

> tooltips are confusing and wordy. ie, 34%. Was 45%. Published 6 October
> 2026; now 21 October 2026. Source: seat_draws.csv, 5,000 simulations, the
> party alone with the most seats, computed at build from the current model
> run.
>
> Make it simple and use the idnetical sructure everywhere:
>
> 35% chance since 21 October. Was 45% on 6 October.
> SOURCE: This Model. The % of 5,000 simulations where the ANC was the largest party.

Written before the code; not amended after.

## The structure

Two lines, the same on every page that shows a figure's tooltip (home,
Our Forecast, the claims and claim pages, the articles, Your Forecast's
first paint, and any tooltip the page scripts write).

**Line 1, the figure and its history.** Dates as "21 October" (no year:
every date on the site is 2026; the year is shown only for a date in
another year). `<v>` is the figure as displayed, followed by its unit word
where it has one ("chance", "seats", "wards"; none for a plain share or a
count whose noun is in line 2).

| the figure | line 1 |
|---|---|
| moved since the last publication | `<v> since <date of this publication>. Was <old> on <date the old value was first published>.` |
| unchanged | `<v> since <date its current value was first published>.` |
| first published in this edition | `<v> since <date of this publication>.` |
| a build that is not a publication (UAT, dry run) | the same, with "since <date>" for this edition replaced by "in this build" |
| a frozen figure in a dated piece whose live counterpart moved | `<v> on <date the piece published it>. <now> since <date>.` |
| a frozen figure whose live counterpart has not moved | `<v> on <date>.` |

**Line 2, the source.** `SOURCE: <who>. <what the figure is, in plain words>.`
`<who>` is "This Model" for every figure computed from the model's run;
otherwise the outside source by name ("IEC 2021 results", "Statistics South
Africa, Census 2022", the poll's house, a news outlet for a quote's figure).
The plain sentence says what was counted, over what, with the party or
group named: "The % of 5,000 simulations where the ANC was the largest
party." No file names, no code names, no "computed at build".

## How

* One function writes both lines (in `src/build_site.py`'s tooltip code, the
  one place they are written now); every tooltip on the site comes from it.
* The plain sentences: one table (`src/tooltip_says.py`), keyed by token
  name patterns, each pattern giving the unit word, `<who>` and the sentence
  template, filled with party and group names from `render_sheet.NAMES` and
  the run's simulation count. The technical source stays in the ledger and
  in `NUMBERS-REVIEW.md`, where it is read by us, not readers.
* A test: every token the build publishes matches exactly one pattern (both
  directions: no published token without a sentence, no pattern matching
  nothing), and a constructed unmatched token stops the build.
* The arrows (▲▼) are unchanged.

## Checks (QC.md §4b)

Diff reviewed by another agent before the build; the build and
`deploy_check`; the page test modules; the whole suite once for the UAT
version. Live with the owner's yes, in the same release as the 22 October
site round if both are ready.
