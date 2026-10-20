# The by-election weight tested on 2021, with the 2016-cycle by-elections

Written before the run. No model code changes; the experiment runs in a
scratch directory and writes nothing into `data/`.

## The question

The forecast blends each party's expected share halfway with what the
by-elections since the last local election imply (`w_bye` 0.5, owner,
JUDGEMENT-CALLS §A59), untested because no backtested election had
by-elections before it in the record. The by-elections between the 2016 and
2021 local elections are now on disk
(`data/raw/byelections/byelections_SA_vd_party_2016.csv`, 77 metro contests).
With them the 2021 elections in the eight metros can be forecast with the
by-election term switched on, using only contests before 1 November 2021.

The owner's second question: a by-election in which the ward changed party
should count more than one the same party held.

## Method

* Deltas per metro built by `byelections.main(["--city", slug, "--target",
  "2021", "--data-dir", RAW, "--processed", OUT])` from a scratch raw tree in
  which `byelections/byelections_Gauteng_vd_party.csv` is a link to the
  2016-cycle file and `elections` a link to `data/raw/elections`. Each scratch
  processed directory also holds a copy of the metro's
  `data/processed/<slug>/2021/turnout.csv` (and `gamma_recent.csv` where it
  exists).
* Scored with `compare_history.run_city_year(slug, "2021", 1000, data_dir,
  overrides=[...])`, with `montecarlo.run_model` wrapped to pass the scratch
  `processed`, in process: the same draws (1,000) and seed (20261104) as the
  committed `history.json`, so the arms differ only in the by-election term.
* Instruments, per city-year and summed over the eight metros: average
  list-vote error (`pr_mae`, points), wards called wrong, seats given to the
  wrong party (half the summed absolute seat error).
* Arms:
  * **A0**: `w_bye` 0, deltas present.
  * **A5**: `w_bye` 0.5 (the shipped value).
  * **A10**: `w_bye` 1.0.
  * **F**: `w_bye` 0.5, each contest whose ward winner differs from its 2016
    ward winner weighted ×2 (its votes ×4 in a scratch copy of the input, so
    √votes doubles and shares are unchanged).
* Every arm records, per party, its by-election weight sum, the implied
  level, the level after the cap, and the centre (`30_centres` trace).

## What the sample is (computed before writing this)

By-elections reach a party only with contest weight ≥ 30. Parties admitted:
Johannesburg ANC, DA, EFF (12 contests); Ekurhuleni 7 parties (14); Cape Town
12 (17); eThekwini 12 (15); Nelson Mandela Bay 5 (9); Mangaung ANC, EFF (4);
Tshwane and Buffalo City none (3 each). Five contests changed the ward's
party: Johannesburg 1 (DA→ANC), Ekurhuleni 1 (DA→ANC), eThekwini 3 (DA→ANC
twice, independent→ANC). Every flip is toward the ANC.

## Predictions

The mechanism: each admitted party's centre moves halfway toward its 2016
list share plus its by-election swing (held inside its usual range). The
by-election swings (ward ballot, weighted) against the real 2016→2021 list
change:

| metro | ANC: by-elections / real | DA: by-elections / real |
|---|---|---|
| Johannesburg | +4.1 / −11.7 | −2.6 / −13.0 |
| Ekurhuleni | −1.0 / −10.5 | −2.0 / −5.7 |
| Cape Town | −7.7 / −5.8 | −8.7 / −8.1 |
| eThekwini | +0.6 / −16.6 | −1.9 / −1.2 |
| Nelson Mandela Bay | +3.0 / −1.9 | −1.6 / −6.7 |
| Mangaung | −3.7 / −5.3 | — |

So the by-elections missed the ANC's 2021 fall everywhere except Cape Town
and Mangaung. The model without them already forecasts the ANC too high in
Johannesburg (+5.3 points), Ekurhuleni (+4.3), eThekwini (+3.8) and Cape Town
(+3.5), and too low in Mangaung (−2.6) and Nelson Mandela Bay (−2.0).

B1. **Control.** A0 reproduces the committed `history.json` 2021 rows
exactly, for all eight metros.

B2. Tshwane and Buffalo City are identical to A0 in every arm.

B3. At A5, the list-vote error worsens in Johannesburg, Ekurhuleni and
eThekwini (the ANC is moved up toward its 2016 share when it fell) and
improves in Cape Town and Mangaung (the ANC moves down in Cape Town and up
in Mangaung, toward its 2021 result in both). Nelson Mandela Bay: no prediction of sign.

B4. Summed over the eight metros, A5's average list-vote error is worse than
A0's.

B5. A10 is worse than A5 in each of Johannesburg, Ekurhuleni and eThekwini.

B6. F is worse than A5 on the ANC's list error in Johannesburg, Ekurhuleni
and eThekwini (every flip raises the ANC's swing, and the ANC fell).

B7. Wards called wrong and seats given to the wrong party, summed over the
eight metros, are no better at A5 than at A0.

## What it can and cannot settle

One cycle, six city-years with any by-election effect, and five seat flips
in three of them. A result here is evidence about 2016→2021, when turnout
fell most in ANC areas, and only indirectly about 2021→2026. It cannot
choose a weight to a decimal place; it can say whether by-elections, as the
model reads them, moved the 2021 forecast toward or away from the result.
Calibration and band coverage are not read: the width record was measured
about centres with no by-election term.

Nothing here changes the model. The weight is the owner's decision
(§A59); this is evidence for it.
