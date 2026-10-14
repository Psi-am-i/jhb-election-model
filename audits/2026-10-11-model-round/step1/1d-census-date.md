# 1d. Census vintage in the backtest

Read-only investigation, 2026-10-11, branch `remediation`. Nothing was run except key-reading of emitted specs. "Measured" means read directly from a file or code in this tree; "argued" means reasoned, not computed.

## Summary of findings

* Census 2022 is the only census the model holds and reads, for every target (2011, 2016, 2021, 2026) and every city. There is no year switch (measured, §2).
* The census supplies pool composition (population-group shares per ward) and head counts (people, adults). The roll and results supply levels.
* The 2022 census is held flat across 5 to 16 years. The interpolation branch that would use a second census never executes (measured, §1).
* Census 2011 on 2011 wards is not held. The commented-out stub in `config/dimensions.toml:77-85` marks the slot. It is probably fetchable from Stats SA SuperWEB2 (argued from SOURCES.md; not tested).
* The leak is a covariate-not-outcome leak, already declared in `src/backtest.py:213-217` and `src/build_validation.py:318-322`. It is not mentioned in the specs themselves. Argued direction: it flatters the 2011 and 2016 backtests most (§5).

## 1. Where census data enters

Config: `config/dimensions.toml:46` sets `covariate_root`. Three dimensions each declare exactly one census, all `year = 2022, delimitation = 2021`:

| dimension | role | admitted | file / sheet | toml line |
|---|---|---|---|---|
| population_group | base | true | `PP_Population Group_27-10-2025.xlsx` / `Wards` | 50-85 |
| age | tilt | false | `PP_Age Group_27-10-2025.xlsx` / `Age_group` | 101-108 |
| sex | tilt | false | `PP_Sex_27-10-2025.xlsx` / `Wards_Sex` | 122-129 |

Readers in `src/pools.py`:

| reader | file:line | produces | consumed by |
|---|---|---|---|
| `load_config` (builds `Census` objects) | 155-162, 590-602 | per-dimension census list; refuses a dimension with none | everything below |
| `read_census(dim, census, cfg)` | 626-660 | ward -> composition (shares over the four groups, "Other" dropped) | `composition_at`, `drift` check |
| `read_census_population(census, cfg)` | 662-695 | ward -> head count (people; adults for the age table) | `pool_counts` |
| `composition_at(dim, cfg, when, ...)` | 2064-2170 | composition at a decimal year; with one census returns it unchanged ("held flat", line 2127) | `pool_counts` (1287) |
| `pool_counts(city, year, cfg)` | 1258-1580 | the nested levels people -> adults -> registered -> voted per ward x pool; rates `adult_share`, `registration`, `turnout`, `census_correction` | `emit_pools` (3238), `turnout_record` (2867), `montecarlo.py:4485` |
| `reproject` / `reproject_counts` | 1837-1873 / 2006-2065 | move the 2022 shares (and counts) from the 2021 wards onto the fitting election's wards via VDs | `composition_at` 2099, `pool_counts` 1311-1345 |
| census drift / coverage guards | 1904-1915, 1946-2000, 1380-1440 | refusals when the join is unsafe | `pool_counts` |
| `REGISTRATION_MAX = 2.0` | 914, 1495-1500 | census-derived ceiling on registered/adults | `_nest_holding_silent` |
| `rates["census_correction"]` | 1510 | registered / adults, reported not consumed | report only |

Other `src/` hits: `montecarlo.py:4364-4500` consumes the emitted spec and re-calls `pool_counts` for `_vd_pool_composition` (pool geography at the fitting year). `backtest.py:213-217` and `build_validation.py:194, 318-322` declare the post-dating. `build_site.py:251` credits Stats SA. `levels.py`, `archive.py`, `build_play.py`, `compare_history.py` mention the census only in comments (measured by grep).

Quantities the census determines downstream (argued from `pool_counts` docstring, 1258-1280, and DATA-QUALITY §11, lines 218-236): the split of each ward's counted registration and votes across the four pools. Each ward is forced to its published totals by `_nest`, so levels are counted and only the split is census-driven. The split feeds the party-by-pool membership weights (`pools[...]["members"]`), the per-pool turnout record, `adult_share` and `registration` rates, and the pool geography.

Standing rule, DATA-QUALITY.md:218-236: registration and votes outrank the census; the census is the apportionment key and a soft ceiling.

Unexercised code: the two-census interpolation (`pools.py:2138-2170`, `_LOG_FLOOR` at 1895) is documented as never executing (JUDGEMENT-CALLS.md:94, 647-649; comment at pools.py:1876-1894). Measured by the config: every dimension has one census.

## 2. Census vintage per target year

Measured from code: there is no year switch. `composition_at` iterates `dim.censuses` (2083) and every dimension has one entry. `delimitation_for(year)` (1916-1925) picks only the election's ward delimitation, to decide whether to reproject (2091), not which census.

What each backtest target actually reads, from the spec provenance strings (`data/processed/**/pools_*.json`, key `provenance`) and `pool_counts(city, spec["fitted_on"])`:

| target | pool counts fitted at | spec `provenance` (measured) | census used | gap from the fitting year to Census 2022 |
|---|---|---|---|---|
| 2011 | 2006 | "nested pool counts from 2006; pools sized by 2009 roll carried to 2011 ..." | 2022, held flat, reprojected 2021 wards -> 2006 wards | about 16 years |
| 2016 | 2011 | "... from 2011 ..." | 2022, reprojected 2021 -> 2011 wards | about 11 years |
| 2021 | 2016 | "... from 2016 ..." | 2022, reprojected 2021 -> 2016 wards | about 6 years |
| 2026 | 2021 | "... from 2021 ..." | 2022 | about 1 year (legitimate; census pre-dates the forecast) |

The same pattern holds in all eight metro directories (24 backtest specs checked by provenance string). The specs carry no census provenance of their own: `artefact_key` holds only hashes (`config_sha`, `pools_sha`, ...) and no spec contains the string "Census" (measured: regex over each file). So the vintage is recoverable only from code and config, not from the artefact.

Earlier fitting years also read the 2022 census. `turnout_record` (pools.py:2840-2880) calls `pool_counts` for every prior election before the target, so 2000, 2004, 2006 and so on are all nested on Census 2022 too (code reading; not run).

## 3. Census data held locally

| path | vintage | geography | variables | status |
|---|---|---|---|---|
| `data/raw/covariates/Ward Product_Locked spreadsheets/PP_Population Group_27-10-2025.xlsx` | 2022 | ward (2021 delimitation; national, about 4,470 wards) | population group | read by the model |
| same dir, `PP_Age Group_...xlsx`, `PP_Sex_...xlsx` | 2022 | ward (2021 delimitation) | age band, sex | read; dimensions rejected by the gate |
| `data/raw/covariates/Ward-Product_Locked-spreadsheets.zip`, `Ward-statistical-product-technical-note.pdf` | 2022 | ward | same | source archive and note |
| `data/raw/covariates/Languages by Municipalities Census 2022.xls` and a copy under `new data from statsSA/` | 2022 | local municipality | home language | not read by any model code (grep: no reader) |
| `new data from statsSA/*.inetloc` | 2022 | n/a | mail links to Stats SA correspondence | pointers only |

Measured: `find` for census files returns only the 2022 files above. No Census 2001 or 2011 data file is held.

Geometry held that matters for a join: `data/raw/geo/wards2011_{JHB,TSH}.geojson`, `wards2011_SA.gdb.zip`, `wards2016_*`, `wards2020_*` (the 2021 wards), `wards2026_*`. The 2011 ward geodatabase is national (SOURCES.md:553 area, "the 2011 and 2016 ward geodatabases were already national").

Not held, per SOURCES.md:
* Census 2011 ward tables (population group). SOURCES.md:515-518 says Census 2011 is available by electoral ward through SuperWEB2 (`superweb.statssa.gov.za/webapi`, Community Profiles -> Census 2011 -> Descriptive -> "South Africa by Electoral Ward"), with Language among the indicator groups. Reported in the Stats SA correspondence (drafts/statssa-reply-2026-08-26.md:41), not tested here. Population group is a standard Community Profiles variable, argued but unverified for this geography.
* Census 2011 Small Area Layer (SAL), EA, main place, sub place: geometry that Stats SA will supply, no variables attached (SOURCES.md:504-510). UIS can advise which 2011 variables exist at SAL (reported, not verified).
* Census 2001: no mention of a held file. Not examined for availability.
* Census 2022 SAL does not exist (Stats SA, 2026-08-27, quoted at SOURCES.md:476-490). DATA-QUALITY.md:208-212 §15 still says "request-only", and SOURCES.md corrects that. The two documents disagree; SOURCES.md is the later entry.

## 4. Mapping census geography to election wards and VDs

Mechanism (measured from code):
1. Census 2022 rows are keyed by an 8-digit ward code (pools.py:651 filter). They are on the 2021 delimitation (toml `delimitation = 2021`).
2. `composition_at` compares `census.delimitation` with `delimitation_for(election_year)` (2091). If different, `reproject` (1837-1873) goes through voting districts. `vd_map(city, year)` (pool code) maps each VD to its ward for that election's file. Each old-ward composition is pushed to its VDs and pulled into the new wards, weighted by registered voters. `reproject_counts` (2006-2065) does the same for head counts by splitting in proportion to registration.
3. Ward codes are contiguous and reused, so a code join across delimitations succeeds wrongly. Joburg's 135 census codes match the 2011 election's 130 wards at 130/130, all the wrong polygons (pools.py:34-36; toml:36-39). The trigger is the delimitation, not an empty overlap (pools.py:1296-1311 comment).
4. Guards: coverage (`CENSUS_COVERAGE_FLOOR = 0.80`, 1904, reported not refused at the census read), drift ceiling (`CENSUS_DRIFT_CEILING = 0.05`, 1910), and a refusal when no ward joins (1429-1440). Measured coverage runs 87.0% (Joburg 2006) to 72.5% (Mangaung 2006) per the comment at 1900-1904.
5. Split VDs: Joburg has 1,059 VD-ward rows for 865 VDs (CLAUDE.md §4b); `montecarlo.ward_parts` is the join for them. This is a separate question from the census reprojection above, which uses `vd_map`.

Could a Census 2011 be joined for 2011 and 2016 targets? Argued yes, with a caveat for each:
* 2011 election wards and Census 2011 electoral wards share the 2011 delimitation (`wards2011_*` held). The toml stub at lines 77-85 already declares `delimitation = 2011`. For a 2011 target, `pool_counts` is called at fitting year 2006 (2006 wards, delimitation 2006). So Census 2011 would be reprojected 2011 -> 2006 wards via VDs, the same operation already run for 2022 -> 2006 today. The existing code would take a 2011 entry with no new code: `composition_at` reprojects any census whose delimitation differs (2091), and `pool_counts` gates the base and age dimensions separately (1311, 1341, §1.195).
* The age dimension is a tilt, not admitted, and does not enter the party fit. It does enter `adults_by_ward` (1291) and so `adult_share`. If only the base dimension gains a 2011 entry, the age table stays 2022. That mismatch is exactly the case the §1.195 code was written for (toml and pools.py comments 1331-1345).
* Timing: Census 2011 was enumerated in October 2011 (general knowledge, not in the repo), five months after the 18 May 2011 election (`cityconfig.py:105`). It is clean for a 2016 target and for 2021, and only approximately clean for 2011. A strictly pre-election source for 2011 and 2016-fitted-2006 is Census 2001 (October 2001), on 2000 wards. Whether it is published by ward in a usable form was not examined.
* With two censuses held (2011 and 2022), the interpolation branch becomes live for the first time (`pools.py:2138`). For a 2016 target a strict backtest must exclude the 2022 entry. The code has no "censuses available at date" filter, so using both would re-leak for 2016 and 2021 (the 2021 gap, 2011 -> 2022, interpolates toward 2022).

## 5. Expected direction and size (argued, not measured)

Model quantities that would change: the party-by-pool membership weights and `identified` flags (`pools[...]` in each spec), the per-pool registered and turnout shares, the per-pool turnout record in `turnout_limits`, `adult_share`, `registration` and `turnout` rates, `rates_on_a_bound`, and the pool geography `_vd_pool_composition`. The roll and vote totals do not change (each ward is forced to its published totals).

Which city-years: all 24 non-2026 specs and everything fitted on earlier years. The effect should be largest where composition moved most between the fitting year and 2022: the 2011 target (16-year gap, fitted at 2006) and then 2016 (11 years), smallest at 2021 (6 years).

Evidence of size, reported from the MODEL-LOG, not re-measured:
* MODEL-LOG, "The owner's three observations" (line 11979): Census 2011 put Joburg's white share at 12.3% against 7.0% in Census 2022, a 43% relative fall while the city's population barely moved. A census-2022 composition applied to 2006-2016 wards understates the white pool then by that order.
* MODEL-LOG, "Buffalo City's registration split" (line 26853): the emitted `pools_2011.json` carries the White pool at 6.3% of the roll, the 2006 fit value, against 10.6 / 12.3 / 12.5 in 2011-2021. The log says 2006 at 5.51% is the outlier. It names two mechanisms it could not separate, one of them the census interpolation at 2006. Taken with this audit, the 2022 hold-flat is a third candidate.
* MODEL-LOG line 26914 (Cape Town): the Indian/Asian pool is 8.3-10.0% of the roll in the specs against 1.61% of Census 2022 population. Black African reads 33.0-33.8% in the specs against 46.35% in the census. The fitted pools do not track the census composition, so the census gives direction (which wards are more white) rather than magnitude.
* MODEL-LOG line 18705: reprojection preserves tails; it does not flatten (measured there at the four-decimal level).

Direction, argued: a post-dated census usually flatters the backtest, but here the sign is not a given. The reasons:
* The census says who lives in a ward and not how they voted, as `backtest.py:213-217` argues. It enters as a covariate to decompose votes already cast. Using later ward composition to decompose earlier votes can attenuate or distort the fitted party-by-pool weights where composition moved (white to non-white ward change, 43% in the Joburg white share above), which would worsen the backtest.
* It can also flatter. The decomposition is estimated on the fitting election and applied to the target. If a ward's 2022 composition correlates with its later-vote direction beyond what the 2006-2016 composition would have told, the shares at the target are decomposed with hindsight. This route is plausible for wards that changed fast (informal settlement growth, Joburg north infill). The size is unknown.
* Because every ward is forced to its published totals (`_nest`), the leak acts only on the split. Total votes and seats cannot be moved directly by it. The seat effect passes through party-by-ward sorting, so the seat-score impact is probably smaller than the pool-level impact.

My ranking is that the effect is real, pool-level, and biggest at the 2011 target, with a sign that a measurement must settle. The claim "flatters" has no measurement under it. The honest wording is the one in `build_validation.py:318-322` ("information from after the fact, and is declared as such"), which does not claim a size.

What would settle size and sign: the same panel run with a 2011 census at 2016 and 2021 targets (see §6). 2011 as a target is not clean even then.

## 6. Effort and the cheapest honest alternative

Fix with Census 2011 (a data step plus a small code step):
1. Acquire Census 2011 population group, age and sex by ward on 2011 wards, from SuperWEB2 (Stats SA, Community Profiles -> Census 2011 -> "South Africa by Electoral Ward"; SOURCES.md:515-518; not fetched). Needs a browser per the project's IEC experience; whether SuperWEB2 exports ward cross-tabs of population group by age is unverified. Alternatives to name: Stats SA's "Census 2011 Municipal Fact Sheet" and Community Profile downloads, and Wazimap (SOURCES.md:520 says Wazimap-NG was unreachable when tried).
2. Add `[[dimension.census]] year = 2011, delimitation = 2011` entries (toml:77-85 stub; one each for population_group, age, sex) and put the files under `data/raw/covariates/`.
3. Add a date filter so a backtest target only sees censuses enumerated before it (new, about 10 lines in `composition_at` near pools.py:2083, plus the same in `pool_counts` where it picks `base.censuses[-1]` at 1289, 1291, 1311, 1341 and in `drift` at 1976-1977). Today `censuses[-1]` is always the latest, which would silently pick 2022 again for every target. This is the main code risk: the tests for the two-census path do not exist, since the branch is declared unexercised (JUDGEMENT-CALLS.md:647), so it needs the four-part absence-test treatment in CLAUDE.md §4.
4. Re-emit all pool specs (POOLS-REEMIT-QUEUE.md; a `pools.py` code change invalidates every spec), under the one-writer rule (CLAUDE.md §3), then re-measure with `compare_history` once on a settled tree. Per CLAUDE.md §4, pre-register what is expected before the run, and record in MODEL-LOG; update MACHINERY.md:42 and :183, `backtest.py:213-217`, the `build_validation.py` text, and the toml header.
5. Check the census join guards on the 2011 data: the coverage floor, the drift ceiling, and the `REGISTRATION_MAX` binding cells (DATA-QUALITY §11).

Order of magnitude (my estimate, not measured): one data-acquisition session, a day of code and tests, one full re-emit and measurement.

Residual even after the fix: the 2011 target would still use Census 2011 (October 2011, after the May election) or, for strictness, Census 2001. A fully clean 2011 target needs Census 2001 ward tables on 2000 wards, which were not examined.

Cheapest honest alternatives, in rising cost:
* **Declare the limit** (no code, no re-emit). The limit is already declared at `backtest.py:213-217` (pools banner) and `build_validation.py:194, 318-322`. Extend it to say the census is held flat from 2022 across a 6 to 16 year gap, that Census 2011 exists but is not held, and that no sensitivity was run. Note that the validation text says the census "cannot leak a result" while the banner says it is information from after the fact; both are true and compatible, but a reader should be told the magnitude is untested.
* **Sensitivity check at the 2021 target only** (cheap: the 2021 target has the shortest gap, so a null there is weak evidence about 2011). Not recommended as the single check.
* **A 2016-and-2021 sensitivity with Census 2011 only** (data step plus the date filter in step 3, one re-emit of 16 specs). This gives a measured sign and size on the cycle where Census 2011 is clean, without needing Census 2001. 2011 stays declared.
* **A placebo within the existing data**: fit pool composition with the 2022 table shuffled across wards within a delimitation (argued as a lower bound on how much composition information the fit uses). It does not answer the leak question directly, so the 2011-census run above is preferred.

Everything above in §5-6 about size, sign and effort is argued, not measured.
