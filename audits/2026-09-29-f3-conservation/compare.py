import json, glob, os, sys
sys.path.insert(0, '/Users/simondavis/projects/jhb-election-model/tests')
sys.path.insert(0, '/Users/simondavis/projects/jhb-election-model/src')
from test_pool_bounds import _p1_violations

def flat(x, pre=""):
    if isinstance(x, dict):
        for k, v in x.items(): yield from flat(v, f"{pre}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x): yield from flat(v, f"{pre}[{i}]")
    else:
        yield pre, x

for new in sorted(glob.glob('/tmp/f3/new/*.json')):
    name = os.path.basename(new)[:-5]
    o = json.load(open(f'/tmp/f3/old/{name}.json')); n = json.load(open(new))
    if not n['ok']:
        print(f"{name:24s} NEW FAILED: {n['error'][:200]}"); continue
    p1o = _p1_violations(o['spec']) if o['ok'] else ['old failed']
    p1n = _p1_violations(n['spec'])
    fo, fn = dict(flat(o['spec'])), dict(flat(n['spec']))
    keys = set(fo) | set(fn)
    diff = []
    for k in keys:
        a, b = fo.get(k, '<absent>'), fn.get(k, '<absent>')
        if a != b:
            if isinstance(a, float) and isinstance(b, float):
                diff.append((abs(a-b), k, a, b))
            else:
                diff.append((float('inf'), k, a, b))
    diff.sort(key=lambda t: -t[0])
    tops = sorted({d[1].split('/')[1].split('[')[0] for d in diff})
    print(f"{name:24s} P1old={len(p1o)} P1new={len(p1n)} ndiff={len(diff)} fields={tops}")
    for d in diff[:int(sys.argv[1]) if len(sys.argv)>1 else 0]:
        print("     ", d[1][:90], str(d[2])[:60], '->', str(d[3])[:60])
