import csv, json, sys
import geopandas as gpd
S="/Users/simondavis/.claude/jobs/26965cd4/tmp/maps"
GEO={"2011":"wards2011_JHB","2016":"wards2016_JHB","2021":"wards2020_JHB","2026":"wards2026_JHB"}
def short(w):
    w=str(w).strip().lstrip("0"); return w[-3:].lstrip("0") if len(w)>3 else w
def res(y): return {short(r["ward"]):r["winner"] for r in csv.DictReader(open(f"{S}/result_{y}_ward_winners.csv"))}
f26={short(r["ward"]):r["winner"] for r in csv.DictReader(open("data/processed/ward_winner_probs.csv"))}
def geo(y):
    g=gpd.read_file(f"data/raw/geo/{GEO[y]}.geojson").to_crs(epsg=32735)
    g["w"]=g["WardID"].astype(str).map(short); return g[["w","geometry"]]
def overlap_map(new,old):
    inter=gpd.overlay(geo(new),geo(old).rename(columns={"w":"wo"}),how="intersection",keep_geom_type=True)
    inter["a"]=inter.area
    return inter.sort_values("a").groupby("w").last()["wo"].to_dict()
pairs=[("2011","2016",res("2011"),res("2016"),"result"),("2016","2021",res("2016"),res("2021"),"result"),("2021","2026",res("2021"),f26,"forecast modal winner")]
for a,b,ra,rb,kind in pairs:
    same=[w for w in rb if w in ra]
    bynum=[(w,ra[w],rb[w]) for w in same if ra[w]!=rb[w]]
    om=overlap_map(b,a)
    byov=[(w,om[w],ra[om[w]],rb[w]) for w in rb if ra[om[w]]!=rb[w]]
    print(f"{a}->{b} ({kind}): wards={len(rb)} numbers in both={len(same)} new numbers={sorted(set(rb)-set(ra),key=int)}")
    print("  by ward number changed:",len(bynum), sorted(bynum,key=lambda t:int(t[0])))
    print("  by largest-overlap predecessor changed:",len(byov), sorted(byov,key=lambda t:int(t[0])))
    from collections import Counter
    print("  flows (number):",Counter((x[1],x[2]) for x in bynum))
