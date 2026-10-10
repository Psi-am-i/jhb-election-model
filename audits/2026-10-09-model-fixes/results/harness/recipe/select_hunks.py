"""Build a patch from 0-based hunk indices of a git-show diff (split at each @@ line)."""
import sys
src, out, idx = sys.argv[1], sys.argv[2], {int(x) for x in sys.argv[3].split(",")}
lines = open(src).read().splitlines(keepends=True)
files = []  # (header_lines, [hunks])
cur = None
for ln in lines:
    if ln.startswith("diff --git"):
        cur = [[ln], []]; files.append(cur); continue
    if cur is None:
        continue
    if ln.startswith("@@"):
        cur[1].append([ln]); continue
    if cur[1]:
        cur[1][-1].append(ln)
    else:
        cur[0].append(ln)
n = 0; outl = []
for hdr, hunks in files:
    keep = []
    for h in hunks:
        if n in idx: keep.append(h)
        n += 1
    if keep:
        outl += hdr
        for h in keep: outl += h
open(out, "w").write("".join(outl))
print("hunks total", n)
