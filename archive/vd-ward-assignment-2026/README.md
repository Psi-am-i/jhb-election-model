# Which 2026 ward each voting district belongs to

`assignment.csv` (`VD_Number, WardID_2026, status`) places each of the crosswalk's
865 voting districts wholly in one 2026 ward. `src/build_concordance.py`
(`ASSIGNMENT_2026`, `read_assignment`, `apportion_roll`) reads it to build
`part_registered_2026`. Rule and judgement calls: JUDGEMENT-CALLS section T1;
input limits: DATA-QUALITY item 20.

## Why it exists

The IEC snapshot (`../iec-registration-2026-09-26/`) gives, per ward, a voter
total and a count of voting districts, and counts each of its VDs in one ward.
The crosswalk's split VDs carry the delimitation planner's part figures. The
assignment recovers which ward the IEC counts each VD in.

## How it was solved

Integer programme (scipy `milp`, HiGHS), `solver/solve.py`.

* Each VD takes one of the wards it has a part in (a VD may be dropped).
* Objective: the sum over wards of |IEC_w / g - sum of `vd_registered` of the VDs
  assigned to w|, in voters. `g` is the citywide growth, 2,417,915 / 2,348,781
  (the snapshot's ward rows over the crosswalk's `vd_registered`).
* Count deviations from the IEC's voting-district count per ward are penalised
  (`countpen`, 1e6 per VD in the tests; see `solver/run*.py` for the variants).
* At most 3 VDs may be dropped.
* `status`: `forced` (822) = the alternative ward costs more than 1,000 voters of
  objective, so the solver's choice is not a near-tie; `free` (40) = a
  near-tie, placed by the solver's pick (`solver/alts.csv` gives the cost of the
  alternative per VD); `dropped-largest-part` (3) = the solver dropped them and
  they are placed in the ward holding their largest `part_registered`.

## Tests run at the time (2026-10-15)

* Per-ward ratio IEC_w / sum of assigned `vd_registered`: sd 0.054 (min 0.949,
  max 1.267) for the solver's output; sd 0.168 (0.704 to 1.704) under the
  earlier rule (every part of a ward scaled by one factor). With the 3 dropped
  VDs placed, sd 0.060, min 0.823, max 1.267.
* Null test (in `solver/run*.py`): random growth targets in place of the IEC's cannot get the sd below
  0.18, so 0.054 is not what the solver reaches on anything.
* Recovery test (`solver/run5.py`): the solver was run on targets
  built from a known assignment with noisy growth; it recovered 90 to 97% of
  the split VDs.

## Limits

* No assignment matches the IEC's VD counts exactly: about 17 VDs are counted in
  wards neither geo file offers.
* The 40 `free` VDs are near-ties; the solver's pick is not evidence. The
  voting-station file agrees with the pick for 17 of the 40 (`solver/run7.py`).
* A measured recovery on constructed truth says nothing about how many of the
  IEC's real placements are right; only the IEC's membership list would.

## Re-solving

The project venv has no scipy, highspy or pandas-solver stack. Make a throwaway
venv with `scipy numpy pandas highspy`, set `R` at the top of `solver/solve.py`
to this repository, and run from `solver/` (the `run*.py` scripts `exec`
`solve.py` and `run2.py`, and read `assignment.csv` in the working directory
in the form of the original solver output: `VD_Number, ward_2026, status`).
The solver's output used ward ids as numbers and `dropped` rows with no ward;
`assignment.csv` here is that output with the ward written as `WardID_2026` and
the three dropped rows filled. The scripts are kept as they were run.
