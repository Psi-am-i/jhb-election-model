// Shared helpers for the prototype pages. ES module.
//
// ⚠ PROTOTYPE. Every number the pages draw comes from interactive/fixtures/,
// which are SYNTHETIC placeholders (see tools/make_fixtures.py). Nothing here
// is, or may be mistaken for, the model's forecast.

const base = new URL("../", import.meta.url);   // interactive/

export async function loadJSON(name) {
  const r = await fetch(new URL("fixtures/" + name, base));
  if (!r.ok) throw new Error(`fixture ${name}: HTTP ${r.status}`);
  return r.json();
}

export async function loadAll() {
  const [geom, model] = await Promise.all([
    loadJSON("geometry.json"), loadJSON("placeholder-model.json")]);
  const parties = model.parties;
  const byCode = Object.fromEntries(parties.map(p => [p.code, p]));
  return { geom, model, parties, byCode };
}

export function pageURL(rel) { return new URL(rel, base).href; }

export function esc(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// A display name is untrusted text that ends up on an image published from our
// domain. The server re-validates (BACKEND.md §5); this only keeps the preview
// honest about what the server will accept.
export function cleanName(s) {
  return String(s || "").normalize("NFKC")
    .replace(/[\u0000-\u001f\u007f​-‏‪-‮⁦-⁩]/g, "")
    .replace(/\s+/g, " ").trim().slice(0, 40);
}

export function possessive(name) {
  if (!name) return "A reader's forecast";
  return /s$/i.test(name) ? `${name}' forecast` : `${name}'s forecast`;
}

export function fmtDate(iso) {
  return new Date(iso).toLocaleDateString("en-ZA",
    { day: "numeric", month: "long", year: "numeric" });
}

// The theme toggle, the same localStorage key and logic as build_site.THEME_HEAD
// (the <head> of each page sets the initial value before paint).
export function wireTheme() {
  document.querySelectorAll(".themetoggle").forEach(b => b.addEventListener("click", () => {
    const root = document.documentElement;
    const light = root.getAttribute("data-theme") !== "light";
    root.setAttribute("data-theme", light ? "light" : "dark");
    try { localStorage.setItem("theme", light ? "light" : "dark"); } catch (e) {}
  }));
}

// Draft storage: a per-viewer convenience only. The saved forecast of record
// lives on the server (BACKEND.md); here the stub server is api-stub.js.
const DRAFT = "jhb-interactive-draft-v1";
export function loadDraft() {
  try { return JSON.parse(localStorage.getItem(DRAFT) || "null"); } catch (e) { return null; }
}
export function saveDraft(d) {
  try { localStorage.setItem(DRAFT, JSON.stringify(d)); } catch (e) {}
}

export function topN(seats, n, byCode) {
  return Object.entries(seats).filter(([, v]) => v > 0)
    .sort((a, b) => b[1] - a[1] || byCode[a[0]].name.localeCompare(byCode[b[0]].name))
    .slice(0, n);
}

export function announce(el, text) {
  // aria-live regions re-announce only on change
  if (el.textContent !== text) el.textContent = text;
}
