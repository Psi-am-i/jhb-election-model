# Johannesburg 2026 — Local Government Election Model

A voting-district-level model of the City of Johannesburg council election on
**4 November 2026**: 5,000 simulations over 865 voting districts, both ballots,
the statutory seat formula including overhang, and full enumeration of the
coalition arithmetic the result permits.

**The forecast, an interactive version, and the full written record live at
[joburg.whysoserious.city](https://joburg.whysoserious.city).** This repository
is the technical layer underneath it: everything needed to reconstruct the
model from public records.

## The record

| Document | What it is |
|---|---|
| [`METHODOLOGY.md`](METHODOLOGY.md) | The review brief: what is predicted, how each stage works, what was validated and what cannot be |
| [`MODEL-LOG.md`](MODEL-LOG.md) | The running engineering log: findings, obstacles, silent data traps, the assumption register, every decision with its rationale |
| [`SOURCES.md`](SOURCES.md) | Acquisition recipes for every input: URLs, the non-obvious election IDs, access workarounds, checksum discipline |
| [`joburg-prediction-model-plan-v2.md`](joburg-prediction-model-plan-v2.md) | The original build plan — kept as written, including the parts the build later proved wrong |
| [`model-review.html`](model-review.html) | The implementation review that found six errors in the first build, and their same-day resolution |

The documents are canonical here; the website renders reader editions of them.

## Reproducing the model

Raw data is not committed (see `SOURCES.md` for why and for every acquisition
recipe); `data/archive_manifest.csv` carries the SHA-256 of every input so a
rebuild can prove it is working from the same bytes.

```bash
python -m venv .venv && .venv/bin/pip install numpy pandas geopandas markdown

# 1. acquire (see SOURCES.md — some downloads need a real browser session)
python src/fetch_iec.py && python src/fetch_boundaries.py && python src/fetch_byelections.py
python src/ingest_npe.py ... && python src/ingest_lge.py ...

# 2. verify the seat allocator against three published councils — exact or exit 1
python src/validate_seats.py --year 2021
python src/validate_seats.py --year 2016
python src/validate_seats.py --year 2011 --seats 260

# 3. build the model layers
python src/build_crosswalk.py && python src/build_geo.py && python src/build_concordance.py
python src/turnout.py && python src/byelections.py && python src/gamma_recent.py
python src/fold.py --fold 1 && python src/fold.py --fold 2 --fit-from 1 --transfer gamma --entrant ASA=0.1812

# 4. the forecast and its outputs
python src/montecarlo.py                 # 5,000 draws; scenario knobs via --config/--set
python src/leverage.py                   # per-ward turnout elasticity
python src/render_sheet.py               # regenerate the sheet's figures
python src/export_interactive.py && python src/build_interactive.py
python src/build_site.py                 # the public site -> ./site
```

Every scenario assumption is a key in `montecarlo.DEFAULTS`, overridable with
`--config scenario.json` — the same schema the interactive page emits, so a
slider position on the website reproduces exactly here.

## Licence

Free to use and distribute with attribution and a link back to
[joburg.whysoserious.city](https://joburg.whysoserious.city).
Model design: psi@whysoserious.city · part of picnic labs.
