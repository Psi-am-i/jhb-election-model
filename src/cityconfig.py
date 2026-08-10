"""The city and the target election are parameters, not assumptions.

Phase 1 hard-coded Johannesburg into every script: municipality codes,
council size, the party universe, and — most dangerously — a set of
*judgements* (θ ranges, national-to-local shift ranges)
that were derived from CoJ history. Applied blind to another metro those
judgements do not crash; they produce plausible, wrong output. So they live
in a config file where they can be seen, sourced and argued with.

Each city is `cities/<slug>.toml` with four sections:

``[identity]``
    Codes and names, including the IEC's own quirks — Nelson Mandela Bay is
    ``NMA`` (not NMB) and the province path segments are ``WP`` for Western
    Cape and ``KN`` for KwaZulu-Natal.

``[structure]``
    Council size, ward count, majority. **Derived from that city's IEC
    files by `derive_city.py`, never typed** — council size is not even
    constant within a city (Johannesburg's was 260 in 2011, 270 since), so
    the block carries a ``[structure.by_year.<year>]`` table and the numbers
    resolve against whichever election is being *targeted*.

``[parties]``
    The party universe carried individually, with display names, chips and
    order. Replaces four parallel copies that used to live in the renderers.

``[judgements]``
    The per-city calls. Every entry should carry a `*_note` explaining the
    evidence behind it; `derive_city.py` proposes values from that city's
    own history for a human to accept or override.

The second axis is time. A forecast for 2026 that has read 2024 is a
forecast; a forecast for 2021 that has read 2024 is not — it is a memory
wearing a forecast's clothes, and it will score beautifully. So the target
election is selected the same way the city is (``--target``), and everything
that depends on when it is — the polling day, the council's size, which
elections count as evidence, where the outputs land — hangs off that one
choice rather than off constants scattered through the producers.

Usage::

    from cityconfig import load
    city = load("joburg")
    city.council            # 270
    city.path("elections", "lge2021_{CODE}_vd_party_clean.csv")

    import cityconfig
    cityconfig.use("joburg")
    t = cityconfig.use_target("2021")
    t.previous_npe          # "2019"
    t.council               # 270  (260 had the target been 2011)
    t.before                # ("1999", "2000", ... "2019")
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from datetime import date as _date
from pathlib import Path

CITIES_DIR = Path("cities")
DEFAULT_CITY = "joburg"


# --------------------------------------------------------------------------
# the time axis
#
# South Africa votes on one nationwide day, so the calendar is a national fact
# and not a per-city one — duplicating it into every cities/*.toml would just
# create eleven places for it to drift. It is also NOT derivable from the
# result files: the IEC's VD-level exports carry no date column at all. So the
# polling days are recorded here once. byelections.py reads two of these dates
# directly — the target's and the preceding LGE's — as the bounds of the window
# a contest has to fall in to count, so a wrong date here silently widens or
# narrows that window rather than raising.
#
# `kind` doubles as the ballot structure: an LGE runs two ballots (ward and
# PR) where an NPE runs one, which is what read_turnout() has to know.
# `results` is the {CODE} template for that election's VD-level result file —
# None for an election not yet held.
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Election:
    year: str
    kind: str                    # "NPE" or "LGE"
    date: _date
    results: str | None = None

    @property
    def two_ballot(self) -> bool:
        return self.kind == "LGE"


CALENDAR: dict[str, Election] = {
    # 1999 is the approximate pre-metro footprint (see ingest_historic.py).
    "1999": Election("1999", "NPE", _date(1999, 6, 2), "npe1999_approx_{CODE}_vd_party.csv"),
    "2000": Election("2000", "LGE", _date(2000, 12, 5), "lge2000_{CODE}_vd_party_clean.csv"),
    "2004": Election("2004", "NPE", _date(2004, 4, 14), "npe2004_{CODE}_vd_party.csv"),
    "2006": Election("2006", "LGE", _date(2006, 3, 1), "lge2006_{CODE}_vd_party_clean.csv"),
    "2009": Election("2009", "NPE", _date(2009, 4, 22), "npe2009_{CODE}_vd_party.csv"),
    "2011": Election("2011", "LGE", _date(2011, 5, 18), "lge2011_{CODE}_vd_party_clean.csv"),
    "2014": Election("2014", "NPE", _date(2014, 5, 7), "npe2014_{CODE}_vd_party.csv"),
    "2016": Election("2016", "LGE", _date(2016, 8, 3), "lge2016_{CODE}_vd_party_clean.csv"),
    "2019": Election("2019", "NPE", _date(2019, 5, 8), "npe2019_{CODE}_vd_party.csv"),
    "2021": Election("2021", "LGE", _date(2021, 11, 1), "lge2021_{CODE}_vd_party_clean.csv"),
    "2024": Election("2024", "NPE", _date(2024, 5, 29), "npe2024_{CODE}_vd_party.csv"),
    # Not yet held: no result file, and the date is the announced polling day,
    # which each city's [structure].election_date may override.
    "2026": Election("2026", "LGE", _date(2026, 11, 4), None),
}


@dataclass
class City:
    slug: str
    raw: dict
    identity: dict = field(default_factory=dict)
    structure: dict = field(default_factory=dict)
    parties: dict = field(default_factory=dict)
    judgements: dict = field(default_factory=dict)
    newsdesk: dict = field(default_factory=dict)
    site: dict = field(default_factory=dict)
    # Which election the size properties below describe. Set by use_target();
    # None means "this city's next one". It lives on the City so that the ~6
    # call sites reading city.council keep working unchanged once a target has
    # been selected, rather than every one of them growing a target argument.
    target_year: str | None = None

    # --- identity -------------------------------------------------------
    @property
    def code(self) -> str:
        return self.identity["code"]

    @property
    def name(self) -> str:
        return self.identity["name"]

    @property
    def province(self) -> str:
        return self.identity["province"]

    @property
    def ward_prefix(self) -> str:
        """Ward-ID prefix used to pick this city out of national files."""
        return str(self.identity["ward_prefix"])

    # --- structure ------------------------------------------------------
    @property
    def default_target(self) -> str:
        """This city's next election — the year of ``[structure].election_date``.

        Read off the config rather than added as a second key, so there is no
        way for the two to disagree.
        """
        return str(_date.fromisoformat(str(self.structure["election_date"])).year)

    def structure_for(self, year: str | None = None) -> dict:
        """The structure block as it stood at `year`.

        The top-level ``[structure]`` keys describe the default target (the
        next election). Every other year must have its own
        ``[structure.by_year.<year>]`` entry, and the absence of one is an
        error rather than a silent fall-through: inheriting 2026's 270-seat
        council into a 2011 backtest would not crash, it would quietly score
        the model against a council that did not exist.
        """
        year = str(year or self.target_year or self.default_target)
        base = {k: v for k, v in self.structure.items() if k != "by_year"}
        if year == self.default_target:
            return base
        by_year = self.structure.get("by_year", {})
        if year not in by_year:
            known = ", ".join(sorted(by_year) + [self.default_target])
            raise SystemExit(
                f"{self.name}: no [structure.by_year.{year}] in "
                f"cities/{self.slug}.toml; council size and ward count for "
                f"{year} are unknown (have: {known})")
        return {**base, **by_year[year]}

    @property
    def council(self) -> int:
        return int(self.structure_for()["council"])

    @property
    def majority(self) -> int:
        return self.council // 2 + 1

    @property
    def wards(self) -> int:
        return int(self.structure_for()["wards"])

    # --- judgements -----------------------------------------------------
    @property
    def plan_bounds(self) -> dict[str, tuple[float, float]]:
        return {k: (float(v[0]), float(v[1]))
                for k, v in self.judgements["plan_bounds"].items()}

    def scenario_defaults(self) -> dict:
        """The judgement block in the shape montecarlo.DEFAULTS expects."""
        j = dict(self.judgements)
        j.pop("plan_bounds", None)
        return {k: v for k, v in j.items() if not k.endswith("_note")}

    # --- paths ----------------------------------------------------------
    def path(self, *parts: str, root: str = "data") -> Path:
        """Build a data path, substituting this city's code.

        Replaces the ~14 hard-coded ``_JHB_`` filename literals that were
        scattered across the pipeline.
        """
        out = Path(root)
        for part in parts:
            out = out / part.replace("{CODE}", self.code).replace("{SLUG}", self.slug)
        return out

    @property
    def processed(self) -> Path:
        """Per-city processed outputs; Johannesburg keeps the legacy path."""
        if self.raw.get("legacy_processed_root", False):
            return Path("data/processed")
        return Path("data/processed") / self.slug

    @property
    def content(self) -> Path:
        return Path("content") / self.slug


def preceding(year: str | int, kind: str) -> str | None:
    """The last election of `kind` strictly before `year`, or None.

    Calendar-only: it says nothing about whether that election's files were
    ingested for any particular city.

    Sorted rather than trusting CALENDAR's insertion order: appending an older
    election the natural way (``"1995": ...`` at the end of the literal) would
    otherwise make ``preceding("2000", "NPE")`` return 1995 instead of 1999,
    and turnout.py's LAMBDA_PAIRS["2000"] would silently become ("1995",
    "2000") — no error, wrong numbers. Years are zero-padded four-digit
    strings, so lexicographic order is chronological order.
    """
    for candidate in sorted((y for y in CALENDAR if y < str(year)), reverse=True):
        if CALENDAR[candidate].kind == kind:
            return candidate
    return None


@dataclass(frozen=True)
class Target:
    """One city building one election.

    The city axis answers "whose ballots"; this answers "as of when". Every
    producer that is ever going to be backtested needs the second, because a
    forecast for 2021 that has seen 2024's results is not a forecast.
    """

    city: City
    year: str

    def __post_init__(self) -> None:
        if self.year not in CALENDAR:
            raise SystemExit(f"unknown target election {self.year!r}; have: "
                             f"{', '.join(CALENDAR)}")

    # --- when -----------------------------------------------------------
    @property
    def election(self) -> Election:
        return CALENDAR[self.year]

    @property
    def kind(self) -> str:
        return self.election.kind

    @property
    def date(self) -> _date:
        """Polling day. The city's own ``election_date`` wins where it has one
        — that is the announced date for a poll not yet held, which can move."""
        own = self.city.structure_for(self.year).get("election_date")
        if own and str(_date.fromisoformat(str(own)).year) == self.year:
            return _date.fromisoformat(str(own))
        return self.election.date

    @property
    def before(self) -> tuple[str, ...]:
        """Elections strictly before this one, oldest first.

        This is the national calendar, not what is on disk: the pre-2011
        archives were only ingested for Johannesburg, and a city whose record
        starts late is a gap in the record rather than a different calendar.
        Callers intersect this with the files they actually find.

        Sorted for the same reason ``preceding()`` is: "oldest first" is a
        promise consumers rely on, and CALENDAR's insertion order is not a
        mechanism for keeping it.
        """
        return tuple(sorted(y for y in CALENDAR if y < self.year))

    @property
    def previous_lge(self) -> str | None:
        """The last local election before this one — the ward delimitation and
        the local baseline a local forecast is built on."""
        return preceding(self.year, "LGE")

    @property
    def previous_npe(self) -> str | None:
        """The last national election before this one — the freshest party
        geography available, and the level λ̂ is applied to."""
        return preceding(self.year, "NPE")

    def results(self, year: str) -> str:
        """The {CODE} template for one election's VD-level result file."""
        name = CALENDAR[year].results
        if name is None:
            raise SystemExit(f"{year} has no result file: it has not been held")
        return name

    # --- how big --------------------------------------------------------
    @property
    def structure(self) -> dict:
        return self.city.structure_for(self.year)

    @property
    def council(self) -> int:
        return int(self.structure["council"])

    @property
    def wards(self) -> int:
        return int(self.structure["wards"])

    @property
    def list_seats(self) -> int:
        return int(self.structure["list_seats"])

    @property
    def majority(self) -> int:
        return self.council // 2 + 1

    # --- where ----------------------------------------------------------
    @property
    def processed(self) -> Path:
        """Per-target outputs: ``data/processed/<slug>/<target>/``.

        One exception, and it is a preservation rather than a rule: the city
        carrying ``legacy_processed_root`` building its own next election
        keeps the bare ``data/processed/``. Johannesburg's 2026 files are
        published from those paths and must not move.

        The exemption covers *that one target only*, not the city. Letting it
        cover the city would compose ``City.processed`` (bare
        ``data/processed/``) with the year and drop a backtest of 2021 into
        ``data/processed/2021/`` — a bare year directory sitting as a sibling
        of Johannesburg's published CSVs and of ``tshwane/``, indistinguishable
        from a top-level output. Every non-default target therefore lands under
        the city's own slug like anyone else's.
        """
        if self.city.raw.get("legacy_processed_root", False):
            if self.year == self.city.default_target:
                return self.city.processed
            return Path("data/processed") / self.city.slug / self.year
        return self.city.processed / self.year


def load(slug: str | None = None, cities_dir: Path | None = None) -> City:
    slug = slug or DEFAULT_CITY
    path = (cities_dir or CITIES_DIR) / f"{slug}.toml"
    if not path.exists():
        available = sorted(p.stem for p in (cities_dir or CITIES_DIR).glob("*.toml"))
        raise SystemExit(f"unknown city {slug!r}; have: {', '.join(available)}")
    with path.open("rb") as fh:
        raw = tomllib.load(fh)
    return City(slug=slug, raw=raw,
                identity=raw.get("identity", {}),
                structure=raw.get("structure", {}),
                parties=raw.get("parties", {}),
                judgements=raw.get("judgements", {}),
                newsdesk=raw.get("newsdesk", {}),
                site=raw.get("site", {}))


# --------------------------------------------------------------------------
# the active city
#
# The ingest chain names its inputs by municipality code
# ("lge2021_JHB_vd_party_clean.csv"). Rather than thread a city object
# through every reader, those literals become "{CODE}" templates and are
# resolved at the file-open boundary against whichever city is active.
# --------------------------------------------------------------------------

_ACTIVE: City | None = None
_TARGET: Target | None = None


def use(slug: str | None) -> City:
    """Set the active city for this process."""
    global _ACTIVE, _TARGET
    _ACTIVE = load(slug)
    _TARGET = None  # a different city has a different default target
    return _ACTIVE


def active() -> City:
    global _ACTIVE
    if _ACTIVE is None:
        _ACTIVE = load()
    return _ACTIVE


def use_target(year: str | int | None = None) -> Target:
    """Set the active target election; None means the active city's next one."""
    global _TARGET
    city = active()
    _TARGET = Target(city=city, year=str(year) if year else city.default_target)
    city.target_year = _TARGET.year
    return _TARGET


def target() -> Target:
    global _TARGET
    if _TARGET is None:
        use_target(None)
    assert _TARGET is not None
    return _TARGET


def resolve_path(path):
    """Substitute {CODE}/{SLUG} in a path or filename."""
    from pathlib import Path as _P
    text = str(path)
    if "{CODE}" in text or "{SLUG}" in text:
        city = active()
        text = text.replace("{CODE}", city.code).replace("{SLUG}", city.slug)
    return _P(text)


def add_city_argument(parser) -> None:
    """Standard ``--city`` flag; every script defaults to Johannesburg so
    existing commands keep working unchanged."""
    parser.add_argument("--city", default=DEFAULT_CITY,
                        help="city slug from cities/ (default: joburg)")


def add_target_argument(parser) -> None:
    """Standard ``--target`` flag: which election is being built.

    The default is deliberately None rather than a year. The real default is
    *the active city's* next election, and --city has not been parsed yet when
    the parser is being built — so resolution happens in ``use_target(None)``
    after parsing, the same way turnout.py's --out already resolves.
    """
    parser.add_argument("--target", default=None, metavar="YEAR",
                        help="election to build, using only evidence from "
                             "before it (default: the city's next election)")
