"""Back up every gitignored file, because git will not.

    .venv/bin/python src/backup_ignored.py            # back up now
    .venv/bin/python src/backup_ignored.py --list     # what would be backed up
    .venv/bin/python src/backup_ignored.py --restore <name>

⛔ THE LOSS THIS EXISTS FOR, 2026-09-27. `build_validation.py` was run to
regenerate a page and it overwrote `data/processed/validation_2021.json` — the
11 August run the published track record was built from. `data/**` is
gitignored, so there was no copy anywhere: not in git, not in `archive/`. The
published FIGURES survived only because the page generated from it is committed.

The project already knew: `MEMORY.md` carries "gitignored is not unimportant —
montecarlo.py --run-dir overwrote the published forecast; data/** is ignored so
nothing warned." Knowing was not enough, because nothing took a copy.

**What this does.** Copies every file git ignores into `backups/<timestamp>/`,
preserving paths, and writes a manifest with each file's sha256 so a restore can
be verified rather than hoped. The backup directory is itself gitignored — this
is protection against overwriting, not a second copy in the repository.

⚠️ **It is not a substitute for archiving a deliberate artefact.** `archive/`
holds things kept ON PURPOSE, with a README saying what they are. This holds
everything, indiscriminately, so that a mistake is recoverable. The two answer
different questions and neither replaces the other.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUPS = ROOT / "backups"

#: Never copied: enormous, reproducible from the network, or noise.
SKIP_PREFIXES = (".venv/", "node_modules/", "backups/", ".git/", "__pycache__/")
SKIP_SUFFIXES = (".pyc", ".pyo")


def ignored_files() -> list[Path]:
    """Every file git ignores, from git itself rather than by parsing .gitignore."""
    out = subprocess.run(
        ["git", "ls-files", "--others", "--ignored", "--exclude-standard"],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout
    keep = []
    for line in out.splitlines():
        if not line or line.endswith("/"):
            continue
        if line.startswith(SKIP_PREFIXES) or line.endswith(SKIP_SUFFIXES):
            continue
        p = ROOT / line
        if p.is_file():
            keep.append(p)
    return sorted(keep)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list", action="store_true", help="print what would be copied and stop")
    ap.add_argument("--restore", metavar="STAMP", help="restore from backups/<STAMP>")
    ap.add_argument("--keep", type=int, default=10, help="how many backups to keep (default 10)")
    args = ap.parse_args(argv)

    if args.restore:
        src = BACKUPS / args.restore
        manifest = json.loads((src / "MANIFEST.json").read_text())
        bad = []
        for rel, want in manifest["files"].items():
            f = src / rel
            if not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest() != want:
                bad.append(rel)
        if bad:
            print(f"REFUSING: {len(bad)} file(s) in the backup do not match its manifest")
            for b in bad[:5]:
                print(f"  {b}")
            return 1
        for rel in manifest["files"]:
            dest = ROOT / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src / rel, dest)
        print(f"restored {len(manifest['files'])} file(s) from {args.restore}")
        return 0

    files = ignored_files()
    total = sum(f.stat().st_size for f in files)
    if args.list:
        for f in files[:40]:
            print(f"  {f.stat().st_size/1048576:8.2f} MB  {f.relative_to(ROOT)}")
        print(f"\n{len(files)} file(s), {total/1073741824:.2f} GB")
        return 0

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    dest = BACKUPS / stamp
    manifest = {"taken": stamp, "root": str(ROOT), "files": {}}
    for f in files:
        rel = str(f.relative_to(ROOT))
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
        manifest["files"][rel] = hashlib.sha256(f.read_bytes()).hexdigest()
    (dest / "MANIFEST.json").write_text(json.dumps(manifest, indent=1))
    print(f"backed up {len(files)} file(s), {total/1073741824:.2f} GB -> backups/{stamp}")

    old = sorted(d for d in BACKUPS.iterdir() if d.is_dir())
    for d in old[:-args.keep]:
        shutil.rmtree(d)
        print(f"  pruned {d.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
