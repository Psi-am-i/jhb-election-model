"""Probe for Amendment 1: winning/runner-up ward shares and ward-list gaps, metro LGE files."""
import csv, glob, collections, sys
win, run, top = [], [], []
gaps = []
for path in sorted(glob.glob(sys.argv[1] + "/lge*_*_vd_party_clean.csv")):
    tag = path.split("/")[-1][:11]
    wv = collections.defaultdict(collections.Counter); W = collections.Counter(); P = collections.Counter()
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            b = r["BallotType"].strip().upper(); v = int(r["Party_Votes"]); p = r["sPartyName"]
            if b == "WARD": wv[r["Ward"]][p] += v; W[p] += v
            elif b == "PR": P[p] += v
    for w, c in wv.items():
        t = sum(c.values()); s = sorted(c.values(), reverse=True)
        if t: win.append((s[0] / t, tag, w)); run.append(((s[1] if len(s) > 1 else 0) / t, tag, w))
    tw, tp = sum(W.values()), sum(P.values())
    for p in set(W) | set(P):
        if P[p] > 0 and W[p] > 0 and "INDEPENDENT" not in p.upper():
            gaps.append(((P[p] / tp - W[p] / tw) * 100, tag, p[:28], W[p] / tw * 100))
def q(xs, f): xs = sorted(xs); return xs[int(f * (len(xs) - 1))]
ws = [x[0] for x in win]; rs = [x[0] for x in run]
print("wards:", len(win), "city-years:", len({x[1] for x in win}))
print("winning share: min", min(win)[:3], "p01", round(q(ws, .01), 4), "p05", round(q(ws, .05), 4), "max", max(win)[:3])
print("runner-up share: max", max(run)[:3], "p99", round(q(rs, .99), 4))
g = [x[0] for x in gaps]
print("party gaps (list% - ward%), n", len(gaps), "min", min(gaps), "max", max(gaps))
print("  p01", round(q(g, .01), 2), "p99", round(q(g, .99), 2))
big = [x for x in gaps if x[3] >= 1]
print("  parties >=1% ward: min", min(big), "max", max(big))
jhb = [x for x in gaps if "JHB" in x[1] and x[3] >= 1]
print("  JHB >=1%: min", min(jhb), "max", max(jhb))
