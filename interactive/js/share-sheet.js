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
// link, the image (a select: the link preview, the story card, and the
// side-by-side card where a friend's forecast is kept), the preview, and
// Share…, WhatsApp, X and Download image.
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
//  * Copy link is always there, with a select-and-copy fallback.
//  * Native <dialog> + showModal(): the page behind is inert, Escape closes,
//    and focus returns to the button that opened it.

import { svgToPNG } from "./card-text.js";
import { brandOf, localStamp, SIZES } from "./share-card.js";
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
// site's logo (site/logo.svg), and the logo of each party in `codes` that has
// one (`party(code).logo`). Loaded once; logos added as parties appear.
export function loadAssets(codes, party) {
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
    await Promise.all(codes.filter(c => c && !(c in a.logos) && party(c).logo).map(async c => {
      try { a.logos[c] = await dataURL(await (await asset("logos/" + c + ".png")).blob()); } catch (e) { a.logos[c] = null; }
    }));
    return a;
  });
}

// ---------- the sheet ----------

// The words under the name field, the same in both sections. `label`: what
// the image says when the name is left empty.
export function nameNote(value, label) {
  if (nameBlocked(value)) return "This name cannot go on the image or in the link: it could pass for the site, the model or the IEC." +
    (label ? " The image says " + label + "." : "");
  return "Left empty, the image says " + label + ". The name goes on the image and in the link, and nowhere else.";
}

const SEAL_PAUSE_MS = 500, NAME_PAUSE_MS = 1500, NAME_TYPING_MS = 250;
const keyOf = f => [f.v, f.c, f.f, f.n].join("\n");

// E: the sheet's elements, from the section's own region: { open, dlg, close,
//   name, namenote, url, copy, seal, entry, kind, duelOpt, img, wa, x,
//   native, dl, toast }.
// H: what the section shares, as functions of what its page shows now:
//   canOpen()          may the sheet open
//   prepare()          async, before it opens (a label to load)
//   fields()           { v, c, f, n } to seal, null for nothing to seal, or
//                      undefined while the forecast to seal is being worked out
//   link()             the link's address, the state in it, before any seal
//   election()         the election (the seal's local time)
//   card(kind, made)   async: { svg, size, alt }, or { wait: words } while a
//                      figure it needs is being worked out; `made` is
//                      { at, sealed } or null
//   emptyName()        what the image says when the name is left empty
//   onName(name)       the name changed (the page rewrites its address and
//                      calls update())
//   shareWords()       { title, text } for the native share
//   fileBase()         the downloaded file's name, before "-<kind>.png"
// Returns { update(): the page's figures changed, redraw if open; isOpen() }.
export function shareSheet(E, H) {
  E.name.maxLength = NAME_MAX;
  let png = null, shown = null, opener = null, drawing = 0, sealing = 0;
  let sealed = null;            // { key, s, at } for the state now in the sheet, or null
  let sealSettled = false, imageSettled = false;
  let sealTimer = null, typingName = false, typing = null;

  const say = s => { E.toast.textContent = s; };
  const kind = () => E.kind.value || "link";
  const current = () => { const f = H.fields(); return f && sealed && sealed.key === keyOf(f) ? sealed : null; };

  // The link a button sends. A forecast to seal goes out through /s/ with its
  // seal, if current, and the button; the model's own forecast, as the page's
  // address.
  function shareURL(ch) {
    const f = H.fields();
    if (!f) return H.link();
    const q = new URL(H.link()).searchParams;
    const s = current();
    if (s) q.set("s", s.s);
    q.set("ch", ch);
    return new URL("s/?" + q.toString().replace(/%2C/g, ","), ROOT).href;
  }

  // The link's box and the buttons that send it, on or off with the seal.
  function buttons() {
    const on = sealSettled;
    E.url.value = on ? shareURL("copy") : "";
    E.copy.disabled = !on;
    for (const [a, href] of [[E.wa, () => "https://wa.me/?text=" + encodeURIComponent(shareURL("wa"))],
                             [E.x, () => "https://x.com/intent/post?url=" + encodeURIComponent(shareURL("x"))]]) {
      if (on) a.href = href(); else a.removeAttribute("href");
      a.setAttribute("aria-disabled", String(!on));
    }
    E.native.disabled = !(on && imageSettled);
  }

  // Ask the Worker to seal the forecast in the sheet, once typing has paused;
  // the newest request wins. A change of name waits longer than any other
  // change: each seal is an entry, and "Th" and "Than" are not the name.
  function seal() {
    const f = H.fields();
    clearTimeout(sealTimer);
    sealTimer = null;
    E.seal.hidden = E.entry.hidden = f === null;
    if (f === null) { E.seal.textContent = ""; sealSettled = true; buttons(); return; }
    if (f === undefined) { E.seal.textContent = "Working out the forecast to seal."; sealSettled = false; buttons(); return; }
    if (sealed && sealed.key === keyOf(f)) {
      E.seal.textContent = "Sealed " + localStamp(sealed.at, H.election()) + ".";
      sealSettled = true;
      buttons();
      return;
    }
    const ticket = ++sealing;
    E.seal.textContent = "Sealing the link.";
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
    const fields = H.fields();
    if (!fields) return;
    const key = keyOf(fields);
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
      E.seal.textContent = "Sealed " + localStamp(at, H.election()) + ".";
      sealSettled = true;
      buttons();
      draw();
    } else {
      E.seal.textContent = r && (r.status === 403 || r.status === 429) && body && body.error ? body.error
        : "Not sealed: the link works, but it cannot show when it was made.";
      sealSettled = true;
      buttons();
    }
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
      if (c.wait) { E.img.alt = ""; say(c.wait); return; }
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
    E.namenote.textContent = nameNote(E.name.value, H.emptyName());
    E.native.hidden = typeof navigator.share !== "function";
    seal();
    draw();
  }

  const fileName = () => H.fileBase() + "-" + kind() + ".png";

  E.open.addEventListener("click", async () => {
    if (!H.canOpen()) return;
    opener = E.open;
    say("");
    await H.prepare?.();
    E.dlg.showModal();
    fill();
    E.name.focus();
  });
  E.close.addEventListener("click", () => E.dlg.close());
  E.dlg.addEventListener("click", e => { if (e.target === E.dlg) E.dlg.close(); });
  E.dlg.addEventListener("close", () => opener?.focus?.());
  E.kind.addEventListener("change", () => { png = null; draw(); });
  E.name.addEventListener("input", () => {
    E.namenote.textContent = nameNote(E.name.value, H.emptyName());
    typingName = true;
    clearTimeout(typing);
    typing = setTimeout(() => H.onName(cardName(E.name.value)), NAME_TYPING_MS);
  });
  E.name.addEventListener("change", () => { clearTimeout(typing); H.onName(cardName(E.name.value)); sealNow(); });
  E.copy.addEventListener("click", async () => {
    let ok = false;
    try { await navigator.clipboard.writeText(E.url.value); ok = true; }
    catch (e) {
      E.url.select();
      try { ok = document.execCommand?.("copy") === true; } catch (e2) { ok = false; }
    }
    say(ok ? "Link copied." : "Copying did not work here. The link is selected: copy it from the box.");
  });
  E.native.addEventListener("click", () => {
    const data = { ...H.shareWords(), url: shareURL("native") };
    if (png) {
      const f = new File([png], fileName(), { type: "image/png" });
      if (navigator.canShare?.({ files: [f] })) data.files = [f];
    }
    navigator.share(data).then(() => say("Shared."))
      .catch(err => { if (err.name !== "AbortError") say("Sharing did not work here. Copy the link instead."); });
  });
  E.dl.addEventListener("click", () => {
    if (!png) return;
    const a = document.createElement("a");
    a.href = URL.createObjectURL(png);
    a.download = fileName();
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 10000);   // after the download has started
    say("Image downloaded.");
  });

  return {
    update() { png = null; if (E.dlg.open) fill(); },
    isOpen: () => E.dlg.open,
    setName(n) { if (document.activeElement !== E.name && cardName(E.name.value) !== cardName(n)) E.name.value = cardName(n); },
    close() { if (E.dlg.open) E.dlg.close(); },
  };
}
