"""EDIT MODE: THE SITE'S WORDS EDITED ON THE SITE, NEVER ITS FIGURES.

`src/edit_mode.py` serves the last build locally with an edit button on every
block `site_text.blocks` offers, and writes an edit back to its source. The
properties asserted here (owner's sweep, 2026-10-03, plan lane E):

* **a token can be kept or deleted, never edited.** A changed name or value is
  a new token and is refused, and so is a half-deleted one; a registry token is
  accepted only when "make it a token" put it there.
* **a new typed number is flagged**, by the build's own number gate, and Apply
  refuses until it is made a token, registered or removed.
* **apply round trip**: the edit reaches its own source file and nothing else,
  wrapped as the file was, and the build's block list finds the new words.
* **never on the public site**: the overlay is not shipped by the build, and
  `deploy_check` refuses a site that carries it (four-part absence rule,
  CLAUDE.md §4: the scan's population is the site's pages, a constructed
  violation is caught, and the detector goes quiet once it is removed).

⛔ **EVERY WRITE GOES TO A TEMPORARY COPY OF THE SOURCES.** The module's ROOT
is pointed at it for the duration; the real tree is never written.
"""
from __future__ import annotations

import email.message
import io
import os
import re
import threading
import tomllib
import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module                            # noqa: E402

import edit_mode as EM                                           # noqa: E402
import site_text as ST                                           # noqa: E402

GEN = "{{@home.p_alone=0.000800;chance;seat_draws.csv, 5,000 simulations}}"


def _block(text: str, source: str = "forecast-sheet.html") -> dict:
    return {"source": source, "kind": "p", "text": text, "id": "x"}


@contextmanager
def _sources():
    """A temporary copy of every source edit mode reads or writes, with
    site_text and edit_mode pointed at it."""
    tmp = Path(tempfile.mkdtemp())
    for rel in ("home.html", "forecast-sheet.html"):
        shutil.copy(ROOT / rel, tmp / rel)
    shutil.copytree(ROOT / "docs-public", tmp / "docs-public")
    (tmp / "content" / "joburg").mkdir(parents=True)
    for f in ("stats.toml", "claims.toml", "articles.toml"):
        shutil.copy(ROOT / "content" / "joburg" / f, tmp / "content" / "joburg" / f)
    saved = ST.ROOT, ST.STATS, EM.ROOT
    ST.ROOT, ST.STATS, EM.ROOT = tmp, tmp / "content" / "joburg" / "stats.toml", tmp
    try:
        yield tmp
    finally:
        ST.ROOT, ST.STATS, EM.ROOT = saved
        shutil.rmtree(tmp)


def _first(session, source: str, need: str = "") -> dict:
    """The first block from ``source`` containing ``need``; from Markdown, the
    first plain paragraph (a number in a heading or a table is not gated)."""
    return next(b for b in session.blocks.values()
                if b["source"] == source and need in b["text"] and "repeated" not in b
                and not (source.endswith(".md") and b["text"].startswith(tuple("#|-<*>0123456789"))))


# --------------------------------------------------------------------------
# tokens

def test_a_token_can_be_kept_or_deleted_never_edited():
    old = f"The largest party: {{{{p_anc_largest}}}} chance; alone {GEN}."
    b = _block(old)
    assert ST.edit_problems(b, old.replace("The largest", "The biggest")) == []
    assert ST.edit_problems(b, old.replace("{{p_anc_largest}}", "")) == [], "deleting is allowed"
    assert ST.edit_problems(b, old.replace(GEN, "")) == [], "deleting is allowed"
    refused = {
        "a renamed token": old.replace("{{p_anc_largest}}", "{{p_da_largest}}"),
        "a generated token's value": old.replace("=0.000800;", "=0.5;"),
        "a generated token's source": old.replace("5,000 simulations}}", "a guess}}"),
        "a half-deleted token": old.replace("{{p_anc_largest}}", "{{p_anc_largest"),
        "a token typed in": old + " {{n_draws}}",
        "a duplicated token": old + " {{p_anc_largest}}",
    }
    for what, new in refused.items():
        problems = ST.edit_problems(b, new)
        assert problems and "figures" in problems[0], (what, problems)
        assert problems[0].startswith("The edit "), problems
    # the message names what happened: a duplicate is not "missing"
    dup = ST.edit_problems(b, refused["a duplicated token"])[0]
    assert "{{p_anc_largest}} appears 2 times; the original has 1" in dup, dup
    assert "{{p_da_largest}} is not in the original block" in ST.edit_problems(
        b, refused["a renamed token"])[0]
    # and through plan(), the one writer: a refused edit raises before writing
    with _sources():
        blk = next(x for x in ST.blocks() if "{{" in x["text"] and "repeated" not in x)
        tok = ST.placeholders(blk["text"])[0]
        try:
            ST.plan({blk["id"]: blk["text"].replace(tok, tok[:-2] + "x}}", 1)})
        except ST.EditRefused as exc:
            assert "figures" in str(exc)
        else:
            raise AssertionError("plan() wrote an edit that changed a token")


def test_a_token_put_in_for_a_typed_number_is_accepted_only_when_declared():
    b = _block("We ran 5,000 simulations.")
    new = "We ran {{n_draws}} simulations."
    assert ST.edit_problems(b, new), "an undeclared new token must be refused"
    assert ST.edit_problems(b, new, added=["{{n_draws}}"]) == []
    assert ST.edit_problems(b, new + " {{n_draws}}", added=["{{n_draws}}"]), (
        "one declared token licenses one occurrence")


def test_broken_markup_is_refused_and_a_deleted_pair_is_not():
    old = 'Read <a href="methodology">how it works</a> first.'
    b = _block(old)
    assert ST.edit_problems(b, 'Read how it works first.') == []
    assert ST.edit_problems(b, 'Read <a href="methodology">how it works first.')
    assert ST.edit_problems(b, 'Read how it works</a> first.')
    toml = _block("A **bold** claim <b>", "content/joburg/claims.toml")
    assert ST.edit_problems(toml, "A **bold** claim") == [], "TOML text carries no markup rule"
    # a tag can be kept, or deleted with its partner; never added or changed
    for added in (old + ' <span style="color:red">x</span>',
                  old + " <script>alert(1)</script>",
                  old.replace('href="methodology"', 'href="https://example.com"'),
                  old + " <br>"):
        problems = ST.edit_problems(b, added)
        assert problems and "markup" in problems[0], (added, problems)


def test_unpaired_markdown_emphasis_is_refused():
    old = "The **largest party** is _not_ the winner, and {{p_anc_largest}} says so."
    b = _block(old, "docs-public/x.md")
    assert ST.edit_problems(b, old.replace("**largest party**", "largest party")) == []
    assert ST.edit_problems(b, old.replace("_not_", "not")) == []
    assert ST.edit_problems(b, old + " A **new** emphasis.") == []
    for broken in (old.replace("**largest", "largest", 1),
                   old.replace("party**", "party", 1),
                   old.replace("_not_", "not_")):
        problems = ST.edit_problems(b, broken)
        assert problems and "emphasis" in problems[0], (broken, problems)
    # the same characters in an HTML source are text, not emphasis
    assert ST.edit_problems(_block(old), old.replace("**largest", "largest", 1)) == []


TYPED = ('… "really"', "two\nlines", "a\\b", 'ends in a quote"', "tab\there")


def test_a_toml_edit_is_escaped_for_its_string_and_read_back():
    """Population: a field of each string style the TOML sources use (a
    one-line title, a multi-line standfirst). The reviewer's three inputs (a
    quotation mark, a line break, a backslash), a closing quote and a tab each
    reach the file and read back exactly as typed."""
    with _sources():
        found = [b for b in ST.blocks() if b["source"].endswith(".toml")
                 and "repeated" not in b]
        title = next(b for b in found if b["kind"].endswith(".title"))
        multi = next(b for b in found if b["kind"].endswith(".standfirst"))
        for blk in (title, multi):
            for typed in TYPED:
                new = blk["text"] + " " + typed
                _changes, files = ST.plan({blk["id"]: new})
                body = files[blk["source"]][1]
                tomllib.loads(body)
                now = {x["kind"]: x["text"] for x in ST._toml_blocks(
                    blk["source"], body, *ST.TOML_SOURCES[blk["source"]])}
                assert now[blk["kind"]] == new.strip(), (blk["kind"], typed, now[blk["kind"]])
        # a string style that cannot hold the text is refused, not corrupted
        for head, text in (("title = '", "it's"), ("title = '", "two\nlines"),
                           ("title = '''", "a ''' b")):
            try:
                ST._toml_escape(title, head, text)
            except ST.EditRefused:
                pass
            else:
                raise AssertionError((head, text))


# --------------------------------------------------------------------------
# the number gate

def test_a_new_typed_number_is_flagged_and_a_kept_one_is_not():
    with _sources():
        s = EM.Session()
        b = _first(s, "docs-public/methodology.md")
        assert s.new_numbers(b, b["text"]) == [], "the unedited block flags nothing"
        new = b["text"] + " The count was 4,321 votes."
        flagged = [h["value"] for h in s.new_numbers(b, new)]
        assert flagged == ["4,321"], flagged
        ok, out = s.save(b["id"], new)
        assert ok and out["numbers"] == ["4,321"]
        review = s.review()
        assert not review["can_apply"], "Apply must wait for the typed number"
        ok, out = s.apply()
        assert not ok and "Apply waits" in out["problems"][0], out
        # removing it clears the gate; the detector goes quiet
        ok, out = s.resolve(b["id"], "4,321", "remove")
        assert ok and out["numbers"] == [], out
        assert s.review()["can_apply"]


def test_make_it_a_token_and_register_it_clear_the_number():
    with _sources() as tmp:
        s = EM.Session()
        b = _first(s, "docs-public/methodology.md")
        shown = s.displays()["n_draws"]
        ok, _ = s.save(b["id"], b["text"] + f" We ran {shown} simulations.")
        assert [n["value"] for n in s.review()["edits"][0]["numbers"]] == [shown]
        cands = s.review()["edits"][0]["numbers"][0]["candidates"]
        assert "n_draws" in [c["name"] for c in cands], cands
        ok, out = s.resolve(b["id"], shown, "token", "n_draws")
        assert ok and out["numbers"] == [], out
        assert s.pending[b["id"]]["text"].endswith("We ran {{n_draws}} simulations.")
        assert s.review()["can_apply"]
        # a name the registry does not define is refused
        ok, out = s.resolve(b["id"], shown, "token", "no_such_token")
        assert not ok
        # register: a second number, given a source, clears. The entry is
        # held with the edit: shown in the review's diff, written only at
        # Apply, dropped by Discard or by an edit that loses its words.
        real = (ROOT / "content/joburg/stats.toml").read_bytes()
        registry = tmp / "content/joburg/stats.toml"
        before = registry.read_bytes()
        src = "the council's own minutes, 2025"
        text = b["text"] + " The council met 17 times."
        s.save(b["id"], text)
        assert [n["value"] for n in s.review()["edits"][0]["numbers"]] == ["17"]
        ok, out = s.register(b["id"], "17", "met 17 times", "", "history")
        assert not ok, "a registration without a source is refused"
        ok, out = s.register(b["id"], "17", "met 17 times", src, "history")
        assert ok, out
        assert registry.read_bytes() == before, "register writes nothing before Apply"
        review = s.review()
        assert review["edits"][0]["numbers"] == [] and review["can_apply"], review
        assert "+[[audit.fixed]]" in review["diff"] and '+value = "17"' in review["diff"]
        s.save(b["id"], text.replace("met 17 times", "sat 17 times"))
        assert [n["value"] for n in s.review()["edits"][0]["numbers"]] == ["17"]
        assert s.registered == {}, "an edit that loses the entry's words drops it"
        s.save(b["id"], text)
        s.register(b["id"], "17", "met 17 times", src, "history")
        s.discard(b["id"])
        assert s.registered == {} and s.review()["diff"] == ""
        assert registry.read_bytes() == before, "Discard writes nothing"
        s.save(b["id"], text)
        s.register(b["id"], "17", "met 17 times", src, "history")
        assert s.review()["can_apply"], s.review()
        ok, out = s.apply()
        assert ok, out
        assert "content/joburg/stats.toml" in out["written"], out["written"]
        after = registry.read_text(encoding="utf-8")
        assert after.startswith(before.decode().rstrip("\n")) and 'value = "17"' in after
        assert s.registered == {} and s.review()["edits"] == []
        assert (ROOT / "content/joburg/stats.toml").read_bytes() == real


# --------------------------------------------------------------------------
# apply

def test_apply_writes_each_edit_to_its_own_source_and_nothing_else():
    with _sources() as tmp:
        files = {p: p.read_bytes() for p in tmp.rglob("*") if p.is_file()}
        s = EM.Session()
        html = _first(s, "forecast-sheet.html", "{{")
        md = _first(s, "docs-public/about-the-model.md")
        art = _first(s, "content/joburg/articles.toml")
        words = html["text"].split(" ")
        k = next(i for i, w in enumerate(words) if w.isalpha() and len(w) > 3)
        edits = {html["id"]: " ".join(words[:k] + ["EDITED"] + words[k + 1:]),
                 md["id"]: md["text"] + " EDITED.",
                 art["id"]: art["text"] + " EDITED."}
        for i, t in edits.items():
            assert s.save(i, t)[0], i
        ok, out = s.apply()
        assert ok, out
        assert sorted(out["written"]) == sorted({"forecast-sheet.html",
                                                  "docs-public/about-the-model.md",
                                                  "content/joburg/articles.toml"})
        changed = sorted(p.relative_to(tmp).as_posix() for p in files
                         if p.read_bytes() != files[p])
        assert changed == sorted(out["written"]), changed
        # one line changed in the HTML: the file's wrapping is kept
        diff = [ln for ln in out["diff"].splitlines()
                if ln.startswith(("+", "-")) and not ln.startswith(("+++", "---"))
                and "forecast-sheet" not in ln]
        sheet_old = files[tmp / "forecast-sheet.html"].decode().splitlines()
        sheet_new = (tmp / "forecast-sheet.html").read_text(encoding="utf-8").splitlines()
        assert len(sheet_old) == len(sheet_new)
        assert sum(a != b for a, b in zip(sheet_old, sheet_new)) == 1, diff
        # the sources now offer the edited words, and nothing is pending
        texts = {b["text"] for b in ST.blocks()}
        assert all(t in texts for t in edits.values())
        assert s.pending == {}


def test_rewrap_keeps_the_files_line_breaks():
    orig = "\n    The largest party is a near tie, where\n    on 8 August the DA led.\n  "
    same = re.sub(r"\s+", " ", orig).strip()
    assert ST.rewrap(orig, same) == orig, "an unedited block is written back unchanged"
    out = ST.rewrap(orig, same.replace("a near tie", "too close to call"))
    assert out == orig.replace("a near tie", "too close to call")


# --------------------------------------------------------------------------
# matching the built page to its sources

def test_a_built_element_is_tagged_with_its_source_block():
    md = _block("Each **simulation** draws {{n_draws}} times.", "docs-public/x.md")
    md["id"] = "m1"
    html = _block("The <em>largest</em> party.")
    html["id"] = "h1"
    index = {EM.block_signature(md): ["m1"], EM.block_signature(html): ["h1"]}
    page = ('<html><head><title>t</title></head><body><div class="wrap">'
            '<p>Each <strong>simulation</strong> draws <span class="mstat" '
            'data-token="n_draws" data-prov="x">5,000</span> times.</p>'
            '<h2><span>The <em>largest</em> party.</span></h2>'
            '<p>Words written by a script.</p></div></body></html>')
    out, tagged = EM.annotate(page, index)
    assert tagged == {"m1", "h1"}
    assert '<p data-edit-block="m1">Each' in out, out
    assert '<h2 data-edit-block="h1">' in out, "the block element carries it, not the inline"
    assert out.count(EM.BLOCK_ATTR) == 2
    # a page that cannot show a block does not tag it
    _out, tagged = EM.annotate(page, index, allowed={"h1"})
    assert tagged == {"h1"}


def test_every_generated_region_is_masked_and_every_page_cut_is_not():
    """Population: every marker pair in the HTML sources, by name. Each is
    either a page cut (`build_site.ARTEFACTS`) or masked; nothing else."""
    for rel in ST.HTML_SOURCES:
        body = (ROOT / rel).read_text(encoding="utf-8")
        names = set(re.findall(r"<!-- __([A-Z_]+?)_START__ -->", body))
        masked = {m.group(1) for m in ST.GENERATED.finditer(body)}
        outer = names - ST.CUT_KINDS
        assert names and outer, rel
        # a region nested in a masked one is masked with it
        blanked = ST._blank_generated(body)
        assert not (set(re.findall(r"__([A-Z_]+?)_START__", blanked)) - ST.CUT_KINDS), rel
        assert not (masked & ST.CUT_KINDS), rel


# --------------------------------------------------------------------------
# never on the public site

def test_the_overlay_never_reaches_a_site():
    import site_assets
    root = Path(tempfile.mkdtemp())
    try:
        site_assets.write(root)
        for rel in ("index.html", "play/index.html"):
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text("<html><head></head><body><p>x</p></body></html>",
                                    encoding="utf-8")
        pages, problems = EM.shipped(root)
        assert pages == ["index.html", "play/index.html"], pages
        assert problems == [], "the build's own assets carry no overlay"
        plants = {
            "js/edit-mode.js": None,
            "css/edit-mode.css": None,
            "play/index.html": f'<html><head><script src="{EM.URL_PREFIX}edit-mode.js"></script></head></html>',
            "index.html": f'<html><body><p {EM.BLOCK_ATTR}="ab12">x</p></body></html>',
        }
        for rel, text in plants.items():
            f = root / rel
            saved = f.read_bytes() if f.exists() else None
            f.write_text(text or "x", encoding="utf-8")
            problems = EM.shipped(root)[1]
            assert len(problems) == 1 and problems[0].startswith(rel), (rel, problems)
            if saved is None:
                f.unlink()
            else:
                f.write_bytes(saved)
            assert EM.shipped(root)[1] == [], rel
    finally:
        shutil.rmtree(root)
    # and the real build: every page scanned (two-sided), none carries it
    import build_site as B
    pages, problems = EM.shipped(ROOT / "site")
    expected = {spec[0] for spec in B.DOCS.values()} | set(B.ARTEFACTS) | {"portal.html"}
    import build_your_forecast
    import og_pages
    expected |= {build_your_forecast.YF_PAGE}
    # each claim's own page (build_site.claim_pages), one per claims.toml entry
    expected |= {f"{og_pages.CLAIM_DIR}/{c['slug']}.html" for c in B.load_claims()}
    assert expected <= set(pages) and len(pages) <= len(expected) + 2, pages
    assert problems == [], problems


def test_deploy_check_refuses_a_site_carrying_the_overlay():
    import deploy_check
    root = Path(tempfile.mkdtemp())
    try:
        (root / "index.html").write_text("<html><body><p>x</p></body></html>", encoding="utf-8")
        review = root / "REVIEW.md"
        review.write_text("<!-- built-pages: index.html=0 blocking=0 -->\n", encoding="utf-8")
        mine = lambda: [p for p in deploy_check.check("joburg", root, True, review)  # noqa: E731
                        if "edit-mode" in p]
        assert mine() == []
        (root / "edit-mode.js").write_text("x", encoding="utf-8")
        assert len(mine()) == 1, deploy_check.check("joburg", root, True, review)
        (root / "edit-mode.js").unlink()
        assert mine() == []
    finally:
        shutil.rmtree(root)


def test_a_relative_or_symlinked_site_path_is_resolved():
    """Register walks the site for the pages a block is on. A relative or
    symlinked --site (`/tmp` is one on macOS) must compare with the resolved
    paths the pages are keyed by."""
    real = Path(tempfile.mkdtemp()).resolve()
    link = real.parent / (real.name + "-link")
    try:
        (real / "about.html").write_text("<html><body><p>x</p></body></html>",
                                         encoding="utf-8")
        link.symlink_to(real)
        with _sources():
            for site in (Path(os.path.relpath(real)), Path(os.path.relpath(link)), link):
                s = EM.Session(site)
                assert s.site == real, site
                assert s.pages_of("nothing") == [], site
    finally:
        link.unlink(missing_ok=True)
        shutil.rmtree(real)


class _NoSession:
    lock = threading.RLock()

    def refresh(self):
        pass


def _post(body: bytes, path: str = "/__edit/api/nothing", **headers) -> int:
    """The status the handler gives a POST, without a socket. ``headers``
    override the defaults (underscores for hyphens; None removes one)."""
    h = EM.Handler.__new__(EM.Handler)
    h.client_address, h.port, h.path = ("127.0.0.1", 50000), EM.PORT, path
    sent = {"Host": f"127.0.0.1:{EM.PORT}", "X-Edit-Mode": "1",
            "Content-Type": "application/json", "Content-Length": str(len(body))}
    sent.update({k.replace("_", "-"): v for k, v in headers.items()})
    h.headers = email.message.Message()
    for k, v in sent.items():
        if v is not None:
            h.headers[k] = v
    h.rfile, h.session, status = io.BytesIO(body), _NoSession(), []
    h._json = lambda code, obj: status.append(code)
    h.send_error = lambda code, msg=None: status.append(code)
    h.do_POST()
    return status[0]


def test_a_write_needs_the_pages_own_request():
    """Each POST guard refuses on its own, and the control request that
    passes them all reaches the router (404: no such endpoint)."""
    good = b'{"id": "x"}'
    assert _post(good) == 404, "the control request passes every guard"
    assert _post(good, X_Edit_Mode=None) == 403, "no custom header"
    assert _post(good, Sec_Fetch_Site="cross-site") == 403, "a cross-site request"
    assert _post(good, Content_Type="text/plain") == 403, "a body a form can send"
    assert _post(b"not json") == 400
    for body in (b"[1]", b'"x"', b'{"id": 1}', b'{"id": "x", "text": 5}'):
        assert _post(body, path="/__edit/api/save") == 400, body


def test_the_server_answers_this_machine_only():
    def refused(client, host, port=EM.PORT):
        h = EM.Handler.__new__(EM.Handler)
        h.client_address, h.port = (client, 50000), port
        h.headers = email.message.Message()
        h.headers["Host"] = host
        sent = []
        h.send_error = lambda code, msg=None: sent.append(code)
        return h._refuse(), sent
    assert refused("127.0.0.1", f"127.0.0.1:{EM.PORT}") == (False, [])
    assert refused("127.0.0.1", f"localhost:{EM.PORT}") == (False, [])
    assert refused("10.10.10.3", f"127.0.0.1:{EM.PORT}")[0], "a client on another machine"
    assert refused("127.0.0.1", f"evil.example:{EM.PORT}")[0], "a rebound DNS name"
    site = Path(tempfile.mkdtemp())
    try:
        (site / "forecast.html").write_text("x", encoding="utf-8")
        (site / "play").mkdir()
        (site / "play" / "index.html").write_text("x", encoding="utf-8")
        assert EM.resolve_path(site, "/forecast").name == "forecast.html"
        assert EM.resolve_path(site, "/play/").as_posix().endswith("play/index.html")
        assert EM.resolve_path(site, "/../README.md") is None
        assert EM.resolve_path(site, "/%2e%2e/README.md") is None
    finally:
        shutil.rmtree(site)


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
