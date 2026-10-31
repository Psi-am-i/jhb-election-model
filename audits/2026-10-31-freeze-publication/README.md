# Freeze and scoring lock for Johannesburg 2026, prepared 2026-10-31

Material for the public page (PLAN.md 5.1, DATA-PLAN §7). Nothing here changes
the forecast.

## The three identifiers, reconciled

| identifier | what it hashes | where it appears | status |
|---|---|---|---|
| `ad6ca1dd1e52…` (in `r-ad6ca1dd1e52-d7699945-dirty`) | `forecast_summary.json` with its `_`-prefixed stamps removed (`publication.forecast_content_sha`); the run label adds the site-build commit `d7699945` and `dirty` because that build ran on an uncommitted tree | `site/changes.json`, the publication ledger | recomputes today to `ad6ca1dd1e526113e4b991f4e2359552156773a351d4b88bb33cdd98520858e9` |
| `e1b960fb…` | `freeze.py`'s `content_sha256` of a **1,500-draw** re-run (`freeze.py --draws` defaults to 1500) | `data/processed/forecast_frozen.json`, MODEL-LOG §1.336 | recomputes; does **not** describe the published forecast, which has 5,000 draws |
| `10bdccc05423b0db38b0a52aeb8d6bd192539442e75da113ee07bc224ebc7c4a` | `freeze.py`'s `content_sha256` at **5,000 draws**, seed 20261104: the scenario, the six environment switches, every pool spec's `artefact_key`, each party's median, mean, 5th and 95th percentile, and a sha256 of the full seat-draw matrix | `forecast_frozen_5000.json` here | **the freeze hash to publish** |

Checks (2026-10-31):
- The 5,000-draw run reproduces the published `data/processed/seat_draws.csv`
  draw for draw on its 13 columns: 0 of 65,000 cells differ.
- Run twice, the normal way (`PYTHONHASHSEED=0`), it gives `10bdccc0…` both
  times. An in-process run without `PYTHONHASHSEED=0` gives `5c0b13c6…` with
  identical draws: the freeze records that switch, as designed.
- The content hash covers no timestamp, path or commit; the commit is in
  `provenance` (`28ceae36`; marked dirty only because this folder was
  untracked during the run).

## Files

| file | what |
|---|---|
| `forecast_frozen_5000.json` | the freeze at 5,000 draws |
| `inputs.json` | every repository file the freeze run opened for reading, recorded by a Python audit hook during the run, with size and sha256: 151 files (82 raw election files across the eight metros, 34 processed, 25 judgement files, 8 city configs, `config/dimensions.toml`, `polls.json`). Code is pinned by the commit instead |
| `preflight-strict.txt` | `src/inputs_preflight.py --strict --city joburg --target 2026`, run 2026-10-31: 7 inputs ok, 1 flagged. The flag is the voters' roll's age (the 26 September snapshot is 35 days old). On 2026-10-28 the IEC page, then dated 29 September, matched it in all 135 wards (`rounds/2026-10-23-out-of-sample/now/A2-roll-check.md`) |
| `scoring-lock.json` | the commit and sha256 of each file that defines how forecasts are scored after the election: `score_forecasts.py`, `rank_entries.py`, `reader_seats.py`, `seats.py`, `prediction.py`, `parties.py`, `official_seats.py`, the certified roster `judgements/joburg-2026.toml`, and `judgements/joburg-2026-result-aliases.json` |

## Not done here, for the owner

- `data/processed/forecast_frozen.json` still holds the 1,500-draw freeze.
  Replacing it with `forecast_frozen_5000.json` overwrites a committed artefact;
  that is the owner's call.
- Readers can check these hashes only against public code. `site-sweep-1` is
  not on GitHub yet (the history scan before pushing is open).
- The published `seat_draws.csv` carries 13 parties; the other 65 hold up to
  56 seats between them in some draws. The freeze's draw hash covers all 78.
