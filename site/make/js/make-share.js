// "Make your own forecast": the share sheet. Anonymous: what is shared is the
// page's address, which carries the whole forecast (make-state.js), and an
// image drawn in the browser from the seats the page is showing
// (forecast-card.js). Nothing is sent anywhere or stored.
//
// ⛔ A LIVE WRITER (stats.LIVE_WRITERS["make/js/make-share.js"]), for the one
// region "share": the button and the <dialog> it opens are in make.html,
// inside that region, and every element is reached through a literal
// '[data-live="share"] …' selector, taken once, below. It writes with
// textContent and properties, never markup.
//
// Practice it follows (as /play/'s play-share.js):
//  * the image is drawn before the share button is enabled, so the native
//    share call happens inside the tap (Safari drops the gesture across an
//    await); files are attached only when navigator.canShare({files}) allows;
//  * Copy link is always there, with a select-and-copy fallback;
//  * native <dialog> + showModal(): the page behind is inert, Escape closes,
//    focus returns to the button that opened it.

import { buildForecastCardSVG, forecastCardAlt, cardTitle, photoUnder, PHOTO_FILE, SITE, SIZES, OTHERS_COLOUR } from "./forecast-card.js";
import { svgToPNG } from "./card-text.js";
import { nameRule, NAME_MAX } from "./make-state.js";

const S = {
  open: document.querySelector('[data-live="share"] .shareopen'),
  dlg: document.querySelector('[data-live="share"] dialog'),
  close: document.querySelector('[data-live="share"] .x'),
  name: document.querySelector('[data-live="share"] .shname'),
  nameerr: document.querySelector('[data-live="share"] .shnameerr'),
  url: document.querySelector('[data-live="share"] .shurl'),
  copy: document.querySelector('[data-live="share"] .shcopy'),
  native: document.querySelector('[data-live="share"] .shnative'),
  img: document.querySelector('[data-live="share"] .preview img'),
  dl: document.querySelector('[data-live="share"] .shdl'),
  toast: document.querySelector('[data-live="share"] .toast'),
};
S.name.maxLength = NAME_MAX + 8;          // the rule, not the box, says what is too long

// The site's photograph, beside the page's own directory: /share.jpg.
const PHOTO_SRC = new URL("../../" + PHOTO_FILE, import.meta.url).href;
const MADE = new Date().toISOString().slice(0, 10);
const PARTY_ROWS = 9;

let now = null, png = null, shown = null, opener = null, nameCb = () => {}, drawing = 0;

export function onNameChange(cb) { nameCb = cb; }

// What the page is showing now: { url, name, calls, seats, council, majority,
// coalition, geom, party(code) -> {name, colour} }.
export function setShareable(info) {
  now = info;
  png = null;
  S.open.disabled = false;
  if (S.dlg.open) fill();
}

const say = s => { S.toast.textContent = s; };

// "2026-11-04" as "4 November 2026", from the city config the build read.
const MONTHS = "January February March April May June July August September October November December".split(" ");
const dateText = iso => { const [y, m, d] = iso.split("-").map(Number); return d + " " + MONTHS[m - 1] + " " + y; };

// The card's words and figures, from the seats the page is showing.
export function cardOf(info) {
  const { seats, council, majority, coalition, party } = info;
  const list = Object.keys(seats).filter(c => seats[c] > 0)
    .sort((a, b) => seats[b] - seats[a] || party(a).name.localeCompare(party(b).name));
  const shown = list.length > PARTY_ROWS + 1 ? list.slice(0, PARTY_ROWS) : list;
  const rows = shown.map(c => ({ label: party(c).name, colour: party(c).colour, value: String(seats[c]), n: seats[c] }));
  const rest = list.slice(shown.length).reduce((a, c) => a + seats[c], 0);
  if (rest) rows.push({ label: "Others", colour: OTHERS_COLOUR, value: String(rest), n: rest });
  const cs = coalition.reduce((a, c) => a + (seats[c] || 0), 0);
  const rowsNote = coalition.length
    ? "Governing: " + coalition.map(c => party(c).name).join(", ") + ". " + cs + " of " + council + " seats" + (cs >= majority ? "." : ", short of a majority.")
    : "";
  return {
    title: cardTitle(info.name),
    lines: [{ text: info.election.city + " council, " + dateText(info.election.date) + " · " + council + " seats, " + majority + " for a majority", tone: "muted" }],
    map: { W: info.geom.W, H: info.geom.H, wards: info.geom.wards.map((w, i) => ({ path: w.path, fill: party(info.calls[i]).colour })) },
    mapNote: "Each ward in the colour of the party the reader called it for.",
    rows, rowsNote,
    foot: ["A reader's forecast: the reader called the wards and set the vote, and the seats follow from the law. Not the model's forecast.",
           "Made " + MADE + ". Make your own at " + SITE + "/make"],
  };
}

function fill() {
  S.url.value = now.url;
  if (document.activeElement !== S.name) S.name.value = now.name || "";
  S.native.hidden = typeof navigator.share !== "function";
  draw();
}

async function draw() {
  const ticket = ++drawing, info = now;
  S.native.disabled = true;
  S.dl.disabled = true;
  const card = cardOf(info);
  S.img.alt = forecastCardAlt(card);
  let made;
  try {
    made = await svgToPNG(buildForecastCardSVG(card), SIZES.link, photoUnder("link", PHOTO_SRC));
  } catch (e) {
    if (ticket === drawing) { say("The image could not be drawn in this browser. The link still works."); S.native.disabled = false; }
    return;
  }
  if (ticket !== drawing) return;           // a newer draw replaced this one
  png = made;
  if (shown) URL.revokeObjectURL(shown);
  shown = URL.createObjectURL(png);
  S.img.src = shown;
  S.native.disabled = false;
  S.dl.disabled = false;
}

const fileName = () => "joburg-forecast.png";

S.open.addEventListener("click", () => {
  if (!now) return;
  opener = S.open;
  say("");
  S.dlg.showModal();
  fill();
  S.copy.focus();
});
S.close.addEventListener("click", () => S.dlg.close());
S.dlg.addEventListener("click", e => { if (e.target === S.dlg) S.dlg.close(); });
S.dlg.addEventListener("close", () => opener?.focus?.());
S.name.addEventListener("input", () => {
  const r = nameRule(S.name.value);
  S.nameerr.textContent = r.ok ? "" : "This name cannot be used: " + r.reason + ".";
  if (!r.ok) return;
  nameCb(r.value);            // the page rewrites the address and calls setShareable
});
S.copy.addEventListener("click", async () => {
  let ok = false;
  try { await navigator.clipboard.writeText(now.url); ok = true; }
  catch (e) {
    S.url.select();
    try { ok = document.execCommand?.("copy") === true; } catch (e2) { ok = false; }
  }
  say(ok ? "Link copied." : "Copying did not work here. The link is selected: copy it from the box.");
});
S.native.addEventListener("click", () => {
  const data = { title: "Make your own Johannesburg election forecast", text: "My forecast for the Johannesburg council.", url: now.url };
  if (png) {
    const f = new File([png], fileName(), { type: "image/png" });
    if (navigator.canShare?.({ files: [f] })) data.files = [f];
  }
  navigator.share(data).then(() => say("Shared."))
    .catch(err => { if (err.name !== "AbortError") say("Sharing did not work here. Copy the link instead."); });
});
S.dl.addEventListener("click", () => {
  if (!png) return;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(png);
  a.download = fileName();
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 10000);
  say("Image downloaded.");
});
