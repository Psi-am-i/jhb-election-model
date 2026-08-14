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
import json
import math
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

    # §3.5 central θ modes — the plan's per-party views. E2: these centre the
    # within-pool split. BOSA has no plan θ; 0.80 is a documented judgement
    # (suburbs NPE party at its first LGE).
    "theta_mode": {"ANC": 0.75, "EFF": 0.85, "MK": 0.60,
                   "DA": 1.30, "ASA": 1.50, "BOSA": 0.80},

    # E6: individual (low, mode, high) raw θ for parties outside the pools,
    # drawn independently. Ranges bracket the observed fold-1/fold-2 raw
    # ratios: IFP 1.34→1.97, VF+ 0.81→1.65, ACDP 0.58→1.82, Al Jama-ah 3.12
    # in 2021. Rise has no LGE history: judgement, wide, collapse risk real.
    "individual_theta": {
        "PA": [1.00, 1.40, 2.20],
        "ALJAMAAH": [0.80, 1.50, 3.00],
        "IFP": [0.80, 1.40, 2.20],
        "VFPLUS": [0.70, 1.20, 2.20],
        "ACDP": [0.60, 1.20, 2.00],
        "RISE": [0.30, 0.80, 1.50],
    },
    "f_other": [0.70, 1.30, 2.00],   # residual bucket only, no seat-winner left in it

    # E4: by-election blend weight (§3.5 w_bye, range 0–1). Polls: pick one
    # from polls.json by id and weight it — replaces the old two-endpoint
    # polling_lean lever (kept for compatibility, no longer surfaced).
    "w_bye": 0.40,
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
    "polling_lean": 0.0,
    "polling_span": 8.0,
    "poll_id": None,        # e.g. "srf-2026q2-coj" — see polls.json
    "poll_weight": 0.0,

    # §1.29 weighted pools — the engine. Each pool: members {party: the share
    # of that party's vote drawn from this pool, summing to 1 across pools per
    # party}, a `ratio` triangular on the base, and an `alpha`. Left empty here
    # because it is not a judgement to be typed: `run_model` loads the measured
    # spec that `python src/pools.py --emit` writes, and refuses to run without
    # one. Splinter and entrant lineage is settled there too — a splinter
    # inherits its parent's pool vector, an entrant defaults to an even share
    # of every pool, and both are overridable in judgements/{city}-{target}.toml.
    "pools": {},

    # A1: ward/PR split-ticket ratios are measured from 2021 per party;
    # overrides for parties without a 2021 measurement or with a changed
    # footprint. MK: list party, no ward machinery — 0.80 is a judgement
    # bounded by ActionSA's observed 0.77. PA uplift: fielding more wards
    # than 2021's 52 raises its ward-ballot capture.
    "ward_pr_ratio_overrides": {"MK": 0.80, "ENTRANT": 0.80},
    "pa_contestation_uplift": 1.25,

    # A2: turnout pattern per draw. blend 0 = pure λ̂ ratio form, 1 = pure
    # 2021-LGE-level pattern; the draw jitters the blend ±jitter and applies
    # per-VD lognormal noise (σ in log units ≈ the unexplained λ dispersion).
    "turnout_pattern_blend": 0.5,
    "turnout_blend_jitter": 0.25,
    "turnout_noise_sd": 0.08,

    # A6: generic-entrant slot. Off by setting probability to 0.
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
}


def logit(p, floor=SHARE_FLOOR):
    p = np.clip(p, floor, 1 - SHARE_FLOOR)
    return np.log(p / (1 - p))


def expit(x):
    return 1.0 / (1.0 + np.exp(-x))


def triangular(rng, spec, size=None):
    low, mode, high = spec
    return rng.triangular(low, min(max(mode, low), high), high, size)


# Degrees of freedom for the level shock. A bounded triangular assigns
# probability EXACTLY ZERO outside its support, and this model kept doing that
# to outcomes that had already happened — Al Jama-ah won a Johannesburg seat in
# 2016 with 0 of 500 draws non-zero, which is an infinite log score for an event
# in the record. Student-t in log space has unbounded support and a tail heavy
# enough that a party trebling is unlikely rather than impossible. Four degrees
# of freedom keeps the variance finite (so the measured sd still means what it
# says) while putting roughly 2% of the mass beyond 3.7 sd, against a normal's
# 0.02% — two orders of magnitude more room for the surprise this model has
# repeatedly been surprised by.
LEVEL_DF = 4.0


def log_shock(rng, sd, size=None, df: float = LEVEL_DF):
    """exp of a Student-t scaled to have log-sd exactly ``sd``. Median 1.

    Standardised by sqrt((df-2)/df) so that ``sd`` is the realised log standard
    deviation rather than the t's own, which would be 41% larger at df=4. The
    measured sd(log θ) can then be handed straight in and mean what levels.py
    measured it to mean.
    """
    scale = np.sqrt((df - 2.0) / df)
    return np.exp(np.asarray(sd) * scale * rng.standard_t(df, size=size))


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


def ward_parts(target, data_dir: Path, processed: Path) -> tuple[list[tuple[str, str, int]], str]:
    """VD → ward parts and their registration: ``[(vd, ward, registered), ...]``.

    Two sources, because the two cases genuinely differ.

    **A target not yet held** has a delimitation newer than any result file, so
    the crosswalk ``vd_ward_<year>.csv`` (built by ``build_crosswalk.py``) is
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
    crosswalk = processed / f"vd_ward_{target.year}.csv"
    if crosswalk.exists():
        with crosswalk.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        column = f"Ward_{target.year}"
        parts = [(r["VD_Number"], r[column], int(r["part_registered"]))
                 for r in rows]
        split = len({r["VD_Number"] for r in rows if r.get("is_split") == "Y"})
        return parts, (f"{crosswalk.name} ({len(parts)} parts over "
                       f"{len({r['VD_Number'] for r in rows})} VDs, {split} split)")

    path = data_dir / target.results(target.year)
    seen: dict[str, tuple[str, int]] = {}
    with cityconfig.resolve_path(path).open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            vd = row["VD_Number"]
            if vd in seen or not row.get("Ward"):
                continue
            registered = int(float(row.get("Registered_Population") or 0))
            seen[vd] = (row["Ward"].strip(), registered)
    parts = [(vd, ward, registered) for vd, (ward, registered) in seen.items()]
    return parts, (f"{cityconfig.resolve_path(path).name} "
                   f"(boundaries and roll only; {len(parts)} VDs, none split)")


def solve_and_predict(dev, base_city, target, gamma, weight, rounds=40, tol=1e-6,
                      level_floor=SHARE_FLOOR):
    """Solve for θ reaching `target` citywide through the model; return VD shares."""
    theta = np.where(base_city > 0, target / np.maximum(base_city, 1e-12), 1.0)
    weights = weight / weight.sum()
    for _ in range(rounds):
        level = logit(base_city * theta, floor=level_floor)
        pred = expit(level[None, :] + gamma[None, :] * dev)
        pred /= pred.sum(axis=1, keepdims=True)
        got = weights @ pred
        gap = np.abs(got - target).max()
        theta = theta * np.where(got > 1e-9, target / np.maximum(got, 1e-12), 1.0)
        if gap < tol:
            break
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
    """Point the module's constants at this city.

    Johannesburg's config was generated from these very constants when the
    spine was introduced, so for CoJ this is a no-op by construction — which
    is what lets the refactor happen without the forecast moving.
    """
    global COUNCIL, PLAN_BOUNDS
    COUNCIL = city.council
    PLAN_BOUNDS = city.plan_bounds
    j = city.judgements
    for key in ("theta_mode", "individual_theta", "ward_pr_ratio_overrides"):
        if key in j:
            DEFAULTS[key] = dict(j[key])
    for key, value in j.get("scalars", {}).items():
        if key.endswith("_note"):
            continue
        DEFAULTS[key] = value


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


def note_constant(scenario: dict, constant: str, party: str | None = None) -> None:
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
    reports those. Kept on the scenario (like ``_ward_pr_measured``) so it
    travels into ``forecast_summary.json`` with everything else: values are
    plain lists, because that file is JSON.
    """
    users = scenario.setdefault("_constants_read", {}).setdefault(constant, [])
    who = party or "(all)"
    if who not in users:
        users.append(who)


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
    theta_mode = scenario["theta_mode"]
    individual = scenario["individual_theta"]

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
    spine_level = scenario.get("spine_level") or {}
    for party, base in base_city.items():
        if seeded.get(party, 0.0) > 0:
            band = bands.get(party)
            mode_level = base * (float(band[1]) if band else 1.0)
        elif party in spine_level:
            mode_level = spine_level[party]
        elif party in prior:
            mode_level = base * prior[party][1]
        elif party in theta_mode:
            mode_level = base * theta_mode[party]
            note_constant(scenario, "theta_mode", party)
        elif party in individual:
            mode_level = base * individual[party][1]
            note_constant(scenario, "individual_theta", party)
        else:
            mode_level = base * scenario["f_other"][1]
            note_constant(scenario, "f_other", party)

        centre = mode_level
        if party in bye and w > 0:
            weight_sum, delta = bye[party]
            if weight_sum >= 30:  # enough contests to mean anything
                implied = prior_pr_share.get(party, 0.0) + delta
                if party in prior:
                    low, high = prior[party][0], prior[party][2]
                    mid = prior[party][1] or 1.0
                else:
                    low, high = PLAN_BOUNDS.get(party, (0.0, float("inf")))
                    mid = 1.0
                    if party in PLAN_BOUNDS:
                        note_constant(scenario, "plan_bounds", party)
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
                notes[party] = (
                    f"θ-mode {mode_level:.1%} → {centre:.1%} "
                    f"(by-elections imply {implied:.1%}"
                    + (f", clamped to {clamped:.1%}" if clamped != implied else "")
                    + f", w_bye {w})"
                )
        centres[party] = centre
    return centres, notes


# --------------------------------------------------------------------------
# the draw
# --------------------------------------------------------------------------

def pool_spec(scenario, base_city_d, centres, index, lean):
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
    spec = {}
    for name, cfg in scenario["pools"].items():
        members = {p: float(w) for p, w in cfg["members"].items()
                   if p in index and float(w) > 0}
        if not members:
            continue
        idx = [index[p] for p in members]
        weights = np.array([members[p] for p in members])
        # A pool's base and centre are its members' weighted contributions, so
        # a party sitting half in one pool brings half its vote to each.
        base_total = float(sum(members[p] * base_city_d.get(p, 0.0) for p in members))
        centre_total = float(sum(members[p] * centres.get(p, 0.0) for p in members))
        # Pool movement is a RATIO, not a shift in points. Points only ever
        # worked because there were exactly two pools of roughly fixed size:
        # "-22 points" is meaningless for a pool holding 1.1% of the vote, and
        # applying it to one produces the nonsense that showed up the first
        # time this engine ran. A ratio scales with the pool, which is how θ
        # already works everywhere else in the model.
        # Measured across eight metros and three transitions (PR ballot,
        # LGE total / preceding NPE total): African-side n=24, 0.82-1.01,
        # median 0.88; white-side n=24, 1.09-1.79, median 1.29 -- the
        # differential local-election turnout, in one number.
        # A POOL'S SIZE IS COUNTED, NOT DRAWN. The published roll, split by
        # each ward's own composition, gives how many voters the pool holds.
        # The only uncertain term is turnout, and turnout is an ASSUMPTION
        # rather than a model output: no CoJ poll publishes one, so it defaults
        # to this city's own local-election record and can be overridden in
        # judgements/. The "ratio" this replaces was a single triangular
        # standing in for population change, registration change and turnout
        # change at once, fitted to two transitions and, for a while, borrowed
        # from other cities.
        registered = float(cfg["registered"])
        low, mode, high = cfg["turnout"]
        props = np.array([members[p] * centres.get(p, 0.0) for p in members])
        if props.sum() <= 0:
            props = weights
        props = props / props.sum()
        levels = np.array([members[p] * centres.get(p, 0.0) for p in members])
        spec[name] = (idx, registered, (low, mode, high),
                      props, float(cfg["alpha"]), list(members), levels,
                      {p: members[p] for p in members})
    return spec


def make_drawer(scenario, base_city_d, centres, index, rng):
    """Return a function drawing one citywide PR target vector."""
    n = len(index)
    base_city = np.zeros(n)
    for party, i in index.items():
        base_city[i] = base_city_d.get(party, SHARE_FLOOR)

    lean = scenario["polling_lean"] * scenario["polling_span"]
    if not scenario.get("pools"):
        raise SystemExit(
            "no pools: the model draws from measured voter pools, and there is "
            "nothing to fall back on. Run:\n"
            "  python src/pools.py --city <city> --target <year> --emit")
    pools = pool_spec(scenario, base_city_d, centres, index, lean)

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
    sd_default = float(scenario.get("level_sd_default", 0.45))

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
        if party not in (scenario.get("theta_prior") or {}) \
                and party not in scenario["individual_theta"]:
            note_constant(scenario, "f_other", party)
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
            group_alpha = float(group.get("alpha", 4.0))
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
    dirichlet_floor = float(scenario.get("dirichlet_floor", DIRICHLET_FLOOR))

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
        for name, (idx, reg, spec, props, alpha, names, levels, wts) in pools.items():
            # A PARTY'S OWN LEVEL MOVES, not just its pool's total and its
            # share of the split. Before this, a pooled party had no level
            # uncertainty of its own at all: the pool's turnout moved every
            # member together and the Dirichlet redistributed between them, so
            # the measured sd(log θ) — the one quantity in the model that says
            # how wrong a party's level can be — never entered the draw for any
            # party large enough to be in a pool. That is the under-dispersion
            # the review called structural, and this is where it lived.
            shocks = np.array([pool_sd_shock[p] for p in names])
            moved = props * log_shock(rng, shocks)
            s = moved.sum()
            moved = moved / s if s > 0 else props
            split = rng.dirichlet(np.maximum(moved * alpha, dirichlet_floor))
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
            split = rng.dirichlet(np.maximum(group_w * group_alpha,
                                             dirichlet_floor))
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

    return draw_pools


# --------------------------------------------------------------------------
# seats with overhang (E3)
# --------------------------------------------------------------------------

def allocate_with_overhang(
    combined: dict[str, int], ward_wins: dict[str, int], rule: str = "expand"
) -> tuple[dict[str, int], int, int, dict[str, int]]:
    """Schedule 1 allocation with the excessive-seats treatment.

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
        while True:
            sub = allocate(combined, total_seats=total)
            deficit = sum(max(0, w - sub.seats.get(p, 0))
                          for p, w in ward_wins.items())
            if deficit == 0:
                return dict(sub.seats), total, total // 2 + 1, over
            total += deficit
    if rule == "deduct":
        fixed: dict[str, int] = {}
        votes = dict(combined)
        while True:
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
    for party, excess in over.items():
        seats[party] = seats.get(party, 0) + excess
    council = COUNCIL + sum(over.values())
    return seats, council, council // 2 + 1, over


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
              verbose: bool = True) -> ModelRun:
    """Run the forecast for one target election. Writes nothing.

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
    global COUNCIL
    COUNCIL = target.council
    processed = target.processed if processed is None else processed

    # --- pools: the parties' measured constituencies -------------------------
    # A pool is a body of voters, measured from the census, and a party's
    # membership of it is the share of its vote that demonstrably comes from
    # there. Emitted by `python src/pools.py --emit`. There is no alternative
    # engine, so a missing spec is an error rather than a quiet substitution.
    if not scenario.get("pools"):
        spec_path = target.city.processed / f"pools_{target.year}.json"
        if spec_path.exists():
            spec = json.loads(spec_path.read_text())
            note_constant(scenario, "pools", f"fitted on {spec['fitted_on']}")
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
            small = _groups.get("small", {})
            med, sd = small.get("median", 0.8), small.get("sd_log", 0.8)
            _prior["__small__"] = (med * float(np.exp(-1.2816 * sd)), med,
                                   med * float(np.exp(1.2816 * sd)))
            scenario["theta_prior"] = _prior
            # The measured log-spread per party, carried to the draw. See
            # make_drawer: this is the number the draw was not using.
            scenario["_theta_sd"] = _groups.get("sd", {})
            scenario["_theta_worth"] = _groups.get("worth", {})
            if verbose:
                centre, spread = _groups["centre"], _groups["spread"]
                print(f"  levels: {centre['n']} transitions before "
                      f"{target.year}, common centre {centre['median']:.2f}; "
                      f"sd(log θ) {spread['at_40%']:.2f} at 40% of the vote "
                      f"rising to {spread['at_0.1%']:.2f} at 0.1%")
        _ratios, _fallback = _levels.ward_pr_ratios(target, target.city)
        if _ratios:
            scenario["_ward_pr_measured"] = _ratios
            scenario["_ward_pr_fallback"] = _fallback
        _contest = _levels.contestation(target, target.city)
        if _contest:
            scenario["_contestation"] = _contest
            note_constant(scenario, "contestation",
                          f"{target.year} ward ballot, {len(_contest)} parties")
            if verbose:
                vals = sorted(_contest.values())
                print(f"  contestation: {len(_contest)} parties, median "
                      f"{vals[len(vals) // 2]:.0%} of wards (was: all parties "
                      f"in all wards, with one uplift for the PA)")
    except FileNotFoundError as _exc:
        # Missing data is a legitimate reason to fall back; a bug is not. This
        # used to be a bare `except Exception`, and a stale key in the progress
        # line above was being swallowed by it — so the run reported falling
        # back to the hand-typed constants while actually using the measured
        # ones, or the reverse, depending only on whether verbose was set.
        print(f"  ! level priors unavailable ({_exc}); falling back to the "
              f"hand-typed constants, WHICH SAW THE TARGET")

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
        for party, band in (scenario.get("pool_seed_bands") or {}).items():
            if seeds.get(party, 0.0) > 0:
                scenario["individual_theta"][party] = list(band)
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
    w_ward = scenario.get("w_bye_local_ward", 0.0)
    w_pr = scenario.get("w_bye_local_pr", 0.0)
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
        cap = scenario.get("bye_local_cap", 1.5)
        tau = scenario.get("bye_tau_months", 18.0)
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
    part_rows, parts_source = ward_parts(target, data_dir, processed)
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
    prior_pr_share = pc
    ratio = np.ones(npar)
    for p, i in index.items():
        if pc.get(p, 0) > 0.001:
            ratio[i] = np.clip(wc.get(p, 0.0) / pc[p], 0.5, 2.0)
    # A party with no ward history at the previous LGE gets the median of the
    # parties that have one — a rule that applies to whoever turns up next,
    # rather than the two hand-set numbers this replaces (MK 0.80 "bounded by
    # ActionSA's observed 0.77", ENTRANT 0.80), both of which were read off the
    # target.
    fallback = scenario.get("_ward_pr_fallback")
    if fallback:
        for p, i in index.items():
            if pc.get(p, 0) <= 0.001:
                ratio[i] = fallback
    for p, value in scenario["ward_pr_ratio_overrides"].items():
        if p in index and not fallback:
            ratio[index[p]] = value
            note_constant(scenario, "ward_pr_ratio_overrides", p)

    # Contestation, for every party rather than one. pa_contestation_uplift was
    # 1.25 applied to the PA alone, because it fought 52 of 135 wards in 2021
    # while the model assumed all 135. The median party contests 36% of wards,
    # so the same correction is owed to everyone, and nomination lists are
    # published before polling day so it can be measured instead of chosen.
    contest = scenario.get("_contestation") or {}
    if contest:
        for p, i in index.items():
            share = contest.get(p)
            if share is not None:
                ratio[i] = float(np.clip(ratio[i] * share, 0.0, 2.0))
    elif "PA" in index:
        ratio[index["PA"]] = min(
            ratio[index["PA"]] * scenario["pa_contestation_uplift"], 1.5)
        note_constant(scenario, "pa_contestation_uplift", "PA")

    # --- by-election evidence (E4) -------------------------------------------
    bye: dict[str, tuple[float, float]] = {}
    bye_path = processed / "byelection_party_deltas.csv"
    if bye_path.exists():
        with bye_path.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                bye[row["party"]] = (float(row["weight_sum"]),
                                    float(row["weighted_delta"]))
    # --- the spine: both records, weighted by which one the party has (#22) ---
    # Computed here rather than beside theta_prior because it needs the previous
    # LOCAL election's citywide shares, which are read a few lines up. Both
    # inputs are strictly before the target.
    try:
        import levels as _levels
        _spine, _spine_info = _levels.spine(
            target, base_city_d, prior_pr_share,
            k=float(scenario.get('spine_k') or _levels.SPINE_K))
        if _spine:
            scenario["spine_level"] = _spine
            scenario["_spine_info"] = _spine_info
            note_constant(scenario, "spine",
                          f"k={_spine_info['k']}, {_spine_info['n_theta']} θ and "
                          f"{_spine_info['n_rho']} ρ observations before "
                          f"{target.year}")
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

    centres, notes = blended_centres(scenario, base_city_d, prior_pr_share, bye)
    if scenario.get("poll_id") and scenario.get("poll_weight", 0) > 0:
        polls = {q["id"]: q for q in json.loads(
            Path("polls.json").read_text(encoding="utf-8"))["polls"]}
        poll = polls[scenario["poll_id"]]
        wp = scenario["poll_weight"]
        # `prior` is a LOCAL OF blended_centres. Referring to it here raised
        # NameError, so this whole branch crashed the instant `poll_weight`
        # went above zero — which is to say the polling channel has never once
        # executed. It reads as merely unused because the default weight is 0
        # and nothing exercises it; the first person to turn the dial up gets a
        # traceback, not a forecast. That is the channel MODEL-LOG task #23
        # depends on and that the external review calls the only pre-election
        # evidence for a party with no electoral history.
        prior = scenario.get("theta_prior") or {}
        for party, share in poll["numbers"].items():
            if party in centres and party in base_city_d:
                if party in prior:
                    low, high = prior[party][0], prior[party][2]
                    mid = prior[party][1] or 1.0
                else:
                    low, high = PLAN_BOUNDS.get(party, (0.0, float("inf")))
                    mid = 1.0
                    if party in PLAN_BOUNDS:
                        note_constant(scenario, "plan_bounds", party)
                # Anchored on the level the model believes, not on the national
                # baseline — the same correction the by-election clamp needed,
                # at the third site carrying it.
                #
                # It matters MORE here than there. A poll exists precisely to
                # say something about a party whose history cannot: one with no
                # θ record and a small or absent national base. Clamping a poll
                # to [low × national, high × national] throws away the poll for
                # exactly that party and keeps it only where it was least
                # needed. Pre-2021 polls had ActionSA near 6% against a model
                # estimate of 0.17% in Tshwane; this clamp would have discarded
                # the 6% and kept the 0.17%.
                anchor = centres.get(party) or base_city_d[party]
                clamped = min(max(share, (low / mid) * anchor),
                              (high / mid) * anchor)
                centres[party] = (1 - wp) * centres[party] + wp * clamped
                notes[party] = notes.get(party, "") +                     f" | poll {poll['id']} @ {wp}: → {centres[party]:.1%}"
    if "ENTRANT" in index:
        centres["ENTRANT"] = 0.0

    draw_target = make_drawer(scenario, base_city_d, centres, index, rng)

    # --- report configuration -------------------------------------------------
    if verbose:
        print(f"{scenario['draws']:,} draws, seed {scenario['seed']}, {nvd} VDs, "
              f"{npar} parties, {len(wards)} wards")
        print(f"target {target.year} ({target.date}), council {target.council}, "
              f"base {cityconfig.resolve_path(target.results(target.previous_npe)).name}, "
              f"γ fold {fold}, wards from {parts_source}")
        print(f"w_bye {scenario['w_bye']}, polling lean {scenario['polling_lean']:+.2f}, "
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
                f"{p} {ratio[index[p]]:.2f}" for p in shown)
                + f" (PA uplift ×{scenario['pa_contestation_uplift']})")
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
                         0.02, 0.95)
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
                               level_floor=floor)
        wd = solve_and_predict(dev_ward, base_city, ward_target, gamma["Ward"], weight_cal,
                               level_floor=floor)

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

    return ModelRun(
        target=target, scenario=scenario, universe=universe, index=index,
        wards=wards, seat_draws=seat_draws, thresholds=thresholds,
        council_sizes=council_sizes,
        ward_winner_counts=ward_winner_counts, ward_win_sum=dict(ward_win_sum),
        overhang_count=dict(overhang_count), excessive_draws=excessive_draws,
        bounds_violations=dict(bounds_violations), bounds_checked=bounds_checked,
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

    run = run_model(target, scenario, args.data_dir, processed)

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
    ww_out = processed / "ward_winner_probs.csv"
    with ww_out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["ward", "winner", "p_win", "dist"])
        for wi, w in enumerate(wards):
            order = np.argsort(-ward_winner_counts[wi])
            dist = "|".join(
                f"{universe[i]}:{ward_winner_counts[wi, i] / draws:.4f}"
                for i in order if ward_winner_counts[wi, i] > 0)
            writer.writerow([
                w, universe[order[0]],
                f"{ward_winner_counts[wi, order[0]] / draws:.4f}", dist])

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
    raise SystemExit(main())
