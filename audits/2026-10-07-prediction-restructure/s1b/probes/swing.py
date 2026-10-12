"""Probe: VD continuity between consecutive LGEs, and the ward-share swing
distribution by starting share, over every metro transition."""
import collections, json, sys
from load import all_data, ward_shares, prior_on, parts_of, CITIES, YEARS, SCRATCH

BINS = [0.0, 1e-9, 0.01, 0.05, 0.10, 0.20, 0.35, 0.50, 0.65, 0.80, 1.0001]
def bin_of(h):
    for i in range(len(BINS) - 1):
        if BINS[i] <= h < BINS[i + 1]:
            return i
    return len(BINS) - 2

data = all_data()
rows = []  # (city, a, b, ward, party, h, s)
cover = []
for c in CITIES:
    for a, b in zip(YEARS, YEARS[1:]):
        prev, _ = data[(c, a)]; cur, _ = data[(c, b)]
        h, cov, _t = prior_on(parts_of(cur), prev)
        s, tot, reg = ward_shares(cur)
        m = sum(v[0] for v in cov.values()); t = sum(v[1] for v in cov.values())
        nowards = [w for w in s if w not in h]
        cover.append((c, a, b, round(m / t, 4), len(s), len(nowards)))
        for w in s:
            if w not in h:
                continue
            for p in set(h[w]) | set(s[w]):
                if p == "IND":
                    continue
                rows.append((c, a, b, w, p, h[w].get(p, 0.0), s[w].get(p, 0.0)))
print("coverage (city, a, b, matched registered share, wards, wards with no prior):")
for x in cover:
    print("  ", x)
json.dump(rows, open(SCRATCH + "/swing_rows.json", "w"))
by = collections.defaultdict(list)
for r in rows:
    by[bin_of(r[5])].append(r)
def q(xs, f):
    xs = sorted(xs); return xs[int(round(f * (len(xs) - 1)))]
print("\nswing s - h (points) by starting share h, all 32 transitions, IND excluded:")
print("bin, n, min, p01, p50, p99, max, (argmin), (argmax)")
for i in sorted(by):
    d = [(r[6] - r[5]) * 100 for r in by[i]]
    mn = min(by[i], key=lambda r: r[6] - r[5]); mx = max(by[i], key=lambda r: r[6] - r[5])
    print(f"[{BINS[i]:.2f},{BINS[i+1]:.2f}) n={len(d)} min={min(d):.1f} p01={q(d,.01):.1f} p50={q(d,.5):.1f} "
          f"p99={q(d,.99):.1f} max={max(d):.1f}  argmin={mn[:5]} {mn[5]:.3f}->{mn[6]:.3f}  argmax={mx[:5]} {mx[5]:.3f}->{mx[6]:.3f}")
