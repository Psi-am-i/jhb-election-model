"""Re-weight the published draws: the interactive's engine, and the draw file's format.

The interactive's "play with the model" controls do not re-run the model. The
published run's draws already vary in the quantities those controls move (each
draw's four pool turnouts, each draw's PR shares), so a control is a WEIGHT on
each draw, and every figure the page shows is a weighted statistic of the same
draws (``audits/2026-09-28-interactive-architecture/PLAN.md`` §§2-5, build step
S4). This module is that arithmetic, and it is the ONE definition of it: the
browser runs this file under Pyodide, copied byte for byte, never a
translation (INTEGRATION.md §3b). So it is pure Python plus numpy: no file
access, no scipy, no import from the rest of ``src/``.

It also defines the draw file's binary layout (:func:`pack`, :func:`unpack`),
because the reader is the browser and a format with a writer in one file and a
reader in another is two definitions. ``src/export_draws.py`` writes through
:func:`pack`.

What it offers, and the one rule over all of it
===============================================

**Every party is treated identically** (``audits/2026-09-27-interactive-levers/
DESIGN-decided.md`` §8). Nothing below names a party, and no argument exists
for one party that does not exist for all.

* :func:`turnout_tilt` — the turnout control. A target for ALL FOUR pools at
  once; PLAN.md finding 3 measured why a single-pool tilt is the wrong control.
* :func:`poll_weights` — a poll as a likelihood on each draw, with a trust
  setting in which 0 is uniform weights EXACTLY (DESIGN-decided §3).
* :func:`combine_polls` — the average of the polls a reader switches on, and
  the spread between them, which is shown and never hidden (DESIGN-decided §2).
* :func:`effective_draws` and :func:`require_effective` — Kish's effective
  sample, and the refusal below :data:`MIN_EFFECTIVE_DRAWS`.
* :func:`weighted_quantile`, :func:`weighted_probability`,
  :func:`ward_win_probability`, :func:`weighted_mean_se` — the statistics the
  page reports, each reducing EXACTLY to the published figure's own formula
  when the weights are uniform, so the untouched page is the published forecast
  (``tests/test_reweight.py`` checks this bitwise against the published files).

What re-weighting cannot do
===========================

It cannot leave the record. A weighted statistic is an average over draws the
model made, so a target outside what the draws span has no answer — the tilt
refuses (:class:`Refused`) rather than extrapolate — and a target near the edge
has an answer resting on few draws, which is what the effective-draw count and
the refusal floor exist to say. It also cannot stand in for a control that
changes HOW the model draws (within-pool movement, the by-election weight):
those need the grid of full runs in PLAN.md §6.

The turnout tilt MATCHES A MEAN; moving turnout in the model moves the whole
distribution. They are different operations. The claim that the first stands in
for the second at the size of move the page offers is a measurement, not an
identity: ``tests/test_reweight.py`` compares the tilt with a paired re-run of
the model, pre-registered in ``prereg/2026-09-28-reweight-against-paired-rerun.md``.
"""

from __future__ import annotations

import numpy as np

#: The fewest effective draws a re-weighted figure may rest on. Below it the
#: page greys the control out rather than show a number (PLAN.md build step
#: S4). A judgement call, not a measurement: JUDGEMENT-CALLS.md carries the
#: row, its evidence and how to check it.
MIN_EFFECTIVE_DRAWS = 200

#: The draw file's format identifier. :func:`unpack` refuses any other, so a
#: page cannot silently read a file laid out by a different version of
#: :func:`pack`.
FORMAT = "draws-columnar-v1"


class Refused(ValueError):
    """A control the draws cannot answer. The page shows the reason, never a number."""


# ==========================================================================
# the draw file: one definition of its layout, both directions
# ==========================================================================

def pack(blocks: list[tuple]) -> tuple[bytes, list[dict]]:
    """Lay out named blocks, COLUMN-MAJOR, as one byte string.

    Each block is ``(name, array, columns)`` or ``(name, array, columns,
    step)``, with ``array`` shaped ``(draws, len(columns))``. It is stored
    transposed — one column's draws contiguous — because a column of one
    party's seats is a run of small, repetitive integers, and that is what
    compresses. Little-endian, whatever the writing machine.

    ``step`` stores a real-valued block as integer multiples of ``step``, in
    16 bits where the largest value fits and 32 where it does not (rounded to
    nearest, so the error is at most ``step / 2``);
    :func:`unpack` multiplies back. The block table records it, so the loss is
    declared in the file rather than known only to the writer.

    Returns the bytes and the block table the manifest carries; :func:`unpack`
    needs both.
    """
    out = bytearray()
    table = []
    draws = None
    for name, array, columns, *rest in blocks:
        step = rest[0] if rest else None
        array = np.asarray(array)
        if array.ndim != 2 or array.shape[1] != len(columns):
            raise ValueError(f"block {name!r}: shape {array.shape} does not "
                             f"match {len(columns)} column name(s)")
        if draws is None:
            draws = array.shape[0]
        if array.shape[0] != draws:
            raise ValueError(f"block {name!r} has {array.shape[0]} draws, "
                             f"the first block {draws}")
        entry = {"name": name}
        if step is not None:
            q = np.round(np.asarray(array, dtype=float) / step)
            if q.size and q.min() < 0:
                raise ValueError(f"block {name!r} is negative; a step stores "
                                 f"non-negative values only")
            top = q.max() if q.size else 0
            width = np.uint16 if top <= np.iinfo(np.uint16).max else np.uint32
            if top > np.iinfo(width).max:
                raise ValueError(f"block {name!r} does not fit 32 bits at step "
                                 f"{step}")
            array = q.astype(width)
            entry["step"] = float(step)
        dtype = array.dtype.newbyteorder("<")
        data = np.ascontiguousarray(array.T, dtype=dtype).tobytes()
        entry.update({"dtype": dtype.str, "offset": len(out),
                      "nbytes": len(data), "columns": list(columns)})
        table.append(entry)
        out += data
    return bytes(out), table


def unpack(blob: bytes, manifest: dict) -> dict[str, np.ndarray]:
    """The blocks of a draw file, each as a ``(draws, columns)`` array.

    A block stored with a ``step`` comes back as float64 multiples of it.

    Refuses a file whose format, length or block table does not agree with
    the manifest, rather than reading it at an offset that might be wrong.
    """
    if manifest.get("format") != FORMAT:
        raise Refused(f"draw file format {manifest.get('format')!r}; this "
                      f"reader understands {FORMAT!r}")
    draws = int(manifest["draws"])
    blocks = manifest["blocks"]
    expected = sum(int(b["nbytes"]) for b in blocks)
    if len(blob) != expected:
        raise Refused(f"draw file is {len(blob)} bytes; its manifest "
                      f"describes {expected}")
    out = {}
    for b in blocks:
        dtype = np.dtype(b["dtype"])
        cols = len(b["columns"])
        if int(b["nbytes"]) != dtype.itemsize * cols * draws:
            raise Refused(f"block {b['name']!r}: {b['nbytes']} bytes cannot "
                          f"hold {cols} x {draws} of {dtype}")
        flat = np.frombuffer(blob, dtype=dtype, count=cols * draws,
                             offset=int(b["offset"]))
        array = flat.reshape(cols, draws).T
        if "step" in b:
            array = array * float(b["step"])
        out[b["name"]] = array
    return out


# ==========================================================================
# weights
# ==========================================================================

def uniform(n: int) -> np.ndarray:
    """The untouched page: every draw counts once. Exactly the published forecast."""
    return np.ones(int(n))


def effective_draws(weights) -> float:
    """Kish's effective sample size, (Σw)² / Σw².

    Uniform weights give exactly the draw count (every product here is an
    exact integer in floating point at the draw counts this model runs).
    """
    w = np.asarray(weights, dtype=float)
    return float(w.sum() ** 2 / np.square(w).sum())


def require_effective(weights, floor: int = MIN_EFFECTIVE_DRAWS) -> float:
    """The effective draw count, or :class:`Refused` if it is below ``floor``."""
    ess = effective_draws(weights)
    if not ess >= floor:
        raise Refused(f"{ess:.0f} effective draws of {len(weights)}; a figure "
                      f"needs at least {floor}. The draws do not reach this "
                      f"setting.")
    return ess


def combine(*weights) -> np.ndarray:
    """Several controls at once: their weights multiply, scaled to a maximum of one."""
    w = np.ones(len(weights[0]))
    for x in weights:
        w = w * np.asarray(x, dtype=float)
    top = w.max()
    if not top > 0:
        raise Refused("these controls together leave no draw with any weight")
    return w / top


def _tilt(features: np.ndarray, targets: np.ndarray, *,
          tolerance: float, steps: int) -> np.ndarray:
    """Exponential tilting: w ∝ exp(λ·x), λ chosen so the weighted mean of x is ``targets``.

    Of all weightings that hit the targets, this is the one closest to uniform
    in Kullback-Leibler divergence, so it moves the draws no further than the
    targets require. λ minimises the convex dual log Σ exp(λ·(x − target));
    Newton's method with step halving. The features are standardised first so
    one tolerance serves every column.

    Raises :class:`Refused` when a target lies outside what the draws span:
    the dual then has no minimum and λ runs away, which is the draws saying
    they hold no weighting with that mean.
    """
    x = np.asarray(features, dtype=float)
    t = np.asarray(targets, dtype=float)
    centre, scale = x.mean(axis=0), x.std(axis=0)
    if not np.all(scale > 0):
        raise Refused("a column does not vary across the draws, so no weighting "
                      "can move its mean")
    z = (x - centre) / scale
    goal = (t - centre) / scale
    lo, hi = z.min(axis=0), z.max(axis=0)
    if np.any(goal <= lo) or np.any(goal >= hi):
        raise Refused("the target lies outside the range the draws span")
    d = z - goal
    lam = np.zeros(d.shape[1])

    def dual(l):
        a = d @ l
        m = a.max()
        return m + np.log(np.exp(a - m).sum())

    for _ in range(steps):
        a = d @ lam
        w = np.exp(a - a.max())
        p = w / w.sum()
        grad = p @ d
        if np.max(np.abs(grad)) < tolerance:
            return w / w.max()
        cov = (d * p[:, None]).T @ d - np.outer(grad, grad)
        try:
            step = np.linalg.solve(cov, grad)
        except np.linalg.LinAlgError as exc:
            raise Refused(f"the tilt is singular: {exc}") from exc
        f0, s = dual(lam), 1.0
        while dual(lam - s * step) > f0 - 1e-4 * s * (grad @ step) and s > 1e-12:
            s *= 0.5
        lam = lam - s * step
    raise Refused("the tilt did not converge: the target is at the edge of what "
                  "the draws span")


def turnout_tilt(turnouts, shift, *, tolerance: float = 1e-10,
                 steps: int = 200) -> np.ndarray:
    """Weights that move EVERY pool's mean turnout by ``shift`` at once.

    ``turnouts`` is the draw file's ``pool_turnout`` block, ``(draws, pools)``;
    ``shift`` has one entry per pool, in turnout points as a fraction (0.05 =
    five points), and 0 means "held at its published mean", which is a target,
    not an absence of one. PLAN.md finding 3 is why there is no single-pool
    form: pool turnouts move together, so selecting draws where one pool is
    high lifts all four, and the reader who asked for "Black African turnout
    up five points" would be shown "everyone's turnout up" instead.

    All shifts zero returns uniform weights exactly: λ = 0 is then the solution
    and nothing needs solving. Weights are scaled to a maximum of one; call
    :func:`require_effective` on them before showing a figure.

    Raises :class:`Refused` if a target leaves the range the draws span.
    """
    x = np.asarray(turnouts, dtype=float)
    s = np.asarray(shift, dtype=float)
    if x.ndim != 2 or s.shape != (x.shape[1],):
        raise ValueError(f"need one shift per pool: turnouts {x.shape}, shift "
                         f"{s.shape}")
    if not np.all(np.isfinite(s)):
        raise ValueError("every pool needs a finite target; 0 holds it at its mean")
    if not np.any(s):
        return uniform(x.shape[0])
    return _tilt(x, x.mean(axis=0) + s, tolerance=tolerance, steps=steps)


def _on_polled_base(shares, columns, poll: dict) -> tuple[np.ndarray, np.ndarray]:
    """Each draw's shares and the poll, both renormalised to the polled parties."""
    missing = sorted(set(poll) - set(columns))
    if missing:
        raise ValueError(f"the poll names {missing}, which the draws do not carry")
    names = sorted(poll)
    idx = [list(columns).index(p) for p in names]
    x = np.asarray(shares, dtype=float)[:, idx]
    total = x.sum(axis=1, keepdims=True)
    if not np.all(total > 0):
        raise Refused("some draw gives the polled parties no votes at all")
    y = np.array([float(poll[p]) for p in names])
    if not y.sum() > 0:
        raise ValueError("the poll gives its parties no share")
    return x / total, y / y.sum()


def poll_weights(shares, columns, poll: dict, *, sigma: float,
                 trust: float) -> np.ndarray:
    """A poll as a likelihood on each draw, raised to the power ``trust``.

    ``shares`` is the draw file's ``pr_share`` block and ``columns`` its
    column names; ``poll`` maps party to share, in any units. Both the poll and
    each draw are renormalised to the polled parties (PLAN.md §5's "stated
    base"), so a poll that omits parties is compared only on the parties it
    names. The likelihood is independent normal, sd ``sigma`` (a fraction:
    0.05 = five points) on each polled party's renormalised share.

    ``trust`` runs from 0 to 1. At 0 every weight is exp(0) = 1 EXACTLY, the
    published forecast (DESIGN-decided §3: our own trust is zero). At 1 the
    weights are the full likelihood — not "the poll happens", but "the draws
    closest to this poll", which is all the draws can offer and what the page
    must say. Between, the likelihood is tempered, equivalent to sd
    ``sigma / sqrt(trust)``.

    ``sigma`` has no default. It is the reader's view of how wrong a poll can
    be, and a default here would be a number the model chose for them.
    """
    if not 0.0 <= trust <= 1.0:
        raise ValueError(f"trust is between 0 and 1, not {trust}")
    if not sigma > 0:
        raise ValueError(f"sigma must be positive, not {sigma}")
    x, y = _on_polled_base(shares, columns, poll)
    loglik = -0.5 * np.square((x - y) / sigma).sum(axis=1)
    a = trust * loglik
    return np.exp(a - a.max())


def combine_polls(polls: list[dict]) -> tuple[dict, dict]:
    """The average of the polls switched on, and the spread between them.

    Each poll is first renormalised over the parties ALL of them name, so they
    are averaged on one base. Returns ``(average, spread)``; ``spread`` maps
    each party to ``(lowest, highest)`` across the polls, which the page shows
    beside the average (DESIGN-decided §2: the disagreement is the finding).
    """
    if not polls:
        raise ValueError("no poll is switched on")
    common = sorted(set.intersection(*(set(p) for p in polls)))
    if not common:
        raise Refused("the polls switched on share no party")
    rows = []
    for p in polls:
        y = np.array([float(p[k]) for k in common])
        rows.append(y / y.sum())
    m = np.array(rows)
    average = {k: float(v) for k, v in zip(common, m.mean(axis=0))}
    spread = {k: (float(lo), float(hi))
              for k, lo, hi in zip(common, m.min(axis=0), m.max(axis=0))}
    return average, spread


# ==========================================================================
# weighted statistics — each reduces to the published formula when uniform
# ==========================================================================

def _lerp(a, b, t):
    """numpy's own linear interpolation, including its t >= 0.5 branch.

    Reproduced rather than approximated: ``np.percentile`` computes a + (b-a)t
    and, for t >= 0.5, b - (b-a)(1-t), and the two differ in the last place.
    Uniform weights must give the published p5/p95 bit for bit.
    """
    diff = b - a
    return b - diff * (1 - t) if t >= 0.5 else a + diff * t


def weighted_quantile(values, weights, q: float) -> float:
    """The ``q``-quantile (0..1) of ``values`` under ``weights``.

    Each draw is placed at the centre of its own weight, measured from the
    centre of the first draw's: sorted draw k sits at
    S_k − w_k/2 − w_1/2, where S_k is the cumulative weight, and the quantile
    sits at q × (W − w_1/2 − w_n/2). With unit weights that is draw k at k and
    the quantile at (n − 1)q — numpy's default 'linear' method exactly, so
    uniform weights reproduce ``np.percentile`` and ``np.median`` bit for bit.
    The placement is symmetric, so reversing the values mirrors the quantile.

    Weights are scaled to a maximum of one first, so any constant weighting is
    exactly the unit case. Draws of zero weight are dropped.
    """
    v = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    keep = w > 0
    v, w = v[keep], w[keep] / w[keep].max()
    order = np.argsort(v, kind="stable")
    v, w = v[order], w[order]
    cum = np.cumsum(w)
    pos = cum - w / 2 - w[0] / 2
    target = q * (cum[-1] - w[0] / 2 - w[-1] / 2)
    k = int(np.searchsorted(pos, target, side="right")) - 1
    k = min(max(k, 0), len(v) - 1)
    if k == len(v) - 1:
        return float(v[-1])
    gamma = (target - pos[k]) / (pos[k + 1] - pos[k])
    return float(_lerp(v[k], v[k + 1], gamma))


def weighted_probability(event, weights) -> float:
    """P(event) under the weights: Σ w·1[event] / Σ w.

    With unit weights, the count over the draw count — the published
    ``(mask).mean()`` exactly.
    """
    e = np.asarray(event, dtype=bool)
    w = np.asarray(weights, dtype=float)
    return float(w[e].sum() / w.sum())


def weighted_mean_se(values, weights) -> tuple[float, float]:
    """The weighted mean and its linearised standard error.

    SE = sqrt(Σ w̃ᵢ² (xᵢ − m)²) with w̃ normalised to sum to one. Under uniform
    weights this is the plug-in SE of a sample mean, sd/√n with the 1/n
    variance.
    """
    x = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    p = w / w.sum()
    m = float(p @ x)
    return m, float(np.sqrt(np.square(p) @ np.square(x - m)))


def ward_win_probability(winners, weights, codes: int) -> np.ndarray:
    """P(each party wins each ward), ``(wards, codes)``, Jeffreys-corrected.

    ``winners`` is the ``ward_winner`` block, ``(draws, wards)`` of codes.
    The published estimate is (k + ½) / (N + 1) (``montecarlo.main``'s
    ``_p_win``: a party that won every draw is never reported certain). Under
    weights, k becomes the weighted win count scaled to the effective sample,
    and N the effective sample, so the correction still speaks to how much
    evidence the figure rests on. With unit weights the scale is exactly one
    and this is the published formula.
    """
    c = np.asarray(winners)
    w = np.asarray(weights, dtype=float)
    total = w.sum()
    ess = effective_draws(w)
    out = np.zeros((c.shape[1], codes))
    for j in range(c.shape[1]):
        out[j] = np.bincount(c[:, j], weights=w, minlength=codes)
    return (out * (ess / total) + 0.5) / (ess + 1.0)
