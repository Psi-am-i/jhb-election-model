# Reader badges: owner's decision (2026-10-10)

**Decision (owner, 2026-10-10):** the reader's badge is judged by the
forecast's **boldest single call**, and uses the five badges in
`audits/2026-10-07-stamp-design/owner-stamps/2026-10-10/svg/reader-*.svg`
with the edges printed on them. "Our score is a little informational but
mainly just fun. All forecasts get judged against the real result."

## Why the present badge is replaced
`reweight.council_outcome` (§N3) scores only the largest party, a majority
alone, and the coalition. On the published draws (model `7ea27c28…`, 5,000
simulations, law `deduct`) "ANC largest, no majority" holds in 46.7% and "DA
largest, no majority" in 45.2%, so nearly every forecast scores about 46%,
and the model's own middle forecast (ANC and DA tied at 66) scores 1.4%,
because a tie for largest occurs in 1.4% of simulations.

## The measure
For each party whose seats in the reader's forecast differ from the model's
middle forecast (`reweight.middle_seats`), the share of simulations at least
that far out on the reader's side: `P(seats ≥ x)` above the middle,
`P(seats ≤ x)` below it. The badge comes from the smallest of these; the card
names that party and its seats ("Your boldest call: PA at 38 seats").

| badge | chance of the boldest call |
|---|---|
| Safe bet | 45% or more |
| Steady as she goes | 30% to under 45% |
| Long shot | 15% to under 30% |
| Wild call | 5% to under 15% |
| Hail Mary | under 5% |

An edge takes the higher band. A forecast equal to the middle forecast is a
Safe bet.

## Measured on the published draws (constructed forecasts, not readers')

| forecast, moved from the model's middle | boldest call | chance |
|---|---|---|
| ANC +3, DA −3 | DA 63 (middle 66) | 43.2% |
| ANC +10, DA −10 | DA 56 | 23.6% |
| EFF +10, ANC −10 | EFF 35 (middle 25) | 26.4% |
| DA +15, ANC −15 | DA 81 | 14.3% |
| PA +8, DA −8 | PA 31 (middle 23) | 12.8% |
| PA +15, DA −15 | PA 38 | 4.1% |
| ANC +25, DA −25 | DA 41 | 2.5% |
| DA 106 | DA 106 | 0.9% |

**Known limit, accepted:** a forecast that moves every party a little takes
its badge from some small party's tail; each simulation taken as a forecast
scores a median of 1.0% this way. The owner judged this not worth a further
rule.

## To do, with the share-image slice (after the batch)
- `reweight.BOLDNESS` → the five bands; `boldness`/`outcome_chance` → the
  boldest-call measure; the card and the arrival view print the party and seats.
- JUDGEMENT-CALLS: a new entry superseding §N6 (the edges above, concretely)
  and amending §N3 (the badge no longer reads `council_outcome`; the
  "this outcome" chance line in "Analyse my forecast" is unchanged unless the
  owner says otherwise).
- `tests/test_reweight.py` holds the four edges.

## Note, 2026-10-12: the reference is the published prediction
The card brief (`CARD-COHERENCE-BRIEF.md`, JUDGEMENT-CALLS §N10 amended)
measures a call from the published prediction (`forecast.json` `start.seats`),
not from `reweight.middle_seats`; the two are different sets of seats (ANC 66
against 70, DA 66 against 65). A party at one seat or fewer in both the
reader's forecast and the prediction is skipped. The eight constructed
forecasts above, re-measured on the same published draws (model `7ea27c28`)
from the prediction (the owner's decision above is unchanged; this table
replaces its figures, which `tests/test_reweight.py` `BADGE_TABLE` now holds):

| forecast, moved from the published prediction | boldest call | chance |
|---|---|---|
| ANC +3, DA −3 | ANC 73 (prediction 70) | 36.2% |
| ANC +10, DA −10 | ANC 80 | 21.0% |
| EFF +10, ANC −10 | EFF 36 (prediction 26) | 24.9% |
| DA +15, ANC −15 | DA 80 (prediction 65) | 15.7% |
| PA +8, DA −8 | PA 32 (prediction 24) | 10.5% |
| PA +15, DA −15 | PA 39 | 3.6% |
| ANC +25, DA −25 | DA 40 | 2.2% |
| DA 106 | DA 106 | 0.9% |

Amended 2026-10-12 (owner: ignore anything under a 10 seat move): a party
counts only if the reader's seats differ from the prediction's by
`reweight.MIN_CALL_SEATS` (10) or more. Of the eight forecasts above, "ANC +3,
DA −3" and "PA +8, DA −8" move no party by 10, so they have no call and are a
Safe bet; the other six are unchanged (`tests/test_reweight.py` `BADGE_TABLE`).
