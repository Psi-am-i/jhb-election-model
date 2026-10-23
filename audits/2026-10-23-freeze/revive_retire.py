"""Revive the retired tokens the frozen forecast prints again; retire two it does not.

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

CITY = "joburg"

TILE = ("In the frozen forecast MK triggers the excessive-seats clause in fewer "
        "simulations than the tile names a party at (scenarios.EXCESSIVE_FLOOR), "
        "so the tile does not name it.")
BYE = ("In the frozen forecast's draws the ANC's middle seat count at full "
       "by-election weight differs from the published half weight by no more than "
       "sampling noise (reweight.beyond_noise), so the line under the by-election "
       "control does not list it.")
RETIRE = {"tile.p_excessive.mk": TILE, "play.bye.w_bye_1.ANC": BYE}

COAL_BACK = ("In the frozen forecast this coalition is again a smallest majority "
             "in at least the share of simulations the who-can-govern table "
             "lists a coalition at (render_sheet MIN_SMALLEST), so the table "
             "prints it as current.")
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
    revive = found["live_retired"]
    wrong = [t for t in revive if not (latest.get(t) and latest[t].superseded_at)]
    if wrong:
        raise SystemExit(f"the probe flagged tokens whose latest row is not a retirement: {wrong}")
    clash = sorted(set(revive) & set(RETIRE))
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
    others = [t for t in found["vanished"] if t not in RETIRE]

    print(f"ledger: {root}/{CITY}/ledger.jsonl")
    print(f"revive ({len(revive)}): printed live by this build, latest row a retirement")
    for t in revive:
        print(f"  + {t}  (retired {latest[t].superseded_at}, was {latest[t].display})")
    print(f"retire ({len(retire)}):")
    for t in retire:
        print(f"  - {t}  (last published {latest[t].published_at}, {latest[t].display})")
    if others:
        print(f"also left the registry unretired, NOT handled here ({len(others)}):")
        for t in others:
            print(f"  ? {t}")

    if not args.apply:
        print("dry run: nothing written. Pass --apply to write these rows.")
        return 0

    when = P._utc()
    for t in revive:
        P.revive(CITY, t, reason=revival_reason(t), change_class="mechanism",
                 when=when, root=root)
    for t in retire:
        P.retire(CITY, t, reason=RETIRE[t], change_class="mechanism",
                 when=when, root=root)
    print(f"wrote {len(revive)} revival(s) and {len(retire)} retirement(s) at {when}")
    after = probe(root)
    print(f"after: {len(after['live_retired'])} retired token(s) printed live, "
          f"{len(after['vanished'])} left the registry unretired")
    if after["live_retired"] or set(after["vanished"]) & set(RETIRE):
        raise SystemExit("the rows did not clear the refusals they were written for:\n"
                         + after["stdout_tail"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
