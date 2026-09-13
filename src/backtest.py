"""Score the forecast model against an election that has already happened.

``fold.py`` validates the deterministic core -- the share model, γ, the ballot
split and the seat allocator. What it cannot touch is the *distributional*
layer, which is where every judgement in this project lives: pool
ranges, the Dirichlet concentrations, the splinter branch, entrant geography,
turnout uncertainty, the by-election terms. This harness runs the model at a
past election and scores the distribution it produced against what actually
happened::

    python src/backtest.py --target 2021
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

**The register was not the model, and for months it was not close.** It held
eight constants; ``montecarlo.DEFAULTS`` holds thirty-five, and the rest were
excused in a paragraph of prose that nothing could enumerate. ``level_shrink``
— fitted by leave-one-city-year-out across a nine-city-year panel this harness
SCORES, and worth coherent seat error 312 -> 264 — appeared nowhere in this
file, so no banner could name it and a declared scenario could inherit it into
a MEASURED all-clear. Provenance now lives in four registers covering every
``DEFAULTS`` key exactly once, enumerated in both directions by a test.

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
from seats import INDEPENDENT, allocate, eligible_parties

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

# ⛔ FOUR REGISTERS, AND EVERY ``montecarlo.DEFAULTS`` KEY IS IN EXACTLY ONE.
#
# This was one register plus a PROSE paragraph of exceptions, and the paragraph
# is why ``level_shrink`` — a parameter worth coherent seat error 312 -> 264,
# fitted by leave-one-city-year-out over a panel this harness SCORES — appeared
# nowhere in this file at all. Prose cannot be enumerated, so nothing could
# notice that 27 of the 35 ``DEFAULTS`` keys reached neither list. The
# enumeration is now machine-checked in BOTH directions by
# ``tests/test_levers_are_live.py::
# test_every_defaults_key_declares_whether_it_read_an_election``.
#
#   FITTED_ON                  read an election result; consumption PROVED by
#                              ``montecarlo.note_constant``
#   FITTED_ON_UNINSTRUMENTED   read an election result; consumption NOT
#                              instrumented — the run resolves the key and
#                              nothing records the read
#   PROVENANCE_UNSETTLED       we do not yet know which of the two it is, and
#                              saying either would be a guess
#   NOT_FITTED                 reads no election result, with the reason
#
# ⚠️ THE SPLIT IS ABOUT EVIDENCE, NOT ABOUT IMPORTANCE. It is the same
# distinction ``montecarlo.assert_delivered`` draws between a ``consulted``
# record and a ``resolved`` one: the first says code read the value, the second
# says the process held it. Merging the two registers would claim a proof that
# does not exist; dropping the second is what produced this defect.
#
# γ is in none of them because it is not a ``DEFAULTS`` key and because
# ``gamma_fold_for`` already REFUSES a fold that does not finish strictly
# before the target — the one part of this problem the code can enforce
# instead of announce.

# Which elections each constant read, taken from the constants' own comments
# rather than from a fresh judgement -- if a comment says a number came from an
# election, that election is listed here. The years are the LGEs whose *results*
# the number saw, so a target at or before a listed year means the prior has
# read the answer.
FITTED_ON: dict[str, tuple[tuple[str, ...], str]] = {
    "pools": (
        ("2011", "2016", "2021"),
        "pool COMPOSITION comes from Census 2022, which post-dates any target "
        "before 2026. The ratio ranges no longer do — they derive from "
        "transitions strictly before the target. A census is a covariate, not "
        "an outcome: it says who lives in a ward, not how they voted."),
    # theta_mode, individual_theta and f_other were listed here until
    # 2026-08-19 and are DELETED with the constants themselves (§1.52).
    #
    # The comment they replaced is worth keeping in outline, because it was
    # RIGHT at the time and stopped being right for a reason. It said the
    # three had been dropped from this list on the grounds that levels.py
    # measures theta from transitions strictly before the target, and that
    # this was 'true per party and false in general' -- a party the record
    # could not reach still fell back to the plan's number, and at target
    # 2021 ActionSA took its 1.50 from theta_mode while 31 parties took bands
    # from individual_theta. So they were listed again.
    #
    # What changed is the general case: since the spine, the record reaches
    # EVERY party at every runnable target, the fallback branches were dead,
    # and they are now gone. A contamination entry for a key nothing can read
    # is a permanent in-sample verdict no scenario can clear.
    "plan_bounds": (
        ("2006", "2011", "2016", "2021"),
        "per-party level bounds from the plan (MK [0.3, 1.0] and the rest), "
        "chosen knowing every result up to 2021"),
    # "ward_pr_ratio_overrides" was here. The key is gone (2026-08-17): it was
    # consumed at no target, because the measured ward/PR fallback is available
    # at all of them. Removed from FITTED_ON too, since a contamination entry
    # for a constant that cannot be read reports a risk that does not exist --
    # which is the same fault, in the other direction, as the phantom keys
    # MODEL-LOG 1.29 removed from this list.
    # "pa_contestation_uplift" was here until 2026-08-18 and is DELETED with
    # the constant itself. A one-party fiddle, live only where no backtest could
    # reach it; the contestation fallback is measured for every party now.
    # "splinter" is gone from this list: `pools.splinter_record` now takes the
    # target and drops any split that had not happened yet, so the code
    # enforces what the key used to announce. It was also unclearable — no
    # scenario sets a key by that name, so every target it named was reported
    # in-sample forever, on the strength of a constant that did not exist.
    "entrant_geography": (
        ("2006", "2011", "2016", "2021"),
        "k measured across the six entrants on record (empty by default)"),
    # ⚠️ AN ENTRY WITH NO YEARS MEANS "NO YEAR IT READS CAN REACH A TARGET".
    # That is NOT the same as "it reads nothing", and the two cases are both
    # here. `contestation`, `spine`, `metro_poll` and `poll_level` read no
    # result at all; `splinter_home` reads several and has its window cut at
    # the target. `contaminated` needs the same answer from both — no year at
    # or after the target — so both carry the empty tuple, and the difference
    # lives in each entry's own prose, which is why the banner prints it.
    # Contestation comes out of the target's own file, which looks alarming
    # and is not: the quantity is which parties appear on each ward's ballot,
    # published when nominations close and available to any forecaster weeks
    # before polling day. It used to count only the wards where a party WON
    # votes, which is not the ballot but the result, and that was a genuine
    # leak.
    #
    # ⛔ A TARGET-AWARE QUANTITY CANNOT BE DESCRIBED BY A STATIC YEAR TUPLE,
    # AND THIS ENTRY TRIED TO FOR THIRTY DAYS. It read ("2019", "2024"),
    # written 2026-08-11 when `pools.home_splinter_record` ignored the target
    # and every run measured MK's eThekwini split. The cutoff landed three days
    # later — `pools.emit_pools` sets `home_cutoff` to the target year unless
    # `--retrospective-home` is given, and `home_splinter_record` drops any
    # split whose second election reaches it — and this entry did not move. So
    # `contaminated` named `splinter_home` on every panel row that read it,
    # while the spec each of those rows loads had measured only splits
    # strictly before its own target. MODEL-LOG §1.232.
    #
    # Two years was also the wrong SHAPE, not merely the wrong pair. The window
    # moves with the target, so the record this key reads is a different set at
    # every target and no single tuple can name it. The tuple that was here
    # named neither the set at 2021 nor the set at 2026: it omitted the NFP
    # split that is in both.
    #
    # ⚠️ IT STAYS IN `FITTED_ON`, AND THAT IS NOT A FREE CHOICE.
    # `tests/test_chain.py` matches every `note_constant(scenario, "...")` in
    # `montecarlo.py` against this dict in BOTH directions, so a key the run
    # notes must be declared HERE and nowhere else. `splinter` could be deleted
    # from this register when its cutoff landed because nothing notes it;
    # `splinter_home` is noted, so deleting it fails that guard, and moving it
    # to `FITTED_ON_UNINSTRUMENTED` or `PROVENANCE_UNSETTLED` fails it too.
    # That it is not a `montecarlo.DEFAULTS` key does not bear on the choice:
    # several entries here are not, and the completeness guard runs DEFAULTS
    # → the registers, never the reverse.
    #
    # ⛔ WHAT THE EMPTY TUPLE DOES NOT COVER: `--retrospective-home`. That flag
    # restores the unfiltered record, and a spec emitted under it CAN carry a
    # year at or after its target. This register cannot see it, because the
    # years are a property of the RUN and not of the constant. The detector is
    # the spec's own `splinter_home` marker, which records which splits were
    # used and when they happened, is emitted on both paths, and which
    # `run_model` turns into this key's `note_constant` text — so every run's
    # `constants_read` carries the years and the scoreboard row records them.
    # ⚠️ The BANNER prints a key's consumers only when the key is IMPLICATED,
    # which on the default path is now never: the clean-reads block prints the
    # key and its reason and not its note. Read the spec's marker or the row's
    # `constants_read`, not this entry, to find out what a given run measured.
    "splinter_home": (
        (),
        "home-city splinter fractions. It DOES read results — the splits on "
        "record are in `pools.SPLITS` — but the window is cut at the target, "
        "so no year it reads can reach one. Which splits a given run used, "
        "and when they happened, are in that spec's `splinter_home` marker "
        "and in this run's own `constants_read`. `--retrospective-home` "
        "disables the cutoff and only the marker catches it"),
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
    # No years, and the reason is enforced in code rather than asserted here:
    # polling.usable_for admits a poll only when its machine-readable
    # fieldwork_end falls strictly before the target's polling day, and refuses
    # any poll it cannot date. Party-commissioned polls are excluded by default.
    # The conversion's other inputs — which municipalities a party contests, and
    # their share of the national vote — are nomination and roll facts published
    # weeks ahead.
    # A metro poll of the target's own city, admitted only when its fieldwork
    # ended before polling day AND it declares this election as its target.
    # Blended by inverse variance against the model's own spread, so it is
    # weighted by precision rather than by how much history a party has.
    "metro_poll": (
        (),
        "a poll of this city, taken before polling day and declared for this "
        "election, blended by inverse variance (task #23). Reads no result"),
    "poll_level": (
        (),
        "an arrival's level taken from a national poll, converted by the share "
        "of the national vote in the municipalities it contests (task #23). "
        "Only for parties with NO record at the preceding national election; "
        "fieldwork must end before polling day or the poll is refused"),
}


# Same shape as :data:`FITTED_ON`, and the difference is the EVIDENCE, not the
# seriousness. Nothing calls ``note_constant`` at these read sites, so this
# harness cannot say the run consumed them; it can say the run RESOLVED them,
# which is what ``scenario[key]`` being present means and no more.
#
# ⛔ THE DECLARATION IS THE AUTHOR'S WORD — the same caveat the module docstring
# puts on ``derived_from``. Nothing here verifies a provenance and none of it is
# evidence. What IS checked is that the register is complete, that its years are
# real elections, and that no entry names a constant the model does not have.
#
# **THE FIX IS TO MAKE A CONSTANT TARGET-AWARE, NOT TO DECLARE IT
# CONTAMINATED** (owner, 2026-09-12). A number recomputed with a cutoff at the
# target stops being a leak; registration is the fallback for what genuinely
# cannot be recomputed — the census being the one real example. Every entry
# below that carries a fix number is scheduled for that treatment, and the
# entry is the bookkeeping in the meantime.
FITTED_ON_UNINSTRUMENTED: dict[str, tuple[tuple[str, ...], str]] = {
    # THE NINE-CITY-YEAR PANEL IS JHB16 + THE EIGHT METROS AT 2021 (MODEL-LOG
    # §1.44's own per-city-year table). It does NOT contain Johannesburg 2011 —
    # a 2011 target is implicated anyway, because a constant fitted on 2016 and
    # 2021 results is hindsight at 2011 and `contaminated` tests `y >= target`.
    "level_shrink": (
        ("2016", "2021"),
        "leave-one-city-year-out over nine city-years chose 0.350 in all nine "
        "folds, and the FORM was screened against the same nine (§1.44 records "
        "that as an L1 leak). Worth coherent seat error 312 -> 264 on that "
        "panel, which is the size of the thing being declared"),
    "level_shrink_scale": (
        ("2016", "2021"),
        "the twenty-fold 0.02-0.40 sweep that selected 0.04 ran on the same "
        "nine city-years (§F20). 'A scale, not a tuned constant' bounds how "
        "much the leak is WORTH — the correction improves 7 of 9 at every "
        "value — and does not make it absent"),
    "dirichlet_scale": (
        ("2016", "2021"),
        "⚠️ UNRESOLVED, AND LISTED IN THE CONSERVATIVE DIRECTION. 1.0 is the "
        "identity on `pools.dirichlet_alpha`'s method-of-moments fit, whose "
        "inputs are pre-target and already covered by `pools` — on that reading "
        "it reads no result. But it was RETAINED after a 0.5/1.0/2.0 sweep "
        "across the nine city-years (§1.55, §1.58), and confirmed-by-the-panel "
        "is still selection-on-the-panel. Over-warning is the cheaper error"),
    "contestation_expand": (
        ("2011", "2016", "2021"),
        "0.220 is the median slate expansion measured across the eight metros "
        "and every consecutive LGE pair on disk, n=165 (§A5). ⚠️ RESOLVED BUT "
        "ALMOST CERTAINLY NOT CONSUMED at any past target: `levels.contestation` "
        "returns the target's published lists and `levels.projected_contestation` "
        "— the only consumer — is then never called. That gate is machine-checked "
        "by tests/test_levers_are_live.py GATES['real_contestation_lists']"),
    "entrant_prob": (
        ("2011", "2016", "2021"),
        "⚠️ UNRESOLVED. 0.25 is TYPED and predates the measurement (§A3), so on "
        "one reading it read nothing. But the arrival base rate that validates "
        "it (NFP 2011, AIC 2016, ActionSA 2021; 7 of 9 city-years) and the "
        "panel sweep that refused to raise it (254/262/264 coherent at "
        "0.25/0.290/0.353) both read those results. ⚠️ Inert wherever the "
        "arrivals are seeded by name — GATES['arrivals_are_named'], which is "
        "OPEN at 2011"),
    "entrant_share": (
        ("2016", "2021"),
        "⚠️ UNRESOLVED, as `entrant_prob`. [0.01, 0.04, 0.12] is typed from the "
        "plan; what is quoted for it is a check against the AIC's 1.62% in 2016 "
        "and against ActionSA in 2021 (§A17). Same arrivals gate"),
    # ⛔ THE EXCUSE THAT USED TO COVER THIS WAS FALSE, AND THAT IS WHY IT MOVED.
    # The deleted prose said the turnout dials "are not fitted on any election's
    # result". True of the three TYPED dials (§A41/§F23) and untrue of this one:
    # `montecarlo.py`'s own comment says 0.63 is measured "over 14
    # metro-transitions (eight metros, 2011->2016 and 2016->2021)".
    "turnout_correlation": (
        ("2016", "2021"),
        "the mean off-diagonal correlation between pools' log turnout changes, "
        "measured over 14 metro-transitions — eight metros, 2011->2016 AND "
        "2016->2021 (montecarlo.py, beside TURNOUT_CORRELATION). It reads "
        "TURNOUT and not votes, which is why it was mistaken for a typed dial; "
        "turnout is still an outcome no forecaster holds before polling day, "
        "and at a 2021 target this constant was fitted on 2021's. FIX #38 "
        "makes the derived calculation take the target into account — a "
        "constant recomputed with a cutoff stops being a leak, which is the "
        "remedy this register is the fallback for. Until then it is declared"),
}


# ⛔ NEITHER A CLEARANCE NOR A VERDICT. A key here has a provenance the record
# states TWICE, incompatibly, and nobody has yet settled which account is true.
#
# It is a register because the completeness guard demands that every
# ``DEFAULTS`` key be accounted for and silence is the failure being fixed; it
# is a SEPARATE register because filing an unsettled key as fitted or as
# excused would replace one false statement with another, which is the whole
# class of defect here. It blocks the MEASURED all-clear and reports itself; it
# does not score the key as contaminated, because that would be a verdict.
#
# The years are the WORST CASE under the unsettled reading — what the constant
# would have read if the less favourable of the two accounts is the true one.
# They are what keeps this from becoming noise: at a target the worst case does
# not reach, the open question cannot bite and the banner says nothing about
# it. Flagging the live 2026 forecast over a constant that on either account
# read nothing after 2021 would spend the banner's credibility where it is
# needed most.
PROVENANCE_UNSETTLED: dict[str, tuple[tuple[str, ...], str]] = {
    "spine_k": (
        ("2011", "2016", "2021"),
        "FIX #39, OPEN. This key ships as None and resolves to "
        "`levels.SPINE_K = 1.0`, and the record gives that constant two "
        "incompatible provenances. `FITTED_ON[\"spine\"]` says k is \"fitted "
        "across metros on pre-target transitions only\" and carries NO years, "
        "so it can never contaminate anything. `levels.py`, beside the "
        "constant, says it was \"fitted by leave-one-metro-out over 180 "
        "party-city-years across eight metros and three transitions\" — and "
        "three transitions on the archive reaches 2016->2021, which is the "
        "2021 result, in Johannesburg among others. One of those two "
        "statements is wrong. Neither is repeated here as though it were "
        "settled; the investigation is the deliverable, and the register waits "
        "for it"),
}


# Reads no election result, one entry per ``montecarlo.DEFAULTS`` key, with the
# reason. This is the paragraph of prose that used to live above ``FITTED_ON``,
# made enumerable — and one claim shorter, because ``turnout_correlation`` was
# in it and should not have been.
#
# ⚠️ An entry here is a CLAIM ABOUT A MECHANISM and it expires when the
# mechanism changes. Several rest on a gate being shut; each names the gate, and
# ``tests/test_levers_are_live.py`` is where those gates are actually checked.
NOT_FITTED: dict[str, str] = {
    # --- run control: not a claim about the world at all -------------------
    "draws": "how many samples to take",
    "seed": "reproducibility, not a model parameter",
    # --- the by-election family -------------------------------------------
    # ⚠️ NOT "it reads no election": a by-election IS an election. It reads no
    # LGE result, and its evidence window POST-DATES every past target, so the
    # whole block is unreachable in a backtest. If the channel ever does deliver
    # at a past target, the window makes that a LEAK and these entries move.
    "w_bye": "the by-election blend weight. The evidence window is 2022-06 to "
             "2026-02, so `bye` is empty at every past target and the weight "
             "multiplies nothing — GATES['bye_deltas_absent']. Typed, 🔴 "
             "argued-not-tested, and scoreable only by the 2026 result",
    "bye_weight_mode": "which weighting the by-election block uses, chosen "
                       "inside a block no past target enters — the same gate as "
                       "`w_bye`. A method choice, not an estimate",
    "w_bye_local_ward": "the ward-local by-election weight; ships 0.0 and its "
                        "input file exists at no past target "
                        "(GATES['bye_contest_detail_absent'])",
    "w_bye_local_pr": "the same, for the list ballot",
    "bye_local_cap": "a cap in logit units on one contest's shift, measured on "
                     "byelection_contest_detail.csv — by-election evidence, "
                     "never an LGE result, and behind the same two gates",
    "bye_tau_months": "the recency half-life on by-election evidence; same "
                      "evidence base and same gates",
    # --- the poll levers ---------------------------------------------------
    # Every one of these reads a POLL. The cutoff is enforced in code, not
    # announced here: `polling.usable_for` admits a poll only when its
    # machine-readable fieldwork_end falls strictly before the target's polling
    # day, and refuses any poll it cannot date. Same reason `metro_poll` and
    # `poll_level` sit in FITTED_ON with no years.
    "poll_paths": "WHICH poll paths run. A switch over mechanisms, not an "
                  "estimate. ⚠️ It ships \"off\" (§1.225), a default the owner "
                  "chose on a channel measured at -6 coherent seats across the "
                  "panel — so the SWITCH is panel-informed even though the "
                  "thing it switches reads no result",
    "poll_credence": "how much to believe a metro poll; declared, 1.0 is the "
                     "identity, and no poll it weighs post-dates its target",
    "poll_house_k": "the cap on one house's weight; declared (§1.67)",
    "poll_deff_subsample": "the design effect charged to a metro subsample; "
                           "declared",
    "poll_screen_sd": "the surcharge for an undisclosed likely-voter screen; "
                      "declared",
    "poll_drift_per_root_day": "assumed opinion drift between fieldwork and "
                               "polling day; declared",
    "poll_min_n": "the admission floor on a poll's n; declared",
    "poll_half_life_days": "the recency half-life across poll waves; declared, "
                           "and asserted equal to polling.POLL_HALF_LIFE_DAYS "
                           "at import",
    # --- the typed turnout dials (A2) -------------------------------------
    # These three ARE what the deleted prose meant by "the turnout dials".
    # Each weighs or jitters a turnout pattern; neither pattern is estimated
    # here, and both are resolved per target from `<target>/turnout.csv`.
    "turnout_pattern_blend": "the weight between two turnout patterns. Typed "
                             "(§A41/§F23); the patterns themselves come from "
                             "the target's own turnout.csv",
    "turnout_blend_jitter": "how far the blend is jittered per draw. Typed; "
                            "measured citywide effect ~0.003",
    "turnout_noise_sd": "per-VD lognormal turnout noise. Typed",
    # --- machinery floors and audit findings -------------------------------
    "ward_noise_sd": "an audit finding about the machinery, not about a party "
                     "(2026-08-05): ward winners were deterministic given a "
                     "citywide draw, which overstated P(overhang)",
    "level_floor": "the same class — the SHARE_FLOOR clamp made sub-0.2% "
                   "levels unattainable and inflated the micro-party tail",
    "dirichlet_floor": "the same clamp on deviation inputs, mirrored as a "
                       "scenario key so the sweep that chose it is reproducible",
    "level_sd_default": "the fallback level spread for a party with no measured "
                        "sd(log theta). It binds on no party at either target "
                        "(GATES['level_sd_fallback_never_binds']) and is a "
                        "fallback, not a fit",
    # --- statute and switches ---------------------------------------------
    "overhang_rule": "the excessive-seats provision. Municipal Structures Act "
                     "Schedule 1 item 16 as amended by Act 3 of 2021 — the "
                     "project did not choose it and cannot",
    "arrival_group_draw": "WHICH arrival mechanism runs. A switch, and its "
                          "value is the off state. ⚠️ The decision to keep it "
                          "off was taken against the panel (§1.63, re-run "
                          "§1.136), so the same selection-by-confirmation "
                          "question `dirichlet_scale` carries applies to the "
                          "SWITCH; the mechanism behind it reads no result",
    # --- and the two DEFAULTS keys that are already in FITTED_ON ------------
    # `pools` and `entrant_geography` are not here; they are instrumented.
}


# The two registers that carry YEARS, merged. One reader, because two callers
# each reaching into both is how the halves drift apart.
def register() -> dict[str, tuple[tuple[str, ...], str]]:
    """``FITTED_ON`` and ``FITTED_ON_UNINSTRUMENTED`` as one mapping."""
    return {**FITTED_ON, **FITTED_ON_UNINSTRUMENTED}


# A key in two registers means two different verdicts on one constant, and
# whichever is read second wins silently. Checked at import, because a register
# that contradicts itself should not survive to be printed.
_OVERLAP = sorted(
    (set(FITTED_ON) & set(FITTED_ON_UNINSTRUMENTED))
    | (set(FITTED_ON) & set(NOT_FITTED))
    | (set(FITTED_ON_UNINSTRUMENTED) & set(NOT_FITTED))
    | (set(PROVENANCE_UNSETTLED) & (set(FITTED_ON) | set(FITTED_ON_UNINSTRUMENTED)
                                    | set(NOT_FITTED))))
assert not _OVERLAP, (
    f"these constants are in more than one provenance register: {_OVERLAP}. "
    f"A constant cannot be both fitted on an election and not fitted on one, "
    f"and a reader would see whichever the code happened to check first.")


def _delivered_names(scenario) -> set[str]:
    """Names the run's value-bearing log records, or an empty set.

    ``montecarlo.delivery_log`` is the one reader for that log, so this does
    not grow a second. **It is only safe to call on a mapping that HAS the
    log**: handed a bare dict without ``_delivered`` it returns the whole dict
    as if every key in it were a recorded read, which would turn every scenario
    key into a false delivery proof.
    """
    if not isinstance(scenario, Mapping) or "_delivered" not in scenario:
        return set()
    return set(M.delivery_log(scenario) or {})


def _grade(key: str, scenario, delivered: set[str]) -> str:
    """How strong the evidence is that this run read ``key``.

    ``consulted`` — the value-bearing log records it, at a value.
    ``resolved``  — the scenario carries it and nothing recorded a read.
    ``""``        — no evidence either way.

    The distinction is ``montecarlo.assert_delivered``'s, and it is the whole
    reason there are two year-bearing registers: a ``resolved`` record says
    this process HELD the value, not that any code read it.
    """
    if key in delivered:
        return "consulted"
    if isinstance(scenario, Mapping) and key in scenario:
        return "resolved"
    return ""


def _held(scenario, keys) -> dict[str, str]:
    """``{key: grade}`` for every one of ``keys`` this run held."""
    if scenario is None:
        return {}
    delivered = _delivered_names(scenario)
    return {k: g for k in keys if (g := _grade(k, scenario, delivered))}


def _shown(scenario, key: str) -> str:
    """The value the scenario holds, short enough to print beside a name."""
    if not isinstance(scenario, Mapping) or key not in scenario:
        return ""
    text = repr(scenario[key])
    return text if len(text) <= 40 else text[:37] + "..."


def unsettled(scenario, declared_clean=(),
              target_year: str | None = None) -> list[str]:
    """:data:`PROVENANCE_UNSETTLED` keys this run held that could bite here.

    Reported, never scored. A key whose provenance nobody has settled cannot be
    called contaminated — that would be a verdict on an open question — and
    must not be quietly counted clean either, which is what the absence of this
    function used to do for every unregistered constant in the model.

    ``target_year`` filters on the entry's WORST-CASE years, so a target the
    unfavourable reading does not reach hears nothing. Omitted, every held key
    is returned.
    """
    return sorted(k for k in _held(scenario, PROVENANCE_UNSETTLED)
                  if k not in declared_clean
                  and (target_year is None
                       or any(y >= str(target_year)
                              for y in PROVENANCE_UNSETTLED[k][0])))


def contaminated(target_year: str, declared_clean: set[str],
                 read: Mapping[str, list[str]] | None = None,
                 scenario: Mapping | None = None) -> list[str]:
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

    ``scenario`` IS WHAT REACHES THE UNINSTRUMENTED HALF, and without it this
    function can only see constants somebody remembered to instrument. That
    asymmetry is the defect it was given: a scenario file declaring the eight
    instrumented keys clean bought a MEASURED all-clear at 2021 while
    ``level_shrink`` — fitted by leave-one-city-year-out over a panel
    containing that very row — came through untouched from ``DEFAULTS`` and
    was named nowhere in this file. Passed a scenario, a
    :data:`FITTED_ON_UNINSTRUMENTED` key is implicated when the run's delivery
    log records it (``consulted``) or, failing that, when the scenario simply
    carries it (``resolved``). **Omitted, those keys are not implicated at
    all** — so a caller holding only a read log gets exactly the old answer,
    and is told by :func:`in_sample_banner` that half the register went
    unchecked rather than being handed an all-clear.
    """
    keys = set(FITTED_ON) if read is None else set(read) & set(FITTED_ON)
    keys |= set(_held(scenario, FITTED_ON_UNINSTRUMENTED))
    years = register()
    return sorted(k for k in keys
                  if k not in declared_clean
                  and any(y >= str(target_year) for y in years[k][0]))


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
                     declared, read: Mapping[str, list[str]] | None = None,
                     scenario: Mapping | None = None) -> str:
    """The warning (or the all-clear) for one scenario at one target.

    Printed on every run, before the numbers, because the alternative is a
    reader taking a seat MAE of 114 for an out-of-sample result.

    ``read`` is what the run actually consumed (``ModelRun.constants_read``).
    Passing it is what makes this a measurement; without it the banner falls
    back to naming every constant that COULD be implicated, which is the
    conservative reading and the one to use if the run has not happened yet.

    ``scenario`` is the run's scenario (``ModelRun.scenario``), and it is what
    lets the banner see the constants nothing instruments.

    ⛔ **THE WORD "MEASURED" IS A CLAIM, AND IT IS NOW ONLY MADE WHEN IT IS
    TRUE.** Without a scenario this function could see only the instrumented
    half of the register and still printed ``OUT-OF-SAMPLE (MEASURED):
    Nothing this run consumed was fitted on <target> or later.`` — a false
    all-clear carrying the word MEASURED, over a register that did not contain
    the largest fitted constant in the model. There are now three all-clears
    and they say different things: MEASURED (both halves checked), PARTLY
    MEASURED (the uninstrumented half was not reachable), and NOT VERIFIED (a
    constant's provenance is an open question). Only the first is an all-clear.
    """
    clean = set(scenario_keys) if declared is not None else set()
    dirty = contaminated(target_year, clean, read, scenario)
    open_questions = unsettled(scenario, clean, target_year)
    if not dirty:
        if read is None:
            return (f"  out-of-sample (DECLARED, not verified): {label} says "
                    f"its numbers derive from "
                    f"{', '.join(str(y) for y in declared)}, all before "
                    f"{target_year}, and it sets every constant this harness "
                    f"knows to have read {target_year} or later.")
        touched = sorted(set(read) & set(FITTED_ON))
        held = _held(scenario, FITTED_ON_UNINSTRUMENTED)
        provenance = (f" It read {', '.join(touched)}, none of which reaches "
                      f"{target_year}." if touched else
                      " It read none of the constants this harness tracks.")
        if held:
            provenance += (f" It also held {', '.join(sorted(held))}, none of "
                           f"which reaches {target_year}.")
        declaration = (f"{label} declares derived_from "
                       f"{', '.join(str(y) for y in declared)}. "
                       if declared is not None else "")
        if scenario is None:
            # The half this harness could not look at is named, with its size,
            # because "I did not check" and "I checked and it was clean" are
            # the two readings a bare all-clear cannot be told apart from.
            return (f"  OUT-OF-SAMPLE (PARTLY MEASURED — "
                    f"{len(FITTED_ON_UNINSTRUMENTED)} constants NOT CHECKED): "
                    f"{declaration}Nothing this run is RECORDED as consuming "
                    f"was fitted on {target_year} or later.{provenance} No "
                    f"scenario was supplied, so the uninstrumented register "
                    f"({', '.join(sorted(FITTED_ON_UNINSTRUMENTED))}) could "
                    f"not be checked at all.")
        if open_questions:
            return (f"  OUT-OF-SAMPLE (NOT VERIFIED — provenance unsettled): "
                    f"{declaration}Nothing this run consumed was fitted on "
                    f"{target_year} or later.{provenance} But this run held "
                    f"{', '.join(open_questions)}, whose provenance the record "
                    f"states two incompatible ways; until that is settled this "
                    f"is not an all-clear. "
                    + " ".join(f"{k}: {PROVENANCE_UNSETTLED[k][1]}"
                               for k in open_questions))
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
    years_for = register()
    held = _held(scenario, FITTED_ON_UNINSTRUMENTED)
    for key in dirty:
        years, why = years_for[key]
        saw = ", ".join(y for y in years if y >= str(target_year))
        lines.append(f"    {key:<24s} read {saw} — {why}")
        users = list((read or {}).get(key) or [])
        if users:
            shown = ", ".join(users[:8])
            more = f" (+{len(users) - 8} more)" if len(users) > 8 else ""
            lines.append(f"      consumed by: {shown}{more}")
        elif key in held:
            # NOT "consumed by". Nothing instruments this read site, so what
            # can honestly be said is what the run HELD and at what value —
            # `resolved`, in the sense montecarlo.assert_delivered gives it.
            lines.append(f"      {held[key]} at {_shown(scenario, key)} "
                         f"(no read-site instrumentation)")
    # The clean reads are printed too. A banner that lists only what is wrong
    # invites the reading that everything else was measured from nothing, and
    # the interesting cases here are the ones that touch the target's own file
    # legitimately — contestation takes the ward ballot and no vote on it.
    clean_reads = sorted(((set(read or {}) & set(FITTED_ON)) | set(held))
                         - set(dirty))
    if clean_reads:
        lines.append("  Also read, and clean at this target:")
        for key in clean_reads:
            years, why = years_for[key]
            # NOT "no result". An empty tuple means no year this key reads
            # can reach the target, which `splinter_home` satisfies by having
            # its window cut at the target rather than by reading nothing.
            # Printing "read no result" beside it asserted something false
            # about a key that reads three elections.
            when = (", ".join(years) if years
                    else "nothing that reaches this target")
            lines.append(f"    {key:<24s} read {when} — {why}")
    if scenario is None:
        lines.append(f"  NOT CHECKED, because no scenario was supplied: "
                     f"{', '.join(sorted(FITTED_ON_UNINSTRUMENTED))}. Nothing "
                     f"instruments their read sites, so only the scenario can "
                     f"say whether this run held them.")
    for key in open_questions:
        lines.append(f"    {key:<24s} PROVENANCE UNSETTLED — "
                     f"{PROVENANCE_UNSETTLED[key][1]}")
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


def arrival_baseline(target, data_dir: Path) -> dict[str, float] | None:
    """**THE ONE DEFINITION OF "HAS A BASELINE" IN THIS REPOSITORY.**

    The preceding national election's citywide shares, filtered to shares above
    zero. A party absent from what this returns "arrived from nothing"; a party
    present in it did not. That is `pools.ARRIVAL_DEFINITIONS
    ["ARRIVED_VS_NATIONAL"]` — *"local share > 0 and preceding-NPE share <= 0,
    party != IND"* — read here rather than a sixth definition being invented,
    because the register exists precisely so a new site names an existing
    population instead of adding one (§1.206).

    ⛔ **THERE WERE THREE OF THESE AND THEY DISAGREED.** Every consumer of
    :func:`entrant_actual_for` built its own baseline and each built a different
    one:

      * ``compare_history._actual_seats`` passed ``{p: 1.0 for p in run.index}``
        — **the model's whole fitted universe**, so a party the pool fit had
        handed a vector to was not an arrival even with no national record at
        all. Not a registered definition, and the only one of the three whose
        answer depends on the model rather than on the world.
      * ``diagnose`` and ``backtest.main`` passed ``citywide(...)`` of the
        preceding NPE **unfiltered**, so a party carrying a row of zeroes in
        that file counted as having a baseline. Membership, not share.
      * ``compare_history._npe_baseline`` passed the same thing **filtered to
        ``> 0``**, which is the registered predicate.

    ⚠️ **AND THE SECOND AND THIRD AGREE VACUOUSLY TODAY.** Measured over all 24
    runnable city-years on 2026-09-13: **zero** parties have a preceding-NPE
    citywide total of exactly zero, so the filter removes nothing and the two
    return identical maps at every row. That is a fact about these files, not a
    property of the operation — a `0` row is one merged VD away — and it is why
    the filtered version is the one kept rather than the one dropped.

    Returns ``None``, never ``{}``, when the preceding NPE cannot be read.
    ⛔ **THE DIFFERENCE IS THE WHOLE SAFETY PROPERTY.** An empty baseline does
    not mean "nobody had a record", it means **everybody arrived** — every party
    in the council, the ANC included, becomes a newcomer, and
    :func:`entrant_actual_for` would relabel the model's generic ENTRANT onto
    the largest party in the chamber. "The record is empty" and "the record is
    unreachable" returning the same value is a fault this project has already
    published twice; here it would fail OPEN, in the most expensive direction
    available. Callers must refuse rather than proceed.
    """
    npe = getattr(target, "previous_npe", None)
    if not npe:
        return None
    path = data_dir / target.results(npe)
    if not cityconfig.resolve_path(path).exists():
        return None
    return {p: v for p, v in citywide(load(path, None)[0]).items() if v > 0}


def entrant_actual_for_target(target, actual_seats: Mapping[str, int],
                              data_dir: Path) -> str | None:
    """Which party arrived from nothing at ``target``. **The one call path.**

    :func:`arrival_baseline` then :func:`entrant_actual_for`, so no consumer has
    to know — or choose — what "from nothing" is measured against. Every caller
    that used to build its own baseline goes through here.

    ⛔ **AN UNREADABLE BASELINE RELABELS NOTHING.** Where
    :func:`arrival_baseline` returns ``None`` this returns ``None`` rather than
    treating an absent record as an empty one. The consequence is the
    conservative one and deliberately so: with no label the model's generic
    ENTRANT column stays in the scored universe as phantom mass and is PENALISED
    (``tests/test_regressions.py`` pins that case), where the failed-open
    alternative would hand the model a free correct label on the largest party
    in the council. A scorer that errs must err against the model.

    ⚠️ It answers "who", not "how well". The assignment is
    ``max(newcomers, key=seats)`` — chosen with the outcome in hand — and
    :func:`arrival_group_score` exists because of it. Nothing about routing the
    three call sites through one definition repairs that; see MODEL-LOG §1.133.
    """
    base = arrival_baseline(target, data_dir)
    if base is None:
        return None
    return entrant_actual_for(actual_seats, base)


def entrant_actual_for(actual_seats: Mapping[str, int],
                       base_city: Mapping[str, float]) -> str | None:
    """Which party actually arrived from nothing, if any.

    The model draws a *generic* entrant -- it cannot know a new party's name --
    so scoring maps ENTRANT onto whichever seat-winning party had no baseline
    at all. Anything else scores the machinery as a total miss even when it
    sized the newcomer correctly, which is the interesting question.

    ⚠️ **THIS FUNCTION DOES NOT DEFINE "HAS A BASELINE" — ITS CALLER DOES**, and
    for most of this repository's life each caller defined it differently. Take
    ``base_city`` from :func:`arrival_baseline`, or better, call
    :func:`entrant_actual_for_target` and never hold the baseline at all. An
    empty ``base_city`` makes **every** seat-winner a newcomer; it is accepted
    here because the predicate is honest arithmetic on whatever it is given, and
    refused one level up where the difference between "empty" and "unreadable"
    is knowable.
    """
    newcomers = {p: s for p, s in actual_seats.items() if p not in base_city}
    # DETERMINISTIC TIE-BREAK. `max(newcomers, key=newcomers.get)` returns the
    # first maximum in ITERATION ORDER, which for a dict built from a file scan
    # depends on insertion order and, where keys collide, on PYTHONHASHSEED. Two
    # identical `compare_history` runs produced three different JSON hashes and
    # a ranks-13+ absolute band of 15.2164 / 15.2164 / 15.3080 — so the
    # nine-city-year scoreboard that decides what ships was not reproducible
    # run to run, and every A/B measured against it carried an unquantified
    # floor on top of the seed noise.
    #
    # Sorting by (seats, name) makes the choice a stated rule instead of an
    # accident. It does not make the choice RIGHT: where two arrivals genuinely
    # tie, the generic ENTRANT column is relabelled onto one of them and the
    # other scores as missed entirely, whichever way the tie falls. What the
    # relabel should do with a real tie is an open question (MODEL-LOG §1.41);
    # this only stops the answer changing between runs.
    return max(newcomers, key=lambda p: (newcomers[p], p)) if newcomers else None


def arrival_group_score(pr_share_draws, seat_draws, index,
                        actual_shares, actual_seats, base_city) -> dict:
    """Score the arrival channel as a GROUP, with **no per-party label**.

    ⛔ **THIS EXISTS BECAUSE THE EXISTING SCORE HANDS THE INCUMBENT THE ANSWER
    KEY.** `entrant_actual_for` maps the model's nameless `ENTRANT` column onto
    ``max(newcomers, key=seats)`` — **the seat-winning newcomer with the most
    seats, chosen with the outcome in hand.** A nameless column must be assigned
    to something, but that is the most favourable assignment available, and
    `montecarlo`'s own comment concedes what it buys: *"the slot it replaces was
    scoring well for a reason that is not skill: it is relabelled onto the
    LARGEST arrival, so a single lump of mass lands on exactly the right party
    after the fact."*

    It is the same class of fault as the `claimed` population selecting away
    from the forecaster's own failures, which `ITERATING.md` rule 8 identified
    and fixed by introducing `reference`. It was never fixed here — **so the
    CRPS 85.9 → 109.9 that rejected the group arrival mechanism is not a fair
    comparison, and Key 1 cannot currently arbitrate this channel at all.**
    MODEL-LOG §1.133.

    The label-free quantity: **total mass and total seats taken by parties with
    no baseline**, forecast against realised. It assigns nothing, so it cannot
    be gamed by the assignment; it is computable on every cycle; and it is
    exactly what `pools.arrival_group_spec` forecasts. Report it BESIDE the
    relabelled score as a sensitivity pair — the same shape as the clip
    sensitivity in `compare_history._band_splits` — never instead of it, because
    the pair is the finding.

    Returns per-draw group totals summarised, plus the realised totals. A `nan`
    for `mass_pit` means **the MODEL held no arrival column** — there was nothing
    to draw, so there is no predictive distribution to take a PIT in. That is a
    legitimate outcome and not a missing measurement.

    ⚠️ **It does NOT mean "no party arrived".** The realised side is selected
    independently, from the whole PR ballot, so `actual_mass` can be non-zero on
    exactly those city-years — and reading the `nan` as "nothing arrived here"
    would code a model-side absence as a fact about the world. `NULL-RESULTS.md`
    calls that a PHANTOM null; four of sixteen city-years produced one under the
    previous outcome-selected rule. §1.136.
    """
    import numpy as _np

    # ⛔ THE ACTUAL SIDE IS SELECTED FROM THE BALLOT, NOT FROM THE SEAT WINNERS.
    # It read `actual_seats` until 2026-08-29, and `actual_result` filters that
    # to `s > 0` (see :func:`actual_result`) — so the realised arrival TOTAL
    # counted only arrivals that won a seat, while the forecast side summed
    # every arrival column the model holds. That is denominator drift with the
    # outcome on one side of it, and it points the same way as the rig this
    # function exists to remove: at Johannesburg 2021 there are 32 arrival
    # columns and 3 seat-winners, so the filter deleted precisely the parties
    # the GROUP mechanism forecasts and the single-slot incumbent does not.
    # Measured across the panel: realised mass understated in all 16
    # city-years, and *exactly zero* in four of them against a true arrival
    # mass of 0.31–1.75pp. `actual_shares` is `citywide(pr)` over every party
    # on the PR ballot, so selecting from it makes both sides input-selected.
    # MODEL-LOG §1.136.
    arrived = [p for p in actual_shares if p not in base_city and p != INDEPENDENT]
    names = [p for p in index if p not in base_city and p != INDEPENDENT]
    cols = [index[p] for p in names]
    out = {"n_arrived": len(arrived), "n_columns": len(cols),
           "actual_mass": float(sum(actual_shares.get(p, 0.0) for p in arrived)),
           "actual_seats": int(sum(actual_seats.get(p, 0) for p in arrived))}
    if not cols:
        out.update(mass_mean=0.0, seats_mean=0.0, mass_pit=float("nan"),
                   seats_pit=float("nan"), mass_median=0.0, seats_median=0.0,
                   mass_err=out["actual_mass"], seats_err=float(out["actual_seats"]),
                   seats_outside_support=bool(out["actual_seats"] > 0))
        return out
    mass = _np.asarray(pr_share_draws)[:, cols].sum(axis=1)
    # ⛔ BY NAME, NOT BY COLUMN. `seat_draws` is `list[dict[str, int]]`
    # (montecarlo.ModelRun), NOT the (draws, parties) array `pr_share_draws`
    # is. Indexing it `[:, cols]` raised `IndexError` on every city-year, so
    # `compare_history` caught it per city-year and printed `nothing runnable`
    # — this referee had never produced a number on real input. The unit test
    # missed it by handing in a dense 2-D fixture production never builds.
    # `relabel_run` rewrites `seat_draws`' keys too, so both orderings agree.
    seats = _np.array([float(sum(d.get(p, 0) for p in names))
                       for d in seat_draws])
    # PIT of the realised total in the drawn total's distribution, mid-rank on
    # the atom. ⚠️ Mid-rank does NOT remove saturation: if the realised total
    # exceeds every draw, `seats_pit` is exactly 1.0 — which is the ActionSA
    # case this score exists to measure, so it is reported, not hidden, and
    # `seats_outside_support` flags it. A mid-P PIT is also UNDER-dispersed
    # against uniform, so it must not be pooled through `_probit` without
    # randomisation. MODEL-LOG §1.136.
    out.update(
        mass_mean=float(mass.mean()), mass_median=float(_np.median(mass)),
        seats_mean=float(seats.mean()), seats_median=float(_np.median(seats)),
        mass_pit=float((mass < out["actual_mass"]).mean()
                       + 0.5 * (mass == out["actual_mass"]).mean()),
        seats_pit=float((seats < out["actual_seats"]).mean()
                        + 0.5 * (seats == out["actual_seats"]).mean()),
        seats_outside_support=bool(out["actual_seats"] > seats.max()
                                   or out["actual_seats"] < seats.min()),
        mass_err=float(out["actual_mass"] - mass.mean()),
        seats_err=float(out["actual_seats"] - seats.mean()))
    return out


def relabel_run(run, entrant: str | None):
    """Rename the generic ``ENTRANT`` **on the run itself**, once, in place.

    :func:`relabel_entrant` fixed ward probabilities and ``score_seats`` has
    taken ``entrant_actual`` since it was written, but every *other* consumer
    read the raw run — and so scored the arrival machinery as a double error.
    Measured on Johannesburg 2016, where the AIC arrived and took 1.62% and 4
    seats: the generic entrant drew **1.39% and 3.82 seats**, which is close to
    right, and ``compare_history`` recorded the AIC's vote as ``NaN`` ("missed
    entirely"), *and* counted 4 phantom ENTRANT seats — 8 seats of error on a
    forecast that was correct. The rank bands lost the 1.39pp too, all of it out
    of ranks 4-12, which is the band this model is already short in.

    This is the same class of fault as the turnout band capped at the observed
    maximum: not the model being wrong, the *instrument* being wrong, in exactly
    the runs used to judge the model. So the relabel happens once, at the source,
    and every downstream helper inherits it rather than each remembering.

    Merges rather than renames when the arrived party somehow already holds a
    column (a seeded splinter that also had no baseline), because two columns
    for one party would double-count it.
    """
    if not entrant or "ENTRANT" not in run.index:
        return run
    src = run.index["ENTRANT"]
    dst = run.index.get(entrant)

    if dst is None:                                   # the usual case: rename
        run.index = {(entrant if p == "ENTRANT" else p): i
                     for p, i in run.index.items()}
        run.universe = [entrant if p == "ENTRANT" else p for p in run.universe]
    else:                                             # merge into the column it has
        for arr in (run.pr_share_draws, run.ward_share_draws):
            if arr is not None:
                arr[:, dst] += arr[:, src]
                arr[:, src] = 0.0
        if run.ward_winner_counts is not None:
            run.ward_winner_counts[:, dst] += run.ward_winner_counts[:, src]
            run.ward_winner_counts[:, src] = 0

    for d in run.seat_draws:
        n = d.pop("ENTRANT", 0)
        if n:
            d[entrant] = d.get(entrant, 0) + n
    for book in (run.ward_win_sum, run.overhang_count):
        n = book.pop("ENTRANT", 0)
        if n:
            book[entrant] = book.get(entrant, 0) + n
    run.notes[entrant] = (run.notes.pop("ENTRANT", "")
                          + " | generic entrant, relabelled for scoring").strip(" |")
    return run


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

    # THE ONE CALL PATH. This built its own baseline — `citywide(load(...))` of
    # the preceding NPE, unfiltered — and `diagnose` built the same one again
    # while `compare_history` built two others. See `arrival_baseline`.
    entrant = entrant_actual_for_target(target, actual_seats, args.data_dir)

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
        # BOTH, and the second is the one that was missing. `constants_read`
        # covers only what `note_constant` instruments; the run's own scenario
        # is the only evidence this harness has about every other constant it
        # resolved — `level_shrink` among them.
        in_sample = bool(contaminated(
            target.year, set(overrides) if declared is not None else set(),
            read, run.scenario))
        print()
        print(in_sample_banner(target.year, label, set(overrides), declared,
                               read, run.scenario))
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
    M.fix_hash_seed()          # may replace the process; see `fix_hash_seed`
    raise SystemExit(main())
