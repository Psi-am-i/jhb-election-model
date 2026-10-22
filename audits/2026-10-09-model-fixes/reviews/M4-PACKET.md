# Slice M4 diff review packet (item 19)

Issued to one fresh reviewer, 2026-10-10. The review is blind: you get the
specification and the diff `git diff d4036ae..121f9de`, not the writer's
account of it. Ignore `audits/2026-10-09-site-batch/` in that range: it is
unrelated share-image work.

## Ground rules
- **Read-only.** Edit nothing.
- **Run nothing that writes** to `data/`, `site/`, `content/` or
  `publications/`, and nothing remote:
  - not `bye_value.py --emit`; `bye_value.py --out <temp dir>` is allowed;
  - in-process imports and tests are allowed, writing to temp directories only.
- **Use scratch trees for before/after comparisons:** `git archive` of each
  commit, with a copy of `data/`. Run with `PYTHONHASHSEED=0` and a fixed seed.
- Use `.venv/bin/python`. Do not sub-delegate. Credit is limited, so be
  economical.
- **Read:**
  - `CLAUDE.md` (§1–§4, especially "level and shape" and the four-part
    absence rule) and `QC.md`;
  - `audits/2026-10-09-model-fixes/BRIEF.md`, owner decision 19;
  - `spec/SPEC.md`: R2.4, R2.5 (P19), R2.6, R2.7, Revision 3 and every R3.6
    addendum (the expected-red list is there);
  - `reviews/M4-WRITER-BRIEF.md`, the brief the writer worked to;
  - `prereg/2026-10-10-byelection-value-test.md`.

## Questions
1. **The population.** Re-derive the (party, metro) pairs yourself from
   `data/raw/byelections/byelections_SA_vd_party.csv` and the list-vote
   condition. Does the count match the artefact? Does any entry in the
   population fail to be a party in the sense the model forecasts, and if so,
   what does it do to each class's slope and gain?
2. **The baseline `B`.** Is it the model's own `_shrunk` on `theta_record` for
   a 2024 target, imported and not re-implemented? Does anything read a file at
   or after 2024, or a by-election on or after 2024-05-29?
3. **The test and the rule.** Re-derive both classes' weight, `G` and 5th
   percentile from a `--out` build. Is the leave-one-metro-out fit free of the
   held-out metro? Is the bootstrap clustered by metro? Is the rule the one
   R2.4 fixed?
4. **Pre-registration.** Was it committed before anything computed the test on
   real data? Does it leave a method choice open that the code then fixed?
   Score it against your re-derivation.
5. **Estimation or tuning** (CLAUDE.md §4): is the weight fitted to a property
   of the world or to a ratio defined on our own output?
6. **The wiring.** Does `blended_centres` take the class weight for every party
   by one rule? Is the class edge one named constant shared by the test and
   the model? Does anything still set `w_bye` to a number on a normal run
   (defaults, city configs, scenario files, the site build)? Does a missing or
   stale `bye_value.json` refuse?
7. **The test against the model's blend.** Does the quantity the test scores
   match what the model does with `w`? If not, state the difference and
   whether it changes the verdict.
8. **Extractions.** Helpers were moved into `byelections` and `levels`. Is each
   behaviour-preserving? Check one by before/after output.
9. **Guards.** For each of G23–G26 check the four-part rule. Name any that can
   pass while blind.
10. **Downstream.** What else reads `w_bye` (interactive build, `/play/`
    cells, export, backtest text, public methodology)? Which break or now
    describe something false?
11. **Expected red.** Is each failing test on the R3.6 list red for the cause
    given?

Return findings ranked blocking / should fix / note, each with file:line, and
mark each verified or argued.
