// The share sheet. One dialog on every device, laid out as a bottom sheet on a
// phone and a centred dialog on a desktop.
//
// Best practice it follows:
//  * The native share sheet (navigator.share) is offered FIRST wherever it
//    exists — on phones that is how people share. The image is rendered BEFORE
//    the button is enabled, so the call happens synchronously inside the tap:
//    Safari drops the user gesture across an await, and share() then fails.
//  * Files are attached only when navigator.canShare({files}) says yes;
//    otherwise the link is shared and the crawler fetches the og:image itself.
//  * Copy link is always there (Clipboard API, with a select-and-copy fallback).
//  * Per-network links are plain <a href> web intents that open in a new tab:
//    they work without JavaScript and without any SDK or tracking script.
//  * Download the image in both sizes.
//  * Native <dialog> + showModal(): the rest of the page is inert, Escape
//    closes, focus is trapped in the dialog and returns to the opener.

import { svgToPNG, SIZES } from "./card.js";

export function intents(url, text) {
  const u = encodeURIComponent(url), t = encodeURIComponent(text);
  return [
    ["X", `https://x.com/intent/post?text=${t}&url=${u}`],
    ["Facebook", `https://www.facebook.com/sharer/sharer.php?u=${u}`],
    ["LinkedIn", `https://www.linkedin.com/sharing/share-offsite/?url=${u}`],
    ["WhatsApp", `https://wa.me/?text=${encodeURIComponent(text + " " + url)}`],
    ["Email", `mailto:?subject=${encodeURIComponent("My Johannesburg election forecast")}&body=${encodeURIComponent(text + "\n\n" + url)}`],
  ];
}

let dlg;

// opts: { url, title, text, svgFor(size) -> string, alt, fileBase }
export async function openShare(opts) {
  if (!dlg) {
    dlg = document.createElement("dialog");
    dlg.className = "sheet";
    dlg.setAttribute("aria-labelledby", "share-title");
    document.body.appendChild(dlg);
  }
  const opener = document.activeElement;
  const canNative = typeof navigator.share === "function";
  dlg.innerHTML = `
  <div class="dh"><h2 id="share-title">Share your forecast</h2>
    <button class="x" type="button" data-close aria-label="Close">×</button></div>
  <div class="db">
    <div class="seg" role="group" aria-label="Image size" style="margin-bottom:8px">
      <button type="button" data-size="link" aria-pressed="true">Link preview</button>
      <button type="button" data-size="story" aria-pressed="false">Story</button>
    </div>
    <div class="preview"><img alt="" id="shimg"></div>
    <div class="row">
      ${canNative ? `<button class="btn primary" type="button" id="shnative" disabled>Share…</button>` : ""}
      <button class="btn${canNative ? "" : " primary"}" type="button" id="shdl" disabled>Download image</button>
    </div>
    <div class="urlrow">
      <label class="visually-hidden" for="shurl">Link to your forecast</label>
      <input id="shurl" type="text" readonly value="">
      <button class="btn" type="button" id="shcopy">Copy link</button>
    </div>
    <p class="toast" id="shtoast" role="status" aria-live="polite"></p>
    <div class="nets" id="shnets"></div>
  </div>`;
  const q = s => dlg.querySelector(s);
  q("#shurl").value = opts.url;
  q("#shnets").innerHTML = intents(opts.url, opts.text).map(([n, h]) =>
    `<a class="btn small" href="${h.replace(/"/g, "&quot;")}" target="_blank" rel="noopener noreferrer">${n}</a>`).join("");

  let size = "link";
  const cache = {};
  const render = async () => {
    q("#shimg").alt = opts.alt;
    if (q("#shnative")) q("#shnative").disabled = true;
    q("#shdl").disabled = true;
    if (!cache[size]) {
      const svg = opts.svgFor(size);
      q("#shimg").src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
      cache[size] = await svgToPNG(svg, SIZES[size]);
    }
    q("#shimg").src = URL.createObjectURL(cache[size]);
    if (q("#shnative")) q("#shnative").disabled = false;
    q("#shdl").disabled = false;
  };
  const file = () => new File([cache[size]], `${opts.fileBase}-${size}.png`, { type: "image/png" });

  dlg.querySelectorAll("[data-size]").forEach(b => b.addEventListener("click", () => {
    size = b.dataset.size;
    dlg.querySelectorAll("[data-size]").forEach(x => x.setAttribute("aria-pressed", String(x === b)));
    render();
  }));
  q("#shnative")?.addEventListener("click", () => {
    const data = { title: opts.title, text: opts.text, url: opts.url };
    const f = cache[size] && file();
    if (f && navigator.canShare?.({ files: [f] })) data.files = [f];
    navigator.share(data).then(() => { q("#shtoast").textContent = "Shared."; })
      .catch(err => { if (err.name !== "AbortError") q("#shtoast").textContent = "Sharing did not work here. Copy the link instead."; });
  });
  q("#shdl").addEventListener("click", () => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(cache[size]); a.download = `${opts.fileBase}-${size}.png`;
    document.body.appendChild(a); a.click(); a.remove();
    q("#shtoast").textContent = "Image downloaded.";
  });
  q("#shcopy").addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(opts.url); }
    catch (e) { q("#shurl").select(); document.execCommand?.("copy"); }
    q("#shtoast").textContent = "Link copied.";
  });
  dlg.onclick = e => { if (e.target.closest("[data-close]")) dlg.close(); };
  dlg.onclose = () => opener?.focus?.();
  dlg.showModal();
  q("#shcopy").focus();
  render().catch(() => { q("#shtoast").textContent = "The image could not be drawn in this browser. The link still works."; });
}
