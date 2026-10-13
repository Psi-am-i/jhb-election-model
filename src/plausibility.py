"""Are the simulated elections ones the world could produce? Whole-election plausibility.

    .venv/bin/python src/plausibility.py --runs DIR --label NAME --out DIR [--mode strict]

``--out`` is required and refused under ``data/``.

Design: ``audits/2026-10-11-model-round/step1/1h-plausibility-check-design.md``
§5; the instrument ``prereg/2026-10-12-universal-draw.md`` §4 scores the round
with (with randomised PIT for count features and exceedance below and above
reported separately, v4 addendum §3.2).

WHAT IT DOES. It turns every simulated election (one draw of a run) and every
real one into the same twenty whole-election FEATURES (§1.1 of the design:
volatility, the new parties' share and the largest, the largest gain and loss,
fragmentation and its change, the top one and two, how many parties clear 1%,
5% and 10%, the small-party bucket, the tiny-party jump and mass, turnout's
change, and three ward features), and judges each run against the REAL record
of consecutive local elections that came before its target:

* envelope exceedance: the share of draws below the record's minimum and above
  its maximum, each against the exchangeable rate 1/(n+1), and the share more
  than ``OUTER_K`` record IQRs beyond the range;
* the calibrated event test: across targets, the count of real elections
  outside the record against the Poisson-binomial of the model's own
  probabilities of being outside, both tails;
* the randomised PIT of the realised value among the target's draws;
* the joint counts: features out of a set on which a draw (or a real
  election) leaves the record, on the seven whole-vote features
  (``J7_no_w_top``, the pre-registration's U1 and U2) and on those plus
  ``w_top`` (``J8_with_w_top``, its U3). A count is ``complete`` only when
  every feature of its set was judged; the panel aggregates complete ones
  only and says how many it left out;
* party level, by size class at the previous election: retained ratios,
  collapse and jump against the record's extremes, threshold events, class mass.

THE PANEL IS PREREG §2's SCORED POPULATION (``scored_population``): the 16
city-years of 2016 and 2021. Every run read gets its per-target rows; 2011
(untestable) and the 2026 forecast are labelled ``scored: false`` with the
reason and enter no panel number. A missing member of the population refuses
unless ``--allow-incomplete``, which the output records.

IT JUDGES AND SETS NOTHING (design §3.1). Every quantity here that compares the
model with the record is a ratio against model output, so using it to SET a
parameter would be tuning. No module the model imports may import this one
(``tests/test_plausibility.py`` asserts it), and its outputs are read by no
code path that produces a draw.

THE RECORD IGNORES `levels.HELD_BACK`, deliberately and visibly: the 2000 files
are held back from the MODEL pending a regime diagnosis, which is a reason
about the model's prior, not about the data (design §2.1). The output says so.

Every feature names no party: ranks, size classes and counts only.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

import cityconfig            # noqa: E402
from fold import citywide, load  # noqa: E402

DATA = REPO / "data/raw/elections"

# THE INSTRUMENT'S JUDGEMENT CALLS (design §5.1; JUDGEMENT-CALLS §P4). None is
# forced by the record.
TINY_LINE = 0.01            # the tiny-party line for features 14-16
SIZE_CLASSES = ((0.0, 0.01), (0.01, 0.03), (0.03, 0.10), (0.10, 0.30),
                (0.30, 1.01))
OUTER_K = 1.0               # the outer envelope, in record IQRs
# THE TWO JOINT COUNTS, named apart (step-6 review, item 1). The
# pre-registration scores U1 (§5.2), §5.1 row 1 and §5.6 row 4 on the SEVEN
# whole-vote features, and only U3 adds the ward feature `w_top`. One tuple of
# eight, counted over whichever were present, reported U1 on the wrong set.
J7_FEATURES = ("vol", "max_gain", "max_loss", "d_enp", "top2", "n_ge5",
               "tiny_max")
J8_FEATURES = J7_FEATURES + ("w_top",)
# The joint statistics, by output key: U1/U2 read "J7_no_w_top", U3 reads
# "J8_with_w_top".
JOINT_SETS = {"J7_no_w_top": J7_FEATURES, "J8_with_w_top": J8_FEATURES}
RATIO_LOG_FLOOR = 1e-4      # the floor under a retained ratio's log
MIN_JUDGING = 8             # the fewest transitions a target may be judged by
FAIL_P = 0.05               # a tail of the event test below this fails
PIT90_MIN_FRACTION = 0.75   # 18 of 24 inside the central 90%
COLLAPSE_JUMP_MULT = 3.0    # a class fails when collapse or jump > 3/(n+1)

CITY_FEATURES = ("vol", "new_share", "max_new", "max_gain", "max_loss", "enp",
                 "d_enp", "top1", "top2", "n_ge1", "n_ge5", "n_ge10",
                 "sub1_mass", "tiny_max", "tiny_mass", "tiny_n_ge1",
                 "d_turnout", "w_top", "w_n", "w_other")
COUNT_FEATURES = ("n_ge1", "n_ge5", "n_ge10", "tiny_n_ge1", "w_n")
# Driven by one national swing per cycle, so their event p-values are
# anti-conservative (design §2.3); reported, not failed.
CYCLE_DRIVEN = ("enp", "d_enp", "top2", "d_turnout")
MODES = ("strict", "strict06", "loco")

# THE SCORED POPULATION (prereg `2026-10-12-universal-draw.md` §2): every
# metro of `compare_history.CITIES` at the 2016 and 2021 backtests, judged by
# real results. 2011 is run and reported, labelled untestable, and enters no
# rule (§2, §10 last row); Johannesburg 2026 is a forecast with no result,
# reported under §5.6. ONE DEFINITION: `arms.compare` scores this population
# too, and both assert its size, `SCORED_COUNT`, the prereg's "16 city-years".
SCORED_YEARS = ("2016", "2021")
SCORED_COUNT = 16
UNSCORED_WHY = {"2011": "untestable: no earlier width record (prereg §2)",
                "2026": "a forecast with no result (prereg §2, §5.6)"}


def scored_population() -> list[tuple[str, str]]:
    """The prereg's scored city-years, ``(city, year)``, in a fixed order.
    REFUSES (SystemExit) when the enumeration is not ``SCORED_COUNT`` long: a
    metro added to or dropped from ``compare_history.CITIES`` changes the
    registered population, which is an amendment, not a default."""
    import compare_history as CH
    out = [(c, y) for y in SCORED_YEARS for c in CH.CITIES]
    if len(out) != SCORED_COUNT:
        raise SystemExit(f"the scored population is {len(out)} city-years; "
                         f"prereg §2 registers {SCORED_COUNT}")
    return out


def unscored_reason(year: str) -> str:
    """Why a city-year outside the scored population is reported only."""
    return UNSCORED_WHY.get(str(year), "outside prereg §2's scored population")


def check_population(have, population, allow_incomplete: bool = False
                     ) -> dict:
    """``{"expected", "missing", "complete", "allow_incomplete"}`` for the
    city-years ``have`` against ``population``. REFUSES (SystemExit) a
    population with a member missing unless ``allow_incomplete``, and the
    output says the flag was passed: a panel scored over fewer city-years
    than registered is a different statistic under the same name."""
    have = set(have)
    missing = sorted(f"{c}-{y}" for c, y in population if (c, y) not in have)
    if missing and not allow_incomplete:
        raise SystemExit(f"the scored population is incomplete: {len(missing)} "
                         f"of {len(population)} city-years missing "
                         f"({', '.join(missing)}); pass allow_incomplete to "
                         f"score the rest, and the output says so")
    return {"expected": len(population), "missing": missing,
            "complete": not missing, "allow_incomplete": bool(allow_incomplete)}


# --------------------------------------------------------------------------
# the real record
# --------------------------------------------------------------------------

def election_record(path: Path) -> dict:
    """One real local election from its result file: citywide list shares,
    ward winners (``backtest.ward_winners``, the one aggregation the backtest's
    ground truth uses), the registered roll and the valid list votes."""
    import backtest
    pr, _ = load(path, "PR")
    wv, ward_of = load(path, "Ward")
    roll, valid = backtest.registered_roll(path)
    return {"pr": citywide(pr), "winners": backtest.ward_winners(wv, ward_of),
            "registered": roll, "pr_valid": valid,
            "turnout": (valid / roll) if roll else None,
            "path": str(cityconfig.resolve_path(path))}


def record(cities=None, years=None) -> dict:
    """``{(city, year): election}`` for every metro LGE with a result file.

    Every local election in ``cityconfig.CALENDAR`` with results, in every
    city; ``levels.HELD_BACK`` is IGNORED (see the module docstring)."""
    import compare_history as CH
    cities = list(cities or CH.CITIES)
    lge = sorted((y for y, e in cityconfig.CALENDAR.items()
                  if e.kind == "LGE" and e.results), key=int)
    years = [y for y in lge if years is None or y in years]
    out = {}
    for c in cities:
        cityconfig.use(c)
        for y in years:
            t = cityconfig.use_target(y)
            path = DATA / t.results(y)
            if not cityconfig.resolve_path(path).exists():
                continue
            out[(c, y)] = election_record(path)
    return out


# --------------------------------------------------------------------------
# the features: ONE definition for a draw and for a real election
# --------------------------------------------------------------------------

def transition_features(s_prev: dict, cols: list, S: np.ndarray,
                        t_prev: float | None, T: np.ndarray | None,
                        W: np.ndarray | None) -> dict[str, np.ndarray]:
    """The twenty features of design §1.1, one value per row of ``S``.

    ``s_prev``: the previous election's citywide list shares (every party that
    stood). ``cols``: the parties of ``S``'s columns. ``S``: draws × parties
    list shares (a real election is a one-row call). ``t_prev``, ``T``: the
    previous turnout and per-row turnout (valid list votes over the roll), or
    None. ``W``: draws × wards column indices of each ward's winner, or None.
    A previous party with no column counts as a loss (it did not stand)."""
    S = np.asarray(S, dtype=float)
    D = S.shape[0]
    colset = set(cols)
    s0 = np.array([s_prev.get(c, 0.0) for c in cols])
    extra = np.array([v for k, v in s_prev.items() if k not in colset] or [0.0])
    diff = S - s0
    f: dict[str, np.ndarray] = {}
    f["vol"] = 50.0 * (np.abs(diff).sum(1) + extra.sum())
    new = s0 == 0
    f["new_share"] = 100 * S[:, new].sum(1) if new.any() else np.zeros(D)
    f["max_new"] = 100 * S[:, new].max(1) if new.any() else np.zeros(D)
    f["max_gain"] = 100 * diff.max(1)
    f["max_loss"] = 100 * np.maximum((-diff).max(1), extra.max())
    f["enp"] = 1.0 / (S ** 2).sum(1)
    f["d_enp"] = f["enp"] - 1.0 / sum(v * v for v in s_prev.values())
    srt = -np.sort(-S, axis=1)
    f["top1"] = 100 * srt[:, 0]
    f["top2"] = 100 * (srt[:, 0] + (srt[:, 1] if S.shape[1] > 1 else 0.0))
    for th, nm in ((0.01, "n_ge1"), (0.05, "n_ge5"), (0.10, "n_ge10")):
        f[nm] = (S >= th).sum(1).astype(float)
    f["sub1_mass"] = 100 * np.where(S < TINY_LINE, S, 0.0).sum(1)
    tiny = (s0 > 0) & (s0 < TINY_LINE)
    if tiny.any():
        f["tiny_max"] = 100 * S[:, tiny].max(1)
        f["tiny_mass"] = 100 * S[:, tiny].sum(1)
        f["tiny_n_ge1"] = (S[:, tiny] >= TINY_LINE).sum(1).astype(float)
    else:
        f["tiny_max"] = f["tiny_mass"] = f["tiny_n_ge1"] = np.zeros(D)
    if T is not None and t_prev is not None:
        f["d_turnout"] = 100 * (np.asarray(T, dtype=float) - t_prev)
    if W is not None:
        W = np.asarray(W, dtype=int)
        cnt = np.zeros((D, S.shape[1]))
        np.add.at(cnt, (np.repeat(np.arange(D), W.shape[1]), W.ravel()), 1)
        nw = W.shape[1]
        cs = -np.sort(-cnt, axis=1)
        f["w_top"] = 100 * cs[:, 0] / nw
        f["w_n"] = (cnt > 0).sum(1).astype(float)
        f["w_other"] = 100 * (1 - (cs[:, 0] + (cs[:, 1] if cs.shape[1] > 1
                                                else 0.0)) / nw)
    return f


def real_features(prev: dict, cur: dict) -> dict[str, float]:
    """A real transition's features: the one definition, called on one row."""
    cols = sorted(cur["pr"])
    S = np.array([[cur["pr"][c] for c in cols]])
    W = None
    if cur.get("winners"):
        extra = sorted({p for p in cur["winners"].values() if p not in cur["pr"]})
        cols = cols + extra
        S = np.hstack([S, np.zeros((1, len(extra)))])
        idx = {c: i for i, c in enumerate(cols)}
        W = np.array([[idx[p] for p in cur["winners"].values()]])
    T = (np.array([cur["turnout"]]) if cur.get("turnout") is not None else None)
    f = transition_features(prev["pr"], cols, S, prev.get("turnout"), T, W)
    return {k: float(v[0]) for k, v in f.items()}


def transitions(rec: dict) -> dict:
    """``{(city, y0, y1): features}`` for every consecutive pair in ``rec``."""
    by_city = defaultdict(list)
    for (c, y) in rec:
        by_city[c].append(y)
    out = {}
    for c, ys in by_city.items():
        ys = sorted(ys, key=int)
        for y0, y1 in zip(ys, ys[1:]):
            out[(c, y0, y1)] = real_features(rec[(c, y0)], rec[(c, y1)])
    return out


def reference(trans: dict, target_year: int, mode: str = "strict",
              minimum: int | None = None) -> list[dict]:
    """The real transitions a target at ``target_year`` may be judged by.

    ``strict``: ending at or before target − 5; ``strict06``: the same without
    the transitions starting in 2000; ``loco``: every cycle but the target's
    own (design §2.2). REFUSES (ValueError) fewer than ``minimum``: an empty
    envelope is not a judgement."""
    if mode not in MODES:
        raise ValueError(f"mode {mode!r} is not one of {MODES}")
    minimum = MIN_JUDGING if minimum is None else int(minimum)
    out = []
    for (c, y0, y1), f in sorted(trans.items()):
        y1i = int(y1)
        if mode == "strict" and y1i <= target_year - 5:
            out.append(f)
        elif mode == "strict06" and y1i <= target_year - 5 and y0 != "2000":
            out.append(f)
        elif mode == "loco" and y1i != target_year:
            out.append(f)
    if len(out) < minimum:
        raise ValueError(f"target {target_year} in mode {mode} has {len(out)} "
                         f"judging transitions, under the minimum {minimum}")
    return out


def envelope(values) -> tuple[float, float, float, int]:
    """``(min, max, IQR, n)`` of the record's values for one feature."""
    v = np.asarray(values, dtype=float)
    q1, q3 = np.percentile(v, [25, 75])
    return float(v.min()), float(v.max()), float(q3 - q1), int(v.size)


def randomised_pit(draws: np.ndarray, x: float, rng) -> float:
    """P(draw < x) + U·P(draw = x): ties split uniformly (count features)."""
    d = np.asarray(draws, dtype=float)
    return float((d < x).mean() + rng.uniform() * (d == x).mean())


def poisson_binomial(ps) -> np.ndarray:
    """The distribution of a sum of independent Bernoullis, by convolution."""
    dist = np.array([1.0])
    for p in ps:
        dist = np.convolve(dist, [1.0 - float(p), float(p)])
    return dist


def event_tails(ps, observed: int) -> tuple[float, float]:
    """``(P(X ≤ obs), P(X ≥ obs))`` under the Poisson-binomial of ``ps``."""
    dist = poisson_binomial(ps)
    return float(dist[:observed + 1].sum()), float(dist[observed:].sum())


# --------------------------------------------------------------------------
# party level, by size class at the previous election
# --------------------------------------------------------------------------

def size_class(s: float) -> int:
    """The size class of a previous share: ``lo <= s < hi`` (design §1.2)."""
    for k, (lo, hi) in enumerate(SIZE_CLASSES):
        if lo <= s < hi:
            return k
    return len(SIZE_CLASSES) - 1


def party_ratios(s_prev: dict, cols: list, S: np.ndarray) -> dict:
    """Per size class at t−1: retained ratios of parties standing at both,
    threshold events (≥ 2%, 5%, 10%) for parties under ``TINY_LINE``, and
    the class mass (log of Σ s_t / Σ s_{t−1} over its standing members).
    Exits (no column) are not drawn and are not in any ratio population."""
    S = np.asarray(S, dtype=float)
    out = {k: {"log_ratio": [], "events": {2: 0, 5: 0, 10: 0}, "n": 0,
               "mass": None} for k in range(len(SIZE_CLASSES))}
    members = defaultdict(list)
    for j, c in enumerate(cols):
        s0 = s_prev.get(c, 0.0)
        if s0 <= 0:
            continue
        k = size_class(s0)
        members[k].append((j, s0))
        out[k]["log_ratio"].append(np.log(np.maximum(S[:, j], RATIO_LOG_FLOOR * s0) / s0))
        if s0 < TINY_LINE:
            for th in (2, 5, 10):
                out[k]["events"][th] += int((S[:, j] >= th / 100.0).sum())
        out[k]["n"] += 1
    for k, mem in members.items():
        idx = [j for j, _ in mem]
        prev = sum(s for _, s in mem)
        out[k]["mass"] = np.log(np.maximum(S[:, idx].sum(1), 1e-12) / prev)
    return out


def record_party_ratios(rec: dict, keys) -> dict:
    """The record's party-level reference over the transitions ``keys``
    (``(city, y0, y1)``): per size class at t−1, the log retained ratios of
    parties that stood at both elections, and the threshold events of parties
    under ``TINY_LINE`` (counts and the population)."""
    out = {k: {"log_ratio": [], "events": {2: 0, 5: 0, 10: 0}, "n_tiny": 0}
           for k in range(len(SIZE_CLASSES))}
    for (c, y0, y1) in keys:
        a, b = rec[(c, y0)]["pr"], rec[(c, y1)]["pr"]
        for p, s0 in a.items():
            if s0 <= 0 or b.get(p, 0.0) <= 0:
                continue
            k = size_class(s0)
            out[k]["log_ratio"].append(math.log(max(b[p], RATIO_LOG_FLOOR * s0) / s0))
            if s0 < TINY_LINE:
                out[k]["n_tiny"] += 1
                for th in (2, 5, 10):
                    out[k]["events"][th] += int(b[p] >= th / 100.0)
    return out


def score_parties(runs: dict, rec: dict, trans: dict, mode: str = "strict",
                  population=None) -> dict:
    """Design §3(d): per size class, the share of party-draws whose retained
    ratio falls below the record's lowest (collapse) or above its highest
    (jump), each against 1/(n+1), and the class fails when either exceeds
    ``COLLAPSE_JUMP_MULT`` times it; and the threshold events (≥ 2, 5, 10%)
    of previously tiny parties per party-draw, beside the record's rate and
    its rule-of-three / one-sided upper bound. ``runs`` maps ``(city,
    year)`` to ``(prev_shares, cols, S)``. Targets weighted equally, over
    the targets of ``population`` only (default :func:`scored_population`);
    a run outside it is not aggregated."""
    population = set(scored_population() if population is None
                     else population)
    acc = defaultdict(lambda: {"collapse": [], "jump": [], "exch": [],
                               "events": {2: [], 5: [], 10: []}})
    rec_rates = {}
    for (city, year), (s_prev, cols, S) in sorted(runs.items()):
        if (city, year) not in population:
            continue
        keys = [k for k in trans
                if (mode == "strict" and int(k[2]) <= int(year) - 5)
                or (mode == "strict06" and int(k[2]) <= int(year) - 5
                    and k[1] != "2000")
                or (mode == "loco" and int(k[2]) != int(year))]
        ref = record_party_ratios(rec, keys)
        mine = party_ratios(s_prev, cols, S)
        for k in range(len(SIZE_CLASSES)):
            lr = ref[k]["log_ratio"]
            if len(lr) < 2 or not mine[k]["log_ratio"]:
                continue
            lo, hi = min(lr), max(lr)
            x = np.concatenate(mine[k]["log_ratio"])
            acc[k]["collapse"].append(float((x < lo).mean()))
            acc[k]["jump"].append(float((x > hi).mean()))
            acc[k]["exch"].append(1.0 / (len(lr) + 1))
            per_draw = S.shape[0] * sum(1 for j, c in enumerate(cols)
                                        if 0 < s_prev.get(c, 0.0) < TINY_LINE
                                        and size_class(s_prev[c]) == k)
            if per_draw and ref[k]["n_tiny"]:
                for th in (2, 5, 10):
                    acc[k]["events"][th].append(mine[k]["events"][th] / per_draw)
                rec_rates[k] = {th: (ref[k]["events"][th], ref[k]["n_tiny"])
                                for th in (2, 5, 10)}
    out = {}
    for k, a in acc.items():
        if not a["exch"]:
            continue
        exch = float(np.mean(a["exch"]))
        ent = {"class": list(SIZE_CLASSES[k]),
               "collapse": float(np.mean(a["collapse"])),
               "jump": float(np.mean(a["jump"])), "exch": exch}
        ent["fails"] = (ent["collapse"] > COLLAPSE_JUMP_MULT * exch
                        or ent["jump"] > COLLAPSE_JUMP_MULT * exch)
        if k in rec_rates:
            ev = {}
            for th in (2, 5, 10):
                hits, n = rec_rates[k][th]
                bound = (3.0 / n) if hits == 0 else (hits + 1.645 * math.sqrt(hits)) / n
                rate = float(np.mean(a["events"][th])) if a["events"][th] else 0.0
                ev[th] = {"draws": rate, "record": hits / n, "bound": bound,
                          "fails": rate > bound}
            ent["threshold_events"] = ev
        out[str(k)] = ent
    return out


# --------------------------------------------------------------------------
# scoring a run, and a panel of runs
# --------------------------------------------------------------------------

def run_features(run: dict, prev: dict, registered: float | None) -> dict:
    """A run's features. ``run`` holds ``pr_share_draws``, ``cols``, and
    optionally ``pr_vote_draws`` and ``ward_winner_draws``. Turnout is the
    drawn valid list votes over ``registered``."""
    S = np.asarray(run["pr_share_draws"], dtype=float)
    S = S / S.sum(axis=1, keepdims=True)
    T = None
    if registered and run.get("pr_vote_draws") is not None:
        T = np.asarray(run["pr_vote_draws"], dtype=float).sum(1) / registered
    W = run.get("ward_winner_draws")
    if np.asarray(S).shape[1] != len(run["cols"]):
        raise ValueError(f"{S.shape[1]} share columns against "
                         f"{len(run['cols'])} named columns")
    return transition_features(prev["pr"], list(run["cols"]), S,
                               prev.get("turnout"), T,
                               None if W is None else np.asarray(W, dtype=int))


def joint_count(features, rows: dict, feats: dict, n_rows: int,
                has_real: bool) -> dict:
    """One joint count over ``features``: per draw, how many of them leave
    the record's range, and the same for the real election.

    ``complete`` is False when a feature of the set was not judged at this
    target (absent from the run, or too few record values), and ``missing``
    names it: the count is then over fewer features than its name says and
    the panel does not aggregate it. Counting whatever was present made an
    eight-feature count silently a seven-feature one on a run with no ward
    winners."""
    present = [ft for ft in features if ft in rows]
    J = np.zeros(n_rows)
    real_J = 0 if has_real else None
    for ft in present:
        lo, hi = rows[ft]["record"]
        x = np.asarray(feats[ft], dtype=float)
        J += (x < lo) | (x > hi)
        if has_real:
            real_J += int(rows[ft].get("real_out", False))
    real_missing = ([ft for ft in present if "real_out" not in rows[ft]]
                    if has_real else [])
    return {"features": present,
            "missing": [ft for ft in features if ft not in rows],
            "real_missing": real_missing,
            "complete": len(present) == len(features) and not real_missing,
            "p_ge2": float((J >= 2).mean()), "p_ge3": float((J >= 3).mean()),
            "real": real_J}


def score_target(feats: dict, ref: list[dict], real: dict | None,
                 rng) -> dict:
    """One target's rows: per feature the envelope rates, the probability of
    being outside, whether the real value was, and its randomised PIT; and the
    joint counts (``JOINT_SETS``) for the draws and the real election."""
    rows = {}
    for ft, x in feats.items():
        vals = [r[ft] for r in ref if ft in r]
        if len(vals) < MIN_JUDGING:
            continue
        lo, hi, iqr, n = envelope(vals)
        x = np.asarray(x, dtype=float)
        row = {"below": float((x < lo).mean()), "above": float((x > hi).mean()),
               "exch_side": 1.0 / (n + 1), "n": n,
               "beyond_iqr": float(((x < lo - OUTER_K * iqr)
                                    | (x > hi + OUTER_K * iqr)).mean()),
               "p_out": float(((x < lo) | (x > hi)).mean()),
               "p_far": float(((x < lo - OUTER_K * iqr)
                               | (x > hi + OUTER_K * iqr)).mean()),
               "quantiles": [float(np.percentile(x, q)) for q in (5, 50, 95)],
               "record": [lo, hi]}
        if real is not None and ft in real:
            v = real[ft]
            row.update(real=v, real_out=bool(v < lo or v > hi),
                       real_far=bool(v < lo - OUTER_K * iqr
                                     or v > hi + OUTER_K * iqr),
                       pit=randomised_pit(x, v, rng))
        rows[ft] = row
    n_rows = len(next(iter(feats.values())))
    for name, features in JOINT_SETS.items():
        rows[name] = joint_count(features, rows, feats, n_rows, real is not None)
    return rows


def score_panel(targets: dict, trans: dict, mode: str = "strict",
                seed: int = 20261012, population=None,
                allow_incomplete: bool = False) -> dict:
    """Aggregate per-target rows into the panel verdicts of design §3.

    ``targets`` maps ``(city, year)`` to the target's features. Every target
    gets its per-target rows; THE PANEL AGGREGATES THE TARGETS OF
    ``population`` ONLY (default :func:`scored_population`, prereg §2's 16
    city-years), and each of them must have a real result. A target outside
    it (2011, a forecast) is reported in ``per_target`` with ``scored``
    false and the reason, and enters no panel number, the mean exceedance
    rates included. REFUSES a population member with no target unless
    ``allow_incomplete`` (:func:`check_population`); the output carries the
    population block either way.

    Returns per feature the mean exceedance rates, the event test's expected
    and realised counts and both tails, the PIT counts, the fail flag of the
    §3.2 rule (cycle-driven features reported, not failed), and each joint
    count's event test over the targets where it is complete
    (``J7_no_w_top`` is what the pre-registration's U1 and U2 read;
    ``J8_with_w_top`` its U3)."""
    population = list(scored_population() if population is None
                      else population)
    pop_block = check_population(targets, population, allow_incomplete)
    rng = np.random.default_rng(seed)
    per = {}
    for (city, year), feats in sorted(targets.items()):
        ref = reference(trans, int(year), mode)
        y0 = str(int(year) - 5)
        real = trans.get((city, y0, year))
        per[(city, year)] = score_target(feats, ref, real, rng)
    out = {}
    scored = [k for k in per if k in set(population)]
    for k in scored:
        if not any("real" in r for f, r in per[k].items()
                   if f not in JOINT_SETS):
            raise SystemExit(f"{k[0]}-{k[1]} is in the scored population and "
                             f"has no real transition to be judged against")
    for ft in CITY_FEATURES:
        rows = [per[k][ft] for k in scored if ft in per[k]]
        srows = [per[k][ft] for k in scored if ft in per[k] and "real" in per[k][ft]]
        if not rows:
            continue
        ent = {"below": float(np.mean([r["below"] for r in rows])),
               "above": float(np.mean([r["above"] for r in rows])),
               "exch_side": float(np.mean([r["exch_side"] for r in rows])),
               "beyond_iqr": float(np.mean([r["beyond_iqr"] for r in rows])),
               "cycle_driven": ft in CYCLE_DRIVEN}
        if srows:
            ps = [r["p_out"] for r in srows]
            obs = sum(r["real_out"] for r in srows)
            le, ge = event_tails(ps, obs)
            pits = np.array([r["pit"] for r in srows])
            in90 = int(((pits > 0.05) & (pits < 0.95)).sum())
            ent.update(expected_out=float(sum(ps)), realised_out=int(obs),
                       p_le=le, p_ge=ge, scored=len(srows),
                       pit_in50=int(((pits > 0.25) & (pits < 0.75)).sum()),
                       pit_in90=in90, pit_lt05=int((pits < 0.05).sum()),
                       pit_gt95=int((pits > 0.95).sum()))
            ent["fails"] = (not ent["cycle_driven"]) and bool(
                le < FAIL_P or ge < FAIL_P
                or in90 < PIT90_MIN_FRACTION * len(srows))
        out[ft] = ent
    for name in JOINT_SETS:
        jr = [per[k][name] for k in scored if per[k][name]["complete"]]
        left_out = sorted(f"{c}-{y}" for (c, y) in scored
                          if not per[(c, y)][name]["complete"])
        if not jr:
            out[name] = {"scored": 0, "incomplete": left_out}
            continue
        p2 = [r["p_ge2"] for r in jr]
        obs2 = sum(1 for r in jr if r["real"] >= 2)
        out[name] = {"p_ge2_mean": float(np.mean(p2)),
                     "expected_ge2": float(sum(p2)), "realised_ge2": obs2,
                     "tails_ge2": event_tails(p2, obs2), "scored": len(jr),
                     "incomplete": left_out,
                     "features": list(JOINT_SETS[name])}
    per_target = {}
    for (c, y), v in per.items():
        v = dict(v)
        v["scored"] = (c, y) in set(population)
        if not v["scored"]:
            v["not_scored_because"] = unscored_reason(y)
        per_target[f"{c}-{y}"] = v
    return {"mode": mode, "per_target": per_target, "panel": out,
            "population": dict(pop_block, scored=sorted(f"{c}-{y}"
                                                        for c, y in scored)),
            "record_ignores_held_back": True}


# --------------------------------------------------------------------------
# reading runs and writing the verdict
# --------------------------------------------------------------------------

def load_run_dir(path: Path) -> dict:
    """A run directory's ``arrays.npz`` and ``meta.json`` (``seat_cols`` names
    the columns) as the dict ``run_features`` reads."""
    a = np.load(path / "arrays.npz")
    meta = json.loads((path / "meta.json").read_text())
    cols = meta["seat_cols"]
    cols = ast.literal_eval(cols) if isinstance(cols, str) else cols
    run = {"pr_share_draws": a["pr_share_draws"], "cols": list(cols)}
    for k in ("pr_vote_draws", "ward_winner_draws"):
        if k in a.files:
            run[k] = a[k]
    if run["pr_share_draws"].shape[0] == 0:
        raise ValueError(f"{path}: no draws")
    return run


def artefact_key(run_paths: list[Path], rec_paths: list[Path], mode: str) -> dict:
    """What produced a verdict: this module's code, every array scored, the
    record's files, the mode, and the HELD_BACK flag (design §5.2)."""
    import pools as _pl

    def sha(p):
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
    return {"plausibility_sha": _pl._code_sha(Path(__file__)),
            "arrays": {str(p): sha(p) for p in sorted(run_paths)},
            "record": {str(p): sha(p) for p in sorted(rec_paths)},
            "mode": mode, "record_ignores_held_back": True}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--runs", type=Path, required=True,
                    help="an arm root holding <city>-<year>/arrays.npz")
    ap.add_argument("--mode", default="strict", choices=MODES)
    ap.add_argument("--label", required=True)
    # REQUIRED, and refused under `data/`: the verdict is not a model artefact
    # and the processed tree has one writer (CLAUDE.md §3; step-7 review 8).
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--allow-incomplete", action="store_true",
                    help="score a panel missing some of prereg §2's city-years "
                         "(the output says so)")
    a = ap.parse_args(argv)
    out_root = a.out.resolve()
    data = (REPO / "data").resolve()
    if out_root == data or data in out_root.parents:
        raise SystemExit(f"--out {out_root} is inside {data}: the verdict is "
                         f"written outside data/")
    rec = record()
    trans = transitions(rec)
    targets, run_paths, party_runs = {}, [], {}
    for d in sorted(p for p in a.runs.iterdir() if (p / "arrays.npz").exists()):
        city, year = d.name.rsplit("-", 1)
        prev = rec.get((city, str(int(year) - 5)))
        if prev is None:
            continue
        cur = rec.get((city, year))
        reg = cur["registered"] if cur else None
        run = load_run_dir(d)
        targets[(city, year)] = run_features(run, prev, reg)
        S = np.asarray(run["pr_share_draws"], dtype=float)
        party_runs[(city, year)] = (prev["pr"], run["cols"],
                                    S / S.sum(axis=1, keepdims=True))
        run_paths.append(d / "arrays.npz")
    res = score_panel(targets, trans, a.mode,
                      allow_incomplete=a.allow_incomplete)
    res["parties"] = score_parties(party_runs, rec, trans, a.mode)
    res["artefact_key"] = artefact_key(run_paths,
                                       [Path(e["path"]) for e in rec.values()],
                                       a.mode)
    res["generated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out_root.mkdir(parents=True, exist_ok=True)
    out = out_root / f"plausibility_{a.label}.json"
    out.write_text(json.dumps(res, indent=1, sort_keys=True, default=str))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
