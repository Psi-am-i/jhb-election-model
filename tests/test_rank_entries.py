"""`rank_entries` and `/leaderboard/`: the results-night pipeline, built and
tested before the result exists (owner, 2026-10-03).

The 2021 Johannesburg result stands in for 2026's, read by the scorer's own
loader (`score_forecasts.ingest_result`, through tests/test_score_forecasts.py's
`_result`), with a schema over its roster and wards (`_schema`). The entries
are constructed as the Worker stores them (share-edge.js ENTRY_COLUMNS, the
forecast as JSON): the result itself, and variants worse on one key each.

1. ORDER. Places follow `score_forecasts.rank_key`, each entry scored by
   `score_forecasts.score`, compared with the order written out by hand.
2. TIES (JUDGEMENT-CALLS §N7). Entries equal on all three keys are placed by
   the earlier seal, then by seal id; every place is distinct. A detector
   shown to fire when the tie rule is dropped.
3. REFUSALS. An entry under a context with no forecast.json, an unscorable
   entry, an export with a missing or extra column, a repeated seal id.
4. THE EXPORT. `wrangler d1 execute --json`'s wrapper and a bare list.
5. THE PAGE. Hidden until `published = true` (no page, no nav entry, an old
   copy removed); refused when published without the artefact; once
   published, a page with no build-time figure whose one script is held to
   its LIVE regions by `stats.script_writes`; the real flag is off today.
"""
from __future__ import annotations

import copy
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module  # noqa: E402

import build_leaderboard as LB  # noqa: E402
import build_site as B  # noqa: E402
import rank_entries as RE  # noqa: E402
import score_forecasts as S  # noqa: E402
import stats as statlib  # noqa: E402
import test_score_forecasts as T  # noqa: E402

CTX = "ctx-2021-as-2026"


def _sig(n: int) -> str:
    """A seal id: 43 base64url characters, distinct in its first twelve."""
    return f"{n:012d}".replace("0", "A") + "x" * 31


def _row(n, forecast, sealed_at, label=""):
    return {"seal_id": _sig(n), "sealed_at": sealed_at, "label": label, "model_ref": "r-test",
            "context_ref": CTX, "state": "AAAA", "forecast": json.dumps(forecast)}


def _setup():
    result = T._result()
    schema = T._schema(result)
    base = T._self_forecast(result, schema)
    wards = schema["x-ward-ids"]
    parties = schema["x-seat-context"]["parties"]
    # one ward called for the party that came second there: worse on wards
    w0 = wards[0]
    other = next(p for p in parties if p != result["wards"][w0] and base["combined_share"].get(p, 0) > 0)
    ward_miss = copy.deepcopy(base)
    ward_miss["ward_calls"][0] = other
    # a sliver of vote moved between the two largest parties: worse on the vote
    big = sorted(base["combined_share"], key=lambda p: -base["combined_share"][p])[:2]
    vote_miss = copy.deepcopy(base)
    eps = schema["x-share-sum"]["target"] * 1e-5
    vote_miss["combined_share"][big[0]] -= eps
    vote_miss["combined_share"][big[1]] += eps
    rows = [
        _row(1, base, 1_000, "Late perfect"),       # ties 2 and 3, sealed last of them
        _row(2, base, 500, ""),                     # ties, earliest second, the higher seal id
        _row(3, base, 500, "Same second"),          # ties, earliest second, ... see ids
        _row(4, ward_miss, 100, "Ward miss"),
        _row(5, vote_miss, 200, "Vote miss"),
    ]
    return result, schema, rows


def _board(rows=None, **kw):
    result, schema, base_rows = _setup()
    return RE.rank_entries(base_rows if rows is None else rows,
                           {CTX: {"schema": schema, "context_ref": CTX}}, result, **kw)


def order_problems(rows, board) -> list[str]:
    """The board's order against rank_key, then seal time, then seal id, by hand."""
    result, schema, _ = _setup()
    keyed = []
    for r in rows:
        s = S.score(json.loads(r["forecast"]), schema, result)
        keyed.append(((s["seat_error"], -s["wards_called"], s["list_vote_error"]),
                      r["sealed_at"], r["seal_id"]))
    want = [k[2][:RE.ID_CHARS] for k in sorted(keyed)]
    got = [x["id"] for x in board["rows"]]
    out = []
    if got != want:
        out.append(f"order {got}, want {want}")
    if [x["place"] for x in board["rows"]] != list(range(1, len(rows) + 1)):
        out.append(f"places {[x['place'] for x in board['rows']]} are not one each")
    return out


# ----------------------------------------------------------------- 1, 2

def test_entries_are_ranked_by_the_three_keys_then_the_earlier_seal():
    _result, _schema, rows = _setup()
    board = _board()
    assert order_problems(rows, board) == []
    first = board["rows"]
    # the three equal entries lead, earliest seal first, the same second by id
    assert [r["id"] for r in first[:3]] == [_sig(2)[:12], _sig(3)[:12], _sig(1)[:12]]
    assert first[0]["seat_error"] == 0 and first[0]["wards_called"] == board["wards"]
    assert first[0]["name"] == "Anonymous #" + _sig(2)[:6]
    assert first[2]["name"] == "Late perfect"
    # one ward wrong and a sliver of vote: each worse on exactly its key
    by = {r["name"]: r for r in first}
    assert by["Ward miss"]["wards_called"] == board["wards"] - 1
    assert by["Vote miss"]["list_vote_error"] >= by["Late perfect"]["list_vote_error"]
    assert board["entries"] == len(rows)
    assert first[0]["sealed_at"] == "1970-01-01T00:08:20Z"
    assert set(first[0]) == {"place", "id", "name", "seat_error", "wards_called", "list_vote_error", "sealed_at"}


def test_order_check_fires_when_the_tie_rule_is_dropped():
    _result, _schema, rows = _setup()
    board = _board()
    swapped = copy.deepcopy(board)
    swapped["rows"][0], swapped["rows"][2] = swapped["rows"][2], swapped["rows"][0]
    assert order_problems(rows, swapped)
    # rank without the seal times orders ties by id alone: 1 before 2
    real = S.rank
    try:
        S.rank = lambda scores, saved_at=None: real(scores)
        assert order_problems(rows, _board())
    finally:
        S.rank = real
    shared = copy.deepcopy(board)
    shared["rows"][1]["place"] = 1
    assert order_problems(rows, shared)
    assert order_problems(rows, board) == []


# ----------------------------------------------------------------- 3

def test_an_entry_that_cannot_be_ranked_stops_the_ranking():
    result, schema, rows = _setup()
    stale = copy.deepcopy(rows)
    stale[0]["context_ref"] = "an-older-context"
    try:
        _board(stale)
        raise AssertionError("an entry under an unknown context was ranked")
    except ValueError as e:
        assert "an-older-context" in str(e) and _sig(1) in str(e)
    broken = copy.deepcopy(rows)
    f = json.loads(broken[3]["forecast"])
    f["ward_calls"] = f["ward_calls"][:-1]
    broken[3]["forecast"] = json.dumps(f)
    try:
        _board(broken)
        raise AssertionError("an unscorable entry was ranked")
    except ValueError as e:
        assert _sig(4) in str(e)


# ----------------------------------------------------------------- 4

def test_the_export_is_read_in_wrangler_s_shape_or_as_rows():
    _result, _schema, rows = _setup()
    assert RE.entry_columns() == list(rows[0])
    with tempfile.TemporaryDirectory() as t:
        p = Path(t, "export.json")
        p.write_text(json.dumps([{"results": rows, "success": True, "meta": {}}]))
        assert RE.load_export(p) == rows
        p.write_text(json.dumps(rows))
        assert RE.load_export(p) == rows
        for bad in ([{**rows[0], "ip": "x"}], [{k: v for k, v in rows[0].items() if k != "label"}],
                    [rows[0], rows[0]]):
            p.write_text(json.dumps(bad))
            try:
                RE.load_export(p)
                raise AssertionError(f"accepted {bad!r:.80}")
            except ValueError:
                pass
        p.write_text(json.dumps([{"results": rows, "success": False}]))
        try:
            RE.load_export(p)
            raise AssertionError("accepted a failed export")
        except ValueError:
            pass


# ----------------------------------------------------------------- 5

def _content(published: bool, with_board: bool = True) -> Path:
    t = Path(tempfile.mkdtemp(prefix="lb-"))
    (t / "joburg").mkdir()
    (t / "joburg" / "leaderboard.toml").write_text(
        f"published = {'true' if published else 'false'}\ntop = 2\n")
    if with_board:
        (t / "joburg" / "leaderboard.json").write_text(json.dumps(_board()))
    return t


def test_the_leaderboard_is_hidden_until_the_flag_is_set():
    # the real flag: off, so no page and no nav entry
    assert LB.settings("joburg") == {"published": False, "top": LB.settings("joburg")["top"]}
    assert not (ROOT / "site" / LB.LB_DIR).exists()
    assert ("leaderboard/", "leaderboard") not in B.nav_items()
    assert 'href="leaderboard/"' not in B.nav_for("forecast")
    # published: after "your forecast"
    items = B.nav_items(True)
    i = [h for h, _l in items].index(LB.LB_HREF)
    assert items[i - 1][1] == "your forecast" and items[i][1] == "leaderboard"
    assert B.nav_items(False) == list(B.NAV_ITEMS)
    out = Path(tempfile.mkdtemp(prefix="lbout-"))
    try:
        (out / LB.LB_DIR).mkdir()
        (out / LB.LB_DIR / "index.html").write_text("old")
        assert LB.write_assets(out, "joburg", _content(False)) == []
        assert not (out / LB.LB_DIR).exists(), "an earlier page survived with the flag off"
        try:
            LB.write_assets(out, "joburg", _content(True, with_board=False))
            raise AssertionError("published without an artefact")
        except SystemExit as e:
            assert "rank_entries" in str(e)
        written = LB.write_assets(out, "joburg", _content(True))
        assert sorted(written) == ["leaderboard/js/leaderboard.js", "leaderboard/leaderboard.json"]
        data = json.loads((out / "leaderboard" / "leaderboard.json").read_text())
        assert data["top"] == 2 and len(data["rows"]) == 5
    finally:
        shutil.rmtree(out)


def test_the_published_page_holds_no_figure_and_its_script_only_its_regions():
    out = Path(tempfile.mkdtemp(prefix="lbpage-"))
    try:
        __import__("site_assets").write(out)      # the scripts every page loads
        LB.write_assets(out, "joburg", _content(True))
        html = LB.assemble(B.shell, __import__("build_play").one_level_down)
        (out / LB.LB_PAGE).write_text(html)
        main = html[html.index('<main class="lb">'):html.index("</main>")]
        assert not re.search(r"\d", re.sub(r"<[^>]*>", "", main)), "a typed figure in the page"
        assert '<script type="module" src="js/leaderboard.js"></script>' in html
        assert 'class="pg-doc pg-board"' in html and 'href="../privacy"' in html
        for region in ("lb-top", "lb-mine"):
            assert html.count(f'data-live="{region}"') == 1
        assert statlib.LIVE_WRITERS["leaderboard/js/leaderboard.js"] == {"lb-top", "lb-mine"}
        assert statlib.script_writes(html, page=out / LB.LB_PAGE, root=out) == []
        # constructed violation: the script reaching outside its regions
        js = out / "leaderboard" / "js" / "leaderboard.js"
        js.write_text(js.read_text() + '\ndocument.querySelector("h1").textContent = "1";\n')
        assert statlib.script_writes(html, page=out / LB.LB_PAGE, root=out)
    finally:
        shutil.rmtree(out)


def test_a_reader_s_link_finds_their_entry_id():
    script = r"""
const { idOf } = await import("%s");
const s = "lz3k2a." + "%s";
process.stdout.write(JSON.stringify([
  idOf("https://joburg.whysoserious.city/your-forecast/?v=1&c=x&f=AA&n=T&s=" + s),
  idOf(s), idOf("%s"), idOf("nonsense"), idOf("https://x.test/?f=1")]));
""" % ((ROOT / "interactive/js/leaderboard.js").as_uri(), _sig(7), _sig(7))
    with tempfile.TemporaryDirectory() as t:
        f = Path(t, "id.mjs")
        # the module touches the DOM at load: give it a stand-in
        f.write_text("globalThis.document = { querySelector: () => ({ addEventListener() {} }) };\n"
                     "globalThis.location = { search: '' };\n"
                     "globalThis.fetch = () => new Promise(() => {});\n" + script)
        p = subprocess.run(["node", str(f)], capture_output=True, text=True, timeout=30)
    assert p.returncode == 0, p.stderr
    want = _sig(7)[:12]
    assert json.loads(p.stdout) == [want, want, want, "", ""]


if __name__ == "__main__":
    sys.exit(run_module(sys.modules[__name__]))
