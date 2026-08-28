"""``montecarlo.ward_parts`` — the VD → ward map every ward result is built on.

``ward_parts(target, data_dir, processed)`` answers one question: which voting
districts sit in which ward, and how many registered voters each of those
pieces carries. Everything ward-shaped downstream rides on it —
``run_model`` sums it into ``registered`` (montecarlo.py:2627), derives the
forecastable ward list from it (``all_wards``, :2699), and weights each ward's
tally by the part registrations (``part_reg``, :2712). A part that goes missing
here does not raise: it silently reweights a ward, or removes one.

The function has **two sources and picks between them by file existence
alone**, which is the whole reason it needs pinning:

* a **crosswalk** ``<processed>/vd_ward_<year>.csv``, written by
  ``build_concordance.ward_parts`` — one row per VD/ward *part*, so a VD
  straddling two wards appears twice with its roll apportioned by
  ``part_registered`` (assumption A1, build_concordance.py:164-167);
* otherwise the target's own **result file**, which names exactly one ward per
  VD and carries the whole VD's roll on the row.

The second return value is the run's only record of which of those two ran —
``run_model`` prints it and nothing else reports it (montecarlo.py:3068). So it
is part of the contract and is tested as such.

WHAT THESE TESTS DO **NOT** DO: they never assert that a number equals what the
code returns because it returns it. Expected values come from arithmetic done
by hand on a constructed CSV, from the ward and VD counts recorded
independently in ``cities/joburg.toml`` ``[structure]`` (derived by
``derive_city.py`` from the IEC's own seat-calculation reports), or from
conservation invariants that must hold whatever the implementation is.

Four tests below document behaviour that is **wrong**. Each says so in its own
docstring and is named for the defect. They are written against the ACTUAL
behaviour deliberately, because phase A of ARCHITECTURE.md is "declare and test
the seams — no refactor"; the fix is not this file's job.

MUTATION COVERAGE OF THE RESULT-FILE BRANCH (re-verified 2026-08-27). §1.97's
mutation pass left two survivors here, and both are now closed and proved
closed by applying the mutation to a copy of ``src/montecarlo.py``, running
this file, and restoring:

* ``if vd in seen or not row.get("Ward")`` → ``if not row.get("Ward")``, which
  turns first-wins into LAST-wins, is caught by
  ``test_the_first_row_that_names_a_ward_wins_and_a_later_row_cannot_move_the_vd``;
* ``row["Ward"].strip()`` → ``row["Ward"]``, which makes a padded ward cell a
  second phantom ward, is caught by
  ``test_a_ward_padded_with_whitespace_is_not_counted_as_a_second_ward``.

Both fixtures were widened in the same pass to close the WEAKER form of each
mutation as well — a de-duplication that only remembers the previous row, and a
``.strip(" ")`` that normalises spaces but not tabs or carriage returns. Each
test's docstring says which variant its fixture exists to kill; that is the
part to preserve if the fixture is ever edited, because the obvious
simplification of either one re-opens the gap.

Run:
    ./.venv/bin/python tests/test_ward_parts.py
    ./.venv/bin/python -m pytest tests/test_ward_parts.py -q
"""

from __future__ import annotations

import ast
import csv
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, skip  # noqa: E402

import cityconfig  # noqa: E402
import montecarlo as M  # noqa: E402

ELECTIONS = ROOT / "data" / "raw" / "elections"

CROSSWALK_COLUMNS = ["VD_Number", "Ward_{year}", "WardID_{year}",
                     "vd_registered", "part_registered", "weight", "is_split"]


# --------------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------------

@contextmanager
def city_target(slug: str, year: str):
    """Point ``cityconfig`` at one city-year and put back what was there.

    ``cityconfig.use`` writes process globals that ``resolve_path`` reads, so a
    test that switched city and did not switch back would hand the next test in
    the file another city's ``{CODE}`` — the un-namespaced-output hazard on file
    for this project (MODEL-LOG §1.40), reached through the test suite.
    """
    previous_city = cityconfig.active().slug
    previous_year = cityconfig.target().year
    try:
        cityconfig.use(slug)
        yield cityconfig.use_target(year)
    finally:
        cityconfig.use(previous_city)
        cityconfig.use_target(previous_year)


@contextmanager
def crosswalk(year: str, rows: list[dict]):
    """A temporary ``processed`` directory holding one hand-built crosswalk."""
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        path = directory / f"vd_ward_{year}.csv"
        fields = [c.format(year=year) for c in CROSSWALK_COLUMNS]
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow({c.format(year=year): v for c, v in row.items()})
        yield directory


@contextmanager
def result_file(target, rows: list[dict],
                columns=("VD_Number", "Ward", "Registered_Population")):
    """A temporary ``data_dir`` holding one hand-built result file.

    Yields ``(data_dir, empty_processed)`` — the empty processed directory is
    what forces the result-file branch, since the branch is chosen by nothing
    but whether the crosswalk exists.
    """
    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp) / "elections"
        data_dir.mkdir()
        processed = Path(tmp) / "processed"
        processed.mkdir()
        name = cityconfig.resolve_path(target.results(target.year)).name
        with (data_dir / name).open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(columns))
            writer.writeheader()
            writer.writerows(rows)
        yield data_dir, processed


def real_crosswalk_rows() -> list[dict]:
    """Johannesburg's committed 2026 crosswalk, read directly."""
    path = ROOT / "data" / "processed" / "vd_ward_2026.csv"
    if not path.exists():
        skip(f"no committed 2026 crosswalk at {path}")
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------------------------
# the crosswalk branch — a split VD is what it exists for
# --------------------------------------------------------------------------

def test_a_split_vd_is_returned_once_per_ward_with_its_roll_apportioned():
    """If this failed, a VD straddling two wards would land whole in one of them.

    Constructed by hand: VD ``A`` has 1,000 registered voters, 600 of them in
    ward 1 and 400 in ward 2; VD ``B`` is wholly inside ward 2 with 500. The
    expected answer is arithmetic on that input, not a recording of output —
    three parts, the two ``A`` parts carrying 600 and 400.

    This is the apportionment MODEL-LOG §1.3 and assumption A1 call for, and
    the only reason the crosswalk is preferred over the result file for a
    target not yet held (``ward_parts`` docstring). 181 of Johannesburg's 865
    VDs are split in 2026, so the whole-VD alternative would misplace voters in
    most of the city's wards.
    """
    rows = [
        {"VD_Number": "A", "Ward_{year}": "1", "WardID_{year}": "79800001",
         "vd_registered": "1000", "part_registered": "600",
         "weight": "0.600000", "is_split": "Y"},
        {"VD_Number": "A", "Ward_{year}": "2", "WardID_{year}": "79800002",
         "vd_registered": "1000", "part_registered": "400",
         "weight": "0.400000", "is_split": "Y"},
        {"VD_Number": "B", "Ward_{year}": "2", "WardID_{year}": "79800002",
         "vd_registered": "500", "part_registered": "500",
         "weight": "1.000000", "is_split": "N"},
    ]
    with city_target("joburg", "2026") as target, crosswalk("2026", rows) as processed:
        parts, _ = M.ward_parts(target, ELECTIONS, processed)

    assert parts == [("A", "1", 600), ("A", "2", 400), ("B", "2", 500)], parts
    assert sum(r for vd, _w, r in parts if vd == "A") == 1000
    assert [type(r) for _vd, _w, r in parts] == [int, int, int], (
        "the registration must be an int: run_model indexes on `r > 0` "
        "(montecarlo.py:2700) and sums it into a defaultdict(int)")


def test_the_source_label_counts_split_vds_not_split_rows():
    """If this failed, the run's only report of the ward source would misstate it.

    ``run_model`` prints this string and nothing else records which of the two
    sources ran (montecarlo.py:3068). A three-way split contributes three rows
    but is ONE split VD; a label counting rows would report 181 Johannesburg
    splits as 240-odd and quietly stop matching the concordance builder's own
    printed count (build_concordance.py:216-219).

    Hand arithmetic on the fixture: 4 rows, 2 VDs, 1 of them split.
    """
    rows = [
        {"VD_Number": "C", "Ward_{year}": str(w), "WardID_{year}": f"7980000{w}",
         "vd_registered": "900", "part_registered": "300",
         "weight": "0.333333", "is_split": "Y"} for w in (1, 2, 3)
    ] + [
        {"VD_Number": "D", "Ward_{year}": "3", "WardID_{year}": "79800003",
         "vd_registered": "100", "part_registered": "100",
         "weight": "1.000000", "is_split": "N"},
    ]
    with city_target("joburg", "2026") as target, crosswalk("2026", rows) as processed:
        parts, source = M.ward_parts(target, ELECTIONS, processed)

    assert len(parts) == 4
    assert source == "vd_ward_2026.csv (4 parts over 2 VDs, 1 split)", source


def test_a_crosswalk_naming_another_years_ward_column_refuses_loudly():
    """If this failed, a mismatched crosswalk would be read as an empty ward map.

    The year appears twice — in the filename and in the ``Ward_<year>`` column
    — and nothing checks that they agree. The contract worth having is that a
    disagreement RAISES: a ``.get(column, "")`` here would hand every VD the
    empty-string ward, and ``run_model``'s ``sorted(..., key=int)`` at :2699
    would then die somewhere else entirely, or worse, collapse all 135 wards
    into one. This pins the loud failure so a later refactor cannot soften it
    into the silent-fallback shape ARCHITECTURE.md exists to retire.
    """
    rows = [
        {"VD_Number": "A", "Ward_{year}": "1", "WardID_{year}": "79800001",
         "vd_registered": "10", "part_registered": "10",
         "weight": "1.000000", "is_split": "N"},
    ]
    # Written with 2026 headers, then renamed to look like a 2021 crosswalk.
    with city_target("joburg", "2021") as target, crosswalk("2026", rows) as processed:
        (processed / "vd_ward_2026.csv").rename(processed / "vd_ward_2021.csv")
        try:
            M.ward_parts(target, ELECTIONS, processed)
        except (KeyError, SystemExit) as exc:
            # RE-RECORDED 2026-08-28: it was a bare `KeyError` from the dict
            # lookup; `read_ward_crosswalk` (§1.97 F18) now raises SystemExit
            # naming the column it wanted and the Ward columns the file has.
            # Both are loud, which is what this test is for; the second is
            # actionable. Accept either so the test pins the CONTRACT — it
            # raises — rather than the exception class.
            assert "Ward_2021" in str(exc), exc
        else:
            raise AssertionError(
                "a crosswalk whose ward column is for a different year was "
                "accepted; it must refuse rather than produce a ward map that "
                "is silently empty or wrong")


def test_the_crosswalk_wins_over_the_result_file_on_existence_alone():
    """If this failed, a past target would read the wrong delimitation.

    The branch is selected by ``crosswalk.exists()`` and by nothing else — not
    by the target being unheld, not by any flag. That is a real property of the
    seam and callers must be able to rely on it: dropping a
    ``vd_ward_<year>.csv`` into a target's processed directory changes which
    delimitation the backtest of that year runs under, with no argument
    changed and no warning printed. The returned label is the only signal, and
    this test is what makes that promise checkable.
    """
    rows = [
        {"VD_Number": "32860728", "Ward_{year}": "1", "WardID_{year}": "79800001",
         "vd_registered": "7", "part_registered": "7",
         "weight": "1.000000", "is_split": "N"},
    ]
    with city_target("joburg", "2021") as target, crosswalk("2021", rows) as processed:
        parts, source = M.ward_parts(target, ELECTIONS, processed)

    assert parts == [("32860728", "1", 7)], parts
    assert source.startswith("vd_ward_2021.csv"), source
    assert "boundaries and roll only" not in source


# --------------------------------------------------------------------------
# the result-file branch — a past target, read from its own published record
# --------------------------------------------------------------------------

def test_a_vd_named_on_every_ballot_row_is_returned_once():
    """If this failed, a VD's roll would be counted once per party per ballot.

    A cleaned IEC result file carries one row per VD per ballot type per party
    — 71,015 rows for 867 Johannesburg VDs in 2021. ``run_model`` sums the
    returned registrations into ``registered[vd]`` (montecarlo.py:2627) and
    uses them as the ward tally's weights (:2712), so a VD returned 82 times
    would carry 82x its true weight.

    Hand arithmetic: one VD on four rows, 3,554 registered → exactly one part
    of 3,554.
    """
    with city_target("joburg", "2021") as target:
        rows = [
            {"VD_Number": "32860728", "Ward": "79800001",
             "Registered_Population": "3554"} for _ in range(4)
        ]
        with result_file(target, rows) as (data_dir, processed):
            parts, source = M.ward_parts(target, data_dir, processed)

    assert parts == [("32860728", "79800001", 3554)], parts
    assert source == ("lge2021_JHB_vd_party_clean.csv "
                      "(boundaries and roll only; 1 VDs, none split)"), source


def test_a_result_row_naming_no_ward_does_not_hide_a_later_row_that_does():
    """If this failed, one blank cell would delete a whole VD from the council.

    The skip is ``if vd in seen or not row.get("Ward")``, so a blank ward is
    skipped as a ROW, not remembered as a VD. A VD whose first row happens to
    carry no ward is therefore still recovered from its second. Johannesburg's
    2011, 2016 and 2021 files have no blank ward cells at all, so this is a
    latent property; it is pinned because the alternative reading of the same
    line — mark the VD seen, then skip — is a one-character change away and
    would lose the VD in silence.
    """
    with city_target("joburg", "2021") as target:
        rows = [
            {"VD_Number": "V1", "Ward": "", "Registered_Population": "111"},
            {"VD_Number": "V1", "Ward": "79800009", "Registered_Population": "222"},
        ]
        with result_file(target, rows) as (data_dir, processed):
            parts, _ = M.ward_parts(target, data_dir, processed)

    assert parts == [("V1", "79800009", 222)], parts


def test_the_first_row_that_names_a_ward_wins_and_a_later_row_cannot_move_the_vd():
    """If this failed, a VD's ward would depend on which ballot row came last.

    Added after adversarial mutation testing: deleting ``vd in seen`` from the
    skip at montecarlo.py:790 — turning first-wins into last-wins — passed
    every other test in this file, because Johannesburg's published files never
    disagree with themselves (checked in
    ``test_no_joburg_result_file_puts_one_vd_in_two_wards``) and a dict keeps
    its first-insertion position even when the value is overwritten. The rule
    was therefore unpinned: a one-token edit could change which delimitation a
    backtest ran under and nothing would say so.

    The expected value is not "the right ward" — nothing in the published
    record can say which of two disagreeing rows is right, which is exactly why
    the resolution must be a STATED, deterministic rule rather than an
    accident of row order. The rule stated by the docstring and repeated by the
    returned label ("none split") is first-wins, and it carries the roll from
    the same row: a VD's ward and roll are properties of the VD, so the answer
    must not depend on how many ballot-type and party rows follow it.

    Both halves are asserted: that a disagreeing later row is ignored, and
    that appending further rows to a VD changes nothing at all.

    **The disagreeing rows are deliberately NOT adjacent** (2026-08-27). The
    first version of this fixture put V1's two rows next to each other, which
    a de-duplication comparing only against the PREVIOUS row — ``if vd ==
    last_vd`` rather than ``if vd in seen`` — would have passed. That weaker
    rule is the plausible one to arrive by accident, because a real IEC file is
    sorted by VD and the two behave identically on it; it stops being
    identical the moment a file is sorted by ballot type or by party, which
    ``lge2021_JHB_vd_party_clean.csv``'s own header order makes a one-sort
    change away. Interleaving V2 between V1's rows makes the memory, not the
    adjacency, the thing being tested.
    """
    with city_target("joburg", "2021") as target:
        rows = [
            {"VD_Number": "V1", "Ward": "79800001", "Registered_Population": "111"},
            {"VD_Number": "V2", "Ward": "79800003", "Registered_Population": "333"},
            {"VD_Number": "V1", "Ward": "79800002", "Registered_Population": "222"},
        ]
        expected = [("V1", "79800001", 111), ("V2", "79800003", 333)]
        with result_file(target, rows) as (data_dir, processed):
            parts, _ = M.ward_parts(target, data_dir, processed)
        assert parts == expected, (
            "the first row naming a ward must win, and its roll with it, "
            "however many rows for other VDs sit between the two: "
            + repr(parts))

        # Stability: the extra rows a real file carries (one per ballot type
        # per party) must not be able to move the answer.
        with result_file(target, rows[:2]) as (data_dir, processed):
            alone, _ = M.ward_parts(target, data_dir, processed)
        assert alone == parts, (alone, parts)


def test_a_ward_padded_with_whitespace_is_not_counted_as_a_second_ward():
    """If this failed, one ward could appear twice under two spellings.

    Added after adversarial mutation testing: removing ``.strip()`` from
    ``row["Ward"].strip()`` (montecarlo.py:795) passed every other test here,
    because today's cleaned files carry no padding. Stray whitespace in IEC
    CSVs is a recorded hazard for this project, and it corrupts silently rather
    than raising.

    The argument for the expected value is independent of the implementation: a
    ward's identity is its number, and ``"79800001 "`` and ``"79800001"`` are
    the same ward of the same council. ``run_model`` keys wards by this string
    (``all_wards``, montecarlo.py:2699, and ``part_reg`` at :2712), so two
    spellings would produce 136 wards where the Municipal Structures Act
    delimitation — and ``cities/joburg.toml`` ``[structure.by_year]`` — has
    135, splitting one ward's roll across two phantom entries. ``key=int``
    would not catch it: ``int(" 79800001 ")`` parses happily.

    **Three padding characters, not one** (2026-08-27). The first version of
    this fixture padded with spaces only, which a ``.strip(" ")`` — a partial
    normalisation, and a likelier edit than deleting the call outright — would
    have passed. A leading tab and a trailing carriage return are the two this
    project has actually met: the recorded IEC CSV traps are CRLF-shaped, and a
    CR surviving into a field is what a file written on one platform and split
    on another produces. All three survive the fixture's own ``csv`` round trip
    intact — checked directly: the writer quotes the CR field and the reader
    hands it back with the CR still attached — so each is genuinely reaching
    ``ward_parts`` as padding rather than being cleaned up in transit.
    ``str.strip()`` with no argument removes all three; anything narrower
    leaves a phantom ward behind.
    """
    with city_target("joburg", "2021") as target:
        rows = [
            {"VD_Number": "V1", "Ward": " 79800001 ", "Registered_Population": "10"},
            {"VD_Number": "V2", "Ward": "\t79800001", "Registered_Population": "20"},
            {"VD_Number": "V3", "Ward": "79800001\r", "Registered_Population": "30"},
            {"VD_Number": "V4", "Ward": "79800001", "Registered_Population": "40"},
        ]
        with result_file(target, rows) as (data_dir, processed):
            parts, _ = M.ward_parts(target, data_dir, processed)

    assert parts == [("V1", "79800001", 10), ("V2", "79800001", 20),
                     ("V3", "79800001", 30), ("V4", "79800001", 40)], parts
    assert len({w for _vd, w, _r in parts}) == 1, (
        "one ward written several ways became several wards: "
        + repr(sorted({w for _vd, w, _r in parts})))


def test_a_vd_whose_every_row_names_no_ward_disappears_without_a_word():
    """DEFECT, documented not fixed: a silent input loss with no counter.

    A VD present in the result file but carrying no ward on any row is dropped.
    Nothing counts it, nothing prints it, and the returned label still reports
    "N VDs" over the survivors — so the number that would reveal the loss is
    computed from the already-truncated list. ``run_model``'s only report of a
    gap is the *ward* drop message at montecarlo.py:2708, which cannot fire
    when the ward still has other VDs in it: the ward simply gets lighter.

    This is the ARCHITECTURE.md defect class in its plainest form — absence
    resolving to the neutral value (here, exclusion) with no way to tell it
    from a file that genuinely has nothing to say. It is latent on today's
    inputs (0 blank ward cells across Johannesburg 2011/2016/2021, checked in
    ``test_no_joburg_result_file_puts_one_vd_in_two_wards``) and would arrive
    with an ingest change, not with a modelling one.

    The assertion below records what the code does TODAY. When the drop becomes
    an error or a counted warning this test must change with it, and that is
    the point: the change will be visible.
    """
    with city_target("joburg", "2021") as target:
        rows = [
            {"VD_Number": "V1", "Ward": "79800009", "Registered_Population": "10"},
            {"VD_Number": "GHOST", "Ward": "", "Registered_Population": "9999"},
            {"VD_Number": "GHOST", "Ward": "", "Registered_Population": "9999"},
        ]
        with result_file(target, rows) as (data_dir, processed):
            parts, source = M.ward_parts(target, data_dir, processed)

    assert parts == [("V1", "79800009", 10)], parts
    assert "1 VDs" in source, (
        "the label counts what survived, so it cannot report the loss: " + source)


def test_a_missing_registration_refuses_instead_of_becoming_zero_voters():
    """RE-RECORDED 2026-08-28. The defect is fixed; this asserts the refusal.

    This was `..._silently_becomes_zero_voters` and pinned the behaviour:
    ``int(float(row.get("Registered_Population") or 0))`` turned a blank cell
    AND a missing column into ``0`` registered voters, indistinguishable from a
    genuinely empty voting district. Its own note asked for the change — *"a
    missing roll is a missing input. It should refuse here and name the file,
    the way `pools._target_roll` was made to after MODEL-LOG §1.40"* — and
    §1.97 F16 is that change.

    **The two cases are now told apart, which is the point.** A MISSING COLUMN
    is a different file and refuses; a BLANK CELL is a datum about one VD and is
    counted and reported in the source label. Collapsing them was the defect.

    What it cost downstream, kept because it is the reason to refuse: `run_model`
    keeps only parts with ``r > 0``, so a renamed column made EVERY part 0,
    ``usable`` empty, and the run died several stages later with the true cause
    a hundred lines upstream.
    """
    with city_target("joburg", "2021") as target:
        # A BLANK CELL: still zero, still returned — and now counted.
        blank = [{"VD_Number": "V1", "Ward": "79800009",
                  "Registered_Population": ""}]
        with result_file(target, blank) as (data_dir, processed):
            parts, source = M.ward_parts(target, data_dir, processed)
        assert parts == [("V1", "79800009", 0)], parts
        assert "1 blank roll" in source, (
            f"a blank roll must be REPORTED, not merely tolerated: {source}")

        # A MISSING COLUMN: a different file, and it refuses naming what it got.
        rows = [{"VD_Number": "V1", "Ward": "79800009"}]
        with result_file(target, rows, columns=("VD_Number", "Ward")) as (d, pr):
            try:
                M.ward_parts(target, d, pr)
            except SystemExit as exc:
                assert "Registered_Population" in str(exc), exc
                assert "columns present" in str(exc), (
                    f"the refusal must show what the file DOES have, or the "
                    f"reader cannot tell which file they handed it: {exc}")
            else:
                raise AssertionError(
                    "a result file with no `Registered_Population` column was "
                    "accepted, and every ward would be given a roll of zero. "
                    "MODEL-LOG §1.97 F16.")

def test_ward_parts_returns_the_same_answer_twice():
    """If this failed, no measurement taken through this seam would be reproducible.

    Both branches iterate a CSV in file order (the crosswalk branch keeps rows,
    the result branch keeps a dict keyed by first appearance), so the output
    must be order-stable, not merely set-equal. ``run_model`` builds numpy
    index arrays from the list positions (montecarlo.py:2710-2712), so a
    reordering would silently permute ward weights between runs.

    Checked on both branches: Johannesburg 2026 (crosswalk) and 2021 (result
    file), the two configurations the repository actually runs.
    """
    for year in ("2026", "2021"):
        with city_target("joburg", year) as target:
            first = M.ward_parts(target, ELECTIONS, target.processed)
            second = M.ward_parts(target, ELECTIONS, target.processed)
        assert first == second, f"{year} is not reproducible"
        assert first[0] == second[0], f"{year} changed order"


def test_the_2026_crosswalk_covers_every_ward_of_the_council_exactly():
    """If this failed, the forecast would be missing or inventing wards.

    ``cities/joburg.toml`` ``[structure]`` records 135 wards and 865 VDs for
    2026 — derived by ``derive_city.py`` from the IEC's own record, not from
    this model. The Municipal Structures Act requires every ward to be
    contiguous and to contain voters, so a delimitation with 135 wards must
    show 135 distinct wards in a complete VD→ward map, and each of the 865 VDs
    must appear at least once.

    ``run_model`` builds its ward list straight from this (``all_wards``,
    montecarlo.py:2699) and reports a shortfall only for wards it drops for
    lack of data — a ward that never appeared here is not even a candidate to
    be reported.
    """
    with city_target("joburg", "2026") as target:
        parts, source = M.ward_parts(target, ELECTIONS, target.processed)
        expected_wards = target.wards
        expected_vds = int(target.structure["vds"])

    assert source.startswith("vd_ward_2026.csv"), (
        "Johannesburg 2026 must come from the crosswalk, not a result file: "
        + source)
    wards = {w for _vd, w, _r in parts}
    vds = {vd for vd, _w, _r in parts}
    assert len(wards) == expected_wards, (len(wards), expected_wards)
    assert len(vds) == expected_vds, (len(vds), expected_vds)
    assert all(w.isdigit() for w in wards), (
        "run_model sorts these with key=int (montecarlo.py:2699); a "
        "non-numeric ward label would raise there, not here")


def test_no_vd_ward_pair_is_listed_twice_and_no_part_is_negative():
    """If this failed, a ward's roll would be double-counted or reduced.

    Two invariants that must hold of any apportionment, checked on the real
    2026 crosswalk:

    * one row per (VD, ward) piece — ``run_model`` sums ``part_registered``
      into ``registered[vd]`` (montecarlo.py:2627) with no de-duplication, so a
      repeated pair inflates that VD's roll;
    * no negative count — a negative part would subtract voters from a ward
      tally, and ``r > 0`` at :2700 would silently drop it instead of raising.

    Zero IS legitimate and is not asserted against: 59 of Johannesburg's 2026
    parts are zero-voter slivers, which ``build_concordance`` weights at 0.0 on
    purpose (build_concordance.py:164-167).
    """
    with city_target("joburg", "2026") as target:
        parts, _ = M.ward_parts(target, ELECTIONS, target.processed)

    pairs = [(vd, w) for vd, w, _r in parts]
    assert len(pairs) == len(set(pairs)), "a (VD, ward) part is listed twice"
    assert all(r >= 0 for _vd, _w, r in parts), "a part carries negative voters"


def test_the_apportioned_parts_of_a_vd_sum_to_that_vds_whole_roll():
    """If this failed, the apportionment would create or destroy voters.

    Splitting a VD between wards moves voters; it must not change how many
    there are. The check is against the crosswalk's own ``vd_registered``
    column — the whole VD's roll as published — read here independently of
    ``ward_parts``. Citywide the parts must also sum to the registered total
    recorded in ``cities/joburg.toml`` (2,348,781, derived from the IEC roll).

    A conservation failure would show up nowhere else: ``run_model`` sums the
    parts and never sees the whole-VD figure, so the loss would be invisible.
    """
    rows = real_crosswalk_rows()
    whole = {r["VD_Number"]: int(r["vd_registered"]) for r in rows}

    with city_target("joburg", "2026") as target:
        parts, _ = M.ward_parts(target, ELECTIONS, target.processed)
        expected_total = int(target.structure["registered"])

    by_vd: dict[str, int] = {}
    for vd, _w, r in parts:
        by_vd[vd] = by_vd.get(vd, 0) + r
    bad = {vd: (got, whole[vd]) for vd, got in by_vd.items() if got != whole[vd]}
    assert not bad, f"apportionment does not conserve the roll: {list(bad)[:5]}"
    assert sum(by_vd.values()) == expected_total, (
        sum(by_vd.values()), expected_total)


def test_no_joburg_result_file_puts_one_vd_in_two_wards():
    """If this failed, ``ward_parts`` would silently discard a real ward split.

    The result-file branch keeps the FIRST ward it sees for a VD and skips
    every later row for it. The docstring justifies that with a claim of fact —
    *"it names exactly one ward per VD — checked for Johannesburg 2011, 2016
    and 2021"* — and the returned label repeats it as "none split". This test
    is that check, run against the published files rather than trusted from
    prose, because a file that DID split a VD would be truncated here with no
    error and the label would state the opposite of the truth.

    Ward and VD counts are cross-checked against ``cities/joburg.toml``
    ``[structure.by_year]`` (130 wards / 797 VDs in 2011; 135 / 842 in 2016;
    135 / 867 in 2021), recorded from the IEC's seat-calculation reports.
    """
    for year in ("2011", "2016", "2021"):
        with city_target("joburg", year) as target:
            path = cityconfig.resolve_path(ELECTIONS / target.results(year))
            if not path.exists():
                skip(f"no result file for joburg {year} at {path}")
            structure = target.city.structure_for(year)
            parts, source = M.ward_parts(target, ELECTIONS, target.processed)

        wards_by_vd: dict[str, set[str]] = {}
        with path.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                if row.get("Ward"):
                    wards_by_vd.setdefault(row["VD_Number"], set()).add(
                        row["Ward"].strip())
        multi = {vd: w for vd, w in wards_by_vd.items() if len(w) > 1}
        assert not multi, (
            f"joburg {year} puts a VD in two wards; ward_parts keeps only the "
            f"first and the label still says 'none split': {list(multi)[:3]}")

        assert source.endswith("none split)"), source
        vds = [vd for vd, _w, _r in parts]
        assert len(vds) == len(set(vds)), f"{year} returns a VD twice"
        assert len(vds) == int(structure["vds"]), (year, len(vds), structure["vds"])
        assert len({w for _vd, w, _r in parts}) == int(structure["wards"]), year


# --------------------------------------------------------------------------
# the duplicated-name and duplicated-rule findings
# --------------------------------------------------------------------------

def test_the_two_functions_called_ward_parts_are_a_producer_and_a_consumer():
    """The name collision is not a duplicated rule, and this pins which it is.

    ``build_concordance.ward_parts(vds: GeoDataFrame) -> list[dict]`` WRITES
    ``vd_ward_2026.csv``; ``montecarlo.ward_parts(target, data_dir, processed)``
    READS it. Different arity, different types, opposite direction — genuinely
    different concerns that share a name (CLAUDE.md's "no duplicated logic"
    rule is not violated by the pair), and neither module imports the other, so
    neither can shadow the other at an import site.

    Worth a test rather than a note because the shadowing case is the dangerous
    one and it is one ``from build_concordance import *`` away. This asserts
    the two are reachable only under their own module and that the signatures
    stayed incompatible, so a future merge of the names cannot pass silently.
    """
    import inspect
    try:
        import build_concordance
    except ImportError as exc:  # geopandas is not a hard dependency of the suite
        skip(f"build_concordance is not importable here: {exc}")

    consumer = list(inspect.signature(M.ward_parts).parameters)
    producer = list(inspect.signature(build_concordance.ward_parts).parameters)
    assert consumer == ["target", "data_dir", "processed"], consumer
    assert producer == ["vds"], producer
    assert M.ward_parts is not build_concordance.ward_parts
    assert getattr(M, "build_concordance", None) is None, (
        "montecarlo has acquired a build_concordance attribute; the two "
        "ward_parts are now one namespace apart and one can shadow the other")
    assert getattr(build_concordance, "montecarlo", None) is None


def test_nothing_reimplements_the_crosswalk_read():
    """RE-RECORDED 2026-08-28. The duplication is gone; this stops it returning.

    This was `test_leverage_reimplements_the_crosswalk_branch_of_ward_parts`
    and it asserted that the two copies AGREED — which was the right test while
    there were two, and became vacuous the moment `leverage` started
    delegating, because two names for one function agree trivially. A test that
    cannot fail is not coverage, so it is replaced rather than left green.

    There were THREE copies of one read (§1.97 F18): `ward_parts`'s crosswalk
    branch, `leverage.load_ward_parts`, and an inline comprehension in
    `export_interactive`. The latter two both hardcoded ``Ward_2026``, so
    neither could read another target, and neither returned a source label.

    Why this matters more than tidiness: `pools._target_roll` and
    `montecarlo.ward_parts` read ONE file by two rules and built two different
    cities — 124 of 135 wards disagreeing (F14, §1.99) — and nothing noticed,
    because the citywide total was identical either way. Copies of a read do
    not announce their divergence.
    """
    import ast
    offenders = []
    for path in sorted((ROOT / "src").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            # The signature of the read: subscripting a row by part_registered.
            if not isinstance(node, ast.Subscript):
                continue
            key = getattr(node.slice, "value", None)
            if key != "part_registered":
                continue
            fn = _enclosing_function(tree, node)
            if (path.name, fn) in {("montecarlo.py", "read_ward_crosswalk"),
                                   ("pools.py", "_target_roll")}:
                continue
            offenders.append(f"{path.name}:{node.lineno} in {fn or '<module>'}")
    assert not offenders, (
        "these read `part_registered` outside the one reader:\n  "
        + "\n  ".join(offenders)
        + "\n\n  `montecarlo.read_ward_crosswalk` is the single crosswalk "
          "reader (§1.97 F18); `pools._target_roll` is the separate, "
          "deliberate roll sum (F14, §1.99). A third site is a second "
          "definition of one rule, and copies of a read do not announce "
          "their divergence — F14 was 124 of 135 wards apart and invisible.")


def _enclosing_function(tree, target):
    """The name of the function containing ``target``, or None."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(node):
                if child is target:
                    return node.name
    return None

def test_pools_and_montecarlo_now_read_one_crosswalk_by_one_rule():
    """FIXED 2026-08-26, and this is the guard that keeps it fixed.

    **What it used to document.** ``montecarlo.ward_parts`` used
    ``part_registered`` — the apportioned split of a voting district across the
    wards it straddles, assumption A1 and the whole reason the column exists —
    while ``pools._target_roll`` read the SAME file, skipped every row after a
    VD's first (``if ... vd in seen: continue``) and summed ``vd_registered``,
    assigning each of the 181 split VDs' ENTIRE roll to whichever ward sorted
    first. The two disagreed for **124 of the 135 wards**, by up to **16,657
    registered voters** in ward 79800008 — close to a whole ward's average roll.

    **Why nothing caught it.** ``sum(part_registered) == vd_registered`` for all
    865 VDs, so the citywide total was identical either way (2,348,781) and
    every conservation check passed under both rules. And ``_target_roll`` is
    reached only when ``CALENDAR[year].results is None``, so all sixteen
    backtest city-years take the other branch: the defect was live at 2026 only,
    in the published forecast, and unscoreable by any backtest.

    **The corroboration that settled it**, beyond A1. Wards are delimited to
    hold roughly equal populations. Under the old rule Johannesburg's ward rolls
    ran 5,902 to 36,649 (CV 30.0%); under the fix they run 14,791 to 20,007
    (CV 11.9%). A 6.2x spread between smallest and largest ward is not something
    a delimitation produces. MODEL-LOG §1.98, F14.

    Asserted here: the two readers agree ward for ward. They must, because there
    is now one rule. If this fails, one of them has been changed alone again.

    Note they still KEY wards differently from the one file — ``ward_parts``
    returns ``Ward_2026`` (``94``), ``_target_roll`` returns ``WardID_2026``
    (``79800094``). That is cosmetic and the mapping is taken from the file.
    """
    try:
        import pools
    except ImportError as exc:
        skip(f"pools is not importable here: {exc}")
    if not hasattr(pools, "_target_roll"):
        skip("pools._target_roll has been renamed; re-point this test")

    rows = real_crosswalk_rows()
    ward_id = {r["Ward_2026"]: r["WardID_2026"] for r in rows}

    with city_target("joburg", "2026") as target:
        parts, _ = M.ward_parts(target, ELECTIONS, target.processed)
        pooled = pools._target_roll(target.city, target)

    apportioned: dict[str, float] = {}
    for _vd, ward, registered in parts:
        apportioned[ward_id[ward]] = apportioned.get(ward_id[ward], 0.0) + registered

    assert set(apportioned) == set(pooled), (
        "the two readers do not agree on the ward set")

    differing = {w: pooled[w] - apportioned[w]
                 for w in apportioned if abs(pooled[w] - apportioned[w]) > 0.5}
    assert not differing, (
        f"pools._target_roll and montecarlo.ward_parts have diverged again on "
        f"{len(differing)} wards, worst "
        f"{max(abs(d) for d in differing.values()):,.0f} voters. One of them has "
        f"stopped honouring part_registered — see MODEL-LOG §1.98 F14 before "
        f"changing this test.")

    # The delimitation argument, held as a property rather than a story: a ward
    # roll that strays this far from the city mean means the apportionment has
    # been lost again, whatever the two readers agree on between themselves.
    vals = sorted(apportioned.values())
    mean = sum(vals) / len(vals)
    assert max(vals) / min(vals) < 2.0, (
        f"ward rolls range {min(vals):,.0f} to {max(vals):,.0f} — a spread no "
        f"delimitation produces; the whole-VD assignment is probably back")
    assert abs(sum(vals) - 2_348_781) < 1.0, (
        f"citywide roll moved to {sum(vals):,.0f}; this fix is a redistribution "
        f"between wards and must never change the total (mean {mean:,.0f})")

def test_montecarlo_cannot_find_the_crosswalk_build_concordance_writes():
    """DEFECT, documented not fixed: producer and consumer use different paths,
    and the resulting error names the wrong cause.

    ``build_concordance.py`` writes ``vd_ward_2026.csv`` into
    ``city.processed`` (build_concordance.py:204 and :210 — the per-city fix from
    MODEL-LOG §1.40). ``ward_parts`` looks for it in ``target.processed``
    (montecarlo.py:776), and for every city except Johannesburg those are
    different directories: ``data/processed/tshwane/`` against
    ``data/processed/tshwane/2026/``. Johannesburg alone is exempt, because
    ``legacy_processed_root`` collapses the two at its default target
    (cityconfig.py:374-378) — so the one city that works is the one that hides
    the defect, which is the same shape as the §1.40 fallback that "was
    reachable only by a city it could only mislead".

    What the user sees is not "the crosswalk is in the wrong place". The
    missing crosswalk drops through to the result-file branch, which asks for a
    2026 result file, which does not exist because the election has not
    happened — so the message is *"2026 has no result file: it has not been
    held"*. That is a true sentence about a fact nobody needed to be told, and
    it names neither the file that was wanted nor the directory it is actually
    sitting in. §1.40's whole lesson was that a missing per-city input must
    refuse by naming the file it wanted.

    This test asserts the defect as it stands today. When the paths are
    reconciled it will fail, and that failure is the notification.
    """
    slug = "tshwane"
    city = cityconfig.load(slug)
    written = ROOT / city.processed / "vd_ward_2026.csv"
    if not written.exists():
        skip(f"{slug} has no 2026 crosswalk on disk at {written}")

    with city_target(slug, "2026") as target:
        looked_for = ROOT / target.processed / "vd_ward_2026.csv"
        assert not looked_for.exists(), (
            "the two paths now coincide for " + slug + "; if the producer and "
            "consumer have been reconciled, delete this test and record it")
        try:
            M.ward_parts(target, ELECTIONS, target.processed)
        except SystemExit as exc:
            message = str(exc)
        else:
            raise AssertionError(
                f"{slug} 2026 now resolves its wards; the path mismatch is "
                f"fixed and this test should be replaced by a positive one")

    assert "no result file" in message, message
    assert "vd_ward_2026.csv" not in message, (
        "the refusal has started naming the crosswalk — good; update this test")


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
