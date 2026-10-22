# Mutation night — the harness (F10, PUBLISHING-BACKLOG §13)

**What it answers.** Change the source one small edit at a time and ask, for
each edit: did a test fail, did the forecast's drawn numbers move, or did
nothing change at all? The owner's concern is the third: code that is inactive
or behaving badly and that nothing notices. Every mutant that no test kills is
listed by file, function and line.

Files:

| file | role |
|---|---|
| `night.py` | the orchestrator: `selftest`, `prepare`, `run`, `report` |
| `probe.py` | what runs inside the sandbox: one model run, or a list of tests |
| `mutants.py` | mutant enumeration and application (pure text in, text out) |
| `_cov/sitecustomize.py` | line coverage for child processes of a test |
| `runs/<name>/` | one run: `meta.json`, `mutants/`, `baseline/`, `results.jsonl`, `report.md`, `report.json` |

## Running it overnight

On Atlas, from the repository root, with nothing emitting pool specs:

    .venv/bin/python audits/2026-09-29-mutation/night.py selftest
    .venv/bin/python -u audits/2026-09-29-mutation/night.py prepare --run audits/2026-09-29-mutation/runs/<name> --jobs 7
    .venv/bin/python -u audits/2026-09-29-mutation/night.py run --run audits/2026-09-29-mutation/runs/<name> --jobs 7 --test-budget 60
    .venv/bin/python -u audits/2026-09-29-mutation/night.py run --run audits/2026-09-29-mutation/runs/<name> --jobs 7 --stage2 --modules src/seats.py src/citywide_table.py
    .venv/bin/python audits/2026-09-29-mutation/night.py report --run audits/2026-09-29-mutation/runs/<name>

* `prepare` without `--modules` takes the default population (below). The
  harness mutates **HEAD**, so a module that is not committed does not exist
  for it: `reweight.py`, `reader_seats.py` and `export_draws.py` were
  untracked on 2026-09-28 and are skipped with a message. Name them in
  `--modules` once committed, in a new run directory. A prepared run's module
  list cannot change.
* `prepare` is resumable by stage: an existing pristine copy, model baseline
  or test baseline is reused (`--redo`, `--redo-tests` retake them). Its test
  baseline runs the whole suite once with coverage, so it costs about one
  suite run.
* `run` appends one line per mutant to `results.jsonl` and skips mutants
  already there, so an interrupted night resumes with the same command. It
  refuses to start while another process holds the pool-artefact lock for an
  emit, and holds the read lock itself for the whole run (CLAUDE.md §3).
* **Stage 1** (`--test-budget S`): each mutant gets the model run and the
  cheapest reaching tests up to S baseline seconds, stopping at the first
  failure. **Stage 2** (`--stage2`): every survivor whose reaching tests were
  not all run gets the rest; INERT survivors first. Stage 1 over the whole
  population is the night; stage 2 is targeted (see *Budget*).
* `--budget-hours H` samples a module whose estimated wall time exceeds H,
  stratified by function × operator, with `--sample-seed` recorded in
  `meta.json` and printed in the report.
* `--limit K` runs only K mutants (smoke test).
* Run it from a terminal session. Observed once, cause not established: the
  pilot's first `prepare`, launched from a backgrounded agent shell, timed a
  table-mode model run at 13.5 s; the same run in a foreground shell took
  3.3 s, sandboxed or not. Atlas is an M1 (four performance and four
  efficiency cores); scheduling onto the efficiency cores would explain it
  and is not measured.

## Isolation

* **Never the live tree.** `prepare` extracts `git archive HEAD` into
  `$TMPDIR/mutnight-<run>/pristine`, and each worker gets its own copy. The
  whole tree is extracted, not only `src/` and `tests/`: `tests/_support.py`
  does `os.chdir(Path(__file__).resolve().parents[1])`, so the tests run from
  the copy's root and read `JUDGEMENT-CALLS.md`, `config/`, `cities/` and
  `judgements/` through it. `data/` is excluded from the extract and symlinked
  to the live `data/`; `.venv` and every other untracked top-level entry are
  symlinked likewise.
* **Nothing writes under `data/`.** Every probe runs under `sandbox-exec` with
  `file-write*` denied beneath the live repository's real path, which covers
  writes through the copy's symlinks. `prepare` proves this before anything
  else runs (a write through `<copy>/data/processed/` must be refused), and
  every `run` compares a size-and-mtime snapshot of the whole of `data/`
  against the one taken at `prepare` and reports any file that changed.
* **What is mutated is HEAD**, as committed when `prepare` ran — not other
  agents' uncommitted edits. `meta.json` records the sha.
* Probes run with `PYTHONHASHSEED` = `montecarlo.HASH_SEED`, bytecode writing
  off, BLAS at one thread, and none of `citywide_table.GATES` in the
  environment.

## Population

The default list is the forecast path named in the brief:
`montecarlo.py`, `pools.py`, `levels.py`, `seats.py`, `overhang_regimes.py`,
`citywide_table.py`, and on the interactive's path, once they exist,
`reweight.py`, `reader_seats.py`, `export_draws.py`.

The report's *Population* table is the check on that list: every `src/`
module the baseline `run_model` executes at least one line of, with the count,
and whether this run mutates it. At HEAD `69cc6cc` it names `polling.py`,
`cityconfig.py`, `fold.py`, `parties.py` and `coalitions.py` as forecast path
outside the brief's list; add them with `--modules` to cover them.
`overhang_regimes.py` is a command-line measurement script: the model executes
none of it, and only tests can kill its mutants.

## The operators

`mutants.py`'s docstring is the definition: `cmp` (flip a comparison: boundary
and negation), `const` (int n→n+1, float x→2x, bool flipped), `drop` (a simple
statement in a function body → `pass`; `print` excluded), `negate` (`if`,
`elif`, `while`, conditional expression → `not (…)`), `boolop` (and↔or),
`offbyone` (`range` argument and slice bound → `+ 1`). Docstrings,
annotations, strings and the `if __name__ == "__main__"` block are not mutated.
Every mutant keeps every line number and is checked to parse before it is
kept.

## Which tests run for a mutant

Test selection is by **baseline coverage at test-function granularity**, not
by module: a test that never executes the mutated line cannot observe it, so
running it costs time and adds nothing. `prepare` records, for every test in
`tests/run_all.py`'s `MODULES`, the `src/` lines it executes (`sys.monitoring`,
re-armed between tests; child processes through `_cov/sitecustomize.py`), the
`src/*.py` files it reads as text, and its time. A mutant then gets:

* **body code** — every test that executes a line of the mutated node;
* **a default argument or decorator** — every test that executes the
  function's body (the literal is evaluated at import and used by the body);
* **module- or class-level code** — every test that executes a function, in
  any `src/` module, mentioning a name the statement binds (followed
  transitively through module-level assignments), plus every test in a test
  module whose source mentions the name; a module-level statement binding no
  name gets every test that executes the module at all;
* **plus every test that reads the file as text** outside a code hash
  (register guards, index generators, `inspect.getsource`): they can see an
  edit without executing it.

A read inside `pools._code_sha` is a **hash read** and is handled by the null
control instead. Imports and source lines fetched for a warning or a traceback
are not reads.

**Removed from every subset, and listed in each report:**

* **static** — `STATIC_EXCLUDE` in `night.py`: `test_temporal` (real pipeline
  commands against the real `data/processed`), `test_chain::test_a_diagnostic_run_does_not_overwrite_the_published_artefacts`
  (`montecarlo.main` against the real processed directory),
  `test_chain::test_the_model_refuses_to_run_without_a_pool_spec` (renames the
  live pool spec), `test_draw_record` (a `git archive` of a pinned commit),
  `test_freeze` (the live tree's git state). `tests/run_all.py`'s
  `SERIAL_ONLY` names only `test_chain` as a module;
* **baseline fail / skip** — anything that does not pass on the unmutated copy
  inside the sandbox (a write the sandbox refused, no `.git` in the copy, or a
  test already failing at HEAD);
* **slow** — a test whose baseline time exceeds `--max-test-s` (default 120 s,
  set at `prepare`). Such a test is never run per mutant, and a survivor it
  reaches says so under its function;
* **hash-sensitive** — a test that fails on the module's **null mutant**
  (`pass` appended: the AST, and so every code hash, changes; nothing the
  code does changes). It would fail on every mutant of that file whatever the
  mutant did;
* **unreliable** — a test that killed a mutant and then failed when run alone
  on the pristine copy. A false kill hides a survivor, so the mutant is re-run
  without it and the test is excluded from then on.

## The model run

`run_model` for Johannesburg 2026, seed 20261104, 20 draws (set at `prepare`),
called directly — never `montecarlo.main`. With `citywide_table.install` the
fixed cost falls to seconds (MODEL-LOG §1.265–§1.267), and it is admissible
because the table reproduces every drawn array; `prepare` re-checks that on
this tree (table mode against parse mode, every `*draws` field) and refuses to
continue if it fails. Two consequences, both handled:

* **Table mode cannot see inside `levels._citywide_and_roster`**, which it
  replaces. The parse-mode baseline records the lines executed inside that
  call; a mutant on one of them runs in parse mode.
* **The table's key hashes `levels.py` and `parties.py`**, so any edit there
  makes `install` refuse. For those files the probe re-keys the table to the
  mutant's hash before installing it; the entries are what the unmutated
  function returns, which is exact for every line table mode is used for.

A mutant whose line the baseline run never executes skips the model run: an
unexecuted line cannot change a drawn number. Every `ModelRun` field ending in
`draws` is compared exactly (dtype, shape, `array_equal`; set-valued arrays as
sorted lists), so a change in the last bit of one share counts as moved.

## Reading the report

`report.md`, per run:

* **Outcome per module** — counts per class:
  * **KILLED** — a selected test failed;
  * **MOVED-UNTESTED** — a `*draws` array moved and no selected test failed:
    behaviour nothing checks;
  * **INERT reached** — the model or a test executes the mutated code, and
    nothing moved and nothing failed: the owner's concern (code computed and
    never read, a branch no input takes, a constant nothing depends on), or an
    equivalent mutant;
  * **INERT unreached** — neither the model nor any test executes the code:
    untested, not necessarily dead (a CLI, an error path, another city's
    branch);
  * **TIMEOUT**, **CRASH** — the model or the test process died or hung and no
    test failed. A model CRASH that no test notices is a finding: the browser
    engine would fail and the suite would stay green.
* **Population** — the forecast-path table above.
* **Controls** — determinism (two table-mode runs identical), table = parse,
  each module's null mutant (the model must not move; the tests that fail on
  it are named), and how many mutants moved the draws per module, which shows
  the detector seeing real moves.
* **Tests not run per mutant** — every exclusion with its reason.
* **Survivors, by file and function** — every non-KILLED mutant: line,
  operator, the edit, class, what the model did (`not-executed` = the run
  never reaches it; the moved fields otherwise), tests `run / selected /
  reaching` († = stage 2 still owed), and how many tests execute the code.
  Under each function, the reaching tests that were excluded.

`report.json` holds every result and the exclusions, for anything the markdown
does not show. Read a survivor as a question, not a verdict: an INERT mutant at
20 draws of one city-year can be live in a draw, a city or a year this run did
not take. The `executed by` column and the `model` column together say which.

## Controls, and what they prove

* `night.py selftest` — the comparator sees a one-ulp change in one float cell,
  one seat, one set member, a dtype change and a removed field, and goes quiet
  when each is reverted; every enumerated `seats.py` mutant keeps its line
  numbers; every operator produces mutants.
* `prepare` — the sandbox refuses a write through the copy's `data/`; two
  table-mode runs are identical; table mode equals parse mode; each module's
  null mutant leaves the model identical.
* `run` — every `--control-every` mutants (default 150) a worker re-runs the
  pristine model; if it moved, the run stops and writes `ABORTED`. The model's
  precomputed inputs are hashed at `prepare` and compared at the end.

## Known limits

* **One city-year, one seed, 20 draws.** A branch taken only in another
  city, another year or a rarer draw reads INERT here if no test executes it.
* **Coverage is from the baseline.** A mutant that sends control flow into
  code the baseline never ran is judged on tests chosen by the baseline's
  paths.
* **Selection by name for module-level constants is lexical.** A constant
  reached through `getattr` with a computed name is found only if a test
  executes the module at all or reads its text.
* **Stage 1 is partial by design.** A † survivor is unresolved until stage 2;
  the report marks each one.
* **Hash-sensitive tests are excluded for their file.** They cannot
  distinguish mutants of that file at all, so this loses nothing they could
  have told apart.

## Pilot, 2026-09-28 — `runs/pilot/`

`citywide_table.py` and `seats.py`, run fully (stage 1 with `--test-budget 60`,
then stage 2 on every survivor). The survivor list and the timings are in
`runs/pilot/report.md`; the figures below were read from that run's
`results.jsonl` and `meta.json` and describe that run only.

**Cost, measured** (`results.jsonl`, `meta.json`; 7 jobs on Atlas's M1):

| phase | wall |
|---|---|
| `prepare`: test baseline (whole suite, with coverage) | 1034 s, of which `test_levers_are_live` alone is the tail |
| `prepare`: model baselines (table ×2, parse with coverage) | about 2 min |
| `prepare`: null controls, both modules | 31 s |
| stage 1, 163 mutants, `--test-budget 60` | 8.3 min |
| stage 2, the 83 survivors stage 1 left unresolved | 19.8 min |

Per mutant, both stages, seconds of one worker: `citywide_table.py` median
51.4, p90 90.2; `seats.py` median 6.9, p90 681.2. The spread is the test
subset: a `seats.py` line inside `allocate` is executed by 96–119 tests, most
of which run the model. One table-mode model run took 3.3 s alone and a median
5.1 s with seven running.

**Outcome** (`report.md`, *Outcome per module*):

| module | mutants | KILLED | MOVED-UNTESTED | INERT reached | INERT unreached |
|---|---|---|---|---|---|
| `citywide_table.py` | 107 | 66 | 0 | 10 | 31 |
| `seats.py` | 56 | 37 | 1 | 7 | 11 |

No TIMEOUT or CRASH survives stage 2. Determinism, table = parse, both nulls
and the comparator self-test held; no file under `data/` changed.

**Survivors worth reading first** (the full list is `runs/pilot/report.md`):

* `seats.py:102`, `outside_pool_wards` — `p not in outside` → `p in outside`
  makes `pool_wins` hold only the C/D winners. `seat_draws`, `excessive_draws`
  and `over_draws` move; the 50 selected tests, 28 of which execute the line,
  all pass. Five reaching tests were not run for it (excluded as slow or
  static, listed under the function in the report), among them
  `test_levers_are_live::test_every_tunable_lever_actually_moves_the_forecast`;
  whether one of those would fail is not known. **Re-derived by hand** on a separate `git archive` copy: the same
  three fields move, and `test_seats`, `test_overhang` and
  `test_stage_realisation` pass in full on the mutant.
* `seats.py` `pr_seats` (157), `overhang` (167) and `Allocation.top` (52–53):
  neither the model run nor any test executes them.
* `seats.py:108`, `allocate(seats_available=270)`: no caller relies on the
  default. `:114` (`available <= 0`) and `:128` (`shortfall > len(...)`)
  are boundaries no input reaches; the `ValueError` at `:115` is never raised.
* `citywide_table.py:138`, `build`: dropping `levels._citywide_and_roster =
  real` leaves the recording wrapper installed after the build, and the one
  test that runs `build` passes. Dropping `cityconfig.use(city)` (`:121`)
  also survives.
* `citywide_table.py:112`, `_gates_set`: dropping its `return` survives six
  executing tests. No test sets a gate, so the refusals at `:118` (`build`)
  and `:181` (`install`) are never executed.
* `citywide_table.py:94`, `_key`: the absolute-path branch, which the
  docstring says exists for Pyodide (review finding 5), is executed by no test
  and not by the native run. The refusals at `:101`, `:160` and `:174` are
  not executed either.
* `citywide_table.py` `main` (`:201`–`:219`): the CLI, executed by nothing.

**Found by the sandbox, not by reading:** `test_chain::test_the_model_refuses_to_run_without_a_pool_spec`
renames the live `data/processed/pools_2026.json` for its duration. It is not
in `tests/run_all.py`'s `SERIAL_ONLY`, so the suite runs it beside modules that
read that file. It is now in `STATIC_EXCLUDE`.

**Failing at HEAD inside the sandbox**, and therefore excluded: two
`test_pool_bounds` tests (Mangaung 2016 pool rates do not sum to 1), two
`test_published_page` tests (the committed page differs from the build), four
`test_provenance_gates` tests (the copy has no `.git`). The first two families
fail on the data and the pages, not on the sandbox.

## The full night — estimate from the pilot

`night.py estimate --run audits/2026-09-29-mutation/runs/pilot` prints this
table. It takes each mutant's upper bound (model time plus the baseline
seconds of every usable reaching test) and scales it by what the pilot
measured against its own upper bounds: stage 1 took 0.367 of its bound, both
stages 0.171, at a measured parallelism of 6.5.

| module | mutants | stage 1 core-h | stage 1 wall h | both stages core-h | both stages wall h |
|---|---|---|---|---|---|
| `montecarlo.py` | 2180 | 13.4 | 2.1 | 70.6 | 10.9 |
| `pools.py` | 2538 | 14.0 | 2.2 | 54.3 | 8.4 |
| `levels.py` | 570 | 4.1 | 0.6 | 28.8 | 4.4 |
| `seats.py` | 56 | 0.4 | 0.1 | 2.1 | 0.3 |
| `overhang_regimes.py` | 48 | 0.2 | 0.0 | 0.2 | 0.0 |
| `citywide_table.py` | 107 | 0.6 | 0.1 | 1.0 | 0.1 |
| total | 5499 | 32.6 | 5.0 | 157.1 | 24.2 |

Plus `prepare` (a new run directory: about 20 minutes, dominated by the test
baseline). **So: stage 1 over the whole population fits one night with about
five hours to spare for stage 2; finishing stage 2 everywhere is about three
nights.** Stage 2 is resumable and takes INERT survivors first, so a second
and third night continue where the first stopped; `--budget-hours` with
`--stage2` is not implemented, so bound a night with `--modules`.

The scaling assumes the other modules kill as the pilot's did. A module with
more survivors costs more in stage 2, because a survivor runs every reaching
test and a killed mutant stops at the first failure. `montecarlo.py` and
`levels.py` lines are executed by the largest test sets, so their stage-2 cost
is the least certain figure here. Measured by one pilot, on two modules.

## Cleaning up

Copies live in `$TMPDIR/mutnight-<run>/` (about 40 MB each, one per worker plus
the pristine one) and are reused on resume. Delete that directory when a run
is finished and its report read.
