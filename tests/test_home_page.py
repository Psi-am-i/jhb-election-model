"""`render_home.py` — the home page's four regions, and what may be typed in them.

The page shipped on 2026-09-24 with no test of its own. `test_published_page`
already regenerates it (its `GENERATORS`) and checks the *tokens* it prints
against the model, and `index.html` is in `build_site.ARTEFACTS`, so the build's
typed-figure audit already reaches the built page. What had nothing was
`render_home` itself: the regions, the lede whose wording is chosen by the
numbers, the "everyone else" row, and the exactly-one-lead refusal.

**Every input here is CONSTRUCTED except three**, and each says so where it is:
`test_regenerating_clears_exactly_the_regions_render_home_owns` and
`test_the_typed_figure_gate_reaches_the_home_page` both regenerate the real
`home.html` (there is no other way to ask "which regions does the generator
own?" or "would the build refuse this page?"), and
`test_the_shipped_article_list_carries_exactly_one_lead` reads
`content/joburg/articles.toml` on purpose — a second lead in the shipped file is
the defect the refusal exists for. Only the gate test injects a fault, catches
it, reverts it byte-exact and shows the detector go quiet again. The sentinel test's
discriminating half is the cleared/survived split — it names which regions the
generator owns and fails on an unexplained survivor — and its can-see proof is
the constructed `region()` test above it. The shipped-articles test's proof is
the constructed test above IT, where 0 leads and 2 leads are shown to refuse.

⛔ `render_home.main` is NOT called in-process. It calls `cityconfig.use`, which
sets global city state, and the suite imports modules into one interpreter. The
page-level checks run it as a subprocess on a scratch copy, which is how
`build_all` runs it too.
"""
from __future__ import annotations

import csv
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))

import hex_cartogram as HC  # noqa: E402
import render_home as RH  # noqa: E402
import render_map as RM  # noqa: E402
import scenarios as SC  # noqa: E402
import stats as statlib  # noqa: E402

PAGE = ROOT / "home.html"
PROCESSED = ROOT / "data" / "processed"
PY = ROOT / ".venv" / "bin" / "python"


# --------------------------------------------------------------------------
# helpers — the marker population, read from the page, never typed here
# --------------------------------------------------------------------------
def _region_names(text: str) -> set[str]:
    """Every marked region the page declares, by name."""
    import re
    return set(re.findall(r"<!-- __([A-Z0-9]+)_START__ -->", text))


def _body(text: str, name: str) -> str:
    start, end = f"<!-- __{name}_START__ -->", f"<!-- __{name}_END__ -->"
    return text[text.index(start) + len(start):text.index(end)]


def _marker_name(mark_start: str) -> str:
    """`<!-- __MAP_START__ -->` -> `MAP`, taken from the module's own constant."""
    return mark_start.split("__")[1].removesuffix("_START")


def _seat_draws(tmp: Path, rows: list[dict], *, council: int, threshold: int,
                columns: list[str]) -> Path:
    """A constructed `seat_draws.csv`.

    ⛔ THE PARTY COLUMNS DELIBERATELY DO NOT SUM TO THE COUNCIL. That is the
    real file's shape — it keeps only the largest parties — and it is the shape
    in which summing the small columns silently loses seats, which is the bug
    `scenarios.others_per_draw` was written to end.
    """
    path = tmp / "seat_draws.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, ["draw", "council_size", "threshold"] + columns)
        w.writeheader()
        for i, row in enumerate(rows):
            w.writerow({"draw": i, "council_size": council,
                        "threshold": threshold, **row})
    return path


def _tok(name, value, fmt, source=None):
    return f"[{name}={value}]"


def _chance(name, value, source=None):
    return f"[{name}={float(value):.4f}]"


# --------------------------------------------------------------------------
# 1 — the regions
# --------------------------------------------------------------------------
def test_a_region_is_replaced_and_a_missing_marker_refuses():
    """`region` overwrites between the markers and touches nothing outside.

    Both directions on constructed text: the stale body goes, the new body
    arrives, and the prose either side is byte-identical. Then the same call
    with the markers removed must REFUSE — an append or a silent no-op would
    leave the last run's numbers on the page, which is the failure the markers
    exist to prevent.
    """
    page = ("<p>before</p>\n<!-- __HOMELEDE_START__ -->\nstale 41 seats\n"
            "<!-- __HOMELEDE_END__ -->\n<p>after</p>")
    out = RH.region(page, "HOMELEDE", "  <h1>fresh</h1>")

    assert "stale 41 seats" not in out, "the previous run's body survived"
    assert "fresh" in _body(out, "HOMELEDE")
    assert out.startswith("<p>before</p>") and out.endswith("<p>after</p>"), out

    # and the detector goes quiet the moment the markers are gone: it refuses
    for broken in (page.replace("<!-- __HOMELEDE_START__ -->", ""),
                   page.replace("<!-- __HOMELEDE_END__ -->", "")):
        try:
            RH.region(broken, "HOMELEDE", "x")
        except SystemExit as exc:
            assert "HOMELEDE" in str(exc), exc
        else:
            raise AssertionError("a page with no markers was filled anyway")


def test_regenerating_clears_exactly_the_regions_render_home_owns():
    """Run the real generator over a sentinel and see which regions move.

    ⛔ THE POPULATION IS THE PAGE'S, NOT A LIST IN THIS FILE. Every marked
    region in `home.html` is filled with a sentinel; after the run, the ones
    that lost it are the ones `render_home` owns and the ones that kept it must
    be exactly the map regions, named by `render_map` and `hex_cartogram`'s own
    constants. A region in the page that NOBODY fills would show up here as an
    unexplained survivor — that is the direction a hand-kept list misses.
    """
    page = PAGE.read_text(encoding="utf-8")
    names = _region_names(page)
    assert len(names) >= 4, f"home.html declares only {sorted(names)}"

    sentinel = "SENTINEL-DO-NOT-KEEP"
    scratch_text = page
    for name in sorted(names):
        start, end = f"<!-- __{name}_START__ -->", f"<!-- __{name}_END__ -->"
        i, j = scratch_text.index(start) + len(start), scratch_text.index(end)
        scratch_text = scratch_text[:i] + f"\n{sentinel}\n" + scratch_text[j:]

    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "home.html"
        copy.write_text(scratch_text, encoding="utf-8")
        r = subprocess.run([str(PY), str(ROOT / "src" / "render_home.py"),
                            "--page", str(copy)],
                           capture_output=True, text=True, cwd=ROOT)
        assert r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]
        filled = copy.read_text(encoding="utf-8")

    kept = {n for n in names if sentinel in _body(filled, n)}
    cleared = names - kept
    # The map generators' regions, where the page carries them. Since
    # 2026-10-10 it carries neither: its map is cut from /forecast's at build
    # time (`render_home.home_map`, the HOMEMAP marker), so every region the
    # page declares is render_home's own.
    map_regions = {_marker_name(RM.MARK_START), _marker_name(HC.MARK_START)} & names

    assert kept == map_regions, (
        f"render_home left {sorted(kept)} untouched; the regions it does not "
        f"own are the map's {sorted(map_regions)}. An extra survivor is a "
        f"region of `home.html` that no generator fills — stale forever.")
    assert cleared and all(_body(filled, n).strip() for n in cleared), (
        f"a region was cleared and left empty: "
        f"{[n for n in cleared if not _body(filled, n).strip()]}")


# --------------------------------------------------------------------------
# 2 — the article list
# --------------------------------------------------------------------------
def _articles_toml(entries: list[str]) -> str:
    return "\n".join(entries)


_ITEM = """
[[article]]
{lead}date = "{date}"
title = "{title}"
standfirst = "A sentence."
href = "{href}"
"""


def _item(date: str, title: str, href: str, lead: bool = False) -> str:
    return _ITEM.format(lead="lead = true\n" if lead else "",
                        date=date, title=title, href=href)


def test_the_home_page_runs_exactly_one_lead_and_refuses_any_other_count():
    """Constructed article lists: 0 and 2 leads refuse, 1 works and goes first.

    The lead flag is the whole mechanism for retiring a stale front-page piece
    (PUBLISHING-BACKLOG §10), so a file with none and a file with two are both
    faults — and a silent pick of the first would reinstate the thing the home
    page was built to end.
    """
    one = [_item("2026-08-31", "The lead", "lead", lead=True),
           _item("2026-09-01", "A later piece", "later")]
    none = [_item("2026-08-31", "The lead", "lead"),
            _item("2026-09-01", "A later piece", "later")]
    two = [_item("2026-08-31", "The lead", "lead", lead=True),
           _item("2026-09-01", "A later piece", "later", lead=True)]

    with tempfile.TemporaryDirectory() as tmp:
        city = Path(tmp)
        for entries, leads in ((none, 0), (two, 2)):
            (city / "articles.toml").write_text(_articles_toml(entries),
                                                encoding="utf-8")
            try:
                RH._articles(city)
            except SystemExit as exc:
                assert f"marks {leads} articles" in str(exc), exc
            else:
                raise AssertionError(f"{leads} leads were accepted")

        # …and the detector goes quiet on exactly one, which is the live shape
        (city / "articles.toml").write_text(_articles_toml(one),
                                            encoding="utf-8")
        html = RH._articles(city)
        assert html.index("The lead") < html.index("A later piece"), (
            "the lead must run first even though it is the older piece")
        assert html.count("lead-item") == 1, html

        # a missing file refuses rather than rendering an empty feed
        (city / "articles.toml").unlink()
        try:
            RH._articles(city)
        except SystemExit as exc:
            assert "articles" in str(exc)
        else:
            raise AssertionError("a missing articles.toml rendered anyway")


def test_the_shipped_article_list_carries_exactly_one_lead():
    """OBSERVED, deliberately: the live file is the thing that can go wrong.

    The constructed test above proves the refusal works. This one proves it is
    satisfied by what is actually on disk, which no constructed input can say.
    """
    RH._articles(ROOT / "content" / "joburg")  # raises SystemExit if not


# --------------------------------------------------------------------------
# 3 — "everyone else"
# --------------------------------------------------------------------------
def test_everyone_else_is_counted_inside_each_simulation():
    """The council minus the named parties, per draw — not a sum of medians.

    Constructed so that the three wrong answers all differ from the right one:

    * council − named, per draw      → [3, 1, 5], median **3**  (correct)
    * summing the file's other column → [1, 1, 4], median 1     (the sheet's
      old bug: `seat_draws.csv` keeps only the largest parties, so the seats of
      everyone below them vanish)
    * the other column's median       → 1                       (§1.214's shape:
      a sum of per-party medians describes no simulation at all)

    ⚠️ The tail party is BOSA on purpose: it is outside `scenarios.NAMED_PARTIES`,
    so it stays in "everyone else" however that set changes. A fixture using a
    NAMED party has no tail at all, and the row under test is never rendered.
    """
    rows = [{"ANC": 4, "DA": 3, "BOSA": 1},
            {"ANC": 6, "DA": 3, "BOSA": 1},
            {"ANC": 3, "DA": 2, "BOSA": 4}]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        _seat_draws(tmp, rows, council=10, threshold=6,
                    columns=["ANC", "DA", "BOSA"])
        others = SC.others_per_draw(tmp, ("ANC", "DA"))
        assert list(others) == [3, 1, 5], list(others)

        med, lo, hi = SC.seat_quantiles(others)
        assert (med, lo, hi) == (3, 1, 5), (med, lo, hi)
        assert med != sum(r["BOSA"] for r in rows) / len(rows), (
            "the median matched an average of the columns the file keeps")
        assert med != sorted(r["BOSA"] for r in rows)[1], (
            "the median matched the small column's own median — the seats held "
            "by parties the file does not list have gone missing")

        # and the row render_home prints reads that quantity, not another one
        summary = {"parties": {
            "ANC": {"median": 4.0, "p5": 3.0, "p95": 6.0},
            "DA": {"median": 3.0, "p5": 2.0, "p95": 3.0},
            "BOSA": {"median": 1.0, "p5": 1.0, "p95": 4.0}}}
        html = RH._seats(summary, _tok, tmp)
        assert "[home.seats.others=3]" in html, html
        assert "[home.seats.others_lo=1]" in html and \
               "[home.seats.others_hi=5]" in html, html
        assert "within" in html, "the note that says per-simulation is gone"
        # ⛔ AND THE BAND BESIDE IT IS A TOKEN, NOT THE WORD "90". Both pages
        # typed it until 2026-09-25, which is a second copy of
        # `scenarios.BAND` sitting in prose — two of the ten `BLOCKS` rows
        # standing between the build and a `--publish`.
        assert "[home.band=" in html and "90%" not in html, html


def test_a_party_the_page_names_is_never_pooled_into_everyone_else():
    """Both directions on the same fixture: named out, unnamed in.

    The named set is `render_home.NAMED`, so a party added to that tuple must
    leave the "everyone else" row in the same change. Here DA moves from named
    to unnamed and the row moves by exactly DA's seats in every draw.
    """
    rows = [{"ANC": 4, "DA": 3, "BOSA": 1},
            {"ANC": 6, "DA": 3, "BOSA": 1},
            {"ANC": 3, "DA": 2, "BOSA": 4}]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        _seat_draws(tmp, rows, council=10, threshold=6,
                    columns=["ANC", "DA", "BOSA"])
        with_da = SC.others_per_draw(tmp, ("ANC", "DA"))
        without_da = SC.others_per_draw(tmp, ("ANC",))
        assert list(without_da - with_da) == [r["DA"] for r in rows], (
            list(without_da), list(with_da))


# --------------------------------------------------------------------------
# 4 — the lede
# --------------------------------------------------------------------------
def _lede_over(alone_of_100: int, anc: float, da: float) -> str:
    """The lede for a constructed run of 10,000 draws: `alone_of_100` in 100
    govern alone, the ANC ALONE has the most seats in `anc` of them, the DA
    alone in `da`, and the rest are ties. The lede reads who is largest from
    the seat draws (reweight.largest_party, side finding S1), so the shares
    are built into the draws, not into forecast_summary.json."""
    n = 10_000
    n_anc, n_da, n_alone = round(anc * n), round(da * n), alone_of_100 * n // 100
    assert n_alone <= n_anc and n_anc + n_da <= n, "the fixture cannot be built"
    rows = ([{"ANC": 6 if i < n_alone else 4, "DA": 3} for i in range(n_anc)]
            + [{"ANC": 3, "DA": 4} for _ in range(n_da)]
            + [{"ANC": 3, "DA": 3} for _ in range(n - n_anc - n_da)])
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        _seat_draws(tmp, rows, council=10, threshold=6, columns=["ANC", "DA"])
        alone, a, d, _n = RH.race_figures(tmp)
        coalition, race, first, second = RH.phrases(alone, a, d)
        return f"{coalition}. The largest party is {race}: {first}, then {second}."


def test_the_strength_of_the_coalition_claim_is_chosen_by_the_number():
    """Each band, ON its exclusive edge — 0, 1, 10 and 35 draws in 100.

    The wording is the largest type on the site. "All but inevitable" at a 35%
    chance would be a lie nobody would notice until a journalist did, so the
    adjective is a function of the measurement and this is the test of that
    function, not of today's forecast.
    """
    assert "all but inevitable" in _lede_over(0, 0.60, 0.30)
    assert "overwhelmingly likely" in _lede_over(1, 0.60, 0.30)
    assert "the likely outcome" in _lede_over(10, 0.60, 0.30)
    assert "one of two live outcomes" in _lede_over(35, 0.60, 0.30)


def test_a_lead_is_never_claimed_between_two_identical_printed_figures():
    """The second clause follows what the READER sees, not the raw gap.

    At four decimal places one party is always ahead; the question is whether
    the difference survives the formatter. The pair below is asserted to format
    identically FIRST — deriving it from `stats._fmt` rather than assuming a
    precision — and the lede must then say dead heat.
    """
    anc, da = 0.4723, 0.4728
    assert statlib._fmt(anc, "chance") == statlib._fmt(da, "chance"), (
        "the fixture no longer exercises the branch: these two now print "
        "differently")
    assert "dead heat" in _lede_over(0, anc, da)

    # a gap the formatter DOES show, still inside the "too close" band
    assert statlib._fmt(0.47, "chance") != statlib._fmt(0.44, "chance")
    close = _lede_over(0, 0.47, 0.44)
    assert "too close to call" in close and "dead heat" not in close, close

    # and a real lead names the leader
    clear = _lede_over(0, 0.60, 0.30)
    assert "leaning to the ANC" in clear and "too close" not in clear, clear
    assert "leaning to the DA" in _lede_over(0, 0.30, 0.60)


# --------------------------------------------------------------------------
# 5 — nothing on the page is a typed figure
# --------------------------------------------------------------------------
def test_the_typed_figure_gate_reaches_the_home_page():
    """The build's own audit, run over the regenerated home page.

    ⛔ THIS TESTS THE GATE, NOT TODAY'S PAGE. `build_site` already refuses a
    `--publish` for every number typed into prose that is neither a token nor a
    registered fixed fact, and lists each as `BLOCKS` in
    `content/joburg/NUMBERS-REVIEW.md`. A second assertion on the same state
    here would be a copy of that gate, and the two would disagree the first
    time one moved. What the build cannot check is whether the gate still
    *sees* — so that is what this does.

    The settings come from `build_site.audit_configs`, not from a copy: a
    retyped structural set answers a different question the moment the council
    changes size.

    ⚠️ The page IS regenerated, so the input is observed. The mutation below is
    what keeps that honest: a typed model figure is injected into the lede,
    caught, reverted byte-exact, and the detector shown to go quiet again.
    """
    import build_site  # imported late: it is heavy and only this test needs it

    if not (PROCESSED / "forecast_summary.json").exists():
        from _support import skip
        skip("needs data/processed/forecast_summary.json; run montecarlo.py")

    registry = statlib.load_registry(ROOT / "content" / "joburg" / "stats.toml")
    ctx = statlib.load_context(PROCESSED)
    audit_cfg, scan_cfg = build_site.audit_configs(registry, ctx)

    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "home.html"
        shutil.copy(PAGE, copy)
        r = subprocess.run([str(PY), str(ROOT / "src" / "render_home.py"),
                            "--page", str(copy)],
                           capture_output=True, text=True, cwd=ROOT)
        assert r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]
        raw = copy.read_text(encoding="utf-8")

    rendered, _, _ = statlib.render(raw, registry, ctx)

    # IT LOOKED: the scan's population is the page's number-shaped strings, and
    # it is bounded on BOTH sides — a floor alone ratchets, and a scan that has
    # drifted onto the wrong text reads as a clean page.
    population = statlib.scan_numbers(rendered, page="index.html", **scan_cfg)
    assert 20 <= len(population) <= 5000, (
        f"{len(population)} number-shaped strings on the home page — the scan "
        f"is looking at the wrong text, or the page has been gutted")
    # `scan_numbers` strips token spans before it looks, so a token is not IN
    # this population at all: what a non-`unreviewed` status marks is a
    # structural or fixed figure. Both are asserted, and separately —
    # they are different claims and the page needs each.
    cleared = [h for h in population if h["status"] != "unreviewed"]
    assert cleared, ("not one number on the page is structural or fixed "
                     "— the registry is not reaching this page")
    assert "{{@home." in raw, (
        "the regenerated page carries no home token at all, so the scan above "
        "is measuring a page the generator did not fill")

    # IT CAN SEE: one typed model figure, in prose, inside the lede region.
    fault = '<p class="sub">The ANC takes just 7 seats.</p>'
    i = rendered.index("<!-- __HOMELEDE_END__ -->")
    broken = rendered[:i] + fault + rendered[i:]
    caught, _ = statlib.audit(broken, page="index.html", **audit_cfg)
    before, _ = statlib.audit(rendered, page="index.html", **audit_cfg)
    assert any("'7'" in n for n in caught), (
        f"a typed seat count inside the lede was not caught: {caught}")
    assert len(caught) == len(before) + 1, (caught, before)

    # …AND GOES QUIET AGAIN when it is taken out.
    reverted = broken.replace(fault, "")
    assert reverted == rendered, "the mutation did not revert byte-exact"
    assert statlib.audit(reverted, page="index.html", **audit_cfg)[0] == before


def test_the_home_map_is_cut_from_the_forecast_map():
    """The home page's map (`render_home.home_map`) is /forecast's map without
    its switch, its equal-ward map or its long key, cut from the map region of
    a CONSTRUCTED sheet; and a sheet that has lost a piece it cuts by is
    refused, not cut wrongly."""
    sheet = ("<p>before</p>\n" + RM.MARK_START + """
  <details class="rollup"><summary>The map</summary>
    <div class="maptoggle"><button data-show="geo">Normal Map</button></div>
    <figure>
      <div class="mapbox">
      <svg id="wardmap" class="mapsvg"><path data-tip="Ward 1"></path></svg>
      <div id="maptip" class="maptip" hidden></div>
      </div>
      <figcaption class="mapcaption">
        <span><span class="mapkey-parties">ANC DA</span>
    <span class="mapkey-item"><b>Solid colour</b></span>
    <br><span class="mapkey-note">A stripe for every party</span></span>
      </figcaption>
    </figure>
  </details>
  """ + RM.MARK_END + "\n<p>after</p>")
    out = RH.home_map(sheet)
    for kept in ('id="wardmap"', 'id="maptip"', "mapkey-parties", "Solid colour"):
        assert kept in out, (kept, out)
    for dropped in ("maptoggle", "Normal Map", "mapkey-note", "<details", "before", "after"):
        assert dropped not in out, (dropped, out)
    # inside the map generator's own markers, so the scan lists its figures
    # as the generator's, exactly as on /forecast
    assert out.startswith(RM.MARK_START) and out.endswith(RM.MARK_END), out
    figured = out.replace("Solid colour", "Solid colour 9 of 10")
    regions = {h["region"] for h in statlib.scan_numbers(figured)}
    assert regions and all(r.startswith("generated:MAP") for r in regions), regions
    # IT CAN SEE: the same cut without the markers is prose, and blocks
    bare = figured.replace(RM.MARK_START, "").replace(RM.MARK_END, "")
    bare_regions = {h["region"] for h in statlib.scan_numbers(bare)}
    assert bare_regions and all(r.startswith("prose") for r in bare_regions), bare_regions
    # IT CAN SEE: a sheet whose map lost its box is refused
    try:
        RH.home_map(sheet.replace('<div class="mapbox">', '<div class="box">'))
    except SystemExit as exc:
        assert "mapbox" in str(exc), exc
    else:
        raise AssertionError("a map without its box was cut anyway")
    # the shipped page carries the marker once, and no map region of its own
    page = PAGE.read_text(encoding="utf-8")
    assert page.count(RH.HOME_MAP_MARKER) == 1, "home.html has no single map marker"
    assert RM.MARK_START not in page and HC.MARK_START not in page


def test_an_article_lists_the_others_but_not_itself():
    """`build_site.more_commentary` lists every OTHER article under an
    article, before the sheet's end marker, and leaves any other page alone.
    The article list is the shipped articles.toml (the only list there is);
    the page is constructed."""
    import build_site as BS
    articles = BS.article_meta("joburg")
    assert len(articles) >= 2, f"articles.toml lists {len(articles)}"
    page = "<div class=\"sheet\"><p>body</p>\n" + BS.SHEET_END
    for output, art in articles.items():
        out = BS.more_commentary(page, output, articles, city="joburg")
        listed = out[out.index("more-commentary"):out.index(BS.SHEET_END)]
        assert f'href="{art["href"]}"' not in listed, f"{output} lists itself"
        others = [a["href"] for o, a in articles.items() if o != output]
        assert all(f'href="{h}"' in listed for h in others), (output, others)
    assert BS.more_commentary(page, "forecast.html", articles, city="joburg") == page


if __name__ == "__main__":
    from _support import run_module
    raise SystemExit(run_module(sys.modules[__name__]))
