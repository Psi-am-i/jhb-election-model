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

It also reports **pooled calibration** -- coverage at 50/80/90 and the
randomised PIT histogram, summed over every city-year. Per city-year those are
noise (seven to fifteen scored columns), which is why they were never worth
printing and therefore never printed; pooled over nine they are ~130 columns and
they say something the rest of this report cannot: whether the intervals are the
right WIDTH and whether they are in the right PLACE. Those are different faults
with different remedies, and this model has the second one. See
:func:`render_calibration` and MODEL-LOG §1.34.

Usage::

    python src/compare_history.py                    # everything runnable
    python src/compare_history.py --city joburg
    python src/compare_history.py --draws 2000 --md report.md
"""

from __future__ import annotations

import argparse
import json
import sys
import zlib
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


def rank_bands(run, actual_pr, actual_seats):
    """Error by where a party sits on the ballot, which is where it fails.

    A single headline hides the shape of this model's error completely. Ranks
    1-3 are over-predicted and everything below is short, and the parties that
    matter for marginal seats are ranks 4-12: big enough to win one, small
    enough that a fraction of a point decides it.

    **SIGNED AND ABSOLUTE, and neither one alone.** The sign is a finding — it
    says one band is eating the other, which an unsigned figure cannot — but a
    signed sum is not a measure of error, because errors in opposite directions
    inside the same band cancel and the band then reports as accurate. This
    statistic shipped signed-only and hid the model's largest single failure:
    at **Johannesburg 2021 ranks 1-3 read +1.36pp signed against 26.69pp
    absolute**, because the ANC (+6.53) and the DA (+7.39) cancelled against
    ActionSA (−12.59). That city-year is the model's WORST on seats (104 of
    error) and read second-best on this table. Across the nine city-years the
    signed total for ranks 1-3 is +32.67pp against 72.06pp absolute — an
    understatement of 2.2×. See MODEL-LOG §1.34.

    **PHANTOM MASS.** The bands iterate the parties that actually stood, so any
    share the model gives to a party that did not stand at all is invisible to
    every band. It is reported separately rather than left out: the citywide
    share vector sums to one over the model's own universe, so the phantom total
    is exactly why the three bands sum to −6.48pp rather than to zero across the
    nine city-years. It includes the generic ``ENTRANT`` column in a city-year
    where no party arrived, which is a real error and should be visible as one.
    """
    order = sorted(actual_pr, key=lambda p: -actual_pr[p])
    bands = {"1-3": order[:3], "4-12": order[3:12], "13+": order[12:]}
    out = {}
    for label, parties in bands.items():
        signed = absolute = won = 0.0
        for party in parties:
            i = run.index.get(party)
            pred = float(run.pr_share_draws[:, i].mean()) if i is not None else 0.0
            signed += pred - actual_pr[party]
            absolute += abs(pred - actual_pr[party])
            won += actual_seats.get(party, 0)
        out[label] = {"n": len(parties), "signed_pp": 100 * signed,
                      "abs_pp": 100 * absolute, "seats_at_stake": won}
    ghosts = {}
    for party, i in (run.index.items() if run.pr_share_draws is not None else ()):
        if party in actual_pr:
            continue
        pred = float(run.pr_share_draws[:, i].mean())
        if pred > 0:
            ghosts[party] = 100 * pred
    out["phantom"] = {"n": len(ghosts), "pp": float(sum(ghosts.values())),
                      "top": sorted(ghosts.items(), key=lambda kv: -kv[1])[:5]}
    return out


# The nominal interval levels calibration is reported at. Three, not one:
# a model can be right at 90% and wrong at 50%, and one number cannot show it.
LEVELS = (0.5, 0.8, 0.9)

# The populations calibration is measured over, in the order they are printed.
# The difference between them IS the finding, so all three are reported and each
# is labelled with what selects it. See :func:`calibration_columns`.
POPULATIONS = ("claimed", "seat_holders", "all")


def _pit_seed(city_slug: str, year: str, base: int = 20211101) -> int:
    """A per-city-year seed for the PIT randomisation, derived deterministically.

    ``score.pit_values`` draws one uniform per column from a fresh generator, so
    with the module default every city-year gives its k-th column the SAME
    uniform. Nine city-years pooled would then share nine draws rather than
    carry ~130 independent ones, and a single unlucky value would tilt the
    pooled histogram. Varying the seed per city-year removes that; deriving it
    from the name rather than a counter keeps the report reproducible and
    independent of which cities were run.
    """
    return base + zlib.crc32(f"{city_slug}:{year}".encode()) % 100_000


def calibration_columns(seat_draws, actual_seats, entrant_actual, seed):
    """Per-column PIT values and interval hits, UNPOOLED, for one city-year.

    Kept unpooled because per city-year these numbers are noise and pooling them
    is the whole point: Johannesburg 2021 reads 12/62/75 against nominal
    50/80/90 on n=8 columns and Cape Town 2021 reads 57/100/100 on n=7. Neither
    says anything. Summed over nine city-years (n≈132 seat-holding columns) they
    say the model under-forecasts, which is a real and previously unreported
    finding — see :func:`pooled_calibration` and MODEL-LOG §1.34.

    Three populations, because which columns you count changes the answer and
    the difference between them is itself informative:

    ``claimed``       columns this forecaster gives a seat in at least
                      ``score.CLAIM_FRACTION`` of its draws. Selection depends on
                      the FORECAST alone, so PIT uniformity survives it; this is
                      the neutral test and the one to quote.
    ``seat_holders``  columns that actually won a seat. Selection depends on the
                      OUTCOME, and zero is the bottom of the support, so under
                      perfect calibration the survivors are U(p₀, 1) rather than
                      uniform — this population reads high even for a flawless
                      forecaster and is INFLATED by construction. Reported
                      because it is the population a reader assumes, and because
                      it is what an outside reviewer computed.
    ``all``           every scored column. Neutral, but diluted by the ~200
                      parties that are correctly zero on both sides, each of
                      which is a free interval hit and a near-uniform PIT.

    Nothing here is reimplemented: the matrix, the randomised PIT and the
    coverage all come from ``score.py``, so the pooled figures and a single
    run's report cannot drift apart.
    """
    parties, samples, truth = S.seat_matrix(seat_draws, actual_seats,
                                            entrant_actual)
    pits = S.pit_values(samples, truth, seed=seed)
    n_cols = samples.shape[1] if samples.ndim == 2 else 0
    claimed = ((samples > 0).mean(axis=0) >= S.CLAIM_FRACTION
               if samples.shape[0] else np.zeros(n_cols, dtype=bool))
    masks = {"claimed": claimed,
             "seat_holders": truth > 0,
             "all": np.ones(n_cols, dtype=bool)}
    out = {}
    for name in POPULATIONS:
        mask = masks[name]
        out[name] = {
            "n": int(mask.sum()),
            "parties": [p for p, keep in zip(parties, mask) if keep],
            "pit": [float(v) for v in np.asarray(pits)[mask]],
            "coverage": S.coverage(samples[:, mask], truth[mask], LEVELS),
        }
    return out


def pooled_calibration(results, bins: int = 10) -> dict:
    """Coverage and PIT summed over every city-year. **This is the one to read.**

    Coverage pools by adding hits and columns; PIT pools by concatenating the
    values, because each column is one draw from what should be U(0,1) whatever
    city-year it came from. A per-city-year figure on seven to fifteen columns
    cannot separate 50% from 80%; the pooled one on ~130 can, and it is what
    exposed a systematic level bias the harness had never reported.
    """
    out = {}
    for pop in POPULATIONS:
        pits: list[float] = []
        cov: dict[float, dict] = {}
        for r in results:
            block = (r.get("calibration") or {}).get(pop)
            if not block:
                continue
            pits.extend(block["pit"])
            for row in block["coverage"]:
                acc = cov.setdefault(float(row["level"]),
                                     {"inside": 0, "counted": 0})
                acc["inside"] += int(row["inside"])
                acc["counted"] += int(row["counted"])
        out[pop] = {
            "n": len(pits),
            "pit": S.pit_histogram(np.array(pits, dtype=float), bins=bins),
            "coverage": [
                {"level": level, "inside": acc["inside"],
                 "counted": acc["counted"],
                 "empirical": (acc["inside"] / acc["counted"]
                               if acc["counted"] else float("nan"))}
                for level, acc in sorted(cov.items())],
        }
    return out


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
    # THE UNTRIMMED MEAN, and it was tested against the alternative. A review
    # proposed trimming, on the reasoning that a micro-party's seat draws are
    # zero in almost every draw and occasionally large, so its mean is tail-
    # driven and largest remainder rewards exactly that. The reasoning is sound
    # and the result is the other way: a 5%/95% trim took the nine-city coherent
    # seat error from 338 to 384. Trimming strips the small parties' mass, which
    # is where it genuinely lives, and hands it to the top three, which this
    # model already over-forecasts. Kept untrimmed, with the measurement.
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


def run_city_year(city_slug: str, year: str, draws: int, data_dir: Path,
                  overrides: list[str] | None = None) -> dict:
    city = cityconfig.use(city_slug)
    target = cityconfig.use_target(year)
    M.apply_city(city)
    # `set` AFTER apply_city, which is the whole point: apply_city writes the
    # city toml's scalars over DEFAULTS, so a --set is the only override that
    # survives it. See the --set help text.
    scenario = M.load_scenario(argparse.Namespace(
        config=None, set=list(overrides or []), draws=draws, seed=None,
        city=city_slug, target=year))
    run = M.run_model(target, scenario, data_dir, verbose=False)

    actual_pr, actual_ward = actual_shares(target, data_dir)
    actual_seats, entrant_actual = _actual_seats(target, data_dir, run)
    # Before ANY of the tables below. entrant_actual used to reach score_seats
    # and nothing else, so votes, rank bands and both seat errors all scored the
    # arrival machinery as a total miss plus a phantom. See backtest.relabel_run.
    run = B.relabel_run(run, entrant_actual)

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
        "bands": rank_bands(run, actual_pr, actual_seats),
        "seats": {p: (actual_seats.get(p, 0), model_seats.get(p, 0))
                  for p in sorted(set(actual_seats) | set(model_seats))},
        "seat_abs_err": sum(abs(actual_seats.get(p, 0) - model_seats.get(p, 0))
                            for p in set(actual_seats) | set(model_seats)),
        "seat_abs_err_coherent": sum(
            abs(actual_seats.get(p, 0) - coherent.get(p, 0))
            for p in set(actual_seats) | set(coherent)),
        "median_sum": sum(model_seats.values()),
        "calibration": calibration_columns(
            run.seat_draws, actual_seats, entrant_actual,
            _pit_seed(city_slug, year)),
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


_POP_LABEL = {
    "claimed": "claimed by the model (forecast-selected — the neutral test)",
    "seat_holders": "won a seat (outcome-selected — INFLATED by construction)",
    "all": "every scored column (neutral, but diluted by correct zeros)",
}


def render_calibration(results: list[dict], bins: int = 10) -> str:
    """The pooled calibration block. **Pooled is the only readable version.**

    Coverage says whether the intervals are the right WIDTH; the PIT mean says
    whether they are in the right PLACE. They can disagree, and here they do:
    a model whose 90% band covers 87% and whose PIT mean is far above 0.5 is not
    too narrow, it is too low. That distinction decides what to fix, and until
    this block existed the harness produced neither number.
    """
    pooled = pooled_calibration(results, bins=bins)
    lines: list[str] = []
    add = lines.append
    add("\n## Calibration — pooled across every city-year\n")
    add("**Read the pooled row, not a city-year.** Seven to fifteen scored "
        "columns per city-year cannot distinguish a 50% interval from an 80% "
        "one; the pooled ~130 can. Coverage should match the nominal level. PIT "
        "should be flat with mean 0.50 — a mean ABOVE 0.50 means the truth keeps "
        "landing high in the forecast distribution, i.e. the model under-"
        "forecasts.\n")
    add("| population | n | 50% | 80% | 90% | mean PIT | χ² vs flat (5% crit) |")
    add("|---|---|---|---|---|---|---|")
    for pop in POPULATIONS:
        block = pooled[pop]
        cov = {row["level"]: row["empirical"] for row in block["coverage"]}
        hist = block["pit"]
        crit = hist.get("chi2_crit_95")
        add(f"| {_POP_LABEL[pop]} | {block['n']} | "
            + " | ".join(f"{100 * cov.get(level, float('nan')):.0f}%"
                         for level in LEVELS)
            + f" | {hist['mean']:.3f} | {hist['chi2']:.1f} "
              f"({crit if crit is not None else '—'}) |")
    add("")
    for pop in POPULATIONS:
        block = pooled[pop]
        add(f"* **{pop}** (n={block['n']}) PIT histogram "
            f"{block['pit']['counts']} — {block['pit']['verdict']}")
    add("\nThe verdict at the end of each line is `score.pit_histogram`'s shape "
        "heuristic, which reads the end mass and the mean; **the χ² column is "
        "the test.** They can disagree — a histogram can be sloped rather than "
        "U-shaped, print 'approximately flat' and still be far past the "
        "critical value, which is what a level bias looks like when it is "
        "spread over the upper half rather than piled in the last bin.")
    add("\nThe three populations differ by which columns they count, and the "
        "difference is itself the finding. `claimed` selects on the FORECAST, "
        "which leaves PIT uniform under calibration, so it is the honest test. "
        "`seat_holders` selects on the OUTCOME: zero is the bottom of the "
        "support, so winning a seat selects over-performers and the population "
        "reads high even for a perfect forecaster — it is quoted because it is "
        "the population a reader assumes, not because it is neutral. `all` is "
        "neutral and diluted: most of its columns are parties correctly at zero "
        "on both sides, each a free interval hit and a near-uniform PIT.\n")

    add("Per city-year, for provenance only — **every n below is too small to "
        "read, and none of these rows is evidence of anything on its own.**\n")
    add("| city-year | n claimed | 50% | 80% | 90% | mean PIT (claimed) |")
    add("|---|---|---|---|---|---|")
    for r in results:
        block = (r.get("calibration") or {}).get("claimed")
        if not block:
            continue
        cov = {row["level"]: row["empirical"] for row in block["coverage"]}
        pit = np.array(block["pit"], dtype=float)
        cells = " | ".join(f"{100 * cov.get(level, float('nan')):.0f}%"
                           for level in LEVELS) if pit.size else "— | — | —"
        mean = f"{pit.mean():.3f}" if pit.size else "—"
        add(f"| {r['city']} {r['year']} | {block['n']} | {cells} | {mean} |")
    add("")
    return "\n".join(lines)


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

    add("\n## Where the vote error sits on the ballot\n")
    add("**Two columns per band, and they answer different questions.** *signed* "
        "is the net error in points — positive means the model gave that band "
        "MORE than it won — and it is what shows one band eating another. *abs* "
        "sums the per-party error without cancelling, and it is the only one of "
        "the two that is a measure of error at all. Where they diverge, the band "
        "is wrong about individual parties in both directions at once: "
        "Johannesburg 2021's ranks 1-3 are the case that motivated the column "
        "(ANC and DA over, ActionSA far under). The bands are by actual rank.\n")
    add("| city-year | 1-3 signed | 1-3 abs | 4-12 signed | 4-12 abs | "
        "13+ signed | 13+ abs | phantom | seats at stake in 4-12 |")
    add("|---|---|---|---|---|---|---|---|---|")
    for r in results:
        b = r["bands"]
        ph = b.get("phantom", {"pp": float("nan"), "n": 0})
        add(f"| {r['city']} {r['year']} | {b['1-3']['signed_pp']:+.2f}pp | "
            f"{b['1-3']['abs_pp']:.2f}pp | "
            f"**{b['4-12']['signed_pp']:+.2f}pp** | {b['4-12']['abs_pp']:.2f}pp | "
            f"{b['13+']['signed_pp']:+.2f}pp | {b['13+']['abs_pp']:.2f}pp | "
            f"{ph['pp']:.2f}pp ({ph['n']}) | "
            f"{b['4-12']['seats_at_stake']:.0f} |")
    tot = {k: sum(r["bands"][k]["signed_pp"] for r in results)
           for k in ("1-3", "4-12", "13+")}
    tot_abs = {k: sum(r["bands"][k]["abs_pp"] for r in results)
               for k in ("1-3", "4-12", "13+")}
    phantom = sum((r["bands"].get("phantom") or {}).get("pp", 0.0)
                  for r in results)
    add(f"\n**Totals across {len(results)} city-years:** ranks 1-3 "
        f"{tot['1-3']:+.2f}pp signed / {tot_abs['1-3']:.2f}pp absolute, ranks "
        f"4-12 {tot['4-12']:+.2f}pp / {tot_abs['4-12']:.2f}pp, ranks 13+ "
        f"{tot['13+']:+.2f}pp / {tot_abs['13+']:.2f}pp.")
    add(f"\n**Phantom mass: {phantom:.2f}pp** on parties that did not stand at "
        f"all — including the generic `ENTRANT` column where no party arrived. "
        f"The bands iterate the parties that DID stand, so none of them can see "
        f"it; it is exactly why the three signed bands sum to "
        f"{sum(tot.values()):+.2f}pp rather than to zero.\n")

    add(render_calibration(results))

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
    ap.add_argument("--set", action="append", metavar="KEY=VALUE",
                    help="override a scenario key for EVERY city-year, e.g. "
                         "--set entrant_prob=0.5. This is the only honest way to "
                         "sweep a constant here: editing montecarlo.DEFAULTS does "
                         "NOT reach a run, because apply_city writes cities/"
                         "<city>.toml's scalars over DEFAULTS afterwards — and "
                         "leaves them there for every city that follows. A sweep "
                         "of DEFAULTS returns byte-identical rows and reads as "
                         "'this constant does nothing'.")
    args = ap.parse_args(argv)

    results = []
    for slug in ([args.city] if args.city else CITIES):
        city = cityconfig.load(slug)
        for year in runnable(city):
            if args.target and year != args.target:
                continue
            print(f"  {slug} {year} ...", flush=True)
            try:
                results.append(run_city_year(slug, year, args.draws, args.data_dir,
                                         args.set))
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
