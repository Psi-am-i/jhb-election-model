# Slice M4 writer brief (2026-10-10)

One writer. Branch `remediation`, starting at `8c74fe4`. M1, M2 and M3 are
committed and reviewed, M3's fix round included (`reviews/M1-SUMMARY.md`,
`reviews/M2-SUMMARY.md`, `reviews/M3-SUMMARY.md`, SPEC R3.6 addenda).

## Read first
- `CLAUDE.md`, `QC.md`.
- `audits/2026-10-09-model-fixes/BRIEF.md`, including every owner decision.
  Item 19 is "Owner's decisions on the specification", decision 19.
- `spec/SPEC.md`:
  - R2.4 (item 19) in full: the population, the baseline `B`, the test, the
    rule, the code changes, G23-G26;
  - R2.5's P19 block, R2.6 (step 7), R2.7;
  - §4, §5;
  - Revision 3 through the last R3.6 addendum (the known-red list).
- `src/byelections.py`, `montecarlo.blended_centres`, `export_draws.py`
  around the by-election report (`reaches_model`), JUDGEMENT-CALLS §A35.

## Scope: writing-order step 7 (R2.6)
In order, one commit each:
1. **Item 19's pre-registered section first** (R2.6): P19's test prediction,
   committed before `bye_value.py` computes anything on real data. Copy P19
   from R2.5; amend only where M3 changed a premise (items 16 and 17 now move
   `mu_θ`), and say so in a dated note, never by editing R2.5.
2. **`src/bye_value.py`**: the test exactly as R2.4 steps 1-6, the artefact
   `data/processed/bye_value.json` with its `artefact_key`, `declares.py`,
   `tests/test_intermediates_are_current.py`, `ENTRY_POINTS`, and a pointer
   line in CLAUDE.md §5's standalone block (a pointer, no numbers). G23, G25.
   Build its output into a temp directory to test it. Writing the real
   `data/processed/bye_value.json` belongs to the window (step 10). Do not
   write it now.
3. **The model wiring**: `blended_centres` takes the class weight, `w_bye`
   becomes a sweep-only override defaulting to `None`, a missing or stale
   `bye_value.json` refuses, `export_draws` reports the class weight. The
   JUDGEMENT-CALLS entry superseding §A35 states every typed part concretely
   (the two classes and their 1% edge, leave-one-metro-out, the
   5th-percentile rule, the 10-pair floor). G24, G26.

The wiring makes every target that reads by-elections refuse until the window
writes `bye_value.json`. That red is by design: list each test it turns red
in a dated SPEC R3.6 addendum.

**Not in M4:** item 10's stale-spec refusal (step 8), the pre-registration of
the arms (step 9), the window, the measurement and the suite.

## Rules
- **Do not sub-delegate.** `.venv/bin/python` only.
- **Run nothing that writes** to `data/`, `site/`, `content/` or
  `publications/`:
  - no `pools.py --emit`, no `compare_history`, no bare `montecarlo.py`,
    no `bye_value.py` writing to `data/processed`;
  - in-process `run_model`, writing to temp, is allowed.
- **No re-emit.** Every new red goes on SPEC R3.6 as a dated addendum, never
  edited text.
- **One definition.** `B` uses the model's own `_shrunk` on `theta_record`
  (items 11, 16, 17 applied), imported, never re-implemented. `δ_pr` comes from
  `byelections.py` and the conversion `blended_centres` already does, imported.
  The 1% class edge is one named constant used by both `bye_value.py` and
  `blended_centres`.
- **No look-ahead.** The test reads no by-election on or after 2024-05-29 and
  no result at or after 2024 for `B` (G25).
- **Every party, the same rule.** No party is named in code or treated apart.
- **The cross-ballot caveat** (by-elections are ward contests, the outcome is
  the 2024 national-provincial ballot) is stated wherever the test's result is
  quoted: the JUDGEMENT-CALLS entry, the docstring, the artefact.
- **Guards** G23-G26 meet CLAUDE.md §4's four-part rule where they are
  scan-shaped. Each mutation is caught, and the guard goes quiet when it is
  reverted.
- **Docs in the same commit** as the mechanism: docstring, MACHINERY.md,
  JUDGEMENT-CALLS.md.
- Run `-k levers_are_live` once, after the last commit. `w_bye` changes from a
  lever to an override.
- If credit or time runs short, stop after a commit. Never leave a half-made
  step committed.

## Commits
Each commit ends with the targeted modules its items reach (§4 and R2.7:
`-k bye_value -k temporal -k blended_centres -k export_draws`, plus whatever
else it reaches), run after the last edit and quoted in the body:
- pass and fail counts per module;
- every failure assigned to R3.2, R3.5 or R3.6, or fixed.

End each message with:

    Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

## Return
- The commit hashes.
- Per commit: what changed, and the test table.
- Every deviation from the spec, and why.
- What the spec got wrong: measured or argued, labelled.
- Anything the pre-registration (step 9) must now predict differently.
