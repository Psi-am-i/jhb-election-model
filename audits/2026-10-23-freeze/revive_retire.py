"""Revive the retired tokens the frozen forecast prints again; retire those the release no longer prints.

The frozen forecast (MODEL-LOG §1.335-1.336) puts back in the live pages
figures that `audits/2026-10-21-actionsa-call/retire.py` retired, and
`build_site.py --publish` refuses them ("SUPERSEDED FIGURES IN LIVE PRESENT
TENSE"). The list is computed, not typed: a probe build (into a scratch
directory, no `--publish`) against the target ledger reports every token it
prints in live present tense whose latest ledger row is a retirement, which is
`publication.dated_context_violations` by construction. Each is revived
(`publication.revive`). The same probe's "left the registry unretired" refusal
must name `tile.p_excessive.mk` and `play.bye.w_bye_1.ANC`, which are then
retired; any other token it names is printed and left for a human.

    .venv/bin/python audits/2026-10-23-freeze/revive_retire.py                       # dry run, real ledger
    .venv/bin/python audits/2026-10-23-freeze/revive_retire.py --ledger-root DIR     # dry run, a copy
    .venv/bin/python audits/2026-10-23-freeze/revive_retire.py --ledger-root DIR --apply

Extended 2026-10-24 for the release that also withdraws the in-sample
backtest scores (`audits/2026-10-23-site-sweep/BRIEF-step0-withdraw-scores.md`,
re-applied on `site-sweep-1`; MODEL-LOG §1.337) and carries the tone sweep
(`audits/2026-10-23-site-sweep/BRIEF-2-tone.md`). The same probe's "left the
registry unretired" list is classified, not typed:

* **step 0's retirements** are the listed tokens whose latest ledger row has a
  backtest source (:data:`SCORE_PREFIXES`, the prefixes
  `tests/test_quarantine.py` guards), plus :data:`STEP0_NAMED`, the three
  step 0 retired by name whose source is not a backtest prefix;
* :data:`SWEEP_RETIRE` names two more the owner listed (2026-10-24), each of
  which the probe must also report as left unretired.

Extended again 2026-10-24 for owner item 35
(`audits/2026-10-23-site-sweep/BRIEF-3-item35.md`, items 7-8):

* :data:`ITEM35_RETIRE` names the who-can-govern lede's two DA figures, which
  the lede no longer prints; each must be reported by the probe;
* a ``coal.*`` token the probe lists is retired with :data:`COAL_CUT` only
  when its combination governs in fewer than render_sheet ``MIN_GOVERNS`` of
  the frozen forecast's simulations (`coalition_shares`, by
  `render_sheet.coalition_cuts`); the set is the probe's, not typed here.
  A revived ``coal.*`` token gets :data:`COAL_BACK` only for a combination of
  two or more parties that passes both cuts. Any other is NOT handled.

A token NOT handled stops ``--apply``.

Anything else the probe lists is printed and left for a human.

Dry run by default; `--apply` writes, then probes again and fails unless both
refusals are empty. Run it immediately before the `build_site.py --publish`
that prints the revived tokens: `build_site` refuses a build that leaves a
revival unprinted (`publication.unpublished_revivals`).

The probe skips `build_site.maps_are_current`: it lists the tokens a build
prints, which the ward maps do not change, and it publishes nothing. The real
publish build keeps that check.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

import publication as P  # noqa: E402
import cityconfig  # noqa: E402
import render_sheet as RS  # noqa: E402

CITY = "joburg"

TILE = ("In the frozen forecast MK triggers the excessive-seats clause in fewer "
        "simulations than the tile names a party at (scenarios.EXCESSIVE_FLOOR), "
        "so the tile does not name it.")
BYE = ("In the frozen forecast's draws the ANC's middle seat count at full "
       "by-election weight differs from the published half weight by no more than "
       "sampling noise (reweight.beyond_noise), so the line under the by-election "
       "control does not list it.")
RETIRE = {"tile.p_excessive.mk": TILE, "play.bye.w_bye_1.ANC": BYE}

#: Sources that state a backtest result (tests/test_quarantine.SCORE_PREFIXES).
SCORE_PREFIXES = ("validation:", "history:", "compare_history:")
#: Step 0 retired these by name (dfdb334): the fold-2 blind test's pair and
#: the panel's target size, whose sources are not backtest prefixes.
STEP0_NAMED = ("blind_test_called", "blind_test_of", "backtest_target")
#: Step 0's own reason and class, as dfdb334 wrote them.
STEP0_REASON = ("Withdrawn: an in-sample backtest score, scored with settings "
                "chosen on the election scored or a later one (owner, 2026-10-23, "
                "OWNER-DECISIONS-ANSWERED.md item 29; "
                "audits/2026-10-23-site-sweep/BRIEF-step0-withdraw-scores.md).")
STEP0_CLASS = "bugfix"
SWEEP_RETIRE = {
    "ballots.typical.draw": (
        "The forecast page no longer names which simulation its typical ballot "
        "is (tone sweep, audits/2026-10-23-site-sweep/BRIEF-2-tone.md, work A)."),
    "judgement_asa_support": (
        "The ActionSA support judgement was withdrawn on 23 October 2026 "
        "(MODEL-LOG §1.335); the methodology states it as history under its "
        "own token."),
}


#: Owner item 35 (2026-10-24): the lede's two DA figures, no longer printed.
ITEM35_REASON = ("The who-can-govern lede no longer states the DA's routes without "
                 "the ANC, the EFF and MK; it gives the ANC's and the DA's workable "
                 "majorities without each other (owner, 2026-10-24, "
                 "OWNER-DECISIONS-ANSWERED.md item 35).")
ITEM35_RETIRE = {"govern.da_best_without": ITEM35_REASON,
                 "govern.da_with_small_without": ITEM35_REASON}
#: Owner item 35: a combination under the 10% cut is no longer printed.
COAL_CUT = ("This coalition governs in fewer than the share of simulations the "
            "who-can-govern table lists a combination at (render_sheet "
            "MIN_GOVERNS; owner, 2026-10-24, OWNER-DECISIONS-ANSWERED.md item 35), "
            "so the table no longer prints it.")


def coal_members(token: str) -> list[str]:
    """``coal.DA+ASA+PA.majority`` -> ``["DA", "ASA", "PA"]``."""
    return token.split(".")[1].split("+")


def load_seats(processed: Path | None = None):
    """``(seats per party, majority line)`` per simulation, from the frozen
    forecast's seat_draws.csv, read as render_sheet reads it."""
    import csv
    import numpy as np
    if processed is None:
        cityconfig.use(CITY)
        processed = Path(cityconfig.use_target(None).processed)
        processed = processed if processed.is_absolute() else REPO / processed
    with (processed / "seat_draws.csv").open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    parties = [k for k in rows[0] if k not in ("draw", "threshold", "council_size")]
    seats = {p: np.array([int(r[p]) for r in rows]) for p in parties}
    return seats, np.array([int(r["threshold"]) for r in rows])


def coalition_shares(token: str, seats, thr) -> dict | None:
    """`render_sheet.coalition_cuts` for a ``coal.*`` token's combination;
    None when a member has no seat column."""
    members = coal_members(token)
    if any(p not in seats for p in members):
        return None
    tot = sum(seats[p] for p in members)
    return RS.coalition_cuts(tot, [seats[p] for p in members], thr)


def under_the_cut(token: str, seats, thr) -> bool:
    got = coalition_shares(token, seats, thr)
    return got is not None and got["governs"] < RS.MIN_GOVERNS


def back_in_the_table(token: str, seats, thr) -> bool:
    got = coalition_shares(token, seats, thr)
    return (len(coal_members(token)) >= 2 and got is not None
            and got["smallest"] >= RS.MIN_SMALLEST and got["governs"] >= RS.MIN_GOVERNS)


def classify_vanished(vanished: list[str], latest: dict, seats=None, thr=None
                      ) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
    """``vanished`` split into (step 0's, :data:`SWEEP_RETIRE`'s,
    :data:`ITEM35_RETIRE`'s, the ``coal.*`` tokens under the 10% cut, the
    rest), leaving out the tokens :data:`RETIRE` handles. ``seats``/``thr``
    are `load_seats`'s; without them no ``coal.*`` token is under the cut."""
    step0, sweep, item35, cut, rest = [], [], [], [], []
    for t in vanished:
        if t in RETIRE:
            continue
        row = latest.get(t)
        if t in SWEEP_RETIRE:
            sweep.append(t)
        elif t in ITEM35_RETIRE:
            item35.append(t)
        elif t.startswith("coal.") and seats is not None and under_the_cut(t, seats, thr):
            cut.append(t)
        elif t in STEP0_NAMED or (row is not None and str(row.source).startswith(SCORE_PREFIXES)):
            step0.append(t)
        else:
            rest.append(t)
    return sorted(step0), sorted(sweep), sorted(item35), sorted(cut), sorted(rest)

COAL_BACK = ("In the frozen forecast this coalition is again a smallest majority "
             "in at least the share of simulations the who-can-govern table "
             "lists a coalition at (render_sheet MIN_SMALLEST), and governs in at "
             "least the share it lists a combination at (render_sheet "
             "MIN_GOVERNS), so the table prints it as current.")
BYE_BACK = ("In the frozen forecast's draws this party's middle seat count at "
            "this by-election weight differs from the published weight by more "
            "than sampling noise (reweight.beyond_noise), so the line under the "
            "by-election control lists it again.")
BACK = ("The frozen forecast prints this figure again as current, so the "
        "retirement no longer describes the published forecast.")


def revival_reason(token: str) -> str:
    if token.startswith("coal."):
        return COAL_BACK
    if token.startswith("play.bye."):
        return BYE_BACK
    return BACK


def _vanished(stdout: str) -> list[str]:
    """The tokens under build_site's "LEFT THE REGISTRY UNRETIRED" heading."""
    out, inside = [], False
    for line in stdout.splitlines():
        if "LEFT THE REGISTRY UNRETIRED" in line:
            inside = True
            continue
        if inside:
            s = line.strip()
            if s.startswith("✗ "):
                out.append(s[2:].split(" = ", 1)[0])
            elif s and not s.startswith(("Each was", "carries", "when it",
                                         "P.retire")):
                inside = False
    return out


def _probe_here(ledger_root: Path, out: Path) -> dict:
    """Run `build_site.main` once, in this process, against ``ledger_root``."""
    import build_site as B
    seen: list[dict] = []
    real = P.dated_context_violations

    def spy(rendered, ledger):
        got = real(rendered, ledger)
        seen.append({"violations": [v["token"] for v in got]})
        return got

    B.publication.dated_context_violations = spy
    B.maps_are_current = lambda processed, pages=None: []
    buf = io.StringIO()
    os.chdir(REPO)
    with contextlib.redirect_stdout(buf):
        try:
            B.main(["--out", str(out / "site"), "--ledger-root", str(ledger_root)])
        except SystemExit:
            pass
    text = buf.getvalue()
    if not seen:
        raise SystemExit("the probe build stopped before the dated-context check:\n"
                         + text[-2000:])
    return {"live_retired": sorted(set(seen[0]["violations"])),
            "vanished": _vanished(text),
            "stdout_tail": text[-1500:]}


def probe(ledger_root: Path) -> dict:
    """`_probe_here` in a fresh interpreter, so each probe is one clean build."""
    with tempfile.TemporaryDirectory() as tmp:
        dump = Path(tmp) / "probe.json"
        subprocess.run([sys.executable, __file__, "--ledger-root", str(ledger_root),
                        "--_probe", str(dump), "--_out", tmp], check=True, cwd=REPO)
        return json.loads(dump.read_text(encoding="utf-8"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ledger-root", type=Path, default=None,
                    help="ledger root (default: the real publications/)")
    ap.add_argument("--apply", action="store_true",
                    help="write the rows (default: report what would be written)")
    ap.add_argument("--_probe", type=Path, default=None, help=argparse.SUPPRESS)
    ap.add_argument("--_out", type=Path, default=None, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    root = (args.ledger_root or (REPO / P.LEDGER_ROOT)).resolve()

    if args._probe:
        args._probe.write_text(json.dumps(_probe_here(root, args._out)), encoding="utf-8")
        return 0

    latest = P.latest(CITY, root=root)
    found = probe(root)
    seats, thr = load_seats()
    revive_all = found["live_retired"]
    revive = [t for t in revive_all
              if not t.startswith("coal.") or back_in_the_table(t, seats, thr)]
    revive_unhandled = [t for t in revive_all if t not in revive]
    wrong = [t for t in revive_all if not (latest.get(t) and latest[t].superseded_at)]
    if wrong:
        raise SystemExit(f"the probe flagged tokens whose latest row is not a retirement: {wrong}")
    clash = sorted(set(revive_all) & set(RETIRE))
    if clash:
        raise SystemExit(f"tokens both printed live and due for retirement: {clash}")
    retire = []
    for token in RETIRE:
        row = latest.get(token)
        if row is None:
            raise SystemExit(f"{token}: not in the ledger at {root}")
        if row.superseded_at:
            print(f"  - {token}: already retired {row.superseded_at}")
            continue
        if token not in found["vanished"]:
            raise SystemExit(f"{token}: the probe build did not report it as left "
                             f"the registry unretired; it may still be printed")
        retire.append(token)
    step0, sweep, item35, cut, others = classify_vanished(found["vanished"], latest, seats, thr)
    for named, got in ((SWEEP_RETIRE, sweep), (ITEM35_RETIRE, item35)):
        for t in named:
            row = latest.get(t)
            if row is None:
                raise SystemExit(f"{t}: not in the ledger at {root}")
            if row.superseded_at:
                print(f"  - {t}: already retired {row.superseded_at}")
            elif t not in got:
                raise SystemExit(f"{t}: the probe build did not report it as left "
                                 f"the registry unretired; it may still be printed")
    missing0 = [t for t in STEP0_NAMED
                if latest.get(t) and not latest[t].superseded_at and t not in step0]
    if missing0:
        raise SystemExit(f"step 0 names {missing0}, which the probe did not report as "
                         f"left the registry unretired; they may still be printed")

    print(f"ledger: {root}/{CITY}/ledger.jsonl")
    print(f"revive ({len(revive)}): printed live by this build, latest row a retirement")
    for t in revive:
        print(f"  + {t}  (retired {latest[t].superseded_at}, was {latest[t].display})")
    print(f"retire ({len(retire)}):")
    for t in retire:
        print(f"  - {t}  (last published {latest[t].published_at}, {latest[t].display})")
    print(f"retire, step 0 ({len(step0)}): withdrawn in-sample scores")
    for t in step0:
        print(f"  - {t}  (source {latest[t].source}; last published "
              f"{latest[t].published_at}, {latest[t].display})")
    print(f"retire, owner's list ({len(sweep)}):")
    for t in sweep:
        print(f"  - {t}  (last published {latest[t].published_at}, {latest[t].display}): "
              f"{SWEEP_RETIRE[t]}")
    print(f"retire, owner item 35's lede ({len(item35)}):")
    for t in item35:
        print(f"  - {t}  (last published {latest[t].published_at}, {latest[t].display})")
    print(f"retire, under the 10% cut ({len(cut)}):")
    for t in cut:
        print(f"  - {t}  (last published {latest[t].published_at}, {latest[t].display})")
    if others:
        print(f"also left the registry unretired, NOT handled here ({len(others)}):")
        for t in others:
            print(f"  ? {t}")

    if revive_unhandled:
        print(f"printed live, latest row a retirement, NOT handled here ({len(revive_unhandled)}):")
        for t in revive_unhandled:
            print(f"  ? {t}")

    if not args.apply:
        print("dry run: nothing written. Pass --apply to write these rows.")
        return 0
    if others or revive_unhandled:
        raise SystemExit(f"--apply refused: {len(others) + len(revive_unhandled)} token(s) "
                         "NOT handled here (listed above); nothing written")

    when = P._utc()
    for t in revive:
        P.revive(CITY, t, reason=revival_reason(t), change_class="mechanism",
                 when=when, root=root)
    for t in retire:
        P.retire(CITY, t, reason=RETIRE[t], change_class="mechanism",
                 when=when, root=root)
    for t in step0:
        P.retire(CITY, t, reason=STEP0_REASON, change_class=STEP0_CLASS,
                 when=when, root=root)
    for t in sweep:
        P.retire(CITY, t, reason=SWEEP_RETIRE[t], change_class="mechanism",
                 when=when, root=root)
    for t in item35:
        P.retire(CITY, t, reason=ITEM35_RETIRE[t], change_class="mechanism",
                 when=when, root=root)
    for t in cut:
        P.retire(CITY, t, reason=COAL_CUT, change_class="mechanism",
                 when=when, root=root)
    n_retired = len(retire) + len(step0) + len(sweep) + len(item35) + len(cut)
    print(f"wrote {len(revive)} revival(s) and {n_retired} retirement(s) at {when}")
    after = probe(root)
    print(f"after: {len(after['live_retired'])} retired token(s) printed live, "
          f"{len(after['vanished'])} left the registry unretired")
    handled = set(RETIRE) | set(step0) | set(sweep) | set(item35) | set(cut)
    if after["live_retired"] or set(after["vanished"]) & handled:
        raise SystemExit("the rows did not clear the refusals they were written for:\n"
                         + after["stdout_tail"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
