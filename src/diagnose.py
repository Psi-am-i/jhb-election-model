"""One election, laid out so a fault can be ISOLATED rather than summarised.

A headline seat error says the forecast was 62 out. It does not say whether the
citywide vote was wrong, or the vote was right and the ward geography wrong, or
the ward calls were right and the seat arithmetic concentrated a small vote
error at the top. Those are three different bugs with three different fixes, and
a single number cannot tell them apart.

So this prints four things for one city-year, in the order a fault travels
through the model:

1. **CITYWIDE VOTE** — every party, PR and ward ballot, predicted against
   actual, with the error in points. This is the model's primary output; seats
   are a consequence of it.
2. **SEATS, SPLIT INTO WARD AND LIST** — because they fail for different
   reasons. Ward seats are won one contest at a time and depend on geography;
   list seats are the entitlement left over after ward wins are deducted, and
   depend only on the citywide vote and the quota. A party can be right on
   votes and wrong on wards, or the reverse.
3. **EVERY WARD CALLED WRONG** — the ward, who won it, who the model said, and
   what probability the model put on the party that actually won. A ward lost at
   p=0.45 is noise; a ward lost at p=0.02 is a fault.
4. **WHERE THE SEAT ERROR CAME FROM** — the same total decomposed by party, so
   a 62 can be read as "the ANC alone is 25 of it" instead of as a mystery.

Usage::

    python src/diagnose.py --city joburg --target 2016
    python src/diagnose.py --city joburg --target 2021 --draws 2000
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import backtest as B
import benchmarks as BM
import cityconfig
import montecarlo as M
import score as S
from fold import citywide, load
from seats import allocate, eligible_parties


def run(city_slug: str, year: str, draws: int, data_dir: Path):
    city = cityconfig.use(city_slug)
    target = cityconfig.use_target(year)
    M.apply_city(city)
    scenario = M.load_scenario(argparse.Namespace(
        config=None, set=None, draws=draws, seed=None,
        city=city_slug, target=year))
    return target, M.run_model(target, scenario, data_dir, verbose=False)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--city", default="joburg")
    ap.add_argument("--target", default="2021")
    ap.add_argument("--draws", type=int, default=1000)
    ap.add_argument("--data-dir", type=Path, default=Path("data/raw/elections"))
    ap.add_argument("--wards", type=int, default=40,
                    help="how many wrong ward calls to list (0 = all)")
    args = ap.parse_args(argv)

    target, run_ = run(args.city, args.target, args.draws, args.data_dir)
    path = args.data_dir / target.results(target.year)
    actual_seats, actual_ward_winners = B.actual_result(
        path, target.council, int(target.year))

    pr_votes, _ = load(path, "PR")
    ward_votes, _ = load(path, "Ward")
    actual_pr, actual_wd = citywide(pr_votes), citywide(ward_votes)

    idx = run_.index
    name = cityconfig.active().name

    # ---- 1. citywide vote ------------------------------------------------
    print(f"\n{'=' * 78}\n{name} {target.year} — council {target.council}, "
          f"{len(run_.wards)} wards, {run_.draws} draws\n{'=' * 78}")
    print("\n1. CITYWIDE VOTE  (model = mean over draws; err in percentage points)\n")
    print(f"  {'party':<14}{'PR model':>10}{'PR actual':>11}{'err':>8}"
          f"{'ward model':>12}{'ward actual':>12}{'err':>8}")
    universe = sorted(set(actual_pr) | set(idx),
                      key=lambda p: -actual_pr.get(p, 0.0))
    pr_err_total = wd_err_total = 0.0
    for p in universe:
        a_pr, a_wd = actual_pr.get(p, 0.0), actual_wd.get(p, 0.0)
        i = idx.get(p)
        m_pr = float(run_.pr_share_draws[:, i].mean()) if i is not None else 0.0
        m_wd = float(run_.ward_share_draws[:, i].mean()) if i is not None else 0.0
        pr_err_total += abs(m_pr - a_pr)
        wd_err_total += abs(m_wd - a_wd)
        if max(a_pr, m_pr) < 0.002:
            continue
        print(f"  {p[:13]:<14}{m_pr:>9.2%} {a_pr:>10.2%} {100*(m_pr-a_pr):>+7.2f}"
              f"{m_wd:>11.2%} {a_wd:>11.2%} {100*(m_wd-a_wd):>+7.2f}")
    print(f"\n  total absolute vote error: PR {100*pr_err_total:.2f}pp, "
          f"ward {100*wd_err_total:.2f}pp  (sums both directions, so a model "
          f"that moves 3pp from small parties to large scores 6)")

    # ---- 2. seats, split -------------------------------------------------
    actual_wardwins = Counter(actual_ward_winners.values())
    model_seats = {p: int(np.median([d.get(p, 0) for d in run_.seat_draws]))
                   for p in {q for d in run_.seat_draws for q in d}}
    # Model ward wins: the modal winner of each ward, which is the call it makes.
    model_ward_call: dict[str, str] = {}
    probs = run_.ward_probabilities()
    for ward, dist in probs.items():
        if dist:
            model_ward_call[ward] = max(dist, key=dist.get)
    model_wardwins = Counter(model_ward_call.values())

    print("\n2. SEATS — total, ward and list, because they fail differently\n")
    print(f"  {'party':<14}{'seats':>13}{'ward seats':>16}{'list seats':>16}")
    print(f"  {'':<14}{'model':>6}{'actual':>7}{'model':>8}{'actual':>8}"
          f"{'model':>8}{'actual':>8}")
    rows = sorted(set(actual_seats) | set(model_seats),
                  key=lambda p: -actual_seats.get(p, 0))
    for p in rows:
        a_s, m_s = actual_seats.get(p, 0), model_seats.get(p, 0)
        a_w, m_w = actual_wardwins.get(p, 0), model_wardwins.get(p, 0)
        if not (a_s or m_s or a_w or m_w):
            continue
        # List seats are the entitlement left after ward wins are deducted --
        # plan §0: winning a ward does not add a seat, it decides which
        # entitled seat a ward councillor fills. Negative means overhang.
        print(f"  {p[:13]:<14}{m_s:>6}{a_s:>7}{m_w:>8}{a_w:>8}"
              f"{m_s - m_w:>8}{a_s - a_w:>8}")
    seat_err = {p: model_seats.get(p, 0) - actual_seats.get(p, 0)
                for p in set(actual_seats) | set(model_seats)}
    print(f"\n  ward calls: {sum(1 for w, c in model_ward_call.items() if actual_ward_winners.get(w) == c)}"
          f"/{len(model_ward_call)} correct")

    # ---- 3. wards called wrong -------------------------------------------
    wrong = []
    for ward, call in model_ward_call.items():
        truth = actual_ward_winners.get(ward)
        if truth is None or truth == call:
            continue
        wrong.append((probs[ward].get(truth, 0.0), ward, truth, call,
                      probs[ward].get(call, 0.0)))
    wrong.sort()
    print(f"\n3. WARDS CALLED WRONG — {len(wrong)} of {len(model_ward_call)}\n")
    if wrong:
        print(f"  {'ward':<12}{'won by':<14}{'model said':<14}"
              f"{'P(model call)':>14}{'P(actual winner)':>18}")
        shown = wrong if args.wards == 0 else wrong[:args.wards]
        for p_true, ward, truth, call, p_call in shown:
            flag = "  <-- ruled out" if p_true < 0.02 else ""
            print(f"  {ward:<12}{truth[:13]:<14}{call[:13]:<14}"
                  f"{p_call:>13.0%}{p_true:>17.0%}{flag}")
        if len(wrong) > len(shown):
            print(f"  ... and {len(wrong) - len(shown)} more")
        ruled_out = sum(1 for p, *_ in wrong if p < 0.02)
        print(f"\n  of the {len(wrong)} wrong calls, {ruled_out} gave the actual "
              f"winner under 2% — those are faults, not bad luck; the rest are "
              f"contests the model saw as close and lost")

    # ---- 4. where the seat error came from -------------------------------
    print("\n4. WHERE THE SEAT ERROR CAME FROM\n")
    total = sum(abs(v) for v in seat_err.values())
    print(f"  {'party':<14}{'error':>8}{'share of total':>17}")
    for p, v in sorted(seat_err.items(), key=lambda kv: -abs(kv[1])):
        if v == 0:
            continue
        print(f"  {p[:13]:<14}{v:>+8}{abs(v) / total:>16.0%}")
    print(f"  {'':<14}{'':>8}\n  total absolute seat error: {total}")

    # ---- benchmarks, on the same party set -------------------------------
    print("\n5. THE SAME MEASURE FOR THE NAIVE BASELINES\n")
    ctx = BM.build_context(int(target.year), args.data_dir)
    print(f"  {'forecaster':<20}{'seat error':>12}{'vs model':>12}")
    print(f"  {'this model':<20}{total:>12}{'—':>12}")
    for bench in ("last-lge", "uniform-swing", "prior-lge-noise"):
        try:
            bd = BM.run_one(bench, ctx, draws=min(args.draws, 2000))
        except SystemExit as exc:
            print(f"  {bench:<20}{'—':>12}   {exc}")
            continue
        bs = {p: int(np.median([d.get(p, 0) for d in bd]))
              for p in {q for d in bd for q in d}}
        berr = sum(abs(bs.get(p, 0) - actual_seats.get(p, 0))
                   for p in set(actual_seats) | set(bs))
        verdict = "model better" if total < berr else "BASELINE BETTER"
        print(f"  {bench:<20}{berr:>12}{verdict:>16}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
