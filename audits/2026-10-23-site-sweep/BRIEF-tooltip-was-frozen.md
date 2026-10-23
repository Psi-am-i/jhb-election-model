# Brief: a corrected frozen figure's tooltip says what it was

Follows `BRIEF-tooltip-was.md` (commit f51b54a), which covered live figures only.
Owner, 2026-10-23: "When a number changes we are meant to show what it was and
what it is now … in every case the original has been changed and the
correction says the exact same thing as the article."

## The defect

A frozen figure (`mode = "fixed"`, `historical` or `tracks`) takes the
`tooltip_text` branch that prints "<value> on <date first published>". When a
frozen figure is corrected, its value changes and that branch prints the new
value against the old date. After a `--publish` build of the current tree:

| token | page | ledger | tooltip |
|---|---|---|---|
| `rev0806_da_largest_fixed` | review | 63% until 23 Oct, then 61% | "61% chance on 6 August." |
| `rev0806_da_minority_viable` | review | 61%, then 53% | "53% chance on 6 August." |
| `hist_laingsburg_da_share` | laingsburg-2021 | 23%, then 24% | "24% on 8 August." |
| `claim_others_shed` | claim card | 190,000, then 248,674 | "248,674 on 8 August." |

On 6 August the review said 63%, not 61%. The only trace of the old value was
the move arrow, which shows only in the edition that moved it.

## Required

1. In `tooltip_text`'s frozen branch: a figure with a prior distinct published
   value (`prior`, `prior_since`, from `publication.prior_values`) prints
   "<value> since <date the current value first appeared>. Was <prior> on
   <date the prior value was first published>." The prior value's date uses the
   branch's existing rule for a first publication (earliest of the dated
   passage, `on_site`, first ledger row) when the prior run is the token's first
   run, else `prior_since`. A frozen figure that never changed is unchanged
   ("63% on 6 August."). A `tracks` figure keeps its tracked-live clause after
   these.
2. Docstring updated.
3. Tests:
   - unit (`tests/test_tooltip_says.py`): a constructed ledger where a fixed
     token is published at 63% (first published 6 August via `dated_on`) and
     corrected to 61% in a later edition, then republished unchanged: both
     editions say "61% chance since <correction date>. Was 63% on 6 August."
     A fixed token never corrected says only "on <date>".
   - the site scan in `tests/test_published_page.py` (`_was_population` /
     `was_faults`) covers every token on the page, frozen as well as live, with
     the expected text for each; bounds restated; the planted-violation tests
     extended to one frozen figure.
4. Rebuild `site/` with `src/render_sheet.py` then
   `src/build_site.py --as-published`, and report the four tooltips above as
   they now read. Note: `--as-published` builds against the last publication
   (23 October 03:02), where these four had already moved; the scan must hold
   for that build.

## Limits

Branch `site-sweep-1`; commit there. No push, `--publish`, deploy, ledger write,
or writes under `data/**`. Targeted modules only, `-j 1`, `nice -n 15`:
`tooltip_says`, `published_page`, `provenance_dates`, `publication_ledger`,
`model_index` (regenerate `MODEL-INDEX.md` if it changes). Do not sub-delegate.
Report files changed, the four tooltips' text, the scan's population counts,
commands with counts, the commit id.
