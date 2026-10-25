"""Build the old-against-new model report for one forecast-moving round.

Owner, 2026-10-14: every round that moves the forecast gets this report, kept
here. One folder per round, ``reports/model-changes/<date>/``, holding:

* ``lede.html`` and ``why.html``: the round's own words, written by hand
  (what changed and why, in plain terms, no internal labels);
* ``f2026.json`` and ``backtest.json``: written by this script;
* ``report.html``: the page, written by this script from ``template.html``.

Inputs. The two forecasts are arm runs with their arrays saved
(``arrays.npz`` + ``meta.json``, as ``src/arms.py run`` and the batch arms
write them), same draws and seed. The two backtests are ``history.json``
files from ``src/compare_history.py``, same draws and seed; the old one is
usually the tracked file at the commit before the round, given as
``REV:path``. Give both histories or neither: with neither (a round whose
inputs no backtest tests), no ``history.json`` is read, ``backtest.json`` is
``null`` and the backtest panel says only ``NO_BACKTEST``.

    .venv/bin/python reports/model-changes/build_report.py \\
        --old-arm data/arms/step11/A/joburg-2026 \\
        --new-arm .claude/step7-2026-10-13/arms/U/joburg-2026 \\
        --old-history 7f0a921:data/processed/history.json \\
        --new-history data/processed/history.json \\
        --round reports/model-changes/2026-10-14

Reads only; writes only into ``--round``.

Per party the forecast carries mean seats (``seats``), median seats
(``median``), the 5-95% range, list share, wards won, the largest-party chance
(ties split evenly among the tied) and the majority chance.
"""
import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
NO_BACKTEST = "No backtest: neither input is tested by any backtest."
PARTIES = ["ANC", "DA", "EFF", "ASA", "MK", "PA", "IFP", "ACDP", "VFPLUS",
           "RISE", "ALJAMAAH"]


def load_arm(d):
    d = Path(d)
    f = np.load(d / "arrays.npz", allow_pickle=True)
    cols = json.loads((d / "meta.json").read_text())["seat_cols"]
    return f["seat_draws"], f["ward_winner_draws"], f["pr_share_draws"], cols


def forecast(arms, council):
    majority = council // 2 + 1
    out = {"parties": {}, "wards": {}, "any_majority": {}}
    for name, (sd, ww, pr, cols) in arms.items():
        n = sd.shape[0]
        mx = sd.max(1)
        n_top = (sd == mx[:, None]).sum(1)
        for p in PARTIES:
            if p not in cols:
                continue
            i = cols.index(p)
            s = sd[:, i]
            out["parties"].setdefault(p, {})[name] = {
                "seats": round(float(s.mean()), 1),
                "median": float(np.median(s)),
                "lo": int(np.percentile(s, 5)),
                "hi": int(np.percentile(s, 95)),
                "vote": round(100 * float(pr[:, i].mean()), 1),
                "wards": round(float((ww == i).sum(1).mean()), 1),
                # a tie for most seats is split evenly among the tied parties
                "largest": round(100 * float(((s == mx) / n_top).mean())),
                "majority": round(100 * float((s >= majority).mean()), 1),
            }
        for w in range(ww.shape[1]):
            v, c = np.unique(ww[:, w], return_counts=True)
            o = c.argsort()[::-1]
            out["wards"].setdefault(str(w + 1), {})[name] = {
                "fav": cols[v[o[0]]], "p": round(float(c[o[0]] / n), 2),
                "second": cols[v[o[1]]] if len(o) > 1 else None,
                "p2": round(float(c[o[1]] / n), 2) if len(o) > 1 else 0}
        out["any_majority"][name] = round(100 * float((mx >= majority).mean()), 1)
    return out


def read_history(spec):
    if ":" in spec and not Path(spec).exists():
        return json.loads(subprocess.check_output(["git", "show", spec], cwd=ROOT))
    return json.loads(Path(spec).read_text())


def backtest(old, new):
    key = lambda r: (r["slug"], r["year"])
    old = {key(r): r for r in old["records"]}

    def pick(x):
        w = x["wards"]
        return {"wards_n": w["n_wards"], "called": w["called"],
                "wrong_seats": x["seat_abs_err_coherent"] / 2,
                "vote_err": round(x["pr_mae"], 2), "seats": x["seats"]}

    return [{"city": r["city"], "slug": r["slug"], "year": r["year"],
             "council": r["council"], "old": pick(old[key(r)]), "new": pick(r)}
            for r in new["records"]]


IN_SAMPLE_START, IN_SAMPLE_END = "<!-- __IN_SAMPLE_START__ -->", "<!-- __IN_SAMPLE_END__ -->"


def in_sample_banner(page, backtest):
    """``page`` with the in-sample banner kept when ``backtest`` holds scores
    and cut, markers and all, when it is ``None`` (no backtest panel, so no
    score for the banner to describe). The banner's words stay in
    ``template.html``; ``tests/test_quarantine.py`` checks every scored
    report carries them."""
    a, z = page.index(IN_SAMPLE_START), page.index(IN_SAMPLE_END) + len(IN_SAMPLE_END)
    if backtest is None:
        return page[:a].rstrip(" ") + page[z:].lstrip("\n")
    return (page[:a].rstrip(" ") + page[a + len(IN_SAMPLE_START):z - len(IN_SAMPLE_END)].strip("\n").rstrip()
            + "\n" + page[z:].lstrip("\n"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old-arm", required=True)
    ap.add_argument("--new-arm", required=True)
    ap.add_argument("--old-history", default=None)
    ap.add_argument("--new-history", default=None)
    ap.add_argument("--round", required=True, type=Path)
    ap.add_argument("--council", type=int, default=270)
    ap.add_argument("--map", default=str(ROOT / "data/processed/ward_paths.json"))
    a = ap.parse_args()
    if (a.old_history is None) != (a.new_history is None):
        ap.error("give both --old-history and --new-history, or neither")

    f = forecast({"old": load_arm(a.old_arm), "new": load_arm(a.new_arm)}, a.council)
    b = (None if a.old_history is None
         else backtest(read_history(a.old_history), read_history(a.new_history)))
    (a.round / "f2026.json").write_text(json.dumps(f))
    (a.round / "backtest.json").write_text(json.dumps(b))
    page = in_sample_banner((HERE / "template.html").read_text(), b)
    for k, v in {"__LEDE__": (a.round / "lede.html").read_text(),
                 "__WHY__": (a.round / "why.html").read_text(),
                 "__F2026__": json.dumps(f), "__BACKTEST__": json.dumps(b),
                 "__NO_BACKTEST__": json.dumps(NO_BACKTEST),
                 "__MAP__": Path(a.map).read_text()}.items():
        page = page.replace(k, v)
    (a.round / "report.html").write_text(page)
    print(f"wrote {a.round / 'report.html'}")


if __name__ == "__main__":
    main()
