# Slice A diff review packet

Issued to one fresh reviewer, 2026-10-08. Blind: you get the specification and
the diff, not the writer's account of it.

## Ground rules
- Read-only. Edit nothing. Run nothing that writes `data/`, `site/`, `content/`,
  `publications/`. You may import modules and run pure tests that write nothing
  (`tests/test_prediction_rule.py`). Use `.venv/bin/python`. Do not sub-delegate.
- Read: `CLAUDE.md`, `QC.md` §4b, `audits/2026-10-07-prediction-restructure/`
  `BRIEF.md`, `s1/SPEC-A.md`, `s1/SYNTHESIS.md` (its resolutions and the owner's
  answers override SPEC-A), `review/S0-SYNTHESIS.md` (guards G1–G6).
- The diff: the path given to you. It excludes six unrelated uncommitted files.

## Questions
1. **Spec coverage.** Every item in SPEC-A §1–§3 as amended: done, done
   differently (is the difference sound?), or missing.
2. **`src/montecarlo.py`.** Can any change move a draw: a random call, an
   ordering, a dtype, anything read before it was written? This decides whether
   an early whole-suite run is needed.
3. **Correctness of `src/prediction.py`:** tie rule, exact integer mean and its
   rounding, weights, refusals; `seats_of` against `run_model`'s composition
   (pool order, `COUNCIL` restore, overhang rule); `reader_seats` delegation and
   its precedence change.
4. **One definition.** Any second computation of a modal ward, a mean vote, a
   list share, or a seat-law composition left or added anywhere.
5. **The guards.** For each of G1–G6: does it state its population and check it
   both ways where needed, does its constructed violation get caught and go
   quiet when reverted, is its input constructed rather than observed (CLAUDE.md
   §4)? Can any of them pass while blind?
6. **Records.** MACHINERY, JUDGEMENT-CALLS, MODEL-LOG, docstrings: accurate
   against the code, no typed number outside where numbers are generated, every
   run-produced figure left as TO-MEASURE.
7. **The check step's test list.** Given the diff, which test modules can see
   the change? Is anything missing from this list:
   `prediction_rule chain stage_realisation draw_record export_draws reweight
   score_forecasts reader_seats regressions your_forecast_page worker_routing
   home_page published_page model_index judgement_sheet served_draws`, plus node
   `page.test.mjs make.test.mjs yf.test.mjs builder.test.mjs play-share.test.mjs`
   and `worker-api/test/node/build.test.js`?

Return findings ranked by severity: blocking (must fix before checks), should
fix, note. For each, give the file:line and say verified or argued.
