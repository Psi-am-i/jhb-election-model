"""B2 probe: the 2026 editor under ward-by-ward ranges. Rule A's prediction
(forecast.json start), the screenshot state, and random box-bounded states,
each checked by the per-party box and the joint LP."""
import collections, json, random, sys
sys.path.append("pylib")
from load import all_data, ward_shares, prior_on, parts_2026, REPO
import b2bt as B
from ward_poly import ward_range

F = json.load(open(REPO + "/site/your-forecast/forecast.json"))
ctx = F["schema"]["x-seat-context"]; codes = ctx["parties"]; wards = ctx["wards"]
xb = F["schema"]["x-editor-bounds"]; e = {w: xb["e"][w] for w in wards}
st = F["start"]
calls = st["ward_calls"] if isinstance(st["ward_calls"], dict) else dict(zip(wards, st["ward_calls"]))
TW = sum(st["ward_votes"].values()); VA = {p: st["ward_votes"][p] / TW for p in codes}

data = all_data()
v21 = data[("JHB", "2021")][0]
h21, cov, _ = prior_on(parts_2026(), v21)
# 2021 MDB ward ids are not the 2026 numbers; prior_on keyed by crosswalk ward number
missing_codes = sorted({p for w in h21 for p in h21[w]} - set(codes))
no_hist = sorted(p for p in codes if not any(h21.get(w, {}).get(p, 0) > 0 for w in wards))

HC21 = B.city_prior("JHB", "2021")
def build(stat, combine):
    D, N, _, _ = B.allowance("2027", stat)        # all 32 transitions
    qw, qr = F["schema"]["x-editor-bounds"]["q_win"], F["schema"]["x-editor-bounds"]["q_run"]
    per = {}
    for w in wards:
        lo, hi = B.ranges(h21.get(w), codes, D, N, 0.05, HC21)
        per[w] = (lo, hi)
    return per, qw, qr, D, N

FALLBACK = []
def apply_map(per, calls, qw, qr, combine):
    out = {}; FALLBACK.clear()
    for w in wards:
        lo, hi = dict(per[w][0]), dict(per[w][1])
        W0 = calls[w]
        if combine:
            lo[W0] = max(lo[W0], qw)
            for p in codes:
                if p != W0: hi[p] = min(hi[p], qr)
        if not ward_range(codes, lo, hi, W0)[0]:
            FALLBACK.append((w, W0))
            lo = {p: 0.0 for p in codes}; hi = {p: qr for p in codes}; lo[W0] = qw; hi[W0] = 1.0
        out[w] = (lo, hi)
    return out

def box(per_m, calls):
    fl = collections.Counter(); ce = collections.Counter(); bad = []
    for w in wards:
        lo, hi = per_m[w]
        ok, mins, maxs = ward_range(codes, lo, hi, calls[w])
        if not ok:
            bad.append((w, calls[w], round(hi[calls[w]], 3), max(((round(lo[p], 3), p) for p in codes if p != calls[w]))))
            mins = {p: 0.0 for p in codes}; maxs = {p: 1.0 for p in codes}
        for p in codes:
            fl[p] += e[w] * mins[p]; ce[p] += e[w] * maxs[p]
    return fl, ce, bad

def slice_b(calls, qw, qr):
    won = collections.Counter()
    for w in wards: won[calls[w]] += e[w]
    return {p: qw * won[p] for p in codes}, {p: won[p] + qr * (1 - won[p]) for p in codes}

def report(name, V, calls, variants):
    print(f"\n=== {name}")
    for stat, comb in variants:
        per, qw, qr, D, N = build(stat, comb)
        pm = apply_map(per, calls, qw, qr, comb)
        fl, ce, bad = box(pm, calls); bad = list(FALLBACK)
        outs = [(p, round(100 * V[p], 2), round(100 * fl[p], 2), round(100 * ce[p], 2)) for p in codes
                if V[p] < fl[p] - 1e-9 or V[p] > ce[p] + 1e-9]
        joint = B.joint_lp(codes, wards, pm, calls, e, V)
        big = {p: (round(100 * fl[p], 1), round(100 * V[p], 1), round(100 * ce[p], 1)) for p in ["ANC", "DA", "PA", "MK", "EFF", "ASA"]}
        print(f"  {stat}{'+sb' if comb else ''}: wards falling back to slice B's shape {len(bad)} {bad[:4]}; box outside {outs}; joint LP slack (points) {joint}")
        print(f"     floor/value/ceiling: {big}")
    sf, sc = slice_b(calls, F['schema']['x-editor-bounds']['q_win'], F['schema']['x-editor-bounds']['q_run'])
    print("  slice B floor/value/ceiling:", {p: (round(100 * sf[p], 1), round(100 * V[p], 1), round(100 * sc[p], 1)) for p in ["ANC", "DA", "PA", "MK", "EFF", "ASA"]})

if __name__ == "__main__":
    print("2021 codes absent from the 2026 roster:", len(missing_codes), missing_codes[:8])
    print("2026 roster parties with no 2021 ward record in any 2026 ward:", len(no_hist), [p for p in no_hist if VA[p] > .003])
    print("calls:", collections.Counter(calls.values()))
    print("2026 wards with a part lacking a 2021 VD:", sum(1 for w in wards if cov[w][0] < cov[w][1]),
          "wards with no prior:", sum(1 for w in wards if w not in h21))
    V = [("ext", False), ("ext", True), ("p01", True), ("p05", True)]
    report("rule A (forecast.json start)", VA, calls, V)
    # the screenshot state (slice B UAT, vote-375-edited.png): rule A's map, ward vote as shown
    shot = {"ANC": 8.4, "DA": 29.3, "ASA": 10.7, "EFF": 12.1, "PA": 13.8, "MK": 10.0, "IFP": 1.8, "RISE": 1.8,
            "SOUTH_AFRICAN_COMMUNIST_PARTY": 1.5, "ALJAMAAH": 1.3, "BOSA": 1.1, "ACDP": 0.6, "ALL_CITIZENS_PARTY": 1.0,
            "ATM": 0.6, "VFPLUS": 0.9, "AHC": 0.5, "AIC": 0.5, "APC": 0.2, "DUDULA": 0.1, "PAC": 0.5,
            "TRUTH_AND_SOLIDARITY_MOVEMENT": 0.1, "UDM": 0.2, "UNITED_AFRICANS_TRANSFORMATION": 0.2}
    rest = [p for p in codes if p not in shot]
    left = 100 - sum(shot.values())
    VS = {p: shot.get(p, left / len(rest)) / 100 for p in codes}
    report("screenshot state (approximate: the 23 shown, the rest spread evenly)", VS, calls, V)
    # random states: rule A's map, votes drawn inside the per-party box (ext+sb), joint LP on each
    per, qw, qr, D, N = build("ext", True); pm = apply_map(per, calls, qw, qr, True)
    fl, ce, bad = box(pm, calls)
    rng = random.Random(3); n_inf = 0; slacks = []
    for t in range(int(sys.argv[1]) if len(sys.argv) > 1 else 60):
        # a random point of the box with sum 1: start at floors, fill to ceilings in random order and amounts
        v = {p: fl[p] for p in codes}; spare = 1 - sum(v.values())
        order = codes[:]; rng.shuffle(order)
        for p in order:
            take = min(ce[p] - fl[p], spare * rng.random() ** 0.5); v[p] += take; spare -= take
        for p in order:
            take = min(ce[p] - v[p], spare); v[p] += take; spare -= take
        sl = B.joint_lp(codes, wards, pm, calls, e, v)
        slacks.append(sl); n_inf += (sl or 0) > 1e-6
    print(f"\nrandom box points (ext+sb, rule A's map): {len(slacks)}; jointly infeasible {n_inf}; slack points max {max(slacks)}")
