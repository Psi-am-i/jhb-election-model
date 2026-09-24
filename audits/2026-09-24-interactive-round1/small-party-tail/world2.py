import sys, json
from pathlib import Path
sys.path.insert(0, "src")
import numpy as np
import cityconfig, official_seats
import parties as P
from fold import load, citywide
W = json.load(open("/tmp/smalltail_world.json"))
CODES = {"joburg":"JHB","tshwane":"TSH","ekurhuleni":"EKU","ethekwini":"ETH","capetown":"CPT","mangaung":"MAN","nelsonmandelabay":"NMA","buffalocity":"BUF"}
D = Path("data/raw/elections")
allshares = []
for r in W:
    if "council" not in r: continue
    code = CODES[r["city"]]
    p = D / cityconfig.CALENDAR[r["year"]].results.replace("{CODE}", code)
    pr, _ = load(p, "PR"); wd, _ = load(p, "Ward")
    cpr = citywide(pr)
    # combined votes
    tot = {}
    for v in (pr, wd):
        for vd, c in v.items():
            for q, n in c.items(): tot[q] = tot.get(q, 0) + n
    T = sum(tot.values())
    comb = {q: n / T for q, n in tot.items()}
    off = official_seats.read(code, int(r["year"]))
    seats = {}
    for name, row in off["parties"].items():
        c = P.canonical(name); seats[c] = seats.get(c, 0) + row["seats"]
    won = [comb[q] for q, s in seats.items() if s > 0 and q in comb and q != "IND"]
    lost = [comb[q] for q, s in comb.items() if seats.get(q, 0) == 0 and q != "IND"]
    fs = [cpr.get(q, 0) for q in r["first_list"]]
    allshares += [(r["city"], r["year"], q, cpr.get(q, 0), seats.get(q, 0)) for q in r["first_list"]]
    print(r["city"], r["year"], "min seat-winning combined %.4f%%" % (100*min(won)), "max seatless combined %.4f%%" % (100*max(lost) if lost else 0),
          "first-timer PR share median %.4f%% mean %.4f%%" % (100*np.median(fs) if fs else 0, 100*np.mean(fs) if fs else 0))
json.dump(allshares, open("/tmp/smalltail_firstshares.json", "w"))
a = np.array([x[3] for x in allshares]); won = np.array([x[4] > 0 for x in allshares])
print("n first-timers 2011-21:", len(a), "won:", won.sum(), "rate %.3f" % won.mean(), "median share %.4f%%" % (100*np.median(a)), "mean %.4f%%" % (100*a.mean()))
for lo, hi in [(0, .0005), (.0005, .001), (.001, .002), (.002, .005), (.005, 1)]:
    m = (a >= lo) & (a < hi); print("PR share [%.2f%%,%.2f%%): n=%d won=%d" % (100*lo, 100*hi, m.sum(), won[m].sum()))
