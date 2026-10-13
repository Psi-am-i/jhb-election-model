"""joburg-seats: seats for a reader's forecast, from the project's own seat code.

The contract is defined by the callers, worker-api/src/seats.js (saved
forecasts) and src/worker.js (the link preview of a shared one). The request
body of /v1/seats is the four arguments of ``reader_seats.reader_seats`` by
name, a reader's prediction (entry version 2):

    POST /v1/seats  {"ward_votes": {code: int},    whole votes, ward ballot
                     "list_votes": {code: int},    whole votes, list ballot
                     "ward_winners": {ward_id: code},
                     "context": {city, target, council, wards, parties,
                                 no_pr_list}}
    200             {"seats": {code: int}, "ward": {code: int}, "pr": {code: int},
                     "council_total": int, "majority": int,
                     "excessive": {code: int}, "code_ref": sha256}
    422             {"errors": [str]}   reader_seats refused the input

    POST /v1/card   {"seats": <the /v1/seats body>, "coalition": [code],
                     "draws_sha256": hex, "prediction_sha256": hex}
    200             the /v1/seats answer, plus
                    {"outcome": reweight.outcome_badge's answer: the
                                council in words, "badge" and "measure",
                     "draws_sha256": hex, "prediction_sha256": hex}
    409             {"error": ...}      the published draws or prediction this
                                        Worker holds are not the ones the
                                        caller's page was built from (a
                                        re-publish in between)
    422, 400, 501   as /v1/seats

``/v1/card`` is the link preview's answer (src/worker.js, audits/
2026-10-03-share-design/DESIGN.md §3): the seats the law gives the reader's
forecast, its council in words, and its badge: how close it is to the
published prediction, banded by the cut-offs the site's ``forecast.json``
carries (``reweight.outcome_badge``, the one definition the page's analysis
also calls; JUDGEMENT-CALLS §N10). The draws are the site's own
``/draws/manifest.json`` and ``/draws/base.bin``, and the prediction and
cut-offs its ``/your-forecast/forecast.json``, fetched from SITE_ORIGIN once
per isolate.

reader_seats.py and every project module it imports, and reweight.py, are
copied here from the repository's src/ by worker-api/tools/sync_seats_py.mjs,
byte for byte; code_ref.py is written by the same script. Nothing about the
seat law or the badge is written in this file: it passes the body through and
reshapes the answer.
"""

import hashlib
import json

from workers import Response, WorkerEntrypoint

try:
    import reader_seats  # copied from ../../../src by tools/sync_seats_py.mjs
    import reweight
    from code_ref import CODE_REF
except ImportError:  # not copied yet: the stub answer
    reader_seats = None
    reweight = None
    CODE_REF = None

ARGUMENTS = ("ward_votes", "list_votes", "ward_winners", "context")
CARD_ARGUMENTS = ("seats", "coalition", "draws_sha256", "prediction_sha256")


def answer(body):
    """``(status, payload)`` for one parsed /v1/seats body. No I/O."""
    if reader_seats is None or not hasattr(reader_seats, "reader_seats"):
        return 501, {"error": "reader_seats.py is not installed in this Worker"}
    if not isinstance(body, dict) or set(body) != set(ARGUMENTS):
        return 400, {"error": f"the body must carry exactly {list(ARGUMENTS)}"}
    out = reader_seats.reader_seats(*(body[k] for k in ARGUMENTS))
    if not out["ok"]:
        return 422, {"errors": [str(e) for e in out["errors"]]}
    seats = out["seats"]
    return 200, {
        "seats": {p: int(v["total"]) for p, v in seats.items()},
        "ward": {p: int(v["ward"]) for p, v in seats.items() if v["ward"]},
        "pr": {p: int(v["pr"]) for p, v in seats.items() if v["pr"]},
        "council_total": int(out["council"]),
        "majority": int(out["majority"]),
        "excessive": {p: int(v) for p, v in out["excessive"].items()},
        "code_ref": CODE_REF,
    }


def load_draws(manifest_bytes, blob):
    """The published draws as the card reads them: the party seat columns
    under ``reweight.PUBLISHED_LAW``, each simulation's list-ballot percents
    (``reweight.draw_percents``), and the sha256 of manifest + blob
    (``src/build_make.py``'s ``draws_sha256``). ``_draws`` adds the
    prediction and cut-offs (:func:`load_prediction`) to this."""
    manifest = json.loads(manifest_bytes)
    arrays = reweight.unpack(blob, manifest)
    law = reweight.PUBLISHED_LAW
    cols = next(b for b in manifest["blocks"] if b["name"] == f"seats/{law}")["columns"]
    seats, parties = reweight.party_columns(arrays[f"seats/{law}"], cols)
    share_cols = next(b for b in manifest["blocks"] if b["name"] == "list_vote")["columns"]
    return {"sha256": hashlib.sha256(bytes(manifest_bytes) + bytes(blob)).hexdigest(),
            "seats": seats, "columns": parties,
            "shares": reweight.draw_percents(arrays["list_vote"]), "share_columns": list(share_cols)}


def prediction_sha256(seats):
    """sha256 of a prediction's seats, one ``code=seats`` line per party in
    code order: the edge computes the same from forecast.json's
    ``start.seats`` (src/share-edge.js ``predictionSha``), so a card is drawn
    only from the prediction the page and the edge hold, and its image is
    cached under it."""
    h = hashlib.sha256()
    for c in sorted(seats):
        h.update(f"{c}={int(seats[c])}\n".encode())
    return h.hexdigest()


def load_prediction(forecast_bytes, draws_sha256):
    """The published prediction and the badge's cut-offs, from the site's
    ``forecast.json``, which must have been built from the draws hashed
    ``draws_sha256``: ``{"prediction": {party: seats}, "ours": {"seats",
    "share"} (reweight.closeness's form, list percents by
    reweight.list_percent), "cuts": closeness_cuts}``. A forecast.json
    without cut-offs is refused (the Worker then answers 503)."""
    data = json.loads(forecast_bytes)
    if data.get("draws_sha256") != draws_sha256:
        raise ValueError("forecast.json was built from other draws than the Worker holds")
    if not isinstance(data.get("closeness_cuts"), dict):
        raise ValueError("forecast.json carries no closeness_cuts")
    seats = {str(p): int(v) for p, v in data["start"]["seats"].items()}
    return {"prediction": seats,
            "ours": {"seats": seats, "share": reweight.list_percent(data["start"]["list_votes"])},
            "cuts": {str(k): float(v) for k, v in data["closeness_cuts"].items()}}


def card(body, draws):
    """``(status, payload)`` for one parsed /v1/card body against ``draws``
    (:func:`load_draws` with :func:`load_prediction`'s keys). No I/O."""
    if reweight is None:
        return 501, {"error": "reweight.py is not installed in this Worker"}
    if not isinstance(body, dict) or set(body) != set(CARD_ARGUMENTS) \
            or not isinstance(body["coalition"], list):
        return 400, {"error": f"the body must carry exactly {list(CARD_ARGUMENTS)}"}
    if body["draws_sha256"] != draws["sha256"]:
        return 409, {"error": "the published draws differ from the caller's"}
    if body["prediction_sha256"] != draws["prediction_sha256"]:
        return 409, {"error": "the published prediction differs from the caller's"}
    status, seats = answer(body["seats"])
    if status != 200:
        return status, seats
    mine = {"seats": seats["seats"], "share": reweight.list_percent(body["seats"]["list_votes"])}
    outcome = reweight.outcome_badge(draws["seats"], draws["columns"], draws["shares"], draws["share_columns"],
                                     None, mine, seats["majority"], body["coalition"],
                                     ours=draws["ours"], cuts=draws["cuts"])
    return 200, {**seats, "outcome": outcome, "draws_sha256": draws["sha256"],
                 "prediction_sha256": draws["prediction_sha256"]}


def _json(data, status=200):
    return Response(json.dumps(data), status=status,
                    headers={"content-type": "application/json"})


_DRAWS = None  # the published draws, once per isolate (not a request's data)


async def _draws(origin):
    global _DRAWS
    if _DRAWS is None:
        from js import fetch  # the Workers runtime's fetch, under Pyodide
        man = await fetch(origin + "/draws/manifest.json")
        blob = await fetch(origin + "/draws/base.bin")
        fc = await fetch(origin + "/your-forecast/forecast.json")
        if not (man.ok and blob.ok and fc.ok):
            raise RuntimeError("the published draws could not be fetched")
        drawn = load_draws((await man.arrayBuffer()).to_bytes(),
                           (await blob.arrayBuffer()).to_bytes())
        drawn.update(load_prediction((await fc.arrayBuffer()).to_bytes(), drawn["sha256"]))
        drawn["prediction_sha256"] = prediction_sha256(drawn["prediction"])
        _DRAWS = drawn
    return _DRAWS


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method != "POST":
            return _json({"error": "POST only"}, 405)
        try:
            body = json.loads(await request.text())
        except ValueError:
            return _json({"error": "the body is not JSON"}, 400)
        if str(request.url).endswith("/v1/card"):
            try:
                draws = await _draws(str(self.env.SITE_ORIGIN))
            except Exception:  # noqa: BLE001 - the caller falls back to the generic image
                return _json({"error": "the published draws are not available"}, 503)
            status, payload = card(body, draws)
        else:
            status, payload = answer(body)
        return _json(payload, status)
