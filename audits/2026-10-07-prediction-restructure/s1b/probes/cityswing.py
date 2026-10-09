"""Probe: a citywide swing allowance per party (option, not the packet's
ward-by-ward rule). Out-of-sample backtest on the 24 city-years and the 2026
check of rule A and the screenshot state. Prior H_p = the party's share of the
preceding LGE's ward votes re-weighted onto the target's wards by e (the same
join as the ward ranges), so the ward ranges and this bound share one prior."""
import collections, json, sys
from load import all_data, ward_shares, prior_on, parts_of, parts_2026, CITIES, YEARS, REPO
EDGES = [0.0, 0.01, 0.05, 0.15, 0.35, 0.60, 1.0001]
def bin_of(h):
    for i in range(len(EDGES) - 1):
        if h <= EDGES[i + 1]:
            return i
data = all_data()

def prior_city(c, T):
    vds = data[(c, T)][0]
    prevY = YEARS[YEARS.index(T) - 1]
    h, cov, turn = prior_on(parts_of(vds), data[(c, prevY)][0])
    s, tot, reg = ward_shares(vds)
    exp = {w: reg[w] * turn.get(w, sum(turn.values()) / len(turn)) for w in s}
    E = sum(exp.values())
    H = collections.Counter()
    for w in s:
        for p, v in (h.get(w) or {}).items():
            H[p] += exp[w] / E * v
    A = sum(tot.values()); V = collections.Counter()
    for w in s:
        for p, v in s[w].items():
            V[p] += tot[w] / A * v
    return H, V

PAIRS = []  # (city, b, party, H, V)
for c in CITIES:
    for b in YEARS[1:]:
        H, V = prior_city(c, b)
        for p in set(H) | set(V):
            if p != "IND":
                PAIRS.append((c, b, p, H[p], V[p]))

def allowance(before):
    by = collections.defaultdict(list); new = []
    for c, b, p, H, V in PAIRS:
        if b >= before: continue
        if H > 0 and V > 0: by[bin_of(H)].append(V - H)
        elif H == 0 and V > 0: new.append(V)
    D = {i: (min(v), max(v)) for i, v in by.items()}
    for i in range(len(EDGES) - 1):
        if i not in D: D[i] = (min(x[0] for x in D.values()), max(x[1] for x in D.values()))
    return D, max(new)

def bound(H, D, N, w=.05):
    if H > 0:
        dl, dh = D[bin_of(H)]; return max(0, H + dl - w), min(1, H + dh + w)
    return 0.0, min(1, N + w)

tot = collections.Counter(); outs = []
for T in ["2011", "2016", "2021"]:
    D, N = allowance(T)
    for c in CITIES:
        H, V = prior_city(c, T)
        for p in V:
            if p == "IND" or V[p] == 0: continue
            lo, hi = bound(H[p], D, N)
            tot["parties"] += 1; tot["ge1"] += V[p] >= .01
            if V[p] < lo or V[p] > hi:
                tot["out"] += 1; tot["out_ge1"] += V[p] >= .01
                outs.append((c, T, p, round(100 * H[p], 1), round(100 * V[p], 1), round(100 * lo, 1), round(100 * hi, 1)))
print("citywide swing allowance, out of sample, 24 city-years:", dict(tot))
for o in outs: print("  outside:", o)
D, N = allowance("2027")
print("2026 allowance (32 transitions):", {i: (round(100 * a, 1), round(100 * b, 1)) for i, (a, b) in D.items()}, "newcomer max", round(100 * N, 1))

F = json.load(open(REPO + "/site/your-forecast/forecast.json"))
codes = F["schema"]["x-seat-context"]["parties"]; wards = F["schema"]["x-seat-context"]["wards"]
e = F["schema"]["x-editor-bounds"]["e"]
h21, _, _ = prior_on(parts_2026(), data[("JHB", "2021")][0])
H26 = collections.Counter()
for w in wards:
    for p, v in h21[w].items(): H26[p] += e[w] * v
st = F["start"]; TW = sum(st["ward_votes"].values())
for p in ["ANC", "DA", "EFF", "ASA", "PA", "MK", "IFP", "BOSA", "ALJAMAAH", "RISE"]:
    lo, hi = bound(H26[p], D, N)
    print(f"  2026 {p}: prior {100*H26[p]:.1f}  allowed {100*lo:.1f}..{100*hi:.1f}  rule A {100*st['ward_votes'][p]/TW:.1f}")
out = [(p, round(100 * st['ward_votes'][p] / TW, 2)) for p in codes if not (bound(H26[p], D, N)[0] <= st['ward_votes'][p] / TW <= bound(H26[p], D, N)[1])]
print("  rule A parties outside the citywide allowance:", out)
