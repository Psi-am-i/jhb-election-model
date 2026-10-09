"""Draw forecast and result frames with render_map's own functions; assemble GIFs.

Usage: render_frames.py SCRATCH OUTDIR   (cwd = repository root)
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

REPO = Path("/Users/simondavis/projects/atlas-jhb-election-model")
sys.path.insert(0, str(REPO / "src"))
import render_map as RM
import build_play
import render_sheet

SCR = Path(sys.argv[1])
OUT = Path(sys.argv[2])
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
GEO = {"2011": "wards2011_JHB", "2016": "wards2016_JHB", "2021": "wards2020_JHB",
       "2026": "wards2026_JHB"}
ROSTER = build_play.roster()
fallback = set()


def short(w: str) -> str:
    # render_map.main's own normalisation of an 8-digit WardID
    w = str(w).strip().lstrip("0")
    return w[-3:].lstrip("0") if len(w) > 3 else w


def colour(p):
    if p in ROSTER:
        return ROSTER[p]["colour"]
    fallback.add(p)
    return render_sheet.OTHER_CHIP


def pname(p):
    return ROSTER[p]["name"] if p in ROSTER else build_play.reader_name(p)


def read_probs(path):
    with open(path, newline="") as fh:
        return {short(r["ward"]): dict(r, ward=short(r["ward"])) for r in csv.DictReader(fh)}


def geometry(year, probs_path):
    """render_map.main, every output redirected to scratch; returns its paths JSON."""
    d = SCR / f"geo_{year}"
    d.mkdir(exist_ok=True)
    dummy = d / "dummy.html"
    dummy.write_text(f"{RM.MARK_START}\n{RM.MARK_END}\n")
    pj = d / "ward_paths.json"
    RM.main(["--geo", str(REPO / f"data/raw/geo/{GEO[year]}.geojson"),
             "--probs", str(probs_path), "--paths-out", str(pj),
             "--into", str(dummy), "--city", "joburg"])
    return json.loads(pj.read_text())


FONT = REPO / "site/fonts"
CSS = f"""
@font-face{{font-family:Plex;src:url('file://{FONT}/IBMPlexSans-Regular-Latin1.woff2');font-weight:400}}
@font-face{{font-family:Plex;src:url('file://{FONT}/IBMPlexSans-SemiBold-Latin1.woff2');font-weight:600}}
@font-face{{font-family:PlexMono;src:url('file://{FONT}/IBMPlexMono-SemiBold-Latin1.woff2');font-weight:600}}
:root{{--paper:#fbfbfa;--ink:#1a1d1b;--ink-3:#6b716c}}
html,body{{margin:0;background:var(--paper);color:var(--ink);font-family:Plex,sans-serif}}
.frame{{width:WIDTHpx;padding:14px 14px 10px;box-sizing:border-box}}
.panels{{display:flex;gap:14px}}
.panel{{flex:1;min-width:0}}
.yr{{font:600 34px PlexMono,monospace;line-height:1}}
.lbl{{font-size:15px;margin:4px 0 6px;color:var(--ink)}}
svg{{width:100%;height:auto;display:block}}
.maplabel{{font:600 11px Plex,sans-serif;letter-spacing:.08em;text-transform:uppercase;fill:#2b2f2c;opacity:.75}}
.mapnorth{{font:600 11px PlexMono,monospace;fill:var(--ink-3)}}
.key{{font-size:12.5px;line-height:1.5;color:var(--ink);margin-top:4px}}
.chip{{display:inline-block;width:11px;height:11px;border-radius:2px;vertical-align:-1px;margin-right:4px}}
.k{{margin-right:10px;white-space:nowrap}}
.note{{color:var(--ink-3);font-size:12px}}
.empty{{display:flex;align-items:center;justify-content:center;border:1px dashed #c9ccc6;
       color:var(--ink-3);font-size:15px;text-align:center;padding:0 20px;box-sizing:border-box}}
"""


def svg_for(geo, calls, prefix):
    pats, fills, hatches = RM.ward_layers(geo["paths"], calls, prefix=prefix, tips=False)
    labels = "".join(f'<text x="{l["x"]}" y="{l["y"]}" text-anchor="middle" class="maplabel">{l["t"]}</text>'
                     for l in geo["labels"])
    W, H = geo["W"], geo["H"] - 30.0   # drop the strip reserved for the council inset
    return (f'<svg viewBox="0 0 {W:.0f} {H:.0f}"><defs>{pats}</defs>{fills}{hatches}{labels}'
            f'<text x="{W - 14:.0f}" y="20" text-anchor="end" class="mapnorth">N ↗</text></svg>'), W, H


def key_html(parties, forecast, draws=None):
    chips = "".join(f'<span class="k"><span class="chip" style="background:{colour(p)}"></span>{pname(p)}</span>'
                    for p in parties)
    if forecast:
        return (f'<div class="key">{chips}<br><span class="note">Solid: one party wins the ward in at least '
                f'9 of every 10 of {draws:,} simulations. Stripes: contested; a stripe for each party winning '
                f'1 in 10 or more, grey for the rest.</span></div>')
    return f'<div class="key">{chips}<br><span class="note">Ward winners, IEC results.</span></div>'


def panel(year, label, body, key):
    return f'<div class="panel"><div class="yr">{year}</div><div class="lbl">{label}</div>{body}{key}</div>'


def shoot(name, html, width):
    page = SCR / f"{name}.html"
    page.write_text(f"<!doctype html><meta charset=utf-8><style>{CSS.replace('WIDTH', str(width))}</style>"
                    f'<div class="frame" id="f">{html}</div>')
    png = OUT / f"{name}.png"
    tall = SCR / f"{name}_tall.png"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1", f"--window-size={width},1400",
                    "--virtual-time-budget=3000",
                    f"--screenshot={tall}", f"file://{page}"], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return tall


def trim(tall, png):
    from PIL import Image, ImageChops
    im = Image.open(tall).convert("RGB")
    bg = Image.new("RGB", im.size, (0xfb, 0xfb, 0xfa))
    bbox = ImageChops.difference(im, bg).getbbox()
    im.crop((0, 0, im.width, min(im.height, bbox[3] + 12))).save(png)
    return png


LABEL_F = "Forecast made from data before the {y} election"
LABEL_R = "Result, {y}"
years_f = ["2011", "2016", "2021", "2026"]
years_r = ["2011", "2016", "2021"]
data = {}
for y in years_f:
    if y == "2026":
        probs_src = REPO / "data/processed/ward_winner_probs.csv"
        draws = json.loads((REPO / "data/processed/forecast_summary.json").read_text())["scenario"]["draws"]
    else:
        probs_src = SCR / f"forecast_{y}_ward_winner_probs.csv"
        draws = json.loads((SCR / f"meta_{y}.json").read_text())["draws"]
    probs = read_probs(probs_src)
    sp = SCR / f"probs_short_{y}.csv"
    with sp.open("w", newline="") as fh:
        wr = csv.DictWriter(fh, ["ward", "winner", "p_win", "dist"])
        wr.writeheader()
        wr.writerows(probs.values())
    geo = geometry(y, sp)
    assert set(geo["paths"]) == set(probs), (y, set(geo["paths"]) ^ set(probs))
    calls = RM.probs_calls(probs.values())
    res = None
    if y in years_r:
        with (SCR / f"result_{y}_ward_winners.csv").open(newline="") as fh:
            res = {short(r["ward"]): r["winner"] for r in csv.DictReader(fh)}
        assert set(res) == set(geo["paths"]), (y, set(res) ^ set(geo["paths"]))
    data[y] = dict(probs=probs, geo=geo, calls=calls, res=res, draws=draws)

ORDER = ["ANC", "DA", "EFF", "ASA", "IFP", "PA", "ALJAMAAH", "MK"]


def present(parties):
    s = set(parties)
    return [p for p in ORDER if p in s] + sorted(s - set(ORDER))


def forecast_panel(y, prefix):
    d = data[y]
    svg, W, H = svg_for(d["geo"], d["calls"], prefix)
    parties = set()
    for c in d["calls"].values():
        parties |= {b[0] for b in c["bands"] if b[0] != RM.REST}
    parties |= {d["probs"][w]["winner"] for w, c in d["calls"].items() if c["cls"] == "solid"}
    return panel(y, LABEL_F.format(y=y), svg, key_html(present(parties), True, d["draws"])), W, H


def result_panel(y, prefix):
    d = data[y]
    calls = {w: {"fill": colour(p), "cls": "solid", "bands": [], "tip": ""} for w, p in d["res"].items()}
    svg, W, H = svg_for(d["geo"], calls, prefix)
    return panel(y, LABEL_R.format(y=y), svg, key_html(present(d["res"].values()), False))


frames = {"forecast": [], "results": [], "side": []}
for y in years_f:
    html, W, H = forecast_panel(y, f"f{y}")
    frames["forecast"].append(trim(shoot(f"forecast_{y}", html, 720), OUT / f"forecast_{y}.png"))
for y in years_r:
    frames["results"].append(trim(shoot(f"result_{y}", result_panel(y, f"r{y}"), 720), OUT / f"result_{y}.png"))
for y in years_f:
    left, W, H = forecast_panel(y, f"sf{y}")
    if data[y]["res"] is not None:
        right = result_panel(y, f"sr{y}")
    else:
        right = panel(y, LABEL_R.format(y=y),
                      f'<div class="empty" style="aspect-ratio:{W:.0f}/{H:.0f}">The {y} election has not been held.</div>', "")
    frames["side"].append(trim(shoot(f"side_{y}", f'<div class="panels">{left}{right}</div>', 1080),
                               OUT / f"side_{y}.png"))

from PIL import Image


def gif(pngs, name):
    ims = [Image.open(p).convert("RGB") for p in pngs]
    w = max(i.width for i in ims); h = max(i.height for i in ims)
    canvas = []
    for i in ims:
        c = Image.new("RGB", (w, h), (0xfb, 0xfb, 0xfa)); c.paste(i, (0, 0)); canvas.append(c)
    pal = [c.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for c in canvas]
    pal[0].save(OUT / name, save_all=True, append_images=pal[1:], duration=2000, loop=0, optimize=True)


gif(frames["forecast"], "forecast.gif")
gif(frames["results"], "results.gif")
gif(frames["side"], "side-by-side.gif")
print("fallback colours used for:", sorted(fallback))
