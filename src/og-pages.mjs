#!/usr/bin/env node
// The site's share images, one per designed page (src/og_pages.py builds the
// specs; OG-IMPLEMENTATION-SPEC.md, audits/2026-10-09-site-batch/). Each spec
// carries every figure and word as text; this module holds the layouts'
// constants only (positions, sizes, the page-kind colours) and draws with
// share-card.js's primitives, the owner's stamps (src/stamps/) and logos.
// Not served.
//
//   node src/og-pages.mjs <specs.json | -> <out-dir>
//
// Writes <out-dir>/<slug>-<name>.png for each spec, where <name> is the first
// 12 hex digits of sha256(SVG, the card faces, resvg's version) written as
// letters a-p, and prints {slug: file name} as JSON. Exits non-zero on any
// failure.
import { readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { toPNG } from "./og-raster-node.mjs";
import { FACES } from "../interactive/tools/card_fonts.mjs";
import * as SC from "../interactive/js/share-card.js";

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const { C, text, rect, brand, chip, brandWidth, stampOf, stampSVG, textWidth, fitText, wrapText } = SC;
const [W, H] = SC.SIZES.link;
const X = 56, R = W - 56;
const n1 = v => Number(v.toFixed(1));

// ---------- the frame: a bar in the page kind's colour, our logo large at the
// top right, the headline's cap line level with it, the date line at the foot
// (owner, 2026-10-09: "keep logo same place big and top right for all") ----------
const KIND = { claims: "#d9954f", article: "#7aa6d6", forecast: "#eceee9", interactive: "#b98ad6" };
const KIND_BAR = 8;
const FOOT = 560, FOOT_TEXT = 606, FOOT_FS = 21;
const TOP = 40;
const LOGO_H = 120;
const ASSETS = { brand: SC.brandOf(readFileSync(resolve(REPO, "src/brand/logo.svg"), "utf8")), logos: {} };
const LOGO_W = brandWidth(ASSETS, LOGO_H), LOGO_X = R - LOGO_W + 6;
const HEAD_MAX = LOGO_X - X - 36;                  // a line level with the logo stops short of it
const capBase = fs => TOP + fs * 0.7;              // a first line whose cap height starts at TOP
const HEAD_LEADING = 1.08;

function frame(kind, dateLine) {
  let s = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">` + rect(0, 0, W, H, C.paper);
  s += rect(0, 0, W, KIND_BAR, KIND[kind]);
  s += brand(ASSETS, LOGO_X, TOP, LOGO_H);
  s += rect(X, FOOT, R - X, 1, C.rule);
  s += text(X, FOOT_TEXT, fitText(dateLine, R - X, FOOT_FS, "sans", FOOT_FS * 0.75).text, FOOT_FS, "sans", { fill: C.ink3 });
  return s;
}

// The headline, top left: the largest size from `big` down to `least` at which
// it takes at most `lines` lines of `maxW`. Returns { svg, last } (the last
// baseline). A headline that will not fit at `least` is refused.
function headline(words, maxW, big, least, lines) {
  for (let fs = big; fs >= least; fs -= 2) {
    const L = wrapText(words, maxW, fs, "serifSemi");
    if (L.length <= lines) {
      return { svg: L.map((l, k) => text(X, capBase(fs) + k * fs * HEAD_LEADING, l, fs, "serifSemi")).join(""),
        last: capBase(fs) + (L.length - 1) * fs * HEAD_LEADING, fs };
    }
  }
  throw new Error(`headline "${words}" does not fit ${lines} lines at ${least}px`);
}

// An owner's stamp centred on (cx, cy), `h` tall: share-card.js stampSVG, the
// one function that places a stamp (its ids prefixed by `prefix`).
const STAMPS = {};
function stamp(file, prefix, cx, cy, h) {
  STAMPS[file] ??= stampOf(readFileSync(resolve(REPO, "src/stamps", file), "utf8"));
  const st = STAMPS[file];
  const [, , vw, vh] = st.viewBox.split(/\s+/).map(Number);
  return stampSVG(st, prefix, cx - h * vw / vh / 2, cy - h / 2, h);
}

function logoOf(file) {
  if (!file) return null;
  return "data:image/png;base64," + readFileSync(resolve(REPO, "site/logos", file)).toString("base64");
}

// ---------- /claims: the headline, then one badge per party ----------
const CLAIM_HEAD = { big: 74, least: 52, lines: 2 };
const CLAIM_STRIP = { minCols: 4, badge: 168, cy: 300, chip: 56, chipTop: 396, name: 30, nameY: 494, who: 19, whoY: 526 };
function claims(spec) {
  let s = frame("claims", spec.date_line);
  s += headline(spec.headline, HEAD_MAX, CLAIM_HEAD.big, CLAIM_HEAD.least, CLAIM_HEAD.lines).svg;
  const n = spec.items.length, cw = (R - X) / Math.max(n, CLAIM_STRIP.minCols), x0 = X + ((R - X) - cw * n) / 2;
  const bh = Math.min(CLAIM_STRIP.badge, cw * 0.92);
  spec.items.forEach((c, k) => {
    const cx = x0 + cw * (k + 0.5);
    s += stamp(c.badge, "v" + k, cx, CLAIM_STRIP.cy, bh);
    const logo = logoOf(c.logo);
    if (logo) ASSETS.logos[c.code] = logo;
    s += chip({ code: c.code, colour: c.colour, logo: !!logo }, cx - CLAIM_STRIP.chip / 2, CLAIM_STRIP.chipTop, CLAIM_STRIP.chip, ASSETS);
    s += text(cx, CLAIM_STRIP.nameY, fitText(c.party, cw - 12, CLAIM_STRIP.name, "sansBold", 22).text, CLAIM_STRIP.name, "sansBold", { anchor: "middle" });
    s += text(cx, CLAIM_STRIP.whoY, fitText(c.speaker, cw - 12, CLAIM_STRIP.who, "sans", 15).text, CLAIM_STRIP.who, "sans", { fill: C.ink2, anchor: "middle" });
  });
  return s + "</svg>";
}

// ---------- an article: the headline; the seat ranges where it has them ----------
const ART_HEAD = { big: 88, least: 52, lines: 4 };
const ART_HEAD_BESIDE = { big: 80, least: 48, lines: 3 };
const RANGES = { x: 660, top: 216, pitch: 52, name: 17, bar: 16, value: 17, note: 14, lead: 30 };
function article(spec) {
  let s = frame("article", spec.date_line);
  if (!spec.ranges) {
    // headline only: as large as fits the page under the logo's line
    s += headline(spec.headline, HEAD_MAX, ART_HEAD.big, ART_HEAD.least, ART_HEAD.lines).svg;
    return s + "</svg>";
  }
  const g = spec.ranges;
  const h = headline(spec.headline, RANGES.x - X - 30, ART_HEAD_BESIDE.big, ART_HEAD_BESIDE.least, ART_HEAD_BESIDE.lines);
  s += h.svg;
  s += text(X, h.last + 96, fitText(g.lead, RANGES.x - X - 30, RANGES.lead, "sansSemi", 20).text, RANGES.lead, "sansSemi", { fill: C.ink2 });
  const gx = RANGES.x, gw = R - gx, sx = v => gx + gw * Number(v) / g.scale;
  const top = RANGES.top, maj = Number(g.majority);
  s += rect(sx(maj) - 1, top - 24, 2.5, g.rows.length * RANGES.pitch + 12, C.ink);
  s += text(sx(maj), top - 32, g.majority_label, 16, "sansSemi", { anchor: "end" });
  g.rows.forEach((r, k) => {
    const y = top + k * RANGES.pitch;
    s += text(gx, y + 4, r.name, RANGES.name, "sansSemi", { fill: C.ink2 });
    s += rect(gx, y + 20, gw, 1, C.rule);
    s += rect(sx(r.p5), y + 12, Math.max(2, sx(r.p95) - sx(r.p5)), RANGES.bar, r.colour, ` rx="8" fill-opacity="0.85"`);
    s += rect(sx(r.m) - 1.5, y + 6, 3, 28, C.ink);
    s += text(sx(r.p95) + 8, y + 26, r.m, RANGES.value, "sansSemi");
  });
  s += text(gx, top + g.rows.length * RANGES.pitch + 4, g.note, RANGES.note, "sans", { fill: C.ink3 });
  return s + "</svg>";
}

// ---------- /forecast: the headline and the figures left, the striped map right ----------
// The page's map, its contested wards' stripes drawn as geometry. The page
// fills each contested ward twice: a solid grey base, then a pattern of
// parallel stripes (one direction, rotate(45), 7-unit tile). resvg renders a
// rotated pattern tile by tile, and at card scale the tile edges leave
// hairline seams through which the base shows. Here each contested ward is
// clipped to itself and filled with long parallel bands in the pattern's
// colours and widths, over a base in its widest band's colour.
const STRIPE_STEP = 7;
function stripedMap(svgText) {
  const pats = {};
  for (const [, id, body] of svgText.matchAll(/<pattern id="([^"]+)"[^>]*>([\s\S]*?)<\/pattern>/g))
    pats[id] = [...body.matchAll(/x1="([\d.]+)"[^>]*stroke="(#[0-9A-Fa-f]{6})" stroke-width="([\d.]+)"/g)].map(([, x, c, w]) => ({ x: +x, c, w: +w }));
  const k45 = Math.SQRT1_2;
  let out = "", defs = "", n = 0;
  const overlaid = new Set([...svgText.matchAll(/<path d="([^"]+)" fill="url\(/g)].map(m => m[1]));
  for (const p of svgText.match(/<path [^>]*>/g)) {
    const d = /d="([^"]+)"/.exec(p)[1];
    const fill = /fill="([^"]+)"/.exec(p)[1];
    const pm = /url\(#([^)]+)\)/.exec(fill);
    if (!pm) {
      if (overlaid.has(d)) continue;                 // the base under a stripe overlay
      out += `<path d="${d}" fill="${fill}" stroke="${C.paper}" stroke-width="0.8" stroke-linejoin="round"/>`;
      continue;
    }
    const bands = pats[pm[1]];
    if (!bands || !bands.length) throw new Error("a striped ward's pattern " + pm[1] + " has no stripes");
    const nums = d.match(/-?[\d.]+/g).map(Number);
    const xs = nums.filter((_, i) => i % 2 === 0), ys = nums.filter((_, i) => i % 2 === 1);
    const us = xs.map((x, i) => (x + ys[i]) * k45), vs = xs.map((x, i) => (ys[i] - x) * k45);
    const u0 = Math.floor(Math.min(...us) / STRIPE_STEP) - 1, u1 = Math.ceil(Math.max(...us) / STRIPE_STEP) + 1;
    const v0 = Math.min(...vs) - 10, v1 = Math.max(...vs) + 10;
    const widest = bands.reduce((a, b) => (b.w > a.w ? b : a));
    const id = "cw" + n++;
    defs += `<clipPath id="${id}"><path d="${d}"/></clipPath>`;
    let g = rect(Math.min(...xs) - 2, Math.min(...ys) - 2, Math.max(...xs) - Math.min(...xs) + 4, Math.max(...ys) - Math.min(...ys) + 4, widest.c);
    g += `<g transform="rotate(45)">`;
    for (let k = u0; k <= u1; k++) for (const b of bands) if (b !== widest)
      g += `<rect x="${n1(k * STRIPE_STEP + b.x - b.w / 2)}" y="${n1(v0)}" width="${b.w.toFixed(2)}" height="${n1(v1 - v0)}" fill="${b.c}"/>`;
    g += "</g>";
    out += `<g clip-path="url(#${id})">${g}</g><path d="${d}" fill="none" stroke="${C.paper}" stroke-width="0.8" stroke-linejoin="round"/>`;
  }
  return `<defs>${defs}</defs>` + out;
}
const FC_HEAD = { big: 64, least: 44, lines: 2 };
const FC = { left: 600, gapHead: 58, head: 24, row: 30, alone: 26, coal: 26, pitch: 36, coalPitch: 35, mapH: 330 };
const KEY = { w: 34, h: 22, bands: 5 };
function forecast(spec) {
  let s = frame("forecast", spec.date_line);
  const h = headline(spec.headline, HEAD_MAX, FC_HEAD.big, FC_HEAD.least, FC_HEAD.lines);
  s += h.svg;
  const LW = FC.left - X;
  const row = (y, label, value, fs) => text(X, y, fitText(label, LW - textWidth(value, fs, "sansSemi") - 16, fs, "sans", fs * 0.75).text, fs, "sans", { fill: C.ink2 }) +
    text(X + LW, y, value, fs, "sansSemi", { anchor: "end" });
  let y = h.last + FC.gapHead;
  s += text(X, y, spec.most_seats, FC.head, "sans", { fill: C.ink3 });
  for (const r of spec.rows) { y += FC.pitch; s += row(y, r.label, r.value, FC.row); }
  y += FC.pitch + 6;
  s += row(y, spec.alone.label, spec.alone.value, FC.alone);
  y += FC.pitch + 8;
  s += text(X, y, spec.coalitions_head, FC.head, "sans", { fill: C.ink3 });
  for (const c of spec.coalitions) { y += FC.coalPitch; s += row(y, c.label, c.value, FC.coal); }
  if (y > FOOT - 8) throw new Error("the forecast card's figures run into its foot");
  // the map under the logo, its key under it: stripes in the card's inks
  const vb = /viewBox="([^"]+)"/.exec(spec.map_svg)[1];
  const [, , vw, vh] = vb.split(/\s+/).map(Number);
  const inner = stripedMap(spec.map_svg);
  const mh = FC.mapH, mw = mh * vw / vh, mx = R + 10 - mw;
  s += `<svg x="${n1(mx)}" y="${TOP + LOGO_H + 6}" width="${n1(mw)}" height="${n1(mh)}" viewBox="${vb}">${inner}</svg>`;
  const ky = FOOT - 34, kx = FC.left + 100;
  let key = "";
  for (let k = 0; k < KEY.bands; k++) key += rect(kx + KEY.w / 2 + (k - (KEY.bands - 1) / 2) * 2 * 3.5 - 1.6, ky - 30, 3.2, 82, C.ink3);
  s += `<defs><clipPath id="key"><rect x="${kx}" y="${ky}" width="${KEY.w}" height="${KEY.h}" rx="3"/></clipPath></defs><g clip-path="url(#key)">` +
    rect(kx, ky, KEY.w, KEY.h, C.ink2) + `<g transform="rotate(45 ${kx + KEY.w / 2} ${ky + KEY.h / 2})">` + key + "</g></g>";
  s += text(kx + KEY.w + 12, ky + 18, spec.key_label, 20, "sans", { fill: C.ink2 });
  return s + "</svg>";
}

// ---------- /your-forecast/: the call to make one, and our prediction's map with its seal ----------
const YF = { head: 96, mapMaxW: 600, textX: 670, body: 34, bodyPitch: 46, y: 222, cta: 28, url: 34, seal: 132, label: 20 };
function interactive(spec) {
  let s = frame("interactive", spec.date_line);
  const h = headline(spec.headline, HEAD_MAX, YF.head, YF.head * 0.6, 1);
  s += h.svg;
  const g = spec.map;
  const mt = h.last + 40, mh0 = FOOT - 14 - mt - YF.label * 1.6;
  const mw = Math.min(YF.mapMaxW, mh0 * g.W / g.H), sc = mw / g.W, mh = g.H * sc;
  const my = mt + YF.label * 1.6 + (mh0 - mh) / 2;
  s += text(X, my - YF.label * 0.6, spec.map_label, YF.label, "sansSemi", { fill: C.ink2 });
  let paths = "";
  for (const w of g.wards) paths += `<path d="${w.path}" fill="${w.colour}" stroke="${C.paper}" stroke-width="${n1(0.8 / sc)}" stroke-linejoin="round"/>`;
  s += `<g transform="translate(${X - 8} ${n1(my)}) scale(${sc.toFixed(4)})">${paths}</g>`;
  s += stamp(spec.seal, "ps", X - 8 + mw - YF.seal * 0.45, my + mh - YF.seal * 0.45, YF.seal);
  const tw = R - YF.textX;
  const body = wrapText(spec.body, tw, YF.body, "sans");
  body.forEach((l, k) => { s += text(YF.textX, YF.y + k * YF.bodyPitch, l, YF.body, "sans", { fill: C.ink }); });
  const cy = YF.y + body.length * YF.bodyPitch + 44;
  s += text(YF.textX, cy, spec.cta, YF.cta, "sans", { fill: C.ink2 });
  const url = fitText(spec.site, tw, YF.url, "monoSemi", 24);
  s += text(YF.textX, cy + 44, url.text, url.fs, "monoSemi", { fill: C.ink });
  return s + "</svg>";
}

export const LAYOUTS = { claims, article, forecast, interactive };

// ---------- naming ----------
const RESVG = JSON.parse(readFileSync(resolve(REPO, "worker-api/node_modules/@resvg/resvg-wasm/package.json"), "utf8")).version;
const FONT_BYTES = Object.values(FACES).map(([file]) => readFileSync(resolve(REPO, "src/card-fonts", file)));
// The first 12 hex digits of sha256(svg, the faces, resvg's version), as
// letters: 0-9a-f -> a-p, so an image's address carries no digit.
export function imageName(svg) {
  const h = createHash("sha256").update(svg).update(RESVG);
  for (const b of FONT_BYTES) h.update(b);
  return [...h.digest("hex").slice(0, 12)].map(c => String.fromCharCode(97 + parseInt(c, 16))).join("");
}

export function cardSVG(spec) {
  const draw = LAYOUTS[spec.layout];
  if (!draw) throw new Error(`no layout ${spec.layout} (${spec.slug})`);
  return draw(spec);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [src, out] = process.argv.slice(2);
  if (!src || !out) { console.error("usage: node src/og-pages.mjs <specs.json | -> <out-dir>"); process.exit(2); }
  const specs = JSON.parse(src === "-" ? readFileSync(0, "utf8") : readFileSync(src, "utf8"));
  const manifest = {};
  for (const spec of specs) {
    const svg = cardSVG(spec);
    const file = `${spec.slug}-${imageName(svg)}.png`;
    writeFileSync(resolve(out, file), await toPNG(svg));
    manifest[spec.slug] = file;
  }
  process.stdout.write(JSON.stringify(manifest));
}
