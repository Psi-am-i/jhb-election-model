import pickle, sys, json, numpy as np
sys.path.insert(0,"interactive/tools"); sys.path.insert(0,"src")
import share_fixture as SF, build_make
R="/Users/simondavis/.claude/jobs/26965cd4/tmp/review-A/"
d=pickle.load(open(R+"run5000.pkl","rb")); c=pickle.load(open(R+"run5000.comb.pkl","rb"))
print("comb type", type(c), (list(c)[:5] if isinstance(c,dict) else getattr(c,"shape",None)))
C=np.asarray(c["C"])/100.0; allp=list(c["allp"]); print("C", C.shape, "row sums", C.sum(1).min(), C.sum(1).max())
# independent check: these draws' seats equal the published seat_detail_draws
import csv
rows=list(csv.DictReader(open("data/processed/seat_detail_draws.csv")))
print("published draws", len(rows), "cols sample", list(rows[0])[:6])
sd=d["seat_draws"]; 
from collections import defaultdict
pub=defaultdict(dict)
for r in rows: pub[int(r["draw"])][r["party"]]=int(r["seats"])
draws=sorted(pub); print("draw ids", draws[0], draws[-1], len(draws))
cap=[{k:int(v) for k,v in s.items() if v} for s in sd]
same=sum(1 for i,dr in enumerate(draws) if {k:v for k,v in pub[dr].items() if v}==cap[i]); print("captured draws equal to published:", same, "of", len(draws))
mean={p:float(C[:,i].mean()) for i,p in enumerate(allp)}; med={p:float(np.median(C[:,i])) for i,p in enumerate(allp)}
print("sum mean", sum(mean.values()), "sum median", sum(med.values()))
for p in ["ANC","DA","ASA","EFF","PA","MK"]: print(p, "mean %.2f median %.2f"%(100*mean[p],100*med[p]))
entry=SF._entry(); data=build_make.forecast_data(); ctx=data["schema"]["x-seat-context"]; total=int(data["schema"]["x-total-votes"])
wards=[str(w["id"]) for w in data["geometry"]["wards"]]; calls=data["start"]["ward_calls"]
sh={p:mean.get(p,0.0) for p in ctx["parties"]}; s=sum(sh.values()); sh={p:v/s for p,v in sh.items()}
print("roster share coverage", s)
st,ans=entry.answer({"combined_shares":sh,"ward_winners":dict(zip(wards,calls)),"context":ctx,"total_votes":total})
print(st, sorted([(k,v) for k,v in ans["seats"].items() if v],key=lambda x:-x[1]), "council", ans.get("council_total"), "excess", {k:v for k,v in ans.get("excessive",{}).items() if v})
main=["ANC","DA","ASA","EFF","PA","MK"]; print("others", sum(v for k,v in ans["seats"].items() if k not in main))
for p in main:
    col=np.array([pub[dr].get(p,0) for dr in draws]); print(p, ans["seats"][p], "pct-ile %.0f"%(100*(col<ans["seats"][p]).mean()+50*(col==ans["seats"][p]).mean()))
