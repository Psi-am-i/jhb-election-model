// "Your forecast": how many forecasts have been sealed so far (owner,
// 2026-10-03). Every seal is stored as one entry (src/share-edge.js), and
// before the results only their number is shown: no name and no forecast.
//
// ⛔ A LIVE WRITER (stats.LIVE_WRITERS["your-forecast/js/entries.js"]) for the
// one region "entries", reached through the literal selector below, written
// with textContent only. arrival.js prints the same line in its own region,
// from entryCount and countLine here: one request, one wording.
//
// The count is the site Worker's GET /entries/1/count, kept at the edge a
// minute. Off the site (a local build), before the entries database exists,
// or at zero, the region stays hidden.

const R = document.querySelector('[data-live="entries"]');
// Beside the page's own directory: /entries/1/count.
const ROOT = new URL("../../", import.meta.url);

let asked = null;
// The number of entries, or null when it cannot be read. Asked once per page.
export function entryCount() {
  asked ??= fetch(new URL("entries/1/count", ROOT))
    .then(r => (r.ok ? r.json() : null))
    .then(b => (b && Number.isInteger(b.count) && b.count >= 0 ? b.count : null))
    .catch(() => null);
  return asked;
}

// The line, or "" when there is nothing to show.
export function countLine(n) {
  if (!n) return "";
  return n + (n === 1 ? " forecast" : " forecasts") + " sealed so far.";
}

entryCount().then(n => {
  if (!R) return;
  R.textContent = countLine(n);
  R.hidden = !R.textContent;
});
