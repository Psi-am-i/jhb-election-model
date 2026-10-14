"""Which simulations make a scenario, and what their wards did.

A sentence on the page like "in the few simulations where the DA governs alone,
the ANC falls to ~47 seats because the DA flips its stronghold wards" is a claim
about particular draws. Until 2026-09-17 nothing could check it: the model threw
the per-draw ward winners away. `montecarlo.main` now writes them
(`ward_draws.csv`, `seat_detail_draws.csv`), and this reads them back.

    .venv/bin/python src/scenarios.py "DA>=136"
    .venv/bin/python src/scenarios.py "ANC<=50" "MK>=30" --limit 5

Conditions are `PARTY OP N` on total seats (`>=`, `<=`, `>`, `<`, `==`), all of
which must hold. For each matching draw it prints every party's seats split into
ward and list seats, whether the excessive-seats clause fired, and the wards
whose winner differs from that ward's MODAL winner across all draws — the flips
that make this draw different from the typical one.

⚠️ The model is over-confident at ward level (a ward it calls over 99% has lost
in the record), so a draw's ward map looks more settled than an election would.
Read flips as the model's mechanism, not as a prediction of which wards fall.
"""
from __future__ import annotations

import argparse
import csv
import operator
import re
from collections import Counter, defaultdict
from pathlib import Path

OPS = {">=": operator.ge, "<=": operator.le, ">": operator.gt,
       "<": operator.lt, "==": operator.eq}
COND = re.compile(r"^\s*([A-Za-z_]+)\s*(>=|<=|==|>|<)\s*(\d+)\s*$")


def parse(conditions: list[str]) -> list[tuple[str, str, int]]:
    out = []
    for c in conditions:
        m = COND.match(c)
        if not m:
            raise SystemExit(f"cannot read condition {c!r}: use PARTY>=N")
        out.append((m.group(1).upper(), m.group(2), int(m.group(3))))
    return out


def load(processed: Path):
    """(seats, detail, winners): per-draw totals, split and ward winners."""
    detail: dict[int, dict[str, dict]] = defaultdict(dict)
    with (processed / "seat_detail_draws.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            detail[int(r["draw"])][r["party"]] = {
                "wards": int(r["ward_seats"]), "list": int(r["list_seats"]),
                "seats": int(r["seats"]), "excessive": r["excessive"] == "1"}
    with (processed / "ward_draws.csv").open(encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        wards = next(reader)[1:]
        winners = {int(row[0]): dict(zip(wards, row[1:])) for row in reader}
    return detail, winners, wards


def majority_alone_share(processed: Path) -> float:
    """The share of simulations in which ONE party reaches the threshold.

    ⛔ ONE DEFINITION, TWO PAGES. `render_sheet` computed this inline for its
    tile and the home page needs the same quantity for its heading — and a
    heading that says a coalition is inevitable has to be reading the same
    number as the tile that says how often one is not. A second copy is how
    "the tiles disagreed with the article beside them" happens.

    It is the seat draws' row-wise maximum against that row's own threshold:
    the threshold varies by draw because the council size does.
    """
    import csv as _csv

    path = Path(processed) / "seat_draws.csv"
    if not path.exists():
        raise SystemExit(
            f"no {path}: the share of simulations where one party governs "
            f"alone cannot be read, and it may not be guessed.")
    alone = total = 0
    with path.open(encoding="utf-8", newline="") as fh:
        for row in _csv.DictReader(fh):
            threshold = int(float(row["threshold"]))
            best = max(int(float(v or 0)) for k, v in row.items()
                       if k not in ("draw", "threshold", "council_size"))
            alone += best >= threshold
            total += 1
    return alone / total if total else 0.0


# The percentiles `seat_quantiles` reports, and the share of simulations they
# cover. ⛔ THE 90 IS NOT A WORD. Both pages print "the range covering 90% of
# them" beside the table, and until 2026-09-25 both TYPED it — a second copy of
# this tuple, sitting in prose on a published page, which is exactly what the
# number audit blocks (it was two of the ten `BLOCKS` rows standing between the
# build and a `--publish`). The renderers now print `BAND_SHARE` as a token, so
# the sentence cannot say 90 while the code says something else.
BAND = (5, 95)
BAND_SHARE = (BAND[1] - BAND[0]) / 100


def seat_quantiles(series) -> tuple[int, int, int]:
    """(median, p5, p95) of a per-simulation seat series, as whole seats.

    ONE DEFINITION for every seats table on the site. The home page used a
    nearest-rank quantile and the sheet `np.percentile`, so the same party
    could print a different range on two pages; `forecast_summary.json`'s
    p5/p95 are `np.percentile`, so that is the convention.
    """
    import numpy as _np
    x = _np.asarray(series)
    return (int(round(float(_np.median(x)))),
            int(round(float(_np.percentile(x, BAND[0])))),
            int(round(float(_np.percentile(x, BAND[1])))))


# The parties a seats table NAMES, and therefore the complement that "Others"
# means. ⛔ ONE SET, EVERY PAGE. Until 2026-09-25 the forecast sheet named ten
# parties and the home page seven, so both pages printed a row labelled
# "Others" and the two numbers differed by the seats of the three the home page
# left out — one word, two figures, and nothing wrong with either arithmetic.
# The owner's ruling: the same "Others" throughout. Adding a party here adds a
# row to every seats table and removes its seats from every "Others"; that is
# the point, and it is why the set may not be redeclared per page.
NAMED_PARTIES = ("DA", "ANC", "EFF", "ASA", "MK", "PA", "IFP", "RISE",
                 "ALJAMAAH", "ENTRANT")


def others_per_draw(processed: Path, named) -> "np.ndarray":
    """Seats held by every party NOT in `named`, within each simulation.

    ⛔ ONE DEFINITION, TWO PAGES (owner, 2026-09-24: the two "Others" rows
    differed by about twenty seats). The sheet summed the small columns of
    `seat_draws.csv` — but that file keeps only the 13 largest parties, so
    every seat held by a party ranked lower was silently dropped. The home
    page took the council minus the named parties in each simulation, which
    is simply true: the seats exist and somebody holds them. That is this.

    And never a sum of per-party medians or percentiles: those describe no
    simulation (the "smaller parties — 39 seats" error, §1.214's shape).
    """
    import csv as _csv
    import numpy as _np
    path = Path(processed) / "seat_draws.csv"
    if not path.exists():
        raise SystemExit(
            f"no {path}: the seats held outside the named parties can only be "
            f"counted within each simulation, and may not be guessed.")
    named = set(named)
    out = []
    with path.open(encoding="utf-8", newline="") as fh:
        for row in _csv.DictReader(fh):
            council = int(float(row["council_size"]))
            held = sum(int(float(row.get(p) or 0)) for p in named if p in row)
            out.append(council - held)
    if not out:
        raise SystemExit(f"{path} has no simulations in it")
    return _np.array(out)


def all_party_seats(processed: Path, rows=None):
    """EVERY party's seats in every simulation: ``(seats, thresholds, councils)``.

    ⛔ ONE DEFINITION OF "THE WHOLE COUNCIL, PARTY BY PARTY" (owner,
    2026-10-07). ``seat_draws.csv`` keeps only the largest parties, so a
    coalition written as "every party except X" and summed over its columns
    drops every smaller party's seats, which is how the red-lines claim
    understated a majority without the ANC, the EFF and MK (MODEL-LOG §1.286
    has the figures). This reads ``seat_detail_draws.csv``, which carries
    every party, and returns ``seats`` as ``{party: array}`` in the order of
    ``seat_draws.csv``'s rows (``rows``, if the caller has already read them).

    It refuses rather than guesses when: the two files hold different
    simulations; a simulation's parties do not add up to its council; or a
    party ``seat_draws.csv`` names has different seats in the two files (two
    different runs).
    """
    import numpy as _np
    processed = Path(processed)
    if rows is None:
        with (processed / "seat_draws.csv").open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
    detail: dict[int, dict[str, int]] = defaultdict(dict)
    with (processed / "seat_detail_draws.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            detail[int(r["draw"])][r["party"]] = int(r["seats"])
    ids = [int(r["draw"]) for r in rows]
    if sorted(ids) != sorted(detail) or len(set(ids)) != len(ids):
        raise SystemExit("seat_draws.csv and seat_detail_draws.csv do not hold the "
                         "same simulations; every party's seats cannot be read")
    parties = sorted({p for d in detail.values() for p in d})
    columns = [k for k in rows[0] if k not in ("draw", "threshold", "council_size")]
    for r in rows:
        d = detail[int(r["draw"])]
        if sum(d.values()) != int(r["council_size"]):
            raise SystemExit(f"simulation {r['draw']}: the parties in seat_detail_draws.csv "
                             f"hold {sum(d.values())} seats, not its council of "
                             f"{r['council_size']}")
        bad = [p for p in columns if d.get(p, 0) != int(float(r[p] or 0))]
        if bad:
            raise SystemExit(f"simulation {r['draw']}: {bad} have different seats in "
                             f"seat_draws.csv and seat_detail_draws.csv")
    seats = {p: _np.array([detail[i].get(p, 0) for i in ids]) for p in parties}
    thr = _np.array([int(r["threshold"]) for r in rows])
    council = _np.array([int(r["council_size"]) for r in rows])
    return seats, thr, council


def matching(detail, conditions) -> list[int]:
    return [d for d in sorted(detail)
            if all(OPS[op](detail[d].get(p, {}).get("seats", 0), n)
                   for p, op, n in conditions)]


def summary_lot(processed: Path) -> str:
    """The published run's identity for the seeded lot (``seats.lot_identity``):
    the active city and target (``cityconfig.target()``, which the caller has
    pointed at ``processed``) and the seed in ``processed/forecast_summary.json``.
    The same identity ``montecarlo.main`` gave the run that wrote these files
    (``ModelRun.lot``). Refuses a summary with no seed: a lot cannot be named
    without one, and a tie must not fall to whatever order the file has.

    The city and target come from the configuration, not the summary, because
    the summary's ``scenario`` does not record them."""
    import json
    import cityconfig
    import seats
    path = processed / "forecast_summary.json"
    try:
        seed = json.loads(path.read_text())["scenario"]["seed"]
    except (OSError, KeyError, ValueError) as exc:
        raise SystemExit(f"{path}: no scenario seed to name the run's lot "
                         f"({exc!r}). JUDGEMENT-CALLS §Q2") from None
    if seed is None:
        raise SystemExit(f"{path}: the scenario seed is null, so the run's lot "
                         f"cannot be named. JUDGEMENT-CALLS §Q2")
    target = cityconfig.target()
    return seats.lot_identity(target.city.slug, str(target.year), seed)


def modal_winners(winners, wards, *, lot: str | None = None) -> dict[str, str]:
    """Each ward's party winning it in the most simulations, by rule A's call
    (``prediction.top_party``: a tie drawn by the seeded lot under
    ``seats.ward_key(lot, ward)``, ``lot`` being the run's identity,
    :func:`summary_lot`; ``Counter.most_common`` gave a tie to the party first
    seen, and from 2026-10-08 to 2026-10-09 the code first in string order)."""
    import prediction
    counts = {w: Counter() for w in wards}
    for row in winners.values():
        for w, p in row.items():
            counts[w][p] += 1
    from seats import ward_key
    return {w: prediction.top_party(c, lot=None if lot is None else ward_key(lot, w))
            for w, c in counts.items()}


def flips(winners, modal, draw) -> list[tuple[str, str, str]]:
    """(ward, usual winner, this draw's winner) where they differ."""
    return [(w, modal[w], p) for w, p in winners[draw].items() if p != modal[w]]


def typical(seats_by_party: dict, parties) -> int:
    """The simulation closest to every listed party's median seats, each
    party's distance scaled by its own 5-95% spread. A real simulation adds up
    exactly and is something the model produced, where a mean or median of each
    party is not (the ANC's mean list seats were 3.85 while 64% of simulations
    gave it none). Used by the "two ballots" bars and the map's council bar.
    ``seats_by_party`` maps party -> sequence of seats per simulation."""
    import numpy as np
    parties = [p for p in parties if p in seats_by_party]
    n = len(next(iter(seats_by_party.values())))
    meds = {p: float(np.median(seats_by_party[p])) for p in parties}
    spread = {p: max(float(np.percentile(seats_by_party[p], 95)
                           - np.percentile(seats_by_party[p], 5)), 1.0) for p in parties}
    return min(range(n), key=lambda i: sum(
        abs(seats_by_party[p][i] - meds[p]) / spread[p] for p in parties))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("conditions", nargs="+")
    ap.add_argument("--processed", type=Path, default=None,
                    help="default: the target's own processed directory")
    ap.add_argument("--limit", type=int, default=10)
    import cityconfig
    cityconfig.add_city_argument(ap)
    args = ap.parse_args(argv)
    cityconfig.use(getattr(args, "city", None))
    args.processed = args.processed or cityconfig.use_target(
        getattr(args, "target", None)).processed
    conditions = parse(args.conditions)
    detail, winners, wards = load(args.processed)
    hits = matching(detail, conditions)
    n = len(detail)
    print(f"{len(hits)} of {n:,} simulations match "
          f"{' and '.join(''.join(map(str, c)) for c in conditions)}")
    modal = modal_winners(winners, wards, lot=summary_lot(args.processed))
    for d in hits[:args.limit]:
        parties = sorted(detail[d].items(), key=lambda kv: -kv[1]["seats"])
        print(f"\n— simulation {d}")
        for p, v in parties:
            flag = "  (excessive-seats clause: no list seats)" if v["excessive"] else ""
            print(f"    {p:<30s} {v['seats']:>3d}  = {v['wards']:>3d} wards + "
                  f"{v['list']:>3d} list{flag}")
        fl = flips(winners, modal, d)
        moved = Counter((a, b) for _, a, b in fl)
        print(f"    wards won by someone other than their usual winner: {len(fl)}")
        for (a, b), k in moved.most_common(6):
            print(f"      {k:>3d}  {a} -> {b}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# The excessive-seats clause, said by party (owner, 2026-10-02: "is this the
# ANC or also other parties? We should say who they are. That is the story").
# A party is named when its chance is at or above this floor; the rest are
# summed up as "every other party <the highest of them> or less". PRESENTATION:
# it chooses which figures a sentence prints and changes no draw, seat or
# probability. The parties named come from the figures, in their order, never
# from a list.
#
# ⚠️ A party that crosses the floor between editions changes which tokens the
# page prints. One that drops below it leaves its published token off the page,
# and build_site refuses a published token that vanishes unretired: retire it
# (`publication.retire`) in that edition, as for any figure that stops being
# printed.
EXCESSIVE_FLOOR = 0.02


def excessive_by_party(by_party: dict, names: dict, chance, prefix: str,
                       source: str, exclude: tuple = ()) -> str:
    """"the ANC 62%, MK Party 3.8%, the EFF 2.7%, every other party 1.3% or less".

    ``by_party`` is forecast_summary.json's ``p_excessive_by_party``; ``names``
    maps a code to its reader name; ``chance(name, value, source)`` makes a
    token. Parties at or above ``EXCESSIVE_FLOOR`` are named, highest first;
    the clause about the rest carries the highest of their figures as its own
    token, and is left out when no other party ever triggers the clause.
    ``exclude`` drops parties the sentence has already given.
    """
    import stats as _stats

    figures = sorted(((float(v), c) for c, v in by_party.items() if c not in exclude),
                     key=lambda t: (-t[0], t[1]))
    named = [(v, c) for v, c in figures if v >= EXCESSIVE_FLOOR]
    rest = [v for v, c in figures if v < EXCESSIVE_FLOOR and v > 0]

    def who(c):
        nm = names.get(c, c)
        return ("the " if nm.isupper() else "") + nm

    parts = [f"{who(c)} {chance(f'{prefix}.{c.lower()}', v, source)}" for v, c in named]
    if rest:
        top = max(rest)
        t = chance(f"{prefix}_rest", top, source + ", the highest of the parties not named")
        tail = " or less" if _stats._fmt(top, "chance")[:1].isdigit() else ""
        parts.append(f"every other party {t}{tail}")
    return ", ".join(parts)
