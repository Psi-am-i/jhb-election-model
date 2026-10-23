# Brief: withdraw the in-sample backtest scores (plan step 0)

Owner, 2026-10-23 (`OWNER-DECISIONS-ANSWERED.md` item 29): "DELETE ANY
CONTAMINATED SCORES OR RESULTS. I WANT EXACTLY ZERIO chance they are being read
and accepted blindly." Every backtest score on disk was produced with settings
chosen on the election scored or a later one
(`rounds/2026-10-23-out-of-sample/POLLSTER-ON-RECORD.md`). The plan is
`rounds/2026-10-23-out-of-sample/PLAN.md` step 0; its review is `PLAN-REVIEW.md`.

## Required, in this order

1. **Retire the published scores.** In `content/joburg/stats.toml`, every token
   whose `source` reads `validation:` or `history:` (55 at the time of writing;
   count them yourself and report the list), and any other token that states a
   backtest result (e.g. the home page's past ward-winner counts: find them by
   their tooltips in `src/tooltip_says.py` and by `src/stats.py`'s readers of
   `history.json` / `validation_*.json`). For each: remove it from every page and
   from `stats.toml`, and retire it in the ledger with
   `publication.retire(city, token, reason=...)` and one reason naming this
   brief. Pages: the scoring page (`docs-public/about-the-model.md` and
   `src/build_validation.py`, which generates it), methodology, home
   (`content/joburg/home.toml`), review, and anything else the build reports.
   Sentences that only existed to carry a score go with it; do not leave a
   sentence with a hole.
2. **The scoring page** becomes a short withdrawal notice following `STYLE.md`:
   the past scores were withdrawn on 23 October 2026 because several of This
   Model's settings had been chosen on the elections they were scored against;
   re-scored figures, from earlier elections only, will be published here. No
   figures. `build_validation` must not write scores while this holds; it may be
   reduced to writing the notice.
3. **Corrections entry** (`docs-public/corrections.md`, the agreed format: the
   quoted error, published date, corrected date; what was wrong; what is right).
   What was wrong: the scoring page and the pages quoting it presented the
   backtest as a test of forecasting from earlier elections; several settings
   had been chosen on records including the elections scored. What is right:
   the scores are withdrawn; re-scored figures will be published.
4. **Move the files**, only after 1–3 build clean. Run
   `.venv/bin/python src/backup_ignored.py` first. Move (not copy, not delete)
   to `/Users/simondavis/projects/quarantine/jhb-election-model-2026-10-23-in-sample/`
   (outside the repository), keeping relative paths, with a `README.md` listing
   each file, its size, its sha256 and why it is there:
   - `data/processed/history.json`, `history.md`, `validation_*.json`,
     `sweep.json`, `regime_*_summary.json`, `width_budget.json`;
   - every past target's (2011, 2016, 2021, every city) `seat_draws.csv`,
     `ward_winner_probs.csv`, `coalition_*.csv`, `regime_*_seat_draws.csv`
     under `data/processed/<city>/<year>/` (not the 2026 forecast's files);
   - plausibility and arm outputs, wherever `src/plausibility.py` and
     `src/arms.py` wrote them (find their `--out` dirs from `prereg/` and
     `rounds/`);
   - score tables in `reports/model-changes/`: move the generated score files;
     leave committed text to item 6.
   **Do not move `data/processed/width_record.json`** (the live forecast reads
   it). Report anything you found that you were unsure about rather than moving it.
5. **The test** (new module, collected by `tests/run_all.py`, `CLAUDE.md` §4's
   four parts): (a) no file under `src/`, `tests/`, `content/`, `docs-public/`
   or `site/` names a quarantined path or reads one; (b) no token in
   `stats.toml` has a `validation:` or `history:` source unless it carries
   `label = "in-sample"` or `label = "forward-chained"`, and every page that
   prints such a token prints the label beside it; (c) a planted unlabelled
   score token and a planted read of a quarantined path each fail, and the test
   is quiet when they are reverted; (d) the population scanned is stated and
   bounded. It must not forbid `compare_history` writing a new `history.json`.
6. **Committed text.** Count the files that quote in-sample figures (grep for
   digits beside "coherent", "city-years", "beats uniform swing", "CRPS",
   "seat error", in `*.md` outside `site/`; report the count and the command).
   Add one banner at the top of `MODEL-LOG.md`, `JUDGEMENT-CALLS.md` and
   `rounds/2026-10-23-out-of-sample/POLLSTER-ON-RECORD.md` (MODEL-LOG: as a new
   appended entry and a one-line pointer at the top): every backtest figure
   dated before 2026-10-23 is in-sample and is not evidence of forecast
   accuracy. Do not edit earlier entries.
7. **The forecast page's widths.** Where the forecast or methodology says how
   wide the ranges are or where they come from, add one sentence: the ranges are
   fitted on errors from past tests whose settings had seen those elections, so
   they are likely too narrow. Plain words, "This Model".

## Limits

- Branch `site-sweep-1`. Commit there; no push, no `--publish`, no deploy.
- You may write `content/`, `docs-public/`, `src/`, `tests/`, `site/` (via
  `src/build_site.py --as-published`), the ledger only through
  `publication.retire`, and move files as in item 4. Nothing else under `data/`.
- `nice -n 15` on anything heavy; targeted modules only
  (`tests/run_all.py -k <module> -j 1`), plus `published_page`, `tooltip_says`,
  `prediction_rule`, `model_index` (regenerate `MODEL-INDEX.md` with
  `src/model_index.py` if it changes), `publication_ledger`. No whole suite.
- Do not sub-delegate.
- Report: the tokens retired (list), pages changed, files moved (list with the
  README path), the test's module name and its counts, the committed-text count
  and command, each command run with its counts, and the commit id(s).
