"""Prediction-rule backtest, one city-year (prereg/2026-10-08-prediction-rule-backtest.md).
Writes only to the output path given. Usage: one.py <city> <year> <out.json>"""
import argparse, json, sys
from collections import Counter
from pathlib import Path
import numpy as np
sys.path.insert(0, "src")
import cityconfig, montecarlo as M, compare_history as CH
from seats import eligible_parties, outside_pool_wards

city, year, out = sys.argv[1:4]
data_dir = Path("data/raw/elections")
c = cityconfig.use(city); target = cityconfig.use_target(year); M.apply_city(c)
scenario = M.load_scenario(argparse.Namespace(config=None, set=[], draws=1000, seed=None, city=city, target=year))
cap = []
real_elig = M.eligible_parties
def capturing(w, p):
    cap.append((dict(w), dict(p))); return real_elig(w, p)
M.eligible_parties = capturing
run = M.run_model(target, scenario, data_dir, verbose=False)
M.eligible_parties = real_elig
n = len(run.seat_draws)
assert len(cap) == n, (len(cap), n)

actual_pr, actual_ward = CH.actual_shares(target, data_dir)
actual_seats, entrant, actual_winners = CH._actual_seats(target, data_dir)
ren = (lambda p: entrant if (entrant and p == "ENTRANT") else p)
def rn(d):
    o = Counter()
    for k, v in d.items(): o[ren(k)] += v
    return dict(o)
uni = [ren(p) for p in run.universe]
wards = [str(w) for w in run.wards]

# A: modal ward calls (ties to the earlier universe index), mean ballots, seat law
modal = [uni[i] for i in run.ward_winner_counts.argmax(axis=1)]
parties = sorted({p for w, l in cap for p in list(w) + list(l)})
mw = {p: float(np.mean([w.get(p, 0) for w, _ in cap])) for p in parties}
ml = {p: float(np.mean([l.get(p, 0) for _, l in cap])) for p in parties}
mw = rn({p: int(round(v)) for p, v in mw.items()}); ml = rn({p: int(round(v)) for p, v in ml.items()})
combined = eligible_parties(mw, ml)
wins = dict(Counter(modal))
cw, dw, pool = outside_pool_wards(wins, combined)
seatsA, councilA, thrA, overA = M.allocate_with_overhang(combined, pool, scenario["overhang_rule"], independent_wards=cw, no_pr_list_wards=dw)
seatsA = {p: s for p, s in seatsA.items() if s}

# B: the draw with the lowest mean seat L1 distance to all draws
seat_draws = [rn(s) for s in run.seat_draws]
sp = sorted({p for s in seat_draws for p in s})
S = np.array([[s.get(p, 0) for p in sp] for s in seat_draws], float)
cost = np.array([np.abs(S - S[i]).sum(1).mean() for i in range(n)])
b = int(cost.argmin())
seatsB = {p: int(v) for p, v in zip(sp, S[b]) if v}
callsB = [uni[i] for i in run.ward_winner_draws[b]]
wB, lB = rn(cap[b][0]), rn(cap[b][1])

def shares(d):
    t = sum(d.values()); return {p: v / t for p, v in d.items()} if t else {}
def l1(a, b):
    ks = set(a) | set(b); return float(sum(abs(a.get(k, 0) - b.get(k, 0)) for k in ks))
def calls_ok(calls):
    return sum(1 for w, p in zip(wards, calls) if actual_winners.get(w) == p)
assert sum(1 for w in wards if w in actual_winners) == len(wards), "ward ids do not align"
act_wins = Counter(actual_winners.values())
median = {p: float(np.median(S[:, j])) for j, p in enumerate(sp)}
coherent = CH.coherent_seats(seat_draws, target.council)
topA = max(wins, key=wins.get)
# excessive in A: seats equal to ward wins and no list seats, wins > 0
excA = [p for p in seatsA if wins.get(p, 0) and seatsA[p] == wins[p] and p in overA]
res = {
  "city": city, "year": year, "draws": n, "council": target.council, "wards": len(wards),
  "A": {"seats": seatsA, "seat_err": l1(seatsA, actual_seats), "wards_ok": calls_ok(modal),
        "ward_vote_err_pp": 100 * l1(shares(mw), actual_ward), "list_vote_err_pp": 100 * l1(shares(ml), actual_pr),
        "top": topA, "top_wards": wins[topA], "top_actual_wards": act_wins.get(topA, 0),
        "excessive": {p: {"wards": wins[p], "actual_seats": actual_seats.get(p, 0), "actual_wards": act_wins.get(p, 0)} for p in sorted(overA)},
        "council": councilA, "ward_wins": wins},
  "B": {"draw": b, "seats": seatsB, "seat_err": l1(seatsB, actual_seats), "wards_ok": calls_ok(callsB),
        "ward_vote_err_pp": 100 * l1(shares(wB), actual_ward), "list_vote_err_pp": 100 * l1(shares(lB), actual_pr)},
  "median_seat_err": l1(median, actual_seats), "median_total": float(sum(median.values())),
  "coherent_seat_err": l1(coherent, actual_seats),
  "actual": {"seats": actual_seats, "ward_wins": dict(act_wins)},
}
Path(out).write_text(json.dumps(res, indent=1, default=str))
print(city, year, "A", res["A"]["seat_err"], res["A"]["wards_ok"], "B", res["B"]["seat_err"], res["B"]["wards_ok"], "coh", res["coherent_seat_err"])
