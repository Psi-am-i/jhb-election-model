"""Reader text names This Model and none of its internal parts.

Owner, 2026-10-24 (audits/2026-10-23-site-sweep/BRIEF-2-tone.md, F; STYLE.md
rule 6): where the site means its own model it says "This Model", never "the
model" or "our model", and internal terms (pools, draws, seed, overhang, θ,
modal, the file and script names) never appear.

What is scanned, on the built site: every live page's visible text (the
`<title>` included; scripts, styles and HTML comments are not reader text),
the tooltip attributes (`data-tip`, `data-prov`, `title`), `aria-label`, and
the meta descriptions (`description`, `og:description`, `twitter:description`).
The strings the interactive's scripts write at run time are not on a built
page and are not scanned here.

The population, and how each part of the four-part rule (CLAUDE.md §4) is met:

* **It scanned the right thing.** Every built `*.html` is either LIVE or
  FROZEN, and FROZEN is asserted equal to the dated pieces the site itself
  names: the review (`build_site.DOCS`) and every article in
  `content/joburg/articles.toml`. A frozen page is not rewritten (STYLE.md rule
  13), so on it only the live regions are scanned: its "since then" notes and
  the teasers under it. EXCLUDED names the one page left out whole, and why.
* **It looked.** The scanned pages are a two-sided share of the built pages,
  the scanned text a two-sided share of their bytes, and every region kind is
  non-empty.
* **It can see.** A constructed page carrying each term in each region kind is
  caught, the same page with the term removed is quiet, and the parts that are
  not reader text (a comment, a script) stay quiet.
* **Its input is constructed** for the detector; only the population scan
  reads a build, into a temporary directory against an empty ledger.

EXEMPT lists the uses that are not the internal term (the verb "to draw") and
the one held for the owner, each with the exact count it must still match, so
an exemption whose text has gone fails instead of hiding the next use.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import tomllib
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import run_module, skip  # noqa: E402

#: Each forbidden term, by name. "The model" is the site's own model said the
#: wrong way; the rest are internal terms.
TERMS = {
    "the model": re.compile(r"\b(?:the|our)\s+model\b", re.I),
    "pool": re.compile(r"\bpools?\b", re.I),
    "draw": re.compile(r"\bdraws?\b", re.I),
    "seed": re.compile(r"\bseeds?\b", re.I),
    "overhang": re.compile(r"\boverhang", re.I),
    "θ": re.compile("θ"),
    "modal": re.compile(r"\bmodal\b", re.I),
    "render_sheet": re.compile(r"render_sheet"),
    ".py": re.compile(r"\b\w+\.py\b"),
}
#: The attributes a reader sees or hears.
READER_ATTRS = ("data-tip", "data-prov", "title", "aria-label")
META = ({"name": "description"}, {"property": "og:description"},
        {"name": "twitter:description"})
#: The region kinds, each of which the population must contain.
KINDS = ("text", "data-tip", "data-prov", "title", "aria-label", "meta")

#: The dated pieces (STYLE.md rule 13). Asserted equal to what the site names.
FROZEN = ("if-the-law-were-german.html", "laingsburg-2021.html",
          "minority-administrations.html", "nobody-catches-the-votes.html",
          "nobody-will-win.html", "review.html")
#: Pages left out whole, and why.
EXCLUDED = {
    "corrections.html": "quotes the published wording it corrects; an entry "
                        "changes only under a brief that names it",
}
#: (page, term, exact phrase) -> how many times it must match. A phrase is
#: matched in the scanned text with whitespace collapsed. A phrase of "*"
#: exempts every use of the term on that page, and must still match one.
EXEMPT = {
    # the verb, not the simulations
    ("methodology.html", "draw", "the ANC and the IFP draw overwhelmingly"): 1,
    ("methodology.html", "draw", "This Model draws thousands of answers"): 1,
    ("methodology.html", "draw", "Each simulation draws fresh values"): 1,
    ("sources.html", "draw", "The IEC draws these"): 1,
    ("privacy.html", "draw", "the server draws from the link"): 1,
    ("your-forecast/index.html", "draw", "map draws it as"): 1,
}
#: (lo, hi) shares: scanned pages of built pages; scanned characters of the
#: scanned pages' bytes.
PAGE_SHARE = (0.5, 1.0)
TEXT_SHARE = (0.03, 0.8)


# --- the detector ---------------------------------------------------------------

class _Reader(HTMLParser):
    """Collects (kind, text) pairs a reader meets. `live_only` keeps only the
    live regions of a frozen page: `aside.since` and `section.more-commentary`."""

    LIVE = (("aside", "since"), ("section", "more-commentary"))

    def __init__(self, live_only: bool = False):
        super().__init__(convert_charrefs=True)
        self.live_only = live_only
        self.out: list[tuple[str, str]] = []
        self._skip = 0
        self._live: list[list] = []      # [tag, depth]

    def _on(self) -> bool:
        return not self._skip and (not self.live_only or bool(self._live))

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self._live and tag == self._live[-1][0]:
            self._live[-1][1] += 1
        elif self.live_only and any(tag == t and c in (a.get("class") or "").split()
                                    for t, c in self.LIVE):
            self._live.append([tag, 1])
        if tag in ("script", "style"):
            self._skip += 1
        if not self._on():
            return
        for k in READER_ATTRS:
            if a.get(k):
                self.out.append((k, a[k]))
        if tag == "meta" and any(all(a.get(k) == v for k, v in m.items()) for m in META):
            self.out.append(("meta", a.get("content") or ""))

    def handle_startendtag(self, tag, attrs):
        if not self._on():
            return
        a = dict(attrs)
        for k in READER_ATTRS:
            if a.get(k):
                self.out.append((k, a[k]))
        if tag == "meta" and any(all(a.get(k) == v for k, v in m.items()) for m in META):
            self.out.append(("meta", a.get("content") or ""))

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1
        if self._live and tag == self._live[-1][0]:
            self._live[-1][1] -= 1
            if not self._live[-1][1]:
                self._live.pop()

    def handle_data(self, data):
        if self._on() and data.strip():
            self.out.append(("text", data))


def reader_text(html: str, live_only: bool = False) -> list[tuple[str, str]]:
    r = _Reader(live_only)
    r.feed(html)
    r.close()
    return r.out


def _flat(s: str) -> str:
    return re.sub(r"\s+", " ", s)


def hits(page: str, html: str, live_only: bool = False) -> list[tuple[str, str, str, str]]:
    """(page, kind, term, context) for every forbidden term not exempted."""
    pieces = reader_text(html, live_only)
    found = []
    for kind, text in pieces:
        flat = _flat(text)
        for name, rx in TERMS.items():
            for m in rx.finditer(flat):
                found.append((page, kind, name, flat[max(0, m.start() - 50):m.end() + 50]))
    return found


def apply_exemptions(found, texts: dict[str, str]):
    """Drop the exempted hits; return (kept, faults), where a fault is an
    exemption that no longer matches its stated count."""
    faults, kept = [], list(found)
    for (page, term, phrase), n in EXEMPT.items():
        if phrase == "*":
            mine = [h for h in kept if h[0] == page and h[2] == term]
            if not mine:
                faults.append((page, term, phrase, "at least 1", 0))
            kept = [h for h in kept if h not in mine]
            continue
        got = texts.get(page, "").count(phrase)
        if got != n:
            faults.append((page, term, phrase, n, got))
        dropped = 0
        for h in list(kept):
            if h[0] == page and h[2] == term and phrase in h[3] and dropped < min(got, n):
                kept.remove(h)
                dropped += 1
    return kept, faults


# --- the detector, on constructed pages -------------------------------------------

def _page(term: str = "") -> str:
    """A constructed page carrying `term` in every region kind (or nowhere)."""
    t = term
    return (f'<!doctype html><html><head><title>Forecast {t}</title>'
            f'<meta name="description" content="How sure {t} is.">'
            f'<meta property="og:description" content="Seats {t}.">'
            f'<script>var x = "the model";</script><style>.x{{}}</style></head><body>'
            f'<!-- the model, pools and draws: a comment is not reader text -->'
            f'<p>Every ward {t} counts.</p>'
            f'<span data-tip="Ward 1 {t}">1</span>'
            f'<span class="mstat" data-prov="5 seats.&#10;SOURCE: {t}.">5</span>'
            f'<a title="Open {t}" href="#">x</a>'
            f'<svg aria-label="Map {t}"><rect/></svg>'
            f'</body></html>')


def test_each_term_is_caught_in_each_region_and_the_clean_page_is_quiet():
    assert hits("p.html", _page()) == [], hits("p.html", _page())
    samples = {"the model": "the model", "pool": "pools", "draw": "draws",
               "seed": "seed", "overhang": "overhang", "θ": "θ", "modal": "modal",
               "render_sheet": "render_sheet", ".py": "src/render_sheet.py"}
    assert set(samples) == set(TERMS)
    for name, word in samples.items():
        found = hits("p.html", _page(word))
        kinds = {k for _, k, n, _ in found if n == name}
        assert kinds == set(KINDS), (name, sorted(kinds))
        assert hits("p.html", _page()) == []          # reverted: quiet again
    # "This Model" is the right form and is not caught
    assert hits("p.html", _page("This Model")) == []
    # our model, in either case
    assert {n for _, _, n, _ in hits("p.html", _page("Our model"))} == {"the model"}


def test_comments_scripts_and_styles_are_not_reader_text():
    html = ("<html><head><style>.pools{}</style><script>draws()</script></head>"
            "<body><!-- the model --><p>Seats.</p></body></html>")
    assert hits("p.html", html) == []
    assert hits("p.html", html.replace("<p>Seats.</p>", "<p>the model</p>"))


def test_a_frozen_page_is_scanned_only_in_its_live_regions():
    body = ('<h1>Dated piece</h1><p>the model, as written on 8 August</p>'
            '<aside class="since"><div class="since-h">Now</div><p>{x}</p></aside>'
            '<section class="more-commentary"><div><a>{y}</a></div></section>'
            '<p>after the model</p>')
    clean = body.format(x="This Model says", y="Teaser")
    assert hits("a.html", clean, live_only=True) == []
    assert hits("a.html", clean, live_only=False)          # the frozen text is seen whole
    note = hits("a.html", body.format(x="the model says", y="Teaser"), live_only=True)
    teaser = hits("a.html", body.format(x="This Model", y="the model's pools"), live_only=True)
    assert [h[2] for h in note] == ["the model"], note
    assert sorted(h[2] for h in teaser) == ["pool", "the model"], teaser


def test_an_exemption_that_no_longer_matches_its_count_is_a_fault():
    key = next(k for k, n in EXEMPT.items() if k[2] != "*")
    page, term, phrase = key
    text = f"before {phrase} after"
    found = hits(page, f"<p>{text}</p>")
    assert any(h[2] == term for h in found), found
    kept, faults = apply_exemptions(found, {page: text})
    assert not [h for h in kept if h[2] == term] and not [f for f in faults if f[:3] == key]
    # the phrase gone from the page: the exemption is reported, not silently kept
    _, faults = apply_exemptions([], {page: "before after"})
    assert [f[:3] for f in faults if f[:3] == key] == [key], faults
    # the phrase twice: the second use is not exempted
    found2 = hits(page, f"<p>{text} {text}</p>")
    kept2, faults2 = apply_exemptions(found2, {page: f"{text} {text}"})
    assert [f[:3] for f in faults2 if f[:3] == key] == [key]
    assert [h for h in kept2 if h[2] == term], kept2


# --- the built site ---------------------------------------------------------------

_BUILT: dict = {}


def _site() -> Path:
    """`build_site.main` into a temporary directory against an empty ledger, the
    way `test_tooltip_says` builds; skipped, by name, where the build refuses
    for a reason outside this module (the maps drawn from another run)."""
    if not (ROOT / "data" / "processed" / "forecast_summary.json").exists():
        skip("needs data/processed/forecast_summary.json; run montecarlo.py")
    if "site" in _BUILT:
        return _BUILT["site"]
    tmp = Path(tempfile.mkdtemp(prefix="reader-terms-"))
    (tmp / "led" / "joburg").mkdir(parents=True)
    driver = ("import sys; sys.path.insert(0, 'src'); import build_site as B; "
              f"raise SystemExit(B.main(['--out', {json.dumps(str(tmp / 'site'))}, "
              f"'--ledger-root', {json.dumps(str(tmp / 'led'))}, "
              "'--allow-orphans', '--allow-stale-sources']))")
    r = subprocess.run([str(ROOT / ".venv/bin/python"), "-c", driver],
                       capture_output=True, text=True, cwd=ROOT)
    out = r.stdout + r.stderr
    if r.returncode != 0 and "refusing to build" in out and "map was drawn from run" in out:
        skip("the build refuses: the ward maps were drawn from another run "
             "(render_map.py and hex_cartogram.py must be re-run first)")
    assert r.returncode == 0, out[-2000:]
    _BUILT["site"] = tmp / "site"
    return _BUILT["site"]


def frozen_named_by_the_site() -> set[str]:
    import build_site as B
    arts = tomllib.loads((ROOT / "content" / "joburg" / "articles.toml").read_text(encoding="utf-8"))
    pieces = {a["href"] + ".html" for a in arts["article"]}
    review = B.DOCS["docs-public/review.md"][0]
    return pieces | {review}


def scan_site(site: Path) -> dict:
    """The scan of a built site: its population, its hits and its faults."""
    pages = {str(f.relative_to(site)): f.read_text(encoding="utf-8")
             for f in sorted(site.rglob("*.html"))}
    found, texts, kinds, chars, nbytes = [], {}, set(), 0, 0
    scanned = []
    for page, html in pages.items():
        if page in EXCLUDED:
            continue
        live_only = page in FROZEN
        pieces = reader_text(html, live_only)
        scanned.append(page)
        kinds |= {k for k, _ in pieces}
        chars += sum(len(t) for _, t in pieces)
        nbytes += len(html)
        texts[page] = _flat(" ".join(t for _, t in pieces))
        found += hits(page, html, live_only)
    kept, faults = apply_exemptions(found, texts)
    return {"pages": pages, "scanned": scanned, "kinds": kinds, "chars": chars,
            "bytes": nbytes, "hits": kept, "faults": faults}


def check_scan(scan: dict) -> list:
    """Every assertion the population scan makes, as a list of failures."""
    bad = []
    built = set(scan["pages"])
    if set(FROZEN) != frozen_named_by_the_site():
        bad.append(("FROZEN is not the site's dated pieces",
                    sorted(set(FROZEN) ^ frozen_named_by_the_site())))
    for name in set(FROZEN) | set(EXCLUDED):
        if name not in built:
            bad.append(("named page not built", name))
    if set(FROZEN) & set(EXCLUDED):
        bad.append(("frozen and excluded", sorted(set(FROZEN) & set(EXCLUDED))))
    share = len(scan["scanned"]) / max(1, len(built))
    if not PAGE_SHARE[0] <= share <= PAGE_SHARE[1]:
        bad.append(("scanned pages share", share))
    text_share = scan["chars"] / max(1, scan["bytes"])
    if not TEXT_SHARE[0] <= text_share <= TEXT_SHARE[1]:
        bad.append(("scanned text share", text_share))
    missing = set(KINDS) - scan["kinds"]
    if missing:
        bad.append(("region kinds never seen", sorted(missing)))
    bad += [("exemption count", f) for f in scan["faults"]]
    bad += [("forbidden term", h) for h in scan["hits"]]
    return bad


def test_the_population_check_fires_on_a_constructed_site_and_clears():
    """The population assertions themselves, on a constructed site: a clean
    one passes, a planted violation and a wrong population each fail."""
    with tempfile.TemporaryDirectory() as t:
        site = Path(t)
        live = _page()
        for name in sorted(frozen_named_by_the_site() | set(EXCLUDED)
                           | {"index.html", "forecast.html", "sources.html",
                              "privacy.html", "methodology.html", "your-forecast/index.html"}):
            (site / name).parent.mkdir(parents=True, exist_ok=True)
            html = live
            if name in FROZEN:
                html = live.replace("<p>Every ward", '<aside class="since"><p>Every ward').replace(
                    " counts.</p>", " counts.</p></aside>")
            (site / name).write_text(html, encoding="utf-8")
        # the exempt phrases, present exactly as often as stated
        for (page, term, phrase), n in EXEMPT.items():
            f = site / page
            f.write_text(f.read_text().replace(
                "</body>", (f"<p>{phrase}</p>" * n if phrase != "*" else f"<p>{term}s</p>") + "</body>"))
        assert check_scan(scan_site(site)) == [], check_scan(scan_site(site))[:5]
        # a planted violation on a live page fires, and goes quiet when reverted
        f = site / "index.html"
        f.write_text(_page("the model"))
        assert [b[1][2] for b in check_scan(scan_site(site)) if b[0] == "forbidden term"]
        f.write_text(live)
        assert check_scan(scan_site(site)) == []
        # the frozen text of a dated piece is not scanned; its since note is
        g = site / "review.html"
        g.write_text(g.read_text().replace("<body>", "<body><h1>the model</h1>", 1))
        assert check_scan(scan_site(site)) == []
        g.write_text(g.read_text().replace("<aside class=\"since\"><p>Every ward",
                                           "<aside class=\"since\"><p>the model, every ward"))
        assert check_scan(scan_site(site)), "a since note on a frozen page was not scanned"


def test_every_live_page_names_this_model_and_no_internal_term():
    scan = scan_site(_site())
    bad = check_scan(scan)
    assert not bad, bad[:10]


if __name__ == "__main__":
    raise SystemExit(run_module(sys.modules[__name__]))
