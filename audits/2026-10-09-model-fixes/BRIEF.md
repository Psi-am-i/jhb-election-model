# Brief: model correction batch, 2026-10-09 (revised with the owner's decisions)

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


## Added from the model investigation and the integrity review (owner, 2026-10-09)

Sources: `audits/2026-10-09-model-questions/FINDINGS.md` and
`integrity/FINDINGS.md`.

6. **PA contestation, vote-weighted** (owner: "vote weighted").
   - In `montecarlo.py` (~4796-4802), `now/was` becomes the share of the party's
     previous list vote lying in the wards it contests, then and now, in place
     of the count of wards.
   - The duplicate `[0, 2.0]` clip literal goes; the registered
     `WARD_PR_RATIO_MIN/MAX` is used instead.
   - Pre-registered and tested in the investigation (`PREREG-ward-list-fix.md`):
     F1–F6 held, B2 partly falsified at four city-years. It is re-run on the
     final tree.
7. **The PA's centre against the Coloured pool, and the capacity guard that
   cannot fire** (owner: "investigate"). Investigation first, read-only:
   - why the PA's centre (7.57%) exceeds the whole Coloured pool (7.11%);
   - whether the PA's level, its pool vector or the pool's size is wrong,
     against real results;
   - a guard that can see a party taking more of a group than history
     allows, with a constructed violation.

   A fix is specified only after the owner sees the findings.
8. **Seven certified-roster parties missing from the run** (owner: "agree").
   Parties with a 2021 local record enter the run's party list. A guard checks
   the certified roster against the run's parties in both directions.
9. **The 46 parties with no level shock: evaluate, then decide** (owner: "46
   parties need to be evaluated. Who are they, how big are they and what
   variation is in the record for other parties, if noise adequately describes
   the variation then we go with Occam's razor and don't add another - but the
   variation should actually happen").
   - Who they are and how big.
   - The variation real parties of comparable size have shown between
     elections.
   - Whether the draws' existing variation (the within-pool split) matches that
     record.
   - If it does, no new source is added, and the false claim in the code (the
     "band" that nothing reads) is corrected so the stated mechanism is the one
     that runs.
   - If it does not, the owner decides.
10. **Smaller items** (owner: "agree"):
    - a stale or unreadable pool spec stops the run;
    - unregistered defaults are registered (γ = 1.0 for 56 parties, the
      city-mean turnout fallback);
    - the turnout bands' width is reviewed against the observed range;
    - preflight says "present" rather than "used" for the 2026 roll;
    - `levels._citywide` refuses a renamed column;
    - `bounds_checked` counts checks, not draws.

## Not in this batch (own briefs)
- Turnout by voter group reaching the ward layer (integrity F5).
- Using the 2026 roll.
- The within-pool split reformulation (owner's direction: history plus a record
  margin, size-aware), after items 7 and 9.

## Order
1. **Investigations, in parallel, read-only:** item 7, and item 9's evaluation.
2. **Specification** of items 1–6, 8 and 10, read-only.
3. **Owner review.**
4. **One writer.**
5. **Pre-registered panel measurement, then the whole suite once.**
