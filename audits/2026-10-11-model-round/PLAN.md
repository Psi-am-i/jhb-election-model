# Model round of 2026-10-11: plan and owner decisions

Follows MODEL-LOG §1.296. Process: CLAUDE.md §4 and QC.md.

## Owner decisions, 2026-10-11
1. Draws are paired across arms by giving each party its own seeded draw stream
   (common random numbers), checked to leave every party's distribution unchanged.
2. Item 8 (parties on the certified roster with a 2021 record enter the run) is
   REVISED, not shipped as is and not dropped. Owner: tiny parties are better
   modelled as a class whose combined performance is more predictable. Open: where
   the line is drawn. It must come from the record, and any value the record does
   not force is a judgement call shown to the owner before code.
3. Item 6 (ward/list ratio) ships.
4. One ultra review, owner-triggered, on the code diff of step 5 before the
   canonical run (step 7). Its brief is written in step 4, before the code.
5. Publishing the changed forecast: owner sees before/after first.

## Steps
1a seat-error source and extreme-draw audit (existing arrays) · 1b small-party
range + tiny-party class + new-entrant sizing, one design · 1c paired draw
streams · 1d census-date investigation · 1e merge site-release into remediation,
state-independent cleanup · 2 re-derive + blind challenge of 1b, 1c · 3 owner
checkpoint on judgement calls · 4 pre-registration + ultra brief · 5 one writer,
serial · 6 diff review, ultra review · 7 re-emit once, canonical paired runs ·
8 two independent scorings, MODEL-LOG · 9 goldens, freeze, index, suite, draws
export · 10 site UAT, promote, then redeploy joburg-seats.

## Owner decisions at the step-3 checkpoint, 2026-10-11
- The small-party line is a flat 1% of the list vote (owner: "a nice number"), in
  place of the designed three seats' quotas. Judgement call, registered as such.
  Membership otherwise as design v3 (stood at the previous election in this city;
  both that result and the current centre below the line).
- Parties above the line keep the within-pool split this round; their spikes are
  next round's work.
- The `compress_levels` small-party lift: designed and reviewed now; included in
  this round only if it passes review before the canonical run.
- 2026-10-12: owner moved the small-party line to 5% after the randomness audit
  (1-5% parties behave like sub-1% in the record), and asked for a literature
  review before more fixes: if the draw is wrong across the spectrum, a fix at one
  end is a bandage. Turnout's two unconnected calculations: measured in this
  round's plausibility check, fixed next round.
- 2026-10-12, after the literature review (step1/1i): owner approved one
  log-scale draw for every party in place of the 5% line (MODEL-LOG §1.297).
  Pooling sub-1% parties into a class may follow once the universal draw is
  measured. Paired draws and the census registration change proceed unchanged.
- 2026-10-12, owner on new parties and collapses: parties with no record, and
  collapses like COPE's, rest on judgement calls about strength that the record
  cannot supply. Requirement for the design: one consistent way to enter such a
  judgement (centre and width) that applies to any party the same way, declared
  in JUDGEMENT-CALLS.md, not per-party special cases.
- 2026-10-12, owner: (1) census — a group the wards cannot identify is capped:
  the hold (reach < 25% of every ward → the city's registration rate), applied
  to every group by one rule; Cape Town Indian/Asian goes to about 2.7% of the
  roll. (2) Middle-width A/B and outlier removal withdrawn: "we were trying to
  look at the whole vote not just certain segments". Design v4: one smooth
  width curve over all sizes fitted to every party-election, newness as one
  term in it, judged on whole-election measures; judgement entry an optional
  overlay only.
- 2026-10-12, owner checkpoint: adopt design v4 with option L1 (step1/1j-universal-
  draw-design-v4.md + v4-addendum), plus a paired arm that corrects small parties'
  centres by the size bias the joint fit measures from earlier elections
  (estimation, out of sample). Census: the identification hold (cap). Next: step 4
  (pre-registration and the ultra-review brief, both before code), then step 5.

## Open notes: check before the canonical run (2026-10-13)

The owner asked that every open note be kept here so nothing is tested without
it. Work through this list before step 7's canonical runs and record each
outcome. Close an item by stating what was done; never by deleting it.

Before the re-emit:
1. Fixes from the local two-reviewer review of the frozen brief. The ultra
   review on PR #18 failed with no findings. The fix writer is applying them;
   its MODEL-LOG § lists them. They cover the scored population (2011 and 2026
   out), arm pairing, the width-record key, the judgement file location,
   declares, the instruments for every registered quantity, and the C0 recipe.
2. JUDGEMENT-CALLS §L2 against line ~2481. A party carrying a run-time strength
   judgement currently stays inside the arrival budget at emit. The reviewers
   say §L2 puts it outside. Owner decision if the writer stops on it.
3. Owner's party sheet. The owner marks the parties he disagrees with; his
   calls go in as `support`/`overperform`/`sigma_j` in
   judgements/joburg-2026.toml, each with a §SJ row (reason, date, check).
   This must land before the canonical forecast run. The forecast is run and
   reported both with and without them.
4. Step-7 order: POOLS-REEMIT-QUEUE, "model round's step 7". backup_ignored and
   R1 on the current specs come first.

Measure in the canonical runs (pointers, no new definitions):
5. Ward-call calibration. The page says the model expects 108 of its own 135
   ward calls to come true. Compare its expected hits with realised hits in the
   2016 and 2021 backtests. If realised is clearly higher, ward chances are too
   cautious: a model finding, not a page fix.
6. 2011 fallback width: computed 0.235/0.464 against the design's 0.27/0.48.
   The statistic is unnamed in design 1b v3. 2011 is unscored, but say which
   statistic is right.

Known, deliberately not fixed this round:
7. `poll_model_sd` reads the universal width at the whole-city share. Inert
   while polls are off; revisit before polls return.
8. VD-turnout noise adds list-share spread that is not in the subtracted
   composition variance (reviewer B, design question).
9. Backtests ignore strength judgements by design: a judgement written today
   would carry hindsight into a past election. The past judgement files hold
   only blank lineage entries (default treatment). So no judgement call is
   tested against results until 2026 is held, and the forecast states the
   difference its calls make.
10. Next round: sub-1% class; small-party centre correction (m(s)) if UC does
    not ship; turnout unification; census 2011 date filter; test_pool_bounds
    (2011 DA/White); new-party centre sizing.

Site (separate repo, separate release):
11. Closeness badge (CLOSENESS-BADGE-BRIEF.md) in build; the owner is drawing
    new number-free badges. The live card server and live site promotion are
    the owner's, after he sees the test site.
12. Splinter voter mix (owner question, 2026-10-13). `SPLINTER_PARENT_WEIGHT` 0.35 (JUDGEMENT-CALLS §F6, 🔴) is the median of 22 past splinter cases, which range from EFF 0.89 through GOOD 0.28 to ActionSA about 0.02, so one median serves a very wide range. Proposed general rule, for every party and not MK alone: where a party stood in the preceding national election, fit its voter mix from that election's ward results in the city, and use the splinter weight only for parties with no such result. Owner decision; design and measure before adopting.

Closed 2026-10-13:
- Item 1: the review fixes landed (46606f8..8e33386, MODEL-LOG §1.300, prereg
  amendment 3). Whole suite 1221 passed / 139 failed / 19 skipped; the failing
  set matches the baseline by name (stale specs and no width record, cleared by
  step 7).
- Item 2: §L2 restored, not changed. A party with a run-time strength
  judgement sits outside the arrival budget. The emit reads only which parties
  are judged, never the values (bd22d47, queue 37). Number-neutral today.
  Reported to the owner.
- Item 3 (owner's party calls) does not block step 7. Backtests ignore
  judgements, and no strength entry exists yet. When the owner's calls land,
  the 2026 forecast is re-run with and without them; that run alone, not the
  arms.

## Owner decisions after step 8, 2026-10-14
1. The census hold is left out of this round (K1 falsified, MODEL-LOG §1.301).
   Its held pool's rate is read from every pool's census level; fix next round.
2. The universal draw (arm U) ships, M5 and the R2 Monte Carlo clause recorded
   as falsified, not blocking.
3. `SPLINTER_PARENT_WEIGHT` stays 0.35 as the default; whether it is adjusted
   for a party is a judgement call made case by case on the owner's party
   sheet, entered the same way for any party (one mechanism, §SJ row each).
4. First such call: MK, owner's note "it is more like 90% ANC resemblance".
5. Step 9 proceeds; the owner sees before/after against real results.
