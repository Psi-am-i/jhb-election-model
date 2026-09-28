// Shared helpers for the prototype pages. ES module.
//
// ⚠ PROTOTYPE. Every number the pages draw comes from interactive/fixtures/,
// which are SYNTHETIC placeholders (see tools/make_fixtures.py). Nothing here
// is, or may be mistaken for, the model's forecast.

// interactive/, computed when first asked for and never at module load: the
// share-card Worker (worker-api) imports this module for esc and possessive,
// and a bundled Worker has no URL to resolve import.meta.url against.
const base = () => new URL("../", import.meta.url);

export async function loadJSON(name) {
  const r = await fetch(new URL("fixtures/" + name, base()));
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

// The one definition of a reader's forecast, the file the Worker validates
// against (worker-api/generated/forecast.schema.json, generated from the
// model artefact). Fetched once.
let schemaP = null;
export function loadSchema() {
  schemaP ??= fetch(new URL("../worker-api/generated/forecast.schema.json", base())).then(r => {
    if (!r.ok) throw new Error(`forecast schema: HTTP ${r.status}`);
    return r.json();
  });
  return schemaP;
}

export function pageURL(rel) { return new URL(rel, base()).href; }

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
// v2 (2026-09-28): the draft's shares became the combined vote (`share`,
// DESIGN-decided §10); a v1 draft held list-vote shares under `pr` and is not
// read as if it meant the same thing.
// v3 (2026-09-29): the builder holds whole votes (`votes`) and every ward
// called (DESIGN-decided §14); a v2 draft could hold uncalled wards and a
// share sum off 100, so it is not read.
const DRAFT = "jhb-interactive-draft-v3";
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
