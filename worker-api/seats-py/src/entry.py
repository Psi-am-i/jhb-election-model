"""joburg-seats: seats for a reader's forecast, from the project's own seat code.

The contract is defined by the caller, worker-api/src/seats.js. The request
body is the four arguments of ``reader_seats.reader_seats`` by name:

    POST /v1/seats  {"combined_shares": {code: fraction},
                     "ward_winners": {ward_id: code},
                     "context": {city, target, council, wards, parties,
                                 no_pr_list},
                     "total_votes": int}
    200             {"seats": {code: int}, "ward": {code: int}, "pr": {code: int},
                     "council_total": int, "majority": int,
                     "excessive": {code: int}, "code_ref": sha256}
    422             {"errors": [str]}   reader_seats refused the input

reader_seats.py and every project module it imports are copied here from the
repository's src/ by worker-api/tools/sync_seats_py.mjs, byte for byte;
code_ref.py is written by the same script. Nothing about the seat law is
written in this file: it passes the body through and reshapes the answer.
"""

import json

from workers import Response, WorkerEntrypoint

try:
    import reader_seats  # copied from ../../../src by tools/sync_seats_py.mjs
    from code_ref import CODE_REF
except ImportError:  # not copied yet: the stub answer
    reader_seats = None
    CODE_REF = None

ARGUMENTS = ("combined_shares", "ward_winners", "context", "total_votes")


def answer(body):
    """``(status, payload)`` for one parsed request body. No I/O."""
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


def _json(data, status=200):
    return Response(json.dumps(data), status=status,
                    headers={"content-type": "application/json"})


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method != "POST":
            return _json({"error": "POST only"}, 405)
        try:
            body = json.loads(await request.text())
        except ValueError:
            return _json({"error": "the body is not JSON"}, 400)
        status, payload = answer(body)
        return _json(payload, status)
