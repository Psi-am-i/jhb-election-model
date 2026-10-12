# Route B in Pyodide: does the citywide table reproduce the model in the browser engine?

**Written 2026-09-28, before the run.** Not edited afterwards; scored as written.

**The consumer.** The interactive runs the real `run_model` under Pyodide with
`citywide_table.install` in place of `levels._citywide_and_roster`
(`src/citywide_table.py`, MODEL-LOG §1.265 and §1.266). The native model never
installs it. The prediction is therefore about the BROWSER engine: a native
table-against-parse comparison proves nothing about the consumer, because
native never reads the table.

**The run.** Pyodide 0.28.3 under Node 24 (V8's WASM engine; files through
NODEFS, so load times are a floor for a browser), numpy from Pyodide's
distribution, `openpyxl` installed with `micropip`. Johannesburg 2026, seed
20261104, 40 draws, default scenario, no `run_dir`. The harness is
`audits/2026-09-28-route-b/identity.mjs` and `compare_native.py`, committed
with this file.

In one Pyodide interpreter: a parse-mode run, then a table-mode run with the
table loaded by Python's `json` from `data/processed/citywide_2026.json`. Then
a native run on Atlas (parse mode, one BLAS thread) on the same seed and draws,
compared with the Pyodide table-mode arrays.

## Predictions

**P1 — same interpreter, exact.** Every `*draws` array of the Pyodide table-mode
run is `np.array_equal` to the Pyodide parse-mode run. Mechanism: the lookup
returns the same dicts and sets the parse returns, and both runs share one hash
seed, one numpy and one libm.

**P2 — across engines, seats exact, shares within 1e-12.** Against the native
run, every integer-valued array (seats, ward seats, ward winners, the
excessive and overhang draws) is exactly equal, and every float array differs by
at most 1e-12 absolute. Mechanism: Pyodide has its own hash seed, numpy build and
libm, so floats may differ in the last places (the blind review measured up to
4.7e-16 natively across hash seeds). A seat moves only if a share sits within
that distance of an allocation threshold, which is not expected in 40 draws.
**If a seat does differ, the predicate "the browser reproduces Atlas" is false
at this tolerance, and the page cannot claim its default reproduces the
published run.**

**P3 — the files that leave.** In table mode, the Pyodide run opens exactly two
election files, `lge2021_JHB_vd_party_clean.csv` and `npe2024_JHB_vd_party.csv`,
both through readers other than `_citywide_and_roster` (MODEL-LOG §1.266).

**P4 — time.** The table-mode 40-draw run takes 4–9 s and the parse-mode run
20–35 s. Derivation: natively a 20-draw run is 3.0 s with the table and 15.0 s
parsing (§1.265); Node Pyodide was 1.7× native on the fixed cost and 48.3 ms per
draw (§1.264), so the table run is about 3.0 × 1.7 plus 40 × 0.048, and the
parse run about 15 × 1.7 plus the same. The range is wide because the 1.7× was
measured on the parse path, which is mostly file IO under NODEFS; the table path
is mostly Python, and the WASM penalty on pure Python may be larger.

## What would falsify the approach, not just a number

* **P1 failing** means the table is not a faithful stand-in even inside one
  interpreter. Route B does not ship until that is explained.
* **P2 failing on seats** does not stop Route B, but it forbids the page from
  presenting its untouched state as the published forecast by re-running it.
  Decision §7 already shows the published 5,000 draws before any control moves,
  so this bears on what the page says after a control moves, not before.
