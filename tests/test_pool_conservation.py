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
    A party takes nothing from a pool it holds no weight in — asserted on the
    DRAW, against a Monte Carlo noise floor measured inside the test, with the
    absence CONSTRUCTED because the emitted specs contain no seeded instance of
    it. This is the user's sentence, directly.

``test_a_pools_split_is_conserved``
    Each party's pool weights sum to one ACROSS pools, so no party's vote is
    created or destroyed by being allocated to pools.

``test_an_arrival_does_not_touch_pools_it_is_not_in``
    The arrival form: a party added to one pool is given a column in that pool's
    draw and in NO other, so every other pool contributes exactly zero of its
    votes. ⚠️ It used to assert this on the drawn means instead, against a typed
    tolerance that sat BELOW its own Monte Carlo noise floor and whose positive
    case never separated — see its docstring and §1.234.

⛔ **THE SPEC POPULATION IS STATED AND ASSERTED IN ONE PLACE**, :func:`_population`,
and every test here that scans the emitted specs goes through it. Its
denominator is the city-years ``cities/*.toml`` declares — not the files on
disk, and not a number typed into a document: ``POOLS-REEMIT-QUEUE.md`` step 3
carried a typed spec count, it went stale, and it sent an operator hunting a
discrepancy that did not exist.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
# ``skip`` was used at the bottom of this file and never imported, so the one
# deliberate skip in it raised NameError and `run_module` reported FAIL with a
# message that said nothing about the missing Cape Town spec.
from _support import (ROOT, declared_city_years, run_module,  # noqa: E402
                      scanned, skip)

sys.path.insert(0, str(ROOT / "src"))

import cityconfig  # noqa: E402
import montecarlo as M  # noqa: E402

SPECS = sorted((ROOT / "data" / "processed").glob("*/pools_*.json")) + \
        sorted((ROOT / "data" / "processed").glob("pools_*.json"))
TOL = 1e-9

# The constructed-capture measurement below. 400 draws is what it takes for the
# Monte Carlo noise floor to sit an order of magnitude under the signal on the
# pool a party DOES hold; three seeds because one measurement of a mean over a
# Dirichlet is one measurement (MODEL-LOG: a threshold sweep inverted an F46
# conclusion, and a 1-seat move came from a 0.002pp change).
DRAWS = 400
SEEDS = (7, 19, 31)

_PROCESSED_DIRS: dict = {}


def _specs():
    """Every emitted pool spec, parsed. **A PARSE ERROR NOW RAISES.**

    It used to be ``except Exception: continue``, which is the worst available
    behaviour for a scan: a spec that became unparseable left the population in
    silence, and every test over it got *quieter* rather than redder. Together
    with ``test_a_pools_split_is_conserved`` having no non-empty assertion at
    all, a checkout with no emitted specs passed both of them.
    """
    return [(path, json.loads(path.read_text()))
            for path in SPECS if "simulation" not in path.name]


def _spec_city_year(path: Path) -> tuple:
    """``(slug, year)`` for an emitted spec, via ``cityconfig``'s directory map.

    Johannesburg's specs sit in ``data/processed/`` rather than
    ``data/processed/joburg/`` (``legacy_processed_root``), so the slug cannot
    be read off the parent directory name. ``City.processed`` is the production
    definition of where a city's artefacts live and is used here rather than a
    second copy of that rule living in the tests.
    """
    if not _PROCESSED_DIRS:
        for toml_path in sorted(cityconfig.CITIES_DIR.glob("*.toml")):
            _PROCESSED_DIRS[cityconfig.load(toml_path.stem).processed.resolve()] \
                = toml_path.stem
    slug = _PROCESSED_DIRS.get(path.parent.resolve())
    assert slug is not None, (
        f"{path} sits in {path.parent}, which is no city's `processed` "
        f"directory. Either a city was added without a config or a spec was "
        f"written where nothing reads it — an un-namespaced output is how a "
        f"Tshwane run could reach Johannesburg's forecast.")
    return slug, path.stem.split("_")[1]


def _population():
    """The spec population, STATED AND ASSERTED — CLAUDE.md §4 requirements 0
    and 1, in one place, for every test in this file that scans the specs.

    Bidirectional, because a containment checked in one direction only is §4's
    "worst record of the four":

    * every declared backtest city-year HAS a spec — the direction that catches
      a lost or unparseable one *exactly*, where a ratio cannot: with two
      forward specs in the population, losing one backtest spec still leaves the
      ratio above any floor worth writing;
    * every spec that is NOT a declared backtest city-year is that city's own
      forward target, so nothing unexpected has been swept in.
    """
    specs = _specs()
    declared = declared_city_years()
    on_disk = {_spec_city_year(path) for path, _ in specs}

    missing = sorted(declared - on_disk)
    assert not missing, (
        f"{len(missing)} city-years are declared in cities/*.toml and have no "
        f"emitted pool spec — {missing[:5]}. Every test in this file scans the "
        f"specs, so this is a scan that has lost part of its population and "
        f"would otherwise report the loss as a pass. Re-emit: "
        f"POOLS-REEMIT-QUEUE.md step 2.")

    forward = sorted(on_disk - declared)
    unexpected = [(slug, year) for slug, year in forward
                  if year != cityconfig.load(slug).default_target]
    assert not unexpected, (
        f"{unexpected}: emitted specs for city-years that are neither a "
        f"declared backtest target nor that city's own forward target. The "
        f"population is no longer the one these tests make claims about.")

    scanned(specs, of=declared, low=1.0, high=1.5,
            what="emitted pool specs (simulation specs excluded)",
            denominator="backtest city-years declared by cities/*.toml "
                        "[structure.by_year]")
    return specs


def test_capture_is_zero_outside_a_partys_pools():
    """A party takes ZERO from a pool it holds no weight in — ON THE DRAW.

    ⛔ **WHAT STOOD HERE UNTIL 2026-09-14 COULD NOT FAIL, AND ITS LOOP BODY
    NEVER RAN.** It built ``absent`` as the pools where ``weight > 0`` is false
    and then asserted ``weight <= 1e-9`` for each of them — ``x <= 0`` implies
    ``x <= 1e-9`` for any non-NaN weight, so the only thing it could catch was a
    NaN. It could not catch that either: measured across every emitted spec on
    2026-09-14, the number of (seeded party, pool) pairs where the party holds
    no weight was **zero**, because ``pools.balance_within_bounds`` seeds every
    zeroed cell — so ``absent`` was empty and the loop executed not once. Its
    stated claim is about CAPTURE and it computed no capture quantity anywhere.

    That is §4 requirement 3 twice over: the premise was an observed state of a
    derived artefact, and it had already expired. So the absence is
    **constructed**, and the claim is asserted **on the draw**, through the real
    ``make_drawer``.

    **The instrument is a lever and a noise floor.** Take a real emitted spec,
    remove one party ``X`` from one pool ``G`` it really belongs to —
    renormalising its remaining weights, so ``test_a_pools_split_is_conserved``
    would still hold of the fixture — then pull ``X``'s own level lever, its
    centre, and watch two pools:

    * ``G``, which ``X`` no longer holds: its internal split must not move by
      more than Monte Carlo noise;
    * ``H``, the pool ``X`` holds most of: its internal split must move by
      several times that noise, or the lever is not connected and "``G`` did not
      move" is worth nothing.

    ⛔ **THE NOISE FLOOR IS MEASURED, NOT TYPED.** It is the same comparison run
    at a different RNG seed with the centres unchanged, so it moves with the
    draw count and with the spec instead of being a number somebody once chose.
    A typed tolerance on this quantity is how
    ``test_an_arrival_does_not_touch_pools_it_is_not_in`` came to pass at 0.0193
    against a hard 0.02 — 96% of its own threshold, and nothing says so.

    ⚠️ **THE CLAIM IS NOT "POOL G IS FROZEN".** ``pool_spec`` imposes both
    margins by IPF, so lifting ``X``'s centre does perturb ``G`` slightly,
    through members the two pools share: ``G``'s voters still all vote, and a
    member squeezed out of ``H`` must make its citywide level up somewhere.
    That residual is the party margin, not capture. What is exactly zero is
    ``X``'s own take — ``pool_spec`` gives ``X`` no column in ``G``'s draw at
    all, so ``G`` contributes exactly nothing to it in every draw, and that is
    asserted separately and exactly.

    ⛔ **AND THE DETECTOR GOES QUIET WHEN THE VIOLATION IS REVERTED.** Put ``X``
    back into ``G`` — the spec exactly as emitted — and the identical
    measurement must show ``G``'s split moving several times the noise floor.
    If it did not, this fixture could not see the thing it is quiet about.
    """
    specs = _population()

    # (0) THE POPULATION OF THE CLAIM, on live state and two-sided. Every
    #     (party, pool) pair where the party holds no weight is a pair the
    #     production `pool_spec` must give no column to — a column is a claim on
    #     that pool's voters, because every vote the pool casts is split among
    #     the parties in that list. Counted as a fraction of ALL (party, pool)
    #     pairs, so neither an emission that stopped producing zeros nor one
    #     that produced nothing else reads as a pass.
    absent_pairs = total_pairs = seeded_absent = 0
    with contextlib.redirect_stdout(io.StringIO()):     # pool_spec narrates
        for path, spec in specs:
            pools = spec["pools"]
            parties = sorted({p for cfg in pools.values() for p in cfg["members"]})
            index = {p: i for i, p in enumerate(parties)}
            drawn = M.pool_spec({"pools": pools}, {p: 0.02 for p in parties},
                                index, {})
            columns = {name: set(block[5]) for name, block in drawn.items()}
            seeds = {p for p, v in (spec.get("seeds") or {}).items()
                     if float(v) > 0}
            for name, cfg in pools.items():
                for party in parties:
                    total_pairs += 1
                    if float(cfg["members"].get(party, 0.0)) > 0:
                        continue
                    absent_pairs += 1
                    seeded_absent += party in seeds
                    assert party not in columns.get(name, ()), (
                        f"{path.name}: {party} holds no weight in pool {name!r} "
                        f"and `montecarlo.pool_spec` still gave it a column in "
                        f"that pool's draw.")
    scanned(absent_pairs, of=total_pairs, low=0.02, high=0.60,
            what="(party, pool) pairs where the party holds no weight",
            denominator="(party, pool) pairs across every emitted spec")

    # (1) THE FIXTURE, constructed on a real spec.
    spec_path = ROOT / "data" / "processed" / "pools_2021.json"
    if not spec_path.exists():
        skip(f"{spec_path} is not emitted; run "
             f"src/pools.py --city joburg --target 2021 --emit")
    pools = json.loads(spec_path.read_text())["pools"]
    parties = sorted({p for cfg in pools.values() for p in cfg["members"]})
    index = {p: i for i, p in enumerate(parties)}
    base = {p: 0.02 for p in parties}

    # X is the most genuinely TWO-POOL party in the spec — the one whose
    # second-largest weight is largest. Chosen by a stated rule rather than by
    # name, so the fixture is not a party that happened to give a good answer,
    # and the rule's premise is asserted: a party with one pool cannot be
    # stripped of one, and a party with a negligible second pool is not changed
    # by losing it.
    def second_weight(party):
        w = sorted((float(cfg["members"].get(party, 0.0))
                    for cfg in pools.values()), reverse=True)
        return w[1] if len(w) > 1 else 0.0

    X = max(parties, key=second_weight)
    weights = {name: float(pools[name]["members"].get(X, 0.0)) for name in pools}
    H = max(weights, key=weights.get)
    G = sorted(weights, key=weights.get, reverse=True)[1]
    assert weights[G] > 0.05 and weights[H] > 0.05, (
        f"the fixture strips {X} of a pool it is meant really to draw on, and "
        f"its weights are {weights}. With nothing substantial in {G!r} the "
        f"strip is not a change and the contrast below measures nothing.")

    def without_X_in_G():
        pl = json.loads(json.dumps(pools))
        pl[G]["members"].pop(X, None)
        total = sum(float(pl[name]["members"].get(X, 0.0)) for name in pl)
        for name in pl:
            if X in pl[name]["members"]:
                pl[name]["members"][X] = float(pl[name]["members"][X]) / total
        return pl

    def draw_means(pl, centres, seed):
        scen = dict(M.DEFAULTS)
        scen["pools"] = pl
        scen["entrant_prob"] = 0.0
        scen["_theta_sd"] = {p: 0.0 for p in parties}   # isolate the pool term
        draw = M.make_drawer(scen, base, centres, index,
                             np.random.default_rng(seed))
        return np.array([draw() for _ in range(DRAWS)])

    def internal_shift(pl, A, B, pool):
        """How far a pool's members' shares OF EACH OTHER moved between two runs.

        Relative, not absolute: a newcomer or a level change moves the citywide
        total everything is renormalised by, which is arithmetic on the
        denominator and not the pool mechanism.
        """
        members = [p for p in pl[pool]["members"] if p in index]
        a = A[:, [index[p] for p in members]]
        b = B[:, [index[p] for p in members]]
        a = a / np.maximum(a.sum(axis=1, keepdims=True), 1e-12)
        b = b / np.maximum(b.sum(axis=1, keepdims=True), 1e-12)
        return float(np.abs(a.mean(axis=0) - b.mean(axis=0)).max())

    lifted = dict(base)
    lifted[X] = base[X] * 3.0

    def measure(pl):
        """``(shift in G, shift in H, noise floor)``, averaged over ``SEEDS``."""
        g, h, noise = [], [], []
        with contextlib.redirect_stdout(io.StringIO()):
            for seed in SEEDS:
                A = draw_means(pl, base, seed)
                B = draw_means(pl, lifted, seed)
                C = draw_means(pl, base, seed + 1000)
                g.append(internal_shift(pl, A, B, G))
                h.append(internal_shift(pl, A, B, H))
                noise.append(max(internal_shift(pl, A, C, G),
                                 internal_shift(pl, A, C, H)))
        return float(np.mean(g)), float(np.mean(h)), float(np.mean(noise))

    # (2) THE EXACT HALF: no column, so a take of exactly zero in every draw.
    stripped = without_X_in_G()
    with contextlib.redirect_stdout(io.StringIO()):
        drawn = M.pool_spec({"pools": stripped}, base, index, {})
    assert X not in drawn[G][5] and index[X] not in drawn[G][0], (
        f"{X} was removed from pool {G!r} and `pool_spec` still lists it among "
        f"that pool's draw columns. Pool {G!r}'s votes are split across exactly "
        f"those columns, so {X} would be taking votes from every other member "
        f"of a pool it holds no weight in.")
    assert X in drawn[H][5], (
        f"precondition: {X} must still hold pool {H!r} after the strip, or the "
        f"lever below has nothing to pull")

    # (3) THE DRAWN HALF, bidirectional and against a measured noise floor.
    g_out, h_out, noise_out = measure(stripped)
    assert g_out <= 2.0 * noise_out, (
        f"tripling {X}'s centre moved pool {G!r}'s internal split by {g_out:.5f} "
        f"against a Monte Carlo noise floor of {noise_out:.5f}. {X} holds no "
        f"weight in {G!r}: a move this far above noise means it is reaching "
        f"voters it does not share — a citywide term doing the debiting, or a "
        f"renormalisation over the wrong axis.")
    assert h_out >= 4.0 * noise_out, (
        f"tripling {X}'s centre moved pool {H!r}'s split by only {h_out:.5f} "
        f"against a noise floor of {noise_out:.5f}. The lever is not connected, "
        f"so the quiet on {G!r} above is evidence of nothing at all.")
    assert h_out >= 5.0 * g_out, (
        f"{X}'s level moved the pool it holds ({H!r}, {h_out:.5f}) barely more "
        f"than the pool it does not ({G!r}, {g_out:.5f}). Capture is not "
        f"confined to a party's own pools.")

    # (4) ⛔ CAN IT SEE, AND DOES IT GO QUIET AGAIN? The same measurement on the
    #     spec exactly as emitted, where X IS a member of G.
    g_in, h_in, noise_in = measure(pools)
    assert g_in >= 4.0 * noise_in, (
        f"with {X} restored to pool {G!r}, tripling its centre moved that "
        f"pool's split by {g_in:.5f} against a noise floor of {noise_in:.5f}. "
        f"The detector cannot see a party that IS in a pool taking votes from "
        f"it, so it proves nothing when it is quiet about one that is not.")
    assert g_in >= 4.0 * g_out, (
        f"membership made almost no difference to {X}'s reach into {G!r}: "
        f"{g_in:.5f} as a member against {g_out:.5f} as a non-member. The two "
        f"states are indistinguishable and this test separates nothing.")
    print(f"  {absent_pairs} of {total_pairs} (party, pool) pairs hold no "
          f"weight ({seeded_absent} of them seeded); {X} stripped of {G!r}: "
          f"shift {g_out:.5f} vs noise {noise_out:.5f} there and {h_out:.5f} "
          f"in {H!r}; restored, {g_in:.5f}")


def test_a_pools_split_is_conserved():
    """Every pool's member weights describe a split, and splits sum to one.

    Weights are per-party shares of THAT PARTY's vote, so they do not sum to one
    across a pool. What must hold is the other direction: each party's weights
    sum to one ACROSS pools, so no party's vote is created or destroyed by being
    allocated to pools.

    ⛔ **UNTIL 2026-09-14 THIS PASSED ON AN EMPTY POPULATION.** ``for path, spec
    in _specs():`` over an empty list is a pass, and that is the state of any
    checkout with no emitted specs — ``data/**`` is gitignored, so it is also
    the state of a fresh clone. Worse, ``_specs`` swallowed parse errors, so a
    spec that became unparseable left the population and the test got *quieter*
    rather than redder. It was the only scan in this file with no non-empty
    assertion; ``test_capture_is_zero_outside_a_partys_pools`` guarded the same
    thing four lines away. Both now go through :func:`_population`.
    """
    specs = _population()
    checked = 0
    for path, spec in specs:
        pools = spec["pools"]
        parties: dict[str, float] = {}
        for cfg in pools.values():
            for party, w in cfg["members"].items():
                parties[party] = parties.get(party, 0.0) + float(w)
        assert parties, (
            f"{path.name}: no party appears in any of its {len(pools)} pools, "
            f"so this spec contributes nothing and the emptiness asserted "
            f"below is vacuous for it.")
        checked += len(parties)
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
    print(f"  {checked} party weight vectors across {len(specs)} specs sum to 1")


def test_an_arrival_does_not_touch_pools_it_is_not_in():
    """An arrival draws from the pool it joins and from no other.

    ⛔ **WHAT STOOD HERE UNTIL 2026-09-14 WAS A SEED LOTTERY MEASURING NOISE,
    AND ITS POSITIVE CASE WAS NEVER RESOLVABLE AT ALL.** It added a NEWCOMER to
    one pool and asserted that the OTHER pool's members' shares of each other
    moved by less than a typed ``0.02``. Three things were wrong with it and
    each was measured rather than argued (§1.234):

    * it passed at **0.01931**, 97% of its own threshold;
    * the Monte Carlo noise floor of that statistic — the same scenario at a
      different RNG seed, nothing else changed — is **0.0226 to 0.0261** at 200
      draws on this spec. **The threshold was BELOW the noise**, so whether it
      passed was decided by the seed;
    * and the positive case never separated. Adding the newcomer **into** the
      pool being watched moves that pool's split by the same amount as adding it
      to a different pool — ``into/away`` measured **0.91 to 1.26** across two
      specs at 400 and 1500 draws, both at ~1x noise. Pairwise correlation does
      not separate them either (NEWCOMER placed in Black African correlates
      −0.133 with that pool's members and −0.135 with the other pool's).

    **WHY, and it is a fact about the model rather than about the test.**
    ``pool_spec`` imposes BOTH margins by IPF. Every party in this fixture
    carries the same flat centre, so adding a newcomer moves every incumbent's
    party margin by the same proportional amount whichever pool it joins — and
    IPF then lands on the matrix closest in KL to the starting one subject to
    those margins. With a FLAT centre vector, pool membership is very nearly
    unobservable in the drawn means. Its docstring claimed "if a citywide term
    were doing the debiting instead of the pool term, this is the test that
    would catch it"; it would have caught neither.

    **The lever that IS resolvable is a party's own CENTRE**, because that makes
    one party's margin differ and forces IPF to source the difference from the
    pools that party actually holds. That is
    ``test_capture_is_zero_outside_a_partys_pools`` above: 7.9x the noise floor
    on a pool the party holds, 0.7x on one it does not.

    So this keeps the ARRIVAL scenario — which is the one the model's central
    claim is about — and asserts the part of it that is exact rather than the
    part that is noise: an arrival added to one pool is given a column in that
    pool's draw and **in no other**, so every other pool contributes exactly
    zero of its votes in every draw. Constructed, bidirectional, and the
    detector is shown to move when the newcomer is placed elsewhere.
    """
    path, spec = _population()[0]
    pools = json.loads(json.dumps(spec["pools"]))
    names = sorted(pools)
    assert len(names) >= 2, f"{path.name}: need at least two pools"
    host, other = names[0], names[1]

    base = {p: 0.02 for cfg in pools.values() for p in cfg["members"]}
    assert "NEWCOMER" not in base, "the fixture's name is taken by a real party"

    def joined(pool):
        """The spec with a NEWCOMER added to exactly one pool, drawn for real."""
        pl = json.loads(json.dumps(pools))
        pl[pool]["members"]["NEWCOMER"] = 1.0
        centres = dict(base)
        centres["NEWCOMER"] = 0.02
        index = {p: i for i, p in enumerate(sorted(centres))}
        with contextlib.redirect_stdout(io.StringIO()):
            drawn = M.pool_spec({"pools": pl}, centres, index, {})
        return pl, centres, index, drawn

    # (1) THE EXACT CLAIM, through production `pool_spec`: one column, in one
    #     pool. Every vote a pool casts is split across the parties in its
    #     column list, so a column anywhere else is a claim on those voters.
    _pl, centres, index, drawn = joined(host)
    assert "NEWCOMER" in drawn[host][5], (
        f"{path.name}: NEWCOMER was added to pool {host!r} with weight 1.0 and "
        f"`pool_spec` gave it no column there, so it draws nothing from the "
        f"one pool it belongs to and the test below is about nothing.")
    assert index["NEWCOMER"] in drawn[host][0], drawn[host][0]
    elsewhere = sorted(n for n in drawn if n != host
                       and "NEWCOMER" in drawn[n][5])
    assert not elsewhere, (
        f"{path.name}: NEWCOMER holds weight in pool {host!r} alone and "
        f"`pool_spec` gave it a column in {elsewhere} as well. It would be "
        f"taking votes from every member of a pool it does not share — the "
        f"'ActionSA cannot take DA votes unless it shares the DA's pool' claim "
        f"this module exists to assert.")

    # (2) ⛔ CAN THE DETECTOR SEE, AND DOES IT GO QUIET? Put the newcomer in the
    #     OTHER pool instead: the column must move with it, both ways.
    _pl2, _c2, _i2, moved = joined(other)
    assert "NEWCOMER" in moved[other][5], moved[other][5]
    assert "NEWCOMER" not in moved[host][5], (
        f"NEWCOMER was placed in {other!r} and still has a column in {host!r}. "
        f"The column list does not follow the weight vector, so assertion (1) "
        f"above would have been satisfied by a `pool_spec` that gives every "
        f"party a column everywhere.")

    # (3) AND IT IS ACTUALLY DRAWN — otherwise "it takes nothing from `other`"
    #     is true of a party that takes nothing from anywhere. End to end
    #     through `make_drawer`, on the same constructed spec.
    scen = dict(M.DEFAULTS)
    scen["pools"] = _pl
    scen["entrant_prob"] = 0.0
    scen["_theta_sd"] = {p: 0.0 for p in centres}
    with contextlib.redirect_stdout(io.StringIO()):
        draw = M.make_drawer(scen, centres, centres, index,
                             np.random.default_rng(7))
        sample = np.array([draw() for _ in range(200)])
    share = float(sample[:, index["NEWCOMER"]].mean())
    even = 1.0 / len(centres)
    assert 0.2 * even < share < 5.0 * even, (
        f"NEWCOMER drew a mean citywide share of {share:.5f} against {even:.5f} "
        f"for an even split of the ballot. Outside [0.2x, 5x] it is not being "
        f"drawn from its pool at all, and the column assertions above are "
        f"true of a party nobody is counting.")
    print(f"  NEWCOMER in {host!r} only: columns {sorted(n for n in drawn if 'NEWCOMER' in drawn[n][5])}, "
          f"drawn share {share:.5f} vs {even:.5f} even")


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
    specs = _population()
    with_seeds = [(path, spec) for path, spec in specs if (spec.get("seeds") or {})]
    seeded_total = sum(len([1 for v in (spec.get("seeds") or {}).values() if float(v) > 0])
                       for _p, spec in specs)

    # IT LOOKED, two-sided, against a computed denominator rather than a typed
    # floor: a bare "> 0" ratchets, and the cheapest way to fix it when it trips
    # is to lower it.
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
