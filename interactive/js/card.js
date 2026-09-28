// The share graphic, built as a self-contained SVG and rasterised to PNG in
// the browser for download and native share.
//
// Two sizes:
//   "link"  1200 x 630   — the Open Graph / X large-card size
//   "story" 1080 x 1920  — 9:16 for WhatsApp Status, Instagram and Facebook
//                          stories; the key content sits inside the middle
//                          1420 px, clear of the top and bottom story chrome.
//
// Always the site's dark palette as literal hex (no CSS variables — the image
// leaves the page). Fonts are the system serif/sans stacks: an SVG drawn into a
// canvas cannot load web fonts, and a <foreignObject> would taint the canvas.
// So the browser-made PNG varies slightly by device; the image crawlers see is
// the one the server renders with an embedded font (BACKEND.md §4), from the
// same builder.
//
// Text is laid out by MEASURED width, not by character count: party names
// come from the roster and can be long, and a name that runs into its bar is
// unreadable. The widths are DejaVu's (the faces the server renders with),
// which are wider than the browsers' serif and sans stacks, so the browser
// PNG errs roomy rather than overlapping.
//
// The council size is the one the seat law returned for this forecast
// (model.council), never a typed number: the excessive-seats clause can
// change it under a non-statutory rule, and it differs by city.
//
// Everything the reader typed is escaped. The card says, in words, that it is
// a reader's forecast and not the model's (PUBLISHING-BACKLOG §10's open
// question, answered: the card is clearly framed as a reader's forecast).

import { esc, possessive, topN } from "./common.js";

const C = {
  paper: "#141715", paper2: "#1c201d", rule: "#333833", ink: "#eceee9",
  ink2: "#b6bcb6", ink3: "#868d86", accent: "#d9954f", reader: "#b98ad6", bad: "#d98070",
};
const SERIF = `'Iowan Old Style','Palatino Linotype',Palatino,Georgia,serif`;
const SANS = `ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif`;
const MONO = `ui-monospace,'SF Mono',Menlo,Consolas,monospace`;

export const SIZES = { link: [1200, 630], story: [1080, 1920] };

// Advance widths of printable ASCII (32..126) in font units, per face, read
// from the bundled DejaVu fonts by worker-api/tools/font_widths.mjs; that
// package's test/node/build.test.js holds this table equal to the fonts.
export const FONT_WIDTHS = {
  sans: { em: 2048, w: [651,821,942,1716,1303,1946,1597,563,799,799,1024,1716,651,739,651,690,1303,1303,1303,1303,1303,1303,1303,1303,1303,1303,690,690,1716,1716,1716,1087,2048,1401,1405,1430,1577,1294,1178,1587,1540,604,604,1343,1141,1767,1532,1612,1235,1612,1423,1300,1251,1499,1401,2025,1403,1251,1403,799,690,799,1716,1024,1024,1255,1300,1126,1300,1260,721,1300,1298,569,569,1186,569,1995,1298,1253,1300,1300,842,1067,803,1298,1212,1675,1212,1212,1075,1303,690,1303,1716] },
  sansBold: { em: 2048, w: [713,934,1067,1716,1425,2052,1786,627,936,936,1071,1716,778,850,778,748,1425,1425,1425,1425,1425,1425,1425,1425,1425,1425,819,819,1716,1716,1716,1188,2048,1585,1561,1503,1700,1399,1399,1681,1714,762,762,1587,1305,2038,1714,1741,1501,1741,1577,1475,1397,1663,1585,2259,1579,1483,1485,936,748,936,1716,1024,1024,1382,1466,1214,1466,1389,891,1466,1458,702,702,1362,702,2134,1458,1407,1466,1466,1010,1219,979,1458,1335,1892,1321,1335,1192,1458,748,1458,1716] },
  serifBold: { em: 2048, w: [713,899,1067,1716,1425,1946,1849,627,969,969,1071,1716,713,850,713,748,1425,1425,1425,1425,1425,1425,1425,1425,1425,1425,756,756,1716,1716,1716,1200,2048,1589,1731,1630,1776,1561,1454,1749,1935,958,969,1780,1440,2267,1872,1784,1540,1784,1702,1479,1524,1786,1589,2300,1589,1462,1495,969,748,969,1716,1024,1024,1327,1432,1247,1432,1303,881,1432,1489,778,741,1419,778,2167,1489,1366,1432,1432,1079,1153,946,1489,1190,1763,1221,1190,1163,1317,745,1317,1716] },
};
const WIDEST = Object.fromEntries(Object.entries(FONT_WIDTHS).map(([k, t]) => [k, Math.max(...t.w)]));

// The width of `s` at `fs` px in `face`. A character outside the table counts
// as the face's widest glyph, so an unmeasured name errs wide, never narrow.
export function textWidth(s, fs, face = "sans") {
  const t = FONT_WIDTHS[face];
  let u = 0;
  for (const ch of String(s)) {
    const c = ch.codePointAt(0);
    u += c >= 32 && c <= 126 ? t.w[c - 32] : WIDEST[face];
  }
  return u * fs / t.em;
}

// `s` at the largest size from `fs` down to `minFs` at which it fits `maxW`;
// if it does not fit even at `minFs`, cut with an ellipsis until it does.
export function fitText(s, maxW, fs, face = "sans", minFs = fs * 0.75) {
  const w = textWidth(s, fs, face);
  if (w <= maxW) return { text: s, fs };
  const f = Math.max(minFs, Math.floor(fs * maxW / w * 10) / 10);
  if (textWidth(s, f, face) <= maxW) return { text: s, fs: f };
  const chars = [...String(s)];
  while (chars.length > 1 && textWidth(chars.join("") + "…", f, face) > maxW) chars.pop();
  return { text: chars.join("").trimEnd() + "…", fs: f };
}

function mapGroup(geom, calls, byCode, x, y, w) {
  const s = w / geom.W;
  const paths = geom.wards.map((wd, i) => {
    const c = calls[i];
    return c
      ? `<path d="${wd.path}" fill="${byCode[c].colour}" stroke="${C.paper}" stroke-width="${(0.8 / s).toFixed(2)}"/>`
      : `<path d="${wd.path}" fill="${C.paper}" stroke="${C.rule}" stroke-width="${(1 / s).toFixed(2)}"/>`;
  }).join("");
  return `<g transform="translate(${x} ${y}) scale(${s.toFixed(4)})">${paths}</g>`;
}

function bars(top, byCode, x, y, w, rowH, maxSeats, fs) {
  // Columns: name | bar | seat count. The count column fits the widest count
  // drawn; the name column fits the widest name, up to half of what is left,
  // and a longer name is shrunk, then cut, to that column rather than run
  // into its bar.
  const gap = fs * 0.5;
  const numW = Math.max(...top.map(([, n]) => textWidth(String(n), fs, "sansBold"))) + gap;
  const nameMax = (w - numW) / 2;
  const nameW = Math.min(nameMax, Math.max(...top.map(([c]) => textWidth(byCode[c].name, fs)))) + gap;
  const barMax = w - nameW - numW;
  return top.map(([code, n], k) => {
    const p = byCode[code];
    const yy = y + k * rowH;
    const bw = Math.max(3, barMax * n / maxSeats);
    const nm = fitText(p.name, nameW - gap, fs);
    return `<text class="nm" x="${x}" y="${yy + fs * 0.9}" font-family="${SANS}" font-size="${nm.fs}" fill="${C.ink}">${esc(nm.text)}</text>` +
      `<rect x="${(x + nameW).toFixed(1)}" y="${yy + fs * 0.12}" width="${bw.toFixed(1)}" height="${fs * 0.95}" fill="${p.colour}"/>` +
      `<text x="${x + w}" y="${yy + fs * 0.9}" text-anchor="end" font-family="${SANS}" font-weight="700" font-size="${fs}" fill="${C.ink}">${n}</text>`;
  }).join("");
}

function councilOf(model) {
  const { council, majority } = model;
  if (!Number.isInteger(council) || council <= 0 || !Number.isInteger(majority))
    throw new Error("the card needs the council and majority the seat law returned (model.council, model.majority)");
  return { council, majority };
}

function coalitionText(f, seats, byCode, { council, majority }) {
  if (!f.coalition?.length) return { line: "No coalition picked", sub: "" };
  const names = f.coalition.map(c => byCode[c].name);
  const total = f.coalition.reduce((a, c) => a + (seats[c] || 0), 0);
  const list = names.length > 1 ? names.slice(0, -1).join(", ") + " and " + names.at(-1) : names[0];
  const sub = `${total} of ${council} seats — ` + (total >= majority
    ? `a majority (${majority} needed)` : `short of the ${majority} needed`);
  return { line: `${list} govern${names.length > 1 ? "" : "s"}`, sub };
}

// Wrap a string into lines no wider than `maxW` at `fs` in `face`, on spaces.
// A single word wider than `maxW` keeps a line of its own; callers that cannot
// allow that shrink the size (fitTitle) or cut the line (fitText).
function wrap(s, maxW, fs, face) {
  const out = []; let cur = "";
  for (const w of String(s).split(" ")) {
    const next = (cur + " " + w).trim();
    if (cur && textWidth(next, fs, face) > maxW) { out.push(cur); cur = w; }
    else cur = next;
  }
  if (cur) out.push(cur);
  return out;
}

// The title at the first size in `options` at which it wraps to two lines or
// fewer inside `maxW`; failing all of them, the last size stepped down until
// it does, so a 40-character name without a space still stays on the card.
function fitTitle(title, options, maxW) {
  const fits = (fs) => {
    const lines = wrap(title, maxW, fs, "serifBold");
    return lines.length <= 2 && lines.every(l => textWidth(l, fs, "serifBold") <= maxW) ? lines : null;
  };
  for (const o of options) {
    const lines = fits(o.fs);
    if (lines) return { ...o, lines };
  }
  const last = options.at(-1);
  for (let fs = last.fs - 1; fs >= 12; fs--) {
    const lines = fits(fs);
    if (lines) return { fs, lh: Math.round(last.lh * fs / last.fs), lines };
  }
  const fs = 12;
  return { fs, lh: Math.round(last.lh * fs / last.fs),
    lines: wrap(title, maxW, fs, "serifBold").slice(0, 2).map(l => fitText(l, maxW, fs, "serifBold", fs).text) };
}

// The coalition line: up to two lines inside `maxW`, the second cut if the
// list of parties runs longer.
function coalitionLines(line, maxW, fs) {
  const lines = wrap(line, maxW, fs, "serifBold");
  const two = lines.slice(0, 2);
  if (lines.length > 2) two[1] = fitText(two[1] + " " + lines.slice(2).join(" "), maxW, fs, "serifBold", fs).text;
  return two.map(l => fitText(l, maxW, fs, "serifBold", fs).text);
}

export function buildCardSVG({ forecast, seats, geom, byCode, model, size = "link", showName = true, placeholder = true }) {
  const [W, H] = SIZES[size];
  const name = showName ? forecast.display_name : "";
  const title = possessive(name);
  const top = topN(seats, 5, byCode);
  const maxSeats = Math.max(1, ...top.map(t => t[1]));
  const cm = councilOf(model);
  const co = coalitionText(forecast, seats, byCode, cm);
  const site = "joburg.whysoserious.city";
  const proto = placeholder
    ? `<text x="${W / 2}" y="${H - 10}" text-anchor="middle" font-family="${MONO}" font-size="${size === "link" ? 13 : 22}" fill="${C.bad}">PROTOTYPE — PLACEHOLDER DATA, NOT A REAL FORECAST</text>` : "";
  let body;

  if (size === "link") {
    const mapW = 640, mapX = 36, mapY = 118;
    const colX = 712, colW = 452;
    const T = fitTitle(title, [{ fs: 42, lh: 46 }, { fs: 34, lh: 38 }], W - 36 - colX);
    const tl = T.lines;
    const tY = 150;
    const barsY = tY + tl.length * T.lh + 30;
    const coY = barsY + 5 * 38 + 36;
    const coLines = coalitionLines(co.line, colW, 25);
    body =
      `<rect x="0" y="0" width="${W}" height="8" fill="${C.reader}"/>` +
      `<text x="36" y="58" font-family="${MONO}" font-size="22" font-weight="700" fill="${C.accent}">${site}</text>` +
      `<text x="36" y="90" font-family="${SANS}" font-size="19" fill="${C.ink2}">Who governs Johannesburg after 4 November 2026?</text>` +
      mapGroup(geom, forecast.ward_calls, byCode, mapX, mapY, mapW) +
      tl.map((l, k) => `<text x="${colX}" y="${tY + k * T.lh}" font-family="${SERIF}" font-size="${T.fs}" font-weight="600" fill="${C.ink}">${esc(l)}</text>`).join("") +
      `<text x="${colX}" y="${barsY - 10}" font-family="${SANS}" font-size="16" fill="${C.ink3}">Seats in the ${cm.council}-seat council, top five</text>` +
      bars(top, byCode, colX, barsY, colW, 38, maxSeats, 22) +
      coLines.map((l, k) => `<text x="${colX}" y="${coY + k * 30}" font-family="${SERIF}" font-size="25" font-weight="600" fill="${C.ink}">${esc(l)}</text>`).join("") +
      `<text x="${colX}" y="${coY + coLines.length * 30 + 2}" font-family="${SANS}" font-size="17" fill="${C.ink2}">${esc(co.sub)}</text>` +
      `<rect x="0" y="${H - 64}" width="${W}" height="64" fill="${C.paper2}"/>` +
      `<text x="36" y="${H - 34}" font-family="${SANS}" font-size="18" fill="${C.reader}">A reader's forecast, not the model's.</text>` +
      `<text x="${W - 36}" y="${H - 34}" text-anchor="end" font-family="${SANS}" font-size="18" fill="${C.ink2}">Make your own at ${site}</text>`;
  } else {
    const mapW = 900, mapX = 90;
    const T = fitTitle(title, [{ fs: 68, lh: 74 }, { fs: 54, lh: 60 }], W - 120);
    const tl = T.lines;
    const tY = 300;   // baseline; the cap line sits near 250, below the subtitle
    const mapY = tY + tl.length * T.lh - 10;
    const mapH = geom.H * mapW / geom.W;
    const barsY = mapY + mapH + 60;
    const coY = barsY + 5 * 56 + 64;
    const coLines = coalitionLines(co.line, W - 120, 42);
    // Everything that matters ends above y = 1720, clear of the story app's
    // reply bar; the footer follows the content rather than a fixed line.
    const footY = coY + coLines.length * 50 + 100;
    body =
      `<rect x="0" y="0" width="${W}" height="14" fill="${C.reader}"/>` +
      `<text x="60" y="170" font-family="${MONO}" font-size="36" font-weight="700" fill="${C.accent}">${site}</text>` +
      `<text x="60" y="216" font-family="${SANS}" font-size="30" fill="${C.ink2}">Who governs Johannesburg after 4 November?</text>` +
      tl.map((l, k) => `<text x="60" y="${tY + k * T.lh}" font-family="${SERIF}" font-size="${T.fs}" font-weight="600" fill="${C.ink}">${esc(l)}</text>`).join("") +
      mapGroup(geom, forecast.ward_calls, byCode, mapX, mapY, mapW) +
      `<text x="60" y="${barsY - 18}" font-family="${SANS}" font-size="26" fill="${C.ink3}">Seats in the ${cm.council}-seat council, top five</text>` +
      bars(top, byCode, 60, barsY, 960, 56, maxSeats, 34) +
      coLines.map((l, k) => `<text x="60" y="${coY + k * 50}" font-family="${SERIF}" font-size="42" font-weight="600" fill="${C.ink}">${esc(l)}</text>`).join("") +
      `<text x="60" y="${coY + coLines.length * 50 + 4}" font-family="${SANS}" font-size="28" fill="${C.ink2}">${esc(co.sub)}</text>` +
      `<text x="60" y="${footY}" font-family="${SANS}" font-size="30" fill="${C.reader}">A reader's forecast, not the model's.</text>` +
      `<text x="60" y="${footY + 46}" font-family="${SANS}" font-size="30" fill="${C.ink2}">Make your own at ${site}</text>`;
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">` +
    `<rect width="${W}" height="${H}" fill="${C.paper}"/>${body}${proto}</svg>`;
}

export function cardAlt({ forecast, seats, byCode, model, showName = true }) {
  const top = topN(seats, 5, byCode).map(([c, n]) => `${byCode[c].name} ${n}`).join(", ");
  const co = coalitionText(forecast, seats, byCode, councilOf(model));
  return `${possessive(showName ? forecast.display_name : "")} for the Johannesburg council: ` +
    `a ward map, top five seat totals (${top}), coalition: ${co.line}, ${co.sub}. A reader's forecast, not the model's.`;
}

export function svgToPNG(svg, [W, H]) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(new Blob([svg], { type: "image/svg+xml;charset=utf-8" }));
    img.onload = () => {
      const cv = document.createElement("canvas");
      cv.width = W; cv.height = H;
      cv.getContext("2d").drawImage(img, 0, 0, W, H);
      URL.revokeObjectURL(url);
      cv.toBlob(b => b ? resolve(b) : reject(new Error("toBlob failed")), "image/png");
    };
    img.onerror = () => { URL.revokeObjectURL(url); reject(new Error("SVG did not load")); };
    img.src = url;
  });
}
