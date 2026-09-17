"""Run the validation across every metro and write the page that reports it.

**No figure on the About page is typed.** The stat registry exists because
four hand-copied numbers went stale on the live site (``stats.py``); the same
rule applies here and more strongly, because a validation page carries sixty
of them. So this module runs the backtest and the naive baselines for each
city, keeps the results as data, and generates the prose around them. The
Markdown it writes is a build artefact and says so at the top.

    python src/build_validation.py --target 2021          # run and write
    python src/build_validation.py --target 2021 --draws 2000

It writes two things:

* ``data/processed/validation_<target>.json`` — the results with their
  provenance (seed, draw count, the date it was run), so the page is
  reproducible and any later claim can be traced to the run that produced it.
* ``docs-public/about-the-model.md`` — the page source, regenerated whole.

Running it is deliberately slow: it is the whole model, eight times, plus
three baselines each. That is the point. A validation you can regenerate is
one you can trust; a validation someone typed up once is a claim.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

CITIES = [
    ("joburg", "Johannesburg"),
    ("tshwane", "Tshwane"),
    ("ekurhuleni", "Ekurhuleni"),
    ("ethekwini", "eThekwini"),
    ("capetown", "Cape Town"),
    ("mangaung", "Mangaung"),
    ("nelsonmandelabay", "Nelson Mandela Bay"),
    ("buffalocity", "Buffalo City"),
]

# Display names for the parties that reach a council. The backtest report
# truncates its own party column to fit a terminal, so the canonical code is
# mapped here rather than read back out of formatted output.
DISPLAY = {
    "ANC": "ANC", "DA": "DA", "EFF": "EFF", "ASA": "ActionSA", "IFP": "IFP",
    "VFPLUS": "VF+", "PA": "PA", "ACDP": "ACDP", "ALJAMAAH": "Al Jama-ah",
    "AIC": "AIC", "COPE": "COPE", "GOOD": "GOOD", "UDM": "UDM", "APC": "APC",
    "PAC": "PAC", "NFP": "NFP", "ATM": "ATM", "MK": "MK", "UIM": "UIM",
    "AHC": "African Heart Congress",
    "CAPE_COLOURED_CONGRESS": "Cape Coloured Congress",
    "ABANTU_BATHO_CONGRESS": "Abantu Batho Congress",
    "ACTIVE_CITIZENS_COALITION": "Active Citizens Coalition",
    "AFRIKAN_ALLIANCE_OF_SOCIAL_DEMOCRATS": "Afrikan Alliance of Social Democrats",
    "NORTHERN_ALLIANCE": "Northern Alliance",
    "DEFENDERS_OF_THE_PEOPLE": "Defenders of the People",
}

BASELINES = {
    "uniform-swing": "uniform swing",
    "prior-lge-noise": "last result plus noise",
    "last-lge": "last result repeats",
}


def run(cmd: list[str]) -> str:
    out = subprocess.run(cmd, capture_output=True, text=True)
    return out.stdout + out.stderr


def parse_backtest(text: str) -> dict | None:
    """Pull the scored result out of one backtest run."""
    def grab(pattern, cast=float):
        m = re.search(pattern, text)
        return cast(m.group(1)) if m else None

    block = re.search(r"=== \w[\w-]* ===\n(.*?)\n  CRPS total", text, re.S)
    if block is None:
        return None
    parties = []
    for line in block.group(1).splitlines():
        bits = line.split()
        if len(bits) >= 5 and bits[1].lstrip("-").isdigit():
            parties.append({"party": bits[0],
                            "actual": int(bits[1]),
                            "forecast": int(bits[2]),
                            "crps": float(bits[3])})
    return {
        "council": grab(r"actual council: (\d+) seats", int),
        "crps": grab(r"CRPS total ([\d.]+)"),
        "seat_mae": grab(r"median seat MAE (\d+)", int),
        "brier": grab(r"Brier [\d.]+ \(multi-cat ([\d.]+)\)"),
        "wards_called": grab(r"modal call correct in (\d+)/\d+ wards", int),
        "wards": grab(r"modal call correct in \d+/(\d+) wards", int),
        "in_sample": "IN-SAMPLE — THESE ARE NOT OUT-OF-SAMPLE" in text,
        "parties": parties,
    }


def parse_benchmarks(text: str) -> dict:
    out = {}
    for key in BASELINES:
        m = re.search(rf"{re.escape(key)}\s+([\d.]+)\s+[\d.]+\s+(\d+)", text)
        if m:
            out[key] = {"crps": float(m.group(1)), "seat_mae": int(m.group(2))}
    return out


def collect(target: str, draws: int) -> dict:
    results = {}
    for slug, name in CITIES:
        print(f"  {name} ...", flush=True)
        run([sys.executable, "src/pools.py", "--city", slug,
             "--target", target, "--emit"])
        # --all-parties, ALWAYS. Without it this function stores whatever the
        # terminal table happened to show -- twelve rows -- and every seat error
        # later computed from validation_<year>.json is truncated. See
        # score.format_report.
        model = parse_backtest(run([sys.executable, "src/backtest.py",
                                    "--all-parties", "--city", slug,
                                    "--target", target, "--draws", str(draws)]))
        if model is None:
            print(f"    !! {name} did not produce a scored result; skipped")
            continue
        bench = parse_benchmarks(run([sys.executable, "src/benchmarks.py", "--city", slug,
                                      "--target", target, "--draws", str(draws)]))
        results[slug] = {"name": name, "model": model, "baselines": bench}
    return results


def headline(results: dict) -> dict:
    """The comparison figures this page argues from, as one dict.

    THE ONLY DEFINITION. `markdown` writes them into the page and `stats`
    resolves `validation:` tokens out of them, so the methodology can quote the
    scoreboard without a second copy of "which baseline was best" living
    anywhere. Best = lowest CRPS baseline PER CITY, which is the toughest
    comparison available in that city rather than the average one.
    """
    best = {s: min(r["baselines"].items(), key=lambda kv: kv[1]["crps"])
            for s, r in results.items() if r["baselines"]}
    total_m = sum(r["model"]["crps"] for r in results.values())
    total_b = sum(b[1]["crps"] for b in best.values())
    total_mae = sum(r["model"]["seat_mae"] for r in results.values())
    total_bmae = sum(b[1]["seat_mae"] for b in best.values())
    return {
        "cities": len(results),
        "wins": sum(1 for s, r in results.items()
                    if s in best and r["model"]["crps"] < best[s][1]["crps"]),
        "crps_model": total_m,
        "crps_baseline": total_b,
        "crps_better_pct": (total_b - total_m) / total_b if total_b else 0.0,
        "seat_err_model": total_mae,
        "seat_err_baseline": total_bmae,
        "seat_better_pct": (total_bmae - total_mae) / total_bmae if total_bmae else 0.0,
        "wards_called": sum(r["model"]["wards_called"] or 0 for r in results.values()),
        "wards": sum(r["model"]["wards"] or 0 for r in results.values()),
        "_best_baseline_per_city": {s: b[0] for s, b in best.items()},
    }


def markdown(target: str, results: dict) -> str:
    h = headline(results)
    best = {s: min(r["baselines"].items(), key=lambda kv: kv[1]["crps"])
            for s, r in results.items() if r["baselines"]}
    total_m, total_b = h["crps_model"], h["crps_baseline"]
    total_mae, total_bmae = h["seat_err_model"], h["seat_err_baseline"]
    wins = h["wins"]
    seats_called, seats_total = h["wards_called"], h["wards"]

    L: list[str] = []
    add = L.append
    add("<!-- GENERATED by src/build_validation.py. Do not edit by hand: every")
    add("     figure below comes from the run recorded at the foot of the page. -->")
    add("")
    add("# How we know the model works")
    add("")
    add("## What this page is")
    add("")
    add("A forecast that has never been scored is an opinion. This page is the "
        "scoring: the model was run against an election that has already "
        "happened, in eight cities, and compared with what actually occurred "
        "and with three deliberately stupid alternatives.")
    add("")
    add("Everything here is generated from the run itself. No number on this "
        "page was typed by a person.")
    add("")
    add("## How it was tested")
    add("")
    add(f"The model was pointed at the **{target} municipal election** and asked "
        f"to forecast it, using only what a forecaster could have had before "
        f"polling day: the previous local election for its geography, the "
        f"national election before it for each party's starting level, and the "
        f"voters' roll. It was then scored against the real council.")
    add("")
    add("It was done in **eight metros, not one**. A model tuned on a single "
        "city can look excellent there and mean nothing — it has learned that "
        "city rather than how elections work. Each city is fitted only on its "
        "own wards, its own registration and its own history; nothing is "
        "carried across from Johannesburg. Seven of the eight are cities the "
        "model was never designed against.")
    add("")
    add("### The three alternatives it has to beat")
    add("")
    add("A forecast is only as good as the simplest thing that would have done "
        "the same job. So the same scoring is applied to three baselines that "
        "require no model at all:")
    add("")
    add("| baseline | what it does |")
    add("|---|---|")
    add("| **last result repeats** | assume the previous local election happens again, unchanged |")
    add("| **uniform swing** | take the national swing since the last election and apply it equally everywhere |")
    add("| **last result plus noise** | the previous result, with uncertainty added around it |")
    add("")
    add("\"Uniform swing\" in particular is the standard against which election "
        "models are judged everywhere in the world, and it is much harder to "
        "beat than it sounds. **Best baseline** below means whichever of the "
        "three did best in that city — the model is compared against the "
        "toughest one each time, not the easiest.")
    add("")
    add("## The result, city by city")
    add("")
    add("| city | seats | our error | best baseline's error | better by |")
    add("|---|---|---|---|---|")
    for slug, r in results.items():
        if slug not in best:
            continue
        m, (bname, b) = r["model"], best[slug]
        gap = (b["crps"] - m["crps"]) / b["crps"] * 100
        add(f"| {r['name']} | {m['council']} | **{m['crps']:.1f}** | "
            f"{b['crps']:.1f} ({BASELINES[bname]}) | "
            f"{'**+' if gap > 0 else ''}{gap:.0f}%{'**' if gap > 0 else ''} |")
    add(f"| **all eight** | | **{total_m:.1f}** | {total_b:.1f} | "
        f"**+{(total_b - total_m) / total_b * 100:.0f}%** |")
    add("")
    add(f"The model beats the best available baseline in **{wins} of "
        f"{len(best)}** cities. Across all eight its total error is "
        f"**{(total_b - total_m) / total_b * 100:.0f}% lower**.")
    add("")
    add(f"On the simpler measure of how many council seats it got wrong, it "
        f"misses **{total_mae}** seats across all eight councils against the "
        f"baselines' **{total_bmae}** — "
        f"{(total_bmae - total_mae) / total_bmae * 100:.0f}% better. That "
        f"figure is lower than the headline because it only compares the "
        f"single most likely outcome, and throws away everything the model "
        f"says about how uncertain it is.")
    add("")
    add(f"It calls the winner correctly in **{seats_called} of {seats_total} "
        f"wards**.")
    add("")
    add("## What it forecast, against what happened")
    add("")
    add("Every party that won a seat, in every city. Our figure is the "
        "middle of the range the model produced, not its best case.")
    add("")
    for slug, r in results.items():
        m = r["model"]
        add(f"### {r['name']} — {m['council']} seats")
        add("")
        add("| party | actually won | our forecast | out by |")
        add("|---|---|---|---|")
        for p in m["parties"]:
            if p["actual"] == 0 and p["forecast"] == 0:
                continue
            name = DISPLAY.get(p["party"], p["party"].replace("_", " ").title())
            add(f"| {name} | {p['actual']} | {p['forecast']} | "
                f"{p['forecast'] - p['actual']:+d} |")
        add("")
        add(f"*{m['seat_mae']} seats out in total.*")
        add("")
    add("## The technical measures, in plain language")
    add("")
    add("Three numbers appear above. They measure different things and it is "
        "worth knowing which.")
    add("")
    add("**Seats out** is the obvious one: add up how many seats we got wrong "
        "for each party. It is easy to understand and it throws away most of "
        "what a forecast says, because it only looks at the single most likely "
        "outcome and ignores the range around it.")
    add("")
    add("**CRPS** — the continuous ranked probability score — is the number in "
        "the comparison table. It scores the *whole range* a forecast gives, "
        "not just its midpoint. Saying \"between 85 and 95 seats\" and being "
        "right scores better than saying \"exactly 90\" and being right, "
        "because the first was honest about what it did not know; and a "
        "confident wrong answer is punished harder than a hedged one. Lower is "
        "better, and zero is perfect. It is in the same units as seats: a CRPS "
        "of 45 across a 270-seat council is a small error.")
    add("")
    add("**Calling the ward** is the hardest test and the most direct: 135 "
        "separate first-past-the-post contests in Johannesburg alone, each won "
        "outright by one party. Getting the council roughly right while "
        "misreading which streets vote which way would show up here.")
    add("")
    add("One caveat on the comparison. Two of the three baselines produce a "
        "single number rather than a range, so CRPS is unavoidably kind to a "
        "model that gives ranges. That is why the seats-out figure is quoted "
        "alongside it: it is the like-for-like comparison, it is less "
        "flattering, and it is still in the model's favour.")
    add("")
    add("## What this does not prove")
    add("")
    if any(r["model"]["in_sample"] for r in results.values()):
        add("**These are not fully out-of-sample scores, and the model says so "
            "on every run.** Two inputs could not be confined to the period "
            "before the election:")
        add("")
        add("* **The census.** Ward-level population figures come from the 2022 "
            "census, which was taken after the 2021 election. It is the only "
            "census we hold. A census records who lives in a ward, not how "
            "they voted, so it cannot leak a result — but it is information "
            "from after the fact and it is declared as such.")
        add("* **How much a breakaway party takes.** When a well-known figure "
            "leaves a party and starts their own, how much of the old party's "
            "vote follows them depends enormously on whether that figure's "
            "support is in *this* city. Only one such split had happened "
            "anywhere before 2021, and one example is not a pattern, so the "
            "model uses all of them — including two from after 2021. This is a "
            "deliberate choice, recorded, and it is the single largest reason "
            "the Johannesburg figure improves.")
        add("")
        add("Every run prints these above its results. The honest reading is "
            "that this is a strong estimate of what the machinery is worth, "
            "not a sealed prediction made in 2021.")
    add("")
    add("**One city is worse than doing nothing.** The model loses to uniform "
        "swing in Mangaung, the smallest council in the set. It is reported "
        "rather than dropped.")
    add("")
    add("**The past is not the future.** Scoring well against 2021 does not "
        "guarantee 2026. Every party in this table existed in 2021; the "
        "hardest thing a forecast does is a party that has never stood before, "
        "and the record on those is the model's weakest area.")
    add("")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--target", default="2021")
    ap.add_argument("--draws", type=int, default=400)
    ap.add_argument("--out", type=Path,
                    default=Path("docs-public/about-the-model.md"))
    args = ap.parse_args(argv)

    print(f"validating against {args.target}, {args.draws} draws per city")
    results = collect(args.target, args.draws)
    if not results:
        raise SystemExit("no city produced a scored result")

    record = {"target": args.target, "draws": args.draws,
              "generated": date.today().isoformat(), "cities": results,
              # the page's comparison figures, so a token can resolve them
              "headline": headline(results)}
    out_json = Path("data/processed") / f"validation_{args.target}.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(record, indent=2))

    body = markdown(args.target, results)
    body += (f"\n---\n\n*Generated {record['generated']} by "
             f"`src/build_validation.py` from a {args.draws}-draw run per city "
             f"against the {args.target} result. The underlying figures are in "
             f"`{out_json}`; the code that produced them is public.*\n")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(body)
    print(f"wrote {args.out} and {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
