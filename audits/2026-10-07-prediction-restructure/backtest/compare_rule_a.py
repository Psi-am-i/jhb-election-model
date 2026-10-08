"""Compare rule_a.py's A blocks with §1.290's (results/), all city-years.

    .venv/bin/python audits/2026-10-07-prediction-restructure/backtest/compare_rule_a.py \
        audits/2026-10-07-prediction-restructure/backtest/results <new dir>

Exits 1 on any difference in the compared keys, or on a city-year present on
one side only; then prints the A columns in TABLE.txt's layout. Acceptance
(SPEC-A §1.12): every city-year identical. Reads only; writes nothing.
"""
import json
import sys
from pathlib import Path

KEYS = ("seats", "ward_wins", "seat_err", "wards_ok", "ward_vote_err_pp",
        "list_vote_err_pp", "excessive")

old_dir, new_dir = (Path(a) for a in sys.argv[1:3])
old = {p.name: json.loads(p.read_text()) for p in sorted(old_dir.glob("*.json"))}
new = {p.name: json.loads(p.read_text()) for p in sorted(new_dir.glob("*.json"))}
bad = []
for name in sorted(set(old) | set(new)):
    if name not in old or name not in new:
        bad.append(f"{name}: present in {'new' if name in new else 'old'} only")
        continue
    for k in KEYS:
        a, b = old[name]["A"][k], new[name]["A"][k]
        if a != b:
            bad.append(f"{name}: A.{k} was {a!r}, now {b!r}")
print(f"{len(set(old) & set(new))} city-years compared; {len(old)} old, {len(new)} new")
for line in bad:
    print("DIFFERS", line)
print(f"\n{'city-year':22} {'seats':>5} {'wds':>4} | {'A seat':>6} | {'A ok':>4} | {'A wv':>5} {'A lv':>5} | top A/actual  excess  tied")
for name in sorted(new, key=lambda n: (new[n]["city"], new[n]["year"])):
    r, A = new[name], new[name]["A"]
    print(f"{r['city'] + ' ' + r['year']:22} {r['council']:>5} {r['wards']:>4} | {A['seat_err']:>6.0f} | "
          f"{A['wards_ok']:>4} | {A['ward_vote_err_pp']:>5.1f} {A['list_vote_err_pp']:>5.1f} | "
          f"{A['top']} {A['top_wards']}/{A['top_actual_wards']}  {A['excessive']}  {len(r.get('tied_wards', []))}")
sys.exit(1 if bad else 0)
