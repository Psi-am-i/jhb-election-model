// The share image of a council: "[Name]'s Election Forecast", a ward map, one
// seat bar per party, on the site's photograph of Hillbrow Tower.
//
// ONE MODULE FOR EVERY PAGE'S CARD. It knows nothing about where its figures
// came from: the page hands it the title's name, the subtitle, the wards'
// paths and fills, the rows (label, colour, value as text) and the foot lines,
// all from the result that page is showing. "Make your own forecast"
// (make-share.js) is its first caller; /play/'s card is meant to become one
// (the redesign on branch play-redesign; the lead unifies at merge).
//
// ⛔ A LIVE WRITER WITH NO REGION (stats.LIVE_WRITERS["make/js/forecast-card.js"]):
// it turns figures it is handed into an SVG, and reaches no element of the
// page. It may hold no data block and open no data source.
//
// The photograph is not in the SVG: an SVG drawn as an image may not fetch,
// and a canvas an SVG <image> was drawn into can refuse to export. The page
// passes PHOTO (where and how to crop it) to card-text.js's svgToPNG, which
// draws it under the SVG; the SVG leaves that strip transparent and shades its
// edge into the paper.
//
// Text is laid out by measured width (card-text.js): a long name drops to a
// smaller size, then is cut with an ellipsis; a long party name the same.
// Literal hex and system fonts: the image leaves the page, and an SVG drawn
// into a canvas cannot load web fonts.

import { textWidth, fitText } from "./card-text.js";

export const W = 1200, H = 630;
const STRIP = 250;
// share.jpg is 1200 x 630 with the tower right of centre; this crop keeps it.
export const PHOTO = { file: "share.jpg", sx: 488, sy: 0, sw: STRIP, sh: H, dx: 0, dy: 0, dw: STRIP, dh: H };
export const SITE = "joburg.whysoserious.city";

const C = { paper: "#141715", rule: "#333833", ink: "#eceee9", ink2: "#b6bcb6", ink3: "#868d86", dark: "#1b1208" };
const SERIF = "'Iowan Old Style','Palatino Linotype',Palatino,Georgia,serif";
const SANS = "ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif";
const MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace";

const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

export function cardTitle(name) {
  if (!name) return "My Election Forecast";
  return name + (/s$/i.test(name) ? "'" : "'s") + " Election Forecast";
}

function text(x, y, s, { fs, family = SANS, fill = C.ink2, weight = "", anchor = "" }) {
  return `<text x="${x}" y="${y}" font-family="${family}" font-size="${fs}"${weight ? ` font-weight="${weight}"` : ""}${anchor ? ` text-anchor="${anchor}"` : ""} fill="${fill}">${esc(s)}</text>`;
}

// Wrap on spaces into lines no wider than maxW.
function wrap(s, maxW, fs) {
  const out = [];
  let cur = "";
  for (const w of String(s).split(" ")) {
    const next = (cur + " " + w).trim();
    if (cur && textWidth(next, fs) > maxW) { out.push(cur); cur = w; }
    else cur = next;
  }
  if (cur) out.push(cur);
  return out;
}

// { name, subtitle, map: {W, H, wards: [{path, fill}]}, rows: [{label, colour,
//   value, n}], note, foot: [line] }. `n` is the bar length; `value` the text.
export function buildForecastCardSVG({ name, subtitle, map, rows, note = "", foot = [] }) {
  const x0 = STRIP + 18, right = W - 34;
  const title = fitText(cardTitle(name), right - x0, 44, "serifBold", 30);
  let body = "";
  body += `<defs><linearGradient id="fade" x1="0" x2="1" y1="0" y2="0"><stop offset="0.7" stop-color="${C.paper}" stop-opacity="0"/><stop offset="1" stop-color="${C.paper}"/></linearGradient></defs>`;
  body += `<rect x="${STRIP}" y="0" width="${W - STRIP}" height="${H}" fill="${C.paper}"/>`;
  body += `<rect x="0" y="0" width="${STRIP}" height="${H}" fill="url(#fade)"/>`;
  body += `<text transform="translate(26 ${H - 22}) rotate(-90)" font-family="${MONO}" font-size="15" font-weight="700" fill="${C.dark}" letter-spacing="0.6">${esc(SITE)}</text>`;
  body += text(x0, 74, title.text, { fs: title.fs, family: SERIF, fill: C.ink, weight: "600" });
  body += text(x0, 104, subtitle, { fs: 16 });

  // the map, fitted into its box
  const mx = x0, my = 134, mw = 520, mh = 380;
  const s = Math.min(mw / map.W, mh / map.H);
  const ox = mx + (mw - map.W * s) / 2, oy = my + (mh - map.H * s) / 2;
  body += `<g transform="translate(${ox.toFixed(1)} ${oy.toFixed(1)}) scale(${s.toFixed(5)})" stroke="${C.paper}" stroke-width="${(0.8 / s).toFixed(2)}" stroke-linejoin="round">` +
    map.wards.map(w => `<path d="${w.path}" fill="${w.fill}"/>`).join("") + "</g>";

  // the seat rows
  const rx = mx + mw + 26, rw = right - rx;
  const rowH = Math.min(29, Math.floor(380 / Math.max(1, rows.length)));
  const top = Math.max(1, ...rows.map(r => r.n));
  const nameW = 112, valW = 44, barW = rw - nameW - valW - 12;
  const ry = my + (mh - rows.length * rowH) / 2;
  rows.forEach((r, k) => {
    const y = ry + k * rowH;
    const nm = fitText(r.label, nameW - 6, 15, "sansBold", 11);
    body += text(rx, (y + rowH * 0.66).toFixed(1), nm.text, { fs: nm.fs, fill: C.ink, weight: "600" });
    body += `<rect x="${rx + nameW}" y="${(y + rowH * 0.26).toFixed(1)}" width="${Math.max(3, barW * r.n / top).toFixed(1)}" height="14" rx="2" fill="${r.colour}"/>`;
    body += text(right, (y + rowH * 0.7).toFixed(1), r.value, { fs: 19, fill: C.ink, weight: "700", anchor: "end" });
  });
  if (note) {
    wrap(note, rw, 13).slice(0, 3).forEach((l, k) => {
      body += text(rx, (ry + rows.length * rowH + 22 + k * 17).toFixed(1), l, { fs: 13, fill: C.ink3 });
    });
  }

  // the foot
  const lines = foot.flatMap(l => wrap(l, right - x0, 12)).slice(0, 3);
  const fy = H - 14 - (lines.length - 1) * 17;
  body += `<rect x="${x0}" y="${fy - 22}" width="${right - x0}" height="1" fill="${C.rule}"/>`;
  lines.forEach((l, k) => { body += text(x0, fy + k * 17, l, { fs: 12, fill: C.ink3 }); });

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${body}</svg>`;
}

// The image's text alternative: the same words and figures, in the same order.
export function forecastCardAlt({ name, subtitle, rows, note = "", foot = [] }) {
  return [cardTitle(name), subtitle, "Seats: " + rows.map(r => r.label + " " + r.value).join(", "), note, ...foot]
    .filter(Boolean).map(s => s.replace(/\.$/, "")).join(". ") + ".";
}
