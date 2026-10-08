// Shared helpers for the prototype pages. ES module.
//
// ⚠ PROTOTYPE. Every number the pages draw comes from interactive/fixtures/,
// which are SYNTHETIC placeholders (see tools/make_fixtures.py). Nothing here
// is, or may be mistaken for, the model's forecast.

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

export function topN(seats, n, byCode) {
  return Object.entries(seats).filter(([, v]) => v > 0)
    .sort((a, b) => b[1] - a[1] || byCode[a[0]].name.localeCompare(byCode[b[0]].name))
    .slice(0, n);
}

export function announce(el, text) {
  // aria-live regions re-announce only on change
  if (el.textContent !== text) el.textContent = text;
}
