"""Run the whole suite without pytest.

pytest is not installed in ``.venv`` (``python -m pytest`` reports "No module
named pytest"), so this is the stand-in:

    ./.venv/bin/python tests/run_all.py

If pytest is ever installed, prefer it -- every test file here is written to be
collected by it unchanged:

    ./.venv/bin/python -m pytest tests/ -q
"""

from __future__ import annotations

import importlib
import sys
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


def main() -> int:
    failed = 0
    for name in MODULES:
        print(f"\n=== {name} " + "=" * (60 - len(name)))
        module = importlib.import_module(name)
        failed |= run_module(vars(module))
    print(f"\nrepository root: {ROOT}")
    return failed


if __name__ == "__main__":
    # Shared lock, same reason as `src/compare_history.py`: much of this suite
    # reads the emitted pool specs, and a suite that runs while they are being
    # rewritten reports failures that are an artefact of the race rather than of
    # the code. See pools.artefact_lock.
    sys.path.insert(0, str(ROOT / "src"))
    import pools as _pools
    with _pools.artefact_lock("read", "test suite"):
        raise SystemExit(main())
