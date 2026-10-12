# Ultra review 3: the model changes that go into the freeze (R1)

**Written 2026-09-29, after the code.** The project's rule is that a brief is
written before the code it covers (CLAUDE.md §4). It was not this time: the
changes were built first, under two blind reviews
(`audits/2026-09-29-pollster-blind/`, and the F5 research spec). This brief is
frozen from here and is not amended once the review starts.

## When

**Before the F8 re-emit**, which rewrites every pool spec
(`data/processed/**/pools_*.json`, gitignored). After the re-emit there is no
clean baseline to compare against. The freeze plan is `TODO.md` §0.

## Scope: the pull request's diff is exactly six files

* `src/pools.py`, `src/montecarlo.py`, `src/theta_residual.py`,
  `src/backtest.py`
* `tests/test_pool_bounds.py`, `tests/test_roster_aware_baseline.py`

The base branch holds the rest of the tree constant; only these six files
differ. Their state before the batch is commit `caa350f`.

## What changed

1. **F3: a pool silenced at a fitting year** (POOLS-REEMIT-QUEUE entry 30;
   MODEL-LOG §1.269; JUDGEMENT-CALLS §L14).
   * `pool_counts`' nested NNLS left an Indian/Asian pool at turnout or
     registration exactly 0 in four specs, and `emit_pools` dropped the pool.
   * The pool is now held at the city's own rate (`_nest_holding_silent`,
     `_silent_pools`, `_nnls`/`_nest` `hold=`); the other pools are re-fitted,
     `PoolCounts.imputed` is recorded, and a cascade guard handles a re-fit
     that silences a second pool.
   * `emit_pools` raises on a pool with no members.
2. **F5: mergers** (MODEL-LOG §1.275; JUDGEMENT-CALLS §O1;
   `audits/2026-09-29-mergers/SPEC.md`).
   * `Merger`, `MERGERS`, `MERGER_RETENTION = 0.75` in [0.5, 0.9],
     `apply_mergers`, `merged_vector`, `MERGER_CONSUMERS`.
   * The roster decides direction. The transfer is r × P, applied only where the
     successor already holds a share: a merger never creates a record.
   * It is applied in `run_model` (citywide and per VD, before
     `absent_from_ballot`), to `prior_pr_share` before the spine, in
     `emit_pools`, and in `theta_residual`.
   * `backtest.FITTED_ON` gains `MERGER_RETENTION`.

## Facts established before this review (lead-verified)

* **Merger-free equivalence.** With `pools.MERGERS = ()`, the live code gives
  every drawn array bit-identical to commit `4711a15` at Johannesburg 2026
  (1,000 draws, seed 20261104, `PYTHONHASHSEED=0`). With mergers on, it does
  not.
* **P1.** In-process, 26 of 26 specs satisfy prereg P1 (`set(pools) ==
  set(categories)`) under the new code, against 22 of 26 before; the four were
  buffalocity 2016 and mangaung 2011/2016/2021.
* **The transfer is exact.** GOOD's 2024 share of 0.225% × 0.75 = 0.1688%
  moves to RISE.

## Hunt list

1. **The hold.**
   * Is the held value, the city's own rate from `_uninformed_rate`, applied
     at the right nesting level in all three solves?
   * Can the hold fire where it should not, on a pool that is legitimately
     empty?
   * Does `panel_turnout_spread`'s exclusion of held transitions leak into
     other cities' bands in a way §1.269 does not state?
   * Is the cascade guard reachable, and correct when it fires?
2. **The re-fit.** The blind review found the hold displaces White and Coloured
   turnout toward the low end of their panel range, at a ward-level SSE cost of
   5–27%. Is there a defect beyond that stated cost, for example a constraint
   dropped when `hold=` is set?
3. **Mergers, direction and scope.**
   * Every consumer of the national baseline and the prior local share: is any
     missed? `arrivals.py`, `gamma_recent.py`, `turnout.py` and `backtest.py`
     are known not to apply mergers. Does that matter for Johannesburg 2026 or
     the backtest?
   * Is `MERGER_CONSUMERS`' two-way AST scan sound?
   * The date and leak guard: a merger dated on or after polling day must not
     fire, and no backtest may see a merger dated after its target.
4. **The no-record-creation rule.** Is it enforced at every consumer,
   including per VD and `prev_local`? Could a successor still acquire a local
   record through `emit_pools`' vector blend or `theta_residual`?
5. **Interaction with `absent_from_ballot`.** The (1 − r) × P remainder is
   dropped and renormalised like any off-ballot party. Is renormalisation
   applied once, not twice, at every consumer?
6. **`artefact_key`, and the one-definition rule.** Does every spec that should
   change after the re-emit change, and every one that should not, not? Is
   there any second definition of the merged baseline?
7. **The tests.** Do the new tests in the two test files prove the four things
   CLAUDE.md §4 requires, including can-it-see and a constructed input? Name
   any mutant of the diff that would survive them.

## What the review may not do

It cannot re-emit, run `montecarlo.py` main, or write under `data/`. The
specs on disk are pre-batch and stale by design until F8.
