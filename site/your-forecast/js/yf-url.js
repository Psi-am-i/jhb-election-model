// "Your forecast": the page's ONE address. Both sections keep the reader's
// state in it, and nowhere else; this module is the only place it is written.
//
// PURE apart from the one history call: no DOM, no fetch, no figures. Read by
// stats.script_writes as a NON-writer module.
//
// The address is three disjoint parts, each written by its own state module:
//   section 1, "Adjust the model"   play-state.js serialize:  t p k l b mv
//   section 2, "Break the model"    make-state.js serialize:  v c f
//   the name on either share image  n (play-state.cleanName, the one rule)
// so a link opened by one section is never clobbered by the other's next
// write (one writer per address). Old /play/?… and /make/?… links reach this
// page with their query strings (src/worker.js), and each part reads back
// unchanged. A link to section 2 carries section 1's settings too: section 2
// "continues the same forecast", so its start is section 1's hand-off.

import { cleanName, NAME_MAX } from "./play-state.js";

export const ADJUST_KEYS = "t p k l b mv".split(" ");
export const BREAK_KEYS = "v c f".split(" ");
export const NAME_KEY = "n";

const parts = { adjust: "", break: "" };
let name = "";

// The address for `adjust` and `brk` (each a serialize() string, "" or
// "?…"), and `n`. Throws if a part carries a key that is not its own: two
// parts writing one key is the defect this module exists to prevent.
export function compose(adjust, brk, n) {
  const q = new URLSearchParams();
  for (const [part, keys] of [[adjust, ADJUST_KEYS], [brk, BREAK_KEYS]]) {
    for (const [k, v] of new URLSearchParams(part || "")) {
      if (!keys.includes(k)) throw new Error("the address part for " + keys.join(",") + " wrote " + k);
      q.set(k, v);
    }
  }
  const nm = cleanName(n);
  if (nm) q.set(NAME_KEY, nm);
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

// The name an address carries, as the page keeps it. A name longer than
// NAME_MAX is refused whole, never cut (code review, 2026-10-01): "".
export function nameOf(search) {
  const raw = new URLSearchParams(search).get(NAME_KEY);
  return raw == null || raw.length > NAME_MAX ? "" : cleanName(raw);
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
  name = nameOf(search);
}

// The address with one part, or the name, replaced. `which` is "adjust",
// "break" or "name". Returns the query string written.
export function write(which, value) {
  if (which === "name") name = cleanName(value);
  else if (which in parts) parts[which] = value || "";
  else throw new Error("no address part " + which);
  const q = compose(parts.adjust, parts.break, name);
  history.replaceState(null, "", location.pathname + q + location.hash);
  return q;
}

// The link to one section as it stands: section 1's share link carries only
// section 1 and the name; section 2's carries both, since it continues
// section 1. `hash` is the section's anchor.
export function linkTo(which, hash) {
  const q = which === "adjust" ? compose(parts.adjust, "", name) : compose(parts.adjust, parts.break, name);
  return new URL(location.pathname + q + (hash || ""), location.href).href;
}

export function currentName() { return name; }
