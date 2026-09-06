"""CLASS 12 — A LEVER THAT DOES NOTHING.

A tunable that is declared, documented, registered as a judgement call, and has
no effect on any output. It is worse than a missing lever: it is quoted in
`JUDGEMENT-CALLS.md` as a choice the project made, argued over in review, and
swept for calibration — and every one of those activities is wasted, because the
answer does not depend on it.

This is distinct from CLASS 11 (`test_regressions.py`), which catches a constant
whose value *cannot be changed* from the command line. A CLASS 11 lever moves the
model once you reach it. A CLASS 12 lever does not move it at all.

The instances that motivated this file, all confirmed by an independent review on
2026-08-17 and each found by a different accident rather than by a test:

  * `LEVEL_DF` — bound as a default argument, `def log_shock(..., df=LEVEL_DF)`,
    evaluated once at import. Swept at 2.5, 4, 7, 30, 200 and 1000: BYTE-IDENTICAL
    output every time. It is 🔴 in the register, it is the most-attacked constant
    in the project, and it did nothing at any value anyone contemplated.
  * `polling_lean` / `polling_span` — `lean` was computed and passed to
    `pool_spec`, whose body never referenced the parameter. Inert at any value,
    not merely defaulted to zero. DELETED 2026-08-17, which is why they are no
    longer in `PERTURB`; their removal is what
    `test_every_defaults_key_is_swept_or_excused` was written to catch, because
    the first deletion took their test coverage with it and nothing failed.
  * `pool_spec`'s `base_city_d` argument — same thing, never referenced, and
    missed by the review.
  * `ward_pr_ratio_overrides` (MK 0.80, ENTRANT 0.80) — gated on `not fallback`.
    The code's own comment says the fallback REPLACES these two numbers; they
    were left in `DEFAULTS` and in the register anyway.

    **The mechanism named here was wrong until 2026-08-28 (§1.97 F32) and the
    conclusion was right.** It said `levels.ward_pr_ratios` "returns a fallback
    at every target the harness can run", which reads as a fact about the
    targets. It is not: `ward_pr_ratios` returns a fallback **unconditionally**
    — its failure path returns `({}, 0.8)`. What decides delivery is the gate at
    the CALLER, `if _ratios:` (montecarlo.py:3379): the fallback reaches the
    scenario only when the measured map is non-empty, and it is then truthy only
    because 0.8 is not 0. So the overrides are dead at all 32 (city, target)
    pairs for two reasons stacked, not one — and if the fallback were ever 0.0
    they would come back to life through `not fallback`, which is exactly the
    truthiness trap F27 is about.

The guard is behavioural and there is no static version of it: a textual
reference count passes for every one of the four above. So the test perturbs each
lever to a value that MUST change the answer and asserts that the answer changes
— which is `ITERATING.md` rule 6, applied automatically instead of remembered.

A lever that is legitimately inert at a given target belongs in `EXPECTED_INERT`
with the reason, so that "does nothing" is a claim someone made on purpose rather
than a thing nobody noticed.

--------------------------------------------------------------------------
A NULL HAS FOUR CAUSES AND ONLY ONE OF THEM IS A RESULT
--------------------------------------------------------------------------
`NULL-RESULTS.md` §1, adopted here 2026-08-27:

    UNDELIVERED         the value never reached the computation
    ABSORBED:<stage>    it arrived, and something downstream ate it
    CANCELLED:<param>   it arrived, and a fitted parameter moved to offset it
    INERT               it arrived, propagated, and genuinely does not matter

**Only INERT is a result.** UNDELIVERED is a defect report. ABSORBED is a
structural fact about the model that has to be stated. CANCELLED is a statement
about identifiability, not about the world.

`EXPECTED_INERT` held eighteen entries of PROSE, and prose cannot tell those
four apart — which is the entire problem this file now exists to stop.
`src/pools.py` records that two of these reasons were written from unstable
readings and had to be retracted, so it is not hypothetical.

**Read against the code on 2026-08-27, all eighteen entries are UNDELIVERED.**
Not one of them is a lever that arrived, propagated and did not matter. Every
single one is a gate that was shut — which means the register named for inert
levers currently contains no inert lever at all, and the word "inert" in it has
been doing work it never earned.

That is not bookkeeping. A gate-shut null is **VOID, not NULL**: it says nothing
whatever about the lever. `poll_k` was certified inert on exactly that mistake
(`_LEGACY_POLL` below) and moved the DA 3.4pp and nine seats once the gate was
opened. Three more were found the same way on 2026-08-27, by opening the gate
instead of arguing about it — each was sitting in this register as inert:

  * `bye_local_cap` at 2026 — gate `w_bye_local_ward`/`w_bye_local_pr`, both
    shipped at 0.0. Opened to 0.9, the lever 1.5 -> 40.0 moves the forecast 2.0.
  * `bye_tau_months` at 2026 — same gate; 18.0 -> 400.0 moves it 14.0.
  * `poll_house_k` at 2026 — gate `polling.SIGMA_TWO_TERM`, which the entry
    itself says leaves the retired path "reachable ... for A/B". Reached, at
    `SIGMA_TWO_TERM=False`, the lever 1.0 -> 6.0 moves the forecast **226.0**.

(40 draws, Johannesburg, `_moves` in points/wins/seat-draws as everywhere else
in this file. The magnitudes are recorded as evidence of DELIVERY, not as
targets: nothing here asserts them, and none of them is a standard of
correctness.)

So an entry is no longer a string. It is a `Null` record carrying a
machine-checkable cause code, the gate that was shut, whether that gate is shut
by DATA / a SWITCH / broken CODE, and the name of a check that PROVES it shut.
The rules are enforced by `test_every_excuse_carries_a_machine_readable_cause`,
`test_the_gate_named_by_every_excuse_is_actually_shut` and
`test_no_undelivered_null_is_excused_without_opening_its_gate`.

`MODULE_PERTURB` extends the liveness sweep past `DEFAULTS` keys to module
constants — `montecarlo.LEVEL_DF`, `montecarlo.SHARE_FLOOR`, `polling.
SIGMA_TWO_TERM` and the rest — which `NULL-RESULTS.md` §3 names as the largest
uncovered class (42 of the 48 constants pre-registered for B2).
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import json
import os
from concurrent.futures import ProcessPoolExecutor
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, skip, run_module, scanned  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))

import cityconfig  # noqa: E402
import montecarlo as M  # noqa: E402

SRC = ROOT / "src"

DRAWS = 40
DATA = ROOT / "data/raw/elections"

# Perturbable through `--set` only because `load_scenario` copies them into the
# scenario; they are module constants, not DEFAULTS keys, and the sweep reaches
# them by scenario key of the same lowercase name where one exists.
_MODULE_LEVEL = {"turnout_correlation"}

# The four causes of a null (NULL-RESULTS.md §1). Only INERT is a result.
CAUSES = ("UNDELIVERED", "ABSORBED", "CANCELLED", "INERT")

# What holds an UNDELIVERED gate shut, which decides whether the entry is an
# accepted VOID or an open defect:
#
#   DATA    the evidence this gate needs does not exist at this target, and no
#           code or configuration change here opens it. The lever was never
#           measured at this target and nothing about it has been learned.
#   SWITCH  a value we ship shuts the gate, and the harness CAN open it. Then
#           the harness must, and this file must record what happened when it
#           did — otherwise "inert" is the poll_k mistake with a new name.
#   CODE    the wiring is broken: nothing opens it. That is a defect, and a
#           defect is never an excuse.
BLOCKERS = ("DATA", "SWITCH", "CODE")


@dataclass(frozen=True)
class Null:
    """Why a lever did not move the forecast, in a shape a test can check.

    A prose reason cannot distinguish "this lever is genuinely inert here" from
    "this lever never arrived", and those two have opposite consequences: the
    first is a property of the model worth writing down, the second is a
    measurement that did not happen. Every field below exists because a reader
    could not otherwise tell which one they are looking at.

    ``cause``       one of :data:`CAUSES`.
    ``where``       the GATE that was shut (UNDELIVERED), the STAGE that ate it
                    (ABSORBED) or the PARAMETER that offset it (CANCELLED),
                    named so it can be looked at. Empty only for INERT, which
                    has nowhere to point.
    ``blocker``     one of :data:`BLOCKERS`, for UNDELIVERED only.
    ``gate_check``  the key in :data:`GATES` of a check that PROVES the gate is
                    shut — the difference between a claim and evidence. An
                    entry whose gate nothing checks is reopened
                    (`NULL-RESULTS.md` §4.2), not accepted.
    ``evidence``    what was actually observed, and when. For an entry whose
                    gate the harness opened, the number the lever moved when it
                    was.
    ``reason``      the prose, kept verbatim from before this record existed.
                    Where the prose has since been shown to be WRONG the text
                    stays and ``evidence`` carries the correction, because a
                    silently rewritten excuse destroys the record of what was
                    believed — the convention `_LEGACY_POLL` already set.
    """

    cause: str
    where: str = ""
    blocker: str = ""
    gate_check: str = ""
    evidence: str = ""
    reason: str = ""

    @property
    def code(self) -> str:
        """``UNDELIVERED:<gate>`` / ``ABSORBED:<stage>`` / ``CANCELLED:<param>``
        / ``INERT``.

        NULL-RESULTS.md writes UNDELIVERED bare. It is qualified here for the
        same reason ABSORBED and CANCELLED are: a gate nobody can name is a gate
        nobody checked, and that is how six of these entries came to share one
        paragraph.
        """
        return f"{self.cause}:{self.where}" if self.where else self.cause

    def __str__(self) -> str:
        tail = f" [{self.blocker}]" if self.blocker else ""
        return f"{self.code}{tail} — {self.reason}"


# Reasons shared by several EXPECTED_INERT entries. Each is a claim about the
# model that a reader can check, not a suppression.
# Kept after the path it described was deleted, because the lesson is about
# measurement rather than about that lever: a null measured with the gate shut
# is not a null. §1.68.
_LEGACY_POLL = (
    "RETRACTED 2026-08-17 and kept only as a warning. This entry used to say "
    "'verified directly: poll_k 1.0 vs 40.0 at 2026 moves the DA, ANC, ASA, MK "
    "and EFF by exactly 0.0000pp'. That null was measured WITH THE GATE SHUT — "
    "`poll_id` is None by default, so the branch never ran. It is ITERATING.md "
    "rule 6's exact fault, committed inside the commit that automated rule 6. "
    "Open the gate and poll_k 1.0 -> 1000 moves the DA 33.26 -> 36.67pp and "
    "89.8 -> 99.2 seats, live at 2016, 2021 AND 2026. The lever is not inert; "
    "it is CONDITIONAL, and a conditional lever has to be perturbed together "
    "with its condition — which `_PAIRED` below now does.")

# Levers that do nothing alone and something together. A conditional lever
# perturbed without its gate reads as dead, which is how the poll path was
# wrongly certified inert. Each entry names the keys that must move as a set.
PAIRED: dict[str, dict[str, object]] = {
    # The legacy poll path lived here — `poll_id` + `poll_weight` + `poll_k`,
    # perturbed as a set because a conditional lever moved alone reads as dead.
    # **All three were DELETED on 2026-08-22 (MODEL-LOG §1.68)**, so the entry
    # goes with them; leaving it would name keys that are not in DEFAULTS, which
    # the sweep silently skips while reporting success — the exact failure
    # `test_every_defaults_key_is_swept_or_excused` exists to catch, and it did.
    #
    # The lesson the entry carried is kept in `_LEGACY_POLL` below, because it
    # is about how to measure a lever and not about that lever.
}
_WARD_LOCAL_BYE = (
    "parameters of the §1.28 ward-local by-election term, which is gated on "
    "`w_bye_local_ward` / `w_bye_local_pr`, both 0.0 by design so the published "
    "forecast is untouched until it is deliberately switched on. Inert with "
    "their gate shut, and untestable in any backtest even open, because the "
    "by-election window is 2022-06 to 2026-02.")

# A lever may be inert at a target for a REASON. Each entry is that reason, and
# each is a claim about the model that a reader can check — not a suppression.
# theta_mode, individual_theta and f_other were excused here from 2026-08-17
# until 2026-08-19, when they were DELETED. Three keys carrying twelve
# party-specific numbers between them, certified dead at every runnable target
# and then kept anyway for two days because their disposition was recorded as
# "an open decision". The decision had already been made -- twice -- by the
# project owner. MODEL-LOG §1.52.
# Every poll-weighting judgement call is inert at 2021 for the same reason, so
# the reason is written once. It is NOT that the levers are dead: they are inert
# because the register holds no metro poll of Johannesburg for that target, and
# the metro path is the only consumer. They are live at 2026, where two SRF
# waves are admitted — which puts them in the `w_bye` position, live exactly
# where no backtest can score them, and that is stated wherever they are quoted.
# MODEL-LOG §1.67.
_NO_METRO_POLL = (
    "the metro-poll path is the only consumer of this lever and the register "
    "holds no metro poll of Johannesburg declared for 2021 — the only admitted "
    "2021 poll is `ipsos-2021-lge-national`, which drives the ARRIVALS path "
    "instead. Live at 2026 on the two SRF waves. Inert here by data, not by "
    "design: add a 2021 Johannesburg metro poll to `polls.json` and this moves.\n"
    "  NOTE (§1.75): this reason is only true of levers the metro path ALONE "
    "consumes. `poll_min_n` was carried here on it and should never have been — "
    "the floor sits ahead of every scope test in `polling.screen`, so it gates "
    "the national poll the arrivals path reads too. Its entry is deleted.")

_NO_METRO_POLL_NULL = Null(
    cause="UNDELIVERED",
    where="`_metro` is empty, so `_agg` is None and run_model skips the entire "
          "poll-blend block — no lever inside it is read at all",
    blocker="DATA",
    gate_check="no_metro_poll",
    evidence="`polling.screen(joburg, 2021)` admits exactly one poll, "
             "`ipsos-2021-lge-national`, whose scope is `national`; the only "
             "2021 metro poll on file, `actionsa-internal-2021`, is declined by "
             "the `commissioned` rule. At 2026 the same call admits two metro "
             "waves and every one of these levers is live. Checked 2026-08-27 "
             "by `GATES['no_metro_poll']`, which needs no model run.\n"
             "  NOTE, and it is not in the reason below: the gate is OPEN at "
             "**2016** — `ipsos-2016-lge-joburg` is admitted as metro — and the "
             "sweep does not run 2016, so these six levers have a live target "
             "the harness has never swept them at.",
    reason=_NO_METRO_POLL)

EXPECTED_INERT: dict[tuple[str, str], Null] = {
    ("w_bye", "2021"): Null(
        cause="UNDELIVERED",
        where="`bye` is empty — run_model fills it from "
              "`<target.processed>/byelection_party_deltas.csv`, which a past "
              "target does not have, so `if party in bye and w > 0` never fires "
              "and `w` multiplies nothing",
        blocker="DATA",
        gate_check="bye_deltas_absent",
        evidence="the file is absent from `data/processed/joburg/2021/` and "
                 "present for the 2026 target, where the lever is live and the "
                 "sweep says so. Checked by `GATES['bye_deltas_absent']`, no "
                 "model run needed. NOTE what this does NOT establish: nothing "
                 "here shows what `w_bye` is worth, at 2021 or anywhere. It is "
                 "0.40 on the published forecast and no backtest can score it.",
        reason=
        "by-election data covers 2022-06 to 2026-02 only, so no past target has "
        "any. Inert in every backtest by construction; live in 2026. This is why "
        "JUDGEMENT-CALLS.md §A carries it at 🔴 as argued-not-tested."),
    ("bye_weight_mode", "2021"): Null(
        cause="UNDELIVERED",
        where="`bye` is empty at every past target, so the block this lever "
              "chooses a weight INSIDE is never entered. It cannot be inert "
              "for its own reasons because it is never consulted — the same "
              "gate that makes `w_bye` undeliverable at 2021",
        blocker="DATA",
        gate_check="bye_deltas_absent",
        evidence="the same gate as `w_bye` above, checked by "
                 "`GATES['bye_deltas_absent']` with no model run. At 2026 the "
                 "lever IS live and measured: derived weights run 0.031 (ATM, "
                 "3 contests) to 0.722 (EFF, 11 contests) against a typed "
                 "0.40, moving 2.005pp of centre across all parties. NOTE what "
                 "this does NOT establish: nothing scores which weighting is "
                 "BETTER, because no backtest reaches the by-election channel.",
        reason=
        "the minimum-variance weight derived from the two estimates' own "
        "precisions, instead of a typed 0.40. Adopted as a LEVER rather than a "
        "default on 2026-08-28: switching it moves the published 2026 forecast "
        "and nothing can score it, so it is the owner's decision. §1.122"),
    ("level_sd_default", "2021"): Null(
        cause="UNDELIVERED",
        where="`sd_for_party` is never called. `handled` is every party holding "
              "membership of any pool, `pools.emit_pools` gives every baseline "
              "party a vector, so the `individual` list the fallback serves is "
              "EMPTY — the fallback is not merely unused, its consumer does not "
              "run",
        blocker="DATA",
        gate_check="level_sd_fallback_never_binds",
        evidence="measured 2026-08-27 against the base run and the emitted "
                 "spec: every party in the run's index is a pool member, at "
                 "both targets (56 of 56 at 2021, 44 of 44 at 2026), so "
                 "`individual` is empty at both.\n"
                 "  **THE REASON BELOW IS WRONG AND IS KEPT AS WRITTEN.** It "
                 "says `levels.theta_prior` returns an sd for EVERY party in "
                 "the baseline. At 2021 it does not: 33 of the 56 parties in "
                 "the index have no measured sd — ActionSA among them — so if "
                 "the individual path ever ran, this fallback would bind for a "
                 "third of the ballot at 1.60 instead of 0.45. The null is "
                 "real; the stated cause of it is not, and the entry has been "
                 "right by luck since 2026-08-20. Corrected here rather than "
                 "silently rewritten, per `_LEGACY_POLL`. At 2026 the second "
                 "consumer (`_sd.get(party, default)` in the poll blend) does "
                 "run, and every party it reaches has a measured sd.",
        reason=
        "the fallback level spread for a party with no measured sd(log theta), "
        "and `levels.theta_prior` returns an `sd` for EVERY party in the "
        "baseline — so `sd_for_party` takes the measured branch every time and "
        "the default never binds. JUDGEMENT-CALLS.md predicted exactly this "
        "('binds only on parties outside it') before there was a test to show "
        "it. **It was also not a DEFAULTS key at all until 2026-08-20**, so it "
        "was frozen at 0.45 and unreachable; the register's own instruction was "
        "'either measure it or promote it', and it is now promoted. Inert is "
        "the honest reading and not a defect: a fallback that never fires is "
        "what you want, and the value only matters if the baseline ever stops "
        "covering the ballot. MODEL-LOG §1.63."),
    ("level_sd_default", "2026"): Null(
        cause="UNDELIVERED",
        where="the same as at 2021: `handled` covers the whole index, so the "
              "`individual` list `sd_for_party` serves is empty",
        blocker="DATA",
        gate_check="level_sd_fallback_never_binds",
        evidence="44 of 44 index parties are pool members at 2026. The reason "
                 "below repeats the 2021 claim and inherits its error — see "
                 "that entry; at 2026 the claim happens to be true (the only "
                 "index party without a measured sd is ENTRANT, which the "
                 "fallback's consumers both skip), and it is still not why the "
                 "lever cannot move.",
        reason="same reason as at 2021 — theta_prior covers "
        "every party in the baseline, so the fallback never binds"),
    ("poll_house_k", "2021"): _NO_METRO_POLL_NULL,
    ("poll_house_k", "2026"): Null(
        cause="UNDELIVERED",
        where="`_cap = 1.0 if polling.SIGMA_TWO_TERM else weight_cap(..., "
              "house_k=...)` — the shipped switch takes the branch that never "
              "reads the lever",
        blocker="SWITCH",
        gate_check="sigma_two_term_shipped_on",
        evidence="THE GATE WAS OPENED, because the entry itself says the "
                 "retired path stays reachable for A/B and an excuse that names "
                 "its own escape hatch has to use it. With "
                 "`polling.SIGMA_TWO_TERM = False`, `poll_house_k` 1.0 -> 6.0 "
                 "moves the 2026 forecast by 226.0 (40 draws, 2026-08-27). The "
                 "lever is not inert and never was: it is CONDITIONAL, and "
                 "`CONDITIONAL['poll_house_k@2026']` now perturbs it together "
                 "with its gate on every run of this file — which is exactly "
                 "what `_LEGACY_POLL` says was owed to `poll_k` and was not "
                 "done for eight days.",
        reason=
        "**THE MECHANISM IT DRIVES IS RETIRED (2026-08-24, §1.91).** It set the "
        "cap `H_eff/(H_eff+k)` on a poll's weight, and `SIGMA_TWO_TERM` — now "
        "the DEFAULT — deletes the cap: `montecarlo` sets `_cap = 1.0` under the "
        "switch, so nothing reads this lever on the shipped path. It is NOT "
        "deleted, because the retired σ remains reachable with "
        "`SIGMA_TWO_TERM=0` for A/B and reads it there. Inert by design and "
        "stated as such in JUDGEMENT-CALLS.md, which now carries the row struck "
        "through. What bounds a single house instead is `polling.house_ceiling`, "
        "derived from the σ floor rather than chosen: a lone house saturates at "
        "0.5761 of the blend however many waves it publishes, and two houses "
        "pass that with four polls (§1.92). If this lever is ever wanted back, "
        "the thing to change is the σ, not the cap."),
    ("poll_deff_subsample", "2021"): _NO_METRO_POLL_NULL,
    ("poll_screen_sd", "2021"): _NO_METRO_POLL_NULL,
    ("poll_drift_per_root_day", "2021"): _NO_METRO_POLL_NULL,
    ("poll_half_life_days", "2021"): _NO_METRO_POLL_NULL,
    ("poll_credence", "2021"): _NO_METRO_POLL_NULL,
    ("arrival_group_draw", "2026"): Null(
        cause="UNDELIVERED",
        where="`group = scenario.get('arrival_group') or None` — the emitted "
              "spec carries `arrival_group: null` at this target, so the draw "
              "the switch selects has nothing to draw",
        blocker="DATA",
        gate_check="no_arrival_group_spec",
        evidence="read straight out of the artefact 2026-08-27: "
                 "`pools_2026.json` and `pools_2016.json` carry "
                 "`arrival_group: null`; `pools_2021.json` carries a six-field "
                 "object. Correction to the reason below, which says the key is "
                 "ABSENT from the 2026 spec: it is PRESENT and null. The gate "
                 "is `or None` either way, so the conclusion holds — but a "
                 "reader checking the claim as written would have found the key "
                 "there and concluded the entry was stale.",
        reason=
        "GATED ON DATA THAT DOES NOT EXIST YET, and the gate is three deep. "
        "`pools.arrival_group_spec` returns None unless the target has a real "
        "ROSTER — it splits the group total by each named arrival's ward reach, "
        "and there are no named arrivals until nomination lists close. Its own "
        "docstring says so: 'the 2026 forecast therefore still depends on the "
        "generic entrant slot until nomination lists close.' Confirmed in the "
        "emitted specs: `arrival_group` is present in pools_2021.json (32 "
        "members) and ABSENT from pools_2026.json and pools_2016.json. The IEC "
        "publishes the final 2026 candidate list on **16 September 2026** "
        "(nominations closed 28 August; polling 4 November), so this is inert "
        "at 2026 until task A4 ingests them and cannot be made live by any code "
        "change. Two further layers were fixed on 2026-08-20 to get this far: "
        "the key was in no DEFAULTS so the mechanism was UNREACHABLE rather "
        "than off, and the branch raised `NameError: dirichlet_floor` the first "
        "time anything reached it. Measured where it CAN fire — the eight 2021 "
        "metros — it is much worse: coherent 254 -> 348, CRPS 232.9 -> 296.0. "
        "MODEL-LOG §1.63."),
    ("contestation_expand", "2021"): Null(
        cause="UNDELIVERED",
        where="`if not _contest and _contest_prev` — `levels.contestation` "
              "reads the target's own result file, so `_contest` is non-empty "
              "and `levels.projected_contestation`, the lever's only consumer, "
              "is never called",
        blocker="DATA",
        gate_check="real_contestation_lists",
        evidence="`levels.contestation` returns 55 parties at 2021 and `{}` at "
                 "2026 (measured 2026-08-27, no model run). That is the gate in "
                 "both directions, and it is why the lever is live at exactly "
                 "the one target no backtest can score — stated in the reason "
                 "below and in JUDGEMENT-CALLS.md, and it does not stop being "
                 "true because the gate check passes.",
        reason=
        "SUPERSEDED BY DATA, which is the point. It projects a ward slate for a "
        "target whose nomination lists are not published, and `levels."
        "contestation` reads the target's own result file — which exists for "
        "every backtestable target and for no live forecast. So at 2021 the "
        "real lists are used, `levels.projected_contestation` is never called, "
        "and this lever cannot move anything. **That is the same shape as "
        "`pa_contestation_uplift`, which fired only where nothing could check "
        "it and survived for weeks** (MODEL-LOG §1.47), so read the difference "
        "carefully: this one is declared, its default is measured against the "
        "eight-metro slate record (median +0.220 of the way to a full slate, "
        "65.5% of parties expanding), it is inert the moment real lists exist, "
        "and it is at 🔴 in JUDGEMENT-CALLS.md as argued-not-tested. It is a "
        "named assumption replacing an unnamed one — before it, the live "
        "forecast silently assumed every party fields exactly last time's "
        "slate. Verified live at 2026: Johannesburg's PA goes 17 -> 19 -> 22 "
        "median seats at expand 0.0 / 0.220 / 0.5. MODEL-LOG §1.60."),
    ("w_bye_local_ward", "2021"): Null(
        cause="UNDELIVERED",
        where="`if (w_ward or w_pr) and (processed / "
              "'byelection_contest_detail.csv').exists()` — the file is not in "
              "a past target's processed directory, so the ward-local block "
              "does not run even with the weight opened",
        blocker="DATA",
        gate_check="bye_contest_detail_absent",
        evidence="absent from `data/processed/joburg/2021/`, present for the "
                 "2026 target (checked 2026-08-27, no model run). At 2026 this "
                 "lever IS live and the sweep says so, which is why there is no "
                 "2026 entry. What that means for the pair below matters: at "
                 "2026 the file exists and only the weights are shut, so their "
                 "gate is a SWITCH, not data.",
        reason="built, disabled, and untestable for the same reason as w_bye"),
    ("w_bye_local_pr", "2021"): Null(
        cause="UNDELIVERED",
        where="the same gate as `w_bye_local_ward` at 2021 — no "
              "`byelection_contest_detail.csv` for a past target",
        blocker="DATA",
        gate_check="bye_contest_detail_absent",
        evidence="as `w_bye_local_ward` at 2021; live at 2026, where the sweep "
                 "reaches it and no entry is needed.",
        reason="built, disabled, and untestable for the same reason as w_bye"),
    # --- added 2026-08-17, when the enumeration test raised PERTURB from 13 of
    # --- 27 DEFAULTS keys to 23 and seven more levers turned out not to move.
    # Each is inert for a DIFFERENT reason and every reason is checkable.
    #
    # AND TWO OF THE FOUR WERE NOT INERT AT ALL (2026-08-27). At 2026 the file
    # their block needs EXISTS; the only thing shutting the gate is that
    # `w_bye_local_ward` and `w_bye_local_pr` ship at 0.0 — a switch this
    # harness can open, and `_LEGACY_POLL` is four lines of why it then must.
    # Opened, both levers move the forecast. The entries stay, because the
    # SHIPPED configuration really does not move; what changes is that they no
    # longer claim the lever is inert, and `CONDITIONAL` now measures them on
    # every run.
    ("bye_local_cap", "2021"): Null(
        cause="UNDELIVERED",
        where="two gates, both shut: `byelection_contest_detail.csv` is not in "
              "a past target's processed directory, and `w_bye_local_ward` / "
              "`w_bye_local_pr` are 0.0. The file is the one no switch opens",
        blocker="DATA",
        gate_check="bye_contest_detail_absent",
        evidence="the by-election window is 2022-06 to 2026-02, so no past "
                 "target has a contest detail file at all — opening the weights "
                 "at 2021 would still not reach this lever. Nothing has been "
                 "learned about the cap at 2021 and nothing can be.",
        reason=_WARD_LOCAL_BYE),
    ("bye_local_cap", "2026"): Null(
        cause="UNDELIVERED",
        where="`if (w_ward or w_pr) and ...` — `w_bye_local_ward` and "
              "`w_bye_local_pr` both ship at 0.0, so the ward-local block never "
              "runs. The DATA is present at this target; only the switch is off",
        blocker="SWITCH",
        gate_check="local_bye_weights_shipped_off",
        evidence="THE GATE WAS OPENED 2026-08-27. With both weights at 0.9, "
                 "`bye_local_cap` 1.5 -> 40.0 moves the 2026 forecast by 2.0 "
                 "(40 draws). The lever is CONDITIONAL, not inert; "
                 "`CONDITIONAL['bye_local_cap@2026']` perturbs it with its gate "
                 "on every run of this file. The reason below is true about the "
                 "shipped forecast and was being read as a statement about the "
                 "lever, which it never was.",
        reason=_WARD_LOCAL_BYE),
    ("bye_tau_months", "2021"): Null(
        cause="UNDELIVERED",
        where="the same two gates as `bye_local_cap` at 2021, and the missing "
              "contest detail file is again the one no switch opens",
        blocker="DATA",
        gate_check="bye_contest_detail_absent",
        evidence="as `bye_local_cap` at 2021.",
        reason=_WARD_LOCAL_BYE),
    ("bye_tau_months", "2026"): Null(
        cause="UNDELIVERED",
        where="the same shipped-at-0.0 weights as `bye_local_cap` at 2026",
        blocker="SWITCH",
        gate_check="local_bye_weights_shipped_off",
        evidence="THE GATE WAS OPENED 2026-08-27. With both weights at 0.9, "
                 "`bye_tau_months` 18.0 -> 400.0 moves the 2026 forecast by "
                 "14.0 (40 draws) — seven times what the cap moves it, which is "
                 "worth knowing about a decay constant nobody could previously "
                 "measure. `CONDITIONAL['bye_tau_months@2026']` keeps it "
                 "measured.",
        reason=_WARD_LOCAL_BYE),
    # ("overhang_rule", "2021") was excused here from 2026-08-17 to 2026-08-18.
    # THE ENTRY RETIRED ITSELF, exactly as it said it would. It recorded that
    # its own excuse was weak -- the overhang clause fired in 1 draw of 200 at
    # that target, so the lever was inert only because a rare clause missed
    # under this seed and draw count -- and it predicted that any change to the
    # draws would make it live and fail the entry as a stale register claim.
    # The contestation correction (MODEL-LOG §1.47) changed the ward wins, the
    # clause now fires, and the `elif` in `_sweep_target` duly reported it.
    # Deleted rather than re-argued: the lever is live at both targets.
    # `pa_contestation_uplift` was excused here until 2026-08-18, on the
    # grounds that it fired only where no backtest could reach it. That was a
    # true statement and the wrong conclusion: a lever live ONLY in the live
    # forecast is not a lever to excuse, it is one to delete. It is gone, and
    # the branch it held now falls back to the previous local election's
    # measured contestation for EVERY party. MODEL-LOG §1.47.
}

# An argument may be accepted and ignored for a REASON. Each entry is that
# reason. `_`-prefixing is the usual way to say so, but it does not work where
# the argument is dispatched BY KEYWORD through a uniform interface — renaming
# it there breaks every caller.
DELIBERATELY_UNUSED: dict[str, str] = {
    "benchmarks.py:last_lge(seed)":
        "dispatched as BENCHMARKS[name](ctx, draws=draws, seed=seed), so the "
        "name is load-bearing and cannot be prefixed. The baseline is "
        "deterministic by design — and THIS IS WHY its CRPS is identically its "
        "absolute seat error, which matters when reading 'the model beats it "
        "8/9 on CRPS': a point forecast is maximally penalised by CRPS.",
    "benchmarks.py:uniform_swing(seed)": "same uniform dispatch, same reason",
    "benchmarks.py:blended_swing(seed)":
        "same uniform dispatch, same reason. It is `prev + BLEND_W * swing` and "
        "BLEND_W is 1.0, so it is currently `uniform-swing` exactly — kept "
        "runnable so the measurement that put it there stays repeatable, and "
        "deliberately NOT printed as a fourth baseline column. MODEL-LOG §1.57.",
    "width_budget.py:_no_pool_turnout(rng)":
        "an ABLATION STUB. `src/width_budget.py` measures what each variance source contributes by replacing it with a version that has none, and a replacement must present the signature of the thing it replaces or `montecarlo` cannot call it. Ignoring this argument IS the measurement. MODEL-LOG §1.48.",
    "width_budget.py:_no_pool_turnout(z_common)":
        "an ABLATION STUB. `src/width_budget.py` measures what each variance source contributes by replacing it with a version that has none, and a replacement must present the signature of the thing it replaces or `montecarlo` cannot call it. Ignoring this argument IS the measurement. MODEL-LOG §1.48.",
    "width_budget.py:_no_pool_turnout(rho)":
        "an ABLATION STUB. `src/width_budget.py` measures what each variance source contributes by replacing it with a version that has none, and a replacement must present the signature of the thing it replaces or `montecarlo` cannot call it. Ignoring this argument IS the measurement. MODEL-LOG §1.48.",
    "width_budget.py:_no_shock(rng)":
        "the same, for the theta level shock, which returns 1.0. NOTE that it therefore consumes no randomness -- which is exactly why the harness averages five seeds: an ablation that skips a draw shifts every later draw, and the first run of it reported negative variance contributions because of that.",
    "width_budget.py:_no_shock(df)":
        "the same, for the theta level shock, which returns 1.0. NOTE that it therefore consumes no randomness -- which is exactly why the harness averages five seeds: an ablation that skips a draw shifts every later draw, and the first run of it reported negative variance contributions because of that.",
    "levels.py:sd_raw(size)":
        "the POOLED fallback branch, taken when fewer than 6 observations "
        "support a size fit. The fitted branch two lines above does use size. "
        "Both must present the same signature to their caller.\n"
        "  KEY RENAMED 2026-08-27, `sd_for` -> `sd_raw`, FOLLOWING THE CODE and "
        "not to silence it: `levels.sd_for` was split into `sd_raw` plus a "
        "`clip(sd_raw(size), SD_FLOOR, SD_CEILING)` wrapper so the clamp could "
        "be counted. `sd_for` now passes `size` on and needs no excuse; the "
        "pooled `sd_raw` still ignores it, for the reason above, which the new "
        "code states at the call site as 'SIZE DOES NOT ENTER, and that is this "
        "branch's absorption'. That is a cause code in prose — ABSORBED, at a "
        "named stage — and it is the same claim this entry has always made.",
}

# Keys that are NOT model judgements: how many draws, which seed, where the
# inputs came from. Perturbing them is meaningless, so they are excused by name
# rather than by omission — see `test_every_defaults_key_is_swept_or_excused`.
OPERATIONAL: dict[str, str] = {
    "draws": "how many samples to take; not a claim about the world",
    "seed": "reproducibility, not a model parameter",
    "pools": "the emitted pool spec itself, loaded from pools_<year>.json",
}

# ⛔ STATUTE. A THIRD CATEGORY, BECAUSE THE OTHER TWO ARE BOTH WRONG FOR IT.
#
# `OPERATIONAL` means "not a claim about the world" — the statute emphatically
# is one. `PERTURB` means "the project chose this and must show the choice
# matters" — the project chose nothing; the legislature did.
#
# Filing the excessive-seats provision under `PERTURB` for its whole life is
# how this module came to demand that a law move the forecast, and to offer
# "delete it from DEFAULTS" as one of three remedies when it did not. Its value
# is now refused at the `--set` boundary by `montecarlo.STATUTORY_VALUES`, so
# what this category asserts is that the two lists agree: a statutory key is
# named here and nailed down there, and neither can drift without the other.
# MODEL-LOG §1.165.
STATUTORY: dict[str, str] = {
    "overhang_rule": (
        "Municipal Structures Act Schedule 1 item 16 as amended by Act 3 of "
        "2021. Not selected by score and not scoreable: it has never bound in "
        "a metro across 24 city-years, tightest margin 2 seats."),
}

# Perturbations chosen to be large enough that no honest lever could absorb them.
# Keys `montecarlo` reads out of `scenario` that are INJECTED AT RUNTIME rather
# than declared: the pool spec writes them, or a stage writes them for a later
# stage. They are not levers and must not be in `DEFAULTS` — declaring them would
# invite a user to --set a value the run then overwrites. Anything reachable by a
# leading underscore is covered by the convention; these are the ones that are
# not. See `test_no_scenario_key_is_read_without_being_declared`.
RUNTIME_INJECTED: dict[str, str] = {
    "theta_prior": "written by run_model from levels.theta_prior",
    "pool_seeds": "written by the seeding stage for the draw stage",
    "pool_seed_bands": "the same, the bands beside the seeds",
    "pool_seed_notes": "the same, the reasons, for the verbose line and the trace",
    "spine_level": "written by run_model from levels.spine",
    "poll_levels": "written by the polling stage where a usable poll exists",
    "arrival_group": "read out of the emitted pool spec; None where the target "
                     "has no roster, which is every unheld election",
}

PERTURB: dict[str, object] = {
    # Perturbed to the OTHER mode, not to a number: it is a categorical lever.
    # Live at 2026, where it moves nine parties and 2.005pp of centre; inert at
    # 2021 for exactly the reason `w_bye` is, and the entry below says so.
    "bye_weight_mode": "inverse_variance",
    "entrant_prob": 0.95,
    "dirichlet_floor": 0.05,
    "ward_noise_sd": 0.60,
    "turnout_pattern_blend": 1.0,
    "turnout_blend_jitter": 0.90,
    "turnout_noise_sd": 0.50,
    "w_bye": 0.95,
    "arrival_group_draw": True,   # the mechanism instead of the generic slot
    "poll_paths": "off",          # both poll paths off; worth -6 on sixteen (§1.94)
    "poll_credence": 0.0,         # believe the metro polls not at all
    "poll_house_k": 6.0,          # cap 0.86 at one house — near-uncapped
    "poll_deff_subsample": 4.0,   # a subsample worth a quarter of its headline n
    "poll_screen_sd": 0.12,       # an undisclosed screen priced as ruinous
    "poll_drift_per_root_day": 0.02,   # opinion moving very fast
    "poll_min_n": 5000,           # admits nothing under 5,000 respondents
    "poll_half_life_days": 5.0,   # only the freshest wave counts
    "level_sd_default": 1.60,     # was frozen at 0.45 and unreachable
    "contestation_expand": 1.0,   # every party in every ward
    "w_bye_local_ward": 0.90,
    "w_bye_local_pr": 0.90,
    "spine_k": 40.0,
    "level_floor": 0.02,
    # ONE entry only. This key was set twice — 0.0 here with an explanation
    # and -0.9 forty lines on — and Python keeps the last, so the documented
    # perturbation never ran. -0.9 is kept because it is the further from the
    # 0.63 default and so the stronger test. MODEL-LOG 1.93.
    "turnout_correlation": -0.9,   # anti-correlated pools; default is 0.63
    # The level shrink, added 2026-08-17 and ADOPTED at 0.35 the next day.
    # PERTURBED TO 0.0, WHICH IS THE POINT: 0.0 is exactly the identity in
    # `compress_levels`, so this sweep asks whether the committed shrink is
    # doing anything at all, and a null here would mean the largest scored
    # improvement this model has had is not reaching the forecast. Perturbing
    # it to 0.35 -- as this entry did for a few minutes -- perturbs it to its
    # own default and is guaranteed to report a lever that cannot move.
    "level_shrink": 0.0,
    "level_shrink_scale": 0.40,
    # The dominant width lever (§1.48), sweepable since §1.55. 2.0 halves the
    # within-pool spread and moves everything; 1.0 is the fitted identity.
    "dirichlet_scale": 2.0,
    # Added 2026-08-17 after the enumeration test below found that PERTURB
    # covered 13 of 27 DEFAULTS keys and nobody had noticed.
    "entrant_share": [0.20, 0.30, 0.45],
    "bye_local_cap": 40.0,
    "bye_tau_months": 400.0,
    # k = 0.0, NOT 1.0. `dev[ENTRANT] = (1-k) * dev[parent]`, so k=1 is flat by
    # construction and is exactly what the empty default already does -- the
    # value this entry carried until 2026-08-20 was the IDENTITY, and the
    # EXPECTED_INERT entry that excused the resulting null blamed a missing
    # `parent` when a parent was in fact supplied. Two wrong explanations of one
    # non-perturbation. At k=0 the slot inherits the parent's per-VD map and the
    # forecast moves at both targets. MODEL-LOG §1.53.
    "entrant_geography": {"parent": "ANC", "k": 0.0},
}


def _run(target_year: str, overrides: list[str], run_dir: Path | None = None,
         draws: int | None = None):
    city = cityconfig.use("joburg")
    target = cityconfig.use_target(target_year)
    M.apply_city(city)
    scenario = M.load_scenario(argparse.Namespace(
        config=None, set=list(overrides), draws=draws or DRAWS, seed=20261104,
        city="joburg", target=target_year))
    # `run_dir` is opt-in and changes no number -- asserted by
    # `test_chain.py::test_the_trace_is_inert_without_a_run_directory` -- and
    # only `_base` passes one. It is what lets a gate check LOOK at a quantity
    # (the measured sd(log theta), say) instead of arguing about it: the whole
    # point of a delivery proof is that somebody can go and see the value.
    run = M.run_model(target, scenario, DATA, verbose=False, run_dir=run_dir)
    # ALL THREE OUTPUTS, because a lever may touch only one of them and the
    # first version of this test compared the list ballot alone. It therefore
    # reported `ward_noise_sd` and `pa_contestation_uplift` as dead when both
    # are live: the first perturbs the ward TALLY (so it moves winners, not
    # shares) and the second the ward/PR ratio (so it moves the ward ballot
    # only — measured at 2026, PA ward share 5.64% -> 6.95%, mean seats
    # 15.11 -> 16.83, with the list share unchanged to the digit).
    seats: dict[str, float] = {}
    for d in run.seat_draws:
        for party, n in d.items():
            seats[party] = seats.get(party, 0.0) + n
    return (run.pr_share_draws.copy(), run.ward_share_draws.copy(),
            dict(run.ward_win_sum), seats, dict(run.index))


# HOW MANY WORKERS THE SWEEP MAY USE.
#
# This module is 999s of a 1455s suite -- 69% of it -- because it does roughly
# 108 `run_model` calls at 40 draws, one per lever per target, and they are
# INDEPENDENT: each perturbs one key from the shipped configuration and is
# compared against the same base. Measured 2026-08-28 by the per-module timing
# in `run_all.py`, which is why this is an evidence-led change and not a guess:
# the first plan was to parallelise the SUITE across modules, and the profile
# said that would win 1.46x against 7x here.
#
# THE FAILURE MODE IS LOUD, WHICH IS WHAT MAKES THIS SAFE. A worker that did not
# receive its perturbation runs the shipped configuration, so `_moves` returns 0
# and the lever is reported DEAD. A broken parallel sweep therefore fails with
# "these levers are dead", never passes quietly -- which is the opposite of the
# 42-of-48 undelivered class this file exists to catch, and the reason that
# class is dangerous is precisely that it is silent.
#
# `_sweep_module_constants` is NOT parallelised and must not be: a module
# constant rebound in the parent DOES NOT CROSS a ProcessPoolExecutor boundary
# (MODEL-LOG §1.33, §1.104), so those six runs stay serial where the `setattr`
# is visible to the code under test.
_SWEEP_WORKERS = max(1, min(8, (os.cpu_count() or 2) - 1))


# ⛔ A LEVER WHOSE EFFECT IS A RARE TAIL NEEDS MORE DRAWS, NOT AN EXCUSE.
#
# `DRAWS` is 40, which resolves any lever that shifts the central mass. It does
# NOT resolve one that changes the answer in a small fraction of draws, and
# reporting such a lever as DEAD is a false negative of exactly the kind this
# module exists to prevent.
#
# ⚠️ THIS TABLE IS EMPTY, AND ITS ONE ENTRY WAS A MISTAKE WORTH RECORDING.
# `("overhang_rule", "2021")` was given a 400-draw budget on 2026-09-01 so the
# harness could resolve a 3.5% tail. The measurement was sound and the
# conclusion was wrong: `overhang_rule` is STATUTE, it is not a lever, and the
# fix was to take it out of `PERTURB` rather than to make this module better at
# policing it. A test whose remedy menu offers "delete it" for the
# excessive-seats provision is a hazard, not a guard. MODEL-LOG §1.165.
#
# Keep the mechanism: the next lever with a genuinely rare effect will need it,
# and re-deriving the argument from scratch would be waste. Keep it EMPTY until
# then, so nothing is resolved harder than the evidence warrants.
RESOLUTION: dict[tuple[str, str], int] = {}


def _run_job(job: tuple[str, list[str]]):
    """One perturbed run. Module level so a worker process can pickle it."""
    year, overrides = job[0], job[1]
    draws = job[2] if len(job) > 2 else None
    return _run(year, overrides, draws=draws)


def _run_many(jobs: list[tuple[str, list[str]]]) -> list:
    """Every job, in order, in parallel where that is worth the spawn.

    Processes and not threads, for the same reason `compare_history` uses them:
    `apply_city` and the module constants are module STATE, and two threads
    would tread on each other's city.
    """
    if len(jobs) < 2 or _SWEEP_WORKERS < 2:
        return [_run_job(j) for j in jobs]
    with ProcessPoolExecutor(max_workers=_SWEEP_WORKERS) as pool:
        return list(pool.map(_run_job, jobs))


def _moves(base, other) -> float:
    """Largest change any lever produced on any output, in percentage points."""
    (bp, bw, bwin, bs, bi), (op, ow, owin, os, oi) = base, other
    shared = set(bi) & set(oi)
    if not shared:
        return float("inf")
    share = max(
        max(abs(bp[:, bi[p]].mean() - op[:, oi[p]].mean()) for p in shared),
        max(abs(bw[:, bi[p]].mean() - ow[:, oi[p]].mean()) for p in shared))
    wins = max(abs(bwin.get(p, 0) - owin.get(p, 0))
               for p in set(bwin) | set(owin)) if (bwin or owin) else 0.0
    # SEATS TOO. `overhang_rule` touches nothing else -- it decides the
    # excessive-seats treatment at allocation, after every vote is drawn -- and
    # the first three versions of this test could not see it. Three
    # false-negative channels in one test written to catch false negatives:
    # list-only, then no ward wins, then no seats.
    seats = max(abs(bs.get(p, 0.0) - os.get(p, 0.0))
                for p in set(bs) | set(os)) if (bs or os) else 0.0
    return max(100 * share, float(wins), float(seats))


# --------------------------------------------------------------------------
# the shipped base run, once per target, with its trace kept
# --------------------------------------------------------------------------
# Three tests need the unperturbed run: the sweep, the gate proofs and the
# module-constant sweep. It is memoised so the file does not pay for it three
# times, and it is memoised ONLY for the shipped configuration -- `_patched`
# refuses to let anything be cached while a module constant is held at a value
# it does not ship at, because a base measured under a patch is the fault this
# whole file is about, one level up.
_BASE: dict[str, tuple] = {}
_TRACE: dict[str, Path] = {}
_PATCH_DEPTH = 0
_TRACE_ROOT: Path | None = None


def _trace_root() -> Path:
    global _TRACE_ROOT
    if _TRACE_ROOT is None:
        _TRACE_ROOT = Path(tempfile.mkdtemp(prefix="levers-trace-"))
        import atexit
        atexit.register(shutil.rmtree, _TRACE_ROOT, True)
    return _TRACE_ROOT


def _base(year: str, draws: int | None = None):
    """The unperturbed run at `year`, with a trace on disk beside it.

    ``draws`` overrides the module default for a lever that needs more
    resolution; that base is cached separately and carries no trace.
    """
    assert _PATCH_DEPTH == 0, (
        "a base run was requested while a module constant is patched. Cache it "
        "and every later comparison is against a configuration this project "
        "does not ship.")
    if draws is not None and draws != DRAWS:
        # A comparison must be against a base at the SAME draw count and seed,
        # or the difference measured is the sample, not the lever.
        if (year, draws) not in _BASE:
            _BASE[(year, draws)] = _run(year, [], draws=draws)
        return _BASE[(year, draws)]
    if year not in _BASE:
        run_dir = _trace_root() / year
        _BASE[year] = _run(year, [], run_dir=run_dir)
        _TRACE[year] = run_dir
    return _BASE[year]


def _trace(year: str, stage: str) -> dict:
    """One stage of the base run's trace, as a dict."""
    _base(year)
    path = _TRACE[year] / f"{stage}.json"
    assert path.exists(), (
        f"the base run at {year} wrote no {stage}.json. A gate check that reads "
        f"the trace cannot fall back to reasoning -- if the stage has been "
        f"renamed, the check must be rewritten against the new name, not "
        f"dropped.")
    return json.loads(path.read_text())


@contextlib.contextmanager
def _patched(module, name: str, value):
    """Hold a MODULE constant at `value` for the duration.

    `--set` reaches `DEFAULTS` keys and nothing else, which is why 42 of the 48
    constants pre-registered for the B2 sweep have never been swept at all
    (NULL-RESULTS.md §3). In one process a module constant is reachable, and
    `montecarlo` resolves the ones that matter at CALL time -- `LEVEL_DF` was
    changed to do exactly that after it spent weeks bound as a default argument
    and swept 2.5 -> 1000 for byte-identical output.

    Restored in a `finally`, because these are process-global and the suite
    runs every module in one process.
    """
    global _PATCH_DEPTH
    before = getattr(module, name)
    _PATCH_DEPTH += 1
    try:
        setattr(module, name, value)
        yield
    finally:
        setattr(module, name, before)
        _PATCH_DEPTH -= 1


def _sweep_paired(year: str, base) -> list[str]:
    """Perturb a conditional lever TOGETHER WITH ITS GATE.

    A lever behind a gate reads as dead when the gate is shut, and that is not a
    fact about the lever. `poll_k` was certified inert on exactly that mistake —
    measured with `poll_id=None`, so the branch never ran — and the null was
    written into this file and into MODEL-LOG. Opened, the same lever moves the
    DA by 3.4pp and nine seats.
    """
    dead = []
    jobs, labels = [], []
    for label, keys in sorted(PAIRED.items()):
        if not all(k in M.DEFAULTS for k in keys):
            dead.append(f"{label}: {sorted(set(keys) - set(M.DEFAULTS))} not in DEFAULTS")
            continue
        jobs.append((year, [f"{k}={json.dumps(v)}" for k, v in keys.items()]))
        labels.append((label, sorted(keys)))
    for (label, keys), result in zip(labels, _run_many(jobs)):
        if _moves(base, result) < 1e-9:
            dead.append(f"{label} at {year} (perturbed {keys} together, "
                        f"nothing moved)")
    return dead


def _sweep_target(year: str) -> list[str]:
    base = _base(year)
    dead = _sweep_paired(year, base)
    # json.dumps, not an f-string: `--set` parses its value as JSON, and
    # Python's repr of a dict uses single quotes, which json.loads rejects.
    # It then falls back to storing the raw STRING, and the model gets a
    # str where it expects a mapping — which is an AttributeError deep in
    # run_model rather than a clear failure here.
    keys = [k for k, _v in sorted(PERTURB.items()) if k in M.DEFAULTS]
    jobs = [(year, [f"{k}={json.dumps(PERTURB[k])}"], RESOLUTION.get((k, year)))
            for k in keys]
    results = _run_many(jobs)
    for key, result in zip(keys, results):
        value = PERTURB[key]
        # Against a base at the SAME draw count, or the difference measured is
        # the sample rather than the lever.
        moved = _moves(_base(year, RESOLUTION.get((key, year))), result)
        why = EXPECTED_INERT.get((key, year))
        if moved < 1e-9 and why is None:
            # Name the year. Without it a key that is inert at one target and
            # live at the other reports identically to one that is dead
            # everywhere, and the reader cannot tell which -- that cost a
            # diagnosis when `overhang_rule` went inert at 2021 alone.
            dead.append(f"{key} at {year} (perturbed to {value}, nothing moved)")
        elif moved >= 1e-9 and why is not None:
            dead.append(f"{key} IS live at {year} but EXPECTED_INERT claims it is "
                        f"not: {why.code} — {why.reason!r} — the register is now "
                        f"wrong, delete the entry")
    return dead


# --------------------------------------------------------------------------
# GATES — the evidence half of a cause code
# --------------------------------------------------------------------------
# A declaration of what a thing reads is a CLAIM; a check of what was actually
# read, at what value, is the EVIDENCE (ARCHITECTURE.md's lists A/B against
# C/D). Every UNDELIVERED entry above names one of these, and every one of them
# looks at the same object the model looks at rather than restating the belief.
#
# They are deliberately CHEAP. Five of the seven need no model run at all, which
# is what makes it reasonable to demand one from every entry: an excuse whose
# gate nobody can check is reopened, not accepted (NULL-RESULTS.md §4.2).


def _joburg(year: str):
    city = cityconfig.use("joburg")
    return city, cityconfig.use_target(year)


def _spec_path(target):
    # The same expression `run_model` uses to find the emitted spec. If it ever
    # diverges, the gate check is looking at a file the model does not read.
    return target.city.processed / f"pools_{target.year}.json"


def _gate_bye_deltas_absent(year: str) -> tuple[bool, str]:
    """`bye` is empty, so `w_bye` multiplies nothing."""
    _, target = _joburg(year)
    path = target.processed / "byelection_party_deltas.csv"
    return not path.exists(), f"{path} {'exists' if path.exists() else 'absent'}"


def _gate_bye_contest_detail_absent(year: str) -> tuple[bool, str]:
    """The ward-local by-election block's input file is not there."""
    _, target = _joburg(year)
    path = target.processed / "byelection_contest_detail.csv"
    return not path.exists(), f"{path} {'exists' if path.exists() else 'absent'}"


def _gate_no_metro_poll(year: str) -> tuple[bool, str]:
    """No admitted metro poll, so `_agg` is None and the poll block is skipped."""
    import polling as _pg
    _, target = _joburg(year)
    screened, _declined = _pg.screen(
        target, min_n=float(M.DEFAULTS["poll_min_n"]))
    metro = [q.get("id") for q in screened if q.get("scope") == "metro"]
    return not metro, (f"polling.screen admits {len(screened)} poll(s) at "
                       f"{year}; metro among them: {metro or 'none'}")


def _gate_no_arrival_group_spec(year: str) -> tuple[bool, str]:
    """The emitted spec carries no arrival group, so the draw has nothing."""
    _, target = _joburg(year)
    path = _spec_path(target)
    if not path.exists():
        return True, f"no pool spec at {path}"
    group = json.loads(path.read_text()).get("arrival_group")
    return not group, (f"{path.name} arrival_group = "
                       + ("null" if group is None else
                          f"{len(group)} fields — THE GATE IS OPEN"))


def _gate_real_contestation_lists(year: str) -> tuple[bool, str]:
    """Real ward lists exist, so the projection the lever drives is not called."""
    import levels as _levels
    city, target = _joburg(year)
    published = _levels.contestation(target, city)
    return bool(published), (
        f"levels.contestation returns {len(published)} parties at {year} "
        + ("(real lists supersede the projection)" if published else
           "(nothing published — THE PROJECTION RUNS AND THE LEVER IS LIVE)"))


def _gate_sigma_two_term_shipped_on(year: str) -> tuple[bool, str]:
    """The shipped sigma deletes the cap `poll_house_k` sets."""
    import polling as _pg
    return bool(_pg.SIGMA_TWO_TERM), (
        f"polling.SIGMA_TWO_TERM = {_pg.SIGMA_TWO_TERM!r}, so montecarlo takes "
        f"`_cap = 1.0` and never calls weight_cap(house_k=...)")


def _gate_local_bye_weights_shipped_off(year: str) -> tuple[bool, str]:
    """Both ward-local weights ship at 0.0, so the block they gate never runs."""
    w = (float(M.DEFAULTS["w_bye_local_ward"]), float(M.DEFAULTS["w_bye_local_pr"]))
    return not any(w), (f"DEFAULTS w_bye_local_ward={w[0]}, w_bye_local_pr={w[1]}"
                        + ("" if not any(w) else " — THE GATE IS OPEN"))


def _gate_level_sd_fallback_never_binds(year: str) -> tuple[bool, str]:
    """No party can reach `sd_measured.get(party, sd_default)`'s second argument.

    Two consumers, and the gate must be shut for both: `sd_for_party`, which
    only sees parties on the `individual` path, and the poll blend's
    `_sd.get(party, default)`, which only runs where a metro poll is admitted.

    This is the one gate that needs the model. It reads the base run's index and
    the base run's own trace — the measured sd(log θ) as the run actually had
    it — rather than recomputing either, because a check that recomputes its
    subject is checking its own arithmetic.
    """
    base = _base(year)
    index = set(base[4])
    _, target = _joburg(year)
    spec = json.loads(_spec_path(target).read_text())
    members = {p for cfg in spec["pools"].values() for p in cfg["members"]}
    measured = set(_trace(year, "10_theta_prior").get("sd") or {})
    # `handled` is exactly this, in make_drawer: a party in any pool.
    individual = index - members - {"ENTRANT"}
    exposed = individual - measured
    detail = (f"{len(index)} parties in the index, {len(index & members)} of "
              f"them pool members, so the individual path holds "
              f"{len(individual)}")
    if _gate_no_metro_poll(year)[0]:
        detail += "; the poll blend does not run at this target"
    else:
        polled = index - {"ENTRANT"} - measured
        exposed |= polled
        detail += (f"; the poll blend runs and {len(polled)} of the index has "
                   f"no measured sd")
    return not exposed, detail + (f"; EXPOSED TO THE FALLBACK: {sorted(exposed)}"
                                  if exposed else "")


GATES = {
    "bye_deltas_absent": _gate_bye_deltas_absent,
    "bye_contest_detail_absent": _gate_bye_contest_detail_absent,
    "no_metro_poll": _gate_no_metro_poll,
    "no_arrival_group_spec": _gate_no_arrival_group_spec,
    "real_contestation_lists": _gate_real_contestation_lists,
    "sigma_two_term_shipped_on": _gate_sigma_two_term_shipped_on,
    "local_bye_weights_shipped_off": _gate_local_bye_weights_shipped_off,
    "level_sd_fallback_never_binds": _gate_level_sd_fallback_never_binds,
}


# --------------------------------------------------------------------------
# CONDITIONAL — open the gate, then perturb the lever
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Conditional:
    """A lever measured with its gate held open.

    `PAIRED` above perturbs a lever AND its gate together and asks whether the
    pair moves anything. That is not the same question, and on these three it
    would answer yes for the wrong reason: `w_bye_local_ward` moves the forecast
    all by itself, so a pair containing it passes however dead the lever is.

    So this holds the gate open in BOTH runs and perturbs only the lever. What
    it measures is the lever, at a configuration the project does not ship —
    which is the only honest thing to say about a lever whose gate is shut.
    """

    key: str
    year: str
    value: object
    opens: str                      # the GATES key this configuration opens
    gate_scenario: tuple = ()       # ((scenario key, value), ...)
    gate_module: tuple = ()         # ((module name, CONSTANT, value), ...)
    why: str = ""


CONDITIONAL: dict[str, Conditional] = {
    "bye_local_cap@2026": Conditional(
        key="bye_local_cap", year="2026", value=40.0,
        opens="local_bye_weights_shipped_off",
        gate_scenario=(("w_bye_local_ward", 0.9), ("w_bye_local_pr", 0.9)),
        why="the cap on one contest's logit shift. At the shipped 1.5 it binds "
            "on 11 of the 65 party-contests; the question this asks is whether "
            "the model can tell the difference between that and no cap at all."),
    "bye_tau_months@2026": Conditional(
        key="bye_tau_months", year="2026", value=400.0,
        opens="local_bye_weights_shipped_off",
        gate_scenario=(("w_bye_local_ward", 0.9), ("w_bye_local_pr", 0.9)),
        why="the recency half-life on by-election evidence. 400 months is "
            "exp(-age/tau) ~ 1 for every contest in the window, i.e. no decay, "
            "against the shipped 18."),
    "poll_house_k@2026": Conditional(
        key="poll_house_k", year="2026", value=6.0,
        opens="sigma_two_term_shipped_on",
        gate_module=(("polling", "SIGMA_TWO_TERM", False),),
        why="the retired weight cap. The EXPECTED_INERT entry keeps the lever "
            "on the grounds that `SIGMA_TWO_TERM=0` still reads it — so that is "
            "the configuration it is measured in. If this ever goes dead the "
            "entry's own justification has gone with it and the lever should "
            "be deleted."),
}


def _module(name: str):
    import importlib
    return importlib.import_module(name)


def _sweep_conditional() -> list[str]:
    """Every gate the harness can open, opened."""
    dead: list[str] = []
    gate_base: dict[tuple, tuple] = {}
    for label, c in sorted(CONDITIONAL.items()):
        # BEFORE the runs. `parse_set` rejects a key that is not already in the
        # scenario, so a stale name here would raise from deep inside
        # `load_scenario` instead of naming itself -- and a deleted lever must
        # report as a deleted lever, which is the whole of §1.68.
        absent = [k for k, _ in c.gate_scenario if k not in M.DEFAULTS]
        if c.key not in M.DEFAULTS or absent:
            dead.append(f"{label}: not DEFAULTS keys, so nothing was perturbed: "
                        f"{sorted(set(absent) | ({c.key} - set(M.DEFAULTS)))}")
            continue
        overrides = [f"{k}={json.dumps(v)}" for k, v in c.gate_scenario]
        with contextlib.ExitStack() as stack:
            for mod, const, value in c.gate_module:
                stack.enter_context(_patched(_module(mod), const, value))
            sig = (c.year, tuple(overrides), c.gate_module)
            if sig not in gate_base:
                gate_base[sig] = _run(c.year, overrides)
            moved = _moves(gate_base[sig],
                           _run(c.year, overrides
                                + [f"{c.key}={json.dumps(c.value)}"]))
        if moved < 1e-9:
            dead.append(f"{label}: gate opened ({c.opens}) and the lever still "
                        f"did not move at {c.value!r}")
    return dead


# --------------------------------------------------------------------------
# MODULE_PERTURB — the class `--set` cannot reach
# --------------------------------------------------------------------------
# NULL-RESULTS.md §3, gap 1: "Coverage is DEFAULTS keys only. The 42 blocked
# constants are mostly MODULE constants — montecarlo.LEVEL_DF, SHARE_FLOOR,
# DIRICHLET_FLOOR, TURNOUT_DRAW_FLOOR/CEILING, the whole polling.SIGMA_* family
# — none of which is in DEFAULTS, so none is swept for liveness."
#
# This is a start on that and not the end of it: five constants, at 2026 only,
# chosen because each is a judgement someone made and none is reachable from a
# scenario key. A constant that IS shadowed by a DEFAULTS key (DIRICHLET_FLOOR,
# TURNOUT_CORRELATION) is already swept through it and is not repeated here.
#
# 2026 alone, and the reason is not economy: at 2021 `BYE_MIN_WEIGHT` guards a
# `bye` dict that is empty, so it would land straight back in EXPECTED_INERT as
# another UNDELIVERED entry. Sweeping a constant where its evidence exists is
# the whole lesson of this file.
MODULE_PERTURB: tuple = (
    ("montecarlo", "LEVEL_DF", "2026", 2.5,
     "the t degrees of freedom on the level shock, and this project's founding "
     "CLASS 12 defect: swept 2.5 -> 1000 for BYTE-IDENTICAL output while bound "
     "as `def log_shock(..., df=LEVEL_DF)`, evaluated once at import. It now "
     "resolves at call time, and this is the test that says so."),
    ("montecarlo", "SHARE_FLOOR", "2026", 0.05,
     "the floor a share is clipped to before the logit. NULL-RESULTS.md §1 B "
     "names this clip as an ABSORBER — a party under the floor stops responding "
     "to theta entirely — so what it does at 25x is worth having measured."),
    ("montecarlo", "BYE_MIN_WEIGHT", "2026", 1.0,
     "how much by-election weight a party needs before its evidence is used at "
     "all. It gates `w_bye`, which is 🔴 argued-not-tested, and nothing has "
     "ever swept it."),
    ("montecarlo", "TURNOUT_DRAW_CEILING", "2026", 0.50,
     "the ceiling on a drawn turnout. A guard that has gone blind reports "
     "exactly what a guard that never fires reports."),
    ("polling", "SIGMA_TWO_TERM", "2026", False,
     "the switch between the shipped two-term sigma and the retired "
     "four-component one. `poll_house_k`'s whole EXPECTED_INERT entry rests on "
     "this being reachable; this is the check that it still is."),
)


def _sweep_module_constants() -> list[str]:
    dead: list[str] = []
    for mod_name, const, year, value, _why in MODULE_PERTURB:
        module = _module(mod_name)
        assert hasattr(module, const), (
            f"{mod_name}.{const} does not exist. A constant named here and gone "
            f"from the source is coverage that deleted itself — the fault "
            f"`test_every_defaults_key_is_swept_or_excused` exists to catch, "
            f"one namespace over.")
        base = _base(year)
        with _patched(module, const, value):
            moved = _moves(base, _run(year, []))
        if moved < 1e-9:
            dead.append(f"{mod_name}.{const} at {year} (set to {value!r}, "
                        f"nothing moved)")
    return dead


def test_every_tunable_lever_actually_moves_the_forecast():
    """A lever that cannot change the answer is not a judgement call.

    `LEVEL_DF` was swept at 2.5 through 1000 and returned byte-identical output,
    while sitting at 🔴 in the register as one of the model's most-argued
    constants. `polling_lean` is computed, passed to `pool_spec`, and never read
    by it. Both were found by accident. This finds them on purpose.
    """
    dead = _sweep_target("2021") + _sweep_target("2026")
    assert not dead, (
        "these levers did not move the forecast when perturbed to a value that "
        "must change it:\n  " + "\n  ".join(dead) +
        "\nEither wire the lever up, delete it from DEFAULTS and from "
        "JUDGEMENT-CALLS.md, or add it to EXPECTED_INERT with the reason it is "
        "legitimately inert at that target. A constant nobody can move is not a "
        "choice the project made — see ITERATING.md rule 6.")


def test_every_defaults_key_is_swept_or_excused():
    """A lever deleted from DEFAULTS must not silently delete its own coverage.

    `PERTURB` was a hand-maintained allowlist, and hand-maintained allowlists
    rot. An independent reviewer found it covered **13 of 27** DEFAULTS keys —
    omitting `ward_pr_ratio_overrides`, which this file's own docstring names as
    one of the four instances that motivated it. Worse, three PERTURB entries
    were being *silently skipped* by the `key not in M.DEFAULTS` guard:
    `polling_lean` and `polling_span`, which had just been deleted (so a
    deletion removed test coverage with no failure at all), and
    `turnout_correlation`, which is the module constant `TURNOUT_CORRELATION`
    and had therefore never been exercised despite appearing in the list.

    `test_every_tunable_constant_is_in_the_judgement_register` gets this right by
    ENUMERATING rather than listing. This does the same, in both directions.
    """
    keys = set(M.DEFAULTS)
    missing = sorted(keys - set(PERTURB) - set(OPERATIONAL) - set(STATUTORY))
    assert not missing, (
        "these DEFAULTS keys are never perturbed, so nothing would notice if "
        f"they stopped doing anything:\n  {missing}\n"
        "Give each a perturbation in PERTURB, name it in OPERATIONAL with the "
        "reason it is not a model judgement, or name it in STATUTORY if the "
        "project does not get to choose it at all.")

    # The two halves of the statutory claim must agree, in BOTH directions: a
    # key named here must be nailed down in the source, and every key nailed
    # down there must be named here. One without the other is a claim nobody
    # checks -- and the source list is what actually refuses the override.
    assert set(STATUTORY) == set(M.STATUTORY_VALUES), (
        f"STATUTORY here is {sorted(STATUTORY)} and "
        f"montecarlo.STATUTORY_VALUES is {sorted(M.STATUTORY_VALUES)}. A "
        f"statutory key named in one and not the other is either an "
        f"unenforced claim or an unexplained refusal.")
    for key, want in M.STATUTORY_VALUES.items():
        assert M.DEFAULTS[key] == want, (
            f"DEFAULTS[{key!r}] is {M.DEFAULTS[key]!r} but the statute is "
            f"{want!r} -- the shipped default is not the law.")

    stale = sorted(set(PERTURB) - keys - set(_MODULE_LEVEL))
    assert not stale, (
        "these PERTURB entries are not DEFAULTS keys, so the sweep SILENTLY "
        f"SKIPS them and reports success:\n  {stale}\n"
        "Either they were deleted — in which case remove them here and say so "
        "in MODEL-LOG — or they are module constants, which need naming in "
        "_MODULE_LEVEL and reaching a different way.")


def test_no_function_argument_is_accepted_and_never_used():
    """An unused parameter is a lever the caller believes in and the callee ignores.

    `pool_spec(scenario, base_city_d, centres, index, lean, ipf_out)` never
    references `lean` OR `base_city_d`. The caller computes `lean` from
    `polling_lean * polling_span` and passes it in good faith. The independent
    review caught `lean`; `base_city_d` it missed, which is the argument for a
    test rather than a reading.
    """
    import ast

    offenders = []
    for path in sorted((ROOT / "src").glob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            args = [a.arg for a in node.args.args + node.args.kwonlyargs]
            used = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
            used |= {n.attr for n in ast.walk(node) if isinstance(n, ast.Attribute)}
            for a in args:
                if a in ("self", "cls") or a.startswith("_"):
                    continue
                key = f"{path.name}:{node.name}({a})"
                if a not in used and key not in DELIBERATELY_UNUSED:
                    offenders.append(f"{path.name}:{node.lineno} {node.name}({a})")
    assert not offenders, (
        "these functions accept an argument they never read, so every caller "
        "passing it is passing it into nothing:\n  " + "\n  ".join(offenders) +
        "\nDelete the parameter and its call sites, or use it. If it exists only "
        "to satisfy a uniform dispatch interface, add it to DELIBERATELY_UNUSED "
        "with the reason — an ignored argument should be a claim someone made, "
        "not a thing nobody noticed.")


def test_no_scenario_key_is_read_without_being_declared():
    """CLASS 11, THE VARIANT NO LEVER GUARD CAN SEE.

    Every other guard in this file iterates `DEFAULTS`. **A key that is read but
    never declared is invisible to all of them**, and it is not inert — it is
    frozen at whatever fallback the `scenario.get` call supplies, and it cannot
    be moved by `--set` or by a config file, because `parse_set` and
    `read_scenario_file` both reject a key that is not already in the scenario.

    Three live instances on 2026-08-20, all found at once and all pre-existing:

      * `arrival_group_draw` — the whole arrival-group mechanism, which
        `MACHINERY.md` described as a *switched-off lever* and whose own code
        comment said "DEFAULT OFF". There was no switch and no default. It was
        also broken: the branch raised `NameError: dirichlet_floor` the first
        time anything reached it, and a code comment scheduled a retry "by 2026"
        against a crash. MODEL-LOG §1.63.
      * `level_sd_default` — `scenario.get("level_sd_default", 0.45)` at two
        sites, registered in `JUDGEMENT-CALLS.md` at its own name, and frozen at
        0.45 for anyone who tried to change it.
      * `turnout_correlation` — `scenario.get("turnout_correlation",
        TURNOUT_CORRELATION)`, registered at 🟡 with a note that one constant for
        every city and pool pair is a judgement, and unsweepable.

    A registered constant that cannot be swept is `LEVEL_DF` again (§1.33), and
    this is the third form it has taken. The check is static and cheap: parse
    `montecarlo.py`, collect every literal key passed to `scenario.get`, and
    require it to be declared, injected at runtime, or underscore-private.
    """
    keys: dict[str, int] = {}
    tree = ast.parse((SRC / "montecarlo.py").read_text())
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "scenario"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)):
            continue
        keys.setdefault(node.args[0].value, node.lineno)

    assert keys, ("no `scenario.get(\"...\")` calls found at all, so this test "
                  "is checking nothing — the access pattern has changed and the "
                  "guard must be rewritten, not deleted")

    undeclared = {k: ln for k, ln in keys.items()
                  if not k.startswith("_")
                  and k not in M.DEFAULTS
                  and k not in RUNTIME_INJECTED}
    assert not undeclared, (
        "these scenario keys are READ but never DECLARED, so each is frozen at "
        "the fallback in its own `scenario.get` call and cannot be moved by "
        "`--set` or by a config file:\n  "
        + "\n  ".join(f"montecarlo.py:{ln} {k!r}"
                       for k, ln in sorted(undeclared.items(),
                                           key=lambda kv: kv[1]))
        + "\nAdd it to DEFAULTS at the value it is currently frozen at — which "
          "changes no number and makes it sweepable — or, if the run writes it "
          "rather than reading a choice, add it to RUNTIME_INJECTED with the "
          "stage that writes it.")

    stale = sorted(set(RUNTIME_INJECTED) - set(keys))
    assert not stale, (
        f"RUNTIME_INJECTED names {stale}, which `montecarlo.py` no longer reads. "
        f"An excuse for a key that is gone hides the next real one; delete it.")

def test_every_named_fallback_resolves_to_the_declared_default():
    """CLASS 18 — THE WHOLE CLASS, NOT THE INSTANCE.

    **This test used to police LITERAL fallbacks — `scenario.get("k", 120.0)` —
    and on 2026-08-24 it failed by finding none, which is the correct outcome
    and the reason its self-check existed.** Every literal fallback in `src/`
    was replaced by `DEFAULTS[...]`, and the structural guard
    `test_no_scenario_fallback_is_a_bare_literal` now refuses new ones outright.
    An equality check over a set that is empty by construction passes forever
    while checking nothing, so the guarantee moved rather than being deleted.

    What is left to police is the fallback that is a NAMED CONSTANT —
    `scenario.get("turnout_correlation", TURNOUT_CORRELATION)`. That is the
    good pattern and it is still two objects: a module constant and a `DEFAULTS`
    entry. `montecarlo` had an import-time assert linking exactly ONE of the six
    poll constants to its default; the other five were unlinked. This is that
    assert, generalised, with no allowlist.

    MODEL-LOG §1.85, §1.93.
    """
    import ast as _ast

    # every module-level numeric constant in src/, by name
    constants: dict[str, list[tuple[str, float]]] = {}
    for path in sorted((ROOT / "src").glob("*.py")):
        try:
            tree = _ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in tree.body:
            if not isinstance(node, _ast.Assign) or len(node.targets) != 1:
                continue
            tgt = node.targets[0]
            if not (isinstance(tgt, _ast.Name) and tgt.id.isupper()):
                continue
            if not (isinstance(node.value, _ast.Constant)
                    and isinstance(node.value.value, (int, float))
                    and not isinstance(node.value.value, bool)):
                continue
            constants.setdefault(tgt.id, []).append((path.name, node.value.value))

    offenders, checked = [], 0
    for path in sorted((ROOT / "src").glob("*.py")):
        try:
            tree = _ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in _ast.walk(tree):
            if not (isinstance(node, _ast.Call)
                    and isinstance(node.func, _ast.Attribute)
                    and node.func.attr == "get"
                    and isinstance(node.func.value, _ast.Name)
                    and node.func.value.id == "scenario"
                    and len(node.args) == 2
                    and isinstance(node.args[0], _ast.Constant)
                    and isinstance(node.args[0].value, str)):
                continue
            key, fb = node.args[0].value, node.args[1]
            if isinstance(fb, _ast.Name):
                name = fb.id
            elif isinstance(fb, _ast.Attribute):
                name = fb.attr                    # `_pg.POLL_HALF_LIFE_DAYS`
            else:
                continue                          # DEFAULTS[...] and friends
            if key not in M.DEFAULTS or name not in constants:
                continue
            declared = M.DEFAULTS[key]
            if not isinstance(declared, (int, float)) or isinstance(declared, bool):
                continue
            for where, value in constants[name]:
                checked += 1
                if abs(float(value) - float(declared)) > 1e-12:
                    offenders.append(
                        f"{path.name}:{node.lineno}  scenario.get({key!r}, {name}) "
                        f"-> {where} defines {name} = {value!r}, but "
                        f"DEFAULTS[{key!r}] = {declared!r}")

    assert checked, (
        "no `scenario.get(key, NAMED_CONSTANT)` calls found at all — either the "
        "pattern changed or this test has stopped looking, and it would then "
        "pass forever while checking nothing. That is exactly how its previous "
        "form ended: the literals it policed were all removed (§1.93).")
    assert not offenders, (
        "a named-constant fallback disagrees with the declared default:\n  "
        + "\n  ".join(sorted(set(offenders)))
        + "\n\nTwo values for one lever, resolved by different code paths, is how "
          "`poll_half_life_days` moved 5.6pp of ANC through a path no sweep could "
          "reach (§1.84). The constant and the DEFAULTS entry must agree.")


def test_no_lever_is_passed_to_one_consumer_and_withheld_from_another():
    """CLASS 18 — A LEVER THAT REACHES THE WIDTH AND NOT THE CENTRE.

    `test_every_tunable_lever_actually_moves_the_forecast` asks whether a lever
    moves the forecast AT ALL. `poll_half_life_days` passed that test at 2026
    for weeks while being **half** connected: `montecarlo` passed
    `scenario["poll_half_life_days"]` to `polling.effective_houses` and
    `polling.aggregate_sd` — the WIDTH — and passed nothing to
    `polling.aggregate`, the CENTRE, which therefore used a hardcoded `120.0`
    default argument that no sweep could reach. The ANC's blended share runs
    18.4% to 24.0% across that lever's range in the live 2026 forecast.

    So the existing test cannot see this: the lever DOES move the forecast, just
    not through the path anyone reading the register would assume. This one
    checks the shape instead — if a scenario key is passed to some calls of a
    module's functions and withheld from others, say so.

    **WHAT THIS STILL CANNOT SEE**, stated so it is not mistaken for complete:
    keys forwarded through a `**kwargs` splat, keys forwarded positionally, and
    consumers outside `polling`. The guard that DOES cover the whole class
    mechanically is `test_every_literal_fallback_equals_the_declared_default`
    above; this one is the narrower structural check.

    MODEL-LOG §1.84, widened §1.85.
    """
    import ast as _ast
    src = (ROOT / "src" / "montecarlo.py").read_text(encoding="utf-8")
    tree = _ast.parse(src)

    # every keyword= that forwards a scenario.get("<key>") into a call
    forwarded: dict[str, set[str]] = {}
    withheld: dict[str, set[str]] = {}
    for node in _ast.walk(tree):
        if not isinstance(node, _ast.Call):
            continue
        fn = node.func
        name = (fn.attr if isinstance(fn, _ast.Attribute)
                else fn.id if isinstance(fn, _ast.Name) else None)
        if not name:
            continue
        for kw in node.keywords:
            for sub in _ast.walk(kw.value):
                if (isinstance(sub, _ast.Call)
                        and isinstance(sub.func, _ast.Attribute)
                        and sub.func.attr == "get"
                        and isinstance(sub.func.value, _ast.Name)
                        and sub.func.value.id == "scenario"
                        and sub.args
                        and isinstance(sub.args[0], _ast.Constant)
                        and isinstance(sub.args[0].value, str)):
                    forwarded.setdefault(sub.args[0].value, set()).add(name)

    # For each forwarded key, find calls to POLLING functions that take that
    # parameter and were called WITHOUT it.
    import polling as _pg
    import inspect as _inspect
    # EVERY public callable in `polling`, not a three-name allowlist. The first
    # version of this test hardcoded ("aggregate", "aggregate_sd",
    # "effective_houses") — which could not see `screen`, whose `min_n` is the
    # live `poll_min_n` lever. An independent review named it as this project's
    # own recurring lesson: "a guard written against one route through a
    # function is not a guard on the function." MODEL-LOG §1.85.
    candidates = [n for n in dir(_pg)
                  if not n.startswith("_") and callable(getattr(_pg, n, None))
                  and getattr(getattr(_pg, n), "__module__", "") == _pg.__name__]
    for key, fns in forwarded.items():
        # match on the parameter name OR the key, and try the poll_ prefix both
        # ways, so a lever whose parameter breaks the naming convention is still
        # compared rather than silently skipped.
        aliases = {key, key.replace("poll_", ""), "poll_" + key}
        for cand in candidates:
            f = getattr(_pg, cand, None)
            if f is None:
                continue
            try:
                sig = _inspect.signature(f)
            except (TypeError, ValueError):
                continue
            if not (aliases & set(sig.parameters)):
                continue
            # A consumer that DOCUMENTS the parameter as accepted-and-ignored is
            # not withholding it — it is declining it, on the record. `validate`
            # accepts `min_n` and ignores it because §1.69 moved the sample-size
            # floor from validation to screening: a small poll is
            # well-formed-but-inadmissible, not malformed. The exemption must be
            # written in the docstring, so it is discoverable from the code
            # rather than hidden in this test.
            doc = (_inspect.getdoc(f) or "").lower()
            if any(f"``{a}`` is accepted and ignored" in doc
                   or f"{a} is accepted and ignored" in doc for a in aliases):
                continue
            for node in _ast.walk(tree):
                if (isinstance(node, _ast.Call)
                        and isinstance(node.func, _ast.Attribute)
                        and node.func.attr == cand):
                    passed = {k.arg for k in node.keywords}
                    # a `**kwargs` splat may carry it; that is invisible here,
                    # so a splat call is not reported rather than false-flagged.
                    if any(k.arg is None for k in node.keywords):
                        continue
                    if node.args:
                        continue          # positional forwarding, not inspectable
                    if not (passed & aliases):
                        withheld.setdefault(key, set()).add(cand)

    assert not withheld, (
        "scenario keys forwarded to some consumers and WITHHELD from others:\n  "
        + "\n  ".join(f"`{k}` reaches {sorted(forwarded.get(k, ()))} "
                      f"but is NOT passed to {sorted(v)}"
                      for k, v in sorted(withheld.items()))
        + "\n\nA half-connected lever passes "
          "`test_every_tunable_lever_actually_moves_the_forecast` — it moves the "
          "forecast through the path it IS wired to — while the register "
          "describes a value that the other path never sees. That is how "
          "`poll_half_life_days` moved 5.6pp of ANC unreachably. Pass it, or "
          "explain in the call why this consumer takes a different value.")


def test_no_scenario_fallback_is_a_bare_literal():
    """A declared default must be declared ONCE.

    Twenty `scenario.get(...)` call sites in `montecarlo` carried a bare literal
    fallback and not one of them read `DEFAULTS`. Every literal happened to
    equal its declared default, so the equality guard beside this test passed —
    and that is exactly the state a third copy is born into. `montecarlo` was
    inconsistent with ITSELF: one call wrote `_pg.POLL_HALF_LIFE_DAYS` and
    another thirty lines later wrote `120.0`.

    The rule this asserts is structural rather than numerical: a fallback is
    `DEFAULTS[...]` or a named module constant, never a number typed again.
    MODEL-LOG 1.93.
    """
    import ast as _ast
    import re as _re
    text = (ROOT / "src" / "montecarlo.py").read_text()
    pat = _re.compile(r'scenario\.get\(\s*"([a-z_]+)"\s*,\s*([^()]*?)\s*\)', _re.S)
    offenders = []
    for key, fallback in pat.findall(text):
        fallback = fallback.strip()
        if fallback.startswith("DEFAULTS["):
            continue
        try:
            _ast.literal_eval(fallback)
        except Exception:
            continue                      # a named constant — that is the point
        offenders.append(f'scenario.get("{key}", {fallback})')
    assert not offenders, (
        "a declared default is typed again as a literal at the call site:\n  "
        + "\n  ".join(sorted(set(offenders)))
        + "\nUse DEFAULTS[...] or a named module constant. A literal that merely "
          "HAPPENS to equal the default today is the defect, not the drift that "
          "follows it.")


def test_no_dict_literal_declares_the_same_key_twice():
    """`PERTURB` set `turnout_correlation` twice and Python kept the last.

    The first entry carried the explanation — "independent pools; was frozen at
    0.63" — and never ran. A sweep silently testing a different value than its
    own comment describes is worse than an unswept lever, because it reports a
    result.

    Cheap, total, and it walks every dict literal in `src/` and `tests/`.
    MODEL-LOG 1.93.
    """
    import ast as _ast
    from collections import Counter as _Counter
    bad = []
    files = (sorted((ROOT / "src").glob("*.py"))
             + sorted((ROOT / "tests").glob("*.py")))
    parsed, can_fail = [], []
    for path in files:
        try:
            tree = _ast.parse(path.read_text())
        except SyntaxError:
            continue
        parsed.append(path)
        for node in _ast.walk(tree):
            if not isinstance(node, _ast.Dict):
                continue
            keys = [k.value for k in node.keys
                    if isinstance(k, _ast.Constant) and isinstance(k.value, str)]
            if len(keys) > 1:
                # Only a dict with two or more string keys CAN declare one
                # twice. That subset is the population this claim is about.
                can_fail.append(f"{path.name}:{node.lineno}")
            for key, n in _Counter(keys).items():
                if n > 1:
                    bad.append(f"{path.name}:{node.lineno} declares {key!r} {n} times")
    # (1) IT LOOKED. `assert not bad` is satisfied by parsing nothing, and a
    # single SyntaxError in a file this walk touches drops it silently through
    # the `continue` above. Both bounds are fractions of the file count, so
    # neither goes stale as the tree grows — 84 files and 449 two-key dicts on
    # 2026-08-31.
    scanned(parsed, of=files, low=1.0, high=1.0,
            what="files this walk parsed",
            denominator=".py files in src/ and tests/")
    scanned(can_fail, of=files, low=2.0, high=20.0,
            what="dict literals with two or more string keys — the only ones "
                 "that CAN declare a key twice",
            denominator=".py files in src/ and tests/")
    assert not bad, (
        "a dict literal declares one key more than once; every copy but the "
        "last is dead, along with any comment explaining it:\n  "
        + "\n  ".join(bad))


def test_every_excuse_carries_a_machine_readable_cause():
    """A reason is a claim; a cause code is a claim a test can read.

    `EXPECTED_INERT` was eighteen paragraphs, and a paragraph cannot be checked,
    cannot be counted, and cannot be told apart from the next one. Six of the
    eighteen shared a single paragraph — which is how `poll_min_n` came to be
    excused by a reason that was not true of it (§1.75), and how two entries
    came to be written from unstable readings and retracted (`pools.py`).

    So the shape is enforced here: four causes and no others, a named gate for
    anything that claims not to have arrived, a blocker saying whether that gate
    is shut by data or by us, a registered check that PROVES it shut, and
    evidence saying what was observed. None of that makes an entry true. It
    makes an entry falsifiable, which the prose was not.
    """
    bad: list[str] = []
    for (key, year), null in sorted(EXPECTED_INERT.items()):
        at = f"{key}@{year}"
        if not isinstance(null, Null):
            bad.append(f"{at}: {type(null).__name__}, not a Null — a bare string "
                       f"is the shape this test exists to retire")
            continue
        if null.cause not in CAUSES:
            bad.append(f"{at}: cause {null.cause!r} is not one of {CAUSES}")
        if null.cause == "INERT":
            if null.where or null.blocker or null.gate_check:
                bad.append(f"{at}: INERT means it arrived, propagated and did "
                           f"not matter — there is no gate, no stage and no "
                           f"blocker to name")
            if not null.evidence.startswith("DELIVERED:"):
                bad.append(
                    f"{at}: INERT is the ONLY cause that is a result, and it is "
                    f"a claim that the value REACHED the computation. Its "
                    f"evidence must open with `DELIVERED:` and say how that was "
                    f"established. (No entry has ever claimed it, so this rule "
                    f"has never fired in anger — it is here to make the first "
                    f"one produce the proof rather than the paragraph.)")
        else:
            if not null.where.strip():
                bad.append(f"{at}: {null.cause} must name where — the gate, the "
                           f"absorbing stage or the offsetting parameter. A "
                           f"cause nobody can point at is the prose again")
        if null.cause == "UNDELIVERED":
            if null.blocker not in BLOCKERS:
                bad.append(f"{at}: blocker {null.blocker!r} is not one of "
                           f"{BLOCKERS}")
        elif null.blocker:
            bad.append(f"{at}: blocker is for UNDELIVERED only; {null.cause} "
                       f"carries {null.blocker!r}")
        if null.gate_check and null.gate_check not in GATES:
            bad.append(f"{at}: gate_check {null.gate_check!r} is not in GATES")
        if not null.reason.strip():
            bad.append(f"{at}: no reason. The cause code says WHAT; the reason "
                       f"still has to say why anyone believes it")
        if not null.evidence.strip():
            bad.append(f"{at}: no evidence. NULL-RESULTS.md §4.2 — an entry that "
                       f"cannot produce a delivery proof is reopened")
    assert not bad, (
        "EXPECTED_INERT entries that are not machine-checkable:\n  "
        + "\n  ".join(bad))


def test_the_gate_named_by_every_excuse_is_actually_shut():
    """The claim is that the value never arrived. This goes and looks.

    Every UNDELIVERED entry names a gate. If the gate is OPEN, the value did
    arrive and the null has some other cause — most likely a real one — and the
    entry is not merely stale, it is hiding a measurement that did happen.

    This is the check `poll_k` never had. Its entry said "poll_k 1.0 vs 40.0 at
    2026 moves every party by exactly 0.0000pp", which was true, measured, and
    meaningless: `poll_id` was None, so the branch never ran. A gate check would
    have said so in a millisecond.
    """
    open_gates, unchecked = [], []
    for (key, year), null in sorted(EXPECTED_INERT.items()):
        if null.cause != "UNDELIVERED":
            continue
        if not null.gate_check:
            unchecked.append(f"{key}@{year}: {null.code}")
            continue
        shut, detail = GATES[null.gate_check](year)
        if not shut:
            open_gates.append(f"{key}@{year} names gate {null.gate_check!r} and "
                              f"IT IS OPEN: {detail}")
    assert not open_gates, (
        "an UNDELIVERED excuse names a gate that is not shut:\n  "
        + "\n  ".join(open_gates)
        + "\n\nThe value reached the computation. Either the null has a "
          "different cause — ABSORBED, CANCELLED or, if it really arrived and "
          "really did not matter, INERT — or the sweep is now measuring "
          "something it was not measuring before. Re-measure; do not re-word.")
    assert not unchecked, (
        "an UNDELIVERED excuse with no gate check:\n  " + "\n  ".join(unchecked)
        + "\n\nNULL-RESULTS.md §4.2: an entry that cannot produce a delivery "
          "proof is reopened.")

    # And the registry does not rot in the other direction either.
    named = ({n.gate_check for n in EXPECTED_INERT.values() if n.gate_check}
             | {c.opens for c in CONDITIONAL.values()})
    stale = sorted(set(GATES) - named)
    assert not stale, (
        f"GATES defines {stale}, which nothing names. A check for a gate nobody "
        f"claims is a check that will be believed for a claim it never made — "
        f"delete it, or point an entry at it.")


def test_no_undelivered_null_is_excused_without_opening_its_gate():
    """An UNDELIVERED entry is a DEFECT REPORT. Only INERT is an excuse.

    NULL-RESULTS.md §1: only D — arrived, propagated, does not matter — is a
    result. A is a defect, B is a structural fact, C is a statement about
    identifiability. `EXPECTED_INERT` accepted all four as though they were D,
    and today it contains no D at all.

    What this admits, and why it is not a loophole:

      * UNDELIVERED [DATA] — the evidence does not exist at this target and no
        change here creates it. The entry is accepted as a VOID: it records that
        NOTHING WAS MEASURED. It must still prove its gate is shut, which
        `test_the_gate_named_by_every_excuse_is_actually_shut` does.
      * UNDELIVERED [SWITCH] — we shut the gate, so we can open it, so we must.
        Accepted only with a `CONDITIONAL` entry that opens exactly that gate
        and measures the lever behind it on every run. Without one this is the
        `poll_k` fault verbatim, and it is reported as a defect.
      * UNDELIVERED [CODE] — nothing opens it. Never an excuse.
      * ABSORBED / CANCELLED — admitted, because both are real properties of
        this model (`solve_and_predict` absorbs geography almost perfectly;
        pool size and fitted rate are jointly identified). Both must name the
        stage or the parameter, which `test_every_excuse_carries_a_machine_
        readable_cause` enforces.
    """
    defects: list[str] = []
    for (key, year), null in sorted(EXPECTED_INERT.items()):
        if null.cause != "UNDELIVERED":
            continue
        if null.blocker == "CODE":
            defects.append(
                f"{key}@{year} is UNDELIVERED [CODE]: {null.where}. A lever the "
                f"code cannot deliver is a defect, not an inert lever — wire it "
                f"up or delete it")
            continue
        if null.blocker != "SWITCH":
            continue
        c = CONDITIONAL.get(f"{key}@{year}")
        if c is None:
            defects.append(
                f"{key}@{year} is UNDELIVERED [SWITCH]: {null.where}. WE shut "
                f"that gate, so the harness can open it, and until it does "
                f"nothing whatever is known about this lever")
        elif c.opens != null.gate_check:
            defects.append(
                f"{key}@{year} is excused by gate {null.gate_check!r} but its "
                f"CONDITIONAL opens {c.opens!r} — the measurement is behind a "
                f"different door from the excuse")
    assert not defects, (
        "these are defect reports being carried as excuses:\n  "
        + "\n  ".join(defects)
        + "\n\nA null measured with the gate shut is VOID, not NULL. See "
          "_LEGACY_POLL: the same mistake was committed inside the commit that "
          "automated the rule against it.")

    # The census, in one line, because eighteen entries called EXPECTED_INERT
    # of which none is inert is the sort of fact that should be impossible to
    # walk past.
    print("  EXPECTED_INERT census: " + ", ".join(
        f"{c}={sum(1 for n in EXPECTED_INERT.values() if n.cause == c)}"
        for c in CAUSES) + " (blockers: " + ", ".join(
        f"{b}={sum(1 for n in EXPECTED_INERT.values() if n.blocker == b)}"
        for b in BLOCKERS) + ")")


def test_a_lever_whose_gate_the_harness_can_open_is_measured_with_it_open():
    """The excuse said the lever was inert. Opened, all three move.

    `bye_local_cap` 2.0, `bye_tau_months` 14.0 and `poll_house_k` 226.0 at 2026
    on 2026-08-27 — every one of them sitting in `EXPECTED_INERT` at the time,
    and `poll_house_k`'s entry arguing for its own retention on the grounds that
    the configuration measured here is still reachable. It is. Nobody had
    reached it.

    Nothing asserted here is a magnitude: a magnitude is a fact about a
    configuration this project does not ship, and it is recorded in the entries
    as evidence of DELIVERY, not as a target. What is asserted is that the lever
    moves at all once its gate is open — because the day it stops, the excuse
    that rests on it has to be re-argued from scratch.
    """
    if not DATA.exists():
        skip("data/raw/elections is not present")
    dead = _sweep_conditional()
    assert not dead, (
        "a lever did not move even with its gate held open:\n  "
        + "\n  ".join(dead)
        + "\nThat is a much stronger statement than the EXPECTED_INERT entry "
          "makes, and it means the entry is now wrong in the other direction: "
          "either this really is INERT — in which case say so, with the "
          "delivery proof — or the gate is not the one that matters.")

    stale = sorted(set(CONDITIONAL)
                   - {f"{k}@{y}" for k, y in EXPECTED_INERT})
    assert not stale, (
        f"CONDITIONAL measures {stale}, which nothing excuses any more. A "
        f"conditional sweep whose entry has gone is coverage nobody asked for, "
        f"and it costs a model run per lever per target — delete it, or say in "
        f"EXPECTED_INERT why the lever still needs it.")


def test_module_constants_are_swept_for_liveness_too():
    """`--set` reaches DEFAULTS keys. The judgement calls are not all there.

    NULL-RESULTS.md §3: of the 48 constants pre-registered for the B2 sweep, 42
    carry a blocker, and the largest class is simply that a module constant is
    not a `DEFAULTS` key, so no liveness sweep has ever touched one. §3 gap 2 is
    sharper still — the serial-forcing guard in `compare_history` names
    `LEVEL_DF` as the defect it was built for and then checks five `levels`
    names, none of which is `montecarlo.LEVEL_DF`.

    In one process a module constant is perturbable, and the ones that matter
    resolve at call time. This sweeps five of them. It does not sweep all of
    them: the inventory has to be GENERATED from the register rather than listed
    here, and that needs a file this test does not own — stated so the five are
    not mistaken for the forty-two.
    """
    if not DATA.exists():
        skip("data/raw/elections is not present")
    dead = _sweep_module_constants()
    assert not dead, (
        "these module constants did not move the forecast when set to a value "
        "that must change it:\n  " + "\n  ".join(dead)
        + "\nA module constant that cannot move is `LEVEL_DF` again — bound "
          "once at import, argued over for weeks, and worth nothing at any "
          "value. Give it a cause code and a gate check, wire it up, or delete "
          "it.")


def _default_argument_scan(paths):
    """The scan behind CLASS 12, as a function so a fixture can be pushed through it.

    Returns ``(offenders, numeric, bound_as_default)`` — the offenders, the
    numeric module constants examined, and the (module, name) pairs bound as a
    default argument. The last two are the SCANNED population; the first is the
    verdict. Keeping them apart is the point: a guard that bounds the verdict
    would be demanding violations, and a guard that bounds nothing passes on an
    empty tree.
    """
    offenders: list[str] = []
    numeric_seen: list[str] = []
    bound: list[str] = []
    for path in sorted(paths):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        numeric = {t.id for node in tree.body
                   if isinstance(node, ast.Assign) and len(node.targets) == 1
                   for t in node.targets
                   if isinstance(t, ast.Name) and t.id.isupper()
                   and isinstance(node.value, ast.Constant)
                   and isinstance(node.value.value, (int, float))
                   and not isinstance(node.value.value, bool)}
        numeric_seen += [f"{path.name}:{n}" for n in sorted(numeric)]
        if not numeric:
            continue
        as_default: dict[str, list[str]] = {}
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for d in (list(node.args.defaults)
                      + [x for x in node.args.kw_defaults if x is not None]):
                for n in ast.walk(d):
                    if isinstance(n, ast.Name):
                        as_default.setdefault(n.id, []).append(
                            f"{node.name}():{node.lineno}")
        bound += [f"{path.name}:{n}" for n in sorted(as_default)]
        for name in sorted(numeric & set(as_default)):
            loads = sum(1 for n in ast.walk(tree)
                        if isinstance(n, ast.Name) and n.id == name
                        and isinstance(n.ctx, ast.Load))
            if loads <= len(as_default[name]):
                offenders.append(
                    f"{path.name} {name} is read ONLY as a default argument "
                    f"({', '.join(as_default[name])})")
    return offenders, numeric_seen, bound


def test_the_default_argument_scan_can_still_see_the_LEVEL_DF_shape():
    """(1) AND (2) for the scan below, which has a population of ZERO offenders.

    **Measured 2026-08-31: `numeric & as_default` is empty in all 50 files of
    `src/`, so `test_no_numeric_module_constant_is_reachable_only_as_a_default_argument`
    cannot fail for any reason.** That is the healthy state for a guard on a
    defect — but it means the only evidence the guard still works is the scan's
    own inputs and a constructed violation, and its `assert seen_defaults`
    supplied neither: `seen_defaults` counted 22 by tallying every `ast.Name`
    inside every default expression, which on that date was `Path` (×2),
    `frozenset`, `blk` (a local), `levels` (a module, ×5) and six real
    constants. **The guard read 22 on a tested population of 0** — a set
    disjoint from the one under test — and its message named
    `official_seats.REPORTS`, which the scan does not reach at all because that
    module has no numeric constant.

    So: bound the two SCANNED sets against the file count, and re-run the
    detector on the exact shape the original `LEVEL_DF` defect had.
    """
    src = sorted((ROOT / "src").glob("*.py"))
    offenders, numeric, bound = _default_argument_scan(src)
    scanned(numeric, of=src, low=0.6, high=6.0,
            what="numeric UPPERCASE module constants in src/",
            denominator=".py files in src/")
    scanned(bound, of=src, low=0.1, high=3.0,
            what="module-level names bound as a default argument",
            denominator=".py files in src/")

    with tempfile.TemporaryDirectory() as tmp:
        # Exactly `def log_shock(..., df: float = LEVEL_DF)`: the constant is
        # loaded nowhere else in its own module, so setting it after import
        # changes nothing.
        fake = Path(tmp) / "fake_levels.py"
        fake.write_text(
            "LEVEL_DF = 4.0\nSD_FLOOR = 0.01\n\n"
            "def log_shock(rng, df: float = LEVEL_DF):\n"
            "    return rng\n\n"
            "def widen(sd):\n"
            "    return max(sd, SD_FLOOR)\n")
        caught, _, _ = _default_argument_scan([fake])
    assert len(caught) == 1 and "LEVEL_DF" in caught[0], (
        f"the detector was handed the original defect verbatim — a numeric "
        f"constant read only as a default argument, beside one that is read in "
        f"a body — and reported {caught}. It must report LEVEL_DF and only "
        f"LEVEL_DF. Its live population is 0, so this is the ONLY evidence it "
        f"can still see anything.")


def test_no_numeric_module_constant_is_reachable_only_as_a_default_argument():
    """CLASS 12's founding shape, made structural.

    `def log_shock(..., df: float = LEVEL_DF)` is evaluated once at import, so
    setting `montecarlo.LEVEL_DF` afterwards changes nothing — and every sweep
    of it, at 2.5, 4, 7, 30, 200 and 1000, returned byte-identical output while
    the constant sat at 🔴 in the register as the most-attacked number in the
    project. It was found by accident. This finds it by construction: a numeric
    module constant whose ONLY use in its own module is as a default argument
    cannot be perturbed by anything, `MODULE_PERTURB` included.

    Non-numeric constants are exempt on purpose. `levels.METRO_CODES`,
    `pools.CONFIG` and `official_seats.REPORTS` are all in this shape and none
    of them is a judgement call — they are maps and paths, and a caller passes
    them explicitly. The class this catches is a NUMBER someone chose.

    The scan lives in :func:`_default_argument_scan`, and the evidence that it
    still SEES — a constructed `LEVEL_DF` bound as a default, plus two-sided
    bounds on both scanned sets — is in
    `test_the_default_argument_scan_can_still_see_the_LEVEL_DF_shape`. It has
    to be, because the offender population here has been 0 since the original
    defect was fixed and an empty verdict is indistinguishable from a dead scan
    without one.
    """
    offenders, _numeric, _bound = _default_argument_scan(
        (ROOT / "src").glob("*.py"))
    assert not offenders, (
        "a numeric module constant is bound once at import and nowhere else:\n  "
        + "\n  ".join(offenders)
        + "\nSetting it afterwards changes nothing, so no sweep can reach it "
          "and every null measured on it is UNDELIVERED. Resolve it at call "
          "time — `df = LEVEL_DF if df is None else float(df)` is the fix that "
          "was applied to the original.")


if __name__ == "__main__":
    # `run_module`, NOT a hand-rolled loop. Until 2026-08-23 this file ended with
    # `for name, fn in sorted(globals().items()): ... fn()`, which catches
    # neither `SkipTest` nor `SystemExit` — so the FIRST skip aborted the run and
    # every later test in the file silently never executed, and no summary was
    # printed. Five files were in that state; `test_regressions` alone has five
    # `skip(` calls. Under `run_all.py` they were fine, because the suite calls
    # `run_module(vars(module))` itself — the suite hid it. MODEL-LOG §1.84.
    # Append new tests ABOVE this line.
    raise SystemExit(run_module(globals()))
