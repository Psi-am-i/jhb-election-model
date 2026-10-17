import sys, io, contextlib, argparse, json
sys.path.insert(0, 'src')
import numpy as np, cityconfig, montecarlo as M
c = cityconfig.use('joburg'); target = cityconfig.use_target('2026'); M.apply_city(c)
rec = {'hi':0,'lo':0,'n':0,'hi_w':0.0,'w':0.0,'city':[], 'city_ref':None}
orig_d = M.drawn_district_turnout
orig_r = M.reference_district_turnout
st = {}
def ref(centre, own, comp, pool_reference, reg):
    T, s = orig_r(centre, own, comp, pool_reference, reg)
    st['reg']=np.asarray(reg); st['comp']=np.asarray(comp)
    raw = M.district_pool_turnout(np.where(own, centre, s*(np.asarray(comp)@pool_reference)), comp, pool_reference)
    st['ref_clip_hi'] = float(((raw>M.TURNOUT_DRAW_CEILING)*st['comp']*st['reg'][:,None]).sum()/ (st['comp']*st['reg'][:,None]).sum())
    st['city_ref'] = float((st['reg'][:,None]*st['comp']*T).sum()/st['reg'].sum())
    return T, s
def drawn(level, comp, pool_reference, pool_drawn):
    ref_ = np.asarray(pool_reference); k = np.asarray(pool_drawn)/ref_
    raw = M.district_pool_turnout(level, comp, ref_, k)
    w = st['reg'][:,None]*np.asarray(comp)
    rec['hi_w'] += float((w*(raw>M.TURNOUT_DRAW_CEILING)).sum()); rec['w'] += float(w.sum())
    rec['lo'] += int((raw<M.TURNOUT_DRAW_FLOOR).sum()); rec['n'] += raw.size
    out = orig_d(level, comp, pool_reference, pool_drawn)
    rec['city'].append(float((w*out).sum()/st['reg'].sum()))
    rec.setdefault('lost',0.0); rec['lost'] += float((w*(raw-out)).sum()/st['reg'].sum())
    return out
M.drawn_district_turnout = drawn; M.reference_district_turnout = ref
sc = M.load_scenario(argparse.Namespace(config=None, set=[], draws=500, seed=20261104, city='joburg', target='2026'))
with contextlib.redirect_stdout(io.StringIO()):
    run = M.run_model(target, sc, verbose=False)
city = np.array(rec['city'])
print(json.dumps({'city_ref_turnout': st['city_ref'], 'ref_cells_over_ceiling_roll_share': st['ref_clip_hi'],
  'drawn_city_turnout_mean': city.mean(), 'sd': city.std(), 'p5': float(np.quantile(city,.05)), 'p95': float(np.quantile(city,.95)),
  'pool_roll_share_clipped_at_ceiling_per_draw': rec['hi_w']/rec['w'], 'cells_below_floor': rec['lo']/rec['n'],
  'mean_turnout_pts_removed_by_clip': 100*rec['lost']/len(city)}, indent=1))
