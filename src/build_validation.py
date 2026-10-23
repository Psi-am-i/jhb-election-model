"""Run the validation across every metro and write the section that reports it.

The section is /methodology's "How accurate is it?" scoring: it was the About
page until the owner's sweep of 2026-10-03, and `build_site.validation_html`
splices it into the methodology page, under its own headings (`###` and
below), as a region the number scan lists as generated.

**No figure in the section is typed.** The stat registry exists because
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
* ``docs-public/about-the-model.md`` — the section's source, regenerated whole.

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

# The backtest report truncates its own party column to fit a terminal
# (twelve characters: "ACTIVE_CITIZ", "INDEPENDENT_"), so the stored code is
# resolved back to the party it stands for (`party_names`) and named by the
# site's one rule (`render_map.party_label`). Until 2026-10-23 a typed table
# named some parties and the rest printed as truncated codes in title case
# ("Active Citiz", "Dop", two rows of "Independent").
CODE_WIDTH = 12


def party_names(slug: str, year: str, rows: list[dict]) -> list[str]:
    """The reader's name for each of ``rows``' parties, in order.

    A stored code is the party's code cut to :data:`CODE_WIDTH`. It is matched
    to the parties on that city's ballot that year (the cleaned voting-district
    file); where the cut fits several, the IEC's published seats pick the one
    with the row's actual seats, and parties with identical figures take their
    names in alphabetical order, each once. A code that matches nothing keeps
    the code's words."""
    import csv as _csv
    import cityconfig
    import official_seats
    import parties
    import render_map
    code = cityconfig.load(slug).code
    path = Path("data/raw/elections") / f"lge{year}_{code}_vd_party_clean.csv"
    on_ballot: dict[str, str] = {}      # code -> the ballot's own name
    if path.exists():
        with path.open(encoding="utf-8", newline="") as fh:
            on_ballot = {parties.canonical(r["sPartyName"]): r["sPartyName"]
                         for r in _csv.DictReader(fh)}
    official = (official_seats.read(code, int(year)) or {}).get("parties", {})
    seats_of = {parties.canonical(k): v.get("seats") for k, v in official.items()}
    used: set[str] = set()
    out = []
    for r in rows:
        short = r["party"]
        fits = sorted(f for f in on_ballot if f == short or
                      (len(short) == CODE_WIDTH and f.startswith(short)))
        if len(fits) > 1:
            fits = [f for f in fits if seats_of.get(f) == r["actual"]] or fits
        fits = [f for f in fits if f not in used]
        full = fits[0] if fits else short
        used.add(full)
        # a short code the pages do not name ("DOP") is named from the
        # ballot's own words, by the same rule
        named = full in render_map.NAMES or full in render_map.READER_NAMES \
            or full in parties.PARTIES or full not in on_ballot
        out.append(render_map.party_label(full) if named else render_map.reader_name(
            parties._derived_code(parties.normalise(on_ballot[full]))))
    return out


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


def losses_sentence(results: dict, best: dict) -> str:
    """Where This Model loses to its best baseline (by CRPS, the comparison
    table's) on each measure, read from the scores. It said "In one city the
    model loses ... Mangaung, the smallest council in the set" until
    2026-10-23: Buffalo City's council is smaller, and on seats This Model
    loses in two other cities."""
    import stats
    names = {s: r["name"] for s, r in results.items()}

    def _join(xs):
        return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]

    crps_lose = [names[s] for s, r in results.items()
                 if s in best and r["model"]["crps"] > best[s][1]["crps"]]
    wrong = {s: (stats.wrong_party_seats(r["model"]["seat_mae"]),
                 stats.wrong_party_seats(best[s][1]["seat_mae"]))
             for s, r in results.items() if s in best}
    seat_lose = [names[s] for s, (m, b) in wrong.items() if m > b]
    seat_tie = [names[s] for s, (m, b) in wrong.items() if m == b]
    parts = []
    parts.append(f"On the range score its best baseline beats This Model in "
                 f"{_join(crps_lose)}." if crps_lose else
                 "On the range score This Model beats its best baseline in every city.")
    if seat_lose:
        parts.append(f"On seats given to the wrong party it loses in {_join(seat_lose)}"
                     + (f" and ties in {_join(seat_tie)}." if seat_tie else "."))
    elif seat_tie:
        parts.append(f"On seats given to the wrong party it ties in {_join(seat_tie)}.")
    return "**Where This Model loses.** " + " ".join(parts)


def largest_miss_sentence(target: str, results: dict) -> str:
    """The largest seat miss in the city tables, read from the scores, and
    whether that party stood at the city's previous local election (its
    cleaned voting-district file). It said "Every party in this table existed
    in 2021" until 2026-10-23, above a table whose largest miss is ActionSA,
    which first stood in 2021."""
    import csv as _csv
    import cityconfig
    import parties
    miss, slug, row = max(((abs(p["forecast"] - p["actual"]), s, p)
                           for s, r in results.items() for p in r["model"]["parties"]),
                          key=lambda t: t[0])
    name = party_names(slug, target, [row])[0]
    city = results[slug]["name"]
    prev = str(int(target) - 5)
    code = cityconfig.load(slug).code
    path = Path("data/raw/elections") / f"lge{prev}_{code}_vd_party_clean.csv"
    stood = None
    if path.exists():
        with path.open(encoding="utf-8", newline="") as fh:
            stood = any(parties.canonical(r["sPartyName"]).startswith(row["party"])
                        for r in _csv.DictReader(fh))
    lead = (f"{name} first stood in {city} in {target}, and its seats there are"
            if stood is False else f"{name}'s seats in {city} are")
    return (f"{lead} This Model's largest miss in the tables above: "
            f"{row['forecast']} forecast, {row['actual']} won.")


def markdown(target: str, results: dict) -> str:
    """The section's Markdown, from the validation record ``results``.

    It says "Several" settings were chosen on records that include the
    elections scored, and gives no count: the validation record holds only
    each city's in-sample flag, and the one count on disk (history.json's
    in-sample manifest) is of a different, later run. A count from it would
    describe a run other than the one scored here (review, 2026-10-23)."""
    import stats
    h = headline(results)
    best = {s: min(r["baselines"].items(), key=lambda kv: kv[1]["crps"])
            for s, r in results.items() if r["baselines"]}
    total_m, total_b = h["crps_model"], h["crps_baseline"]

    L: list[str] = []
    add = L.append
    add("<!-- GENERATED by src/build_validation.py. Do not edit by hand: every")
    add("     figure below comes from the run recorded at the end of the section. -->")
    add("")
    # No title: the section sits under /methodology's "How accurate is it?",
    # so its headings start one level down (build_site.validation_html).
    add("Every result in this section comes from the run of This Model "
        "described at its end. The forecasts and scores used as examples under "
        "*The technical measures* are made up to explain the measures; they "
        "are not results.")
    add("")
    add("### How it was tested")
    add("")
    add("Each forecast used the previous local election for its geography, "
        "the national election before it for each party's starting level, and "
        "the voters' roll. It also used the 2022 census, taken after the "
        "election, and settings chosen on records that include the elections "
        "scored; *What this does not prove* says which.")
    add("")
    add("It was done in **eight metros, not one**. A model tuned on a single "
        "city can look excellent there and have learned only that city. Each "
        "city is fitted on its own wards, registration and history. The "
        "narrowest range a population group's turnout is given, and how "
        "closely the groups' turnouts move together, are measured across the "
        "eight metros, Johannesburg included.")
    add("")
    add("#### The three baselines")
    add("")
    add("The same scoring is applied to three baselines that need no model:")
    add("")
    add("| baseline | what it does |")
    add("|---|---|")
    add("| **last result repeats** | assume the previous local election happens again, unchanged |")
    add("| **uniform swing** | take the previous local election and add each party's change between the city's two national elections before the one forecast, equally in every voting district |")
    add("| **last result plus noise** | the previous result, with uncertainty added around it |")
    add("")
    add("Uniform swing is the usual standard for judging election models, and "
        "it is hard to beat. **Best baseline** below means whichever of the "
        "three did best in that city.")
    add("")
    add("### The result, city by city")
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
    # ⛔ THE HEADLINE IS NOT WRITTEN HERE. Wins, the total error, seats out and
    # wards called are /methodology's own sentence, as ledgered tokens
    # (`validation:` sources in content/joburg/stats.toml), directly above this
    # section: a figure that moves gets its arrow and its history there. Writing
    # them here as well printed every headline figure twice on one page.
    add(f"### What it forecast for {target}, against what happened")
    add("")
    # ⛔ SAY HOW MANY ROWS THIS IS. It read "Every party that won a seat in
    # 2021, in every city", and the artefact carries TWELVE parties per city
    # while Johannesburg seated eighteen. The page then printed a total over
    # ALL parties beneath rows that do not add up to it — Johannesburg's rows
    # sum to 56 against a printed 62, and the gap is exactly the six parties
    # left out. A reader with a calculator got a different number from the one
    # printed beside the table.
    # COUNTED from the table, not typed. The comment above is the whole
    # point: a sentence that describes the table has to be derived from the
    # table, or it goes stale the first time the table changes shape. The
    # count therefore lives in each table's own note (`len(shown)`), which is
    # what the reader sees. It was printed here as the artefact's row cap
    # (every city's `parties` list), which is not the number of rows shown
    # once parties with no seat actual or forecast are dropped.
    add(f"The largest parties in each city, by seats won in {target}; the "
        f"note under each table says how many are shown. Our figure is the "
        f"middle of the range This Model produced, not its best case.")
    add("")
    for slug, r in results.items():
        m = r["model"]
        add(f"#### {r['name']} — {m['council']} seats")
        add("")
        add("| party | actually won | our forecast | out by |")
        add("|---|---|---|---|")
        shown = [p for p in m["parties"]
                 if not (p["actual"] == 0 and p["forecast"] == 0)]
        for p, name in zip(shown, party_names(slug, target, shown)):
            add(f"| {name} | {p['actual']} | {p['forecast']} | "
                f"{p['forecast'] - p['actual']:+d} |")
        add("")
        # The total is over EVERY party, not over the rows above, which are
        # the largest few. Saying so is the difference between a total and a
        # total that appears not to add up. ONE UNIT with the methodology's
        # table: seats given to the wrong party (`stats.wrong_party_seats`,
        # the one definition), not the summed error, which counts each
        # misplaced seat twice and printed 96 beside the table's 48.
        add(f"*{stats.wrong_party_seats(m['seat_mae'])} seats given to the wrong "
            f"party in total, across every party that stood, not only the "
            f"{len(shown)} shown above.*")
        add("")
    add("### The technical measures, in plain language")
    add("")
    add("Three measures appear above, and they measure different things.")
    add("")
    add("**Seats given to the wrong party** counts the seats the forecast "
        "placed with a party that did not win them, from each party's middle "
        "forecast. It is easy to read, and it ignores most of what a forecast "
        "says: it looks only at each party's middle figure, not the range "
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
    add("Two of the three baselines produce a single number rather "
        "than a range, so CRPS favours a model that gives ranges. The seats "
        "given to the wrong party are the like-for-like comparison; their "
        "margin is smaller, and still in This Model's favour.")
    add("")
    add("### What this does not prove")
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
            "so.** Two kinds of input could not be confined to the period "
            "before the election:")
        add("")
        add("* **Settings.** Several of This Model's settings were chosen on "
            "records that include the elections scored here, so they have seen "
            "the results they are tested against.")
        add("* **The census.** Ward-level population-group shares come from the 2022 "
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
            #
            # ⛔ AND ITS COUNT WAS WRONG UNTIL 2026-10-23: "Only one such split
            # had happened anywhere before 2021", on a page naming Malema and
            # De Lille. The record cut at 2021 (`pools.home_splinter_record(
            # before_year="2021")`) holds two splits measured in the leader's
            # own city, GOOD (2019, Cape Town) and the NFP (2014, eThekwini);
            # the sentence now names them.
            "support is in *this* city. Before 2021 the record held two such "
            "splits measured in the leader's own city: GOOD in Cape Town and "
            "the NFP in eThekwini. This Model used to add splits from after "
            "2021, including MK's three years later, which flattered these "
            "scores. Since 14 August 2026 the record is cut at the election "
            "being forecast, as every other record here is. Johannesburg's "
            "figure is worse for it.")
        add("")
        add("Read the scores as an estimate of what the machinery is worth, "
            "not as a sealed prediction made in 2021.")
    add("")
    add(losses_sentence(results, best))
    add("")
    add(f"**The past is not the future.** Scoring well against {target} does "
        f"not guarantee 2026. {largest_miss_sentence(target, results)} A party "
        f"that has never stood before is the hardest thing to forecast, and "
        f"This Model's weakest area.")
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



def _long_date(iso: str) -> str:
    """"30 September 2026", the site's long date."""
    d = date.fromisoformat(str(iso)[:10])
    return f"{d.day} {d:%B %Y}"


def _which_model(record: dict) -> str:
    """"an earlier version of This Model" when the validation record was
    generated before the forecast now published (forecast_summary.json's
    `_generated`), else "This Model"."""
    summary = Path("data/processed") / "forecast_summary.json"
    try:
        now = str(json.loads(summary.read_text())["_generated"])[:10]
    except (OSError, KeyError, ValueError):
        return "an earlier version of This Model"
    return ("an earlier version of This Model" if str(record["generated"])[:10] < now
            else "This Model")

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
    # ⛔ NO FILE NAMES AND NO "draws" IN READER TEXT (owner, 2026-10-22,
    # audits/2026-10-22-headline-method/BRIEF.md B6). The artefact and the
    # code stay named in this module's docstring, for us. "An earlier
    # version" while the record predates the forecast it sits beside.
    body += (f"\n---\n\n*Tested on {_long_date(record['generated'])} against "
             f"{_which_model(record)}, on {record.get('draws', args.draws):,} "
             f"simulations per city of the {args.target} election.*\n")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(body)
    print(f"wrote {args.out}"
          + ("" if args.from_json else f" and {out_json}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
