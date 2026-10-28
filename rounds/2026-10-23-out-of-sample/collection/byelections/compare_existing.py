"""Compare this collection with the by-election files the model holds (read-only).

Contest key (EEID, WardID), both directions, per cycle; then VD x party votes
where both hold the contest. Writes compare.json beside this file.
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
EXISTING = {
    "2021": REPO / "data/raw/byelections/byelections_SA_vd_party.csv",
    "2016": REPO / "data/raw/byelections/byelections_SA_vd_party_2016.csv",
}


def load(path, cycle=None):
    contests, votes, meta = set(), {}, {}
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if cycle and r.get("cycle") != cycle:
                continue
            k = (str(r["EEID"]), str(r["WardID"]))
            contests.add(k)
            meta[k] = (r["ByElectionDate"], r["Municipality"])
            votes[k + (str(r["VD_Number"]), str(r["PartyID"]))] = int(r["Party_Votes"])
    return contests, votes, meta


out = {}
for cycle, path in EXISTING.items():
    old_c, old_v, old_m = load(path)
    new_c, new_v, new_m = load(HERE / "byelections_vd_party.csv", cycle)
    shared = old_c & new_c
    diffs = [f"{k} old={old_v.get(k)} new={new_v.get(k)}"
             for k in set(old_v) | set(new_v)
             if k[:2] in shared and old_v.get(k) != new_v.get(k)]
    out[cycle] = {
        "existing_file": str(path.relative_to(REPO)),
        "existing_contests": len(old_c), "collected_contests": len(new_c), "shared": len(shared),
        "only_in_collection": sorted(f"{k[0]} {k[1]} {new_m[k][0]} {new_m[k][1]}" for k in new_c - old_c),
        "only_in_existing": sorted(f"{k[0]} {k[1]} {old_m[k][0]} {old_m[k][1]}" for k in old_c - new_c),
        "vd_party_value_differences_in_shared": sorted(diffs),
        "existing_rows": len(old_v), "collected_rows_cycle": len(new_v),
    }
(HERE / "compare.json").write_text(json.dumps(out, indent=1))
for cycle, o in out.items():
    print(cycle, {k: (len(v) if isinstance(v, list) else v) for k, v in o.items()})
