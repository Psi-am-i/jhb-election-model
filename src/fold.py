"""Backtest a national/provincial baseline against a local-government target (plan §4).

Implements the share sub-model of §3.4(b) and scores it by §4.2's metrics.

The §3.4(b) formula is written as ``logit(Share(i,p) × θ_p) + γ_p·localdev(i,p)``,
which would double-count local information if ``Share(i,p)`` were the VD-level
share, since that already carries it. The reading used here is the one that
matches γ's stated meaning -- "how much of a party's local variation is preserved
versus flattened toward its citywide mean":

    logit(pred(i,p)) = logit(citywide_base(p) · θ_p)
                     + γ_p · [logit(base(i,p)) − logit(citywide_base(p))]
                     + δ_p

so γ_p = 1 preserves the VD's full deviation from the citywide mean, γ_p = 0
flattens every VD to the citywide prediction. Shares are softmax-renormalised
within each VD and floored before the logit so zero-vote VDs stay finite.

θ is measured, not fitted: it is the observed citywide LGE/NPE ratio for the
transition. γ is fitted, per party, by regressing the target's VD-level logit
deviation on the baseline's through the origin, weighted by votes cast. δ is left
at zero here -- it is the scenario lever for the live case, and setting it from
the target would be fitting to the answer.

Because an LGE has two ballots and an NPE one, θ and γ are fitted separately for
the ward and PR ballots. Per the §0 correction, seats follow the two combined.

Usage:
    python src/fold.py --fold 1        # 2014 NPE -> 2016 LGE
    python src/fold.py --fold 2        # 2019 NPE -> 2021 LGE
"""

from __future__ import annotations

import argparse
import csv

import cityconfig
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

import parties as P
from seats import allocate, eligible_parties

FOLDS = {
    1: {
        "base": ("npe2014_{CODE}_vd_party.csv", None),
        "target": ("lge2016_{CODE}_vd_party_clean.csv", True),
        "prior_lge": "2011",
        # The 2009 NPE was acquired on 2026-08-09 (ingest_historic.py), so this
        # fold can now exercise the ratio turnout specification it could not
        # before.
        "lambda_pair": ("2009", "2011"),
    },
    2: {
        "base": ("npe2019_{CODE}_vd_party.csv", None),
        "target": ("lge2021_{CODE}_vd_party_clean.csv", True),
        "prior_lge": "2016",
        "lambda_pair": ("2014", "2016"),
    },
    # Folds 3-5 come from the pre-2011 archives ingested on 2026-08-09. They
    # take the validated NPE->LGE transitions from two to five, which is the
    # single biggest thing available against R6 (single-cycle inference).
    # Voting-district identifiers are stable back to 1999, so these run at VD
    # level unchanged; *ward* identifiers are not, but a fold only ever
    # compares a base to its own target, so that does not bite.
    3: {
        "base": ("npe2009_{CODE}_vd_party.csv", None),
        "target": ("lge2011_{CODE}_vd_party_clean.csv", True),
        "prior_lge": "2006",
        "lambda_pair": ("2004", "2006"),
    },
    4: {
        "base": ("npe2004_{CODE}_vd_party.csv", None),
        "target": ("lge2006_{CODE}_vd_party_clean.csv", True),
        "prior_lge": "2000",
        "lambda_pair": ("1999", "2000"),
    },
    # 1999 predates the metro: the base is the five metropolitan local councils
    # that became Johannesburg, so this fold's geography is approximate and its
    # result should be read as indicative. There is no prior LGE before it.
    5: {
        "base": ("npe1999_approx_{CODE}_vd_party.csv", None),
        "target": ("lge2000_{CODE}_vd_party_clean.csv", True),
        "prior_lge": None,
        "lambda_pair": None,
    },
}

SHARE_FLOOR = 0.002  # plan §3.4(b): keep zero-vote VDs finite under the logit

# The same floor applied to the LEVEL term is not a numerical guard, it is a
# claim: that no party can be smaller than 0.2% of the city anywhere. Johannesburg
# seats cost about 0.37% of the vote, so that claim is worth half a seat to every
# party in the universe that holds one — and the universe has sixty-nine parties
# in it. Measured on fold 2: 42 seats went to 21 parties that won nothing, which
# was the whole of that fold's headline error, because no θ the calibration could
# choose can push logit(city × θ) below logit(0.002).
#
# So the two floors are separated, exactly as montecarlo.py separated them on
# 2026-08-06 (its ``level_floor``, 1e-6). The deviation term keeps 0.002, which
# is what §3.4(b) asked for and what keeps a zero-vote VD finite; the level term
# is freed to represent a party that really is one voter in a thousand.
LEVEL_FLOOR = 1e-6


def logit(p: float, floor: float = SHARE_FLOOR) -> float:
    p = min(max(p, floor), 1 - SHARE_FLOOR)
    return math.log(p / (1 - p))


def load(path: Path, ballot: str | None) -> tuple[dict[str, dict[str, int]], dict[str, str]]:
    """Return VD -> canonical party -> votes, and VD -> ward."""
    votes: defaultdict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
    ward: dict[str, str] = {}
    path = cityconfig.resolve_path(path)   # "{CODE}" -> this city's IEC code
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if ballot and row.get("BallotType", "").upper() != ballot.upper():
                continue
            vd = row["VD_Number"]
            votes[vd][P.canonical(row["sPartyName"])] += int(row["Party_Votes"])
            if row.get("Ward"):
                ward[vd] = row["Ward"]
    return {vd: dict(counts) for vd, counts in votes.items()}, ward


def shares(votes: dict[str, dict[str, int]]) -> dict[str, dict[str, float]]:
    out = {}
    for vd, counts in votes.items():
        total = sum(counts.values())
        if total:
            out[vd] = {party: count / total for party, count in counts.items()}
    return out


def citywide(votes: dict[str, dict[str, int]]) -> dict[str, float]:
    totals: defaultdict[str, int] = defaultdict(int)
    for counts in votes.values():
        for party, count in counts.items():
            totals[party] += count
    cast = sum(totals.values())
    return {party: count / cast for party, count in totals.items()}


def fit_gamma(
    base: dict[str, dict[str, float]],
    target: dict[str, dict[str, float]],
    base_city: dict[str, float],
    target_city: dict[str, float],
    weights: dict[str, int],
    party: str,
) -> tuple[float, int]:
    """Regress target logit-deviation on baseline logit-deviation, through the origin."""
    common = [vd for vd in base if vd in target]
    x, y, w = [], [], []
    for vd in common:
        x.append(logit(base[vd].get(party, 0.0)) - logit(base_city.get(party, SHARE_FLOOR)))
        y.append(logit(target[vd].get(party, 0.0)) - logit(target_city.get(party, SHARE_FLOOR)))
        w.append(weights.get(vd, 1))
    xa, ya, wa = np.array(x), np.array(y), np.array(w, dtype=float)
    denominator = float((wa * xa * xa).sum())
    if denominator == 0:
        return 0.0, len(common)
    return float((wa * xa * ya).sum() / denominator), len(common)


def expit(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def predict(
    base: dict[str, dict[str, float]],
    base_city: dict[str, float],
    theta: dict[str, float],
    gamma: dict[str, float],
    delta: dict[str, float] | None = None,
) -> dict[str, dict[str, float]]:
    """Apply the §3.4(b) share model, renormalised within each VD.

    §3.4(b) says to work in logit space and then "softmax renormalise". Those two
    do not pair. ``logit(p) = log(p/(1-p))`` exponentiates to *odds*, so a softmax
    over logits normalises odds rather than shares, which inflates large parties
    at everyone else's expense -- in fold 1 it put the ANC at 54.0% against an
    actual 44.9% even though θ was set to the exactly-observed citywide ratio.

    Softmax pairs with multinomial log-shares; binary logit pairs with expit
    followed by rescaling. The latter is used here, because it keeps the logit
    semantics §3.4(b) actually wants -- proportional swing where a party is
    small, additive where it is mid-sized, never negative.
    """
    delta = delta or {}
    out: dict[str, dict[str, float]] = {}
    for vd, local in base.items():
        provisional = {}
        for party, city in base_city.items():
            level = logit(city * theta.get(party, 1.0), floor=LEVEL_FLOOR)
            deviation = logit(local.get(party, 0.0)) - logit(city)
            score = level + gamma.get(party, 1.0) * deviation + delta.get(party, 0.0)
            provisional[party] = expit(score)
        total = sum(provisional.values())
        out[vd] = {p: v / total for p, v in provisional.items()} if total else provisional
    return out


def predicted_citywide(
    prediction: dict[str, dict[str, float]], weights: dict[str, int], universe: list[str]
) -> dict[str, float]:
    total = sum(weights.get(vd, 0) for vd in prediction)
    return {
        p: sum(prediction[vd].get(p, 0.0) * weights.get(vd, 0) for vd in prediction) / total
        for p in universe
    }


def calibrate_theta(
    base: dict[str, dict[str, float]],
    base_city: dict[str, float],
    target_city: dict[str, float],
    gamma: dict[str, float],
    weights: dict[str, int],
    universe: list[str],
    rounds: int = 60,
) -> dict[str, float]:
    """Solve for the θ that reproduces the target's citywide shares *through* the model.

    The raw citywide ratio is not the right value. Renormalising within each VD
    moves the aggregate, so feeding the raw ratio in leaves a systematic residual
    on the largest parties -- in fold 1 the ANC came out +3.1pp and the DA -3.3pp.
    Iterative proportional fitting removes it, and makes θ mean the same thing
    when it is *set* for the live case as when it is *measured* here.
    """
    theta = {
        p: (target_city.get(p, 0.0) / base_city[p]) if base_city.get(p, 0) > 0 else 1.0
        for p in universe
    }

    def _rescale(theta: dict[str, float]) -> None:
        """Pin the overall scale of θ. THE ITERATION IS OTHERWISE DEGENERATE.

        ``predict`` renormalises within each VD, so multiplying every θ by a
        constant leaves the prediction unchanged wherever ``expit`` is in its
        exponential tail — and once the levels are low enough, that is every
        party at once. The ratio update then has nothing pulling the common
        factor back, and it wanders.

        It did. On fold 2 the iteration drove the whole vector down by four
        orders of magnitude: the ANC ended at θ = 0.0001, a level of −10.2, and
        the twenty-odd parties pinned at the level floor sat only 3.6 logits
        below it — one thirty-seventh of the ANC rather than the one
        five-thousandth they deserved. Renormalised, that is 0.67% of the vote
        each, just over the 6,838-vote quota, and **21 parties that won nothing
        were allocated 2 seats apiece: 42 of that fold's 96 seat errors.**

        MODEL-LOG blamed SHARE_FLOOR for those seats. The floor is where the
        damage surfaced, not where it came from — lowering it from 0.002 to
        1e-6 moves the compression point and changes the seat totals not at
        all, which is how this was found.

        The constraint is the one the quantity already implies: predicted
        citywide shares are shares, so Σ base·θ = 1.
        """
        total = sum(base_city.get(p, 0.0) * theta.get(p, 1.0) for p in universe)
        if total > 0:
            for p in universe:
                theta[p] /= total

    _rescale(theta)
    for _ in range(rounds):
        got = predicted_citywide(predict(base, base_city, theta, gamma), weights, universe)
        worst = 0.0
        for p in universe:
            want = target_city.get(p, 0.0)
            if got.get(p, 0.0) > 1e-9 and want > 1e-9:
                theta[p] *= want / got[p]
                worst = max(worst, abs(got[p] - want))
        _rescale(theta)
        if worst < 1e-6:
            break
    return theta


def load_parameters(path: Path) -> dict[str, dict[str, dict[str, float]]]:
    """Read a fold's fitted parameters back in, for out-of-sample transfer."""
    out: defaultdict[str, dict[str, dict[str, float]]] = defaultdict(
        lambda: {"theta": {}, "theta_raw": {}, "gamma": {}}
    )
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            ballot = row["ballot"]
            out[ballot]["theta"][row["party"]] = float(row["theta_calibrated"])
            out[ballot]["theta_raw"][row["party"]] = float(row["theta_raw"])
            out[ballot]["gamma"][row["party"]] = float(row["gamma"])
    return dict(out)


def turnout_weights(
    spec: dict,
    method: str,
    data_dir: Path,
    universe_vds: set[str],
) -> tuple[dict[str, float], str]:
    """Votes cast per VD in the target election, under one turnout specification.

    The share model produces shares; turning those into seats needs a *weight*
    per VD, which is votes cast. Earlier versions used the baseline election's
    votes cast, which silently assumed the turnout pattern does not change
    between an NPE and an LGE -- exactly the assumption §3.3 exists to model.

    Every specification is rescaled so its citywide total equals the target's
    actual votes cast. Without that, the comparison would be dominated by which
    method happens to guess the citywide turnout level, when the question here is
    which is right about the *distribution* of turnout across VDs. Getting the
    citywide level right is a separate problem, handled by λ̂ (see turnout.py).

    Returns the weights and a human description.
    """
    from turnout import ELECTIONS as TURNOUT_FILES, read_turnout

    def series(year: str) -> dict[str, tuple[int, int]]:
        filename, two_ballot = TURNOUT_FILES[year]
        return read_turnout(data_dir / filename, two_ballot)

    def have(year: str | None) -> bool:
        """Is that election on disk for the active city?

        A specification can need an election this fold or this city does not
        hold -- fold 5 has no LGE before it, and Tshwane's archive starts at
        2011 where Johannesburg's starts at 1999. That is a gap in the record,
        not a bug, so it is reported rather than raised.
        """
        return bool(year) and cityconfig.resolve_path(
            data_dir / TURNOUT_FILES[year][0]
        ).exists()

    base_year = spec["base"][0][3:7]
    target_year = spec["target"][0][3:7]
    target = series(target_year)
    actual_total = sum(cast for _, cast in target.values())

    if method == "actual":
        raw = {vd: float(cast) for vd, (_, cast) in target.items()}
        label = "actual target turnout (oracle upper bound)"
    elif method == "base":
        base = series(base_year)
        raw = {vd: float(cast) for vd, (_, cast) in base.items()}
        label = f"{base_year} votes cast (assumes turnout pattern unchanged)"
    elif method == "level":
        if not spec["prior_lge"]:
            return {}, "unavailable for this fold"
        if not have(spec["prior_lge"]):
            return {}, f"unavailable for this city (no {spec['prior_lge']} file)"
        prior = series(spec["prior_lge"])
        prior_turnout = {vd: c / r for vd, (r, c) in prior.items() if r}
        raw = {
            vd: target[vd][0] * prior_turnout[vd]
            for vd in target
            if vd in prior_turnout
        }
        label = f"{spec['prior_lge']} LGE turnout pattern x target registration"
    elif method == "ratio":
        if not spec["lambda_pair"]:
            return {}, "unavailable for this fold"
        before, after = spec["lambda_pair"]
        absent = [year for year in (before, after) if not have(year)]
        if absent:
            return {}, f"unavailable for this city (no {', '.join(absent)} file)"
        s_before, s_after, s_base = series(before), series(after), series(base_year)
        lam = {
            vd: (s_after[vd][1] / s_after[vd][0]) / (s_before[vd][1] / s_before[vd][0])
            for vd in set(s_before) & set(s_after)
            if s_before[vd][0] and s_after[vd][0] and s_before[vd][1] / s_before[vd][0] > 0.05
        }
        base_turnout = {vd: c / r for vd, (r, c) in s_base.items() if r}
        raw = {
            vd: target[vd][0] * base_turnout[vd] * lam[vd]
            for vd in target
            if vd in lam and vd in base_turnout
        }
        label = f"{base_year} turnout x λ_{after} (the plan's §3.3 ratio form)"
    else:
        raise ValueError(method)

    raw = {vd: v for vd, v in raw.items() if vd in universe_vds}
    total = sum(raw.values())
    factor = actual_total / total if total else 1.0
    return {vd: v * factor for vd, v in raw.items()}, label


def suspect_vds(concordance: Path, election: str) -> set[str]:
    """VDs flagged as possibly redrawn for a given election (see build_concordance)."""
    if not concordance.exists():
        return set()
    with concordance.open(encoding="utf-8", newline="") as handle:
        return {
            row["vd_historic"]
            for row in csv.DictReader(handle)
            if row["election"] == election and row["stability"] not in ("stable", "unknown")
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fold", type=int, choices=sorted(FOLDS), default=1)
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw/elections"))
    parser.add_argument("--report", type=int, default=8, help="parties to list")
    parser.add_argument(
        "--fit-from",
        type=int,
        choices=sorted(FOLDS),
        help="use another fold's fitted parameters instead of refitting (§4.1)",
    )
    parser.add_argument(
        "--transfer",
        choices=("all", "gamma"),
        default="all",
        help="'all' transfers each party's θ and γ; 'gamma' transfers only γ",
    )
    parser.add_argument(
        "--stability",
        choices=("all", "downweight", "exclude"),
        default="all",
        help="how to treat VDs flagged as possibly redrawn (task #17)",
    )
    parser.add_argument("--w-split", type=float, default=0.6, help="down-weight for suspect VDs")
    parser.add_argument(
        "--turnout",
        choices=("base", "actual", "level", "ratio"),
        default="level",
        help="how to weight VDs by votes cast in the target election (task #19)",
    )
    parser.add_argument(
        "--entrant",
        action="append",
        default=[],
        metavar="CODE=SHARE[:PARENT:K]",
        help="seed a party absent from the baseline with a citywide share, "
             "e.g. ASA=0.1812. Multiplicative θ cannot create a party from zero. "
             "Optionally give the geography it inherits and how far it departs "
             "from it: ASA=0.1812:DA:0.0 places it exactly on the DA's map, "
             ":DA:1.0 spreads it evenly (the old behaviour). k is the "
             "cross-appeal coefficient of MODEL-LOG 1.27 -- measured 0.03 for "
             "MK on the ANC, 0.05 for the EFF on the ANC, 1.00 for ActionSA on "
             "the DA.",
    )
    cityconfig.add_city_argument(parser)
    args = parser.parse_args(argv)
    cityconfig.use(getattr(args, "city", None))

    # CODE=SHARE, or CODE=SHARE:PARENT:K to give the entrant a geography.
    entrants: dict[str, float] = {}
    entrant_map: dict[str, tuple[str, float]] = {}
    for item in args.entrant:
        code, _, value = item.partition("=")
        parts = value.split(":")
        code = code.strip()
        entrants[code] = float(parts[0])
        if len(parts) == 3:
            entrant_map[code] = (parts[1].strip(), float(parts[2]))
        elif len(parts) != 1:
            raise SystemExit(f"--entrant {item!r}: expected CODE=SHARE or "
                             f"CODE=SHARE:PARENT:K")

    spec = FOLDS[args.fold]
    # A fold exists nationally; its FILES exist per city. Only Johannesburg has
    # the pre-2011 ingest, so folds 3-5 die on any other city — and they used to
    # die on a bare FileNotFoundError naming a path, which reads as a broken
    # install rather than as "that fold does not exist for this city". Say which
    # folds this city can actually run, since that is the next thing anyone
    # hitting this needs to know.
    city = cityconfig.active()

    def _file(template: str) -> Path:
        return args.data_dir / template.replace("{CODE}", city.code)

    for role in ("base", "target"):
        path = _file(spec[role][0])
        if not path.exists():
            runnable = [n for n, s in sorted(FOLDS.items())
                        if all(_file(s[r][0]).exists() for r in ("base", "target"))]
            raise SystemExit(
                f"fold {args.fold} needs {path.name}, which {city.name} does "
                f"not have: the pre-2011 archives were only ingested for "
                f"Johannesburg.\n"
                f"  folds runnable for {city.name}: "
                f"{', '.join(str(n) for n in runnable) or 'none'}")
    base_votes, _ = load(args.data_dir / spec["base"][0], spec["base"][1])
    base_share, base_city = shares(base_votes), citywide(base_votes)
    base_weight = {vd: sum(counts.values()) for vd, counts in base_votes.items()}

    # Task #17: the concordance keys on VD number, which cannot be verified
    # geometrically. Re-run with suspect VDs down-weighted or dropped and see
    # whether the parameters move.
    base_year = spec["base"][0][3:7]
    flagged = suspect_vds(Path("data/processed/vd_concordance.csv"), base_year)
    if args.stability == "exclude":
        base_share = {vd: s for vd, s in base_share.items() if vd not in flagged}
        base_weight = {vd: w for vd, w in base_weight.items() if vd not in flagged}
    elif args.stability == "downweight":
        base_weight = {
            vd: int(w * args.w_split) if vd in flagged else w for vd, w in base_weight.items()
        }

    # Votes-cast weights for the target election. This is what turns predicted
    # shares into seats, and it is where the turnout sub-model enters the fold.
    weight, weight_label = turnout_weights(
        spec, args.turnout, args.data_dir, set(base_share)
    )
    if not weight:
        print(f"turnout method '{args.turnout}' is {weight_label}")
        return 1
    base_share = {vd: v for vd, v in base_share.items() if vd in weight}
    base_weight = {vd: base_weight[vd] for vd in base_share}

    source = None
    if args.fit_from:
        # Per-city, or a Tshwane run silently overwrites Joburg's fitted
        # parameters -- and fold1_parameters.csv is what the live forecast
        # reads. Johannesburg keeps the legacy path via City.processed.
        source = load_parameters(
            cityconfig.active().processed / f"fold{args.fit_from}_parameters.csv"
        )

    print(f"fold {args.fold}: {spec['base'][0]} -> {spec['target'][0]}")
    print(
        f"  parameters: {'refit in-sample' if not source else f'from fold {args.fit_from} ({args.transfer})'}"
        f"   turnout: {args.turnout}"
        f"\n  weights: {weight_label}"
        f"\n  stability: {args.stability}"
        f"   ({len(flagged)} of {len(base_share) + (len(flagged) if args.stability == 'exclude' else 0)}"
        f" base VDs flagged)\n"
    )

    fitted: dict[str, dict[str, dict[str, float]]] = {}
    predicted_votes: dict[str, dict[str, dict[str, float]]] = {}

    for ballot in ("PR", "Ward"):
        target_votes, ward_of = load(args.data_dir / spec["target"][0], ballot)
        target_share, target_city = shares(target_votes), citywide(target_votes)
        common = sorted(set(base_share) & set(target_share))

        universe = [p for p in set(base_city) | set(target_city) if p != "IND"]

        # A party with no baseline cannot be produced by a multiplicative θ. Seed
        # it at an assumed citywide share, spatially flat, and let everything else
        # renormalise around it. Without this, IPF silently absorbs the entrant's
        # share into every other party's θ and the θ values stop meaning anything.
        model_base_city = dict(base_city)
        model_base_share = base_share
        if entrants:
            # Where do the entrant's votes go? The default is spatially flat,
            # which is only right for a party with no inherited geography. An
            # entrant given PARENT:K is placed on
            #     share(i) = S * [ (1-k) * parent_index(i) + k ]
            # where parent_index is the parent's VD share over its citywide
            # share, so the weighted mean is 1 and the entrant still totals S
            # whatever k is. k=0 is the parent's map exactly, k=1 is flat.
            total_w = sum(base_weight.values())

            def placed(code: str) -> dict[str, float]:
                share = entrants[code]
                if code not in entrant_map:
                    return {vd: share for vd in base_share}
                parent, k = entrant_map[code]
                pc = sum(base_share[vd].get(parent, 0.0) * base_weight[vd]
                         for vd in base_share) / total_w
                if pc <= 0:
                    raise SystemExit(f"--entrant {code}: parent {parent!r} has "
                                     f"no vote in the baseline, so it has no map")
                return {vd: share * ((1 - k) * (base_share[vd].get(parent, 0.0) / pc) + k)
                        for vd in base_share}

            local_entrants = {code: placed(code) for code in entrants}
            scale = 1 - sum(entrants.values())
            model_base_city = {p: v * scale for p, v in base_city.items()}
            model_base_city.update(entrants)
            model_base_share = {
                vd: {
                    **{p: v * scale for p, v in local.items()},
                    **{code: local_entrants[code][vd] for code in entrants},
                }
                for vd, local in base_share.items()
            }
        if source and ballot in source:
            # Out-of-sample: γ comes from the other fold, defaulting to 1.0 for
            # parties it never saw.
            gamma = {p: source[ballot]["gamma"].get(p, 1.0) for p in universe}
        else:
            gamma = {}
            for p in universe:
                if base_city.get(p, 0) > 0.001:
                    gamma[p], _ = fit_gamma(
                        model_base_share, target_share, model_base_city,
                        target_city, base_weight, p
                    )
                else:
                    gamma[p] = 1.0
        # The raw citywide ratio is what §3.5 quotes as θ; the calibrated value
        # is what this model needs. They are not interchangeable -- see the
        # report below.
        theta_raw = {
            p: (target_city.get(p, 0.0) / model_base_city[p])
            if model_base_city.get(p, 0) > 0 else 1.0
            for p in universe
        }
        if source and ballot in source and args.transfer == "all":
            # Fully out-of-sample: the other fold's θ too, so nothing about this
            # transition's outcome is used. Parties it never saw get 1.0.
            #
            # Worth adding: a `--transfer pool` mode carrying a whole pool's θ
            # and splitting it by prior shares, which tests out of sample
            # whether a pool's members really do trade votes — the forecast's
            # central bet. It must read data/processed/{city}/pools_{target}.json
            # rather than any typed list of parties.
            theta = {p: source[ballot]["theta"].get(p, 1.0) for p in universe}
        else:
            theta = calibrate_theta(
                model_base_share, model_base_city, target_city, gamma,
                weight, universe
            )
        fitted[ballot] = {"theta": theta, "theta_raw": theta_raw, "gamma": gamma}

        prediction = predict(model_base_share, model_base_city, theta, gamma)
        predicted_votes[ballot] = prediction

        # --- §4.2 metrics ---------------------------------------------------
        ranked = sorted(target_city, key=lambda p: -target_city[p])[: args.report]
        print(f"  --- {ballot} ballot ---")
        print(f"  {'party':<10s} {'base':>8s} {'θ raw':>7s} {'θ cal':>7s} {'γ':>6s}"
              f" {'actual':>8s} {'pred':>8s} {'err':>8s}")
        for p in ranked:
            if p == "IND":
                continue
            pred_city = sum(
                prediction[vd].get(p, 0) * weight[vd] for vd in common
            ) / sum(weight[vd] for vd in common)
            print(
                f"  {p:<10s} {base_city.get(p, 0):>8.2%} {theta_raw.get(p, 1):>7.2f}"
                f" {theta.get(p, 1):>7.2f} {gamma.get(p, 1):>6.2f}"
                f" {target_city.get(p, 0):>8.2%}"
                f" {pred_city:>8.2%} {(pred_city - target_city.get(p, 0)) * 100:>+6.2f}pp"
            )

        errors = []
        for vd in common:
            for p in universe:
                errors.append(abs(prediction[vd].get(p, 0) - target_share[vd].get(p, 0)))
        print(f"  VD-level MAE across {len(common)} VDs, {len(universe)} parties: "
              f"{np.mean(errors) * 100:.2f}pp")

        # Ward winner accuracy, on the ward ballot only -- that is what elects.
        if ballot == "Ward" and ward_of:
            wards: defaultdict[str, defaultdict[str, float]] = defaultdict(lambda: defaultdict(float))
            actual: defaultdict[str, defaultdict[str, float]] = defaultdict(lambda: defaultdict(float))
            for vd in common:
                w = ward_of.get(vd)
                if not w:
                    continue
                for p in universe:
                    wards[w][p] += prediction[vd].get(p, 0) * weight[vd]
                    actual[w][p] += target_share[vd].get(p, 0) * weight[vd]
            correct = sum(
                1
                for w in wards
                if max(wards[w], key=wards[w].get) == max(actual[w], key=actual[w].get)
            )
            print(f"  ward winner correct: {correct}/{len(wards)} ({correct / len(wards):.1%})")
        print()

    # --- seats, on the combined ballot per the §0 correction -----------------
    print("  --- seat allocation (combined ward+PR, per §0) ---")
    actual_ward, _ = load(args.data_dir / spec["target"][0], "Ward")
    actual_pr, _ = load(args.data_dir / spec["target"][0], "PR")
    actual_seats = allocate(
        eligible_parties(citywide_counts(actual_ward), citywide_counts(actual_pr))
    ).seats

    predicted_counts = {}
    for ballot, source in (("Ward", actual_ward), ("PR", actual_pr)):
        cast = sum(sum(c.values()) for c in source.values())
        predicted_counts[ballot] = {
            p: int(round(
                sum(
                    predicted_votes[ballot][vd].get(p, 0) * weight[vd]
                    for vd in predicted_votes[ballot]
                )
                / sum(weight.values())
                * cast
            ))
            for p in fitted[ballot]["theta"]
        }
    predicted_seats = allocate(
        eligible_parties(predicted_counts["Ward"], predicted_counts["PR"])
    ).seats

    everyone = sorted(set(actual_seats) | set(predicted_seats), key=lambda p: -actual_seats.get(p, 0))
    print(f"  {'party':<10s} {'actual':>7s} {'predicted':>10s} {'err':>5s}")
    seat_errors = []
    for p in everyone:
        a, b = actual_seats.get(p, 0), predicted_seats.get(p, 0)
        if a or b:
            seat_errors.append(abs(a - b))
            print(f"  {p:<10s} {a:>7d} {b:>10d} {b - a:>+5d}")
    print(f"\n  seat MAE: {np.mean(seat_errors):.2f}   total absolute seat error: {sum(seat_errors)}")

    # Only a DEFAULT fit may claim the canonical filename. Every option below
    # changes the fitted values, and the live forecast reads
    # fold1_parameters.csv for γ -- so a `--turnout ratio` experiment used to
    # replace the parameters the published forecast depends on, silently. It
    # did: on 2026-08-10 a diagnostic run moved 55 of the forecast's 555
    # values, and the only reason anyone noticed was an unrelated check.
    # Anything non-default now writes beside it instead of over it.
    suffix = "" if not args.fit_from else f"_from{args.fit_from}"
    variant = "".join(
        f"__{name}-{value}"
        for name, value, default in (
            ("turnout", args.turnout, "level"),
            ("stability", args.stability, "all"),
            ("transfer", args.transfer, "all"),
            ("wsplit", args.w_split, 0.6),
        )
        if value != default
    )
    if args.entrant:
        variant += "__entrant-" + "_".join(sorted(e.replace("=", "-").replace(":", "-")
                                                  for e in args.entrant))
    out = (cityconfig.active().processed
           / f"fold{args.fold}{suffix}_parameters{variant}.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["ballot", "party", "theta_raw", "theta_calibrated", "gamma"])
        for ballot, values in fitted.items():
            for party in sorted(values["theta"]):
                writer.writerow([
                    ballot, party,
                    f"{values['theta_raw'][party]:.4f}",
                    f"{values['theta'][party]:.4f}",
                    f"{values['gamma'][party]:.4f}",
                ])
    print(f"\n  wrote {out}  (fold 2 validates against these, per §4.1)")
    print(
        "\n  Note on θ: 'raw' is the observed citywide ratio, which is what §3.5"
        "\n  quotes. 'cal' is the value that reproduces that ratio *through* the"
        "\n  model, once within-VD renormalisation is accounted for. They differ"
        "\n  most for the largest parties, so the two are not interchangeable and"
        "\n  §3.5's priors cannot be fed in directly as calibrated θ."
    )
    return 0


def citywide_counts(votes: dict[str, dict[str, int]]) -> dict[str, int]:
    totals: defaultdict[str, int] = defaultdict(int)
    for counts in votes.values():
        for party, count in counts.items():
            totals[party] += count
    return dict(totals)


if __name__ == "__main__":
    raise SystemExit(main())
