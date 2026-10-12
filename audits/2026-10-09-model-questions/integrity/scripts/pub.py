import json, numpy as np
def load():
    m=json.load(open('site/draws/manifest.json')); raw=open('site/draws/base.bin','rb').read()
    B={b['name']:b for b in m['blocks']}
    def blk(name):
        b=B[name]; a=np.frombuffer(raw[b['offset']:b['offset']+b['nbytes']], dtype=np.dtype(b['dtype'])); return a.reshape(-1, m['draws']).T, b.get('columns')
    return m, blk
