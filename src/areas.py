"""Named groups of a city's wards, generated from raw files and checked.

A claim about "Soweto" needs a list of wards, and no IEC or MDB file names
Soweto: it is not a ward, a region code or a voting-district field. The list is
therefore a judgement (JUDGEMENT-CALLS.md §P2), and this module is its ONE
DEFINITION. It derives the list from the raw files and writes it, with the rule
that produced it, into ``cities/<city>.toml`` ``[areas.<name>]``. The pages read
that table; ``tests/test_areas.py`` regenerates the list from the raw files and
compares, so the committed list cannot drift from its rule.

    .venv/bin/python src/areas.py --check   # exit 1 if the committed table differs
    .venv/bin/python src/areas.py --write   # rewrite the table from the raw files

The rule, for Soweto (owner-accepted, 2026-10-07): a 2026 ward is a Soweto ward
if at least ``SOWETO_CUT`` of its registered voters are in voting districts
whose IEC voting-station address names Soweto or a Soweto township
(``SOWETO_GAZETTEER``), and the address names none of ``SOWETO_EXCLUDE``.
Registration is ``part_registered`` from the VD -> 2026 ward crosswalk, read by
``montecarlo.read_ward_crosswalk`` (the one reader), so a voting district split
between wards counts in each ward for its own part.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

import cityconfig

#: Place names that put a voting station in Soweto. Matched at the START of a
#: word in the station's address, after upper-casing and collapsing spaces, so
#: ``BRAAMFISCHER`` matches ``BRAAMFISCHERVILLE`` and ``DUBE`` does not match
#: inside another word. Braamfischerville's stations give ROODEPOORT as their
#: town, so it is in the set by this list and not by any address saying Soweto.
#: Owner-accepted judgement, JUDGEMENT-CALLS.md §P2.
SOWETO_GAZETTEER = (
    "SOWETO", "CHIAWELO", "TSHIAWELO", "DHLAMINI", "DLAMINI", "DIEPKLOOF",
    "DOBSONVILLE", "DOORNKOP", "DUBE", "EMDENI", "MNDENI", "EMNDENI", "JABAVU",
    "JABULANI", "JABULANE", "KLIPTOWN", "KLIPSPRUIT", "MAPETLA", "MEADOWLANDS",
    "MMESI", "MOFOLO", "MOLAPO", "MOLETSANE", "MOROKA", "NALEDI", "ORLANDO",
    "PHIRI", "PIMVILLE", "PROTEA GLEN", "PROTEA NORTH", "PROTEA SOUTH",
    "PROTEA CITY", "SENAOANE", "TLADI", "WHITE CITY", "WHITECITY", "ZOLA",
    "ZONDI", "LUFHERENG", "SLOVOVILLE", "GLEN RIDGE", "GLENRIDGE",
    "BRAAMFISCHER", "BRAAM FISCHER",
)
#: An address naming one of these is NOT a Soweto station, whatever else it
#: names: Klipspruit West and Eldorado Park border Soweto and are not part of
#: it. Same matching rule as the gazetteer.
SOWETO_EXCLUDE = ("KLIPSPRUIT WEST", "ELDORADO")
#: The share of a ward's registered voters that must be at Soweto stations for
#: the ward to be a Soweto ward. A share exactly at the cut is in.
SOWETO_CUT = 0.5

#: The areas this module can derive: (city, area) -> where its inputs are.
#: ``{CODE}`` is the city's IEC code (cityconfig.resolve_path).
AREAS = {
    ("joburg", "soweto"): {
        "label": "Soweto",
        "stations": "data/raw/geo/votingstations2026_{CODE}.geojson",
        "year": "2026",
        "gazetteer": SOWETO_GAZETTEER,
        "exclude": SOWETO_EXCLUDE,
        "cut": SOWETO_CUT,
    },
}


def _norm(text: str) -> str:
    return " ".join(str(text or "").upper().split())


def _names(address: str, terms) -> bool:
    return any(re.search(r"\b" + re.escape(_norm(t)), address) for t in terms)


def address_in_area(address: str, gazetteer, exclude) -> bool:
    """Whether a station address names the area: a gazetteer term at the start
    of a word, and no excluded term."""
    a = _norm(address)
    return _names(a, gazetteer) and not _names(a, exclude)


def station_vds(stations: Path, gazetteer, exclude) -> tuple[set[str], set[str]]:
    """(voting districts whose station address names the area, every voting
    district in the file). One station per voting district, or it refuses."""
    features = json.loads(Path(stations).read_text(encoding="utf-8"))["features"]
    seen: set[str] = set()
    inside: set[str] = set()
    for f in features:
        p = f["properties"]
        vd = str(int(p["VOTINGDIST"]))
        if vd in seen:
            raise SystemExit(f"{stations}: voting district {vd} has two stations; "
                             f"which address it takes would be a guess")
        seen.add(vd)
        if address_in_area(p.get("ADDRESS"), gazetteer, exclude):
            inside.add(vd)
    return inside, seen


def area_wards(parts, inside: set[str], cut: float) -> list[int]:
    """The wards with at least ``cut`` of their registered voters in ``inside``.

    ``parts`` is ``[(vd, ward, registered), ...]``, one row per VD/ward part,
    as ``montecarlo.read_ward_crosswalk`` returns it."""
    total: dict[str, int] = defaultdict(int)
    held: dict[str, int] = defaultdict(int)
    for vd, ward, registered in parts:
        total[ward] += registered
        if vd in inside:
            held[ward] += registered
    empty = sorted(w for w, n in total.items() if n <= 0)
    if empty:
        raise SystemExit(f"ward(s) {empty} have no registered voters, so their "
                         f"share in the area is undefined")
    return sorted(int(w) for w in total if held[w] / total[w] >= cut)


def roll_share(parts, wards) -> float:
    """The share of the city's registered voters in ``wards``."""
    wards = {str(w) for w in wards}
    total = sum(r for _vd, _w, r in parts)
    return sum(r for _vd, w, r in parts if w in wards) / total


def crosswalk_parts(city: str, year: str):
    """The VD -> ward parts for a city's target year, through the one reader.
    It builds its own Target, so the process's active city and target stay as
    the caller set them."""
    import montecarlo
    target = cityconfig.Target(city=cityconfig.load(city), year=str(year))
    parts, _n_vds, _split = montecarlo.read_ward_crosswalk(target.crosswalk, str(year))
    return parts


def stations_path(city: str, area: str) -> Path:
    """The station file an area is derived from, with the city's code filled in."""
    code = cityconfig.load(city).code
    return Path(AREAS[(city, area)]["stations"].replace("{CODE}", code))


def derive(city: str, area: str, parts=None, stations: Path | None = None) -> list[int]:
    """The area's wards, from the raw files. ``parts`` and ``stations`` let a
    test hand in constructed inputs."""
    spec = AREAS[(city, area)]
    if parts is None:
        parts = crosswalk_parts(city, spec["year"])
    if stations is None:
        stations = stations_path(city, area)
    inside, every = station_vds(stations, spec["gazetteer"], spec["exclude"])
    unplaced = sorted({vd for vd, _w, _r in parts} - every)
    if unplaced:
        raise SystemExit(f"{len(unplaced)} voting district(s) in the crosswalk have no "
                         f"station in {stations} (first: {unplaced[:5]}); their "
                         f"voters cannot be placed in or out of {spec['label']}")
    return area_wards(parts, inside, spec["cut"])


def committed(city: str, area: str, cities_dir: Path | None = None) -> list[int] | None:
    """The ward list committed in ``cities/<city>.toml``, or None if absent."""
    raw = cityconfig.load(city, cities_dir).raw
    table = raw.get("areas", {}).get(area)
    return None if table is None else [int(w) for w in table["wards"]]


def check(city: str, area: str, cities_dir: Path | None = None,
          derived: list[int] | None = None) -> tuple[list[int] | None, list[int]]:
    """(committed, derived): equal when the committed table follows its rule."""
    derived = derive(city, area) if derived is None else derived
    return committed(city, area, cities_dir), derived


def section_text(city: str, area: str, wards: list[int]) -> str:
    """The ``[areas.<area>]`` table exactly as ``--write`` writes it."""
    spec = AREAS[(city, area)]
    lines = ", ".join(str(w) for w in wards)
    return (
        f"[areas.{area}]\n"
        f"# GENERATED by src/areas.py --write from the voting-station addresses\n"
        f"# and the VD -> ward crosswalk; tests/test_areas.py regenerates it and\n"
        f"# compares. Do not edit by hand: change the rule in src/areas.py.\n"
        f'label = "{spec["label"]}"\n'
        f"wards = [{lines}]\n"
        f"cut = {spec['cut']}\n"
        f'derivation = "A {spec["year"]} ward is in {spec["label"]} if at least the '
        f"cut share of its registered voters (vd_ward_{spec['year']}.csv "
        f"part_registered, split voting districts counted by part) are in voting "
        f"districts whose IEC voting-station address names a place in "
        f"src/areas.py's gazetteer, matched at the start of a word, and none of "
        f'its exclusions. JUDGEMENT-CALLS.md section P2."\n')


def write(city: str, area: str, wards: list[int], path: Path | None = None) -> Path:
    """Replace (or append) the ``[areas.<area>]`` table in the city's TOML."""
    path = path or (cityconfig.CITIES_DIR / f"{city}.toml")
    text = path.read_text(encoding="utf-8")
    block = section_text(city, area, wards)
    header = f"[areas.{area}]"
    if header in text:
        start = text.index(header)
        nxt = re.search(r"^\[", text[start + len(header):], re.M)
        end = start + len(header) + nxt.start() if nxt else len(text)
        text = text[:start] + block + ("\n" if nxt else "") + text[end:]
    else:
        text = text.rstrip("\n") + "\n\n" + block
    path.write_text(text, encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--area", default="soweto")
    cityconfig.add_city_argument(ap)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)
    city = getattr(args, "city", None) or cityconfig.DEFAULT_CITY
    wards = derive(city, args.area)
    if args.write:
        print(f"wrote {len(wards)} wards to {write(city, args.area, wards)}")
        return 0
    have, wards = check(city, args.area, derived=wards)
    if have != wards:
        print(f"[areas.{args.area}] in cities/{city}.toml differs from its rule:\n"
              f"  committed: {have}\n  derived:   {wards}")
        return 1
    print(f"[areas.{args.area}]: {len(wards)} wards, as committed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
