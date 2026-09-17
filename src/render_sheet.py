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
NAMES = {
    "DA": "DA", "ANC": "ANC", "EFF": "EFF", "MK": "MK Party", "ASA": "ActionSA",
    "PA": "PA", "IFP": "IFP", "RISE": "Rise Mzansi", "VFPLUS": "VF+",
    "ACDP": "ACDP", "ALJAMAAH": "Al Jama-ah", "ENTRANT": "New entrant",
    "SOUTH_AFRICAN_COMMUNIST_PARTY": "SACP", "BOSA": "BOSA",
    "ALL_CITIZENS_PARTY": "All Citizens Party",
}
CHART_PARTIES = ["DA", "ANC", "EFF", "ASA", "MK", "PA", "IFP", "RISE",
                 "ALJAMAAH", "ENTRANT"]

ALLIANCE_8 = ("DA", "ASA", "PA", "IFP", "VFPLUS", "ACDP", "RISE", "ALJAMAAH")


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

    def q(series):
        return (int(round(np.median(series))), int(round(np.percentile(series, 5))),
                int(round(np.percentile(series, 95))))

    def coalition(*members):
        total = sum(S[p] for p in members if p in S)
        med, lo, hi = q(total)
        return {"p": round(float((total >= thr).mean()), 4),
                "med": med, "lo": lo, "hi": hi}

    # largest party, and whether anyone ever gets to govern alone
    stack = np.stack([S[p] for p in parties])
    largest = stack.argmax(axis=0)
    p_da_largest = float((np.array(parties)[largest] == "DA").mean())
    p_anc_largest = float((np.array(parties)[largest] == "ANC").mean())
    p_alone = float((stack.max(axis=0) >= thr).mean())
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
         "ANC + DA have a majority — the only two-party combination that reliably "
         "reaches one", ""),
        (chance("tile.p_da_largest", p_da_largest), "The DA is the largest single party", ""),
        (chance("tile.p_anc_largest", p_anc_largest), "The ANC is the largest single party", ""),
        (chance("tile.p_anc_excessive", p_excessive, "forecast_summary.json p_excessive_by_party"),
         "The ANC triggers the excessive-seats clause",
         "Keeps every ward it wins, takes zero list seats — everyone else squeezed"),
    ]
    tiles_html = "".join(
        f'<div class="stat"><div class="n">{n}<span class="chancew"> of simulations</span></div>'
        f'<div class="l">{l}{f"<span class=sub>{sub}</span>" if sub else ""}</div></div>'
        for n, l, sub in tiles)
    # (no 'council 270 · majority 136' tile: that is the law, not something the simulations say)

    # --- where the parties land: ordered by median, then mean ----------------
    others = sum(S[p] for p in parties if p not in CHART_PARTIES)
    chart = [(NAMES[p], CHIPS[p], S[p], p) for p in CHART_PARTIES if p in S]
    chart.sort(key=lambda c: (-np.median(c[2]), -c[2].mean()))
    chart.append(("Others", "#8b918b", others, "OTHERS"))
    MAX = 125
    seats_html = ""
    for name, chip, series, code in chart:
        med, lo, hi = q(series)
        seats_html += (
            f'<div class="row"><div class="pname"><span class="chip" '
            f'style="background:{chip}"></span>{name}</div>'
            f'<div class="track"><span class="band" style="left:{lo / MAX * 100:.2f}%;'
            f'width:{(hi - lo) / MAX * 100:.2f}%"></span><span class="med" '
            f'style="left:calc({med / MAX * 100:.2f}% - 1.5px)"></span></div>'
            f'<div class="val"><b>{seats(f"seats.{code}.median", med)}</b> '
            f'<span style="color:var(--ink-3)">{seats(f"seats.{code}.p5", lo)}–'
            f'{seats(f"seats.{code}.p95", hi)}</span></div></div>')

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
            carried = win.any() and all(
                float(((tot - S[p_]) >= thr)[win].mean()) < 0.5 for p_ in members_of(m))
            if s >= MIN_SMALLEST and carried:
                cands[m] = s
            else:
                _sum_cache.pop(m, None)

    def label(m):
        return " + ".join(
            f'<span class="chip" style="background:{CHIPS.get(p, "#8b918b")};display:inline-block;'
            f'width:8px;height:8px;border-radius:2px;margin-right:4px"></span>{NAMES.get(p, p)}'
            for p in members_of(m))

    rows_out = []
    for m, s in sorted(cands.items(), key=lambda ms: -float((msum(ms[0]) >= thr).mean())):
        tot = msum(m)
        win = tot >= thr
        key = "+".join(members_of(m))
        p_major = float(win.mean())
        med_w = int(np.median(tot[win]))
        cushion = med_w - int(np.median(thr))
        stab = min(100.0, max(cushion, 0) / med_w * 100)
        surv = []
        for p in members_of(m):
            left = float(((tot - S[p]) >= thr)[win].mean())
            surv.append(f"{NAMES.get(p, p)} leaves: majority holds in "
                        + chance(f"coal.{key}.survive.{p}", left,
                                 f"{SRC}, among those where this combination wins")
                        + " of simulations")
        cond = f"{SRC}, among the simulations where this combination wins"
        rows_out.append(
            f'<tr data-parties="{" ".join(members_of(m))}" data-p="{p_major:.4f}">'
            f"<td>{label(m)}</td>"
            f'<td class="num">{chance(f"coal.{key}.majority", p_major)}</td>'
            f'<td class="num">{seats(f"coal.{key}.seats_when_wins", med_w, cond)}</td>'
            f'<td class="num">+{seats(f"coal.{key}.cushion_when_wins", cushion, cond)}</td>'
            f'<td style="font-size:12px">{tok(f"coal.{key}.stability", f"{stab / 100:.4f}", "pct0", cond)}'
            f" of its councillors could defect</td>"
            f'<td style="font-size:12px">{"".join(f"<div>{s_}</div>" for s_ in surv)}</td></tr>')
    govern_html = "\n".join(rows_out)
    govern_parties = [p for p in top if any(p in members_of(m) for m in cands)]
    filter_html = "".join(
        f'<option value="{p}">{NAMES.get(p, p)}</option>' for p in govern_parties)
    untracked = 270 - sum(means.values())
    govern_note = (
        f"Every combination listed is a smallest workable majority in at least 1 in 20 of the "
        f"{{{{n_draws}}}} simulations: it has the numbers, and loses them if any one partner leaves. "
        f"A partner the majority can do without in most of the simulations where it governs is a "
        f"passenger, and such combinations are left out — the list shows the version without it. "
        f"The percentage is the share of simulations in which it can govern — not a vote share, "
        f"and not the chance the deal is made. Seats, cushion, stability and survivability are "
        f"measured only over the simulations in which it governs. The simulations track "
        f"{tok('govern.tracked_parties', nT, 'int')} parties individually; the rest hold "
        f"{tok('govern.untracked_seats', f'{untracked:.2f}', 'int')} seats on average and are left "
        f"out of every combination.")

    # --- minority administrations ---------------------------------------------
    minority_rows = summary["minority"]
    minority_html = "".join(
        f"<tr><td>{esc(m['scenario'])}</td><td class=\"num\">"
        f"{chance('minority.' + re.sub(r'[^A-Za-z0-9]+', '_', m['scenario']).strip('_'), m['p_viable'], 'forecast_summary.json minority')}"
        f"</td></tr>" for m in minority_rows)

    regions = {"TILES": tiles_html, "SEATS": seats_html, "GOVERN": govern_html,
               "GOVERN_FILTER": filter_html, "GOVERN_NOTE": govern_note,
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
                                         if a == "ANC" and b == "DA") >= 30]
        _odd = [d for d in _da if d not in _wall]
        _sd = "ward_draws.csv + seat_detail_draws.csv"

        def _seats(d, p):
            return _detail[d].get(p, {}).get("seats", 0)
        since_vals = {
            "da_alone_share": chance("claim.da_alone.share", len(_da) / N),
            "da_alone_count": tok("claim.da_alone.count", len(_da), "int"),
            "n_draws": "{{n_draws}}",
            "wall_count": tok("claim.da_alone.wall_count", len(_wall), "int", _sd),
        }
        if _wall:
            anc = [_seats(d, "ANC") for d in _wall]
            since_vals["wall_anc_low"] = tok("claim.da_alone.wall_anc_low", min(anc), "int", _sd)
            since_vals["wall_anc_high"] = tok("claim.da_alone.wall_anc_high", max(anc), "int", _sd)
        if len(_odd) == 1:
            d = _odd[0]
            for key, p in (("odd_anc", "ANC"), ("odd_asa", "ASA"), ("odd_eff", "EFF"), ("odd_nfp", "NFP")):
                since_vals[key] = tok(f"claim.da_alone.{key}", _seats(d, p), "int", f"{_sd}, simulation {d}")

        def _since(text):
            missing = [k for k in re.findall(r"\[\[(\w+)\]\]", text) if k not in since_vals]
            if missing:
                raise SystemExit(f"claims.toml 'since' names {missing}, which render_sheet "
                                 f"cannot compute for today's simulations — rewrite the box")
            return re.sub(r"\[\[(\w+)\]\]", lambda m: since_vals[m.group(1)], text)

        for c in claims:
            since_html = ""
            if c.get("since"):
                since_html = ('<aside class="since"><div class="since-h">{{generated_date}}: what the '
                              'model says now</div><p>' + _md(_since(c["since"])) + "</p></aside>")
            steps = "".join(
                f'<li><div class="stepbody">{_md(step)}</div></li>'
                for step in c.get("steps", []))
            vclass = "vtrue" if c["verdict"].upper() == "TRUE" else "vfalse"
            link = (f'<a href="{c["url"]}" target="_blank" rel="noopener">'
                    f'{c["outlet"]}</a>') if c.get("url") else c.get("outlet", "")
            badge = (f'<span class="verdict {vclass}">'
                     f'{c["verdict"].upper()}</span>')
            ident = (f'<img class="plogo" src="logos/{c["logo"]}.png" alt="" '
                     f'width="44" height="44">' if c.get("logo") else
                     f'<span class="chip" style="background:{c["chip"]}"></span>')
            boxes.append(
                f'<article class="claim" data-party="{c["party"]}">'
                f'<div class="pubdate">{c["published"]}: Published</div>'
                f'<div class="claim-top">{ident}'
                f'<div class="claim-who"><b>{c.get("party_name", c["party"])}'
                f'</b><span>{c["speaker"]} \u00b7 {link}</span></div>'
                f'{badge}</div>'
                f'<blockquote class="claim-quote">{c["quote"]}'
                f'<span class="q-close">\u201d</span></blockquote>'
                f'<p class="claim-intro">{_md(c["intro"])}</p>'
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
    def bar(items, total, label):
        segs = ""
        for nm, n, col in items:
            if n <= 0: continue
            segs += (f'<div data-tip="{nm} — {n} seats" title="{nm} — {n} seats" style="width:{n/total*100:.2f}%;'
                     f'background:{col}"></div>')
        return (f'<div style="display:flex;flex-direction:column;gap:4px">'
                f'<div style="font:650 10.5px var(--sans, sans-serif);letter-spacing:.1em;'
                f'text-transform:uppercase;color:var(--ink-3)">{label}</div>'
                f'<div style="display:flex;height:26px;border-radius:3px;overflow:hidden">{segs}</div></div>')

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
        return ("Smaller parties", "#8b918b") if k == OTHER else (NAMES[k], CHIPS[k])
    order = named_codes + [OTHER]
    wardsb = [(seg(k)[0], ward_n[k], seg(k)[1]) for k in order if ward_n.get(k, 0) > 0]
    listb = [(seg(k)[0], list_n[k], seg(k)[1]) for k in order if list_n.get(k, 0) > 0]
    totb = [(seg(k)[0], tot_n[k], seg(k)[1]) for k in order if tot_n.get(k, 0) > 0]
    council_n = sum(tot_n.values())

    anc_w, anc_l = sim.get("ANC", (0, 0))
    src_typ = f"seat_detail_draws.csv, simulation {typical}"
    anc_note = (f"In it the ANC wins {tok('ballots.typical.anc_wards', anc_w, 'int', src_typ)} wards "
                f"and gets {tok('ballots.typical.anc_list', anc_l, 'int', src_typ)} list seats"
                + (" — its ward wins already exceed its proportional share, so the excessive-seats "
                   "clause gives it no list seats and everyone else's list seats shrink to fit. That "
                   "happens in " if anc_l == 0 else ". The excessive-seats clause strips the ANC's list "
                   "seats in ")
                + chance("ballots.p_anc_excessive", p_excessive,
                         "forecast_summary.json p_excessive_by_party")
                + " of the simulations")
    ballots_caption = (f"These bars are one real simulation — number "
                       f"{tok('ballots.typical.draw', typical, 'raw', 'seat_detail_draws.csv')}, "
                       f"the one closest to every party's median — so the three add up exactly. "
                       f"Hover a segment for its seats. {anc_note}. ActionSA, with broad support but "
                       "no stronghold wards, lives almost wholly on the list. Two opposite ways of "
                       "turning votes into seats, in one city.")
    assert council_n == int(np.median(council)), (council_n, "typical simulation is not a full council")
    strip = f"""<!-- __BALLOTS_START__ -->
  <details class="rollup" data-band="forecast" open>
    <summary><span class="eyebrow">The arithmetic — two ballots, one council</span>
    <h2>135 wards + 135 list seats = 270</h2></summary>
    <div style="display:flex;flex-direction:column;gap:14px">
      {bar(wardsb, 135, "Ward seats — won race by race")}
      {bar(listb, 135, "+ List seats — topping parties up to their share")}
      {bar(totb, 270, "= The council")}
    </div>
    <figcaption>{ballots_caption}</figcaption>
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
            ("expand", "Germany 2000", "council grows"),
            ("level", "Germany 2015", "council grows &amp; levelled"),
            ("cap", "Germany 2023",
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
        head = "".join(
            f'<th colspan="2" style="text-align:center'
            + (';border-left:1px solid var(--rule-soft)' if k else "")
            + f'">{lab}<br><span style="font-weight:400;color:var(--ink-3)">{note}</span></th>'
            for k, (lab, note, *_) in enumerate(regimes))
        sub = "<th></th>" + "".join(
            f'<th class="num"'
            + (f' style="border-left:1px solid var(--rule-soft)"' if k else "")
            + '>seats</th><th class="num">share</th>'
            for k in range(len(regimes)))
        cols = ('<colgroup><col style="width:15%">'
                + '<col style="width:9.5%"><col style="width:11.75%">' * 4
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
            chip = "#8b918b" if p == "__OTH__" else CHIPS[p]
            nm = (f'<span class="chip" style="background:{chip};display:inline-block;'
                  f'width:9px;height:9px;border-radius:2px;margin-right:6px"></span>'
                  f'{"Smaller parties" if p == "__OTH__" else NAMES[p]}')
            n0 = _n_for(p, base_meds, base_cm)
            s0 = n0 / base_cm * 100
            cells = ""
            for k, (lab, note, meds, cm, tm) in enumerate(regimes):
                n = _n_for(p, meds, cm)
                ds = "" if k == 0 else _delta(n, n0)
                dp = "" if k == 0 else _delta(n / cm * 100, s0, "pt")
                gl = ';border-left:1px solid var(--rule-soft)' if k else ""
                cells += (f'<td class="num" style="white-space:nowrap{gl}">{n}{ds}</td>'
                          f'<td class="num" style="color:var(--ink-3);white-space:nowrap">'
                          f'{n / cm:.1%}{dp}</td>')
            body += f"<tr><td>{nm}</td>{cells}</tr>"
        for row_lab, pick in (("Council size", 3), ("Majority line", 4)):
            cells = "".join(
                f'<td class="num" colspan="2"'
                + (' style="border-left:1px solid var(--rule-soft)"' if k else "")
                + f'><b>{rr[pick]}</b></td>'
                for k, rr in enumerate(regimes))
            body += (f'<tr style="border-top:1px solid var(--rule)">'
                     f"<td><b>{row_lab}</b></td>{cells}</tr>")
        regimes_html = (
            "<!-- __REGIMES_START__ -->\n"
            '    <div class="tablewrap"><table style="table-layout:fixed;min-width:820px">'
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
