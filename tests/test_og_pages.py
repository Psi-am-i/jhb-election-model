"""The share images (src/og_pages.py, src/og-pages.mjs): OG-IMPLEMENTATION-SPEC.md
§6, items 1-6, and the stamps' id prefixing (share-card.js ``stampSVG``).

Each scan-shaped test states its population and asserts it equals what was
scanned, bounds it on both sides, and shows its detector catches a constructed
violation and goes quiet when it is reverted (CLAUDE.md §4).

Items 1 and 2 build the site once into a temporary directory (a subprocess, on
a throwaway ledger), as tests/test_provenance_dates.py does. They need node
and ``npm ci`` in worker-api/, as the build does.
"""
from __future__ import annotations

import html as htmllib
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, run_module, skip  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))
import og_pages  # noqa: E402

PY = ROOT / ".venv" / "bin" / "python"
SITE_URL = "https://joburg.whysoserious.city"

# ---------------------------------------------------------------------------
# helpers


def _node(script: str, payload) -> str:
    run = subprocess.run(["node", "--input-type=module", "-e", script], input=json.dumps(payload),
                         capture_output=True, text=True, cwd=ROOT)
    assert run.returncode == 0, run.stderr[-2000:]
    return run.stdout


_NAMES = ("import { cardSVG, imageName } from " + json.dumps((ROOT / "src" / "og-pages.mjs").as_uri()) + ";\n"
          "let s = ''; process.stdin.on('data', d => s += d).on('end', () => {\n"
          "  process.stdout.write(JSON.stringify(JSON.parse(s).map(x => imageName(cardSVG(x)))));\n"
          "});\n")


def image_names(specs: list[dict]) -> list[str]:
    """The name og-pages.mjs gives each spec's image, regenerated."""
    return json.loads(_node(_NAMES, specs))


def png_size(path: Path) -> tuple[int, int]:
    head = path.read_bytes()[:24]
    assert head[:8] == b"\x89PNG\r\n\x1a\n", f"{path.name} is not a PNG"
    return struct.unpack(">II", head[16:24])


_BUILT: dict = {}


def built() -> Path:
    """One build into a temporary --out, shared by the tests that need it."""
    if "out" in _BUILT:
        return _BUILT["out"]
    if not (ROOT / "data" / "processed" / "forecast_summary.json").exists():
        skip("needs data/processed/forecast_summary.json")
    if not (ROOT / "worker-api" / "node_modules" / "@resvg" / "resvg-wasm").is_dir():
        skip("needs `npm ci` in worker-api/ (resvg-wasm)")
    tmp = Path(tempfile.mkdtemp(prefix="og-pages-"))
    (tmp / "led" / "joburg").mkdir(parents=True)
    (tmp / "led" / "joburg" / "ledger.jsonl").write_text("", encoding="utf-8")
    r = subprocess.run([str(PY), str(ROOT / "src" / "build_site.py"), "--out", str(tmp / "site"),
                        "--ledger-root", str(tmp / "led"), "--allow-orphans", "--allow-stale-sources"],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
    import atexit
    atexit.register(shutil.rmtree, tmp, ignore_errors=True)
    _BUILT["out"] = tmp / "site"
    return _BUILT["out"]


def expected_pages() -> dict[str, str | None]:
    """Every page build_site writes, from its own tables, and the slug of its
    share image (None: it keeps og.png)."""
    import build_leaderboard as lb
    import build_site
    import build_your_forecast as yf
    import cityconfig
    arts = build_site.article_meta()
    pages = [spec[0] for spec in build_site.DOCS.values()] + list(build_site.ARTEFACTS) + [yf.YF_PAGE]
    pages += [f"{og_pages.CLAIM_DIR}/{c['slug']}.html" for c in build_site.load_claims()]
    if lb.published(cityconfig.active().slug):
        pages.append(lb.LB_PAGE)
    return {p: (og_pages.designed(p, arts) or (None,))[0] for p in pages}


def meta(page: str, key: str) -> list[str]:
    attr = "name" if key.startswith("twitter:") else "property"
    return re.findall(rf'<meta {attr}="{re.escape(key)}" content="([^"]*)">', page)


def image_faults(out: Path, pages: dict[str, str | None]) -> list[str]:
    """Item 1's detector: each designed page names its own image in og:image
    and twitter:image, a 1200 x 630 PNG in og-page/; each other page names
    og.png; and every file in og-page/ is named by exactly one page."""
    faults, named = [], {}
    for p, slug in pages.items():
        text = (out / p).read_text(encoding="utf-8")
        og, tw = meta(text, "og:image"), meta(text, "twitter:image")
        if len(og) != 1 or og != tw:
            faults.append(f"{p}: og:image {og} and twitter:image {tw}")
            continue
        if slug is None:
            if og[0] != f"{SITE_URL}/og.png":
                faults.append(f"{p}: keeps no og.png ({og[0]})")
            continue
        m = re.fullmatch(rf"{re.escape(SITE_URL)}/{og_pages.OG_DIR}/({re.escape(slug)}-[a-p]{{12}}\.png)", og[0])
        if not m:
            faults.append(f"{p}: {og[0]} is not its own image")
            continue
        f = out / og_pages.OG_DIR / m.group(1)
        if not f.is_file():
            faults.append(f"{p}: names {m.group(1)}, which is not there")
            continue
        if png_size(f) != (1200, 630):
            faults.append(f"{p}: {f.name} is {png_size(f)}")
        named.setdefault(f.name, []).append(p)
    for f in sorted((out / og_pages.OG_DIR).iterdir()):
        if len(named.get(f.name, [])) != 1:
            faults.append(f"og-page/{f.name} is named by {named.get(f.name, [])}")
    return faults


# ---------------------------------------------------------------------------
# 1. every page has its own image, and every image a page


def test_every_designed_page_has_its_own_image_and_every_image_a_page():
    out = built()
    pages = expected_pages()
    scanned = {p.relative_to(out).as_posix() for p in out.rglob("*.html")
               if meta(p.read_text(encoding="utf-8"), "og:image")}
    # the population is what was scanned: every page the tables name, and
    # beyond them only the apex portal, which is not Johannesburg's
    assert set(pages) <= scanned and scanned - set(pages) <= {"portal.html"}, scanned ^ set(pages)
    designed = [s for s in pages.values() if s]
    claims = tomllib.loads((ROOT / "content/joburg/claims.toml").read_text(encoding="utf-8"))["claim"]
    n = len(list((out / og_pages.OG_DIR).iterdir()))
    assert n == len(designed), n                                  # one image per designed page
    assert len(designed) >= 4 + len(claims)                       # forecast, claims, an article, yf, each claim
    assert image_faults(out, pages) == []
    # it can see: a missing image and an unreferenced one are caught, and the
    # detector goes quiet again when both are put back
    one = sorted((out / og_pages.OG_DIR).iterdir())[0]
    keep = one.read_bytes()
    one.unlink()
    stray = out / og_pages.OG_DIR / "stray-aaaaaaaaaaaa.png"
    stray.write_bytes(keep)
    got = image_faults(out, pages)
    assert any("which is not there" in f for f in got) and any("stray" in f for f in got), got
    stray.unlink()
    one.write_bytes(keep)
    assert image_faults(out, pages) == []


# ---------------------------------------------------------------------------
# 2. every figure in an image is the page's figure


def _rebuild_specs(out: Path) -> list[dict]:
    """The specs, rebuilt from the BUILT pages: the pool is every token span the
    pages carry (the string each printed), as og_pages.figure_pool takes them."""
    import build_make
    import build_site
    import build_your_forecast as yf
    import cityconfig
    cityconfig.use(None)
    pages = expected_pages()
    records = []
    for p in pages:
        for tok, disp in re.findall(r'data-token="([^"]+)"[^>]*>([^<]*)<', (out / p).read_text(encoding="utf-8")):
            records.append({"token": tok, "display": htmllib.unescape(disp)})
    pool, _records = og_pages.figure_pool(records)
    el = build_make.election_of(cityconfig.active())
    yfd = json.loads((out / yf.YF_DIR / build_make.DATA).read_text(encoding="utf-8"))
    arts = build_site.article_meta()
    fc = (out / "forecast.html").read_text(encoding="utf-8")
    claims = tomllib.loads((ROOT / "content/joburg/claims.toml").read_text(encoding="utf-8"))["claim"]
    specs = []
    for p, slug in pages.items():
        if not slug:
            continue
        page = (out / p).read_text(encoding="utf-8")
        layout = og_pages.designed(p, arts)[1]
        if layout == "forecast":
            s = og_pages.forecast_spec(pool, yfd=yfd, out=out, election=el, headline=build_site.OG_TITLE)
        elif layout == "claims":
            s = og_pages.claims_spec(page, claims, headline=build_site.ARTEFACTS["claims.html"][2], pool=pool)
        elif layout == "article":
            s = og_pages.article_spec(arts[p], pool, rows=og_pages.seat_rows(fc))
        elif layout == "claim":
            s = og_pages.claim_spec(page, next(c for c in claims if p == f"{og_pages.CLAIM_DIR}/{c['slug']}.html"), pool)
        else:
            s = og_pages.interactive_spec(yfd, pool, election=el, site=build_site.SITE_NAME)
        s["slug"] = slug
        s["page"] = p
        specs.append(og_pages.check(s))
    return specs, pool


_DRAWN = ("import { cardSVG, imageName } from " + json.dumps((ROOT / "src" / "og-pages.mjs").as_uri()) + ";\n"
          "let s = ''; process.stdin.on('data', d => s += d).on('end', () => {\n"
          "  process.stdout.write(JSON.stringify(JSON.parse(s).map(x => { const v = cardSVG(x); return { name: imageName(v), svg: v }; })));\n"
          "});\n")


def expected_figures(spec: dict, forecast_html: str) -> set[str]:
    """The figure fields each layout must carry, written from og_pages' own
    declarations, not from the spec: the population the comparison covers."""
    import seat_table  # noqa: F401
    if spec["layout"] == "forecast":
        return {t for _c, t in og_pages.FORECAST_LARGEST} | {"generated_date", "council_size"}
    # every card is dated "as of" the pages' date (owner, 2026-10-24)
    if spec["layout"] == "interactive":
        return {"council_size", "generated_date"}
    if spec["layout"] in ("claims", "claim"):
        return {"generated_date"}
    arts = __import__("build_site").article_meta()
    if arts[spec["page"]].get("og_visual") != "seat-ranges":
        return {"generated_date"}
    rows = og_pages.seat_rows(forecast_html)[:og_pages.SEAT_RANGE_ROWS]
    return ({f"seats.{r['code']}.{q}" for r in rows for q in ("median", "p5", "p95")}
            | {"majority", og_pages.FORECAST_ALONE, "seats.band", "generated_date"})


def figure_faults(specs: list[dict], pool: dict, out: Path) -> tuple[list[str], int, int]:
    """``(faults, compared, denominator)``. For each image: its figure fields
    are exactly the layout's (:func:`expected_figures`); each is the string a
    page printed; each is drawn in the image's SVG; and the image the page
    names is the one these figures draw (its name regenerated)."""
    fc = (out / "forecast.html").read_text(encoding="utf-8")
    drawn = json.loads(_node(_DRAWN, specs))
    faults, compared, denominator = [], 0, 0
    for s, d in zip(specs, drawn):
        want = expected_figures(s, fc)
        denominator += len(want)
        if set(s["figures"]) != want:
            faults.append(f"{s['slug']}: carries {sorted(set(s['figures']) ^ want)} against its layout")
        for tok in sorted(want & set(s["figures"])):
            f = s["figures"][tok]
            compared += 1
            if f["display"] != pool.get(tok):
                faults.append(f"{s['slug']}: {tok} is {f['display']!r}, the pages print {pool.get(tok)!r}")
            if htmllib.escape(f["display"], quote=False) not in d["svg"]:
                faults.append(f"{s['slug']}: {tok} ({f['display']!r}) is not drawn")
        og = meta((out / s["page"]).read_text(encoding="utf-8"), "og:image")[0]
        if not og.endswith(f"/{s['slug']}-{d['name']}.png"):
            faults.append(f"{s['slug']}: the page names {og}, these figures draw {d['name']}")
    return faults, compared, denominator


def test_every_figure_in_an_image_is_a_figure_a_page_printed():
    out = built()
    specs, pool = _rebuild_specs(out)
    pages = expected_pages()
    assert {s["slug"] for s in specs} == {v for v in pages.values() if v}   # the images scanned
    faults, compared, denominator = figure_faults(specs, pool, out)
    assert faults == [], faults
    # every field of every layout was compared; the denominator lies between
    # the forecast layout's own count and that plus a seat-range article's
    # (at most 22 fields) for every other image
    fc = next(s for s in specs if s["layout"] == "forecast")
    n_fc = len(expected_figures(fc, (out / "forecast.html").read_text(encoding="utf-8")))
    assert compared == denominator and n_fc <= denominator <= n_fc + 22 * (len(specs) - 1), (compared, denominator)
    # it can see: the forecast image drawing a different figure from the one
    # the page printed is caught, and the detector is quiet when it is reverted
    # (the card draws the compute result's text, so the carried figure and the drawn one are compared)
    keep = fc["result"]["largest"]["ANC"]["text"]
    fc["result"]["largest"]["ANC"]["text"] = "99.9%"
    got, _c, _d = figure_faults(specs, pool, out)
    assert any("these figures draw" in f or "is not drawn" in f for f in got), got
    fc["result"]["largest"]["ANC"]["text"] = keep
    # a carried figure that is not the page's and is not drawn
    tok = next(iter(fc["figures"]))
    keep = fc["figures"][tok]["display"]
    fc["figures"][tok]["display"] = "no such figure"
    got, _c, _d = figure_faults(specs, pool, out)
    assert any("the pages print" in f for f in got) and any("is not drawn" in f for f in got), got
    fc["figures"][tok]["display"] = keep
    # and an image carrying a field its layout does not declare
    fc["figures"]["n_draws"] = {"token": "n_draws", "display": pool.get("n_draws", "x")}
    got, _c, _d = figure_faults(specs, pool, out)
    assert any("against its layout" in f for f in got), got
    del fc["figures"]["n_draws"]
    assert figure_faults(specs, pool, out)[0] == []


def claim_card_faults(spec: dict, svg: str, W: int = 1200, H: int = 630) -> list[str]:
    """What a claim card must be (owner, 2026-10-13 and 2026-10-22): the top bar
    in the party's colour, at least 24px; the quote, then directly under it the
    party's name and speaker, then lower the verdict stamp beside the tested
    statement (where the claim sets card_test) or one reason and the pointer to
    the page; the foot line naming the current forecast's date; and nothing at the
    left in the lowest 15% of the card, where X lays the link's title."""
    out = []
    texts = [(float(x), float(y), anchor, htmllib.unescape(t)) for x, y, anchor, t in
             re.findall(r'<text x="([\d.]+)" y="([\d.]+)"[^>]*?(text-anchor="end")?[^>]*>([^<]*)</text>', svg)]
    flat = " ".join(" ".join(t for _x, _y, _a, t in texts).split())
    # beside the stamp: the tested statement under its tag where the claim
    # sets card_test, otherwise one reason and the pointer to the page (owner,
    # 2026-10-22)
    if spec.get("statement"):
        if spec["statement"] + "." not in flat:
            out.append(f"the tested statement {spec['statement']!r} is not printed on the card")
    elif not spec.get("reason") or spec["reason"] not in flat or not spec.get("more") or spec["more"] not in flat:
        out.append(f"no tested statement, and the reason {spec.get('reason')!r} or its pointer is not printed")
    elif "Tested statement" in flat:
        out.append("a card with no tested statement prints the tag")
    bar = re.search(r'<rect x="0" y="0" width="1200" height="(\d{1,2})" fill="([^"]+)"', svg)
    if not bar or bar.group(2).lower() != spec["colour"].lower():
        out.append(f"the top bar is {bar.group(2) if bar else None}, the party's colour is {spec['colour']}")
    elif int(bar.group(1)) < 24:
        out.append(f"the top bar is {bar.group(1)}px; the owner asked for it much wider (24)")
    m = re.search(r'scale\(([\d.]+)\)"><clipPath id="v-viewbox"><rect x="0" y="0" width="[\d.]+" height="([\d.]+)"', svg)
    stamp_h = float(m.group(1)) * float(m.group(2)) if m else 0
    if stamp_h < 170:
        out.append(f"the verdict stamp is {stamp_h:.0f}px tall; it must be at least 170 on a {H}px card")
    y_of = lambda s_: next((y for x, y, a, t in texts if t == s_ and not a), None)
    first = (spec.get("statement") or spec.get("reason") or "").split()[:1]
    party = y_of(spec["party"])
    beside = y_of("Tested statement") if spec.get("statement") else next(
        (y for x, y, a, t in texts if first and t.startswith(first[0]) and x > 200), None)
    quote_last = max((y for x, y, a, t in texts if x == 56 and t.endswith("\u201d")), default=None)
    if party is None or beside is None or quote_last is None or not (quote_last < party < beside):
        out.append(f"the order is not quote ({quote_last}), party ({party}), text beside the stamp ({beside})")
    elif party - quote_last > 80:
        out.append(f"the party is {party - quote_last:.0f}px under the quote's last line, not directly under it")
    if spec["date_line"] not in flat or "forecast as of" not in flat:
        out.append("the foot line does not name the forecast's date")
    for x, y, anchor, t in texts:
        if y > H * 0.85 and not anchor and x < W / 2:
            out.append(f"text {t!r} at the left, y={y}, in the band X covers")
    return out


def test_a_claim_card_prints_its_statement_beside_a_large_stamp_and_keeps_the_foot_clear():
    out = built()
    specs, pool = _rebuild_specs(out)
    claims = [s for s in specs if s["layout"] == "claim"]
    toml = tomllib.loads((ROOT / "content/joburg/claims.toml").read_text(encoding="utf-8"))["claim"]
    assert len(claims) == len(toml) >= 4
    drawn = json.loads(_node(_DRAWN, claims))
    for spec, d in zip(claims, drawn):
        c = next(c for c in toml if spec["slug"] == og_pages.claim_image_slug(c["slug"]))
        assert (spec["statement"] == " ".join(c["label"].split())) if c.get("card_test") else \
            (spec["statement"] is None and spec["reason"]), (spec["slug"], spec["statement"], spec.get("reason"))
        assert spec["date_line"] == (
            f"Tested on {c['published']}; the verdict stands on the forecast as of {pool['generated_date']}."
            if c["verdict"] in ("FALSE", "TRUE") else
            f"Tested against the whysoserious.city forecast as of {pool['generated_date']}.")
        assert claim_card_faults(spec, d["svg"]) == [], (spec["slug"], claim_card_faults(spec, d["svg"]))
        # the page's og:title is not the statement the card prints
        page = (out / og_pages.CLAIM_DIR / f"{c['slug']}.html").read_text(encoding="utf-8")
        assert meta(page, "og:title") == [f"Party claims tested: {spec['party']}"], meta(page, "og:title")
    spec, svg = claims[0], drawn[0]["svg"]
    # it can see: no statement, a small stamp, text in the covered band, the wrong bar
    assert claim_card_faults({**spec, "statement": "A statement the card never drew"}, svg)
    assert claim_card_faults({**spec, "statement": None, "reason": "A reason the card never drew"}, svg)
    assert claim_card_faults(spec, svg.replace('width="1200" height="24"', 'width="1200" height="8"', 1))
    assert claim_card_faults(spec, re.sub(r'scale\(([\d.]+)\)"><clipPath id="v-viewbox"',
                                          lambda m: f'scale({float(m.group(1)) / 2:.6f})"><clipPath id="v-viewbox"', svg))
    low = svg.replace("</svg>", '<text x="56" y="606" font-size="21">Tested against the forecast.</text></svg>')
    assert any("band X covers" in f for f in claim_card_faults(spec, low))
    assert claim_card_faults({**spec, "colour": "#123456"}, svg)
    assert claim_card_faults(spec, svg) == []


def test_the_renderer_types_no_figure_list():
    """A typed array of figures cannot enter src/og-pages.mjs: the site's
    live-writer scan's data-block pattern finds none, and finds one when it is
    constructed."""
    import stats
    block = dict(stats.SCRIPT_FORBIDDEN)["a data block"]
    src = (ROOT / "src" / "og-pages.mjs").read_text(encoding="utf-8")
    assert not block.search(src)
    assert block.search(src + "\nconst SEATS = [66, 66, 27];\n")


def test_the_forecast_image_is_the_one_card_with_the_forecasts_own_figures_and_date():
    """/forecast's share image is the card the share sheet draws (play-card.js):
    the whysoserious.city logo, "Forecast as of <date>", no "Shared by" and no "Made"
    line, "Make your own prediction at ..." in the foot; its chances are the
    page's and its date is forecast.json's. forecast_spec refuses a page that
    prints another chance or date."""
    import build_make
    out = built()
    specs, pool = _rebuild_specs(out)
    spec = next(s for s in specs if s["layout"] == "forecast")
    d = json.loads(_node(_DRAWN, [spec]))[0]["svg"]
    yfd = json.loads((out / "your-forecast" / build_make.DATA).read_text(encoding="utf-8"))
    flat = " ".join(htmllib.unescape(t) for t in re.findall(r"<text\b[^>]*>([^<]*)</text>", d))
    date = og_pages._long(yfd["forecast_date"])
    assert f"Forecast as of {date}" in flat and date == pool["generated_date"]
    assert 'viewBox="0 0 1969 1002"' in d, "the whysoserious.city logo is not on the card"
    assert "Make your own prediction at joburg.whysoserious.city/your-forecast." in flat
    assert not re.search(r"shared by|try your own|made \d", flat, re.I), flat
    # the chances printed are the page's tokens, and the council the page's size
    for code, tok in og_pages.FORECAST_LARGEST:
        assert f"{pool[tok]} chance it's the" in flat, (code, pool[tok])
    assert f"{pool['council_size']} seats" in flat
    # it can see: a page printing another chance, or another date, is refused
    el = {"city": "Johannesburg", "date": "2026-11-04"}
    kw = dict(yfd=yfd, out=out, election=el, headline="H")
    og_pages.forecast_spec(pool, **kw)
    for bad in ({**pool, "p_anc_largest": "1%"}, {**pool, "generated_date": "1 January 2026"}, {**pool, "council_size": "1"}):
        try:
            og_pages.forecast_spec(bad, **kw)
        except og_pages.OgError:
            continue
        raise AssertionError("forecast_spec took a figure the card does not draw")


def _toy() -> dict:
    return {"slug": "toy", "layout": "article", "headline": "A constructed headline",
            "date_line": "Published 1 October 2026.", "ranges": None, "figures": {}, "alt": "x",
            "kind_colour": og_pages.kind_colour("article")}


def test_the_image_name_moves_with_the_content_and_only_with_it():
    a = _toy()
    b = {**a, "headline": "A constructed headline, changed"}
    na, nb, na2 = image_names([a, b, a])
    assert na != nb and na == na2
    assert re.fullmatch(r"[a-p]{12}", na)
    # two renders of one spec give identical bytes
    with tempfile.TemporaryDirectory() as t1, tempfile.TemporaryDirectory() as t2:
        m1 = og_pages.render_all([a], Path(t1))
        m2 = og_pages.render_all([a], Path(t2))
        assert m1 == m2 == {"toy": f"toy-{na}.png"}
        assert (Path(t1) / m1["toy"]).read_bytes() == (Path(t2) / m2["toy"]).read_bytes()
        # an earlier image stays, byte for byte (owner, 2026-10-24: share
        # images are kept forever), and a drawn image beside it is unchanged
        old = Path(t1) / "old-aaaaaaaaaaaa.png"
        old.write_bytes(b"an image shared in an earlier post")
        og_pages.render_all([a], Path(t1))
        assert sorted(f.name for f in Path(t1).iterdir()) == sorted([m1["toy"], old.name])
        assert old.read_bytes() == b"an image shared in an earlier post"
        assert (Path(t1) / m1["toy"]).read_bytes() == (Path(t2) / m2["toy"]).read_bytes()
        # a file under a drawn name with other bytes is refused, never overwritten
        clash = Path(t1) / m1["toy"]
        good = clash.read_bytes()
        clash.write_bytes(b"other bytes")
        try:
            og_pages.render_all([a], Path(t1))
        except SystemExit as e:
            assert "never overwritten" in str(e)
        else:
            raise AssertionError("an image of the same name with other bytes was overwritten")
        assert clash.read_bytes() == b"other bytes"
        clash.write_bytes(good)
        og_pages.render_all([a], Path(t1))
        assert clash.read_bytes() == good
        # and refuses, rather than removes, a directory it finds there
        (Path(t1) / "sub").mkdir()
        try:
            og_pages.render_all([a], Path(t1))
        except SystemExit as e:
            assert "is a directory" in str(e)
        else:
            raise AssertionError("a directory in og-page/ was passed over")
        assert (Path(t1) / "sub").is_dir()
        (Path(t1) / "sub").rmdir()
        og_pages.render_all([a], Path(t1))


def test_deploy_check_refuses_a_site_missing_a_share_image_git_has_held():
    """`deploy_check.missing_share_images`, on a throwaway repository: an
    image committed and later deleted is reported, on another branch too, and
    the report clears when it is restored. Then on the real tree: every image
    git has held is present."""
    import subprocess
    import deploy_check
    with tempfile.TemporaryDirectory() as t:
        repo = Path(t)
        og = repo / "site" / "og-page"
        og.mkdir(parents=True)
        git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)
        git("init", "-q")
        commit = lambda m: git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", m)
        (og / "a-aaaaaaaaaaaa.png").write_bytes(b"a")
        git("add", "-A"); commit("a")
        assert deploy_check.missing_share_images(repo / "site", root=repo) == []
        git("rm", "-q", "site/og-page/a-aaaaaaaaaaaa.png"); commit("a deleted")
        assert deploy_check.missing_share_images(repo / "site", root=repo) == ["og-page/a-aaaaaaaaaaaa.png"]
        # an image held only on another branch counts too
        git("checkout", "-qb", "other")
        og.mkdir(parents=True, exist_ok=True)     # git removed the emptied directory
        (og / "b-bbbbbbbbbbbb.png").write_bytes(b"b")
        git("add", "-A"); commit("b")
        git("checkout", "-q", "-")
        assert deploy_check.missing_share_images(repo / "site", root=repo) == [
            "og-page/a-aaaaaaaaaaaa.png", "og-page/b-bbbbbbbbbbbb.png"]
        og.mkdir(parents=True, exist_ok=True)
        (og / "a-aaaaaaaaaaaa.png").write_bytes(b"a")
        (og / "b-bbbbbbbbbbbb.png").write_bytes(b"b")
        assert deploy_check.missing_share_images(repo / "site", root=repo) == []
    assert deploy_check.missing_share_images(ROOT / "site") == []


# ---------------------------------------------------------------------------
# 4. badges, both directions


def badge_faults(table: dict, words: set, files: set) -> list[str]:
    out = [f"{w}: no badge" for w in sorted(words - set(table))]
    out += [f"{w}: not a verdict" for w in sorted(set(table) - words)]
    out += [f"{f}: in no row" for f in sorted(files - set(table.values()))]
    out += [f"{f}: no such file" for f in sorted(set(table.values()) - files)]
    return out


def test_every_verdict_has_a_badge_and_every_badge_a_verdict():
    import render_sheet
    words = set(render_sheet.VERDICT_STEP)
    files = {f.name for f in og_pages.STAMPS.glob("verdict-*.svg")}
    assert len(words) == len(files) == len(render_sheet.VERDICT_BADGE) == 9
    assert badge_faults(render_sheet.VERDICT_BADGE, words, files) == []
    # it can see: a row removed is caught both ways, and restored is quiet
    cut = dict(render_sheet.VERDICT_BADGE)
    gone = cut.pop("QUITE UNLIKELY")
    got = badge_faults(cut, words, files)
    assert got == ["QUITE UNLIKELY: no badge", f"{gone}: in no row"], got
    cut["QUITE UNLIKELY"] = gone
    assert badge_faults(cut, words, files) == []


def test_a_claim_whose_verdict_has_no_badge_is_refused():
    claim = {"party": "DA", "verdict": "PROBABLY", "speaker": "Someone, DA", "published": "1 October 2026"}
    page = '<span class="verdict v-open">PROBABLY</span>'
    try:
        og_pages.claims_spec(page, [claim], headline="H", pool={"generated_date": "1 October 2026"})
    except SystemExit as e:
        assert "no badge" in str(e)
    else:
        raise AssertionError("a verdict with no badge was drawn")
    good = {**claim, "verdict": "TRUE"}
    assert og_pages.claims_spec('<span class="verdict v-true">TRUE</span>', [good], headline="H",
                                pool={"generated_date": "1 October 2026"})["items"]


# ---------------------------------------------------------------------------
# 5. tags


def test_page_og_writes_all_six_tags_and_refuses_a_malformed_head():
    import build_site
    img, alt = og_pages.pending(SITE_URL, "toy")
    out = build_site.page_og("A description.", "A title", "toy", img, alt)
    assert meta(out, "og:image") == meta(out, "twitter:image") == [img]
    assert meta(out, "og:image:alt") == [alt]
    assert meta(out, "og:image:width") == ["1200"] and meta(out, "og:image:height") == ["630"]
    assert re.search(r'<meta name="twitter:card" content="summary_large_image">', out)
    filled = og_pages.fill(out, SITE_URL, "toy", "toy-abcdefabcdef.png", "Alt & more")
    assert meta(filled, "og:image") == [f"{SITE_URL}/{og_pages.OG_DIR}/toy-abcdefabcdef.png"]
    assert meta(filled, "og:image:alt") == ["Alt &amp; more"]
    # without an image the page keeps og.png
    plain = build_site.page_og("A description.", "A title", "toy")
    assert meta(plain, "og:image") == [f"{SITE_URL}/og.png"]
    # a head missing a tag page_og rewrites is refused, and restored is not
    saved = build_site.OG_META
    try:
        build_site.OG_META = re.sub(r'<meta property="og:image:alt"[^>]*>\n', "", saved)
        try:
            build_site.page_og("A description.", "A title", "toy", img, alt)
        except SystemExit as e:
            assert "image fields" in str(e)
        else:
            raise AssertionError("a head without og:image:alt was accepted")
    finally:
        build_site.OG_META = saved
    build_site.page_og("A description.", "A title", "toy", img, alt)
    # fill refuses a page whose placeholders are not as page_og wrote them
    try:
        og_pages.fill(plain, SITE_URL, "toy", "toy-abcdefabcdef.png", "x")
    except SystemExit:
        pass
    else:
        raise AssertionError("fill accepted a page with no placeholder")


# ---------------------------------------------------------------------------
# 6. glyph coverage


def test_a_character_the_card_faces_lack_is_refused():
    have = og_pages.faces()
    assert set(have) == {"sans", "sansSemi", "sansBold", "serifSemi", "monoSemi"}
    assert all(200 <= len(v) <= 300 for v in have.values()), {k: len(v) for k, v in have.items()}
    ok = _toy()
    assert og_pages.uncovered(ok, have) == []
    bad = {**ok, "headline": "Ten \u2192 eleven"}      # an arrow: in no card face
    assert og_pages.uncovered(bad, have) and "\u2192" in og_pages.uncovered(bad, have)[0]
    try:
        og_pages.check(bad)
    except SystemExit as e:
        assert "do not carry" in str(e)
    else:
        raise AssertionError("a character no face carries was accepted")
    og_pages.check(ok)


# ---------------------------------------------------------------------------
# the stamps' ids


_STAMPS = ("import * as SC from " + json.dumps((ROOT / "interactive" / "js" / "share-card.js").as_uri()) + ";\n"
           "import { readFileSync } from 'node:fs';\n"
           "let s = ''; process.stdin.on('data', d => s += d).on('end', () => {\n"
           "  const files = JSON.parse(s);\n"
           "  const st = files.map(f => SC.stampOf(readFileSync(f, 'utf8')));\n"
           "  const raw = st.map(x => '<svg viewBox=\"' + x.viewBox + '\">' + x.body + '</svg>');\n"
           "  const placed = st.map((x, k) => SC.stampSVG(x, 's' + k, k * 300, 0, 240));\n"
           "  process.stdout.write(JSON.stringify({ raw, placed }));\n"
           "});\n")


def embed_faults(embeds: list[str]) -> list[str]:
    """Each embed's references (href="#…", url(#…)) resolve to an id defined
    in the SAME embed, and no id is defined twice on the card."""
    out, owner = [], {}
    for k, e in enumerate(embeds):
        for i in re.findall(r'\bid="([^"]+)"', e):
            if i in owner:
                out.append(f"id {i} defined by embeds {owner[i]} and {k}")
            owner.setdefault(i, k)
    for k, e in enumerate(embeds):
        refs = set(re.findall(r'href="#([^"]+)"', e)) | set(re.findall(r"url\(#([^)]+)\)", e))
        mine = set(re.findall(r'\bid="([^"]+)"', e))
        out += [f"embed {k} reaches {r}, defined by embed {owner.get(r)}" for r in sorted(refs - mine)]
    return out


def test_two_badges_on_one_card_keep_their_own_glyphs_and_masks():
    """Two different owner badges on one card (the claims image puts several):
    placed by stampSVG, each keeps its own glyphs, masks, clips and filters.
    Constructed: the same two bodies placed WITHOUT the prefixing collide (the
    files share ids such as glyph-0-0), and the detector reports it."""
    # two different badges that both carry glyphs (href="#…") and masks (url(#…)).
    # The reader badges were redrawn with outlined text on 2026-10-13 and no
    # longer carry glyph ids, so the pair is two verdict badges, which do.
    files = [str(og_pages.STAMPS / "verdict-false.svg"), str(og_pages.STAMPS / "verdict-very-likely.svg")]
    got = json.loads(_node(_STAMPS, files))
    raw_faults = embed_faults(got["raw"])
    assert raw_faults, "the unprefixed bodies did not collide: the test cannot see"
    assert any("glyph" in f for f in raw_faults), raw_faults[:5]
    assert embed_faults(got["placed"]) == []
    # the population: both embeds carry references, and every one was checked
    for e in got["placed"]:
        assert re.search(r'href="#', e) and re.search(r"url\(#", e)
    # the five reader badges on one card: their placed ids never collide
    readers = sorted(str(f) for f in og_pages.STAMPS.glob("reader-*.svg"))
    assert len(readers) == 5
    assert embed_faults(json.loads(_node(_STAMPS, readers))["placed"]) == []


_EMBED = ("import * as SC from " + json.dumps((ROOT / "interactive" / "js" / "share-card.js").as_uri()) + ";\n"
          "import { toPNG } from " + json.dumps((ROOT / "src" / "og-raster-node.mjs").as_uri()) + ";\n"
          "import { readFileSync } from 'node:fs';\n"
          "const GROUND = '#333333', M = 40;\n"
          "let s = ''; process.stdin.on('data', d => s += d).on('end', async () => {\n"
          "  const { files, unclipped } = JSON.parse(s); const out = [];\n"
          "  for (const f of files) {\n"
          "    const text = readFileSync(f, 'utf8'); const st = SC.stampOf(text);\n"
          "    const [vx, vy, vw, vh] = st.viewBox.split(/\\s+/).map(Number);\n"
          "    // the file alone, one unit to the pixel, on the ground\n"
          "    const alone = text.replace(/<svg[^>]*>/, m => m.replace(/width=\"[^\"]*\"/, 'width=\"' + vw + '\"')\n"
          "      .replace(/height=\"[^\"]*\"/, 'height=\"' + vh + '\"') + '<rect x=\"' + vx + '\" y=\"' + vy + '\" width=\"' + vw + '\" height=\"' + vh + '\" fill=\"' + GROUND + '\"/>');\n"
          "    // the same file embedded at (M, M), one unit to the pixel, on a larger ground\n"
          "    const placed = unclipped\n"
          "      ? '<g transform=\"translate(' + M + ' ' + M + ')\"><g transform=\"translate(' + (-vx) + ' ' + (-vy) + ')\">' + SC.prefixIds(st.body, 'e') + '</g></g>'\n"
          "      : SC.stampSVG(st, 'e', M, M, vh);\n"
          "    const card = '<svg xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" width=\"' + (vw + 2 * M) + '\" height=\"' + (vh + 2 * M) + '\">' +\n"
          "      SC.rect(0, 0, vw + 2 * M, vh + 2 * M, GROUND) + placed + '</svg>';\n"
          "    out.push({ file: f, m: M, alone: Buffer.from(await toPNG(alone)).toString('base64'), card: Buffer.from(await toPNG(card)).toString('base64') });\n"
          "  }\n"
          "  process.stdout.write(JSON.stringify(out));\n"
          "});\n")


def embed_render_faults(files: list[str], unclipped: bool = False) -> list[str]:
    """For each stamp: its embedded render (share-card.js stampSVG, at one unit
    to the pixel) equals the file drawn alone within the badge's box, and the
    embed draws nothing outside the box. ``unclipped`` places the body by its
    viewBox with no clip: the constructed violation."""
    import base64
    import io
    import numpy as np
    from PIL import Image
    got = json.loads(_node(_EMBED, {"files": files, "unclipped": unclipped}))
    faults = []
    for g in got:
        alone = np.asarray(Image.open(io.BytesIO(base64.b64decode(g["alone"]))).convert("RGB"), dtype=int)
        card = np.asarray(Image.open(io.BytesIO(base64.b64decode(g["card"]))).convert("RGB"), dtype=int)
        m, (h, w) = g["m"], alone.shape[:2]
        inside = card[m:m + h, m:m + w]
        name = Path(g["file"]).name
        # equal up to anti-aliasing: a pixel differing by more than 8 levels in
        # any channel is a difference, and they may be at most 1 in 2,000 of
        # the box (reader-hail-mary's masks rasterise 22 pixels of its 257,536
        # differently in the two renders; a misplaced or missing part of a
        # badge moves thousands)
        if inside.shape != alone.shape:
            faults.append(f"{name}: the embed's box is not the file's size")
        elif (np.abs(inside - alone).max(axis=2) > 8).sum() > h * w / 2000:
            faults.append(f"{name}: the embed differs from the file inside the badge's box")
        ground = card[0, 0]
        outside = card.copy()
        outside[m:m + h, m:m + w] = ground
        if np.abs(outside - ground).max() > 8:
            faults.append(f"{name}: the embed draws outside the badge's box")
    return faults


#: A constructed stamp drawing past its viewBox, as the owner's FALSE badge
#: did until its stray lettering was removed (2026-10-10).
SPILL = ('<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" '
         'xmlns:xlink="http://www.w3.org/1999/xlink" width="100pt" height="100pt" viewBox="50 50 100 100">'
         '<defs><clipPath id="clip-0"><rect x="0" y="0" width="400" height="400"/></clipPath></defs>'
         '<g clip-path="url(#clip-0)"><circle cx="100" cy="100" r="40" fill="#ff0000"/>'
         '<rect x="160" y="60" width="20" height="20" fill="#ffffff"/></g></svg>')


def test_every_stamp_embeds_as_the_file_draws_alone_and_nothing_outside_it():
    """Each of the owner's stamps, embedded by stampSVG, draws exactly what the
    file draws alone within its viewBox and nothing outside it. Constructed: a
    stamp with drawing past its viewBox is clean through stampSVG and caught
    when its body is placed without the clip."""
    files = sorted(str(f) for f in og_pages.STAMPS.glob("*.svg"))
    assert len(files) == 15
    assert embed_render_faults(files) == []
    with tempfile.TemporaryDirectory() as t:
        spill = Path(t) / "spill.svg"
        spill.write_text(SPILL, encoding="utf-8")
        assert embed_render_faults([str(spill)]) == []
        caught = embed_render_faults([str(spill)], unclipped=True)
        assert caught == ["spill.svg: the embed draws outside the badge's box"], caught


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
