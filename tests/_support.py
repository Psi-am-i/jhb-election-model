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

import builtins
import os
import re
import sys
import traceback
from contextlib import contextmanager
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


_ELECTION_FILE = re.compile(r"\b(npe|lge)(\d{4})", re.IGNORECASE)


@contextmanager
def election_files_read():
    """Record every election result file opened inside the block.

    A temporal-validity test has one hard problem: it is trying to prove a
    negative, and the obvious way to write it is to re-state the production
    loop's own guard ("every LGE in the calendar before the target is earlier
    than the target") — which is true of the calendar no matter what the code
    reads, and passes with the guard deleted. That is how
    ``test_the_level_prior_reads_no_election_at_or_after_its_target`` came to
    assert nothing at all about the level prior.

    So watch the reads instead. Every result file this repository consumes is
    named for its election (``npe2019_JHB_vd_party.csv``,
    ``lge2021_JHB_vd_party_clean.csv``), so a leak is visible in the filename:
    if a fit for target 2016 opens ``lge2021_...``, it has read the future,
    whatever the loop believed. This catches the defect rather than the
    guard — including leaks through helpers nobody thought to check.

    Yields a list of ``(year, kind, path)``, filled as the block runs.

    It sees ``open``, ``Path.open`` and ``pandas.read_csv``, which is every
    route ``src/`` currently uses. A module that reads by some other means is
    invisible to it, so a test using this must also assert that the files it
    DID expect were seen — "no late file" is only evidence when something was
    read at all.
    """
    seen: list[tuple[str, str, str]] = []
    real_open, real_path_open = builtins.open, Path.open
    try:
        import pandas as _pd
        real_read_csv = _pd.read_csv
    except ImportError:  # pragma: no cover - pandas is a hard dep of src/
        _pd = real_read_csv = None

    def note(target):
        match = _ELECTION_FILE.search(str(target))
        if match:
            seen.append((match.group(2), match.group(1).upper(), str(target)))

    def spy_open(file, *args, **kwargs):
        note(file)
        return real_open(file, *args, **kwargs)

    def spy_path_open(self, *args, **kwargs):
        note(self)
        return real_path_open(self, *args, **kwargs)

    def spy_read_csv(filepath_or_buffer, *args, **kwargs):
        note(filepath_or_buffer)
        return real_read_csv(filepath_or_buffer, *args, **kwargs)

    builtins.open = spy_open
    Path.open = spy_path_open
    if _pd is not None:
        _pd.read_csv = spy_read_csv
    try:
        yield seen
    finally:
        builtins.open = real_open
        Path.open = real_path_open
        if _pd is not None:
            _pd.read_csv = real_read_csv


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
        except SystemExit:
            # SystemExit is a BaseException, so `except Exception` misses it —
            # and every module in src/ raises SystemExit for a missing input
            # (grep: 9 in montecarlo.py, 12 in pools.py). Without this the
            # first missing file killed the whole run mid-file: four tests
            # never executed, no summary printed, and exit 1 looked like an
            # ordinary failure. A missing input is one failing test, not a
            # truncated suite that reports nothing.
            failed += 1
            failures.append(f"FAIL {name}\n{traceback.format_exc()}")
            print(f"FAIL {name} (SystemExit)")
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
