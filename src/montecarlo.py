"""Monte Carlo forecast of a metro council (plan §3.4–§3.8, review fixes).

Draws a scenario, runs it through the share model at VD level, aggregates
both ballots, predicts ward winners, allocates seats under Schedule 1 with the
overhang check, and reports the full coalition arithmetic. The deliverable is
a distribution over coalition viability, never a point forecast (§4.3).

**The target election is a parameter.** ``--target`` selects it and everything
that depends on when it is — the baseline NPE, the previous local election, the
council's size, the polling day the by-election decay counts back from, which
γ fold may be read, where the outputs land — resolves off
``cityconfig.Target`` rather than off constants written into this file. That is
what lets ``backtest.py`` score *this* model at 2011, 2016 or 2021 instead of a
second, reduced reimplementation of it: the model function below is the only
one there is. See :func:`run_model` for what a past target can and cannot be
given (by-election evidence and split-VD apportionment are the two gaps, and
both are gaps in the record rather than omissions here).

This is a rewrite of the first implementation, fixing the review findings:

* **E1** — coalition arithmetic is fully enumerated (`coalitions.py`): every
  subset, minimal winning coalitions, Banzhaf/Shapley–Shubik, and the
  minority-government class. No pre-filtering on political plausibility.
* **E2** — the within-pool split is centred on the plan's §3.5 θ modes (its
  deliberate per-party views: MK 0.60, ANC 0.75), not on 2024 proportions,
  which silently discarded them. Implied per-party θ is checked against
  §3.5's ranges and the violation rate reported — the "sanity bounds" the
  plan promised.
* **E3** — ward winners are predicted per draw from the ward-ballot shares;
  overhang expands the council and moves the majority threshold (plan §3.7
  step 5). Threshold is per-draw, not a constant 136.
* **E4** — by-election evidence (`byelections.py`, plan §3.6) tilts each
  party's central level at weight ``w_bye``, clamped to §3.5's ranges so a
  concentrated party's stronghold deltas cannot claim an absurd citywide
  level (the A4 selection caveat, enforced numerically). A polling lever
  spans the SRF↔Ipsos disagreement (§8.3): ±1 moves the pool modes ±4 points,
  the modes stay clamped to their historical ranges.
* **E6** — minor parties draw *independent* θ from ranges set around their
  observed NPE→LGE ratios (fold 1 and fold 2), not one shared f_other draw
  that moved them in lockstep and produced two-seat "90% intervals".
* **A1** — ward/PR split-ticket ratios are per-party from 2021 with explicit
  overrides: MK (absent in 2021, list party without ward machinery) defaults
  to 0.80 rather than a silent 1.0; the PA's ratio carries a contestation
  uplift for fielding more than 2021's 52 ward candidates.
* **A2** — turnout is uncertain per draw: a blend between the λ̂ ratio-form
  pattern and the 2021-LGE-level pattern (the two candidates from MODEL-LOG
  1.2), plus VD-level noise. The citywide level cancels in seats (MODEL-LOG
  1.10); this varies the *differential* pattern, which does not.
* **A4** — γ falls back to the 2021→2024 fit (`gamma_recent.py`) before 1.0.
  ActionSA's fitted γ is 0.49, not the 1.0 the first build assumed.
* **A6** — an optional generic-entrant slot: with some probability a party
  absent from every baseline appears at a drawn citywide share, spatially
  flat. Every backtest fold and the live case contained such an entrant; a
  forecast that cannot is overconfident by construction.

Every knob lives in ``DEFAULTS`` and can be overridden with ``--config
scenario.json`` or ``--set key=value`` — the same schema the interactive
forecast page exposes, so a slider position there is reproducible here.

Usage:
    python src/montecarlo.py [--draws 5000] [--seed 20261104]
                             [--config file.json] [--set w_bye=0.0] ...
    python src/montecarlo.py --target 2021    # the same model, built for 2021
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import numpy as np

import cityconfig
import coalitions
from fold import FOLDS, citywide, load, load_parameters, shares
from seats import INDEPENDENT, allocate

SHARE_FLOOR = 0.002
COUNCIL = 270

# Keeps every Dirichlet concentration strictly positive, which is all numpy
# needs and all this is for. See the note at its use site in make_drawer: the
# previous value, 0.05, was a claim rather than a guard and was manufacturing
# several points of citywide vote for parties the model itself puts near zero.
DIRICHLET_FLOOR = 1e-4

# POLL_K WAS DELETED HERE, 2026-08-22 (MODEL-LOG §1.68), with the legacy poll
# path it served. It keyed a poll's weight on how much θ HISTORY a party had —
# m/(worth+m) — which §1.67 replaced with how PRECISE the two estimates are.
# The shape survives: `poll_house_k` uses the same m/(k+m) form, keyed on how
# many independent HOUSES stand behind a poll rather than on the party.

# Blocs are gone. They were two hand-drawn lists of parties assumed to trade
# votes with each other — a claim about parties, made by a person, that no
# measurement could check. Parties are now described by the voter pools they
# draw from (``src/pools.py``), which is a claim about the electorate and can
# be measured, bounded and falsified. See MACHINERY.md §0.

# §3.5 raw-θ ranges: the plan's sanity bounds on any derived per-party value,
# and the clamp on what by-election or polling evidence may claim.
PLAN_BOUNDS = {
    "ANC": (0.65, 0.90), "DA": (1.05, 1.60), "EFF": (0.55, 1.10),
    "ASA": (0.90, 3.00), "MK": (0.30, 1.00), "PA": (1.00, 2.20),
    "ALJAMAAH": (0.80, 3.00),
}

DEFAULTS: dict = {
    "draws": 5000,
    "seed": 20261104,



    # E4: by-election blend weight (§3.5 w_bye, range 0–1). Polls: pick one
    # from polls.json by id and weight it — this replaced the old two-endpoint
    # polling_lean lever, which was kept "for compatibility" and deleted
    # 2026-08-17 once CLASS 12 showed it was computed, passed to `pool_spec`
    # as an argument that function never read, and printed. Three appearances,
    # no effect. See MODEL-LOG §1.35.
    "w_bye": 0.40,

    # HOW MUCH A PARTY'S WARD SLATE GROWS BETWEEN LOCAL ELECTIONS, used ONLY
    # where the target's own nomination lists are not published — which is
    # every live forecast and no backtest. `levels.contestation` reads the
    # target's result file for who stood; at 2026 that file does not exist, so
    # until now the contestation correction was silently the IDENTITY, i.e. an
    # unexamined assumption that every party fields exactly the slate it fielded
    # five years ago. This makes that assumption a number someone chose.
    #
    # The projection is `now = was + expand * (1 - was)`: each party moves this
    # fraction of the way from its previous slate to a full one. 0.0 restores
    # the old identity; 1.0 puts every party in every ward.
    #
    # MEASURED, not typed. Across the eight metros and every consecutive LGE
    # pair on disk (n=165 parties present at both), the median party moves
    # **+0.220** of the way to a full slate and **65.5% expand**. The most
    # recent transition alone (2016->2021) is much stronger — per-metro medians
    # of +0.46, +0.14, +0.78, +0.59, +0.63, +0.20, +0.71, +0.06, so about +0.5 —
    # which is what a fragmenting party system looks like. 0.220 is the
    # conservative reading and the one shipped; 0.5 is the defensible
    # alternative and is why this is a lever rather than a constant.
    #
    # **ARGUED, NOT TESTED, and live exactly where nothing can check it.** This
    # is the same position `pa_contestation_uplift` was in, and that constant
    # survived for weeks because the one branch it fired on was the one branch
    # no backtest reaches. The difference is that this one is declared, measured
    # against the record, and inert the moment real nomination lists exist —
    # see `levels.projected_contestation` and JUDGEMENT-CALLS.md.
    "contestation_expand": 0.220,
    # §1.28 ward-local by-election term. Both weights default to 0, so the
    # published forecast is untouched until this is deliberately switched on.
    # The ward ballot carries most of the signal because a by-election IS a
    # ward contest; the same ward's list vote gets roughly half, because the
    # evidence about list voting is real but weaker; and no ward but the one
    # that held the contest is touched. The cap is in logit units and is a
    # working constraint on the largest movers, not a freak guard: measured on
    # byelection_contest_detail.csv, 1.5 binds on 11 of the 65 party-contest
    # rows that have a share on both sides, spread across 9 of the 15 contests
    # -- among them the DA at +2.83 in ward 99, +2.69 in ward 90 and +2.47 in
    # ward 89. A by-election routinely turns a ward's own baseline over that
    # hard, so this dial decides how much of a real landslide the forecast is
    # allowed to believe, and raising it is a substantive change rather than
    # slack. τ is the same recency half-life the citywide term uses.
    "w_bye_local_ward": 0.0,     # 0.75 is the value tested
    "w_bye_local_pr": 0.0,       # 0.35 is the value tested
    "bye_local_cap": 1.5,
    "bye_tau_months": 18.0,
    # WHICH POLL PATHS RUN, so the channel can be scored. There are two live
    # ones and they answer different questions: "arrivals" is a national poll
    # converted to a contested area, for parties with NO record at all;
    # "all" adds the metro-poll inverse-variance blend, which touches every
    # party a poll of THIS city names.
    #
    # It exists because until 2026-08-21 the only way to switch the channel off
    # was to empty `polls.json` — so the one thing nobody had ever done was
    # measure what it is worth. `backtest.FITTED_ON` declares both paths
    # leak-free and neither has ever been scored. MODEL-LOG §1.65.
    "poll_paths": "all",    # "off" | "arrivals" | "all"

    # HOW MUCH TO BELIEVE THE POLLS, as a continuous dial rather than a switch.
    #
    # Multiplies the metro-poll blend weight `w` before it is applied, then
    # clamps to [0, 1]. **1.0 is the identity and the shipped default**, so
    # adding this moves no number: it is the sigma arithmetic's own answer,
    # untouched. 0.0 ignores metro polls entirely (the metro half of
    # `poll_paths="off"`); above 1.0 leans in.
    #
    # WHY A DIAL AND NOT A SWITCH. Polls do three jobs here and the backtest
    # scores only one of them. As a forecast INPUT the channel currently
    # measures **−6 coherent seats** on sixteen city-years (§1.94). As an
    # EXTERNAL CHECK that the model is in the ballpark they are the only
    # independent reading we have, and that job is unscoreable by construction.
    # And in the interactive a reader must be able to say how much they believe
    # a given house. A binary switch cannot express any of that, and −6 is
    # evidence that the *weighting* is wrong, not that the polls are empty.
    #
    # Scoped to the METRO blend deliberately. The arrivals path is a route
    # precedence in `blended_centres`, not a blend — for a party with no local
    # record there is no alternative estimate to blend against — so credence has
    # no meaning there and `poll_paths` remains its switch.
    #
    # DECLARED, and pending a paired sweep across the panel to find the value
    # the backtest supports. Until that lands, 1.0 is the incumbent and not a
    # recommendation.
    "poll_credence": 1.0,

    # THE POLL WEIGHTING'S JUDGEMENT CALLS, every one of them adjustable.
    # These are DECLARED numbers — none is measured and none can be until a
    # second house publishes a Johannesburg metro poll — so per the standing
    # rule they are noted in JUDGEMENT-CALLS.md *and* reachable from `--set`,
    # a config file, the sweep and the interactive. A judgement call nobody can
    # move is indistinguishable from a fact, which is how `POLL_HOUSE_K` came
    # to ship at 1.4 for a day with no reason anyone could check. §1.67.
    #
    # `poll_house_k` is the one to argue with: it caps a poll at
    # H_eff/(H_eff+k), so 1.0 means "a single unreplicated house is never worth
    # more than the model itself" and 1.4 (the value it shipped at) means 0.42.
    "poll_house_k": 1.0,
    "poll_deff_subsample": 1.6,
    "poll_screen_sd": 0.020,
    "poll_drift_per_root_day": 0.0010,
    "poll_min_n": 300,      # below this a poll is recorded, never admitted

    # RECENCY HALF-LIFE for combining poll waves. It was registered in
    # JUDGEMENT-CALLS.md at 120 and DID NOT EXIST — a default argument on
    # `polling.aggregate`, so no `--set` and no config file could reach it, and
    # the register documented a constant that was not there. Mirrored here and
    # asserted equal to `polling.POLL_HALF_LIFE_DAYS` at import. §1.67.
    "poll_half_life_days": 120.0,


    # §1.29 weighted pools — the engine. Each pool: members {party: the share
    # of that party's vote drawn from this pool, summing to 1 across pools per
    # party}, a `ratio` triangular on the base, and an `alpha`. Left empty here
    # because it is not a judgement to be typed: `run_model` loads the measured
    # spec that `python src/pools.py --emit` writes, and refuses to run without
    # one. Splinter and entrant lineage is settled there too — a splinter
    # inherits its parent's pool vector, an entrant defaults to an even share
    # of every pool, and both are overridable in judgements/{city}-{target}.toml.
    "pools": {},

    # A2: turnout pattern per draw. blend 0 = pure λ̂ ratio form, 1 = pure
    # 2021-LGE-level pattern; the draw jitters the blend ±jitter and applies
    # per-VD lognormal noise (σ in log units ≈ the unexplained λ dispersion).
    "turnout_pattern_blend": 0.5,
    "turnout_blend_jitter": 0.25,
    "turnout_noise_sd": 0.08,

    # A6: generic-entrant slot. Off by setting probability to 0.
    # THE ARRIVAL-GROUP DRAW, and until 2026-08-20 this key DID NOT EXIST.
    #
    # `blended_centres` reads `scenario.get("arrival_group_draw")` to decide
    # between the arrival-group mechanism — a group total drawn from a fitted
    # lognormal and split among named arrivals by a Dirichlet — and the generic
    # `ENTRANT` slot, which is a Bernoulli times a triangular. The comment there
    # says "DEFAULT OFF" and `MACHINERY.md` lists it among the switched-off
    # levers. **There was no switch.** The key was in no `DEFAULTS`, so
    # `scenario.get` returned None on every run; `parse_set` and
    # `read_scenario_file` both reject a key that is not already in the
    # scenario, so `--set` and a config file could not create it either. The
    # mechanism was not off, it was unreachable, and the code comment scheduling
    # a retry "by 2026" scheduled something that could not be done.
    #
    # Same class as `LEVEL_DF` bound as a default argument (§1.33) and
    # `polling_lean` passed to a function that never read it: a lever that
    # cannot move. It escaped `test_every_defaults_key_is_swept_or_excused` and
    # `test_every_tunable_lever_actually_moves_the_forecast` for the one reason
    # neither can catch — those iterate `DEFAULTS`, and this was not in it.
    #
    # Declared here so it is reachable, sweepable and registered. Still False:
    # what changes is that "off" is now true rather than merely written down.
    # MODEL-LOG §1.63.
    "arrival_group_draw": False,

    # TWO MORE KEYS THAT WERE READ AND NEVER DECLARED, found by the same guard
    # (§1.63). Both were `scenario.get(key, <hardcoded fallback>)`, so both were
    # frozen at the fallback and unreachable from `--set` or a config file — a
    # registered constant that cannot be swept is `LEVEL_DF` again.
    #
    # Declared at exactly the values they were already frozen at, so nothing
    # moves. What changes is that they can now be swept, and that the guards can
    # see them.
    "level_sd_default": 0.45,
    "turnout_correlation": 0.63,   # == TURNOUT_CORRELATION, asserted below

    "entrant_prob": 0.25,
    "entrant_share": [0.01, 0.04, 0.12],
    # Whose map does the 2026 entrant inherit, and how far does it depart from
    # it (§1.27)? Empty keeps the flat default. {"parent": "ANC", "k": 0.05}
    # would place it like the EFF placed itself in 2014. Observed k across the
    # entrants on record spans 0.03 to 1.16, so for a party nobody has seen yet
    # this is genuinely unknown — the honest default is flat, stated as a
    # choice rather than left implicit.
    "entrant_geography": {},

    # E3: what to do when a party wins more wards than its entitlement.
    # "expand" = the plan §3.7 reading (council grows, threshold moves);
    # "cap" = counterfactual with the council fixed at 270 (entitlement
    # honoured, excess ward wins not); "deduct" = third reading (audit
    # 2026-08-05): overhang party keeps its wards, council stays 270, the
    # OTHER parties' entitlements are re-allocated over the remaining seats,
    # threshold stays 136. RESOLVED 2026-08-05 (MODEL-LOG 1.17): "deduct" is
    # the law — Amendment Act 3 of 2021, Schedule 1 item 16(3)-(9), applied by
    # the IEC in Laingsburg 2021. "expand" kept as labelled counterfactual.
    "overhang_rule": "deduct",

    # Audit 2026-08-05: ward winners were deterministic given a citywide draw,
    # overstating P(overhang) confidence. Lognormal noise (log-sd) applied to
    # each ward x party tally before calling winners; 0 = old behaviour.
    "ward_noise_sd": 0.10,  # adopted 2026-08-06: audit suite showed headlines stable, P(excessive) honestly softened

    # Audit 2026-08-05: the SHARE_FLOOR clamp on the *level* term makes
    # citywide shares below ~0.2% unattainable, inflating the micro-party
    # tail. Lowering this floor (e.g. 1e-6) frees the level while keeping the
    # 0.002 floor on deviation inputs. Default keeps published behaviour.
    # See DIRICHLET_FLOOR. A scenario key so the sweep that chose it is
    # reproducible and so a reader can put the old behaviour back.
    "dirichlet_floor": DIRICHLET_FLOOR,
    # How much θ evidence a party needs before the national spine is trusted
    # over its own last local result; the weight on the LOCAL route is
    # k/(worth+k). A scenario key rather than only a module constant, so it can
    # be swept -- levels.SPINE_K is a DEFAULT ARGUMENT and rebinding the module
    # attribute after import silently does nothing, which cost one experiment.
    "spine_k": None,
    "level_floor": 0.000001,  # adopted 2026-08-06: frees sub-0.2% targets; structural rows barely move
    # THE LEVEL SHRINK. How hard a party's central level is pulled down by its
    # own size, and the share at which that pull reaches half strength.
    # ADOPTED 2026-08-17 at nine city-years and 1500 draws: coherent seat error
    # 312 -> 264, CRPS 264.8 -> 236.4, beats-uniform-swing 6/9 -> 8/9. The
    # value is NOT from those nine -- fitted on Johannesburg 2016 alone it
    # gives 0.375 and transfers to the eight 2021 metros. Set `level_shrink` to
    # 0.0 to recover the previous model exactly; 0.0 is the identity in
    # `compress_levels`. See MODEL-LOG §1.44.
    "level_shrink": 0.35,
    "level_shrink_scale": 0.04,
    # Multiplier on the fitted per-pool Dirichlet concentration; 1.0 is the
    # fit itself. See `_dirichlet_scale` and MODEL-LOG §1.55.
    "dirichlet_scale": 1.0,
}

# What DEFAULTS looked like before any city touched it. `apply_city` restores
# from this, so a city never inherits the previous city's judgements and the
# scoreboard cannot depend on the order the cities were looped in.
_PRISTINE_DEFAULTS = copy.deepcopy(DEFAULTS)


def logit(p, floor=None):
    # Resolved at call time; see `log_shock` and MODEL-LOG §1.33.
    #
    # THE CEILING HONOURS `floor` SINCE 2026-08-28 (§1.97 F13). It was
    # `1 - SHARE_FLOOR` whatever was passed, so `logit(p, floor=1e-6)` clipped
    # asymmetrically at [1e-6, 0.998] — the argument moved one end of the
    # interval and not the other.
    #
    # NUMBER-NEUTRAL, MEASURED RATHER THAN ASSUMED: instrumented across all
    # sixteen backtest city-years, the largest value ever passed here is
    # **0.983** (ethekwini 2016; joburg's worst is 0.932) against a ceiling of
    # 0.998, and the count of cells above that ceiling is **zero**. Neither
    # form of the clip binds at the top on any input this model has.
    #
    # `fold.logit` and the JS engine in `interactive_template.html` carry the
    # SAME asymmetry and are deliberately NOT changed here. `fold.logit` feeds
    # precomputed artefacts (`fold{N}_parameters.csv`, `gamma_recent.csv`), so
    # changing it is inert until those are regenerated and then is not; and
    # `audits/model-audit-2026-08-06-second-round.md` certifies the JS and
    # Python floors as matching, so a one-sided change there would falsify a
    # standing audit. All three are unreachable at the top end, so the
    # divergence costs nothing today — but it is a divergence, and it is
    # recorded rather than left to be discovered.
    floor = SHARE_FLOOR if floor is None else floor
    p = np.clip(p, floor, 1 - floor)
    return np.log(p / (1 - p))


def expit(x):
    return 1.0 / (1.0 + np.exp(-x))


def triangular(rng, spec, size=None):
    low, mode, high = spec
    return rng.triangular(low, min(max(mode, low), high), high, size)


# Degrees of freedom for the level shock.
#
# WAS 4.0, AND 4.0 IS INDEFENSIBLE. exp(c·t_v) has an INFINITE MEAN whenever
# v <= 2/c² is false in the wrong direction — concretely, the t₄ density's |t|⁻⁵
# tail loses to the exponential and no moment exists. Measured over 400,000
# draws at df=4:
#
#     sd handed in   median   sample mean       p99.9        max
#     0.26            1.000        46,591        3.71    1.9e+10
#     0.72            1.001           859       39.33    3.4e+08
#     1.20            0.998     4,709,109      429.33    1.9e+12
#
# The median is perfect and the mean is nonsense, which is exactly the failure
# mode that hides: every summary this repository reports as a "mean" — the vote
# tables in compare_history, the arrival sizes in arrivals.py, and above all the
# MEAN SEAT VECTOR that coherent_seats apportions by largest remainder — was
# being computed on a statistic that does not exist. It is also why small
# parties showed mean/median ratios of 6x to 10x where a lognormal of the same
# sd gives about 2x.
#
# At df=7 the same draws give means of 1.03, 1.35 and 2.93. Support is still
# unbounded and the tail is still far heavier than a normal's, so the reason the
# shock exists at all is intact.
#
# A bounded triangular assigns
# probability EXACTLY ZERO outside its support, and this model kept doing that
# to outcomes that had already happened — Al Jama-ah won a Johannesburg seat in
# 2016 with 0 of 500 draws non-zero, which is an infinite log score for an event
# in the record. Student-t in log space has unbounded support and a tail heavy
# enough that a party trebling is unlikely rather than impossible. Four degrees
# of freedom keeps the variance finite (so the measured sd still means what it
# says) while putting roughly 2% of the mass beyond 3.7 sd, against a normal's
# 0.02% — two orders of magnitude more room for the surprise this model has
# repeatedly been surprised by.
# THE ADMISSION GATE ON THE WHOLE BY-ELECTION CHANNEL, promoted from an
# inline literal 2026-08-22 (MODEL-LOG §1.69). `w_bye` = 0.40 is registered at
# 🔴 as "live in the 2026 forecast, untested by anything here" — and the
# threshold deciding whether it fires for a given party was a bare `30` in the
# function body, in the same untestable branch and with the same reach into the
# published forecast. Below this many weighted contests the by-election
# evidence is discarded in silence.
BYE_MIN_WEIGHT = 30.0

# FLOOR AND CEILING ON PER-VD TURNOUT IN EVERY DRAW. Promoted from inline
# literals in the same pass. Note that JUDGEMENT-CALLS §C describes the turnout
# band as one that "REMOVES caps rather than adding one — no observed-maximum
# cap, no 1.0 cap". These two are caps, they are applied per draw, and the
# register did not know they existed.
TURNOUT_DRAW_FLOOR = 0.02
TURNOUT_DRAW_CEILING = 0.95

# CLIP ON THE WARD/PR SPLIT-TICKET RATIO, which multiplies the PR target to
# make the ward target and therefore drives ward wins and overhang.
# JUDGEMENT-CALLS §E lists "ward/PR split ratios" as coming FROM THE RECORD;
# this is the clip that overrides the record when it disagrees, and it was
# undeclared.
WARD_PR_RATIO_MIN = 0.5
WARD_PR_RATIO_MAX = 2.0

LEVEL_DF = 7.0


def log_shock(rng, sd, size=None, df: float | None = None):
    """exp of a Student-t scaled to have log-sd exactly ``sd``. Median 1.

    Standardised by sqrt((df-2)/df) so that ``sd`` is the realised log standard
    deviation rather than the t's own, which would be 41% larger at df=4. The
    measured sd(log θ) can then be handed straight in and mean what levels.py
    measured it to mean.

    ``df`` RESOLVES ``LEVEL_DF`` AT CALL TIME, and it must. It was written
    ``df: float = LEVEL_DF``, which Python evaluates once at import: setting
    ``montecarlo.LEVEL_DF`` afterwards changed nothing at all, and the constant
    was swept at 2.5, 4, 7, 30, 200 and 1000 for byte-identical output every
    time. That reads as "the tail does nothing" when the truth is "you did not
    change the tail" — the exact trap ITERATING.md rule 6 exists for, and the
    same class of defect as `entrant_prob` in MODEL-LOG §1.31. See §1.33.
    """
    df = LEVEL_DF if df is None else float(df)
    scale = np.sqrt((df - 2.0) / df)
    sd = np.asarray(sd)
    # SIZE DEFAULTS TO THE SHAPE OF sd. Passing an array of per-party spreads
    # with size=None gave every party the SAME t draw — one scalar broadcast
    # across the vector — so the shocks were perfectly correlated. A common
    # multiplicative shock cancels exactly under the normalisation that follows,
    # which is why the ANC and DA realised sd(log) 0.08 against a measured 0.21
    # while a small party, whose share barely moves the normaliser, realised its
    # own. The level shock existed and did nothing for precisely the parties it
    # was added for.
    if size is None and sd.ndim > 0:
        size = sd.shape
    return np.exp(sd * scale * rng.standard_t(df, size=size))


# How close to a party's own pool capacity the IPF is allowed to be asked to
# go. A party can take at most every vote cast in the pools it belongs to, so
# asking for more is not a hard problem but an IMPOSSIBLE one, and
# `pools.balance_margins` runs to its iteration cap and raises. Asking for
# exactly the capacity is only marginally better: IPF approaches a boundary
# solution geometrically, so the last percent costs more iterations than the
# whole rest of the fit. The margin buys the fit somewhere to converge to.
#
# 0.98 is typed. Swept on the 2026 forecast at 600 draws, the per-draw failure
# rate is 41.5% at margin 1.0000, 41.5% at 0.9999, 39.8% at 0.995, 37.0% at
# 0.991 — and 0.0% at 0.990 and at 0.980. That is a cliff, not a slope: inside
# about 1% of the boundary, `balance_margins`' 2000 iterations cannot reach its
# 1e-12 tolerance, so the last percent is a convergence-rate problem and the
# safe margin is a function of the iteration cap. 0.98 keeps a full step in
# hand. Its cost is that a party pinned at capacity is forecast 2% below the
# level the centres asked for — the correct direction (the level is
# unreachable) but not a measured amount. See MODEL-LOG §1.33.
POOL_CAPACITY_MARGIN = 0.98


def capped_targets(target: np.ndarray, cap: np.ndarray) -> np.ndarray:
    """Hold every column target under its cap WITHOUT changing the total.

    Water-filling. Clip the columns above their cap, then hand the freed mass
    to the columns that still have room, in proportion to what they already
    hold, and repeat until nothing is over. Each pass fixes at least one more
    column at its cap, so it terminates.

    A NAIVE CLIP DOES NOT WORK, and both of the places that would have taken
    one immediately undo it:

    * ``pool_spec`` clipped at the ceiling and then wrote ``want = want /
      want.sum()`` — and after a clip that sum is below one, so the divide
      scales the clipped party straight back over its own ceiling;
    * ``pools.balance_margins`` opens with ``target_cols *= target_rows.sum() /
      target_cols.sum()``, because IPF has no solution unless the two margins
      agree on the grand total. Hand it column targets that sum to less than
      the pool votes and it restores exactly the mass the clip removed.

    So the invariant this function keeps is the one both of them need: the sum
    is preserved to floating point, and no element exceeds its cap. See
    MODEL-LOG §1.33.

    THE ONE BRANCH THAT CANNOT KEEP BOTH is when every party at its own capacity
    still does not fill the city (``cap.sum() <= total``). Then no allocation
    satisfies the caps and the total at once, and something has to give. It
    gives the caps, because the caller needs the total — but that means the
    function returns a vector with EVERY element above its cap, which is the
    opposite of what its name promises. It cannot fire in this model, since
    parties belong to several pools and the capacities sum far above one. It is
    counted anyway, on ``_capacity_undershoot``, because an uncounted branch
    that silently does the opposite of its docstring is precisely the defect
    this whole function was written to remove (§1.33), and "it cannot happen"
    is what was said about the balance failure too.
    """
    t = np.array(target, dtype=float)
    cap = np.asarray(cap, dtype=float)
    total = float(t.sum())
    if total <= 0:
        return t
    if float(cap.sum()) <= total:
        # Every party at its own capacity still does not fill the city. The two
        # margins cannot both hold at any allocation, so there is nothing to
        # redistribute to; hand back the caps in proportion, COUNT IT, and let
        # the caller's fallback report the infeasibility.
        capped_targets.undershoots += 1
        return cap * (total / max(float(cap.sum()), 1e-12))
    for _ in range(len(t) + 2):
        over = t > cap
        if not over.any():
            return t
        excess = float((t[over] - cap[over]).sum())
        t[over] = cap[over]
        free = ~over & (t < cap)
        room = float(t[free].sum())
        if room > 0:
            # PROPORTIONAL TO WHAT EACH PARTY ALREADY HOLDS -- a judgement, and
            # the larger of the two in this function. The margin (0.98) decides
            # how much moves; this decides WHERE IT GOES, and the register
            # argued only the first until 2026-08-17.
            #
            # Measured on the live 2026 forecast, 600 draws: the rule moves a
            # mean 0.445% of the city sideways (median 0.000%, p90 1.462%, max
            # 6.933%), firing in 39.2% of draws and averaging 1.136% over those.
            # Proportional-to-mass means the DA collects roughly a third of it
            # and the ANC a fifth -- so the guard systematically transfers the
            # PA's truncated upside to the TOP of the ballot, which is the band
            # already measured to be over-forecast (ranks 1-3 mean PIT 0.431,
            # signed +32.50pp). It also correlates the DA's upside with the size
            # of the PA's level shock, which is a dependency nobody asked for.
            #
            # Two alternatives are equally defensible and neither has been
            # measured: proportional to HEADROOM (cap - t), which spreads toward
            # parties with room rather than parties with votes; and proportional
            # to POOL OVERLAP with the offender, which is the only one of the
            # three that respects where the displaced votes could actually have
            # gone. See JUDGEMENT-CALLS.md §A and MODEL-LOG §1.33.
            t[free] += excess * t[free] / room
            capped_targets.moved += excess
        else:
            # Nothing under its cap carries any mass yet — spread by headroom
            # instead, which is the only proportion available.
            head = np.where(free, cap - t, 0.0)
            if head.sum() <= 0:
                break
            t = t + excess * head / head.sum()
    return t


# How many alternating row/column passes the partial balance takes when the two
# margins cannot both hold. Operational: a convergence budget, not a belief —
# but not a large one either, because the sequence converges slowly by nature
# (it is converging to the boundary of an infeasible problem, so it does not
# converge at all in the limit; it just moves less and less). Measured at Nelson
# Mandela Bay 2021, against the 200-pass matrix: 30 passes differ by 186 votes,
# 60 by 45.6, 100 by 16.7, on a city of 364,000. 200 is kept because it costs
# nothing at this size (4 pools × ~90 parties) and because the number the
# committed model used was 200 — changing it would move that city's forecast
# for no stated reason.
PARTIAL_BALANCE_PASSES = 200


# Times `capped_targets` hit the branch that cannot keep both invariants, and the
# total mass its redistribution rule moved sideways.
#
# THE COMMENT HERE USED TO CLAIM these were "read by `run_model`'s report and
# asserted on in tests/test_ipf_feasibility.py". Neither was true: grep found
# only the increments and these initialisations. That was written in the commit
# whose entire thesis is that a quantity computed and never read is a defect,
# and a comment naming a reader that does not exist is worse than no comment,
# because the next reader trusts it. See MODEL-LOG §1.41.
#
# They are module-level and therefore accumulate across every run in a process —
# nine city-years in one `compare_history` invocation share them — so `reset()`
# exists and `run_model` calls it. Read them per run, never as a global.
capped_targets.undershoots = 0


def _reset_cap_counters() -> None:
    """Zero the `capped_targets` counters. Called once per `run_model`."""
    capped_targets.undershoots = 0
    capped_targets.moved = 0.0
# Total mass moved sideways by the redistribution rule, in the units the caller
# passed in. Reported so the rule's cost is visible rather than inferred.
capped_targets.moved = 0.0


def partial_balance(R: np.ndarray, pool_votes: np.ndarray,
                    col_target: np.ndarray,
                    passes: int | None = None) -> np.ndarray:
    """Alternating scaling for margins that CANNOT both hold. Ends on the rows.

    When no matrix satisfies both margins, the POOL margin wins: a pool's
    voters vote for somebody, whereas a party's centre is the model's belief.
    Ending on the row pass is what enforces that — every pool comes out exactly
    allocated and the party levels land as close as the arithmetic permits.

    Two conditions have to hold for IPF to converge at all, and the model can
    break either. A COLUMN can ask for more than the pools it belongs to hold
    (the PA at Johannesburg 2026, 102% of the Coloured pool); a ROW can hold
    more votes than its members' targets add up to (Nelson Mandela Bay 2021's
    Indian/Asian pool, 8,303 votes against 8,168 asked of its sixteen members).
    ``capped_targets`` removes the first. The second cannot be removed by
    moving the party margin without violating the first, so it is handled here
    — and counted, so a run says how often it happened.
    """
    passes = PARTIAL_BALANCE_PASSES if passes is None else int(passes)
    C = R * pool_votes[:, None]
    for _ in range(passes):
        cs = C.sum(axis=0)
        C *= np.divide(col_target, cs, out=np.ones_like(cs), where=cs > 0)[None, :]
        rs = C.sum(axis=1, keepdims=True)
        C *= np.divide(pool_votes[:, None], rs, out=np.ones_like(rs), where=rs > 0)
    return C / np.maximum(C.sum(axis=1, keepdims=True), 1e-12)


# How much of a pool's turnout move is shared with the other pools. MEASURED,
# 2026-08-13, over 14 metro-transitions (eight metros, 2011→2016 and
# 2016→2021): the mean off-diagonal correlation between pools' log turnout
# changes is +0.63. Black African, Coloured and White move almost as one
# (+0.86 to +0.91); Indian/Asian, the smallest and by far the noisiest pool
# (sd 0.63 against 0.16-0.22), is the loose one at +0.21 to +0.47.
#
# It matters because it sets how variable the CITY's turnout is, which is the
# thing 2021 actually moved. Four independent pools put the citywide sd at 0.50
# of a single pool's; the record puts it at 0.82. So drawing them independently
# understated aggregate turnout uncertainty by a factor of 1.64 in a model
# whose own documentation says the last election was decided by 587,000
# abstentions.
TURNOUT_CORRELATION = 0.63

# The scenario key and the module constant are two copies of one number and
# this repository's most reliable defect is two copies of one thing drifting.
# `DEFAULTS` is a literal declared above this line, so it cannot reference the
# constant; this asserts at import that it did not have to. MODEL-LOG §1.63.
import polling as _polling_check

assert DEFAULTS["poll_half_life_days"] == _polling_check.POLL_HALF_LIFE_DAYS, (
    f'DEFAULTS["poll_half_life_days"]={DEFAULTS["poll_half_life_days"]} but '
    f'polling.POLL_HALF_LIFE_DAYS={_polling_check.POLL_HALF_LIFE_DAYS}; they are '
    f'one number. MODEL-LOG §1.67.')

assert DEFAULTS["turnout_correlation"] == TURNOUT_CORRELATION, (
    f'DEFAULTS["turnout_correlation"]={DEFAULTS["turnout_correlation"]} but '
    f'TURNOUT_CORRELATION={TURNOUT_CORRELATION}; they are one number')


def _tri_ppf(u, spec):
    """Inverse CDF of a triangular. Used to drive correlated draws."""
    a, c, b = spec
    c = min(max(c, a), b)
    if b <= a:
        return a
    split = (c - a) / (b - a)
    if u < split:
        return a + np.sqrt(u * (b - a) * (c - a))
    return b - np.sqrt((1.0 - u) * (b - a) * (b - c))


def correlated_triangular(rng, spec, z_common: float, rho: float):
    """A triangular draw pushed by a shared standard normal.

    A Gaussian copula: the pool's own normal is ``sqrt(rho)*z_common +
    sqrt(1-rho)*z_own``, which is standard normal with correlation ``rho`` to
    every other pool drawn against the same ``z_common``, and it is mapped
    through the triangular's inverse CDF. The MARGINAL is therefore exactly the
    triangular ``pools.turnout_band`` measured — this changes how the pools move
    together and nothing about how far any one of them can move.
    """
    if rho <= 0:
        return triangular(rng, spec)
    rho = min(rho, 1.0)
    z = np.sqrt(rho) * z_common + np.sqrt(1.0 - rho) * rng.standard_normal()
    # Φ(z) without scipy: the normal CDF from the error function.
    u = 0.5 * (1.0 + math.erf(z / np.sqrt(2.0)))
    return _tri_ppf(min(max(u, 1e-9), 1 - 1e-9), spec)


def months_before_election(stamp: str, election_day: date) -> float:
    """How long before election day a by-election was held, in months.

    Feeds the same exp(-age/τ) recency decay ``byelections.py`` uses for the
    citywide term, so a contest is weighted identically whichever term reads
    it. A date the file cannot parse returns a large age, which decays the
    contest to nothing rather than letting it count at full strength.

    ``election_day`` was a module constant (2026-11-04) until the target became
    a parameter; it is now the target's own polling day, so a backtest counts
    back from the election it is forecasting rather than from 2026.
    """
    try:
        held = date.fromisoformat(stamp.strip())
    except ValueError:
        return 1e6
    return (election_day - held).days / 30.44


# Which fold's fitted γ each target may read. γ is fitted once and transferred
# across cycles (MODEL-LOG 1.7), and the fold it comes from must have finished
# strictly before the target or the forecast has read its own answer —
# ``gamma_fold_for`` asserts exactly that rather than trusting this table.
#
# The table exists because for 2026 the constraint alone does not pick one.
# Both fold 1 (2014→2016) and fold 2 (2019→2021) precede 2026, and the
# published forecast uses fold 1: §4.1's discipline is fit on fold 1, validate
# on fold 2, and a forecast fitted on both has nothing left to validate it.
# For every other target the entry is simply the most recent qualifying fold.
GAMMA_FOLD = {"2026": 1, "2021": 1, "2016": 3, "2011": 4}


def fold_target_year(fold: int) -> str:
    """The year of the LGE a fold predicts, read off its target filename."""
    return FOLDS[fold]["target"][0][3:7]


def gamma_fold_for(target) -> int:
    """The fold supplying γ for this target, checked to precede it."""
    fold = GAMMA_FOLD.get(target.year)
    if fold is None:
        raise SystemExit(
            f"no γ fold recorded for target {target.year}; add one to "
            f"montecarlo.GAMMA_FOLD (have: {', '.join(sorted(GAMMA_FOLD))})")
    if fold_target_year(fold) >= target.year:
        raise SystemExit(
            f"fold {fold} targets {fold_target_year(fold)}, which does not "
            f"precede {target.year}: its γ has seen the answer")
    return fold


def read_ward_crosswalk(path: Path, year: str) -> tuple[list[tuple[str, str, int]], int, int]:
    """The VD→ward crosswalk: ``([(vd, ward, part_registered), ...], vds, split)``.

    ONE READER (§1.97 F18). There were three: this one, `leverage.load_ward_
    parts` and an inline comprehension in `export_interactive`, the latter two
    both hardcoding ``Ward_2026`` where this takes the year. Three copies of a
    read is how `pools._target_roll` and this function came to build two
    different cities out of one file (F14, §1.99) — 124 of 135 wards disagreeing
    with nobody noticing, because the citywide total was identical either way.
    """
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    column = f"Ward_{year}"
    if rows and column not in rows[0]:
        raise SystemExit(
            f"{path.name} has no `{column}` column; it carries "
            f"{', '.join(k for k in rows[0] if k.startswith('Ward'))or 'no Ward column'}. "
            f"A crosswalk built for one year cannot be read for another.")
    parts = [(r["VD_Number"], r[column], int(r["part_registered"])) for r in rows]
    vds = len({r["VD_Number"] for r in rows})
    split = len({r["VD_Number"] for r in rows if r.get("is_split") == "Y"})
    return parts, vds, split


def ward_parts(target, data_dir: Path, processed: Path) -> tuple[list[tuple[str, str, int]], str]:
    """VD → ward parts and their registration: ``[(vd, ward, registered), ...]``.

    Two sources, because the two cases genuinely differ.

    **A target not yet held** has a delimitation newer than any result file, so
    the crosswalk ``vd_ward_<year>.csv`` (built by ``build_concordance.py``,
    NOT ``build_crosswalk.py``, which this said until 2026-08-28 and which
    builds the unrelated PARTY crosswalk — a citation pointing at a real
    file that has nothing to do with wards) is
    the only thing that knows it. A voting district straddling two new wards
    appears there once per ward with its registration split by
    ``part_registered`` — 181 of Johannesburg's 865 VDs in 2026 — and that
    apportionment is what puts the right number of voters in each ward.

    **A past target** ran under the delimitation its own result file records,
    and boundaries and the roll are published months before polling day, so
    reading them there is not peeking (the votes in the same file are used only
    for scoring). What that file cannot carry is a split: it names exactly one
    ward per VD — checked for Johannesburg 2011, 2016 and 2021, where no VD
    carries two ward IDs — and the registration on the row is the whole VD's.
    So for a past target every VD is assigned whole. That is a limit of the
    published record, not a modelling choice: if a historic VD *was* split
    between wards, no file in this repository says so, and inventing an
    apportionment would be inventing data. The consequence is confined to ward
    winners in a handful of wards; citywide totals are unaffected either way.
    """
    # THE SOURCE IS A FUNCTION OF THE CALENDAR, NOT OF THE FILESYSTEM
    # (§1.97 F19, §1.120). It used to be `if crosswalk.exists():` and nothing
    # else — so dropping a `vd_ward_<year>.csv` into a directory changed which
    # delimitation a BACKTEST ran under, with no argument changed and no
    # warning printed. A held election has a published record of its own wards
    # and that record is the answer; an unheld one has only the crosswalk.
    #
    # The filename comes from `Target.crosswalk` so there is one definition of
    # it; the DIRECTORY is the caller's, which is what lets the tests point
    # this at a temporary one.
    crosswalk = processed / target.crosswalk.name
    if cityconfig.CALENDAR[target.year].results is None:
        if not crosswalk.exists():
            # §1.40's lesson: name the file you wanted and the command that
            # makes it. This used to fall through to `target.results()` and
            # raise "2026 has no result file: it has not been held" — a true
            # fact about the calendar that nobody needed, naming neither the
            # file nor the directory it was actually sitting in.
            raise SystemExit(
                f"{target.city.name} {target.year}: no VD→ward crosswalk. "
                f"Wanted {crosswalk}, which does not exist.\n"
                f"  {target.year} has not been held, so no result file carries "
                f"its wards and the crosswalk is the only source. Build it "
                f"with\n"
                f"    .venv/bin/python src/build_concordance.py "
                f"--city {target.city.slug}")
        parts, n_vds, split = read_ward_crosswalk(crosswalk, target.year)
        return parts, (f"{crosswalk.name} ({len(parts)} parts over "
                       f"{n_vds} VDs, {split} split)")

    # A HELD TARGET READS ITS OWN PUBLISHED RECORD, and a crosswalk sitting in
    # its directory is now ignored rather than silently preferred.
    path = cityconfig.resolve_path(data_dir / target.results(target.year))
    seen: dict[str, tuple[str, int]] = {}
    vds_in_file: set[str] = set()
    blank_roll = 0
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        # F16: A MISSING COLUMN AND A BLANK CELL BOTH BECAME ZERO. `.get(...)
        # or 0` cannot tell "this file does not have a roll" from "this VD's
        # roll is blank" from "this VD has no voters", and the first is a
        # different file, not a datum. Refuse it; count the second.
        if reader.fieldnames is not None and \
                "Registered_Population" not in reader.fieldnames:
            raise SystemExit(
                f"{path.name} has no `Registered_Population` column, so every "
                f"ward would be given a roll of zero.\n"
                f"  columns present: {', '.join(reader.fieldnames)}\n"
                f"  MODEL-LOG §1.97 F16 — this used to read as a city with no "
                f"voters rather than as the wrong file.")
        for row in reader:
            vd = row["VD_Number"]
            vds_in_file.add(vd)
            if vd in seen or not row.get("Ward"):
                continue
            raw = row.get("Registered_Population")
            if raw is None or str(raw).strip() == "":
                blank_roll += 1
            registered = int(float(raw or 0))
            seen[vd] = (row["Ward"].strip(), registered)
    parts = [(vd, ward, registered) for vd, (ward, registered) in seen.items()]
    # F17: A VD WHOSE EVERY ROW LACKS A WARD WAS DROPPED IN SILENCE, and the
    # label then reported the survivors as though they were the file. Say what
    # was lost, in the one line the run prints about where its wards came from.
    lost = len(vds_in_file) - len(seen)
    detail = f"{len(parts)} VDs, none split"
    if lost:
        detail += f", {lost} DROPPED (no ward on any row)"
    if blank_roll:
        detail += f", {blank_roll} blank roll"
    return parts, f"{path.name} (boundaries and roll only; {detail})"


def solve_and_predict(dev, base_city, target, gamma, weight, rounds=40, tol=1e-6,
                      level_floor=None, stats=None):
    """Solve for θ reaching `target` citywide through the model; return VD shares.

    ``level_floor`` resolves ``DEFAULTS["level_floor"]`` at call time; see
    `log_shock` and MODEL-LOG §1.33 for why no module constant may be a default
    argument here. It resolved ``SHARE_FLOOR`` (0.002) until 2026-08-26 — the
    floor production abandoned on 2026-08-06 — which no run ever saw, because
    both production call sites pass ``level_floor`` explicitly from
    ``scenario["level_floor"]``. It was a trap for the next caller, and phase A's
    own test file walked into it (MODEL-LOG §1.98, F11).

    ``stats``, when given, is a dict this records into. **It does not raise.**
    This loop does not converge on the shipped configuration — not rarely, but on
    *every* draw — because `logit` clips at ``level_floor`` and the tail of the
    Dirichlet always lands beneath it, so those parties' θ updates are no-ops and
    the iteration sits on a fixed point that is not the target (MODEL-LOG §1.98,
    F12). `pools.balance_margins` raises on the same condition; raising here
    would abort every draw, which is why this counts instead.

    Nothing recorded here changes the returned array.
    """
    level_floor = DEFAULTS["level_floor"] if level_floor is None else level_floor
    theta = np.where(base_city > 0, target / np.maximum(base_city, 1e-12), 1.0)
    weights = weight / weight.sum()
    # JUDGE CONVERGENCE ONLY WHERE IT IS ACHIEVABLE (owner's call, 2026-08-26).
    #
    # A party whose target sits under `level_floor` cannot be moved onto it by
    # ANY θ — `logit` clips at the floor, so its level stops responding and its
    # error is irreducible. Including it in the stopping test guarantees the test
    # never passes, which is why the `break` below was dead code and all `rounds`
    # were always spent: on the shipped configuration every draw carries such a
    # party (dirichlet_floor 1e-4 against α = 26.86 puts 97.4% of floored members
    # under 1e-6).
    #
    # ⛔ **THE EARLY STOP BELOW STILL NEVER FIRES, AND TWO CLAIMS THAT USED TO
    # STAND HERE WERE WRONG.** Both are corrected in MODEL-LOG §1.108:
    #
    #   * *"the solve converges in ~10 rounds and then burns 30 more achieving
    #     nothing"* — it does not converge at all. `solve_rounds / solve_calls`
    #     is exactly `rounds` on every measured target (§1.105), and running
    #     **25x longer moves the reachable gap by 2%**: 9.8379e-06 at 40 rounds,
    #     9.8033e-06 at 200, 9.6336e-06 at 1000. The loop is not
    #     under-iterated; it has reached a plateau it cannot leave.
    #   * *"repairing it would move numbers without improving the forecast"* —
    #     an UNMEASURED claim, and it is now known to be unrepairable at a fixed
    #     `level_floor` rather than merely not worth repairing. Which half of
    #     that sentence is true has never been tested.
    #
    # WHY IT PLATEAUS, measured rather than argued. The floor does not only stop
    # sub-floor parties responding: it makes each of them HOLD about
    # `level_floor` of every row whatever its target says, and the row
    # renormalisation takes that excess from everyone above the floor in
    # proportion to size. On Johannesburg 2021, 100 draws, 200 solves: 14.5
    # sub-floor parties hold 1.4866e-05 against targets asking 1.6011e-06, so the
    # floor INJECTS 1.3265e-05. The largest party (share 0.4066) ends 5.2612e-06
    # short of its drawn target, against 5.4284e-06 predicted by
    # `share x injected` — agreement to 3%, which is what identifies the
    # mechanism rather than merely being consistent with it.
    #
    # It is therefore an ABSORPTION, and `stats` now reports it
    # (`floor_injected_*`) as NULL-RESULTS.md §4.3 requires of an absorbing
    # stage. **The lever that could actually shrink it is `level_floor` itself**,
    # which has a range and is therefore a scored change facing the full bar in
    # `ITERATING.md` — not something to adjust in passing here.
    #
    # THE ARITHMETIC IS DELIBERATELY UNTOUCHED. This changes only WHEN the loop
    # is allowed to stop, not what it computes. MODEL-LOG §1.98 F12, §1.105,
    # §1.108.
    reachable = target > level_floor
    used, gap = rounds, float("inf")
    identity_hits = 0
    for _i in range(rounds):
        level = logit(base_city * theta, floor=level_floor)
        pred = expit(level[None, :] + gamma[None, :] * dev)
        pred /= pred.sum(axis=1, keepdims=True)
        got = weights @ pred
        err = np.abs(got - target)
        gap = err.max()
        # F10: where `got` has collapsed, the update takes the IDENTITY and the
        # party is never lifted. Counted rather than assumed, because §1.98
        # records that "the obvious cure for F12 activates F10's identity
        # guard" -- so any future change to the floor must be able to see
        # whether it has.
        stuck = got <= 1e-9
        identity_hits += int(stuck.sum())
        theta = theta * np.where(got > 1e-9, target / np.maximum(got, 1e-12), 1.0)
        if (err[reachable].max() if reachable.any() else 0.0) < tol:
            used = _i + 1
            break
    if stats is not None:
        # The reachable gap is what the floor can actually deliver: a party whose
        # target sits under `level_floor` cannot be moved onto it by any θ, so
        # including it in the convergence test guarantees failure. Recording both
        # separates "the solver failed" from "the target was unreachable".
        reachable = target > level_floor
        reach_gap = (float(np.abs(got - target)[reachable].max())
                     if reachable.any() else 0.0)
        stats["solves"] = stats.get("solves", 0) + 1
        stats["rounds"] = stats.get("rounds", 0) + used
        if gap >= tol:
            stats["nonconvergent"] = stats.get("nonconvergent", 0) + 1
        if reach_gap >= tol:
            stats["nonconvergent_reachable"] = \
                stats.get("nonconvergent_reachable", 0) + 1
        stats["worst_gap"] = max(float(stats.get("worst_gap", 0.0)), float(gap))
        stats["worst_gap_reachable"] = max(
            float(stats.get("worst_gap_reachable", 0.0)), reach_gap)
        stats["unreachable_parties"] = max(
            int(stats.get("unreachable_parties", 0)), int((~reachable).sum()))
        stats["identity_hits"] = stats.get("identity_hits", 0) + identity_hits
        # ABSORPTION ACCOUNTING (NULL-RESULTS.md §4.3). The floor does not just
        # stop sub-floor parties responding -- it makes them HOLD roughly
        # `level_floor` of every row whatever their target says, and the row
        # renormalisation takes that excess from everyone above the floor, in
        # proportion to size. Measured on Johannesburg 2021, 100 draws, 200
        # solves: 14.5 sub-floor parties hold 1.4866e-05 against targets asking
        # 1.6011e-06, so the floor INJECTS 1.3265e-05; the largest party (0.4066)
        # falls 5.2612e-06 short of its drawn target against 5.4284e-06 predicted
        # by `share x injected` -- agreement to 3%.
        #
        # It is IRREDUCIBLE at a fixed `level_floor`, and that was measured too:
        # 25x the rounds moves the reachable gap 2% (9.8379e-06 at 40 rounds,
        # 9.8033e-06 at 200, 9.6336e-06 at 1000). The loop is not under-iterated.
        # See MODEL-LOG §1.108.
        injected = float(got[~reachable].sum() - target[~reachable].sum())
        stats["floor_injected_sum"] = (
            float(stats.get("floor_injected_sum", 0.0)) + injected)
        stats["floor_injected_worst"] = max(
            float(stats.get("floor_injected_worst", 0.0)), injected)
    level = logit(base_city * theta, floor=level_floor)
    pred = expit(level[None, :] + gamma[None, :] * dev)
    return pred / pred.sum(axis=1, keepdims=True)


# --------------------------------------------------------------------------
# scenario configuration
# --------------------------------------------------------------------------

def parse_set(pairs: list[str], scenario: dict) -> None:
    """Apply --set key=value overrides; values parsed as JSON where possible."""
    for item in pairs:
        key, _, value = item.partition("=")
        key = key.strip()
        if key not in scenario:
            raise SystemExit(f"unknown scenario key: {key!r} (see DEFAULTS)")
        try:
            scenario[key] = json.loads(value)
        except json.JSONDecodeError:
            scenario[key] = value


def apply_city(city) -> None:
    """Point the module's constants at this city, from a CLEAN baseline.

    Johannesburg's config was generated from these very constants when the
    spine was introduced, so for CoJ this is a no-op by construction — which
    is what lets the refactor happen without the forecast moving.

    **THE RESET IS THE POINT, and it was missing until 2026-08-18.** This wrote
    each city's scalars over ``DEFAULTS`` and never put back what the previous
    city had written, so in a nine-city-year loop a city inherited whatever the
    cities before it happened to declare. Only two of the eight metros declare
    scalars at all, so the six that declare none were running on Johannesburg's
    or Tshwane's values rather than on ``DEFAULTS`` — **and which one depended
    on iteration order**.

    Exactly one key actually differs between them today —
    ``pa_contestation_uplift``, 1.25 for Johannesburg against 1.0 for Tshwane —
    and it is consumed at 2026 and at no backtested target, so no score in this
    repository moved because of it. That is luck, not design: a second differing
    key, or a 2026 city-year entering the panel, would have made the scoreboard
    depend on the order the cities were looped in.

    It also made the serial loop and a parallel one different programs, which is
    why this is fixed here rather than worked around in `compare_history`.
    """
    global COUNCIL, PLAN_BOUNDS
    # Restore the module's own defaults before applying this city's, so a run
    # never inherits the previous city's judgements.
    DEFAULTS.clear()
    DEFAULTS.update(copy.deepcopy(_PRISTINE_DEFAULTS))
    COUNCIL = city.council
    PLAN_BOUNDS = city.plan_bounds
    j = city.judgements
    # `theta_mode` and `individual_theta` were copied from the city toml here
    # until 2026-08-19. Both are deleted; a city file that still carries them
    # is carrying a dead key, and nothing reads it.
    unknown = []
    for key, value in j.get("scalars", {}).items():
        if key.endswith("_note"):
            continue
        # A CITY TOML MAY NOT INVENT A LEVER, and until 2026-08-22 it could.
        # `read_scenario_file` has always rejected an unknown key; this path
        # accepted anything and wrote it straight into DEFAULTS. So when §1.68
        # deleted `poll_weight`, `cities/joburg.toml` and `cities/tshwane.toml`
        # went on carrying it and `apply_city` faithfully put it back — a key
        # nothing reads, sitting in the model's parameter dict, which
        # `read_scenario_file` would then ACCEPT from a scenario file and
        # silently ignore. That is the half-finished-deletion failure the sweep
        # guard caught inside §1.68 itself, one layer down and pointing the
        # other way: the guard checks DEFAULTS against PERTURB, and this route
        # adds to DEFAULTS after the guard has looked. MODEL-LOG §1.69.
        if key not in _PRISTINE_DEFAULTS:
            unknown.append(key)
            continue
        DEFAULTS[key] = value
    if unknown:
        raise SystemExit(
            f"cities/{city.slug}.toml declares [judgements.scalars] key(s) "
            f"that are not model levers: {', '.join(sorted(unknown))}.\n"
            f"Either the lever was deleted and the city file was not updated, "
            f"or the key is a typo. A city file may not invent a lever: "
            f"`DEFAULTS` is the register of what exists.")


# Top-level keys a scenario file may carry that are *not* model parameters.
# They are about the scenario rather than in it, so they are split off before
# the unknown-key check rather than being added to DEFAULTS (a metadata key in
# DEFAULTS would travel into every run's reported configuration).
#
#   derived_from -- the elections whose results the scenario's numbers were
#       fitted on, as a list of years. ``backtest.py`` uses it to decide
#       whether a run against a past target is out-of-sample; see
#       ``backtest.FITTED_ON``. Undeclared means "assume in-sample".
SCENARIO_METADATA = ("derived_from",)


# --------------------------------------------------------------------------
# reproducibility: the hash seed, which is a property of the PROCESS
# --------------------------------------------------------------------------
#
# Python randomises `hash()` for `str` per process, which reorders `set` and
# `dict` iteration, which reorders a float summation somewhere on the model
# path. MODEL-LOG §1.104 measured it on unmodified HEAD: three runs at
# `PYTHONHASHSEED=0` agree to the digest, three at `PYTHONHASHSEED=random`
# disagree in every one of them. The magnitude is machine epsilon -- max 3.1e-16
# to 5.0e-16 against party shares whose median is 9.4e-5 -- so NO FORECAST
# MOVES. What moves is whether a re-run is bit-comparable to the one before it.
#
# WHY IT IS WORTH A RE-EXEC ANYWAY, given the magnitude:
#
#   * `test_the_model_is_reproducible_from_its_seed` runs in ONE process and
#     therefore cannot see this. The claim it appears to make -- that the seed
#     determines the answer -- holds WITHIN a process and not BETWEEN them.
#   * `compare_history` fans out to worker processes, each of which got its own
#     hash seed, so the sixteen city-years were each computed under a different
#     iteration order.
#   * `forecast_frozen.json` is PUBLISHED so the forecast can be held to account
#     after 4 November, and the honest statement of what it guarantees is
#     "identical to the last bit under a fixed hash seed" rather than the
#     "reproducible" it would otherwise have to claim.
#
# THE SEED MUST BE SET BEFORE THE INTERPRETER STARTS. `PYTHONHASHSEED` is read
# by CPython at start-up; assigning `os.environ["PYTHONHASHSEED"]` inside a
# running process changes nothing about that process's own `hash()`. So the
# only way to honour it from inside is to re-exec once, which is what this does
# -- and the child then sees the variable already set and does not re-exec
# again, so it terminates.
#
# It also fixes the WORKERS for free and that is the larger half: a
# `ProcessPoolExecutor` child is a fresh interpreter that inherits `os.environ`
# from its parent at spawn, so a parent which has re-exec'd under a fixed seed
# hands that seed to all eight workers without anything being passed explicitly.
HASH_SEED = "0"


def fix_hash_seed(seed: str | None = None) -> None:
    """Re-exec this process once under a fixed ``PYTHONHASHSEED``.

    ``seed`` resolves ``HASH_SEED`` IN THE BODY and is not a default argument.
    A module constant captured as a default is frozen at import, so rebinding
    the attribute would move this function's record and not its behaviour --
    `LEVEL_DF` §1.33, and `test_no_numeric_module_constant_is_a_default_argument`
    caught this one the first time the suite ran against it.

    Call it FROM AN ``if __name__ == "__main__"`` GUARD AND NOWHERE ELSE. It
    replaces the running process, so calling it at import time would re-exec
    whatever program happened to import this module -- a test runner, a site
    build -- with `montecarlo`'s argv, which is not a thing any caller could
    recover from.

    Returns normally, having done nothing, when the seed is already what was
    asked for; that is the re-exec'd child's own path through here, and it is
    what stops the recursion.
    """
    seed = HASH_SEED if seed is None else seed
    if os.environ.get("PYTHONHASHSEED") == seed:
        return
    os.environ["PYTHONHASHSEED"] = seed
    sys.stdout.flush()
    sys.stderr.flush()
    os.execv(sys.executable, [sys.executable, *sys.argv])


# --------------------------------------------------------------------------
# the delivery proof: a read log that records the VALUE, not just the name
# --------------------------------------------------------------------------
#
# THE PROBLEM. "This change did nothing" and "this change never arrived" are
# the same observation, and the harness has been reporting both as a null. Of
# the 48 constants pre-registered for the B2 sweep, 42 carry a blocker and the
# largest class is undeliverability: a module constant rebound in the parent
# process does not cross a `ProcessPoolExecutor` boundary, so a sweep fans out
# to eight workers that re-import the default and comes back with a flat,
# confident null. `LEVEL_DF` was swept 2.5 -> 1000 for byte-identical output
# because `df: float = LEVEL_DF` had been bound once at import (MODEL-LOG
# §1.33); nothing in the run could say so.
#
# THE RULE, from NULL-RESULTS.md §4.1: **the swept constant must appear in the
# read log, at the value that was set. Until it does, a flat result is VOID,
# NOT NULL.** Four causes of a null -- UNDELIVERED, ABSORBED:<stage>,
# CANCELLED:<parameter>, INERT -- and only INERT is a result. This log is what
# separates the first from the other three; nothing here can tell the other
# three apart, and it does not pretend to.
#
# A DECLARATION IS A CLAIM AND THIS IS THE EVIDENCE. `ARCHITECTURE.md`'s list A
# is what each unit says it reads; this is list C, what a run demonstrably read.
# `A != C` is a hard failure either way round: the code stopped reading what it
# says it reads, or it never did.
#
# WHAT IT DOES NOT DO. It records; it does not check. A guard that has gone
# blind will be recorded faithfully as having run. What catches that is an
# assertion -- which is the point of `assert_delivered` below, and of putting
# the value on disk where an assertion is cheap to write.

class Undelivered(AssertionError):
    """A value a measurement set was never consulted, or was consulted changed.

    Raised by :func:`assert_delivered`. An ``AssertionError`` so a test or a
    sweep treats it as a failure by default: the whole point is that a run
    which cannot prove delivery must not be allowed to report a null.
    """


# Sentinel for "the caller did not record a value". `None` is a legitimate
# value for several constants (`spine_k` ships as None), so it cannot be the
# sentinel -- that confusion is CLASS 13 in tests/test_levers_are_live.py.
class _Unrecorded:
    def __repr__(self) -> str:                      # pragma: no cover - display
        return "<unrecorded>"


_UNRECORDED = _Unrecorded()

# How many DISTINCT values of one name the log keeps. A per-party or per-draw
# site can consult one name at many values, and the log is serialised into
# `forecast_summary.json` on every run -- an uncapped list would put a
# megabyte of diagnostics into a published artefact. The count of reads and of
# dropped distinct values is kept, so truncation is visible rather than silent.
DELIVERY_MAX_VALUES = 12


# The longest a single rendered value may be before it is replaced by a count
# and a digest. `levels.KNOWN_ABSENT` is fourteen entries of prose reason and
# renders in full under the <=16-key rule -- several kilobytes into every
# `forecast_summary.json`, on every run, for a constant whose value changes
# about once a month.
DELIVERY_MAX_CHARS = 2000


def _delivery_digest(value) -> str:
    """A short, order-stable content hash of a value the log cannot show whole.

    **A DELIVERY PROOF THAT CANNOT SEE A CHANGED VALUE IS NOT A DELIVERY
    PROOF.** Before this existed, `_delivery_value` rendered
    `parties.ALIASES` -- seventeen ballot-string-to-party-code mappings read
    inside `run_model`, which decide WHAT THE MODEL IS FORECASTING -- as
    ``{"__dict__": 17}``. That is a length. Two entirely different alias tables
    of the same size were indistinguishable in the log that exists to prove
    what a run consulted, and `assert_delivered` would have passed a sweep that
    changed every mapping in it.

    Order-stable because a `set` iterates in hash order and dicts are only
    conventionally ordered: the digest is taken over a sorted rendering, so the
    same content hashes the same across processes whatever the hash seed did.
    """
    try:
        if isinstance(value, dict):
            payload = repr(sorted((str(k), repr(v)) for k, v in value.items()))
        elif isinstance(value, (set, frozenset)):
            payload = repr(sorted(repr(v) for v in value))
        else:
            payload = repr(value)
    except Exception:                        # pragma: no cover - exotic __repr__
        payload = f"<unrenderable {type(value).__name__}>"
    return hashlib.sha256(payload.encode("utf-8", "replace")).hexdigest()[:12]


def _delivery_value(value, depth: int = 0):
    """A JSON-native, comparable rendering of a value that was consulted.

    `scenario` is dumped with a plain ``json.dump`` and no ``default=`` hook
    (see :func:`main`), so anything left on it must already be JSON. A numpy
    array on the scenario produced malformed JSON and broke the site build
    once already; this is that lesson applied to the read log.

    **Every lossy rendering carries a digest of the whole value**, because the
    alternative -- a bare count, or a `repr` cut at 200 characters -- silently
    turns "this constant was delivered unchanged" into a claim the log cannot
    actually support. See :func:`_delivery_digest`.
    """
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else repr(value)
    if isinstance(value, np.generic):
        return _delivery_value(value.item(), depth)
    if isinstance(value, np.ndarray):
        flat = value.ravel()
        if flat.size <= 8 and np.issubdtype(value.dtype, np.number):
            return [float(x) for x in flat]
        return {"__array__": list(value.shape),
                "sum": float(np.nansum(flat)) if flat.size else 0.0,
                "sha": _delivery_digest(value.tobytes())}
    if depth >= 2:
        return {"__repr__": repr(value)[:200], "sha": _delivery_digest(value)}
    if isinstance(value, (set, frozenset)):
        shown = sorted(_delivery_value(v, depth + 1) for v in value)
        if len(shown) > 16:
            return {"__set__": len(value), "sha": _delivery_digest(value)}
        return shown
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (list, tuple)):
        if len(value) > 16:
            return {"__list__": len(value), "sha": _delivery_digest(value)}
        rendered = [_delivery_value(v, depth + 1) for v in value]
    elif isinstance(value, dict):
        if len(value) > 16:
            return {"__dict__": len(value), "sha": _delivery_digest(value)}
        rendered = {str(k): _delivery_value(v, depth + 1)
                    for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    else:
        return {"__repr__": repr(value)[:200], "sha": _delivery_digest(value)}
    # Small by count and still enormous by content: collapse on size too, and
    # keep the digest so the collapse is not a loss of evidence.
    if len(repr(rendered)) > DELIVERY_MAX_CHARS:
        tag = "__list__" if isinstance(rendered, list) else "__dict__"
        return {tag: len(value), "sha": _delivery_digest(value)}
    return rendered


def note_value(scenario: dict | None, name: str, value, where: str,
               who: str | None = None, kind: str = "consulted"):
    """Record that ``name`` was consulted AT ``value``, and return ``value``.

    Returns its argument so a read can be instrumented by wrapping it, the way
    :meth:`Trace.put` does, without moving code or adding a branch::

        floor = note_value(scenario, "montecarlo.SHARE_FLOOR", SHARE_FLOOR,
                           where="montecarlo:run_model")

    ``kind`` is the strength of the claim and the distinction matters more than
    anything else here:

    * ``consulted`` -- recorded AT the site that reads it, so the value
      demonstrably reached the computation. This is a delivery proof.
    * ``resolved`` -- the value THIS PROCESS holds for a module-level constant,
      recorded once per run without reference to any reader. It proves the
      value crossed the process boundary, which is the single largest cause of
      an undelivered sweep; it does NOT prove any code read it. §1.68 was burned
      by exactly this distinction -- *"that null was measured WITH THE GATE
      SHUT"* -- so a ``resolved`` record must never be reported as evidence
      that a lever is INERT.
    * ``not-imported`` / ``missing`` -- written by :func:`note_module_constants`
      when a declared name is not there to read. A renamed constant shows up as
      an absence rather than as silence.

    Writing to ``scenario`` (like ``_constants_read`` and ``_ward_pr_trusted``)
    keeps the log travelling with the run into ``forecast_summary.json``, and
    keeps this function free of module state -- which is what lets it be called
    inside a worker process and mean something.
    """
    if scenario is None:
        return value
    log = scenario.setdefault("_delivered", {})
    rec = log.get(name)
    if rec is None:
        rec = log[name] = {"values": [], "where": [], "kinds": [], "who": [],
                           "reads": 0, "dropped": 0}
    rec["reads"] += 1
    for field_name, item in (("where", where), ("kinds", kind),
                             ("who", who or "(all)")):
        if item not in rec[field_name] and len(rec[field_name]) < DELIVERY_MAX_VALUES:
            rec[field_name].append(item)
    shown = _delivery_value(value)
    if shown not in rec["values"]:
        if len(rec["values"]) < DELIVERY_MAX_VALUES:
            rec["values"].append(shown)
        else:
            rec["dropped"] += 1
    return value


# MODULE CONSTANTS, BY MODULE. None of these is in `DEFAULTS`, so none is swept
# by `test_every_tunable_lever_actually_moves_the_forecast`, and none crosses a
# `ProcessPoolExecutor` boundary when a sweep rebinds it in the parent. That is
# the 42-of-48 class. Recording them per run, in the process that ran, is what
# turns "the sweep did nothing" into "the sweep never arrived".
#
# Read from the LIVE module namespace at call time, never bound at import --
# binding at import is the `LEVEL_DF` defect itself (§1.33) and would make this
# log agree with the sweep while the model disagreed with both.
#
# THE RULE FOR WHAT BELONGS HERE, applied module by module on 2026-08-27 and
# the reason the table roughly doubled: **a name belongs here if and only if it
# is READ IN THIS PROCESS, ON THE MODEL PATH.** Not "is it a judgement" -- that
# is `JUDGEMENT-CALLS.md`'s question and it has a different answer. A constant
# read only while an artefact is PRECOMPUTED reaches the model through that
# artefact, and recording the value this process happens to hold would attest
# to something the run never consulted. See DELIBERATELY NOT DECLARED below,
# which is the larger list and the more useful one.
#
# ENVIRONMENT VARIABLES ARE LOGGED, and until 2026-08-27 this comment said the
# opposite -- "an env var is a class of input nothing in this repository logs
# at all". That was false when it was written and this table is what falsifies
# it: `levels.FILTER_TYPE_A`, `levels.EXCLUDE_DEMARCATION_CROSSING`,
# `levels.THETA_WINDOW`, `levels.THETA_EXCLUDE_TARGETS` and
# `polling.SIGMA_TWO_TERM` are all env-derived, all declared below, and all
# resolved into `_delivered` on every run. `freeze.ENV_SWITCHES` records the
# raw environment as well. What is true, and worth keeping, is that only the
# RESOLVED value is recorded here: `THETA_WINDOW=0` and `THETA_WINDOW` unset
# are the same record, and only the freeze separates them.
MODULE_CONSTANTS: dict[str, tuple[str, ...]] = {
    # PLAN_BOUNDS and COUNCIL are rebound per city by `apply_city`, so the
    # recorded value is the city's, not the module's shipped default.
    # POOL_CAPACITY_MARGIN is the one whose EFFECT was already instrumented --
    # `capped_targets.moved` in `41_guards` -- while its CAUSE was not, which
    # is the failure NULL-RESULTS §4.1 is against. HASH_SEED records the
    # reproducibility guarantee the run was made under; see `fix_hash_seed`.
    "montecarlo": ("SHARE_FLOOR", "DIRICHLET_FLOOR", "TURNOUT_DRAW_FLOOR",
                   "TURNOUT_DRAW_CEILING", "LEVEL_DF", "BYE_MIN_WEIGHT",
                   "WARD_PR_RATIO_MIN", "WARD_PR_RATIO_MAX", "COUNCIL",
                   "TURNOUT_CORRELATION", "PLAN_BOUNDS",
                   "POOL_CAPACITY_MARGIN", "GAMMA_FOLD",
                   "PARTIAL_BALANCE_PASSES", "HASH_SEED", "FOLDS"),
    # FOLDS is declared HERE and not under `fold` on purpose: `montecarlo.py`
    # does `from fold import FOLDS`, and `fold_target_year` resolves the name
    # in THIS module's globals. A record keyed `fold.FOLDS` would report a
    # value the model cannot see, which is a false delivery proof rather than a
    # missing one.
    #
    # The four added to `levels` are the PAYLOADS of switches that were already
    # declared: the log recorded THAT a filter ran and nothing about what it
    # removed. KNOWN_ABSENT's own docstring calls it "the largest absorber in
    # this module, and it is not counted".
    "levels": ("SD_FLOOR", "SD_CEILING", "SHRINK", "RELIABILITY_HALF",
               "SPINE_K", "FILTER_TYPE_A", "EXCLUDE_DEMARCATION_CROSSING",
               "THETA_WINDOW", "THETA_EXCLUDE_TARGETS", "METRO_CODES",
               "TYPE_A_EVENTS", "DEMARCATION_CROSSING", "KNOWN_ABSENT"),
    # POLL_DEFF_STANDALONE is the only one of the four `deff`/`screen`/`drift`
    # constants that a `DEFAULTS` key does NOT shadow at the call site, so it
    # is the only one a sweep of the module constant can actually move -- and
    # it was the undeclared one while its three shadowed siblings were
    # declared. NATIONAL_VOTES (2016, 2021) and PROJECTED_METRO_SHARE (2026,
    # and nothing the backtest panel can reach) are the two halves of the
    # national-poll-to-metro denominator.
    "polling": ("SIGMA_COMMON", "SIGMA_IDIO", "SIGMA_DRIFT_PER_ROOT_DAY",
                "SIGMA_VOLATILITY", "SIGMA_TWO_TERM", "POLL_HOUSE_K",
                "POLL_HALF_LIFE_DAYS", "POLL_MIN_N",
                "POLL_HOUSE_SD", "CAMPAIGN_WINDOW_DAYS",
                "POLL_DRIFT_PP_PER_ROOT_DAY", "REGISTER",
                "POLL_DEFF_STANDALONE", "NATIONAL_VOTES",
                "PROJECTED_METRO_SHARE"),
    # ONE name out of sixteen in `pools.py`. METRO_CODES is read in this
    # process, inside `run_model`'s poll path, and holds the same eight codes
    # as `levels.METRO_CODES` IN A DIFFERENT ORDER (EKU and CPT are swapped).
    # The two records therefore differ, and that is not a bug to be filed.
    "pools": ("METRO_CODES",),
    # ALIASES and MINOR_ALIASES decide WHAT THE MODEL IS FORECASTING: they are
    # read on every raw ballot row via `parties.canonical`, inside `run_model`,
    # and adding one merges two ballot strings into a single party for every
    # fold, theta and arrival downstream. Nothing tested them, no guard saw
    # them (`compare_history`'s serial-forcing guard keeps int/float/bool
    # only), and they were absent from every register. They are recorded as a
    # count and a CONTENT DIGEST -- see `_delivery_digest`, without which a
    # same-length edit was invisible.
    "parties": ("ALIASES", "MINOR_ALIASES"),
}

# DELIBERATELY NOT DECLARED, and the reasons, because an empty row in a table
# like this reads as an oversight and each of these is a decision.
#
# THE ARTEFACT-BORNE CLASS -- eleven of sixteen constants in `pools.py`, both
# floors in `fold.py`, and everything in `turnout.py`. `pools.ALPHA_MIN_SHARE`,
# `ALPHA_FLOOR`, `ALPHA_CEILING`, `ALPHA_FALLBACK`, `ARRIVAL_BAND_LO/HI`,
# `SPLINTER_PARENT_WEIGHT`, `SPLIT_SD_FLOOR`, `MIN_HOME_SPLITS`, `SPLITS`,
# `SOLVE_TOL`; `fold.SHARE_FLOOR`, `fold.LEVEL_FLOOR`; `turnout.ELECTIONS`,
# `turnout.LAMBDA_PAIRS`. Every one is read only while `pools --emit`, `fold`
# or `turnout` PRECOMPUTES an artefact. The model reads the artefact, possibly
# weeks later. Declaring them would write a `resolved` record for a value that
# had no bearing on the run, and a sweep could then pass a presence check while
# being UNDELIVERED in the only sense that matters.
#
#   **THE DELIVERY PROOF FOR THAT CLASS IS THE ARTEFACT KEY, NOT THIS TABLE.**
#   `artefact_key` / `pools_sha` is already recorded on the scenario, so: a
#   sweep of any ALPHA_* that does not move `pools_sha` never arrived. That is
#   checkable today. This matters because the handover into 2026-08-27 named
#   "the whole ALPHA_* family" as the top gap here, on the strength of
#   NULL-RESULTS.md crediting it with 83-98% of drawn variance. The variance
#   claim is not in dispute; the ROUTE was. It is not a process constant.
#
# `turnout` IS NOT IN `sys.modules` DURING A RUN AT ALL -- its only importer
# anywhere is a function-local `import turnout` inside `fold.turnout_weights`,
# reached only from `fold.main`. Declaring it would write `not-imported` for
# every name on every run, which is worse than silence: a reader scanning
# `45_delivered.json` takes presence in the table for relevance.
#
# `benchmarks` SHAPES THE OPPONENT, NOT THE MODEL. Its six constants set the
# `prior-lge-noise` spread and the baseline dispatch -- they move the BAR, not
# the forecast. Declared in one flat table beside `LEVEL_DF`, a future reader
# sweeping `NEW_PARTY_SIGMA` would see CRPS move and conclude a model lever is
# live. That is a category error that SURVIVES a correct delivery proof, which
# makes it worse than the VOID-vs-NULL confusion this whole instrument exists
# to end. It is also not imported at all under `python src/montecarlo.py`.
#
# `parties.PARTIES`, `parties.OTHER`, `parties.INDEPENDENT` -- off the model
# path. `PARTIES` is read only by `build_crosswalk.py`, an audit CLI whose
# output has no consumer. `OTHER` and `INDEPENDENT` have ZERO readers; the
# name the model actually reads is `seats.INDEPENDENT`.
#
# `pools.CONFIG` and `levels.METRO_CODES` ARE read in this process and are
# declared -- but both are bound as FUNCTION DEFAULTS at import, so the live
# attribute this table records is not necessarily what ran. See
# `FROZEN_DEFAULTS`, which is why `levels.METRO_CODES` is recorded under a
# kind of its own and `pools.CONFIG` is left out entirely until the freeze is
# repaired in `pools.py` (a code change there invalidates all eighteen pool
# specs, so it is not a change to make in passing).

# (module, constant) pairs whose value is captured as a FUNCTION DEFAULT at
# import time, so that rebinding the module attribute -- which is exactly what
# a sweep does -- moves the record here and NOT the computation. `LEVEL_DF`
# §1.33 is this defect and cost weeks. Recording them under a kind of their own
# means the log cannot be misread as delivery, and `assert_delivered(...,
# kind="consulted")` refuses them like any other `resolved` record.
#
# `levels.METRO_CODES` is bound in four signatures -- `theta_record`,
# `local_record`, `theta_prior`, `spine` -- and `run_model` passes `codes` to
# none of them. It defines the entire evidence set every party's theta and
# level is estimated from.
#
# `polling.REGISTER` was found by the guard test written the same day, and it is
# the worst of the three: `polling.load(path: Path = REGISTER)` freezes the poll
# register at import, so **pointing the model at a different register is
# silently ignored** while the read log would faithfully report the new path.
# Verified by rebinding it to a nonexistent file and watching `load()` return
# the same ten polls. Every internal caller invokes `load()` with no argument,
# and `run_model` reaches it through `validate_or_die`. The poll channel is
# worth 48 coherent seats at 2026 (§1.65), so a silently-ignored register is not
# a small thing.
#
# `montecarlo.HASH_SEED` was the same shape and is NOT listed, because it was
# REPAIRED rather than declared: `fix_hash_seed` now resolves it in the body.
# That is the better answer wherever it is available, and
# `test_no_numeric_module_constant_is_a_default_argument` insists on it. An
# entry here is for a binding that cannot be unfrozen without a wider change --
# `levels.METRO_CODES` is bound in four signatures across two call paths, and
# `polling.REGISTER` is a Path, which that numeric test cannot see at all.
FROZEN_DEFAULTS: frozenset[tuple[str, str]] = frozenset({
    ("levels", "METRO_CODES"),
    ("polling", "REGISTER"),
})


def _module_namespace(module_name: str):
    """The live module object for ``module_name``, or ``None``.

    Falls back to ``__main__`` when that IS the module asked for, because a
    module executed as a script is registered under ``__main__`` and NOT under
    its own name. Matched on the file, never on a guess: two modules can share
    a basename, and recording one module's constants under another's name would
    be a false delivery proof rather than a missing one.
    """
    module = sys.modules.get(module_name)
    if module is not None:
        return module
    main = sys.modules.get("__main__")
    main_file = getattr(main, "__file__", None)
    if main_file and Path(main_file).stem == module_name:
        return main
    return None


def note_module_constants(scenario: dict, where: str) -> None:
    """Record what THIS PROCESS holds for every declared module constant.

    Call it at the END of a run, not the start: it reads ``sys.modules`` and
    never imports anything, so a module the run never needed is recorded as
    ``not-imported`` rather than being dragged in by the instrumentation. An
    import performed for the sake of a log is a side effect, and instrumentation
    that has side effects is not instrumentation.

    Every record is ``kind="resolved"``. Read :func:`note_value` on what that
    is and is not evidence for.

    **A MODULE RUN AS A SCRIPT IS NOT IN ``sys.modules`` UNDER ITS OWN NAME**,
    and that made this function blind on the entry point `CLAUDE.md` documents
    for tracing -- `python src/montecarlo.py --city joburg --target 2021
    --run-dir /tmp/t`. There, `montecarlo` is `__main__`; nothing in its import
    closure imports it by name; so `sys.modules.get("montecarlo")` was `None`
    and all ten of its own declared constants recorded `not-imported`, on the
    one command whose purpose is to say what the run read. `compare_history`
    was unaffected -- it does `import montecarlo as M`, so the name is bound --
    which is exactly the shape of defect that survives: broken where you look
    by hand, correct where the panel runs. Measured 2026-08-27; see
    :func:`_module_namespace`.
    """
    for module_name, names in MODULE_CONSTANTS.items():
        module = _module_namespace(module_name)
        for const in names:
            full = f"{module_name}.{const}"
            if module is None:
                note_value(scenario, full, None, where=where,
                           kind="not-imported")
            elif not hasattr(module, const):
                note_value(scenario, full, None, where=where, kind="missing")
            else:
                note_value(scenario, full, getattr(module, const), where=where,
                           kind=("resolved-frozen"
                                 if (module_name, const) in FROZEN_DEFAULTS
                                 else "resolved"))


def delivery_log(source) -> dict:
    """The value-bearing read log of a run, from whatever holds it.

    Accepts a :class:`ModelRun`, a scenario dict, the log itself, or a
    ``--run-dir`` path (reading ``45_delivered.json``). One reader, because the
    alternative is every sweep growing its own and disagreeing about the shape.
    """
    if source is None:
        return {}
    if isinstance(source, (str, Path)):
        path = Path(source)
        if path.is_dir():
            path = path / "45_delivered.json"
        if not path.exists():
            return {}
        with path.open(encoding="utf-8") as handle:
            return json.load(handle) or {}
    scenario = getattr(source, "scenario", None)
    if isinstance(scenario, dict):
        return dict(scenario.get("_delivered") or {})
    if isinstance(source, dict):
        if "_delivered" in source:
            return dict(source["_delivered"] or {})
        return dict(source)
    raise TypeError(f"delivery_log cannot read a {type(source).__name__}")


def _match(recorded, expected, tol: float) -> bool:
    """Did a recorded value deliver ``expected``? Floats compared with ``tol``."""
    if isinstance(expected, bool) or isinstance(recorded, bool):
        return recorded is expected or recorded == expected
    if isinstance(expected, (int, float)) and isinstance(recorded, (int, float)):
        if not (math.isfinite(float(expected)) and math.isfinite(float(recorded))):
            return repr(recorded) == repr(expected)
        return abs(float(recorded) - float(expected)) <= tol * max(
            1.0, abs(float(expected)))
    return recorded == _delivery_value(expected)


def assert_delivered(run, name: str, expected=_UNRECORDED, kind: str | None = None,
                     tol: float = 1e-12) -> dict:
    """Prove that ``name`` reached the run, at ``expected``. Raise if it did not.

    **This is the assertion NULL-RESULTS.md §4.1 requires on every sweep**, and
    the error text is the deliverable: a sweep that cannot prove delivery has
    not measured anything, and must say so in those words rather than reporting
    a confident zero.

    ``run`` is anything :func:`delivery_log` reads -- a :class:`ModelRun`, a
    scenario, a ``--run-dir``. ``expected`` omitted asserts presence only.
    ``kind="consulted"`` demands the strong proof and refuses a ``resolved``
    record, which says the process held the value and not that anything read it.

    Returns the record, so a caller can report ``reads`` and the sites.
    """
    log = delivery_log(run)
    rec = log.get(name)
    if rec is None:
        near = [k for k in sorted(log) if name.split(".")[-1] in k and k != name]
        raise Undelivered(
            f"UNDELIVERED: {name}"
            + (f" was set to {expected!r} for this run" if expected is not _UNRECORDED
               else " was expected to be read by this run")
            + f", and the read log records no consultation of it at all.\n"
            f"\n"
            f"  THE RESULT OF THIS RUN IS VOID, NOT NULL. \"the change did "
            f"nothing\" and \"the change never arrived\" are the same "
            f"observation without a delivery proof, and this is the delivery "
            f"proof failing. Do not report a flat sweep here as INERT; it is "
            f"not a measurement of the model at all.\n"
            f"\n"
            f"  The usual cause is a module constant rebound in the parent "
            f"process: it does not cross a ProcessPoolExecutor boundary, so "
            f"every worker re-imports the default. Set it inside the worker, "
            f"or force serial (--jobs 1). The next most common is a value "
            f"bound as a function default at import time, which no later "
            f"rebinding can move (MODEL-LOG §1.33).\n"
            f"\n"
            f"  Third: the site that reads {name} may simply not be "
            f"instrumented. An absence here is a fact about the LOG, not about "
            f"the model -- add a note_value call at the read site and run again "
            f"before concluding anything."
            + (f"\n\n  Names the log does carry that look related: "
               f"{', '.join(near[:8])}" if near else "")
            + f"\n  The log carries {len(log)} name(s) in total.")
    if kind is not None and kind not in rec.get("kinds", []):
        raise Undelivered(
            f"UNDELIVERED at the strength asked for: {name} is in the read log "
            f"as {rec.get('kinds')}, and {kind!r} was required.\n"
            f"\n"
            f"  A 'resolved' record says THIS PROCESS held the value. It does "
            f"not say any code read it, and a lever behind a shut gate resolves "
            f"perfectly while doing nothing -- §1.68 measured a null with the "
            f"gate shut and believed it. Until a 'consulted' record exists at "
            f"the read site, a flat result is VOID, NOT NULL.")
    if expected is _UNRECORDED:
        return rec
    values = rec.get("values", [])
    if any(_match(v, expected, tol) for v in values):
        return rec
    raise Undelivered(
        f"UNDELIVERED at the wrong value: {name} was set to {expected!r} and "
        f"this run consulted it at {values!r}"
        + (f" (+{rec['dropped']} further distinct value(s), log truncated at "
           f"{DELIVERY_MAX_VALUES})" if rec.get("dropped") else "")
        + f", at {', '.join(rec.get('where', [])) or 'an unrecorded site'}.\n"
        f"\n"
        f"  THE RESULT OF THIS RUN IS VOID, NOT NULL. The run read something, "
        f"and it was not what the measurement set, so the measurement did not "
        f"happen. A flat score here says nothing about whether {name} matters.\n"
        f"\n"
        f"  Either the value was overwritten between being set and being read "
        f"-- a city TOML, `apply_city`, a scenario file, a default argument "
        f"resolved at import -- or two different things are being logged under "
        f"one name. Read the sites above and find which.")

def note_constant(scenario: dict, constant: str, party: str | None = None,
                  value=_UNRECORDED, where: str | None = None) -> None:
    """Record that a hand-typed constant was actually consumed by this run.

    Whether a plan judgement contaminates a backtest depends on the target,
    not on the constant: ``levels.py`` measures θ per party from transitions
    strictly before the target, and only a party the record cannot cover falls
    back to the number somebody typed. So ``DEFAULTS`` alone cannot say what a
    run read, and the in-sample accounting in ``backtest.py`` was asserting
    that ``theta_mode`` "is no longer read" while target 2021 quietly took
    ActionSA's 1.50 from it — a party worth 11% of that baseline, and one
    whose only local result IS the target.

    The run therefore measures its own reads and ``backtest.in_sample_banner``
    reports those. Kept on the scenario (like ``_ward_pr_trusted``) so it
    travels into ``forecast_summary.json`` with everything else: values are
    plain lists, because that file is JSON.

    ``value`` IS THE DELIVERY PROOF, and it is optional only because this
    function predates it. A name in the log says a constant was consulted; it
    cannot say *at what*, and those are different facts. A sweep that sets
    ``LEVEL_DF = 1000`` and gets a flat answer has learned nothing at all
    unless the run recorded reading 1000 — see :func:`note_value` and
    :func:`assert_delivered`. Passing ``value`` writes the same read into the
    value-bearing log as well; ``where`` names the site, defaulting to the
    constant's own name.
    """
    users = scenario.setdefault("_constants_read", {}).setdefault(constant, [])
    who = party or "(all)"
    if who not in users:
        users.append(who)
    if value is not _UNRECORDED:
        note_value(scenario, constant, value,
                   where=where or f"note_constant:{constant}", who=party)


def read_scenario_file(path) -> tuple[dict, dict]:
    """``(overrides, metadata)`` from a scenario JSON, unknown keys rejected.

    One reader for every consumer. ``backtest.py`` used to apply a scenario
    file with its own loop and no validation at all, so a typo'd key was
    dropped in silence and the run reported itself as the config under test
    while actually scoring DEFAULTS — two identical rows in an A/B table with
    nothing to say they were the same model twice.
    """
    with open(path, encoding="utf-8") as handle:
        overrides = json.load(handle)
    if not isinstance(overrides, dict):
        raise SystemExit(f"{path}: a scenario file must be a JSON object")
    metadata = {k: overrides.pop(k) for k in SCENARIO_METADATA if k in overrides}
    unknown = set(overrides) - set(DEFAULTS)
    if unknown:
        raise SystemExit(f"unknown scenario keys in {path}: {sorted(unknown)} "
                         f"(scenario metadata: {', '.join(SCENARIO_METADATA)})")
    return overrides, metadata


def blend_poll_centre(mu: float, share: float, w_raw: float,
                      credence: float = 1.0) -> tuple[float, float]:
    """Blend a poll reading into a modelled centre. Returns ``(centre, w)``.

    **A seam, added 2026-08-25 because the invariant could not be tested without
    one.** This arithmetic lived inline in `run_model`, so the only guard on it
    was `tests/test_regressions.py` asserting that the LITERAL SOURCE LINE
    ``_w = min(_pg.blend_weight(_psd, _msd), _cap)`` still appeared in the file.
    That test passed for weeks while the property it claimed to guard — "the
    poll weight stays bounded by `weight_cap`" — was FALSE, because `_cap` is
    1.0 under `SIGMA_TWO_TERM`; and then it went red on a variable rename that
    changed no behaviour at all. A test that fails on cosmetics and passes on
    defects is worse than none.

    The invariants, now assertable and asserted:

    * `w` is in [0, 1], so the result is a CONVEX combination and lies between
      `mu` and `share` — it can never overshoot the poll or move away from it;
    * `credence = 0` returns `mu` exactly: the poll is ignored, not
      approximately ignored;
    * the result is monotone in `credence` — believing a poll more moves the
      centre further toward it, never past it;
    * a `w_raw` above 1, however it arose, is clamped rather than trusted.

    `credence` is the reader's dial (`poll_credence`, DEFAULTS 1.0 = identity).

    sources:
        MODEL-LOG 1.95 — poll_credence, and why belief is a dial not a switch
        MODEL-LOG 1.96 — why the source-text test it replaces was harmful
        ARCHITECTURE.md, "Order of work" step A
    """
    w = min(max(float(w_raw) * float(credence), 0.0), 1.0)
    return (1.0 - w) * float(mu) + w * float(share), w


def apply_overrides(scenario: dict, overrides: dict) -> dict:
    """Merge a validated override dict into a scenario, dicts key by key."""
    for key, value in overrides.items():
        if isinstance(scenario.get(key), dict) and isinstance(value, dict):
            scenario[key].update(value)
        else:
            scenario[key] = value
    return scenario


def load_scenario(args) -> dict:
    scenario = copy.deepcopy(DEFAULTS)
    if args.config:
        overrides, _metadata = read_scenario_file(args.config)
        apply_overrides(scenario, overrides)
    parse_set(args.set or [], scenario)
    if args.draws:
        scenario["draws"] = args.draws
    if args.seed:
        scenario["seed"] = args.seed
    return scenario


# --------------------------------------------------------------------------
# evidence blending (E2 + E4)
# --------------------------------------------------------------------------

def blended_centres(
    scenario: dict,
    base_city: dict[str, float],
    prior_pr_share: dict[str, float],
    bye: dict[str, tuple[float, float]],
    trace: "Trace | None" = None,
) -> tuple[dict[str, float], dict[str, str]]:
    """Central citywide level per party at the target, from θ modes tilted by evidence.

    Start from the §3.5 θ-mode view (the baseline NPE share × mode). For parties
    with meaningful by-election weight, the implied level (the previous LGE's PR
    share + weighted delta) is clamped to §3.5's range — a concentrated party's
    stronghold swing cannot claim an absurd citywide level — and blended in at
    w_bye. Returns the centres and a note per adjusted party for the report.
    """
    w = scenario["w_bye"]
    notes: dict[str, str] = {}
    centres: dict[str, float] = {}
    prior = scenario.get("theta_prior") or {}

    # Two paths, and every party takes exactly one of them.
    #
    # WITHOUT HISTORY. A party with no national share has no θ, because θ is
    # the ratio of a local share to a national one and there is nothing to
    # divide by. That is not a gap to be filled with a judgement — it is a
    # different question, and ``pools.arrival_rules`` has already answered it
    # from the arrival record, seeding the party and handing back a band whose
    # mode is 1.0 (the seed IS the estimate). This branch exists because the
    # code used to fall through to ``theta_mode`` instead: ActionSA arrived in
    # 2021 with no 2019 vote, was correctly seeded at 11.07% by the arrival
    # rules, and then had that LOCAL estimate multiplied by 1.50 — a
    # NATIONAL-to-local conversion factor, applied to something already local,
    # and one chosen knowing what ActionSA went on to do. It reached the
    # drawer at 16.61%.
    #
    # WITH HISTORY. Everything ``levels.theta_prior`` covers: the party's own
    # retention record weighted by what it is worth and shrunk toward the
    # common centre, or the centre itself for a party holding a national vote
    # that has not yet faced a local election (MK in 2026).
    seeded = scenario.get("pool_seeds") or {}
    bands = scenario.get("pool_seed_bands") or {}
    # THE SPINE (task #22). Where ``levels.spine`` has a level for a party, it
    # is the answer: it already weighed the party's national route against its
    # own last local result by how much θ evidence the party has, and returned
    # the blend. The θ-only branch below is what runs for a party the spine
    # cannot reach — and for a seeded arrival, which has neither record and is
    # sized from the arrival record instead.
    # F37: AN ABSENT SPINE AND A SPINE THAT REACHED NOBODY ARE DIFFERENT
    # FACTS, and both degraded every party to the θ route below in silence —
    # a run with no spine at all was indistinguishable from one where the
    # spine ran and reached everyone. Recorded rather than repaired, because
    # the fallback itself is correct: what was missing is any record that it
    # happened. `None` means the spine block did not run; 0 means it ran and
    # placed nobody.
    _spine_level = scenario.get("spine_level")
    note_value(scenario, "spine_level.reached",
               -1 if _spine_level is None else len(_spine_level),
               where="montecarlo:blended_centres", kind="consulted")
    spine_level = _spine_level or {}
    poll_levels = scenario.get("poll_levels") or {}
    for party, base in base_city.items():
        # WHICH ROUTE SET THE LEVEL, so the note can say. It used to say
        # "θ-mode" whichever of the four ran, and only the last one IS a θ
        # mode: at joburg 2026 all NINE tilted parties took the SPINE route, so
        # the label was wrong for every one of them on the live forecast. Not
        # latent — that is what the published run says today. §1.121
        if party in poll_levels:
            # A poll outranks the arrival record for a party with no record.
            mode_level = float(poll_levels[party])
            route = "poll level"
            notes[party] = f"level from poll: {mode_level:.2%}"
        elif seeded.get(party, 0.0) > 0:
            band = bands.get(party)
            mode_level = base * (float(band[1]) if band else 1.0)
            route = "seeded level"
        elif party in spine_level:
            mode_level = spine_level[party]
            route = "spine level"
        elif party in prior:
            mode_level = base * prior[party][1]
            route = "θ-mode"
        else:
            # NO PARTY-SPECIFIC FALLBACK. Until 2026-08-19 three more branches
            # sat here -- `theta_mode` (six named parties), `individual_theta`
            # (six more) and `f_other` -- and all three were dead: the spine
            # reaches every party at every runnable target, so `spine_level`
            # above always answers first. They were carried in DEFAULTS,
            # `apply_city`, two city tomls and the register for weeks after
            # being certified inert.
            #
            # A party that reaches here has a national baseline, no spine
            # level, no theta prior and no seed, which the three branches
            # above make impossible. If that ever changes it must be a loud
            # failure rather than a typed number for whichever parties someone
            # happened to name in 2026. MODEL-LOG §1.52.
            raise AssertionError(
                f"{party} has a national baseline but no spine level, no theta "
                f"prior and no arrival seed. That combination was previously "
                f"absorbed by a per-party constant; there is no longer one. "
                f"See MODEL-LOG §1.52.")

        centre = mode_level
        if party in bye and w > 0:
            weight_sum, delta = bye[party]
            if weight_sum >= BYE_MIN_WEIGHT:  # enough to mean anything
                # THE BALLOTS DIFFER HERE ON PURPOSE, AND IT WAS MEASURED
                # (§1.97 F46, §1.110). `delta` is built by `byelections.py`
                # against the WARD ballot; `prior_pr_share` is the PR ballot.
                # That looks like a units error and is not one: the delta is a
                # within-ward DIFFERENCE whose two terms are both on the ward
                # ballot, so the mismatch enters only through how the ballots
                # move relative to each other.
                #
                # Tested on the 2016 -> 2021 transition across the eight
                # metros, where both movements are known. THE ANSWER DEPENDS ON
                # PARTY SIZE and §1.110 got it wrong by measuring at one
                # threshold (§1.113 corrects it):
                #
                #   base >= 0.5%   n=45   additive 1.052pp   proportional 1.237
                #   base >= 1%     n=34   additive 1.096pp   proportional 0.910
                #   base >= 5%     n=22   additive 1.347pp   proportional 1.107
                #   weighted by size      additive 1.677pp   proportional 1.398
                #
                # The ratio is ward_share/pr_share; for a party at 0.1% that is
                # a quotient of two noisy numbers, so dividing by it amplifies
                # noise faster than it removes bias. Above ~1% the ratio is well
                # estimated and proportional is the better description — which
                # is the same threshold shape `run_model`'s OWN ratio block
                # uses a few hundred lines below (pc > 0.001, clipped to
                # WARD_PR_RATIO_MIN/MAX). NOT `levels.ward_pr_ratios`, which
                # applies NEITHER — this comment said so until 2026-08-28 and
                # was wrong when written (§1.121). The difference is not
                # cosmetic: it is why the two are not interchangeable.
                #
                # ADOPTED 2026-08-28 on the owner's decision, and applied
                # ONLY where the ratio is trustworthy — `_ward_pr_trusted`
                # carries exactly the parties above the 0.001 threshold, with
                # the same [WARD_PR_RATIO_MIN, WARD_PR_RATIO_MAX] clip the
                # model already uses for this quantity. Everyone else keeps the
                # additive form, which the sweep says is better for them.
                # §1.109, §1.110, §1.113, §1.114.
                # F34 CASE (3): A WARD-ONLY PARTY HAS AN UNKNOWN BASE, NOT A
                # ZERO ONE. `prior_pr_share.get(party, 0.0)` below conflates
                # three states: a party that stood and polled (the base is
                # real and `delta` is a genuine within-ward SWING); one that
                # did not exist (zero IS the value, and `byelections.py`
                # measured its deltas against that same zero, so `delta` is a
                # LEVEL); and one that stood on the WARD ballot only, where
                # the PR base is unknown and `0 + delta` is neither.
                #
                # Only the third is wrong, and it is UNREACHABLE today: at
                # joburg 2026 the single party reaching this block with no PR
                # share is MK, which did not exist (2021 PR 0.000%, ward
                # 0.000%, and all eight of its contests carry base 0.0000).
                # The real case-(3) parties are under the weight bar — IND at
                # 8.4 against BYE_MIN_WEIGHT 30.0. Skipped rather than raised:
                # it is a legitimate data state, not an impossible one, and
                # killing a live run over it would be worse than declining to
                # tilt. §1.121
                if (party not in prior_pr_share
                        and (scenario.get("_prior_ward_share") or {}
                             ).get(party, 0.0) > 0):
                    note_value(scenario, "bye.ward_only_base_skipped", party,
                               where="montecarlo:blended_centres bye base",
                               kind="consulted")
                    print(f"  !! {party}: by-election weight {weight_sum:.1f} "
                          f"and no previous PR share, but it DID stand on the "
                          f"ward ballot. Its PR base is unknown, not zero, so "
                          f"the by-election tilt is SKIPPED. MODEL-LOG §1.121.")
                    centres[party] = centre
                    continue
                _r = (scenario.get("_ward_pr_trusted") or {}).get(party)
                delta_pr = (delta / _r) if _r else delta
                implied = prior_pr_share.get(party, 0.0) + delta_pr
                if party in prior:
                    low, high = prior[party][0], prior[party][2]
                    mid = prior[party][1] or 1.0
                else:
                    low, high = PLAN_BOUNDS.get(party, (0.0, float("inf")))
                    mid = 1.0
                    if party in PLAN_BOUNDS:
                        # The BOUND, not just the fact of one: a per-party
                        # delivery proof, and the shape that shows a value log
                        # has to be keyed on (name, who) and not on name alone.
                        note_constant(scenario, "plan_bounds", party,
                                      value=PLAN_BOUNDS[party],
                                      where="montecarlo:blended_centres bye clamp")
                # THE CLAMP IS ANCHORED ON THE LEVEL THE MODEL BELIEVES, not on
                # the national baseline. θ's band is a band on the NATIONAL
                # route; multiplying it by `base` bounds the by-election
                # evidence to what a party's national share could become, which
                # is precisely the assumption task #22 exists to abandon.
                #
                # ActionSA 2026 is the case. The spine puts it at 15.2% from its
                # own 2021 local result; the by-elections independently imply
                # 18.7%; and the clamp, computed as high × 5.99% national, cut
                # that to 7.5% and dragged the blended centre DOWN to 12.1%. Two
                # pieces of evidence agreeing that the party is larger than its
                # national share were overruled by a bound derived from the
                # national share. The PA was clamped from 21.9% to 7.1% the same
                # way.
                #
                # The band is therefore applied as a RELATIVE spread — low/mode
                # and high/mode, which is what θ's dispersion actually measures —
                # around whatever central level the spine settled on.
                anchor = mode_level if mode_level > 0 else base
                clamped = min(max(implied, (low / mid) * anchor),
                              (high / mid) * anchor)
                centre = (1 - w) * mode_level + w * clamped
                _n_bye, _sd_bye = (scenario.get("_bye_spread")
                                   or {}).get(party, (0, 0.0))
                notes[party] = (
                    # F38: THIS WAS AN ASSIGNMENT AND THE POLL ROUTE'S NOTE
                    # DIED HERE. A party whose level came from a poll and was
                    # then tilted by by-elections reported only the second
                    # half. The metro-poll block later already appends; this one
                    # now does too, so the note reads in the order the
                    # contributions were applied. TEXT ONLY — `notes` reaches
                    # `print`, `ModelRun.notes` and the trace, and no
                    # arithmetic anywhere; `route_notes` has no reader at all.
                    #
                    # Latent today: the poll route and this block are mutually
                    # exclusive at every target that exists. `national_polls`
                    # returns nothing at 2026 (both admitted polls are
                    # metro-scope), and `bye` is empty at all sixteen backtest
                    # city-years. It becomes reachable the moment a national
                    # poll declared for 2026 names a seeded arrival that also
                    # clears BYE_MIN_WEIGHT. §1.121
                    (notes[party] + " | " if party in notes else "")
                    + f"{route} {mode_level:.1%} → {centre:.1%} "
                    f"(by-elections imply {implied:.1%}"
                    # WHICH CONVERSION RAN, because the two are a 0.2pp
                    # difference on the DA and invisible otherwise. A trace that
                    # cannot say which branch it took cannot be used to check
                    # this change later.
                    + (f", ward delta {delta:+.2%}/ratio {_r:.3f}" if _r
                       else f", ward delta {delta:+.2%} additive")
                    # THE SPREAD, NOT JUST THE MEAN. For a party with no
                    # previous result nothing differences out and this is a
                    # LEVEL read off a handful of self-selected wards: MK's
                    # eight run 0.74%-22.90%, sd 9.1pp, so its own 95%
                    # interval is [3.8%, 17.4%] against a clamp of [9.3%,
                    # 13.7%]. A reader who sees only "imply 10.6%" cannot
                    # tell that from a citywide measurement. §1.121
                    + (f", {_n_bye} contests sd {_sd_bye:.1%}" if _n_bye
                       else "")
                    + (f", clamped to {clamped:.1%}" if clamped != implied else "")
                    + f", w_bye {w})"
                )
        centres[party] = centre
    # F35 — THE LOOP IS OVER `base_city`, SO A `poll_levels` ENTRY FOR A PARTY
    # OUTSIDE IT IS DISCARDED HERE: no centre, no note, no warning. This
    # assertion is the gate on WIDENING that loop, and it exists because
    # widening it is simultaneously number-moving and useless.
    #
    #   USELESS: `universe` and `index` are built from the same dict and passed
    #   to this function, so a party absent from `base_city` is absent from the
    #   draw matrix and every consumer downstream ignores whatever centre it
    #   were given.
    #
    #   NUMBER-MOVING: `compress_levels` renormalises over the MEMBERSHIP of
    #   `centres` — `total` and `freed` are both sums over it — and it ships
    #   live at level_shrink = 0.35. One extra key rescales EVERY party.
    #
    # So the repair is ONE change spanning universe construction, this loop and
    # `compress_levels`' normalisation base, or it is this assertion. If you
    # are here because this fired, you are doing the first and you must do all
    # three: a green suite after widening the loop alone would be wrong.
    #
    # Passes today by construction (`centres` is written only inside this loop,
    # which has no `continue`/`break` and a raising `else`) and empirically —
    # the dropped set is empty on all seventeen runnable configurations, because
    # `national_polls` returns nothing at 2026 and the only 2021 candidate,
    # ASA, is seeded and therefore in `base_city`. §1.121
    if set(centres) != set(base_city):
        raise AssertionError(
            f"`blended_centres` no longer returns exactly the baseline's "
            f"parties: added {sorted(set(centres) - set(base_city))}, dropped "
            f"{sorted(set(base_city) - set(centres))}. `compress_levels` "
            f"renormalises over this membership at level_shrink="
            f"{scenario.get('level_shrink')}, so this moved every party. See "
            f"the comment above — the repair spans three places or it is none.")
    before = dict(centres)
    centres = compress_levels(centres, scenario)
    if trace:
        # Before and after, per party, plus the ratio. The shrink's whole claim
        # is an ORDERING -- the big come down, the small go up, monotonically in
        # size -- and that is checkable at a glance from this file rather than
        # by reasoning about the formula. MODEL-LOG §1.44.
        trace.put("30_centres", {
            "before_shrink": before,
            "after_shrink": centres,
            "ratio": {p: (centres[p] / before[p]) if before.get(p) else None
                      for p in before},
            "level_shrink": scenario.get("level_shrink"),
            "level_shrink_scale": scenario.get("level_shrink_scale"),
            "route_notes": notes,
        })
    return centres, notes


def _dirichlet_scale(scenario: dict) -> float:
    """Multiplier on every pool's fitted Dirichlet concentration.

    THE MODEL'S DOMINANT WIDTH LEVER, and until 2026-08-20 it had no handle at
    all. The width budget (§1.48) measured the within-pool Dirichlet supplying
    **83-98% of drawn variance for every party except the ANC and DA**, while
    `alpha` sat in the register as a concentration guard fitted by method of
    moments and was never swept against realised width.

    A Dirichlet's variance falls as its concentration rises, so a scale above
    1.0 NARROWS the forecast and below 1.0 WIDENS it. 1.0 is exactly the fitted
    value and is the identity.

    It multiplies rather than replaces because the fit is per pool and carries
    real information about which pools are volatile; a single replacement value
    would throw that away to move one number.
    """
    return float(scenario.get("dirichlet_scale") or 1.0)


def compress_levels(centres: dict[str, float], scenario: dict) -> dict[str, float]:
    """Pull each central level down by its own size, then give the mass back.

    THE FAULT THIS ADDRESSES. Across nine city-years the model over-forecasts
    the top of the ballot and under-forecasts the middle by almost exactly the
    same amount — ranks 1-3 **+32.30pp** signed against ranks 4-12 **−36.20pp**.
    That is not a level error in one party; it is a share vector whose spread is
    too wide, and the standard remedy for a vector of noisy estimates is to
    shrink it toward its centre.

    THE FORM. Each party keeps ``1 - c * s/(s + h)`` of its level, where ``s``
    is that level and ``h`` (``level_shrink_scale``) is the share at which the
    pull reaches half strength; the freed mass is returned by renormalising to
    the original total. The pull is therefore smooth and monotone in size —
    near zero for a micro-party, near ``c`` for a dominant one — which is the
    point. A hard threshold was measured first and is knife-edged: the review's
    8% cut gives −13.2% at 5%, −5.6% at 8% and −0.8% at 15%, so where the line
    falls decides the answer. This form has no line.

    WHY IT IS NOT SCOREBOARD-FITTING (ITERATING.md rule 10). The parameter is
    not chosen on the nine city-years it is scored against. Fitted on
    **Johannesburg 2016 alone** it comes out at 0.375, and applied to the eight
    2021 metros — a different cycle, seven of them different cities, none of
    them seen by the fit — it improves 6 of 8 and takes the reconstructed seat
    error from 284 to 258. Leave-one-city-year-out across all nine chooses
    0.350 in every one of the nine folds. A constant that lands in the same
    place from one city-year, from nine, and across a cycle boundary is a
    property of the model rather than of the scoreboard.

    ROBUSTNESS OF ``h``. Swept 0.02 → 0.40, twenty-fold, the correction improves
    7 of 9 at every value and the gain runs −11.7, −13.6, −13.0, −11.4, −9.6,
    −9.3, −7.6, −5.6pp. There is no cliff, so ``h`` is a scale rather than a
    tuned constant; 0.04 is its optimum and 0.06 is within a third of a point.

    THE COST, STATED. The freed mass is returned by uniform renormalisation,
    which is a multiplicative boost, and there are many micro-parties to
    receive it: ranks 13+ go from **+0.78pp to +8.68pp**, an unbiased band
    turned into an over-forecast one. Three targeted redistributions were
    measured — to predicted ranks 4-12, to everything below the predicted top
    three, and weighted by remaining room — and all three balance the bands
    better while scoring WORSE on both summed absolute error and seats. That
    trade is recorded rather than hidden, and it is the first thing to attack
    if this is revisited.

    Off by default (``level_shrink = 0.0`` is exactly the identity).
    """
    c = float(scenario.get("level_shrink") or 0.0)
    h = float(scenario.get("level_shrink_scale") or 0.04)
    if c <= 0.0 or h <= 0.0 or not centres:
        return centres
    total = sum(v for v in centres.values() if v > 0)
    if total <= 0:
        return centres
    kept = {p: (v * max(1.0 - c * v / (v + h), 1e-9) if v > 0 else v)
            for p, v in centres.items()}
    freed = sum(v for v in kept.values() if v > 0)
    if freed <= 0:
        return centres
    scale = total / freed
    return {p: (v * scale if v > 0 else v) for p, v in kept.items()}


# --------------------------------------------------------------------------
# the draw
# --------------------------------------------------------------------------

def pool_spec(scenario, centres, index, ipf_out=None):
    """Build the per-pool draw specification for the weighted engine (§1.29).

    A pool is a body of voters choosing between the same parties, and a party
    may draw from more than one. That last point is not a refinement for
    awkward entrants -- it is what the ANC has needed all along. MK took 71% of
    its Johannesburg vote out of the ANC (flow −0.712 per point) while standing
    on IFP ground (+0.50), and the IFP lost nothing: 1.47% to 1.41%. So the ANC
    was holding voters from at least two pools, invisibly, because nobody was
    contesting the second one. No partition can express that.

    Each pool gets ``members`` (party -> the weight of that party's support
    drawn from this pool, weights summing to 1 across pools per party), a
    ``shift`` triangular in points on the base, and an ``alpha``. Weight 1.0
    everywhere reduces this to a plain per-group draw, which is the
    regression test.
    """
    # THE CENTRES MUST BIND, and until now they did not.
    #
    # A pool's votes are its registration times a drawn turnout, and its members
    # split it by a Dirichlet whose mean is `props`. `props` was
    # members x centre, normalised WITHIN the pool — so a party's realised
    # citywide share was (pool's share of the city) x (its share of that pool),
    # and its centre only ever moved the second factor. For a party that already
    # holds most of its pool that is almost no leverage at all: cutting the
    # ANC's centre by 15% moves its normalised share of the Black African pool
    # by about a tenth of that, because the normaliser falls with it.
    #
    # It is why the model's largest parties sit +36.6pp over nine city-years
    # while ranks 4-12 sit -43.4pp, and why blending an accurate metro poll into
    # the ANC's centre at weight 0.92 moved its realised share by half a point.
    # The level layer was writing to a variable the draw barely read.
    #
    # Two margins are known and neither is a modelling choice: each pool holds a
    # counted number of voters, and each party's citywide level is what the
    # spine, the by-elections and the polls have just agreed on. Iterative
    # proportional fitting is the standard way to impose both, it preserves
    # non-negativity and every structural zero, and it lands on the matrix
    # closest to the starting one in KL divergence — so it ADJUSTS the measured
    # pool vectors rather than replacing them. `pools.balance_margins` already
    # does exactly this for the ecological fit; this is the same procedure
    # applied to the same object one stage later.
    names = list(scenario["pools"])
    parties = sorted({p for cfg in scenario["pools"].values()
                      for p in cfg["members"] if p in index})
    if not names or not parties:
        return {}
    pidx = {p: j for j, p in enumerate(parties)}
    R = np.zeros((len(names), len(parties)))
    pool_votes = np.zeros(len(names))
    for g, name in enumerate(names):
        cfg = scenario["pools"][name]
        pool_votes[g] = float(cfg["registered"]) * float(cfg["turnout"][1])
        for p, w in cfg["members"].items():
            if p in pidx and float(w) > 0:
                R[g, pidx[p]] = float(w) * max(centres.get(p, 0.0), 1e-9)
    rows = R.sum(axis=1, keepdims=True)
    R = np.divide(R, rows, out=np.zeros_like(R), where=rows > 0)

    # The party margin is the centres, renormalised over the parties the pools
    # actually carry — an individually-drawn party is not in this system and
    # must not be given pool votes.
    want = np.array([max(centres.get(p, 0.0), 0.0) for p in parties])
    # FEASIBILITY FIRST. IPF can only satisfy two margins that CAN both hold. A
    # party can take at most all of the pools it belongs to, so its ceiling is
    # the share of the city those pools hold; asking for more is unsatisfiable
    # and the iteration runs to its cap and raises.
    #
    # It did, at Nelson Mandela Bay, where seven parties carry a centre and
    # belong to no pool at all. The failure was caught and the run continued
    # with the centres NOT binding — so that city was silently forecast by the
    # old, worse mechanism while the other eight used the new one, and its
    # small-party seats came out at 9 against an actual 16.
    #
    # THIS IS A CLIP ON A SYMPTOM, NOT A FIX. What it reports is that the level
    # layer and the pool layer disagree, and neither knows about the other. The
    # PA at Johannesburg 2026 is the standing case: it belongs to exactly one
    # pool (Coloured, weight 1.0, and at 2026 that weight is `identified=False`
    # — a bound-limited artefact, not a measurement), that pool casts about
    # 66,700 votes, and the spine plus the by-election blend between them ask
    # for about 68,000 (until 2026-08-18 `pa_contestation_uplift` was a third
    # contributor; it is deleted, and its share of this is gone). That is 102%
    # of every Coloured vote in the city. Which side is wrong — a vector too
    # narrow or a level too high — is not settled here and is not settled by
    # this clip. The clip only makes the disagreement SAFE and VISIBLE instead
    # of silent. See MODEL-LOG §1.33.
    # THE CEILING IS WEIGHT-AWARE. It was an INDICATOR until 2026-08-17 —
    # `1.0 if members.get(pp, 0.0) > 0 else 0.0` — so a membership of 0.00019
    # counted exactly like one of 1.0, and a party's ceiling was the size of
    # every pool it touched at all rather than the size of the pools it
    # actually draws from.
    #
    # That was survivable while the fit emitted hard zeros. It stopped being
    # survivable the moment `pools.balance_within_bounds` began seeding every
    # zeroed cell (§1.38): the Duncan-Davis projection moved 159 of the PA's
    # 27,346 Johannesburg votes into its three other pools, flipping three
    # indicator bits, and its declared ceiling went from the Coloured pool
    # alone (0.0673 of votes cast) to 1.0000. Across the fits, parties sitting
    # at a ceiling of exactly 1.0 went from 6 of 54 to 53 of 54 at Johannesburg
    # 2021, and the mean ceiling from 0.622 to 0.992. THE GUARD SHIPPED FOR F1
    # WENT BLIND, and its silence — "0 fell back, nothing held" — was reported
    # as evidence the projection had removed the problem. It had not: the PA
    # still draws 99.18% of its vote from a pool casting 6.73% of the ballots
    # and its 2026 centre still asks for about 109% of that pool.
    #
    # The right ceiling is the largest citywide share a party can reach while
    # holding its own weight vector with every pool rate at most 1:
    #
    #     min over pools g with w_g > 0 of  poolshare_g / w_g
    #
    # A party spread evenly over everything keeps a ceiling near 1; a party
    # that draws 99% of its vote from a 7% pool is bounded near 7%, which is
    # the arithmetic truth about it. See MODEL-LOG §1.41.
    # THE CEILING IS AN INDICATOR, AND THE WEIGHT-AWARE VERSION WAS TRIED AND
    # REJECTED ON MEASUREMENT (2026-08-17, MODEL-LOG §1.41).
    #
    # The defect is real and is not fixed here: a membership of 0.00019 counts
    # like one of 1.0, so once `pools.balance_within_bounds` began seeding every
    # zeroed cell, 74 of 75 parties had a ceiling of exactly 1.0 at 2026 and the
    # capacity guard could no longer fire for anybody. Its silence was reported
    # as evidence the projection had removed the problem.
    #
    # The obvious repair — `min over pools g with w_g > 0 of poolshare_g / w_g`,
    # the largest citywide share a party can reach holding its weight vector
    # with every pool rate at most one — is ARITHMETICALLY SOUND AND EMPIRICALLY
    # A DISASTER. Nine city-years: coherent seat error 306 -> 486, and Mangaung
    # alone 10 -> 112 with everything else held (measured by reverting this line
    # and nothing else).
    #
    # WHY, and it is the interesting part. The bound assumes a party's pool
    # composition is FIXED. It is not: the draw varies each pool's turnout and
    # each party's within-pool rate, so the realised composition moves. After
    # seeding, every party carries a small weight in every pool -- and for a
    # SMALL weight in a SMALL pool, `poolshare / w` collapses below the party's
    # own actual share. A 0.02 weight on a pool holding 0.005 of the vote caps
    # the party at 25% of the city however it actually votes. The formula bounds
    # a quantity the model does not hold still.
    #
    # So the guard needs a bound that is invariant to the draw, not a tighter
    # one. Left as an indicator, with the defect stated, rather than shipping a
    # constraint that is wrong in a different direction. ITERATING.md: worse
    # does not ship, and "arithmetically defensible" is not a measurement.
    ceiling = np.array([
        float((pool_votes * np.array([
            1.0 if float(scenario["pools"][nm]["members"].get(pp, 0.0)) > 0 else 0.0
            for nm in names])).sum() / max(pool_votes.sum(), 1e-9))
        for pp in parties])

    if want.sum() > 0:
        want = want / want.sum()
    # Normalise BEFORE capping, not after. The old order clipped at the ceiling
    # and then divided by the new sum, which — the sum having just fallen —
    # scaled the clipped party straight back over the ceiling it was clipped
    # to. `capped_targets` keeps the total instead of restoring it to the
    # offender.
    cap = POOL_CAPACITY_MARGIN * ceiling
    asked = want.copy()
    want = capped_targets(want, cap)
    headroom = {p: (float(asked[j]) / float(cap[j]) if cap[j] > 0 else float("inf"))
                for j, p in enumerate(parties)}
    moved = float(np.maximum(asked - cap, 0.0).sum())
    if moved > 1e-9:
        over = [f"{parties[j]} {headroom[parties[j]]:.0%} of capacity"
                for j in np.argsort(-(asked - cap))[:4]
                if asked[j] - cap[j] > 1e-9]
        print(f"  ! {moved:.2%} of the citywide level asked for more than a "
              f"party's own pools can supply and was moved to the parties that "
              f"can hold it ({'; '.join(over)}). Those parties belong to fewer "
              f"pools than their level implies; the level and the pool vectors "
              f"disagree and this clip does not settle which is wrong.")
    if ipf_out is not None:
        ipf_out["headroom"] = headroom
        ipf_out["cap_votes"] = cap * float(pool_votes.sum())
    try:
        import pools as _pl
        R = _pl.balance_margins(R, pool_votes, want * pool_votes.sum())
    except Exception as exc:
        # THE TWO MARGINS CAN GENUINELY CONFLICT, and when they do the POOL
        # margin wins: a pool's voters vote for somebody, whereas a party's
        # centre is the model's belief. Nelson Mandela Bay is the case — its
        # Indian/Asian pool holds 2.3% of the city's votes and its sixteen
        # members' centres do not add to that between them, so no matrix
        # satisfies both and `balance_margins` runs to its cap and raises.
        #
        # Abandoning the balance entirely was worse than a partial one: it
        # dropped that city back to the un-bound centres while the other eight
        # used the new mechanism, and its small-party seats came out at 9
        # against an actual 16. A bounded alternating scaling that ENDS on the
        # row pass gets most of the way and leaves every pool exactly allocated.
        R = partial_balance(R, pool_votes, want * pool_votes.sum())
        print(f"  ! pool and party margins are not jointly satisfiable "
              f"({exc}); used a partial balance that keeps every pool exactly "
              f"allocated and gets the party levels as close as it can")
    # Kept so the draw can re-balance against SHOCKED centres. See draw_pools:
    # applying a party's level shock inside the pool and renormalising there
    # cancels it for a dominant member, which left the top three drawing a
    # realised sd(log) of 0.078 against a measured 0.26.
    # Written into a caller-supplied box, NOT into the spec and NOT onto the
    # scenario. `spec` is a dict of pools that several callers iterate expecting
    # every value to be a pool tuple, so a metadata key in it took out
    # tests/test_drawer.py; and the scenario is SERIALISED into
    # forecast_summary.json, so a numpy array on it produced malformed JSON that
    # broke the site build. Two ways to leak the same object, both found by
    # something downstream rather than by reading.
    if ipf_out is not None:
        ipf_out.update({"R0": R.copy(), "pool_votes": pool_votes,
                        "parties": parties, "pidx": pidx, "names": names})

    spec = {}
    for g, name in enumerate(names):
        cfg = scenario["pools"][name]
        members = {p: float(w) for p, w in cfg["members"].items()
                   if p in index and float(w) > 0}
        if not members:
            continue
        idx = [index[p] for p in members]
        props = np.array([R[g, pidx[p]] if p in pidx else 0.0 for p in members])
        if props.sum() <= 0:
            props = np.array([members[p] for p in members])
        props = props / props.sum()
        levels = np.array([members[p] * centres.get(p, 0.0) for p in members])
        spec[name] = (idx, float(cfg["registered"]),
                      tuple(cfg["turnout"]), props,
                      float(cfg["alpha"]) * _dirichlet_scale(scenario),
                      list(members), levels, dict(members))
    return spec


def _balance(R, electorate, party_votes):
    import pools as _pl
    return _pl.balance_margins(R, electorate, party_votes)


def make_drawer(scenario, base_city_d, centres, index, rng):
    """Return a function drawing one citywide PR target vector.

    The returned closure carries an ``ipf_stats`` attribute — how many per-draw
    balances were attempted, how many fell back, and which parties were pinned
    at their pool capacity and by how much. ``run_model`` reads it onto the
    ``ModelRun`` so the fallback rate can be asserted in a test and printed in
    the run report, rather than being swallowed. See MODEL-LOG §1.33.
    """
    n = len(index)
    base_city = np.zeros(n)
    for party, i in index.items():
        base_city[i] = base_city_d.get(party, SHARE_FLOOR)

    if not scenario.get("pools"):
        raise SystemExit(
            "no pools: the model draws from measured voter pools, and there is "
            "nothing to fall back on. Run:\n"
            "  python src/pools.py --city <city> --target <year> --emit")
    ipf_box: dict = {}
    pools = pool_spec(scenario, centres, index, ipf_box)
    ipf = ipf_box or None
    ipf_stats: dict = {"balances": 0, "failures": 0, "clipped": {}, "worst": {},
                       "headroom": dict(ipf_box.get("headroom") or {})}

    # Lineage belongs to the pool fit, not here. A splinter inherits its
    # parent's pool vector, an entrant takes an even share of every pool, and
    # both are overridable per target in judgements/. See `pools.emit_pools`.
    # The rule can therefore act on a party that did not previously exist,
    # which the old branch could not (`if party not in index: continue`).

    handled = {p for cfg in scenario["pools"].values() for p in cfg["members"]
               if p in index}
    # NOTE: seeded parties are deliberately left INSIDE the pool draw. Moving
    # them to the individual path so their band applied made things far worse —
    # 39 arrivals each drawing a triangular with a high tail averaged ~32x their
    # seed and collectively ate the ballot, taking CRPS from 84 to 172 and the
    # DA from 89 seats to 47. The band is per-party but the constraint that
    # matters is on arrivals AS A GROUP: historically they take about 20% of a
    # metro between them. Until that total is drawn and split, a per-party band
    # is not safe to apply.
    # A party in the baseline that reached no pool would fall to the residual
    # bucket and be drawn against a range meant for minor parties — which is
    # what happened to MK, 12.2% of the 2024 base, at mode 1.30 against a
    # theta_mode of 0.60. pools.emit_pools gives every baseline party a vector,
    # so this should be empty; say so loudly if it is not.
    orphans = {p: base_city_d.get(p, 0.0) for p in index
               if p not in handled and p != "ENTRANT"
               and base_city_d.get(p, 0.0) >= 0.01}
    if orphans:
        listed = ", ".join(f"{p} {s:.1%}" for p, s in
                           sorted(orphans.items(), key=lambda kv: -kv[1]))
        print(f"  ! in no pool, drawn from the residual range: {listed}. "
              f"Re-emit pools, or declare lineage in judgements/.")
    # How wide each party's level is, in log units, straight off the measured
    # size-dispersion line. This is the connection the external review found
    # missing: levels.py has been measuring sd(log θ) — 0.26 at 40% of the vote
    # rising to 0.72 at 0.1% — and the draw was ignoring it, taking its spread
    # instead from the 10th and 90th percentiles of that same lognormal squeezed
    # back into a bounded triangular. The measurement now reaches the draw
    # directly, and unbounded (see LEVEL_DF).
    sd_measured = (scenario.get("_theta_sd") or {})
    sd_default = float(scenario.get("level_sd_default", DEFAULTS["level_sd_default"]))

    def sd_for_party(party: str) -> float:
        return float(sd_measured.get(party, sd_default))

    individual = []
    for party, i in index.items():
        if party in handled or party == "ENTRANT":
            continue
        # Same two paths as blended_centres, in the same order: a seeded
        # arrival is drawn against the arrival record's band, never against a
        # retention prior it has no history to have earned.
        seed_band = (scenario.get("pool_seed_bands") or {}).get(party) \
            if (scenario.get("pool_seeds") or {}).get(party, 0.0) > 0 else None
        if seed_band is not None:
            # An arrival's band IS the estimate, so it keeps its triangular:
            # the arrival record is a set of observed entry sizes, not a
            # dispersion around a centre, and widening it with a t-tail would
            # be inventing evidence the record does not contain.
            low, _, high = seed_band
            mode = min(max(centres[party] / max(base_city[i], 1e-9), low), high)
            individual.append((i, (low, mode, high), None))
            continue
        # The CENTRE is the spine's, and it is no longer clamped into the θ
        # band. That clamp existed when the centre and the band came from the
        # same θ; now they do not, and it was silently undoing task #22 — it
        # would have pulled ActionSA's 15.2% blended level back to about 11%
        # because the ratio it implies against a 6.2% national base sits above
        # the top of a band measured on parties that have a θ at all.
        individual.append((i, None, (centres[party], sd_for_party(party))))

    entrant_index = index.get("ENTRANT")

    # ARRIVALS AS A GROUP — BUILT, MEASURED, AND NOT ADOPTED.
    #
    # The design is the external review's item 4 and it is well motivated: the
    # single generic slot gives a median seat to ONE of the thirty-two arrivals
    # that won one (src/arrivals.py), and it cannot do better, because reality
    # delivers 11 to 32 arrivals per metro and the slot holds one. The group
    # TOTAL is the quantity that behaves regularly — 0.31% to 19.99% over
    # sixteen metro-years — and ward reach predicts the split (corr +0.393 on
    # log vote, against +0.145 for metros contested and -0.09 for geographic
    # concentration). Seat-winning arrivals have a median ward reach of 99%
    # against 33% for the rest.
    #
    # It scores WORSE, and by a lot:
    #
    #   Johannesburg 2021   CRPS 85.9 -> 109.9   seat MAE 113 -> 134
    #   Johannesburg 2016   CRPS 45.0 ->  45.7   seat MAE  61 ->  62
    #
    # WHY, and it is not a bug. At target 2021 the group total may only be fitted
    # on 2016, whose metro-years run 0.31%-4.74% with a median of 1.57%. 2021
    # came in at 19.99%. No honest draw from that record reaches it — the model's
    # 90% band is 0.41%-5.93% — so the mechanism correctly forecasts what the
    # record says and the record was superseded. Meanwhile the slot it replaces
    # was scoring well for a reason that is not skill: it is relabelled onto the
    # LARGEST arrival, so a single lump of mass lands on exactly the right party
    # after the fact.
    #
    # So this is off by default. It is kept, with its measurement, because the
    # reasoning survives its own result: by 2026 the record includes 2021 and
    # the group total centres near 7% instead of 1.6%. Retry it then, against a
    # target whose prior cycle is not a regime change.
    # DEFAULT OFF. Measured on Johannesburg and rejected -- see the note below
    # and MODEL-LOG. The spec is still emitted and the draw still implemented,
    # because the measurement is worth keeping and the mechanism should be
    # retried when the group total has more than one prior cycle behind it.
    group = (scenario.get("arrival_group") or None) \
        if scenario.get("arrival_group_draw") else None
    group_idx, group_w, group_alpha = None, None, None
    if group and group.get("weights"):
        members = [p for p in group["weights"] if p in index]
        if members:
            group_idx = np.array([index[p] for p in members])
            w = np.array([float(group["weights"][p]) for p in members])
            group_w = w / w.sum()
            group_alpha = float(group.get("alpha", 4.0)) * _dirichlet_scale(scenario)
            group_ln = (float(group["total_log_median"]),
                        float(group["total_log_sd"]))

    # Pools sharing a `tie` draw ONE shock between them, apportioned by base.
    # This matters more than it looks. South Africa's African electorate is not
    # one pool -- Zulu, Xhosa, Sotho, Pedi, Tswana, Tsonga, Venda, Ndebele and
    # Swati are distinct, and the ANC's long decline is partly the Zulu share
    # leaving it. We should carry all of them in the structure. But declaring
    # nine pools and drawing them independently would make the model *more*
    # confident, not less: nine independent shocks aggregate to a third of the
    # variance of one. Tying them shares a single shock, so a group behaves as
    # one pool in aggregate while remaining separately addressable the moment
    # census language data lets us untie it. English and Afrikaans are tied for
    # the same reason -- VF+ and the DA share ground (+0.61 Johannesburg, +0.86
    # Tshwane), so nothing yet justifies letting them move apart.
    ties: defaultdict[str, list[str]] = defaultdict(list)
    for name in (pools or {}):
        ties[scenario["pools"][name].get("tie") or name].append(name)

    # Each pooled party's own level spread, looked up once rather than per draw.
    # A seeded arrival is excluded (its band, not a dispersion, is the estimate)
    # by giving it zero: its size comes from the arrival record and the pool
    # split, and a t-shock on top would double-count the uncertainty the band
    # already carries.
    seeded_set = {p for p, s in (scenario.get("pool_seeds") or {}).items() if s > 0}
    pool_sd_shock = {p: (0.0 if p in seeded_set else sd_for_party(p))
                     for cfg in scenario["pools"].values() for p in cfg["members"]}

    rho_t = float(scenario.get("turnout_correlation", TURNOUT_CORRELATION))
    # The ONLY job of this floor is to keep every Dirichlet concentration
    # strictly positive, which numpy requires. It was 0.05, which is not a
    # numerical guard but a claim — and a large one.
    #
    # A Dirichlet's mean share is alpha_i / Σalpha, so raising a small party's
    # alpha to 0.05 raises its expected vote to whatever 0.05 is worth against
    # the pool's total concentration. Measured on Johannesburg 2021 with the
    # real levels in place, 44 of the Black African pool's 52 members were
    # floored, and their collective share went from the 1.59% the model believed
    # to 8.41% — a 6.82pp transfer, taken proportionally from every other member
    # of that pool. Across the four pools it is of the order of 5pp of the
    # citywide vote handed to parties the model itself puts near zero.
    #
    # That is the missing half of the mid-ballot squeeze. Over nine city-years
    # ranks 13+ came out +18.65pp and ranks 4-12 -56.36pp, and this floor is
    # where the tail's share was manufactured.
    mean_floor = float(scenario.get("dirichlet_floor", DIRICHLET_FLOOR))
    # DELIVERY PROOF. The EFFECTIVE values, after the scenario has had its say:
    # a sweep that sets `montecarlo.DIRICHLET_FLOOR` while a city TOML sets
    # `dirichlet_floor` is overridden here and would otherwise report a null it
    # never earned. `LEVEL_DF` is recorded because `log_shock(df=None)`
    # resolves it AT CALL TIME out of this same module namespace, once per
    # draw, and nothing rebinds it mid-run -- so the value here is the value
    # every draw below will use, and recording it per draw would buy nothing.
    note_value(scenario, "turnout_correlation", rho_t,
               where="montecarlo:make_drawer")
    note_value(scenario, "dirichlet_floor", mean_floor,
               where="montecarlo:make_drawer")
    note_value(scenario, "montecarlo.LEVEL_DF", LEVEL_DF,
               where="montecarlo:make_drawer -> log_shock(df=None)")

    def draw_pools():
        """One draw. Each pool's VOTES are its counted registration times a
        drawn turnout; the pool's share of the city follows from the votes,
        and its members split it. Turnout is the only quantity here that is
        not counted, which is the whole point: it is the assumption, and it is
        the correlated shock 2021 delivered when every pool fell at once.

        That last sentence was aspirational until now. Every pool drew its own
        independent turnout, so the citywide total came out half as variable as
        a single pool when the record says 0.82 as variable (see
        TURNOUT_CORRELATION). The pools are now tied together by a common
        factor, which is the review's "single correlated citywide turnout
        shock" — implemented as a copula so that each pool keeps EXACTLY the
        marginal turnout band ``pools.turnout_band`` measured for it, and only
        the dependence between them changes.
        """
        target = np.zeros(n)
        totals = {}
        # One standard normal for the whole city, per draw. Every pool's
        # turnout is pushed by it in proportion to sqrt(rho).
        z_common = rng.standard_normal()
        for group, names in ties.items():
            if len(names) == 1:
                name = names[0]
                # registration (counted) x turnout (drawn) = votes
                totals[name] = pools[name][1] * correlated_triangular(
                    rng, pools[name][2], z_common, rho_t)
                continue
            # one shock for the group, shared out in proportion to base, so the
            # group's total moves exactly as a single pool of that size would
            # one RATIO for the group: every tied pool moves by the same
            # factor, so the group behaves exactly as a single pool of its
            # combined size whatever the split between its members.
            lo = sum(pools[nm][2][0] for nm in names) / len(names)
            md = sum(pools[nm][2][1] for nm in names) / len(names)
            hi = sum(pools[nm][2][2] for nm in names) / len(names)
            shock = correlated_triangular(rng, (lo, md, hi), z_common, rho_t)
            for nm in names:
                totals[nm] = pools[nm][1] * shock
        # Shares follow from votes, so the pool side sums to one by
        # construction rather than by a later division.
        cast = sum(totals.values())
        # THE LEVEL SHOCK MOVES TO THE CENTRES, BEFORE THE BALANCE.
        #
        # Applying it inside the pool and renormalising there cancels it for a
        # dominant member — the normaliser falls with the party — so the top
        # three drew a realised sd(log) of 0.078 against the 0.26 levels.py
        # measures for their size band. Binding the centres by IPF fixed the
        # CENTRE and left that dispersion untouched, which made the model
        # accurate and overconfident rather than inaccurate and overconfident.
        #
        # Shocking the centres and re-balancing means the whole shock survives:
        # the IPF forces each party's expected citywide share onto its SHOCKED
        # centre, so a draw in which the ANC is 8% lower is a draw in which the
        # ANC really is 8% lower. It costs 0.15 ms a draw.
        pool_props = {name: p[3] for name, p in pools.items()}
        if ipf is not None and ipf["parties"]:
            base_c = np.array([max(centres.get(q, 0.0), 1e-12)
                               for q in ipf["parties"]])
            share = base_c / base_c.sum()
            # NO COMPOSITIONAL INFLATION. One was added when the top parties
            # were realising a third of their measured spread, on the theory
            # that normalising a share vector eats a large party's own move.
            # The real cause was that every party was being handed the SAME t
            # draw (see log_shock), and with genuinely independent shocks the
            # normaliser is an average over many parties and barely moves — so
            # the correction became a 1.4x over-shoot. Measured both ways.
            sds = np.array([pool_sd_shock.get(q, 0.0) for q in ipf["parties"]])
            shocked = base_c * log_shock(rng, sds)
            if shocked.sum() > 0:
                shocked = shocked / shocked.sum()
                # THE SHOCK CAN ASK FOR MORE THAN THE POOLS HOLD, and until
                # 2026-08-17 that was the end of the mechanism for the whole
                # draw. `balance_margins` raised, the bare `except: pass` below
                # kept the UNSHOCKED props, and the level shock was discarded
                # for EVERY party in that draw — not just the offender — in
                # 42.7% of the live 2026 forecast's draws and 12.7% of Nelson
                # Mandela Bay 2021's. It fired preferentially on the draws where
                # the shock was largest, which is the worst possible selection.
                # No backtest could see it: across the nine city-years the rate
                # was 1.4%, and forcing it to zero left the output identical.
                #
                # The column targets are now water-filled under each party's own
                # pool capacity BEFORE the balance, which is feasible by
                # construction. Note that a plain clip would not survive:
                # `balance_margins` rescales the column margin back up to the
                # row total on entry. See `capped_targets`.
                col_target = capped_targets(
                    shocked * ipf["pool_votes"].sum(), ipf["cap_votes"])
                if ipf_stats is not None:
                    ipf_stats["balances"] += 1
                    for j, q in enumerate(ipf["parties"]):
                        capj = float(ipf["cap_votes"][j])
                        askj = float(shocked[j] * ipf["pool_votes"].sum())
                        if capj > 0 and askj > capj * (1.0 + 1e-9):
                            ipf_stats["clipped"][q] = \
                                ipf_stats["clipped"].get(q, 0) + 1
                            ipf_stats["worst"][q] = max(
                                ipf_stats["worst"].get(q, 0.0), askj / capj)
                        elif capj <= 0 and askj > 0:
                            ipf_stats["clipped"][q] = \
                                ipf_stats["clipped"].get(q, 0) + 1
                            ipf_stats["worst"][q] = float("inf")
                try:
                    Rd = _balance(ipf["R0"], ipf["pool_votes"], col_target)
                except Exception as exc:            # noqa: BLE001 — counted
                    # NEVER SILENT, AND NEVER `pass`. The old branch kept the
                    # UNSHOCKED proportions, which threw the level shock away
                    # for every party in the draw. It now falls back to the same
                    # partial balance `pool_spec` uses one stage earlier — every
                    # pool exactly allocated, the party levels as close as the
                    # arithmetic permits — so the shock is degraded rather than
                    # deleted. `run_model` carries the count onto `ModelRun` and
                    # `main` prints it, the same way `bounds_violations` is.
                    if ipf_stats is not None:
                        ipf_stats["failures"] += 1
                        ipf_stats.setdefault("first_error", str(exc))
                    Rd = partial_balance(ipf["R0"], ipf["pool_votes"], col_target)
                for gi, nm in enumerate(ipf["names"]):
                    if nm not in pools:
                        continue
                    members = pools[nm][5]
                    v = np.array([Rd[gi, ipf["pidx"][q]] if q in ipf["pidx"]
                                  else 0.0 for q in members])
                    if v.sum() > 0:
                        pool_props[nm] = v / v.sum()
        for name, (idx, reg, spec, props, alpha, names, levels, wts) in pools.items():
            props = pool_props.get(name, props)
            # A PARTY'S OWN LEVEL MOVES, not just its pool's total and its
            # share of the split. Before this, a pooled party had no level
            # uncertainty of its own at all: the pool's turnout moved every
            # member together and the Dirichlet redistributed between them, so
            # the measured sd(log θ) — the one quantity in the model that says
            # how wrong a party's level can be — never entered the draw for any
            # party large enough to be in a pool. That is the under-dispersion
            # the review called structural, and this is where it lived.
            # The shock has already been applied to the centres above and
            # balanced through, so it must NOT be applied again here.
            moved = props
            # FLOOR THE MEAN, NOT THE CONCENTRATION. A Dirichlet's component
            # mean is alpha_i / Σalpha, so clipping alpha_i injects mass no
            # centre asked for -- a conservation violation rather than a tuning
            # knob. It was doing so at both settings tried: 0.05 manufactured
            # about 5pp of citywide vote for parties the model puts near zero,
            # and 1e-4 left components with concentration far below one, which
            # is a spike at zero with a rare large chunk (PAC in Buffalo City
            # read median 0.001% against mean 0.250%, a ratio of 416).
            #
            # Flooring the MEAN and normalising afterwards makes E[X] exactly
            # the vector asked for, and alpha_i = mean_i x alpha is then
            # strictly positive without any clip. A party whose share is small
            # enough that its concentration is still under one keeps its spike
            # at zero -- which is an honest statement that it may win nothing --
            # but it no longer gets mass it was never given.
            moved = np.maximum(moved, mean_floor)
            moved = moved / moved.sum()
            split = rng.dirichlet(moved * alpha)
            np.add.at(target, idx, (totals[name] / cast if cast > 0 else 0.0) * split)
        for i, tri, level in individual:
            if tri is not None:
                target[i] = base_city[i] * triangular(rng, tri)
            else:
                centre, sd = level
                target[i] = centre * log_shock(rng, sd)
        total = target.sum()
        if total > 0:
            target = target / total
        if group_idx is not None:
            # One lognormal draw for what all arrivals take between them, then a
            # reach-weighted Dirichlet for who takes it. The concentration is
            # measured (median 4.85 across sixteen metro-years) and is what lets
            # a single party take most of the group, as ActionSA took 91% of
            # Johannesburg's in 2021.
            total = float(np.exp(rng.normal(group_ln[0], group_ln[1])))
            total = min(total, 0.45)          # arithmetic guard, never binding
            # group_alpha is the TOTAL concentration, not per-component: the
            # method of moments in pools.arrival_group_record solves
            # A = m(1-m)/var - 1 with m = 1/n, and A is nα. Multiplying by n
            # again forced an even split and buried the big arrival, which is
            # the opposite of what the record shows — the largest arrival took
            # 91% of the group in Johannesburg 2021 (A = 0.22).
            # `mean_floor`, not `dirichlet_floor`. This line read the latter
            # until 2026-08-20 and there is no such name in scope — the branch
            # raised `NameError` the first time anything reached it, which was
            # the first time anything COULD. See the `arrival_group_draw`
            # comment in DEFAULTS. MODEL-LOG §1.63.
            split = rng.dirichlet(np.maximum(group_w * group_alpha,
                                             mean_floor))
            target[group_idx] = 0.0
            s_all = target.sum()
            if s_all > 0:
                target *= (1.0 - total) / s_all
            target[group_idx] = total * split
        elif entrant_index is not None:
            share = (triangular(rng, scenario["entrant_share"])
                     if rng.random() < scenario["entrant_prob"] else 0.0)
            target *= (1.0 - share)
            target[entrant_index] = share
        return target

    draw_pools.ipf_stats = ipf_stats
    return draw_pools


# --------------------------------------------------------------------------
# seats with overhang (E3)
# --------------------------------------------------------------------------

# THE ONLY STRINGS `allocate_with_overhang` ACCEPTS, and the source the
# docstring's list is derived from rather than re-typed (§1.97 F39, F43).
#
# `level` MUST be in here. It is implemented, it is exercised by
# `src/overhang_regimes.py`, and it appears on the forecast sheet's regime
# table — but until 2026-08-28 the docstring listed only deduct/expand/cap and
# mentioned `level` in an inline comment. A whitelist derived from what the
# docstring documented would have raised on a rule the model actually runs,
# which is why these two are one change and not two.
OVERHANG_RULES = ("deduct", "expand", "cap", "level")

# Iteration bounds for the two `while` loops below. NEITHER HAD ONE (§1.97 F41,
# F44), so a termination defect wedged `tests/run_all.py` as a hang rather than
# a failure — and a hang in a suite that takes forty minutes reads as slowness.
#
# `deduct` fixes at least one party per round and never un-fixes, so it cannot
# run longer than there are parties; +2 is slack for the final no-op round.
#
# `level` is bounded on ROUNDS, not on council size, and the first attempt at
# this got it wrong in a way worth recording: a bound of 4x COUNCIL was taken
# from the largest council a real regime run has produced (396 against a 270
# base) and it fired immediately on a 15-seat test fixture, where covering a
# party holding 4 of 7 wards on 2.6% of the vote legitimately needs ~150 seats.
# **A magnitude read off the real panel does not transfer to a toy** — the same
# error as §1.105, in reverse. Rounds carry no such assumption: each round adds
# at least one seat and a converging case takes a handful.
OVERHANG_DEDUCT_MAX_ROUNDS_SLACK = 2
OVERHANG_LEVEL_MAX_ROUNDS = 200


def allocate_with_overhang(
    combined: dict[str, int], ward_wins: dict[str, int], rule: str = "deduct"
) -> tuple[dict[str, int], int, int, dict[str, int]]:
    """Schedule 1 allocation with the excessive-seats treatment.

    ``rule`` must be one of :data:`OVERHANG_RULES` — ``deduct``, ``expand``,
    ``cap``, ``level`` — and anything else raises. It used to fall through to
    ``expand`` in silence, so ``--set overhang_rule=dedcut`` ran the legacy
    counterfactual, grew the council and moved the majority threshold without a
    word (§1.97 F39). Nothing upstream catches it either: ``parse_set``
    validates that a KEY exists in ``DEFAULTS`` and never looks at the value.

    **The signature default is ``deduct`` since 2026-08-28** (§1.97 F40). It was
    ``expand`` — disagreeing with this docstring, with ``DEFAULTS`` and with the
    statute, so a two-argument call written from the prose got the legacy
    counterfactual. Both production call sites pass ``rule`` explicitly, which
    is what made the change number-neutral and is asserted below.

    A party keeps every ward it wins. Default rule "deduct" is the amended
    Act 3/2021 Schedule 1 item 16(1),(3)-(9), as the IEC applied it in
    Laingsburg 2021 (MODEL-LOG 1.17): a party whose wins are *equal to or
    greater than* its entitlement keeps its wards and gets no list seats;
    the quota is recomputed for everyone else over the remaining seats, and
    the council stays at 270. The equality trigger follows 16(1)'s "equal to
    or greater" wording (MODEL-LOG 1.19) — excluding an exactly-at-quota
    party is not a no-op for the others. "expand" (council grows by the
    excess) is kept as the legacy pre-research toggle; "cap" ignores wins.

    Returns (seats, council_size, threshold, excessive_by_party) — the dict
    maps each party that triggered item 16 (in any re-allocation round) to
    its excess at the round it was fixed (0 for an exactly-equal party).
    """
    if rule not in OVERHANG_RULES:
        raise ValueError(
            f"unknown overhang_rule {rule!r}; expected one of "
            f"{', '.join(OVERHANG_RULES)}.\n"
            f"\n"
            f"  This used to fall through to `expand` in SILENCE, which grows "
            f"the council and moves the majority threshold — so a typo did not "
            f"fail, it quietly ran a different law. `parse_set` cannot catch it "
            f"either: it validates that a KEY exists in DEFAULTS and never "
            f"looks at the value. MODEL-LOG §1.97 F39.")
    # A WARD WINNER THAT IS NOT IN `combined` CANNOT BE SEATED (§1.97 F42). It
    # would be counted excessive here and then never appear in any allocation,
    # so its seats vanish and the council silently fails to add up. No input in
    # the archive reaches this; it is a guard against the input that would.
    ghosts = sorted(p for p, w in ward_wins.items() if w > 0 and p not in combined)
    if ghosts:
        raise ValueError(
            f"ward winner(s) absent from the combined-ballot tally: {ghosts}.\n"
            f"\n"
            f"  A party that wins a ward but has no combined-ballot votes would "
            f"be counted excessive and then seated nowhere. `combined` is "
            f"`pr_votes + ward_votes`, so this means the two ballots disagree "
            f"about who stood. MODEL-LOG §1.97 F42.")
    alloc = allocate(combined, total_seats=COUNCIL)
    over = {p: ward_wins[p] - alloc.seats.get(p, 0)
            for p in ward_wins
            if ward_wins[p] > 0 and ward_wins[p] >= alloc.seats.get(p, 0)}
    seats = dict(alloc.seats)
    if rule == "cap" or not over:
        return seats, COUNCIL, COUNCIL // 2 + 1, over
    if rule == "level":
        # modern-Germany counterfactual (Ausgleichsmandate): grow the council
        # until every ward winner's seats are covered by its proportional
        # share — nobody is squeezed, the chamber pays instead
        total = COUNCIL
        for _round in range(OVERHANG_LEVEL_MAX_ROUNDS):
            try:
                sub = allocate(combined, total_seats=total)
            except ValueError as exc:
                # THE RULE NAMES ITSELF. `allocate` fails when the council has
                # grown large against the vote total, and its message names the
                # allocator — so the report pointed at the arithmetic instead of
                # at the rule that demanded the council. That misdirection is
                # the complaint in §1.97 F41 and it is what this re-raise fixes;
                # the allocator's own words are kept because they say what
                # actually broke.
                raise RuntimeError(
                    f"the `level` rule grew the council from {COUNCIL} to "
                    f"{total} seats covering ward winners, and the allocation "
                    f"then failed: {exc}\n"
                    f"\n"
                    f"  `level` grows the chamber by the current deficit each "
                    f"round (Ausgleichsmandate). A party holding many wards on "
                    f"a small vote share demands a council far larger than the "
                    f"votes can fill, and largest-remainder gives out before it "
                    f"gets there. This is a property of the INPUT under this "
                    f"rule, not a defect in `allocate`. MODEL-LOG §1.97 F41."
                ) from exc
            deficit = sum(max(0, w - sub.seats.get(p, 0))
                          for p, w in ward_wins.items())
            if deficit == 0:
                return dict(sub.seats), total, total // 2 + 1, over
            total += deficit
        raise RuntimeError(
            f"the `level` rule did not converge in "
            f"{OVERHANG_LEVEL_MAX_ROUNDS} rounds; the council reached {total} "
            f"from a base of {COUNCIL} and a ward winner is still short.\n"
            f"\n"
            f"  Each round adds at least one seat and a converging case takes a "
            f"handful, so this means the deficit is not closing — `allocate` is "
            f"not monotone in `total_seats`, or a ward winner is absent from "
            f"`combined`, which the guard at the top of this function refuses. "
            f"Before this bound existed the loop simply never returned, and a "
            f"hang in a forty-minute suite reads as slowness rather than as a "
            f"failure. MODEL-LOG §1.97 F41, F44.")
    if rule == "deduct":
        fixed: dict[str, int] = {}
        votes = dict(combined)
        # At least one party is fixed and removed per round, so the loop cannot
        # outlast the parties; the slack covers the final round that fixes none.
        for _round in range(len(combined) + OVERHANG_DEDUCT_MAX_ROUNDS_SLACK):
            sub = allocate(votes, total_seats=COUNCIL - sum(fixed.values()))
            newly = {p: ward_wins[p] for p in list(votes)
                     if ward_wins.get(p, 0) > 0
                     and ward_wins.get(p, 0) >= sub.seats.get(p, 0)}
            if not newly:
                return {**sub.seats, **fixed}, COUNCIL, COUNCIL // 2 + 1, over
            for party, wins in newly.items():
                over.setdefault(party, wins - sub.seats.get(party, 0))
                fixed[party] = wins
                votes.pop(party)
        raise RuntimeError(
            f"the `deduct` rule did not settle in {len(combined) + 2} rounds "
            f"over {len(combined)} parties.\n"
            f"\n"
            f"  Each round fixes at least one party and removes it from the "
            f"pool, so this is unreachable unless a party is being re-fixed — "
            f"which would mean `votes.pop` is not removing it. Before this "
            f"bound existed the loop simply never returned. "
            f"MODEL-LOG §1.97 F41, F44.")
    for party, excess in over.items():
        seats[party] = seats.get(party, 0) + excess
    council = COUNCIL + sum(over.values())
    return seats, council, council // 2 + 1, over


# --------------------------------------------------------------------------
# the trace
# --------------------------------------------------------------------------

def _jsonable(obj):
    """numpy scalars and arrays are not JSON; everything here might be either."""
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (set, frozenset)):
        return sorted(obj, key=str)
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, date):
        return obj.isoformat()
    return str(obj)


class Trace:
    """Writes each stage's output to a run directory, so it can be READ.

    THE PROBLEM THIS SOLVES. Every intermediate in ``run_model`` lives as one of
    **228 locals inside a 1,099-line function** (was 223 in 863 when this class
    was written on 2026-08-18 — it grew 27% in a week), so the only way to see
    one has been to add a print and re-run the whole comparison.
 That cost is paid on every investigation, and it is why several
    findings this month were argued from a single expensive reading rather than
    checked cheaply against a second.

    INERT BY DEFAULT. With no ``run_dir`` every method returns its argument
    untouched and writes nothing, so a run that does not ask for a trace is
    byte-identical to one from before this existed. That is asserted by
    ``tests/test_chain.py::test_the_trace_is_inert_without_a_run_directory``.

    ``put`` RETURNS WHAT IT IS GIVEN, which is the point: a stage can be
    recorded by wrapping the expression that produces it, without moving code
    or introducing a branch::

        centres = trace.put("centres", blended_centres(...))

    NOT A MANIFEST, AND NOT A SUBSTITUTE FOR A GATE. This records what happened;
    it does not check it. The pool ceiling that went blind would appear here as
    74 of 75 parties at exactly 1.0 and nobody would have looked. What catches
    that is an assertion, and the value of this class is that it makes such
    assertions cheap to write because the quantity is already exposed. See
    ARCHITECTURE.md, "Order of work".
    """

    def __init__(self, run_dir: Path | str | None = None, detail: bool = False):
        self.dir = Path(run_dir) if run_dir else None
        self.detail = detail
        self.written: list[str] = []
        if self.dir is not None:
            self.dir.mkdir(parents=True, exist_ok=True)

    def __bool__(self) -> bool:
        return self.dir is not None

    def put(self, name: str, obj, detail: bool = False):
        """Record ``obj`` under ``name`` and return it unchanged.

        ``detail=True`` marks a per-draw quantity — large, and useful only when
        chasing something specific — which is written only when the trace was
        opened with ``detail``. Per-draw arrays over 1500 draws are tens of
        megabytes and would make tracing too expensive to leave on.
        """
        if self.dir is None or (detail and not self.detail):
            return obj
        path = self.dir / f"{name}.json"
        try:
            with path.open("w") as handle:
                json.dump(obj, handle, indent=1, default=_jsonable,
                          sort_keys=True)
            self.written.append(name)
        except (TypeError, ValueError, OSError) as exc:
            # A trace that raises would turn a diagnostic into an outage, and
            # this runs inside the forecast. Record the failure and continue.
            with path.open("w") as handle:
                json.dump({"__unserialisable__": repr(exc)}, handle)
            self.written.append(f"{name} (FAILED: {exc})")
        return obj

    def close(self, **summary) -> None:
        if self.dir is None:
            return
        self.put("_index", {"written": sorted(self.written), **summary})


# --------------------------------------------------------------------------
# the model
# --------------------------------------------------------------------------

@dataclass
class ModelRun:
    """Everything one set of draws produced, and nothing derived from it.

    ``main`` reports and writes from this; ``backtest`` scores from it.

    Ward winners are kept as ``ward_winner_counts`` — a (wards × parties)
    tally — and *not* per draw. A ``(draws, wards)`` int16 array of per-draw
    winners lived here until 2026-08-10, justified as "the highest-power
    calibration evidence available"; nothing ever read it. Every consumer
    (``ward_probabilities`` here, the Brier score and the reliability table in
    ``score.py``, the published ``ward_winner_probs.csv``) is marginal, one
    ward at a time, and marginals come out of the counts. So the array was
    allocated and filled on every run — 5000 × 135 on the published 2026 one —
    to be thrown away. It is deleted rather than kept against a future need,
    because a claim this repository cannot point at a consumer for is a claim
    it does not get to make. A joint scorer (a variogram over the ward vector,
    a correlated-error test) would need the per-draw array back; restore it
    *with* that scorer, in the same change.
    """

    target: object
    scenario: dict
    universe: list[str]
    index: dict[str, int]
    wards: list[str]
    seat_draws: list[dict[str, int]] = field(default_factory=list)
    thresholds: np.ndarray | None = None
    council_sizes: np.ndarray | None = None
    ward_winner_counts: np.ndarray | None = None  # (wards, parties)
    ward_win_sum: dict[str, int] = field(default_factory=dict)
    overhang_count: dict[str, int] = field(default_factory=dict)
    excessive_draws: int = 0
    bounds_violations: dict[str, int] = field(default_factory=dict)
    bounds_checked: int = 0
    # The per-draw IPF that binds the SHOCKED centres, and what it cost.
    # ``ipf_balances`` counts the attempts, ``ipf_failures`` the draws that fell
    # back to the unshocked pool proportions — which discards the level shock
    # for every party in that draw, so a non-zero count is a report that the
    # model's central mechanism did not run. ``ipf_clipped`` maps each party
    # held at its pool capacity to the number of draws it was held, and
    # ``ipf_worst`` to the largest fraction of that capacity it asked for.
    # ``ipf_headroom`` is the pre-draw ratio — a party near 1.0 is one shock
    # away from being clipped, which is what nobody could see before.
    ipf_balances: int = 0
    ipf_failures: int = 0
    # `capped_targets`' counters, snapshotted per run. See the note beside
    # their definition: they are module-level and would otherwise accumulate
    # across the nine city-years of one `compare_history` invocation.
    cap_undershoots: int = 0
    cap_moved: float = 0.0
    ipf_clipped: dict[str, int] = field(default_factory=dict)
    ipf_worst: dict[str, float] = field(default_factory=dict)
    ipf_headroom: dict[str, float] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)
    gamma_source: dict[str, str] = field(default_factory=dict)
    ratio: np.ndarray | None = None
    n_vd: int = 0
    # Citywide shares per draw, (draws, parties), one array per ballot. The
    # model has always computed these -- they are what the seats are allocated
    # from -- and always thrown them away, so every comparison against a real
    # election could talk about seats and not about VOTES. Seats are a step
    # function of votes through a quota, so a forecast can be several seats out
    # while being a tenth of a point out on the ballot, or the reverse, and
    # reporting only the seat error hides which of those is happening.
    pr_share_draws: np.ndarray | None = None
    ward_share_draws: np.ndarray | None = None

    @property
    def draws(self) -> int:
        return len(self.seat_draws)

    @property
    def constants_read(self) -> dict[str, list[str]]:
        """Hand-typed constants this run consumed, and what consumed them.

        Filled by :func:`note_constant`. ``backtest.in_sample_banner`` reports
        it, so the in-sample verdict is a measurement of the run rather than a
        statement about ``DEFAULTS``.
        """
        return dict(self.scenario.get("_constants_read") or {})

    @property
    def delivered(self) -> dict[str, dict]:
        """The value-bearing read log: what this run consulted, AT WHAT VALUE.

        Filled by :func:`note_value`, :func:`note_module_constants` and
        :func:`note_constant`. :func:`assert_delivered` is what a sweep should
        read it with; the raw dict is here so a diagnostic can report the sites
        and the read counts. See the delivery-proof block above ``note_constant``
        for why a read log without values cannot tell UNDELIVERED from INERT.
        """
        return dict(self.scenario.get("_delivered") or {})

    def ward_probabilities(self) -> dict[str, dict[str, float]]:
        """``{ward: {party: P(win)}}`` — the shape ``score.score_wards`` takes."""
        out: dict[str, dict[str, float]] = {}
        for i, w in enumerate(self.wards):
            counts = self.ward_winner_counts[i]
            out[w] = {self.universe[j]: float(counts[j]) / self.draws
                      for j in np.nonzero(counts)[0]}
        return out


def run_model(target, scenario: dict,
              data_dir: Path = Path("data/raw/elections"),
              processed: Path | None = None,
              verbose: bool = True,
              run_dir: Path | str | None = None,
              trace_detail: bool = False) -> ModelRun:
    """Run the forecast for one target election.

    **Writes nothing unless ``run_dir`` is given**, and then it writes only a
    trace: each stage's output as JSON, so an intermediate can be read instead
    of re-derived by adding a print and running again. The trace never feeds
    back into the forecast — with ``run_dir`` unset the run is byte-identical
    to one from before tracing existed, which a test asserts. See :class:`Trace`.

    Every input is resolved from ``target``: the baseline is the NPE preceding
    it, the ward/PR split ratios and the local by-election geography come from
    the LGE preceding it, γ from a fold that finished before it, turnout from
    ``turnout.py`` run for this same target, and the council is the one that
    city had in that year. Nothing here opens the target's own votes; the ward
    layer and the roll are read from its result file only when no delimitation
    crosswalk exists (see :func:`ward_parts`), and both are public months
    ahead.

    Two inputs a past target simply does not have, stated because their absence
    is silent rather than loud:

    * **By-elections.** ``byelection_*.csv`` is scraped for the window since the
      last LGE (2022-2026 as this is written), so for a past target the files
      are not in its processed directory, ``bye`` stays empty and ``w_bye`` and
      the local ward terms have nothing to act on. The code path is the same
      one; the evidence does not exist.
    * **Split voting districts.** See :func:`ward_parts`.
    """

    _reset_cap_counters()
    # A LOCAL, deliberately, not a module global. Module-level mutable state is
    # what makes this file unsafe to run city-years through concurrently, and
    # adding more of it would work against exactly the parallelism the trace is
    # meant to enable.
    trace = Trace(run_dir, detail=trace_detail)
    global COUNCIL
    COUNCIL = target.council
    processed = target.processed if processed is None else processed
    trace.put("00_target", {
        # `target.city` is the whole City object and repr()s to 4kB of config;
        # the slug is the identifying thing and the config is already on disk.
        "city": getattr(getattr(target, "city", None), "slug", None),
        "year": getattr(target, "year", None),
        "council": target.council,
        "draws": scenario.get("draws"),
        "seed": scenario.get("seed"),
    })
    trace.put("01_scenario_in", {k: v for k, v in scenario.items()
                                 if not k.startswith("_")})

    # --- pools: the parties' measured constituencies -------------------------
    # A pool is a body of voters, measured from the census, and a party's
    # membership of it is the share of its vote that demonstrably comes from
    # there. Emitted by `python src/pools.py --emit`. There is no alternative
    # engine, so a missing spec is an error rather than a quiet substitution.
    if not scenario.get("pools"):
        spec_path = target.city.processed / f"pools_{target.year}.json"
        if spec_path.exists():
            spec = json.loads(spec_path.read_text())
            # IS THIS SPEC STILL THE ONE THIS CODE WOULD PRODUCE? The artefact
            # is precomputed, so `pools.py` can change without it changing, and
            # a measurement taken across that gap is not a measurement. This
            # has already cost twice; see `pools.artefact_key`.
            try:
                import pools as _pools_key
                _stale = _pools_key.stale_reason(spec, target.city, target)
            except Exception:                       # never fail a run over this
                _stale = None
            if _stale:
                print(f"  ! pools_{target.year}.json is STALE: {_stale}")
            scenario["_pools_stale"] = _stale
            scenario["_pools_artefact_key"] = spec.get("artefact_key")
            trace.put("02_pools_artefact", {
                "path": str(spec_path),
                "artefact_key": spec.get("artefact_key"),
                "stale_reason": _stale,
                "fitted_on": spec.get("fitted_on"),
            })
            # `artefact_key` is the DELIVERY PROOF for the precomputed-artefact
            # class: city, target, a hash of config/dimensions.toml and a hash
            # of pools.py's code. A run that reports "pools were read" says
            # nothing about WHICH pools; this says which, and a sweep over
            # `config/dimensions.toml` that does not move this key never
            # arrived. See CLAUDE.md, "Shared artefacts".
            note_constant(scenario, "pools", f"fitted on {spec['fitted_on']}",
                          value=spec.get("artefact_key"),
                          where=f"montecarlo:run_model <- {spec_path.name}")
            home = spec.get("splinter_home")
            if home:
                note_constant(scenario, "splinter_home",
                              f"{', '.join(sorted(home['fractions']))} "
                              f"measured at {', '.join(home['measured_at'])}")
            scenario["pools"] = spec["pools"]
            scenario["pool_seeds"] = spec.get("seeds", {})
            scenario["pool_seed_bands"] = spec.get("seed_bands", {})
            scenario["pool_seed_notes"] = spec.get("seed_notes", {})
            scenario["arrival_group"] = spec.get("arrival_group")
            try:
                import pools as _pools
                _cfg = _pools.load_config()
                _counts = _pools.pool_counts(target.city, spec["fitted_on"], _cfg)
                _comp = _counts.composition("voted")
                _by_ward = {w: dict(zip(_counts.categories, _comp[i]))
                            for i, w in enumerate(_counts.wards)}
                _ward_of, _ = _pools.vd_map(target.city, spec["fitted_on"])
                scenario["_vd_pool_composition"] = {
                    vd: _by_ward[w] for vd, w in _ward_of.items() if w in _by_ward}
            except Exception as exc:            # geography is a bonus, not a gate
                if verbose:
                    print(f"  ! no VD pool composition ({exc}); seeded parties "
                          f"will have a citywide level but no geography")
            if verbose:
                print(f"  pools: {len(spec['pools'])} measured from "
                      f"{spec['fitted_on']} ({spec['provenance']})")
                unidentified = [n for n, c in spec["pools"].items()
                                if not c.get("identified")]
                if unidentified:
                    print(f"  ! pools with no member weight identified by ward "
                          f"data: {', '.join(unidentified)} — these are "
                          f"judgements, not measurements")
        else:
            raise SystemExit(
                f"no pool spec at {spec_path}. The model has no other engine. "
                f"Run:\n  python src/pools.py --city {target.city.slug} "
                f"--target {target.year} --emit")

    rng = np.random.default_rng(scenario["seed"])

    # --- baseline: the last national election before the target --------------
    base_votes, _ = load(data_dir / target.results(target.previous_npe), None)
    base_share_d, base_city_d = shares(base_votes), citywide(base_votes)

    # A PARTY THAT IS NOT ON THE BALLOT CANNOT TAKE VOTES, and it is removed
    # HERE — before θ, ρ, the spine, the pool fit or the seeds have seen it —
    # rather than having its votes reapportioned afterwards. A party that is not
    # standing never had the votes to reapportion.
    #
    # The universe used to be built from the national baseline alone, so every
    # party that contested the last NATIONAL election kept a share at the local
    # one whether or not it stood. Johannesburg 2021: 13 parties in the 2019
    # baseline were not on the 2021 ballot, holding 0.42% of it between them.
    # About 0.4% of the vote is a seat under largest remainder, so that is of
    # the order of one invented seat, and it is funded out of the parties ranked
    # 4th to 12th — the ones that win marginal seats and that this model
    # under-predicts almost everywhere.
    #
    # (0.42% is the honest figure. A larger number quoted during review, ~2.5%,
    # was mostly the generic ENTRANT slot, which is a different thing: at a past
    # target where a party really did arrive, ENTRANT IS the forecast for it and
    # `backtest.relabel_entrant` maps it across. Do not conflate the two.)
    #
    # Removing them redistributes nothing by hand: the pools renormalise when
    # drawn, so whatever a pool holds is split between the parties actually
    # drawing on it.
    #
    # Reading the roster from the target's result file is legitimate and is the
    # same justification `levels.contestation` already runs on: nomination lists
    # close and are published weeks before polling day, so WHO IS ON THE BALLOT
    # is available to a forecaster. Their votes are not, and none are read here.
    # A target not yet held has no roster and is left alone.
    try:
        import pools as _pools
        _roster = _pools.contesting_parties(target.city, target.year)
    except Exception:
        _roster = set()
    if _roster:
        _absent = sorted(p for p in base_city_d
                         if p not in _roster and p not in (INDEPENDENT, "IND")
                         and base_city_d.get(p, 0.0) > 0)
        if _absent:
            _held = sum(base_city_d[p] for p in _absent)
            for p in _absent:
                base_city_d.pop(p, None)
            for _vd in base_share_d.values():
                for p in _absent:
                    _vd.pop(p, None)
            if verbose:
                print(f"  not on the {target.year} ballot: dropped {len(_absent)} "
                      f"parties holding {_held:.2%} of the "
                      f"{target.previous_npe} baseline "
                      f"({', '.join(_absent[:5])}"
                      f"{', …' if len(_absent) > 5 else ''})")


    # A party with no baseline cannot be grown into existence: theta multiplies,
    # and anything times zero is zero. ActionSA held 0.0000% of the 2019
    # national vote and won 44 of Johannesburg's 270 seats in 2021; the model
    # scored it at zero, and those seats reappeared as ANC +17 and DA +20.
    # pools.default_seeds gives every such party a starting share — a splinter
    # takes half its parent's vote, an entrant the median arrival on record,
    # both capped at the largest entry ever observed — and debits the parent
    # where there is one, because those votes moved rather than appeared.
    # Levels are measured from transitions strictly before the target, which
    # is what takes theta_mode, individual_theta, f_other and PLAN_BOUNDS out
    # of the in-sample list. f_other in particular had every minor party
    # growing 30% into a local election; the record says they retain 0.79.
    try:
        import levels as _levels
        _prior, _groups = _levels.theta_prior(target, base_city_d)
        if _prior:
            # `__small__` WAS HERE, AND IT WAS A HAND-TYPED 0.8 (MODEL-LOG §1.98).
            #
            # The line read `_groups.get("small", {})` and then `.get("median",
            # 0.8)`. `theta_prior` has three returns: two empty dicts that fail
            # the `if _prior:` gate above, and one literal whose keys are exactly
            # {centre, spread, worth, sd}. **"small" could never be a key**, and
            # `git log -S'"small"' -- src/levels.py` returns no commits, so the
            # typed 0.8 won every time the line ran — and it reached the
            # published artefact: forecast_summary.json carried
            # `scenario.theta_prior.__small__ == [0.28695681, 0.8, 2.23030077]`,
            # which is exactly 0.8·exp(∓1.2816·0.8).
            #
            # `__small__` was not read either. Its consumer was montecarlo.py:629
            # at 49193a5 and task #22 (48e173d) deleted it, so this wrote a
            # hand-typed retention prior into the artefact of a model whose whole
            # point (49193a5) is that the hand-typed priors are gone.
            #
            # DELETED RATHER THAN REPAIRED. Adding a `small` group to
            # `levels.theta_prior` would restore a mechanism that was removed
            # deliberately, and that is a scored change, not a bug fix.
            scenario["theta_prior"] = _prior
            # The measured log-spread per party, carried to the draw. See
            # make_drawer: this is the number the draw was not using.
            scenario["_theta_sd"] = _groups.get("sd", {})
            # `scenario["_theta_worth"]` was written here and READ BY NOTHING —
            # one occurrence in the whole tree, this line (§1.97 F45). Deleted
            # 2026-08-28. It is `__small__`'s twin (F20, deleted in §1.99): 52
            # parties wide at 2026 and published in `forecast_summary.json`,
            # where a reader would reasonably take it for something the model
            # uses. `_theta_sd` directly above IS read — at `make_drawer` and in
            # the guards — which is exactly why the dead one beside it was
            # invisible.
            # The width layer, exposed. `SD_FLOOR` binds on two or three
            # parties holding most of the ballot and FLATTENS them to one
            # number; that is visible here without instrumenting anything.
            # MODEL-LOG §1.45.
            trace.put("10_theta_prior", {
                "prior": _prior,
                "sd": _groups.get("sd", {}),
                "worth": _groups.get("worth", {}),
                "centre": _groups.get("centre"),
                "spread": _groups.get("spread"),
                "sd_floor": _levels.SD_FLOOR,
                "sd_ceiling": _levels.SD_CEILING,
                "at_the_floor": sorted(
                    p for p, v in (_groups.get("sd") or {}).items()
                    if abs(v - _levels.SD_FLOOR) < 1e-12),
            })
            if verbose:
                centre, spread = _groups["centre"], _groups["spread"]
                print(f"  levels: {centre['n']} transitions before "
                      f"{target.year}, common centre "
                      f"{centre['weighted_geomean']:.2f}; "
                      f"sd(log θ) {spread['at_40%']:.2f} at 40% of the vote "
                      f"rising to {spread['at_0.1%']:.2f} at 0.1%")
        # `scenario["_ward_pr_measured"] = _ratios` was written here and READ
        # BY NOTHING — zero loads in all of `src/` (§1.109 F26). DELETED
        # 2026-08-28. The third of its kind after `__small__` (§1.98) and
        # `_theta_worth` (F45): written to the scenario, carried into
        # `forecast_summary.json` where a reader would take it for something
        # the model uses, and consumed nowhere. Only the median — the second
        # element — ever crossed this seam.
        #
        # DELETED RATHER THAN WIRED THROUGH, and that is the measured part.
        # `run_model` recomputes the same ratios inline below from the same
        # file, and the two are BIT-IDENTICAL where the consumer trusts them:
        # 496 party-ratios above the 0.1% PR floor across all 32 (city, target)
        # pairs, worst absolute difference exactly 0.0. What they do NOT agree
        # on is WHO GETS A RATIO. `levels` drops a party with no ward votes;
        # the inline copy keeps it at 0.0 and clips to WARD_PR_RATIO_MIN. AGANG
        # at Tshwane 2026 is exactly that party — 761 PR votes, 0.113% of the
        # ballot, no ward row at all — and consuming this map would move it
        # from 0.5 to the fallback 0.855. One moved party is a SCORED change,
        # not a tidy-up, so the duplication STAYS and the dead write goes.
        _ratios, _fallback = _levels.ward_pr_ratios(target, target.city)
        if _ratios:
            scenario["_ward_pr_fallback"] = _fallback
        # CONTESTATION IS A CHANGE, NOT A LEVEL. See where it is applied.
        # `_contestation` is who stands at the TARGET; `_contestation_prev` is
        # who stood at the election the ward/PR ratio was measured from, which
        # is `target.previous_lge` — the same one `ward_pr_ratios` reads.
        _contest = _levels.contestation(target, target.city)
        _prev_lge = target.previous_lge
        _contest_prev = {}
        if _prev_lge:
            _contest_prev = _levels.contestation(
                cityconfig.use_target(_prev_lge), target.city)
            cityconfig.use_target(target.year)   # restore the active target
        # NO TARGET LISTS -> PROJECT THEM, and say so. `contestation` reads who
        # stood from the target's own result file, which exists for every
        # backtest and for no live forecast, so this branch is the 2026 case and
        # only the 2026 case. Until 2026-08-20 it left the correction as the
        # identity — an assumption that every party fields exactly last time's
        # slate, made by omission rather than by anyone. `contestation_expand`
        # replaces it with a measured projection, and REAL LISTS SUPERSEDE IT:
        # the moment `contestation` returns anything for the target, this does
        # not run and the lever is inert.
        _projected = False
        if not _contest and _contest_prev:
            _contest = _levels.projected_contestation(
                _contest_prev,
                # NOT a fresh literal: `0.0` here was the identity while
                # DEFAULTS declares 0.220, so if the key were ever absent
                # this path would silently apply no expansion while the
                # message printed below reported 0.220. Found by
                # test_every_literal_fallback_equals_the_declared_default,
                # on the run that introduced it. MODEL-LOG §1.85.
                scenario.get("contestation_expand",
                             DEFAULTS["contestation_expand"]))
            _projected = bool(_contest)
        if _contest:
            scenario["_contestation"] = _contest
        if _contest_prev:
            scenario["_contestation_prev"] = _contest_prev
        if _contest and _contest_prev:
            note_constant(scenario, "contestation",
                          f"{target.year} against {_prev_lge}, "
                          f"{len(_contest)} parties"
                          + (f", PROJECTED at contestation_expand="
                             f"{scenario.get('contestation_expand')}"
                             if _projected else ", from published lists"))
            if verbose:
                vals = sorted(_contest.values())
                print(f"  contestation: {len(_contest)} parties, median "
                      f"{vals[len(vals) // 2]:.0%} of wards"
                      + (f" — PROJECTED from {_prev_lge} at "
                         f"contestation_expand="
                         f"{scenario.get('contestation_expand')}; no "
                         f"nomination lists published for {target.year}"
                         if _projected else " — from published lists"))
    except FileNotFoundError as _exc:
        # Missing data is a legitimate reason to fall back; a bug is not. This
        # used to be a bare `except Exception`, and a stale key in the progress
        # line above was being swallowed by it — so the run reported falling
        # back to the hand-typed constants while actually using the measured
        # ones, or the reverse, depending only on whether verbose was set.
        print(f"  ! level priors unavailable ({_exc}); falling back to the "
              f"hand-typed constants, WHICH SAW THE TARGET")

    # The baseline AS THE ELECTION LEFT IT, before any seed is added. "Has a
    # record" has to mean the party took votes at the preceding national
    # election, not that this model handed it a starting share five lines ago —
    # and the seed loop below mutates base_city_d in place, so ActionSA looked
    # like an established party to every later test.
    baseline_before_seeds = dict(base_city_d)
    scenario["_baseline_before_seeds"] = baseline_before_seeds

    seeds = scenario.get("pool_seeds") or {}
    if seeds:
        notes_by_party = scenario.get("pool_seed_notes") or {}
        for party, seed in seeds.items():
            base_city_d[party] = max(base_city_d.get(party, 0.0) + seed, 0.0)

        # A citywide level is not enough. The voting-district solve places a
        # party by its deviation from its own baseline, so a party with no
        # baseline has no geography and stays at zero in every district however
        # large its citywide seed — which is why ActionSA was still scoring
        # nothing after being seeded. Its pool vector is exactly the missing
        # information: put it where its pools live. This is the one place the
        # pools do work the old baseline-deviation model cannot do at all.
        members_by_party: dict[str, dict[str, float]] = defaultdict(dict)
        for pool_name, cfg in scenario["pools"].items():
            for party, weight in cfg["members"].items():
                members_by_party[party][pool_name] = float(weight)
        vd_pool = scenario.get("_vd_pool_composition") or {}
        if vd_pool:
            for party in seeds:
                weights = members_by_party.get(party)
                if not weights or base_city_d.get(party, 0.0) <= 0:
                    continue
                for vd, comp in vd_pool.items():
                    place = sum(weights.get(name, 0.0) * comp.get(name, 0.0)
                                for name in comp)
                    if place > 0:
                        base_share_d.setdefault(vd, {})[party] = max(
                            place * base_city_d[party], SHARE_FLOOR)
        # The band is what the record says an arrival can be worth, and it is
        # wide because arrivals genuinely are. Carrying it as this party's own
        # theta range is what stops a seeded party being pinned to its seed.
        # A DEAD STORE, REMOVED 2026-08-19. This wrote each seeded arrival's
        # band into `individual_theta`, and nothing read it back:
        # `blended_centres` and `make_drawer` both take `pool_seed_bands`
        # directly and short-circuit before any membership test. Confirmed
        # three ways in §1.41 -- multiplying every written band by 100,
        # setting the whole dict to [50,80,99], and deleting all 32 keys, all
        # byte-identical. The key it wrote into no longer exists.
        if verbose:
            for party in sorted(seeds, key=lambda p: -abs(seeds[p]))[:8]:
                why = notes_by_party.get(party, "parent debited")
                print(f"  seed {party:<12} {seeds[party]:+.2%}  {why}")
    universe = sorted(p for p in base_city_d if p != INDEPENDENT and p != "IND")
    if scenario["entrant_prob"] > 0:
        universe.append("ENTRANT")
    index = {party: i for i, party in enumerate(universe)}
    vds = sorted(base_share_d)
    nvd, npar = len(vds), len(universe)

    base_city = np.array([base_city_d.get(p, SHARE_FLOOR) for p in universe])
    local = np.array([[base_share_d[v].get(p, 0.0) for p in universe] for v in vds])
    if "ENTRANT" in index:
        local[:, index["ENTRANT"]] = SHARE_FLOOR  # flat unless given a map below
    dev = logit(local) - logit(base_city)[None, :]
    # DELIVERY PROOF for two classes at once. `SHARE_FLOOR` is a module
    # constant (not in DEFAULTS, never swept for liveness, does not cross a
    # process boundary), and `logit(p, floor=None)` resolves that SAME constant
    # as a FUNCTION DEFAULT -- the shape that made `LEVEL_DF` sweepable in
    # appearance and frozen in fact (§1.33). Recorded here because `logit` has
    # no scenario and runs per draw; the value is the module's, read live.
    note_value(scenario, "montecarlo.SHARE_FLOOR", SHARE_FLOOR,
               where="montecarlo:run_model baseline fill, logit(floor=None)")

    # --- where does a new party's vote sit? (§1.27) --------------------------
    # Prediction is expit(level + γ·dev), so a party's geography *is* its dev
    # column. An entrant has no baseline, so dev is zero and it lands evenly
    # across the city. Measured against the six entrants on record that is
    # right for exactly one of them: fitting
    #     entrant_index(i) = (1-k)·parent_index(i) + k
    # gives k = 0.03 for MK on the ANC and 0.05 for the EFF on the ANC -- they
    # inherit the parent's map almost exactly -- against k = 1.00 for ActionSA
    # on the DA, which ignored it completely. Scaling the parent's dev by
    # (1-k) reproduces that interpolation directly in logit space, and k = 1
    # returns the flat default unchanged.
    ent = scenario.get("entrant_geography") or {}
    if "ENTRANT" in index and ent.get("parent"):
        parent = ent["parent"]
        if parent not in index:
            raise SystemExit(f"entrant_geography parent {parent!r} is not in the "
                             f"baseline, so it has no map to inherit")
        k = float(ent.get("k", 1.0))
        note_constant(scenario, "entrant_geography", parent)
        dev[:, index["ENTRANT"]] = (1.0 - k) * dev[:, index[parent]]
        if verbose:
            print(f"entrant geography: {parent}'s map at k={k} "
                  f"({'flat' if k >= 1 else 'inherited' if k <= 0 else 'partial'})")

    # --- by-elections move the ward they happened in (§1.28) -----------------
    # E4 turns each contest into a *citywide* per-party delta and applies it to
    # the party's citywide centre, so a by-election in ward 82 moves ward 82's
    # forecast exactly as much as it moves ward 1's. The ward identity is used
    # to compute the delta and then discarded. That is right for estimating a
    # citywide level and wrong for the 135 separate first-past-the-post races,
    # where a recent result in *this* ward is the strongest local evidence
    # available: the model currently says DA 64% in a ward the PA won in April
    # 2025 and ANC 94% in one the PA won that October.
    #
    # The local term shifts that ward's own voting districts by the logit
    # movement the contest actually showed,
    #     shift(p) = w · decay · [logit(share_bye) − logit(share_2021)]
    # damped by w, decayed by the same τ the citywide term uses, and clamped.
    # Three deliberate choices, all reversible via the scenario:
    #   * ρ (how typical the ward is of the city) is NOT applied. ρ exists to
    #     judge whether a contest generalises citywide; using a ward's own
    #     result on itself needs no such discount.
    #   * The shift is applied to the contest's VOTING DISTRICTS, not its ward.
    #     By-elections sit on the PREVIOUS LGE's ward boundaries and the
    #     forecast on the target's; voting districts carry across both, so this
    #     sidesteps re-delimitation entirely.
    #   * Ward and PR get separate weights, because a by-election is a ward
    #     contest. Its evidence about list voting in the same ward is real but
    #     weaker, and it says nothing about list voting anywhere else.
    # Note the containment limit: shares are renormalised within each VD, and
    # the citywide total is pinned by calibration, so lifting a party here
    # shaves a vanishing amount off it elsewhere. That is a property of a model
    # that fixes citywide totals, not a leak in this term.
    dev_pr, dev_ward = dev, dev
    w_ward = scenario.get("w_bye_local_ward", DEFAULTS["w_bye_local_ward"])
    w_pr = scenario.get("w_bye_local_pr", DEFAULTS["w_bye_local_pr"])
    if (w_ward or w_pr) and (processed / "byelection_contest_detail.csv").exists():
        # By-election wards are on the previous LGE's delimitation, so the
        # ward -> VD map comes from that election's result file rather than
        # from the target's ward crosswalk.
        ward_of_vd: dict[str, str] = {}
        with cityconfig.resolve_path(
                data_dir / target.results(target.previous_lge)
        ).open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                ward_of_vd.setdefault(row["VD_Number"], row["Ward"].strip())
        vd_of_ward: defaultdict[str, list[int]] = defaultdict(list)
        for i, vd in enumerate(vds):
            ward = ward_of_vd.get(vd)
            if ward:
                vd_of_ward[ward].append(i)
        cap = scenario.get("bye_local_cap", DEFAULTS["bye_local_cap"])
        tau = scenario.get("bye_tau_months", DEFAULTS["bye_tau_months"])
        # A ward that has voted twice has shown one ward twice over, not two
        # separate movements to be stacked. Ward 102 went to the polls in 2023
        # and again in 2026 and the DA landed within a point of itself both
        # times; adding the two shifts claimed half again the movement either
        # contest on its own supports. So each (VD, party) accumulates a
        # recency-weighted numerator and its weight and divides at the end --
        # the same mean the citywide term takes in byelections.py -- which
        # averages repeat contests towards the most recent instead of
        # compounding them. One contest divides by its own weight, so the
        # single-contest case is exactly the formula stated above.
        moved_num = np.zeros_like(dev)
        moved_weight = np.zeros_like(dev)
        applied = 0
        with (processed / "byelection_contest_detail.csv").open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                party, ward = row["party"], row["ward"]
                if party not in index or ward not in vd_of_ward:
                    continue
                before, after = float(row["share_2021"]), float(row["share_bye"])
                if before <= 0 or after <= 0:
                    continue          # a party arriving from nothing is a level
                age = months_before_election(row["date"], target.date)
                decay = np.exp(-age / tau)
                move = np.clip(np.log(after / (1 - after)) - np.log(before / (1 - before)),
                               -cap, cap) * decay
                moved_num[vd_of_ward[ward], index[party]] += decay * move
                moved_weight[vd_of_ward[ward], index[party]] += decay
                applied += 1
        shift = np.divide(moved_num, moved_weight, out=np.zeros_like(moved_num),
                          where=moved_weight > 0)
        if applied:
            dev_ward = dev + w_ward * shift
            dev_pr = dev + w_pr * shift
            moved = int((shift != 0).any(axis=1).sum())
            if verbose:
                print(f"by-election local term: {applied} party-contests applied "
                      f"to {moved} voting districts (ward w={w_ward}, PR "
                      f"w={w_pr}, cap {cap} logit, τ {tau}m)")

    # --- γ: the fold, then the previous LGE→NPE fit, then 1.0 (A4) -----------
    # Fold parameters are a CITY-level artefact -- fold 3 is the 2009→2011
    # transition whichever election is being built -- so they are read from the
    # city's processed root, where fold.py writes them, not from the target's
    # own directory. Everything else here (turnout, γ_recent, by-elections, the
    # ward crosswalk) is per-target and comes from `processed`. For Johannesburg
    # 2026 the two are the same directory, which is why this looks redundant.
    fold = gamma_fold_for(target)
    params = load_parameters(
        cityconfig.active().processed / f"fold{fold}_parameters.csv")
    recent: dict[str, float] = {}
    recent_path = processed / "gamma_recent.csv"
    if recent_path.exists():
        with recent_path.open(encoding="utf-8", newline="") as fh:
            recent = {r["party"]: float(r["gamma"]) for r in csv.DictReader(fh)}
    recent_label = f"{target.previous_lge}→{target.previous_npe}"
    gamma = {}
    gamma_source = {}
    for ballot in ("PR", "Ward"):
        values = np.ones(npar)
        for p, i in index.items():
            if p in params[ballot]["gamma"]:
                values[i] = params[ballot]["gamma"][p]
                gamma_source[p] = f"fold{fold}"
            elif p in recent:
                values[i] = recent[p]
                gamma_source.setdefault(p, recent_label)
            else:
                gamma_source.setdefault(p, "default 1.0")
        gamma[ballot] = values

    # --- ward parts and registration ----------------------------------------
    # F15: the crosswalk lives at CITY level — `build_concordance` is
    # city-scoped and has no target — while `processed` here is the TARGET's
    # directory. Seven cities' crosswalks sat on disk where nothing looked.
    # See `cityconfig.Target.crosswalk`. §1.120
    part_rows, parts_source = ward_parts(target, data_dir,
                                         target.crosswalk.parent)
    registered: defaultdict[str, int] = defaultdict(int)
    for vd, _ward, part_registered in part_rows:
        registered[vd] += part_registered

    # --- turnout patterns (A2) ----------------------------------------------
    # The "on record" anchors for the turnout tilts read the elections from
    # 2011 on, which is what the published 2026 forecast does. That floor is
    # kept rather than widened to the whole archive: it is where the current
    # registration record and VD footprint settle down. A target early enough
    # to have nothing at or after 2011 uses everything it does have, because
    # an empty anchor is a division by zero, not a conservative choice.
    prior_years = [y for y in target.before if y >= "2011"] or list(target.before)
    hi_years = prior_years
    lge_years = [y for y in prior_years if cityconfig.CALENDAR[y].kind == "LGE"]
    projected_col = f"turnout_{target.year}_projected"
    level_col = f"turnout_{target.previous_lge}"

    ratio_pattern: dict[str, float] = {}
    level_pattern: dict[str, float] = {}
    thi_pattern: dict[str, float] = {}
    tlo_pattern: dict[str, float] = {}
    turnout_path = processed / "turnout.csv"
    if not turnout_path.exists():
        raise SystemExit(
            f"{turnout_path} is missing: build it with "
            f"`python src/turnout.py --city {cityconfig.active().slug} "
            f"--target {target.year}`")
    with turnout_path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            vd = row["VD_Number"]
            if row[projected_col]:
                ratio_pattern[vd] = float(row[projected_col])
            if row.get(level_col) and row[level_col] != "nan":
                level_pattern[vd] = min(float(row[level_col]), 1.0)
            hi = [row.get(f"turnout_{y}") for y in hi_years]
            hi_vals = [float(x) for x in hi if x and x != "nan"]
            if hi_vals:
                thi_pattern[vd] = min(max(hi_vals), 1.0)
            lge = [row.get(f"turnout_{y}") for y in lge_years]
            vals = [float(x) for x in lge if x and x != "nan"]
            if vals:
                tlo_pattern[vd] = min(min(vals), 1.0)

    reg = np.array([registered.get(v, 0) for v in vds], dtype=float)
    t_ratio = np.array([ratio_pattern.get(v, np.nan) for v in vds])
    t_level = np.array([level_pattern.get(v, np.nan) for v in vds])
    mean_ratio = np.nansum(t_ratio * reg) / np.nansum(np.where(np.isnan(t_ratio), 0, reg))
    t_ratio = np.where(np.isnan(t_ratio), mean_ratio, t_ratio)
    mean_level = np.nansum(t_level * reg) / np.nansum(np.where(np.isnan(t_level), 0, reg))
    # Rescale the previous-LGE-level pattern to the λ̂ citywide level: the level
    # comes from λ̂ either way (MODEL-LOG 1.2); only the *pattern* differs.
    t_level = np.where(np.isnan(t_level), mean_level, t_level) * (mean_ratio / mean_level)
    # DELIVERY PROOF for an artefact that reaches the model WITH NO KEY AT ALL.
    # Nothing declares `turnout.csv`, nothing sweeps it, and it carries no
    # artefact key: a stale or rebuilt copy moves every draw in silence. The
    # citywide levels it delivered are recorded so a run can be asked WHICH
    # turnout file it was given, not merely whether one existed.
    note_value(scenario, "artefact:turnout.csv",
               {"vds": len(ratio_pattern),
                "mean_ratio": float(mean_ratio), "mean_level": float(mean_level),
                "projected_col": projected_col, "level_col": level_col},
               where="montecarlo:run_model")

    # who-turns-out anchors per VD (highest turnout on record; worst LGE
    # turnout on record), for the turnout_tilt_* dials
    t_hi = np.array([thi_pattern.get(v, np.nan) for v in vds])
    mhi = np.nansum(t_hi * reg) / np.nansum(np.where(np.isnan(t_hi), 0, reg))
    t_hi = np.where(np.isnan(t_hi), mhi, t_hi)
    t_lo = np.array([tlo_pattern.get(v, np.nan) for v in vds])
    mlo = np.nansum(t_lo * reg) / np.nansum(np.where(np.isnan(t_lo), 0, reg))
    t_lo = np.where(np.isnan(t_lo), mlo, t_lo)

    # --- ward structure (E3) -------------------------------------------------
    # A ward is only forecastable if at least one of its VD parts is in the
    # baseline NPE (``vd_index``) *and* carries registered voters: the ward
    # tally is built from those parts alone. A ward with none of them keeps an
    # all-zero row in ``ward_tally``, and ``argmax`` on all-zero returns index
    # 0 — so the alphabetically-first party in ``universe`` would "win" it with
    # p = 1.00 in every draw, feeding both the ward Brier score and the seat
    # allocation with a winner nothing measured. Excluding it loses that ward's
    # seat from the draw's ward wins, which is the honest cost: the model has
    # no evidence about who holds it, and inventing a certainty is worse than
    # admitting a gap. Johannesburg 2011/2016/2021/2026 lose none.
    vd_index = {v: i for i, v in enumerate(vds)}
    all_wards = sorted({ward for _vd, ward, _reg in part_rows}, key=int)
    usable = [(vd, w, r) for vd, w, r in part_rows if vd in vd_index and r > 0]
    wards = sorted({w for _vd, w, _r in usable}, key=int)
    dropped = [w for w in all_wards if w not in set(wards)]
    if dropped:
        print(f"  !! {len(dropped)} ward(s) have no voting district in the "
              f"{target.previous_npe} baseline with registered voters and are "
              f"EXCLUDED from the forecast: {', '.join(dropped)}. They win no "
              f"ward seat in any draw and appear in no ward probability; "
              f"{len(wards)} of {len(all_wards)} wards are forecast.")
    ward_index = {w: i for i, w in enumerate(wards)}
    part_vd = np.array([vd_index[vd] for vd, _w, _r in usable])
    part_ward = np.array([ward_index[w] for _vd, w, _r in usable])
    part_reg = np.array([r for _vd, _w, r in usable], dtype=float)

    # --- ward/PR split-ticket ratios (A1) ------------------------------------
    prior_lge_file = data_dir / target.results(target.previous_lge)
    prior_ward, _ = load(prior_lge_file, "Ward")
    prior_pr, _ = load(prior_lge_file, "PR")
    wc, pc = citywide(prior_ward), citywide(prior_pr)
    # F34 case (3): `blended_centres` cannot otherwise tell a party that DID
    # NOT STAND from one that stood on the WARD ballot only. At joburg 2021 the
    # second is real — IND at 1.290% of the ward ballot with no PR line, and
    # SAKHISIZWE_CONVENTION and AFRICAN_COVENANT beside it. For such a party
    # the PR base is UNKNOWN, not zero, and `0 + delta` is neither a level nor
    # a swing. Recorded here rather than recomputed there: one definition.
    scenario["_prior_ward_share"] = dict(wc)
    prior_pr_share = pc
    ratio = np.ones(npar)
    # THE SAME RATIOS, KEYED BY PARTY, for the by-election conversion (F46,
    # §1.113). Recorded in this loop rather than recomputed, because two
    # definitions of one quantity is the defect this repository has paid for
    # most often. Only the TRUSTED ones are carried: a party under the 0.001
    # threshold has a ratio that is a quotient of two noisy numbers, and
    # dividing a delta by it amplifies noise faster than it removes bias —
    # measured, and it is why `blended_centres` falls back to additive there.
    trusted_ward_pr: dict[str, float] = {}
    for p, i in index.items():
        if pc.get(p, 0) > 0.001:
            ratio[i] = np.clip(wc.get(p, 0.0) / pc[p],
                               WARD_PR_RATIO_MIN, WARD_PR_RATIO_MAX)
            trusted_ward_pr[p] = float(ratio[i])
    # A party with no ward history at the previous LGE gets the median of the
    # parties that have one — a rule that applies to whoever turns up next,
    # rather than the two hand-set numbers this replaces (MK 0.80 "bounded by
    # ActionSA's observed 0.77", ENTRANT 0.80), both of which were read off the
    # target.
    # Consumed by `blended_centres` for the by-election conversion. NOT the
    # fallback: an untrusted party keeps the additive treatment.
    scenario["_ward_pr_trusted"] = trusted_ward_pr
    note_value(scenario, "montecarlo.WARD_PR_RATIO_MIN", WARD_PR_RATIO_MIN,
               where="montecarlo:run_model ward/PR ratio clip")
    note_value(scenario, "montecarlo.WARD_PR_RATIO_MAX", WARD_PR_RATIO_MAX,
               where="montecarlo:run_model ward/PR ratio clip")
    fallback = scenario.get("_ward_pr_fallback")
    # `is not None`, NOT truthiness (§1.109 F27). A zero fallback is
    # REPRESENTABLE — 2 of the 753 measured ratios across the 32 (city, target)
    # pairs are exactly 0.0, so a median of zero is something this data can
    # produce — and `if fallback:` would discard it in silence, reverting every
    # party below the 0.1% floor (ENTRANT included) to `ratio = 1.0` from
    # `np.ones(npar)`: the identity wearing the fallback's name.
    #
    # NUMBER-NEUTRAL, and measured so: the fallback is a float in
    # [0.7533, 1.1227] at all 32 pairs and `None` at none of them, so both
    # spellings take the same branch everywhere the model can run. THIS IS THE
    # GUARD, INSTALLED BEFORE ANYTHING NEEDS IT. The change that would need it —
    # delivering the fallback unconditionally so the miss path stops landing on
    # 1.0 — is NOT made here: that path fires at none of the 32 pairs, so it is
    # unscoreable, therefore argued and not tested.
    if fallback is not None:
        for p, i in index.items():
            if pc.get(p, 0) <= 0.001:
                ratio[i] = fallback
    # `ward_pr_ratio_overrides` (MK 0.80, ENTRANT 0.80) lived here, gated on
    # `not fallback`. DELETED 2026-08-17: `run.constants_read` reports it
    # CONSUMED AT NO TARGET -- 2016, 2021 and 2026 alike -- because
    # `levels.ward_pr_ratios` returns a fallback at every one of them, which is
    # what the comment above already says it does. A judgement nobody could
    # reach, carried in DEFAULTS, in apply_city's per-city list, in two city
    # tomls, in backtest.FITTED_ON and in the register. MODEL-LOG 1.37.

    # Contestation, for every party rather than one.
    #
    # `pa_contestation_uplift` -- 1.25 applied to the PA alone, because it
    # fought 52 of 135 wards in 2021 while the model assumed all 135 -- was
    # DELETED on 2026-08-18. The observation behind it was sound and the remedy
    # was not: the median party contests well under half the wards, so the same
    # correction is owed to everyone, and it is measurable rather than chosen.
    # `levels.contestation`'s own docstring had said it "replaces
    # pa_contestation_uplift" for weeks while the constant went on firing,
    # because it fired in the `elif` for when the target's nomination lists do
    # not exist yet -- which is every live forecast, and no backtest. So the one
    # place it was live was the one place nothing could check it.
    #
    # It now falls back to the previous local election's measured shares (see
    # where `_contestation` is set), so there is no branch here that treats one
    # party differently from the rest.
    # AND IT IS APPLIED AS A CHANGE, NOT AS A LEVEL — corrected 2026-08-18.
    #
    # The multiplier used to be the target's contested share outright, and that
    # DOUBLE-COUNTED. `ward_pr_ratios` measures each party's ward-over-PR ratio
    # from the previous LGE's actual votes, and a party that stood in 38% of
    # wards banked ward votes in only those wards — so its measured ratio has
    # already been discounted by its contestation. Multiplying by the share
    # again applies the same discount twice.
    #
    # Measured: the correlation between the measured ratio and the contested
    # share is +0.699, parties contesting under 25% of wards average a ratio of
    # 0.512 against 1.075 for those above 75%, and dividing the ratio through by
    # contestation flips the correlation to -0.499 (over-correction). The
    # scoreboard says the same thing — at 2021 over four metros, applying the
    # level made ward MAE 10.79 against 8.90 with no adjustment at all.
    #
    # What the ratio does NOT know is how a party's slate has CHANGED since
    # then, so that is what is applied. It is 1.0 when the target's nomination
    # lists are not published — the live forecast's case — which is why 2026
    # correctly gets no adjustment rather than a constant for one party.
    contest = scenario.get("_contestation") or {}
    prev = scenario.get("_contestation_prev") or {}
    if contest and prev:
        for p, i in index.items():
            now, was = contest.get(p), prev.get(p)
            if now is not None and was:
                ratio[i] = float(np.clip(ratio[i] * (now / was), 0.0, 2.0))

    # --- by-election evidence (E4) -------------------------------------------
    bye: dict[str, tuple[float, float]] = {}
    bye_path = processed / "byelection_party_deltas.csv"
    if bye_path.exists():
        with bye_path.open(encoding="utf-8", newline="") as fh:
            _spread: dict[str, tuple[int, float]] = {}
            for row in csv.DictReader(fh):
                bye[row["party"]] = (float(row["weight_sum"]),
                                    float(row["weighted_delta"]))
                # THE SPREAD TRAVELS WITH THE MEAN. A note reporting only
                # "by-elections imply 10.6%" conceals that the reading is
                # eight contests spanning a factor of 31, with a 95% interval
                # three times wider than the clamp that bounds it. On the
                # scenario rather than in `bye` so the tuple shape every
                # consumer unpacks stays as it was.
                _spread[row["party"]] = (int(row.get("contests") or 0),
                                         float(row.get("delta_sd") or 0.0))
            scenario["_bye_spread"] = _spread
    # --- polls, for the parties nothing else can see (task #23) ------------
    # ONLY arrivals. An established party has a record and the spine uses it;
    # a poll is a competing estimate of the same quantity there and blending
    # the two is a policy question this does not answer. A party with NO
    # baseline has nothing else at all, and that is the case the model gets
    # wrong 31 times in 32 (src/arrivals.py).
    #
    # The number is a national poll share divided by the share of the national
    # vote sitting in the municipalities the party actually contests -- both
    # public before polling day. See src/polling.py for the arithmetic and what
    # it does and does not buy.
    import polling as _polling
    import pools as _pl
    # `validate_or_die` is deliberately OUTSIDE the try below. §1.68 made a
    # malformed register fatal because "a poll we meant to count and silently
    # did not is worse than a run that stops" — and it was then called from
    # inside a bare `except Exception`, which silently un-fatalled it on this
    # path. MODEL-LOG §1.69.
    _polling.validate_or_die()
    try:
        _min_n = float(scenario.get("poll_min_n", DEFAULTS["poll_min_n"]))
        _usable = (_polling.national_polls(target, min_n=_min_n)
                   if scenario.get("poll_paths",
                                   DEFAULTS["poll_paths"]) in ("arrivals", "all")
                   else [])
        if _usable:
            _votes = _polling.votes_by_metro(target.year)
            # `_rosters` was built here and never read — the loop below reads
            # `_roster`, a DIFFERENT name bound far above. It re-read a whole
            # VD result file to duplicate work already done, and its
            # `cityconfig.by_code` branch was permanently dead because that
            # function does not exist. Deleted 2026-08-22, MODEL-LOG §1.69;
            # number-neutral, because nothing consumed it.
            _poll = _usable[-1]
            for _party in (_poll.get("numbers") or {}):
                if baseline_before_seeds.get(_party, 0.0) > 0:
                    continue                      # has a record; the spine has it
                if _party not in (_roster or set()):
                    continue                      # not on this city's ballot
                # WHO STOOD, not who scored. `metro_citywide(...) > 0` reads
                # the result this backtest is predicting; row existence is the
                # nomination fact. See pools.metro_roster. MODEL-LOG §1.65.
                _stood = [c for c in _pl.METRO_CODES
                          if _party in _pl.metro_roster(c, target.year)]
                _est = _polling.metro_estimate(_poll, _party, _stood,
                                               target.year, _votes)
                if not _est:
                    continue
                scenario.setdefault("poll_levels", {})[_party] = _est["share"]
                note_constant(scenario, "poll_level",
                              f"{_party} from {_est['poll']}")
                if verbose:
                    print(f"  poll: {_party} -> {_est['share']:.2%}  ({_est['basis']})")
    except (FileNotFoundError, KeyError, ValueError) as _exc:
        # NARROWED 2026-08-22 (MODEL-LOG §1.69). This was `except Exception`,
        # wrapped around the arrivals poll path — the largest single measured
        # effect in the poll channel, 48 coherent seats (§1.65). A NameError or
        # an AttributeError in here would have disabled all 48 of them and
        # printed a verbose-only warning, which is precisely how the legacy
        # poll path stayed broken and unnoticed (§1.68). Missing data is
        # expected and is caught; a programming error is not, and now
        # propagates.
        if verbose:
            print(f"  ! polls unavailable ({type(_exc).__name__}: {_exc})")

    # --- the spine: both records, weighted by which one the party has (#22) ---
    # Computed here rather than beside theta_prior because it needs the previous
    # LOCAL election's citywide shares, which are read a few lines up. Both
    # inputs are strictly before the target.
    try:
        import levels as _levels
        # F1: `scenario.get("spine_k") or SPINE_K` — and `0.0 or 1.0` is 1.0,
        # so `spine_k=0` was UNDELIVERABLE and a sweep of it measured the
        # default at every value. `spine_k` ships as None, which is why the
        # idiom looked right; None is the only value it ever had to resolve.
        # Resolved on `is None` so zero is a value like any other.
        _spine_k = scenario.get("spine_k")
        _spine, _spine_info = _levels.spine(
            target, base_city_d, prior_pr_share,
            k=float(_levels.SPINE_K if _spine_k is None else _spine_k))
        # F4: THE WHOLE BLOCK USED TO BE GATED ON `if _spine:`, so a spine that
        # reached NOBODY wrote no `spine_level`, no `20_spine` trace and no
        # `note_constant` — and a run where the spine placed no party was
        # indistinguishable from one where this code never executed. The empty
        # case is exactly the one a reader needs the trace for.
        #
        # An empty `spine_level` behaves identically downstream (`party in {}`
        # is False for every party), so writing it unconditionally is
        # number-neutral and turns `blended_centres`' F37 record from "the
        # block did not run" into "it ran and placed nobody" — which are
        # different facts.
        scenario["spine_level"] = _spine
        scenario["_spine_info"] = _spine_info
        # Per party: which route it took, what each route said, and what
        # the blend weight was. This is the question the level chain gets
        # asked most often -- "why is this party at this number?" -- and it
        # has been answered by re-running with prints every time.
        trace.put("20_spine", {
            "level": _spine,
            "k": _spine_info.get("k"),
            "n_theta": _spine_info.get("n_theta"),
            "n_rho": _spine_info.get("n_rho"),
            "theta_centre": _spine_info.get("theta_centre"),
            "rho_centre": _spine_info.get("rho_centre"),
            "detail": _spine_info.get("detail"),
            # F5/F6: `levels.spine` builds a full absorption block — route
            # counts, the blend's disagreement accounting, centre
            # fallbacks, shrink totals, and now the NAMES of the parties it
            # dropped and of those whose level nothing can read. The trace
            # discarded all of it. "Written, never read" was true of the
            # producer and the reason was here.
            "absorption": _spine_info.get("absorption"),
        })
        # `spine_k` is the constant ARCHITECTURE.md records as UNSETTABLE
        # -- `scenario.get("spine_k") or SPINE_K`, and `0.0 or 1.0` is 1.0.
        # Recording the k the spine actually ran on is how a sweep of it
        # finds that out from the run instead of from a code reading.
        note_constant(scenario, "spine",
                      f"k={_spine_info['k']}, {_spine_info['n_theta']} θ and "
                      f"{_spine_info['n_rho']} ρ observations before "
                      f"{target.year}",
                      value=_spine_info.get("k"),
                      where="montecarlo:run_model -> levels.spine")
        if verbose:
            d = _spine_info["detail"]
            moved = sorted((p for p in d if base_city_d.get(p, 0) >= 0.005),
                           key=lambda p: -abs(d[p]["local"] - d[p]["national"]))
            print(f"  spine: {_spine_info['n_theta']} θ and "
                  f"{_spine_info['n_rho']} ρ observations before "
                  f"{target.year}; θ centre "
                  f"{_spine_info['theta_centre']:.2f}, ρ centre "
                  f"{_spine_info['rho_centre']:.2f}")
            for p in moved[:6]:
                print(f"    {p:<12} w_local {d[p]['w_local']:.2f} "
                      f"(θ worth {d[p]['worth']:.1f})  national "
                      f"{d[p]['national']:.2%} / local {d[p]['local']:.2%} "
                      f"-> {_spine[p]:.2%}")
    except FileNotFoundError as _exc:
        print(f"  ! spine unavailable ({_exc}); levels fall back to the "
              f"national route alone")

    centres, notes = blended_centres(scenario, base_city_d, prior_pr_share, bye,
                                     trace=trace)

    # --- metro polls, blended by PRECISION not by party history --------------
    # A poll of THIS city is a direct reading of the quantity being forecast, so
    # it applies to every party it names rather than only to arrivals. How much
    # it counts is inverse-variance (polling.blend_weight): the measured house
    # error is 3.0pp against model intervals that are far wider for a large
    # party, so an accurate metro poll is not thrown away because the party has
    # a long record — which a weight keyed on observation counts would do.
    #
    # SEVERAL POLLS ARE AGGREGATED FIRST, once, by recency. Applying them one
    # after another is not aggregation, it is the last one applied winning, and
    # the order was the register's — so Johannesburg 2026 was having its OLDEST
    # wave applied last and dominating.
    #
    # NO BARE EXCEPT. This block previously swallowed anything into a one-line
    # warning, and it swallowed a KeyError on 'house' for the whole of the 2026
    # forecast: the one channel with demonstrated skill silently did nothing in
    # the one case it was built for, and the warning scrolled past. A failure
    # here now says exactly what broke.
    import polling as _pg
    # A MALFORMED REGISTER STOPS THE RUN. Every admission rule below used to be
    # a silent `continue`, so a `scope` of "Metro" or a typo'd `city` dropped a
    # poll with no warning — and with one house behind the 2026 forecast, losing
    # one of its two waves that way would move a published number and print
    # nothing. Warnings (a house that never published its sample size) do not
    # raise. MODEL-LOG §1.68.
    _pg.validate_or_die()
    _screened, _declined = _pg.screen(
        target, min_n=float(scenario.get("poll_min_n", DEFAULTS["poll_min_n"])))
    # The city rule lives in `polling`, not here. See polling.metro_polls.
    _metro = ([q for q in _screened if q.get("scope") == "metro"]
              if scenario.get("poll_paths", DEFAULTS["poll_paths"]) == "all"
              else [])
    if verbose and _declined:
        print(f"  polls declined ({len(_declined)}):")
        for _x in _declined:
            print(f"      {_x}")
    # PASS THE LEVER. Until 2026-08-23 this call took no arguments, so the
    # poll-blended CENTRE used `aggregate`'s hardcoded 120.0 default while
    # the two calls below correctly passed the scenario key to the WIDTH.
    # The centre moved 5.6pp of ANC across the lever's range and no sweep
    # could reach it. Number-neutral at the shipped default of 120.0.
    _agg = _pg.aggregate(
        _metro,
        half_life_days=float(scenario.get("poll_half_life_days",
                                          _pg.POLL_HALF_LIFE_DAYS))
    ) if _metro else None
    # `asof` is deliberately NOT passed. The sigma path uses target.date and
    # this uses the newest fieldwork date; aligning them is arguably more
    # correct but it MOVES THE NUMBERS at float level, so it is a separate
    # change that needs its own justification rather than a free rider on
    # this one. Left as it was, and recorded so it is a decision.
    if _agg:
        _sd = scenario.get("_theta_sd") or {}
        _default_sd = float(scenario.get("level_sd_default", DEFAULTS["level_sd_default"]))
        # σ_poll IS NO LONGER A CONSTANT. It is decomposed per poll per party —
        # sampling from the achieved sample, a common term no number of houses
        # removes, an idiosyncratic term that shrinks with houses, a declared
        # surcharge for an undisclosed screen, and drift since fieldwork.
        # See polling._sigma_total; MODEL-LOG §1.87, §1.91.
        #
        # AND THE CAP IS GONE — see the `_cap` line below, which is where this
        # comment used to contradict the code twenty lines beneath it (§1.93).
        # Inverse variance is only correct if both estimates are unbiased, and
        # one house with an undisclosed screen is exactly where the bias term
        # is unbounded; that is still true, and it is now priced by σ_common
        # never dividing by H_eff rather than by a chosen ceiling. Both
        # admitted 2026 Johannesburg polls remain the same house, so H_eff is
        # 1.0 — but a lone house now SATURATES at 0.5761 of the blend on the
        # synthetic fixture instead of being truncated at 0.50, and two houses
        # pass that with four polls (§1.92).
        _asof = target.date
        _credence = float(scenario.get("poll_credence",
                                       DEFAULTS["poll_credence"]))
        _pk = {"screen_sd": float(scenario.get("poll_screen_sd", DEFAULTS["poll_screen_sd"])),
               "drift_rate": float(scenario.get("poll_drift_per_root_day", DEFAULTS["poll_drift_per_root_day"])),
               "deff_subsample": float(scenario.get("poll_deff_subsample", DEFAULTS["poll_deff_subsample"]))}
        _h_eff = _pg.effective_houses(
            _metro, half_life_days=float(scenario.get("poll_half_life_days", DEFAULTS["poll_half_life_days"])), asof=_asof)
        # THE CAP IS DELETED UNDER THE PRE-REGISTERED REPLACEMENT (§1.87).
        # It moves the DA's weight by 0.023 while 538 prices a house with no
        # track record at +0.66pp of ERROR, not a halving of weight — so it is
        # both non-standard in kind and roughly ten times more punitive in
        # degree. Under SIGMA_TWO_TERM the protection is the sigma_common FLOOR,
        # which is the documented mechanism, and the cap would double-count it.
        _cap = (1.0 if _pg.SIGMA_TWO_TERM else
                _pg.weight_cap(_h_eff,
                               house_k=float(scenario.get("poll_house_k", DEFAULTS["poll_house_k"]))))
        for _party, _share in sorted(_agg.items(), key=lambda kv: -kv[1]):
            _mu = float(centres.get(_party, 0.0))
            if _mu <= 0:
                continue
            _msd = float(_sd.get(_party, _default_sd)) * _mu
            # The aggregate's own error: sampling shrinks across waves, the
            # house term shrinks across HOUSES and so does not shrink here.
            _psd = _pg.aggregate_sd(
                _metro, _party, _share, asof=_asof,
                half_life_days=float(scenario.get("poll_half_life_days", DEFAULTS["poll_half_life_days"])),
                **_pk)
            _w_raw = min(_pg.blend_weight(_psd, _msd), _cap)
            # The blend and the reader's credence dial, in one place that can be
            # tested. See blend_poll_centre.
            centres[_party], _w = blend_poll_centre(
                _mu, _share, _w_raw, _credence)
            notes[_party] = notes.get(_party, "") + (
                f" | polls {_share:.1%} @ w={_w:.2f}"
                + (f" (credence {_credence:.2f} on {_w_raw:.2f})"
                   if _credence != 1.0 else "")
                + f" (σp {_psd:.3f}, σm {_msd:.3f}, H_eff {_h_eff:.1f},"
                f" cap {_cap:.2f}): → {centres[_party]:.1%}")
        note_constant(scenario, "metro_poll",
                      ", ".join(q["id"] for q in _metro))
        if verbose:
            print(f"  polls: {len(_metro)} metro wave(s) aggregated by recency "
                  f"({', '.join(q['id'] for q in _metro)})")

    # THE LEGACY POLL PATH WAS DELETED HERE, 2026-08-22 (MODEL-LOG §1.68).
    #
    # `poll_id` / `poll_weight` / `poll_k` re-read `polls.json` directly and
    # applied whatever they found, **bypassing `polling.usable_for` entirely**:
    # no fieldwork-date check, no party-commissioned exclusion, no scope or city
    # check, no election-declaration rule. `--set poll_id="da-internal-2026aug"`
    # admitted the DA's own internal poll; `--set poll_id="ipsos-2016-lge-joburg"`
    # at target 2021 admitted a five-year-stale one, which §1.66 measured at
    # +10.0 CRPS and +8 coherent seats.
    #
    # It had also never executed: it referred to `prior`, a local of
    # `blended_centres`, so it raised NameError the instant `poll_weight` went
    # above zero. Its weight was keyed on how much θ history a party had, which
    # §1.67 replaced with precision — so it was a second poll-weighting
    # implementation sitting beside the live one and disagreeing with it.
    #
    # Nothing is lost. What it existed to do — let a poll speak for a party the
    # record cannot see — is the arrivals path, measured at 48 coherent seats
    # (§1.65). What it did in addition, applying an unscreened poll to every
    # party, is the metro path with admission rules (§1.67).

    if "ENTRANT" in index:
        centres["ENTRANT"] = 0.0

    draw_target = make_drawer(scenario, base_city_d, centres, index, rng)
    _ipf_stats = getattr(draw_target, "ipf_stats", {})
    # The IPF has had a failure counter since it was written; the θ solve that
    # runs twice per draw has never had one, and it has never converged
    # (MODEL-LOG §1.98). Records only — see `solve_and_predict`.
    _solve_stats: dict = {}

    # --- report configuration -------------------------------------------------
    if verbose:
        # A party near its pool capacity BEFORE any shock is one draw away from
        # being clipped, and until 2026-08-17 nobody found out until the balance
        # raised — silently. Say it up front instead.
        tight = sorted(((p, h) for p, h in (_ipf_stats.get("headroom") or {}).items()
                        if h >= 0.90), key=lambda kv: -kv[1])
        if tight:
            print("  ! at or near their pools' capacity before any shock "
                  "(centre ÷ 0.98 × capacity): "
                  + ", ".join(f"{p} {h:.0%}" for p, h in tight[:6]))
    if verbose:
        print(f"{scenario['draws']:,} draws, seed {scenario['seed']}, {nvd} VDs, "
              f"{npar} parties, {len(wards)} wards")
        print(f"target {target.year} ({target.date}), council {target.council}, "
              f"base {cityconfig.resolve_path(target.results(target.previous_npe)).name}, "
              f"γ fold {fold}, wards from {parts_source}")
        print(f"w_bye {scenario['w_bye']}, "
              f"turnout blend {scenario['turnout_pattern_blend']} "
              f"± {scenario['turnout_blend_jitter']} (σ {scenario['turnout_noise_sd']}), "
              f"entrant P {scenario['entrant_prob']}")
        if notes:
            print("\nby-election tilts (clamped to §3.5 ranges):")
            for party, note in sorted(notes.items()):
                print(f"  {party:<10s} {note}")
        shown = [p for p in ("ASA", "MK", "PA") if p in gamma_source]
        if shown:
            print("\nγ sources: " + ", ".join(f"{p}={gamma_source[p]}" for p in shown))
        shown = [p for p in ("MK", "ASA", "PA") if p in index]
        if shown:
            print("ward/PR ratios: " + ", ".join(
                f"{p} {ratio[index[p]]:.2f}" for p in shown))
        print()

    # --- the loop -------------------------------------------------------------
    draws = scenario["draws"]
    seat_draws: list[dict[str, int]] = []
    thresholds = np.zeros(draws, dtype=int)
    council_sizes = np.zeros(draws, dtype=int)
    overhang_count: defaultdict[str, int] = defaultdict(int)
    excessive_draws = 0
    ward_win_sum: defaultdict[str, int] = defaultdict(int)
    ward_winner_counts = np.zeros((len(wards), npar), dtype=np.int32)
    bounds_violations: defaultdict[str, int] = defaultdict(int)
    bounds_checked = 0
    pr_share_draws = np.zeros((draws, npar))
    ward_share_draws = np.zeros((draws, npar))

    for d in range(draws):
        pr_target = draw_target()

        # §3.5 sanity bounds on the implied raw θ (E2). ENTRANT exempt.
        bounds_checked += 1
        for p, (low, high) in PLAN_BOUNDS.items():
            if p in index and base_city[index[p]] > 0.005:
                implied = pr_target[index[p]] / base_city[index[p]]
                if not (low * 0.95 <= implied <= high * 1.05):
                    bounds_violations[p] += 1

        ward_target = pr_target * ratio
        ward_target /= ward_target.sum()

        # A2: turnout pattern for this draw.
        blend = np.clip(scenario["turnout_pattern_blend"]
                        + rng.uniform(-1, 1) * scenario["turnout_blend_jitter"], 0, 1)
        noise = rng.normal(0.0, scenario["turnout_noise_sd"], nvd)
        t_draw = np.clip(((1 - blend) * t_ratio + blend * t_level)
                         * np.exp(noise - scenario["turnout_noise_sd"] ** 2 / 2),
                         TURNOUT_DRAW_FLOOR, TURNOUT_DRAW_CEILING)
        if d == 0:
            # DELIVERY PROOF, recorded at the read site and once rather than
            # 5,000 times. These two are caps applied per draw that
            # JUDGEMENT-CALLS §C did not know existed -- it describes the
            # turnout band as one that REMOVES caps. A constant the register
            # cannot see is exactly the constant a sweep reports flat.
            note_value(scenario, "montecarlo.TURNOUT_DRAW_FLOOR",
                       TURNOUT_DRAW_FLOOR,
                       where="montecarlo:run_model per-draw turnout clip")
            note_value(scenario, "montecarlo.TURNOUT_DRAW_CEILING",
                       TURNOUT_DRAW_CEILING,
                       where="montecarlo:run_model per-draw turnout clip")
        # The who-turns-out tilt used to sit here. It selected supporters by
        # a hand-drawn party grouping, and it was applied AFTER
        # solve_and_predict had already calibrated shares to the drawn target,
        # so rows stopped summing to one and the realised citywide share was no
        # longer the one drawn. It was off by default and never measured.
        # Differential turnout by pool is real and belongs in the model, but it
        # has to enter the weights the calibration sees, not be multiplied on
        # afterwards — and it should key on voter pools, which is where the
        # turnout data can actually be attached.
        weight_cal = reg * t_draw
        weight = weight_cal
        tilt_scale = None

        floor = scenario["level_floor"]
        pr = solve_and_predict(dev_pr, base_city, pr_target, gamma["PR"], weight_cal,
                               level_floor=floor, stats=_solve_stats)
        wd = solve_and_predict(dev_ward, base_city, ward_target, gamma["Ward"], weight_cal,
                               level_floor=floor, stats=_solve_stats)

        pr_eff = pr if tilt_scale is None else pr * tilt_scale
        wd_eff = wd if tilt_scale is None else wd * tilt_scale
        pr_votes = weight @ pr_eff
        ward_votes = weight @ wd_eff
        pr_share_draws[d] = pr_votes / max(pr_votes.sum(), 1e-12)
        ward_share_draws[d] = ward_votes / max(ward_votes.sum(), 1e-12)

        # E3: ward winners from the ward ballot, on the target's own wards.
        part_cast = part_reg * t_draw[part_vd]
        ward_tally = np.zeros((len(wards), npar))
        np.add.at(ward_tally, part_ward, part_cast[:, None] * wd_eff[part_vd])
        if scenario["ward_noise_sd"] > 0:
            ward_tally = ward_tally * np.exp(
                rng.normal(0.0, scenario["ward_noise_sd"], ward_tally.shape))
        winners = ward_tally.argmax(axis=1)
        ward_winner_counts[np.arange(len(wards)), winners] += 1
        wins: defaultdict[str, int] = defaultdict(int)
        for w in winners:
            wins[universe[w]] += 1

        combined = {universe[i]: int(round(pr_votes[i] + ward_votes[i]))
                    for i in range(npar)}
        combined = {p: v for p, v in combined.items() if v > 0}
        seats, council, threshold, over = allocate_with_overhang(
            combined, dict(wins), scenario["overhang_rule"])

        seat_draws.append(seats)
        thresholds[d] = threshold
        council_sizes[d] = council
        for p in over:
            overhang_count[p] += 1
        if over:
            excessive_draws += 1
        for p, w in wins.items():
            ward_win_sum[p] += w
        if verbose and (d + 1) % 1000 == 0:
            print(f"  {d + 1:,} draws")

    # THE OUTCOME AND THE GUARDS THAT FIRED. Everything below was previously
    # visible only as a printed line or not at all; `cap_moved` and
    # `ipf_failures` in particular are the counters whose SILENCE was read as
    # success for two days (MODEL-LOG §1.41), and a silence is much harder to
    # misread when it sits in a file next to the run that produced it.
    trace.put("40_draws", {
        "pr_mean": {universe[i]: float(pr_share_draws[:, i].mean())
                    for i in range(npar)},
        "pr_p5": {universe[i]: float(np.percentile(pr_share_draws[:, i], 5))
                  for i in range(npar)},
        "pr_p95": {universe[i]: float(np.percentile(pr_share_draws[:, i], 95))
                   for i in range(npar)},
        "ward_mean": {universe[i]: float(ward_share_draws[:, i].mean())
                      for i in range(npar)},
        "ward_win_sum": dict(ward_win_sum),
        "seat_mean": {p: float(np.mean([s.get(p, 0) for s in seat_draws]))
                      for p in {q for s in seat_draws for q in s}},
    })
    trace.put("41_guards", {
        "ipf_balances": int(_ipf_stats.get("balances", 0)),
        "ipf_failures": int(_ipf_stats.get("failures", 0)),
        "cap_undershoots": int(capped_targets.undershoots),
        "cap_moved": float(capped_targets.moved),
        "ipf_clipped": dict(_ipf_stats.get("clipped") or {}),
        "ipf_headroom": dict(_ipf_stats.get("headroom") or {}),
        "bounds_violations": dict(bounds_violations),
        "bounds_checked": bounds_checked,
        "excessive_draws": excessive_draws,
        "overhang_count": dict(overhang_count),
        # `solve_nonconvergent` is expected to equal `solve_calls` on the shipped
        # configuration and that is NOT reassuring — see MODEL-LOG §1.98. Read
        # `solve_nonconvergent_reachable` instead: it excludes parties whose
        # target sits under the level floor, which no θ can reach.
        "solve_calls": int(_solve_stats.get("solves", 0)),
        "solve_rounds": int(_solve_stats.get("rounds", 0)),
        "solve_nonconvergent": int(_solve_stats.get("nonconvergent", 0)),
        "solve_nonconvergent_reachable":
            int(_solve_stats.get("nonconvergent_reachable", 0)),
        "solve_worst_gap": float(_solve_stats.get("worst_gap", 0.0)),
        "solve_worst_gap_reachable":
            float(_solve_stats.get("worst_gap_reachable", 0.0)),
        "solve_unreachable_parties":
            int(_solve_stats.get("unreachable_parties", 0)),
        # ABSORPTION, not a failure: the mass the level floor INJECTS, which the
        # row renormalisation then takes from every party above the floor in
        # proportion to size. This is the cause of `solve_worst_gap_reachable`
        # and it is irreducible at a fixed `level_floor` -- 25x the rounds moves
        # the gap 2%. NULL-RESULTS.md §4.3 requires an absorbing stage to report
        # how much it absorbed; this is that number for this stage.
        "solve_floor_injected_mean":
            (float(_solve_stats.get("floor_injected_sum", 0.0))
             / max(int(_solve_stats.get("solves", 0)), 1)),
        "solve_floor_injected_worst":
            float(_solve_stats.get("floor_injected_worst", 0.0)),
        # F10's identity guard: `theta` updates that took 1.0 because `got` had
        # collapsed. Expected to be 0 on the shipped configuration; §1.98 warns
        # that a cure for F12 can activate it, so it is watched rather than
        # assumed.
        "solve_identity_hits": int(_solve_stats.get("identity_hits", 0)),
    })
    trace.put("42_pr_share_draws", pr_share_draws, detail=True)
    trace.put("43_ward_share_draws", ward_share_draws, detail=True)
    trace.put("44_seat_draws", seat_draws, detail=True)
    # THE DELIVERY PROOF. Written LAST and after `note_module_constants`, which
    # reads `sys.modules` and imports nothing: by here every module this run
    # needed has been imported, so a constant recorded `not-imported` really was
    # not reachable rather than merely not reached yet. `41_guards` says what the
    # run did; this says what it was given, and NULL-RESULTS.md §4.1 is the
    # argument for why a null without it is VOID.
    note_module_constants(scenario, where="montecarlo:run_model")
    trace.put("45_delivered", delivery_log(scenario))
    trace.close(constants_read=sorted((scenario.get("_constants_read") or {})),
                delivered=sorted(scenario.get("_delivered") or {}))

    return ModelRun(
        target=target, scenario=scenario, universe=universe, index=index,
        wards=wards, seat_draws=seat_draws, thresholds=thresholds,
        council_sizes=council_sizes,
        ward_winner_counts=ward_winner_counts, ward_win_sum=dict(ward_win_sum),
        overhang_count=dict(overhang_count), excessive_draws=excessive_draws,
        bounds_violations=dict(bounds_violations), bounds_checked=bounds_checked,
        ipf_balances=int(_ipf_stats.get("balances", 0)),
        ipf_failures=int(_ipf_stats.get("failures", 0)),
        cap_undershoots=int(capped_targets.undershoots),
        cap_moved=float(capped_targets.moved),
        ipf_clipped=dict(_ipf_stats.get("clipped") or {}),
        ipf_worst=dict(_ipf_stats.get("worst") or {}),
        ipf_headroom=dict(_ipf_stats.get("headroom") or {}),
        notes=notes, gamma_source=gamma_source, ratio=ratio, n_vd=nvd,
        pr_share_draws=pr_share_draws, ward_share_draws=ward_share_draws)


# --------------------------------------------------------------------------
# main: run the model for one target and write the published outputs
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    cityconfig.add_city_argument(parser)
    cityconfig.add_target_argument(parser)
    parser.add_argument("--draws", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--config", type=Path, help="scenario JSON overriding DEFAULTS")
    parser.add_argument("--set", action="append", metavar="KEY=VALUE",
                        help="override one scenario key, e.g. --set w_bye=0")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw/elections"))
    parser.add_argument("--processed", type=Path, default=None,
                        help="where inputs are read and outputs written "
                             "(default: the target's own processed directory)")
    parser.add_argument("--run-dir", type=Path, default=None,
                        help="write a TRACE here: every stage's output as JSON, "
                             "so an intermediate can be read instead of "
                             "re-derived by adding a print and running again. "
                             "Changes no forecast.")
    parser.add_argument("--trace-detail", action="store_true",
                        help="include per-draw arrays in the trace. Large: tens "
                             "of megabytes at 1500 draws.")
    args = parser.parse_args(argv)
    # use(), not load(): fold.load() and the other readers resolve "{CODE}"
    # against the ACTIVE city, so loading a city without activating it read
    # Johannesburg's files under another city's name.
    city = cityconfig.use(getattr(args, "city", None))
    target = cityconfig.use_target(getattr(args, "target", None))
    apply_city(city)          # after use_target: council size is per-year
    scenario = load_scenario(args)
    processed = args.processed or target.processed
    processed.mkdir(parents=True, exist_ok=True)

    run = run_model(target, scenario, args.data_dir, processed,
                    run_dir=args.run_dir, trace_detail=args.trace_detail)

    universe, wards, index = run.universe, run.wards, run.index
    seat_draws, thresholds = run.seat_draws, run.thresholds
    council_sizes, ward_win_sum = run.council_sizes, run.ward_win_sum
    ward_winner_counts, overhang_count = run.ward_winner_counts, run.overhang_count
    excessive_draws, draws = run.excessive_draws, run.draws
    npar = len(universe)

    # --- report ---------------------------------------------------------------
    def series(party: str) -> np.ndarray:
        return np.array([s.get(party, 0) for s in seat_draws])

    print("\nseat distribution (median [5th–95th percentile]):")
    ranked = sorted(universe, key=lambda p: -series(p).mean())
    for party in ranked:
        s = series(party)
        if s.mean() < 0.4:
            continue
        wins_med = ward_win_sum.get(party, 0) / draws
        print(f"  {party:<10s} {np.median(s):>5.0f}  [{np.percentile(s, 5):>3.0f} – "
              f"{np.percentile(s, 95):>3.0f}]   ward wins ≈ {wins_med:>5.1f}")

    print(f"\ncouncil size: median {int(np.median(council_sizes))}, "
          f"max {council_sizes.max()}   ·   majority threshold: median "
          f"{int(np.median(thresholds))}, max {thresholds.max()}")
    p_excessive_any = excessive_draws / draws
    print(f"P(any party excessive): {p_excessive_any:.1%}" + (
        "   by party: " + ", ".join(
            f"{p} {overhang_count[p] / draws:.1%}"
            for p in sorted(overhang_count, key=lambda q: -overhang_count[q]))
        if overhang_count else ""))

    # The per-draw balance that binds the shocked centres. A fallback here means
    # the level shock was thrown away for EVERY party in that draw, so the rate
    # is reported whether it is zero or not — it was 42.7% of the 2026 forecast
    # and invisible until 2026-08-17. See MODEL-LOG §1.33.
    if run.ipf_balances:
        rate = run.ipf_failures / run.ipf_balances
        print(f"\nper-draw centre balance: {run.ipf_balances:,} attempted, "
              f"{run.ipf_failures:,} fell back ({rate:.1%})"
              + ("   ← the level shock was DISCARDED for every party in those "
                 "draws" if run.ipf_failures else ""))
        if run.ipf_clipped:
            print("  held at their pools' capacity (share of draws, worst ask):")
            for p in sorted(run.ipf_clipped, key=lambda q: -run.ipf_clipped[q])[:6]:
                print(f"    {p:<10s} {run.ipf_clipped[p] / run.ipf_balances:>6.1%}"
                      f"   worst {run.ipf_worst.get(p, 0.0):.0%} of capacity")

    # THE CAPACITY CAP, reported whether it fired or not. `cap_undershoots` and
    # `cap_moved` are named in the comment above the trace as "the counters
    # whose SILENCE was read as success for two days (MODEL-LOG §1.41)" — and
    # they were still, on 2026-08-22, incremented by nothing that printed them
    # and asserted on by nothing. They reached the opt-in trace alone, and
    # CLAUDE.md's own warning about the trace is that it "will happily record a
    # guard that has gone blind". A guard nobody reads is not a guard. §1.69.
    print(f"\ncapacity cap: {run.cap_undershoots:,} target(s) could not be met "
          f"from their own pools; {run.cap_moved:.4%} of the citywide vote was "
          f"redistributed"
          + ("" if run.cap_undershoots else "   (the cap did not bind)"))

    if run.bounds_violations:
        print("\nimplied θ outside §3.5 sanity ranges (share of draws):")
        for p in sorted(run.bounds_violations, key=lambda q: -run.bounds_violations[q]):
            print(f"  {p:<10s} {run.bounds_violations[p] / run.bounds_checked:>6.1%}")

    # E1: the full coalition arithmetic, per-draw thresholds.
    seats_by_party = {p: series(p) for p in ranked if series(p).mean() >= 0.4}
    results = coalitions.analyse(seats_by_party, thresholds)
    # The "widest field" structural rows must count every seat-holding party,
    # not just the top twelve the enumeration works over — the micro-party
    # tail holds ~8 seats and its omission understates the field materially.
    # Named explicitly: this is one specific coalition arithmetic ("can a
    # majority form without these three"), not a claim that they move together.
    WITHOUT = ("ANC", "EFF", "MK")
    field = np.array([sum(v for p, v in s.items() if p not in WITHOUT)
                      for s in seat_draws])
    no_anc = np.array([sum(v for p, v in s.items() if p != "ANC")
                       for s in seat_draws])
    results["structural"]["P(some majority without ANC, EFF and MK)"] = float(
        (field >= thresholds).mean())
    results["structural"]["P(some majority without the ANC)"] = float(
        (no_anc >= thresholds).mean())
    no_da = np.array([sum(v for p, v in s.items() if p != "DA")
                      for s in seat_draws])
    results["structural"]["P(some majority without the DA)"] = float(
        (no_da >= thresholds).mean())
    seat_matrix = np.stack([series(p) for p in ranked])
    largest_names = np.array(ranked)[seat_matrix.argmax(axis=0)]
    results["structural"]["P(DA is the largest single party)"] = float(
        (largest_names == "DA").mean())
    results["structural"]["P(ANC is the largest single party)"] = float(
        (largest_names == "ANC").mean())
    results["structural"]["field without ANC, EFF and MK: median seats"] = float(
        np.median(field))
    coalitions.report(results, "(per-draw threshold, overhang-adjusted)")
    coalitions.write_outputs(results, processed)

    # --- outputs --------------------------------------------------------------
    # A MONTE CARLO ESTIMATE OF 1.000 IS A STATEMENT ABOUT THE DRAW COUNT, NOT
    # ABOUT THE ELECTION, and reporting it as certainty is indefensible.
    # ---------------------------------------------------------------------
    # Until 2026-08-22 this wrote `count / draws`, so a party that won a ward
    # in every draw was published at **p = 1.000** — the map's tooltip said
    # "DA — DA 100%" for 25 of Johannesburg's 135 wards on the 2026 forecast,
    # every one of them DA. That asserts P(anyone else wins) is exactly zero,
    # which is the bounded-support fault: an outcome at probability zero that
    # then happens carries an infinite log score and cannot be defended.
    #
    # **And it is not hypothetical here — it is measured.** Backtested on
    # Johannesburg 2021 at 1500 draws, the wards this model called certain were
    # right **31 times in 32, not 32** (ward 7: PA at p = 1.000, actual ANC).
    # Every other band is calibrated or conservative (0.90-0.99 -> 93% against
    # a nominal 94%; 0.75-0.90 -> 95% against 82%); the top band is the only
    # one that overclaims, and it overclaims a probability of one.
    #
    # Two separate things follow, and only the first is fixed here.
    #
    # 1. **The ESTIMATOR must not report more precision than the sample holds.**
    #    Seeing k = N wins in N draws bounds the loss probability near 1/N; it
    #    does not establish zero. The Jeffreys posterior mean, (k + 1/2)/(N + 1),
    #    is the standard correction and at N = 1500 it reports 0.9997 rather
    #    than 1.0000 — the honest reading of "won every draw we took". It moves
    #    nothing else: no seat, no median, no coherent vector, and no band below
    #    the top is shifted by more than 1/(2N).
    # 2. **The MODEL is still over-confident at the top, and this does not fix
    #    that.** 97% observed against a corrected 99.97% claimed is a real
    #    miscalibration and its cause is that the ward draw carries no mechanism
    #    for a local upset — candidate quality, a defection, a strong
    #    independent. `universe` excludes independents outright, which is
    #    defensible for Johannesburg (they won no ward in 2016 or 2021) and is
    #    an assumption elsewhere. Fixing THAT is a modelling change and needs
    #    measuring; it is written up rather than attempted here.
    #    MODEL-LOG §1.71, DATA-QUALITY item 12.
    def _p_win(count: int) -> float:
        """Jeffreys posterior mean. Never exactly 0 or 1 from a finite sample."""
        return (count + 0.5) / (draws + 1.0)

    # ⛔ A DIAGNOSTIC RUN MUST NOT OVERWRITE THE PUBLISHED ARTEFACTS.
    #
    # `main` writes three files into `data/processed/` — `ward_winner_probs.csv`,
    # `seat_draws.csv`, `forecast_summary.json` — and they are the SITE'S
    # inputs. `data/**` is gitignored, so nothing warns and no artefact key
    # notices; the only symptom is a test failing later for a reason that looks
    # unrelated.
    #
    # That happened on 2026-08-28. `CLAUDE.md` documents
    # `python src/montecarlo.py --city joburg --target 2021 --run-dir /tmp/t`
    # as the way to trace a run, and two such runs — the second a `--set
    # spine_k=0` sweep at 60 draws — replaced the 5,000-draw shipped forecast on
    # disk. `test_the_cartogram_ink_is_proportional_to_seats` went red an hour
    # later, and the cause was a DIAGNOSTIC COMMAND.
    #
    # `run_model`'s docstring says "writes nothing unless `run_dir` is given,
    # and then it writes only a trace". That is true OF THE FUNCTION and was
    # read as covering the command. It does not.
    #
    # So: `--run-dir` means "I am looking at this run", and a run being looked
    # at does not publish. `build_all.py` invokes this with no `--run-dir`
    # (build_all.py:85) and is unaffected.
    if args.run_dir is not None:
        print(f"\n  --run-dir given: the trace is in {args.run_dir} and the "
              f"published artefacts in {processed} were NOT rewritten.\n"
              f"  (A diagnostic run does not publish. Re-run without "
              f"--run-dir to regenerate them.)")
        return 0

    ww_out = processed / "ward_winner_probs.csv"
    with ww_out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["ward", "winner", "p_win", "dist"])
        for wi, w in enumerate(wards):
            order = np.argsort(-ward_winner_counts[wi])
            dist = "|".join(
                f"{universe[i]}:{_p_win(ward_winner_counts[wi, i]):.4f}"
                for i in order if ward_winner_counts[wi, i] > 0)
            writer.writerow([
                w, universe[order[0]],
                f"{_p_win(ward_winner_counts[wi, order[0]]):.4f}", dist])

    seats_out = processed / "seat_draws.csv"
    top = ranked[:13]
    with seats_out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["draw", "threshold", "council_size"] + top)
        for i, s in enumerate(seat_draws):
            writer.writerow([i, thresholds[i], council_sizes[i]]
                            + [s.get(p, 0) for p in top])

    summary = {
        "scenario": scenario,
        "parties": {
            p: {"median": float(np.median(series(p))),
                "p5": float(np.percentile(series(p), 5)),
                "p95": float(np.percentile(series(p), 95)),
                "ward_wins_mean": ward_win_sum.get(p, 0) / draws}
            for p in ranked if series(p).mean() >= 0.4
        },
        "p_excessive_any": p_excessive_any,
        "p_excessive_by_party": {p: overhang_count[p] / draws
                                 for p in sorted(overhang_count,
                                                 key=lambda q: -overhang_count[q])},
        "threshold_median": int(np.median(thresholds)),
        "structural": results["structural"],
        "pairs_triples": results["pairs_triples"][:40],
        "mwc": results["mwc"][:15],
        "power": results["power"],
        "minority": results["minority"],
    }
    summary_out = processed / "forecast_summary.json"
    with summary_out.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=1)

    print(f"\nwrote {seats_out}, {summary_out} and coalition_*.csv")
    return 0


if __name__ == "__main__":
    # Before anything else: this may replace the process. See `fix_hash_seed`.
    fix_hash_seed()
    raise SystemExit(main())
