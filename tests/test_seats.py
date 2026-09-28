"""The statutory seat allocator must reproduce the IEC's published council.

``src/seats.py`` implements Municipal Structures Act Schedule 1:

    Q = (A / (B - C - D)) + 1, disregarding fractions

with the undistributed remainder allocated by largest remainder. It is the one
component of this model that has an objectively correct answer, published by
the IEC for every municipality and every election, in the "Seat Calculation
Detail" spreadsheet that ``src/official_seats.py`` reads.

This test takes the raw VD-level result files, adds up the ward and PR ballots,
runs them through ``seats.allocate``, and demands that the outcome equals the
published council **exactly**: the quota, the total valid votes A, the council
size, every party's seat count, and -- just as important -- that no party the
IEC left on zero is given a seat.

Nothing here is typed from memory. The expected values are parsed out of the
IEC's own file, and the city-years are discovered from what is on disk, so
adding a metro's data automatically extends the test rather than silently
leaving it untested. Where one side of the pair is missing (votes without a
report, or a report without votes) the test skips with the reason rather than
asserting something weaker.

One thing the archive cannot check: **C and D are zero in every city-year on
disk.** Johannesburg and Tshwane have never had an independent win a ward, nor
a party win one without a PR list, so the published councils exercise the
formula only in its ``C = D = 0`` form -- an allocator that ignored the two
deductions entirely would reproduce all six. The deductions therefore get a
constructed municipality of their own, further down, where both are non-zero
and the two rules give different councils.

Run:
    ./.venv/bin/python tests/test_seats.py
    ./.venv/bin/python -m pytest tests/test_seats.py -q
"""

from __future__ import annotations

import csv
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, skip  # noqa: E402

import official_seats  # noqa: E402
from seats import (INDEPENDENT, allocate, eligible_parties,  # noqa: E402
                   outside_pool_wards, overhang, pr_seats)

ELECTIONS = ROOT / "data" / "raw" / "elections"
REPORTS = ELECTIONS / "_reports"

CLEAN_RE = re.compile(r"^lge(\d{4})_([A-Z]{3})_vd_party_clean\.csv$")
REPORT_RE = re.compile(r"^lge(\d{4})_([A-Z]{3})_seat_calculation_detail\.xls$")


# --------------------------------------------------------------------------
# discovery
# --------------------------------------------------------------------------

def discover() -> list[tuple[str, int, bool, bool]]:
    """Return (code, year, has_votes, has_official) for every city-year seen."""
    votes: set[tuple[str, int]] = set()
    for path in sorted(ELECTIONS.glob("lge*_vd_party_clean.csv")):
        match = CLEAN_RE.match(path.name)
        if match:
            votes.add((match.group(2), int(match.group(1))))

    official: set[tuple[str, int]] = set()
    if REPORTS.is_dir():
        for path in sorted(REPORTS.glob("lge*_seat_calculation_detail.xls")):
            match = REPORT_RE.match(path.name)
            if match:
                official.add((match.group(2), int(match.group(1))))

    return [
        (code, year, (code, year) in votes, (code, year) in official)
        for code, year in sorted(votes | official, key=lambda pair: (pair[0], pair[1]))
    ]


# --------------------------------------------------------------------------
# the raw result file -> votes by party (independent of the rest of src/)
# --------------------------------------------------------------------------

def load_votes(path: Path) -> tuple[dict[str, int], dict[str, int]]:
    """Return (ward votes, PR votes) by party from a cleaned LGE result file."""
    ward: Counter[str] = Counter()
    pr: Counter[str] = Counter()
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            bucket = ward if row["BallotType"].upper() == "WARD" else pr
            bucket[row["sPartyName"]] += int(row["Party_Votes"])
    return dict(ward), dict(pr)


def ward_winners(path: Path) -> Counter[str]:
    """Ward wins by party: the top party on the ward ballot in each ward."""
    totals: dict[str, Counter[str]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["BallotType"].upper() != "WARD":
                continue
            totals.setdefault(row["Ward"], Counter())[row["sPartyName"]] += int(
                row["Party_Votes"]
            )
    return Counter(party.most_common(1)[0][0] for party in totals.values())


# --------------------------------------------------------------------------
# the check
# --------------------------------------------------------------------------

def check_city_year(code: str, year: int, has_votes: bool, has_official: bool) -> None:
    if not has_votes:
        skip(f"no {ELECTIONS.name}/lge{year}_{code}_vd_party_clean.csv on disk — "
             f"the IEC publishes the council for {code} {year} but the VD-level "
             f"votes to reproduce it from have not been ingested")
    if not has_official:
        skip(f"no Seat Calculation Detail for {code} {year} on disk — fetch it "
             f"with: python src/fetch_iec.py --muni {code} --province <PROV>. "
             f"Without it there is no ground truth and the allocator must not "
             f"be checked against a weaker substitute")

    official = official_seats.read(code, year, reports=REPORTS)
    assert official is not None, f"{code} {year}: official_seats.read returned None"
    for key in ("quota", "A", "seats"):
        assert key in official, (
            f"{code} {year}: the seat calculation detail parsed without a "
            f"{key!r} — the IEC's layout changed and official_seats.LABELS no "
            f"longer matches it")
    assert official["parties"], f"{code} {year}: no party rows parsed from the report"

    path = ELECTIONS / f"lge{year}_{code}_vd_party_clean.csv"
    ward, pr = load_votes(path)
    # The same eligibility rule fold.py applies before allocating (fold.py:630):
    # independents and parties with no PR list are excluded from the pool and
    # accounted for through C and D instead.
    combined = eligible_parties(ward, pr)
    wins = ward_winners(path)
    inferred_independent_wards = wins.get(INDEPENDENT, 0)
    no_pr_list_wards = sum(
        count for party, count in wins.items()
        if party not in combined and party != INDEPENDENT
    )

    # C IS READ FROM THE IEC, NOT INFERRED. It cannot be inferred: the IEC
    # merges every independent candidate in a voting district into ONE row
    # named "INDEPENDENT", with no candidate column anywhere in the published
    # data, so a ward with several independents shows their SUM. Buffalo City
    # ward 29200044 reads INDEPENDENT 1,899 against the ANC's 1,714 while the
    # IEC records C = 0 for that municipality: several stood, the largest
    # polled under 1,714, the ANC won the ward. The bloc total is an upper
    # bound on any single candidate and nothing in the data narrows it.
    #
    # So this test asks the question that CAN be answered — does the allocator
    # reproduce Schedule 1 given the correct inputs — and the inferred figure
    # is checked below as the bound it is, rather than as an answer.
    # See DATA-QUALITY.md item 12 and MODEL-LOG O13.
    independent_wards = official.get("independents", inferred_independent_wards)

    result = allocate(
        combined,
        total_seats=official["seats"],
        independent_wards=independent_wards,
        no_pr_list_wards=no_pr_list_wards,
    )

    # --- A, the quota, and the size of the council ------------------------
    # The 2011 layout omits the valid-vote total, so official_seats derives it
    # by summing the party rows (official_seats.py:78) and flags that. Saying
    # "the IEC published" of a figure we computed ourselves would send anyone
    # chasing a mismatch to the wrong side of the comparison.
    a_source = (f"summed from the report's own party rows, because the {year} "
                f"layout does not publish it"
                if official.get("A_derived") else "as published by the IEC")
    assert result.total_votes == official["A"], (
        f"{code} {year}: A (total valid votes over eligible parties) is "
        f"{result.total_votes:,}, the report gives {official['A']:,} "
        f"({a_source}) — the eligibility rule or the vote file disagrees with "
        f"the pool the quota was computed over")
    assert result.quota == official["quota"], (
        f"{code} {year}: quota is {result.quota:,}, the IEC published "
        f"{official['quota']:,}")

    # C and D, against the report's own figures. (Asserting instead that
    # allocated + C + D == official["seats"] would be untestable: allocate is
    # handed total_seats=official["seats"] and always distributes exactly
    # total_seats - C - D, so that identity holds whatever C and D are.)
    if "independents" in official:
        # Merging can only ever ADD apparent wins, never remove them, so the
        # inferred count is an upper bound. If it ever comes out BELOW the
        # published C the explanation above is wrong and this stops being a
        # data limit and becomes a bug.
        assert inferred_independent_wards >= official["independents"], (
            f"{code} {year}: inferred {inferred_independent_wards} independent "
            f"ward win(s) but the IEC published C = {official['independents']}. "
            f"Merged independents can only inflate the count, so a figure "
            f"below the published one means the ward-winner rule is wrong "
            f"rather than merely imprecise.")
    if "no_list" in official:
        assert no_pr_list_wards == official["no_list"], (
            f"{code} {year}: counted {no_pr_list_wards} ward(s) won by a party "
            f"with no PR list, the IEC published D = {official['no_list']}. "
            f"Same consequence as C: the quota is struck over "
            f"{official['seats']} - C - D seats, not {official['seats']}.")
        published_party_seats = sum(p["seats"] for p in official["parties"].values())
        assert (published_party_seats + official.get("independents", 0)
                + official["no_list"] == official["seats"]), (
            f"{code} {year}: the report's own party rows sum to "
            f"{published_party_seats} seats, which with C "
            f"{official.get('independents', 0)} and D {official['no_list']} "
            f"does not make the published council of {official['seats']}. The "
            f"party table has been parsed wrongly (a missing or duplicated "
            f"row), so the per-party comparison below is against a table that "
            f"is not the council.")

    # --- every party, including the ones the IEC left on zero -------------
    wrong = []
    for name, want in sorted(official["parties"].items()):
        got = result.seats.get(name, 0)
        if got != want["seats"]:
            wrong.append(f"{name}: expected {want['seats']}, got {got} "
                         f"(votes published {want['votes']:,}, "
                         f"counted {combined.get(name, 0):,})")
    # a party the report does not list at all must not be handed a seat
    phantom = {party: count for party, count in result.seats.items()
               if count > 0 and party not in official["parties"]}
    assert not wrong, (
        f"{code} {year}: {len(wrong)} party seat mismatch(es) against the "
        f"published council:\n  " + "\n  ".join(wrong))
    assert not phantom, (
        f"{code} {year}: seats awarded to parties absent from the published "
        f"table: {phantom}")


# --------------------------------------------------------------------------
# the C/D exclusion path, which no real city-year on disk exercises
# --------------------------------------------------------------------------
#
# Every JHB and TSH year in the archive has C = D = 0: no independent has ever
# won a Johannesburg or Tshwane ward, and no party has won one without
# registering a PR list. The comparisons above therefore say nothing about the
# deductions -- deleting the ``- independent_wards - no_pr_list_wards`` from
# seats.allocate leaves all six passing. (The IEC's own reports show the case
# is real elsewhere: eThekwini published C = 1 in 2011 and C = 4 in 2016. The
# moment those VD files are ingested the tests above start exercising it, and
# then they must not be the first place it is ever checked.)
#
# So the rule gets a constructed municipality instead, small enough that every
# figure below can be checked by hand against Schedule 1:
#
#   A = 18,000 over three parties with PR lists; B = 10 seats;
#   C = 1 (an independent wins ward 3); D = 1 (NOLIST wins ward 4 with no list)
#   Q = 18,000 / (10 - 1 - 1) + 1 = 2,251        <- with the deductions
#   Q = 18,000 / 10 + 1          = 1,801        <- if they were ignored
#
# and the two quotas produce different councils, so an allocator that dropped
# the deductions fails on the seats as well as on the quota.

CONSTRUCTED_ROWS = [
    # BallotType, Ward, sPartyName, Party_Votes
    ("WARD", "1", "BIG", 3000), ("WARD", "1", "MID", 1000),
    ("WARD", "2", "BIG", 2000), ("WARD", "2", "MID", 1500),
    ("WARD", "3", "INDEPENDENT", 900),
    ("WARD", "3", "BIG", 400), ("WARD", "3", "MID", 200),
    ("WARD", "4", "NOLIST", 700),
    ("WARD", "4", "BIG", 300), ("WARD", "4", "MID", 100),
    ("PR", "1", "BIG", 4300), ("PR", "1", "MID", 2200), ("PR", "1", "SMALL", 3000),
]


def write_constructed(directory: Path) -> Path:
    path = directory / "constructed_vd_party_clean.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["BallotType", "Ward", "sPartyName", "Party_Votes"])
        writer.writerows(CONSTRUCTED_ROWS)
    return path


def constructed_case() -> tuple[dict[str, int], int, int]:
    """(combined votes, C, D) derived the same way ``check_city_year`` derives them."""
    with tempfile.TemporaryDirectory(prefix="seats-constructed-") as tmp:
        path = write_constructed(Path(tmp))
        ward, pr = load_votes(path)
        combined = eligible_parties(ward, pr)
        wins = ward_winners(path)
    independent_wards = wins.get(INDEPENDENT, 0)
    no_pr_list_wards = sum(
        count for party, count in wins.items()
        if party not in combined and party != INDEPENDENT
    )
    return combined, independent_wards, no_pr_list_wards


def test_an_independent_never_takes_a_pr_vote_in_any_file_we_hold():
    """An independent contests a WARD. It gets the ward or it gets nothing.

    It cannot appear on the proportional ballot, so it takes no part in the
    quota pool — which is why ``eligible_parties`` requires ``pr_votes > 0``
    rather than naming independents specially. That is the statute, and this
    checks the data agrees with it across every city-year on disk, because
    the rule is enforced by a condition that would silently stop working if a
    file ever carried a PR line for one.

    It also documents the limit that stops two councils being reproduced: the
    IEC merges every independent in a voting district into ONE row, so the
    ward-ballot side of this cannot be attributed to a candidate at all. See
    MODEL-LOG O13.
    """
    offenders = []
    checked = 0
    for code, year, has_votes, _official in CITY_YEARS:
        if not has_votes:
            continue
        path = ELECTIONS / f"lge{year}_{code}_vd_party_clean.csv"
        ward, pr = load_votes(path)
        checked += 1
        for name, votes in pr.items():
            if name.strip().upper() in ("INDEPENDENT", "INDEPENDENTS", "IND") and votes:
                offenders.append(f"{code} {year}: {name!r} holds {votes:,} PR votes")
        combined = eligible_parties(ward, pr)
        for name in combined:
            if name.strip().upper() in ("INDEPENDENT", "INDEPENDENTS", "IND"):
                offenders.append(f"{code} {year}: {name!r} entered the quota pool")
    assert checked, "no city-year had votes on disk; this test checked nothing"
    assert not offenders, (
        "independents are contesting the proportional ballot, or reaching the "
        "pool the quota is struck over:\n  " + "\n  ".join(offenders))


def test_constructed_eligibility_excludes_independents_and_listless_parties():
    combined, independent_wards, no_pr_list_wards = constructed_case()
    assert combined == {"BIG": 10000, "MID": 5000, "SMALL": 3000}, (
        f"eligible_parties admitted the wrong pool: {combined}. INDEPENDENT "
        f"must be excluded by name and NOLIST for having no PR list; SMALL has "
        f"no ward votes at all but a PR list, and must be kept.")
    assert independent_wards == 1, (
        f"C is {independent_wards}, should be 1 — the independent wins ward 3 "
        f"on 900 votes against BIG's 400")
    assert no_pr_list_wards == 1, (
        f"D is {no_pr_list_wards}, should be 1 — NOLIST wins ward 4 on 700 "
        f"votes and has no PR list, so its seat comes out through D")


def test_constructed_quota_is_struck_over_seats_less_C_and_D():
    """Schedule 1's Q = (A / (B - C - D)) + 1, with C and D actually non-zero."""
    combined, independent_wards, no_pr_list_wards = constructed_case()
    result = allocate(combined, total_seats=10,
                      independent_wards=independent_wards,
                      no_pr_list_wards=no_pr_list_wards)
    ignoring = allocate(combined, total_seats=10)

    assert result.total_votes == 18000, f"A is {result.total_votes}, should be 18,000"
    assert result.seats_available == 8, (
        f"B - C - D is {result.seats_available}, should be 10 - 1 - 1 = 8")
    assert result.quota == 2251, (
        f"quota is {result.quota:,}, Schedule 1 gives 18,000 / 8 + 1 = 2,251. "
        f"Ignoring the C and D deductions would give {ignoring.quota:,}.")
    assert ignoring.quota == 1801, (
        f"the no-deduction control quota is {ignoring.quota:,}, should be "
        f"18,000 / 10 + 1 = 1,801; the constructed case no longer separates "
        f"the two code paths")
    assert result.seats == {"BIG": 5, "MID": 2, "SMALL": 1}, (
        f"seats are {result.seats}, should be BIG 5, MID 2, SMALL 1 "
        f"(4 + 2 + 1 on the quota, BIG taking the one remainder seat on "
        f"0.443 against MID's 0.221 and SMALL's 0.333)")
    assert sum(result.seats.values()) == 8, (
        f"{sum(result.seats.values())} list-pool seats allocated, should be 8; "
        f"the other two are the independent's ward and NOLIST's ward")
    assert ignoring.seats == {"BIG": 5, "MID": 3, "SMALL": 2}, (
        f"the no-deduction control allocates {ignoring.seats}, should be "
        f"BIG 5, MID 3, SMALL 2 — if this ever equals the deducted answer the "
        f"test above can no longer tell the two rules apart")


# --------------------------------------------------------------------------
# outside_pool_wards, and the council it feeds — a second constructed case
# --------------------------------------------------------------------------
#
# The case above derives C and D INLINE, so it never calls
# `seats.outside_pool_wards` — the function every production caller
# (`montecarlo`, `benchmarks`, `reader_seats`) uses to split ward wins into C, D
# and the wins that stay in the pool. The mutation pilot
# (audits/2026-09-29-mutation/runs/pilot/report.md, `src/seats.py`) found that
# inverting its last line to `if p in outside` moved `seat_draws`,
# `excessive_draws` and `over_draws` while every test stayed green. It also
# found `in`/`not in` swaps on the C and D sums that no test executed, and the
# C = D = 1 case above could not have told them apart anyway. So this council
# has C != D, spells its independent "IND" (the merged-row alias the result
# files use), and gives a pool party wards equal to and above its entitlement.
#
#   B = 12 seats. Combined (ward + PR) votes of the list parties:
#       BIG 10,000   MID 5,000   SMALL 3,200            A = 18,200
#   Wards won:
#       IND 2 (independent: out through C)
#       NOLIST 1 (contested a ward, registered no PR list: out through D)
#       SMALL 3   MID 2   BIG 0
#   (Eight wards on twelve seats is not a real metro's ratio; nothing in the
#   arithmetic below depends on it.)
#
#   C = 2, D = 1, so B - C - D = 9 seats in the pool.
#   Q = 18,200 // 9 + 1 = 2,022 + 1 = 2,023           (9 x 2,022 = 18,198)
#   floors: BIG 10,000 // 2,023 = 4 (8,092, remainder 1,908 -> .943)
#           MID  5,000 // 2,023 = 2 (4,046, remainder   954 -> .472)
#           SMALL 3,200 // 2,023 = 1 (2,023, remainder 1,177 -> .582)
#   7 by quota, 2 by largest remainder: BIG (.943), SMALL (.582).
#   Entitlement: BIG 5, MID 2, SMALL 2  (sums to 9).
#
#   Ward/PR split (`pr_seats`, entitlement less POOL wins):
#       BIG 5 - 0 = 5,  MID 2 - 2 = 0,  SMALL 2 - 3 = -1
#   `overhang` (wins strictly above entitlement): SMALL by 1.
#
#   Item 16 as amended by Act 3/2021 (`allocate_with_overhang(rule="deduct")`,
#   the statutory rule; derivation as in tests/test_overhang.py): a party whose
#   wards are EQUAL TO OR GREATER than its entitlement keeps its wards and gets
#   no list seats. SMALL (3 >= 2) and MID (2 >= 2) are both fixed. The quota is
#   re-struck for the rest over the seats left:
#       (18,200 - 3,200 - 5,000) // (12 - 3 - 2 - 2 - 1) + 1
#       = 10,000 // 4 + 1 = 2,501
#       BIG 10,000 // 2,501 = 3 (7,503), 4 - 3 = 1 seat by remainder -> BIG 4
#   Council: BIG 4 + MID 2 + SMALL 3 + C 2 + D 1 = 12, and stays 12.

POOL_COMBINED = {"BIG": 10000, "MID": 5000, "SMALL": 3200}
POOL_WARD_WINS = {"IND": 2, "NOLIST": 1, "SMALL": 3, "MID": 2}
POOL_COUNCIL = 12


def test_outside_pool_wards_splits_C_D_and_the_pool_on_a_constructed_council():
    """C, D and the pool wins, each counted from a council where C != D."""
    c, d, pool = outside_pool_wards(dict(POOL_WARD_WINS), dict(POOL_COMBINED))
    assert c == 2, (
        f"C is {c}, should be 2 — the two wards the independent (row name "
        f"'IND', the IEC's merged alias) won")
    assert d == 1, (
        f"D is {d}, should be 1 — NOLIST won a ward and is not in the combined "
        f"pool because it registered no PR list")
    assert pool == {"SMALL": 3, "MID": 2}, (
        f"pool wins are {pool}, should be SMALL 3, MID 2 — every ward won by a "
        f"party that stays in the quota pool, and nothing that left through C "
        f"or D")


def test_the_constructed_council_splits_ward_and_list_seats_as_schedule_1_requires():
    """Entitlement, then the ward/list split, over `outside_pool_wards`' pool."""
    c, d, pool = outside_pool_wards(dict(POOL_WARD_WINS), dict(POOL_COMBINED))
    result = allocate(dict(POOL_COMBINED), total_seats=POOL_COUNCIL,
                      independent_wards=c, no_pr_list_wards=d)
    assert result.total_votes == 18200, f"A is {result.total_votes}, should be 18,200"
    assert result.seats_available == 9, (
        f"B - C - D is {result.seats_available}, should be 12 - 2 - 1 = 9")
    assert result.quota == 2023, (
        f"quota is {result.quota:,}, should be 18,200 // 9 + 1 = 2,023")
    assert result.seats == {"BIG": 5, "MID": 2, "SMALL": 2}, (
        f"entitlement is {result.seats}, should be BIG 5, MID 2, SMALL 2 "
        f"(4 + 2 + 1 on the quota; BIG .943 and SMALL .582 take the two "
        f"remainder seats over MID's .472)")
    # `top` sorts stably on seat count, so MID (first in `combined`) precedes
    # SMALL on the 2-2 tie.
    assert result.top(2) == [("BIG", 5), ("MID", 2)], (
        f"top(2) is {result.top(2)}; should be exactly BIG 5 then MID 2")

    split = pr_seats(result, pool)
    assert split == {"BIG": 5, "MID": 0, "SMALL": -1}, (
        f"list seats are {split}, should be BIG 5 - 0 = 5, MID 2 - 2 = 0, "
        f"SMALL 2 - 3 = -1. Any IND or NOLIST key means the C/D wards were "
        f"charged against the pool")
    assert overhang(result, pool) == {"SMALL": 1}, (
        f"overhang is {overhang(result, pool)}, should be SMALL by 1 only — "
        f"MID holds exactly its entitlement, which is not an excess")


def test_the_constructed_council_under_item_16_is_the_statutory_one():
    """The whole chain production runs per draw, on the statutory `deduct` rule.

    `eligible_parties` -> `outside_pool_wards` -> `allocate_with_overhang`, as
    `montecarlo.run_model` calls them. Expected values are the long division in
    the block comment above, not model output.

    Under the pilot's line-102 mutant (`if p in outside`), the pool wins become
    {IND: 2, NOLIST: 1}. Neither is in `combined`, so `allocate_with_overhang`'s
    ghost-winner guard raises ValueError before any seat is computed: the kill
    in THIS test is that exception. The value kill is in the two tests above.
    """
    import montecarlo as M
    from test_overhang import council_of

    c, d, pool = outside_pool_wards(dict(POOL_WARD_WINS), dict(POOL_COMBINED))
    with council_of(POOL_COUNCIL):
        seats, council, threshold, over = M.allocate_with_overhang(
            dict(POOL_COMBINED), pool, "deduct",
            independent_wards=c, no_pr_list_wards=d)
    assert seats == {"BIG": 4, "MID": 2, "SMALL": 3}, (
        f"seats are {seats}, should be BIG 4, MID 2, SMALL 3: SMALL and MID "
        f"keep their wards (3 >= 2, 2 >= 2) and BIG takes the re-struck pool, "
        f"10,000 // 4 + 1 = 2,501 -> 3 + 1 by remainder")
    assert "IND" not in seats and "NOLIST" not in seats, (
        f"a party that left through C or D was seated from the pool: {seats}")
    assert sum(seats.values()) + c + d == POOL_COUNCIL == council, (
        f"{sum(seats.values())} pool seats + C {c} + D {d} != council "
        f"{council} (should be {POOL_COUNCIL}; `deduct` never grows it)")
    assert threshold == 7, f"majority threshold is {threshold}, should be 12 // 2 + 1"
    assert over == {"MID": 0, "SMALL": 1}, (
        f"item-16 parties are {over}, should be MID (excess 0, fixed on the "
        f"'equal to' limb) and SMALL (excess 1)")


def test_allocate_defaults_to_the_270_seat_council():
    """`total_seats` defaults to Johannesburg's 270.

    Production always passes `total_seats` (montecarlo passes `COUNCIL`), so no
    forecast relies on this default; this pins it so a changed default is seen,
    rather than surviving as the pilot's `270 -> 271` mutant did.
    """
    plain = allocate({"A": 200000, "B": 100000})
    assert plain.seats_available == 270, plain.seats_available
    assert sum(plain.seats.values()) == 270
    deducted = allocate({"A": 200000, "B": 100000}, independent_wards=2,
                        no_pr_list_wards=1)
    assert deducted.seats_available == 267, (
        f"270 - 2 - 1 should leave 267, got {deducted.seats_available}")


def test_allocate_refuses_a_council_with_no_seats_left_and_fills_one_with_one():
    """The `available <= 0` boundary, from both sides.

    At zero it must raise ValueError with its own message. The mutants the pilot
    left alive (`<=` -> `<`, and dropping the raise) reach `// 0` instead and
    raise ZeroDivisionError, which `except ValueError` does not catch. At one
    seat (`<= 0` -> `<= 1` would refuse it) the seat must go to the larger
    remainder: Q = 15 // 1 + 1 = 16, floors 0 and 0, A .625 beats B .3125.
    """
    try:
        allocate({"A": 10}, total_seats=3, independent_wards=2,
                 no_pr_list_wards=1)
    except ValueError as exc:
        assert "no seats left to allocate (0)" in str(exc), str(exc)
    else:
        raise AssertionError("allocate accepted a council with 3 - 2 - 1 = 0 "
                             "seats left")

    one = allocate({"A": 10, "B": 5}, total_seats=3, independent_wards=1,
                   no_pr_list_wards=1)
    assert one.seats_available == 1 and one.quota == 16, (one.seats_available,
                                                          one.quota)
    assert one.seats == {"A": 1, "B": 0}, one.seats


def test_allocate_fills_a_shortfall_equal_to_the_party_count_and_refuses_more():
    """The largest-remainder guard at `shortfall > len(ranked)`, both sides.

    EQUAL: votes A 3, B 2 over 4 seats. Q = 5 // 4 + 1 = 2; floors A 1, B 1;
    shortfall 2 == 2 parties, so each gets one more: A 2, B 2. The pilot's
    `>` -> `>=` mutant refuses this.
    MORE: votes A 1, B 1 over 5 seats. Q = 2 // 5 + 1 = 1; floors 1 + 1;
    shortfall 3 > 2 parties, which largest remainder cannot fill.
    """
    equal = allocate({"A": 3, "B": 2}, total_seats=4)
    assert equal.quota == 2 and equal.round_one == {"A": 1, "B": 1}, (
        equal.quota, equal.round_one)
    assert equal.seats == {"A": 2, "B": 2}, equal.seats

    try:
        allocate({"A": 1, "B": 1}, total_seats=5)
    except ValueError as exc:
        assert "shortfall 3 exceeds party count 2" in str(exc), str(exc)
    else:
        raise AssertionError("allocate handed out 5 seats to 2 one-vote parties "
                             "with a shortfall it cannot fill")


def _make(code: str, year: int, has_votes: bool, has_official: bool):
    def test():
        check_city_year(code, year, has_votes, has_official)

    test.__name__ = f"test_official_council_{code}_{year}"
    test.__doc__ = f"{code} {year}: allocator reproduces the published council."
    return test


CITY_YEARS = discover()
for _code, _year, _votes, _official in CITY_YEARS:
    _test = _make(_code, _year, _votes, _official)
    globals()[_test.__name__] = _test


def test_at_least_one_city_year_is_checkable():
    """The suite is worthless if discovery silently finds nothing."""
    checkable = [(c, y) for c, y, v, o in CITY_YEARS if v and o]
    assert checkable, (
        f"no city-year has both cleaned VD results and an IEC Seat Calculation "
        f"Detail on disk (looked in {ELECTIONS} and {REPORTS}); the allocator "
        f"is therefore untested, which is the situation this file exists to "
        f"prevent")


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
