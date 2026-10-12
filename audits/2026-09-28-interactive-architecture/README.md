# Interactive architecture: re-weight the published draws (2026-09-28)

**What this is.** A read-only architecture review, requested by the owner after
the build plan grew to weeks: *"I want some architecture input on how this
interactive is being built and faster ways to do so."* The full specification
is `PLAN.md` beside this file, as the agent returned it.

**What the lead verified before it went to the owner:**

* Every draw sets each population group's turnout from its measured band with
  `correlated_triangular`, and that drawn turnout weights the group's vote in
  the citywide target: `src/montecarlo.py:2930-2952` and `:3071`. The
  variation a turnout control moves is therefore inside the published draws.

**Not re-derived by the lead**, and carried as the agent's measurement:

* The Black African +5pp re-weighting against a paired re-run.
* The effective draw counts.
* The poll-weighting table.
* The claim that sector turnout is absorbed by `solve_and_predict`, which is
  consistent with `audits/2026-09-27-interactive-levers/MEASURED.md`'s 0.01
  seats for per-VD turnout noise.

**Supersedes** `audits/2026-09-27-interactive-levers/INPUT-ROUTE.md` as the
route for the controls it covers. Route B (MODEL-LOG §1.265-§1.267) is parked,
not discarded: it remains the path for combinations the grid does not hold.
