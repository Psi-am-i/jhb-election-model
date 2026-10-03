"""Regenerate forecast-sheet.html's data block from the model outputs.

The sheet's previous revision hand-copied its numbers into the HTML, so any
re-run silently made them stale (review, Part 4). This script computes every
figure the sheet displays from `seat_draws.csv` and `forecast_summary.json`
and rewrites the block between the __GEN_START__ / __GEN_END__ markers.

Run after any montecarlo.py re-run:
    python src/render_sheet.py
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import tomllib
from pathlib import Path

import numpy as np

import cityconfig


def _md(text: str) -> str:
    """The only markup claims.toml needs: **bold**."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

CHIPS = {
    "DA": "#1B5EA8", "ANC": "#1B7A3D", "EFF": "#B3202B", "MK": "#5B6E22",
    "ASA": "#2FA79B", "PA": "#E0A419", "IFP": "#C8442A", "RISE": "#7A6BA8",
    "VFPLUS": "#B0752D", "ACDP": "#6B4E9E", "ALJAMAAH": "#2E8B72",
    "ENTRANT": "#b9b9b9",
}
#: The colour of every party CHIPS leaves out, and of "Others".
OTHER_CHIP = "#8b918b"
NAMES = {
    "DA": "DA", "ANC": "ANC", "EFF": "EFF", "MK": "MK Party", "ASA": "ActionSA",
    "PA": "PA", "IFP": "IFP", "RISE": "Rise Mzansi", "VFPLUS": "VF+",
    "ACDP": "ACDP", "ALJAMAAH": "Al Jama-ah", "ENTRANT": "New entrant",
    "SOUTH_AFRICAN_COMMUNIST_PARTY": "SACP", "BOSA": "BOSA",
    "ALL_CITIZENS_PARTY": "All Citizens Party",
}
import scenarios as _scenarios  # noqa: E402  (constants below read it)

# ⛔ A COALITION TOKEN'S IDENTITY MAY NOT DEPEND ON A RUN'S SEAT RANKING. The
# key was `"+".join(members_of(m))`, and `members_of` follows the parties'
# mean-seat order, so when MK and the PA swapped places between the
# 27 September edition and the F11 build every four-party key containing both
# changed spelling ("ANC+ASA+PA+MK" became "ANC+ASA+MK+PA"): the ledger read
# seven still-listed coalitions as retired and seven identical ones as new,
# with no history. The key now spells members in this fixed order, which is
# the order every coalition token in the ledger was first published in;
# a party not listed follows, alphabetically. Presentation only: the row's
# displayed order is still by seats. Set 2026-09-29.
COALITION_KEY_ORDER = ("DA", "ANC", "ASA", "EFF", "PA", "MK")


def coalition_key(members) -> str:
    rank = {p: i for i, p in enumerate(COALITION_KEY_ORDER)}
    return "+".join(sorted(members,
                           key=lambda p: (rank.get(p, len(rank)), p)))



# ⛔ NOT A LIST OF ITS OWN — `scenarios.NAMED_PARTIES` is the one set both seats
# tables name, because "Others" is its complement and one word may not mean two
# numbers. See that constant's note.
CHART_PARTIES = list(_scenarios.NAMED_PARTIES)

ALLIANCE_8 = ("DA", "ASA", "PA", "IFP", "VFPLUS", "ACDP", "RISE", "ALJAMAAH")

# How many ANC wards a DA-majority simulation has to take before the narrative
# calls it "breaking the wall". ⛔ IT IS A PARAMETER OF THE QUERY, AND THE PAGE
# USED TO TYPE IT TOO — "at least 30 of the ANC's usual wards" sat in
# `forecast-sheet.html` beside a count computed with `>= 30` here, so an edit to
# either left the sentence describing a different scenario from the number next
# to it. The page now renders it as a token.
WALL_FLIPS = 30


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed", type=Path, default=None,
                        help="where inputs are read (default: the target's own processed "
                             "directory). A literal data/processed is "
                             "JOHANNESBURG's, whatever --city says")
    parser.add_argument("--sheet", type=Path, default=Path("forecast-sheet.html"))
    cityconfig.add_city_argument(parser)
    args = parser.parse_args(argv)
    # Only the real sheet also writes the draft copy and the shared claim boxes.
    # A --sheet elsewhere (a test regenerating into a scratch copy) writes that
    # file and nothing else, so checking the page can never rewrite it.
    real_sheet = args.sheet.resolve() == Path("forecast-sheet.html").resolve()
    PAGES = ((Path("forecast-sheet.html"), Path("drafts/forecast-draft.html"))
             if real_sheet else (args.sheet,))
    cityconfig.use(getattr(args, "city", None))
    args.processed = args.processed or cityconfig.use_target(
        getattr(args, "target", None)).processed

    with (args.processed / "seat_draws.csv").open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    parties = [k for k in rows[0] if k not in ("draw", "threshold", "council_size")]
    S = {p: np.array([int(r[p]) for r in rows]) for p in parties}
    thr = np.array([int(r["threshold"]) for r in rows])
    council = np.array([int(r["council_size"]) for r in rows])
    summary = json.loads((args.processed / "forecast_summary.json").read_text())

    import scenarios as _scq

    def q(series):
        return _scq.seat_quantiles(series)

    def coalition(*members):
        total = sum(S[p] for p in members if p in S)
        med, lo, hi = q(total)
        return {"p": round(float((total >= thr).mean()), 4),
                "med": med, "lo": lo, "hi": hi}

    # largest party, and whether anyone ever gets to govern alone. ONE
    # DEFINITION, shared with /play/: reweight.largest_party. This was an
    # argmax over this file's column order, which credited every tied
    # simulation to the first column, the DA (side finding S1, 2026-10-02).
    import reweight as _rw
    _lp = _rw.largest_party(np.stack([S[p] for p in parties], axis=1), parties)
    p_da_largest = _lp["outright"]["DA"]
    p_anc_largest = _lp["outright"]["ANC"]
    p_tied_largest = _lp["tied"]
    # ONE DEFINITION, shared with the home page's heading — see
    # scenarios.majority_alone_share. The inline version lived here and
    # the heading needed the same number; two copies of "can anyone
    # govern alone" is how a tile comes to disagree with the prose.
    import scenarios as _sc_alone
    p_alone = _sc_alone.majority_alone_share(args.processed)
    alone_str = f"{p_alone:.0%}" if p_alone >= 0.001 else "&lt;0.1%"

    p_excessive = summary.get("p_excessive_by_party", {}).get("ANC", 0.0)
    thr_med = int(np.median(thr))
    minority = {m["scenario"]: m["p_viable"] for m in summary["minority"]}
    da_minority = minority.get("DA minority, only ANC opposes (2021 pattern)", 0.0)
    anc_da = coalition("ANC", "DA")

    # ⛔ NO FIGURE ON THE PAGE IS WRITTEN BY SCRIPT ANY MORE (owner, 2026-09-17).
    # These sections used to be a `const GEN = {...}` JSON block that page script
    # poured into the DOM at view time. A number written that way had no
    # provenance underline or tooltip, no ledger row and so no arrow, and was
    # invisible to the number scanner — which is how the minority section kept
    # a stale framing under an unflagged figure. Every figure is now a generated
    # token `{{@name=value;fmt;source}}` rendered into the HTML at build time.
    N = len(rows)
    SRC = f"seat_draws.csv, {N:,} simulations"

    def tok(name, value, fmt, source=SRC):
        return f"{{{{@{name}={value};{fmt};{source}}}}}"

    def chance(name, value, source=SRC):
        return tok(name, f"{float(value):.6f}", "chance", source)

    def seats(name, value, source=SRC):
        return tok(name, int(round(float(value))), "int", source)

    def esc(s):
        return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # --- tiles --------------------------------------------------------------
    tiles = [
        (chance("tile.p_alone", p_alone), "One party reaches a majority alone", ""),
        (chance("tile.p_anc_da", anc_da["p"]),
         "ANC + DA have a majority. No other pair of parties reliably reaches one", ""),
        (chance("tile.p_da_largest", p_da_largest), "The DA alone has the most seats", ""),
        (chance("tile.p_anc_largest", p_anc_largest), "The ANC alone has the most seats", ""),
        (chance("tile.p_tied_largest", p_tied_largest),
         "Two or more parties tie for the most seats", ""),
        (chance("tile.p_anc_excessive", p_excessive, "forecast_summary.json p_excessive_by_party"),
         "The ANC triggers the excessive-seats clause",
         "It keeps every ward it wins and gets no list seats; the other parties' list seats shrink. "
         "At least one party triggers it: " + chance("tile.p_excessive_any", summary["p_excessive_any"],
                                                     "forecast_summary.json p_excessive_any")
         + " chance" + (". Beyond the ANC: " + _excl if (_excl := _scq.excessive_by_party(
             summary.get("p_excessive_by_party", {}), NAMES, chance, "tile.p_excessive",
             "forecast_summary.json p_excessive_by_party", exclude=("ANC",))) else "")),
    ]
    tiles_html = "".join(
        f'<div class="stat"><div class="n">{n}<span class="chancew"> chance</span></div>'
        f'<div class="l">{l}{f"<span class=sub>{sub}</span>" if sub else ""}</div></div>'
        for n, l, sub in tiles)
    # (no 'council 270 · majority 136' tile: that is the law, not something the simulations say)

    # --- where the parties land: ordered by median, then mean ----------------
    others = _scq.others_per_draw(args.processed, CHART_PARTIES)
    chart = [(NAMES[p], S[p], p) for p in CHART_PARTIES if p in S]
    chart.sort(key=lambda c: (-np.median(c[1]), -c[1].mean()))
    chart.append(("Others", others, "OTHERS"))
    # THE SITE'S ONE SEAT TABLE (src/seat_table.py), shared with the home page
    # and the published panels of /play/ and /make/. build_play reads these
    # rows back (its `seat_rows`) by their data-code/data-m/-p5/-p95.
    import seat_table
    seat_rows = []
    for name, series, code in chart:
        med, lo, hi = q(series)
        seat_rows.append({"code": code, "name": name,
                          "seats": seats(f"seats.{code}.median", med),
                          "lo": seats(f"seats.{code}.p5", lo),
                          "hi": seats(f"seats.{code}.p95", hi),
                          "m": med, "p5": lo, "p95": hi})
    seats_html = seat_table.table(seat_rows, label="Projected seats by party")

    # --- who can govern ------------------------------------------------------
    means = {p: float(S[p].mean()) for p in parties}
    top = [p for p in sorted(parties, key=lambda q_: -means[q_]) if means[p] >= 0.4]
    nT = len(top)
    _sum_cache: dict[int, np.ndarray] = {}

    def msum(m):
        if m not in _sum_cache:
            tot = np.zeros(N, dtype=int)
            for k in range(nT):
                if m & (1 << k):
                    tot = tot + S[top[k]]
            _sum_cache[m] = tot
        return _sum_cache[m]

    def members_of(m):
        return [top[k] for k in range(nT) if m & (1 << k)]

    def smallest(m, tot):
        ok = tot >= thr
        for p in members_of(m):
            ok &= (tot - S[p]) < thr
        return ok

    from itertools import combinations
    # One simulation in twenty, and at most five parties: at 1% there were 1,049
    # rows (191 even capped at four parties) — unreadable, and a ledger row for
    # every figure in each. At 5% the list is 90 rows and still carries every
    # DA-without-the-ANC option that is ever a smallest majority that often.
    # Presentation, set 2026-09-17; the owner can move it.
    MIN_SMALLEST, MAX_SIZE = 0.05, 5
    cands = {}
    for k in range(2, MAX_SIZE + 1):
        for combo in combinations(range(nT), k):
            m = sum(1 << i for i in combo)
            tot = msum(m)
            s = float(smallest(m, tot).mean())
            win = tot >= thr
            # No passengers (owner, 2026-09-17: "if a coalition can survive the
            # exit of a party, remove the party"). A member whose exit the
            # majority survives in most of the simulations where it governs is
            # a passenger, and the combination without it is the one to show.
            # JUDGED ON THE PRINTED FIGURE (owner, 2026-09-30: "keep as is,
            # just round all numbers, so 49.86 is 50%"). Two rows at 49.86%
            # and 49.95% survival printed "50%" beside a note saying the
            # coalition usually loses them; rounding to the displayed
            # precision first makes the cut agree with what a reader sees.
            carried = win.any() and all(
                round(float(((tot - S[p_]) >= thr)[win].mean()), 2) < 0.5
                for p_ in members_of(m))
            if s >= MIN_SMALLEST and carried:
                cands[m] = s
            else:
                _sum_cache.pop(m, None)

    def label(m):
        return "".join(
            f'<span class="cparty">{"" if i == 0 else chr(43) + " "}'
            f'<span class="pchip sm pc-{p}"></span>'
            f'{NAMES.get(p, p)}</span> '
            for i, p in enumerate(members_of(m)))

    rows_out = []
    for m, s in sorted(cands.items(), key=lambda ms: -float((msum(ms[0]) >= thr).mean())):
        tot = msum(m)
        win = tot >= thr
        key = coalition_key(members_of(m))
        p_major = float(win.mean())
        med_w = int(np.median(tot[win]))
        cushion = med_w - int(np.median(thr))
        stab = min(100.0, max(cushion, 0) / med_w * 100)
        surv = []
        for p in members_of(m):
            left = float(((tot - S[p]) >= thr)[win].mean())
            surv.append(f'<span class="survp"><span class="survn">{NAMES.get(p, p)}</span> '
                        + chance(f"coal.{key}.survive.{p}", left,
                                 f"{SRC}, among those where this combination wins")
                        + "</span>")
        cond = f"{SRC}, among the simulations where this combination wins"
        rows_out.append(
            f'<tr data-parties="{" ".join(members_of(m))}" data-p="{p_major:.4f}">'
            f'<td class="combo">{label(m)}</td>'
            f'<td class="num">{chance(f"coal.{key}.majority", p_major)}</td>'
            f'<td class="num">{seats(f"coal.{key}.seats_when_wins", med_w, cond)}</td>'
            f'<td class="num">+{seats(f"coal.{key}.cushion_when_wins", cushion, cond)}</td>'
            f'<td class="num">{tok(f"coal.{key}.stability", f"{stab / 100:.4f}", "pct0", cond)}</td>'
            f'<td class="surv">{"".join(surv)}</td></tr>')
    govern_html = "\n".join(rows_out)
    govern_parties = [p for p in top if any(p in members_of(m) for m in cands)]
    filter_html = "".join(
        f'<option value="{p}">{NAMES.get(p, p)}</option>' for p in govern_parties)
    untracked = 270 - sum(means.values())
    # The lede carries the finding the table exists to show, with both figures
    # as build-time tokens: the DA's best route without the ANC/EFF/MK, and how
    # many routes the ANC has without the DA.
    def _best(anchor, barred):
        best = 0.0
        for m in cands:
            ps = set(members_of(m))
            if anchor in ps and not (ps & barred):
                best = max(best, float((msum(m) >= thr).mean()))
        return best
    da_best = _best("DA", {"ANC", "EFF", "MK"})
    anc_routes = sum(1 for m in cands
                     if "ANC" in members_of(m) and "DA" not in members_of(m))
    anc_strong = sum(1 for m in cands
                     if "ANC" in members_of(m) and "DA" not in members_of(m)
                     and float((msum(m) >= thr).mean()) > 0.5)
    govern_lede = (
        f'<p class="lede">If the DA rules out the ANC, the EFF and MK, its one realistic '
        f'option is ActionSA and the PA: {chance("govern.da_best_without", da_best)} chance '
        f'they have the numbers. The ANC without the DA has '
        f'{tok("govern.anc_routes", anc_routes, "int")} workable majorities, '
        f'{tok("govern.anc_routes_strong", anc_strong, "int")} of them with a better than '
        f'even chance of reaching {{{{majority}}}} seats. This is arithmetic, not a '
        f'judgement of which deal is likely.</p>')

    govern_note = (
        f"<b>How to read it.</b> Each row is a smallest workable majority: it has the numbers, "
        f"and usually loses them if any one partner leaves. Combinations that a partner leaving "
        f"usually does not break are left out. <b>Governs in</b> is the chance it reaches "
        f"{{{{majority}}}} seats: the share of the {{{{n_draws}}}} simulations in which it does. "
        f"It is not a vote share, or the chance that a deal is made. <b>Seats</b>, <b>cushion</b>, "
        f"<b>stability</b> and <b>if a partner leaves</b> are over the simulations in which it "
        f"governs. Stability is the share of its own councillors who could defect without "
        f"sinking it.")

    # How many parties the simulation carries, and the seats it leaves to the
    # ones it does not. This used to sit under the coalition table, which lists
    # only the large parties — the wrong place for a note about small ones
    # (owner, 2026-09-18). It belongs to the seats chart, where the reader meets
    # the pooled "Others" row and can see the bars do not add to the council.
    band = chance("seats.band", _scq.BAND_SHARE,
                  "scenarios.BAND, the percentiles seat_quantiles reports")
    seats_note = (
        "<b>Others</b> is the council minus the named parties' seats, within each simulation. "
        "Each row is that party's own middle value and "
        f"{band} range across the simulations, so the rows do not add up to the council.")

    # --- minority administrations ---------------------------------------------
    minority_rows = summary["minority"]
    minority_html = "".join(
        f"<tr><td>{esc(m['scenario'])}</td><td class=\"num\">"
        f"{chance('minority.' + re.sub(r'[^A-Za-z0-9]+', '_', m['scenario']).strip('_'), m['p_viable'], 'forecast_summary.json minority')}"
        f"</td></tr>" for m in minority_rows)

    regions = {"TILES": tiles_html, "SEATS": seats_html, "GOVERN": govern_html,
               "GOVERN_LEDE": govern_lede,
               "GOVERN_FILTER": filter_html, "GOVERN_NOTE": govern_note,
               "SEATS_NOTE": seats_note,
               "MINORITY": minority_html}

    # --- claims tested: rendered from content/<city>/claims.toml ----------
    # Claims are data so the newsdesk can propose one as a diff. Verdicts
    # stay human — they require a model run.
    claims_path = Path("content") / args.city / "claims.toml"
    if claims_path.exists():
        with claims_path.open("rb") as fh:
            claims = tomllib.load(fh).get("claim", [])
        boxes = []
        # Figures a claim's "Since then" box may quote, each a generated token.
        # The DA-alone scenario is read from the per-simulation ward results so
        # every clause of the narrative points at simulations that exist.
        import scenarios as _sc
        _detail, _winners, _wards = _sc.load(args.processed)
        _modal = _sc.modal_winners(_winners, _wards)
        _da = _sc.matching(_detail, [("DA", ">=", int(np.median(thr)))])
        _wall = [d for d in _da if sum(1 for _, a, b in _sc.flips(_winners, _modal, d)
                                         if a == "ANC" and b == "DA") >= WALL_FLIPS]
        _odd = [d for d in _da if d not in _wall]
        _sd = "ward_draws.csv + seat_detail_draws.csv"

        def _seats(d, p):
            return _detail[d].get(p, {}).get("seats", 0)
        _anc_alone = float((S["ANC"] >= thr).mean()) if "ANC" in S else 0.0

        def _bloc(exclude):
            """Seats held by every party in the simulation except `exclude` —
            the arithmetic a stated red line leaves behind, not a prediction
            that those parties would ever sit together."""
            return sum(S[p] for p in parties if p not in exclude)
        _no_red = _bloc(("EFF", "MK", "ANC"))
        _anc_side = _bloc(("EFF", "MK", "DA"))
        _three = sum(S[p] for p in ("DA", "ASA", "PA") if p in S)
        _left = sum(S[p] for p in ("ANC", "EFF", "MK") if p in S)
        # the same definition as the tiles above (reweight.largest_party)
        _outright = _lp["outright"]
        since_vals = {
            "anc_alone_share": chance("claim.anc_alone.share", _anc_alone),
            "anc_alone_count": tok("claim.anc_alone.count", int((S["ANC"] >= thr).sum()), "int"),
            "anc_best": tok("claim.anc_alone.best", int(S["ANC"].max()), "int"),
            "anc_median": tok("claim.anc.median", int(np.median(S["ANC"])), "int"),
            "da_median": tok("claim.da.median", int(np.median(S["DA"])), "int"),
            "mk_largest_share": chance("claim.mk_largest.share", _outright["MK"]),
            "mk_median": tok("claim.mk.median", int(np.median(S["MK"])), "int"),
            "mk_p95": tok("claim.mk.p95", int(np.percentile(S["MK"], 95)), "int"),
            "anc_largest_share": chance("claim.anc_largest.share", _outright["ANC"]),
            "da_largest_share": chance("claim.da_largest.share", _outright["DA"]),
            "largest_tied_share": chance("claim.largest_tied.share", _lp["tied"]),
            "da_alone_share": chance("claim.da_alone.share", len(_da) / N),
            "da_alone_count": tok("claim.da_alone.count", len(_da), "int"),
            "n_draws": "{{n_draws}}",
            "wall_count": tok("claim.da_alone.wall_count", len(_wall), "int", _sd),
            "wall_flips": tok("claim.da_alone.wall_flips", WALL_FLIPS, "int",
                              "render_sheet.WALL_FLIPS, the threshold this "
                              "scenario is counted at"),
            "no_red_share": chance("claim.red_lines.no_red_share", float((_no_red >= thr).mean())),
            "no_red_median": tok("claim.red_lines.no_red_median", int(np.median(_no_red)), "int"),
            "three_share": chance("claim.red_lines.three_share", float((_three >= thr).mean())),
            # TWO MEDIANS, AND THEY ANSWER DIFFERENT QUESTIONS. The
            # unconditional one is what this combination holds in a typical
            # simulation; the conditional one is what it holds in the
            # simulations where it actually reaches a majority, which is what
            # the who-can-govern table reports as `seats_when_wins`. They
            # differ by more than 20 seats for DA+ASA+PA, and quoting one
            # against the other — 118 on this page, 144 in the table, both
            # called "median" — is how a reader is told the page contradicts
            # itself. Owner, 2026-09-27: "it can't be 118 seats and 144 seats".
            "three_median": tok("claim.red_lines.three_median", int(np.median(_three)), "int"),
            "three_median_when_wins": tok(
                "claim.red_lines.three_median_when_wins",
                int(np.median(_three[_three >= thr])) if (_three >= thr).any() else 0,
                # SRC, not _sd. The value is a median over `_three`, which
                # is built from `S` — read from seat_draws.csv — while `_sd` is
                # "ward_draws.csv + seat_detail_draws.csv". Its twin
                # `three_median` cites SRC correctly, so the tooltip on one of
                # the pair named a file the figure never touched.
                "int", f"{SRC}, among the simulations where this combination "
                       f"reaches a majority"),
            "anc_side_share": chance("claim.red_lines.anc_side_share", float((_anc_side >= thr).mean())),
            "anc_left_share": chance("claim.anc_routes.left_share", float((_left >= thr).mean())),
            "anc_left_median": tok("claim.anc_routes.left_median", int(np.median(_left)), "int"),
            "grand_share": chance("claim.red_lines.grand_share", float((S["ANC"] + S["DA"] >= thr).mean())),
            "majority": "{{majority}}",
        }
        if _wall:
            # ⛔ A RANGE OVER ONE SIMULATION IS NOT A RANGE. This printed
            # "the ANC falling to 34 – 34 seats" — min and max of a single
            # draw, rendered as an interval. The source line now says how many
            # draws it is over, so a reader can see that "34 – 34" would be one
            # of them, and the claims text asks for the low bound alone when
            # there is only one.
            anc = [_seats(d, "ANC") for d in _wall]
            src = f"{_sd}, over the {len(anc)} simulation{'' if len(anc) == 1 else 's'} where this happens"
            since_vals["wall_anc_low"] = tok("claim.da_alone.wall_anc_low", min(anc), "int", src)
            # `wall_anc_TOP`, not `wall_anc_high`: the latter was retired on
            # 2026-09-27 when the range collapsed to one simulation, and a
            # retired token is not brought back (owner, 2026-09-29). The upper
            # end starts again as a new figure; the old record stays whole.
            since_vals["wall_anc_high"] = tok("claim.da_alone.wall_anc_top", max(anc), "int", src)
            since_vals["wall_anc_span"] = (
                since_vals["wall_anc_low"] if len(anc) == 1
                else f'{since_vals["wall_anc_low"]}–{since_vals["wall_anc_high"]}')
        if len(_odd) == 1:
            d = _odd[0]
            for key, p in (("odd_anc", "ANC"), ("odd_asa", "ASA"), ("odd_eff", "EFF"), ("odd_nfp", "NFP")):
                since_vals[key] = tok(f"claim.da_alone.{key}", _seats(d, p), "int", f"{_sd}, simulation {d}")

        def _fill(text):
            missing = [k for k in re.findall(r"\[\[(\w+)\]\]", text) if k not in since_vals]
            if missing:
                raise SystemExit(f"claims.toml 'since' names {missing}, which render_sheet "
                                 f"cannot compute for today's simulations — rewrite the box")
            return re.sub(r"\[\[(\w+)\]\]", lambda m: since_vals[m.group(1)], text)

        # Claim prose carries computed figures the same way its "Since then" box
        # does: a placeholder the build resolves into a token, never a number a
        # human typed into a quote-testing argument.
        _since = _fill

        for c in claims:
            since_html = ""
            if c.get("since"):
                since_html = ('<aside class="since"><div class="since-h">{{generated_date}}: what the '
                              'model says now</div><p>' + _md(_since(c["since"])) + "</p></aside>")
            steps = "".join(
                f'<li><div class="stepbody">{_md(_fill(step))}</div></li>'
                for step in c.get("steps", []))
            vclass = "vtrue" if c["verdict"].upper() == "TRUE" else "vfalse"
            link = (f'<a href="{c["url"]}" target="_blank" rel="noopener">'
                    f'{c["outlet"]}</a>') if c.get("url") else c.get("outlet", "")
            badge = (f'<span class="verdict {vclass}">'
                     f'{c["verdict"].upper()}</span>')
            ident = (f'<img class="plogo" src="logos/{c["logo"]}.png" alt="" '
                     f'width="44" height="44">' if c.get("logo") else
                     f'<span class="pchip pc-{c["party"]}"></span>')
            boxes.append(
                f'<article class="claim" data-party="{c["party"]}">'
                f'<div class="pubdate">{c["published"]}: Published</div>'
                f'<div class="claim-top">{ident}'
                f'<div class="claim-who"><b>{c.get("party_name", c["party"])}'
                f'</b><span>{c["speaker"]} \u00b7 {link}</span></div>'
                f'{badge}</div>'
                f'<blockquote class="claim-quote">{c["quote"]}'
                f'<span class="q-close">\u201d</span></blockquote>'
                f'<p class="claim-intro">{_md(_fill(c["intro"]))}</p>'
                f'<ol class="claimsteps">{steps}</ol>{since_html}</article>')
        claims_html = ("<!-- __CLAIMS_START__ -->\n    "
                       + "\n    ".join(boxes)
                       + "\n    <!-- __CLAIMS_END__ -->")
        for tgt in PAGES:
            t = tgt.read_text(encoding="utf-8")
            if "__CLAIMS_START__" in t:
                a = t.index("<!-- __CLAIMS_START__ -->")
                b2 = t.index("<!-- __CLAIMS_END__ -->") + len("<!-- __CLAIMS_END__ -->")
                tgt.write_text(t[:a] + claims_html + t[b2:], encoding="utf-8")
        print(f"claims: {len(claims)} box(es) rendered from {claims_path}")

    # two-ballots arithmetic strip: 135 wards + 135 list = 270
    # One SVG per ballot, the segments placed in percent of its width: the
    # geometry is attributes and the colours are party classes, so the page
    # carries no style (owner's sweep, 2026-10-03).
    def bar(items, total, label):
        segs, at = "", 0.0
        for nm, n, code in items:
            if n <= 0: continue
            segs += (f'<rect class="pc-{code}" x="{at / total * 100:.2f}%" y="0" '
                     f'width="{n / total * 100:.2f}%" height="26" '
                     f'data-tip="{nm} — {n} seats"><title>{nm} — {n} seats</title></rect>')
            at += n
        return (f'<div class="ballot"><div class="ballot-h">{label}</div>'
                f'<svg class="ballot-bar" width="100%" height="26" role="img" '
                f'aria-label="{label}">{segs}</svg></div>')

    # Bars must sum exactly as the headline claims (135 + 135 = 270): named
    # parties plus a "Smaller parties" bucket are rounded with largest
    # remainder to the exact bar totals, and list = council − wards so the
    # three bars are mutually consistent by construction.
    def round_to_total(vals: dict[str, float], total: int) -> dict[str, int]:
        floors = {k: int(v) for k, v in vals.items()}
        rem = total - sum(floors.values())
        for k in sorted(vals, key=lambda q: floors[q] - vals[q])[:max(rem, 0)]:
            floors[k] += 1
        return floors

    # ⛔ ONE REAL SIMULATION, NOT A SUMMARY STATISTIC. Medians do not add (the
    # party medians summed to 240 of 270, so "Smaller parties" showed 39 seats).
    # Means do add, but a mean is an outcome no simulation produces: the ANC's
    # mean list seats were 3.85 while its MEDIAN is 0 and 64.3% of simulations
    # give it none — so the bar said "4 list seats" beside a tile saying the
    # clause fires in 64% (owner, 2026-09-17: "can't be both"). A single real
    # simulation adds up exactly AND is something the model actually produced:
    # the one closest to every charted party's median seats.
    OTHER = "__other__"
    detail: dict[int, dict[str, tuple[int, int]]] = {}
    with (args.processed / "seat_detail_draws.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            detail.setdefault(int(r["draw"]), {})[r["party"]] = (
                int(r["ward_seats"]), int(r["list_seats"]))
    import scenarios as _scen
    typical = _scen.typical(S, CHART_PARTIES)
    sim = detail[typical]
    named_codes = [p for p in sorted(sim, key=lambda q_: -sum(sim[q_]))
                   if NAMES.get(p) and CHIPS.get(p) and sum(sim[p]) >= 3]
    ward_n = {p: sim[p][0] for p in named_codes}
    list_n = {p: sim[p][1] for p in named_codes}
    ward_n[OTHER] = sum(w for p, (w, _) in sim.items() if p not in named_codes)
    list_n[OTHER] = sum(l_ for p, (_, l_) in sim.items() if p not in named_codes)
    tot_n = {k: ward_n[k] + list_n[k] for k in ward_n}

    def seg(k):
        return ("Smaller parties", "OTHERS") if k == OTHER else (NAMES[k], k)
    order = named_codes + [OTHER]
    wardsb = [(seg(k)[0], ward_n[k], seg(k)[1]) for k in order if ward_n.get(k, 0) > 0]
    listb = [(seg(k)[0], list_n[k], seg(k)[1]) for k in order if list_n.get(k, 0) > 0]
    totb = [(seg(k)[0], tot_n[k], seg(k)[1]) for k in order if tot_n.get(k, 0) > 0]
    council_n = sum(tot_n.values())

    anc_w, anc_l = sim.get("ANC", (0, 0))
    src_typ = f"seat_detail_draws.csv, simulation {typical}"
    anc_note = (f"In it the ANC wins {tok('ballots.typical.anc_wards', anc_w, 'int', src_typ)} wards "
                f"and gets {tok('ballots.typical.anc_list', anc_l, 'int', src_typ)} list seats"
                + ("; its ward wins exceed its proportional share, so the excessive-seats "
                   "clause gives it no list seats and the other parties' list seats shrink. That "
                   "happens in " if anc_l == 0 else ". The excessive-seats clause removes the ANC's list "
                   "seats in ")
                + chance("ballots.p_anc_excessive", p_excessive,
                         "forecast_summary.json p_excessive_by_party")
                + " of the simulations")
    ballots_caption = (f"The most typical result: of the {{{{n_draws}}}} simulations, the one "
                       f"closest to the middle of every party's range (simulation "
                       f"{tok('ballots.typical.draw', typical, 'int', 'seat_detail_draws.csv')}). "
                       f"It is a single simulation, so its ward and list seats add up to the "
                       f"council exactly. Hover a segment for its seats. {anc_note}. ActionSA, "
                       "with broad support and no stronghold wards, takes almost all its seats "
                       "from the list.")
    assert council_n == int(np.median(council)), (council_n, "typical simulation is not a full council")
    strip = f"""<!-- __BALLOTS_START__ -->
  <details class="rollup" data-band="forecast" open>
    <summary><span class="eyebrow">The arithmetic — two ballots, one council</span>
    <h2>135 wards + 135 list seats = 270</h2></summary>
    <div class="ballots">
      {bar(wardsb, 135, "Ward seats — won race by race")}
      {bar(listb, 135, "+ List seats — topping parties up to their share")}
      {bar(totb, 270, "= The council")}
    </div>
    <figcaption class="ballots-note">{ballots_caption}</figcaption>
  </details>
  <!-- __BALLOTS_END__ -->"""
    for tgt in PAGES:
        s = tgt.read_text(encoding="utf-8")
        if "__BALLOTS_START__" in s:
            a = s.index("<!-- __BALLOTS_START__ -->")
            b2 = s.index("<!-- __BALLOTS_END__ -->") + len("<!-- __BALLOTS_END__ -->")
            tgt.write_text(s[:a] + strip + s[b2:], encoding="utf-8")

    # --- excessive-seats regime comparison (regenerate via ------------------
    # src/overhang_regimes.py, which runs the expand and level counterfactuals
    # and restores the reference outputs)
    REG_PARTIES = ["DA", "ANC", "EFF", "ASA", "MK", "PA", "IFP", "ALJAMAAH"]
    regimes = []
    for key, label, note in (
            ("deduct", "South African law", "fixed 270 — others squeezed"),
            ("expand", "Germany 2000 law", "council grows"),
            ("level", "Germany 2015 law", "council grows &amp; levelled"),
            ("cap", "Germany 2023 law",
             "fixed 270 — wins not seated if not proportional")):
        if key == "deduct":
            summ = summary
            sd = rows
        else:
            sp = args.processed / f"regime_{key}_summary.json"
            dp = args.processed / f"regime_{key}_seat_draws.csv"
            if not (sp.exists() and dp.exists()):
                regimes = []
                break
            summ = json.loads(sp.read_text(encoding="utf-8"))
            with dp.open(encoding="utf-8", newline="") as fh:
                sd = list(csv.DictReader(fh))
        council_med = int(np.median([int(r["council_size"]) for r in sd]))
        thr_med = int(np.median([int(r["threshold"]) for r in sd]))
        meds = {p: int(round(v["median"])) for p, v in summ["parties"].items()}
        regimes.append((label, note, meds, council_med, thr_med))

    if regimes:
        def k_(k, base=""):
            # a rule after the first is set off by a hairline (.rg-k)
            cls = (base + (" rg-k" if k else "")).strip()
            return f' class="{cls}"' if cls else ""
        head = "".join(
            f'<th colspan="2"{k_(k, "rg-h")}>{lab}<br><span class="rg-note">{note}</span></th>'
            for k, (lab, note, *_) in enumerate(regimes))
        sub = "<th></th>" + "".join(
            f'<th{k_(k, "num")}>seats</th><th class="num">share</th>'
            for k in range(len(regimes)))
        cols = ('<colgroup><col class="rg-c0">'
                + '<col class="rg-cn"><col class="rg-cs">' * 4
                + "</colgroup>")

        def _n_for(p, meds, cm):
            return (max(cm - sum(meds.get(q, 0) for q in REG_PARTIES), 0)
                    if p == "__OTH__" else meds.get(p, 0))

        def _delta(val, base, unit=""):
            d = val - base
            if abs(d) < (0.05 if unit else 0.5):
                return ""
            cls = "up" if d > 0 else "dn"
            mag = f"{abs(d):.1f}" if unit else f"{abs(d):.0f}"
            return f'<span class="rd {cls}">{"+" if d > 0 else "−"}{mag}{unit}</span>'

        base_meds, base_cm = regimes[0][2], regimes[0][3]
        body = ""
        for p in REG_PARTIES + ["__OTH__"]:
            code = "OTHERS" if p == "__OTH__" else p
            nm = (f'<span class="pchip pc-{code}"></span>'
                  f'{"Smaller parties" if p == "__OTH__" else NAMES[p]}')
            n0 = _n_for(p, base_meds, base_cm)
            s0 = n0 / base_cm * 100
            cells = ""
            for k, (lab, note, meds, cm, tm) in enumerate(regimes):
                n = _n_for(p, meds, cm)
                ds = "" if k == 0 else _delta(n, n0)
                dp = "" if k == 0 else _delta(n / cm * 100, s0, "pt")
                cells += (f'<td{k_(k, "num")}>{n}{ds}</td>'
                          f'<td class="num rg-s">{n / cm:.1%}{dp}</td>')
            body += f"<tr><td>{nm}</td>{cells}</tr>"
        for row_lab, pick in (("Council size", 3), ("Majority line", 4)):
            cells = "".join(
                f'<td{k_(k, "num")} colspan="2"><b>{rr[pick]}</b></td>'
                for k, rr in enumerate(regimes))
            body += (f'<tr class="rg-sum">'
                     f"<td><b>{row_lab}</b></td>{cells}</tr>")
        regimes_html = (
            "<!-- __REGIMES_START__ -->\n"
            '    <div class="tablewrap"><table class="rg">'
            f"{cols}"
            f'<thead><tr><th></th>{head}</tr><tr>{sub}</tr></thead>'
            f"<tbody>{body}</tbody></table></div>\n"
            "    <!-- __REGIMES_END__ -->")
        for tgt in PAGES:
            s = tgt.read_text(encoding="utf-8")
            if "__REGIMES_START__" in s:
                a = s.index("<!-- __REGIMES_START__ -->")
                b2 = s.index("<!-- __REGIMES_END__ -->") + len("<!-- __REGIMES_END__ -->")
                tgt.write_text(s[:a] + regimes_html + s[b2:], encoding="utf-8")
        print("regimes table:", " · ".join(
            f"{lab}: council {cm}, thr {tm}" for lab, _, _, cm, tm in regimes))

    for tgt in PAGES:
        if not tgt.exists():
            continue
        page = tgt.read_text(encoding="utf-8")
        for name, body in regions.items():
            s, e = f"<!-- __{name}_START__ -->", f"<!-- __{name}_END__ -->"
            if s in page:
                i, j = page.index(s) + len(s), page.index(e)
                page = page[:i] + "\n" + body + "\n" + page[j:]
        tgt.write_text(page, encoding="utf-8")
    print(f"rendered {len(regions)} regions into {args.sheet}: "
          f"{len(rows_out)} coalitions, {len(chart)} party rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
