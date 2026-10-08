// Default labels for shared predictions (owner, 2026-09-29).
//
// No real name is collected or shown. A shared prediction carries a label:
//   * the reader's own text, if they typed one (validated like any label);
//   * otherwise, for a reader who signed in with X, "@username";
//   * otherwise a RANDOM "<word>-<number>" label, e.g. "pollster-23",
//     generated on the server with a CSPRNG, ONCE PER FORECAST (not per
//     account, so two predictions by one reader are not linkable by label),
//     and checked unique against live labels (worker-api/src/forecasts.js).
//
// The word list is the one place these words live. Rules for adding a word:
// neutral election-watcher words only; no party name, abbreviation, colour or
// slogan that suggests an allegiance; nothing offensive; nothing that reads as
// an official or the site ("iec", "official", "admin", "moderator"). The
// worker-api tests check every word against the display-name blocklist and
// against the party roster.
//
// PURE: Web Crypto only; the Worker (validate.js, forecasts.js) imports it.

export const LABEL_WORDS = [
  "politico", "pollster", "analyst", "swingvoter", "psephologist", "canvasser",
  "observer", "forecaster", "strategist", "commentator", "wardwatcher", "tallyclerk",
  "numbercruncher", "spectator", "voter", "boothwatcher", "turnoutwatcher",
  "seatcounter", "councilwatcher",
];

// Numbers 1..LABEL_MAX_NUMBER: with the word list above that is
// LABEL_WORDS.length * LABEL_MAX_NUMBER combinations, so collisions are rare
// and a collision is retried.
export const LABEL_MAX_NUMBER = 9999;

export const LABEL_RE = new RegExp(`^(${LABEL_WORDS.join("|")})-([1-9][0-9]{0,3})$`);

// An unbiased integer in [0, n) from crypto.getRandomValues (rejection
// sampling: values in the incomplete top range are discarded).
export function randomBelow(n, rand = a => crypto.getRandomValues(a)) {
  if (!Number.isInteger(n) || n < 1 || n > 2 ** 32) throw new Error("randomBelow: bad range");
  const limit = Math.floor(2 ** 32 / n) * n;
  const buf = new Uint32Array(1);
  for (;;) {
    rand(buf);
    if (buf[0] < limit) return buf[0] % n;
  }
}

export function randomLabel(rand) {
  const w = LABEL_WORDS[randomBelow(LABEL_WORDS.length, rand)];
  return `${w}-${randomBelow(LABEL_MAX_NUMBER, rand) + 1}`;
}

// The X default: "@" + the username X returned. X usernames are 1-15 letters,
// digits or underscores; anything else is not used.
export function handleLabel(username) {
  return typeof username === "string" && /^[A-Za-z0-9_]{1,15}$/.test(username) ? "@" + username : null;
}
