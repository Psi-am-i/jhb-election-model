"""Shared loading for the best-cases analysis. Reads only; writes nothing."""
import csv, json, sys, re
from collections import defaultdict
from pathlib import Path
import numpy as np
ROOT = Path("/Users/simondavis/projects/atlas-jhb-election-model")
sys.path.insert(0, str(ROOT / "src"))
import reweight as R
import scenarios as SC

MAIN = ["ANC", "DA", "ASA", "EFF", "PA", "MK"]
NAMES = {"DA": "DA", "ANC": "ANC", "EFF": "EFF", "MK": "MK Party", "ASA": "ActionSA",
         "PA": "PA", "IFP": "IFP", "ALJAMAAH": "Al Jama-ah", "RISE": "Rise Mzansi",
         "ACDP": "ACDP", "VFPLUS": "VF Plus", "ENTRANT": "a new party"}


def load():
    m = json.loads((ROOT / "site/draws/manifest.json").read_text())
    b = R.unpack((ROOT / "site/draws/base.bin").read_bytes(), m)
    cols = {blk["name"]: blk["columns"] for blk in m["blocks"]}
    D = {"m": m, "b": b, "cols": cols}
    D["seat_cols"] = cols["seats/deduct"]
    D["S"] = b["seats/deduct"].astype(int)
    D["thr"] = b["council/deduct"][:, 0].astype(int)
    D["council"] = b["council/deduct"][:, 1].astype(int)
    D["wards"] = cols["ward_winner"]
    D["wp"] = m["ward_parties"]
    D["W"] = b["ward_winner"]
    D["vcols"] = cols["ward_vote"]
    assert cols["ward_vote"] == cols["list_vote"]
    wv = b["ward_vote"].astype(float); lv = b["list_vote"].astype(float)
    D["wshare"] = wv / wv.sum(1, keepdims=True)
    D["lshare"] = R.list_shares(lv)
    D["turn"] = b["pool_turnout"]; D["turn_names"] = cols["pool_turnout"]
    n = D["S"].shape[0]
    det = defaultdict(dict)
    with (ROOT / "data/processed/seat_detail_draws.csv").open() as fh:
        for r in csv.DictReader(fh):
            det[int(r["draw"])][r["party"]] = (int(r["ward_seats"]), int(r["list_seats"]),
                                                int(r["seats"]), r["excessive"] == "1")
    D["det"] = det
    parties = sorted({p for d in det.values() for p in d})
    D["wseats"] = {p: np.array([det[i].get(p, (0, 0, 0, 0))[0] for i in range(n)]) for p in parties}
    D["lseats"] = {p: np.array([det[i].get(p, (0, 0, 0, 0))[1] for i in range(n)]) for p in parties}
    D["exc"] = {p: np.array([det[i].get(p, (0, 0, 0, 0))[3] for i in range(n)]) for p in parties}
    D["exc_any"] = np.array([any(v[3] for v in det[i].values()) for i in range(n)])
    # every party's total seats agrees between the two files (checked)
    for j, p in enumerate(D["seat_cols"]):
        if p == "OTHER":
            continue
        tot = D["wseats"].get(p, 0) + D["lseats"].get(p, 0)
        assert np.array_equal(D["S"][:, j], tot if not np.isscalar(tot) else np.zeros(n)), p
    return D


def seats(D, p):
    return D["S"][:, D["seat_cols"].index(p)]


def ward_freq(D, p, idx=None):
    W = D["W"] if idx is None else D["W"][idx]
    if p not in D["wp"]:
        return np.zeros(W.shape[1])
    return (W == D["wp"].index(p)).mean(0)


def areas():
    txt = (ROOT / "content/joburg/areas.toml").read_text()
    soweto = set(re.search(r"wards = \[([^\]]*)\]", txt).group(1).replace(" ", "").split(","))
    paths = json.loads((ROOT / "data/processed/ward_paths.json").read_text())
    labels = [l for l in paths["labels"] if l["t"] != "Soweto"]
    out = {}
    for w, d in paths["paths"].items():
        pts = np.array([[float(x) for x in s.split()] for s in re.split(r"[MLZ]", d) if s.strip()])
        cx, cy = pts.mean(0)
        if w in soweto:
            out[w] = "Soweto"
        else:
            near = min(labels, key=lambda l: (l["x"] - cx) ** 2 + (l["y"] - cy) ** 2)
            out[w] = "near " + near["t"]
    return out, paths
