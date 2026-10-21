# Rebuild checklist, from the pre-rebuild review (2026-10-21)

Every item is closed here before the canonical run (`open-notes-before-runs`).
Reviewer A covered the code, Reviewer B the record; their reports are in this
session's transcript and summarised in MODEL-LOG §1.329.

## What the rebuild must run, and what it can skip

Model code has not changed since a9754ed apart from `src/fetch_byelections.py`,
which no model path reads. `declares.py --verify` (2026-10-21): every pool
spec, the width record, `bye_value.json` and the group-share record declare
current; the nine artefacts declaring wrongly are outputs the rebuild
regenerates (`history.json`, `forecast_summary.json` and the three regime
summaries, `forecast_frozen.json`, the three `site/draws` manifests).

So, owner's instruction ("anything we do not need to run ... we should do
that"):

- **Skip the full re-emit.** No `pools.py` code change goes in before go-live;
  the queued items that would force one (below, "after go-live") wait.
- **If the ActionSA call is entered:** it changes `judgements/joburg-2026.toml`,
  which is in the Johannesburg 2026 spec's key and the width record's key.
  Re-emit that one spec, then `width_record.py --emit` (after `bye_value.json`
  and the group-share record, which are current and need no re-emit).
- **The backtest (`compare_history`)**: no model code changed since a9754ed.
  §1.328's arm P, run at the clean f30f913 tree, reproduced all 24
  `history.json` rows (list-vote error within 1.47e-11, seat errors
  identical). `history.json`'s manifest records a9754ed with `git_dirty: true`;
  re-run only if the freeze's provenance check refuses that. A judgement on
  Johannesburg 2026 does not reach any backtest row.

## Before the rebuild

- [ ] **ActionSA call**: the owner's answer to OWNER-DECISIONS item 1 (18.1% or
      12.6%), entered with reason in `judgements/joburg-2026.toml` and
      JUDGEMENT-CALLS; forecast reported with and without it.
- [x] **A red guard that cannot see** (Reviewer A 1): `tests/test_pool_bounds.py`
      `test_no_emitted_composition_weight_is_arithmetically_impossible` fails on
      seven known 2011 DA cells (MODEL-LOG §1.321 P8, census shares held flat to
      2011). Exempt exactly those seven cells, each citing §1.321, so the test
      goes red on any new cell. A test change: written, then reviewed by another
      agent.
      Done: 3f0e019 and the commit after it (`KNOWN_2011_FATAL`, exact ratios,
      tolerance 1e-3), reviewed. Johannesburg 2011's headroom is 0.0006, so a
      rebuild that moves that spec at all turns the test red (fails safe). The
      test does not scan the 2026 spec: a future target has no result to check.
- [x] **By-election deltas have no run-time key** (Reviewer A 2): regenerate
      `data/processed/byelection_party_deltas.csv` with `byelections.py` into a
      scratch directory and diff it against the live file; confirm the Gauteng
      rows of `byelections_Gauteng_vd_party.csv` and `byelections_SA_vd_party.csv`
      still agree (they did on 2026-10-21: 1,385 rows identical).
      Done 2026-10-21: `byelections.py --city joburg --target 2026` into a
      scratch directory gives all three files byte-identical to the live ones.

## The rebuild, in order (with the owner's go-live yes, OWNER-DECISIONS item 7)

1. `src/backup_ignored.py`.
2. If the ActionSA call is entered: `pools.py --city joburg --target 2026
   --emit`, then `width_record.py --emit` (`--emit` writes data/ even with
   `--out`).
3. `inputs_preflight.py --strict --city joburg --target 2026`; the voters'
   roll snapshot is 24+ days old (read in a browser and committed under
   `archive/iec-registration-<date>/` if the IEC page has changed).
4. The freeze, `export_draws`, the site draws.
5. Old-against-new report (QC.md §4c) if any Johannesburg 2026 number moved.
6. Whole suite once for the UAT version; failures compared with the known
   baseline set.
7. UAT build on `site-r11`; `joburg-seats` re-synced and redeployed only if
   `src/reader_seats.py` or its import closure changed, site first
   (`docs/DEPLOY-UAT.md`).

## After go-live (not blocking)

- The pools.py refusal when the city's national results file is missing (MK
  would be seeded and lose its by-elections, §A60). A `pools.py` code change:
  forces a full re-emit.
- `cities/joburg.toml:98`, `cities/tshwane.toml:137`: stale "w_bye derived per
  class" comments (move `cities_sha`, so batched with a re-emit).
- `src/pools.py:2953` and `:2968`: the same comment paragraph twice.
- Window wording disagrees: `backtest.py` NOT_FITTED says "2022-02 to 2026-06",
  `blended_centres` and `test_levers_are_live` say "2022-06 to 2026-02"
  (Johannesburg's contests).
- Give `byelection_party_deltas.csv` an artefact key that `run_model` checks.
- Unkeyed inputs (Reviewer A 5): `width_record_key` omits the previous local
  file, the national baseline and the θ-record files; the group-share key is
  code-only.
- MK's drawn mean fell while its centre rose when `w_bye` went to ½ (§1.323
  P3, unexplained).
- Experiment scripts save `seat_abs_err_coherent` as well as `seat_abs_err`
  (MODEL-LOG §1.329).
- Re-measure `SPLINTER_PARENT_WEIGHT` (owner, OWNER-DECISIONS item 6).
- Tshwane (owner: after Johannesburg is live).
