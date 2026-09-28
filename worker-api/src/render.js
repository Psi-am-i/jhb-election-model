// /f/<id> as server-rendered HTML with Open Graph tags, and the share card as
// a PNG rendered here from the stored, validated forecast.
//
// ONE card builder: buildCardSVG is imported from the page's own
// interactive/js/card.js, never copied (BACKEND.md §5). The server differs only
// in the rasteriser: resvg-wasm with embedded DejaVu fonts (Bitstream Vera
// licence, free to embed and redistribute), so crawlers see one stable image
// whatever fonts a phone has.
//
// No image is ever accepted from a client. Nothing a reader typed reaches the
// SVG or the HTML without escaping (esc, from the page's common.js).

import { initWasm, Resvg } from "@resvg/resvg-wasm";
import resvgWasm from "@resvg/resvg-wasm/index_bg.wasm";
import sansTTF from "dejavu-fonts-ttf/ttf/DejaVuSans.ttf";
import sansBoldTTF from "dejavu-fonts-ttf/ttf/DejaVuSans-Bold.ttf";
import serifBoldTTF from "dejavu-fonts-ttf/ttf/DejaVuSerif-Bold.ttf";
import monoBoldTTF from "dejavu-fonts-ttf/ttf/DejaVuSansMono-Bold.ttf";
import { buildCardSVG, cardAlt, SIZES } from "../../interactive/js/card.js";
import { esc, possessive, topN } from "../../interactive/js/common.js";

export { SIZES };

export function byCodeOf(schema) {
  return Object.fromEntries(schema["x-parties"].map(p => [p.code, p]));
}

function cardInputs(row, schema, geom) {
  const forecast = JSON.parse(row.body);
  const answer = JSON.parse(row.seats);
  return {
    forecast, seats: answer.seats, geom, byCode: byCodeOf(schema),
    // The council and majority the seat law returned for THIS forecast, not
    // the configured size: the card must say what was seated.
    model: { council: answer.council_total, majority: answer.majority },
    showName: Boolean(forecast.display_name),
    placeholder: schema["x-placeholder"],
  };
}

export function cardSVG(row, schema, geom, size = "link") {
  return buildCardSVG({ ...cardInputs(row, schema, geom), size });
}

// Initialised once per isolate: this caches a compiled module and font bytes,
// not anything belonging to a request.
let ready;
function resvgReady() {
  ready ??= initWasm(resvgWasm);
  return ready;
}

export async function renderPNG(svg) {
  await resvgReady();
  const r = new Resvg(svg, {
    font: {
      fontBuffers: [sansTTF, sansBoldTTF, serifBoldTTF, monoBoldTTF].map(b => new Uint8Array(b)),
      defaultFontFamily: "DejaVu Sans",
      sansSerifFamily: "DejaVu Sans",
      serifFamily: "DejaVu Serif",
      monospaceFamily: "DejaVu Sans Mono",
    },
    fitTo: { mode: "original" },
  });
  try {
    const img = r.render();
    try { return img.asPng(); } finally { img.free(); }
  } finally { r.free(); }
}

export const cardKey = (row, size) => `cards/${row.id}/${row.rev}-${row.seats_code_ref.slice(0, 16)}/${size}.png`;

const SHARE = [
  ["X", u => `https://x.com/intent/post?url=${u}`],
  ["Facebook", u => `https://www.facebook.com/sharer/sharer.php?u=${u}`],
  ["LinkedIn", u => `https://www.linkedin.com/sharing/share-offsite/?url=${u}`],
  ["WhatsApp", u => `https://wa.me/?text=${u}`],
  ["Email", u => `mailto:?subject=${encodeURIComponent("A Johannesburg election forecast")}&body=${u}`],
];

const STYLE = `:root{color-scheme:dark;--paper:#141715;--ink:#eceee9;--ink2:#b6bcb6;--reader:#b98ad6;--accent:#d9954f}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
.wrap{max-width:960px;margin:0 auto;padding:16px}a{color:var(--accent)}
.stamp{color:var(--reader);font-weight:700;text-transform:uppercase;font-size:13px;letter-spacing:.06em}
.notours{border:1px solid var(--reader);padding:10px 12px;border-radius:6px}
figure{margin:16px 0}figure svg{width:100%;height:auto;display:block}
table{border-collapse:collapse}td,th{padding:3px 10px 3px 0;text-align:left}td.n{text-align:right}
.share a{margin-right:12px}.proto{color:#d98070;font-weight:700}`;

export function forecastPage(row, schema, geom, env) {
  const { forecast, seats, byCode, model } = cardInputs(row, schema, geom);
  const title = possessive(forecast.display_name);
  const url = `${env.SITE_ORIGIN}/f/${row.id}`;
  const img = `${url}/card.png?v=${row.rev}`;
  const alt = cardAlt(cardInputs(row, schema, geom));
  const s = JSON.parse(row.seats);
  const rows = topN(seats, Object.keys(seats).length, byCode)
    .map(([c, n]) => `<tr><td>${esc(byCode[c].name)}</td><td class="n">${n}</td><td class="n">${s.ward[c] || 0}</td><td class="n">${s.pr[c] || 0}</td></tr>`).join("");
  const co = forecast.coalition;
  const coSeats = co.reduce((a, c) => a + (seats[c] || 0), 0);
  const coNames = co.map(c => esc(byCode[c].name)).join(", ");
  const u = encodeURIComponent(url);
  const made = new Date(row.created_at).toISOString().slice(0, 10);
  const proto = schema["x-placeholder"]
    ? `<p class="proto">Prototype: the roster and ward list are placeholders, not the IEC's.</p>` : "";
  return `<!doctype html>
<html lang="en-ZA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)} · Johannesburg 2026</title>
<meta name="description" content="A reader's forecast of the Johannesburg council, not the model's. Make your own.">
<meta name="robots" content="noindex">
<link rel="canonical" href="${esc(url)}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="joburg.whysoserious.city">
<meta property="og:title" content="${esc(title)} for Johannesburg">
<meta property="og:description" content="Their ward map, seats and coalition. A reader's forecast, not the model's.">
<meta property="og:url" content="${esc(url)}">
<meta property="og:image" content="${esc(img)}">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="${SIZES.link[0]}">
<meta property="og:image:height" content="${SIZES.link[1]}">
<meta property="og:image:alt" content="${esc(alt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="${esc(img)}">
<style>${STYLE}</style>
</head>
<body><div class="wrap"><main>
${proto}<p class="stamp">A reader's forecast</p>
<h1>${esc(title)}</h1>
<p>Made ${made}. Model run ${esc(forecast.model_ref)}.</p>
<p class="notours">This is a forecast made by a reader, not by the model. It shows what they expect; nobody checked it against the evidence. The model's forecast is on the <a href="/forecast.html">forecast page</a>.</p>
<figure>${cardSVG(row, schema, geom, "link")}<figcaption>${esc(alt)}</figcaption></figure>
<h2>Their council</h2>
<table><thead><tr><th>Party</th><th>Seats</th><th>Wards</th><th>List</th></tr></thead><tbody>${rows}</tbody></table>
<p>${s.council_total} seats in all.</p>
<h2>Who governs</h2>
<p><b>${coNames}</b>: ${coSeats} seats, ${coSeats >= model.majority ? "a majority" : `short of the ${model.majority} needed`}.${forecast.mayor ? ` Mayor from ${esc(byCode[forecast.mayor].name)}.` : ""}</p>
<h2>Share</h2>
<p class="share">${SHARE.map(([n, f]) => `<a href="${esc(f(u))}" rel="noopener">${n}</a>`).join("")}</p>
<p><a href="/make">Make your own forecast</a> · <a href="/privacy#report">Report this forecast</a></p>
</main></div></body></html>`;
}

const GONE = {
  deleted: ["Forecast deleted", "This forecast was deleted", "It was deleted, so the link no longer works."],
  hidden: ["Forecast withheld", "This forecast is withheld", "It was reported and is withheld while it is reviewed."],
  missing: ["Forecast not found", "We can't find that forecast", "The link may be mistyped, or the forecast was never saved."],
};

export function gonePage(kind) {
  const [t, h, p] = GONE[kind];
  return `<!doctype html><html lang="en-ZA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><title>${t}</title><style>${STYLE}</style></head>
<body><div class="wrap"><main><h1>${h}</h1>
<p>${p} You can <a href="/make">make your own forecast</a> or see <a href="/forecast.html">the model's</a>.</p></main></div></body></html>`;
}
