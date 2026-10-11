// "Your forecast": the ONE share sheet both sections use (owner, 2026-10-06:
// one sheet, one set of options, the wording the same in both). Section 1's
// play-share.js and section 2's make-share.js each hand it the elements of
// their own copy of the sheet (the same markup in your-forecast.html, once in
// each section's region) and what differs between them, which is content
// only: the card, the link, whether there is a forecast to seal, and the
// words a share carries.
//
// ⛔ A LIVE WRITER (stats.LIVE_WRITERS["your-forecast/js/share-sheet.js"]) for
// the regions "share" and "b-share", that LOOKS UP NOTHING: it holds no
// selector at all, and writes only to the elements each section took from its
// own region by its literal '[data-live="…"] …' selectors. It writes with
// textContent and properties, never markup.
//
// The controls, in both sections: the name on the image, the link and Copy
// link, the image (a select: the link preview and the story card), the
// preview, and Share…, WhatsApp, X and Download image.
//
// THE SEAL. When a section hands it a forecast to seal (`fields`: v, c, f and
// the name; section 2's forecast, or section 1's hand-off once a setting is
// moved), the link's state and name go to the site's Worker (POST /seal/1,
// src/seal.js), which signs them with its own clock and returns the signature
// the link then carries as `s`. Any edit or new name asks for a new one; from
// the moment polls open the Worker refuses. Off the site (a local build)
// there is no Worker and the link goes unsealed. The Worker stores every seal
// as one entry for the results-night ranking (src/share-edge.js storeEntry),
// so a name is sealed once typing has paused NAME_PAUSE_MS, or at once when
// the field is left, not after every letter. The model's own forecast
// (section 1 untouched) is not a reader's forecast: nothing is sealed, the
// seal's line and the ranking's words are hidden, and its link is the page's.
// A sealed forecast's link goes out as /s/?…&ch=<button>, which the Worker
// counts by button and forwards to the arrival view (src/share-edge.js).
//
// Practice it follows:
//  * The image is drawn before the share button is enabled, so the native
//    share call happens inside the tap: Safari drops the user gesture across
//    an await. Files are attached only when navigator.canShare({files})
//    allows; otherwise the link is shared and the receiving app shows the
//    page's own preview.
//  * The buttons that send the link wait for the seal: until the Worker has
//    sealed the state in the sheet, or refused, or cannot be reached, they
//    are off, so no button sends the unsealed link while a seal is on its way
//    (review of the share build, 2026-10-03).
//  * The dialog, Copy link (with its select-and-copy fallback), WhatsApp, X,
//    Share…, Download image and the line under them are the site's ONE share
//    sheet (src/js/share-dialog.js), the same controls every site page's
//    share button opens; this module adds what only "Your forecast" has: the
//    name, the seal, the image picker and the drawn card.

import { shareDialog } from "../../js/share-dialog.js";
import { svgToPNG } from "./card-text.js";
import { brandOf, stampOf, badgeFile, STAMP_DIR, localStamp, SIZES } from "./share-card.js";
import { FACES } from "./card-fonts.js";
import { cardName, nameBlocked, NAME_MAX } from "./play-state.js";

// Beside the page's own directory: /logos/, /fonts/, /logo.svg, /seal/1, /s/.
const ROOT = new URL("../../", import.meta.url);

// ---------- what every card draws with ----------

let assetsReady = null;
function dataURL(blob) {
  return new Promise((ok, no) => { const fr = new FileReader(); fr.onload = () => ok(fr.result); fr.onerror = no; fr.readAsDataURL(blob); });
}
async function asset(path) {
  const r = await fetch(new URL(path, ROOT));
  if (!r.ok) throw new Error(path + ": " + r.status);
  return r;
}
// The site's IBM Plex faces as data: URIs (an SVG drawn as an image cannot
// fetch web fonts, so the card carries the faces it is measured in), the
// site's logo (site/logo.svg), the logo of each party in `codes` that has
// one (`party(code).logo`), and the owner's badge for each of `badges` (the
// badge words, share-card.js badgeFile). Loaded once; logos and badges added
// as they are asked for. A badge that cannot be fetched is drawn as its words.
export function loadAssets(codes, party, badges = []) {
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
    return { fontCSS: faces.join(""), brand, logos: {}, badges: {} };
  })();
  return assetsReady.then(async a => {
    await Promise.all(codes.filter(c => c && !(c in a.logos) && party(c).logo).map(async c => {
      try { a.logos[c] = await dataURL(await (await asset("logos/" + c + ".png")).blob()); } catch (e) { a.logos[c] = null; }
    }));
    await Promise.all(badges.filter(w => w && !(w in a.badges)).map(async w => {
      try { a.badges[w] = stampOf(await (await asset(STAMP_DIR + "/" + badgeFile(w))).text()); } catch (e) { a.badges[w] = null; }
    }));
    return a;
  });
}

// ---------- the sheet ----------

// The words under the name field, the same in both sections, true of the
// sheet they sit in. `label`: what the image says when the name is left
// empty; `entered`: whether the sheet seals and enters the forecast, so the
// name is also stored with the entry (docs-public/privacy.md, "Forecasts
// entered").
export function nameNote(value, label, entered) {
  if (nameBlocked(value)) return "This name cannot go on the image or in the link: it could pass for the site, the model or the IEC." +
    (label ? " The image says " + label + "." : "");
  return "Left empty, the image says " + label + "." + (entered
    ? " The name goes on the image, in the link and with the entry this sheet seals."
    : " The name goes on the image, and nowhere else.");
}

const SEAL_PAUSE_MS = 500, NAME_PAUSE_MS = 1500;
const keyOf = f => [f.v, f.c, f.f, f.n].join("\n");
// Every seal the Worker has given this page, by the state and name it signed,
// shared by both sections' sheets: the same forecast under the same name is
// one entry, whichever sheet asks (review of the one-sheet diff, 2026-10-06).
const SEALS = new Map();
// Seals asked for and not yet answered, by key: a second sheet asking for the
// same key waits on the first request instead of entering it again.
const ASKED = new Map();
function requestSeal(fields) {
  const key = keyOf(fields);
  if (SEALS.has(key)) return Promise.resolve({ seal: SEALS.get(key) });
  if (ASKED.has(key)) return ASKED.get(key);
  const p = (async () => {
    let r, body = null;
    try {
      r = await fetch(new URL("seal/1", ROOT), { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(fields) });
      body = await r.json();
    } catch (e) {
      r = null;
    }
    if (r && r.ok && body && typeof body.s === "string") {
      const seal = { s: body.s, at: parseInt(body.s.split(".")[0], 36) * 1000 };
      SEALS.set(key, seal);
      return { seal };
    }
    return { refused: r && (r.status === 403 || r.status === 429) && body && body.error ? body.error
      : "Not sealed: the link works, but it cannot show when it was made." };
  })();
  ASKED.set(key, p);
  p.finally(() => ASKED.delete(key));
  return p;
}

// E: the sheet's elements, from the section's own region: { open, dlg, close,
//   name, namenote, url, copy, seal, entry, kind, img, wa, x,
//   native, dl, toast }.
// H: what the section shares, as functions of what its page shows now:
//   canOpen()          may the sheet open
//   prepare()          async, before it opens
//   fields()           { v, c, f, n } to seal; null for nothing to seal (the
//                      model's forecast); undefined while the forecast to
//                      seal is being worked out; { failed: reason } when it
//                      cannot be
//   link()             the link's address, the state in it, before any seal
//   election()         the election (the seal's local time)
//   card(kind, made)   async: { svg, size, alt }, or { wait: words } while a
//                      figure it needs is being worked out or cannot be;
//                      `made` is { at, sealed } or null
//   emptyName()        what the image says when the name is left empty
//   entered()          does this sheet seal and enter what it shares
//   onName(name)       the name changed (the page rewrites its address and
//                      calls update())
//   shareWords()       { title, text } for the native share
//   fileBase()         the downloaded file's name, before "-<kind>.png"
// Returns { update(): the page's figures changed, redraw if open; isOpen(),
// setName(name), close() }.
export function shareSheet(E, H) {
  E.name.maxLength = NAME_MAX;
  let png = null, shown = null, drawing = 0, sealing = 0;
  // the key the link's buttons are on for: the state whose seal settled
  // (sealed, refused, or nothing to seal), or null while one is on its way
  let settled = null, imageSettled = false;
  let sealTimer = null, typingName = false;

  const kind = () => E.kind.value || "link";
  // what the buttons send now: "none" (nothing to seal), "failed", the
  // state's key, or null while it is being worked out
  const keyNow = () => {
    const f = H.fields();
    return f === null ? "none" : f === undefined ? null : f.failed ? "failed" : keyOf(f);
  };
  const current = () => { const k = keyNow(); return k && SEALS.get(k) || null; };

  // The link a button sends. A forecast to seal goes out through /s/ with its
  // seal, if current, and the button; the model's own forecast, and a
  // forecast that could not be worked out, as the page's address.
  function shareURL(ch) {
    const f = H.fields();
    if (!f || f.failed) return H.link();
    const q = new URL(H.link()).searchParams;
    const s = current();
    if (s) q.set("s", s.s);
    q.set("ch", ch);
    return new URL("s/?" + q.toString().replace(/%2C/g, ","), ROOT).href;
  }

  const fileName = () => H.fileBase() + "-" + kind() + ".png";

  // The controls every share sheet has (src/js/share-dialog.js). The link's
  // box and the buttons that send it are on only when the state they would
  // send is the one whose seal settled; Share… also waits for the image.
  const D = shareDialog(E, {
    canOpen: () => H.canOpen(),
    prepare: () => H.prepare?.(),
    opened: () => fill(),
    link: shareURL,
    on: () => { const k = keyNow(); return k !== null && settled === k; },
    nativeOn: () => imageSettled,
    shareWords: () => H.shareWords(),
    file: () => png ? new File([png], fileName(), { type: "image/png" }) : null,
    download() {
      if (!png) return null;
      const href = URL.createObjectURL(png);
      return { href, name: fileName(), done: () => URL.revokeObjectURL(href) };
    },
  });
  const say = D.say, buttons = D.buttons;

  // Seal the state in the sheet, once typing has paused. EVERY call starts
  // a new ticket and takes the buttons off, so an answer for an earlier
  // state can never show as this one's or turn its buttons on. A change of
  // name waits longer than any other change: each seal is an entry, and
  // "Th" and "Than" are not the name.
  function seal() {
    const ticket = ++sealing, f = H.fields(), k = keyNow();
    clearTimeout(sealTimer);
    sealTimer = null;
    settled = null;
    E.seal.hidden = f === null;
    E.entry.hidden = f === null || !!(f && f.failed);
    if (f === null) { E.seal.textContent = ""; settled = k; typingName = false; buttons(); return; }
    if (f === undefined) { E.seal.textContent = "Working out the forecast to seal."; buttons(); return; }
    if (f.failed) { E.seal.textContent = "Not sealed: " + f.failed + "."; settled = k; typingName = false; buttons(); return; }
    if (SEALS.has(k)) {
      E.seal.textContent = "Sealed " + localStamp(SEALS.get(k).at, H.election()) + ".";
      settled = k;
      typingName = false;
      buttons();
      return;
    }
    E.seal.textContent = "Sealing the link.";
    buttons();
    sealTimer = setTimeout(() => { sealTimer = null; askSeal(ticket, f); }, typingName ? NAME_PAUSE_MS : SEAL_PAUSE_MS);
    typingName = false;
  }
  // The name field left (or Enter): seal what it holds now.
  function sealNow() {
    if (!sealTimer) return;
    clearTimeout(sealTimer);
    sealTimer = null;
    const f = H.fields();
    if (f && !f.failed) askSeal(sealing, f);
  }
  async function askSeal(ticket, fields) {
    const key = keyOf(fields);
    const got = await requestSeal(fields);
    // only the newest request, for the state the sheet still holds, shows
    if (ticket !== sealing || keyNow() !== key) return;
    E.seal.textContent = got.seal ? "Sealed " + localStamp(got.seal.at, H.election()) + "." : got.refused;
    settled = key;
    buttons();
    if (got.seal) draw();
  }

  // The image, drawn before the buttons that send it are on.
  async function draw() {
    const ticket = ++drawing, want = kind();
    imageSettled = false;
    buttons();
    E.dl.disabled = true;
    let made;
    try {
      const f = H.fields(), s = current();
      const c = await H.card(want, f ? (s ? { at: s.at, sealed: true } : { at: Date.now(), sealed: false }) : null);
      if (ticket !== drawing) return;
      if (c.wait) {
        // no earlier card stays in view under words that say there is none
        E.img.alt = "";
        E.img.removeAttribute("src");
        if (shown) { URL.revokeObjectURL(shown); shown = null; }
        png = null;
        say(c.wait);
        return;
      }
      E.img.alt = c.alt;
      made = await svgToPNG(c.svg, SIZES[c.size]);
    } catch (e) {
      if (ticket === drawing) { say("The image could not be drawn in this browser. The link still works."); imageSettled = true; buttons(); }
      return;
    }
    if (ticket !== drawing) return;           // a newer draw replaced this one
    say("");
    png = made;
    if (shown) URL.revokeObjectURL(shown);
    shown = URL.createObjectURL(png);
    E.img.src = shown;
    imageSettled = true;
    buttons();
    E.dl.disabled = false;
  }

  function fill() {
    E.namenote.textContent = nameNote(E.name.value, H.emptyName(), H.entered());
    seal();
    draw();
  }

  E.kind.addEventListener("change", () => { png = null; draw(); });
  // every keystroke reaches the page at once; the seal waits for the pause
  E.name.addEventListener("input", () => {
    E.namenote.textContent = nameNote(E.name.value, H.emptyName(), H.entered());
    typingName = true;
    H.onName(cardName(E.name.value));
  });
  E.name.addEventListener("change", sealNow);
  return {
    update() { png = null; if (E.dlg.open) fill(); },
    isOpen: D.isOpen,
    setName(n) { if (document.activeElement !== E.name && cardName(E.name.value) !== cardName(n)) E.name.value = cardName(n); },
    close: D.close,
  };
}
