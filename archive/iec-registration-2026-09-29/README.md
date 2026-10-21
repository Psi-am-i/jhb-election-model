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
