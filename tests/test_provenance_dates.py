"""The dates a reader is shown beside a figure, and the scope of a registered fact.

The owner's sweep of 2026-10-03, items 1 and 2:

* **"Unchanged since" named the last edition, not the first.** A figure printed
  unchanged in every edition since 8 August read "Unchanged since 30 September".
  The date is now the start of the value's unbroken run in the ledger
  (`publication.run_starts`).
* **A dated article printed live figures.** The 8 August standfirst sat inside
  `data-asof` and carried the live `{{n_draws}}`; three passages were dated 31
  August, a date the piece was never published on. A figure in a dated passage
  must be one that was true on that date (`publication.misdated_figures`).
* **`page` on a registered fact was ignored**, and an `[audit].allow` phrase
  cleared any "NN%" near it on any page. A fact now clears only on the pages it
  lists, and an allow phrase clears no number (`stats.for_page`).

Inputs are constructed unless a test says it reads the tree, and each detector
is shown to fire and to go quiet again.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import publication as P  # noqa: E402
import stats as S  # noqa: E402
from _support import run_module, skip  # noqa: E402

STATS = ROOT / "content" / "joburg" / "stats.toml"


def _row(token="t", display="44", published_at="2026-08-08T17:29:45+00:00",
         movement="none", value=44, superseded_at=None):
    return P.Row(token=token, value=value, display=display, fmt="int",
                 source="s", model_run_id="r1", run_at=None, as_of=None,
                 published_at=published_at, change_class=None, reason=None,
                 movement=movement, superseded_at=superseded_at)


# --- "since" is the first date of the current value's unbroken run -----------

def test_since_is_the_first_row_of_the_unbroken_run_not_the_last():
    rows = [
        # A: the same figure in three editions -> its first edition
        _row("a", "44", "2026-08-08T17:29:45+00:00", "new"),
        _row("a", "44", "2026-09-26T13:58:54+00:00"),
        _row("a", "44", "2026-09-30T04:21:21+00:00"),
        # B: moved in the second edition, then held -> the second edition
        _row("b", "74", "2026-08-08T17:29:45+00:00", "new", 74),
        _row("b", "61", "2026-09-26T13:58:54+00:00", "material", 61),
        _row("b", "61", "2026-09-30T04:21:21+00:00", "none", 61),
        # C: a raw move below the displayed precision continues the run
        _row("c", "47%", "2026-09-26T13:58:54+00:00", "new", 0.471),
        _row("c", "47%", "2026-09-30T04:21:21+00:00", "rounding", 0.468),
        # D: a value that returns after a different one starts a NEW run
        _row("d", "5", "2026-08-08T17:29:45+00:00", "new", 5),
        _row("d", "6", "2026-09-26T13:58:54+00:00", "material", 6),
        _row("d", "5", "2026-09-30T04:21:21+00:00", "material", 5),
    ]
    got = P.run_starts(reversed(rows))   # order of the input is not trusted
    assert got == {"a": "2026-08-08T17:29:45+00:00",
                   "b": "2026-09-26T13:58:54+00:00",
                   "c": "2026-09-26T13:58:54+00:00",
                   "d": "2026-09-30T04:21:21+00:00"}, got


def test_a_retirement_ends_the_run():
    rows = [_row("r", "9", "2026-08-08T00:00:00Z", "new", 9),
            _row("r", "9", "2026-09-01T00:00:00Z", "none", 9,
                 superseded_at="2026-09-01T00:00:00Z"),
            _row("r", "9", "2026-09-26T00:00:00Z", "new", 9)]
    assert P.run_starts(rows) == {"r": "2026-09-26T00:00:00Z"}


def test_the_change_record_carries_both_dates():
    """`changes.json` and every tooltip read `since` from `_ledger_candidates`,
    so it must be there, and be the run start, not the latest row."""
    import build_site as B
    ledger = [_row("same", "44", "2026-08-08T00:00:00Z", "new"),
              _row("same", "44", "2026-09-30T00:00:00Z"),
              _row("moved", "74", "2026-08-08T00:00:00Z", "new", 74),
              _row("moved", "74", "2026-09-30T00:00:00Z", "none", 74)]
    latest = {r.token: r for r in ledger}
    occ = [{"token": t, "value": v, "display": d, "fmt": "int", "source": "s",
            "mode": "free", "tolerance": None, "dated": False, "page": "x.html"}
           for t, v, d in (("same", 44, "44"), ("moved", 60, "60"), ("new", 1, "1"))]
    ident = {"model_run_id": "r-abc-1234", "run_at": None, "as_of": None}
    _, changes = B._ledger_candidates(occ, latest, ident, "2026-10-03T00:00:00Z",
                                      reason="r", change_class="mechanism",
                                      since=P.run_starts(ledger))
    by = {c["token"]: c for c in changes}
    assert by["same"]["since"] == "2026-08-08T00:00:00Z", by["same"]
    assert by["same"]["previous_published_at"] == "2026-09-30T00:00:00Z"
    assert by["moved"]["since"] is None, "a moved value has no run yet"
    assert by["moved"]["previous_since"] == "2026-08-08T00:00:00Z", by["moved"]
    assert by["new"]["since"] is None and by["new"]["previous_since"] is None


def test_the_built_tooltip_dates_an_unchanged_figure_to_its_first_edition():
    """End to end: the tooltip text is assembled inside `build_site.main`, which
    no unit test reaches. A throwaway ledger holds one token in three editions;
    the page must say the first."""
    if not (ROOT / "data" / "processed" / "forecast_summary.json").exists():
        skip("needs data/processed/forecast_summary.json; run montecarlo.py")
    token = "asa_2021_seats"     # a fixed, unchanging IEC figure on /forecast
    reg = tomllib.loads(STATS.read_text(encoding="utf-8"))
    assert reg[token]["mode"] == "fixed", reg[token]
    shown = S._fmt(reg[token]["value"], reg[token].get("format"))
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        led = tmp / "led" / "joburg"
        led.mkdir(parents=True)
        import json
        led.joinpath("ledger.jsonl").write_text("".join(
            json.dumps(_row(token, shown, when, mv, reg[token]["value"]).as_json()) + "\n"
            for when, mv in (("2026-08-08T17:29:45+00:00", "new"),
                             ("2026-09-26T13:58:54+00:00", "none"),
                             ("2026-09-30T04:21:21+00:00", "none"))), encoding="utf-8")
        r = subprocess.run(
            [str(ROOT / ".venv/bin/python"), str(ROOT / "src/build_site.py"),
             "--out", str(tmp / "site"), "--ledger-root", str(tmp / "led"),
             "--allow-orphans", "--allow-stale-sources"],
            capture_output=True, text=True, cwd=ROOT)
        assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]
        page = (tmp / "site" / "forecast.html").read_text(encoding="utf-8")
    import html
    import re
    tips = [html.unescape(m) for m in re.findall(
        rf'data-token="{token}"[^>]*data-prov="([^"]*)"', page)]
    assert tips, f"{token} is not on /forecast; the test is looking at nothing"
    for tip in tips:
        assert tip.startswith(f"{shown}. Unchanged since 8 August 2026."), tip
        assert "30 September" not in tip, tip


# --- a figure in a dated passage is the figure of that date ------------------

def _occ(token, mode, captured, asof, display="61"):
    return {"token": token, "mode": mode, "captured": captured, "asof": asof,
            "dated": bool(asof), "display": display, "page": "a.html"}


def test_a_dated_passage_accepts_only_figures_of_its_date():
    good = [_occ("pub", "fixed", "2026-08-08", "2026-08-08"),
            _occ("older", "fixed", "2026-08-06", "2026-08-08"),
            _occ("council_size", "free", "", "2026-08-08", display="270"),
            _occ("live_undated", "free", "", "")]
    assert P.misdated_figures(good, structural={"270"}) == []
    bad = [_occ("live", "free", "", "2026-08-08"),
           _occ("generated", "generated", "", "2026-08-08"),
           _occ("pinned_later", "fixed", "2026-09-01", "2026-08-08"),
           _occ("pinned_undated", "fixed", "", "2026-08-08")]
    caught = P.misdated_figures(good + bad, structural={"270"})
    assert sorted(v["token"] for v in caught) == sorted(o["token"] for o in bad), caught
    # and quiet again once the bad occurrences are taken out
    assert P.misdated_figures(good, structural={"270"}) == []
    # a structural constant is exempt only as a constant of THIS council
    assert P.misdated_figures([_occ("c", "free", "", "2026-08-08", "270")]), (
        "a free figure was exempted without the council's constants passed in")


def test_every_dated_figure_in_the_lead_article_is_of_the_article_date():
    """Reads the tree: the 8 August piece, rendered as the build renders it.
    Every token inside one of its dated passages is dated to the piece's own
    `date` in articles.toml, and passes `misdated_figures`."""
    import build_site as B
    import cityconfig
    cityconfig.use(None)
    processed = cityconfig.use_target(None).processed
    if not (processed / "forecast_summary.json").exists():
        skip("needs data/processed/forecast_summary.json; run montecarlo.py")
    arts = tomllib.loads((ROOT / "content/joburg/articles.toml").read_text())["article"]
    lead = next(a for a in arts if a.get("lead"))
    page = lead["href"].split("#")[0] + ".html"
    source, cut, _ = B.ARTEFACTS[page]
    html = B.cut_spans((ROOT / source).read_text(encoding="utf-8"), cut)
    registry = S.load_registry(STATS)
    ctx = S.load_context(processed)
    rec: list = []
    S.render(html, registry, ctx, record=rec)
    dated = [r for r in rec if r.get("token") and r.get("dated")]
    # it looked: the standfirst and the two commentary passages, no more
    assert 3 <= len(dated) <= 20, [r["token"] for r in dated]
    assert {r["asof"] for r in dated} == {lead["date"]}, sorted(
        {(r["token"], r["asof"]) for r in dated})
    structural = B.audit_configs(registry, ctx)[0]["structural"]
    assert P.misdated_figures(dated, structural) == []


# --- a registered fact clears only on its own page; an allow phrase, nowhere ---

def test_a_fixed_fact_clears_only_on_the_pages_it_lists():
    html = "<p>The DA won three wards on just 23% of the vote.</p>"
    fact = {"value": "23%", "context": "on just 23% of the vote", "page": "a.html, b.html"}

    def status(**kw):
        return [h["status"] for h in S.scan_numbers(html, fixed=[fact], **kw)
                if h["value"] == "23%"]
    assert status(page="a.html") == ["fixed"]
    assert status(page="b.html") == ["fixed"]
    assert status(page="c.html") == ["unreviewed"], "cleared on a page it does not list"
    assert status() == ["unreviewed"], "a caller naming no page got a scoped fact"
    assert [h["status"] for h in S.scan_numbers(
        html, page="c.html", fixed=[{**fact, "page": "*"}]) if h["value"] == "23%"] == ["fixed"]


def test_an_allow_phrase_clears_no_number_and_excuses_a_claim_only_on_its_page():
    html = "<p>In Laingsburg the DA won 23% and nobody will win Johannesburg.</p>"
    allow = [{"phrase": "laingsburg", "page": "a.html"},
             {"phrase": "nobody will win johannesburg", "page": "a.html"}]
    numbers, claims = S.audit(html, page="a.html", allow=allow)
    assert any("'23%'" in n for n in numbers), "an allow phrase cleared a number"
    assert claims == [], claims
    numbers, claims = S.audit(html, page="b.html", allow=allow)
    assert claims, "an allow phrase excused a claim on a page it does not list"


def test_the_registry_refuses_an_entry_without_a_page():
    ok = {"audit": {"fixed": [{"value": "1", "context": "x 1", "page": "a.html"}],
                    "allow": [{"phrase": "x", "page": "a.html"}]}}
    S.load_audit_config(ok)
    for bad in ({"audit": {"fixed": [{"value": "1", "context": "x 1"}]}},
                {"audit": {"allow": [{"phrase": "x"}]}},
                {"audit": {"allow": ["x"]}}):
        try:
            S.load_audit_config(bad)
        except ValueError:
            continue
        raise AssertionError(f"accepted an entry with no page: {bad}")


def test_every_registered_page_is_a_page_the_build_writes():
    """Reads the tree, both directions of the registry's page names: every page
    an entry names is one the build writes, and the entries cover more than
    one page (a registry scoped to nothing would pass the check above)."""
    import build_play
    import build_make
    import build_site as B
    built = ({spec[0] for spec in B.DOCS.values()} | set(B.ARTEFACTS)
             | {build_play.PLAY_PAGE, build_make.MAKE_PAGE, "portal.html"})
    cfg = S.load_audit_config(S.load_registry(STATS))
    named = set()
    for e in cfg["fixed"] + cfg["allow"]:
        for p in str(e["page"]).split(","):
            p = p.strip()
            if p != S.ALL_PAGES:
                named.add(p)
                assert p in built, f"{e} names {p!r}, which the build does not write"
    assert 4 <= len(named) <= len(built), sorted(named)


def test_every_registered_entry_clears_something_on_every_page_it_names():
    """Reads the tree, the other direction: a page the build writes is cleared
    by the entries (the build's own refusal), and every entry clears at least
    one occurrence on EACH page it names. An entry that clears nothing there is
    a stale scope — the state eleven entries were in, naming index.html for an
    article that had moved — or a dead entry for prose that is gone."""
    if not (ROOT / "data" / "processed" / "forecast_summary.json").exists():
        skip("needs data/processed/forecast_summary.json; run montecarlo.py")
    import build_site as B
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "led" / "joburg").mkdir(parents=True)
        r = subprocess.run(
            [str(ROOT / ".venv/bin/python"), str(ROOT / "src/build_site.py"),
             "--out", str(tmp / "site"), "--ledger-root", str(tmp / "led"),
             "--allow-orphans", "--allow-stale-sources"],
            capture_output=True, text=True, cwd=ROOT)
        assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]
        texts = {str(f.relative_to(tmp / "site")): f.read_text(encoding="utf-8")
                 for f in (tmp / "site").rglob("*.html")}
    import cityconfig
    cityconfig.use(None)
    registry = S.load_registry(STATS)
    ctx = S.load_context(cityconfig.use_target(None).processed)
    audit_cfg, scan_cfg = B.audit_configs(registry, ctx)
    generated = {"about.html", "portal.html"}
    stale = []
    for f in audit_cfg["fixed"]:
        listed = [x.strip() for x in str(f["page"]).split(",")]
        for page in (sorted(texts) if S.ALL_PAGES in listed else listed):
            hits = S.scan_numbers(texts.get(page, ""), page=page, fixed=[f],
                                  structural=scan_cfg["structural"],
                                  generated_page=page in generated)
            if not any(h["status"] == "fixed" for h in hits):
                stale.append(f"fixed {f['value']!r} ({f['context'][:40]}…) on {page}")
    for a in audit_cfg["allow"]:
        for page in (x.strip() for x in str(a["page"]).split(",")):
            kw = dict(page=page, fixed=audit_cfg["fixed"],
                      structural=audit_cfg["structural"])
            if not len(S.audit(texts.get(page, ""), allow=[a], **kw)[1]) < len(
                    S.audit(texts.get(page, ""), allow=[], **kw)[1]):
                stale.append(f"allow {a['phrase']!r} on {page}")
    assert len(audit_cfg["fixed"]) >= 10 and audit_cfg["allow"], audit_cfg.keys()
    assert not stale, "entries that clear nothing where they say they do:\n  " + "\n  ".join(stale)


if __name__ == "__main__":
    raise SystemExit(run_module(sys.modules[__name__]))
