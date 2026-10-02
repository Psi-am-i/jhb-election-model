"""Refuse a Cloudflare deploy of a site whose numbers were not reviewed.

Wired as `[build] command` in `wrangler.toml`, so wrangler runs it before every
`deploy` and `versions upload` — the gate cannot be forgotten the way a flag on
`build_site.py --publish` can, because deploying is a separate command that
ships `site/` whatever the ledger says (blind review, 2026-09-17).

It checks that every file wrangler would upload from the repository's own
`site/` is committed (`untracked`), and two things against
`content/<city>/NUMBERS-REVIEW.md`:

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
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def untracked(site: Path, root: Path | None = None) -> list[str]:
    """Files under ``site`` that git does not track, as paths relative to it.

    ⛔ WRANGLER UPLOADS THE DIRECTORY, NOT THE COMMIT (code review, 2026-10-01).
    Two `.pyc` files written into `site/play/py/page/__pycache__/` by an
    ad-hoc import of the served Python were gitignored, so the runbook's
    `git status --short` stayed clean, and nothing here looked: they carried
    the machine's absolute path and would have been served. A file nobody
    committed is a file nobody reviewed, so it is refused here, whatever it is.
    `site/.assetsignore` is the second line (wrangler skips what it lists);
    this check does not rely on it.

    ``check`` runs it only for a ``site`` inside this repository: a test's
    temporary build has no git index to compare with. Raises if git cannot be asked: a gate that
    cannot look must not pass.
    """
    root = ROOT if root is None else root
    site, root = site.resolve(), root.resolve()
    rel = site.relative_to(root).as_posix()
    tracked = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--", rel],
                             check=True, capture_output=True).stdout.decode()
    tracked = {Path(t).relative_to(rel).as_posix() for t in tracked.split("\0") if t}
    on_disk = {f.relative_to(site).as_posix() for f in site.rglob("*") if f.is_file()}
    # Finder's .DS_Store is the one exception: `site/.assetsignore` lists it.
    return sorted(f for f in on_disk - tracked if Path(f).name != ".DS_Store")


def check(city: str, site: Path, preview: bool, review: Path | None = None) -> list[str]:
    review = review or ROOT / "content" / city / "NUMBERS-REVIEW.md"
    if not review.is_file():
        return [f"{review} does not exist — run build_site.py first"]
    text = review.read_text(encoding="utf-8")
    head = re.search(r"<!-- built-pages: (.*?) blocking=(\d+) -->", text)
    if not head:
        return [f"{review} carries no built-pages stamp — rebuild with build_site.py"]
    problems = []
    try:
        inside = site.resolve().is_relative_to(ROOT.resolve())
    except OSError:
        inside = False
    if inside:
        try:
            stray = untracked(site)
        except (OSError, subprocess.CalledProcessError) as exc:
            problems.append(f"cannot ask git which files under {site} are committed ({exc!r})")
        else:
            if stray:
                problems.append(
                    f"{len(stray)} file(s) under {site}/ are not committed, and wrangler "
                    f"uploads the directory: {', '.join(stray[:10])}"
                    f"{' …' if len(stray) > 10 else ''}. Commit them or delete them.")
    for pair in head.group(1).split():
        page, sha = pair.split("=", 1)
        f = site / page
        if not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest() != sha:
            problems.append(f"site/{page} is not the page the review scanned — rebuild")
    # ⛔ A PAGE THE REVIEW NEVER SCANNED IS A PAGE THIS GATE CANNOT SEE.
    # `wrangler.toml` ships `directory = "./site"` wholesale, so every .html in
    # there reaches a reader, while the loop above only checks the ones named in
    # the review's stamp. `portal.html` — the apex page — was outside it, and on
    # 2026-09-27 it went a whole batch without being regenerated: it would have
    # shipped claiming sliders that do not exist, and nothing here would have
    # objected. Check 1 was real for eight pages and blind to the ninth.
    #
    # RECURSIVE since 2026-09-30 (blind review B2): the interactive ships pages
    # below the root (`/play/`, `/f/`), and a top-level glob could not see them.
    # Stamp keys are paths relative to site/, so `play/index.html` is a key.
    stamped = {pair.split("=", 1)[0] for pair in head.group(1).split()}
    unscanned = sorted(rel for rel in (f.relative_to(site).as_posix()
                                       for f in site.rglob("*.html"))
                       if rel not in stamped)
    if unscanned:
        problems.append(
            f"{len(unscanned)} page(s) ship from {site}/ that the number review "
            f"never scanned: {', '.join(unscanned)}. Either build them through "
            f"build_site.py so they enter the stamp, or move them out of the "
            f"directory wrangler deploys — a page nobody checked is a page "
            f"nobody can vouch for.")
    # ⛔ THE SHIPPED `_headers` MUST BE THE ONE THE CODE GENERATES (deploy
    # review, 2026-09-30). `build_site.headers_text()` was corrected in 34297da
    # and `site/_headers` was not rewritten, so every non-HTML file would have
    # gone out as text/html while every test passed on the generator alone.
    headers = site / "_headers"
    try:
        import build_site as _B
        want = _B.headers_text()
    except Exception as exc:          # a gate that cannot look must not pass
        problems.append(f"cannot generate the expected _headers ({exc!r})")
    else:
        if not headers.is_file() or headers.read_text(encoding="utf-8") != want:
            problems.append(
                f"{headers} is not what build_site.headers_text() generates — "
                f"rewrite it (only that file; a full build strips a published "
                f"edition's arrows)")
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
