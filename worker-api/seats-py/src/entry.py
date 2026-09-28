"""joburg-seats: seats for a reader's forecast, from the project's own seat code.

The contract is defined by the caller, worker-api/src/seats.js:

    POST /v1/seats  {"ward_calls": [code, ...], "pr_share": {code: percent},
                     "council_seats": int}
    200             {"seats": {code: int}, "ward": {code: int}, "pr": {code: int},
                     "council_total": int, "code_ref": sha256}

reader_seats.py and seats.py are copied here from the repository's src/ by
worker-api/tools/sync_seats_py.mjs, byte for byte; code_ref.py is written by the
same script. Nothing about the seat law is written in this file.

ASSUMED INTERFACE (to reconcile with the author of src/reader_seats.py):
    reader_seats.reader_seats(ward_calls: list[str], pr_share: dict[str, float],
                              council_seats: int) -> dict
returning at least "seats", "ward" and "pr" as {party: int}. Until that module
exists and the name is agreed, every request answers 501.
"""

import json

from workers import Response, WorkerEntrypoint

try:
    import reader_seats  # copied from ../../../src by tools/sync_seats_py.mjs
    from code_ref import CODE_REF
except ImportError:  # not copied yet: the stub answer
    reader_seats = None
    CODE_REF = None


def _json(data, status=200):
    return Response(json.dumps(data), status=status,
                    headers={"content-type": "application/json"})


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if reader_seats is None or not hasattr(reader_seats, "reader_seats"):
            return _json({"error": "reader_seats.py is not installed in this Worker"}, 501)
        if request.method != "POST":
            return _json({"error": "POST only"}, 405)
        body = json.loads(await request.text())
        out = reader_seats.reader_seats(body["ward_calls"], body["pr_share"], body["council_seats"])
        seats = {k: int(v) for k, v in out["seats"].items()}
        return _json({
            "seats": seats,
            "ward": {k: int(v) for k, v in out["ward"].items()},
            "pr": {k: int(v) for k, v in out["pr"].items()},
            "council_total": sum(seats.values()),
            "code_ref": CODE_REF,
        })
