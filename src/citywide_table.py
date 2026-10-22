"""The browser engine's stand-in for re-reading 65 election files.

    .venv/bin/python src/citywide_table.py --city joburg --target 2026          # build
    .venv/bin/python src/citywide_table.py --city joburg --target 2026 --check  # regenerate, compare

**What it is.** One Johannesburg 2026 run opens 75 data files, 147.7 MB, and 65
of them, 132.9 MB, are opened by one function: `levels._citywide_and_roster`,
which reduces each election file to its citywide PR shares and the set of
parties on its ballot. What it returns for all of them fits in about 90 KB. The
interactive runs the real model under Pyodide and cannot ship 133 MB, so it
ships this table instead and `install` swaps the function for a lookup into it.
MODEL-LOG §1.265 measured the swap: every drawn array identical on one seed, and
a 20-draw run 15 s → 3 s.

**The native model never uses this.** `run_model` on Atlas keeps parsing the
files, and every temporal spy in `tests/_support.py` keeps watching those
parses. `_citywide_and_roster` refuses a cache for exactly that reason — a memo
would let a file dated after the target be read without being seen — so the
table must never be installed on the native path. Only the browser installs it,
and for the browser the temporal guarantee becomes STATIC: `install` refuses any
target but the table's own, and refuses a table holding an election dated at or
after that target (blind review, `audits/2026-09-28-route-b/`, finding 1).

**One definition.** The table is never computed independently. `build` runs the
real `run_model` and RECORDS what the real function returned, keyed by the path
it was asked for. It is therefore an output of the function, and it stays one
only while it is regenerated: `--check` rebuilds it and compares bytes, and
`tests/test_citywide_table.py` does the same. The key names the code
(`levels.py` and `parties.py`, whose `canonical` decides every party code in
it) and the sha256 of every file reduced, so a stale table declares itself
stale rather than looking current.

**A miss is a refusal.** A path the table lacks means the page is running a
model the table was not built for. It raises `SystemExit`, as `levels._absent`
does. NOT `FileNotFoundError`: `run_model` catches that at two sites and falls
back to other constants — one of them hand-typed and fitted on the target —
so a missing entry would change the forecast and say only "unavailable"
(review finding 2).

**Environment gates.** `HELD_BACK_OFF`, `THETA_WINDOW`, `THETA_EXCLUDE_TARGETS`,
`FILTER_TYPE_A` and `EXCLUDE_DEMARCATION_CROSSING` change WHICH files are asked for, never what the function
returns for a given file (`HELD_BACK_OFF=1` asks for 80 paths instead of 66).
A table built under any of them is not the published model's, so `build`
refuses to run with one set, and `install` refuses to run with one set. A gate
that reaches the browser would then surface as a refusal, not a miss.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import cityconfig  # noqa: E402
import levels  # noqa: E402
import pools  # noqa: E402

#: The gates that move the set of files `_citywide_and_roster` is asked for.
#: Every `os.environ.get` in `levels.py` at the time of writing;
#: `tests/test_citywide_table.py` asserts this tuple still equals that set.
GATES = ("HELD_BACK_OFF", "THETA_WINDOW", "THETA_EXCLUDE_TARGETS",
         "FILTER_TYPE_A", "EXCLUDE_DEMARCATION_CROSSING")

SCHEMA = 1
_YEAR = re.compile(r"(?:lge|npe)(\d{4})")


class TableRefusal(SystemExit):
    """The table cannot stand in for the function here. Never caught by
    `run_model`, whose fallbacks catch `FileNotFoundError` and `KeyError`."""


def table_path(target) -> Path:
    return REPO / target.processed / f"citywide_{target.year}.json"


def _key(path) -> str:
    """The path as the model asked for it, repository-relative, POSIX.

    Not `relpath(abspath(...))`: that depends on the working directory, and
    Pyodide's is not the repository root (review finding 5).
    """
    p = Path(str(path))
    if p.is_absolute():
        p = p.relative_to(REPO)
    return p.as_posix()


def election_year(key: str) -> int:
    m = _YEAR.search(Path(key).name)
    if not m:
        raise TableRefusal(f"citywide table: cannot date {key!r}; an undatable "
                           f"entry cannot be shown to precede the target")
    return int(m.group(1))


def code_key() -> dict:
    return {"levels_sha": pools._code_sha(HERE / "levels.py"),
            "parties_sha": pools._code_sha(HERE / "parties.py")}


def _gates_set() -> list[str]:
    return [g for g in GATES if os.environ.get(g) not in (None, "")]


def build(city: str, target_year: str) -> dict:
    """Run the real model once and record every reduction it asked for."""
    if _gates_set():
        raise TableRefusal(f"citywide table: refusing to build with "
                           f"{_gates_set()} set; that is not the published model")
    import montecarlo as mc
    cityconfig.use(city)
    target = cityconfig.use_target(target_year)
    real = levels._citywide_and_roster
    seen: dict[str, tuple[dict, set]] = {}

    def recording(path):
        out = real(path)
        seen[_key(path)] = out
        return out

    class _Args:
        config = None; set = None; draws = 2; seed = None  # noqa: E702

    levels._citywide_and_roster = recording
    try:
        mc.run_model(target, mc.load_scenario(_Args()), verbose=False)
    finally:
        levels._citywide_and_roster = real
    entries = {}
    inputs = {}
    for k in sorted(seen):
        shares, roster = seen[k]
        entries[k] = {"shares": {p: shares[p] for p in sorted(shares)},
                      "roster": sorted(roster)}
        inputs[k] = hashlib.sha256((REPO / k).read_bytes()).hexdigest()
    return {"artefact_key": {"schema": SCHEMA, "city": city,
                             "target": int(target.year), **code_key(),
                             "inputs": inputs},
            "entries": entries}


def dumps(table: dict) -> str:
    return json.dumps(table, sort_keys=True, indent=1) + "\n"


def stale_reason(table: dict, target_year) -> str | None:
    """Why this table may not stand in for the function, or None."""
    key = table.get("artefact_key") or {}
    if key.get("schema") != SCHEMA:
        return f"schema {key.get('schema')!r}, expected {SCHEMA}"
    if int(key.get("target", -1)) != int(target_year):
        return (f"built for target {key.get('target')}, asked for "
                f"{target_year}; a table is locked to its own target")
    live = code_key()
    for f, v in live.items():
        if key.get(f) != v:
            return f"{f} {key.get(f)} but the live code is {v}; rebuild"
    late = sorted(k for k in table.get("entries", {})
                  if election_year(k) >= int(key["target"]))
    if late:
        return (f"holds {late[0]}, dated at or after target {key['target']}; "
                f"that is the election being forecast, or a later one")
    if set(table.get("entries", {})) != set(key.get("inputs", {})):
        return "entries and declared inputs name different files"
    return None


def install(table: dict, target_year) -> None:
    """Replace `levels._citywide_and_roster` with a lookup. BROWSER ONLY."""
    if _gates_set():
        raise TableRefusal(f"citywide table: {_gates_set()} set; the table was "
                           f"built without them")
    why = stale_reason(table, target_year)
    if why:
        raise TableRefusal(f"citywide table refused: {why}")
    entries = table["entries"]

    def lookup(path):
        k = _key(path)
        if k not in entries:
            raise TableRefusal(
                f"citywide table has no entry for {k}; the page is running a "
                f"model the table was not built for")
        e = entries[k]
        return dict(e["shares"]), set(e["roster"])

    levels._citywide_and_roster = lookup


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--city", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--check", action="store_true",
                    help="regenerate and compare with the file on disk; write nothing")
    a = ap.parse_args(argv)
    os.chdir(REPO)
    fresh = dumps(build(a.city, a.target))
    path = table_path(cityconfig.use_target(a.target))
    if a.check:
        if not path.exists():
            print(f"✗ {path.relative_to(REPO)} does not exist"); return 1
        if path.read_text() != fresh:
            print(f"✗ {path.relative_to(REPO)} differs from a fresh build"); return 1
        print(f"✓ {path.relative_to(REPO)} matches a fresh build"); return 0
    path.write_text(fresh)
    print(f"wrote {path.relative_to(REPO)} ({len(fresh) / 1e3:.1f} KB, "
          f"{len(json.loads(fresh)['entries'])} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
