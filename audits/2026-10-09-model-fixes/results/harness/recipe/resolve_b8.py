import sys
p = "src/levels.py"
L = open(p).read().split("\n")
s = L.index("<<<<<<< ours"); m = L.index("=======", s); e = L.index(">>>>>>> theirs", m)
ours = L[s+1:m]; theirs = L[m+1:e]
d = next(i for i, x in enumerate(theirs) if x.startswith("def local_record_only("))
L = L[:s] + ours + ["", ""] + theirs[d:] + L[e+1:]
open(p, "w").write("\n".join(L))
p = "src/montecarlo.py"
L = open(p).read().split("\n")
s = L.index("<<<<<<< ours"); m = L.index("=======", s); e = L.index(">>>>>>> theirs", m)
ours = L[s+1:m]
assert ours == ['        "bounds_checked": bounds_checked,'], ours
add = ['        "roster_unrepresented": roster_unrepresented,',
       '        "level_sd_default_parties": sorted(',
       '            p for p in draw_target.level_sd_default if p in index),']
L = L[:s] + ours + add + L[e+1:]
open(p, "w").write("\n".join(L))
