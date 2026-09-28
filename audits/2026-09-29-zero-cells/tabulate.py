"""Summarise results/*.json from zero_cells.py. Prints; writes nothing."""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

R = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "results")
panel = [l.split() for l in (R / "panel.txt").read_text().split("\n") if l.strip()]
tot = Counter()
by_party = defaultdict(lambda: Counter())
by_cy = []
univ_min = []
hz = []
for c, y in panel:
    d = json.loads((R / f"{c}-{y}.json").read_text())
    assert d["draws"] >= 1000 and d["control"] == "none"
    cells = [x for x in d["zero_cells"] if x["party"] != "ZC_CONTROL"]
    ctrl = [x for x in d["zero_cells"] if x["party"] == "ZC_CONTROL"]
    assert len(ctrl) == 2, (c, y)
    row = {"cy": f"{c} {y}", "draws": d["draws"],
           "unmatched": sum(len(v) for v in d["unmatched_actual_wards"].values()),
           "relabel": d["relabel_entrant"]}
    for b in ("PR", "Ward"):
        cb = [x for x in cells if x["ballot"] == b]
        row[b] = len(cb)
        row[b + "_votes"] = sum(x["votes"] for x in cb)
        row[b + "_scanned"] = d["cells_scanned"][b]
        row[b + "_why"] = dict(Counter(x["why"] for x in cb))
    for x in cells:
        k = (x["party"], x["why"], x["named_in_spec"])
        by_party[k]["cells_" + x["ballot"]] += 1
        by_party[k]["votes_" + x["ballot"]] += x["votes"]
        by_party[k]["cy:" + f"{c} {y}"] = 1
        tot[(x["ballot"], x["why"])] += 1
        tot[("votes", x["ballot"], x["why"])] += x["votes"]
    by_cy.append(row)
    # floor seen by universe parties: min over wards of max share
    for b in ("W", "PR"):
        m = d["min_over_wards_of_max_share"][b]
        p = min(m, key=m.get)
        univ_min.append((m[p], f"{c} {y}", b, p))
    # universe parties that carry a hard pool zero in this spec
    spec = json.loads(Path(d["spec"]).read_text())
    pools = spec["pools"]
    for p in d["universe"]:
        z = [g for g in pools if float(pools[g]["members"].get(p, 0.0)) == 0.0]
        named = any(p in pools[g]["members"] for g in pools)
        if named and z:
            hz.append((f"{c} {y}", p, len(z), len(pools),
                       d["min_over_wards_of_max_share"]["W"][p],
                       d["min_over_wards_of_max_share"]["PR"][p]))

print("PER CITY-YEAR (cells with model max share < 1e-12 and actual share > 0)")
print(f"{'city-year':24s} {'draws':>5s} {'PR':>5s} {'PRvotes':>8s} {'Ward':>5s} {'Wvotes':>8s}  why")
for r in by_cy:
    print(f"{r['cy']:24s} {r['draws']:5d} {r['PR']:5d} {r['PR_votes']:8d} {r['Ward']:5d} "
          f"{r['Ward_votes']:8d}  PR {r['PR_why']} W {r['Ward_why']} unmatched={r['unmatched']} relabel={r['relabel']}")
print("\nTOTALS", dict(tot))
print("\nBY PARTY (party, why, named in spec)")
rows = sorted(by_party.items(), key=lambda kv: -(kv[1]["votes_PR"] + kv[1]["votes_Ward"]))
for (p, why, named), v in rows:
    cys = sorted(k[3:] for k in v if k.startswith("cy:"))
    print(f"{p:45s} {why:16s} named={named!s:5s} PR {v['cells_PR']:4d}/{v['votes_PR']:7d}  "
          f"W {v['cells_Ward']:4d}/{v['votes_Ward']:7d}  in {len(cys)}: {', '.join(cys)}")
print("\nSMALLEST max-over-draws ward share of ANY universe party, per city-year/ballot")
for m, cy, b, p in sorted(univ_min)[:10]:
    print(f"  {m:.3e} {cy} {b} {p}")
print(f"  largest of these minima: {max(univ_min)[0]:.3e}")
print(f"\nUNIVERSE PARTIES WITH A HARD POOL ZERO: {len(hz)} party-city-years")
print("  smallest min-over-wards max share (Ward, PR):",
      f"{min(h[4] for h in hz):.3e}", f"{min(h[5] for h in hz):.3e}")
for h in sorted(hz, key=lambda h: h[4])[:8]:
    print("  ", h)
