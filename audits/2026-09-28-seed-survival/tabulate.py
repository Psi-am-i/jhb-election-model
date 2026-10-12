"""Tabulate seed_survival.py outputs. Usage: tabulate.py <out_dir>"""
import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
rows = [json.loads(p.read_text()) for p in sorted(out.glob("*-*.json"))]
VARS = ["placebo", "c4_eps", "c4_mild", "c4_strong", "c3_target", "c3_proj"]


def matters(c):
    return (c["seats_moved"] >= 1.0 and c["max_z"] > 3) or c["ward_calls_moved"] >= 1.0


print(f"commit {(out / 'COMMIT').read_text().strip() if (out / 'COMMIT').exists() else '?'}; "
      f"{len(rows)} city-years; draws {rows[0]['draws'] if rows else '?'}\n")
print("## Structure: IPF preserves the seed's interaction exactly\n")
print("| city-year | zero cells | single-pool parties | log-ratio resid | zeros kept (R0, every draw) | seed->post-IPF TV, seat-weighted mean over parties |")
print("|---|---|---|---|---|---|")
for r in rows:
    s = r.get("structure", {})
    c = s.get("mean_seats") or {}  # weight: the party's mean seats in base
    tv = s.get("seed_vs_post_ipf_tv", {})
    w = sum(c.get(p, 0) for p in tv)
    wtv = sum(c.get(p, 0) * tv[p] for p in tv) / w if w else float("nan")
    print(f"| {r['city']} {r['year']} | {s.get('zero_cells')}/{s.get('cells')} | "
          f"{len(s.get('single_pool_parties', []))} | {s.get('logratio_additive_max_resid', float('nan')):.1e} | "
          f"{s.get('zero_pattern_identical_R0')}, {s.get('zero_pattern_identical_draws')} | {wtv:.3f} |")

print("\n## Outcome sensitivity: expected seats moved (max paired z) / expected ward calls moved\n")
print("| city-year | seed2 (unpaired floor) | " + " | ".join(VARS) + " | C3 dose (L1/roll) |")
print("|---|---|" + "---|" * len(VARS) + "---|")
flag = {v: [] for v in VARS}
for r in rows:
    V = r["variants"]
    cells = []
    s2 = V.get("seed2", {}).get("vs_base")
    cells.append(f"{s2['seats_moved']:.2f} / {s2['ward_calls_moved']:.2f}" if s2 else "-")
    for v in VARS:
        d = V.get(v, {})
        c = d.get("vs_base")
        if not c:
            cells.append("n/a")
            continue
        m = "**" if matters(c) else ""
        if matters(c):
            flag[v].append(f"{r['city']} {r['year']}")
        cells.append(f"{m}{c['seats_moved']:.2f} ({c['max_z']:.1f}) / {c['ward_calls_moved']:.2f}{m}")
    dose = V.get("c3_target", {}).get("info", {}).get("dose_L1_of_roll")
    cells.append(f"{dose:.3f}" if dose is not None else "n/a")
    print(f"| {r['city']} {r['year']} | " + " | ".join(cells) + " |")

print("\n## Panel totals (sum over city-years)\n")
for v in ["seed2"] + VARS:
    cs = [r["variants"].get(v, {}).get("vs_base") for r in rows]
    cs = [c for c in cs if c]
    print(f"- {v}: {len(cs)} city-years; seats moved {sum(c['seats_moved'] for c in cs):.1f}; "
          f"ward calls moved {sum(c['ward_calls_moved'] for c in cs):.1f}; "
          f"max |dPR| {max((c['max_abs_d_pr_pp'] for c in cs), default=0):.2f}pp; "
          f"matters at: {', '.join(flag.get(v, [])) or 'none'}")

print("\n## Per party: |d mean seats| >= 0.5 and paired z > 3\n")
print("| variant | city-year | party | d mean seats | paired SE |")
print("|---|---|---|---|---|")
for v in VARS:
    for r in rows:
        c = r["variants"].get(v, {}).get("vs_base")
        if not c:
            continue
        for p, d in sorted(c["d_mean_seats"].items(), key=lambda kv: -abs(kv[1])):
            se = c["se_paired"][p]
            if abs(d) >= 0.5 and se > 0 and abs(d) / se > 3:
                print(f"| {v} | {r['city']} {r['year']} | {p} | {d:+.2f} | {se:.2f} |")

print("\n## Guards that differ from base (cap channel)\n")
for r in rows:
    b = r["variants"].get("base", {}).get("guards", {})
    for v in VARS:
        g = r["variants"].get(v, {}).get("guards")
        if not g:
            continue
        diff = {k: (b.get(k), g.get(k)) for k in ("ipf_failures", "cap_moved", "ipf_clipped")
                if b.get(k) != g.get(k)}
        if diff:
            print(f"- {r['city']} {r['year']} {v}: {diff}")
    if b.get("stale"):
        print(f"- {r['city']} {r['year']}: spec STALE: {b['stale']}")
for r in rows:
    for v, d in r["variants"].items():
        if "skipped" in d:
            print(f"- skipped {r['city']} {r['year']} {v}: {d['skipped']}")
