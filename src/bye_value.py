"""Did by-election evidence predict the next real result beyond the model? (BRIEF item 19)

The owner, 2026-10-09: "by elections we need to use history as the judge of
whether they predicted anything not already predicted by model". By-election
evidence gets weight only to the extent that, historically, it predicted the
next real result beyond the model's own baseline, out of sample; if it adds
nothing measurable its weight is zero. Every party, one rule. SPEC R2.4 is the
specification; ``prereg/2026-10-10-byelection-value-test.md`` pre-registered
the prediction and fixed every method choice R2.4 left open before this module
existed.

⚠️ **A CROSS-BALLOT TEST ON THE WHOLE RECORD.** The archive's by-elections start
in 2022-02, so the only real result after them is the 2024 provincial ballot.
By-elections are local ward contests; the outcome is a national-provincial
list ballot. Every quotation of this module's result says so; the artefact
carries the sentence as ``caveat``.

The test, per (party, metro) pair:

* **Population.** The party stood in at least one by-election in the metro in
  ``byelections.SA_FILE``, dated after the 2021 LGE and before 2024-05-29, in
  a ward with a 2021 base; and it has a positive list share at the 2021 LGE
  or on the 2024 provincial ballot there.
* **Baseline ``B``**, the model's prediction of the 2024 result without
  by-elections: the 2021 LGE list share converted to the national ballot by
  the model's own national-local relation at the party's size,
  ``B = s_2021 / exp(mu_θ)``. ``mu_θ`` is ``levels._shrunk`` on
  ``levels.theta_record`` for a 2024 target (the record strictly before 2024,
  items 11, 16 and 17 applied), at each party's 2019 national share in the
  metro, with the window ``levels.size_window`` derives at 2024. A party with
  no ``mu_θ`` takes the common mean ``_shrunk`` returns, as ``levels.spine``
  does. With no 2021 list share, ``B = 0``.
* **The delta ``δ_pr``.** ``byelections.weighted_deltas`` with ages taken to
  2024-05-29 (``byelections.TAU_MONTHS``, the same similarity weight),
  converted to the list scale by ``byelections.delta_pr`` with the metro's
  ``levels.trusted_ward_pr`` ratio: the conversion ``blended_centres`` uses.
* **Residual** ``e = actual_2024 − B``; the augmented prediction is
  ``B + w·δ_pr``.
* **Classes.** By ``s_2021``: ``byelections.size_class`` (edge
  ``BYE_CLASS_EDGE``, 1%), each with its own ``w``.
* **Leave one metro out.** ``w_(−m) = max(0, Σeδ/Σδ²)`` over the class's
  pairs in the other metros; ``G = mean|e| − mean|e − w_(−m)·δ|`` pooled over
  every pair of the class, in points of share.
* **Uncertainty.** ``BYE_VALUE_RESAMPLES`` bootstrap resamples of the metros
  holding any pair (the cluster), hold-out by metro identity, seed
  ``BYE_VALUE_SEED``; the ``BYE_VALUE_PERCENTILE``-th percentile of ``G``.
* **Rule.** A class with fewer than ``BYE_VALUE_MIN_PAIRS`` pairs: weight 0,
  "not measurable". Otherwise the slope on all its pairs (floored at 0) if
  the percentile of ``G`` is above 0, else 0.
* **Secondary, reported, not deciding.** Each contest's delta predicted from
  the same party's other contests in the same metro, against predicting 0.

The artefact, ``data/processed/bye_value.json`` (``byelections.BYE_VALUE``),
carries both classes' weights, ``G`` and its interval, the pair counts, the
verdicts, every pair, the secondary and an ``artefact_key``
(``byelections.bye_value_key``). ``montecarlo.run_model`` reads the weights
and refuses a missing or stale file at a target that reads by-elections.

Usage::

    .venv/bin/python src/bye_value.py --out DIR    # into DIR
    .venv/bin/python src/bye_value.py --emit       # data/processed/bye_value.json

``--emit`` belongs to a re-emit window (``POOLS-REEMIT-QUEUE.md``), after the
pool specs. Run from the repository root: ``levels.theta_record`` reads the
election files by relative path.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

import byelections as BY
import cityconfig
import levels
import montecarlo as M

ROOT = Path(__file__).resolve().parent.parent

#: The eight metros, in the order the artefact lists them.
CITIES = ("joburg", "tshwane", "ekurhuleni", "ethekwini", "capetown",
          "nelsonmandelabay", "buffalocity", "mangaung")
#: The outcome election, the local election the deltas are taken against, and
#: the national election before the outcome (the size ``mu_θ`` is taken at).
OUTCOME, BASE_LGE, BASE_NPE = BY.BYE_VALUE_OUTCOME, "2021", "2019"

#: Typed parts of the test (JUDGEMENT-CALLS §A55), fixed in the
#: pre-registration before the run.
BYE_VALUE_MIN_PAIRS = 10
BYE_VALUE_RESAMPLES = 2000
BYE_VALUE_PERCENTILE = 5.0
BYE_VALUE_SEED = 20261010

CAVEAT = ("Cross-ballot test on the whole record: by-elections are local ward "
          "contests (from 2022-02), and the only real result after them is "
          "the 2024 provincial ballot, a national-provincial list ballot.")


def _cutoff():
    """The outcome's polling day: no by-election on or after it is read."""
    return cityconfig.CALENDAR[OUTCOME].date


def _election(slug: str, year: str) -> Path:
    city = cityconfig.load(slug)
    return ROOT / "data" / "raw" / "elections" / cityconfig.CALENDAR[
        year].results.replace("{CODE}", city.code)


def baselines(cities=CITIES) -> tuple[dict, dict]:
    """``B`` per metro and party, from files strictly before 2024 only.

    Returns ``({slug: {"s2021": {...}, "B": {...}, "fallback": [...]}},
    window_report)``. ``tests/test_temporal.py`` spies this function's file
    opens (G25): it reads the θ record before 2024, each metro's 2021 LGE and
    2019 national files, and nothing dated 2024 or later.
    """
    target = cityconfig.Target(city=cityconfig.load(cities[0]), year=OUTCOME)
    record = levels.theta_record(target)
    h, window = levels.size_window(target, levels.theta_record, record=record)
    out = {}
    for slug in cities:
        s2021 = levels._citywide(_election(slug, BASE_LGE))
        national = levels._citywide(_election(slug, BASE_NPE))
        mus, common, _worth = levels._shrunk(record, current=national, h=h)
        base, fallback = {}, []
        for party, share in sorted(s2021.items()):
            if share <= 0:
                continue
            if party not in mus:
                fallback.append(party)
            base[party] = share / math.exp(mus.get(party, common))
        out[slug] = {"s2021": s2021, "B": base, "fallback": fallback}
    return out, window


def outcomes(cities=CITIES) -> dict[str, dict[str, float]]:
    """Each metro's 2024 provincial-ballot shares: the outcome, read apart
    from ``B`` so the temporal spy can scope one without the other."""
    return {slug: levels._citywide(_election(slug, OUTCOME)) for slug in cities}


def deltas(slug: str, s2021: dict[str, float]) -> dict:
    """One metro's by-election evidence, by the model's own definitions.

    ``byelections.weighted_deltas`` over the metro's contests between the
    2021 LGE and 2024-05-29, against the 2021 ward ballot, ages to
    2024-05-29; each party's weighted delta converted by
    ``byelections.delta_pr`` with ``levels.trusted_ward_pr`` (the 2021 ward
    and PR citywide shares, ``montecarlo.WARD_PR_RATIO_MIN/MAX``).
    """
    city = cityconfig.load(slug)
    lge = _election(slug, BASE_LGE)
    contests = BY.load_byelections(ROOT / BY.SA_FILE, city.ward_prefix,
                                   cityconfig.CALENDAR[BASE_LGE].date,
                                   _cutoff())
    votes, registered = BY.ward_ballot(lge)
    found = BY.weighted_deltas(contests, votes, registered, _cutoff(),
                               BY.TAU_MONTHS, BASE_LGE)
    totals: dict[str, int] = defaultdict(int)
    for tally in votes.values():
        for party, n in tally.items():
            totals[party] += n
    cast = sum(totals.values())
    wc = {p: n / cast for p, n in totals.items()} if cast else {}
    trusted = levels.trusted_ward_pr(wc, s2021, M.WARD_PR_RATIO_MIN,
                                     M.WARD_PR_RATIO_MAX)
    dates: dict[str, list[str]] = defaultdict(list)
    for row in found["delta_rows"]:
        dates[row["party"]].append(row["date"])
    parties = {}
    for party in sorted(found["weight_sum"]):
        ws = found["weight_sum"][party]
        if ws <= 0:
            continue
        d = found["weighted"][party] / ws
        parties[party] = {"weight_sum": ws, "delta": d,
                          "ratio": trusted.get(party),
                          "delta_pr": BY.delta_pr(d, trusted.get(party)),
                          "dates": sorted(dates[party])}
    return {"contests": len(contests), "skipped": len(found["skipped"]),
            "parties": parties, "delta_rows": found["delta_rows"]}


def collect(cities=CITIES) -> dict:
    """Every pair of the population, with ``B``, ``actual``, ``e`` and ``δ_pr``.

    Quiet: the helpers' prints are swallowed. Returns ``{"pairs": [...],
    "window": ..., "metros": {slug: {contests, skipped}}, "delta_rows":
    {slug: [...]}}``.
    """
    with contextlib.redirect_stdout(io.StringIO()):
        base, window = baselines(cities)
        actual = outcomes(cities)
        evidence = {slug: deltas(slug, base[slug]["s2021"]) for slug in cities}
    pairs = []
    for slug in cities:
        s2021 = base[slug]["s2021"]
        for party, ev in evidence[slug]["parties"].items():
            s = float(s2021.get(party, 0.0))
            a = float(actual[slug].get(party, 0.0))
            if s <= 0 and a <= 0:
                continue
            b = float(base[slug]["B"].get(party, 0.0))
            pairs.append({
                "metro": slug, "party": party, "s2021": s, "B": b,
                "actual": a, "e": a - b, "delta": ev["delta"],
                "ratio": ev["ratio"], "delta_pr": ev["delta_pr"],
                "weight_sum": ev["weight_sum"], "contests": len(ev["dates"]),
                "dates": ev["dates"], "class": BY.size_class(s),
                "mu_fallback": party in base[slug]["fallback"]})
    return {"pairs": pairs, "window": window,
            "metros": {slug: {"contests": evidence[slug]["contests"],
                              "skipped_no_base": evidence[slug]["skipped"]}
                       for slug in cities},
            "delta_rows": {slug: evidence[slug]["delta_rows"]
                           for slug in cities}}


def slope(e: np.ndarray, d: np.ndarray) -> float:
    """Least squares through the origin, floored at 0 (0 where ``Σd² = 0``)."""
    denom = float((d * d).sum())
    if denom <= 0:
        return 0.0
    return max(0.0, float((e * d).sum()) / denom)


def lomo_gain(groups: list[tuple[object, np.ndarray, np.ndarray]]
              ) -> tuple[float, dict]:
    """Pooled out-of-sample gain over ``groups``, held out by identity.

    ``groups`` is ``[(metro, e, d), ...]``; a metro may appear more than once
    (a bootstrap copy), and every copy of a metro is held out together and
    fitted on the copies of the others. Returns ``(G, {metro: w_(−m)})``;
    ``G = mean|e| − mean|e − w_(−m)·d|`` over every pair, 0 with no pair.
    """
    metros = sorted({m for m, _e, _d in groups}, key=str)
    weights = {}
    before = after = 0.0
    n = 0
    for m in metros:
        fit = [(e, d) for k, e, d in groups if k != m]
        w = (slope(np.concatenate([e for e, _ in fit]),
                   np.concatenate([d for _, d in fit])) if fit else 0.0)
        weights[m] = w
        for k, e, d in groups:
            if k != m:
                continue
            before += float(np.abs(e).sum())
            after += float(np.abs(e - w * d).sum())
            n += len(e)
    if n == 0:
        return 0.0, weights
    return (before - after) / n, weights


def evaluate(pairs: list[dict], resamples: int = BYE_VALUE_RESAMPLES,
             seed: int = BYE_VALUE_SEED,
             percentile: float = BYE_VALUE_PERCENTILE,
             min_pairs: int = BYE_VALUE_MIN_PAIRS) -> dict:
    """Steps 2-5 of SPEC R2.4 on ``pairs`` (each with ``metro``, ``class``,
    ``e``, ``delta_pr``, ``contests``). Data-free: G23 runs it on
    constructed pairs. Every number is in shares (0-1); the artefact's
    ``*_points`` fields are the same in points.
    """
    metros = sorted({p["metro"] for p in pairs})
    rng = np.random.default_rng(seed)
    draws = [rng.integers(0, len(metros), size=len(metros)).tolist()
             for _ in range(resamples)] if metros else []
    out = {}
    for cls in BY.SIZE_CLASSES:
        mine = [p for p in pairs if p["class"] == cls]
        by_metro = {m: (np.array([p["e"] for p in mine if p["metro"] == m]),
                        np.array([p["delta_pr"] for p in mine
                                  if p["metro"] == m]))
                    for m in metros}
        groups = [(m, *by_metro[m]) for m in metros if len(by_metro[m][0])]
        g, w_out = lomo_gain(groups)
        all_e = (np.concatenate([e for _m, e, _d in groups])
                 if groups else np.array([]))
        all_d = (np.concatenate([d for _m, _e, d in groups])
                 if groups else np.array([]))
        w_all = slope(all_e, all_d) if len(all_e) else 0.0
        boot = []
        for draw in draws:
            copies = [(metros[i], *by_metro[metros[i]]) for i in draw]
            copies = [c for c in copies if len(c[1])]
            boot.append(lomo_gain(copies)[0] if copies else 0.0)
        low = (float(np.percentile(boot, percentile)) if boot else 0.0)
        n = len(mine)
        if n < min_pairs:
            verdict, weight = "not measurable", 0.0
        elif low > 0.0:
            verdict, weight = "admitted", w_all
        else:
            verdict, weight = "no measurable gain", 0.0
        out[cls] = {
            "pairs": n,
            "pairs_two_or_more_contests": sum(1 for p in mine
                                              if p["contests"] >= 2),
            "metros": len(groups),
            "slope_all_metros": w_all,
            "w_leave_one_metro_out": {m: w_out[m] for m in sorted(w_out)},
            "G": g, "G_points": 100.0 * g,
            "G_percentile": low, "G_percentile_points": 100.0 * low,
            "G_bootstrap_median": (float(np.median(boot)) if boot else 0.0),
            "verdict": verdict, "weight": weight,
        }
    return out


def secondary(delta_rows: dict[str, list[dict]]) -> dict:
    """Each contest's delta predicted from the same party's other contests in
    the same metro (their weight-averaged delta), against predicting 0.

    Ward-ballot scale, read from ``weighted_deltas``' rows (as the CSVs
    carry them, four decimals). Reported, not deciding (SPEC R2.4 step 6);
    the metros only, where the 2021 ward bases exist (pre-registration
    decision 10).
    """
    loo_abs = zero_abs = 0.0
    n = 0
    for slug in sorted(delta_rows):
        by_party: dict[str, list[tuple[float, float]]] = defaultdict(list)
        for row in delta_rows[slug]:
            by_party[row["party"]].append((float(row["delta"]),
                                           float(row["weight"])))
        for party in sorted(by_party):
            rows = by_party[party]
            if len(rows) < 2:
                continue
            for i, (d, _w) in enumerate(rows):
                others = [r for j, r in enumerate(rows) if j != i]
                wsum = sum(w for _d, w in others)
                if wsum <= 0:
                    continue
                pred = sum(dd * w for dd, w in others) / wsum
                loo_abs += abs(d - pred)
                zero_abs += abs(d)
                n += 1
    return {"contests_scored": n,
            "mae_points_other_contests": 100.0 * loo_abs / n if n else None,
            "mae_points_zero": 100.0 * zero_abs / n if n else None,
            "gain_points": 100.0 * (zero_abs - loo_abs) / n if n else None,
            "scope": "party-contests in the eight metros with at least one "
                     "other contest by the same party in the same metro"}


def build(cities=CITIES) -> dict:
    """The artefact: key, caveat, method, both classes, every pair."""
    found = collect(cities)
    pairs = found["pairs"]
    classes = evaluate(pairs)
    return {
        "artefact_key": BY.bye_value_key((M.WARD_PR_RATIO_MIN,
                                          M.WARD_PR_RATIO_MAX)),
        "caveat": CAVEAT,
        "outcome": f"npe{OUTCOME} provincial ballot",
        "cutoff": _cutoff().isoformat(),
        "class_edge": BY.BYE_CLASS_EDGE,
        "tau_months": BY.TAU_MONTHS,
        "resamples": BYE_VALUE_RESAMPLES, "seed": BYE_VALUE_SEED,
        "percentile": BYE_VALUE_PERCENTILE,
        "min_pairs": BYE_VALUE_MIN_PAIRS,
        "size_window": found["window"],
        "metros": found["metros"],
        "classes": classes,
        "weights": {cls: classes[cls]["weight"] for cls in BY.SIZE_CLASSES},
        "population": len(pairs),
        "mu_fallback_pairs": sum(1 for p in pairs if p["mu_fallback"]),
        "pairs": sorted(pairs, key=lambda p: (p["metro"], p["party"])),
        "secondary": secondary(found["delta_rows"]),
    }


def write(payload: dict, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / BY.BYE_VALUE
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n",
                    encoding="utf-8")
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    where = ap.add_mutually_exclusive_group(required=True)
    where.add_argument("--emit", action="store_true",
                       help="write data/processed/bye_value.json")
    where.add_argument("--out", type=Path,
                       help="write bye_value.json into this directory")
    args = ap.parse_args(argv)
    directory = (ROOT / "data" / "processed") if args.emit else args.out
    payload = build()
    path = write(payload, directory)
    for cls in BY.SIZE_CLASSES:
        c = payload["classes"][cls]
        print(f"{cls:>10s}: {c['pairs']} pairs, G {c['G_points']:+.3f} pts, "
              f"{BYE_VALUE_PERCENTILE:g}th pct {c['G_percentile_points']:+.3f}, "
              f"{c['verdict']}, weight {c['weight']:.3f}")
    print(f"{CAVEAT}\nwrote {path}")
    return 0


if __name__ == "__main__":
    # The θ record is gathered through set intersections, so the order its
    # floats are summed in, and their last bit, follows the hash seed. Pinned
    # as the model pins it, so two builds of one tree are byte-equal.
    M.fix_hash_seed()
    raise SystemExit(main())
