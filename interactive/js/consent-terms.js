// The consent screen's wording and its contract with the server, in ONE place.
//
// PURE: no DOM, no Worker APIs, no I/O. The page (js/auth-ui.js) renders the
// screen from consentTerms() and nothing else; the Worker
// (worker-api/src/consent.js) imports this module to accept exactly the keys
// the page sends and to derive the wording version.
//
// WORDING VERSION = a hash of the displayed text. The page hashes the terms it
// rendered and sends the hash; the server hashes the terms it would render
// (same function, same deletion date) and refuses a mismatch, so the version
// recorded in the consent log names text the reader was actually shown. Any
// edit to a string below changes the version; there is nothing to bump.
//
// ⛔ DRAFT WORDING for the owner and counsel (worker-api/README.md, "Stubs").
// The "Where" line is a placeholder for an owner decision (R5 finding 3) and
// must be replaced before launch.
//
// Owner, 2026-09-29: a saved forecast is a PREDICTION of the outcome, treated
// as ordinary personal information; no real name is collected or shown (the
// label defaults to an X @username where the reader signed in with X, or to a
// random "<word>-<number>" label per forecast, js/labels.js).

// The four choices the screen asks for, each sent as true or false. The server
// refuses a missing one rather than defaulting it.
export const SCREEN_PURPOSES = ["store", "age18", "contact_if_win", "updates"];
// Saving needs these two.
export const REQUIRED_PURPOSES = ["store", "age18"];
// Every key POST /api/consent accepts. `contact` is optional: an address the
// reader asks us to confirm (one link is sent; nothing is stored until the
// link is used). `wording_version` is required.
export const CONSENT_KEYS = [...SCREEN_PURPOSES, "contact", "wording_version"];

export const PROVIDER_LABELS = { google: "Google", apple: "Apple", facebook: "Facebook", x: "X", microsoft: "Microsoft" };

export const DATE_NOT_SET = "[date to be set by the owner]";

// The deletion date as the screen prints it: the calendar date of DELETION_AT
// (UTC), or the placeholder while the owner has not set it.
export function deletionDateText(iso) {
  if (!iso) return DATE_NOT_SET;
  const t = Date.parse(iso);
  if (!Number.isFinite(t)) throw new Error(`not a date: ${iso}`);
  return new Date(t).toISOString().slice(0, 10);
}

// Everything the consent screen shows, in display order. `deletionDate` is the
// output of deletionDateText.
export function consentTerms({ deletionDate }) {
  return {
    title: "Before we save your prediction",
    signedInWith: "Signed in with",
    boxes: {
      store: "Save my prediction and link it to my sign-in. I agree to it being kept and used as described below.",
      age18: "I am 18 or older.",
      contact_if_win: "Email me if my prediction wins.",
      updates: "Email me updates about the forecast before and after the election. Every email has an unsubscribe link.",
    },
    requiredHeading: "Needed to save",
    optionalHeading: "Optional: leave these unticked and your prediction is still saved",
    contactLabel: "Email address (optional)",
    contactHelp: "We send one email to this address with a link to confirm it. We keep the address only if you use that link. We never email an address that has not been confirmed, apart from that one link.",
    facts: [
      ["We keep", "the sign-in service you used and its account id for you, one email address once it is confirmed, your predictions with the label you chose for each, and these choices with the date. We do not collect your name."],
      ["Label", "A shared prediction shows a label, never your name: your X @username if you signed in with X, otherwise a random name such as \"pollster-23\", new for each prediction. You can replace it with your own words before sharing, or clear yours to go back to the random one."],
      ["Who sees it", "Anyone with the link to a prediction can see it. Links are not listed and are marked so search engines do not index them."],
      ["Used to", "show your prediction at its link, score it against the result, and analyse saved predictions against the result and against past elections."],
      ["One email", `Whatever you tick here, we send one email after the election to your confirmed address, asking whether to delete your data now or to keep your address to tell you about the next election. If you do not answer, your account, predictions and address are deleted on ${deletionDate}.`],
      ["No confirmed email", `If we hold no confirmed address for you, we cannot send that email. Your account and predictions are then deleted on ${deletionDate} without it.`],
      ["Delete", "any prediction, or your whole account, at any time from \"My forecasts\". You do not need an email address to delete."],
      ["After deleting", "Deleting removes it from our database and image store at once. Copies last a limited time after that: database backups up to 30 days, service logs up to 7 days, and a browser that has already shown a prediction's image may keep its copy for up to a year. The privacy notice lists each one."],
      ["Where", "[Where the data is stored: the owner and counsel to decide before launch.]"],
      ["Never", "sold, used for advertising, or shared except as you choose to share it."],
    ],
    links: { notice: "Privacy notice", officer: "Information Officer", competition: "Competition rules" },
    submit: "Agree and save",
    cancel: "Don't save",
  };
}

// The exact text the version is computed over: every string in the terms, in
// display order, as JSON.
export function canonicalText(terms) {
  return JSON.stringify(terms);
}

// "w1-" + the first 24 hex digits of sha256(canonicalText). Web Crypto only,
// so the page and the Worker compute it the same way.
export async function wordingVersion(terms) {
  const d = new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(canonicalText(terms))));
  return "w1-" + Array.from(d.slice(0, 12), b => b.toString(16).padStart(2, "0")).join("");
}

// The body the page posts to /api/consent. Exactly CONSENT_KEYS; `contact` is
// left out when the reader typed none.
export function consentPayload({ store, age18, contact_if_win, updates, contact, wording_version }) {
  const out = { store: Boolean(store), age18: Boolean(age18), contact_if_win: Boolean(contact_if_win),
    updates: Boolean(updates), wording_version };
  const c = typeof contact === "string" ? contact.trim() : "";
  if (c) out.contact = c;
  return out;
}
