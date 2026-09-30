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


def poll_weights(shares, columns, polls_on: list[dict], trust: float) -> np.ndarray:
    """Each switched-on poll's ``reweight.poll_weights(trust=...)``, multiplied.

    Multiplying treats the polls as independent; two waves of one house are
    not, and JUDGEMENT-CALLS §N2 says so. At trust 0 every factor is uniform.
    """
    w = R.uniform(len(shares))
    for poll in polls_on:
        w = w * R.poll_weights(shares, columns, poll, trust=trust)
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
        average, spread = R.combine_polls(on)
        base = poll_weights(a["pr_share"], pr, on, trust)
        info["poll"] = {"average": average, "spread": spread,
                        "label": R.POLL_LABEL, "trust": trust,
                        "sd": {p["id"]: {k: R.poll_trust_sd(p, s, trust)
                                         for k, s in p["numbers"].items()}
                               for p in on}}
    shift = np.asarray(settings.get("shift") or [0, 0, 0, 0], dtype=float) / 100.0
    if base is None and not np.any(shift):
        return R.uniform(a["pool_turnout"].shape[0]), info
    pin = _CELLS[BASE]["arrays"]["pool_turnout"].mean(axis=0)
    info["turnout_pinned"] = base is not None and not np.any(shift)
    w = turnout_tilt(a["pool_turnout"], shift, base=base, pin_to=pin)
    return w, info


#: The quantiles the seat table shows for each party: its range ends and middle.
SHOWN_QUANTILES = {"p5": 0.05, "median": 0.5, "p95": 0.95}


def _seats(cell: dict, law: str, w: np.ndarray, poll: bool) -> tuple[dict, list, bool]:
    """Median and 90% range of every party that wins a seat in any draw, under ``w``.

    Also returns the parties the page SHOWS (a middle or an upper end above
    zero, or a figure withheld, so a withheld row is shown as withheld rather
    than dropped) and whether every figure it shows passes the precision rule
    (``reweight.within_precision``, DESIGN-decided §15): the page stops a
    control at the last setting for which this was true. Deciding here which
    rows are shown keeps the rule and the rows it covers in one place.
    """
    block = cell["arrays"][f"seats/{law}"]
    cols = next(b for b in cell["manifest"]["blocks"]
                if b["name"] == f"seats/{law}")["columns"]
    out, values = {}, {}
    for j, party in enumerate(cols):
        v = block[:, j].astype(float)
        if party == "OTHER" or not v.max() > 0:
            continue
        values[party] = v
        out[party] = {k: figure(v, w, q, poll=poll) for k, q in SHOWN_QUANTILES.items()}
        out[party]["median_se"] = out[party]["median"]["sampling_se"]
    shown = [p for p, f in out.items()
             if any(f[k]["withheld"] for k in SHOWN_QUANTILES)
             or f["median"]["value"] > 0 or f["p95"]["value"] > 0]
    precise = R.within_precision(
        {f"{p}.{k}": (values[p], q) for p in shown for k, q in SHOWN_QUANTILES.items()}, w)
    return out, shown, precise


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
    seats, shown, precise = _seats(cell, law, w, info["poll"] is not None)
    centres = cell["manifest"].get("centres") or {}
    out = {"cell": path, "law": law, "refused": None,
           "draws": int(cell["manifest"]["draws"]), "effective_draws": ess,
           "seats": seats, "shown": shown, "within_precision": precise,
           "max_figure_se": R.MAX_FIGURE_SE_SEATS,
           "majority": R.weighted_quantile(council[:, 0], w, 0.5),
           "council": R.weighted_quantile(council[:, 1], w, 0.5),
           # the model's deterministic LEVELS (run_model's centres after the
           # shrink), not shares: they do not sum to one, and the page compares
           # them only cell against cell (review F20, DESIGN-decided §11)
           "centres": centres.get("values"),
           "centres_source": centres.get("source"),
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
