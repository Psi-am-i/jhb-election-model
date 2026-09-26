"""Enter what the live site published, so a change is measured against it.

Owner, 2026-09-26: *"change must always be against previously published
number."* The ledger started empty while the site did not, so the first
`--publish` would have entered all 318 tokens as first-published and told
readers every figure was new. This enters the figures the live pages actually
showed, keyed to their archived bytes, and after it a change is a change.

⛔ ONE-OFF, and deliberately not wired into `build_site`, which never calls
`backfill()` (see `publication.backfill`'s docstring for why that separation is
the point). Run it once against the real ledger, then leave it as the record of
how those rows got there.

    python audits/2026-09-26-ledger-backfill/backfill_live.py --ledger-root <scratch>   # rehearse
    python audits/2026-09-26-ledger-backfill/backfill_live.py                           # the real one

The pages are `archive/live-2026-08-07/`, with their sha256 in MANIFEST.md.
Every row's `as_of` is the page's own `data-when`, never the file's mtime.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import publication  # noqa: E402

PAGES = ROOT / "archive" / "live-2026-08-07"
SPAN = re.compile(r'<span[^>]*data-token="([^"]+)"[^>]*>(.*?)</span>', re.S)
ATTRS = re.compile(r'(data-when|data-live|data-mode)="([^"]*)"')
SOURCE = re.compile(r'source:\s*([^"]+)"')
TAGS = re.compile(r"<[^>]+>")


def _raw(display: str, fmt: str | None):
    """The reader's string back to the number the ledger stores.

    `publication.display_scale` is the same function the build uses to take a raw value the
    other way, so the two cannot drift: a `chance` token shows 62% and stores
    0.62, and inverting with any other constant would make every percentage
    read as moved.
    """
    text = display.strip().replace(",", "").rstrip("%")
    try:
        number = float(text)
    except ValueError:
        return display.strip()
    scale = publication.display_scale(fmt) if fmt else 1.0
    value = number / scale if scale else number
    return int(value) if float(value).is_integer() and (scale or 1) == 1 else value


def rows(registry: dict) -> tuple[list, list]:
    out, skipped = [], []
    # ONE ROW PER TOKEN ACROSS THE WHOLE SITE, not per page. `bloc_leak_votes`
    # appears on the front page and in the methodology; it is one published
    # figure, and two first-publication rows for it would make the second a
    # duplicate the ledger can never take back.
    claimed: set[str] = set()
    for page in sorted(PAGES.glob("*.html")):
        text = page.read_text(encoding="utf-8", errors="replace")
        ident = publication.preledger_identity(page.relative_to(ROOT))
        seen = set()
        for match in SPAN.finditer(text):
            token, body = match.group(1), match.group(2)
            if token in seen or token in claimed:
                continue
            seen.add(token)
            claimed.add(token)
            attrs = dict(ATTRS.findall(match.group(0)))
            display = (attrs.get("data-live")
                       or TAGS.sub("", body).strip().split("\n")[0]).strip()
            entry = registry.get(token) if isinstance(registry.get(token), dict) else {}
            fmt = entry.get("format")
            source = entry.get("source") or ""
            if not source:
                found = SOURCE.search(match.group(0))
                source = found.group(1).strip() if found else "external:the live page"
            if not display:
                skipped.append((token, page.name, "no display value on the page"))
                continue
            out.append(publication.Row(
                token=token, value=_raw(display, fmt), display=display,
                fmt=fmt, source=source,
                model_run_id=ident["model_run_id"], run_at=ident["run_at"],
                # The page's own statement of what the model knew. Not the
                # file's mtime, which says when the bytes were copied.
                as_of=attrs.get("data-when") or None,
                published_at=_dt.datetime.now(_dt.timezone.utc)
                                .replace(microsecond=0).isoformat(),
                change_class=None, reason=None, movement="new",
                provenance=ident["provenance"]))
    return out, skipped


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--city", default="joburg")
    ap.add_argument("--ledger-root", type=Path, default=None,
                    help="a throwaway ledger to rehearse against; the real one "
                         "is append-only and cannot be rewritten")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the rows and write nothing")
    args = ap.parse_args(argv)

    registry = tomllib.loads(
        (ROOT / "content" / args.city / "stats.toml").read_text(encoding="utf-8"))
    batch, skipped = rows(registry)
    by_page: dict[str, int] = {}
    for row in batch:
        page = row.provenance["reconstructed_from"]["page"]
        by_page[page] = by_page.get(page, 0) + 1
    for page, n in sorted(by_page.items()):
        print(f"  {n:3d} token(s) from {page}")
    for token, page, why in skipped:
        print(f"  skipped {token} on {page}: {why}")
    if args.dry_run:
        for row in sorted(batch, key=lambda r: r.token):
            print(f"    {row.token:30s} {row.display:>12s}  value={row.value!r} "
                  f"fmt={row.fmt} as_of={row.as_of}")
        return 0
    n = publication.backfill(args.city, batch, root=args.ledger_root)
    where = args.ledger_root or "publications/ (THE REAL LEDGER)"
    print(f"\nbackfilled {n} row(s) -> {where}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
