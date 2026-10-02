"""The "play with the model" page's Python entry: the published draws, re-weighted.

The page (``js/model-worker.js``, a Web Worker, under Pyodide) and the native
harness (``tools/native_play.py``, under the project's CPython) both run this
file, with the served copy of the page code (``interactive/py/page/``, written
by ``tools/sync_py.mjs`` from ``src/``) on ``sys.path`` and as the working
directory. Every figure comes from ``src/reweight.py``, and every ward is drawn
by ``src/render_map.py``'s ``ward_call``; this file only routes a reader's
settings to them and collects what they return. There is no arithmetic of the
model's here, and none in JavaScript.

Two calls:

    load_cell(path, manifest_json, blob)   one lever-grid cell, from the served
                                           manifest.json and base.bin
    compute(settings_json) -> json         every figure the page shows for one
                                           setting of the controls

The settings (``js/play-state.js`` holds the page's copy and its bounds)::

    {"cell": ".", "law": "deduct", "shift": [pp, pp, pp, pp],
     "polls": ["<poll id>"], "trust": 0..1}

``shift`` is in turnout POINTS per pool, in the manifest's pool order.
``polls`` holds at most ONE poll (owner, 2026-10-02: one poll at a time); a
setting naming more is refused.

What ``compute`` returns beside the seat figures: the share of simulations in
which each party alone has the most seats and in which two or more tie
(``reweight.largest_party``, the definition /forecast uses), the share in which
one party reaches a majority alone, each group's turnout, and every ward drawn
by ``render_map.ward_call`` with the wards whose most likely winner differs
from the published forecast's. Every "against the published forecast" figure
is the published cell, each draw counted once, under the seat law the
forecast publishes (``PUBLISHED_LAW``).
"""

from __future__ import annotations

import json
import math

import numpy as np

import cityconfig
import polling
import render_map as RM
import reweight as R

#: The cell the published forecast was drawn in (``site/draws/index.json``'s
#: entry with no overrides). Its pool-turnout means are the published means.
BASE = "."
#: The seat law the published forecast uses: every "against the published
#: forecast" figure is taken under it.
PUBLISHED_LAW = "deduct"
#: A party gets its own seat row when its middle seat count is at least this,
#: in the published forecast or under the reader's settings; every other party
#: is summed into "Others" (owner, decision D1, 2026-10-02).
MIN_SHOWN_SEATS = 2
#: The quantiles the seat rows show for each party: its range ends and middle.
SHOWN_QUANTILES = {"p5": 0.05, "median": 0.5, "p95": 0.95}
#: The row of every party below MIN_SHOWN_SEATS, summed within each draw.
OTHERS = "OTHERS"

_CELLS: dict[str, dict] = {}
_POLLS: list[dict] | None = None
_PUBLISHED: dict | None = None


# ==========================================================================
# THE PAGE'S CALLS INTO src/reweight.py. Thin by design: every rule lives in
# reweight.py (one definition); these only fix the page's target and shape.
# ==========================================================================

def _target():
    cityconfig.use("joburg")
    return cityconfig.use_target("2026")


def set_polls(records_json: str) -> int:
    """The poll set, as ``site/draws/index.json`` carries it.

    ``reweight.page_polls`` selects it at BUILD time (``export_draws --index``):
    the selection reads ``montecarlo.DEFAULTS``, and importing the model into
    the browser to read one default would ship its whole closure. The records
    arrive with ``asof`` stamped, which ``poll_weights(trust>0)`` requires.
    """
    global _POLLS
    _POLLS = json.loads(records_json)
    return len(_POLLS)


def poll_weights(shares, columns, poll: dict, trust: float) -> np.ndarray:
    """The chosen poll's ``reweight.poll_weights(trust=...)``, normalised.

    One poll at a time (owner, 2026-10-02), so two waves of one house are never
    multiplied as if they were independent readings. At trust 0 the weights
    are uniform.
    """
    w = R.poll_weights(shares, columns, poll, trust=trust)
    return w / w.sum()


def turnout_tilt(turnouts, shift, *, base, pin_to) -> np.ndarray:
    """``reweight.turnout_tilt(..., pin_to=)``: targets are ``pin_to + shift``,
    ``pin_to`` the PUBLISHED cell's mean turnout per pool (F4, F10)."""
    return R.turnout_tilt(turnouts, shift, base=base, pin_to=pin_to)


def figure(values, weights, q: float, *, poll: bool) -> dict:
    """``reweight.figure``, which withholds a figure above MAX_FIGURE_SE_SEATS."""
    return R.figure(values, weights, q, poll=poll)


def model_version(manifest: dict) -> str:
    """The model-only code hash (Lane E), the page's ``model_version``."""
    return str(manifest["artefact_key"]["model_sha256"])


def load_cell(path: str, manifest_json: str, blob) -> dict:
    """Unpack one cell (``reweight.unpack`` refuses a file its manifest does not describe)."""
    manifest = json.loads(manifest_json)
    # under Pyodide the bytes arrive as a JsProxy of a Uint8Array
    blob = blob.to_bytes() if hasattr(blob, "to_bytes") else bytes(blob)
    arrays = R.unpack(blob, manifest)
    _CELLS[path] = {"manifest": manifest, "arrays": arrays}
    return {"path": path, "draws": int(manifest["draws"]),
            "laws": manifest["laws"], "model_version": model_version(manifest)}


def polls() -> list[dict]:
    """The page's poll rows: the register's own fields, as the register holds them."""
    if _POLLS is None:
        raise R.Refused("no poll set: call set_polls with index.json's polls first")
    keep = ("id", "label", "pollster", "house", "fieldwork", "fieldwork_end",
            "n", "caveat", "numbers", "url")
    return [{k: p.get(k) for k in keep} for p in _POLLS]


def _pools(manifest: dict) -> list[str]:
    return next(b for b in manifest["blocks"] if b["name"] == "pool_turnout")["columns"]


def _block(cell: dict, name: str) -> tuple[np.ndarray, list[str]]:
    cols = next(b for b in cell["manifest"]["blocks"] if b["name"] == name)["columns"]
    return cell["arrays"][name], cols


def _party_columns(cell: dict, law: str) -> tuple[np.ndarray, list[str]]:
    """The seat block's PARTY columns: ``OTHER`` (the export's remainder) is not a party."""
    block, cols = _block(cell, f"seats/{law}")
    keep = [j for j, c in enumerate(cols) if c != "OTHER"]
    return block[:, keep].astype(float), [cols[j] for j in keep]


def _weights(cell: dict, settings: dict) -> tuple[np.ndarray, dict]:
    """The weights for one setting, and what they are; raises ``Refused``."""
    a = cell["arrays"]
    pr = next(b for b in cell["manifest"]["blocks"] if b["name"] == "pr_share")["columns"]
    trust = float(settings.get("trust", 0.0))
    ids = list(dict.fromkeys(settings.get("polls") or []))
    if len(ids) > 1:
        raise R.Refused("one poll at a time: this setting names more than one")
    polls()
    on = [p for p in _POLLS if p["id"] in ids]
    info = {"poll": None, "turnout_pinned": False}
    base = None
    if trust > 0 and on:
        poll = on[0]
        base = poll_weights(a["pr_share"], pr, poll, trust)
        info["poll"] = {"id": poll["id"], "label": R.POLL_LABEL, "trust": trust,
                        "sd": {k: R.poll_trust_sd(poll, v, trust)
                               for k, v in poll["numbers"].items()}}
    shift = np.asarray(settings.get("shift") or [0, 0, 0, 0], dtype=float) / 100.0
    if base is None and not np.any(shift):
        return R.uniform(a["pool_turnout"].shape[0]), info
    pin = _CELLS[BASE]["arrays"]["pool_turnout"].mean(axis=0)
    info["turnout_pinned"] = base is not None and not np.any(shift)
    w = turnout_tilt(a["pool_turnout"], shift, base=base, pin_to=pin)
    return w, info


def _ward_calls(cell: dict, w: np.ndarray) -> list[dict]:
    """Every ward under ``w``, drawn by ``render_map.ward_call`` (the forecast map's rule).

    ``dist`` is built as ``ward_winner_probs.csv`` carries it: each party that
    wins the ward in any draw with weight, strongest first, at its
    ``reweight.ward_win_probability``. ``bands`` is ``render_map.toss_bands``
    of the call's contenders: the stripe geometry the page draws as DOM.
    """
    winners, wards = _block(cell, "ward_winner")
    codes = cell["manifest"]["ward_parties"]
    probs = R.ward_win_probability(winners, w, len(codes))
    out = []
    for j, ward in enumerate(wards):
        hit = np.bincount(winners[:, j], weights=w, minlength=len(codes)) > 0
        order = [int(k) for k in np.argsort(-probs[j], kind="stable") if hit[k]]
        dist = "|".join(f"{codes[k]}:{probs[j, k]:.4f}" for k in order)
        call = RM.ward_call(ward, codes[order[0]], float(probs[j, order[0]]), dist)
        out.append({"ward": ward, "winner": codes[order[0]], "fill": call["fill"],
                    "bands": RM.toss_bands(call["bands"]) if call["cls"] == "contested" else None,
                    "tip": call["tip"]})
    return out


def _published() -> dict:
    """The published forecast's figures this page compares against: the BASE
    cell, every draw counted once, under PUBLISHED_LAW. Computed once."""
    global _PUBLISHED
    if _PUBLISHED is None:
        cell = _CELLS[BASE]
        w = R.uniform(int(cell["manifest"]["draws"]))
        seats, cols = _party_columns(cell, PUBLISHED_LAW)
        council = cell["arrays"][f"council/{PUBLISHED_LAW}"]
        lp = R.largest_party(seats, cols, w)
        _PUBLISHED = {
            "median": {c: R.weighted_quantile(seats[:, j], w, 0.5) for j, c in enumerate(cols)},
            "largest": lp["outright"], "tied": lp["tied"],
            "alone": R.majority_alone(seats, council[:, 0], w),
            "turnout": dict(zip(_pools(cell["manifest"]),
                                cell["arrays"]["pool_turnout"].mean(axis=0).tolist())),
            "winner": {x["ward"]: x["winner"] for x in _ward_calls(cell, w)},
        }
    return _PUBLISHED


def _points(x: float) -> int:
    """A share as the whole percentage point the page compares (shares are fractions)."""
    return int(round(100.0 * x))


def _seats(cell: dict, law: str, w: np.ndarray, poll: bool) -> tuple[dict, list, bool, int]:
    """Median and 90% range of each party the page shows, and of "Others", under ``w``.

    The rows (owner, D1, 2026-10-02): every party whose middle seat count is at
    least MIN_SHOWN_SEATS in the published forecast or under these weights, or
    whose middle is withheld (a withheld row is shown as withheld rather than
    dropped). Every other party's seats are summed WITHIN each draw into
    ``OTHERS`` (``scenarios.others_per_draw``'s rule: never a sum of
    quantiles); the count of those parties that win a seat in any draw is
    returned too. ``vs_published`` is the middle seat count, rounded, less the
    published one, rounded.

    Also returns whether every figure shown passes the precision rule
    (``reweight.within_precision``, DESIGN-decided §15): the page stops a
    control at the last setting for which this was true. Deciding here which
    rows are shown keeps the rule and the rows it covers in one place.
    """
    block, cols = _party_columns(cell, law)
    pub = _published()["median"]
    out, values, rest = {}, {}, []
    for j, party in enumerate(cols):
        v = block[:, j]
        if not v.max() > 0:
            continue
        med = figure(v, w, 0.5, poll=poll)
        if med["withheld"] or med["value"] >= MIN_SHOWN_SEATS or pub.get(party, 0.0) >= MIN_SHOWN_SEATS:
            values[party] = v
        else:
            rest.append(j)
    others = block[:, rest].sum(axis=1) if rest else np.zeros(block.shape[0])
    rows = [*values.items(), (OTHERS, others)]
    for party, v in rows:
        out[party] = {k: figure(v, w, q, poll=poll) for k, q in SHOWN_QUANTILES.items()}
        out[party]["median_se"] = out[party]["median"]["sampling_se"]
        m, b = out[party]["median"], pub.get(party)
        out[party]["vs_published"] = (None if m["withheld"] or b is None
                                      else int(round(m["value"])) - int(round(b)))
    precise = R.within_precision(
        {f"{p}.{k}": (v, q) for p, v in rows for k, q in SHOWN_QUANTILES.items()}, w)
    return out, list(values), precise, len(rest)


def _outcomes(cell: dict, law: str, w: np.ndarray) -> dict:
    """Largest party (ties apart), a majority alone, turnout and the wards, each
    with the change from the published forecast where the page shows one."""
    pub = _published()
    seats, cols = _party_columns(cell, law)
    council = cell["arrays"][f"council/{law}"]
    lp = R.largest_party(seats, cols, w)
    largest = {c: {"p": p, "vs_published": _points(p) - _points(pub["largest"].get(c, 0.0))}
               for c, p in lp["outright"].items() if p > 0 or pub["largest"].get(c, 0.0) > 0}
    share = w / w.sum()
    turnout = {g: {"mean": float(t), "published": pub["turnout"][g]}
               for g, t in zip(_pools(cell["manifest"]), share @ cell["arrays"]["pool_turnout"])}
    wards = _ward_calls(cell, w)
    flips = [{"ward": x["ward"], "from": pub["winner"][x["ward"]], "to": x["winner"]}
             for x in wards if x["winner"] != pub["winner"].get(x["ward"], x["winner"])]
    return {"largest": largest,
            "tied": {"p": lp["tied"], "vs_published": _points(lp["tied"]) - _points(pub["tied"])},
            "alone": {"p": R.majority_alone(seats, council[:, 0], w),
                      "vs_published": None},
            "turnout": turnout, "wards": wards, "flips": flips}


def _one(path: str, settings: dict) -> dict:
    cell = _CELLS[path]
    law = settings.get("law", "deduct")
    if law not in cell["manifest"]["laws"]:
        raise ValueError(f"no seat law {law!r} in this export")
    try:
        w, info = _weights(cell, settings)
        ess = R.require_effective(w)
    except R.Refused as exc:
        return {"cell": path, "refused": str(exc)}
    council = cell["arrays"][f"council/{law}"]
    seats, shown, precise, others_count = _seats(cell, law, w, info["poll"] is not None)
    centres = cell["manifest"].get("centres") or {}
    out = {"cell": path, "law": law, "refused": None,
           "draws": int(cell["manifest"]["draws"]), "effective_draws": ess,
           "seats": seats, "shown": shown, "others_count": others_count,
           "within_precision": precise,
           "max_figure_se": R.MAX_FIGURE_SE_SEATS,
           "majority": R.weighted_quantile(council[:, 0], w, 0.5),
           "council": R.weighted_quantile(council[:, 1], w, 0.5),
           **_outcomes(cell, law, w),
           # the model's deterministic LEVELS (run_model's centres after the
           # shrink), not shares: they do not sum to one, and the page compares
           # them only cell against cell (review F20, DESIGN-decided §11)
           "centres": centres.get("values"),
           "centres_source": centres.get("source"),
           "model_version": model_version(cell["manifest"]), **info}
    return out


def compute(settings_json: str) -> str:
    """Every figure for one setting of the controls, as JSON.

    When the chosen cell is not the published one, the same settings are also
    computed on the published cell, and each party's median difference is
    reported against the noise rule of F2 (``reweight.beyond_noise``): two
    unpaired cells differ by sampling alone unless the difference is at least
    ``2 * sqrt(se_a**2 + se_b**2)``.
    """
    s = json.loads(settings_json)
    path = s.get("cell", BASE)
    if path not in _CELLS:
        raise ValueError(f"cell {path!r} is not loaded")
    out = _one(path, s)
    if path != BASE and out["refused"] is None:
        ref = _one(BASE, s)
        out["published_cell"] = {"centres": ref.get("centres"),
                                 "refused": ref["refused"]}
        if ref["refused"] is None:
            cmp = {}
            for party in sorted((set(out["seats"]) | set(ref["seats"])) - {OTHERS}):
                a = out["seats"].get(party)
                b = ref["seats"].get(party)
                if (a and a["median"]["withheld"]) or (b and b["median"]["withheld"]):
                    continue
                cmp[party] = R.beyond_noise(a["median"]["value"] if a else 0.0,
                                            a["median_se"] if a else 0.0,
                                            b["median"]["value"] if b else 0.0,
                                            b["median_se"] if b else 0.0)
            out["against_published_cell"] = cmp
    return json.dumps(_plain(out), allow_nan=False)


def _plain(o):
    """JSON-safe: numpy scalars as Python ones; NaN and infinity as None."""
    if isinstance(o, dict):
        return {str(k): _plain(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_plain(v) for v in o]
    if isinstance(o, np.ndarray):
        return _plain(o.tolist())
    if isinstance(o, (np.floating, np.integer, np.bool_)):
        o = o.item()
    if isinstance(o, float) and not math.isfinite(o):
        return None
    return o


def pools_of(path: str = BASE) -> list[str]:
    """The pool names, in the order ``shift`` is read."""
    return _pools(_CELLS[path]["manifest"])
