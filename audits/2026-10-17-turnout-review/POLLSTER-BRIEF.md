# Blind review brief: turnout in the Johannesburg model (2026-10-17)

Issued verbatim to the reviewer. Not to be rewritten by anyone under review.

Load the `pollster` skill and review as a senior election forecaster. Do not delegate to sub-agents. Read-only: do not edit tracked files, write nothing under `data/`, run no `montecarlo.py` script, `compare_history.py`, sweep or emit. You may import modules in-process with `.venv/bin/python` and write scratch output only under `/private/tmp/claude-501/-Users-simondavis-projects-atlas-jhb-election-model/27a9fa73-12b6-40c5-aa8b-cbca7f88e582/scratchpad/turnout-review/pollster/`.

Repository: `/Users/simondavis/projects/atlas-jhb-election-model`, branch `remediation`. Read `CLAUDE.md` and `ITERATING.md` first. The only standard of correctness is real election results.

## The situation

A forecast of the Johannesburg 2026 local election. On 2026-10-16 the model was changed so that turnout reaches the vote: each population pool's turnout is drawn per simulation and the citywide vote is the sum of district votes at that turnout (MACHINERY.md "Turnout enters the vote"; JUDGEMENT-CALLS.md §V1–§V7; MODEL-LOG.md §1.315 and §1.317; code commit `4fb8002`). The owner says he is not happy publishing this model and that it is clearly wrong.

## The evidence

1. `audits/2026-10-17-turnout-review/map/map.md` — a read-only audit of the turnout chain, with code citations and probe runs (probe scripts beside it).
2. `audits/2026-10-17-turnout-review/measure/report.md` and the CSVs beside it — turnout forecast accuracy over 24 backtest city-years, and decompositions of real share changes into between-district turnout composition and within-district change.
3. MODEL-LOG.md §1.317 — the canonical backtest before and after, and three "oracle" arms that fed the target's realised turnout into the model.

Check anything you rely on in the code or data; both reports are agent output and may be wrong.

## The questions

1. Is the turnout mechanism at `4fb8002` fit to drive a published forecast? Answer for the mean forecast, for its width, and for a reader-facing turnout scenario control separately.
2. When realised turnout is fed in, the backtest list error rises. Which explanations does the evidence support, which does it rule out, and which remain unseparated? Name the measurement that would separate the remaining ones.
3. The canonical backtest's list error fell slightly with the change. Is that improvement evidence that the change is right?
4. How should turnout be forecast in this model — level, spatial pattern, by population group, and its uncertainty? Give a ranked list of improvements. For each: what it changes, the real-election measurement that would accept or reject it (stated so it could be pre-registered), its cost, and whether it is estimation from the world or tuning to the model's own output.
5. Should the model ship with turnout entering the vote, with the previous mechanism (a fixed citywide total redistributed over districts), or with something else in the interim? Give the reason in terms of the record.

Report as your final message, with every number labelled (what it is, over which elections) and with what you verified yourself separated from what you took from the reports.
