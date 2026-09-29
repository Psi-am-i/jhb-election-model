# F10 mechanism census — results (run `runs/r1`, 2026-09-29)

**Revised the same day on an independent review** (`R-tests-brief.md`,
findings in `R-tests-findings.md`): the C5-nudge check restated, C1-nudge's
stage evidence qualified, two field lists completed, the unguarded list's
cause corrected, and C4 moved to "not measured".

Claims: `CLAIMS.md` at `c90e693`, written and reviewed (R3 and its fix check)
before this run. Harness: `census.py` / `probe.py`. Each mutant's full record
is `runs/r1/<name>/result.json`; `runs/r1/results.json` has them all. The
per-draw trace stages (42–44) were compared and then deleted to keep the
commit small; their comparison is in each `result.json`.

One harness correction after the run: `45_delivered` carries the code hash
bare as `pools_sha`, so the CONTROL mutant (an inert code edit) differed
there and nowhere else. `pools_sha` was added to the ignored keys and every
mutant recompared from the saved outputs (`census.py recompare`); nothing was
re-run.

**Control.** Spec identical, trace identical, no test failure beyond the
base's one standing failure (the capacity scan). The staleness restamp works;
the test runs are not confounded.

## Per claim

| mutant | predicted | observed | verdict |
|---|---|---|---|
| C1-off | B's emit refuses (inferred) | refused: Indian/Asian has no member (registered 2,698, turnout 0.0001); 4 F3 tests fail | as claimed |
| C1-nudge | IA central turnout = base × 1.10 exactly; another pool falls; `20_spine` if seeds move | ratio 1.1000; all three other pools fall; `seeds` moved **at the 17th digit**, and `20_spine` differs only in AIC's level at relative 3e-16, so the first MATERIAL change is `40_draws`. The edit scales every hold level, so `registration_series["2006"]` also moved (Indian/Asian 0.006407 → 0.007046); two F3 tests failed | as claimed by the registered rule; the stage evidence is round-off |
| C1-guard | cascade test fails; no change at B, J | `test_a_refit_that_silences_a_second_pool_holds_it_too` fails; specs and traces identical | as claimed |
| C2-off | spec diffs empty; the same test fails | as predicted (per-part failure not separable from the runner's output) | as claimed |
| C3-guard | no change; unguarded | no change; no test fails | **unguarded**, as claimed |
| C3-guard + C1-off | spec written without IA; P1 violated | pools = BA, Coloured, White; both P1 clauses violated | as claimed |
| C4-off | exactly `40_draws` | `40_draws`, spec identical | as claimed |
| C4-nudge | exactly `40_draws` | `40_draws`, spec identical | as claimed |
| C9-off | spread: IA changes at 2016 and 2026, nothing else; spec band conditional | spread: IA only, both years (n 34 → 36, 94 → 100); B: IA band ends only (0.295–0.770 → 0.266–0.795); J: no spec change (panel not above own range); no test fails | as claimed; **unguarded** |
| C5-off | `10_theta_prior`; RISE spine 1.4411% ± 0.00005pp | `10_theta_prior`; RISE 1.44109% | as claimed. No test fails: the national-baseline call site is **unguarded** (not predicted either way) |
| C5-nudge | `10_theta_prior`; RISE factor exact; only RISE, ASA rise | `10_theta_prior`. The registered procedure could not run as written (the `_mergers` rows carry P, not RISE's B). Checked instead with P from the run's row (0.22507%) and B read from the 2024 national result file (RISE 1.55692%), no run involved: factor (B + 0.85P)/(B + 0.75P) = 1.0130421, observed ratio 1.0130421, relative error 2e-16. RISE's spine level is its national share × 0.9256, the national-to-local factor (`nat_level = national·exp(c_t)`); risers ASA, RISE | as claimed |
| C5-guard | three-partner test fails; no change at J | `test_the_roster_decides_which_partner_inherits` fails; no change | as claimed |
| C6-off | `20_spine`; ASA falls; RISE unchanged | `20_spine`; ASA 13.5092% → 13.4906%; RISE identical; FORUM_4 (off the ballot) also moves; no test fails | as claimed; call site **unguarded**, as claimed |
| C6-guard | `20_spine`; RISE takes a local record; the no-record test fails | `20_spine`; RISE's route becomes "blend at full local" and its level falls from 1.597% to 0.187%; the test fails | as claimed |
| C7-off | spec: RISE and ASA weights, every pool's `alpha`; not turnout/registered/identified; `40_draws`; unguarded | in `pools`, exactly RISE's and ASA's weights and every `alpha`; outside `pools`, the mutation's own flag `mergers[*].vector_blended` and the note `no_measured_vector.RISE`; `40_draws`; no test fails | as claimed; **unguarded** |
| C7-nudge | RISE Coloured weight further, same direction | 0.072 (off) → 0.133 (base) → 0.184 (nudge); `40_draws` | as claimed |
| C7-guard | no change at J; running-mass test fails | as predicted | as claimed |
| C8-off | K live in base; K = real in mutant; real rows identical; consumer scan fails | K's predecessor SOCIALIST_REVOLUTIONARY_WORKERS_PARTY; all three hold; the test fails | as claimed |
| C10-off | exactly `40_draws`; the per-VD test fails | `40_draws`; `test_a_merger_moves_retention_times_the_predecessor_and_nothing_else` fails | as claimed |

## The three lists

**Dead:** none. Every "off" of a mechanism claimed live changed what the
claim said it would.

**Wrong-way or wrong-stage:** none. Every first changed stage is the one the
claim names, and every nudge moved in the stated direction, by the stated
amount where one was stated.

**Unguarded** (no test in `pool_bounds`, `pool_conservation`,
`roster_aware_baseline`, `theta`, `chain` notices the mechanism removed):

1. C3: `emit_pools`' refusal of a memberless pool (with C1 on nothing reaches
   it; with C1 off it is the only thing that stops a P1-violating spec).
2. C9: the panel spread's skip of held pools.
3. C5: the national-baseline `apply_mergers` call in `run_model`.
4. C6: the preceding-local `apply_mergers` call in `run_model`.
5. C7: `emit_pools`' `blend_merger_vectors` call.

Items 3–4 share a cause: the consumer scan
(`test_every_consumer_the_spec_names_calls_apply_mergers`) worked per
function, so it stayed green while one call in a function that has another
was removed. Item 5 had no scan at all: nothing looked for
`blend_merger_vectors`.

**Not measured:** C4 (the run-time composition). Its mutants ran with the
test modules off, so whether a test notices its removal is unknown. Re-run
with tests on: see `runs/r2-guards` once it has run.

**Harness note.** `first_changed` treats a stage missing on both sides as
equal. The per-draw stages 42–44 were deleted after the recompare, so running
`recompare` again on `runs/r1` would drop them silently; the saved
`result.json` files hold the comparison made while they existed.

## Also found building the harness

The draw follows the members' key order in the spec. `emit_pools` writes
with `sort_keys=True`, so every spec on disk is sorted and the forecast is
stable; a caller handing `run_model` an unsorted in-memory spec would draw
differently from the same spec on disk.
