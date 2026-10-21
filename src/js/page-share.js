// The share button by every page's title (build_site.share_button, owner,
// 2026-10-11): the site's one share sheet (share-dialog.js) with this page's
// content. The link is the page's canonical address, read from its head; the
// preview and the download are its own share image (its og:image), which the
// build wrote into the sheet's <img>, relative, so a preview or a UAT version
// shows the image beside it. Share… sends the link; the app it goes to draws
// the page's own preview from og:image.
//
// It writes words and properties only, and no figure.
import { shareDialog } from "./share-dialog.js";

const box = document.querySelector("[data-pgshare]");
if (box) {
  const q = sel => box.querySelector(sel);
  const canonical = document.querySelector('link[rel="canonical"]');
  const page = canonical ? canonical.href : location.href;
  const pic = q(".preview img");
  const E = {
    open: q(".pgshare-open"), more: [...document.querySelectorAll("[data-pgshare-more]")], dlg: q("dialog"), close: q(".x"), url: q(".shurl"), copy: q(".shcopy"),
    wa: q(".shwa"), x: q(".shx"), native: q(".shnative"), dl: q(".shdl"), toast: q(".toast"),
  };
  const D = shareDialog(E, {
    opened: () => D.buttons(),
    link: () => page,
    on: () => true,
    shareWords: () => ({ title: document.title }),
    file: () => null,
    download: () => ({ href: pic.src, name: pic.src.split("/").pop() }),
  });
  D.buttons();
}
