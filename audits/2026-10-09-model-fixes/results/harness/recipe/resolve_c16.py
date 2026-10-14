p = "src/montecarlo.py"
L = open(p).read().split("\n")
s = L.index("<<<<<<< ours"); m = L.index("=======", s); e = L.index(">>>>>>> theirs", m)
assert m + 1 == e, "theirs side not empty"
ours = L[s+1:m]
d = next(i for i, x in enumerate(ours) if x.startswith("def level_shock_sd("))
L = L[:s] + ours[:d] + L[e+1:]
open(p, "w").write("\n".join(L))
