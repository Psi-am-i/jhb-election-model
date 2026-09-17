"""Inventory every raw input with a checksum and its provenance.

The sources this model depends on are not durable. The MDB has already retired
the per-municipality shapefile downloads its old site served, the IEC's
by-election reports are reachable only through session-bound tokens, and Stats SA
withdraws and reissues products. If a file we relied on disappears upstream, we
need to know exactly what we had, where it came from, and whether the copy on
disk is still the copy we validated against.

``data/`` is gitignored, so the manifest is the tracked record: it goes in git
even though the bytes do not. Together with ``SOURCES.md``, which records how
each file was obtained, it makes the raw layer reconstructible or at least
auditable.

    python src/archive.py            # build/refresh the manifest
    python src/archive.py --verify   # re-hash and report drift
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path

MANIFEST = Path("data/archive_manifest.csv")
COLUMNS = ["path", "bytes", "sha256", "modified_utc", "provenance"]

# Longest matching prefix wins, so specific paths override general ones.
PROVENANCE = {
    "data/raw/elections/_source/npe2014": "elections.org.za Downloadable-results, 2014 NPE complete VD-level (zipped CSV)",
    "data/raw/elections/_source/npe2019": "results.elections.org.za NPEPublicReports/827/Downloadable Results/Provincial.zip",
    "data/raw/elections/_source/npe2024": "results.elections.org.za NPEPublicReports/1335/Downloadable Results/Provincial.zip",
    "data/raw/elections/_source/lge2016_national": "elections.org.za Downloadable-results, 2016 LGE complete VD-level (zipped CSV)",
    "data/raw/elections/_source/lge2016_JHB_seats": "results.elections.org.za LGEPublicReports/402/Seat Calculation Detail/GP/JHB.pdf",
    "data/raw/elections/_source/lge2021_JHB_seats": "results.elections.org.za LGEPublicReports/1091/Seat Calculation Detail/GP/JHB.pdf",
    "data/raw/elections/_source/lge2021_JHB_detailed": "results.elections.org.za LGEPublicReports/1091/Detailed Results/GP/JHB.pdf",
    "data/raw/elections/_reports/": "results.elections.org.za LGEPublicReports/{402,1091,197}, via src/fetch_iec.py",
    "data/raw/elections/lge": "derived: src/ingest_lge.py",
    "data/raw/elections/npe": "derived: src/ingest_npe.py",
    # These two are raw downloads that predate fetch_iec.py, so they sit beside
    # the derived files and would otherwise inherit the wrong label.
    "data/raw/elections/lge2016_JHB_vd_party.csv": "results.elections.org.za LGEPublicReports/402/Downloadable Party Results/GP/JHB.csv",
    "data/raw/elections/lge2021_JHB_vd_party.csv": "results.elections.org.za LGEPublicReports/1091/Downloadable Party Results/GP/JHB.csv",
    "data/raw/geo/wards2011_SA": "arcgis.com item 12d2deb98816451ab7c4dc09cdfeee6b (MDB Wards 2011, File Geodatabase)",
    "data/raw/geo/wards2016_SA": "arcgis.com item cfddb54aab5f4d62b2144d80d49b3fdb (MDB Wards 2016, File Geodatabase)",
    "data/raw/geo/wards2011_JHB": "derived: src/build_geo.py, clipped from wards2011_SA",
    "data/raw/geo/wards2016_JHB": "derived: src/build_geo.py, clipped from wards2016_SA",
    "data/raw/geo/wards2020_JHB": "MDB FeatureServer SA_Wards2020 (2021 LGE delimitation), via src/fetch_boundaries.py",
    "data/raw/geo/wards2026_JHB": "MDB FeatureServer MDBWards2026, via src/fetch_boundaries.py",
    "data/raw/geo/vds2026_JHB": "MDB FeatureServer VotingDistricts2026_Final, via src/fetch_boundaries.py",
    "data/raw/geo/votingstations2026_JHB": "MDB FeatureServer VotingStations_March2026, via src/fetch_boundaries.py",
    # THE ALL-METRO SWEEP (2026-08-07, SOURCES.md "All-metro sweep").
    # Until 2026-08-23 only the Johannesburg entries above existed, so the
    # seven other metros' boundary extracts — 28 files — carried "UNRECORDED"
    # and `archive.py` exited 1 every time it was run. That is a large part of
    # why nobody ran it, and a manifest nobody runs is the tracked record of
    # `data/**` going stale: it was twelve days out of date when six raw inputs
    # went missing (MODEL-LOG §1.75). Longest-prefix wins, so the per-JHB rows
    # above still take precedence.
    "data/raw/geo/wards2026_": "MDB FeatureServer MDBWards2026, via src/fetch_boundaries.py --muni <CODE>",
    "data/raw/geo/vds2026_": "MDB FeatureServer VotingDistricts2026_Final, via src/fetch_boundaries.py --muni <CODE>",
    "data/raw/geo/votingstations2026_": "MDB FeatureServer VotingStations_March2026, via src/fetch_boundaries.py --muni <CODE>",
    "data/raw/geo/wards2020_": "MDB FeatureServer SA_Wards2020 (2021 LGE delimitation), via src/fetch_boundaries.py --muni <CODE>",
    "data/raw/geo/wards2011_": "derived: src/build_geo.py, clipped from wards2011_SA",
    "data/raw/geo/wards2016_": "derived: src/build_geo.py, clipped from wards2016_SA",
    # Per-metro LGE Downloadable Party Results at VD level. `pools.metro_file`
    # resolves these and `_reports/` and NOTHING ELSE, so they ARE in use.
    #
    # ⛔ THIS USED TO SAY THEIR HEADER "differs from the `_clean` files
    # (`PartyName`), which pools.py handles". **pools.py does not handle it.**
    # `ingest_lge.read_municipality` parses the IEC raw header only and raises
    # `KeyError: 'VOTINGDISTRICT'` on a `_clean` file (verified 2026-09-08).
    # The two formats have two readers, deliberately: `_clean` files reach the
    # model through `pools._npe_citywide_for` and `levels._citywide`. A reader
    # that looked like it handled both is why the 2000/2006 metro results sat
    # on disk and unread for weeks. §1.197.
    "data/raw/elections/_metros/": "results.elections.org.za LGEPublicReports Downloadable Party Results per metro, via src/fetch_iec.py (all-metro sweep)",
    # The pre-2011 national bulk export: one zipped national CSV per election,
    # at a path linked from no page of either IEC site and absent from the
    # downloads portal — SOURCES.md "The pre-2011 archive". Six files.
    "data/raw/elections/_source/": "elections.org.za/content/uploadedfiles/{YYYY}%20{NPE|LGE}.zip — unlinked national bulk export, archived 2026-08-09/10",
    "data/raw/byelections/": "results.elections.org.za by-election dashboard MapsJason, via src/fetch_byelections.py",
    "data/raw/covariates/Ward-Product": "statssa.gov.za Ward-level Small Area Population Estimates 2022",
    "data/raw/covariates/Ward Product_Locked spreadsheets/": "unpacked from statssa.gov.za Ward-Product_Locked-spreadsheets.zip",
    "data/raw/covariates/Ward-statistical": "statssa.gov.za ward product technical note",
    # Supplied by email, not published: Stats SA User Information Services
    # (Magakwe Jan Kgope) on 2026-08-24, answering the ward-language request.
    # It is a SuperCROSS extract at MUNICIPALITY level -- not the ward table
    # asked for -- so it is held as provenance, not as a model input. See
    # SOURCES.md "Census 2022 home language" and DATA-QUALITY.md.
    # The IEC's certified candidate list for Gauteng, LGE 2026, published on
    # nomination day. The source of `[roster]` in judgements/joburg-2026.toml.
    # SOURCES.md "Nomination lists — certified candidates, LGE 2026".
    "data/raw/nominations/lge2026_certified_candidates_GP.pdf": "elections.org.za LGE2026 Certified Candidate List - GP.pdf, published 2026-09-16",
    "data/raw/covariates/Languages by Municipalities": "Stats SA User Information Services, emailed 2026-08-24 (SuperCROSS extract, municipality level)",
    # ⛔ EVERY ROW UNDER data/processed CARRIED ONE BLANKET STRING, AND IT WAS
    # FALSE FOR NEARLY ALL OF THEM.
    #
    # It read "derived: src/build_concordance.py, src/build_crosswalk.py" for
    # all 130 processed rows — the fold parameters, the turnout tables, the
    # pool specs, the seat draws, the coalition tables. Two of those files
    # write four of the 130. The rest named a script that had never touched
    # them.
    #
    # That is the `measure_pool_ratios` class exactly (§1.210): a declaration
    # that reads as informative, is machine-checkable, and is wrong — which is
    # worse than the blank it replaced, because a blank invites a question and
    # a wrong answer closes it. And it mattered here specifically: 80 of the
    # 104 CSVs under data/processed are FITTED INTERMEDIATES that later runs
    # read back as INPUTS (`fold3_parameters.csv` supplies theta and gamma to
    # every 2016 target), and they carry no identity of their own — no date, no
    # code version, no input hash, no sidecar. This manifest is the only thing
    # standing between them and §1.75, where six raw inputs left `data/raw`
    # while the intermediates fitted from them stayed on disk and kept being
    # read.
    #
    # Longest-prefix wins, so the specific rows below take precedence and the
    # generic tail catches anything new — loudly, as "UNRECORDED", which is the
    # honest answer for a file nobody has classified yet.
    #
    # Each entry below was confirmed at its WRITE site, not by grep: a grep for
    # the filename returns every READER too, and taking the first hit is how
    # the wrong attribution would be written a second time.
    "data/processed/party_crosswalk.csv":
        "derived: src/build_crosswalk.py (--out default)",
    "data/processed/vd_concordance.csv":
        "derived: src/build_concordance.py",
    "data/processed/vd_ward_":
        "derived: src/build_concordance.py",
    "data/processed/seat_draws.csv":
        "MODEL OUTPUT: src/montecarlo.py — one row per draw. Reproducible only "
        "with the run's draws and seed, which this file does not carry",
    "data/processed/ward_winner_probs.csv":
        "MODEL OUTPUT: src/montecarlo.py",
    "data/processed/regime_":
        "MODEL OUTPUT: src/overhang_regimes.py, re-invoking montecarlo per "
        "overhang rule",
    "data/processed/coalition_":
        "derived: src/coalitions.write_outputs, from seat_draws.csv",
    "data/processed/byelection_":
        "derived: src/byelections.py, from data/raw/byelections/",
    "data/processed/ward_leverage.csv":
        "⛔ ORPHAN, DELETED 2026-09-10 (§1.222). Was written by src/leverage.py, "
        "RETIRED 2026-08-31 to archive/retired-scripts/ (§1.140). Nothing in "
        "src/ wrote or read it and it ran `f_other`, deleted from the model "
        "2026-08-19 (§1.52). The row is kept so a reappearing file is not "
        "mistaken for a live intermediate",
    # Per-city, per-target intermediates. These are the 80 that later runs read
    # back as INPUTS, and the reason this table is worth correcting at all.
    "data/processed/fold":
        "FITTED INTERMEDIATE: src/fold.py --fit-from N (theta and gamma per "
        "party). Read back as an input by every later run at that target",
    "data/processed/gamma_recent.csv":
        "FITTED INTERMEDIATE: src/gamma_recent.py",
    "data/processed/turnout.csv":
        "FITTED INTERMEDIATE: src/turnout.py (per voting district)",
    "data/processed/pools_":
        "derived: src/pools.py --emit. Unlike everything else here this one "
        "DOES declare itself, via artefact_key; see pools.stale_reason",
    # The tail. Anything not matched above is unclassified, and says so.
    "data/processed/": "UNRECORDED -- add a specific row to src/archive.py",
}

# ⛔ THE PREFIX TABLE CANNOT REACH THE FILES THAT MATTER MOST, AND MY FIRST
# CORRECTION OF IT DID NOT NOTICE.
#
# `provenance_for` matches on `path.startswith(key)`, but the 80 fitted
# intermediates live at `data/processed/<city>/fold3_parameters.csv` and
# `data/processed/<city>/<year>/turnout.csv` — the city segment sits between
# the prefix and the filename, so a `data/processed/fold` key matches none of
# them. Measured on the real tree: 80 of 104 CSVs still fell through to the
# UNRECORDED tail after the prefix rows were "fixed".
#
# Matched on the FILENAME as well, therefore, and consulted only when the
# prefix match lands on the generic tail — so `data/raw`'s longest-prefix
# behaviour is untouched.
BY_FILENAME = (
    ("fold", "_parameters.csv",
     "FITTED INTERMEDIATE: src/fold.py --fit-from N (theta and gamma per "
     "party, per ballot). READ BACK AS AN INPUT by every later run at this "
     "target — the class §1.75 lost"),
    ("turnout", ".csv",
     "FITTED INTERMEDIATE: src/turnout.py (per voting district). Read back as "
     "an input"),
    ("gamma_recent", ".csv", "FITTED INTERMEDIATE: src/gamma_recent.py"),
    ("vd_concordance", ".csv", "derived: src/build_concordance.py"),
    ("vd_ward_", ".csv", "derived: src/build_concordance.py"),
    ("pools_", ".json",
     "derived: src/pools.py --emit. Unlike everything else here this one DOES "
     "declare itself, via artefact_key; see pools.stale_reason"),
    ("seat_draws", ".csv", "MODEL OUTPUT: src/montecarlo.py"),
    ("regime_", ".csv", "MODEL OUTPUT: src/overhang_regimes.py"),
    ("coalition_", ".csv", "derived: src/coalitions.write_outputs"),
    ("byelection", ".csv", "derived: src/byelections.py"),
    ("ward_winner_probs", ".csv", "MODEL OUTPUT: src/montecarlo.py"),
    ("forecast_summary", ".json",
     "MODEL OUTPUT: src/montecarlo.py. Carries _generated and _draws but NO "
     "seed, git sha or env switches — see src/declares.py"),
    ("forecast_frozen", ".json",
     "MODEL OUTPUT: src/freeze.py. The one artefact here carrying a full run "
     "manifest, and the one CLAUDE.md bars from arbitrating anything"),
    ("history", ".json",
     "SCOREBOARD: src/compare_history.py. Carries a manifest since 2026-09-09; "
     "read it with compare_history.load_history, which refuses the older "
     "bare-list shape"),
    ("history", ".md", "SCOREBOARD, rendered: src/compare_history.render"),
    ("validation_", ".json",
     "src/build_validation.py. ⛔ Carries in_sample: True on every city — a "
     "contaminated artefact, and the one behind the `published` "
     "self-benchmark deleted in §1.216"),
    ("width_budget", ".json", "src/width_budget.py"),
    ("sweep", ".json", "src/sweep.py — obvious-fault sweep"),
    ("interactive_data", ".json", "src/export_interactive.py"),
    ("ward_paths", ".json", "derived: src/render_map.py"),
    ("ward_hex_layout", ".json", "derived: src/hex_cartogram.py"),
    ("ward_leverage", ".csv",
     "ORPHAN, DELETED 2026-09-10 (§1.222): src/leverage.py, RETIRED 2026-08-31 "
     "(§1.140). Nothing in src/ writes or reads it"),
)


def provenance_for(path: str) -> str:
    """Where did this file come from? Longest prefix, then filename.

    The filename pass exists because the prefix table structurally cannot see
    a per-city intermediate — see BY_FILENAME. It runs only when the prefix
    match is the generic `data/processed/` tail, so nothing under `data/raw`
    changes behaviour.
    """
    match = max(
        (key for key in PROVENANCE if path.startswith(key)), key=len, default=None
    )
    answer = (PROVENANCE[match] if match
              else "UNRECORDED -- add to src/archive.py")
    if match == "data/processed/" or not match:
        name = Path(path).name
        for prefix, suffix, prov in BY_FILENAME:
            if name.startswith(prefix) and name.endswith(suffix):
                return prov
    return answer


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            sha.update(chunk)
    return sha.hexdigest()


def scan(roots: list[Path]) -> list[dict[str, str]]:
    rows = []
    for root in roots:
        for path in sorted(root.rglob("*")):
            # ⛔ RUNTIME STATE IS NOT AN ARTEFACT. `.pools.lock` is the flock
            # `pools.artefact_lock` holds during an emit — its content is a pid
            # and a label, it changes on every run, and recording it would make
            # the manifest report "changed" for a file whose whole purpose is
            # to change. It was in the manifest, and it was the one row the
            # provenance table could not answer for, which is the tell.
            if not path.is_file() or path.name in {".gitkeep", ".DS_Store",
                                                   ".pools.lock"}:
                continue
            if path == MANIFEST:
                continue
            stat = path.stat()
            key = path.as_posix()
            rows.append(
                {
                    "path": key,
                    "bytes": str(stat.st_size),
                    "sha256": digest(path),
                    "modified_utc": datetime.fromtimestamp(
                        stat.st_mtime, timezone.utc
                    ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "provenance": provenance_for(key),
                }
            )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="check against the manifest")
    parser.add_argument(
        "--roots",
        nargs="*",
        type=Path,
        default=[Path("data/raw"), Path("data/processed")],
    )
    args = parser.parse_args(argv)

    current = scan(args.roots)

    if args.verify:
        if not MANIFEST.exists():
            print(f"no manifest at {MANIFEST} -- run without --verify first")
            return 1
        with MANIFEST.open(encoding="utf-8", newline="") as handle:
            recorded = {row["path"]: row for row in csv.DictReader(handle)}
        now = {row["path"]: row for row in current}

        missing = sorted(set(recorded) - set(now))
        added = sorted(set(now) - set(recorded))
        changed = [
            p for p in sorted(set(recorded) & set(now))
            if recorded[p]["sha256"] != now[p]["sha256"]
        ]
        for label, items in (("missing", missing), ("changed", changed), ("new", added)):
            for item in items:
                print(f"  {label:<8s} {item}")
        total = len(missing) + len(changed) + len(added)
        print(f"\n{len(now):,} files; {total} difference(s) from the manifest")
        return 1 if missing or changed else 0

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(current)

    total = sum(int(row["bytes"]) for row in current)
    unrecorded = [r["path"] for r in current if r["provenance"].startswith("UNRECORDED")]
    print(f"{len(current):,} files, {total / 1e6:,.1f} MB -> {MANIFEST}")
    for row in current:
        print(f"  {int(row['bytes']) / 1e6:>8.2f} MB  {row['path']}")
    if unrecorded:
        print(f"\n{len(unrecorded)} file(s) with no recorded provenance:")
        for path in unrecorded:
            print(f"  - {path}")
        return 1
    print("\nevery file has recorded provenance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
