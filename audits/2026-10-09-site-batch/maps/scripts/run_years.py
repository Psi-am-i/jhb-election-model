"""Run the Joburg backtests in-process, as compare_history.run_city_year sets them up.

Writes only to the maps directory given. Usage: run_years.py OUTDIR YEAR...
"""
import argparse
import csv
import json
import sys
from pathlib import Path

REPO = Path("/Users/simondavis/projects/atlas-jhb-election-model")
sys.path.insert(0, str(REPO / "src"))

import numpy as np
import cityconfig
import montecarlo as M
import backtest as B
import score as S
import prediction
import compare_history as CH

out = Path(sys.argv[1])
DRAWS = 1000  # compare_history --draws default
for year in sys.argv[2:]:
    city = cityconfig.use("joburg")
    target = cityconfig.use_target(year)
    M.apply_city(city)
    scenario = M.load_scenario(argparse.Namespace(
        config=None, set=[], draws=DRAWS, seed=None, city="joburg", target=year))
    run = M.run_model(target, scenario, REPO / "data/raw/elections", verbose=False, run_dir=None)
    draws = int(run.ward_winner_counts.sum(axis=1)[0])

    def _p_win(c):
        return (c + 0.5) / (draws + 1.0)

    rows = []
    for wi, w in enumerate(run.wards):
        cnt = run.ward_winner_counts[wi]
        order = np.argsort(-cnt)
        dist = "|".join(f"{run.universe[i]}:{_p_win(cnt[i]):.4f}" for i in order if cnt[i] > 0)
        rows.append([w, run.universe[order[0]], f"{_p_win(cnt[order[0]]):.4f}", dist])
    with (out / f"forecast_{year}_ward_winner_probs.csv").open("w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["ward", "winner", "p_win", "dist"])
        wr.writerows(rows)

    seats, entrant, winners = CH._actual_seats(target, REPO / "data/raw/elections")
    pre = run.ward_probabilities()
    sc_pre = S.score_wards(pre, winners)
    run2 = B.relabel_run(run, entrant)
    post = run2.ward_probabilities()
    sc_post = S.score_wards(post, winners)
    top_pre = {w: prediction.top_party(p) for w, p in pre.items()}
    argmax_rows = {r[0]: r[1] for r in rows}
    mism = [w for w in top_pre if top_pre[w] != argmax_rows[w]]
    with (out / f"result_{year}_ward_winners.csv").open("w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["ward", "winner"])
        for w in sorted(winners, key=lambda k: int(k)):
            wr.writerow([w, winners[w]])
    meta = {
        "year": year, "draws": draws, "n_run_wards": len(run.wards),
        "n_result_wards": len(winners),
        "matched": sum(1 for w in winners if pre.get(w)),
        "called_pre_relabel": sc_pre["modal_calls_correct"],
        "called_post_relabel": sc_post["modal_calls_correct"],
        "entrant_actual": entrant,
        "modal_entrant_wards": [w for w, p in top_pre.items() if p == "ENTRANT"],
        "top_party_vs_argmax_mismatch": mism,
        "solid": sum(1 for r in rows if float(r[2]) >= 0.90),
        "sample_run_ward": run.wards[0], "sample_result_ward": next(iter(winners)),
        "modal_calls_wrong": sorted(
            [(w, top_pre.get(w), winners[w]) for w in winners if top_pre.get(w) != winners[w]],
            key=lambda t: int(t[0])),
    }
    (out / f"meta_{year}.json").write_text(json.dumps(meta, indent=1, default=str))
    print(json.dumps({k: v for k, v in meta.items() if k != "modal_calls_wrong"}, default=str), flush=True)
