"""Export the site's editable prose to one markdown file, and apply it back.

    .venv/bin/python src/site_text.py --export        # writes SITE-TEXT.md
    .venv/bin/python src/site_text.py --apply         # applies edits to source
    .venv/bin/python src/site_text.py --apply --dry-run

`src/edit_mode.py` is the same machinery behind a local page with an edit
button on every block: it reads :func:`blocks`, checks an edit with
:func:`edit_problems` and writes through :func:`plan`, exactly as `--apply`
does.

**IT EXPORTS FROM THE SOURCES, NOT FROM THE BUILT PAGES.** Round-tripping the
built HTML would be a second place the site's words live, and the build would
overwrite it at the next run — the `site/*.html` trap `README` already warns
about. Every block here names the file it came from, and an edit is written
back to that file: at the block's own offsets in an HTML or Markdown source,
by its exact text in a TOML one, escaped for the string it sits in and read
back before anything is written.

⛔ **A FIGURE IS NEVER EDITABLE HERE.** A token — `{{name}}`, a generated
`{{@name=value;fmt;source}}` (`stats.GEN_TOKEN`) or `[[name]]` — can be kept or
deleted, never changed. :func:`edit_problems` refuses a block in which a token
was altered or added, or left half-deleted (a stray `{{`). The one exception
is edit mode's "make it a token", which puts a registry `{{name}}` in place of
a typed number on purpose and says so (``added``). CLAUDE.md §2's rule made
mechanical: prose is the author's, numbers come from the run.

**What is editable:** every text block outside a generated region of the front
pages (`forecast-sheet.html`, `home.html`), including blocks with inline
markup (links, emphasis, dated spans), which is kept as it is unless a whole
pair of tags is deleted; the reader editions (`docs-public/*.md`); the tested
claims (`content/joburg/claims.toml` — the quote, the verdict line, the
argument steps, the "since" box); and the article list
(`content/joburg/articles.toml` — titles and standfirsts).

**What is not, and why:** anything inside a generated region — every
`__NAME_START__`/`__NAME_END__` pair except the page cuts `build_site` uses to
make two pages from one template (`build_site.ARTEFACTS`) — because a script
rewrites it on every run; `content/joburg/stats.toml`, which holds figures;
and the portal, whose text is in `build_portal.py` and is a template rather
than an edition.
"""
from __future__ import annotations

import argparse
import hashlib
import html as _html
import json
import re
import tomllib
from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

import build_site
import stats

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "SITE-TEXT.md"
STATS = ROOT / "content" / "joburg" / "stats.toml"
#: The command that turns an applied edit into pages. The site's normal build.
REBUILD = ".venv/bin/python src/build_all.py --city joburg"

#: The marker pairs that cut one template into two pages. Their contents are
#: hand-written prose; every OTHER marker pair is written by a script.
CUT_KINDS = frozenset(spec[1] for spec in build_site.ARTEFACTS.values() if spec[1])

#: A region the build owns: text inside it is regenerated and must not be
#: edited. Matched as whole comment markers, so blanking one leaves no stray
#: `<!--` or `-->` behind, in HTML and Markdown alike.
GENERATED = re.compile(
    r"<!--\s*__(?!(?:" + "|".join(sorted(CUT_KINDS)) + r")_START__)"
    r"([A-Z][A-Z_]*?)_START__\s*-->.*?<!--\s*__\1_END__\s*-->", re.S)
GENERATED_MD = GENERATED


def _blank_generated(text: str) -> str:
    """The text with every generated region blanked, length and line breaks kept."""
    return GENERATED.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


#: Every token form, from stats' own definitions plus `[[name]]`.
PLACEHOLDER = re.compile("|".join((stats.GEN_TOKEN.pattern, r"\{\{\w+\}\}",
                                   r"\[\[\w+\]\]")))
_STRAY = re.compile(r"\{\{|\}\}|\[\[|\]\]")
BLOCK_ID = re.compile(r"^<!-- block (\w+) -->$", re.M)

CLAIM_FIELDS = ("quote", "speaker", "outlet", "tests", "intro", "since")
ARTICLE_FIELDS = ("title", "standfirst")


def placeholders(text: str) -> list[str]:
    """Every token in ``text``, verbatim, in order."""
    return [m.group(0) for m in PLACEHOLDER.finditer(text)]


def _digest(text: str) -> str:
    """A short, stable id for a block, from its own text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


# --------------------------------------------------------------------------
# text blocks in HTML: one parser for the sources and for the built pages

#: Inline elements: they sit inside a text block and are carried in its text.
INLINE_TAGS = frozenset("a abbr b bdi bdo br cite code data dfn em i img kbd mark q s "
                   "samp small span strong sub sup time u var wbr".split())
#: Elements whose content is not prose. A block that contains one is not a
#: text block (its inner HTML would carry a chart or a control).
OPAQUE = frozenset("script style svg head title select textarea template "
                   "noscript button iframe object canvas math video audio "
                   "picture input".split())
VOID = frozenset("area base br col embed hr img input link meta source track "
                 "wbr".split())


@dataclass
class Leaf:
    """One text block in an HTML document: an element whose content is text
    and inline markup only. ``open_end``/``close_start`` bound its inner HTML."""
    tag: str
    attrs: dict
    start: int
    open_end: int
    close_start: int = -1
    block_child: bool = False
    text: bool = False
    kids: list = field(default_factory=list)


class _LeafParser(HTMLParser):
    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.source = source
        self.lines = [0]
        for m in re.finditer(r"\n", source):
            self.lines.append(m.end())
        self.stack: list[Leaf] = []
        self.leaves: list[Leaf] = []
        self.elements: list[Leaf] = []

    def _pos(self) -> int:
        line, col = self.getpos()
        return self.lines[line - 1] + col

    def handle_starttag(self, tag, attrs):
        start = self._pos()
        raw = self.get_starttag_text() or ""
        if tag in VOID:
            if tag not in INLINE_TAGS and self.stack:
                self.stack[-1].block_child = True
            return
        self.stack.append(Leaf(tag, dict(attrs), start, start + len(raw)))

    def handle_startendtag(self, tag, attrs):
        if tag in VOID:
            return self.handle_starttag(tag, attrs)
        if tag not in INLINE_TAGS and self.stack:
            self.stack[-1].block_child = True

    def handle_data(self, data):
        if data.strip():
            for node in self.stack:
                node.text = True

    def handle_endtag(self, tag):
        if not any(n.tag == tag for n in self.stack):
            return
        at = self._pos()
        while self.stack:
            node = self.stack.pop()
            node.close_start = at
            self._finish(node)
            if node.tag == tag:
                break

    def _finish(self, node: Leaf) -> None:
        parent = self.stack[-1] if self.stack else None
        if any(n.tag in OPAQUE for n in self.stack):
            return
        if node.tag in OPAQUE:
            if parent:
                parent.block_child = True
            return
        if node.text:
            self.elements.append(node)
        if node.tag in INLINE_TAGS:
            if node.block_child:
                if parent:
                    parent.block_child = True
            elif node.text and parent:
                parent.kids.append(node)
            return
        if parent:
            parent.block_child = True
        if not node.block_child:
            if node.text:
                self.leaves.append(node)
        else:
            # A container: its inline children with text are blocks of their
            # own (`<summary><span class="eyebrow">…</span><h2>…</h2></summary>`).
            self.leaves.extend(node.kids)


def _parse(source: str) -> _LeafParser:
    parser = _LeafParser(source)
    parser.feed(source)
    parser.close()
    return parser


def text_blocks(source: str) -> list[Leaf]:
    """Every text block of an HTML document, in document order."""
    return sorted(_parse(source).leaves, key=lambda leaf: leaf.start)


def text_elements(source: str) -> tuple[list[Leaf], list[Leaf]]:
    """``(elements, text blocks)``: every element of an HTML document that
    holds text outside an opaque one, and the text blocks among them, each in
    document order."""
    parser = _parse(source)
    order = lambda leaf: leaf.start  # noqa: E731
    return sorted(parser.elements, key=order), sorted(parser.leaves, key=order)


def _has_words(text: str) -> bool:
    bare = stats.TAGS.sub(" ", PLACEHOLDER.sub(" ", text))
    return bool(re.search(r"\w", bare))


# --------------------------------------------------------------------------
# the blocks

def _html_source_blocks(rel: str, body: str) -> list[dict]:
    masked = _blank_generated(body)
    out = []
    for leaf in text_blocks(masked):
        lo, hi = leaf.open_end, leaf.close_start
        if masked[lo:hi] != body[lo:hi]:
            continue            # part of it is a generated region
        text = re.sub(r"\s+", " ", body[lo:hi]).strip()
        if not text or not _has_words(text):
            continue
        out.append({"source": rel, "kind": leaf.tag, "text": text,
                    "id": _digest(text), "span": (lo, hi)})
    return out


def _md_source_blocks(rel: str, body: str) -> list[dict]:
    masked = _blank_generated(body)
    out = []
    for m in re.finditer(r"[^\n]*\S[^\n]*(?:\n[^\n]*\S[^\n]*)*", masked):
        para = m.group(0).strip()
        if not para or para.startswith(("<span", "</span", "<!--")):
            continue
        lo = m.start() + (len(m.group(0)) - len(m.group(0).lstrip()))
        hi = lo + len(para)
        if body[lo:hi] != para:
            continue            # part of it is a generated region
        out.append({"source": rel, "kind": "md", "text": para,
                    "id": _digest(para), "span": (lo, hi)})
    return out


def _toml_blocks(rel: str, body: str, table: str, fields: tuple,
                 lists: tuple = ()) -> list[dict]:
    """The blocks of a TOML source. Raises `tomllib.TOMLDecodeError` when
    ``body`` does not parse, which is how :func:`plan` checks what it wrote."""
    data = tomllib.loads(body)
    out = []
    for i, entry in enumerate(data.get(table, [])):
        for name in fields:
            val = entry.get(name)
            if isinstance(val, str) and val.strip():
                out.append({"source": rel, "kind": f"{table}[{i}].{name}",
                            "text": val.strip(), "id": _digest(val.strip())})
        for name in lists:
            for j, item in enumerate(entry.get(name, []) or []):
                out.append({"source": rel, "kind": f"{table}[{i}].{name}[{j}]",
                            "text": item.strip(), "id": _digest(item.strip())})
    return out


#: The sources, relative to ROOT. HTML front pages:
HTML_SOURCES = ("home.html", "forecast-sheet.html")
#: the reader editions (every ``*.md`` in it):
MD_DIR = "docs-public"
#: and TOML tables: ``file: (table, text fields, list-of-text fields)``.
TOML_SOURCES = {
    "content/joburg/articles.toml": ("article", ARTICLE_FIELDS, ()),
    "content/joburg/claims.toml": ("claim", CLAIM_FIELDS, ("steps",)),
}


def source_files() -> list[str]:
    """Every file :func:`blocks` reads, relative to ROOT, in the order a
    reader meets it. Edit mode reloads when one of them changes."""
    md = [f"{MD_DIR}/{p.name}" for p in sorted((ROOT / MD_DIR).glob("*.md"))]
    return [*HTML_SOURCES, *md, *TOML_SOURCES]


def blocks() -> list[dict]:
    """Every editable block, in the order a reader meets it.

    Each is ``{"source", "kind", "text", "id"}``; a block from an HTML or
    Markdown source also carries ``span``, the offsets of its text in that
    file, which is where an edit is written."""
    found: list[dict] = []
    for rel in source_files():
        path = ROOT / rel
        if not path.exists():
            continue
        body = path.read_text(encoding="utf-8")
        if rel in TOML_SOURCES:
            found += _toml_blocks(rel, body, *TOML_SOURCES[rel])
        elif rel.endswith(".md"):
            found += _md_source_blocks(rel, body)
        else:
            found += _html_source_blocks(rel, body)

    # ⛔ EVERY BLOCK GETS ITS OWN ID, even when two blocks say the same words.
    # The id is a digest of the text, so identical text collided — and a dict
    # keyed by it silently dropped one of the pair, so the export offered an
    # edit that `--apply` would have written to the wrong block or to neither.
    # The suffix makes the marker unique; a block with a `span` is written at
    # its own offsets, and one without (TOML) only when its text is unique in
    # its file (`plan`).
    seen: dict[str, int] = {}
    for b in found:
        seen[b["id"]] = seen.get(b["id"], 0) + 1
        if seen[b["id"]] > 1:
            b["id"] = f"{b['id']}-{seen[b['id']]}"
            b["repeated"] = True
    return found


# --------------------------------------------------------------------------
# what an edit may and may not do

class EditRefused(SystemExit):
    """An edit the tools will not write. A SystemExit, so the CLI exits with
    the message; `edit_mode` catches it and shows it."""


def registry_names(path: Path | None = None) -> frozenset[str]:
    """The token names the stats registry defines (default: `STATS`)."""
    path = STATS if path is None else path
    if not path.exists():
        return frozenset()
    return frozenset(k for k, v in stats.load_registry(path).items()
                     if k != "audit" and isinstance(v, dict))


#: A tag or an HTML comment in a block's text.
TAG = re.compile(r"<!--.*?-->|<(/?)([a-zA-Z][\w-]*)[^>]*?>", re.S)


def _tags(text: str) -> list[str]:
    return [m.group(0) for m in TAG.finditer(PLACEHOLDER.sub(" ", text))
            if m.group(2)]


def _unbalanced(text: str) -> str | None:
    """The first tag that does not nest, or None."""
    stack: list[str] = []
    for m in TAG.finditer(PLACEHOLDER.sub(" ", text)):
        closing, name = m.group(1), (m.group(2) or "").lower()
        if not name or name in VOID or m.group(0).endswith("/>"):
            continue
        if not closing:
            stack.append(name)
        elif not stack or stack.pop() != name:
            return m.group(0)
    return f"<{stack[-1]}>" if stack else None


def edit_problems(block: dict, new_text: str, added=()) -> list[str]:
    """Why ``new_text`` may not replace ``block``'s text, or [] when it may.

    ``added`` is the tokens put in on purpose in place of a typed number
    (edit mode's "make it a token", which checks each is a registry token
    first). Any other token the original did not have is refused: a token
    whose name or value was changed is a new token, and so is one typed in.
    """
    problems = []
    allowed = Counter(placeholders(block["text"])) + Counter(added)
    for tok, n in Counter(placeholders(new_text)).items():
        if n > allowed[tok]:
            where = (f"{tok} appears {n} times; the original has {allowed[tok]}"
                     if allowed[tok] else f"{tok} is not in the original block")
            problems.append(
                f"The edit changes the block's figures: {where}. A token can be "
                f"kept or deleted, never edited: the build fills it in from the run.")
    if _STRAY.search(PLACEHOLDER.sub(" ", new_text)):
        problems.append("The edit breaks one of the block's figures: a token was "
                        "partly deleted or typed by hand (a stray {{, }}, [[ or ]]). "
                        "Delete the whole token or put it back.")
    if not block["source"].endswith(".toml"):
        new_tags = Counter(_tags(new_text)) - Counter(_tags(block["text"]))
        if new_tags:
            problems.append(f"The edit adds or changes markup: {', '.join(sorted(new_tags))}. "
                            f"A tag can be kept, or deleted with its partner.")
        elif _tags(new_text) != _tags(block["text"]):
            bad = _unbalanced(new_text)
            if bad:
                problems.append(f"The edit breaks the page's markup: {bad} no "
                                f"longer pairs. Delete a tag only with its partner.")
    if block["source"].endswith(".md"):
        extra = _loose_marks(block, new_text) - _loose_marks(block, block["text"])
        if extra:
            problems.append(
                f"The edit leaves Markdown emphasis unpaired: "
                f"{', '.join(sorted(extra))} would show on the page as typed. "
                f"Delete ** or * only with its partner.")
    if not new_text.strip():
        problems.append("The edit empties the block. Delete the element in its "
                        "source file instead.")
    return problems


def _loose_marks(block: dict, text: str) -> Counter:
    """The emphasis characters (``*``, ``_``) a Markdown block shows as typed
    once rendered: a ``**`` whose partner was deleted is one of them."""
    return Counter(c for c in shown_text(block, text) if c in "*_")


# --------------------------------------------------------------------------
# the number gate on an edit

def model_context() -> dict:
    """The current run's outputs, which the gate's structural set is read from."""
    import cityconfig
    cityconfig.use(None)
    return stats.load_context(cityconfig.use_target(None).processed)


def scan_config(registry: dict | None = None, ctx: dict | None = None) -> dict:
    """What `stats.scan_numbers` is called with: `build_site.audit_configs`,
    the settings every page is scanned with."""
    registry = stats.load_registry(STATS) if registry is None else registry
    ctx = model_context() if ctx is None else ctx
    return build_site.audit_configs(registry, ctx)[1]


def scan_form(block: dict, text: str) -> str:
    """A block's text as the number gate reads it: tokens out (on a page a
    token's span is removed before scanning), Markdown rendered as the build
    renders it."""
    bare = PLACEHOLDER.sub(" ", text)
    if block["source"].endswith(".md"):
        import markdown
        bare = markdown.markdown(bare, extensions=list(build_site.MD_EXTENSIONS))
    return bare


def shown_text(block: dict, text: str) -> str:
    """A block's text as a reader sees it: tokens out, Markdown rendered,
    tags dropped, entities decoded."""
    return _html.unescape(stats.TAGS.sub(" ", scan_form(block, text)))


def typed_numbers(block: dict, new_text: str, scan_cfg: dict) -> list[dict]:
    """Every number in ``new_text`` that would block a publish
    (`stats.is_blocking`) and that ``block`` did not already have as one —
    a typed number the edit brings in, including one put where a token was.
    A number the original had as a registered fixed fact comes back marked
    ``was_fixed``: the edit changed the words its entry names.

    A block is scanned alone, so a page context that clears a number (a dated
    passage around a whole article entry, a quotation's class) is not seen:
    such a number is listed, which errs toward asking."""
    def scan(text):
        return stats.scan_numbers(scan_form(block, text), **scan_cfg)
    old = scan(block["text"])
    left = Counter(h["value"] for h in old if stats.is_blocking(h))
    fixed = {h["value"] for h in old if h["status"] == "fixed"}
    out = []
    for h in scan(new_text):
        if not stats.is_blocking(h):
            continue
        if left[h["value"]] > 0:
            left[h["value"]] -= 1
        else:
            out.append({**h, "was_fixed": h["value"] in fixed})
    return out


# --------------------------------------------------------------------------
# writing

def plan(edits: dict[str, str], added: dict[str, list[str]] | None = None
         ) -> tuple[list[tuple[dict, str]], dict[str, tuple[str, str]]]:
    """What applying ``edits`` ({block id: new text}) would write.

    ``added`` is, per block, the tokens put in on purpose (`edit_problems`).

    Returns the changed blocks and, per source file, ``(before, after)``.
    Raises :class:`EditRefused` for an unknown block, a refused edit, or a
    TOML block whose text is not unique in its file. Writes nothing.
    """
    found = {b["id"]: b for b in blocks()}
    unknown = sorted(set(edits) - set(found))
    if unknown:
        raise EditRefused(
            f"{len(unknown)} block id(s) are not in the sources: {unknown[:5]}. "
            f"The sources changed under the edit — re-export (or reload edit "
            f"mode), redo the edit, and do not hand-edit the markers.")
    added = added or {}
    changes: list[tuple[dict, str]] = []
    for block_id, new_text in edits.items():
        old = found[block_id]
        if new_text == old["text"]:
            continue
        problems = edit_problems(old, new_text, added.get(block_id, ()))
        if problems:
            raise EditRefused(f"block {block_id} ({old['source']}, {old['kind']}): "
                              + " ".join(problems))
        changes.append((old, new_text))

    files: dict[str, tuple[str, str]] = {}
    for source in dict.fromkeys(old["source"] for old, _ in changes):
        before = (ROOT / source).read_text(encoding="utf-8")
        body = before
        mine = [(old, new) for old, new in changes if old["source"] == source]
        spanned = sorted((c for c in mine if "span" in c[0]),
                         key=lambda c: c[0]["span"][0], reverse=True)
        for old, new_text in spanned:
            lo, hi = old["span"]
            if source in HTML_SOURCES:
                new_text = rewrap(body[lo:hi], new_text)
            body = body[:lo] + new_text + body[hi:]
        unspanned = [c for c in mine if "span" not in c[0]]
        for old, new_text in unspanned:
            if body.count(old["text"]) != 1:
                raise EditRefused(
                    f"block {old['id']} matched {body.count(old['text'])} times "
                    f"in {source}; refusing to guess which one you meant.")
            at = body.index(old["text"])
            body = (body[:at] + _toml_escape(old, body[:at], new_text.strip())
                    + body[at + len(old["text"]):])
        if unspanned:
            _check_toml(source, body, unspanned)
        files[source] = (before, body)
    return changes, files


def _toml_escape(block: dict, head: str, text: str) -> str:
    """``text`` written for the TOML string it replaces, whose opening
    delimiter ends ``head``. Raises EditRefused when the string's style
    cannot hold it (a literal string has no escapes)."""
    m = re.search(r"(\"\"\"|'''|\"|')\s*\Z", head)
    delim = m.group(1) if m else ""
    control = [c for c in text if (ord(c) < 0x20 and c not in "\t\n") or c == "\x7f"]
    if delim == '"':
        return json.dumps(text, ensure_ascii=False)[1:-1].replace("\x7f", "\\u007f")
    if delim == '"""':
        return "".join("\\" + c if c in '\\"' else
                       f"\\u{ord(c):04x}" if c in control else c for c in text)
    if delim in ("'", "'''") and not control and delim not in text \
            and (delim == "'''" or "\n" not in text):
        return text
    raise EditRefused(
        f"block {block['id']} ({block['source']}, {block['kind']}): the new text "
        f"cannot be written into that string as it stands (a {delim or '?'} "
        f"string with a quotation mark, line break or control character in "
        f"the text). Change it in the file by hand.")


def _check_toml(source: str, body: str, edits: list[tuple[dict, str]]) -> None:
    """Refuse unless ``body`` parses and every edited field now reads exactly
    as edited: what the next build will load, checked before it is written."""
    try:
        now = {b["kind"]: b["text"] for b in _toml_blocks(source, body, *TOML_SOURCES[source])}
    except tomllib.TOMLDecodeError as exc:
        raise EditRefused(f"the edit would leave {source} unreadable ({exc}); "
                          f"nothing was written.") from None
    for old, new_text in edits:
        if now.get(old["kind"]) != new_text.strip():
            raise EditRefused(
                f"block {old['id']} ({source}, {old['kind']}): written into the "
                f"file, the text would read back as {now.get(old['kind'])!r}, not "
                f"as edited; nothing was written.")


def rewrap(orig: str, new_text: str) -> str:
    """``new_text`` laid out like ``orig``, the HTML it replaces.

    A block's text is offered with its whitespace collapsed; written back as
    it is, one edited word would turn a wrapped paragraph into one long line
    and the file's diff into the whole paragraph. So every word the edit kept
    keeps the whitespace that followed it in the file, and the whitespace
    around the element's content is kept too. HTML only: whitespace there is
    not content.
    """
    import difflib
    core = orig.strip()
    lead, trail = orig[:len(orig) - len(orig.lstrip())], orig[len(orig.rstrip()):]
    parts = re.split(r"(\s+)", core)
    words, gaps = parts[0::2], parts[1::2]
    new = new_text.split()
    where: list[int | None] = [None] * len(new)
    sm = difflib.SequenceMatcher(None, words, new, autojunk=False)
    for tag, i1, _i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(j2 - j1):
                where[j1 + k] = i1 + k
    out = []
    for j, word in enumerate(new):
        if j:
            a, b = where[j - 1], where[j]
            if a is not None and b == a + 1:
                out.append(gaps[a])
            elif b is not None and b > 0 and "\n" in gaps[b - 1]:
                out.append(gaps[b - 1])
            else:
                out.append(" ")
        out.append(word)
    return lead + "".join(out) + trail


def write(files: dict[str, tuple[str, str]]) -> list[str]:
    """Write a :func:`plan`'s files. Returns the paths written."""
    for source, (_before, after) in files.items():
        (ROOT / source).write_text(after, encoding="utf-8")
    return list(files)


# --------------------------------------------------------------------------
# the markdown round trip

def export() -> int:
    found = blocks()
    texts = [b["text"] for b in found]
    dupes = {b["id"] for b in found if texts.count(b["text"]) > 1}
    lines = [
        "# The site's words, for editing",
        "",
        "Generated by `src/site_text.py --export`. **Edit the text under each",
        "heading and nothing else.** Leave the `<!-- block … -->` markers where",
        "they are: `--apply` finds your edit by them.",
        "",
        "⛔ **Do not edit anything in `{{double braces}}` or `[[double",
        "brackets]]`.** Those are figures the build fills in from the run that",
        "produced them. Typing a number over one publishes a figure nothing can",
        "trace, and `--apply` refuses the block rather than let that through.",
        "",
        "Blocks inside the page's generated regions are not here at all: the",
        "build rewrites them, so an edit would vanish at the next run.",
        "",
        f"{len(found)} blocks from "
        f"{len({b['source'] for b in found})} files.",
        "",
    ]
    current = None
    for b in found:
        if b["source"] != current:
            current = b["source"]
            lines += ["", f"## {current}", ""]
        if b["id"] in dupes and "span" not in b:
            lines += [f"<!-- block {b['id']} SAME WORDS APPEAR ELSEWHERE — "
                      f"an edit here is refused unless the text is unique in "
                      f"its own file -->"]
        else:
            lines += [f"<!-- block {b['id']} -->"]
        lines += [f"*{b['kind']}*", "", b["text"], "",
                  f"<!-- /block {b['id']} -->", ""]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    where = OUT.relative_to(ROOT) if OUT.is_relative_to(ROOT) else OUT
    print(f"wrote {where} — {len(found)} blocks, {len(dupes)} repeated")
    return 0


def _parse_edits() -> dict[str, str]:
    """The edited file, as {block id: text}."""
    if not OUT.exists():
        raise SystemExit(f"{OUT} does not exist — run --export first.")
    text = OUT.read_text(encoding="utf-8")
    edits: dict[str, str] = {}
    # ⛔ PAIRED MARKERS, NOT A SPLIT ON THE NEXT HEADING. The first version
    # ended a block at the next `## `, and the reader editions are full of `## `
    # headings — so any block containing one was silently truncated to nothing
    # and `--apply` would have written that emptiness back into the page.
    for m in re.finditer(r"<!-- block ([\w-]+)[^>]*-->\n(.*?)\n<!-- /block \1 -->",
                         text, re.S):
        chunk = re.sub(r"^\s*\*[^*]+\*\s*", "", m.group(2), count=1)
        edits[m.group(1)] = chunk.strip()
    opened = len(re.findall(r"<!-- block ([\w-]+)", text))
    if opened != len(edits):
        raise SystemExit(
            f"{OUT.name} has {opened} block markers but {len(edits)} complete "
            f"blocks. A `<!-- /block … -->` line was moved or deleted, and the "
            f"text between them is what would be written to the site.")
    return edits


def apply(dry_run: bool = False) -> int:
    changes, files = plan(_parse_edits())
    if not changes:
        print("no edits to apply.")
        return 0
    cfg = scan_config()
    for old, new_text in changes:
        typed = typed_numbers(old, new_text, cfg)
        if typed:
            raise EditRefused(
                f"block {old['id']} ({old['source']}, {old['kind']}) brings in "
                f"typed figures that are not tokens: "
                f"{', '.join(repr(h['value']) for h in typed)}. Use a token from "
                f"content/joburg/stats.toml, register the number there as an "
                f"[[audit.fixed]] fact with its source, or remove it "
                f"(src/edit_mode.py does each in the browser).")
    for old, _new in changes:
        print(f"  {old['source']:32} {old['kind']:22} {old['id']}")
    if not dry_run:
        write(files)
    verb = "would change" if dry_run else "changed"
    print(f"{verb} {len(changes)} block(s). {'' if dry_run else 'Rebuild: ' + REBUILD}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--export", action="store_true", help="write SITE-TEXT.md")
    ap.add_argument("--apply", action="store_true", help="apply its edits back")
    ap.add_argument("--dry-run", action="store_true",
                    help="with --apply: say what would change, write nothing")
    args = ap.parse_args(argv)
    if args.export == args.apply:
        raise SystemExit("choose one: --export or --apply")
    return export() if args.export else apply(args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
