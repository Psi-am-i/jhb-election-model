"""Re-weight the published draws: the interactive's engine, and the draw file's format.

The interactive's "play with the model" controls do not re-run the model. The
published run's draws already vary in the quantities those controls move (each
draw's four pool turnouts, each draw's PR shares), so a control is a WEIGHT on
each draw, and every figure the page shows is a weighted statistic of the same
draws (``audits/2026-09-28-interactive-architecture/PLAN.md`` §§2-5, build step
S4). This module is that arithmetic, and it is the ONE definition of it: the
browser runs this file under Pyodide, copied byte for byte, never a
translation (INTEGRATION.md §3b). So it is pure Python plus numpy: no file
access, no scipy, and no TOP-LEVEL import from the rest of ``src/``.

Two functions import from ``src/`` inside their bodies, because the rule they
apply is the model's and has one definition there:

* :func:`page_polls` imports ``polling`` (and through it ``cityconfig``) and
  ``montecarlo``, and reads ``polls.json``. It runs at BUILD time, never in the
  browser.
* :func:`poll_trust_sd`, and :func:`poll_weights` when given ``trust``,
  import ``polling`` for ``polling.poll_sd``. At ``trust == 0`` neither
  imports anything, so the untouched page needs only numpy. A page that offers
  the trust dial must serve ``polling.py`` and ``cityconfig.py`` beside this
  file.

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
  With a poll switched on, the tilt is solved ON the poll's weights
  (``base=``), so the turnout the reader asked for is the turnout shown.
* :func:`page_polls` — the polls the page offers: exactly those the model's
  own admission rules (``polling.screen`` / ``polling.metro_polls``) admit for
  the target (the S6 review's F8).
* :func:`poll_weights` — a poll as a likelihood on each draw, with ONE control:
  either the reader's trust ``t`` in [0, 1] (preferred, :func:`poll_trust_sd`)
  or the poll error ``sd`` directly. Zero trust, like an infinite error, is
  uniform weights EXACTLY (DESIGN-decided §3: our own trust is zero). Figures
  computed under it are :data:`POLL_LABEL`, never "what happens if the poll is
  right".
* :func:`poll_trust_sd` — the trust dial's meaning (owner's decision 2,
  2026-09-30; JUDGEMENT-CALLS §N2): ``sd(t) = polling.poll_sd / t``.
* :func:`combine_polls` — the average of the polls a reader switches on, and
  the spread between them, which is shown and never hidden (DESIGN-decided §2).
* :func:`effective_draws` and :func:`require_effective` — Kish's effective
  sample, and the refusal below :data:`MIN_EFFECTIVE_DRAWS`.
* :func:`quantile_effective_draws`, :func:`tail_effective_draws` and
  :func:`figure` — the effective draws behind ONE statistic. Kish's count
  describes the weights; a 5th percentile rests on how the weight falls either
  side of it, which can be far fewer.
* :func:`sampling_se` — the Monte Carlo sampling error of one weighted
  quantile, in seats, so the page can say when two figures differ by less than
  the draws can resolve (the review's F2: the by-election cells are unpaired).
* :func:`figure` WITHHOLDS a quantile whose sampling error exceeds
  :data:`MAX_FIGURE_SE_SEATS`, and :func:`within_precision` tells the page
  when a control has reached that point for any figure it shows (the review's
  F17, as the owner re-decided it on 2026-09-30). The Kish floor,
  :data:`MIN_EFFECTIVE_DRAWS`, stays as a separate whole-page refusal.
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
#: row, its evidence and how to check it. It is a WHOLE-PAGE refusal on the
#: weights; whether one figure is shown is :data:`MAX_FIGURE_SE_SEATS`'s.
MIN_EFFECTIVE_DRAWS = 200

#: The largest Monte Carlo standard error, in seats, a figure the page shows
#: may carry (:func:`sampling_se`). Above it :func:`figure` withholds the
#: figure and :func:`within_precision` stops the control. The owner's rule of
#: 2026-09-30, superseding an absolute tail-draw floor that withheld every
#: range at any move. A judgement call: JUDGEMENT-CALLS.md §N2 carries it with
#: its evidence. In the values' own units, which on the page are seats.
MAX_FIGURE_SE_SEATS = 2.0

#: What a figure computed under a poll's weights is, in the page's words. The
#: weights select the model's own draws that lie near the poll; they do not
#: make the poll come true, and a draw set with nothing near the poll gives an
#: answer about the nearest draws there are. :func:`figure` attaches it.
POLL_LABEL = "the model's draws nearest this poll"

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


def require_effective(weights, floor: int | None = None) -> float:
    """The effective draw count, or :class:`Refused` if it is below ``floor``.

    ``floor`` defaults to :data:`MIN_EFFECTIVE_DRAWS`, read at call time so
    that rebinding the module constant reaches the call
    (``tests/test_ipf_feasibility.py``, CLASS 13).
    """
    floor = MIN_EFFECTIVE_DRAWS if floor is None else floor
    ess = effective_draws(weights)
    if not ess >= floor:
        raise Refused(f"{ess:.0f} effective draws of {len(weights)}; a figure "
                      f"needs at least {floor}. The draws do not reach this "
                      f"setting.")
    return ess


def _tilt(features: np.ndarray, targets: np.ndarray, *, base=None,
          tolerance: float, steps: int) -> np.ndarray:
    """Exponential tilting: w ∝ base·exp(λ·x), λ chosen so the weighted mean of x is ``targets``.

    Of all weightings that hit the targets, this is the one closest to
    ``base`` (uniform when ``base`` is None) in Kullback-Leibler divergence, so
    it moves the draws no further than the targets require. λ minimises the
    convex dual log Σ base·exp(λ·(x − target)); Newton's method with step
    halving. The features are standardised first so one tolerance serves every
    column.

    The targets are met under the RETURNED weights, base included. Solving on
    uniform weights and multiplying a base in afterwards does not do that: the
    base moves the means the tilt was solved to hit, by as much as turnout and
    the base's own quantity are correlated across draws (the blind review's
    A7; ``tests/test_reweight.py`` builds the correlated case).

    Raises :class:`Refused` when a target lies outside what the draws of
    positive base weight span: the dual then has no minimum and λ runs away,
    which is the draws saying they hold no weighting with that mean.
    """
    x = np.asarray(features, dtype=float)
    t = np.asarray(targets, dtype=float)
    if base is None:
        logb = np.zeros(x.shape[0])
    else:
        b = np.asarray(base, dtype=float)
        if b.shape != (x.shape[0],) or not np.all(np.isfinite(b)) \
                or np.any(b < 0):
            raise ValueError("the base needs one finite, non-negative weight "
                             "per draw")
        live = b > 0
        if not np.any(live):
            raise Refused("the base leaves no draw with any weight")
        x = x[live]
        logb = np.log(b[live])
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
        a = logb + d @ l
        m = a.max()
        return m + np.log(np.exp(a - m).sum())

    def result(w):
        if base is None:
            return w / w.max()
        out = np.zeros(len(live))
        out[live] = w / w.max()
        return out

    for _ in range(steps):
        a = logb + d @ lam
        w = np.exp(a - a.max())
        p = w / w.sum()
        grad = p @ d
        if np.max(np.abs(grad)) < tolerance:
            return result(w)
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


def turnout_tilt(turnouts, shift, *, base=None, pin_to=None,
                 tolerance: float = 1e-10, steps: int = 200) -> np.ndarray:
    """Weights that move EVERY pool's mean turnout by ``shift`` at once.

    ``turnouts`` is the draw file's ``pool_turnout`` block, ``(draws, pools)``;
    ``shift`` has one entry per pool, in turnout points as a fraction (0.05 =
    five points), and 0 means "held at its published mean", which is a target,
    not an absence of one. PLAN.md finding 3 is why there is no single-pool
    form: pool turnouts move together, so selecting draws where one pool is
    high lifts all four, and the reader who asked for "Black African turnout
    up five points" would be shown "everyone's turnout up" instead.

    ``base`` is the weights of every other control switched on — a poll's,
    from :func:`poll_weights`. The tilt is solved ON them, so the returned
    weights already include the base and hit the turnout targets exactly under
    it; never multiply a tilt solved without the base by the base afterwards
    (the blind review's A7: that misses the target by as much as turnout and
    poll agreement are correlated across draws). The targets are the pinned
    means plus ``shift`` whatever the base, because that is what the reader
    set.

    ``pin_to`` is the per-pool mean turnout the targets are measured from.
    Omitted, it is these draws' own unweighted mean — the published mean when
    ``turnouts`` is the published cell. Two cases need it passed (the S6
    review's F4 and F10):

    * **A poll is on.** The page pins turnout at the PUBLISHED mean — calling
      this with ``base=`` the poll's weights and ``pin_to=`` the published
      cell's mean turnouts, even when the reader has not touched turnout — so
      a poll never moves turnout by the back door. The page says so.
    * **Another cell is shown.** The cells are unpaired re-runs, so a cell's
      own mean turnout differs from the published one by sampling alone; a
      target taken from it would mean a different turnout in each cell.

    All shifts zero with no base and no ``pin_to`` returns uniform weights
    exactly: λ = 0 is then the solution and nothing needs solving. With a base
    or a ``pin_to``, all shifts zero is NOT a no-op: it holds every pool at the
    pinned mean under the base. Weights are scaled to a maximum of one; call
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
    if pin_to is None:
        if base is None and not np.any(s):
            return uniform(x.shape[0])
        centre = x.mean(axis=0)
    else:
        centre = np.asarray(pin_to, dtype=float)
        if centre.shape != (x.shape[1],) or not np.all(np.isfinite(centre)):
            raise ValueError(f"pin_to needs one finite mean per pool: turnouts "
                             f"{x.shape}, pin_to {centre.shape}")
    return _tilt(x, centre + s, base=base, tolerance=tolerance, steps=steps)


def page_polls(target) -> list[dict]:
    """The polls the page offers for ``target``: those the model's own rules admit.

    ``target`` is a ``cityconfig.Target``. The set is ``polling.metro_polls``
    after ``polling.validate_or_die`` — the same calls, in the same order, with
    the same sample-size floor (``montecarlo.DEFAULTS["poll_min_n"]``) that
    ``montecarlo.run_model`` makes before it blends a poll. So a poll the model
    refuses (after polling day, commissioned, another city, no city, too small,
    undated) never appears, and nothing here restates a rule (the S6 review's
    F8). A malformed register raises, as it does for the model.

    ``poll_paths`` is deliberately NOT applied. It is the model's switch for
    whether the published forecast USES the admitted polls (``"off"`` since
    2026-09-12), not a rule about which polls are admissible; the page's dial
    exists to let a reader turn on what the forecast leaves off, at a trust the
    site states as zero.

    Each record is returned as a copy with one field added, ``asof``: the
    target's polling day, ISO 8601. :func:`poll_trust_sd` prices a poll at that
    date, as the model does (``asof=target.date``), so the dial's 1 is the
    model's own error for the poll, drift included.

    BUILD TIME ONLY: it reads ``polls.json`` from the working directory
    (``polling.REGISTER``) and imports ``montecarlo``.
    """
    import montecarlo
    import polling

    polling.validate_or_die()
    kept = polling.metro_polls(
        target, min_n=float(montecarlo.DEFAULTS["poll_min_n"]))
    asof = target.date.isoformat()
    return [dict(p, asof=asof) for p in kept]


def _asof(poll: dict, asof):
    """The date a poll is priced at: ``asof`` if given, else the record's own."""
    from datetime import date

    when = asof if asof is not None else poll.get("asof")
    if when is None:
        raise Refused(f"poll {poll.get('id', '<no id>')!r} carries no date to "
                      f"price its drift at; pass asof, or take it from "
                      f"page_polls, which stamps the target's polling day")
    return when if isinstance(when, date) else date.fromisoformat(str(when))


def poll_trust_sd(poll: dict, share: float, trust: float, *,
                  asof=None) -> float:
    """The poll error the trust dial means: ``polling.poll_sd / trust``.

    The owner's decision 2 (2026-09-30; JUDGEMENT-CALLS §N2). ``trust`` is in
    [0, 1]; the page shows it as 0-100.

    * ``trust == 1`` is the poll at the model's own error for it,
      ``polling.poll_sd(poll, share, asof=…)``: sampling from the poll's
      effective sample, plus the house term, the undisclosed-screen term and
      drift since fieldwork. It is that TOTAL, not sampling error alone; a
      poll with no published ``n`` is priced on the house term (``poll_sd``'s
      own fallback).
    * ``trust == 0`` is ``math.inf``: no weight on the poll, uniform weights
      exactly, the published forecast. It returns before touching ``polling``.
    * In between, the error grows as ``1 / trust``, so the likelihood's width
      is always a multiple of a number the model derived, never one the page
      chose.

    ``poll`` is the register record (``polling.poll_sd`` reads ``n``,
    ``n_basis``, ``deff``, ``screen_disclosed``, ``fieldwork_end``) and
    ``share`` that party's share as the poll reports it. ``asof`` is the date
    the drift is measured to; if omitted, the record's own ``asof``
    (:func:`page_polls` stamps it); if neither exists, :class:`Refused`
    rather than a drift of zero.

    Refuses ``trust`` outside [0, 1] (NaN included): above 1 would claim more
    than the model's own reading of the poll.
    """
    t = float(trust)
    if not 0.0 <= t <= 1.0:
        raise Refused(f"trust is {trust!r}; it runs from 0 (the published "
                      f"forecast) to 1 (the poll at the model's own error)")
    if t == 0.0:
        return float("inf")
    import polling

    return float(polling.poll_sd(poll, share, asof=_asof(poll, asof))) / t


def _numbers(poll: dict) -> dict:
    """Party to share: a register record's ``numbers``, or the map itself."""
    numbers = poll.get("numbers")
    return numbers if isinstance(numbers, dict) else poll


def _on_polled_base(shares, columns, poll: dict) -> tuple[np.ndarray, np.ndarray]:
    """Each draw's shares and the poll, both renormalised to the polled parties.

    Every failure is :class:`Refused` (the S6 review's F9): each is a poll the
    draws cannot answer, which the page reports as a reason, not a crash.
    """
    missing = sorted(set(poll) - set(columns))
    if missing:
        raise Refused(f"the poll names {missing}, which the draws do not carry")
    if not poll:
        raise Refused("the poll names no party")
    names = sorted(poll)
    idx = [list(columns).index(p) for p in names]
    x = np.asarray(shares, dtype=float)[:, idx]
    total = x.sum(axis=1, keepdims=True)
    if not np.all(total > 0):
        raise Refused("some draw gives the polled parties no votes at all")
    y = np.array([float(poll[p]) for p in names])
    if not y.sum() > 0:
        raise Refused("the poll gives its parties no share")
    return x / total, y / y.sum()


def poll_weights(shares, columns, poll: dict, *, sd: float | None = None,
                 trust: float | None = None, asof=None) -> np.ndarray:
    """A poll as a likelihood on each draw, with ONE control: ``trust`` or ``sd``.

    ``shares`` is the draw file's ``pr_share`` block and ``columns`` its
    column names. ``poll`` is a register record (its ``numbers`` are read) or
    a bare party-to-share map, in any units. Both the poll and each draw are
    renormalised to the polled parties (PLAN.md §5's "stated base"), so a poll
    that omits parties is compared only on the parties it names. The
    likelihood is independent normal on each polled party's RENORMALISED
    share.

    Exactly one control, never both and never neither (a default would be a
    number the model chose for the reader):

    * ``trust`` in [0, 1] — preferred, the page's dial (owner's decision 2).
      Each polled party ``p`` gets its own error, :func:`poll_trust_sd` of
      the record at the poll's reported share ``y_p``, divided by ``S``, the
      sum of the poll's reported shares over the parties it names. ``poll_sd``
      is in the poll's raw units; renormalising a share divides it by ``S``,
      and so divides its error by ``S`` (holding the denominator fixed). This
      puts the error on the base the comparison is made on. Needs the record,
      not a bare map. ``trust == 0`` is uniform weights EXACTLY and imports
      nothing.
    * ``sd`` — one error for every party, on the renormalised base, as a
      fraction (0.05 = five points). ``sd = math.inf`` is uniform EXACTLY.

    A likelihood raised to a power t at sd σ is the same likelihood at sd
    σ/√t, so a second exponent would be the same degree of freedom shown twice
    (the blind review's A8); there is none. As the error falls the weights
    concentrate on the draws closest to the poll — not "the poll happens", but
    :data:`POLL_LABEL`, which is all the draws can offer and what the page
    must say.

    SEVERAL POLLS ON: the likelihoods are independent in this function's
    arithmetic, so the page's weights for several polls are the PRODUCT of
    each poll's weights at the one trust. Two waves of one house share its
    house error, which that product does not know; ``polling.effective_houses``
    measures how many independent houses stand behind a set of polls.
    """
    if (sd is None) == (trust is None):
        raise TypeError("poll_weights takes exactly one of trust= and sd=")
    numbers = _numbers(poll)
    x, y = _on_polled_base(shares, columns, numbers)
    if trust is not None:
        if not isinstance(poll.get("numbers"), dict):
            raise Refused("trust prices the poll from its register record; a "
                          "bare party-to-share map carries no sample size")
        if poll_trust_sd(poll, 0.5, trust, asof=asof) == float("inf"):
            return uniform(x.shape[0])
        names = sorted(numbers)
        raw = np.array([float(numbers[p]) for p in names])
        scale = raw.sum()
        sds = np.array([poll_trust_sd(poll, share, trust, asof=asof)
                        for share in raw]) / scale
    else:
        sd = float(sd)
        if not sd > 0:
            raise ValueError(f"sd must be positive, not {sd}")
        if np.isinf(sd):
            return uniform(x.shape[0])
        sds = sd
    loglik = -0.5 * np.square((x - y) / sds).sum(axis=1)
    return np.exp(loglik - loglik.max())


def combine_polls(polls: list[dict]) -> tuple[dict, dict]:
    """The average of the polls switched on, and the spread between them.

    Each poll (a register record or a party-to-share map) is renormalised over
    the parties IT names, and the average is taken over every party that at
    least two of the polls name, each party averaged over the polls that name
    it. The party base is NOT shrunk to the parties every poll names: one poll
    naming fewer parties would otherwise delete the rest from all of them (the
    S6 review's F8). A party only one poll names is left out, because one
    reading has no average and no spread.

    Returns ``(average, spread)``; ``spread`` maps each party to ``(lowest,
    highest)`` across the polls naming it, which the page shows beside the
    average (DESIGN-decided §2: the disagreement is the finding). The average
    is on no single poll's base, so its shares need not sum to one;
    :func:`poll_weights` renormalises whatever it is given.

    ONE poll is returned as itself, renormalised, with each spread its single
    value: there is nothing to combine, and no disagreement can be measured.
    Two or more polls with no party in common between any two:
    :class:`Refused`.
    """
    if not polls:
        raise ValueError("no poll is switched on")
    rows = []
    for p in polls:
        numbers = _numbers(p)
        total = sum(float(v) for v in numbers.values())
        if not total > 0:
            raise Refused(f"poll {p.get('id', '<no id>')!r} gives its parties "
                          f"no share")
        rows.append({k: float(v) / total for k, v in numbers.items()})
    counts: dict[str, int] = {}
    for r in rows:
        for k in r:
            counts[k] = counts.get(k, 0) + 1
    need = 1 if len(rows) == 1 else 2
    parties = sorted(k for k, c in counts.items() if c >= need)
    if not parties:
        raise Refused("no party is named by two of the polls switched on")
    average, spread = {}, {}
    for k in parties:
        vals = np.array([r[k] for r in rows if k in r])
        average[k] = float(vals.mean())
        spread[k] = (float(vals.min()), float(vals.max()))
    return average, spread


# ==========================================================================
# weighted statistics — each reduces to the published formula when uniform
# ==========================================================================

def _lerp(a, b, t):
    """numpy's own linear interpolation, including its t >= 0.5 branch.

    Reproduced rather than approximated: ``np.percentile`` computes a + (b-a)t
    and, for t >= 0.5, b - (b-a)(1-t), and the two differ in the last place.
    Uniform weights must give the published p5/p95 bit for bit. Elementwise,
    so one call serves many quantiles; each element is computed by the same
    floating-point operations as a scalar call would.
    """
    diff = b - a
    return np.where(t >= 0.5, b - diff * (1 - t), a + diff * t)


def _weighted_quantiles(values, weights, qs) -> np.ndarray:
    """:func:`weighted_quantile` at every level in ``qs``, sorting once.

    The one definition of the weighted quantile; :func:`weighted_quantile` is
    this at a single level, and :func:`sampling_se` calls it at many.
    """
    v = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    keep = w > 0
    v, w = v[keep], w[keep] / w[keep].max()
    order = np.argsort(v, kind="stable")
    v, w = v[order], w[order]
    q = np.asarray(qs, dtype=float)
    if len(v) == 1:
        return np.full(q.shape, v[0])
    cum = np.cumsum(w)
    pos = cum - w / 2 - w[0] / 2
    target = q * (cum[-1] - w[0] / 2 - w[-1] / 2)
    k = np.searchsorted(pos, target, side="right") - 1
    k = np.clip(k, 0, len(v) - 1)
    last = k == len(v) - 1
    k = np.minimum(k, len(v) - 2)
    gamma = (target - pos[k]) / (pos[k + 1] - pos[k])
    return np.where(last, v[-1], _lerp(v[k], v[k + 1], gamma))


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
    return float(_weighted_quantiles(values, weights, [q])[0])


def quantile_effective_draws(values, weights, q: float) -> tuple[float, float]:
    """The effective draws behind ONE quantile, and the standard error of its level.

    Kish's count (:func:`effective_draws`) describes the weights as a whole. A
    quantile rests on something narrower: the weighted share of draws on its
    own side, P = Σ w̃·h with h = 1[x ≤ x_q] for q ≤ ½ and 1[x ≥ x_q] above
    (w̃ normalised to sum to one). The self-normalised estimate of P has
    linearised variance V = Σ w̃²(h − P)², and the effective draws for this
    statistic are P(1 − P) / V — the number of equally weighted draws that
    would estimate P as precisely. Under uniform weights V = P(1 − P)/n, so the
    count is exactly the draw count, the same unit as the floor. When a few
    heavy draws carry the tail it falls far below Kish's count, which is the
    case it exists to show.

    Returns ``(effective draws, sqrt(V))``: the second is the standard error of
    the quantile's LEVEL, as a fraction — how far the reported 5th percentile
    could sit from the true 5th, in percentile units. Ties count on the
    quantile's side, so for integer seats P can exceed q.

    Returns ``(0.0, nan)`` when every draw is on one side (P is 0 or 1 and the
    statistic has no spread to estimate).
    """
    v = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    p = w / w.sum()
    h = _quantile_side(v, w, q)
    share = float(p @ h)
    var = float(np.square(p) @ np.square(h - share))
    if not var > 0:
        return 0.0, float("nan")
    return share * (1.0 - share) / var, float(np.sqrt(var))


def _quantile_side(v: np.ndarray, w: np.ndarray, q: float) -> np.ndarray:
    """1 for the draws on the quantile's own side, ties included."""
    xq = weighted_quantile(v, w, q)
    return (v <= xq) if q <= 0.5 else (v >= xq)


def tail_effective_draws(values, weights, q: float) -> float:
    """Kish's effective count over the draws on the quantile's own side alone.

    Where :func:`quantile_effective_draws` says how precisely the weights place
    the quantile's LEVEL, this says how many draws its VALUE is read from:
    under uniform weights, the draw count on that side (about q·n, more with
    ties). A few heavy draws owning a tail drive it towards their number while
    Kish's count for the whole weighting stays healthy.
    """
    v = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    return effective_draws(w * _quantile_side(v, w, q))


def sampling_se(values, weights, q: float) -> float:
    """The Monte Carlo standard error of one weighted quantile, in the values' units.

    How far the ``q``-quantile of these draws under these weights could move
    if the model were run again with a different seed — the noise the page
    compares a lever's effect against (the S6 review's F2), and the number
    :data:`MAX_FIGURE_SE_SEATS` is set on. On the page the values are seats,
    so this is in seats.

    THE ESTIMATOR, and why this one. Bootstrap-free, because the page runs it
    on every control move. The sample quantile is the population quantile
    function read at a random LEVEL: to first order the level it lands on is
    normal about ``q`` with standard deviation ``s``, the linearised standard
    error of the self-normalised level estimate, Σ w̃²(h − P)² — the second
    return of :func:`quantile_effective_draws`, which carries the weights
    (a few heavy draws raise ``s``). So the SE is the standard deviation of
    ``Q(q + s·Z)``, Z standard normal, with Q this draw set's own weighted
    quantile function (:func:`weighted_quantile`), taken by Gauss–Hermite
    quadrature. It is the large-sample form of Maritz & Jarrett's (1978)
    quantile SE.

    The textbook alternative, the asymptotic ``s / f(x_q)`` with a density
    ``f`` (or Woodruff's finite difference over a narrow level interval), is
    what this reduces to where the values are smooth — and it fails on seats.
    Seats are integers: a quantile inside a block of tied values has a flat
    quantile function nearby, so a density-based SE is zero, while a
    re-run moves the figure by a whole seat whenever the level crosses the
    block's edge. Integrating over the level's distribution counts those
    crossings. ``tests/test_reweight.py`` checks it against a bootstrap and
    against repeated samples, on integer values.

    Its limit: for an integer-valued figure the true SE depends on where the
    population quantile sits within its block, which one draw set estimates
    only roughly, so on integers it is a noisy estimate of a noisy quantity.
    Where the quantile sits deep inside a block (true SE zero) it overstates,
    by about a tenth of a seat on average, and a bootstrap does the same; where
    re-runs flip the figure between two seats it and the bootstrap both
    understate by up to about a quarter. Neither is an error of this
    estimator in particular; both are what one draw set can say.
    Returns 0.0 when every draw lies on the quantile's side (nothing to
    estimate, as :func:`quantile_effective_draws` reports).
    """
    _, level = quantile_effective_draws(values, weights, q)
    if not np.isfinite(level):
        return 0.0
    # 41 nodes integrates Q(q + s·Z) to well within a draw's resolution: the
    # outermost nodes sit near ±8.6 s, beyond which the normal carries no
    # weight worth summing. Numerical accuracy, not a belief about elections.
    z, g = np.polynomial.hermite_e.hermegauss(41)
    g = g / g.sum()
    levels = np.clip(float(q) + level * z, 0.0, 1.0)
    vals = _weighted_quantiles(values, weights, levels)
    mean = float(g @ vals)
    return float(np.sqrt(g @ np.square(vals - mean)))


def _too_imprecise(se: float) -> bool:
    """The page's rule for one figure. The ceiling is read at call time."""
    return not se <= MAX_FIGURE_SE_SEATS


def figure(values, weights, q: float, *, poll: bool) -> dict:
    """One quantile as the page shows it: the value, what it rests on, and what it is.

    ``withheld`` is True, and ``value`` None, when the figure's sampling
    standard error (:func:`sampling_se`) exceeds :data:`MAX_FIGURE_SE_SEATS`
    (owner, 2026-09-30); the page shows a refusal in its place. That rule is
    per figure. :func:`require_effective` is separate: a refusal of the
    weights as a whole, below which the page shows no figure at all.

    ``poll`` says whether a poll's weights are among ``weights``; when they
    are, the figure carries :data:`POLL_LABEL`, and the page prints it beside
    the number. The effective counts are reported for the reader.
    """
    ess_q, level_se = quantile_effective_draws(values, weights, q)
    se = sampling_se(values, weights, q)
    withheld = _too_imprecise(se)
    return {"value": None if withheld else weighted_quantile(values, weights, q),
            "q": float(q),
            "withheld": withheld,
            "sampling_se": se,
            "effective_draws": effective_draws(weights),
            "quantile_effective_draws": ess_q,
            "tail_effective_draws": tail_effective_draws(values, weights, q),
            "level_se": level_se,
            "label": POLL_LABEL if poll else None}


def imprecise_figures(figures: dict, weights) -> list:
    """The names of the figures :func:`figure` would withhold under ``weights``.

    ``figures`` maps a name (anything the page uses to find the figure) to
    ``(values, q)``. Same rule as :func:`figure`, by the same function.
    """
    return [name for name, (values, q) in figures.items()
            if _too_imprecise(sampling_se(values, weights, q))]


def within_precision(figures: dict, weights) -> bool:
    """True when EVERY figure the page shows passes :data:`MAX_FIGURE_SE_SEATS`.

    The page's stop for a slider: it moves a control only as far as this
    stays true, so the reader is never walked into a page of withheld figures.
    ``figures`` is as for :func:`imprecise_figures`, and should be every
    median and range end the page shows.
    """
    return not imprecise_figures(figures, weights)


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
