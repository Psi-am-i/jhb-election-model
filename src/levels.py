"""How big each party will be, measured instead of typed.

The model's level layer was a set of hand-written per-party constants —
``theta_mode`` for six parties, ``individual_theta`` for six more, ``f_other``
for everyone else, and ``PLAN_BOUNDS`` clamping the lot. Every one of them was
formed by reading the outcomes it would later be asked to predict, which is
what the backtest's in-sample banner has been reporting. They also disagreed
with the record:

===============  ============  ====================================
constant         hand-typed    measured
===============  ============  ====================================
ANC theta_mode   0.75          0.84 (0.95, 0.86, 0.84, 0.67, 0.76)
DA theta_mode    1.30          1.19
f_other mode     1.30          0.79 — applied to 31 parties
PLAN_BOUNDS ANC  (0.65, 0.90)  excludes the observed 0.95
===============  ============  ====================================

``f_other`` mattered most: it had every minor party *growing* 30% on its way
into a local election when the record says they retain about four fifths.

What this module measures is θ, the national-to-local retention ratio: a
party's share at a local election over its share at the national election
before it. Binned by party size, the record says something specific::

    baseline share    n   median θ   sd(log θ)
    0    – 0.5%      18     0.84       0.72
    0.5% – 2%        17     0.90       0.46
    5%   – 15%        4     0.85       0.25
    15%  – 100%      12     0.93       0.26

**That table was measured on TWO metros, n=51, and its conclusion is wrong.**
It said the centre hardly moves and only the spread does, so size predicts how
uncertain a party is and not how it trends. On eight metros, n=235::

    national size before    n    median θ   geometric mean
    < 0.2%                 75      1.31         1.53
    0.2 - 0.5%             57      1.03         0.98
    0.5 - 2%               44      1.04         0.90
    2 - 10%                18      1.05         0.90
    > 10%                  41      0.94         0.95

Small parties GAIN going into a local election and large ones lose — Reif and
Schmitt's second-order effect, in this archive's own numbers. A single common
centre erases it, and erases it against the parties the model already
under-forecasts: they were being handed the large-party number. ``size_centre``
now fits ``log θ = a + b·log(size)`` and each party shrinks toward the centre
for a party ITS SIZE. The spread still collapses with size as the table always
said, so both terms now depend on it. A small or
unfamiliar party gets a wide interval automatically rather than one typed for
it, and nothing has probability zero — which is what the old triangulars kept
doing to outcomes that had already happened.

Everything here is filtered to transitions strictly before the target, so a
backtest cannot read its own result.

THE SPINE (2026-08-13, MODEL-LOG task #22)
------------------------------------------

θ alone is only half a forecast. It converts a party's last NATIONAL share into
a local one, which is the right spine for a nationally-organised party and the
wrong one for a party whose evidence is local — and until now the model used it
unconditionally. ActionSA is the case that forced this: 18.12% locally in 2021
against 6.22% nationally in 2024, and no θ of its own, so the forecast built it
from the 6.22% and discounted it to about 6%.

There is a second route. A party's previous LOCAL result, moved by the measured
local-to-local retention ρ, estimates the same quantity from different evidence.
Measured over 180 party-city-years across eight metros and three transitions,
neither route dominates — but **which one wins is predictable, and the thing
that predicts it is how much θ evidence the party has**:

    θ evidence (Σ reliability)    n    RMSE(log) national    local    best weight on local
    0     – 2                    60          1.53            0.72            1.00
    2     – 5                    55          0.089           0.24            0.10
    5     – 20                   65          0.20            0.41            0.10

That is not party size wearing a disguise. Within *every* size band the flip
survives: among parties under 0.5% of the vote, those with θ evidence want the
national route (best w 0.00) and those without want the local one (best w 1.00);
the same holds in the 0.5–5% band. Keying the same rule on size instead of
evidence is measurably worse (0.2377 against 0.2358 held out by metro).

So the weight on the local route is ``k / (worth + k)``: all local for a party
whose θ is nothing but the group centre, almost all national for a party with a
long retention record. One parameter, and it is a statement about *evidence*
rather than about which parties are "local" — which matters, because the two
things that sound like they should identify a local party do not (geographic
concentration correlates with the local premium at r = −0.09, and the premium is
no larger at home than away; MODEL-LOG §6).

Held out one metro at a time, refitting both routes without it: pooled
vote-weighted RMSE(log) 0.236 against the national spine's 0.275, a 14% gain.
It wins on four metros of eight by count and on the pooled error because the
wins land where the national route fails worst (Buffalo City 0.320 → 0.111,
Johannesburg 0.559 → 0.480) and the losses where it was already accurate
(Mangaung 0.077 → 0.094).

**Recency is priced by construction, not by a term.** The local result is five
years stale at polling day where the national is two. Each route is corrected by
a ratio fitted over its own gap — ρ over five-year LGE-to-LGE pairs, θ over
roughly two-year NPE-to-LGE ones — and the blend weight was fitted on local
results that were themselves five years stale. Nothing further is owed.

**Rejected: measuring θ in both directions.** MODEL-LOG proposed this as the
partial fix — a local→national pair inverted is nominally the same ratio, and it
would give ActionSA a θ of its own. Measured, it makes the forecast worse:
pooled held-out RMSE(log) 0.292 against forward-only 0.275, and every adaptive
blend built on it is worse than the same blend on forward θ. The reason is
visible in the pairs. A reverse observation divides a local result by a *later*
national one, so a party's secular trend enters with the opposite sign: the PA,
growing, measures 1.90 forward and 0.60 reverse; the ANC, declining, 0.85
forward and 1.05 reverse. The two numbers are not the same quantity, and pooling
them averages a party's trend into its local premium. The blend above solves
ActionSA's case directly and better, so the inversion is not needed for it
either.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np

import cityconfig
import parties as P
# The independent SLOT's name, from its one definition. `montecarlo` reads the
# same symbol; `absent_from_ballot` must exclude exactly what `run_model` did.
from seats import INDEPENDENT as _INDEPENDENT

# There is no "large party" threshold, because the record does not contain one.
# Binning the observations by baseline share gives sd(log theta) of 0.72, 0.46,
# 0.25 and 0.26 from the smallest band to the largest — a smooth decline, not a
# break, with the correlation between log size and |log theta| at -0.37. The
# *centre* barely moves at all (median 0.84 to 0.93 across every band). So size
# predicts how UNCERTAIN a party is, not how it trends, and it does so
# continuously. An earlier version split at 5%, which invented a discontinuity
# and put the difference in the median where it belongs in the spread.
SD_FLOOR, SD_CEILING = 0.15, 1.20

# WHY THE DISPERSION FIT IS NOT BIAS-CORRECTED, AND WHY SD_FLOOR IS RIGHT.
#
# `sd_for` recovers a dispersion from a least-squares line through
# log(residual^2), and that is biased downwards by a KNOWN factor: if
# r ~ N(0, s^2) then r^2/s^2 is chi-square with one degree of freedom, and
# E[log chi2_1] = psi(1/2) + log 2 = -1.270363. So the line estimates log(s^2)
# MINUS 1.270363, and exponentiating half of it returns 0.5298 of the true s.
# The correction would be exp(1.270363 / 2) = 1.887365 — derived, not fitted.
#
# It is real, and it checks out to three decimals against the record it fits:
# the binned sd(log theta) for parties at or above 15% of the vote is 0.227 over
# 39 observations, the uncorrected fit gives 0.120, and 0.120 x 1.8874 = 0.2265.
#
# APPLYING IT MAKES THE MODEL WORSE, measured over nine city-years at 600 draws:
# coherent seat error 258 -> 268, CRPS 231.9 -> 246.8, beats-uniform-swing 7/9 ->
# 6/9, and ranks 4-12 sd(z) 0.856 -> 0.522, i.e. from nearly correct width to
# badly over-wide.
#
# The reason is the whole point of MODEL-LOG §1.48's width budget. The binned
# record is a MARGINAL dispersion — everything that moved a party's local share
# against its national one — while this layer is CONDITIONAL: the within-pool
# Dirichlet independently supplies 39-98% of the drawn variance, and the turnout
# and ward layers a little more. Asking theta to reproduce the marginal record
# counts the same uncertainty twice.
#
# So SD_FLOOR = 0.15 is not the hedge against a level bias it was read as in
# §1.45. It is approximately the CONDITIONAL dispersion this layer should carry,
# sitting between the raw fit (0.120, too narrow because of the bias above) and
# the marginal record (0.227, too wide because it belongs to the whole model).
# That is a much better reason to keep it than "it scored best", and it is why
# the derived quantity CANNOT simply replace it: the derived quantity answers a
# different question. MODEL-LOG §1.50.
LOG_CHI2_BIAS = 1.8873652674492816   # documented, deliberately unused

# How many of a party's own observations are worth one group observation. Low,
# because a party has at most three and the group has dozens.
SHRINK = 2.0

# The national share at which one observed ratio is worth half of a large
# party's. Set to the hard cut it replaces, so the same evidence is being
# discounted — continuously, and without denying any party a measured θ.
RELIABILITY_HALF = 0.002

# How much θ evidence a party needs before the national spine is trusted over
# its own last local result. The weight on the LOCAL route is k / (worth + k),
# so at worth = k the two routes are equal. Fitted by leave-one-metro-out over
# 180 party-city-years: the curve is flat between 0.5 and 1.5 (0.2377, 0.2358,
# 0.2387) and degrades either side, so 1.0 is the middle of a plateau rather
# than a point estimate. See the module docstring.
SPINE_K = 1.0

# THE SIZE WINDOW'S RULE (BRIEF item 16, JUDGEMENT-CALLS §A52). A party's own
# ratios count toward its shrunk mean only where they were measured off a size
# within `h` (natural-log units) of its size now. `h` is DERIVED per target and
# per record by `size_window`, by scoring every candidate on how well each
# party's record predicted its next real ratio, and taking the WIDEST candidate
# whose cycle-clustered paired error difference from the best is not
# measurably worse (owner, 2026-10-09: "the window tie is settled by measuring
# the uncertainty"). What is typed is the grid it chooses from, the minimum
# number of scored observations below which it does not choose (and leaves the
# filter off), and the one-sided level at which a wider window counts as
# measurably worse. The t quantile is arithmetic (`_t_upper`), not a choice.
SIZE_WINDOW_GRID = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, float("inf"))
SIZE_WINDOW_MIN_SCORED = 20
SIZE_WINDOW_ALPHA = 0.05


# Every metro with a VD-level archive. The retention record is a national fact
# about how parties behave between election types, not a Johannesburg one, and
# reading it off eight cities instead of two is what makes ρ measurable at all:
# two metros give four LGE-to-LGE pairs, eight give sixteen. Nothing here is
# ever read at or after the target, so a wider evidence base is more evidence,
# not more leakage. A city whose archive does not go back simply contributes
# nothing — _citywide returns empty on a missing file.
METRO_CODES = ("JHB", "TSH", "CPT", "ETH", "EKU", "MAN", "NMA", "BUF")

# ⛔ HELD BACK PENDING DIAGNOSIS — NOT BECAUSE IT SCORES WORSE.
#
# The pre-2011 archive was ingested for all eight metros on 2026-09-01,
# `lge2000` and `npe1999`, every one reconciled at 100% and validated against
# each metro's own 2000 election. **The data is right and it is staying.**
#
# The reason recorded here matters more than the decision, because a hold-back
# justified by a score is **selection of training data on the test set** — the
# same failure as tuning a parameter to the panel, one level up and harder to
# see. If "keep the history that improves the panel" were ever the rule, the
# panel would stop being an out-of-sample check on this model. So:
#
#   **This is held back because its effect is NOT UNDERSTOOD, and it is void
#   the moment it is.** The cost is 13.65 CRPS across 12 of 16 city-years.
#
# **The boundary hypothesis is REFUTED, and that is why this entry is broad.**
# The first reading was that Ekurhuleni and eThekwini — constituted at the 2000
# election out of "Greater East Rand Metro" and "Durban Metro" — might not cover
# the modern ground, and that the damage would concentrate there. Tested:
#
#     all history live                  CRPS 345.99   seats 430
#     EKU + ETH held back only          CRPS 344.49   seats 428
#     all history held back             CRPS 332.34   seats 376
#
# Quarantining the two suspect metros recovers **1.50 of 13.65 — 11%**, against
# the ~44% the hypothesis predicted from their share of the per-city-year damage.
# Two further things follow. **The 2000 election was the first under wall-to-wall
# demarcation, so EVERY metro was constituted at it** — the reason never
# distinguished those two. And per-city-year attribution does not predict what
# removing an input recovers, because the splinter, entrant and pooled records
# are computed ACROSS ALL EIGHT METROS: damage attributed to a city-year can be
# caused by another city's data.
#
# **The surviving hypothesis is a REGIME effect**: 1999→2000 sits in a different
# party system (NNP extant, the DA newly merged, near-total ANC dominance) and
# its retention ratios are not exchangeable with 2019→2021's. The record is
# already known to be cycle-unstable — k* runs 0.62 / 2.48 / 1.70 / 1.76 across
# 2006 / 2011 / 2016 / 2021 with no covariate — so adding a fifth cycle whose k*
# is unknown perturbs the pooled fit and degrades every target at once, which is
# the pattern observed.
#
# **THE VOIDING TEST, SHARPENED BY MEASUREMENT (§1.158).** `THETA_WINDOW` was
# swept with this history live: the optimum is 2 transitions at 338.35, against
# 345.99 unlimited and 332.34 with the history out. So a recency window recovers
# **7.64 of the 13.65 and leaves 6.01** — the θ half of the damage is a recency
# effect and the rest is not. Since `THETA_WINDOW` trims only the θ record, the
# remainder is in the splinter, entrant and pooled records, which reach this data
# by a different path.
#
# **So the test is: hold the pre-2011 data out of the POOLED records only,
# leaving θ alone, and see whether the last 6.01 returns.** One run, more direct
# than the k* measurement it replaces, and it tests the half that is actually
# unexplained. **This entry is not evidence about the data; it is an admission
# that its effect is unexplained — and it is now half explained.**
# `HELD_BACK_OFF=1` lifts the gate for one run, so the diagnosis this entry is
# waiting for can be MEASURED without editing the file that records it. Sweeping
# `THETA_WINDOW` requires the held-back history to be live; editing the gate to
# do that, then editing it back, is how a measurement ends up taken against a
# tree nobody can reconstruct.
import os as _os_gate
_HELD_BACK_OFF = _os_gate.environ.get("HELD_BACK_OFF") == "1"

HELD_BACK: dict[tuple[str, str], str] = {} if _HELD_BACK_OFF else {
    (tag, code): "pre-2011 history, ingested and correct; held pending "
                 "diagnosis of a 13.65 CRPS regime effect, NOT because it "
                 "scores worse. Void once k* for the 2000 cycle is measured "
                 "(MODEL-LOG 1.154)"
    for tag in ("lge2000", "npe1999")
    # ⛔ JOHANNESBURG IS NOT HELD BACK, AND INCLUDING IT WAS A REGRESSION I
    # INTRODUCED. `lge2000_JHB` and `npe1999_approx_JHB` were the ONLY files of
    # their kind before 2026-09-01 and were already live — `KNOWN_ABSENT` listed
    # the other seven metros and never Johannesburg. Holding all eight back
    # therefore removed a transition the model had been using for weeks, and
    # KEY 4's folds are Johannesburg's: held-out NLL at fold 2016 went 1.1363 ->
    # 1.1777, an untradeable floor moving because of the gate rather than
    # because of the data. Caught by the suite, not by me — I had adjudicated
    # Keys 1 and 2 and not looked at 4.
    #
    # The seven metros below are the ones ingested on 2026-09-01 and never
    # before used. Holding those is the actual quarantine; holding Johannesburg
    # was an unmeasured change wearing the same name.
    for code in ("TSH", "EKU", "ETH", "CPT", "MAN", "NMA", "BUF")
}


def _citywide(path) -> dict[str, float]:
    """One election's citywide PR shares. **Deliberately not cached.**

    Widening the record from two metros to eight multiplied the file reads, and
    a path-keyed memo is the obvious fix. It was written, and it broke
    ``test_the_level_prior_reads_no_election_at_or_after_its_target`` — the
    guard that spies on file opens to prove the θ record never touches an
    election at or after its target. A memo makes the second target's reads
    invisible to it, so the leak test passes by seeing nothing rather than by
    seeing only clean files.

    That trade is the wrong way round in this repository. The temporal guards
    are the reason any score here can be believed, and the cost being bought
    with them is a few seconds of CSV parsing per run.
    """
    if _held_back(path):
        return {}
    shares, _roster = _citywide_and_roster(path)
    return shares


def _held_back(path) -> bool:
    """Is this election ingested but deliberately not yet fed to the model?"""
    parts = Path(path).name.split("_")
    tag = parts[0] if parts else ""
    code = next((x for x in parts if x.isupper() and len(x) == 3), "")
    return (tag, code) in HELD_BACK


def _citywide_and_roster(path) -> tuple[dict[str, float], set[str]]:
    """One pass: the PR shares AND every party name on any ballot.

    **One parse, because `residuals` needs both and the file is enormous.**
    Reading the target's result file twice — once for the outcome and once for
    the roster `run_model` drops absent parties by — took
    `theta_residual.residuals` from 43s to 113s. A VD-level result file is
    hundreds of thousands of rows.

    The two answers are deliberately different reads of it: the shares filter to
    `BallotType` PR because they are counting PR votes; the roster does not,
    because a party on either ballot is standing. Names are canonicalised once
    per DISTINCT name rather than once per row.

    Still **not cached** — see `_citywide`'s docstring; the temporal guards spy
    on file opens and a memo makes a leak invisible rather than absent.
    """
    counts: dict[str, int] = defaultdict(int)
    raw: set[str] = set()
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            reader = csv.DictReader(fh)
            # Both columns are read with `.get` or by key below; a renamed
            # `Party_Votes` would otherwise read as zero votes everywhere.
            for col in ("sPartyName", "Party_Votes"):
                if col not in (reader.fieldnames or ()):
                    raise KeyError(col)
            for row in reader:
                name = row["sPartyName"]
                raw.add(name)
                if row.get("BallotType") in (None, "", "PR"):
                    counts[P.canonical(name)] += int(
                        float(row.get("Party_Votes") or 0))
    except FileNotFoundError:
        return _absent(path), set()
    except KeyError as exc:
        # A RENAMED COLUMN IS NOT AN EMPTY ELECTION. This returned `{}` until
        # 2026-10-09, which every caller reads as "nobody voted" (BRIEF item 10).
        raise SystemExit(f"{path}: column {exc} missing — a renamed column, "
                         f"not an empty election") from None
    total = sum(counts.values())
    return ({k: v / total for k, v in counts.items()} if total else {},
            {P.canonical(n) for n in raw})


# ELECTION FILES THIS RECORD IS ALLOWED NOT TO HAVE.
# ---------------------------------------------------------------------------
# Keyed (archive tag, metro code) -> why. **A missing file NOT on this list is a
# refusal, not an empty dict**, which is the whole point of the table.
#
# Until 2026-08-23 `_citywide` returned `{}` for any file it could not open. The
# comment three lines below the call site said exactly what was wrong with that
# — *"a swallowed file error is indistinguishable from a deliberate exclusion,
# which is why it survived"* — and §1.43 fixed the one instance then known, a
# template that did not match `npe1999_approx_JHB`. The MECHANISM was left in,
# and it went on to eat twelve transitions: Mangaung's and Buffalo City's entire
# pre-2011 history vanished from `data/raw/elections/` between the run that
# measured §1.70's headline and the commit that published it, the record lost
# 16 coherent seats' worth of θ observations, and nothing anywhere went red.
# MODEL-LOG §1.75.
#
# Every absence here is DECLARED, with the reason, and each mirrors a refusal
# `ingest_historic.MUNI_HEAD` already makes for the same archive.
#
# ⛔ EMPTIED 2026-09-01, BECAUSE THERE IS NOTHING LEFT TO DECLARE. Every file
# the CALENDAR walk asks for is now on disk — all sixteen pre-2011 extracts,
# `lge2000` and `npe1999` for all eight metros, ingested and reconciled on
# 2026-08-31/09-01. Verified by walking `cityconfig.CALENDAR` against
# `data/raw/elections`: ten (transition, tag) pairs, eight metros each,
# **zero missing**.
#
# The fourteen entries removed here said two things that had both stopped being
# true, and each had already caused a wrong conclusion:
#
#   * `npe1999` for the seven non-Johannesburg metros — "predates every metro
#     but Johannesburg … MUNI_HEAD declares npe1999 for joburg ONLY". MUNI_HEAD
#     now declares all eight, each as the sum of the councils that amalgamated
#     into it in December 2000. 1999 predates every metro INCLUDING
#     Johannesburg, which is why all eight carry the `_approx` tag.
#   * `lge2000` for the same seven — "has never been ingested … Ekurhuleni and
#     eThekwini are ABSENT FROM THE ARCHIVE under any name". They were not
#     absent. They are in the 2000 archive as "EAST RAND" and "DURBAN", the
#     heads `npe2004` had carried all along; the note telling the next reader
#     not to look is what kept them missing. Corrected in `MUNI_HEAD`
#     2026-08-31.
#
# **AN ABSENCE AND A QUARANTINE ARE DIFFERENT FACTS AND THIS TABLE HOLDS ONLY
# THE FIRST.** Fourteen of these sixteen files are on disk and are NOT being
# fed to the model — that is `HELD_BACK` above, which means *present, correct,
# and withheld pending a stated diagnosis*. Merging the two would make a
# deliberate quarantine indistinguishable from a file nobody ever fetched,
# which is the confusion §1.43 and §1.75 both are.
#
# The table stays, empty, because `_absent` is the refusal path and it must
# keep a place to declare a real future absence. A file going missing now is a
# `SystemExit`, which is the intended behaviour.
KNOWN_ABSENT: dict[tuple[str, str], str] = {}


def _absent(path) -> dict[str, float]:
    """A missing election file: declared absence, or a named refusal.

    The archive tag and metro code are recovered from the FILENAME rather than
    passed in, so no caller can forget to ask. Every path this module builds
    comes from a CALENDAR template of the form ``<tag>_[approx_]<CODE>_vd_...``.

    **THE LARGEST ABSORBER IN THIS MODULE, AND IT IS NOT COUNTED**
    (NULL-RESULTS.md 4.3). A declared absence returns ``{}``, and an empty
    citywide dict contributes no θ or ρ observations at all — the twelve
    transitions §1.75 records disappeared exactly this way, with nothing
    anywhere going red. The refusal above closes the UNDECLARED case; the
    DECLARED case is still a silent subtraction from the evidence base, taken
    on every run, and its size is nowhere reported.

    It is not instrumented, deliberately, because the only home for the count
    is a parameter on :func:`theta_record` / :func:`local_record`, and
    ``tests/test_theta_prior.py`` monkeypatches ``theta_record`` with a stub of
    signature ``(target, codes)`` — an added keyword would be a ``TypeError``
    inside the test rather than a measurement. The count belongs in the same
    change that gives those two functions a diagnostic return.
    """
    name = Path(path).name
    parts = name.split("_")
    tag = parts[0] if parts else ""
    code = next((x for x in parts if x.isupper() and len(x) == 3), "")
    if (tag, code) in KNOWN_ABSENT:
        return {}
    raise SystemExit(
        f"levels: no election file at {path}\n"
        f"  archive {tag!r}, metro {code!r} — and that pair is NOT declared in "
        f"`levels.KNOWN_ABSENT`.\n"
        f"  This is a REFUSAL, not a missing feature. An absent input used to "
        f"return an empty dict here, which the θ and ρ records cannot tell "
        f"apart from a metro that contested nothing, so the observations "
        f"simply disappeared and every score moved with no warning. It has "
        f"happened twice: MODEL-LOG §1.43 and §1.75.\n"
        f"  Either restore the file — `.venv/bin/python src/ingest_historic.py "
        f"--city <city> --year {tag}` rebuilds the pre-2011 archives "
        f"deterministically — or, if the absence is intended, ADD IT TO "
        f"`KNOWN_ABSENT` WITH ITS REASON so the next reader knows it was a "
        f"decision.")


# LGE YEARS WHOSE TRANSITION IS EXCLUDED FROM THE θ RECORD.
# ---------------------------------------------------------------------------
# **AN EXPERIMENT HARNESS, NOT A LEVER, AND EMPTY BY DEFAULT** — with this empty
# the record is exactly what it was and no number moves.
#
# It exists to run one specific test (MODEL-LOG §1.74). §1.70 measured that
# ingesting the pre-2011 archive for seven metros cost **26 coherent seats** on
# the original nine city-years, and §1.72 identified the mechanism as the
# 2009→2011 transition, which carries COPE's collapse, the NFP's split from the
# IFP and the Independent Democrats merging into the DA. γ fold 3 IS
# `npe2009 → lge2011`, so the ingest imported seven metros' worth of that one
# transition into the retention prior at once.
#
# The narrow test this enables: drop 2011 from the θ RECORD while leaving γ fold
# 3 intact, so the sixteen city-years still run, and see whether the nine return
# toward 254. One flag, one run, and it discriminates — if the nine recover AND
# the sixteen hold, the panel doubling is bought without the regression.
#
# **Read via the environment, deliberately.** `compare_history` fans out over
# `ProcessPoolExecutor`, and a module constant set in the parent DOES NOT REACH
# A WORKER — children re-import `levels` fresh. That defect has bitten this
# repository before (`levels.SD_FLOOR`, MODEL-LOG §1.33) and `compare_history`
# now refuses a run that would hit it. An environment variable is inherited by
# every child, so the sweep is honest.
#
#     THETA_EXCLUDE_TARGETS=2011 .venv/bin/python src/compare_history.py
#
# If this test succeeds it must be PROMOTED to a declared `DEFAULTS` lever with
# a register row before anything ships on it. An env var is how you run an
# experiment, not how you carry a judgement.
import os as _os
THETA_EXCLUDE_TARGETS = frozenset(
    y for y in _os.environ.get("THETA_EXCLUDE_TARGETS", "").split(",") if y)


# THE TYPE A EVENT REGISTER — party lifecycle events that are not retention.
# ---------------------------------------------------------------------------
# PRE-REGISTERED IN MODEL-LOG §1.74, COMMITTED BEFORE ANY MEASUREMENT. Built
# from documented party events with dates; no residual was consulted. That
# matters because an independent review showed that dropping the five most
# extreme |log θ| observations *regardless of cause* gives sd 0.273 against this
# register's 0.221 — so a residual-built register cannot be told apart from
# plain outlier-dropping, and would not survive review.
#
# Powell & Tucker (BJPS 2014) call volatility from party ENTRY AND EXIT "Type A"
# and vote switching among existing parties "Type B". θ is a retention ratio, so
# it is meant to be Type B; Type A has its own machinery here (`pools.SPLITS`,
# `splinter_record`, the arrivals path). Most Type A never reaches this record —
# `theta_record` needs the party in BOTH elections with a positive base — so
# only three shapes survive that filter, and they are the whole register:
#
#   MERGER_ABSORBED         the target vote contains a party that no longer
#                           exists; the ratio is an acquisition, not retention
#   SPLIT_PARENT            a faction left between base and target; the ratio is
#                           a departure, not a failure to persuade
#   POST_FORMATION_COLLAPSE the base reading was a founding surge; the ratio
#                           measures a failure to institutionalise
#   LEADER_DEATH            personal-vehicle only. §1.73: the effect flips sign
#                           with institutionalisation, so it is not retention
#
# NOT IN THE REGISTER, deliberately, and each is a decision:
#   * the PA, which supplies the four largest residuals in the whole record
#     (θ 10.9 to 100.3). By Powell & Tucker it is Type B — it existed at both
#     elections and grew. Its extremes are a SMALL-DENOMINATOR problem (0.03% of
#     the vote) that `_reliability(share)` already handles. Including it would be
#     precisely the residual-driven choice §1.74 exists to avoid.
#   * the EFF, founded 2013 and contesting the 2014 NPE, so Type B by 2016. It
#     is eleven of the seventeen observations in the 5-15% bin, so excluding it
#     would empty the bin that carries the headline.
#
# Keyed by the TARGET LGE of the transition, because that is what
# `theta_record`'s loop iterates.
TYPE_A_EVENTS: dict[str, dict[str, str]] = {
    "2011": {
        # Independent Democrats merged into the DA: announced 15 Aug 2010,
        # complete before the May 2011 LGE. The DA's 2011 vote contains the
        # ID's; its 2009 base does not.
        "DA": "MERGER_ABSORBED",
        # NFP founded by Zanele Magwaza-Msibi, the IFP's National Chairperson,
        # January 2011 — four months before the LGE. Also in pools.SPLITS.
        "IFP": "SPLIT_PARENT",
        # Formed Dec 2008; the April 2009 NPE reading of 7.4% nationally was a
        # founding surge, and the party had fractured by 2011.
        "COPE": "POST_FORMATION_COLLAPSE",
    },
    "2016": {
        # Agang SA, founded by Mamphela Ramphele Feb 2013, contested the 2014
        # NPE, effectively defunct thereafter.
        "AGANG": "POST_FORMATION_COLLAPSE",
        # Amichand Rajbansi, founder and sole national figure, died 29 Dec 2011
        # — after the 2011 LGE, before 2016. A personal vehicle by §1.73.
        "MINORITY_FRONT": "LEADER_DEATH",
    },
    "2021": {
        # Herman Mashaba, the DA's own mayor of Johannesburg, resigned Oct 2019
        # and founded ActionSA in 2020 — between the 2019 NPE base and the 2021
        # LGE. Also in pools.SPLITS.
        "DA": "SPLIT_PARENT",
    },
}

# Off by default: with this False the record is exactly what it was and no
# number moves. Promoted to a declared lever only if §1.74's pass condition is
# met. Read via the environment because `compare_history` fans out over
# processes and a module constant set in the parent does not reach a worker
# (§1.33).
FILTER_TYPE_A = _os.environ.get("FILTER_TYPE_A", "").lower() in ("1", "true", "yes")

# TRANSITIONS THAT CROSS THE 2011 MUNICIPAL DEMARCATION.
# ---------------------------------------------------------------------------
# **AN EXPERIMENT HARNESS, OFF BY DEFAULT** — with `EXCLUDE_DEMARCATION_CROSSING`
# unset the record is exactly what it was and no number moves.
#
# It exists to test the FIRST of §1.70's two hypotheses, pre-registered in
# §1.80. Mangaung and Buffalo City are keyed on their pre-demarcation
# municipality codes `FS172` and `EC125` before 2011, and the 2011 demarcation
# moved municipal boundaries as well as wards — so for those two metros a ratio
# computed ACROSS 2011 divides a share of one area by a share of a different
# one. `DATA-QUALITY.md` item 13 documents the footprint change and Buffalo
# City's 5.1% -> 3.9% step, and left it unchased.
#
# **Only the crossing pair is listed.** MAN and BUF's 2004->2006 theta and
# 2000->2006 rho have BOTH endpoints inside the old footprint and are clean by
# this argument; §1.75's state B removed them too, which is why state B is an
# over-exclusion and not a test of this hypothesis. Keyed by (metro code, the
# LGE year the transition lands on) — 2011 for both theta (npe2009 -> lge2011)
# and rho (lge2006 -> lge2011).
DEMARCATION_CROSSING: frozenset[tuple[str, str]] = frozenset({
    ("MAN", "2011"),
    ("BUF", "2011"),
})

EXCLUDE_DEMARCATION_CROSSING = _os.environ.get(
    "EXCLUDE_DEMARCATION_CROSSING", "").lower() in ("1", "true", "yes")

# HOW MANY TRANSITIONS BACK THE theta RECORD REACHES.
# ---------------------------------------------------------------------------
# **AN EXPERIMENT HARNESS, UNLIMITED BY DEFAULT** — with `THETA_WINDOW` unset
# the record is exactly what it was and no number moves.
#
#     THETA_WINDOW=1 .venv/bin/python src/theta_residual.py
#
# `THETA_EXCLUDE_TARGETS` can only name absolute LGE years, which is the wrong
# shape for a RECENCY question: "keep the last k transitions" is relative to
# each target, and the same absolute year is the most recent transition for one
# target and three cycles back for another. That is why this exists separately.
#
# The question it was built for (MODEL-LOG §1.82): `theta_record` weights an
# observation by `_reliability(share)` — how much of the vote it was measured
# off — and by NOTHING ELSE, while rho, the spine and the poll aggregate all
# carry a recency term. A transition three cycles back is pooled as the equal
# of one cycle back.
THETA_WINDOW = int(_os.environ.get("THETA_WINDOW", "0") or 0)


def _crosses_demarcation(code: str, lge_year: str) -> bool:
    """Is this (metro, transition) one the 2011 demarcation makes incomparable?"""
    return (EXCLUDE_DEMARCATION_CROSSING
            and (code, str(lge_year)) in DEMARCATION_CROSSING)




def ballot_roster(path) -> set[str]:
    """The party NAMES on one result file's ballot. Names only, never votes.

    Nomination lists close and are published weeks before polling day, so who
    is standing is available to a forecaster; the results are not. `pools.
    contesting_parties` makes the same argument at greater length and reads the
    same column — it is kept there because it takes a `City`, and this takes a
    path, which is what the historical metro archive offers.

    No `BallotType` filter, deliberately: a party on either ballot is standing.
    `_citywide` filters to PR because it is counting PR votes; this is counting
    names.
    """
    return _citywide_and_roster(path)[1]


def absent_from_ballot(baseline: dict, roster) -> list[str]:
    """Parties holding baseline share that are NOT standing at the target.

    **One definition, two callers** (`montecarlo.run_model` builds the drawer's
    universe from this; `theta_residual.residuals` has to reproduce the same
    baseline or it measures an estimator the model does not run). The rule and
    its justification live in `run_model`'s comment: a party that is not on the
    ballot cannot take votes, and it is removed before θ, ρ, the spine, the
    pool fit and the seeds have seen it.

    Independents are never dropped — they are a slot, not a party, and no
    roster names them.

    An empty roster returns nothing to drop: a target not yet held has no
    published result file to read names from, and dropping the whole baseline
    because a file is missing would be catastrophic rather than conservative.
    """
    if not roster:
        return []
    return sorted(p for p in baseline
                  if p not in roster and p not in (_INDEPENDENT, "IND")
                  and baseline.get(p, 0.0) > 0)


def theta_record(target: cityconfig.Target,
                 codes=METRO_CODES) -> dict[str, list[tuple[float, float]]]:
    """Every observed national-to-local retention ratio before the target.

    One entry per party per metro per transition, as ``(ratio, share)`` where
    ``share`` is the national share the ratio was measured off.

    **There is no minimum share.** Parties below 0.2% of the national vote used
    to be dropped here, on the grounds that a party going from 30 votes to 90
    is not evidence that parties triple. That reasoning is right about the
    NUMBER and wrong about the PARTY: dropping it did not stop the model
    forming a view of that party, it just meant the view came from a constant
    somebody typed instead of from the party's own record. A hard cut also has
    a cliff at 0.2% that nothing in the data puts there.

    So every party with any history at all keeps its ratios, and ``share``
    travels with them so :func:`theta_prior` can weight by how much the ratio
    is worth. A party measured off 0.02% of the vote lands on the group centre
    because its own observations carry almost no weight — which is what the
    cut was reaching for, without the cliff and without handing the party to a
    judgement.
    """
    lge = sorted((y for y, e in cityconfig.CALENDAR.items()
                  if e.kind == "LGE" and e.results), key=int)
    # THETA_WINDOW: keep only the k most recent transitions before this target.
    # Computed per target, which is the whole point — see THETA_WINDOW.
    if THETA_WINDOW > 0:
        earlier = [y for y in lge if int(y) < int(target.year)]
        keep = set(earlier[-THETA_WINDOW:])
    else:
        keep = None
    out: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for year in lge:
        if int(year) >= int(target.year):
            continue                      # strictly before the target
        if keep is not None and year not in keep:
            continue                      # see THETA_WINDOW
        if year in THETA_EXCLUDE_TARGETS:
            continue                      # see THETA_EXCLUDE_TARGETS
        npe = cityconfig.preceding(year, "NPE")
        if not npe:
            continue
        # THE TEMPLATES COME FROM THE CALENDAR, not from a format string built
        # here. Until 2026-08-17 this line was
        # `f"data/raw/elections/npe{npe}_{code}_vd_party.csv"`, and the 1999
        # national election is on disk as `npe1999_approx_JHB_vd_party.csv` —
        # so the open failed, `_citywide` swallowed the FileNotFoundError and
        # returned {}, and the whole NPE1999 -> LGE2000 transition contributed
        # ZERO observations while `lge2000_JHB_vd_party_clean.csv` sat there.
        # A swallowed file error is indistinguishable from a deliberate
        # exclusion, which is why it survived. See MODEL-LOG §1.43.
        npe_tpl = cityconfig.CALENDAR[npe].results
        lge_tpl = cityconfig.CALENDAR[year].results
        if not npe_tpl or not lge_tpl:
            continue
        for code in codes:
            if _crosses_demarcation(code, year):
                continue              # see DEMARCATION_CROSSING
            before = _citywide("data/raw/elections/"
                               + npe_tpl.replace("{CODE}", code))
            after = _citywide("data/raw/elections/"
                              + lge_tpl.replace("{CODE}", code))
            _events = TYPE_A_EVENTS.get(year, {}) if FILTER_TYPE_A else {}
            for party in set(before) & set(after):
                if party in _events:
                    continue          # Type A, not retention. See TYPE_A_EVENTS
                if before[party] > 0:
                    out[party].append((after[party] / before[party],
                                       before[party]))
    return dict(out)


def result_path(target: cityconfig.Target,
                city: cityconfig.City) -> Path | None:
    """Where this city-year's VD result file would be, or None if unscheduled."""
    template = cityconfig.CALENDAR[target.year].results
    return city.path("raw", "elections", template) if template else None


def has_result_file(target: cityconfig.Target, city: cityconfig.City) -> bool:
    """Has this election been held and ingested?

    **The one definition of "is this a live forecast".** Two callers ask it:
    :func:`contestation`, to decide whether slates come from the result file or
    from a declaration, and ``montecarlo.run_model``, to decide whether a
    partial declaration may be topped up with a projection. Writing it out
    twice is the shape ``DUPLICATION-AUDIT.md`` exists for: a second copy that
    drifted would make a backtest eligible for gap-filling, which
    prereg/2026-09-23-declared-ward-slates.md forbids in P1.
    """
    path = result_path(target, city)
    return bool(path and path.exists())


def declared_contestation(target: cityconfig.Target, city: cityconfig.City,
                          ) -> tuple[dict[str, float], bool]:
    """The ward slates a NOMINATION LIST declares, and whether it is the whole
    ballot.

    Nomination lists close and are published before polling day, which is the
    fact :func:`contestation` is built on — but that function reads them out of
    the target's RESULT file, and a live forecast has none. From 2026-09-16 the
    certified per-ward lists have sat in the judgement file under
    ``[roster.wards]``, read only by ``pools`` for an arrival's reach, while the
    correction that is ABOUT slates went on projecting them from five years ago
    with ``contestation_expand``. MODEL-LOG §1.251.

    Returns ``({party: fraction of the city's wards}, complete)``, and
    ``({}, False)`` when nothing is declared.

    **The denominator is the CITY'S wards, never the wards the paste mentions.**
    That was already a defect once, in the ``reach`` derivation: counting
    against the named wards made a party's value a function of how far through
    the list the typist had got, maximal at the first party entered
    (POOLS-REEMIT-QUEUE entry 23, guard C).

    ⛔ **ZERO IS A FACT ONLY WHEN THE ROSTER SAYS IT IS THE WHOLE BALLOT.** Under
    ``complete = true`` a roster party with no ward list fields no ward
    candidates, and 0.0 is its true slate — Johannesburg 2026 has two such
    parties, CHANGE and PRO SOUTH AFRICA, which filed PR lists only. Under
    ``complete = false`` the list is half-typed and absence means UNKNOWN, so
    nothing is filled in and the caller keeps projecting those parties. A
    partial paste must fail safe: §1.175 measured the drop branch deleting
    2.4-2.9% of a city's vote when it fires on an incomplete list.
    """
    import pools as _pools          # lazy: `pools` imports this module

    b = ballots(target, city)
    if b.source != "declared":
        return {}, False
    wards = b.wards
    if not wards:
        return {}, b.complete
    ward_of, _registered = _pools.vd_map(city, target.year)
    city_wards = set(ward_of.values())
    # `vd_map` refuses rather than returning nothing, so this cannot be empty —
    # asserted rather than assumed, because a zero denominator here would
    # silently make every declared slate infinite.
    assert city_wards, (
        f"vd_map({city.slug}, {target.year}) returned no wards; a declared "
        f"slate cannot be a fraction of nothing.")
    slates = {party: len(ws) / len(city_wards)
              for party, ws in wards.items()}
    if b.complete:
        for party in b.parties:
            slates.setdefault(party, 0.0)
    return slates, b.complete


def projected_contestation(previous: dict[str, float],
                           expand: float) -> dict[str, float]:
    """A slate for a target whose nomination lists are not published yet.

    ``now = was + expand * (1 - was)`` — every party moves this fraction of the
    way from the slate it fielded last time to a full one, so a party that stood
    in 38% of wards gains far more than one that already stood in 95%. That
    party-specific asymmetry is the whole point: a uniform multiplier would
    carry no information, because :func:`montecarlo.blended_centres` applies
    contestation as the CHANGE ``now / was`` and a constant change is the same
    change for everyone.

    **Why this exists at all.** ``contestation`` reads who stood from the
    target's own result file. At a live forecast that file does not exist, so
    the change was silently 1.0 — an unexamined assumption that every party
    fields exactly the slate it fielded five years ago. It is not obviously
    wrong, and it is not obviously right: on the eight-metro record the median
    party expands its slate by 0.220 of the remaining distance and 65.5% expand
    at all. Now it is a declared number rather than a missing branch.

    **This is superseded, not supplemented, the moment real lists exist.**
    ``montecarlo`` calls this ONLY when ``contestation`` returned nothing for
    the target. When the IEC publishes 2026 candidate lists and they are
    ingested, ``contestation`` returns them, this function is not called, and
    ``contestation_expand`` becomes inert — which is the correct behaviour for a
    stand-in and is asserted in ``tests/test_levers_are_live.py``.

    Clipped to [0, 1] because a slate is a fraction of wards. ``expand = 0`` is
    exactly the previous behaviour.

    **NOT AN ABSORBER, and provably so** (NULL-RESULTS.md 4.3). The inner clip
    cannot bind on any input this function is given: for ``was ∈ [0, 1]`` and
    ``e ∈ [0, 1]``, ``was + e·(1 − was)`` lies in ``[was, 1] ⊆ [0, 1]``, so it
    is the identity on a well-formed slate and would only fire on a
    ``previous`` that was already out of range — which would be a defect in
    ``contestation``, not an absorption here. The OUTER clip on ``expand`` is a
    real clamp on a declared lever, and it is the one to look at if a sweep of
    ``contestation_expand`` outside [0, 1] returns a flat null. Neither is
    counted, because this function returns a bare dict with nowhere to put a
    count and its callers pin that shape.
    """
    if not previous:
        return {}
    e = float(np.clip(expand, 0.0, 1.0))
    return {party: float(np.clip(was + e * (1.0 - was), 0.0, 1.0))
            for party, was in previous.items()}


def local_record(target: cityconfig.Target,
                 codes=METRO_CODES) -> dict[str, list[tuple[float, float]]]:
    """Every observed LOCAL-to-LOCAL retention ratio before the target.

    ρ is θ's opposite number: a party's share at one local election over its
    share at the local election before it, as ``(ratio, share)`` where ``share``
    is the earlier local share the ratio was measured off. It is what moves a
    party's *own* last local result forward five years, and it is the second of
    the two routes :func:`spine` weighs against each other.

    Consecutive LGE pairs only, both strictly before the target — pairing 2011
    with 2021 would measure ten years of drift and call it five.
    """
    lge = sorted((y for y, e in cityconfig.CALENDAR.items()
                  if e.kind == "LGE" and e.results), key=int)
    out: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for earlier, later in zip(lge, lge[1:]):
        if int(later) >= int(target.year):
            continue                      # strictly before the target
        for code in codes:
            if _crosses_demarcation(code, later):
                continue              # see DEMARCATION_CROSSING
            before = _citywide(
                f"data/raw/elections/lge{earlier}_{code}_vd_party_clean.csv")
            after = _citywide(
                f"data/raw/elections/lge{later}_{code}_vd_party_clean.csv")
            for party in set(before) & set(after):
                if before[party] > 0:
                    out[party].append((after[party] / before[party],
                                       before[party]))
    return dict(out)


def _reliability(share: float) -> float:
    """How much one observed ratio is worth, on 0-1, from what it was measured off.

    ``share / (share + RELIABILITY_HALF)``: an observation taken off the old
    0.2% cut is worth half of one taken off a large party, 2% is worth 0.91,
    0.02% is worth 0.09. Continuous, so nothing changes character at a
    threshold, and monotone in the only thing that governs the noise — how
    many votes the ratio was computed from.
    """
    return float(share) / (float(share) + RELIABILITY_HALF)


def size_sd_raw(size: float, sd_fit: dict) -> float:
    """The size group's width in log θ at ``size``, before the clamp.

    ``sd_fit`` is :func:`theta_prior`'s ``groups["sd_fit"]``: either the
    dispersion line ``{"route": "size_fit", "slope", "intercept"}``, evaluated
    as ``exp(½(intercept + slope·log size))`` with ``size`` floored at 1e-5, or
    ``{"route": "pooled", "pooled"}``, one width for every size.
    """
    if sd_fit.get("route") == "pooled":
        return float(sd_fit["pooled"])
    x = np.log(max(size, 1e-5))
    return float(np.exp(0.5 * (sd_fit["intercept"] + sd_fit["slope"] * x)))


def size_sd(size: float, sd_fit: dict) -> float:
    """The size group's width (the RANGE of BRIEF item 17), clamped to
    ``[SD_FLOOR, SD_CEILING]``. One definition: :func:`theta_prior` gives every
    party with a baseline this width, and ``montecarlo.level_shock_sd`` gives
    it to a party with no record of its own, at its own size. Since 2026-10-12
    that reaches the draw only under ``draw_law = "incumbent"``: the universal
    draw's widths come from the width record (``src/width_record.py``)."""
    return float(np.clip(size_sd_raw(size, sd_fit), SD_FLOOR, SD_CEILING))


def theta_prior(target: cityconfig.Target, baseline: dict[str, float],
                codes=METRO_CODES, h: float = float("inf"),
                ) -> tuple[dict[str, tuple], dict]:
    """Per-party (low, mode, high) on θ, and the groups they were drawn from.

    A party's own log-mean is shrunk toward the size centre by
    ``worth / (worth + SHRINK)``, and the width comes from the group's
    log-spread. The size centre is evaluated at the party's CURRENT size, its
    share of ``baseline`` (BRIEF item 11, 2026-10-09), through
    :func:`_shrink_one`, the helper :func:`_shrunk` also calls; a party in the
    record with no baseline keeps its observed size and is counted in the
    ``shrink`` block's ``size_fallback``. ``h`` is the θ size window (BRIEF
    item 16, :func:`size_window`), the same value ``run_model`` passes to
    :func:`spine`; the default, ``inf``, filters nothing. The band is the 10th to
    90th percentile of that lognormal, so it is wide where the record is wide
    and nothing sits at probability zero.

    **The second return value carries an ``absorption`` block** (NULL-RESULTS.md
    4.3) reporting what each absorbing stage here ate: the
    ``[SD_FLOOR, SD_CEILING]`` clamp, the shrink toward the size centre, and
    which branch of the dispersion fit and of the centre ran. It is written and
    never read, so it moves no number; it exists so a null measured downstream
    of this layer can be labelled ``ABSORBED:<stage>`` instead of ``INERT``.

    **The two early returns absorb everything and report nothing**, by
    construction: an empty record, or a record whose observations are worth
    nothing, returns ``({}, {})`` and there is no block to carry a count. The
    caller's ``if _prior:`` gate is the only thing that sees it.
    """
    record = theta_record(target, codes)
    if not record:
        return {}, {}

    # The weighted common centre. Weighted by what each observation is worth,
    # which is what replaced the 0.2% cut — an unweighted mean over every ratio
    # would let a party that went from 30 votes to 90 move the centre as far as
    # the ANC does.
    #
    # THIS COMMENT USED TO OPEN "the record says the trend does not vary with
    # size", and that claim is false: on eight metros the median θ runs 1.31
    # below 0.2% of the vote against 0.94 above 15%. `size_centre` exists
    # because of it. `mu_all` is kept as the fallback for when the size fit
    # cannot be made, and as the reported group figure; the shrink target below
    # is the size centre, as it is in `_shrunk`.
    everything = [obs for ratios in record.values() for obs in ratios]
    ratios_all = np.array([r for r, _ in everything])
    weights_all = np.array([_reliability(s) for _, s in everything])
    if weights_all.sum() <= 0:
        return {}, {}
    mu_all = float(np.average(np.log(ratios_all), weights=weights_all))

    # Dispersion IS a function of size, so fit it as one — against the COMMON
    # centre, not each party's own. Two earlier attempts used within-party
    # deviation and both came out too narrow (sd 0.15 for a large party where
    # the binned record shows 0.26), because with two or three observations a
    # party's own mean sits almost on top of them. What a forecast faces is the
    # total spread: we do not know a party's centre either, and the shrinkage
    # above leans on the common one. Erring wide is also the right way to be
    # wrong here — this model's measured failure has always been overconfidence.
    xs, ys = [], []
    for party, ratios in record.items():
        size = baseline.get(party, 0.0)
        if size <= 0:
            continue
        for r, _share in ratios:
            xs.append(np.log(size))
            ys.append((np.log(r) - mu_all) ** 2)
    # THE RAW WIDTH AND THE CLAMPED ONE ARE NOW SEPARATE FUNCTIONS, so the
    # clamp can be COUNTED rather than inferred. `sd_for` is `clip(sd_raw)` and
    # nothing else, so no value moves; what changes is that the quantity the
    # clamp ate is observable. Before this, a party pinned to `SD_FLOOR` was
    # indistinguishable from a party the fit happened to place at 0.15, and the
    # only account of it was the call site counting `abs(v - SD_FLOOR) < 1e-12`
    # in `montecarlo`'s `10_theta_prior` trace — which can see the floor, cannot
    # see the ceiling, and cannot see HOW FAR anything was moved.
    if len(xs) >= 6:
        slope, intercept = np.polyfit(xs, np.log(np.maximum(ys, 1e-6)), 1)
        sd_route = "size_fit"
        # NOT corrected by LOG_CHI2_BIAS, deliberately — see the constant.
        sd_fit = {"route": "size_fit", "slope": float(slope),
                  "intercept": float(intercept)}
    else:
        # ddof=1 OVER ONE OBSERVATION IS `nan`, AND IT IS SILENT (§1.97 F21).
        # `np.clip` propagates it, `sd_for` hands the same nan to every party,
        # and `make_drawer` reads `sd_measured.get(party, sd_default)` with the
        # key PRESENT — so the default never fires and the nan reaches the draw.
        # Refused rather than defaulted: a typed width here would be a
        # judgement call and belongs in JUDGEMENT-CALLS.md, not in a fallback.
        #
        # THE REFUSAL IS UNREACHABLE ON THE ARCHIVE, and saying so is the point
        # of it. `theta_record` reads `target.year` and `codes` and never
        # `target.city`, so the record is IDENTICAL for all eight metros: 175
        # observations at 2016, 272 at 2021, 410 at 2026 (measured by calling
        # `theta_record` directly). Narrowed to a single metro code — the only
        # narrowing any caller can do, via `theta_residual.py` — the thinnest
        # non-empty record on the archive is 7, and 7 again under
        # THETA_WINDOW=1. An empty record returns earlier and never arrives
        # here. §1.121
        if len(ratios_all) < 2:
            # `getattr`, because `theta_prior` passes `target` straight to
            # `theta_record` and never touches it otherwise — the tests hand it
            # a plain string for exactly that reason. A refusal that raises a
            # DIFFERENT error while reporting the first is worse than useless.
            raise ValueError(
                f"the θ record holds {len(ratios_all)} observation(s) before "
                f"{getattr(target, 'year', target)}: sd(log θ) is undefined "
                f"and every party's band would come back nan in silence. "
                f"See MODEL-LOG §1.121.")
        pooled = float(np.std(np.log(ratios_all), ddof=1))
        sd_route = "pooled"
        # No correction here: `pooled` is sd(log ratios) computed directly,
        # not recovered from a fit to squared residuals, so it carries no
        # log-chi-square bias.
        #
        # SIZE DOES NOT ENTER, and that is this branch's absorption: every
        # party on the ballot is handed one width. `sd_route` reports which
        # branch ran, because a size sweep against a run in this branch is
        # a null with a known cause and not a finding.
        sd_fit = {"route": "pooled", "pooled": pooled}

    # ONE DEFINITION OF THE SIZE-GROUP WIDTH (BRIEF item 17): the fit is a
    # value (`sd_fit`), and `size_sd_raw`/`size_sd` evaluate it. The drawer
    # calls the same function for a party with no record of its own.
    def sd_raw(size: float) -> float:
        return size_sd_raw(size, sd_fit)

    def sd_for(size: float) -> float:
        return size_sd(size, sd_fit)

    # PATH ONE — a party WITH history. Its own log-mean, shrunk toward the
    # common centre by how much that history is worth rather than by how many
    # rows of it there are: three ratios measured off 0.02% of the vote are
    # three weak statements, not three strong ones, and the party ends up on
    # the group centre. A party with no ratios of its own but a baseline to
    # apply θ to (MK in 2026 — a national vote, no local election yet) IS this
    # path, sitting at the centre with the group's spread.
    #
    # PATH TWO — a party with NO baseline at all is not here and cannot be:
    # θ converts a national share into a local one and there is no national
    # share to convert. It is an arrival, and ``pools.arrival_rules`` sizes it
    # from the arrival record. ``montecarlo.blended_centres`` routes it there.
    # ONE ESTIMATOR, NOT TWO. Until 2026-08-18 this shrank toward the flat
    # `mu_all` while `_shrunk` — the estimator the spine uses for the same
    # quantity — shrank toward `size_centre`. They disagreed by construction
    # (ANC 0.869 against 0.862, PA 1.115 against 1.197) and the register carried
    # that at 🔴 as "at least one is wrong".
    #
    # The flat one was the wrong one, and for a reason that matters: a common
    # centre hands every party the same retention, when the record says small
    # parties GAIN going into a local election and large ones lose. Erasing that
    # works against exactly the mid-ballot parties this model under-forecasts.
    #
    # Changing it moves NOTHING, which is why it could be done as a correctness
    # fix rather than a scored change: the mode this function returns is
    # consumed at no runnable target. The `blended_centres` branch that reads it
    # is the one for parties the spine cannot reach, and the spine reaches every
    # party at every target measured; the by-election clamp reads the band as
    # `low/mid` and `high/mid`, so a shift in the centre cancels out of it.
    # Verified by shifting the whole band ×3 at 2021 and 2026: byte-identical
    # seat draws at both. MODEL-LOG §1.49.
    fit = size_centre(record)

    def _centre_for(size: float) -> float:
        if not fit:
            return mu_all
        return float(fit[0] + fit[1] * np.log(max(size, 1e-6)))

    # ABSORPTION ACCOUNTING (NULL-RESULTS.md 4.3). Two of this function's three
    # stages are attractors, and until now neither declared how much it ate:
    #
    #   * the [SD_FLOOR, SD_CEILING] clamp on the fitted width — §1.59 measured
    #     that the FLOOR, not the fit, sets the width on most observations, so
    #     a change to the dispersion fit is absorbed for those parties and a
    #     sweep of it returns a null with a location rather than a finding;
    #   * the shrink toward the size centre — a party whose record is worth
    #     little is pulled almost entirely onto the centre, so a change to its
    #     own observations does not reach the mode.
    #
    # `absorbed / offered` is the attractor strength: at 1.0 the stage ate
    # everything it was given and is an attractor by definition. NOTHING HERE
    # IS READ BACK; every counter is write-only, which is what makes the
    # accounting number-neutral.
    sd_clip = {"route": sd_route, "n": 0, "at_floor": 0, "at_ceiling": 0,
               "nonfinite": 0, "mass": 0.0}
    shrink = {"target": "size_centre" if fit else "flat_common_centre",
              "n_shrunk": 0, "n_all_centre": 0, "offered": 0.0,
              "absorbed": 0.0, "size_fallback": 0, "outside_window": 0,
              "window": _json_h(h)}
    no_baseline = 0

    priors: dict[str, tuple] = {}
    worth_of: dict[str, float] = {}
    for party in set(record) | set(baseline):
        size = baseline.get(party, 0.0)
        sd = sd_for(size)
        raw = sd_raw(size)
        sd_clip["n"] += 1
        if size <= 0.0:
            # No national share to be sized off: the width is the fit
            # extrapolated to `log(1e-5)` and the centre to `log(1e-6)`. Two
            # different floors for the same missing quantity, which is worth
            # knowing and is not this change's to alter.
            no_baseline += 1
        if not np.isfinite(raw):
            sd_clip["nonfinite"] += 1
        elif raw < SD_FLOOR:
            sd_clip["at_floor"] += 1
            sd_clip["mass"] += SD_FLOOR - raw
        elif raw > SD_CEILING:
            sd_clip["at_ceiling"] += 1
            sd_clip["mass"] += raw - SD_CEILING
        own = record.get(party, [])
        if own:
            # GROWTH AT CURRENT SIZE (BRIEF item 11, 2026-10-09). The shrink
            # target is the size centre at the party's size NOW, its share of
            # the baseline, for every party. Until this batch it was taken at
            # the size the party's own ratios were measured off, which hands a
            # party that grew the multiplier of the party it used to be (the
            # PA's θ, measured off 0.014%-0.29% against a current 2.9%: item 7).
            # A party in the record with no baseline has no current size, keeps
            # the observed one, and is counted in `size_fallback`. The body is
            # `_shrink_one`, which `_shrunk` also calls: one estimator (§A26).
            if size > 0.0:
                at, window = size, h
            else:
                at, window = _observed_size(own), float("inf")
                shrink["size_fallback"] += 1
            mu, worth, own_mu, centre = _shrink_one(own, at, fit, mu_all,
                                                    window)
            worth_of[party] = worth
            if worth == 0.0:
                shrink["outside_window"] += 1
            weight = worth / (worth + SHRINK)
            shrink["n_shrunk"] += 1
            shrink["offered"] += abs(own_mu - centre)
            shrink["absorbed"] += (1 - weight) * abs(own_mu - centre)
        else:
            mu = _centre_for(size)
            # A party with no record of its own is 100% absorbed: its mode IS
            # the centre. Counted separately because it does not appear in
            # `offered` at all — there was nothing to offer.
            shrink["n_all_centre"] += 1
        priors[party] = (float(np.exp(mu - 1.2816 * sd)), float(np.exp(mu)),
                         float(np.exp(mu + 1.2816 * sd)))
    sd_clip["share"] = ((sd_clip["at_floor"] + sd_clip["at_ceiling"])
                        / sd_clip["n"]) if sd_clip["n"] else 0.0
    shrink["share"] = (shrink["absorbed"] / shrink["offered"]
                       if shrink["offered"] > 0 else 0.0)
    return priors, {
        # `weighted_geomean`, NOT `median` — renamed 2026-08-28 (§1.97 F24,
        # §1.121). `exp(mu_all)` is exp of the reliability-weighted mean of
        # log θ, i.e. the weighted GEOMETRIC MEAN of the record, not an order
        # statistic of it. It is also the median of the LogNormal(mu_all, sd)
        # this function goes on to fit, which is why the old name survived —
        # but it sat beside `n` and `effective_n`, which describe THE RECORD,
        # so that is not how it read. Not a published key: it appears nowhere
        # in `forecast_summary.json` (checked by recursive walk), in `content/`
        # or in `site/`; the `median` that IS published is a seat median on a
        # different dict.
        "centre": {"n": len(everything),
                   "weighted_geomean": float(np.exp(mu_all)),
                   "effective_n": float(weights_all.sum())},
        "spread": {"at_0.1%": sd_for(0.001), "at_1%": sd_for(0.01),
                   "at_10%": sd_for(0.10), "at_40%": sd_for(0.40)},
        # What each party's own θ record is WORTH, on the same 0-1-per-
        # observation scale the shrinkage uses. This is the quantity the spine
        # blend is keyed on, and it is reported rather than recomputed so the
        # weight and the shrinkage can never be keyed on different numbers.
        # Over the observations inside the size window only (BRIEF item 16),
        # which is what `_shrunk` reports, since both come from `_shrink_one`.
        "worth": dict(worth_of),
        # Per-party log-spread, so the draw can use the width that was measured
        # instead of a triangular fitted to the same band's endpoints.
        "sd": {party: float(sd_for(baseline.get(party, 0.0)))
               for party in priors},
        # The width fit itself, as a value `size_sd` evaluates (BRIEF item
        # 17): `make_drawer` sizes a party with no record of its own with it,
        # at that party's own size, through the same function as `sd` above.
        "sd_fit": dict(sd_fit),
        # WHAT THIS FUNCTION ABSORBED. See the block above the priors loop.
        # `sd_clip.share` is the fraction of parties whose width is set by the
        # clamp and not by the fit; `shrink.share` is the fraction of the
        # distance between a party's own mean and its centre that the shrink
        # took back. A stage at share ≈ 1.0 is an attractor and any null
        # measured through it is ABSORBED, not INERT.
        "absorption": {
            "sd_clip": sd_clip,
            "shrink": shrink,
            "no_baseline": no_baseline,
        },
    }


def size_centre(record: dict[str, list[tuple[float, float]]]):
    """The centre θ shrinks TOWARD, as a function of how big the party is.

    ``levels.py`` has said since it was written that "size predicts how
    UNCERTAIN a party is, not how it trends — the centre hardly moves (0.84 to
    0.93 across every band)". That was measured on TWO metros, n=51. On eight
    metros, n=235, it is not true::

        national size before    n    median θ   geometric mean
        < 0.2%                 75      1.31         1.53
        0.2 - 0.5%             57      1.03         0.98
        0.5 - 2%               44      1.04         0.90
        2 - 10%                18      1.05         0.90
        > 10%                  41      0.94         0.95

    Small parties GAIN going into a local election and large ones lose, which is
    Reif and Schmitt's second-order effect stated in this archive's own numbers,
    and which a single common centre erases. The model was applying 0.83 to 0.96
    to every party at once, so the parties it under-forecasts most were being
    handed the large-party number.

    Fitted as ``log θ = a + b·log(size)`` on the same reliability weights the
    shrinkage uses — correlation −0.27, and a gradient from about 1.10 at a
    twentieth of a per cent to 0.89 at thirty. The R² is 0.04, which is the
    honest figure: this moves the CENTRE by a quarter across the ballot and
    explains almost none of the variance around it. Both facts matter, and the
    second is why the dispersion stays where it is.

    Returns ``(a, b)``; ``centre(size) = exp(a + b·log(size))``.

    **Fitted on one size, evaluated at another.** Each observation enters the
    fit at the size its ratio was measured off, because that is the size at
    which it happened. The consumers (:func:`_shrink_one`, so both
    :func:`_shrunk` and :func:`theta_prior`) evaluate the line at the party's
    CURRENT size, since BRIEF item 11 (2026-10-09).
    """
    obs = [(np.log(max(sz, 1e-6)), np.log(r))
           for v in record.values() for r, sz in v if r > 0 and sz > 0]
    if len(obs) < 20:
        return None
    x = np.array([o[0] for o in obs])
    y = np.array([o[1] for o in obs])
    # UNWEIGHTED, and the weight is not computed at all (§1.97 F25). It used to
    # be — `w = np.sqrt(...)` sat here and reached nothing, which reads as an
    # oversight rather than as the decision below. The decision is the comment;
    # the dead array was only ever evidence that somebody had considered it.
    #
    # The reliability weight exists to stop a party that went from
    # 30 votes to 90 moving a party's OWN mean, and it is right for that. Here
    # it is wrong: the quantity being fitted is how the centre varies WITH SIZE,
    # and down-weighting the small end removes the observations that identify
    # it. Weighted, the gradient runs 1.10 to 0.89; unweighted, 1.31 to 0.94,
    # which is what the size bands actually show.
    b, a = np.polyfit(x, y, 1)
    return float(a), float(b)


def _observed_size(obs: list[tuple[float, float]]) -> float:
    """The reliability-weighted size a party's ratios were measured off."""
    w = [_reliability(s) for _, s in obs]
    return float(np.average([sz for _, sz in obs], weights=w))


def _in_window(obs: list[tuple[float, float]], size: float,
               h: float) -> list[tuple[float, float]]:
    """The observations measured off a size within ``h`` (log units) of ``size``.

    No filter where ``h`` is infinite or ``size`` is not positive (BRIEF item
    16: the window is centred on the party's current size, and a party with
    no current size on the route is read by no level).
    """
    if not np.isfinite(h) or size <= 0.0:
        return list(obs)
    centre = np.log(size)
    return [(r, sz) for r, sz in obs
            if sz > 0.0 and abs(np.log(sz) - centre) <= h]


def _shrink_one(obs: list[tuple[float, float]], size: float, fit,
                mu_all: float, h: float = float("inf"),
                ) -> tuple[float, float, float, float]:
    """One party's shrunk log-mean: ``(mu, worth, own, target)``.

    ``own`` is the reliability-weighted mean of ``log r`` over ``obs``;
    ``worth`` is the sum of the reliabilities; ``target`` is the size centre
    evaluated at ``size`` (the flat ``mu_all`` where ``fit`` is None); and
    ``mu = w·own + (1 − w)·target`` with ``w = worth / (worth + SHRINK)``.

    **``size`` is the party's CURRENT size** on the route the record belongs
    to (its national share for θ, its previous local share for ρ), since
    BRIEF item 11 (2026-10-09). The size centre says how parties of a given
    size retain their vote; the size that matters is the one the party has
    at the target, not the one its historical ratios were measured off.

    **Only observations from a similar size count** (BRIEF item 16): those
    measured off a size within ``h`` of ``size`` (:func:`_in_window`). If none
    survive, the party has no own record on this route: ``worth`` is 0 and
    ``mu`` is the target, the size centre at its current size. ``worth`` is
    over the surviving observations only, so the spine's blend weight loses
    the filtered record's pull as well. ``h`` is :func:`size_window`'s; at
    ``h = inf`` nothing is filtered (item 11a alone).

    The per-party body of both :func:`_shrunk` and :func:`theta_prior`, so
    the spine's estimator and the θ prior's cannot drift apart (§A26).
    """
    target = (float(fit[0] + fit[1] * np.log(max(size, 1e-6)))
              if fit else mu_all)
    obs = _in_window(obs, size, h)
    if not obs:
        return target, 0.0, target, target
    w = [_reliability(s) for _, s in obs]
    worth = float(sum(w))
    weight = worth / (worth + SHRINK)
    own = float(np.average([np.log(r) for r, _ in obs], weights=w))
    return weight * own + (1 - weight) * target, worth, own, target


def _shrunk(record: dict[str, list[tuple[float, float]]],
            report: dict | None = None, *,
            current: dict[str, float], h: float = float("inf"),
            ) -> tuple[dict[str, float], float, dict[str, float]]:
    """Per-party log-mean shrunk to the size centre at its current size, and the worth.

    The estimator :func:`theta_prior` uses on θ, extracted so ρ gets exactly the
    same treatment. If the two routes were shrunk differently, the comparison
    between them in :func:`spine` would be measuring the estimators rather than
    the evidence. The per-party body is :func:`_shrink_one`.

    ``current`` is each party's size now on this record's route: the national
    baseline for θ, the previous local result for ρ (BRIEF item 11). The size
    centre is evaluated there. A party in ``record`` with no positive
    ``current`` size keeps the reliability-weighted size of its own
    observations and is counted in ``report["size_fallback"]``; no level reads
    such a party, because the spine consults ``mu_t`` only where the national
    share is positive and ``mu_r`` only where the local share is.

    **``report`` is an absorption account, written and never read.** The return
    is a three-tuple that two test files pin exactly (``({}, 0.0, {})`` on an
    empty record), so the account cannot travel in it; :func:`spine` passes a
    dict in and forwards it into its own diagnostic block. Filled with:

    * ``target`` — the centre shrunk toward, ``size_centre`` or, where the
      record has under twenty usable observations, the flat common mean. The
      flat fallback absorbs the size signal ENTIRELY, which is the thing
      `size_centre` was fitted to deny, so it is named rather than inferred.
    * ``offered`` — Σ |own mean − centre|, how far the parties' own evidence
      asked to move them off the centre;
    * ``absorbed`` — Σ (1 − weight)·|own mean − centre|, how much of that the
      shrink took back, and ``share`` = absorbed / offered. At share ≈ 1 this
      is an attractor and a change to a party's own observations cannot reach
      the level.
    * ``size_fallback`` — parties shrunk at their observed size because
      ``current`` gives them none (no window is applied to them);
    * ``at_size_centre`` — parties in ``current`` with no record at all,
      returned at the size centre for their current size (BRIEF item 17);
      only where the size fit exists;
    * ``outside_window`` — parties whose every observation lay outside the
      size window ``h`` (BRIEF item 16), so their ``mu`` is the size centre
      at their current size and their ``worth`` is 0; ``window`` is ``h``.
    """
    if report is not None:
        report.update({"n": 0, "target": None, "offered": 0.0,
                       "absorbed": 0.0, "share": 0.0, "empty": True,
                       "size_fallback": 0, "outside_window": 0,
                       "at_size_centre": 0, "window": _json_h(h)})
    everything = [obs for obs in (o for v in record.values() for o in v)]
    if not everything:
        return {}, 0.0, {}
    ratios = np.array([r for r, _ in everything])
    weights = np.array([_reliability(s) for _, s in everything])
    if weights.sum() <= 0:
        return {}, 0.0, {}
    mu_all = float(np.average(np.log(ratios), weights=weights))
    fit = size_centre(record)
    offered = absorbed = 0.0
    size_fallback = outside_window = 0
    mus: dict[str, float] = {}
    worth: dict[str, float] = {}
    for party, obs in record.items():
        # Shrink toward the centre for a party THIS SIZE NOW, not toward one
        # number for the whole ballot and not toward the size it used to be.
        size = float(current.get(party, 0.0) or 0.0)
        window = h
        if size <= 0.0:
            size = _observed_size(obs)
            size_fallback += 1
            window = float("inf")
        mus[party], worth[party], own, target = _shrink_one(
            obs, size, fit, mu_all, window)
        if worth[party] == 0.0:
            outside_window += 1
        weight = worth[party] / (worth[party] + SHRINK)
        offered += abs(own - target)
        absorbed += (1 - weight) * abs(own - target)
    # NO RECORD OF ITS OWN: THE SIZE GROUP'S AVERAGE AT ITS CURRENT SIZE (BRIEF
    # item 17, the "11b" half of item 11). A party with a current size on this
    # route and no observations takes the size centre at that size, which is
    # what `theta_prior` already gave it; before this the spine handed it the
    # flat common mean (`mu_t.get(party, c_t)`), the one place the size signal
    # was still erased (MK at 2026). Only where the size fit exists: without
    # it the target IS the flat mean and the spine's fallback says so
    # (`centre_fallback`). No worth is entered: the party has no evidence.
    at_size_centre = 0
    if fit:
        for party, size in current.items():
            if party not in mus and size and size > 0.0:
                mus[party] = float(fit[0] + fit[1] * np.log(max(size, 1e-6)))
                at_size_centre += 1
    if report is not None:
        report.update({
            "n": len(record),
            "target": "size_centre" if fit else "flat_common_centre",
            "offered": float(offered), "absorbed": float(absorbed),
            "share": float(absorbed / offered) if offered > 0 else 0.0,
            "empty": False,
            "size_fallback": size_fallback,
            "outside_window": outside_window,
            "at_size_centre": at_size_centre,
            "window": _json_h(h),
        })
    return mus, mu_all, worth


def _json_h(h: float):
    """A window as JSON can carry it: ``"inf"`` for no filter."""
    return float(h) if np.isfinite(h) else "inf"


def _t_upper(alpha: float, df: int) -> float:
    """Student's t upper quantile: ``t`` with ``P(T > t) = alpha`` on ``df``.

    Arithmetic, not judgement (scipy is not a dependency here). For integer
    ``df`` the two-sided probability ``A(t) = P(|T| < t)`` has a closed form in
    ``θ = atan(t / √df)`` (Abramowitz and Stegun 26.7.3, 26.7.4); it rises
    monotonically in ``θ`` on ``(0, π/2)``, so ``A = 1 − 2·alpha`` is solved by
    bisection on ``θ``. ``tests/test_spine.py`` checks it against the
    published table values.
    """
    df = int(df)
    if df < 1 or not 0.0 < alpha < 0.5:
        raise ValueError(f"t quantile needs df >= 1 and 0 < alpha < 0.5, "
                         f"got df={df}, alpha={alpha}")
    goal = 1.0 - 2.0 * alpha

    def two_sided(theta: float) -> float:
        s, c = np.sin(theta), np.cos(theta)
        if df % 2 == 1:
            if df == 1:
                return 2.0 * theta / np.pi
            term = total = 1.0
            for k in range(1, (df - 3) // 2 + 1):
                term *= (2.0 * k) / (2.0 * k + 1.0) * c * c
                total += term
            return 2.0 / np.pi * (theta + s * c * total)
        term = total = 1.0
        for k in range(1, (df - 2) // 2 + 1):
            term *= (2.0 * k - 1.0) / (2.0 * k) * c * c
            total += term
        return s * total

    lo, hi = 0.0, np.pi / 2
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if two_sided(mid) < goal:
            lo = mid
        else:
            hi = mid
    return float(np.sqrt(df) * np.tan(0.5 * (lo + hi)))


def size_window(target: cityconfig.Target, record_fn, codes=METRO_CODES,
                record: dict | None = None) -> tuple[float, dict]:
    """The size window ``h`` for one record at ``target``, derived from data.

    BRIEF item 16 (owner, 2026-10-09): a party's own growth record counts only
    from elections where it stood at a size similar to now, and the
    similarity window is derived, not typed. Called once per record (``θ``
    through :func:`theta_record`, ``ρ`` through :func:`local_record`), so each
    route gets its own window. The rule is JUDGEMENT-CALLS §A52, written down
    (2026-10-09) before it was run on the archive.

    The derivation, a walk forward through the calendar:

    1. The LGE targets ``T_1 < … < T_k ≤ target``. ``record_fn(T_j)`` holds
       only transitions strictly before ``T_j``, so nothing at or after
       ``target`` is read (``test_temporal`` watches the file opens).
    2. The NEW observations at ``T_j`` are ``record_fn(T_j)`` minus
       ``record_fn(T_{j−1})``, as multisets per party. The new observations
       of one step are one CYCLE: the cluster.
    3. Each new observation ``(r, sz)`` of party ``p`` is predicted from
       ``p``'s record at ``T_{j−1}`` by :func:`_shrink_one` with current size
       ``sz`` and window ``h``, the size-centre fit and the common mean also
       taken from the record at ``T_{j−1}``. A party with no earlier record
       is predicted at the size centre (the same for every ``h``).
    4. The score at ``h`` is the reliability-weighted mean of
       ``|ln r − predicted|`` over every new observation of every party
       (``errors``). ``best`` is the grid value with the lowest score.
    5. For each grid value ``h ≥ best``, the paired difference per
       observation is ``d_i = |e_i(h)| − |e_i(best)|``; ``mean`` is its
       reliability-weighted mean ``D``, and ``se`` its cluster-robust (CR1)
       standard error over the ``G`` cycles:
       ``se² = G/(G−1) · Σ_g (Σ_{i∈g} w_i (d_i − D))² / (Σ_i w_i)²``.
       ``h`` is MEASURABLY WORSE than ``best`` when the one-sided lower bound
       ``D − t·se`` is above 0, with ``t`` the upper ``SIZE_WINDOW_ALPHA``
       quantile of Student's t on ``G − 1`` degrees of freedom
       (:func:`_t_upper`).
    6. The window is the WIDEST grid value ``≥ best`` that is not measurably
       worse (``status = "derived"``). It need not be adjacent to ``best``:
       a wider value that is not measurably worse wins even where a value
       between them is.
    7. Fewer than ``SIZE_WINDOW_MIN_SCORED`` scored observations, or fewer
       than two cycles (a cluster-robust error has no degrees of freedom on
       one): ``h = inf`` and ``status = "underdetermined"``.

    ``record`` may carry ``record_fn(target, codes)`` already computed, to
    avoid reading the target's record twice. ``record_fn`` is looked up by
    the caller (a module global swapped by a test is honoured).

    Returns ``(h, report)``; ``report`` carries the score at every grid value,
    ``best``, the per-value ``paired`` block (``mean``, ``se``, ``lower``,
    ``worse``), ``clusters``, ``alpha``, ``t_crit``, the count scored, the
    targets walked, the choice and the status, all JSON-safe (``"inf"`` for an
    infinite window), so the choice can be re-derived from the report alone.
    """
    year = int(target.year)
    years = sorted(int(y) for y, e in cityconfig.CALENDAR.items()
                   if e.kind == "LGE" and int(y) <= year)
    records = []
    for y in years:
        if y == year:
            rec = record if record is not None else record_fn(target, codes)
        else:
            rec = record_fn(cityconfig.Target(city=target.city, year=str(y)),
                            codes)
        records.append(rec or {})

    from collections import Counter
    # (cycle, log r, size, reliability, the party's earlier obs, fit, mu_all)
    scored: list[tuple[int, float, float, float, list, object, float]] = []
    nonpositive = 0
    for cycle, (prev, cur) in enumerate(zip(records, records[1:])):
        everything = [o for v in prev.values() for o in v]
        weights = [_reliability(sz) for _, sz in everything]
        if not everything or sum(weights) <= 0:
            continue
        mu_all = float(np.average([np.log(r) for r, _ in everything],
                                  weights=weights))
        fit = size_centre(prev)
        for party, obs in cur.items():
            new = Counter(obs) - Counter(prev.get(party, []))
            for (r, sz), n in sorted(new.items()):
                if r <= 0 or sz <= 0:
                    nonpositive += n
                    continue
                for _ in range(n):
                    scored.append((cycle, float(np.log(r)), float(sz),
                                   _reliability(sz), prev.get(party, []),
                                   fit, mu_all))
    cycles = np.array([c for c, *_ in scored], dtype=int)
    w = np.array([rel for _c, _l, _s, rel, *_ in scored], dtype=float)
    abs_err: dict[float, np.ndarray] = {}
    errors: dict[str, float] = {}
    for h in SIZE_WINDOW_GRID:
        e = np.array([abs(log_r - _shrink_one(earlier, sz, fit, mu_all, h)[0])
                      for _c, log_r, sz, _rel, earlier, fit, mu_all in scored],
                     dtype=float)
        abs_err[h] = e
        if w.sum() > 0:
            errors[str(_json_h(h))] = float((w * e).sum() / w.sum())
    n_clusters = len(set(cycles.tolist()))
    report = {"targets": [str(y) for y in years], "scored": len(scored),
              "nonpositive_skipped": nonpositive, "errors": errors,
              "grid": [_json_h(h) for h in SIZE_WINDOW_GRID],
              "min_scored": SIZE_WINDOW_MIN_SCORED,
              "alpha": SIZE_WINDOW_ALPHA, "clusters": n_clusters}
    if len(scored) < SIZE_WINDOW_MIN_SCORED or not errors or n_clusters < 2:
        report.update(h="inf", status="underdetermined")
        return float("inf"), report
    best_score = min(errors.values())
    best = min(h for h in SIZE_WINDOW_GRID
               if errors[str(_json_h(h))] == best_score)
    t_crit = _t_upper(SIZE_WINDOW_ALPHA, n_clusters - 1)
    W = float(w.sum())
    paired: dict[str, dict] = {}
    chosen = best
    for h in SIZE_WINDOW_GRID:
        if h < best:
            continue
        d = abs_err[h] - abs_err[best]
        mean = float((w * d).sum() / W)
        sums = np.zeros(n_clusters)
        index = {c: i for i, c in enumerate(sorted(set(cycles.tolist())))}
        for c, wi, di in zip(cycles, w, d):
            sums[index[int(c)]] += wi * (di - mean)
        se = float(np.sqrt(n_clusters / (n_clusters - 1)
                           * float((sums ** 2).sum())) / W)
        lower = mean - t_crit * se
        worse = bool(lower > 0.0)
        paired[str(_json_h(h))] = {"mean": mean, "se": se, "lower": lower,
                                   "worse": worse}
        if not worse:
            chosen = h
    report.update(best=_json_h(best), t_crit=t_crit, paired=paired,
                  h=_json_h(chosen), status="derived")
    return float(chosen), report


def spine(target: cityconfig.Target, baseline: dict[str, float],
          prev_local: dict[str, float], codes=METRO_CODES,
          k: float | None = None,
          read_local_only: frozenset = frozenset(),
          h_theta: float = float("inf"), h_rho: float = float("inf"),
          ) -> tuple[dict[str, float], dict]:
    """Each party's central level at the target, from BOTH of its records.

    ``baseline`` is the preceding national election's citywide shares;
    ``prev_local`` the preceding local election's. Returns the blended central
    share per party and a diagnostic block naming, for every party, which route
    it came from and why — because the whole point of task #22 is that the model
    could not previously say.

    Three cases, and every party is in exactly one:

    * **Both records.** The blend, weighted ``k / (worth + k)`` toward the local
      route, where ``worth`` is what the party's own θ record is worth. A party
      with a long retention history sits on the national spine; a party whose θ
      is nothing but the group centre sits on its own last local result.
    * **National only.** A party facing its first local election — MK in 2026.
      Weight 0: there is no local result to blend, and inventing one from the
      group would be worse than using the national route the party does have.
    * **Local only.** A party that contested locally and then did not contest
      nationally, or was not yet national when it did. Weight 1 by necessity.

    A party with neither is an arrival and is not here at all;
    ``pools.arrival_rules`` sizes it from the arrival record.

    ``read_local_only`` names parties the caller will read on the local route
    although they are absent from ``baseline``: the roster parties whose only
    record is the previous LGE (:func:`local_record_only`, BRIEF item 8). They
    are not reported in ``local_only_unused``.

    ``h_theta`` and ``h_rho`` are the size windows (BRIEF item 16): a party's
    own θ (ρ) observations count only where measured off a national (local)
    share within that log distance of its current one. ``run_model`` derives
    them with :func:`size_window` and passes the θ window to
    :func:`theta_prior` as well; the default, ``inf``, filters nothing.

    **The diagnostic block carries an ``absorption`` account** (NULL-RESULTS.md
    4.3): the route census, how much of the two routes' disagreement the blend
    weight took from each, how many parties fell back to the flat group centre
    because they have no record of their own, and the shrink account from each
    call to :func:`_shrunk`. It is write-only and moves nothing. It exists so
    that "changing the national route did not move the forecast" can be told
    apart from "the national route was never worth anything here": at
    ``share_local ≈ 1`` the blend is an attractor and the null is
    ``ABSORBED:spine``, not ``INERT``.
    """
    # RESOLVED AT CALL TIME. `k: float = SPINE_K` would freeze the constant at
    # import, so setting `levels.SPINE_K` afterwards would change nothing and a
    # sweep of it would return identical rows — the trap ITERATING.md rule 6
    # exists for, and the one `montecarlo.LEVEL_DF` was actually in until
    # 2026-08-17. See MODEL-LOG §1.33.
    k = SPINE_K if k is None else float(k)
    theta_obs = theta_record(target, codes)
    rho_obs = local_record(target, codes)
    # The shrink each route performed, forwarded into the block below. `_shrunk`
    # cannot return it — its three-tuple is pinned by test_spine and
    # test_theta_prior — so it fills a dict handed in. See its docstring.
    theta_shrink: dict = {}
    rho_shrink: dict = {}
    # Each route's size centre is evaluated at the party's current size on
    # that route (BRIEF item 11): its national share for θ, its previous
    # local share for ρ.
    mu_t, c_t, worth_t = _shrunk(theta_obs, theta_shrink, current=baseline,
                                 h=h_theta)
    mu_r, c_r, _worth_r = _shrunk(rho_obs, rho_shrink, current=prev_local,
                                  h=h_rho)
    if not mu_t and not mu_r:
        return {}, {}

    # ABSORPTION ACCOUNTING (NULL-RESULTS.md 4.3). The blend is the model's
    # most consequential attractor and had no account of itself: two routes
    # disagree by |log(local) − log(national)|, and `w` decides how much of
    # that disagreement survives. `moved_from_national` is the mass the local
    # route actually won; a change to the national route with
    # `share_local ≈ 1` is ABSORBED here and is not a null about the world.
    #
    # `centre_fallback` counts the OTHER absorber in this function, the one
    # §1.93 named: `mu_t.get(party, c_t)` hands a party with no retention
    # record of its own the flat common centre — the size-blind number
    # `size_centre` exists to replace. MK at 2026 was the case. Since BRIEF
    # item 17 (2026-10-09) `_shrunk` returns a no-record party at the size
    # centre for its current size wherever the size fit exists, so this
    # fallback, and this count, now fire only where there is no size fit
    # (fewer than twenty observations in the record).
    routes = {"blend": 0, "national_only": 0, "local_only": 0, "dropped": 0}
    # NAMES, NOT JUST COUNTS (§1.97 F5, F6). A count says how much was lost; a
    # reader chasing "why is this party at this number?" needs to know WHICH.
    # Both lists are bounded by the party universe and are written into the
    # trace, so they cost nothing anyone will notice.
    dropped_parties: list[str] = []
    local_only_unused: list[str] = []
    blend = {"n": 0, "disagreement": 0.0, "moved_from_national": 0.0,
             "moved_from_local": 0.0, "at_full_local": 0,
             "at_full_national": 0, "nonfinite": 0}
    centre_fallback = {"theta": 0, "rho": 0}

    levels: dict[str, float] = {}
    detail: dict[str, dict] = {}
    for party in set(baseline) | set(prev_local):
        national = float(baseline.get(party, 0.0))
        local = float(prev_local.get(party, 0.0))
        worth = float(worth_t.get(party, 0.0))
        if national > 0 and party not in mu_t:
            centre_fallback["theta"] += 1
        if local > 0 and party not in mu_r:
            centre_fallback["rho"] += 1
        nat_level = national * float(np.exp(mu_t.get(party, c_t))) if national > 0 else 0.0
        loc_level = local * float(np.exp(mu_r.get(party, c_r))) if local > 0 else 0.0
        if national > 0 and local > 0:
            # F2: `k / (worth + k)` is 0/0 when a party has both records and NO
            # θ evidence, and `spine_k=0` is exactly the sweep worth running
            # (§1.30 measured k=0 at RMSE 0.275 against the blend's 0.236). It
            # raised ZeroDivisionError out of the middle of `run_model`, past
            # the `except FileNotFoundError` above it, for five blend-route
            # parties at joburg 2026.
            #
            # THE LIMIT IS CHOSEN, NOT DERIVED — the owner's call, 2026-08-28.
            # `w` is the weight on the LOCAL route, so `k=0` means "pure
            # national spine". Taking `w = 0.0` when `worth + k <= 0` keeps that
            # meaning for EVERY party. The alternative — `w = 1.0` when
            # `worth <= 0`, the limit from above — would have made `k=0` mean
            # pure-national for everyone EXCEPT the parties with no θ evidence,
            # which is the single largest thing the spine does at 2026. A lever
            # that means two things is not a lever. Registered in
            # JUDGEMENT-CALLS.md.
            w = 0.0 if (worth + k) <= 0 else k / (worth + k)
            # Hoisted so the accounting below reuses the logs the blend already
            # took, rather than taking them twice — same values, same warnings.
            log_loc, log_nat = np.log(loc_level), np.log(nat_level)
            level = float(np.exp(w * log_loc + (1 - w) * log_nat))
            # F7: SAY WHAT HAPPENED, NOT WHICH BRANCH RAN. A party with both
            # records and no θ evidence gets `w = 1.0` — one hundred per cent
            # its own last local result, nothing blended — and was labelled
            # "blend" anyway. That is the label a reader checks when asking why
            # a party sits where it does, and for ActionSA at 2026 it said the
            # national route was contributing when it was not.
            #
            # `routes["blend"]` still counts it as blend, because that counter
            # is about WHICH RECORDS THE PARTY HAS and it does have both.
            route = "blend"
            if w >= 1.0:
                route = "blend at full local (no θ evidence)"
            elif w <= 0.0:
                route = "blend at full national (k=0)"
            routes["blend"] += 1
            gap = abs(float(log_loc) - float(log_nat))
            if np.isfinite(gap):
                blend["n"] += 1
                blend["disagreement"] += gap
                blend["moved_from_national"] += w * gap
                blend["moved_from_local"] += (1 - w) * gap
                if w >= 1.0:
                    blend["at_full_local"] += 1
                elif w <= 0.0:
                    blend["at_full_national"] += 1
            else:
                blend["nonfinite"] += 1
        elif national > 0:
            w, level, route = 0.0, nat_level, "national only (first local election)"
            routes["national_only"] += 1
        elif local > 0:
            w, level, route = 1.0, loc_level, "local only (no national record)"
            routes["local_only"] += 1
            # F6: WHO READS THIS LEVEL. `spine` walks
            # `set(baseline) | set(prev_local)`, and its only consumer,
            # `montecarlo.blended_centres`, iterates `base_city`. A party on
            # the target's roster whose only record is the previous LGE is
            # entered into `base_city` by `run_model` and named here in
            # `read_local_only` (item 8, 2026-10-09), so its level is read.
            # Any other party with a local record and no baseline entry, which
            # means one not on the target's roster, gets a level nothing looks
            # up, and is named in `local_only_unused`.
            if party not in baseline and party not in read_local_only:
                local_only_unused.append(party)
        else:
            # Present in one of the two inputs at exactly zero, and dropped
            # entirely — no level, no detail row, no trace. Counted, because a
            # party that vanishes here reappears downstream as whatever
            # `blended_centres` finds first.
            # F5: a party that vanishes here reappears downstream as whatever
            # `blended_centres` finds first, and until now the only signal was
            # its ABSENCE from the returned dict — a count with no names.
            routes["dropped"] += 1
            dropped_parties.append(party)
            continue
        levels[party] = level
        detail[party] = {"w_local": w, "worth": worth, "route": route,
                         "national": nat_level, "local": loc_level}
    return levels, {
        "k": k,
        "n_theta": sum(len(v) for v in theta_obs.values()),
        "n_rho": sum(len(v) for v in rho_obs.values()),
        "theta_centre": float(np.exp(c_t)), "rho_centre": float(np.exp(c_r)),
        "detail": detail,
        # WHAT THIS FUNCTION ABSORBED, and where. Written, never read.
        "absorption": {
            "routes": routes,
            "dropped_parties": sorted(dropped_parties),
            "local_only_unused": sorted(local_only_unused),
            "blend": dict(blend, share_local=(
                blend["moved_from_national"] / blend["disagreement"]
                if blend["disagreement"] > 0 else 0.0)),
            "centre_fallback": centre_fallback,
            "theta_shrink": theta_shrink,
            "rho_shrink": rho_shrink,
        },
    }


def ward_pr_ratios(target: cityconfig.Target, city: cityconfig.City,
                   ) -> tuple[dict[str, float], float]:
    """Each party's ward-ballot share over its PR share, from the last LGE.

    Replaces the hand-set overrides (``MK 0.80`` "bounded by ActionSA's
    observed 0.77", ``ENTRANT 0.80``). A party with no ward history gets the
    median of those that have one, which is a rule rather than a per-party
    number and applies to whoever turns up next.

    **THIS FUNCTION DOES NOT ABSORB — IT REPORTS A FALLBACK IT NEVER APPLIES**
    (NULL-RESULTS.md 4.3). The median, and the ``0.8`` literal behind it, are
    the SECOND element of the return; every party without a measured ratio is
    given one by the caller, so the absorption happens at
    ``montecarlo``'s call site and must be counted there. What happens here is
    a filter, not a clamp: ``pr[p] > 0`` drops a party that took ward votes and
    no PR votes, and a party in neither set never appears.

    Two absences ARE decided here and both collapse to the same pair — a
    missing previous-LGE file and a file with no votes on one ballot both
    return ``({}, 0.8)``, so the caller cannot tell "not measurable" from
    "measured at nothing". The literal is unreachable whenever any ratio was
    computed. There is no seam for a count: the two-tuple is pinned exactly by
    ``tests/test_ward_pr_ratios.py``, including ``== ({}, 0.8)``.
    """
    year = target.previous_lge
    template = cityconfig.CALENDAR[year].results if year else None
    path = city.path("raw", "elections", template) if template else None
    if not path or not path.exists():
        return {}, 0.8
    pr: dict[str, int] = defaultdict(int)
    ward: dict[str, int] = defaultdict(int)
    with open(path, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            party = P.canonical(row["sPartyName"])
            votes = int(float(row.get("Party_Votes") or 0))
            (ward if row.get("BallotType") == "Ward" else pr)[party] += votes
    pr_total, ward_total = sum(pr.values()), sum(ward.values())
    if not pr_total or not ward_total:
        return {}, 0.8
    ratios = {p: (ward[p] / ward_total) / (pr[p] / pr_total)
              for p in set(pr) & set(ward) if pr[p] > 0}
    fallback = float(np.median(list(ratios.values()))) if ratios else 0.8
    return ratios, fallback


def trusted_ward_pr(wc: dict[str, float], pc: dict[str, float],
                    lo: float, hi: float, parties=None) -> dict[str, float]:
    """Each party's ward/PR split-ticket ratio, where it is trustworthy.

    ``wc`` and ``pc`` are the previous LGE's citywide ward-ballot and PR
    shares. A party whose PR share exceeds 0.001 gets ``wc/pc`` clipped to
    ``[lo, hi]`` (``montecarlo.WARD_PR_RATIO_MIN/MAX``); below that the ratio
    is a quotient of two noisy numbers and the party is left out (F46,
    §1.113). Over ``parties`` where given (the run's index), else over
    ``pc``.

    One definition for two consumers: ``montecarlo.run_model``'s ratio array
    (the draws' ward/PR split, and ``_ward_pr_trusted`` for the by-election
    conversion in ``blended_centres``), and ``bye_value.py``'s conversion of
    each metro's by-election delta (BRIEF item 19). Lifted out of
    ``run_model``'s loop 2026-10-10, no behaviour change. Not
    :func:`ward_pr_ratios`, which applies neither the threshold nor the clip.
    """
    out: dict[str, float] = {}
    for p in (pc if parties is None else parties):
        if pc.get(p, 0) > 0.001:
            out[p] = float(np.clip(wc.get(p, 0.0) / pc[p], lo, hi))
    return out


def contestation(target: cityconfig.Target, city: cityconfig.City,
                 ) -> dict[str, float]:
    """The fraction of wards each party fields a ward candidate in.

    Nomination lists close and are published before polling day, so this is
    available to a forecaster. It replaced ``pa_contestation_uplift`` — a
    one-party constant of 1.25 that existed because the PA contested 52 of 135
    wards in 2021 and the model assumed every party contested all of them. The
    same correction is owed to every party, and measured rather than chosen:
    the median party contests well under half the wards.

    **This docstring said "replaces" for weeks while the constant went on
    firing**, because it only replaced it where the target's own lists exist —
    every backtest — and the constant held the branch where they do not, which
    is every live forecast. So the one place it was live was the one place
    nothing could check it. Since 2026-08-18 that branch falls back to the
    PREVIOUS local election's measured shares instead, and the constant is
    deleted. MODEL-LOG §1.47.

    **Presence on the ballot, never a vote.** The justification above is a
    statement about nomination lists, and the code used to count a ward only
    where the party had ``Party_Votes > 0`` — which is not who stood, it is
    who scored, and it is exactly the outcome a backtest is meant to be
    predicting. The IEC publishes a row per party per voting district *where
    that party is on the ballot* (20 to 34 parties per VD in Johannesburg
    2021, not a cross-product of every party), so the row's existence is the
    nomination fact and reading it does not touch the result. It matters most
    where the model is weakest: Royal Loyal Progress stood in all 135 wards
    and scored in 79, so the old rule called a full slate 59% of a slate, and
    contestation multiplies through to an arrival's size.

    **A missing file returns ``{}``, which the caller cannot tell from "nobody
    stood"** (NULL-RESULTS.md 4.3). It is not an accident — at a live forecast
    the target's result file does not exist, and that is what routes
    ``montecarlo`` to :func:`projected_contestation` — but the branch is taken
    on an ABSENCE, so a broken path and a live forecast look identical from
    here. Not counted: the return is a bare dict with no seam, and the caller
    already separates the two cases by whether the previous LGE's lists exist.
    """
    if not has_result_file(target, city):
        # NO RESULT FILE, BUT THE LISTS MAY STILL BE PUBLISHED. Nominations
        # close months before polling day, so at a live forecast the slates can
        # be known even though the outcome is not. Declared slates are read
        # here; when none are declared this returns {} exactly as before, which
        # is what routes `montecarlo` to `projected_contestation`.
        # MODEL-LOG §1.251, prereg/2026-09-23-declared-ward-slates.md.
        slates, _complete = declared_contestation(target, city)
        return slates
    b = ballots(target, city)
    n = len(b.ward_ballot)
    return {p: len(w) / n for p, w in b.wards.items()} if n else {}


def _result_ballots(path) -> tuple[dict[str, set], set, set]:
    """``({party: wards it fields a ward candidate in}, every ward on the ward
    ballot, {parties on the PR ballot})`` from a result file. A row is the
    nomination fact whatever its vote count. The file reader behind
    :func:`ballots`; nothing else reads slates out of a result file."""
    wards: dict[str, set] = defaultdict(set)
    seen: set = set()
    pr: set = set()
    with open(path, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            kind = row.get("BallotType")
            if kind == "PR":
                pr.add(P.canonical(row["sPartyName"]))
                continue
            if kind != "Ward":
                continue
            ward = (row.get("Ward") or "").strip()
            if not ward:
                continue
            seen.add(ward)
            wards[P.canonical(row["sPartyName"])].add(ward)
    return dict(wards), seen, pr


@dataclass(frozen=True)
class Ballots:
    """Who is on each ballot at one city-year. Built only by :func:`ballots`.

    ``wards`` maps a party to the WardIDs (``79800001`` form, the result
    files' and ``pools.vd_map``'s key space) where it fields a ward
    candidate. ``pr`` is the set of parties with a PR list, or None when the
    source does not say (a declared roster with no ``pr`` key). ``parties`` is
    every party the source names on either ballot. ``complete`` says absence is
    a fact: True for a result file, ``[roster] complete`` for a declaration.
    ``ward_ballot`` is the set of wards the ward slates cover. ``source`` is
    ``"result"``, ``"declared"`` or ``"none"``.
    """
    wards: dict
    pr: frozenset | None
    parties: frozenset
    complete: bool
    ward_ballot: frozenset
    source: str

    def slate(self, party: str) -> frozenset | None:
        """The wards ``party`` contests, or None when that is UNKNOWN.

        A party the slates name: its wards. A party the source names but gives
        no ward slate, or any party under a complete source: no wards (an empty
        set, a fact). Otherwise None: a partial declaration says nothing about
        a party it omits (§1.175), so the party keeps an unmasked ward ballot.
        """
        if party in self.wards:
            return self.wards[party]
        if self.complete:
            return frozenset()
        return None

    def ward_only(self) -> frozenset:
        """Parties with a ward slate and no PR list. Empty when ``pr`` is
        unknown. Independents are excluded: they are not in any run's
        universe and leave the pool through the C term."""
        if self.pr is None:
            return frozenset()
        return frozenset(p for p in self.wards
                         if p not in self.pr and p not in (_INDEPENDENT, "IND"))


def ballots(target: cityconfig.Target, city: cityconfig.City) -> Ballots:
    """**The one definition of who stands where** at ``target``.

    From the target's result file where it exists (:func:`has_result_file`):
    a ward slate is the wards with a ward-ballot row for the party, a PR list
    is any PR-ballot row. Otherwise from ``[roster]`` in the judgement file
    (``pools.declared_roster``): ``[roster.wards]`` and ``[roster] pr``.
    Owner rule, 2026-10-15: a party running for ward seats only is omitted
    from every citywide calculation and wins only in the wards it contests;
    ``montecarlo.run_model`` reads that from here, as do :func:`contestation`,
    :func:`declared_contestation`, :func:`slate_coverage` and
    :func:`unopposed_wards`. Before this, three copies of the two-source branch
    existed and the montecarlo copy compared WardIDs with ward NUMBERS, so at
    2026 no ward matched (MODEL-LOG §1.306).
    """
    if has_result_file(target, city):
        wards, seen, pr = _result_ballots(result_path(target, city))
        return Ballots(wards={p: frozenset(w) for p, w in wards.items()},
                       pr=frozenset(pr), parties=frozenset(set(wards) | pr),
                       complete=True, ward_ballot=frozenset(seen),
                       source="result")
    import pools as _pools          # lazy: `pools` imports this module

    roster = _pools.declared_roster(city, target) or {}
    if not roster:
        return Ballots(wards={}, pr=None, parties=frozenset(), complete=False,
                       ward_ballot=frozenset(), source="none")
    wards = {p: frozenset(str(w).strip() for w in ws)
             for p, ws in (roster.get("wards") or {}).items()}
    pr = roster.get("pr")
    pr = None if pr is None else frozenset(pr)
    named = set(roster.get("parties") or ()) | set(wards) | set(pr or ())
    return Ballots(wards=wards, pr=pr, parties=frozenset(named),
                   complete=bool(roster.get("complete")),
                   ward_ballot=frozenset(w for ws in wards.values() for w in ws),
                   source="declared")


def slate_coverage(target: cityconfig.Target, city: cityconfig.City,
                   weights_lge: str | None) -> dict[str, float]:
    """Each party's slate, weighted by where its own list vote lies.

    BRIEF item 6 (owner: "vote weighted"), model correction batch 2026-10-09.
    For every party :func:`contestation` returns at ``target``: the share of
    the party's own PR votes at ``weights_lge`` that were cast in voting
    districts lying in wards where it fields a ward candidate at ``target``.
    ``montecarlo.run_model`` passes the forecast target's previous LGE for
    both the target's slate and the previous one, so the change ``now / was``
    compares two slates on one set of weights.

    Each VD is placed in its ward at ``target`` by ``pools.vd_map`` (a split VD
    goes to the part with the most registered voters); a VD with no ward there
    is left out. Slates come from the target's result file where it exists,
    else from ``[roster.wards]``; a party absent from the declared slates
    fields none (0.0, as :func:`declared_contestation` gives it under a
    complete roster). A party with no PR vote at ``weights_lge`` keeps
    :func:`contestation`'s count fraction, as does every party when the
    weights' file is missing. The prototype is
    ``audits/2026-10-09-model-questions/data/scripts/votecov.py``.

    :func:`contestation` itself is unchanged: it is the who-stands fact that
    ``declared_contestation``'s completeness logic and ``compare_history``
    read.
    """
    base = contestation(target, city)
    if not base or not weights_lge:
        return base
    wpath = result_path(cityconfig.Target(city=city, year=weights_lge), city)
    if not wpath or not wpath.exists():
        return base
    import pools as _pools          # lazy: `pools` imports this module

    pr: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    with open(wpath, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            if row.get("BallotType") != "PR":
                continue
            pr[P.canonical(row["sPartyName"])][row["VD_Number"]] += int(
                float(row.get("Party_Votes") or 0))
    slates = ballots(target, city).wards
    ward_of, _registered = _pools.vd_map(city, target.year)
    out: dict[str, float] = {}
    for party, frac in base.items():
        pairs = [(ward_of[vd], v) for vd, v in (pr.get(party) or {}).items()
                 if vd in ward_of]
        total = sum(v for _w, v in pairs)
        if total <= 0:
            out[party] = frac
            continue
        stood = slates.get(party, set())
        out[party] = sum(v for w, v in pairs if w in stood) / total
    return out


# ---------------------------------------------------------------------------
# UNOPPOSED WARDS (Schedule 1 item 12(2), 13(1)(b), 16(5))
# ---------------------------------------------------------------------------
# A ward whose only candidate is elected unopposed (item 8A) holds no ward
# ballot, and the statute counts every PR vote cast for that candidate's party
# by the ward's voters twice. The seat law takes those votes as an input
# (`seats.eligible_parties(..., unopposed_pr=)`). The draw loop does not model
# such a ward: no ward in any metro LGE file 2000-2021 has one, and every 2026
# Johannesburg ward lists many parties, so a draw-loop branch would have no
# case to score. `montecarlo.run_model` refuses a target that has one instead.
# JUDGEMENT-CALLS §Q7.


def unopposed_in(ward_parties: dict[str, set[str]],
                 all_wards) -> dict[str, str | None]:
    """The unopposed wards in one election, from who stood in each ward.

    ``ward_parties`` maps a ward to the parties on its ward ballot;
    ``all_wards`` is every ward the election covers. Returns ``{ward: party}``
    for a ward with exactly one ward-ballot party, ``IND`` counting as a party,
    and ``{ward: None}`` for a ward with no ward-ballot party at all: a result
    file shows an unopposed ward that way, with PR rows and no ward rows, and
    does not say who the candidate was. A pure function so the result-file and
    the declared-slate readers share one rule.
    """
    out: dict[str, str | None] = {}
    for ward in all_wards:
        stood = ward_parties.get(ward) or set()
        if len(stood) == 1:
            out[ward] = next(iter(stood))
        elif not stood:
            out[ward] = None
    return out


def ward_ballots(path) -> tuple[dict[str, set[str]], set[str]]:
    """Every ward a result file covers, and the parties on each ward ballot.

    Returns ``(ward_parties, all_wards)``: ``all_wards`` is every ward named on
    a row of either ballot, so a ward with PR rows only is in it and absent
    from ``ward_parties``. A row is a nomination fact whatever its vote count
    (see :func:`contestation`). Party names are canonical.
    """
    ward_parties: dict[str, set[str]] = defaultdict(set)
    all_wards: set[str] = set()
    with open(path, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            ward = (row.get("Ward") or "").strip()
            if not ward:
                continue
            all_wards.add(ward)
            if row.get("BallotType") == "Ward":
                ward_parties[ward].add(P.canonical(row["sPartyName"]))
    return dict(ward_parties), all_wards


def unopposed_wards(target: cityconfig.Target,
                    city: cityconfig.City) -> dict[str, str | None]:
    """``{ward: party}`` for each unopposed ward at ``target``.

    From the target's result file where it exists (:func:`ward_ballots`, every
    ward on either ballot). Otherwise from the declared slates,
    ``[roster.wards]`` in the judgement file (``pools.declared_roster``): a
    ward listed for exactly one party. A ward the declaration does not mention
    is not reported, because a partial paste cannot say nobody stood there.
    ``{}`` when neither source exists. ``None`` as a value means the result
    file shows the ward with no ward ballot and does not name the candidate.
    """
    if has_result_file(target, city):
        ward_parties, all_wards = ward_ballots(result_path(target, city))
        return unopposed_in(ward_parties, all_wards)
    ward_parties: dict[str, set[str]] = defaultdict(set)
    for party, wards in ballots(target, city).wards.items():
        for ward in wards:
            ward_parties[ward].add(party)
    return unopposed_in(ward_parties, set(ward_parties))


def unopposed_pr_votes(path, unopposed: dict[str, str | None],
                       ) -> dict[str, int]:
    """``{party: its PR votes in the wards it won unopposed}``, from a result file.

    The input :func:`seats.eligible_parties` counts a second time (Schedule 1
    item 12(2)). Refuses a ward whose candidate the file does not name, since
    the votes to double cannot then be chosen.
    """
    if not unopposed:
        return {}
    unnamed = sorted(w for w, p in unopposed.items() if p is None)
    if unnamed:
        raise SystemExit(
            f"{path}: ward(s) {unnamed} have PR rows and no ward-ballot rows. "
            f"That is how an unopposed ward would appear, but the file does "
            f"not say so or name a candidate. If it was unopposed, Schedule 1 "
            f"item 12(2) doubles its winner's PR votes in the ward; establish "
            f"what happened there and name the party before the council can "
            f"be reconstructed (JUDGEMENT-CALLS §Q7).")
    out: dict[str, int] = defaultdict(int)
    with open(path, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            if row.get("BallotType") != "PR":
                continue
            ward = (row.get("Ward") or "").strip()
            party = P.canonical(row["sPartyName"])
            if unopposed.get(ward) == party:
                out[party] += int(float(row.get("Party_Votes") or 0))
    return dict(out)


def local_record_only(roster, baseline: dict[str, float],
                      prev_local: dict[str, float],
                      seeds: dict[str, float]) -> list[str]:
    """Roster parties whose only record is the previous local election.

    **The one classifier** for BRIEF item 8 (model correction batch,
    2026-10-09). A party on the target's roster, not an independent, with no
    national baseline, no arrival seed, and a positive list vote at the
    previous LGE. Before this, such a party was in no input the run read: the
    national baseline did not carry it, `pools` did not seed it (it has a
    record), and the run's party list is built from the baseline plus the
    seeds. Seven certified Johannesburg 2026 parties fell through that gap.
    `montecarlo.run_model` enters each at its previous-LGE list share, places
    it by its fitted pool vector, and sizes it on the spine's local route
    (``spine(..., read_local_only=...)``).

    Returns the parties sorted.
    """
    out = []
    for party in roster or ():
        if party in (_INDEPENDENT, "IND"):
            continue
        if baseline.get(party, 0.0) > 0 or (seeds or {}).get(party, 0.0) > 0:
            continue
        if prev_local.get(party, 0.0) > 0:
            out.append(party)
    return sorted(out)
