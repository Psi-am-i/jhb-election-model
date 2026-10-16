# Historical performance — votes and seats, predicted against actual

24 city-years. Shares are citywide percentages; the model column is the median over draws.

## Provenance — are these out-of-sample scores?

**IN-SAMPLE.** 24 of 24 scored rows use priors fitted on their own target election or later.

| constant | rows it implicates |
|---|---|
| `contestation_expand` | 24 — buffalocity:2011, buffalocity:2016, buffalocity:2021, capetown:2011, capetown:2016, capetown:2021, ekurhuleni:2011, ekurhuleni:2016, ekurhuleni:2021, ethekwini:2011, ethekwini:2016, ethekwini:2021, joburg:2011, joburg:2016, joburg:2021, mangaung:2011, mangaung:2016, mangaung:2021, nelsonmandelabay:2011, nelsonmandelabay:2016, nelsonmandelabay:2021, tshwane:2011, tshwane:2016, tshwane:2021 |
| `dirichlet_scale` | 24 — buffalocity:2011, buffalocity:2016, buffalocity:2021, capetown:2011, capetown:2016, capetown:2021, ekurhuleni:2011, ekurhuleni:2016, ekurhuleni:2021, ethekwini:2011, ethekwini:2016, ethekwini:2021, joburg:2011, joburg:2016, joburg:2021, mangaung:2011, mangaung:2016, mangaung:2021, nelsonmandelabay:2011, nelsonmandelabay:2016, nelsonmandelabay:2021, tshwane:2011, tshwane:2016, tshwane:2021 |
| `entrant_prob` | 24 — buffalocity:2011, buffalocity:2016, buffalocity:2021, capetown:2011, capetown:2016, capetown:2021, ekurhuleni:2011, ekurhuleni:2016, ekurhuleni:2021, ethekwini:2011, ethekwini:2016, ethekwini:2021, joburg:2011, joburg:2016, joburg:2021, mangaung:2011, mangaung:2016, mangaung:2021, nelsonmandelabay:2011, nelsonmandelabay:2016, nelsonmandelabay:2021, tshwane:2011, tshwane:2016, tshwane:2021 |
| `entrant_share` | 24 — buffalocity:2011, buffalocity:2016, buffalocity:2021, capetown:2011, capetown:2016, capetown:2021, ekurhuleni:2011, ekurhuleni:2016, ekurhuleni:2021, ethekwini:2011, ethekwini:2016, ethekwini:2021, joburg:2011, joburg:2016, joburg:2021, mangaung:2011, mangaung:2016, mangaung:2021, nelsonmandelabay:2011, nelsonmandelabay:2016, nelsonmandelabay:2021, tshwane:2011, tshwane:2016, tshwane:2021 |
| `level_shrink` | 24 — buffalocity:2011, buffalocity:2016, buffalocity:2021, capetown:2011, capetown:2016, capetown:2021, ekurhuleni:2011, ekurhuleni:2016, ekurhuleni:2021, ethekwini:2011, ethekwini:2016, ethekwini:2021, joburg:2011, joburg:2016, joburg:2021, mangaung:2011, mangaung:2016, mangaung:2021, nelsonmandelabay:2011, nelsonmandelabay:2016, nelsonmandelabay:2021, tshwane:2011, tshwane:2016, tshwane:2021 |
| `level_shrink_scale` | 24 — buffalocity:2011, buffalocity:2016, buffalocity:2021, capetown:2011, capetown:2016, capetown:2021, ekurhuleni:2011, ekurhuleni:2016, ekurhuleni:2021, ethekwini:2011, ethekwini:2016, ethekwini:2021, joburg:2011, joburg:2016, joburg:2021, mangaung:2011, mangaung:2016, mangaung:2021, nelsonmandelabay:2011, nelsonmandelabay:2016, nelsonmandelabay:2021, tshwane:2011, tshwane:2016, tshwane:2021 |
| `pools` | 24 — buffalocity:2011, buffalocity:2016, buffalocity:2021, capetown:2011, capetown:2016, capetown:2021, ekurhuleni:2011, ekurhuleni:2016, ekurhuleni:2021, ethekwini:2011, ethekwini:2016, ethekwini:2021, joburg:2011, joburg:2016, joburg:2021, mangaung:2011, mangaung:2016, mangaung:2021, nelsonmandelabay:2011, nelsonmandelabay:2016, nelsonmandelabay:2021, tshwane:2011, tshwane:2016, tshwane:2021 |
| `turnout_correlation` | 24 — buffalocity:2011, buffalocity:2016, buffalocity:2021, capetown:2011, capetown:2016, capetown:2021, ekurhuleni:2011, ekurhuleni:2016, ekurhuleni:2021, ethekwini:2011, ethekwini:2016, ethekwini:2021, joburg:2011, joburg:2016, joburg:2021, mangaung:2011, mangaung:2016, mangaung:2021, nelsonmandelabay:2011, nelsonmandelabay:2016, nelsonmandelabay:2021, tshwane:2011, tshwane:2016, tshwane:2021 |

Covering **Johannesburg 2011, Tshwane 2011, Ekurhuleni 2011, eThekwini 2011, Cape Town 2011, Mangaung 2011, Nelson Mandela Bay 2011, Buffalo City 2011**:

```
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  !! IN-SAMPLE — THESE ARE NOT OUT-OF-SAMPLE SCORES
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  Scenario 'defaults' scores target 2011 using priors fitted on 2011 or later.
  The scores below measure fit, not forecasting skill; read them as an upper bound.
  No "derived_from" declared. These constants were READ BY THIS RUN, with what read them:
    contestation_expand      read 2011, 2016, 2021 — 0.220 is the median slate expansion measured across the eight metros and every consecutive LGE pair on disk, n=165 (§A5). ⚠️ RESOLVED BUT ALMOST CERTAINLY NOT CONSUMED at any past target: `levels.contestation` returns the target's published lists and `levels.projected_contestation` — the only consumer — is then never called. That gate is machine-checked by tests/test_levers_are_live.py GATES['real_contestation_lists']
      resolved at 0.22 (no read-site instrumentation)
    dirichlet_scale          read 2016, 2021 — ⚠️ UNRESOLVED, AND LISTED IN THE CONSERVATIVE DIRECTION. 1.0 is the identity on `pools.dirichlet_alpha`'s method-of-moments fit, whose inputs are pre-target and already covered by `pools` — on that reading it reads no result. But it was RETAINED after a 0.5/1.0/2.0 sweep across the nine city-years (§1.55, §1.58), and confirmed-by-the-panel is still selection-on-the-panel. Over-warning is the cheaper error
      resolved at 1.0 (no read-site instrumentation)
    entrant_prob             read 2011, 2016, 2021 — ⚠️ UNRESOLVED. 0.25 is TYPED and predates the measurement (§A3), so on one reading it read nothing. But the arrival base rate that validates it (NFP 2011, AIC 2016, ActionSA 2021; 7 of 9 city-years) and the panel sweep that refused to raise it (254/262/264 coherent at 0.25/0.290/0.353) both read those results. ⚠️ Inert wherever the arrivals are seeded by name — GATES['arrivals_are_named'], which is OPEN at 2011
      resolved at 0.25 (no read-site instrumentation)
    entrant_share            read 2016, 2021 — ⚠️ UNRESOLVED, as `entrant_prob`. [0.01, 0.04, 0.12] is typed from the plan; what is quoted for it is a check against the AIC's 1.62% in 2016 and against ActionSA in 2021 (§A17). Same arrivals gate
      resolved at [0.01, 0.04, 0.12] (no read-site instrumentation)
    level_shrink             read 2016, 2021 — leave-one-city-year-out over nine city-years chose 0.350 in all nine folds, and the FORM was screened against the same nine (§1.44 records that as an L1 leak). Worth coherent seat error 312 -> 264 on that panel, which is the size of the thing being declared
      resolved at 0.35 (no read-site instrumentation)
    level_shrink_scale       read 2016, 2021 — the twenty-fold 0.02-0.40 sweep that selected 0.04 ran on the same nine city-years (§F20). 'A scale, not a tuned constant' bounds how much the leak is WORTH — the correction improves 7 of 9 at every value — and does not make it absent
      resolved at 0.04 (no read-site instrumentation)
    pools                    read 2011, 2016, 2021 — pool COMPOSITION comes from Census 2022, which post-dates any target before 2026. The ratio ranges no longer do — they derive from transitions strictly before the target. A census is a covariate, not an outcome: it says who lives in a ward, not how they voted.
      consumed by: fitted on 2006
    turnout_correlation      read 2016, 2021 — the mean off-diagonal correlation between pools' log turnout changes, measured over 14 metro-transitions — eight metros, 2011->2016 AND 2016->2021 (montecarlo.py, beside TURNOUT_CORRELATION). It reads TURNOUT and not votes, which is why it was mistaken for a typed dial; turnout is still an outcome no forecaster holds before polling day, and at a 2021 target this constant was fitted on 2021's. FIX #38 makes the derived calculation take the target into account — a constant recomputed with a cutoff stops being a leak, which is the remedy this register is the fallback for. Until then it is declared
      resolved at 0.63 (no read-site instrumentation)
  Also read, and clean at this target:
    contestation             read nothing that reaches this target — ward-ballot PRESENCE at the target, taken from the target's own file. Nomination lists are public before polling day; no vote is read
    spine                    read nothing that reaches this target — the national-and-local level blend (task #22). Both records are filtered to elections strictly before the target; k=1.0 is fitted across metros on pre-target transitions only
    spine_k                  PROVENANCE UNSETTLED — FIX #39, OPEN. This key ships as None and resolves to `levels.SPINE_K = 1.0`, and the record gives that constant two incompatible provenances. `FITTED_ON["spine"]` says k is "fitted across metros on pre-target transitions only" and carries NO years, so it can never contaminate anything. `levels.py`, beside the constant, says it was "fitted by leave-one-metro-out over 180 party-city-years across eight metros and three transitions" — and three transitions on the archive reaches 2016->2021, which is the 2021 result, in Johannesburg among others. One of those two statements is wrong. Neither is repeated here as though it were settled; the investigation is the deliverable, and the register waits for it
  Declare a clean scenario with a top-level "derived_from": ["2011", ...] naming every
  election its numbers were fitted on; a run refuses if any entry reaches the target.
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```

Covering **Johannesburg 2016, Tshwane 2016, Ekurhuleni 2016, eThekwini 2016, Cape Town 2016, Mangaung 2016, Nelson Mandela Bay 2016, Buffalo City 2016**:

```
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  !! IN-SAMPLE — THESE ARE NOT OUT-OF-SAMPLE SCORES
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  Scenario 'defaults' scores target 2016 using priors fitted on 2016 or later.
  The scores below measure fit, not forecasting skill; read them as an upper bound.
  No "derived_from" declared. These constants were READ BY THIS RUN, with what read them:
    contestation_expand      read 2016, 2021 — 0.220 is the median slate expansion measured across the eight metros and every consecutive LGE pair on disk, n=165 (§A5). ⚠️ RESOLVED BUT ALMOST CERTAINLY NOT CONSUMED at any past target: `levels.contestation` returns the target's published lists and `levels.projected_contestation` — the only consumer — is then never called. That gate is machine-checked by tests/test_levers_are_live.py GATES['real_contestation_lists']
      resolved at 0.22 (no read-site instrumentation)
    dirichlet_scale          read 2016, 2021 — ⚠️ UNRESOLVED, AND LISTED IN THE CONSERVATIVE DIRECTION. 1.0 is the identity on `pools.dirichlet_alpha`'s method-of-moments fit, whose inputs are pre-target and already covered by `pools` — on that reading it reads no result. But it was RETAINED after a 0.5/1.0/2.0 sweep across the nine city-years (§1.55, §1.58), and confirmed-by-the-panel is still selection-on-the-panel. Over-warning is the cheaper error
      resolved at 1.0 (no read-site instrumentation)
    entrant_prob             read 2016, 2021 — ⚠️ UNRESOLVED. 0.25 is TYPED and predates the measurement (§A3), so on one reading it read nothing. But the arrival base rate that validates it (NFP 2011, AIC 2016, ActionSA 2021; 7 of 9 city-years) and the panel sweep that refused to raise it (254/262/264 coherent at 0.25/0.290/0.353) both read those results. ⚠️ Inert wherever the arrivals are seeded by name — GATES['arrivals_are_named'], which is OPEN at 2011
      resolved at 0.25 (no read-site instrumentation)
    entrant_share            read 2016, 2021 — ⚠️ UNRESOLVED, as `entrant_prob`. [0.01, 0.04, 0.12] is typed from the plan; what is quoted for it is a check against the AIC's 1.62% in 2016 and against ActionSA in 2021 (§A17). Same arrivals gate
      resolved at [0.01, 0.04, 0.12] (no read-site instrumentation)
    level_shrink             read 2016, 2021 — leave-one-city-year-out over nine city-years chose 0.350 in all nine folds, and the FORM was screened against the same nine (§1.44 records that as an L1 leak). Worth coherent seat error 312 -> 264 on that panel, which is the size of the thing being declared
      resolved at 0.35 (no read-site instrumentation)
    level_shrink_scale       read 2016, 2021 — the twenty-fold 0.02-0.40 sweep that selected 0.04 ran on the same nine city-years (§F20). 'A scale, not a tuned constant' bounds how much the leak is WORTH — the correction improves 7 of 9 at every value — and does not make it absent
      resolved at 0.04 (no read-site instrumentation)
    pools                    read 2016, 2021 — pool COMPOSITION comes from Census 2022, which post-dates any target before 2026. The ratio ranges no longer do — they derive from transitions strictly before the target. A census is a covariate, not an outcome: it says who lives in a ward, not how they voted.
      consumed by: fitted on 2011
    turnout_correlation      read 2016, 2021 — the mean off-diagonal correlation between pools' log turnout changes, measured over 14 metro-transitions — eight metros, 2011->2016 AND 2016->2021 (montecarlo.py, beside TURNOUT_CORRELATION). It reads TURNOUT and not votes, which is why it was mistaken for a typed dial; turnout is still an outcome no forecaster holds before polling day, and at a 2021 target this constant was fitted on 2021's. FIX #38 makes the derived calculation take the target into account — a constant recomputed with a cutoff stops being a leak, which is the remedy this register is the fallback for. Until then it is declared
      resolved at 0.63 (no read-site instrumentation)
  Also read, and clean at this target:
    contestation             read nothing that reaches this target — ward-ballot PRESENCE at the target, taken from the target's own file. Nomination lists are public before polling day; no vote is read
    spine                    read nothing that reaches this target — the national-and-local level blend (task #22). Both records are filtered to elections strictly before the target; k=1.0 is fitted across metros on pre-target transitions only
    splinter_home            read nothing that reaches this target — home-city splinter fractions. It DOES read results — the splits on record are in `pools.SPLITS` — but the window is cut at the target, so no year it reads can reach one. Which splits a given run used, and when they happened, are in that spec's `splinter_home` marker and in this run's own `constants_read`. `--retrospective-home` disables the cutoff and only the marker catches it
    spine_k                  PROVENANCE UNSETTLED — FIX #39, OPEN. This key ships as None and resolves to `levels.SPINE_K = 1.0`, and the record gives that constant two incompatible provenances. `FITTED_ON["spine"]` says k is "fitted across metros on pre-target transitions only" and carries NO years, so it can never contaminate anything. `levels.py`, beside the constant, says it was "fitted by leave-one-metro-out over 180 party-city-years across eight metros and three transitions" — and three transitions on the archive reaches 2016->2021, which is the 2021 result, in Johannesburg among others. One of those two statements is wrong. Neither is repeated here as though it were settled; the investigation is the deliverable, and the register waits for it
  Declare a clean scenario with a top-level "derived_from": ["2011", ...] naming every
  election its numbers were fitted on; a run refuses if any entry reaches the target.
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```

Covering **Johannesburg 2021, Tshwane 2021, Ekurhuleni 2021, eThekwini 2021, Cape Town 2021, Mangaung 2021, Nelson Mandela Bay 2021, Buffalo City 2021**:

```
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  !! IN-SAMPLE — THESE ARE NOT OUT-OF-SAMPLE SCORES
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  Scenario 'defaults' scores target 2021 using priors fitted on 2021 or later.
  The scores below measure fit, not forecasting skill; read them as an upper bound.
  No "derived_from" declared. These constants were READ BY THIS RUN, with what read them:
    contestation_expand      read 2021 — 0.220 is the median slate expansion measured across the eight metros and every consecutive LGE pair on disk, n=165 (§A5). ⚠️ RESOLVED BUT ALMOST CERTAINLY NOT CONSUMED at any past target: `levels.contestation` returns the target's published lists and `levels.projected_contestation` — the only consumer — is then never called. That gate is machine-checked by tests/test_levers_are_live.py GATES['real_contestation_lists']
      resolved at 0.22 (no read-site instrumentation)
    dirichlet_scale          read 2021 — ⚠️ UNRESOLVED, AND LISTED IN THE CONSERVATIVE DIRECTION. 1.0 is the identity on `pools.dirichlet_alpha`'s method-of-moments fit, whose inputs are pre-target and already covered by `pools` — on that reading it reads no result. But it was RETAINED after a 0.5/1.0/2.0 sweep across the nine city-years (§1.55, §1.58), and confirmed-by-the-panel is still selection-on-the-panel. Over-warning is the cheaper error
      resolved at 1.0 (no read-site instrumentation)
    entrant_prob             read 2021 — ⚠️ UNRESOLVED. 0.25 is TYPED and predates the measurement (§A3), so on one reading it read nothing. But the arrival base rate that validates it (NFP 2011, AIC 2016, ActionSA 2021; 7 of 9 city-years) and the panel sweep that refused to raise it (254/262/264 coherent at 0.25/0.290/0.353) both read those results. ⚠️ Inert wherever the arrivals are seeded by name — GATES['arrivals_are_named'], which is OPEN at 2011
      resolved at 0.25 (no read-site instrumentation)
    entrant_share            read 2021 — ⚠️ UNRESOLVED, as `entrant_prob`. [0.01, 0.04, 0.12] is typed from the plan; what is quoted for it is a check against the AIC's 1.62% in 2016 and against ActionSA in 2021 (§A17). Same arrivals gate
      resolved at [0.01, 0.04, 0.12] (no read-site instrumentation)
    level_shrink             read 2021 — leave-one-city-year-out over nine city-years chose 0.350 in all nine folds, and the FORM was screened against the same nine (§1.44 records that as an L1 leak). Worth coherent seat error 312 -> 264 on that panel, which is the size of the thing being declared
      resolved at 0.35 (no read-site instrumentation)
    level_shrink_scale       read 2021 — the twenty-fold 0.02-0.40 sweep that selected 0.04 ran on the same nine city-years (§F20). 'A scale, not a tuned constant' bounds how much the leak is WORTH — the correction improves 7 of 9 at every value — and does not make it absent
      resolved at 0.04 (no read-site instrumentation)
    pools                    read 2021 — pool COMPOSITION comes from Census 2022, which post-dates any target before 2026. The ratio ranges no longer do — they derive from transitions strictly before the target. A census is a covariate, not an outcome: it says who lives in a ward, not how they voted.
      consumed by: fitted on 2016
    turnout_correlation      read 2021 — the mean off-diagonal correlation between pools' log turnout changes, measured over 14 metro-transitions — eight metros, 2011->2016 AND 2016->2021 (montecarlo.py, beside TURNOUT_CORRELATION). It reads TURNOUT and not votes, which is why it was mistaken for a typed dial; turnout is still an outcome no forecaster holds before polling day, and at a 2021 target this constant was fitted on 2021's. FIX #38 makes the derived calculation take the target into account — a constant recomputed with a cutoff stops being a leak, which is the remedy this register is the fallback for. Until then it is declared
      resolved at 0.63 (no read-site instrumentation)
  Also read, and clean at this target:
    contestation             read nothing that reaches this target — ward-ballot PRESENCE at the target, taken from the target's own file. Nomination lists are public before polling day; no vote is read
    spine                    read nothing that reaches this target — the national-and-local level blend (task #22). Both records are filtered to elections strictly before the target; k=1.0 is fitted across metros on pre-target transitions only
    splinter_home            read nothing that reaches this target — home-city splinter fractions. It DOES read results — the splits on record are in `pools.SPLITS` — but the window is cut at the target, so no year it reads can reach one. Which splits a given run used, and when they happened, are in that spec's `splinter_home` marker and in this run's own `constants_read`. `--retrospective-home` disables the cutoff and only the marker catches it
    spine_k                  PROVENANCE UNSETTLED — FIX #39, OPEN. This key ships as None and resolves to `levels.SPINE_K = 1.0`, and the record gives that constant two incompatible provenances. `FITTED_ON["spine"]` says k is "fitted across metros on pre-target transitions only" and carries NO years, so it can never contaminate anything. `levels.py`, beside the constant, says it was "fitted by leave-one-metro-out over 180 party-city-years across eight metros and three transitions" — and three transitions on the archive reaches 2016->2021, which is the 2021 result, in Johannesburg among others. One of those two statements is wrong. Neither is repeated here as though it were settled; the investigation is the deliverable, and the register waits for it
  Declare a clean scenario with a top-level "derived_from": ["2011", ...] naming every
  election its numbers were fitted on; a run refuses if any entry reaches the target.
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```

## Headline

| city-year | council | list MAE | ward MAE | seat err (median) | medians sum to | seat err (coherent) | CRPS | last-lge | uniform-swing | prior-lge-noise | uniform-swing+roster |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Johannesburg 2011 | 260 | 5.10pp | 3.41pp | 58 | 256 | 58 | 41.6 | 52 | 60 | 56 | 56 |
| Johannesburg 2016 | 270 | 0.97pp | 1.39pp | 35 | 261 | 28 | 23.3 | 92 | 26 | 96 | 26 |
| Johannesburg 2021 | 270 | 6.24pp | 5.20pp | 99 | 257 | 88 | 69.7 | 134 | 126 | 130 | 128 |
| Tshwane 2011 | 210 | 6.47pp | 4.46pp | 53 | 205 | 58 | 38.6 | 40 | 56 | 46 | 56 |
| Tshwane 2016 | 214 | 1.42pp | 0.92pp | 20 | 206 | 18 | 14.5 | 70 | 10 | 76 | 16 |
| Tshwane 2021 | 214 | 2.12pp | 1.98pp | 43 | 201 | 34 | 27.9 | 80 | 60 | 80 | 60 |
| Ekurhuleni 2011 | 202 | 4.45pp | 2.89pp | 41 | 197 | 44 | 27.8 | 32 | 44 | 42 | 40 |
| Ekurhuleni 2016 | 224 | 1.43pp | 1.78pp | 26 | 216 | 24 | 19.8 | 80 | 22 | 80 | 16 |
| Ekurhuleni 2021 | 224 | 2.60pp | 2.19pp | 39 | 213 | 32 | 26.1 | 72 | 48 | 64 | 46 |
| eThekwini 2011 | 205 | 2.98pp | 1.18pp | 35 | 202 | 36 | 27.1 | 50 | 36 | 62 | 34 |
| eThekwini 2016 | 219 | 1.34pp | 3.33pp | 25 | 210 | 26 | 21.6 | 68 | 54 | 68 | 40 |
| eThekwini 2021 | 222 | 2.52pp | 2.85pp | 36 | 212 | 32 | 24.7 | 82 | 36 | 80 | 34 |
| Cape Town 2011 | 221 | 4.01pp | 2.69pp | 34 | 217 | 36 | 24.5 | 94 | 58 | 100 | 40 |
| Cape Town 2016 | 231 | 0.26pp | 0.36pp | 13 | 224 | 8 | 10.6 | 46 | 30 | 58 | 34 |
| Cape Town 2021 | 231 | 2.30pp | 2.66pp | 44 | 219 | 38 | 33.9 | 68 | 38 | 62 | 34 |
| Mangaung 2011 | 97 | 7.85pp | 5.49pp | 28 | 95 | 30 | 19.4 | 28 | 30 | 30 | 32 |
| Mangaung 2016 | 100 | 1.09pp | 1.78pp | 10 | 96 | 8 | 7.4 | 24 | 12 | 26 | 10 |
| Mangaung 2021 | 101 | 1.62pp | 0.65pp | 9 | 96 | 8 | 7.4 | 24 | 8 | 18 | 10 |
| Nelson Mandela Bay 2011 | 120 | 7.35pp | 6.35pp | 34 | 118 | 36 | 21.8 | 48 | 42 | 52 | 38 |
| Nelson Mandela Bay 2016 | 120 | 0.57pp | 0.84pp | 8 | 116 | 8 | 6.9 | 38 | 16 | 40 | 16 |
| Nelson Mandela Bay 2021 | 120 | 2.90pp | 3.04pp | 22 | 114 | 20 | 15.8 | 28 | 22 | 30 | 20 |
| Buffalo City 2011 | 100 | 6.36pp | 5.66pp | 26 | 98 | 28 | 18.9 | 28 | 30 | 28 | 30 |
| Buffalo City 2016 | 100 | 0.86pp | 2.80pp | 12 | 98 | 10 | 7.3 | 28 | 14 | 26 | 14 |
| Buffalo City 2021 | 100 | 2.82pp | 1.62pp | 9 | 97 | 6 | 5.9 | 14 | 12 | 16 | 12 |
| **TOTAL** [rows=24] | 4375 | — | — | **759** | — | **714** | **542.5** | 1320 | 890 | 1366 | 842 |

### Citable totals

**Quoting one number in a sentence? Paste this token, do not retype the figure:**

```
seat_abs_err_coherent=714/@4fb8002d/1000d/pools:76bfd9d6/rows=24
```

The full set, for anything more than one number:

```
seat_abs_err_coherent = 714      [rows=24]
seat_abs_err          = 759      [rows=24]   # MARGINAL, not comparable to the line above
crps                  = 542.49   [rows=24]
n_scored              = 807      [rows=24]   # summed scoring columns. NOT a denominator: `crps` is a sum, and this count differs between forecasters (§1.141)
margin_vs_uniform_swing = 19.8%   [rows=24, coherent, vs a point forecast]
margin_vs_prior_lge_noise = 47.7% [rows=24, coherent, vs a probabilistic forecast — the only reference here that expresses uncertainty]
```

`seat_abs_err` and `seat_abs_err_coherent` are DIFFERENT STATISTICS. Quoting one against the other is §1.214.

**The references are not the same kind of forecast**, and the margins above are not the same kind of claim: `last-lge` is **point**; `uniform-swing` is **point**; `prior-lge-noise` is **probabilistic**; `uniform-swing+roster` is **point**. A margin over a point forecast says the central estimate is better; only a margin over a probabilistic one says anything about the intervals. Measured from the rows, not declared.

### The margin is not evenly spread

The margin below is against **uniform swing** — **uniform swing is a POINT forecast here**.

**A margin over a POINT forecast is a claim about the central estimate, not about uncertainty.** CRPS collapses to absolute error when a forecast expresses no spread, so for those references the CRPS column below is the same statistic as the seat-error column beside it, not an independent check. Only a reference marked *probabilistic* puts the model's intervals under any test at all.

| | city-years | seat err (coherent) | uniform-swing | margin | CRPS | uniform-swing CRPS (point) | margin |
|---|---|---|---|---|---|---|---|
| Gauteng (Ekurhuleni, Johannesburg, Tshwane) | 9 | 384 | 452 | 15% | 289.3 | 452.0 | 36% |
| everywhere else (Buffalo City, Cape Town, Mangaung, Nelson Mandela Bay, eThekwini) | 15 | 330 | 438 | 25% | 253.2 | 438.0 | 42% |

**The headline margin is NOT concentrated in Gauteng on this panel**: 15% inside against 25% outside. Quote the split anyway — the point of the table is that the reader checks rather than assumes.  The model is beaten by uniform swing on seats at **4 of 24** city-years: Johannesburg 2016, Tshwane 2011, Tshwane 2016, Ekurhuleni 2016.

**Sign count against uniform swing: 15 wins, 4 losses, 5 ties across 24 city-years** — 2011: 4W 1L 3T; 2016: 5W 3L 0T; 2021: 6W 0L 2T. The sign REPLICATES across cycles, which is what the amended bar's Key 1 asks of any candidate and is the strongest claim this panel supports. Metros inside one cycle share a national swing, so 24 city-years across 8 cities is nearer **3 effective clusters** than 24. Never quote a p-value off the pooled count.

**Read the two seat-error columns together.** *seat err (median)* uses the per-party marginal median, which is what the per-party tables below show and which **does not sum to a council** — the *medians sum to* column says by how much. *seat err (coherent)* apportions the mean seat vector by largest remainder, so it IS a chamber. Lower is better throughout.

**The reference columns are the COHERENT statistic too, and until fix #34 they were not.** They carried the marginal median under the coherent key. That is exact for a deterministic reference — whose draws are identical repeats, so its median IS its allocation — and wrong for a stochastic one: `prior-lge-noise`'s medians fell short of the chamber, and a short vector flatters a forecaster wherever it over-forecasts, so the model's margin over the one reference here that expresses uncertainty was understated. Every forecaster in this table is now scored by `compare_history.coherent_seats`, the single definition of a coherent chamber.

**Every forecaster in every row is scored on one held column set** (24 distinct sets across 24 rows — they differ by city-year, which is expected; what matters is that the model and every reference share one within a row). CRPS and energy are invariant to the columns that holding adds, so those two are comparable with runs that predate it; **the variogram is not** — it is a mean over pairs and moves with the column count, so quote a variogram difference within a run and never across two.


## Guards — what fired, per city-year

**A zero here is a MEASURED zero.** The panel is scored with `verbose=False`, which suppresses `run_model`'s printed warnings, and until `ModelRun.guards` existed the solve counters were locals reachable only through a `--run-dir` trace — so the guard state of every city-year in this report used to be *unknown*, not clean. A `—` is an unreachable record and is NOT a zero.

`cap moved` and `IPF fell back` are the two counters whose silence was read as success for two days (§1.41). `solve non-conv (reachable)` excludes parties whose target sits under the level floor, which no θ can reach — read it rather than the raw count, which is expected to equal `solve_calls` (§1.98). The full board is in `history.json` under each record's `guards.counters`.

| city-year | IPF fell back | cap moved | cap undershoots | θ-bound violations | solve non-conv (reachable) | floor injected mean | floor injected worst | identity hits | excessive draws | roster |
|---|---|---|---|---|---|---|---|---|---|---|
| Johannesburg 2011 | 0/1,000 (0.0%) | 0.0000% | 0 | 549/2,000 (27.5%) | 0/2,000 (0.0%) | 0.0000% | 0.0001% | 21,154 | 0 | published (22, 9 dropped) |
| Johannesburg 2016 | 0/1,000 (0.0%) | 0.0000% | 0 | 877/3,000 (29.2%) | 235/2,000 (11.8%) | 0.0000% | 0.0000% | 12,436 | 255 | published (28, 9 dropped) |
| Johannesburg 2021 | 0/1,000 (0.0%) | 0.0000% | 0 | 873/4,000 (21.8%) | 26/2,000 (1.3%) | 0.0000% | 0.0000% | 64,534 | 92 | published (57, 13 dropped) |
| Tshwane 2011 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/0 | 4/2,000 (0.2%) | 0.0000% | 0.0001% | 23,822 | 0 | published (19, 7 dropped) |
| Tshwane 2016 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/0 | 88/2,000 (4.4%) | 0.0000% | 0.0000% | 14,986 | 62 | published (22, 8 dropped) |
| Tshwane 2021 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/0 | 95/2,000 (4.8%) | 0.0000% | 0.0000% | 95,994 | 121 | published (51, 15 dropped) |
| Ekurhuleni 2011 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/0 | 2/2,000 (0.1%) | 0.0000% | 0.0001% | 53,236 | 0 | published (24, 10 dropped) |
| Ekurhuleni 2016 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/0 | 22/2,000 (1.1%) | 0.0000% | 0.0000% | 0 | 21 | published (26, 9 dropped) |
| Ekurhuleni 2021 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/0 | 14/2,000 (0.7%) | 0.0000% | 0.0000% | 36,994 | 34 | published (38, 19 dropped) |
| eThekwini 2011 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/0 | 322/2,000 (16.1%) | 0.0000% | 0.0001% | 30,712 | 3 | published (19, 8 dropped) |
| eThekwini 2016 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/0 | 82/2,000 (4.1%) | 0.0000% | 0.0000% | 0 | 118 | published (28, 5 dropped) |
| eThekwini 2021 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/0 | 38/2,000 (1.9%) | 0.0000% | 0.0000% | 79,781 | 10 | published (54, 10 dropped) |
| Cape Town 2011 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/0 | 394/2,000 (19.7%) | 0.0000% | 0.0001% | 29,049 | 0 | published (34, 5 dropped) |
| Cape Town 2016 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/0 | 4/2,000 (0.2%) | 0.0000% | 0.0000% | 0 | 0 | published (37, 10 dropped) |
| Cape Town 2021 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/0 | 19/2,000 (0.9%) | 0.0000% | 0.0000% | 92,675 | 14 | published (54, 15 dropped) |
| Mangaung 2011 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/0 | 7/2,000 (0.4%) | 0.0000% | 0.0001% | 25,733 | 2 | published (11, 6 dropped) |
| Mangaung 2016 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/0 | 51/2,000 (2.5%) | 0.0000% | 0.0000% | 0 | 21 | published (16, 7 dropped) |
| Mangaung 2021 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/0 | 21/2,000 (1.1%) | 0.0000% | 0.0000% | 0 | 20 | published (24, 16 dropped) |
| Nelson Mandela Bay 2011 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/0 | 110/2,000 (5.5%) | 0.0000% | 0.0001% | 23,512 | 0 | published (14, 8 dropped) |
| Nelson Mandela Bay 2016 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/0 | 1/2,000 (0.1%) | 0.0000% | 0.0000% | 0 | 1 | published (20, 7 dropped) |
| Nelson Mandela Bay 2021 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/0 | 9/2,000 (0.4%) | 0.0000% | 0.0000% | 0 | 17 | published (29, 13 dropped) |
| Buffalo City 2011 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/0 | 34/2,000 (1.7%) | 0.0000% | 0.0001% | 19,041 | 0 | published (9, 9 dropped) |
| Buffalo City 2016 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/0 | 30/2,000 (1.5%) | 0.0000% | 0.0000% | 0 | 11 | published (13, 9 dropped) |
| Buffalo City 2021 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/0 | 14/2,000 (0.7%) | 0.0000% | 0.0000% | 35,830 | 7 | published (28, 12 dropped) |

**Guards that bound on at least one city-year:** excessive draws (17 of 24); floor injected mean (9 of 24); floor injected worst (9 of 24); identity hits (16 of 24); solve non-conv (reachable) (23 of 24); θ-bound violations (3 of 24). Every other counter above is a measured zero across the whole panel.


## The arrival channel, scored without the label

The headline CRPS above is scored after the model's generic `ENTRANT` column is renamed onto the largest party that actually arrived — a label chosen with the result in hand, which no baseline gets. This table does not use it. **PIT above 0.5 means the model forecast too little.**

| city-year | arrived | actual mass | forecast mass | actual seats | forecast seats | mass PIT | seats PIT |
|---|---|---|---|---|---|---|---|
| Johannesburg 2011 | 10 | 1.64% | 2.38% | 4 | 3.8 | 0.705 | 0.741 |
| Johannesburg 2016 | 13 | 2.29% | 2.00% | 5 | 4.7 | 0.734 | 0.635 |
| Johannesburg 2021 | 32 | 19.99% | 8.95% | 46 | 20.9 | 0.911 | 0.906 |
| Tshwane 2011 | 5 | 0.36% | 1.54% | 0 | 2.2 | 0.498 | 0.029 |
| Tshwane 2016 | 7 | 0.31% | 1.88% | 0 | 3.9 | 0.003 | 0.017 |
| Tshwane 2021 | 25 | 11.38% | 7.68% | 21 | 15.1 | 0.821 | 0.794 |
| Ekurhuleni 2011 | 12 | 2.56% | 4.36% | 5 | 7.8 | 0.252 | 0.212 |
| Ekurhuleni 2016 | 12 | 2.06% | 2.19% | 5 | 4.9 | 0.538 | 0.586 |
| Ekurhuleni 2021 | 20 | 9.14% | 6.29% | 17 | 13.2 | 0.824 | 0.783 |
| eThekwini 2011 | 8 | 5.61% | 2.49% | 11 | 4.1 | 0.866 | 0.962 |
| eThekwini 2016 | 14 | 3.25% | 1.97% | 6 | 4.1 | 0.913 | 0.828 |
| eThekwini 2021 | 29 | 7.21% | 3.88% | 15 | 7.4 | 0.937 | 0.940 |
| Cape Town 2011 | 16 | 1.02% | 1.43% | 1 | 1.5 | 0.760 | 0.759 |
| Cape Town 2016 | 20 | 1.43% | 1.97% | 2 | 3.9 | 0.227 | 0.172 |
| Cape Town 2021 | 31 | 8.00% | 2.38% | 18 | 4.5 | 0.999 | 0.999 |
| Mangaung 2011 | 2 | 0.28% | 1.45% | 0 | 0.7 | 0.742 | 0.371 |
| Mangaung 2016 | 6 | 4.74% | 2.09% | 3 | 1.7 | 0.948 | 0.852 |
| Mangaung 2021 | 11 | 1.53% | 3.67% | 0 | 3.4 | 0.079 | 0.010 |
| Nelson Mandela Bay 2011 | 4 | 0.41% | 1.95% | 0 | 1.6 | 0.240 | 0.120 |
| Nelson Mandela Bay 2016 | 8 | 1.59% | 1.92% | 2 | 1.9 | 0.494 | 0.618 |
| Nelson Mandela Bay 2021 | 15 | 7.02% | 3.00% | 8 | 3.0 | 0.978 | 0.976 |
| Buffalo City 2011 | 0 | 0.00% | 1.40% | 0 | 0.7 | 0.000 | 0.374 |
| Buffalo City 2016 | 3 | 0.68% | 2.09% | 0 | 1.8 | 0.149 | 0.105 |
| Buffalo City 2021 | 12 | 1.75% | 2.09% | 0 | 1.3 | 0.504 | 0.181 |
| **panel mean** | | | | | | **0.588** | **0.540** |

Mass PIT is above 0.5 at **15 of 24** city-years. A panel mean well above 0.5 on both columns is the model systematically under-forecasting how much of the ballot goes to parties arriving from nothing — read it next to the mid-ballot calibration below, which is the same leak seen through a different instrument.


### Does the arrival budget equal the arrival draw?

**The forecast side of the table above, reconciled against what was declared.** `declared` is the mass the emitted pool spec seeds by name; `generic slot` is the nameless `ENTRANT` column's expectation (`entrant_prob x mean(entrant_share)`), counted only where the model actually held that column; `unexplained` is what the draw produced beyond the two. **A row is flagged when the residual is at least as large as the budget it is a residual of** — that threshold is derived from the row, not typed.

| city-year | declared | generic slot | slot held? | budget | drawn | unexplained | |
|---|---|---|---|---|---|---|---|
| Johannesburg 2011 | 0.00% | 1.42% | yes | 1.42% | 2.38% | +0.96% |
| Johannesburg 2016 | 1.40% | 0.00% | no | 1.40% | 2.00% | +0.61% |
| Johannesburg 2021 | 8.48% | 0.00% | no | 8.48% | 8.95% | +0.47% |
| Tshwane 2011 | 0.00% | 1.42% | yes | 1.42% | 1.54% | +0.12% |
| Tshwane 2016 | 1.40% | 0.00% | no | 1.40% | 1.88% | +0.48% |
| Tshwane 2021 | 7.34% | 0.00% | no | 7.34% | 7.68% | +0.34% |
| Ekurhuleni 2011 | 0.00% | 1.42% | yes | 1.42% | 4.36% | +2.95% **← FLAG** |
| Ekurhuleni 2016 | 1.40% | 0.00% | no | 1.40% | 2.19% | +0.79% |
| Ekurhuleni 2021 | 5.18% | 0.00% | no | 5.18% | 6.29% | +1.10% |
| eThekwini 2011 | 0.00% | 1.42% | yes | 1.42% | 2.49% | +1.07% |
| eThekwini 2016 | 1.40% | 0.00% | no | 1.40% | 1.97% | +0.57% |
| eThekwini 2021 | 2.57% | 0.00% | no | 2.57% | 3.88% | +1.31% |
| Cape Town 2011 | 0.00% | 1.42% | yes | 1.42% | 1.43% | +0.01% |
| Cape Town 2016 | 1.40% | 0.00% | no | 1.40% | 1.97% | +0.57% |
| Cape Town 2021 | 1.64% | 0.00% | no | 1.64% | 2.38% | +0.73% |
| Mangaung 2011 | 0.00% | 1.42% | yes | 1.42% | 1.45% | +0.03% |
| Mangaung 2016 | 1.40% | 0.00% | no | 1.40% | 2.09% | +0.69% |
| Mangaung 2021 | 1.64% | 0.00% | no | 1.64% | 3.67% | +2.03% **← FLAG** |
| Nelson Mandela Bay 2011 | 0.00% | 1.42% | yes | 1.42% | 1.95% | +0.54% |
| Nelson Mandela Bay 2016 | 1.40% | 0.00% | no | 1.40% | 1.92% | +0.52% |
| Nelson Mandela Bay 2021 | 1.64% | 0.00% | no | 1.64% | 3.00% | +1.35% |
| Buffalo City 2011 | 0.00% | 1.42% | yes | 1.42% | 1.40% | -0.02% |
| Buffalo City 2016 | 1.40% | 0.00% | no | 1.40% | 2.09% | +0.70% |
| Buffalo City 2021 | 1.64% | 0.00% | no | 1.64% | 2.09% | +0.45% |

⛔ **The residual exceeds the accounted budget at 2 of 24 city-years: Ekurhuleni 2011, Mangaung 2021.** At those rows the arrival mass the model draws is not the arrival mass anything declared, by more than the declaration itself. Go and look; this is a tripwire, not a verdict.

⚠️ The model drew arrival mass with **no generic slot recorded** at 16 of 24 city-years (Johannesburg 2016, Johannesburg 2021, Tshwane 2016, Tshwane 2021, Ekurhuleni 2016, Ekurhuleni 2021, eThekwini 2016, eThekwini 2021, Cape Town 2016, Cape Town 2021, Mangaung 2016, Mangaung 2021, Nelson Mandela Bay 2016, Nelson Mandela Bay 2021, Buffalo City 2016, Buffalo City 2021). Before the presence test was moved ahead of the relabel this was true at twenty of twenty-four rows and meant the detector was blind, not that the slot was absent. If it is non-empty here, check that against `montecarlo`'s rule for appending `ENTRANT` before reading it as a fact about the model.


## Where the vote error sits on the ballot

**Two columns per band, and they answer different questions.** *signed* is the net error in points — positive means the model gave that band MORE than it won — and it is what shows one band eating another. *abs* sums the per-party error without cancelling, and it is the only one of the two that is a measure of error at all. Where they diverge, the band is wrong about individual parties in both directions at once: Johannesburg 2021's ranks 1-3 are the case that motivated the column (ANC and DA over, ActionSA far under). The bands are by actual rank.

| city-year | 1-3 signed | 1-3 abs | 4-12 signed | 4-12 abs | 13+ signed | 13+ abs | phantom | seats at stake in 4-12 |
|---|---|---|---|---|---|---|---|---|
| Johannesburg 2011 | -10.56pp | 12.75pp | **+10.13pp** | 11.41pp | +0.43pp | 0.77pp | 0.00pp (0) | 12 |
| Johannesburg 2016 | -0.66pp | 4.08pp | **-1.63pp** | 2.70pp | +2.29pp | 2.33pp | 0.00pp (0) | 15 |
| Johannesburg 2021 | +1.67pp | 24.12pp | **-2.05pp** | 9.38pp | +0.38pp | 1.46pp | 0.00pp (0) | 58 |
| Tshwane 2011 | -10.50pp | 17.46pp | **+8.72pp** | 9.49pp | +0.58pp | 0.90pp | 1.20pp (1) | 6 |
| Tshwane 2016 | -3.02pp | 4.60pp | **+1.04pp** | 1.19pp | +1.98pp | 2.06pp | 0.00pp (0) | 7 |
| Tshwane 2021 | +7.31pp | 7.31pp | **-7.84pp** | 7.89pp | +0.53pp | 1.45pp | 0.00pp (0) | 44 |
| Ekurhuleni 2011 | -8.38pp | 10.28pp | **+8.14pp** | 9.07pp | +0.24pp | 1.21pp | 0.00pp (0) | 13 |
| Ekurhuleni 2016 | -0.67pp | 5.30pp | **-1.37pp** | 2.58pp | +2.04pp | 2.04pp | 0.00pp (0) | 12 |
| Ekurhuleni 2021 | +6.70pp | 6.70pp | **-7.51pp** | 7.51pp | +0.81pp | 1.54pp | 0.00pp (0) | 38 |
| eThekwini 2011 | -4.00pp | 6.18pp | **+4.17pp** | 11.33pp | -0.17pp | 0.35pp | 0.00pp (0) | 24 |
| eThekwini 2016 | -1.09pp | 3.59pp | **+0.25pp** | 5.65pp | +0.84pp | 1.20pp | 0.00pp (0) | 18 |
| eThekwini 2021 | +6.01pp | 6.21pp | **-5.47pp** | 6.04pp | -0.55pp | 3.22pp | 0.00pp (0) | 31 |
| Cape Town 2011 | -3.06pp | 14.96pp | **+3.21pp** | 4.14pp | -0.15pp | 1.20pp | 0.00pp (0) | 10 |
| Cape Town 2016 | +0.14pp | 1.65pp | **-1.15pp** | 1.34pp | +1.01pp | 1.35pp | 0.00pp (0) | 12 |
| Cape Town 2021 | +6.98pp | 6.98pp | **-7.16pp** | 7.24pp | +0.17pp | 1.58pp | 0.00pp (0) | 38 |
| Mangaung 2011 | -5.17pp | 26.09pp | **+3.72pp** | 4.79pp | +0.00pp | 0.00pp | 1.45pp (1) | 3 |
| Mangaung 2016 | +1.38pp | 3.43pp | **-1.66pp** | 5.22pp | +0.29pp | 0.33pp | 0.00pp (0) | 6 |
| Mangaung 2021 | -0.68pp | 4.15pp | **-1.64pp** | 3.05pp | +2.32pp | 2.54pp | 0.00pp (0) | 12 |
| Nelson Mandela Bay 2011 | -2.72pp | 26.42pp | **+1.38pp** | 2.61pp | -0.05pp | 0.05pp | 1.38pp (1) | 3 |
| Nelson Mandela Bay 2016 | -0.15pp | 1.85pp | **-1.03pp** | 2.61pp | +1.18pp | 1.18pp | 0.00pp (0) | 7 |
| Nelson Mandela Bay 2021 | +5.03pp | 8.22pp | **-6.39pp** | 6.73pp | +1.36pp | 1.64pp | 0.00pp (0) | 15 |
| Buffalo City 2011 | +0.56pp | 24.74pp | **-1.96pp** | 3.78pp | +0.00pp | 0.00pp | 1.40pp (1) | 5 |
| Buffalo City 2016 | -0.93pp | 5.01pp | **+0.93pp** | 5.85pp | +0.00pp | 0.00pp | 0.00pp (0) | 8 |
| Buffalo City 2021 | -0.65pp | 6.68pp | **-0.22pp** | 1.78pp | +0.87pp | 1.33pp | 0.00pp (0) | 6 |

**Totals across 24 city-years:** ranks 1-3 -16.43pp signed / 238.76pp absolute, ranks 4-12 -5.40pp / 133.40pp, ranks 13+ +16.39pp / 29.73pp.

**Phantom mass: 5.43pp** on parties that did not stand at all — including the generic `ENTRANT` column where no party arrived. The bands iterate the parties that DID stand, so none of them can see it; it is exactly why the three signed bands sum to -5.43pp rather than to zero.


## Ward winners — the geography key

**`seat_abs_err_coherent` sees geography only weakly and this sees it directly.** `solve_and_predict` places the draw's preliminary vote on the districts at reference weights, so `dev` and `gamma` reach the citywide share only through how they interact with district turnout, and the seat score mostly through an overhang trigger. A change to the VD layer is judged here. Hit rate is the modal call; Brier (multi-category, 0 to 2) is the proper score and is what a change in CONFIDENCE moves. **Read the model against the baselines in its own row** — safe wards are called correctly by anything at all.

| city-year | wards | model called | hit rate | Brier MC | last-lge | uniform-swing | prior-lge-noise | uniform-swing+roster |
|---|---|---|---|---|---|---|---|---|
| Johannesburg 2011 | 130 | 126 | 96.9% | 0.052 | 92.3% | 93.8% | 92.3% | 93.8% |
| Johannesburg 2016 | 135 | 135 | 100.0% | 0.014 | 94.8% | 97.8% | 94.8% | 97.8% |
| Johannesburg 2021 | 135 | 127 | 94.1% | 0.092 | 93.3% | 93.3% | 93.3% | 93.3% |
| Tshwane 2011 | 105 (only 99 matched) | 98 | 93.3% | 0.082 | 98.1% | 98.1% | 98.1% | 98.1% |
| Tshwane 2016 | 107 | 104 | 97.2% | 0.045 | 98.1% | 98.1% | 98.1% | 98.1% |
| Tshwane 2021 | 107 | 105 | 98.1% | 0.024 | 98.1% | 98.1% | 98.1% | 98.1% |
| Ekurhuleni 2011 | 101 | 98 | 97.0% | 0.049 | 94.1% | 96.0% | 95.0% | 96.0% |
| Ekurhuleni 2016 | 112 | 111 | 99.1% | 0.026 | 97.3% | 99.1% | 97.3% | 99.1% |
| Ekurhuleni 2021 | 112 | 107 | 95.5% | 0.066 | 95.5% | 94.6% | 95.5% | 94.6% |
| eThekwini 2011 | 103 | 90 | 87.4% | 0.148 | 93.2% | 92.2% | 93.2% | 92.2% |
| eThekwini 2016 | 110 (only 109 matched) | 97 | 88.2% | 0.182 | 82.7% | 85.5% | 83.6% | 85.5% |
| eThekwini 2021 | 111 | 109 | 98.2% | 0.029 | 96.4% | 98.2% | 96.4% | 98.2% |
| Cape Town 2011 | 111 | 111 | 100.0% | 0.017 | 85.6% | 97.3% | 85.6% | 96.4% |
| Cape Town 2016 | 116 | 116 | 100.0% | 0.001 | 100.0% | 100.0% | 100.0% | 100.0% |
| Cape Town 2021 | 116 | 115 | 99.1% | 0.015 | 99.1% | 99.1% | 99.1% | 99.1% |
| Mangaung 2011 | 49 | 49 | 100.0% | 0.020 | 98.0% | 95.9% | 98.0% | 95.9% |
| Mangaung 2016 | 50 (only 49 matched) | 48 | 96.0% | 0.033 | 96.0% | 98.0% | 96.0% | 98.0% |
| Mangaung 2021 | 51 | 50 | 98.0% | 0.043 | 98.0% | 96.1% | 98.0% | 96.1% |
| Nelson Mandela Bay 2011 | 60 | 60 | 100.0% | 0.018 | 83.3% | 96.7% | 83.3% | 96.7% |
| Nelson Mandela Bay 2016 | 60 | 57 | 95.0% | 0.053 | 96.7% | 96.7% | 96.7% | 96.7% |
| Nelson Mandela Bay 2021 | 60 | 57 | 95.0% | 0.054 | 95.0% | 95.0% | 95.0% | 95.0% |
| Buffalo City 2011 | 50 | 47 | 94.0% | 0.097 | 94.0% | 98.0% | 94.0% | 98.0% |
| Buffalo City 2016 | 50 | 48 | 96.0% | 0.087 | 100.0% | 96.0% | 100.0% | 96.0% |
| Buffalo City 2021 | 50 | 48 | 96.0% | 0.076 | 96.0% | 96.0% | 96.0% | 96.0% |

**Pooled over 24 city-years: 2113/2191 = 96.4% of ward contests called correctly, against last-lge 94.7%, uniform-swing 96.2%, prior-lge-noise 94.8%, uniform-swing+roster 96.1%. A margin over the baselines that is smaller than the seat margin is the model's geography adding less than its citywide machinery, which is a statement the seat columns cannot make.

## Calibration — pooled across every city-year, and split by rank

**Pool over city-years; never over rank bands.** Seven to fifteen scored columns per city-year cannot distinguish a 50% interval from an 80% one, so the city-years must be pooled to say anything at all. But the rank bands must NOT be: this model is biased in opposite directions at the top of the ballot and in the middle, and a mean over both lands between them and reports a model that does not exist. The pooled table comes first because it is the familiar one; **the split table below it is the one to read.**

A mean PIT above 0.50 means the truth keeps landing high in the forecast distribution — the model forecast too LOW for those columns. Below 0.50 means it forecast too HIGH. Read the sign per band; the pooled sign is an artefact of how the two bands happen to be sized.

| population | n | 50% | 80% | 90% | mean PIT | χ²_RS vs flat (5% crit) |
|---|---|---|---|---|---|---|
| reference (INPUT-selected — fixed; the only one to compare on) | 514 | 78% | 90% | 92% | 0.523 | 20.1 (16.92) |
| claimed by the model (forecast-selected — neutral for ONE model) | 231 | 71% | 87% | 90% | 0.447 | 33.6 (16.92) |
| won a seat (outcome-selected — INFLATED by construction) | 271 | 60% | 83% | 85% | 0.608 | 65.6 (16.92) |
| every scored column (MIXED: outcome-selected + neutral, diluted) | 607 | 81% | 91% | 93% | 0.500 | 16.3 (16.92) |

* **reference** (n=514) PIT histogram [59, 33, 42, 48, 50, 51, 52, 65, 63, 51] — approximately flat
* **claimed** (n=231) PIT histogram [45, 16, 19, 21, 25, 22, 19, 25, 32, 7] — approximately flat
* **seat_holders** (n=271) PIT histogram [28, 8, 16, 16, 24, 24, 20, 36, 48, 51] — U-shaped: the truth lands outside the distribution too often — under-dispersed, widen it
* **all** (n=607) PIT histogram [77, 49, 53, 59, 61, 58, 55, 67, 72, 56] — approximately flat


The verdict at the end of each line is `score.pit_histogram`'s shape heuristic, which reads the end mass and the mean. **DO NOT ACT ON IT AS A WIDTH VERDICT — it is not reliable as one, and on this model it is demonstrably wrong.** The heuristic tests the mass in the two END bins against flat, so a histogram that is monotone increasing scores as U-shaped: a shifted forecast piles mass in the top bin and gets called under-dispersed. On the ranks 4-12 columns it reads the histogram `[1, 1, 1, 11, 14]` — 25 of 28 in the top two bins, monotone, nothing at the bottom — and prints *"U-shaped … under-dispersed, widen it"*, while calling the pooled population *"hump-shaped — over-dispersed, hedging"*. The two verdicts contradict each other and the band one contradicts the level-free width table below, which is the one that is right. `score.py` is not changed here — the heuristic is fine for its own purpose and what is wrong is quoting it about width. **The χ²_RS column is the test of uniformity — `score.chi2_clustered`, clustered by city-year and averaged over the PIT re-randomisations, set out below; the level-free dispersion table is the test of width.**

### The uniformity test — `score.chi2_clustered`

* **reference** (24 city-years, R=64) — not established: χ²_RS averages 20.09 against 16.92 but only 39/64 randomisations reject — the answer depends on the PIT re-roll, not on the model [cells 0.75–2.52, cv² 0.27; Satterthwaite χ² 15.79 against 14.26 on 7.1 dof, 35/64]. The NOMINAL χ² it corrects averages 22.2 with sd 8.1 across those 64 randomisations; the 95% cluster-bootstrap interval on it is [10.7, 67.7] from 20,000 replicates.
* **claimed** (24 city-years, R=64) — uniformity REJECTED after the clustering correction: χ²_RS 33.57 against 16.92 on 9 dof, design effect 1.26, in 64/64 randomisations [cells 0.56–3.99, cv² 0.60; Satterthwaite χ² 21.03 against 12.10 on 5.7 dof, 63/64]. The NOMINAL χ² it corrects averages 42.1 with sd 7.4 across those 64 randomisations; the 95% cluster-bootstrap interval on it is [24.2, 102.4] from 20,000 replicates.
* **seat_holders** (24 city-years, R=64) — uniformity REJECTED after the clustering correction: χ²_RS 65.61 against 16.92 on 9 dof, design effect 1.12, in 64/64 randomisations [cells 0.29–2.47, cv² 0.39; Satterthwaite χ² 47.28 against 13.34 on 6.5 dof, 64/64]. The NOMINAL χ² it corrects averages 72.9 with sd 8.9 across those 64 randomisations; the 95% cluster-bootstrap interval on it is [46.4, 132.4] from 20,000 replicates.
* **all** (24 city-years, R=64) — uniformity NOT rejected once the columns are clustered: χ²_RS 16.30 against 16.92 on 9 dof, design effect 1.07 (nominal χ² 17.30) [cells 0.75–2.42, cv² 0.27; Satterthwaite χ² 12.89 against 14.27 on 7.1 dof, 17/64]. The NOMINAL χ² it corrects averages 17.3 with sd 6.9 across those 64 randomisations; the 95% cluster-bootstrap interval on it is [8.1, 59.1] from 20,000 replicates.

⚠️ **The cluster level is this file's choice, not the statistic's**, and `score.chi2_clustered` returns the limitation with the number so that it is quoted with it: *the clusters are whatever the caller grouped by. On this panel city-year clustering (k=24) moves the design effect little; the CYCLE level, where sd(z) differs most (see the per-cycle split this report prints for each band), has k=3 and cannot be estimated. Quote the city-year result WITH that limitation — see score.chi2_clustered.__doc__.*

**Two corrections separate this column from the χ² a PIT histogram reports, and the second is the one that was missing.** The PIT of an integer seat count is randomised within its jump, so a χ² computed on one draw of that randomisation is a draw from a distribution and not a statistic — the `sd` printed above is its spread with the model standing still, and on this panel it is a large fraction of the statistic itself. And the columns inside a city-year share a turnout draw, a pool structure and a national swing, so the nominal test's critical value is not this design's. `score.chi2_clustered` averages over R re-randomisations and applies the Rao-Scott correction with the design effect ESTIMATED from the city-years; it needs at least 8 of them and says `not established` rather than printing a number when it has fewer. See its docstring for what the design effect turns out to be here, and why.

The three populations differ by which columns they count, and the difference is itself the finding. `claimed` selects on the FORECAST, which leaves PIT uniform under calibration, so it is the honest test and the only one to quote. `seat_holders` selects on the OUTCOME: zero is the bottom of the support, so winning a seat selects over-performers and the population reads high even for a perfect forecaster — it is quoted because it is the population a reader assumes, not because it is neutral. `all` was documented as neutral and **is not**: `score.seat_matrix` admits a column when `truth[i] > 0 or samples[:, i].max() > 0`, and the first clause lets a party in because it WON, which is outcome selection. **13 of its 607 columns across 24 city-years carry PIT exactly 0 or 1** — parties the model gave zero seats in every draw, present only because they won a seat (Johannesburg 2011 ALJAMAAH, Johannesburg 2011 COPE, Johannesburg 2021 PA, Tshwane 2011 COPE, Tshwane 2011 UNITED_CHRISTIAN_DEMOCRATIC_PARTY, +8 more). It is a mixture of an outcome-selected set and a neutral one.

**The dilution is in `reference`, not in `all`, and this report said otherwise for months.** A column correctly at zero on both sides is a free interval hit and a near-uniform PIT — but `seat_matrix`'s admission rule excludes it from `all` by construction, and the count there is **0 of 607**. Such columns are admitted to `reference`, which is built with `keep_all=True` over a fixed universe, and there the count is **61 of 514**. `all` is still not a test of anything — its outcome-selected part and its neutral part push opposite ways — but quote the dilution against the population that actually carries it.

### Split by actual PR rank — `claimed` columns

**The pooled row above is the average of the rows below, and they have opposite signs.** This is the same fault as a signed error sum inside a rank band, one level up: an average over subsets biased in opposite directions reports the midpoint and calls it centred.

| band | n | mean PIT | 95% CI (cluster bootstrap) | 50% | 80% | 90% | 50% (PIT) | 80% (PIT) | 90% (PIT) |
|---|---|---|---|---|---|---|---|---|---|
| ranks 1-3 | 72 | 0.477 | [0.435, 0.516] | 60% [44–75] | 85% [76–92] | 92% [86–97] | 54% [40–68] | 82% [74–90] | 88% [81–93] |
| ranks 4-12 | 125 | 0.456 | [0.373, 0.538] | 73% [63–83] | 86% [78–94] | 87% [80–94] | 45% [34–56] | 75% [64–86] | 82% [74–91] |
| ranks 13+ | 34 | 0.350 | [0.209, 0.477] | 88% [74–98] | 94% [83–100] | 97% [89–100] | 47% [21–71] | 76% [56–91] | 82% [67–94] |

The CI resamples CITY-YEARS, not columns: columns inside one city-year share a turnout draw, a pool structure and a national swing, so a column bootstrap would give an interval far too tight. 20,000 replicates, fixed seed.

**The two coverage triples are the same question asked twice.** The first is `score.coverage` — the empirical quantile interval, which on integer seats must include whole endpoints and therefore over-covers. The second is the fraction of columns whose randomised PIT falls in the central interval, which carries no such inflation. They agree at ranks 1-3, where parties hold tens of seats and one endpoint is worth nothing, and diverge at ranks 4-12, where parties hold one to ten and an endpoint is a large part of the interval. **Read the PIT columns whenever the two are compared** — but neither triple is the width verdict on its own; that is the table below.

**Read all three coverage levels together, never one of them.** A forecast whose intervals are too NARROW under-covers at EVERY level — that is what narrow means. A forecast that is merely SHIFTED loses coverage at the 50% level first and hardest, because it has vacated the middle of its own interval, and its 80% and 90% coverages fall too. Only intervals that are too WIDE push the 80% and 90% coverages above nominal. So a band that reads LOW at 50% and HIGH at 80 and 90 is shifted and too wide, and reading its 50% column alone gives exactly the opposite instruction. **That mistake has been made twice on this report, in opposite directions, and rule 8 of `ITERATING.md` carried each of them.** The width verdict belongs to the level-free table above; the coverage rows corroborate it or they do not.

The rank-band vote table further up and the mean-PIT column here are the same LEVEL finding measured twice — top three over, middle short. Because shares sum to one that gap is a zero-sum transfer, not two independent faults, so a level fix has to move mass rather than add it.

### Is it the right WIDTH? — the level divided out

**This table, not the coverage rows, is the width verdict.** Coverage moves with the level as well as the width: a forecast pushed off centre vacates the middle of its own interval, so its 50% coverage falls however wide it is. Read at one level, coverage says 'too narrow' for a forecast that is merely shifted. The columns below divide the level out. **1.00 is right; below 1.00 the intervals are too WIDE; above 1.00 too narrow.** `1/ratio` is roughly the factor they are out by.

| band | n | probit-SD (level-free) | same @1e-2 clip | drop saturated | sat. PITs | exact SD of z | standardised bias (mean z) | PIT variance vs 1/12 |
|---|---|---|---|---|---|---|---|---|
| ranks 1-3 | 72 | **1.112** | 1.010 | 1.112 | 0 | 0.916 | -0.132 | 0.0830 vs 0.0833 |
| ranks 4-12 | 125 | 1.447 ⛔UNQUOTABLE | 1.121 | 1.082 | 6 | 1.074 | -0.359 | 0.0942 vs 0.0833 |
| ranks 13+ | 34 | **0.960** | 0.958 | 0.960 | 0 | 0.768 | -0.447 | 0.0719 vs 0.0833 |

⛔ **A probit-SD from a band carrying a saturated PIT is a property of the CLIP, not of the forecast, and this table prints both so the reader can see which.** `_probit` clips at 1e-6; a column whose truth exceeded every draw has a PIT of exactly 1.0, and `Φ⁻¹(1)` is infinite, so the figure in the first column is whatever the clip decides. The `@1e-2` column is the same statistic with a looser clip and the `drop saturated` column is the same statistic with those columns removed instead of pinned — the honest answer to a question the clip only papers over. **Where the three disagree and `sat. PITs` is non-zero, the band's width is UNQUOTABLE**: say so, or quote the drop-saturated figure and say that is what it is. Measured on `reference` ranks 4-12 over Johannesburg alone, the three read 1.55 / 1.07 / 1.10 — the same band, two different verdicts. MODEL-LOG §1.132, §1.134.

#### The same question on the FIXED population — and it disagrees

**The `n` here is the number of columns the width figure was actually computed on** — columns with a defined `z`. A column whose draws are all identical has no scale, so it carries a PIT and no `z`; the pooled tables above count PIT values and their `n` is larger.

| band | `claimed` n(z) | `claimed` SD of z | `reference` n(z) | `reference` SD of z | `reference` mean z | `reference` probit-SD | same @1e-2 | drop saturated | sat. PITs |
|---|---|---|---|---|---|---|---|---|---|
| ranks 1-3 | 72 | 0.916 | 72 | 0.916 | -0.132 | **1.112** | 1.010 | 1.112 | 0 |
| ranks 4-12 | 125 | 1.074 | 183 | 2.744 | +0.548 | 1.616 ⛔UNQUOTABLE | 1.263 | 1.209 | 10 |
| ranks 13+ | 34 | 0.768 | 196 | 0.645 | -0.188 | **0.878** | 0.867 | 0.878 | 0 |

⛔ **A probit-SD from a band carrying a saturated PIT is a property of the CLIP, not of the forecast, and this table prints both so the reader can see which.** `_probit` clips at 1e-6; a column whose truth exceeded every draw has a PIT of exactly 1.0, and `Φ⁻¹(1)` is infinite, so the figure in the first column is whatever the clip decides. The `@1e-2` column is the same statistic with a looser clip and the `drop saturated` column is the same statistic with those columns removed instead of pinned — the honest answer to a question the clip only papers over. **Where the three disagree and `sat. PITs` is non-zero, the band's width is UNQUOTABLE**: say so, or quote the drop-saturated figure and say that is what it is. Measured on `reference` ranks 4-12 over Johannesburg alone, the three read 1.55 / 1.07 / 1.10 — the same band, two different verdicts. MODEL-LOG §1.132, §1.134.


**Read the last column, not the `SD of z` column, on ranks 13+.** `sd(z)` is exact under a level shift and **meaningless on a near-degenerate discrete column**: where the forecast is roughly Bernoulli(p) and the truth is zero, `z = −√(p/(1−p))` exactly, a function of the forecast probability with no room to spread. On the 96 ranks-13+ columns whose truth is zero, observed `z` correlates with that expression at **+0.93**. probit-SD comes from the randomised PIT, which is uniform under calibration whatever the support, and is the one to read there — at the cost of being attenuated by a level shift, so it is a LOWER BOUND wherever `mean z` is far from zero. Neither statistic is right everywhere; the pair is. MODEL-LOG §1.58.

**Ranks 1-3 are the same columns in both populations** — the top three are always claimed — so that row is a consistency check and the two `SD of z` numbers should agree exactly. It is also the band that is genuinely too WIDE and the band that responds to `dirichlet_scale`.

**Ranks 4-12 cannot be described by one width, and that is the finding.** On the same columns `sd(z)` says far too narrow, `IQR-sd` says too wide, and probit-SD disagrees with both — because the error distribution is a narrow shifted bulk with a few enormous outliers, which `claimed` excludes by construction. They are NAMED below, from the rows actually scored. A distribution that reads differently depending which moment you take is mis-SHAPED, not mis-scaled, and no scalar fixes it.


⛔ **AND THE SPREAD AT 4-12 IS A HANDFUL OF COLUMNS.** On the `reference` population over the 183 columns carrying a defined `z`, the two largest carry **58.1%** of the band's total squared `z`: **Johannesburg 2021 PA** (z +23.46, 38.3% of the band's squared deviation); **Cape Town 2021 CAPE_COLOURED_CONGRESS** (z +17.02, 19.8% of the band's squared deviation). Dropping them takes `sd(z)` from 2.744 to **1.773**. Quote the leave-the-largest-out figure beside the headline or the headline is two observations, not a width. §1.56, §1.58, §1.131.

**`probit-SD` is the one to quote when only a PIT is available.** It is `sd(Φ⁻¹(u))`, and under a location shift of a roughly normal forecast `Φ⁻¹(u)` translates — the shift lands in the mean, not the spread. `exact SD of z` is `(truth − forecast mean) / forecast sd` per column, centred, which is invariant to a shift by construction; it reads `—` on an artefact written before `calibration_columns` stored the `z` column, and it is the number to prefer when it is there. The standardised bias is the LEVEL, kept in its own column so that it can never be read as width again.

**The last column is printed to show it failing.** PIT variance against a nominal 1/12 has been proposed on this project as "shift-invariant, therefore a clean width statistic". **It is neither.** A PIT lives on [0, 1]; move the forecast off centre and its mass piles against a boundary and the variance falls whatever the width is. On the suite's fixture whose width is exactly right (`tests/test_calibration_report.py::_shift_scale_results`) it reads 0.0829, 0.0450 and 0.0240 at truth shifts of 0, +2 and +3 seats against a nominal 0.0833 — a pure level error reading as a 3.5× under-dispersion, which is the wrong diagnosis with the wrong remedy. Do not quote it as a width statistic; it is here so that nobody rediscovers it as one.

Per city-year, for provenance only — **every n below is too small to read, and none of these rows is evidence of anything on its own.**

| city-year | n claimed | 50% | 80% | 90% | mean PIT (claimed) |
|---|---|---|---|---|---|
| Johannesburg 2011 | 11 | 45% | 82% | 91% | 0.317 |
| Johannesburg 2016 | 11 | 100% | 100% | 100% | 0.392 |
| Johannesburg 2021 | 13 | 38% | 69% | 77% | 0.565 |
| Tshwane 2011 | 10 | 30% | 40% | 50% | 0.246 |
| Tshwane 2016 | 10 | 100% | 100% | 100% | 0.358 |
| Tshwane 2021 | 8 | 62% | 88% | 100% | 0.521 |
| Ekurhuleni 2011 | 12 | 42% | 67% | 75% | 0.315 |
| Ekurhuleni 2016 | 11 | 100% | 100% | 100% | 0.404 |
| Ekurhuleni 2021 | 11 | 73% | 100% | 100% | 0.579 |
| eThekwini 2011 | 8 | 62% | 75% | 75% | 0.247 |
| eThekwini 2016 | 9 | 89% | 89% | 89% | 0.441 |
| eThekwini 2021 | 16 | 75% | 100% | 100% | 0.548 |
| Cape Town 2011 | 11 | 73% | 91% | 91% | 0.379 |
| Cape Town 2016 | 10 | 90% | 100% | 100% | 0.592 |
| Cape Town 2021 | 10 | 80% | 90% | 100% | 0.636 |
| Mangaung 2011 | 7 | 29% | 71% | 71% | 0.338 |
| Mangaung 2016 | 6 | 100% | 100% | 100% | 0.392 |
| Mangaung 2021 | 8 | 88% | 88% | 100% | 0.445 |
| Nelson Mandela Bay 2011 | 9 | 56% | 78% | 78% | 0.369 |
| Nelson Mandela Bay 2016 | 8 | 100% | 100% | 100% | 0.616 |
| Nelson Mandela Bay 2021 | 9 | 89% | 100% | 100% | 0.383 |
| Buffalo City 2011 | 7 | 29% | 57% | 57% | 0.534 |
| Buffalo City 2016 | 8 | 88% | 100% | 100% | 0.517 |
| Buffalo City 2021 | 8 | 75% | 100% | 100% | 0.545 |


## Johannesburg 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 55.78% | 55.39% | 59.29% | 56.64% | 57.82% | 147 | 153 |
| DA | 26.08% | 26.60% | 34.35% | 27.48% | 34.90% | 69 | 90 |
| IFP | 2.59% | 2.70% | 1.61% | 2.63% | 1.66% | 7 | 4 |
| COPE | 8.82% | 9.68% | 1.11% | 9.44% | 1.19% | 23 | 3 |
| NFP | 0.00% | 1.30% | 0.82% | 0.00% | 0.74% | 0 | 2 |
| APC | 0.15% | 0.16% | 0.53% | 0.16% | 0.39% | 0 | 1 |
| ACDP | 0.83% | 0.86% | 0.40% | 0.81% | 0.44% | 2 | 1 |
| PAC | 0.52% | 0.55% | 0.35% | 0.67% | 0.43% | 2 | 1 |
| ALJAMAAH | nan% | nan% | 0.27% | nan% | 0.19% | 0 | 1 |
| OKM | 0.51% | 0.58% | 0.25% | 0.13% | 0.15% | 1 | 1 |
| VFPLUS | 0.79% | 0.82% | 0.23% | 0.85% | 0.27% | 2 | 1 |
| UDM | 0.35% | 0.36% | 0.22% | 0.36% | 0.25% | 1 | 1 |

## Johannesburg 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 45.86% | 45.24% | 44.92% | 44.43% | 44.09% | 123 | 121 |
| DA | 40.43% | 39.86% | 38.48% | 40.77% | 38.34% | 111 | 104 |
| EFF | 6.06% | 8.56% | 10.93% | 8.84% | 11.24% | 17 | 30 |
| IFP | 1.05% | 1.26% | 1.71% | 1.28% | 1.74% | 3 | 5 |
| AIC | 0.09% | 0.17% | 1.62% | 0.17% | 1.40% | 0 | 4 |
| ACDP | 0.39% | 0.50% | 0.31% | 0.53% | 0.28% | 1 | 1 |
| VFPLUS | 0.29% | 0.37% | 0.31% | 0.45% | 0.34% | 1 | 1 |
| ALJAMAAH | 0.11% | 0.14% | 0.31% | 0.12% | 0.22% | 0 | 1 |
| UDM | 0.26% | 0.33% | 0.25% | 0.37% | 0.28% | 1 | 1 |
| COPE | 0.16% | 0.21% | 0.21% | 0.13% | 0.15% | 0 | 1 |
| PA | 0.04% | 0.09% | 0.17% | 0.09% | 0.13% | 0 | 1 |
| PAC | 0.29% | 0.37% | 0.17% | 0.12% | 0.09% | 1 | 0 |

**Missed entirely:** AIC — won seats, median zero.

## Johannesburg 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 39.19% | 38.85% | 33.22% | 39.16% | 33.97% | 106 | 91 |
| DA | 32.96% | 32.72% | 25.45% | 33.49% | 26.83% | 90 | 71 |
| ASA | 4.22% | 6.89% | 18.12% | 5.82% | 13.98% | 11 | 44 |
| EFF | 13.71% | 13.68% | 10.11% | 14.46% | 11.14% | 38 | 29 |
| PA | 0.06% | 0.08% | 2.96% | 0.07% | 2.91% | 0 | 8 |
| IFP | 1.03% | 1.33% | 2.36% | 1.43% | 2.36% | 3 | 7 |
| VFPLUS | 0.66% | 0.85% | 1.33% | 0.94% | 1.35% | 2 | 4 |
| ACDP | 0.43% | 0.56% | 1.03% | 0.58% | 1.08% | 1 | 3 |
| ALJAMAAH | 0.22% | 0.30% | 0.83% | 0.23% | 1.08% | 1 | 3 |
| AIC | 0.54% | 0.74% | 0.69% | 0.39% | 0.50% | 1 | 2 |
| AHC | 0.04% | 0.09% | 0.43% | 0.07% | 0.47% | 0 | 1 |
| GOOD | 0.19% | 0.38% | 0.33% | 0.31% | 0.40% | 1 | 1 |

**Missed entirely:** PA — won seats, median zero.

## Tshwane 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 51.07% | 51.21% | 56.46% | 51.52% | 54.18% | 108 | 118 |
| DA | 29.74% | 30.01% | 38.74% | 31.20% | 38.56% | 64 | 82 |
| VFPLUS | 4.89% | 5.07% | 1.59% | 5.30% | 1.73% | 11 | 4 |
| COPE | 6.95% | 7.79% | 0.89% | 7.39% | 0.92% | 14 | 2 |
| ACDP | 1.29% | 1.34% | 0.59% | 1.47% | 0.67% | 3 | 1 |
| APC | 0.15% | 0.17% | 0.46% | 0.16% | 0.35% | 0 | 1 |
| PAC | 0.48% | 0.50% | 0.25% | 0.64% | 0.28% | 1 | 1 |
| AZAPO | 0.38% | 0.39% | 0.18% | 0.41% | 0.21% | 1 | 1 |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | 0.78% | 0.81% | 0.15% | 0.54% | 0.12% | 1 | 0 |
| IFP | 0.20% | 0.21% | 0.12% | 0.18% | 0.13% | 0 | 0 |
| CHRISTIAN_DEMOCRATIC_PARTY | 0.32% | 0.33% | 0.11% | 0.34% | 0.13% | 1 | 0 |
| INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA | nan% | nan% | 0.09% | nan% | 0.05% | 0 | 0 |

## Tshwane 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 41.84% | 41.05% | 43.10% | 41.49% | 43.20% | 90 | 93 |
| ANC | 43.11% | 42.27% | 41.48% | 41.10% | 41.02% | 91 | 89 |
| EFF | 6.93% | 9.88% | 11.64% | 10.47% | 11.62% | 15 | 25 |
| VFPLUS | 1.89% | 2.22% | 1.97% | 2.44% | 2.02% | 4 | 4 |
| ACDP | 0.57% | 0.70% | 0.47% | 0.81% | 0.52% | 1 | 1 |
| APC | 0.31% | 0.37% | 0.24% | 0.09% | 0.05% | 0 | 0 |
| COPE | 0.14% | 0.18% | 0.22% | 0.19% | 0.27% | 0 | 1 |
| PAC | 0.25% | 0.32% | 0.14% | 0.34% | 0.20% | 1 | 1 |
| UDM | 0.14% | 0.18% | 0.13% | 0.21% | 0.10% | 0 | 0 |
| IFP | 0.09% | 0.11% | 0.10% | 0.02% | 0.02% | 0 | 0 |
| AFRICAN_MANDATE_CONGRESS | 0.19% | 0.36% | 0.09% | 0.39% | 0.06% | 0 | 0 |
| PA | 0.03% | 0.06% | 0.09% | 0.06% | 0.05% | 0 | 0 |

## Tshwane 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 37.01% | 36.76% | 34.84% | 36.58% | 34.42% | 79 | 75 |
| DA | 33.41% | 33.28% | 31.77% | 33.49% | 32.29% | 72 | 69 |
| EFF | 14.39% | 14.31% | 10.43% | 14.34% | 10.94% | 31 | 23 |
| ASA | 3.17% | 5.70% | 9.28% | 5.33% | 7.99% | 7 | 19 |
| VFPLUS | 4.02% | 4.89% | 7.79% | 5.02% | 7.96% | 9 | 17 |
| ACDP | 0.57% | 0.76% | 0.91% | 0.83% | 0.93% | 1 | 2 |
| AIC | 0.35% | 0.59% | 0.81% | 0.55% | 0.38% | 1 | 1 |
| DOP | 0.05% | 0.10% | 0.49% | 0.09% | 0.58% | 0 | 1 |
| PA | 0.03% | 0.04% | 0.48% | 0.07% | 0.52% | 0 | 1 |
| PAC | 0.18% | 0.23% | 0.21% | 0.28% | 0.18% | 1 | 1 |
| IFP | 0.09% | 0.12% | 0.21% | 0.24% | 0.09% | 0 | 1 |
| COPE | 0.08% | 0.10% | 0.19% | 0.12% | 0.20% | 0 | 1 |

## Ekurhuleni 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 57.87% | 57.33% | 62.17% | 58.69% | 61.08% | 118 | 125 |
| DA | 25.22% | 25.64% | 30.13% | 26.05% | 30.46% | 51 | 62 |
| IFP | 2.03% | 2.11% | 1.16% | 1.73% | 1.04% | 4 | 2 |
| NFP | 0.00% | 1.31% | 1.13% | 0.00% | 1.19% | 0 | 3 |
| COPE | 5.70% | 6.44% | 1.09% | 6.12% | 0.79% | 11 | 2 |
| APC | 0.20% | 0.23% | 0.68% | 0.21% | 0.54% | 0 | 1 |
| PAC | 0.66% | 0.69% | 0.61% | 0.71% | 0.75% | 1 | 2 |
| ACDP | 1.04% | 1.08% | 0.59% | 1.05% | 0.67% | 2 | 1 |
| VFPLUS | 1.56% | 1.64% | 0.51% | 1.56% | 0.59% | 3 | 1 |
| UDM | 0.40% | 0.41% | 0.42% | 0.42% | 0.51% | 1 | 1 |
| DISPLACEES_RATE_PAYERS_ASSOCIATION | 1.51% | 1.67% | 0.41% | 1.90% | 0.48% | 3 | 1 |
| INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA | 0.40% | 0.45% | 0.32% | 0.89% | 0.78% | 1 | 1 |

**Missed entirely:** NFP — won seats, median zero.

## Ekurhuleni 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 48.88% | 48.10% | 48.84% | 46.94% | 48.44% | 108 | 109 |
| DA | 37.05% | 36.44% | 34.13% | 36.64% | 34.17% | 83 | 77 |
| EFF | 6.15% | 8.85% | 11.10% | 9.79% | 11.35% | 15 | 25 |
| AIC | 0.08% | 0.17% | 1.65% | 0.19% | 1.63% | 0 | 4 |
| IFP | 0.72% | 0.90% | 1.04% | 0.78% | 0.99% | 2 | 2 |
| VFPLUS | 0.72% | 0.88% | 0.90% | 1.03% | 0.89% | 2 | 2 |
| ACDP | 0.51% | 0.64% | 0.42% | 0.74% | 0.43% | 1 | 1 |
| PAC | 0.39% | 0.50% | 0.42% | 0.28% | 0.43% | 1 | 1 |
| COPE | 0.13% | 0.17% | 0.28% | 0.14% | 0.25% | 0 | 1 |
| PA | 0.02% | 0.04% | 0.28% | 0.05% | 0.25% | 0 | 1 |
| APC | 0.36% | 0.47% | 0.27% | 0.15% | 0.06% | 1 | 0 |
| UDM | 0.26% | 0.33% | 0.23% | 0.30% | 0.16% | 1 | 0 |

**Missed entirely:** AIC — won seats, median zero.

## Ekurhuleni 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 43.23% | 43.01% | 38.34% | 42.64% | 38.03% | 97 | 86 |
| DA | 29.94% | 29.81% | 28.37% | 29.80% | 29.07% | 67 | 65 |
| EFF | 13.80% | 13.86% | 13.27% | 14.15% | 13.87% | 31 | 31 |
| ASA | 2.13% | 4.06% | 7.36% | 4.01% | 5.84% | 5 | 15 |
| VFPLUS | 2.22% | 2.77% | 3.48% | 2.74% | 3.18% | 5 | 8 |
| PA | 0.14% | 0.18% | 1.87% | 0.20% | 1.89% | 0 | 4 |
| IFP | 0.81% | 1.07% | 1.47% | 1.05% | 1.24% | 2 | 3 |
| AIC | 0.63% | 0.79% | 1.36% | 0.86% | 1.22% | 2 | 3 |
| ACDP | 0.49% | 0.62% | 0.86% | 0.64% | 0.82% | 1 | 2 |
| INDEPENDENT_CITIZENS_MOVEMENT | 0.06% | 0.13% | 0.45% | 0.13% | 0.44% | 0 | 1 |
| PAC | 0.31% | 0.41% | 0.43% | 0.40% | 0.31% | 1 | 1 |
| INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA | 0.07% | 0.10% | 0.36% | 0.20% | 0.78% | 0 | 1 |

**Missed entirely:** PA — won seats, median zero.

## eThekwini 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 58.51% | 58.33% | 62.02% | 59.06% | 60.11% | 121 | 126 |
| DA | 19.99% | 20.41% | 21.81% | 20.41% | 20.21% | 41 | 43 |
| MINORITY_FRONT | 5.80% | 6.02% | 4.94% | 6.32% | 5.68% | 12 | 11 |
| NFP | 0.00% | 1.23% | 4.48% | 0.00% | 4.92% | 0 | 10 |
| IFP | 8.05% | 8.36% | 3.96% | 8.57% | 4.30% | 17 | 9 |
| ACDP | 1.17% | 1.22% | 0.67% | 1.32% | 0.80% | 3 | 2 |
| TRULY_ALLIANCE | 0.81% | 0.91% | 0.62% | 0.99% | 0.83% | 2 | 1 |
| APC | 0.18% | 0.20% | 0.41% | 0.20% | 0.20% | 0 | 1 |
| COPE | 2.33% | 2.59% | 0.40% | 2.55% | 0.35% | 5 | 1 |
| UNITED_ACTION_FRONT | nan% | nan% | 0.13% | nan% | 0.21% | 0 | 0 |
| AZAPO | 0.33% | 0.35% | 0.13% | 0.29% | 0.14% | 1 | 0 |
| UDM | 0.21% | 0.21% | 0.11% | 0.16% | 0.15% | 0 | 0 |

**Missed entirely:** NFP — won seats, median zero.

## eThekwini 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 57.69% | 57.60% | 59.11% | 57.06% | 52.95% | 126 | 126 |
| DA | 28.92% | 28.79% | 27.54% | 27.82% | 26.30% | 62 | 61 |
| IFP | 3.05% | 3.45% | 4.28% | 3.78% | 4.12% | 7 | 10 |
| EFF | 1.70% | 2.78% | 3.63% | 3.11% | 3.26% | 4 | 8 |
| AIC | 0.07% | 0.15% | 1.51% | 0.17% | 1.23% | 0 | 3 |
| ACDP | 0.49% | 0.63% | 0.54% | 0.76% | 0.55% | 1 | 1 |
| MINORITY_FRONT | 2.88% | 3.21% | 0.46% | 3.76% | 0.60% | 7 | 1 |
| DEMOCRATIC_LIBERAL_CONGRESS | 0.07% | 0.14% | 0.43% | 0.16% | 0.60% | 0 | 1 |
| TRULY_ALLIANCE | 0.35% | 0.46% | 0.42% | 0.62% | 0.40% | 1 | 1 |
| MINORITIES_OF_SOUTH_AFRICA | 0.07% | 0.14% | 0.27% | 0.15% | 0.35% | 0 | 1 |
| APC | 0.27% | 0.34% | 0.26% | 0.21% | 0.15% | 1 | 1 |
| ALJAMAAH | 0.07% | 0.13% | 0.18% | 0.14% | 0.20% | 0 | 1 |

**Missed entirely:** AIC, IND — won seats, median zero.

## eThekwini 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 46.69% | 46.50% | 42.51% | 45.31% | 41.77% | 102 | 96 |
| DA | 28.39% | 28.45% | 26.33% | 29.55% | 25.57% | 65 | 59 |
| EFF | 10.57% | 10.71% | 10.80% | 10.51% | 10.15% | 23 | 24 |
| IFP | 3.91% | 4.74% | 7.45% | 5.05% | 6.67% | 9 | 16 |
| ASA | 0.60% | 1.06% | 2.35% | 1.04% | 1.50% | 1 | 4 |
| AIC | 0.66% | 0.86% | 1.01% | 0.32% | 0.33% | 1 | 2 |
| ACTIVE_CITIZENS_COALITION | 0.06% | 0.12% | 0.81% | 0.12% | 1.03% | 0 | 2 |
| ACDP | 0.50% | 0.68% | 0.76% | 0.75% | 0.78% | 1 | 2 |
| ABANTU_BATHO_CONGRESS | 0.05% | 0.10% | 0.65% | 0.10% | 0.76% | 0 | 2 |
| JUSTICE_AND_EMPLOYMENT_PARTY | 0.17% | 0.31% | 0.61% | 0.30% | 0.51% | 1 | 1 |
| ATM | 0.35% | 0.67% | 0.57% | 0.65% | 0.66% | 1 | 1 |
| MINORITY_FRONT | 0.53% | 0.69% | 0.50% | 0.98% | 0.47% | 2 | 1 |

## Cape Town 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 58.23% | 57.80% | 61.15% | 59.09% | 60.69% | 130 | 135 |
| ANC | 27.08% | 27.51% | 33.17% | 27.40% | 32.44% | 60 | 73 |
| COPE | 6.44% | 7.08% | 1.13% | 7.16% | 1.08% | 14 | 3 |
| ACDP | 1.67% | 1.71% | 1.06% | 1.87% | 1.37% | 4 | 3 |
| NATIONAL_PARTY_SOUTH_AFRICA | 0.20% | 0.22% | 0.54% | 0.22% | 0.51% | 1 | 1 |
| UDM | 0.57% | 0.59% | 0.38% | 0.41% | 0.40% | 1 | 1 |
| ALJAMAAH | 0.73% | 0.83% | 0.35% | 0.84% | 0.39% | 2 | 1 |
| AFRICA_MUSLIM_PARTY | 0.84% | 0.88% | 0.28% | 0.96% | 0.40% | 2 | 1 |
| CAPE_MUSLIM_CONGRESS | 0.00% | 1.37% | 0.25% | 0.00% | 0.33% | 0 | 1 |
| PAC | 0.50% | 0.52% | 0.18% | 0.52% | 0.23% | 1 | 1 |
| VFPLUS | 0.42% | 0.44% | 0.17% | 0.46% | 0.19% | 1 | 1 |
| DEMOCRATS_FOR_CHANGE | nan% | nan% | 0.15% | nan% | 0.08% | 0 | 0 |

## Cape Town 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 67.11% | 66.77% | 66.75% | 66.73% | 66.46% | 155 | 154 |
| ANC | 25.23% | 25.40% | 24.52% | 24.84% | 24.20% | 58 | 57 |
| EFF | 1.33% | 2.36% | 3.12% | 2.56% | 3.22% | 3 | 7 |
| ACDP | 0.76% | 0.93% | 1.13% | 1.15% | 1.29% | 2 | 3 |
| AIC | 0.22% | 0.46% | 0.76% | 0.51% | 0.42% | 1 | 1 |
| ALJAMAAH | 0.26% | 0.34% | 0.55% | 0.38% | 0.76% | 1 | 2 |
| VFPLUS | 0.22% | 0.29% | 0.39% | 0.34% | 0.43% | 1 | 1 |
| UDM | 0.28% | 0.36% | 0.33% | 0.26% | 0.20% | 1 | 1 |
| DEMOCRATIC_INDEPENDENT_PARTY | 0.04% | 0.09% | 0.28% | 0.10% | 0.32% | 0 | 1 |
| CAPE_MUSLIM_CONGRESS | 0.08% | 0.11% | 0.27% | 0.15% | 0.25% | 0 | 1 |
| COPE | 0.11% | 0.15% | 0.24% | 0.14% | 0.25% | 0 | 1 |
| PAC | 0.24% | 0.30% | 0.24% | 0.37% | 0.27% | 1 | 1 |

## Cape Town 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 61.68% | 61.12% | 58.74% | 60.74% | 57.78% | 142 | 135 |
| ANC | 22.66% | 22.64% | 18.71% | 22.44% | 18.46% | 52 | 43 |
| EFF | 3.96% | 4.83% | 4.15% | 4.96% | 4.10% | 9 | 10 |
| GOOD | 1.77% | 3.19% | 3.68% | 3.09% | 3.94% | 4 | 9 |
| CAPE_COLOURED_CONGRESS | 0.04% | 0.08% | 2.83% | 0.08% | 2.78% | 0 | 7 |
| ACDP | 1.78% | 2.33% | 2.29% | 2.73% | 2.40% | 5 | 6 |
| VFPLUS | 0.68% | 0.89% | 1.54% | 0.96% | 1.63% | 2 | 4 |
| PA | 0.08% | 0.11% | 1.43% | 0.14% | 1.54% | 0 | 4 |
| ALJAMAAH | 0.60% | 0.79% | 1.19% | 1.08% | 1.32% | 2 | 3 |
| AFRICA_RESTORATION_ALLIANCE | 0.04% | 0.09% | 0.64% | 0.08% | 0.81% | 0 | 2 |
| CAPE_INDEPENDENCE_PARTY_KAAPSE_ONAFHANKLIKHEIDS_PARTY | 0.04% | 0.08% | 0.62% | 0.08% | 0.65% | 0 | 2 |
| UIM | 0.04% | 0.07% | 0.56% | 0.07% | 0.58% | 0 | 1 |

**Missed entirely:** CAPE_COLOURED_CONGRESS, PA — won seats, median zero.

## Mangaung 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 58.79% | 58.36% | 66.57% | 60.89% | 65.96% | 58 | 65 |
| DA | 18.97% | 19.41% | 26.82% | 20.77% | 27.40% | 19 | 26 |
| COPE | 12.91% | 13.76% | 3.30% | 11.77% | 3.02% | 11 | 3 |
| VFPLUS | 4.17% | 4.37% | 1.40% | 4.83% | 1.62% | 4 | 2 |
| ACDP | 1.02% | 1.05% | 0.56% | 0.45% | 0.29% | 1 | 0 |
| APC | 0.26% | 0.30% | 0.55% | 0.26% | 0.39% | 0 | 1 |
| PAC | 0.66% | 0.68% | 0.26% | 0.52% | 0.21% | 1 | 0 |
| DIKWANKWETLA_PARTY_OF_SOUTH_AFRICA | 0.59% | 0.62% | 0.25% | 0.52% | 0.22% | 1 | 0 |
| BLACK_CONSCIOUSNESS_PARTY | nan% | nan% | 0.15% | nan% | 0.09% | 0 | 0 |
| UNITED_RESIDENTS_FRONT | nan% | nan% | 0.14% | nan% | 0.20% | 0 | 0 |

## Mangaung 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 58.65% | 57.67% | 56.77% | 57.51% | 56.28% | 59 | 58 |
| DA | 27.90% | 27.70% | 26.20% | 28.49% | 25.73% | 28 | 27 |
| EFF | 5.34% | 7.82% | 8.84% | 7.10% | 8.48% | 5 | 9 |
| AIC | 0.23% | 0.43% | 2.74% | 0.38% | 0.64% | 0 | 2 |
| VFPLUS | 2.00% | 2.28% | 1.85% | 2.66% | 1.99% | 2 | 2 |
| AGENCY_FOR_NEW_AGENDA | 0.25% | 0.49% | 1.57% | 0.42% | 0.21% | 0 | 1 |
| COPE | 0.55% | 0.68% | 0.56% | 0.72% | 0.63% | 1 | 1 |
| ACDP | 0.46% | 0.60% | 0.39% | 0.71% | 0.39% | 1 | 0 |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | 0.12% | 0.24% | 0.28% | 0.21% | 0.11% | 0 | 0 |
| APC | 0.43% | 0.54% | 0.25% | 0.45% | 0.17% | 0 | 0 |
| AZANIAN_ALLIANCE_CONGRESS | 0.26% | 0.51% | 0.13% | 0.45% | 0.06% | 0 | 0 |
| BOTSHABELO_UNEMPLOYED_MOVEMENT | 0.24% | 0.46% | 0.12% | 0.41% | 0.09% | 0 | 0 |

## Mangaung 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 49.41% | 49.10% | 51.51% | 48.76% | 49.75% | 50 | 51 |
| DA | 26.32% | 26.33% | 25.48% | 25.90% | 25.98% | 26 | 26 |
| EFF | 12.20% | 12.26% | 11.37% | 11.77% | 11.24% | 12 | 12 |
| VFPLUS | 2.76% | 3.53% | 4.41% | 3.80% | 4.55% | 3 | 5 |
| PA | 0.98% | 1.65% | 1.78% | 1.58% | 1.83% | 1 | 2 |
| AFRIKAN_ALLIANCE_OF_SOCIAL_DEMOCRATS | 0.19% | 0.35% | 1.26% | 0.34% | 1.61% | 0 | 2 |
| AIC | 1.09% | 1.44% | 0.84% | 2.33% | 1.70% | 2 | 1 |
| ACDP | 0.45% | 0.62% | 0.70% | 0.64% | 0.74% | 1 | 1 |
| ATM | 0.33% | 0.62% | 0.61% | 0.60% | 0.58% | 0 | 1 |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | 0.11% | 0.15% | 0.38% | 0.16% | 0.38% | 0 | 0 |
| COPE | 0.14% | 0.18% | 0.30% | 0.09% | 0.16% | 0 | 0 |
| MANGAUNG_COMMUNITY_FORUM | 0.15% | 0.30% | 0.21% | 0.28% | 0.02% | 0 | 0 |

## Nelson Mandela Bay 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 44.29% | 44.50% | 52.13% | 44.94% | 51.69% | 53 | 63 |
| DA | 32.73% | 33.31% | 40.24% | 34.33% | 40.02% | 40 | 48 |
| COPE | 15.79% | 16.73% | 4.88% | 16.41% | 5.01% | 19 | 6 |
| UDM | 0.64% | 0.66% | 0.54% | 0.61% | 0.55% | 1 | 1 |
| PAC | 0.66% | 0.68% | 0.52% | 0.75% | 0.57% | 1 | 1 |
| APC | 0.11% | 0.12% | 0.43% | 0.12% | 0.01% | 0 | 0 |
| ACDP | 0.71% | 0.74% | 0.36% | 0.78% | 0.40% | 1 | 1 |
| AZAPO | 0.54% | 0.57% | 0.28% | 0.49% | 0.22% | 1 | 0 |
| VFPLUS | 0.72% | 0.75% | 0.20% | 0.90% | 0.25% | 1 | 0 |
| CHRISTIAN_DEMOCRATIC_PARTY | nan% | nan% | 0.16% | nan% | 0.18% | 0 | 0 |
| AFRICAN_COMMUNITY_MOVEMENT | nan% | nan% | 0.14% | nan% | 0.18% | 0 | 0 |
| UNITED_INDEPENDENT_FRONT | 0.51% | 0.57% | 0.06% | 0.67% | 0.08% | 1 | 0 |

## Nelson Mandela Bay 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 47.88% | 47.52% | 46.66% | 48.11% | 46.75% | 58 | 57 |
| ANC | 41.57% | 41.25% | 41.50% | 40.59% | 40.34% | 50 | 50 |
| EFF | 2.52% | 4.28% | 5.03% | 4.45% | 5.21% | 3 | 6 |
| UDM | 0.86% | 1.04% | 1.83% | 1.08% | 2.00% | 1 | 2 |
| AIC | 0.55% | 1.11% | 1.61% | 1.16% | 0.28% | 1 | 1 |
| UNITED_FRONT_OF_THE_EASTERN_CAPE | 0.19% | 0.42% | 0.80% | 0.43% | 1.09% | 0 | 1 |
| COPE | 0.57% | 0.69% | 0.70% | 0.71% | 0.77% | 1 | 1 |
| ACDP | 0.36% | 0.45% | 0.35% | 0.52% | 0.37% | 1 | 1 |
| PA | 0.08% | 0.16% | 0.29% | 0.16% | 0.24% | 0 | 1 |
| ALTERNATIVE_DEMOCRATS | 0.14% | 0.27% | 0.25% | 0.28% | 0.08% | 0 | 0 |
| VFPLUS | 0.41% | 0.52% | 0.25% | 0.65% | 0.26% | 1 | 0 |
| PAC | 0.50% | 0.62% | 0.23% | 0.22% | 0.12% | 0 | 0 |

## Nelson Mandela Bay 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 45.37% | 45.19% | 40.04% | 45.14% | 39.80% | 54 | 48 |
| ANC | 38.08% | 38.01% | 39.60% | 37.51% | 39.26% | 45 | 48 |
| EFF | 7.39% | 7.87% | 6.40% | 8.14% | 6.40% | 9 | 8 |
| NORTHERN_ALLIANCE | 0.09% | 0.19% | 2.09% | 0.20% | 2.18% | 0 | 3 |
| ACDP | 0.78% | 1.07% | 1.68% | 1.13% | 1.64% | 1 | 2 |
| VFPLUS | 0.95% | 1.22% | 1.64% | 1.26% | 1.51% | 1 | 2 |
| DOP | 0.09% | 0.17% | 1.38% | 0.18% | 1.47% | 0 | 2 |
| PA | 0.16% | 0.21% | 1.32% | 0.22% | 1.42% | 0 | 2 |
| ABANTU_INTEGRITY_MOVEMENT | 0.08% | 0.18% | 1.11% | 0.18% | 1.05% | 0 | 1 |
| UDM | 0.62% | 0.82% | 1.07% | 0.92% | 1.01% | 1 | 1 |
| AIC | 0.67% | 0.85% | 0.68% | 0.75% | 0.38% | 1 | 1 |
| PAC | 0.29% | 0.37% | 0.51% | 0.34% | 0.48% | 0 | 1 |

**Missed entirely:** NORTHERN_ALLIANCE — won seats, median zero.

## Buffalo City 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 62.87% | 62.31% | 69.13% | 64.61% | 70.88% | 64 | 71 |
| DA | 14.59% | 14.99% | 20.26% | 16.33% | 20.71% | 15 | 21 |
| COPE | 15.30% | 16.35% | 3.70% | 12.89% | 2.02% | 14 | 3 |
| AIC | 0.64% | 0.71% | 3.58% | 0.56% | 0.17% | 1 | 2 |
| PAC | 1.70% | 1.75% | 1.66% | 2.05% | 2.11% | 2 | 2 |
| UDM | 0.89% | 0.94% | 0.74% | 1.95% | 0.53% | 1 | 0 |
| ACDP | 1.24% | 1.28% | 0.70% | 1.40% | 0.79% | 1 | 1 |
| PAN_AFRICANIST_MOVEMENT | 0.24% | 0.27% | 0.23% | 0.21% | 0.13% | 0 | 0 |

## Buffalo City 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 60.74% | 59.98% | 59.86% | 60.57% | 57.63% | 61 | 60 |
| DA | 25.42% | 25.38% | 23.45% | 25.59% | 23.35% | 26 | 24 |
| EFF | 3.49% | 5.24% | 8.21% | 4.54% | 7.74% | 3 | 8 |
| AIC | 1.78% | 2.08% | 3.89% | 4.08% | 2.95% | 3 | 4 |
| UDM | 2.32% | 2.62% | 1.29% | 0.72% | 0.45% | 2 | 1 |
| COPE | 0.32% | 0.41% | 0.99% | 0.36% | 0.72% | 0 | 1 |
| PAC | 1.20% | 1.44% | 0.98% | 1.57% | 0.82% | 1 | 1 |
| ACDP | 0.47% | 0.58% | 0.55% | 0.70% | 0.56% | 1 | 1 |
| UNITED_FRONT_OF_THE_EASTERN_CAPE | 0.49% | 0.93% | 0.32% | 0.80% | 0.27% | 0 | 0 |
| PAN_AFRICANIST_MOVEMENT | 0.10% | 0.12% | 0.20% | 0.06% | 0.04% | 0 | 0 |
| PEOPLES_ALLIANCE | 0.55% | 1.04% | 0.16% | 0.86% | 0.02% | 1 | 0 |
| UNITED_CONGRESS | 0.09% | 0.18% | 0.10% | 0.15% | 0.09% | 0 | 0 |

## Buffalo City 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 56.99% | 56.85% | 60.51% | 57.36% | 58.35% | 57 | 61 |
| DA | 22.45% | 22.45% | 19.49% | 23.45% | 19.55% | 23 | 20 |
| EFF | 12.27% | 12.43% | 12.37% | 12.29% | 11.76% | 12 | 13 |
| UDM | 0.61% | 0.80% | 1.10% | 1.17% | 0.82% | 1 | 1 |
| PAC | 0.85% | 1.12% | 1.05% | 1.01% | 0.83% | 1 | 1 |
| AIC | 1.19% | 1.53% | 0.97% | 0.46% | 0.45% | 1 | 1 |
| ATM | 0.53% | 0.96% | 0.89% | 0.86% | 0.93% | 1 | 1 |
| ACDP | 0.47% | 0.64% | 0.57% | 0.69% | 0.55% | 1 | 1 |
| VFPLUS | 0.23% | 0.44% | 0.52% | 0.39% | 0.51% | 0 | 1 |
| PA | 0.07% | 0.14% | 0.42% | 0.12% | 0.19% | 0 | 0 |
| INDEPENDENT_SOUTH_AFRICAN_NATIONAL_CIVIC_ORGANISATION | 0.08% | 0.16% | 0.34% | 0.14% | 0.10% | 0 | 0 |
| COPE | 0.09% | 0.12% | 0.27% | 0.01% | 0.05% | 0 | 0 |