"""Probe: observed pairs (ward-ballot vote share, share of wards won) per party, metro LGE city-years."""
import csv, glob, collections, sys
rows = []
for path in sorted(glob.glob(sys.argv[1] + "/lge*_*_vd_party_clean.csv")):
    tag = path.split("/")[-1][:11]
    by_ward = collections.defaultdict(collections.Counter); tot = collections.Counter()
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["BallotType"].strip().upper() != "WARD": continue
            v = int(r["Party_Votes"]); by_ward[r["Ward"]][r["sPartyName"]] += v; tot[r["sPartyName"]] += v
    W = len(by_ward); T = sum(tot.values())
    wins = collections.Counter(max(c, key=c.get) for c in by_ward.values())
    for p, n in wins.items():
        rows.append((tag, p[:30], tot[p] / T * 100, n / W * 100, n / W / (tot[p] / T)))
print("city-years:", len({r[0] for r in rows}), "party-rows with >=1 ward:", len(rows))
print("max ratio wards%/vote%:"); [print(" ", r) for r in sorted(rows, key=lambda r: -r[4])[:6]]
print("max gap wards% - vote% (pp):"); [print(" ", r) for r in sorted(rows, key=lambda r: -(r[3]-r[2]))[:6]]
