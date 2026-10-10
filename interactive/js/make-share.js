// "Your forecast", section 2 ("Break the model"): its share sheet, the one
// sheet both sections use (share-sheet.js), with section 2's content: a link
// that carries the whole forecast (make-state.js, with section 1's settings,
// through yf-url.js), sealed, and an image drawn in the browser from the
// seats the page is showing (share-card.js, the card module the site's Worker
// also draws link previews with). The design is
// audits/2026-10-03-share-design.
//
// ⛔ A LIVE WRITER (stats.LIVE_WRITERS["your-forecast/js/make-share.js"]), for
// the one region "b-share": the button and the <dialog> it opens are in
// your-forecast.html, inside that region, and every element is reached
// through a literal '[data-live="b-share"] …' selector, taken once, below,
// and handed to share-sheet.js. It writes with textContent and properties,
// never markup.

import { forecastSpec, linkCardSVG, storyCardSVG, duelCardSVG, cardAlt, duelAlt, cardTitle } from "./share-card.js";
import { shareSheet, loadAssets } from "./share-sheet.js";

const E = {
  open: document.querySelector('[data-live="b-share"] .shareopen'),
  dlg: document.querySelector('[data-live="b-share"] dialog'),
  close: document.querySelector('[data-live="b-share"] .x'),
  name: document.querySelector('[data-live="b-share"] .shname'),
  namenote: document.querySelector('[data-live="b-share"] .shnamenote'),
  url: document.querySelector('[data-live="b-share"] .shurl'),
  copy: document.querySelector('[data-live="b-share"] .shcopy'),
  seal: document.querySelector('[data-live="b-share"] .shseal'),
  entry: document.querySelector('[data-live="b-share"] .shentry'),
  kind: document.querySelector('[data-live="b-share"] .shimg'),
  duelOpt: document.querySelector('[data-live="b-share"] .shimg .shduel'),
  friend: document.querySelector('[data-live="b-share"] .shfriend'),
  off: document.querySelector('[data-live="b-share"] .shoff'),
  img: document.querySelector('[data-live="b-share"] .preview img'),
  wa: document.querySelector('[data-live="b-share"] .shwa'),
  x: document.querySelector('[data-live="b-share"] .shx'),
  native: document.querySelector('[data-live="b-share"] .shnative'),
  dl: document.querySelector('[data-live="b-share"] .shdl'),
  toast: document.querySelector('[data-live="b-share"] .toast'),
};

let now = null;
let nameCb = () => {}, openCb = () => {}, friendNameCb = () => {};
export function onNameChange(cb) { nameCb = cb; }
// cb(): the sheet opened, so the page should work out the reader's outcome
export function onOpen(cb) { openCb = cb; }
// cb(leaveOff): the reader chose whether the return link names the friend
export function onFriendName(cb) { friendNameCb = cb; }

const specOf = (F, name, made) => forecastSpec({ name, answer: F.answer, outcome: F.outcome, vote: F.vote, calls: F.calls,
  party: now.party, baseline: now.baseline, election: now.election, made });

const sheet = shareSheet(E, {
  canOpen: () => !!now,
  prepare: async () => {},
  fields: () => now.fields,
  link: () => now.link,
  election: () => now.election,
  emptyName: () => cardTitle(""),
  entered: () => true,
  onName: n => nameCb(n),                 // the page rewrites the address and calls setShareable
  shareWords: () => ({ title: "My Johannesburg election forecast", text: "My forecast for the Johannesburg council." }),
  fileBase: () => "joburg-forecast",
  async card(kind, made) {
    const info = now;
    if (!info.outcome) { openCb(); return { wait: "Working out the chance we give your outcome." }; }
    const friend = info.friend;
    const A = specOf(info, info.name, made);
    const B = kind === "duel" && friend && friend.outcome ? specOf(friend, friend.leftOff ? "a friend" : friend.name || "a friend", made) : null;
    if (kind === "duel" && !B) return { wait: "Working out the chance we give your friend's outcome." };
    const codes = [...new Set([...A.rows, ...(B ? B.rows : [])].map(r => r.code))];
    const assets = { ...(await loadAssets(codes, info.party, [A.badge, B && B.badge])), geom: info.geom };
    if (B) return { svg: duelCardSVG({ ...A, name: A.name || "A reader" }, B, assets, info.party), size: "duel", alt: duelAlt(A, B) };
    return { svg: kind === "story" ? storyCardSVG(A, assets, info.party) : linkCardSVG(A, assets, info.party), size: kind, alt: cardAlt(A) };
  },
});

// What the page is showing now:
//   { link, fields: { v, c, f, n }, name, answer, outcome (null until worked
//     out), vote, calls, party(code) -> { name, colour, article, logo },
//     baseline, election, geom, friend: null | { name, answer, outcome, vote,
//     calls, leftOff } }
export function setShareable(info) {
  now = info;
  E.open.disabled = false;
  sheet.setName(info.name || "");
  const hasFriend = !!(info.friend && info.friend.answer);
  E.duelOpt.hidden = !hasFriend;
  E.duelOpt.disabled = !hasFriend;   // Safari has ignored `hidden` on an option
  E.friend.hidden = !info.friend;
  E.off.checked = !!(info.friend && info.friend.leftOff);
  if (!hasFriend && E.kind.value === "duel") E.kind.value = "link";
  sheet.update();
}

E.off.addEventListener("change", () => friendNameCb(E.off.checked));
