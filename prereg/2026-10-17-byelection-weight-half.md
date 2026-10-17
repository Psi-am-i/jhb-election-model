# By-election weight 0.5 for every party (owner decision, 2026-10-17)

Written before the change is made or run.

## The change

Owner: "since we do not know what the by-election weight should be. Weight
them all at 50%. So if our forecast says 10% and by election result was 8%,
then use 9%."

`DEFAULTS["w_bye"]` goes from `None` (each party's weight read from its size
class in `bye_value.json`, currently 0.0 for both classes) to `0.5`, the same
for every party. In `montecarlo.blended_centres` each party with by-election
evidence then gets `centre = 0.5 × level + 0.5 × by-election level`, where the
by-election level is the previous local PR share plus the weighted ward delta
(`byelections.delta_pr`). Kept unchanged:

- the cap on the by-election level (`clamped`, θ's relative band around the
  model's level);
- the evidence floor `BYE_MIN_WEIGHT`;
- the level shrink and the normalisation after the blend, so "halfway" is
  halfway before those two steps, not in the drawn means.

## Predictions

P1. All 24 backtest city-years in `compare_history` are identical, row for row
(list error, ward error, seats, wards called). No backtested target has a
by-election before its polling day: the by-election file starts in 2022 and
the last backtest target is 2021.

P2. No pool spec changes: `pools.py` does not read `w_bye`, so every
`artefact_key` stays as it is.

P3. Johannesburg 2026 pre-shrink centres (measured in process before this was
written, `stop_after="drawer_inputs"`): DA, ActionSA, MK, PA, IFP, ATM and
All Citizens Party up; ANC, EFF and AIC down; parties without by-election
evidence unchanged. The drawn means move in the same direction for the five
largest parties.

P4. Johannesburg 2026: P(ANC largest party alone) falls and P(DA largest
party alone) rises.

P5. Tshwane 2026 centres move as well (same default, every city).

P6. Four Johannesburg parties' by-election levels are capped (AIC, ActionSA,
IFP, PA), so their centres do not land halfway between the two readings.

## Limits stated now

The weight cannot be scored on the panel by construction (P1), so it is
declared and argued, not tested. The by-election level is read off a handful
of self-selected wards per party and extended citywide; for a party with no
previous local result it is a level read from two to eight contests.
