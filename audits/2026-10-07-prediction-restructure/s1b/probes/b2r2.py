"""SPEC-B2r2 probe: the bounds with the measured allowance (mean record
exceedance), the 2024-national prior for parties new to local elections, and
the citywide swing limit. Backtest (24 city-years) and 2026 (rule A, the
screenshot state). B2a = per-party box from ward ranges, intersected with the
citywide limit. B2b = B2a's ranges, whole state checked by the joint LP."""
import collections, json, statistics, sys
sys.path.append("pylib")
from load import all_data, ward_shares, prior_on, parts_of, parts_2026, CITIES, YEARS, REPO
import b2bt as B, cityswing as CS, records as R, npe as NP
from ward_poly import ward_range

D = all_data(); NPE = NP.N
MISS = []
NPE_OF = {"2006": "2004", "2011": "2009", "2016": "2014", "2021": "2019", "2026": "2024"}
FALLBACK_A = 0.05      # used only where no record event precedes the target (2011)

def mean_before(ev, T, fallback=FALLBACK_A):
    xs = [e[5] for e in ev if e[0] < T]
    return (statistics.mean(xs), len(xs)) if xs else (fallback, 0)

# record events (exclusions detected from data: records.detect)
EV_WARD = R.exceedances(R.ward_obs("all"), lambda o: o[3])
EV_CITY = R.exceedances(R.city_obs("all"), lambda o: o[3])
# shape quantities, per election over all metros
SHAPE = {}
for y in YEARS:
    w0, r0 = 1, 0
    for c in CITIES:
        s, _, _ = ward_shares(D[(c, y)][0])
        for sh in s.values():
            v = sorted(sh.values(), reverse=True); w0 = min(w0, v[0]); r0 = max(r0, v[1] if len(v) > 1 else 0)
    SHAPE[y] = (w0, r0)
def shape_bounds(T):
    ys = [y for y in YEARS if y < T]
    def ev(i, d):
        rec = None; out = []
        for y in ys:
            m = SHAPE[y][i]
            if rec is not None and ((d < 0 and m < rec) or (d > 0 and m > rec)):
                out.append(abs(m - rec)); rec = m
            elif rec is None: rec = m
        return out
    ew, er = ev(0, -1), ev(1, 1)
    import os
    MINEV = int(os.environ.get("SHAPE_MIN_EVENTS", "1"))
    aw = statistics.mean(ew) if len(ew) >= MINEV else FALLBACK_A
    ar = statistics.mean(er) if len(er) >= MINEV else FALLBACK_A
    qw = min(SHAPE[y][0] for y in ys); qr = max(SHAPE[y][1] for y in ys)
    return max(0, qw - aw), min(0.5, qr + ar), (aw, len(ew)), (ar, len(er))

def ext_by_bin(rows, T, key_b, key_sw):
    d = collections.defaultdict(lambda: [1.0, -1.0])
    for r in rows:
        if r[0] < T:
            b = key_b(r); d[b][0] = min(d[b][0], key_sw(r)); d[b][1] = max(d[b][1], key_sw(r))
    allv = [x for v in d.values() for x in v]
    for b in range(len(B.EDGES) - 1):
        if b not in d: d[b] = [min(allv), max(allv)]
    return d

WARD_ROWS = [(r[2], r[5], r[6] - r[5]) for r in B.TRANS if r[5] > 0 and r[6] > 0]          # (b, h, swing)
CITY_ROWS = [(b, H, V - H) for c, b, p, H, V in CS.PAIRS if H > 0 and V > 0]
NPE_COLLAPSE = {(c, l, p) for c, n, l, p, Nn, V in NP.city_rows if Nn >= 0.02 and V < 0.25 * Nn}
NPE_WARD = [(r[2], r[5], r[6] - r[5]) for r in NP.ward_rows if (r[0], r[2], r[4]) not in NPE_COLLAPSE]
NPE_CITY = [(l, Nn, V - Nn) for c, n, l, p, Nn, V in NP.city_rows if (c, l, p) not in NPE_COLLAPSE]

def newcomer_caps(T):
    """Greatest ward and citywide share of a party new to its city with no vote at the preceding NPE."""
    wmax = cmax = 0.0
    for c in CITIES:
        for a, b in zip(YEARS, YEARS[1:]):
            if b >= T: continue
            stood = {p for d in D[(c, a)][0].values() for p, v in d["wv"].items() if v}
            npe = NP.city_of(NPE[(c, NPE_OF[b])]) if b in NPE_OF else {}
            s, tot, _ = ward_shares(D[(c, b)][0]); A = sum(tot.values())
            V = collections.Counter()
            for w in s:
                for p, v in s[w].items():
                    V[p] += tot[w] / A * v
                    if p != "IND" and p not in stood and npe.get(p, 0) == 0: wmax = max(wmax, v)
            for p, v in V.items():
                if p != "IND" and p not in stood and npe.get(p, 0) == 0: cmax = max(cmax, v)
    return wmax, cmax

def build(T, c, vds_target_parts, prev_vds, npe_vds, roster, wards, e, H_city_e, Hc_prev, Hn_city):
    """Per-ward (lo, hi) before the shape; citywide limit per party; the allowance used."""
    Aw, nw = mean_before(EV_WARD, T); Ac, nc = mean_before(EV_CITY, T)
    ew = ext_by_bin(WARD_ROWS, T, lambda r: B.bin_of(r[1]), lambda r: r[2])
    ec = ext_by_bin(CITY_ROWS, T, lambda r: B.bin_of(r[1]), lambda r: r[2])
    nw_ = ext_by_bin(NPE_WARD, T, lambda r: B.bin_of(r[1]), lambda r: r[2])
    nc_ = ext_by_bin(NPE_CITY, T, lambda r: B.bin_of(r[1]), lambda r: r[2])
    Nw, Nc = newcomer_caps(T)
    h, _, _ = prior_on(vds_target_parts, prev_vds)
    hn = prior_on(vds_target_parts, npe_vds)[0] if npe_vds else {}
    per = {}
    kinds = collections.Counter()
    for w in wards:
        lo, hi = {}, {}
        for p in roster:
            x = (h.get(w) or {}).get(p, 0.0)
            if x == 0 and Hc_prev.get(p, 0) > 0: x = Hc_prev[p]
            if x > 0:
                dl, dh = ew[B.bin_of(x)]; lo[p], hi[p] = max(0, x + dl - Aw), min(1, x + dh + Aw); kinds["lge"] += 1
                continue
            xn = (hn.get(w) or {}).get(p, 0.0) or Hn_city.get(p, 0.0)
            if xn > 0:
                dl, dh = nw_[B.bin_of(xn)]; lo[p], hi[p] = max(0, xn + dl - Aw), min(1, xn + dh + Aw); kinds["npe"] += 1
            else:
                lo[p], hi[p] = 0.0, min(1, Nw + Aw); kinds["new"] += 1
        per[w] = (lo, hi)
    city = {}
    for p in roster:
        if H_city_e.get(p, 0) > 0:
            dl, dh = ec[B.bin_of(H_city_e[p])]; city[p] = (max(0, H_city_e[p] + dl - Ac), min(1, H_city_e[p] + dh + Ac))
        elif Hn_city.get(p, 0) > 0:
            dl, dh = nc_[B.bin_of(Hn_city[p])]; city[p] = (max(0, Hn_city[p] + dl - Ac), min(1, Hn_city[p] + dh + Ac))
        else:
            city[p] = (0.0, min(1, Nc + Ac))
    return per, city, {"A_ward": Aw, "n_ward_events": nw, "A_city": Ac, "n_city_events": nc, "N_ward": Nw, "N_city": Nc, "kinds": dict(kinds)}

def shape_and_box(per, roster, wards, e, calls, qw, qr):
    out = {}; fb = []
    fl = collections.Counter(); ce = collections.Counter()
    for w in wards:
        lo, hi = dict(per[w][0]), dict(per[w][1]); W = calls[w]
        lo[W] = max(lo[W], qw)
        for p in roster:
            if p != W: hi[p] = min(hi[p], qr)
        ok, mins, maxs = ward_range(roster, lo, hi, W)
        if not ok:
            fb.append((w, W)); lo = {p: 0.0 for p in roster}; hi = {p: qr for p in roster}; lo[W] = qw; hi[W] = 1.0
            ok, mins, maxs = ward_range(roster, lo, hi, W)
        out[w] = (lo, hi)
        for p in roster:
            fl[p] += e[w] * mins[p]; ce[p] += e[w] * maxs[p]
    return out, fl, ce, fb

def b2a_limits(fl, ce, city, roster):
    """B2a: box intersected with the citywide limit; the map wins where they conflict."""
    lo, hi, conflict = {}, {}, []
    for p in roster:
        a, b = max(fl[p], city[p][0]), min(ce[p], city[p][1])
        if a > b:
            conflict.append(p); a, b = fl[p], max(fl[p], min(ce[p], city[p][1]))
        lo[p], hi[p] = a, b
    return lo, hi, conflict

def backtest():
    tot = collections.Counter(); rows = []
    for T in ["2011", "2016", "2021"]:
        prevY = YEARS[YEARS.index(T) - 1]
        qw, qr, aqw, aqr = shape_bounds(T)
        for c in CITIES:
            vds = D[(c, T)][0]; s, tots, reg = ward_shares(vds)
            parts = parts_of(vds)
            _, _, turn = prior_on(parts, D[(c, prevY)][0])
            exp = {w: reg[w] * turn.get(w, sum(turn.values()) / len(turn)) for w in s}; E = sum(exp.values()); e = {w: exp[w] / E for w in s}
            roster = sorted({p for w in s for p in s[w]}); wards = list(s)
            Hprev = B.city_prior(c, prevY)
            h, _, _ = prior_on(parts, D[(c, prevY)][0])
            He = collections.Counter()
            for w in wards:
                for p, v in (h.get(w) or {}).items(): He[p] += e[w] * v
            import os
            npe_v = NPE[(c, NPE_OF[T])] if not os.environ.get("NO_NPE") else {}
            Hn = NP.city_of(npe_v) if npe_v else {}
            Hn = {p: v for p, v in Hn.items() if Hprev.get(p, 0) == 0}     # only for parties new to local
            per, city, info = build(T, c, parts, D[(c, prevY)][0], npe_v, roster, wards, e, He, Hprev, Hn)
            winner = {w: max(s[w], key=s[w].get) for w in wards}
            pm, fl, ce, fb = shape_and_box(per, roster, wards, e, winner, qw, qr)
            A = sum(tots.values()); V = collections.Counter()
            for w in wards:
                for p, v in s[w].items(): V[p] += tots[w] / A * v
            wo = 0; npairs = 0
            for w in wards:
                lo, hi = pm[w]
                for p in roster:
                    sp, hp = s[w].get(p, 0), (h.get(w) or {}).get(p, 0)
                    if p == "IND" or (sp == 0 and hp == 0): continue
                    npairs += 1; o_ = sp < lo[p] - 1e-12 or sp > hi[p] + 1e-12; wo += o_
                    if o_: MISS.append((T, c, p))
            lo, hi, conf = b2a_limits(fl, ce, city, roster)
            box_out = [p for p in roster if V[p] < fl[p] - 1e-9 or V[p] > ce[p] + 1e-9]
            city_out = [(p, round(100 * V[p], 2), round(100 * city[p][0], 1), round(100 * city[p][1], 1)) for p in roster
                        if p != "IND" and (V[p] < city[p][0] - 1e-9 or V[p] > city[p][1] + 1e-9)]
            a_out = [p for p in roster if V[p] < lo[p] - 1e-9 or V[p] > hi[p] + 1e-9]
            slack = B.joint_lp(roster, wards, pm, winner, e, V)
            r = {"city": c, "T": T, "wards": len(wards), "pairs": npairs, "ward_out": wo, "fallback": len(fb),
                 "parties": len(roster), "box_out": len(box_out), "city_limit_out": city_out, "b2a_out": len(a_out),
                 "conflict": conf, "joint_slack": slack, "A_ward": round(100 * info["A_ward"], 2), "A_city": round(100 * info["A_city"], 2),
                 "q_win": round(100 * qw, 2), "q_run": round(100 * qr, 2), "kinds": info["kinds"]}
            rows.append(r); print(json.dumps(r))
            for k in ("wards", "pairs", "ward_out", "fallback", "parties", "box_out", "b2a_out"): tot[k] += r[k]
            tot["city_limit_out"] += len(city_out); tot["b2b_out"] += (slack is None or slack > 1e-6) or bool(city_out)
            tot["joint_fail"] += slack is None or slack > 1e-6
    print("TOTAL", dict(tot))
    return rows

def year2026():
    F = json.load(open(REPO + "/site/your-forecast/forecast.json"))
    ctx = F["schema"]["x-seat-context"]; roster = ctx["parties"]; wards = ctx["wards"]
    e = F["schema"]["x-editor-bounds"]["e"]; st = F["start"]
    calls = st["ward_calls"] if isinstance(st["ward_calls"], dict) else dict(zip(wards, st["ward_calls"]))
    parts = parts_2026(); prev = D[("JHB", "2021")][0]; npe_v = NPE[("JHB", "2024")]
    Hprev = B.city_prior("JHB", "2021")
    h, _, _ = prior_on(parts, prev); He = collections.Counter()
    for w in wards:
        for p, v in h[w].items(): He[p] += e[w] * v
    Hn = {p: v for p, v in NP.city_of(npe_v).items() if Hprev.get(p, 0) == 0}
    per, city, info = build("2026", "JHB", parts, prev, npe_v, roster, wards, e, He, Hprev, Hn)
    qw, qr, aqw, aqr = shape_bounds("2026")
    print(f"2026: A_ward {100*info['A_ward']:.2f} pts from {info['n_ward_events']} events; A_city {100*info['A_city']:.2f} from {info['n_city_events']};"
          f" q_win {100*qw:.2f} (allowance {100*aqw[0]:.2f}, {aqw[1]} events); q_run {100*qr:.2f} (allowance {100*aqr[0]:.2f}, {aqr[1]} events);"
          f" newcomer caps ward {100*info['N_ward']:.1f} city {100*info['N_city']:.1f}; range kinds {info['kinds']}")
    TW = sum(st["ward_votes"].values()); VA = {p: st["ward_votes"][p] / TW for p in roster}
    TL = sum(st["list_votes"].values())
    shot = {"ANC": 8.4, "DA": 29.3, "ASA": 10.7, "EFF": 12.1, "PA": 13.8, "MK": 10.0, "IFP": 1.8, "RISE": 1.8,
            "SOUTH_AFRICAN_COMMUNIST_PARTY": 1.5, "ALJAMAAH": 1.3, "BOSA": 1.1, "ACDP": 0.6, "ALL_CITIZENS_PARTY": 1.0,
            "ATM": 0.6, "VFPLUS": 0.9, "AHC": 0.5, "AIC": 0.5, "APC": 0.2, "DUDULA": 0.1, "PAC": 0.5,
            "TRUTH_AND_SOLIDARITY_MOVEMENT": 0.1, "UDM": 0.2, "UNITED_AFRICANS_TRANSFORMATION": 0.2}
    rest = [p for p in roster if p not in shot]; left = 100 - sum(shot.values())
    VS = {p: shot.get(p, left / len(rest)) / 100 for p in roster}
    pm, fl, ce, fb = shape_and_box(per, roster, wards, e, calls, qw, qr)
    lo, hi, conf = b2a_limits(fl, ce, city, roster)
    big = ["ANC", "DA", "PA", "MK", "EFF", "ASA", "BOSA", "RISE"]
    print("  fallback wards on rule A's map:", fb, "conflicts (map needs more than the citywide limit):", conf)
    print("  per party: box [floor, ceil] | citywide limit | B2a [lo, hi] | rule A | screenshot")
    for p in big:
        print(f"   {p:5s} box {100*fl[p]:.1f}-{100*ce[p]:.1f} | city {100*city[p][0]:.1f}-{100*city[p][1]:.1f} | B2a {100*lo[p]:.1f}-{100*hi[p]:.1f} | A {100*VA[p]:.2f} | shot {100*VS[p]:.1f}")
    for name, V in (("rule A", VA), ("screenshot", VS)):
        a_out = [(p, round(100 * V[p], 2), round(100 * lo[p], 2), round(100 * hi[p], 2)) for p in roster if V[p] < lo[p] - 1e-9 or V[p] > hi[p] + 1e-9]
        slack = B.joint_lp(roster, wards, pm, calls, e, V)
        print(f"  {name}: B2a outside {a_out}; B2b joint LP slack {slack} pts plus the B2a citywide check")
    # gaps of rule A against the shape-measured gap bounds
    gaps = {p: 100 * (st["list_votes"][p] / TL - VA[p]) for p in roster}
    print("  rule A gap range (list% - ward%):", round(min(gaps.values()), 2), "to", round(max(gaps.values()), 2),
          [(p, round(g, 2)) for p, g in sorted(gaps.items(), key=lambda x: x[1])[:2]], [(p, round(g, 2)) for p, g in sorted(gaps.items(), key=lambda x: -x[1])[:2]])
    # paintability
    bad = collections.Counter()
    for w in wards:
        for W in roster:
            l2, h2 = dict(per[w][0]), dict(per[w][1]); l2[W] = max(l2[W], qw)
            for p in roster:
                if p != W: h2[p] = min(h2[p], qr)
            if not ward_range(roster, l2, h2, W)[0]: bad[W] += 1
    print(f"  unpaintable (ward, party) pairs: {sum(bad.values())} of {len(wards)*len(roster)}; top {bad.most_common(4)}")
    return per, city, pm, fl, ce, calls, e, roster, wards, VA

if __name__ == "__main__":
    if "2026" in sys.argv: year2026()
    else: backtest()
