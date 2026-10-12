"""Sharing a reader's forecast: the data the share cards and the arrival view
read from ``your-forecast/forecast.json`` (audits/2026-10-03-share-design).

* ``build_make.baseline``: the council election before the target, per roster
  party. Its seats come from the IEC's seat calculation and must sum to that
  election's council before the roster filter; its wards from the VD file,
  summing to that election's ward count; its vote from the same file. A party
  that did not stand is absent, which the cards print as "new". Each total is
  checked against the city config, never a typed figure, and the refusal is
  shown to fire on a constructed short file.
* ``build_make.election_of``: ``polls_open`` is the config's polling day,
  opening time and offset, as one ISO instant the Worker can parse.
"""
from __future__ import annotations

import csv
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))

import build_make  # noqa: E402
import build_play  # noqa: E402
import cityconfig  # noqa: E402


def _city():
    return cityconfig.active()


def test_the_baseline_sums_to_that_elections_council_wards_and_vote():
    city = _city()
    roster = list(build_play.roster())
    b = build_make.baseline(city, roster)
    year = cityconfig.preceding(city.default_target, "LGE")
    struct = city.structure_for(year)
    assert b["year"] == year
    # roster parties only, each with all four figures, and only parties that
    # stood (on either ballot)
    assert set(b["seats"]) == set(b["wards"]) == set(b["list_vote"]) == set(b["ward_vote"]) <= set(roster)
    assert all(b["list_vote"][c] > 0 or b["ward_vote"][c] > 0 for c in b["list_vote"])
    assert "vote" not in b, "the combined vote is retired: each ballot is its own"
    # the roster filter drops seats only of parties not on today's roster
    assert sum(b["seats"].values()) <= int(struct["council"])
    assert sum(b["wards"].values()) <= int(struct["wards"])
    for ballot in ("list_vote", "ward_vote"):
        assert 0 < sum(b[ballot].values()) <= 100.0 + 1e-9, ballot
    # the two ballots differ: list is not ward
    assert b["list_vote"] != b["ward_vote"]
    # it looked: most of the council is held by roster parties
    assert sum(b["seats"].values()) > int(struct["council"]) // 2


def test_the_baseline_refuses_a_file_whose_wards_do_not_add_up():
    """Constructed: the real VD file with one ward's rows dropped."""
    city = _city()
    roster = list(build_play.roster())
    year = cityconfig.preceding(city.default_target, "LGE")
    real = ROOT / city.path("raw", "elections", cityconfig.CALENDAR[year].results)
    with tempfile.TemporaryDirectory() as t, open(real, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
        first = rows[0]["Ward"]
        short = Path(t) / "data" / "raw" / "elections" / real.name
        short.parent.mkdir(parents=True)
        # the seat calculation is read from the same root: the real one
        (short.parent / "_reports").symlink_to(real.parent / "_reports")
        with open(short, "w", newline="", encoding="utf-8") as out:
            w = csv.DictWriter(out, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(r for r in rows if r["Ward"] != first)
        saved = build_make.REPO_ROOT
        build_make.REPO_ROOT = Path(t)
        try:
            try:
                build_make.baseline(city, roster)
            except build_make.MakeBuildError as e:
                assert "wards" in str(e)
            else:
                raise AssertionError("a file one ward short was accepted")
        finally:
            build_make.REPO_ROOT = saved
    # quiet again on the real file
    build_make.baseline(city, roster)


def test_polls_open_is_the_configs_day_time_and_offset():
    city = _city()
    e = build_make.election_of(city)
    struct = city.structure_for(city.default_target)
    at = datetime.fromisoformat(e["polls_open"])
    assert at.date().isoformat() == e["date"] == str(struct["election_date"])
    import tomllib
    clock = tomllib.loads((ROOT / "content" / city.slug / "election.toml").read_text(encoding="utf-8"))
    assert at.strftime("%H:%M") == clock["polls_open"]
    assert at.utcoffset() is not None
    assert e["polls_open"].endswith(clock["utc_offset"]) and e["zone"] == clock["time_zone"]


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
