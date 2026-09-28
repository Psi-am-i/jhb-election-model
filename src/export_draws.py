"""Export the published run's draws for the interactive: one binary file and its manifest.

    .venv/bin/python src/export_draws.py --out /tmp/draws
    .venv/bin/python src/export_draws.py --laws deduct --out /tmp/draws

Build step S2 of ``audits/2026-09-28-interactive-architecture/PLAN.md``
(INTEGRATION.md §3a). The page re-weights these draws (``src/reweight.py``)
instead of re-running the model, so the file must hold, per draw, everything a
control weights by and everything a figure is computed from:

* **seats** for every seat-winning party plus ``OTHER``, under each of the four
  seat laws (``deduct``, the statute, and the three counterfactuals of
  ``src/overhang_regimes.py``), with each law's majority threshold and council
  size;
* **ward winners**, one code per ward;
* **PR shares**, the same parties plus ``OTHER``;
* **pool turnouts**, ``ModelRun.pool_turnout_draws`` (MACHINERY.md, "Per-draw
  pool turnouts").

"Seat-winning" is a rule, the same for every party: a party that takes at least
one seat in at least one draw under at least one law gets its own column; every
other party is summed into ``OTHER``. ``OTHER`` seats are therefore zero by
construction and are written anyway, so the page can check that each draw's
columns sum to its council.

⛔ IT CALLS ``run_model`` AND NEVER ``montecarlo.main``
======================================================

``main`` writes the published forecast's files into ``data/processed``, and a
bare ``python src/montecarlo.py`` or ``overhang_regimes.py`` run overwrites the
site's inputs (``overhang_regimes.py``'s docstring is the incident). This module
writes only to ``--out`` and refuses an ``--out`` inside ``data/``. Each seat
law runs in its own process under ``montecarlo.HASH_SEED``, as ``main`` does;
a run under a random hash seed can move a tied last seat (``seats.allocate``'s
largest-remainder key is not a total order), so the export refuses to run
without it.

What the export asserts before it writes
========================================

* **The draws are shared across seat laws.** Pool turnouts, PR shares and ward
  winners are stored ONCE, which is only honest if the four runs drew them
  identically — the seat law acts after every random draw. The export compares
  them array for array and refuses if they differ, because a weight computed on
  one law's draws would then not carry to another by draw index (PLAN.md §7).
* **The inputs did not move under it.** The pool specs' artefact keys are read
  before the first run and after the last; a re-emit in between
  (``CLAUDE.md`` §3) is a refusal, not a footnote.
* **Every draw's seats sum to its council**, per law.

The manifest
============

``manifest.json`` carries the block table :func:`reweight.unpack` needs (names,
dtypes, offsets, column names), the party codes of the ward block, and an
``artefact_key`` with the fields ``declares.py`` requires of a run: ``git``,
``draws``, ``seed``, ``env`` (``freeze.resolved_switches``), ``inputs`` (the
pool specs' keys), ``time``, plus ``code_sha256`` over every ``.py`` file in the
source directory the model was actually imported from — the commit alone does
not describe a tree with uncommitted modules in it — and ``config``, the
scenario levers each law ran with.

Storage choices, stated because they lose information: seats, thresholds and
councils are unsigned integers of the smallest width that holds the largest
value (exact); ward winners are one byte per ward (exact); pool turnouts are
float64, exactly ``ModelRun.pool_turnout_draws``; PR shares are rounded to
:data:`PR_SHARE_STEP`, an error of at most half a step, declared in
the block table. ``tests/test_export_draws.py`` checks
the seat columns byte for byte against the published CSVs.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import gzip
import hashlib
import json
import multiprocessing
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import reweight  # noqa: E402

#: PR shares are stored as whole multiples of this, in 16 bits while every
#: share is under about 0.65 (32 bits above, for a city where one party takes
#: more than that): a thousandth
#: of a percentage point. Storage precision, not a belief about an election —
#: a poll error or a turnout step on the page is thousands of times larger —
#: and it is what brings the file under PLAN.md's size budget (float32 shares
#: alone compressed to more than the whole budget). Recorded in the block
#: table, so the reader knows the loss.
PR_SHARE_STEP = 1e-5

#: The four seat laws, statute first. `deduct` is `montecarlo.DEFAULTS`'s
#: `overhang_rule`; the other three are `overhang_regimes.RULES`.
LAWS = ("deduct", "expand", "level", "cap")


def _code_sha256(src: Path) -> str:
    """sha256 over every ``.py`` file in ``src``, by name and content."""
    h = hashlib.sha256()
    for path in sorted(src.glob("*.py")):
        h.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
    return h.hexdigest()


def _git(*args: str) -> str:
    try:
        return subprocess.run(("git", *args), capture_output=True, text=True,
                              check=True, cwd=Path.cwd()).stdout.strip()
    except Exception:                                    # noqa: BLE001
        return "<unavailable>"


def _run_law(rule: str, city_slug: str, year: str, draws: int, seed: int) -> dict:
    """One full run under one seat law. Returns plain arrays, in a worker process.

    The same order of set-up as ``montecarlo.main``: city, target, then
    ``apply_city`` (council size is per year), then the scenario.
    """
    import cityconfig
    import montecarlo as M

    if os.environ.get("PYTHONHASHSEED") != str(M.HASH_SEED):
        raise SystemExit(f"PYTHONHASHSEED is {os.environ.get('PYTHONHASHSEED')!r}, "
                         f"not montecarlo.HASH_SEED {M.HASH_SEED!r}: a tied last "
                         f"seat would be a coin flip. Run this module as a "
                         f"script, which re-executes under the fixed seed.")
    city = cityconfig.use(city_slug)
    target = cityconfig.use_target(year)
    M.apply_city(city)
    args = argparse.Namespace(
        config=None, draws=draws, seed=seed,
        set=None if rule == "deduct" else [f"overhang_rule={rule}"],
        counterfactual=rule != "deduct")
    scenario = M.load_scenario(args)
    config = {k: scenario[k] for k in sorted(M.DEFAULTS) if k in scenario}
    config = json.loads(json.dumps(config, default=str))
    run = M.run_model(target, scenario, verbose=False)
    universe = list(run.universe)
    seats = np.array([[s.get(p, 0) for p in universe] for s in run.seat_draws],
                     dtype=np.int64)
    return {
        "rule": rule,
        "config": config,
        "universe": universe,
        "wards": list(run.wards),
        "seats": seats,
        "thresholds": np.asarray(run.thresholds, dtype=np.int64),
        "council_sizes": np.asarray(run.council_sizes, dtype=np.int64),
        "ward_winners": np.asarray(run.ward_winner_draws),
        "pr_shares": np.asarray(run.pr_share_draws, dtype=float),
        "pool_turnouts": np.asarray(run.pool_turnout_draws, dtype=float),
        "pool_names": list(run.pool_turnout_names),
        "model_file": str(Path(M.__file__).resolve()),
    }


def _uint(array: np.ndarray) -> np.dtype:
    """The narrowest unsigned integer type that holds every value exactly."""
    if array.size and array.min() < 0:
        raise ValueError("a count is negative")
    top = int(array.max()) if array.size else 0
    for dt in (np.uint8, np.uint16, np.uint32):
        if top <= np.iinfo(dt).max:
            return np.dtype(dt)
    raise ValueError(f"{top} does not fit an unsigned 32-bit integer")


def shared_draw_differences(runs: dict[str, dict]) -> list[str]:
    """Which per-draw inputs differ between laws. Empty means they may be stored once."""
    first = runs[next(iter(runs))]
    differ = []
    for rule, run in runs.items():
        for key in ("universe", "wards", "pool_names"):
            if run[key] != first[key]:
                differ.append(f"{rule}:{key}")
        for key in ("ward_winners", "pr_shares", "pool_turnouts"):
            a, b = run[key], first[key]
            if a.shape != b.shape or a.dtype != b.dtype or not np.array_equal(a, b):
                differ.append(f"{rule}:{key}")
    return differ


def build(runs: dict[str, dict]) -> tuple[bytes, dict]:
    """The draw file and the manifest's data half, from one run per law.

    Refuses if the laws' shared draws differ, or if any draw's seats do not
    sum to its council.
    """
    differ = shared_draw_differences(runs)
    if differ:
        raise SystemExit(f"the seat laws did not share their draws ({differ}); "
                         f"weights cannot cross laws by draw index")
    first = runs[next(iter(runs))]
    universe = first["universe"]
    draws = first["seats"].shape[0]

    won = np.zeros(len(universe), dtype=bool)
    for run in runs.values():
        won |= run["seats"].max(axis=0) > 0
    parties = [p for p, w in zip(universe, won) if w]
    keep = np.flatnonzero(won)
    rest = np.flatnonzero(~won)
    columns = parties + ["OTHER"]

    blocks = []
    for rule, run in runs.items():
        seats = np.column_stack([run["seats"][:, keep],
                                 run["seats"][:, rest].sum(axis=1)])
        if not np.array_equal(seats.sum(axis=1), run["council_sizes"]):
            raise SystemExit(f"{rule}: a draw's seats do not sum to its council")
        blocks.append((f"seats/{rule}", seats.astype(_uint(seats)), columns))
        council = np.column_stack([run["thresholds"], run["council_sizes"]])
        blocks.append((f"council/{rule}", council.astype(_uint(council)),
                       ["threshold", "council_size"]))

    codes = sorted(set(np.unique(first["ward_winners"]).tolist()))
    ward_parties = [universe[j] for j in codes]
    lookup = np.full(len(universe), -1, dtype=np.int64)
    lookup[codes] = np.arange(len(codes))
    winners = lookup[first["ward_winners"]]
    blocks.append(("ward_winner", winners.astype(_uint(winners)), first["wards"]))

    pr = first["pr_shares"]
    pr_cols = np.column_stack([pr[:, keep], pr[:, rest].sum(axis=1)])
    blocks.append(("pr_share", pr_cols, columns, PR_SHARE_STEP))
    blocks.append(("pool_turnout", first["pool_turnouts"], first["pool_names"]))

    blob, table = reweight.pack(blocks)
    data = {
        "format": reweight.FORMAT,
        "draws": int(draws),
        "laws": list(runs),
        "parties": parties,
        "ward_parties": ward_parties,
        "blocks": table,
    }
    return blob, data


def export(city_slug: str, year: str, draws: int, seed: int, out: Path,
           laws: tuple[str, ...] = LAWS, jobs: int | None = None) -> dict:
    """Run each law, build the file, write ``base.bin`` and ``manifest.json`` to ``out``."""
    import cityconfig
    import freeze

    out = out.resolve()
    data_root = (Path.cwd() / "data").resolve()
    if out == data_root or data_root in out.parents:
        raise SystemExit(f"--out {out} is inside {data_root}: the export never "
                         f"writes into the published tree")
    unknown = [law for law in laws if law not in LAWS]
    if unknown:
        raise SystemExit(f"unknown seat law(s) {unknown}; the four are {LAWS}")

    city = cityconfig.use(city_slug)
    keys_before = freeze.pool_artefact_keys(city)
    ctx = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=jobs or len(laws), mp_context=ctx) as pool:
        futures = {law: pool.submit(_run_law, law, city_slug, year, draws, seed)
                   for law in laws}
        runs = {law: futures[law].result() for law in laws}
    keys_after = freeze.pool_artefact_keys(city)
    if keys_after != keys_before:
        raise SystemExit("the pool specs changed while the export ran (a re-emit "
                         "landed); nothing was written. Re-run on a settled tree.")

    blob, manifest = build(runs)
    src = Path(runs[laws[0]]["model_file"]).parent
    manifest["artefact_key"] = {
        "git": {"commit": _git("rev-parse", "HEAD"),
                "dirty": bool(_git("status", "--porcelain", "--", "src"))},
        "code_sha256": _code_sha256(src),
        "code_dir": str(src),
        "city": city_slug,
        "target": year,
        "draws": int(draws),
        "seed": int(seed),
        "env": freeze.resolved_switches(),
        "inputs": keys_before,
        "config": {law: runs[law]["config"] for law in laws},
        "time": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "base.bin").write_bytes(blob)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1),
                                       encoding="utf-8")
    return {"out": str(out), "bytes": len(blob),
            "gzip_bytes": len(gzip.compress(blob, compresslevel=9)),
            "manifest_bytes": (out / "manifest.json").stat().st_size}


def main(argv: list[str] | None = None) -> int:
    import cityconfig
    import montecarlo as M

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    cityconfig.add_city_argument(parser)
    cityconfig.add_target_argument(parser)
    parser.add_argument("--draws", type=int, default=None,
                        help="default: montecarlo.DEFAULTS, the published count")
    parser.add_argument("--seed", type=int, default=None,
                        help="default: montecarlo.DEFAULTS, the published seed")
    parser.add_argument("--laws", nargs="+", default=list(LAWS), choices=LAWS)
    parser.add_argument("--jobs", type=int, default=None)
    parser.add_argument("--out", type=Path, default=None,
                        help="default: a new scratch directory")
    args = parser.parse_args(argv)
    city = cityconfig.use(getattr(args, "city", None))
    target = cityconfig.use_target(getattr(args, "target", None))
    draws = args.draws or int(M.DEFAULTS["draws"])
    seed = args.seed or int(M.DEFAULTS["seed"])
    out = args.out or Path(tempfile.mkdtemp(prefix="export_draws_"))
    report = export(city.slug, target.year, draws, seed, out,
                    tuple(args.laws), args.jobs)
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    # Before anything else, as `montecarlo`'s own guard does: this may replace
    # the process with one under the fixed hash seed, which the workers inherit.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import montecarlo
    montecarlo.fix_hash_seed()
    raise SystemExit(main())
