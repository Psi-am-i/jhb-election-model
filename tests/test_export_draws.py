"""The draw file the interactive re-weights holds the published draws, exactly.

Build step S2 of `audits/2026-09-28-interactive-architecture/PLAN.md`.
`src/export_draws.py` runs the model under all four seat laws and writes one
binary file plus a manifest. The page shows these draws as the published
forecast when no control is moved, so the file must BE the published draws,
not a re-derivation that happens to look like them.

What this module proves, at the published city-year, seed and draw count (read
from `forecast_summary.json`, not typed here), by running the export itself:

1. SEATS. Rebuilt from the file, `seat_draws.csv` and the three
   `regime_{rule}_seat_draws.csv` are byte-equal to the published files, and
   `ward_draws.csv` likewise from the ward block.
2. CONSERVATION. In every draw under every law the party columns plus OTHER
   sum to the council, and OTHER is zero because every seat-winning party has
   its own column (an absence-shaped check: CLAUDE.md §4's four parts are
   below it).
3. THE FILE DECLARES ITSELF. The manifest's `artefact_key` carries every field
   `declares.py` requires of a run, each one a real value.
4. SIZE. Under PLAN.md's budget gzipped.
5. THE REFUSALS SEE. On constructed runs: laws that do not share their draws,
   a draw whose seats miss its council, and a file whose manifest disagrees
   with it are each refused, and the refusal goes quiet when reverted.

⚠️ Check 1 holds while the published files are what the code produces. When
the published forecast is regenerated from a changed model, both sides move
together and it stays green; when the model changes and the forecast is NOT
regenerated, it fails, which is the published tree going stale, not the export
breaking. Say which before repairing anything (CLAUDE.md §1).

The export runs four full models in parallel, so this module takes minutes.
"""

from __future__ import annotations

import csv
import gzip
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, scanned  # noqa: E402

import declares  # noqa: E402
import export_draws as E  # noqa: E402
import reweight as R  # noqa: E402

PROCESSED = ROOT / "data" / "processed"
SUMMARY = PROCESSED / "forecast_summary.json"
#: PLAN.md build step S2's budget for the file, gzipped.
BUDGET_GZIP_BYTES = 1_500_000
PUBLISHED = {"deduct": PROCESSED / "seat_draws.csv",
             **{r: PROCESSED / f"regime_{r}_seat_draws.csv"
                for r in ("expand", "level", "cap")}}

_STATE: dict = {}


def _published_run() -> tuple[int, int]:
    """The seed and draw count the published forecast declares."""
    summary = json.loads(SUMMARY.read_text())
    return int(summary["scenario"]["seed"]), int(summary["_draws"])


def _export() -> dict:
    """Run the export once at the published seed and draws; cache the result."""
    if _STATE:
        return _STATE
    seed, draws = _published_run()
    tmp = tempfile.TemporaryDirectory(prefix="export_draws_test_")
    out = Path(tmp.name) / "out"
    done = subprocess.run(
        [sys.executable, str(ROOT / "src" / "export_draws.py"),
         "--city", "joburg", "--target", "2026",
         "--seed", str(seed), "--draws", str(draws), "--out", str(out)],
        cwd=ROOT, capture_output=True, text=True, timeout=5400,
        env=dict(os.environ))
    if done.returncode != 0:
        raise AssertionError(f"the export failed:\n{done.stderr[-4000:]}")
    manifest = json.loads((out / "manifest.json").read_text())
    blob = (out / "base.bin").read_bytes()
    _STATE.update(tmp=tmp, out=out, manifest=manifest, blob=blob,
                  arrays=R.unpack(blob, manifest), seed=seed, draws=draws)
    return _STATE


# -- reconstruction of the published files from the export -------------------

def seat_csv_bytes(arrays: dict, manifest: dict, law: str) -> bytes:
    """`seat_draws.csv` as `montecarlo.main` writes it, from the draw file.

    `main` ranks the WHOLE universe by mean seats with a stable sort and writes
    the first thirteen. The file keeps the seat-winning parties in universe
    order, and a party with no seat in any draw has mean zero and sorts after
    them, so the same stable sort over the file's parties gives the same
    columns whenever at least thirteen parties win a seat.
    """
    parties = manifest["parties"]
    seats = arrays[f"seats/{law}"].astype(np.int64)
    council = arrays[f"council/{law}"].astype(np.int64)
    means = {p: seats[:, j].mean() for j, p in enumerate(parties)}
    top = sorted(parties, key=lambda p: -means[p])[:13]
    col = {p: j for j, p in enumerate(parties)}
    buf = io.StringIO(newline="")
    writer = csv.writer(buf)
    writer.writerow(["draw", "threshold", "council_size"] + top)
    for i in range(seats.shape[0]):
        writer.writerow([i, council[i, 0], council[i, 1]]
                        + [seats[i, col[p]] for p in top])
    return buf.getvalue().encode("utf-8")


def ward_csv_bytes(arrays: dict, manifest: dict) -> bytes:
    """`ward_draws.csv` as `montecarlo.main` writes it, from the draw file."""
    block = next(b for b in manifest["blocks"] if b["name"] == "ward_winner")
    codes = manifest["ward_parties"]
    winners = arrays["ward_winner"]
    buf = io.StringIO(newline="")
    writer = csv.writer(buf)
    writer.writerow(["draw"] + block["columns"])
    for i in range(winners.shape[0]):
        writer.writerow([i] + [codes[c] for c in winners[i]])
    return buf.getvalue().encode("utf-8")


# -- 1: the seats are the published seats -------------------------------------

def test_the_export_ran_the_published_seed_and_draws():
    st = _export()
    key = st["manifest"]["artefact_key"]
    assert (key["seed"], key["draws"]) == (st["seed"], st["draws"])
    for law, path in PUBLISHED.items():
        if law == "deduct":
            continue
        declared = json.loads(path.with_name(f"regime_{law}_summary.json")
                              .read_text())["scenario"]
        assert (int(declared["seed"]), int(declared["draws"])) == (
            st["seed"], st["draws"]), (
            f"{path.name} was published at another seed or draw count, so no "
            f"export can reproduce it")
    assert st["manifest"]["laws"] == list(E.LAWS)


def test_every_published_seat_file_is_reproduced_byte_for_byte():
    st = _export()
    differ = [law for law, path in PUBLISHED.items()
              if seat_csv_bytes(st["arrays"], st["manifest"], law)
              != path.read_bytes()]
    assert not differ, (
        f"{[PUBLISHED[law].name for law in differ]} not reproduced from the "
        f"draw file. If the model changed since they were published, the "
        f"published tree is stale; if not, the export is wrong.")
    scanned(len(PUBLISHED), of=len(E.LAWS), low=1.0, high=1.0,
            what="seat files compared", denominator="the four seat laws")


def test_the_published_ward_winners_are_reproduced_byte_for_byte():
    st = _export()
    assert ward_csv_bytes(st["arrays"], st["manifest"]) == \
        (PROCESSED / "ward_draws.csv").read_bytes()


def test_a_changed_seat_or_ward_is_caught_and_the_check_then_goes_quiet():
    st = _export()
    arrays = dict(st["arrays"])
    law = "level"
    good = arrays[f"seats/{law}"]
    bad = good.copy()
    # a party the published file carries: its first party column
    with PUBLISHED[law].open(encoding="utf-8", newline="") as handle:
        first = next(csv.reader(handle))[3]
    bad[7, st["manifest"]["parties"].index(first)] += 1
    arrays[f"seats/{law}"] = bad
    assert seat_csv_bytes(arrays, st["manifest"], law) != \
        PUBLISHED[law].read_bytes()
    arrays[f"seats/{law}"] = good
    assert seat_csv_bytes(arrays, st["manifest"], law) == \
        PUBLISHED[law].read_bytes()

    good = arrays["ward_winner"]
    bad = good.copy()
    bad[3, 5] = (bad[3, 5] + 1) % len(st["manifest"]["ward_parties"])
    arrays["ward_winner"] = bad
    assert ward_csv_bytes(arrays, st["manifest"]) != \
        (PROCESSED / "ward_draws.csv").read_bytes()
    arrays["ward_winner"] = good
    assert ward_csv_bytes(arrays, st["manifest"]) == \
        (PROCESSED / "ward_draws.csv").read_bytes()


# -- 2: conservation, and no seat-winning party folded into OTHER -------------

def _other_seated_draws(arrays: dict, laws) -> list[tuple[str, int]]:
    """(law, draw) where OTHER holds a seat: a seat-winner lost its column."""
    other = []
    for law in laws:
        seats = arrays[f"seats/{law}"]
        other += [(law, int(i)) for i in np.flatnonzero(seats[:, -1] > 0)]
    return other


def _council_misses(arrays: dict, laws) -> list[tuple[str, int]]:
    out = []
    for law in laws:
        seats = arrays[f"seats/{law}"].astype(np.int64)
        council = arrays[f"council/{law}"].astype(np.int64)[:, 1]
        out += [(law, int(i)) for i in np.flatnonzero(seats.sum(axis=1) != council)]
    return out


def test_every_draw_sums_to_its_council_and_other_holds_no_seat():
    st = _export()
    arrays, manifest = st["arrays"], st["manifest"]
    laws = manifest["laws"]
    # 0. the right population: every law's block, every draw, and OTHER last
    assert all(f"seats/{law}" in arrays for law in E.LAWS)
    for law in laws:
        block = next(b for b in manifest["blocks"] if b["name"] == f"seats/{law}")
        assert block["columns"] == manifest["parties"] + ["OTHER"]
    # 1. it looked: every draw under every law
    examined = sum(arrays[f"seats/{law}"].shape[0] for law in laws)
    scanned(examined, of=st["draws"] * len(E.LAWS), low=1.0, high=1.0,
            what="law-draws examined", denominator="draws x seat laws")
    assert _other_seated_draws(arrays, laws) == []
    assert _council_misses(arrays, laws) == []
    # the file holds a real party list: some but not all of the columns carry
    # seats in the median draw
    seats = arrays["seats/deduct"]
    seated = int((np.median(seats[:, :-1], axis=0) > 0).sum())
    scanned(seated, of=len(manifest["parties"]), low=0.05, high=0.95,
            what="parties seated in the median draw",
            denominator="the file's seat-winning parties")

    # 2. it can see, and goes quiet on revert
    good = arrays["seats/cap"]
    bad = good.copy()
    bad[11, -1] += 1
    probe = dict(arrays, **{"seats/cap": bad})
    assert _other_seated_draws(probe, laws) == [("cap", 11)]
    assert _council_misses(probe, laws) == [("cap", 11)]
    probe["seats/cap"] = good
    assert _other_seated_draws(probe, laws) == []
    assert _council_misses(probe, laws) == []


def _constructed_runs(draws: int = 6) -> dict:
    """Three tiny runs, one per law, over four parties. Nothing observed."""
    rng = np.random.default_rng(1)
    universe = ["A", "B", "C", "Z"]
    turnouts = rng.uniform(0.3, 0.6, size=(draws, 2))
    shares = rng.dirichlet(np.ones(4), size=draws)
    winners = rng.integers(0, 2, size=(draws, 3))
    runs = {}
    for k, law in enumerate(("deduct", "expand", "cap")):
        seats = np.zeros((draws, 4), dtype=np.int64)
        seats[:, 0] = 5 + k
        seats[:, 1] = 3
        seats[0, 2] = 1          # C wins one seat, once: it keeps a column
        council = seats.sum(axis=1)
        runs[law] = {"universe": universe, "wards": ["w1", "w2", "w3"],
                     "pool_names": ["p", "q"], "seats": seats,
                     "thresholds": council // 2 + 1, "council_sizes": council,
                     "ward_winners": winners.copy(), "pr_shares": shares.copy(),
                     "pool_turnouts": turnouts.copy()}
    return runs


def test_the_build_puts_every_seat_winner_in_a_column_and_the_rest_in_other():
    runs = _constructed_runs()
    blob, manifest = E.build(runs)
    manifest["draws"] = runs["deduct"]["seats"].shape[0]
    arrays = R.unpack(blob, manifest)
    assert manifest["parties"] == ["A", "B", "C"]      # Z never seated
    assert manifest["ward_parties"] == ["A", "B"]
    assert _other_seated_draws(arrays, runs) == []
    other_pr = arrays["pr_share"][:, -1]
    assert np.allclose(other_pr, runs["deduct"]["pr_shares"][:, 3],
                       atol=E.PR_SHARE_STEP / 2 + 1e-12)
    assert np.array_equal(arrays["pool_turnout"], runs["deduct"]["pool_turnouts"])


# -- 5: the refusals see ------------------------------------------------------

def test_laws_that_do_not_share_their_draws_are_refused_and_then_accepted():
    runs = _constructed_runs()
    assert E.shared_draw_differences(runs) == []
    kept = runs["cap"]["pool_turnouts"]
    runs["cap"]["pool_turnouts"] = kept + np.where(
        np.arange(kept.size).reshape(kept.shape) == 3, 1e-9, 0.0)
    assert E.shared_draw_differences(runs) == ["cap:pool_turnouts"]
    try:
        E.build(runs)
    except SystemExit as exc:
        assert "did not share their draws" in str(exc)
    else:
        raise AssertionError("a law with different draws was not refused")
    runs["cap"]["pool_turnouts"] = kept
    assert E.shared_draw_differences(runs) == []
    E.build(runs)


def test_a_draw_that_misses_its_council_is_refused():
    runs = _constructed_runs()
    runs["expand"]["council_sizes"] = runs["expand"]["council_sizes"].copy()
    runs["expand"]["council_sizes"][2] += 1
    try:
        E.build(runs)
    except SystemExit as exc:
        assert "do not sum to its council" in str(exc)
    else:
        raise AssertionError("a draw whose seats miss its council was accepted")
    runs["expand"]["council_sizes"][2] -= 1
    E.build(runs)


def test_a_file_that_disagrees_with_its_manifest_is_refused():
    runs = _constructed_runs()
    blob, manifest = E.build(runs)
    manifest["draws"] = runs["deduct"]["seats"].shape[0]
    R.unpack(blob, manifest)
    for broken_blob, broken_manifest in (
            (blob[:-1], manifest),
            (blob, dict(manifest, format="something-else")),
            (blob, dict(manifest, draws=manifest["draws"] + 1))):
        try:
            R.unpack(broken_blob, broken_manifest)
        except R.Refused:
            continue
        raise AssertionError("a draw file that disagrees with its manifest was read")


# -- 3 and 4: the manifest declares, and the file fits ------------------------

def test_the_manifest_carries_every_field_declares_requires_of_a_run():
    st = _export()
    key = st["manifest"]["artefact_key"]
    required = declares.KINDS["run"].required
    missing = [f for f in required if not declares._declared(key.get(f))]
    assert not missing, f"artefact_key lacks {missing}"
    # `_declared` accepts any non-empty dict, so the commit string itself is
    # checked: "<unavailable>" (no git checkout) fails here
    assert len(key["git"]["commit"]) == 40, key["git"]
    assert len(key["code_sha256"]) == 64
    assert set(key["config"]) == set(E.LAWS)
    assert {key["config"][law]["overhang_rule"] for law in E.LAWS} == set(E.LAWS)
    # the pool spec the file was made from is the one on disk now
    import cityconfig
    import freeze
    assert key["inputs"] == freeze.pool_artefact_keys(cityconfig.use("joburg"))


def test_the_file_is_within_the_budget_gzipped():
    st = _export()
    size = len(gzip.compress(st["blob"], compresslevel=9))
    print(f"  base.bin {len(st['blob']):,} bytes, {size:,} gzipped")
    assert size <= BUDGET_GZIP_BYTES, f"{size:,} bytes gzipped"


def test_shares_and_turnouts_are_what_the_model_drew_within_the_declared_step():
    st = _export()
    arrays, manifest = st["arrays"], st["manifest"]
    rows = arrays["pr_share"].sum(axis=1)
    cols = len(manifest["parties"]) + 1
    assert np.max(np.abs(rows - 1.0)) <= cols * E.PR_SHARE_STEP / 2 + 1e-9
    spec = json.loads((PROCESSED / "pools_2026.json").read_text())["pools"]
    block = next(b for b in manifest["blocks"] if b["name"] == "pool_turnout")
    assert set(block["columns"]) == set(spec)
    t = arrays["pool_turnout"]
    for j, name in enumerate(block["columns"]):
        lo, _, hi = spec[name]["turnout"]
        assert np.all((t[:, j] > lo) & (t[:, j] < hi)), name
        assert np.std(t[:, j]) > 0, name


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
