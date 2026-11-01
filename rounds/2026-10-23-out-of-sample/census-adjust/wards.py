"""Johannesburg wards (2021 map): Census 2022 group mix beside the evidence the
published criticism makes available. Read-only; writes wards.csv and summary.json here.

Columns, per 2021 ward:
  c22_*      Census 2022 Ward Statistical Product, all ages, four groups ("Other"
             dropped, renormalised) -- what the model reads.
  nat_*      the same with Moultrie & Dorrington's national overstatements removed
             (white -290,000 of 4,525,800; Indian/Asian -190,000 of 1,705,882),
             renormalised. A national correction, not a ward one.
  c11_*      Census 2011 by ward, all ages, moved onto the 2021 wards through VDs
             (pools.reproject: uniform within each 2011 ward, roll-weighted).
  c11a_*     the same for adults 18+.
  roll21     registered voters, 2021 LGE result file (vd_map).
  adults22   Census 2022 adults 18+ (20+ bands plus 2/5 of 15-19).
  ratio22    roll21 / adults22.
  ratio11    2011 LGE roll / Census 2011 adults per 2011 ward, moved onto 2021 wards.
  dratio     ratio22 - ratio11.
"""
import csv, json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
import openpyxl, cityconfig, pools

HERE = Path(__file__).resolve().parent
G = ["Black African", "Coloured", "Indian/Asian", "White"]
COV = ROOT / "data/raw/covariates/Ward Product_Locked spreadsheets"
city = cityconfig.load("joburg")

def sheet(name, sh):
    ws = openpyxl.load_workbook(COV / name, read_only=True, data_only=True)[sh]
    it = ws.iter_rows(values_only=True); head = next(it)
    return head, [r for r in it if str(r[0]).startswith("798") and len(str(r[0])) == 8]

head, rows = sheet("PP_Population Group_27-10-2025.xlsx", "Wards")
c22 = {str(r[0]): np.array([float(r[head.index(g)]) for g in G]) for r in rows}
head, rows = sheet("PP_Age Group_27-10-2025.xlsx", "Age_group")
adults22 = {str(r[0]): sum(float(r[head.index(b)]) for b in head[5:-1]) + 0.4 * float(r[head.index("15-19")]) for r in rows}

EXCESS = {"White": 290000 / 4525800, "Indian/Asian": 190000 / 1705882}
fac = np.array([1 - EXCESS.get(g, 0.0) for g in G])

c11, c11a = {}, {}
NAME = {"Indian or Asian": "Indian/Asian"}
for r in csv.DictReader(open(ROOT / "rounds/2026-10-23-out-of-sample/collection/census/census2011_ward_age_popgroup_long.csv")):
    w = r["ward"]
    if not w.startswith("798"): continue
    g = NAME.get(r["group"], r["group"])
    if g not in G: continue
    v = float(r["persons"]); i = G.index(g)
    c11.setdefault(w, np.zeros(4))[i] += v
    if r["age"].isdigit() and int(r["age"]) >= 18:
        c11a.setdefault(w, np.zeros(4))[i] += v

share = lambda d: {k: v / v.sum() for k, v in d.items() if v.sum() > 0}
s11, map11 = pools.reproject(share(c11), city, "2011", "2021")
s11a, _ = pools.reproject(share(c11a), city, "2011", "2021")

def roll(year):
    vw, reg = pools.vd_map(city, year); out = {}
    for vd, w in vw.items(): out[w] = out.get(w, 0.0) + reg.get(vd, 0.0)
    return out
roll11, roll21 = roll("2011"), roll("2021")
r11 = {w: np.array([roll11.get(w, 0.0) / c11a[w].sum()]) for w in c11a if c11a[w].sum() > 0}
rr11, _ = pools.reproject(r11, city, "2011", "2021")

out = []
for w in sorted(c22):
    s22 = c22[w] / c22[w].sum(); n = c22[w] * fac; n = n / n.sum()
    row = {"ward": w}
    for tag, v in (("c22", s22), ("nat", n), ("c11", s11.get(w)), ("c11a", s11a.get(w))):
        for g, x in zip(G, v if v is not None else [np.nan] * 4):
            row[f"{tag}_{g}"] = round(100 * float(x), 2)
    row["roll21"] = round(roll21.get(w, 0.0)); row["adults22"] = round(adults22.get(w, np.nan))
    row["ratio22"] = round(row["roll21"] / adults22[w], 3) if w in adults22 else None
    row["ratio11"] = round(float(rr11[w][0]), 3) if w in rr11 else None
    row["dratio"] = round(row["ratio22"] - row["ratio11"], 3) if row["ratio22"] is not None and row["ratio11"] is not None else None
    out.append(row)
with open(HERE / "wards.csv", "w", newline="") as f:
    wr = csv.DictWriter(f, fieldnames=list(out[0])); wr.writeheader(); wr.writerows(out)

# city level and checks
tot22 = sum(c22.values()); tot11 = sum(c11.values())
mv = lambda a, b: max(abs(r[f"{a}_{g}"] - r[f"{b}_{g}"]) for r in out for g in G if r[f"{b}_{g}"] == r[f"{b}_{g}"])
d = np.array([[r["c22_White"] - r["c11_White"], r["dratio"]] for r in out if r["dratio"] is not None])
summ = {
  "wards_2022": len(c22), "wards_2011": len(c11), "fraction_2021_roll_mapped_from_2011": round(map11, 4),
  "city_c22_pct": dict(zip(G, np.round(100 * tot22 / tot22.sum(), 2).tolist())),
  "city_c11_pct": dict(zip(G, np.round(100 * tot11 / tot11.sum(), 2).tolist())),
  "max_ward_shift_nat_vs_c22_pts": round(mv("nat", "c22"), 2),
  "max_ward_shift_c11_vs_c22_pts": round(mv("c11", "c22"), 2),
  "wards_ratio22_gt_1": [r["ward"] for r in out if r["ratio22"] and r["ratio22"] > 1],
  "city_roll21": round(sum(roll21.values())), "city_adults22": round(sum(adults22.values())),
  "city_roll11": round(sum(roll11.values())), "city_adults11": round(sum(v.sum() for v in c11a.values())),
  "corr_white_change_vs_dratio": round(float(np.corrcoef(d[:, 0], d[:, 1])[0, 1]), 3),
}
json.dump(summ, open(HERE / "summary.json", "w"), indent=1)
print(json.dumps(summ, indent=1))
