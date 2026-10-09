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
function frame(kind, kicker, dateLine, { footRule = true, logo = true } = {}) {
  let s = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">` + rect(0, 0, W, H, C.paper);
  s += rect(0, 0, W, 8, KIND[kind]);
  s += mono(X, 56, kicker, 17, KIND[kind]);
  if (footRule) s += rect(X, FOOT, R - X, 1, C.rule);
  s += text(X, 604, dateLine, 17, "sans", { fill: C.ink3 });
  const bh = 50, bw = brandWidth(A, bh);
  if (logo) s += brand(R - bw + 4, 572, bh);
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
// One claim per party (owner, 2026-10-09). Where a party has several, the
// first on the page stands for it. The strip lays out however many parties
// there are, so a fifth (the EFF claim being researched) needs no layout change.
const perParty = claims.filter((c, k) => claims.findIndex(d => d.code === c.code) === k);
const SHORT_NAME = { DA: "DA", ANC: "ANC", MK: "MK Party", ASA: "ActionSA", EFF: "EFF" };
function claimsIndex(list = perParty) {
  let s = frame("claim", "The campaign arithmetic", `One claim per party, each tested against the forecast. Latest tested ${list.map(c => c.tested).sort((a, b) => Date.parse(b) - Date.parse(a))[0]}.`);
  s += text(X, 150, "The parties' claims, tested", 80, "serifSemi");
  const n = list.length, cw = (R - X) / Math.max(n, 4), x0 = X + ((R - X) - cw * n) / 2;
  const r = Math.min(80, cw * 0.36), cy = 278;
  list.forEach((c, k) => {
    const cx = x0 + cw * (k + 0.5);
    s += stamp(cx, cy, r, c.verdict, VERDICT[c.vclass], { ring: false, rot: k % 2 ? 6 : -7 });
    const ls = 68;
    s += chip(c.code, cx - ls / 2, 384, ls, colourOf(c.code));
    s += text(cx, 498, fitText(SHORT_NAME[c.code] || c.party, cw - 12, 32, "sansBold", 22).text, 32, "sansBold", { anchor: "middle" });
    s += text(cx, 530, fitText(c.person.split(",")[0], cw - 12, 19, "sans", 15).text, 19, "sans", { fill: C.ink2, anchor: "middle" });
  });
  return s + "</svg>";
}

// ---------- 2. one claim ----------
// The site's logo large at the top right, over the stamp (owner: "make our logo much bigger").
function claimCard(c) {
  let s = frame("claim", "The parties' claims, tested", `Tested ${c.tested}. Quoted from ${c.source}.`, { logo: false });
  const col = colourOf(c.code);
  const bh = 120, bw = brandWidth(A, bh);
  s += brand(R - bw + 6, 26, bh);
  const ls = 96;
  s += chip(c.code, X + 3, 82, ls, col);
  s += text(X + ls + 28, 120, c.party, 32, "serifSemi");
  s += text(X + ls + 28, 154, fitText(c.person, 640 - ls, 19, "sans", 14).text, 19, "sans", { fill: C.ink2 });
  // the quote, as large as fits five lines in its column; past that, the marked cut
  const QX = X + 52, QW = 690, QTOP = 214, QH = 318;
  let q = c.quote, fs, lines;
  const fit = t => { for (let f = 50; f >= 32; f--) { const L = wrapText(t, QW, f, "serifSemi"); if (L.length * f * 1.22 <= QH && L.length <= 5) return [f, L]; } return null; };
  let got = fit(q);
  if (!got || got[0] < 36) { if (SHORT[c.i]) { q = SHORT[c.i]; got = fit(q); } }
  [fs, lines] = got;
  const lh = fs * 1.22, top = QTOP + (QH - lines.length * lh) / 2 + fs * 0.8;
  s += text(X - 6, top + fs * 0.62, "“", fs * 2.6, "serifSemi", { fill: col });
  s += lines.map((l, k) => text(QX, top + k * lh, l + (k === lines.length - 1 ? "”" : ""), fs, "serifSemi")).join("");
  s += stamp(992, 366, 150, c.verdict, VERDICT[c.vclass]);
  return s + "</svg>";
}

// ---------- 3a. article: Nobody will win Johannesburg ----------
// headline on the left in three set lines, the seat ranges against the majority line on the right
function nobodyWillWin() {
  const nw = page("nobody-will-win.html");
  const pAlone = token(nw, "p_alone");
  let s = frame("article", "Article", `Published 8 August 2026. Figures as of ${generated}.`);
  ["Nobody", "will win", "Johannesburg"].forEach((l, k) => { s += text(X, 168 + k * 86, l, 78, "serifSemi"); });
  s += text(X, 168 + 2 * 86 + 74, `Chance of 1 party majority: ${pAlone}`, 28, "sansSemi", { fill: C.ink2 });
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

// ---------- 3b. article: Laingsburg ----------
// Two aligned 100% bars: the vote, and the seats split into ward and list.
// TYPED, not tokens: the IEC's Seat Calculation Detail for WC051, LGE 2021
// (law/sources/iec-lge2021-seat-calculation-detail-wc051-laingsburg.pdf).
// The page carries a token for the DA's share only.
const LB = [  // [code, label, votes, ward seats, list seats], in vote order; the rest pooled
  ["ANC", "ANC", 1694, 1, 1], ["KDF", "KDF", 1576, 0, 1], ["DA", "DA", 1530, 3, 0], ["PA", "PA", 895, 0, 1],
  ["OTHER", "Others", 395 + 248 + 74 + 41, 0, 0],
];
function laingsburg() {
  let s = frame("article", "Article · the precedent", "Published 8 August 2026. Votes and seats: the IEC's 2021 Laingsburg seat calculation.");
  s += text(X, 128, "Laingsburg and the quirk about to hit Joburg.", 50, "serifSemi");
  s += text(X, 172, "Ward wins count more than proportional vote", 26, "sans", { fill: C.ink2 });
  const votes = LB.reduce((a, r) => a + r[2], 0), seats = LB.reduce((a, r) => a + r[3] + r[4], 0);
  const LX = X + 96, BW = R - LX, BH = 70;
  const col = code => code === "KDF" ? "#9aa09a" : code === "OTHER" ? "#464d47" : colourOf(code);
  const pct = v => (Math.round(v * 1000) / 10).toFixed(1).replace(/\.0$/, "") + "%";
  // the vote bar
  const vy = 222;
  s += text(X, vy + 44, "Votes", 22, "sansSemi", { fill: C.ink2 });
  let x = LX;
  for (const [code, label, v] of LB) {
    const w = BW * v / votes;
    s += rect(x, vy, w - 2, BH, col(code));
    const t = `${label} ${pct(v / votes)}`;
    const ink = code === "KDF" || code === "PA" ? C.paper : "#ffffff";
    if (textWidth(t, 19, "sansSemi") < w - 16) s += text(x + 10, vy + 44, t, 19, "sansSemi", { fill: ink });
    else if (textWidth(label, 17, "sansSemi") < w - 12) s += text(x + 8, vy + 30, label, 17, "sansSemi", { fill: ink }) + text(x + 8, vy + 54, pct(v / votes), 17, "sans", { fill: ink });
    x += w;
  }
  // the seat bar: one cell per seat, ward seats solid, list seats tinted
  const sy = 330;
  s += text(X, sy + 44, "Seats", 22, "sansSemi", { fill: C.ink2 });
  x = LX;
  const cell = BW / seats;
  for (const [code, label, , ward, list] of LB) {
    const n = ward + list;
    if (!n) continue;
    for (let i = 0; i < n; i++) {
      const isWard = i < ward;
      s += rect(x + i * cell, sy, cell - 2, BH, col(code), isWard ? "" : ` fill-opacity="0.45"`);
      s += text(x + i * cell + cell / 2, sy + 44, isWard ? "ward" : "list", 18, "sansSemi", { fill: "#ffffff", anchor: "middle" });
    }
    s += text(x, sy + BH + 26, `${label} ${n} of ${seats}`, 18, "sansSemi");
    x += n * cell;
  }
  const da = LB.find(r => r[0] === "DA");
  s += text(X, 498, `The DA: ${pct(da[2] / votes)} of the vote, 3 of ${seats} seats (${pct(3 / seats)}), all wards.`, 22, "sans", { fill: C.ink });
  return s + "</svg>";
}

// ---------- 4. the forecast page: headline left, the striped map right ----------
// The page's map, with its contested wards' stripes drawn as geometry. The
// page fills each contested ward twice: a solid grey base, then a pattern of
// parallel stripes (one direction, rotate(45), 7-unit tile). resvg renders a
// rotated pattern tile by tile, and at card scale the anti-aliased tile
// edges leave hairline seams through which the grey base shows; the seams
// across the stripes read as a second hatch direction. Here each contested
// ward is clipped to itself and filled with long parallel bands in the
// pattern's colours and widths, over a base in its widest band's colour, so
// there are no tiles and no seams.
function stripedMap(svgText) {
  const pats = {};
  for (const [, id, body] of svgText.matchAll(/<pattern id="([^"]+)"[^>]*>([\s\S]*?)<\/pattern>/g))
    pats[id] = [...body.matchAll(/x1="([\d.]+)"[^>]*stroke="(#[0-9A-Fa-f]{6})" stroke-width="([\d.]+)"/g)].map(([, x, c, w]) => ({ x: +x, c, w: +w }));
  const step = 7, k45 = Math.SQRT1_2;
  let out = "", defs = "", n = 0;
  for (const p of svgText.match(/<path [^>]*>/g)) {
    const d = /d="([^"]+)"/.exec(p)[1];
    const fill = /fill="([^"]+)"/.exec(p)[1];
    const pm = /url\(#([^)]+)\)/.exec(fill);
    if (!pm) {
      if (fill === "#9aa09a" && svgText.includes(`<path d="${d}" fill="url(`)) continue;  // the base under a stripe overlay
      out += `<path d="${d}" fill="${fill}" stroke="${C.paper}" stroke-width="0.8" stroke-linejoin="round"/>`;
      continue;
    }
    const bands = pats[pm[1]];
    const nums = d.match(/-?[\d.]+/g).map(Number);
    const xs = nums.filter((_, i) => i % 2 === 0), ys = nums.filter((_, i) => i % 2 === 1);
    // the ward's extent across the stripes, in the pattern's rotated frame: u = x cos45 + y sin45
    const us = xs.map((x, i) => (x + ys[i]) * k45), vs = xs.map((x, i) => (ys[i] - x) * k45);
    const u0 = Math.floor(Math.min(...us) / step) - 1, u1 = Math.ceil(Math.max(...us) / step) + 1;
    const v0 = Math.min(...vs) - 10, v1 = Math.max(...vs) + 10;
    const widest = bands.reduce((a, b) => (b.w > a.w ? b : a));
    const id = "cw" + n++;
    defs += `<clipPath id="${id}"><path d="${d}"/></clipPath>`;
    let g = `<rect x="${n1(Math.min(...xs) - 2)}" y="${n1(Math.min(...ys) - 2)}" width="${n1(Math.max(...xs) - Math.min(...xs) + 4)}" height="${n1(Math.max(...ys) - Math.min(...ys) + 4)}" fill="${widest.c}"/>`;
    g += `<g transform="rotate(45)">`;
    for (let k = u0; k <= u1; k++) for (const b of bands) if (b !== widest)
      g += `<rect x="${n1(k * step + b.x - b.w / 2)}" y="${n1(v0)}" width="${b.w.toFixed(2)}" height="${n1(v1 - v0)}" fill="${b.c}"/>`;
    g += "</g>";
    out += `<g clip-path="url(#${id})">${g}</g><path d="${d}" fill="none" stroke="${C.paper}" stroke-width="0.8" stroke-linejoin="round"/>`;
  }
  return `<defs>${defs}</defs>` + out;
}
function forecastMap() {
  const m = (() => { const i = fc.indexOf("<pattern"), a = fc.lastIndexOf("<svg", i), b = fc.indexOf("</svg>", i); return fc.slice(a, b); })();
  const inner = stripedMap(m.replace(/<g transform="translate\(532,548\)">[\s\S]*?<\/g>/, ""));
  let s = frame("forecast", "Our forecast · Johannesburg, 4 November 2026", `Forecast of ${generated}. Johannesburg council, 270 seats, vote on 4 November 2026.`);
  const head = wrapText("Who governs Johannesburg?", 440, 62, "serifSemi");
  head.forEach((l, k) => { s += text(X, 160 + k * 70, l, 62, "serifSemi"); });
  const yA = 160 + head.length * 70 + 20;
  const pa = token(fc, "p_anc_largest") || token(page("nobody-will-win.html"), "p_anc_largest");
  const pd = token(fc, "p_da_largest") || token(page("nobody-will-win.html"), "p_da_largest");
  s += text(X, yA, "Most seats:", 20, "sans", { fill: C.ink3 });
  s += text(X, yA + 34, `ANC ${pa} chance`, 26, "sansSemi") + text(X, yA + 68, `DA ${pd} chance`, 26, "sansSemi");
  // the key: a swatch of two-colour stripes, and the words
  const ky = yA + 108;
  s += `<defs><clipPath id="key"><rect x="${X}" y="${ky}" width="34" height="22" rx="3"/></clipPath></defs><g clip-path="url(#key)">` + rect(X, ky, 34, 22, "#1B7A3D") +
    `<g transform="rotate(45 ${X + 17} ${ky + 11})">` + [-4, -2, 0, 2, 4].map(k => rect(X + 17 + k * 7 - 1.6, ky - 30, 3.2, 82, "#1B5EA8")).join("") + "</g></g>";
  s += text(X + 46, ky + 17, "Striped: contested wards", 19, "sans", { fill: C.ink2 });
  const mh = 470, mw = mh * 840 / 596, mx = R + 12 - mw;
  s += `<svg x="${n1(mx)}" y="${(FOOT - mh) / 2 + 20}" width="${n1(mw)}" height="${n1(mh)}" viewBox="0 0 840 596">${inner}</svg>`;
  return s + "</svg>";
}

// ---------- 5. the interactive: a solid map (a prediction) and the call to make one ----------
function interactive() {
  const { A: spec } = specs();
  const g = A.geom;
  let s = frame("interactive", "Your prediction", "Johannesburg council, 270 seats, vote on 4 November 2026.");
  const mw = 600, sc = mw / g.W, mh = g.H * sc;
  const my = (FOOT - mh) / 2 + 24;
  let paths = "";
  g.wards.forEach((wd, k) => {
    const open = k % 4 === 1;
    paths += `<path d="${wd.path}" fill="${open ? C.paper2 : F(spec.calls[k]).colour}" stroke="${open ? "#5a615b" : C.paper}" stroke-width="${n1((open ? 1.4 : 0.8) / sc)}"${open ? ` stroke-dasharray="${n1(4 / sc)} ${n1(3 / sc)}"` : ""} stroke-linejoin="round"/>`;
  });
  s += `<g transform="translate(${X - 8} ${n1(my)}) scale(${sc.toFixed(4)})">${paths}</g>`;
  const tx = 676;
  s += text(tx, 196, "Know Politics?", 64, "serifSemi");
  const y = 258;
  wrapText("Pick your winners, seal your prediction and let's see if you can beat us on election day.", R - tx, 27, "sans")
    .forEach((l, k) => { s += text(tx, y + k * 38, l, 27, "sans", { fill: C.ink2 }); });
  s += rect(tx, 446, textWidth("Make yours at " + SITE, 18, "monoSemi") + 36, 48, KIND.interactive, ` rx="24"`);
  s += text(tx + 18, 476, "Make yours at " + SITE, 18, "monoSemi", { fill: C.paper });
  return s + "</svg>";
}

// ---------- write ----------
const cards = [
  ["og-claims.png", claimsIndex(), "/claims", "Claims index: one claim per party, the first on the page for each (Zille's red-line claim, the second DA claim, is left out)."],
  ...claims.map(c => [`og-claim-${c.i + 1}-${c.code.toLowerCase()}.png`, claimCard(c), "/claims#" + (c.i + 1),
    `Claim ${c.i + 1}: ${c.person.split(",")[0]}. Verdict as on the page.`]),
  ["og-article-nobody-will-win.png", nobodyWillWin(), "/nobody-will-win", "Article: seat ranges against the majority line. Ranges and the 0.1% (token p_alone) are today's values, 9 October 2026."],
  ["og-article-laingsburg.png", laingsburg(), "/laingsburg-2021", "Article: vote and seats as two 100% bars. Votes and seats typed from the IEC's 2021 WC051 seat calculation; the page has no tokens for them yet."],
  ["og-forecast.png", forecastMap(), "/forecast", "Forecast: the page's ward map, contested wards as parallel stripes drawn as geometry; chances are today's values, 9 October 2026."],
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
