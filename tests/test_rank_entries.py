"""`rank_entries` and `/leaderboard/`: the results-night pipeline, built and
tested before the result exists (owner, 2026-10-03).

The 2021 Johannesburg result stands in for 2026's, read by the scorer's own
loader (`score_forecasts.ingest_result`, through tests/test_score_forecasts.py's
`_result`), with a schema over its roster and wards (`_schema`). The entries
are constructed as the Worker stores them (share-edge.js ENTRY_COLUMNS, the
forecast as JSON): the result itself, and variants worse on one key each.

1. ORDER. Places follow `score_forecasts.rank_key`, each entry scored by
   `score_forecasts.score`, the vote error rounded to `VOTE_DP` decimals as
   the page prints it, compared with the order written out by hand. An entry
   off on seats with every ward right places below one right on seats with a
   ward missed: the first key decides before the second.
2. TIES (JUDGEMENT-CALLS §N7). Entries equal on all three keys are placed by
   the earlier seal, then by seal id; every place is distinct. A detector
   shown to fire when the tie rule is dropped.
3. AFTER PUBLICATION. `--drop` removes an entry and renumbers the places;
   `--anonymise` replaces every name; an unknown id is refused.
3. REFUSALS. An entry under a context with no forecast.json, an unscorable
   entry, an export with a missing or extra column, a repeated seal id.
4. THE EXPORT. `wrangler d1 execute --json`'s wrapper and a bare list.
5. THE PAGE. Hidden until `published = true` (no page, no nav entry, an old
   copy removed); refused when published without the artefact; once
   published, every entry in the artefact, and a page with no build-time
   figure whose one script is held to its LIVE regions by
   `stats.script_writes`; the real flag is off today. The artefact and its
   source are gitignored, and deploy_check lets the built one ship.
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


def _row(n, forecast, sealed_at, label="", version=None):
    return {"seal_id": _sig(n), "sealed_at": sealed_at, "label": label, "model_ref": "r-test",
            "context_ref": CTX, "state": "AAAA", "forecast": json.dumps(forecast),
            "version": int(RE._format()) if version is None else version}


def _setup():
    result = T._result()
    schema = T._schema(result)
    base = T._self_forecast(result, schema)
    wards = schema["x-ward-ids"]
    parties = schema["x-seat-context"]["parties"]
    by_size = sorted(base["list_votes"], key=lambda p: -base["list_votes"][p])
    pool = T._pool_total(base)

    def moved(frm, to, frac):
        """``frac`` of the pooled votes moved on the list ballot."""
        f = copy.deepcopy(base)
        n = int(pool * frac)
        f["list_votes"][by_size[frm]] -= n
        f["list_votes"][by_size[to]] += n
        return f

    # ward 0 called for another party, with the seats still right: worse on
    # wards only
    ward_miss = None
    for p in parties:
        if p == result["wards"][wards[0]] or not (base["list_votes"].get(p, 0) > 0
                                                  and base["ward_votes"].get(p, 0) > 0):
            continue
        f = copy.deepcopy(base)
        f["ward_calls"][0] = p
        if S.score(f, schema, result)["seat_error"] == 0:
            ward_miss = f
            break
    assert ward_miss is not None, "no ward miss keeps the seats right"
    # vote moved from the third party to the second: worse on the vote only,
    # by more than the page's rounding
    vote_miss = moved(2, 1, 1e-3)
    # vote moved from the second party to the first: a seat off, every ward right
    seat_miss = moved(1, 0, 1e-3)
    rows = [
        _row(1, base, 1_000, "Late perfect"),       # ties 2 and 3, sealed last of them
        _row(2, base, 500, ""),                     # ties, earliest second, the higher seal id
        _row(3, base, 500, "Same second"),          # ties, earliest second, ... see ids
        _row(4, ward_miss, 100, "Ward miss"),
        _row(5, vote_miss, 200, "Vote miss"),
        _row(6, seat_miss, 50, "Seat miss"),
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
        keyed.append(((s["seat_error"], -s["wards_called"], round(s["list_vote_error"], RE.VOTE_DP)),
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
    assert by["Ward miss"]["wards_called"] == board["wards"] - 1 and by["Ward miss"]["seat_error"] == 0
    assert by["Vote miss"]["list_vote_error"] > by["Late perfect"]["list_vote_error"]
    assert (by["Vote miss"]["seat_error"], by["Vote miss"]["wards_called"]) == (0, board["wards"])
    assert board["entries"] == len(rows)
    assert first[0]["sealed_at"] == "1970-01-01T00:08:20Z"
    assert set(first[0]) == {"place", "id", "name", "seat_error", "wards_called", "list_vote_error", "sealed_at"}
    assert (board["id_chars"], board["vote_dp"]) == (RE.ID_CHARS, RE.VOTE_DP)
    # the vote error is printed and ranked at the same precision
    assert all(r["list_vote_error"] == round(r["list_vote_error"], RE.VOTE_DP) for r in first)


def test_seats_decide_before_wards():
    """Seat error first: an entry a seat off with every ward right places
    below one right on seats with a ward missed, though it was sealed earlier."""
    _result, _schema, rows = _setup()
    by = {r["name"]: r for r in _board()["rows"]}
    seat, ward = by["Seat miss"], by["Ward miss"]
    assert seat["seat_error"] > 0 and seat["wards_called"] == _board()["wards"]
    assert (ward["seat_error"], ward["wards_called"]) == (0, _board()["wards"] - 1)
    assert seat["place"] > ward["place"] and seat["sealed_at"] < ward["sealed_at"]
    # constructed violation: the first two keys swapped
    real = S.rank_key
    try:
        S.rank_key = lambda sc: (-sc["wards_called"], sc["seat_error"], sc["list_vote_error"])
        swapped = {r["name"]: r for r in _board()["rows"]}
        assert swapped["Seat miss"]["place"] < swapped["Ward miss"]["place"]
    finally:
        S.rank_key = real


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


def test_the_board_ranks_on_the_vote_error_it_prints():
    """An entry off on the vote by less than the page prints ties with the
    perfect entries and, sealed first, places first; ranked on the unrounded
    value it would place after them while the page showed the same figures."""
    result, schema, rows = _setup()
    sliver = json.loads(rows[0]["forecast"])
    big = sorted(sliver["list_votes"], key=lambda p: -sliver["list_votes"][p])[:2]
    eps = max(1, int(sum(sliver["list_votes"].values()) * 1e-5))     # list votes, a sliver
    sliver["list_votes"][big[0]] -= eps
    sliver["list_votes"][big[1]] += eps
    raw = S.score(sliver, schema, result)["list_vote_error"]
    perfect = S.score(json.loads(rows[0]["forecast"]), schema, result)["list_vote_error"]
    assert raw != perfect and round(raw, RE.VOTE_DP) == round(perfect, RE.VOTE_DP)
    board = _board(rows + [_row(9, sliver, 10, "Sliver")])
    assert board["rows"][0]["name"] == "Sliver"
    real = RE.VOTE_DP
    try:
        RE.VOTE_DP = 15
        assert _board(rows + [_row(9, sliver, 10, "Sliver")])["rows"][0]["name"] != "Sliver"
    finally:
        RE.VOTE_DP = real


# ----------------------------------------------------------------- after publication

def test_an_entry_is_dropped_or_every_name_anonymised_on_the_board():
    board = _board()
    gone = board["rows"][1]
    dropped = RE.edit_board(board, drop=[_sig(3)])          # a whole seal id
    assert gone["id"] == _sig(3)[:RE.ID_CHARS]
    assert [r["id"] for r in dropped["rows"]] == [r["id"] for r in board["rows"] if r["id"] != gone["id"]]
    assert [r["place"] for r in dropped["rows"]] == list(range(1, len(board["rows"])))
    assert dropped["entries"] == board["entries"] - 1
    assert board["rows"][1] is gone and gone["place"] == 2, "the board passed in was changed"
    anon = RE.edit_board(board, anonymise=True)
    assert all(r["name"] == "Anonymous #" + r["id"][:RE.ANON_CHARS] for r in anon["rows"])
    assert not {r["name"] for r in anon["rows"]} & {"Late perfect", "Same second", "Ward miss"}
    try:
        RE.edit_board(board, drop=["not-a-seal-on-the-board"])
        raise AssertionError("an unknown seal id was accepted")
    except ValueError:
        pass
    # through the command line, on a board file, with no export
    with tempfile.TemporaryDirectory() as t:
        f = Path(t, "leaderboard.json")
        f.write_text(json.dumps(board))
        assert RE.main(["--out", str(f), "--drop", _sig(1)[:RE.ID_CHARS], "--anonymise"]) == 0
        got = json.loads(f.read_text())
        assert got["entries"] == board["entries"] - 1
        assert _sig(1)[:RE.ID_CHARS] not in {r["id"] for r in got["rows"]}
        assert all(r["name"].startswith("Anonymous #") for r in got["rows"])


def test_the_board_is_kept_out_of_git():
    for path in ("content/joburg/leaderboard.json", "site/leaderboard/leaderboard.json"):
        p = subprocess.run(["git", "-C", str(ROOT), "check-ignore", "-q", path])
        assert p.returncode == 0, f"{path} is not gitignored"
    import deploy_check
    assert deploy_check.SHIPPED_UNCOMMITTED == {f"{LB.LB_DIR}/leaderboard.json"}
    # the built board ships uncommitted; anything else beside it does not
    with tempfile.TemporaryDirectory() as t:
        repo = Path(t)
        site = repo / "site"
        (site / LB.LB_DIR / "js").mkdir(parents=True)
        (site / "index.html").write_text("<p>page</p>")
        git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)
        git("init", "-q")
        git("add", "-A")
        git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "site")
        (site / LB.LB_DIR / "leaderboard.json").write_text("{}")
        assert deploy_check.untracked(site, root=repo) == []
        (site / LB.LB_DIR / "js" / "leaderboard.js").write_text("x")
        (site / "leaderboard.json").write_text("{}")
        assert deploy_check.untracked(site, root=repo) == ["leaderboard.json", f"{LB.LB_DIR}/js/leaderboard.js"]


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


def test_a_row_of_another_version_is_refused_by_name():
    """Guard G12. A row stored under another entry version (version 1 held one
    combined share) stops the ranking, naming its seal id, before anything is
    scored; every row of the version the schema reads ranks."""
    result, schema, rows = _setup()
    assert _board(rows)["entries"] == len(rows)
    old = copy.deepcopy(rows)
    old[4]["version"] = 1
    try:
        _board(old)
        raise AssertionError("a row of another version was ranked")
    except ValueError as e:
        assert _sig(5) in str(e) and "version" in str(e)
        assert _sig(1) not in str(e)
    old[4]["version"] = int(RE._format())
    assert _board(old)["entries"] == len(rows)


class _D1:
    """A stand-in for ``npx wrangler d1 execute --json``: answers COUNT(*) from
    a count it holds and records every command; a DELETE empties it."""

    def __init__(self, n):
        self.n, self.commands = n, []

    def __call__(self, cmd, **kw):
        sql = cmd[cmd.index("--command") + 1]
        self.commands.append(sql)
        if sql.startswith("DELETE"):
            self.n = 0
        body = [{"results": [{"n": self.n}] if "COUNT" in sql else [], "success": True}]
        return type("Done", (), {"returncode": 0, "stdout": json.dumps(body), "stderr": ""})()


def test_clearing_a_version_prints_the_count_first_and_needs_it_confirmed():
    """The release step for the old test entries (owner, 2026-10-08): counted
    and printed, nothing deleted without --confirm; a confirm that is not the
    count now deletes nothing; the version the scorer reads is never cleared."""
    import contextlib
    import io
    d1 = _D1(7)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        assert RE.clear_version(1, run=d1) == 0
    assert "7 entries of version 1" in out.getvalue()
    assert not any(c.startswith("DELETE") for c in d1.commands)
    try:
        RE.clear_version(1, 6, run=d1)
        raise AssertionError("a stale count deleted")
    except SystemExit as e:
        assert "not the count now" in str(e)
    assert not any(c.startswith("DELETE") for c in d1.commands)
    with contextlib.redirect_stdout(io.StringIO()):
        assert RE.clear_version(1, 7, run=d1) == 7
    assert [c for c in d1.commands if c.startswith("DELETE")] == ["DELETE FROM entries WHERE version = 1"]
    try:
        RE.clear_version(int(RE._format()), 0, run=_D1(0))
        raise AssertionError("the version the scorer reads was cleared")
    except SystemExit as e:
        assert "the scorer reads" in str(e)
    assert RE.entries_database() == "joburg-entries"


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
        f"published = {'true' if published else 'false'}\n")
    if with_board:
        (t / "joburg" / "leaderboard.json").write_text(json.dumps(_board()))
    return t


def test_the_leaderboard_is_hidden_until_the_flag_is_set():
    # the real flag: off, so no page and no nav entry
    assert LB.settings("joburg") == {"published": False}
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
        assert "top" not in data and len(data["rows"]) == data["entries"] == len(_setup()[2])
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
const s = "lz3k2a." + "%s", n = %d;
process.stdout.write(JSON.stringify([
  idOf("https://joburg.whysoserious.city/your-forecast/?v=1&c=x&f=AA&n=T&s=" + s, n),
  idOf(s, n), idOf("%s", n), idOf("nonsense", n), idOf("https://x.test/?f=1", n)]));
""" % ((ROOT / "interactive/js/leaderboard.js").as_uri(), _sig(7), RE.ID_CHARS, _sig(7))
    with tempfile.TemporaryDirectory() as t:
        f = Path(t, "id.mjs")
        # the module touches the DOM at load: give it a stand-in
        f.write_text("globalThis.document = { querySelector: () => ({ addEventListener() {} }) };\n"
                     "globalThis.location = { search: '' };\n"
                     "globalThis.fetch = () => new Promise(() => {});\n" + script)
        p = subprocess.run(["node", str(f)], capture_output=True, text=True, timeout=30)
    assert p.returncode == 0, p.stderr
    want = _sig(7)[:RE.ID_CHARS]
    assert json.loads(p.stdout) == [want, want, want, "", ""]


if __name__ == "__main__":
    sys.exit(run_module(sys.modules[__name__]))
