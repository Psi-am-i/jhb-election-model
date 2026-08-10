"""Shared bootstrap for the test suite.

There is no test runner installed in ``.venv`` (``python -m pytest`` reports
"No module named pytest"), so every test file here is written to run **both**
ways:

    ./.venv/bin/python -m pytest tests/ -q      # once pytest is installed
    ./.venv/bin/python tests/test_seats.py      # today, with no dependencies

That is what this module exists for. It puts ``src/`` on the path, pins the
working directory to the repository root (the pipeline modules address data
with relative paths such as ``data/raw/elections``), and supplies a ``skip``
that maps onto ``pytest.skip`` when pytest is present and onto a local
exception when it is not.

The standalone runner in :func:`run_module` collects every ``test_*`` callable
in a module's namespace, which is the same rule pytest applies -- so the two
runners see the same tests, including the ones generated per city-year in
``test_seats.py``.
"""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# The pipeline modules read `data/...` relative to the process's cwd, so the
# tests must run from the repository root whichever runner invoked them.
os.chdir(ROOT)


class SkipTest(Exception):
    """Raised by :func:`skip` when pytest is not available."""


try:  # pragma: no cover - depends on the environment, not on the code
    import pytest as _pytest
except ImportError:  # pragma: no cover
    _pytest = None


def _skip_exceptions() -> tuple[type[BaseException], ...]:
    """Every exception type :func:`skip` can raise, for the runner to catch.

    ``pytest.skip`` raises ``_pytest.outcomes.Skipped``, which derives from
    ``BaseException``, NOT from ``Exception`` -- deliberately, so that a test's
    own ``except Exception`` cannot swallow a skip. The standalone runner below
    must therefore catch it by name. If it did not, the day pytest lands in
    ``.venv`` every skip would abort ``run_all.py`` on the spot instead of
    being reported, and most of this suite skips when its input files are
    absent.
    """
    types: tuple[type[BaseException], ...] = (SkipTest,)
    if _pytest is None:
        return types
    skipped = getattr(_pytest.skip, "Exception", None)
    if skipped is None:  # pragma: no cover - very old/very new pytest
        try:
            from _pytest.outcomes import Skipped as skipped  # type: ignore
        except ImportError:
            skipped = None
    if isinstance(skipped, type) and issubclass(skipped, BaseException):
        types += (skipped,)
    return types


SKIP_EXCEPTIONS = _skip_exceptions()


def skip(reason: str):
    """Skip the current test, explicitly and with a reason.

    A test that cannot be written honestly -- because the data it would check
    against is not on disk -- must say so rather than quietly weaken what it
    asserts.
    """
    if _pytest is not None:
        _pytest.skip(reason)
    raise SkipTest(reason)


def run_module(namespace: dict) -> int:
    """Run every ``test_*`` callable in ``namespace``. Returns an exit code."""
    names = sorted(
        name for name, value in namespace.items()
        if name.startswith("test_") and callable(value)
    )
    passed = failed = skipped = 0
    failures: list[str] = []
    for name in names:
        try:
            namespace[name]()
        except SKIP_EXCEPTIONS as exc:
            skipped += 1
            print(f"SKIP {name}: {exc}")
        except Exception:  # noqa: BLE001 - a test runner reports everything
            failed += 1
            failures.append(f"FAIL {name}\n{traceback.format_exc()}")
            print(f"FAIL {name}")
        else:
            passed += 1
            print(f"ok   {name}")
    for text in failures:
        print()
        print(text)
    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0
