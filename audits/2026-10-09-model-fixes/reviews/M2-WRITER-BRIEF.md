# Slice M2 writer brief (2026-10-09)

One writer. Branch `remediation`, starting at `954086b` (M1). M1 is checked:
its targeted modules are green apart from the three expected-red tests
(`test_draw_record::test_the_published_seats_are_byte_equal_with_recording_on`,
`test_export_draws::test_every_published_seat_file_is_reproduced_byte_for_byte`,
`test_export_draws::test_a_changed_seat_or_ward_is_caught_and_the_check_then_goes_quiet`),
which fail because the published seat files are stale under the corrected law
(SPEC R3.2, R3.5).

## Read first
- `CLAUDE.md`, `QC.md`.
- `audits/2026-10-09-model-fixes/BRIEF.md`, including every owner decision.
- `spec/SPEC.md`: §0 (O3, O4, O5, O6), §1.3, §1.6, §1.7, §1.8, §1.9, §1.9a,
  the §2 rows for items 3, 6, 8, 9 and 10, the §3 guards G7, G8, G9, G11, G12,
  G17 and G18, §4, §5, §7, and Revisions 2 and 3.
- `item9/FINDINGS.md` Q5 (the 15 rows).

## Scope: writing-order steps 3, 4 and 5 (SPEC §7)
- **Step 3.** Item 3, guard G7. Item 10 **except** two parts:
  - the stale-spec refusal (G10) is step 8 and is **not** this slice;
  - the turnout-band review runs after the window, read-only, and is **not**
    this slice.
  This step covers G11, G12, G18 and the register entries.
- **Step 4.** Item 9, all 15 Q5 rows, plus the `test_chain` and
  `test_regressions` assertions in §1.8. Guard G17.
- **Step 5.** Item 8 (G8), then item 6 (G9).
- **Records:** the §2 rows for these items. The `41_guards` field-set pin
  (§1.9a) changes once, in this slice, for the fields this slice adds:
  `bounds_checked` per party, `draws`, `roster_unrepresented` and
  `level_sd_default_parties`. `group_share_tripwire` is item 12 (slice M3); do
  not add it here.

## Rules
- **Do not sub-delegate.** `.venv/bin/python` only.
- **Run nothing that writes** to `data/`, `site/`, `content/` or
  `publications/`:
  - no `pools.py --emit`, no `compare_history`, no bare `montecarlo.py`;
  - in-process `run_model`, in tests or probes, writing to temp only, is
    allowed.
  - Run `src/backup_ignored.py` once before you start.
- **No re-emit.** Item 9's `pools.py` rows and the `levels.py` changes move
  `pools_sha`/`deps_sha` on every spec. That is expected; the re-emit is the
  O6 window (step 10).
  - Find every test that reports a stale spec after your change: candidates are
    `test_intermediates_are_current`, `declares.py`, and any `artefact_key` or
    `stale_reason` check.
  - Add each to the expected-red list, as a dated note under SPEC Revision 3
    (append "R3.6"; do not edit earlier text), with the cause.
  - Never re-emit to make a test green.
- **One definition** (owner's rule). Item 6: grep for any other copy of the
  `[0, 2.0]` ratio clip or of the contestation fraction and route it through
  the one definition. Item 8: `local_record_only` is the one classifier.
- **No numbers typed into CLAUDE.md**, or into docs that point elsewhere
  (CLAUDE.md §0, §2). JUDGEMENT-CALLS entries state their values concretely.
- **Item 3's refusal message** cites Schedule 1 item 12(2) and the
  JUDGEMENT-CALLS entry. It does not cite a MODEL-LOG section number: the
  batch's MODEL-LOG entry is written at step 13.
- **Item 3's population:** O4 measured that no 2026 Johannesburg ward is
  unopposed, using `[roster.wards]` (declared slates). Say in the commit which
  source `unopposed_wards` reads at 2026.
- **Item 8:** state in the commit which file the "roster" is and whether it is
  IEC-certified (CLAUDE.md §4b: Johannesburg's was typed from newspapers). The
  guard is scan-shaped:
  - it checks both directions;
  - it states its population and asserts the scanned set equals it;
  - it catches a constructed violation and goes quiet on the revert;
  - its input is constructed.
- **Every guard** G7, G8, G9, G11, G12, G17 and G18 meets the four-part
  absence rule where it is scan-shaped (CLAUDE.md §4). For each, check that the
  detector goes quiet when the mutation is reverted.
- **Docs in the same commit** as the mechanism (CLAUDE.md §2): docstring and
  MACHINERY.md for a mechanism, JUDGEMENT-CALLS for an undriven number.

## Commits
One commit per step (3, 4, 5). Each commit ends with that step's targeted
modules (§4, the subset its items reach) run after the last edit, and their
result quoted in the commit body:
- pass counts per module;
- every failure, named and assigned to R3.2/R3.5/R3.6 or fixed;
- `*** PARTIAL RUN` is expected.

Run `-k levers_are_live` once, after step 4. End each message with:

    Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
    Claude-Session: https://claude.ai/code/session_017VSLE7jEWudaMbJDUcAPeR

## Return
- The three commit hashes.
- Per step: what changed, file by file, and the test result after the last edit.
- Every deviation from the spec, and why.
- Anything you found that the spec got wrong: measured or argued, labelled.
- The R3.6 expected-red list.
