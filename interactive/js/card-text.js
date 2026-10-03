// Text layout by MEASURED width, and SVG to PNG, for both share cards: the
// builder's (card.js) and "play with the model"'s (play-card.js). One
// definition; card.js re-exports it for the worker-api.
//
// Pure apart from svgToPNG, which needs a browser (Image, canvas). Served with
// /your-forecast/ section 1 and read by stats.script_writes as a NON-writer module: it puts no
// figure on a page.

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

// The SVG as a PNG blob. `under`, if given, is a photograph drawn on the
// canvas first, beneath the SVG: { src, sx, sy, sw, sh, dx, dy, dw, dh } as
// drawImage takes them. It is drawn here and not inside the SVG because an
// SVG loaded as an image may not fetch, and a browser can refuse to export a
// canvas an SVG <image> was drawn into. `src` must be same-origin.
//
// `label`, if given, is the site's name, drawn on the canvas after the SVG
// in the page's own IBM Plex Mono: an SVG drawn as an image cannot load a
// web font, the canvas can once the page has it, so this waits for
// document.fonts before drawing. { text, x, y, fs, weight, fill, rotate
// (degrees, about x, y), mark: { src, w, h } }: the mark (the logo's
// tower-J, same-origin) is drawn first, in `fill`, its foot on the
// baseline's descender line, and the name follows it.
export const LABEL_FONT = '"IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace';
export function svgToPNG(svg, [W, H], under = null, label = null) {
  const load = src => new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error("image did not load"));
    img.src = src;
  });
  const font = label ? label.weight + " " + label.fs + "px " + LABEL_FONT : "";
  const fontReady = label && document.fonts ? document.fonts.load(font, label.text).catch(() => null) : null;
  const url = URL.createObjectURL(new Blob([svg], { type: "image/svg+xml;charset=utf-8" }));
  return Promise.all([load(url), under ? load(under.src) : null, label && label.mark ? load(label.mark.src) : null, fontReady])
    .then(([img, photo, mark]) => {
      URL.revokeObjectURL(url);
      const cv = document.createElement("canvas");
      cv.width = W; cv.height = H;
      const g = cv.getContext("2d");
      if (photo) g.drawImage(photo, under.sx, under.sy, under.sw, under.sh, under.dx, under.dy, under.dw, under.dh);
      g.drawImage(img, 0, 0, W, H);
      if (label) drawLabel(g, label, mark, font);
      return new Promise((resolve, reject) =>
        cv.toBlob(b => b ? resolve(b) : reject(new Error("toBlob failed")), "image/png"));
    }, e => { URL.revokeObjectURL(url); throw e; });
}

function drawLabel(g, label, mark, font) {
  g.save();
  g.translate(label.x, label.y);
  if (label.rotate) g.rotate(label.rotate * Math.PI / 180);
  let x = 0;
  if (mark) {
    // the mark in the label's colour: drawn alone, then filled where it is
    const { w, h } = label.mark;
    const m = document.createElement("canvas");
    m.width = Math.ceil(w); m.height = Math.ceil(h);
    const mg = m.getContext("2d");
    mg.drawImage(mark, 0, 0, w, h);
    mg.globalCompositeOperation = "source-in";
    mg.fillStyle = label.fill;
    mg.fillRect(0, 0, w, h);
    g.drawImage(m, 0, label.fs * 0.28 - h, w, h);
    x = w + label.fs * 0.15;
  }
  g.font = font;
  g.fillStyle = label.fill;
  g.textBaseline = "alphabetic";
  g.fillText(label.text, x, 0);
  g.restore();
}
