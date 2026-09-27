# What the interactive ships, and why it is not 141 MB

The open question since A2 was measured: one `run_model` call opens **75 files
totalling 140.9 MB**, and no page can ship that. Three routes were named and
none was costed. They are costed here.

## What the 141 MB actually is

Measured with an audit hook on `open`, one 5-draw Johannesburg 2026 run:

| group | files | MB | share |
|---|---|---|---|
| **other metros' election results** | 56 | **107.3** | **76%** |
| Johannesburg's own | 11 | 31.8 | 23% |
| census / covariates | 2 | 1.5 | 1% |
| everything else | 6 | 0.2 | — |

The largest single files are `lge2021_ETH_vd_party_clean.csv` (8.6 MB),
`lge2021_CPT` (8.0), `lge2021_TSH` (6.3). **A Johannesburg forecast reads
eThekwini and Cape Town at voting-district level.**

## Why it reads them, and why that is the answer

`levels.py:868-880`. The other metros are opened for one purpose: to build the
**theta record**, the party-level transition ratios between consecutive local
elections. Each file is passed to `_citywide()`, which reduces a
voting-district table to **citywide party totals** — and the ratios are formed
from those totals.

So 107.3 MB of CSV exists to produce, for 52 parties, a list of
`(ratio, weight)` pairs.

    theta_record: 52 parties, serialised 18.8 KB

**107.3 MB becomes 18.8 KB — a reduction of about 5,700 times — and no number
changes, because `_citywide` is a pure reduction.** The browser does not need
the other metros. It needs a table those metros produce.

## The three routes, costed

| | route | payload | what it costs |
|---|---|---|---|
| **A** | **Prune** — ship only what Johannesburg needs | **~33 MB** | ⛔ Cannot be done as stated. The other metros are not surplus; deleting them deletes the theta record, which is the evidence-keyed blend (MODEL-LOG task #22, a 14% gain held out by metro). Pruning to "Johannesburg only" is a model change that removes a measured improvement. |
| **B** | **Precompute the reductions** — serialise the theta record and the census read, enter the model below them | **≈ 20 KB + Johannesburg's own** | Nothing. `_citywide` and the census read are pure functions of files that do not change between runs. The page runs the same `run_model` on the same numbers. It also removes `openpyxl` and the spreadsheet parse from the load path, which A2 measured as a large share of the 25 s fixed cost. |
| **C** | **Ship the fixed stage's output as an artefact** — precompute everything up to the draw loop | smallest | The page no longer runs the model's setup, only its draws. "The page runs the real model" stops being literally true in the way §9 means it, and the self-check has less to compare. |

## Recommendation

**Route B.** It is not a compromise between A and C — it is the observation that
the 141 MB is an implementation detail of a reduction, not an input to the
forecast. It keeps §9's "no second definition to drift" exactly, because the
page runs the same code on the same numbers; what changes is that a pure
function is evaluated once on Atlas instead of once per reader.

⛔ **The thing that makes B safe is also the thing to test.** The precomputed
record must be byte-identical to what the live path produces, checked in the
suite, or B becomes a second definition of the theta record — the precise
failure §9 chose Pyodide to avoid. The check is cheap: rebuild the record from
the CSVs and compare with the shipped JSON.

⚠️ **What B does NOT solve.** Johannesburg's own 31.8 MB is still there. It has
not been broken down by what the draw loop needs against what its setup needs,
and that is the next measurement. Route B is worth taking before that work
because it removes three quarters of the problem and can be checked in an
afternoon.

## What this decides, and what it does not

**Decided, pending the owner:** the browser ships derived tables, not the
raw archive, and the model code is unchanged.

**Still open:** the draw count and what the page prints before a reader touches
anything (TODO B1); whether Johannesburg's own 31.8 MB needs the same treatment;
and the browser timing, which has never been measured in a browser (TODO D7).
