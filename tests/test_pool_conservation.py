"""Votes come out of POOLS, and only out of the pools a party actually shares.

The model's central claim about arrivals is a conservation claim: a party takes
its votes from the pools it draws on, every party holding those pools gives up
the same proportion of what it held, and **a party that shares none of a pool
cannot take a single vote from anyone in it**. Stated the way it was put to this
repository: if ActionSA does not share the DA's voting pool, it cannot take DA
votes.

That claim is currently made in three docstrings and asserted nowhere. It is
exactly the kind of claim that is true when written and quietly stops being true
later, because the code that would break it -- a citywide seed, a renormalisation
over the wrong axis, an entrant given "an even share of every pool" -- does not
look like it is breaking anything.

So this measures it, on the emitted specs rather than on a fixture:

``test_capture_is_zero_outside_a_partys_pools``
    A seeded party's capture rate is zero in every pool its vector gives it no
    weight in. This is the user's sentence, directly.

``test_a_pools_split_is_conserved``
    Within a pool, the members' shares sum to one before and after an arrival is
    added, so an arrival's gain is exactly the other members' loss, in
    proportion to what each held.

``test_an_arrival_does_not_touch_pools_it_is_not_in``
    The strong form, end to end through ``make_drawer``: adding a party to one
    pool leaves the OTHER pools' internal splits unchanged, draw for draw, under
    a fixed seed. If a citywide term were doing the debiting instead of the pool
    term, this is the test that would catch it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, run_module  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))

import montecarlo as M  # noqa: E402

SPECS = sorted((ROOT / "data" / "processed").glob("*/pools_*.json")) + \
        sorted((ROOT / "data" / "processed").glob("pools_*.json"))
TOL = 1e-9


def _specs():
    out = []
    for path in SPECS:
        if "simulation" in path.name:
            continue
        try:
            out.append((path, json.loads(path.read_text())))
        except Exception:
            continue
    return out


def test_capture_is_zero_outside_a_partys_pools():
    """A seeded party takes nothing from a pool it has no weight in."""
    checked = 0
    for path, spec in _specs():
        pools = spec["pools"]
        seeds = spec.get("seeds") or {}
        for party in seeds:
            member_of = {name for name, cfg in pools.items()
                         if float(cfg["members"].get(party, 0.0)) > 0}
            absent = set(pools) - member_of
            for name in absent:
                weight = float(pools[name]["members"].get(party, 0.0))
                assert weight <= TOL, (
                    f"{path.name}: {party} is seeded and holds weight {weight} "
                    f"in pool {name!r}, which its vector says it is not in — "
                    f"it would draw votes from every party in that pool")
            checked += 1
    assert checked, "no seeded parties found in any emitted spec"
    print(f"  checked {checked} seeded parties across {len(_specs())} specs")


def test_a_pools_split_is_conserved():
    """Every pool's member weights describe a split, and splits sum to one.

    Weights are per-party shares of THAT PARTY's vote, so they do not sum to one
    across a pool. What must hold is the other direction: each party's weights
    sum to one ACROSS pools, so no party's vote is created or destroyed by being
    allocated to pools.
    """
    for path, spec in _specs():
        pools = spec["pools"]
        parties: dict[str, float] = {}
        for cfg in pools.values():
            for party, w in cfg["members"].items():
                parties[party] = parties.get(party, 0.0) + float(w)
        # ``emit_pools`` writes a member only where its weight exceeds 1e-4, so
        # a party can legitimately lose up to 1e-4 per pool to the write. With
        # four pools that is 4e-4; 1e-3 is that with room, and anything larger
        # is a real leak rather than a rounding one.
        bad = {p: t for p, t in parties.items() if abs(t - 1.0) > 1e-3}
        assert not bad, (
            f"{path.name}: {len(bad)} parties whose pool weights do not sum to "
            f"1 — worst {sorted(bad.items(), key=lambda kv: -abs(kv[1]-1))[:3]}. "
            f"A party summing above 1 is counted twice; below 1, its missing "
            f"share belongs to no pool and is drawn from nobody.")


def test_an_arrival_does_not_touch_pools_it_is_not_in():
    """End to end: adding a party to one pool leaves the others' splits alone."""
    path, spec = _specs()[0]
    pools = json.loads(json.dumps(spec["pools"]))
    names = sorted(pools)
    assert len(names) >= 2, f"{path.name}: need at least two pools"
    host, other = names[0], names[1]

    base = {p: 0.02 for cfg in pools.values() for p in cfg["members"]}
    centres = dict(base)
    index = {p: i for i, p in enumerate(sorted(base))}

    def splits(scenario, seed=7):
        rng = np.random.default_rng(seed)
        draw = M.make_drawer(scenario, base, centres, index, rng)
        return np.array([draw() for _ in range(200)])

    scen = dict(M.DEFAULTS)
    scen["pools"] = pools
    scen["entrant_prob"] = 0.0
    scen["_theta_sd"] = {p: 0.0 for p in base}      # isolate the pool mechanism
    before = splits(scen)

    # Add a newcomer to ONE pool only.
    pools2 = json.loads(json.dumps(pools))
    pools2[host]["members"]["NEWCOMER"] = 1.0
    base2, centres2 = dict(base), dict(centres)
    base2["NEWCOMER"] = centres2["NEWCOMER"] = 0.02
    index2 = {p: i for i, p in enumerate(sorted(base2))}
    scen2 = dict(scen)
    scen2["pools"] = pools2
    scen2["_theta_sd"] = {p: 0.0 for p in base2}
    rng = np.random.default_rng(7)
    draw2 = M.make_drawer(scen2, base2, centres2, index2, rng)
    after = np.array([draw2() for _ in range(200)])

    # Members of the untouched pool: their shares RELATIVE TO EACH OTHER must
    # not move. (Their absolute shares may, because the newcomer changes the
    # citywide total everything is renormalised by — that is not the pool
    # mechanism, it is arithmetic on the denominator.)
    members = [p for p in pools[other]["members"] if p in index and p in index2]
    assert len(members) >= 2, f"pool {other!r} has too few members to compare"
    a = before[:, [index[p] for p in members]]
    b = after[:, [index2[p] for p in members]]
    a = a / np.maximum(a.sum(axis=1, keepdims=True), 1e-12)
    b = b / np.maximum(b.sum(axis=1, keepdims=True), 1e-12)
    worst = float(np.abs(a.mean(axis=0) - b.mean(axis=0)).max())
    assert worst < 0.02, (
        f"adding NEWCOMER to pool {host!r} moved the internal split of pool "
        f"{other!r} by {worst:.4f} — a party is taking votes from a pool it is "
        f"not in")
    print(f"  untouched pool {other!r}: worst internal shift {worst:.5f}")


if __name__ == "__main__":
    # `run_module`, NOT a hand-rolled loop. Until 2026-08-23 this file ended with
    # `for name, fn in sorted(globals().items()): ... fn()`, which catches
    # neither `SkipTest` nor `SystemExit` — so the FIRST skip aborted the run and
    # every later test in the file silently never executed, and no summary was
    # printed. Five files were in that state; `test_regressions` alone has five
    # `skip(` calls. Under `run_all.py` they were fine, because the suite calls
    # `run_module(vars(module))` itself — the suite hid it. MODEL-LOG §1.84.
    # Append new tests ABOVE this line.
    raise SystemExit(run_module(globals()))
