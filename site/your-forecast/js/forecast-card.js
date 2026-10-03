// The share image of a Johannesburg council, for every page that has one:
// /your-forecast/ section 1 (play-card.js: a reader's settings on the model, each party's middle
// seat count and range) and /your-forecast/ section 2 (make-share.js: a reader's own forecast,
// exact seats). ONE MODULE, ONE LAYOUT: the site's photograph of Hillbrow
// Tower down the left (link) or behind the top (story), a headline, the lines
// under it, the ward map, one row per party, and a foot.
//
// It knows nothing about where its figures came from. The caller hands it the
// headline, the lines, the wards' paths and fills (and stripes, where a ward
// is contested), the rows and the notes, all from the result that page shows,
// and every word: the headline is the caller's, because /your-forecast/ section 1 never prints a
// reader's name over the model's own forecast (critic G1, 2026-10-02) and
// /your-forecast/ section 2 heads the reader's forecast with their name (cardTitle).
//
// ⛔ A LIVE WRITER WITH NO REGION (stats.LIVE_WRITERS["play/js/forecast-card.js"]
// and ["make/js/forecast-card.js"]): it turns the figures it is handed into an
// SVG, and reaches no element of the page. It may hold no data block and open
// no data source.
//
// A ROW is { label, colour, value } plus either `n` (a bar from zero to n: a
// seat count, null when withheld) or `mid`, `lo`, `hi` and `range` (the range
// holding nine in ten as a band, the middle as a tick, `range` as text beside
// `value`). `lo`/`hi`/`mid` may be null when the figure is withheld. All rows
// share one scale. Without a range column the name column takes what the
// longest name needs, up to NAME_SHARE of the width, so names are not cut.
//
// The photograph is not in the SVG: an SVG drawn as an image may not fetch,
// and a canvas an SVG <image> was drawn into can refuse to export. The page
// passes photoUnder(size, src) to card-text.js's svgToPNG, which draws the
// crop under the SVG; the SVG leaves that area transparent and shades its
// edge into the paper. With `photo: false` it fills the area with paper.
//
// Text is laid out by measured width (card-text.js). Literal hex and system
// fonts: the image leaves the page, and an SVG drawn into a canvas cannot load
// web fonts. The site's name is the exception: svgToPNG draws it on the
// canvas in the page's IBM Plex Mono (siteLabel).

import { fitText, textWidth } from "./card-text.js";

export const SIZES = { link: [1200, 630], story: [1080, 1920] };
export const SITE = "joburg.whysoserious.city";
// The lowest a story card's words may sit: story apps lay their reply bar
// over the band below it.
export const STORY_TEXT_BOTTOM = 1660;
// The story card's headline baseline: the photograph shows above it.
const STORY_TITLE_Y = 380;
export const OTHERS_COLOUR = "#464d47";

const C = { paper: "#141715", paper2: "#1c201d", rule: "#333833", ink: "#eceee9", ink2: "#b6bcb6", ink3: "#868d86" };
const SERIF = "'Iowan Old Style','Palatino Linotype',Palatino,Georgia,serif";
const SANS = "ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif";
const MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace";
// share.jpg: 1200 x 630, the tower's column at x = 613.
const PHOTO = { file: "share.jpg", w: 1200, h: 630, towerX: 613 };
// The link card's photograph strip, in card pixels.
const STRIP = 250;
export const PHOTO_FILE = PHOTO.file;

// The site's name on the card, as svgToPNG's `label` takes it: drawn on the
// canvas in IBM Plex Mono, after the logo's tower-J (MARK_FILE, the
// favicon, same-origin: `markSrc`). Up the photograph's left edge on the
// link card, across the top of the story card. The card's SVG leaves the
// place empty.
export const MARK_FILE = "mark.svg";
// mark.svg's box, width over height
const MARK_ASPECT = 106 / 404;
export function siteLabel(size, markSrc) {
  const H = SIZES[size][1];
  // the link card's name runs up the strip's edge, so its mark is no taller
  // than the strip's margin allows
  const at = size === "link" ? { x: 30, y: H - 22, fs: 15, rotate: -90, mh: 1.7 } : { x: 60, y: 120, fs: 30, rotate: 0, mh: 2.6 };
  const h = at.fs * at.mh;
  return { text: SITE, weight: "700", fill: C.ink, x: at.x, y: at.y, fs: at.fs, rotate: at.rotate,
           mark: markSrc ? { src: markSrc, w: h * MARK_ASPECT, h } : null };
}

// The crop of share.jpg drawn under the card at `size`, as svgToPNG's `under`
// takes it: a window on the tower with the card area's proportions.
export function photoUnder(size, src) {
  const [W, H] = SIZES[size];
  const dw = size === "link" ? STRIP : W, dh = H;
  const sh = PHOTO.h, sw = Math.min(PHOTO.w, sh * dw / dh);
  const sx = Math.max(0, Math.min(PHOTO.w - sw, PHOTO.towerX - sw / 2));
  return { src, sx, sy: 0, sw, sh, dx: 0, dy: 0, dw, dh };
}

// Section 2's headline: "[Name]'s election forecast", in the sentence case of
// section 1's ("[Name]'s settings on the model").
export function cardTitle(name) {
  if (!name) return "My election forecast";
  return name + (/s$/i.test(name) ? "'" : "'s") + " election forecast";
}

const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

function text(x, y, s, { fs, family = SANS, fill = C.ink2, weight = "", anchor = "", transform = "" }) {
  return `<text x="${x}" y="${y}" font-family="${family}" font-size="${fs}"${weight ? ` font-weight="${weight}"` : ""}${anchor ? ` text-anchor="${anchor}"` : ""}${transform ? ` transform="${transform}"` : ""} fill="${fill}">${esc(s)}</text>`;
}

// Wrap on spaces into lines whose measured width fits maxW.
function wrap(s, maxW, fs) {
  const out = [];
  let cur = "";
  for (const w of String(s).split(" ")) {
    const next = (cur + " " + w).trim();
    if (cur && fitText(next, maxW, fs, "sans", fs).text !== next) { out.push(cur); cur = w; }
    else cur = next;
  }
  if (cur) out.push(cur);
  return out;
}

// A line's look: "strong" (bright, bold), "plain" (bright) or "muted".
const TONE = { strong: { fill: C.ink, weight: "600" }, plain: { fill: C.ink }, muted: { fill: C.ink2 } };

// The ward map: fills, then the stripes over contested wards, then north.
// `map` is { W, H, step, rotate, wards: [{ path, fill, bands? }] }, where
// bands are the stripe tile's lines ({ x, w, colour }).
function drawMap(map, { x, y, w, prefix, fs }) {
  const s = w / map.W, h = map.H * s;
  const defs = [], fills = [], hatches = [];
  map.wards.forEach((ward, i) => {
    if (!ward.path) return;
    fills.push(`<path d="${ward.path}" fill="${ward.fill}" stroke="${C.paper}" stroke-width="${(0.7 / s).toFixed(2)}" stroke-linejoin="round"/>`);
    if (ward.bands) {
      const id = prefix + i;
      defs.push(`<pattern id="${id}" width="${map.step}" height="${map.step}" patternTransform="rotate(${map.rotate})" patternUnits="userSpaceOnUse">` +
        ward.bands.map(b => `<line x1="${b.x.toFixed(2)}" y1="0" x2="${b.x.toFixed(2)}" y2="${map.step}" stroke="${b.colour}" stroke-width="${b.w.toFixed(2)}"/>`).join("") + "</pattern>");
      hatches.push(`<path d="${ward.path}" fill="url(#${id})"/>`);
    }
  });
  const north = text(x + w - 4, y + fs, "N ↗", { fs, family: MONO, fill: C.ink2, anchor: "end" });
  return { h, svg: `<g transform="translate(${x} ${y}) scale(${s.toFixed(4)})"><defs>${defs.join("")}</defs>${fills.join("")}${hatches.join("")}</g>` + north };
}

// The rows, on one scale: a range band and a middle tick where the row has a
// range, a bar from zero otherwise; the figure, then the range if any.
const NAME_SHARE = 0.45;
function drawRows(rows, { x, y, w, rowH, fs }) {
  const ranged = rows.some(r => "range" in r);
  const hi = r => (ranged ? (r.hi ?? r.mid ?? 0) : (r.n ?? 0));
  const top = Math.max(1, ...rows.map(hi));
  const longest = Math.max(...rows.map(r => textWidth(r.label, fs, "sansBold")));
  const nameW = ranged ? fs * 6.2 : Math.max(fs * 6.2, Math.min(w * NAME_SHARE, longest + 10));
  const figW = fs * 2.2, rngW = ranged ? fs * 3.6 : 0, barW = w - nameW - figW - rngW - 8;
  const at = v => x + nameW + barW * v / top;
  return rows.map((r, k) => {
    const yy = y + k * rowH;
    const fitted = fitText(r.label, nameW - 8, fs, "sansBold", fs * 0.75);
    let marks;
    if (ranged) {
      marks = (r.lo == null || r.hi == null ? ""
        : `<rect x="${at(r.lo).toFixed(1)}" y="${(yy + fs * 0.2).toFixed(1)}" width="${Math.max(2, at(r.hi) - at(r.lo)).toFixed(1)}" height="${(fs * 0.7).toFixed(1)}" rx="2" fill="${r.colour}" fill-opacity="0.6"/>`) +
        (r.mid == null ? ""
          : `<rect x="${(at(r.mid) - 1.5).toFixed(1)}" y="${yy.toFixed(1)}" width="3" height="${(fs * 1.1).toFixed(1)}" rx="1" fill="${C.ink}"/>`);
    } else {
      marks = r.n == null ? ""
        : `<rect x="${(x + nameW).toFixed(1)}" y="${(yy + fs * 0.2).toFixed(1)}" width="${Math.max(3, barW * r.n / top).toFixed(1)}" height="${(fs * 0.7).toFixed(1)}" rx="2" fill="${r.colour}"/>`;
    }
    return text(x, yy + fs * 0.85, fitted.text, { fs: fitted.fs, fill: C.ink, weight: "600" }) + marks +
      text(x + w - rngW, yy + fs * 0.9, r.value, { fs: fs * 1.15, fill: C.ink, weight: "700", anchor: "end" }) +
      (ranged ? text(x + w, yy + fs * 0.9, r.range, { fs: fs * 0.85, fill: C.ink3, anchor: "end" }) : "");
  }).join("");
}

// The paper's fade over the photograph's edge.
function fade(size, W, H) {
  if (size === "link") {
    return `<defs><linearGradient id="pf" x1="0" x2="1" y1="0" y2="0"><stop offset="0.7" stop-color="${C.paper}" stop-opacity="0"/><stop offset="1" stop-color="${C.paper}"/></linearGradient></defs>` +
      `<rect x="${STRIP}" y="0" width="${W - STRIP}" height="${H}" fill="${C.paper}"/><rect x="0" y="0" width="${STRIP}" height="${H}" fill="url(#pf)"/>`;
  }
  // the photograph shows above the headline; from the headline down the
  // paper is near-opaque, a scrim, so grey text stays readable over it
  return `<defs><linearGradient id="pf" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="${C.paper}" stop-opacity="0.15"/><stop offset="0.12" stop-color="${C.paper}" stop-opacity="0.35"/><stop offset="0.17" stop-color="${C.paper}" stop-opacity="0.88"/><stop offset="0.33" stop-color="${C.paper}"/></linearGradient></defs>` +
    `<rect width="${W}" height="${H}" fill="url(#pf)"/>`;
}

// The card. { size, title, lines: [{ text, tone }], map, mapNote, rows,
// rowsNote, foot: [paragraph], photo }. Every string is drawn as text.
export function buildForecastCardSVG({ size = "link", title, lines = [], map, mapNote = "", rows, rowsNote = "", foot = [], photo = true }) {
  if (!map) throw new Error("the card needs the ward map");
  const [W, H] = SIZES[size];
  const under = photo ? "" : `<rect width="${size === "link" ? STRIP : W}" height="${H}" fill="${C.paper2}"/>`;
  let body;
  if (size === "link") {
    const sx = 268, sw = W - sx - 34;
    const head = fitText(title, sw, 40, "serifBold", 26);
    let y = 64, first = true;
    let top = text(sx, y, head.text, { fs: head.fs, family: SERIF, fill: C.ink, weight: "600" });
    for (const l of lines) {
      wrap(l.text, sw, 15).forEach((t, k) => {
        y += first ? 28 : k ? 20 : 22;
        first = false;
        top += text(sx, y, t, { fs: 15, ...TONE[l.tone || "muted"] });
      });
    }
    const feet = foot.flatMap(f => wrap(f, sw, 12));
    const footTop = H - 14 - (feet.length - 1) * 16 - 12;
    const mapY = y + 18, mapW = 470;
    const m = drawMap(map, { x: sx, y: mapY, w: mapW, prefix: "cl", fs: 12 });
    const notes = mapNote ? wrap(mapNote, mapW, 12) : [];
    const bx = sx + mapW + 22, bw = sw - mapW - 22;
    const bnotes = rowsNote ? wrap(rowsNote, bw, 12) : [];
    const rowH = Math.min(28, (footTop - 10 - mapY - bnotes.length * 15 - 6) / rows.length);
    const rowsEnd = mapY + rowH * rows.length;
    body = under + fade(size, W, H) +
      top + m.svg +
      notes.map((l, k) => text(sx, Math.min(mapY + m.h + 14, footTop - 6 - (notes.length - 1) * 15) + k * 15, l, { fs: 12, fill: C.ink3 })).join("") +
      drawRows(rows, { x: bx, y: mapY, w: bw, rowH, fs: 14 }) +
      bnotes.map((l, k) => text(bx, rowsEnd + 12 + k * 15, l, { fs: 12, fill: C.ink3 })).join("") +
      `<rect x="${sx}" y="${footTop - 4}" width="${sw}" height="1" fill="${C.rule}"/>` +
      feet.map((l, k) => text(sx, footTop + 12 + k * 16, l, { fs: 12, fill: C.ink3 })).join("");
  } else {
    const x = 60, w = W - 120;
    const head = fitText(title, w, 64, "serifBold", 40);
    let y = STORY_TITLE_Y, first = true;
    let top = text(x, y, head.text, { fs: head.fs, family: SERIF, fill: C.ink, weight: "600" });
    for (const l of lines) {
      wrap(l.text, w, 28).forEach((t, k) => {
        y += first ? 50 : k ? 38 : 40;
        first = false;
        top += text(x, y, t, { fs: 28, ...TONE[l.tone || "muted"] });
      });
    }
    const feet = foot.flatMap(f => wrap(f, w, 22));
    const notes = mapNote ? wrap(mapNote, w, 22) : [], bnotes = rowsNote ? wrap(rowsNote, w, 22) : [];
    const rowH = 40, rowsH = rows.length * rowH;
    const footTop = STORY_TEXT_BOTTOM - (feet.length - 1) * 28;
    const mapY = y + 30;
    const room = footTop - 40 - bnotes.length * 28 - 20 - rowsH - 30 - notes.length * 28 - 20 - mapY;
    const mw = Math.min(w, room * map.W / map.H);
    const m = drawMap(map, { x: x + (w - mw) / 2, y: mapY, w: mw, prefix: "cs", fs: 22 });
    let yy = mapY + m.h + 6;
    const mapText = notes.map(l => text(x, (yy += 28), l, { fs: 22, fill: C.ink3 })).join("");
    const rowsY = yy + 30;
    yy = rowsY + rowsH;
    const rowText = bnotes.map(l => text(x, (yy += 28), l, { fs: 22, fill: C.ink3 })).join("");
    body = (photo ? "" : under) + fade(size, W, H) +
      top + m.svg + mapText +
      drawRows(rows, { x, y: rowsY, w, rowH, fs: 26 }) + rowText +
      feet.map((l, k) => text(x, footTop + k * 28, l, { fs: 22, fill: C.ink3 })).join("");
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${body}</svg>`;
}

// The image's text alternative: the same words and figures, in the same order.
export function forecastCardAlt({ title, lines = [], rows, mapNote = "", rowsNote = "", foot = [] }) {
  const row = r => r.label + " " + r.value + (r.range ? " (" + r.range + ")" : "");
  return [title, ...lines.map(l => l.text), "Seats: " + rows.map(row).join(", "), mapNote, rowsNote, ...foot]
    .filter(Boolean).map(s => s.replace(/\.$/, "")).join(". ") + ".";
}
