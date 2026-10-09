"""Our prediction is rule A, from one function (SPEC-A G1, G3, G4).

``src/prediction.py`` reduces the forecast's simulations to one complete
result: each ward to the party that wins it in the most simulations, each
party's mean whole votes on each ballot, seats by the law. This module holds
that to one definition and shows each guard can see:

G1. ONE DEFINITION.
    * the modules that import ``prediction`` are exactly the declared four,
      scanned both ways over every ``src/*.py`` and the page's entry;
    * no other function reduces the draws' ward winners or votes to a call or
      a mean, except the exemptions listed with their reasons (each of which
      must still match a site);
    * a tied ward resolves one way through the rule, the scorer, the build's
      start, and the page's hand-off and map, whatever order the parties come
      in;
    * the whole votes are the exact mean, rounded half to even.
G3. A MISSING BALLOT IS REFUSED, NAMED: no list block, a list block that is a
    copy of the ward block, a page cell without a list block.
G4. NO PARTY IS SUMMED. Small parties under one quota each keep their own
    columns and win nothing; summed into one column they would win a seat.

Every input is constructed; nothing here runs the model or reads ``data/``.
The test that the seat law on a draw's recorded votes reproduces that draw's
council needs a model run and lives in ``tests/test_chain.py``.
"""
from __future__ import annotations

import ast
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, scanned  # noqa: E402

import prediction as P  # noqa: E402

SRC = ROOT / "src"
PAGE = ROOT / "interactive" / "pyboot" / "page.py"

#: The modules that may import ``prediction``: the scorer (our prediction as
#: it is scored), the build (section 2's start), the seat path a reader's
#: forecast takes (``prediction.seats_of``), the page's engine, and the three
#: ward-call sites routed through ``prediction.top_party`` (the claims'
#: modal winners, the diagnostic, the backtest's ward hit rate).
DECLARED_IMPORTERS = {"score_forecasts", "build_make", "reader_seats", "page",
                      "scenarios", "diagnose", "score"}


def _population() -> list[Path]:
    return sorted(SRC.glob("*.py")) + [PAGE]


# ==========================================================================
# G1: one definition
# ==========================================================================

def importers(paths) -> set[str]:
    """The module names among ``paths`` that import ``prediction``."""
    found = set()
    for path in paths:
        if path.name == "prediction.py":
            continue
        tree = ast.parse(Path(path).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(a.name == "prediction" for a in node.names):
                found.add(Path(path).stem)
            elif isinstance(node, ast.ImportFrom) and node.module == "prediction":
                found.add(Path(path).stem)
    return found


def test_rule_a_has_one_definition_and_its_importers_are_declared():
    files = _population()
    scanned(files, of=len(list(SRC.glob("*.py"))) + 1, low=1.0, high=1.0,
            what="files scanned for imports of prediction",
            denominator="src/*.py and interactive/pyboot/page.py")
    found = importers(files)
    assert found == DECLARED_IMPORTERS, (
        f"undeclared importers {sorted(found - DECLARED_IMPORTERS)}; declared and "
        f"absent {sorted(DECLARED_IMPORTERS - found)}")
    # it can see: a module importing prediction is reported, and removed, quiet
    with tempfile.TemporaryDirectory() as tmp:
        stray = Path(tmp) / "stray_reader.py"
        stray.write_text("import prediction as P\n", encoding="utf-8")
        assert importers(files + [stray]) == DECLARED_IMPORTERS | {"stray_reader"}
        stray.write_text("from prediction import rule_a\n", encoding="utf-8")
        assert importers(files + [stray]) == DECLARED_IMPORTERS | {"stray_reader"}
        stray.unlink()
    assert importers(files) == DECLARED_IMPORTERS


#: What marks a ward-winner source and a vote source. A NAME is tainted when
#: it contains one of these, or is assigned (directly, through a loop or a
#: comprehension, to a fixed point) from an expression that reads one, so a
#: clone that renames ``arrays["ward_winner"]`` to ``w`` is still seen.
WIN_SOURCES = ("ward_winner", "winners", "ward_probabilities", "ward_probs")
VOTE_SOURCES = ("ward_vote", "list_vote", "pr_vote_draws", "ward_vote_draws")
#: A modal call: these, or ``max``/``min`` with a ``key=``, on a ward-winner
#: source. A mean: these, or ``sum(axis=0)``, on a vote source.
MODAL_CALLS = {"argmax", "argsort", "bincount", "most_common"}
MEAN_CALLS = {"mean", "median"}

#: (file, function) -> why the flagged calls there are not a second rule A.
#: Populated from the widened scan's output (2026-10-08 fix round); a key
#: matching no site fails the test. Three sites the scan found were ROUTED
#: through ``prediction.top_party`` instead (scenarios.modal_winners,
#: diagnose.main's ward call, score.score_wards), so they are not here.
EXEMPT = {
    ("montecarlo.py", "main"): (
        "ward_winner_probs.csv's `winner` column is order[0] of an unstable "
        "argsort of the ward-winner counts (SPEC-A M11); routing it changes "
        "montecarlo.py beyond a recorded field, which brings the whole suite "
        "forward (FLOW.md). Pending owner decision (s1/SYNTHESIS.md item 8); "
        "covered meanwhile by test_served_draws check 2 (the winner agrees "
        "wherever the top count is unique). The function's other flagged call, "
        "`seat_matrix.argmax`, is over seats, not wards."),
    ("montecarlo.py", "run_model"): (
        "the draw itself (`ward_tally.argmax`: one draw's ward winners) and the "
        "40_draws summary's mean shares and mean seats: forecast statistics "
        "over the simulations, not a prediction."),
    ("diagnose.py", "main"): (
        "mean SHARES per ballot for the diagnostic's vote table (a forecast "
        "statistic). Its ward call is routed through prediction.top_party."),
    ("render_home.py", "_overhang"): (
        "the median list share over the simulations in which item 16 applies: "
        "a published forecast statistic, not a prediction."),
    ("reweight.py", "ward_win_probability"): (
        "the weighted share of draws each party wins a ward: a probability "
        "(the forecast map), not a call."),
    ("reweight.py", "scored_as_results"): (
        "the mean over the draws of a reader's list-vote ERROR (a score), not "
        "of the draws' votes."),
    ("scenarios.py", "main"): (
        "`moved.most_common(6)`: which ward flips are most frequent, a report "
        "of counts, not a call. Its ward calls are modal_winners, routed."),
    ("backtest.py", "actual_result"): (
        "the winner of each ward in the REAL result (the ground truth's vote "
        "tallies), not a reduction over simulations."),
    ("page.py", "_ward_calls"): (
        "`hit` and the stable argsort: which parties win the ward in any "
        "weighted draw and their order in the map's tooltip distribution. The "
        "call itself is prediction.ward_calls."),
}


def _call_name(func) -> str | None:
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def _names_in(node) -> set[str]:
    """Every name, attribute, argument and string constant under ``node``."""
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
        elif isinstance(n, ast.arg):
            out.add(n.arg)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            out.add(n.value)
    return out


def _reads(names: set[str], sources, tainted: set[str]) -> bool:
    return bool(names & tainted) or any(s in n for n in names for s in sources)


def _tainted(fn, sources) -> set[str]:
    """Names in ``fn`` that hold, or were derived from, one of ``sources``."""
    args = fn.args.posonlyargs + fn.args.args + fn.args.kwonlyargs
    tainted = {a.arg for a in args if any(s in a.arg for s in sources)}
    changed = True
    while changed:
        changed = False
        for n in ast.walk(fn):
            if isinstance(n, ast.Assign):
                pairs = [(t, n.value) for t in n.targets]
            elif isinstance(n, (ast.AnnAssign, ast.AugAssign)) and n.value is not None:
                pairs = [(n.target, n.value)]
            elif isinstance(n, (ast.For, ast.comprehension)):
                pairs = [(n.target, n.iter)]
            else:
                continue
            for target, value in pairs:
                if _reads(_names_in(value), sources, tainted):
                    new = {x.id for x in ast.walk(target) if isinstance(x, ast.Name)} - tainted
                    if new:
                        tainted |= new
                        changed = True
    return tainted


def reduction_sites(source: str, filename: str) -> list[tuple[str, str, str]]:
    """``(file, function, call text)`` for every flagged call, each attributed
    to the innermost function holding it."""
    tree = ast.parse(source)
    out: list[tuple[str, str, str]] = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        win, vote = _tainted(fn, WIN_SOURCES), _tainted(fn, VOTE_SOURCES)
        stack = list(ast.iter_child_nodes(fn))
        while stack:
            node = stack.pop()
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            stack.extend(ast.iter_child_nodes(node))
            if not isinstance(node, ast.Call):
                continue
            name, names = _call_name(node.func), _names_in(node)
            keyed = name in ("max", "min") and any(k.arg == "key" for k in node.keywords)
            axis0 = name == "sum" and any(
                k.arg == "axis" and isinstance(k.value, ast.Constant) and k.value.value == 0
                for k in node.keywords)
            if ((name in MODAL_CALLS or keyed) and _reads(names, WIN_SOURCES, win)) or \
                    ((name in MEAN_CALLS or axis0) and _reads(names, VOTE_SOURCES, vote)):
                out.append((filename, fn.name, ast.get_source_segment(source, node) or ""))
    return out


#: A rule-A clone that renames its sources before reducing them: the case the
#: first, name-only detector could not see (blind diff review, 2026-10-08).
CLONE = """
def clone(arrays):
    w = arrays["ward_winner"]
    v = arrays["list_vote"]
    calls = [np.bincount(w[:, j]).argmax() for j in range(w.shape[1])]
    return calls, v.mean(axis=0)
"""


def test_no_modal_or_mean_reduction_over_draws_outside_prediction():
    files = [f for f in _population() if f.name != "prediction.py"]
    scanned(files, of=len(_population()) - 1, low=1.0, high=1.0,
            what="files scanned for reductions over the draws",
            denominator="src/*.py and page.py, less prediction.py")
    sites = []
    for path in files:
        sites += reduction_sites(path.read_text(encoding="utf-8"), path.name)
    flagged = {(f, fn) for f, fn, _ in sites}
    stray = sorted(flagged - set(EXEMPT))
    assert not stray, (
        "a reduction over the draws' ward winners or votes outside "
        "src/prediction.py: " + "; ".join(f"{f}:{fn}: {t}" for f, fn, t in sites
                                          if (f, fn) in stray)
        + ". Call prediction.ward_calls / top_party / mean_votes instead, or "
          "exempt it here with the reason.")
    dead = sorted(set(EXEMPT) - flagged)
    assert not dead, f"exemptions matching no site (register -> code): {dead}"
    # the rule sees prediction.py's own reductions, so it is not blind there
    own = reduction_sites((SRC / "prediction.py").read_text(encoding="utf-8"), "prediction.py")
    assert {fn for _, fn, _ in own} >= {"ward_calls"}
    # it can see: the renaming clone is flagged at both reductions; removed, quiet
    caught = reduction_sites(CLONE, "fake.py")
    assert {t for _, _, t in caught} >= {"np.bincount(w[:, j])", "v.mean(axis=0)"}, caught
    assert reduction_sites(CLONE.replace("arrays[\"ward_winner\"]", "arrays[\"seat\"]")
                           .replace("arrays[\"list_vote\"]", "arrays[\"seat\"]"),
                           "fake.py") == []
    assert reduction_sites("def pick(d):\n    return max(d, key=d.get)\n", "fake.py") == []
    keyed = "def pick(ward_probs):\n    return max(ward_probs, key=ward_probs.get)\n"
    assert reduction_sites(keyed, "fake.py")


# -- one tie, every caller --------------------------------------------------

#: The constructed tie: two wards, ward "1" won by ZED in half the draws and
#: by ABC in the other half, ward "2" by ZED always. ZED is listed FIRST, so a
#: rule that follows the order of the parties would call ward "1" for ZED.
TIE_PARTIES = ["ZED", "ABC"]
TIE_WARDS = ["1", "2"]
#: Draws: the four-draw pattern repeated, so the page's effective-draw floor
#: (reweight.MIN_EFFECTIVE_DRAWS) is met by uniform weights.
TIE_REPEAT = 100


def _tie_draws():
    import reweight as R
    pattern = np.array([[0, 0], [0, 0], [1, 0], [1, 0]], dtype=np.uint8)
    reps = max(TIE_REPEAT, -(-R.MIN_EFFECTIVE_DRAWS // len(pattern)) + 1)
    winners = np.tile(pattern, (reps, 1))
    n = winners.shape[0]
    cols = sorted(TIE_PARTIES)                       # ["ABC", "ZED"]
    rng = np.random.default_rng(7)
    ward_votes = rng.integers(40_000, 60_000, size=(n, 2)).astype(np.uint32)
    list_votes = rng.integers(40_000, 60_000, size=(n, 2)).astype(np.uint32)
    return winners, ward_votes, list_votes, cols


def _tie_schema(cols) -> dict:
    """The entry schema's shape over the tie's parties and wards. The entry
    version is make-state.js FORMAT, read; the editor's bounds are constructed
    (equal ward shares, bounds wide enough to bind nothing), because the build
    encodes the start through the page's encoder, which reads them."""
    import re
    fmt = re.search(r'export const FORMAT = "([^"]+)";',
                    (ROOT / "interactive/js/make-state.js").read_text()).group(1)
    return {"properties": {"v": {"const": fmt}, "model_ref": {"enum": ["test"]}},
            "x-seat-context": {"city": "test", "target": "2026", "council": 5,
                               "wards": list(TIE_WARDS), "parties": list(cols),
                               "no_pr_list": []},
            "x-editor-bounds": {"e": {w: 1 / len(TIE_WARDS) for w in TIE_WARDS},
                                "q_win": 0.0, "q_run": 1.0, "gap_min": -100.0, "gap_max": 100.0,
                                "ward_ranges": {},
                                "party_ranges": {c: {"kind": "newcomer", "prior": 0.0, "lo": 0.0, "hi": 1.0}
                                                 for c in cols},
                                "city_limits": {c: {"kind": "newcomer", "prior": 0.0, "lo": 0.0, "hi": 1.0}
                                                for c in cols}},
            "x-ward-ids": list(TIE_WARDS)}


def _tie_cell():
    """A served cell (manifest + base.bin) holding the tie, packed by reweight."""
    import reweight as R
    winners, wv, lv, cols = _tie_draws()
    n = winners.shape[0]
    seats = np.tile(np.array([[2, 3, 0]], dtype=np.uint8), (n, 1))
    council = np.tile(np.array([[3, 5]], dtype=np.uint8), (n, 1))
    turnout = np.tile(np.array([[0.5, 0.4, 0.6, 0.55]]), (n, 1))
    blob, table = R.pack([("seats/deduct", seats, cols + ["OTHER"]),
                          ("council/deduct", council, ["threshold", "council_size"]),
                          ("ward_winner", winners, TIE_WARDS),
                          ("ward_vote", wv, cols), ("list_vote", lv, cols),
                          ("pool_turnout", turnout, ["a", "b", "c", "d"])])
    manifest = {"format": R.FORMAT, "draws": n, "laws": ["deduct"], "parties": cols,
                "ward_parties": list(TIE_PARTIES), "blocks": table,
                "centres": {"refused": True, "source": "test", "reason": "test"},
                "artefact_key": {"model_sha256": "test"}}
    return manifest, blob, R.unpack(blob, manifest)


def _page():
    """The page's engine, imported as the native harness imports it."""
    import importlib
    if str(PAGE.parent) not in sys.path:
        sys.path.insert(0, str(PAGE.parent))
    page = importlib.import_module("page")
    page._CELLS.clear()
    page._PUBLISHED = None
    page.set_polls("[]")
    return page


def test_a_tied_ward_resolves_one_way_through_build_handoff_compute_and_scorer():
    import build_make
    import score_forecasts as SF
    winners, wv, lv, cols = _tie_draws()
    # control: the two rules differ on this tie
    counts = np.bincount(winners[:, 0].astype(np.int64), minlength=2)
    assert counts[0] == counts[1]
    assert TIE_PARTIES[int(np.argmax(counts))] == "ZED"
    want = min(TIE_PARTIES)
    assert want == "ABC"

    pred = P.rule_a(winners, TIE_PARTIES, TIE_WARDS, wv, lv, cols)
    assert pred["ward_calls"] == ["ABC", "ZED"]
    # the order of the parties does not move the call
    flipped = 1 - winners
    again = P.rule_a(flipped, list(reversed(TIE_PARTIES)), TIE_WARDS, wv, lv, cols)
    assert again["ward_calls"] == pred["ward_calls"]

    schema = _tie_schema(cols)
    scored = SF.model_forecast(winners, TIE_PARTIES, TIE_WARDS, wv, lv, cols, schema)
    assert scored["ward_calls"][0] == want

    manifest, blob, arrays = _tie_cell()
    # the build's start, encoded and decoded by the page's own encoder
    start = build_make.start_state(manifest, arrays, schema)
    assert start["ward_calls"][0] == want

    page = _page()
    try:
        page.load_cell(".", json.dumps(manifest), blob)
        h = json.loads(page.handoff(json.dumps({"settings": {"cell": "."}})))
        assert not h.get("refused"), h
        assert h["ward_calls"]["1"] == want
        out = json.loads(page.compute(json.dumps({"cell": ".", "law": "deduct"})))
        assert out["refused"] is None, out
        assert {x["ward"]: x["winner"] for x in out["wards"]}["1"] == want
    finally:
        page._CELLS.clear()
        page._PUBLISHED = None


def test_rule_a_whole_votes_are_the_exact_mean():
    """Half to even, in integers: 2.5 -> 2, 3.5 -> 4, off the half to nearest.
    Control: half up would give 3 for 2.5, so the test separates the two."""
    votes = np.array([[2, 3, 1, 10], [3, 4, 2, 10]], dtype=np.uint32)   # means 2.5, 3.5, 1.5, 10
    got = P.mean_votes(votes, ["a", "b", "c", "d"])
    assert got == {"a": 2, "b": 4, "c": 2, "d": 10}
    assert int(np.floor(2.5 + 0.5)) == 3 != got["a"]
    off = np.array([[2, 3], [3, 3], [3, 4]], dtype=np.int64)              # 2.667, 3.333
    assert P.mean_votes(off, ["a", "b"]) == {"a": 3, "b": 3}
    # equal weights take the integer path exactly; a uint32 column whose sum
    # passes 2**32 is not wrapped
    big = np.full((5_000, 1), 1_000_001, dtype=np.uint32)
    assert P.mean_votes(big, ["x"], np.full(5_000, 0.2)) == {"x": 1_000_001}
    # other weights: the weighted mean, half to even
    w = np.array([3.0, 1.0])
    assert P.mean_votes(np.array([[1], [3]]), ["x"], w) == {"x": round(1.5)}
    # refusals: floats, negatives, wrong width
    for bad in (np.array([[1.5, 2.0]]), np.array([[-1, 2]]), np.array([[1, 2, 3]])):
        try:
            P.mean_votes(bad, ["a", "b"])
        except P.RuleAError:
            continue
        raise AssertionError(f"mean_votes accepted {bad!r}")


# ==========================================================================
# G3: a missing ballot is refused, by name
# ==========================================================================

def test_a_missing_or_copied_ballot_is_refused_by_name():
    winners, wv, lv, cols = _tie_draws()
    for kwargs, words in (({"list_votes": None}, "list_vote"),
                          ({"ward_votes": None}, "ward_vote"),
                          ({"list_votes": wv}, "copy of the other")):
        args = {"ward_votes": wv, "list_votes": lv, **kwargs}
        try:
            P.rule_a(winners, TIE_PARTIES, TIE_WARDS, args["ward_votes"],
                     args["list_votes"], cols)
        except P.RuleAError as exc:
            assert words in str(exc), (words, str(exc))
        else:
            raise AssertionError(f"rule_a accepted {kwargs}")
    # quiet when both are there
    P.rule_a(winners, TIE_PARTIES, TIE_WARDS, wv, lv, cols)


def test_the_page_and_the_build_refuse_a_cell_without_a_list_vote_block():
    import build_make
    import reweight as R
    manifest, blob, arrays = _tie_cell()
    table = [b for b in manifest["blocks"] if b["name"] != "list_vote"]
    # repack without the block, so the cell is a real file that unpacks
    blocks = [(b["name"], arrays[b["name"]], b["columns"]) for b in table]
    blob2, table2 = R.pack(blocks)
    manifest2 = dict(manifest, blocks=table2)
    page = _page()
    try:
        page.load_cell(".", json.dumps(manifest2), blob2)
        h = json.loads(page.handoff(json.dumps({"settings": {"cell": "."}})))
        assert "list_vote" in (h.get("refused") or ""), h
        page.load_cell(".", json.dumps(manifest), blob)
        page._PUBLISHED = None
        h = json.loads(page.handoff(json.dumps({"settings": {"cell": "."}})))
        assert not h.get("refused"), h
    finally:
        page._CELLS.clear()
        page._PUBLISHED = None
    arrays2 = R.unpack(blob2, manifest2)
    try:
        build_make.start_state(manifest2, arrays2, _tie_schema(sorted(TIE_PARTIES)))
    except build_make.MakeBuildError as exc:
        assert "list_vote" in str(exc)
    else:
        raise AssertionError("the build accepted a draw file with no list_vote block")


# ==========================================================================
# G4: nothing is summed
# ==========================================================================

def test_no_party_is_summed_and_summing_would_seat_differently():
    """A council of ten, five wards. Four large parties hold a little over two
    quotas each; six minor parties each hold a sixth of a quota of the
    combined vote, a whole quota together. Rule A keeps all ten columns and the
    largest remainders go to the large parties, so the minors win nothing; the
    same votes summed into one ``OTHER`` column hold a quota and win OTHER a
    seat. So summing before the law is not a display choice: it seats
    differently."""
    combined = {"A": 23_000, "B": 22_800, "C": 22_200, "D": 22_000,
                **{f"M{k}": 1_666 for k in range(6)}}
    cols = list(combined)
    ward_row = np.array([c // 2 for c in combined.values()], dtype=np.int64)
    list_row = np.array(list(combined.values()), dtype=np.int64) - ward_row
    ward_row[0] -= 1
    list_row[0] += 1                      # the two ballots are not copies
    ward_votes, list_votes = np.vstack([ward_row] * 2), np.vstack([list_row] * 2)
    winners = np.array([[0, 0, 1, 1, 2]] * 2, dtype=np.int64)
    wards = [str(k) for k in range(1, 6)]
    pred = P.rule_a(winners, cols, wards, ward_votes, list_votes, cols)
    assert list(pred["list_votes"]) == cols and list(pred["ward_votes"]) == cols, \
        "a column was summed or dropped"
    minors = [c for c in cols if c.startswith("M")]
    total = sum(combined.values())
    assert all(combined[m] < total / 10 for m in minors), "a minor holds a quota"
    assert sum(combined[m] for m in minors) >= total / 10 - len(minors), \
        "the minors together do not hold a quota, so summing could not seat them"
    kept = P.seats_of(pred, 10)
    seats = lambda r: {p: v["total"] for p, v in r["seats"].items()}  # noqa: E731
    assert sum(seats(kept).values()) == 10
    assert not any(m in kept["seats"] for m in minors)
    summed = {"ward_calls": pred["ward_calls"],
              "ward_votes": {**{p: pred["ward_votes"][p] for p in cols if p not in minors},
                             "OTHER": sum(pred["ward_votes"][m] for m in minors)},
              "list_votes": {**{p: pred["list_votes"][p] for p in cols if p not in minors},
                             "OTHER": sum(pred["list_votes"][m] for m in minors)}}
    lumped = P.seats_of(summed, 10)
    assert seats(lumped).get("OTHER", 0) > 0
    assert seats(kept) != seats(lumped)


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
