# Pre-registration: whole-VD roll assignment and the owner's MK call (2026-10-15)

Written before the re-emit. Changes: `982cc97` (one roll in the spec, preflight
guards, claims register, `parent_weight`, MK = 0.9 §SJ1) and `185fa78` (each VD
assigned wholly to one ward, `archive/vd-ward-assignment-2026/`). Baseline for
comparison: the §1.304 run (`.claude/roll-2026-10-15/arm-roll`).

Gates: G1 every backtest city-year identical to the tracked `history.json`
(no backtest reads the 2026 crosswalk or the 2026 judgements file); G2 the 2026
roll sums to 2,417,915, each ward to its IEC row.

Predictions, from the mechanism (§1.304: citywide shares are pinned by
`solve_and_predict`; the roll and the pool vectors move geography only):
P1. With MK's call, every party's mean citywide list share within 0.05 points
    of the run without it; same for the assignment change against §1.304.
P2. The assignment change moves under 6 ward favourites against §1.304, and no
    party's mean seats by more than 1.
P3. MK's call (MK drawn 90% from the ANC's pool vector, not 35%) makes MK's
    and the ANC's geography more alike, so MK's ward wins fall (it no longer
    concentrates where the city mix put it) and the ANC's rise, with mean seats
    moving under 2 for any party. Direction of MK's ward wins: down.
Scored in the round's report, including what it got wrong.
