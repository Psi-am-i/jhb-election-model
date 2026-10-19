# By-elections do not move a party with no earlier record (owner decision, 2026-10-19)

Written before the change is made or run.

## The change

Owner, 2026-10-19, after seeing the All Citizens Party moved from 0.05% to
1.24% of the Johannesburg vote by two by-elections (159 and 39 votes): "So if
they have no record I would ignore them entirely ... no record means no record
of any kind (MK keeps its seats)."

In `montecarlo.blended_centres`, a party gets no by-election weight when it
has no earlier vote of its own anywhere the model reads: no θ prior (so no
national share), no previous local PR share and no previous local ward share.
At Johannesburg 2026 these are the parties sized by the arrival record
(the "seeded level" route). MK has a 2024 national share and a θ prior, so it
keeps its by-election weight. Everything else from MODEL-LOG §1.323 is kept:
`w_bye` 0.5, the cap, `BYE_MIN_WEIGHT`, the shrink and normalisation.

## Predictions

Measured against the tree at the end of the 0.5 change (MODEL-LOG §1.323),
Johannesburg and Tshwane 2026, 5,000 draws, seed 20261104, in process.

Q1. All 24 backtest city-years identical (no backtested target has a
by-election in the current file).

Q2. No pool spec changes.

Q3. Johannesburg: the two parties moved by by-elections with no record, the
All Citizens Party and the Truth and Solidarity Movement, return to their
pre-shrink centres at `w_bye = None` (0.04% and 0.06%). Every other party's
pre-shrink centre is unchanged from §1.323.

Q4. Johannesburg: the All Citizens Party's mean seats fall from 3.3 to under
0.5; the seats it gave up go mostly to the five largest parties, none of
which moves by more than 1.5 seats.

Q5. Tshwane: no number moves (it has no by-election input).

## Limits stated now

Argued, not tested: the rule is the owner's judgement that two by-elections
are not evidence about a party nobody has measured before. The backtest cannot
score it until earlier by-elections are added.
