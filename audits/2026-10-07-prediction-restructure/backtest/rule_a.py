"""Rule A through src/prediction.py, one city-year: the reproduction of MODEL-LOG
§1.290's A columns by the shipped function (SPEC-A §1.12).

`one.py` stays as the record of how §1.290 ran (rule A written inline, with an
`eligible_parties` monkeypatch to capture each draw's votes). This script runs
the same set-up with no monkeypatch: the votes are `ModelRun.ward_vote_draws`
and `pr_vote_draws`, the calls and means are `prediction.rule_a`, and the seats
are `prediction.seats_of`. The ENTRANT relabel is applied to the prediction
(calls and both vote dicts, collisions summed) after the rule and before the
seat law, as `one.py` effectively did.

Writes only to the output path given. Run from the repository root:

    PYTHONHASHSEED=0 .venv/bin/python audits/2026-10-07-prediction-restructure/backtest/rule_a.py <city> <year> <out.json>

Then `compare_rule_a.py results <new dir>`.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, "src")
import cityconfig  # noqa: E402
import compare_history as CH  # noqa: E402
import montecarlo as M  # noqa: E402
import prediction  # noqa: E402

city, year, out = sys.argv[1:4]
data_dir = Path("data/raw/elections")
c = cityconfig.use(city)
target = cityconfig.use_target(year)
M.apply_city(c)
scenario = M.load_scenario(argparse.Namespace(config=None, set=[], draws=1000, seed=None,
                                              city=city, target=year))
run = M.run_model(target, scenario, data_dir, verbose=False)
n = len(run.seat_draws)

pred = prediction.rule_a(run.ward_winner_draws, run.universe, run.wards,
                         run.ward_vote_draws, run.pr_vote_draws, run.universe)

# ties the rule broke by string order (JUDGEMENT-CALLS §Q2): one.py broke them
# by universe index, so a tied ward is where the two can differ
counts = np.zeros((len(run.wards), len(run.universe)), dtype=np.int64)
for j in range(len(run.wards)):
    counts[j] = np.bincount(run.ward_winner_draws[:, j].astype(np.int64),
                            minlength=len(run.universe))
tied = [str(w) for j, w in enumerate(run.wards)
        if (counts[j] == counts[j].max()).sum() > 1]

actual_pr, actual_ward = CH.actual_shares(target, data_dir)
actual_seats, entrant, actual_winners = CH._actual_seats(target, data_dir)


def ren(p):
    return entrant if (entrant and p == "ENTRANT") else p


def rn(d):
    o = Counter()
    for k, v in d.items():
        o[ren(k)] += v
    return dict(o)


pred = {"ward_calls": [ren(p) for p in pred["ward_calls"]],
        "ward_votes": rn(pred["ward_votes"]), "list_votes": rn(pred["list_votes"])}
seated = prediction.seats_of(pred, M.COUNCIL)
seatsA = {p: v["total"] for p, v in seated["seats"].items() if v["total"]}
wards = [str(w) for w in run.wards]
wins = dict(Counter(pred["ward_calls"]))
overA = seated["excessive"]


def shares(d):
    t = sum(d.values())
    return {p: v / t for p, v in d.items()} if t else {}


def l1(a, b):
    ks = set(a) | set(b)
    return float(sum(abs(a.get(k, 0) - b.get(k, 0)) for k in ks))


assert sum(1 for w in wards if w in actual_winners) == len(wards), "ward ids do not align"
act_wins = Counter(actual_winners.values())
topA = max(wins, key=wins.get)
res = {
    "city": city, "year": year, "draws": n, "council": target.council, "wards": len(wards),
    "tied_wards": tied,
    "A": {"seats": seatsA, "seat_err": l1(seatsA, actual_seats),
          "wards_ok": sum(1 for w, p in zip(wards, pred["ward_calls"]) if actual_winners.get(w) == p),
          "ward_vote_err_pp": 100 * l1(shares(pred["ward_votes"]), actual_ward),
          "list_vote_err_pp": 100 * l1(shares(pred["list_votes"]), actual_pr),
          "top": topA, "top_wards": wins[topA], "top_actual_wards": act_wins.get(topA, 0),
          "excessive": {p: {"wards": wins[p], "actual_seats": actual_seats.get(p, 0),
                            "actual_wards": act_wins.get(p, 0)} for p in sorted(overA)},
          "council": seated["council"], "ward_wins": wins},
}
Path(out).write_text(json.dumps(res, indent=1, default=str))
print(city, year, "A", res["A"]["seat_err"], res["A"]["wards_ok"], "tied", len(tied))
