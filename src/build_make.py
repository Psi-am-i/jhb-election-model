"""Section 2 of "your forecast" ("Break the model"): its data and its start.

``src/build_your_forecast.py`` assembles the page (``/your-forecast/``) and
copies its files; ``build_site.main`` renders, scans, stamps and ledgers it.
This module writes the one data file section 2 reads and states where it
starts; it decides nothing about what is allowed on a page. Anonymous: the
reader's forecast lives in the page's address (``js/make-state.js``, through
``js/yf-url.js``).

``your-forecast/forecast.json``
    The one data file section 2 reads (:func:`forecast_data`): the generated
    entry schema (``worker-api/tools/make_schema.mjs``'s own ``build``, run on
    the artefact :func:`model_artefact` writes from the published draws), the
    ward geometry, and the start state. It is the ONE entry schema: the site
    Worker validates a sealed entry against it, the scorer reads it, and the
    placeholder ``worker-api/generated/forecast.schema.json`` is retired
    (2026-10-08, guard G13).
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

A missing block is a :class:`MakeBuildError` naming it.

**The encoded start, ``start.f``.** The prediction object is encoded once by
the page's own encoder (``js/make-state.js`` ``encode``, entry version
``FORMAT``) in one node call, which also decodes it again and lists the
parties outside the editor's bounds (``js/builder-state.js`` ``outOfBounds``).
The build refuses (:class:`MakeBuildError`) unless ``decode(f)`` is the object:
the same ward calls and the same whole votes on both ballots (guard G7). The
page opens on ``decode(start.f)``, and a sealed entry of the untouched start is
that state. ``start.out_of_bounds`` records the parties outside the editor's
bounds as a reported fact, possibly empty: bounds constrain the editor and
never validity (SPEC-B D4).

**Ballot totals belong to the prediction.** Each ballot's total is the sum of
its whole votes, carried in ``f``: our prediction states rule A's totals, and a
hand-off from section 1 states its own. Nothing fixes a total. What was, until
2026-10-08: one combined vote total, ``x-total-votes``, two ballots times the
median of each draw's votes cast, which a reader's percentages were scaled to.

**The editor's bounds** (:func:`editor_bounds`, the schema's
``x-editor-bounds``) are regenerated from the past results at every build and
limit the page's editor only (JUDGEMENT-CALLS §R).
"""
from __future__ import annotations

import collections
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

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


# --------------------------------------------------------------------------
# the editor's bounds (JUDGEMENT-CALLS §R)

#: How far the editor's bounds are widened beyond the past results' extremes,
#: in percentage points of a ballot, on each side: the owner's call
#: (JUDGEMENT-CALLS §R2, 2026-10-08).
EDITOR_WIDEN_PP = 5.0
#: The most a ward's runner-up can hold of its ward vote: half, because a
#: runner-up holding more would be the winner. The widened runner-up bound is
#: capped here (JUDGEMENT-CALLS §R2).
RUNNER_UP_MAX = 0.5


def _panel(city, target: str) -> list[Path]:
    """Every cleaned metro LGE result file before ``target``: the past results
    the editor's bounds are read from (JUDGEMENT-CALLS §R1). Every metro's,
    not only ``city``'s."""
    import cityconfig
    elections = REPO_ROOT / city.path("raw", "elections")
    files = []
    for f in sorted(elections.glob("lge*_*_vd_party_clean.csv")):
        year = f.name[3:7]
        if year.isdigit() and year < str(target) and year in cityconfig.CALENDAR \
                and cityconfig.CALENDAR[year].kind == "LGE":
            files.append(f)
    return files


def panel_extremes(files) -> dict:
    """The extremes of the past results the editor's bounds widen, from the
    cleaned files' own rows (``score_forecasts._read_rows``, the one reader):

    * ``q_win``: the lowest share of its ward's valid ward-ballot votes with
      which any ward was won;
    * ``q_run``: the highest share any ward's runner-up held;
    * ``gap_min``, ``gap_max``: the extremes of list share minus ward share,
      in percentage points of each ballot's citywide total, over every party
      that stood on both ballots in a city-year (the merged ``INDEPENDENT``
      row, which stands on no list, excluded by the same test).

    Each comes with where it was found. Names are the IEC's, per file: the
    bounds are about shapes of results, not about parties."""
    import score_forecasts
    from seats import INDEPENDENT
    win = run = lo = hi = None
    for f in files:
        ward_raw, pr_raw, _names, _roll = score_forecasts._read_rows(f)
        for ward, counts in ward_raw.items():
            total = sum(counts.values())
            if not total:
                continue
            top = sorted(counts.values(), reverse=True)
            w = (top[0] / total, f.name, ward)
            r = ((top[1] if len(top) > 1 else 0) / total, f.name, ward)
            win = w if win is None or w[0] < win[0] else win
            run = r if run is None or r[0] > run[0] else run
        ward_tot = collections.Counter()
        for counts in ward_raw.values():
            ward_tot.update(counts)
        tw, tp = sum(ward_tot.values()), sum(pr_raw.values())
        for name in sorted(set(ward_tot) | set(pr_raw)):
            if name == INDEPENDENT or not (ward_tot[name] > 0 and pr_raw.get(name, 0) > 0):
                continue
            g = (100.0 * (pr_raw[name] / tp - ward_tot[name] / tw), f.name, name)
            lo = g if lo is None or g[0] < lo[0] else lo
            hi = g if hi is None or g[0] > hi[0] else hi
    if win is None or lo is None:
        raise MakeBuildError("build_make: the editor bounds' panel holds no ward or no party")
    return {"q_win": {"value": win[0], "file": win[1], "ward": win[2]},
            "q_run": {"value": run[0], "file": run[1], "ward": run[2]},
            "gap_min": {"value": lo[0], "file": lo[1], "party": lo[2]},
            "gap_max": {"value": hi[0], "file": hi[1], "party": hi[2]}}


def expected_ward_shares(city, target: str, wards: list[str], *, roll: Path | None = None,
                         previous: Path | None = None) -> tuple[dict, dict]:
    """``({ward: share of the expected ward vote}, provenance)``, summing to one.

    A ward's expected ward vote is its roll on the newest registration snapshot
    (``inputs_preflight.roll_snapshot``, the one ``--strict`` checks) times its
    expected turnout: the registration-weighted mean, over its voting-district
    parts (``montecarlo.ward_parts``, the split VDs apportioned), of each
    part's VD's ward-ballot turnout at the preceding local election (valid ward
    votes over registered). A part whose VD has no record there, or a record
    with no one registered, is left out of its ward's mean and counted; a ward
    left with no part refuses the build (JUDGEMENT-CALLS §R3). ``roll`` and
    ``previous`` name other files in the same layouts (the tests' constructed
    copies); by default they are the snapshot and the preceding election's."""
    import cityconfig
    import inputs_preflight
    import montecarlo
    import score_forecasts
    try:
        snap = inputs_preflight.roll_snapshot(city.slug) if roll is None else Path(roll)
    except ValueError as exc:
        raise MakeBuildError(f"build_make: {exc}") from None
    if snap is None:
        raise MakeBuildError(f"build_make: no registration snapshot for {city.slug} "
                             f"(archive/iec-registration-<date>/); run inputs_preflight.py --strict")
    roll: dict[str, int] = {}
    with open(snap, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            roll[score_forecasts.ward_number(row["Ward"], city.ward_prefix)] = int(row["Registered"])
    if sorted(roll, key=int) != sorted(wards, key=int):
        raise MakeBuildError(f"build_make: the roll's wards ({len(roll)}) are not the schema's "
                             f"({len(wards)}): {snap.name}")
    tgt = cityconfig.Target(city=city, year=str(target))
    prev = tgt.previous_lge
    elections = REPO_ROOT / city.path("raw", "elections")
    path = cityconfig.resolve_path(elections / tgt.results(prev)) if previous is None else Path(previous)
    _w, _p, _n, vd_roll = score_forecasts._read_rows(path, roll=True)
    parts, label = montecarlo.ward_parts(tgt, elections, REPO_ROOT / tgt.crosswalk.parent)
    reg = collections.Counter()
    cast = collections.Counter()
    left_out = {"parts": 0, "registered": 0}
    for vd, ward, registered in parts:
        rec = vd_roll.get(str(vd))
        if rec is None or not rec[1] > 0:
            left_out["parts"] += 1
            left_out["registered"] += int(registered)
            continue
        reg[str(ward)] += registered
        cast[str(ward)] += registered * rec[2] / rec[1]
    bare = sorted((w for w in wards if not reg[w] > 0), key=int)
    if bare:
        raise MakeBuildError(f"build_make: wards with no part recorded at {prev}: {bare}")
    expected = {w: roll[w] * cast[w] / reg[w] for w in wards}
    whole = sum(expected.values())
    return ({w: expected[w] / whole for w in wards},
            {"roll": str(snap.relative_to(REPO_ROOT)) if snap.is_relative_to(REPO_ROOT) else snap.name,
             "roll_sha256": _sha(snap.read_bytes()),
             "turnout_from": path.name, "turnout_sha256": _sha(path.read_bytes()),
             "parts": label, "parts_left_out": left_out})


def editor_bounds(city, target: str, wards: list[str]) -> dict:
    """The schema's ``x-editor-bounds``: what the page's editor lets a reader
    set, regenerated from the past results at every build (JUDGEMENT-CALLS §R).
    They limit the editor only, never what an entry may be (SPEC-B D4).

    ``e``: each ward's share of the expected ward vote
    (:func:`expected_ward_shares`). ``q_win``, ``q_run``: the lowest winning
    and highest runner-up shares of a ward's vote; ``gap_min``, ``gap_max``:
    list share minus ward share per party, in points. Each is the past results'
    extreme (:func:`panel_extremes`, kept under ``panel_extremes``) widened by
    :data:`EDITOR_WIDEN_PP`, the runner-up bound capped at
    :data:`RUNNER_UP_MAX`. ``panel`` names the files and ``sources`` their
    sha256, so a changed file changes the bounds visibly."""
    files = _panel(city, target)
    if not files:
        raise MakeBuildError(f"build_make: no cleaned LGE result file before {target}")
    ext = panel_extremes(files)
    e, provenance = expected_ward_shares(city, target, wards)
    widen = EDITOR_WIDEN_PP / 100.0
    return {
        "e": e,
        "q_win": max(0.0, ext["q_win"]["value"] - widen),
        "q_run": min(RUNNER_UP_MAX, ext["q_run"]["value"] + widen),
        "gap_min": ext["gap_min"]["value"] - EDITOR_WIDEN_PP,
        "gap_max": ext["gap_max"]["value"] + EDITOR_WIDEN_PP,
        "panel_extremes": ext,
        "widen_pp": EDITOR_WIDEN_PP,
        "runner_up_max": RUNNER_UP_MAX,
        "panel": [f.name for f in files],
        "sources": {f.name: _sha(f.read_bytes()) for f in files},
        "expected_ward_vote": provenance,
        "rules": {
            "q_win": "a party's ward vote is at least q_win times the expected ward vote of the wards it wins",
            "q_run": ("a party's ward vote is at most the expected ward vote of the wards it wins "
                      "plus q_run times that of the wards it does not"),
            "gap": "a party's list share minus its ward share, in points, is between gap_min and gap_max",
            "scope": "the editor only: an entry outside these bounds is valid and opens with a note",
        },
    }


def model_artefact(manifest: dict, roster: dict, bounds: dict) -> dict:
    """The model artefact ``make_schema.mjs`` reads, from the published draws
    and the editor's bounds (:func:`editor_bounds`)."""
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
        "no_pr_list": [],
        "editor_bounds": bounds,
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
              "  process.stdout.write(JSON.stringify(out));\n"
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
    return json.loads(run.stdout)["schema"]


def encode_start(pred: dict, schema: dict) -> dict:
    """``{"f", "out_of_bounds"}`` for a prediction object, by the page's own
    encoder (module docstring), refusing unless ``decode(f)`` is the object."""
    js = INTERACTIVE / "js"
    script = ("import * as MS from " + json.dumps((js / "make-state.js").as_uri()) + ";\n"
              "import * as B from " + json.dumps((js / "builder-state.js").as_uri()) + ";\n"
              "let s = ''; process.stdin.on('data', d => s += d).on('end', () => {\n"
              "  const { schema, pred } = JSON.parse(s);\n"
              "  const ctx = B.contextOf(schema);\n"
              "  const state = B.stateFromPrediction(ctx, pred);\n"
              "  const f = MS.encode(state, [], ctx);\n"
              "  const back = MS.decode(f, ctx);\n"
              "  process.stdout.write(JSON.stringify({ f, decoded: back.state, coalition: back.coalition,\n"
              "    out_of_bounds: B.outOfBounds(state, ctx) }));\n"
              "});\n")
    payload = json.dumps({"schema": schema, "pred": {k: pred[k] for k in ("ward_calls", "ward_votes", "list_votes")}})
    try:
        run = subprocess.run(["node", "--input-type=module", "-e", script], input=payload,
                             capture_output=True, text=True, cwd=REPO_ROOT)
    except FileNotFoundError:
        raise MakeBuildError("build_make: node is not installed, so the start cannot be encoded "
                             "by interactive/js/make-state.js") from None
    if run.returncode:
        raise MakeBuildError(f"build_make: encoding the start failed:\n{run.stderr}")
    got = json.loads(run.stdout)
    back = got["decoded"]
    if (back["calls"] != list(pred["ward_calls"]) or back["ward"] != dict(pred["ward_votes"])
            or back["list"] != dict(pred["list_votes"]) or got["coalition"] != []):
        raise MakeBuildError("build_make: decode(start.f) is not our prediction (guard G7)")
    return {"f": got["f"], "out_of_bounds": got["out_of_bounds"]}


def start_state(manifest: dict, arrays: dict, schema: dict) -> dict:
    """Our prediction, the start of section 2; module docstring."""
    import prediction
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
    context, _ward_ids = score_forecasts.schema_context(schema)
    try:
        seated = prediction.seats_of(pred, context["council"], order=roster)
    except (ValueError, RuntimeError) as exc:
        raise MakeBuildError(f"build_make: the seat law cannot seat our prediction: {exc}") from None
    seats = {p: v["total"] for p, v in seated["seats"].items()}
    # the entry path seats it the same way (reader_seats calls seats_of)
    entry = score_forecasts.seat_forecast(pred, schema)
    if not entry["ok"]:
        raise MakeBuildError(f"build_make: our prediction is refused as an entry: {entry['errors']}")
    if {p: v["total"] for p, v in entry["seats"].items()} != seats:
        raise MakeBuildError("build_make: our prediction seats differently as an entry")
    encoded = encode_start(pred, schema)
    return {
        "ward_calls": pred["ward_calls"],
        "ward_votes": pred["ward_votes"],
        "list_votes": pred["list_votes"],
        "seats": seats,
        "f": encoded["f"],
        "out_of_bounds": encoded["out_of_bounds"],
        "rule": "rule A: src/prediction.py",
    }


def _inputs(draws: Path | None = None) -> dict:
    """What the start and ``forecast.json`` are built from: the served draws,
    the editor's bounds, the model artefact, the geometry and the generated
    schema. Reads only."""
    import cityconfig
    city = cityconfig.active()
    manifest, arrays, raw = _draws(draws)
    geom = geometry()
    bounds = editor_bounds(city, str(city.default_target), [str(w["id"]) for w in geom["wards"]])
    artefact = model_artefact(manifest, build_play.roster(), bounds)
    return {"manifest": manifest, "arrays": arrays, "raw": raw,
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
    * ``list_vote``, ``ward_vote``: each party's percent of the valid votes on
      the PR (list) ballot and on the Ward ballot, from the same file. The
      cards compare a prediction's list vote with ``list_vote``, list with
      list (STYLE.md rule 11; until 2026-10-08 this was one ``vote`` of both
      ballots summed, compared with a combined share).

    Only roster parties that stood are keyed: a party absent from
    ``list_vote`` stood on neither ballot, and the cards print "new" for it
    (owner, 2026-10-03). A party that held seats then and is not on the roster now
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
    ballot = {"PR": collections.Counter(), "Ward": collections.Counter()}
    path = REPO_ROOT / city.path("raw", "elections", cityconfig.CALENDAR[year].results)
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["BallotType"] not in ("PR", "Ward"):
                continue
            c, v = P.canonical(r["sPartyName"]), int(r["Party_Votes"])
            votes[c] += v
            ballot[r["BallotType"]][c] += v
            if r["BallotType"] == "Ward":
                by_ward[r["Ward"]][c] += v
    wards = collections.Counter(max(w, key=w.get) for w in by_ward.values())
    if sum(seats.values()) != int(struct["council"]) or sum(wards.values()) != int(struct["wards"]):
        raise MakeBuildError(f"build_make: the {year} seats sum to {sum(seats.values())} and the wards to "
                             f"{sum(wards.values())}, not {struct['council']} and {struct['wards']}")
    stood = [c for c in roster if votes.get(c, 0) > 0]
    pr_total, ward_total = sum(ballot["PR"].values()), sum(ballot["Ward"].values())
    return {"year": year, "list_valid_votes": pr_total, "ward_valid_votes": ward_total,
            "seats": {c: seats.get(c, 0) for c in stood},
            "wards": {c: wards.get(c, 0) for c in stood},
            "list_vote": {c: ballot["PR"][c] * 100.0 / pr_total for c in stood},
            "ward_vote": {c: ballot["Ward"][c] * 100.0 / ward_total for c in stood}}


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
    raw = inputs["raw"]
    start = our_prediction(inputs=inputs)
    ctx = schema["x-seat-context"]
    # What a link is read against: change either and an old link's positions
    # mean different parties or wards (js/make-state.js). Nothing else: new
    # bounds or a new roll snapshot do not break a link (SPEC-B D5).
    context_ref = _sha(json.dumps([ctx["parties"], ctx["wards"]]).encode())[:12]
    city = cityconfig.active()
    election = election_of(city)
    return {
        "_about": ("Written by src/build_make.py from the published draws (site/draws/). "
                   "Do not edit."),
        "model_ref": artefact["model_ref"],
        "election": election,
        "context_ref": context_ref,
        "draws_sha256": _sha(raw),
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
