// ⛔ PROTOTYPE SHIM, replaced at integration. The published forecast's panels on
// "play with the model", before any control moves (SPEC-v2 F6, F14).
//
// In production build_site renders these panels into the page from the ledger
// as {{tokens}} (INTEGRATION §3c: "first paint is static"), and this file is
// deleted. The unbuilt prototype has no renderer, so it shows the published
// page's own rendered regions instead: it fetches site/forecast.html and moves
// its TILES, SEATS, GOVERN, CLAIMS and MAP regions, with their ledgered token
// spans, into the hosts below. It computes nothing and types no figure; every
// digit it shows is the published page's.
//
// Each panel lives in a shadow root carrying the published page's own styles,
// so the two pages' class names (.row, .chip) cannot collide. The published
// page's scripts do not run here, so its map toggle and coalition filter are
// hidden rather than left dead.
//
//   <div class="published" data-published="seats|tiles|govern|claims|map"></div>

const FORECAST = new URL("../../site/forecast.html", import.meta.url);

function region(doc, name) {
  const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_COMMENT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    if (n.nodeValue.trim() === `__${name}_START__`) return n.parentNode;
  }
  return null;
}

const PICK = {
  tiles: doc => doc.querySelector("#tiles") || region(doc, "TILES"),
  seats: doc => region(doc, "SEATS"),
  govern: doc => region(doc, "GOVERN")?.closest(".tablewrap") || region(doc, "GOVERN")?.closest("table"),
  claims: doc => doc.querySelector("#claims") || region(doc, "CLAIMS"),
  map: doc => region(doc, "MAP"),
};

const HIDE = ".maptoggle,.govfilter,script{display:none!important}:host{display:block}";

export async function paintPublished(root = document) {
  const hosts = [...root.querySelectorAll("[data-published]")];
  let doc;
  try {
    const r = await fetch(FORECAST);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    doc = new DOMParser().parseFromString(await r.text(), "text/html");
  } catch (e) {
    for (const h of hosts) h.textContent = `The published forecast (${FORECAST.pathname}) could not be loaded: ${e.message}.`;
    return false;
  }
  const styles = [...doc.querySelectorAll("style")].map(s => s.textContent).join("\n");
  for (const h of hosts) {
    const el = PICK[h.dataset.published]?.(doc);
    if (!el) { h.textContent = `The published page has no ${h.dataset.published} panel.`; continue; }
    const shadow = h.shadowRoot || h.attachShadow({ mode: "open" });
    const style = document.createElement("style");
    style.textContent = styles + "\n" + HIDE;
    const node = document.importNode(el, true);
    // the published page's relative links and images resolve against it, not here
    for (const [sel, attr] of [["img[src]", "src"], ["a[href]", "href"]])
      node.querySelectorAll(sel).forEach(x => {
        const v = x.getAttribute(attr);
        if (!/^(#|[a-z]+:)/i.test(v)) x.setAttribute(attr, new URL(v, FORECAST).href);
      });
    shadow.replaceChildren(style, node);
  }
  return true;
}
