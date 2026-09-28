# Blind review brief — shipping a precomputed reduction to the browser engine

You are reviewing for the owner of a public election forecast for the City of
Johannesburg, which votes on 4 November 2026. The forecast is a Monte Carlo
model in `src/`; the site is live at joburg.whysoserious.city.

**You have the repository. You do not have the lead's reasoning, and that is
deliberate.** The lead's own argument is written at the end of MODEL-LOG §1.265.
**Form your view before reading that paragraph**, then say where you agree and
where you do not.

**Read only. Do not edit any file, do not run `montecarlo.py` (it overwrites the
published artefacts), and do not delegate to other agents.** Running
`audits/2026-09-28-route-b/*.py` is fine; they write only to the scratch
directory you give them as `S`.

## The situation

An interactive page is planned that runs the real model in the browser under
Pyodide, so a reader can move a few controls and re-run the forecast for 2026.
One run today opens 75 data files, 147.7 MB, which a page cannot ship.

Measured on 2026-09-28 (harness and README in `audits/2026-09-28-route-b/`,
numbers in MODEL-LOG §1.265):

* `levels._citywide_and_roster` opens 65 of the 75 files, 132.9 MB. It is called
  66 times in one Johannesburg 2026 run and returns, per election file, the PR
  vote shares and the set of party names on the ballot.
* Serialising those 66 return values gives an 89.2 KB table.
* Replacing the function in-process with a lookup into that table, same seed:
  every `*draws` array of the run is identical. A 20-draw run takes 3 s instead
  of 15 s.

Read `_citywide_and_roster` and `_citywide` in `src/levels.py` — both
docstrings say why the function is deliberately **not cached** — and the
election-file spy in `tests/_support.py` with the tests that use it
(`tests/test_roster_aware_baseline.py`, `tests/test_temporal.py`). One of those
spies is how the project found the 2021 backtest reading a party split from
three years after that election (MODEL-LOG, and commit `f33528f`).

## The proposal, as a mechanism only

The browser build ships the table and, before running the model, replaces
`levels._citywide_and_roster` with a lookup into it. The native model on Atlas
is not changed. No file under `src/` changes.

## What is being asked

1. **Does this let the browser's forecast use anything the native forecast
   would not?** Consider the temporal guards specifically: what they watch, what
   they would stop seeing, and whether that matters for this consumer.
2. **Is the table a second definition of the function?** The project's rule is
   one definition only. What would the build step and the tests have to do for
   the table to remain an output of the function rather than a copy of it?
3. **Coverage.** The table holds exactly the paths one default run asked for.
   Can a reader's control (`dirichlet_scale`, `w_bye`, the seat law, turnout,
   polls — see `audits/2026-09-27-interactive-levers/`) make the model ask for a
   path the table lacks? What should happen then?
4. **Fidelity.** The in-process check compared Python objects. The browser loads
   JSON. Name anything that can differ across that round trip — float
   representation, set ordering, name canonicalisation — and whether it can
   move a drawn number.
5. **The completion predicate.** State the artefacts and tests that must exist
   for this to count as done, each as something that goes red when it stops
   being true (see `QC.md` §5, and `CLAUDE.md` §4 on tests that assert absence).

If the proposal is sound, say so and say what it costs. If it is not, say what
would make it sound, or what to do instead.

## Output

A specification, not edits: numbered findings, each with the file and line it
rests on, what you verified by running or reading, and what you did not. Keep it
under 1,200 words.
