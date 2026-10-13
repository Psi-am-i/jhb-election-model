// "Your forecast", section 1 ("Adjust the model"): its share sheet, the one
// sheet both sections use (share-sheet.js), with section 1's content.
//
// TWO THINGS TO SHARE (owner, 2026-10-06).
//  * Untouched, the page shows the model's own forecast. The image is the
//    model's card (play-card.js, drawn by share-card.js modelCardSVG: the
//    whysoserious.city logo, "forecast" and the forecast's date), the link is
//    the page's address with section 1's settings, and nothing is sealed: it
//    is not a reader's prediction and not an entry. The sheet has no name
//    field for it (owner, 2026-10-13: nameShown), so no name is typed, kept,
//    sealed or drawn.
//  * Once a setting is moved, the reader shares a forecast of their own,
//    like section 2's: section 1's hand-off (the forecast section 2 opens
//    at from these settings: page.py handoff, src/prediction.py), seated by
//    the seat Worker, its chance worked out by page.py analyse, under the
//    reader's name, sealed and entered (share-sheet.js). make.js does that
//    work (setHandoff); the link carries section 1's settings and the sealed
//    forecast (yf-url.js compose), the image is share-card.js's reader card.
//
// ⛔ A LIVE WRITER (stats.LIVE_WRITERS["your-forecast/js/play-share.js"]), for
// the one region "share": the button and the <dialog> it opens are in
// your-forecast.html, inside that region, and every element is reached by a
// literal '[data-live="share"] …' selector, taken once, below, and handed to
// share-sheet.js. It writes with textContent and properties, never markup,
// and adds nothing outside the region.
//
// THE NAME (D6/D7, owner 2026-10-02). Free text, at most
// play-state.NAME_MAX characters, as play-state.cardName prints it, from ONE
// source for both sections (yf-url.js sealName: never the name of a shared
// link's sharer). It goes into the input's value, a sealed forecast's link
// (`n=`) and its entry, and the image, where share-card.js
// escapes it and draws it as text: "{name}'s Election Forecast" on the
// reader's own card, and nowhere on the model's. It is never written into the
// page as markup or as page text.
//
// ONLY SOUTH AFRICAN LAW IS SHARED (owner, 2026-10-03; play-state.shareable).
// Under another seat law the button is disabled and the note beside it says
// why: those laws are for comparison, and a shared council seated under them
// would read as a forecast.

import { buildPlayCardSVG, playCardAlt, section1Share, forecastWords, FORECAST_NAME } from "./play-card.js";
import { forecastSpec, linkCardSVG, storyCardSVG, cardAlt, cardTitle } from "./share-card.js";
import { shareSheet, loadAssets } from "./share-sheet.js";
import * as YU from "./yf-url.js";

const E = {
  open: document.querySelector('[data-live="share"] .shareopen'),
  why: document.querySelector('[data-live="share"] .pl-sharewhy'),
  dlg: document.querySelector('[data-live="share"] dialog'),
  close: document.querySelector('[data-live="share"] .x'),
  namefield: document.querySelector('[data-live="share"] .namefield'),
  name: document.querySelector('[data-live="share"] .shname'),
  namenote: document.querySelector('[data-live="share"] .shnamenote'),
  url: document.querySelector('[data-live="share"] .shurl'),
  copy: document.querySelector('[data-live="share"] .shcopy'),
  seal: document.querySelector('[data-live="share"] .shseal'),
  entry: document.querySelector('[data-live="share"] .shentry'),
  kind: document.querySelector('[data-live="share"] .shimg'),
  img: document.querySelector('[data-live="share"] .preview img'),
  wa: document.querySelector('[data-live="share"] .shwa'),
  x: document.querySelector('[data-live="share"] .shx'),
  native: document.querySelector('[data-live="share"] .shnative'),
  dl: document.querySelector('[data-live="share"] .shdl'),
  toast: document.querySelector('[data-live="share"] .toast'),
};

// What the page is showing now: { r, st, ctx, party, made, when, geometry,
// touched, shareable, lawName, onName }.
let now = null;

// The forecast's own date, forecast.json's `forecast_date` (written by
// src/build_make.py from the published run): printed on the model's card and
// in its words. Null where forecast.json cannot be read, and the card then
// cannot be drawn (a date typed here would be a second copy).
let forecastDate = null;
const dateP = fetch(new URL("../forecast.json", import.meta.url))
  .then(r => (r.ok ? r.json() : null)).catch(() => null)
  .then(F => { forecastDate = (F && /^\d{4}-\d{2}-\d{2}$/.test(F.forecast_date || "")) ? F.forecast_date : null; return forecastDate; });

// What section 2 (make.js) provides: forecast(settings) -> the hand-off as a
// reader's forecast, { fields: { v, c, f }, answer, outcome, vote, calls,
// party, baseline, election, geom }. Null if make.js never loaded.
let handoff = null;
export function setHandoff(h) { handoff = h; if (now) sheet.update(); }

// The name both sections seal and print: yf-url.js's, never a shared link's
// sharer's (sealName).
const nameNow = () => YU.sealName();
const content = section1Share({
  now: () => now, name: nameNow, handoff: () => handoff,
  page: () => ({ pathname: location.pathname, href: location.href }),
  changed: () => sheet.update(),
});

const sheet = shareSheet(E, {
  canOpen: () => !!(now && now.shareable),
  // a forecast that failed is tried again each time the sheet opens
  prepare: async () => { content.retry(); await dateP; },
  fields: () => content.fields(),
  link: () => content.link(),
  election: () => (content.ready()?.forecast || {}).election,
  emptyName: () => cardTitle(""),
  // the model's forecast has no name to type: the field is not offered
  nameShown: () => !!now.touched,
  // the model's forecast is entered nowhere; a reader's is
  entered: () => !!now.touched,
  // the page keeps the name in its address (model.js onName, yf-url.js); the
  // sheet redraws with it
  onName: n => { now.onName?.(n); sheet.update(); },
  shareWords: () => (now.touched ? { title: "My Johannesburg election prediction", text: "My prediction for the Johannesburg council." }
    : { title: forecastDate ? forecastWords(forecastDate) : FORECAST_NAME, text: "The Johannesburg election model's forecast." }),
  fileBase: () => now.touched
    ? "joburg-prediction-" + (nameNow() || "reader").replace(/[^A-Za-z0-9-]+/g, "-").replace(/^-+|-+$/g, "").toLowerCase().slice(0, 40)
    : "joburg-forecast" + (forecastDate ? "-" + forecastDate : ""),
  async card(kind, made) {
    const info = now, size = kind === "story" ? "story" : "link";
    if (!info.touched) {
      if (!forecastDate) return { wait: "No image: the forecast's date could not be read." };
      const card = { ...info, forecastDate };
      const assets = await loadAssets(info.r.shown, info.party);
      return { svg: buildPlayCardSVG({ ...card, size, assets }), size, alt: playCardAlt(card) };
    }
    content.ask();
    const f = content.fields();
    if (f === undefined) return { wait: "Working out your prediction from your settings." };
    if (f.failed) return { wait: "No image: your prediction could not be worked out (" + f.failed + "). The link still works." };
    const F = content.ready().forecast;
    const A = forecastSpec({ name: nameNow(), answer: F.answer, outcome: F.outcome, vote: F.vote, calls: F.calls, party: F.party,
      baseline: F.baseline, election: F.election, made });
    const assets = { ...(await loadAssets(A.rows.map(r => r.code), F.party, [A.badge])), geom: F.geom };
    return { svg: size === "story" ? storyCardSVG(A, assets, F.party) : linkCardSVG(A, assets, F.party), size, alt: cardAlt(A) };
  },
});

export function setShareable(info) {
  now = info;
  E.open.disabled = !info.geometry || !info.shareable;
  E.why.textContent = info.shareable ? "" : "Only a council seated under " + info.lawName +
    " can be shared. The other laws are here for comparison.";
  if (!info.shareable) sheet.close();
  sheet.setName(nameNow());
  sheet.update();
}
