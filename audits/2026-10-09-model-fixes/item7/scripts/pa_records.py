"""PA's theta and rho observation records and the shrink, at target 2026."""
import sys, os, json
os.chdir('/Users/simondavis/projects/atlas-jhb-election-model'); sys.path.insert(0, 'src')
import numpy as np, cityconfig, levels
city = cityconfig.use('joburg'); target = cityconfig.use_target(2026)
for name, fn in [('theta', levels.theta_record), ('rho', levels.local_record)]:
    rec = fn(target)
    pa = rec.get('PA', [])
    print(name, 'PA obs (ratio, base share):', [(round(r,3), round(s*100,3)) for r, s in pa])
    mus, mu_all, worth = levels._shrunk(rec)
    fit = levels.size_centre(rec)
    w = [levels._reliability(s) for _, s in pa]
    own = float(np.average([np.log(r) for r, _ in pa], weights=w))
    size = float(np.average([s for _, s in pa], weights=w))
    tgt = fit[0] + fit[1]*np.log(size)
    wt = worth['PA']/(worth['PA']+levels.SHRINK)
    print(f'  own exp(mean log)={np.exp(own):.3f} worth={worth["PA"]:.3f} SHRINK={levels.SHRINK} weight={wt:.3f} size_centre target={np.exp(tgt):.3f} -> shrunk mult={np.exp(mus["PA"]):.3f}')
