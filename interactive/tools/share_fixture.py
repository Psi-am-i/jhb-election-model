"""Two readers' forecasts for the share-card tests and screenshots.

    .venv/bin/python interactive/tools/share_fixture.py --write

Writes ``interactive/tests/share-fixture.json``. Every figure in it comes from
the project's own code: the forecasts are made by the share design's stated
rules (audits/2026-10-03-share-design/DESIGN.md §1) from the published start
(``build_make.forecast_data``); their seats from the seat law
(``reader_seats``, through the seat Worker's own ``entry.answer``); the chance
of each outcome and its badge from the published draws
(``reweight.outcome_chance``, through the seat Worker's own ``entry.card``,
with the published prediction from the served ``forecast.json``);
the previous election and polling day from ``build_make``; names, colours and
logo flags from ``build_play.roster``. The names are invented labels.

Each forecast is a prediction, entry version 2: ward calls and whole votes on
the ward ballot and on the list ballot. ``vote`` is its list-ballot percent,
the column a card prints and an entry is scored on.

* **A**: the start's ward calls, except each ward whose most likely winner has
  under 55% (``data/processed/ward_winner_probs.csv``) goes to its second most
  likely; the start's whole votes on both ballots; the coalition is parties in
  seat order until a majority.
* **B**: the same with a 70% cut; each ballot's votes halfway between the
  start's and the previous election's share of that ballot (at the start's
  ballot totals, rounded to whole votes); the coalition skips the second
  largest.
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
    wards = [str(w["id"]) for w in data["geometry"]["wards"]]
    start = data["start"]
    base = data["baseline"]
    probs = {}
    with open(REPO / "data/processed/ward_winner_probs.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            probs[str(r["ward"])] = [(p.split(":")[0], float(p.split(":")[1])) for p in r["dist"].split("|")]
    draws = entry.load_draws((REPO / "site/draws/manifest.json").read_bytes(), (REPO / "site/draws/base.bin").read_bytes())
    # the published prediction the boldest call is measured from, as the Worker loads it
    draws["prediction"] = entry.load_prediction((REPO / "site/your-forecast/forecast.json").read_bytes(), draws["sha256"])

    def calls_with(cut):
        return [probs[w][1][0] if probs[w][0][1] < cut and len(probs[w]) > 1 else c
                for w, c in zip(wards, start["ward_calls"])]

    def forecast(name, calls, ward_votes, list_votes, skip_second):
        ward_votes = {c: int(ward_votes.get(c, 0)) for c in ctx["parties"]}
        list_votes = {c: int(list_votes.get(c, 0)) for c in ctx["parties"]}
        tot = sum(list_votes.values())
        pct = {c: list_votes[c] * 100.0 / tot for c in ctx["parties"]}
        body = {"ward_votes": ward_votes, "list_votes": list_votes,
                "ward_winners": dict(zip(wards, calls)), "context": ctx}
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
                "ward_votes": ward_votes, "list_votes": list_votes,
                "coalition": coalition, "answer": ans}

    def halfway(votes, past):
        total = sum(votes.values())
        return {c: round(0.5 * votes.get(c, 0) + 0.5 * past.get(c, 0.0) / 100.0 * total)
                for c in ctx["parties"]}
    return {
        "_about": "Written by interactive/tools/share_fixture.py. Do not edit.",
        "election": data["election"], "baseline": base, "draws_sha256": data["draws_sha256"],
        "context_ref": data["context_ref"],
        "parties": build_play.roster(),
        "geometry": {"W": data["geometry"]["W"], "H": data["geometry"]["H"],
                     "wards": [{"path": w["path"]} for w in data["geometry"]["wards"]]},
        "A": forecast("Thandi", calls_with(0.55), start["ward_votes"], start["list_votes"], False),
        "B": forecast("@kgomotso_m", calls_with(0.70), halfway(start["ward_votes"], base["ward_vote"]),
                      halfway(start["list_votes"], base["list_vote"]), True),
    }


if __name__ == "__main__":
    out = build()
    text = json.dumps(out, indent=None, sort_keys=True, separators=(",", ":")) + "\n"
    if "--write" in sys.argv:
        OUT.write_text(text, encoding="utf-8")
        print(f"wrote {OUT.relative_to(REPO)}")
    for k in ("A", "B"):
        print(k, out[k]["name"], out[k]["coalition"], out[k]["answer"]["outcome"])
