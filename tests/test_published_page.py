"""CLASS: THE PAGE ON DISK IS NOT THE MODEL, AND NOTHING WAS ASKING.

Every guard this repository has about published figures asks a question about
the REGISTRY or about the BUILD. `stats.audit` asks whether a figure reached the
reader unsourced. `orphaned_scenario_claims` asks whether a pinned claim names a
lever that is gone. `freshness_problems` asks whether the file under a live
token is older than the reference run. All three fire during a build.

None of them looks at the bytes that are actually being served, and a build that
never completes never runs any of them.

That is the whole defect. `site/index.html` said the DA finishes first **87%**
of the time for ELEVEN DAYS after the model settled on **71%**:

    site/index.html                        2026-08-17 13:56   what was served
    forecast-sheet.html (its own source)   2026-08-22 11:23   +5 days
    data/processed/forecast_summary.json   2026-08-28 04:23   +11 days

The page predated its own source by five days and the run by eleven. The cause
was not a missing guard — it was a working one. `build_site.py` has been exiting
1 since 17 August (ten claims orphaned to the deleted `turnout_tilt_da`, plus
`regime_cap_summary.json` older than the reference run), so every rebuild
refused, the last successful build's output stayed on disk, and the refusal was
invisible because a refusal that happens every day reads as the weather.

So these tests ask the only question nothing else asks: **does the artefact on
disk agree with the model on disk, right now?**

    T1  every `mode="free"` span on every built page re-resolves to what it
        renders. This is the test that catches the 87%.
    T6  the committed pages are byte-for-byte what this tree builds today, with
        no escape-hatch flags. Two failures, two messages: the build refuses at
        all, or it builds and the bytes differ.
    T7  no pinned token is "drift-checked against nothing". Twenty-four of
        twenty-four are today, and `drift_report` has therefore printed "no
        drift" on every build of its life without ever having been able to find
        any.

⚠️ THESE TESTS READ THE REAL `site/*.html`, THE REAL `content/joburg/stats.toml`
AND THE REAL `data/processed`. They run the production resolver over production
artefacts; the one synthetic input in the module is a planted mismatch used to
prove the comparison FIRES, and it is a mutation of the real page, paired with a
positive assertion that the real page was examined. A check that has never been
shown to fail, and a check whose only subject is a fixture, are the same thing.

⚠️ `skip` IS LEGAL ONLY WHEN `site/index.html` IS ABSENT. Staleness is a
failure. A stale page that skips is the state this module exists to end.

They do not run the model. The whole module is well under a second: the build is
~0.2s and everything else is reading JSON and HTML.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import sys
import tempfile
from datetime import datetime
from difflib import unified_diff
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, skip  # noqa: E402

import build_site  # noqa: E402
import stats as statlib  # noqa: E402

SITE = ROOT / "site"
PROCESSED = ROOT / "data" / "processed"
REGISTRY_PATH = ROOT / "content" / "joburg" / "stats.toml"
LANDING = SITE / "index.html"

# `_span` writes a fixed attribute order and escapes everything that could
# close the tag early, so the shape is stable. Anchored on class="mstat" so a
# `.stat` headline tile (a different class, deliberately — see stats.STAT_CSS)
# can never be mistaken for a sourced figure.
SPAN = re.compile(r'<span class="mstat"([^>]*)>(.*?)</span>', re.S)
ATTR = re.compile(r'([a-zA-Z-]+)="([^"]*)"')

# The ONE byte in a built page that is legitimately not a function of the tree:
# `render_doc` stamps the build date into the colophon. Normalised for the
# byte comparison and asserted on separately, because "the page was built on a
# different day" and "the page disagrees with the model" are different faults
# and only one of them is about the forecast.
BUILD_DATE = re.compile(r"(?i)(generated from [^<\n]{0,120}? on )(\d{4}-\d{2}-\d{2})")

# Pages this test module compares. Derived from `build_site` rather than
# retyped: a hand-kept second list is the duplication that let `plan.html` be
# served for weeks after no build produced it.
BUILT_PAGES = tuple(sorted(
    {spec[0] for spec in build_site.DOCS.values()} | set(build_site.ARTEFACTS.values())
))

# output page -> the file the build reads to produce it.
PAGE_INPUT = {spec[0]: ROOT / src for src, spec in build_site.DOCS.items()}
PAGE_INPUT.update({out: ROOT / src for src, out in build_site.ARTEFACTS.items()})


# --------------------------------------------------------------------------
# reading what is on disk
# --------------------------------------------------------------------------

def _stamp(path: Path) -> str:
    if not path.exists():
        return f"{path} (absent)"
    when = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        rel = path
    return f"{rel} {when}"


def _spans(html: str) -> list[dict]:
    """Every provenance span on a page, with its attributes and its glyph."""
    out = []
    for match in SPAN.finditer(html):
        attrs = dict(ATTR.findall(match.group(1)))
        attrs["rendered"] = unescape(match.group(2))
        out.append(attrs)
    return out


def _entries(registry: dict) -> dict:
    """Token entries only — the registry also carries the `[audit]` block."""
    return {name: entry for name, entry in registry.items()
            if isinstance(entry, dict) and "mode" in entry}


def _registry() -> dict:
    # `load_registry` prints the orphan warning; it is build output, not test
    # output, and the orphans have their own assertion in T6.
    with contextlib.redirect_stdout(io.StringIO()):
        return _entries(statlib.load_registry(REGISTRY_PATH))


def _backing(source: str, ctx: dict) -> Path:
    """The FILE a source resolves out of — the third timestamp that matters."""
    prefix = ":".join(source.split(":")[:2])
    if prefix in (ctx.get("files") or {}):
        return Path(ctx["files"][prefix])
    if source.startswith("derived:"):
        return PROCESSED / "seat_draws.csv"
    return PROCESSED / statlib.REFERENCE_ARTEFACT


def _run_stamp() -> str:
    """When the reference run happened, by its own account if it has one.

    `_generated` was added to `forecast_summary.json` on 2026-08-30 and the
    artefact currently on disk predates it, so the mtime fallback is the live
    path today, not a theoretical one. It is labelled rather than silently
    substituted: mtime is a property of the filesystem, and `cp -p`, a restore
    or a `touch` all move it or fail to (stats.freshness_problems says the same
    thing at more length).
    """
    path = PROCESSED / statlib.REFERENCE_ARTEFACT
    if not path.exists():
        return "(no forecast_summary.json)"
    try:
        blob = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        blob = {}
    generated, draws = blob.get("_generated"), blob.get("_draws")
    if generated:
        return f"{generated} (self-declared _generated, {draws} draws)"
    return (f"{datetime.fromtimestamp(path.stat().st_mtime):%Y-%m-%d %H:%M} "
            f"(mtime — this artefact carries no _generated stamp)")


# --------------------------------------------------------------------------
# T1 — every live token on the page still says what the model says
# --------------------------------------------------------------------------

_GENERATED_NOW: dict | None = None


def generated_now() -> dict[str, str]:
    """Every generated token as `render_sheet.py` would render it TODAY.

    Generated figures carry their value inline and have no registry entry, so
    the registry cannot re-derive them. This does instead: regenerate the sheet
    into a scratch copy from the current `data/processed`, render it, and read
    the spans back. Nothing in the tree is written.
    """
    global _GENERATED_NOW
    if _GENERATED_NOW is None:
        import shutil
        import subprocess
        import tempfile
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            sheet = Path(tmp) / "forecast-sheet.html"
            shutil.copy(root / "forecast-sheet.html", sheet)
            r = subprocess.run([str(root / ".venv/bin/python"), str(root / "src/render_sheet.py"),
                                "--sheet", str(sheet)], capture_output=True, text=True, cwd=root)
            assert r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]
            text, _, _ = statlib.render(sheet.read_text(encoding="utf-8"), _registry(),
                                        statlib.load_context(PROCESSED))
        _GENERATED_NOW = {s.get("data-token", ""): s["rendered"] for s in _spans(text)
                          if s.get("data-mode") == "generated"}
    return _GENERATED_NOW


def live_token_faults(pages: dict[str, str], registry: dict,
                      ctx: dict) -> tuple[list[dict], int]:
    """Free spans whose rendered glyph is not what the model says now.

    Returns ``(faults, n_checked)``. **`n_checked` is not decoration.** A
    comparison that examined nothing returns no faults and reads exactly like a
    clean bill of health, which is how a scoring function in this repository
    raised on every input for its entire life.
    """
    faults: list[dict] = []
    checked = 0
    for page in sorted(pages):
        for span in _spans(pages[page]):
            if span.get("data-mode") == "generated":
                token = span.get("data-token", "")
                now = generated_now().get(token)
                checked += 1
                if now != span["rendered"]:
                    faults.append({"page": page, "token": token,
                                   "rendered": span["rendered"], "live": now,
                                   "source": "render_sheet.py, regenerated now",
                                   "used_in": "", "why": "moved" if now else "unresolvable"})
                continue
            if span.get("data-mode") != "free":
                continue
            token = span.get("data-token", "")
            entry = registry.get(token)
            if entry is None:
                faults.append({"page": page, "token": token,
                               "rendered": span["rendered"], "live": None,
                               "source": "(none — token not in the registry)",
                               "used_in": "", "why": "unregistered"})
                continue
            checked += 1
            source = entry.get("source", "")
            value = statlib.resolve(source, ctx)
            live = None if value is None else statlib._fmt(value, entry.get("format"))
            if live == span["rendered"]:
                continue
            faults.append({"page": page, "token": token,
                           "rendered": span["rendered"], "live": live,
                           "source": source, "used_in": entry.get("used_in", ""),
                           "why": "unresolvable" if live is None else "moved"})
    return faults, checked


def _fault_report(faults: list[dict], ctx: dict) -> str:
    out = [f"{len(faults)} live figure(s) on the published pages disagree with "
           f"the model in data/processed.", ""]
    for f in faults:
        page = SITE / f["page"]
        if f["why"] == "unregistered":
            out += [f"  ✗ {f['page']}  token {f['token']!r} renders "
                    f"{f['rendered']!r} and is NOT IN THE REGISTRY.",
                    "      Nothing can re-derive or drift-check it. It is a "
                    "number on a page with no source at all.", ""]
            continue
        verdict = ("the source no longer resolves at all — the build would "
                   "refuse, and this page is what it refused to replace"
                   if f["why"] == "unresolvable" else
                   f"the page says {f['rendered']!r}; the model says {f['live']!r}")
        out += [
            f"  ✗ {f['page']}  {f['token']}",
            f"      {verdict}",
            f"      source:   {f['source']}",
            f"      used_in:  {f['used_in'] or '(not recorded)'}",
            f"      page:     {_stamp(page)}",
            f"      its own build input: "
            f"{_stamp(PAGE_INPUT.get(f['page'], SITE / f['page']))}",
            f"      the model:{'':<1}{_stamp(_backing(f['source'], ctx))}",
            f"      the run:  {_run_stamp()}",
            "",
        ]
    out += [
        "  A `mode=\"free\"` span is the registry PROMISING the reader that the "
        "figure was recomputed this build. Each one above is that promise, "
        "broken, in published prose.",
        "  This does not mean the model is wrong and it does not mean the prose "
        "is wrong. It means the page is not the model's. Rebuild it — and if "
        "`build_site.py` refuses, the refusal is the actual defect and is what "
        "has to be cleared. See test_the_published_pages_are_what_this_tree_"
        "builds_today.",
    ]
    return "\n".join(out)


def test_every_live_figure_on_a_published_page_is_what_the_model_says_now():
    """THE DEFECT. 87% served for eleven days against a model saying 71%."""
    if not LANDING.exists():
        skip("site/index.html is absent — nothing has been built to check")
    registry = _registry()
    ctx = statlib.load_context(PROCESSED)
    pages = {p.name: p.read_text(encoding="utf-8")
             for p in sorted(SITE.glob("*.html"))}
    faults, checked = live_token_faults(pages, registry, ctx)
    assert checked, (
        "no `mode=\"free\"` span was found on any page in site/. This check "
        "then examined nothing and would pass over any figure whatsoever. "
        f"Pages read: {sorted(pages)}")
    assert not faults, "\n" + _fault_report(faults, ctx)


def test_the_live_figure_check_fires_when_a_page_disagrees():
    """The negative case, on the REAL page with one glyph moved.

    Paired with the positive assertion above, deliberately: the positive test
    proves the comparison ran over production bytes, and this proves it can
    fail. Neither is sufficient alone — a fixture proves mechanism, never
    magnitude, and this repository has three toy-derived claims that died on
    the panel in one session to say so.
    """
    if not LANDING.exists():
        skip("site/index.html is absent — nothing has been built to check")
    registry = _registry()
    ctx = statlib.load_context(PROCESSED)
    original = LANDING.read_text(encoding="utf-8")

    victim = next((s for s in _spans(original)
                   if s.get("data-mode") == "free"
                   and s.get("data-token") in registry
                   and statlib.resolve(registry[s["data-token"]].get("source", ""),
                                       ctx) is not None), None)
    assert victim is not None, (
        "site/index.html carries no resolvable free span, so the planted "
        "mismatch has nothing to plant against")

    good = f'data-token="{victim["data-token"]}"'
    start = original.index(good)
    open_end = original.index(">", start)
    close = original.index("</span>", open_end)
    planted = (original[:open_end + 1] + "NOT-WHAT-THE-MODEL-SAYS"
               + original[close:])

    faults, checked = live_token_faults({"index.html": planted}, registry, ctx)
    assert checked, "the planted page yielded no free spans to check"
    hit = [f for f in faults if f["token"] == victim["data-token"]
           and f["rendered"] == "NOT-WHAT-THE-MODEL-SAYS"]
    assert hit, (f"a planted mismatch on {victim['data-token']!r} was not "
                 f"reported. Faults seen: {faults}")
    report = _fault_report(hit, ctx)
    for needed in (victim["data-token"], "NOT-WHAT-THE-MODEL-SAYS",
                   "source:", "used_in:", "the run:"):
        assert needed in report, f"{needed!r} missing from:\n{report}"


# --------------------------------------------------------------------------
# T6 — the published pages are what this tree builds today
# --------------------------------------------------------------------------

_STRIP = re.compile(r"<(script|style|svg)\b[^>]*>.*?</\1>", re.S | re.I)
_TAGS = re.compile(r"<[^>]+>")


def _visible(html: str) -> list[str]:
    """Reader-visible prose, one fragment per line.

    ⛔ NEVER DIFF THE RAW HTML. The map block alone carries 225 percentages
    and tens of KB of SVG path data whose `<defs>` come out in dictionary
    order, and index.html is one enormous line per section. Measured on the
    real pages today: a raw unified diff of served-against-built index.html is
    177,077 characters with a single line of 82,866, and the same diff of
    visible text is 865 characters. That is 205x, and the difference between a
    reader who sees `-87% / +71%` and one who sees `patternTransform`.

    Scripts, styles and SVG go; entities are unescaped so an em-dash compares
    as an em-dash on both sides.
    """
    body = _STRIP.sub(" ", html)
    body = _TAGS.sub("\n", body)
    return [line for line in (l.strip() for l in unescape(body).splitlines())
            if line]


def _token_map(html: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for span in _spans(html):
        out.setdefault(span.get("data-token", "?"), []).append(span["rendered"])
    return out


def _token_diff(old: str, new: str) -> list[str]:
    a, b = _token_map(old), _token_map(new)
    lines = []
    for token in sorted(set(a) | set(b)):
        if a.get(token) == b.get(token):
            continue
        if token not in a:
            lines.append(f"      + {token}: {b[token]}  (new on the page)")
        elif token not in b:
            lines.append(f"      - {token}: {a[token]}  (gone from the page)")
        else:
            lines.append(f"      ~ {token}: served {a[token]} -> builds {b[token]}")
    return lines


def _build_to(out: Path) -> tuple[int | str | None, str]:
    """Run the real build with NO escape hatches. Returns (exit code, output)."""
    buf = io.StringIO()
    code: int | str | None = 0
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            code = build_site.main(["--out", str(out)])
    except SystemExit as exc:
        code = exc.code
    return code, buf.getvalue()


def _normalise(html: str) -> str:
    """Byte comparison, minus the one byte that is a function of the clock.

    `render_doc` stamps `date.today()` into the colophon of each rendered
    document. That is the ONLY intentional non-determinism in the build, and
    normalising it is what stops this test failing every day for a reason that
    has nothing to do with the forecast — a test that always fails is a test
    that is always ignored, which is precisely how an exit-1 build survived
    eleven days. The stamp is not thereby unchecked: it is the subject of
    `test_no_published_page_reports_a_build_older_than_the_run_it_quotes`.
    """
    return BUILD_DATE.sub(r"\g<1>YYYY-MM-DD", html)


def test_the_page_diff_is_readable_and_names_the_token_first():
    """The (b) branch's machinery, exercised on the REAL served bytes.

    Branch (b) of the byte comparison is unreachable while the build refuses,
    and an unreachable failure message is an unwritten one — this repository
    has a scoring function that raised on every input for its whole life
    because nothing ever exercised it. So the diff renderers are asserted here
    against production HTML: `site/index.html` as served, against the very
    bytes the (refused) build wrote for it.

    ⛔ It asserts NOTHING about whether the pages agree. That is T1 and T6.

    **AND ON A FRESH TREE IT USED TO ASSERT NOTHING AT ALL.** It returned at
    the `_normalise(old) == _normalise(new)` line — which on 2026-08-31 was not
    merely normalise-equal but BYTE-equal — so the only assertion that ever
    executed was `fresh.exists()`, and every diff renderer below it was
    unreached. That is precisely the failure the docstring above describes
    happening to a scoring function, reproduced in the test written to prevent
    it: a fresh tree is the NORMAL state of this repository, so the normal
    state was zero coverage. **The divergence is now CONSTRUCTED when the tree
    does not supply one**, which is CLAUDE.md's third requirement — a test
    whose premise is a passing state of the tree expires silently.
    """
    if not LANDING.exists():
        skip("site/index.html is absent — nothing has been built to check")
    with tempfile.TemporaryDirectory() as tmp:
        fresh = Path(tmp) / "index.html"
        _build_to(Path(tmp))
        assert fresh.exists(), (
            "the build wrote no index.html at all, even before its refusal — "
            "the diff machinery has nothing to run on")
        old = LANDING.read_text(encoding="utf-8")
        new = fresh.read_text(encoding="utf-8")
        constructed = False
        if _normalise(old) == _normalise(new):
            # Move ONE free token's rendered glyph, which is exactly the shape
            # branch (b) exists to report, and carry on into the renderers.
            spans = [s for s in _spans(old) if s.get("data-mode") == "free"]
            assert spans, (
                "site/index.html carries no free stat token, so no divergence "
                "of the shape this test reports can be constructed and the "
                "diff renderers below have never been executed on anything.")
            victim = spans[0]
            anchor = f'data-token="{victim["data-token"]}"'
            start = old.index(">", old.index(anchor)) + 1
            end = old.index("</span>", start)
            new = old[:start] + "MOVED-FOR-THE-DIFF-TEST" + old[end:]
            constructed = True
            assert _normalise(old) != _normalise(new), (
                "the constructed divergence survived normalisation, so this "
                "test still runs the renderers on nothing")

        tokens = _token_diff(old, new)
        prose = list(unified_diff(_visible(old), _visible(new), lineterm="", n=1))
        raw = list(unified_diff(old.splitlines(), new.splitlines(),
                                lineterm="", n=1))
        assert tokens or prose, (
            "the pages differ byte-for-byte but neither the token diff nor the "
            "visible-text diff shows anything. The difference is invisible to "
            "the reader of this failure, which is the same as no report.")
        raw_chars = sum(len(line) for line in raw)
        prose_chars = sum(len(line) for line in prose)
        assert prose_chars <= max(4000, raw_chars), (
            f"the visible-text diff ({prose_chars} chars) is no smaller than "
            f"the raw one ({raw_chars}). Something is leaking markup — check "
            "that <svg>, <script> and <style> are still being stripped.")
        assert not any(len(line) > 4000 for line in prose), (
            "a visible-text diff line runs past 4,000 characters, so a block "
            "of markup survived stripping. The whole point is that the reader "
            "can see which figure moved.")
        if constructed:
            # (2) IT CAN SEE. The divergence was planted on one named token, so
            # the token diff must NAME it — which is what "names the token
            # first" in this test's title actually claims and never checked.
            assert any(victim["data-token"] in line for line in tokens), (
                f"a free token's rendered figure was changed and the token "
                f"diff did not name {victim['data-token']!r}. It reported: "
                f"{tokens[:5]}")


def test_the_published_pages_are_what_this_tree_builds_today():
    """Build with no flags, compare bytes. Two faults, two messages."""
    if not LANDING.exists():
        skip("site/index.html is absent — nothing has been built to check")

    with tempfile.TemporaryDirectory() as tmp:
        fresh_dir = Path(tmp)
        code, output = _build_to(fresh_dir)

        # (a) THE BUILD REFUSES. This is not a precondition failure to be
        #     routed around — it IS the eleven-day defect. A refusing build
        #     leaves the last successful build's output on disk and serves it,
        #     and nothing downstream can tell.
        if code not in (0, None):
            raise AssertionError(
                "\n`build_site.py` REFUSES TO BUILD, so nothing can rebuild the "
                f"pages that are being served. Exit {code!r}.\n\n"
                + output.rstrip() + "\n\n"
                "  ⛔ DO NOT pass --allow-orphans or --allow-stale-sources to "
                "get this test green. Both flags publish exactly the class of "
                "figure this test exists to catch — a number that reads as "
                "current and cannot be re-derived or drift-checked — and using "
                "them here would make the test certify the defect.\n"
                "  Clear the refusal instead: re-capture or cut each orphaned "
                "claim, and re-run whatever writes the stale file.\n"
                "  Until it is cleared, every rebuild is a no-op and site/*.html "
                "keeps whatever it last had. For information, the pages this "
                "refused build DID write differ from the committed ones in: "
                + (", ".join(p for p in BUILT_PAGES
                             if (fresh_dir / p).exists() and (SITE / p).exists()
                             and _normalise((fresh_dir / p).read_text("utf-8"))
                             != _normalise((SITE / p).read_text("utf-8")))
                   or "(none)") + ".")

        # (b) IT BUILDS, AND THE BYTES DIFFER.
        differing = []
        for name in BUILT_PAGES:
            served, built = SITE / name, fresh_dir / name
            if not built.exists():
                differing.append((name, ["      (this build produced no such page)"],
                                  []))
                continue
            if not served.exists():
                differing.append((name, ["      (the page is not committed in site/)"],
                                  []))
                continue
            old_raw = served.read_text(encoding="utf-8")
            new_raw = built.read_text(encoding="utf-8")
            if _normalise(old_raw) == _normalise(new_raw):
                continue
            prose = list(unified_diff(_visible(old_raw), _visible(new_raw),
                                      fromfile=f"served site/{name}",
                                      tofile=f"built  {name}", lineterm="", n=1))
            differing.append((name, _token_diff(old_raw, new_raw), prose))

        if differing:
            out = ["", f"{len(differing)} published page(s) are NOT what this "
                       "tree builds today.", ""]
            for name, tokens, prose in differing:
                out.append(f"  ✗ site/{name}")
                out.append(f"      served: {_stamp(SITE / name)}")
                out.append(f"      its own build input: "
                           f"{_stamp(PAGE_INPUT.get(name, SITE / name))}")
                out.append(f"      the run: {_run_stamp()}")
                out.append("    -- tokens --")
                out += tokens or ["      (no token moved; the difference is prose)"]
                out.append("    -- visible text (tags, scripts and SVG removed) --")
                shown = prose[:60]
                out += [f"      {line}" for line in shown]
                if len(prose) > len(shown):
                    out.append(f"      … and {len(prose) - len(shown)} more lines")
                out.append("")
            out.append("  The committed page is what is served. Rebuild and "
                       "commit, or explain in the commit why the served bytes "
                       "should differ from what the tree produces.")
            raise AssertionError("\n".join(out))


def test_no_published_page_reports_a_build_older_than_the_run_it_quotes():
    """The colophon date against the run date — content, not mtime.

    This is the defect's own table, asserted: the served page said it was
    generated on 2026-08-17 while the run it quotes from is dated 2026-08-28.
    It reads the date out of the PAGE TEXT rather than off the filesystem
    deliberately — a fresh clone rewrites every tracked mtime to checkout time,
    so an mtime comparison between a tracked page and a tracked source proves
    nothing on a machine that is not this one. `data/processed` is gitignored,
    so the run artefact's mtime is genuine and is the fallback when the run
    carries no `_generated` of its own.
    """
    if not LANDING.exists():
        skip("site/index.html is absent — nothing has been built to check")
    run_path = PROCESSED / statlib.REFERENCE_ARTEFACT
    assert run_path.exists(), f"{run_path} is absent; there is no run to compare to"
    blob = json.loads(run_path.read_text(encoding="utf-8"))
    generated = blob.get("_generated")
    run_day = ((generated or "")[:10]
               or f"{datetime.fromtimestamp(run_path.stat().st_mtime):%Y-%m-%d}")

    behind = []
    checked = 0
    for name in BUILT_PAGES:
        page = SITE / name
        if not page.exists():
            continue
        match = BUILD_DATE.search(page.read_text(encoding="utf-8"))
        if match is None:
            continue          # index.html is copied verbatim and carries none
        checked += 1
        if match.group(2) < run_day:
            behind.append((name, match.group(2)))

    assert checked, (
        "no committed page carries a build-date colophon, so this check "
        "examined nothing. `render_doc` stamps one into every rendered "
        f"document; pages looked at: {[p for p in BUILT_PAGES]}")
    assert not behind, "\n" + "\n".join(
        [f"{len(behind)} published page(s) were built BEFORE the run they "
         f"present as current (run: {_run_stamp()}).", ""]
        + [f"  ✗ site/{name}  says it was generated {when}  "
           f"({_stamp(SITE / name)})" for name, when in behind]
        + ["", "  A page older than the run is not a formatting problem. Every "
              "live figure on it was resolved out of a model that has since "
              "moved, and the page states them in the present tense."])


# --------------------------------------------------------------------------
# T7 — a pinned token that is drift-checked against nothing
# --------------------------------------------------------------------------

UNVERIFIABLE = "unverifiable"
# ONE definition of "long enough to be a reason", shared with
# `stats.DECLARATION_MIN_CHARS`. It was a bare `12` here and a bare
# `12` there, for two different fields.
from stats import DECLARATION_MIN_CHARS  # noqa: E402


def test_no_pinned_token_is_drift_checked_against_nothing():
    """24 of 24 today, and `drift_report` has never had anything to report.

    A `mode="fixed"` token is trusted by construction: it renders its pinned
    value and the build reports DRIFT if the live value has moved away from it.
    That bargain is void when the source does not resolve — `run:` and
    `external:` sources never resolve by design — because `render` only ever
    appends a drift row inside `if live is not None`. So a pinned token with an
    unresolvable source is not "within tolerance". It is unmeasured, and the
    build's cheerful "no drift — every pinned stat is within tolerance" is not
    a finding but the absence of one.

    The fix is not to ban such tokens: `asa_2021_seats` is an IEC record and
    `claim_poll_base` is a published poll, and neither is a model output. The
    fix is that it must be SAID. `unverifiable = "<reason>"` on the entry is
    the declaration, and this test enforces set equality in both directions so
    a declaration cannot outlive the reason for it.
    """
    registry = _registry()
    ctx = statlib.load_context(PROCESSED)
    pinned = {n: e for n, e in registry.items() if e.get("mode") == "fixed"}
    assert pinned, (
        f"{REGISTRY_PATH} declares no pinned tokens at all, so this check "
        "examined nothing")

    unresolvable = {n for n, e in pinned.items()
                    if statlib.resolve(e.get("source", ""), ctx) is None}
    declared = {n for n, e in pinned.items()
                if str(e.get(UNVERIFIABLE, "")).strip()}
    malformed = sorted(n for n, e in pinned.items()
                       if UNVERIFIABLE in e
                       and len(str(e[UNVERIFIABLE]).strip()) < DECLARATION_MIN_CHARS)

    problems: list[str] = []
    undeclared = sorted(unresolvable - declared)
    if undeclared:
        problems += [
            f"{len(undeclared)} of {len(pinned)} pinned token(s) cannot be "
            "drift-checked and do not say so:", ""]
        problems += [f"  ✗ {n:<28s} source: {pinned[n].get('source', '')}"
                     f"{chr(10)}      used_in: "
                     f"{pinned[n].get('used_in') or '(not recorded)'}"
                     for n in undeclared]
        problems += [
            "", "  Each renders a pinned value that nothing re-derives, so its "
            "tolerance is decorative and `drift_report` will keep printing "
            "'no drift — every pinned stat is within tolerance' whatever the "
            "model does.",
            "  Either give it a source that resolves, or declare it:",
            '      unverifiable = "IEC 2021 result — an external fact, not a '
            'model output"',
            "  A declared one is still unchecked. The declaration only stops it "
            "being COUNTED as checked.", ""]

    stale = sorted(declared - unresolvable)
    if stale:
        problems += [
            f"{len(stale)} pinned token(s) declare `{UNVERIFIABLE}` but their "
            "source resolves now, so the declaration has outlived its reason:",
            ""]
        for n in stale:
            live = statlib.resolve(pinned[n].get("source", ""), ctx)
            problems += [
                f"  ✗ {n:<28s} source: {pinned[n].get('source', '')}",
                f"      resolves to {statlib._fmt(live, pinned[n].get('format'))!r}"
                f"; pinned at {pinned[n].get('value')!r}",
                f"      declared unverifiable because: "
                f"{pinned[n][UNVERIFIABLE]!r}"]
        problems += [
            "", "  Delete the declaration so the build drift-checks it again. A "
            "standing `unverifiable` on a resolvable source suppresses a real "
            "drift row, which is the failure mode inverted.", ""]

    if malformed:
        problems += [
            f"{len(malformed)} `{UNVERIFIABLE}` declaration(s) give no usable "
            f"reason: {', '.join(malformed)}",
            "  A reason is what a reviewer reads instead of re-deriving the "
            "number. `true`, `yes` and `''` are not reasons.", ""]

    assert not problems, "\n" + "\n".join(problems)


def test_a_free_token_may_not_declare_itself_unverifiable():
    """`free` means recomputed every build. There is nothing to excuse."""
    registry = _registry()
    offenders = sorted(n for n, e in registry.items()
                       if e.get("mode") != "fixed" and UNVERIFIABLE in e)
    assert not offenders, (
        f"\n{len(offenders)} `mode=\"free\"` token(s) declare "
        f"`{UNVERIFIABLE}`: {', '.join(offenders)}.\n"
        "  A free token that cannot resolve is a FATAL build error already "
        "(`render` appends it to `unresolved`, and `build_site` refuses rather "
        "than publish a silent blank). The declaration is meaningless there, "
        "and reads as an excuse that the build does not honour.")


def test_the_unverifiable_declaration_is_inert_to_the_build():
    """It must not change a rendered byte. A label, not a lever.

    Asserted rather than assumed: the day `unverifiable` starts suppressing a
    refusal, it becomes `--allow-orphans` spelled differently, and the whole
    point is that it declares an absence of checking instead of creating one.
    """
    registry_raw = _registry()
    ctx = statlib.load_context(PROCESSED)
    name = next((n for n, e in registry_raw.items() if e.get("mode") == "fixed"),
                None)
    assert name is not None, "no pinned token to test with"
    plain = {name: dict(registry_raw[name])}
    labelled = {name: {**registry_raw[name],
                       UNVERIFIABLE: "planted by the test suite, not a real reason"}}
    text = "{{" + name + "}}"
    assert statlib.render(text, plain, ctx) == statlib.render(text, labelled, ctx), (
        f"declaring {UNVERIFIABLE} changed what `stats.render` produced for "
        f"{name!r}. It is a label on a token that cannot be checked; it must "
        "never change a byte, a drift row or a refusal.")


def test_a_historical_claim_may_not_be_published_undated():
    """⛔ THE SOLE PROTECTION FOR THE TEN `turnout_tilt_da` CLAIMS, AND IT HAD NO TEST.

    `historical = "<reason>"` exempts a token from the orphan refusal because
    its mechanism is gone and nothing can re-derive it. The whole reason that is
    a discipline rather than `--allow-orphans` renamed is the other half of the
    bargain: the build REFUSES a historical token rendered outside a `data-asof`
    region, so declaring one obliges the prose to say when it was true.

    Deleting that refusal left **46 tests green** across all four modules that
    invoke `build_site` (verified in review, 2026-08-31). One untested line was
    the only thing standing between ten claims pinned to a deleted lever and
    undated republication.

    This constructs the violation rather than trusting the tree: a real
    registry, a real page, the claim NOT wrapped — and the build must refuse and
    name the token.
    """
    import subprocess
    import tempfile
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        undated = tmp / "undated.html"
        # the same token, in prose that does NOT date it
        undated.write_text(
            "<html><body><p>The DA falls short by {{claim_short_by}} "
            "seats.</p></body></html>", encoding="utf-8")
        out = subprocess.run(
            [str(root / ".venv/bin/python"), "-c",
             "import sys; sys.path.insert(0, 'src');\n"
             "import stats as S, cityconfig; from pathlib import Path;\n"
             "cityconfig.use('joburg');\n"
             "reg = S.load_registry(Path('content/joburg/stats.toml'));\n"
             "ctx = S.load_context(Path('data/processed'));\n"
             "rec = [];\n"
             f"S.render(open({str(undated)!r}).read(), reg, ctx, record=rec);\n"
             "bad = [r for r in rec if r.get('historical') and not r['dated']];\n"
             "print('UNDATED_HISTORICAL', [r['token'] for r in bad])"],
            capture_output=True, text=True, cwd=root)
        assert "UNDATED_HISTORICAL ['claim_short_by']" in out.stdout, (
            f"a token declared `historical` rendered in undated prose and was "
            f"not flagged. The declaration would then be a free pass: the "
            f"orphan refusal skipped, and nothing requiring the date that "
            f"skipping it was traded for.\n{out.stdout}\n{out.stderr}")


def test_a_malformed_dated_region_dates_NOTHING_and_says_so():
    """⛔ THE REGEX FAILED OPEN, WHICH IS THE ONE DIRECTION THAT MUST NOT HAPPEN.

    `dated_spans` was `<tag …data-asof…>.*?</tag>`, which is not an element.
    Verified in review: an **unclosed** dated tag whose closer is supplied by a
    *different, undated* element later in the page dated **every token in
    between** — including tokens inside their own separate undated sections. One
    malformed tag discharged the dating obligation for the rest of the page.

    That is exactly the failure `stats`' own rationale gives for preferring a
    declaration to a sniff: *"fails open on exactly the prose it cannot parse"*.
    A regex over HTML **is** the sniff. It is a real parser now, and a region
    that does not parse dates NOTHING and is reported so the build can refuse.

    `data-asof="banana"` is also refused: the obligation is to say WHEN, and a
    string that is not a date says nothing.
    """
    import stats as S
    reg = {k: {"source": "model:p", "format": "pct0"} for k in "abc"}
    ctx = {"summary": {"p": 0.5}}

    leaky = ('<section data-asof="2026-08-07">{{a}}<div>{{b}}</div>'
             '<section class="undated">{{c}}</section>')
    rec: list = []
    S.render(leaky, reg, ctx, record=rec)
    dated = {r["token"]: r["dated"] for r in rec if r.get("token")}
    assert dated == {"a": False, "b": False, "c": False}, (
        f"an unclosed dated region leaked onto later tokens: {dated}. This is "
        f"the fail-open direction and it silently excuses undated claims.")
    assert S._dated_scan(leaky)[1], "the malformed region was not reported"

    ok = '<section data-asof="2026-08-07">{{a}}</section><div>{{b}}</div>'
    rec = []
    S.render(ok, reg, ctx, record=rec)
    assert {r["token"]: r["dated"] for r in rec if r.get("token")} == {
        "a": True, "b": False}, "a well-formed region stopped working"
    assert not S._dated_scan(ok)[1]

    nested = '<div data-asof="2026-08-07">{{a}}<div>{{b}}</div>{{c}}</div>'
    rec = []
    S.render(nested, reg, ctx, record=rec)
    assert all(r["dated"] for r in rec if r.get("token")), (
        "a nested same-tag element truncated the region at the INNER closer, "
        "so tokens after it lost their dating. Fails closed, but still wrong.")

    rec = []
    S.render('<div data-asof="banana">{{a}}</div>', reg, ctx, record=rec)
    assert not [r for r in rec if r.get("token")][0]["dated"], (
        "'banana' bought the dating exemption. The declaration must say WHEN.")


if __name__ == "__main__":
    # Append new tests ABOVE this line.
    raise SystemExit(run_module(globals()))
