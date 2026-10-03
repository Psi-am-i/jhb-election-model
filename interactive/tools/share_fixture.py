"""Two readers' forecasts for the share-card tests and screenshots.

    .venv/bin/python interactive/tools/share_fixture.py --write

Writes ``interactive/tests/share-fixture.json``. Every figure in it comes from
the project's own code: the forecasts are made by the share design's stated
rules (audits/2026-10-03-share-design/DESIGN.md §1) from the published start
(``build_make.forecast_data``); their seats from the seat law
(``reader_seats``, through the seat Worker's own ``entry.answer``); the chance
of each outcome and its badge from the published draws
(``reweight.outcome_chance``, through the seat Worker's own ``entry.card``);
the previous election and polling day from ``build_make``; names, colours and
logo flags from ``build_play.roster``. The names are invented labels.

* **A**: the start's ward calls, except each ward whose most likely winner has
  under 55% (``data/processed/ward_winner_probs.csv``) goes to its second most
  likely; the start's combined shares; the coalition is parties in seat order
  until a majority.
* **B**: the same with a 70% cut; shares halfway between the start's and the
  previous election's combined vote; the coalition skips the second largest.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import sys
import types
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
OUT = REPO / "interactive" / "tests" / "share-fixture.json"


def _entry():
    workers = types.ModuleType("workers")
    workers.Response = workers.WorkerEntrypoint = object
    sys.modules.setdefault("workers", workers)
    code_ref = types.ModuleType("code_ref")
    code_ref.CODE_REF = "0" * 64
    sys.modules.setdefault("code_ref", code_ref)
    spec = importlib.util.spec_from_file_location("seats_entry", REPO / "worker-api/seats-py/src/entry.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def build() -> dict:
    import build_make
    import build_play
    import cityconfig
    entry = _entry()
    data = build_make.forecast_data()
    ctx = data["schema"]["x-seat-context"]
    total = int(data["schema"]["x-total-votes"])
    wards = [str(w["id"]) for w in data["geometry"]["wards"]]
    start = data["start"]
    base = data["baseline"]
    probs = {}
    with open(REPO / "data/processed/ward_winner_probs.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            probs[str(r["ward"])] = [(p.split(":")[0], float(p.split(":")[1])) for p in r["dist"].split("|")]
    draws = entry.load_draws((REPO / "site/draws/manifest.json").read_bytes(), (REPO / "site/draws/base.bin").read_bytes())

    def calls_with(cut):
        return [probs[w][1][0] if probs[w][0][1] < cut and len(probs[w]) > 1 else c
                for w, c in zip(wards, start["ward_calls"])]

    def forecast(name, calls, share, skip_second):
        tot = sum(share.values())
        pct = {c: share.get(c, 0.0) * 100.0 / tot for c in ctx["parties"]}
        body = {"combined_shares": {c: pct[c] / 100.0 for c in ctx["parties"]},
                "ward_winners": dict(zip(wards, calls)), "context": ctx, "total_votes": total}
        status, ans = entry.answer(body)
        assert status == 200, ans
        seats = ans["seats"]
        order = sorted((c for c in seats if seats[c] > 0), key=lambda c: (-seats[c], c))
        skip = {order[1]} if skip_second else set()
        coalition = []
        for c in order:
            if c in skip:
                continue
            coalition.append(c)
            if sum(seats[x] for x in coalition) >= ans["majority"]:
                break
        status, card = entry.card({"seats": body, "coalition": coalition, "draws_sha256": draws["sha256"]}, draws)
        assert status == 200, card
        ans = {k: v for k, v in card.items() if k not in ("code_ref", "draws_sha256")}
        return {"name": name, "calls": calls, "vote": {c: v for c, v in pct.items() if v > 0},
                "coalition": coalition, "answer": ans}

    share_a = dict(start["combined_share"])
    share_b = {c: 0.5 * share_a.get(c, 0.0) + 0.5 * base["vote"].get(c, 0.0) for c in ctx["parties"]}
    return {
        "_about": "Written by interactive/tools/share_fixture.py. Do not edit.",
        "election": data["election"], "baseline": base, "draws_sha256": data["draws_sha256"],
        "context_ref": data["context_ref"],
        "parties": build_play.roster(),
        "geometry": {"W": data["geometry"]["W"], "H": data["geometry"]["H"],
                     "wards": [{"path": w["path"]} for w in data["geometry"]["wards"]]},
        "A": forecast("Thandi", calls_with(0.55), share_a, False),
        "B": forecast("@kgomotso_m", calls_with(0.70), share_b, True),
    }


if __name__ == "__main__":
    out = build()
    text = json.dumps(out, indent=None, sort_keys=True, separators=(",", ":")) + "\n"
    if "--write" in sys.argv:
        OUT.write_text(text, encoding="utf-8")
        print(f"wrote {OUT.relative_to(REPO)}")
    for k in ("A", "B"):
        print(k, out[k]["name"], out[k]["coalition"], out[k]["answer"]["outcome"])
