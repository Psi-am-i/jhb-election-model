# S6 — "Play with the model" on the frozen draws: spec, and the review brief

Committed before the review runs. Reissued verbatim or not at all. The
reviewer gets this file and the repository, nothing else from the lead.

## Where things stand (facts, with where to check)

* The model is frozen (MODEL-LOG §1.282). Its draws are exported (S2) to
  `site/draws/base.bin` + `manifest.json`: per draw, seats under four seat
  laws, ward winners, PR shares, pool turnouts (`src/export_draws.py`,
  `tests/test_export_draws.py`).
* The lever grid (S3) is `w_bye` only (owner, DESIGN-decided §11): cells
  `site/draws/w_bye-0/` and `w_bye-1/`, with `site/draws/index.json` listing
  them. **Measured: the cells are NOT paired** — draw i of one cell is not
  draw i of another (pool turnouts equal for the first 79 draws, then
  per-pool correlation ≈ 0.005). `export_draws.write_index`.
* `src/reweight.py` implements the turnout tilt, the poll weight, effective
  draws and weighted quantiles (`tests/test_reweight.py`).
* The page prototype is `interactive/` (`README.md` there): `model.html` +
  `js/model.js` run a JavaScript sketch of the re-weighting on synthetic
  fixtures. The seat code already runs under Pyodide via
  `interactive/tools/sync_py.mjs` → `interactive/py/`.
* Contracts: `audits/2026-09-28-interactive-architecture/INTEGRATION.md`
  §3b–§3c; decided levers: `audits/2026-09-27-interactive-levers/DESIGN-decided.md`
  §7–§14; open items: `TODO.md` §2.

## The proposed build (the lead's spec)

1. **Data.** `model.html` loads `site/draws/index.json`, then the selected
   cell's `manifest.json` and `base.bin` (a cell is fetched only when
   chosen). `placeholder-draws.json` is deleted. Roster, wards and the
   published figures come from the base manifest and the published tokens,
   replacing `placeholder-model.json` on this page.
2. **One definition.** `js/model.js`'s re-weighting is deleted; the page
   calls `src/reweight.py` under Pyodide. `sync_py.mjs` adds `reweight.py`
   to the copied set; a test asserts each served file is byte-identical to
   `src/` and that the copied list equals what the page imports, both
   directions.
3. **Controls.**
   * Turnout by community: one tilt per pool, applied jointly (`reweight`).
   * Polls: one row per poll with its caveat, a toggle each, one trust
     slider (0 = the published forecast).
   * Seat law: the four laws; weights carry across laws by draw index
     within a cell (the export asserts the draws are shared across laws).
   * By-election weight: none / 0.40 (published) / full, choosing a cell,
     shown beside each party's actual by-election swing since 2021
     (`data/processed/byelection_party_deltas.csv`, with wards contested)
     and the model's predicted change at the chosen weight. **Because the
     cells are unpaired**, switching cells re-samples: the page states
     that a change of up to a few seats can be sampling alone, and turnout
     and poll weights are recomputed on the new cell's own draws.
   * Within-community movement: dropped (owner).
4. **Effective draws** (Kish) shown beside every figure; below 200 the
   control that caused it greys out and the figure is withheld.
5. **First paint is static**: the published tokens, no Pyodide. The
   untouched page equals the published forecast exactly (uniform weights on
   the base cell reproduce it; `test_reweight`). Pyodide loads behind it.
6. **Built by `build_site.py`** from `interactive/`, so the number gate and
   `deploy_check` see it; computed regions are marked so the gate does not
   read them as typed figures.
7. **Tests.** Node: untouched page = published figures; one fixed control
   setting gives `reweight.py`'s native output (the Route B identity harness,
   `audits/2026-09-28-route-b/identity.mjs`); a cell switch recomputes
   weights on that cell.

## Questions for the reviewer

1. **Unpaired cells.** Is the treatment in 3 honest and sufficient? Should a
   reader be able to combine a `w_bye` cell with turnout or poll weights at
   all, and how should the page express the re-sampling noise — measured
   how, and against what? Is there a cheaper design that pairs the cells?
2. **The first paint.** TODO §2 says a 300-draw default "prints different
   headline percentages". Under this spec the page uses all 5,000 draws of
   the base cell. Is the untouched page then provably identical to the
   published forecast? What would break that?
3. **The poll control.** DESIGN-decided and TODO §2 say it is "a new
   parameterisation, not a relabelling". Does `reweight.py` as it stands
   implement the decided control, or does something need building first?
4. **Payload and timing.** Three cells at ~0.86 MB gzipped each, plus
   Pyodide and numpy. Is lazy per-cell loading enough? What must be measured
   in a real browser before this ships (TODO §2: "no browser measurement
   exists")?
5. **The number gate.** What exactly must `build_site.py` learn so the
   page's live regions pass `blocking=0` without weakening the gate for
   typed figures?
6. **What is missing** from the spec that the decided design (DESIGN-decided
   §7–§14) or INTEGRATION.md requires — for instance the coalition table,
   the ward map, and the tested claims when a lever moves (TODO §2).
7. **Anything that would make a figure on this page wrong or misleading.**

## Rules

Read-only. Do not run the model, `compare_history`, `export_draws`,
anything with `--emit` or `--publish`, or `wrangler`. You may read any file
and run `tests/run_all.py -k reweight -k export_draws`. Do not delegate.

## Return

Findings, each with where, the defect, and the fix; then one line per
numbered spec item: **sound**, **needs change**, or **missing**.
