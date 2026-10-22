# Pre-registration: each ward's roll split by its census group shares (2026-10-17)

Written before any code change, emit or run. Owner decision, 2026-10-17: the model concerns
itself with registered voters only. Census data is used for one thing, each population group's
share of a ward's census population, applied to that ward's IEC roll:

    registered_wg = roll_w × census_people_wg / census_people_w

No adults, age bands, population counts, fitted registration rates or census-count
reprojection. Votes cast per group are still not observed, so each group's turnout stays a
fit (votes ÷ registered by group, one rate per group, each ward scaled to its counted votes).

## What changes (code)

`pools.pool_counts`: `registered = composition × ward roll`; the people → adults →
registered nest, `adult_share`, `registration` rates, `census_correction`, `REGISTRATION_MAX`,
the age read and `reproject_counts` are deleted. `_reprojection_drift` weights each ward's
census mix by its registered voters instead of its census population. `projected_pool_shares`
(no caller) deleted. `registration_series` and `registered_at_target` are unchanged in code
and now read the new split. The two hand-typed site tokens built on the old split
(`hist_roll_white_voters`, `hist_census_white_adults`) and the methodology passage that
prints them are removed.

## Consumers (where the change can reach)

1. Every pool's registered size at every fitting year and at 2026 (`registered_at_target`).
2. Each pool's fitted turnout (`turnout_record`) and so the turnout bands in every spec.
3. Each party's composition by pool (`fit_city`, `composition("voted")`).
4. Placement of parties with no national record (`place_by_pool` in `run_model`).
5. The drawer's pool totals and so the drawn widths (`pool_spec`; `test_drawer` GOLDEN_POOLS).
6. Which fitting years the drift gate admits (re-weighted by the roll).

MODEL-LOG §1.315 found pool size and pool turnout move no mean citywide share at Johannesburg
2026 (largest 0.011 points), because the pool fit compensates. So this change is expected to
move widths and ward placement, not the mean.

## Predictions

- **P1 (mechanism).** Johannesburg 2021, `pool_counts`: registered shares of the roll Black
  African 75.6%, Coloured 5.5%, Indian/Asian 5.0%, White 13.9% (±0.1), against 64.8 / 5.5 /
  4.5 / 25.2 now. Ward sums equal the IEC roll to 1e-6.
- **P2 (mechanism).** No `registered`-over-adults violation is reported anywhere (the level is
  gone); `voted ≤ registered` holds per pool in every emitted city-year.
- **P3 (world).** Ward turnout predicted from each ward's group mix and one fitted turnout per
  group (roll-weighted RMSE over wards, 2021 local election) is lower under the new split than
  the old at ≥ 5 of the 8 metros. Johannesburg measured before this file: 5.22 against 5.46
  points.
- **P4 (2026 means).** Johannesburg 2026, 5,000 draws, seed 20261104: every party at ≥ 5% moves
  its mean list share by < 0.3 points; P(ANC largest alone) within ±3 points of 56.1%.
- **P5 (2026 turnout bands).** White band mode at Johannesburg 2026 rises from 0.527 toward
  0.60; Black African mode within ±0.03 of 0.364.
- **P6 (widths).** The drawer's White pool total narrows and centres lower (it is 31.7% of the
  drawn vote at the old golden); direction for the party bands not predicted.
- **P7 (backtest).** `compare_history` list MAE moves by < 0.10 points either way; wards wrong
  changes by ≤ 3. Direction not predicted.
- **P8 (record).** `test_pool_bounds::test_no_emitted_composition_weight_is_arithmetically_impossible`
  fails now on three 2011 city-years (DA in White at Buffalo City 1.25×, Cape Town 1.14×,
  Nelson Mandela Bay 1.07×). A smaller White pool gives the DA less room, so these are
  predicted to remain and grow, unless the re-fitted party composition moves the DA out of the
  White pool. Direction stated: at least the three remain.

Accept the change if P1 and P2 hold and the backtest does not worsen while explaining nothing
(ITERATING.md). P3 is the test of whether the owner's split describes the world better than the
fitted one; a failure there is reported, not tuned.
