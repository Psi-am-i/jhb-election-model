# Working rules for this repository

## The documentation is part of the model, not a description of it

**Whenever the model changes, the record changes in the same commit.** Not
afterwards, not in a cleanup pass. A stale document here is worse than a missing
one: it looks current and cannot be, and every reader downstream — including the
next session, including a reviewer — takes it at its word.

This has already gone wrong more than once. `MACHINERY.md` spent weeks
describing a level layer that no longer ran. The published forecast page carried
ten claims pinned to `turnout_tilt_da`, a lever deleted from `run_model`, and the
stat audit kept reporting "no drift" because a fixed token cannot drift.
`site/plan.html` was served for weeks after no build produced it.

### Which file takes what

| change | goes in |
|---|---|
| a **mechanism** — how something is computed | the function's docstring **and** `MACHINERY.md` |
| a **number** the data did not force | `JUDGEMENT-CALLS.md`, with status, evidence and how to check it |
| a **finding** — including a rejected one, and especially a negative result | `MODEL-LOG.md` (append; never rewrite history) |
| a change in **what counts as better** | `ITERATING.md` |
| a defect in the **inputs** | `DATA-QUALITY.md` |
| a new or changed **source** | `SOURCES.md`, with provenance |
| a **claim on the public site** | `content/<city>/stats.toml` as a token — never typed into prose |

`MODEL-LOG.md` is the record of record. If a thing was measured and rejected, it
belongs there with its number, so nobody spends a day rediscovering it.

### Non-negotiable

- **A rejected idea is written up with the measurement that rejected it.** Three
  of this project's most useful entries are negative results.
- **A constant that is not measured is declared** in `JUDGEMENT-CALLS.md`, or it
  will be mistaken for one that is — and then none of them are trusted.
- **Anything that cannot be tested by the harness is labelled as argued, not
  tested**, wherever it is quoted. `w_bye` and the first-local-election bias
  correction are both in this position.
- **Never type a model figure into prose.** It goes stale silently. Register it
  as a stat token; `build_site.py` audits for typed figures and will name them.
- **Re-record a golden test deliberately and say why in the file.** A silent
  re-record destroys the only guard on the prior.

## Two backlogs, and they do not mix

`PUBLISHING-BACKLOG.md` holds the presentation layer — the interactive, the live
page, the stat tokens. **This repository's working list is the model's ability to
predict, and nothing else.** The owner's standing position is that the page gets
rebuilt when the model is ready, so presentation work is not a competing
priority and is never a reason to change a forecast.

## Iterating, not publishing

Read `ITERATING.md` first. The published forecast is a recent output of an
earlier version — not a benchmark, not a target, not evidence. The only question
is whether the current model predicts PAST elections better than the previous
iteration and better than the naive baselines. If it does not, it does not ship,
however well argued. Worse does not ship.

## Shared artefacts: one writer, and nobody measures while it writes

`data/processed/pools_*.json` is **precomputed**. Changing `src/pools.py` does
nothing until you re-emit it, and re-emitting it changes the baseline of every
measurement anyone else is taking at that moment.

This has cost twice. A lever sweep returned **different answers on two identical
runs** because another worker was re-emitting the artefacts underneath it; two
`EXPECTED_INERT` reasons were written from those unstable readings and had to be
retracted. Partitioning work by *file* is not enough — `pools.py` and
`compare_history.py` do not overlap as files and collide completely as work.

So, when more than one worker is active:

* **Exactly one** may re-emit `pools_*.json`, and it owns them for the duration.
* **Nobody else runs the model, `compare_history`, or any sweep** while that is
  true. Verify at unit level instead, and say so.
* The re-emit and the canonical measurement happen **once, at the end, on a
  settled tree** — and every number quoted anywhere must come from that run.

A number measured against a moving artefact is not a measurement. It reads
exactly like one.

**Since 2026-08-18 the artefacts say what built them.** Every `pools_*.json`
carries an `artefact_key` — city, target, a hash of `config/dimensions.toml`,
and a hash of `pools.py`'s code with comments and docstrings ignored — and a run
prints a named reason when it does not match. That does not replace the rule
above: it stops a stale result being *believed afterwards*, it does not stop the
artefacts moving under a measurement in progress. Re-emit with:

    .venv/bin/python src/pools.py --city <city> --target <year> --emit

Emission is deterministic — re-emitting all eleven specs changed nothing but the
key — so the hazard is re-emitting *while someone measures*, not re-emitting.

**The specs are not tracked by git.** They have no version history, which is why
the key exists.

**`compare_history` runs its nine city-years in parallel processes** (since
2026-08-18), which is safe because they only READ the specs — the rule above is
about who WRITES them, and that is still one worker at a time. Measured at 1500
draws: 499s serial against 169s parallel, a 2.96x speedup, with
`seat_abs_err_coherent`, `crps`, `seat_abs_err` and `median_sum` bit-identical
and the MAE columns agreeing to 6.7e-15 (float summation order, MODEL-LOG
§1.46). Processes rather than threads because `apply_city` and `levels.SD_FLOOR`
are module state.

## Running things

Use `.venv/bin/python`, never bare `python` — numpy is not on the system
interpreter.

    .venv/bin/python tests/run_all.py                  # the suite
    .venv/bin/python src/compare_history.py            # votes and seats vs actual, 9 city-years
                                                       #   runs in parallel by default; --jobs 1 forces serial
    .venv/bin/python src/diagnose.py --city joburg --target 2021 --wards 0
    .venv/bin/python src/arrivals.py                   # the arrival machinery, scored alone
    .venv/bin/python src/theta_residual.py             # the CONDITIONAL sd(log theta),
                                                       #   forward validated, against what
                                                       #   the model actually uses (§1.59)
    .venv/bin/python src/sweep.py                      # obvious-fault sweep

**Before adding a print to find out what something is, ask for a trace.**

    .venv/bin/python src/montecarlo.py --city joburg --target 2021 \
        --run-dir /tmp/t                  # every stage's output, as JSON
    .venv/bin/python src/compare_history.py --run-dir /tmp/t   # one per city-year

`--run-dir` writes each stage of the run — the θ prior and its per-party
`sd(log θ)`, the spine's level and route per party, the centres before and after
the level shrink, the drawn means and bands, and every guard counter — to files
you can read without running anything again. It is **opt-in and changes no
number**: with no `--run-dir` the run is byte-identical, and `test_chain.py`
asserts it.

This exists because the alternative was re-running the whole comparison with a
print added — 499s serial, 169s parallel at 1500 draws — and that cost was being
paid on every investigation. It is a *record*, not a
check: it will happily record a guard that has gone blind. What catches those is
an assertion — and the trace is what makes assertions cheap to write, because
the quantity is already on disk.
