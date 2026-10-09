# Slice B2 design packet: ward-by-ward editor bounds

Issued to one designer, 2026-10-09.

## Why

Slice B (commit 685716c) bounds each party's citywide ward vote by its own
painted wards alone: floor = q_win × the expected-vote share of its wards,
ceiling = that + q_run × the rest, q_win/q_run the panel extremes widened by
5pp (JUDGEMENT-CALLS §R). The screenshot `s2/screens-b/vote-375-edited.png`
shows the ANC held at 8.4% of the ward vote while painted to win 70 wards, with
the DA at 29.3%. Each party's bound ignores the others and ignores each ward's
own history.

The owner (verbatim): "1 ward by ward is certainly preferred. i have a belief
(and it is so far only that), that a model that adheres tro how reality works is
ultimately going to be more defensible and has the ability to be more accurate
than a heuristic that attempts to get the same answer using a shortcut)."
His earlier decision stands: "use real historical limits and allow 5% either
side".

## Ground rules

- **Read-only.** Edit nothing. Write nothing to `data/`, `site/`, `content/` or
  `publications/`. In-process probes may write to your scratch directory only.
  Use `.venv/bin/python`.
- **Do not sub-delegate.**
- Read first:
  - `CLAUDE.md`, including §4b on delimitation and `montecarlo.ward_parts`;
  - `QC.md` §4b;
  - `STYLE.md` rule 11;
  - this directory's `BRIEF.md`, `s1/SPEC-B.md`, `s1/SYNTHESIS.md`, and
    `s2/B-DIFF-REVIEW-SUMMARY.md`;
  - `MODEL-LOG.md` §1.292;
  - `JUDGEMENT-CALLS.md` §R;
  - the slice B code: `interactive/js/builder-state.js` (`wonE`, `wardBounds`,
    `gapOf`, `listBounds`) and `src/build_make.py`'s `editor_bounds` and
    `expected_ward_shares`.
- Mark every claim **verified** (file:line, or a probe you ran) or **argued**.

## The task: a specification, not edits

Design ward-by-ward bounds that follow how a ward is actually won:

1. **Per ward, per party, a plausible share range** for 2026. Build it from:
   - that ward's own past results, joined to the 2026 wards through
     `montecarlo.ward_parts` for split voting districts;
   - a swing allowance derived from real consecutive elections in the panel
     (how far a party's ward share has actually moved between elections, by
     party size or by starting share if that matters);
   - the owner's 5pp widening.

   Say how you handle a party with no history in a ward (new parties, MK,
   ActionSA in 2016 wards, independents) and a ward with no past result.
2. **The joint condition in each painted ward:** the painted winner's share must
   be at least each other party's share there. Turn this into what the editor
   enforces. Options include:
   - per-party citywide floors and ceilings recomputed from the ward ranges and
     the painted map;
   - a feasibility check of the whole state.

   Recommend one, and give its cost in the browser. It is recomputed on every
   paint stroke and slider move, at phone speed.
3. **What happens at the edges:**
   - a painted map that no vote vector can satisfy;
   - a state from a link or the hand-off that falls outside.

   Bounds still never decide validity (SPEC-B D4).
4. **Our own prediction (rule A):** does it sit inside the new bounds? Measure
   it. If it does not, that is a finding about rule A or about the bounds;
   say which.
5. **Evidence.** Backtest the bounds on the panel. For each past city-year,
   built only from the elections before it, report:
   - how many real ward results fall outside their range;
   - how many real citywide results fall outside the editor's limits given
     the real ward winners.

   Report these counts against the current slice B bounds as well.
6. **Records, guards and tests:**
   - JUDGEMENT-CALLS entries;
   - the guard that regenerates the bounds from a mutated copy of the data and
     sees each mutation (CLAUDE.md §4: constructed input, both directions,
     population stated);
   - the exact targeted test list;
   - whether any FLOW.md whole-suite exception applies.
7. **Files, functions and an estimate**, and what this replaces in slice B.

Return the specification as your final message, and save it as `SPEC-B2.md` in
your scratch directory.

## Owner's decisions on SPEC-B2 (2026-10-09, verbatim then interpreted)

> "1. widest allowed swings. Now that I think of it, this can be measured. when a
> party moved up or down more than it ever had previuously, what was the delta
> of that new swing? Leave out mergers splits and collapse (cope) then avereage
> it out and set the allowable swing (does taght work in yoru estimation?)
> 2. new parties... 2024 result plus usual party vote deterioration if one
> exists. 3. add scipy yes - but if this will take 5 days, keep the allowed
> swing to previous history while we work on it. 4. agreed, it is reasonable.
> but same as 3."

- **O1, the widening is measured, not a flat 5 points.** Each time a party's swing
  broke its own previous record (up or down), the amount by which the new
  record exceeded the old one is a record exceedance. Mergers, splits and
  collapses are excluded (COPE named). The mean exceedance replaces
  `EDITOR_WIDEN_PP`. The coordinator is asked whether this works; the designer
  measures it.
- **O2, parties new to local elections** take their 2024 national result as the
  prior, adjusted by the usual national-to-local change for parties where one
  can be measured.
- **O3, scipy is approved.** The witness editor is staged:
  - **B2a, fast:** history-based ward ranges, the per-party box, and the
    citywide swing limit, with no solver.
  - **B2b:** the witness editor, which needs scipy.
- **O4, the citywide swing limit is agreed.** It lands in B2a.
