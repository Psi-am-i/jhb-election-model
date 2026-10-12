# Blind review brief — why does the backtest score differently now?

You have the repository. You do not have the lead's reasoning, deliberately.

## The observation

The published page `/about` carries the model's track record: it is scored
against the 2021 local election in eight metros, against three baselines. Its
figures come from `data/processed/validation_2021.json`, generated **2026-08-11
from a 400-draw run per city** (the page's own footer says so).

That artefact was regenerated on **2026-09-27** from the current tree, with the
same script, `src/build_validation.py`. The figures moved:

| | published (11 Aug artefact) | regenerated (27 Sept) |
|---|---|---|
| total error, eight cities | 213.9 | **224.1** |
| beats best baseline by | **+37%** | **+34%** |
| Johannesburg, seats out | **62** | **96** |
| Tshwane, seats out | 47 | 36 |
| Ekurhuleni, seats out | 53 | 38 |
| party rows per city in the artefact | 12 | 15 to 24 |

Some cities improved and Johannesburg got much worse.

## The question, in this order

**1. Is this an implementation error?** That is the first hypothesis, not the
last. Something may be miscounted, misaligned, double-counted, or scored
against the wrong object. The row count per city changing from a uniform 12 to
a variable 15–24 is itself unexplained and may be the whole story or none of it.

**2. If it is not an error, what changed in the model between 11 August and now
that accounts for it?** `MODEL-LOG.md` is dated and append-only and should let
you name the changes in that window. Attribute the movement to specific ones if
you can, and say which you cannot account for.

**3. Could the treatment of INDEPENDENTS explain part of it?** The owner raised
this. `JUDGEMENT-CALLS.md` §1.166 records that the forecast universe drops
`INDEPENDENT`/`IND`, so no simulation can seat an independent, and the model is
**charged** in the backtest for seats independents actually won — it allocates
them to parties and takes the error. Independents took 11,904 votes in
Johannesburg in 2021 (0.645%, rank 10 of 57) and 52 council seats nationally.
Johannesburg is the city that got much worse. Quantify whether this accounts for
any of the movement, or rule it out.

⛔ **Do not assume the new figure is the right one.** Both runs are 400 draws on
one seed. Neither has an interval attached. Part of the difference may be
sampling, and saying how much is part of the answer.

## Ground rules

Read-only. ⛔ **DO NOT RUN `src/montecarlo.py` OR `src/build_validation.py`** —
both write into `data/processed/`, which is gitignored, and running
`build_validation.py` is what destroyed the 11 August artefact in the first
place. Its values survive only in the committed page, `docs-public/about-the-model.md`
at git HEAD, and in `git log -p` for that file. Work from those.

Use `.venv/bin/python` if you compute anything. Quote file paths and line
numbers. Where you are uncertain, name the measurement that would settle it —
and say whether that measurement can be taken without overwriting anything.

## What a useful answer looks like

Not a list of faults. A verdict on question 1, an attribution for question 2,
a number or a refutation for question 3, and an honest statement of how much of
the movement you cannot explain.
