"""Monte Carlo forecast of the 2026 CoJ council (plan §3.4–§3.8, review fixes).

Draws a 2026 scenario, runs it through the share model at VD level, aggregates
both ballots, predicts ward winners, allocates seats under Schedule 1 with the
overhang check, and reports the full coalition arithmetic. The deliverable is
a distribution over coalition viability, never a point forecast (§4.3).

This is a rewrite of the first implementation, fixing the review findings:

* **E1** — coalition arithmetic is fully enumerated (`coalitions.py`): every
  subset, minimal winning coalitions, Banzhaf/Shapley–Shubik, and the
  minority-government class. No pre-filtering on political plausibility.
* **E2** — the within-bloc split is centred on the plan's §3.5 θ modes (its
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
  spans the SRF↔Ipsos disagreement (§8.3): ±1 moves the bloc modes ±4 points,
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
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

import cityconfig
import coalitions
from fold import citywide, load, load_parameters, shares
from seats import INDEPENDENT, allocate

SHARE_FLOOR = 0.002
COUNCIL = 270

BLOCS = {"ANC_BLOC": ("ANC", "EFF", "MK"), "DA_BLOC": ("DA", "ASA", "BOSA")}
ANC_BLOC_PARTIES = ("ANC", "EFF", "MK")

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

    # NPE→LGE bloc shifts in points on the 2024 base (§3.4a, four observed
    # transitions). The *mode* is recentred by evidence (θ modes, by-elections,
    # polling) but always clamped to the historical (low, high).
    "anc_bloc_shift": [-22.0, -9.0, -3.0],
    "da_bloc_shift": [5.0, 9.0, 14.0],
    "alpha_anc": 60.0,       # within-bloc Dirichlet concentration (§3.5 α_split)
    "alpha_da": 12.0,        # low: the ActionSA outcome is genuinely bimodal

    # §3.5 central θ modes — the plan's per-party views. E2: these centre the
    # within-bloc split. BOSA has no plan θ; 0.80 is a documented judgement
    # (suburbs NPE party at its first LGE).
    "theta_mode": {"ANC": 0.75, "EFF": 0.85, "MK": 0.60,
                   "DA": 1.30, "ASA": 1.50, "BOSA": 0.80},

    # E6: individual (low, mode, high) raw θ for parties outside the blocs,
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
    "polling_lean": 0.0,
    "polling_span": 8.0,
    "poll_id": None,        # e.g. "srf-2026q2-coj" — see polls.json
    "poll_weight": 0.0,

    # Trend-break dial (2026-08-06, from the bloc-leakage measurement in
    # MODEL-LOG 1.18). Signed, [-1, 1]. History says ~0 (the 2021 collapse
    # shed 587k votes and the DA bloc captured none).
    #   > 0: that share of the ANC bloc's drawn losses (local share below its
    #        national base) CROSSES to the DA bloc instead of staying home.
    #   < 0: the mirror — that share of DA-bloc losses crosses to the ANC
    #        bloc. Symmetric by construction; the DA bloc's observed range
    #        never dips below base, so this side only fires when user-set
    #        levels push it there.
    "bloc_leak": 0.0,

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
    # who-turns-out tilts, in [-1, 1] per bloc: 0 = as the draw says; +1 =
    # that bloc's supporters vote at their area's highest turnout on record
    # ("all turn out"); -1 = at its worst local-election turnout on record
    # ("stay home"). Supporter-selective and compositional.
    "turnout_tilt_anc": 0.0,
    "turnout_tilt_da": 0.0,

    # A6: generic-entrant slot. Off by setting probability to 0.
    "entrant_prob": 0.25,
    "entrant_share": [0.01, 0.04, 0.12],

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
    global COUNCIL, BLOCS, ANC_BLOC_PARTIES, PLAN_BOUNDS
    COUNCIL = city.council
    BLOCS = city.blocs
    ANC_BLOC_PARTIES = BLOCS["ANC_BLOC"]
    PLAN_BOUNDS = city.plan_bounds
    j = city.judgements
    for key in ("theta_mode", "individual_theta", "ward_pr_ratio_overrides"):
        if key in j:
            DEFAULTS[key] = dict(j[key])
    for key, value in j.get("scalars", {}).items():
        if key.endswith("_note"):
            continue
        DEFAULTS[key] = value


def load_scenario(args) -> dict:
    scenario = copy.deepcopy(DEFAULTS)
    if args.config:
        with open(args.config, encoding="utf-8") as handle:
            overrides = json.load(handle)
        unknown = set(overrides) - set(scenario)
        if unknown:
            raise SystemExit(f"unknown scenario keys in {args.config}: {sorted(unknown)}")
        for key, value in overrides.items():
            if isinstance(scenario[key], dict) and isinstance(value, dict):
                scenario[key].update(value)
            else:
                scenario[key] = value
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
    share_2021: dict[str, float],
    bye: dict[str, tuple[float, float]],
) -> tuple[dict[str, float], dict[str, str]]:
    """Central citywide 2026 level per party, from θ modes tilted by evidence.

    Start from the §3.5 θ-mode view (base_2024 × mode). For parties with
    meaningful by-election weight, the implied level (2021 share + weighted
    delta) is clamped to §3.5's range — a concentrated party's stronghold
    swing cannot claim an absurd citywide level — and blended in at w_bye.
    Returns the centres and a note per adjusted party for the report.
    """
    w = scenario["w_bye"]
    notes: dict[str, str] = {}
    centres: dict[str, float] = {}
    theta_mode = scenario["theta_mode"]
    individual = scenario["individual_theta"]

    for party, base in base_city.items():
        if party in theta_mode:
            mode_level = base * theta_mode[party]
        elif party in individual:
            mode_level = base * individual[party][1]
        else:
            mode_level = base * scenario["f_other"][1]

        centre = mode_level
        if party in bye and w > 0:
            weight_sum, delta = bye[party]
            if weight_sum >= 30:  # enough contests to mean anything
                implied = share_2021.get(party, 0.0) + delta
                low, high = PLAN_BOUNDS.get(party, (0.0, float("inf")))
                clamped = min(max(implied, low * base), high * base)
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

def make_drawer(scenario, base_city_d, centres, index, rng):
    """Return a function drawing one citywide PR target vector."""
    n = len(index)
    base_city = np.zeros(n)
    for party, i in index.items():
        base_city[i] = base_city_d.get(party, SHARE_FLOOR)

    lean = scenario["polling_lean"] * scenario["polling_span"]
    bloc_spec = {}
    for bloc, members in BLOCS.items():
        idx = [index[p] for p in members if p in index]
        base_total = sum(base_city_d.get(p, 0.0) for p in members if p in index)
        centre_total = sum(centres.get(p, 0.0) for p in members if p in index)
        low, mode, high = (scenario["anc_bloc_shift"] if bloc == "ANC_BLOC"
                           else scenario["da_bloc_shift"])
        # Evidence recentres the mode; history bounds it. Polling lever pushes
        # the DA bloc up and the ANC bloc down (SRF) or the reverse (Ipsos).
        evidence_mode = (centre_total - base_total) * 100.0
        evidence_mode += lean if bloc == "DA_BLOC" else -lean
        clamped_mode = min(max(evidence_mode, low), high)
        centre_props = np.array([centres[p] for p in members if p in index])
        centre_props = centre_props / centre_props.sum()
        alpha = scenario["alpha_anc"] if bloc == "ANC_BLOC" else scenario["alpha_da"]
        bloc_spec[bloc] = (idx, base_total, (low, clamped_mode, high),
                          centre_props, alpha)

    handled = {p for members in BLOCS.values() for p in members if p in index}
    individual = []
    for party, i in index.items():
        if party in handled or party == "ENTRANT":
            continue
        spec = scenario["individual_theta"].get(party)
        if spec is not None:
            low, _, high = spec
            mode = min(max(centres[party] / max(base_city[i], 1e-9), low), high)
            individual.append((i, (low, mode, high)))
        else:
            individual.append((i, tuple(scenario["f_other"])))

    entrant_index = index.get("ENTRANT")

    def draw():
        target = np.zeros(n)
        a_idx, a_base, a_spec, a_props, a_alpha = bloc_spec["ANC_BLOC"]
        d_idx, d_base, d_spec, d_props, d_alpha = bloc_spec["DA_BLOC"]
        a_shift = triangular(rng, a_spec) / 100.0
        d_shift = triangular(rng, d_spec) / 100.0
        leak = scenario["bloc_leak"]
        a_total = a_base + a_shift
        d_total = d_base + d_shift
        # symmetric lost-votes crossover: each direction moves a share of the
        # SOURCE bloc's losses (its local share falling below its national
        # base) to the other bloc instead of the couch. The DA bloc's observed
        # range never goes below base, so leak < 0 only fires when user-set
        # levels push d_shift negative — "if there are none, there are none".
        if leak > 0:      # ANC-bloc losses cross to the DA bloc
            d_total += leak * max(0.0, -a_shift)
        elif leak < 0:    # DA-bloc losses cross to the ANC bloc
            a_total += -leak * max(0.0, -d_shift)
        for idx, total, props, alpha in ((a_idx, a_total, a_props, a_alpha),
                                         (d_idx, d_total, d_props, d_alpha)):
            split = rng.dirichlet(np.maximum(props * alpha, 0.05))
            target[idx] = max(total, 0.005) * split
        for i, spec in individual:
            target[i] = base_city[i] * triangular(rng, spec)
        target = target / target.sum()
        if entrant_index is not None:
            share = (triangular(rng, scenario["entrant_share"])
                     if rng.random() < scenario["entrant_prob"] else 0.0)
            target *= (1.0 - share)
            target[entrant_index] = share
        return target

    return draw


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
# main
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    cityconfig.add_city_argument(parser)
    parser.add_argument("--draws", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--config", type=Path, help="scenario JSON overriding DEFAULTS")
    parser.add_argument("--set", action="append", metavar="KEY=VALUE",
                        help="override one scenario key, e.g. --set w_bye=0")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw/elections"))
    parser.add_argument("--processed", type=Path, default=Path("data/processed"))
    args = parser.parse_args(argv)
    city = cityconfig.load(getattr(args, "city", None))
    apply_city(city)
    scenario = load_scenario(args)

    rng = np.random.default_rng(scenario["seed"])

    # --- baseline ------------------------------------------------------------
    base_votes, _ = load(args.data_dir / "npe2024_{CODE}_vd_party.csv", None)
    base_share_d, base_city_d = shares(base_votes), citywide(base_votes)
    universe = sorted(p for p in base_city_d if p != INDEPENDENT and p != "IND")
    if scenario["entrant_prob"] > 0:
        universe.append("ENTRANT")
    index = {party: i for i, party in enumerate(universe)}
    vds = sorted(base_share_d)
    nvd, npar = len(vds), len(universe)

    base_city = np.array([base_city_d.get(p, SHARE_FLOOR) for p in universe])
    local = np.array([[base_share_d[v].get(p, 0.0) for p in universe] for v in vds])
    if "ENTRANT" in index:
        local[:, index["ENTRANT"]] = SHARE_FLOOR  # spatially flat by construction
    dev = logit(local) - logit(base_city)[None, :]

    # --- γ: fold 1, then the 2021→2024 fit, then 1.0 (A4) --------------------
    params = load_parameters(args.processed / "fold1_parameters.csv")
    recent: dict[str, float] = {}
    recent_path = args.processed / "gamma_recent.csv"
    if recent_path.exists():
        with recent_path.open(encoding="utf-8", newline="") as fh:
            recent = {r["party"]: float(r["gamma"]) for r in csv.DictReader(fh)}
    gamma = {}
    gamma_source = {}
    for ballot in ("PR", "Ward"):
        values = np.ones(npar)
        for p, i in index.items():
            if p in params[ballot]["gamma"]:
                values[i] = params[ballot]["gamma"][p]
                gamma_source[p] = "fold1"
            elif p in recent:
                values[i] = recent[p]
                gamma_source.setdefault(p, "2021→2024")
            else:
                gamma_source.setdefault(p, "default 1.0")
        gamma[ballot] = values

    # --- turnout patterns (A2) ----------------------------------------------
    with (args.processed / "vd_ward_2026.csv").open(encoding="utf-8", newline="") as fh:
        part_rows = list(csv.DictReader(fh))
    registered: defaultdict[str, int] = defaultdict(int)
    for row in part_rows:
        registered[row["VD_Number"]] += int(row["part_registered"])

    ratio_pattern: dict[str, float] = {}
    level_pattern: dict[str, float] = {}
    thi_pattern: dict[str, float] = {}
    tlo_pattern: dict[str, float] = {}
    with (args.processed / "turnout.csv").open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            vd = row["VD_Number"]
            if row["turnout_2026_projected"]:
                ratio_pattern[vd] = float(row["turnout_2026_projected"])
            if row.get("turnout_2021") and row["turnout_2021"] != "nan":
                level_pattern[vd] = min(float(row["turnout_2021"]), 1.0)
            hi = [row.get(f"turnout_{y}") for y in (2011, 2014, 2016, 2019,
                                                    2021, 2024)]
            hi_vals = [float(x) for x in hi if x and x != "nan"]
            if hi_vals:
                thi_pattern[vd] = min(max(hi_vals), 1.0)
            lge = [row.get(f"turnout_{y}") for y in (2011, 2016, 2021)]
            vals = [float(x) for x in lge if x and x != "nan"]
            if vals:
                tlo_pattern[vd] = min(min(vals), 1.0)

    reg = np.array([registered.get(v, 0) for v in vds], dtype=float)
    t_ratio = np.array([ratio_pattern.get(v, np.nan) for v in vds])
    t_level = np.array([level_pattern.get(v, np.nan) for v in vds])
    mean_ratio = np.nansum(t_ratio * reg) / np.nansum(np.where(np.isnan(t_ratio), 0, reg))
    t_ratio = np.where(np.isnan(t_ratio), mean_ratio, t_ratio)
    mean_level = np.nansum(t_level * reg) / np.nansum(np.where(np.isnan(t_level), 0, reg))
    # Rescale the 2021-level pattern to the λ̂ citywide level: the level comes
    # from λ̂ either way (MODEL-LOG 1.2); only the *pattern* differs.
    t_level = np.where(np.isnan(t_level), mean_level, t_level) * (mean_ratio / mean_level)

    # who-turns-out anchors per VD (highest turnout on record; worst LGE
    # turnout on record), for the turnout_tilt_* dials
    t_hi = np.array([thi_pattern.get(v, np.nan) for v in vds])
    mhi = np.nansum(t_hi * reg) / np.nansum(np.where(np.isnan(t_hi), 0, reg))
    t_hi = np.where(np.isnan(t_hi), mhi, t_hi)
    t_lo = np.array([tlo_pattern.get(v, np.nan) for v in vds])
    mlo = np.nansum(t_lo * reg) / np.nansum(np.where(np.isnan(t_lo), 0, reg))
    t_lo = np.where(np.isnan(t_lo), mlo, t_lo)
    anc_ids = [index[p] for p in BLOCS["ANC_BLOC"] if p in index]
    da_ids = [index[p] for p in BLOCS["DA_BLOC"] if p in index]

    # --- ward structure (E3) -------------------------------------------------
    vd_index = {v: i for i, v in enumerate(vds)}
    wards = sorted({row["Ward_2026"] for row in part_rows}, key=int)
    ward_index = {w: i for i, w in enumerate(wards)}
    part_vd = np.array([vd_index[r["VD_Number"]] for r in part_rows
                        if r["VD_Number"] in vd_index])
    part_ward = np.array([ward_index[r["Ward_2026"]] for r in part_rows
                          if r["VD_Number"] in vd_index])
    part_reg = np.array([int(r["part_registered"]) for r in part_rows
                         if r["VD_Number"] in vd_index], dtype=float)

    # --- ward/PR split-ticket ratios (A1) ------------------------------------
    ward21, _ = load(args.data_dir / "lge2021_{CODE}_vd_party_clean.csv", "Ward")
    pr21, _ = load(args.data_dir / "lge2021_{CODE}_vd_party_clean.csv", "PR")
    wc, pc = citywide(ward21), citywide(pr21)
    share_2021 = pc
    ratio = np.ones(npar)
    for p, i in index.items():
        if pc.get(p, 0) > 0.001:
            ratio[i] = np.clip(wc.get(p, 0.0) / pc[p], 0.5, 2.0)
    for p, value in scenario["ward_pr_ratio_overrides"].items():
        if p in index:
            ratio[index[p]] = value
    if "PA" in index:
        ratio[index["PA"]] = min(ratio[index["PA"]] * scenario["pa_contestation_uplift"], 1.5)

    # --- by-election evidence (E4) -------------------------------------------
    bye: dict[str, tuple[float, float]] = {}
    bye_path = args.processed / "byelection_party_deltas.csv"
    if bye_path.exists():
        with bye_path.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                bye[row["party"]] = (float(row["weight_sum"]),
                                    float(row["weighted_delta"]))
    centres, notes = blended_centres(scenario, base_city_d, share_2021, bye)
    if scenario.get("poll_id") and scenario.get("poll_weight", 0) > 0:
        polls = {q["id"]: q for q in json.loads(
            Path("polls.json").read_text(encoding="utf-8"))["polls"]}
        poll = polls[scenario["poll_id"]]
        wp = scenario["poll_weight"]
        for party, share in poll["numbers"].items():
            if party in centres and party in base_city_d:
                low, high = PLAN_BOUNDS.get(party, (0.0, float("inf")))
                clamped = min(max(share, low * base_city_d[party]),
                              high * base_city_d[party])
                centres[party] = (1 - wp) * centres[party] + wp * clamped
                notes[party] = notes.get(party, "") +                     f" | poll {poll['id']} @ {wp}: → {centres[party]:.1%}"
    if "ENTRANT" in index:
        centres["ENTRANT"] = 0.0

    draw_target = make_drawer(scenario, base_city_d, centres, index, rng)

    # --- report configuration -------------------------------------------------
    print(f"{scenario['draws']:,} draws, seed {scenario['seed']}, {nvd} VDs, "
          f"{npar} parties, {len(wards)} wards")
    print(f"w_bye {scenario['w_bye']}, polling lean {scenario['polling_lean']:+.2f}, "
          f"turnout blend {scenario['turnout_pattern_blend']} "
          f"± {scenario['turnout_blend_jitter']} (σ {scenario['turnout_noise_sd']}), "
          f"entrant P {scenario['entrant_prob']}")
    if notes:
        print("\nby-election tilts (clamped to §3.5 ranges):")
        for party, note in sorted(notes.items()):
            print(f"  {party:<10s} {note}")
    print("\nγ sources: " + ", ".join(
        f"{p}={gamma_source[p]}" for p in ("ASA", "MK", "PA") if p in gamma_source))
    print(f"ward/PR ratios: MK {ratio[index['MK']]:.2f} (override), "
          f"ASA {ratio[index['ASA']]:.2f}, PA {ratio[index['PA']]:.2f} "
          f"(uplift ×{scenario['pa_contestation_uplift']})\n")

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
        # who-turns-out tilts are PARTY-SELECTIVE and compositional: the
        # scenario's within-VD shares are calibrated on the untilted weights,
        # then the tilt scales the target BLOC'S SUPPORTERS — wherever they
        # live — between the draw's turnout and the anchor (highest turnout
        # on record up, worst LGE on record down). Neighbours' votes are
        # untouched: one camp's machine outworking the other, not a ward-wide
        # tide (which would mobilise the other camp's voters too).
        weight_cal = reg * t_draw
        weight = weight_cal
        tilt_a = scenario["turnout_tilt_anc"]
        tilt_d = scenario["turnout_tilt_da"]
        tilt_scale = None
        if tilt_a or tilt_d:
            def _bloc_scale(t):
                # "all turn out" can only add votes; "stay home" can only
                # remove them (the worst-ever anchor can sit a hair above the
                # baseline, which must not make staying home a gain)
                anchor = t_hi if t >= 0 else t_lo
                raw = 1.0 + abs(t) * (anchor / t_draw - 1.0)
                return (np.clip(raw, 1.0, 4.0) if t >= 0
                        else np.clip(raw, 0.25, 1.0))
            tilt_scale = np.ones((nvd, npar))
            if tilt_a:
                tilt_scale[:, anc_ids] = _bloc_scale(tilt_a)[:, None]
            if tilt_d:
                tilt_scale[:, da_ids] = _bloc_scale(tilt_d)[:, None]

        floor = scenario["level_floor"]
        pr = solve_and_predict(dev, base_city, pr_target, gamma["PR"], weight_cal,
                               level_floor=floor)
        wd = solve_and_predict(dev, base_city, ward_target, gamma["Ward"], weight_cal,
                               level_floor=floor)

        pr_eff = pr if tilt_scale is None else pr * tilt_scale
        wd_eff = wd if tilt_scale is None else wd * tilt_scale
        pr_votes = weight @ pr_eff
        ward_votes = weight @ wd_eff

        # E3: ward winners from the ward ballot, at 2026-ward level.
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
        if (d + 1) % 1000 == 0:
            print(f"  {d + 1:,} draws")

    # --- report ---------------------------------------------------------------
    def series(party: str) -> np.ndarray:
        return np.array([s.get(party, 0) for s in seat_draws])

    print("\nseat distribution (median [5th–95th percentile]):")
    ranked = sorted(universe, key=lambda p: -series(p).mean())
    for party in ranked:
        s = series(party)
        if s.mean() < 0.4:
            continue
        wins_med = ward_win_sum[party] / draws
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

    if bounds_violations:
        print("\nimplied θ outside §3.5 sanity ranges (share of draws):")
        for p in sorted(bounds_violations, key=lambda q: -bounds_violations[q]):
            print(f"  {p:<10s} {bounds_violations[p] / bounds_checked:>6.1%}")

    # E1: the full coalition arithmetic, per-draw thresholds.
    seats_by_party = {p: series(p) for p in ranked if series(p).mean() >= 0.4}
    results = coalitions.analyse(seats_by_party, thresholds)
    # The "widest field" structural rows must count every seat-holding party,
    # not just the top twelve the enumeration works over — the micro-party
    # tail holds ~8 seats and its omission understates the field materially.
    field = np.array([sum(v for p, v in s.items() if p not in ANC_BLOC_PARTIES)
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
    results["structural"]["non-bloc field median seats"] = float(np.median(field))
    coalitions.report(results, "(per-draw threshold, overhang-adjusted)")
    coalitions.write_outputs(results, args.processed)

    # --- outputs --------------------------------------------------------------
    ww_out = args.processed / "ward_winner_probs.csv"
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

    seats_out = args.processed / "seat_draws.csv"
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
                "ward_wins_mean": ward_win_sum[p] / draws}
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
    summary_out = args.processed / "forecast_summary.json"
    with summary_out.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=1)

    print(f"\nwrote {seats_out}, {summary_out} and coalition_*.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
