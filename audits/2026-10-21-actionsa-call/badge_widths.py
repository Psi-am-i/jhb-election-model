"""The brief's badge test predictions on several published draw exports, with
each large party's seat spread (MODEL-LOG 1.332). Usage: badge_widths.py DIR REV...;
DIR/REV holds manifest.json, base.bin and forecast.json from git (site/draws,
site/your-forecast), e.g. `git show REV:site/draws/base.bin > DIR/REV/base.bin`."""
import json,sys,hashlib
from pathlib import Path
import numpy as np
R0=Path(__file__).resolve().parents[2]
import reweight as R
import test_reweight as T
fx=json.loads((R0/'interactive/tests/share-fixture.json').read_text())
out={}
for rev in sys.argv[2:]:
    d=Path(sys.argv[1])/rev
    man=json.loads((d/'manifest.json').read_bytes()); arr=R.unpack((d/'base.bin').read_bytes(),man)
    law=R.PUBLISHED_LAW
    cols=next(b for b in man['blocks'] if b['name']==f'seats/{law}')['columns']
    seats,parties=R.party_columns(arr[f'seats/{law}'],cols)
    xcols=list(next(b for b in man['blocks'] if b['name']=='list_vote')['columns'])
    x=R.draw_percents(arr['list_vote'])
    fc=json.loads((d/'forecast.json').read_text())
    ours={'seats':{c:int(v) for c,v in fc['start']['seats'].items()},'share':R.list_percent(fc['start']['list_votes'])}
    def moved(ch):
        s,v=dict(ours['seats']),dict(ours['share'])
        for c,dd in ch.items(): v[c]=v[c]*(s[c]+dd)/s[c]; s[c]+=dd
        return {'seats':s,'share':v}
    o=R.large_parties(ours['seats'])
    shot={'seats':{**ours['seats'],**{c:a for c,(a,_b) in T.SCREENSHOT.items()}},'share':{**ours['share'],**{c:b for c,(_a,b) in T.SCREENSHOT.items()}}}
    F={'ours':ours,'fixture A':{'seats':fx['A']['answer']['seats'],'share':R.list_percent(fx['A']['list_votes'])},
       'fixture B':{'seats':fx['B']['answer']['seats'],'share':R.list_percent(fx['B']['list_votes'])},'screenshot':shot,
       'mild':moved({o[0]:-8,o[1]:8}),'moderate':moved({o[0]:-15,o[1]:5,o[2]:5,o[3]:5,'IFP':2}),
       'wild':moved({o[0]:-25,o[3]:25,'ALJAMAAH':3,'IFP':3,'RISE':3})}
    med=R.middle_seats(seats,parties,R.uniform(seats.shape[0]))
    print(f'== {rev} model {man["artefact_key"]["model_sha256"][:8]}  large={o}')
    print('   ours seats vs median:', {c:(ours["seats"][c],med.get(c)) for c in o})
    sd={c:float(np.std(seats[:,parties.index(c)])) for c in o}
    print('   seat sd of large:', {c:round(v,1) for c,v in sd.items()})
    for n,m in F.items():
        r=R.closeness(seats,parties,x,xcols,None,m,ours)
        big={c:round(r['parties'][c],3) for c in o}
        print(f'   {n:11s} overall {r["overall"]:.3f} {R.closeness_badge(r["overall"]):20s} large {r["large"]:.3f} small {r["small"] if r["small"] is None else round(r["small"],3)} n_small {len(r["small_parties"])}  {big}')
