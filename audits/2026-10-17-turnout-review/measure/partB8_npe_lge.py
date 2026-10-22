"""Part B extra (B8): same decomposition NPE -> following LGE. Part B: what turnout does to list (PR) shares in the real record. No model.

Join: VD number identity between consecutive LGEs (build_concordance.py's own
finding: VD numbers are stable and the concordance is keyed on identity). A
VD whose registration moved more than 30% relative to the city's change is
flagged 'unstable' (the same proxy build_concordance uses), and every
quantity is reported on all joined VDs and on stable ones only.
"""
from __future__ import annotations

import csv

import numpy as np

from common import CITIES, OUT, cityconfig, pr_votes, realised_turnout, wcorr, wols

PAIRS = [("2009", "2011"), ("2014", "2016"), ("2019", "2021")]
ID = "INDEPENDENT_DEMOCRATS"
rows_dec, rows_reg = [], []


def share(w, s):
    return float((w * s).sum() / w.sum())


for city in CITIES:
    cityconfig.use(city)
    for y0, y1 in PAIRS:
        cityconfig.use_target(y1)
        pv0, pv1 = pr_votes(y0), pr_votes(y1)
        c0, c1 = realised_turnout(y0), realised_turnout(y1)
        tot0 = {v: sum(d.values()) for v, d in pv0.items()}
        tot1 = {v: sum(d.values()) for v, d in pv1.items()}
        city_ratio = sum(r for r, _ in c1.values()) / sum(r for r, _ in c0.values())
        common = [v for v in sorted(set(c0) & set(c1) & set(pv0) & set(pv1))
                  if c0[v][0] > 0 and c1[v][0] > 0 and tot0[v] > 0 and tot1[v] > 0
                  and c0[v][1] / c0[v][0] <= 1.05 and c1[v][1] / c1[v][0] <= 1.05]
        stable = {v for v in common
                  if abs((c1[v][0] / c0[v][0]) / city_ratio - 1) <= 0.30}
        parties_ = ["DA", "ANC"]
        if any("EFF" in d for d in pv0.values()):
            parties_.append("EFF")
        if y0 == "2006" and any(ID in d for d in pv0.values()):
            parties_.append("DA+ID")

        def sv(pv, tot, v, p):
            if p == "DA+ID":
                return (pv[v].get("DA", 0) + pv[v].get(ID, 0)) / tot[v]
            return pv[v].get(p, 0) / tot[v]

        allV0 = sum(tot0.values()); allV1 = sum(tot1.values())
        for subset_name, subset in (("all_joined", common), ("stable_only", [v for v in common if v in stable])):
            reg0 = np.array([c0[v][0] for v in subset], float)
            reg1 = np.array([c1[v][0] for v in subset], float)
            cast0 = np.array([c0[v][1] for v in subset], float)
            cast1 = np.array([c1[v][1] for v in subset], float)
            V0 = np.array([tot0[v] for v in subset], float)
            V1 = np.array([tot1[v] for v in subset], float)
            Wb = reg1 * V0 / reg0  # new roll at old (valid-vote) turnout
            t0 = cast0 / reg0; t1 = cast1 / reg1
            for p in parties_:
                s0 = np.array([sv(pv0, tot0, v, p) for v in subset])
                s1 = np.array([sv(pv1, tot1, v, p if p != "DA+ID" else "DA") for v in subset])
                # citywide over ALL VDs
                cw0 = sum(sv(pv0, tot0, v, p) * tot0[v] for v in pv0 if tot0[v]) / allV0
                cw1 = sum(sv(pv1, tot1, v, p if p != "DA+ID" else "DA") * tot1[v] for v in pv1 if tot1[v]) / allV1
                actual = share(V1, s1) - share(V0, s0)
                between = share(V1, s0) - share(V0, s0)
                reg_part = share(Wb, s0) - share(V0, s0)
                turn_part = share(V1, s0) - share(Wb, s0)
                within = share(V1, s1 - s0)
                rows_dec.append(dict(city=city, pair=f"{y0}-{y1}", subset=subset_name, party=p,
                                     n_vds=len(subset),
                                     vote_share_joined_t0=100 * V0.sum() / allV0,
                                     vote_share_joined_t1=100 * V1.sum() / allV1,
                                     citywide_share_t0_allVDs=100 * cw0, citywide_share_t1_allVDs=100 * cw1,
                                     citywide_change_allVDs=100 * (cw1 - cw0),
                                     change_joined=100 * actual, between_total=100 * between,
                                     between_registration=100 * reg_part, between_turnout=100 * turn_part,
                                     within=100 * within,
                                     citywide_turnout_change=100 * (cast1.sum() / reg1.sum() - cast0.sum() / reg0.sum())))
                # ---- item 6: within-VD differential turnout
                ds = 100 * (s1 - s0); dt = 100 * (t1 - t0)
                w = V1
                spec = {
                    "ds~dt": np.column_stack([np.ones_like(dt), dt]),
                    "ds~dt+s0": np.column_stack([np.ones_like(dt), dt, 100 * s0]),
                    "ds~dt+s0+t0": np.column_stack([np.ones_like(dt), dt, 100 * s0, 100 * t0]),
                }
                for name, X in spec.items():
                    b, se = wols(X, ds, w)
                    rows_reg.append(dict(city=city, pair=f"{y0}-{y1}", subset=subset_name, party=p,
                                         model=name, n_vds=len(subset), slope_share_per_turnout_pt=b[1],
                                         robust_se=se[1], wcorr_ds_dt=wcorr(dt, ds, w)))
                # mixed vs homogeneous VDs (prev DA and ANC shares both 20-80%)
                da0 = np.array([sv(pv0, tot0, v, "DA") for v in subset])
                anc0 = np.array([sv(pv0, tot0, v, "ANC") for v in subset])
                mixed = (da0 > 0.2) & (da0 < 0.8) & (anc0 > 0.2) & (anc0 < 0.8)
                for lab, m in (("mixed_DA_ANC_20to80", mixed), ("not_mixed", ~mixed)):
                    if m.sum() >= 15:
                        X = np.column_stack([np.ones(m.sum()), dt[m], 100 * s0[m]])
                        b, se = wols(X, ds[m], w[m])
                        rows_reg.append(dict(city=city, pair=f"{y0}-{y1}", subset=subset_name, party=p,
                                             model=f"ds~dt+s0 [{lab}]", n_vds=int(m.sum()),
                                             slope_share_per_turnout_pt=b[1], robust_se=se[1],
                                             wcorr_ds_dt=wcorr(dt[m], ds[m], w[m])))


def dump(name, rows):
    with (OUT / name).open("w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0]))
        wr.writeheader()
        for r in rows:
            wr.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()})


dump("partB8_npe_to_lge_decomposition.csv", rows_dec)
dump("partB8_npe_to_lge_regression.csv", rows_reg)
