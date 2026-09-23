"""THE SLATES A NOMINATION LIST DECLARES REACH THE CORRECTION THAT IS ABOUT SLATES.

`levels.contestation` read who stood from the target's own RESULT file, so the
certified per-ward lists — pasted into the judgement file on nomination day,
2026-09-16, and read by `pools` for an arrival's reach ever since — never
reached the ward correction. Johannesburg 2026 went on projecting 2021's slates
with `contestation_expand = 0.220` while the real answer sat in the file the
model already opens. The PA's real slate is all 135 wards against a projected
0.520. MODEL-LOG §1.251; predictions in
`prereg/2026-09-23-declared-ward-slates.md`.

**JUDGEMENT-CALLS §A5 promised this behaviour and nothing tested it.** The row
said the lever is "superseded automatically the day the IEC publishes 2026
lists", and `test_levers_are_live` swept it only at 2021, where it is inert by
construction because every backtest has a result file. The promise was untested
at the one target where it applies — the same shape as `pa_contestation_uplift`,
which fired only where nothing could check it (§1.47).

**Every test here builds its own judgement file** (CLAUDE.md §4: a test whose
premise is the state of the tree expires silently). The live tree is asserted
separately, and only for the claim that the hazard is real rather than
hypothetical.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import run_module                                 # noqa: E402

import cityconfig                                               # noqa: E402
import levels                                                   # noqa: E402
import pools                                                    # noqa: E402

CITY = "joburg"
LIVE = "2026"
PAST = "2021"


def _with_roster(body: str, year: str = LIVE):
    """Run with a constructed judgement file in place of the real one."""
    city = cityconfig.use(CITY)
    target = cityconfig.use_target(year)
    original = pools.lineage_path
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"{CITY}-{year}.toml"
        path.write_text(body)
        try:
            pools.lineage_path = lambda c, t: path
            return levels.contestation(target, city), levels.declared_contestation(
                target, city)
        finally:
            pools.lineage_path = original


def test_a_declared_slate_is_counted_over_the_citys_wards_not_the_pasted_ones():
    """The denominator is the city, which is the repair `reach` already needed.

    Counting against the wards the paste happens to mention made a party's
    value a function of how far through the list the typist had got — maximal
    at the first party entered, shrinking as the list grew (POOLS-REEMIT-QUEUE
    entry 23, guard C). One party on 20 of 135 wards is 0.148, never 1.0.
    """
    wards = ", ".join(f'"7980{n:04d}"' for n in range(1, 21))
    slates, _ = _with_roster(
        '[roster]\nparties = ["ANC", "DA"]\n'
        f'[roster.wards]\n"AFRICAN NATIONAL CONGRESS" = [{wards}]\n')
    assert slates["ANC"] == 20 / 135, (
        f"ANC declared on 20 wards scored {slates['ANC']}, not 20/135. A "
        f"denominator of the pasted set makes the first party entered look "
        f"city-wide whatever it declared.")


def test_an_incomplete_list_never_zeroes_a_party_it_does_not_mention():
    """`complete = false` means half-typed, so absence is UNKNOWN, not zero.

    The drop branch deletes 2.4-2.9% of a city's vote across 16-20 parties when
    it fires on an incomplete list (§1.175). A partial paste must fail safe.
    """
    wards = ", ".join(f'"7980{n:04d}"' for n in range(1, 21))
    slates, (_declared, complete) = _with_roster(
        '[roster]\nparties = ["ANC", "DA"]\ncomplete = false\n'
        f'[roster.wards]\n"AFRICAN NATIONAL CONGRESS" = [{wards}]\n')
    assert complete is False
    assert "DA" not in slates, (
        f"DA was given a slate of {slates.get('DA')} from a list that does not "
        f"claim to be the whole ballot. Absence from a half-typed list is not "
        f"evidence that a party fields no ward candidates.")


def test_a_complete_list_zeroes_a_party_that_filed_no_ward_candidates():
    """Under `complete = true`, zero is the truth and not an absence.

    Johannesburg 2026 has two such parties, CHANGE and PRO SOUTH AFRICA: on the
    ballot, PR lists only. A party with no ward candidates cannot win a ward.
    """
    wards = ", ".join(f'"7980{n:04d}"' for n in range(1, 136))
    slates, (_declared, complete) = _with_roster(
        '[roster]\nparties = ["ANC", "DA"]\ncomplete = true\n'
        f'[roster.wards]\n"AFRICAN NATIONAL CONGRESS" = [{wards}]\n')
    assert complete is True
    assert slates["ANC"] == 1.0
    assert slates["DA"] == 0.0, (
        f"DA is on a roster that declares itself the WHOLE ballot and is in no "
        f"ward list, so it filed no ward candidates — it scored "
        f"{slates.get('DA')} rather than 0.0.")


def test_a_past_target_still_reads_its_result_file_and_ignores_any_declaration():
    """P1 of the pre-registration: the panel may not move.

    A declaration is only ever consulted where the result file does not exist.
    A backtest that could be steered by a judgement file would make every
    measured score a function of a hand-typed table.
    """
    wards = ", ".join(f'"7980{n:04d}"' for n in range(1, 21))
    slates, _ = _with_roster(
        '[roster]\nparties = ["ANC"]\ncomplete = true\n'
        f'[roster.wards]\n"AFRICAN NATIONAL CONGRESS" = [{wards}]\n', year=PAST)
    assert slates["ANC"] == 1.0, (
        f"the 2021 ANC slate came back as {slates['ANC']}. 2021's result file "
        f"says it stood in every ward, so a declaration reached a backtest.")
    assert len(slates) > 40, (
        f"2021 returned {len(slates)} parties; the result file carries far "
        f"more, so the declared path was taken at a target that has one.")


def test_the_live_tree_really_does_declare_its_ward_slates():
    """The hazard is live, not hypothetical — the one claim about the tree.

    Without this, every test above guards an interaction nobody would meet.
    """
    city = cityconfig.use(CITY)
    target = cityconfig.use_target(LIVE)
    assert not levels.has_result_file(target, city), (
        "Johannesburg 2026 has a result file, so this suite is being run after "
        "the election and these tests need re-reading, not re-running.")
    slates, complete = levels.declared_contestation(target, city)
    assert complete and len(slates) > 50, (
        f"the live judgement file declares {len(slates)} slates, complete="
        f"{complete}. The certified list was pasted on 2026-09-16.")
    assert slates["PA"] == 1.0, (
        f"the PA's declared slate is {slates['PA']}. The certified list puts "
        f"it on all 135 wards, against 0.385 in 2021 — which is the whole "
        f"reason this path exists.")


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
