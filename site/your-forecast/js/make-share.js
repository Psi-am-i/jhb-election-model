// "Your forecast", section 2 ("Break the model"): the share sheet. Anonymous:
// what is shared is a link that carries the whole forecast (make-state.js,
// with section 1's settings, through yf-url.js), and an image drawn in the
// browser from the seats the page is showing (share-card.js, the card module
// the site's Worker also draws link previews with). The design is
// audits/2026-10-03-share-design.
//
// ⛔ A LIVE WRITER (stats.LIVE_WRITERS["your-forecast/js/make-share.js"]), for
// the one region "b-share": the button and the <dialog> it opens are in
// your-forecast.html, inside that region, and every element is reached
// through a literal '[data-live="b-share"] …' selector, taken once, below. It
// writes with textContent and properties, never markup.
//
// What leaves the browser, and only when the sheet is open:
//  * the SEAL: the link's state and name go to the site's Worker (POST
//    /seal/1, src/seal.js), which signs them with its own clock and returns
//    the signature the link then carries as `s`. Any edit or new name asks
//    for a new one; from the moment polls open the Worker refuses. Off the
//    site (a local build) there is no Worker and the link goes unsealed.
//    The Worker stores every seal as one entry for the results-night ranking
//    (src/share-edge.js storeEntry), so a name is sealed once typing has
//    paused NAME_PAUSE_MS, or at once when the field is left, not after
//    every letter;
//  * the LINK goes out as /s/?…&ch=<button>, which the Worker counts by
//    button and forwards to the arrival view (src/share-edge.js).
//
// Practice it follows (as section 1's play-share.js):
//  * the image is drawn before the share button is enabled, so the native
//    share call happens inside the tap (Safari drops the gesture across an
//    await); files are attached only when navigator.canShare({files}) allows;
//  * Copy link is always there, with a select-and-copy fallback;
//  * native <dialog> + showModal(): the page behind is inert, Escape closes,
//    focus returns to the button that opened it.

import { forecastSpec, linkCardSVG, storyCardSVG, duelCardSVG, cardAlt, duelAlt, brandOf, localStamp, SIZES } from "./share-card.js";
import { FACES } from "./card-fonts.js";
import { svgToPNG } from "./card-text.js";
import { cardName, nameBlocked, NAME_MAX } from "./play-state.js";

const S = {
  open: document.querySelector('[data-live="b-share"] .shareopen'),
  dlg: document.querySelector('[data-live="b-share"] dialog'),
  close: document.querySelector('[data-live="b-share"] .x'),
  name: document.querySelector('[data-live="b-share"] .shname'),
  namenote: document.querySelector('[data-live="b-share"] .shnamenote'),
  url: document.querySelector('[data-live="b-share"] .shurl'),
  seal: document.querySelector('[data-live="b-share"] .shseal'),
  copy: document.querySelector('[data-live="b-share"] .shcopy'),
  wa: document.querySelector('[data-live="b-share"] .shwa'),
  x: document.querySelector('[data-live="b-share"] .shx'),
  native: document.querySelector('[data-live="b-share"] .shnative'),
  kind: document.querySelector('[data-live="b-share"] .shimg'),
  duelOpt: document.querySelector('[data-live="b-share"] .shimg .shduel'),
  friend: document.querySelector('[data-live="b-share"] .shfriend'),
  off: document.querySelector('[data-live="b-share"] .shoff'),
  img: document.querySelector('[data-live="b-share"] .preview img'),
  dl: document.querySelector('[data-live="b-share"] .shdl'),
  toast: document.querySelector('[data-live="b-share"] .toast'),
};
S.name.maxLength = NAME_MAX;

// Beside the page's own directory: /logos/, /fonts/, /logo.svg, /seal/1.
const ROOT = new URL("../../", import.meta.url);

let now = null, png = null, shown = null, opener = null, drawing = 0, sealing = 0;
let nameCb = () => {}, openCb = () => {}, friendNameCb = () => {};
let sealed = null;          // { key, s, at } for the state now in the sheet, or null
// The buttons that send the link wait for the seal: until the Worker has
// sealed the state in the sheet, or refused, or cannot be reached, they are
// off, so no button sends the unsealed link while a seal is on its way
// (review of the share build, 2026-10-03). Native sharing also waits for the
// image.
let sealSettled = false, imageSettled = false;

export function onNameChange(cb) { nameCb = cb; }
// cb(): the sheet opened, so the page should work out the reader's outcome
export function onOpen(cb) { openCb = cb; }
// cb(leaveOff): the reader chose whether the return link names the friend
export function onFriendName(cb) { friendNameCb = cb; }

// What the page is showing now:
//   { link, fields: { v, c, f, n }, name, answer, outcome (null until worked
//     out), vote, calls, party(code) -> { name, colour, article, logo },
//     baseline, election, geom, friend: null | { name, answer, outcome, vote,
//     calls, leftOff } }
export function setShareable(info) {
  now = info;
  png = null;
  S.open.disabled = false;
  if (S.dlg.open) fill();
}

const say = s => { S.toast.textContent = s; };
const keyOf = f => [f.v, f.c, f.f, f.n].join("\n");

// The link a button sends: /s/ with the state, the seal if it is current,
// and the button.
function shareURL(ch) {
  const u = new URL(now.link);
  const q = u.searchParams;
  if (sealed && sealed.key === keyOf(now.fields)) q.set("s", sealed.s);
  q.set("ch", ch);
  return new URL("s/?" + q.toString().replace(/%2C/g, ","), ROOT).href;
}

function fill() {
  if (document.activeElement !== S.name) S.name.value = now.name || "";
  S.native.hidden = typeof navigator.share !== "function";
  const hasFriend = !!(now.friend && now.friend.answer);
  S.duelOpt.hidden = !hasFriend;
  S.duelOpt.disabled = !hasFriend;   // Safari has ignored `hidden` on an option
  S.friend.hidden = !now.friend;
  S.off.checked = !!(now.friend && now.friend.leftOff);
  if (!hasFriend && S.kind.value === "duel") S.kind.value = "link";
  seal();
  draw();
}

// The link's box and the buttons that send it, on or off with the seal.
function buttons() {
  const on = sealSettled;
  S.url.value = on ? shareURL("copy") : "";
  S.copy.disabled = !on;
  for (const [a, href] of [[S.wa, () => "https://wa.me/?text=" + encodeURIComponent(shareURL("wa"))],
                           [S.x, () => "https://x.com/intent/post?url=" + encodeURIComponent(shareURL("x"))]]) {
    if (on) a.href = href(); else a.removeAttribute("href");
    a.setAttribute("aria-disabled", String(!on));
  }
  S.native.disabled = !(on && imageSettled);
}

// Ask the Worker to seal the state in the sheet, once typing has paused; the
// newest request wins. A change of name waits longer than any other change:
// each seal is an entry, and "Th" and "Than" are not the reader's name.
const SEAL_PAUSE_MS = 500, NAME_PAUSE_MS = 1500;
let sealTimer = null, typingName = false;
function seal() {
  const key = keyOf(now.fields);
  clearTimeout(sealTimer);
  if (sealed && sealed.key === key) {
    S.seal.textContent = "Sealed " + localStamp(sealed.at, now.election) + ".";
    sealSettled = true;
    buttons();
    return;
  }
  const ticket = ++sealing;
  S.seal.textContent = "Sealing the link.";
  sealSettled = false;
  buttons();
  sealTimer = setTimeout(() => { sealTimer = null; askSeal(ticket); }, typingName ? NAME_PAUSE_MS : SEAL_PAUSE_MS);
  typingName = false;
}
// The name field left (or Enter): seal what it holds now.
function sealNow() {
  if (!sealTimer) return;
  clearTimeout(sealTimer);
  sealTimer = null;
  askSeal(sealing);
}
async function askSeal(ticket) {
  const fields = now.fields, key = keyOf(fields);
  let r, body = null;
  try {
    r = await fetch(new URL("seal/1", ROOT), { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(fields) });
    body = await r.json();
  } catch (e) {
    r = null;
  }
  if (ticket !== sealing) return;
  if (r && r.ok && body && typeof body.s === "string") {
    const at = parseInt(body.s.split(".")[0], 36) * 1000;
    sealed = { key, s: body.s, at };
    S.seal.textContent = "Sealed " + localStamp(at, now.election) + ".";
    sealSettled = true;
    buttons();
    draw();
  } else {
    S.seal.textContent = r && (r.status === 403 || r.status === 429) && body && body.error ? body.error
      : "Not sealed: the link works, but it cannot show when it was made.";
    sealSettled = true;
    buttons();
  }
}

// ---------- the image ----------

let assetsReady = null;
function dataURL(blob) {
  return new Promise((ok, no) => { const fr = new FileReader(); fr.onload = () => ok(fr.result); fr.onerror = no; fr.readAsDataURL(blob); });
}
async function asset(path) {
  const r = await fetch(new URL(path, ROOT));
  if (!r.ok) throw new Error(path + ": " + r.status);
  return r;
}
// The site's IBM Plex faces as data: URIs: an SVG drawn as an image cannot
// fetch web fonts, so the card carries the faces it is measured in.
function loadAssets(codes) {
  assetsReady ??= (async () => {
    const faces = await Promise.all(Object.values(FACES).map(async f => {
      const file = { "400": "Regular", "600": "SemiBold", "700": "Bold" }[String(f.weight)];
      const stem = f.family.replace(/ /g, "") + "-" + file + "-Latin1.woff2";
      try {
        const src = await dataURL(await (await asset("fonts/" + stem)).blob());
        return "@font-face{font-family:\"" + f.family + "\";font-weight:" + f.weight + ";src:url(" + src + ") format(\"woff2\")}";
      } catch (e) { return ""; }
    }));
    let brand = null;
    try { brand = brandOf(await (await asset("logo.svg")).text()); } catch (e) { brand = null; }
    return { fontCSS: faces.join(""), brand, logos: {} };
  })();
  return assetsReady.then(async a => {
    await Promise.all(codes.filter(c => !(c in a.logos) && now.party(c).logo).map(async c => {
      try { a.logos[c] = await dataURL(await (await asset("logos/" + c + ".png")).blob()); } catch (e) { a.logos[c] = null; }
    }));
    return a;
  });
}

function specOf(F, name) {
  return forecastSpec({ name, answer: F.answer, outcome: F.outcome, vote: F.vote, calls: F.calls, party: now.party,
    baseline: now.baseline, election: now.election,
    made: sealed && sealed.key === keyOf(now.fields) ? { at: sealed.at, sealed: true } : { at: Date.now(), sealed: false } });
}

async function draw() {
  const ticket = ++drawing, info = now;
  imageSettled = false;
  buttons();
  S.dl.disabled = true;
  if (!info.outcome) { S.img.alt = ""; say("Working out the chance we give your outcome."); openCb(); return; }
  const kind = S.kind.value;
  const A = specOf(info, info.name);
  const friend = info.friend;
  const B = kind === "duel" && friend && friend.outcome ? specOf(friend, friend.leftOff ? "a friend" : friend.name || "a friend") : null;
  if (kind === "duel" && !B) { say("Working out the chance we give your friend's outcome."); return; }
  const codes = [...new Set([...A.rows, ...(B ? B.rows : [])].map(r => r.code))];
  let made;
  try {
    const assets = { ...(await loadAssets(codes)), geom: info.geom };
    if (ticket !== drawing) return;
    const svg = kind === "story" ? storyCardSVG(A, assets, info.party)
      : B ? duelCardSVG({ ...A, name: A.name || "A reader" }, B, assets, info.party) : linkCardSVG(A, assets, info.party);
    S.img.alt = B ? duelAlt(A, B) : cardAlt(A);
    made = await svgToPNG(svg, SIZES[B ? "duel" : kind]);
  } catch (e) {
    if (ticket === drawing) { say("The image could not be drawn in this browser. The link still works."); imageSettled = true; buttons(); }
    return;
  }
  if (ticket !== drawing) return;           // a newer draw replaced this one
  say("");
  png = made;
  if (shown) URL.revokeObjectURL(shown);
  shown = URL.createObjectURL(png);
  S.img.src = shown;
  imageSettled = true;
  buttons();
  S.dl.disabled = false;
}

const fileName = () => "joburg-forecast-" + (S.kind.value || "link") + ".png";

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
S.kind.addEventListener("change", () => { png = null; draw(); });
S.off.addEventListener("change", () => friendNameCb(S.off.checked));
S.name.addEventListener("input", () => {
  S.namenote.textContent = nameBlocked(S.name.value)
    ? "This name cannot go on the image or in the link: it could pass for the site, the model or the IEC." : "";
  typingName = true;
  nameCb(cardName(S.name.value));     // the page rewrites the address and calls setShareable
});
S.name.addEventListener("change", sealNow);
S.copy.addEventListener("click", async () => {
  let ok = false;
  try { await navigator.clipboard.writeText(S.url.value); ok = true; }
  catch (e) {
    S.url.select();
    try { ok = document.execCommand?.("copy") === true; } catch (e2) { ok = false; }
  }
  say(ok ? "Link copied." : "Copying did not work here. The link is selected: copy it from the box.");
});
S.native.addEventListener("click", () => {
  const data = { title: "My Johannesburg election forecast", text: "My forecast for the Johannesburg council.", url: shareURL("native") };
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
