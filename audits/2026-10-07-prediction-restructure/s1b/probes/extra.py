"""Widths of the citywide limits given the real winners (top 4 parties per
city-year), unpaintable (ward, party) pairs in 2026, and LP size and time."""
import json, collections, time, sys
sys.path.append("pylib")
import b2bt as B, ours as O
from ward_poly import ward_range
from load import CITIES
rows = collections.defaultdict(list)
for stat, comb in [("ext", False), ("ext", True), ("p01", True), ("p05", True)]:
    for T in ["2011", "2016", "2021"]:
        for c in CITIES:
            r = B.city_year(c, T, stat, combine=comb)
            for p, (fl, V, ce, sf, sc) in r["width_big"].items():
                if V >= 5:
                    rows[stat + ("+sb" if comb else "")].append((ce - fl, sc - sf, fl, sf, V))
for k, v in rows.items():
    n = len(v)
    print(f"{k}: party-city-years with >=5% ward vote among top 4: {n}; mean width {sum(x[0] for x in v)/n:.1f} pts "
          f"(slice B {sum(x[1] for x in v)/n:.1f}); mean floor {sum(x[2] for x in v)/n:.1f} (slice B {sum(x[3] for x in v)/n:.1f}); "
          f"floor above slice B's in {sum(1 for x in v if x[2] > x[3] + 0.05)}")
# unpaintable pairs, 2026, ext+sb
for stat in ["ext", "p01", "p05"]:
    per, qw, qr, D, N = O.build(stat, True)
    bad = collections.Counter()
    for w in O.wards:
        for W in O.codes:
            lo, hi = dict(per[w][0]), dict(per[w][1])
            if hi[W] >= qw: lo[W] = max(lo[W], qw)
            for p in O.codes:
                if p != W: hi[p] = max(lo[p], min(hi[p], qr))
            ok, _, _ = ward_range(O.codes, lo, hi, W)
            if not ok: bad[W] += 1
    print(f"2026 {stat}+sb: (ward, party) pairs a reader could not paint within the ranges: {sum(bad.values())} of {len(O.wards)*len(O.codes)}; by party (top): {bad.most_common(5)}")
per, qw, qr, D, N = O.build("ext", True); pm = O.apply_map(per, O.calls, qw, qr, True)
t = time.time(); s = B.joint_lp(O.codes, O.wards, pm, O.calls, O.e, O.VA); print(f"joint LP rule A: slack {s}, {time.time()-t:.2f}s native HiGHS incl. matrix build (python)")
# coupling rows that can bind: hi_q > lo_W
nb = sum(1 for w in O.wards for q in O.codes if q != O.calls[w] and pm[w][1][q] > pm[w][0][O.calls[w]])
print("coupling rows:", len(O.wards) * (len(O.codes) - 1), "of which can bind (hi_q > lo_winner):", nb)
