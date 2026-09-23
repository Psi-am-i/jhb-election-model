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
| Johannesburg 2011 | 260 | 5.06pp | 4.24pp | 56 | 244 | 60 | 41.4 | 52 | 60 | 56 | 56 |
| Johannesburg 2016 | 270 | 0.89pp | 1.27pp | 21 | 259 | 30 | 20.7 | 92 | 26 | 96 | 26 |
| Johannesburg 2021 | 270 | 6.29pp | 5.10pp | 96 | 252 | 86 | 69.4 | 134 | 126 | 130 | 128 |
| Tshwane 2011 | 210 | 6.51pp | 4.86pp | 46 | 196 | 60 | 32.5 | 40 | 56 | 46 | 56 |
| Tshwane 2016 | 214 | 1.20pp | 0.96pp | 15 | 209 | 16 | 12.9 | 70 | 10 | 76 | 16 |
| Tshwane 2021 | 214 | 2.04pp | 1.99pp | 36 | 202 | 34 | 27.4 | 80 | 60 | 80 | 60 |
| Ekurhuleni 2011 | 202 | 3.55pp | 2.48pp | 32 | 188 | 36 | 24.8 | 32 | 44 | 42 | 40 |
| Ekurhuleni 2016 | 224 | 1.71pp | 2.15pp | 18 | 212 | 28 | 17.7 | 80 | 22 | 80 | 16 |
| Ekurhuleni 2021 | 224 | 2.55pp | 2.20pp | 38 | 208 | 30 | 29.2 | 72 | 48 | 64 | 46 |
| eThekwini 2011 | 205 | 2.68pp | 1.89pp | 28 | 196 | 31 | 23.3 | 49 | 35 | 61 | 33 |
| eThekwini 2016 | 219 | 1.59pp | 2.69pp | 30 | 211 | 34 | 21.1 | 64 | 50 | 64 | 36 |
| eThekwini 2021 | 222 | 2.47pp | 2.66pp | 40 | 202 | 34 | 30.3 | 82 | 36 | 80 | 34 |
| Cape Town 2011 | 221 | 4.27pp | 3.69pp | 38 | 207 | 42 | 26.6 | 94 | 58 | 100 | 40 |
| Cape Town 2016 | 231 | 0.27pp | 0.50pp | 11 | 222 | 8 | 12.2 | 46 | 30 | 58 | 34 |
| Cape Town 2021 | 231 | 2.32pp | 2.50pp | 44 | 219 | 42 | 34.0 | 68 | 38 | 62 | 34 |
| Mangaung 2011 | 97 | 8.00pp | 8.13pp | 29 | 92 | 34 | 18.7 | 28 | 30 | 30 | 32 |
| Mangaung 2016 | 100 | 0.67pp | 1.15pp | 7 | 95 | 8 | 7.3 | 24 | 12 | 26 | 10 |
| Mangaung 2021 | 101 | 1.64pp | 0.67pp | 7 | 94 | 8 | 9.4 | 24 | 8 | 18 | 10 |
| Nelson Mandela Bay 2011 | 120 | 7.20pp | 6.76pp | 33 | 111 | 34 | 21.0 | 48 | 42 | 52 | 38 |
| Nelson Mandela Bay 2016 | 120 | 0.66pp | 0.96pp | 7 | 115 | 8 | 7.7 | 38 | 16 | 40 | 16 |
| Nelson Mandela Bay 2021 | 120 | 2.81pp | 2.99pp | 22 | 112 | 20 | 17.0 | 28 | 22 | 30 | 20 |
| Buffalo City 2011 | 100 | 7.16pp | 6.90pp | 32 | 90 | 32 | 19.9 | 28 | 30 | 28 | 30 |
| Buffalo City 2016 | 100 | 0.81pp | 2.75pp | 9 | 93 | 10 | 9.1 | 28 | 14 | 26 | 14 |
| Buffalo City 2021 | 100 | 3.14pp | 2.03pp | 12 | 92 | 8 | 7.9 | 14 | 12 | 16 | 12 |
| **TOTAL** [rows=24] | 4375 | — | — | **707** | — | **733** | **541.5** | 1315 | 885 | 1361 | 837 |

### Citable totals

**Quoting one number in a sentence? Paste this token, do not retype the figure:**

```
seat_abs_err_coherent=733/@2ac4c1eb/1000d/pools:7264a929/rows=24
```

The full set, for anything more than one number:

```
seat_abs_err_coherent = 733      [rows=24]
seat_abs_err          = 707      [rows=24]   # MARGINAL, not comparable to the line above
crps                  = 541.53   [rows=24]
n_scored              = 805      [rows=24]   # summed scoring columns. NOT a denominator: `crps` is a sum, and this count differs between forecasters (§1.141)
margin_vs_uniform_swing = 17.2%   [rows=24, coherent, vs a point forecast]
margin_vs_prior_lge_noise = 46.1% [rows=24, coherent, vs a probabilistic forecast — the only reference here that expresses uncertainty]
```

`seat_abs_err` and `seat_abs_err_coherent` are DIFFERENT STATISTICS. Quoting one against the other is §1.214.

**The references are not the same kind of forecast**, and the margins above are not the same kind of claim: `last-lge` is **point**; `uniform-swing` is **point**; `prior-lge-noise` is **probabilistic**; `uniform-swing+roster` is **point**. A margin over a point forecast says the central estimate is better; only a margin over a probabilistic one says anything about the intervals. Measured from the rows, not declared.

### The margin is not evenly spread

The margin below is against **uniform swing** — **uniform swing is a POINT forecast here**.

**A margin over a POINT forecast is a claim about the central estimate, not about uncertainty.** CRPS collapses to absolute error when a forecast expresses no spread, so for those references the CRPS column below is the same statistic as the seat-error column beside it, not an independent check. Only a reference marked *probabilistic* puts the model's intervals under any test at all.

| | city-years | seat err (coherent) | uniform-swing | margin | CRPS | uniform-swing CRPS (point) | margin |
|---|---|---|---|---|---|---|---|
| Gauteng (Ekurhuleni, Johannesburg, Tshwane) | 9 | 380 | 452 | 16% | 276.1 | 452.0 | 39% |
| everywhere else (Buffalo City, Cape Town, Mangaung, Nelson Mandela Bay, eThekwini) | 15 | 353 | 433 | 18% | 265.4 | 433.0 | 39% |

**The headline margin is NOT concentrated in Gauteng on this panel**: 16% inside against 18% outside. Quote the split anyway — the point of the table is that the reader checks rather than assumes.  The model is beaten by uniform swing on seats at **7 of 24** city-years: Johannesburg 2016, Tshwane 2011, Tshwane 2016, Ekurhuleni 2016, Cape Town 2021, Mangaung 2011, Buffalo City 2011.

**Sign count against uniform swing: 15 wins, 7 losses, 2 ties across 24 city-years** — 2011: 4W 3L 1T; 2016: 5W 3L 0T; 2021: 6W 1L 1T. The sign REPLICATES across cycles, which is what the amended bar's Key 1 asks of any candidate and is the strongest claim this panel supports. Metros inside one cycle share a national swing, so 24 city-years across 8 cities is nearer **3 effective clusters** than 24. Never quote a p-value off the pooled count.

**Read the two seat-error columns together.** *seat err (median)* uses the per-party marginal median, which is what the per-party tables below show and which **does not sum to a council** — the *medians sum to* column says by how much. *seat err (coherent)* apportions the mean seat vector by largest remainder, so it IS a chamber. Lower is better throughout.

**The reference columns are the COHERENT statistic too, and until fix #34 they were not.** They carried the marginal median under the coherent key. That is exact for a deterministic reference — whose draws are identical repeats, so its median IS its allocation — and wrong for a stochastic one: `prior-lge-noise`'s medians fell short of the chamber, and a short vector flatters a forecaster wherever it over-forecasts, so the model's margin over the one reference here that expresses uncertainty was understated. Every forecaster in this table is now scored by `compare_history.coherent_seats`, the single definition of a coherent chamber.

**Every forecaster in every row is scored on one held column set** (24 distinct sets across 24 rows — they differ by city-year, which is expected; what matters is that the model and every reference share one within a row). CRPS and energy are invariant to the columns that holding adds, so those two are comparable with runs that predate it; **the variogram is not** — it is a mean over pairs and moves with the column count, so quote a variogram difference within a run and never across two.


## Guards — what fired, per city-year

**A zero here is a MEASURED zero.** The panel is scored with `verbose=False`, which suppresses `run_model`'s printed warnings, and until `ModelRun.guards` existed the solve counters were locals reachable only through a `--run-dir` trace — so the guard state of every city-year in this report used to be *unknown*, not clean. A `—` is an unreachable record and is NOT a zero.

`cap moved` and `IPF fell back` are the two counters whose silence was read as success for two days (§1.41). `solve non-conv (reachable)` excludes parties whose target sits under the level floor, which no θ can reach — read it rather than the raw count, which is expected to equal `solve_calls` (§1.98). The full board is in `history.json` under each record's `guards.counters`.

| city-year | IPF fell back | cap moved | cap undershoots | θ-bound violations | solve non-conv (reachable) | floor injected mean | floor injected worst | identity hits | excessive draws | roster |
|---|---|---|---|---|---|---|---|---|---|---|
| Johannesburg 2011 | 0/1,000 (0.0%) | 0.0000% | 0 | 629/1,000 (62.9%) | 1,275/2,000 (63.7%) | 0.0003% | 0.0013% | 0 | 0 | published (22, 9 dropped) |
| Johannesburg 2016 | 0/1,000 (0.0%) | 0.0000% | 0 | 535/1,000 (53.5%) | 364/2,000 (18.2%) | 0.0001% | 0.0005% | 0 | 0 | published (28, 9 dropped) |
| Johannesburg 2021 | 0/1,000 (0.0%) | 0.0000% | 0 | 1,367/1,000 (136.7%) | 2,000/2,000 (100.0%) | 0.0022% | 0.0039% | 0 | 84 | published (57, 13 dropped) |
| Tshwane 2011 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/1,000 (0.0%) | 1,337/2,000 (66.8%) | 0.0003% | 0.0008% | 0 | 3 | published (19, 7 dropped) |
| Tshwane 2016 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/1,000 (0.0%) | 670/2,000 (33.5%) | 0.0002% | 0.0007% | 0 | 0 | published (22, 8 dropped) |
| Tshwane 2021 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/1,000 (0.0%) | 2,000/2,000 (100.0%) | 0.0018% | 0.0030% | 0 | 94 | published (51, 15 dropped) |
| Ekurhuleni 2011 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/1,000 (0.0%) | 1,235/2,000 (61.8%) | 0.0003% | 0.0006% | 0 | 1 | published (24, 10 dropped) |
| Ekurhuleni 2016 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/1,000 (0.0%) | 1,186/2,000 (59.3%) | 0.0003% | 0.0008% | 0 | 0 | published (26, 9 dropped) |
| Ekurhuleni 2021 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/1,000 (0.0%) | 1,994/2,000 (99.7%) | 0.0009% | 0.0021% | 0 | 26 | published (38, 19 dropped) |
| eThekwini 2011 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/1,000 (0.0%) | 1,060/2,000 (53.0%) | 0.0002% | 0.0006% | 0 | 1 | published (19, 8 dropped) |
| eThekwini 2016 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/1,000 (0.0%) | 516/2,000 (25.8%) | 0.0002% | 0.0079% | 0 | 0 | published (28, 5 dropped) |
| eThekwini 2021 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/1,000 (0.0%) | 2,000/2,000 (100.0%) | 0.0016% | 0.0032% | 0 | 0 | published (54, 10 dropped) |
| Cape Town 2011 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/1,000 (0.0%) | 1,974/2,000 (98.7%) | 0.0006% | 0.0011% | 0 | 0 | published (34, 5 dropped) |
| Cape Town 2016 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/1,000 (0.0%) | 1,907/2,000 (95.3%) | 0.0005% | 0.0012% | 0 | 0 | published (37, 10 dropped) |
| Cape Town 2021 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/1,000 (0.0%) | 2,000/2,000 (100.0%) | 0.0018% | 0.0028% | 0 | 8 | published (54, 15 dropped) |
| Mangaung 2011 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/1,000 (0.0%) | 1,194/2,000 (59.7%) | 0.0002% | 0.0007% | 0 | 10 | published (11, 6 dropped) |
| Mangaung 2016 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/1,000 (0.0%) | 247/2,000 (12.3%) | 0.0002% | 0.0076% | 0 | 0 | published (16, 7 dropped) |
| Mangaung 2021 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/1,000 (0.0%) | 1,203/2,000 (60.2%) | 0.0003% | 0.0008% | 0 | 68 | published (24, 16 dropped) |
| Nelson Mandela Bay 2011 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/1,000 (0.0%) | 983/2,000 (49.1%) | 0.0002% | 0.0006% | 0 | 4 | published (14, 8 dropped) |
| Nelson Mandela Bay 2016 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/1,000 (0.0%) | 63/2,000 (3.1%) | 0.0001% | 0.0004% | 0 | 2 | published (20, 7 dropped) |
| Nelson Mandela Bay 2021 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/1,000 (0.0%) | 1,620/2,000 (81.0%) | 0.0004% | 0.0015% | 0 | 20 | published (29, 13 dropped) |
| Buffalo City 2011 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/1,000 (0.0%) | 1,023/2,000 (51.1%) | 0.0002% | 0.0006% | 0 | 2 | published (9, 9 dropped) |
| Buffalo City 2016 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/1,000 (0.0%) | 45/2,000 (2.2%) | 0.0001% | 0.0003% | 0 | 3 | published (13, 9 dropped) |
| Buffalo City 2021 | 0/1,000 (0.0%) | 0.0000% | 0 | 0/1,000 (0.0%) | 1,056/2,000 (52.8%) | 0.0003% | 0.0016% | 0 | 6 | published (28, 12 dropped) |

**Guards that bound on at least one city-year:** excessive draws (15 of 24); floor injected mean (24 of 24); floor injected worst (24 of 24); solve non-conv (reachable) (24 of 24); θ-bound violations (3 of 24). Every other counter above is a measured zero across the whole panel.


## The arrival channel, scored without the label

The headline CRPS above is scored after the model's generic `ENTRANT` column is renamed onto the largest party that actually arrived — a label chosen with the result in hand, which no baseline gets. This table does not use it. **PIT above 0.5 means the model forecast too little.**

| city-year | arrived | actual mass | forecast mass | actual seats | forecast seats | mass PIT | seats PIT |
|---|---|---|---|---|---|---|---|
| Johannesburg 2011 | 10 | 1.64% | 1.51% | 4 | 3.8 | 0.728 | 0.728 |
| Johannesburg 2016 | 13 | 2.29% | 1.82% | 5 | 4.8 | 0.718 | 0.588 |
| Johannesburg 2021 | 32 | 19.99% | 8.58% | 46 | 20.9 | 0.997 | 0.992 |
| Tshwane 2011 | 5 | 0.36% | 1.46% | 0 | 3.0 | 0.741 | 0.370 |
| Tshwane 2016 | 7 | 0.31% | 1.77% | 0 | 3.9 | 0.033 | 0.022 |
| Tshwane 2021 | 25 | 11.38% | 7.94% | 21 | 16.2 | 0.849 | 0.771 |
| Ekurhuleni 2011 | 12 | 2.56% | 1.41% | 5 | 2.8 | 0.766 | 0.766 |
| Ekurhuleni 2016 | 12 | 2.06% | 1.97% | 5 | 4.5 | 0.612 | 0.640 |
| Ekurhuleni 2021 | 20 | 9.14% | 6.11% | 17 | 13.4 | 0.845 | 0.733 |
| eThekwini 2011 | 8 | 5.61% | 1.41% | 11 | 2.9 | 0.875 | 0.868 |
| eThekwini 2016 | 14 | 3.25% | 2.01% | 6 | 4.3 | 0.907 | 0.772 |
| eThekwini 2021 | 29 | 7.21% | 3.49% | 15 | 7.4 | 0.911 | 0.903 |
| Cape Town 2011 | 16 | 1.02% | 1.49% | 1 | 3.3 | 0.747 | 0.747 |
| Cape Town 2016 | 20 | 1.43% | 1.73% | 2 | 3.9 | 0.449 | 0.248 |
| Cape Town 2021 | 31 | 8.00% | 2.10% | 18 | 4.5 | 0.996 | 0.994 |
| Mangaung 2011 | 2 | 0.28% | 1.26% | 0 | 1.1 | 0.782 | 0.391 |
| Mangaung 2016 | 6 | 4.74% | 1.98% | 3 | 1.7 | 0.932 | 0.808 |
| Mangaung 2021 | 11 | 1.53% | 2.24% | 0 | 2.0 | 0.533 | 0.152 |
| Nelson Mandela Bay 2011 | 4 | 0.41% | 1.32% | 0 | 1.6 | 0.766 | 0.383 |
| Nelson Mandela Bay 2016 | 8 | 1.59% | 1.70% | 2 | 1.9 | 0.574 | 0.605 |
| Nelson Mandela Bay 2021 | 15 | 7.02% | 2.20% | 8 | 2.4 | 0.969 | 0.959 |
| Buffalo City 2011 | 0 | 0.00% | 1.45% | 0 | 1.3 | 0.000 | 0.376 |
| Buffalo City 2016 | 3 | 0.68% | 1.95% | 0 | 1.7 | 0.349 | 0.164 |
| Buffalo City 2021 | 12 | 1.75% | 2.31% | 0 | 1.8 | 0.582 | 0.181 |
| **panel mean** | | | | | | **0.694** | **0.590** |

Mass PIT is above 0.5 at **20 of 24** city-years. A panel mean well above 0.5 on both columns is the model systematically under-forecasting how much of the ballot goes to parties arriving from nothing — read it next to the mid-ballot calibration below, which is the same leak seen through a different instrument.


### Does the arrival budget equal the arrival draw?

**The forecast side of the table above, reconciled against what was declared.** `declared` is the mass the emitted pool spec seeds by name; `generic slot` is the nameless `ENTRANT` column's expectation (`entrant_prob x mean(entrant_share)`), counted only where the model actually held that column; `unexplained` is what the draw produced beyond the two. **A row is flagged when the residual is at least as large as the budget it is a residual of** — that threshold is derived from the row, not typed.

| city-year | declared | generic slot | slot held? | budget | drawn | unexplained | |
|---|---|---|---|---|---|---|---|
| Johannesburg 2011 | 0.00% | 1.42% | yes | 1.42% | 1.51% | +0.09% |
| Johannesburg 2016 | 1.40% | 0.00% | no | 1.40% | 1.82% | +0.42% |
| Johannesburg 2021 | 8.48% | 0.00% | no | 8.48% | 8.58% | +0.10% |
| Tshwane 2011 | 0.00% | 1.42% | yes | 1.42% | 1.46% | +0.04% |
| Tshwane 2016 | 1.40% | 0.00% | no | 1.40% | 1.77% | +0.37% |
| Tshwane 2021 | 7.34% | 0.00% | no | 7.34% | 7.94% | +0.59% |
| Ekurhuleni 2011 | 0.00% | 1.42% | yes | 1.42% | 1.41% | -0.01% |
| Ekurhuleni 2016 | 1.40% | 0.00% | no | 1.40% | 1.97% | +0.57% |
| Ekurhuleni 2021 | 5.18% | 0.00% | no | 5.18% | 6.11% | +0.93% |
| eThekwini 2011 | 0.00% | 1.42% | yes | 1.42% | 1.41% | -0.01% |
| eThekwini 2016 | 1.40% | 0.00% | no | 1.40% | 2.01% | +0.61% |
| eThekwini 2021 | 2.57% | 0.00% | no | 2.57% | 3.49% | +0.91% |
| Cape Town 2011 | 0.00% | 1.42% | yes | 1.42% | 1.49% | +0.08% |
| Cape Town 2016 | 1.40% | 0.00% | no | 1.40% | 1.73% | +0.33% |
| Cape Town 2021 | 1.64% | 0.00% | no | 1.64% | 2.10% | +0.46% |
| Mangaung 2011 | 0.00% | 1.42% | yes | 1.42% | 1.26% | -0.16% |
| Mangaung 2016 | 1.40% | 0.00% | no | 1.40% | 1.98% | +0.58% |
| Mangaung 2021 | 1.64% | 0.00% | no | 1.64% | 2.24% | +0.60% |
| Nelson Mandela Bay 2011 | 0.00% | 1.42% | yes | 1.42% | 1.32% | -0.10% |
| Nelson Mandela Bay 2016 | 1.40% | 0.00% | no | 1.40% | 1.70% | +0.30% |
| Nelson Mandela Bay 2021 | 1.64% | 0.00% | no | 1.64% | 2.20% | +0.55% |
| Buffalo City 2011 | 0.00% | 1.42% | yes | 1.42% | 1.45% | +0.03% |
| Buffalo City 2016 | 1.40% | 0.00% | no | 1.40% | 1.95% | +0.56% |
| Buffalo City 2021 | 1.64% | 0.00% | no | 1.64% | 2.31% | +0.67% |

No row's residual exceeds its accounted budget (24 city-years checked).

⚠️ The model drew arrival mass with **no generic slot recorded** at 16 of 24 city-years (Johannesburg 2016, Johannesburg 2021, Tshwane 2016, Tshwane 2021, Ekurhuleni 2016, Ekurhuleni 2021, eThekwini 2016, eThekwini 2021, Cape Town 2016, Cape Town 2021, Mangaung 2016, Mangaung 2021, Nelson Mandela Bay 2016, Nelson Mandela Bay 2021, Buffalo City 2016, Buffalo City 2021). Before the presence test was moved ahead of the relabel this was true at twenty of twenty-four rows and meant the detector was blind, not that the slot was absent. If it is non-empty here, check that against `montecarlo`'s rule for appending `ENTRANT` before reading it as a fact about the model.


## Where the vote error sits on the ballot

**Two columns per band, and they answer different questions.** *signed* is the net error in points — positive means the model gave that band MORE than it won — and it is what shows one band eating another. *abs* sums the per-party error without cancelling, and it is the only one of the two that is a measure of error at all. Where they diverge, the band is wrong about individual parties in both directions at once: Johannesburg 2021's ranks 1-3 are the case that motivated the column (ANC and DA over, ActionSA far under). The bands are by actual rank.

| city-year | 1-3 signed | 1-3 abs | 4-12 signed | 4-12 abs | 13+ signed | 13+ abs | phantom | seats at stake in 4-12 |
|---|---|---|---|---|---|---|---|---|
| Johannesburg 2011 | -10.31pp | 12.42pp | **+10.36pp** | 12.04pp | -0.05pp | 0.54pp | 0.00pp (0) | 12 |
| Johannesburg 2016 | -0.67pp | 3.57pp | **-1.67pp** | 2.98pp | +2.17pp | 2.38pp | 0.17pp (1) | 15 |
| Johannesburg 2021 | +1.33pp | 24.52pp | **-1.83pp** | 9.42pp | +0.43pp | 1.67pp | 0.07pp (2) | 58 |
| Tshwane 2011 | -10.61pp | 17.46pp | **+8.51pp** | 9.46pp | +0.64pp | 0.96pp | 1.46pp (1) | 6 |
| Tshwane 2016 | -3.11pp | 3.89pp | **+1.20pp** | 1.31pp | +1.78pp | 2.06pp | 0.13pp (1) | 7 |
| Tshwane 2021 | +7.01pp | 7.01pp | **-7.59pp** | 7.64pp | +0.29pp | 1.54pp | 0.29pp (4) | 44 |
| Ekurhuleni 2011 | -6.32pp | 8.55pp | **+6.94pp** | 9.27pp | -0.63pp | 0.76pp | 0.00pp (0) | 13 |
| Ekurhuleni 2016 | -0.60pp | 5.12pp | **-1.21pp** | 2.74pp | +1.81pp | 2.08pp | 0.00pp (0) | 12 |
| Ekurhuleni 2021 | +6.25pp | 6.25pp | **-7.19pp** | 7.24pp | +0.89pp | 1.56pp | 0.05pp (1) | 38 |
| eThekwini 2011 | -3.25pp | 5.58pp | **+3.38pp** | 11.58pp | -0.13pp | 0.38pp | 0.00pp (0) | 24 |
| eThekwini 2016 | -1.41pp | 4.04pp | **+0.47pp** | 5.88pp | +0.94pp | 1.28pp | 0.00pp (0) | 18 |
| eThekwini 2021 | +5.77pp | 6.15pp | **-4.88pp** | 5.34pp | -1.12pp | 3.66pp | 0.22pp (3) | 31 |
| Cape Town 2011 | -3.34pp | 16.09pp | **+3.50pp** | 4.52pp | -0.16pp | 1.24pp | 0.00pp (0) | 10 |
| Cape Town 2016 | +0.10pp | 1.54pp | **-1.07pp** | 1.34pp | +0.97pp | 1.66pp | 0.00pp (0) | 12 |
| Cape Town 2021 | +7.13pp | 7.13pp | **-7.12pp** | 7.36pp | -0.23pp | 2.05pp | 0.22pp (3) | 38 |
| Mangaung 2011 | -4.90pp | 26.38pp | **+3.64pp** | 4.71pp | +0.00pp | 0.00pp | 1.26pp (1) | 3 |
| Mangaung 2016 | +1.18pp | 2.34pp | **-1.32pp** | 5.31pp | +0.14pp | 0.50pp | 0.00pp (0) | 6 |
| Mangaung 2021 | -0.41pp | 4.31pp | **-0.66pp** | 3.61pp | +1.06pp | 1.78pp | 0.00pp (0) | 12 |
| Nelson Mandela Bay 2011 | -2.23pp | 26.22pp | **+0.96pp** | 2.25pp | -0.05pp | 0.05pp | 1.32pp (1) | 3 |
| Nelson Mandela Bay 2016 | -0.16pp | 2.23pp | **-0.94pp** | 2.58pp | +1.10pp | 1.17pp | 0.00pp (0) | 7 |
| Nelson Mandela Bay 2021 | +5.64pp | 8.10pp | **-6.41pp** | 6.95pp | +0.77pp | 1.48pp | 0.00pp (0) | 15 |
| Buffalo City 2011 | +0.14pp | 26.78pp | **-1.59pp** | 3.93pp | +0.00pp | 0.00pp | 1.45pp (1) | 5 |
| Buffalo City 2016 | -0.93pp | 4.60pp | **+0.93pp** | 5.93pp | +0.00pp | 0.00pp | 0.00pp (0) | 8 |
| Buffalo City 2021 | -1.47pp | 7.06pp | **+0.25pp** | 2.01pp | +1.06pp | 1.59pp | 0.15pp (1) | 6 |

**Totals across 24 city-years:** ranks 1-3 -15.16pp signed / 237.31pp absolute, ranks 4-12 -3.32pp / 135.39pp, ranks 13+ +11.71pp / 30.40pp.

**Phantom mass: 6.77pp** on parties that did not stand at all — including the generic `ENTRANT` column where no party arrived. The bands iterate the parties that DID stand, so none of them can see it; it is exactly why the three signed bands sum to -6.77pp rather than to zero.


## Ward winners — the geography key

**`seat_abs_err_coherent` cannot see geography and this can.** `solve_and_predict` forces every party's citywide share onto the share the draw drew, and both ballots are `weight @ pred` against those same targets, so `dev`, `gamma`, pool composition and the whole VD layer reach the seat score ONLY through an overhang trigger. Any change to those is judged here, or it is judged by an instrument that is blind to it. Hit rate is the modal call; Brier (multi-category, 0 to 2) is the proper score and is what a change in CONFIDENCE moves. **Read the model against the baselines in its own row** — safe wards are called correctly by anything at all.

| city-year | wards | model called | hit rate | Brier MC | last-lge | uniform-swing | prior-lge-noise | uniform-swing+roster |
|---|---|---|---|---|---|---|---|---|
| Johannesburg 2011 | 130 | 126 | 96.9% | 0.048 | 92.3% | 93.8% | 92.3% | 93.8% |
| Johannesburg 2016 | 135 | 134 | 99.3% | 0.017 | 94.8% | 97.8% | 94.8% | 97.8% |
| Johannesburg 2021 | 135 | 127 | 94.1% | 0.093 | 93.3% | 93.3% | 93.3% | 93.3% |
| Tshwane 2011 | 105 (only 99 matched) | 98 | 93.3% | 0.081 | 98.1% | 98.1% | 98.1% | 98.1% |
| Tshwane 2016 | 107 | 104 | 97.2% | 0.043 | 98.1% | 98.1% | 98.1% | 98.1% |
| Tshwane 2021 | 107 | 105 | 98.1% | 0.036 | 98.1% | 98.1% | 98.1% | 98.1% |
| Ekurhuleni 2011 | 101 | 97 | 96.0% | 0.045 | 94.1% | 96.0% | 95.0% | 96.0% |
| Ekurhuleni 2016 | 112 | 111 | 99.1% | 0.029 | 97.3% | 99.1% | 97.3% | 99.1% |
| Ekurhuleni 2021 | 112 | 107 | 95.5% | 0.068 | 95.5% | 94.6% | 95.5% | 94.6% |
| eThekwini 2011 | 103 | 97 | 94.2% | 0.101 | 93.2% | 92.2% | 93.2% | 92.2% |
| eThekwini 2016 | 110 (only 109 matched) | 97 | 88.2% | 0.199 | 82.7% | 85.5% | 83.6% | 85.5% |
| eThekwini 2021 | 111 | 110 | 99.1% | 0.036 | 96.4% | 98.2% | 96.4% | 98.2% |
| Cape Town 2011 | 111 | 111 | 100.0% | 0.014 | 85.6% | 97.3% | 85.6% | 96.4% |
| Cape Town 2016 | 116 | 116 | 100.0% | 0.005 | 100.0% | 100.0% | 100.0% | 100.0% |
| Cape Town 2021 | 116 | 115 | 99.1% | 0.015 | 99.1% | 99.1% | 99.1% | 99.1% |
| Mangaung 2011 | 49 | 49 | 100.0% | 0.026 | 98.0% | 95.9% | 98.0% | 95.9% |
| Mangaung 2016 | 50 (only 49 matched) | 48 | 96.0% | 0.036 | 96.0% | 98.0% | 96.0% | 98.0% |
| Mangaung 2021 | 51 | 50 | 98.0% | 0.038 | 98.0% | 96.1% | 98.0% | 96.1% |
| Nelson Mandela Bay 2011 | 60 | 59 | 98.3% | 0.024 | 83.3% | 96.7% | 83.3% | 96.7% |
| Nelson Mandela Bay 2016 | 60 | 57 | 95.0% | 0.070 | 96.7% | 96.7% | 96.7% | 96.7% |
| Nelson Mandela Bay 2021 | 60 | 57 | 95.0% | 0.052 | 95.0% | 95.0% | 95.0% | 95.0% |
| Buffalo City 2011 | 50 | 49 | 98.0% | 0.045 | 94.0% | 98.0% | 94.0% | 98.0% |
| Buffalo City 2016 | 50 | 48 | 96.0% | 0.081 | 100.0% | 96.0% | 100.0% | 96.0% |
| Buffalo City 2021 | 50 | 48 | 96.0% | 0.072 | 96.0% | 96.0% | 96.0% | 96.0% |

**Pooled over 24 city-years: 2120/2191 = 96.8% of ward contests called correctly, against last-lge 94.7%, uniform-swing 96.2%, prior-lge-noise 94.8%, uniform-swing+roster 96.1%. A margin over the baselines that is smaller than the seat margin is the model's geography adding less than its citywide machinery, which is a statement the seat columns cannot make.

## Calibration — pooled across every city-year, and split by rank

**Pool over city-years; never over rank bands.** Seven to fifteen scored columns per city-year cannot distinguish a 50% interval from an 80% one, so the city-years must be pooled to say anything at all. But the rank bands must NOT be: this model is biased in opposite directions at the top of the ballot and in the middle, and a mean over both lands between them and reports a model that does not exist. The pooled table comes first because it is the familiar one; **the split table below it is the one to read.**

A mean PIT above 0.50 means the truth keeps landing high in the forecast distribution — the model forecast too LOW for those columns. Below 0.50 means it forecast too HIGH. Read the sign per band; the pooled sign is an artefact of how the two bands happen to be sized.

| population | n | 50% | 80% | 90% | mean PIT | χ²_RS vs flat (5% crit) |
|---|---|---|---|---|---|---|
| reference (INPUT-selected — fixed; the only one to compare on) | 514 | 79% | 90% | 94% | 0.584 | 36.4 (16.92) |
| claimed by the model (forecast-selected — neutral for ONE model) | 153 | 77% | 92% | 95% | 0.540 | 44.4 (16.92) |
| won a seat (outcome-selected — INFLATED by construction) | 269 | 58% | 81% | 87% | 0.693 | 117.7 (16.92) |
| every scored column (MIXED: outcome-selected + neutral, diluted) | 580 | 81% | 91% | 94% | 0.555 | 27.9 (16.92) |

* **reference** (n=514) PIT histogram [34, 28, 29, 42, 42, 66, 67, 81, 66, 59] — approximately flat
* **claimed** (n=153) PIT histogram [11, 9, 7, 14, 15, 30, 21, 25, 18, 3] — hump-shaped: the truth lands mid-distribution too often — over-dispersed, the model is hedging
* **seat_holders** (n=269) PIT histogram [10, 4, 7, 14, 15, 31, 34, 49, 47, 58] — U-shaped: the truth lands outside the distribution too often — under-dispersed, widen it; mean PIT 0.69 — the model under-predicts seats
* **all** (n=580) PIT histogram [45, 43, 38, 52, 51, 71, 65, 83, 68, 64] — approximately flat


The verdict at the end of each line is `score.pit_histogram`'s shape heuristic, which reads the end mass and the mean. **DO NOT ACT ON IT AS A WIDTH VERDICT — it is not reliable as one, and on this model it is demonstrably wrong.** The heuristic tests the mass in the two END bins against flat, so a histogram that is monotone increasing scores as U-shaped: a shifted forecast piles mass in the top bin and gets called under-dispersed. On the ranks 4-12 columns it reads the histogram `[1, 1, 1, 11, 14]` — 25 of 28 in the top two bins, monotone, nothing at the bottom — and prints *"U-shaped … under-dispersed, widen it"*, while calling the pooled population *"hump-shaped — over-dispersed, hedging"*. The two verdicts contradict each other and the band one contradicts the level-free width table below, which is the one that is right. `score.py` is not changed here — the heuristic is fine for its own purpose and what is wrong is quoting it about width. **The χ²_RS column is the test of uniformity — `score.chi2_clustered`, clustered by city-year and averaged over the PIT re-randomisations, set out below; the level-free dispersion table is the test of width.**

### The uniformity test — `score.chi2_clustered`

* **reference** (24 city-years, R=64) — uniformity REJECTED after the clustering correction: χ²_RS 36.36 against 16.92 on 9 dof, design effect 1.07, in 64/64 randomisations [cells 0.65–1.82, cv² 0.19; Satterthwaite χ² 30.50 against 14.91 on 7.6 dof, 64/64]. The NOMINAL χ² it corrects averages 38.5 with sd 9.9 across those 64 randomisations; the 95% cluster-bootstrap interval on it is [20.5, 88.3] from 20,000 replicates.
* **claimed** (24 city-years, R=64) — uniformity REJECTED after the clustering correction: χ²_RS 44.44 against 16.92 on 9 dof, design effect 0.99, in 64/64 randomisations [cells 0.34–1.69, cv² 0.28; Satterthwaite χ² 34.74 against 14.14 on 7.0 dof, 64/64]. The NOMINAL χ² it corrects averages 43.8 with sd 5.5 across those 64 randomisations; the 95% cluster-bootstrap interval on it is [28.9, 86.5] from 20,000 replicates.
* **seat_holders** (24 city-years, R=64) — uniformity REJECTED after the clustering correction: χ²_RS 117.66 against 16.92 on 9 dof, design effect 1.12, in 64/64 randomisations [cells 0.11–3.07, cv² 0.63; Satterthwaite χ² 72.30 against 11.88 on 5.5 dof, 64/64]. The NOMINAL χ² it corrects averages 131.3 with sd 5.9 across those 64 randomisations; the 95% cluster-bootstrap interval on it is [94.3, 208.3] from 20,000 replicates.
* **all** (24 city-years, R=64) — not established: χ²_RS averages 27.92 against 16.92 but only 61/64 randomisations reject — the answer depends on the PIT re-roll, not on the model [cells 0.70–1.40, cv² 0.14; Satterthwaite χ² 24.48 against 15.35 on 7.9 dof, 60/64]. The NOMINAL χ² it corrects averages 28.7 with sd 7.0 across those 64 randomisations; the 95% cluster-bootstrap interval on it is [15.8, 70.2] from 20,000 replicates.

⚠️ **The cluster level is this file's choice, not the statistic's**, and `score.chi2_clustered` returns the limitation with the number so that it is quoted with it: *the clusters are whatever the caller grouped by. On this panel city-year clustering (k=24) gives delta-bar 1.07 and buys almost nothing; the CYCLE level, where the dependence actually is (sd(z) across 2011/2016/2021 is 0.601/0.889/1.265 pooled and 0.452/1.155/1.960 on ranks 4-12), has k=3 and cannot be estimated. Quote the city-year result WITH that limitation — see score.chi2_clustered.__doc__.*

**Two corrections separate this column from the χ² a PIT histogram reports, and the second is the one that was missing.** The PIT of an integer seat count is randomised within its jump, so a χ² computed on one draw of that randomisation is a draw from a distribution and not a statistic — the `sd` printed above is its spread with the model standing still, and on this panel it is a large fraction of the statistic itself. And the columns inside a city-year share a turnout draw, a pool structure and a national swing, so the nominal test's critical value is not this design's. `score.chi2_clustered` averages over R re-randomisations and applies the Rao-Scott correction with the design effect ESTIMATED from the city-years; it needs at least 8 of them and says `not established` rather than printing a number when it has fewer. See its docstring for what the design effect turns out to be here, and why.

The three populations differ by which columns they count, and the difference is itself the finding. `claimed` selects on the FORECAST, which leaves PIT uniform under calibration, so it is the honest test and the only one to quote. `seat_holders` selects on the OUTCOME: zero is the bottom of the support, so winning a seat selects over-performers and the population reads high even for a perfect forecaster — it is quoted because it is the population a reader assumes, not because it is neutral. `all` was documented as neutral and **is not**: `score.seat_matrix` admits a column when `truth[i] > 0 or samples[:, i].max() > 0`, and the first clause lets a party in because it WON, which is outcome selection. **16 of its 580 columns across 24 city-years carry PIT exactly 0 or 1** — parties the model gave zero seats in every draw, present only because they won a seat (Johannesburg 2011 ALJAMAAH, Johannesburg 2011 OKM, Johannesburg 2016 ALJAMAAH, Johannesburg 2021 PA, Ekurhuleni 2011 DISPLACEES_RATE_PAYERS_ASSOCIATION, +11 more). It is a mixture of an outcome-selected set and a neutral one.

**The dilution is in `reference`, not in `all`, and this report said otherwise for months.** A column correctly at zero on both sides is a free interval hit and a near-uniform PIT — but `seat_matrix`'s admission rule excludes it from `all` by construction, and the count there is **0 of 580**. Such columns are admitted to `reference`, which is built with `keep_all=True` over a fixed universe, and there the count is **87 of 514**. `all` is still not a test of anything — its outcome-selected part and its neutral part push opposite ways — but quote the dilution against the population that actually carries it.

### Split by actual PR rank — `claimed` columns

**The pooled row above is the average of the rows below, and they have opposite signs.** This is the same fault as a signed error sum inside a rank band, one level up: an average over subsets biased in opposite directions reports the midpoint and calls it centred.

| band | n | mean PIT | 95% CI (cluster bootstrap) | 50% | 80% | 90% | 50% (PIT) | 80% (PIT) | 90% (PIT) |
|---|---|---|---|---|---|---|---|---|---|
| ranks 1-3 | 72 | 0.527 | [0.490, 0.561] | 74% [61–86] | 92% [85–97] | 96% [92–100] | 68% [54–81] | 92% [85–97] | 94% [89–99] |
| ranks 4-12 | 74 | 0.580 | [0.501, 0.648] | 78% [68–88] | 92% [86–97] | 93% [88–98] | 64% [53–75] | 91% [84–96] | 93% [88–98] |
| ranks 13+ | 7 | 0.247 | [0.147, 0.498] | 100% [100–100] | 100% [100–100] | 100% [100–100] | 29% [0–100] | 86% [25–100] | 100% [100–100] |

The CI resamples CITY-YEARS, not columns: columns inside one city-year share a turnout draw, a pool structure and a national swing, so a column bootstrap would give an interval far too tight. 20,000 replicates, fixed seed.

**The two coverage triples are the same question asked twice.** The first is `score.coverage` — the empirical quantile interval, which on integer seats must include whole endpoints and therefore over-covers. The second is the fraction of columns whose randomised PIT falls in the central interval, which carries no such inflation. They agree at ranks 1-3, where parties hold tens of seats and one endpoint is worth nothing, and diverge at ranks 4-12, where parties hold one to ten and an endpoint is a large part of the interval. **Read the PIT columns whenever the two are compared** — but neither triple is the width verdict on its own; that is the table below.

**Read all three coverage levels together, never one of them.** A forecast whose intervals are too NARROW under-covers at EVERY level — that is what narrow means. A forecast that is merely SHIFTED loses coverage at the 50% level first and hardest, because it has vacated the middle of its own interval, and its 80% and 90% coverages fall too. Only intervals that are too WIDE push the 80% and 90% coverages above nominal. So a band that reads LOW at 50% and HIGH at 80 and 90 is shifted and too wide, and reading its 50% column alone gives exactly the opposite instruction. **That mistake has been made twice on this report, in opposite directions, and rule 8 of `ITERATING.md` carried each of them.** The width verdict belongs to the level-free table above; the coverage rows corroborate it or they do not.

The rank-band vote table further up and the mean-PIT column here are the same LEVEL finding measured twice — top three over, middle short. Because shares sum to one that gap is a zero-sum transfer, not two independent faults, so a level fix has to move mass rather than add it.

### Is it the right WIDTH? — the level divided out

**This table, not the coverage rows, is the width verdict.** Coverage moves with the level as well as the width: a forecast pushed off centre vacates the middle of its own interval, so its 50% coverage falls however wide it is. Read at one level, coverage says 'too narrow' for a forecast that is merely shifted. The columns below divide the level out. **1.00 is right; below 1.00 the intervals are too WIDE; above 1.00 too narrow.** `1/ratio` is roughly the factor they are out by.

| band | n | probit-SD (level-free) | same @1e-2 clip | drop saturated | sat. PITs | exact SD of z | standardised bias (mean z) | PIT variance vs 1/12 |
|---|---|---|---|---|---|---|---|---|
| ranks 1-3 | 72 | **0.783** | 0.750 | 0.783 | 0 | 0.774 | +0.067 | 0.0533 vs 0.0833 |
| ranks 4-12 | 74 | **0.847** | 0.823 | 0.847 | 0 | 0.776 | +0.039 | 0.0551 vs 0.0833 |
| ranks 13+ | 7 | **0.550** | 0.550 | 0.550 | 0 | 0.384 | -0.570 | 0.0310 vs 0.0833 |

⛔ **A probit-SD from a band carrying a saturated PIT is a property of the CLIP, not of the forecast, and this table prints both so the reader can see which.** `_probit` clips at 1e-6; a column whose truth exceeded every draw has a PIT of exactly 1.0, and `Φ⁻¹(1)` is infinite, so the figure in the first column is whatever the clip decides. The `@1e-2` column is the same statistic with a looser clip and the `drop saturated` column is the same statistic with those columns removed instead of pinned — the honest answer to a question the clip only papers over. **Where the three disagree and `sat. PITs` is non-zero, the band's width is UNQUOTABLE**: say so, or quote the drop-saturated figure and say that is what it is. Measured on `reference` ranks 4-12 over Johannesburg alone, the three read 1.55 / 1.07 / 1.10 — the same band, two different verdicts. MODEL-LOG §1.132, §1.134.

#### The same question on the FIXED population — and it disagrees

**The `n` here is the number of columns the width figure was actually computed on** — columns with a defined `z`. A column whose draws are all identical has no scale, so it carries a PIT and no `z`; the pooled tables above count PIT values and their `n` is larger.

| band | `claimed` n(z) | `claimed` SD of z | `reference` n(z) | `reference` SD of z | `reference` mean z | `reference` probit-SD | same @1e-2 | drop saturated | sat. PITs |
|---|---|---|---|---|---|---|---|---|---|
| ranks 1-3 | 72 | 0.774 | 72 | 0.774 | +0.067 | **0.783** | 0.750 | 0.783 | 0 |
| ranks 4-12 | 74 | 0.776 | 170 | 1.529 | +0.403 | 1.312 ⛔UNQUOTABLE | 0.967 | 0.913 | 10 |
| ranks 13+ | 7 | 0.384 | 171 | 0.335 | -0.168 | 1.114 ⛔UNQUOTABLE | 0.910 | 0.865 | 5 |

⛔ **A probit-SD from a band carrying a saturated PIT is a property of the CLIP, not of the forecast, and this table prints both so the reader can see which.** `_probit` clips at 1e-6; a column whose truth exceeded every draw has a PIT of exactly 1.0, and `Φ⁻¹(1)` is infinite, so the figure in the first column is whatever the clip decides. The `@1e-2` column is the same statistic with a looser clip and the `drop saturated` column is the same statistic with those columns removed instead of pinned — the honest answer to a question the clip only papers over. **Where the three disagree and `sat. PITs` is non-zero, the band's width is UNQUOTABLE**: say so, or quote the drop-saturated figure and say that is what it is. Measured on `reference` ranks 4-12 over Johannesburg alone, the three read 1.55 / 1.07 / 1.10 — the same band, two different verdicts. MODEL-LOG §1.132, §1.134.


**Read the last column, not the `SD of z` column, on ranks 13+.** `sd(z)` is exact under a level shift and **meaningless on a near-degenerate discrete column**: where the forecast is roughly Bernoulli(p) and the truth is zero, `z = −√(p/(1−p))` exactly, a function of the forecast probability with no room to spread. On the 96 ranks-13+ columns whose truth is zero, observed `z` correlates with that expression at **+0.93**. probit-SD comes from the randomised PIT, which is uniform under calibration whatever the support, and is the one to read there — at the cost of being attenuated by a level shift, so it is a LOWER BOUND wherever `mean z` is far from zero. Neither statistic is right everywhere; the pair is. MODEL-LOG §1.58.

**Ranks 1-3 are the same columns in both populations** — the top three are always claimed — so that row is a consistency check and the two `SD of z` numbers should agree exactly. It is also the band that is genuinely too WIDE and the band that responds to `dirichlet_scale`.

**Ranks 4-12 cannot be described by one width, and that is the finding.** On the same columns `sd(z)` says far too narrow, `IQR-sd` says too wide, and probit-SD disagrees with both — because the error distribution is a narrow shifted bulk with a few enormous outliers, which `claimed` excludes by construction. They are NAMED below, from the rows actually scored. A distribution that reads differently depending which moment you take is mis-SHAPED, not mis-scaled, and no scalar fixes it.


⛔ **AND THE SPREAD AT 4-12 IS A HANDFUL OF COLUMNS.** On the `reference` population over the 170 columns carrying a defined `z`, the two largest carry **59.3%** of the band's total squared `z`: **Johannesburg 2021 PA** (z +12.65, 37.9% of the band's squared deviation); **Cape Town 2021 CAPE_COLOURED_CONGRESS** (z +9.59, 21.4% of the band's squared deviation). Dropping them takes `sd(z)` from 1.529 to **0.973**. Quote the leave-the-largest-out figure beside the headline or the headline is two observations, not a width. §1.56, §1.58, §1.131.

**`probit-SD` is the one to quote when only a PIT is available.** It is `sd(Φ⁻¹(u))`, and under a location shift of a roughly normal forecast `Φ⁻¹(u)` translates — the shift lands in the mean, not the spread. `exact SD of z` is `(truth − forecast mean) / forecast sd` per column, centred, which is invariant to a shift by construction; it reads `—` on an artefact written before `calibration_columns` stored the `z` column, and it is the number to prefer when it is there. The standardised bias is the LEVEL, kept in its own column so that it can never be read as width again.

**The last column is printed to show it failing.** PIT variance against a nominal 1/12 has been proposed on this project as "shift-invariant, therefore a clean width statistic". **It is neither.** A PIT lives on [0, 1]; move the forecast off centre and its mass piles against a boundary and the variance falls whatever the width is. On the suite's fixture whose width is exactly right (`tests/test_calibration_report.py::_shift_scale_results`) it reads 0.0829, 0.0450 and 0.0240 at truth shifts of 0, +2 and +3 seats against a nominal 0.0833 — a pure level error reading as a 3.5× under-dispersion, which is the wrong diagnosis with the wrong remedy. Do not quote it as a width statistic; it is here so that nobody rediscovers it as one.

Per city-year, for provenance only — **every n below is too small to read, and none of these rows is evidence of anything on its own.**

| city-year | n claimed | 50% | 80% | 90% | mean PIT (claimed) |
|---|---|---|---|---|---|
| Johannesburg 2011 | 6 | 67% | 83% | 83% | 0.501 |
| Johannesburg 2016 | 8 | 88% | 100% | 100% | 0.532 |
| Johannesburg 2021 | 9 | 33% | 67% | 78% | 0.641 |
| Tshwane 2011 | 5 | 40% | 80% | 80% | 0.472 |
| Tshwane 2016 | 9 | 100% | 100% | 100% | 0.383 |
| Tshwane 2021 | 7 | 71% | 100% | 100% | 0.606 |
| Ekurhuleni 2011 | 6 | 67% | 83% | 100% | 0.439 |
| Ekurhuleni 2016 | 6 | 100% | 100% | 100% | 0.551 |
| Ekurhuleni 2021 | 9 | 78% | 89% | 89% | 0.689 |
| eThekwini 2011 | 6 | 100% | 100% | 100% | 0.449 |
| eThekwini 2016 | 8 | 75% | 88% | 88% | 0.500 |
| eThekwini 2021 | 8 | 88% | 100% | 100% | 0.556 |
| Cape Town 2011 | 6 | 67% | 83% | 83% | 0.535 |
| Cape Town 2016 | 8 | 100% | 100% | 100% | 0.629 |
| Cape Town 2021 | 7 | 71% | 100% | 100% | 0.520 |
| Mangaung 2011 | 4 | 0% | 75% | 100% | 0.452 |
| Mangaung 2016 | 4 | 100% | 100% | 100% | 0.471 |
| Mangaung 2021 | 6 | 100% | 100% | 100% | 0.577 |
| Nelson Mandela Bay 2011 | 3 | 33% | 67% | 100% | 0.555 |
| Nelson Mandela Bay 2016 | 7 | 100% | 100% | 100% | 0.576 |
| Nelson Mandela Bay 2021 | 6 | 83% | 100% | 100% | 0.492 |
| Buffalo City 2011 | 3 | 33% | 67% | 67% | 0.541 |
| Buffalo City 2016 | 6 | 83% | 100% | 100% | 0.600 |
| Buffalo City 2021 | 6 | 100% | 100% | 100% | 0.552 |


## Johannesburg 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 55.85% | 55.18% | 59.29% | 55.25% | 57.82% | 145 | 153 |
| DA | 27.04% | 27.10% | 34.35% | 27.41% | 34.90% | 71 | 90 |
| IFP | 1.31% | 2.67% | 1.61% | 2.22% | 1.66% | 3 | 4 |
| COPE | 9.01% | 10.13% | 1.11% | 9.69% | 1.19% | 23 | 3 |
| NFP | 0.00% | 1.51% | 0.82% | 1.44% | 0.74% | 0 | 2 |
| APC | 0.00% | 0.21% | 0.53% | 0.20% | 0.39% | 0 | 1 |
| ACDP | 0.31% | 0.79% | 0.40% | 0.77% | 0.44% | 1 | 1 |
| PAC | 0.00% | 0.63% | 0.35% | 0.87% | 0.43% | 0 | 1 |
| ALJAMAAH | nan% | nan% | 0.27% | nan% | 0.19% | 0 | 1 |
| OKM | nan% | nan% | 0.25% | nan% | 0.15% | 0 | 1 |
| VFPLUS | 0.27% | 0.91% | 0.23% | 0.92% | 0.27% | 1 | 1 |
| UDM | 0.01% | 0.36% | 0.22% | 0.71% | 0.25% | 0 | 1 |

## Johannesburg 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 44.74% | 44.74% | 44.92% | 44.02% | 44.09% | 120 | 121 |
| DA | 39.55% | 39.93% | 38.48% | 40.90% | 38.34% | 108 | 104 |
| EFF | 8.69% | 8.99% | 10.93% | 9.32% | 11.24% | 24 | 30 |
| IFP | 1.03% | 1.26% | 1.71% | 1.16% | 1.74% | 3 | 5 |
| AIC | 0.03% | 0.17% | 1.62% | 0.17% | 1.40% | 0 | 4 |
| ACDP | 0.29% | 0.48% | 0.31% | 0.51% | 0.28% | 1 | 1 |
| VFPLUS | 0.20% | 0.42% | 0.31% | 0.51% | 0.34% | 1 | 1 |
| ALJAMAAH | nan% | nan% | 0.31% | nan% | 0.22% | 0 | 1 |
| UDM | 0.18% | 0.37% | 0.25% | 0.41% | 0.28% | 1 | 1 |
| COPE | 0.06% | 0.21% | 0.21% | 0.13% | 0.15% | 0 | 1 |
| PA | 0.00% | 0.07% | 0.17% | 0.07% | 0.13% | 0 | 1 |
| PAC | 0.21% | 0.42% | 0.17% | 0.10% | 0.09% | 0 | 0 |

**Missed entirely:** AIC — won seats, median zero.

## Johannesburg 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 38.42% | 38.48% | 33.22% | 38.57% | 33.97% | 104 | 91 |
| DA | 32.76% | 33.13% | 25.45% | 33.71% | 26.83% | 89 | 71 |
| ASA | 6.14% | 6.53% | 18.12% | 5.40% | 13.98% | 15 | 44 |
| EFF | 13.21% | 13.74% | 10.11% | 14.41% | 11.14% | 37 | 29 |
| PA | 0.03% | 0.09% | 2.96% | 0.17% | 2.91% | 0 | 8 |
| IFP | 0.78% | 1.40% | 2.36% | 1.82% | 2.36% | 2 | 7 |
| VFPLUS | 0.61% | 0.87% | 1.33% | 0.96% | 1.35% | 2 | 4 |
| ACDP | 0.26% | 0.57% | 1.03% | 0.58% | 1.08% | 1 | 3 |
| ALJAMAAH | 0.23% | 0.31% | 0.83% | 0.28% | 1.08% | 1 | 3 |
| AIC | 0.26% | 0.86% | 0.69% | 0.43% | 0.50% | 1 | 2 |
| AHC | 0.00% | 0.06% | 0.43% | 0.05% | 0.47% | 0 | 1 |
| GOOD | 0.08% | 0.33% | 0.33% | 0.27% | 0.40% | 0 | 1 |

**Missed entirely:** PA — won seats, median zero.

## Tshwane 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 52.29% | 51.10% | 56.46% | 50.91% | 54.18% | 110 | 118 |
| DA | 29.79% | 30.07% | 38.74% | 31.03% | 38.56% | 63 | 82 |
| VFPLUS | 4.13% | 5.01% | 1.59% | 5.26% | 1.73% | 9 | 4 |
| COPE | 6.54% | 7.82% | 0.89% | 7.35% | 0.92% | 13 | 2 |
| ACDP | 0.49% | 1.37% | 0.59% | 1.49% | 0.67% | 1 | 1 |
| APC | 0.00% | 0.19% | 0.46% | 0.18% | 0.35% | 0 | 1 |
| PAC | 0.01% | 0.46% | 0.25% | 0.58% | 0.28% | 0 | 1 |
| AZAPO | 0.00% | 0.43% | 0.18% | 0.48% | 0.21% | 0 | 1 |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | 0.06% | 0.83% | 0.15% | 0.32% | 0.12% | 0 | 0 |
| IFP | 0.01% | 0.25% | 0.12% | 0.21% | 0.13% | 0 | 0 |
| CHRISTIAN_DEMOCRATIC_PARTY | nan% | nan% | 0.11% | nan% | 0.13% | 0 | 0 |
| INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA | nan% | nan% | 0.09% | nan% | 0.05% | 0 | 0 |

## Tshwane 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 41.03% | 41.11% | 43.10% | 41.66% | 43.20% | 88 | 93 |
| ANC | 42.02% | 41.87% | 41.48% | 40.55% | 41.02% | 89 | 89 |
| EFF | 9.77% | 10.13% | 11.64% | 10.85% | 11.62% | 22 | 25 |
| VFPLUS | 2.04% | 2.24% | 1.97% | 2.48% | 2.02% | 5 | 4 |
| ACDP | 0.44% | 0.69% | 0.47% | 0.80% | 0.52% | 1 | 1 |
| APC | 0.17% | 0.41% | 0.24% | 0.07% | 0.05% | 0 | 0 |
| COPE | 0.02% | 0.21% | 0.22% | 0.22% | 0.27% | 0 | 1 |
| PAC | 0.11% | 0.34% | 0.14% | 0.37% | 0.20% | 0 | 1 |
| UDM | 0.02% | 0.21% | 0.13% | 0.26% | 0.10% | 0 | 0 |
| IFP | 0.00% | 0.12% | 0.10% | 0.02% | 0.02% | 0 | 0 |
| AFRICAN_MANDATE_CONGRESS | 0.17% | 0.39% | 0.09% | 0.42% | 0.06% | 0 | 0 |
| PA | 0.00% | 0.05% | 0.09% | 0.05% | 0.05% | 0 | 0 |

## Tshwane 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 36.72% | 36.50% | 34.84% | 36.59% | 34.42% | 79 | 75 |
| DA | 32.97% | 33.39% | 31.77% | 33.60% | 32.29% | 71 | 69 |
| EFF | 13.72% | 14.16% | 10.43% | 14.19% | 10.94% | 29 | 23 |
| ASA | 5.27% | 5.85% | 9.28% | 5.44% | 7.99% | 11 | 19 |
| VFPLUS | 4.55% | 4.86% | 7.79% | 4.99% | 7.96% | 10 | 17 |
| ACDP | 0.39% | 0.79% | 0.91% | 0.86% | 0.93% | 1 | 2 |
| AIC | 0.26% | 0.64% | 0.81% | 0.59% | 0.38% | 1 | 1 |
| DOP | 0.00% | 0.08% | 0.49% | 0.07% | 0.58% | 0 | 1 |
| PA | 0.02% | 0.06% | 0.48% | 0.13% | 0.52% | 0 | 1 |
| PAC | 0.00% | 0.23% | 0.21% | 0.22% | 0.18% | 0 | 1 |
| IFP | 0.00% | 0.11% | 0.21% | 0.17% | 0.09% | 0 | 1 |
| COPE | 0.00% | 0.14% | 0.19% | 0.17% | 0.20% | 0 | 1 |

## Ekurhuleni 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 59.74% | 58.38% | 62.17% | 59.06% | 61.08% | 122 | 125 |
| DA | 25.72% | 26.49% | 30.13% | 26.64% | 30.46% | 52 | 62 |
| IFP | 0.87% | 2.28% | 1.16% | 1.45% | 1.04% | 1 | 2 |
| NFP | 0.00% | 1.41% | 1.13% | 1.33% | 1.19% | 0 | 3 |
| COPE | 5.20% | 6.95% | 1.09% | 6.55% | 0.79% | 10 | 2 |
| APC | 0.00% | 0.25% | 0.68% | 0.24% | 0.54% | 0 | 1 |
| PAC | 0.04% | 0.72% | 0.61% | 0.73% | 0.75% | 0 | 2 |
| ACDP | 0.47% | 1.05% | 0.59% | 1.25% | 0.67% | 1 | 1 |
| VFPLUS | 1.05% | 1.85% | 0.51% | 1.75% | 0.59% | 2 | 1 |
| UDM | 0.00% | 0.48% | 0.42% | 0.88% | 0.51% | 0 | 1 |
| DISPLACEES_RATE_PAYERS_ASSOCIATION | nan% | nan% | 0.41% | nan% | 0.48% | 0 | 1 |
| INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA | nan% | nan% | 0.32% | nan% | 0.78% | 0 | 1 |

**Missed entirely:** NFP — won seats, median zero.

## Ekurhuleni 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 47.40% | 47.29% | 48.84% | 45.92% | 48.44% | 105 | 109 |
| DA | 35.81% | 36.39% | 34.13% | 36.65% | 34.17% | 80 | 77 |
| EFF | 9.51% | 9.79% | 11.10% | 10.94% | 11.35% | 23 | 25 |
| AIC | 0.02% | 0.17% | 1.65% | 0.19% | 1.63% | 0 | 4 |
| IFP | 0.53% | 0.88% | 1.04% | 1.08% | 0.99% | 1 | 2 |
| VFPLUS | 0.69% | 0.92% | 0.90% | 1.08% | 0.89% | 2 | 2 |
| ACDP | 0.38% | 0.66% | 0.42% | 0.80% | 0.43% | 1 | 1 |
| PAC | 0.23% | 0.54% | 0.42% | 0.25% | 0.43% | 0 | 1 |
| COPE | 0.02% | 0.18% | 0.28% | 0.19% | 0.25% | 0 | 1 |
| PA | 0.00% | 0.04% | 0.28% | 0.05% | 0.25% | 0 | 1 |
| APC | 0.21% | 0.55% | 0.27% | 0.14% | 0.06% | 0 | 0 |
| UDM | 0.09% | 0.32% | 0.23% | 0.17% | 0.16% | 0 | 0 |

**Missed entirely:** AIC — won seats, median zero.

## Ekurhuleni 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 43.20% | 43.12% | 38.34% | 42.85% | 38.03% | 96 | 86 |
| DA | 29.41% | 29.75% | 28.37% | 29.57% | 29.07% | 66 | 65 |
| EFF | 12.74% | 13.35% | 13.27% | 13.55% | 13.87% | 29 | 31 |
| ASA | 3.35% | 4.00% | 7.36% | 3.93% | 5.84% | 7 | 15 |
| VFPLUS | 2.52% | 2.88% | 3.48% | 2.83% | 3.18% | 6 | 8 |
| PA | 0.14% | 0.21% | 1.87% | 0.41% | 1.89% | 1 | 4 |
| IFP | 0.48% | 1.18% | 1.47% | 1.05% | 1.24% | 1 | 3 |
| AIC | 0.25% | 0.86% | 1.36% | 0.97% | 1.22% | 1 | 3 |
| ACDP | 0.27% | 0.73% | 0.86% | 0.75% | 0.82% | 1 | 2 |
| INDEPENDENT_CITIZENS_MOVEMENT | 0.00% | 0.15% | 0.45% | 0.14% | 0.44% | 0 | 1 |
| PAC | 0.02% | 0.46% | 0.43% | 0.52% | 0.31% | 0 | 1 |
| INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA | nan% | nan% | 0.36% | nan% | 0.78% | 0 | 1 |

## eThekwini 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 59.72% | 58.72% | 62.02% | 61.35% | 60.11% | 125 | 126 |
| DA | 20.23% | 20.70% | 21.81% | 16.88% | 20.21% | 38 | 43 |
| MINORITY_FRONT | 5.93% | 6.10% | 4.94% | 6.61% | 5.68% | 13 | 11 |
| NFP | 0.00% | 1.41% | 4.48% | 1.43% | 4.92% | 0 | 10 |
| IFP | 6.93% | 8.44% | 3.96% | 8.91% | 4.30% | 15 | 9 |
| ACDP | 0.75% | 1.31% | 0.67% | 1.52% | 0.80% | 2 | 2 |
| TRULY_ALLIANCE | nan% | nan% | 0.62% | nan% | 0.83% | 0 | 1 |
| APC | 0.00% | 0.25% | 0.41% | 0.26% | 0.20% | 0 | 1 |
| COPE | 1.36% | 2.64% | 0.40% | 2.69% | 0.35% | 3 | 1 |
| UNITED_ACTION_FRONT | nan% | nan% | 0.13% | nan% | 0.21% | 0 | 0 |
| AZAPO | nan% | nan% | 0.13% | nan% | 0.14% | 0 | 0 |
| UDM | 0.00% | 0.23% | 0.11% | 0.18% | 0.15% | 0 | 0 |

**Missed entirely:** NFP — won seats, median zero.

## eThekwini 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 57.26% | 57.21% | 59.11% | 52.67% | 52.95% | 120 | 126 |
| DA | 28.66% | 28.85% | 27.54% | 33.03% | 26.30% | 68 | 61 |
| IFP | 3.27% | 3.46% | 4.28% | 3.44% | 4.12% | 7 | 10 |
| EFF | 2.59% | 2.76% | 3.63% | 2.88% | 3.26% | 6 | 8 |
| AIC | 0.04% | 0.13% | 1.51% | 0.14% | 1.23% | 0 | 3 |
| ACDP | 0.49% | 0.68% | 0.54% | 0.77% | 0.55% | 1 | 1 |
| MINORITY_FRONT | 3.03% | 3.25% | 0.46% | 3.54% | 0.60% | 7 | 1 |
| DEMOCRATIC_LIBERAL_CONGRESS | 0.04% | 0.15% | 0.43% | 0.15% | 0.60% | 0 | 1 |
| TRULY_ALLIANCE | 0.36% | 0.50% | 0.42% | 0.63% | 0.40% | 1 | 1 |
| MINORITIES_OF_SOUTH_AFRICA | 0.04% | 0.14% | 0.27% | 0.14% | 0.35% | 0 | 1 |
| APC | 0.27% | 0.43% | 0.26% | 0.24% | 0.15% | 1 | 1 |
| ALJAMAAH | 0.05% | 0.15% | 0.18% | 0.15% | 0.20% | 0 | 1 |

**Missed entirely:** AIC — won seats, median zero.

## eThekwini 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 46.76% | 46.58% | 42.51% | 45.18% | 41.77% | 102 | 96 |
| DA | 27.75% | 28.21% | 26.33% | 29.14% | 25.57% | 63 | 59 |
| EFF | 10.00% | 10.62% | 10.80% | 10.51% | 10.15% | 22 | 24 |
| IFP | 4.37% | 5.15% | 7.45% | 5.65% | 6.67% | 10 | 16 |
| ASA | 0.67% | 1.21% | 2.35% | 1.18% | 1.50% | 2 | 4 |
| AIC | 0.26% | 0.98% | 1.01% | 0.42% | 0.33% | 0 | 2 |
| ACTIVE_CITIZENS_COALITION | 0.00% | 0.12% | 0.81% | 0.11% | 1.03% | 0 | 2 |
| ACDP | 0.43% | 0.69% | 0.76% | 0.75% | 0.78% | 1 | 2 |
| ABANTU_BATHO_CONGRESS | 0.00% | 0.10% | 0.65% | 0.10% | 0.76% | 0 | 2 |
| JUSTICE_AND_EMPLOYMENT_PARTY | 0.03% | 0.28% | 0.61% | 0.27% | 0.51% | 0 | 1 |
| ATM | 0.16% | 0.59% | 0.57% | 0.57% | 0.66% | 0 | 1 |
| MINORITY_FRONT | 0.52% | 0.72% | 0.50% | 1.01% | 0.47% | 1 | 1 |

## Cape Town 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 57.97% | 57.72% | 61.15% | 58.07% | 60.69% | 128 | 135 |
| ANC | 26.87% | 26.88% | 33.17% | 26.25% | 32.44% | 59 | 73 |
| COPE | 6.89% | 7.51% | 1.13% | 7.44% | 1.08% | 15 | 3 |
| ACDP | 1.17% | 1.80% | 1.06% | 1.92% | 1.37% | 3 | 3 |
| NATIONAL_PARTY_SOUTH_AFRICA | 0.00% | 0.17% | 0.54% | 0.17% | 0.51% | 0 | 1 |
| UDM | 0.10% | 0.62% | 0.38% | 0.54% | 0.40% | 0 | 1 |
| ALJAMAAH | 0.23% | 0.86% | 0.35% | 0.85% | 0.39% | 1 | 1 |
| AFRICA_MUSLIM_PARTY | 0.38% | 0.89% | 0.28% | 1.12% | 0.40% | 1 | 1 |
| CAPE_MUSLIM_CONGRESS | 0.00% | 1.49% | 0.25% | 1.48% | 0.33% | 0 | 1 |
| PAC | 0.08% | 0.55% | 0.18% | 0.57% | 0.23% | 0 | 1 |
| VFPLUS | 0.08% | 0.48% | 0.17% | 0.48% | 0.19% | 0 | 1 |
| DEMOCRATS_FOR_CHANGE | nan% | nan% | 0.15% | nan% | 0.08% | 0 | 0 |

## Cape Town 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 66.84% | 66.70% | 66.75% | 67.14% | 66.46% | 155 | 154 |
| ANC | 24.94% | 25.34% | 24.52% | 24.29% | 24.20% | 56 | 57 |
| EFF | 2.23% | 2.45% | 3.12% | 2.69% | 3.22% | 5 | 7 |
| ACDP | 0.68% | 0.92% | 1.13% | 1.14% | 1.29% | 2 | 3 |
| AIC | 0.28% | 0.46% | 0.76% | 0.50% | 0.42% | 1 | 1 |
| ALJAMAAH | 0.25% | 0.46% | 0.55% | 0.55% | 0.76% | 1 | 2 |
| VFPLUS | 0.18% | 0.32% | 0.39% | 0.38% | 0.43% | 1 | 1 |
| UDM | 0.22% | 0.38% | 0.33% | 0.19% | 0.20% | 0 | 1 |
| DEMOCRATIC_INDEPENDENT_PARTY | 0.01% | 0.11% | 0.28% | 0.12% | 0.32% | 0 | 1 |
| CAPE_MUSLIM_CONGRESS | nan% | nan% | 0.27% | nan% | 0.25% | 0 | 1 |
| COPE | 0.04% | 0.16% | 0.24% | 0.16% | 0.25% | 0 | 1 |
| PAC | 0.17% | 0.33% | 0.24% | 0.42% | 0.27% | 1 | 1 |

## Cape Town 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 61.18% | 61.14% | 58.74% | 60.30% | 57.78% | 141 | 135 |
| ANC | 22.47% | 22.59% | 18.71% | 22.86% | 18.46% | 52 | 43 |
| EFF | 4.74% | 5.01% | 4.15% | 5.11% | 4.10% | 11 | 10 |
| GOOD | 2.79% | 3.13% | 3.68% | 3.01% | 3.94% | 6 | 9 |
| CAPE_COLOURED_CONGRESS | 0.00% | 0.08% | 2.83% | 0.08% | 2.78% | 0 | 7 |
| ACDP | 2.06% | 2.41% | 2.29% | 2.87% | 2.40% | 5 | 6 |
| VFPLUS | 0.63% | 0.95% | 1.54% | 1.03% | 1.63% | 2 | 4 |
| PA | nan% | nan% | 1.43% | nan% | 1.54% | 0 | 4 |
| ALJAMAAH | 0.61% | 0.83% | 1.19% | 1.14% | 1.32% | 2 | 3 |
| AFRICA_RESTORATION_ALLIANCE | 0.00% | 0.08% | 0.64% | 0.08% | 0.81% | 0 | 2 |
| CAPE_INDEPENDENCE_PARTY_KAAPSE_ONAFHANKLIKHEIDS_PARTY | 0.00% | 0.08% | 0.62% | 0.07% | 0.65% | 0 | 2 |
| UIM | 0.00% | 0.09% | 0.56% | 0.09% | 0.58% | 0 | 1 |

**Missed entirely:** CAPE_COLOURED_CONGRESS, PA — won seats, median zero.

## Mangaung 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 58.92% | 58.03% | 66.57% | 57.24% | 65.96% | 57 | 65 |
| DA | 18.62% | 19.73% | 26.82% | 20.10% | 27.40% | 18 | 26 |
| COPE | 12.45% | 14.04% | 3.30% | 11.41% | 3.02% | 11 | 3 |
| VFPLUS | 3.78% | 4.33% | 1.40% | 8.65% | 1.62% | 6 | 2 |
| ACDP | 0.23% | 1.03% | 0.56% | 0.45% | 0.29% | 0 | 0 |
| APC | 0.00% | 0.30% | 0.55% | 0.25% | 0.39% | 0 | 1 |
| PAC | 0.01% | 0.66% | 0.26% | 0.32% | 0.21% | 0 | 0 |
| DIKWANKWETLA_PARTY_OF_SOUTH_AFRICA | 0.00% | 0.62% | 0.25% | 0.57% | 0.22% | 0 | 0 |
| BLACK_CONSCIOUSNESS_PARTY | nan% | nan% | 0.15% | nan% | 0.09% | 0 | 0 |
| UNITED_RESIDENTS_FRONT | nan% | nan% | 0.14% | nan% | 0.20% | 0 | 0 |

## Mangaung 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 57.14% | 56.62% | 56.77% | 56.36% | 56.28% | 57 | 58 |
| DA | 27.47% | 27.96% | 26.20% | 28.70% | 25.73% | 28 | 27 |
| EFF | 7.86% | 8.41% | 8.84% | 7.57% | 8.48% | 8 | 9 |
| AIC | 0.17% | 0.48% | 2.74% | 0.43% | 0.64% | 0 | 2 |
| VFPLUS | 2.06% | 2.29% | 1.85% | 2.66% | 1.99% | 2 | 2 |
| AGENCY_FOR_NEW_AGENDA | 0.18% | 0.53% | 1.57% | 0.48% | 0.21% | 0 | 1 |
| COPE | 0.26% | 0.72% | 0.56% | 0.78% | 0.63% | 0 | 1 |
| ACDP | 0.29% | 0.61% | 0.39% | 0.96% | 0.39% | 0 | 0 |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | 0.03% | 0.28% | 0.28% | 0.25% | 0.11% | 0 | 0 |
| APC | 0.20% | 0.69% | 0.25% | 0.64% | 0.17% | 0 | 0 |
| AZANIAN_ALLIANCE_CONGRESS | 0.18% | 0.51% | 0.13% | 0.46% | 0.06% | 0 | 0 |
| BOTSHABELO_UNEMPLOYED_MOVEMENT | 0.17% | 0.46% | 0.12% | 0.41% | 0.09% | 0 | 0 |

## Mangaung 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 49.64% | 49.15% | 51.51% | 48.73% | 49.75% | 50 | 51 |
| DA | 25.74% | 26.44% | 25.48% | 25.96% | 25.98% | 26 | 26 |
| EFF | 11.60% | 12.37% | 11.37% | 11.87% | 11.24% | 12 | 12 |
| VFPLUS | 3.45% | 3.62% | 4.41% | 3.88% | 4.55% | 4 | 5 |
| PA | 1.21% | 2.12% | 1.78% | 2.04% | 1.83% | 1 | 2 |
| AFRIKAN_ALLIANCE_OF_SOCIAL_DEMOCRATS | 0.04% | 0.36% | 1.26% | 0.34% | 1.61% | 0 | 2 |
| AIC | 0.71% | 1.81% | 0.84% | 3.30% | 1.70% | 1 | 1 |
| ACDP | 0.24% | 0.74% | 0.70% | 0.76% | 0.74% | 0 | 1 |
| ATM | 0.12% | 0.63% | 0.61% | 0.60% | 0.58% | 0 | 1 |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | nan% | nan% | 0.38% | nan% | 0.38% | 0 | 0 |
| COPE | 0.00% | 0.25% | 0.30% | 0.11% | 0.16% | 0 | 0 |
| MANGAUNG_COMMUNITY_FORUM | 0.02% | 0.31% | 0.21% | 0.29% | 0.02% | 0 | 0 |

## Nelson Mandela Bay 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 45.27% | 44.72% | 52.13% | 45.06% | 51.69% | 54 | 63 |
| DA | 32.49% | 33.43% | 40.24% | 33.10% | 40.02% | 39 | 48 |
| COPE | 15.22% | 16.88% | 4.88% | 15.95% | 5.01% | 18 | 6 |
| UDM | 0.04% | 0.66% | 0.54% | 1.04% | 0.55% | 0 | 1 |
| PAC | 0.03% | 0.83% | 0.52% | 1.44% | 0.57% | 0 | 1 |
| APC | 0.00% | 0.15% | 0.43% | 0.14% | 0.01% | 0 | 0 |
| ACDP | 0.35% | 0.69% | 0.36% | 0.75% | 0.40% | 0 | 1 |
| AZAPO | 0.01% | 0.58% | 0.28% | 0.44% | 0.22% | 0 | 0 |
| VFPLUS | 0.31% | 0.74% | 0.20% | 0.84% | 0.25% | 0 | 0 |
| CHRISTIAN_DEMOCRATIC_PARTY | nan% | nan% | 0.16% | nan% | 0.18% | 0 | 0 |
| AFRICAN_COMMUNITY_MOVEMENT | nan% | nan% | 0.14% | nan% | 0.18% | 0 | 0 |
| UNITED_INDEPENDENT_FRONT | nan% | nan% | 0.06% | nan% | 0.08% | 0 | 0 |

## Nelson Mandela Bay 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 47.49% | 47.70% | 46.66% | 48.13% | 46.75% | 57 | 57 |
| ANC | 41.32% | 41.25% | 41.50% | 40.82% | 40.34% | 49 | 50 |
| EFF | 3.77% | 4.09% | 5.03% | 4.25% | 5.21% | 5 | 6 |
| UDM | 0.80% | 1.06% | 1.83% | 1.04% | 2.00% | 1 | 2 |
| AIC | 0.88% | 1.18% | 1.61% | 1.23% | 0.28% | 1 | 1 |
| UNITED_FRONT_OF_THE_EASTERN_CAPE | 0.16% | 0.39% | 0.80% | 0.40% | 1.09% | 0 | 1 |
| COPE | 0.40% | 0.68% | 0.70% | 0.70% | 0.77% | 1 | 1 |
| ACDP | 0.25% | 0.47% | 0.35% | 0.55% | 0.37% | 0 | 1 |
| PA | 0.02% | 0.16% | 0.29% | 0.17% | 0.24% | 0 | 1 |
| ALTERNATIVE_DEMOCRATS | 0.08% | 0.26% | 0.25% | 0.27% | 0.08% | 0 | 0 |
| VFPLUS | 0.31% | 0.54% | 0.25% | 0.69% | 0.26% | 1 | 0 |
| PAC | 0.34% | 0.61% | 0.23% | 0.20% | 0.12% | 0 | 0 |

## Nelson Mandela Bay 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 45.07% | 45.32% | 40.04% | 45.30% | 39.80% | 54 | 48 |
| ANC | 38.51% | 38.37% | 39.60% | 37.84% | 39.26% | 46 | 48 |
| EFF | 7.34% | 7.98% | 6.40% | 8.38% | 6.40% | 9 | 8 |
| NORTHERN_ALLIANCE | 0.01% | 0.20% | 2.09% | 0.21% | 2.18% | 0 | 3 |
| ACDP | 0.82% | 1.10% | 1.68% | 1.17% | 1.64% | 1 | 2 |
| VFPLUS | 1.06% | 1.28% | 1.64% | 1.32% | 1.51% | 1 | 2 |
| DOP | 0.01% | 0.17% | 1.38% | 0.18% | 1.47% | 0 | 2 |
| PA | nan% | nan% | 1.32% | nan% | 1.42% | 0 | 2 |
| ABANTU_INTEGRITY_MOVEMENT | 0.01% | 0.18% | 1.11% | 0.19% | 1.05% | 0 | 1 |
| UDM | 0.25% | 0.79% | 1.07% | 0.94% | 1.01% | 0 | 1 |
| AIC | 0.27% | 0.96% | 0.68% | 0.48% | 0.38% | 0 | 1 |
| PAC | 0.03% | 0.40% | 0.51% | 0.47% | 0.48% | 0 | 1 |

**Missed entirely:** NORTHERN_ALLIANCE — won seats, median zero.

## Buffalo City 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 62.12% | 61.23% | 69.13% | 63.06% | 70.88% | 63 | 71 |
| DA | 12.77% | 14.83% | 20.26% | 15.69% | 20.71% | 13 | 21 |
| COPE | 15.68% | 17.16% | 3.70% | 13.58% | 2.02% | 14 | 3 |
| AIC | 0.02% | 0.83% | 3.58% | 0.65% | 0.17% | 0 | 2 |
| PAC | 0.26% | 1.72% | 1.66% | 1.99% | 2.11% | 0 | 2 |
| UDM | 0.02% | 1.06% | 0.74% | 2.04% | 0.53% | 0 | 0 |
| ACDP | 0.35% | 1.40% | 0.70% | 1.57% | 0.79% | 0 | 1 |
| PAN_AFRICANIST_MOVEMENT | 0.00% | 0.32% | 0.23% | 0.25% | 0.13% | 0 | 0 |

## Buffalo City 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 60.66% | 60.02% | 59.86% | 60.45% | 57.63% | 61 | 60 |
| DA | 24.06% | 25.13% | 23.45% | 25.74% | 23.35% | 24 | 24 |
| EFF | 4.65% | 5.44% | 8.21% | 4.68% | 7.74% | 4 | 8 |
| AIC | 1.07% | 2.12% | 3.89% | 4.03% | 2.95% | 2 | 4 |
| UDM | 1.79% | 2.58% | 1.29% | 0.78% | 0.45% | 1 | 1 |
| COPE | 0.04% | 0.46% | 0.99% | 0.47% | 0.72% | 0 | 1 |
| PAC | 0.57% | 1.52% | 0.98% | 1.33% | 0.82% | 1 | 1 |
| ACDP | 0.20% | 0.57% | 0.55% | 0.67% | 0.56% | 0 | 1 |
| UNITED_FRONT_OF_THE_EASTERN_CAPE | 0.34% | 0.96% | 0.32% | 0.82% | 0.27% | 0 | 0 |
| PAN_AFRICANIST_MOVEMENT | nan% | nan% | 0.20% | nan% | 0.04% | 0 | 0 |
| PEOPLES_ALLIANCE | 0.36% | 1.00% | 0.16% | 0.86% | 0.02% | 0 | 0 |
| UNITED_CONGRESS | 0.00% | 0.21% | 0.10% | 0.18% | 0.09% | 0 | 0 |

## Buffalo City 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 56.73% | 56.25% | 60.51% | 56.57% | 58.35% | 57 | 61 |
| DA | 21.29% | 22.28% | 19.49% | 23.18% | 19.55% | 22 | 20 |
| EFF | 11.35% | 12.37% | 12.37% | 12.19% | 11.76% | 11 | 13 |
| UDM | 0.34% | 0.82% | 1.10% | 1.67% | 0.82% | 1 | 1 |
| PAC | 0.25% | 1.13% | 1.05% | 1.15% | 0.83% | 0 | 1 |
| AIC | 0.66% | 1.76% | 0.97% | 0.43% | 0.45% | 0 | 1 |
| ATM | 0.42% | 1.04% | 0.89% | 0.92% | 0.93% | 0 | 1 |
| ACDP | 0.50% | 0.68% | 0.57% | 0.73% | 0.55% | 1 | 1 |
| VFPLUS | 0.13% | 0.51% | 0.52% | 0.45% | 0.51% | 0 | 1 |
| PA | 0.02% | 0.17% | 0.42% | 0.15% | 0.19% | 0 | 0 |
| INDEPENDENT_SOUTH_AFRICAN_NATIONAL_CIVIC_ORGANISATION | 0.01% | 0.15% | 0.34% | 0.14% | 0.10% | 0 | 0 |
| COPE | 0.00% | 0.12% | 0.27% | 0.01% | 0.05% | 0 | 0 |