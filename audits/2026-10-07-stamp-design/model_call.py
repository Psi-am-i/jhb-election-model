"""Our call as a reader-card fixture: the start's ward calls and shares (mock-up only)."""
import json, sys
sys.path.insert(0, "interactive/tools"); sys.path.insert(0, "src")
import share_fixture as SF
import build_make, build_play
from pathlib import Path
entry = SF._entry()
data = build_make.forecast_data()
ctx = data["schema"]["x-seat-context"]; total = int(data["schema"]["x-total-votes"])
wards = [str(w["id"]) for w in data["geometry"]["wards"]]
start = data["start"]
tot = sum(start["combined_share"].values())
pct = {c: start["combined_share"].get(c, 0.0) * 100 / tot for c in ctx["parties"]}
body = {"combined_shares": {c: pct[c] / 100 for c in ctx["parties"]},
        "ward_winners": dict(zip(wards, start["ward_calls"])), "context": ctx, "total_votes": total}
st, ans = entry.answer(body); assert st == 200, ans
draws = entry.load_draws(Path("site/draws/manifest.json").read_bytes(), Path("site/draws/base.bin").read_bytes())
res = {}
for coal in ([], None):
    if coal is None: break
    st, card = entry.card({"seats": body, "coalition": coal, "draws_sha256": draws["sha256"]}, draws)
    res = card if st == 200 else {"err": card}
print(json.dumps(res.get("outcome", res))[:600])
print(sorted(ans["seats"].items(), key=lambda x: -x[1])[:10], ans.get("excessive"))
F = json.load(open("interactive/tests/share-fixture.json"))
F["M"] = {"name": "Our", "calls": start["ward_calls"], "vote": {c: v for c, v in pct.items() if v > 0}, "coalition": [],
          "answer": {k: v for k, v in (res if "seats" in res else ans).items() if k not in ("code_ref", "draws_sha256")}}
json.dump(F, open(sys.argv[1], "w"))
