# Slice B diff review packet

Issued to one fresh reviewer, 2026-10-08. Blind: you get the specification and
the diff, not the writer's account of it.

## Ground rules
- Read-only. Edit nothing. Run nothing that writes `data/`, `site/`, `content/`,
  `publications/`, and nothing against a remote (no wrangler, no D1). You may
  import modules and run pure tests that write nothing. Use `.venv/bin/python`.
  Do not sub-delegate.
- Read: `CLAUDE.md`, `QC.md` §4b, `audits/2026-10-07-prediction-restructure/`
  `BRIEF.md`, `s1/SPEC-B.md`, `s1/SPEC-A.md` §5 and `MODEL-LOG.md` §1.291 (what
  slice A landed, commit 2bc6740), `s1/SYNTHESIS.md` (its resolutions and the
  owner's answers override SPEC-B: no OTHER party; no export, a clear step only;
  bounds = panel extremes widened 5pp, runner-up capped at 50%), and
  `review/S0-SYNTHESIS.md` (guards G7, G8, G12–G15).
- The diff: the path given to you. It excludes six unrelated uncommitted files.

## Questions
1. **Spec coverage.** Every item in SPEC-B as amended: done, done differently
   (sound?), or missing.
2. **The entry format.** Encoding v2 round-trips exactly; nothing silently
   fills a missing ballot, party or ward (no fallback to the published start,
   no zero, no even spread); old-version links get the version note; the
   validator, the seat Worker, the stored schema and the scorer all read the
   same shape.
3. **The seat law.** `reader_seats`' two-ballot signature: one composition
   (through `prediction.seats_of`), refusals R1/R2 exactly, no second
   definition anywhere (Python, the seat Worker copy, JS).
4. **The bounded editor.** Bounds derived from the data (not typed), widened and
   capped as the owner decided, limiting the editor only and never validity;
   their guard regenerates from a mutated copy and sees each mutation.
5. **One definition / no typed numbers / no inline CSS or JS**, and STYLE.md
   rule 11 in any reader-facing word changed.
6. **The guards** G7 (encoding side), G8, G12, G13, G14, G15 and the bounds
   guard: population stated and checked both ways where needed, constructed
   violation caught and quiet when reverted, input constructed not observed.
   Can any pass while blind? G8 is held by source text: is that adequate?
7. **Records** accurate against the code; figures only where generated;
   TO-MEASURE for run-produced values.
8. **The check-step list** the writer proposes (below): anything missing?
   Regenerations: sync_seats_py, sync_py, site build, native_play --write,
   share_fixture --write. run_all -k: reader_seats score_forecasts rank_entries
   entries your_forecast_page worker_routing share served_draws export_draws
   overhang seats site_structure number_scan site_assets prediction_rule
   register_matches_code regressions model_index judgement_sheet
   inputs_preflight standalone_modules. Node: builder make yf share page
   play-share play-state api. Vitest: the whole workers project and node/build,
   node/consent-screen. Checks: sync --check ×2, make_schema --check,
   yf_jump_check, screenshots.
9. **Release safety.** Migration 0002, the deploy order (migration → seat Worker
   → site Worker), the clear step: can any order leave a live site that accepts
   or stores an entry nothing can score?

Return findings ranked: blocking, should fix, note. File:line, verified or
argued, for each.
