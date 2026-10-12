# Pre-registration: reducing a forecast to a prediction, scored on past elections

Written 2026-10-08, before the run. Not to be edited after it.

## Question

The owner will choose how our forecast is reduced to one prediction
(`STYLE.md` rule 11; `audits/2026-10-07-prediction-restructure/review/SYNTHESIS.md`).
He asked to see the leading rule against known election results first. A
prediction must carry the four things an election produces: ward votes, ward
seats, list votes and the final seat count.

## Candidates, each built from one city-year's simulations

- **A, built.** Each ward to the party that wins it in the most simulations.
  Ward-ballot votes: each party's mean ward-ballot vote across simulations.
  List-ballot votes: each party's mean list-ballot vote. Final seats: those
  votes and ward wins through the model's own seat law (`eligible_parties`,
  `outside_pool_wards`, `allocate_with_overhang`, the scenario's overhang rule),
  the same path every simulation and the real result take.
- **B, one simulation.** The simulation with the lowest mean seat error
  (sum of |seat difference|) against all the other simulations; its own wards,
  votes and seats.
- **References, not predictions:** the per-party median seats (not a council)
  and `compare_history.coherent_seats` (largest remainder on mean seats: a
  council, no wards or votes). Reported for seats only.

## Run

Every city-year with emitted pools for 2011, 2016 and 2021 (eight metros):
whatever `find data/processed -name 'pools_20{11,16,21}.json'` counts.
`montecarlo.run_model` in-process, the scenario as `compare_history.run_city_year`
builds it, `compare_history`'s default draw count and seed, the generic
entrant relabelled as `compare_history` does. Nothing written to `data/`,
`site/`, `content/`, `publications/`. Truth: `compare_history.actual_shares`
and `_actual_seats` (IEC-verified councils).

## Scores, per city-year, against the real result

1. final seat error (sum over parties of |predicted − actual seats|);
2. correct ward calls;
3. ward-ballot vote error, and 4. list-ballot vote error (sum of |pp|);
5. the ward count of A's largest ward-winner against that party's actual count;
6. excessive seats: parties A seats at their ward count with no list seats,
   against whether the actual result did the same for that party.

## Predictions

| # | prediction | mechanism |
|---|---|---|
| P1 | A's top ward-winner is given more wards than it actually won in at least 14 of the city-years scored | calling every ward for its favourite gives the favourite every close ward |
| P2 | A's final seat error is lower than B's in at least 13 of them | B carries one simulation's noise on top of the model's error |
| P3 | A calls at least as many wards correctly as B in at least 18 of them | the modal call maximises expected correct calls ward by ward |
| P4 | A's list-ballot vote error is lower than B's in at least 16 of them; same for the ward ballot | a mean is closer to the centre than one draw |
| P5 | A's panel total seat error is within 15% of `coherent_seats`' | both sit at the centre of the seat distribution; A adds ward calls and the law |
| P6 | where A gives a party excessive seats, the actual result did too in at least half of those cases | overhang follows from a party's ward dominance, which modal calls exaggerate |

"Of them" means of the city-years that run and score; any that fail are listed
with the error, not dropped.
