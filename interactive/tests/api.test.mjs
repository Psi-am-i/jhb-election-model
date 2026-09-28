// The pages' backend door (js/api.js): which backend a page uses, and how
// GET /api/me becomes the session the consent screen renders from.
//
//   node --test interactive/tests/*.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { modeFor, sessionFromMe } from "../js/api.js";
import { consentScreenHTML } from "../js/auth-ui.js";
import { consentTerms, deletionDateText } from "../js/consent-terms.js";

const repo = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const L = u => { const x = new URL(u); return { hostname: x.hostname, protocol: x.protocol, search: x.search }; };

test("loopback previews use the stub; any other host is production; ?api= overrides", () => {
  for (const u of ["http://127.0.0.1:8801/interactive/make.html", "http://localhost:8801/", "http://[::1]:8801/"])
    assert.equal(modeFor(L(u)), "stub", u);
  assert.equal(modeFor(L("https://joburg.whysoserious.city/make")), "production");
  assert.equal(modeFor(L("https://joburg.whysoserious.city/make?api=stub")), "stub");
  assert.equal(modeFor(L("http://127.0.0.1:8801/make?api=live")), "production");
  assert.equal(modeFor(null), "stub");
});

// The Worker's /api/me (worker-api/src/index.js, me()) answers one of three
// shapes. These literals are its field names; the source check below fails if
// the Worker stops sending any of them.
test("the Worker's /api/me still sends every field the page reads", () => {
  const src = readFileSync(resolve(repo, "worker-api/src/index.js"), "utf8");
  const me = src.slice(src.indexOf("async function me("), src.indexOf("async function deleteMe("));
  for (const k of ["deletion_date", "wording_version", "signed_in", "provider", "has_contact", "handle", "consents",
    "pending", "contact_confirmed", "unconfirmed_contact"])
    assert.match(me, new RegExp(`\\b${k}\\b`), k);
});

test("a pending sign-in opens the consent screen with the server's date, handle and unverified address", () => {
  const s = sessionFromMe({ signed_in: false, pending: true, provider: "microsoft", contact_confirmed: false,
    unconfirmed_contact: "reader@example.com", handle: null, deletion_date: "2027-06-30T00:00:00Z", wording_version: "w1-x" });
  assert.deepEqual(s, { deletion_date: "2027-06-30T00:00:00Z", wording_version: "w1-x", handle: null, provider: "microsoft",
    pending: true, contact_confirmed: false, unconfirmed_contact: "reader@example.com", consent: null });
  const html = consentScreenHTML(s, consentTerms({ deletionDate: deletionDateText(s.deletion_date) }));
  assert.match(html, /value="reader@example\.com"/);
  assert.match(html, /2027-06-30/);
  const x = sessionFromMe({ pending: true, provider: "x", handle: "someone", contact_confirmed: false, unconfirmed_contact: null });
  assert.equal(x.handle, "someone");
});

test("a signed-in reader may save only with both required consents granted", () => {
  const base = { signed_in: true, provider: "google", has_contact: true, handle: null, deletion_date: null, wording_version: "w" };
  assert.equal(sessionFromMe({ ...base, consents: { store: { granted: true }, age18: { granted: true } } }).consent.store, true);
  assert.equal(sessionFromMe({ ...base, consents: { store: { granted: true }, age18: { granted: false } } }).consent, null);
  assert.equal(sessionFromMe({ ...base, consents: {} }).consent, null);
  assert.equal(sessionFromMe({ signed_in: false, deletion_date: null }), null);
});
