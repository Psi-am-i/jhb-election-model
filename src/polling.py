"""Polls, filtered by date and converted from national numbers to metro ones.

A party with no electoral history cannot be forecast from a record it does not
have. Scored across nine city-years, this model gives a median seat to ONE of
the thirty-two parties that arrived from nothing and won one (``src/arrivals.py``),
14 seats against 130 — and no tuning of the arrival machinery reaches the gap,
because the machinery is extrapolating from splits that were an order of
magnitude smaller. Polls are the only pre-election evidence that exists for such
a party, which is the literature's unanimous position and this repository's own
measurement.

THE OBSTACLE, AND THE ARITHMETIC THAT REMOVES IT
------------------------------------------------

Published South African polls are NATIONAL and this model forecasts a metro. The
conversion is not a modelling assumption, it is arithmetic on two public facts.

If a party takes ``X`` of a territory's vote but stands only in municipalities
holding share ``s`` of that territory, then its average share **where it stands**
is ``X / s``. The poll supplies ``X``; nomination lists — which close weeks
before polling day — supply which municipalities, and the published roll supplies
their size. Nothing here is read from the result.

Measured against every arrival in the eight-metro archive, as the median
absolute log ratio between estimate and actual metro share::

                         raw national share    contested-area adjusted
    2016 (83 arrivals)            1.609                 0.000
    2021 (175 arrivals)           1.228                 0.144

2016 is trivially exact because nearly every arrival stood in a single metro;
2021 is the real test, and it is an order of magnitude.

WHAT IT DOES AND DOES NOT BUY
-----------------------------

Feeding the one independent pre-2021 poll — Ipsos, 16-20 August 2021, ActionSA at
1.5% national — the conversion gives about 6.3% wherever ActionSA stood::

    metro           poll + conversion    model (no poll)    actual
    Johannesburg           6.3%               6.4%          18.12%
    Tshwane                6.3%               1.5%           9.28%
    Ekurhuleni             6.3%               1.5%           7.36%
    eThekwini              6.3%               1.5%           2.35%

Better in two metros, far better in one, worse in one. **Nothing available would
have called Johannesburg**, and this does not pretend to: the conversion yields
the average where a party stands, and distributing it between metros still needs
the home-city effect. What it removes is the model's silence in the metros where
it currently says 1.5% and the answer was seven or nine.

TWO RULES ABOUT WHICH POLLS COUNT
---------------------------------

**Fieldwork dates are machine-readable and enforced.** A poll may only inform a
target if its fieldwork ENDED before that target's polling day. The register
previously stored dates as free text ("8-31 July 2026"), which no backtest can
filter on — a temporal leak waiting to happen in a repository that has spent
weeks removing them.

**Party-commissioned polls are excluded**, and the evidence is in the same
election. ActionSA commissioned a poll reporting it "on course to win Joburg";
it finished third on 16.05%. The one independent poll had the party low by a
factor of 1.6. Admitting the first and excluding the second would have been
worse than having no poll at all.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import cityconfig

REGISTER = Path("polls.json")

# Registered voters nationally, per local election. Needed as the denominator of
# the contested-area conversion and NOT derivable from anything on disk: the
# archive holds eight metros, not the country. Sourced from the IEC's published
# figures as reported in Wikipedia's "<year> South African municipal elections",
# and recorded here rather than typed at a call site so a wrong one is findable.
# VOTES CAST, not registration: the conversion's numerator is a share of the
# vote, so its denominator must be too. Mixing the two understates the
# territory by the turnout ratio and inflates every estimate by about 2x.
NATIONAL_VOTES = {
    # roll x turnout, both as published by the IEC.
    "2016": int(26_333_353 * 0.5794),
    "2021": int(26_204_579 * 0.4579),
    # 2026 is not yet known; registration closes with the voters' roll for the
    # election. Until then the conversion cannot run for a 2026 target and says
    # so rather than guessing.
}


def load(path: Path = REGISTER) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("polls", [])


def usable_for(target: cityconfig.Target, polls: list[dict] | None = None,
               allow_commissioned: bool = False) -> list[dict]:
    """Polls whose fieldwork ended before this target's polling day.

    Anything without a machine-readable ``fieldwork_end`` is REFUSED rather than
    parsed leniently. A poll that cannot be dated cannot be shown to precede the
    election it is informing, and "probably before" is not a standard this
    repository applies anywhere else.
    """
    out = []
    for poll in (polls if polls is not None else load()):
        end = poll.get("fieldwork_end")
        if not end:
            continue
        try:
            when = date.fromisoformat(str(end))
        except ValueError:
            continue
        if when >= target.date:
            continue
        if poll.get("commissioned_by") and not allow_commissioned:
            continue
        out.append(poll)
    return out


def contested_share(codes: list[str], year: str,
                    roll: dict[str, float] | None = None) -> float | None:
    """What fraction of the national roll sits in the municipalities listed.

    ``roll`` maps IEC code to registered voters; supplying it keeps this
    testable. Returns None when the national figure for that year is unknown,
    because a conversion with a guessed denominator is worse than none.
    """
    national = NATIONAL_VOTES.get(str(year))
    if not national or not codes:
        return None
    if roll is None:
        roll = votes_by_metro(year)
    held = sum(roll.get(c, 0.0) for c in codes)
    return (held / national) if held > 0 else None


def votes_by_metro(year: str) -> dict[str, float]:
    """Votes cast per metro on the PR ballot, from the published result files."""
    import pools as PL
    from ingest_lge import read_municipality

    out: dict[str, float] = {}
    for code in PL.METRO_CODES:
        path = PL.metro_file(code, year)
        if path is None:
            continue
        total = 0
        for row in read_municipality(path, code, "PR"):
            total += int(row["Party_Votes"] or 0)
        if total:
            out[code] = total
    return out


def metro_estimate(poll: dict, party: str, contests: list[str], year: str,
                   roll: dict[str, float] | None = None) -> dict | None:
    """A national poll number converted to a share of each contested metro.

    Returns ``{"share": s, "contested_share": t, "basis": ...}`` or None when
    the poll does not carry the party, or the denominator cannot be formed.

    The estimate is the party's AVERAGE across everywhere it stands. It is not a
    per-metro forecast and must not be presented as one: ActionSA's 9.78% by this
    route sat against actuals of 18.12%, 9.28%, 7.36% and 2.35%.
    """
    share = (poll.get("numbers") or {}).get(party)
    if share is None or poll.get("scope") != "national":
        return None
    t = contested_share(contests, year, roll)
    if not t:
        return None
    return {"share": float(share) / t, "contested_share": t,
            "national": float(share), "poll": poll.get("id"),
            "basis": (f"{poll.get('house')} {poll.get('fieldwork_end')}: "
                      f"{share:.1%} national, contesting municipalities holding "
                      f"{t:.1%} of the roll")}
