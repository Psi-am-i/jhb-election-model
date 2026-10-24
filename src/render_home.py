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

The lede's words are the owner's, in `content/<city>/home.toml` (editable in
edit mode since 2026-10-06), with `{{lede_…}}` placeholders this module fills
(:data:`LEDE_PLACEHOLDERS`). A figure becomes a generated token. A phrase whose
strength depends on a figure is chosen by it (:func:`phrases`): "too close to
call" is a claim about the two leaders being close, and it would be a lie the
day one of them pulls away, so the number picks the words rather than leaving
a human to remember.
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
# The head-to-head's fixed order, for the one figure a dead heat prints.
# Presentation, not a ranking: the order `home.p_da_largest` was first
# published in (ledger, 2026-09-26). See `render_home`'s dead-heat branch.
HEAD_TO_HEAD_ORDER = ("DA", "ANC")

import render_sheet as _sheet
import scenarios as _scenarios

# ⛔ THE SEATS TABLE IS NOT THIS PAGE'S OWN DESIGN, AND THAT IS DELIBERATE.
# The parties named come from the run (`scenarios.named_parties`), their labels from the forecast sheet, and their
# colours from the site's one party palette (src/site_assets.py), so the two tables name the same parties — which is the only way the
# word "Others" can mean one number on both (owner, 2026-09-25). This page used
# to declare its own shorter list and its own colour map, and the cost was two
# "Others" rows differing by the seats of the three parties it left out, plus an
# IFP chip that was grey here and red there.
LABEL = _sheet.NAMES


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


#: What each {{lede_…}} placeholder in content/<city>/home.toml stands for. A
#: figure becomes a generated token (its source, a ledger row, an arrow); a
#: phrase chosen by a figure becomes a `data-word` span, which edit mode reads
#: as locked, like a token, and which is never a figure.
LEDE_PLACEHOLDERS = {
    "lede_coalition": "phrase: how certain a coalition is, chosen by lede_p_alone",
    "lede_race": "phrase: the race for largest party, chosen by the two chances",
    "lede_first": "phrase: the party with the higher chance of the most seats alone",
    "lede_second": "phrase: the other of the two",
    "lede_p_first": "figure: chance lede_first alone has the most seats",
    "lede_p_second": "figure: chance lede_second alone has the most seats",
    "lede_p_alone": "figure: chance one party reaches a majority alone",
    "lede_overhang_party": "phrase: the party the excessive-seats clause applies to most often",
    "lede_p_overhang": "figure: chance the clause applies to that party",
    "lede_overhang_seats": "figure: that party's share of the council, median where the clause applies to it",
    "lede_overhang_votes": "figure: its share of the party-list vote, median in the same simulations",
    "lede_first_cap": "phrase: lede_first at the start of a sentence",
    "lede_second_cap": "phrase: lede_second at the start of a sentence",
    # The ward sentence's joins (ward_phrases): its contrast ("While", "only")
    # is said only when ward_contrast holds, so each join is chosen by it.
    "lede_wards_open": "phrase: \"While \" + lede_first when ward_contrast holds, else lede_first_cap",
    "lede_wards_in": "phrase: \"in \" when ward_contrast holds, else nothing",
    "lede_wards_lead": "phrase: \"the lead is \" when ward_contrast holds, else nothing",
    "lede_wards_only": "phrase: \" with only\" when ward_contrast holds, else \",\"",
    "lede_wards_that": "phrase: \"that are \" when ward_contrast holds, else \"of them \"",
    "lede_not_safe": "phrase: \"not safe\", with its tooltip (tooltip_says.WORDS): won in under render_map.SAFE of simulations",
    "lede_wards_first": "figure: wards in which lede_first is the likeliest winner",
    "lede_close_first": "figure: of those, wards the map draws as contested (not safe)",
    "lede_wards_second": "figure: wards in which lede_second is the likeliest winner",
    "lede_close_second": "figure: of those, wards the map draws as contested",
}


def ward_races(processed: Path) -> dict:
    """``{party: (wards it is the likeliest winner of, how many of those the
    map draws as contested)}``, from ``ward_winner_probs.csv`` through the
    map's own call (``render_map.ward_call``), so "close" here is exactly a
    ward the map shades as contested (owner, 2026-10-22: the ANC's wards are
    far tighter than the DA's)."""
    import csv as _csv
    import render_map as _rm
    out: dict[str, list[int]] = {}
    with (Path(processed) / "ward_winner_probs.csv").open(encoding="utf-8", newline="") as fh:
        for r in _csv.DictReader(fh):
            call = _rm.ward_call(r["ward"], r["winner"], float(r["p_win"]), r["dist"])
            n = out.setdefault(r["winner"], [0, 0])
            n[0] += 1
            n[1] += call["cls"] == "contested"
    return {p: (a, b) for p, (a, b) in out.items()}


def ward_contrast(first: str, second: str, races: dict) -> bool:
    """Whether the first-named party has more not-safe wards than the second,
    both in number and as a share of the wards it leads: the one test for the
    ward sentence's contrast ("While", "only"), so the contrast is said only
    when it is true. The same test whichever party is named first."""
    (w1, c1), (w2, c2) = races.get(first, (0, 0)), races.get(second, (0, 0))
    return bool(c1 > c2 and w1 and w2 and c1 / w1 > c2 / w2)


def ward_phrases(first_name: str, contrast: bool) -> dict:
    """The ward sentence's joins, by :func:`ward_contrast` (owner, 2026-10-22,
    OWNER-DECISIONS 24). With the contrast: "While the ANC is ahead in N
    wards, in M of them the lead is not safe. The DA is ahead in K wards with
    only J that are not safe." Without: "The ANC is ahead in N wards, M of
    them not safe. The DA is ahead in K wards, J of them not safe."
    ``first_name`` is the first party as the page names it ("the ANC")."""
    cap = first_name[:1].upper() + first_name[1:]
    if contrast:
        return {"lede_wards_open": f"While {first_name}", "lede_wards_in": "in ",
                "lede_wards_lead": "the lead is ", "lede_wards_only": " with only",
                "lede_wards_that": "that are "}
    return {"lede_wards_open": cap, "lede_wards_in": "", "lede_wards_lead": "",
            "lede_wards_only": ",", "lede_wards_that": "of them "}


def not_safe_word() -> str:
    """"not safe", carrying its own tooltip: `data-say` names its sentence in
    ``tooltip_says.WORDS``, and ``build_site`` writes it into `data-prov` in
    the same pass as every figure's (the one tooltip writer). Class `mstat`
    so src/css/stat.css draws it like a figure's; no `data-token`, because it
    is not a figure."""
    return ('<span class="mstat" data-word="lede_not_safe" data-say="not_safe" '
            'data-prov="" tabindex="0">not safe</span>')


def load_lede(city_dir: Path) -> dict:
    """content/<city>/home.toml's one ``[[lede]]``: the owner's headline and
    paragraph, with placeholders. The one reader of that file."""
    path = city_dir / "home.toml"
    if not path.exists():
        raise SystemExit(f"no {path}: the home page's headline is written there.")
    items = tomllib.loads(path.read_text(encoding="utf-8")).get("lede", [])
    if len(items) != 1 or not all(isinstance(items[0].get(k), str) for k in ("head", "sub")):
        raise SystemExit(f"{path} must hold exactly one [[lede]] with `head` and `sub`.")
    return items[0]


def load_intro(city_dir: Path) -> dict:
    """content/<city>/home.toml's ``[intro]``: the introduction's heading and
    paragraphs (owner-approved, 2026-10-10)."""
    path = city_dir / "home.toml"
    intro = tomllib.loads(path.read_text(encoding="utf-8")).get("intro")
    if (not isinstance(intro, dict) or not isinstance(intro.get("heading"), str)
            or not intro.get("paragraphs")
            or not all(isinstance(p, str) for p in intro["paragraphs"])):
        raise SystemExit(f"{path} must hold one [intro] with `heading` and `paragraphs`.")
    return intro


def _intro(city_dir: Path) -> str:
    """The introduction, as written in home.toml: its heading as the section's
    eyebrow and each paragraph as one. Its words carry markup (links) and
    registry tokens, which the build resolves; nothing here is filled in."""
    intro = load_intro(city_dir)
    paras = "\n".join(f"  <p>{' '.join(p.split())}</p>" for p in intro["paragraphs"])
    return f'  <div class="eyebrow">{html.escape(intro["heading"])}</div>\n{paras}'


def fill_lede(template: str, values: dict, where: str) -> str:
    """``template`` with each ``{{lede_…}}`` replaced by its value. Refuses a
    placeholder it has no value for, rather than printing the braces."""
    import re as _re

    def one(m):
        name = m.group(1)
        if name not in values:
            raise SystemExit(
                f"{where}: {{{{{name}}}}} is not a placeholder the home page "
                f"fills. The ones it fills: {', '.join(sorted(values))} "
                f"(render_home.LEDE_PLACEHOLDERS).")
        return values[name]
    return _re.sub(r"\{\{(\w+)\}\}", one, " ".join(template.split()))


def _word(name: str, text: str) -> str:
    return f'<span data-word="{name}">{html.escape(text)}</span>'


def _overhang(processed: Path, party: str) -> tuple[float, float, int]:
    """``party``'s median share of the council's seats and of the party-list
    vote, over the simulations in which the excessive-seats clause applies to
    it, and how many those are.

    Seats and the clause come from the run's `seat_detail_draws.csv` (its
    `excessive` flag counts a party exactly at its quota, as the statute does);
    the list vote from the published draw export (`site/draws`, block
    `list_vote`, whole votes, as a share by `reweight.list_shares`), the only
    place the run's per-simulation list votes are kept. The
    two are joined by simulation number, and refused unless they hold the same
    seats for ``party`` in every simulation: two different runs would join
    silently otherwise.
    """
    import csv as _csv
    import numpy as _np
    import reweight as _rw

    with (processed / "seat_draws.csv").open(encoding="utf-8", newline="") as fh:
        size = {int(r["draw"]): int(r["council_size"]) for r in _csv.DictReader(fh)}
    seats, applies = {}, {}
    with (processed / "seat_detail_draws.csv").open(encoding="utf-8", newline="") as fh:
        for r in _csv.DictReader(fh):
            if r["party"] == party:
                d = int(r["draw"])
                seats[d], applies[d] = int(r["seats"]), r["excessive"] == "1"
    blocks, cols = _scenarios.published_draw_blocks(ROOT)
    statute = blocks["seats/deduct"][:, cols["seats/deduct"].index(party)]
    share = _rw.list_shares(blocks["list_vote"])[:, cols["list_vote"].index(party)]
    order = sorted(seats)
    if order != list(range(len(statute))) or any(seats[d] != int(statute[d]) for d in order):
        raise SystemExit(
            f"site/draws and seat_detail_draws.csv disagree about {party}'s seats: "
            f"they are not the same run. Re-export the draws from the run the "
            f"home page quotes (src/export_draws.py --index).")
    hit = [d for d in order if applies[d]]
    if not hit:
        return 0.0, 0.0, 0
    return (float(_np.median([seats[d] / size[d] for d in hit])),
            float(_np.median([share[d] for d in hit])), len(hit))


def race_figures(processed: Path) -> tuple[float, float, float, int]:
    """The chance one party governs alone, the chance the ANC and the DA each
    ALONE have the most seats, and the number of simulations.

    WHO IS LARGEST: reweight.largest_party, the one definition the forecast
    page and /your-forecast/ use, over the seat draws. forecast_summary.json's
    `structural.P(X is the largest single party)` is an argmax that credits
    every tied simulation to the first party in the model's order (side
    finding S1, 2026-10-02); a tie is its own outcome and is said as one.
    """
    import csv as _csv
    import numpy as _np
    import reweight as _rw
    import scenarios as _sc
    with (processed / "seat_draws.csv").open(encoding="utf-8", newline="") as fh:
        rows = list(_csv.DictReader(fh))
    parties = [k for k in rows[0] if k not in ("draw", "threshold", "council_size")]
    lp = _rw.largest_party(_np.array([[int(float(r[p] or 0)) for p in parties]
                                      for r in rows]), parties)
    return (_sc.majority_alone_share(processed), float(lp["outright"].get("ANC", 0.0)),
            float(lp["outright"].get("DA", 0.0)), len(rows))


def phrases(alone: float, anc: float, da: float) -> tuple[str, str, str, str]:
    """The headline's figure-chosen phrases: how certain a coalition is, the
    race for largest party, and the two parties in the order they are named.
    ``alone`` is the chance one party governs alone; ``anc`` and ``da`` the
    chance each alone has the most seats."""
    import stats as _stats

    # The owner's wording, 2026-09-23: "all but inevitable" at the top of the
    # ladder rather than "inevitable". One simulation in 5,000 IS a majority
    # alone, so the flat word would be contradicted by the figure printed in
    # the same paragraph.
    if alone < 0.01:
        coalition = "A coalition is all but inevitable"
    elif alone < 0.10:
        coalition = "A coalition is overwhelmingly likely"
    elif alone < 0.35:
        coalition = "A coalition is the likely outcome"
    else:
        coalition = "A coalition is one of two live outcomes"

    # ⛔ THE RACE FOLLOWS WHAT THE READER WILL SEE. An earlier version branched
    # on the raw gap and produced "the DA leads in 47% of simulations, the ANC
    # in 47%": a claimed lead between two identical printed figures. A dead
    # heat is decided by the formatter, and its order is HEAD_TO_HEAD_ORDER,
    # the order the ledger first published the pair in; otherwise the higher
    # figure goes first (STYLE rule 7, numeric). Both parties' tokens are
    # always printed, so neither is ever dropped and retired when the lead
    # changes hands.
    if _stats._fmt(max(anc, da), "chance") == _stats._fmt(min(anc, da), "chance"):
        first, second = HEAD_TO_HEAD_ORDER
        race = "a dead heat"
    else:
        first, second = ("ANC", "DA") if anc > da else ("DA", "ANC")
        race = ("too close to call" if abs(anc - da) < 0.05
                else f"leaning toward the {first}")
    return coalition, race, first, second


def _lede(summary: dict, processed: Path, tok, chance, city_dir: Path) -> str:
    """The headline and the paragraph under it: the owner's words from
    content/<city>/home.toml, with every figure and every figure-chosen phrase
    filled in from the run.

    It leads on the coalition (owner, 2026-09-23), because that is the finding:
    who is marginally ahead matters far less than the fact that nobody governs
    alone.

    ⛔ THE STRENGTH OF THE CLAIM IS CHOSEN BY THE NUMBER, NOT TYPED. The share of
    simulations in which one party reaches the threshold is read from the draws
    (`scenarios.majority_alone_share`, the same definition the sheet's tile
    uses). At 0.02% "inevitable" is honest; at 6% it would be a lie sitting in
    the largest type on the site, and nobody would notice until a journalist
    did. So the adjective is a placeholder the number fills, and the owner's
    words go round it.
    """
    alone, anc, da, n = race_figures(Path(processed))
    _src = f"seat_draws.csv, {n:,} simulations, the party alone with the most seats"
    coalition, race, first, second = phrases(alone, anc, da)
    value = {"ANC": anc, "DA": da}

    def party(code: str) -> str:
        nm = LABEL.get(code) or code
        return ("the " if nm.isupper() else "") + nm

    # THE CLAUSE: about the party it applies to most often (owner, 2026-10-05:
    # "leave the point to be about the ANC" unless another party is likely to
    # trigger it), chosen by the figures, so the sentence follows if that
    # changes.
    by_party = {p: float(v) for p, v in summary.get("p_excessive_by_party", {}).items()}
    over = max(sorted(by_party), key=lambda p: by_party[p])
    o_seats, o_votes, o_n = _overhang(Path(processed), over)
    o_name = party(over)
    o_src = (f"over the {o_n:,} simulations in which the excessive-seats clause "
             f"applies to {o_name}, counting a party exactly at its quota as the "
             f"statute does")

    values = {
        "lede_coalition": _word("lede_coalition", coalition),
        "lede_race": _word("lede_race", race),
        "lede_first": _word("lede_first", party(first)),
        "lede_second": _word("lede_second", party(second)),
        "lede_p_first": chance(f"home.p_{first.lower()}_largest", value[first], _src),
        "lede_p_second": chance(f"home.p_{second.lower()}_largest", value[second], _src),
        "lede_p_alone": chance("home.p_alone", alone,
                               "seat_draws.csv, one party at or above the threshold"),
        "lede_overhang_party": _word("lede_overhang_party", o_name),
        "lede_p_overhang": chance(f"home.p_excessive.{over.lower()}", by_party[over],
                                  "forecast_summary.json p_excessive_by_party"),
        "lede_overhang_seats": tok("home.overhang_seat_share", f"{o_seats:.6f}", "pct0",
                                   f"seat_detail_draws.csv seats over seat_draws.csv "
                                   f"council_size, median {o_src}"),
        "lede_overhang_votes": tok("home.overhang_list_share", f"{o_votes:.6f}", "pct0",
                                   f"site/draws list_vote, median {o_src}"),
    }
    races = ward_races(Path(processed))
    w_src = "ward_winner_probs.csv, the likeliest winner of each ward"
    c_src = ("ward_winner_probs.csv, wards the map draws as contested: the winner "
             "wins in under render_map.SAFE of simulations (render_map.ward_call)")
    cap = lambda s: s[:1].upper() + s[1:]  # noqa: E731
    values.update({
        "lede_first_cap": _word("lede_first_cap", cap(party(first))),
        "lede_second_cap": _word("lede_second_cap", cap(party(second))),
        **{k: _word(k, v) for k, v in
           ward_phrases(party(first), ward_contrast(first, second, races)).items()},
        "lede_not_safe": not_safe_word(),
        "lede_wards_first": tok(f"home.wards.{first.lower()}", races.get(first, (0, 0))[0], "int", w_src),
        "lede_close_first": tok(f"home.wards_close.{first.lower()}", races.get(first, (0, 0))[1], "int", c_src),
        "lede_wards_second": tok(f"home.wards.{second.lower()}", races.get(second, (0, 0))[0], "int", w_src),
        "lede_close_second": tok(f"home.wards_close.{second.lower()}", races.get(second, (0, 0))[1], "int", c_src),
    })
    assert set(values) == set(LEDE_PLACEHOLDERS), "LEDE_PLACEHOLDERS is the list"
    lede = load_lede(city_dir)
    where = str(city_dir / "home.toml")
    head = fill_lede(lede["head"], values, where + " head")
    sub = fill_lede(lede["sub"], values, where + " sub")
    # `date_long` is the registry's only date format; there is no "date".
    stamp = (f'{tok("home.n_draws", int(summary["_draws"]), "comma")} '
             f"of This Model's simulations as of "
             f'{tok("home.generated", summary["_generated"], "date_long")}')
    return (f'  <h1 class="state">{head}</h1>\n'
            f'  <p class="sub">{sub}</p>\n'
            f'  <div class="stamp">{stamp}</div>')


def _seats(summary: dict, tok, processed: Path) -> str:
    parties = summary["parties"]
    named = [p for p in _scenarios.named_parties(processed) if p in parties]
    others = sorted(set(parties) - set(named))
    # THE FORECAST PAGE'S ORDER (render_sheet's seat chart): middle seat count,
    # then mean seats over the draws, highest first. STYLE rule 7: numeric,
    # never a fixed list (the rows used to follow NAMED_PARTIES, which put the
    # EFF above ActionSA with fewer seats; review 2026-10-02).
    import csv as _csv
    with (Path(processed) / "seat_draws.csv").open(encoding="utf-8", newline="") as fh:
        _draws = list(_csv.DictReader(fh))
    _mean = {p: sum(float(r[p] or 0) for r in _draws) / len(_draws) for p in named}
    rows_order = sorted(named, key=lambda p: (-float(parties[p]["median"]), -_mean[p]))
    rows = []

    # THE SITE'S ONE SEAT TABLE (src/seat_table.py), the forecast page's own.
    # The token names are this page's (`home.seats.<party>`, `_lo`, `_hi`):
    # they are what its ledger rows were published under.
    def row(code: str, label: str, med: float, lo: float, hi: float,
            source: str | None = None) -> dict:
        key = code.lower()
        src_of = (lambda n, v, f: tok(n, v, f, source)) if source else tok
        return {"code": code.upper(), "name": label,
                "seats": src_of(f"home.seats.{key}", int(round(med)), "int"),
                "lo": src_of(f"home.seats.{key}_lo", int(round(lo)), "int"),
                "hi": src_of(f"home.seats.{key}_hi", int(round(hi)), "int"),
                "m": med, "p5": lo, "p95": hi}

    for code in rows_order:
        p = parties[code]
        rows.append(row(code, LABEL.get(code, code),
                        float(p["median"]), float(p["p5"]), float(p["p95"])))
    if others:
        import scenarios as _scn
        med, lo, hi = _scn.seat_quantiles(_scn.others_per_draw(processed, named))
        # ⛔ "Others" ON BOTH PAGES, ONE WORD FOR ONE NUMBER. This row read
        # "Everyone else" here and "Others" on the forecast sheet until
        # 2026-09-26. The two now print the same figure (`scenarios.named_parties`
        # is the one named set), and two labels for one figure invites the same
        # confusion the shared set was adopted to end (owner: settle for one).
        rows.append(row("Others", "Others", med, lo, hi,
                        source="seat_draws.csv, council minus the named "
                               "parties in each simulation"))

    # ⛔ NOT "the middle simulation". Each row is that PARTY's middle value
    # across the simulations, and different parties peak in different ones — so
    # the rows do not add to the council and must not be described as if they
    # were one scenario. That conflation is the shape of §1.214.
    import scenarios as _scn
    band = tok("home.band", _scn.BAND_SHARE, "chance",
               "scenarios.BAND, the percentiles seat_quantiles reports")
    note = ('  <div class="stamp seatnote">Each party\'s middle '
            f'value across the simulations, with the range covering {band} of '
            'them. They do not add up to the council: a party\'s best '
            'simulations are not the same ones as its rivals\'. "Others" is '
            'the council minus the parties named above, taken '
            '<em>within</em> each simulation.</div>')
    import seat_table
    return ("  " + seat_table.table(rows, label="Seats by party, if the election were held now")
            + "\n" + note)


#: Where the home page's map goes (home.html), filled at build time by
#: :func:`home_map` (`build_site.fill_home_map`).
HOME_MAP_MARKER = "<!-- __HOMEMAP__ -->"


def home_map(sheet: str) -> str:
    """The home page's map: the simplified version of the forecast page's
    (owner, 2026-10-10: "a simplified version, not a copy"), cut from the
    map ``render_map`` wrote into ``sheet`` (forecast-sheet.html) at build
    time, so the two maps are always the same run. The map itself with its
    ward tips and the key's party colours and its solid/stripes line; not the
    heading, the explanation, the Normal/Equal Sized switch, the equal-ward
    map or the key's long note, which /forecast carries. The caption is
    /forecast's own, note removed, so its words about the council bar the
    map still draws come from where /forecast's do. Refuses a sheet
    whose map has lost a piece it cuts by.

    The cut keeps ``render_map``'s own region markers round it: its figures
    (the key's thresholds and ward counts) are the map generator's, and the
    number scan lists them as such (``stats.GENERATED_MARKERS``), as it does
    on /forecast. Only the built page carries them; home.html's source has
    the build-time marker alone, so ``render_map`` never writes into it."""
    import render_map
    if sheet.count(render_map.MARK_START) != 1:
        raise SystemExit("forecast-sheet.html has no single map region for the "
                         "home page's map")
    region = sheet[sheet.index(render_map.MARK_START):sheet.index(render_map.MARK_END)]

    def cut(start: str, end: str) -> str:
        if region.count(start) != 1 or end not in region[region.index(start):]:
            raise SystemExit(f"the forecast map no longer has {start!r} ... {end!r}, "
                             "which the home page's map is cut by")
        i = region.index(start)
        return region[i:region.index(end, i)]
    box = cut('<div class="mapbox">', "\n      <figcaption")
    caption = cut('<figcaption class="mapcaption">', "</figcaption>") + "</figcaption>"
    import re as _re
    caption, n = _re.subn(r'\s*<br><span class="mapkey-note">[^<]*</span>', "", caption)
    if n != 1:
        raise SystemExit(f"the forecast map's key has {n} long notes, not one, "
                         "for the home page's map to leave out")
    return (f'{render_map.MARK_START}\n    <figure class="homemap">\n      {box.strip()}\n'
            f'      {caption.strip()}\n'
            f'    </figure>\n    {render_map.MARK_END}')


def load_articles(city_dir: Path) -> list[dict]:
    """The articles in content/<city>/articles.toml: the one reader of that
    file. The home page's and /commentary's lists, and each article page's
    <title> and share card (`build_site.artefact_head`), all come from here."""
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
    return items


def _articles(city_dir: Path, exclude: str | None = None) -> str:
    """The list of articles: the home page's, /commentary's and, without the
    article itself (``exclude``, its href), the one under each article
    (``build_site.more_commentary``). One definition for all three."""
    items = [a for a in load_articles(city_dir) if a["href"] != exclude]
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
    """The home page's list of claims, each linked to its own page
    (``/claims/<slug>``, build_site.claim_pages; owner, 2026-10-11)."""
    from og_pages import CLAIM_DIR
    path = city_dir / "claims.toml"
    if not path.exists():
        return '  <div class="feed"></div>'
    items = tomllib.loads(path.read_text(encoding="utf-8")).get("claim", [])
    # The one verdict check, its form only: this page computes no figure, so
    # the chance itself is checked where it is computed (render_sheet).
    _sheet.claims_faults(items)
    out = []
    for c in items:
        when = c.get("captured", "")
        # The date of the QUOTE, and labelled so: it is not when we published
        # the test (fault-finder review 2026-09-30; that is the claim box's
        # `published`, from the ledger).
        # The party's colour and logo, and the verdict on the one verdict
        # scale: the same class names /claims uses (render_sheet), so the two
        # cannot drift (owner, 2026-10-06).
        party = c.get("party", "")
        ident = (f'<img class="plogo" src="logos/{html.escape(c["logo"])}.png" alt="" '
                 f'width="56" height="56">' if c.get("logo") else
                 f'<span class="pchip pc-{html.escape(party)}"></span>')
        verdict = c.get("verdict", "")
        out.append(
            f'    <div class="item pc-{html.escape(party)}" data-asof="{when}">\n'
            f'      {ident}\n'
            f'      <div>\n'
            f'        <div class="t"><a href="{CLAIM_DIR}/{html.escape(c["slug"])}">'
            f'{html.escape(c.get("label") or c.get("tests") or c.get("quote", "")[:90])}</a></div>\n'
            f'        <div class="meta"><span class="verdict {_sheet.verdict_class(verdict)}">'
            f'{html.escape(verdict)}</span>'
            f'<span class="when">{html.escape(LABEL.get(party) or party)} · said {_pretty(when)}</span></div>\n'
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
                  _lede(summary, city.processed, tok, chance,
                        ROOT / "content" / city.slug))
    page = region(page, "HOMESEATS", _seats(summary, tok, city.processed))
    city_dir = ROOT / "content" / city.slug
    page = region(page, "HOMEINTRO", _intro(city_dir))
    page = region(page, "HOMEARTICLES", _articles(city_dir))
    page = region(page, "HOMECLAIMS", _claims(city_dir))
    args.page.write_text(page, encoding="utf-8")

    n_articles = len(load_articles(city_dir))
    print(f"home: lede, {len(_scenarios.named_parties(city.processed))} named parties + others, "
          f"{n_articles} articles -> {args.page.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
