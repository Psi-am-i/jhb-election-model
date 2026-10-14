#!/usr/bin/env node
// MOCK-UP ONLY (audits/2026-10-11-share-sheets). Draws the proposed share
// images from specs built by make_mockups.py, with the release tree's own
// pipeline: og-pages.mjs's LAYOUTS (the frame, and the two existing layouts
// unchanged), share-card.js's primitives, the owner's stamps and logos, and
// og-raster-node.mjs's rasteriser. No figure is typed here: every value and
// every bar length comes from the spec.
//
//   node mock-cards.mjs <specs.json> <out-dir>
//
// `headline` and `stamp` below copy og-pages.mjs's private functions of the
// same names: production would export them, or put these layouts inside
// og-pages.mjs (BRIEF.md, "Production").
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const REL = "/Users/simondavis/projects/atlas-jhb-site-release";
const { LAYOUTS } = await import(REL + "/src/og-pages.mjs");
const { toPNG } = await import(REL + "/src/og-raster-node.mjs");
const SC = await import(REL + "/interactive/js/share-card.js");
const { C, text, rect, chip, brandWidth, stampOf, stampSVG, textWidth, fitText, wrapText } = SC;

const [W] = SC.SIZES.link;
const X = 56, R = W - 56, TOP = 40, LOGO_H = 120, FOOT = 560;
const LOGO_X = R - brandWidth({ brand: SC.brandOf(readFileSync(resolve(REL, "src/brand/logo.svg"), "utf8")) }, LOGO_H) + 6;
const HEAD_MAX = LOGO_X - X - 36;
const capBase = (fs, top = TOP) => top + fs * 0.7;
const HEAD_LEADING = 1.08;

// og-pages.mjs `headline`, copied
function headline(words, maxW, big, least, lines, top = TOP, face = "serifSemi") {
  for (let fs = big; fs >= least; fs -= 2) {
    const L = wrapText(words, maxW, fs, face);
    if (L.length <= lines)
      return { svg: L.map((l, k) => text(X, capBase(fs, top) + k * fs * HEAD_LEADING, l, fs, face)).join(""),
        last: capBase(fs, top) + (L.length - 1) * fs * HEAD_LEADING, fs, n: L.length };
  }
  throw new Error(`headline "${words}" does not fit ${lines} lines at ${least}px`);
}
// og-pages.mjs `stamp`, copied
const STAMPS = {};
function stamp(file, prefix, cx, cy, h) {
  STAMPS[file] ??= stampOf(readFileSync(resolve(REL, file), "utf8"));
  const st = STAMPS[file];
  const [, , vw, vh] = st.viewBox.split(/\s+/).map(Number);
  return stampSVG(st, prefix, cx - h * vw / vh / 2, cy - h / 2, h);
}

// The frame (bar, logo, rule, date line) from the real article layout, with
// no headline: everything before the closing tag.
function frame(spec) {
  const s = LAYOUTS.article({ ...spec, layout: "article", headline: " ", ranges: null });
  return s.slice(0, s.lastIndexOf("</svg>"));
}

// The approved seat-ranges geometry: headline left of x = 660, a lead line
// under it, the graphic from x = 660 to the right margin.
const GX = 660, GTOP = 216;
function leftHead(spec) {
  const h = headline(spec.headline, GX - X - 30, 80, 44, 3);
  let s = h.svg;
  if (spec.lead) s += text(X, h.last + 96, fitText(spec.lead, GX - X - 30, 30, "sansSemi", 20).text, 30, "sansSemi", { fill: C.ink2 });
  return s;
}

// ---- bars: one row per item, a bar from 0 to value on a shared scale ----
function bars(spec) {
  const g = spec.chart;
  let s = frame(spec) + leftHead(spec);
  const gw = R - GX - 70, sx = v => gw * v / g.scale;
  const pitch = g.pitch || 64;
  g.rows.forEach((r, k) => {
    const y = GTOP + k * pitch;
    s += text(GX, y + 4, fitText(r.label, R - GX, 17, "sansSemi", 13).text, 17, "sansSemi", { fill: C.ink2 });
    s += rect(GX, y + 14, gw, 22, C.paper2, ` rx="4"`);
    s += rect(GX, y + 14, Math.max(3, sx(r.v)), 22, r.colour, ` rx="4"`);
    s += text(GX + Math.max(3, sx(r.v)) + 10, y + 32, r.value, 20, "sansSemi");
  });
  s += text(GX, GTOP + g.rows.length * pitch + 8, g.note, 14, "sans", { fill: C.ink3 });
  return s + "</svg>";
}

// ---- councils: one row per seat law, the council as a bar of its size,
// the two largest parties' seats drawn in it, the majority line ticked ----
function councils(spec) {
  const g = spec.chart;
  let s = frame(spec) + leftHead(spec);
  const gw = R - GX - 50, sx = v => gw * v / g.scale;
  const pitch = 70;
  g.rows.forEach((r, k) => {
    const y = GTOP + k * pitch;
    s += text(GX, y, fitText(r.label, R - GX, 17, "sansSemi", 12).text, 17, "sansSemi", { fill: C.ink2 });
    s += rect(GX, y + 10, sx(r.council), 24, C.rule, ` rx="3"`);
    let x = GX;
    for (const p of r.parts) { s += rect(x, y + 10, sx(p.v), 24, p.colour); x += sx(p.v); }
    s += rect(GX + sx(r.majority) - 1, y + 4, 2.5, 36, C.ink);
    s += text(GX + sx(r.council) + 8, y + 29, r.council_text, 18, "sansSemi");
  });
  const ky = GTOP + g.rows.length * pitch;
  let kx = GX;
  for (const p of g.key) {
    s += rect(kx, ky - 11, 14, 14, p.colour, ` rx="2"`);
    s += text(kx + 20, ky + 1, p.label, 15, "sans", { fill: C.ink2 });
    kx += 34 + textWidth(p.label, 15, "sans");
  }
  s += text(GX, ky + 26, g.note, 14, "sans", { fill: C.ink3 });
  return s + "</svg>";
}

// ---- meter: one chance, as a large figure over a 0-100 bar, with two
// supporting figures under it ----
function meter(spec) {
  const g = spec.chart;
  let s = frame(spec) + leftHead(spec);
  const gw = R - GX;
  s += text(GX, GTOP + 60, g.value, 84, "sansBold");
  s += text(GX, GTOP + 100, fitText(g.label, gw, 22, "sans", 16).text, 22, "sans", { fill: C.ink2 });
  s += rect(GX, GTOP + 124, gw, 26, C.paper2, ` rx="5"`);
  s += rect(GX, GTOP + 124, gw * g.v, 26, g.colour, ` rx="5"`);
  g.rows.forEach((r, k) => {
    const y = GTOP + 210 + k * 44;
    s += text(GX, y, r.label, 22, "sans", { fill: C.ink2 });
    s += text(R, y, r.value, 26, "sansSemi", { anchor: "end" });
  });
  return s + "</svg>";
}

// ---- one claim: the quote as the headline, the party and speaker, the
// owner's verdict badge under our logo, and the figure the verdict rests on ----
const CL = { badge: 230, badgeCx: R - 150, badgeCy: 360, chip: 84, fig: 64, figLabel: 22 };
const ASSETS = { logos: {} };
function claim(spec) {
  let s = frame(spec);
  const qw = HEAD_MAX;
  const h = headline("“" + spec.quote + "”", qw, 50, 34, 4);
  s += h.svg;
  const cy = h.last + 34;
  if (spec.logo) ASSETS.logos[spec.code] = "data:image/png;base64," + readFileSync(resolve(REL, "site/logos", spec.logo)).toString("base64");
  s += chip({ code: spec.code, colour: spec.colour, logo: !!spec.logo }, X, cy, CL.chip, ASSETS);
  const tx = X + CL.chip + 20, tw = CL.badgeCx - CL.badge / 2 - tx - 20;
  s += text(tx, cy + 32, fitText(spec.speaker, tw, 28, "sansBold", 20).text, 28, "sansBold");
  s += text(tx, cy + 66, fitText(spec.party + " · " + spec.outlet, tw, 20, "sans", 14).text, 20, "sans", { fill: C.ink2 });
  const fy = Math.max(cy + CL.chip + 80, FOOT - 70);
  const fw = CL.badgeCx - CL.badge / 2 - X - 30;
  s += text(X, fy, spec.figure.value, CL.fig, "sansBold");
  const vx = X + textWidth(spec.figure.value, CL.fig, "sansBold") + 22;
  const L = wrapText(spec.figure.label, CL.badgeCx - CL.badge / 2 - vx - 10, CL.figLabel, "sans");
  if (L.length > 2) throw new Error(`${spec.slug}: figure label takes ${L.length} lines`);
  L.forEach((l, k) => { s += text(vx, fy - (L.length - 1) * 28 + k * 28 - 4, l, CL.figLabel, "sans", { fill: C.ink2 }); });
  if (fy > FOOT - 20) throw new Error(`${spec.slug}: figure runs into the foot`);
  s += stamp(spec.badge, "vb", CL.badgeCx, CL.badgeCy, CL.badge);
  void fw;
  return s + "</svg>";
}

const MOCK = { bars, councils, meter, claim };
const [src, out] = process.argv.slice(2);
const specs = JSON.parse(readFileSync(src, "utf8"));
const manifest = {};
for (const spec of specs) {
  const svg = spec.mock ? MOCK[spec.mock](spec) : LAYOUTS[spec.layout](spec);
  const file = `${spec.slug}.png`;
  writeFileSync(resolve(out, file), await toPNG(svg));
  manifest[spec.slug] = file;
}
process.stdout.write(JSON.stringify(manifest));
