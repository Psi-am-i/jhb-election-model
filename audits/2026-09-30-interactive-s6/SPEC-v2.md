# S6 build spec, v2 — after the blind review and the owner's decisions (2026-09-30)

Supersedes the spec in `SPEC-and-review-brief.md`. Review findings are cited
as B1–B4, F1–F22 (the review report is summarised in `REVIEW-findings.md`).

## Owner's decisions (2026-09-30)

1. **Live figures are exempt from the build-time rule, clearly labelled.**
   The untouched page is ordinary ledgered `{{tokens}}`. Figures computed from
   a reader's settings appear only inside LIVE regions: they hold no
   build-time digits, carry a visible label ("computed in your browser from
   your settings"), and only allow-listed modules may write into them.
   `deploy_check` scans every page, recursively.
2. **Poll dial: 100 = the poll's own sampling error.** Trust t ∈ [0, 1] maps
   to the likelihood width `sd(t) = poll_sd / t` (t = 0 → `sd = inf`,
   exactly uniform), with `poll_sd` from `polling.poll_sd` for that poll.
   A JUDGEMENT-CALLS entry records the mapping.
3. **Turnout by area is dropped for launch** (F12).
4. **Cells stay unpaired; the noise is measured and shown** (F2, F3, F5).

## Lanes (parallel, disjoint files; merged serially by the lead)

### Lane R — `src/reweight.py`, `tests/test_reweight.py`, `JUDGEMENT-CALLS.md` (one new entry)

* `poll_trust_sd(poll: dict, share: float, trust: float) -> float` —
  decision 2; `trust == 0` → `inf`; refuses trust outside [0, 1].
* `poll_weights(..., trust=...)`: accepts `trust` (preferred) or `sd`.
* `page_polls(target) -> list[dict]` — the poll set, from
  `polling.screen` / `polling.metro_polls` only (F8); a poll the model's own
  rules exclude never appears.
* `combine_polls` must not shrink the party base to the intersection when a
  poll names fewer parties: renormalise each poll to its own named parties
  and combine only over parties at least two polls name, else refuse (F8).
* `_on_polled_base` raises `Refused`, not `ValueError` (F9).
* Turnout with a poll on (F10): **turnout is pinned at the published mean**
  when a poll is on; `turnout_tilt` gains `pin_to=` for that. Stated on the
  page.
* A tail rule (F17): `figure()` returns `withheld: True` when the tail
  effective draws for the quantile shown fall below `MIN_EFFECTIVE_DRAWS`.
* `sampling_se(values, weights, q) -> float` (bootstrap-free: the asymptotic
  SE of a weighted quantile, or a documented approximation) for F2.
* Tests: each new function against a constructed case; uniform weights
  still reproduce the published figures; the trust mapping's endpoints.

### Lane E — `src/export_draws.py`, `tests/test_export_draws.py`, new `tests/test_served_draws.py`

* Manifest additions per cell: `centres` (each party's deterministic
  blended centre, from `run_model`'s centres, F3); `combined_share` block
  per draw (F13) if `run_model` exposes the combined vote, else a stated
  refusal in the manifest; `published_run` = the ledger run id and the pool
  artefact keys (B3); `model_sha256` over the model's import closure only,
  excluding `export_draws.py` itself (B3, INTEGRATION §2 `model_version`).
* `tests/test_served_draws.py`: unpacks `site/draws/base.bin` (the served
  bytes) and checks it against `seat_draws.csv`, the `regime_*` CSVs,
  `forecast_summary.json` and `ward_winner_probs.csv`; checks each cell's
  manifest `published_run` against the ledger's latest run; skips loudly if
  `site/draws/` is absent.
* The lead re-exports all cells after this lane merges.

### Lane G — `src/build_site.py`, `src/stats.py`, `src/deploy_check.py`, their tests

* `_headers` (B1): correct `Content-Type` for `/draws/*`
  (`application/octet-stream`, and `.json`), `/py/*` (`text/x-python`),
  `/js/*` and `*.mjs` (`text/javascript`), `.json`, `.wasm`
  (`application/wasm`). Test: every non-HTML file under `site/` matches a
  non-HTML rule.
* LIVE regions (decision 1): a marker (`data-live="<name>"`) that the number
  scan treats as containing NO build-time digits (a digit inside one at
  build time is blocking); NOT a `GENERATED_MARKERS` entry. `script_writes`
  also reads external `<script src>` modules; only modules in
  `stats.LIVE_WRITERS` may write, and only into LIVE regions.
* `deploy_check` globs `site/**/*.html`.
* Tests: a constructed page with a typed digit in a LIVE region is blocked;
  an unlisted module writing figures is blocked; a nested page is scanned.

### Lane P — `interactive/**` only (page, JS, tools, node tests)

* Delete `js/model.js`'s JavaScript re-weighting; run `reweight.py` under
  Pyodide in a **Web Worker** (F11); debounce slider input.
* `tools/sync_py.mjs`: a separate PAGE list (`reweight.py` and its imports)
  beside the seat Worker's `FILES` (F18); both hashed into the manifest;
  test both directions.
* Data: `site/draws/index.json` → the chosen cell's manifest + `base.bin`,
  fetched lazily. Roster names and colours from the published tokens/fixture
  until Lane E's manifest carries them.
* Controls: turnout by community (range limited to what was tested,
  ±5 points Black African; other pools labelled "argued, not tested", F21);
  polls (toggle each from `page_polls`, one trust slider with the site's
  position "zero trust" stated, F15); seat law (four); by-election weight
  (three cells) with the evidence column labelled per F20 and the noise rule
  per F2 ("within sampling noise" when under 2·√(se_a² + se_b²)).
* Floor (F17): grey the last-moved control; withhold any figure `figure()`
  withholds.
* First paint: the published tokens stay until a control moves (F6); the
  tested claims, coalition table and ward map show "of the published
  forecast" once a control moves (F14).
* Share state (F16): lever positions in the URL, bounded and validated on
  load, with `model_version`.
* Tests (F19): a harness that computes a fixed fixture natively with
  `.venv/bin/python`, stores it, and compares Pyodide's output to it.

## Release gates (the lead, after merge)

Re-export the cells; full suite; a real-browser load of `/play` against a
`wrangler versions upload` preview (B1, F11) with timings recorded; a blind
review of the built page before it is published.
