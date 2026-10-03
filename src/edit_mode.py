"""Edit the site's words on the site itself, locally, and write them back to
their sources.

    .venv/bin/python src/edit_mode.py            # then open http://127.0.0.1:8801/

Serves the last build (``site/``) on the loopback interface with an edit button
on every text block that comes from an editable source, as `site_text.blocks`
defines them: the front pages' prose, the reader editions, the claims and the
article list. Nothing is written until you press **Apply**; then you run the
normal build (`site_text.REBUILD`) and reload.

What it will not do
===================

* **Edit a figure.** A token shows as a locked chip. It can be kept or deleted,
  never changed: Save refuses any change inside a token (`site_text.edit_problems`),
  whether it was typed in the raw-text view or sent to the endpoint directly.
* **Let a typed number through unnoticed.** *Review changes* runs the build's
  own number gate (`stats.scan_numbers` with `build_site.audit_configs`) on the
  edited text and lists every number-shaped string the original did not have,
  with three ways out: make it a token (a registry token whose value it is),
  register it (a ``[[audit.fixed]]`` entry in the stats registry, with its
  source, written at Apply with the edit), or remove it. *Apply* refuses while
  one is unresolved.
* **Reach the public site.** It binds 127.0.0.1 only, answers only a loopback
  client and its own ``Host``, and takes writes only from its own pages (a
  custom header a cross-site form cannot send). The overlay
  (``src/edit/edit-mode.js`` and ``.css``) is injected into each page as it is
  served and is never written into ``site/``; `deploy_check` refuses a site
  that carries either file or a page that references them (:func:`shipped`).

How a built element is matched to its source block
==================================================

By text. Both sides are reduced to the same :func:`signature`: tokens (a
rendered ``data-token`` span on the page, a placeholder in the source) become
one sentinel, markup goes, and only letters, digits and the sentinel are
compared. A Markdown block is first rendered the way `build_site.render_doc`
renders it (`build_site.MD_EXTENSIONS`). A block whose words were rewritten by
a script on the way to the page (a generated region) matches nothing and gets
no button, which is the point: an edit there would be lost at the next build.
A source edited since the last build matches nothing until the next build.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import difflib
import html as _html
import json
import mimetypes
import re
import sys
import threading
import tomllib
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import site_text
import stats

ROOT = site_text.ROOT
SITE = ROOT / "site"
PORT = 8801
LOOPBACK = "127.0.0.1"
OVERLAY_DIR = ROOT / "src" / "edit"
#: The overlay's files. Served from `URL_PREFIX`, never copied into a site.
OVERLAY_FILES = ("edit-mode.js", "edit-mode.css")
#: Every URL edit mode answers itself starts with this.
URL_PREFIX = "/__edit/"
#: The attribute that ties a served element to its source block(s).
BLOCK_ATTR = "data-edit-block"


# --------------------------------------------------------------------------
# the guard deploy_check runs

def shipped(site: Path) -> tuple[list[str], list[str]]:
    """``(pages scanned, problems)``: every overlay file under ``site`` and
    every page that references the overlay or carries its block attribute.
    `deploy_check` refuses a deploy on any problem."""
    problems = [f"{f.relative_to(site).as_posix()}: the edit-mode overlay file"
                for f in sorted(site.rglob("*")) if f.is_file() and f.name in OVERLAY_FILES]
    pages = sorted(f.relative_to(site).as_posix() for f in site.rglob("*.html"))
    for rel in pages:
        text = (site / rel).read_text(encoding="utf-8", errors="replace")
        for marker in (URL_PREFIX, BLOCK_ATTR):
            if marker in text:
                problems.append(f"{rel}: carries {marker!r} (an edit-mode page)")
    return pages, problems


# --------------------------------------------------------------------------
# matching built elements to source blocks

_TOK = "qqtokqq"


def signature(fragment: str) -> str:
    """A fragment of HTML (built or source) reduced to what both sides share."""
    s = stats.SOURCED.sub(f" {_TOK} ", fragment)
    s = site_text.PLACEHOLDER.sub(f" {_TOK} ", s)
    s = _html.unescape(stats.TAGS.sub(" ", s)).lower().replace(_TOK, "#")
    return re.sub(r"[^\w#]|_", "", s)


def block_signature(block: dict) -> str:
    """The signature of what ``block`` becomes on a page, or "" when it is too
    bare to identify an element (no letters: a lone token, a bare number)."""
    text = block["text"]
    if block["source"].endswith(".md"):
        import markdown
        import build_site
        text = markdown.markdown(site_text.PLACEHOLDER.sub(f" {_TOK} ", text),
                                 extensions=list(build_site.MD_EXTENSIONS))
    sig = signature(text)
    return sig if re.search(r"[^\W\d_]", sig) else ""


def annotate(page: str, index: dict[str, list[str]],
             allowed: set[str] | None = None) -> tuple[str, set[str]]:
    """``page`` with each element that renders a source block tagged with the
    block's id, and the ids tagged.

    ``index`` maps a signature to the ids of the blocks that have it, in
    source order; ``allowed`` (None: any) is the blocks that can be on this
    page. An element matches when its whole text is a block's: of nested
    elements saying the same thing, the innermost block-level one carries the
    tag. When several blocks share the words (a repeated dated label), the
    k-th such element on the page is the k-th such block — the page keeps its
    source's order — if the counts agree; otherwise the element carries every
    candidate and the editor says so.
    """
    elements, leaves = site_text.text_elements(page)
    ok = (lambda i: True) if allowed is None else (lambda i: i in allowed)  # noqa: E731
    by_sig: dict[str, list] = {}
    for el in elements:
        sig = signature(page[el.open_end:el.close_start])
        if any(ok(i) for i in index.get(sig, ())):
            by_sig.setdefault(sig, []).append(el)
    inserts: list[tuple[int, list[str]]] = []
    for sig, els in by_sig.items():
        def inside(a, b):
            return b.start <= a.start and a.close_start <= b.close_start and a is not b
        keep = [e for e in els
                if not any(inside(o, e) and o.tag not in site_text.INLINE_TAGS for o in els)
                and not (e.tag in site_text.INLINE_TAGS and any(inside(e, o) for o in els))]
        ids = [i for i in index[sig] if ok(i)]
        if len(ids) > 1 and len(ids) == len(keep):
            inserts += [(e.open_end - 1, [i]) for e, i in zip(keep, ids)]
        else:
            inserts += [(e.open_end - 1, ids) for e in keep]
    matched = {at for at, _ in inserts}
    for leaf in leaves:
        if leaf.open_end - 1 in matched:
            continue
        # An element that joins several fields ("speaker · outlet", or a label
        # before the text): the blocks inside it, if together they are most
        # of what it says.
        sig = signature(page[leaf.open_end:leaf.close_start])
        inside = [s for s in index if len(s) >= 8 and s in sig
                  and any(ok(i) for i in index[s])]
        if sig and sum(map(len, inside)) >= 0.6 * len(sig):
            inserts.append((leaf.open_end - 1, list(dict.fromkeys(
                i for s in inside for i in index[s] if ok(i)))))
    out, last, tagged = [], 0, set()
    for at, ids in sorted(inserts):
        out += [page[last:at], f' {BLOCK_ATTR}="{_html.escape(" ".join(ids))}"']
        tagged.update(ids)
        last = at
    out.append(page[last:])
    return "".join(out), tagged


def inject(page: str) -> str:
    """The overlay's two files, linked from the page's <head>."""
    tags = (f'<link rel="stylesheet" href="{URL_PREFIX}edit-mode.css">'
            f'<script defer src="{URL_PREFIX}edit-mode.js"></script>')
    i = page.find("</head>")
    return page[:i] + tags + page[i:] if i != -1 else tags + page


def page_blocks(blocks) -> dict[str | None, set[str]]:
    """Which blocks each built page can show, from `build_site`'s own map of
    page to source (`ARTEFACTS`, with the half of a template a page cuts, and
    `DOCS`). A TOML block can be on any page; key None is every other page."""
    import build_site
    sources: dict[str, list[tuple[str, str | None]]] = {}
    for output, (source, cut, _title) in build_site.ARTEFACTS.items():
        sources.setdefault(output, []).append((source, cut))
    for source, spec in build_site.DOCS.items():
        sources.setdefault(spec[0], []).append((source, None))
    blocks = list(blocks)
    anywhere = {b["id"] for b in blocks if b["source"].endswith(".toml")}
    out: dict[str | None, set[str]] = {None: anywhere}
    for page, feeds in sources.items():
        ids = set(anywhere)
        for source, cut in feeds:
            cuts = []
            if cut:
                body = (ROOT / source).read_text(encoding="utf-8")
                cuts = [m.span() for m in re.finditer(
                    rf"<!-- __{cut}_START__ -->.*?<!-- __{cut}_END__ -->", body, re.S)]
            ids |= {b["id"] for b in blocks if b["source"] == source
                    and not any(lo <= b["span"][0] < hi for lo, hi in cuts)}
        out[page] = ids
    return out


# --------------------------------------------------------------------------
# the editor's view of a block

_SEGMENT = re.compile(site_text.PLACEHOLDER.pattern + "|" + site_text.TAG.pattern, re.S)


def segments(block: dict, text: str) -> list[dict]:
    """``text`` as the editor shows it: plain text, locked token chips and,
    outside TOML, locked tag chips."""
    out, last = [], 0
    toml = block["source"].endswith(".toml")
    for m in _SEGMENT.finditer(text):
        tok = site_text.PLACEHOLDER.fullmatch(m.group(0))
        if not tok and toml:
            continue
        if m.start() > last:
            out.append({"t": "text", "v": text[last:m.start()]})
        if tok:
            gen = stats.GEN_TOKEN.fullmatch(m.group(0))
            name = gen.group(1) if gen else m.group(0).strip("{}[]")
            out.append({"t": "token", "v": m.group(0), "name": name})
        else:
            tag = re.match(r"<(/?[a-zA-Z][\w-]*|!--)", m.group(0)).group(1)
            out.append({"t": "tag", "v": m.group(0), "label": f"<{tag}>"})
        last = m.end()
    if last < len(text):
        out.append({"t": "text", "v": text[last:]})
    return out


# --------------------------------------------------------------------------
# the number gate on one block

def _number_offsets(text: str, value: str) -> list[tuple[int, int]]:
    """Where ``value`` occurs as a number in ``text``, outside tokens and tags."""
    blank = lambda m: " " * len(m.group(0))  # noqa: E731
    masked = _SEGMENT.sub(blank, text)
    return [(m.start(), m.start() + len(m.group(0).strip()))
            for m in stats.NUMBERISH.finditer(masked)
            if m.group(0).strip() == value and m.lastgroup in stats.GATING]


class Session:
    """The pending edits and everything needed to judge them. One per server."""

    def __init__(self, site: Path | None = None):
        # Resolved: pages are found by walking it and keyed by their path
        # relative to it, and a relative or symlinked path (`/tmp`) would not
        # compare with the resolved one `resolve_path` returns.
        self.site = (SITE if site is None else site).resolve()
        self.pending: dict[str, dict] = {}
        #: `[[audit.fixed]]` entries made by "register it", per block. Held
        #: with the edit: written at Apply, dropped with a Discard.
        self.registered: dict[str, list[dict]] = {}
        self._gate = None
        self.lock = threading.RLock()
        self._key = None
        self._ctx = None
        self._pages: dict[str, tuple[float, str, set]] = {}
        self.refresh()

    # -- state ----------------------------------------------------------
    def _sources_key(self):
        files = [ROOT / rel for rel in site_text.source_files()] + [site_text.STATS]
        return tuple((str(f), f.stat().st_mtime_ns) for f in files if f.exists())

    def refresh(self) -> None:
        """Re-read the sources and the registry if any of them changed."""
        key = self._sources_key()
        if key == self._key:
            return
        if self._ctx is None:
            self._ctx = site_text.model_context()
        self.blocks = {b["id"]: b for b in site_text.blocks()}
        self.registry = stats.load_registry(site_text.STATS)
        self.names = site_text.registry_names(site_text.STATS)
        self.scan_cfg = site_text.scan_config(self.registry, self._ctx)
        self.index: dict[str, list[str]] = {}
        for b in self.blocks.values():
            sig = block_signature(b)
            if sig:
                self.index.setdefault(sig, []).append(b["id"])
        self.allowed = page_blocks(self.blocks.values())
        self._displays = None
        self._gate = None
        self._pages.clear()
        self._key = key

    def displays(self) -> dict[str, str]:
        """What each registry token shows a reader now."""
        if self._displays is None:
            self._displays = {}
            for name in sorted(self.names):
                shown, _drift, unresolved = stats.render(
                    "{{%s}}" % name, self.registry, self._ctx, wrap=False)
                if not unresolved:
                    self._displays[name] = shown
        return self._displays

    def page(self, path: Path) -> tuple[str, set]:
        """A built page with its blocks tagged, cached until it is rebuilt."""
        mtime = path.stat().st_mtime
        hit = self._pages.get(str(path))
        if hit and hit[0] == mtime:
            return hit[1], hit[2]
        rel = path.relative_to(self.site).as_posix()
        text, tagged = annotate(path.read_text(encoding="utf-8"), self.index,
                                self.allowed.get(rel, self.allowed[None]))
        self._pages[str(path)] = (mtime, text, tagged)
        return text, tagged

    def pages_of(self, block_id: str) -> list[str]:
        """The built pages a block appears on."""
        out = []
        for f in sorted(self.site.rglob("*.html")):
            _text, tagged = self.page(f)
            if block_id in tagged:
                out.append(f.relative_to(self.site).as_posix())
        return out

    def text_of(self, block_id: str) -> str:
        edit = self.pending.get(block_id)
        return edit["text"] if edit else self.blocks[block_id]["text"]

    # -- judging an edit -------------------------------------------------
    def stats_file(self) -> dict[str, tuple[str, str]]:
        """``{stats.toml: (before, after)}`` with every pending registration
        appended, or {} when there is none."""
        entries = [e for block_id in self.registered for e in self.registered[block_id]]
        if not entries:
            return {}
        before = site_text.STATS.read_text(encoding="utf-8")
        after = before.rstrip("\n") + "\n" + "".join(
            "\n[[audit.fixed]]\n" + "".join(
                f"{k} = {json.dumps(v, ensure_ascii=False)}\n" for k, v in e.items())
            for e in entries)
        return {site_text.STATS.relative_to(ROOT).as_posix(): (before, after)}

    def gate(self) -> dict:
        """The number gate's settings, with the pending registrations in the
        registry as Apply would write them."""
        if self._gate is None:
            pending = self.stats_file()
            self._gate = (site_text.scan_config(tomllib.loads(
                next(iter(pending.values()))[1]), self._ctx)
                if pending else self.scan_cfg)
        return self._gate

    def new_numbers(self, block: dict, new_text: str) -> list[dict]:
        return site_text.typed_numbers(block, new_text, self.gate())

    @staticmethod
    def prose(block: dict, text: str) -> str:
        """``text`` as a reader reads it, lower-cased: what a registered
        entry's context is matched against."""
        return re.sub(r"\s+", " ", _html.unescape(stats.TAGS.sub(
            " ", site_text.scan_form(block, text)))).lower()

    def _fresh_offset(self, block: dict, text: str, value: str) -> tuple[int, int] | None:
        """The occurrence of ``value`` in ``text`` that the original lacked."""
        spans = _number_offsets(text, value)
        fresh = [(lo, hi) for lo, hi in spans
                 if text[max(0, lo - 12):hi + 12] not in block["text"]]
        return (fresh or spans or [None])[-1]

    # -- the API ---------------------------------------------------------
    def block(self, block_id: str) -> dict:
        b = self.blocks.get(block_id)
        if not b:
            raise LookupError(f"no block {block_id!r} in the sources; reload the page")
        text = self.text_of(block_id)
        return {"id": block_id, "source": b["source"], "kind": b["kind"],
                "text": text, "pending": block_id in self.pending,
                "segments": segments(b, text)}

    def segment(self, block_id: str, text: str) -> dict:
        return {"segments": segments(self.blocks[block_id], text)}

    def save(self, block_id: str, text: str, page: str = "",
             added: tuple = ()) -> tuple[bool, dict]:
        b = self.blocks.get(block_id)
        if not b:
            raise LookupError(f"no block {block_id!r} in the sources; reload the page")
        text = text.strip()
        if text == b["text"]:
            self.discard(block_id)
            return True, {"saved": False, "numbers": []}
        added = [t for t in (self.pending.get(block_id) or {}).get("added", [])
                 if t in text] + list(added)
        problems = site_text.edit_problems(b, text, added)
        if problems:
            return False, {"problems": problems}
        self.pending[block_id] = {"text": text, "page": page, "added": added}
        # A registration whose words the edit no longer has is dropped, so a
        # stale entry never reaches Apply.
        kept = [e for e in self.registered.pop(block_id, [])
                if e["context"].lower() in self.prose(b, text)]
        if kept:
            self.registered[block_id] = kept
        self._gate = None
        return True, {"saved": True,
                      "numbers": [h["value"] for h in self.new_numbers(b, text)]}

    def discard(self, block_id: str) -> dict:
        self.pending.pop(block_id, None)
        self.registered.pop(block_id, None)
        self._gate = None
        return {"pending": sorted(self.pending)}

    def _added(self) -> dict[str, list[str]]:
        return {i: e["added"] for i, e in self.pending.items()}

    def kinds(self) -> list[str]:
        """The kinds the registry's fixed facts already use."""
        return sorted({str(f.get("kind")) for f in self.scan_cfg["fixed"] if f.get("kind")})

    def review(self) -> dict:
        edits, ok_edits, blocked = [], {}, False
        for block_id, edit in self.pending.items():
            b = self.blocks.get(block_id)
            if b is None:
                edits.append({"id": block_id, "problems": [
                    "The source block changed under the edit. Discard it and redo it."]})
                blocked = True
                continue
            problems = site_text.edit_problems(b, edit["text"], edit["added"])
            numbers = []
            for h in self.new_numbers(b, edit["text"]):
                shown = {n: d for n, d in self.displays().items()
                         if d.replace(",", "") == h["value"].replace(",", "")}
                numbers.append({"value": h["value"], "kind": h["kind"],
                                "context": h["context"], "was_fixed": h["was_fixed"],
                                "candidates": [{"name": n, "display": d}
                                               for n, d in sorted(shown.items())]})
            blocked = blocked or bool(problems or numbers)
            if not problems:
                ok_edits[block_id] = edit["text"]
            edits.append({"id": block_id, "source": b["source"], "kind": b["kind"],
                          "problems": problems, "numbers": numbers})
        diff = ""
        if ok_edits:
            try:
                _changes, files = site_text.plan(ok_edits, self._added())
            except site_text.EditRefused as exc:
                diff, blocked = "", True
                edits.append({"id": "", "problems": [str(exc)]})
            else:
                diff = file_diff({**files, **self.stats_file()})
        return {"edits": edits, "diff": diff, "can_apply": bool(self.pending) and not blocked,
                "kinds": self.kinds(), "rebuild": site_text.REBUILD}

    def resolve(self, block_id: str, value: str, action: str, token: str = "") -> tuple[bool, dict]:
        """Make a flagged number a token, or remove it, in the pending edit."""
        b, edit = self.blocks.get(block_id), self.pending.get(block_id)
        if not b or not edit:
            raise LookupError(f"no pending edit for block {block_id!r}")
        at = self._fresh_offset(b, edit["text"], value)
        if at is None:
            return False, {"problems": [f"The edited text has no {value!r}."]}
        lo, hi = at
        text = edit["text"]
        if action == "token":
            if token not in self.names:
                return False, {"problems": [f"The registry (content/joburg/stats.toml) "
                                            f"has no token {token!r}."]}
            text = text[:lo] + "{{%s}}" % token + text[hi:]
            return self.save(block_id, text, edit["page"], ("{{%s}}" % token,))
        elif action == "remove":
            left, right = text[:lo].rstrip(" "), text[hi:].lstrip(" ")
            sep = "" if not left or not right or right[0] in ".,;:)" else " "
            text = left + sep + right
        else:
            return False, {"problems": [f"The action {action!r} is not one edit mode knows."]}
        return self.save(block_id, text, edit["page"])

    def register(self, block_id: str, value: str, context: str, source: str,
                 kind: str) -> tuple[bool, dict]:
        """Hold an ``[[audit.fixed]]`` entry for a flagged number. It shows in
        the review's diff and is written to the registry at Apply, with the
        edit; Discard drops it."""
        b, edit = self.blocks.get(block_id), self.pending.get(block_id)
        if not b or not edit:
            raise LookupError(f"no pending edit for block {block_id!r}")
        problems = []
        if len(source.strip()) < stats.DECLARATION_MIN_CHARS:
            problems.append("The entry needs a source: say where the number "
                            "comes from.")
        if (value.lower() not in context.lower()
                or context.strip().lower() not in self.prose(b, edit["text"])):
            problems.append("The context must be words from the edited text "
                            "that contain the number.")
        if problems:
            return False, {"problems": problems}
        pages = self.pages_of(block_id) or [edit["page"].lstrip("/") or "index.html"]
        entry = {"value": value, "context": context.strip(), "kind": kind or "history",
                 "source": source.strip(), "reviewed": _dt.date.today().isoformat(),
                 "page": ", ".join(pages)}
        self.registered.setdefault(block_id, []).append(entry)
        self._gate = None
        try:
            self.gate()                 # the registry Apply would write must load
        except tomllib.TOMLDecodeError as exc:
            self.registered[block_id].pop()
            self._gate = None
            return False, {"problems": [f"The entry would break the registry ({exc})."]}
        return True, {"registered": entry}

    def apply(self) -> tuple[bool, dict]:
        review = self.review()
        if not review["can_apply"]:
            return False, {"problems": ["Apply waits for every flagged number and "
                                        "refused edit (Review changes)."], "review": review}
        edits = {i: e["text"] for i, e in self.pending.items()}
        _changes, files = site_text.plan(edits, self._added())
        files.update(self.stats_file())
        written = site_text.write(files)
        self.pending.clear()
        self.registered.clear()
        self.refresh()
        return True, {"written": written, "diff": file_diff(files),
                      "rebuild": site_text.REBUILD}


def file_diff(files: dict[str, tuple[str, str]]) -> str:
    return "".join("".join(difflib.unified_diff(
        before.splitlines(True), after.splitlines(True),
        fromfile=f"a/{src}", tofile=f"b/{src}", n=1)) for src, (before, after) in files.items())


# --------------------------------------------------------------------------
# the server

def resolve_path(site: Path, url_path: str) -> Path | None:
    """The file the deployed site serves for ``url_path`` (`/forecast` is
    forecast.html, `/play/` is play/index.html), or None."""
    rel = unquote(url_path).lstrip("/")
    base = site.resolve()
    for cand in (rel, rel + ".html", (rel.rstrip("/") + "/index.html").lstrip("/")):
        p = (base / cand).resolve()
        if p.is_file() and p.is_relative_to(base):
            return p
    return None


class Handler(BaseHTTPRequestHandler):
    session: Session
    port: int = PORT
    server_version = "edit-mode"

    def log_message(self, fmt, *args):
        """Quiet: only a refused or failed request is logged."""
        if len(args) > 1 and str(args[1])[:1] in "45":
            sys.stderr.write("edit mode: " + (fmt % args) + "\n")

    def _refuse(self) -> bool:
        """Anything not from this machine, to this server, is refused."""
        host = self.headers.get("Host", "")
        if (self.client_address[0] not in ("127.0.0.1", "::1")
                or host not in (f"127.0.0.1:{self.port}", f"localhost:{self.port}")):
            self.send_error(HTTPStatus.FORBIDDEN, "edit mode answers this machine only")
            return True
        return False

    def _send(self, status, body: bytes, ctype: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status, obj) -> None:
        self._send(status, json.dumps(obj).encode(), "application/json; charset=utf-8")

    def do_GET(self):
        if self._refuse():
            return
        url = urlparse(self.path)
        s = self.session
        if url.path.startswith(URL_PREFIX):
            name = url.path[len(URL_PREFIX):]
            if name in OVERLAY_FILES:
                ctype = "text/css" if name.endswith(".css") else "text/javascript"
                return self._send(200, (OVERLAY_DIR / name).read_bytes(), ctype + "; charset=utf-8")
            q = {k: v[0] for k, v in parse_qs(url.query).items()}
            with s.lock:
                s.refresh()
                try:
                    if name == "api/block":
                        return self._json(200, s.block(q.get("id", "")))
                    if name == "api/review":
                        return self._json(200, s.review())
                    if name == "api/status":
                        return self._json(200, {"pending": sorted(s.pending)})
                except LookupError as exc:
                    return self._json(404, {"problems": [str(exc)]})
            return self._json(404, {"problems": [f"no such endpoint {name!r}"]})
        path = resolve_path(s.site, url.path)
        if path is None:
            return self.send_error(HTTPStatus.NOT_FOUND)
        if path.suffix == ".html":
            with s.lock:
                s.refresh()
                text, _tagged = s.page(path)
            return self._send(200, inject(text).encode("utf-8"), "text/html; charset=utf-8")
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return self._send(200, path.read_bytes(), ctype)

    def do_POST(self):
        if self._refuse():
            return
        # A page on another site can POST a form here; it cannot add a custom
        # header without a CORS preflight, which this server never answers.
        if (self.headers.get("X-Edit-Mode") != "1"
                or not self.headers.get("Content-Type", "").startswith("application/json")
                or self.headers.get("Sec-Fetch-Site", "same-origin") != "same-origin"):
            return self._json(403, {"problems": ["edit mode takes writes from its own pages only"]})
        url = urlparse(self.path)
        name = url.path[len(URL_PREFIX):] if url.path.startswith(URL_PREFIX) else ""
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        except ValueError:
            return self._json(400, {"problems": ["The request is not JSON."]})
        if not isinstance(body, dict) or not all(isinstance(v, str) for v in body.values()):
            return self._json(400, {"problems": ["The request must be a JSON object of strings."]})
        s = self.session
        with s.lock:
            s.refresh()
            try:
                if name == "api/segments":
                    return self._json(200, s.segment(body["id"], body["text"]))
                if name == "api/save":
                    ok, out = s.save(body["id"], body["text"], body.get("page", ""))
                elif name == "api/discard":
                    ok, out = True, s.discard(body["id"])
                elif name == "api/resolve":
                    ok, out = s.resolve(body["id"], body["value"], body["action"],
                                        body.get("token", ""))
                elif name == "api/register":
                    ok, out = s.register(body["id"], body["value"], body.get("context", ""),
                                         body.get("source", ""), body.get("kind", ""))
                elif name == "api/apply":
                    ok, out = s.apply()
                    if ok:
                        print(f"edit mode: wrote {', '.join(out['written'])}. "
                              f"Now run: {out['rebuild']}", flush=True)
                else:
                    return self._json(404, {"problems": [f"no such endpoint {name!r}"]})
            except (KeyError, LookupError) as exc:
                return self._json(404, {"problems": [f"{exc}"]})
            except site_text.EditRefused as exc:
                return self._json(422, {"problems": [str(exc)]})
        return self._json(200 if ok else 422, out)


def serve(site: Path | None = None, port: int | None = None) -> ThreadingHTTPServer:
    """A server bound to the loopback interface; the caller runs it."""
    site, port = (SITE if site is None else site), (PORT if port is None else port)
    session = Session(site)
    handler = type("BoundHandler", (Handler,), {"session": session, "port": port})
    return ThreadingHTTPServer((LOOPBACK, port), handler)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--site", type=Path, default=SITE,
                    help="the build to serve (default: site/)")
    ap.add_argument("--port", type=int, default=PORT)
    args = ap.parse_args(argv)
    if not (args.site / "index.html").is_file():
        raise SystemExit(f"{args.site} has no index.html — build the site first: "
                         f"{site_text.REBUILD}")
    try:
        httpd = serve(args.site, args.port)
    except OSError as exc:
        raise SystemExit(f"cannot listen on {LOOPBACK}:{args.port} ({exc}). Is another "
                         f"server using it? `lsof -nP -iTCP:{args.port} -sTCP:LISTEN`")
    print(f"edit mode: http://{LOOPBACK}:{args.port}/  (this machine only; Ctrl-C stops it)",
          flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
