# Brief: model fix batch (seat law and tie rules), 2026-10-09

Model tier: the whole suite runs once, before promote. It follows the
prediction restructure's slices, or lands with B2a, whichever comes first. Each
item is pinned to the statute text saved in
`audits/2026-10-09-site-batch/law/sources/`.

## Items

1. **Ties are settled by lot, not by name** (owner, 2026-10-09: "item 8 is a coin
   flip, so flip a coin. alphabetically favours one name above others if it
   happens twice").
   - **The lot is seeded,** so a repeat gives the same answer. The seed is a hash
     of the run's identity plus the ward (for a ward call) or the seat round
     (for a seat). No party name enters it.
   - **Ward calls tied in the count of simulations.**
     - `prediction.top_party` / `ward_calls`: rule A's alphabetical rule,
       JUDGEMENT-CALLS §Q2, is replaced.
     - `montecarlo.main`'s `ward_winner_probs.csv` winner column: the unstable
       argsort, S1 item 8.
     - `scenarios`, `score` and `diagnose`: these already route through
       `top_party`.
     - This matches the statute for a ward tie (Sch 1 item 8(2), by lot).
   - **Seat remainders tied on both surplus and votes.** The statute settles an
     equal surplus by the higher vote (item 13(2)(b), 16(4)(c)) and says nothing
     beyond that. Lot is applied there, in place of input order. This decided
     Johannesburg 2016 in MODEL-LOG §1.291.
2. **Surpluses ranked as integers** (law summary D3). Rank by
   `votes − floor × quota`, not the float `votes/quota − floor`, so that an equal
   surplus falls to the higher vote as the statute says. Fix the comment that
   claims Schedule 1 breaks ties by lot.
3. **Unopposed wards counted twice** (D4; items 12(2), 13(1)(b), 16(5)), from the
   certified candidate lists where they exist. First check whether any 2026
   Johannesburg ward is unopposed.
4. **`test_overhang` pinned to Laingsburg 2021's real votes** (D10). The IEC
   report publishes them, and the coordinator verified that they reproduce the
   published council.
5. **Records.**
   - JUDGEMENT-CALLS §Q2 (ward ties by lot, item 8(2)) and row §M1 (surplus ties
     by the higher vote) are corrected.
   - D1 and D2 (the IEC's no-list term against the statute's text) are
     registered as a judgement call that follows the counting authority's
     published formula.

## Acceptance
- A constructed tied ward and a constructed tied seat each resolve by the seeded
  lot. The result is identical across the build, the page and the scorer, and
  changes when the seed changes.
- No party's name order affects any result: swapping two party codes in a
  constructed case gives the swapped answer.
- Rule A's 2026 prediction and the published draws are unchanged where no tie
  exists. The re-run says how many ties there were.
- The backtest's Johannesburg 2016 row is recomputed and recorded in MODEL-LOG.
