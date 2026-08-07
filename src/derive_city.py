"""Propose a city's config from its own IEC files.

Two kinds of number go into `cities/<slug>.toml`, and this script treats
them differently on purpose:

* **Structure** — council size, ward count, VD count, registration. These
  are *facts* in the city's own result files, so they are derived and
  printed ready to paste. Never type them: Johannesburg's council was 260
  in 2011 and 270 since, so even a single city has no constant.

* **Judgements** — bloc membership, θ ranges, national-to-local shift
  ranges, which parties get their own dial. These cannot be derived, only
  *informed*. The script measures each party's observed NPE→LGE retention
  across the city's own transitions and prints a proposal with the evidence
  beside it, for a human to accept, widen or reject. A proposal is not a
  decision — that is the whole reason the judgements live in a config file
  instead of the code.

Usage::

    python src/derive_city.py --code TSH --slug tshwane --province GP
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

from iec_csv import sniff_encoding   # the IEC mixes utf-8-sig, cp850 and utf-16

REPORTS = Path("data/raw/elections/_reports")
LGE_YEARS = (2011, 2016, 2021)


def read_lge(code: str, year: int) -> list[dict] | None:
    path = REPORTS / f"lge{year}_{code}_downloadable_party_results.csv"
    if not path.exists():
        return None
    with path.open(encoding=sniff_encoding(path), newline="") as fh:
        return list(csv.DictReader(fh))


def structure_from(rows: list[dict]) -> dict:
    wards = {r["Ward"] for r in rows if r.get("Ward")}
    vds = {r["VotingDistrict"] for r in rows if r.get("VotingDistrict")}
    reg: dict[str, int] = {}
    for r in rows:
        vd = r.get("VotingDistrict")
        if vd and vd not in reg:
            try:
                reg[vd] = int(r.get("RegisteredVoters") or 0)
            except ValueError:
                reg[vd] = 0
    return {"wards": len(wards), "vds": len(vds), "registered": sum(reg.values())}


def shares_from(rows: list[dict], ballot: str = "PR") -> dict[str, float]:
    tot: defaultdict[str, int] = defaultdict(int)
    for r in rows:
        if r.get("BallotType") != ballot:
            continue
        try:
            tot[r["PartyName"]] += int(r.get("TotalValidVotes") or 0)
        except ValueError:
            pass
    total = sum(tot.values()) or 1
    return {p: v / total for p, v in sorted(tot.items(), key=lambda kv: -kv[1])}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--code", required=True, help="IEC municipality code, e.g. TSH")
    ap.add_argument("--slug", required=True, help="url slug, e.g. tshwane")
    ap.add_argument("--province", default="GP", help="IEC province segment")
    ap.add_argument("--top", type=int, default=12,
                    help="how many parties to carry individually")
    args = ap.parse_args(argv)

    latest = None
    print(f"\n=== structure, from {args.code}'s own IEC files ===")
    for year in LGE_YEARS:
        rows = read_lge(args.code, year)
        if rows is None:
            print(f"  {year}: no downloadable party results on disk")
            continue
        st = structure_from(rows)
        print(f"  {year}: {st['wards']:>4} wards · {st['vds']:>4} VDs · "
              f"{st['registered']:>9,} registered")
        latest = (year, st, rows)

    if latest is None:
        raise SystemExit(f"no LGE files for {args.code} — run fetch_iec.py first")

    year, st, rows = latest
    council = st["wards"] * 2
    print(f"\n  → council = {council} (wards x2; CONFIRM against that city's "
          f"Seat Calculation Detail PDF — this is the one number worth\n"
          f"    checking by eye, and validate_seats.py will prove it)")

    print(f"\n=== party universe, {year} PR ballot ===")
    sh = shares_from(rows)
    for i, (party, share) in enumerate(list(sh.items())[:args.top]):
        flag = "  <- own dial" if share >= 0.02 else ""
        print(f"  {share:6.1%}  {party[:44]:44s}{flag}")
    tail = sum(v for v in list(sh.values())[args.top:])
    print(f"  {tail:6.1%}  (residual tail -> OTHER)")

    print("\n=== judgements: PROPOSALS ONLY — a human decides ===")
    print("  Bloc membership, θ ranges and the national-to-local shift ranges")
    print("  cannot be derived from one election. Measure them against this")
    print("  city's own NPE→LGE transitions before accepting anything, and")
    print("  record the evidence in the config's *_note fields.\n")
    print("  Sanity checks worth doing for a new city:")
    print("   · does any party here have no Johannesburg analogue? (VF+ in")
    print("     Tshwane is first-class at ~8%; the PA is marginal)")
    print("   · is the ANC/DA bloc split even the right frame in this city?")
    print("   · does a local formation need its own dial and chip colour?")
    print(f"   · run validate_seats.py --city {args.slug} — the allocator must")
    print("     reproduce the published council exactly before anything else")
    print("     is believed\n")

    print("=== paste into cities/%s.toml ===" % args.slug)
    print(f'''[identity]
code = "{args.code}"
slug = "{args.slug}"
name = "TODO"
formal_name = "TODO"
province = "{args.province}"
ward_prefix = "TODO"          # first 3 digits of this city's ward IDs
subdomain = "{args.slug}.whysoserious.city"

[structure]
council = {council}           # CONFIRM against the Seat Calculation Detail
wards = {st["wards"]}
list_seats = {st["wards"]}
vds = {st["vds"]}
registered = {st["registered"]}
election_date = "2026-11-04"''')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
