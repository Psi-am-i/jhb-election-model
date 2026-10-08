# Slice B diff review: summary (2026-10-08)

Blind reviewer, packet `B-DIFF-REVIEW-PACKET.md`. **Nothing blocking.**

**Re-derived by the reviewer:**
- `forecast_data` builds; `out_of_bounds` is empty; `context_ref` is cf63e052f0a3.
- Bounds 0.1862 / 0.5 (capped) / −6.758..+11.157.
- MODEL-LOG §1.292's figures reproduce.
- A 6,000-state random walk produced 0 invalid states.
- `f` round-trips byte for byte.
- Migrations 0001 and 0002 apply in sqlite.

**Should fix, all sent to the writer:**
1. The release order is written in no single place. A wrong order can seal an entry that is never stored.
2. JUDGEMENT-CALLS §R1 gives the limit's direction the wrong way round.
3. "The next edit brings it inside" is false for the gap bound, and the bounds note is never cleared.
4. The bounds guard misses q_run, gap_min, the cap and the previous turnout, and its floors are one-sided.
5. G8 is held by source text only.
6. MACHINERY overstates that the four validity readers agree.

Notes: see the fix list sent 2026-10-08. Two points carry forward to slice C:
- G16 must compare decoded states, not `f` strings, because several links decode
  to one prediction.
- The card's "% of votes" header (BRIEF change 5) is unowned and moves to slice C.
