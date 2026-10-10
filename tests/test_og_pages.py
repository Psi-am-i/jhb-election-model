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
    assert len(designed) <= n <= len(designed) + len(claims), n   # two-sided
    assert len(designed) >= 4                                     # forecast, claims, an article, yf
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
    pages carry (the string each printed), plus the forecast card's coalition
    tokens no page prints, computed as og_pages.figure_pool computes them."""
    import build_make
    import build_site
    import build_your_forecast as yf
    import cityconfig
    import stats
    cityconfig.use(None)
    pages = expected_pages()
    records = []
    for p in pages:
        for tok, disp in re.findall(r'data-token="([^"]+)"[^>]*>([^<]*)<', (out / p).read_text(encoding="utf-8")):
            records.append({"token": tok, "display": htmllib.unescape(disp)})
    reg = stats.load_registry(ROOT / "content/joburg/stats.toml")
    ctx = stats.load_context(ROOT / "data/processed")
    pool, _records = og_pages.figure_pool(records, reg, ctx)
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
            s = og_pages.forecast_spec(page, pool, election=el, headline=build_site.OG_TITLE,
                                       wards=len(yfd["geometry"]["wards"]))
        elif layout == "claims":
            s = og_pages.claims_spec(page, claims, headline=build_site.ARTEFACTS["claims.html"][2])
        elif layout == "article":
            s = og_pages.article_spec(arts[p], pool, rows=og_pages.seat_rows(fc))
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
        return ({t for _c, t in og_pages.FORECAST_LARGEST} | {og_pages.FORECAST_ALONE}
                | {og_pages.coalition_token(g) for g in og_pages.FORECAST_COALITIONS}
                | {"generated_date", "council_size"})
    if spec["layout"] == "interactive":
        return {"council_size"}
    if spec["layout"] == "claims":
        return set()
    arts = __import__("build_site").article_meta()
    if arts[spec["page"]].get("og_visual") != "seat-ranges":
        return set()
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
    keep = fc["rows"][0]["value"]
    fc["rows"][0]["value"] = "99.9%"
    got, _c, _d = figure_faults(specs, pool, out)
    assert any("these figures draw" in f for f in got), got
    fc["rows"][0]["value"] = keep
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


def test_the_renderer_types_no_figure_list():
    """A typed array of figures cannot enter src/og-pages.mjs: the site's
    live-writer scan's data-block pattern finds none, and finds one when it is
    constructed."""
    import stats
    block = dict(stats.SCRIPT_FORBIDDEN)["a data block"]
    src = (ROOT / "src" / "og-pages.mjs").read_text(encoding="utf-8")
    assert not block.search(src)
    assert block.search(src + "\nconst SEATS = [66, 66, 27];\n")


def test_the_forecast_map_must_be_cut_out_whole():
    """forecast_spec refuses a map with a ward outline fewer than the geometry's."""
    page = ('<svg viewBox="0 0 10 10"><defs><pattern id="p"><line x1="1" stroke="#000000" stroke-width="1"/>'
            '</pattern></defs><path d="M0 0L1 1Z" fill="#111111"/><path d="M2 2L3 3Z" fill="url(#p)"/></svg>')
    assert og_pages.ward_shapes(og_pages.map_paths(page)) == 2
    pool = {og_pages.coalition_token(g): "1%" for g in og_pages.FORECAST_COALITIONS}
    pool.update({t: "1%" for _c, t in og_pages.FORECAST_LARGEST})
    pool.update({og_pages.FORECAST_ALONE: "1%", "generated_date": "1 October 2026", "council_size": "270"})
    el = {"city": "Johannesburg", "date": "2026-11-04"}
    og_pages.forecast_spec(page, pool, election=el, wards=2, headline="H")
    try:
        og_pages.forecast_spec(page, pool, election=el, wards=3, headline="H")
    except SystemExit as e:
        assert "ward outlines" in str(e)
    else:
        raise AssertionError("a map short of a ward was accepted")


# ---------------------------------------------------------------------------
# 3. the name moves with the content


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
        # render_all leaves exactly what it drew
        (Path(t1) / "old-aaaaaaaaaaaa.png").write_bytes(b"x")
        og_pages.render_all([a], Path(t1))
        assert sorted(f.name for f in Path(t1).iterdir()) == [m1["toy"]]
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
    gone = cut.pop("UNLIKELY")
    got = badge_faults(cut, words, files)
    assert got == ["UNLIKELY: no badge", f"{gone}: in no row"], got
    cut["UNLIKELY"] = gone
    assert badge_faults(cut, words, files) == []


def test_a_claim_whose_verdict_has_no_badge_is_refused():
    claim = {"party": "DA", "verdict": "PROBABLY", "speaker": "Someone, DA", "published": "1 October 2026"}
    page = '<span class="verdict v-open">PROBABLY</span>'
    try:
        og_pages.claims_spec(page, [claim], headline="H")
    except SystemExit as e:
        assert "no badge" in str(e)
    else:
        raise AssertionError("a verdict with no badge was drawn")
    good = {**claim, "verdict": "TRUE"}
    assert og_pages.claims_spec('<span class="verdict v-true">TRUE</span>', [good], headline="H")["items"]


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
    # two different badges that both carry glyphs (href="#…") and masks (url(#…))
    files = [str(og_pages.STAMPS / "verdict-false.svg"), str(og_pages.STAMPS / "reader-safe-bet.svg")]
    got = json.loads(_node(_STAMPS, files))
    raw_faults = embed_faults(got["raw"])
    assert raw_faults, "the unprefixed bodies did not collide: the test cannot see"
    assert any("glyph" in f for f in raw_faults), raw_faults[:5]
    assert embed_faults(got["placed"]) == []
    # the population: both embeds carry references, and every one was checked
    for e in got["placed"]:
        assert re.search(r'href="#', e) and re.search(r"url\(#", e)


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
