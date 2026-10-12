# Ultra review: the step-5 diff of the 2026-10-11 model round

**Written 2026-10-12 at `3f2f1bb`, before any step-5 code exists.** Frozen
from this commit: it is never amended after code exists (CLAUDE.md §4,
"Ultra reviews"). If the code does something this brief did not anticipate,
that is a finding for the review, not a reason to edit the brief.

**When.** After the step-5 writer finishes and the step-6 diff review is done,
**before** the canonical emit and runs of step 7. After the emit there is no
clean baseline. Owner-triggered; one review.

**The pre-registration it serves:** `prereg/2026-10-12-universal-draw.md`.
Its arms, predictions and gates define what the code must make possible. The
review asks whether the code does what the designs say, not whether it passes
those tests.

---

## What the diff is meant to do

Four changes, applied serially by one writer, in this order:

1. **Paired per-entity random streams.** Every random quantity reads its own
   keyed, draw-indexed stream of parameter-free primitives; parameters enter
   through exact transforms. Design: `step1/1c-paired-draws-design.md`, with
   every fix of `step2/2-review-1c.md` (boost at every gamma shape; Dirichlet
   reference for small α; tie key by declared label; breakages its §4 lists;
   fallback tested alone; run-level wiring tests; paired bootstrap).
2. **One log-scale draw for every party (v4, option L1).** One smooth width
   curve over size fitted jointly with a location curve `m(s)` to every
   party-election of earlier cycles; one newness term; the location fitted and
   not carried in the draw. Design: `step1/1j-universal-draw-design-v4.md` and
   `step1/1j-universal-draw-design-v4-addendum.md` (L1, clamp at 0.016%),
   review `step2/2-review-1j-v4.md`. Machinery inherited from v2/v3: the
   calibration pass and mean-conservation falsifier (v2 §1.2), the normal own
   term and shared factor (v2 §1.1, §3), the base vector as the `pool_spec`
   centre and the individual path joining it (v2 §1.1), the judgement overlay
   read at run time (v3 §11), the judgement hash (v3 addendum §2).
3. **A switchable small-party centre correction:** centres below 20% multiplied
   by `exp(m(s))`, `m` fitted out of sample on earlier cycles only, clamped,
   then renormalised (prereg §3.3). Off by default.
4. **Census:** `REGISTRATION_MAX` deleted, and a pool reaching under 25% of
   every ward held at the city's own registration rate. Design:
   `step1/1g-census-composition-design.md` (P_hold); POOLS-REEMIT-QUEUE
   entry 31 as amended.

The canonical run also needs the **old draw law selectable by a scenario
switch** (the incumbent arm) and `level_shrink = 0` as a scenario override
(`step1/1e-level-lift-design.md` §2.5 step 1).

## Files in scope

* `src/montecarlo.py`: `DrawStreams` and the samplers, `make_drawer`,
  `draw_pools`, `run_model`'s draw loop, the width and location code or its
  call site, the calibration pass, `blended_centres` / `compress_levels`
  interaction with the correction, `pool_spec`, `ModelRun`, the trace stages
  (`30_centres`, `35_widths`, `40_draws`, `41_guards`).
* `src/seats.py` (`stable_entropy`), `src/score.py` (`_column_entropy`).
* Any new module for the width record (designs call it `width_record.py`).
* `src/pools.py`: the registration solve, the identification hold, the bound
  detector, `imputed` / `unidentified`, `_judgements_sha`, `PARTY_KEYS`, the
  end of `support` / `overperform` at emit.
* `src/width_budget.py`, `src/declares.py`, `src/backtest.py` (lever
  registers), and `src/plausibility.py` if it lands in this diff.
* Every test file the diff adds or changes, and the register entries
  (JUDGEMENT-CALLS, MACHINERY) only insofar as a guard reads them.

## Out of scope

* `interactive/py/`, `worker-api/seats-py/`, `site/` mirrors and draws export:
  re-synced at step 9 from whatever this diff becomes.
* Prose documents, except where a test reads them.
* Whether v4-L1 is the right model, which width the record supports, and
  whether the correction should ship. Those are the pre-registration's and the
  owner's. The review asks whether the code implements the designs and whether
  the instruments that will judge it can see.
* Anything outside the four changes, unless the diff touches it.

---

## Risks, in order of what a defect would cost

Each is a question to answer from the code. Where a design or review names a
mechanism, the question is whether the code has it, not whether a test of
the same name exists.

### 1. Pairing that is not pairing

The canonical comparison rests on arms seeing the same primitives. Two arms
can look paired and not be.

* Can any stream's values depend on the order in which entities are visited,
  the number of other entities, the position of a column, or how many values
  another stream consumed? Consider refills, caches of stacked blocks keyed by
  a tuple of names, and the per-draw counter against the draw index the loop
  passes.
* Does any transform still consume a variable number of primitives
  (rejection inside numpy, a draw taken only when a gate passes, a branch that
  reads an extra uniform below one shape and not above it)?
* Is the gamma boost applied at every shape, so a shape crossing 1 between
  arms stays paired?
* Are tie groups and pools keyed by something that survives a change in their
  membership?
* Is the root key specific to city, target and seed, so city-years are not
  correlated with each other?
* Does the incumbent switch share stages with the v4 law in a way that makes
  incumbent-against-v4 differences look paired when they read different
  primitives, or the reverse: does it read the v4 stages under the old names?
* Does any consumer outside the run loop (calibration pass, width-budget
  ablation, `export_draws` across seat laws) read the run's streams and
  advance them?

### 2. Distributions changed by the plumbing

* Is each sampler exact for the law it replaces at every parameter the model
  reaches, including the fallback path on its own, shapes at the
  `DIRICHLET_FLOOR`, and df values the level shock uses?
* Does the incumbent law under the new streams reproduce arm E's law, or did
  a clip, a normalisation, the df resolution or the Student-t constant change
  in passing?
* Is the gamma fallback counted with a denominator, so a rise is visible?

### 3. The mean not conserved, or conserved by the wrong thing

* Does the calibration pass conserve the `pool_spec` centre the design names,
  on its own streams, with recording off and counters reset, or does it touch
  the run's streams or guards?
* Is the falsifier's standard error computed as v2 §1.2 states, over the
  parties it states, with a threshold that follows the party count?
* Under the correction switch, is the centre the calibration conserves the
  corrected one, and is the correction applied once, at the declared place
  relative to `compress_levels`?

### 4. Width counted twice, or the old width still running

* Is the citywide width the v4 curve has replaced removed from the draw, or
  does any old term (level-shock sd at size, Dirichlet concentration, the
  individual path's own shock, the arrival factor for a judged party) still
  add spread?
* Does turnout composition get subtracted as specified, floored, with the
  excess recorded?
* Is the location `m(s)` kept out of the L1 draw, while still fitted jointly
  so the width is not inflated by it?
* Is the newness term added once, to the right population, defined on the
  previous local election in this city?

### 5. Fitting on what it must not see

* Does the width-and-location fit for a target read only cycles before it,
  for every target including the 2016 targets' single-cycle record?
* Does the correction's `m(s)` come from the same out-of-sample fit, and is
  the clamp applied where the design applies it?
* Could a realised result of the target reach the fit, the calibration or the
  correction through a shared cache, a module-level record or a default?

### 6. Judgements leaking

* Can `support`, `overperform`, `sigma_j` or `register` reach a backtest, the
  spec hash or the emit?
* Does the run's judgement hash cover exactly the applied entries, and does a
  hand edit after a run show as declared-and-wrong in `declares.py --verify`
  and `test_intermediates_are_current`?
* Does any code path name a party?

### 7. Guards gone blind

This model has shipped observers that could not see (QC §3). For every guard,
counter and scan the diff adds or rewrites (`41_guards` keys, `stream_keys`,
`gamma_fallbacks`, the mean-error record, the identification hold's record,
the register guards, the stage predicates):

* Does it scan the right population, both directions where the claim is
  bidirectional?
* Can a constructed violation turn it red, and does it go quiet when
  reverted?
* Is its input constructed, or copied from a passing run?
* Did a rewrite of `GUARD_KEYS`, `GUARD_DENOMINATORS` or a stage predicate's
  table make a check vacuous rather than updated?
* Is `width_budget`'s ablation still measuring something, or did its patches
  go inert under the new signatures?

### 8. Stale artefacts and the emit

* Does every pools code change move `pools_sha`, so no stale spec can run
  silently? Does anything in the run read a precomputed intermediate the diff
  changed without a key (`turnout.csv`, `fold*_parameters.csv`)?
* `run_model` recomputes pool geography from code at every run. Can a run on
  the final tree ever combine new geography with old specs, or the reverse,
  without refusing?
* The census-off arm runs on the commit before the census change. Does that
  commit stand alone (emits and runs) with the streams, v4 and the correction
  switch in place?

### 9. The ward and list link

* Is the ward target still derived from the list target by the existing
  ratio, unchanged in form, and does the ward-noise stream keep the
  `(ward, party)` assembly order the tally expects?
* Do the VD turnout blend and noise read their streams once per draw, in the
  VD order the solve uses?

### 10. Census hold mis-keyed

* Is the identification test applied per pool and fitting year, with the
  threshold named in code where the register guard sees it?
* Does a held pool enter the solve through the existing hold path, at the
  city's own rate, and get recorded where `panel_turnout_spread` and the spec
  read it?
* Can the hold fire on a pool the ward table does identify, or miss one it
  should catch, through a units error (reach as share of ward vs of city;
  registered per census adult vs share of roll)?
* Is there any remaining upper bound on registration?

### 11. Results that depend on how the run was cut

* Do drawn arrays depend on `STREAM_CHUNK`, on the total draw count, on the
  order of city-years in a batch, on `PYTHONHASHSEED`, or on whether
  `--run-dir` is given?
* Is a 1,000-draw run the prefix of a 5,000-draw run at the same seed?

---

## What the review returns

For each finding: the file and line, the mechanism, what number it would
move or which guard it blinds, a constructed reproduction where one is
cheap, and a severity (blocks the canonical run / should be fixed before it /
note). Disagreement between reviewers is reported unsplit. The writer does not
amend this brief in response.
