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


def matching(detail, conditions) -> list[int]:
    return [d for d in sorted(detail)
            if all(OPS[op](detail[d].get(p, {}).get("seats", 0), n)
                   for p, op, n in conditions)]


def modal_winners(winners, wards) -> dict[str, str]:
    counts = {w: Counter() for w in wards}
    for row in winners.values():
        for w, p in row.items():
            counts[w][p] += 1
    return {w: c.most_common(1)[0][0] for w, c in counts.items()}


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
    modal = modal_winners(winners, wards)
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
