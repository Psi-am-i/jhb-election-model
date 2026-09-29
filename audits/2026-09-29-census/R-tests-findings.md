# Review of the guard tests and the F9/F10 conclusions — findings and disposition

Brief `R-tests-brief.md` (committed `fab8adc` before the review). Read-only
reviewer; ran only the two test modules. Each finding re-derived by the lead.

| # | finding | lead's check | done |
|---|---|---|---|
| T1 | the new tests sat after `__main__`, so a standalone run never runs them | line numbers | moved above it |
| T2 | the panel-spread test typed `["Indian/Asian"]` and `before="2016"`; a fallback pool moving would fail it | the claim allows fallback movers | held set RECORDED from `pool_counts` during the pass; asserts n rises and a held pool moves; other movers reported |
| T3 | the refusal test asserts wording and rests on observed data | agreed | asserts the refusal and the pool name only; the premise stated in the docstring; the constructed version queued (POOLS-REEMIT-QUEUE), since it needs a `pools.py` change |
| T4 | the per-call count was a second matcher with no can-see | agreed | one matcher (`Counter` per function) for set, counts and self-checks; can-see removes one of `run_model`'s two calls and the blend call |
| T5 | structural checks miss a disabled call (`if False:`, a discarded result) | agreed | new behavioural test `test_the_run_model_mergers_reach_the_spine`: run_model at J with and without the mergers, RISE's spine (national call) and ASA's (local call) must both rise; blend check matches attribute calls too |
| C1 | C5-nudge's "relative error 0" was not the registered check | **disagreed in part.** The reviewer's 9.3e-4 used RISE's spine level for B. With B read from the 2024 result file (share 1.55692%) the registered factor matches to 2e-16; the "unexplained" 0.9256 is the national-to-local factor `exp(c_t)`. The reviewer is right that the procedure as registered could not run (the rows lack B) and that RESULTS described a merely affine check | RESULTS row restated with the independent B |
| C2 | C4 never had its tests run | agreed | "not measured" in RESULTS; C4's mutants re-run with tests on |
| C3 | C1-nudge's `20_spine` is a one-ulp change | agreed | reported with its magnitude |
| C4 | C1-nudge also moved `registration_series` and failed two tests | agreed | reported |
| C5 | "items 3–5 share a cause" wrong for 5 | agreed | corrected |
| C6 | C7-off field list loose | agreed | completed |
| C7 | `pools_sha` correction legitimate; `first_changed` drops a stage missing on both sides | agreed | harness note in RESULTS |
| F1 | arrival: one re-seed is nearer than the change | agreed (seed 5, +0.23 vs +0.50) | MODEL-LOG correction |
| F2 | yardstick pooled two populations; decorrelation premise fails on band-only rows | agreed, re-derived | MODEL-LOG correction with the split table |
| F3 | Buffalo City 2021 moved `turnout_limits` too | agreed | MODEL-LOG correction |
| F4 | the whole-`data/` comparison is reported, not recorded | agreed | MODEL-LOG correction |

The disagreement in C1 is settled by a measurement taken from the input
file with no run involved; it is recorded here, not taken to the owner.
