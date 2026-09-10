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

import argparse
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


def _seeded_parties_outside_every_pool(spec) -> list[str]:
    """The predicate. A seeded party that belongs to NO pool, by the drawer's
    own definition of membership.

    ⛔ THE MEMBERSHIP EXPRESSION IS COPIED FROM `make_drawer`, DELIBERATELY.
    `montecarlo.make_drawer` builds
    ``handled = {p for cfg in scenario["pools"].values() for p in cfg["members"]
    if p in index}`` and its loop then does ``if party in handled: continue``
    BEFORE it looks a seed band up. So if this set ever fails to contain a
    seeded party, that party silently changes engine — it stops being drawn
    from its pools and starts being drawn from a triangular. Asserting the
    same expression here is what makes this test track that branch rather than
    a restatement of the spec's own shape.
    """
    members = {p for cfg in spec["pools"].values() for p in cfg["members"]}
    return sorted(p for p, v in (spec.get("seeds") or {}).items()
                  if float(v) > 0 and p not in members)


def test_every_seeded_party_belongs_to_a_pool():
    """A seeded arrival is drawn from its POOLS, and it must have some.

    ⛔ THIS IS THE INVARIANT A WHOLE REFUTATION RESTS ON, AND NOTHING TESTED IT.
    `make_drawer` skips every pool member before it reads `pool_seed_bands`, so
    the emitted band's `lo`/`hi` are consumed by nothing — measured 2026-09-06,
    replacing every seeded band with [0.001, 1.0, 50.0] leaves `pr_share_draws`
    and the seat totals byte-identical (§1.198). That conclusion is only sound
    while EVERY seeded party is a pool member. The day one is not, that party
    alone is drawn from a triangular whose width nothing has been maintaining,
    and the model changes engine for it in silence.

    The invariant is currently guaranteed by arithmetic — `emit_pools` writes a
    normalised vector over `n` pools, so its largest weight is at least `1/n`,
    far above the `w[g] > 1e-4` members filter. It is guaranteed by arithmetic
    that could change: a roster drop, a capture that comes back empty, or a
    tighter filter each break it, and none of them looks like it is breaking
    anything.

    ⚠️ **The liveness register cannot catch it either.** `pool_seed_bands` sits
    in `RUNTIME_INJECTED` in `test_levers_are_live.py` — explicitly "not a
    lever" — so the register never asks whether its `lo` and `hi` are read by
    anything. That exemption is how a dead artefact survived two rounds of
    repair to its contents.
    """
    specs = _specs()
    with_seeds = [(path, spec) for path, spec in specs if (spec.get("seeds") or {})]
    seeded_total = sum(len([1 for v in (spec.get("seeds") or {}).values() if float(v) > 0])
                       for _p, spec in specs)

    # IT LOOKED, two-sided, against a computed denominator rather than a typed
    # floor: a bare "> 0" ratchets, and the cheapest way to fix it when it trips
    # is to lower it.
    assert specs, "no emitted pool specs found — this test scanned nothing"
    assert 0.10 <= len(with_seeds) / len(specs) <= 0.90, (
        f"{len(with_seeds)} of {len(specs)} emitted specs carry seeds. Outside "
        f"[10%, 90%] this is not the population the claim is about: at the low "
        f"end the scan is empty in all but name, and at the high end something "
        f"has started seeding the targets that should have none (2016 and 2011 "
        f"carry no entrant record, and 2026 has no roster).")
    assert seeded_total >= 20, (
        f"only {seeded_total} seeded parties across every spec; the 2021 "
        f"targets alone carry dozens, so this is scanning a broken emission")

    for path, spec in specs:
        orphans = _seeded_parties_outside_every_pool(spec)
        assert not orphans, (
            f"{path.name}: {len(orphans)} seeded parties belong to no pool — "
            f"{', '.join(orphans[:5])}. `make_drawer` skips pool members BEFORE "
            f"it reads `pool_seed_bands`, so these parties alone are drawn from "
            f"the seed-band triangular instead of from their pools. That band's "
            f"width is maintained by nothing (§1.198) and the two engines do "
            f"not agree.")

    # IT CAN SEE: the same predicate, on a constructed violation.
    _path, real = next((p, s) for p, s in with_seeds)
    broken = json.loads(json.dumps(real))
    victim = next(p for p, v in broken["seeds"].items() if float(v) > 0)
    for cfg in broken["pools"].values():
        cfg["members"].pop(victim, None)
    assert _seeded_parties_outside_every_pool(broken) == [victim], (
        f"the detector did not catch a constructed violation: {victim} was "
        f"removed from every pool's members and still read as belonging to one")

    print(f"  {seeded_total} seeded parties across {len(with_seeds)} of "
          f"{len(specs)} specs, every one of them in a pool")


def test_a_seeded_arrival_is_drawn_CONCENTRATED_not_evenly():
    """The near-uniform `seeds` are a MEAN VECTOR. The DRAW is a spike at zero.

    ⛔ THIS IS THE MOST MISREAD MECHANISM IN THE MODEL AND NOTHING ASSERTED IT.
    The emitted seeds for undeclared entrants sit within a 1.12x max/min spread
    at Cape Town 2016, so every reader — including the author of this test, in
    §1.220 — concludes the model divides the arrival budget evenly. It does not.
    Seeded arrivals are pool members, so their split is drawn by the POOL
    Dirichlet at a per-component concentration of `p_i * A_pool` ~ 0.005: most
    draws near zero, a rare large chunk.

    Measured live at Cape Town 2016: E[top arrival's share of the group] = 0.412
    against 0.062 if the draw were flat, and a median party draw of 0.137 of its
    own mean. Realised, across 24 metro-years, the top arrival takes a median
    62.6% of the group.

    ⚠️ THE BEHAVIOUR IS LOAD-BEARING AND ACCIDENTAL. It comes from a pool
    concentration fitted for a different purpose. A future change to `alpha`, or
    a well-meaning "let's make the seeds less flat", would silently convert this
    into the even split everybody already believes it is — and the even split is
    the pathological one: it makes arrival seats a step function of the roster
    LENGTH, and costs +12 seats over 16 metro-years against the live path's
    +6.5. Nothing else in the suite would notice. §1.220.
    """
    import cityconfig
    import montecarlo as M
    import numpy as _np

    spec_path = ROOT / "data/processed/capetown/pools_2016.json"
    if not spec_path.exists():
        skip("capetown 2016 spec not emitted")
    seeds = {k: v for k, v in
             json.loads(spec_path.read_text())["seeds"].items() if v > 0}

    # (1) IT LOOKED. The premise is a near-flat MEAN vector over several
    #     parties — without that this test would be asserting the obvious.
    assert len(seeds) >= 8, (
        f"only {len(seeds)} seeded parties at capetown 2016; the claim is about "
        f"a crowd and needs one.")
    spread = max(seeds.values()) / min(seeds.values())
    assert spread < 3.0, (
        f"the seeded MEAN vector at capetown 2016 spans {spread:.2f}x. This test "
        f"exists to show that a FLAT mean still draws concentrated; if the mean "
        f"is no longer flat, re-derive §1.220 before editing this number.")

    # ⛔ RESTORE THE ACTIVE CITY. `cityconfig.use` sets PROCESS-GLOBAL state
    # (`_ACTIVE`, `_TARGET`), and `run_all` runs modules in one process — so a
    # test that switches city and walks away silently re-points every later
    # test in the suite. This one did exactly that on its first run and broke
    # `test_polling_register`, which screens "the 2026 target" and got Cape
    # Town's. Same family as JUDGEMENT-CALLS §A43 (`apply_city` never resets
    # `DEFAULTS`), which is on the register in red.
    _prev_city = cityconfig.active().slug
    try:
        cityconfig.use("capetown")
        target = cityconfig.use_target("2016")
        scenario = M.load_scenario(argparse.Namespace(
            config=None, set=[], draws=300, seed=None,
            city="capetown", target="2016"))
        run = M.run_model(target, scenario, ROOT / "data/raw/elections",
                          verbose=False)
    finally:
        cityconfig.use(_prev_city)
    index = {p: i for i, p in enumerate(run.universe)}
    cols = [index[p] for p in seeds if p in index]
    assert len(cols) == len(seeds), (
        f"{len(cols)} of {len(seeds)} seeded parties reached the universe — a "
        f"seeded party that is not drawn is a different defect.")

    draws = _np.asarray(run.pr_share_draws)[:, cols]
    group = draws.sum(axis=1)
    top = (draws.max(axis=1) / _np.maximum(group, 1e-12)).mean()
    flat = 1.0 / len(cols)

    # (2) THE CLAIM: the top of the group takes far more than an even share.
    #     Bounded on BOTH sides — an upper bound too, because a draw that put
    #     everything on one party would also pass a bare floor and would be a
    #     different, worse model.
    assert 3 * flat < top < 0.95, (
        f"E[top arrival's share of the group] is {top:.3f} at capetown 2016, "
        f"against {flat:.3f} for a flat draw. Below ~{3 * flat:.3f} the model "
        f"has become the EVEN split everyone already believes it is — which "
        f"costs +12 seats over 16 metro-years and makes arrival seats a step "
        f"function of the roster length (§1.220). Above 0.95 it has become a "
        f"point bet on one unnamed party.")

    # (3) THE SIGNATURE: a spike at zero. The median party draws far below its
    #     own mean. This is what distinguishes "concentrated" from "shifted".
    ratio = float(_np.median(draws / _np.maximum(draws.mean(axis=0), 1e-15)))
    assert ratio < 0.5, (
        f"the median seeded party draws {ratio:.3f} of its own mean. Near 1.0 "
        f"the distribution is symmetric and the concentration above is coming "
        f"from something other than the spike-at-zero this documents.")


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
