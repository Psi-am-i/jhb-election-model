"""What makes a bloc a bloc — measured, not assumed.

Johannesburg's blocs (ANC/EFF/MK against DA/ActionSA) were a judgement. Before
that judgement is copied to another metro it has to be earned there, so this
script asks what a bloc actually *looks like* in the data and applies the same
test to whichever city is active.

Two signatures, both computable from voting-district results:

**1. Shared pool (spatial correlation).** Parties fishing for the same voters
stand in the same places. Across a city's districts, their vote shares move
together — a district strong for one is strong for the other — because both
are drawing on the same population. Measured as the correlation of district
shares, registration-weighted.

**2. Offsetting, ACROSS DISTRICTS.** Whether the bloc's total varies less
from place to place than its members do individually.

**A limitation to state plainly, because it changes how signature 2 should
be read.** The model's bloc claim is temporal, not spatial: it draws a bloc
*level* for the election and splits it between members, betting that members
trade votes with each other between elections. This script measures variation
*across districts within one election*, which is a different question. A low
ratio here is suggestive; it is not the model's claim tested. The correct
test compares members' shares across the NPE→LGE transitions — and with only
four observed transitions that test is weak by construction, which is exactly
why the bloc structure is a documented judgement rather than a fitted
parameter (MODEL-LOG §1.4).

A further caution the numbers cannot supply: high spatial correlation does
not prove a shared pool. Two parties can be strong in the same suburbs
because those suburbs simply turn out, not because their voters choose
between them. Treat all of this as an argument to weigh, never a verdict.

    python src/bloc_signature.py --city joburg
    python src/bloc_signature.py --city tshwane --election lge2021
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import numpy as np

import cityconfig
from iec_csv import sniff_encoding
from parties import canonical


def district_shares(path: Path, ballot: str | None = "PR"):
    """VD -> {party: share}, plus VD -> votes cast."""
    votes: defaultdict[str, defaultdict[str, int]] = defaultdict(
        lambda: defaultdict(int))
    with path.open(encoding=sniff_encoding(path), newline="") as fh:
        for row in csv.DictReader(fh):
            if ballot and row.get("BallotType", "").upper() != ballot.upper():
                continue
            vd = row["VD_Number"]
            votes[vd][canonical(row["sPartyName"])] += int(row["Party_Votes"] or 0)
    shares, cast = {}, {}
    for vd, tally in votes.items():
        total = sum(tally.values())
        if total < 50:                 # tiny districts are noise
            continue
        cast[vd] = total
        shares[vd] = {p: v / total for p, v in tally.items()}
    return shares, cast


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    cityconfig.add_city_argument(ap)
    ap.add_argument("--election", default="lge2021")
    ap.add_argument("--top", type=int, default=8)
    args = ap.parse_args(argv)
    city = cityconfig.use(args.city)

    path = Path("data/raw/elections") / f"{args.election}_{city.code}_vd_party_clean.csv"
    if not path.exists():
        raise SystemExit(f"no {path}")
    shares, cast = district_shares(path)
    vds = sorted(shares)
    w = np.array([cast[v] for v in vds], dtype=float)

    totals: defaultdict[str, float] = defaultdict(float)
    for vd in vds:
        for p, s in shares[vd].items():
            totals[p] += s * cast[vd]
    grand = sum(totals.values())
    top = [p for p, _ in sorted(totals.items(), key=lambda kv: -kv[1])][:args.top]

    matrix = {p: np.array([shares[v].get(p, 0.0) for v in vds]) for p in top}

    def wcorr(a, b):
        ma, mb = np.average(a, weights=w), np.average(b, weights=w)
        va, vb = a - ma, b - mb
        denom = np.sqrt(np.average(va**2, weights=w) * np.average(vb**2, weights=w))
        return float(np.average(va * vb, weights=w) / denom) if denom else 0.0

    print(f"\n{city.name} · {args.election} · {len(vds)} districts")
    print(f"citywide: " + " · ".join(
        f"{p} {totals[p]/grand:.1%}" for p in top[:6]))

    print("\n1. SHARED POOL — correlation of district shares "
          "(positive = same places)\n")
    print("        " + "".join(f"{p[:7]:>8s}" for p in top))
    for a in top:
        row = "".join(f"{wcorr(matrix[a], matrix[b]):>8.2f}" if a != b
                      else f"{'—':>8s}" for b in top)
        print(f"{a[:7]:>7s} {row}")

    print("\n2. OFFSETTING — does grouping steady the total?\n")
    print(f"   {'candidate bloc':38s} {'ratio':>6s}  reading")
    for label, members in list(city.blocs.items()) + [
            ("ANC+EFF+MK (Joburg's ANC bloc)", ("ANC", "EFF", "MK")),
            ("DA+ASA (Joburg's DA bloc)", ("DA", "ASA")),
            ("DA+ASA+VFPLUS", ("DA", "ASA", "VFPLUS")),
            ("DA+VFPLUS", ("DA", "VFPLUS")),
            ("ANC+EFF", ("ANC", "EFF"))]:
        present = [m for m in members if m in matrix]
        if len(present) < 2:
            continue
        stacked = np.vstack([matrix[m] for m in present])
        total_sd = np.sqrt(np.average((stacked.sum(axis=0)
                                       - np.average(stacked.sum(axis=0), weights=w))**2,
                                      weights=w))
        parts_sd = sum(np.sqrt(np.average((matrix[m] - np.average(matrix[m], weights=w))**2,
                                          weights=w)) for m in present)
        ratio = total_sd / parts_sd if parts_sd else 1.0
        reading = ("strong offsetting" if ratio < 0.6 else
                   "some offsetting" if ratio < 0.85 else
                   "little — grouping buys almost nothing")
        print(f"   {label + ' [' + '+'.join(present) + ']':38.38s} "
              f"{ratio:>6.2f}  {reading}")

    print("\n   Ratio = sd(bloc total) / sum of members' sd, across districts.")
    print("   Below ~0.6 the members genuinely trade votes with each other;")
    print("   near 1.0 they move independently and the bloc is a fiction.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
