# Census 2011 and 2001 by ward, single year of age × population group

Downloaded 2026-10-30 from Stats SA SuperWEB2 (superweb.statssa.gov.za/webapi),
guest login, as CSV (semicolon-separated, decimal comma, person-weighted
counts, so not whole numbers).

| file | dataset path | rows × columns | geography |
|---|---|---|---|
| `census2011_ward_age_popgroup.csv` | Census Profiles → Census 2011 → Electoral Ward Profiles → Descriptive | 4,277 wards × (122 ages incl. total × 6 groups incl. total) | level "South Africa by Electoral Wards"; ward codes as in the 2011 LGE (Johannesburg 798xxxxx) |
| `census2001_ward_age_popgroup.csv` | Census Profiles → Census 2001 → Electoral Ward Profiles → Descriptive | 3,794 wards × (122 × 5 incl. total) | the ward level (the menu labels it "Geography"); "Codes" switched on in the Geography column menu; Johannesburg 79400xxx |

Groups: 2011 Black African, Coloured, Indian or Asian, White, Other; 2001 the
first four (no "Other").

`parse_superweb.py SRC OUT` writes a long table (ward, ward_label, age, group,
persons) without the Total rows and columns. The long files (`*_long.csv`,
about 116 MB and 80 MB) are gitignored; rebuild them with the script.

## Checks (measured 2026-10-30, from the long tables)

| | sum over wards | published | |
|---|---|---|---|
| South Africa 2011 | 51,770,560 | 51,770,560 (Census 2011) | equal |
| Johannesburg 2011 (798, 130 wards) | 4,434,827 | 4,434,827 | equal |
| South Africa 2001 | 44,819,778 | 44,819,778 (Census 2001) | equal |
| Johannesburg 2001 (79400, 109 wards) | 3,225,832 | 3,225,812 | +20, weighting |

Johannesburg's group shares: 2011 Black African 76.42%, Coloured 5.58%,
Indian or Asian 4.88%, White 12.28%, Other 0.85%; 2001 Black African 73.5%,
Coloured 6.4%, Indian or Asian 4.1%, White 15.9%.

Nothing the model reads was changed. Purpose: `DATA-PLAN.md` C8 and
`DATA-QUALITY.md` 23 (the census released before each backtest target; the
2011-against-2022 comparison of ward group mix).
