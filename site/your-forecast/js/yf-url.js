// "Your forecast": the page's ONE address. Both sections keep the reader's
// state in it, and nowhere else; this module is the only place it is written.
//
// PURE apart from the one history call: no DOM, no fetch, no figures. Read by
// stats.script_writes as a NON-writer module.
//
// The address is five disjoint parts, each written by its own state module:
//   section 1, "Adjust the model"   play-state.js serialize:  t p k l b mv
//   section 2, "Break the model"    make-state.js serialize:  v c f
//   the name on either share image  n (play-state.cardName, the one rule)
//   a friend's forecast, kept for   vs vn (make.js: the forecast a shared
//     the return card                link opened with, and its name)
//   a shared link's arrival         from s (read only: `from=1` opens the
//                                    arrival view, `s` is the link's seal;
//                                    kept until the reader picks a start,
//                                    then dropped, since any edit or new name
//                                    needs a new seal)
// so a link opened by one section is never clobbered by the other's next
// write (one writer per address). Old /play/?… and /make/?… links reach this
// page with their query strings (src/worker.js), and each part reads back
// unchanged. A link to section 2 carries section 1's settings too: section 2
// "continues the same forecast", so its start is section 1's hand-off.

import { cardName, NAME_MAX } from "./play-state.js";

export const ADJUST_KEYS = "t p k l b mv".split(" ");
export const BREAK_KEYS = "v c f".split(" ");
export const NAME_KEY = "n";
export const FRIEND_KEYS = "vs vn".split(" ");
export const ARRIVAL_KEYS = "from s".split(" ");

const parts = { adjust: "", break: "", friend: "", arrival: "" };
let name = "";

// The address for `adjust` and `brk` (each a serialize() string, "" or
// "?…"), and `n`. Throws if a part carries a key that is not its own: two
// parts writing one key is the defect this module exists to prevent.
export function compose(adjust, brk, n, friend = "", arrival = "") {
  const q = new URLSearchParams();
  const own = (part, keys) => {
    for (const [k, v] of new URLSearchParams(part || "")) {
      if (!keys.includes(k)) throw new Error("the address part for " + keys.join(",") + " wrote " + k);
      q.set(k, v);
    }
  };
  own(adjust, ADJUST_KEYS);
  own(brk, BREAK_KEYS);
  const nm = cardName(n);
  if (nm) q.set(NAME_KEY, nm);
  own(friend, FRIEND_KEYS);
  own(arrival, ARRIVAL_KEYS);
  const s = q.toString().replace(/%2C/g, ",");
  return s ? "?" + s : "";
}

// One section's part of an address: the query string with only its keys.
export function partOf(search, keys) {
  const q = new URLSearchParams(search);
  const out = new URLSearchParams();
  for (const [k, v] of q) if (keys.includes(k)) out.set(k, v);
  const s = out.toString().replace(/%2C/g, ",");
  return s ? "?" + s : "";
}

// The name an address carries, as the page keeps it (cardName): a name longer
// than NAME_MAX is refused whole, never cut (code review, 2026-10-01), and so
// is one the owner's blocklist refuses: "".
export function nameOf(search) {
  return cardName(new URLSearchParams(search).get(NAME_KEY));
}

// Did the address carry a name too long to use?
export function nameRefused(search) {
  const raw = new URLSearchParams(search).get(NAME_KEY);
  return raw != null && raw.length > NAME_MAX;
}

// Seed the parts from the address the page opened with, so a section that has
// not started yet keeps its part of a shared link.
export function open(search) {
  parts.adjust = partOf(search, ADJUST_KEYS);
  parts.break = partOf(search, BREAK_KEYS);
  parts.friend = partOf(search, FRIEND_KEYS);
  parts.arrival = partOf(search, ARRIVAL_KEYS);
  name = nameOf(search);
}

// The arrival the address opened with: { from: did a shared link open the
// page, s: its seal or "" }.
export function arrival() {
  const q = new URLSearchParams(parts.arrival);
  return { from: q.get("from") === "1", s: q.get("s") || "" };
}

// The friend's forecast the address carries for the return card:
// { f, name } or null. The name is the page's one rule's (cardName).
export function friend() {
  const q = new URLSearchParams(parts.friend);
  if (!q.get("vs")) return null;
  return { f: q.get("vs"), name: cardName(q.get("vn")) };
}

// The address with one part, or the name, replaced. `which` is "adjust",
// "break" or "name". Returns the query string written.
export function write(which, value) {
  if (which === "name") name = cardName(value);
  else if (which in parts) parts[which] = value || "";
  else throw new Error("no address part " + which);
  const q = compose(parts.adjust, parts.break, name, parts.friend, parts.arrival);
  history.replaceState(null, "", location.pathname + q + location.hash);
  return q;
}

// The friend part for a forecast `f` and its name ("" leaves the name off).
export function friendPart(f, n) {
  if (!f) return "";
  const q = new URLSearchParams({ vs: f });
  const nm = cardName(n);
  if (nm) q.set("vn", nm);
  return "?" + q.toString();
}

// The link to one section as it stands: section 1's share link carries only
// section 1 and the name; section 2's carries both, since it continues
// section 1. `hash` is the section's anchor.
// The return card's link adds the friend's part (`withFriend`); a link never
// carries the arrival part: a seal is added by the share sheet for the state
// it shares, and `from` by the server's /s/ redirect.
export function linkTo(which, hash, { withFriend = false } = {}) {
  const q = which === "adjust" ? compose(parts.adjust, "", name)
    : compose(parts.adjust, parts.break, name, withFriend ? parts.friend : "");
  return new URL(location.pathname + q + (hash || ""), location.href).href;
}

export function currentName() { return name; }

// In the page, the parts are seeded from the address it opened with, before
// either section writes: a section that has not written yet (section 2 is
// lazy) keeps its part of a shared link, and so does the name. Under node
// there is no address; the tests call open() themselves.
if (typeof location !== "undefined") open(location.search);
