# Johannesburg 2026 — Local Government Election Model

A voting-district-level model of the City of Johannesburg council election on
**4 November 2026**: 5,000 simulations over 865 voting districts, both ballots,
the statutory seat formula including overhang, and full enumeration of the
coalition arithmetic the result permits.

**It has been scored, on sixteen city-years.** The whole pipeline is run against
the 2016 *and* 2021 municipal elections in all eight South African metros — each
fitted only on its own wards, its own roll and its own history — and compared
with baselines that need no model at all. It wins on coherent seat error against
uniform swing in most of the sixteen, on both cycles — but **read the per-cycle
split from the run, not from a number typed here**: eight metros inside one cycle
share a national swing, so they are not eight independent facts, and the seat
figures are scored after a relabel that assigns the model's generic newcomer
column to the largest arrival with the outcome in hand (`ITERATING.md`, Key 1).

Regenerate the full comparison with `.venv/bin/python src/compare_history.py`.
The 2021 scoring page is `.venv/bin/python src/build_validation.py --target 2021`;
note that `data/processed/validation_2021.json` is a **400-draw artefact last
generated 2026-08-11** and predates several corrections, so regenerate it before
citing it.

**The forecast, an interactive version, and the full written record live at
[joburg.whysoserious.city](https://joburg.whysoserious.city).** This repository
is the technical layer underneath it: everything needed to reconstruct the
model from public records.

## The record

| Document | What it is |
|---|---|
| [`MACHINERY.md`](MACHINERY.md) | How each stage actually works, and which numbers are measured, argued or declared |
| [`ITERATING.md`](ITERATING.md) | The four-key bar a change must pass to ship, and why the rule is "more honest usually ships" |
| [`JUDGEMENT-CALLS.md`](JUDGEMENT-CALLS.md) | Every constant the data did not force, with its status, its evidence and how to check it |
| [`archive/superseded-docs/METHODOLOGY.md`](archive/superseded-docs/METHODOLOGY.md) | **SUPERSEDED** — the original review brief, archived 2026-08-23. `MACHINERY.md` replaces it |
| [`MODEL-LOG.md`](MODEL-LOG.md) | The running engineering log: findings, obstacles, silent data traps, the assumption register, every decision with its rationale |
| [`audits/ENGINE-SUMMARY-2026-09-05.md`](audits/ENGINE-SUMMARY-2026-09-05.md) | **Where the engine stands as a whole** — accuracy on the record, what is good, what needs work, and what to expect on 4 November. Start here for the state of the model rather than of the code |
| [`audits/`](audits/) | Review briefs and their state documents. `ULTRA-REVIEW-1-pools-reemit.md` is frozen and must not be amended; `ULTRA-REVIEW-1-STATE.md` is the one that may change |
| [`SOURCES.md`](SOURCES.md) | Acquisition recipes for every input: URLs, the non-obvious election IDs, access workarounds, checksum discipline |
| [`DATA-QUALITY.md`](DATA-QUALITY.md) | Defects in the official published records, each with the file, the arithmetic and what it cost us — thousands separators that silently drop 68% of a city's vote, a comma inside a party's name, every independent published under one shared name |
| [`archive/original-plan/joburg-prediction-model-plan-v2.md`](archive/original-plan/joburg-prediction-model-plan-v2.md) | The original build plan — kept as written, including the parts the build later proved wrong |
| [`archive/superseded-pages/model-review.html`](archive/superseded-pages/model-review.html) | The implementation review that found six errors in the first build, and their same-day resolution |

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
python src/turnout.py --target 2026 && python src/byelections.py && python src/gamma_recent.py
python src/fold.py --fold 1 && python src/fold.py --fold 2 --fit-from 1 --transfer gamma

# 4. measure the voter pools and emit the spec the simulation draws from
python src/pools.py --city joburg --target 2026 --emit
python src/pools.py --city joburg --target 2026 --emit --simulation   # reader edition

# 5. the forecast and its outputs
python src/montecarlo.py                 # 5,000 draws; scenario knobs via --config/--set
python src/render_sheet.py               # regenerate the sheet's figures
python src/build_site.py                 # the public site -> ./site
python src/build_portal.py               # the multi-city portal

# `leverage.py` used to be step 5 here. It was retired to
# archive/retired-scripts/ — nothing imported it, nothing ran it, and this
# line was the only thing still claiming it existed. That is why
# tests/test_standalone_modules.py does not accept "named in a .md file" as
# evidence that a module is alive.

# or all of the above in one command
python src/build_all.py --city joburg

# The interactive page is NOT built. `build_interactive.py` refuses at
# import: its in-browser drawer is the old two-bloc engine and has not
# been ported to voter pools, so running it exits 1 by design. It is
# behind `build_all.py --interactive`, where its refusal is survivable.
```

## Scoring it against a past election

Every claim on the [about the model](https://joburg.whysoserious.city/about)
page is regenerated by one command, which runs the model and the baselines
across all eight metros and writes the page from the results. Nothing on it is
typed by hand.

```bash
python src/build_validation.py --target 2021          # ~8 cities, several minutes

# or one city at a time
python src/backtest.py   --city capetown --target 2021    # the model, scored
python src/benchmarks.py --city capetown --target 2021    # the three naive baselines
```

Any backtest prints an **in-sample banner above its numbers** naming every
constant that has seen the election being predicted. A run that reads nothing
implicated says so instead. That accounting is `backtest.FITTED_ON` and it is
measured from the run rather than asserted — `montecarlo.note_constant`
records what was actually consumed.

A new city needs a config and its own ingested history; `cities/*.toml` carries
the structure (council size read from the Commission's own Seat Calculation
Detail, never wards x 2) and deliberately carries **no judgements**, because
the levels are measured per city.

Every scenario assumption is a key in `montecarlo.DEFAULTS`, overridable with
`--config scenario.json` — the same schema the interactive page emits, so a
slider position on the website reproduces exactly here.

## Licence

Free to use and distribute with attribution and a link back to
[joburg.whysoserious.city](https://joburg.whysoserious.city).
Model design: psi@whysoserious.city · part of picnic labs.
