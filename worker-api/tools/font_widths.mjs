#!/usr/bin/env node
// Advance widths of the printable ASCII characters in a TrueType font, read
// from its own cmap and hmtx tables. interactive/js/card.js lays the share card
// out with these numbers for the DejaVu faces the server renders with
// (src/render.js), so a party name is measured, not guessed from its length;
// test/node/build.test.js holds card.js's table equal to this output.
//
//   node tools/font_widths.mjs     print card.js's table for the bundled faces
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

export const FIRST = 32, LAST = 126;

// The faces card.js draws in: SANS regular (names, captions), SANS bold (seat
// numbers), SERIF bold (title, coalition line).
export const FACES = { sans: "DejaVuSans.ttf", sansBold: "DejaVuSans-Bold.ttf", serifBold: "DejaVuSerif-Bold.ttf" };

function tables(dv) {
  const out = {};
  const n = dv.getUint16(4);
  for (let i = 0; i < n; i++) {
    const at = 12 + 16 * i;
    const tag = String.fromCharCode(...[0, 1, 2, 3].map(k => dv.getUint8(at + k)));
    out[tag] = dv.getUint32(at + 8);
  }
  return out;
}

function glyphOf(dv, cmap) {
  const n = dv.getUint16(cmap + 2);
  let sub = null;
  for (let i = 0; i < n; i++) {
    const at = cmap + 4 + 8 * i;
    const platform = dv.getUint16(at), encoding = dv.getUint16(at + 2);
    const off = cmap + dv.getUint32(at + 4);
    if (dv.getUint16(off) === 4 && ((platform === 3 && encoding === 1) || platform === 0)) { sub = off; break; }
  }
  if (sub === null) throw new Error("no format-4 Unicode cmap");
  const segs = dv.getUint16(sub + 6) / 2;
  const ends = sub + 14, starts = ends + 2 * segs + 2, deltas = starts + 2 * segs, ranges = deltas + 2 * segs;
  return code => {
    for (let s = 0; s < segs; s++) {
      if (code > dv.getUint16(ends + 2 * s)) continue;
      const start = dv.getUint16(starts + 2 * s);
      if (code < start) return 0;
      const delta = dv.getInt16(deltas + 2 * s), ro = dv.getUint16(ranges + 2 * s);
      if (!ro) return (code + delta) & 0xffff;
      const g = dv.getUint16(ranges + 2 * s + ro + 2 * (code - start));
      return g ? (g + delta) & 0xffff : 0;
    }
    return 0;
  };
}

// Every character a format-4 cmap maps, with its advance: { em, w: { code:
// advance } }. For a subset font (the site's Latin-1 IBM Plex), this is the
// whole repertoire: a character outside it has no glyph to draw.
export function advanceMap(buf) {
  const dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength);
  const t = tables(dv);
  const em = dv.getUint16(t.head + 18);
  const nh = dv.getUint16(t.hhea + 34);
  const glyph = glyphOf(dv, t.cmap);
  const adv = g => dv.getUint16(t.hmtx + 4 * Math.min(g, nh - 1));
  const w = {};
  for (let c = 32; c < 0xfffe; c++) {
    const g = glyph(c);
    if (g) w[c] = adv(g);
  }
  return { em, w };
}

export function advanceTable(buf) {
  const dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength);
  const t = tables(dv);
  const em = dv.getUint16(t.head + 18);
  const nh = dv.getUint16(t.hhea + 34);
  const glyph = glyphOf(dv, t.cmap);
  const adv = g => dv.getUint16(t.hmtx + 4 * Math.min(g, nh - 1));
  const widths = [];
  for (let c = FIRST; c <= LAST; c++) widths.push(adv(glyph(c)));
  return { em, widths };
}

export function bundledTables() {
  const require = createRequire(import.meta.url);
  return Object.fromEntries(Object.entries(FACES).map(([k, f]) =>
    [k, advanceTable(readFileSync(require.resolve(`dejavu-fonts-ttf/ttf/${f}`)))]));
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  for (const [k, t] of Object.entries(bundledTables()))
    console.log(`  ${k}: { em: ${t.em}, w: [${t.widths.join(",")}] },`);
}
