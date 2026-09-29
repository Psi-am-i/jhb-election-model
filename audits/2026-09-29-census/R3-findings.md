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
