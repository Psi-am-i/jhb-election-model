"""The preflight check must report what is there, not what it hopes is there.

`inputs_preflight` exists because every input to a forecast of an unheld
election has a silent fallback. A check with its own silent fallback would be
worse than none, so these tests are about the check being WRONG rather than
about it being red: they build trees where an input is absent or stale and
assert it says so, and they assert the two numbers it reports are counted and
not guessed.
"""
from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import inputs_preflight as P  # noqa: E402

from _support import ROOT  # noqa: E402


def _rows(city="joburg", target="2026"):
    return {r["input"]: r for r in P._rows(city, target)}


def test_the_roster_is_parsed_not_pattern_matched():
    """82, counted from the TOML.

    The first version regexed the file for `parties = [` and reported 5 for a
    roster of 82 — a wrong number on a check whose entire output is numbers,
    and one nothing would have contradicted.
    """
    row = _rows()["2026 certified party roster"]
    doc = __import__("tomllib").loads(
        (ROOT / "judgements" / "joburg-2026.toml").read_text(encoding="utf-8"))
    n = len(doc["roster"]["parties"])
    assert f"{n} parties" in row["have"], \
        f"roster row says {row['have']!r}, the file holds {n} parties"
    assert n > 10, "a roster this small means the parse found the wrong table"


def test_split_voting_districts_are_counted_from_the_file():
    """The split count is the trap the row exists to name, so it must be real."""
    row = _rows()["2026 split voting districts"]
    feats = json.loads(
        (ROOT / "data" / "raw" / "geo" / "vds2026_JHB.geojson").read_text())["features"]
    uniq = {str(f["properties"]["VDNumber"]) for f in feats}
    assert f"{len(feats)} VD-ward rows for {len(uniq)} VDs" in row["have"]
    assert len(feats) > len(uniq), \
        "no split VDs found in Johannesburg, which contradicts ward_parts"


def test_every_declared_city_is_looked_up_under_its_own_iec_code():
    """The boundary and baseline rows use the code in ``cities/<slug>.toml``.

    ⛔ They used a typed map of three Gauteng cities and fell back to
    ``city.upper()``, so eThekwini, Cape Town, Mangaung, Nelson Mandela Bay and
    Buffalo City looked for ``vds2026_ETHEKWINI.geojson`` and the like, and
    reported their boundaries and both baselines MISSING while every file was
    on disk (2026-09-29). The population is every declared city, both ways.
    """
    import cityconfig
    slugs = sorted(p.stem for p in (ROOT / "cities").glob("*.toml"))
    assert 2 <= len(slugs) <= 50, f"declared cities out of range: {slugs}"
    found_outside_gauteng = False
    for slug in slugs:
        city = cityconfig.load(slug)
        rows = _rows(slug)
        vds = ROOT / "data" / "raw" / "geo" / f"vds2026_{city.code}.geojson"
        assert rows["2026 voting districts"]["ok"] == vds.exists(), (
            f"{slug}: the preflight and the file named by its IEC code "
            f"{city.code!r} disagree about the 2026 voting districts")
        if vds.exists() and city.province != "GP":
            found_outside_gauteng = True
    if any((ROOT / "data" / "raw" / "geo").glob("vds2026_*.geojson")):
        assert found_outside_gauteng, (
            "no city outside Gauteng has its 2026 voting districts found — "
            "the lookup this test guards is the one that failed that way")


def test_a_missing_required_input_is_reported_and_exits_under_strict(tmp_path=None):
    """The whole point: absence must be loud, because the model is quiet."""
    rows = P._rows("nosuchcity", "2026")
    required = [r for r in rows if r["level"] == P.REQUIRED]
    assert required, "no required inputs declared"
    assert all(not r["ok"] for r in required), \
        "a city with no data reported some required input as in hand"
    assert P.main(["--city", "nosuchcity", "--target", "2026"]) == 0
    assert P.main(["--city", "nosuchcity", "--target", "2026", "--strict"]) == 1


def test_a_stale_roll_snapshot_is_not_counted_as_having_it():
    """Present is not current. Registration moves daily before a poll."""
    snaps = sorted(ROOT.glob("archive/iec-registration-*/"))
    assert snaps, "no registration snapshot archived at all"
    import re
    dates = [re.search(r"(\d{4}-\d{2}-\d{2})", s.name) for s in snaps]
    assert all(dates), "a snapshot directory carries no date in its name"
    age = (_dt.date.today() - _dt.date.fromisoformat(dates[-1].group(1))).days
    row = _rows()["2026 voters' roll (registration)"]
    assert row["ok"] == (age <= P.SNAPSHOT_STALE_DAYS), \
        f"snapshot is {age} days old and the row says ok={row['ok']}"
