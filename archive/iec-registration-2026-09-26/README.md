# The 2026 voters' roll for Johannesburg, by ward

`joburg_ward_registration_2026-09-26.csv` — 135 wards, read off the IEC's
**live** registration statistics page on 2026-09-27 for the snapshot it labelled
**"Registered voters as at 26 September 2026"**.

    elections.org.za/pw/StatsData/Voter-Registration-Statistics
    -> province: Gauteng -> municipality: JHB - City of Johannesburg

⛔ **That page is live and has no archive.** It reports one snapshot and
overwrites it. These are the only bytes of this date, which is why a 135-row
CSV is committed rather than left in a scratchpad.

The figure is behind a province/municipality selector that plain HTTP will not
drive — three attempts at the ASP.NET postback returned no municipality list.
It was read in a browser, and the ward table was paged through seven pages.
Pages 1 and 2 were transcribed by hand and then re-extracted programmatically
and compared: identical.

## What it says

| | |
|---|---|
| City total, demographics block | **2,417,302** |
| City total, summing the 135 ward rows | **2,417,915** |
| Voting districts, summed over wards | 862 |

⚠️ **The IEC's own page gives two different city totals, 613 apart** (0.025%),
on one snapshot. Not a transcription error: both figures were re-read. Which is
authoritative is unknown. Recorded rather than reconciled.

Cross-check that the scrape is complete: the nine Gauteng municipality figures
on the same page sum exactly to the provincial 6,749,631, and 2,417,302 of that
is 35.81%, the percentage printed beside it.

## Two traps before this is compared with anything

⛔ **Wards were re-delimited for 2026.** 153 of the 860 voting districts common
to both sit in a different ward code than they did in 2021. A ward-to-ward
comparison across that boundary is comparing different areas, and any "growth"
read off it is part migration and part redrawing, in unknown proportion.

⛔ **Johannesburg has split voting districts.** `data/raw/geo/vds2026_JHB.geojson`
carries **1,059 VD-ward rows for 865 unique VDs**: a VD that straddles a ward
boundary appears once per ward. Grouping its features naively assigns each split
VD's whole roll to one ward and produces ward growth rates from -42% to +254%,
which are an artefact of the join and not a measurement. `montecarlo.ward_parts`
is the function that already handles this and is what a real comparison must go
through.

## What it is for

The model weights its turnout projection **per voting district**, using the
registration recorded in the base national election — NPE 2024, 2,348,781 across
865 VDs. This file is per WARD. Using it therefore means apportioning each
ward's 2026 total down to its voting districts, for which the geojson supplies
both the VD-to-ward parts and each VD's 2024 registration.

That is a change to a model input and needs a pre-registration before it is
built, not a quiet edit.

## Re-read on 2026-10-15

The IEC page, re-read on 2026-10-15, shows "Registered voters as at 29 September
2026". All 135 ward rows are identical to this 26 September file, so the roll
appears closed. The page offers no voting-district-level view.
