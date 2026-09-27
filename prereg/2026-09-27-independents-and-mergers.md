# Pre-registration — independents as a party, and mergers as the inverse of splits

Written 2026-09-27, before any measurement. Owner's decisions, his words quoted.
Nothing here is applied; this states what will be changed, what it is predicted
to do, and what would count as the change failing.

## Why a pre-registration

Both changes move a published forecast. `ITERATING.md` and the re-emit
discipline require the prediction to be on record before the run that tests it,
or a result is only ever read as confirmation.

---

## Change 1 — independents become their own party

**The defect.** `IND` is on the certified 2026 ballot and is on our roster. It
has **no pool membership** — the pools carry 81 members against a roster of 82,
and `IND` is the one missing, in 2021 as well as 2026. A party with no pool
membership cannot be drawn, so **independents cannot win a single ward or seat
in any of the 5,000 simulations**, and `site/forecast.html` states that "every
party on the IEC's certified ballot is named in the simulations".

**The size of the hole, measured:**

| | |
|---|---|
| Independents, Johannesburg 2021 | **11,904 votes, 0.645%, rank 10 of 57** |
| just above | Al Jama-ah 0.954% — **median 2 seats in our 2026 forecast** |
| just below | African Independent Congress 0.594% |
| by-election record | 2 contests, 8.39% mean share, **+6.5 points** |
| nationally, 2021 | **52 seats, 1.73%** (IEC results dashboard) |

So a class of candidate that outpolled 47 of the 57 parties on the 2021 ballot,
that is growing where it stands, and that took 52 council seats nationally, is
represented in this model by nothing at all.

**The change.** Owner: *"we dont know who IND's are so they should be treated as
their own party because that's all we have."* `IND` is given a pool composition
and becomes a member like any other, fitted from its own 2021 result.

⚠️ **What this does NOT claim.** Independents are not a party and do not behave
like one: they do not stand city-wide, their support is ward-local by
construction, and aggregating them hides that. Treating them as one party is the
best available representation of the evidence we have, not a belief about how
they behave. That sentence belongs on the methodology page if this ships.

**Pre-registered predictions.**

1. `IND` takes **at least one seat in more than 2% of draws** — the floor
   §5b item 1 sets for a party to be defensibly on the ballot. If it stays under
   that, the fit is wrong rather than independents being unrepresentable, and
   the reason has to be found before it ships.
2. The 81 existing members lose mass to make room. **No party's median moves by
   more than 2 seats**, because `IND` enters at well under 1% of the vote.
3. **Ward winners change in fewer than 5 of the 135 wards.** Independents win
   wards in South Africa, but rarely, and a bigger move than that means the
   composition has been given to the wrong pools.

**What would falsify the change rather than confirm it:** any party's median
moving by more than 2 seats, or the ward map moving in more than 5 wards. Either
means `IND`'s vector is taking mass from the wrong place.

---

## Change 2 — a merger transfers a baseline, as a split divides one

**The precedent, and it is already here.** `pools.py` treats a SPLIT as
structurally different from an entrant: a split takes *a fraction of its
parent's vote* and *inherits its parent's pool vector*, and the fraction is
**measured, not typed** — COPE took 0.140 of the ANC, the EFF 0.162, MK 0.246.
The declaration of who split from whom is a judgement carrying a person, a party
and a date; the size is evidence.

Owner: *"We should certainly allow parties that merge to combine their vote like
we do the opposite with splitters."*

**What is missing, measured on the current roster.** Two of the three largest
parties the roster drops merged into parties that ARE on the ballot, and their
vote is deleted rather than transferred:

| dropped | 2021 Joburg vote | merged into | on the 2026 ballot? |
|---|---|---|---|
| GOOD | 6,773 (0.367%) | RISE Mzansi — RISE is the ballot party in Gauteng, GOOD leads the Western Cape; their Joburg mayoral candidate runs under RISE | RISE ✓ |
| Forum 4 Service Delivery | 504 (0.027%) | ActionSA, January 2025; its leader is ActionSA's deputy president | ASA ✓ |

⛔ **And it lands where it is least affordable.** **RISE Mzansi did not contest
Johannesburg in 2021** — it was founded in 2023 — so it has no local baseline and
is sized as an ARRIVAL, which `/about` calls the model's weakest area and where
the 2021 record is ActionSA forecast at 34 against an actual 44. The closest
thing RISE has to a predecessor vote in this city is the 6,773 the roster
deletes. ActionSA's case is immaterial by comparison: 504 against its own
296,345.

**The change.** Owner: *"If something merges and one of the parties was on the
vote use that rather than assuming a new entrant."* A `Merger` is declared the
way a `Split` is — named parties, a date, a source — and the successor inherits
the predecessor's baseline and pool vector instead of being sized as an arrival.

**The retention factor, and why it is not 1.0.** Owner: *"I would not make it a
perfect combination — a merger will always lose some votes even if the net gain
is positive."* Correct, and it is the same asymmetry the split side already
respects: COPE did not take 100% of the ANC's vote either.

⛔ **The honest problem: we have no measured merger.** The split fractions are
measured off two national elections each. No merger in this city's record has a
before-and-after pair to measure, so a retention factor typed here would be a
judgement wearing the clothes of a measurement — the exact fault
`JUDGEMENT-CALLS.md` exists to catch.

So the rule is:

1. **Look for a measurable case first** across the eight-metro panel — a party
   that merged into another between two elections both of which we hold. If one
   exists, measure the retention the way `splinter_record` measures splits.
2. **If none exists, the factor is a declared judgement**, registered in
   `JUDGEMENT-CALLS.md` with a 🔴 and a stated range, not a bare number, and the
   sensitivity swept before it ships.

**Pre-registered prediction.** RISE's median moves **up by 0 to 2 seats** and no
other party's median moves by more than 1. If RISE moves by more than that, the
transfer is doing more than inheriting a 0.367% baseline and the mechanism is
wrong.

---

## Change 3 — the roster count stays where it is

Owner: *"leave party number as is until it is confirmed."*

82 stands. It is a newspaper count and the provenance is now recorded at the
flag, but it is not changed on the strength of other newspapers — press reports
of the same certification give CoJ 75 or 82, and the outlet reporting 82 also
gives Tshwane 81 and Ekurhuleni 78 where earlier reports of that certification
gave 70–72 and 67–69. Nothing moves until the IEC's own list is in hand.

⚠️ **Change 1 adds `IND` to the POOLS. It does not change the roster count** —
`IND` is already one of the 82. The two are independent and this one is not a
count change.
