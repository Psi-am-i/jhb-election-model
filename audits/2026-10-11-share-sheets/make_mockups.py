"""MOCK-UP ONLY: share images and share lines for each article and each claim.

Runs the release tree's real site build into a temporary --out (no --publish,
so no ledger row; the number review lands beside the temporary output), keeps
the token pool the build hands og_pages, builds one card spec per page or
claim with og_pages' own helpers (``_fig``, ``check``, ``verdict_badge``,
``kind_colour``) and draws them with mock-cards.mjs. Writes into this folder
only.

    cd /Users/simondavis/projects/atlas-jhb-site-release
    /Users/simondavis/projects/atlas-jhb-election-model/.venv/bin/python \
        /Users/simondavis/projects/atlas-jhb-election-model/audits/2026-10-11-share-sheets/make_mockups.py
"""
from __future__ import annotations

import html as H
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

REL = Path("/Users/simondavis/projects/atlas-jhb-site-release")
AUD = Path(__file__).resolve().parent
os.chdir(REL)
sys.path.insert(0, str(REL / "src"))

import build_site  # noqa: E402
import og_pages  # noqa: E402

CAP: dict = {}
_orig_share, _orig_pool = build_site.share_images, og_pages.figure_pool


def _share(held, out, published, registry, ctx, articles):
    CAP.update(held=held, articles=articles)
    return _orig_share(held, out, published, registry, ctx, articles)


def _pool(published, registry, ctx):
    pool, records = _orig_pool(published, registry, ctx)
    CAP.update(pool=pool, records=records)
    return pool, records


build_site.share_images, og_pages.figure_pool = _share, _pool
TMP = Path(tempfile.mkdtemp(prefix="og-mock-"))
build_site.main(["--out", str(TMP / "site")])
pool, records = CAP["pool"], CAP["records"]
pages = {o: h for o, _s, _l, h in CAP["held"]}
articles = CAP["articles"]
claims = tomllib.loads((REL / "content/joburg/claims.toml").read_text(encoding="utf-8"))["claim"]

import build_play  # noqa: E402
roster = build_play.roster()


def fig(figures: dict, tok: str) -> str:
    """The string the page printed for ``tok`` (og_pages._fig: refuses an
    unprinted or ambiguous token), recorded under the spec's figures."""
    figures[tok] = og_pages._fig(pool, tok)
    return pool[tok]


def val(tok: str) -> float:
    """The token's value as the page's record holds it: bar geometry only."""
    return float(records[tok]["value"])


def gd(figures):
    return f"Figures as of {fig(figures, 'generated_date')}."


specs, lines = [], []


def line(slug, template, tokens):
    """A share line: {{token}} references, and the same with each resolved to
    the string the page printed, for review."""
    resolved = re.sub(r"\{\{([^}]+)\}\}", lambda m: f"{pool[m.group(1)]}", template)
    review = re.sub(r"\{\{([^}]+)\}\}", lambda m: f"{{{{{m.group(1)}}}}} [{pool.get(m.group(1), 'NO TOKEN')}]", template)
    for t in re.findall(r"\{\{([^}]+)\}\}", template):
        og_pages._fig(pool, t)
    lines.append({"slug": slug, "line": template, "review": review, "resolved": resolved,
                  "chars": len(resolved), "tokens": tokens})


def text_of(s):
    return H.unescape(re.sub(r"<[^>]+>", "", s)).strip()


# ---------------------------------------------------------------- articles
A = {a["href"]: a for a in articles.values()}

# 1. nobody-will-win: the existing seat-ranges spec, unchanged
rows = og_pages.seat_rows(pages["forecast.html"])
s = og_pages.article_spec(A["nobody-will-win"], pool, rows=rows)
s.update(slug="article-nobody-will-win", page="nobody-will-win.html")
specs.append(s)
line(s["slug"], "Chance any one party wins a majority of Johannesburg's council: {{p_alone}}. "
     "The ANC's middle is {{seats.ANC.median}} seats, the DA's {{seats.DA.median}}; a majority is {{majority}}.",
     ["p_alone", "seats.ANC.median", "seats.DA.median", "majority"])

# 2. nobody-catches-the-votes: the two blocs' vote losses, one scale
f: dict = {}
a = A["nobody-catches-the-votes"]
anc, da = fig(f, "bloc_leak_votes"), fig(f, "hist_da_bloc_change_votes")
s = {"layout": "article", "mock": "bars", "slug": "article-nobody-catches-the-votes",
     "page": "nobody-catches-the-votes.html", "headline": a["title"], "figures": f,
     "lead": "Votes lost, ANC bloc and DA bloc",
     "chart": {"scale": val("bloc_leak_votes"), "pitch": 80,
               "rows": [{"label": "ANC bloc", "value": anc, "v": val("bloc_leak_votes"), "colour": roster["ANC"]["colour"]},
                        {"label": "DA bloc", "value": da, "v": val("hist_da_bloc_change_votes"), "colour": roster["DA"]["colour"]}],
               "note": "Votes lost between the 2019 national and 2021 local elections"},
     "date_line": f"Published {og_pages._long(a['date'])}.",
     "alt": f"{a['title']}. Votes lost between the 2019 national and 2021 local elections: ANC bloc {anc}, DA bloc {da}."}
specs.append(s)
line(s["slug"], "Between 2019 and 2021 the ANC bloc in Johannesburg shed {{bloc_leak_votes}} votes. "
     "The DA bloc lost {{hist_da_bloc_change_votes}} over the same period. The ANC's lost votes became abstention.",
     ["bloc_leak_votes", "hist_da_bloc_change_votes"])

# 3. minority-administrations: the page's table, as bars, candidates in
# alphabetical order (STYLE 7), page order within a candidate
f = {}
a = A["minority-administrations"]
html = pages["minority-administrations.html"]
trs = re.findall(r'<tr><td>([^<]+)</td><td class="num"><span class="mstat"[^>]*data-token="([^"]+)"', html)
trs.sort(key=lambda r: r[0].split()[0])
s = {"layout": "article", "mock": "bars", "slug": "article-minority-administrations",
     "page": "minority-administrations.html", "headline": a["title"], "figures": f,
     "lead": "Chance a minority mayor is elected",
     "chart": {"scale": 1.0, "rows": [{"label": text_of(lab), "value": fig(f, tok), "v": val(tok),
                                        "colour": roster[lab.split()[0]]["colour"]} for lab, tok in trs],
               "note": "Candidate, and who votes against; everyone else abstains"},
     "date_line": f"Published {og_pages._long(a['date'])}. {gd(f)}",
     "alt": a["title"] + ". " + "; ".join(f"{text_of(l)}: {pool[t]}" for l, t in trs) + "."}
specs.append(s)
line(s["slug"], "Abstention can elect a minority mayor. Opposed only by the DA, an ANC candidate wins: "
     "{{minority.ANC_minority_only_DA_opposes}} chance. Opposed only by the ANC, a DA candidate: "
     "{{minority.DA_minority_only_ANC_opposes_2021_pattern}}.",
     ["minority.ANC_minority_only_DA_opposes", "minority.DA_minority_only_ANC_opposes_2021_pattern"])

# 4. if-the-law-were-german: the page's regimes table (render_sheet writes it
# from regime_*_summary.json; NOT tokens, so `figures` stays empty and the
# image's numbers are unledgered: BRIEF, "Could not source")
a = A["if-the-law-were-german"]
html = pages["if-the-law-were-german.html"]
tbl = html[html.find('<table class="rg"'):html.find("</table>", html.find('<table class="rg"'))]
labels = [text_of(m) for m in re.findall(r'<th colspan="2" class="rg-h[^"]*">([^<]+)<br>', tbl)]
body = {}
for tr in re.findall(r"<tr[^>]*>([\s\S]*?)</tr>", tbl.split("<tbody>")[1]):
    cells = [text_of(re.sub(r'<span class="rd[^"]*">[^<]*</span>', "", c)) for c in re.findall(r"<td[^>]*>([\s\S]*?)</td>", tr)]
    body[cells[0]] = cells[1:]
seats = lambda name, k: body[name][2 * k]  # noqa: E731  (seats, share alternate)
council, maj = body["Council size"], body["Majority line"]
grows = max(int(c) for c in council)
s = {"layout": "article", "mock": "councils", "slug": "article-if-the-law-were-german",
     "page": "if-the-law-were-german.html", "headline": a["title"], "figures": {},
     "lead": "One set of votes, four councils",
     "chart": {"scale": grows,
               "rows": [{"label": lab, "council": int(council[k]), "council_text": council[k],
                         "majority": int(maj[k]),
                         "parts": [{"v": int(seats(roster[c]["name"], k)), "colour": roster[c]["colour"]}
                                   for c in ("ANC", "DA")]} for k, lab in enumerate(labels)],
               "key": [{"label": roster[c]["name"], "colour": roster[c]["colour"]} for c in ("ANC", "DA")]
                      + [{"label": "Other parties", "colour": "#333833"}],
               "note": "Median seats; the tick is each council's majority line"},
     "date_line": f"Published {og_pages._long(a['date'])}.",
     "alt": a["title"] + ". " + "; ".join(f"{lab}: council {council[k]}, ANC {seats(roster['ANC']['name'], k)}, DA {seats(roster['DA']['name'], k)}"
                                          for k, lab in enumerate(labels)) + "."}
specs.append(s)
lines.append({"slug": s["slug"], "tokens": [],
              "line": "The same simulated votes under four seat laws. Ours keeps the council at "
                      "{{regime.deduct.council}} seats; Germany's 2015 law grows it to {{regime.level.council}} "
                      "so every party's seats match its vote.",
              "review": "PROPOSED TOKENS, none exist: regime.deduct.council [" + council[0] + "], regime.level.council ["
                        + council[2] + "] (read from the rendered table)",
              "resolved": f"The same simulated votes under four seat laws. Ours keeps the council at {council[0]} seats; "
                          f"Germany's 2015 law grows it to {council[2]} so every party's seats match its vote."})
lines[-1]["chars"] = len(lines[-1]["resolved"])

# 5. laingsburg-2021: the live figures (not the pinned pub0831_* ones)
f = {}
a = A["laingsburg-2021"]
s = {"layout": "article", "mock": "meter", "slug": "article-laingsburg-2021",
     "page": "laingsburg-2021.html",
     # the page's own <h1>, as a proposed og_headline (articles.toml `title` is "Laingsburg, 2021")
     "headline": text_of(re.search(r"<h1[^>]*>([^<]+)</h1>", pages["laingsburg-2021.html"]).group(1)),
     "figures": f, "lead": "",
     "chart": {"value": fig(f, "p_excessive_anc"), "v": val("p_excessive_anc"),
               "label": "Chance the clause fires for the ANC in Johannesburg",
               "colour": roster["ANC"]["colour"],
               "rows": [{"label": "ANC wards won, middle", "value": fig(f, "anc_ward_median")},
                        {"label": "ANC seat entitlement, middle", "value": fig(f, "anc_entitlement")}]},
     "date_line": f"Published {og_pages._long(a['date'])}. {gd(f)}"}
s["alt"] = (f"{s['headline']}. Chance the clause fires for the ANC in Johannesburg: {pool['p_excessive_anc']}. "
            f"ANC wards won, middle: {pool['anc_ward_median']}; seat entitlement: {pool['anc_entitlement']}.")
specs.append(s)
line(s["slug"], "Johannesburg's excessive-seats clause has fired once before, in Laingsburg in 2021. "
     "Chance it fires for the ANC in Johannesburg in November: {{p_excessive_anc}}.", ["p_excessive_anc"])

# ---------------------------------------------------------------- claims
s = og_pages.claims_spec(pages["claims.html"], claims, headline=build_site.ARTEFACTS["claims.html"][2])
s.update(slug="claims-page", page="claims.html")
specs.append(s)
from datetime import datetime  # noqa: E402
latest = max(claims, key=lambda c: datetime.strptime(c["published"], "%d %B %Y"))
line("claims-page", "What the parties say about Johannesburg's council vote, each claim tested against "
     "the forecast and given a verdict.", [])

# The [[name]] -> token map, read from render_sheet's one definition of it.
src = (REL / "src/render_sheet.py").read_text(encoding="utf-8")
NAME = dict(re.findall(r'"(\w+)": (?:chance|tok)\(\s*"([\w.]+)"', src))

# Per claim: proposed `slug` (no digits: the number scan reads content="..."
# attributes, og_pages' image-name rule), proposed `quote_short`, and the
# figure the verdict rests on. These three are the proposed claims.toml fields.
PROPOSED = {
    "490,000 DA voters would win the city outright": {
        "slug": "da-turnout-majority", "quote_short": None,
        "figure": ("claim_half_surged", "half the votes cast if her voters turn out; she names {{claim_zille_votes}}"),
        "share": "Helen Zille: {{claim_zille_votes}} DA voters would win the DA a majority. If they all vote, the "
                 "total rises and half of it is {{claim_half_surged}}. Verdict: FALSE."},
    "The ANC can govern Johannesburg alone again": {
        "slug": "anc-absolute-authority",
        "quote_short": "We can only be able to do so if the people of greater Johannesburg give their "
                       "organisation, the ANC, absolute authority",
        "figure": ("claim.anc_alone.share", "chance the ANC wins a council majority alone"),
        "share": "Dickson Masemola asks for the ANC to have absolute authority in Johannesburg. Chance it wins "
                 "a council majority alone: {{claim.anc_alone.share}}. Verdict: NEAR IMPOSSIBLE."},
    "MK will be the biggest party in the city": {
        "slug": "mk-biggest-party",
        "quote_short": "According to us, we are going to be the biggest party in the city",
        "figure": ("claim.mk_largest.share", "chance MK wins the most seats"),
        "share": "Bongani Baloyi says MK will be the biggest party in Johannesburg. Chance MK wins the most "
                 "seats: {{claim.mk_largest.share}}. Verdict: EXTREMELY UNLIKELY."},
    "A majority without the ANC, the EFF and MK": {
        "slug": "da-coalition-red-lines",
        "quote_short": "We won't go into a coalition with MK, and we will not go into coalition with the EFF",
        "figure": ("claim.red_lines.no_red_share", "chance of a council majority without the ANC, the EFF and MK"),
        "share": "Helen Zille rules out coalitions with the EFF and MK. Chance of a council majority without "
                 "the ANC, the EFF and MK: {{claim.red_lines.no_red_share}}. Verdict: VERY LIKELY."},
    "The DA cannot win Joburg without Soweto": {
        "slug": "asa-soweto", "quote_short": None,
        "figure": ("claim.soweto.realistic_given_none",
                   "chance the DA governs with ActionSA and the PA, or the ANC, if it wins no Soweto ward"),
        "share": "Herman Mashaba: the DA cannot win Joburg without Soweto. If it wins no Soweto ward, chance "
                 "the DA governs with ActionSA and the PA or the ANC: {{claim.soweto.realistic_given_none}}. "
                 "Verdict: VERY LIKELY."},
}
for c in claims:
    p = PROPOSED[c["label"]]
    f = {}
    tok, label = p["figure"]
    label = re.sub(r"\{\{([^}]+)\}\}", lambda m: fig(f, m.group(1)), label)
    logo = REL / "site" / "logos" / f"{c.get('logo', c['party'])}.png"
    when = (f"Tested {c['published']}. Figures from that test."
            if records[tok].get("dated") else f"Tested {c['published']}. {gd(f)}")
    s = {"layout": "claims", "mock": "claim", "slug": "claim-" + p["slug"], "page": "claims.html",
         "quote": " ".join((p["quote_short"] or c["quote"]).split()), "quote_cut": bool(p["quote_short"]),
         "speaker": c["speaker"].split(",")[0], "party": roster[c["party"]]["name"], "outlet": c["outlet"],
         "code": c["party"], "colour": roster[c["party"]]["colour"],
         "logo": logo.name if logo.is_file() else None,
         "badge": og_pages.stamp_path(og_pages.verdict_badge(c["verdict"])), "verdict": c["verdict"],
         "figure": {"value": fig(f, tok), "label": label, "token": tok}, "figures": f, "date_line": when}
    s["alt"] = (f"{s['speaker']}, {s['party']}: “{s['quote']}” Verdict: {c['verdict']}. "
                f"{s['figure']['value']}: {label}.")
    specs.append(s)
    line(s["slug"], p["share"], re.findall(r"\{\{([^}]+)\}\}", p["share"]))

# ---------------------------------------------------------------- draw
for s in specs:
    og_pages.check(s)
for L in lines:
    if L["chars"] > 200:
        raise SystemExit(f"{L['slug']}: share line is {L['chars']} characters")
(AUD / "specs.json").write_text(json.dumps(specs, ensure_ascii=False, indent=1), encoding="utf-8")
(AUD / "share-lines.json").write_text(json.dumps(lines, ensure_ascii=False, indent=1), encoding="utf-8")
run = subprocess.run(["node", str(AUD / "mock-cards.mjs"), str(AUD / "specs.json"), str(AUD)],
                     capture_output=True, text=True)
if run.returncode:
    raise SystemExit(run.stderr)
manifest = json.loads(run.stdout)

from PIL import Image  # noqa: E402
names = [manifest[s["slug"]] for s in specs]
cols, tw, th, pad = 3, 600, 315, 12
rows_n = -(-len(names) // cols)
sheet = Image.new("RGB", (cols * (tw + pad) + pad, rows_n * (th + pad) + pad), (40, 44, 41))
for k, n in enumerate(names):
    im = Image.open(AUD / n).convert("RGB").resize((tw, th), Image.LANCZOS)
    sheet.paste(im, (pad + (k % cols) * (tw + pad), pad + (k // cols) * (th + pad)))
sheet.save(AUD / "contact-sheet.png")
print(json.dumps(manifest, indent=1))
for L in lines:
    print(L["chars"], L["slug"], L["resolved"])
