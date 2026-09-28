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
  const nameW = fs * 7.2;
  return top.map(([code, n], k) => {
    const p = byCode[code];
    const yy = y + k * rowH;
    const bw = Math.max(3, (w - nameW - fs * 3.2) * n / maxSeats);
    return `<text x="${x}" y="${yy + fs * 0.9}" font-family="${SANS}" font-size="${fs}" fill="${C.ink}">${esc(p.name)}</text>` +
      `<rect x="${x + nameW}" y="${yy + fs * 0.12}" width="${bw.toFixed(1)}" height="${fs * 0.95}" fill="${p.colour}"/>` +
      `<text x="${x + w}" y="${yy + fs * 0.9}" text-anchor="end" font-family="${SANS}" font-weight="700" font-size="${fs}" fill="${C.ink}">${n}</text>`;
  }).join("");
}

function coalitionText(f, seats, byCode, majority) {
  if (!f.coalition?.length) return { line: "No coalition picked", sub: "" };
  const names = f.coalition.map(c => byCode[c].name);
  const total = f.coalition.reduce((a, c) => a + (seats[c] || 0), 0);
  const list = names.length > 1 ? names.slice(0, -1).join(", ") + " and " + names.at(-1) : names[0];
  const sub = `${total} of 270 seats — ` + (total >= majority
    ? `a majority (${majority} needed)` : `short of the ${majority} needed`);
  return { line: `${list} govern${names.length > 1 ? "" : "s"}`, sub };
}

// Wrap a string into lines of at most `n` characters, on spaces.
function wrap(s, n) {
  const out = []; let cur = "";
  for (const w of s.split(" ")) {
    if ((cur + " " + w).trim().length > n && cur) { out.push(cur); cur = w; }
    else cur = (cur + " " + w).trim();
  }
  if (cur) out.push(cur);
  return out;
}

// The longest title a 40-character name can make still fits: try each type
// size in turn and take the first at which it wraps to two lines or fewer.
function fitTitle(title, options) {
  for (const o of options) {
    const lines = wrap(title, o.n);
    if (lines.length <= 2) return { ...o, lines };
  }
  const o = options.at(-1);
  return { ...o, lines: wrap(title, o.n).slice(0, 3) };
}

export function buildCardSVG({ forecast, seats, geom, byCode, model, size = "link", showName = true, placeholder = true }) {
  const [W, H] = SIZES[size];
  const name = showName ? forecast.display_name : "";
  const title = possessive(name);
  const top = topN(seats, 5, byCode);
  const maxSeats = Math.max(1, ...top.map(t => t[1]));
  const co = coalitionText(forecast, seats, byCode, model.majority);
  const site = "joburg.whysoserious.city";
  const proto = placeholder
    ? `<text x="${W / 2}" y="${H - 10}" text-anchor="middle" font-family="${MONO}" font-size="${size === "link" ? 13 : 22}" fill="${C.bad}">PROTOTYPE — PLACEHOLDER DATA, NOT A REAL FORECAST</text>` : "";
  let body;

  if (size === "link") {
    const mapW = 640, mapX = 36, mapY = 118;
    const colX = 712, colW = 452;
    const T = fitTitle(title, [{ n: 22, fs: 42, lh: 46 }, { n: 28, fs: 34, lh: 38 }]);
    const tl = T.lines;
    const tY = 150;
    const barsY = tY + tl.length * T.lh + 30;
    const coY = barsY + 5 * 38 + 36;
    body =
      `<rect x="0" y="0" width="${W}" height="8" fill="${C.reader}"/>` +
      `<text x="36" y="58" font-family="${MONO}" font-size="22" font-weight="700" fill="${C.accent}">${site}</text>` +
      `<text x="36" y="90" font-family="${SANS}" font-size="19" fill="${C.ink2}">Who governs Johannesburg after 4 November 2026?</text>` +
      mapGroup(geom, forecast.ward_calls, byCode, mapX, mapY, mapW) +
      tl.map((l, k) => `<text x="${colX}" y="${tY + k * T.lh}" font-family="${SERIF}" font-size="${T.fs}" font-weight="600" fill="${C.ink}">${esc(l)}</text>`).join("") +
      `<text x="${colX}" y="${barsY - 10}" font-family="${SANS}" font-size="16" fill="${C.ink3}">Seats in the 270-seat council, top five</text>` +
      bars(top, byCode, colX, barsY, colW, 38, maxSeats, 22) +
      wrap(co.line, 34).slice(0, 2).map((l, k) => `<text x="${colX}" y="${coY + k * 30}" font-family="${SERIF}" font-size="25" font-weight="600" fill="${C.ink}">${esc(l)}</text>`).join("") +
      `<text x="${colX}" y="${coY + (wrap(co.line, 34).slice(0, 2).length) * 30 + 2}" font-family="${SANS}" font-size="17" fill="${C.ink2}">${esc(co.sub)}</text>` +
      `<rect x="0" y="${H - 64}" width="${W}" height="64" fill="${C.paper2}"/>` +
      `<text x="36" y="${H - 34}" font-family="${SANS}" font-size="18" fill="${C.reader}">A reader's forecast, not the model's.</text>` +
      `<text x="${W - 36}" y="${H - 34}" text-anchor="end" font-family="${SANS}" font-size="18" fill="${C.ink2}">Make your own at ${site}</text>`;
  } else {
    const mapW = 900, mapX = 90;
    const T = fitTitle(title, [{ n: 20, fs: 68, lh: 74 }, { n: 26, fs: 54, lh: 60 }]);
    const tl = T.lines;
    const tY = 300;   // baseline; the cap line sits near 250, below the subtitle
    const mapY = tY + tl.length * T.lh - 10;
    const mapH = geom.H * mapW / geom.W;
    const barsY = mapY + mapH + 60;
    const coY = barsY + 5 * 56 + 64;
    const coLines = wrap(co.line, 30).slice(0, 2);
    // Everything that matters ends above y = 1720, clear of the story app's
    // reply bar; the footer follows the content rather than a fixed line.
    const footY = coY + coLines.length * 50 + 100;
    body =
      `<rect x="0" y="0" width="${W}" height="14" fill="${C.reader}"/>` +
      `<text x="60" y="170" font-family="${MONO}" font-size="36" font-weight="700" fill="${C.accent}">${site}</text>` +
      `<text x="60" y="216" font-family="${SANS}" font-size="30" fill="${C.ink2}">Who governs Johannesburg after 4 November?</text>` +
      tl.map((l, k) => `<text x="60" y="${tY + k * T.lh}" font-family="${SERIF}" font-size="${T.fs}" font-weight="600" fill="${C.ink}">${esc(l)}</text>`).join("") +
      mapGroup(geom, forecast.ward_calls, byCode, mapX, mapY, mapW) +
      `<text x="60" y="${barsY - 18}" font-family="${SANS}" font-size="26" fill="${C.ink3}">Seats in the 270-seat council, top five</text>` +
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
  const co = coalitionText(forecast, seats, byCode, model.majority);
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
