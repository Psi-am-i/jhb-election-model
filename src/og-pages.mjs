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
import { buildPlayCardSVG } from "../interactive/js/play-card.js";

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const { C, text, rect, brand, chip, brandWidth, stampOf, stampSVG, textWidth, fitText, wrapText } = SC;
const [W, H] = SC.SIZES.link;
const X = 56, R = W - 56;
const n1 = v => Number(v.toFixed(1));

// ---------- the frame: a bar in the page kind's colour, our logo large at the
// top right, the headline's cap line level with it, the date line at the foot
// (owner, 2026-10-09: "keep logo same place big and top right for all") ----------
// The bar's colour is the spec's (og_pages.kind_colour, from tokens.css).
const KIND_BAR = 8;
const FOOT = 560, FOOT_TEXT = 606, FOOT_FS = 21;
const TOP = 40;
const LOGO_H = 120;
const ASSETS = { brand: SC.brandOf(readFileSync(resolve(REPO, "src/brand/logo.svg"), "utf8")), logos: {} };
const LOGO_W = brandWidth(ASSETS, LOGO_H), LOGO_X = R - LOGO_W + 6;
const HEAD_MAX = LOGO_X - X - 36;                  // a line level with the logo stops short of it
const capBase = (fs, top = TOP) => top + fs * 0.7; // a first line whose cap height starts at `top`
// The top of the logo's wordmark ("ELECTION FORECAST"), as a share of the
// logo's height: measured on the drawn card, its letters start 41px below the
// logo's top at LOGO_H (2026-10-10).
const WORDMARK_TOP = TOP + LOGO_H * 41 / 120;
const HEAD_LEADING = 1.08;

function frame(spec, { footRight = false } = {}) {
  const dateLine = spec.date_line;
  if (!/^#[0-9a-fA-F]{6}$/.test(spec.kind_colour || "")) throw new Error(`${spec.slug}: no kind colour`);
  let s = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">` + rect(0, 0, W, H, C.paper);
  s += rect(0, 0, W, KIND_BAR, spec.kind_colour);
  s += brand(ASSETS, LOGO_X, TOP, LOGO_H);
  s += rect(X, FOOT, R - X, 1, C.rule);
  s += text(footRight ? R : X, FOOT_TEXT, fitText(dateLine, R - X, FOOT_FS, "sans", FOOT_FS * 0.75).text, FOOT_FS, "sans",
    footRight ? { fill: C.ink3, anchor: "end" } : { fill: C.ink3 });
  return s;
}

// The headline, top left: the largest size from `big` down to `least` at which
// it takes at most `lines` lines of `maxW`. Returns { svg, last } (the last
// baseline). A headline that will not fit at `least` is refused.
function headline(words, maxW, big, least, lines, top = TOP) {
  for (let fs = big; fs >= least; fs -= 2) {
    const L = wrapText(words, maxW, fs, "serifSemi");
    if (L.length <= lines) {
      return { svg: L.map((l, k) => text(X, capBase(fs, top) + k * fs * HEAD_LEADING, l, fs, "serifSemi")).join(""),
        last: capBase(fs, top) + (L.length - 1) * fs * HEAD_LEADING, fs };
    }
  }
  throw new Error(`headline "${words}" does not fit ${lines} lines at ${least}px`);
}

// An owner's stamp centred on (cx, cy), `h` tall: share-card.js stampSVG, the
// one function that places a stamp (its ids prefixed by `prefix`). `file` is
// its path from the repository root, as the spec carries it.
const STAMPS = {};
function stamp(file, prefix, cx, cy, h) {
  STAMPS[file] ??= stampOf(readFileSync(resolve(REPO, file), "utf8"));
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
// the party logos large (owner's notes, 2026-10-10: "Much bigger party logos")
const CLAIM_STRIP = { minCols: 4, badge: 140, cy: 270, chip: 112, chipTop: 348, name: 30, nameY: 496, who: 19, whoY: 528 };
function claims(spec) {
  let s = frame(spec);
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

// ---------- a claim's own page ----------
// Top to bottom (owner, 2026-10-13): the quote; directly under it the party's
// logo, name and speaker; then, lower, the verdict stamp, large, beside the
// tested statement (claims.toml's label, with a full stop). The top bar is the
// party's colour. X lays the link's title over the image's bottom left, so
// nothing is drawn in the lowest 15% of the card at the left: the rule
// and the foot line end it, and the foot line is set at the right.
const CLAIM_QUOTE = { big: 40, least: 24, lines: 6 };
const CLAIM_ROW = { chip: 56, gapTop: 18, gap: 18, party: 28, who: 20 };
const CLAIM_STAMP = { max: 250, min: 200, preferred: 230, bottom: 526, gapTop: 14, gap: 40 };
const CLAIM_STATEMENT = { tag: 21, big: 46, least: 28, lines: 3 };
// A party's logo in the one container every claim card uses: a rounded white
// square, the logo inset by equal padding, centred and whole (a logo that is
// itself a full-bleed square gets the same margin as one with a transparent
// ground). A party with no logo gets its colour in the same square.
function claimChip(spec, x, y, s) {
  const src = logoOf(spec.logo), rx = s / 6, pad = s * 0.1;
  if (!src) return rect(x, y, s, s, spec.colour, ` rx="${n1(rx)}"`);
  const id = "cc";
  return `<clipPath id="${id}"><rect x="${n1(x + pad)}" y="${n1(y + pad)}" width="${n1(s - 2 * pad)}" height="${n1(s - 2 * pad)}" rx="${n1(rx / 2)}"/></clipPath>` +
    rect(x, y, s, s, C.chip, ` rx="${n1(rx)}"`) +
    `<image x="${n1(x + pad)}" y="${n1(y + pad)}" width="${n1(s - 2 * pad)}" height="${n1(s - 2 * pad)}" href="${src}" preserveAspectRatio="xMidYMid meet" clip-path="url(#${id})"/>`;
}
function claim(spec) {
  let s = frame(spec, { footRight: true });
  if (!spec.statement) throw new Error(`${spec.slug}: no tested statement`);
  STAMPS[spec.badge] ??= stampOf(readFileSync(resolve(REPO, spec.badge), "utf8"));
  const [, , vw, vh] = STAMPS[spec.badge].viewBox.split(/\s+/).map(Number);
  const words = "\u201c" + spec.quote + "\u201d";
  // the quote at the largest size that leaves the stamp its preferred height
  // (or, at the smallest size, the room there is, never under CLAIM_STAMP.min)
  let pick = null;
  for (let fs = CLAIM_QUOTE.big; fs >= CLAIM_QUOTE.least && !pick; fs -= 2) {
    const L = wrapText(words, HEAD_MAX, fs, "serifSemi");
    if (L.length > CLAIM_QUOTE.lines) continue;
    const last = capBase(fs) + (L.length - 1) * fs * HEAD_LEADING;
    const rowTop = last + CLAIM_ROW.gapTop, rowBottom = rowTop + CLAIM_ROW.chip;
    const stampH = Math.min(CLAIM_STAMP.max, CLAIM_STAMP.bottom - (rowBottom + CLAIM_STAMP.gapTop));
    if (stampH >= CLAIM_STAMP.preferred || fs === CLAIM_QUOTE.least) pick = { fs, L, rowTop, rowBottom, stampH };
  }
  if (!pick || pick.stampH < CLAIM_STAMP.min) throw new Error(`${spec.slug}: the quote leaves the stamp under ${CLAIM_STAMP.min}px`);
  const { fs, L, rowTop, rowBottom, stampH } = pick;
  s += L.map((l, k) => text(X, capBase(fs) + k * fs * HEAD_LEADING, l, fs, "serifSemi")).join("");
  // the party, directly under the quote
  if (spec.logo) ASSETS.logos[spec.code] = logoOf(spec.logo);
  s += claimChip(spec, X, rowTop, CLAIM_ROW.chip);
  const px = X + CLAIM_ROW.chip + CLAIM_ROW.gap, pw = R - px;
  const pn = fitText(spec.party, pw, CLAIM_ROW.party, "sansBold", 22), who = fitText(spec.speaker, pw, CLAIM_ROW.who, "sans", 16);
  s += text(px, rowTop + 25, pn.text, pn.fs, "sansBold");
  s += text(px, rowTop + 48, who.text, who.fs, "sans", { fill: C.ink2 });
  // the stamp, and the tested statement beside it
  const sTop = rowBottom + CLAIM_STAMP.gapTop, cy = sTop + stampH / 2, bw = stampH * vw / vh;
  s += stamp(spec.badge, "v", X + bw / 2, cy, stampH);
  const tx = X + bw + CLAIM_STAMP.gap, tw = R - tx;
  const statement = spec.statement + ".";
  let st = null;
  for (let sf = CLAIM_STATEMENT.big; sf >= CLAIM_STATEMENT.least && !st; sf -= 2) {
    const SL = wrapText(statement, tw, sf, "serifSemi");
    if (SL.length <= CLAIM_STATEMENT.lines) st = { sf, SL };
  }
  if (!st) throw new Error(`${spec.slug}: the statement does not fit ${CLAIM_STATEMENT.lines} lines at ${CLAIM_STATEMENT.least}px`);
  const pitch = st.sf * HEAD_LEADING, block = CLAIM_STATEMENT.tag + 14 + st.sf * 0.9 + (st.SL.length - 1) * pitch;
  const top = cy - block / 2;
  s += text(tx, top + CLAIM_STATEMENT.tag, "Tested statement", CLAIM_STATEMENT.tag, "sansSemi", { fill: C.ink2 });
  s += st.SL.map((l, k) => text(tx, top + CLAIM_STATEMENT.tag + 14 + st.sf * 0.9 + k * pitch, l, st.sf, "serifSemi")).join("");
  return s + "</svg>";
}

// ---------- an article: the headline; the seat ranges where it has them ----------
const ART_HEAD = { big: 88, least: 52, lines: 4 };
const ART_HEAD_BESIDE = { big: 80, least: 48, lines: 3 };
const RANGES = { x: 660, top: 216, pitch: 52, name: 17, bar: 16, value: 17, note: 14, lead: 30 };
function article(spec) {
  let s = frame(spec);
  if (!spec.ranges) {
    // headline only: as large as fits the page under the logo's line, its
    // cap line level with the top of the logo's wordmark rather than the
    // tower's tip, clear of the bar (owner, 2026-10-10: it crowded the top)
    s += headline(spec.headline, HEAD_MAX, ART_HEAD.big, ART_HEAD.least, ART_HEAD.lines, WORDMARK_TOP).svg;
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

// ---------- /forecast: our forecast's one card ----------
// The card the share sheet of /your-forecast/ draws in the browser (owner,
// 2026-10-13: one card for our forecast, one code path): play-card.js's
// buildPlayCardSVG, over the compute result for the published settings, which
// og_pages.forecast_spec takes from page.py run natively. Nothing is drawn
// here: the logo, the title "forecast, <date>", the figures and the foot are
// play-card.js's and share-card.js's.
const WORDMARK = SC.brandOf(readFileSync(resolve(REPO, "src/brand/whysoseriouscity.svg"), "utf8"));
function forecast(spec) {
  const logos = {};
  for (const [code, file] of Object.entries(spec.logos)) logos[code] = logoOf(file);
  const party = c => spec.roster[c];
  return buildPlayCardSVG({ r: spec.result, party, forecastDate: spec.forecast_date, geometry: spec.geometry, when: spec.when,
    size: "link", assets: { logos, wsc: WORDMARK } });
}

// ---------- /your-forecast/: our prediction's map, its seal large over the
// map's top-left, and the call to make one (owner's notes, 2026-10-10) ----------
const YF = { head: 96, mapMaxW: 600, mapTop: 132, textX: 670, body: 34, bodyPitch: 46, cta: 28, ctaGap: 72, url: 34, seal: 190, textBottom: 528 };
function interactive(spec) {
  let s = frame(spec);
  const h = headline(spec.headline, HEAD_MAX, YF.head, YF.head * 0.6, 1);
  s += h.svg;
  const g = spec.map;
  const mt = Math.max(YF.mapTop, h.last + 24), mh0 = FOOT - 12 - mt;
  const mw = Math.min(YF.mapMaxW, mh0 * g.W / g.H), sc = mw / g.W, mh = g.H * sc;
  const mx = X + 20, my = mt + (mh0 - mh) / 2;
  let paths = "";
  for (const w of g.wards) paths += `<path d="${w.path}" fill="${w.colour}" stroke="${C.paper}" stroke-width="${n1(0.8 / sc)}" stroke-linejoin="round"/>`;
  s += `<g transform="translate(${n1(mx)} ${n1(my)}) scale(${sc.toFixed(4)})">${paths}</g>`;
  // the owner's seal says whose map it is: OFFICIAL PREDICTION
  s += stamp(spec.seal, "ps", X - 8 + YF.seal / 2, mt - 8 + YF.seal / 2, YF.seal);
  // the text, right, its last line at YF.textBottom
  const tw = R - YF.textX;
  const body = wrapText(spec.body, tw, YF.body, "sans");
  const blockH = (body.length - 1) * YF.bodyPitch + YF.ctaGap + 44;
  const y0 = YF.textBottom - blockH;
  body.forEach((l, k) => { s += text(YF.textX, y0 + k * YF.bodyPitch, l, YF.body, "sans", { fill: C.ink }); });
  const cy = y0 + (body.length - 1) * YF.bodyPitch + YF.ctaGap;
  s += text(YF.textX, cy, spec.cta, YF.cta, "sans", { fill: C.ink2 });
  const url = fitText(spec.site, tw, YF.url, "monoSemi", 24);
  s += text(YF.textX, cy + 44, url.text, url.fs, "monoSemi", { fill: C.ink });
  return s + "</svg>";
}

export const LAYOUTS = { claims, claim, article, forecast, interactive };

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
