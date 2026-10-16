"""Are the inputs for a forecast of THIS election actually in hand, and current?

    .venv/bin/python src/inputs_preflight.py --city joburg --target 2026

⛔ **RUN THIS BEFORE A FORECAST FOR AN ELECTION THAT HAS NOT HAPPENED.** A
backtest resolves everything it needs from the target's own result file. A
forecast has no result file, so every input arrives from somewhere else, on its
own schedule, and the two ways it goes wrong are both silent:

* an input is **absent** and something falls back — `levels._citywide` returned
  `{}` for six missing election files and no test went red (MODEL-LOG §1.75);
* an input is **present but stale** — the roll the model divides by is whatever
  the last national election recorded, and it keeps working perfectly while the
  real electorate grows under it.

This module answers one question per input: *do we have the current one, and if
not, what is the exact step that gets it?* It decides nothing and repairs
nothing. `--strict` makes a missing REQUIRED input exit 1, which is what a
scheduled run should use.

⛔ **Present is not used (guard A).** Every REQUIRED row carries a `used` bool
that is COMPUTED from the artefact the model reads, never typed: the boundary
rows compare the geojson with the crosswalk built from it, the roll row asks
whether the crosswalk declares the newest snapshot, the baseline row whether
the election files the target's calendar names are among those found, the
roster row whether the file is the one `pools.lineage_path` reads and holds
parties. `_require_used` refuses a REQUIRED row with no bool `used`, and
`--strict` exits 1 for a REQUIRED input that is present and not used, in the
same way as for one that is missing. Without `--strict` an unused input prints
`present` and a note and the exit is 0.

⚠️ **The roll is the input this exists for.** Registration ships INSIDE an IEC
results file, so every past election brought its own — and the election being
forecast has no result file and therefore no roll, from 1999 to now. The IEC
publishes it separately, on a page that holds one snapshot and overwrites it
(`archive/iec-registration-<date>/`). Nothing else in this repository will
notice that it is missing.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: How old a live-and-overwritten snapshot may be before it is called stale.
#: Registration moves daily in the weeks before a poll; this is a judgement, not
#: a measurement, and it is here rather than in a docstring so it can be changed
#: in one place and seen by `--strict`.
SNAPSHOT_STALE_DAYS = 21

REQUIRED, ADVISORY = "required", "advisory"


def roll_snapshot(city: str) -> Path | None:
    """The newest registration snapshot's ward file for ``city``
    (``archive/iec-registration-<date>/<city>_*registration*.csv``), or None.
    One definition: this check and ``build_make.editor_bounds`` read the same
    file. Scoped to the city (the comment in :func:`_rows` says why)."""
    snaps = sorted(d for d in ROOT.glob("archive/iec-registration-*/")
                   if any(d.glob(f"{city}_*registration*.csv")))
    if not snaps:
        return None
    files = sorted(snaps[-1].glob(f"{city}_*registration*.csv"))
    if len(files) != 1:
        raise ValueError(f"{snaps[-1]}: {len(files)} registration files for {city}, not one")
    return files[0]


def read_roll_snapshot(path: Path) -> dict[str, int]:
    """``{ward id: registered}`` from a snapshot's ward file (columns ``Ward``,
    ``Registered``). The one reader of that layout; a repeated ward or a
    non-integer count refuses rather than being resolved by order."""
    out: dict[str, int] = {}
    with Path(path).open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ward = row["Ward"].strip()
            if ward in out:
                raise ValueError(f"{Path(path).name}: ward {ward} appears twice")
            out[ward] = int(row["Registered"])
    return out


def snapshot_label(snap: Path) -> str:
    """A snapshot's path as the crosswalk declares it: relative to the repo."""
    snap = Path(snap).resolve()
    return str(snap.relative_to(ROOT)) if snap.is_relative_to(ROOT) else snap.name


def declared_roll_snapshot(city: str, target: str, crosswalk: Path | None = None) -> str | None:
    """The snapshot the city's crosswalk says it was built from (its
    ``roll_snapshot`` column), or None when the crosswalk is absent or
    declares none. ``crosswalk`` names another copy (the tests')."""
    import cityconfig
    path = Path(crosswalk) if crosswalk is not None else \
        ROOT / cityconfig.Target(city=cityconfig.load(city), year=str(target)).crosswalk
    if not path.exists():
        return None
    with path.open(encoding="utf-8", newline="") as fh:
        first = next(csv.DictReader(fh), None)
    return (first or {}).get("roll_snapshot") or None


def _crosswalk_path(city: str, target: str) -> Path | None:
    """The crosswalk ``Target.crosswalk`` names for the city, or None when the
    city has no config or the file is absent."""
    import cityconfig
    if not (ROOT / "cities" / f"{city}.toml").exists():
        return None
    path = ROOT / cityconfig.Target(city=cityconfig.load(city), year=str(target)).crosswalk
    return path if path.exists() else None


def _crosswalk_column(city: str, target: str, column: str) -> set[str]:
    path = _crosswalk_path(city, target)
    if path is None:
        return set()
    with path.open(encoding="utf-8", newline="") as fh:
        return {str(r[column]).strip() for r in csv.DictReader(fh) if column in r}


def vds_used(city: str, target: str, geojson: Path) -> bool:
    """The crosswalk's voting districts are exactly the geojson's: the model
    reads the crosswalk, so the file is used only if the crosswalk was built
    from it."""
    if not geojson.exists():
        return False
    feats = json.loads(geojson.read_text())["features"]
    ids = {str(f["properties"]["VDNumber"]).strip() for f in feats}
    return bool(ids) and ids == _crosswalk_column(city, target, "VD_Number")


def wards_used(city: str, target: str, geojson: Path) -> bool:
    """Every ward the crosswalk assigns parts to is a ward of the geojson."""
    if not geojson.exists():
        return False
    feats = json.loads(geojson.read_text())["features"]
    ids = {str(f["properties"]["WardID"]).strip() for f in feats}
    used = _crosswalk_column(city, target, "WardID_2026" if str(target) == "2026"
                             else f"WardID_{target}")
    return bool(used) and used <= ids


def baseline_used(city: str, target: str, kind: str, with_roll: list[str]) -> bool:
    """The election file the target's calendar names for the preceding election
    of ``kind`` is among the files found carrying registration."""
    import cityconfig
    if not (ROOT / "cities" / f"{city}.toml").exists():
        return False
    year = cityconfig.preceding(str(target), kind)
    if year is None:
        return False
    name = cityconfig.CALENDAR[year].results
    return name is not None and name.replace("{CODE}", cityconfig.load(city).code) in with_roll


def roster_used(city: str, target: str, roster_n: int | None) -> bool:
    """The roster sits in the file ``pools.lineage_path`` reads, and holds
    parties."""
    import cityconfig
    import pools
    if not roster_n or not (ROOT / "cities" / f"{city}.toml").exists():
        return False
    c = cityconfig.load(city)
    return pools.lineage_path(c, cityconfig.Target(city=c, year=str(target))).exists()


def pr_used(city: str, target: str) -> bool:
    """The model's reader (`levels.ballots`) returns a PR list for the target,
    from the declaration rather than a result file."""
    import cityconfig
    import levels
    if not (ROOT / "cities" / f"{city}.toml").exists():
        return False
    c = cityconfig.load(city)
    b = levels.ballots(cityconfig.Target(city=c, year=str(target)), c)
    return b.source == "declared" and bool(b.pr)


def _require_used(rows: list[dict]) -> None:
    """Guard A: a REQUIRED row without a computed ``used`` bool is a defect in
    the check, not in the inputs."""
    for r in rows:
        if r["level"] == REQUIRED and not isinstance(r.get("used"), bool):
            raise ValueError(f"inputs_preflight: required row {r['input']!r} "
                             "carries no computed `used` bool")


def unusable(rows: list[dict]) -> list[str]:
    """REQUIRED inputs that are missing, stale, or present and not used."""
    return [r["input"] for r in rows if r["level"] == REQUIRED
            and (not r["ok"] or r["used"] is False)]


def _rows(city: str, target: str) -> list[dict]:
    """One row per input. `ok` False means the `fix` line has to be done."""
    out: list[dict] = []
    # The IEC municipality code, from the city's own config. This was a typed
    # map of three Gauteng cities with `city.upper()` as the fallback, so every
    # other metro looked for `vds2026_ETHEKWINI.geojson` and reported its
    # boundaries and both baselines MISSING while all of them were on disk.
    # A city with no config has no code, and so no input can match it: every
    # required row then reads MISSING, which is the truth about that city.
    import cityconfig
    code = (cityconfig.load(city).code
            if (ROOT / "cities" / f"{city}.toml").exists() else f"<no config for {city}>")

    # --- 1. boundaries: which VD is in which ward, for THIS delimitation ----
    vds = ROOT / "data" / "raw" / "geo" / f"vds{target}_{code}.geojson"
    wards = ROOT / "data" / "raw" / "geo" / f"wards{target}_{code}.geojson"
    for path, what in ((vds, "voting districts"), (wards, "wards")):
        out.append({
            "input": f"{target} {what}", "level": REQUIRED, "ok": path.exists(),
            "used": (vds_used if what == "voting districts" else wards_used)(city, target, path),
            "have": path.name if path.exists() else "—",
            "source": "MDB FeatureServer",
            "fix": f"python src/fetch_boundaries.py --muni {code}",
        })

    # --- 2. the delimitation trap, reported as a number --------------------
    if vds.exists():
        feats = json.loads(vds.read_text())["features"]
        uniq = {str(f["properties"]["VDNumber"]) for f in feats}
        split = len(feats) - len(uniq)
        out.append({
            "input": f"{target} split voting districts", "level": ADVISORY, "ok": True,
            "have": f"{len(feats)} VD-ward rows for {len(uniq)} VDs ({split} split)",
            "source": "the boundary file itself",
            "fix": "join through montecarlo.ward_parts, never on WardID directly — "
                   "a naive join gives one ward the whole roll of every split VD",
        })

    # --- 3. the roll for the target, which no result file will bring -------
    # ⛔ SCOPED TO THE CITY, and it was not at first: the check globbed
    # `archive/iec-registration-*` and a Johannesburg snapshot satisfied a
    # Tshwane preflight. A check that passes for a city it has no data for is
    # the failure it was written to catch, one layer up.
    try:
        snap = roll_snapshot(city)
    except ValueError as exc:
        print(f"inputs_preflight: {exc}")
        snap = None
    newest, age = (snap.parent if snap else None), None
    if newest:
        m = re.search(r"(\d{4}-\d{2}-\d{2})", newest.name)
        if m:
            age = (_dt.date.today() - _dt.date.fromisoformat(m.group(1))).days
    out.append({
        "input": f"{target} voters' roll (registration)", "level": REQUIRED,
        # "used" is a measurement: the crosswalk the model reads declares the
        # newest snapshot as the one it was built from. A snapshot in hand
        # that the crosswalk does not name is present, not used.
        "used": bool(snap) and declared_roll_snapshot(city, target) == snapshot_label(snap),
        "ok": newest is not None and (age is not None and age <= SNAPSHOT_STALE_DAYS),
        "have": (f"{newest.name}, {age} days old" if newest and age is not None
                 else (newest.name if newest else "—")),
        "source": "elections.org.za/pw/StatsData/Voter-Registration-Statistics",
        "fix": f"province -> municipality in a BROWSER (the selector will not "
               "drive over plain HTTP), page the ward table, commit it as "
               f"archive/iec-registration-<date>/{city}_ward_registration_<date>.csv "
               "— that page keeps no archive",
    })

    # --- 4. the baselines the model reads instead ---------------------------
    elections = ROOT / "data" / "raw" / "elections"
    for pattern, what in ((f"npe*_{code}_vd_party.csv", "national baseline"),
                          (f"lge*_{code}_vd_party*.csv", "local baseline")):
        found = sorted(elections.glob(pattern))
        with_roll = []
        for f in found:
            try:
                head = next(csv.reader(f.open(encoding="utf-8-sig")), [])
            except OSError:
                continue
            if "Registered_Population" in head:
                with_roll.append(f.name)
        out.append({
            "input": what, "level": REQUIRED, "ok": bool(with_roll),
            "used": baseline_used(city, target, "NPE" if what.startswith("national") else "LGE", with_roll),
            "have": f"{len(with_roll)} file(s) carrying registration"
                    + (f", newest {with_roll[-1]}" if with_roll else ""),
            "source": "IEC downloadable party results, per VD",
            "fix": "python src/fetch_iec.py",
        })

    # --- 5. who is on the ballot -------------------------------------------
    judgement = ROOT / "judgements" / f"{city}-{target}.toml"
    roster_n, complete = None, None
    if judgement.exists():
        # PARSED, not regexed. A regex over the file counted the first
        # `parties = [...]` it met and reported 5 for a roster of 82 — a
        # wrong number on a check whose whole job is to report numbers.
        doc = tomllib.loads(judgement.read_text(encoding="utf-8"))
        roster = doc.get("roster") or {}
        complete = bool(roster.get("complete"))
        parties = roster.get("parties")
        if parties is not None:
            roster_n = len(parties)
    out.append({
        "input": f"{target} certified party roster", "level": REQUIRED,
        "ok": judgement.exists() and roster_n is not None,
        "used": roster_used(city, target, roster_n),
        "have": (f"{roster_n} parties, complete={complete}" if roster_n is not None else "—"),
        "source": "IEC certified candidate lists",
        "fix": "type the certified list into judgements/<city>-<target>.toml. "
               "⛔ complete=true LICENSES DELETING every party it omits, so it "
               "needs the IEC's own list, not a newspaper's count of it",
    })

    # --- 6. who filed a PR list --------------------------------------------
    # Owner rule 2026-10-15: a party with a ward slate and no PR list is
    # ward-only, out of every citywide vote (`levels.ballots`). Without
    # `[roster] pr` nobody is ward-only and each such party takes a list share
    # it cannot receive. The count comes from the parsed file; `used` from the
    # reader the model calls.
    pr_n = None
    if judgement.exists():
        pr = (doc.get("roster") or {}).get("pr")
        pr_n = None if pr is None else len(pr)
    out.append({
        "input": f"{target} certified PR lists", "level": REQUIRED,
        "ok": pr_n is not None and pr_n > 0,
        "used": pr_used(city, target),
        "have": f"{pr_n} parties with a PR list" if pr_n is not None else "—",
        "source": "IEC certified candidate lists (PR rows: `Ward \\ List "
                  "Order` a small integer; SOURCES.md)",
        "fix": "add `pr = [...]` under [roster] in judgements/<city>-<target>.toml, "
               "the parties with PR-list rows in the certified candidate PDF, "
               "spelt as in `parties`",
    })
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--city", default="joburg")
    ap.add_argument("--target", default="2026")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if a REQUIRED input is missing, stale or present and not used")
    args = ap.parse_args(argv)

    rows = _rows(args.city, args.target)
    _require_used(rows)
    print(f"inputs for a {args.city} {args.target} forecast\n")
    bad = unusable(rows)
    for r in rows:
        unused = r["ok"] and r.get("used", True) is False
        mark = ("present" if unused else "ok  ") if r["ok"] else (
            "MISSING" if r["level"] == REQUIRED else "note")
        print(f"  [{mark:>7s}] {r['input']}")
        if unused:
            print("            the model does not read this input")
        print(f"            have: {r['have']}")
        print(f"            from: {r['source']}")
        if not r["ok"] or r["level"] == ADVISORY:
            print(f"            do:   {r['fix']}")
    print()
    if bad:
        print(f"{len(bad)} required input(s) missing, stale or not used: " + ", ".join(bad))
        print("A forecast run will NOT fail because of these. That is the point "
              "of this check: each of them has a silent fallback.")
    else:
        print("every required input is in hand, used, and within "
              f"{SNAPSHOT_STALE_DAYS} days.")
    return 1 if (bad and args.strict) else 0


if __name__ == "__main__":
    raise SystemExit(main())
