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
import importlib
import sys
import time
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
           "test_pool_conservation", "test_pool_bounds", "test_regressions",
           "test_calibration_report", "test_ipf_feasibility",
           "test_levels_dispersion", "test_polling_sd",
           "test_polling_synthetic", "test_polling_register",
           "test_register_matches_code", "test_data_coverage",
           "test_freeze",
           "test_spine", "test_theta_prior", "test_ward_pr_ratios",
           "test_ward_parts", "test_solve_and_predict",
           "test_blended_centres",
           "test_levers_are_live", "test_build_all", "test_stat_freshness",
           "test_hex_cartogram"]


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
    ap.add_argument("--slowest", type=int, default=8, metavar="N",
                    help="how many modules to name in the timing summary")
    args = ap.parse_args(argv)

    if args.list:
        for m in MODULES:
            print(m)
        return 0

    chosen = select(args.only, args.skip)
    partial = len(chosen) != len(MODULES)

    failed = 0
    times: list[tuple[float, str]] = []
    started = time.monotonic()
    for name in chosen:
        print(f"\n=== {name} " + "=" * (60 - len(name)))
        t0 = time.monotonic()
        module = importlib.import_module(name)
        failed |= run_module(vars(module))
        times.append((time.monotonic() - t0, name))

    total = time.monotonic() - started
    # WHERE THE TIME GOES, every run, because a forty-minute suite that does not
    # say which module owns the forty minutes cannot be made faster on evidence.
    print(f"\n=== timing " + "=" * 51)
    for seconds, name in sorted(times, reverse=True)[:args.slowest]:
        print(f"  {seconds:7.1f}s  {seconds / total:5.1%}  {name}")
    print(f"  {total:7.1f}s   100.0%  TOTAL ({len(chosen)} modules)")

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
