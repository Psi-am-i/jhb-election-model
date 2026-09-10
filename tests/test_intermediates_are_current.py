"""Every processed intermediate is what today's generators produce.

⛔ THIS IS THE GUARD THAT DID NOT EXIST ON 2026-09-10, WHEN 26 OF THE 104 CSVs
UNDER ``data/processed`` TURNED OUT NOT TO MATCH THE CODE (MODEL-LOG §1.222).

Seven cities' ``<city>/2021/turnout.csv`` predated the 2026-08-09 pre-2011
archive ingest, so λ̂ had no 2011 anchor and ``turnout_2021_projected`` — the
column ``montecarlo.py`` reads as ``ratio_pattern`` — was wrong on 207 to 709
voting districts each, for a month. ``montecarlo.py:4142`` already said in a
comment that this artefact "reaches the model WITH NO KEY AT ALL … a stale or
rebuilt copy moves every draw in silence". **It was right, and being right in a
comment caught nothing.**

``pools_*.json`` cannot go stale unnoticed because it carries an
``artefact_key``. Nothing else here does. For those, the only check available is
to run the generator and compare, which is what this module does.

WHY IT REGENERATES INTO A PURGED SCRATCH ROOT, AND NOT IN PLACE
---------------------------------------------------------------
Two earlier attempts at this audit returned confident wrong answers, both from
the population and not from the tree (CLAUDE.md §4 rule 0):

* a reader trace that was too narrow reported "nothing reads it" for six
  families that have real readers;
* a comparison against a scratch tree in which **most files had never been
  rewritten**, so ``IDENTICAL`` was trivially true for them. The mtime fence
  meant to catch that was worthless, because ``cp -R`` restamps every file.

So this test **deletes every CSV in the scratch copy first**. A file that exists
afterwards was written by a generator in this run; one that does not was written
by nothing. There is no way for an unwritten file to score as current.
"""

from __future__ import annotations

import atexit
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, run_module, skip  # noqa: E402

PROCESSED = ROOT / "data" / "processed"
PY = ROOT / ".venv" / "bin" / "python"

CITIES = ("joburg", "buffalocity", "capetown", "ekurhuleni", "ethekwini",
          "mangaung", "nelsonmandelabay", "tshwane")
YEARS = ("2011", "2016", "2021", "2026")

# ⛔ THE POPULATION THIS TEST DOES **NOT** COVER, STATED RATHER THAN IMPLIED.
#
# These are written by running the MODEL (or a retired script), not by an
# ingest generator, so regenerating them would mean 24 Monte Carlo runs. They
# are excluded by name and the exclusion is asserted BOTH WAYS below: a new
# family that this module cannot reproduce must be added here deliberately, and
# a name here that no longer exists on disk must be removed.
NOT_GENERATED_HERE = (
    "coalition_minority.csv", "coalition_mwc.csv",
    "coalition_pairs_triples.csv", "coalition_power.csv",
    "seat_draws.csv", "ward_winner_probs.csv",
    "regime_cap_seat_draws.csv", "regime_expand_seat_draws.csv",
    "regime_level_seat_draws.csv",
    # Fold 5 has `lambda_pair: None`, so the default `--turnout level` is
    # refused and every non-default option writes a VARIANT filename. No
    # invocation available today reproduces this file under this name (§1.222).
    # Read only by `fold.py --fit-from 5`, never by the forecast.
    "fold5_parameters.csv",
    # A deliberate experiment variant, reproducible with `--turnout ratio`.
    "fold1_parameters__turnout-ratio.csv",
)

# A two-sided bound on the population, as a fraction of a COMPUTED denominator
# (CLAUDE.md §4 rule 1). A bare floor ratchets; when it trips the cheapest fix
# is to lower it.
MIN_COMPARED_FRACTION = 0.55
MAX_COMPARED_FRACTION = 0.95


def _scratch_root(tmp: Path) -> Path:
    """A repository root whose `data/processed` holds no CSV at all."""
    root = tmp / "root"
    (root / "data").mkdir(parents=True)
    shutil.copytree(PROCESSED, root / "data" / "processed")
    for stale in (root / "data" / "processed").rglob("*.csv"):
        stale.unlink()
    (root / "data" / "raw").symlink_to(ROOT / "data" / "raw")
    for name in ("src", "cities", "config", "content"):
        if (ROOT / name).exists():
            (root / name).symlink_to(ROOT / name)
    return root


def _regenerate(root: Path) -> list[str]:
    """Run every ingest generator from empty. Returns the ones that failed."""
    failed: list[str] = []

    def run(*argv: str) -> None:
        proc = subprocess.run([str(PY), *argv], cwd=root,
                              capture_output=True, text=True)
        if proc.returncode != 0:
            failed.append(" ".join(argv) + f" -> {proc.stderr.strip()[-200:]}")

    for city in CITIES:
        run("src/build_concordance.py", "--city", city)
    run("src/build_crosswalk.py")
    run("src/byelections.py")
    for city in CITIES:
        for year in YEARS:
            run("src/turnout.py", "--city", city, "--target", year)
            run("src/gamma_recent.py", "--city", city, "--target", year)
        for fold in ("1", "2", "3", "4"):
            run("src/fold.py", "--fold", fold, "--city", city)
    return failed


def _compare(root: Path) -> tuple[list[str], list[str]]:
    """(stale, uncovered) — differing files, and live files nothing produced."""
    stale, uncovered = [], []
    for live in sorted(PROCESSED.rglob("*.csv")):
        rel = live.relative_to(PROCESSED)
        made = root / "data" / "processed" / rel
        if not made.exists():
            uncovered.append(str(rel))
        elif live.read_bytes() != made.read_bytes():
            stale.append(str(rel))
    return stale, uncovered


_CACHE: dict[str, object] = {}


def _sweep() -> dict:
    """The sweep, run once and shared by every test below."""
    if _CACHE:
        return _CACHE  # type: ignore[return-value]
    if not PY.exists():
        skip(f"no interpreter at {PY}")
    if not PROCESSED.exists():
        skip("no data/processed; nothing to check")
    tmp = Path(tempfile.mkdtemp(prefix="intermediates-"))
    try:
        root = _scratch_root(tmp)
        failed = _regenerate(root)
        stale, uncovered = _compare(root)
        made = {p.name for p in (root / "data" / "processed").rglob("*.csv")}
        _CACHE.update(root=str(root), failed=failed, stale=stale,
                      uncovered=uncovered, made=made,
                      total=len(list(PROCESSED.rglob("*.csv"))))
        # Removed once, at interpreter exit, rather than by a fake `test_`
        # function whose passing would mean nothing.
        atexit.register(shutil.rmtree, tmp, True)
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    return _CACHE  # type: ignore[return-value]


def test_it_looked_at_a_population_of_the_expected_size():
    """RULE 1: non-empty, and inside a TWO-SIDED bound on a computed total."""
    s = _sweep()
    total = s["total"]
    assert total > 0, "no CSVs under data/processed at all -- nothing scanned"
    compared = total - len(s["uncovered"])
    lo, hi = int(total * MIN_COMPARED_FRACTION), int(total * MAX_COMPARED_FRACTION)
    assert lo <= compared <= hi, (
        f"this test compared {compared} of {total} processed CSVs, outside the "
        f"expected {lo}-{hi}. Too few means the generators stopped producing "
        f"things and the test has gone quietly blind; too many means a family "
        f"listed in NOT_GENERATED_HERE is now reproducible and the list is "
        f"stale. Either way the population changed and the change is the "
        f"finding -- do not widen the bound to make this pass.")


def test_every_generator_ran():
    """A generator that CRASHED would otherwise leave its file 'uncovered'."""
    s = _sweep()
    tolerated = [f for f in s["failed"] if "fold 5" not in f]
    assert not tolerated, (
        "generators failed during the sweep, so their files were never "
        "produced and would have been silently reported as uncovered rather "
        "than stale:\n  " + "\n  ".join(tolerated))


def test_the_uncovered_set_is_exactly_the_declared_one_BOTH_WAYS():
    """RULE 0: assert the exclusion list against the tree, in both directions."""
    s = _sweep()
    unexpected = [u for u in s["uncovered"]
                  if Path(u).name not in NOT_GENERATED_HERE]
    assert not unexpected, (
        "files under data/processed that NO generator reproduces and that "
        "NOT_GENERATED_HERE does not declare. Each is a file whose provenance "
        "is unknown -- establish it, then either add a generator or add it to "
        "the list with the reason:\n  " + "\n  ".join(unexpected))

    on_disk = {p.name for p in PROCESSED.rglob("*.csv")}
    ghosts = [n for n in NOT_GENERATED_HERE if n not in on_disk]
    assert not ghosts, (
        "NOT_GENERATED_HERE names files that are no longer on disk. An "
        "exclusion nobody can see is how a register drifts (§1.222 found a "
        "deleted lever sitting in one for days): remove them.\n  "
        + "\n  ".join(ghosts))


def test_no_processed_intermediate_is_stale():
    """The claim itself: on-disk equals what today's code produces."""
    s = _sweep()
    assert not s["stale"], (
        f"{len(s['stale'])} processed intermediate(s) differ from what today's "
        f"generators produce. These reach the model with NO artefact key, so "
        f"nothing else will notice. Regenerate them and MEASURE -- do not "
        f"assume a stale intermediate is inert, and do not assume it is not "
        f"(§1.222: 26 were stale, 7 of them in a column the model reads, and "
        f"the measured effect on the 24-city-year seat table was exactly "
        f"zero):\n  " + "\n  ".join(s["stale"]))


def test_the_comparator_CAN_SEE_a_stale_file():
    """RULE 2: a constructed violation, pushed through the same detector."""
    s = _sweep()
    root = Path(s["root"])
    victim = None
    for cand in sorted((root / "data" / "processed").rglob("*.csv")):
        rel = cand.relative_to(root / "data" / "processed")
        if (PROCESSED / rel).exists():
            victim = cand
            break
    assert victim is not None, "no regenerated file to perturb -- see rule 1"

    original = victim.read_bytes()
    try:
        victim.write_bytes(original + b"\n# a byte the generator did not write\n")
        stale, _ = _compare(root)
        rel = str(victim.relative_to(root / "data" / "processed"))
        assert rel in stale, (
            f"the comparator did not notice {rel} differing by an appended "
            f"line. It is therefore not testing what its name claims.")
    finally:
        victim.write_bytes(original)

    # And the other half of "it can see": with the perturbation reverted, the
    # same detector must go quiet again. A comparator that always fires proves
    # nothing either.
    stale, _ = _compare(root)
    assert str(victim.relative_to(root / "data" / "processed")) not in stale, (
        "the comparator still reports the file as stale after the constructed "
        "violation was reverted, so it is not reading the file it names.")


def test_the_scratch_root_really_was_purged():
    """The instrument's own premise, asserted rather than trusted.

    If the copy were not purged, every unwritten file would compare equal to
    itself and the whole module would pass while checking nothing. That is not
    hypothetical: it is exactly how the 2026-09-10 audit's second attempt got a
    wrong answer, and an mtime fence does NOT catch it because `cp -R`
    restamps.
    """
    s = _sweep()
    root = Path(s["root"])
    made = {p.name for p in (root / "data" / "processed").rglob("*.csv")}
    # Every CSV now in the scratch root is one a generator wrote in this run,
    # so no name excluded from the sweep may be present.
    leaked = sorted(n for n in NOT_GENERATED_HERE if n in made)
    assert not leaked, (
        "files that no generator in this sweep produces are present in the "
        "scratch root, so the purge did not happen and 'identical' is "
        "trivially true for them:\n  " + "\n  ".join(leaked))


if __name__ == "__main__":
    # AT THE END — see test_register_matches_code. Append tests ABOVE this.
    raise SystemExit(run_module(globals()))
