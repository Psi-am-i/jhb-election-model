# R3 findings on `CLAIMS.md` (at `335a721`), and what was done with each

Read-only review from the committed brief. The lead re-derived the
load-bearing facts before applying: the `02_pools_artefact` payload
(montecarlo.py:3953, four fields); `prior_pr_share` entering `levels.spine`
at montecarlo.py:4876 before `blended_centres`; `_PANEL_SPREAD_CACHE` keyed on
config content, not code (pools.py:3020); the held-pool skip (pools.py:3071)
and the per-VD branch (pools.py:3784); and, from the harness smoke run, that
stages 42–44 are absent without `trace_detail`. No finding was disputed;
nothing went to the owner. No mutation had run.

| # | finding | applied in `CLAIMS.md` |
|---|---|---|
| F1 | spec content never reaches `02_pools_artefact`; first reach is `40_draws`, or `20_spine` if `seeds` move | stages renamed; the spec diff is the first compared artefact; the `seeds` rule pre-registered |
| F2 | C6 acts at `20_spine`; its guard as worded crashes (KeyError) | stage `20_spine`; guard mutation stated exactly (`out.get(...)` and the `continue` removed) |
| F3 | C7-off also moves every pool's `alpha` | prediction restated |
| F4 | C8 cannot be seen at B (run_model does not call theta_residual); the test is a source scan | constructed fixture K, cache cleared; source-edit test |
| F5 | C4's "nothing before 40" holds for a no-op | predicts exactly `40_draws` |
| F6 | C5's stage is conditional; ASA's rise is C6's | conditional stated; only RISE scored for C5; tolerance stated |
| F7 | C1 nudge can be exact; off is inferred; guard mutation stated loosely | exact prediction; "inferred" labelled; exact mutation |
| F8 | "no change" rests on an unscanned population | worded as scanned-only; a change elsewhere is a finding |
| F9 | cache carry-over, base from disk, detail stages | fresh processes, in-process base, `trace_detail` on |
| F10 | two unclaimed mechanisms; unguarded call sites | C9 and C10 added; every off also run as a source edit against named test modules |

## Fix check (on `2c8986d`), and what was done

| # | defect | applied |
|---|---|---|
| N1 | C7-off as "skip the call" crashes: the loop after it reads `vector_blended` | the call is replaced by setting each row's `vector_blended` to False |
| N2 | C5-off and C6-off as deletions leave names unbound (NameError) | each "off" replaces an assignment with its input; nothing is deleted that is read later |
| N3 | a `pools.py` edit moves `pools_sha` and fails `test_chain`'s current-key test on every spec, so every guard reads "guarded" | each scratch clone's specs carry that root's own code hash; a CONTROL mutant (inert code edit) must add no failure; "guarded" = a failure absent from base and control |
| N4 | C10's test row held whatever happened | predicts `test_a_merger_moves_retention_times_the_predecessor_and_nothing_else` fails |
| N5 | C9 claimed too much and predicted the wrong quantity | narrowed to Indian/Asian; the discriminating prediction is on `panel_turnout_spread` itself (a read-only probe); the band change is conditional on measured > own |
| — | C5-nudge named no stage; 1e-6 tolerance too tight for 4-figure inputs | stage stated; P and B taken from the run's own `_mergers` rows at 1e-9 |
| — | C2 hedge missing; wrong test parts | hedge added; parts (b) and (d) |
| — | fixture K under-specified | the pair rule fixed in the claim before the run |
| — | C3 line | 6379 |
