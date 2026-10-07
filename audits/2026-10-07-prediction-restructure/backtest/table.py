import json, glob, sys
rs = [json.load(open(f)) for f in sorted(glob.glob(sys.argv[1] + "/*.json"))]
rs.sort(key=lambda r: (r["city"], r["year"]))
print(f"{'city-year':22} {'seats':>5} {'wds':>4} | {'A seat':>6} {'B seat':>6} {'coh':>5} {'med':>5} | {'A ok':>4} {'B ok':>4} | {'A wv':>5} {'B wv':>5} {'A lv':>5} {'B lv':>5} | top A/actual  excess")
T = dict(A=0, B=0, coh=0, med=0); p = dict(P1=0, P2=0, P3=0, P4l=0, P4w=0); exc = []
for r in rs:
    A, B = r["A"], r["B"]
    print(f"{r['city']+' '+r['year']:22} {r['council']:>5} {r['wards']:>4} | {A['seat_err']:>6.0f} {B['seat_err']:>6.0f} {r['coherent_seat_err']:>5.0f} {r['median_seat_err']:>5.0f} | {A['wards_ok']:>4} {B['wards_ok']:>4} | {A['ward_vote_err_pp']:>5.1f} {B['ward_vote_err_pp']:>5.1f} {A['list_vote_err_pp']:>5.1f} {B['list_vote_err_pp']:>5.1f} | {A['top']} {A['top_wards']}/{A['top_actual_wards']}  {A['excessive']}")
    T["A"] += A["seat_err"]; T["B"] += B["seat_err"]; T["coh"] += r["coherent_seat_err"]; T["med"] += r["median_seat_err"]
    p["P1"] += A["top_wards"] > A["top_actual_wards"]; p["P2"] += A["seat_err"] < B["seat_err"]; p["P3"] += A["wards_ok"] >= B["wards_ok"]
    p["P4l"] += A["list_vote_err_pp"] < B["list_vote_err_pp"]; p["P4w"] += A["ward_vote_err_pp"] < B["ward_vote_err_pp"]
    for q, e in A["excessive"].items():
        aw, asx = e["actual_wards"], e["actual_seats"]
        exc.append((r["city"], r["year"], q, e["wards"], aw, asx, asx == aw and aw > 0))
n = len(rs)
print("\nn =", n, "totals", T, "A/coh = %.3f" % (T["A"] / T["coh"]))
ties2 = sum(r["A"]["seat_err"] == r["B"]["seat_err"] for r in rs)
print("P1 A top over actual:", p["P1"], "| P2 A<B seats:", p["P2"], "(ties", ties2, ") | P3 A>=B wards:", p["P3"], "| P4 list:", p["P4l"], "ward:", p["P4w"])
print("A wards ok total", sum(r["A"]["wards_ok"] for r in rs), "B", sum(r["B"]["wards_ok"] for r in rs), "of", sum(r["wards"] for r in rs))
print("excessive in A (city,year,party,A wards,actual wards,actual seats, actual excessive?):"); [print(" ", e) for e in exc]
