"""Fill the home page's generated regions from the run that produced them.

    .venv/bin/python src/render_home.py --city joburg

Writes between the `__HOMELEDE__`, `__HOMESEATS__`, `__HOMEARTICLES__` and
`__HOMECLAIMS__` markers of `home.html`. The map arrives separately, from
`render_map.py`, which writes into every file carrying its own markers.

⛔ **EVERY FIGURE IS A GENERATED TOKEN**, `{{@name=value;fmt;source}}`, resolved
by `build_site` — which is what gives it a source, a ledger row and an arrow
when it moves. Nothing here types a number into prose and nothing is written by
page script: that was the defect the whole 2026-09-17 pass was about, and the
home page is not allowed to reintroduce it.

The lede is a SENTENCE, and its shape changes with the result: "too close to
call" is a claim about the two leaders being within a seat of each other, and it
would be a lie the day one of them pulls away. `_lede` picks the wording from
the numbers rather than leaving a human to remember.
"""
from __future__ import annotations

import argparse
import html
import json
import tomllib
from pathlib import Path

import cityconfig

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "home.html"

# The parties the seat table names. Everyone else is pooled into "Others",
# which is what the council actually looks like: the long tail is real but
# nobody reads a table of forty rows.
NAMED = ("ANC", "DA", "ASA", "EFF", "MK", "PA", "IFP")
LABEL = {"ANC": "ANC", "DA": "DA", "ASA": "ActionSA", "EFF": "EFF",
         "MK": "MK Party", "PA": "PA", "IFP": "IFP"}
COLOUR = {"ANC": "var(--anc)", "DA": "var(--da)", "ASA": "var(--asa)",
          "EFF": "var(--eff)", "MK": "var(--mk)", "PA": "var(--pa)",
          "IFP": "var(--oth)", "Others": "var(--oth)"}


def region(page: str, name: str, body: str) -> str:
    """Replace one marked region, refusing rather than appending blindly."""
    start, end = f"<!-- __{name}_START__ -->", f"<!-- __{name}_END__ -->"
    if start not in page or end not in page:
        raise SystemExit(
            f"home.html has no {name} region. The markers are what make this "
            f"page regenerable; without them a build would silently leave the "
            f"last run's numbers in place.")
    i, j = page.index(start), page.index(end) + len(end)
    return page[:i] + start + "\n" + body.rstrip() + "\n  " + end + page[j:]


def _lede(summary: dict, processed: Path, tok, chance) -> str:
    """The verdict, in a sentence whose SHAPE follows the numbers.

    It leads on the coalition (owner, 2026-09-23), because that is the finding:
    who is marginally ahead matters far less than the fact that nobody governs
    alone.

    ⛔ THE STRENGTH OF THE CLAIM IS CHOSEN BY THE NUMBER, NOT TYPED. The share of
    simulations in which one party reaches the threshold is read from the draws
    (`scenarios.majority_alone_share`, the same definition the sheet's tile
    uses). At 0.02% "inevitable" is honest; at 6% it would be a lie sitting in
    the largest type on the site, and nobody would notice until a journalist
    did. So the adjective is a function of the measurement, and the measurement
    is shown in the same breath.
    """
    import scenarios as _sc

    st = summary["structural"]
    anc = float(st.get("P(ANC is the largest single party)", 0.0))
    da = float(st.get("P(DA is the largest single party)", 0.0))
    alone = _sc.majority_alone_share(processed)
    lead, trail = ("ANC", "DA") if anc >= da else ("DA", "ANC")

    p_lead = chance(f"home.p_{lead.lower()}_largest", max(anc, da))
    p_trail = chance(f"home.p_{trail.lower()}_largest", min(anc, da))
    p_alone = chance("home.p_alone", alone,
                     "seat_draws.csv, one party at or above the threshold")

    # The owner's wording, 2026-09-23: "all but inevitable" at the top of the
    # ladder rather than "inevitable". One simulation in 5,000 IS a majority
    # alone, so the flat word would be contradicted by the figure printed in
    # the next sentence.
    if alone < 0.01:
        coalition = "A coalition is all but inevitable"
    elif alone < 0.10:
        coalition = "A coalition is overwhelmingly likely"
    elif alone < 0.35:
        coalition = "A coalition is the likely outcome"
    else:
        coalition = "A coalition is one of two live outcomes"

    # ⛔ THE SECOND CLAUSE FOLLOWS WHAT THE READER WILL SEE. An earlier version
    # branched on the raw gap and produced "the DA leads in 47% of simulations,
    # the ANC in 47%" — a claimed lead between two identical printed figures.
    # At four decimal places one of them is always ahead; the question is
    # whether the difference survives the formatter.
    import stats as _stats
    if _stats._fmt(max(anc, da), "chance") == _stats._fmt(min(anc, da), "chance"):
        race = (f'we have a dead heat: the ANC and the DA each lead in '
                f'{p_lead} of simulations')
    elif abs(anc - da) < 0.05:
        race = (f'the race is too close to call: the {lead} leads in {p_lead} '
                f'of simulations, the {trail} in {p_trail}')
    else:
        race = (f'the {lead} leads, in {p_lead} of simulations against the '
                f'{trail}\'s {p_trail}')

    head = f'<em>{coalition}</em> and {race}.'

    excessive = chance("home.p_excessive_any", float(summary["p_excessive_any"]),
                       "forecast_summary.json p_excessive_any")
    sub = (f'One party governs alone in {p_alone} of simulations. And a '
           f'rarely-used clause lets a party keep every ward it wins whatever '
           f'its proportional share, taking the shortfall from everyone else — '
           f'it fires in {excessive} of them.')
    # `date_long` is the registry's only date format; there is no "date".
    stamp = (f'Model run '
             f'{tok("home.generated", summary["_generated"], "date_long")} '
             f'· {tok("home.n_draws", int(summary["_draws"]), "comma")} '
             f'simulations')
    return (f'  <h1 class="state">{head}</h1>\n'
            f'  <p class="sub">{sub}</p>\n'
            f'  <div class="stamp">{stamp}</div>')


def _others_from_draws(processed: Path, named: set[str]):
    """Everyone except the named parties, per simulation, then its quantiles.

    ⛔ PERCENTILES DO NOT ADD, AND THE DRAWN PARTIES ARE NOT THE WHOLE COUNCIL.
    Two ways to get this row wrong, and the first version managed both:

    * summing each small party's median gives a number no simulation produced,
      and summing their p5s and p95s gives a "range" wider than any draw — 1 to
      95 seats, for a row whose real spread is a few. The same arithmetic in the
      other direction is how "smaller parties — 39 seats" was published.
    * `seat_draws.csv` carries only the parties drawn INDIVIDUALLY — 13 of
      them. They sum to about 259 of 270, so a tail built from those columns
      alone silently loses ~11 seats that belong to parties the model does not
      draw separately.

    So the quantity is the council minus the named parties, TAKEN WITHIN EACH
    SIMULATION, where it is simply true: the seats exist and somebody holds
    them. Quantiles are then read off that distribution.
    """
    import csv as _csv
    path = processed / "seat_draws.csv"
    if not path.exists():
        return None
    totals = []
    with path.open(encoding="utf-8", newline="") as fh:
        for row in _csv.DictReader(fh):
            council = int(float(row.get("council_size") or 0))
            held = sum(int(float(row.get(p) or 0)) for p in named)
            totals.append(council - held)
    if not totals:
        return None
    totals.sort()
    n = len(totals)

    def q(p):
        return float(totals[min(n - 1, max(0, int(round(p * (n - 1)))))])

    return q(0.5), q(0.05), q(0.95)


def _seats(summary: dict, tok, processed: Path) -> str:
    parties = summary["parties"]
    named = [p for p in NAMED if p in parties]
    others = sorted(set(parties) - set(named))
    rows, widest = [], max(float(parties[p]["p95"]) for p in named) or 1.0

    def row(code: str, label: str, med: float, lo: float, hi: float,
            source: str | None = None) -> str:
        key = code.lower()
        src_of = (lambda n, v, f: tok(n, v, f, source)) if source else tok
        return (
            f'    <div class="srow">\n'
            f'      <div class="sname"><span class="chip" style="background:'
            f'{COLOUR.get(code, "var(--oth)")}"></span>{html.escape(label)}</div>\n'
            f'      <div class="strack"><i style="width:'
            f'{100 * med / widest:.1f}%;background:{COLOUR.get(code, "var(--oth)")}">'
            f'</i></div>\n'
            f'      <div class="sval"><b>'
            f'{src_of(f"home.seats.{key}", int(round(med)), "int")}'
            f'</b> {src_of(f"home.seats.{key}_lo", int(round(lo)), "int")}–'
            f'{src_of(f"home.seats.{key}_hi", int(round(hi)), "int")}</div>\n'
            f'    </div>')

    for code in named:
        p = parties[code]
        rows.append(row(code, LABEL.get(code, code),
                        float(p["median"]), float(p["p5"]), float(p["p95"])))
    tail = _others_from_draws(processed, set(named)) if others else None
    if tail:
        med, lo, hi = tail
        rows.append(row("Others", "Everyone else", med, lo, hi,
                        source="seat_draws.csv, council minus the named "
                               "parties in each simulation"))
    elif others:
        raise SystemExit(
            "no seat_draws.csv, so the small parties' total cannot be taken "
            "per simulation — and it may not be faked by adding up their "
            "medians. Run the model first.")

    # ⛔ NOT "the middle simulation". Each row is that PARTY's middle value
    # across the simulations, and different parties peak in different ones — so
    # the rows do not add to the council and must not be described as if they
    # were one scenario. That conflation is the shape of §1.214.
    note = ('  <div class="stamp" style="margin-top:12px">Each party\'s middle '
            'value across the simulations, with the range covering 90% of '
            'them. They do not add up to the council: a party\'s best '
            'simulations are not the same ones as its rivals\'. "Everyone '
            'else" is the council minus the parties named above, taken '
            '<em>within</em> each simulation.</div>')
    return '  <div class="seats">\n' + "\n".join(rows) + "\n  </div>\n" + note


def _articles(city_dir: Path) -> str:
    path = city_dir / "articles.toml"
    if not path.exists():
        raise SystemExit(f"no {path}: the home page has no articles to list.")
    items = tomllib.loads(path.read_text(encoding="utf-8")).get("article", [])
    leads = [a for a in items if a.get("lead")]
    if len(leads) != 1:
        raise SystemExit(
            f"{path} marks {len(leads)} articles as `lead`, and the home page "
            f"runs exactly one. Retiring a lead means moving that flag, not "
            f"deleting the piece.")
    out = []
    # The lead first, then the rest newest first.
    for a in sorted(items, key=lambda x: (bool(x.get("lead")), x["date"]),
                    reverse=True):
        when = a["date"]
        klass = "item lead-item" if a.get("lead") else "item"
        # Each entry is its own dated passage: the figures inside a standfirst
        # are the ones that were PUBLISHED on that date and are not re-derived.
        out.append(
            f'    <div class="{klass}" data-asof="{when}">\n'
            f'      <div class="when">{_pretty(when)}</div>\n'
            f'      <div>\n'
            f'        <div class="t"><a href="{html.escape(a["href"])}">'
            f'{html.escape(a["title"])}</a></div>\n'
            f'        <div class="d">{html.escape(" ".join(a["standfirst"].split()))}</div>\n'
            f'      </div>\n'
            f'    </div>')
    return '  <div class="feed">\n' + "\n".join(out) + "\n  </div>"


def _claims(city_dir: Path) -> str:
    path = city_dir / "claims.toml"
    if not path.exists():
        return '  <div class="feed"></div>'
    items = tomllib.loads(path.read_text(encoding="utf-8")).get("claim", [])
    out = []
    for c in items:
        when = c.get("captured", "")
        out.append(
            f'    <div class="item" data-asof="{when}">\n'
            f'      <div class="when">{_pretty(when)}</div>\n'
            f'      <div>\n'
            f'        <div class="t"><a href="forecast#claims">'
            f'{html.escape(c.get("label") or c.get("tests") or c.get("quote", "")[:90])}</a></div>\n'
            f'        <div class="verdict">{html.escape(c.get("verdict", ""))}</div>\n'
            f'      </div>\n'
            f'    </div>')
    return '  <div class="feed">\n' + "\n".join(out) + "\n  </div>"


def _pretty(iso: str) -> str:
    if not iso:
        return ""
    y, m, d = iso.split("-")
    return f"{int(d)} {'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()[int(m) - 1]}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    cityconfig.add_city_argument(ap)
    ap.add_argument("--page", type=Path, default=PAGE,
                    help="the page to fill; a scratch copy lets a test "
                         "regenerate the tokens without writing the tree")
    args = ap.parse_args(argv)
    city = cityconfig.use(getattr(args, "city", None))

    summary_path = city.processed / "forecast_summary.json"
    if not summary_path.exists():
        raise SystemExit(
            f"no {summary_path}. The home page quotes the run, so there has to "
            f"be one: python src/montecarlo.py --city {city.slug}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    src = f"forecast_summary.json, {summary['_draws']:,} simulations"

    def tok(name, value, fmt, source=src):
        return f"{{{{@{name}={value};{fmt};{source}}}}}"

    def chance(name, value, source=src):
        return tok(name, f"{float(value):.6f}", "chance", source)

    page = args.page.read_text(encoding="utf-8")
    page = region(page, "HOMELEDE",
                  _lede(summary, city.processed, tok, chance))
    page = region(page, "HOMESEATS", _seats(summary, tok, city.processed))
    city_dir = ROOT / "content" / city.slug
    page = region(page, "HOMEARTICLES", _articles(city_dir))
    page = region(page, "HOMECLAIMS", _claims(city_dir))
    args.page.write_text(page, encoding="utf-8")

    n_articles = len(tomllib.loads((city_dir / "articles.toml")
                                   .read_text(encoding="utf-8"))["article"])
    print(f"home: lede, {len(NAMED)} named parties + others, "
          f"{n_articles} articles -> {args.page.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
