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
MODULES = ["test_seats", "test_drawer", "test_temporal", "test_chain",
           "test_pool_conservation", "test_pool_bounds", "test_regressions",
           "test_calibration_report", "test_ipf_feasibility",
           "test_levels_dispersion", "test_polling_sd",
           "test_polling_synthetic", "test_polling_register",
           "test_register_matches_code", "test_data_coverage",
           "test_freeze",
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
    raise SystemExit(main())
