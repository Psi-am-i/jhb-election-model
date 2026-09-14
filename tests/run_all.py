"""Run the whole suite without pytest.

pytest is not installed in ``.venv`` (``python -m pytest`` reports "No module
named pytest"), so this is the stand-in:

    ./.venv/bin/python tests/run_all.py

If pytest is ever installed, prefer it -- every test file here is written to be
collected by it unchanged:

    ./.venv/bin/python -m pytest tests/ -q
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module  # noqa: E402

# THE ORDER IS DELIBERATE — cheap and structural first, model runs last — but
# THE MEMBERSHIP IS NOT A CHOICE. This list was hand-maintained, and on
# 2026-08-25 `tests/test_freeze.py` was written, committed, and never collected:
# the suite reported 201/201 green while five new tests did not exist as far as
# the harness was concerned. A test that is not collected is worse than one that
# is missing, because it reads as coverage.
#
# `test_every_test_module_is_collected` below now fails if any tests/test_*.py
# is absent from this list, so the next one cannot vanish the same way.
#
# THE PHASE A BLOCK (2026-08-26) — ARCHITECTURE.md "Order of work", step A:
# "declare and TEST the seams that already exist. No refactor." Seven functions
# that `run_model` already calls through clean signatures had no value test:
# `allocate_with_overhang` and `ward_parts` had none at all, `solve_and_predict`
# and `ward_pr_ratios` were named only in a comment and a docstring, and
# `spine`, `theta_prior` and `blended_centres` were used as FIXTURES to build
# other tests' inputs while nothing asserted on what they returned.
#
# A fixture is not coverage. `tests/test_drawer.py:410` had already recorded the
# consequence: the goldens "did not move when §1.49 changed `theta_prior`: they
# were not reaching it."
MODULES = ["test_seats", "test_overhang", "test_drawer", "test_temporal",
           "test_chain",
           "test_delivery_proof",
           "test_standalone_modules",
           "test_pool_conservation", "test_pool_bounds", "test_regressions",
           "test_calibration_report", "test_ipf_feasibility",
           "test_levels_dispersion", "test_polling_sd",
           "test_polling_synthetic", "test_polling_register",
           "test_register_matches_code", "test_data_coverage",
           "test_intermediates_are_current",
           "test_freeze",
           "test_spine", "test_theta_prior", "test_ward_pr_ratios",
           "test_ward_parts", "test_solve_and_predict",
           "test_blended_centres",
           "test_levers_are_live", "test_build_all", "test_stat_freshness",
           "test_publication_ledger", "test_published_page",
           "test_hex_cartogram",
           # Added 2026-09-12 with the Phase 0 instrument repairs.
           # Membership is not optional: `test_every_test_module_is
           # _collected` turns the suite red for any `tests/test_*.py`
           # missing from this list.
           "test_scoreboard_disclosure",
           "test_diagnose_baselines",
           "test_roster_fails_closed",
           # Added 2026-09-13 with the Phase 1 repairs. Same rule as the block
           # above: a module that is written, committed and never listed here
           # reads as coverage and is not.
           "test_roster_aware_baseline",
           "test_scored_universe",
           "test_panel_wiring",
           # Added 2026-09-13 with the stage observers. Same rule again:
           # membership is not a judgement, only the position is.
           "test_stage_inputs",
           "test_stage_realisation",
           "test_stage_estimation",
           # Added 2026-09-14 with the provenance gates. Same rule: a module
           # that is written and never listed here reads as coverage and is
           # not, and `test_every_test_module_is_collected` says so. It said so
           # twice in one day: `test_covariate_fail_open` landed from the
           # fail-open work (§1.233) and was uncollected on the same run.
           "test_provenance_gates",
           "test_covariate_fail_open",
           # Added 2026-09-14 with POOLS-REEMIT-QUEUE entries 21-25. Same rule
           # as every block above, and it has now bitten three times: a module
           # that is written, committed and never listed here reads as coverage
           # and is not. All four are fault-injection guards for fail-open or
           # cry-wolf paths in `pools.py`, and none of the four had anything in
           # the suite before this.
           "test_prior_local_fails_closed",
           "test_census_refusal_is_not_swallowed",
           "test_declared_reach_matches_ward_reach",
           "test_artefact_key_discriminates",
           # Added 2026-09-14 with the projected-roster declaration.
           # Same rule as every block above. This one guards a MESSAGE,
           # which the suite otherwise has no habit of doing — but the
           # message is the only thing standing between a reader and a
           # forecast built on an assumed ballot, and its population
           # check is a bidirectional scan of `pools.resolve_roster`'s
           # own AST, which goes stale the moment a fourth roster
           # source is added and nobody notices.
           "test_projected_roster_declaration"]


# MODULES THAT MAY NOT RUN CONCURRENTLY WITH ANYTHING ELSE.
#
# Everything else in this suite writes only into temporary directories, which
# is what makes module-level parallelism safe at all — checked file by file.
# These do not:
#
#   test_chain — `test_a_diagnostic_run_does_not_overwrite_the_published_
#     artefacts` runs `montecarlo.main` against the REAL processed directory,
#     because that is the path §1.118 broke and a temporary one cannot supply
#     the pool spec. It snapshots and restores the three published artefacts,
#     but a concurrent module reading them mid-test would see a 20-draw
#     forecast. It is correct AND it is not concurrency-safe.
#
# Being on this list costs wall clock, so a module earns its place by touching
# state outside a temp directory — not by being slow or by being important.
#
# ⛔ `test_levers_are_live` WAS PUT HERE AND IT MADE THE SUITE SLOWER. The
# reasoning was sound and the measurement refuted it: the module is already
# parallel inside (~7 workers over ~108 run_model calls, §1.115), so nesting it
# in a 7-worker pool oversubscribes 8 cores — module time rose 812s -> 982s.
# Running it alone removed that. It also left SEVEN CORES IDLE for its whole
# 362s, and wall clock went 586s -> 679s: the oversubscription cost less than
# the idleness. Reverted, and the lesson is scheduled instead — see
# LONGEST_FIRST. §1.121
SERIAL_ONLY = {"test_chain"}

# LONGEST JOB FIRST. `pool.map` starts work in the order given, so a 362s module
# submitted last finishes ~362s after the pool would otherwise have drained. The
# fix is not to isolate it but to START it first, which is the oldest scheduling
# heuristic there is. Named rather than sorted by a stored timing, because a
# timings file would be one more artefact to go stale; the profile is printed on
# every run and this list is three names long.
LONGEST_FIRST = ("test_levers_are_live", "test_levels_dispersion", "test_drawer")


def _run_one(name: str) -> tuple[str, int, str, float]:
    """Import and run one module, capturing its output. For a worker process."""
    t0 = time.monotonic()
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            module = importlib.import_module(name)
            failed = run_module(vars(module))
    except BaseException as exc:                       # noqa: BLE001
        # A module that dies on IMPORT must be a failure, not a lost future.
        buf.write(f"\n!! {name} raised {type(exc).__name__}: {exc}\n")
        failed = 1
    return name, failed, buf.getvalue(), time.monotonic() - t0


def select(patterns: list[str] | None, skip: list[str] | None) -> list[str]:
    """The modules to run. A pattern matches by substring, so `-k poll` works.

    THE DEFAULT IS EVERYTHING. A subset is for iterating; it is not a run of
    the suite, and `main` says so in its output rather than letting a partial
    green be quoted as a full one.
    """
    chosen = list(MODULES)
    if patterns:
        chosen = [m for m in chosen if any(pat in m for pat in patterns)]
        unmatched = [pat for pat in patterns
                     if not any(pat in m for m in MODULES)]
        if unmatched:
            raise SystemExit(
                f"no test module matches {unmatched}. Known modules:\n  "
                + "\n  ".join(MODULES))
    if skip:
        chosen = [m for m in chosen if not any(pat in m for pat in skip)]
    if not chosen:
        raise SystemExit("the selection is empty; nothing to run.")
    return chosen


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-k", "--only", action="append", metavar="PATTERN",
                    help="run only modules whose name contains PATTERN "
                         "(repeatable). A SUBSET IS NOT A SUITE RUN.")
    ap.add_argument("-x", "--skip", action="append", metavar="PATTERN",
                    help="skip modules whose name contains PATTERN")
    ap.add_argument("--list", action="store_true",
                    help="print the module list and exit")
    ap.add_argument("-j", "--jobs", type=int, default=0, metavar="N",
                    help="run modules in N parallel PROCESSES (0 = auto, "
                         "1 = serial). Modules in SERIAL_ONLY always run "
                         "alone, after the rest.")
    ap.add_argument("--slowest", type=int, default=8, metavar="N",
                    help="how many modules to name in the timing summary")
    args = ap.parse_args(argv)

    if args.list:
        for m in MODULES:
            print(m)
        return 0

    chosen = select(args.only, args.skip)
    partial = len(chosen) != len(MODULES)

    workers = args.jobs or max(1, min(8, (os.cpu_count() or 2) - 1))
    parallel = [m for m in chosen if m not in SERIAL_ONLY]
    parallel.sort(key=lambda m: (LONGEST_FIRST.index(m)
                                 if m in LONGEST_FIRST else len(LONGEST_FIRST)))
    serial = [m for m in chosen if m in SERIAL_ONLY]

    failed = 0
    times: list[tuple[float, str]] = []
    started = time.monotonic()

    # PARALLEL FIRST, SERIAL AFTER. Output is buffered per module and printed
    # in the declared order, so a parallel run reads exactly like a serial one
    # — interleaved output would make a failure impossible to attribute, which
    # would cost more than the wall clock saves.
    if workers > 1 and len(parallel) > 1:
        print(f"running {len(parallel)} modules across {workers} processes"
              + (f", then {len(serial)} serially" if serial else ""))
        with ProcessPoolExecutor(max_workers=workers) as pool:
            for name, f, out, secs in pool.map(_run_one, parallel):
                print(f"\n=== {name} " + "=" * (60 - len(name)))
                print(out, end="")
                failed |= f
                times.append((secs, name))
    else:
        serial = chosen

    for name in serial:
        print(f"\n=== {name} " + "=" * (60 - len(name)))
        t0 = time.monotonic()
        module = importlib.import_module(name)
        failed |= run_module(vars(module))
        times.append((time.monotonic() - t0, name))

    total = time.monotonic() - started
    # WHERE THE TIME GOES, every run, because a forty-minute suite that does not
    # say which module owns the forty minutes cannot be made faster on evidence.
    # THE SHARE IS OF MODULE TIME, NOT OF WALL CLOCK. In parallel mode those
    # differ and the naive version printed percentages summing past 100%, which
    # is exactly the kind of statistic that gets quoted. Both numbers are shown
    # because they answer different questions: the share says what to optimise
    # NEXT, and the wall clock says what the run cost.
    spent = sum(sec for sec, _ in times) or 1.0
    print(f"\n=== timing " + "=" * 51)
    for seconds, name in sorted(times, reverse=True)[:args.slowest]:
        print(f"  {seconds:7.1f}s  {seconds / spent:5.1%}  {name}")
    print(f"  {spent:7.1f}s   100.0%  module time ({len(chosen)} modules)")
    if abs(spent - total) > 1.0:
        print(f"  {total:7.1f}s          WALL CLOCK "
              f"({spent / total:.2f}x from running in parallel)")

    print(f"\nrepository root: {ROOT}")
    if partial:
        print(f"\n*** PARTIAL RUN: {len(chosen)} of {len(MODULES)} modules. "
              f"This is NOT a suite run and must not be reported as one. ***")
    return failed


if __name__ == "__main__":
    # Shared lock, same reason as `src/compare_history.py`: much of this suite
    # reads the emitted pool specs, and a suite that runs while they are being
    # rewritten reports failures that are an artefact of the race rather than of
    # the code. See pools.artefact_lock.
    sys.path.insert(0, str(ROOT / "src"))
    # Before the lock, because it may replace the process. A fixed hash seed is
    # what makes a golden recorded on one run comparable to the next bit for
    # bit; see `montecarlo.fix_hash_seed` and MODEL-LOG §1.104.
    import montecarlo as _M
    _M.fix_hash_seed()
    import pools as _pools
    with _pools.artefact_lock("read", "test suite"):
        raise SystemExit(main())
