// Mockups for the share-card design. Reads data.json (make_data.py: every
// figure from repo files or the project's own code), writes HTML beside it,
// and screenshots each with headless Chromium. Nothing typed but words.
//   node render.mjs   (run with playwright-core resolvable: NODE_PATH=../pyo/node_modules)
import { readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PW || "../pyo/node_modules/playwright-core");

const HERE = new URL(".", import.meta.url).pathname;
const REPO = "/Users/simondavis/projects/atlas-jhb-election-model";
const FU = REPO + "/.claude/worktrees/followup";
const D = JSON.parse(readFileSync(HERE + "data.json", "utf8"));
const LOGO = readFileSync(FU + "/src/brand/logo.svg", "utf8").replace(/<!--[\s\S]*?-->/g, "");
const MADE = "2026-10-03";
const SITE = "joburg.whysoserious.city";
const OTHERS = "#464d47";

// ---------- words and figures ----------
const MONTHS = "January February March April May June July August September October November December".split(" ");
const dateText = iso => { const [y, m, d] = iso.split("-").map(Number); return d + " " + MONTHS[m - 1] + " " + y; };
const daysTo = (a, b) => Math.round((Date.parse(b) - Date.parse(a)) / 864e5);
const DAYS = daysTo(MADE, D.election.date);
const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const poss = n => n + (/s$/i.test(n) ? "'" : "'s");
const signed = (x, dp = 0) => (x > 0 ? "+" : x < 0 ? "−" : "±") + Math.abs(x).toFixed(dp);
const seatChange = r => (r.seats21 == null ? "new" : signed(r.seats - r.seats21));
const voteChange = r => (r.vote21 == null ? "new" : signed(r.vote - r.vote21, 1));
const nameOf = code => (code === "OTHERS" ? "Others" : D.A.rows.concat(D.B.rows).find(r => r.code === code)?.name || code);
const listAnd = xs => (xs.length < 2 ? xs.join("") : xs.slice(0, -1).join(", ") + " and " + xs[xs.length - 1]);
const article = c => (["ANC", "DA", "EFF", "PA", "IFP", "ACDP", "SACP"].includes(nameOf(c)) ? "the " : "");
const the = c => article(c) + nameOf(c);
// boldness: a judgement call on the page's own chance (DESIGN.md §4)
const band = p => (p >= 0.20 ? "Safe call" : p >= 0.05 ? "Bold call" : "Wild call");

function outcomeWords(F) {
  const o = F.outcome;
  const cap = t => t.charAt(0).toUpperCase() + t.slice(1);
  const lead = o.largest ? cap(the(o.largest)) + " is the largest party" : "Two or more parties tie for the most seats";
  const maj = o.majority_alone ? (o.largest ? " with a majority of its own" : "") : ", no party has a majority";
  const gov = o.coalition.length ? ", and " + listAnd(o.coalition.map(the)) + " govern" + (o.coalition.length === 1 ? "s" : "") : "";
  return lead + maj + gov + ".";
}

// rows: the top n by seats, the rest summed as Others
function topRows(F, n) {
  const shown = F.rows.slice(0, n), rest = F.rows.slice(n);
  const sum = k => rest.reduce((a, r) => a + (r[k] || 0), 0);
  return rest.length ? [...shown, { code: "OTHERS", name: "Others", colour: OTHERS, seats: sum("seats"), ward: sum("ward"), pr: sum("pr"),
    vote: Math.round(sum("vote") * 10) / 10, seats21: null, vote21: null, others: true }] : shown;
}
const colourOf = r => (r.colour === "#8b918b" ? "#8b918b" : r.colour);
const logoSrc = c => `file://${REPO}/site/logos/${c}.png`;
const hasLogo = r => r.logo && !r.others;

// ---------- the council: 270 seats, 27 columns of 10 ----------
// Coalition parties first (seat order), then the rest (seat order). Within a
// party, ward seats solid, PR seats tinted. The stepped line encloses the
// first majority-1 seats: a block that crosses it holds a majority.
function council(F, { cell, gap, line = "#eceee9", rows = 10, label = true, fs = 14 }) {
  const order = [...F.rows.filter(r => F.coalition.includes(r.code)), ...F.rows.filter(r => !F.coalition.includes(r.code))];
  const seats = [];
  for (const r of order) {
    for (let i = 0; i < r.ward; i++) seats.push({ c: colourOf(r), pr: false });
    for (let i = 0; i < r.pr; i++) seats.push({ c: colourOf(r), pr: true });
  }
  const cols = Math.ceil(F.council / rows), step = cell + gap;
  const W = cols * step - gap, top = label ? fs + 10 : 0, H = top + rows * step - gap;
  let s = "";
  seats.forEach((x, i) => {
    const cx = Math.floor(i / rows) * step, cy = top + (i % rows) * step;
    s += `<rect x="${cx}" y="${cy}" width="${cell}" height="${cell}" rx="${Math.max(1, cell / 6)}" fill="${x.c}"${x.pr ? ' fill-opacity="0.42"' : ""}/>`;
  });
  // the majority line: after seat (majority - 1)
  const k = F.majority - 1, col = Math.floor(k / rows), row = k % rows;
  const xa = col * step - gap / 2, xb = (col + 1) * step - gap / 2, ym = top + row * step - gap / 2;
  const y0 = top - 4, y1 = top + rows * step - gap + 4;
  const path = row === 0 ? `M${xa} ${y0}V${y1}` : `M${xb} ${y0}V${ym}H${xa}V${y1}`;
  s += `<path d="${path}" fill="none" stroke="${line}" stroke-width="${Math.max(2, gap)}" stroke-linejoin="miter"/>`;
  if (label) s += `<text x="${xb + 6}" y="${fs}" font-size="${fs}" fill="#b6bcb6" font-family="IBM Plex Sans">${F.majority} for a majority</text>`;
  return `<svg class="council" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" style="overflow:visible;display:block">${s}</svg>`;
}

// ---------- the ward map ----------
function map(F, w) {
  const g = D.geom, h = w * g.H / g.W;
  const p = g.paths.map((d, i) => `<path d="${d}" fill="${D.colours[F.calls[i]] || "#8b918b"}" stroke="#141715" stroke-width="0.8" stroke-linejoin="round"/>`).join("");
  return `<svg class="map" width="${w}" height="${h.toFixed(0)}" viewBox="0 0 ${g.W} ${g.H}">${p}</svg>`;
}
const logo = (h, colour = "#eceee9") => LOGO.replace("<svg ", `<svg style="height:${h}px;width:auto;display:block;color:${colour}" `);

// ---------- shared CSS ----------
const fontFace = [["IBM Plex Sans", "IBMPlexSans", [["Regular", 400], ["Medium", 500], ["SemiBold", 600], ["Bold", 700]]],
  ["IBM Plex Serif", "IBMPlexSerif", [["Regular", 400], ["SemiBold", 600], ["Bold", 700]]],
  ["IBM Plex Mono", "IBMPlexMono", [["Regular", 400], ["SemiBold", 600]]]]
  .flatMap(([fam, stem, faces]) => faces.map(([n, w]) => `@font-face{font-family:"${fam}";font-weight:${w};src:url("file://${FU}/src/fonts/${stem}-${n}-Latin1.woff2") format("woff2")}`)).join("\n");
const BASE_CSS = `${fontFace}
:root{--paper:#141715;--paper-2:#1c201d;--rule:#333833;--ink:#eceee9;--ink-2:#b6bcb6;--ink-3:#868d86;--accent:#d9954f}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--paper);color:var(--ink);font-family:"IBM Plex Sans",system-ui,sans-serif;-webkit-font-smoothing:antialiased}
.serif{font-family:"IBM Plex Serif",Georgia,serif}.mono{font-family:"IBM Plex Mono",monospace}
.num{font-variant-numeric:tabular-nums}`;

const page = (w, h, css, body) => `<!doctype html><meta charset="utf-8"><style>${BASE_CSS}
html,body{width:${w}px;height:${h}px;overflow:hidden}${css}</style><body>${body}</body>`;

// ---------- the link card, 1200 x 630 ----------
function linkCard(F) {
  const lead = F.rows[0], rows = topRows(F, 6);
  const cs = F.coalition.reduce((a, c) => a + F.rows.find(r => r.code === c).seats, 0);
  const css = `
.band{position:absolute;left:0;top:0;width:1200px;height:10px;background:${lead.colour}}
.card{position:absolute;inset:10px 0 0 0;padding:30px 48px 0 48px}
.lg{position:absolute;right:44px;top:22px}
.top{display:flex;justify-content:space-between;align-items:flex-start}
.when{font-size:19px;color:var(--ink-3);text-align:right;line-height:1.35;margin-top:4px}
h1{font-family:"IBM Plex Serif";font-weight:600;font-size:56px;line-height:1.05;letter-spacing:-.01em;margin-top:34px;white-space:nowrap;display:inline-block}
.sub{font-size:20px;color:var(--ink-2);margin-top:8px;line-height:1.35}
.main{display:grid;grid-template-columns:620px 1fr;gap:36px;margin-top:18px;align-items:start}
.gov{font-size:22px;margin-top:14px;color:var(--ink)}
.gov b{font-weight:600}
table{border-collapse:collapse;width:100%}
th{font-size:16px;font-weight:500;color:var(--ink-3);text-align:right;padding:0 0 6px}
th:first-child{text-align:left}
td{font-size:23px;padding:3px 0;line-height:1.15}
td.n{text-align:right;font-weight:700;font-size:26px;width:64px}
td.d{text-align:right;color:var(--ink-2);font-size:19px;width:82px}
.p{display:flex;align-items:center;gap:10px;font-weight:600}
.chip{width:26px;height:26px;border-radius:4px;flex:none}
.chip img{width:26px;height:26px;border-radius:4px;display:block;background:#fff}
.foot{position:absolute;left:48px;right:48px;bottom:26px;display:flex;justify-content:space-between;align-items:flex-end;border-top:1px solid var(--rule);padding-top:14px}
.chance{font-family:"IBM Plex Serif";font-size:30px;font-weight:600}
.what{font-size:17px;color:var(--ink-2);margin-bottom:4px}
.badge{display:inline-block;font-family:"IBM Plex Sans";font-size:17px;font-weight:600;border:1.5px solid var(--ink-2);color:var(--ink);border-radius:20px;padding:2px 12px;margin-left:12px;vertical-align:5px}
.url{font-size:19px;color:var(--ink-2);text-align:right}
.url b{color:var(--ink);font-family:"IBM Plex Mono";font-weight:600}`;
  const tr = r => `<tr><td><div class="p"><span class="chip" style="background:${r.colour}">${hasLogo(r) ? `<img src="${logoSrc(r.code)}">` : ""}</span>${esc(r.name)}</div></td>
    <td class="n num">${r.seats}</td><td class="d num">${r.others ? "" : seatChange(r)}</td></tr>`;
  const body = `<div class="band"></div><div class="card">
  <div class="lg">${logo(118)}</div>
  <h1 class="fit" data-max="900">${esc(poss(F.name))} election forecast</h1>
  <div class="sub">Johannesburg council, ${dateText(D.election.date)}, ${F.council} seats.<br>Made ${dateText(MADE)}, ${DAYS} days before the vote.</div>
  <div class="main"><div>${council(F, { cell: 18, gap: 3, fs: 15 })}
     <div class="gov">Governing: <b>${esc(listAnd(F.coalition.map(nameOf)))}</b>, ${cs} seats.</div></div>
    <table><tr><th>Seats</th><th>Seats</th><th>vs 2021</th></tr>${rows.map(tr).join("")}</table></div>
  <div class="foot"><div><div class="what">${esc(outcomeWords(F))}</div>
    <div class="chance">We give this outcome a ${F.outcome.text} chance.<span class="badge">${band(F.outcome.p)}</span></div></div>
    <div class="url">Make yours at<br><b>${SITE}</b></div></div></div>`;
  return page(1200, 630, css, body.replace("<th>Seats</th><th>Seats</th>", "<th></th><th>Seats</th>"));
}

// ---------- the story card, 1080 x 1920 ----------
function storyCard(F) {
  const lead = F.rows[0], rows = topRows(F, 6);
  const cs = F.coalition.reduce((a, c) => a + F.rows.find(r => r.code === c).seats, 0);
  const exc = Object.entries(F.excessive || {}).filter(([, v]) => v > 0);
  const css = `
.band{position:absolute;left:0;top:0;width:1080px;height:16px;background:${lead.colour}}
.card{position:absolute;inset:16px 0 0 0;padding:44px 60px 0}
.top{display:flex;justify-content:space-between;align-items:flex-start}
.when{font-size:28px;color:var(--ink-3);text-align:right;line-height:1.35}
h1{font-family:"IBM Plex Serif";font-weight:600;font-size:70px;line-height:1.05;letter-spacing:-.015em;margin-top:28px;white-space:nowrap;display:inline-block}
.sub{font-size:30px;color:var(--ink-2);margin-top:12px}
.cn{margin-top:28px}
.key{font-size:24px;color:var(--ink-3);margin-top:12px;display:flex;gap:28px}.key b{color:var(--ink);font-weight:600}
.key i{display:inline-block;width:20px;height:20px;border-radius:3px;background:var(--ink-2);vertical-align:-3px;margin-right:8px}
.key i.t{opacity:.42}
.gov{font-size:32px;margin-top:22px}.gov b{font-weight:600}
table{border-collapse:collapse;width:100%;margin-top:30px}
th{font-size:22px;font-weight:500;color:var(--ink-3);text-align:right;padding:0 0 10px;line-height:1.2;vertical-align:bottom}
th:first-child{text-align:left}
td{font-size:29px;padding:3px 0;text-align:right;border-top:1px solid var(--rule)}
td:first-child{text-align:left}
td.n{font-weight:700;font-size:34px}
td.d{color:var(--ink-2);font-size:26px}
.p{display:flex;align-items:center;gap:14px;font-weight:600}
.chip{width:36px;height:36px;border-radius:5px;flex:none}.chip img{width:36px;height:36px;border-radius:5px;display:block;background:#fff}
.low{display:grid;grid-template-columns:340px 1fr;gap:40px;margin-top:24px;align-items:start}
.what{font-size:27px;color:var(--ink-2);line-height:1.35}
.chance{font-family:"IBM Plex Serif";font-size:42px;font-weight:600;line-height:1.15;margin-top:10px}
.badge{display:inline-block;font-size:26px;font-weight:600;border:2px solid var(--ink-2);border-radius:30px;padding:3px 18px;margin-top:18px}
.note{font-size:22px;color:var(--ink-3);margin-top:16px;line-height:1.4}
.foot{margin-top:24px;border-top:1px solid var(--rule);padding-top:20px;font-size:27px;color:var(--ink-2);line-height:1.4}
.foot b{font-family:"IBM Plex Mono";font-weight:600;color:var(--ink)}`;
  const tr = r => `<tr><td><div class="p"><span class="chip" style="background:${r.colour}">${hasLogo(r) ? `<img src="${logoSrc(r.code)}">` : ""}</span>${esc(r.name)}</div></td>
    <td class="n num">${r.seats}</td><td class="num">${r.ward}</td><td class="num">${r.pr}</td><td class="num">${r.vote.toFixed(1)}%</td>
    <td class="d num">${r.others ? "" : seatChange(r)}</td><td class="d num">${r.others ? "" : voteChange(r)}</td></tr>`;
  const body = `<div class="band"></div><div class="card">
  <div class="top">${logo(130)}<div class="when">Made ${dateText(MADE)}<br>${DAYS} days to the vote</div></div>
  <h1 class="fit" data-max="960">${esc(poss(F.name))} election forecast</h1>
  <div class="sub">Johannesburg council, ${dateText(D.election.date)}. ${F.council} seats.</div>
  <div class="cn">${council(F, { cell: 25, gap: 4, fs: 22 })}
    <div class="key"><span><i></i>ward seats</span><span><i class="t"></i>PR seats</span><span>Governing first: <b>${esc(listAnd(F.coalition.map(nameOf)))}</b>, ${cs} seats</span></div></div>
  <table><tr><th></th><th>Seats</th><th>Wards</th><th>PR</th><th>Vote</th><th>Seats<br>vs 2021</th><th>Vote<br>vs 2021</th></tr>${rows.map(tr).join("")}</table>
  <div class="low">${map(F, 340)}<div><div class="what">${esc(outcomeWords(F))}</div>
    <div class="chance">We give this outcome a ${F.outcome.text} chance.</div><div class="badge">${band(F.outcome.p)}</div>
    ${exc.length ? `<div class="note">${exc.map(([c, v]) => `${esc(the(c).replace(/^t/, "T"))} wins ${v} more wards than its vote entitles it to seats. It keeps them, and gets no PR seats.`).join(" ")}</div>` : ""}</div></div>
  <div class="foot">Bring this link back after the count. It will be scored against the result.<br>Make yours at <b>${SITE}</b></div></div>`;
  return page(1080, 1920, css, body);
}

// ---------- the duel card, 1200 x 630 ----------
function duelCard(A, B) {
  const codes = [...new Set([...A.rows.slice(0, 7), ...B.rows.slice(0, 7)].map(r => r.code))]
    .sort((x, y) => (A.rows.find(r => r.code === y)?.seats || 0) - (A.rows.find(r => r.code === x)?.seats || 0)).slice(0, 7);
  const get = (F, c) => F.rows.find(r => r.code === c);
  const css = `
.card{position:absolute;inset:0;padding:40px 48px 0}
.lg{position:absolute;right:44px;top:26px}
h1{font-family:"IBM Plex Serif";font-weight:600;font-size:48px;line-height:1.05;margin-top:22px}
h1 span{color:var(--ink-3);font-weight:400}
.sub{font-size:21px;color:var(--ink-2);margin-top:6px}
.main{display:grid;grid-template-columns:470px 1fr;gap:40px;margin-top:22px;align-items:start}
.who{font-size:20px;font-weight:600;margin:0 0 6px}.who span{font-weight:400;color:var(--ink-2)}
.pair{margin-bottom:12px}
table{border-collapse:collapse;width:100%}
th{font-size:17px;font-weight:600;color:var(--ink-2);text-align:right;padding:0 0 6px;max-width:150px}
th:first-child{text-align:left}
td{font-size:23px;padding:3px 0;text-align:right}
td:first-child{text-align:left}
td.n{font-weight:700;font-size:25px}
td.d{color:var(--ink-3);font-size:19px}
.p{display:flex;align-items:center;gap:10px;font-weight:600}
.chip{width:24px;height:24px;border-radius:4px;flex:none}.chip img{width:24px;height:24px;border-radius:4px;display:block;background:#fff}
.foot{position:absolute;left:48px;right:48px;bottom:24px;border-top:1px solid var(--rule);padding-top:12px;display:flex;justify-content:space-between;font-size:19px;color:var(--ink-2)}
.foot b{font-family:"IBM Plex Mono";color:var(--ink);font-weight:600}`;
  const g = F => `<div class="pair"><div class="who">${esc(F.name)} <span>We give it a ${F.outcome.text} chance. ${band(F.outcome.p)}.</span></div>${council(F, { cell: 11, gap: 2, label: false })}</div>`;
  const tr = c => { const a = get(A, c)?.seats || 0, b = get(B, c)?.seats || 0; const r = get(A, c) || get(B, c);
    return `<tr><td><div class="p"><span class="chip" style="background:${r.colour}">${hasLogo(r) ? `<img src="${logoSrc(r.code)}">` : ""}</span>${esc(r.name)}</div></td><td class="n num">${a}</td><td class="n num">${b}</td><td class="d num">${signed(b - a)}</td></tr>`; };
  const body = `<div class="card"><div class="lg">${logo(104)}</div>
  <h1>${esc(A.name)} <span>and</span> ${esc(B.name)}</h1>
  <div class="sub">Two forecasts of the Johannesburg council, ${F_council(A)} seats.<br>Made ${dateText(MADE)}, ${DAYS} days before the vote.</div>
  <div class="main"><div>${g(A)}${g(B)}</div>
  <table><tr><th>Seats</th><th>${esc(A.name)}</th><th>${esc(B.name)}</th><th>Difference</th></tr>${codes.map(tr).join("")}</table></div>
  <div class="foot"><span>Bring this link back after the count. Both forecasts will be scored.</span><span><b>${SITE}</b></span></div></div>`;
  return page(1200, 630, css, body);
}
const F_council = F => F.council;

// ---------- the arrival page ----------
function arrival(F, width) {
  const narrow = width < 700, rows = topRows(F, narrow ? 7 : 9);
  const cs = F.coalition.reduce((a, c) => a + F.rows.find(r => r.code === c).seats, 0);
  const css = `
html,body{height:auto;overflow:visible}
.topnav{display:flex;flex-wrap:wrap;gap:${narrow ? "6px 14px" : "8px 22px"};padding:${narrow ? "12px 16px" : "16px 40px"};border-bottom:1px solid var(--rule);font-size:${narrow ? 13 : 14}px;align-items:center}
.topnav a{color:var(--ink-2);text-decoration:none}.topnav a.home{color:var(--ink);font-family:"IBM Plex Mono";font-weight:600}
.wrap{max-width:1180px;margin:0 auto;padding:${narrow ? "22px 16px 48px" : "40px 40px 80px"}}
.from{font-size:${narrow ? 14 : 15}px;color:var(--ink-3);display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.from .sw{width:10px;height:10px;border-radius:2px;background:${F.rows[0].colour}}
h1{font-family:"IBM Plex Serif";font-weight:600;font-size:${narrow ? 32 : 48}px;line-height:1.08;margin:10px 0 6px}
.sub{color:var(--ink-2);font-size:${narrow ? 16 : 18}px}
.grid{display:grid;grid-template-columns:${narrow ? "1fr" : "auto 1fr"};gap:${narrow ? 26 : 48}px;margin-top:${narrow ? 22 : 34}px}
.verdict{border:1px solid var(--rule);background:var(--paper-2);border-radius:8px;padding:${narrow ? "16px" : "22px 26px"};margin-top:${narrow ? 20 : 28}px}
.verdict .what{color:var(--ink-2);font-size:${narrow ? 15 : 17}px;line-height:1.45}
.verdict .ch{font-family:"IBM Plex Serif";font-weight:600;font-size:${narrow ? 24 : 30}px;margin-top:6px;line-height:1.2}
.verdict .badge{display:inline-block;font-size:14px;font-weight:600;border:1.5px solid var(--ink-2);border-radius:20px;padding:1px 10px;margin-left:8px;vertical-align:4px;font-family:"IBM Plex Sans"}
.verdict .how{font-size:13px;color:var(--ink-3);margin-top:8px;line-height:1.45}
.key{font-size:13px;color:var(--ink-3);margin-top:8px;display:flex;gap:16px;flex-wrap:wrap}
.key i{display:inline-block;width:11px;height:11px;border-radius:2px;background:var(--ink-2);margin-right:6px;vertical-align:-1px}.key i.t{opacity:.42}
.gov{margin-top:10px;font-size:${narrow ? 15 : 17}px}.gov b{font-weight:600}
table{border-collapse:collapse;width:100%}
th{font-size:12.5px;font-weight:500;color:var(--ink-3);text-align:right;padding:0 0 6px 6px;vertical-align:bottom;line-height:1.25}
th:first-child{text-align:left;padding-left:0}
td{font-size:${narrow ? 14 : 16}px;padding:6px 0 6px 6px;text-align:right;border-top:1px solid var(--rule)}
td:first-child{text-align:left;padding-left:0}
td.n{font-weight:700}td.d{color:var(--ink-2)}
.p{display:flex;align-items:center;gap:8px;font-weight:600}
.chip{width:${narrow ? 18 : 20}px;height:${narrow ? 18 : 20}px;border-radius:3px;flex:none}.chip img{width:100%;height:100%;border-radius:3px;display:block;background:#fff}
.mapwrap{margin-top:${narrow ? 18 : 30}px}.mapwrap .cap{font-size:13px;color:var(--ink-3);margin-top:4px}
.ctas{margin-top:${narrow ? 30 : 44}px;border-top:1px solid var(--rule);padding-top:${narrow ? 22 : 30}px}
.ctas h2{font-family:"IBM Plex Serif";font-weight:600;font-size:${narrow ? 22 : 26}px}
.ctas p{color:var(--ink-2);font-size:${narrow ? 15 : 16}px;margin-top:6px;max-width:62ch;line-height:1.5}
.btns{display:flex;flex-direction:${narrow ? "column" : "row"};gap:12px;margin-top:18px}
.btn{display:block;text-decoration:none;border-radius:6px;padding:${narrow ? "13px 16px" : "13px 20px"};font-weight:600;font-size:16px;border:1.5px solid var(--rule);color:var(--ink);text-align:${narrow ? "left" : "center"}}
.btn small{display:block;font-weight:400;font-size:13px;color:var(--ink-2);margin-top:2px}
.quick{margin-top:14px;text-align:center}
.btn.primary{background:var(--ink);color:var(--paper);border-color:var(--ink)}.btn.primary small{color:#4a4f4b}
.later{margin-top:${narrow ? 30 : 40}px;display:grid;grid-template-columns:${narrow ? "1fr" : "repeat(3,1fr)"};gap:${narrow ? 14 : 22}px}
.later div{border-top:1px solid var(--rule);padding-top:12px}
.later h3{font-size:15px;font-weight:600}.later p{font-size:14px;color:var(--ink-2);margin-top:4px;line-height:1.5}
.later .big{font-family:"IBM Plex Serif";font-size:30px;font-weight:600;color:var(--ink)}`;
  const tr = r => `<tr><td><div class="p"><span class="chip" style="background:${r.colour}">${hasLogo(r) ? `<img src="${logoSrc(r.code)}">` : ""}</span>${esc(r.name)}</div></td>
    <td class="n num">${r.seats}</td><td class="num">${r.ward}</td>${narrow ? "" : `<td class="num">${r.pr}</td>`}<td class="num">${r.vote.toFixed(1)}%</td>
    <td class="d num">${r.others ? "" : seatChange(r)}</td>${narrow ? "" : `<td class="d num">${r.others ? "" : voteChange(r)}</td>`}</tr>`;
  const cell = narrow ? 10 : 18, gap = narrow ? 2 : 3;
  const MAP = `<div class="mapwrap">${map(F, narrow ? 343 : 500)}<div class="cap">Each ward in the colour of the party ${esc(F.name)} called it for.</div></div>`;
  const body = `<nav class="topnav"><a class="home">${SITE}</a><a>our forecast</a><a>your forecast</a>${narrow ? "" : "<a>commentary</a><a>party claims tested</a><a>methodology</a><a>corrections</a><a>sources</a>"}</nav>
<div class="wrap">
  <div class="from"><span class="sw"></span>A forecast shared with you, made ${dateText(MADE)}.</div>
  <h1>${esc(poss(F.name))} election forecast</h1>
  <div class="sub">Johannesburg council, ${dateText(D.election.date)}. ${F.council} seats, ${F.majority} for a majority.</div>
  <div class="verdict"><div class="what">${esc(outcomeWords(F))}</div>
    <div class="ch">We give this outcome a ${F.outcome.text} chance.<span class="badge">${band(F.outcome.p)}</span></div>
    <div class="how">The chance is ours, from the forecast as published today. The seats are ${esc(poss(F.name))}: every ward called, the vote set, and the law seating the result.</div></div>
  ${narrow ? `<a class="btn primary quick">Make your own, starting from ${esc(poss(F.name))}</a>` : ""}
  <div class="grid"><div>${council(F, { cell, gap, fs: 13 })}
      <div class="key"><span><i></i>ward seats</span><span><i class="t"></i>PR seats</span><span>governing parties first</span></div>
      <div class="gov">Governing: <b>${esc(listAnd(F.coalition.map(nameOf)))}</b>, ${cs} of ${F.council} seats.</div>
      ${narrow ? MAP : ""}</div>
    <div><table><tr><th></th><th>Seats</th><th>Wards</th>${narrow ? "" : "<th>PR</th>"}<th>Vote</th><th>Seats vs 2021</th>${narrow ? "" : "<th>Vote vs 2021, points</th>"}</tr>${rows.map(tr).join("")}</table>${narrow ? "" : MAP}</div></div>
  <div class="ctas"><h2>Make your own</h2>
    <p>Change any ward, the vote or who governs. The seats follow from the law. When you share yours, the link can show both forecasts side by side.</p>
    <div class="btns"><a class="btn primary">Start from ${esc(poss(F.name))}<small>Every ward and vote as ${esc(F.name)} set them</small></a>
      <a class="btn">Start from our forecast<small>The model's most likely winners</small></a>
      <a class="btn">See our forecast<small>Chances for every party and ward</small></a></div></div>
  <div class="later"><div><h3>The vote</h3><p><span class="big">${DAYS} days</span><br>Polls open at 07:00 on ${dateText(D.election.date)}.</p></div>
    <div><h3>After the count</h3><p>Open this link again once the results are declared. It will be scored against them: seats per party first, then wards won, then wards called right.</p></div>
    <div><h3>Nothing stored</h3><p>The forecast is in the link. We keep no copy and nothing about ${esc(F.name)} or you.</p></div></div>
</div>`;
  return `<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><style>${BASE_CSS}${css}</style><body>${body}</body>`;
}

// ---------- write and shoot ----------
const jobs = [
  ["card-1200x630", linkCard(D.A), 1200, 630, false],
  ["card-1080x1920", storyCard(D.A), 1080, 1920, false],
  ["card-1200x630-B", linkCard(D.B), 1200, 630, false],
  ["duel-1200x630", duelCard(D.A, D.B), 1200, 630, false],
  ["arrival-375", arrival(D.A, 375), 375, 812, true],
  ["arrival-1440", arrival(D.A, 1440), 1440, 900, true],
];
const b = await chromium.launch({ headless: true });
for (const [name, html, w, h, full] of jobs) {
  writeFileSync(HERE + name + ".html", html);
  const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: full ? 2 : 1 });
  await p.goto("file://" + HERE + name + ".html");
  await p.evaluate(() => document.fonts.ready);
  const low = await p.evaluate(() => {
    for (const e of document.querySelectorAll(".fit")) { const max = +e.dataset.max; let fs = parseFloat(getComputedStyle(e).fontSize);
      while (e.scrollWidth > max && fs > 24) { fs -= 1; e.style.fontSize = fs + "px"; } }
    return Math.max(...[...document.querySelectorAll(".card *")].map(e => e.getBoundingClientRect().bottom), 0);
  });
  if (!full) console.log(name, "lowest text", Math.round(low));
  await p.waitForTimeout(300);
  await p.screenshot({ path: HERE + name + ".png", fullPage: full });
  await p.close();
}
await b.close();
console.log("wrote", jobs.map(j => j[0]).join(", "));
