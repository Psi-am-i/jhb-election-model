"""The "play with the model" page's Python entry: the published draws, re-weighted.

The page (``js/model-worker.js``, a Web Worker, under Pyodide) and the native
harness (``tools/native_play.py``, under the project's CPython) both run this
file, with the served copy of the page code (``interactive/py/page/``, written
by ``tools/sync_py.mjs`` from ``src/``) on ``sys.path`` and as the working
directory. Every figure comes from ``src/reweight.py``; this file only routes a
reader's settings to it and collects what it returns. There is no arithmetic of
the model's here, and none in JavaScript.

Two calls:

    load_cell(path, manifest_json, blob)   one lever-grid cell, from the served
                                           manifest.json and base.bin
    compute(settings_json) -> json         every figure the page shows for one
                                           setting of the controls

The settings (``js/play-state.js`` holds the page's copy and its bounds)::

    {"cell": ".", "law": "deduct", "shift": [pp, pp, pp, pp],
     "polls": ["<poll id>", ...], "trust": 0..1}

``shift`` is in turnout POINTS per pool, in the manifest's pool order.
"""

from __future__ import annotations

import inspect
import json
import math

import numpy as np

import cityconfig
import polling
import reweight as R

#: The cell the published forecast was drawn in (``site/draws/index.json``'s
#: entry with no overrides). Its pool-turnout means are the published means.
BASE = "."

_CELLS: dict[str, dict] = {}
_POLLS: list[dict] | None = None


# ==========================================================================
# ADAPTER — REMOVE AT MERGE.
#
# Lane R (SPEC-v2) adds these to src/reweight.py. Each is called here through
# `getattr(R, name, None)`: once Lane R merges, the real function is used and
# the fallback below it is dead code, to be deleted with this block. Nothing
# outside this block calls a fallback directly.
# ==========================================================================

def _target():
    cityconfig.use("joburg")
    return cityconfig.use_target("2026")


def page_polls() -> list[dict]:
    """The poll set the page offers: ``reweight.page_polls(target)``.

    Fallback: ``polling.metro_polls``, which is ``polling.screen`` filtered to
    readings of this city, the source SPEC-v2 names (F8).
    """
    fn = getattr(R, "page_polls", None)
    t = _target()
    return list(fn(t)) if fn else polling.metro_polls(t)


def poll_trust_sd(poll: dict, share: float, trust: float) -> float:
    """``reweight.poll_trust_sd``: decision 2, ``sd = poll_sd / trust``.

    Fallback: that mapping, with ``polling.poll_sd`` at its defaults.
    """
    fn = getattr(R, "poll_trust_sd", None)
    if fn:
        return float(fn(poll, share, trust))
    trust = float(trust)
    if not 0.0 <= trust <= 1.0:
        raise R.Refused(f"trust must lie in [0, 1], not {trust}")
    if trust == 0.0:
        return math.inf
    return polling.poll_sd(poll, share) / trust


def poll_weights(shares, columns, average: dict, polls_on: list[dict],
                 trust: float) -> np.ndarray:
    """``reweight.poll_weights(..., trust=...)``.

    Fallback: one ``sd`` for the combined poll, the root mean square over the
    switched-on polls and the polled parties of :func:`poll_trust_sd` at the
    combined share. An approximation standing in for Lane R's rule, which
    replaces it.
    """
    fn = R.poll_weights
    if "trust" in inspect.signature(fn).parameters:
        return fn(shares, columns, average, trust=trust, polls=polls_on)
    if trust == 0.0:
        return fn(shares, columns, average, sd=math.inf)
    sds = [poll_trust_sd(p, average[k], trust) for p in polls_on for k in average]
    return fn(shares, columns, average, sd=math.sqrt(np.mean(np.square(sds))))


def turnout_tilt(turnouts, shift, *, base, pin_to) -> np.ndarray:
    """``reweight.turnout_tilt(..., pin_to=)``: targets are ``pin_to + shift``.

    ``pin_to`` is the PUBLISHED cell's mean turnout per pool (F4, F10), so a
    reader's "+5" means five points on the published turnout in every cell.
    Fallback: the same targets through ``reweight._tilt``, which
    ``turnout_tilt`` itself calls.
    """
    fn = R.turnout_tilt
    if "pin_to" in inspect.signature(fn).parameters:
        return fn(turnouts, shift, base=base, pin_to=pin_to)
    return R._tilt(np.asarray(turnouts, dtype=float),
                   np.asarray(pin_to, dtype=float) + np.asarray(shift, dtype=float),
                   base=base, tolerance=1e-10, steps=200)


def figure(values, weights, q: float, *, poll: bool) -> dict:
    """``reweight.figure``, with Lane R's ``withheld`` (F17).

    Fallback for ``withheld``: the tail effective draws under
    ``MIN_EFFECTIVE_DRAWS``, the rule SPEC-v2 states.
    """
    out = R.figure(values, weights, q, poll=poll)
    if "withheld" not in out:
        out["withheld"] = bool(out["tail_effective_draws"] < R.MIN_EFFECTIVE_DRAWS)
    return out


def sampling_se(values, weights, q: float) -> float:
    """``reweight.sampling_se``: the standard error of a weighted quantile (F2).

    Fallback: the quantile's level error from
    ``reweight.quantile_effective_draws``, carried through the weighted
    quantile function: (Q(q + se) - Q(q - se)) / 2.
    """
    fn = getattr(R, "sampling_se", None)
    if fn:
        return float(fn(values, weights, q))
    _, level = R.quantile_effective_draws(values, weights, q)
    if not math.isfinite(level):
        return 0.0
    lo = R.weighted_quantile(values, weights, max(q - level, 0.0))
    hi = R.weighted_quantile(values, weights, min(q + level, 1.0))
    return (hi - lo) / 2.0


def model_version(manifest: dict) -> str:
    """Lane E's ``model_sha256``; fallback, the draws' ``code_sha256``."""
    return str(manifest.get("model_sha256")
               or manifest["artefact_key"]["code_sha256"])

# ==========================================================================
# END ADAPTER
# ==========================================================================


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
    global _POLLS
    if _POLLS is None:
        _POLLS = page_polls()
    keep = ("id", "label", "pollster", "house", "fieldwork", "fieldwork_end",
            "n", "caveat", "numbers", "url")
    return [{k: p.get(k) for k in keep} for p in _POLLS]


def _pools(manifest: dict) -> list[str]:
    return next(b for b in manifest["blocks"] if b["name"] == "pool_turnout")["columns"]


def _weights(cell: dict, settings: dict) -> tuple[np.ndarray, dict]:
    """The weights for one setting, and what they are; raises ``Refused``."""
    a = cell["arrays"]
    pr = next(b for b in cell["manifest"]["blocks"] if b["name"] == "pr_share")["columns"]
    trust = float(settings.get("trust", 0.0))
    ids = set(settings.get("polls") or [])
    polls()
    on = [p for p in _POLLS if p["id"] in ids]
    info = {"poll": None, "turnout_pinned": False}
    base = None
    if trust > 0 and on:
        average, spread = R.combine_polls([p["numbers"] for p in on])
        base = poll_weights(a["pr_share"], pr, average, on, trust)
        info["poll"] = {"average": average, "spread": spread,
                        "label": R.POLL_LABEL, "trust": trust,
                        "sd": {k: [poll_trust_sd(p, average[k], trust) for p in on]
                               for k in average}}
    shift = np.asarray(settings.get("shift") or [0, 0, 0, 0], dtype=float) / 100.0
    if base is None and not np.any(shift):
        return R.uniform(a["pool_turnout"].shape[0]), info
    pin = _CELLS[BASE]["arrays"]["pool_turnout"].mean(axis=0)
    info["turnout_pinned"] = base is not None and not np.any(shift)
    w = turnout_tilt(a["pool_turnout"], shift, base=base, pin_to=pin)
    return w, info


def _seats(cell: dict, law: str, w: np.ndarray, poll: bool) -> dict:
    """Median and 90% range of every party that wins a seat in any draw, under ``w``."""
    block = cell["arrays"][f"seats/{law}"]
    cols = next(b for b in cell["manifest"]["blocks"]
                if b["name"] == f"seats/{law}")["columns"]
    out = {}
    for j, party in enumerate(cols):
        v = block[:, j].astype(float)
        if party == "OTHER" or not v.max() > 0:
            continue
        out[party] = {
            "p5": figure(v, w, 0.05, poll=poll),
            "median": figure(v, w, 0.5, poll=poll),
            "p95": figure(v, w, 0.95, poll=poll),
            "median_se": sampling_se(v, w, 0.5),
        }
    return out


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
    out = {"cell": path, "law": law, "refused": None,
           "draws": int(cell["manifest"]["draws"]), "effective_draws": ess,
           "seats": _seats(cell, law, w, info["poll"] is not None),
           "majority": R.weighted_quantile(council[:, 0], w, 0.5),
           "council": R.weighted_quantile(council[:, 1], w, 0.5),
           "centres": cell["manifest"].get("centres"),
           "model_version": model_version(cell["manifest"]), **info}
    if "combined_share" in cell["arrays"]:
        cols = next(b for b in cell["manifest"]["blocks"]
                    if b["name"] == "combined_share")["columns"]
        p = w / w.sum()
        out["combined_share"] = dict(zip(cols, (p @ cell["arrays"]["combined_share"]).tolist()))
    else:
        out["combined_share"] = None
    return out


def compute(settings_json: str) -> str:
    """Every figure for one setting of the controls, as JSON.

    When the chosen cell is not the published one, the same settings are also
    computed on the published cell, and each party's median difference is
    reported against the noise rule of F2: two unpaired cells differ by
    sampling alone unless the difference is at least
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
            for party in sorted(set(out["seats"]) | set(ref["seats"])):
                a = out["seats"].get(party)
                b = ref["seats"].get(party)
                ma = a["median"]["value"] if a else 0.0
                mb = b["median"]["value"] if b else 0.0
                sa = a["median_se"] if a else 0.0
                sb = b["median_se"] if b else 0.0
                noise = 2.0 * math.sqrt(sa * sa + sb * sb)
                cmp[party] = {"difference": ma - mb, "noise": noise,
                              "within_noise": abs(ma - mb) < noise}
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
