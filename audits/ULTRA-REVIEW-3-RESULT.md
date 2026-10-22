# Ultra review 3: result (2026-09-29)

Run by the owner as `/ultrareview 17` (the last of three free runs) on PR #17:
the six-file model diff, brief `ULTRA-REVIEW-3-freeze-model.md`, frozen at
`6104020`.

**One finding, severity nit, verified by the lead by reading
`src/pools.py`.**

* **Where:** `emit_pools`' merger blend loop, `src/pools.py:6204-6216`.
* **What:** it passes each merger the successor's pre-merger mass. On a second
  merger into the same successor, the already-blended vector is weighted with
  the original mass, so the second predecessor is over-weighted.
* **Why it is latent:** today's two declarations have distinct successors
  (RISE, ActionSA). The two pending ActionSA declarations would move zero,
  since P = 0, so `merged_vector` returns the vector unchanged.
* **Fix:** a running mass per successor, with a test that fails on the unfixed
  code. Being applied by an agent before the F8 re-emit.

**No other finding** across the hunt list: the hold, the re-fit, merger scope
and direction, the no-record rule, renormalisation, `artefact_key` and the
tests.

The two blind reviews and the zero-cell and seed-survival measurements stand as
the other evidence on this batch.
