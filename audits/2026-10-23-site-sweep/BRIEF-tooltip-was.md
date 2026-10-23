# Brief: a live figure's tooltip keeps its previous value

Owner, 2026-10-23: "When a number changes we are meant to show what it was and
what it is now. Every number I've looked at just gives the 21 October date …
we need a proper test for that."

## The defect

`build_site.tooltip_text` adds "Was X on <date>" only when the figure moved in
the edition being built (`part == this`). The next publication that repeats the
figure unchanged drops the clause. Example from `publications/joburg/ledger.jsonl`:

| published | `p_anc_largest` | movement |
|---|---|---|
| 26 Sep – 17 Oct | 47% | new / none / rounding |
| 21 Oct 16:46 | 58% | material |
| 22 Oct 11:38 | 58% | none |
| 23 Oct 03:02 | 58% | none |

The 21 October page said "58% chance since 21 October. Was 47% on 26
September." The 22 and 23 October pages say "58% chance since 21 October."
In the current build, 718 tooltips carry no live "Was" clause; 276 of the
ledger's 505 tokens have had more than one published value.

## Required

1. **One function in `src/publication.py`** over ledger rows (ignore rows with
   `superseded_at`) that returns, per token, the last published display that
   differs from the current one, and the date that value first appeared. Its
   date must come from the same logic as `run_starts`, so the two cannot
   disagree. Rows whose movement is `rounding` or whose display did not change
   do not end a run of one value.
2. **Thread it into `_ledger_candidates`** as new fields (e.g. `prior`,
   `prior_since`). Do not change the meaning of `previous` /
   `previous_since`; `classify` and the arrows path read them.
3. **`tooltip_text`:** a live figure (not `fixed`, `tracks`, `historical` or
   `date_long`) that has a prior distinct value always ends line 1 with
   "Was <prior> on <date that value first appeared>.", in the moving edition
   and every later one. The frozen and date branches are unchanged. Update the
   docstring's description of the cases.
4. **Tests (`CLAUDE.md` §4, the four-part rule):**
   - Unit (`tests/test_tooltip_says.py`): a constructed ledger in which a token
     moves in edition N and is republished unchanged in N+1 and N+2. The Was
     clause, value and date are asserted in all three. A token that never
     moved has no Was clause. A superseded row is not used as a prior value.
   - Site scan (the published-page test family): from the ledger, the set of
     live tokens rendered on the built site that have a prior distinct value;
     from the built HTML, the set of those tokens' tooltips that carry
     "Was <prior> on <date>". Assert the two sets are equal (both directions),
     that the population is non-empty and within a two-sided bound as a
     fraction of live tokens rendered, and that a constructed violation (one
     Was clause stripped from a copy of a page, and one added to a token that
     never moved) is caught and goes quiet when reverted.
   - Make sure the new modules are collected by `tests/run_all.py`.
5. **Records:** the docstring; `MACHINERY.md` if it describes the tooltip; a
   `TODO.md` line is not needed.

## Limits

- Work on branch `site-sweep-1`. Commit your work there; do not push, build
  with `--publish`, deploy, or write into `data/**` or `publications/**`.
- You may run `src/build_site.py` without `--publish` to regenerate `site/`
  for the scan test, and the targeted test modules with
  `nice -n 15 .venv/bin/python tests/run_all.py -k <module> -j 1`. Do not run
  the whole suite; the reviewer does that.
- `nice -n 15` on anything heavy. Do not sub-delegate.
- Report: the diff summary, the commands run and their exact counts, and the
  count of live tooltips with a Was clause in the regenerated `site/` against
  the count of live tokens with a prior value.
