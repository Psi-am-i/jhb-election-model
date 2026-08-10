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

MODULES = ["test_seats", "test_drawer", "test_temporal"]


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
