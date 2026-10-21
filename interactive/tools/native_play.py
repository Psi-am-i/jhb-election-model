"""The native side of the page's identity harness (SPEC-v2 F19), and the closure probe.

    .venv/bin/python interactive/tools/native_play.py            print the cases
    .venv/bin/python interactive/tools/native_play.py --write     store them in
                                                                  tests/native-play.json
    .venv/bin/python interactive/tools/native_play.py --result NAME  one case's compute
                                                                  result, as JSON
    .venv/bin/python interactive/tools/native_play.py --measure   the src/ modules
                                                                  page.py imports and
                                                                  the files it opens

Runs ``interactive/pyboot/page.py`` exactly as the page's Web Worker does, but
under the project's CPython: the served copy ``interactive/py/page/`` (written
by ``tools/sync_py.mjs``) is the working directory and the only project
directory on ``sys.path``, the cells are read from ``site/draws/`` as the page
fetches them, and the settings are ``tests/play-settings.json``: its cases for
section 1's ``compute``, and its ``section2`` block for ``handoff`` and
``analyse``.
``tests/page.test.mjs`` runs the same cases under Pyodide and compares.

``--measure`` is how ``PAGE_FILES`` and ``PAGE_DATA`` are held to the truth:
it imports page.py from ``src/`` itself (not the copy, so a module missing from
the copy still shows) with an audit hook on ``open``, runs every case, and
reports what was imported from ``src/`` and what was opened under the
repository.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SERVED = REPO / "interactive" / "py" / "page"
DRAWS = REPO / "site" / "draws"
SETTINGS = REPO / "interactive" / "tests" / "play-settings.json"
FIXTURE = REPO / "interactive" / "tests" / "native-play.json"
BOOT = REPO / "interactive" / "pyboot" / "page.py"


def _page(code_dir: Path, cwd: Path):
    os.chdir(cwd)
    sys.path.insert(0, str(code_dir))
    sys.dont_write_bytecode = True
    ns = {"__name__": "page"}
    exec(compile(BOOT.read_text(), str(BOOT), "exec"), ns)
    return ns


def cells() -> list[dict]:
    return json.loads((DRAWS / "index.json").read_text())["cells"]


def run(ns) -> list[dict]:
    for c in cells():
        d = DRAWS / c["path"]
        ns["load_cell"](c["path"], (d / "manifest.json").read_text(),
                        (d / "base.bin").read_bytes())
    # As the page does: the poll set comes from index.json (build-time selection).
    ns["set_polls"](json.dumps(json.loads((DRAWS / "index.json").read_text()).get("polls", [])))
    ids = [p["id"] for p in ns["polls"]()]
    out = []
    for case in json.loads(SETTINGS.read_text())["cases"]:
        s = dict(case["settings"])
        if s["polls"] == "*":
            s["polls"] = ids
        out.append({"name": case["name"], "result": json.loads(ns["compute"](json.dumps(s)))})
    return out


def held_wards(ward_calls: dict) -> dict[str, int]:
    """Each party's count of called wards (the analysis input this harness uses)."""
    out: dict[str, int] = {}
    for party in ward_calls.values():
        out[party] = out.get(party, 0) + 1
    return out


def run_section2(ns) -> list[dict]:
    """Section 2's two calls on the settings ``play-settings.json`` names:
    the hand-off, then the analysis of the forecast it hands over."""
    doc = json.loads(SETTINGS.read_text())
    by_name = {c["name"]: c["settings"] for c in doc["cases"]}
    out = []
    for name in doc["section2"]["cases"]:
        h = json.loads(ns["handoff"](json.dumps({"settings": by_name[name]})))
        # The hand-off carries no seats (rule A: they are derived, by the seat
        # Worker on the page). The analysis needs a council-shaped input, and
        # this harness compares two runtimes on ONE input, so each party's
        # called wards stand in for its seats (page.test.mjs builds the same).
        seats = held_wards(h["ward_calls"])
        # the two parties with most seats as the governing coalition, so the
        # outcome's coalition part is exercised (page.test.mjs picks the same)
        two = sorted(seats, key=lambda c: (-seats[c], c))[:2]
        # the reader's list-ballot percent, as make.js sends it (B.percentOf "list")
        lt = sum(h["list_votes"].values())
        share = {c: 100.0 * v / lt for c, v in h["list_votes"].items()}
        ours = {"seats": seats, "list_votes": h["list_votes"]}
        a = json.loads(ns["analyse"](json.dumps({"ward_calls": h["ward_calls"], "share": share,
                                                 "seats": seats, "prediction": ours,
                                                 "coalition": two})))
        # the first reader IS the prediction (a Safe bet); the second is
        # measured from a prediction twelve seats away on the two largest
        # parties, a different input for the two runtimes to agree on
        assert a["outcome"]["badge"] == "Safe bet", name
        pred = {"seats": {**seats, two[0]: seats[two[0]] - 12, two[1]: seats[two[1]] + 12},
                "list_votes": h["list_votes"]}
        a2 = json.loads(ns["analyse"](json.dumps({"ward_calls": h["ward_calls"], "share": share,
                                                  "seats": seats, "prediction": pred,
                                                  "coalition": two})))
        out.append({"name": name, "handoff": h, "analyse": a, "analyse_moved": a2})
    return out


def describe(ns) -> dict:
    import numpy as np
    return {
        "_about": "Written by interactive/tools/native_play.py --write: the page's "
                  "Python run natively on the served draws. tests/page.test.mjs "
                  "compares Pyodide's output to it (F19). Regenerate after a "
                  "re-export or a change to the page code; the test says which.",
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "page_ref": json.loads((REPO / "interactive/py/manifest.json").read_text())["page"]["code_ref"],
        "draws": {c["path"]: c["code_sha256"] for c in cells()},
        "polls": ns["polls"](),
    }


def measure() -> dict:
    opened: set[str] = set()
    repo = str(REPO)

    def hook(event, args):
        if event == "open" and isinstance(args[0], (str, Path)):
            p = os.path.abspath(str(args[0]))
            # Project files only: the interpreter's own packages (numpy comes
            # from Pyodide in the browser) and bytecode caches are not page data.
            if (p.startswith(repo + os.sep) and "__pycache__" not in p
                    and not p.startswith(os.path.join(repo, ".venv") + os.sep)):
                opened.add(os.path.relpath(p, repo))

    src = REPO / "src"
    ns = _page(src, REPO)
    sys.addaudithook(hook)
    run(ns)
    mods = sorted(Path(m.__file__).name for m in list(sys.modules.values())
                  if getattr(m, "__file__", None)
                  and Path(m.__file__).resolve().parent == src)
    # the harness's own reads of the served draws and settings are not the page's
    own = {str(p.relative_to(REPO)) for p in (SETTINGS, *DRAWS.rglob("*"))}
    return {"modules": mods, "opened": sorted(opened - own)}


def result(name: str = "untouched") -> dict:
    """``compute`` for the settings of the case ``name``, as the page's Python
    gives it. The share image of /forecast is drawn from the "untouched" case:
    the published forecast (src/og_pages.py forecast_spec)."""
    ns = _page(SERVED, SERVED)
    for c in run(ns):
        if c["name"] == name:
            return c["result"]
    raise SystemExit(f"native_play: no case {name!r} in {SETTINGS.relative_to(REPO)}")


def main(argv: list[str]) -> int:
    if "--result" in argv:
        sys.stdout.write(json.dumps(result(argv[argv.index("--result") + 1])))
        return 0
    if "--measure" in argv:
        print(json.dumps(measure()))
        return 0
    ns = _page(SERVED, SERVED)
    cases = run(ns)          # first: it hands the page its poll set
    doc = {**describe(ns), "cases": cases, "section2": run_section2(ns)}
    text = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    if "--write" in argv:
        FIXTURE.write_text(text)
        print(f"wrote {FIXTURE.relative_to(REPO)}: {len(doc['cases'])} cases")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
