import sys, json
from pathlib import Path
sys.path.insert(0, "src")
import cityconfig, official_seats
import parties as P
from fold import load, citywide
from pools import SPLITS
CITIES = {"joburg":"JHB","tshwane":"TSH","ekurhuleni":"EKU","ethekwini":"ETH",
          "capetown":"CPT","mangaung":"MAN","nelsonmandelabay":"NMA","buffalocity":"BUF"}
D = Path("data/raw/elections")
EXCL = set(SPLITS) | {"IND"}
out = []
for slug, code in CITIES.items():
    city = cityconfig.use(slug)
    hist = set()   # parties with >0 votes in any earlier archive election in this metro
    for y in sorted(cityconfig.CALENDAR):
        e = cityconfig.CALENDAR[y]
        if not e.results: continue
        p = D / e.results.replace("{CODE}", code)
        if not p.exists(): continue
        ballot = "PR" if e.kind == "LGE" else None
        v, _ = load(p, ballot)
        cw = citywide(v)
        stood = {q for q, s in cw.items() if s > 0 and q != "IND"}
        if e.kind == "LGE":
            first = sorted(q for q in stood if q not in hist and q not in EXCL)
            off = official_seats.read(code, int(y))
            seats = None
            if off:
                seats = {}
                for name, row in off["parties"].items():
                    c = P.canonical(name)
                    seats[c] = seats.get(c, 0) + row["seats"]
                seats = {q: s for q, s in seats.items() if s > 0}
            row = {"city": slug, "year": y, "ballot": len(stood),
                   "has_history": bool(hist), "first_stood": len(first),
                   "first_list": first}
            if seats is not None:
                pp = {q: s for q, s in seats.items() if q != "IND"}
                srt = sorted(pp.values(), reverse=True)
                row.update(council=sum(seats.values()), seated=len(pp),
                           ind_seats=seats.get("IND", 0),
                           out5=sum(srt[5:]), out7=sum(srt[7:]),
                           first_won=sum(1 for q in first if seats.get(q, 0) > 0),
                           first_seats=sum(seats.get(q, 0) for q in first),
                           first_winners={q: seats[q] for q in first if seats.get(q, 0) > 0},
                           seat_unmatched=sorted(q for q in pp if q not in stood))
            out.append(row)
        hist |= stood
json.dump(out, open(sys.argv[1], "w"), indent=1)
for r in out:
    print(r["city"], r["year"], "ballot", r["ballot"], "hist", r["has_history"], "first_stood", r["first_stood"],
          *( [ "council", r["council"], "seated", r["seated"], "IND", r["ind_seats"], "out5", r["out5"], "out7", r["out7"],
               "first_won", r["first_won"], "first_seats", r["first_seats"], r["first_winners"], "unmatched", r["seat_unmatched"]] if "council" in r else []))
