// "Play with the model": the share sheet. Anonymous: what is shared is the
// page's address with the reader's settings in it (play-state.js serialize),
// and an image drawn from the figures the page is showing (play-card.js).
// Nothing is sent anywhere, stored, or asked of the reader.
//
// ⛔ A LIVE WRITER (stats.LIVE_WRITERS["play/js/play-share.js"]), for the one
// region "share": the button and the <dialog> it opens are in model.html,
// inside that region, and every element is reached through a literal
// '[data-live="share"] …' selector, taken once, below. It writes with
// textContent and properties, never markup, and adds nothing outside the region.
//
// THE NAME (D6/D7, owner 2026-10-02). The reader may put a name on the image,
// untouched page or not: free text, at most play-state.NAME_MAX characters,
// cleaned by play-state.cleanName. It goes into the input's value, the link
// (`n=`) and the image, where play-card.js escapes it and draws it as text.
// It is never written into the page as markup or as page text. Left empty,
// the image carries a random label: a word and a number from
// interactive/js/labels.js, which the build serves as play/labels.json.
//
// Practice it follows (the builder's share.js, adapted to the writer rules):
//  * The native share sheet (navigator.share) is offered where it exists. The
//    image is drawn before the button is enabled, so the call happens inside
//    the tap: Safari drops the user gesture across an await.
//  * Files are attached only when navigator.canShare({files}) says yes;
//    otherwise the link is shared and the receiving app shows the page's own
//    preview (og:image), which is generic: no server draws a card per link.
//  * Copy link is always there, with a select-and-copy fallback.
//  * Native <dialog> + showModal(): the page behind is inert, Escape closes,
//    and focus returns to the button that opened it.

import { buildPlayCardSVG, playCardAlt, SIZES } from "./play-card.js";
import { svgToPNG } from "./card-text.js";
import { cleanName, NAME_MAX, serialize } from "./play-state.js";

const S = {
  open: document.querySelector('[data-live="share"] .pl-shareopen'),
  dlg: document.querySelector('[data-live="share"] dialog'),
  close: document.querySelector('[data-live="share"] .x'),
  name: document.querySelector('[data-live="share"] .pl-name'),
  namenote: document.querySelector('[data-live="share"] .pl-fldnote'),
  url: document.querySelector('[data-live="share"] .shurl'),
  copy: document.querySelector('[data-live="share"] .shcopy'),
  native: document.querySelector('[data-live="share"] .shnative'),
  sizes: document.querySelectorAll('[data-live="share"] .sizes button'),
  img: document.querySelector('[data-live="share"] .preview img'),
  dl: document.querySelector('[data-live="share"] .shdl'),
  toast: document.querySelector('[data-live="share"] .toast'),
};
S.name.maxLength = NAME_MAX;

// What the page is showing now: { url, r, st, ctx, party, made, when,
// geometry, touched, onName }.
let now = null;
let size = "link";
let cache = {};
let opener = null;
let shown = null;             // the preview's object URL, revoked when replaced
let label = "";               // the random label used when no name is given
let photoSrc = null;          // share.jpg as a data URL, fetched once

// share.jpg (the site's Hillbrow Tower image), as a data URL the card's SVG can
// carry into a canvas: an SVG drawn as an image may not load other files.
const photoP = fetch(new URL("../../share.jpg", import.meta.url))
  .then(r => (r.ok ? r.blob() : null))
  .then(b => b && new Promise(ok => { const f = new FileReader(); f.onload = () => ok(f.result); f.onerror = () => ok(null); f.readAsDataURL(b); }))
  .catch(() => null)
  .then(src => { photoSrc = src; return src; });

// A random label, "<word>-<number>", in labels.js's form.
const labelP = fetch(new URL("../labels.json", import.meta.url))
  .then(r => (r.ok ? r.json() : null)).catch(() => null)
  .then(L => {
    if (!L || !L.words || !L.words.length) return "reader";
    const u = new Uint32Array(2);
    crypto.getRandomValues(u);
    return L.words[u[0] % L.words.length] + "-" + (1 + (u[1] % L.max));
  })
  .then(l => { label = l; return l; });

export function setShareable(info) {
  now = info;
  cache = {};
  S.open.disabled = !info.geometry;
  if (S.name.value !== cleanName(info.st.name)) S.name.value = cleanName(info.st.name);
  if (S.dlg.open) fill();
}

const say = s => { S.toast.textContent = s; };
const nameNow = () => cleanName(S.name.value) || label;
const urlNow = () => new URL(location.pathname + serialize({ ...now.st, name: cleanName(S.name.value) }, now.ctx), location.href).href;

function fill() {
  S.url.value = urlNow();
  S.native.hidden = typeof navigator.share !== "function";
  S.namenote.textContent = "Left empty, the image says " + label + ". The name goes on the image and in the link, and nowhere else.";
  draw();
}

async function draw() {
  const want = size, info = now, who = nameNow();
  S.native.disabled = true;
  S.dl.disabled = true;
  for (const b of S.sizes) b.setAttribute("aria-pressed", String(b.dataset.size === want));
  const card = { ...info, name: who, photoSrc };
  S.img.alt = playCardAlt(card);
  try {
    if (!cache[want + who]) cache[want + who] = await svgToPNG(buildPlayCardSVG({ ...card, size: want }), SIZES[want]);
  } catch (e) {
    say("The image could not be drawn in this browser. The link still works.");
    S.native.disabled = false;
    return;
  }
  if (want !== size || info !== now || who !== nameNow()) return;
  if (shown) URL.revokeObjectURL(shown);
  shown = URL.createObjectURL(cache[want + who]);
  S.img.src = shown;
  S.native.disabled = false;
  S.dl.disabled = false;
}

const fileBase = () => "joburg-forecast-" + nameNow().replace(/[^A-Za-z0-9-]+/g, "-").replace(/^-+|-+$/g, "").toLowerCase().slice(0, 40);
const file = () => new File([cache[size + nameNow()]], fileBase() + "-" + size + ".png", { type: "image/png" });

S.open.addEventListener("click", async () => {
  if (!now) return;
  opener = S.open;
  say("");
  await Promise.all([photoP, labelP]);
  S.dlg.showModal();
  fill();
  S.name.focus();
});
let typing = null;
S.name.addEventListener("input", () => {
  clearTimeout(typing);
  typing = setTimeout(() => {
    now.onName?.(cleanName(S.name.value));
    S.url.value = urlNow();
    draw();
  }, 250);
});
S.close.addEventListener("click", () => S.dlg.close());
S.dlg.addEventListener("click", e => { if (e.target === S.dlg) S.dlg.close(); });
S.dlg.addEventListener("close", () => opener?.focus?.());
for (const b of S.sizes) b.addEventListener("click", () => { size = b.dataset.size; draw(); });
S.copy.addEventListener("click", async () => {
  const url = urlNow();
  let ok = false;
  try { await navigator.clipboard.writeText(url); ok = true; }
  catch (e) {
    S.url.value = url;
    S.url.select();
    try { ok = document.execCommand?.("copy") === true; } catch (e2) { ok = false; }
  }
  say(ok ? "Link copied." : "Copying did not work here. Copy the page's address instead.");
});
S.native.addEventListener("click", () => {
  const data = { title: "Play with the Johannesburg election model", text: "My Johannesburg election forecast.", url: urlNow() };
  if (cache[size + nameNow()]) {
    const f = file();
    if (navigator.canShare?.({ files: [f] })) data.files = [f];
  }
  navigator.share(data).then(() => say("Shared."))
    .catch(err => { if (err.name !== "AbortError") say("Sharing did not work here. Copy the link instead."); });
});
S.dl.addEventListener("click", () => {
  const blob = cache[size + nameNow()];
  if (!blob) return;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = fileBase() + "-" + size + ".png";
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 10000);   // after the download has started
  say("Image downloaded.");
});
