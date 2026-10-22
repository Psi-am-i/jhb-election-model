"""Line coverage for CHILD processes of a test (subprocess, process pools).

Armed only when `MUTCOV_DIR` and `MUTCOV_SRC` are in the environment, which
`probe.py tests --cov-dir` sets for its children and never for itself. Writes
one JSON file per process at exit: the test id it was spawned under and the
`src/` lines it executed (import-time lines included: conservative).
"""
import os

if os.environ.get("MUTCOV_DIR") and os.environ.get("MUTCOV_SRC"):
    import atexit
    import json
    import sys

    _src = os.environ["MUTCOV_SRC"]
    _hits = set()

    def _line(code, line):
        f = code.co_filename
        if f.startswith(_src):
            _hits.add((f[len(_src):], line))
        return sys.monitoring.DISABLE

    try:
        sys.monitoring.use_tool_id(4, "mutnight-child")
        sys.monitoring.register_callback(4, sys.monitoring.events.LINE, _line)
        sys.monitoring.set_events(4, sys.monitoring.events.LINE)
    except Exception:  # noqa: BLE001
        pass

    def _dump():
        out = {}
        for f, ln in _hits:
            out.setdefault(f, []).append(ln)
        path = os.path.join(os.environ["MUTCOV_DIR"],
                            f"child-{os.getpid()}-{id(_hits)}.json")
        try:
            with open(path, "w") as fh:
                json.dump({"test": os.environ.get("MUTCOV_TEST"), "lines": out}, fh)
        except OSError:
            pass

    atexit.register(_dump)
