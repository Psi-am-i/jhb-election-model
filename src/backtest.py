"""Score the forecast model against an election that has already happened.

``fold.py`` validates the deterministic core -- the share model, γ, the ballot
split and the seat allocator. What it cannot touch is the *distributional*
layer, which is where every judgement in this project lives: pool
ranges, the Dirichlet concentrations, the splinter branch, entrant geography,
turnout uncertainty, the by-election terms. This harness runs the model at a
past election and scores the distribution it produced against what actually
happened::

    python src/backtest.py --target 2021
    python src/backtest.py --target 2016 --config scenarios/joburg-pools.json
    python src/backtest.py --target 2011 --a scenarios/old.json --b scenarios/new.json

**It runs the model itself.** ``montecarlo.run_model`` is called with a
:class:`cityconfig.Target` for the past year; there is no second implementation
here. Until 2026-08-10 there was one -- a ``run_one`` that reproduced about
two-thirds of the model -- and the numbers it produced were quietly the scores
of a different, simpler forecaster: no per-draw turnout variation, no turnout
tilts, no ward noise (its ward winners were a bare argmax, deterministic given
a draw, which is the defect a 2026-08-05 audit had already fixed in the live
model), no PA contestation uplift, no poll term, no γ_recent fallback, no
by-election path at all despite a docstring that said contests were date
filtered, and every split voting district assigned whole to one ward. This file
now assembles a target, calls the one model, and compares.

**What "honest" means here, enforced by where the model reads from.** For a
past target ``run_model`` resolves every input off the target: the baseline is
the NPE before it, ratios and by-election geography come from the LGE before
it, γ from a fold that finished before it, turnout from ``turnout.py --target
<year>``, and the council is the one that city had in that year. Boundaries and
the roll come from the target's own result file, which is legitimate -- both
are published months ahead -- and the votes in that file are used only for
scoring. Two things a past target does not get, both gaps in the record rather
than omissions: by-election evidence (only the post-2021 window is scraped) and
split-VD apportionment (see ``montecarlo.ward_parts``).

**The priors have read the answer, and the harness says so.** ``DEFAULTS``
was fitted on these very elections — the pool ratios on "sixteen observed
transitions" that include 2019→2021, ``individual_theta`` on the fold-1 and
fold-2 raw ratios, ``alpha_da`` on the ActionSA outcome, the ward/PR ratios and
the PA uplift on 2021 — so a default run against 2021 is an in-sample fit
statistic wearing a forecast's clothes. Every run therefore prints an IN-SAMPLE
banner naming the constants implicated for that target (see :data:`FITTED_ON`),
and it prints by default, because a caveat that lives only in a docstring is a
caveat nobody reads next to the number.

A scenario file can declare itself clean with a top-level ``"derived_from"``:
the list of elections its numbers were fitted on. Any entry at or after the
target and the run refuses. Entries all before it and the banner is downgraded
to a one-line note — for the keys that file actually sets. Everything it leaves
alone still comes from ``DEFAULTS`` and is still called out, because inheriting
a 2021-fitted constant is no less circular for being inherited. The declaration
is the author's word: nothing here can verify it, and it is not evidence.

**What it reports**, all of it through ``score.py`` so the model and the
``benchmarks.py`` baselines are scored by identical code: per-party CRPS, the
PIT histogram, coverage at 50/80/90, the energy and variogram scores on the
joint seat vector, and -- the highest-power test available -- the ward-winner
Brier score with its reliability table, ~135 genuine events per target.
"""

from __future__ import annotations

import argparse
import copy
import csv
from collections import Counter, defaultdict
from collections.abc import Mapping
from pathlib import Path

import cityconfig
import montecarlo as M
import official_seats
import parties as P
import score as S
from fold import citywide, load
from seats import allocate, eligible_parties

def runnable_targets(city=None) -> tuple[str, ...]:
    """Past local elections this harness can actually run, for one city.

    "An LGE with a result file" is not the test, and advertising that set as
    ``--target``'s choices offered 2000 and 2006, both of which die on the
    first thing they touch: no ``[structure.by_year.2006]`` in the city config
    (so no council size), and no ``montecarlo.GAMMA_FOLD`` entry (so no γ).
    A CLI that offers a value it cannot run is a bug report waiting to be
    filed, so the set is *derived* from what each requirement can supply:

    * an LGE, strictly in the past, with a VD-level result file;
    * a previous LGE and a previous NPE, both with result files, because the
      baseline, the ward/PR ratios and the ward geography come from them;
    * a council size for that year in ``cities/<slug>.toml``;
    * a γ fold that finished strictly before it.

    It is per city because the answers are: Johannesburg's councils were
    260/270/270 where Tshwane's were 210/214/214, and a city whose archive
    starts later has fewer runnable targets. Files on disk are deliberately not
    checked here — a missing file is a loud error with a fetch command
    attached, not a reason to hide a target from ``--help``.
    """
    city = city or cityconfig.active()
    out: list[str] = []
    for year, election in sorted(cityconfig.CALENDAR.items()):
        if election.kind != "LGE" or not election.results:
            continue
        target = cityconfig.Target(city=city, year=year)
        if not target.previous_lge or not target.previous_npe:
            continue
        try:
            target.results(target.previous_lge)
            target.results(target.previous_npe)
            target.council                  # [structure.by_year.<year>]
            M.gamma_fold_for(target)        # a γ fold that precedes it
        except SystemExit:
            continue
        out.append(year)
    return tuple(out)


class _Targets(Mapping):
    """Per-target filenames and council size, resolved from the active city.

    ``backtest`` itself no longer needs a table -- it asks ``cityconfig``. This
    exists because ``benchmarks.py`` imports it for the same filenames, and it
    is derived rather than typed so that the council size is the *right city's*.
    The literal table it replaces carried 260/270/270, which are Johannesburg's
    councils; Tshwane's were 210/214/214, so a Tshwane backtest allocated a
    chamber that never existed. Resolution happens on access because the active
    city is not known at import time -- which is also why ``YEARS`` is a
    property over :func:`runnable_targets` rather than the ``(2011, 2016,
    2021)`` literal it used to be, in a class whose own docstring claimed to be
    derived rather than typed.
    """

    @property
    def YEARS(self) -> tuple[int, ...]:
        return tuple(int(y) for y in runnable_targets())

    def __getitem__(self, year):
        if int(year) not in self.YEARS:
            raise KeyError(year)
        t = cityconfig.Target(city=cityconfig.active(), year=str(int(year)))
        return {
            "base": t.results(t.previous_npe),
            "actual": t.results(t.year),
            "prior_lge": t.results(t.previous_lge),
            "election_day": t.date,
            "council": t.council,
            "gamma_fold": M.gamma_fold_for(t),
        }

    def __iter__(self):
        return iter(self.YEARS)

    def __len__(self):
        return len(self.YEARS)


TARGETS = _Targets()


# ---------------------------------------------------------------------------
# in-sample accounting
# ---------------------------------------------------------------------------

# Which elections each ``montecarlo.DEFAULTS`` constant read, taken from the
# constants' own comments rather than from a fresh judgement -- if a comment
# says a number came from an election, that election is listed here. The years
# are the LGEs whose *results* the number saw, so a target at or before a listed
# year means the prior has read the answer.
#
# Not listed, because they are not fitted on any election's result: the turnout
# dials (A2 judgements), the by-election weights (no evidence exists for a past
# target -- see ``montecarlo.run_model``), ``ward_noise_sd`` and ``level_floor``
# (both audit findings about the machinery, not about a party), the overhang
# rule (law), and γ itself -- ``gamma_fold_for`` already refuses a fold that
# does not finish strictly before the target, which is the one part of this
# problem the code can enforce instead of announce.
FITTED_ON: dict[str, tuple[tuple[str, ...], str]] = {
    "pools": (
        ("2011", "2016", "2021"),
        "pool COMPOSITION comes from Census 2022, which post-dates any target "
        "before 2026. The ratio ranges no longer do — they derive from "
        "transitions strictly before the target. A census is a covariate, not "
        "an outcome: it says who lives in a ward, not how they voted."),
    # The four below were removed from this list on the grounds that
    # src/levels.py measures θ, the ward/PR split and contestation from
    # transitions strictly before the target, so the hand-typed constants are
    # "no longer read". That is true per party and false in general: the
    # measurement covers the parties the record covers, and a party the record
    # cannot reach still falls back to the plan's number. Measured on target
    # 2021, ActionSA — 11% of that baseline, and a party whose ONLY local
    # result is the target — took its 1.50 from theta_mode, and 31 parties
    # took bands from individual_theta. Both went unnamed while the banner
    # discussed pools. So they are listed again, and `montecarlo.note_constant`
    # records which ones a run actually consumed: the banner reports the
    # measurement, and a run that genuinely never touches them still prints
    # the all-clear.
    "theta_mode": (
        ("2006", "2011", "2016", "2021"),
        "the plan's per-party θ views, written with the whole record in "
        "hand. ASA 1.50 is the sharpest case: ActionSA has exactly one local "
        "result and it is the 2021 target"),
    "individual_theta": (
        ("2016", "2021"),
        "the bands say so themselves — \"ranges bracket the observed "
        "fold-1/fold-2 raw ratios: IFP 1.34→1.97, VF+ 0.81→1.65, ACDP "
        "0.58→1.82, Al Jama-ah 3.12 in 2021\""),
    "f_other": (
        ("2006", "2011", "2016", "2021"),
        "the residual bucket's triangular, a judgement made against the same "
        "record; the measured retention it replaces is 0.79, not 1.30"),
    "plan_bounds": (
        ("2006", "2011", "2016", "2021"),
        "per-party level bounds from the plan (MK [0.3, 1.0] and the rest), "
        "chosen knowing every result up to 2021"),
    "ward_pr_ratio_overrides": (
        ("2021",),
        "MK 0.80 is \"bounded by ActionSA's observed 0.77\", which is a 2021 "
        "measurement. Only read when the measured ward/PR ratio has no "
        "fallback to offer"),
    "pa_contestation_uplift": (
        ("2021",),
        "1.25 because the PA fought 52 of 135 wards in 2021. Only read when "
        "measured contestation is unavailable"),
    # "splinter" is gone from this list: `pools.splinter_record` now takes the
    # target and drops any split that had not happened yet, so the code
    # enforces what the key used to announce. It was also unclearable — no
    # scenario sets a key by that name, so every target it named was reported
    # in-sample forever, on the strength of a constant that did not exist.
    "entrant_geography": (
        ("2006", "2011", "2016", "2021"),
        "k measured across the six entrants on record (empty by default)"),
    # An entry with no years reads no RESULT, and so can never contaminate a
    # target; it is here to be reported rather than to be scored. Contestation
    # comes out of the target's own file, which looks alarming and is not: the
    # quantity is which parties appear on each ward's ballot, published when
    # nominations close and available to any forecaster weeks before polling
    # day. It used to count only the wards where a party WON votes, which is
    # not the ballot but the result, and that was a genuine leak.
    # Deliberately retrospective, at the project owner's direction and with
    # the reasoning recorded: only one home-city split had happened before
    # 2021, and one observation is not a sample — sizing ActionSA from it
    # alone gave 1.87% against an actual 16.1%. Using the whole record gives
    # 15.78%, from GOOD and MK, neither of which is ActionSA. A target at or
    # before the latest split used is therefore IN-SAMPLE and says so here,
    # which is the difference between a declared choice and a leak.
    "splinter_home": (
        ("2019", "2024"),
        "home-city splinter fractions (GOOD in Cape Town 2019, MK in "
        "eThekwini 2024). A split takes far more where its leader's own "
        "following is, and the effect is only measurable across elections "
        "either side of most targets"),
    "contestation": (
        (),
        "ward-ballot PRESENCE at the target, taken from the target's own "
        "file. Nomination lists are public before polling day; no vote is "
        "read"),
    # No years, for the same reason as `contestation` and with the same
    # obligation to say so. `levels.spine` weighs a party's national route
    # against its own previous local result; both records are filtered to
    # elections strictly before the target inside `theta_record` and
    # `local_record`, and the blend weight k is a single constant fitted by
    # leave-one-metro-out over transitions that are themselves all pre-target.
    # It is listed because a fallback the banner cannot name is exactly what
    # this registry exists to prevent — not because it reads a result.
    "spine": (
        (),
        "the national-and-local level blend (task #22). Both records are "
        "filtered to elections strictly before the target; k=1.0 is fitted "
        "across metros on pre-target transitions only"),
}


def contaminated(target_year: str, declared_clean: set[str],
                 read: Mapping[str, list[str]] | None = None) -> list[str]:
    """``FITTED_ON`` keys that read this target or later, minus declared ones.

    ``declared_clean`` is the set of keys a scenario file actually sets while
    declaring a ``derived_from`` that predates the target. Everything else is
    still whatever ``DEFAULTS`` says, and an inherited 2021-fitted constant is
    exactly as circular as one written out.

    ``read`` is ``montecarlo``'s record of the constants the run actually
    consumed. Given it, a key is only implicated if the run touched it — which
    is the difference between a warning and a measurement, and the difference
    between a target that can print an all-clear and one that cannot. Two keys
    here default to empty and are read by nothing until somebody fills them
    in, so before this every target from 2011 to 2016 was reported in-sample
    on the strength of two constants that had no value at all.
    """
    keys = set(FITTED_ON) if read is None else set(read) & set(FITTED_ON)
    return sorted(k for k in keys
                  if k not in declared_clean
                  and any(y >= str(target_year) for y in FITTED_ON[k][0]))


def check_derived_from(declared, target_year: str, label: str) -> list[str]:
    """Validate a scenario's ``derived_from`` list; return it as strings."""
    if not isinstance(declared, list) or not all(
            isinstance(y, (str, int)) for y in declared):
        raise SystemExit(f"{label}: \"derived_from\" must be a list of election "
                         f"years, e.g. [\"2011\", \"2016\"]")
    years = [str(y) for y in declared]
    unknown = [y for y in years if y not in cityconfig.CALENDAR]
    if unknown:
        raise SystemExit(f"{label}: \"derived_from\" names elections that are "
                         f"not in the calendar: {unknown}")
    peeking = sorted(y for y in years if y >= str(target_year))
    if peeking:
        raise SystemExit(
            f"{label} declares derived_from {years}, which includes "
            f"{peeking} — at or after the target {target_year}. A scenario "
            f"fitted on the election it is being scored against cannot be "
            f"scored against it; refit leaving {target_year} out, or run it "
            f"at a later target.")
    return years


def in_sample_banner(target_year: str, label: str, scenario_keys: set[str],
                     declared, read: Mapping[str, list[str]] | None = None
                     ) -> str:
    """The warning (or the all-clear) for one scenario at one target.

    Printed on every run, before the numbers, because the alternative is a
    reader taking a seat MAE of 114 for an out-of-sample result.

    ``read`` is what the run actually consumed (``ModelRun.constants_read``).
    Passing it is what makes this a measurement; without it the banner falls
    back to naming every constant that COULD be implicated, which is the
    conservative reading and the one to use if the run has not happened yet.
    """
    clean = set(scenario_keys) if declared is not None else set()
    dirty = contaminated(target_year, clean, read)
    if not dirty:
        if read is None:
            return (f"  out-of-sample (DECLARED, not verified): {label} says "
                    f"its numbers derive from "
                    f"{', '.join(str(y) for y in declared)}, all before "
                    f"{target_year}, and it sets every constant this harness "
                    f"knows to have read {target_year} or later.")
        touched = sorted(set(read) & set(FITTED_ON))
        provenance = (f" It read {', '.join(touched)}, none of which reaches "
                      f"{target_year}." if touched else
                      " It read none of the constants this harness tracks.")
        declaration = (f"{label} declares derived_from "
                       f"{', '.join(str(y) for y in declared)}. "
                       if declared is not None else "")
        return (f"  OUT-OF-SAMPLE (MEASURED): {declaration}Nothing this run "
                f"consumed was fitted on {target_year} or later.{provenance}")

    rule = "  " + "!" * 74
    lines = [rule,
             "  !! IN-SAMPLE — THESE ARE NOT OUT-OF-SAMPLE SCORES",
             rule,
             f"  Scenario {label!r} scores target {target_year} using priors "
             f"fitted on {target_year} or later.",
             "  The scores below measure fit, not forecasting skill; read them "
             "as an upper bound."]
    if declared is not None:
        lines.append(f"  Its derived_from ({', '.join(str(y) for y in declared)})"
                     f" covers only the keys it sets; these are inherited from "
                     f"montecarlo.DEFAULTS:")
    elif read is not None:
        lines.append("  No \"derived_from\" declared. These constants were "
                     "READ BY THIS RUN, with what read them:")
    else:
        lines.append("  No \"derived_from\" declared, so nothing is claimed to "
                     "be clean. Implicated constants:")
    for key in dirty:
        years, why = FITTED_ON[key]
        saw = ", ".join(y for y in years if y >= str(target_year))
        lines.append(f"    {key:<24s} read {saw} — {why}")
        users = list((read or {}).get(key) or [])
        if users:
            shown = ", ".join(users[:8])
            more = f" (+{len(users) - 8} more)" if len(users) > 8 else ""
            lines.append(f"      consumed by: {shown}{more}")
    # The clean reads are printed too. A banner that lists only what is wrong
    # invites the reading that everything else was measured from nothing, and
    # the interesting cases here are the ones that touch the target's own file
    # legitimately — contestation takes the ward ballot and no vote on it.
    clean_reads = sorted((set(read or {}) & set(FITTED_ON)) - set(dirty))
    if clean_reads:
        lines.append("  Also read, and clean at this target:")
        for key in clean_reads:
            years, why = FITTED_ON[key]
            when = ", ".join(years) if years else "no result"
            lines.append(f"    {key:<24s} read {when} — {why}")
    lines.append("  Declare a clean scenario with a top-level \"derived_from\": "
                 "[\"2011\", ...] naming every")
    lines.append("  election its numbers were fitted on; a run refuses if any "
                 "entry reaches the target.")
    lines.append(rule)
    return "\n".join(lines)


def relabel_entrant(ward_probs: Mapping[str, Mapping[str, float]],
                    entrant: str | None) -> dict[str, dict[str, float]]:
    """Rename the generic ``ENTRANT`` to the party that actually arrived.

    ``score_seats`` has taken ``entrant_actual`` since it was written; ward
    scoring did not, so a draw was credited for ActionSA's *seats* and debited
    for ENTRANT's *ward wins* — the model punished for the one thing the
    entrant machinery exists to get right. Harmless only while the entrant is
    flat and never tops a ward; the moment ``entrant_geography`` is set it
    bites, in exactly the comparison this module exists to make.
    """
    if not entrant:
        return {w: dict(p) for w, p in ward_probs.items()}
    out: dict[str, dict[str, float]] = {}
    for ward, probs in ward_probs.items():
        merged: defaultdict[str, float] = defaultdict(float)
        for party, p in probs.items():
            merged[entrant if party == "ENTRANT" else party] += p
        out[ward] = dict(merged)
    return out


def ward_structure(path: Path):
    """VD -> ward and VD -> registered, from the target's own result file.

    Boundaries and the roll are public before polling day, so taking them from
    the result file is not peeking; the votes in the same file are used only
    for scoring. Kept here because ``benchmarks.py`` builds its baselines from
    it; the model reaches the same data through ``montecarlo.ward_parts``.
    """
    ward_of: dict[str, str] = {}
    registered: dict[str, int] = {}
    with cityconfig.resolve_path(path).open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            vd = row["VD_Number"]
            if row.get("Ward"):
                ward_of.setdefault(vd, row["Ward"].strip())
            if row.get("Registered_Population"):
                registered.setdefault(vd, int(float(row["Registered_Population"])))
    return ward_of, registered


def _year_from(path: Path) -> int:
    """The election year in a result filename: ``lge2021_JHB_...`` -> 2021."""
    stem = Path(path).name
    digits = "".join(c for c in stem[:8] if c.isdigit())
    if len(digits) != 4:
        raise ValueError(f"cannot read an election year from {stem!r}")
    return int(digits)


def actual_result(path: Path, council: int, year: int | None = None,
                  code: str | None = None):
    """The real council and the real ward winners, checked against the IEC.

    Seats follow the *combined* ward and PR ballots (§0), over the parties the
    quota is computed on -- which is ``seats.eligible_parties``: independents
    and parties that contested a ward with no PR list are handled through
    Schedule 1's C and D terms rather than by earning an entitlement. Running
    ``allocate`` over every party instead, as this function did until
    2026-08-10, both mis-states the answer and invents seats no forecaster
    could win: ActionSA came out at 43 against the 44 the IEC published, the
    2016 ANC at 120 against 121, the 2011 ANC at 152 against 153, and
    independents were handed 1-2 list seats they cannot hold. ``fold.py`` has
    always done this correctly; this now matches it.

    The reconstruction is then checked party by party against the IEC's own
    Seat Calculation Detail and raises on any disagreement. A ground truth that
    is only *probably* right is not a ground truth.
    """
    ward_votes, ward_of = load(path, "Ward")
    pr_votes, _ = load(path, "PR")

    def totals(votes) -> dict[str, int]:
        out: defaultdict[str, int] = defaultdict(int)
        for counts in votes.values():
            for party, n in counts.items():
                out[party] += n
        return dict(out)

    combined = eligible_parties(totals(ward_votes), totals(pr_votes))

    per_ward: defaultdict[str, defaultdict[str, int]] = defaultdict(
        lambda: defaultdict(int))
    for vd, counts in ward_votes.items():
        w = ward_of.get(vd)
        if not w:
            continue
        for party, n in counts.items():
            per_ward[w][party] += n
    winners = {w: max(counts, key=counts.get) for w, counts in per_ward.items()}

    # C and D: seats that leave the entitlement pool with the councillor.
    year = year or _year_from(path)
    code = code or cityconfig.active().code
    official = official_seats.read(code, int(year))

    wins = Counter(winners.values())
    outside = {party: n for party, n in wins.items()
               if party == "IND" or party not in combined}
    no_pr_list_wards = sum(n for party, n in outside.items() if party != "IND")

    # C IS TAKEN FROM THE IEC WHEREVER THE REPORT EXISTS, because it cannot be
    # counted from the published votes. Every independent in a voting district
    # arrives merged into one row named IND, so a ward contested by several of
    # them shows their SUM: Buffalo City ward 29200044 reads IND 1,899 against
    # the ANC's 1,714, while the IEC records C = 0 for that municipality — the
    # largest single independent polled under 1,714 and the ANC won the ward.
    # Counting the bloc as a winner deducted a seat that was never deducted,
    # and since C leaves the pool BEFORE the quota is struck it moved the
    # quota and every party's entitlement with it. See DATA-QUALITY.md item 12.
    #
    # The inferred figure is kept and reported: it is an upper bound, and the
    # gap between it and C is the size of the problem in that city.
    inferred_independent_wards = outside.get("IND", 0)
    independent_wards = (official["independents"]
                         if official and "independents" in official
                         else inferred_independent_wards)
    if independent_wards != inferred_independent_wards:
        print(f"  ! independent ward wins: counted {inferred_independent_wards} "
              f"from merged IND rows, using the IEC's published C = "
              f"{independent_wards}. They cannot be told apart in the data; "
              f"the counted figure is an upper bound (DATA-QUALITY.md item 12).")
        outside["IND"] = independent_wards

    seats = allocate(combined, total_seats=council,
                     independent_wards=independent_wards,
                     no_pr_list_wards=no_pr_list_wards).seats
    seats = {p: s for p, s in seats.items() if s > 0}
    if official is None:
        print(f"  !! no Seat Calculation Detail for {code} {year}: the "
              f"reconstructed council is UNVERIFIED. Fetch it with "
              f"python src/fetch_iec.py --muni {code} "
              f"--province {cityconfig.active().province}")
    else:
        want: Counter[str] = Counter()
        for name, row in official["parties"].items():
            want[P.canonical(name)] += row["seats"]
        # The IEC's table is the whole chamber; ``seats`` is the entitlement
        # pool only. ``allocate`` was asked for ``council - C - D`` seats, so
        # the ward seats that left the pool with an independent or a party
        # without a PR list have to be added back before the totals can be
        # compared, and subtracted from that party's IEC row before the
        # per-party comparison. Comparing the pool against the chamber was
        # latent while C = D = 0 in every city-year on disk; it would have
        # blocked the first metro with an independent ward win — which is the
        # case this reconstruction most needs to get right.
        want = {p: n - outside.get(p, 0) for p, n in want.items()}
        want = {p: n for p, n in want.items() if n > 0}
        rebuilt_total = sum(seats.values()) + sum(outside.values())
        if want != seats or rebuilt_total != official["seats"]:
            bad = sorted(set(want) | set(seats),
                         key=lambda p: -abs(want.get(p, 0) - seats.get(p, 0)))
            detail = ", ".join(f"{p}: IEC {want.get(p, 0)} vs rebuilt "
                               f"{seats.get(p, 0)}" for p in bad
                               if want.get(p, 0) != seats.get(p, 0))
            raise SystemExit(
                f"the reconstructed {year} council does not match the IEC's "
                f"published seat calculation ({Path(official['path']).name}): "
                f"{detail or 'totals differ'}. Everything scored against it "
                f"would be scored against the wrong answer.")
    return seats, winners


def entrant_actual_for(actual_seats: Mapping[str, int],
                       base_city: Mapping[str, float]) -> str | None:
    """Which party actually arrived from nothing, if any.

    The model draws a *generic* entrant -- it cannot know a new party's name --
    so scoring maps ENTRANT onto whichever seat-winning party had no baseline
    at all. Anything else scores the machinery as a total miss even when it
    sized the newcomer correctly, which is the interesting question.
    """
    newcomers = {p: s for p, s in actual_seats.items() if p not in base_city}
    return max(newcomers, key=newcomers.get) if newcomers else None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    cityconfig.add_city_argument(ap)
    # No `choices=`: the runnable set is per city (see runnable_targets) and
    # --city has not been parsed yet. Validated below, once the city is known.
    ap.add_argument("--target", default="2021", metavar="YEAR",
                    help="past local election to score against (default 2021); "
                         "runnable targets are derived per city — pass a bad "
                         "one to be told this city's set")
    ap.add_argument("--config", type=Path, help="scenario json (model to test)")
    ap.add_argument("--a", type=Path, help="A/B: first scenario")
    ap.add_argument("--b", type=Path, help="A/B: second scenario")
    ap.add_argument("--draws", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20211101)
    ap.add_argument("--data-dir", type=Path, default=Path("data/raw/elections"))
    ap.add_argument("--processed", type=Path, default=None,
                    help="target inputs (default: the target's own directory)")
    ap.add_argument("--all-parties", action="store_true",
                    help="print every scored party, not the top 12. REQUIRED by "
                         "anything that turns this output back into data: the 12 "
                         "is a terminal-width limit, and these targets have 15 to "
                         "24 actual seat-winners, so a truncated table stored as "
                         "JSON gives a truncated seat error that is not comparable "
                         "to one summed over the whole ballot")
    args = ap.parse_args(argv)

    city = cityconfig.use(args.city)
    runnable = runnable_targets(city)
    if args.target not in runnable:
        raise SystemExit(
            f"--target {args.target} cannot be scored for {city.name}; "
            f"runnable targets are {', '.join(runnable)}. A past LGE also "
            f"needs a council size in cities/{city.slug}.toml, a γ fold that "
            f"precedes it, and a previous LGE and NPE with result files.")
    target = cityconfig.use_target(args.target)
    M.apply_city(city)                    # after use_target: council is per-year
    processed = args.processed or target.processed

    actual_path = args.data_dir / target.results(target.year)
    actual_seats, actual_winners = actual_result(
        actual_path, target.council, int(target.year), city.code)

    base_votes, _ = load(args.data_dir / target.results(target.previous_npe), None)
    base_city = citywide(base_votes)
    entrant = entrant_actual_for(actual_seats, base_city)

    print(f"backtest: {city.name} {target.year} ({target.date}) "
          f"— council {target.council}, γ fold {M.gamma_fold_for(target)}, "
          f"inputs from {processed}")
    if entrant:
        print(f"  party arriving from nothing: {entrant} "
              f"({actual_seats[entrant]} seats) — scored against ENTRANT")
    print(f"  actual council: {sum(actual_seats.values())} seats to "
          f"{len(actual_seats)} parties (matches the IEC's published "
          f"calculation); {len(actual_winners)} wards")

    if args.a and args.b:
        configs = [("A", args.a), ("B", args.b)]
    elif args.config:
        configs = [(args.config.stem, args.config)]
    else:
        configs = [("defaults", None)]

    summary = []
    for label, path in configs:
        scenario = copy.deepcopy(M.DEFAULTS)
        overrides: dict = {}
        declared = None
        if path:
            # Same validation montecarlo.load_scenario applies: an unknown key
            # used to be dropped in silence here, so a typo produced a run that
            # reported itself as the config under test while scoring DEFAULTS,
            # and an A/B table printed two identical rows as if they were two
            # models.
            overrides, metadata = M.read_scenario_file(path)
            M.apply_overrides(scenario, overrides)
            if "derived_from" in metadata:
                declared = check_derived_from(metadata["derived_from"],
                                              target.year, str(path))
        scenario["draws"] = args.draws
        scenario["seed"] = args.seed

        # The banner used to print here, before the run, and could therefore
        # only list what MIGHT be contaminated. Two of its keys are empty by
        # default and read by nothing, so every target from 2011 to 2016 was
        # declared in-sample on their account and no run could ever come back
        # clean — while theta_mode, which target 2021 really does read, was
        # not on the list at all. It now prints after the run and reports what
        # the run actually consumed. It is still above the numbers, which is
        # what matters: nobody reads a seat MAE and then checks the provenance.
        run = M.run_model(target, scenario, args.data_dir, processed)
        read = run.constants_read
        in_sample = bool(contaminated(
            target.year, set(overrides) if declared is not None else set(),
            read))
        print()
        print(in_sample_banner(target.year, label, set(overrides), declared,
                               read))
        seats = S.score_seats(run.seat_draws, actual_seats, entrant, seed=args.seed)
        wards = S.score_wards(
            relabel_entrant(run.ward_probabilities(), entrant), actual_winners)
        print()
        print(S.format_report(seats, wards, label=label,
                              top=None if args.all_parties else 12))
        summary.append((label, seats, wards, in_sample))

    if len(summary) > 1:
        print(f"\n  {'scenario':18s}{'CRPS':>9s}{'energy':>9s}{'seatMAE':>9s}"
              f"{'BrierMC':>9s}{'90% coverage':>15s}")
        for label, seats, wards, in_sample in summary:
            cov90 = next(r for r in seats["coverage"] if r["level"] == 0.9)
            cov = f"{cov90['inside']}/{cov90['counted']} = {cov90['empirical']:.0%}"
            print(f"  {label:18s}{seats['crps']['total']:>9.2f}"
                  f"{seats['energy']:>9.2f}{seats['seat_mae_median']:>9.0f}"
                  f"{wards['brier_multicategory']:>9.4f}{cov:>15s}"
                  f"{'  IN-SAMPLE' if in_sample else '':>12s}")
        if any(row[3] for row in summary):
            print("  IN-SAMPLE rows carry priors fitted on the target election; "
                  "they are not comparable to a")
            print("  declared out-of-sample row, and neither is comparable to a "
                  "benchmarks.py baseline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
