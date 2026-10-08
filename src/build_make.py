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
``your-forecast/js/seats.js``, ``http.js``, ``blocklist.js``
    Copied from ``worker-api/src`` (``WORKER_API_JS``) beside
    ``seat-engine.js``, whose ONE declared import line (``SEATS_LINE``) is
    rewritten to them. The first two run only inside section 2's Web Worker,
    which the number gate does not follow (it cannot touch the page);
    ``blocklist.js`` is the owner's name blocklist, imported by
    ``play-state.js``.

The start state, stated exactly
===============================

Section 2 opens on **our prediction**: rule A on the published draws
(``site/draws/``), each draw counted once, by ``score_forecasts.model_forecast``,
which calls ``src/prediction.py``, the one definition (JUDGEMENT-CALLS §Q):

* **Ward calls**: each ward to the party that wins it in the most simulations
  (the ``ward_winner`` block), a tie to the code first in string order.
* **Votes**: each party's mean ward-ballot and mean list-ballot whole votes
  across the simulations (the ``ward_vote`` and ``list_vote`` blocks).
* **Seats**: by the seat law from those wards and votes
  (``prediction.seats_of``), never stored as an input.

A missing block is a :class:`MakeBuildError` naming it. Until the reader entry
carries both ballots (slice B), the start also carries an INTERIM
``combined_share`` (both ballots' votes as one share, the shape a reader's
forecast has today) and an empty ``published_middle``; the build seats the
interim share through ``reader_seats`` and refuses to write a start whose
seats differ from the prediction's.

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

REPO_ROOT = Path(__file__).resolve().parents[1]
INTERACTIVE = REPO_ROOT / "interactive"
DRAWS = REPO_ROOT / "site" / "draws"
WORKER_SRC = REPO_ROOT / "worker-api" / "src"

#: The worker-api files the page imports, copied beside its modules: the two
#: section 2's seat Worker imports, and the owner's name blocklist, which
#: ``play-state.js`` imports (``build_your_forecast.BLOCKLIST_LINE``).
WORKER_API_JS = ("seats.js", "http.js", "blocklist.js")
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


def start_state(manifest: dict, arrays: dict, schema: dict) -> dict:
    """Our prediction, the start of section 2; module docstring."""
    import prediction
    import reader_seats
    import score_forecasts
    for name in ("ward_winner", "ward_vote", "list_vote"):
        if name not in arrays:
            raise MakeBuildError(f"build_make: the draw file carries no {name} block")
    roster = list(schema["x-seat-context"]["parties"])
    wards = _columns(manifest, "ward_winner")
    columns = _columns(manifest, "list_vote")
    if _columns(manifest, "ward_vote") != columns:
        raise MakeBuildError("build_make: the ward_vote and list_vote blocks have different columns")
    try:
        pred = score_forecasts.model_forecast(
            arrays["ward_winner"], manifest["ward_parties"], wards,
            arrays["ward_vote"], arrays["list_vote"], columns, schema)
    except ValueError as exc:
        raise MakeBuildError(f"build_make: {exc}") from None
    context, total, target, _tol, ward_ids = score_forecasts.schema_context(schema)
    try:
        seated = prediction.seats_of(pred, context["council"], order=roster)
    except (ValueError, RuntimeError) as exc:
        raise MakeBuildError(f"build_make: the seat law cannot seat our prediction: {exc}") from None
    seats = {p: v["total"] for p, v in seated["seats"].items()}
    # INTERIM (until slice B): the combined share must seat exactly the
    # prediction through today's reader path
    got = reader_seats.reader_seats({p: v / target for p, v in pred["combined_share"].items()},
                                    dict(zip(ward_ids, pred["ward_calls"])), context, total)
    if not got["ok"]:
        raise MakeBuildError(f"build_make: the interim combined share does not seat: {got['errors']}")
    interim = {p: v["total"] for p, v in got["seats"].items()}
    if interim != seats:
        raise MakeBuildError(f"build_make: the interim combined share seats {interim}, "
                             f"not the prediction's {seats}")
    return {
        "ward_calls": pred["ward_calls"],
        "ward_votes": pred["ward_votes"],
        "list_votes": pred["list_votes"],
        "seats": seats,
        "combined_share": pred["combined_share"],      # INTERIM, slice B deletes
        "published_middle": {},                         # INTERIM, slice B deletes
        "rule": "rule A: src/prediction.py",
    }


def _inputs(draws: Path | None = None) -> dict:
    """What the start and ``forecast.json`` are built from: the served draws,
    the total vote, the model artefact, the geometry and the generated
    schema. Reads only."""
    import cityconfig
    manifest, arrays, raw = _draws(draws)
    pools_file = REPO_ROOT / "data" / "processed" / f"pools_{cityconfig.active().default_target}.json"
    total, total_src = total_votes(manifest, arrays, pools_file)
    geom = geometry()
    artefact = model_artefact(manifest, total, build_play.roster())
    return {"manifest": manifest, "arrays": arrays, "raw": raw, "total_src": total_src,
            "geometry": geom, "artefact": artefact, "schema": make_schema(artefact, geom)}


def our_prediction(draws: Path | None = None, *, inputs: dict | None = None) -> dict:
    """Our prediction from the served draws, without writing anything: the
    ``start`` that :func:`forecast_data` puts in ``forecast.json`` (it calls
    this), and what a caller reads before that file exists (``render_sheet``'s
    pointer on ``/forecast``). ``inputs`` is :func:`_inputs`' result, when the
    caller has it already."""
    inputs = _inputs(draws) if inputs is None else inputs
    return start_state(inputs["manifest"], inputs["arrays"], inputs["schema"])


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
    ``zone``, that offset's name: polling day from ``cities/<slug>.toml``,
    the opening time and zone from ``content/<slug>/election.toml`` (which
    says why it is not in the city file).
    The Worker refuses to seal a reader's forecast from that instant
    (src/worker.js); the share cards print times in that zone."""
    import tomllib
    struct = city.structure_for(city.default_target)
    clock = tomllib.loads((REPO_ROOT / "content" / city.slug / "election.toml").read_text(encoding="utf-8"))
    return {"city": city.name, "date": str(struct["election_date"]),
            "polls_open": f"{struct['election_date']}T{clock['polls_open']}:00{clock['utc_offset']}",
            "zone": str(clock["time_zone"])}


def forecast_data(draws: Path | None = None) -> dict:
    """Everything ``make/forecast.json`` carries."""
    import cityconfig
    inputs = _inputs(draws)
    schema, geom, artefact = inputs["schema"], inputs["geometry"], inputs["artefact"]
    raw, total_src = inputs["raw"], inputs["total_src"]
    start = our_prediction(inputs=inputs)
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
