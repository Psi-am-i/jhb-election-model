// "Play with the model": the share sheet. Anonymous: what is shared is the
// page's address with the reader's settings in it (play-state.js serialize),
// and optionally an image drawn from the figures the page is showing
// (play-card.js). Nothing is sent anywhere, stored, or asked of the reader.
//
// ⛔ A LIVE WRITER (stats.LIVE_WRITERS["play/js/play-share.js"]), for the one
// region "share": the button and the <dialog> it opens are in model.html,
// inside that region, and every element is reached through a literal
// '[data-live="share"] …' selector, taken once, below. It writes with
// textContent and properties, never markup, and adds nothing outside the region.
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

const S = {
  open: document.querySelector('[data-live="share"] .shareopen'),
  dlg: document.querySelector('[data-live="share"] dialog'),
  close: document.querySelector('[data-live="share"] .x'),
  url: document.querySelector('[data-live="share"] .shurl'),
  copy: document.querySelector('[data-live="share"] .shcopy'),
  native: document.querySelector('[data-live="share"] .shnative'),
  about: document.querySelector('[data-live="share"] .shabout'),
  imagebox: document.querySelector('[data-live="share"] .shimage'),
  sizes: document.querySelectorAll('[data-live="share"] .sizes button'),
  img: document.querySelector('[data-live="share"] .preview img'),
  dl: document.querySelector('[data-live="share"] .shdl'),
  toast: document.querySelector('[data-live="share"] .toast'),
};

// What the page is showing now: { url, r, st, ctx, party } with r null when
// no control is moved (the published forecast) or the setting was refused.
let now = null;
let size = "link";
let cache = {};
let opener = null;

export function setShareable(info) {
  now = info;
  cache = {};
  S.open.disabled = false;
  if (S.dlg.open) fill();
}

const say = s => { S.toast.textContent = s; };

function fill() {
  S.url.value = now.url;
  S.native.hidden = typeof navigator.share !== "function";
  if (!now.r) {
    S.native.disabled = false;
    S.about.textContent = "No control is moved, so this link opens the published forecast. Move a control to share your own settings and an image of what they give.";
    S.imagebox.hidden = true;
    return;
  }
  S.about.textContent = "The link opens this page with your settings, and anyone who follows it sees the same figures. " +
    "The image shows the seats your settings give: the model's simulations re-weighted by your assumptions, not its forecast.";
  S.imagebox.hidden = false;
  draw();
}

async function draw() {
  const want = size, info = now;
  S.native.disabled = true;
  S.dl.disabled = true;
  for (const b of S.sizes) b.setAttribute("aria-pressed", String(b.dataset.size === want));
  S.img.alt = playCardAlt(info);
  try {
    if (!cache[want]) cache[want] = await svgToPNG(buildPlayCardSVG({ ...info, size: want }), SIZES[want]);
  } catch (e) {
    say("The image could not be drawn in this browser. The link still works.");
    S.native.disabled = false;
    return;
  }
  if (want !== size || info !== now) return;
  S.img.src = URL.createObjectURL(cache[want]);
  S.native.disabled = false;
  S.dl.disabled = false;
}

const fileBase = () => "joburg-play-settings";
const file = () => new File([cache[size]], fileBase() + "-" + size + ".png", { type: "image/png" });

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
for (const b of S.sizes) b.addEventListener("click", () => { size = b.dataset.size; draw(); });
S.copy.addEventListener("click", async () => {
  try { await navigator.clipboard.writeText(now.url); }
  catch (e) { S.url.select(); document.execCommand?.("copy"); }
  say("Link copied.");
});
S.native.addEventListener("click", () => {
  const data = { title: "Play with the Johannesburg election model", text: "My settings for the Johannesburg election model.", url: now.url };
  if (now.r && cache[size]) {
    const f = file();
    if (navigator.canShare?.({ files: [f] })) data.files = [f];
  }
  navigator.share(data).then(() => say("Shared."))
    .catch(err => { if (err.name !== "AbortError") say("Sharing did not work here. Copy the link instead."); });
});
S.dl.addEventListener("click", () => {
  if (!cache[size]) return;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(cache[size]);
  a.download = fileBase() + "-" + size + ".png";
  a.click();
  say("Image downloaded.");
});
