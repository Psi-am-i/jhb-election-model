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
  (the ``ward_winner`` block), a tie drawn by the seeded lot under the published
  run's identity (``run_lot``, carried by the model artefact into
  ``x-seat-context["lot"]`` by ``make_schema.mjs``).
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
#
# Three layers, each regenerated from the result files at every build and
# written into the schema's ``x-editor-bounds`` with its provenance, so every
# figure the editor uses is fetched from there and none is typed here:
#
# * the SHAPE of a ward result (``q_win``, ``q_run``) and of a party's two
#   ballots (``gap_min``, ``gap_max``): the past extremes (:func:`panel_extremes`),
#   widened by the mean of their record events (:func:`shape_allowances`);
# * per ward and party, a RANGE for its share of the ward's vote: its share
#   there at the preceding local election (or national election, for a party
#   new to local elections), moved by the most any party of its starting size
#   has swung between consecutive local elections, widened by the mean record
#   exceedance (:func:`ward_ranges`);
# * per party, a CITYWIDE LIMIT on its share of the ward ballot, by the same
#   rule on citywide swings (:func:`city_limits`).
#
# The editor (``interactive/js/builder-state.js``) intersects the per-party
# box the ward ranges allow on the painted map with the citywide limit.

#: How far an editor's bound is widened beyond the past extremes where its
#: quantity has fewer than :data:`MIN_RECORD_EVENTS` record events, in
#: percentage points of a ballot, on each side: the owner's call
#: (JUDGEMENT-CALLS §R2, 2026-10-08; §R14 for where it still applies).
EDITOR_WIDEN_PP = 5.0
#: The most a ward's runner-up can hold of its ward vote: half, because a
#: runner-up holding more would be the winner. The widened runner-up bound is
#: capped here (JUDGEMENT-CALLS §R2).
RUNNER_UP_MAX = 0.5
#: The interior edges of the starting-share bins a swing is grouped by, as
#: shares of a ward's (or a city's) ward-ballot votes: a swing's spread grows
#: with the share it starts from (JUDGEMENT-CALLS §R7, typed).
SWING_BINS = (0.01, 0.05, 0.15, 0.35, 0.60)
#: The fewest record events whose mean widens a bound; a quantity with fewer
#: is widened by :data:`EDITOR_WIDEN_PP` (JUDGEMENT-CALLS §R14, typed).
MIN_RECORD_EVENTS = 2
#: The exclusion rules of the record events (JUDGEMENT-CALLS §R13, typed), as
#: shares of a city's ward-ballot votes. A party holding at least VANISH_MIN at
#: the earlier election and standing nowhere at the later one has vanished; one
#: new to the city with at least SPLIT_MIN has split from someone; one falling
#: from at least COLLAPSE_FROM to under COLLAPSE_KEEP of that share has
#: collapsed. A vanished party's absorber, or a newcomer's source, is named
#: only where the correlation of the swings with its ward shares reaches
#: CORRELATION_MIN in size.
VANISH_MIN = 0.01
SPLIT_MIN = 0.05
COLLAPSE_FROM = 0.02
COLLAPSE_KEEP = 0.25
CORRELATION_MIN = 0.5
#: The marker in a calendar result template that names an approximation of
#: another election's footprint (``npe1999_approx_*``); such a file is not a
#: national result in a metro's own VDs and is never a national prior.
APPROXIMATE = "_approx_"


def _panel(city, target: str, elections: Path | None = None) -> list[Path]:
    """Every cleaned metro LGE result file before ``target``: the past results
    the editor's bounds are read from (JUDGEMENT-CALLS §R1). Every metro's,
    not only ``city``'s. ``elections`` names another directory in the same
    layout (the tests' constructed copies)."""
    import cityconfig
    elections = REPO_ROOT / city.path("raw", "elections") if elections is None else Path(elections)
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
        ward_raw, pr_raw, _names, _roll, _vd = score_forecasts._read_rows(f)
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


#: Which way each shape quantity sets a record, and so which way it is widened.
SHAPE_DIRECTION = {"q_win": "down", "q_run": "up", "gap_min": "down", "gap_max": "up"}


def _turnout_parts(parts, vd_roll) -> tuple[collections.Counter, collections.Counter, dict]:
    """``(registered, cast, left_out)`` per ward over voting-district parts:
    each part ``(vd, ward, registered)`` whose VD has a record in ``vd_roll``
    (``{vd: (ward, registered, valid ward-ballot votes)}``) with someone
    registered adds its registration, and its registration times its VD's
    turnout (valid ward votes over registered); a part without one is left out
    and counted. The one definition of a ward's expected turnout, read by
    :func:`expected_ward_shares` and by the citywide swings of
    :func:`swing_panel`."""
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
    return reg, cast, left_out


def expected_ward_shares(city, target: str, wards: list[str], *,
                         previous: Path | None = None,
                         processed: Path | None = None) -> tuple[dict, dict]:
    """``({ward: share of the expected ward vote}, provenance)``, summing to one.

    A ward's expected ward vote is its roll (the sum of its parts'
    registration as ``montecarlo.ward_parts`` returns them, which for 2026 is
    the newest registration snapshot apportioned into the crosswalk by
    ``build_concordance``; one reader, one roll) times its expected turnout: the
    registration-weighted mean, over its voting-district parts (the same
    ``montecarlo.ward_parts``, the split VDs apportioned), of each
    part's VD's ward-ballot turnout at the preceding local election (valid ward
    votes over registered; :func:`_turnout_parts`). A part whose VD has no
    record there, or a record with no one registered, is left out of its ward's
    mean and counted; a ward left with no part refuses the build
    (JUDGEMENT-CALLS §R3). ``previous`` names another file in the
    preceding election's layout, and ``processed`` another directory holding
    the crosswalk (the tests' constructed copies); by default they are the
    preceding election's file and the city's processed directory."""
    import cityconfig
    import inputs_preflight
    import montecarlo
    import score_forecasts
    tgt = cityconfig.Target(city=city, year=str(target))
    prev = tgt.previous_lge
    elections = REPO_ROOT / city.path("raw", "elections")
    path = cityconfig.resolve_path(elections / tgt.results(prev)) if previous is None else Path(previous)
    _w, _p, _n, vd_roll, _vd = score_forecasts._read_rows(path, roll=True)
    parts, label = montecarlo.ward_parts(tgt, elections, _processed(tgt, processed))
    crosswalk = _processed(tgt, processed) / tgt.crosswalk.name
    declared = inputs_preflight.declared_roll_snapshot(city.slug, str(target), crosswalk)
    if declared is None:
        raise MakeBuildError(f"build_make: {crosswalk.name} declares no registration snapshot "
                             f"(no roll_snapshot column), so its rolls are not the target's; "
                             f"run build_concordance.py --city {city.slug}")
    roll: dict[str, int] = collections.Counter()
    for _vd_number, ward, registered in parts:
        roll[str(ward)] += registered
    if sorted(roll, key=int) != sorted(wards, key=int):
        raise MakeBuildError(f"build_make: the roll's wards ({len(roll)}) are not the schema's "
                             f"({len(wards)}): {label}")
    reg, cast, left_out = _turnout_parts(parts, vd_roll)
    bare = sorted((w for w in wards if not reg[w] > 0), key=int)
    if bare:
        raise MakeBuildError(f"build_make: wards with no part recorded at {prev}: {bare}")
    expected = {w: roll[w] * cast[w] / reg[w] for w in wards}
    whole = sum(expected.values())
    return ({w: expected[w] / whole for w in wards},
            {"roll": declared, "roll_sha256": _sha(crosswalk.read_bytes()),
             "turnout_from": path.name, "turnout_sha256": _sha(path.read_bytes()),
             "parts": label, "parts_left_out": left_out})


# --------------------------------------------------------------------------
# the result files, read once per content (JUDGEMENT-CALLS §R6)

#: ``{(kind, sha256): read}``: a file is parsed once per content, wherever it
#: lies, so a test that mutates one file of a mirrored panel re-reads only
#: that one.
_READS: dict = {}
_CODES: dict = {}


def _code(name: str) -> str:
    import parties
    if name not in _CODES:
        _CODES[name] = parties.canonical(name)
    return _CODES[name]


def _folded(counts: dict) -> collections.Counter:
    out = collections.Counter()
    for name, v in counts.items():
        if v:
            out[_code(name)] += v
    return out


def _lge(path: Path) -> dict:
    """A cleaned local result file by VD: ``{"vds": {vd: {"ward", "reg",
    "valid", "votes": Counter(code)}}, "pr": Counter(code), "sha256"}``, read
    by ``score_forecasts._read_rows`` (the one reader) and folded onto codes
    by ``parties.canonical``. Zero counts are dropped."""
    import score_forecasts
    path = Path(path)
    sha = _sha(path.read_bytes())
    key = ("LGE", sha)
    if key not in _READS:
        _w, pr, _n, roll, by_vd = score_forecasts._read_rows(path, roll=True, vd_votes=True)
        vds = {vd: {"ward": ward, "reg": reg, "valid": valid, "votes": _folded(by_vd.get(vd, {}))}
               for vd, (ward, reg, valid) in roll.items()}
        _READS[key] = {"vds": vds, "pr": _folded(pr), "sha256": sha}
    return _READS[key]


def _npe(path: Path) -> dict:
    """A national result file by VD: ``{"vds": {vd: {"votes": Counter(code)}},
    "sha256"}``, read by ``score_forecasts._read_npe``."""
    import score_forecasts
    path = Path(path)
    sha = _sha(path.read_bytes())
    key = ("NPE", sha)
    if key not in _READS:
        _READS[key] = {"vds": {vd: {"votes": _folded(c)} for vd, c in score_forecasts._read_npe(path).items()},
                       "sha256": sha}
    return _READS[key]


def _held_parts(lge: dict) -> list[tuple[str, str, int]]:
    """A held election's parts, every VD whole in the ward its own file names,
    with its registration: ``montecarlo.ward_parts``' rule for a held target
    (its docstring). Read here from the panel's own parse because that function
    resolves the file through the ACTIVE city (``cityconfig.resolve_path``),
    and the panel reads every metro. ``tests/test_your_forecast_page.py``
    holds the two equal on the active city's held elections."""
    return [(vd, d["ward"], d["reg"]) for vd, d in lge["vds"].items()]


def _ward_shares(lge: dict) -> tuple[dict, dict, dict]:
    """``({ward: {code: share}}, {ward: valid ward votes}, {ward: registered})``."""
    acc = collections.defaultdict(collections.Counter)
    reg = collections.Counter()
    for d in lge["vds"].values():
        acc[d["ward"]].update(d["votes"])
        reg[d["ward"]] += d.get("reg", 0)
    shares, totals = {}, {}
    for w, c in acc.items():
        t = sum(c.values())
        if t:
            shares[w] = {p: v / t for p, v in c.items() if v}
            totals[w] = t
    return shares, totals, dict(reg)


def _city_shares(vds: dict) -> dict:
    """Each code's share of every vote in ``vds`` (the ward ballot of a local
    file, the one ballot of a national file)."""
    acc = collections.Counter()
    for d in vds.values():
        acc.update(d["votes"])
    t = sum(acc.values())
    return {p: v / t for p, v in acc.items() if v} if t else {}


def _join(parts, prior_vds: dict) -> dict:
    """Shares on the parts' wards from another election's VD votes: each part
    ``(vd, ward, registered)`` takes its VD's votes times its registration over
    the registration of all the VD's parts (a split VD apportioned, a whole one
    taken whole). A part whose VD is not in ``prior_vds`` adds nothing.
    ``{ward: {code: share}}``, wards with no vote absent."""
    vd_reg = collections.Counter()
    for vd, _w, r in parts:
        vd_reg[vd] += r
    acc = collections.defaultdict(collections.Counter)
    for vd, w, r in parts:
        d = prior_vds.get(vd)
        if d is None or not vd_reg[vd]:
            continue
        f = r / vd_reg[vd]
        for p, v in d["votes"].items():
            acc[str(w)][p] += v * f
    out = {}
    for w, c in acc.items():
        t = sum(c.values())
        if t:
            out[w] = {p: v / t for p, v in c.items() if v}
    return out


def _election_files(elections: Path, kind: str) -> dict:
    """``{(metro code, year): path}`` for every result file of ``kind`` ("LGE"
    or "NPE") on disk, by each election's calendar template. An approximation
    (:data:`APPROXIMATE`) is not a result and is left out."""
    import cityconfig
    out = {}
    for year, el in cityconfig.CALENDAR.items():
        if el.kind != kind or el.results is None or APPROXIMATE in el.results:
            continue
        pre, post = el.results.split("{CODE}")
        for f in sorted(Path(elections).glob(pre + "*" + post)):
            out[(f.name[len(pre):len(f.name) - len(post)], year)] = f
    return out


def _bin(share: float) -> int:
    """The :data:`SWING_BINS` bin of a starting share: bin i holds shares in
    (edge i-1, edge i], the first from zero."""
    import bisect
    return bisect.bisect_left(SWING_BINS, share)


def _extremes_by_bin(rows) -> list[list[float]]:
    """``[[least, greatest] swing]`` per bin over ``(start, swing)`` rows. A bin
    with no row takes the widest of the others."""
    d: dict[int, list[float]] = {}
    for start, swing in rows:
        b = _bin(start)
        if b not in d:
            d[b] = [swing, swing]
        else:
            d[b][0] = min(d[b][0], swing)
            d[b][1] = max(d[b][1], swing)
    if not d:
        raise MakeBuildError("build_make: no swing to bound the editor with")
    widest = [min(v[0] for v in d.values()), max(v[1] for v in d.values())]
    return [d.get(b, widest) for b in range(len(SWING_BINS) + 1)]


def swing_panel(city, target: str, *, elections: Path | None = None) -> dict:
    """The swings the ward ranges and citywide limits are built from, every
    metro's, before ``target`` (JUDGEMENT-CALLS §R6, §R8):

    * ``pairs``: every (metro, a, b) of consecutive local elections, a the
      calendar's local election before b, both files on disk and b before the
      target. Each b's wards take a's VD votes through b's own VDs, each whole
      (:func:`_held_parts`).
    * ``npe_pairs``: every (metro, n, l), n the national election before the
      local election l, l before the target.
    * ``ward_rows``: ``(metro, a, b, ward, code, h, s)``, a party's share in a
      ward at a (joined) and at b, over every party with either, ``IND``
      (every independent in a VD merged into one row) left out.
    * ``city_rows``: ``(metro, b, code, H, V)``: H a party's share at a on b's
      wards weighted by b's expected ward vote (b's roll times a's turnout,
      :func:`_turnout_parts`), V its share of b's ward ballot. A ward of b
      none of whose VDs has a record at a takes the mean turnout of b's
      other wards; each such ward is listed in ``mean_turnout_wards`` (with
      ``panel_wards``, every ward of every b, as the denominator), where the
      target's own build (:func:`expected_ward_shares`) refuses instead,
      because a past election's record cannot be repaired.
    * ``npe_ward_rows``, ``npe_city_rows``: the same from n to l, the party
      on both.
    * ``newcomer``: the greatest ward share and the greatest citywide share
      taken by a party with no ward vote in its city at a and no vote at the
      national election before b.
    * ``pair_data``: per local pair, what :func:`exclusions` reads.
    * ``sources``: each file read and its sha256.
    """
    import cityconfig
    T = str(target)
    elections = REPO_ROOT / city.path("raw", "elections") if elections is None else Path(elections)
    lge = _election_files(elections, "LGE")
    npe = _election_files(elections, "NPE")
    pairs, npe_pairs = [], []
    for (code, b) in sorted(lge):
        if b >= T:
            continue
        a = cityconfig.preceding(b, "LGE")
        if a is not None and (code, a) in lge:
            pairs.append((code, a, b))
        n = cityconfig.preceding(b, "NPE")
        if n is not None and (code, n) in npe:
            npe_pairs.append((code, n, b))
    out = {"pairs": pairs, "npe_pairs": npe_pairs, "ward_rows": [], "city_rows": [],
           "npe_ward_rows": [], "npe_city_rows": [], "pair_data": {}, "sources": {},
           "newcomer": {"ward": None, "city": None}, "mean_turnout_wards": [], "panel_wards": 0}

    def note(path, read):
        out["sources"][Path(path).name] = read["sha256"]

    def newcomer(kind, share, where):
        best = out["newcomer"][kind]
        if best is None or share > best["value"]:
            out["newcomer"][kind] = {"value": share, **where}

    for code, a, b in pairs:
        A, B = _lge(lge[(code, a)]), _lge(lge[(code, b)])
        note(lge[(code, a)], A)
        note(lge[(code, b)], B)
        parts = _held_parts(B)
        h = _join(parts, A["vds"])
        s, tot, reg_b = _ward_shares(B)
        for w in s:
            if w not in h:
                continue
            for p in sorted(set(h[w]) | set(s[w])):
                if p != "IND":
                    out["ward_rows"].append((code, a, b, w, p, h[w].get(p, 0.0), s[w].get(p, 0.0)))
        # the citywide prior on b's wards, by b's expected ward vote
        roll_a = {vd: (d["ward"], d["reg"], d["valid"]) for vd, d in A["vds"].items()}
        reg, cast, _left = _turnout_parts(parts, roll_a)
        turn = {w: cast[w] / reg[w] for w in reg if reg[w] > 0}
        mean_turn = sum(turn.values()) / len(turn) if turn else 0.0
        # a ward of b none of whose VDs was recorded at a takes the mean
        # turnout of b's other wards (declared: JUDGEMENT-CALLS §R12)
        unmatched = sorted(w for w in s if w not in turn)
        out["mean_turnout_wards"].extend([code, b, w] for w in unmatched)
        out["panel_wards"] += len(s)
        exp = {w: reg_b.get(w, 0) * turn.get(w, mean_turn) for w in s}
        E, V_tot = sum(exp.values()), sum(tot.values())
        H, V = collections.Counter(), collections.Counter()
        for w in s:
            for p, v in (h.get(w) or {}).items():
                H[p] += exp[w] / E * v
            for p, v in s[w].items():
                V[p] += tot[w] / V_tot * v
        for p in sorted(set(H) | set(V)):
            if p != "IND":
                out["city_rows"].append((code, b, p, H[p], V[p]))
        Ha, Hb = _city_shares(A["vds"]), _city_shares(B["vds"])
        out["pair_data"][(code, a, b)] = {"h": h, "s": s, "Ha": Ha, "Hb": Hb, "pr_b": B["pr"]}
        # parties new to the city with no national vote before b
        n = cityconfig.preceding(b, "NPE")
        national = _city_shares(_npe(npe[(code, n)])["vds"]) if (code, n) in npe else {}
        fresh = {p for p in Hb if p != "IND" and Ha.get(p, 0) == 0 and national.get(p, 0) == 0}
        for w in s:
            for p in fresh & set(s[w]):
                newcomer("ward", s[w][p], {"metro": code, "year": b, "ward": w, "party": p})
        for p in fresh:
            newcomer("city", V[p], {"metro": code, "year": b, "party": p})
    for code, n, l in npe_pairs:
        N, L = _npe(npe[(code, n)]), _lge(lge[(code, l)])
        note(npe[(code, n)], N)
        note(lge[(code, l)], L)
        hn = _join(_held_parts(L), N["vds"])
        s, tot, _reg = _ward_shares(L)
        for w in s:
            for p in sorted(set(hn.get(w, {})) & set(s[w])):
                if p != "IND":
                    out["npe_ward_rows"].append((code, n, l, w, p, hn[w][p], s[w][p]))
        Hn = _city_shares(N["vds"])
        V_tot = sum(tot.values())
        V = collections.Counter()
        for w in s:
            for p, v in s[w].items():
                V[p] += tot[w] / V_tot * v
        for p in sorted(set(Hn) & set(V)):
            if p != "IND":
                out["npe_city_rows"].append((code, n, l, p, Hn[p], V[p]))
    for kind in ("ward", "city"):
        if out["newcomer"][kind] is None:
            raise MakeBuildError(f"build_make: no party new to its city in the panel ({kind})")
    return out


def _corr(x, y) -> float:
    n = len(x)
    if n < 3:
        return 0.0
    mx, my = sum(x) / n, sum(y) / n
    sx = sum((a - mx) ** 2 for a in x) ** 0.5
    sy = sum((b - my) ** 2 for b in y) ** 0.5
    if sx == 0 or sy == 0:
        return 0.0
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def exclusions(panel: dict) -> list[dict]:
    """The swings left out of the record events (never out of the bounds),
    detected from the data per metro and local pair (a → b), JUDGEMENT-CALLS
    §R13:

    * **merger**: a party holding at least :data:`VANISH_MIN` of the city's
      ward vote at a that stands nowhere at b (no ward or list vote). Its
      absorber is the party standing at both whose ward swings correlate best
      with the vanished party's ward shares at a, if the correlation is at
      least :data:`CORRELATION_MIN`; the absorber's swings are left out. Below
      it the vanishing is a dissolution, recorded and excluding nothing.
    * **split**: a party new to the city with at least :data:`SPLIT_MIN` at b.
      Its source is the party whose ward swings correlate most negatively with
      the newcomer's ward shares, if at or below minus
      :data:`CORRELATION_MIN`; the source's swings are left out. Otherwise a
      new party, recorded.
    * **collapse**: a party falling from at least :data:`COLLAPSE_FROM` to
      under :data:`COLLAPSE_KEEP` of that share; its own swings are left out.

    Each entry: ``{kind, metro, a, b, party, share, partner, r, excludes}``,
    ``excludes`` the party whose swings it leaves out (None for a dissolution
    or a new party)."""
    out = []
    for (code, a, b), d in sorted(panel["pair_data"].items()):
        h, s, Ha, Hb, prb = d["h"], d["s"], d["Ha"], d["Hb"], d["pr_b"]
        wards = sorted(w for w in s if w in h)
        stood = sorted(p for p in Hb if Ha.get(p, 0) > 0 and p != "IND")
        swing = {p: [s[w].get(p, 0.0) - h[w].get(p, 0.0) for w in wards] for p in stood}
        if not stood:
            continue
        for q in sorted(Ha):
            v = Ha[q]
            if q == "IND" or v < VANISH_MIN or Hb.get(q, 0) > 0 or prb.get(q, 0) > 0:
                continue
            hq = [h[w].get(q, 0.0) for w in wards]
            r = {p: _corr(swing[p], hq) for p in stood}
            best = max(stood, key=lambda p: (r[p], p))
            merger = r[best] >= CORRELATION_MIN
            out.append({"kind": "merger" if merger else "dissolution", "metro": code, "a": a, "b": b,
                        "party": q, "share": v, "partner": best, "r": r[best],
                        "excludes": best if merger else None})
        for q in sorted(Hb):
            v = Hb[q]
            if q == "IND" or v < SPLIT_MIN or Ha.get(q, 0) > 0:
                continue
            sq = [s[w].get(q, 0.0) for w in wards]
            r = {p: _corr(swing[p], sq) for p in stood}
            src = min(stood, key=lambda p: (r[p], p))
            split = r[src] <= -CORRELATION_MIN
            out.append({"kind": "split" if split else "new party", "metro": code, "a": a, "b": b,
                        "party": q, "share": v, "partner": src, "r": r[src],
                        "excludes": src if split else None})
        for p in stood:
            if Ha[p] >= COLLAPSE_FROM and Hb[p] < COLLAPSE_KEEP * Ha[p]:
                out.append({"kind": "collapse", "metro": code, "a": a, "b": b, "party": p,
                            "share": Ha[p], "partner": None, "r": None, "excludes": p, "to": Hb[p]})
    return out


def record_events(obs) -> list[dict]:
    """The record events of ``obs``, ``[(round, key, value)]``: rounds taken
    in order, the first round in which a key appears sets its record in each
    direction (its greatest value up, its least down), and a later round whose
    greatest (least) value beats the record is an event of size new record
    minus old, after which it is the record. Each event ``{round, key,
    direction, old, new, exceedance}``."""
    by_round = collections.defaultdict(lambda: collections.defaultdict(list))
    for rnd, key, value in obs:
        by_round[rnd][key].append(value)
    record, events = {}, []
    for rnd in sorted(by_round):
        for key in sorted(by_round[rnd], key=str):
            vals = by_round[rnd][key]
            for direction, pick in (("up", max), ("down", min)):
                m = pick(vals)
                old = record.get((key, direction))
                if old is None:
                    record[(key, direction)] = m
                elif (direction == "up" and m > old) or (direction == "down" and m < old):
                    events.append({"round": rnd, "key": key, "direction": direction,
                                   "old": old, "new": m, "exceedance": abs(m - old)})
                    record[(key, direction)] = m
    return events


def _allowance(events: list[dict], fallback: float) -> dict:
    """The mean exceedance of ``events``, or ``fallback`` where there are fewer
    than :data:`MIN_RECORD_EVENTS` (JUDGEMENT-CALLS §R9, §R14)."""
    xs = [e["exceedance"] for e in events]
    if len(xs) >= MIN_RECORD_EVENTS:
        return {"value": sum(xs) / len(xs), "rule": "mean of the record events", "events": events}
    return {"value": fallback, "rule": "EDITOR_WIDEN_PP (fewer than MIN_RECORD_EVENTS events)",
            "events": events}


def allowances(panel: dict, excluded: list[dict]) -> dict:
    """``{"ward", "city"}``: how far a ward range and a citywide limit are
    widened beyond the swings' extremes, each the mean of the POOLED record
    events (a record per starting-share bin and direction over every party
    and metro, rounds by the later election of each pair) of the swings of
    parties standing at both elections, the :func:`exclusions` left out
    (JUDGEMENT-CALLS §R9)."""
    skip = {(e["metro"], e["b"], e["excludes"]) for e in excluded if e["excludes"]}
    ward = [(b, _bin(h), s - h) for code, _a, b, _w, p, h, s in panel["ward_rows"]
            if h > 0 and s > 0 and (code, b, p) not in skip]
    city = [(b, _bin(H), V - H) for code, b, p, H, V in panel["city_rows"]
            if H > 0 and V > 0 and (code, b, p) not in skip]
    fallback = EDITOR_WIDEN_PP / 100.0
    return {"ward": _allowance(record_events(ward), fallback),
            "city": _allowance(record_events(city), fallback)}


def shape_allowances(per_year: dict) -> dict:
    """``{quantity: allowance}`` for ``q_win``, ``q_run``, ``gap_min`` and
    ``gap_max``: the record events of each over the elections in order (each
    election's extreme over every metro, :func:`panel_extremes` per year), in
    the direction it is widened (:data:`SHAPE_DIRECTION`), and their mean; with
    fewer than :data:`MIN_RECORD_EVENTS`, :data:`EDITOR_WIDEN_PP` (in shares
    for the ward shapes, in points for the gaps; JUDGEMENT-CALLS §R14, the
    coordinator's D1)."""
    out = {}
    for q, direction in SHAPE_DIRECTION.items():
        obs = [(y, q, per_year[y][q]["value"]) for y in sorted(per_year)]
        events = [e for e in record_events(obs) if e["direction"] == direction]
        fallback = EDITOR_WIDEN_PP / 100.0 if q.startswith("q_") else EDITOR_WIDEN_PP
        out[q] = _allowance(events, fallback)
    return out


def _processed(tgt, processed: Path | None) -> Path:
    """The directory ``montecarlo.ward_parts`` reads the target's crosswalk
    from: the city's own, or ``processed`` (a test's constructed copy)."""
    return REPO_ROOT / tgt.crosswalk.parent if processed is None else Path(processed)


def ward_priors(city, target: str, wards: list[str], *, elections: Path | None = None,
                processed: Path | None = None) -> dict:
    """Each party's share in each of the target's wards at the preceding local
    election, its VDs joined through ``montecarlo.ward_parts(target)`` (split
    VDs apportioned by registration), and its share of the whole city's ward
    vote there: ``{"h": {ward: {code: share}}, "city": {code: share}, "file",
    "sha256", "parts", "wards_without_prior"}``. ``elections`` and
    ``processed`` name other directories holding the result files and the
    crosswalk (the tests' constructed copies)."""
    import cityconfig
    import montecarlo
    elections = REPO_ROOT / city.path("raw", "elections") if elections is None else Path(elections)
    tgt = cityconfig.Target(city=city, year=str(target))
    prev = tgt.previous_lge
    path = elections / tgt.results(prev).replace("{CODE}", city.code)
    read = _lge(path)
    parts, label = montecarlo.ward_parts(tgt, elections, _processed(tgt, processed))
    h = _join(parts, read["vds"])
    stray = sorted(set(h) - set(wards))
    if stray:
        raise MakeBuildError(f"build_make: the preceding election joins onto wards not on the map: {stray[:5]}")
    return {"h": h, "city": _city_shares(read["vds"]), "file": path.name, "sha256": read["sha256"],
            "parts": label, "wards_without_prior": sorted((w for w in wards if w not in h), key=int)}


def npe_priors(city, target: str, *, elections: Path | None = None,
               processed: Path | None = None) -> dict:
    """The same from the national election before the target
    (``Target.previous_npe``): ``{"h", "city", "file", "sha256", "year"}``. A
    missing file, or an approximation (:data:`APPROXIMATE`), refuses the
    build: the prior for parties new to local elections would be empty in
    silence. ``elections`` and ``processed`` as :func:`ward_priors`."""
    import cityconfig
    import montecarlo
    elections = REPO_ROOT / city.path("raw", "elections") if elections is None else Path(elections)
    tgt = cityconfig.Target(city=city, year=str(target))
    n = tgt.previous_npe
    files = _election_files(elections, "NPE")
    if (city.code, n) not in files:
        raise MakeBuildError(f"build_make: no national result file for {city.code} {n}, the "
                             f"prior of parties new to local elections (JUDGEMENT-CALLS §R8)")
    path = files[(city.code, n)]
    read = _npe(path)
    parts, _label = montecarlo.ward_parts(tgt, elections, _processed(tgt, processed))
    h = _join(parts, read["vds"])
    return {"h": h, "city": _city_shares(read["vds"]), "file": path.name, "sha256": read["sha256"],
            "year": n}


def _moved(start: float, extremes, allowance: float) -> list[float]:
    """``[lo, hi]``: a starting share moved by its bin's least and greatest
    swing and widened by ``allowance`` on each side, inside [0, 1]."""
    lo, hi = extremes[_bin(start)]
    return [max(0.0, start + lo - allowance), min(1.0, start + hi + allowance)]


def party_kind(code: str, local_city: dict, national_city: dict) -> str:
    """The one rule for which history a party's ward ranges and citywide limit
    are built from (JUDGEMENT-CALLS §R8): ``local`` if it had a ward vote
    anywhere in the city at the preceding local election (``local_city``, its
    citywide shares there), else ``national`` if it had a vote at the
    preceding national election, else ``newcomer``."""
    if local_city.get(code, 0) > 0:
        return "local"
    if national_city.get(code, 0) > 0:
        return "national"
    return "newcomer"


def ward_ranges(roster: list[str], wards: list[str], local: dict, national: dict,
                bins: dict, allow: dict, newcomer: dict) -> tuple[dict, dict]:
    """``(ward_ranges, party_ranges)``: each party's range of its share of a
    ward's ward-ballot votes (JUDGEMENT-CALLS §R6, §R8).

    * ``ward_ranges[ward][code] = [lo, hi]`` where the party has a prior in
      that ward: its share there at the preceding local election (h > 0),
      moved by the local swing extremes of its bin; or, for a party new to
      local elections in the city (no ward vote anywhere in it at the
      preceding local election), its share there at the preceding national
      election, moved by the national-to-local extremes of its bin.
    * ``party_ranges[code] = {kind, prior, lo, hi}``, the range in every ward
      without one of those: ``local`` (its citywide share at the preceding
      local election as the prior), ``national`` (its citywide national share,
      for a party new to local elections), or ``newcomer`` ([0, the greatest
      ward share any party new to its city with no national vote has taken]).

    Every range is widened by the ward allowance on each side."""
    A = allow["ward"]["value"]
    party = {}
    for p in roster:
        kind = party_kind(p, local["city"], national["city"])
        if kind == "local":
            party[p] = {"kind": "local", "prior": local["city"][p],
                        **dict(zip(("lo", "hi"), _moved(local["city"][p], bins["ward"], A)))}
        elif kind == "national":
            party[p] = {"kind": "national", "prior": national["city"][p],
                        **dict(zip(("lo", "hi"), _moved(national["city"][p], bins["npe_ward"], A)))}
        else:
            party[p] = {"kind": "newcomer", "prior": 0.0, "lo": 0.0,
                        "hi": min(1.0, newcomer["ward"]["value"] + A)}
    cells: dict[str, dict] = {}
    for w in wards:
        row = {}
        for p in roster:
            x = local["h"].get(w, {}).get(p, 0.0)
            if x > 0:
                row[p] = _moved(x, bins["ward"], A)
            elif party[p]["kind"] == "national" and national["h"].get(w, {}).get(p, 0.0) > 0:
                row[p] = _moved(national["h"][w][p], bins["npe_ward"], A)
        if row:
            cells[w] = row
    return cells, party


def city_limits(roster: list[str], prior_e: dict, national: dict, local_city: dict,
                bins: dict, allow: dict, newcomer: dict) -> dict:
    """``{code: {kind, prior, lo, hi}}``: each party's limit on its share of
    the city's ward ballot (JUDGEMENT-CALLS §R12), by the kind
    :func:`party_kind` gives it (the same rule as its ward ranges): a
    ``local`` party, its share at the preceding local election on the
    target's wards, weighted by each ward's expected ward vote (``prior_e``),
    moved by the citywide swing extremes of its bin; a ``national`` party,
    its citywide national share moved by the national-to-local citywide
    extremes; a ``newcomer``, [0, the greatest citywide share a party new to
    its city with no national vote has taken]. Widened by the city allowance
    on each side."""
    A = allow["city"]["value"]
    out = {}
    for p in roster:
        kind = party_kind(p, local_city, national["city"])
        if kind == "local":
            x = prior_e.get(p, 0.0)
            out[p] = {"kind": "local", "prior": x,
                      **dict(zip(("lo", "hi"), _moved(x, bins["city"], A)))}
        elif kind == "national":
            out[p] = {"kind": "national", "prior": national["city"][p],
                      **dict(zip(("lo", "hi"), _moved(national["city"][p], bins["npe_city"], A)))}
        else:
            out[p] = {"kind": "newcomer", "prior": 0.0, "lo": 0.0,
                      "hi": min(1.0, newcomer["city"]["value"] + A)}
    return out


def swing_extremes(panel: dict) -> dict:
    """The least and greatest swing per :data:`SWING_BINS` bin, of the parties
    standing at both elections: ``ward`` and ``city`` from local pairs (every
    real swing, none excluded), ``npe_ward`` and ``npe_city`` from national to
    local pairs, leaving out every (metro, local election, party) that
    collapsed from the national election to the local one: a citywide
    national share of at least :data:`COLLAPSE_FROM` and a local ward share
    under :data:`COLLAPSE_KEEP` of it, whether or not it was the party's first
    local election (JUDGEMENT-CALLS §R8)."""
    collapsed = {(c, l, p) for c, _n, l, p, Hn, V in panel["npe_city_rows"]
                 if Hn >= COLLAPSE_FROM and V < COLLAPSE_KEEP * Hn}
    return {
        "ward": _extremes_by_bin((h, s - h) for _c, _a, _b, _w, _p, h, s in panel["ward_rows"]
                                 if h > 0 and s > 0),
        "city": _extremes_by_bin((H, V - H) for _c, _b, _p, H, V in panel["city_rows"] if H > 0 and V > 0),
        "npe_ward": _extremes_by_bin((h, s - h) for c, _n, l, _w, p, h, s in panel["npe_ward_rows"]
                                     if (c, l, p) not in collapsed),
        "npe_city": _extremes_by_bin((H, V - H) for c, _n, l, p, H, V in panel["npe_city_rows"]
                                     if (c, l, p) not in collapsed),
        "npe_collapses": sorted(collapsed),
    }


def editor_bounds(city, target: str, wards: list[str], roster: list[str], *,
                  elections: Path | None = None) -> dict:
    """The schema's ``x-editor-bounds``: what the page's editor lets a reader
    set, regenerated from the past results at every build (JUDGEMENT-CALLS §R).
    They limit the editor only, never what an entry may be (SPEC-B D4).

    ``e``: each ward's share of the expected ward vote
    (:func:`expected_ward_shares`). ``q_win``, ``q_run``, ``gap_min``,
    ``gap_max``: the past extremes (``panel_extremes``, every election's under
    ``shape.per_year``) widened by ``shape.allowance`` (the mean of their
    record events, or :data:`EDITOR_WIDEN_PP` where they have fewer than
    :data:`MIN_RECORD_EVENTS`), the runner-up's capped at
    :data:`RUNNER_UP_MAX`. ``ward_ranges``, ``party_ranges``: each party's
    range in each ward (:func:`ward_ranges`); ``city_limits``: its citywide
    limit (:func:`city_limits`); ``allowance``: their widening with the
    record events it is the mean of; ``exclusions``: the swings those events
    leave out; ``swing``: the pairs, the bins' extremes and the newcomer caps.
    ``panel`` names the local files of the shape and ``sources`` the sha256 of
    every file read, so a changed file changes the bounds visibly."""
    import cityconfig
    files = _panel(city, target, elections)
    if not files:
        raise MakeBuildError(f"build_make: no cleaned LGE result file before {target}")
    by_year = collections.defaultdict(list)
    for f in files:
        by_year[f.name[3:7]].append(f)
    per_year = {y: panel_extremes(fs) for y, fs in sorted(by_year.items())}
    ext = {}
    for q, direction in SHAPE_DIRECTION.items():
        pick = min if direction == "down" else max
        ext[q] = pick((per_year[y][q] for y in sorted(per_year)), key=lambda x: x["value"])
    shape = shape_allowances(per_year)
    # the turnout of the preceding election is read from the same directory
    # as everything else; the roll snapshot and the crosswalk are not in it
    previous = None
    if elections is not None:
        tgt = cityconfig.Target(city=city, year=str(target))
        previous = Path(elections) / tgt.results(tgt.previous_lge).replace("{CODE}", city.code)
    e, provenance = expected_ward_shares(city, target, wards, previous=previous)
    panel = swing_panel(city, target, elections=elections)
    excl = exclusions(panel)
    allow = allowances(panel, excl)
    bins = swing_extremes(panel)
    local = ward_priors(city, target, wards, elections=elections)
    national = npe_priors(city, target, elections=elections)
    cells, party = ward_ranges(roster, wards, local, national, bins, allow, panel["newcomer"])
    prior_e = collections.Counter()
    for w in wards:
        for p, v in local["h"].get(w, {}).items():
            prior_e[p] += e[w] * v
    limits = city_limits(roster, prior_e, national, local["city"], bins, allow, panel["newcomer"])
    sources = {f.name: _sha(f.read_bytes()) for f in files}
    sources.update(panel["sources"])
    sources[local["file"]] = local["sha256"]
    sources[national["file"]] = national["sha256"]
    return {
        "e": e,
        "q_win": max(0.0, ext["q_win"]["value"] - shape["q_win"]["value"]),
        "q_run": min(RUNNER_UP_MAX, ext["q_run"]["value"] + shape["q_run"]["value"]),
        "gap_min": ext["gap_min"]["value"] - shape["gap_min"]["value"],
        "gap_max": ext["gap_max"]["value"] + shape["gap_max"]["value"],
        "panel_extremes": ext,
        "shape": {"per_year": per_year, "allowance": shape},
        "ward_ranges": cells,
        "party_ranges": party,
        "city_limits": limits,
        "allowance": allow,
        "exclusions": excl,
        "swing": {"pairs": [list(x) for x in panel["pairs"]],
                  "npe_pairs": [list(x) for x in panel["npe_pairs"]],
                  "bins": list(SWING_BINS),
                  "extremes": {k: bins[k] for k in ("ward", "city", "npe_ward", "npe_city")},
                  "npe_collapses": [list(x) for x in bins["npe_collapses"]],
                  "newcomer": panel["newcomer"],
                  "mean_turnout_wards": panel["mean_turnout_wards"],
                  "panel_wards": panel["panel_wards"]},
        "priors": {"local": {k: local[k] for k in ("file", "parts", "wards_without_prior")},
                   "national": {k: national[k] for k in ("file", "year")}},
        "thresholds": {"MIN_RECORD_EVENTS": MIN_RECORD_EVENTS, "EDITOR_WIDEN_PP": EDITOR_WIDEN_PP,
                       "RUNNER_UP_MAX": RUNNER_UP_MAX, "VANISH_MIN": VANISH_MIN, "SPLIT_MIN": SPLIT_MIN,
                       "COLLAPSE_FROM": COLLAPSE_FROM, "COLLAPSE_KEEP": COLLAPSE_KEEP,
                       "CORRELATION_MIN": CORRELATION_MIN},
        "panel": [f.name for f in files],
        "sources": dict(sorted(sources.items())),
        "expected_ward_vote": provenance,
        "rules": {
            "shape": ("in a painted ward the winner holds at least q_win of the ward's vote and every "
                      "other party at most q_run; a party's list share minus its ward share, in points, "
                      "is between gap_min and gap_max"),
            "ward_ranges": ("a party's share of a ward's vote lies in ward_ranges[ward][party], or, where "
                            "that is absent, in party_ranges[party]; together with the shape, the least and "
                            "greatest each party can hold in each ward, weighted by e, bound its ward vote"),
            "city_limits": "a party's share of the ward ballot lies in city_limits[party]",
            "conflict": ("where the map needs more (or less) of the vote than the citywide limit allows, "
                         "the map wins"),
            "fallback": ("a painted ward whose ranges no share vector satisfies uses the shape alone: "
                         "winner at least q_win, every other party at most q_run"),
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
        # the seeded lot's run identity; make_schema.mjs writes it into
        # x-seat-context, its one writer
        "lot": run_lot(manifest),
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
    if not context.get("lot"):
        raise MakeBuildError("build_make: the schema's x-seat-context has no lot "
                             "(model_artefact carries it and make_schema.mjs writes it), so an exact seat tie "
                             "cannot be drawn")
    try:
        seated = prediction.seats_of(pred, context["council"], order=roster,
                                     lot=context["lot"])
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
    bounds = editor_bounds(city, str(city.default_target), [str(w["id"]) for w in geom["wards"]],
                           list(manifest["parties"]))
    artefact = model_artefact(manifest, build_play.roster(), bounds)
    return {"manifest": manifest, "arrays": arrays, "raw": raw,
            "geometry": geom, "artefact": artefact, "schema": make_schema(artefact, geom)}


def run_lot(manifest: dict) -> str:
    """The published run's identity for the seeded lot, from the served draws'
    ``artefact_key`` (city, target, seed): ``seats.lot_identity``. Written into
    the model artefact (:func:`model_artefact`), from which
    ``worker-api/tools/make_schema.mjs`` alone writes the schema's
    ``x-seat-context["lot"]``, which the start (:func:`start_state`),
    the scorer (``score_forecasts.model_forecast``), the seat Worker (it sends
    the context with each entry) and the page (``interactive/pyboot/page.py``
    computes the same from the same manifest) all read, so a tied ward or an
    exact seat tie falls one way everywhere. JUDGEMENT-CALLS §Q2, §Q6."""
    import seats
    key = manifest.get("artefact_key") or {}
    missing = [k for k in ("city", "target", "seed") if key.get(k) in (None, "")]
    if missing:
        raise MakeBuildError(f"build_make: the draws' artefact_key lacks {missing}, "
                             f"so the run's lot cannot be named")
    return seats.lot_identity(key["city"], str(key["target"]), key["seed"])


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


def map_attrs() -> dict[str, str]:
    """Section 2's ward map's ``viewBox``, set in the page by the build so the
    map has its height before ``forecast.json`` arrives (owner, 2026-10-10:
    the layout must not shift; the empty map grew by its whole height when
    the data came). It is the string ``js/map.js`` sets from the same
    geometry, "0 0 W ceil(H)", with W written as JavaScript writes a number;
    ``tests/test_your_forecast_page.py`` holds the two to each other."""
    import math
    geom = geometry()
    w = float(geom["W"])
    return {"<!-- __MAKE:mapviewbox__ -->": f"0 0 {int(w) if w.is_integer() else w} {math.ceil(geom['H'])}"}


def seat_attrs() -> dict[str, str]:
    """The reader's council table's axis, ticks and header words, set on its
    region for js/make.js (``seat_table.HEAD_COUNCIL``: a single council has
    no range, so its range column carries no heading)."""
    import seat_table
    return {"<!-- __MAKE:seatscale__ -->": str(seat_table.SEAT_SCALE),
            "<!-- __MAKE:seatticks__ -->": " ".join(str(x) for x in seat_table.SEAT_TICKS),
            "<!-- __MAKE:seathead__ -->": "|".join(seat_table.HEAD_COUNCIL)}
