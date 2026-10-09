# Slice M3 writer brief (2026-10-09)

One writer. Branch `remediation`, starting at `65fe31a`. M1 and M2 are
committed and reviewed (`reviews/M1-SUMMARY.md`, `reviews/M2-SUMMARY.md`).

## Read first
- `CLAUDE.md`, `QC.md`.
- `audits/2026-10-09-model-fixes/BRIEF.md`, including every owner decision.
  Items 11, 12 and 13 come from "Owner's decisions (later)". Items 16, 17 and
  18 come from "Owner's decisions on the specification".
- `spec/SPEC.md`:
  - §0 (O1, O2, O8);
  - §1.10 (item 11), §1.11 (item 12), §1.12 (item 13);
  - §1.9a (`group_share_tripwire`);
  - the §2 rows for items 11, 12 and 13;
  - §3 G13, G14, G15;
  - §4, §5;
  - Revision 2: R2.1 (item 16), R2.2 (item 17), R2.3 (item 18), R2.6, R2.7;
  - Revision 3 through R3.7.
- `item7/FINDINGS.md` (the PA's centre and the capacity guard).
- The scratch probes cited by the spec (`item11_spine.py`, `item16_spine.py`)
  are under `/Users/simondavis/.claude/jobs/26965cd4/tmp/modelspec/`, if they
  still exist. Treat them as prototypes, not as truth: the M2 review found that
  one of that set (`universe_gap.py`) read Johannesburg's file for every city.

## Scope: writing-order step 6 as revised by R2.6
In order, one commit each:
1. **Item 11a**, growth at current size (G13).
2. **Item 16**, own record only from similar-size elections; the window `H16`
   is derived, not typed.
3. **Item 17**, no-record parties take their size group's average and range.
4. **Item 12**, the group-share tripwire, plus `group_share_record.py` (G14,
   G15). It reports and changes no number. `41_guards.group_share_tripwire`
   is a third change to the field pin. Add `group_share_record.py` to
   CLAUDE.md §5's standalone block and to `ENTRY_POINTS`: a pointer, no numbers.
5. **Item 13/18**, the SACP is a normal new party: §L13 retired, judgement
   file and register.

Also, first, as a small separate commit, the M2 review's S4 follow-up.
`run_model` records the set of parties whose drawn base was range-checked, or
the base itself, in `41_guards`. The S4 population test in
`test_stage_realisation` then reads it instead of recomputing "pre-seed
baseline plus seed" outside the run. This applies the owner's one-definition
rule.

**Not in M3:**
- item 19, the by-election value test (step 7, slice M4);
- item 10's stale-spec refusal (step 8);
- the pre-registration (step 9);
- the window, the measurement and the suite.

## Rules
- **Do not sub-delegate.** `.venv/bin/python` only.
- **Run nothing that writes** to `data/`, `site/`, `content/` or
  `publications/`:
  - no `pools.py --emit`, no `compare_history`, no bare `montecarlo.py`;
  - `group_share_record.py --emit` belongs to the window. Do not run it now.
    Build its output into a temp directory to test it.
  - In-process `run_model`, writing to temp, is allowed.
- **No re-emit.** Every new stale-spec red goes on SPEC R3.6 as a dated
  addendum, never edited text. Known red now: R3.2, R3.5, R3.6.
- **One definition.** `theta_prior` and `_shrunk`/`spine` must agree party for
  party (G13 widens the existing §A26 test to `current`). Item 17's size-group
  average and range have one definition, shared with whatever already computes
  a size centre.
- **The PA is not singled out.** Every change applies to all parties (owner).
  O1 states that the PA's centre may still exceed the Coloured pool after this
  batch. The tripwire is what reports that; do not "fix" it.
- **Derived, not typed.** `H16`, and any threshold in item 12 that is not
  already a registered judgement call, are derived from data, with the
  derivation in the commit and a JUDGEMENT-CALLS entry that states the value
  concretely. Never put a number into CLAUDE.md.
- **Guards** G13, G14 and G15 meet CLAUDE.md §4's four-part rule where they are
  scan-shaped. Each mutation is caught, and the guard goes quiet when it is
  reverted.
- **Docs in the same commit** as the mechanism: docstring, MACHINERY.md,
  JUDGEMENT-CALLS.md.
- Run `-k levers_are_live` once, after the last commit. Item 17 can make a
  lever live or inert. Item 16 adds a window, which is a lever.
- If credit or time runs short, stop after a commit. Never leave a half-made
  step committed.

## Commits
Each commit ends with the targeted modules its items reach (§4 and R2.7), run
after the last edit and quoted in the body:
- pass and fail counts per module;
- every failure assigned to R3.2, R3.5 or R3.6, or fixed.

End each message with:

    Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
    Claude-Session: https://claude.ai/code/session_017VSLE7jEWudaMbJDUcAPeR

## Return
- The commit hashes.
- Per commit: what changed, and the test table.
- Every deviation from the spec, and why.
- What the spec got wrong: measured or argued, labelled.
- Anything the pre-registration (step 9) must now predict differently.
