#!/usr/bin/env node
// Item 9 mock-ups: one 1200 x 630 share image per page type, drawn as SVG and
// rasterised through the share cards' own path (render_cards.mjs toPNG:
// src/og-raster.js, resvg-wasm, src/card-fonts/). Figures are today's values
// read from the built pages (data-current, or the span text where a token
// carries none); the build would take them from tokens. Writes PNGs beside
// this file.
//
//   node audits/2026-10-09-site-batch/og-design/make_og.mjs
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { toPNG, assets as cardAssets, specs } from "../../../interactive/tools/render_cards.mjs";
import { textWidth, fitText, wrapText, brandWidth, SITE } from "../../../interactive/js/share-card.js";
import { FACES } from "../../../interactive/js/card-fonts.js";

const OUT = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(OUT, "../../..");
const page = f => readFileSync(resolve(REPO, "site", f), "utf8");
const W = 1200, H = 630, X = 56, R = W - 56;

// ---------- the house: palette (site.css dark theme) and kind colours ----------
const C = { paper: "#141715", paper2: "#1c201d", rule: "#333833", ink: "#eceee9", ink2: "#b6bcb6", ink3: "#868d86" };
const KIND = { claim: "#d9954f", article: "#7aa6d6", forecast: "#eceee9", interactive: "#b98ad6" };
const VERDICT = { "v-false": "#d98070", "v-unlikely": "#c99482", "v-open": "#9aa09a", "v-likely": "#c7a76a", "v-true": "#6fb98a" };

// ---------- primitives (share-card.js keeps these private; same definitions) ----------
const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const n1 = v => Number(v.toFixed(1));
function text(x, y, s, fs, face = "sans", { fill = C.ink, anchor = "", ls = 0 } = {}) {
  const f = FACES[face];
  return `<text x="${n1(x)}" y="${n1(y)}" font-family="${f.family}" font-weight="${f.weight}" font-size="${n1(fs)}"` +
    `${anchor ? ` text-anchor="${anchor}"` : ""}${ls ? ` letter-spacing="${ls}"` : ""} fill="${fill}">${esc(s)}</text>`;
}
const rect = (x, y, w, h, fill, extra = "") => `<rect x="${n1(x)}" y="${n1(y)}" width="${n1(w)}" height="${n1(h)}" fill="${fill}"${extra}/>`;
const A = cardAssets();
function brand(x, y, h, ink = C.ink) {
  const b = A.brand;
  const [, , vw, vh] = b.viewBox.split(/\s+/).map(Number);
  const body = ink === C.ink ? b.body : b.body.split(C.ink).join(ink);
  return `<svg x="${n1(x)}" y="${n1(y)}" width="${n1(h * vw / vh)}" height="${n1(h)}" viewBox="${b.viewBox}" fill="${ink}">${body}</svg>`;
}
function chip(code, x, y, s, colour) {
  const src = A.logos[code];
  const rx = Math.max(2, s / 6.5);
  if (!src) return rect(x, y, s, s, colour, ` rx="${n1(rx)}"`);
  return rect(x - 3, y - 3, s + 6, s + 6, colour, ` rx="${n1(rx + 2)}"`) + rect(x, y, s, s, "#ffffff", ` rx="${n1(rx)}"`) +
    `<image x="${n1(x + 2)}" y="${n1(y + 2)}" width="${n1(s - 4)}" height="${n1(s - 4)}" href="${src}" preserveAspectRatio="xMidYMid meet"/>`;
}
const mono = (x, y, s, fs, fill, anchor = "") => text(x, y, s.toUpperCase(), fs, "monoSemi", { fill, anchor, ls: 1.5 });

// ---------- the fixed frame: kind bar, kicker, footer with date line and logo ----------
const FOOT = 560;
function frame(kind, kicker, dateLine, { footRule = true } = {}) {
  let s = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">` + rect(0, 0, W, H, C.paper);
  s += rect(0, 0, W, 8, KIND[kind]);
  s += mono(X, 56, kicker, 17, KIND[kind]);
  if (footRule) s += rect(X, FOOT, R - X, 1, C.rule);
  s += text(X, 604, dateLine, 17, "sans", { fill: C.ink3 });
  const bh = 50, bw = brandWidth(A, bh);
  s += brand(R - bw + 4, 572, bh);
  return s;
}

// ---------- the verdict stamp: a toothed seal in the verdict's colour ----------
// Words in the card faces, the verdict text verbatim from the page; the seal
// is the owner's stamp idiom (ragged edge, a ring, slight rotation).
let uid = 0;
function stamp(cx, cy, r, words, colour, { ring = true, rot = -9 } = {}) {
  const id = "st" + uid++;
  const teeth = Math.round(r / 5.5), pts = [];
  for (let i = 0; i < teeth * 2; i++) {
    const a = Math.PI * i / teeth, rr = i % 2 ? r * 0.93 : r;
    pts.push(n1(cx + rr * Math.cos(a)) + "," + n1(cy + rr * Math.sin(a)));
  }
  const ri = ring ? r * 0.7 : r * 0.8;
  let s = `<g transform="rotate(${rot} ${cx} ${cy})">`;
  s += `<polygon points="${pts.join(" ")}" fill="${colour}"/>`;
  s += `<circle cx="${cx}" cy="${cy}" r="${n1(ri)}" fill="${C.paper}"/>`;
  s += `<circle cx="${cx}" cy="${cy}" r="${n1(ri - r * 0.05)}" fill="none" stroke="${colour}" stroke-width="${n1(Math.max(1.5, r * 0.018))}"/>`;
  if (ring) {
    // arc text on the coloured band: over the top, and under the bottom left to right
    const ra = r * 0.79, fs = r * 0.105;
    s += `<defs><path id="${id}t" d="M${n1(cx - ra)} ${cy} A${n1(ra)} ${n1(ra)} 0 0 1 ${n1(cx + ra)} ${cy}"/>` +
      `<path id="${id}b" d="M${n1(cx - ra - fs * 0.72)} ${cy} A${n1(ra + fs * 0.72)} ${n1(ra + fs * 0.72)} 0 0 0 ${n1(cx + ra + fs * 0.72)} ${cy}"/></defs>`;
    const arc = (pid, t) => `<text font-family="IBM Plex Sans" font-weight="700" font-size="${n1(fs)}" fill="${C.paper}" letter-spacing="${n1(fs * 0.18)}">` +
      `<textPath href="#${pid}" startOffset="50%" text-anchor="middle">${esc(t)}</textPath></text>`;
    s += arc(id + "t", "CLAIM TESTED") + arc(id + "b", SITE.toUpperCase());
  }
  // the verdict, as large as fits the inner circle, on at most two lines
  const inner = ri * 1.62;
  let fs = r * 0.36, lines;
  for (; fs > 8; fs -= 1) {
    lines = wrapText(words, inner, fs, "sansBold");
    const lh = fs * 1.02, hh = lines.length * lh;
    const ok = lines.length <= 2 && lines.every((l, k) => {
      const yy = Math.abs(-hh / 2 + (k + 0.5) * lh) + fs * 0.4;
      const chord = 2 * Math.sqrt(Math.max(0, (ri * 0.88) ** 2 - yy ** 2));
      return textWidth(l, fs, "sansBold") <= chord;
    });
    if (ok) break;
  }
  const lh = fs * 1.02, y0 = cy - (lines.length * lh) / 2 + lh * 0.78;
  s += lines.map((l, k) => text(cx, y0 + k * lh, l, fs, "sansBold", { fill: colour, anchor: "middle", ls: n1(fs * 0.03) })).join("");
  return s + "</g>";
}

// ---------- page data, from the built pages ----------
const claimsHTML = page("claims.html");
const unescape = s => s.replace(/&#x27;/g, "'").replace(/&amp;/g, "&").replace(/&quot;/g, '"');
const strip = s => unescape(s.replace(/<[^>]+>/g, "")).replace(/\s+/g, " ").trim();
const SHORT = {   // a quote that will not fit is cut, and the cut marked [...] (packet: "shortened only where it must be, marked")
  1: "[…] we can only be able to do so if the people of greater Johannesburg give their organisation, the ANC, absolute authority without any hesitation",
  2: "[…] According to us, we are going to be the biggest party in the city",
  3: "We won't go into a coalition with MK, and we will not go into coalition with the EFF. […] You cannot govern with people who don't share any of your ideology",
};
const claims = [...claimsHTML.matchAll(/<article class="claim[^"]*" data-party="([^"]*)">([\s\S]*?)<\/blockquote>/g)].map(([, code, b], i) => {
  const who = /<div class="claim-who"><b>([^<]*)<\/b><span>([\s\S]*?)<\/span><\/div>/.exec(b);
  const [person, source] = strip(who[2]).split(" · ");
  const v = /class="verdict ([^"]*)">([^<]*)/.exec(b);
  return { i, code, party: unescape(who[1]), person, source,
    tested: /class="pubdate">([^:<]*)/.exec(b)[1], vclass: v[1], verdict: v[2],
    quote: strip(/claim-quote">([\s\S]*?)<span class="q-close">/.exec(b)[1]) };
});
const F = specs().party;
const colourOf = c => (F(c) || {}).colour || "#868d86";
const token = (html, name) => {
  const m = new RegExp(`data-token="${name.replace(/\./g, "\\.")}"[^>]*?(?:data-current="([^"]*)")?[^>]*>([^<]*)<`).exec(html);
  return m ? (m[1] ?? m[2]) : null;
};
const fc = page("forecast.html");
const generated = token(fc, "generated_date");
const ranges = [...fc.matchAll(/data-code="([^"]*)" data-m="(\d+)" data-p5="(\d+)" data-p95="(\d+)"/g)]
  .map(([, code, m, p5, p95]) => ({ code, m: +m, p5: +p5, p95: +p95 }));

// ---------- 1. the claims page ----------
function claimsIndex() {
  let s = frame("claim", "The campaign arithmetic", `${claims.length} claims, each tested against the forecast. Latest tested ${claims.map(c => c.tested).sort((a, b) => Date.parse(b) - Date.parse(a))[0]}.`);
  const head = wrapText("The parties' claims, tested", R - X, 84, "serifSemi");
  head.forEach((l, k) => { s += text(X, 178 + k * 92, l, 84, "serifSemi"); });
  // the strip: one seal per claim, in page order, its party's chip and claimant under it
  const n = claims.length, cw = (R - X) / n, cy = 360, r = 92;
  claims.forEach((c, k) => {
    const cx = X + cw * (k + 0.5);
    s += stamp(cx, cy, r, c.verdict, VERDICT[c.vclass], { ring: false, rot: k % 2 ? 6 : -7 });
    const surname = c.person.split(",")[0];
    s += chip(c.code, cx - textWidth(surname, 19, "sansSemi") / 2 - 34, 497, 26, colourOf(c.code));
    s += text(cx + 17, 517, surname, 19, "sansSemi", { anchor: "middle" });
    s += text(cx, 541, c.party === "uMkhonto weSizwe Party" ? "MK Party" : c.party, 15, "sans", { fill: C.ink3, anchor: "middle" });
  });
  return s + "</svg>";
}

// ---------- 2. one claim ----------
function claimCard(c) {
  let s = frame("claim", "The parties' claims, tested", `Tested ${c.tested}. Quoted from ${c.source}.`);
  const col = colourOf(c.code);
  s += chip(c.code, X + 3, 86, 58, col);
  s += text(X + 82, 112, c.party, 27, "serifSemi");
  s += text(X + 82, 140, fitText(c.person, 560, 18, "sans", 14).text, 18, "sans", { fill: C.ink2 });
  // the quote, as large as fits five lines in its column; past that, the marked cut
  const QX = X + 52, QW = 690;
  let q = c.quote, fs, lines;
  const fit = t => { for (let f = 54; f >= 33; f--) { const L = wrapText(t, QW, f, "serifSemi"); if (L.length * f * 1.22 <= 340 && L.length <= 5) return [f, L]; } return null; };
  let got = fit(q);
  if (!got || got[0] < 36) { if (SHORT[c.i]) { q = SHORT[c.i]; got = fit(q); } }
  [fs, lines] = got;
  const lh = fs * 1.22, top = 182 + (360 - lines.length * lh) / 2 + fs * 0.8;
  s += text(X - 6, top + fs * 0.62, "“", fs * 2.6, "serifSemi", { fill: col });
  s += lines.map((l, k) => text(QX, top + k * lh, l + (k === lines.length - 1 ? "”" : ""), fs, "serifSemi")).join("");
  s += stamp(990, 322, 158, c.verdict, VERDICT[c.vclass]);
  return s + "</svg>";
}

// ---------- 3a. article: Nobody will win Johannesburg ----------
// headline on the left, the seat ranges against the majority line on the right
function nobodyWillWin() {
  const nw = page("nobody-will-win.html");
  const pAlone = token(nw, "p_alone");
  let s = frame("article", "Article", `Published 8 August 2026. Figures as of ${generated}.`);
  const head = wrapText("Nobody will win Johannesburg", 470, 76, "serifSemi");
  head.forEach((l, k) => { s += text(X, 168 + k * 84, l, 76, "serifSemi"); });
  const hy = 168 + (head.length - 1) * 84 + 70;
  wrapText(`A single party reaches a majority on its own: ${pAlone} chance.`, 450, 25, "sans")
    .forEach((l, k) => { s += text(X, hy + k * 34, l, 25, "sans", { fill: C.ink2 }); });
  // ranges: the six largest by middle, ties by name; 5th to 95th percentile, the middle marked
  const rows = ranges.filter(r => r.code !== "OTHERS").sort((a, b) => b.m - a.m || F(a.code).name.localeCompare(F(b.code).name)).slice(0, 6);
  const gx = 640, gw = R - gx, max = 150, sx = v => gx + gw * v / max;
  const top = 120, pitch = 64;
  const maj = 136;
  s += rect(sx(maj) - 1, top - 30, 2.5, rows.length * pitch + 20, C.ink);
  s += text(sx(maj), top - 38, maj + " for a majority", 16, "sansSemi", { anchor: "end" });
  rows.forEach((r, k) => {
    const y = top + k * pitch, col = colourOf(r.code);
    s += text(gx, y + 4, F(r.code).name, 18, "sansSemi", { fill: C.ink2 });
    s += rect(gx, y + 22, gw, 1, C.rule);
    s += rect(sx(r.p5), y + 14, sx(r.p95) - sx(r.p5), 17, col, ` rx="8.5" fill-opacity="0.85"`);
    s += rect(sx(r.m) - 1.5, y + 8, 3, 29, C.ink);
    s += text(sx(r.p95) + 8, y + 28, String(r.m), 17, "sansSemi");
  });
  s += text(gx, top + rows.length * pitch + 6, "Seats: middle, and the range in 9 of 10 simulations", 14, "sans", { fill: C.ink3 });
  return s + "</svg>";
}

// ---------- 3b. article: Laingsburg, 2021 ----------
// headline across the top, the seven seats as the visual
function laingsburg() {
  const lb = page("laingsburg-2021.html");
  const daShare = token(lb, "hist_laingsburg_da_share");
  let s = frame("article", "Article · the precedent", `Published 8 August 2026. Seats from the Electoral Commission's 2021 calculation.`);
  const head = wrapText("Laingsburg, 2021: the whole mechanism in seven seats", R - X, 58, "serifSemi");
  head.forEach((l, k) => { s += text(X, 136 + k * 66, l, 58, "serifSemi"); });
  // the result, from the IEC report (law/SUMMARY.md): ANC 2, DA 3 (all wards, no list seats), KDF 1, PA 1
  const seats = [["DA", "DA", 3], ["ANC", "ANC", 2], ["KDF", "Karoo Democratic Force", 1], ["PA", "PA", 1]];
  const sq = 96, gap = 14, y = 262;
  let x = X;
  for (const [code, name, n] of seats) {
    const col = code === "KDF" ? "#9aa09a" : colourOf(code);
    for (let i = 0; i < n; i++) {
      s += rect(x + i * (sq + gap), y, sq, sq, col, ` rx="10"`);
      if (code === "DA") s += text(x + i * (sq + gap) + sq / 2, y + sq / 2 + 7, "ward", 20, "sansSemi", { fill: "#ffffff", anchor: "middle" });
    }
    const gw = n * sq + (n - 1) * gap;
    s += text(x, y + sq + 32, name === "Karoo Democratic Force" ? "KDF" : name, 20, "sansSemi");
    x += gw + gap * 2.4;
  }
  // the DA's three: its share, its entitlement
  wrapText(`The DA won 3 of 4 wards on ${daShare} of the vote, a share worth 2 seats. It kept all 3 and got no list seats.`, R - X, 23.5, "sans")
    .forEach((l, k) => { s += text(X, y + sq + 92 + k * 34, l, 23.5, "sans", { fill: C.ink2 }); });
  return s + "</svg>";
}

// ---------- 4. the forecast page: headline left, the striped map right ----------
function forecastMap() {
  let m = readFileSync(resolve(REPO, "site/forecast.html"), "utf8");
  const i = m.indexOf("<pattern"), a = m.lastIndexOf("<svg", i), b = m.indexOf("</svg>", i);
  m = m.slice(a, b);
  const inner = m.slice(m.indexOf(">") + 1)
    .replace(/<text[\s\S]*?<\/text>/g, "")
    .replace(/<g transform="translate\(532,548\)">[\s\S]*?<\/g>/, "")
    .replace(/var\(--paper\)/g, C.paper);
  let s = frame("forecast", "Our forecast · Johannesburg, 4 November 2026", `Forecast of ${generated}. Johannesburg council, 270 seats, vote on 4 November 2026.`);
  const head = wrapText("Who governs Johannesburg", 440, 62, "serifSemi");
  head.forEach((l, k) => { s += text(X, 160 + k * 70, l, 62, "serifSemi"); });
  // the two parties' chances of most seats, from the page
  const yA = 160 + head.length * 70 + 20;
  const pa = token(fc, "p_anc_largest") || token(page("nobody-will-win.html"), "p_anc_largest");
  const pd = token(fc, "p_da_largest") || token(page("nobody-will-win.html"), "p_da_largest");
  s += text(X, yA, "Most seats:", 20, "sans", { fill: C.ink3 });
  s += text(X, yA + 34, `ANC ${pa} chance`, 26, "sansSemi") + text(X, yA + 68, `DA ${pd} chance`, 26, "sansSemi");
  // the map, as the page draws it: solid where one party wins most simulations, striped where it does not
  const mh = 470, mw = mh * 840 / 596, mx = R + 12 - mw;
  s += `<svg x="${n1(mx)}" y="${(FOOT - mh) / 2 + 20}" width="${n1(mw)}" height="${n1(mh)}" viewBox="0 0 840 596">${inner}</svg>`;
  wrapText("Striped: no party wins the ward in most simulations.", 400, 16, "sans")
    .forEach((l, k) => { s += text(X, yA + 112 + k * 21, l, 16, "sans", { fill: C.ink3 }); });
  return s + "</svg>";
}

// ---------- 5. the interactive: a solid map (a prediction) and the call to make one ----------
function interactive() {
  const { A: spec } = specs();
  const g = A.geom;
  let s = frame("interactive", "Your prediction", "Johannesburg council, 270 seats, vote on 4 November 2026.");
  // the map on the left, every ward one party's colour; every fourth ward left open
  const mw = 600, sc = mw / g.W, mh = g.H * sc;
  const my = (FOOT - mh) / 2 + 24;
  let paths = "";
  g.wards.forEach((wd, k) => {
    const open = k % 4 === 1;
    paths += `<path d="${wd.path}" fill="${open ? C.paper2 : F(spec.calls[k]).colour}" stroke="${open ? "#5a615b" : C.paper}" stroke-width="${n1((open ? 1.4 : 0.8) / sc)}"${open ? ` stroke-dasharray="${n1(4 / sc)} ${n1(3 / sc)}"` : ""} stroke-linejoin="round"/>`;
  });
  s += `<g transform="translate(${X - 8} ${n1(my)}) scale(${sc.toFixed(4)})">${paths}</g>`;
  const tx = 676;
  const head = wrapText("Make your prediction", R - tx, 72, "serifSemi");
  head.forEach((l, k) => { s += text(tx, 190 + k * 80, l, 72, "serifSemi"); });
  const y = 190 + head.length * 80 + 18;
  ["Pick a winner in every ward.", "The seat law fills the council.", "We score it against the result."]
    .forEach((l, k) => { s += text(tx, y + k * 36, l, 24, "sans", { fill: C.ink2 }); });
  s += rect(tx, y + 132, textWidth("Make yours at " + SITE, 18, "monoSemi") + 36, 48, KIND.interactive, ` rx="24"`);
  s += text(tx + 18, y + 162, "Make yours at " + SITE, 18, "monoSemi", { fill: C.paper });
  return s + "</svg>";
}

// ---------- write ----------
const cards = [
  ["og-claims.png", claimsIndex(), "/claims", "Claims index: headline and the five verdicts in page order."],
  ...claims.map(c => [`og-claim-${c.i + 1}-${c.code.toLowerCase()}.png`, claimCard(c), "/claims#" + (c.i + 1),
    `Claim ${c.i + 1}: ${c.person.split(",")[0]}. Verdict as on the page.`]),
  ["og-article-nobody-will-win.png", nobodyWillWin(), "/nobody-will-win", "Article: seat ranges against the majority line. Ranges and the 0.1% are today's values (data-current / span text, 9 October 2026)."],
  ["og-article-laingsburg.png", laingsburg(), "/laingsburg-2021", "Article: the seven Laingsburg seats (IEC 2021 result; 23% is the page's token)."],
  ["og-forecast.png", forecastMap(), "/forecast", "Forecast: the page's striped ward map and the most-seats chances, today's values (9 October 2026)."],
  ["og-interactive.png", interactive(), "/your-forecast", "Interactive: a solid map is a prediction. Ward calls are the share fixture's reader A, not a real entry."],
];
const pngs = [];
for (const [name, svg] of cards) {
  const png = await toPNG(svg);
  writeFileSync(resolve(OUT, name), png);
  pngs.push(png);
  console.log("wrote", name);
}

// the contact sheet: the cards as a feed would show them, two across, each
// scaled to half size with its caption, through the same raster path
const cw = 600, ch = 315, pad = 36, capH = 64, cols = 2;
const rows = Math.ceil(cards.length / cols);
const SW = cols * cw + (cols + 1) * pad, SH = 110 + rows * (ch + capH + pad);
let sheet = `<svg xmlns="http://www.w3.org/2000/svg" width="${SW}" height="${SH}" viewBox="0 0 ${SW} ${SH}">` + rect(0, 0, SW, SH, "#0b0d0c");
sheet += text(pad, 58, "Share images, item 9 mock-ups: a feed of them side by side", 26, "serifSemi");
sheet += text(pad, 88, "Figures are today's values read from the built pages' data-current (or span text), 9 October 2026; the build takes them from tokens.", 15, "sans", { fill: C.ink3 });
cards.forEach(([name, , path, cap], k) => {
  const x = pad + (k % cols) * (cw + pad), y = 110 + Math.floor(k / cols) * (ch + capH + pad);
  sheet += rect(x - 1, y - 1, cw + 2, ch + 2, "#2a2f2b", ` rx="13"`);
  sheet += `<image x="${x}" y="${y}" width="${cw}" height="${ch}" href="data:image/png;base64,${Buffer.from(pngs[k]).toString("base64")}"/>`;
  sheet += text(x, y + ch + 24, "joburg.whysoserious.city" + path, 15, "monoSemi", { fill: C.ink2 });
  wrapText(cap, cw, 14, "sans").slice(0, 2).forEach((l, j) => { sheet += text(x, y + ch + 44 + j * 18, l, 14, "sans", { fill: C.ink3 }); });
});
sheet += "</svg>";
writeFileSync(resolve(OUT, "contact-sheet.png"), await toPNG(sheet));
console.log("wrote contact-sheet.png");
