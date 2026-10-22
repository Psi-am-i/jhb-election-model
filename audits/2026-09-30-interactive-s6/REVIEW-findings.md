# Blind review of the S6 spec (2026-09-30) — findings, condensed

Reviewer read-only at `e7db677`; ran `-k reweight -k export_draws` (12/12,
20/20). Disposition: `SPEC-v2.md`.

**Blockers.** B1 `_headers` serves every path as `text/html` (ES modules refuse
to run). B2 the 17 Sept build-time rule vs a live page; `script_writes` never
reads external modules; `deploy_check` globs top-level pages only. B3 the
served `site/draws/` is tested by nothing; its code hash covers
`export_draws.py`, so it matches no published run. B4 the poll dial's "100 =
poll comes true" collapses the effective draws.

**Findings.** F1 the pairing detail in §1.283 is wrong (79 / 122 equal rows,
scattered; 0 equal PR rows). F2 cell noise must be measured (median SE 0.34–
0.49 seats; a two-cell difference ≈ 0.5–0.7; tails move up to 2). F3 show the
lever's effect through deterministic centres. F4 the tilt targets the cell's
own mean. F5 no cheap pairing. F6 identity proven for part of the page only.
F7 trust→sd missing. F8 poll set must come from `polling.screen`;
`combine_polls` intersects party sets. F9 `ValueError` not `Refused`. F10
turnout with a poll on unchosen. F11 measure payload/latency in a real
browser; use a Web Worker. F12 area turnout silently dropped. F13 no combined
share for the builder hand-off. F14 claims/coalitions/map under a moved lever.
F15 required statements missing. F16 share state unspecified. F17 floor rules
undefined; tails fall below the floor unnoticed. F18 adding `reweight.py` to
worker-api's FILES breaks `test_reader_seats`. F19 the Route B harness is not
native-vs-Pyodide. F20 the by-election column compares ward-level contested
swings with citywide clamped centres. F21 turnout range beyond what was
tested. F22 the largest-party tie-break asymmetry is inherited.
