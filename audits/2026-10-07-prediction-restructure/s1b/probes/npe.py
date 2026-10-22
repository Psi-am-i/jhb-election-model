"""SPEC-B2r2 probe: the national-to-local change. Each NPE (2004, 2009, 2014,
2019) is joined to the next LGE's wards by VD number (the LGE's own VD->ward,
VDs whole), and to the city. 1999 is an approximation file and is left out.
Stood both = a vote in the NPE and a ward vote at the LGE."""
import collections, csv, os, pickle, statistics
from load import EL, CITIES, all_data, ward_shares, prior_on, parts_of, parts_2026, SCRATCH
import parties

PAIRS = [("2004", "2006"), ("2009", "2011"), ("2014", "2016"), ("2019", "2021")]
EDGES = [0.0, 0.01, 0.05, 0.15, 0.35, 0.60, 1.0001]
def bin_of(h):
    for i in range(len(EDGES) - 1):
        if h <= EDGES[i + 1]: return i

def read_npe(city, year):
    vds = {}
    with open(f"{EL}/npe{year}_{city}_vd_party.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            d = vds.setdefault(r["VD_Number"].strip(), {"ward": "", "reg": int(float(r["Registered_Population"] or 0)),
                                                       "wv": collections.Counter()})
            d["wv"][parties.canonical(r["sPartyName"])] += int(r["Party_Votes"])
    return vds

def npe_all():
    p = SCRATCH + "/npe_cache.pkl"
    if os.path.exists(p): return pickle.load(open(p, "rb"))
    d = {(c, y): read_npe(c, y) for c in CITIES for y in ["2004", "2009", "2014", "2019", "2024"]}
    pickle.dump(d, open(p, "wb")); return d

def city_of(vds):
    acc = collections.Counter()
    for d in vds.values(): acc.update(d["wv"])
    t = sum(acc.values()); return {p: v / t for p, v in acc.items() if v}

N = npe_all(); L = all_data()
ward_rows, city_rows = [], []
for c in CITIES:
    for n, l in PAIRS:
        lv = L[(c, l)][0]
        h, cov, _ = prior_on(parts_of(lv), N[(c, n)])
        s, tot, _ = ward_shares(lv)
        Hn = city_of(N[(c, n)])
        A = sum(tot.values()); V = collections.Counter()
        for w in s:
            for p, v in s[w].items(): V[p] += tot[w] / A * v
        for p in set(Hn) & set(V):
            if p != "IND": city_rows.append((c, n, l, p, Hn[p], V[p]))
        for w in s:
            if w not in h: continue
            for p in set(h[w]) & set(s[w]):
                if p != "IND": ward_rows.append((c, n, l, w, p, h[w][p], s[w][p]))

def q(xs, f): xs = sorted(xs); return xs[int(round(f * (len(xs) - 1)))]
if __name__ == "__main__":
    print("files: npe2004/2009/2014/2019/2024 for all 8 metros; npe1999_approx left out")
    print("\ncitywide: LGE ward share - NPE share, stood both, 32 pairs, by NPE share")
    by = collections.defaultdict(list)
    for r in city_rows: by[bin_of(r[4])].append(r)
    for b in sorted(by):
        d = [100 * (r[5] - r[4]) for r in by[b]]; rat = [r[5] / r[4] for r in by[b]]
        lo = min(by[b], key=lambda r: r[5] - r[4]); hi = max(by[b], key=lambda r: r[5] - r[4])
        print(f"  ({EDGES[b]:.2f},{EDGES[b+1]:.2f}] n={len(d)} diff median {statistics.median(d):.2f} mean {statistics.mean(d):.2f} "
              f"min {min(d):.1f} {lo[:4]} max {max(d):.1f} {hi[:4]} | ratio median {statistics.median(rat):.2f}")
    print("\nward level: LGE ward share - NPE share in the ward, stood both, by NPE ward share")
    bw = collections.defaultdict(list)
    for r in ward_rows: bw[bin_of(r[5])].append(r[6] - r[5])
    for b in sorted(bw):
        d = [100 * x for x in bw[b]]
        print(f"  ({EDGES[b]:.2f},{EDGES[b+1]:.2f}] n={len(d)} median {statistics.median(d):.2f} min {min(d):.1f} p01 {q(d,.01):.1f} p99 {q(d,.99):.1f} max {max(d):.1f}")
    # the parties new to local in 2026 Joburg: no 2021 LGE ward vote, a 2024 NPE vote
    l21 = L[("JHB", "2021")][0]; stood21 = {p for d in l21.values() for p, v in d["wv"].items() if v}
    n24 = city_of(N[("JHB", "2024")])
    import json
    F = json.load(open("/Users/simondavis/projects/atlas-jhb-election-model/site/your-forecast/forecast.json"))
    codes = F["schema"]["x-seat-context"]["parties"]
    new_local = sorted((p for p in codes if p not in stood21 and n24.get(p, 0) > 0), key=lambda p: -n24[p])
    print("\n2026 roster parties new to local in Joburg with a 2024 NPE vote:", len(new_local),
          [(p, round(100 * n24[p], 2)) for p in new_local[:8]])
    print("2026 roster parties with neither:", sorted(p for p in codes if p not in stood21 and n24.get(p, 0) == 0)[:10], "...",
          len([p for p in codes if p not in stood21 and n24.get(p, 0) == 0]))
