"""E1-E4: every arm's emitted specs against arm A's saved pre-batch specs.

    .venv/bin/python spec_diff.py <arms root> <out.json>

<arms root>/<arm>/data/processed holds each arm tree's specs. Reads only.
For each arm and spec: byte equality with A's copy, and the list of JSON
paths that differ (recursive; lists compared element-wise when lengths agree).
seed_notes is reported per note: count changed, and whether each change is
the item-9 band deletion (A11): the old note carries a "Band ...%" sentence
and the new note is the old with that sentence replaced by "The draw's width
comes from the pool split." or removed.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

root, out = Path(sys.argv[1]), Path(sys.argv[2])
ARMS = ["B0", "B6", "B8", "B", "C", "C16", "E"]


def specs(arm):
    base = root / arm / "data" / "processed"
    return {str(p.relative_to(base)): p for p in sorted(base.rglob("pools_*.json"))}


def diff(a, b, path=""):
    if type(a) is not type(b):
        return [path or "/"]
    if isinstance(a, dict):
        outp = []
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                outp.append(f"{path}/{k}")
            else:
                outp += diff(a[k], b[k], f"{path}/{k}")
        return outp
    if isinstance(a, list):
        if len(a) != len(b):
            return [path]
        outp = []
        for i, (x, y) in enumerate(zip(a, b)):
            outp += diff(x, y, f"{path}[{i}]")
        return outp
    return [] if a == b else [path]


BAND = re.compile(r"Band \d.*?\.(?=\s+[A-Z|(]|\s*$)")
NEW = "The draw's width comes from the pool split."


def band_deletion(old: str, new: str) -> bool:
    """True if `new` is `old` with one band sentence replaced by NEW or removed."""
    norm = lambda t: re.sub(r"\s+", " ", t).strip()
    for m in BAND.finditer(old):
        for repl in (NEW, ""):
            if norm(old[:m.start()] + repl + old[m.end():]) == norm(new):
                return True
    return False


A = specs("A")
report = {"A_count": len(A), "arms": {}}
for arm in ARMS:
    S = specs(arm)
    rows = {}
    for name in sorted(set(A) | set(S)):
        if name not in A or name not in S:
            rows[name] = {"present": "A only" if name in A else f"{arm} only"}
            continue
        ba, bs = A[name].read_bytes(), S[name].read_bytes()
        ja, js = json.loads(ba), json.loads(bs)
        paths = diff(ja, js)
        top = sorted({p.split("/")[1].split("[")[0] for p in paths})
        row = {"bytes_equal": ba == bs,
               "sha_A": hashlib.sha256(ba).hexdigest()[:16],
               "sha_arm": hashlib.sha256(bs).hexdigest()[:16],
               "top_fields_differing": top,
               "artefact_key_fields": sorted(p for p in paths if p.startswith("/artefact_key")),
               "n_paths": len(paths)}
        na, ns = ja.get("seed_notes") or {}, js.get("seed_notes") or {}
        if na != ns:
            changed = [k for k in sorted(set(na) | set(ns)) if na.get(k) != ns.get(k)]
            kinds = {"band_deletion": 0, "other": []}
            for k in changed:
                o, n = na.get(k), ns.get(k)
                if isinstance(o, str) and isinstance(n, str) and band_deletion(o, n):
                    kinds["band_deletion"] += 1
                else:
                    kinds["other"].append({"party": k, "A": o, arm: n})
            row["seed_notes_changed"] = len(changed)
            row["seed_notes_kinds"] = kinds
        row["n_seeds"] = len(js.get("seeds") or {})
        rows[name] = row
    report["arms"][arm] = rows
# C against C16, byte for byte
c, c16 = specs("C"), specs("C16")
report["C_vs_C16_bytes_equal"] = {n: c[n].read_bytes() == c16[n].read_bytes()
                                  for n in sorted(set(c) | set(c16))
                                  if n in c and n in c16}
# group_share_record.json `cities` content in B, C, C16, E
gs = {}
for arm in ("B", "C", "C16", "E"):
    p = root / arm / "data" / "processed" / "group_share_record.json"
    gs[arm] = (hashlib.sha256(json.dumps(json.loads(p.read_text())["cities"],
                                         sort_keys=True).encode()).hexdigest()[:16]
               if p.exists() else None)
report["group_share_cities_sha"] = gs
out.write_text(json.dumps(report, indent=1))
print("written", out)
