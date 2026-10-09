import sys, copy, csv, collections, numpy as np, pickle
sys.path.insert(0, 'src')
import cityconfig, montecarlo as mc
city = cityconfig.use('joburg'); target = cityconfig.use_target(2026); mc.apply_city(city)
cap=[]; W=[]; FR={}
orig=mc.solve_and_predict
def wrap(dev, base_city, tgt, gamma, weight, *a, **k):
    out=orig(dev, base_city, tgt, gamma, weight, *a, **k); cap.append(out.copy()); W.append(weight.copy())
    if not FR: f=sys._getframe(1).f_locals; FR.update(part_vd=f["part_vd"].copy(), part_ward=f["part_ward"].copy(), part_reg=f["part_reg"].copy())
    return out
mc.solve_and_predict=wrap
sc = copy.deepcopy(mc.DEFAULTS); sc['draws'] = 30; sc['seed'] = 20261104
run = mc.run_model(target, sc, verbose=False)
pickle.dump({"cap":cap,"W":W,"universe":run.universe,"FR":FR}, open(sys.argv[1],'wb'))
print(len(cap), cap[0].shape)
