# Route B, measured natively — 2026-09-28

Three scripts, each run from the repository root with `.venv/bin/python` and
`S=<a scratch directory>` in the environment. BLAS pinned to one thread
(`VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
MKL_NUM_THREADS=1`) because Pyodide is single-threaded. None of them writes under
`data/`: each calls `run_model` directly, never `montecarlo.py`.

* `trace_opens.py` (also needs `OUT=<file>`) — every data file a Johannesburg
  2026 run opens, its size, and the `src/` function that opened it, via an
  audit hook. Prints the per-reader totals.
* `routeb_proto.py` (`N=<draws>`) — runs the model once recording what
  `levels._citywide_and_roster` returns for each path, writes that as
  `$S/reduced_table.json`, then runs again with the function replaced by a
  lookup into the table, and compares every `*draws` array of the two runs.
* `routeb_fresh.py` (`MODE=parse` or `MODE=table`) — times a 20-draw run twice
  in a fresh process in either mode, so the table run cannot inherit a cache.

Results and limits: MODEL-LOG §1.265.

## The Pyodide check (pre-registered in `prereg/2026-09-28-route-b-in-pyodide.md`)

* `identity.mjs` — `npm install pyodide@0.28` in a directory outside the repo,
  copy this file there, then
  `node identity.mjs <repo> <draws> <seed> <out.json>`. Runs parse mode then
  table mode in one Pyodide interpreter and writes the table-mode arrays.
* `compare_native.py` — from the repo root,
  `.venv/bin/python audits/2026-09-28-route-b/compare_native.py <out.json>`:
  a native parse-mode run on the same seed and draws, compared array by array.
