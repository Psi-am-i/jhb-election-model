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
