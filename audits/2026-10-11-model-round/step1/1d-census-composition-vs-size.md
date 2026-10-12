# 1d (follow-up). Census: composition only, or also size?

Read-only, 2026-10-11. Rule under test (owner): the census supplies ward COMPOSITION only; SIZE comes from the roll (registered) and results (votes). "Measured" = read in code or an emitted file; "argued" = reasoned, not run. Census reads are those listed in `1d-census-date.md` §1 plus a fresh grep of `src/` for census, people_by_ward, adults_by_ward, census_correction, ceiling, cap, extrapolat.

## Verdict

The rule is not applied uniformly. Ward totals are forced to the roll and to results (`_nest` rescales every ward row, pools.py:930-934), so the level of registered and voted per ward is not census-derived. The census head counts (`people`, `adults`) do enter the pool split through the fitted rates, and a census-derived ceiling clips those rates. No census figure reaches a draw as a count directly; it reaches draws as the registered-level split, the turnout record and the pool capacity.

## Table

| read site | quantity | composition or size | roll alternative for the same unit and year | effect |
|---|---|---|---|---|
| pools.py:626-660 `read_census`; 2083, 1287 `composition_at` | ward shares over the 4 groups | (a) composition | n/a (roll has no population group, DATA-QUALITY §11, 218-231) | sets `people` shares; back-dated from 2022 for every pre-2026 fitting year |
| pools.py:1289 `read_census_population(base)`, applied at 1467 `people = comp * pop` | ward head count of people, multiplied onto the shares | (b) size, in magnitude only | `reg_by_ward` (1252-1255, roll) exists for each unit and year, but gives no group split | `people_wg` is the parent of the adult and registration solves (1498). Ward totals cancel in the within-ward split (row rescale), but the ward-to-ward relative size is the weight in the rate fits below |
| pools.py:1291, 1340-1344, 1480-1483 `adults_by_ward` -> `observed_adults` -> `_nest_holding_silent(people, observed_adults)` | ward adult count (age table, 20+ approximated) and the fitted `adult_share` per pool | (b) size | roll is already adults who registered, so adults is not needed to size anything the model draws | `voting_age` ward totals equal the census adults. `adult_share` is fitted and bound at 1.0. Pool bounds bind here (§1.164, line 946: 1.30 and 2.06 before the bound). Not admitted as a dimension (toml:97), but this read is live: it is the denominator of the registration fit |
| pools.py:1497-1500 `registered = _nest(voting_age, reg_by_ward, upper=REGISTRATION_MAX)` | pool split of the counted roll, and the `registration` rate per pool | split is (a)-like; the rate is (b) | the ward totals ARE the roll; the split across pools is not available from the roll | the ward total is exact. The split per pool is set by `people_wg x adult_share_g x registration_g`, so a census adult count that is wrong for one group moves registered voters between pools within a ward |
| pools.py:914 `REGISTRATION_MAX = 2.0`, used 1500, 1541 | ceiling on registered per census adult | (b) a census-derived ceiling on a counted quantity | roll is the count | binds on four cells in two cities (pools.py:899-911; DATA-QUALITY.md:243-250): Cape Town Indian/Asian 2011 and 2016, Mangaung Indian/Asian 2016 and 2021. Where it binds, the census overrules the roll and `_nest`'s row scaling pushes the surplus into the other pools of the ward. Value recorded as "deferred, not defended" (§L9) |
| pools.py:1508-1510 `rates["census_correction"]` | registered / census adults | (b) diagnostic | roll is the numerator | report only; no consumer found in `src/` outside pools.py (grep: no other file reads it) |
| pools.py:1566-1580 `violations` | registered > adults, voted > registered | (b) diagnostic | roll | report only; message states the roll outranks the census |
| pools.py:1521-1547 `unidentified` | pools on a bound at each level | (b) diagnostic | n/a | listed in the spec as `rates_on_a_bound`; no draw effect |
| pools.py:1585-1590 `PoolCounts`, via `registered_at_target` (3238-3335) | `composition("registered")` x target roll = pool size at target | the split is (a); the product is size from the roll | the roll supplies the size | the capacity of each pool in the spec (`registered`) is roll x a census-influenced split; this is where census enters pool capacity |
| pools.py:2840-2880 `turnout_record` -> `pool_counts` per prior election, `rates["turnout"]` | per-pool turnout (voted / registered) at every prior election | (b) size (turnout base) | votes cast and registered per ward are counted; per-pool turnout cannot be read from them | per-pool turnout is fitted on the census-influenced `registered` split. Back-dated: every prior election in the record is nested on Census 2022. It reaches the `turnout` triple (`pools[...]["turnout"]`, the spec's `turnout_limits`) and so the vote total each pool casts in every draw |
| montecarlo.py:4485 `pool_counts(spec["fitted_on"])` -> `_vd_pool_composition` | VD-level pool shares at the fitting year | (a) composition | n/a | pool geography |
| pools.py:1976-1977 drift check; 1380-1440 coverage and match guards; 2044-2065 `reproject_counts` denominators | census people as weights and denominators for a coverage fraction | (b) guard weights | n/a | refusal and admission only (`CENSUS_COVERAGE_FLOOR`, `CENSUS_DRIFT_CEILING`, 50% match). Can remove a city-year from the panel; does not size a pool |
| pools.py:2064-2170 extrapolation (`damping`, `max_extrapolation`, toml:47-48) | composition drift beyond the last census | (a) composition | n/a | with one census the code holds flat and only prints a note when beyond 8 years (2116-2127: "composition only, pool sizes still come from the roll"). The 2011-target gap is about 16 years, past that guide |
| pools.py:2006-2065 `reproject_counts` | splits census counts across VDs by registration, onto the fitting wards | (b) size transported by roll weights | roll | areal interpolation; error pushed into `people_wg` |
| `config/dimensions.toml` sex and age | sex shares (not admitted); age bands feed `adults_by_ward` only | (a) / (b) as above | n/a | sex is unused in the fit; age is the adults read above |
| `src/levels.py`, `archive.py`, `build_play.py`, `compare_history.py`, `build_site.py`, `build_validation.py` | none | none | n/a | comments or credits only (grep, measured) |
| `src/montecarlo.py:3139` | language idea in a comment | none | n/a | no read |

Searches for "ceiling", "cap" and "extrapolat" in `src/pools.py` found no other census-derived ceiling. The `REGISTRATION_MAX` ceiling is the one count-clipping use.

## How the size use reaches a draw

1. Rates, not counts. `_nnls` fits `observed_w ~ sum_g parent_wg r_g` across wards (pools.py:937-980). The parent is census `people_wg` or `voting_age_wg`, so the cross-ward variation in census head counts, including the disputed 2022 group estimates (DATA-QUALITY §11, 262-286), sets `adult_share` and `registration`. This is the only route by which census magnitude changes a split. Within a ward the magnitude cancels in the row rescale (933).
2. Bounds. `REGISTRATION_MAX` binds four cells (above). `adult_share` and `turnout` are bounded at 1.0, and the 1.0 bound produced the degenerate-cell pattern of §1.164 (pools.py:942-963).
3. Capacity. The spec's `registered` per pool is roll x the registered-level composition, and `turnout` per pool is the fitted triple. Both feed `pool_spec` and the capacity test (tests/test_pool_bounds.py:333-407, `votes = registered x turnout[1]`).
4. Back-dating. Every one of these rates is fitted at the prior election on Census 2022 composition and counts (`1d-census-date.md` §2).

## The 2011 DA-in-White seeds

Measured from the tests and the log: `tests/test_pool_bounds.py:411` computes `need = rel x party_votes` against `pool_hi = registered x turnout[2]` (lines 396-405) from the emitted spec alone.

The log's diagnosis (MODEL-LOG §1.248, line 26263): the seed is "stale by construction". The weights come from pool vectors "fitted on <city> 2006" (the cities named: Buffalo City 0.602, Cape Town 0.536, Nelson Mandela Bay 0.624) and "the composition carries the party's SHAPE from the earlier election and its LEVEL from the target one": the DA was fitted at 97.5% of Cape Town's 2006 White pool and had grown past it by 2011 (line 18314-18315, with 1.26x for Cape Town). So the trigger is the party's growth between 2006 and 2011, not a size use of the census.

What the census adds, argued and not measured:
* The denominator side of the ratio is pool capacity: roll at the 2011 target x White share of registered at 2006 (census-influenced split) x White turnout (fitted on the same split). Both are built on Census 2022 composition back-dated to 2006 wards.
* The owner's evidence on direction: Census 2011 had Joburg's White share at 12.3% against 7.0% in Census 2022 (MODEL-LOG:11979, reported). A back-dated 2022 composition therefore tends to understate the White pool in 2006-2011. A smaller White pool lowers `pool_hi`, which raises the need/capacity ratio. So the back-dating probably makes these three violations worse, not cause them. The mechanism is composition, not a census size read.
* The size use (rate fits, `REGISTRATION_MAX`) is not implicated in these three: `REGISTRATION_MAX` binds on Indian/Asian cells, not White, and White rates sit under 2.0 (pools.py:905-911: 1.27 to 1.74 for Johannesburg White). Measured from that table for Johannesburg only; the table lists no Buffalo City, Cape Town White or Nelson Mandela Bay White figure, so for those three it is not shown that no size-side effect is present.
* The log's own note (line 26340) says the seed's size is unchanged by shape changes (`seeds` is invariant to the shape), and the capacity guard is not a fit constraint (§1.41, reverted).

What would separate the two: re-emit the three 2011 specs with the 2022 White share replaced by a Census 2011 (or Census 2001) White share and read whether the ratio falls below 1. That is a re-emit, so it is outside this read-only task.

## Summary

1. Not uniform. Ward registered and voted totals are roll and results (`_nest`, pools.py:930-934); the census is still read as a head count at 1289, 1291, 1467 and 1480.
2. Census head counts set `people_wg` and `voting_age_wg`, the parents of the registration solve, so they weight the rate fit across wards. Within a ward the magnitude cancels; between wards it does not.
3. One census-derived ceiling clips a counted quantity: `REGISTRATION_MAX = 2.0` (pools.py:914, 1500), binding on four cells in two cities; the roll exists for all of them.
4. The turnout record (pools.py:2840-2880) and the pool capacity (`registered_at_target`) are fitted on the census-influenced split at every prior election, back-dated from 2022. This is where census reaches draws.
5. The 2011 DA-in-White seeds are not a census size use. The log diagnoses a 2006 shape sold at a 2011 level (MODEL-LOG §1.248); the back-dated composition plausibly lowers the White capacity and so worsens the ratio. Argued, not measured.
6. All other census reads (drift, coverage, match, violations, `census_correction`) are guards or reports with no draw effect.
