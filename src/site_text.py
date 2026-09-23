"""Export the site's editable prose to one markdown file, and apply it back.

    .venv/bin/python src/site_text.py --export        # writes SITE-TEXT.md
    .venv/bin/python src/site_text.py --apply         # applies edits to source
    .venv/bin/python src/site_text.py --apply --dry-run

**IT EXPORTS FROM THE SOURCES, NOT FROM THE BUILT PAGES.** Round-tripping the
built HTML would be a second place the site's words live, and the build would
overwrite it at the next run — the `site/*.html` trap `README` already warns
about. Every block here names the file it came from, and `--apply` writes back
to that file by matching the block's text exactly.

⛔ **A FIGURE IS NEVER EDITABLE HERE.** `{{token}}` and `[[token]]` placeholders
are carried through verbatim and `--apply` refuses a block whose placeholder set
has changed. That is CLAUDE.md §2's rule made mechanical: prose is the author's,
numbers come from the run, and an editor who types a number over a token would
be publishing a figure nobody can trace.

**What is editable:** the front page (`forecast-sheet.html`, the hand-written
prose between its generated regions), the reader editions (`docs-public/*.md`)
and the tested claims (`content/joburg/claims.toml` — the quote, the verdict
line, the argument steps, the "since" box).

**What is not, and why:** anything inside a generated region
(`__GEN_START__`/`__GEN_END__` and friends), because the build rewrites it on
every run; `content/joburg/stats.toml`, which holds figures; and the portal,
whose text is in `build_portal.py` and is a template rather than an edition.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "SITE-TEXT.md"

# Regions the build owns. Text inside them is regenerated and must not be edited.
GENERATED = re.compile(
    r"__(GEN|BALLOTS|CLAIMS|REGIMES|MAP|HEXMAP|SEATS_NOTE)_START__.*?"
    r"__(GEN|BALLOTS|CLAIMS|REGIMES|MAP|HEXMAP|SEATS_NOTE)_END__",
    re.S)

PLACEHOLDER = re.compile(r"\{\{\w+\}\}|\[\[\w+\]\]")
BLOCK_ID = re.compile(r"^<!-- block (\w+) -->$", re.M)

# Prose-bearing tags on the front page. A block is one element's inner text.
PROSE_TAGS = ("h1", "h2", "h3", "h4", "p", "li", "figcaption", "summary",
              "blockquote")
TAG_BLOCK = re.compile(
    r"<(" + "|".join(PROSE_TAGS) + r")\b[^>]*>(.*?)</\1>", re.S | re.I)

CLAIM_FIELDS = ("quote", "speaker", "outlet", "tests", "intro", "since")


def _digest(text: str) -> str:
    """A short, stable id for a block, from its own text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


def _has_markup(text: str) -> bool:
    """Nested tags mean editing the text would mean editing HTML."""
    return bool(re.search(r"<[a-zA-Z/]", text))


def blocks() -> list[dict]:
    """Every editable block, in the order a reader meets it."""
    found: list[dict] = []

    sheet = ROOT / "forecast-sheet.html"
    if sheet.exists():
        body = sheet.read_text(encoding="utf-8")
        # Blank the generated regions so nothing inside them is offered.
        masked = GENERATED.sub(lambda m: " " * len(m.group(0)), body)
        for m in TAG_BLOCK.finditer(masked):
            inner = m.group(2).strip()
            if not inner or _has_markup(inner):
                continue
            text = re.sub(r"\s+", " ", inner)
            found.append({"source": "forecast-sheet.html", "kind": m.group(1),
                          "text": text, "id": _digest(text)})

    for md in sorted((ROOT / "docs-public").glob("*.md")):
        for para in re.split(r"\n\s*\n", md.read_text(encoding="utf-8")):
            para = para.strip()
            if not para or para.startswith(("<span", "</span", "<!--")):
                continue
            found.append({"source": f"docs-public/{md.name}", "kind": "md",
                          "text": para, "id": _digest(para)})

    claims = ROOT / "content" / "joburg" / "claims.toml"
    if claims.exists():
        raw = claims.read_text(encoding="utf-8")
        data = tomllib.loads(raw)
        for i, claim in enumerate(data.get("claim", [])):
            for field in CLAIM_FIELDS:
                val = claim.get(field)
                if not isinstance(val, str) or not val.strip():
                    continue
                found.append({"source": "content/joburg/claims.toml",
                              "kind": f"claim[{i}].{field}",
                              "text": val.strip(), "id": _digest(val.strip())})
            for j, step in enumerate(claim.get("steps", []) or []):
                found.append({"source": "content/joburg/claims.toml",
                              "kind": f"claim[{i}].steps[{j}]",
                              "text": step.strip(), "id": _digest(step.strip())})

    # ⛔ EVERY BLOCK GETS ITS OWN ID, even when two blocks say the same words.
    # The id is a digest of the text, so identical text collided — and a dict
    # keyed by it silently dropped one of the pair, so the export offered an
    # edit that `--apply` would have written to the wrong block or to neither.
    # The suffix makes the marker unique; whether the EDIT can be applied is a
    # separate question, answered by the uniqueness check in `apply`.
    seen: dict[str, int] = {}
    for b in found:
        seen[b["id"]] = seen.get(b["id"], 0) + 1
        if seen[b["id"]] > 1:
            b["id"] = f"{b['id']}-{seen[b['id']]}"
            b["repeated"] = True
    return found


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
        if b["id"] in dupes:
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
    found = {b["id"]: b for b in blocks()}
    edits = _parse_edits()
    unknown = sorted(set(edits) - set(found))
    if unknown:
        raise SystemExit(
            f"{len(unknown)} block id(s) in {OUT.name} are not in the sources: "
            f"{unknown[:5]}. The sources changed under the export — re-export, "
            f"re-apply your edits, and do not hand-edit the markers.")

    changes: list[tuple[dict, str]] = []
    for block_id, new_text in edits.items():
        old = found[block_id]
        if new_text == old["text"]:
            continue
        before, after = PLACEHOLDER.findall(old["text"]), PLACEHOLDER.findall(new_text)
        if sorted(before) != sorted(after):
            raise SystemExit(
                f"block {block_id} ({old['source']}, {old['kind']}) changed its "
                f"figures: {sorted(before)} -> {sorted(after)}.\n\n"
                f"Those are filled in from the run. Editing one publishes a "
                f"number nothing can trace back — CLAUDE.md §2. Put the "
                f"placeholders back, or say which number should move and it "
                f"moves where it is generated.")
        changes.append((old, new_text))

    if not changes:
        print("no edits to apply.")
        return 0

    for old, new_text in changes:
        path = ROOT / old["source"]
        body = path.read_text(encoding="utf-8")
        needle = old["text"]
        if old["source"] == "forecast-sheet.html":
            # The export collapsed whitespace; find the block by its own text
            # with whitespace made flexible, so the file's wrapping survives.
            pattern = re.compile(r"\s+".join(re.escape(w) for w in needle.split()))
            hits = list(pattern.finditer(body))
            if len(hits) != 1:
                raise SystemExit(
                    f"block {old['id']} matched {len(hits)} times in "
                    f"{old['source']}; refusing to guess which one you meant.")
            body = body[:hits[0].start()] + new_text + body[hits[0].end():]
        else:
            if body.count(needle) != 1:
                raise SystemExit(
                    f"block {old['id']} matched {body.count(needle)} times in "
                    f"{old['source']}; refusing to guess which one you meant.")
            body = body.replace(needle, new_text, 1)
        print(f"  {old['source']:32} {old['kind']:22} {old['id']}")
        if not dry_run:
            path.write_text(body, encoding="utf-8")

    verb = "would change" if dry_run else "changed"
    print(f"{verb} {len(changes)} block(s). "
          f"{'' if dry_run else 'Rebuild: .venv/bin/python src/build_all.py --city joburg'}")
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
