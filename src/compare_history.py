"""Every past election we can run, as votes and as seats, against every opponent.

``sweep.py`` answers "is anything obviously broken". This answers the question
that comes next: **how close was it, on what the ballots actually said.**

Three quantities per party, not one. Seats are a step function of votes through
a quota, so a forecast can be four seats out while being a tenth of a point out
on the ballot, or a tenth of a point out and four seats wrong. Reporting seats
alone hides which. So each table carries:

    list votes    the PR ballot, citywide share, predicted median vs actual
    ward votes    the ward ballot, citywide share, same
    seats         the combined-ballot council, same

and each is scored against three opponents, all through ``score.py`` so nothing
is scored by different code:

    last-lge          "the last local election happens again"
    uniform-swing     that, shifted by the national movement bracketing it
    prior-lge-noise   that, with a spread from the previous transition
    published         the run recorded in data/processed/validation_<year>.json,
                      where one exists -- the model as it stood then, so a
                      change can be read as a change rather than asserted

Usage::

    python src/compare_history.py                    # everything runnable
    python src/compare_history.py --city joburg
    python src/compare_history.py --draws 2000 --md report.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import backtest as B
import benchmarks as BM
import cityconfig
import montecarlo as M
import score as S
from fold import citywide, load

CITIES = ["joburg", "tshwane", "ekurhuleni", "ethekwini", "capetown",
          "mangaung", "nelsonmandelabay", "buffalocity"]


def runnable(city) -> list[str]:
    out = []
    for year in B.runnable_targets(city):
        if (city.processed / f"pools_{year}.json").exists():
            out.append(year)
    return out


def actual_shares(target, data_dir: Path) -> tuple[dict, dict]:
    """The target's own citywide PR and ward shares. Scoring only."""
    path = data_dir / target.results(target.year)
    pr, _ = load(path, "PR")
    ward, _ = load(path, "Ward")
    return citywide(pr), citywide(ward)


def vote_table(run, actual_pr, actual_ward, top=12):
    """Per-party predicted vs actual on both ballots, MEAN AND MEDIAN.

    Both, because for this model they are not the same statement and the gap is
    the finding. A small party's share within a pool comes out of a Dirichlet
    whose concentration for that party is a fraction of one, which is a spike
    near zero with a long right tail: at Johannesburg 2021 the AIC's median
    predicted share is 0.11% and its mean 0.58%, a factor of five, and the
    actual was 0.69%. Reporting the median alone says the model missed the AIC
    by six-fold; reporting the mean alone says it was within 16%. Neither
    sentence is the whole truth and the distance between them is the story.
    """
    idx = run.index
    rows = []
    for party in sorted(actual_pr, key=lambda p: -actual_pr[p])[:top]:
        i = idx.get(party)
        if i is None:
            rows.append((party, float("nan"), float("nan"), actual_pr[party],
                         float("nan"), float("nan"),
                         actual_ward.get(party, 0.0)))
            continue
        pr, wd = run.pr_share_draws[:, i], run.ward_share_draws[:, i]
        rows.append((party,
                     float(np.median(pr)), float(pr.mean()), actual_pr[party],
                     float(np.median(wd)), float(wd.mean()),
                     actual_ward.get(party, 0.0)))
    return rows


def vote_mae(run, actual, ballot="pr", weighted=True, stat="mean") -> float:
    """Mean absolute error on citywide share, in percentage points.

    ``stat`` selects the point forecast. The default is the MEAN, because that
    is the central estimate of a right-skewed distribution; the median is
    reported next to it so the difference stays visible.
    """
    draws = run.pr_share_draws if ballot == "pr" else run.ward_share_draws
    if draws is None:
        return float("nan")
    err, wt = [], []
    for party, share in actual.items():
        i = run.index.get(party)
        if i is None:
            pred = 0.0
        else:
            col = draws[:, i]
            pred = float(col.mean() if stat == "mean" else np.median(col))
        err.append(abs(pred - share))
        wt.append(share)
    if not err:
        return float("nan")
    w = np.array(wt) if weighted else np.ones(len(err))
    return float(100 * np.average(err, weights=w if w.sum() > 0 else None))


def seats_from_draws(draws):
    """Median seats per party over a list of {party: seats} dicts.

    **These are MARGINAL medians and they do not sum to a council.** The median
    of a sum is not the sum of medians, and with many parties the shortfall is
    large: at Johannesburg 2021 this returns 243 seats against a 270-seat
    chamber, so 27 of the reported seat error is the aggregation rather than the
    model. The baselines in ``benchmarks.py`` allocate per draw and sum exactly,
    which makes any seat-error comparison against them unfair to this side.

    Kept, because the per-party median is what a reader wants to see next to a
    per-party actual. :func:`coherent_seats` is the summable counterpart, and
    :func:`render` prints both totals so the gap is never invisible.
    """
    parties = sorted({p for d in draws for p in d})
    return {p: int(np.median([d.get(p, 0) for d in draws])) for p in parties}


def coherent_seats(draws, council: int):
    """A point forecast that IS a council: largest remainder on the mean vector.

    The mean seat vector sums to the council up to rounding (every draw does),
    so apportioning it by largest remainder gives a chamber rather than a set of
    unrelated marginals. Use this for any seat-error comparison against the
    baselines; use the median for the per-party table a reader reads.
    """
    parties = sorted({p for d in draws for p in d})
    if not parties or council <= 0:
        return {}
    mean = np.array([np.mean([d.get(p, 0) for d in draws]) for p in parties])
    total = mean.sum()
    if total <= 0:
        return {p: 0 for p in parties}
    exact = mean * (council / total)
    base = np.floor(exact).astype(int)
    short = council - int(base.sum())
    if short > 0:
        order = np.argsort(-(exact - base))
        for i in order[:short]:
            base[i] += 1
    return {p: int(n) for p, n in zip(parties, base)}


def published_for(city_slug: str, year: str) -> dict | None:
    path = Path("data/processed") / f"validation_{year}.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
    except Exception:
        return None
    entry = (payload.get("cities") or {}).get(city_slug)
    return entry


def run_city_year(city_slug: str, year: str, draws: int, data_dir: Path) -> dict:
    city = cityconfig.use(city_slug)
    target = cityconfig.use_target(year)
    M.apply_city(city)
    scenario = M.load_scenario(argparse.Namespace(
        config=None, set=None, draws=draws, seed=None, city=city_slug,
        target=year))
    run = M.run_model(target, scenario, data_dir, verbose=False)

    actual_pr, actual_ward = actual_shares(target, data_dir)
    actual_seats, entrant_actual = _actual_seats(target, data_dir, run)

    model_seats = seats_from_draws(run.seat_draws)
    coherent = coherent_seats(run.seat_draws, target.council)
    out = {
        "city": city.name, "slug": city_slug, "year": year,
        "council": target.council,
        "votes": vote_table(run, actual_pr, actual_ward),
        "pr_mae": vote_mae(run, actual_pr, "pr", stat="mean"),
        "ward_mae": vote_mae(run, actual_ward, "ward", stat="mean"),
        "pr_mae_median": vote_mae(run, actual_pr, "pr", stat="median"),
        "ward_mae_median": vote_mae(run, actual_ward, "ward", stat="median"),
        "seats": {p: (actual_seats.get(p, 0), model_seats.get(p, 0))
                  for p in sorted(set(actual_seats) | set(model_seats))},
        "seat_abs_err": sum(abs(actual_seats.get(p, 0) - model_seats.get(p, 0))
                            for p in set(actual_seats) | set(model_seats)),
        "seat_abs_err_coherent": sum(
            abs(actual_seats.get(p, 0) - coherent.get(p, 0))
            for p in set(actual_seats) | set(coherent)),
        "median_sum": sum(model_seats.values()),
        "opponents": {},
    }
    scored = S.score_seats(run.seat_draws, actual_seats,
                           entrant_actual=entrant_actual)
    out["crps"] = scored["crps"]["total"]

    ctx = BM.build_context(int(year), data_dir)
    for name in ("last-lge", "uniform-swing", "prior-lge-noise"):
        try:
            seat_draws = BM.run_one(name, ctx, draws=min(draws, 2000))
        except SystemExit as exc:
            out["opponents"][name] = {"error": str(exc)}
            continue
        bench_seats = seats_from_draws(seat_draws)
        out["opponents"][name] = {
            "crps": S.score_seats(seat_draws, actual_seats,
                                  entrant_actual=entrant_actual)["crps"]["total"],
            "seat_abs_err": sum(
                abs(actual_seats.get(p, 0) - bench_seats.get(p, 0))
                for p in set(actual_seats) | set(bench_seats))}

    pub = published_for(city_slug, year)
    if pub and pub.get("model"):
        m = pub["model"]
        out["opponents"]["published"] = {
            "crps": m.get("crps"),
            "seat_abs_err": sum(
                abs(r["actual"] - r["forecast"]) for r in m.get("parties", [])),
            "generated": pub.get("generated")}
    return out


def _actual_seats(target, data_dir: Path, run):
    """The published council for this target, via the backtest's own reader.

    ``actual_result`` returns more than the seats and its arity has changed
    before, so the seat map is picked out by shape rather than by position.
    ``entrant_actual`` needs the model's own BASELINE — which party had no
    national share to grow from — not the target, which is what makes a
    correctly sized newcomer score as a newcomer rather than as a total miss.
    """
    path = data_dir / target.results(target.year)
    actual = B.actual_result(path, target.council, int(target.year))
    seats = None
    for item in (actual if isinstance(actual, tuple) else (actual,)):
        if hasattr(item, "seats"):
            seats = item.seats
            break
        if isinstance(item, dict) and item and all(
                isinstance(v, (int, float)) for v in item.values()):
            seats = item
            break
    if seats is None:
        raise ValueError(f"actual_result returned no seat map for {target.year}")
    base = {p: 1.0 for p in run.index}
    return seats, B.entrant_actual_for(seats, base)


def render(results: list[dict]) -> str:
    lines: list[str] = []
    add = lines.append
    add("# Historical performance — votes and seats, predicted against actual\n")
    add(f"{len(results)} city-years. Shares are citywide percentages; the "
        f"model column is the median over draws.\n")

    add("## Headline\n")
    add("| city-year | council | list MAE | ward MAE | seat err (median) | "
        "medians sum to | seat err (coherent) | CRPS | last-lge | "
        "uniform-swing | prior-lge-noise |")
    add("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        o = r["opponents"]
        def cell(key, field="seat_abs_err"):
            v = o.get(key, {})
            if "error" in v or v.get(field) is None:
                return "—"
            return f"{v[field]:.0f}" if field == "seat_abs_err" else f"{v[field]:.1f}"
        add(f"| {r['city']} {r['year']} | {r['council']} | "
            f"{r['pr_mae']:.2f}pp | {r['ward_mae']:.2f}pp | "
            f"{r['seat_abs_err']} | {r['median_sum']} | "
            f"{r['seat_abs_err_coherent']} | {r['crps']:.1f} | "
            f"{cell('last-lge')} | {cell('uniform-swing')} | "
            f"{cell('prior-lge-noise')} |")
    add("\n**Read the two seat-error columns together.** *seat err (median)* "
        "uses the per-party marginal median, which is what the per-party tables "
        "below show and which **does not sum to a council** — the *medians sum "
        "to* column says by how much. *seat err (coherent)* apportions the mean "
        "seat vector by largest remainder, so it IS a chamber and is the only "
        "one comparable to the baselines, which allocate per draw and sum "
        "exactly. Lower is better throughout.\n")

    for r in results:
        add(f"\n## {r['city']} {r['year']}\n")
        add("| party | list median | list mean | list actual | ward mean | "
            "ward actual | seats model | seats actual |")
        add("|---|---|---|---|---|---|---|---|")
        seats = r["seats"]
        for party, pr_md, pr_mn, pr_a, wd_md, wd_mn, wd_a in r["votes"]:
            a, m = seats.get(party, (0, 0))
            add(f"| {party} | {pr_md:.2%} | {pr_mn:.2%} | {pr_a:.2%} | "
                f"{wd_mn:.2%} | {wd_a:.2%} | {m} | {a} |")
        missed = [p for p, (a, m) in seats.items() if a >= 3 and m == 0]
        if missed:
            add(f"\n**Missed entirely:** {', '.join(missed)} — won seats, "
                f"median zero.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--draws", type=int, default=1000)
    ap.add_argument("--city", default=None)
    ap.add_argument("--target", default=None)
    ap.add_argument("--data-dir", type=Path, default=Path("data/raw/elections"))
    ap.add_argument("--md", type=Path, default=Path("data/processed/history.md"))
    ap.add_argument("--json", type=Path, default=Path("data/processed/history.json"))
    args = ap.parse_args(argv)

    results = []
    for slug in ([args.city] if args.city else CITIES):
        city = cityconfig.load(slug)
        for year in runnable(city):
            if args.target and year != args.target:
                continue
            print(f"  {slug} {year} ...", flush=True)
            try:
                results.append(run_city_year(slug, year, args.draws, args.data_dir))
            except Exception as exc:
                print(f"    failed: {type(exc).__name__}: {exc}")
    if not results:
        print("nothing runnable")
        return 1
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(results, indent=2, default=float))
    text = render(results)
    args.md.write_text(text)
    print(text)
    print(f"\nwrote {args.md} and {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
