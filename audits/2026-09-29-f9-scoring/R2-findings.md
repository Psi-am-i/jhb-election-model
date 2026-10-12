# R2 findings on `score_f9.py` (at `10fcd53`), and what was done with each

The reviewer ran from the committed brief, read no value from any
`history.json`, and edited nothing. Its full report is summarised here; the
lead re-derived each finding before applying it. Nothing was taken to the
owner: there was no finding the lead disputed. F6 was left to the lead by the
reviewer and is applied as reporting only.

| # | finding | lead's check | applied |
|---|---|---|---|
| F1 | P5 cannot fail when seat error moves in only the C1 cities: a percentile bound sits at exactly 0 | (6/8)^8 = 0.100 of resamples contain none of two moved cities; the reviewer's constructed case gives [−12.5, 0.0], reproduced | P5 is PASSED (uninformative) when a bound is exactly 0. The reviewer proposed zero-mass > 2.5% as the test; the self-test showed symmetric integer moves give 27% zero mass with zero well inside the interval, so the test is the pinned bound, zero mass reported |
| F2 | P5's established-columns clause decides on the MEDIAN seat | `row["seats"]` holds `model_seats`, the marginal median (compare_history.py:1916); `coherent` is not stored per party | demoted to context, labelled median |
| F3 | "established" swept in unseeded arrivals; the directional sum double-counted seeded arrivals | the READING admitted it | arrivals excluded by `backtest.arrival_baseline`; the directional claim is scored on the arrival group's \|seats_err\| alone |
| F4 | P7 applies C3's dose to C1's change; C1 reaches rows by `registered`, the bands, and the run-time `pool_counts` recompute (montecarlo.py:3990) | the recompute is not recorded in any spec field | P7 and the window's "no dose–response" are NOT TESTED; per-row dose, band dose and ΔCRPS printed as context |
| F5 | round-off specs are neither placebo nor F3 and enter every sum | §1.279 | the before specs are re-emitted today from `69cc6cc` in the worktree, so both sides share one environment; round-off (< 1e-9, same structure) is also classed with key-only as placebo |
| F6 | CRPS-by-cycle and calibration have no noise yardstick | §1.275: a spec change decorrelates the draw like a new seed | `--noise`: before-tree runs at other seeds; the seed spread is printed beside each paired statistic and never changes a verdict |
| F7 | "PIT drifts" is shape, not the mean | `calibration_columns` docstring | PIT sd and per-band mean PIT printed |
| F8 | P6's band was typed around a 25 Sept run; read it as a change | the prereg fixed the band around its stated 2,120 | scored as a change (−10..+15), falsified by a gain above +15 (the one-sided falsifier) or Cape Town > 1 ward; absolute band printed; VOID if any `wards_matched` differs; Cape Town clause marked uninformative |
| F9 | nothing asserts the populations or binds the pair | — | pair refused unless: seed, draws, seed_by_row, env_switches, overrides, filters, excluded equal; before commit `69cc6cc`; both clean; population = the prereg's 24; each history's `pool_artefact_keys` equal to its spec directory. P1 scored on the spec files |
| F10 | placebo field list incomplete | — | the whole row, less `constants_read` |
| F11 | the capacity scan sees only a row's top-12 parties | `vote_table(top=12)` | stated in the scan's output |
| F12 | self-test left branches unflipped | — | one constructed case per branch, each flipped and reverted |
| F13 | "votes do not improve" reading lenient | — | kept; both components printed |

**Not done, from the report:** hashing the rest of `data/` inside the script.
The reviewer checked it by hand on the backup (only the 27 specs differ), and
the before tree's `data/` is an APFS clone of that backup plus today's
re-emitted specs.

## Fix check (on `af9551e`), and what was done

The same reviewer checked the fixes under the same rules. Six were confirmed
as they stood (F2, F4, F7, F8, F11, F13). Each remaining point was
re-derived and applied:

| point | the defect | re-derived | applied |
|---|---|---|---|
| F1 | a pinned bound misses opposite signs: Mangaung −300 ×3 and Buffalo City +1 once gives [−112.5, +0.125], read as informative | resamples drawing neither city are (6/8)^8 = 10% and are exactly 0; those drawing Buffalo City alone are (7/8)^8 − (6/8)^8 = 24% and positive, so zero is inside at any magnitude | informative iff ((k−m)/k)^k ≤ 2.5%, m = cities with any nonzero difference; pinned bound and zero mass reported; self-test case added |
| F3 | `arrived()` returned the BASELINED parties, the inverse; seeded columns are not all arrivals | `arrival_baseline`'s docstring; seven seeded parties hold a 2019/2014 share | renamed `baselined`; established = baselined and not seeded; seeded-and-baselined columns reported as context; READING restated; a real-data check (ACDP baselined, ActionSA not, Johannesburg 2021) in the self-test |
| F5 | binding is by `pools_sha`, shared by the backup and the worktree re-emit | both `7264a929` | stated in the code; which spec set the before run read is recorded in MODEL-LOG |
| F6a | noise runs unchecked | — | each must match the before commit, be clean, share draws, hash seed and overrides, carry a different seed, and be bound to the before specs; a failing run is not used |
| F6b | `headline_noise` is a sum over moved rows beside a per-row mean | — | READING says compare with `headline.total` |
| F9, F12 | pair checks and branches not flipped | — | self-test flips filters, excluded, before dirt, before binding, noise validity, a round-off placebo break, and the directional VOID |

Remaining by hand: the "only specs differ" data check, re-run on the worktree
after its re-emit.
