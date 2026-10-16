"""Each draw's pool turnouts are recorded, and recording them moves no draw.

F1 of the freeze plan (TODO.md §0; audits/2026-09-28-interactive-architecture/
PLAN.md findings 2, 3 and 8, build step S1). `draw_pools` now keeps the turnout
each voter pool received from `correlated_triangular` in every draw, and
`run_model` carries it out as `ModelRun.pool_turnout_draws`. The interactive
re-weights the published draws by these values, so they must be the values
the published draws were made with, and recording them must not change one.

What this module proves, at Johannesburg 2026 on the shipped seed and the
shipped draw count, each run in its own interpreter under `HASH_SEED`:

1. OFF vs ON. The code before the recording existed (`BEFORE_RECORDING`,
   extracted with `git archive`) and the live code produce identical values in
   every `*draws` field of `ModelRun`, and the only field the live run adds is
   `pool_turnout_draws`. Both produce `seat_draws.csv` byte for byte.
2. INDEPENDENT CAPTURE. A wrapper around `montecarlo.correlated_triangular`
   (the architecture report's fallback, which needs no edit to the model)
   sees exactly the values recorded, pool by pool and draw by draw. Pools are
   identified by the band the wrapper was handed, not by position. Under the
   universal law the calibration streams also reach the function (one
   N_CAL-draw pass for the composition variance, then N_CAL draws per κ
   iteration, recording nothing); the wrapper tags those calls by the
   caller's stage prefix, and they are counted against
   N_CAL x (iterations + 1) x pools rather than silently dropped.
3. THE CHECKS CAN SEE. A one-ulp change to one cell, two swapped columns, one
   changed drawn share and one value pushed onto a band edge are each caught,
   and each check goes quiet again when the change is reverted.
4. BANDS. Every recorded value lies strictly inside its pool's (lo, hi) from
   the pool spec, and the recorded pools are exactly the spec's pools.

A tied group (none at Johannesburg 2026) is covered at `make_drawer` level by
tying two pools in memory: every member records the group's one shock.

⛔ CHECK 1 WAS RETIRED AT THE FREEZE (2026-09-30), AS PLANNED. F3 and F8
changed drawn numbers legitimately, so the live model no longer matches
`4711a15` and the off-vs-on comparison expired. It was removed, not re-pinned:
re-pinning would compare the model with itself. It held from F1 (`bfa5d2b`)
until then, which is the window the recording landed in. Check 2 now compares
only the live run with the published seats, which the freeze edition
regenerated from this model. The original note follows.

⚠️ CHECK 1 HAS A SHELF LIFE, AND IT ENDS LOUDLY. It compares the live model
with commit `BEFORE_RECORDING`. It holds only while no drawn number has
legitimately changed since that commit; the first pool repair (F3) or re-emit
(F8) ends it, and the test then fails saying so. Retire it at that point —
keeping it green by moving the pin would compare the model with itself, and
comparing a changed model with the old commit would be self-benchmarking
(CLAUDE.md §1). Check 2 (the published seats) likewise holds until the
published forecast is next regenerated from a changed model; checks 2-4 on
the live run do not expire.

Three runs at the full draw count go in parallel subprocesses, so this module
takes a few minutes.
"""

from __future__ import annotations

import csv
import io
import json
import os
import pickle
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, scanned  # noqa: E402

import montecarlo as M  # noqa: E402

CITY, TARGET = "joburg", "2026"
SEED = 20261104
PUBLISHED_SEATS = ROOT / "data" / "processed" / "seat_draws.csv"
SPEC = ROOT / "data" / "processed" / "pools_2026.json"
RECORD = "pool_turnout_draws"

# Runs in a fresh interpreter: argv = src dir, output pickle, wrap flag.
_WORKER = r'''
import pickle, sys
src, out, wrap = sys.argv[1], sys.argv[2], sys.argv[3] == "1"
sys.path.insert(0, src)
import numpy as np
import cityconfig
cityconfig.use(%(city)r)
target = cityconfig.use_target(%(target)r)
import montecarlo as mc
calls = []
if wrap:
    real = mc.correlated_triangular
    def recording(z_own, spec, z_common, rho):
        value = real(z_own, spec, z_common, rho)
        # The caller is the drawer's `pool_turnouts`, which has no stage
        # prefix: since 2026-10-16 the calibration pass draws no turnout. A
        # caller carrying `pre == "calib."` would be a calibration pass that
        # sees turnout again (the κ lock, MODEL-LOG §1.315), counted below.
        calib = sys._getframe(1).f_locals.get("pre") == "calib."
        calls.append((tuple(float(x) for x in spec), float(value), calib))
        return value
    mc.correlated_triangular = recording
class Args:
    config = None; set = None; draws = None; seed = %(seed)d
run_dir = (sys.argv[4] if len(sys.argv) > 4 else None)
run = mc.run_model(target, mc.load_scenario(Args()), verbose=False,
                   run_dir=run_dir)
kappa_iters = None
if run_dir:
    import json, pathlib
    widths = json.loads((pathlib.Path(run_dir) / "35_widths.json").read_text())
    kappa_iters = widths["kappa_iters"]
fields = {n: getattr(run, n) for n in dir(run)
          if n.endswith("draws") and not n.startswith("_")}
payload = {
    "file": mc.__file__, "fields": fields, "universe": list(run.universe),
    "thresholds": run.thresholds, "council_sizes": run.council_sizes,
    "names": list(getattr(run, "pool_turnout_names", []) or []),
    "has_record": hasattr(run, "pool_turnout_draws"),
    "calls": calls, "kappa_iters": kappa_iters, "n_cal": mc.N_CAL,
}
with open(out, "wb") as handle:
    pickle.dump(payload, handle)
''' % {"city": CITY, "target": TARGET, "seed": SEED}

_STATE: dict = {}


def _launch(src: Path, out: Path, wrap: bool, worker: Path) -> Path:
    env = dict(os.environ, PYTHONHASHSEED=M.HASH_SEED)
    # The wrapped run also writes a trace, for the calibration pass's
    # iteration count (`35_widths.kappa_iters`). A trace changes no drawn
    # number (test_chain), and the wrapped run is compared field by field
    # with the unwrapped, untraced one below.
    argv = [sys.executable, str(worker), str(src), str(out), "1" if wrap else "0"]
    if wrap:
        argv.append(str(out.with_suffix(".trace")))
    done = subprocess.run(
        argv,
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=3600)
    if done.returncode != 0:
        raise AssertionError(f"run from {src} failed:\n{done.stderr[-3000:]}")
    return out


def _runs() -> dict:
    """Live, and live+wrapper, run once and cached. (The pre-recording run
    was retired with check 1 at the freeze; see the module docstring.)"""
    if _STATE:
        return _STATE
    tmp = tempfile.TemporaryDirectory(prefix="draw_record_")
    base = Path(tmp.name)
    worker = base / "worker.py"
    worker.write_text(_WORKER, encoding="utf-8")
    jobs = {"on": (ROOT / "src", False),
            "wrapped": (ROOT / "src", True)}
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futures = {k: pool.submit(_launch, src, base / f"{k}.pkl", wrap, worker)
                   for k, (src, wrap) in jobs.items()}
        for k, fut in futures.items():
            with fut.result().open("rb") as handle:
                _STATE[k] = pickle.load(handle)
    _STATE["_tmp"] = tmp
    return _STATE


# -- comparators, each exercised against a constructed violation below --------

def _same(a, b) -> bool:
    if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        a, b = np.asarray(a), np.asarray(b)
        return a.dtype == b.dtype and a.shape == b.shape and np.array_equal(a, b)
    return type(a) is type(b) and a == b


def _differing_fields(off: dict, on: dict) -> list[str]:
    return sorted(n for n in set(off) & set(on) if not _same(off[n], on[n]))


def _spec_pools() -> dict[str, tuple[float, float, float]]:
    pools = json.loads(SPEC.read_text())["pools"]
    return {name: tuple(float(x) for x in cfg["turnout"])
            for name, cfg in pools.items()}


def _capture_matrix(calls, names, draws) -> np.ndarray:
    """The wrapper's values as a (draws, pools) matrix, pools found by band."""
    bands = _spec_pools()
    by_band = {bands[n]: n for n in names}
    assert len(by_band) == len(names), "two pools share a band; cannot identify"
    column = {n: j for j, n in enumerate(names)}
    seen = {n: 0 for n in names}
    out = np.full((draws, len(names)), np.nan)
    for spec, value, calib in calls:
        if calib:
            continue
        assert spec in by_band, f"a call with band {spec} matches no pool"
        name = by_band[spec]
        out[seen[name], column[name]] = value
        seen[name] += 1
    assert all(k == draws for k in seen.values()), (
        f"wrapper calls per pool {seen}, expected {draws} each")
    return out


def _record_disagreement(record: np.ndarray, capture: np.ndarray) -> int:
    """Cells where the record differs from the capture (shape mismatch = all)."""
    if record.shape != capture.shape:
        return max(record.size, capture.size)
    return int(np.sum(record != capture))


def _outside_band(record: np.ndarray, names) -> list[tuple[str, int]]:
    bands = _spec_pools()
    bad = []
    for j, name in enumerate(names):
        lo, _, hi = bands[name]
        col = record[:, j]
        bad += [(name, int(i)) for i in np.flatnonzero(~((col > lo) & (col < hi)))]
    return bad


def _seat_csv_bytes(payload: dict, top: list[str]) -> bytes:
    """`seat_draws.csv` as `montecarlo.main` writes it, from a run's payload."""
    buf = io.StringIO(newline="")
    writer = csv.writer(buf)
    writer.writerow(["draw", "threshold", "council_size"] + top)
    for i, s in enumerate(payload["fields"]["seat_draws"]):
        writer.writerow([i, payload["thresholds"][i], payload["council_sizes"][i]]
                        + [s.get(p, 0) for p in top])
    return buf.getvalue().encode("utf-8")


def _published_top() -> list[str]:
    with PUBLISHED_SEATS.open(encoding="utf-8", newline="") as handle:
        return next(csv.reader(handle))[3:]


# -- 0: the comparison ran the code it claims to have run ---------------------

def test_the_published_seats_are_byte_equal_with_recording_on():
    runs = _runs()
    published = PUBLISHED_SEATS.read_bytes()
    top = _published_top()
    seats = runs["on"]["fields"]["seat_draws"]
    ranked = sorted(runs["on"]["universe"],
                    key=lambda p: -np.mean([s.get(p, 0) for s in seats]))
    assert top == ranked[:len(top)], "published columns are not the run's ranking"
    assert _seat_csv_bytes(runs["on"], top) == published, (
        "with the recording in place the published seats are not reproduced")


# -- 2: the record is what an independent wrapper sees ------------------------

def test_the_record_equals_an_independent_capture_of_every_pool_turnout():
    runs = _runs()
    wrapped, on = runs["wrapped"], runs["on"]
    names = wrapped["names"]
    record = np.asarray(wrapped["fields"][RECORD])
    draws = len(wrapped["fields"]["seat_draws"])
    capture = _capture_matrix(wrapped["calls"], names, draws)
    assert _record_disagreement(record, capture) == 0
    # The wrapper is a pass-through: the wrapped run is the live run.
    assert names == on["names"]
    assert not _differing_fields(on["fields"], wrapped["fields"])
    run_calls = [c for c in wrapped["calls"] if not c[2]]
    calib_calls = [c for c in wrapped["calls"] if c[2]]
    scanned(len(run_calls), of=draws * len(names), low=1.0, high=1.0,
            what="wrapper calls in the run's draws",
            denominator="draws x pools (no ties here)")
    # The calibration pass reads NO turnout (owner, 2026-10-16: turnout
    # enters the vote downstream of the preference draw, so κ never sees it).
    # Under the previous law it made N_CAL x (kappa_iters + 1) x pools calls
    # here; any call now is the κ lock put back.
    assert wrapped["kappa_iters"] and wrapped["kappa_iters"] >= 1, (
        "the run made no calibration pass; the universal law is not in force")
    assert not calib_calls, (
        f"{len(calib_calls)} pool-turnout draws on the calibration streams: "
        f"the calibration pass sees turnout")


# -- 3: each check can see ----------------------------------------------------

def test_each_check_catches_a_constructed_violation_and_then_goes_quiet():
    runs = _runs()
    wrapped = runs["wrapped"]
    names = wrapped["names"]
    record = np.array(wrapped["fields"][RECORD], copy=True)
    capture = _capture_matrix(wrapped["calls"], names,
                              len(wrapped["fields"]["seat_draws"]))

    # a one-ulp change to one cell
    assert _record_disagreement(record, capture) == 0
    kept = record[17, 1]
    record[17, 1] = np.nextafter(kept, 1.0)
    assert _record_disagreement(record, capture) == 1
    record[17, 1] = kept
    assert _record_disagreement(record, capture) == 0

    # the wrong pool: two columns swapped
    record[:, [0, 1]] = record[:, [1, 0]]
    assert _record_disagreement(record, capture) > 0
    record[:, [0, 1]] = record[:, [1, 0]]
    assert _record_disagreement(record, capture) == 0

    # a value on its band's edge
    lo = _spec_pools()[names[2]][0]
    kept = record[5, 2]
    record[5, 2] = lo
    assert _outside_band(record, names) == [(names[2], 5)]
    record[5, 2] = kept
    assert _outside_band(record, names) == []

    # one drawn share changed between two otherwise identical runs (the
    # wrapped run is a pass-through of the live one)
    on = runs["on"]["fields"]
    wr = dict(runs["wrapped"]["fields"])
    assert _differing_fields(on, wr) == []
    pr = np.array(wr["pr_share_draws"], copy=True)
    pr[3, 0] = np.nextafter(pr[3, 0], 1.0)
    wr["pr_share_draws"] = pr
    assert _differing_fields(on, wr) == ["pr_share_draws"]
    wr["pr_share_draws"] = runs["wrapped"]["fields"]["pr_share_draws"]
    assert _differing_fields(on, wr) == []


# -- 4: inside the bands ------------------------------------------------------

def test_every_recorded_turnout_lies_inside_its_pools_band():
    runs = _runs()
    names = runs["on"]["names"]
    record = np.asarray(runs["on"]["fields"][RECORD])
    spec = _spec_pools()
    assert set(names) == set(spec), (
        f"recorded {sorted(names)}, the spec declares {sorted(spec)}")
    assert record.shape == (len(runs["on"]["fields"]["seat_draws"]), len(spec))
    assert not _outside_band(record, names)
    # it looked: every column moves, so a constant fill would fail here
    assert all(np.std(record[:, j]) > 0 for j in range(len(names)))


# -- ties: every member records the group's one shock -------------------------

def test_a_tied_group_records_its_one_shared_shock():
    from test_drawer import build_inputs
    scenario, base_city_d, centres, index = build_inputs(law="incumbent")
    names = list(scenario["pools"])
    tied = names[-2:]
    for nm in tied:
        scenario["pools"][nm]["tie"] = "tied-for-test"
    bands = {nm: tuple(float(x) for x in scenario["pools"][nm]["turnout"])
             for nm in names}
    group_band = tuple(float(np.mean([bands[nm][k] for nm in tied]))
                       for k in range(3))

    calls = []
    real = M.correlated_triangular

    def recording(z_own, spec, z_common, rho):
        value = real(z_own, spec, z_common, rho)
        calls.append((tuple(float(x) for x in spec), float(value)))
        return value

    M.correlated_triangular = recording
    try:
        draws = 50
        draw = M.make_drawer(scenario, base_city_d, centres, index,
                             M.DrawStreams(f"joburg|2026|{SEED}", draws))
        for d in range(draws):
            draw(d)
            # as run_model does: the draw's pool turnouts, which the
            # preference draw no longer reads (2026-10-16)
            draw.pool_turnouts(d)
    finally:
        M.correlated_triangular = real

    record = np.asarray(draw.turnout_record)
    cols = {nm: j for j, nm in enumerate(draw.turnout_pools)}
    groups = len(names) - len(tied) + 1
    assert len(calls) == draws * groups
    assert record.shape == (draws, len(names))
    seen: dict[str, list[float]] = {}
    for spec, value in calls:
        if np.allclose(spec, group_band, rtol=0, atol=1e-15):
            key = "group"
        else:
            key = next(nm for nm in names if nm not in tied and spec == bands[nm])
        seen.setdefault(key, []).append(value)
    assert np.array_equal(record[:, cols[tied[0]]], record[:, cols[tied[1]]])
    assert np.array_equal(record[:, cols[tied[0]]], np.array(seen["group"]))
    for nm in names:
        if nm not in tied:
            assert np.array_equal(record[:, cols[nm]], np.array(seen[nm]))


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
