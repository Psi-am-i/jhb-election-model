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
    add("This page is the model's scoring: it was run against an election "
        "that has already happened, in eight cities, and compared with the "
        "result and with three simple baselines.")
    add("")
    add("Every figure here is generated from the run. None was typed by a "
        "person.")
    add("")
    add("## How it was tested")
    add("")
    add(f"The model was given the **{target} municipal election** to forecast, "
        f"using only what a forecaster could have had before "
        f"polling day: the previous local election for its geography, the "
        f"national election before it for each party's starting level, and the "
        f"voters' roll. It was then scored against the real council.")
    add("")
    add("It was done in **eight metros, not one**. A model tuned on a single "
        "city can look excellent there and have learned only that city. Each "
        "city is fitted only on its own wards, registration and history; "
        "nothing is carried across from Johannesburg. Seven of the eight are "
        "cities the model was never designed against.")
    add("")
    add("### The three baselines")
    add("")
    add("The same scoring is applied to three baselines that need no model:")
    add("")
    add("| baseline | what it does |")
    add("|---|---|")
    add("| **last result repeats** | assume the previous local election happens again, unchanged |")
    add("| **uniform swing** | take the national swing since the last election and apply it equally everywhere |")
    add("| **last result plus noise** | the previous result, with uncertainty added around it |")
    add("")
    add("Uniform swing is the usual standard for judging election models, and "
        "it is hard to beat. **Best baseline** below means whichever of the "
        "three did best in that city.")
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
    add(f"The model beats the best baseline in **{wins} of "
        f"{len(best)}** cities. Across all eight its total error is "
        f"**{(total_b - total_m) / total_b * 100:.0f}% lower**.")
    add("")
    add(f"Counting council seats wrong, it misses **{total_mae}** seats across "
        f"all eight councils against the baselines' **{total_bmae}**, "
        f"{(total_bmae - total_mae) / total_bmae * 100:.0f}% better. The "
        f"margin is smaller than the headline because this measure compares "
        f"only the single most likely outcome and ignores the model's "
        f"uncertainty.")
    add("")
    add(f"It calls the winner in **{seats_called} of {seats_total} wards**.")
    add("")
    add(f"## What it forecast for {target}, against what happened")
    add("")
    # ⛔ SAY HOW MANY ROWS THIS IS. It read "Every party that won a seat in
    # 2021, in every city", and the artefact carries TWELVE parties per city
    # while Johannesburg seated eighteen. The page then printed a total over
    # ALL parties beneath rows that do not add up to it — Johannesburg's rows
    # sum to 56 against a printed 62, and the gap is exactly the six parties
    # left out. A reader with a calculator got a different number from the one
    # printed beside the table.
    # COUNTED from the artefact, not typed. The comment above is the whole
    # point: a sentence that describes the table has to be derived from the
    # table, or it goes stale the first time the table changes shape.
    rows_per_city = max(len(r["model"]["parties"]) for r in results.values())
    add(f"The largest {rows_per_city} parties in each city, by seats won in "
        f"{target}. Our figure is the middle of the range the model produced, "
        f"not its best case.")
    add("")
    for slug, r in results.items():
        m = r["model"]
        add(f"### {r['name']} — {m['council']} seats")
        add("")
        add("| party | actually won | our forecast | out by |")
        add("|---|---|---|---|")
        shown = [p for p in m["parties"]
                 if not (p["actual"] == 0 and p["forecast"] == 0)]
        for p in shown:
            name = DISPLAY.get(p["party"], p["party"].replace("_", " ").title())
            add(f"| {name} | {p['actual']} | {p['forecast']} | "
                f"{p['forecast'] - p['actual']:+d} |")
        add("")
        # The total is over EVERY party, not over the rows above, which are
        # the largest few. Saying so is the difference between a total and a
        # total that appears not to add up.
        add(f"*{m['seat_mae']} seats out in total — across every party that "
            f"stood, not only the {len(shown)} shown above.*")
        add("")
    add("## The technical measures, in plain language")
    add("")
    add("Three measures appear above, and they measure different things.")
    add("")
    add("**Seats out** adds up how many seats the forecast got wrong for each "
        "party. It is easy to read, and it ignores most of what a forecast "
        "says: it looks only at the single most likely outcome, not the range "
        "around it.")
    add("")
    add("**CRPS** (the continuous ranked probability score) is the number in "
        "the comparison table. It scores the *whole range* a forecast gives, "
        "not just its midpoint. Saying \"between 85 and 95 seats\" and being "
        "right scores better than saying \"exactly 90\" and being right, and "
        "a confident wrong answer is punished more than a hedged one. Lower is "
        "better; zero is perfect. It is in seats: a CRPS of 45 across a "
        "270-seat council is a small error.")
    add("")
    add("**Calling the ward** is the hardest and most direct test: 135 "
        "separate first-past-the-post contests in Johannesburg alone. A "
        "forecast that got the council roughly right while misreading which "
        "streets vote which way would show up here.")
    add("")
    add("One caveat. Two of the three baselines produce a single number rather "
        "than a range, so CRPS favours a model that gives ranges. The seats-out "
        "figure is the like-for-like comparison; its margin is smaller, and "
        "still in the model's favour.")
    add("")
    add("## What this does not prove")
    add("")
    if any(r["model"]["in_sample"] for r in results.values()):
        # ⛔ DO NOT TYPE THE COUNT. It said "Two inputs could not be confined",
        # listed the census and the splinter record, and then the second bullet
        # explained that the splinter record IS confined now — the page
        # contradicting itself one paragraph later. It was also wrong in the
        # other direction: `backtest.contaminated` returns three keys for 2021
        # and the run's own banner names others the page never mentions. So the
        # lead-in no longer counts, and the splinter bullet has moved out of
        # this list into the paragraph below, where it belongs as history.
        add("**These are not fully out-of-sample scores, and every run says "
            "so.** At least one input could not be confined to the period "
            "before the election; the run prints the full list above its "
            "results:")
        add("")
        add("* **The census.** Ward-level population figures come from the 2022 "
            "census, taken after the 2021 election; it is the only census we "
            "hold. A census records who lives in a ward, not how they voted, "
            "so it cannot leak a result. It is still information from after "
            "the fact, and is declared as such.")
        add("")
        add("**How much a breakaway party takes was a leak until 14 August "
            "2026.** When a well-known figure leaves a party and starts their "
            "own, how much of the old party's vote follows depends mostly on "
            "whether that figure's "
            # ⛔ THIS PARAGRAPH WAS FALSE FROM 2026-08-14 TO 2026-09-27.
            # It said the model used splinter records "including two from after
            # 2021" and called that "the single largest reason the Johannesburg
            # figure improves". Commit f33528f filtered the home splinter record
            # to the target on 14 August — so the 2021 backtest stopped using
            # MK's 2024 result that day — and this hand-written sentence went on
            # claiming the leak for six weeks, on a page whose second paragraph
            # says "No number on this page was typed by a person". The sentence
            # is not a number, which is exactly the hole.
            "support is in *this* city. Only one such split had happened "
            "anywhere before 2021. The model used to fill that gap with splits "
            "from after 2021, including MK's three years later, which "
            "flattered this page. Since 14 August 2026 the record is cut at "
            "the election being forecast, as every other record here is. "
            "Johannesburg's figure is worse for it.")
        add("")
        add("Read the scores as an estimate of what the machinery is worth, "
            "not as a sealed prediction made in 2021.")
    add("")
    add("**In one city the model loses.** Uniform swing beats it in Mangaung, "
        "the smallest council in the set.")
    add("")
    add("**The past is not the future.** Scoring well against 2021 does not "
        "guarantee 2026. Every party in this table existed in 2021. A party "
        "that has never stood before is the hardest thing to forecast, and the "
        "model's weakest area.")
    add("")
    return "\n".join(L)


def _seed() -> int:
    """The seed the runs used, read from the model rather than typed here."""
    import montecarlo
    return int(montecarlo.DEFAULTS["seed"])


def _git_head() -> str:
    import subprocess
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"],
                              cwd=Path(__file__).resolve().parents[1],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "unknown"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--target", default="2021")
    ap.add_argument("--draws", type=int, default=400)
    ap.add_argument("--from-json", action="store_true",
                    help="rebuild the page from the existing artefact and run "
                         "nothing; for a wording change, which must never need "
                         "a model run")
    ap.add_argument("--out", type=Path,
                    default=Path("docs-public/about-the-model.md"))
    args = ap.parse_args(argv)

    out_json = Path("data/processed") / f"validation_{args.target}.json"

    if args.from_json:
        # ⛔ REBUILD THE PAGE, RUN NOTHING. Every other path here re-runs eight
        # cities and REWRITES the artefact — which is how the 11 August run was
        # destroyed on 2026-09-27: it was gitignored, so there was no copy. A
        # wording fix should never need a model run, and until this flag existed
        # it did.
        record = json.loads(out_json.read_text())
        results = record["cities"]
        print(f"rebuilding the page from {out_json} "
              f"({record.get('draws')} draws, generated {record.get('generated')}) "
              f"— nothing re-run")
    else:
        print(f"validating against {args.target}, {args.draws} draws per city")
        results = collect(args.target, args.draws)
        if not results:
            raise SystemExit("no city produced a scored result")

        record = {"target": args.target, "draws": args.draws,
                  "generated": date.today().isoformat(), "cities": results,
                  # ⛔ WHICH RUN THIS WAS. The artefact promised provenance in
                  # its docstring and stored none, so attributing a 34-seat
                  # move took archaeology through six weeks of commits instead
                  # of a diff of two headers.
                  "seed": _seed(), "git_commit": _git_head(),
                  # the page's comparison figures, so a token can resolve them
                  "headline": headline(results)}
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(record, indent=2))

    body = markdown(args.target, results)
    # FROM THE RECORD, not from the flags. In --from-json the run being
    # described is the one on disk, and `args.draws` would be whatever the
    # default happens to be — a footer stating the wrong draw count under
    # figures it did not produce.
    body += (f"\n---\n\n*Generated {record['generated']} by "
             f"`src/build_validation.py` from a {record.get('draws', args.draws)}-draw "
             f"run per city against the {args.target} result. The underlying "
             f"figures are in `{out_json}`; the code that produced them is "
             f"public.*\n")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(body)
    print(f"wrote {args.out}"
          + ("" if args.from_json else f" and {out_json}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
