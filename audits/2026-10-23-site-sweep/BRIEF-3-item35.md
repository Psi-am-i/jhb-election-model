# Brief 3: owner item 35, the wording before the freeze release

Owner's answers, 2026-10-24, are in `OWNER-DECISIONS-ANSWERED.md` item 35,
which quotes them in full. Branch `site-sweep-1`. A writer makes the edits; I
review the diff; then `/code-review`, UAT, the owner's yes. Every reader-facing
word below is the owner's or was approved by them; **add no other words**
(memory `no-unapproved-reader-words`). If an edit seems to need a word this
brief does not give, stop and list it in the report.

## Reader-facing changes

1. **New corrections entry** (`docs-public/corrections.md`, with the other
   entries of this release, same markup as theirs):
   - Heading: "The model uses only what was known before each election it is
     tested on" — published 2 October 2026, corrected <release date>.
   - **What was wrong.** That overclaimed, because several scores on previous
     elections had been inadvertently using data that included those same
     elections.
   - **What is right.** This Model's 2026 forecast uses only what was known
     before the 2026 election. Its scores on past elections are withdrawn;
     re-scored figures, for earlier elections, will be published on the
     methodology page.
2. **The "deliberate choice" entry**: its What is right becomes "This Model no
   longer uses party splits that happened after the election it is tested on."
   Its heading, dates and What was wrong do not change.
3. **The "forecasting that election from earlier ones" entry**: its What is
   right becomes "The ward counts are withdrawn with This Model's other scores
   on past elections."
4. **Methodology**: remove the two sentences saying the DA and ActionSA draw
   from the same population group so that when one rises the other tends to
   fall (a mild offset). In the 23 October correction "Parties that compete for
   the same voters trade support", add "and the methodology" to its What was
   wrong, at the place that names the page the claim was on.
5. **Methodology**: "Halfway is the owner's choice" becomes "Halfway is our
   choice."
6. **Home stamp**: "This Model's simulations as of <date> · 5,000 simulations"
   becomes "5,000 of This Model's simulations as of <date>" (the count and date
   stay tokens).
7. **Coalition table, 10% cut** (`src/render_sheet.py`, who can govern): a
   combination is listed only if it governs (reaches a majority) in at least 10%
   of simulations, in addition to the existing smallest-majority and
   no-passenger rules. A named constant beside `MIN_SMALLEST`, with a comment
   citing the owner's 2026-10-24 words. On the frozen forecast's page this
   should take the table from 21 rows to 16; report the count you get.
   - "How to read it" gains: "Combinations that govern in fewer than 10% of the
     simulations are left out." (the 10% from the constant, not typed).
   - **"Single party majority" preset**: shows "No party wins a majority alone
     in 10% or more of the simulations." when no party does, and otherwise one
     row per party at or above the cut, with its chance.
8. **The who-can-govern lede** becomes only: "The ANC without the DA has N
   workable majorities, n of them with a better than even chance of reaching
   {majority} seats; the DA without the ANC has M, m of them with a better than
   even chance." N, n, M, m are tokens counted over the listed rows. The two
   sentences beginning "If the DA rules out the ANC, the EFF and MK" and "With
   the smaller parties as well" are removed, with their tokens
   (`govern.da_best_without`, `govern.da_with_small_without`) left for
   `revive_retire.py` to retire. Expected at the 10% cut: ANC 8 and 4, DA 7 and 4.

## Mechanical changes (no reader words)

9. Every new corrections entry of this release carries the release date as its
   corrected date. Find how the step-0 entry's date is set; make all of them
   come from one place set at publish, not typed per entry. Report how.
10. The in-sample banner in the model-change report template prints only when
    that report's `backtest.json` holds scores; `tests/test_quarantine.py`
    stays the guard.
11. Delete the three stale `[[audit.fixed]]` entries '1', '16' and '1.296' in
    `content/joburg/stats.toml`, if they are still there; report what each was.
12. Regenerate the node "stored native fixture" against the re-exported draws.

## Limits

- No forecast number changes; no `montecarlo.py`, no re-emit, no writes under
  `data/` (run `src/backup_ignored.py` first if anything must).
- `nice -n 15`, BLAS threads 2, one heavy process at a time. Targeted site
  tests only (`tests/run_all.py -k ...`); no whole suite.
- Re-render the pages the changes reach and commit, one commit per numbered
  group is fine. Do not run `revive_retire.py --apply`, `build_site.py
  --publish`, or deploy.
- Do not sub-delegate. Report: each change with before and after text, the row
  and token counts, test output, commits.
