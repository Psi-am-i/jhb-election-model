"""Mockup data for the share-card designs. READ-ONLY on the repo.

Every figure comes from repo files or the project's own code:
  * the published start of "Break the model": site/your-forecast/forecast.json
  * seats for a reader's picks: src/reader_seats.reader_seats (the seat law)
  * "We give this outcome N% chance": interactive/pyboot/page.py analyse()
    over site/draws (the published 5,000 draws), followup worktree code
  * 2021: data/processed/history.json seats[code][0] (actual), and
    data/raw/elections/lge2021_JHB_vd_party_clean.csv (PR + Ward ballots)
Two forecasts are derived from the start by stated rules (see RULES).
Writes data.json beside this file.
"""
import collections, csv, json, os, sys
REPO = "/Users/simondavis/projects/atlas-jhb-election-model"
FU = REPO + "/.claude/worktrees/followup"
OUT = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [FU + "/src", FU + "/interactive/pyboot"]
os.chdir(FU)
import reader_seats as RS
import page

fj = json.load(open(REPO + "/site/your-forecast/forecast.json"))
parties = json.load(open(REPO + "/site/your-forecast/parties.json"))
ctx = fj["schema"]["x-seat-context"]; total = int(fj["schema"]["x-total-votes"])
wards = [w["id"] for w in fj["geometry"]["wards"]]
start = fj["start"]

# ---- 2021 ----
h = json.load(open(REPO + "/data/processed/history.json"))
rec = [x for x in h["records"] if x["slug"] == "joburg" and x["year"] == "2021"][0]
seats21 = {c: v[0] for c, v in rec["seats"].items() if v[0] > 0}
assert sum(seats21.values()) == 270
cw = {r["raw_name"]: r["canonical"] for r in csv.DictReader(open(REPO + "/data/processed/party_crosswalk.csv"))}
v21 = collections.Counter(); wv = collections.defaultdict(collections.Counter)
for r in csv.DictReader(open(REPO + "/data/raw/elections/lge2021_JHB_vd_party_clean.csv")):
    if r["BallotType"] not in ("PR", "Ward"): continue
    c = cw[r["sPartyName"]]; v = int(r["Party_Votes"]); v21[c] += v
    if r["BallotType"] == "Ward": wv[r["Ward"]][c] += v
T21 = sum(v21.values())
share21 = {c: 100 * v / T21 for c, v in v21.items()}
wards21 = collections.Counter(max(w, key=w.get) for w in wv.values())
assert sum(wards21.values()) == 135

# ---- forecasts by rule ----
probs = {r["ward"]: [(p.split(":")[0], float(p.split(":")[1])) for p in r["dist"].split("|")]
         for r in csv.DictReader(open(REPO + "/data/processed/ward_winner_probs.csv"))}

def second_where(cut, base_calls):
    out = []
    for wid, c in zip(wards, base_calls):
        d = probs[wid]
        out.append(d[1][0] if d[0][1] < cut and len(d) > 1 else c)
    return out

def seat(calls, share_pct):
    tot = sum(share_pct.values())
    fr = {c: share_pct.get(c, 0.0) / tot for c in ctx["parties"]}
    r = RS.reader_seats(fr, dict(zip(wards, calls)), ctx, total)
    assert r["ok"], r["errors"]
    return r

def coalition_in_order(seats, majority, skip=()):
    order = sorted(seats, key=lambda c: (-seats[c], c)); out = []
    for c in order:
        if c in skip: continue
        out.append(c)
        if sum(seats[x] for x in out) >= majority: return out
    return out

RULES = {
 "A": "Ward calls: the published start, except each ward whose most likely winner has under 55% is called for its second most likely (ward_winner_probs.csv). Vote: the start's combined shares. Coalition: parties in seat order until a majority.",
 "B": "Ward calls: as A with a 70% cut. Vote: halfway between the start's combined shares and the 2021 combined vote (PR + ward ballots). Coalition: parties in seat order, skipping the second largest, until a majority.",
}
def build(key, name, calls, share, skip_second):
    r = seat(calls, share)
    seats = {c: s["total"] for c, s in r["seats"].items() if s["total"] > 0}
    order = sorted(seats, key=lambda c: (-seats[c], c))
    coal = coalition_in_order(seats, r["majority"], skip=(order[1],) if skip_second else ())
    req = {"ward_calls": dict(zip(wards, calls)), "share": share, "seats": seats,
           "majority": r["majority"], "coalition": coal}
    an = json.loads(page.analyse(json.dumps(req)))
    rows = []
    for c in order:
        s = r["seats"][c]
        rows.append({"code": c, "name": parties.get(c, {}).get("name", c), "colour": parties.get(c, {}).get("colour", "#8b918b"),
                     "logo": parties.get(c, {}).get("logo", False), "seats": s["total"], "ward": s["ward"], "pr": s["pr"],
                     "vote": round(share.get(c, 0.0) * 100 / sum(share.values()), 1),
                     "seats21": (seats21.get(c, 0) if v21[c] > 0 else None), "wards21": wards21.get(c, 0) if c in v21 else None,
                     "vote21": round(share21[c], 1) if c in share21 and v21[c] > 0 else None})
    return {"key": key, "name": name, "rule": RULES[key], "council": r["council"], "majority": r["majority"],
            "calls": calls, "coalition": coal, "rows": rows, "outcome": an["outcome"],
            "expected": an["expected"], "excessive": r["excessive"]}

shareA = dict(start["combined_share"])
callsA = second_where(0.55, start["ward_calls"])
allc = set(shareA) | set(share21)
shareB = {c: 0.5 * shareA.get(c, 0.0) + 0.5 * share21.get(c, 0.0) for c in ctx["parties"]}
callsB = second_where(0.70, start["ward_calls"])

# load the published cell exactly as the page does
man = open(REPO + "/site/draws/manifest.json").read()
page.load_cell(page.BASE, man, open(REPO + "/site/draws/base.bin", "rb").read())

A = build("A", "Thandi", callsA, shareA, False)
B = build("B", "@kgomotso_m", callsB, shareB, True)
geom = {"W": fj["geometry"]["W"], "H": fj["geometry"]["H"], "paths": [w["path"] for w in fj["geometry"]["wards"]]}
colours = {c: p["colour"] for c, p in parties.items()}
json.dump({"A": A, "B": B, "geom": geom, "colours": colours, "election": fj["election"],
           "draws": json.loads(man)["draws"], "context_ref": fj["context_ref"]},
          open(OUT + "/data.json", "w"))
for F in (A, B):
    print(F["name"], F["council"], F["majority"], F["coalition"], F["outcome"])
    for r in F["rows"][:10]: print("  ", r)

# calibration for the boldness bands: the chance of each council-level outcome
# with no coalition, and of the start's own outcome
import numpy as np, reweight as R
cell = page._CELLS[page.BASE]; seats, cols = page._party_columns(cell, page.PUBLISHED_LAW)
thr = cell["arrays"][f"council/{page.PUBLISHED_LAW}"][:, 0]; w = R.uniform(seats.shape[0])
cal = {}
for lg in ["ANC", "DA", "ASA", "EFF", "MK", "PA", None]:
    for ma in (False, True):
        p = R.council_outcome(seats, cols, thr, w, largest=lg, majority_alone=ma)
        if p > 0: cal[f"{lg}|{'majority' if ma else 'no majority'}"] = round(p, 4)
for co in (["ANC","DA"], ["ANC","EFF","MK"], ["DA","ASA","EFF"], ["ANC","ASA","EFF"], ["DA","ASA","PA","IFP","VFPLUS","ACDP"], ["ANC","EFF","MK","PA"]):
    for lg in ("ANC", "DA"):
        cal[f"{lg}|no majority|{'+'.join(co)}"] = round(R.council_outcome(seats, cols, thr, w, largest=lg, majority_alone=False, coalition=co), 4)
d = json.load(open(OUT + "/data.json")); d["calibration"] = cal; json.dump(d, open(OUT + "/data.json", "w"))
print(json.dumps(cal, indent=1))
