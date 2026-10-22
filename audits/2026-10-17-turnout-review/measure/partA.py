"""Part A: turnout forecast accuracy against real results, 24 city-years.

Projection = turnout.py main() regenerated into regen/ (identical to the
on-disk data/processed/<city>/<T>/turnout.csv at all 24, checked by cmp).
Blend replicates montecarlo.run_model: ratio = turnout_<T>_projected; level =
raw turnout_<prevLGE> capped at 1, rescaled to the ratio's roll-weighted mean;
centre = 0.5 ratio + 0.5 level (DEFAULTS turnout_pattern_blend). Roll = the
target's own registered voters per VD (what ward_parts reads for a held target).
"""
from __future__ import annotations

import csv
import json
import sys

import numpy as np

from common import (CITIES, OUT, cityconfig, pr_votes, realised_turnout,
                    turnout, wcorr, wstats)
import pools  # noqa: E402

BLEND = 0.5
TARGETS = ["2011", "2016", "2021"]
cfg = pools.load_config()

rowsA, rowsVD, rowsPool, rowsPart = [], [], [], []

for city in CITIES:
    for T in TARGETS:
        c = cityconfig.use(city)
        tgt = cityconfig.use_target(T)
        prev = tgt.previous_lge
        regen = OUT / "regen" / f"turnout_{city}_{T}.csv"
        proj, lvl = {}, {}
        with regen.open() as fh:
            for r in csv.DictReader(fh):
                v = r[f"turnout_{T}_projected"]
                if v:
                    proj[r["VD_Number"]] = float(v)
                lv = r.get(f"turnout_{prev}")
                if lv and lv != "nan":
                    lvl[r["VD_Number"]] = min(float(lv), 1.0)
        counts = realised_turnout(T)
        city_real = turnout.citywide(counts)
        prev_counts = realised_turnout(prev)
        city_prev = turnout.citywide(prev_counts)
        vds = sorted(v for v, (r, _) in counts.items() if r > 0)
        reg = np.array([counts[v][0] for v in vds], float)
        cast = np.array([counts[v][1] for v in vds], float)
        t_real = cast / reg
        own = np.array([v in proj for v in vds])
        t_ratio = np.array([proj.get(v, np.nan) for v in vds])
        t_level = np.array([lvl.get(v, np.nan) for v in vds])
        m_ratio = np.nansum(t_ratio * reg) / reg[~np.isnan(t_ratio)].sum()
        m_level = np.nansum(t_level * reg) / reg[~np.isnan(t_level)].sum()
        t_ratio_f = np.where(np.isnan(t_ratio), m_ratio, t_ratio)
        t_level_raw = np.where(np.isnan(t_level), m_level, t_level)
        t_level_f = t_level_raw * (m_ratio / m_level)
        centre = (1 - BLEND) * t_ratio_f + BLEND * t_level_f
        cw = lambda t: float((t * reg).sum() / reg.sum())

        # pool band -> approximate draw-mean factor (band mean / mode)
        spec = json.loads((c.processed / f"pools_{T}.json").read_text())
        band = {g: tuple(p["turnout"]) for g, p in spec["pools"].items()}
        vref = {g: spec["pools"][g]["registered"] * band[g][1] for g in band}
        kfac = sum(vref[g] * (sum(band[g]) / 3) / band[g][1] for g in band) / sum(vref.values())

        rowsA.append(dict(city=city, target=T, prev_lge=prev,
                          realised_citywide=100 * city_real,
                          projected_centre=100 * cw(centre),
                          projected_ratio=100 * cw(t_ratio_f),
                          projected_level=100 * cw(t_level_f),
                          naive_prev_lge_citywide=100 * city_prev,
                          err_centre=100 * (city_real - cw(centre)),
                          err_naive_prev=100 * (city_real - city_prev),
                          roll_share_own_projection=100 * reg[own].sum() / reg.sum(),
                          band_mean_over_mode_factor=kfac,
                          approx_draw_mean=100 * cw(centre) * kfac,
                          err_approx_draw_mean=100 * (city_real - cw(centre) * kfac)))

        # ---- VD level
        ok = own & ~np.isnan(t_level) & (t_real <= 1.05)
        w = reg[ok]; y = t_real[ok]
        preds = {
            "centre": centre[ok], "ratio": t_ratio_f[ok], "level_rescaled": t_level_f[ok],
            "naive_prev_lge": t_level_raw[ok],
            "prev_lge_x_oracle_city_change": t_level_raw[ok] * city_real / city_prev,
        }
        yc = (y * w).sum() / w.sum()
        for name, p in preds.items():
            e = y - p
            pc = (p * w).sum() / w.sum()
            e_pat = y - p * yc / pc  # pattern only: predictor rescaled to the realised mean
            rowsVD.append(dict(city=city, target=T, predictor=name, n_vds=int(ok.sum()),
                               roll_share=100 * w.sum() / reg.sum(),
                               mean_err=100 * np.average(e, weights=w),
                               rmse=100 * np.sqrt(np.average(e ** 2, weights=w)),
                               mae=100 * np.average(np.abs(e), weights=w),
                               rmse_pattern_only=100 * np.sqrt(np.average(e_pat ** 2, weights=w)),
                               mae_pattern_only=100 * np.average(np.abs(e_pat), weights=w),
                               wcorr=wcorr(p, y, w)))

        # ---- partisan structure of the error (prev-LGE list shares)
        pv = pr_votes(prev)
        sh = {}
        for v in vds:
            tot = sum(pv.get(v, {}).values())
            sh[v] = {p: (pv[v].get(p, 0) / tot if tot else np.nan) for p in ("DA", "ANC", "EFF")}
        S = {p: np.array([sh[v][p] for v in vds]) for p in ("DA", "ANC", "EFF")}
        okp = ok & ~np.isnan(S["DA"])
        err = 100 * (t_real - centre)
        wp = reg[okp]
        rec = dict(city=city, target=T, prev_lge=prev, n_vds=int(okp.sum()))
        for p in ("DA", "ANC", "EFF"):
            s = 100 * S[p][okp]
            if np.nanmax(s) <= 0:
                rec[f"slope_err_per10pts_{p}"] = ""; rec[f"se_{p}"] = ""; rec[f"wcorr_{p}"] = ""
                continue
            b, se = wstats(s, err[okp], wp)
            rec[f"slope_err_per10pts_{p}"] = 10 * b[1]
            rec[f"se_{p}"] = 10 * se[1]
            rec[f"wcorr_{p}"] = wcorr(s, err[okp], wp)
        da_maj = okp & (S["DA"] > 0.5); anc_maj = okp & (S["ANC"] > 0.5)
        rec["mean_err_DA_majority_VDs"] = np.average(err[da_maj], weights=reg[da_maj]) if da_maj.any() else np.nan
        rec["mean_err_ANC_majority_VDs"] = np.average(err[anc_maj], weights=reg[anc_maj]) if anc_maj.any() else np.nan
        rec["roll_share_DA_maj"] = 100 * reg[da_maj].sum() / reg.sum()
        rec["roll_share_ANC_maj"] = 100 * reg[anc_maj].sum() / reg.sum()
        rec["DAmaj_minus_ANCmaj"] = rec["mean_err_DA_majority_VDs"] - rec["mean_err_ANC_majority_VDs"]
        # item 11: fixed prev-LGE VD shares, reweighted by realised vs projected turnout
        for p in ("DA", "ANC", "EFF"):
            s = S[p][okp]
            if np.nanmax(s) <= 0:
                rec[f"oracle_composition_shift_{p}"] = ""; continue
            wr = reg[okp] * t_real[okp]; wc = reg[okp] * centre[okp]
            rec[f"oracle_composition_shift_{p}"] = 100 * ((wr * s).sum() / wr.sum() - (wc * s).sum() / wc.sum())
        rowsPart.append(rec)

        # ---- pool level
        try:
            real_pc = pools.pool_counts(c, T, cfg)
            ref_pc = pools.pool_counts(c, spec["fitted_on"], cfg)
        except BaseException as exc:  # noqa: BLE001  (pool_counts refuses with SystemExit)
            print(f"{city} {T}: pool_counts failed: {exc}", file=sys.stderr)
            continue
        for i, g in enumerate(real_pc.categories):
            if g not in band:
                continue
            lo, md, hi = band[g]
            r = float(real_pc.rates["turnout"][i])
            j = list(ref_pc.categories).index(g)
            rowsPool.append(dict(city=city, target=T, pool=g, fitted_on=spec["fitted_on"],
                                 band_low=100 * lo, band_mode=100 * md, band_high=100 * hi,
                                 band_mean=100 * (lo + md + hi) / 3,
                                 reference_pool_counts_fitted_on=100 * float(ref_pc.rates["turnout"][j]),
                                 mode_minus_reference=100 * (md - float(ref_pc.rates["turnout"][j])),
                                 realised_ecological=100 * r,
                                 err_vs_mode=100 * (r - md), err_vs_mean=100 * (r - (lo + md + hi) / 3),
                                 inside_band=lo <= r <= hi,
                                 imputed_turnout=i in (real_pc.imputed or {}).get("turnout", []),
                                 unidentified=g in (real_pc.unidentified or [])))
        print(f"done {city} {T}", file=sys.stderr)


def dump(name, rows):
    with (OUT / name).open("w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0]))
        wr.writeheader()
        for r in rows:
            wr.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()})


dump("partA1_citywide.csv", rowsA)
dump("partA2_vd.csv", rowsVD)
dump("partA3_pool.csv", rowsPool)
dump("partA4_partisan_error.csv", rowsPart)
