# How much of its first local result does a party keep at its second?

Written 2026-10-23, before the scoring below is run. Owner, item 28: "Commission
the measurement as a pre-registered round", with elections up to 2021 only
("yes until 2021 not beyond").

**Already known before this was written, and not predicted here.** The design
pass computed each party's first and second local-election list shares in the
eight metros. The table is in `rounds/2026-10-23-out-of-sample/retention/SPEC.md`,
and I re-derived the Johannesburg figures from the raw files.
- **Collapse:** COPE 0.14–0.36, APC 0.31–0.65.
- **Growth:** EFF 0.90–2.98, Al Jama-ah 1.15–1.57, AIC (Buffalo City) 1.09.
- **UDM (2000 → 06):** 0.29–0.98. Only its Johannesburg row is in the live record.
- **Exits:** NFP and ID.

The model gives ActionSA the size line from all consecutive local-election
pairs, 0.720 at 18.1% (`levels.size_centre`). No second-election party in the
record is near ActionSA's size; the closest is EFF at about 11%.

So the descriptive record is not a result of this round. What is not yet known
is whether either rule predicts a second election out of sample.

## The test (no model run)

Two rules for a party at its second local election, each fitted only on pairs
whose later election comes before the target:
- **S, the size line.** As the model does now, `size_centre` refitted on the
  pairs available before the target.
- **P, second-election parties.** The median over parties of each party's median
  ratio across metros (clustered by party), using only first-to-second pairs.

The 2000 files the model quarantines (`HELD_BACK`) are excluded, as in the live
record. Exits are excluded, as in the live record.

| target | P is fitted on | scored on (party-metro pairs) |
|---|---|---|
| 2016 | UDM Johannesburg 2000 → 06; the 2006 first-time parties that stood again in 2011 | COPE, APC, Al Jama-ah (2011 → 16); AIC Buffalo City |
| 2021 | the above plus the 2011 → 16 pairs | EFF (2016 → 21, eight metros); AIC's 2016 → 21 metros |

**Score:** the mean absolute log error of the predicted ratio against the
realised ratio, per party (party-metros averaged within a party first), then
averaged over parties.

## Predictions

- **R1.** Neither rule's score is better than the other's by more than 0.2 in
  log units at either target. The record has two groups, one collapsing and
  one growing, and no rule fitted on earlier elections says which group the
  next party will join.
- **R2.** At 2021 both rules forecast EFF too low: the predicted ratio is below
  0.9 in at least six of its eight metros.
- **R3.** P fitted at 2021, for use at 2026, lies between 0.4 and 1.2.

## Limits stated here

- **The effective sample is the number of parties:** four scored at 2016 and two at 2021.
  This cannot establish a rule. It can say whether the evidence prefers one.
- **Survivors only:** parties that stopped standing are excluded, which biases both
  rules upward as a description of new parties.
- **ActionSA's own by-elections are not used here.** They are already in its centre at ½,
  and using them again would count them twice.

## What the owner receives

- The record (per party, both groups), R1–R3 scored, and the arithmetic of ActionSA's
  2026 centre for each candidate value. That arithmetic is the table in the
  specification: 0.44 gives 8.5%, 0.72 gives 12.6%, 1.00 gives 15.2%.
- The options:
  1. keep the size line;
  2. use P;
  3. keep the centre and widen ActionSA's range to cover both groups.

  The third would be a new judgement call.
