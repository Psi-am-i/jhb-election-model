p = "src/montecarlo.py"
L = open(p).read().split("\n")
hits = [i for i, x in enumerate(L) if x.strip() == "_h_rho, _win_rho = _levels.size_window(target, _levels.local_record)"]
assert len(hits) == 1, hits
i = hits[0]
ind = L[i][:len(L[i]) - len(L[i].lstrip())]
assert ind == " " * 8, repr(ind)
add = ['        # ARM C (step 9 prereg): item 16 off, no size filter on either route.',
       '        _h_theta = _h_rho = float("inf")',
       '        _win_theta = dict(_win_theta, h="inf", arm="C: forced inf")',
       '        _win_rho = dict(_win_rho, h="inf", arm="C: forced inf")']
L = L[:i+1] + add + L[i+1:]
open(p, "w").write("\n".join(L))
