"""The city is a parameter, not an assumption.

Phase 1 hard-coded Johannesburg into every script: municipality codes,
council size, the party universe, and — most dangerously — a set of
*judgements* (bloc membership, θ ranges, national-to-local shift ranges)
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
    constant within a city (Johannesburg's was 260 in 2011, 270 since).

``[parties]``
    The party universe carried individually, with display names, chips and
    order. Replaces four parallel copies that used to live in the renderers.

``[judgements]``
    The per-city calls. Every entry should carry a `*_note` explaining the
    evidence behind it; `derive_city.py` proposes values from that city's
    own history for a human to accept or override.

Usage::

    from cityconfig import load
    city = load("joburg")
    city.council            # 270
    city.path("elections", "lge2021_{CODE}_vd_party_clean.csv")
    city.blocs              # {"ANC_BLOC": (...), "DA_BLOC": (...)}
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CITIES_DIR = Path("cities")
DEFAULT_CITY = "joburg"


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
    def council(self) -> int:
        return int(self.structure["council"])

    @property
    def majority(self) -> int:
        return self.council // 2 + 1

    @property
    def wards(self) -> int:
        return int(self.structure["wards"])

    # --- judgements -----------------------------------------------------
    @property
    def blocs(self) -> dict[str, tuple[str, ...]]:
        return {k: tuple(v) for k, v in self.judgements["blocs"].items()}

    @property
    def plan_bounds(self) -> dict[str, tuple[float, float]]:
        return {k: (float(v[0]), float(v[1]))
                for k, v in self.judgements["plan_bounds"].items()}

    def scenario_defaults(self) -> dict:
        """The judgement block in the shape montecarlo.DEFAULTS expects."""
        j = dict(self.judgements)
        j.pop("blocs", None)
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


def use(slug: str | None) -> City:
    """Set the active city for this process."""
    global _ACTIVE
    _ACTIVE = load(slug)
    return _ACTIVE


def active() -> City:
    global _ACTIVE
    if _ACTIVE is None:
        _ACTIVE = load()
    return _ACTIVE


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
