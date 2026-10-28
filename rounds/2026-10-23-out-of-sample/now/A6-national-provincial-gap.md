# A6. National and provincial ballots, City of Johannesburg, NPE 2009 and 2014

Bounds DATA-USE-AUDIT §2 item 6: everything the code calls "national" reads the
provincial ballot. Produced 2026-10-28 by `now/A6_gap.py` (read-only; prints to
stdout). Every number below is **measured** from that run unless marked otherwise.

Inputs:

- `data/raw/elections/_source/npe2009_national_and_provincial.zip` (member `2009 NPE.csv`; events `22 APR 2009 NATIONAL ELECTION`, `22 APR 2009 PROVINCIAL ELECTION`)
- `data/raw/elections/_source/npe2014_national_and_provincial.zip` (member `2014 NPE.csv`; events `2014 NATIONAL ELECTION`, `2014 PROVINCIAL ELECTION`)
- `data/raw/elections/npe2009_JHB_vd_party.csv`, `data/raw/elections/npe2014_JHB_vd_party.csv` (the model's files)

Parsing: municipality head before ` - ` equal to `JHB`; party votes from the
`VALID VOTES` column (the party's votes, not the VD total); thousands separators
stripped; decoded latin-1 line by line as `ingest_historic.open_member` does. The
memory note `iec-csv-format-traps.md` named in MEMORY.md does not exist on disk;
the traps were taken from the docstrings of `src/ingest_historic.py` and
`src/ingest_npe.py`.

Gap = national share minus provincial share, in percentage points (pp), each share
over that ballot's own valid votes in the same unit (city or ward).

## 1. Checks

| check | 2009 national | 2009 provincial | 2014 national | 2014 provincial |
|---|---|---|---|---|
| VDs | 759 | 759 | 825 | 825 |
| wards (2006 delimitation in 2009, 2011 in 2014) | 109 | 109 | 130 | 130 |
| parties on the ballot | 26 | 20 | 29 | 22 |
| sum of party votes, citywide | 1,546,041 | 1,483,848 | 1,644,413 | 1,570,600 |
| sum over VDs of (total cast − spoilt) | 1,546,041 | 1,483,848 | 1,644,413 | 1,570,600 |
| VDs where party votes ≠ cast − spoilt | 0 | 0 | 0 | 0 |
| spoilt votes, citywide | 16,563 | 15,590 | 15,596 | 14,579 |

The model's files against the zip's provincial ballot, per (ward, VD, party) cell:

| | 2009 | 2014 |
|---|---|---|
| cells in model file / in zip provincial | 15,180 / 15,180 | 18,150 / 18,150 |
| cells that differ | 0 | 0 |
| VD `Total_Valid_Votes` that differ from zip cast − spoilt | 0 | 0 |
| model cells equal to the zip's **national** cell | 5,485 of 15,180 | 7,224 of 18,150 |

The model's NPE 2009 and 2014 files are the provincial ballot exactly.

## 2. Citywide shares

### NPE 2009 (national valid 1,546,041; provincial valid 1,483,848)

| party (IEC name) | national votes | national % | provincial votes | provincial % | gap pp |
|---|---|---|---|---|---|
| AFRICAN NATIONAL CONGRESS | 978,568 | 63.295 | 925,181 | 62.350 | +0.945 |
| DEMOCRATIC ALLIANCE/DEMOKRATIESE ALLIANSIE | 320,043 | 20.701 | 323,285 | 21.787 | −1.086 |
| CONGRESS&nbsp;&nbsp;OF THE PEOPLE (two spaces in the file) | 146,757 | 9.492 | 142,650 | 9.614 | −0.121 |
| INKATHA FREEDOM PARTY | 36,173 | 2.340 | 35,391 | 2.385 | −0.045 |
| INDEPENDENT DEMOCRATS | 14,408 | 0.932 | 14,554 | 0.981 | −0.049 |
| AFRICAN CHRISTIAN DEMOCRATIC PARTY | 13,146 | 0.850 | 10,928 | 0.736 | +0.114 |
| VRYHEIDSFRONT PLUS | 7,134 | 0.461 | 7,665 | 0.517 | −0.055 |
| UNITED DEMOCRATIC MOVEMENT | 6,670 | 0.431 | 6,330 | 0.427 | +0.005 |
| AL JAMA-AH (national ballot only) | 4,293 | 0.278 | 0 | 0 | +0.278 |
| PAN AFRICANIST CONGRESS OF AZANIA | 3,639 | 0.235 | 3,907 | 0.263 | −0.028 |
| MINORITY FRONT (national only) | 1,317 | 0.085 | 0 | 0 | +0.085 |
| AFRICAN CHRISTIAN ALLIANCE-AFRIKANER CHRISTEN ALLIANSIE (provincial only) | 0 | 0 | 885 | 0.060 | −0.060 |
| 15 other parties, each \|gap\| ≤ 0.03 pp | | | | | |

Sum of \|gap\| over all 27 parties: 3.077 pp.

### NPE 2014 (national valid 1,644,413; provincial valid 1,570,600)

| party (IEC name) | national votes | national % | provincial votes | provincial % | gap pp |
|---|---|---|---|---|---|
| AFRICAN NATIONAL CONGRESS | 881,903 | 53.630 | 821,109 | 52.280 | +1.350 |
| DEMOCRATIC ALLIANCE | 489,409 | 29.762 | 508,362 | 32.367 | −2.605 |
| ECONOMIC FREEDOM FIGHTERS | 166,888 | 10.149 | 159,105 | 10.130 | +0.019 |
| INKATHA FREEDOM PARTY | 21,651 | 1.317 | 20,060 | 1.277 | +0.039 |
| UNITED DEMOCRATIC MOVEMENT | 10,522 | 0.640 | 7,423 | 0.473 | +0.167 |
| AFRICAN CHRISTIAN DEMOCRATIC PARTY | 10,126 | 0.616 | 8,471 | 0.539 | +0.076 |
| AGANG SOUTH AFRICA | 10,060 | 0.612 | 8,124 | 0.517 | +0.095 |
| NATIONAL FREEDOM PARTY | 10,039 | 0.610 | 9,127 | 0.581 | +0.029 |
| CONGRESS&nbsp;&nbsp;OF THE PEOPLE (two spaces in the file) | 9,072 | 0.552 | 8,229 | 0.524 | +0.028 |
| VRYHEIDSFRONT PLUS | 7,262 | 0.442 | 6,041 | 0.385 | +0.057 |
| AFRICAN INDEPENDENT CONGRESS (national only) | 6,868 | 0.418 | 0 | 0 | +0.418 |
| AL JAMA-AH (national only) | 5,186 | 0.315 | 0 | 0 | +0.315 |
| UBUNTU PARTY (national only) | 1,498 | 0.091 | 0 | 0 | +0.091 |
| MINORITY FRONT | 1,347 | 0.082 | 2,169 | 0.138 | −0.056 |
| 17 other parties, each \|gap\| ≤ 0.04 pp | | | | | |

Sum of \|gap\| over all 31 parties: 5.569 pp.

Full per-party rows for both years are in the script's output.

## 3. Ward-level gap, six largest parties by national vote

Per ward: national share minus provincial share, each over that ward's own valid
votes on that ballot. Every ward in the zip, both ballots present in all.

### NPE 2009, 109 wards (2006 delimitation)

| party | wards | median pp | 10th pct pp | 90th pct pp | min pp | max pp | mean \|gap\| pp |
|---|---|---|---|---|---|---|---|
| ANC | 109 | +0.903 | −0.204 | +1.905 | −6.421 | +9.220 | 1.214 |
| DA | 109 | −0.421 | −2.819 | +0.005 | −4.436 | +4.442 | 1.082 |
| COPE | 109 | −0.215 | −0.918 | +0.957 | −5.273 | +3.145 | 0.617 |
| IFP | 109 | −0.029 | −0.345 | +0.081 | −1.609 | +0.686 | 0.153 |
| ID | 109 | −0.003 | −0.336 | +0.175 | −1.985 | +1.542 | 0.177 |
| ACDP | 109 | +0.004 | −0.112 | +0.180 | −4.027 | +7.848 | 0.264 |

### NPE 2014, 130 wards (2011 delimitation)

| party | wards | median pp | 10th pct pp | 90th pct pp | min pp | max pp | mean \|gap\| pp |
|---|---|---|---|---|---|---|---|
| ANC | 130 | +1.153 | −0.009 | +2.947 | −7.884 | +4.526 | 1.558 |
| DA | 130 | −1.692 | −4.859 | −0.733 | −7.581 | +0.302 | 2.383 |
| EFF | 130 | −0.089 | −0.799 | +0.563 | −1.606 | +1.905 | 0.483 |
| IFP | 130 | +0.002 | −0.107 | +0.143 | −1.706 | +3.715 | 0.138 |
| UDM | 130 | +0.087 | −0.015 | +0.432 | −0.220 | +1.150 | 0.171 |
| ACDP | 130 | +0.047 | −0.085 | +0.262 | −0.196 | +1.524 | 0.121 |

Percentiles are linear-interpolated over wards, unweighted. Both ballots place every
VD in the same ward (VDs whose ward string differs between the national and
provincial rows: 0 in 2009, 0 in 2014; VDs on one ballot only: 0 and 0), so the
ward rolls aggregate identical geography.

## 4. Turnout on the two ballots

| | 2009 | 2014 |
|---|---|---|
| registered (sum over VDs, model file `Registered_Population`) | 2,003,007 | 2,184,484 |
| national cast (valid + spoilt) | 1,562,604 | 1,660,009 |
| provincial cast (valid + spoilt) | 1,499,438 | 1,585,179 |
| national turnout, % of registered | 78.013 | 75.991 |
| provincial turnout, % of registered | 74.859 | 72.565 |
| gap, pp | +3.154 | +3.426 |
| per-ward national − provincial valid votes: median / min / max | 513 / −2,473 / 2,149 | 473 / −949 / 2,173 |

The national ballot carries 62,193 (2009) and 73,813 (2014) more valid votes than
the provincial one. *Inferred, not checked:* these are voters casting outside their
registered province, who may vote on the national ballot only; the 2014 file's
`SECTION 24A VOTES` column was not read. The excess is not uniform: national cast is below provincial cast in 45 of 759 VDs
(2009) and 47 of 825 (2014), and national valid votes are below provincial in 4 wards
each year (largest: ward 79400054, 19,483 vs 21,956, in 2009; ward 79800075, 8,258
vs 9,207, in 2014). Measured; the cause is not established.

## 5. Which file and ballot each "national" reader opens

Every reader resolves the filename through `cityconfig.CALENDAR`
(`src/cityconfig.py:104` `npe2009_{CODE}_vd_party.csv`, `:106`
`npe2014_{CODE}_vd_party.csv`). Those files were written provincial-only by
`src/ingest_historic.py:93` (`npe2009`, `prefer_event: "PROVINCIAL"`, applied at
`:396`) and `src/ingest_npe.py:186-189` (`--event` default `PROVINCIAL`, 2014);
§1 confirms both cell for cell. No reader filters by ballot on an NPE file; each
takes every row, which is every provincial row.

| reader | where the path is built / file opened | file | ballot |
|---|---|---|---|
| baseline, `montecarlo.run_model` (def `:5919`) | `src/montecarlo.py:6161` `load(data_dir / target.results(target.previous_npe), None)` | previous NPE | provincial (all rows) |
| baseline second read, `pools.emit_pools` (def `:5961`) | `src/pools.py:6066-6074` | previous NPE | provincial |
| θ, `levels.theta_record` (def `:680`) | `src/levels.py:731,738` → `_citywide` `:305` | every NPE before an LGE < T | provincial |
| `pools.national_fits` | `src/pools.py:5419`, `fit_city(city, npe, …)` `:5451` → `ward_party_shares` `:1904-1907` | previous NPE | provincial |
| arrivals / prior-local, `pools._npe_citywide_state` | `src/pools.py:4001`, path `:4023-4035`; called `:4056`, `:5696` | NPE before each LGE | provincial |
| VD turnout level, `turnout.py` | `ELECTIONS` `src/turnout.py:69-72`; `read_turnout` `:83`, opened `:94`; level `base_npe` `:251`, roll `:304` | every election; level from previous NPE | provincial (NPE is not `two_ballot`, `cityconfig.py:94-95`) |
| γ fallback, `gamma_recent.py` | `src/gamma_recent.py:70` `load(…target.results(target_year), None)` | previous NPE | provincial |
| γ folds, `fold.py` | `FOLDS` base `src/fold.py:80` (2014), `:89` (2019); `load` `:150` with `ballot=None` | fold base NPE | provincial |

Line numbers are from the tree at commit `99556398`; the audit's `run_model :6064`
now sits at `:6161`.
