"""P3: levels.unopposed_wards at every runnable target and Johannesburg 2026,
in the tree this runs from (cwd). Prints JSON. Reads only."""
import json, sys
sys.path.insert(0, "src")
import cityconfig, compare_history as CH, levels
out = {}
for s in CH.CITIES:
    city = cityconfig.use(s)
    ok, _ = CH.runnable(city)
    for y in ok + (["2026"] if s == "joburg" else []):
        t = cityconfig.use_target(y)
        out[f"{s}-{y}"] = levels.unopposed_wards(t, city)
print(json.dumps(out))
