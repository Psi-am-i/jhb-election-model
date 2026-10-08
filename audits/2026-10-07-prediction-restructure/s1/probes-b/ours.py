"""Probe: does a rule-A-like prediction (modal wards from site/draws, mean LIST share standing in for the
unexported ward share) sit inside the Amendment-1 bounds? Approximate: the ward block is not served."""
import csv, json, sys, collections
from pathlib import Path
import numpy as np
root = Path(sys.argv[1]); sys.path.insert(0, str(root / "src"))
import reweight, cityconfig, montecarlo as M, score_forecasts as SF
man = json.loads((root / "site/draws/manifest.json").read_text()); arr = reweight.unpack((root / "site/draws/base.bin").read_bytes(), man)
cols = lambda n: next(b for b in man["blocks"] if b["name"] == n)["columns"]
wards = cols("ward_winner"); codes = man["ward_parties"]; W = np.asarray(arr["ward_winner"], dtype=int)
calls = [codes[np.bincount(W[:, j], minlength=len(codes)).argmax()] for j in range(len(wards))]
pr = np.asarray(arr["pr_share"], dtype=float); share = dict(zip(cols("pr_share"), pr.mean(axis=0)))
c = cityconfig.use("joburg"); t = cityconfig.use_target("2026")
parts, _ = M.ward_parts(t, root / "data/raw/elections", root / "data/processed")
vd = {}
for r in csv.DictReader(open(root / "data/raw/elections/lge2021_JHB_vd_party_clean.csv", newline="", encoding="utf-8")):
    if r["BallotType"].strip().upper() == "WARD" and r["VD_Number"] not in vd:
        vd[r["VD_Number"]] = (int(float(r["Registered_Population"] or 0)), int(r["Total_Valid_Votes"]))
reg = collections.Counter(); cast = collections.Counter()
for v, w, n in parts:
    if v in vd and vd[v][0]: reg[w] += n; cast[w] += n * vd[v][1] / vd[v][0]
roll = {SF.ward_number(r["Ward"], c.ward_prefix): int(r["Registered"]) for r in csv.DictReader(open(root / "archive/iec-registration-2026-09-26/joburg_ward_registration_2026-09-26.csv"))}
E = {w: roll[w] * cast[w] / reg[w] for w in wards}; S = sum(E.values()); e = {w: E[w] / S for w in wards}
won = collections.Counter()
for w, p in zip(wards, calls): won[p] += e[w]
for qname, q in (("min", 0.2362), ("p01", 0.3514), ("p05", 0.4373)):
    bad = {p: (round(q * won[p] * 100, 2), round(share[p] * 100, 2)) for p in won if share[p] < q * won[p]}
    print(qname, "parties below floor (floor%, share%):", bad)
rmax = 0.4776
over = {p: round(s * 100, 2) for p, s in share.items() if s > rmax * (1 - won[p]) + won[p]}
print("above ceiling:", over)
print("won e by party:", {p: round(v * 100, 1) for p, v in won.items()})
