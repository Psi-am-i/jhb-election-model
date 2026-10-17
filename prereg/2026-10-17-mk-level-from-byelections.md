# Measurement: does the 2026 MK level match what post-2024 by-elections show?

Written 2026-10-17, before any by-election share was computed against 2024.
A measurement, not a model change: nothing here moves a forecast. A change to
any party's level that follows from it gets its own pre-registration.

## What is measured

Population: every ward by-election in the eight metros after 2024-05-29 in
`data/raw/byelections/byelections_SA_vd_party.csv` (IEC by-election dashboard).

For each contest and each party: its share of valid votes in the voting
districts that reported in the by-election, and its share of valid votes in
the **same voting districts** on the 2024 provincial ballot
(`data/raw/elections/npe2024_<CODE>_vd_party.csv`), joined on `VD_Number`.
No ward crosswalk is used, so the comparison is place for place.
Party names go through `parties.canonical` on both sides.

Ratio r = by-election share / 2024 share, for each party with a 2024 share
of at least 3% in the contest's districts. Two versions for every party:

- A: contests the party stood in.
- B: A plus contests where it held at least 3% in 2024 and did not stand (r = 0).

Summary per party: the median of log r and the vote-weighted ratio (sum of
by-election votes over the sum of the 2024 share times by-election valid
votes), with the contest count. All parties are scored, Johannesburg alone
and the eight metros together.

The model's ratio for each party: Johannesburg's 2026 citywide centre
(`run_model(..., stop_after="drawer_inputs").centres`, no draws, nothing
written) over its 2024 provincial-ballot citywide share.

## What would mean what

- MK's by-election ratio (version B, Johannesburg and all metros) within
  ±0.15 of the model's MK ratio: the level is consistent with the by-elections.
- MK's by-election ratio more than 0.15 above the model's, and the same gap is
  not seen in the other parties (ANC, DA, EFF, ActionSA within ±0.15 of their
  model ratios): the MK level is too low.
- Every party's by-election ratio sits away from the model's in the same
  direction: a by-election effect (low turnout, a different electorate),
  not an MK finding.
- Fewer than five Johannesburg contests with MK at or above 3% in 2024:
  Johannesburg alone cannot decide it, and only the metro pool is read.

## Limits stated now

- By-elections are low-turnout contests with a ward candidate on the ballot.
  The ratio measures a by-election electorate, not the 2026 electorate.
- Where MK stood is MK's choice. Version A over-states its strength wherever
  it stood selectively, which is why B is read first.
- `montecarlo.blended_centres` already adds a by-election term to the 2026
  centres (`w_bye`). That term is reported with the result, so a match is not
  read as independent confirmation if the by-elections built it.
