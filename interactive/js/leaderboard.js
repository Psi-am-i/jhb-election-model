// /leaderboard/ (src/build_leaderboard.py): every sealed forecast ranked
// against the result, from leaderboard.json (src/rank_entries.py, which
// scores each entry by src/score_forecasts.py). This module computes nothing:
// it lists every entry and finds a reader's own entry by its link. How much
// of a seal id names an entry (`id_chars`) and the vote error's decimals
// (`vote_dp`) come from leaderboard.json, their one definition being
// src/rank_entries.py.
//
// ⛔ A LIVE WRITER (stats.LIVE_WRITERS["leaderboard/js/leaderboard.js"]) for
// the regions "lb-top" (every entry, by place) and "lb-mine" (the reader's link and
// where it placed), each reached through a literal selector below and
// written with createElement and textContent, never markup.

const TOP = document.querySelector('[data-live="lb-top"]');
const FORM = document.querySelector('[data-live="lb-mine"] form');
const LINK = document.querySelector('[data-live="lb-mine"] input');
const FOUND = document.querySelector('[data-live="lb-mine"] .lb-found');
const YOURS = document.querySelector('[data-live="lb-mine"] .lb-yours');
// leaderboard.json sits beside the page, one level above this module.
const DATA = new URL("../leaderboard.json", import.meta.url);

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

// The SAST time a seal was made, from its ISO time.
function when(iso) {
  return new Date(iso).toLocaleString("en-ZA", { timeZone: "Africa/Johannesburg", day: "numeric",
    month: "short", hour: "2-digit", minute: "2-digit" });
}

function table(rows, b, mine) {
  const t = el("table", "lb-table");
  const head = el("tr");
  for (const [text, num] of [["Place", true], ["Forecast", false], ["Seats off", true],
                             ["Wards right, of " + b.wards, true], ["Vote off, points", true], ["Sealed", false]]) {
    const th = el("th", num ? "num" : "", text);
    th.scope = "col";
    head.append(th);
  }
  const thead = el("thead"), tbody = el("tbody");
  thead.append(head);
  for (const r of rows) {
    const tr = el("tr", r.id === mine ? "lb-you" : "");
    tr.append(el("td", "num", String(r.place)), el("td", "", r.name), el("td", "num", String(r.seat_error)),
      el("td", "num", String(r.wards_called)), el("td", "num", r.list_vote_error.toFixed(b.vote_dp)), el("td", "", when(r.sealed_at)));
    tbody.append(tr);
  }
  t.append(thead, tbody);
  const wrap = el("div", "lb-wrap");
  wrap.append(t);
  return wrap;
}

// The entry's id from a reader's link (its `s`, the part after the dot), or
// from a seal id pasted alone: its first `idChars` characters.
export function idOf(text, idChars) {
  const raw = String(text || "").trim();
  let s = raw;
  try { s = new URL(raw).searchParams.get("s") || ""; } catch (e) { s = raw; }
  const sig = s.includes(".") ? s.split(".")[1] : s;
  return /^[A-Za-z0-9_-]+$/.test(sig) && sig.length >= idChars ? sig.slice(0, idChars) : "";
}

let board = null;
function find(text) {
  const id = idOf(text, board.id_chars);
  YOURS.replaceChildren();
  if (!id) { FOUND.textContent = "That is not a sealed link."; return; }
  const row = board.rows.find(r => r.id === id);
  if (!row) { FOUND.textContent = "No entry has this seal. Only links sealed before polls opened are entered."; return; }
  FOUND.textContent = row.name + " placed " + row.place + " of " + board.entries + ".";
  YOURS.append(table([row], board, id));
  show(id);
}

function show(mine) {
  TOP.replaceChildren(table(board.rows, board, mine));
}

fetch(DATA).then(r => (r.ok ? r.json() : Promise.reject(new Error(String(r.status))))).then(b => {
  board = b;
  show("");
  const s = new URLSearchParams(location.search).get("s");
  if (s) { LINK.value = location.href; find(location.href); }
}).catch(() => { TOP.textContent = "The leaderboard could not be loaded."; });

FORM.addEventListener("submit", e => {
  e.preventDefault();
  if (board) find(LINK.value);
});
