"""A diagnostic run must never touch the published forecast's inputs.

On 2026-08-10 a `fold.py` run with a non-default option wrote its results over
``data/processed/fold1_parameters.csv`` -- the file the live forecast reads γ
from -- and moved 55 of the published forecast's 555 values. Nobody noticed for
hours, because the repository had no tests. Separately, `turnout.py --city
tshwane` used to write Johannesburg's ``data/processed/turnout.csv``, which
``montecarlo.py`` then read.

Both are the same class of bug: a *variant* run claiming the *canonical*
output. These tests encode the invariant directly.

    fold.py with any non-default option  -> fold1_parameters.csv unchanged
    turnout.py --city tshwane            -> data/processed/turnout.csv unchanged

They go further than the two named files: they assert that a variant run
changes **nothing else** under ``data/processed`` either, apart from the one
output that run is entitled to write. A test that only watched the file that
broke last time would miss the next one.

Each test also insists the command actually SUCCEEDED and actually wrote its
own output. An invariant test that passes because the process crashed before
writing anything is worse than no test at all.

What this file does and does not touch
--------------------------------------
It runs real pipeline commands against the real ``data/processed``. There is no
way to test "does this command write the canonical file" without letting it
try. So the safety rule here is narrow and absolute:

* **Guarded.** Exactly the two canonical files named above are copied to a
  backup before the run, and are the *only* things ever written back. The
  backup lives outside the repository, the restore runs in a ``finally``, and
  the backup is deleted only once every guarded file has been verified byte-
  for-byte and mtime-for-mtime back where it started. If a restore cannot be
  completed -- a permissions error, a full disk, a run killed mid-write -- the
  backup directory is **kept** and its path is printed and asserted on, so
  there is always a copy to recover from. ``data/**`` is gitignored; a lost
  file here is lost for good, so "compare against your last commit" is not a
  recovery plan and is not offered as one.
* **Observed, never touched.** Everything else under ``data/processed`` is read
  (mtimes only, before and after) purely to decide what the run wrote. Files
  the command legitimately produces -- ``fold1_parameters__turnout-ratio.csv``,
  ``tshwane/turnout.csv`` -- are left exactly as the command left them. An
  earlier version of this file restored the whole tree, which meant a test run
  deleted files and reverted writes belonging to any *other* process that
  happened to be building at the same time. That is not a test being cautious;
  that is the very bug this file exists to catch, committed by the test.

One consequence of observing rather than owning the tree: if another pipeline
build is running in this working tree, its writes are indistinguishable from
the writes of the run under test, and the "wrote nothing else" assertions can
fail spuriously. That is a false failure with no data loss. Re-run alone.

This file never runs ``montecarlo.py``, which overwrites the published outputs.

Run:
    ./.venv/bin/python tests/test_temporal.py
    ./.venv/bin/python -m pytest tests/test_temporal.py -q
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, skip  # noqa: E402

PROCESSED = ROOT / "data" / "processed"
CANONICAL_FOLD = PROCESSED / "fold1_parameters.csv"
CANONICAL_TURNOUT = PROCESSED / "turnout.csv"

#: The only files this module will ever write. Adding one here means backing it
#: up and restoring it; anything not in this tuple is observed and left alone.
GUARDED = (CANONICAL_FOLD, CANONICAL_TURNOUT)

TIMEOUT = 300


# --------------------------------------------------------------------------
# observing the tree (read-only) and guarding the canonical files
# --------------------------------------------------------------------------

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def state(path: Path) -> tuple[str | None, int | None]:
    """(sha256, mtime_ns) for one file, or (None, None) if it is not there.

    Content answers "did the file's meaning change"; mtime answers "was it
    written at all". Both matter: a variant run that rewrites the canonical
    parameters with today's identical bytes is still a variant run claiming the
    canonical output, and it will produce *different* bytes the next time the
    input data moves.
    """
    try:
        return digest(path), path.stat().st_mtime_ns
    except OSError:
        return None, None


def tree_mtimes(root: Path) -> dict[str, int]:
    """Modification time of every file under ``root``, in ns, keyed relatively.

    Read-only, and deliberately tolerant: a file that disappears between the
    ``rglob`` and the ``stat`` belongs to somebody else's build, and is not
    this test's business.
    """
    out: dict[str, int] = {}
    for path in root.rglob("*"):
        try:
            if path.is_file():
                out[str(path.relative_to(root))] = path.stat().st_mtime_ns
        except OSError:
            continue
    return out


class Guard:
    """Back up a fixed set of files; restore only those, only if they moved.

    Nothing outside ``paths`` is ever written. The backup directory outlives
    the restore if the restore did not fully succeed, and :attr:`error` then
    carries a message naming it -- the tests assert on that before anything
    else, so a failed restore is reported as a failure with a recovery path
    rather than as a mysterious downstream mismatch.
    """

    def __init__(self, paths: tuple[Path, ...]):
        self.dir = Path(tempfile.mkdtemp(prefix="jhb-canonical-guard-"))
        self.error: str | None = None
        self.backups: dict[Path, Path] = {}
        self.before: dict[Path, tuple[str | None, int | None]] = {
            path: (None, None) for path in paths
        }
        for path in paths:
            if not path.exists():
                continue  # nothing on disk to protect; the tests skip on this
            try:
                # ValueError here means someone added a GUARDED path from
                # outside data/processed; that is a mistake, not a backup this
                # module knows how to take.
                backup = self.dir / path.relative_to(PROCESSED)
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, backup)
                recorded = state(path)
                if recorded == (None, None) or state(backup) != recorded:
                    raise OSError("backup does not match the original")
            except (OSError, ValueError) as exc:
                # Refuse to run at all rather than run unguarded: the command
                # under test is one whose whole point is that it MIGHT write
                # this file.
                self.error = (
                    f"could not back up {path} ({exc}), so the pipeline "
                    f"command was not run. Fix the backup before testing: "
                    f"this module will not run a command that may overwrite a "
                    f"canonical file it cannot restore.")
                shutil.rmtree(self.dir, ignore_errors=True)
                self.backups.clear()
                return
            self.backups[path] = backup
            self.before[path] = recorded

    def restore(self) -> None:
        """Put back every guarded file that moved. Never raises."""
        if not self.backups:
            shutil.rmtree(self.dir, ignore_errors=True)
            return
        problems: list[str] = []
        for path, backup in self.backups.items():
            want = self.before[path]
            try:
                if state(path) != want:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    # copy2 carries the mtime back too, so a run that rewrote
                    # the file with identical bytes does not get to leave its
                    # timestamp behind.
                    shutil.copy2(backup, path)
                if state(path) != want:
                    problems.append(f"{path} still does not match the backup")
            except OSError as exc:
                problems.append(f"{path}: {exc}")
        if problems:
            self.error = (
                "FAILED TO RESTORE a canonical file after the test run:\n  "
                + "\n  ".join(problems)
                + f"\n\nThe backup has been KEPT at {self.dir} — it holds the "
                f"pre-run copy of "
                f"{', '.join(str(p) for p in sorted(self.backups))}. "
                f"data/** is gitignored, so that directory is the only copy. "
                f"Restore from it by hand before running anything else, then "
                f"delete it.")
            print(self.error, file=sys.stderr)
            return
        shutil.rmtree(self.dir, ignore_errors=True)


def run_pipeline(argv: list[str]) -> dict:
    """Run a pipeline command with the canonical files guarded.

    Returns the process result, the before/after state of each guarded file,
    the set of relative paths under ``data/processed`` whose mtime moved, and
    any restore failure.
    """
    if not PROCESSED.is_dir():
        skip(f"{PROCESSED} does not exist — nothing to protect")

    guard = Guard(GUARDED)
    result = {
        "argv": argv, "proc": None, "failure": None,
        "restore_error": guard.error, "before": guard.before,
        "after": dict(guard.before), "written": set(),
    }
    if guard.error is not None:
        return result  # the command was never run; nothing was touched

    before_tree = tree_mtimes(PROCESSED)
    try:
        try:
            result["proc"] = subprocess.run(
                [sys.executable, *argv],
                cwd=ROOT, capture_output=True, text=True, timeout=TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            # subprocess.run has already killed the child and reaped it, so
            # the tree is quiescent by the time this lands.
            result["failure"] = f"did not finish within {TIMEOUT}s and was killed"
        except OSError as exc:
            result["failure"] = f"could not be started: {exc}"
    finally:
        # Both readings must happen before the restore, or the restore hides
        # exactly the write this test exists to detect. Nothing between the
        # backup above and the restore below may raise past this block: a
        # KeyboardInterrupt or a timeout must still put the canonical files
        # back, which is why this is a finally and not a context manager
        # wrapped around the assertions.
        after_tree = tree_mtimes(PROCESSED)
        result["after"] = {path: state(path) for path in GUARDED}
        result["written"] = {name for name in set(before_tree) | set(after_tree)
                             if before_tree.get(name) != after_tree.get(name)}
        guard.restore()
        result["restore_error"] = guard.error

    return result


_RUNS: dict[tuple[str, ...], dict] = {}


def cached_run(argv: list[str]) -> dict:
    key = tuple(argv)
    if key not in _RUNS:
        _RUNS[key] = run_pipeline(argv)
    return _RUNS[key]


def require_success(result: dict) -> None:
    """The run completed, exited 0, and the guarded files are safely back."""
    argv = " ".join(result["argv"])
    # First, always: if a canonical file could not be put back, say so before
    # any other assertion, because that is the one failure that needs a human.
    assert result["restore_error"] is None, result["restore_error"]
    assert result["failure"] is None, (
        f"`{argv}` {result['failure']}; the invariants below would pass "
        f"vacuously. The guarded files were restored.")
    proc = result["proc"]
    assert proc.returncode == 0, (
        f"`{argv}` exited {proc.returncode}; the invariant below would "
        f"pass vacuously.\nstdout tail:\n{proc.stdout[-2000:]}\n"
        f"stderr tail:\n{proc.stderr[-2000:]}")


def assert_canonical_untouched(result: dict, path: Path, why: str) -> None:
    """The guarded file has neither changed content nor been rewritten."""
    argv = " ".join(result["argv"])
    before_content, before_mtime = result["before"][path]
    after_content, after_mtime = result["after"][path]
    assert after_content == before_content, (
        f"`{argv}` CHANGED {path}. {why}")
    assert after_mtime == before_mtime, (
        f"`{argv}` rewrote {path}. The bytes happen to be identical today, so "
        f"nothing moved this time — but the run has claimed the canonical "
        f"output, and the next time its inputs change it will move the "
        f"published forecast for real. {why}")


def guarded_or_skip(path: Path, extra: str) -> None:
    """Skip unless ``path`` is where this module expects the canonical file."""
    if not path.exists():
        skip(f"{path} is not on disk, so there is nothing to protect. {extra} "
             f"If a refactor moved the canonical file (per-target directories, "
             f"say), point GUARDED at its new home — this module can only "
             f"protect files it is told about, and silently testing nothing "
             f"would be worse than skipping.")


# --------------------------------------------------------------------------
# fold.py: a non-default fit must not claim the canonical parameters
# --------------------------------------------------------------------------

FOLD_ARGV = ["src/fold.py", "--turnout", "ratio"]


def is_fold_variant(name: str) -> bool:
    """Does this relative path look like a fold VARIANT output?

    fold.py names a non-default fit ``fold<n>[_from<m>]_parameters__<opts>.csv``.
    Matching on the ``__`` marker rather than one exact filename keeps this test
    honest through the per-target directory refactor: what matters is that the
    only thing written is a variant-named file, not where the tree puts it.
    """
    base = Path(name).name
    return base.startswith("fold") and "_parameters__" in base


def test_fold_variant_run_leaves_canonical_parameters_untouched():
    guarded_or_skip(CANONICAL_FOLD, "Run src/fold.py once first.")
    result = cached_run(FOLD_ARGV)
    require_success(result)
    assert_canonical_untouched(
        result, CANONICAL_FOLD,
        "That is the file the live forecast reads γ from: a diagnostic run has "
        "just moved the published forecast. Non-default fits must write beside "
        "the canonical parameters, never over them (fold.py's `variant` "
        "suffix). This is what happened on 2026-08-10.")


def test_fold_variant_run_writes_only_its_own_variant_file():
    result = cached_run(FOLD_ARGV)
    require_success(result)
    # positive control: the run must really have written a variant. The file
    # can be byte-identical to the copy already on disk, so existence proves
    # nothing -- the mtime set is what shows the write happened.
    variants = {name for name in result["written"] if is_fold_variant(name)}
    assert variants, (
        f"`{' '.join(FOLD_ARGV)}` wrote no variant-named parameter file "
        f"(fold<n>_parameters__<opts>.csv). Either the naming scheme changed "
        f"or the run wrote nothing, in which case this file's invariants are "
        f"not being exercised.\nwritten: {sorted(result['written'])}\n"
        f"stdout tail:\n{result['proc'].stdout[-1500:]}")
    stray = result["written"] - variants
    assert not stray, (
        f"`{' '.join(FOLD_ARGV)}` also wrote {sorted(stray)} under "
        f"data/processed. A variant run owns its variant-named output and "
        f"nothing else. Those files have been LEFT AS THE RUN WROTE THEM — "
        f"this test does not revert other people's output. (If another "
        f"pipeline build was running in this working tree at the same time, "
        f"they are its files, not fold.py's — see the caveat at the top of "
        f"this module and re-run alone.)")


# --------------------------------------------------------------------------
# turnout.py: another city's run must not claim Johannesburg's turnout
# --------------------------------------------------------------------------

TURNOUT_ARGV = ["src/turnout.py", "--city", "tshwane"]
# Everything a non-legacy city writes nests under its own slug. The test does
# not care whether that is `tshwane/turnout.csv` or `tshwane/2026/turnout.csv`
# -- only that Johannesburg's copy is not the one being written.
TURNOUT_OWN_PREFIX = "tshwane/"


def test_turnout_for_another_city_leaves_joburg_turnout_untouched():
    if not (ROOT / "cities" / "tshwane.toml").exists():
        skip("cities/tshwane.toml is not present, so there is no second city "
             "to run and no collision to test")
    guarded_or_skip(CANONICAL_TURNOUT, "Run src/turnout.py first.")
    result = cached_run(TURNOUT_ARGV)
    require_success(result)
    assert_canonical_untouched(
        result, CANONICAL_TURNOUT,
        "That is Johannesburg's published turnout file and an input to "
        "montecarlo.py; another city's run has claimed it. --out must default "
        "to the ACTIVE city's processed directory, not to data/processed/.")


def test_turnout_for_another_city_writes_only_its_own_directory():
    if not (ROOT / "cities" / "tshwane.toml").exists():
        skip("cities/tshwane.toml is not present")
    result = cached_run(TURNOUT_ARGV)
    require_success(result)
    # positive control, as above: the file may be byte-identical to what was
    # already there, so the mtime set is what proves the run wrote anything.
    own = {name for name in result["written"]
           if name.startswith(TURNOUT_OWN_PREFIX) and Path(name).name == "turnout.csv"}
    assert own, (
        f"`{' '.join(TURNOUT_ARGV)}` wrote no turnout.csv under "
        f"data/processed/{TURNOUT_OWN_PREFIX}; the run produced no output, so "
        f"this file's invariant is untested.\n"
        f"written: {sorted(result['written'])}\n"
        f"stdout tail:\n{result['proc'].stdout[-1500:]}")
    outside = {name for name in result["written"]
               if not name.startswith(TURNOUT_OWN_PREFIX)}
    assert not outside, (
        f"`{' '.join(TURNOUT_ARGV)}` wrote {sorted(outside)} outside "
        f"data/processed/{TURNOUT_OWN_PREFIX}. A city's run writes only its "
        f"own city's outputs. Those files have been LEFT AS THE RUN WROTE THEM "
        f"— this test does not revert other people's output. (If another "
        f"pipeline build was running in this working tree at the same time, "
        f"they are its files — see the caveat at the top of this module and "
        f"re-run alone.)")


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
