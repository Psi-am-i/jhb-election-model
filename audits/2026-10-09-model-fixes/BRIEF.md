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

## Owner's decisions, 2026-10-09 (later), added to the batch

The owner, verbatim: "2. growth changes by size for sure and you seem to have
modelled that. so yes, lets do that for everyone and see what happens. 3.
tripwire just tells us but doesnt stop it? if so yes. 4. it's a strange case.
it's usually in the alliance so strange it is running alone, but only in some
wards I think. Narrow it and treat like everyone else until we have a mechanism
to change that has some basis. 5. no. certainly not."

11. **Growth measured at current size, for every party** (item 7, candidate b2).
    `_shrunk` evaluates the size centre at the party's current base, not at the
    mean base of its own historical observations. It applies to all parties and
    singles none out. The effect on every party is pre-registered and measured
    ("see what happens").
12. **The group-share tripwire** (item 7, Q4). It counts and reports each
    party's realised share of each pool's vote above its record plus the
    largest real one-cycle rise. It changes no number. It is recorded in the
    run's guards, and the build prints it.
13. **The SACP treated like everyone else.** Its special owner-declared sizing
    (JUDGEMENT-CALLS §L13) is retired. It is sized and varied by the same rules
    as other parties of its kind, until a mechanism with a basis exists for
    parties that usually stand in an alliance (the SACP stands alone in some
    wards only; that is noted, not modelled).
14. **By-election evidence needs a minimum before it moves a small party.** Two
    contests and 198 votes lifting the All Citizens Party from 0.04% to 1.07%
    is rejected. The minimum is derived from data: how well by-election swings
    of a given size and count predicted the next real result. The rule applies
    to every party.
15. **Long editor notes are shortened** where they stay understandable;
    otherwise the note area grows. This is cosmetic and lands with the next
    editor change.

## Owner's decisions on the specification (2026-10-09)

The owner, verbatim: "PA fix agree - no growth record we should have size ranges
and maintain averages for each. SACP normal. Is it treated as a split or new
entrant? Part of me thinks it should be a split but it's really just an
alliance partner. Really not sure. But leave it as a normal new party. 3. ok 4.
agree. 5. by elections we need to use history as the judge of whether they
predicted anything not already predicted by model... lets see. decisions 1.
yes. 2. ok. 3. yes. 4. yes"

16. **A party's own growth record counts only from elections where it stood at a
    size similar to now** (new arm, all parties). The similarity window is
    derived from data, not typed. Where a party's own similar-size record is
    empty, the size-group centre applies (item 11). This addresses the PA's
    emergence-era multipliers without singling it out.
17. **Parties with no own record** (item 11b, its own arm) take the average and
    the range of their size group, at their current size.
18. **The SACP is a normal new party** (item 13 as specified). Its alliance
    status is noted, not modelled.
19. **Item 14 redefined: by-elections are judged by history.**
    - By-election evidence gets weight only to the extent that, historically,
      it predicted the next real result beyond what the model predicted
      without it. That is incremental, out-of-sample value against the model's
      own baseline.
    - If it adds nothing measurable, its weight is zero.
    - It applies to every party. Pre-registered; the thin data (from 2022, and
      the 2024 national election as the only later result) is stated.
- **O4** unopposed: OK.
- **O6** the re-emit for this batch only: yes.
- **Writing is approved.**
