"""`_headers` serves every file with its own Content-Type (blind review B1,
2026-09-30).

The blanket `/*` rule that serves extensionless pages as UTF-8 HTML also matched
every asset, so `.js` modules, `.bin` draws and `.py` files went out as
text/html and ES modules refused to run. `build_site.headers_text()` now
detaches that type per extension.

The check here is an EMULATION of Cloudflare's matcher run over the file's
text, not a read-back of `build_site.CONTENT_TYPES`: a splat matches greedily,
every matching rule applies, a header two rules set is comma-joined, and
`! Name` removes the value a more pervasive rule set (developers.cloudflare.com
/workers/static-assets/headers/). The expected type comes from Python's
`mimetypes`, which knows nothing of this repository.
"""
from __future__ import annotations

import mimetypes
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import build_site as B  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
HTML = "text/html"


def _rules(text: str) -> list[tuple[str, list[tuple[str, str | None]]]]:
    rules: list[tuple[str, list[tuple[str, str | None]]]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        if not line[0].isspace():
            rules.append((line.strip(), []))
            continue
        op = line.strip()
        if op.startswith("! "):
            rules[-1][1].append((op[2:].strip().lower(), None))
        else:
            name, value = op.split(":", 1)
            rules[-1][1].append((name.strip().lower(), value.strip()))
    return rules


def _pattern(p: str) -> re.Pattern:
    assert p.count("*") <= 1, f"Cloudflare allows one splat per rule: {p}"
    out = re.escape(p).replace(r"\*", ".*")
    out = re.sub(r":[A-Za-z]\w*", "[^/]+", out)
    return re.compile(out)


def _served(path: str, text: str) -> tuple[str | None, int]:
    """``(Content-Type, number of non-blanket rules that set it)`` for a URL path."""
    values: list[tuple[int, str]] = []
    detached: set[int] = set()
    for i, (pat, ops) in enumerate(_rules(text)):
        if not _pattern(pat).fullmatch(path):
            continue
        for name, value in ops:
            if name != "content-type":
                continue
            if value is None:
                detached.add(i)
            else:
                values.append((i, value))
    if detached:
        values = [(i, v) for i, v in values if i in detached]
    setters = sum(1 for i, _ in values if _rules(text)[i][0] != "/*")
    return (", ".join(v for _, v in values) or None), setters


def _problems(site: Path, text: str) -> list[str]:
    """Every file under ``site`` that would be served with the wrong type."""
    out = []
    for dirpath, _dirs, files in os.walk(site):
        for name in files:
            rel = (Path(dirpath) / name).relative_to(site).as_posix()
            # consumed by Cloudflare / wrangler, never served
            if rel in ("_headers", ".assetsignore"):
                continue
            ctype, setters = _served("/" + rel, text)
            want = HTML if rel.endswith(".html") else mimetypes.guess_type(name)[0]
            if want is None:
                out.append(f"/{rel}: no known type for this extension")
                continue
            got = (ctype or "").split(";")[0].strip()
            if got != want:
                out.append(f"/{rel}: served as {ctype!r}, is {want}")
            if want == HTML and setters:
                out.append(f"/{rel}: a page matched {setters} non-HTML rule(s)")
            if want != HTML and setters != 1:
                out.append(f"/{rel}: {setters} non-HTML rules set its type")
    return out


#: The files the spec names (SPEC-v2 Lane G) and those already served.
CONSTRUCTED = ["index.html", "play/index.html", "f/index.html",
               "draws/index.json", "draws/base.bin", "draws/w_bye-0/manifest.json",
               "draws/w_bye-0/base.bin", "py/reweight.py", "py/manifest.json",
               "js/model.js", "play/js/worker.mjs", "pyodide/pyodide.asm.wasm",
               "css/interactive.css", "logos/ANC.png", "share.jpg", "robots.txt",
               "changes.json", "icon.svg"]


def _tree(tmp: Path, files) -> Path:
    for rel in files:
        (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp / rel).write_bytes(b"x")
    return tmp


def test_the_oracle_knows_every_type_the_spec_names():
    # mimetypes is the independent expectation; check it says what we think
    for ext, want in ((".py", "text/x-python"), (".mjs", "text/javascript"),
                      (".js", "text/javascript"), (".wasm", "application/wasm"),
                      (".bin", "application/octet-stream"), (".json", "application/json")):
        assert mimetypes.guess_type("x" + ext)[0] == want, ext


def test_every_constructed_file_is_served_as_its_own_type():
    with tempfile.TemporaryDirectory() as t:
        site = _tree(Path(t), CONSTRUCTED)
        assert _problems(site, B.headers_text()) == []
    # pages have no extension in their URL and must stay HTML
    for path in ("/", "/forecast", "/play/", "/dev/forecast"):
        ctype, setters = _served(path, B.headers_text())
        assert ctype == "text/html; charset=utf-8" and setters == 0, (path, ctype)


def test_every_file_under_the_served_site_matches_one_non_html_rule():
    site = ROOT / "site"
    population = [p for p in site.rglob("*") if p.is_file() and p.name != "_headers"]
    if not population:
        print("SKIP: site/ holds no files in this checkout")
        return
    # it looked: the assets the site ships today are in the population
    exts = {p.suffix for p in population}
    assert ".html" in exts and exts - {".html"}, exts
    assert _problems(site, B.headers_text()) == []
    # ...and the file that SHIPS is that one (deploy review F5: this test used
    # to check only the generator, and passed while site/_headers was stale).
    shipped = (site / "_headers").read_text(encoding="utf-8")
    assert _problems(site, shipped) == [], "site/_headers is stale; regenerate it"


def test_the_check_can_see_a_missing_type_and_an_overlapping_rule():
    with tempfile.TemporaryDirectory() as t:
        site = _tree(Path(t), CONSTRUCTED + ["draws/extra.qqq"])
        found = _problems(site, B.headers_text())
        assert found == ["/draws/extra.qqq: no known type for this extension"], found
        (site / "draws/extra.qqq").unlink()
        (site / "draws/cells.csv").write_bytes(b"x")
        found = _problems(site, B.headers_text())
        assert found and found[0].startswith("/draws/cells.csv: served as 'text/html"), found
        (site / "draws/cells.csv").unlink()
        assert _problems(site, B.headers_text()) == []
        # a directory rule beside an extension rule comma-joins the header
        overlapping = B.headers_text() + ("/draws/*\n  ! Content-Type\n"
                                          "  Content-Type: application/octet-stream\n")
        found = _problems(site, overlapping)
        assert any("draws/index.json" in f and "2 non-HTML rules" in f for f in found), found
        # the old file, the defect B1 names, is caught
        old = ("/*\n  Content-Type: text/html; charset=utf-8\n"
               "/share.jpg\n  ! Content-Type\n  Content-Type: image/jpeg\n")
        assert any(f.startswith("/js/model.js: served as 'text/html")
                   for f in _problems(site, old))
