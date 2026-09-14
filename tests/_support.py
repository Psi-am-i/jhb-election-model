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


def run_module(namespace) -> int:
    """Run every ``test_*`` callable in ``namespace``. Returns an exit code.

    **Takes a module OR its namespace dict, because four files passed the
    wrong one for weeks and nothing noticed** (MODEL-LOG §1.75).
    `run_all.py` calls `run_module(vars(module))`; `test_levels_dispersion`,
    `test_polling_sd`, `test_polling_synthetic` and `test_polling_register` all
    end with `run_module(sys.modules[__name__])`. Under the suite they ran fine
    — the suite supplies the dict — and standalone every one of them died on
    `AttributeError: module '__main__' has no attribute 'items'` before a single
    test executed. CLAUDE.md documents running these files directly, so the
    documented invocation was the broken one, and the suite hid it.
    """
    if not isinstance(namespace, dict):
        namespace = vars(namespace)
    names = sorted(
        name for name, value in namespace.items()
        if name.startswith("test_") and callable(value)
    )
    passed = failed = skipped = 0
    failures: list[str] = []

    # ⛔ THE ACTIVE CITY IS PROCESS-GLOBAL, AND `run_all` REUSES WORKERS.
    #
    # `cityconfig.use(slug)` sets module-level `_ACTIVE`/`_TARGET`. ELEVEN test
    # modules call it and most never put it back, and `ProcessPoolExecutor`
    # gives one worker several modules in sequence — so a module that switches
    # city silently re-points every module scheduled after it in that worker.
    #
    # Measured: `polling.screen` on the 2026 target admits 2 polls with joburg
    # active and **0** with capetown active, because the metro filter reads the
    # active city. `test_polling_register` asserts "no polls admitted at 2026 —
    # the register or the rules moved", which is exactly the right message for
    # the wrong cause, and it made a real defect look like a poll-register
    # change. The failure is ORDER-DEPENDENT, so it appears and disappears as
    # modules are added.
    #
    # Restored PER TEST, here, rather than in each of the eleven: one
    # definition, and a module added tomorrow inherits it. Same family as
    # JUDGEMENT-CALLS §A43 (`apply_city` never resets `DEFAULTS`), which is on
    # the register in red for the same reason.
    try:
        import cityconfig as _cc
        _city0 = _cc.active().slug
    except Exception:
        _cc = _city0 = None

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
        finally:
            # Put the active city back after EVERY test, pass or fail. A test
            # that fails mid-way is exactly the one most likely to have left
            # the global switched.
            if _cc is not None and _city0 is not None:
                try:
                    if _cc.active().slug != _city0:
                        _cc.use(_city0)
                except Exception:
                    pass
    for text in failures:
        print()
        print(text)
    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


def declared_city_years() -> set:
    """The backtest city-years this repository is supposed to cover, COMPUTED.

    Every ``[structure.by_year.<year>]`` block in ``cities/*.toml`` is a target
    a city can be run at, and the emit loop, the panel and the backtest all
    iterate that same product. It is offered here rather than in one test file
    because two of them need it and **a denominator defined twice is a
    denominator that disagrees with itself.**

    ⛔ **NEVER TYPE THIS COUNT.** ``POOLS-REEMIT-QUEUE.md`` step 3 carried it as
    a number, the number went stale, and it sent an operator hunting a
    discrepancy that did not exist — which is the failure that paragraph had
    been written to warn about. That document now refuses to name a figure in
    either direction and says to count against what the loop issues. This is
    that count, taken from the configs the loop iterates and not from the
    artefacts it wrote, so it cannot be satisfied by the very output under test.
    """
    import tomllib

    import cityconfig  # noqa: E402 - SRC is on the path from this module's top

    out = set()
    for toml_path in sorted(cityconfig.CITIES_DIR.glob("*.toml")):
        raw = tomllib.loads(toml_path.read_text())
        for year in ((raw.get("structure") or {}).get("by_year") or {}):
            out.add((toml_path.stem, str(year)))
    assert out, (
        f"no [structure.by_year] blocks in any of "
        f"{sorted(p.name for p in cityconfig.CITIES_DIR.glob('*.toml'))}. "
        f"Every caller uses this as a denominator, and a denominator of zero "
        f"turns a scan into a vacuous pass.")
    return out


def scanned(population, *, of, low, high, what, denominator):
    """Assert a scan LOOKED: population non-empty and inside a two-sided band.

    Written for the class CLAUDE.md calls "a test that asserts ABSENCE". Such a
    test collects offenders from live repository state and asserts the
    collection is empty; it passes identically when the scan found nothing
    because there is nothing wrong and when the scan found nothing because it
    scanned nothing. This is the second of that section's four requirements.

    Both bounds are FRACTIONS of a denominator the caller computes from the
    tree — the number of ``.py`` files in ``src/``, the number of rows in a
    register, the number of test modules — so neither goes stale when the tree
    grows. A bare integer floor is deliberately not offered: **when a bare
    floor trips, the cheapest repair is to lower it**, which converts a guard
    into a record of decline. A ratio against a denominator that moves with the
    tree has no such cheap repair.

    The UPPER bound matters as much as the lower one and is the half people
    leave out. A scan that suddenly sees three times what it used to has
    usually broken its own filter — the register guard's underscore filter, the
    dead-code guard's substring count — and a one-sided floor calls that a
    success.

    Args:
      population: what the scan actually examined (sized, or an int).
      of:          the denominator, likewise.
      low, high:   fractions of ``of``; the band is inclusive at both ends.
      what:        what the population IS, for the failure message.
      denominator: what the denominator IS, for the failure message.
    """
    n = population if isinstance(population, int) else len(population)
    d = of if isinstance(of, int) else len(of)
    assert d > 0, (
        f"the denominator ({denominator}) is zero, so the bound on {what} "
        f"means nothing. The scan has lost its input, not passed.")
    lo, hi = low * d, high * d
    assert lo <= n <= hi, (
        f"{what}: the scan examined {n}, and {denominator} is {d}, so the "
        f"expected band is {lo:.1f}..{hi:.1f} ({low:.3g}..{high:.3g} of the "
        f"denominator).\n"
        f"BELOW the band the scan has stopped seeing its population and the "
        f"emptiness it asserts is vacuous. ABOVE it the filter has broken open "
        f"and the population is no longer the one the claim is about. Fix the "
        f"scan; move the band only with a reason written beside it.")
    return n
