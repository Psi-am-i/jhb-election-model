# The 2026 voters' roll for Tshwane, by ward

`tshwane_ward_registration_2026-09-29.csv` — 107 wards, read off the IEC's
**live** registration statistics page on 2026-10-21 for the snapshot it labelled
**"Registered voters as at 29 September 2026"**. Columns match
`../iec-registration-2026-09-26/joburg_ward_registration_2026-09-26.csv`.

    https://www.elections.org.za/pw/StatsData/Voter-Registration-Statistics
    -> province: Gauteng -> municipality: TSH - City of Tshwane

⛔ **That page is live and has no archive.** It reports one snapshot and
overwrites it. These are the only bytes of this date for Tshwane.

## How it was read

In Chrome, through the page's own province and municipality selectors (no
login, nothing submitted beyond those selectors and the table pager). The ward
table has six pages: five of 20 rows and one of 7. Each page's rows were read
from the DOM by JavaScript (table cells, no transcription), and paged with the
table's own Next button.

Cross-check of the copy: for each part written to disk (page 1; pages 2-6
together) the SHA-256 of the comma-stripped rows was computed both locally and
in the page against a fresh DOM read. Both matched. Page 1 was re-read after
paging back to it; page 1's DOM read also agreed row for row with the page's
text extraction.

## Checks

| check | result |
|---|---|
| ward rows | 107 |
| duplicate ward codes | 0 |
| ward codes vs `WardID_2026` in `data/processed/tshwane/vd_ward_2026.csv` | identical sets (107 each, 79900001-79900107) |
| Tshwane total, summing the 107 ward rows | **1,684,463** |
| Tshwane total, the page's demographics block | **1,684,463** (agrees) |
| Tshwane total, the page's Gauteng by-municipality block | 1,684,463, printed as 24.95% of Gauteng |
| Gauteng total, demographics block | 6,751,064 |
| Gauteng, summing the nine municipality figures on the page | 6,751,064 (agrees) |
| Registered per ward, smallest / largest | 10,455 (79900074) / 23,094 (79900048) |

## One count that does not match

The ward table's voting-district column sums to **796**. `vd_ward_2026.csv`
has **774** distinct voting districts in **951** VD-ward rows (334 rows flagged
split). The page's count is neither figure. It probably counts a split VD in each
ward it touches, but the page does not say so and this was not reconciled.
The model reads only `Ward` and `Registered` from this file
(`inputs_preflight.read_roll_snapshot`).

## Notes

- `inputs_preflight.roll_snapshot("tshwane")` resolves to this file and
  reads 107 wards totalling 1,684,463. The Johannesburg snapshot stays at
  `../iec-registration-2026-09-26/`, because the lookup is scoped by city.
- The Johannesburg traps in `../iec-registration-2026-09-26/README.md`
  (re-delimitation, split VDs, join through `montecarlo.ward_parts`) apply here
  too. Tshwane's split VDs are the `is_split = Y` rows of `vd_ward_2026.csv`.

Note on the voting-district column (checked on commit, 2026-10-21): Johannesburg's
26 September file shows the same kind of gap. Its column sums to 862, against
865 voting districts in 1,059 VD-ward rows in `data/processed/vd_ward_2026.csv`.
The IEC's per-ward VD count follows a rule of its own that is not documented on
the page. No reader uses the column.

## All eight metros, read 2026-10-23

On 2026-10-23 the page still labelled its snapshot "Registered voters as at
29 September 2026". Every metro was read through the same selectors and pager,
by same-origin form posts from inside the page (the page's own postback, no
login, nothing else submitted). Each metro's rows were sent out of the page
compactly encoded and decoded locally. The decoded ward count, voting-district
sum and registered sum were checked against the page's own figures, and all
matched:

| metro | file | wards | voting districts | registered (ward sum = demographics total) |
|---|---|---|---|---|
| Johannesburg | `../iec-registration-2026-09-26/joburg_ward_registration_2026-09-26.csv` (unchanged) | 135 | 862 | 2,417,915 |
| Tshwane | `tshwane_ward_registration_2026-09-29.csv` (unchanged) | 107 | 796 | 1,684,463 |
| Ekurhuleni | `ekurhuleni_ward_registration_2026-09-29.csv` | 112 | 653 | 1,711,998 |
| eThekwini | `ethekwini_ward_registration_2026-09-29.csv` | 112 | 839 | 2,032,565 |
| Cape Town | `capetown_ward_registration_2026-09-29.csv` | 118 | 829 | 2,158,976 |
| Mangaung | `mangaung_ward_registration_2026-09-29.csv` | 51 | 388 | 447,397 |
| Nelson Mandela Bay | `nelsonmandelabay_ward_registration_2026-09-29.csv` | 60 | 268 | 636,660 |
| Buffalo City | `buffalocity_ward_registration_2026-09-29.csv` | 50 | 380 | 458,695 |

- **Johannesburg:** the 29 September ward table is identical, ward by ward
  (voting districts and registered), to the 26 September file. The
  demographics block, which read 2,417,302 on 26 September (613 short of the
  ward sum), now reads 2,417,915, equal to the ward sum. Gauteng's total moved
  from 6,749,631 (26 September) to 6,751,064 (29 September), +1,433, outside
  Johannesburg.
- **Tshwane:** identical, ward by ward, to the file read on 2026-10-21.
- **The other six metros** are new here. `build_concordance.py` reads a city's
  newest snapshot (`inputs_preflight.roll_snapshot`), so these reach a city's
  2026 crosswalk the next time it is built. No 2026 forecast is run for them
  today.
- **Which roll is official:** the IEC timetable put the certified roll's
  publication at 26 August, after objections closed on 18 August. The roll
  closed at proclamation. The page's snapshot dates (26 and 29 September) are
  later than that. Whether the 29 September figures are the certified roll or
  a later update is not stated on the page; the Johannesburg and Tshwane ward
  rows did not change between the two dates.
- **The ANC nomination case** (Electoral Court 16 September; Constitutional
  Court 15 October) concerns candidate lists in six municipalities, Mangaung
  the only metro, not the voters' roll.
