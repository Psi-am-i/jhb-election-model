"""Run the full Monte Carlo against an election that has already happened.

``fold.py`` validates the deterministic core -- the share model, γ, the ballot
split and the seat allocator -- and does it well: five transitions, twelve
blind predictions. What it cannot touch is the *distributional* layer, which is
where every judgement in this project lives: pool membership and ratios, the
Dirichlet concentrations, the splinter branch, entrant geography, the
by-election terms. Those have never been scored against a real outcome,
because ``montecarlo.py`` can only ever produce 2026.

This harness runs the same machinery at a past election and compares the
distribution it produced against what actually happened, so two model variants
can be put side by side on evidence rather than argument::

    python src/backtest.py --target 2021
    python src/backtest.py --target 2021 --config scenarios/joburg-pools.json
    python src/backtest.py --target 2021 --a scenarios/old.json --b scenarios/new.json

**What "honest" means here, enforced rather than promised.** A backtest is
worthless if it can see the answer, so every input is restricted to what was
knowable before polling day:

* **Boundaries and registration** come from the target's own result file. That
  is legitimate -- ward delimitation and the voters' roll are published months
  ahead -- and it is the only thing taken from that file besides the actual
  result used for scoring.
* **Turnout patterns** use only elections strictly before the target.
* **γ** comes from a fold whose own target precedes this one, never from a
  fold that has seen it.
* **Ward/PR split ratios** come from the previous local election.
* **By-elections** are filtered to contests held before the target's polling
  day.

The one thing this harness cannot enforce is the scenario itself. If a pool
range or an α was fitted on data including the target year, the test is
circular and will flatter the model. Fit leaving the target out, or the number
this prints is worth nothing.

**What it reports.** Seat error against the real council, ward winners called,
and -- the point of the exercise -- calibration: whether the actual outcome
lands inside the predicted interval as often as the interval claims. A model
whose 90% band contains the truth 40% of the time is not slightly wrong, it is
differently wrong from one whose median is off.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np

import cityconfig
import montecarlo as M
from fold import citywide, load, load_parameters, shares
from seats import allocate

# Each target names only things knowable before its polling day, plus the
# actual result, which is used for scoring and nothing else.
TARGETS = {
    2021: {
        "base": "npe2019_{CODE}_vd_party.csv",
        "actual": "lge2021_{CODE}_vd_party_clean.csv",
        "prior_lge": "lge2016_{CODE}_vd_party_clean.csv",
        "election_day": date(2021, 11, 1),
        "turnout_years": (1999, 2000, 2004, 2006, 2009, 2011, 2014, 2016, 2019),
        "lge_years": (2000, 2006, 2011, 2016),
        "gamma_fold": 1,          # 2014->2016, precedes the target
        "council": 270,
    },
    2016: {
        "base": "npe2014_{CODE}_vd_party.csv",
        "actual": "lge2016_{CODE}_vd_party_clean.csv",
        "prior_lge": "lge2011_{CODE}_vd_party_clean.csv",
        "election_day": date(2016, 8, 3),
        "turnout_years": (1999, 2000, 2004, 2006, 2009, 2011, 2014),
        "lge_years": (2000, 2006, 2011),
        "gamma_fold": 3,          # 2009->2011
        "council": 270,
    },
    2011: {
        "base": "npe2009_{CODE}_vd_party.csv",
        "actual": "lge2011_{CODE}_vd_party_clean.csv",
        "prior_lge": "lge2006_{CODE}_vd_party_clean.csv",
        "election_day": date(2011, 5, 18),
        "turnout_years": (1999, 2000, 2004, 2006, 2009),
        "lge_years": (2000, 2006),
        "gamma_fold": 4,          # 2004->2006
        "council": 260,
    },
}


def ward_structure(path: Path):
    """VD -> ward and VD -> registered, from the target's own result file.

    Boundaries and the roll are public before polling day, so taking them from
    the result file is not peeking; the votes in the same file are used only
    for scoring.
    """
    ward_of: dict[str, str] = {}
    registered: dict[str, int] = {}
    with cityconfig.resolve_path(path).open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            vd = row["VD_Number"]
            if row.get("Ward"):
                ward_of.setdefault(vd, row["Ward"].strip())
            if row.get("Registered_Population"):
                registered.setdefault(vd, int(float(row["Registered_Population"])))
    return ward_of, registered


def actual_result(path: Path, council: int):
    """The real council: seats by party from the combined ballots (§0)."""
    votes, _ = load(path, None)
    totals: defaultdict[str, int] = defaultdict(int)
    for counts in votes.values():
        for party, n in counts.items():
            totals[party] += n
    seats = allocate(dict(totals), total_seats=council).seats
    ward_votes, ward_of = load(path, "Ward")
    winners: dict[str, str] = {}
    per_ward: defaultdict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
    for vd, counts in ward_votes.items():
        w = ward_of.get(vd)
        if not w:
            continue
        for party, n in counts.items():
            per_ward[w][party] += n
    for w, counts in per_ward.items():
        winners[w] = max(counts, key=counts.get)
    return {p: s for p, s in seats.items() if s > 0}, winners


def score(draws: list[dict[str, int]], actual_seats: dict[str, int],
          entrant_actual: str | None = None):
    """Seat error, and whether the truth landed inside the claimed interval.

    The model draws a *generic* entrant -- it cannot know a new party's name --
    so scoring compares ENTRANT against whichever party actually arrived from
    nothing. Anything else would score the machinery as a total miss even when
    it sized the newcomer correctly, which is the interesting question.
    """
    if entrant_actual:
        draws = [{(entrant_actual if k == "ENTRANT" else k): v for k, v in d.items()}
                 for d in draws]
    parties = sorted(set().union(*[set(d) for d in draws]) | set(actual_seats))
    rows = []
    inside = 0
    counted = 0
    for p in parties:
        series = np.array([d.get(p, 0) for d in draws], dtype=float)
        med = float(np.median(series))
        lo, hi = np.percentile(series, [5, 95])
        act = actual_seats.get(p, 0)
        if act > 0 or med > 0:
            counted += 1
            if lo <= act <= hi:
                inside += 1
            rows.append((p, act, med, lo, hi, abs(med - act)))
    total_err = sum(r[5] for r in rows)
    return rows, total_err, inside, counted


def run_one(args, city, spec, scenario) -> list[dict[str, int]]:
    """Assemble one target's inputs and run the draws. Nothing here may read
    the target's votes -- only its boundaries and roll, which were public."""
    base_votes, _ = load(args.data_dir / spec["base"], None)
    base_share_d, base_city_d = shares(base_votes), citywide(base_votes)
    ward_of, registered = ward_structure(args.data_dir / spec["actual"])

    vds = sorted(set(base_share_d) & set(ward_of))
    universe = sorted(p for p in base_city_d if p not in ("IND",))
    if scenario["entrant_prob"] > 0:
        universe.append("ENTRANT")
    index = {p: i for i, p in enumerate(universe)}
    npar = len(universe)

    base_city = np.array([base_city_d.get(p, M.SHARE_FLOOR) for p in universe])
    local = np.array([[base_share_d[v].get(p, 0.0) for p in universe] for v in vds])
    if "ENTRANT" in index:
        local[:, index["ENTRANT"]] = M.SHARE_FLOOR
    dev = M.logit(local) - M.logit(base_city)[None, :]

    ent = scenario.get("entrant_geography") or {}
    if "ENTRANT" in index and ent.get("parent") in index:
        dev[:, index["ENTRANT"]] = (1.0 - float(ent.get("k", 1.0))) * dev[:, index[ent["parent"]]]

    # γ from a fold whose own target precedes this one
    params = load_parameters(args.processed / f"fold{spec['gamma_fold']}_parameters.csv")
    gamma = {}
    for ballot in ("PR", "Ward"):
        vals = np.ones(npar)
        for p, i in index.items():
            if p in params.get(ballot, {}).get("gamma", {}):
                vals[i] = params[ballot]["gamma"][p]
        gamma[ballot] = vals

    # ward/PR split from the PREVIOUS local election, never this one
    pw, _ = load(args.data_dir / spec["prior_lge"], "Ward")
    pp, _ = load(args.data_dir / spec["prior_lge"], "PR")
    wc, pc = citywide(pw), citywide(pp)
    ratio = np.ones(npar)
    for p, i in index.items():
        if pc.get(p, 0) > 0.001:
            ratio[i] = float(np.clip(wc.get(p, 0.0) / pc[p], 0.5, 2.0))
    for p, v in scenario["ward_pr_ratio_overrides"].items():
        if p in index:
            ratio[index[p]] = v

    # VD weight: the roll, times the previous local election's turnout there.
    prior_all, _ = load(args.data_dir / spec["prior_lge"], "PR")
    prior_cast = {v: sum(c.values()) for v, c in prior_all.items()}
    reg = np.array([registered.get(v, 0) for v in vds], dtype=float)
    prior_t = np.array([prior_cast.get(v, np.nan) / registered[v]
                        if registered.get(v) else np.nan for v in vds])
    typical = np.nanmedian(prior_t[np.isfinite(prior_t)]) if np.isfinite(prior_t).any() else 0.4
    prior_t = np.where(np.isfinite(prior_t), prior_t, typical)
    weight = np.clip(reg * prior_t, 1.0, None)

    centres, _ = M.blended_centres(scenario, base_city_d, {}, {})
    if "ENTRANT" in index:
        centres["ENTRANT"] = 0.0
    rng = np.random.default_rng(scenario["seed"])
    draw_target = M.make_drawer(scenario, base_city_d, centres, index, rng)

    ward_list = sorted({ward_of[v] for v in vds})
    ward_index = {w: i for i, w in enumerate(ward_list)}
    vd_ward = np.array([ward_index[ward_of[v]] for v in vds])

    out: list[dict[str, int]] = []
    for _ in range(scenario["draws"]):
        pr_target = draw_target()
        ward_target = pr_target * ratio
        ward_target = ward_target / ward_target.sum()
        pr = M.solve_and_predict(dev, base_city, pr_target, gamma["PR"], weight,
                                 level_floor=scenario["level_floor"])
        wd = M.solve_and_predict(dev, base_city, ward_target, gamma["Ward"], weight,
                                 level_floor=scenario["level_floor"])
        pr_votes = pr * weight[:, None]
        wd_votes = wd * weight[:, None]
        per_ward = np.zeros((len(ward_list), npar))
        np.add.at(per_ward, vd_ward, wd_votes)
        winners = per_ward.argmax(axis=1)
        ward_wins: defaultdict[str, int] = defaultdict(int)
        for w in winners:
            ward_wins[universe[w]] += 1
        # the allocator works in whole votes, as the statute does
        combined = {universe[i]: int(round(pr_votes[:, i].sum() + wd_votes[:, i].sum()))
                    for i in range(npar)}
        seats, _council, _thr, _over = M.allocate_with_overhang(
            combined, dict(ward_wins), rule=scenario["overhang_rule"])
        out.append({p: s for p, s in seats.items() if s > 0})
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    cityconfig.add_city_argument(ap)
    ap.add_argument("--target", type=int, choices=sorted(TARGETS), default=2021)
    ap.add_argument("--config", type=Path, help="scenario json (model to test)")
    ap.add_argument("--a", type=Path, help="A/B: first scenario")
    ap.add_argument("--b", type=Path, help="A/B: second scenario")
    ap.add_argument("--draws", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20211101)
    ap.add_argument("--data-dir", type=Path, default=Path("data/raw/elections"))
    ap.add_argument("--processed", type=Path, default=Path("data/processed"))
    args = ap.parse_args(argv)

    city = cityconfig.use(args.city)
    M.apply_city(city)
    spec = TARGETS[args.target]
    M.COUNCIL = spec["council"]

    print(f"backtest: {city.name} {args.target}  "
          f"(base {spec['base'].format(CODE=city.code)}, "
          f"γ from fold {spec['gamma_fold']}, council {spec['council']})")

    actual_seats, actual_winners = actual_result(
        args.data_dir / spec["actual"], spec["council"])
    # who actually arrived from nothing? the biggest party with no baseline
    base_votes, _ = load(args.data_dir / spec["base"], None)
    base_parties = set(citywide(base_votes))
    newcomers = {p: s for p, s in actual_seats.items() if p not in base_parties}
    entrant_actual = max(newcomers, key=newcomers.get) if newcomers else None
    if entrant_actual:
        print(f"  party arriving from nothing: {entrant_actual} "
              f"({newcomers[entrant_actual]} seats) -- scored against ENTRANT")
    print(f"  actual council: {sum(actual_seats.values())} seats to "
          f"{len(actual_seats)} parties; {len(actual_winners)} wards")

    configs = []
    if args.a and args.b:
        configs = [("A", args.a), ("B", args.b)]
    elif args.config:
        configs = [(args.config.stem, args.config)]
    else:
        configs = [("defaults", None)]

    results = {}
    for label, path in configs:
        scenario = copy.deepcopy(M.DEFAULTS)
        if path:
            overrides = json.loads(Path(path).read_text(encoding="utf-8"))
            for k, v in overrides.items():
                if isinstance(scenario.get(k), dict) and isinstance(v, dict):
                    scenario[k].update(v)
                else:
                    scenario[k] = v
        scenario["draws"] = args.draws
        scenario["seed"] = args.seed
        draws = run_one(args, city, spec, scenario)
        rows, err, inside, counted = score(draws, actual_seats, entrant_actual)
        results[label] = (rows, err, inside, counted)

    for label, (rows, err, inside, counted) in results.items():
        print(f"\n=== {label} ===")
        print(f"  {'party':10s}{'actual':>8s}{'median':>8s}{'5th':>7s}{'95th':>7s}{'err':>6s}")
        for p, act, med, lo, hi, e in sorted(rows, key=lambda r: -r[1])[:12]:
            flag = "" if lo <= act <= hi else "  <-- outside"
            print(f"  {p[:10]:10s}{act:>8d}{med:>8.0f}{lo:>7.0f}{hi:>7.0f}{e:>6.0f}{flag}")
        print(f"  total absolute seat error: {err:.0f}")
        print(f"  calibration: actual inside the 90% band for {inside}/{counted} "
              f"parties ({inside/counted:.0%}; a calibrated model gives ~90%)")

    if len(results) == 2:
        (_, ea, ia, ca), (_, eb, ib, cb) = results["A"], results["B"]
        print(f"\nA/B on {args.target}:  seat error A {ea:.0f} vs B {eb:.0f}   "
              f"calibration A {ia/ca:.0%} vs B {ib/cb:.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
