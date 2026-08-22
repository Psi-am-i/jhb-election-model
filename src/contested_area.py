"""Validate the contested-area conversion — the table `polling.py` asserted.

`polling.metro_estimate` converts a national poll share into a metro one by
dividing by the share of the national vote sitting in the municipalities the
party actually contests: ``estimate = X / s``. Its docstring carried a table
justifying that, measured over every arrival in the eight-metro archive as the
median absolute log ratio between estimate and actual metro share::

                         raw national share    contested-area adjusted
    2016 (83 arrivals)            1.609                 0.000
    2021 (175 arrivals)           1.228                 0.144

**No script produced it.** It was reproduced on 2026-08-22 and it is exactly
right — the arrival counts and both adjusted figures match to three decimals —
but reproducing it showed three things the table does not say, and two of them
change what it establishes. MODEL-LOG §1.66.

    .venv/bin/python src/contested_area.py

WHAT AN ARRIVAL IS HERE. A party that took votes in a metro at the local
election while holding no share of that metro's vote at the preceding national
election — `src/arrivals.py`'s definition, applied per party per metro. That
gives 83 pairs at 2016 and 175 at 2021, which is where the docstring's counts
come from.

--- 1. THE 2016 ROW IS A TAUTOLOGY, AND SO IS HALF OF 2021 -------------------

If a party stands in exactly one metro, its share of its contested area IS its
share of that metro, by identity. The estimate cannot be wrong, and contributes
a hard zero to the median.

    2016   46 of 83 arrivals stood in one metro   =  55%
    2021   67 of 175                              =  38%

At 2016 the majority are single-metro, so **the median is one of those zeros**.
The docstring says "trivially exact because nearly every arrival stood in a
single metro", which is honest and now quantified — but it sits next to a 2021
figure that is treated as a real result while being built from the same
material.

Restricted to MULTI-metro arrivals — the only ones where the conversion does any
work at all:

    2016   n=37    median |log ratio|  0.234
    2021   n=108   median |log ratio|  0.431

0.431 in log units is a factor of about **1.54**. That is the honest figure for
the mechanism, and it is three times the 0.144 the docstring quotes.

--- 2. THE TWO COLUMNS USE DIFFERENT DENOMINATORS ----------------------------

The "raw" column is the party's share of the **eight-metro aggregate**; the
adjusted column runs through `contested_share`, whose denominator is the
**national** vote. Verified by computing both::

    2016   raw vs national total 2.504    raw vs eight-metro total 1.609
    2021   raw vs national total 1.995    raw vs eight-metro total 1.228

The published raw column is the eight-metro one. So the improvement the table
displays is partly a change of denominator rather than the contested-area
adjustment, and the columns are not like-for-like.

--- 3. AND IT DOES NOT TEST THE CONVERSION IT CLAIMS TO ----------------------

This is the one that matters. In the table, ``X`` is reconstructed from the
archive as (party's votes across the metros it stood in) / (national vote), and
``s`` is (votes cast in those metros) / (national vote). **The national figure
cancels**, and the estimate reduces to

    tv / votes cast in the metros it stood in

— the party's share of its own contested area, computed entirely inside the
metro archive. The poll never appears, and neither does `NATIONAL_VOTES`.

So the table validates the GEOGRAPHIC half of the mechanism (a party's average
across the area it contests predicts its share in one metro of that area) and
**not the CONVERSION half** (a poll's national share divided by a roll-derived
denominator). In production the national figure does not cancel — it is what
makes the arithmetic work — and nothing here exercises it.

What does validate the production behaviour is MODEL-LOG §1.65: with the real
Ipsos 2021 poll driving the real path, the arrivals channel is worth 48 coherent
seats across nine city-years. That is the evidence for this mechanism. This
table is a weaker and partly tautological companion to it, and should be quoted
as one.
"""

from __future__ import annotations

import collections
import math
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import levels
import parties as P
import polling
import pools as PL
from ingest_lge import read_municipality

# (local election, the national election whose result decides who is an arrival)
TRANSITIONS = (("2016", "2014"), ("2021", "2019"))


def metro_party_votes(code: str, year: str) -> dict[str, int]:
    """PR-ballot votes per party in one metro, through the shared reader."""
    path = PL.metro_file(code, year)
    if path is None:
        return {}
    out: collections.Counter = collections.Counter()
    for row in read_municipality(path, code, "PR"):
        out[P.canonical(row["sPartyName"])] += int(row["Party_Votes"] or 0)
    return dict(out)


def arrivals(lge: str, npe: str):
    """``(party, code, codes_it_stood_in)`` for every arrival at this LGE."""
    votes = {c: metro_party_votes(c, lge) for c in PL.METRO_CODES}
    stood: dict[str, list[str]] = collections.defaultdict(list)
    for code in PL.METRO_CODES:
        for party, v in votes.get(code, {}).items():
            if v > 0:
                stood[party].append(code)
    out = []
    for party, codes in stood.items():
        for code in codes:
            baseline = levels._citywide(
                f"data/raw/elections/npe{npe}_{code}_vd_party.csv")
            if baseline.get(party, 0.0) > 0:
                continue                      # has a record: not an arrival
            out.append((party, code, codes))
    return out, votes


def report() -> str:
    lines = ["contested-area conversion, median |log(estimate / actual)|", ""]
    lines.append(f"{'':>6} {'n':>5} {'raw(8-metro)':>13} {'raw(national)':>14} "
                 f"{'adjusted':>9} {'single-metro':>13} {'MULTI only':>11}")
    for lge, npe in TRANSITIONS:
        found, votes = arrivals(lge, npe)
        cast = polling.votes_by_metro(lge)
        national = polling.NATIONAL_VOTES[lge]
        metro_total = sum(cast.values())
        raw_m, raw_n, adj, multi, single = [], [], [], [], 0
        for party, code, codes in found:
            actual = votes[code][party] / cast[code]
            total = sum(votes[k].get(party, 0) for k in codes)
            held = sum(cast.get(k, 0.0) for k in codes)
            if actual <= 0 or total <= 0 or held <= 0:
                continue
            # The national figure cancels here — see the module docstring.
            estimate = total / held
            raw_m.append(abs(math.log((total / metro_total) / actual)))
            raw_n.append(abs(math.log((total / national) / actual)))
            adj.append(abs(math.log(estimate / actual)))
            if len(codes) == 1:
                single += 1
            else:
                multi.append(adj[-1])
        lines.append(
            f"{lge:>6} {len(adj):>5} {st.median(raw_m):>13.3f} "
            f"{st.median(raw_n):>14.3f} {st.median(adj):>9.3f} "
            f"{single:>6} ({single / len(adj):>3.0%}) {st.median(multi):>11.3f}")
    lines += [
        "",
        "  `adjusted` and `single-metro` are the docstring's two columns and its",
        "  own caveat. A single-metro arrival is EXACT BY IDENTITY, so it",
        "  contributes a hard zero; at 2016 the majority are single-metro and the",
        "  median is one of those zeros.",
        "  `MULTI only` is the honest figure for the mechanism — the cases where",
        "  the conversion does any work. MODEL-LOG §1.66.",
    ]
    return "\n".join(lines)


def main() -> int:
    print(report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
