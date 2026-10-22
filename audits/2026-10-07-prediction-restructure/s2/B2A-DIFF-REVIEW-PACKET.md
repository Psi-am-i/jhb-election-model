# Slice B2a diff review packet

Issued to one fresh reviewer, 2026-10-09. Blind: you get the specification and
the diff, not the writer's account of it.

## Ground rules
- **Read-only.** Edit nothing.
- Run nothing that writes to `data/`, `site/`, `content/` or `publications/`,
  and nothing remote. You may import modules, call `build_make.editor_bounds`
  in-process, and run pure tests that write only to temp directories.
- Use `.venv/bin/python`. Do not sub-delegate.
- **Read:**
  - `CLAUDE.md`, `QC.md` §4b and `STYLE.md` (rules 1–11);
  - `audits/2026-10-07-prediction-restructure/s1b/PACKET.md`, including the
    owner's decisions and the coordinator's D1/D2 at its end;
  - `s1b/SPEC-B2.md` (what revision 2 leaves standing);
  - `s1b/SPEC-B2r2.md` §4, §5 and §7 (B2a; §6, B2b, is out of scope);
  - the reference probes in `s1b/probes/`.
- **The diff:** the path given to you.

## Questions
1. **Spec coverage.** For every B2a item in SPEC-B2r2: done, done differently
   (sound or not), or missing. Is any B2b element present, or any scipy
   dependency?
2. **One definition.** Is any rule computed in two places? That covers the
   ward-part join, turnout, swing extremes, record events, the shape bounds,
   the closed-form ward range (Python probe against JS), and the bounds read in
   the page and in the build. Each case must name its single owner.
3. **Generated, not typed.** Every value that becomes a bound must come from the
   data; only the registered thresholds (§R7, §R13, §R14) may be typed. Do the
   records point at `x-editor-bounds` rather than copy figures from it?
4. **Correctness.** Re-derive, in-process, at least:
   - A_ward and A_city with their event counts;
   - `q_win`;
   - the gap bounds;
   - three parties' citywide limits;
   - that rule A's start is inside;
   - that a slider move to ANC 8.4% clamps where the spec says.

   Compare against the spec's figures and say where they differ.
5. **The guards.** For each new guard: is its population stated and checked in
   both directions, is a constructed violation caught and quiet when reverted,
   and is its input constructed rather than observed (CLAUDE.md §4)? Can any
   pass while blind?
6. **Reader-facing words.** Do the editor's notes and the `#note-vote` text
   follow STYLE.md, with no typed figures?
7. **The check-step list** (below): is anything missing? Does any FLOW.md
   whole-suite exception apply?
   - Sync, then `--check`.
   - A site build to `--out`.
   - `run_all -k`: `your_forecast_page`, `score_forecasts`, `rank_entries`,
     `entries`, `prediction_rule`, `site_assets`, `site_structure`,
     `number_scan`, `regressions`, `register_matches_code`, `worker_routing`.
   - Node, by file: `builder`, `make`, `yf`, `page`, `share`.
   - Vitest: `node/build`.
   - `yf_jump_check`, and screenshots.

Return findings ranked blocking / should fix / note, each with file:line, and
mark each verified or argued.
