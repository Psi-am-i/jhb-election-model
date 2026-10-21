// THE ONE SHARE SHEET's controls (owner, 2026-10-11: "a share button on every
// page", one sheet, reused). Two callers hand it the elements of their own
// copy of the sheet and what they share:
//  * every site page, through js/page-share.js: the page's own address and
//    its own share image (og:image), both read from the page's head;
//  * "Your forecast", through interactive/js/share-sheet.js: a drawn card and
//    a sealed link (served beside this file as ../../js/share-dialog.js;
//    src/build_your_forecast.py rewrites the one import line).
// What it does, the same for both: the native <dialog> (showModal: the page
// behind is inert, Escape closes, focus returns to the button that opened
// it; a click on the backdrop closes), Copy link with a select-and-copy
// fallback, the WhatsApp and X links, Share… (the Web Share API, shown only
// where the browser has it; a file is attached only where
// navigator.canShare({files}) allows), Download image, and the line that
// says what happened.
//
// It writes words and properties only (textContent, href, disabled, hidden),
// never markup, and holds no figure, selector or data source: it is scanned
// as a non-writer by stats.script_writes wherever a page loads it.

const WA = "https://wa.me/?text=";
const X = "https://x.com/intent/post?url=";

// E: { open, more (optional, more openers), dlg, close, url, copy, wa, x, native, dl, toast }
// H: what the caller shares, as functions of what its page shows now:
//   canOpen()      may the sheet open (default: yes)
//   prepare()      async, before it opens
//   opened()       after it opens: the caller fills the sheet
//   link(ch)       the address the button `ch` sends ("copy", "wa", "x",
//                  "native")
//   on()           may the buttons that send the link send it now
//   nativeOn()     and is the image Share… attaches ready (default: yes)
//   shareWords()   { title, text } for Share…
//   file()         a File for Share… to attach, or null
//   download()     { href, name, done } for Download image, or null; `done`
//                  runs once the download has started
// Returns { say(words), buttons(): the link or its state changed,
//   isOpen(), close() }.
export function shareDialog(E, H) {
  let opener = null;
  const say = s => { E.toast.textContent = s; };
  // Share… exists only where the browser has the Web Share API: hidden and
  // off everywhere else, from the start
  const hasWebShare = () => typeof navigator.share === "function";
  E.native.hidden = !hasWebShare();

  function buttons() {
    const on = !!H.on();
    E.url.value = on ? H.link("copy") : "";
    E.copy.disabled = !on;
    for (const [a, ch, base] of [[E.wa, "wa", WA], [E.x, "x", X]]) {
      if (on) a.href = base + encodeURIComponent(H.link(ch)); else a.removeAttribute("href");
      a.setAttribute("aria-disabled", String(!on));
    }
    E.native.hidden = !hasWebShare();
    E.native.disabled = !(hasWebShare() && on && (H.nativeOn ? H.nativeOn() : true));
  }

  // E.more: further openers of the same sheet (a page's section buttons);
  // focus returns to whichever opened it
  for (const b of [E.open, ...(E.more || [])]) b.addEventListener("click", async () => {
    if (H.canOpen && !H.canOpen()) return;
    opener = b;
    say("");
    await H.prepare?.();
    E.dlg.showModal();
    E.native.hidden = !hasWebShare();
    H.opened?.();
    E.copy.focus();
  });
  E.close.addEventListener("click", () => E.dlg.close());
  E.dlg.addEventListener("click", e => { if (e.target === E.dlg) E.dlg.close(); });
  E.dlg.addEventListener("close", () => opener?.focus?.());
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
    if (!hasWebShare()) return;
    const data = { ...H.shareWords(), url: H.link("native") };
    const f = H.file?.();
    if (f && navigator.canShare?.({ files: [f] })) data.files = [f];
    navigator.share(data).then(() => say("Shared."))
      .catch(err => { if (err.name !== "AbortError") say("Sharing did not work here. Copy the link instead."); });
  });
  E.dl.addEventListener("click", () => {
    const d = H.download();
    if (!d) return;
    const a = document.createElement("a");
    a.href = d.href;
    a.download = d.name;
    a.click();
    if (d.done) setTimeout(d.done, 10000);   // after the download has started
    say("Image downloaded.");
  });

  return {
    say,
    buttons,
    isOpen: () => E.dlg.open,
    close() { if (E.dlg.open) E.dlg.close(); },
  };
}
