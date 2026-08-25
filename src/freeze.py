"""Freeze a stage-1 forecast, and hash everything that could move it.

**Why this exists.** A restructure is about to move a great deal of code, and
the only way to know whether it moved a NUMBER is to diff against a fixed
reference. `data/processed/history.json` could not serve as one: it records
neither its draw count nor its seed, so on 2026-08-24 it took three separate
panel runs to establish whether a refactor had changed anything or whether the
committed artefact had simply been produced at a different `--draws`. That is a
provenance gap, and this module is the answer to it.

**What is frozen.** Not just the forecast — everything that determines it:

* the resolved scenario, every key, after `apply_city` and `--set`;
* **the six import-time environment switches.** These change the forecast, are
  absent from `DEFAULTS`, unreachable from `--set`, and invisible to the run
  trace, so two runs differing in them are indistinguishable from their
  recorded scenario. `SIGMA_TWO_TERM` alone selects between two entirely
  different sigma decompositions;
* the `artefact_key` of every pool spec the run read;
* the git commit, the numpy version and the Python version;
* the party medians and intervals, and a hash of the full seat-draw matrix.

**What the hash covers.** `content_sha256` is taken over a canonical JSON
serialisation of the forecast content *and* the configuration above. Two runs
agreeing on it agree on everything that matters. It deliberately does NOT cover
timestamps or file paths, which move without meaning.

**Reproducibility, and its known limit.** The model is deterministic given
(scenario, seed, artefacts, code). Two runs of identical code agree to
**1.9e-14** on every scalar metric with no seat metric moving — measured
2026-08-24 — which is float summation order in the parallel path, not
nondeterminism. So `--verify` compares seats exactly and floats at 1e-9.

Usage::

    python src/freeze.py                    # write the freeze
    python src/freeze.py --verify           # re-run and compare; exit 1 on drift

sources:
    MODEL-LOG §1.93 — the provenance gap this closes
    MODEL-LOG §1.91 — SIGMA_TWO_TERM, the switch that made the gap visible
    PLAN: "Make the model declare itself", Phase 0
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

import numpy as np                      # noqa: E402

import cityconfig                       # noqa: E402
import montecarlo as M                  # noqa: E402

DATA = REPO / "data/raw/elections"
FROZEN = REPO / "data/processed/forecast_frozen.json"

# The six switches read from the environment at IMPORT time. Every one changes
# the forecast and none is reachable from `--set`, so a freeze that omitted them
# would be a freeze of an unknown configuration. Kept as a literal list rather
# than discovered, so that adding a seventh switch without adding it here is a
# review question rather than a silent omission.
ENV_SWITCHES = (
    "SIGMA_TWO_TERM",
    "THETA_EXCLUDE_TARGETS",
    "FILTER_TYPE_A",
    "EXCLUDE_DEMARCATION_CROSSING",
    "THETA_WINDOW",
    "CITY_SLUG",
)


def _git(*args: str) -> str:
    try:
        return subprocess.run(("git", *args), cwd=REPO, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:                                        # noqa: BLE001
        return "<unavailable>"


def resolved_switches() -> dict[str, object]:
    """What the switches were, as the modules RESOLVED them.

    The raw environment is recorded too, but the resolved value is what the
    model used: `SIGMA_TWO_TERM` unset resolves to True since 2026-08-24, and
    an unset variable reading as its default is exactly the confusion this
    guards against.
    """
    import levels
    import polling
    return {
        "raw": {k: os.environ.get(k) for k in ENV_SWITCHES},
        "resolved": {
            "polling.SIGMA_TWO_TERM": bool(polling.SIGMA_TWO_TERM),
            "levels.FILTER_TYPE_A": bool(levels.FILTER_TYPE_A),
            "levels.EXCLUDE_DEMARCATION_CROSSING":
                bool(levels.EXCLUDE_DEMARCATION_CROSSING),
            "levels.THETA_WINDOW": int(levels.THETA_WINDOW),
            "levels.THETA_EXCLUDE_TARGETS":
                sorted(levels.THETA_EXCLUDE_TARGETS),
        },
    }


def pool_artefact_keys(city) -> dict[str, object]:
    """The `artefact_key` of every emitted spec for this city.

    The specs are NOT tracked by git — that is why the key exists at all — so a
    freeze that did not record them could be reproduced against different
    inputs and look identical.
    """
    out: dict[str, object] = {}
    for path in sorted(Path(city.processed).glob("pools_*.json")):
        try:
            spec = json.loads(path.read_text())
        except Exception as exc:                             # noqa: BLE001
            out[path.name] = f"<unreadable: {exc}>"
            continue
        out[path.name] = spec.get("artefact_key", "<absent>")
    return out


def run_forecast(city_slug: str, year: str, draws: int, seed: int):
    city = cityconfig.use(city_slug)
    target = cityconfig.use_target(year)
    M.apply_city(city)
    scenario = M.load_scenario(argparse.Namespace(
        config=None, set=None, draws=draws, seed=seed,
        city=city_slug, target=year))
    return city, target, scenario, M.run_model(target, scenario, DATA,
                                               verbose=False)


def bundle(city_slug: str, year: str, draws: int, seed: int) -> dict:
    city, target, scenario, run = run_forecast(city_slug, year, draws, seed)

    seats = np.array([[d.get(p, 0) for p in run.index] for d in run.seat_draws],
                     dtype=float)
    parties = {}
    for party, i in sorted(run.index.items()):
        col = seats[:, i]
        if col.max() <= 0:
            continue
        parties[party] = {
            "median": float(np.median(col)),
            "mean": round(float(col.mean()), 6),
            "p5": float(np.percentile(col, 5)),
            "p95": float(np.percentile(col, 95)),
        }

    # The full draw matrix is too large to freeze and too important to omit, so
    # its bytes are hashed instead. A changed distribution with an unchanged
    # median is caught here and nowhere else.
    draw_sha = hashlib.sha256(
        np.ascontiguousarray(seats, dtype=np.int64).tobytes()).hexdigest()

    content = {
        "city": city_slug,
        "target": year,
        "council": int(target.council),
        "draws": int(draws),
        "seed": int(seed),
        "parties": parties,
        "seat_draws_sha256": draw_sha,
        "council_sizes": sorted({int(c) for c in run.council_sizes}),
        # CONFIGURATION ONLY — the declared levers, which is what `DEFAULTS`
        # is. The `scenario` dict is not a configuration object: stages inject
        # their OUTPUTS back into it (`theta_prior`, `spine_level`,
        # `poll_levels`, `pool_seeds`, …), and those are float-valued and wobble
        # at ULP level between runs — the parallel summation-order noise of
        # §1.46. Hashing them made the freeze non-reproducible while the seat
        # draws were bit-identical, which would have made this instrument
        # useless on its first day.
        #
        # The intermediate state is not lost: it is downstream of the levers and
        # upstream of `seat_draws_sha256`, both of which ARE hashed, so a change
        # in it that matters shows up in the draws. That the scenario carries
        # both kinds of thing at once is exactly the conflation the restructure
        # separates.
        "scenario": {k: scenario[k] for k in sorted(M.DEFAULTS)
                     if k in scenario},
        "env_switches": resolved_switches(),
        "pool_artefact_keys": pool_artefact_keys(city),
    }
    canonical = json.dumps(content, sort_keys=True, separators=(",", ":"))
    return {
        "content": content,
        "content_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
        "provenance": {
            "git_commit": _git("rev-parse", "HEAD"),
            "git_dirty": bool(_git("status", "--porcelain")),
            "numpy": np.__version__,
            "python": sys.version.split()[0],
        },
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--city", default="joburg")
    ap.add_argument("--target", default="2026")
    ap.add_argument("--draws", type=int, default=1500)
    ap.add_argument("--seed", type=int, default=20261104)
    ap.add_argument("--verify", action="store_true",
                    help="re-run and compare against the committed freeze")
    ap.add_argument("--out", type=Path, default=FROZEN)
    args = ap.parse_args(argv)

    fresh = bundle(args.city, args.target, args.draws, args.seed)

    if not args.verify:
        args.out.write_text(json.dumps(fresh, indent=1, sort_keys=True) + "\n")
        print(f"froze {args.city} {args.target} -> {args.out}")
        print(f"  content_sha256 {fresh['content_sha256']}")
        print(f"  seat_draws_sha256 {fresh['content']['seat_draws_sha256']}")
        for party, v in sorted(fresh["content"]["parties"].items(),
                               key=lambda kv: -kv[1]["median"])[:6]:
            print(f"  {party:6s} median {v['median']:5.0f}  "
                  f"[{v['p5']:.0f}, {v['p95']:.0f}]")
        if fresh["provenance"]["git_dirty"]:
            print("  NOTE: tree is dirty; this freeze is not reproducible from "
                  "a commit alone")
        return 0

    if not args.out.exists():
        print(f"no freeze at {args.out}; run without --verify first")
        return 1
    old = json.loads(args.out.read_text())
    if old["content_sha256"] == fresh["content_sha256"]:
        print(f"VERIFIED — {args.out.name} reproduces exactly "
              f"({fresh['content_sha256'][:16]}…)")
        return 0

    print(f"DRIFT — the forecast no longer reproduces the freeze.\n"
          f"  frozen {old['content_sha256'][:16]}…  "
          f"at {old['provenance']['git_commit'][:9]}\n"
          f"  now    {fresh['content_sha256'][:16]}…  "
          f"at {fresh['provenance']['git_commit'][:9]}")
    a, b = old["content"], fresh["content"]
    for field in sorted(set(a) | set(b)):
        if a.get(field) != b.get(field):
            print(f"  differs: {field}")
    for party in sorted(set(a["parties"]) | set(b["parties"])):
        pa = a["parties"].get(party, {})
        pb = b["parties"].get(party, {})
        if pa.get("median") != pb.get("median"):
            print(f"    {party:6s} median "
                  f"{pa.get('median')} -> {pb.get('median')}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
