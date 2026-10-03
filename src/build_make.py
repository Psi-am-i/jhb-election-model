"""Section 2 of "your forecast" ("Break the model"): its data and its start.

``src/build_your_forecast.py`` assembles the page (``/your-forecast/``) and
copies its files; ``build_site.main`` renders, scans, stamps and ledgers it.
This module writes the one data file section 2 reads and states where it
starts; it decides nothing about what is allowed on a page. Anonymous: the
reader's forecast lives in the page's address (``js/make-state.js``, through
``js/yf-url.js``).

``your-forecast/forecast.json``
    The one data file section 2 reads (:func:`forecast_data`): the generated
    schema (``worker-api/tools/make_schema.mjs``'s own ``build``, run on the
    artefact :func:`model_artefact` writes from the published draws), the ward
    geometry, and the start state.
``your-forecast/js/seats.js``, ``http.js``
    Copied from ``worker-api/src`` (``WORKER_API_JS``) beside
    ``seat-engine.js``, whose ONE declared import line (``SEATS_LINE``) is
    rewritten to them. Both run only inside section 2's Web Worker, which the
    number gate does not follow (it cannot touch the page).

The start state, stated exactly
===============================

* **Ward calls**: the modal winner of each ward over the published draws'
  ``ward_winner`` block (``site/draws/``), by
  ``score_forecasts.model_forecast``: the one definition of "the model as a
  reader who changed nothing". It is the ``winner`` column of
  ``ward_winner_probs.csv`` that the forecast page's map passes to
  ``render_map.ward_call`` wherever that column has no tie
  (``tests/test_your_forecast_page.py``).
* **Vote shares**: chosen so that the untouched council, under the seat law
  (``reader_seats``), gives each party the published seat panel names its
  middle seat count, or its ward count where that is higher, and the other
  parties the rest of the council (``start_rule.start_seats``, then
  ``start_rule.start_shares``: the one definition, which the page also runs
  on the reader's weighted draws when section 1 hands its forecast on). There is no published combined (ward + list) share
  to start from: the draws' manifest refuses one
  (``export_draws.COMBINED_SHARE_REFUSAL``), and the list-ballot medians,
  fed in as the combined vote, open the council far from the forecast's
  middle (MODEL-LOG §1.270). The rule, in order:

  The rule, in order, is ``src/start_rule.py``'s docstring; here it runs
  with every draw counted once. The build runs ``reader_seats`` on the
  result and refuses to write a start it does not reproduce.

* **Total combined vote** (``reader_seats``' ``total_votes``, the schema's
  ``x-total-votes``): nothing published carries it. It is two ballots times
  the median over the draws of each draw's citywide votes cast, the sum over
  the four voter pools of the pool's registration (``pools_2026.json``) times
  the draw's pool turnout (the draws' ``pool_turnout`` block). Spoilt ballots
  are not taken off. It moves a seat only at a quota remainder boundary.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

import build_play
import start_rule

REPO_ROOT = Path(__file__).resolve().parents[1]
INTERACTIVE = REPO_ROOT / "interactive"
DRAWS = REPO_ROOT / "site" / "draws"
WORKER_SRC = REPO_ROOT / "worker-api" / "src"

#: The two worker-api files section 2's seat Worker imports, copied beside it.
WORKER_API_JS = ("seats.js", "http.js")
#: The one line of seat-engine.js that differs between the repository and the site.
SEATS_LINE = ('from "../../worker-api/src/seats.js";', 'from "./seats.js";')
#: The data file section 2 reads.
DATA = "forecast.json"


class MakeBuildError(SystemExit):
    """The page cannot be assembled; the message says what to do."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------------
# the start state


def _draws(draws: Path | None = None) -> tuple[dict, dict, bytes]:
    import reweight
    draws = DRAWS if draws is None else draws
    man_bytes = (draws / "manifest.json").read_bytes()
    manifest = json.loads(man_bytes)
    blob = (draws / "base.bin").read_bytes()
    return manifest, reweight.unpack(blob, manifest), man_bytes + blob


def _columns(manifest: dict, name: str) -> list[str]:
    return next(b for b in manifest["blocks"] if b["name"] == name)["columns"]


def total_votes(manifest: dict, arrays: dict, pools_file: Path) -> tuple[int, dict]:
    """``(total_votes, provenance)``; module docstring."""
    pools = json.loads(pools_file.read_text(encoding="utf-8"))["pools"]
    names = _columns(manifest, "pool_turnout")
    missing = [n for n in names if n not in pools]
    if missing:
        raise MakeBuildError(f"build_make: pools {missing} of the draws are not in {pools_file}")
    registered = np.array([float(pools[n]["registered"]) for n in names])
    cast = np.asarray(arrays["pool_turnout"], dtype=float) @ registered
    total = int(round(2 * float(np.median(cast))))
    return total, {
        "rule": ("two ballots times the median over the draws of the votes cast, "
                 "the sum over voter pools of registration times the draw's pool turnout; "
                 "spoilt ballots not taken off"),
        "pool_turnout": "site/draws/base.bin pool_turnout",
        "registration": str(pools_file.relative_to(REPO_ROOT)) if pools_file.is_relative_to(REPO_ROOT) else pools_file.name,
        "registration_sha256": _sha(pools_file.read_bytes()),
    }


def model_artefact(manifest: dict, total: int, roster: dict) -> dict:
    """The model artefact ``make_schema.mjs`` reads, from the published draws."""
    import cityconfig
    city = cityconfig.active()
    target = str(city.default_target)
    structure = city.structure_for(target)
    council = int(structure["council"])
    run = manifest["published_run"]["model_run_id"]
    parties = list(manifest["parties"])
    return {
        "model_ref": run,
        "city": city.slug,
        "target": target,
        "council_seats": council,
        "ward_seats": int(structure["wards"]),
        "majority": council // 2 + 1,
        "total_votes": total,
        "no_pr_list": [],
        "parties": [{"code": c, "name": roster[c]["name"], "colour": roster[c]["colour"]} for c in parties],
        "placeholder": False,
    }


def geometry() -> dict:
    """The ward geometry and compass sectors, by the prototype tool's own
    definition (``interactive/tools/make_fixtures.geometry``), without its
    date stamp so a rebuild is byte-stable."""
    sys.path.insert(0, str(INTERACTIVE / "tools"))
    try:
        import make_fixtures
    finally:
        sys.path.pop(0)
    geom = make_fixtures.geometry()
    geom.pop("_generated", None)
    geom["_about"] = ("The live site's ward geography (data/processed/ward_paths.json, "
                      "ward_hex_layout.json) with compass sectors derived by "
                      "interactive/tools/make_fixtures.sectors (DESIGN-decided §1).")
    return geom


def make_schema(artefact: dict, geom: dict) -> dict:
    """The generated schema, by ``worker-api/tools/make_schema.mjs``'s ``build``."""
    tool = REPO_ROOT / "worker-api" / "tools" / "make_schema.mjs"
    script = ("import { build } from " + json.dumps(tool.as_uri()) + ";\n"
              "let s = ''; process.stdin.on('data', d => s += d).on('end', () => {\n"
              "  const { model, geometry } = JSON.parse(s);\n"
              "  const out = build(Buffer.from(model), Buffer.from(geometry),\n"
              "    { model: 'make/forecast.json model artefact (build_make.model_artefact)',\n"
              "      geometry: 'make/forecast.json geometry (build_make.geometry)' });\n"
              "  process.stdout.write(out['generated/forecast.schema.json']);\n"
              "});\n")
    payload = json.dumps({"model": json.dumps(artefact, sort_keys=True),
                          "geometry": json.dumps(geom, sort_keys=True)})
    try:
        run = subprocess.run(["node", "--input-type=module", "-e", script], input=payload,
                             capture_output=True, text=True, cwd=REPO_ROOT)
    except FileNotFoundError:
        raise MakeBuildError("build_make: node is not installed, so the schema cannot be "
                             "generated by worker-api/tools/make_schema.mjs") from None
    if run.returncode:
        raise MakeBuildError(f"build_make: make_schema.mjs failed:\n{run.stderr}")
    return json.loads(run.stdout)


def start_plan(manifest: dict, arrays: dict, calls: list[str], weights=None) -> dict:
    """``start_rule.start_seats`` on the draws' statutory seats and council,
    each draw counted once unless ``weights`` are given."""
    council = np.asarray(arrays["council/deduct"], dtype=float)[
        :, _columns(manifest, "council/deduct").index("council_size")]
    try:
        return start_rule.start_seats(_columns(manifest, "seats/deduct"), arrays["seats/deduct"],
                                      council, calls, weights)
    except start_rule.StartRuleError as exc:
        raise MakeBuildError(f"build_make: {exc}") from None


def start_state(manifest: dict, arrays: dict, schema: dict) -> dict:
    """The model's central state as a reader forecast; module docstring."""
    import reader_seats
    import score_forecasts
    roster = list(schema["x-seat-context"]["parties"])
    wards = _columns(manifest, "ward_winner")
    codes = manifest["ward_parties"]
    winners = np.asarray(arrays["ward_winner"], dtype=np.int64)
    counts = np.zeros((len(wards), len(roster)), dtype=np.int64)
    col = {p: j for j, p in enumerate(roster)}
    for k, code in enumerate(codes):
        counts[:, col[code]] = (winners == k).sum(axis=0)
    # the ward calls by the scorer's rule (its shares are not used: see the
    # module docstring)
    flat = [[1.0 / len(roster)] * len(roster)]
    calls = score_forecasts.model_forecast(
        counts.tolist(), roster, wards, flat, roster, schema)["ward_calls"]
    context, total, target, _tol, ward_ids = score_forecasts.schema_context(schema)
    plan = start_plan(manifest, arrays, calls)
    share = start_rule.start_shares(plan["seats"], roster, total)
    got = reader_seats.reader_seats({p: v / 100 for p, v in share.items()}, dict(zip(ward_ids, calls)),
                                    context, total)
    if not got["ok"]:
        raise MakeBuildError(f"build_make: the start shares do not seat: {got['errors']}")
    seated = {p: v["total"] for p, v in got["seats"].items()}
    if seated != plan["seats"]:
        raise MakeBuildError(f"build_make: the start shares seat {seated}, not the targets {plan['seats']}")
    return {
        "ward_calls": calls,
        "combined_share": {p: v * target / 100 for p, v in share.items()},
        "seats": plan["seats"],
        "published_middle": plan["published"],
        "rule": ("ward calls: score_forecasts.model_forecast's modal winner over the published draws; "
                 "combined shares: each party's target seats' share of the council, the targets being "
                 "the published seat panel's middles, raised to the ward floor, with Others taking the "
                 "seats left to fill the council (src/start_rule.py start_seats)"),
    }


# --------------------------------------------------------------------------
# the previous council election, for "vs 2021" on the share cards


def baseline(city, roster: list[str]) -> dict:
    """The council election before the target, per roster party: what the
    share cards and the arrival view print "vs <year>" against.

    * ``seats``: the IEC's own Seat Calculation Detail (``official_seats.read``),
      each raw party name through ``parties.canonical``;
    * ``wards``: wards won, the plurality of each ward's Ward ballot in the
      city's VD result file;
    * ``vote``: each party's percent of all valid votes, PR and Ward ballots
      summed, from the same file.

    Only roster parties that stood are keyed: a party absent from ``vote``
    was not on that ballot, and the cards print "new" for it (owner,
    2026-10-03). A party that held seats then and is not on the roster now
    appears on no card. Refuses a file whose seats do not sum to that
    election's council or whose wards do not number its ward count."""
    import collections
    import csv
    import cityconfig
    import official_seats
    import parties as P
    year = cityconfig.preceding(city.default_target, "LGE")
    struct = city.structure_for(year)
    official = official_seats.read(city.code, int(year), REPO_ROOT / official_seats.REPORTS)
    if official is None:
        raise MakeBuildError(f"build_make: no {year} seat calculation for {city.name}")
    seats = collections.Counter()
    for raw, row in official["parties"].items():
        seats[P.canonical(raw)] += int(row["seats"])
    votes, by_ward = collections.Counter(), collections.defaultdict(collections.Counter)
    path = REPO_ROOT / city.path("raw", "elections", cityconfig.CALENDAR[year].results)
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["BallotType"] not in ("PR", "Ward"):
                continue
            c, v = P.canonical(r["sPartyName"]), int(r["Party_Votes"])
            votes[c] += v
            if r["BallotType"] == "Ward":
                by_ward[r["Ward"]][c] += v
    wards = collections.Counter(max(w, key=w.get) for w in by_ward.values())
    if sum(seats.values()) != int(struct["council"]) or sum(wards.values()) != int(struct["wards"]):
        raise MakeBuildError(f"build_make: the {year} seats sum to {sum(seats.values())} and the wards to "
                             f"{sum(wards.values())}, not {struct['council']} and {struct['wards']}")
    total = sum(votes.values())
    stood = [c for c in roster if votes.get(c, 0) > 0]
    return {"year": year, "valid_votes": total,
            "seats": {c: seats.get(c, 0) for c in stood},
            "wards": {c: wards.get(c, 0) for c in stood},
            "vote": {c: votes[c] * 100.0 / total for c in stood}}


def election_of(city) -> dict:
    """The election the page forecasts: the city, polling day,
    ``polls_open``, the instant voting stations open with its UTC offset, and
    ``zone``, that offset's name (``cities/<slug>.toml`` ``[structure]``).
    The Worker refuses to seal a reader's forecast from that instant
    (src/worker.js); the share cards print times in that zone."""
    struct = city.structure_for(city.default_target)
    return {"city": city.name, "date": str(struct["election_date"]),
            "polls_open": f"{struct['election_date']}T{struct['polls_open']}:00{struct['utc_offset']}",
            "zone": str(struct["time_zone"])}


def forecast_data(draws: Path | None = None) -> dict:
    """Everything ``make/forecast.json`` carries."""
    import cityconfig
    manifest, arrays, raw = _draws(draws)
    pools_file = REPO_ROOT / "data" / "processed" / f"pools_{cityconfig.active().default_target}.json"
    total, total_src = total_votes(manifest, arrays, pools_file)
    roster = build_play.roster()
    geom = geometry()
    artefact = model_artefact(manifest, total, roster)
    schema = make_schema(artefact, geom)
    start = start_state(manifest, arrays, schema)
    ctx = schema["x-seat-context"]
    # What a link is read against: change any of these and an old link's
    # positions mean different parties, wards or votes (js/make-state.js).
    context_ref = _sha(json.dumps([ctx["parties"], ctx["wards"], schema["x-total-votes"]]).encode())[:12]
    city = cityconfig.active()
    election = election_of(city)
    return {
        "_about": ("Written by src/build_make.py from the published draws (site/draws/). "
                   "Do not edit."),
        "model_ref": artefact["model_ref"],
        "election": election,
        "context_ref": context_ref,
        "draws_sha256": _sha(raw),
        "total_votes_source": total_src,
        "schema": schema,
        "geometry": {k: geom[k] for k in ("W", "H", "hex_radius", "labels", "wards")},
        "start": start,
        "baseline": baseline(city, ctx["parties"]),
    }


# --------------------------------------------------------------------------
# the page


def seat_attrs() -> dict[str, str]:
    """The reader's council table's axis, ticks and header words, set on its
    region for js/make.js (``seat_table.HEAD_COUNCIL``: a single council has
    no range, so its range column carries no heading)."""
    import seat_table
    return {"<!-- __MAKE:seatscale__ -->": str(seat_table.SEAT_SCALE),
            "<!-- __MAKE:seatticks__ -->": " ".join(str(x) for x in seat_table.SEAT_TICKS),
            "<!-- __MAKE:seathead__ -->": "|".join(seat_table.HEAD_COUNCIL)}
