"""Freeze a stage-1 forecast, and hash everything that could move it.

⛔ **THIS IS NOT A BENCHMARK, AND MUST NEVER BE USED AS ONE.** See `CLAUDE.md`,
"Nothing this model has ever produced is a standard of correctness". A change is
judged by backtesting against **real election results**, never by whether it
still agrees with this file. An earlier version of this docstring, and of the
restructure plan, said the opposite — *"every commit must reproduce the frozen
panel to the seat or be reverted"* — and the owner stopped it on 2026-08-25.

**Why that framing was harmful, not merely wrong.** "Reproduce the old numbers
or revert" makes the current bugs the definition of correct. If a change moves a
number it may have FIXED something: the poll channel was worth −6 and nobody
knew for four days (§1.94), the by-election decay is applied twice, and
`allocate_with_overhang` has no test at all. A rule that reverts any change on
those paths protects the defects.

**What this IS for**, both of which are records rather than judgements:

1. **Accountability.** What we published, and the exact configuration that
   produced it, so the forecast can be held to its own numbers after
   4 November — including the six environment switches that are otherwise
   invisible.
2. **A tripwire.** When something moves that you did not expect to move, this
   says *go and look*. Investigating a surprise is not the same as requiring
   agreement, and the verdict still comes from the backtest.

It also closes a real provenance gap: `data/processed/history.json` records
neither its draw count nor its seed, so on 2026-08-24 it took three separate
panel runs to establish whether a refactor had changed anything or whether the
committed artefact had simply been produced at a different `--draws`.

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
import re
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
    # The seventh switch, added 2026-08-27, and the comment above is exactly
    # why it is here: it was the one input that decided whether this published
    # artefact is bit-reproducible, and it was recorded NOWHERE -- not in
    # `forecast_summary.json`, not in a `--run-dir` dump, not here. Two freezes
    # differing only by it were indistinguishable after the fact, which is the
    # condition `tests/test_freeze.py` describes as how a baseline was measured
    # against the RETIRED sigma without anyone noticing. MODEL-LOG §1.104.
    "PYTHONHASHSEED",
    # The eighth, added 2026-09-06, and it is the seventh's lesson repeated.
    # `levels.HELD_BACK` quarantines the pre-2011 history for seven metros, and
    # `HELD_BACK_OFF=1` empties it at import — `levels.py`'s own comment INVITES
    # that run, so a diagnostic freeze is a legitimate thing to take. Measured:
    # the variable moves `theta_record` from 410 observations to 458 and
    # `local_record` from 292 to 353 across six extra parties, which sets
    # `sd(log θ)` and `sd(log ρ)` — **every band width in the published
    # forecast**. Two freezes differing only in it were indistinguishable in the
    # artefact, which is §1.104's failure exactly. A `gates_sha` was added to
    # `pools.artefact_key` on 2026-09-05 and not carried to this register, the
    # other one of the same class. MODEL-LOG §1.193.
    "HELD_BACK_OFF",
    # The ninth, found by the code→register scan the same day, and arguably the
    # most important of all: `JHB_SCORE_NO_RELABEL=1` withholds the arrival
    # label from the MODEL, which changes what the SCORER IS. Two `history.json`
    # files differing only in it are two different scoreboards, and the
    # difference is worth 40 coherent seats (386 → 426). A freeze that does not
    # say which scorer produced its baseline cannot be compared to another.
    "JHB_SCORE_NO_RELABEL",
)

# Environment variables `src/` reads that deliberately do NOT belong above,
# each with the reason. The guard in `tests/test_freeze.py` scans `src/` and
# requires every read to be either registered or listed here — an exemption
# with a reason, never a silent omission.
ENV_NOT_RECORDED = {
    "POOLS_LOCK_WAIT": "a lock TIMEOUT in seconds. It changes how long a writer "
                       "waits for the artefact lock and can change whether a "
                       "run completes, but it cannot change a number that a "
                       "completed run produces.",
}


def _git(*args: str) -> str:
    try:
        return subprocess.run(("git", *args), cwd=REPO, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:                                        # noqa: BLE001
        return "<unavailable>"


def _dirty_excluding(*ignore: Path) -> bool:
    """Is anything uncommitted, other than the paths named?

    Used to answer "was the CODE clean when this freeze was taken", which is
    not the same question as "is the tree clean now": writing the freeze dirties
    the tree, so the artefact being written must be excluded or a clean freeze
    could never be taken at all.

    Paths are compared repository-relative, which is how git prints them.
    """
    skip = {str(p.resolve().relative_to(REPO)) for p in ignore}
    out = _git("status", "--porcelain")
    if out == "<unavailable>":
        return True                       # cannot tell; assume the worse
    for line in out.splitlines():
        # NOT a fixed-column slice. `_git` strips its output, which eats the
        # leading space of a ' M path' line and shifts every column by one —
        # the first version read "rc/freeze.py" and reported a clean tree
        # dirty. Match the status field instead of counting characters.
        m = re.match(r"^\s*(\S{1,2})\s+(.*)$", line)
        if not m:
            continue
        paths = m.group(2)
        # A rename prints `old -> new`; both sides count.
        for path in (p.strip().strip('"')
                     for p in paths.split(" -> ")):
            if path and path not in skip:
                return True
    return False


def resolved_switches() -> dict[str, object]:
    """What the switches were, as the modules RESOLVED them.

    The raw environment is recorded too, but the resolved value is what the
    model used: `SIGMA_TWO_TERM` unset resolves to True since 2026-08-24, and
    an unset variable reading as its default is exactly the confusion this
    guards against.
    """
    import levels
    import montecarlo
    import polling
    return {
        "raw": {k: os.environ.get(k) for k in ENV_SWITCHES},
        "resolved": {
            # Three states, and only recording both separates them: the seed
            # this build asks for, and whether hash randomisation is actually
            # off in the process that wrote the freeze. `fix_hash_seed` runs
            # from a `__main__` guard, so a freeze produced by an IMPORTING
            # caller can hold the constant while the interpreter never got it.
            "montecarlo.HASH_SEED": str(montecarlo.HASH_SEED),
            "hash_randomization": bool(sys.flags.hash_randomization),
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
            # Whether the CODE that produced this was clean — not whether the
            # artefact it is about to write is present. Writing the freeze
            # dirties the tree, so counting it would make a clean freeze
            # impossible to take: the first version of this check could never
            # pass, which its own test caught immediately.
            "git_dirty": _dirty_excluding(FROZEN),
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
    # The freeze is PUBLISHED. A fixed hash seed is what lets its guarantee
    # be "identical to the last bit" rather than "identical to ~1e-16".
    M.fix_hash_seed()
    raise SystemExit(main())
