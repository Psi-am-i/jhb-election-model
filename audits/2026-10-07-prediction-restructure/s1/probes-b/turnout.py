"""Probe: 2026 ward parts (montecarlo.ward_parts) covered by 2021 VD ward-ballot turnout; roll agreement."""
import csv, sys, collections
from pathlib import Path
root = Path(sys.argv[1]); sys.path.insert(0, str(root / "src"))
import cityconfig, montecarlo as M
c = cityconfig.use("joburg"); t = cityconfig.use_target("2026")
parts, label = M.ward_parts(t, root / "data" / "raw" / "elections", root / "data" / "processed")
print(label)
vd = {}
with open(root / "data/raw/elections/lge2021_JHB_vd_party_clean.csv", newline="", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if r["BallotType"].strip().upper() == "WARD" and r["VD_Number"] not in vd:
            reg = int(float(r["Registered_Population"] or 0)); val = int(r["Total_Valid_Votes"])
            vd[r["VD_Number"]] = (reg, val)
miss = [p for p in parts if p[0] not in vd]
print("parts", len(parts), "vds", len({p[0] for p in parts}), "parts with no 2021 VD", len(miss), "their registration", sum(p[2] for p in miss), "of", sum(p[2] for p in parts))
ward_reg = collections.Counter(); ward_cast = collections.Counter()
for v, w, reg in parts:
    if v in vd and vd[v][0]:
        ward_reg[w] += reg; ward_cast[w] += reg * vd[v][1] / vd[v][0]
tos = sorted(ward_cast[w] / ward_reg[w] for w in ward_reg)
print("wards", len(ward_reg), "turnout min/median/max", round(tos[0], 3), round(tos[len(tos)//2], 3), round(tos[-1], 3))
roll = {r["Ward"]: int(r["Registered"]) for r in csv.DictReader(open(root / "archive/iec-registration-2026-09-26/joburg_ward_registration_2026-09-26.csv"))}
ids = sorted(ward_reg)[:3]; print("ward id forms", ids, list(roll)[:3])
