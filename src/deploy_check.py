"""Refuse a Cloudflare deploy of a site whose numbers were not reviewed.

Wired as `[build] command` in `wrangler.toml`, so wrangler runs it before every
`deploy` and `versions upload` — the gate cannot be forgotten the way a flag on
`build_site.py --publish` can, because deploying is a separate command that
ships `site/` whatever the ledger says (blind review, 2026-09-17).

It checks two things against `content/<city>/NUMBERS-REVIEW.md`:

1. the review describes THESE pages — the sha256 of every page it scanned
   matches the file about to ship, so an old review cannot clear a new build;
2. it lists no `BLOCKS` row.

A preview upload may ship unreviewed numbers, because showing them is what a
preview is for: set `JHB_PREVIEW=1`. Check 1 still applies to a preview.

    .venv/bin/python src/deploy_check.py [--city joburg]
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(city: str, site: Path, preview: bool, review: Path | None = None) -> list[str]:
    review = review or ROOT / "content" / city / "NUMBERS-REVIEW.md"
    if not review.is_file():
        return [f"{review} does not exist — run build_site.py first"]
    text = review.read_text(encoding="utf-8")
    head = re.search(r"<!-- built-pages: (.*?) blocking=(\d+) -->", text)
    if not head:
        return [f"{review} carries no built-pages stamp — rebuild with build_site.py"]
    problems = []
    for pair in head.group(1).split():
        page, sha = pair.split("=", 1)
        f = site / page
        if not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest() != sha:
            problems.append(f"site/{page} is not the page the review scanned — rebuild")
    blocks = sum(1 for line in text.splitlines() if line.startswith("| BLOCKS |"))
    if blocks != int(head.group(2)):
        problems.append(f"{review} was edited by hand: stamp says "
                        f"{head.group(2)} blocking, the table lists {blocks}")
    if blocks and not preview:
        problems.append(f"{blocks} number(s) on the site are neither tokens nor "
                        f"registered fixed facts — see {review}")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--city", default="joburg")
    args = ap.parse_args(argv)
    preview = os.environ.get("JHB_PREVIEW") == "1"
    problems = check(args.city, ROOT / "site", preview)
    for p in problems:
        print(f"deploy_check: ✗ {p}", file=sys.stderr)
    if problems:
        return 1
    print(f"deploy_check: ✓ site/ matches its number review"
          f"{' (preview: unreviewed numbers allowed)' if preview else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
