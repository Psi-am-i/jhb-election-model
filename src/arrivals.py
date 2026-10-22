"""Every party that arrived from nothing, and what the model said about it.

The arrival machinery is the most elaborate part of this model — splinter
lineage, home and away records, contestation gating, pool inheritance, arrival
bands — and it has never been scored on its own. Its failures show up inside a
seat total where they are indistinguishable from a level error on an established
party. This separates them.

An ARRIVAL here is a party that took votes at the target while holding **no
share at all** of the national election the model builds its baseline from. That
is the case the machinery exists for and the only case it can be judged on: a
party with any baseline, however small, is being forecast by θ and the spine like
everyone else.

    python src/arrivals.py                  # every runnable city-year
    python src/arrivals.py --city joburg

Two things it is careful about.

**The generic ENTRANT is relabelled**, onto whichever arrival won the most seats,
exactly as ``score.seat_matrix`` and ``backtest.relabel_entrant`` do it. The
model cannot know a newcomer's name; scoring it as a total miss when it sized the
newcomer correctly answers a question nobody asked. Only one party can receive
it, so every other arrival is scored on its own seeded forecast.

**Vote share is reported as the MEAN**, not the median. An arrival's share comes
from a Dirichlet component with a small concentration, which is a spike near zero
with a long right tail, so its median can be a fifth of its mean. The median is
the right summary for "will this party win a seat"; the mean is the right one for
"how big does the model think it is", and this asks the second.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import backtest as B
import cityconfig
import montecarlo as M
from fold import citywide, load

CITIES = ["joburg", "tshwane", "ekurhuleni", "ethekwini", "capetown",
          "mangaung", "nelsonmandelabay", "buffalocity"]


def arrivals_for(city_slug: str, year: str, draws: int, data_dir: Path):
    city = cityconfig.use(city_slug)
    target = cityconfig.use_target(year)
    M.apply_city(city)
    scenario = M.load_scenario(argparse.Namespace(
        config=None, set=None, draws=draws, seed=None,
        city=city_slug, target=year))
    run = M.run_model(target, scenario, data_dir, verbose=False)

    base_votes, _ = load(data_dir / target.results(target.previous_npe), None)
    baseline = citywide(base_votes)
    pr, _ = load(data_dir / target.results(year), "PR")
    actual = citywide(pr)
    actual_seats, _ = B.actual_result(data_dir / target.results(year),
                                      target.council, int(year))

    arrivals = sorted((p for p, s in actual.items()
                       if baseline.get(p, 0.0) <= 0 and s > 0 and p != "IND"),
                      key=lambda p: -actual[p])
    if not arrivals:
        return []

    # ENTRANT goes to whichever arrival won most seats — one party only.
    biggest = max(arrivals, key=lambda p: (actual_seats.get(p, 0), actual[p]))
    ent = run.index.get("ENTRANT")

    rows = []
    for party in arrivals:
        i = run.index.get(party)
        share = float(run.pr_share_draws[:, i].mean()) if i is not None else 0.0
        seat_draws = [d.get(party, 0) for d in run.seat_draws]
        if party == biggest and ent is not None:
            share += float(run.pr_share_draws[:, ent].mean())
            seat_draws = [a + d.get("ENTRANT", 0)
                          for a, d in zip(seat_draws, run.seat_draws)]
        rows.append({
            "city": city.name, "year": year, "party": party,
            "actual_share": actual[party], "model_share": share,
            "actual_seats": actual_seats.get(party, 0),
            "model_seats": int(np.median(seat_draws)),
            "p_any_seat": float(np.mean([s > 0 for s in seat_draws])),
            "got_entrant": party == biggest and ent is not None,
        })
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--city", default=None)
    ap.add_argument("--draws", type=int, default=1500)
    ap.add_argument("--min-seats", type=int, default=1,
                    help="only arrivals that won at least this many seats")
    ap.add_argument("--data-dir", type=Path, default=Path("data/raw/elections"))
    args = ap.parse_args(argv)

    rows = []
    for slug in ([args.city] if args.city else CITIES):
        city = cityconfig.load(slug)
        for year in B.runnable_targets(city):
            if not (city.processed / f"pools_{year}.json").exists():
                continue
            try:
                rows += arrivals_for(slug, year, args.draws, args.data_dir)
            except Exception as exc:
                print(f"  {slug} {year} failed: {type(exc).__name__}: {exc}")

    rows = [r for r in rows if r["actual_seats"] >= args.min_seats]
    rows.sort(key=lambda r: -r["actual_seats"])
    if not rows:
        print("no arrivals found")
        return 1

    print(f"\nEvery party that arrived from nothing and won a seat "
          f"({len(rows)} of them)\n")
    print(f"  {'city':<20}{'yr':>5}  {'party':<26}"
          f"{'model':>8}{'actual':>8}  {'model':>6}{'actual':>7}{'P(seat)':>9}")
    print(f"  {'':<20}{'':>5}  {'':<26}{'vote':>8}{'vote':>8}"
          f"  {'seats':>6}{'seats':>7}{'':>9}")
    for r in rows:
        flag = " *" if r["got_entrant"] else ""
        print(f"  {r['city'][:19]:<20}{r['year']:>5}  {r['party'][:25]:<26}"
              f"{r['model_share']:>7.2%}{r['actual_share']:>8.2%}"
              f"{r['model_seats']:>7}{r['actual_seats']:>7}"
              f"{r['p_any_seat']:>8.0%}{flag}")
    print("  * received the generic ENTRANT slot")

    hit = [r for r in rows if r["model_seats"] > 0]
    close = [r for r in rows
             if r["actual_share"] > 0
             and 0.5 <= r["model_share"] / r["actual_share"] <= 2.0]
    claimed = [r for r in rows if r["p_any_seat"] >= 0.5]
    print(f"\n  arrivals given a median seat at all:      "
          f"{len(hit)}/{len(rows)}")
    print(f"  arrivals sized within a factor of two:    "
          f"{len(close)}/{len(rows)}")
    print(f"  arrivals the model gave a >50% chance of any seat: "
          f"{len(claimed)}/{len(rows)}")
    under = sum(r["actual_share"] - r["model_share"] for r in rows)
    print(f"  total vote under-forecast across arrivals: {100 * under:+.2f}pp")
    print(f"  total seats: model {sum(r['model_seats'] for r in rows)}, "
          f"actual {sum(r['actual_seats'] for r in rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
