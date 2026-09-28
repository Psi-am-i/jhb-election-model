"""Build one pool spec IN-PROCESS and dump it to /tmp. Writes nothing under data/.

usage: build_spec.py <src_dir> <city> <target> <out.json>
"""
import sys, json, io, contextlib
src, slug, year, out = sys.argv[1:5]
sys.path.insert(0, src)
import cityconfig, pools
pools.write_lineage_template = lambda city, target, *a, **k: pools.lineage_path(city, target)
cfg = pools.load_config()
city = cityconfig.use(slug)
target = cityconfig.use_target(year)
buf = io.StringIO()
try:
    with contextlib.redirect_stdout(buf):
        spec = pools.emit_pools(city, target, cfg)
    spec.pop("artefact_key", None)
    json.dump({"ok": True, "spec": spec}, open(out, "w"), sort_keys=True, indent=1)
except BaseException as e:
    json.dump({"ok": False, "error": f"{type(e).__name__}: {e}"}, open(out, "w"))
