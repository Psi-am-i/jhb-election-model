"""CLASS 17 — EVERY DATA FILE IS INGESTED, RECORDED, AND REACHED BY SOMETHING.

**This file exists because the repository lost six verified inputs and scored
384 against a tree that produced 368, with every guard green** (MODEL-LOG
§1.75). Mangaung's and Buffalo City's pre-2011 archives were ingested, verified
at 100% reconciliation, used to fit γ fold 3 and used to measure a published
headline — and were gone from `data/raw/elections` a few hours later. Nothing
noticed, for four separate reasons, and each one is a direction this file now
checks:

* `levels._citywide` swallowed the absence and returned `{}`, which the θ and ρ
  records cannot tell apart from a metro that contested nothing.
  → `test_every_election_the_record_expects_is_present_or_declared_absent`
* the archive is not hashed by `artefact_key`, which covers `dimensions.toml`
  and `pools.py`, so every pool spec reported itself current — correctly, and
  uselessly.  → `test_the_manifest_still_finds_every_raw_input_it_recorded`
* `data/**` is gitignored, so no diff could ever show a raw input appear or
  vanish. The tracked record is `data/archive_manifest.csv`, and **it was
  twelve days stale and wired to nothing.**
  → `test_every_raw_input_on_disk_is_in_the_manifest`
* nothing asked the inverse question — whether a file we HOLD is actually used.
  → `test_no_election_file_on_disk_is_unreachable`,
    `test_every_archive_the_ingest_can_key_is_ingested_or_declared`

**Cheap by construction.** Existence and size are checked on every run; SHA-256
is not, because re-hashing ~380MB on every suite run buys little over size —
the one raw change this repository has seen (two `lge2011` files on 11 August)
moved the size by 19%. Set `ARCHIVE_VERIFY_HASHES=1` to force the full check.
"""

from __future__ import annotations

import csv
import hashlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, skip  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))

import archive  # noqa: E402
import cityconfig as CC  # noqa: E402
import ingest_historic as IH  # noqa: E402
import levels as L  # noqa: E402

ELECTIONS = ROOT / "data" / "raw" / "elections"
RAW = ROOT / "data" / "raw"
MANIFEST = ROOT / "data" / "archive_manifest.csv"

# FILES THAT ARE DELIBERATELY NOT REACHED BY A CALENDAR TEMPLATE.
# ---------------------------------------------------------------------------
# The originals as downloaded, kept for provenance; the model reads the parsed
# `_clean` files beside them, which carry different column names
# (`VotingDistrict` -> `VD_Number`). Both are registered in
# `archive.PROVENANCE`, so this register only names what that cannot: that
# being unreachable is intended rather than a typo in a filename.
UNREACHED_BY_DESIGN = {
    "lge2016_JHB_vd_party.csv":
        "the original IEC download for Johannesburg 2016 — "
        "`LGEPublicReports/402/Downloadable Party Results/GP/JHB.csv`. The "
        "model reads `lge2016_JHB_vd_party_clean.csv`, which is this file "
        "parsed. Kept because `data/**` is gitignored and this is the only "
        "copy of what was actually fetched.",
    "lge2021_JHB_vd_party.csv":
        "the original IEC download for Johannesburg 2021 — "
        "`LGEPublicReports/1091/Downloadable Party Results/GP/JHB.csv`. Same "
        "reason as its 2016 sibling.",
}


def _manifest_rows() -> list[dict[str, str]]:
    if not MANIFEST.exists():
        skip("no data/archive_manifest.csv — build it with "
             "`.venv/bin/python src/archive.py`")
    with MANIFEST.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _raw_rows() -> list[dict[str, str]]:
    """Manifest rows under `data/raw` only.

    `data/processed` is in the manifest too and is EXCLUDED here on purpose:
    those files are outputs and change on every run, so asserting over them
    would make this test fail constantly and be switched off — which is
    precisely how the manifest came to be twelve days stale and unwired.
    Raw inputs are immutable; that is what makes them assertable.
    """
    return [r for r in _manifest_rows() if r["path"].startswith("data/raw/")]


def _files_on_disk() -> set[str]:
    return {p.relative_to(ROOT).as_posix() for p in RAW.rglob("*")
            if p.is_file() and p.name not in {".gitkeep", ".DS_Store"}}


def test_the_manifest_still_finds_every_raw_input_it_recorded():
    """THE §1.75 GUARD. A recorded input that has vanished stops the suite.

    This is the check that would have caught the six deleted files the moment
    anyone ran the suite — provided the manifest had been refreshed after they
    were ingested, which is why the companion test below requires exactly that.
    """
    rows = _raw_rows()
    assert rows, "the manifest records nothing under data/raw"
    gone, resized = [], []
    for row in rows:
        path = ROOT / row["path"]
        if not path.exists():
            gone.append(row["path"])
            continue
        size = path.stat().st_size
        if str(size) != row["bytes"]:
            resized.append(f"{row['path']}  manifest {row['bytes']}B, disk {size}B")

    assert not gone, (
        "raw inputs recorded in the manifest are NO LONGER ON DISK:\n  "
        + "\n  ".join(sorted(gone))
        + "\n\nThis is the failure of MODEL-LOG §1.75. An input can leave "
          "`data/raw` without a git diff, without moving any artefact key, and "
          "without any other test going red — and every number measured after "
          "it left is measured against a different model.\n"
          "Restore it (`src/ingest_historic.py` and `src/ingest_lge.py` rebuild "
          "the archives deterministically), or, if the removal was deliberate, "
          "rebuild the manifest with `.venv/bin/python src/archive.py` IN THE "
          "SAME COMMIT and say why in MODEL-LOG.md.")
    assert not resized, (
        "raw inputs have CHANGED SIZE since the manifest was built:\n  "
        + "\n  ".join(sorted(resized))
        + "\n\nRaw inputs are meant to be immutable. Re-ingesting with a fixed "
          "parser is a legitimate reason to change one — and it silently "
          "changes every measurement taken against it, so it belongs in "
          "MODEL-LOG.md with the re-measurement, not in a manifest refresh on "
          "its own.")


def test_every_raw_input_on_disk_is_in_the_manifest():
    """The manifest must be CURRENT, or the test above checks a stale subset.

    On 2026-08-23 the manifest was twelve days old and held none of the 21
    files §1.70's ingest had produced — so a `--verify` run at that moment
    would have reported the six deleted ones as neither missing nor changed,
    because it had never heard of them. A guard over an out-of-date inventory
    is worth very little, and this is the test that keeps it in date.
    """
    recorded = {r["path"] for r in _raw_rows()}
    unrecorded = sorted(_files_on_disk() - recorded)
    assert not unrecorded, (
        f"{len(unrecorded)} raw input(s) on disk are not in the manifest:\n  "
        + "\n  ".join(unrecorded[:40])
        + ("\n  ..." if len(unrecorded) > 40 else "")
        + "\n\nRebuild it with `.venv/bin/python src/archive.py` and commit it. "
          "`data/**` is gitignored, so the manifest is the ONLY tracked record "
          "that these files existed and what was in them.")


def test_raw_input_hashes_match_when_asked():
    """The full check, opt-in because it re-hashes ~380MB.

        ARCHIVE_VERIFY_HASHES=1 .venv/bin/python tests/run_all.py
    """
    if os.environ.get("ARCHIVE_VERIFY_HASHES", "").lower() not in ("1", "true", "yes"):
        skip("set ARCHIVE_VERIFY_HASHES=1 to re-hash every raw input")
    drift = []
    for row in _raw_rows():
        path = ROOT / row["path"]
        if not path.exists():
            continue                      # reported by the existence test
        sha = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                sha.update(chunk)
        if sha.hexdigest() != row["sha256"]:
            drift.append(row["path"])
    assert not drift, (
        "raw inputs whose CONTENT changed at the same size:\n  "
        + "\n  ".join(sorted(drift)))


def test_every_election_the_record_expects_is_present_or_declared_absent():
    """Walk the CALENDAR the way `theta_record` walks it.

    Every file it will open must exist, or be named in `levels.KNOWN_ABSENT`
    with a reason. A new absence fails here in a second instead of silently
    moving the forecast. MODEL-LOG §1.75.
    """
    undeclared, declared = [], 0
    for year in sorted((y for y, e in CC.CALENDAR.items()
                        if e.kind == "LGE" and e.results), key=int):
        npe = CC.preceding(year, "NPE")
        if not npe:
            continue
        templates = (CC.CALENDAR[npe].results, CC.CALENDAR[year].results)
        if not all(templates):
            continue
        for tag, template in zip((npe, year), templates):
            for code in L.METRO_CODES:
                name = template.replace("{CODE}", code)
                if (ELECTIONS / name).exists():
                    continue
                if (name.split("_")[0], code) in L.KNOWN_ABSENT:
                    declared += 1
                else:
                    undeclared.append(f"{name}  (transition {npe} -> {year})")

    assert not undeclared, (
        "election files the θ/ρ record expects, which are neither on disk nor "
        "declared absent:\n  " + "\n  ".join(sorted(undeclared))
        + "\n\nRestore them, or add each to `levels.KNOWN_ABSENT` with the "
          "reason it is meant to be missing. Do not add entries merely to make "
          "this pass: an absence declared without a reason is the empty dict "
          "this test replaced.")
    assert declared, (
        "nothing is declared absent, so the KNOWN_ABSENT path is unexercised "
        "and a wrong entry there would not be caught")


def test_a_declared_absence_carries_a_reason_somebody_can_read():
    """`KNOWN_ABSENT` is a register, and §1.68's rule applies to it too."""
    assert L.KNOWN_ABSENT, "the declared-absence register is empty"
    for key, reason in L.KNOWN_ABSENT.items():
        assert isinstance(key, tuple) and len(key) == 2, (
            f"{key!r} is not an (archive tag, metro code) pair")
        assert len(reason.split()) >= 12, (
            f"{key} is declared absent with the reason {reason!r}. That is not "
            f"a reason, it is a label. The cost of the failure this register "
            f"exists to stop was that an absence LOOKED deliberate and nobody "
            f"could tell whether it was.")


def test_every_archive_the_ingest_can_key_is_ingested_or_declared():
    """The other direction: data we HOLD and have never extracted.

    `ingest_historic.MUNI_HEAD` is the enumerated table of which municipality
    string identifies each city in each pre-2011 national archive. **If it has
    an entry, the file is derivable today** — the national CSV is in
    `data/raw/elections/_source/` and the ingest is deterministic. So an entry
    with no derived file is data sitting on disk that nothing has ever read.

    Five are in that state and all five are declared: `lge2000` for Tshwane,
    Cape Town, Mangaung, Nelson Mandela Bay and Buffalo City. Ingesting them
    would ADD θ and ρ observations and move every number in the repository, so
    it is a measurement to be run deliberately and not a chore — see §1.75 and
    task P2a.
    """
    missing = []
    for tag, per_city in IH.MUNI_HEAD.items():
        for slug in sorted(per_city):
            city = CC.use(slug)
            suffix = ("_vd_party_clean.csv" if tag.startswith("lge")
                      else "_vd_party.csv")
            approx = "_approx" if tag == "npe1999" else ""
            name = f"{tag}{approx}_{city.code}{suffix}"
            if (ELECTIONS / name).exists():
                continue
            if (tag, city.code) in L.KNOWN_ABSENT:
                continue
            missing.append(f"{tag} / {slug} -> {name}")
    assert not missing, (
        "the ingest can key these archives but no derived file exists, and "
        "they are not declared:\n  " + "\n  ".join(sorted(missing))
        + "\n\nThe source CSV is already in `data/raw/elections/_source/`, so "
          "this is data the project HOLDS and has never used. Either run "
          "`.venv/bin/python src/ingest_historic.py --city <city> --year <tag>` "
          "— and re-measure, because it changes the θ record — or declare it "
          "in `levels.KNOWN_ABSENT` with the reason.")


def test_no_election_file_on_disk_is_unreachable():
    """A file present, plausible-looking, and read by nothing.

    The mirror image of §1.75: there, a file the model wanted was absent; here,
    a file that is present cannot be reached. A one-character slip in a
    filename produces exactly this, and the model goes on running with an
    empty record — which is the failure §1.43 and §1.75 both are.
    """
    expected = {ev.results.replace("{CODE}", code)
                for ev in CC.CALENDAR.values() if ev.results
                for code in L.METRO_CODES}
    unreachable = sorted(
        p.name for p in ELECTIONS.glob("*.csv")
        if p.name not in expected and p.name not in UNREACHED_BY_DESIGN)
    assert not unreachable, (
        "election files that no CALENDAR template can reach:\n  "
        + "\n  ".join(unreachable)
        + "\n\nEach is either misnamed — in which case the model is silently "
          "running without it — or a deliberate keepsake, in which case add it "
          "to `UNREACHED_BY_DESIGN` in this file with what it is and why it is "
          "kept.")


def test_the_missing_input_guard_actually_fires():
    """A GUARD THAT ONLY EVER PASSES IS INDISTINGUISHABLE FROM NO GUARD.

    `test_the_manifest_still_finds_every_raw_input_it_recorded` passes on a
    healthy tree, which is exactly what the four blind guards of §1.75 did. So
    this feeds it a manifest row for a file that is not there and requires it
    to fail — the §1.75 scenario, in miniature, on every run.
    """
    real = globals()["_raw_rows"]
    globals()["_raw_rows"] = lambda: real() + [{
        "path": "data/raw/elections/lge2006_MAN_vd_party_clean.csv.deleted",
        "bytes": "448978", "sha256": "0" * 64,
        "modified_utc": "2026-08-22T09:00:00Z", "provenance": "synthetic"}]
    try:
        try:
            test_the_manifest_still_finds_every_raw_input_it_recorded()
        except AssertionError as exc:
            assert "NO LONGER ON DISK" in str(exc), (
                f"the guard failed for the wrong reason: {exc}")
        else:
            raise AssertionError(
                "the manifest guard did NOT fail on a recorded input that is "
                "absent from disk. It has gone blind, and the deletion it "
                "exists to catch would pass silently — which is precisely what "
                "happened on 2026-08-22.")
    finally:
        globals()["_raw_rows"] = real

    # and the same for a file whose size has moved
    real2 = globals()["_raw_rows"]
    one = real2()[0]
    globals()["_raw_rows"] = lambda: [dict(one, bytes=str(int(one["bytes"]) + 1))]
    try:
        try:
            test_the_manifest_still_finds_every_raw_input_it_recorded()
        except AssertionError as exc:
            assert "CHANGED SIZE" in str(exc), f"wrong reason: {exc}"
        else:
            raise AssertionError(
                "the manifest guard did not notice a raw input changing size")
    finally:
        globals()["_raw_rows"] = real2


if __name__ == "__main__":
    # AT THE END — see test_register_matches_code. Append tests ABOVE this.
    raise SystemExit(run_module(globals()))
