"""Load the seat Worker's request handler outside a Worker.

The builder page (under Pyodide) and interactive/tests (under CPython) both run
this, with the served copy of the seat code (interactive/py/, written by
tools/sync_py.mjs) on ``sys.path``. They then call :func:`seat_answer`, which is
``entry.answer`` — the function the seat Worker runs on every save — so the
page shows exactly what the server will store.

``entry.py`` imports ``workers`` (Cloudflare's Python Worker runtime) for its
``fetch`` class only; ``answer`` never touches it. A stand-in module is
registered here, never edited into the copied file.
"""

import json
import sys
import types

if "workers" not in sys.modules:
    _workers = types.ModuleType("workers")
    _workers.Response = None
    _workers.WorkerEntrypoint = object
    sys.modules["workers"] = _workers

import entry  # noqa: E402  (the stand-in must exist first)

if entry.reader_seats is None or entry.CODE_REF is None:
    # entry.py swallows an ImportError into a 501; here that would hide a
    # broken copy behind a status code, so fail loudly instead.
    import reader_seats  # noqa: F401  re-raises the real import error
    raise ImportError("the seat code is on sys.path but entry.py did not load it")


def seat_answer(body_json: str) -> str:
    """``[status, payload]`` as JSON, for one request body given as JSON.

    Both directions are JSON text: a JavaScript number handed over as a
    Pyodide object arrives as a float, and ``reader_seats`` refuses a vote
    count that is not a whole number.
    """
    status, payload = entry.answer(json.loads(body_json))
    return json.dumps([status, payload])


CODE_REF = entry.CODE_REF
