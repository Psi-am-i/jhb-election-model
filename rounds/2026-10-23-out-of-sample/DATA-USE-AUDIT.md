# Which data each part of the model reads

Read-only audit, 2026-10-23, from the code on branch `site-sweep-1` at
`90037fd`. No model, test or sweep was run. Seven small reads were made under
`nice -n 15`; each is marked **measured**, with what it read. Everything else is
**read** from the code at the cited line. Anything not read directly is marked
**inferred**.

Conventions used in the tables:

- *T* is the target election. "< T" means strictly before it.
- "NPE" files hold the **provincial** ballot only (`ingest_historic.SPECS`
  `prefer_event: "PROVINCIAL"`, `src/ingest_historic.py:74-93`; `ingest_npe.py`
  `--event` default `PROVINCIAL`, `:188`). Where the code says "national", this
  table says "NPE (provincial ballot)".
- "clean file" is `data/raw/elections/<tag>_<CODE>_vd_party[_clean].csv`, the
  per-VD file named by `cityconfig.CALENDAR` (`src/cityconfig.py:100-110`).
- "canonical" is `parties.canonical(sPartyName)` (`src/parties.py:130`): the
  ALIASES table, then MINOR_ALIASES, then a name-derived code.
- "HELD_BACK" is `levels.HELD_BACK` (`src/levels.py:282`): `lge2000` and
  `npe1999` withheld for the seven metros other than Johannesburg.
- The census is Census 2022 ward population-group shares on the 2021
  delimitation (`config/dimensions.toml`, the only `[[dimension.census]]`
  entry). For the 2011, 2016 and 2021 backtests it was taken after the target.

## 1. Matrix

### 1a. Party levels

| Part | Where | Elections and window | Ballot | Geography and join | Roll | Census | Party ID | Artefact, generator, target-aware? | Metros |
|---|---|---|---|---|---|---|---|---|---|
| Baseline level (citywide and VD shares) | `montecarlo.run_model` `:6064` (`fold.load(previous_npe)`); `pools.emit_pools` `:6066-6077` (a second read of the same file) | previous NPE only (2009 / 2014 / 2019 / 2024 for T = 2011 / 2016 / 2021 / 2026) | provincial, every row | VD numbers of the NPE file | – | – | canonical | raw file, read at run time | 8 |
| θ, NPE→LGE retention | `levels.theta_record` `:680` via `levels._citywide` `:305` | every LGE < T, each paired with the NPE before it; from 2000 for JHB, from 2006 for the other seven (HELD_BACK) | LGE PR over NPE provincial | citywide | – | – | canonical | computed per run, no artefact | 8 pooled |
| ρ, LGE→LGE retention | `levels.local_record` `:877` | consecutive LGE pairs, both < T; 2000→2006 JHB only | PR / PR | citywide | – | – | canonical | per run | 8 pooled |
| Spine, size window, θ prior | `levels.spine` `:1646`, `size_window` `:1509`, `theta_prior` `:946` | θ and ρ records as above; current size = previous NPE share (θ route) and previous LGE PR share (ρ route) | as above | citywide | – | – | canonical | per run | 8 pooled |
| Roster parties with only a previous-LGE record | `levels.local_record_only` `:2253`; `run_model` `:6398-6440` | previous LGE | PR | citywide | – | – | canonical | per run | 8 |
| Arrival total, entrant record, splinter records | `pools._arrival_total_prior` `:4366`, `entrant_record` `:3702`, `arrival_group_record` `:4060`, `splinter_record` `:3839`, `home_splinter_record` | LGE < T paired with the NPE before it. LGE shares through `_citywide_for` `:2514`: `_metros/` (2021) or `_reports/` (2011, 2016) first, the clean file for 2000/2006; HELD_BACK honoured by the fallback only | LGE PR vs NPE provincial | citywide | – | – | canonical; lineage from `pools.SPLITS` | in the pool spec | 8 pooled |
| Arrival split weights (ward reach) | `pools._ward_reach` `:3749` | the target's own ward ballot if held; else the fitting LGE "carried forward", overridden by declared reach (`emit_pools` `:6292-6301`) | Ward rows (presence, not votes) | ward | – | – | canonical | in the spec | 8; `_metros/`/`_reports/` only, so empty for every 2000 and 2006 transition |
| Level shrink | `montecarlo.compress_levels`; `DEFAULTS["level_shrink"]` `:413` | no data at run time; the constant was chosen on Johannesburg 2016 and the 2021 panel (`JUDGEMENT-CALLS.md:1096`) | – | – | – | – | – | constant | all |
| Owner judgements | `pools.load_lineage`, `declared_roster` `:5079`; `judgements/<city>-<T>.toml` | none | – | – | – | – | canonical codes | toml | owner values only in `joburg-2026` (MK `parent_weight = 0.9`, ASA `support = 0.176`); no backtest file and not `tshwane-2026` carries one (grep) |
| Polls (off: `poll_paths = "off"`, `montecarlo.py:255`) | `polling.screen`, `metro_estimate` `:1041`, `contested_share` `:1000` | `polls.json`; contested share from the **target year's** votes cast (`votes_by_metro(year)` `:1023`, `NATIONAL_VOTES` `:482`) at a backtest, from `PROJECTED_METRO_SHARE` `:530` (2021) at 2026 | poll numbers: national (*inferred* from `scope`); denominator: LGE PR votes cast | metro | Wikipedia roll × turnout | – | poll codes | register | per city |
| By-election citywide tilt | `run_model` `:6948`, `blended_centres` | `byelection_party_deltas.csv` in the target's processed dir; exists for JHB 2026 only | Ward ballot delta, divided by `trusted_ward_pr` | ward → citywide | previous-LGE ward roll | – | canonical(PartyFullName) | `byelections.py`, target-aware | JHB 2026 only |

### 1b. Pools, turnout and geography

| Part | Where | Elections and window | Ballot | Geography and join | Roll | Census | Party ID | Artefact, generator, target-aware? | Metros |
|---|---|---|---|---|---|---|---|---|---|
| Pool vectors | `pools.fit_city` `:2325`, `ward_party_shares` `:1900`, called by `emit_pools` `:6008` | previous LGE only | PR | wards of the fitting LGE (its own `Ward` column) | fitting LGE's result-file roll | 2022, moved from 2021 wards via `reproject` `:1593` when the delimitation differs | canonical | `pools_<T>.json`; `emit_pools` takes the target; `artefact_key` | 8 × 2011/16/21; JHB and TSH 2026 |
| Pool vectors for parties absent from that LGE | `pools.national_fits` `:5419`, `place_vectorless` `:5492` | previous NPE | provincial | NPE VDs placed in wards by the preceding LGE's map (`_ward_resolver` `:1140`) | NPE result-file roll | 2022; **refused at 2019** (`census_drift_unmeasurable`, below) | canonical | in the spec | used at 2011, 2016, 2026; refused at every 2021 spec read (**measured**: `national_fit_refused` in joburg, tshwane, capetown `pools_2021.json`) |
| Pool sizes at T | `pools.registered_at_target` `:2931`, `_target_roll` `:3047` | target's roll | PR rows' `Registered_Population` | target delimitation; fitting-year composition reprojected fitting→target through `vd_map` | backtest: target result file; JHB 2026: `part_registered_2026`; TSH 2026: `part_registered` (2024 REGPOP) | 2022 | – | spec | as above |
| Pool turnout and its band | `pools.turnout_record` `:2542`, `turnout_band` `:2585`, `panel_turnout_spread` `:2696` | every LGE < T (2000/2006 for the seven only where not HELD_BACK); band width from consecutive LGE transitions < T across all eight cities | PR **valid votes** over roll (`ward_totals` `:1180`, no spoilt) | ward, census split | each LGE's own roll | 2022 | – | spec | 8 |
| Pool concentration α | `emit_pools` `:6340-6378`, `dirichlet_alpha` `:3223` | years in LGE transitions < T, through `metro_citywide` only, so 2011–2021 (deliberately not widened, §1.184 comment) | PR | citywide | – | – | canonical | spec | 8 pooled |
| Group-share tripwire (reports, moves nothing) | `group_share_record.py` `FITTED_LGE` `:68` | 2011, 2016, 2021 and NPEs after each, < T | PR / provincial | ward | – | 2022 | canonical | `group_share_record.json`, `--emit` | 8 |
| VD turnout pattern and level | `turnout.py main` `:156`; read by `run_model` `:6700-6740` | all elections < T; λ from the last two LGE/NPE pairs; level from the previous NPE; `run_model`'s high/low anchors use years ≥ 2011 only (`:6705`) | **higher of the two ballots, valid + spoilt** (`read_turnout` `:83`) | VD numbers | **previous NPE's per-VD roll** (`registered_<npe>` column) | – | – | `turnout.csv` per target; `--target`; no artefact key; **does not honour HELD_BACK** | 8 × 2011/16/21; JHB and TSH 2026 |
| By-election turnout tilt κ | `turnout.py` `:360-385` | `byelection_turnout.csv` in the target dir | ward ballot | previous-LGE wards → VDs | previous-LGE ward roll | – | – | JHB 2026 only | JHB 2026 |
| Ward parts in the draw | `montecarlo.ward_parts` `:1253`, `read_ward_crosswalk` `:1205` | held T: its own result file; 2026: `vd_ward_2026.csv` | – | held T: whole VD, ward number from the file; 2026: crosswalk parts (JHB: one ward per VD by the solver assignment; TSH: split VDs apportioned by `WardPop`) | as pool sizes | – | – | crosswalk from `build_concordance.py` (city-scoped, no target) | 8 |
| VD universe for the draw | `run_model` `:6064`, `:6785-6795` | previous NPE's VDs | – | a ward part enters only if its VD is in the previous NPE file **and** has registration | – | – | – | – | 8 |
| Census reprojection | `composition_at` `:1767`, `reproject` `:1593`, `_reprojection_drift` `:1702`, `delimitation_for` `:1672` | census delimitation 2021 → the election's | – | VD-number join through `vd_map` `:1529`, weighted by the destination year's registration | destination year's | 2022 | – | – | 8 |
| VD → 2026 ward crosswalk | `build_concordance.py` `ward_parts` `:162`, `apportion_roll` `:200` | MDB 2026 VD layer; IEC ward snapshot where held | – | `vds2026_<CODE>.geojson`; JHB: `archive/vd-ward-assignment-2026/assignment.csv` | JHB: 2026-09-26 snapshot; others: `REGPOP` (2024) | – | – | `vd_ward_2026.csv`; TSH file dated 1 Sep, no `part_registered_2026` column (**measured**, header and grep) | 8 |
| Historic VD concordance | `build_concordance.py` `ELECTIONS` `:75` | 1999–2024 | PR or all rows | VD number, then station name | – | – | – | `vd_concordance.csv`; read by the model only at `fold.py:503` | 8 built; JHB's path read for every city |
| Ward contestation and ballot presence | `levels.ballots` `:2050`, `contestation` `:1929`, `slate_coverage` `:2088`, `declared_contestation` `:774` | held T: its own result-file rows (nomination fact); 2026: `[roster.wards]`; else projected from the previous LGE; slate weights: previous LGE PR votes by VD | Ward rows, PR rows | WardID; VD → T's ward by `vd_map` | – | – | canonical | toml / raw | 8; declared at JHB and TSH 2026 |
| Ward/PR split ratio | `run_model` `:6849` (`levels.trusted_ward_pr` `:1904`); fallback median from `levels.ward_pr_ratios` `:1859` | previous LGE | Ward ÷ PR | citywide | – | – | canonical | per run | 8 |
| By-election local ward term | `run_model` `:6593-6650` | `byelection_contest_detail.csv`; hard-coded column `share_2021` (`:6628`) | Ward ballot | previous-LGE wards → VDs | – | – | canonical | JHB 2026 only | JHB 2026 |
| γ (geographic persistence) | `run_model` `:6656-6690`; `fold.py`; `GAMMA_FOLD` `montecarlo.py:1183` | 2026 → fold 1 (2014→2016); 2021 → fold 1 (2014→2016); 2016 → fold 3 (2009→2011); 2011 → fold 4 (2004→2006); then `gamma_recent.csv`; then 1.0 | NPE provincial → LGE PR and Ward, fitted separately | VD | fold weights: target roll × prior-LGE turnout (`fold.turnout_weights` `:305`, default `level`) | – | canonical | `fold<N>_parameters.csv` city-level; fold generator takes no target | fold 1/3/4 in 8 metros; fold 2 JHB and TSH; fold 5 JHB |
| γ fallback | `gamma_recent.py` | previous LGE → previous NPE (LGE→NPE direction, applied NPE→LGE) | PR → provincial | VD | – | – | canonical | `gamma_recent.csv` per target; exists for JHB 2011/16/21/26 and TSH 2021 only (**measured**, `find`) | 2 |

### 1c. Widths, by-election weights, seats, outputs, scoring

| Part | Where | Elections and window | Ballot | Geography and join | Roll | Census | Party ID | Artefact, generator, target-aware? | Metros |
|---|---|---|---|---|---|---|---|---|---|
| By-election deltas | `byelections.py main` `:346-352`, `load_byelections` `:180`, `weighted_deltas` `:249` | **`byelections_Gauteng_vd_party.csv` only**; contests after the previous LGE and before T | delta vs the previous LGE's **ward** ballot | ward prefix; previous-LGE wards | previous-LGE ward roll; by-election turnout = valid votes ÷ that roll | – | canonical(PartyFullName) | three CSVs per target dir; exist only in `data/processed/` (JHB 2026) | Gauteng file only |
| By-election weight test | `bye_value.py`; `byelections.SA_FILE` `:84` | `byelections_SA_vd_party.csv` (2021–26 cycle), contests before 2024-05-29; outcome 2024 | delta on ward ballot; base 2021 PR; outcome provincial | ward | previous-LGE ward roll | – | canonical | `bye_value.json`; read only when `w_bye` is None (default 0.5, `montecarlo.py:162`) | 8 |
| Width record | `width_record.py` `FORWARD` `:80`, `fallback_record` `:504` | 2016 from 2011; 2021 from 2011–16; 2026 from 2011–21; 2011 from the θ residual at target 2006 | realised PR share vs `pool_spec` centre | citywide | – | via the specs (2022) | canonical | `width_record.json`, `--emit`, keyed | 8; the 2006 residual reads `theta_record`, which at 2006 has only JHB's 1999→2000 transition live (*inferred* from HELD_BACK and `theta_record`) |
| Seat allocation | `seats.allocate`; `cities/*.toml [structure.by_year]`; `DEFAULTS["overhang_rule"] = "deduct"` `:384` | – | combined ward + PR | – | – | – | canonical | statute + config | 8; `deduct` applied to 2011 and 2016 although the statute was amended in 2021 (MACHINERY §6) |
| Ground truth | `backtest.actual_result` `:987`; `official_seats` (`_reports/*seat_calculation_detail.xls`) | the target | Ward + PR, clean file | ward from the file | – | – | canonical | raw | 8 |
| Scored shares | `compare_history.actual_shares` | the target | PR and Ward | citywide | – | – | canonical | raw | 8 |
| "Has a baseline" for relabelling | `backtest.arrival_baseline` `:1121` | previous NPE, share > 0 | provincial | citywide | – | – | canonical | raw | 8 |
| Benchmarks | `benchmarks.build_context` `:222`, `sources_for` `:91` | target file (wards, roll), previous LGE, previous NPE, the NPE before the previous LGE, the LGE before that (`earlier_lge`: **2000 for T = 2011**) | Ward, PR, provincial | target's ward map | previous-LGE PR valid votes per VD (written as target roll × previous-LGE votes ÷ target roll, `:270-280`) | – | canonical | raw; **does not honour HELD_BACK** | 8 |
| Interactive data pack (off) | `export_interactive.py` `:139-190` | literal `npe2024`, `lge2021`, `vd_ward_2026`, `turnout_2026_*`, years 2011–2024, `fold1` | as model | crosswalk | crosswalk | – | canonical | `interactive_data.json` | JHB 2026 by construction |
| Interactive draw file | `export_draws.py` | `run_model` for the city and target; the index reads `data/processed/byelection_party_deltas.csv` whatever the city (`:676`) | – | – | – | – | canonical | `base.bin`, `manifest.json`, `index.json` | any; by-election index JHB |

## 2. Inconsistencies, most consequential first

### 1. The pre-2011 quarantine is honoured by three readers and ignored by four

`levels.HELD_BACK` withholds `lge2000` and `npe1999` for seven metros so that
"the effect being diagnosed is the effect being measured" (`pools.py:1190-1212`
comment). It is checked in `levels._citywide` (`levels.py:305`),
`pools._npe_citywide_state` (`pools.py:4032`) and `pools.ward_totals`
(`pools.py:1207`). A grep for `_held_back|HELD_BACK` returns **zero** hits in
`turnout.py`, `fold.py`, `benchmarks.py`, `build_concordance.py`,
`gamma_recent.py`, `byelections.py` and `width_record.py` (**measured**).

What reads the quarantined files anyway:

- `turnout.py`: the 2011 turnout files for Tshwane and Cape Town carry
  `turnout_1999`, `turnout_2000` and `lambda_2000` (**measured**, CSV headers),
  so λ̂ for every 2011 row of the seven is `0.7·λ_2006 + 0.3·λ_2000`.
- `fold.py`: fold 4 (the γ for every 2011 target) defaults to `--turnout level`,
  which weights VDs by the `prior_lge` "2000" turnout pattern
  (`fold.py:79`, `:356-368`). Fold 4 files are dated 1 Sep, after the 2000
  ingest.
- `benchmarks.py`: at T = 2011, `earlier_lge` is 2000 (`sources_for` `:109-110`),
  read by `prior-lge-noise`.
- `build_concordance.py`: `ELECTIONS` starts at 1999 (`:75`). Its concordance
  is read by the model only at `fold.py:503`, under a non-default flag, so this
  one is dormant.

`gamma_recent.py` and `byelections.py` also have no gate but never reach 2000 or
1999 at any target; `width_record.py` reaches them through `levels` and is gated.

**Why it matters.** The seven metros' 2011 rows are a model whose levels never
saw 2000 and whose turnout, γ and one benchmark did. The 13.65 CRPS regime
effect the quarantine waits on (`levels.py:225-275`) compares runs with and
without the gate in the three honouring readers. If `turnout.csv`, the fold 4
files and the benchmark context were the same in both arms (*inferred*: they are
built by separate commands and the gate does not reach them), that figure
measures withholding 2000 from θ, ρ and the pool records only; whatever 2000
contributes through λ, γ and `prior-lge-noise` is present on both sides.

### 2. Seven consumers read six different rolls

| consumer | roll |
|---|---|
| backtest pools and draw (`_target_roll` → `ward_totals`; `ward_parts`) | the target's own result file, whole VD, target delimitation |
| JHB 2026 pools and draw (`read_ward_crosswalk`) | IEC ward snapshot 2026-09-26, each VD wholly in one ward by a solver assignment |
| TSH 2026 pools and draw | MDB `REGPOP` (2024), split VDs apportioned by `WardPop`; the 2026-09-29 snapshot is in `archive/` and unused (**measured**: no `part_registered_2026` column, file dated 1 Sep) |
| `turnout.py` projection weights | the previous NPE's per-VD roll (`registered_2024`, `registered_2019`, …) |
| `byelections.py` turnout | the previous LGE's ward roll |
| `benchmarks.build_context` | the target's roll |
| `polling.NATIONAL_VOTES` | IEC national roll × turnout from Wikipedia |

**Why it matters.** A backtest is scored on the certified election-day roll; the
forecast uses a September snapshot (JHB) or a 2024 roll (TSH), so the backtest
never exercises the roll the forecast relies on. Within one 2026 run, turnout.py
weights its citywide λ̂ level by one roll and `run_model` rescales VD patterns by
another (`:6749-6752`). Split VDs are whole in backtests (the result files name
one ward per VD) and at JHB 2026 (the solver assignment, JUDGEMENT-CALLS §T1),
and apportioned by `WardPop` at TSH 2026.

### 3. Two turnout models, defined differently, feed one run

- **Pool turnout** (`pools.turnout_record`, `turnout_band`): PR valid votes over
  the roll, per census pool, every LGE < T, centred on the last LGE, widened by a
  panel-wide spread. Written into the spec as `turnout: [lo, mid, hi]`.
- **VD turnout** (`turnout.py`): valid + spoilt on the higher ballot over the
  roll, per VD, λ from the last two LGE/NPE pairs applied to the previous NPE's
  turnout. Read by `run_model` from `turnout.csv`.
- `run_model`'s high/low anchors take only elections from 2011 (`:6705`); the
  pool record and turnout.py take everything < T.
- A third and fourth definition: `benchmarks` (previous-LGE PR valid votes
  divided by the **target's** roll, a ratio across two rolls, then multiplied by
  that roll again, so the weight is the previous LGE's votes; `build_context`
  `:270-280`) and `byelections` (by-election valid votes, and previous-LGE ward
  valid votes, each divided by the previous-LGE ward roll).

**Why it matters.** The four definitions differ in ballot (PR, higher of two,
ward), in whether spoilt ballots count, in which roll divides, and in window
(every LGE < T; the last two λ pairs; ≥ 2011). How the pool and VD turnouts
combine inside a draw was not traced (section 3), so which one decides a given
seat is not stated here.

### 4. Census 2022 is used for every backtest, and two NPEs cannot be joined to it

Every pool spec splits the roll with Census 2022 shares on the 2021 wards,
reprojected through VD numbers. That census postdates the 2011, 2016 and 2021
targets; for T = 2011 the composition is applied to the 2006 fitting election,
16 years before the census.

`pools.vd_map` (`:1529`) skips rows with a blank `Ward`, and NPE 2004, 2019 and
2024 carry none: `vd_map(joburg, y)` returns 0 VDs for 2004, 2019 and 2024,
against 759 for 2009 and 825 for 2014 (**measured**). `pools._ward_resolver`
(`:1140`) fills the same blanks from the preceding LGE, but only `ward_totals`
and `ward_party_shares` use it. So:

- `_reprojection_drift` is unmeasurable at 2004 and 2019 and `pool_counts`
  refuses them;
- `national_fits` refuses at every 2021 target (`national_fit_refused`:
  "the 2019 composition is unsafe to fit (census_drift_unmeasurable)",
  **measured** in joburg, tshwane, capetown `pools_2021.json`);
- the rule "a party with its own national record is fitted on it", which places
  MK, BOSA and RISE at JHB 2026, is exercised at the 2011 and 2016 backtests and
  never at 2021.

**Why it matters.** The backtest cycle nearest the forecast cannot test the
placement rule the forecast leans on, and the cause is a second VD→ward resolver,
not missing data.

### 5. γ is two cycles old in the forecast and one cycle old in every backtest

`GAMMA_FOLD = {"2026": 1, "2021": 1, "2016": 3, "2011": 4}`
(`montecarlo.py:1183`). Each backtest takes the transition one cycle back; 2026
takes 2014→2016 although 2019→2021 (fold 2) exists for JHB and TSH. Registered
as contestable (`JUDGEMENT-CALLS.md:130`). Further:

- JHB's `fold1_parameters.csv` is dated 13 Aug; every other city's fold 1 is
  dated 10 Sep (**measured**, `ls`). Different code vintages are *inferred*.
- `gamma_recent.csv` exists for JHB 2011/16/21/26 and TSH 2021 only
  (**measured**). In the other six metros, and at TSH 2011, 2016 and 2026, a
  party with no fold γ takes 1.0 rather than the recent fit.
- `gamma_recent` fits LGE→NPE and is applied NPE→LGE (its own docstring).

**Why it matters.** The γ the forecast uses is not the γ any backtest row scored,
and the γ fallback differs by metro.

### 6. "National" in the code is the provincial ballot

θ, the baseline, `national_fits`, the arrival definition, the VD turnout level
and `gamma_recent` all read the NPE files, which hold the provincial ballot. A
grep for "provincial" in `levels.py`, `pools.py` and `montecarlo.py` returns
0 hits; "national ballot / vote / share" appears 9, 10 and 11 times (**measured**).
`bye_value.py` labels its outcome "the 2024 provincial ballot" correctly.
`polling.metro_estimate` divides a national poll number by a contested share
built from LGE PR votes (*inferred* that polls report national-ballot
intention). INVENTORY item 5 records a provincial figure quoted as a national
one.

**Why it matters.** The two ballots differ by party (they are separate votes);
every retention ratio is a provincial→local ratio described as national→local,
and a poll on the national ballot would be converted against the wrong base.
Polls are off, so the conversion is latent.

### 7. By-election evidence exists for one city-year

`byelections.main` reads `byelections_Gauteng_vd_party.csv` only
(`byelections.py:346-348`), so five metros can never have a delta. Its outputs
exist only in `data/processed/` (JHB 2026) (**measured**, `find`); no backtest
target and not TSH 2026 has any. So `w_bye`, the κ turnout tilt and the local
ward term act only at JHB 2026, and no backtest row scores them. `bye_value.py`
reads the national SA file instead, and the 2016–21 file is read by no live
module. The `w_bye = 0.5` it replaced was set from off-panel audits on that
2016–21 file (MACHINERY §2). By-election turnout uses valid votes over the
previous LGE's roll although the IEC files carry `RegisteredVoters` and
`TotalVotesCast` (INVENTORY, checked item). `run_model` reads a literal
`share_2021` column (`:6628`) where `byelections.py` writes `share_<base_lge>`.

### 8. Two windows for "turnout history", "party history" and "width history"

| record | window at T |
|---|---|
| θ, ρ, pool turnout, arrival and splinter records | every election < T, from 2000 (JHB) / 2006 (others) |
| pool α | 2011–2021 only (`metro_citywide`) |
| arrival reach (`_ward_reach`) | 2011–2021 only; empty for 2000/2006 transitions |
| VD turnout λ | last two LGE/NPE pairs |
| turnout anchors in `run_model` | ≥ 2011 |
| group-share tripwire | 2011, 2016, 2021 |
| width record | 2011 onward; 2011 itself from a 2006 θ residual that, under HELD_BACK, is JHB-only (*inferred*) |
| level shrink | chosen on JHB 2016 and the 2021 panel: in-sample for those rows |

The arrival record counts 2000/2006 metro-years while the reach that splits
arrivals cannot see them. The 2016 width rests on one earlier cycle.

### 9. The benchmarks do not weight the city the way the model does

`benchmarks.py:270-272` says its VD weight is "the same weighting
montecarlo.run_model applies". It is `target roll × (previous-LGE PR valid
votes ÷ target roll)`, which cancels to the previous LGE's PR valid votes in each
VD (the median ratio where a VD is new, floor 1). `run_model` uses `turnout.csv`
(higher ballot, valid + spoilt, λ̂ on the previous NPE) rescaled to λ̂. The benchmarks also read the
quarantined `lge2000` at T = 2011 (item 1). The margin over uniform swing is
therefore taken against an opponent on different turnout inputs.

### 10. Two sources for "how many wards a party contests"

`levels.contestation` / `ballots` (target result file, else declared slates,
else projection) drives the ward mask and ward/PR change. `pools._ward_reach`
drives arrival split weights from `_metros/`/`_reports/` files, and at 2026 falls
back to the 2021 ward ballot plus declared reach (`emit_pools` `:6292-6301`; JHB
2026 spec: "2021 ward ballot, carried forward unchanged; 80 declared"). For an
undeclared party at 2026 the two disagree by construction.

### 11. The draw drops VDs the previous NPE did not have

The draw's VD universe is the previous NPE file (`run_model` `:6064`); a ward
part enters the tally only if its VD is in that file and has registration
(`:6788`). The pools are sized from the target's whole roll. A VD created
between the NPE and T counts in the pool sizes and not in the ward tallies
(read; the number of such VDs per city-year was not counted).

### 12. Tshwane 2026 is built from a different input class from Johannesburg 2026

| input | JHB 2026 | TSH 2026 |
|---|---|---|
| roll | 2026-09-26 snapshot | 2024 REGPOP; 2026-09-29 snapshot unused |
| roster in the spec | declared | projected; the judgement file was edited 21 Oct with the certified list (its comment: entered 2026-10-22), the spec dated 17 Oct (**measured**, `ls` and spec field) |
| γ fallback | `gamma_recent.csv` | none |
| by-elections | yes | none |
| owner calls | MK, ASA | none |

A stale `judgements_sha` should stop a TSH 2026 run (*inferred*; not run).

### 13. Hard-coded Johannesburg paths in city-general code

- `fold.py:503` reads `data/processed/vd_concordance.csv` for every city. At the
  default `--stability all` it only sets a printed count, so no default fold
  moves.
- `export_draws.py:676` reads JHB's `byelection_party_deltas.csv` for any city.
- `export_interactive.py:139-190` hard-codes 2024, 2021, 2026 and fold 1 (off by
  design).

### 14. Backtest polls read the target's own turnout

At a held target `polling.contested_share` divides by `votes_by_metro(year)`,
the target year's votes cast, and `NATIONAL_VOTES[year]`, the target's national
turnout (`polling.py:1000-1037`). At 2026 it uses the 2021 share. Under
`poll_paths = "arrivals"` or `"all"` a backtest would carry outcome information
the forecast cannot have. Off by default.

### 15. The statute applied to the draws is not the one the truth was counted under

Draws use `overhang_rule = "deduct"` for every year (`montecarlo.py:384`);
the 2011 and 2016 councils were seated under the pre-2021 rule. The truth is
rebuilt with `seats.allocate` and asserted against the IEC
(`backtest.py:1073-1110`). Known (MACHINERY §6, "anachronistic").

### 16. Three readers for one citywide share; no difference found

`levels._citywide` (clean files), `pools.metro_citywide` (`_metros/` 2021,
`_reports/` 2011–2016) and `pools._npe_citywide_state` (clean files). For JHB,
TSH, CPT and BUF at 2011, 2016 and 2021 the first two agree exactly (max
absolute difference 0, same party keys; **measured**). Not checked for EKU, ETH,
MAN, NMA. Consequence: maintenance only, on this evidence.

### 17. Party identity: one mapping in use, one report nobody reads

Every model reader uses `parties.canonical`. `data/processed/party_crosswalk.csv`
(`build_crosswalk.py`, elections 2011–2024 only) is read by nothing in the model
(`archive.py` lists it). By-elections key on `PartyFullName`; result files on
`sPartyName`, which holds full names (**measured**, file headers). Empty party
names in by-election files (INVENTORY item 3) go through `canonical("")`; what
code that yields was not checked.

## 3. What could not be determined

| question | why not |
|---|---|
| How pool turnout (spec) and VD turnout (`turnout.csv`) combine in a draw, and which decides seats | `draw_pools` / `make_drawer` not traced; no run allowed |
| Numerical effect of items 1, 2, 3, 5, 9 and 11 | needs model runs or `compare_history`; barred while the suite runs |
| Whether the 2011 width fallback is Johannesburg-only | `theta_residual.residuals` not read; inferred from `theta_record` and HELD_BACK |
| Whether TSH 2026 refuses on a stale `judgements_sha` | not run |
| Whether `inputs_preflight --strict` passes for TSH 2026 | not run |
| Which ballot the poll numbers report | `polls.json` records not read |
| Whether `_metros/` / `_reports/` agree with the clean files in EKU, ETH, MAN, NMA | only four metros compared |
| How many target VDs are absent from the previous NPE per city-year (item 11) | not counted |
| Whether the IEC roll pages' 862 (JHB) and 796 (TSH) VDs against the crosswalks' 865 and 774 reach a live number | INVENTORY item 6; not reconciled here |
| Which canonical code empty party names receive | not checked |
| Whether fold files of different dates were built from different code | file dates only |
