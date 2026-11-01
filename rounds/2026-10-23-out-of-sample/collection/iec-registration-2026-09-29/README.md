# Johannesburg voters' roll by ward, "as at 29 September 2026"

`joburg_ward_registration_2026-09-29.csv` — 135 wards, read on 2026-10-28 from
the IEC's live registration statistics page, which now labels its snapshot
"Registered voters as at 29 September 2026":

    elections.org.za/pw/StatsData/Voter-Registration-Statistics
    -> province: Gauteng -> municipality: JHB - City of Johannesburg

Method: Chrome, the selector driven by hand; each of the seven pages of the ward
table read from the DOM (`td` cells of rows whose first cell is an 8-digit ward
code) and appended. Commas removed from counts.

## What it says (measured 2026-10-28)

| | 26 Sep snapshot (`archive/iec-registration-2026-09-26/`) | 29 Sep snapshot (this file) |
|---|---|---|
| Wards | 135 | 135 |
| Voting districts, summed over wards | 862 | 862 |
| Registered, summed over wards | 2,417,915 | 2,417,915 |
| Registered, the page's demographics block | 2,417,302 | 2,417,915 |
| Wards whose VD count or registration differs between the two | — | 0 |

The ward table is identical, row for row. The two changes are the date label
and the demographics total, which now equals the ward sum (the 613-voter
disagreement recorded in the 26 September README is gone).

Not established: whether "29 September" is the certified roll. The page does not
say so. Nothing in `data/` was changed; the model reads the 26 September file,
whose ward figures are the same.
