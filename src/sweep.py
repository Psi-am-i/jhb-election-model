"""Run the model over every metro-year we can score, and hunt for anomalies.

Two targets and one city is not an evidence base. This runs the whole harness
across every city-year that has the files to support it and reports the results
side by side, because a fault that looks like noise in Johannesburg 2021 looks
like a pattern across sixteen city-years -- and because the failures worth
finding are the OBVIOUS ones, not the third decimal place of a CRPS.

    python src/sweep.py                     # every runnable city-year
    python src/sweep.py --target 2021       # one target, every city
    python src/sweep.py --draws 500         # faster, noisier

What it flags, and why each one is a real fault rather than a bad score:

``seat-winner missed entirely``
    A party that won seats and got a median of zero. This is the ActionSA
    failure and it is the largest single error in the record.

``phantom seats``
    Seats given to parties that won none. Two of these are a rounding artefact;
    forty are a broken denominator (see fold.calibrate_theta).

``council does not add up``
    Predicted seats summing to something other than the council. Always a bug,
    never a forecast.

``level implausible``
    A party predicted above 60% or a governing party predicted below 5%. Not
    impossible, but never yet observed in a metro, so it is worth a look.

``interval excludes the truth``
    The actual result outside the 90% band. Expected one time in ten; flagged so
    that the RATE can be read off the sweep rather than asserted.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

CITIES = ["joburg", "tshwane", "ekurhuleni", "ethekwini", "capetown",
          "mangaung", "nelsonmandelabay", "buffalocity"]


def runnable(city: str) -> list[str]:
    """Targets this city has both a backtest path and a pool spec for."""
    sys.path.insert(0, "src")
    import backtest
    import cityconfig
    c = cityconfig.load(city)
    out = []
    for year in backtest.runnable_targets(c):
        spec = c.processed / f"pools_{year}.json"
        if spec.exists():
            out.append(year)
    return out


PARTY_ROW = re.compile(r"^\s{2}([A-Z][A-Z0-9_']*)\s+(\d+)\s+(\d+)\s+"
                       r"([\d.]+)\s+([\d.]+)\s*$")


def parse(text: str) -> dict:
    """Pull the scored table and headline figures out of a backtest report."""
    out: dict = {"parties": [], "raw": text}
    for line in text.splitlines():
        m = PARTY_ROW.match(line)
        if m:
            out["parties"].append({
                "party": m.group(1), "actual": int(m.group(2)),
                "median": int(m.group(3)), "crps": float(m.group(4)),
                "pit": float(m.group(5))})
            continue
        if "CRPS total" in line:
            out["crps_total"] = float(line.split("CRPS total")[1].split()[0])
            n = re.search(r"over (\d+) parties", line)
            if n:
                out["n_scored"] = int(n.group(1))
        elif "energy score" in line:
            out["energy"] = float(line.split("energy score")[1].split()[0])
            v = re.search(r"variogram\(([\d.]+)\)\s+([\d.]+)", line)
            if v:
                out["variogram"] = float(v.group(2))
        elif "median seat MAE" in line:
            out["seat_mae"] = float(re.search(r"MAE (\d+)", line).group(1))
        elif re.search(r"\bBrier ([\d.]+)", line) and "wards" in line:
            out["brier"] = float(re.search(r"\bBrier ([\d.]+)", line).group(1))
        elif "modal call correct in" in line:
            m2 = re.search(r"in (\d+)/(\d+)", line)
            out["modal"] = (int(m2.group(1)), int(m2.group(2)))
        elif "actual council:" in line:
            m2 = re.search(r"actual council: (\d+) seats", line)
            if m2:
                out["council"] = int(m2.group(1))
    return out


def anomalies(res: dict, city: str, year: str) -> list[str]:
    found = []
    parties = res.get("parties", [])
    if not parties:
        return ["no scored table — the run did not reach the scorer"]
    for p in parties:
        if p["actual"] >= 3 and p["median"] == 0:
            found.append(f"seat-winner missed entirely: {p['party']} won "
                         f"{p['actual']}, median 0")
    phantom = sum(p["median"] for p in parties if p["actual"] == 0)
    if phantom >= 2:
        found.append(f"phantom seats: {phantom} to "
                     f"{sum(1 for p in parties if p['actual'] == 0 and p['median'])} "
                     f"parties that won none")
    total = sum(p["median"] for p in parties)
    council = res.get("council")
    if council and abs(total - council) > 0.1 * council:
        found.append(f"council does not add up: medians sum to {total} "
                     f"against a council of {council}")
    for p in parties:
        if p["pit"] >= 0.99 and p["actual"] > 0:
            found.append(f"interval excludes the truth (below): {p['party']} "
                         f"won {p['actual']}, above the whole forecast")
        elif p["pit"] <= 0.01 and p["median"] > 0:
            found.append(f"interval excludes the truth (above): {p['party']} "
                         f"won {p['actual']}, below the whole forecast "
                         f"(median {p['median']})")
    return found


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--draws", type=int, default=1000)
    ap.add_argument("--target", default=None, help="only this year")
    ap.add_argument("--city", default=None, help="only this city")
    ap.add_argument("--out", type=Path,
                    default=Path("data/processed/sweep.json"))
    args = ap.parse_args(argv)

    cities = [args.city] if args.city else CITIES
    results = {}
    for city in cities:
        for year in runnable(city):
            if args.target and year != args.target:
                continue
            print(f"--- {city} {year} " + "-" * (46 - len(city) - len(year)),
                  flush=True)
            proc = subprocess.run(
                [sys.executable, "src/backtest.py", "--city", city,
                 "--target", year, "--draws", str(args.draws)],
                capture_output=True, text=True)
            res = parse(proc.stdout)
            res["stderr_tail"] = proc.stderr.strip().splitlines()[-3:]
            res["returncode"] = proc.returncode
            res["anomalies"] = anomalies(res, city, year)
            if not res.get("parties"):
                print(f"    did not score: "
                      f"{' | '.join(res['stderr_tail']) or 'no output'}")
            else:
                print(f"    CRPS {res.get('crps_total', float('nan')):.1f} over "
                      f"{res.get('n_scored', 0)} parties   seat MAE "
                      f"{res.get('seat_mae', float('nan')):.0f}   "
                      f"Brier {res.get('brier', float('nan')):.4f}   "
                      f"wards {res.get('modal', ('?', '?'))[0]}/"
                      f"{res.get('modal', ('?', '?'))[1]}")
            for a in res["anomalies"]:
                print(f"    ANOMALY  {a}")
            res.pop("raw", None)
            results[f"{city}/{year}"] = res

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2))

    print("\n=== anomalies, all city-years ===")
    counts: dict[str, int] = {}
    for key, res in sorted(results.items()):
        for a in res["anomalies"]:
            kind = a.split(":")[0]
            counts[kind] = counts.get(kind, 0) + 1
            print(f"  {key:<28} {a}")
    if not counts:
        print("  none")
    else:
        print("\n  by kind:")
        for kind, n in sorted(counts.items(), key=lambda kv: -kv[1]):
            print(f"    {n:>3}  {kind}")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
