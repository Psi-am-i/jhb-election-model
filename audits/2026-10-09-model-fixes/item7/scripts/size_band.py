"""theta and rho ratios across the panel for parties whose base share is in the PA's current band."""
import sys, os
os.chdir('/Users/simondavis/projects/atlas-jhb-election-model'); sys.path.insert(0, 'src')
import numpy as np, cityconfig, levels
cityconfig.use('joburg'); t = cityconfig.use_target(2026)
for name, fn in [('theta', levels.theta_record), ('rho', levels.local_record)]:
    rec = fn(t)
    for lo, hi in [(0.005, 0.015), (0.015, 0.05), (0.05, 0.15)]:
        obs = [(p, r, s) for p, v in rec.items() for r, s in v if lo <= s < hi]
        lr = np.log([r for _, r, _ in obs])
        print(f"{name} base {lo:.1%}-{hi:.1%}: n {len(obs)} geomean {np.exp(lr.mean()):.3f} median {np.exp(np.median(lr)):.3f} p10 {np.exp(np.percentile(lr,10)):.3f} p90 {np.exp(np.percentile(lr,90)):.3f} max {np.exp(lr.max()):.3f}; share > 1.99: {(lr>np.log(1.995)).mean():.2f}; > 2.74: {(lr>np.log(2.741)).mean():.2f}")
    fit = levels.size_centre(rec)
    print(f"  size_centre at 2.9%: {np.exp(fit[0]+fit[1]*np.log(0.029)):.3f}")
