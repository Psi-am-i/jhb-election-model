"""Run the excessive-seats counterfactuals for the regime-comparison table.

Three answers to the same arithmetic (a party winning more wards than its
proportional share):

* ``deduct`` — South African law as amended (Act 3/2021): council fixed at
  270, the winner keeps its wards, everyone else is squeezed. This is the
  published reference run.
* ``expand`` — the old-Germany answer (pre-2013 Überhangmandate) and this
  project's pre-research reading: the council grows by the excess.
* ``level`` — the modern-Germany answer (Ausgleichsmandate): the council
  grows until every ward winner is covered proportionally; nobody pays.
* ``cap`` — the Germany-2023 answer: pure proportionality at a fixed 270;
  a ward winner beyond its party's entitlement is simply not seated.

Each counterfactual is a full run at the published seed, so the table on the
forecast sheet compares the SAME 5,000 simulated elections under different
law. Outputs land as data/processed/regime_{rule}_summary.json and
regime_{rule}_seat_draws.csv.

Usage:
    python src/overhang_regimes.py          # then: python src/render_sheet.py

⛔ THIS SCRIPT WRITES COUNTERFACTUALS THROUGH THE PUBLISHED FORECAST'S OWN
FILES, AND THAT IS WHY EVERYTHING BELOW EXISTS.
=============================================================================
``montecarlo.main`` writes ``forecast_summary.json``, ``seat_draws.csv``,
``ward_winner_probs.csv`` and the coalition tables into ``data/processed``, and
those files ARE the site's inputs. There is no ``--counterfactual`` equivalent
of the ``--run-dir`` guard (montecarlo.py:5229) that stops a diagnostic run
publishing — so a run under a law that does not exist lands on the published
paths, and the only thing that put the real forecast back was a bare statement
at the END of the function:

    for rule in ("expand", "level", "cap"):
        montecarlo.main(["--counterfactual", "--set", f"overhang_rule={rule}"])
        ...
    montecarlo.main([])        # <- the restore. No try. No finally.

**Any exception in that loop skipped it**, and the exception was not
hypothetical: ``allocate_with_overhang`` raises ``RuntimeError`` for the
``level`` rule BY DESIGN (montecarlo.py:3234 — *"the `level` rule grew the
council … and the allocation then failed"*), and ``level`` is the SECOND of the
three. A ``level`` failure, or a Ctrl-C, left ``forecast_summary.json`` holding
the ``expand`` council — grown past 270, with a moved majority threshold —
under the name the site reads. Nothing downstream catches that:
``stats.freshness_problems`` compares mtimes and nothing asserts the published
``scenario.overhang_rule == "deduct"``. ``data/**`` is gitignored, so nothing
warns and nothing restores it. The ``--counterfactual`` guard's own error text
says these runs *"must not reach a forecast"*; this script wrote them to the
forecast's own paths and relied on reaching line 53 to undo it.

So: the published tree is SNAPSHOT before the first counterfactual and restored
BYTE FOR BYTE in a ``finally``. Two properties that a restore-by-re-running
never had —

* it cannot itself fail (it is a file copy, not a Monte Carlo), and
* it is *exactly* the bytes that were published, not a re-derivation of them.

⚠️ AND THE DOCSTRING USED TO CLAIM THE RE-RUN WAS "deterministic seed —
bit-identical". IT WAS NOT.
=============================================================================
``montecarlo.fix_hash_seed`` is called only under ``montecarlo``'s own
``if __name__ == "__main__"`` (montecarlo.py:5301). This script imports
``montecarlo`` and calls ``main()`` as a LIBRARY, and every other library-style
entry point in ``src/`` pins the hash seed for exactly that reason —
``compare_history.py``, ``backtest.py``, ``sweep.py``, ``diagnose.py`` and
``freeze.py`` all call it. This one did not, so all four runs executed under a
RANDOM ``PYTHONHASHSEED`` while the published reference was produced under 0.

That compounds with a defect measured on 2026-09-14: ``seats.allocate``'s
largest-remainder key is not a total order, so under a random hash seed a tied
last seat is a coin flip. The "restore" could therefore write a
``forecast_summary.json`` differing from the published one by a whole seat, and
call it bit-identical. ``fix_hash_seed()`` is now the first statement under
this file's ``__main__`` guard.

The reference re-run is kept — the table's claim is that all four runs are the
same 5,000 elections under different law, which needs the reference produced by
the same code as the counterfactuals — but it is no longer what makes the tree
safe, and whether it reproduced the published bytes is now MEASURED and printed
rather than asserted in a docstring.

⚠️ WHAT WAS CONSIDERED AND REJECTED: ``montecarlo --processed <tmpdir>``, which
looks like it would isolate the counterfactuals and remove the need for any of
this. **It is one flag for two jobs**: ``--processed`` is where inputs are READ
as well as where outputs are written (montecarlo.py:5052). Checked read by read:

* ``turnout.csv`` — ``SystemExit`` if absent (montecarlo.py:4257). Loud.
* the ward crosswalk — refuses, naming the file (montecarlo.py:901).
* ``gamma_recent.csv`` (montecarlo.py:4208), ``byelection_contest_detail.csv``
  (:4141) and ``byelection_party_deltas.csv`` (:4446) — **all three are
  ``if path.exists()`` and fall back in silence.**

So an empty directory does not isolate the run: it stops it on the first two
and, once those are satisfied, hands back a model with the by-election evidence
and the recent-gamma channel switched off, with nothing said. A counterfactual
scored against a reference that quietly lost E4 is a worse answer than the one
this script exists to give. Copying "the inputs" across first would mean typing
a list of them, which is the failure mode this repository names every time it
appears — and that list would have had to be right on the day `--processed`
gained its sixth reader.
"""

from __future__ import annotations

import filecmp
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

import montecarlo

PROCESSED = Path("data/processed")

RULES = ("expand", "level", "cap")

# Runtime state is not an artefact, and restoring it would be actively wrong:
# `.pools.lock` is the flock `pools.artefact_lock` holds, and its content is a
# live pid. `archive.py`'s scan excludes it for the same reason.
_NOT_ARTEFACTS = {".pools.lock", ".DS_Store"}


def _files(root: Path) -> dict[str, Path]:
    """Every regular file under `root`, keyed by its path relative to it."""
    return {str(p.relative_to(root)): p
            for p in sorted(root.rglob("*"))
            if p.is_file() and p.name not in _NOT_ARTEFACTS}


def _restore(snapshot: Path, live: Path) -> tuple[list[str], list[str]]:
    """Put the published bytes back. Returns (restored, appeared).

    ⛔ IT DOES NOT DELETE. A file present now and absent from the snapshot is
    reported, never removed: this script is not the only writer that can touch
    `data/processed`, and a restore that deletes what it does not recognise
    would turn one agent's safety net into another agent's data loss. Naming
    them is the honest half of the job — the half a silent restore skips.
    """
    restored: list[str] = []
    before = _files(snapshot)
    now = _files(live)
    for rel, src in before.items():
        dst = live / rel
        if dst.exists() and filecmp.cmp(src, dst, shallow=False):
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)          # copy2: the published mtime too
        restored.append(rel)
    appeared = sorted(set(now) - set(before))
    return sorted(restored), appeared


def main() -> int:
    if not PROCESSED.is_dir():
        print(f"no processed tree at {PROCESSED.resolve()} — run from the "
              f"repository root (this script's paths are cwd-relative, like "
              f"montecarlo's own)")
        return 1

    with tempfile.TemporaryDirectory(prefix="overhang_regimes_") as tmp:
        snapshot = Path(tmp) / "published"
        staged = Path(tmp) / "staged"
        staged.mkdir(parents=True)
        # THE SNAPSHOT IS TAKEN BEFORE ANYTHING RUNS. ~9 MB today; the cost of
        # not taking it is a counterfactual council on the live front page.
        shutil.copytree(PROCESSED, snapshot,
                        ignore=shutil.ignore_patterns(*_NOT_ARTEFACTS))
        print(f"snapshot: {len(_files(snapshot))} published file(s) held in "
              f"{snapshot}")

        settled = False
        try:
            for rule in RULES:
                print(f"\n=== overhang_rule={rule} ===")
                # `--counterfactual` is required since 2026-09-02:
                # `overhang_rule` is statute and `--set` refuses to change it
                # without the word being said. This script is the one
                # legitimate caller. MODEL-LOG §1.165.
                montecarlo.main(["--counterfactual",
                                 "--set", f"overhang_rule={rule}"])
                # STAGED, not published. The regime artefacts only become
                # visible once every run has succeeded, so an interrupted
                # sweep leaves neither a counterfactual forecast nor a set of
                # regime files half from this run and half from the last one.
                shutil.copy2(PROCESSED / "forecast_summary.json",
                             staged / f"regime_{rule}_summary.json")
                shutil.copy2(PROCESSED / "seat_draws.csv",
                             staged / f"regime_{rule}_seat_draws.csv")

            # THE REFERENCE, RE-RUN. Not for safety — the `finally` below is
            # what makes the tree safe — but because the table's claim is that
            # all four runs are the same simulated elections under different
            # law, which requires the reference to come from the same code as
            # the counterfactuals.
            print("\n=== re-running the reference (default rule) ===")
            montecarlo.main([])
            settled = True
        finally:
            if not settled:
                restored, appeared = _restore(snapshot, PROCESSED)
                print(f"\n⛔ A RUN DID NOT COMPLETE. The published artefacts "
                      f"have been restored byte for byte from the snapshot "
                      f"taken before the first counterfactual: "
                      f"{len(restored)} file(s) put back"
                      + (f" — {', '.join(restored)}" if restored else
                         " (none had been written yet)") + ".")
                if appeared:
                    print(f"  ⚠️ {len(appeared)} file(s) exist now that did "
                          f"not exist before and were NOT removed: "
                          f"{', '.join(appeared)}. Check them by hand.")
                print("  No regime artefact was published. Re-run when the "
                      "cause is fixed.")

        # ------------------------------------------------------------------
        # Everything succeeded. Publish the staged regime artefacts, and
        # MEASURE the claim the docstring used to assert.
        # ------------------------------------------------------------------
        for src in sorted(staged.iterdir()):
            shutil.copy2(src, PROCESSED / src.name)

        # RE-DATE THE COUNTERFACTUALS TO THIS RUN. The staged copies were taken
        # BEFORE the reference was re-run, so on a perfectly correct run every
        # regime_<rule>_summary.json is older than forecast_summary.json by one
        # Monte Carlo — and `stats.freshness_problems`, which refuses to
        # publish a token whose source file lags the reference, would fire on a
        # freshly built pipeline every time. A check that cries wolf on day one
        # is a check somebody switches off. These six files come out of the
        # same invocation as the reference and are stamped to say so.
        now = time.time()
        for rule in RULES:
            for name in (f"regime_{rule}_summary.json",
                         f"regime_{rule}_seat_draws.csv"):
                os.utime(PROCESSED / name, (now, now))
        print(f"  published and re-dated {2 * len(RULES)} regime artefacts")

        # ⚠️ THE REPRODUCIBILITY CLAIM, MEASURED RATHER THAN ASSERTED.
        # The old docstring said the restore was "deterministic seed —
        # bit-identical" and nothing checked it. It is checkable in one line,
        # and a difference here is a real finding: with the hash seed now
        # pinned, the reference run is deterministic, so a mismatch means the
        # bytes on disk were NOT produced by this code at this seed — a stale
        # published forecast, or one drawn before `fix_hash_seed` reached this
        # path and therefore holding a coin-flipped tie.
        moved = [rel for rel, src in _files(snapshot).items()
                 if rel.startswith(("forecast_summary", "seat_draws",
                                    "ward_winner_probs", "coalition_"))
                 and (PROCESSED / rel).exists()
                 and not filecmp.cmp(src, PROCESSED / rel, shallow=False)]
        if moved:
            print(f"\n⚠️ the reference re-run did NOT reproduce the bytes that "
                  f"were on disk: {len(moved)} file(s) changed — "
                  f"{', '.join(moved)}.\n"
                  f"  This is not an error in this script. It means the "
                  f"published artefacts predate the current code (or the "
                  f"current hash seed). The tree now holds the reference this "
                  f"comparison table is actually against; if that was not "
                  f"intended, restore from git-tracked sources or re-publish "
                  f"deliberately.")
        else:
            print("\n  the reference re-run reproduced the published bytes "
                  "exactly")
    return 0


if __name__ == "__main__":
    # FIRST, because it may replace the process. Every library-style caller of
    # `montecarlo.main` in `src/` does this — compare_history, backtest, sweep,
    # diagnose, freeze — and this one did not, so four runs of the published
    # forecast's own files executed under a random PYTHONHASHSEED. See the
    # module docstring and `montecarlo.fix_hash_seed`.
    montecarlo.fix_hash_seed()
    sys.exit(main())
