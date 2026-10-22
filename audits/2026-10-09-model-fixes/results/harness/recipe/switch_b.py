p = "src/levels.py"
s = open(p).read()
L = s.split("\n")
def sub(func, old, new):
    start = next(i for i, x in enumerate(L) if x.startswith(f"def {func}("))
    end = next(i for i in range(start + 1, len(L)) if L[i].startswith("def "))
    hits = [i for i in range(start, end) if L[i].strip() == old]
    assert len(hits) == 1, (func, hits)
    i = hits[0]
    ind = L[i][:len(L[i]) - len(L[i].lstrip())]
    L[i] = ind + new
sub("theta_prior", "if size > 0.0:", "if False:  # ARM B (step 9 prereg): item 11a off")
sub("_shrunk", 'size = float(current.get(party, 0.0) or 0.0)', "size = 0.0  # ARM B (step 9 prereg): item 11a off, observed size")
open(p, "w").write("\n".join(L))
