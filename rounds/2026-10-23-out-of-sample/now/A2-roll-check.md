# The 2026 roll the forecast reads, checked against the IEC (2026-10-28)

`DATA-PLAN.md` §7 "now" row; `DATA-PLAN-REVIEW.md` §3 on A2: refresh the
Johannesburg snapshot only if the IEC has published a later roll than
2026-09-26.

**Measured.** The IEC page now reads "Registered voters as at 29 September
2026". All 135 wards were read off it on 2026-10-28
(`collection/iec-registration-2026-09-29/`). Every ward's VD count and
registration equals the 26 September snapshot the forecast reads: 2,417,915
registered in 862 VDs summed over wards, 0 wards different. The page's
demographic total moved from 2,417,302 to 2,417,915 and now equals the ward
sum.

**Consequence.** No refresh. The forecast's roll is the latest the IEC
publishes, to the voter. Whether the IEC regards it as the certified roll is
not stated on the page.

**The second half of A2 (recorded, not changed).** Two rolls are used in one
Johannesburg 2026 run: `turnout.py` weights its VD turnouts by each VD's
`Registered_Population` from `data/raw/elections/npe2024_JHB_vd_party.csv`
(`turnout.py:84-105`; 865 VDs, 2,348,781 registered), while `run_model` sizes
the electorate from the 2026 crosswalk (`part_registered_2026`, 2,417,915). The
2026 roll is 69,134 voters (2.9%) larger than the 2024 one. How the turnout
level from the first is applied to the second is part of the turnout trace
(`now/A3-turnout-trace.md`), not repeated here.
